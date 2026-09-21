"""
Campus Graph: built deterministically from a CampusConfig. This is the one
authoritative graph shared by simulation and (eventually) navigation — never
a second, independently-built road network.
"""

from dataclasses import dataclass, field

from campus_twin.config import CampusConfig, EntityStatus
from dijkstra import dijkstra


@dataclass
class CampusGraph:
    campus_id: str
    configuration_version: str
    drive_adjacency: dict = field(default_factory=dict)   # node_id -> {node_id: distance}
    walk_adjacency: dict = field(default_factory=dict)
    node_ids: set = field(default_factory=set)

    def shortest_route(self, start: str, destination: str, mode: str = "drive"):
        """Returns (route, cost) using the existing Dijkstra implementation,
        respecting closed roads (already excluded from the adjacency)."""
        adjacency = self.drive_adjacency if mode == "drive" else self.walk_adjacency
        if start not in adjacency or destination not in adjacency:
            return [], float("inf")
        return dijkstra(adjacency, start, destination)


def build_campus_graph(config: CampusConfig) -> CampusGraph:
    """Deterministic: same config always produces the same graph. Closed
    roads/gates/lots are excluded from the routable adjacency, not just
    flagged — a closed road must never be silently routable."""
    drive_adjacency: dict = {}
    walk_adjacency: dict = {}
    node_ids: set = set()

    def add_node(adjacency, node_id):
        adjacency.setdefault(node_id, {})

    for g in config.gates:
        node_ids.add(g.gate_id)
        if g.status == EntityStatus.OPEN:
            add_node(drive_adjacency, g.gate_id)
            add_node(walk_adjacency, g.gate_id)

    for p in config.parking_lots:
        node_ids.add(p.parking_lot_id)
        if p.status == EntityStatus.OPEN:
            add_node(drive_adjacency, p.parking_lot_id)
            add_node(walk_adjacency, p.parking_lot_id)

    for d in config.destinations:
        node_ids.add(d.destination_id)
        if d.status == EntityStatus.OPEN:
            add_node(walk_adjacency, d.destination_id)

    for r in config.roads:
        node_ids.add(r.start_node_id)
        node_ids.add(r.end_node_id)

        if r.status != EntityStatus.OPEN:
            continue  # closed/blocked/restricted/unknown roads are not routable

        if r.driveable:
            add_node(drive_adjacency, r.start_node_id)
            add_node(drive_adjacency, r.end_node_id)
            drive_adjacency[r.start_node_id][r.end_node_id] = r.length_meters
            if not r.one_way:
                drive_adjacency[r.end_node_id][r.start_node_id] = r.length_meters

        if r.walkable:
            add_node(walk_adjacency, r.start_node_id)
            add_node(walk_adjacency, r.end_node_id)
            walk_adjacency[r.start_node_id][r.end_node_id] = r.length_meters
            if not r.one_way:
                walk_adjacency[r.end_node_id][r.start_node_id] = r.length_meters

    return CampusGraph(
        campus_id=config.campus_id,
        configuration_version=config.configuration_version,
        drive_adjacency=drive_adjacency,
        walk_adjacency=walk_adjacency,
        node_ids=node_ids,
    )


def validate_campus_graph(config: CampusConfig, graph: CampusGraph) -> list:
    """Graph-level checks beyond config-level validation: reachability and
    open-entity connectivity. Returns a list of error strings."""
    errors = []

    open_gate_ids = {g.gate_id for g in config.gates if g.status == EntityStatus.OPEN}
    open_lot_ids = {p.parking_lot_id for p in config.parking_lots if p.status == EntityStatus.OPEN}

    for gate_id in open_gate_ids:
        if gate_id not in graph.drive_adjacency or not graph.drive_adjacency[gate_id]:
            reachable = any(
                gate_id in neighbors for neighbors in graph.drive_adjacency.values()
            )
            if not reachable:
                errors.append(f"Open gate '{gate_id}' has no reachable open road.")

    for lot_id in open_lot_ids:
        reachable = lot_id in graph.drive_adjacency and (
            graph.drive_adjacency[lot_id] or
            any(lot_id in neighbors for neighbors in graph.drive_adjacency.values())
        )
        if not reachable:
            errors.append(f"Open parking lot '{lot_id}' is not reachable by any open road.")

    if open_gate_ids and open_lot_ids:
        any_gate_reaches_any_lot = any(
            dijkstra(graph.drive_adjacency, gate_id, lot_id)[0]
            for gate_id in open_gate_ids
            for lot_id in open_lot_ids
        )
        if not any_gate_reaches_any_lot:
            errors.append("No open gate can currently reach any open parking lot.")

    return errors
