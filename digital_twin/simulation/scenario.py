"""
Part 6: Scenario Generation -- the configuration layer Part 4's engine
executes. Scenarios are YAML files under configs/scenarios/{campus_id}/.
Every scenario is SYNTHETIC by construction; none is presented as real
campus behavior.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from digital_twin.models import ConfigError


@dataclass
class ScenarioConfig:
    scenario_id: str
    campus_id: str
    name: str
    duration_minutes: int
    vehicle_count: int
    arrival_rate_profile: dict          # {"type": "constant", "rate": n} or {"type": "profile", "points": [{time, rate}, ...]}
    event_conditions: Optional[dict]    # {"event_id": ...} or {"ad_hoc": true, "demand_multiplier": n}
    availability_overrides: dict        # {"closed_gates": [], "closed_parking_lots": [], "closed_roads": []}
    prediction_error_injection_level: float
    random_seed: int


class ScenarioLoader:
    @staticmethod
    def load(path) -> ScenarioConfig:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return ScenarioLoader.from_dict(raw)

    @staticmethod
    def from_dict(raw: dict) -> ScenarioConfig:
        if "random_seed" not in raw:
            raise ConfigError(
                f"Scenario '{raw.get('scenario_id', '?')}' is missing random_seed. "
                "No scenario runs without an explicit seed."
            )
        return ScenarioConfig(
            scenario_id=raw["scenario_id"],
            campus_id=raw["campus_id"],
            name=raw["name"],
            duration_minutes=raw["duration_minutes"],
            vehicle_count=raw["vehicle_count"],
            arrival_rate_profile=raw["arrival_rate_profile"],
            event_conditions=raw.get("event_conditions"),
            availability_overrides=raw.get(
                "availability_overrides",
                {"closed_gates": [], "closed_parking_lots": [], "closed_roads": []},
            ),
            prediction_error_injection_level=raw.get("prediction_error_injection_level", 0.0),
            random_seed=raw["random_seed"],
        )


class ScenarioValidator:
    @staticmethod
    def validate(scenario: ScenarioConfig, conn) -> list:
        errors = []

        campus_row = conn.execute(
            "SELECT campus_id FROM campuses WHERE campus_id=?", (scenario.campus_id,)
        ).fetchone()
        if not campus_row:
            errors.append(f"Scenario references unknown campus_id '{scenario.campus_id}'.")
            return errors  # nothing else can be checked meaningfully

        if scenario.vehicle_count < 0:
            errors.append("vehicle_count must be non-negative.")

        overrides = scenario.availability_overrides or {}

        def _exists(table, id_column, entity_id):
            row = conn.execute(
                f"SELECT 1 FROM {table} WHERE campus_id=? AND {id_column}=?",
                (scenario.campus_id, entity_id),
            ).fetchone()
            return row is not None

        for gate_id in overrides.get("closed_gates", []):
            if not _exists("gates", "gate_id", gate_id):
                errors.append(f"availability_overrides.closed_gates references unknown gate '{gate_id}' for campus '{scenario.campus_id}'.")

        for lot_id in overrides.get("closed_parking_lots", []):
            if not _exists("parking_lots", "parking_lot_id", lot_id):
                errors.append(f"availability_overrides.closed_parking_lots references unknown parking lot '{lot_id}' for campus '{scenario.campus_id}'.")

        for road_id in overrides.get("closed_roads", []):
            if not _exists("roads", "road_id", road_id):
                errors.append(f"availability_overrides.closed_roads references unknown road '{road_id}' for campus '{scenario.campus_id}'.")

        if scenario.event_conditions:
            ec = scenario.event_conditions
            if ec.get("ad_hoc"):
                if "demand_multiplier" not in ec:
                    errors.append("event_conditions.ad_hoc requires an explicit demand_multiplier.")
            else:
                event_id = ec.get("event_id")
                if not event_id or not _exists("events", "event_id", event_id):
                    errors.append(
                        f"event_conditions references unknown event_id '{event_id}' for campus "
                        f"'{scenario.campus_id}' and is not marked ad_hoc."
                    )

        return errors


CAMPUS_SCENARIOS_ROOT = Path(__file__).resolve().parent.parent.parent / "configs" / "scenarios"
