"""E4 gate closure: no arrivals use the closed main gate during the window; they divert to the visitor gate."""

from pathlib import Path

import pytest

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import NearestAvailableStrategy

MAIN, VISITOR = "vitap-gate-main", "vitap-gate-visitor"
START, END = 45, 105  # E4_gate_closure.yaml timed closure, in minutes


@pytest.fixture(scope="module")
def result():
    conn = get_connection(":memory:")
    apply_migrations(conn)
    load_campus_config(Path("configs/campus/vitap.yaml"), conn)
    scenario = ScenarioLoader.load(Path("configs/scenarios/vitap/E4_gate_closure.yaml"))
    scenario.random_seed = 7
    return SimulationEngine().run(scenario, NearestAvailableStrategy(), conn)


def _gates(result, lo, hi):
    return [v["entry_gate"] for v in result.vehicles if lo <= v["arrival_tick"] < hi]


def test_no_main_gate_arrivals_during_closure(result):
    during = _gates(result, START, END)
    assert during, "scenario should have arrivals inside the closure window"
    assert MAIN not in during
    assert set(during) == {VISITOR}


def test_main_gate_used_before_and_after_closure(result):
    assert MAIN in _gates(result, 0, START)
    assert MAIN in _gates(result, END, 10**6)


def test_all_vehicles_accounted_for(result):
    assert len(result.vehicles) == 400
