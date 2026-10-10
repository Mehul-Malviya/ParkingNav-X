"""
Phase 9 â€” API Functions for Member 4 (Platform)

Pure Python functions for FastAPI to wrap. No database coupling.
All functions are deterministic (seed â†’ identical results).
"""

from pathlib import Path
from typing import List, Tuple

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.graph_service import CampusGraphService
from digital_twin.simulation.demo_strategies import ParkingNavXFullStrategy, PredictionOnlyStrategy
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy, NearestAvailableStrategy

# Module-level state (your FastAPI will manage this)
_graph_service = None
_engine = None
_conn = None
_results: dict = {}  # run_id -> SimulationResult
_run_context: dict = {}  # run_id -> {"scenario": ScenarioConfig, "campus_id": str}

# Strategy registry. Member 3 plugs a strategy in with register_strategy("MyStrategy", MyStrategy)
# (a zero-argument factory returning an AllocationStrategy) -- no edit to this file needed.
_STRATEGIES: dict = {
    "FirstAvailable": FirstAvailableStrategy,
    "NearestAvailable": NearestAvailableStrategy,
    "B1": FirstAvailableStrategy,
    "B2": NearestAvailableStrategy,
    "B3": PredictionOnlyStrategy,       # demo stand-in (no real forecast yet)
    "B4": ParkingNavXFullStrategy,      # demo stand-in
}


def register_strategy(name: str, factory) -> None:
    """Make a strategy available to run_simulation / run_batch under `name`."""
    _STRATEGIES[name] = factory


def init(db_path: str = ":memory:", configs_path: str = "configs"):
    """Initialize the simulation engine and database."""
    global _graph_service, _engine, _conn

    _conn = get_connection(db_path)
    apply_migrations(_conn)
    _graph_service = CampusGraphService()
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

    # Select strategy (built-ins + anything registered via register_strategy)
    factory = _STRATEGIES.get(strategy_name)
    if factory is None:
        raise ValueError(f"Unknown strategy: {strategy_name!r}. Available: {sorted(_STRATEGIES)}")
    strategy = factory()

    # Auto-initialize with defaults if init() was never called
    if _engine is None:
        init()
        load_campus(scenario.campus_id)

    # Run
    result = _engine.run(scenario, strategy, _conn)
    _results[result.run_id] = result
    _run_context[result.run_id] = {"scenario": scenario, "campus_id": scenario.campus_id}

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
    result = _results.get(run_id)
    if result is None:
        raise KeyError(f"No result found for run_id={run_id!r}. Call run_simulation() first.")

    vehicles = result.vehicles
    total = len(vehicles)
    parked = sum(1 for v in vehicles if v.get("final_state") == "parked")
    exited = sum(1 for v in vehicles if v.get("final_state") == "exited")
    rejected = sum(1 for v in vehicles if v.get("final_state") == "rejected")
    success_rate = (parked + exited) / total if total else 0.0

    m = result.metrics
    return {
        "run_id": run_id,
        "primary_metrics": {
            "avg_search_time_min": m.get("avg_search_time_min", 0),
            "avg_waiting_time_min": m.get("avg_wait_time_min", 0),
            "avg_gate_queue_vehicles": m.get("avg_gate_queue", 0),
            "max_gate_queue_vehicles": m.get("max_gate_queue", 0),
            "overflow_events_count": len(result.overflow_events),
            "total_travel_time_veh_min": m.get("total_travel_time_min", 0),
            "total_travel_distance_veh_km": m.get("total_travel_distance_km", 0),
        },
        "secondary_metrics": {
            "total_vehicles_simulated": total,
            "parked_vehicles": parked,
            "exited_vehicles": exited,
            "rejected_vehicles": rejected,
            "allocation_success_rate": round(success_rate, 4),
            # From the engine's own conservation check (entered = queued + driving + searching + parked
            # + departing + exited + rejected); not recomputed here.
            "conservation_check": result.secondary_metrics["conservation_check"],
            "in_system_breakdown": result.secondary_metrics["in_system_breakdown"],
        },
    }


def _result_for(run_id: str):
    result = _results.get(run_id)
    if result is None:
        raise KeyError(f"No result found for run_id={run_id!r}. Call run_simulation() first.")
    return result


def get_vehicles(run_id: str) -> List[dict]:
    """
    Per-vehicle records for a run (JSON-serializable dicts): vehicle_id, entry_gate, destination_id,
    arrival_tick (minutes), arrival_time, search/waiting/travel times (s), travel_distance_meters,
    assigned_lot_id, final_state, internal_state, complied, vehicle_type, reassigned_count,
    state_trace [{tick (min), t_sec, state}], ...
    """
    return [dict(v) for v in _result_for(run_id).vehicles]


def get_timeline(run_id: str) -> List[dict]:
    """
    Full per-minute timeline for dashboard animation:
    [{tick, occupancy_by_lot, queue_by_gate, road_load_by_road, overflow_by_lot}, ...]
    """
    out = []
    for ts in _result_for(run_id).timesteps:
        out.append({
            "tick": ts["tick"],
            "occupancy_by_lot": {k[len("parking_occupancy_"):]: v for k, v in ts.items() if k.startswith("parking_occupancy_")},
            "queue_by_gate": {k[len("gate_queue_"):]: v for k, v in ts.items() if k.startswith("gate_queue_")},
            "road_load_by_road": {k[len("road_load_"):]: v for k, v in ts.items() if k.startswith("road_load_")},
            "overflow_by_lot": {k[len("overflow_"):]: v for k, v in ts.items() if k.startswith("overflow_")},
        })
    return out


def get_state(run_id: str, tick: int) -> dict:
    """Alias: get campus state at a specific simulation tick."""
    return get_campus_state(run_id, tick)


def get_campus_state(run_id: str, tick: int) -> dict:
    """
    Campus state at `tick` (minutes since scenario start) as a StateSnapshot dict, rebuilt from the
    stored run: lots/gates/roads from the per-minute timeline, vehicles from their state traces.

    Keys: sim_time, sim_time_iso, scenario_id, seed, lots, gates, roads, pending_arrivals_by_gate
    (arrivals scheduled in the next 5 minutes), active_events, active_disruptions,
    travel_time_matrix [gate][lot] (seconds, free-flow), walk_time ({} -- no walking model),
    forecast (None), vehicles, event_log.
    """
    return _build_snapshot(run_id, tick).to_dict()


def _build_snapshot(run_id: str, tick: int):
    from datetime import datetime, timedelta, timezone

    import networkx as nx

    from digital_twin.simulation.state_snapshot import (
        EventState,
        GateState,
        LotState,
        RoadState,
        StateSnapshot,
        VehicleState,
        VehicleStateEnum,
    )

    result = _result_for(run_id)
    ctx = _run_context.get(run_id)
    if ctx is None:
        raise KeyError(f"No scenario context for run_id={run_id!r}.")
    scenario = ctx["scenario"]
    timesteps = result.timesteps
    if not 0 <= tick < len(timesteps):
        raise ValueError(f"tick {tick} out of range 0..{len(timesteps) - 1}")
    ts = timesteps[tick]

    lots_cfg = SimulationEngine._load_parking_lots(scenario.campus_id, _conn, scenario.availability_overrides)
    gates_cfg = SimulationEngine._load_gates(scenario.campus_id, _conn, scenario.availability_overrides)
    road_rows = {r["road_id"]: dict(r) for r in _conn.execute("SELECT * FROM roads WHERE campus_id=?", (scenario.campus_id,))}
    timed = (scenario.availability_overrides or {}).get("timed_closures", [])
    closed_now = {(c["entity_type"], c["entity_id"]) for c in timed if c["start_tick"] <= tick < c.get("end_tick", 10 ** 9)}

    def occ_delta(lot_id, window):
        key = f"parking_occupancy_{lot_id}"
        series = [timesteps[t][key] for t in range(max(0, tick - window), tick + 1)]
        up = sum(max(0, b - a) for a, b in zip(series, series[1:]))
        down = sum(max(0, a - b) for a, b in zip(series, series[1:]))
        return up, down

    lots = []
    for lot_id, cfg in lots_cfg.items():
        occ = ts.get(f"parking_occupancy_{lot_id}", 0)
        cap = cfg["usable_capacity"]
        in5, out5 = occ_delta(lot_id, 5)
        in15, out15 = occ_delta(lot_id, 15)
        if cfg["status"] == "closed" or ("parking_lot", lot_id) in closed_now:
            status = "closed"
        else:
            status = "full" if occ >= cap else "open"
        lots.append(LotState(id=lot_id, capacity=cap, occupied=occ, available=max(0, cap - occ), reserved_free=0,
                             status=status, inflow_5m=in5, outflow_5m=out5, arrivals_last_15m=in15, departures_last_15m=out15))

    admitted_by_gate = {}
    for v in result.vehicles:
        if v.get("gate_admitted_tick") is not None:
            admitted_by_gate.setdefault(v["entry_gate"], []).append(v)
    gates = []
    for gate_id, cfg in gates_cfg.items():
        adm = admitted_by_gate.get(gate_id, [])
        t5 = sum(1 for v in adm if tick - 5 < v["gate_admitted_tick"] <= tick)
        t15 = [v for v in adm if tick - 15 < v["gate_admitted_tick"] <= tick]
        waits = [v["waiting_time_seconds"] for v in t15]
        closed = cfg["status"] == "closed" or ("gate", gate_id) in closed_now
        gates.append(GateState(id=gate_id, queue_length=ts.get(f"gate_queue_{gate_id}", 0),
                               service_rate_veh_per_min=float(cfg["capacity"]), status="closed" if closed else "open",
                               throughput_last_5min=t5, throughput_last_15m=len(t15),
                               avg_wait_sec_last_15m=(sum(waits) / len(waits)) if waits else 0.0))

    graph = CampusGraphService().build_graph(scenario.campus_id, _conn)
    edge_by_road = {}
    for u, v_, d in graph.edges(data=True):
        if d.get("road_id") and d["road_id"] not in edge_by_road:
            edge_by_road[d["road_id"]] = d

    roads = []
    for road_id, row in road_rows.items():
        load = ts.get(f"road_load_{road_id}", 0)
        edge = edge_by_road.get(road_id, {})
        cap = int(edge.get("capacity") or 20)   # same default the engine's BPR uses
        ratio = load / cap if cap else 0.0
        level = "low" if ratio < 0.5 else ("med" if ratio < 1.0 else "high")
        closed = ("road", road_id) in closed_now or row.get("status") == "closed"
        travel = row.get("expected_travel_time_seconds") or edge.get("weight_time_seconds") or 0.0
        roads.append(RoadState(id=road_id, travel_time_sec=float(travel), congestion_ratio=ratio,
                               status="closed" if closed else "open", current_load=load, capacity=cap,
                               congestion_level=level))

    pending = {g: 0 for g in gates_cfg}
    for v in result.vehicles:
        if tick < v["arrival_tick"] <= tick + 5:
            pending[v["entry_gate"]] = pending.get(v["entry_gate"], 0) + 1

    ec = scenario.event_conditions or {}
    events = []
    if ec and ec.get("start_tick", 0) <= tick < ec.get("start_tick", 0) + ec.get("duration_ticks", 0):
        end = ec["start_tick"] + ec["duration_ticks"]
        events.append(EventState(event_id=scenario.name or scenario.scenario_id, start_tick=ec["start_tick"],
                                 duration_ticks=ec["duration_ticks"], demand_multiplier=ec.get("demand_multiplier", 1.0),
                                 affected_zones=list(ec.get("affected_zones", [])), minutes_remaining=end - tick))
    disruptions = [{"entity_type": t, "entity_id": e, "kind": "timed_closure"} for t, e in sorted(closed_now)]
    ov = scenario.availability_overrides or {}
    for key, etype in (("closed_gates", "gate"), ("closed_parking_lots", "parking_lot"), ("closed_roads", "road")):
        disruptions += [{"entity_type": etype, "entity_id": e, "kind": "closed_for_run"} for e in ov.get(key, [])]

    ttm = {}
    for g in gates_cfg:
        ttm[g] = {}
        for lot_id in lots_cfg:
            try:
                ttm[g][lot_id] = float(nx.shortest_path_length(graph, g, lot_id, weight="weight_time_seconds"))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                ttm[g][lot_id] = float("inf")

    vehicle_states = []
    now_sec = (tick + 1) * 60 - 1
    for v in result.vehicles:
        if v["arrival_tick"] > tick:
            continue
        seen = [e for e in v.get("state_trace", []) if e["t_sec"] <= now_sec]
        state = VehicleStateEnum(seen[-1]["state"]) if seen else VehicleStateEnum.SCHEDULED
        vehicle_states.append(VehicleState(
            id=v["vehicle_id"], vehicle_type=v.get("vehicle_type", "general"), arrival_time=v["arrival_tick"],
            entry_gate=v["entry_gate"], destination_zone=v.get("destination_id") or "", assigned_lot=v.get("assigned_lot_id"),
            route=[], state=state, timestamps={e["state"]: e["t_sec"] for e in seen},
            search_time=v["search_time_seconds"] / 60.0, wait_time=v["waiting_time_seconds"] / 60.0,
            travel_time=v["travel_time_seconds"] / 60.0, distance_m=float(v["travel_distance_meters"]),
            reassigned_count=v["reassigned_count"]))

    base = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=scenario.start_time_min + tick)
    return StateSnapshot(
        sim_time=tick, sim_time_iso=base.isoformat(), lots=lots, gates=gates, roads=roads,
        pending_arrivals_by_gate=pending, active_events=events, active_disruptions=disruptions,
        travel_time_matrix=ttm, walk_time={}, forecast=None, scenario_id=scenario.scenario_id,
        seed=scenario.random_seed, vehicles=vehicle_states,
        event_log=[e for e in result.overflow_events if e["tick"] <= tick])


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
    from pathlib import Path

    from digital_twin.simulation.engine import SimulationEngine
    from digital_twin.simulation.scenario import ScenarioLoader
    from digital_twin.simulation.strategy import FirstAvailableStrategy

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
                    "travel_distance_m": v.get("travel_distance_meters", 0),
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
        ScenarioLoader.from_dict(scenario_dict)
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
