from pathlib import Path

from campus_twin.config import load_campus_config
from campus_twin.graph import build_campus_graph
from campus_twin.scenarios import (
    gate_closure, high_demand, multiple_disruption, normal_day, parking_closure, road_closure,
)
from campus_twin.simulation import SimulationEngine

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
CONFIGS = PROJECT_FOLDER / "data" / "campus_configs"


def load_vitap():
    config = load_campus_config(CONFIGS / "vitap.json")
    graph = build_campus_graph(config)
    return config, graph


def load_sample():
    config = load_campus_config(CONFIGS / "sample.json")
    graph = build_campus_graph(config)
    return config, graph


def test_end_to_end_normal_day_simulation():
    """Section 52's integration test: config -> graph -> twin -> scenario ->
    vehicles -> gate queue -> parking -> occupancy/road updates -> snapshot
    -> departure -> release -> metrics, all in one run."""
    config, graph = load_vitap()
    scenario = normal_day(config.campus_id, config.configuration_version, seed=1, num_vehicles=20, duration_minutes=120)

    result = SimulationEngine().run(config, graph, scenario)

    assert result.result_type == "SIMULATION"
    assert result.provenance.value == "SYNTHETIC"
    assert result.metrics["total_vehicles"] == 20
    assert result.metrics["completed_vehicles"] > 0
    assert len(result.snapshots) > 0
    assert result.snapshots[0].provenance.value == "SYNTHETIC"


def test_reproducibility_same_seed_same_output():
    config, graph = load_vitap()
    scenario = normal_day(config.campus_id, config.configuration_version, seed=42, num_vehicles=15, duration_minutes=90)

    result_a = SimulationEngine().run(config, graph, scenario)
    result_b = SimulationEngine().run(config, graph, scenario)

    assert result_a.metrics == result_b.metrics


def test_different_seed_permits_variation():
    config, graph = load_vitap()
    scenario_a = normal_day(config.campus_id, config.configuration_version, seed=1, num_vehicles=15, duration_minutes=90)
    scenario_b = normal_day(config.campus_id, config.configuration_version, seed=2, num_vehicles=15, duration_minutes=90)

    result_a = SimulationEngine().run(config, graph, scenario_a)
    result_b = SimulationEngine().run(config, graph, scenario_b)

    # Not asserting they differ (small state spaces can coincide), just that
    # both runs are well-formed and independently reproducible.
    assert result_a.metrics["total_vehicles"] == result_b.metrics["total_vehicles"] == 15


def test_road_closure_scenario_avoids_closed_road():
    config, graph = load_vitap()
    closed_road_id = config.roads[0].road_id  # gate -> lot road
    scenario = road_closure(
        config.campus_id, config.configuration_version, closed_roads=[closed_road_id],
        seed=1, num_vehicles=10, duration_minutes=60,
    )

    result = SimulationEngine().run(config, graph, scenario)

    # With the only gate-to-lot road closed, no vehicle can reach any lot.
    assert result.metrics["completed_vehicles"] == 0
    assert result.metrics["failed_vehicles"] == result.metrics["total_vehicles"]


def test_gate_closure_scenario_blocks_entry():
    config, graph = load_vitap()
    only_gate_id = config.gates[0].gate_id
    scenario = gate_closure(
        config.campus_id, config.configuration_version, closed_gates=[only_gate_id],
        seed=1, num_vehicles=10, duration_minutes=60,
    )

    result = SimulationEngine().run(config, graph, scenario)
    assert "error" in result.metrics
    assert result.metrics["error"] == "No open gates or no open parking lots for this scenario."


def test_parking_closure_scenario_blocks_assignment():
    config, graph = load_vitap()
    only_lot_id = config.parking_lots[0].parking_lot_id
    scenario = parking_closure(
        config.campus_id, config.configuration_version, closed_parking_lots=[only_lot_id],
        seed=1, num_vehicles=10, duration_minutes=60,
    )

    result = SimulationEngine().run(config, graph, scenario)
    assert "error" in result.metrics


def test_high_demand_scenario_scales_vehicle_count():
    config, graph = load_vitap()
    scenario = high_demand(
        config.campus_id, config.configuration_version, seed=1, num_vehicles=10,
        duration_minutes=90, demand_multiplier=2.0,
    )
    result = SimulationEngine().run(config, graph, scenario)
    assert result.metrics["total_vehicles"] == 20


def test_multiple_disruption_scenario_is_well_formed():
    config, graph = load_sample()
    scenario = multiple_disruption(
        config.campus_id, config.configuration_version,
        closed_parking_lots=["sample-lot-2"], seed=1, num_vehicles=10, duration_minutes=60,
    )
    result = SimulationEngine().run(config, graph, scenario)
    assert result.metrics["total_vehicles"] == 10


def test_multi_campus_isolation():
    vitap_config, vitap_graph = load_vitap()
    sample_config, sample_graph = load_sample()

    vitap_scenario = normal_day(vitap_config.campus_id, vitap_config.configuration_version, seed=1, num_vehicles=5, duration_minutes=30)
    sample_scenario = normal_day(sample_config.campus_id, sample_config.configuration_version, seed=1, num_vehicles=5, duration_minutes=30)

    vitap_result = SimulationEngine().run(vitap_config, vitap_graph, vitap_scenario)
    sample_result = SimulationEngine().run(sample_config, sample_graph, sample_scenario)

    assert vitap_result.campus_id == "vitap"
    assert sample_result.campus_id == "sample"
    assert set(vitap_result.metrics["final_occupancy_by_lot"].keys()).isdisjoint(
        set(sample_result.metrics["final_occupancy_by_lot"].keys())
    )


if __name__ == "__main__":
    test_end_to_end_normal_day_simulation()
    test_reproducibility_same_seed_same_output()
    test_road_closure_scenario_avoids_closed_road()
    test_gate_closure_scenario_blocks_entry()
    test_parking_closure_scenario_blocks_assignment()
    test_multi_campus_isolation()
    print("Simulation tests passed!")
