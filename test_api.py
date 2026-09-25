"""
Integration Tests for FastAPI Endpoints.
"""

import pytest
from starlette.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_get_pulse_state(client):
    res = client.get("/api/pulse")
    assert res.status_code == 200
    data = res.json()
    assert "overall_health_score" in data
    assert "pulse_rate_bpm" in data
    assert "zones" in data
    assert "plain_language_summary" in data
    assert len(data["zones"]) >= 5


def test_get_plain_language_summary(client):
    res = client.get("/api/summary")
    assert res.status_code == 200
    data = res.json()
    assert "ten_second_headline" in data
    assert "what_is_happening" in data
    assert "why_it_matters" in data
    assert "actionable_advice" in data


def test_get_zones(client):
    res = client.get("/api/zones")
    assert res.status_code == 200
    data = res.json()
    assert "downtown" in data
    assert "bounds" in data["downtown"]


def test_feed_toggle_graceful_degradation(client):
    # Toggle transit feed OFF
    res = client.post("/api/feeds/toggle", json={"feed_type": "TRANSIT", "enabled": False})
    assert res.status_code == 200

    # Verify state is still computable without crashing
    res_pulse = client.get("/api/pulse")
    assert res_pulse.status_code == 200
    assert res_pulse.json()["feeds_health"]["TRANSIT"]["status"] == "OFFLINE"

    # Toggle back ON
    client.post("/api/feeds/toggle", json={"feed_type": "TRANSIT", "enabled": True})


def test_incident_injection(client):
    res = client.post("/api/inject/incident", json={"zone_id": "downtown", "scenario_type": "FLOOD"})
    assert res.status_code == 200

    # Pulse should show lowered health score or disruption
    res_pulse = client.get("/api/pulse")
    assert res_pulse.status_code == 200
    data = res_pulse.json()
    assert data["overall_health_score"] < 100.0


def test_replay_lifecycle(client):
    # Load scenario
    res_load = client.post("/api/replay/load", json={"scenario_id": "flash_flood"})
    assert res_load.status_code == 200

    # Step forward
    res_step = client.post("/api/replay/step", json={"action": "forward"})
    assert res_step.status_code == 200
    assert res_step.json()["meta"]["step_index"] == 1

    # Check pulse in replay mode
    res_pulse = client.get("/api/pulse")
    assert res_pulse.json()["is_replay_mode"] is True

    # Exit replay
    res_exit = client.post("/api/replay/exit")
    assert res_exit.status_code == 200
