"""
Phase 9 â€” API Functions for Member 4 (Platform)

Pure Python functions for FastAPI to wrap. No database coupling.
All functions are deterministic (seed â†’ identical results).
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from digital_twin.config_loader import load_campus_config
from digital_twin.graph_service import GraphService
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy, NearestAvailableStrategy
from digital_twin.simulation.state_snapshot import StateSnapshot
from digital_twin.db import get_connection, apply_migrations


# Module-level state (your FastAPI will manage this)
_graph_service = None
_engine = None
_conn = None


def init(db_path: str = ":memory:", configs_path: str = "configs"):
    """Initialize the simulation engine and database."""
    global _graph_service, _engine, _conn

    _conn = get_connection(db_path)
    apply_migrations(_conn)
    _graph_service = GraphService()
    _engine = SimulationEngine()


def load_campus(campus_id: str) -> dict:
    """
    Load campus configuration.

    Args:
        campus_id: e.g., "vitap", "sample"

    Returns:
        {gates, lots, roads, graph_edges, zones, event_types, ...}
    """
    config_path = Path("configs/campus") / f"{campus_id}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Campus config not found: {config_path}")

    load_campus_config(config_path, _conn)

    # Return summary
    return {
        "campus_id": campus_id,
        "config_path": str(config_path),
        "loaded": True,
    }


def run_simulation(scenario_dict: dict, strategy_name: str, seed: int) -> str:
    """
    Run a single simulation.

    Args:
        scenario_dict: scenario config (or path to YAML)
        strategy_name: "FirstAvailable", "NearestAvailable", or custom
        seed: random seed for reproducibility

    Returns:
        run_id for later queries
    """
    # Load scenario
    if isinstance(scenario_dict, str):
        scenario = ScenarioLoader.load(scenario_dict)
    else:
        scenario = ScenarioLoader.from_dict(scenario_dict)

    # Override seed if provided
    scenario.random_seed = seed

    # Select strategy
    if strategy_name == "FirstAvailable":
        strategy = FirstAvailableStrategy()
    elif strategy_name == "NearestAvailable":
        strategy = NearestAvailableStrategy()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    # Run
    result = _engine.run(scenario, strategy, _conn)

    # Result run_id is unique identifier
    return result.run_id


def run_batch(scenario_dict: dict, strategies: List[str], seeds: List[int]) -> List[str]:
    """
    Run multiple simulations in sequence.

    Args:
        scenario_dict: scenario config
        strategies: list of strategy names
        seeds: list of seeds

    Returns:
        List of run_ids
    """
    run_ids = []
    for strategy in strategies:
        for seed in seeds:
            run_id = run_simulation(scenario_dict, strategy, seed)
            run_ids.append(run_id)
    return run_ids


def get_metrics(run_id: str) -> dict:
    """
    Get simulation results (5 primary + secondary metrics).

    Args:
        run_id: from run_simulation()

    Returns:
        {primary_metrics, secondary_metrics, ...}
    """
    # Metrics are in runs/{scenario}/{strategy}/seed_{n}/metrics.json
    # You'll need to map run_id back to this path
    # For now, return template
    return {
        "run_id": run_id,
        "primary_metrics": {
            "avg_search_time_min": 0,
            "avg_waiting_time_min": 0,
            "avg_gate_queue_vehicles": 0,
            "max_gate_queue_vehicles": 0,
            "overflow_events_count": 0,
            "total_travel_time_veh_min": 0,
            "total_travel_distance_veh_km": 0,
        },
        "secondary_metrics": {
            "total_vehicles_simulated": 0,
            "parked_vehicles": 0,
            "rejected_vehicles": 0,
            "allocation_success_rate": 0.0,
        }
    }


def get_vehicles(run_id: str) -> List[dict]:
    """
    Get per-vehicle results for export/table.

    Args:
        run_id: from run_simulation()

    Returns:
        List of vehicle dicts: {vehicle_id, entry_gate, assigned_lot, search_time, ...}
    """
    # Load from runs/{scenario}/{strategy}/seed_{n}/vehicles.parquet or .json
    return []


def get_timeline(run_id: str) -> List[dict]:
    """
    Get full state timeline for dashboard animation.

    Args:
        run_id: from run_simulation()

    Returns:
        [{tick, occupancy_by_lot, queue_by_gate, events, ...}, ...]
    """
    # Load from runs/{scenario}/{strategy}/seed_{n}/intervals.parquet or .json
    return []


def get_state(run_id: str, tick: int) -> dict:
    """Alias: get campus state at a specific simulation tick."""
    return get_campus_state(run_id, tick)


def get_campus_state(run_id: str, tick: int) -> dict:
    """
    Get campus state at a specific tick (as StateSnapshot).

    Args:
        run_id: from run_simulation()
        tick: simulation tick (0â€“duration_minutes)

    Returns:
        StateSnapshot JSON-serializable dict
    """
    # Reconstruct state from timeline at tick
    return {
        "sim_time": tick,
        "sim_time_iso": "2026-10-04T12:00:00Z",
        "lots": [],
        "gates": [],
        "roads": [],
        "pending_arrivals_by_gate": {},
        "active_events": [],
        "active_disruptions": [],
    }


def export_geojson(campus_id: str) -> dict:
    """
    Export campus graph as GeoJSON for Leaflet map.

    Args:
        campus_id: e.g., "vitap"

    Returns:
        GeoJSON FeatureCollection
    """
    graph = _graph_service.build_graph(campus_id, _conn)

    features = []

    # Add nodes (gates, lots, junctions) as points
    for node, data in graph.nodes(data=True):
        if "coords" in data:
            lat, lon = data["coords"]
            feature = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "id": node,
                    "type": data.get("node_type", "junction"),
                    "name": data.get("name", node),
                }
            }
            features.append(feature)

    # Add edges (roads) as linestrings
    for u, v, data in graph.edges(data=True):
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        if "coords" in u_data and "coords" in v_data:
            u_lat, u_lon = u_data["coords"]
            v_lat, v_lon = v_data["coords"]
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[u_lon, u_lat], [v_lon, v_lat]]
                },
                "properties": {
                    "id": f"{u}-{v}",
                    "from": u,
                    "to": v,
                    "length_m": data.get("length_m", 0),
                    "status": data.get("status", "open"),
                }
            }
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def make_dataset(campus_id: str, scenario_paths: list, seeds: list, output_path: str) -> dict:
    """
    Export ML training dataset from simulation runs (for Member 2).

    Args:
        campus_id: e.g. "vitap"
        scenario_paths: list of YAML scenario paths to run
        seeds: list of random seeds per scenario
        output_path: path to write CSV (e.g. "data/ml_dataset.csv")

    Returns:
        {"rows": int, "columns": list, "path": str}
    """
    import csv
    from digital_twin.simulation.engine import SimulationEngine
    from digital_twin.simulation.scenario import ScenarioLoader
    from digital_twin.simulation.strategy import FirstAvailableStrategy
    from pathlib import Path

    engine = SimulationEngine()
    rows = []

    for scenario_path in scenario_paths:
        for seed in seeds:
            scenario = ScenarioLoader.load(scenario_path)
            scenario.campus_id = campus_id
            scenario.random_seed = seed
            result = engine.run(scenario, FirstAvailableStrategy(), _conn)
            for v in result.vehicles:
                rows.append({
                    "scenario_id": scenario.scenario_id,
                    "seed": seed,
                    "arrival_time": v.get("arrival_time"),
                    "assigned_lot_id": v.get("assigned_lot_id"),
                    "search_time_min": v.get("search_time_seconds", 0) / 60.0,
                    "wait_time_min": v.get("waiting_time_seconds", 0) / 60.0,
                    "final_state": v.get("final_state"),
                    "complied": v.get("complied"),
                    "travel_distance_m": v.get("outbound_distance_meters", 0),
                })

    columns = list(rows[0].keys()) if rows else []
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    return {"rows": len(rows), "columns": columns, "path": output_path}


def validate_scenario(scenario_dict: dict) -> Tuple[bool, List[str]]:
    """
    Validate scenario config.

    Args:
        scenario_dict: scenario config

    Returns:
        (is_valid, [error_messages])
    """
    try:
        scenario = ScenarioLoader.from_dict(scenario_dict)
        # Further validation
        errors = []
        return (len(errors) == 0, errors)
    except Exception as e:
        return (False, [str(e)])


def get_manifest(run_id: str) -> dict:
    """
    Get audit trail: config hash, git commit, seed, timestamps.

    Args:
        run_id: from run_simulation()

    Returns:
        {scenario_id, strategy, seed, config_hash, git_commit, recorded_at, ...}
    """
    # Load from runs/{scenario}/{strategy}/seed_{n}/manifest.json
    return {
        "run_id": run_id,
        "scenario_id": "unknown",
        "strategy_name": "unknown",
        "random_seed": 0,
        "config_hash": "unknown",
        "git_commit": "unknown",
        "recorded_at": "unknown",
    }
