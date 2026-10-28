"""Download wind actuals and forecasts from Elexon BMRS and store them in backend/data.

Usage (run from the backend folder):
    python -m scripts.fetch_data           # download and (re)write the data files
    python -m scripts.fetch_data --check   # download and compare with the stored files, write nothing

The app serves these stored files instead of calling Elexon on every request.
`--check` exits with code 1 when Elexon's data differs from what is stored,
so a scheduled job can detect revisions and refresh the files.
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.cleaning import clean_actuals, clean_forecasts
from app.config import ACTUALS_FILE, DATA_DIR, FORECASTS_FILE, MANIFEST_FILE
from app.data_loader import actuals_to_csv, forecasts_to_csv

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

# Actuals: settlement dates (UK local days) covering every delivery day, with a day of margin.
ACTUALS_FROM = date(2026, 1, 1)
ACTUALS_TO = date(2026, 2, 2)

# Forecasts: everything published from a few days before the first decision
# until the end of the last decision day (forecasts reach ~2 days ahead).
FORECASTS_FROM = datetime(2025, 12, 29, tzinfo=timezone.utc)
FORECASTS_TO = datetime(2026, 2, 1, tzinfo=timezone.utc)


def get_json(dataset: str, params: dict, retries: int = 3) -> list[dict]:
    url = f"{BASE_URL}/{dataset}/stream?{urllib.parse.urlencode(params)}"
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.load(response)
        except Exception as error:  # network hiccups are retried, then reported
            if attempt == retries:
                raise RuntimeError(f"Failed to fetch {url}: {error}") from error
            time.sleep(2 * attempt)
    return []


def fetch_actuals_csv() -> str:
    records: list[dict] = []
    day = ACTUALS_FROM
    while day <= ACTUALS_TO:
        chunk_end = min(day + timedelta(days=6), ACTUALS_TO)
        records += get_json("FUELHH", {
            "settlementDateFrom": day.isoformat(),
            "settlementDateTo": chunk_end.isoformat(),
            "fuelType": "WIND",
        })
        print(f"  actuals   {day} -> {chunk_end}: {len(records)} records so far")
        day = chunk_end + timedelta(days=1)
    return actuals_to_csv(clean_actuals(records))


def fetch_forecasts_csv() -> str:
    records: list[dict] = []
    start = FORECASTS_FROM
    while start < FORECASTS_TO:
        end = min(start + timedelta(days=2), FORECASTS_TO)
        records += get_json("WINDFOR", {
            "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        print(f"  forecasts {start:%Y-%m-%d} -> {end:%Y-%m-%d}: {len(records)} records so far")
        start = end
    return forecasts_to_csv(clean_forecasts(records))


def compare(name: str, fresh_text: str, path: Path) -> bool:
    """Print how the fresh download differs from the stored file. Returns True if it changed."""
    if not path.exists():
        print(f"  {name}: no stored file yet")
        return True
    stored_rows = set(path.read_text().splitlines()[1:])
    fresh_rows = set(fresh_text.splitlines()[1:])
    added, removed = fresh_rows - stored_rows, stored_rows - fresh_rows
    if not added and not removed:
        print(f"  {name}: unchanged ({len(fresh_rows)} rows)")
        return False
    print(f"  {name}: CHANGED, {len(added)} new/updated rows, {len(removed)} old rows replaced")
    return True


def file_info(text: str, **details) -> dict:
    return {**details, "rows": text.count("\n") - 1, "sha256": hashlib.sha256(text.encode()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="compare with stored data without writing")
    args = parser.parse_args()

    print("Fetching actual wind generation (FUELHH)...")
    actuals_text = fetch_actuals_csv()
    print("Fetching wind forecasts (WINDFOR)...")
    forecasts_text = fetch_forecasts_csv()

    print("Comparing with stored data:")
    changed = compare("actuals", actuals_text, ACTUALS_FILE)
    changed = compare("forecasts", forecasts_text, FORECASTS_FILE) or changed

    if args.check:
        return 1 if changed else 0
    if not changed:
        print("Nothing to write.")
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ACTUALS_FILE.write_text(actuals_text)
    FORECASTS_FILE.write_text(forecasts_text)
    MANIFEST_FILE.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Elexon BMRS Insights API",
        "files": {
            "actuals.csv": file_info(
                actuals_text,
                dataset="FUELHH (fuelType=WIND)",
                settlement_dates=[ACTUALS_FROM.isoformat(), ACTUALS_TO.isoformat()],
            ),
            "forecasts.csv": file_info(
                forecasts_text,
                dataset="WINDFOR",
                publish_window=[FORECASTS_FROM.isoformat(), FORECASTS_TO.isoformat()],
            ),
        },
    }, indent=2) + "\n")
    print(f"Saved data to {DATA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
