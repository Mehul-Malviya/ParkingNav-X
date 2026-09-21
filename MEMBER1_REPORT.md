# Member 1 report — Campus Config / Graph / Digital Twin / Simulation

## 1. What was implemented

The full chain: Campus Configuration → Campus Graph → Digital Twin →
Simulation → Scenarios, as a configuration-driven, multi-campus Python
package (`campus_twin/`). No VIT-AP topology is hard-coded in any business
logic — VIT-AP is one JSON config among any number of others.

- **Module 1 (Config + Graph):** `campus_twin/config.py` — dataclasses for
  Campus/Gate/Road/ParkingLot/Destination, all carrying `provenance` and
  `verification_state`; JSON loader; structural validation (duplicate IDs,
  orphan nodes, invalid references, `usable_capacity > capacity`,
  `EXTERNAL_MAP_REFERENCE` rejected for parking lots). `campus_twin/graph.py`
  builds one deterministic drive/walk adjacency graph from the config and
  excludes closed roads/gates/lots from it (not just flags them), plus graph-
  level validation (reachability, gate-to-lot connectivity).
- **Module 2 (Scenarios):** `campus_twin/scenarios.py` — the 7 required
  starter scenario builders (NORMAL_DAY, HIGH_DEMAND, EVENT,
  PARKING_CLOSURE, GATE_CLOSURE, ROAD_CLOSURE, MULTIPLE_DISRUPTION), each
  `provenance=SYNTHETIC`.
- **Module 3 (Digital Twin):** `campus_twin/digital_twin.py` — `ParkingState`/
  `GateState`/`RoadState`/`VehicleState`/`EventState`, the 11-state vehicle
  lifecycle with transition validation, and `DigitalTwin` with
  initialize/update-per-entity/validate/snapshot/reset/restore/history/
  state-at-timestamp. Rejects negative occupancy/queue and
  occupied > usable_capacity outright — never clamps.
- **Module 6 (Simulation Engine):** `campus_twin/simulation.py` — deterministic
  discrete 1-minute-tick engine: vehicle arrival generation (seeded, uniform
  or peaked), gate queueing/throughput, routing via the one shared campus
  graph (never a second graph), parking search/assignment through a
  pluggable strategy, dwell, departure, road-load/congestion tracking, and
  periodic Digital Twin snapshots. All output is `provenance=SYNTHETIC`,
  `result_type=SIMULATION`.
- **Module 22 (Strategy interface):** `campus_twin/strategies.py` —
  `ParkingAssignmentStrategy` ABC with `FirstAvailable`, `NearestAvailable`,
  `FixedPreference`, `RandomFeasible`, reusing the existing repo's
  `dijkstra.py` and `parking_constraints.py` directly rather than
  duplicating that logic.

## 2. Files created

```
campus_twin/__init__.py
campus_twin/config.py
campus_twin/graph.py
campus_twin/digital_twin.py
campus_twin/scenarios.py
campus_twin/strategies.py
campus_twin/simulation.py
data/campus_configs/vitap.json
data/campus_configs/sample.json
campus_twin_demo.py
test_campus_config.py
test_campus_graph.py
test_digital_twin.py
test_simulation.py
MEMBER1_REPORT.md
```

## 3. Files modified

None. Nothing in the existing flat module set (`dijkstra.py`,
`parking_constraints.py`, `gate_constraints.py`, `road_constraints.py`, the
optimizer/recommendation/risk files, or their tests) was changed.

## 4. Database tables/migrations added

**None.** This repo has no database or web framework (no `requirements.txt`,
no ORM, no migrations directory) — adding one would be new infrastructure
nothing else in the repo uses, not "implementing my part" of the existing
project. The entities the spec describes as DB tables are implemented as
Python dataclasses with the same fields instead. If the team later adds a
real backend (e.g. the FastAPI structure already present in
`Jyothireddy-pula/Parking_nav_`), these dataclasses map directly to tables/
Pydantic models with minimal translation.

## 5. APIs added

**None**, for the same reason — no web framework exists in this repo.
`campus_twin`'s public functions/classes (`load_campus_config`,
`build_campus_graph`, `DigitalTwin`, `SimulationEngine`, scenario builders)
are the "clean interfaces" in lieu of REST routes.

## 6. Services added

`campus_twin.config`, `campus_twin.graph`, `campus_twin.digital_twin`,
`campus_twin.simulation`, `campus_twin.scenarios`, `campus_twin.strategies` —
see file list above.

## 7. Graph functionality added

Deterministic drive/walk adjacency construction from config; closed-entity
exclusion; reachability validation; shortest-route lookup via the existing
`dijkstra.py` (reused, not duplicated).

## 8. Digital Twin functionality added

Full state engine per section 17 of the spec: initialize, get current
state, per-entity update (parking/gate/road/vehicle/event) with validation,
`validate_state`, `snapshot_now`, `reset_state`, `restore_snapshot`,
`get_history`, `get_state_at_timestamp`.

## 9. Simulation functionality added

Vehicle arrival generation (seeded), gate queue + throughput, graph-based
routing that respects closures, parking search/assignment via pluggable
strategy, dwell/departure/release, road load + congestion-level tracking,
periodic snapshots, structured metrics.

## 10. Scenario functionality added

7 starter scenario builders with configurable demand multiplier, closures,
seed, and duration.

## 11. Tests added

30 tests across 4 files (`test_campus_config.py`, `test_campus_graph.py`,
`test_digital_twin.py`, `test_simulation.py`), covering config validation,
graph validation/determinism/closures, digital twin state rules and
snapshot/restore, and simulation reproducibility, all 7 scenario types
(including the section-52 end-to-end integration test), and multi-campus
isolation.

## 12. Test results

```
30 passed in 0.14s
```

The pre-existing 10 test files (`test_dijkstra.py` etc.) still fail to
collect — **this predates this work**: their imports reference an
`optimization.*` package that doesn't exist in this flat repo checkout
(flagged in an earlier session, unrelated to Member 1).

## 13. How to run

```bash
python campus_twin_demo.py
```

## 14. How to test

```bash
python -m pytest test_campus_config.py test_campus_graph.py test_digital_twin.py test_simulation.py -v
```

## 15. What is currently using mock/synthetic data

Everything dynamic: vehicle arrivals, dwell times, gate throughput, parking
occupancy changes, road load/congestion — all `provenance=SYNTHETIC`,
generated by `SimulationEngine`, seeded and reproducible. The VIT-AP campus
config's destination names/coordinates are real (`EXTERNAL_MAP_REFERENCE`,
from OpenStreetMap — see `PROVENANCE.md`); its single gate, single parking
lot, and every road are fabricated `SAMPLE` placeholders.

## 16. What is waiting for real VIT-AP data

A physical GPS survey of VIT-AP's actual gates, parking lot perimeters/
capacities, and road geometry (per `PROVENANCE.md`) — nothing here can
become `REAL` without it. Module 6A's calibration interface exists
conceptually (simulation parameters are already isolated per-scenario) but
no calibration has been performed, and none is claimed.

## 17. Known limitations

- Single gate / single parking lot in the real VIT-AP config means the
  parking-assignment strategies have nothing to choose between there — they
  're exercised meaningfully in `sample.json` instead (2 lots) and are ready
  to matter for VIT-AP once a second real lot exists.
- Road load is "vehicles currently transiting an edge," recomputed each
  tick — a transparent, deliberately simple model per spec section 26, not
  a traffic simulator.
- Gate exit does not queue (vehicles exit as soon as their return route
  completes) — the spec allows this as optional ("queue simulation... where
  applicable").
- Building/BuildingEntrance are not separate entities; `Destination` carries
  `entrance_id`/`pedestrian_access_point` directly to cover the same need
  with less structure, matching this repo's scale.

## 18. What is NOT implemented

Database layer, REST API layer, frontend, real-data ingestion pipeline
(Module 5 — explicitly owned by another member), ML prediction/risk/
optimization/explainability logic (explicitly out of Member 1's scope per
spec section 61), calibration execution (no real data exists yet to
calibrate from).

## 19–26. How Member 1 connects to other modules

- **Member 2 (data pipeline):** real observations would flow through a
  validation step into `DigitalTwin.update_parking_state` /
  `update_gate_state` / `update_road_state` — the same methods simulation
  uses, distinguished only by `provenance=REAL` vs `SYNTHETIC`.
- **Member 3 / Navigation:** consumes `CampusGraph` directly
  (`campus_twin.graph.build_campus_graph`) — the same graph object
  simulation routes on, so product navigation and research simulation can
  never diverge.
- **Prediction:** consumes `DigitalTwin.get_history()` /
  `get_state_at_timestamp()` for time-series state — read-only, never
  writes to campus configuration.
- **Risk:** consumes `DigitalTwin.get_current_state()` plus Prediction's
  output; Member 1 exposes state, not risk logic.
- **Optimization:** consumes `CampusConfig` (capacity/status/access
  constraints) and `DigitalTwin` current/predicted state; the optimizer
  cannot select a closed/full lot or a closed road because
  `build_campus_graph` already excludes closed roads and `ParkingState`
  rejects over-capacity assignment.
- **Experiments:** run multiple `ParkingAssignmentStrategy` implementations
  through the same `SimulationEngine.run(config, graph, scenario)` call for
  fair comparison — `simulation_id`/`scenario_id`/`seed`/
  `configuration_version` are preserved in every `SimulationResult`.
- **Validation:** compares a `DigitalTwin` snapshot (real observations, once
  they exist) against a `SimulationResult` for the same scenario/
  configuration_version — never labeled "validated" here, since no
  comparison has actually been performed yet.
