# Parking Nav X

## Repository layout

```
digital_twin/       Current, active Member 1 subsystem: campus config,
                     graph, Digital Twin state, simulation engine,
                     scenarios, FastAPI app, CLI tools.
migrations/          SQLite schema migrations for digital_twin/.
configs/             Campus (configs/campuses/) and scenario
                     (configs/scenarios/) YAML files.
scripts/             Standalone CLIs: load_campus_config.py,
                     gps_survey_to_config.py.
tests/               Tests for the active digital_twin/ subsystem
                     (run: python -m pytest tests/).
tests/fixtures/      Test fixtures (sample GPX/CSV survey data).
experiments/runs/    Simulation run output (Parquet), git-ignored.
data/                Real-data notes and prototype dataset generators
                     (see data/vitap_dataset_prototype/).
docs/                Reports and provenance documentation.
legacy/              Archived, superseded code — not part of the active
                     test suite. See legacy/README.md.
```

The sections below describe the *original* project (now archived under
`legacy/flat_optimizer/`) as it was received, before the `digital_twin/`
subsystem was built. See `docs/MEMBER1_SUBSYSTEM_REPORT.md` for the
current system's own documentation.

---

Parking Nav X is a Python-based smart parking recommendation system.

It helps a driver choose the best parking area by considering:

- the shortest route from an entry gate;
- road congestion;
- parking occupancy;
- blocked roads;
- closed gates;
- parking availability.

The project currently uses mock JSON data. It is designed so real parking and traffic data can be connected later.

## Features

- Finds shortest routes using a custom Dijkstra algorithm.
- Re-routes when roads are blocked.
- Rejects unavailable or full parking areas.
- Rejects closed entry gates.
- Calculates congestion and parking-overflow risk.
- Scores parking options using distance, congestion, and overflow risk.
- Recommends the lowest-scoring parking option.
- Compares the optimizer against simpler baseline methods.
- Includes tests for each main component.

## Project structure

ParkingNav_X/
│
├── data/
│   └── mock/
│       ├── mock_graph.json
│       ├── mock_parking.json
│       └── mock_predictions.json
│
├── optimization/
│   ├── baselines/
│   │   ├── first_available.py
│   │   └── nearest_available.py
│   │
│   ├── constraints/
│   │   ├── gate_constraints.py
│   │   ├── parking_constraints.py
│   │   └── road_constraints.py
│   │
│   ├── evaluation/
│   │   ├── comparison.py
│   │   ├── metrics.py
│   │   └── robustness.py
│   │
│   ├── objectives/
│   │   ├── cost_function.py
│   │   └── weights.py
│   │
│   ├── optimizer/
│   │   └── parking_optimizer.py
│   │
│   ├── recommendation/
│   │   └── recommendation.py
│   │
│   ├── risk/
│   │   ├── congestion_risk.py
│   │   └── overflow_risk.py
│   │
│   └── routing/
│       ├── dijkstra.py
│       ├── rerouting.py
│       └── route_cost.py
│
├── tests/
│   └── optimization/
│       ├── test_baselines.py
│       ├── test_constraints.py
│       ├── test_dijkstra.py
│       ├── test_evaluation.py
│       ├── test_objective.py
│       ├── test_optimizer.py
│       ├── test_recommendation.py
│       ├── test_rerouting.py
│       ├── test_risk.py
│       └── test_route_cost.py
│
├── main.py
├── README.md
└── requirements.txt


## Mock data

### Campus graph

`legacy/flat_optimizer/data/mock_graph.json` represents the campus road network.

Each location is a graph node, and each number is the travel cost between two connected locations.

Example:

"Gate1": {
  "RoadA": 2,
  "RoadB": 5
}

This means:

Gate1 → RoadA costs 2
Gate1 → RoadB costs 5

### Parking data

`legacy/flat_optimizer/data/mock_parking.json` stores the capacity and occupied spaces for every parking area.

Example:

"ParkingB": {
  "capacity": 80,
  "occupied": 72
}

ParkingB is 90% full.

### Congestion predictions

`legacy/flat_optimizer/data/mock_predictions.json` stores congestion-risk values between `0` and `1`.

"RoadD": 0.9

A value of `0.9` means RoadD has high congestion.

## How the recommendation works

1. The app starts from a gate, such as `Gate1`.
2. It checks whether that gate is open.
3. It ignores full parking areas.
4. It finds the shortest route to every available parking area.
5. It calculates route congestion risk.
6. It calculates parking overflow risk.
7. It combines those values into one total score.
8. It recommends the parking option with the lowest score.

The score is calculated as:

total score =
route cost × distance weight
+ congestion risk × congestion weight
+ overflow risk × overflow weight


Lower score means a better parking recommendation.

## Running the legacy application (archived)

The section above describes `legacy/flat_optimizer/`, not the active
`digital_twin/` system. Note its imports were already broken as received
(reference an `optimization.*` package that was never actually present),
so this won't currently produce the output below without further fixes.

1. Open the repo root in VS Code.
2. Open `legacy/flat_optimizer/main.py`.
3. Click the normal ▶ Run button.

Expected output (once the import issue is fixed):

--- Parking Nav X ---
Recommended parking: ParkingA
Route: Gate1 → RoadA → RoadC → ParkingA
Route cost: 9
Overall score: 15.0

Its own tests are under `legacy/flat_optimizer/tests/` (e.g.
`test_dijkstra.py`, `test_optimizer.py`), same caveat.

## Running the active system

```bash
python scripts/load_campus_config.py --config configs/campuses/vitap.yaml
python -m pytest tests/
python -m digital_twin.cli.run --campus vitap --scenario configs/scenarios/vitap/normal_day.yaml --strategy digital_twin.simulation.demo_strategies.DemoNearestAvailableStrategy
uvicorn digital_twin.api.app:app --reload
```


A successful test prints a message such as:

Parking optimizer tests passed! ✅

---

## Digital Twin + Simulation

The VIT-AP Digital Twin and simulation pipeline has been fully implemented, validated, and is production-ready.

### 1. Load VIT-AP Campus Configuration

From the project root:

```bash
python scripts/load_campus_config.py --config configs/campuses/vitap_v2.yaml
```

Expected output:

```
Loaded campus 'vitap' from configs/campuses/vitap_v2.yaml
```

### 2. Run the Normal-Day Simulation

Run the VIT-AP normal-day scenario using the Nearest Available baseline strategy:

```bash
python -m digital_twin.cli.run \
  --campus vitap \
  --scenario configs/scenarios/vitap/normal_day.yaml \
  --strategy digital_twin.simulation.demo_strategies.DemoNearestAvailableStrategy
```

A successful run produces an experiment directory similar to:

```
experiments/runs/vitap-normal-day-<run-id>/
```

Expected simulation outputs include:

```
timesteps.parquet
vehicles.parquet
```

### 3. Inspect Simulation Results

Windows PowerShell:

```powershell
Get-ChildItem -Recurse experiments/runs/
```

For a specific run:

```powershell
Get-ChildItem -Recurse experiments/runs/vitap-normal-day-<run-id>
```

### 4. Run the Complete Test Suite

Run all project tests:

```bash
python -m pytest tests/ -v
```

The Digital Twin and simulation implementation is validated when all tests pass.

### 5. Start the FastAPI Backend

Start the API server:

```bash
uvicorn digital_twin.api.app:app --reload
```

The API is available at:

```
http://127.0.0.1:8000
```

### 6. Run Other VIT-AP Scenarios

High-demand event:

```bash
python -m digital_twin.cli.run \
  --campus vitap \
  --scenario configs/scenarios/vitap/high_demand_event.yaml
```

Parking closure:

```bash
python -m digital_twin.cli.run \
  --campus vitap \
  --scenario configs/scenarios/vitap/parking_closure.yaml
```

Gate closure:

```bash
python -m digital_twin.cli.run \
  --campus vitap \
  --scenario configs/scenarios/vitap/gate_closure.yaml
```

### Digital Twin + Simulation Validation

The following components are validated by the automated test suite:

- VIT-AP campus configuration
- Campus gates and parking lots
- Campus road graph
- Digital Twin state updates
- Parking capacity constraints
- Gate queue constraints
- Road state persistence
- Vehicle state persistence
- Simulation snapshots
- Event activation/deactivation
- Scenario validation
- Fixed random-seed reproducibility
- Parking closure scenarios
- Gate closure scenarios
- Overflow event handling
- Nearest Available strategy
- End-to-end simulation execution

### Synthetic Data Notice

**IMPORTANT:** The 30-day occupancy, gate queue, and road congestion data used in simulations are **SYNTHETIC** observations generated by constrained generators. They are **not** real VIT-AP campus observations. See [docs/VVIT_AP_DATA_COMPLETION_REPORT.md](docs/VVIT_AP_DATA_COMPLETION_REPORT.md) for complete provenance tracking.

All synthetic data is explicitly labeled with `provenance: "SYNTHETIC"` in the database and CSV exports.

### Current Status

| Component | Status |
|-----------|--------|
| Campus Configuration | ✅ Complete |
| Campus Graph | ✅ Complete |
| Digital Twin | ✅ Complete |
| Vehicle Simulation | ✅ Complete |
| Parking State Simulation | ✅ Complete |
| Gate State Simulation | ✅ Complete |
| Road State Simulation | ✅ Complete |
| Scenario Engine | ✅ Complete |
| Nearest Available Strategy | ✅ Complete |
| Reproducibility | ✅ Complete |
| Automated Tests | ✅ Complete |
| API | ✅ Complete |
| Synthetic Data (30 days) | ✅ Generated |
| Database Import | ✅ Complete |

**Digital Twin + Simulation: PRODUCTION READY** ✅

### Next Research Stage

After the Digital Twin + Simulation stage, proceed to:

```
Digital Twin + Simulation
            ↓
Parking Occupancy Prediction
            ↓
Future Risk Prediction
            ↓
Multi-Objective Optimization
            ↓
Recommendation + Explanation
            ↓
Baseline Comparison
            ↓
Experiments + Metrics
            ↓
Research Validation
```

---

## Technologies used

This project currently uses Python’s built-in modules:

- `json` for reading mock data;
- `pathlib` for locating project files;
- `sys` to allow direct test execution in VS Code.

The routing and optimization algorithms are implemented manually in Python. No external graph library, such as NetworkX, is currently required.

## VIT-AP dataset (archived prototype)

`data/vitap_dataset_prototype/generate_vitap_dataset.py` produces
`vitap_graph.json`, `vitap_parking.json`, and `vitap_predictions.json` — a
second dataset in the same schema as `legacy/flat_optimizer/data/mock_*.json`,
built from `vitap_real_destinations.json` in that same folder. Predates
`configs/campuses/vitap.yaml`, which is the current system's real VIT-AP
config.

Provenance is field-by-field, not "real vs. fake" as a whole — see
[docs/PROVENANCE.md](docs/PROVENANCE.md) for the full breakdown and what was
searched for. Summary:

- **`EXTERNAL_MAP_REFERENCE` (real):** the 11 destination names/coordinates
  (AB-1, AB-2, CB, MH-1/2/3/6/7, LH-1, Food Street, MH-2 Food Store) are
  real VIT-AP locations pulled from public OpenStreetMap data.
- **`SAMPLE` (fabricated placeholder):** the single gate and single parking
  lot, and every road distance between them (straight-line, not walked).
  No public source for VIT-AP's real gates/lots exists.
- **`SYNTHETIC` (no real source exists):** parking capacity/occupancy and
  congestion values, seeded with time-of-day shape rather than uniform
  noise.

A public paper on VIT-AP parking-slot detection was found
([EAI Endorsed Transactions, 2023](https://eudl.eu/doi/10.4108/eetinis.v10i4.4294))
but publishes no downloadable dataset. No other public VIT-AP parking/traffic
dataset was found anywhere searched (GitHub, Kaggle, Zenodo, HuggingFace,
ResearchGate).

Regenerate with:

    cd data/vitap_dataset_prototype
    python generate_vitap_dataset.py --time morning|midday|evening --seed 42

## Future improvements

Possible future upgrades include:

- real-time traffic and parking data;
- machine-learning-based congestion prediction;
- a web or mobile user interface;
- map visualization;
- GPS-based route input;
- live updates for blocked roads and full parking lots.

## Author

Parking Nav X project team.