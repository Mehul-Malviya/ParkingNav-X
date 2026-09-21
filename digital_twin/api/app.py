"""
FastAPI app exposing the Member 1 subsystem's contract:
- Part 1: read-only campus facts (Navigation/Frontend build against these).
- Part 2: campus graph export (Navigation's pathfinding builds on top of this).
- Part 3: Digital Twin state, read (everyone) and write (Member 2's ingestion).

The DB connection is a request-scoped dependency so tests can override it
with a temporary database.
"""

import json
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from digital_twin.db import get_connection
from digital_twin.graph_service import CampusGraphService
from digital_twin.twin_service import DigitalTwinService

app = FastAPI(title="ParkingNav-X Digital Twin API")

_graph_service = CampusGraphService()
_twin_service = DigitalTwinService()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _row_to_dict(row):
    return {k: row[k] for k in row.keys()}


def _campus_exists(conn, campus_id):
    row = conn.execute("SELECT campus_id FROM campuses WHERE campus_id=?", (campus_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Campus '{campus_id}' not found.")


@app.get("/api/v1/campuses/{campus_id}")
def get_campus(campus_id: str, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM campuses WHERE campus_id=?", (campus_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Campus '{campus_id}' not found.")
    return _row_to_dict(row)


@app.get("/api/v1/campuses/{campus_id}/gates")
def get_gates(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    rows = conn.execute("SELECT * FROM gates WHERE campus_id=?", (campus_id,)).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/api/v1/campuses/{campus_id}/roads")
def get_roads(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    rows = conn.execute("SELECT * FROM roads WHERE campus_id=?", (campus_id,)).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["geometry"] = json.loads(d["geometry"])
        result.append(d)
    return result


@app.get("/api/v1/campuses/{campus_id}/parking-lots")
def get_parking_lots(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    rows = conn.execute("SELECT * FROM parking_lots WHERE campus_id=?", (campus_id,)).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/api/v1/campuses/{campus_id}/destinations")
def get_destinations(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    rows = conn.execute("SELECT * FROM destinations WHERE campus_id=?", (campus_id,)).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/api/v1/campuses/{campus_id}/events")
def get_events(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    rows = conn.execute("SELECT * FROM events WHERE campus_id=?", (campus_id,)).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/api/v1/campuses/{campus_id}/graph")
def get_graph(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    graph = _graph_service.build_graph(campus_id, conn)
    return _graph_service.to_json(graph)


@app.get("/api/v1/campuses/{campus_id}/graph/bounds")
def get_graph_bounds(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    graph = _graph_service.build_graph(campus_id, conn)
    return _graph_service.get_graph_bounds(graph)


@app.post("/api/v1/campuses/{campus_id}/graph/refresh")
def refresh_graph(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    graph = _graph_service.refresh_graph(campus_id, conn)
    return {"campus_id": campus_id, "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()}


@app.get("/api/v1/campuses/{campus_id}/state")
def get_state(campus_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    return _twin_service.get_current_state(campus_id, conn)


@app.get("/api/v1/campuses/{campus_id}/state/parking/{lot_id}")
def get_parking_state(campus_id: str, lot_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    state = _twin_service.get_parking_state(campus_id, lot_id, conn)
    if state is None:
        raise HTTPException(status_code=404, detail=f"No state for parking lot '{lot_id}'.")
    return state


@app.get("/api/v1/campuses/{campus_id}/state/history")
def get_state_history(campus_id: str, from_: str = None, to: str = None, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    return _twin_service.get_state_history(campus_id, from_, to, conn)


class ParkingStateUpdate(BaseModel):
    occupied_spaces: int
    source: str
    provenance: str
    observation_timestamp: str = None


@app.post("/api/v1/campuses/{campus_id}/state/parking/{lot_id}")
def post_parking_state(campus_id: str, lot_id: str, update: ParkingStateUpdate, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    observation_timestamp = update.observation_timestamp or datetime.now(timezone.utc).isoformat()
    try:
        state = _twin_service.update_parking_state(
            campus_id, lot_id, update.occupied_spaces, update.source, update.provenance,
            observation_timestamp, conn,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return state


class GateStateUpdate(BaseModel):
    current_queue_length: int
    throughput_last_5min: int = 0
    source: str
    provenance: str
    observation_timestamp: str = None


@app.post("/api/v1/campuses/{campus_id}/state/gates/{gate_id}")
def post_gate_state(campus_id: str, gate_id: str, update: GateStateUpdate, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    observation_timestamp = update.observation_timestamp or datetime.now(timezone.utc).isoformat()
    try:
        state = _twin_service.update_gate_state(
            campus_id, gate_id, update.current_queue_length, update.throughput_last_5min,
            update.source, update.provenance, observation_timestamp, conn,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return state


# --- Simulation + scenario endpoints -----------------------------------
# Same campus-scoped path scheme as everything above, rather than a
# separate flat /simulation or /scenarios namespace -- keeps multi-campus
# isolation consistent across the whole API.

_ALLOWED_STRATEGY_PREFIX = "digital_twin.simulation."  # never import an arbitrary dotted path from the network


class ScenarioValidateRequest(BaseModel):
    scenario: dict


@app.post("/api/v1/campuses/{campus_id}/scenarios/validate")
def post_validate_scenario(campus_id: str, request: ScenarioValidateRequest, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    from digital_twin.models import ConfigError
    from digital_twin.simulation.scenario import ScenarioLoader, ScenarioValidator

    try:
        scenario = ScenarioLoader.from_dict(request.scenario)
    except ConfigError as e:
        return {"valid": False, "errors": [str(e)]}

    errors = ScenarioValidator.validate(scenario, conn)
    return {"valid": not errors, "errors": errors}


class SimulationRunRequest(BaseModel):
    scenario: dict
    strategy: str  # dotted path, must live under digital_twin.simulation.*


@app.post("/api/v1/campuses/{campus_id}/simulation/run")
def post_run_simulation(campus_id: str, request: SimulationRunRequest, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    import importlib

    from digital_twin.graph_service import CampusGraphService
    from digital_twin.models import ConfigError
    from digital_twin.simulation.engine import SimulationEngine
    from digital_twin.simulation.scenario import ScenarioLoader, ScenarioValidator

    if not request.strategy.startswith(_ALLOWED_STRATEGY_PREFIX):
        raise HTTPException(
            status_code=422,
            detail=f"strategy must be under '{_ALLOWED_STRATEGY_PREFIX}' (no arbitrary imports over the API).",
        )

    try:
        scenario = ScenarioLoader.from_dict(request.scenario)
    except ConfigError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if scenario.campus_id != campus_id:
        raise HTTPException(status_code=422, detail="scenario.campus_id does not match the URL's campus_id.")

    errors = ScenarioValidator.validate(scenario, conn)
    if errors:
        raise HTTPException(status_code=422, detail={"scenario_errors": errors})

    module_path, class_name = request.strategy.rsplit(".", 1)
    try:
        strategy_class = getattr(importlib.import_module(module_path), class_name)
    except (ImportError, AttributeError) as e:
        raise HTTPException(status_code=422, detail=f"Could not load strategy '{request.strategy}': {e}")

    graph = CampusGraphService().build_graph(campus_id, conn)
    result = SimulationEngine().run(scenario, strategy_class(), conn)
    return {
        "simulation_id": result.run_id,
        "campus_id": result.campus_id,
        "scenario_id": result.scenario_id,
        "random_seed": result.random_seed,
        "strategy_name": result.strategy_name,
        "vehicle_count": len(result.vehicles),
        "timestep_count": len(result.timesteps),
        "overflow_event_count": len(result.overflow_events),
    }


@app.get("/api/v1/campuses/{campus_id}/simulation/{simulation_id}")
def get_simulation(campus_id: str, simulation_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    row = conn.execute(
        "SELECT * FROM simulation_runs WHERE campus_id=? AND run_id=?", (campus_id, simulation_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Simulation run '{simulation_id}' not found.")
    return _row_to_dict(row)


@app.get("/api/v1/campuses/{campus_id}/simulation/{simulation_id}/metrics")
def get_simulation_metrics(campus_id: str, simulation_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    row = conn.execute(
        "SELECT metrics_json, status FROM simulation_runs WHERE campus_id=? AND run_id=?",
        (campus_id, simulation_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Simulation run '{simulation_id}' not found.")
    if not row["metrics_json"]:
        raise HTTPException(status_code=409, detail=f"Simulation run '{simulation_id}' has not completed yet (status={row['status']}).")
    return json.loads(row["metrics_json"])


@app.get("/api/v1/campuses/{campus_id}/simulation/{simulation_id}/events")
def get_simulation_events(campus_id: str, simulation_id: str, conn=Depends(get_db)):
    _campus_exists(conn, campus_id)
    row = conn.execute(
        "SELECT overflow_events_json FROM simulation_runs WHERE campus_id=? AND run_id=?",
        (campus_id, simulation_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Simulation run '{simulation_id}' not found.")
    return {"overflow_events": json.loads(row["overflow_events_json"]) if row["overflow_events_json"] else []}
