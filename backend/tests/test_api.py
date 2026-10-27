import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)
Q = "from=2026-01-01&to=2026-01-31"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_series_day_ahead_never_uses_forecast_after_gate():
    pts = client.get(f"/api/series?{Q}&mode=day_ahead&gate=09:00").json()["points"]
    assert len(pts) == 31 * 24
    used = [p for p in pts if p["publishTime"] is not None]
    assert used
    for p in used:
        day = p["startTime"][:10]
        # Gate is D-1 09:00, so the forecast must have been published before D-1 09:00 + epsilon.
        assert p["publishTime"][:10] < day
        assert p["leadHours"] >= 15  # D-1 09:00 to D 00:00 is the minimum possible lead


def test_series_horizon_respects_lead():
    pts = client.get(f"/api/series?{Q}&mode=horizon&h=12").json()["points"]
    leads = [p["leadHours"] for p in pts if p["leadHours"] is not None]
    assert leads and min(leads) >= 12


def test_metrics_summary_and_by_hour():
    j = client.get(f"/api/metrics?{Q}").json()
    assert j["summary"]["n"] > 700
    assert len(j["byHour"]) == 24
    assert j["summary"]["mae"] > 0


def test_error_by_horizon_buckets_ordered():
    j = client.get(f"/api/error-by-horizon?{Q}").json()
    assert [b["fromHours"] for b in j] == sorted(b["fromHours"] for b in j)
    assert j[0]["fromHours"] == 0


def test_revisions_flags_exactly_one_used():
    j = client.get("/api/revisions?target=2026-01-15T12:00:00Z").json()
    assert sum(r["usedByGate"] for r in j["revisions"]) == 1
    assert j["actual"] is not None


@pytest.mark.parametrize("qs", [
    "from=2025-12-31&to=2026-01-05",
    "from=2026-01-10&to=2026-01-05",
    "gate=25:00",
    "mode=nope",
    "mode=horizon&h=-1",
])
def test_validation_errors(qs):
    assert client.get(f"/api/series?{qs}").status_code == 422


def test_revisions_unknown_target_404():
    assert client.get("/api/revisions?target=2030-01-01T00:00:00Z").status_code == 404
