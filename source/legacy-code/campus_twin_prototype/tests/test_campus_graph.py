from pathlib import Path

from campus_twin.config import load_campus_config
from campus_twin.graph import build_campus_graph, validate_campus_graph

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
CONFIGS = PROJECT_FOLDER / "data" / "campus_configs"


def test_vitap_graph_builds_and_validates():
    config = load_campus_config(CONFIGS / "vitap.json")
    graph = build_campus_graph(config)
    assert graph.campus_id == "vitap"
    errors = validate_campus_graph(config, graph)
    assert errors == []


def test_gate_can_reach_parking_lot():
    config = load_campus_config(CONFIGS / "vitap.json")
    graph = build_campus_graph(config)
    route, cost = graph.shortest_route("vitap-gate-placeholder", "vitap-lot-placeholder", mode="drive")
    assert route == ["vitap-gate-placeholder", "vitap-lot-placeholder"]
    assert cost == 275


def test_closed_road_removes_edge_from_graph():
    config = load_campus_config(CONFIGS / "vitap.json")
    config.roads[0].status = "CLOSED"
    graph = build_campus_graph(config)
    route, cost = graph.shortest_route("vitap-gate-placeholder", "vitap-lot-placeholder", mode="drive")
    assert route == []
    assert cost == float("inf")


def test_graph_construction_is_deterministic():
    config = load_campus_config(CONFIGS / "vitap.json")
    graph_a = build_campus_graph(config)
    graph_b = build_campus_graph(config)
    assert graph_a.drive_adjacency == graph_b.drive_adjacency
    assert graph_a.walk_adjacency == graph_b.walk_adjacency


def test_sample_campus_graph_validates():
    config = load_campus_config(CONFIGS / "sample.json")
    graph = build_campus_graph(config)
    errors = validate_campus_graph(config, graph)
    assert errors == []


if __name__ == "__main__":
    test_vitap_graph_builds_and_validates()
    test_gate_can_reach_parking_lot()
    test_closed_road_removes_edge_from_graph()
    test_graph_construction_is_deterministic()
    test_sample_campus_graph_validates()
    print("Campus graph tests passed!")
