"""
Module 22: pluggable parking-assignment strategy interface.

The simulator never hard-codes the final ParkingNav-X optimizer. Baselines
here reuse the existing repo logic (dijkstra.py, parking_constraints.py)
directly, rather than duplicating it.
"""

from abc import ABC, abstractmethod

from dijkstra import dijkstra
from parking_constraints import is_parking_available


class ParkingAssignmentStrategy(ABC):
    @abstractmethod
    def choose(self, drive_adjacency: dict, parking_states: dict, from_node: str):
        """Returns a parking_lot_id to attempt, or None if nothing feasible."""


class FirstAvailableStrategy(ParkingAssignmentStrategy):
    def choose(self, drive_adjacency, parking_states, from_node):
        for lot_id, state in parking_states.items():
            if is_parking_available({"capacity": state.usable_capacity, "occupied": state.occupied_spaces}):
                return lot_id
        return None


class NearestAvailableStrategy(ParkingAssignmentStrategy):
    def choose(self, drive_adjacency, parking_states, from_node):
        best_lot, best_cost = None, float("inf")
        for lot_id, state in parking_states.items():
            if not is_parking_available({"capacity": state.usable_capacity, "occupied": state.occupied_spaces}):
                continue
            route, cost = dijkstra(drive_adjacency, from_node, lot_id)
            if route and cost < best_cost:
                best_lot, best_cost = lot_id, cost
        return best_lot


class FixedPreferenceStrategy(ParkingAssignmentStrategy):
    """Always prefers a configured ordered list of lots, falling through
    to the next if unavailable."""

    def __init__(self, preferred_order: list):
        self.preferred_order = preferred_order

    def choose(self, drive_adjacency, parking_states, from_node):
        for lot_id in self.preferred_order:
            state = parking_states.get(lot_id)
            if state and is_parking_available({"capacity": state.usable_capacity, "occupied": state.occupied_spaces}):
                return lot_id
        return None


class RandomFeasibleStrategy(ParkingAssignmentStrategy):
    def __init__(self, rng):
        self.rng = rng

    def choose(self, drive_adjacency, parking_states, from_node):
        feasible = [
            lot_id for lot_id, state in parking_states.items()
            if is_parking_available({"capacity": state.usable_capacity, "occupied": state.occupied_spaces})
        ]
        return self.rng.choice(feasible) if feasible else None
