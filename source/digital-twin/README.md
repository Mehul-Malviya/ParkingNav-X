# digital_twin/

The active Member 1 subsystem: Campus Configuration → Campus Graph →
Digital Twin State → Simulation → Scenarios, plus the FastAPI app and
CLI tools that expose all of it. Full writeup:
[docs/MEMBER1_SUBSYSTEM_REPORT.md](../docs/MEMBER1_SUBSYSTEM_REPORT.md).

| File/folder | What it is |
|---|---|
| `db.py` | SQLite connection + migration runner (see `../migrations/`) |
| `models.py` | Shared enums: `Provenance`, `EntityStatus`, `FreshnessState`, etc. |
| `config_loader.py` | Loads/validates a campus YAML (`../configs/campuses/*.yaml`) into the DB |
| `gps_survey_import.py` | Converts a GPX+CSV survey into that same YAML format |
| `graph_service.py` | Builds a `networkx` graph per campus — structure only, no pathfinding |
| `twin_service.py` | `DigitalTwinService` — the live campus state: parking/gate/road/vehicle, snapshots, history |
| `scheduler.py` | `SnapshotScheduler` — periodic `snapshot_now()` calls |
| `simulation/` | The deterministic simulation engine, scenario loader/validator, the `AllocationStrategy` interface |
| `api/app.py` | FastAPI app exposing all of the above |
| `cli/` | `run.py` (simulation), `validate_scenario.py` |

## Quick start

```bash
pip install -r ../requirements.txt      # from repo root
python ../scripts/load_campus_config.py --config ../configs/campuses/vitap.yaml
python -m pytest ../tests/
python -m digital_twin.cli.run --campus vitap --scenario ../configs/scenarios/vitap/normal_day.yaml --strategy digital_twin.simulation.demo_strategies.DemoNearestAvailableStrategy
```

(Run these from the repo root, not from inside this folder — the `..`
paths above assume that.)
