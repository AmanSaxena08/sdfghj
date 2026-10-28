"""Read and write the stored data files (CSV) and the manifest describing them."""

import csv
import io
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.cleaning import parse_utc
from app.config import ACTUALS_FILE, FORECASTS_FILE, MANIFEST_FILE
from app.models import Actual, Forecast

ACTUAL_HEADER = ["start_time", "generation_mw"]
FORECAST_HEADER = ["publish_time", "start_time", "generation_mw"]


def _iso(value) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _mw(value: float) -> str:
    return f"{value:g}"


def actuals_to_csv(actuals: list[Actual]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(ACTUAL_HEADER)
    writer.writerows([_iso(a.start_time), _mw(a.generation_mw)] for a in actuals)
    return buffer.getvalue()


def forecasts_to_csv(forecasts: list[Forecast]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(FORECAST_HEADER)
    writer.writerows([_iso(f.publish_time), _iso(f.start_time), _mw(f.generation_mw)] for f in forecasts)
    return buffer.getvalue()


def read_actuals(path: Path) -> list[Actual]:
    with path.open(newline="") as file:
        return [Actual(parse_utc(row["start_time"]), float(row["generation_mw"])) for row in csv.DictReader(file)]


def read_forecasts(path: Path) -> list[Forecast]:
    with path.open(newline="") as file:
        return [
            Forecast(parse_utc(row["publish_time"]), parse_utc(row["start_time"]), float(row["generation_mw"]))
            for row in csv.DictReader(file)
        ]


@dataclass(frozen=True)
class Dataset:
    actuals: list[Actual]
    forecasts: list[Forecast]
    manifest: dict


@lru_cache(maxsize=1)
def load_dataset() -> Dataset:
    """Load the stored data once per process; every request then reuses it from memory."""
    manifest = json.loads(MANIFEST_FILE.read_text()) if MANIFEST_FILE.exists() else {}
    return Dataset(read_actuals(ACTUALS_FILE), read_forecasts(FORECASTS_FILE), manifest)
