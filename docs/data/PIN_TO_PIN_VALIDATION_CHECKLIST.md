# PIN-TO-PIN CONNECTIVITY & VALUE VALIDATION CHECKLIST
## Quick Reference for Field-Level Integration Verification

**Purpose:** Verify every connection between data entities works correctly and values are realistic.

---

## SECTION 1: COORDINATE CONSISTENCY (THE BIGGEST PIN-TO-PIN ISSUE)

### 🔴 CRITICAL ISSUE: Gate & Lot Coordinates Are Identical

| Entity | Latitude | Longitude | Expected | Status |
|--------|----------|-----------|----------|--------|
| Gate (vitap-gate-placeholder) | 16.4911715 | 80.5018052 | Real gate location | ⚠️ PLACEHOLDER |
| Lot (vitap-lot-placeholder) | 16.4911715 | 80.5018052 | Real lot location | ⚠️ PLACEHOLDER |
| **Distance between them (road)** | — | — | 275m | ❌ **CONFLICT** |

**Pin-to-pin problem:**
```
IF gate.latitude == lot.latitude AND gate.longitude == lot.longitude
THEN road distance should be ≈ 0
BUT road distance configured as 275m
```

**Root cause:** Gate & lot are both placeholder coordinates (same point in space).

**Fix required:**
- [ ] Option A: Survey real gate coordinates, update gate config
- [ ] Option B: Survey real lot coordinates, update lot config  
- [ ] Option C: Keep placeholders but set road distance = 0
- **Choose ONE and document the decision**

---

## SECTION 2: DESTINATION-TO-PARKING CONNECTIVITY

### Schema Check: `destinations.nearest_parking_lot_ids`

| Destination | nearest_parking_lot_ids | Lot exists? | Distance (m) | Realism |
|-------------|---|---|---|---|
| AB-1 | ["vitap-lot-placeholder"] | ✅ Yes | 519 | ⚠️ Far (0.5km) |
| AB-2 | ["vitap-lot-placeholder"] | ✅ Yes | 638 | ⚠️ Far (0.6km) |
| CB | ["vitap-lot-placeholder"] | ✅ Yes | 452 | ⚠️ Far (0.4km) |
| Food Street | ["vitap-lot-placeholder"] | ✅ Yes | 464 | ⚠️ Far (0.5km) |
| MH-1 | ["vitap-lot-placeholder"] | ✅ Yes | 358 | ⚠️ Moderate (0.4km) |
| MH-2 | ["vitap-lot-placeholder"] | ✅ Yes | 269 | ✅ Close (0.3km) |
| MH-2 Food Store | ["vitap-lot-placeholder"] | ✅ Yes | 303 | ✅ Close (0.3km) |
| MH-3 | ["vitap-lot-placeholder"] | ✅ Yes | 115 | ✅ Very close (0.1km) |
| MH-6 | ["vitap-lot-placeholder"] | ✅ Yes | 238 | ✅ Close (0.2km) |
| MH-7 | ["vitap-lot-placeholder"] | ✅ Yes | 222 | ✅ Close (0.2km) |
| LH-1 | ["vitap-lot-placeholder"] | ✅ Yes | 556 | ⚠️ Far (0.5km) |

**Validation status:**
- ✅ All FK references valid (lot exists)
- ✅ Distances are reasonable (100m–600m range)
- ⚠️ But only **ONE lot** for all destinations — no choice for optimization
- **Action:** Add 3–5 more parking lots with real coordinates

---

## SECTION 3: DESTINATION-TO-GATE CONNECTIVITY

### Schema Check: `destinations.nearest_gate_ids`

| Destination | nearest_gate_ids | Gate exists? | Status |
|-------------|---|---|---|
| All 11 destinations | ["vitap-gate-placeholder"] | ✅ Yes | ✅ Valid FK |

**Assessment:**
- ✅ All FK references valid
- ⚠️ Only **ONE gate** — no backup entry point
- **Action:** Add 1–2 more gates (main, visitor, service)

---

## SECTION 4: ROUTE GRAPH EDGES (FROM_NODE → TO_NODE)

### All Edges Must Have Valid Node References

```
Edge: Gate → Lot
├─ from_node_id: vitap-gate-placeholder
│  └─ Should exist in: gates table ✅
└─ to_node_id: vitap-lot-placeholder
   └─ Should exist in: parking_lots table ✅

Edges: Lot → 11 Destinations
├─ from_node_id: vitap-lot-placeholder
│  └─ Should exist in: parking_lots table ✅
└─ to_node_id: vitap-osm-1485919486 (and 10 others)
   └─ Should exist in: destinations table ✅ (all 11 valid)
```

**Validation status:** ✅ All edges have valid endpoints

**Pin-to-pin problems:**
- ❌ **No reverse edges** — vehicles can't return!
  - Missing: vitap-lot-placeholder → vitap-gate-placeholder
  - Missing: vitap-osm-XXXXXX → vitap-lot-placeholder
  
**Action required:**
- [ ] Add reverse edge: Lot → Gate
- [ ] Add return edges: Each Destination → Lot
- [ ] Verify bidirectional is_driveable (not all are currently)

---

## SECTION 5: ROAD NETWORK TOPOLOGY

### Current Road Coverage (Star Model)

```
Gate → Lot (bidirectional)  [1 road]
Lot → 11 Destinations       [11 roads]

Total: 12 roads
Problem: No inter-destination roads!
```

**Missing connections that would make campus realistic:**

| Missing road | Distance (approx) | Importance |
|---|---|---|
| AB-1 ↔ AB-2 | 100–150m | 🔴 CRITICAL (nearby buildings) |
| MH-1 ↔ MH-2 | 100–120m | 🟡 HIGH (adjacent hostels) |
| MH-2 ↔ MH-3 | 100–150m | 🟡 HIGH (adjacent hostels) |
| Food Street ↔ MH-2 Food Store | 50m | 🟡 MEDIUM (cafeteria cluster) |
| AB-1 ↔ CB | 100–150m | 🟡 MEDIUM (academic area) |
| **Other campus roads** | Unknown | 🔴 CRITICAL (survey needed) |

**Action required:**
- [ ] Calculate inter-destination distances (Haversine or actual path)
- [ ] Add all realistic inter-destination roads to roads table & edges table
- [ ] Verify road directionality (driveable vs. walkable only)

---

## SECTION 6: CAPACITY CONSTRAINTS (Numeric Validation)

### Parking Lot Capacity Breakdown

```
Name:                      vitap-lot-placeholder
Total capacity:            50
├─ Usable capacity:        45     (=50 - reserved - restricted - temp_unavail)
├─ Reserved capacity:      0
├─ Restricted capacity:    0
└─ Temporarily unavailable: 0

Check: 45 == 50 - 0 - 0 - 0?  ✅ YES

Usable ratio: 45/50 = 90%  ✅ Reasonable
```

**Formula validation:**
```python
assert usable_capacity <= total_capacity
assert usable_capacity == total_capacity - reserved - restricted - temp_unavail
# Should be automatic, not manual!
```

**Current issue:** 🟡 Calculation is manual in YAML. Should be derived in code.

**Action required:**
- [ ] Verify parking_lots table constraints:
  ```sql
  CHECK (usable_capacity = total_capacity - reserved_capacity - restricted_capacity - temporarily_unavailable_capacity)
  ```

### Gate Capacity

```
Name:     vitap-gate-placeholder
Capacity: 30 vehicles in queue

Throughput check:
If service rate = 2 vehicles/min (typical university gate entry check time)
Then hourly throughput = 2 * 60 = 120 vehicles/hour
Peak capacity queue = 30 vehicles

Is this realistic? ⚠️ Unknown (needs survey)
```

**Action required:**
- [ ] Observe real VIT-AP gate: measure throughput rate
- [ ] Validate or adjust capacity value

---

## SECTION 7: TEMPORAL CONSTRAINTS (Time-Series Validation)

### Parking Lot State Integrity Checks

**Table:** `parking_lot_state`

```sql
-- Required constraints:
CHECK (occupied_spaces >= 0)
CHECK (occupied_spaces <= capacity)  -- FK to parking_lots.total_capacity
CHECK (available_spaces >= 0)
CHECK (available_spaces == capacity - occupied_spaces)
CHECK (occupancy_percentage >= 0 AND occupancy_percentage <= 1)
CHECK (occupancy_percentage == occupied_spaces / CAST(capacity AS REAL))
CHECK (observation_timestamp <= ingestion_timestamp)  -- Can't ingest before observing
```

**Current state:** ✅ Table exists, but **ZERO rows** (no data).

**Action required:**
- [ ] Generate synthetic occupancy data (1 month, 15-min intervals)
- [ ] Ensure all constraints are enforced
- [ ] Validate temporal continuity (no impossible jumps)

### Temporal Continuity Check (Example)

```
If at T=12:00 occupancy = 20 vehicles
And at T=12:15 occupancy = 50 vehicles
Then vehicles arrived = 30 (between 12:00 and 12:15)

Is 30 vehicles in 15 minutes realistic?
Parking rate = 30/(15 min) = 2 vehicles/min = 120 vehicles/hour
Is this realistic? ⚠️ Depends on time of day (maybe at morning peak)

But if this happens every 15 minutes for 8 hours, total arrivals = 1920 vehicles!
Is that realistic for a single 50-space lot? ❌ NO (capacity constraint violated)
```

**Action required:**
- [ ] Implement temporal continuity validator:
  ```python
  def validate_temporal_continuity(timeseries):
      for t in range(1, len(timeseries)):
          occupancy_delta = timeseries[t].occupied - timeseries[t-1].occupied
          arrivals = timeseries[t].arrivals
          departures = timeseries[t].departures
          assert occupancy_delta == arrivals - departures
  ```

---

## SECTION 8: TRAVEL TIME & DISTANCE CALIBRATION

### Travel Time Audit (All Roads)

| Road | Distance (m) | Time (s) | Implied speed (m/s) | Type | Reality |
|------|---|---|---|---|---|
| Gate → Lot | 275 | 212 | 1.30 | Vehicle | ❌ Too slow (walking speed) |
| Lot → AB-1 | 519 | 399 | 1.30 | Vehicle | ❌ Too slow |
| Lot → AB-2 | 638 | 491 | 1.30 | Vehicle | ❌ Too slow |
| Lot → CB | 452 | 348 | 1.30 | Vehicle | ❌ Too slow |
| Lot → Food St | 464 | 357 | 1.30 | Vehicle | ❌ Too slow |
| Lot → MH-1 | 358 | 275 | 1.30 | Vehicle | ❌ Too slow |
| Lot → MH-2 | 269 | 207 | 1.30 | Vehicle | ❌ Too slow |
| Lot → Food St | 303 | 233 | 1.30 | Vehicle | ❌ Too slow |
| Lot → MH-3 | 115 | 88 | 1.30 | Vehicle | ✅ OK for pedestrian |
| Lot → MH-6 | 238 | 183 | 1.30 | Vehicle | ❌ Too slow |
| Lot → MH-7 | 222 | 171 | 1.30 | Vehicle | ❌ Too slow |
| Lot → LH-1 | 556 | 428 | 1.30 | Vehicle | ❌ Too slow |

**Analysis:**
```
Current avg speed = 1.3 m/s = 4.7 km/h = 3 mph
Walking speed = 1.4 m/s (slightly slower than actual walking!)
Typical campus vehicle speed = 5–10 m/s = 18–36 km/h

Correction factor needed = 5–10 m/s / 1.3 m/s = 3.8–7.7×
Recommended: Multiply travel times by 4–5

Example corrected:
Lot → AB-1: 519m / (5 m/s) = 103.8 sec ≈ 104 sec
Current: 399 sec (too slow by 3.8×)
```

**Action required:**
- [ ] Audit all roads for speed assumptions
- [ ] Multiply vehicle travel times by 4–5
- [ ] Verify walking_vs_driveable flags (which is which?)
- [ ] Confirm speed assumptions match campus vehicle policy

---

## SECTION 9: MISSING NUMERIC DATA (Zeros Detected)

### Should Not Be Zero (But Are)

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| `parking_lot_state` row count | 1000s (1 month data) | **0** | 🔴 CRITICAL |
| `gate_state` row count | 1000s (1 month data) | **0** | 🔴 CRITICAL |
| `road_state` row count | 1000s (1 month data) | **0** | 🔴 CRITICAL |
| `vehicle_state` row count | Varies by scenario | **0** (until simulation runs) | ✅ OK |
| `events` row count | 20–50 (academic calendar) | **0** | 🟡 MEDIUM |
| Parking lot count | 3–5 (realistic minimum) | **1** (placeholder) | 🔴 CRITICAL |
| Gate count | 2–3 (main, visitor, service) | **1** (placeholder) | 🟡 HIGH |

**Action required for all:**
- [ ] Generate or import real/synthetic time-series data
- [ ] Populate events calendar
- [ ] Add more parking lots & gates

---

## SECTION 10: REFERENTIAL INTEGRITY CHECKS

### Foreign Key Validation Script

```python
def validate_referential_integrity(conn):
    checks = {
        "gates": {
            "campus_id": "campuses.campus_id"
        },
        "parking_lots": {
            "campus_id": "campuses.campus_id"
        },
        "destinations": {
            "campus_id": "campuses.campus_id"
        },
        "parking_lot_state": {
            "campus_id": "campuses.campus_id",
            "parking_lot_id": "parking_lots.parking_lot_id",  # Composite FK
        },
        "gate_state": {
            "campus_id": "campuses.campus_id",
            "gate_id": "gates.gate_id",  # Composite FK
        },
        "road_state": {
            "campus_id": "campuses.campus_id",
            "road_id": "roads.road_id",  # Composite FK
        },
        "routes_graph_edges": {
            "campus_id": "campuses.campus_id",
            # from_node_id, to_node_id could be any node type (gate, lot, destination, road)
            # Not enforced at DB level (flexible)
        }
    }
    
    for table, fks in checks.items():
        for column, target in fks.items():
            # Run referential integrity query
            orphaned = conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE {column} NOT IN (SELECT ...)
            """)
            if orphaned.fetchone()[0] > 0:
                print(f"🔴 ORPHANED: {table}.{column} has broken FKs")
            else:
                print(f"✅ OK: {table}.{column}")
```

**Status:** ✅ All current FKs valid (but see Section 3.4 about JSON arrays).

---

## SECTION 11: QUICK VALIDATION CHECKLIST

### Before Running Any Experiment, Verify:

- [ ] **Gate & Lot coordinates**
  - Are they different? OR documented why same?
  - Is road distance >= 0?

- [ ] **Destination coordinates**
  - All 11 within campus bounds? ✅
  - Any duplicates? ✅
  
- [ ] **Road network**
  - Fully connected? (Can route from Gate to every Destination?) ✅
  - Have reverse edges? (Can return to Gate?) ❌ **MISSING**
  - All distances ≥ 0? ✅

- [ ] **Travel times**
  - Match distance / typical speed? ❌ (walking speed, not vehicle)
  - Consistent across all roads? ✅ (all 1.3 m/s)

- [ ] **Capacity constraints**
  - occupied ≤ capacity? Not yet (no data)
  - available ≥ 0? Not yet (no data)
  - usable = total - reserved - restricted - temp_unavail? ⚠️ Manual

- [ ] **Foreign keys**
  - destinations.nearest_parking_lot_ids point to valid lots? ✅
  - destinations.nearest_gate_ids point to valid gates? ✅
  - routes_graph_edges point to valid nodes? ✅

- [ ] **Provenance**
  - Every row has provenance value? Not yet (only in simulation output)
  - Is it realistic for the data? ⚠️ All SYNTHETIC except destinations

---

## SECTION 12: ACTION ITEMS BY PRIORITY

### 🔴 CRITICAL (Do first — blocks everything)

```
[ ] Fix or document Gate-Lot coordinate conflict
    - Gate: 16.4911715, 80.5018052
    - Lot:  16.4911715, 80.5018052 (IDENTICAL)
    - Road distance: 275m (conflict!)
    Decision: [Survey real locations / Update coords / Keep placeholder+document]

[ ] Calibrate travel times (×4–5 for vehicle speed)
    - Current: 1.3 m/s (walking)
    - Target: 5–10 m/s (campus vehicle)
    - Check each road and apply correction

[ ] Add reverse edges to route graph
    - Add: Lot → Gate (return path)
    - Add: Destination → Lot (return paths)
    - Verify: is_driveable = true

[ ] Generate synthetic occupancy time-series
    - 1 month of data, 15-min intervals
    - Must enforce: occupied ≤ capacity, temporal continuity
    - Must have realistic patterns: morning peak, lunch dip, evening peak
```

### 🟡 HIGH (Do next — unblocks functionality)

```
[ ] Add 2–3 more parking lots with real/realistic coordinates
    - Removes single-lot bottleneck
    - Enables multi-lot optimization testing
    
[ ] Extend Provenance enum (add PUBLIC_OBSERVED, INFERRED, UNKNOWN)
    
[ ] Build route graph visualization
    - Verify connectivity makes sense
    - Check for unrealistic distances

[ ] Populate events calendar
    - Add exam periods, placement seasons, festivals
    - Set demand multipliers for each

[ ] Add more gates (2–3 total)
    - Main, visitor, service
    - Reduces single-gate assumption
```

### 🟠 MEDIUM (Do for polish)

```
[ ] Implement data quality validation script
    - Check capacity constraints
    - Check temporal continuity
    - Check leakage
    - Auto-generate DATA_QUALITY_REPORT.md

[ ] Document field-level provenance
    - Add columns to parking_lots, gates, roads
    - Track source, confidence, last_verified

[ ] Build campus road network (GPS survey)
    - Add inter-destination roads
    - Specify speed limits, restrictions
    - Update route graph
```

---

## END OF PIN-TO-PIN CHECKLIST

**Summary:** 
- ✅ **Structural integrity:** OK (FKs valid, schema sound)
- ⚠️ **Value calibration:** Issues (travel times wrong, coordinates conflict)
- ❌ **Data completeness:** Critical gaps (occupancy, events, multiple lots)

**Highest impact fix:** Add synthetic occupancy time-series → enables ML & validation
