"""
Module 3: Digital Twin State Manager.

Holds the current dynamic state of one campus (parking/gate/road/vehicle/
event state) plus its history, completely separate from CampusConfig (what
exists) and from Simulation (how state evolves). The twin does not know or
care whether an update came from a real observation or a simulation step —
it only requires that every update carries its own provenance.
"""

import copy
from dataclasses import dataclass, field
from typing import Optional

from campus_twin.config import Provenance


class StateError(ValueError):
    """Raised when a state update would be logically inconsistent. Never
    silently clamped or corrected."""


@dataclass
class ParkingState:
    parking_lot_id: str
    capacity: int
    usable_capacity: int
    occupied_spaces: int
    reserved_spaces: int = 0
    restricted_spaces: int = 0
    unavailable_spaces: int = 0
    status: str = "OPEN"
    source_type: str = "SIMULATION"
    provenance: Provenance = Provenance.SYNTHETIC
    timestamp: Optional[str] = None
    configuration_version: str = ""

    @property
    def available_spaces(self) -> int:
        return self.usable_capacity - self.occupied_spaces - self.unavailable_spaces

    @property
    def occupancy_percentage(self) -> float:
        if self.usable_capacity == 0:
            return 0.0
        return round(100 * self.occupied_spaces / self.usable_capacity, 2)


@dataclass
class GateState:
    gate_id: str
    current_queue: int = 0
    queue_capacity: Optional[int] = None
    throughput: int = 0
    current_arrival_rate: float = 0.0
    current_departure_rate: float = 0.0
    status: str = "OPEN"
    source_type: str = "SIMULATION"
    provenance: Provenance = Provenance.SYNTHETIC
    timestamp: Optional[str] = None


@dataclass
class RoadState:
    road_id: str
    current_load: int = 0
    capacity: Optional[int] = None
    travel_time: float = 0.0
    congestion_level: str = "FREE"  # FREE/NORMAL/BUSY/CONGESTED/BLOCKED/UNKNOWN
    status: str = "OPEN"
    source_type: str = "SIMULATION"
    provenance: Provenance = Provenance.SYNTHETIC
    timestamp: Optional[str] = None

    @property
    def utilization(self) -> float:
        if not self.capacity:
            return 0.0
        return round(self.current_load / self.capacity, 3)


@dataclass
class VehicleState:
    vehicle_id: str
    campus_id: str
    state: str = "ARRIVING"
    entry_gate: Optional[str] = None
    destination_id: Optional[str] = None
    current_node: Optional[str] = None
    assigned_parking_lot: Optional[str] = None
    route: list = field(default_factory=list)
    arrival_time: Optional[float] = None
    parking_time: Optional[float] = None
    departure_time: Optional[float] = None
    scenario_id: Optional[str] = None
    provenance: Provenance = Provenance.SYNTHETIC
    timestamp: Optional[str] = None


VEHICLE_LIFECYCLE = [
    "ARRIVING", "WAITING_AT_GATE", "ENTERING", "INSIDE_CAMPUS", "TRAVELLING",
    "SEARCHING_FOR_PARKING", "ASSIGNED", "PARKED", "LEAVING", "EXITING", "COMPLETED",
]
_VALID_TRANSITIONS = {
    a: {VEHICLE_LIFECYCLE[i + 1]} for i, a in enumerate(VEHICLE_LIFECYCLE[:-1])
}
# Two intentional loops in the real lifecycle: search can retry, gate queue can retry entry.
_VALID_TRANSITIONS["SEARCHING_FOR_PARKING"].add("SEARCHING_FOR_PARKING")
_VALID_TRANSITIONS["WAITING_AT_GATE"].add("WAITING_AT_GATE")


def validate_vehicle_transition(current_state: str, next_state: str) -> bool:
    return next_state in _VALID_TRANSITIONS.get(current_state, set())


@dataclass
class EventState:
    event_id: str
    campus_id: str
    event_type: str
    affected_gates: list = field(default_factory=list)
    affected_parking: list = field(default_factory=list)
    affected_roads: list = field(default_factory=list)
    demand_multiplier: float = 1.0
    provenance: Provenance = Provenance.SYNTHETIC
    scenario_id: Optional[str] = None


@dataclass
class Snapshot:
    snapshot_id: str
    campus_id: str
    timestamp: str
    configuration_version: str
    scenario_id: Optional[str]
    parking_states: dict
    gate_states: dict
    road_states: dict
    vehicle_states: dict
    active_events: list
    provenance: Provenance
    simulation_time: Optional[float] = None


class DigitalTwin:
    """One instance = one campus's dynamic state. Never mixes two campuses,
    and never mixes REAL and SIMULATED state in the same field silently —
    every state object carries its own provenance and source_type."""

    def __init__(self, campus_id: str, configuration_version: str):
        self.campus_id = campus_id
        self.configuration_version = configuration_version
        self._parking_states: dict = {}
        self._gate_states: dict = {}
        self._road_states: dict = {}
        self._vehicle_states: dict = {}
        self._active_events: dict = {}
        self._history: list = []
        self._snapshot_counter = 0

    def initialize_state(self, parking_states=None, gate_states=None, road_states=None):
        self._parking_states = {p.parking_lot_id: p for p in (parking_states or [])}
        self._gate_states = {g.gate_id: g for g in (gate_states or [])}
        self._road_states = {r.road_id: r for r in (road_states or [])}
        self._vehicle_states = {}
        self._active_events = {}

    def get_current_state(self) -> dict:
        return {
            "campus_id": self.campus_id,
            "configuration_version": self.configuration_version,
            "parking": dict(self._parking_states),
            "gates": dict(self._gate_states),
            "roads": dict(self._road_states),
            "vehicles": dict(self._vehicle_states),
            "events": dict(self._active_events),
        }

    def update_parking_state(self, parking_state: ParkingState):
        if parking_state.occupied_spaces < 0:
            raise StateError(f"Negative occupied_spaces for '{parking_state.parking_lot_id}'.")
        if parking_state.occupied_spaces > parking_state.usable_capacity:
            raise StateError(
                f"occupied_spaces exceeds usable_capacity for '{parking_state.parking_lot_id}'."
            )
        if parking_state.available_spaces < 0:
            raise StateError(f"available_spaces would be negative for '{parking_state.parking_lot_id}'.")
        parking_state.configuration_version = self.configuration_version
        self._parking_states[parking_state.parking_lot_id] = parking_state

    def update_gate_state(self, gate_state: GateState):
        if gate_state.current_queue < 0:
            raise StateError(f"Negative queue for gate '{gate_state.gate_id}'.")
        self._gate_states[gate_state.gate_id] = gate_state

    def update_road_state(self, road_state: RoadState):
        if road_state.current_load < 0:
            raise StateError(f"Negative current_load for road '{road_state.road_id}'.")
        self._road_states[road_state.road_id] = road_state

    def update_vehicle_state(self, vehicle_state: VehicleState):
        existing = self._vehicle_states.get(vehicle_state.vehicle_id)
        if existing and not validate_vehicle_transition(existing.state, vehicle_state.state):
            raise StateError(
                f"Invalid vehicle transition for '{vehicle_state.vehicle_id}': "
                f"{existing.state} -> {vehicle_state.state}"
            )
        self._vehicle_states[vehicle_state.vehicle_id] = vehicle_state

    def apply_event_state(self, event_state: EventState):
        self._active_events[event_state.event_id] = event_state

    def clear_event(self, event_id: str):
        self._active_events.pop(event_id, None)

    def validate_state(self) -> list:
        errors = []
        for lot_id, p in self._parking_states.items():
            if p.occupied_spaces > p.usable_capacity or p.occupied_spaces < 0:
                errors.append(f"Inconsistent parking state for '{lot_id}'.")
        for gate_id, g in self._gate_states.items():
            if g.current_queue < 0:
                errors.append(f"Inconsistent gate state for '{gate_id}'.")
        return errors

    def snapshot_now(self, timestamp: str, scenario_id: Optional[str] = None,
                      simulation_time: Optional[float] = None,
                      provenance: Provenance = Provenance.SYNTHETIC) -> Snapshot:
        self._snapshot_counter += 1
        snapshot = Snapshot(
            snapshot_id=f"{self.campus_id}-snap-{self._snapshot_counter}",
            campus_id=self.campus_id,
            timestamp=timestamp,
            configuration_version=self.configuration_version,
            scenario_id=scenario_id,
            parking_states=copy.deepcopy(self._parking_states),
            gate_states=copy.deepcopy(self._gate_states),
            road_states=copy.deepcopy(self._road_states),
            vehicle_states=copy.deepcopy(self._vehicle_states),
            active_events=list(self._active_events.values()),
            provenance=provenance,
            simulation_time=simulation_time,
        )
        self._history.append(snapshot)
        return snapshot

    def reset_state(self):
        self._parking_states = {}
        self._gate_states = {}
        self._road_states = {}
        self._vehicle_states = {}
        self._active_events = {}

    def restore_snapshot(self, snapshot: Snapshot):
        self._parking_states = copy.deepcopy(snapshot.parking_states)
        self._gate_states = copy.deepcopy(snapshot.gate_states)
        self._road_states = copy.deepcopy(snapshot.road_states)
        self._vehicle_states = copy.deepcopy(snapshot.vehicle_states)
        self._active_events = {e.event_id: e for e in snapshot.active_events}

    def get_history(self) -> list:
        return list(self._history)

    def get_state_at_timestamp(self, timestamp: str) -> Optional[Snapshot]:
        matches = [s for s in self._history if s.timestamp == timestamp]
        return matches[-1] if matches else None
