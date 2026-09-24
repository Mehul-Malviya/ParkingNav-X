from pathlib import Path

import pytest
import yaml

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.models import ConfigError
from digital_twin.simulation.scenario import ScenarioLoader, ScenarioValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIGS = PROJECT_ROOT / "configs" / "campuses"
SCENARIOS = PROJECT_ROOT / "configs" / "scenarios" / "sample"


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    apply_migrations(c)
    load_campus_config(CONFIGS / "sample.yaml", c)
    load_campus_config(CONFIGS / "vitap.yaml", c)
    yield c
    c.close()


@pytest.mark.parametrize("filename", [
    "normal_day.yaml", "high_demand_event.yaml", "parking_closure.yaml", "gate_closure.yaml",
])
def test_starter_scenario_validates_successfully(conn, filename):
    scenario = ScenarioLoader.load(SCENARIOS / filename)
    errors = ScenarioValidator.validate(scenario, conn)
    assert errors == []


def test_scenario_referencing_nonexistent_lot_fails_validation(conn):
    raw = yaml.safe_load(open(SCENARIOS / "parking_closure.yaml"))
    raw["availability_overrides"]["closed_parking_lots"] = ["does-not-exist"]
    scenario = ScenarioLoader.from_dict(raw)
    errors = ScenarioValidator.validate(scenario, conn)
    assert any("unknown parking lot" in e for e in errors)


def test_scenario_missing_random_seed_fails_validation():
    raw = yaml.safe_load(open(SCENARIOS / "normal_day.yaml"))
    del raw["random_seed"]
    with pytest.raises(ConfigError, match="random_seed"):
        ScenarioLoader.from_dict(raw)


def test_scenario_referencing_lot_from_other_campus_fails_validation(conn):
    raw = yaml.safe_load(open(SCENARIOS / "parking_closure.yaml"))
    raw["availability_overrides"]["closed_parking_lots"] = ["vitap-lot-placeholder"]  # exists, but for campus 'vitap'
    scenario = ScenarioLoader.from_dict(raw)
    errors = ScenarioValidator.validate(scenario, conn)
    assert any("unknown parking lot 'vitap-lot-placeholder'" in e for e in errors)


def test_ad_hoc_event_without_demand_multiplier_fails_validation(conn):
    raw = yaml.safe_load(open(SCENARIOS / "normal_day.yaml"))
    raw["event_conditions"] = {"ad_hoc": True}
    scenario = ScenarioLoader.from_dict(raw)
    errors = ScenarioValidator.validate(scenario, conn)
    assert any("demand_multiplier" in e for e in errors)


def test_event_conditions_referencing_real_event_id_validates(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "high_demand_event.yaml")
    errors = ScenarioValidator.validate(scenario, conn)
    assert errors == []


if __name__ == "__main__":
    print("Run with pytest: python -m pytest test_part6_scenarios.py -v")
