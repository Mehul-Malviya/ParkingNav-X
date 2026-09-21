from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from digital_twin.api.app import app, get_db
from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIGS = PROJECT_ROOT / "configs" / "campuses"


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


def test_get_campus(client):
    response = client.get("/api/v1/campuses/sample")
    assert response.status_code == 200
    assert response.json()["campus_id"] == "sample"


def test_get_campus_not_found(client):
    response = client.get("/api/v1/campuses/does-not-exist")
    assert response.status_code == 404


def test_get_gates(client):
    response = client.get("/api/v1/campuses/sample/gates")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_parking_lots(client):
    response = client.get("/api/v1/campuses/sample/parking-lots")
    assert len(response.json()) == 2


def test_get_graph(client):
    response = client.get("/api/v1/campuses/sample/graph")
    body = response.json()
    assert len(body["nodes"]) == 4
    assert len(body["edges"]) == 3


def test_get_graph_bounds(client):
    response = client.get("/api/v1/campuses/sample/graph/bounds")
    assert response.json()["min_lat"] is not None


def test_post_parking_state_and_get_it_back(client):
    response = client.post(
        "/api/v1/campuses/sample/state/parking/sample-lot-1",
        json={"occupied_spaces": 6, "source": "manual", "provenance": "REAL"},
    )
    assert response.status_code == 200
    assert response.json()["occupied_spaces"] == 6

    fetched = client.get("/api/v1/campuses/sample/state/parking/sample-lot-1")
    assert fetched.json()["occupied_spaces"] == 6


def test_post_parking_state_over_capacity_rejected(client):
    response = client.post(
        "/api/v1/campuses/sample/state/parking/sample-lot-1",
        json={"occupied_spaces": 999, "source": "manual", "provenance": "REAL"},
    )
    assert response.status_code == 422


def test_post_parking_state_missing_provenance_rejected(client):
    response = client.post(
        "/api/v1/campuses/sample/state/parking/sample-lot-1",
        json={"occupied_spaces": 5, "source": "manual"},
    )
    assert response.status_code == 422  # pydantic: required field missing


def test_get_state_returns_full_campus_state(client):
    client.post(
        "/api/v1/campuses/sample/state/parking/sample-lot-1",
        json={"occupied_spaces": 3, "source": "manual", "provenance": "REAL"},
    )
    response = client.get("/api/v1/campuses/sample/state")
    body = response.json()
    assert body["campus_id"] == "sample"
    assert len(body["parking"]) == 1


if __name__ == "__main__":
    print("Run with pytest: python -m pytest test_api.py -v")
