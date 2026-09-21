"""
Part 4's seam: the AllocationStrategy interface. The simulation engine
never decides which lot a vehicle goes to -- it only calls whatever
strategy it's handed, exactly once per vehicle at the parking_search step,
and then enforces the physical constraints (closed/full lot, closed road,
gate throughput) regardless of what the strategy returned.

Member 3 implements First Available, Nearest Available, and the final
optimizer against this exact interface. FixedLotStrategy below exists only
to prove, in this module's own tests, that the interface is actually being
called and not bypassed -- it is not a real allocation strategy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Vehicle:
    vehicle_id: str
    entry_gate: str
    destination_id: Optional[str]
    arrival_tick: int


@dataclass
class CampusState:
    """Read-only view handed to a strategy: current parking/gate/road
    state plus the campus graph, for the strategy to reason over. The
    strategy must not mutate this -- only the engine writes state."""
    campus_id: str
    graph: object  # networkx.Graph
    parking_lots: dict   # lot_id -> {"status", "usable_capacity", "occupied_spaces"}
    gates: dict           # gate_id -> {"status", "capacity", "queue_length"}
    roads: dict           # road_id -> {"status", "current_load"}


@dataclass
class AssignmentResult:
    parking_lot_id: Optional[str]
    gate_id: Optional[str] = None
    route: list = field(default_factory=list)


class AllocationStrategy(ABC):
    @abstractmethod
    def assign(self, vehicle: Vehicle, campus_state: CampusState) -> AssignmentResult:
        """Given a vehicle and the current (or predicted) campus state,
        return which parking lot (and optionally gate/route) this vehicle
        should use. Implemented by teammates, NOT by this module."""


class FixedLotStrategy(AllocationStrategy):
    """Test-only strategy: always assigns the configured lot, regardless
    of state. Used to prove the engine actually calls this interface."""

    def __init__(self, lot_id: str):
        self.lot_id = lot_id

    def assign(self, vehicle: Vehicle, campus_state: CampusState) -> AssignmentResult:
        return AssignmentResult(parking_lot_id=self.lot_id, gate_id=vehicle.entry_gate)
