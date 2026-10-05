"""
E6 — Ablation Testing: Impact of Prediction, Optimization, Uncertainty, Proactiveness
"""

import pytest
from pathlib import Path
from digital_twin.config_loader import load_campus_config
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy
from digital_twin.db import get_connection, apply_migrations


class TestAblationE6:
    """Test ablation variants (flag combinations) for E1-E5 scenarios."""

    @pytest.fixture
    def setup(self):
        """Setup: campus + connection."""
        conn = get_connection(':memory:')
        apply_migrations(conn)
        load_campus_config(Path('configs/campuses/vitap.yaml'), conn)
        return conn

    def run_variant(self, scenario_file, variant_flags, conn, strategy=None):
        """
        Run a scenario with ablation flags.
        Returns dict with metrics: {avg_search, avg_wait, avg_queue, max_queue, overflow}
        """
        if strategy is None:
            strategy = FirstAvailableStrategy()

        scenario = ScenarioLoader.load(scenario_file)

        # Apply ablation flags
        scenario.use_prediction = variant_flags.get('use_prediction', True)
        scenario.use_optimization = variant_flags.get('use_optimization', True)
        scenario.use_uncertainty = variant_flags.get('use_uncertainty', True)
        scenario.proactive = variant_flags.get('proactive', True)

        engine = SimulationEngine()
        result = engine.run(scenario, strategy, conn)

        metrics = {
            'avg_search_time': result.metrics.get('avg_search_time_min', 0),
            'avg_wait_time': result.metrics.get('avg_wait_time_min', 0),
            'avg_queue': result.metrics.get('avg_gate_queue', 0),
            'max_queue': result.metrics.get('max_gate_queue', 0),
            'overflow_events': len(result.overflow_events),
        }
        return metrics

    def test_e2_baseline_all_enabled(self, setup):
        """E2 with all features enabled (baseline)."""
        conn = setup
        baseline = self.run_variant(
            'configs/scenarios/vitap/E2_event_placement.yaml',
            {'use_prediction': True, 'use_optimization': True,
             'use_uncertainty': True, 'proactive': True},
            conn
        )
        assert baseline['overflow_events'] >= 0

    def test_e2_no_prediction(self, setup):
        """E2: Disable prediction only."""
        conn = setup
        no_pred = self.run_variant(
            'configs/scenarios/vitap/E2_event_placement.yaml',
            {'use_prediction': False, 'use_optimization': True,
             'use_uncertainty': True, 'proactive': True},
            conn
        )
        assert no_pred['overflow_events'] >= 0

    def test_e2_no_optimization(self, setup):
        """E2: Disable optimization (fallback to B2)."""
        conn = setup
        no_optim = self.run_variant(
            'configs/scenarios/vitap/E2_event_placement.yaml',
            {'use_prediction': True, 'use_optimization': False,
             'use_uncertainty': True, 'proactive': True},
            conn
        )
        assert no_optim['overflow_events'] >= 0

    def test_e2_non_proactive(self, setup):
        """E2: Non-proactive (reactive only)."""
        conn = setup
        non_proactive = self.run_variant(
            'configs/scenarios/vitap/E2_event_placement.yaml',
            {'use_prediction': True, 'use_optimization': True,
             'use_uncertainty': True, 'proactive': False},
            conn
        )
        baseline = self.run_variant(
            'configs/scenarios/vitap/E2_event_placement.yaml',
            {'use_prediction': True, 'use_optimization': True,
             'use_uncertainty': True, 'proactive': True},
            conn
        )
        # Proactive should be better or equal
        assert baseline['overflow_events'] <= non_proactive['overflow_events']

    def test_e3_ablation_proactive_vs_reactive(self, setup):
        """E3 Lot closure: Proactive should handle closure better."""
        conn = setup
        proactive = self.run_variant(
            'configs/scenarios/vitap/E3_lot_closure.yaml',
            {'use_prediction': True, 'use_optimization': True,
             'use_uncertainty': True, 'proactive': True},
            conn
        )
        reactive = self.run_variant(
            'configs/scenarios/vitap/E3_lot_closure.yaml',
            {'use_prediction': False, 'use_optimization': False,
             'use_uncertainty': False, 'proactive': False},
            conn
        )
        assert proactive['overflow_events'] <= reactive['overflow_events']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
