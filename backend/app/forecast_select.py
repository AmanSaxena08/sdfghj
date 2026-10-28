"""The core rule of the app: which forecast did the buyer actually have?

For an hour on delivery day D, the purchase decision is made on day D-1 at the
auction cutoff (UK local time). The usable forecast is the most recent one
published at or before that moment. Anything published later did not exist yet.
"""

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import HORIZON_BUCKET_HOURS, MARKET_TZ
from app.models import Actual, Forecast

LOCAL_TZ = ZoneInfo(MARKET_TZ)


def delivery_day(start_time: datetime) -> date:
    """The UK calendar day a UTC timestamp falls on."""
    return start_time.astimezone(LOCAL_TZ).date()


def decision_time(start_time: datetime, cutoff: time) -> datetime:
    """When the purchase for `start_time` had to be made: the day before delivery, at the cutoff."""
    decision_day = delivery_day(start_time) - timedelta(days=1)
    return datetime.combine(decision_day, cutoff, tzinfo=LOCAL_TZ).astimezone(timezone.utc)


class ForecastIndex:
    """All forecasts grouped by target hour, sorted by publish time, for fast lookups."""

    def __init__(self, forecasts: list[Forecast]):
        grouped: dict[datetime, list[Forecast]] = defaultdict(list)
        for forecast in forecasts:
            grouped[forecast.start_time].append(forecast)
        self._by_target = {start: sorted(items, key=lambda f: f.publish_time) for start, items in grouped.items()}
        self._publish_times = {start: [f.publish_time for f in items] for start, items in self._by_target.items()}

    def latest_before(self, start_time: datetime, moment: datetime) -> Forecast | None:
        """The newest forecast for `start_time` published at or before `moment`, if any."""
        publish_times = self._publish_times.get(start_time)
        if not publish_times:
            return None
        position = bisect_right(publish_times, moment)
        return self._by_target[start_time][position - 1] if position else None

    def all(self) -> list[Forecast]:
        return [forecast for items in self._by_target.values() for forecast in items]


@dataclass(frozen=True)
class ComparisonRow:
    start_time: datetime
    actual_mw: float
    decision_time: datetime
    forecast_mw: float | None
    publish_time: datetime | None

    @property
    def horizon_hours(self) -> float | None:
        """How far ahead the chosen forecast was made."""
        if self.publish_time is None:
            return None
        return (self.start_time - self.publish_time).total_seconds() / 3600

    @property
    def error_mw(self) -> float | None:
        """Forecast minus actual: positive means the forecast was too high."""
        return None if self.forecast_mw is None else self.forecast_mw - self.actual_mw


def hourly_actuals(actuals: list[Actual], first_day: date, last_day: date) -> list[Actual]:
    """Actuals on the full hour within the delivery days; forecasts are hourly, so we compare like with like."""
    return [
        actual for actual in actuals
        if actual.start_time.minute == 0 and first_day <= delivery_day(actual.start_time) <= last_day
    ]


def build_comparison(
    actuals: list[Actual], index: ForecastIndex, first_day: date, last_day: date, cutoff: time
) -> list[ComparisonRow]:
    """For every delivery hour: what happened, and the forecast available at decision time."""
    rows = []
    for actual in hourly_actuals(actuals, first_day, last_day):
        decided_at = decision_time(actual.start_time, cutoff)
        forecast = index.latest_before(actual.start_time, decided_at)
        rows.append(ComparisonRow(
            start_time=actual.start_time,
            actual_mw=actual.generation_mw,
            decision_time=decided_at,
            forecast_mw=forecast.generation_mw if forecast else None,
            publish_time=forecast.publish_time if forecast else None,
        ))
    return rows


def errors_by_horizon(
    actuals: list[Actual], index: ForecastIndex, first_day: date, last_day: date
) -> dict[int, list[tuple[float, float]]]:
    """Every forecast for the period paired with its outcome, grouped by hours-ahead bucket.

    Returns {bucket start hour: [(error_mw, actual_mw), ...]}. Unlike the comparison,
    this uses every published forecast, to show how accuracy changes with lead time.
    """
    actual_by_time = {a.start_time: a.generation_mw for a in hourly_actuals(actuals, first_day, last_day)}
    buckets: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for forecast in index.all():
        actual = actual_by_time.get(forecast.start_time)
        if actual is None:
            continue
        hours_ahead = (forecast.start_time - forecast.publish_time).total_seconds() / 3600
        bucket = int(hours_ahead // HORIZON_BUCKET_HOURS) * HORIZON_BUCKET_HOURS
        buckets[bucket].append((forecast.generation_mw - actual, actual))
    return dict(sorted(buckets.items()))
