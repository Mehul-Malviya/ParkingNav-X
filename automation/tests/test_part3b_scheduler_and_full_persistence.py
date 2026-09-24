"""
Covers two gaps found in a self-audit against the Member 1 spec:
1. The simulation engine must persist gate/road/vehicle state into the
   Digital Twin, not just parking (Part 4: "update Part 3's Digital Twin
   (parking occupancy, gate queues, road load)").
2. Part 3 explicitly asks for a periodic snapshot scheduler.
"""

from pathlib import Path

import pytest

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.scheduler import SnapshotScheduler
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import AllocationStrategy, AssignmentResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIGS = PROJECT_ROOT / "configs" / "campuses"
SCENARIOS = PROJECT_ROOT / "configs" / "scenarios" / "sample"


class AlwaysNearestOpenStrategy(AllocationStrategy):
    def assign(self, vehicle, campus_state):
        for lot_id in sorted(campus_state.parking_lots):
            lot = campus_state.parking_lots[lot_id]
            if lot["status"] == "open" and lot["occupied_spaces"] < lot["usable_capacity"]:
                return AssignmentResult(parking_lot_id=lot_id, gate_id=vehicle.entry_gate)
        return AssignmentResult(parking_lot_id=None)


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    apply_migrations(c)
    load_campus_config(CONFIGS / "sample.yaml", c)
    yield c
    c.close()


def test_simulation_persists_gate_state(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "normal_day.yaml")
    SimulationEngine().run(scenario, AlwaysNearestOpenStrategy(), conn)
    rows = conn.execute("SELECT * FROM gate_state WHERE campus_id='sample'").fetchall()
    assert len(rows) == 1
    assert rows[0]["provenance"] == "SYNTHETIC"
    assert rows[0]["source"] == "simulation"


def test_simulation_persists_road_state(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "normal_day.yaml")
    SimulationEngine().run(scenario, AlwaysNearestOpenStrategy(), conn)
    rows = conn.execute("SELECT * FROM road_state WHERE campus_id='sample'").fetchall()
    assert len(rows) == 3  # sample.yaml has 3 roads
    for row in rows:
        assert row["congestion_level"] in ("free", "moderate", "heavy", "blocked")


def test_simulation_persists_vehicle_state(conn):
    scenario = ScenarioLoader.load(SCENARIOS / "normal_day.yaml")
    SimulationEngine().run(scenario, AlwaysNearestOpenStrategy(), conn)
    rows = conn.execute("SELECT * FROM vehicle_state WHERE campus_id='sample'").fetchall()
    assert len(rows) == scenario.vehicle_count
    assert all(r["source"] == "simulation" for r in rows)


def test_snapshot_scheduler_runs_and_writes_snapshots(conn, tmp_path):
    db_path = tmp_path / "test.db"

    def factory():
        return get_connection(db_path)

    scheduler = SnapshotScheduler("sample", factory, interval_seconds=999999)
    before = conn.execute("SELECT COUNT(*) FROM campus_state_snapshot WHERE campus_id='sample'").fetchone()[0]
    scheduler.run_once_now()
    scheduler.run_once_now()
    after = conn.execute("SELECT COUNT(*) FROM campus_state_snapshot WHERE campus_id='sample'").fetchone()[0]
    assert after == before + 2
    assert scheduler.snapshot_count == 2


def test_scheduler_start_stop_does_not_crash(conn, tmp_path):
    db_path = tmp_path / "test.db"
    scheduler = SnapshotScheduler("sample", lambda: get_connection(db_path), interval_seconds=999999)
    scheduler.start()
    scheduler.stop()  # should cleanly cancel before the (huge) interval ever fires


if __name__ == "__main__":
    print("Run with pytest: python -m pytest test_part3b_scheduler_and_full_persistence.py -v")
