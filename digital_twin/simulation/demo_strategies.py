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

    label = "B2-NearestAvailable"

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


class PredictionOnlyStrategy(AllocationStrategy):
    """B3 — Prediction-aware strategy.

    Uses predicted occupancy (fill rate) to avoid lots that are likely to
    fill up soon, steering vehicles to lots with headroom. Without a real
    Member 2 forecast, the fill-rate proxy is computed from current state.
    This is a placeholder that will be replaced once the forecast module
    is integrated.
    """

    label = "B3-PredictionOnly"
    FILL_THRESHOLD = 0.80  # avoid lots more than 80% full

    def assign(self, vehicle, campus_state):
        best_lot, best_score = None, float("inf")
        for lot_id, lot in campus_state.parking_lots.items():
            if lot["status"] != "open":
                continue
            cap = lot["usable_capacity"]
            occ = lot["occupied_spaces"]
            if cap <= 0 or occ >= cap:
                continue
            fill_rate = occ / cap
            if fill_rate > self.FILL_THRESHOLD:
                continue  # skip nearly-full lots to avoid future overflow
            if not nx.has_path(campus_state.graph, vehicle.entry_gate, lot_id):
                continue
            distance = nx.shortest_path_length(
                campus_state.graph, vehicle.entry_gate, lot_id, weight="weight_distance_meters"
            )
            # Score = distance penalised by fill rate (prefer near + emptier lots)
            score = distance * (1 + fill_rate)
            if score < best_score:
                best_lot, best_score = lot_id, score
        # Fallback: if threshold filtered everything, pick nearest available
        if best_lot is None:
            for lot_id, lot in campus_state.parking_lots.items():
                if lot["status"] != "open" or lot["occupied_spaces"] >= lot["usable_capacity"]:
                    continue
                if not nx.has_path(campus_state.graph, vehicle.entry_gate, lot_id):
                    continue
                distance = nx.shortest_path_length(
                    campus_state.graph, vehicle.entry_gate, lot_id, weight="weight_distance_meters"
                )
                if best_lot is None or distance < best_score:
                    best_lot, best_score = lot_id, distance
        return AssignmentResult(parking_lot_id=best_lot, gate_id=vehicle.entry_gate)


class ParkingNavXFullStrategy(AllocationStrategy):
    """P — ParkingNav-X full system strategy.

    Combines: prediction-aware lot selection + gate load balancing +
    zone-aware routing. Vehicles are steered to the lot with the best
    combined score across distance, predicted fill headroom, and gate
    queue length. This is the target end-state of the ParkingNav-X system.
    """

    label = "P-ParkingNavX"
    FILL_THRESHOLD = 0.85
    GATE_WEIGHT = 0.3      # how much gate queue penalises a lot

    def assign(self, vehicle, campus_state):
        best_lot, best_score = None, float("inf")

        # Prefer the least-loaded gate
        gate_loads = {
            g_id: g.get("queue_length", 0)
            for g_id, g in campus_state.gates.items()
            if g.get("status", "open") == "open"
        }
        preferred_gate = min(gate_loads, key=gate_loads.get) if gate_loads else vehicle.entry_gate

        for lot_id, lot in campus_state.parking_lots.items():
            if lot["status"] != "open":
                continue
            cap = lot["usable_capacity"]
            occ = lot["occupied_spaces"]
            if cap <= 0 or occ >= cap:
                continue
            fill_rate = occ / cap
            if fill_rate > self.FILL_THRESHOLD:
                continue

            entry = preferred_gate if nx.has_path(campus_state.graph, preferred_gate, lot_id) else vehicle.entry_gate
            if not nx.has_path(campus_state.graph, entry, lot_id):
                continue

            distance = nx.shortest_path_length(
                campus_state.graph, entry, lot_id, weight="weight_distance_meters"
            )
            gate_penalty = gate_loads.get(entry, 0) * self.GATE_WEIGHT
            score = distance * (1 + fill_rate) + gate_penalty

            if score < best_score:
                best_lot, best_score = lot_id, score

        # Fallback to nearest if all filtered out
        if best_lot is None:
            for lot_id, lot in campus_state.parking_lots.items():
                if lot["status"] != "open" or lot["occupied_spaces"] >= lot["usable_capacity"]:
                    continue
                if not nx.has_path(campus_state.graph, vehicle.entry_gate, lot_id):
                    continue
                distance = nx.shortest_path_length(
                    campus_state.graph, vehicle.entry_gate, lot_id, weight="weight_distance_meters"
                )
                if best_lot is None or distance < best_score:
                    best_lot, best_score = lot_id, distance

        return AssignmentResult(parking_lot_id=best_lot, gate_id=vehicle.entry_gate)
