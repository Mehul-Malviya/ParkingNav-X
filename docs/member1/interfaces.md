# Team Interfaces — Contracts with Members 2, 3, 4
**Author:** Jyothi Reddy Pula | **Date:** 5 October 2026  
**Status:** READY FOR SIGN-OFF

---

## INTERFACE 1: MEMBER 2 (ML/Prediction)

### **Input: What I Provide**

**ML Training Dataset Generator**
```python
# Command line
python -m simulation.cli make-dataset \
  --scenarios E1,E2,peak_hour,E3_lot_closure,E4_gate_closure,E5_noise_0 \
  --seeds 0-29 \
  --output data/ml_training_set.csv

# Output: CSV file, 5-min resolution
```

**CSV Schema (20 columns, leak-free):**
```
timestamp                    # datetime (2026-10-01 08:00:00)
scenario_id                  # str (E1, E2, etc.)
seed                         # int (0-29)
lot_id                       # str (vitap-lot-academic-main)
gate_id                      # str (vitap-gate-main)
minute_of_day                # int (480-1200 for 8 AM - 8 PM)
day_of_week                  # int (0-6, 0=Monday)
occupied                     # int (current vehicles in lot)
capacity                     # int (max spaces)
occupancy_ratio              # float [0, 1]
inflow_5m                    # int (vehicles entered in last 5 min)
outflow_5m                   # int (vehicles exited in last 5 min)
gate_arrivals_5m             # int (vehicles at gate in last 5 min)
gate_queue                   # int (vehicles waiting at gate)
avg_wait_min                 # float (average wait time)
road_congestion_avg          # float [0, 1] (average congestion on roads)
event_type                   # str|null (placement, exam, fest, sports)
event_intensity              # float [0, 2] (0=no event, 2=peak)
minutes_to_event_start       # int|null (-30 to +120)
is_disruption                # bool (road/gate/lot closed)
target_occ_t15               # float [0, 1] (occupancy at t+15 min) ← TARGET
target_occ_t30               # float [0, 1] (occupancy at t+30 min) ← TARGET
```

**Data Leakage Protection:**
- ✅ Features use only past/current values (t, t-5, t-10, ...)
- ✅ Targets are shifted forward (t+15, t+30)
- ✅ No future events, no look-ahead
- ✅ No leakage: `occupancy_ratio ≤ 1.0` always

**Quality Guarantee:**
- 30 seeds, 9 scenarios = ~50,000 rows per lot
- Missing intervals: logged, not interpolated
- No hand-edited values; all regenerable from scenario + seed

### **Output: What I Expect**

**Occupancy Predictions (for Member 3)**
```python
# At each decision cycle (every 5 minutes):
forecast = {
    "timestamp": "2026-10-01T09:15:00Z",
    "lot_id": "vitap-lot-academic-main",
    "occ_t15": 0.72,                    # predicted occupancy at t+15
    "occ_t30": 0.68,                    # predicted occupancy at t+30
    "confidence_interval_low": 0.65,    # 95% CI lower bound
    "confidence_interval_high": 0.79,   # 95% CI upper bound
    "model_id": "member2_v3",           # version for auditability
}
```

**Used in:** Member 3's optimization, forecast noise injection (E5)

---

## INTERFACE 2: MEMBER 3 (Optimization)

### **Input: What I Provide**

**StateSnapshot (JSON)**
```python
def twin.snapshot() -> dict:
    return {
        "schema_version": "1.0",
        "timestamp": "2026-10-01T09:15:00Z",
        "sim_time_minutes": 135,
        
        "lots": [
            {
                "lot_id": "vitap-lot-academic-main",
                "capacity": 120,
                "occupied": 85,
                "available": 35,
                "reserved_free": 4,
                "status": "open",
                "inflow_5m": 3,
                "outflow_5m": 1,
                "occupancy_ratio": 0.708,
                "predicted_occ_t15": 0.72,
                "predicted_occ_t30": 0.68,
            },
            # ... other lots
        ],
        
        "gates": [
            {
                "gate_id": "vitap-gate-main",
                "service_rate": 6.0,
                "queue_len": 7,
                "throughput_last_5m": 28,
                "avg_wait_last_5m": 0.8,
                "status": "open",
            },
            # ... other gates
        ],
        
        "roads": [
            {
                "road_id": "R1",
                "length_m": 350,
                "current_flow": 12,
                "travel_time_min": 1.15,
                "congestion_ratio": 0.35,
                "status": "open",
            },
            # ... other roads
        ],
        
        "pending_arrivals_by_gate": {
            "vitap-gate-main": 15,
            "vitap-gate-visitor": 8,
        },
        
        "active_events": [
            {
                "event_id": "placement_2026oct1",
                "event_type": "placement",
                "demand_multiplier": 1.8,
                "affected_zones": ["academic"],
                "minutes_until_start": -15,  # event started 15 min ago
            }
        ],
        
        "active_disruptions": [],
        
        "travel_time_matrix_sec": {
            # travel_time_sec[gate][lot] = shortest path travel time
            "vitap-gate-main": {
                "vitap-lot-academic-main": 45,
                "vitap-lot-admin-visitor": 120,
                # ... all lot combos
            },
            # ... all gate combos
        },
        
        "walk_time_min": {
            "academic": {
                "vitap-lot-academic-main": 2.0,
                "vitap-lot-admin-visitor": 5.0,
            },
            # ... zone→lot walk times
        },
    }
```

**Fork for What-If Look-Ahead**
```python
# Member 3's usage:
current_snapshot = twin.snapshot()

# What if we close Gate 1?
fork1 = twin.fork()
fork1.apply({"type": "gate_closure", "gate_id": "vitap-gate-main", "start": "now", "duration_min": 30})
fork1.simulate_forward(duration_min=15, strategy=B2_baseline)
forecast1 = fork1.get_metrics()

# What if we route more to Lot B?
fork2 = twin.fork()
fork2.apply({"type": "allocation_override", "lot_id": "vitap-lot-admin-visitor", "capacity_boost": 20})
fork2.simulate_forward(duration_min=15, strategy=B3_optimized)
forecast2 = fork2.get_metrics()

# Choose based on outcomes
if forecast1.overflow < forecast2.overflow:
    recommend(close_gate=False)
else:
    recommend(dynamic_pricing_lot_b=True)
```

### **Output: What I Expect**

**Decision Interface (Member 3 implements)**
```python
from typing import Protocol

class Strategy(Protocol):
    name: str
    
    def decide(self, 
               state: StateSnapshot, 
               forecast: dict[str, Any] | None
              ) -> Decision:
        """
        state: CurrentStateSnapshot (see above)
        forecast: Member 2's predictions (occupancy_t15, t30, CI, model_id)
                  OR None if unavailable (fallback to B2)
        
        Returns: Decision with:
          - vehicle_assignments: {vehicle_id: lot_id}
          - gate_guidance: {gate_id: routing_rule}
          - routes: {vehicle_id: [node_ids]}
          - explanation: {reason: str, confidence: float}
          - objective_value: float (or None)
        """
        pass
```

**Adapter Wraps It**
```python
# My adapter provides:
result = adapter.decide(state, forecast, timeout_ms=1000)
# If timeout or exception: falls back to B2 and logs

# I provide B1 (FirstAvailable) and B2 (NearestAvailable)
# You provide B3 (prediction-only) and P (full ParkingNav-X)
```

**Success Criteria:**
- ✅ Decision latency: mean < 100ms, p95 < 500ms, max < 1000ms
- ✅ Feasibility: 0 infeasible assignments (my guard checks)
- ✅ Reproducibility: same state + forecast → same decision

---

## INTERFACE 3: MEMBER 4 (Platform)

### **Input: What I Provide**

**Python API (Pure Functions)**
```python
from digital_twin.api_functions import (
    load_campus,
    run_simulation,
    get_state,
    get_metrics,
    get_timeline,
    export_campus_geojson,
)

# 1. Load campus once
campus = load_campus('configs/campuses/vitap.yaml')

# 2. Run simulation
run_id = run_simulation(
    scenario_path='configs/scenarios/vitap/E2_event_placement.yaml',
    strategy=FirstAvailableStrategy(),
    campus_id='vitap',
    seed=42,
    db_conn=conn,  # SQLite connection
)
# Returns: run_id (e.g., "E2-event-placement-a1b2c3d4")

# 3. Get state at specific time
state_t90 = get_state(run_id=run_id, timestamp_min=90)
# Returns: StateSnapshot dict at minute 90

# 4. Get metrics
metrics = get_metrics(run_id=run_id)
# Returns: {avg_search_time_min, avg_wait_time_min, overflow_events, ...}

# 5. Get full timeline for dashboard animation
timeline = get_timeline(run_id=run_id, resolution_min=5)
# Returns: list of StateSnapshots at 5-min intervals

# 6. Export campus for Leaflet map
geojson = export_campus_geojson(campus_id='vitap')
# Returns: GeoJSON with gates, lots, roads as FeatureCollections
```

**Output Format:**
- All responses are JSON-serializable dicts
- No database leakage (no SQL in responses)
- All numeric values are floats/ints (no numpy types)

### **Output: What I Expect**

**REST API (Member 4 builds)**
```
GET  /api/campus/{campus_id}               → Campus config
GET  /api/run/{run_id}                     → Run metadata + result
POST /api/simulation/run                   → Start new run (async)
GET  /api/simulation/{run_id}/state?t=90   → State at minute 90
GET  /api/simulation/{run_id}/metrics      → Final metrics
GET  /api/simulation/{run_id}/timeline     → Full timeline
GET  /api/campus/{campus_id}/geojson       → GeoJSON for map
```

**Success Criteria:**
- ✅ All endpoints return JSON
- ✅ Run can be retrieved after simulation completes
- ✅ Timeline animation works (smooth state transitions)
- ✅ Map shows campus graph with gates & lots

---

## SIGN-OFF CHECKLIST

### **Member 2 (ML):**
- [ ] ML dataset schema matches your ML pipeline
- [ ] 5-min resolution appropriate for your LSTM/model
- [ ] No data leakage (features from past only)
- [ ] You can fit occupancy predictions from this data

**Sign:** ___________________ **Date:** ___________

---

### **Member 3 (Optimization):**
- [ ] StateSnapshot provides all info you need for allocation
- [ ] Fork capability enables your what-if look-ahead
- [ ] Decision interface is clear (state, forecast) → assignments
- [ ] Adapter timeout (1000ms) works for your algorithm

**Sign:** ___________________ **Date:** ___________

---

### **Member 4 (Platform):**
- [ ] Python API is sufficient for your FastAPI wrapper
- [ ] GeoJSON format works with Leaflet
- [ ] Timeline resolution (5-min) works for dashboard animation
- [ ] JSON serialization is complete (no numpy types)

**Sign:** ___________________ **Date:** ___________

---

## VERSIONING

- **Schema version:** 1.0 (StateSnapshot, CSV, Decision)
- **Breaking changes:** Must bump major version
- **Backward compatibility:** Maintain for 2 weeks (grace period)

---

**Next Steps:**
1. Print this document
2. Get signatures from Members 2, 3, 4
3. Commit signed copy to repo
4. Reference in final report (Section 9)
