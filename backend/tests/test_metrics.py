import math

import pytest

from app.metrics import histogram, percentile, summarize


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert percentile([0, 10], 0.9) == 9


def test_summary_on_known_errors():
    errors = [100, -100, 300, -300]
    summary = summarize(errors, [1000, 1000, 1000, 1000])
    assert summary.count == 4
    assert summary.mae_mw == 200
    assert summary.bias_mw == 0
    assert summary.rmse_mw == pytest.approx(math.sqrt((100**2 * 2 + 300**2 * 2) / 4))
    assert summary.max_abs_error_mw == 300
    assert summary.mae_pct_of_mean == 20


def test_bias_sign_means_forecast_too_high():
    assert summarize([500, 500], [1000, 1000]).bias_mw == 500


def test_shortfall_is_never_negative():
    # Forecast always too low: wind never fell short of the forecast.
    assert summarize([-200, -100], [1000, 1000]).shortfall_p90_mw == 0


def test_summary_of_nothing_is_none():
    assert summarize([], []) is None


def test_histogram_fills_empty_bins():
    bins = histogram([-600, 100, 1200], 500)
    assert [(b.from_mw, b.to_mw, b.count) for b in bins] == [
        (-1000, -500, 1), (-500, 0, 0), (0, 500, 1), (500, 1000, 0), (1000, 1500, 1),
    ]
