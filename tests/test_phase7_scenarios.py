"""
Phase 7 — Scenarios & Disruptions (M4)

Tests that all Phase 7 scenario files run end-to-end with B1 and B2 baselines.

Scenarios covered:
- E1: Normal day (baseline)
- E2: High-demand event (placement drive, multiplier 1.8x)
- E3: Parking lot closure (tests diversion)
- E4: Gate closure (tests queue buildup)
- E5: Robustness with forecast noise (0%, 10%, 20%)
"""

from pathlib import Path
import yaml
import pytest

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy, NearestAvailableStrategy
from digital_twin.simulation.forecast_noise import ForecastNoiseInjector

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIGS = PROJECT_ROOT / "configs" / "campuses"
SCENARIOS = PROJECT_ROOT / "configs" / "scenarios" / "vitap"


@pytest.fixture
def conn(tmp_path):
    """Database with VIT-AP campus loaded."""
    c = get_connection(tmp_path / "test.db")
    apply_migrations(c)
    load_campus_config(CONFIGS / "vitap.yaml", c)
    yield c
    c.close()


@pytest.fixture
def engine():
    return SimulationEngine()


class TestPhase7Scenarios:
    """Verify all Phase 7 scenarios run end-to-end."""

    def test_e1_normal_day_b1_b2(self, conn, engine):
        """E1: Normal day runs with both B1 and B2 (baseline)."""
        with open(SCENARIOS / "normal_day.yaml") as f:
            raw = yaml.safe_load(f)
        scenario = ScenarioLoader.from_dict(raw)

        result_b1 = engine.run(scenario, FirstAvailableStrategy(), conn)
        assert len(result_b1.vehicles) > 0

        result_b2 = engine.run(scenario, NearestAvailableStrategy(), conn)
        assert len(result_b2.vehicles) > 0

    def test_e2_event_placement_demand_spike(self, conn, engine):
        """E2: Placement event scenario loads and runs."""
        with open(SCENARIOS / "E2_event_placement.yaml") as f:
            raw = yaml.safe_load(f)

        scenario = ScenarioLoader.from_dict(raw)
        assert scenario.event_conditions is not None
        assert scenario.event_conditions["demand_multiplier"] == 1.8
        assert "academic" in scenario.event_conditions["affected_zones"]

        result = engine.run(scenario, FirstAvailableStrategy(), conn)
        assert len(result.vehicles) > 0

    def test_e3_lot_closure_diversion(self, conn, engine):
        """E3: Lot closure scenario loads and runs."""
        with open(SCENARIOS / "E3_lot_closure.yaml") as f:
            raw = yaml.safe_load(f)

        scenario = ScenarioLoader.from_dict(raw)
        assert len(scenario.availability_overrides["closed_parking_lots"]) > 0

        result = engine.run(scenario, FirstAvailableStrategy(), conn)
        assert len(result.vehicles) > 0

    def test_e4_gate_closure_queue_buildup(self, conn, engine):
        """E4: Gate closure scenario loads and runs."""
        with open(SCENARIOS / "E4_gate_closure.yaml") as f:
            raw = yaml.safe_load(f)

        scenario = ScenarioLoader.from_dict(raw)
        assert len(scenario.availability_overrides["closed_gates"]) > 0

        result = engine.run(scenario, FirstAvailableStrategy(), conn)
        assert len(result.vehicles) > 0
        # Check wait times are recorded
        wait_times = [v["waiting_time_seconds"] for v in result.vehicles
                     if v["waiting_time_seconds"] is not None]
        assert len(wait_times) > 0

    @pytest.mark.parametrize("noise_level", [0, 10, 20])
    def test_e5_robustness_noise_levels(self, conn, engine, noise_level):
        """E5: Robustness with forecast noise (σ=0%, 10%, 20%) runs without error."""
        scenario_file = SCENARIOS / f"E5_noise_{noise_level}.yaml"
        with open(scenario_file) as f:
            raw = yaml.safe_load(f)

        scenario = ScenarioLoader.from_dict(raw)
        assert scenario.prediction_error_injection_level == noise_level / 100.0

        result_b1 = engine.run(scenario, FirstAvailableStrategy(), conn)
        result_b2 = engine.run(scenario, NearestAvailableStrategy(), conn)

        assert len(result_b1.vehicles) > 0
        assert len(result_b2.vehicles) > 0

    def test_forecast_noise_injector(self):
        """ForecastNoiseInjector applies Gaussian noise correctly."""
        injector = ForecastNoiseInjector(noise_level=0.10, seed=999)

        forecast = {
            "occupancy_15min": 50.0,
            "occupancy_30min": 60.0,
            "queue_length_gate_1": 10.0,
            "other_field": "unchanged"
        }

        noisy = injector.perturb(forecast)

        # Numeric occupancy/queue fields should be perturbed
        assert abs(noisy["occupancy_15min"] - 50.0) > 0

        # Non-matching fields unchanged
        assert noisy["other_field"] == "unchanged"

        # All should be non-negative
        assert all(v >= 0 for k, v in noisy.items()
                  if isinstance(v, (int, float)) and k.startswith(("occupancy", "queue")))

    def test_forecast_noise_zero_level_no_op(self):
        """ForecastNoiseInjector with σ=0 is a no-op."""
        injector = ForecastNoiseInjector(noise_level=0.0, seed=999)
        forecast = {"occupancy_15min": 50.0, "queue_length_gate_1": 10.0}
        noisy = injector.perturb(forecast)
        assert noisy == forecast

    def test_scenario_ablation_flags(self):
        """Verify ablation flags are preserved in scenario config."""
        with open(SCENARIOS / "E2_event_placement.yaml") as f:
            raw = yaml.safe_load(f)

        scenario = ScenarioLoader.from_dict(raw)
        assert scenario.use_prediction is True
        assert scenario.use_optimization is True
        assert scenario.use_uncertainty is True
        assert scenario.proactive is True


if __name__ == "__main__":
    print("Run with: python -m pytest tests/test_phase7_scenarios.py -v")
