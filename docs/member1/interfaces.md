# Interfaces to Teammates — Member 1

**Owner:** Jyothi Reddy Pula (23BCE7882) · VIT-AP · ParkingNav-X

---

## → Member 2 (Data + ML)

**What I provide:** ML training dataset as CSV, one row per (timestamp, lot) at 5-min resolution.

**How to generate:**
```python
from digital_twin.api_functions import make_dataset
make_dataset(
    campus_id="vitap",
    scenario_paths=["configs/scenarios/vitap/normal_day.yaml",
                    "configs/scenarios/vitap/E2_event_placement.yaml"],
    seeds=list(range(30)),
    output_path="data/ml_dataset.csv"
)
```

**Columns:** `scenario_id, seed, arrival_time, assigned_lot_id, search_time_min, wait_time_min, final_state, complied, travel_distance_m`

**Guarantee:** features use only past/current values — no future leakage.

---

## → Member 3 (Optimization)

**What I provide:** `StateSnapshot` JSON + `twin.fork()` for look-ahead.

**How to get current state:**
```python
from digital_twin.api_functions import get_state
state = get_state(run_id, tick)
# Returns: {sim_time, lots, gates, roads, pending_arrivals_by_gate,
#           active_events, active_disruptions}
```

**Fork for what-if:**
```python
from digital_twin.simulation.state_snapshot import StateSnapshot
fork = snapshot.fork()  # deep independent copy — safe to mutate
```

**Strategy interface** (`digital_twin/simulation/strategy.py`):
```python
class AllocationStrategy(Protocol):
    def assign(self, vehicle, state) -> AssignmentResult: ...
    def update_policy(self, state, forecast) -> None: ...
```

---

## → Member 4 (Platform + Validation)

**What I provide:** pure Python functions for the FastAPI layer.

```python
from digital_twin.api_functions import (
    load_campus,        # load_campus("vitap") -> campus dict
    get_state,          # get_state(run_id, tick) -> StateSnapshot dict
    run_simulation,     # run_simulation(scenario, strategy, seed) -> run_id
    run_batch,          # run_batch(scenario, strategies, seeds) -> [run_id]
    get_metrics,        # get_metrics(run_id) -> metrics dict
    get_timeline,       # get_timeline(run_id) -> [{tick, ...}]
    export_geojson,     # export_geojson("vitap") -> GeoJSON FeatureCollection
)
```

**Run artifacts** at: `runs/{scenario_id}/{strategy}/seed_{n}/`
- `vehicles.parquet` — per-vehicle records
- `metrics.json` — summary metrics
- `manifest.json` — config hash, seed, git commit, timestamps
