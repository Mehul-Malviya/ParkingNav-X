"""
E7 — Real Data Counterfactual Replay: Run simulator with real observations
"""

import pytest
import csv
from pathlib import Path
from digital_twin.config_loader import load_campus_config
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy, NearestAvailableStrategy
from digital_twin.validation.calibration import CounterfactualReplay, CalibrationReport
from digital_twin.db import get_connection, apply_migrations


class TestE7RealDataReplay:
    """Test counterfactual replay with real campus observations."""

    @pytest.fixture
    def setup(self):
        """Setup: campus + connection."""
        conn = get_connection(':memory:')
        apply_migrations(conn)
        load_campus_config(Path('configs/campuses/vitap.yaml'), conn)
        return conn

    def load_observations_csv(self, csv_path):
        """Load real observations from CSV."""
        observations = []
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                observations.append({
                    'timestamp': row['timestamp'],
                    'gate_id': row['gate_id'],
                    'lot_id': row['lot_id'],
                    'vehicle_arrivals': int(row['vehicle_arrivals']),
                    'vehicle_departures': int(row['vehicle_departures']),
                    'occupied_spaces': int(row['occupied_spaces']),
                    'total_capacity': int(row['total_capacity']),
                    'event_type': row['event_type'],
                    'confidence': float(row['confidence']),
                })
        return observations

    def test_load_sample_observations(self):
        """Verify sample observations CSV loads correctly."""
        csv_path = Path('data/sample_observations.csv')
        if not csv_path.exists():
            pytest.skip("sample_observations.csv not found (real data needed)")

        obs = self.load_observations_csv(csv_path)
        assert len(obs) > 0
        assert 'timestamp' in obs[0]
        assert 'vehicle_arrivals' in obs[0]
        assert 'occupied_spaces' in obs[0]

    def test_infer_scenario_from_real_observations(self):
        """Infer scenario config from real observations."""
        csv_path = Path('data/sample_observations.csv')
        if not csv_path.exists():
            pytest.skip("sample_observations.csv not found")

        obs = self.load_observations_csv(csv_path)

        # Use CounterfactualReplay to infer scenario
        scenario = CounterfactualReplay.infer_scenario_from_observations(obs)

        assert scenario is not None
        assert scenario['campus_id'] == 'vitap'
        assert scenario['vehicle_count'] > 0
        assert 'arrival_rate_profile' in scenario

    def test_counterfactual_replay_with_observations(self, setup):
        """Run counterfactual replay: real demand, different strategies."""
        csv_path = Path('data/sample_observations.csv')
        if not csv_path.exists():
            pytest.skip("sample_observations.csv not found (real data needed)")

        conn = setup
        obs = self.load_observations_csv(csv_path)

        # Infer scenario from observations
        scenario_dict = CounterfactualReplay.infer_scenario_from_observations(obs)
        scenario = ScenarioLoader.from_dict(scenario_dict)

        # Run with B1
        engine = SimulationEngine()
        result_b1 = engine.run(scenario, FirstAvailableStrategy(), conn)

        # Run with B2
        result_b2 = engine.run(scenario, NearestAvailableStrategy(), conn)

        # Compare metrics
        assert result_b1 is not None
        assert result_b2 is not None

        # B2 should generally have lower search time (uses nearest)
        b1_search = result_b1.metrics.get('avg_search_time_min', 0)
        b2_search = result_b2.metrics.get('avg_search_time_min', 0)

        # This is a qualitative check - B2 should be <=  B1
        assert b2_search <= b1_search or abs(b1_search - b2_search) < 0.1

    def test_calibration_report_with_simulated_observations(self, setup):
        """Generate calibration report comparing real vs simulated."""
        csv_path = Path('data/sample_observations.csv')
        if not csv_path.exists():
            pytest.skip("sample_observations.csv not found")

        conn = setup
        obs = self.load_observations_csv(csv_path)

        # Convert observations to calibration format
        real_data = [
            {
                'occupied': obs[i]['occupied_spaces'],
                'arrivals': obs[i]['vehicle_arrivals'],
                'departures': obs[i]['vehicle_departures'],
            }
            for i in range(len(obs))
        ]

        # Simulate scenario and collect similar data
        scenario_dict = CounterfactualReplay.infer_scenario_from_observations(obs)
        scenario = ScenarioLoader.from_dict(scenario_dict)

        engine = SimulationEngine()
        result = engine.run(scenario, FirstAvailableStrategy(), conn)

        # Extract simulated occupancy over time (from vehicles)
        sim_data = []
        for v in result.vehicles[:len(obs)]:  # Match observation count
            sim_data.append({
                'occupied': v.get('final_state') == 'parked' and 1 or 0,
                'arrivals': 1,  # Simplified
                'departures': 1 if v.get('final_state') == 'exited' else 0,
            })

        # Generate calibration report
        report = CalibrationReport(real_data, sim_data)

        mae = report.compute_mae('occupied')
        rmse = report.compute_rmse('occupied')
        bias = report.compute_bias('occupied')

        assert mae is not None
        assert rmse is not None
        assert bias is not None

    def test_honest_counterfactual_label(self):
        """Verify honest reporting: counterfactual results are estimates."""
        from digital_twin.validation.calibration import honest_counterfactual_label

        label = honest_counterfactual_label()

        assert label is not None
        assert 'simulation' in label.lower() or 'estimate' in label.lower()
        assert 'counterfactual' in label.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
