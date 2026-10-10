"""
ParkingNav-X REST API
VIT-AP University Smart Parking Digital Twin
"""
from pathlib import Path
from typing import Optional
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy, NearestAvailableStrategy
from digital_twin.simulation.demo_strategies import PredictionOnlyStrategy, ParkingNavXFullStrategy

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "digital_twin.db"
CAMPUS_YAML = ROOT / "configs" / "campuses" / "vitap.yaml"
SCENARIO_DIR = ROOT / "configs" / "scenarios" / "vitap"

app = FastAPI(
    title="ParkingNav-X API",
    description="VIT-AP University Smart Parking Digital Twin — REST API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STRATEGIES = {
    "B1": FirstAvailableStrategy(),
    "B2": NearestAvailableStrategy(),
    "B3": PredictionOnlyStrategy(),
    "P":  ParkingNavXFullStrategy(),
}


def get_conn():
    conn = get_connection(DB_PATH)
    apply_migrations(conn)
    load_campus_config(CAMPUS_YAML, conn)
    return conn


# ── Models ────────────────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    scenario: str = "peak_hour"
    strategy: str = "P"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "project": "ParkingNav-X",
        "campus": "VIT-AP University, Amaravati, Andhra Pradesh",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/campus", tags=["Campus"])
def get_campus():
    """Return VIT-AP campus summary: gates, parking lots, roads."""
    conn = get_conn()
    gates = conn.execute("SELECT gate_id, name, capacity, status FROM gates WHERE campus_id='vitap'").fetchall()
    lots  = conn.execute("SELECT parking_lot_id, name, total_capacity, status FROM parking_lots WHERE campus_id='vitap'").fetchall()
    roads = conn.execute("SELECT road_id, name, length_meters, status FROM roads WHERE campus_id='vitap'").fetchall()
    dests = conn.execute("SELECT destination_id, name, category FROM destinations WHERE campus_id='vitap'").fetchall()
    conn.close()
    return {
        "campus_id": "vitap",
        "name": "VIT-AP University",
        "location": "Amaravati, Andhra Pradesh, India",
        "gates": [{"id": r[0], "name": r[1], "capacity": r[2], "status": r[3]} for r in gates],
        "parking_lots": [{"id": r[0], "name": r[1], "capacity": r[2], "status": r[3]} for r in lots],
        "roads": [{"id": r[0], "name": r[1], "length_m": r[2], "status": r[3]} for r in roads],
        "destinations": [{"id": r[0], "name": r[1], "category": r[2]} for r in dests],
    }


@app.get("/scenarios", tags=["Simulation"])
def list_scenarios():
    """List all available simulation scenarios."""
    files = sorted(SCENARIO_DIR.glob("*.yaml"))
    return {"scenarios": [f.stem for f in files]}


@app.get("/strategies", tags=["Simulation"])
def list_strategies():
    """List all available parking allocation strategies."""
    return {
        "strategies": [
            {"code": "B1", "name": "First Available",     "description": "Naive — assigns first open lot found"},
            {"code": "B2", "name": "Nearest Available",   "description": "Picks the closest open lot by distance"},
            {"code": "B3", "name": "Prediction Only",     "description": "Avoids nearly-full lots using fill-rate forecast"},
            {"code": "P",  "name": "ParkingNav-X (full)", "description": "Prediction + gate load balancing + zone routing"},
        ]
    }


@app.post("/simulate", tags=["Simulation"])
def simulate(req: SimulateRequest):
    """
    Run a parking simulation scenario with a chosen strategy.

    - **scenario**: e.g. `peak_hour`, `E1_normal_day`, `parking_full`, `E4_gate_closure`
    - **strategy**: `B1`, `B2`, `B3`, or `P`
    """
    scenario_file = SCENARIO_DIR / f"{req.scenario}.yaml"
    if not scenario_file.exists():
        available = [f.stem for f in SCENARIO_DIR.glob("*.yaml")]
        raise HTTPException(status_code=404, detail=f"Scenario '{req.scenario}' not found. Available: {available}")

    strategy = STRATEGIES.get(req.strategy)
    if not strategy:
        raise HTTPException(status_code=400, detail=f"Strategy must be one of: {list(STRATEGIES.keys())}")

    conn = get_conn()
    scenario = ScenarioLoader.load(scenario_file)
    engine = SimulationEngine()
    run_id = f"api-{uuid.uuid4().hex[:8]}"
    result = engine.run(scenario, strategy, conn, run_id=run_id)
    conn.close()

    m = result.metrics
    return {
        "run_id": run_id,
        "scenario": req.scenario,
        "strategy": req.strategy,
        "campus": "vitap",
        "duration_min": scenario.duration_minutes,
        "vehicles": scenario.vehicle_count,
        "metrics": {
            "total_vehicles":       m.get("total_vehicles"),
            "parked_vehicles":      m.get("parked_vehicles"),
            "completed_trips":      m.get("completed_vehicles"),
            "overflow_events":      m.get("overflow_events_count"),
            "avg_search_time_min":  round(m["avg_search_time_min"], 2) if m.get("avg_search_time_min") else None,
            "avg_wait_time_min":    round(m["avg_wait_time_min"], 2)   if m.get("avg_wait_time_min")   else None,
            "avg_gate_queue":       round(m["avg_gate_queue"], 2)      if m.get("avg_gate_queue")      else None,
            "peak_gate_queue":      m.get("max_gate_queue"),
        },
    }


@app.get("/compare/{scenario}", tags=["Simulation"])
def compare_strategies(scenario: str):
    """
    Run all 4 strategies on a scenario and return side-by-side comparison.

    - **scenario**: e.g. `peak_hour`, `E1_normal_day`, `parking_full`
    """
    scenario_file = SCENARIO_DIR / f"{scenario}.yaml"
    if not scenario_file.exists():
        available = [f.stem for f in SCENARIO_DIR.glob("*.yaml")]
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found. Available: {available}")

    conn = get_conn()
    results = {}
    for code, strategy in STRATEGIES.items():
        sc = ScenarioLoader.load(scenario_file)
        engine = SimulationEngine()
        run_id = f"api-cmp-{uuid.uuid4().hex[:6]}"
        result = engine.run(sc, strategy, conn, run_id=run_id)
        m = result.metrics
        results[code] = {
            "overflow_events":     m.get("overflow_events_count"),
            "avg_search_time_min": round(m["avg_search_time_min"], 2) if m.get("avg_search_time_min") else None,
            "avg_wait_time_min":   round(m["avg_wait_time_min"], 2)   if m.get("avg_wait_time_min")   else None,
            "avg_gate_queue":      round(m["avg_gate_queue"], 2)      if m.get("avg_gate_queue")      else None,
            "peak_gate_queue":     m.get("max_gate_queue"),
        }
    conn.close()
    return {"scenario": scenario, "comparison": results}


@app.get("/events", tags=["Campus"])
def get_events():
    """List all campus events loaded from vitap_events.csv."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT event_id, event_type, name, start_time, end_time, status FROM events WHERE campus_id='vitap'"
    ).fetchall()
    conn.close()
    return {
        "campus": "vitap",
        "events": [
            {"id": r[0], "type": r[1], "name": r[2], "start": r[3], "end": r[4], "status": r[5]}
            for r in rows
        ],
    }
