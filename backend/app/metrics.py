"""Accuracy measures for a set of forecast errors (error = forecast - actual, in MW)."""

import math
from dataclasses import dataclass


def percentile(values: list[float], share: float) -> float:
    """Value below which `share` (0..1) of the values fall, interpolating between neighbours."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * share
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


@dataclass(frozen=True)
class Summary:
    count: int
    mae_mw: float  # mean absolute error: the typical size of a miss
    rmse_mw: float  # root mean squared error: like MAE, but big misses weigh more
    bias_mw: float  # mean error: positive = forecasts tend to be too high
    p90_abs_error_mw: float  # 9 in 10 hours the miss was no bigger than this
    max_abs_error_mw: float
    shortfall_p90_mw: float  # 9 in 10 hours wind came in no more than this below forecast
    mean_actual_mw: float
    mae_pct_of_mean: float  # MAE relative to average generation


def summarize(errors: list[float], actuals: list[float]) -> Summary | None:
    if not errors:
        return None
    count = len(errors)
    absolute = [abs(e) for e in errors]
    mean_actual = sum(actuals) / len(actuals)
    mae = sum(absolute) / count
    return Summary(
        count=count,
        mae_mw=mae,
        rmse_mw=math.sqrt(sum(e * e for e in errors) / count),
        bias_mw=sum(errors) / count,
        p90_abs_error_mw=percentile(absolute, 0.9),
        max_abs_error_mw=max(absolute),
        shortfall_p90_mw=max(0.0, percentile(errors, 0.9)),
        mean_actual_mw=mean_actual,
        mae_pct_of_mean=100 * mae / mean_actual if mean_actual else 0.0,
    )


@dataclass(frozen=True)
class HistogramBin:
    from_mw: float
    to_mw: float
    count: int


def histogram(errors: list[float], bin_width: float) -> list[HistogramBin]:
    """Count errors in fixed-width bins, including empty bins in between so the shape reads honestly."""
    if not errors:
        return []
    counts: dict[int, int] = {}
    for error in errors:
        key = math.floor(error / bin_width)
        counts[key] = counts.get(key, 0) + 1
    return [
        HistogramBin(key * bin_width, (key + 1) * bin_width, counts.get(key, 0))
        for key in range(min(counts), max(counts) + 1)
    ]
