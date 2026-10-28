"""End-to-end checks of the HTTP API against the stored January 2026 data."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_meta_describes_the_window():
    body = client.get("/api/meta").json()
    assert body["delivery_first_day"] == "2026-01-02"
    assert body["delivery_last_day"] == "2026-02-01"
    assert body["data"]["actual_rows"] > 0 and body["data"]["forecast_rows"] > 0


def test_series_covers_every_hour_of_the_month():
    points = client.get("/api/series").json()["points"]
    assert len(points) == 31 * 24
    with_forecast = [p for p in points if p["forecast_mw"] is not None]
    assert len(with_forecast) / len(points) > 0.95
    # No chosen forecast may be published after its decision time.
    assert all(p["publish_time"] <= p["decision_time"] for p in with_forecast)


def test_metrics_for_one_week():
    body = client.get("/api/metrics", params={"start": "2026-01-05", "end": "2026-01-11", "cutoff": "09:50"}).json()
    assert body["coverage"]["hours"] == 7 * 24
    assert body["summary"]["mae_mw"] > 0
    assert len(body["daily"]) == 7


def test_horizon_buckets_are_ordered():
    buckets = client.get("/api/horizon").json()["buckets"]
    starts = [b["from_hours"] for b in buckets]
    assert starts == sorted(starts) and starts[0] == 0


def test_rejects_dates_outside_the_window():
    assert client.get("/api/series", params={"start": "2025-12-01"}).status_code == 422


def test_rejects_bad_cutoff():
    assert client.get("/api/series", params={"cutoff": "25:00"}).status_code == 422


def test_rejects_reversed_range():
    assert client.get("/api/series", params={"start": "2026-01-10", "end": "2026-01-05"}).status_code == 422
