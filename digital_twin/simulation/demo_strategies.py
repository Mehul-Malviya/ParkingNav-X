"""
DEMO-ONLY allocation strategies, used to produce real, runnable simulation
output for demonstration purposes. These are NOT the project's final
allocation strategies -- First Available, Nearest Available, and the real
optimizer are explicitly Member 3's ownership (see MEMBER1_SUBSYSTEM_REPORT.md).
This file exists only so `python -m digital_twin.cli.run` has something
concrete to run against.
"""

import networkx as nx

from digital_twin.simulation.strategy import AllocationStrategy, AssignmentResult


class DemoNearestAvailableStrategy(AllocationStrategy):
    """Picks the open, available lot with the shortest drive distance from
    the vehicle's current position. A minimal real implementation, not the
    project's final strategy."""

    def assign(self, vehicle, campus_state):
        best_lot, best_distance = None, float("inf")
        for lot_id, lot in campus_state.parking_lots.items():
            if lot["status"] != "open" or lot["occupied_spaces"] >= lot["usable_capacity"]:
                continue
            if not nx.has_path(campus_state.graph, vehicle.entry_gate, lot_id):
                continue
            distance = nx.shortest_path_length(
                campus_state.graph, vehicle.entry_gate, lot_id, weight="weight_distance_meters"
            )
            if distance < best_distance:
                best_lot, best_distance = lot_id, distance
        return AssignmentResult(parking_lot_id=best_lot, gate_id=vehicle.entry_gate)
