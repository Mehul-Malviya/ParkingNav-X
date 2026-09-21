from pathlib import Path

import pytest

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import (
    AllocationStrategy, AssignmentResult, FixedLotStrategy,
)

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIGS = PROJECT_ROOT / "configs" / "campuses"
SCENARIOS = PROJECT_ROOT / "configs" / "scenarios" / "sample"


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    apply_migrations(c)
    load_campus_config(CONFIGS / "sample.yaml", c)
    yield c
    c.close()


class AlwaysNearestOpenStrategy(AllocationStrategy):
    """Minimal real-ish strategy for engine tests -- picks the first open,
    available lot by sorted id. Not owned by Member 1 in spirit; used here
    only to exercise the engine end-to-end."""

    def assign(self, vehicle, campus_state):
        for lot_id in sorted(campus_state.parking_lots):
            lot = campus_state.parking_lots[lot_id]
            if lot["status"] == "open" and lot["occupied_spaces"] < lot["usable_capacity"]:
                return AssignmentResult(parking_lot_id=lot_id, gate_id=vehicle.entry_gate)
        return AssignmentResult(parking_lot_id=None)


def test_same_seed_produces_byte_identical_metrics(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "normal_day.yaml")
    engine = SimulationEngine()

    result_a = engine.run(scenario, AlwaysNearestOpenStrategy(), conn, run_id="run-a")
    result_b = engine.run(scenario, AlwaysNearestOpenStrategy(), conn, run_id="run-b")

    assert result_a.vehicles == result_b.vehicles
    assert result_a.timesteps == result_b.timesteps


def test_closed_parking_lot_receives_zero_assignments(conn):
    raw_scenario = SCENARIOS / "parking_closure.yaml"
    scenario = ScenarioLoader.load(raw_scenario)
    engine = SimulationEngine()
    result = engine.run(scenario, AlwaysNearestOpenStrategy(), conn)

    assigned_lots = {v["assigned_lot_id"] for v in result.vehicles if v["assigned_lot_id"]}
    assert "sample-lot-1" not in assigned_lots


def test_closed_gate_admits_zero_vehicles(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "gate_closure.yaml")
    engine = SimulationEngine()
    result = engine.run(scenario, AlwaysNearestOpenStrategy(), conn)

    assert all(v["assigned_lot_id"] is None for v in result.vehicles)
    assert all(v["waiting_time_seconds"] == 0 for v in result.vehicles)


def test_gate_queue_length_never_negative(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "normal_day.yaml")
    engine = SimulationEngine()
    result = engine.run(scenario, AlwaysNearestOpenStrategy(), conn)

    for ts in result.timesteps:
        for key, value in ts.items():
            if key.startswith("gate_queue_"):
                assert value >= 0


def test_parking_occupancy_never_exceeds_usable_capacity(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "normal_day.yaml")
    engine = SimulationEngine()
    result = engine.run(scenario, AlwaysNearestOpenStrategy(), conn)

    max_occupancy_seen = max(
        (v for ts in result.timesteps for k, v in ts.items() if k == "parking_occupancy_sample-lot-1"),
        default=0,
    )
    assert max_occupancy_seen <= 18  # sample-lot-1 usable_capacity


def test_fixed_lot_strategy_is_actually_called_not_bypassed(conn):
    """Trivial 2-vehicle scenario: every vehicle must end up assigned to
    the strategy's fixed lot -- proving the engine calls the interface."""
    import yaml
    raw = yaml.safe_load(open(SCENARIOS / "normal_day.yaml"))
    raw["vehicle_count"] = 2
    raw["duration_minutes"] = 30
    scenario = ScenarioLoader.from_dict(raw)

    engine = SimulationEngine()
    result = engine.run(scenario, FixedLotStrategy("sample-lot-2"), conn)

    assigned = [v["assigned_lot_id"] for v in result.vehicles]
    assert assigned == ["sample-lot-2", "sample-lot-2"]


def test_overflow_event_recorded_once_per_timestep_not_per_vehicle(conn):
    import yaml
    raw = yaml.safe_load(open(SCENARIOS / "normal_day.yaml"))
    raw["vehicle_count"] = 5
    raw["duration_minutes"] = 30  # long enough that every vehicle finishes its search
    raw["arrival_rate_profile"] = {"type": "constant", "rate": 5.0}
    scenario = ScenarioLoader.from_dict(raw)

    engine = SimulationEngine()
    # A strategy that always points at a nonexistent lot forces every search to fail.
    result = engine.run(scenario, FixedLotStrategy("nonexistent-lot"), conn)

    assert all(v["assigned_lot_id"] is None for v in result.vehicles)
    assert all(v["final_state"] == "completed" for v in result.vehicles)
    # One failed attempt logged per vehicle...
    assert len(result.overflow_events) == 5
    # ...but the per-timestep flag must collapse same-tick duplicates into one boolean, not a count.
    for ts in result.timesteps:
        for key, value in ts.items():
            if key.startswith("overflow_"):
                assert value in (True, False)


if __name__ == "__main__":
    print("Run with pytest: python -m pytest test_part4_part5_simulation.py -v")
