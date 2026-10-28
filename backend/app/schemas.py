"""Shapes of the JSON the API returns. FastAPI validates against these and documents them at /docs."""

from datetime import date, datetime

from pydantic import BaseModel


class CutoffPreset(BaseModel):
    label: str
    time: str  # "HH:MM", UK local time


class DataInfo(BaseModel):
    source: str
    fetched_at: str | None
    actual_rows: int
    forecast_rows: int


class MetaResponse(BaseModel):
    timezone: str
    delivery_first_day: date
    delivery_last_day: date
    decision_first_day: date
    decision_last_day: date
    default_cutoff: str
    cutoff_presets: list[CutoffPreset]
    data: DataInfo


class Period(BaseModel):
    start: date
    end: date
    cutoff: str


class SeriesPoint(BaseModel):
    time: datetime
    actual_mw: float
    forecast_mw: float | None
    error_mw: float | None
    publish_time: datetime | None
    horizon_hours: float | None
    decision_time: datetime


class SeriesResponse(BaseModel):
    period: Period
    points: list[SeriesPoint]


class Summary(BaseModel):
    count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    p90_abs_error_mw: float
    max_abs_error_mw: float
    shortfall_p90_mw: float
    mean_actual_mw: float
    mae_pct_of_mean: float


class Coverage(BaseModel):
    hours: int
    hours_with_forecast: int


class HistogramBin(BaseModel):
    from_mw: float
    to_mw: float
    count: int


class DailyError(BaseModel):
    day: date
    hours: int
    mae_mw: float
    bias_mw: float
    mean_actual_mw: float
    mean_forecast_mw: float


class MetricsResponse(BaseModel):
    period: Period
    summary: Summary | None
    coverage: Coverage
    histogram: list[HistogramBin]
    daily: list[DailyError]


class HorizonBucket(BaseModel):
    from_hours: int
    to_hours: int
    count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    mae_pct_of_mean: float


class HorizonResponse(BaseModel):
    start: date
    end: date
    bucket_hours: int
    buckets: list[HorizonBucket]
