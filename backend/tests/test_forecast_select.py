from datetime import date, datetime, time, timezone

from app.forecast_select import ForecastIndex, build_comparison, decision_time, errors_by_horizon
from app.models import Actual, Forecast

CUTOFF = time(9, 20)


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_decision_time_is_day_before_at_cutoff():
    # January is GMT, so UK local time equals UTC.
    assert decision_time(utc(2026, 1, 10, 14), CUTOFF) == utc(2026, 1, 9, 9, 20)
    # Midnight belongs to the new delivery day.
    assert decision_time(utc(2026, 1, 10, 0), CUTOFF) == utc(2026, 1, 9, 9, 20)
    assert decision_time(utc(2026, 1, 10, 23), CUTOFF) == utc(2026, 1, 9, 9, 20)


def test_decision_time_respects_british_summer_time():
    # 10 July 14:00 UTC is 15:00 BST; decision on 9 July 09:20 BST = 08:20 UTC.
    assert decision_time(utc(2026, 7, 10, 14), CUTOFF) == utc(2026, 7, 9, 8, 20)


def test_picks_latest_forecast_published_before_decision():
    target = utc(2026, 1, 10, 14)
    index = ForecastIndex([
        Forecast(utc(2026, 1, 8, 22, 30), target, 9000),
        Forecast(utc(2026, 1, 9, 7, 30), target, 10000),  # newest before 09:20, should win
        Forecast(utc(2026, 1, 9, 11, 30), target, 11000),  # published after the decision
    ])
    assert index.latest_before(target, utc(2026, 1, 9, 9, 20)).generation_mw == 10000


def test_forecast_published_exactly_at_cutoff_counts():
    target = utc(2026, 1, 10, 14)
    index = ForecastIndex([Forecast(utc(2026, 1, 9, 9, 20), target, 10000)])
    assert index.latest_before(target, utc(2026, 1, 9, 9, 20)) is not None


def test_no_forecast_when_all_published_too_late():
    target = utc(2026, 1, 10, 14)
    index = ForecastIndex([Forecast(utc(2026, 1, 9, 11, 30), target, 11000)])
    assert index.latest_before(target, utc(2026, 1, 9, 9, 20)) is None


def test_comparison_uses_hourly_actuals_within_days_and_computes_error():
    actuals = [
        Actual(utc(2026, 1, 9, 23), 1),  # day before the range
        Actual(utc(2026, 1, 10, 14), 10500),
        Actual(utc(2026, 1, 10, 14, 30), 10600),  # half hour: no hourly forecast to compare with
        Actual(utc(2026, 1, 10, 15), 11400),
    ]
    index = ForecastIndex([
        Forecast(utc(2026, 1, 9, 7, 30), utc(2026, 1, 10, 14), 12000),
    ])
    rows = build_comparison(actuals, index, date(2026, 1, 10), date(2026, 1, 10), CUTOFF)

    assert [r.start_time for r in rows] == [utc(2026, 1, 10, 14), utc(2026, 1, 10, 15)]
    assert rows[0].error_mw == 1500
    assert rows[0].horizon_hours == 30.5
    assert rows[1].forecast_mw is None and rows[1].error_mw is None


def test_later_cutoff_can_use_a_newer_forecast():
    target = utc(2026, 1, 10, 14)
    actuals = [Actual(target, 10000)]
    index = ForecastIndex([
        Forecast(utc(2026, 1, 9, 7, 30), target, 12000),
        Forecast(utc(2026, 1, 9, 9, 30), target, 10500),
    ])
    early = build_comparison(actuals, index, date(2026, 1, 10), date(2026, 1, 10), time(9, 20))
    late = build_comparison(actuals, index, date(2026, 1, 10), date(2026, 1, 10), time(9, 50))
    assert early[0].forecast_mw == 12000
    assert late[0].forecast_mw == 10500


def test_errors_by_horizon_buckets_every_forecast():
    target = utc(2026, 1, 10, 14)
    index = ForecastIndex([
        Forecast(utc(2026, 1, 10, 11), target, 10100),  # 3 h ahead -> bucket 0
        Forecast(utc(2026, 1, 9, 7), target, 12000),  # 31 h ahead -> bucket 30
    ])
    buckets = errors_by_horizon([Actual(target, 10000)], index, date(2026, 1, 10), date(2026, 1, 10))
    assert buckets == {0: [(100, 10000)], 30: [(2000, 10000)]}
