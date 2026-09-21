"""
Member 1 demonstration (see spec section 65): load a campus, build its
graph, initialize a Digital Twin, run a normal-day simulation, then show a
disruption's effect. Every printed number here is SYNTHETIC — this is a
demonstration of the pipeline, not a claim about real VIT-AP behavior.
"""

from pathlib import Path

from campus_twin.config import load_campus_config
from campus_twin.graph import build_campus_graph, validate_campus_graph
from campus_twin.scenarios import event, normal_day, road_closure
from campus_twin.simulation import SimulationEngine

PROJECT_FOLDER = Path(__file__).resolve().parent
CONFIGS = PROJECT_FOLDER / "data" / "campus_configs"


def main():
    print("=== STEP 1: Load VIT-AP campus configuration ===")
    config = load_campus_config(CONFIGS / "vitap.json")
    print(f"Loaded campus '{config.name}' ({config.configuration_version})")
    print(f"Gates: {len(config.gates)}, Roads: {len(config.roads)}, "
          f"Parking lots: {len(config.parking_lots)}, Destinations: {len(config.destinations)}")

    print("\n=== STEP 2: Build campus graph ===")
    graph = build_campus_graph(config)
    errors = validate_campus_graph(config, graph)
    print(f"Graph validation errors: {errors or 'none'}")

    print("\n=== STEP 3-13: Normal-day simulation ===")
    normal = normal_day(config.campus_id, config.configuration_version, seed=7, num_vehicles=30, duration_minutes=150)
    result = SimulationEngine().run(config, graph, normal)
    print(f"Scenario: {result.metrics['scenario_name']}, seed={result.seed}")
    print(f"Vehicles: {result.metrics['total_vehicles']} total, "
          f"{result.metrics['completed_vehicles']} completed, "
          f"{result.metrics['failed_vehicles']} failed to park")
    print(f"Final occupancy by lot: {result.metrics['final_occupancy_by_lot']}")
    print(f"Snapshots recorded: {len(result.snapshots)}")
    print(f"Provenance: {result.provenance.value}, result_type: {result.result_type}")

    print("\n=== STEP 14-15: Synthetic EVENT scenario (increased demand) ===")
    event_scenario = event(
        config.campus_id, config.configuration_version, seed=7, num_vehicles=30, duration_minutes=150,
        demand_multiplier=2.0, affected_destinations=["vitap-osm-1321555307"],  # Food Street
    )
    event_result = SimulationEngine().run(config, graph, event_scenario)
    print(f"Event scenario vehicle count: {event_result.metrics['total_vehicles']} "
          f"(normal was {result.metrics['total_vehicles']})")
    print("This multiplier is a SYNTHETIC assumption, not a measured VIT-AP event.")

    print("\n=== STEP 16-17: Close the only gate-to-lot road ===")
    closed_road_id = config.roads[0].road_id
    disrupted = road_closure(
        config.campus_id, config.configuration_version, closed_roads=[closed_road_id],
        seed=7, num_vehicles=30, duration_minutes=150,
    )
    disrupted_result = SimulationEngine().run(config, graph, disrupted)
    print(f"With road '{closed_road_id}' closed: "
          f"{disrupted_result.metrics['completed_vehicles']} completed, "
          f"{disrupted_result.metrics['failed_vehicles']} failed (expected: all fail, single-road campus)")

    print("\n=== STEP 22: Reproducibility metadata ===")
    print(f"simulation_id={result.simulation_id}, scenario_id={result.scenario_id}, "
          f"configuration_version={result.configuration_version}, seed={result.seed}")


if __name__ == "__main__":
    main()
