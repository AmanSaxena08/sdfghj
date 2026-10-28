from datetime import datetime, timezone

from app.cleaning import clean_actuals, clean_forecasts


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_actuals_keep_wind_only_and_latest_publication():
    records = [
        {"fuelType": "WIND", "startTime": "2026-01-05T14:00:00Z", "publishTime": "2026-01-05T14:30:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-05T14:00:00Z", "publishTime": "2026-01-05T15:00:00Z", "generation": 120},
        {"fuelType": "CCGT", "startTime": "2026-01-05T14:00:00Z", "publishTime": "2026-01-05T14:30:00Z", "generation": 999},
        {"fuelType": "WIND", "startTime": "2026-01-05T14:30:00Z", "publishTime": "2026-01-05T15:00:00Z", "generation": None},
    ]
    actuals = clean_actuals(records)
    assert len(actuals) == 1
    assert actuals[0].start_time == utc(2026, 1, 5, 14)
    assert actuals[0].generation_mw == 120


def test_forecasts_drop_past_hours_and_duplicates():
    published = "2026-01-05T09:30:00Z"
    records = [
        {"publishTime": published, "startTime": "2026-01-05T08:00:00Z", "generation": 1},  # already past
        {"publishTime": published, "startTime": "2026-01-06T14:00:00Z", "generation": 5000},
        {"publishTime": published, "startTime": "2026-01-06T14:00:00Z", "generation": 5000},  # duplicate
        {"publishTime": published, "startTime": "2026-01-06T15:00:00Z", "generation": "bad"},
    ]
    forecasts = clean_forecasts(records)
    assert len(forecasts) == 1
    assert forecasts[0].publish_time == utc(2026, 1, 5, 9, 30)
    assert forecasts[0].start_time == utc(2026, 1, 6, 14)
