"""HTTP API. Each route only checks its input and calls the logic in the other modules."""

from collections import defaultdict
from dataclasses import asdict
from datetime import date, time
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query

from app import schemas
from app.config import (
    CUTOFF_PRESETS,
    DECISION_FIRST_DAY,
    DECISION_LAST_DAY,
    DEFAULT_CUTOFF,
    DELIVERY_FIRST_DAY,
    DELIVERY_LAST_DAY,
    HORIZON_BUCKET_HOURS,
    MARKET_TZ,
)
from app.data_loader import load_dataset
from app.forecast_select import ForecastIndex, build_comparison, delivery_day, errors_by_horizon
from app.metrics import histogram, summarize

HISTOGRAM_BIN_MW = 500

app = FastAPI(
    title="Wind Forecast Monitor API",
    description="Day-ahead view of GB wind generation forecasts versus actuals, January 2026 decisions.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
router = APIRouter(prefix="/api")


@lru_cache(maxsize=1)
def forecast_index() -> ForecastIndex:
    return ForecastIndex(load_dataset().forecasts)


def day_range_params(
    start: Annotated[date, Query(description="First delivery day (UK)")] = DELIVERY_FIRST_DAY,
    end: Annotated[date, Query(description="Last delivery day (UK)")] = DELIVERY_LAST_DAY,
) -> tuple[date, date]:
    if start > end:
        raise HTTPException(422, "start must be on or before end")
    if start < DELIVERY_FIRST_DAY or end > DELIVERY_LAST_DAY:
        raise HTTPException(422, f"delivery days must be within {DELIVERY_FIRST_DAY} and {DELIVERY_LAST_DAY}")
    return start, end


DayRangeDep = Annotated[tuple[date, date], Depends(day_range_params)]


def period_params(
    days: DayRangeDep,
    cutoff: Annotated[
        str, Query(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="Decision time on the day before, HH:MM UK")
    ] = DEFAULT_CUTOFF.strftime("%H:%M"),
) -> schemas.Period:
    return schemas.Period(start=days[0], end=days[1], cutoff=cutoff)


PeriodDep = Annotated[schemas.Period, Depends(period_params)]


def comparison_for(period: schemas.Period):
    return build_comparison(
        load_dataset().actuals, forecast_index(), period.start, period.end, time.fromisoformat(period.cutoff)
    )


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/meta", response_model=schemas.MetaResponse)
def meta():
    dataset = load_dataset()
    return schemas.MetaResponse(
        timezone=MARKET_TZ,
        delivery_first_day=DELIVERY_FIRST_DAY,
        delivery_last_day=DELIVERY_LAST_DAY,
        decision_first_day=DECISION_FIRST_DAY,
        decision_last_day=DECISION_LAST_DAY,
        default_cutoff=DEFAULT_CUTOFF.strftime("%H:%M"),
        cutoff_presets=[schemas.CutoffPreset(label=label, time=t.strftime("%H:%M")) for label, t in CUTOFF_PRESETS.items()],
        data=schemas.DataInfo(
            source=dataset.manifest.get("source", "Elexon BMRS"),
            fetched_at=dataset.manifest.get("fetched_at"),
            actual_rows=len(dataset.actuals),
            forecast_rows=len(dataset.forecasts),
        ),
    )


@router.get("/series", response_model=schemas.SeriesResponse)
def series(period: PeriodDep):
    """Hour by hour: actual generation and the latest forecast available at decision time."""
    points = [
        schemas.SeriesPoint(
            time=row.start_time,
            actual_mw=row.actual_mw,
            forecast_mw=row.forecast_mw,
            error_mw=row.error_mw,
            publish_time=row.publish_time,
            horizon_hours=row.horizon_hours,
            decision_time=row.decision_time,
        )
        for row in comparison_for(period)
    ]
    return schemas.SeriesResponse(period=period, points=points)


@router.get("/metrics", response_model=schemas.MetricsResponse)
def metrics(period: PeriodDep):
    """Accuracy of the decision-time forecasts: summary, error distribution and day-by-day breakdown."""
    rows = comparison_for(period)
    matched = [row for row in rows if row.error_mw is not None]
    errors = [row.error_mw for row in matched]
    summary = summarize(errors, [row.actual_mw for row in matched])

    by_day = defaultdict(list)
    for row in matched:
        by_day[delivery_day(row.start_time)].append(row)
    daily = [
        schemas.DailyError(
            day=day,
            hours=len(day_rows),
            mae_mw=sum(abs(r.error_mw) for r in day_rows) / len(day_rows),
            bias_mw=sum(r.error_mw for r in day_rows) / len(day_rows),
            mean_actual_mw=sum(r.actual_mw for r in day_rows) / len(day_rows),
            mean_forecast_mw=sum(r.forecast_mw for r in day_rows) / len(day_rows),
        )
        for day, day_rows in sorted(by_day.items())
    ]

    return schemas.MetricsResponse(
        period=period,
        summary=schemas.Summary(**asdict(summary)) if summary else None,
        coverage=schemas.Coverage(hours=len(rows), hours_with_forecast=len(matched)),
        histogram=[schemas.HistogramBin(**asdict(b)) for b in histogram(errors, HISTOGRAM_BIN_MW)],
        daily=daily,
    )


@router.get("/horizon", response_model=schemas.HorizonResponse)
def horizon(days: DayRangeDep):
    """Accuracy of all published forecasts, grouped by how many hours ahead they were made."""
    start, end = days
    buckets = []
    for start_hour, pairs in errors_by_horizon(load_dataset().actuals, forecast_index(), start, end).items():
        summary = summarize([error for error, _ in pairs], [actual for _, actual in pairs])
        buckets.append(schemas.HorizonBucket(
            from_hours=start_hour,
            to_hours=start_hour + HORIZON_BUCKET_HOURS,
            count=summary.count,
            mae_mw=summary.mae_mw,
            rmse_mw=summary.rmse_mw,
            bias_mw=summary.bias_mw,
            mae_pct_of_mean=summary.mae_pct_of_mean,
        ))
    return schemas.HorizonResponse(start=start, end=end, bucket_hours=HORIZON_BUCKET_HOURS, buckets=buckets)


app.include_router(router)
