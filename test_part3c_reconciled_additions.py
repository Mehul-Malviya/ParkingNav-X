"""
Covers what was added to reconcile against the second, larger Member 1
spec version without duplicating the merged foundation: the 4 missing
DigitalTwinService methods, extended provenance validation, and the new
simulation/scenario API endpoints.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from digital_twin.api.app import app, get_db
from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.twin_service import DigitalTwinService

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIGS = PROJECT_ROOT / "configs" / "campuses"


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    apply_migrations(c)
    load_campus_config(CONFIGS / "sample.yaml", c)
    yield c
    c.close()


@pytest.fixture
def twin():
    return DigitalTwinService()


def test_unknown_provenance_value_rejected(conn, twin):
    with pytest.raises(ValueError, match="Unknown provenance"):
        twin.update_parking_state("sample", "sample-lot-1", 5, "manual", "TOTALLY_MADE_UP", "2026-01-01T00:00:00+00:00", conn)


def test_extended_provenance_values_accepted(conn, twin):
    # HISTORICAL/PREDICTION/DERIVED/COUNTERFACTUAL are additive, not conflicting.
    state = twin.update_parking_state("sample", "sample-lot-1", 5, "manual", "HISTORICAL", "2026-01-01T00:00:00+00:00", conn)
    assert state["provenance"] == "HISTORICAL"


def test_apply_event_state_activates_and_deactivates(conn, twin):
    twin.apply_event_state("sample", "sample-event-1", active=True, conn=conn)
    active = twin.get_active_events("sample", conn)
    assert any(e["event_id"] == "sample-event-1" for e in active)

    twin.apply_event_state("sample", "sample-event-1", active=False, conn=conn)
    active_after = twin.get_active_events("sample", conn)
    assert not any(e["event_id"] == "sample-event-1" for e in active_after)


def test_apply_event_state_rejects_unknown_event(conn, twin):
    with pytest.raises(ValueError, match="Unknown event"):
        twin.apply_event_state("sample", "does-not-exist", active=True, conn=conn)


def test_validate_state_detects_no_inconsistency_on_clean_state(conn, twin):
    twin.update_parking_state("sample", "sample-lot-1", 5, "manual", "REAL", "2026-01-01T00:00:00+00:00", conn)
    assert twin.validate_state("sample", conn) == []


def test_restore_snapshot_overwrites_current_state(conn, twin):
    twin.update_parking_state("sample", "sample-lot-1", 4, "manual", "REAL", "2026-01-01T00:00:00+00:00", conn)
    snapshot_id = twin.snapshot_now("sample", conn, timestamp="t=1")

    twin.update_parking_state("sample", "sample-lot-1", 9, "manual", "REAL", "2026-01-01T00:00:00+00:00", conn)
    assert twin.get_parking_state("sample", "sample-lot-1", conn)["occupied_spaces"] == 9

    twin.restore_snapshot("sample", snapshot_id, conn)
    assert twin.get_parking_state("sample", "sample-lot-1", conn)["occupied_spaces"] == 4


def test_get_state_at_timestamp_is_read_only(conn, twin):
    twin.update_parking_state("sample", "sample-lot-1", 4, "manual", "REAL", "2026-01-01T00:00:00+00:00", conn)
    twin.snapshot_now("sample", conn, timestamp="2026-01-01T00:05:00+00:00")

    twin.update_parking_state("sample", "sample-lot-1", 9, "manual", "REAL", "2026-01-01T00:00:00+00:00", conn)

    past = twin.get_state_at_timestamp("sample", "2026-01-01T00:05:00+00:00", conn)
    lot_then = next(p for p in past["full_state"]["parking"] if p["parking_lot_id"] == "sample-lot-1")
    assert lot_then["occupied_spaces"] == 4

    # Current state was NOT mutated by the read-only lookup.
    assert twin.get_parking_state("sample", "sample-lot-1", conn)["occupied_spaces"] == 9


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "api_test.db"
    conn = get_connection(db_path)
    apply_migrations(conn)
    load_campus_config(CONFIGS / "sample.yaml", conn)
    conn.close()

    def override_get_db():
        c = get_connection(db_path)
        try:
            yield c
        finally:
            c.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


VALID_SCENARIO = {
    "scenario_id": "api-test-scenario",
    "campus_id": "sample",
    "name": "NORMAL_DAY",
    "duration_minutes": 30,
    "vehicle_count": 5,
    "arrival_rate_profile": {"type": "constant", "rate": 0.2},
    "event_conditions": None,
    "availability_overrides": {"closed_gates": [], "closed_parking_lots": [], "closed_roads": []},
    "prediction_error_injection_level": 0.0,
    "random_seed": 1,
}


def test_validate_scenario_endpoint_accepts_valid_scenario(client):
    response = client.post("/api/v1/campuses/sample/scenarios/validate", json={"scenario": VALID_SCENARIO})
    assert response.status_code == 200
    assert response.json() == {"valid": True, "errors": []}


def test_validate_scenario_endpoint_rejects_bad_reference(client):
    bad = dict(VALID_SCENARIO, availability_overrides={"closed_gates": ["nope"], "closed_parking_lots": [], "closed_roads": []})
    response = client.post("/api/v1/campuses/sample/scenarios/validate", json={"scenario": bad})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any("unknown gate" in e for e in body["errors"])


def test_run_simulation_endpoint_rejects_disallowed_strategy_path(client):
    response = client.post(
        "/api/v1/campuses/sample/simulation/run",
        json={"scenario": VALID_SCENARIO, "strategy": "os.system"},
    )
    assert response.status_code == 422


def test_run_simulation_endpoint_end_to_end(client):
    response = client.post(
        "/api/v1/campuses/sample/simulation/run",
        json={"scenario": VALID_SCENARIO, "strategy": "digital_twin.simulation.demo_strategies.DemoNearestAvailableStrategy"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["vehicle_count"] == 5
    simulation_id = body["simulation_id"]

    run_response = client.get(f"/api/v1/campuses/sample/simulation/{simulation_id}")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "completed"

    metrics_response = client.get(f"/api/v1/campuses/sample/simulation/{simulation_id}/metrics")
    assert metrics_response.status_code == 200
    assert metrics_response.json()["total_vehicles"] == 5

    events_response = client.get(f"/api/v1/campuses/sample/simulation/{simulation_id}/events")
    assert events_response.status_code == 200
    assert "overflow_events" in events_response.json()


if __name__ == "__main__":
    print("Run with pytest: python -m pytest test_part3c_reconciled_additions.py -v")
