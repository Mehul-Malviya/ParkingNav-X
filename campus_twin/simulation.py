"""
Module 6: deterministic discrete-time Simulation Engine.

Every state change flows through the DigitalTwin (never a separate, parallel
state model), and every route comes from the one shared CampusGraph (never a
second road network built inside the simulator). Output is always
provenance=SYNTHETIC, result_type=SIMULATION — never presented as a real
observation.

Kept deliberately transparent rather than realistic: travel time is a fixed
walking/driving speed applied to route distance, and road load is "number of
vehicles currently transiting an edge on their route" — a simple, replaceable
model, not a traffic simulator.
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from campus_twin.config import CampusConfig, EntityStatus, Provenance
from campus_twin.digital_twin import DigitalTwin, GateState, ParkingState, RoadState, VehicleState
from campus_twin.graph import CampusGraph
from campus_twin.scenarios import Scenario
from campus_twin.strategies import NearestAvailableStrategy, ParkingAssignmentStrategy
from dijkstra import dijkstra

DRIVE_SPEED_M_PER_MIN = 200.0  # ~12 km/h campus driving speed; replaceable constant
GATE_THROUGHPUT_PER_TICK_DEFAULT = 5
SNAPSHOT_INTERVAL_MINUTES_DEFAULT = 5


@dataclass
class SimVehicle:
    vehicle_id: str
    entry_gate: str
    destination_id: str
    dwell_time_minutes: int
    state: str = "ARRIVING"
    route_to_lot: list = field(default_factory=list)
    route_to_gate: list = field(default_factory=list)
    remaining_transit_minutes: float = 0.0
    assigned_parking_lot: Optional[str] = None
    parking_attempts: int = 0
    lots_attempted: list = field(default_factory=list)
    search_start_tick: Optional[int] = None
    search_end_tick: Optional[int] = None
    arrival_tick: int = 0
    completion_tick: Optional[int] = None
    target_lot_hint: Optional[str] = None


@dataclass
class SimulationResult:
    simulation_id: str
    campus_id: str
    scenario_id: str
    configuration_version: str
    seed: int
    duration_minutes: int
    result_type: str
    provenance: Provenance
    metrics: dict
    snapshots: list
    failed_vehicles: list
    vehicle_log: list


def _edges_on_route(route: list) -> list:
    return list(zip(route, route[1:]))


class SimulationEngine:
    def __init__(self, strategy: Optional[ParkingAssignmentStrategy] = None,
                 snapshot_interval_minutes: int = SNAPSHOT_INTERVAL_MINUTES_DEFAULT):
        self.snapshot_interval_minutes = snapshot_interval_minutes
        self._strategy = strategy  # set per-run if None, so RandomFeasible can use the run's rng

    def run(self, config: CampusConfig, graph: CampusGraph, scenario: Scenario) -> SimulationResult:
        rng = random.Random(scenario.seed)
        strategy = self._strategy or NearestAvailableStrategy()

        open_gates = [g for g in config.gates
                      if g.status == EntityStatus.OPEN and g.gate_id not in scenario.closed_gates]
        open_lots = [p for p in config.parking_lots
                     if p.status == EntityStatus.OPEN and p.parking_lot_id not in scenario.closed_parking_lots]
        destinations = list(config.destinations) or open_lots  # fallback: park at nearest lot if no destinations configured

        if not open_gates or not open_lots:
            return SimulationResult(
                simulation_id=f"{scenario.scenario_id}-sim",
                campus_id=config.campus_id,
                scenario_id=scenario.scenario_id,
                configuration_version=config.configuration_version,
                seed=scenario.seed,
                duration_minutes=scenario.duration_minutes,
                result_type="SIMULATION",
                provenance=Provenance.SYNTHETIC,
                metrics={"error": "No open gates or no open parking lots for this scenario."},
                snapshots=[],
                failed_vehicles=[],
                vehicle_log=[],
            )

        destination_by_id = {getattr(d, "destination_id", None): d for d in config.destinations}
        open_lot_ids = {p.parking_lot_id for p in open_lots}

        drive_adjacency = {
            node: {n: d for n, d in edges.items() if self._road_open(config, node, n, scenario)}
            for node, edges in graph.drive_adjacency.items()
        }

        twin = DigitalTwin(config.campus_id, config.configuration_version)
        twin.initialize_state(
            parking_states=[
                ParkingState(
                    parking_lot_id=p.parking_lot_id,
                    capacity=p.capacity,
                    usable_capacity=p.usable_capacity,
                    occupied_spaces=0,
                    provenance=Provenance.SYNTHETIC,
                    timestamp="t=0",
                )
                for p in config.parking_lots
            ],
            gate_states=[
                GateState(gate_id=g.gate_id, provenance=Provenance.SYNTHETIC, timestamp="t=0")
                for g in config.gates
            ],
            road_states=[
                RoadState(road_id=r.road_id, capacity=r.capacity, provenance=Provenance.SYNTHETIC, timestamp="t=0")
                for r in config.roads
            ],
        )

        vehicles = self._generate_arrivals(scenario, open_gates, destinations, rng)
        active: dict = {}
        completed: list = []
        failed: list = []
        snapshots = []
        road_load = {r.road_id: 0 for r in config.roads}
        road_by_endpoints = {(r.start_node_id, r.end_node_id): r.road_id for r in config.roads}
        road_by_endpoints.update({(r.end_node_id, r.start_node_id): r.road_id for r in config.roads if not r.one_way})

        lot_states = twin.get_current_state()["parking"]
        gate_states = twin.get_current_state()["gates"]

        for tick in range(scenario.duration_minutes):
            for v in vehicles:
                if v.arrival_tick == tick:
                    gate_states[v.entry_gate].current_queue += 1
                    v.state = "WAITING_AT_GATE"
                    active[v.vehicle_id] = v
                    twin.update_vehicle_state(VehicleState(
                        vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="ARRIVING",
                        entry_gate=v.entry_gate, destination_id=v.destination_id,
                        scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                    ))
                    twin.update_vehicle_state(VehicleState(
                        vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="WAITING_AT_GATE",
                        entry_gate=v.entry_gate, destination_id=v.destination_id,
                        scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                    ))

            for gate in open_gates:
                gs = gate_states[gate.gate_id]
                throughput = gate.capacity or GATE_THROUGHPUT_PER_TICK_DEFAULT
                admitted = 0
                for v in list(active.values()):
                    if admitted >= throughput:
                        break
                    if v.state == "WAITING_AT_GATE" and v.entry_gate == gate.gate_id:
                        gs.current_queue = max(0, gs.current_queue - 1)
                        gs.throughput += 1
                        target_lot = self._nearest_lot_for_destination(v.destination_id, destination_by_id, open_lot_ids)
                        v.target_lot_hint = target_lot
                        route, cost = dijkstra(drive_adjacency, gate.gate_id, target_lot)
                        if not route:
                            failed.append({"vehicle_id": v.vehicle_id, "reason": "NO_ROUTE_FROM_GATE"})
                            active.pop(v.vehicle_id, None)
                            continue
                        v.route_to_lot = route
                        v.remaining_transit_minutes = max(1.0, cost / DRIVE_SPEED_M_PER_MIN)
                        v.state = "TRAVELLING"
                        v.search_start_tick = tick
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="ENTERING",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="INSIDE_CAMPUS",
                            entry_gate=v.entry_gate, destination_id=v.destination_id, route=route,
                            scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="TRAVELLING",
                            entry_gate=v.entry_gate, destination_id=v.destination_id, route=route,
                            scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                        admitted += 1

            for v in list(active.values()):
                if v.state in ("TRAVELLING",) and v.route_to_lot:
                    for a, b in _edges_on_route(v.route_to_lot):
                        rid = road_by_endpoints.get((a, b))
                        if rid:
                            road_load[rid] += 1
                    v.remaining_transit_minutes -= 1
                    if v.remaining_transit_minutes <= 0:
                        v.state = "SEARCHING_FOR_PARKING"
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="SEARCHING_FOR_PARKING",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))

                elif v.state == "SEARCHING_FOR_PARKING":
                    lot_id = strategy.choose(drive_adjacency, lot_states, v.route_to_lot[-1] if v.route_to_lot else v.entry_gate)
                    v.parking_attempts += 1
                    if lot_id:
                        v.lots_attempted.append(lot_id)
                        lot_states[lot_id].occupied_spaces += 1
                        v.assigned_parking_lot = lot_id
                        v.search_end_tick = tick
                        v.state = "PARKED"
                        v.remaining_transit_minutes = v.dwell_time_minutes
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="ASSIGNED",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            assigned_parking_lot=lot_id, scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="PARKED",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            assigned_parking_lot=lot_id, parking_time=float(tick),
                            scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                    else:
                        failed.append({"vehicle_id": v.vehicle_id, "reason": "NO_FEASIBLE_PARKING", "tick": tick})

                elif v.state == "PARKED":
                    v.remaining_transit_minutes -= 1
                    if v.remaining_transit_minutes <= 0:
                        lot_states[v.assigned_parking_lot].occupied_spaces -= 1
                        route, cost = dijkstra(drive_adjacency, v.assigned_parking_lot, v.entry_gate)
                        v.route_to_gate = route
                        v.remaining_transit_minutes = max(1.0, cost / DRIVE_SPEED_M_PER_MIN) if route else 1.0
                        v.state = "LEAVING"
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="LEAVING",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            assigned_parking_lot=v.assigned_parking_lot,
                            scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))

                elif v.state == "LEAVING":
                    for a, b in _edges_on_route(v.route_to_gate):
                        rid = road_by_endpoints.get((a, b))
                        if rid:
                            road_load[rid] += 1
                    v.remaining_transit_minutes -= 1
                    if v.remaining_transit_minutes <= 0:
                        gate_states[v.entry_gate].throughput += 1
                        v.state = "COMPLETED"
                        v.completion_tick = tick
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="EXITING",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            departure_time=float(tick), scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                        twin.update_vehicle_state(VehicleState(
                            vehicle_id=v.vehicle_id, campus_id=config.campus_id, state="COMPLETED",
                            entry_gate=v.entry_gate, destination_id=v.destination_id,
                            departure_time=float(tick), scenario_id=scenario.scenario_id, timestamp=f"t={tick}",
                        ))
                        completed.append(v)
                        active.pop(v.vehicle_id, None)

            for rid, load in road_load.items():
                road_state = twin._road_states.get(rid)
                if road_state:
                    road_state.current_load = load
                    road_state.congestion_level = self._congestion_level(load, road_state.capacity)
            road_load = {rid: 0 for rid in road_load}  # reset per-tick transit count

            if tick % self.snapshot_interval_minutes == 0:
                snapshots.append(twin.snapshot_now(timestamp=f"t={tick}", scenario_id=scenario.scenario_id))

        metrics = self._compute_metrics(vehicles, completed, failed, lot_states, gate_states, scenario)

        return SimulationResult(
            simulation_id=f"{scenario.scenario_id}-sim",
            campus_id=config.campus_id,
            scenario_id=scenario.scenario_id,
            configuration_version=config.configuration_version,
            seed=scenario.seed,
            duration_minutes=scenario.duration_minutes,
            result_type="SIMULATION",
            provenance=Provenance.SYNTHETIC,
            metrics=metrics,
            snapshots=snapshots,
            failed_vehicles=failed,
            vehicle_log=[v.vehicle_id for v in vehicles],
        )

    @staticmethod
    def _road_open(config: CampusConfig, a: str, b: str, scenario: Scenario) -> bool:
        for r in config.roads:
            if r.road_id in scenario.closed_roads and {r.start_node_id, r.end_node_id} == {a, b}:
                return False
        return True

    @staticmethod
    def _nearest_lot_for_destination(destination_id, destination_by_id, open_lot_ids) -> str:
        """Vehicles drive to a parking lot, never to a pedestrian-only
        destination node. Prefers a lot the destination is actually linked
        to; falls back to any open lot (deterministic: sorted order)."""
        dest = destination_by_id.get(destination_id)
        if dest:
            for lot_id in getattr(dest, "nearest_parking_lots", []):
                if lot_id in open_lot_ids:
                    return lot_id
        if destination_id in open_lot_ids:
            return destination_id
        return sorted(open_lot_ids)[0]

    @staticmethod
    def _congestion_level(load: int, capacity) -> str:
        if not capacity:
            return "UNKNOWN"
        ratio = load / capacity
        if ratio == 0:
            return "FREE"
        if ratio < 0.4:
            return "NORMAL"
        if ratio < 0.8:
            return "BUSY"
        if ratio < 1.0:
            return "CONGESTED"
        return "BLOCKED"

    def _generate_arrivals(self, scenario: Scenario, open_gates, destinations, rng) -> list:
        vehicles = []
        gate_ids = [g.gate_id for g in open_gates]
        gate_weights = [
            (scenario.entry_gate_weights or {}).get(g, 1.0) for g in gate_ids
        ]
        dest_ids = [getattr(d, "destination_id", getattr(d, "parking_lot_id", None)) for d in destinations]
        dest_weights = [
            (scenario.destination_weights or {}).get(d, 1.0) for d in dest_ids
        ]

        effective_count = max(1, round(scenario.num_vehicles * scenario.demand_multiplier))

        for i in range(effective_count):
            if scenario.arrival_profile == "peaked":
                # More arrivals clustered in the first half of the window.
                tick = min(scenario.duration_minutes - 1, int(rng.triangular(0, scenario.duration_minutes, 0)))
            else:
                tick = rng.randint(0, max(0, scenario.duration_minutes - 1))

            gate_id = rng.choices(gate_ids, weights=gate_weights, k=1)[0]
            dest_id = rng.choices(dest_ids, weights=dest_weights, k=1)[0] if dest_ids else gate_id
            dwell = rng.randint(*scenario.dwell_time_minutes)

            vehicles.append(SimVehicle(
                vehicle_id=f"{scenario.scenario_id}-v{i}",
                entry_gate=gate_id,
                destination_id=dest_id,
                dwell_time_minutes=dwell,
                arrival_tick=tick,
            ))

        return vehicles

    @staticmethod
    def _compute_metrics(vehicles, completed, failed, lot_states, gate_states, scenario) -> dict:
        total = len(vehicles)
        completed_count = len(completed)
        peak_occupancy = {lot_id: state.occupied_spaces for lot_id, state in lot_states.items()}
        search_durations = [
            (v.search_end_tick - v.search_start_tick)
            for v in completed if v.search_start_tick is not None and v.search_end_tick is not None
        ]
        return {
            "total_vehicles": total,
            "completed_vehicles": completed_count,
            "failed_vehicles": len(failed),
            "overflow_events": len(failed),
            "average_search_time_minutes": round(sum(search_durations) / len(search_durations), 2) if search_durations else 0,
            "final_occupancy_by_lot": peak_occupancy,
            "gate_queue_final": {gid: gs.current_queue for gid, gs in gate_states.items()},
            "gate_throughput_total": {gid: gs.throughput for gid, gs in gate_states.items()},
            "scenario_name": scenario.scenario_name,
            "seed": scenario.seed,
        }
