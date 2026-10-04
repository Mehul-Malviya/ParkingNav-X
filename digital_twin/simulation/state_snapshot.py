"""
StateSnapshot — Campus state export for Member 3 (Optimizer)

Provides a JSON-serializable snapshot of campus state at any simulation tick,
with fork() capability for look-ahead simulation by Member 3's optimizer.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, List


@dataclass
class LotState:
    """Parking lot state."""
    id: str
    capacity: int
    occupied: int
    available: int
    reserved_free: int
    status: str  # open, closed, full
    inflow_5m: int
    outflow_5m: int

    @property
    def occupancy_ratio(self) -> float:
        return self.occupied / self.capacity if self.capacity > 0 else 0.0


@dataclass
class GateState:
    """Entry gate state."""
    id: str
    queue_length: int
    service_rate_veh_per_min: float
    status: str  # open, closed
    throughput_last_5min: int


@dataclass
class RoadState:
    """Road segment state."""
    id: str
    travel_time_sec: float
    congestion_ratio: float
    status: str  # open, closed, blocked
    current_load: int
    capacity: int


@dataclass
class EventState:
    """Active event (demand multiplier)."""
    event_id: str
    start_tick: int
    duration_ticks: int
    demand_multiplier: float
    affected_zones: List[str]
    minutes_remaining: int


@dataclass
class StateSnapshot:
    """
    Real-time campus state snapshot for Member 3's optimizer.

    Immutable (for safety); fork() creates independent copy for what-if simulation.
    """
    sim_time: int  # current tick (minutes)
    sim_time_iso: str  # ISO 8601 timestamp

    lots: List[LotState]
    gates: List[GateState]
    roads: List[RoadState]

    pending_arrivals_by_gate: Dict[str, int]
    active_events: List[EventState]
    active_disruptions: List[Dict]

    travel_time_matrix: Dict[str, Dict[str, float]]  # [gate][lot] -> seconds
    walk_time: Dict[str, Dict[str, float]]  # [zone][lot] -> seconds

    forecast: Optional[Dict] = None  # From Member 2 (occ_t+15, occ_t+30, confidence)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "sim_time": self.sim_time,
            "sim_time_iso": self.sim_time_iso,
            "lots": [asdict(lot) for lot in self.lots],
            "gates": [asdict(gate) for gate in self.gates],
            "roads": [asdict(road) for road in self.roads],
            "pending_arrivals_by_gate": self.pending_arrivals_by_gate,
            "active_events": [asdict(event) for event in self.active_events],
            "active_disruptions": self.active_disruptions,
            "travel_time_matrix": self.travel_time_matrix,
            "walk_time": self.walk_time,
            "forecast": self.forecast or {},
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "StateSnapshot":
        """Reconstruct from dict (e.g., loaded from JSON)."""
        lots = [LotState(**lot) for lot in data.get("lots", [])]
        gates = [GateState(**gate) for gate in data.get("gates", [])]
        roads = [RoadState(**road) for road in data.get("roads", [])]
        events = [EventState(**event) for event in data.get("active_events", [])]

        return cls(
            sim_time=data["sim_time"],
            sim_time_iso=data["sim_time_iso"],
            lots=lots,
            gates=gates,
            roads=roads,
            pending_arrivals_by_gate=data.get("pending_arrivals_by_gate", {}),
            active_events=events,
            active_disruptions=data.get("active_disruptions", []),
            travel_time_matrix=data.get("travel_time_matrix", {}),
            walk_time=data.get("walk_time", {}),
            forecast=data.get("forecast"),
        )

    def fork(self) -> "StateSnapshot":
        """
        Create an independent deep copy for what-if simulation.

        Member 3 can use this to explore multiple candidate allocations
        without modifying the current state.
        """
        import copy
        return copy.deepcopy(self)

    def get_lot_by_id(self, lot_id: str) -> Optional[LotState]:
        """Get a lot by ID."""
        for lot in self.lots:
            if lot.id == lot_id:
                return lot
        return None

    def get_gate_by_id(self, gate_id: str) -> Optional[GateState]:
        """Get a gate by ID."""
        for gate in self.gates:
            if gate.id == gate_id:
                return gate
        return None
