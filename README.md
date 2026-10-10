# Parking Nav X

A smart-parking research project for the VIT-AP campus. It models the campus
(gates, roads, parking lots, destinations) as a **digital twin**, simulates
vehicles arriving and parking, and is the base for the upcoming
prediction â†’ risk â†’ optimization stages.

## Folder layout

```
ParkingNav-X/
â”œâ”€â”€ digital_twin/     The main Python package (campus model, simulation, API, CLI)
â”œâ”€â”€ configs/
â”‚   â”œâ”€â”€ campuses/     Campus definitions: vitap.yaml (real campus), sample.yaml (tiny test campus)
â”‚   â””â”€â”€ scenarios/    Simulation scenarios, one folder per campus (vitap/, sample/)
â”œâ”€â”€ data/             30-day VIT-AP history CSVs (occupancy, gates, roads) + calendar/events
â”œâ”€â”€ migrations/       SQLite database schema (applied automatically)
â”œâ”€â”€ scripts/          Command-line helpers (load a campus, import data, generate data)
â”œâ”€â”€ tests/            Automated tests for digital_twin/ (+ fixtures/)
â”œâ”€â”€ docs/             Reports, roadmap, and data documentation
â”œâ”€â”€ experiments/runs/ Simulation output (created when you run a simulation; not committed)
â””â”€â”€ legacy/           The original prototype optimizer, kept for reference only
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
python scripts/load_campus_config.py --config configs/campus/vitap.yaml
```

> The former `scripts/import_history_data.py` (30-day history CSV import) is not in this repo, so that step was removed.

Run one simulation (prints the conservation check; `--verbose` adds hourly occupancy curves and one vehicle trace; output goes to `runs/<scenario>/<strategy>/seed_<n>/`):

```bash
python -m simulation run --scenario S1 --strategy nearest --seed 7 --verbose
# same code: python -m digital_twin.simulation.cli run --campus vitap --scenario E1_normal_day --strategy nearest --seed 7
# aliases: S1..S8 = E1_normal_day, E2_event_placement, E3_lot_closure, E4_gate_closure, E5_noise_0, E6_ablation, E7_replay, E8_vehicle_types
```

Run many scenarios x strategies x seeds in parallel, then rebuild the results table:

```bash
python scripts/run_batch.py --scenarios all --seeds 0-29 --strategies B1,B2,B3,B4 --jobs 12
python scripts/generate_results_summary.py     # writes docs/member1/results_summary.md
```

Check a scenario file is valid before running it:

```bash
python -m digital_twin.simulation.cli validate --campus vitap --scenario road_closure
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
