"""Central settings: where the data lives and which period the app covers."""

from datetime import date, time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTUALS_FILE = DATA_DIR / "actuals.csv"
FORECASTS_FILE = DATA_DIR / "forecasts.csv"
MANIFEST_FILE = DATA_DIR / "manifest.json"

# GB market days are defined in UK local time; the raw data is in UTC.
MARKET_TZ = "Europe/London"

# Purchase decisions made in January 2026 are for delivery the next day,
# so the delivery days we analyse run from 2 Jan to 1 Feb 2026.
DECISION_FIRST_DAY = date(2026, 1, 1)
DECISION_LAST_DAY = date(2026, 1, 31)
DELIVERY_FIRST_DAY = date(2026, 1, 2)
DELIVERY_LAST_DAY = date(2026, 2, 1)

# Gate closure of the GB day-ahead auctions (UK local time, day before delivery).
CUTOFF_PRESETS = {
    "EPEX GB day-ahead": time(9, 20),
    "N2EX (Nord Pool) day-ahead": time(9, 50),
}
DEFAULT_CUTOFF = time(9, 20)

# Width of the buckets used when grouping forecasts by how far ahead they were made.
HORIZON_BUCKET_HOURS = 6
