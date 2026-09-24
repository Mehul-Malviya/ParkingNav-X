"""
Module 2: Scenario / Event Configuration.

Scenario parameters here are SYNTHETIC/SAMPLE by construction. None of them
is claimed to represent real VIT-AP (or any campus's) behavior unless a
future calibration step (Module 6A) explicitly marks it CALIBRATED_FROM_REAL_DATA.
"""

from dataclasses import dataclass, field
from typing import Optional

from campus_twin.config import Provenance


@dataclass
class Scenario:
    scenario_id: str
    scenario_name: str
    campus_id: str
    configuration_version: str
    duration_minutes: int
    seed: int
    num_vehicles: int = 50
    arrival_profile: str = "uniform"  # uniform | peaked
    entry_gate_weights: Optional[dict] = None   # gate_id -> weight
    destination_weights: Optional[dict] = None  # destination_id -> weight
    dwell_time_minutes: tuple = (30, 180)        # (min, max) uniform range
    closed_gates: list = field(default_factory=list)
    closed_roads: list = field(default_factory=list)
    closed_parking_lots: list = field(default_factory=list)
    demand_multiplier: float = 1.0
    start_time_minutes: int = 0
    provenance: Provenance = Provenance.SYNTHETIC


def normal_day(campus_id, configuration_version, seed=1, num_vehicles=50, duration_minutes=180):
    return Scenario(
        scenario_id=f"{campus_id}-normal-day-{seed}",
        scenario_name="NORMAL_DAY",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
    )


def high_demand(campus_id, configuration_version, seed=1, num_vehicles=50, duration_minutes=180,
                 demand_multiplier=2.0):
    return Scenario(
        scenario_id=f"{campus_id}-high-demand-{seed}",
        scenario_name="HIGH_DEMAND",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
        arrival_profile="peaked",
        demand_multiplier=demand_multiplier,
    )


def event(campus_id, configuration_version, seed=1, num_vehicles=50, duration_minutes=180,
          demand_multiplier=1.5, affected_destinations=None):
    return Scenario(
        scenario_id=f"{campus_id}-event-{seed}",
        scenario_name="EVENT",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
        demand_multiplier=demand_multiplier,
        destination_weights={d: 3.0 for d in (affected_destinations or [])} or None,
    )


def parking_closure(campus_id, configuration_version, closed_parking_lots, seed=1,
                     num_vehicles=50, duration_minutes=180):
    return Scenario(
        scenario_id=f"{campus_id}-parking-closure-{seed}",
        scenario_name="PARKING_CLOSURE",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
        closed_parking_lots=list(closed_parking_lots),
    )


def gate_closure(campus_id, configuration_version, closed_gates, seed=1,
                  num_vehicles=50, duration_minutes=180):
    return Scenario(
        scenario_id=f"{campus_id}-gate-closure-{seed}",
        scenario_name="GATE_CLOSURE",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
        closed_gates=list(closed_gates),
    )


def road_closure(campus_id, configuration_version, closed_roads, seed=1,
                  num_vehicles=50, duration_minutes=180):
    return Scenario(
        scenario_id=f"{campus_id}-road-closure-{seed}",
        scenario_name="ROAD_CLOSURE",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
        closed_roads=list(closed_roads),
    )


def multiple_disruption(campus_id, configuration_version, closed_gates=None, closed_roads=None,
                         closed_parking_lots=None, seed=1, num_vehicles=50, duration_minutes=180):
    return Scenario(
        scenario_id=f"{campus_id}-multiple-disruption-{seed}",
        scenario_name="MULTIPLE_DISRUPTION",
        campus_id=campus_id,
        configuration_version=configuration_version,
        duration_minutes=duration_minutes,
        seed=seed,
        num_vehicles=num_vehicles,
        closed_gates=list(closed_gates or []),
        closed_roads=list(closed_roads or []),
        closed_parking_lots=list(closed_parking_lots or []),
    )
