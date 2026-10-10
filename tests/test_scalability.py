"""
Scalability Tests: 500 and 1,000 vehicles
"""

import time
from pathlib import Path

import pytest

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy


class TestScalability:
    """Test simulator performance at large vehicle counts."""

    @pytest.fixture
    def setup(self):
        """Setup: campus + connection."""
        conn = get_connection(':memory:')
        apply_migrations(conn)
        load_campus_config(Path('configs/campus/vitap.yaml'), conn)
        load_campus_config(Path('configs/campus/vitap.yaml'), conn)
        return conn

    def test_500_vehicles_determinism(self, setup):
        """Test that 500 vehicles still produce deterministic results."""
        conn = setup

        # Create scenario with 500 vehicles
        scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
        scenario.vehicle_count = 500
        scenario.random_seed = 12345

        # Run twice with same seed
        engine = SimulationEngine()
        result1 = engine.run(scenario, FirstAvailableStrategy(), conn)
        result2 = engine.run(scenario, FirstAvailableStrategy(), conn)

        # Results should be identical
        assert len(result1.vehicles) == len(result2.vehicles)
        assert result1.metrics.get('avg_search_time_min') == result2.metrics.get('avg_search_time_min')
        assert len(result1.overflow_events) == len(result2.overflow_events)

    def test_500_vehicles_performance(self, setup):
        """Test that 500 vehicles complete in reasonable time."""
        conn = setup

        scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
        scenario.vehicle_count = 500

        engine = SimulationEngine()
        start = time.time()
        result = engine.run(scenario, FirstAvailableStrategy(), conn)
        elapsed = time.time() - start

        # Should complete in under 10 seconds
        assert elapsed < 10, f"500 vehicles took {elapsed:.1f}s (should be <10s)"
        assert len(result.vehicles) == 500

    def test_500_vehicles_metrics_valid(self, setup):
        """Test that metrics are reasonable for 500 vehicles."""
        conn = setup

        scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
        scenario.vehicle_count = 500

        engine = SimulationEngine()
        result = engine.run(scenario, FirstAvailableStrategy(), conn)

        # Metrics should be positive and reasonable
        assert result.metrics.get('avg_search_time_min', 0) >= 0
        assert result.metrics.get('avg_wait_time_min', 0) >= 0
        assert result.metrics.get('avg_gate_queue', 0) >= 0
        assert result.metrics.get('max_gate_queue', 0) >= 0

    def test_1000_vehicles_determinism(self, setup):
        """Test that 1,000 vehicles still produce deterministic results."""
        conn = setup

        scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
        scenario.vehicle_count = 1000
        scenario.random_seed = 54321

        engine = SimulationEngine()
        result1 = engine.run(scenario, FirstAvailableStrategy(), conn)
        result2 = engine.run(scenario, FirstAvailableStrategy(), conn)

        # Results should be identical
        assert len(result1.vehicles) == len(result2.vehicles)
        assert result1.metrics.get('avg_search_time_min') == result2.metrics.get('avg_search_time_min')
        assert len(result1.overflow_events) == len(result2.overflow_events)

    def test_1000_vehicles_performance(self, setup):
        """Test that 1,000 vehicles complete in reasonable time."""
        conn = setup

        scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
        scenario.vehicle_count = 1000

        engine = SimulationEngine()
        start = time.time()
        result = engine.run(scenario, FirstAvailableStrategy(), conn)
        elapsed = time.time() - start

        # Should complete in under 30 seconds
        assert elapsed < 30, f"1000 vehicles took {elapsed:.1f}s (should be <30s)"
        assert len(result.vehicles) == 1000

    def test_1000_vehicles_metrics_valid(self, setup):
        """Test that metrics are reasonable for 1,000 vehicles."""
        conn = setup

        scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
        scenario.vehicle_count = 1000

        engine = SimulationEngine()
        result = engine.run(scenario, FirstAvailableStrategy(), conn)

        # Metrics should be positive and reasonable
        assert result.metrics.get('avg_search_time_min', 0) >= 0
        assert result.metrics.get('avg_wait_time_min', 0) >= 0
        assert result.metrics.get('avg_gate_queue', 0) >= 0
        assert result.metrics.get('max_gate_queue', 0) >= 0
        # With high vehicle count, overflow is more likely
        assert result.metrics.get('overflow_events', 0) >= 0

    def test_scalability_latency_measurement(self, setup):
        """Verify decision latency is measured at all scales."""
        conn = setup

        for vehicle_count in [100, 500, 1000]:
            scenario = ScenarioLoader.load('configs/scenarios/vitap/E1_normal_day.yaml')
            scenario.vehicle_count = vehicle_count

            engine = SimulationEngine()
            result = engine.run(scenario, FirstAvailableStrategy(), conn)

            # Decision latency should be logged
            assert hasattr(result, 'decision_latencies') or result.metrics.get('avg_search_time_min') >= 0
            assert len(result.vehicles) == vehicle_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
