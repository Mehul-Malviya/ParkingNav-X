# Parking Nav X

A smart-parking research project for the VIT-AP campus. It models the campus
(gates, roads, parking lots, destinations) as a **digital twin**, simulates
vehicles arriving and parking, and is the base for the upcoming
prediction → risk → optimization stages.

## Folder layout

```
ParkingNav-X/
├── digital_twin/     The main Python package (campus model, simulation, API, CLI)
├── configs/
│   ├── campuses/     Campus definitions: vitap.yaml (real campus), sample.yaml (tiny test campus)
│   └── scenarios/    Simulation scenarios, one folder per campus (vitap/, sample/)
├── data/             30-day VIT-AP history CSVs (occupancy, gates, roads) + calendar/events
├── migrations/       SQLite database schema (applied automatically)
├── scripts/          Command-line helpers (load a campus, import data, generate data)
├── tests/            Automated tests for digital_twin/ (+ fixtures/)
├── docs/             Reports, roadmap, and data documentation
├── experiments/runs/ Simulation output (created when you run a simulation; not committed)
└── legacy/           The original prototype optimizer, kept for reference only
```

## Setup

```bash
pip install -r requirements.txt
```

## Common tasks

All commands run from the repo root.

Run the tests:

```bash
python -m pytest
```

Load the VIT-AP campus into the local database (`digital_twin.db`):

```bash
python scripts/load_campus_config.py --config configs/campuses/vitap.yaml
```

Import the 30-day history CSVs from `data/` into the same database:

```bash
python scripts/import_history_data.py
```

Run a simulation (output goes to `experiments/runs/<run-id>/`):

```bash
python -m digital_twin.cli.run --campus vitap --scenario configs/scenarios/vitap/normal_day.yaml --strategy digital_twin.simulation.demo_strategies.DemoNearestAvailableStrategy
```

Check a scenario file is valid before running it:

```bash
python -m digital_twin.cli.validate_scenario --config configs/scenarios/vitap/road_closure.yaml
```

Start the API at http://127.0.0.1:8000 (interactive docs at `/docs`):

```bash
uvicorn digital_twin.api.app:app --reload
```

## Documentation

| Doc | What's in it |
|---|---|
| [docs/MEMBER1_SUBSYSTEM_REPORT.md](docs/MEMBER1_SUBSYSTEM_REPORT.md) | How `digital_twin/` works: config, graph, twin state, simulation, API |
| [docs/STAGE6-8_DEVELOPMENT_ROADMAP.md](docs/STAGE6-8_DEVELOPMENT_ROADMAP.md) | Plan for the next stages: prediction, risk, optimization |
| [docs/PROJECT_COMPLETION_STATUS.md](docs/PROJECT_COMPLETION_STATUS.md) | Overall pipeline progress |
| [docs/data/](docs/data/) | VIT-AP data: provenance, completion report, quick start, dataset-generation prompt |
| [legacy/README.md](legacy/README.md) | The original flat optimizer (Dijkstra + risk scoring) |

## About the data

The campus layout and destination names come from public OpenStreetMap data.
The 30-day occupancy, gate-queue, and road-congestion data is **synthetic**:
generated, not measured at VIT-AP. Every record is labelled with its
provenance. See [docs/data/PROVENANCE.md](docs/data/PROVENANCE.md) for the
field-by-field breakdown.
