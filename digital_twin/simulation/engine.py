"""
Part 4 (+ Part 5's occupancy/queue refinements): deterministic discrete-time
Simulation Engine.

Determinism is non-negotiable: one seeded random.Random instance is created
per run and threaded through every random decision -- arrivals, gate/
destination choice, dwell time. No unseeded randomness anywhere.

The engine contains no allocation decision logic. It calls the injected
AllocationStrategy exactly once per vehicle at the parking_search step, then
enforces Part 1's real constraints itself (closed/full lot, closed/blocked
road, gate throughput) regardless of what the strategy returned.

Simplification, documented rather than hidden: road_load is attributed to a
vehicle's route once, at the tick its transit begins, not re-added on every
subsequent tick of a multi-minute transit. This keeps the per-timestep
road_load metric transparent and deterministic; a finer-grained "vehicle is
occupying this edge for N ticks" model is a drop-in replacement later.
"""

import json
import random
import signal
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import networkx as nx

from digital_twin.simulation.metrics_recorder import MetricsRecorder

from digital_twin.graph_service import CampusGraphService
from digital_twin.simulation.scenario import ScenarioConfig
from digital_twin.simulation.strategy import AllocationStrategy, AssignmentResult, CampusState, Vehicle, NearestAvailableStrategy
from digital_twin.twin_service import DigitalTwinService

DWELL_MINUTES_RANGE = (20, 180)
STRATEGY_TIMEOUT_MS = 1000  # 1 second timeout for strategy.assign()


class StrategyTimeoutError(Exception):
    """Raised when strategy exceeds time budget."""
    pass


@dataclass
class _RunningVehicle:
    vehicle: Vehicle
    state: str = "arrival"  # arrival, gate_queue, campus_entry, route, parking_search,
                              # parking_assignment, parked, departure, completed
    queue_enter_tick: Optional[int] = None
    gate_admitted_tick: Optional[int] = None
    search_start_tick: Optional[int] = None
    search_end_tick: Optional[int] = None
    assigned_lot_id: Optional[str] = None
    dwell_minutes: int = 0
    remaining_transit_minutes: float = 0.0
    outbound_route_computed: bool = False
    outbound_distance_meters: float = 0.0
    inbound_distance_meters: float = 0.0
    completion_tick: Optional[int] = None


@dataclass
class SimulationResult:
    run_id: str
    campus_id: str
    scenario_id: str
    random_seed: int
    strategy_name: str
    vehicles: list = field(default_factory=list)     # list of per-vehicle metric dicts
    timesteps: list = field(default_factory=list)    # list of per-timestep metric dicts
    overflow_events: list = field(default_factory=list)
    infeasibility_rejections: int = 0                # count of assignments rejected due to infeasibility
    adapter_fallbacks: int = 0                       # count of fallbacks to B2 due to timeout/exception


def _congestion_level(load: int, capacity) -> str:
    """Matches Part 3's exact enum: free|moderate|heavy|blocked."""
    if not capacity or capacity <= 0:
        return "free"
    ratio = load / capacity
    if ratio == 0:
        return "free"
    if ratio < 0.5:
        return "moderate"
    if ratio < 1.0:
        return "heavy"
    return "blocked"


def _arrival_rate_at(profile: dict, t: int) -> float:
    if profile["type"] == "constant":
        return profile["rate"]
    points = sorted(profile["points"], key=lambda p: p["time"])
    if t <= points[0]["time"]:
        return points[0]["rate"]
    if t >= points[-1]["time"]:
        return points[-1]["rate"]
    for i in range(len(points) - 1):
        t0, t1 = points[i]["time"], points[i + 1]["time"]
        if t0 <= t <= t1:
            r0, r1 = points[i]["rate"], points[i + 1]["rate"]
            frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
            return r0 + frac * (r1 - r0)
    return points[-1]["rate"]


class SimulationEngine:
    def __init__(self, graph_service: Optional[CampusGraphService] = None,
                 twin_service: Optional[DigitalTwinService] = None):
        self.graph_service = graph_service or CampusGraphService()
        self.twin_service = twin_service or DigitalTwinService()

    def run(self, scenario: ScenarioConfig, strategy: AllocationStrategy, conn,
            run_id: Optional[str] = None) -> SimulationResult:
        rng = random.Random(scenario.random_seed)  # the ONE seeded RNG for this entire run

        run_id = run_id or f"{scenario.scenario_id}-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc).isoformat()
        strategy_name = f"{strategy.__class__.__module__}.{strategy.__class__.__name__}"

        conn.execute(
            """INSERT INTO simulation_runs (run_id, campus_id, scenario_id, random_seed, strategy_name,
                 configuration_version, started_at, status)
               VALUES (?, ?, ?, ?, ?, (SELECT active_configuration_version FROM campuses WHERE campus_id=?), ?, 'running')""",
            (run_id, scenario.campus_id, scenario.scenario_id, scenario.random_seed, strategy_name,
             scenario.campus_id, started_at),
        )
        conn.commit()

        graph = self.graph_service.build_graph(scenario.campus_id, conn)
        working_graph = self._apply_availability_overrides(graph, scenario)

        gates = self._load_gates(scenario.campus_id, conn, scenario.availability_overrides)
        parking_lots = self._load_parking_lots(scenario.campus_id, conn, scenario.availability_overrides)
        destinations = self._load_destination_ids(scenario.campus_id, conn)
        roads = self._load_roads(scenario.campus_id, conn)

        open_gate_ids = [g for g, d in gates.items() if d["status"] == "open"]
        open_lot_ids = [p for p, d in parking_lots.items() if d["status"] == "open"]

        running_vehicles = self._generate_arrivals(scenario, rng, open_gate_ids, destinations)
        gate_queues = {g: [] for g in gates}  # FIFO lists of vehicle_ids
        by_id = {rv.vehicle.vehicle_id: rv for rv in running_vehicles}

        timesteps_metrics = []
        overflow_events = []
        road_load = {r: 0 for r in roads}
        decision_latencies = []  # log (tick, latency_ms)
        infeasibility_rejections = 0  # count of assignments rejected as infeasible
        adapter_fallbacks = 0  # count of fallbacks to B2

        for tick in range(scenario.duration_minutes):
            # Decision cycle: every 5 minutes, call strategy.update_policy()
            if tick % 5 == 0:
                decision_start = datetime.now(timezone.utc)
                state_snapshot = self.twin_service.get_current_state(scenario.campus_id, conn, now=decision_start)
                strategy.update_policy(state_snapshot, forecast=None)  # No forecast yet (Member 2's job)
                decision_latency_ms = (datetime.now(timezone.utc) - decision_start).total_seconds() * 1000
                decision_latencies.append({"tick": tick, "latency_ms": round(decision_latency_ms, 2)})
            for rv in running_vehicles:
                if rv.vehicle.arrival_tick == tick and rv.state == "arrival":
                    if rv.vehicle.entry_gate in open_gate_ids:
                        rv.state = "gate_queue"
                        rv.queue_enter_tick = tick
                        gate_queues[rv.vehicle.entry_gate].append(rv.vehicle.vehicle_id)
                    else:
                        rv.state = "completed"  # closed gate: never enters, matches spec's requirement

            for gate_id in open_gate_ids:
                throughput = gates[gate_id]["capacity"]
                admitted = 0
                queue = gate_queues[gate_id]
                while queue and admitted < throughput:
                    vehicle_id = queue.pop(0)  # FIFO
                    rv = by_id[vehicle_id]
                    rv.state = "campus_entry"
                    rv.gate_admitted_tick = tick
                    admitted += 1

            for rv in running_vehicles:
                if rv.state == "campus_entry":
                    rv.state = "route"
                elif rv.state == "route":
                    lot_candidate = self._route_target(rv.vehicle.destination_id, destinations, parking_lots, open_lot_ids)
                    if lot_candidate is None or not nx.has_path(working_graph, rv.vehicle.entry_gate, lot_candidate):
                        rv.state = "completed"  # no feasible route at all
                        continue
                    path = nx.shortest_path(working_graph, rv.vehicle.entry_gate, lot_candidate, weight="weight_time_seconds")
                    for a, b in zip(path, path[1:]):
                        road_id = working_graph.edges[a, b].get("road_id")
                        if road_id in road_load:
                            road_load[road_id] += 1
                    distance = nx.shortest_path_length(working_graph, rv.vehicle.entry_gate, lot_candidate, weight="weight_distance_meters")
                    travel_time = nx.shortest_path_length(working_graph, rv.vehicle.entry_gate, lot_candidate, weight="weight_time_seconds")
                    rv.remaining_transit_minutes = max(1.0, travel_time / 60.0)
                    rv.outbound_distance_meters = distance
                    rv.state = "parking_search"
                    rv.search_start_tick = tick

                elif rv.state == "parking_search":
                    rv.remaining_transit_minutes -= 1
                    if rv.remaining_transit_minutes > 0:
                        continue

                    state_view = CampusState(
                        campus_id=scenario.campus_id, graph=working_graph,
                        parking_lots={k: dict(v) for k, v in parking_lots.items()},
                        gates={k: dict(v) for k, v in gates.items()},
                        roads={k: dict(v) for k, v in roads.items()},
                    )

                    # Compliance-based assignment: strategy vs. nearest-lot
                    fallback_reason = None
                    if rv.vehicle.complies_with_strategy:
                        result, fallback_reason = self._assign_with_adapter(
                            strategy, rv.vehicle, state_view, parking_lots, open_lot_ids, working_graph
                        )
                        if fallback_reason:
                            adapter_fallbacks += 1
                    else:
                        # Non-compliant: go to nearest available lot
                        nearest = self._nearest_available_lot(
                            rv.vehicle.entry_gate, open_lot_ids, parking_lots, working_graph
                        )
                        result = AssignmentResult(parking_lot_id=nearest)
                    rv.search_end_tick = tick

                    lot = parking_lots.get(result.parking_lot_id) if result else None
                    feasible = (
                        lot is not None and lot["status"] == "open"
                        and lot["occupied_spaces"] < lot["usable_capacity"]
                    )

                    # Feasibility guard: verify assignment against live twin state
                    if result and not feasible:
                        infeasibility_rejections += 1
                        rv.state = "completed"  # failed assignment; no retry
                        overflow_events.append({"tick": tick, "parking_lot_id": result.parking_lot_id, "reason": "infeasible"})
                        continue

                    if feasible:
                        lot["occupied_spaces"] += 1
                        rv.assigned_lot_id = result.parking_lot_id
                        rv.dwell_minutes = rng.randint(*DWELL_MINUTES_RANGE)
                        rv.remaining_transit_minutes = rv.dwell_minutes
                        rv.state = "parked"
                        self.twin_service.update_parking_state(
                            scenario.campus_id, result.parking_lot_id, lot["occupied_spaces"],
                            "simulation", "SYNTHETIC", datetime.now(timezone.utc).isoformat(), conn,
                            commit=False,
                        )
                    else:
                        requested_lot = result.parking_lot_id if result else None
                        overflow_events.append({"tick": tick, "parking_lot_id": requested_lot})
                        rv.state = "completed"  # failed assignment; not retried automatically (no decision logic here)

                elif rv.state == "parked":
                    rv.remaining_transit_minutes -= 1
                    if rv.remaining_transit_minutes <= 0:
                        lot = parking_lots[rv.assigned_lot_id]
                        # Part 5's one intentional clamp: internal consistency guard only.
                        lot["occupied_spaces"] = max(0, lot["occupied_spaces"] - 1)
                        self.twin_service.update_parking_state(
                            scenario.campus_id, rv.assigned_lot_id, lot["occupied_spaces"],
                            "simulation", "SYNTHETIC", datetime.now(timezone.utc).isoformat(), conn,
                            commit=False,
                        )
                        if nx.has_path(working_graph, rv.assigned_lot_id, rv.vehicle.entry_gate):
                            distance = nx.shortest_path_length(working_graph, rv.assigned_lot_id, rv.vehicle.entry_gate, weight="weight_distance_meters")
                            travel_time = nx.shortest_path_length(working_graph, rv.assigned_lot_id, rv.vehicle.entry_gate, weight="weight_time_seconds")
                            rv.inbound_distance_meters = distance
                            rv.remaining_transit_minutes = max(1.0, travel_time / 60.0)
                        else:
                            rv.remaining_transit_minutes = 1.0
                        rv.state = "departure"

                elif rv.state == "departure":
                    rv.remaining_transit_minutes -= 1
                    if rv.remaining_transit_minutes <= 0:
                        rv.state = "completed"
                        rv.completion_tick = tick

            for gate_id, queue in gate_queues.items():
                gates[gate_id]["queue_length"] = len(queue)

            now_iso = datetime.now(timezone.utc).isoformat()
            for gate_id, gate in gates.items():
                self.twin_service.update_gate_state(
                    scenario.campus_id, gate_id, gate["queue_length"], 0,
                    "simulation", "SYNTHETIC", now_iso, conn, commit=False,
                )
            for road_id, load in road_load.items():
                road_capacity = roads[road_id].get("capacity")
                self.twin_service.update_road_state(
                    scenario.campus_id, road_id, load, _congestion_level(load, road_capacity),
                    "simulation", "SYNTHETIC", now_iso, conn, commit=False,
                )
            for rv in running_vehicles:
                if rv.state not in ("arrival",):  # only persist vehicles that have actually started their lifecycle
                    self.twin_service.update_vehicle_state(
                        scenario.campus_id, rv.vehicle.vehicle_id, rv.state, "simulation", now_iso, conn,
                        destination_id=rv.vehicle.destination_id,
                        assigned_parking_lot_id=rv.assigned_lot_id,
                        commit=False,
                    )
            conn.commit()  # one batched commit per tick instead of one per write

            overflow_this_tick = {e["parking_lot_id"] for e in overflow_events if e["tick"] == tick}
            timesteps_metrics.append({
                "tick": tick,
                **{f"gate_queue_{g}": gates[g]["queue_length"] for g in gates},
                **{f"parking_occupancy_{p}": parking_lots[p]["occupied_spaces"] for p in parking_lots},
                **{f"overflow_{p}": p in overflow_this_tick for p in parking_lots},
                **{f"road_load_{r}": road_load[r] for r in roads},
            })
            road_load = {r: 0 for r in road_load}

        vehicle_metrics = []
        for rv in running_vehicles:
            waiting_time = ((rv.gate_admitted_tick - rv.queue_enter_tick) * 60) if rv.gate_admitted_tick and rv.queue_enter_tick else 0
            search_time = ((rv.search_end_tick - rv.search_start_tick) * 60) if rv.search_end_tick and rv.search_start_tick else 0
            vehicle_metrics.append({
                "vehicle_id": rv.vehicle.vehicle_id,
                "entry_gate": rv.vehicle.entry_gate,
                "destination_id": rv.vehicle.destination_id,
                "search_time_seconds": search_time,
                "waiting_time_seconds": waiting_time,
                "travel_time_seconds": (rv.completion_tick - rv.vehicle.arrival_tick) * 60 if rv.completion_tick else None,
                "travel_distance_meters": rv.outbound_distance_meters + rv.inbound_distance_meters,
                "assigned_lot_id": rv.assigned_lot_id,
                "final_state": rv.state,
            })

        completed_at = datetime.now(timezone.utc).isoformat()
        summary_metrics = {
            "total_vehicles": len(vehicle_metrics),
            "completed_vehicles": sum(1 for v in vehicle_metrics if v["final_state"] == "completed"),
            "parked_vehicles": sum(1 for v in vehicle_metrics if v["final_state"] == "parked"),
            "failed_vehicles": len(overflow_events),
            "peak_occupancy_by_lot": {
                lot_id: max((ts.get(f"parking_occupancy_{lot_id}", 0) for ts in timesteps_metrics), default=0)
                for lot_id in parking_lots
            },
        }
        conn.execute(
            "UPDATE simulation_runs SET completed_at=?, status='completed', metrics_json=?, overflow_events_json=? WHERE run_id=?",
            (completed_at, json.dumps(summary_metrics), json.dumps(overflow_events), run_id),
        )
        conn.commit()

        # Record metrics to disk (Phase 8)
        recorder = MetricsRecorder()
        try:
            recorder.record_run(
                scenario_id=scenario.scenario_id,
                strategy_name=strategy_name,
                seed=scenario.random_seed,
                vehicle_metrics=vehicle_metrics,
                timestep_metrics=timesteps_metrics,
                overflow_events=overflow_events,
                config_dict={"campus_id": scenario.campus_id},
                decision_latencies=decision_latencies,
            )
        except Exception as e:
            print(f"Warning: metrics recording failed: {e}")

        return SimulationResult(
            run_id=run_id, campus_id=scenario.campus_id, scenario_id=scenario.scenario_id,
            random_seed=scenario.random_seed, strategy_name=strategy_name,
            vehicles=vehicle_metrics, timesteps=timesteps_metrics, overflow_events=overflow_events,
            infeasibility_rejections=infeasibility_rejections, adapter_fallbacks=adapter_fallbacks,
        ) # decision_latencies logged above, available for analysis

    @staticmethod
    def _generate_arrivals(scenario: ScenarioConfig, rng: random.Random, open_gate_ids, destination_ids) -> list:
        """Deterministic given rng: arrival ticks are weighted by the
        scenario's arrival_rate_profile shape, event-aware demand multiplier,
        entry gate and destination are chosen uniformly via the same seeded rng.

        Event-aware demand: if event_conditions exists, applies its demand_multiplier
        to the arrival rate profile during the event window."""
        ticks = list(range(scenario.duration_minutes))

        # Base arrival rate per tick
        weights = [max(0.0001, _arrival_rate_at(scenario.arrival_rate_profile, t)) for t in ticks]

        # Apply event-aware demand multiplier if event is active
        if scenario.event_conditions:
            multiplier = scenario.event_conditions.get("demand_multiplier", 1.0)
            event_start = scenario.event_conditions.get("start_tick", 0)
            event_duration = scenario.event_conditions.get("duration_ticks", 0)
            event_end = event_start + event_duration
            for t in ticks:
                if event_start <= t < event_end:
                    weights[t] *= multiplier

        vehicles = []
        if not open_gate_ids or scenario.vehicle_count == 0:
            return vehicles

        arrival_ticks = sorted(rng.choices(ticks, weights=weights, k=scenario.vehicle_count))
        for i, tick in enumerate(arrival_ticks):
            gate_id = rng.choice(sorted(open_gate_ids))
            destination_id = rng.choice(sorted(destination_ids)) if destination_ids else None
            compliance = rng.random() < scenario.event_conditions.get("compliance_rate", 0.85) if scenario.event_conditions else True
            vehicles.append(_RunningVehicle(
                vehicle=Vehicle(
                    vehicle_id=f"{scenario.scenario_id}-v{i}",
                    entry_gate=gate_id, destination_id=destination_id, arrival_tick=tick,
                    complies_with_strategy=compliance,
                )
            ))
        return vehicles

    @staticmethod
    def _apply_availability_overrides(graph: nx.Graph, scenario: ScenarioConfig) -> nx.Graph:
        working = graph.copy()
        overrides = scenario.availability_overrides or {}
        for gate_id in overrides.get("closed_gates", []):
            if gate_id in working:
                working.remove_node(gate_id)
        for lot_id in overrides.get("closed_parking_lots", []):
            if lot_id in working:
                working.remove_node(lot_id)
        closed_roads = set(overrides.get("closed_roads", []))
        if closed_roads:
            for u, v, d in list(working.edges(data=True)):
                if d.get("road_id") in closed_roads:
                    working.remove_edge(u, v)
        return working

    @staticmethod
    def _load_gates(campus_id, conn, overrides) -> dict:
        closed = set((overrides or {}).get("closed_gates", []))
        gates = {}
        for row in conn.execute("SELECT * FROM gates WHERE campus_id=?", (campus_id,)):
            gates[row["gate_id"]] = {
                "status": "closed" if row["gate_id"] in closed else row["status"],
                "capacity": row["capacity"],
                "queue_length": 0,
            }
        return gates

    @staticmethod
    def _load_parking_lots(campus_id, conn, overrides) -> dict:
        closed = set((overrides or {}).get("closed_parking_lots", []))
        lots = {}
        for row in conn.execute("SELECT * FROM parking_lots WHERE campus_id=?", (campus_id,)):
            lots[row["parking_lot_id"]] = {
                "status": "closed" if row["parking_lot_id"] in closed else row["status"],
                "usable_capacity": row["usable_capacity"],
                "occupied_spaces": 0,
            }
        return lots

    @staticmethod
    def _load_roads(campus_id, conn) -> dict:
        return {row["road_id"]: {"status": row["status"], "current_load": 0}
                for row in conn.execute("SELECT * FROM roads WHERE campus_id=?", (campus_id,))}

    @staticmethod
    def _load_destination_ids(campus_id, conn) -> list:
        return [row["destination_id"] for row in conn.execute("SELECT destination_id FROM destinations WHERE campus_id=?", (campus_id,))]

    @staticmethod
    def _route_target(destination_id, destinations, parking_lots, open_lot_ids):
        """Vehicles drive to a parking lot node, never to a pedestrian-only
        destination. This is simulation movement mechanics, not a Navigation
        feature -- no decision about WHICH lot happens here beyond picking
        a routable target; the actual assignment decision is the strategy's."""
        if destination_id in parking_lots and destination_id in open_lot_ids:
            return destination_id
        if not open_lot_ids:
            return None
        return sorted(open_lot_ids)[0]

    @staticmethod
    def _nearest_available_lot(from_node, open_lot_ids, parking_lots, graph):
        """Non-compliant driver behavior: find nearest open, non-full lot.
        Uses shortest path distance from current node."""
        if not open_lot_ids:
            return None
        candidates = [
            (lot_id, nx.shortest_path_length(graph, from_node, lot_id, weight="weight_distance_meters"))
            for lot_id in open_lot_ids
            if lot_id in graph and parking_lots[lot_id]["occupied_spaces"] < parking_lots[lot_id]["usable_capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda x: x[1])[0]

    @staticmethod
    def _assign_with_adapter(strategy: AllocationStrategy, vehicle: Vehicle,
                             campus_state: CampusState, parking_lots: dict,
                             open_lot_ids: list, graph) -> tuple:
        """Adapter pattern: wrap strategy.assign() with timeout + fallback + validation.

        Returns: (AssignmentResult, fallback_reason or None)

        Fallback triggers (apply B2 Nearest-Available):
        1. Strategy raises exception
        2. Strategy exceeds time budget
        3. Strategy returns infeasible result (lot closed/full)
        """
        fallback_reason = None
        result = None

        try:
            assign_start = datetime.now(timezone.utc)
            result = strategy.assign(vehicle, campus_state)
            assign_time_ms = (datetime.now(timezone.utc) - assign_start).total_seconds() * 1000

            # Check timeout
            if assign_time_ms > STRATEGY_TIMEOUT_MS:
                fallback_reason = f"timeout_{assign_time_ms:.0f}ms"
                result = None
            # Check feasibility
            elif result and result.parking_lot_id:
                lot = parking_lots.get(result.parking_lot_id)
                if not lot or lot["status"] != "open" or lot["occupied_spaces"] >= lot["usable_capacity"]:
                    fallback_reason = f"infeasible_{result.parking_lot_id}"
                    result = None

        except Exception as e:
            fallback_reason = f"exception_{type(e).__name__}"
            result = None

        # Fallback to B2 (Nearest-Available) if any trigger fired
        if fallback_reason:
            try:
                b2_strategy = NearestAvailableStrategy()
                result = b2_strategy.assign(vehicle, campus_state)
            except Exception:
                result = None

        return result, fallback_reason
