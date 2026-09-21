# Member 1 — Digital Twin + Simulation subsystem report

Full build against the 6-part spec (Campus Config → Graph → Digital Twin →
Simulation → Parking/Queue state → Scenarios), config-driven and
multi-campus. This supersedes the earlier lighter `campus_twin/` prototype
for the same ownership area — that prototype had no DB/API because I'd
wrongly assumed this repo had no such infrastructure available; it does
(FastAPI, SQLite, networkx, pandas/pyarrow are all installed), so this
version implements the real thing instead.

## What was built, per part

**Part 1 — Campus Configuration** (`digital_twin/config_loader.py`,
`digital_twin/gps_survey_import.py`, `migrations/0001_initial.sql`):
7 SQLite tables scoped by `campus_id` (campuses, gates, roads,
parking_lots, destinations, events, routes_graph_edges). YAML config
loader is idempotent (upsert keyed by `(campus_id, entity_id)`) and
validates before writing anything: duplicate IDs, non-positive/malformed
capacities, out-of-range coordinates, a road with fewer than 3 geometry
points (2 endpoints alone can't represent a real path), unknown node
references, orphan nodes, and capacity breakdowns exceeding total
capacity. `gps_survey_to_config` converts a GPX+CSV survey into this YAML
format, preserving track point order exactly (never straightened/
reordered). Sample fixtures at `tests_fixtures/`.

**Part 2 — Campus Graph** (`digital_twin/graph_service.py`): builds a
`networkx.Graph` per `campus_id`, cached until `refresh_graph`.
Deliberately has **no pathfinding** — only structure, `get_neighbors`/
`get_node`/`get_edge`/`is_connected`/`get_graph_bounds`, and a documented
JSON/GeoJSON export for Navigation to build its own routing on top of.

**Part 3 — Digital Twin State** (`digital_twin/twin_service.py`): the
live, continuously-updating state of parking lots, gates, roads, and
vehicles — 4 state tables + `campus_state_snapshot` for history.
`update_parking_state`/`update_gate_state`/`update_road_state` validate
before writing and reject (never clamp) over-capacity or negative values;
missing `source`/`provenance` is rejected. `freshness_state`
(FRESH/AGING/STALE/UNKNOWN) is computed on read from
`now() - observation_timestamp`, never stored statically.

**Part 4 — Simulation Engine** (`digital_twin/simulation/engine.py`,
`strategy.py`): deterministic discrete 1-minute-tick engine driven by one
seeded `random.Random` instance (no unseeded randomness anywhere).
Contains **no allocation decision logic** — it calls the injected
`AllocationStrategy.assign()` exactly once per vehicle at the
parking_search step, then independently enforces closed/full lots,
closed/blocked roads, and gate throughput regardless of what the strategy
returned. `FixedLotStrategy` exists only to prove the interface is
actually invoked, not bypassed (tested).

**Part 5 — Parking/Queue refinements**: occupancy increments on
assignment, decrements on departure with the spec's one intentional clamp
(floor at zero, logged as an internal consistency guard — never applied
anywhere else). Gate queues are FIFO, bounded by configured throughput.
Overflow events are recorded as one boolean flag per `(lot, timestep)` in
the timestep metrics — never double-counted per failed vehicle.

**Part 6 — Scenario Generation** (`digital_twin/simulation/scenario.py`):
YAML scenarios under `configs/scenarios/{campus_id}/`. 4 starter scenarios
(normal_day, high_demand_event, parking_closure, gate_closure), all
SYNTHETIC. Validator rejects unknown gate/lot/road references, a missing
`random_seed` (never defaulted), and cross-campus references. CLI:
`python -m digital_twin.cli.validate_scenario --config <path>`.

**API** (`digital_twin/api/app.py`, FastAPI): all endpoints from Parts 1–3
of the spec — read-only campus facts, graph export/bounds/refresh, twin
state read + the two ingestion-facing POST endpoints Member 2 writes real
observations through (same validated `update_*` methods the simulator
uses, distinguished only by `source`/`provenance`).

**CLI runner** (`digital_twin/cli/run.py`): `python -m digital_twin.cli.run
--campus <id> --scenario <path> --strategy <module.ClassName> [--seed N]`.
Writes `experiments/runs/{run_id}/vehicles.parquet` and
`timesteps.parquet`, and a `simulation_runs` DB row.

## Files created

```
migrations/0001_initial.sql
digital_twin/__init__.py
digital_twin/db.py
digital_twin/models.py
digital_twin/config_loader.py
digital_twin/gps_survey_import.py
digital_twin/graph_service.py
digital_twin/twin_service.py
digital_twin/simulation/__init__.py
digital_twin/simulation/scenario.py
digital_twin/simulation/strategy.py
digital_twin/simulation/engine.py
digital_twin/api/__init__.py
digital_twin/api/app.py
digital_twin/cli/__init__.py
digital_twin/cli/validate_scenario.py
digital_twin/cli/run.py
configs/campuses/sample.yaml
configs/campuses/vitap.yaml
configs/scenarios/sample/normal_day.yaml
configs/scenarios/sample/high_demand_event.yaml
configs/scenarios/sample/parking_closure.yaml
configs/scenarios/sample/gate_closure.yaml
tests_fixtures/sample_survey.gpx
tests_fixtures/sample_waypoints.csv
test_part1_campus_config.py
test_part2_campus_graph.py
test_part3_digital_twin.py
test_part4_part5_simulation.py
test_part6_scenarios.py
test_api.py
MEMBER1_SUBSYSTEM_REPORT.md
```

## Files modified

None. The existing flat module set and its (pre-existing, already-broken)
tests were not touched.

## Database tables / migrations added

`migrations/0001_initial.sql`: campuses, gates, roads, parking_lots,
destinations, events, routes_graph_edges, parking_lot_state, gate_state,
road_state, vehicle_state, campus_state_snapshot, simulation_runs,
schema_migrations. Applied via SQLite (`digital_twin/db.py`) — no external
DB server required, so nobody on the team is blocked by infra setup.

## APIs added

```
GET  /api/v1/campuses/{campus_id}
GET  /api/v1/campuses/{campus_id}/gates
GET  /api/v1/campuses/{campus_id}/roads
GET  /api/v1/campuses/{campus_id}/parking-lots
GET  /api/v1/campuses/{campus_id}/destinations
GET  /api/v1/campuses/{campus_id}/events
GET  /api/v1/campuses/{campus_id}/graph
GET  /api/v1/campuses/{campus_id}/graph/bounds
POST /api/v1/campuses/{campus_id}/graph/refresh
GET  /api/v1/campuses/{campus_id}/state
GET  /api/v1/campuses/{campus_id}/state/parking/{lot_id}
GET  /api/v1/campuses/{campus_id}/state/history
POST /api/v1/campuses/{campus_id}/state/parking/{lot_id}   -- Member 2 ingestion contract
POST /api/v1/campuses/{campus_id}/state/gates/{gate_id}    -- Member 2 ingestion contract
```

## Services added

`CampusGraphService`, `DigitalTwinService`, `SimulationEngine`,
`ScenarioLoader`/`ScenarioValidator`, `AllocationStrategy` interface.

## Graph functionality added

Per-campus `networkx.Graph` construction from DB rows, cached + refreshable,
isolation between campuses verified by test, structural reachability
(`is_connected`) without any pathfinding.

## Digital Twin functionality added

Full state engine: initialize/update-per-entity (validated)/current
state/history/snapshot, freshness computed on read with a mockable clock
for testing.

## Simulation functionality added

Seeded deterministic vehicle lifecycle (arrival → gate_queue →
campus_entry → route → parking_search → parking_assignment → parked →
departure → completed), gate throughput/FIFO queueing, parking occupancy
with the one documented clamp, overflow event tracking, road load per
timestep, Parquet run output, `simulation_runs` DB row.

## Scenario functionality added

4 starter YAML scenarios + loader/validator + CLI.

## Tests added

54 tests across 6 files (`test_part1_campus_config.py` through
`test_part6_scenarios.py`, plus `test_api.py`), covering every explicitly
required test case in the spec: idempotent reload, every Part 1 validation
rule, GPX point-order preservation, campus isolation, graph refresh/
reachability, freshness transitions with a mocked clock, over-capacity
rejection without clamping, snapshot/history reconstruction, seed
reproducibility (byte-identical metrics), closed-gate/closed-lot exclusion,
non-negative queues/occupancy, the "always assign to lot X" strategy-not-
bypassed test, overflow de-duplication, every starter scenario validating,
and cross-campus reference rejection.

## Test results

```
54 passed in 6.49s
```

## How to run

```bash
# Load a campus config
python -c "from digital_twin.db import get_connection, apply_migrations; from digital_twin.config_loader import load_campus_config; c = get_connection(); apply_migrations(c); load_campus_config('configs/campuses/vitap.yaml', c)"

# Validate a scenario
python -m digital_twin.cli.validate_scenario --config configs/scenarios/sample/normal_day.yaml

# Run a simulation
python -m digital_twin.cli.run --campus sample --scenario configs/scenarios/sample/normal_day.yaml --strategy digital_twin.simulation.strategy.FixedLotStrategy

# Start the API
uvicorn digital_twin.api.app:app --reload
```

## How to test

```bash
python -m pytest test_part1_campus_config.py test_part2_campus_graph.py test_part3_digital_twin.py test_part4_part5_simulation.py test_part6_scenarios.py test_api.py -v
```

## What is currently using mock/synthetic data

Everything dynamic: all scenario-generated vehicle arrivals, dwell times,
gate throughput, occupancy, road load — all `provenance=SYNTHETIC`,
`source=simulation`. The VIT-AP campus config's 11 destination names/
coordinates are real (from public OpenStreetMap); its gate, parking lot,
and every road distance are fabricated placeholders pending a physical
GPS survey (see the existing `PROVENANCE.md`).

## What is waiting for real VIT-AP data

A physical GPS survey (the `gps_survey_to_config` importer is ready for
it) for VIT-AP's actual gates, lot capacities, and road geometry. Real
observations would flow into the exact same `update_parking_state`/
`update_gate_state` methods the simulator uses, via the two POST endpoints,
with `provenance=REAL` instead of `SYNTHETIC` — no architecture change
needed when that data arrives.

## Known limitations

- `road_load` is attributed to a vehicle's route once, at the tick its
  transit begins, rather than re-added every tick of a multi-minute
  transit — documented in `engine.py`'s docstring, a deliberately simple
  and replaceable model.
- Gate exit doesn't queue (vehicles complete as soon as their return
  transit finishes) — the spec allows this ("queue simulation...where
  applicable").
- `prediction_error_injection_level` is accepted and stored per the spec
  ("your job is only to accept and pass this parameter through") but not
  applied by anything in this module, since using it is explicitly
  Member 3's robustness-testing responsibility.
- The API's DB dependency defaults to a single SQLite file
  (`digital_twin.db`) rather than a connection pool — fine at this scale;
  swapping to Postgres later only touches `digital_twin/db.py`.

## What is NOT implemented

Any allocation strategy beyond the trivial test-only `FixedLotStrategy`
(First Available, Nearest Available, the final optimizer are explicitly
Member 3's), pathfinding/turn-by-turn navigation (explicitly Navigation's,
built on top of Part 2's graph export), prediction/risk/explainability,
frontend/UI, real-data collection tooling (Member 2 writes through the
ingestion API this module exposes, but doesn't build the collection
tooling itself).

## Integration contract — how this connects to the rest of the team

- **Navigation (Member 3/4):** consumes `GET /graph` (documented
  `{nodes, edges}` shape) and Part 1's read-only campus-facts endpoints.
  Builds its own pathfinding on top; never writes to these tables.
- **Data Collection / CV (Member 2):** writes real observations through
  `POST /state/parking/{lot_id}` and `POST /state/gates/{gate_id}`, which
  require `source` + `provenance` and reject anything missing them or
  violating capacity — the same validated path the simulator itself uses.
- **Prediction/Risk/Optimization/Explainability (Member 3):** reads
  `GET /state` and `GET /state/history` for current + historical Digital
  Twin state, and the simulation's `vehicles.parquet`/`timesteps.parquet`
  output for experiment analysis. Implements `AllocationStrategy` against
  `digital_twin/simulation/strategy.py`'s exact interface to plug into the
  engine.
- **Frontend (Member 4):** reads `GET /state` and Part 1's facts endpoints
  for display; never writes.
- **Experiments (Member 3):** the scenario YAML schema
  (`configs/scenarios/{campus_id}/*.yaml`) is what experiments are
  designed against; `SimulationRunner.run()` accepts any
  `AllocationStrategy` and produces the same reproducibility metadata
  (`run_id`, `scenario_id`, `random_seed`, `configuration_version`) for
  fair comparison across strategies.
