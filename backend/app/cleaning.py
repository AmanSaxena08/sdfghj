"""Turn raw Elexon API records into clean, de-duplicated records."""

from datetime import datetime, timezone

from app.models import Actual, Forecast


def parse_utc(value: str) -> datetime:
    """Parse an ISO timestamp such as '2026-01-05T14:00:00Z' into an aware UTC datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _number(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_actuals(records: list[dict]) -> list[Actual]:
    """Keep wind rows only, one value per half hour (the most recently published one wins)."""
    latest: dict[datetime, tuple[datetime, float]] = {}
    for record in records:
        if record.get("fuelType") != "WIND":
            continue
        generation = _number(record.get("generation"))
        if generation is None:
            continue
        start, published = parse_utc(record["startTime"]), parse_utc(record["publishTime"])
        if start not in latest or published >= latest[start][0]:
            latest[start] = (published, generation)

    return [Actual(start, generation) for start, (_, generation) in sorted(latest.items())]


def clean_forecasts(records: list[dict]) -> list[Forecast]:
    """Keep genuine forecasts: one value per (publish time, target hour), target not in the past.

    Each WINDFOR publication also repeats hours that have already passed;
    those are not forecasts, so they are dropped.
    """
    unique: dict[tuple[datetime, datetime], float] = {}
    for record in records:
        generation = _number(record.get("generation"))
        if generation is None:
            continue
        published, start = parse_utc(record["publishTime"]), parse_utc(record["startTime"])
        if start >= published:
            unique[(published, start)] = generation

    forecasts = [Forecast(published, start, generation) for (published, start), generation in unique.items()]
    return sorted(forecasts, key=lambda f: (f.start_time, f.publish_time))
