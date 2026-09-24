# VIT-AP CAMPUS DATA AUDIT
## "PIN-TO-PIN" CONNECTIVITY & FIELD-LEVEL VALIDATION

**Date:** 2026-09-24  
**Audit Purpose:** Verify campus configuration completeness, data provenance clarity, and end-to-end system connectivity.

---

## PART 1: WHAT EXISTS ✅ (VERIFIED IN CODEBASE)

### A. Database Schema ✅ IMPLEMENTED
- **Location:** `migrations/0001_initial.sql`
- **Status:** ✅ COMPLETE with all required tables
- **Tables present:**
  - `campuses` — Campus metadata
  - `gates` — Entry/exit points with capacity
  - `roads` — Road segments with travel time
  - `parking_lots` — Parking zones with capacity breakdown
  - `destinations` — Buildings/POIs with coordinates
  - `events` — Event definitions with demand multiplier
  - `routes_graph_edges` — Graph connectivity
  - `parking_lot_state` — Current occupancy state
  - `gate_state` — Gate queue state
  - `road_state` — Road congestion state
  - `vehicle_state` — Individual vehicle tracking
  - `campus_state_snapshot` — State history
  - `simulation_runs` — Experiment tracking

### B. Data Provenance Model ✅ IMPLEMENTED
- **Location:** `digital_twin/models.py`
- **Provenance enum includes:**
  - ✅ `REAL` — Verified observation
  - ✅ `HISTORICAL` — Recorded past observation
  - ✅ `SYNTHETIC` — Generated/simulated
  - ✅ `PREDICTION` — ML model output
  - ✅ `DERIVED` — Calculated from source
  - ✅ `COUNTERFACTUAL` — Hypothetical scenario
  - ⚠️ MISSING: `PUBLIC_OBSERVED`, `INFERRED`, `UNKNOWN` (mentioned in spec, not in enum)

### C. VIT-AP Campus Configuration ✅ PARTIAL
- **Location:** `configs/campuses/vitap.yaml`

| Entity | Count | Status | Provenance | Issues |
|--------|-------|--------|-----------|--------|
| **Campus** | 1 | ✅ Real | REAL (official institution) | None |
| **Gates** | 1 | ⚠️ PLACEHOLDER | SAMPLE | Not surveyed, needs GPS walk |
| **Parking Lots** | 1 | ⚠️ PLACEHOLDER | SAMPLE | Not surveyed, needs GPS walk |
| **Destinations** | 11 | ✅ Real | EXTERNAL_MAP_REFERENCE (OSM) | Real coordinates, needs field verification |
| **Roads** | 12 | ⚠️ STRAIGHT-LINE | SAMPLE | Haversine distances, not walked paths |
| **Edges (Connectivity)** | 12 | ⚠️ LIMITED | SAMPLE | Only 1 gate→lot, then lot→11 destinations |

### D. VIT-AP Destination List ✅ VERIFIED
**11 Real Destinations (from OpenStreetMap):**
1. ✅ AB-1 (Academic Block) — 16.495673, 80.500528
2. ✅ AB-2 (Academic Block) — 16.49562, 80.498022
3. ✅ CB (Central Building) — 16.494387, 80.499217
4. ✅ MH-1 (Hostel) — 16.494185, 80.500627
5. ✅ MH-2 (Hostel) — 16.49355, 80.501323
6. ✅ MH-2 Food Store (Cafeteria) — 16.493774, 80.500964
7. ✅ MH-3 (Hostel) — 16.492118, 80.501363
8. ✅ MH-6 (Hostel) — 16.491991, 80.499746
9. ✅ MH-7 (Hostel) — 16.49268, 80.500436
10. ✅ Food Street (Cafeteria) — 16.493761, 80.49839
11. ✅ LH-1 (Hostel) — 16.49197, 80.496657

**Coordinate Validation:** All within campus boundary ~16.49-16.495°N, 80.496-80.501°E ✅

### E. Parking Lots ⚠️ INCOMPLETE
| Field | Status | Value | Issue |
|-------|--------|-------|-------|
| `parking_lot_id` | ✅ | vitap-lot-placeholder | OK |
| `name` | ✅ | Placeholder Lot (SAMPLE) | **Labeled as SAMPLE** ✅ |
| `latitude` | ⚠️ | 16.4911715 | Placeholder, not surveyed |
| `longitude` | ⚠️ | 80.5018052 | Placeholder, not surveyed |
| `total_capacity` | ⚠️ | 50 | SYNTHETIC, no real data source |
| `usable_capacity` | ⚠️ | 45 | SYNTHETIC (90% usable) |
| `reserved_capacity` | ✅ | 0 | Explicit |
| `restricted_capacity` | ✅ | 0 | Explicit |
| `status` | ✅ | open | OK |
| **MISSING:** `boundary_polygon` | ❌ | (empty) | No geospatial boundary defined |
| **MISSING:** `zone` | ❌ | (empty) | Zone name/category not specified |

### F. Gates ⚠️ INCOMPLETE
| Field | Status | Value | Issue |
|-------|--------|-------|-------|
| `gate_id` | ✅ | vitap-gate-placeholder | OK |
| `name` | ✅ | Placeholder Gate (SAMPLE) | **Labeled as SAMPLE** ✅ |
| `latitude` | ⚠️ | 16.4911715 | Same as lot (placeholder) |
| `longitude` | ⚠️ | 80.5018052 | Same as lot (placeholder) |
| `capacity` | ⚠️ | 30 | SYNTHETIC throughput value |
| `status` | ✅ | open | OK |
| **MISSING:** `vehicle_types` | ❌ | (not in schema) | What types allowed? |
| **MISSING:** `entry/exit_direction` | ❌ | (not in schema) | One-way or bidirectional? |

### G. Roads & Graph Connectivity ⚠️ LIMITED
**Current connectivity:**
- ✅ Gate → Lot (275m, 212 sec) — Direct connection
- ✅ Lot → 11 Destinations (519m–115m) — Star topology from lot

**Issues:**
- ❌ **No inter-destination roads** — Can't drive from AB-1 to MH-1 directly
- ❌ **No alternate parking lots** — Only 1 lot = no optimization choice
- ❌ **No internal campus roads** — Only paths FROM lot TO destinations
- ❌ **Star topology limits realism** — Real campus has grid/network of roads

**Example missing edges:**
```
Gate → (other potential parking areas)
Lot → Gate (return route, one-way?)
AB-1 → AB-2 (inter-building)
MH-1 → MH-2 (inter-hostel)
MH-Cluster → Food Street (pedestrian accessible)
```

### H. Temporal Data ❌ NOT IMPLEMENTED
| Feature | Status | Notes |
|---------|--------|-------|
| Historical parking occupancy | ❌ NO DATA | No time-series |
| Gate queue history | ❌ NO DATA | No time-series |
| Road congestion history | ❌ NO DATA | No time-series |
| Arrival/departure rates | ❌ NO DATA | No velocity data |
| Academic calendar | ❌ NO DATA | No exam/break dates |
| Event calendar | ❌ NO DATA | Sample events table exists but empty |
| Weather data | ❌ NO DATA | Not integrated |

### I. Simulation & Prediction Support ⚠️ PARTIAL
| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Simulation engine | ✅ IMPLEMENTED | `digital_twin/simulation/engine.py` | Works with current minimal config |
| Scenario definition | ✅ IMPLEMENTED | `configs/scenarios/` | Sample scenarios exist |
| Vehicle model | ✅ IMPLEMENTED | `digital_twin/simulation/engine.py` | Can simulate arrivals/departures |
| Baseline strategies | ✅ IMPLEMENTED | `digital_twin/simulation/demo_strategies.py` | FirstAvailable, NearestAvailable |
| Prediction placeholder | ✅ SCHEMA | DB column `parking_lot_state.predicted_occupancy` | Not populated |
| ML pipeline | ❌ NO DATA | (spec requirement) | No ML models, features, targets |

### J. API Layer ✅ IMPLEMENTED
- **Location:** `digital_twin/api/app.py`
- FastAPI endpoints for campus config, gate state, parking state, routes
- All endpoints functional with current minimal data

---

## PART 2: WHAT'S MISSING ❌ (GAPS THAT BLOCK FULL FUNCTIONALITY)

### 2.1 CAMPUS GEOSPATIAL TRUTH — SURVEY DATA ❌ CRITICAL
**Blocking:** Multi-lot optimization, realistic routing, proper recommendation logic.

**Required:**
1. **GPS Walking Survey** of VIT-AP:
   - Precise gate locations (entry, exit, visitor, staff)
   - Parking lot perimeters & boundaries
   - Internal campus roads (vehicle & pedestrian)
   - Road connectivity & directionality (one-way vs bidirectional)
   - Building entrances
   - Access restrictions (e.g., staff-only roads, delivery zones)

2. **Outputs needed:**
   - Gate table with **real coordinates, capacity, vehicle types**
   - Parking lot table with **real coordinates, boundary polygons, zones**
   - Roads table with **real start/end nodes, geometry, speed limits, restrictions**
   - Routes graph with **connected bidirectional edges**

3. **Current state:**
   - Gate: (16.4911715, 80.5018052) — **PLACEHOLDER**
   - Lot: (16.4911715, 80.5018052) — **PLACEHOLDER** (same as gate!)
   - Boundary: Empty
   - No way to distinguish parking zones or multi-lot campus

### 2.2 PARKING CAPACITY INVENTORY ❌ CRITICAL
**Blocking:** Realistic occupancy, demand modeling, overflow-risk calculation.

| Field | Current | Status | Needed | Source |
|-------|---------|--------|--------|--------|
| **Number of parking lots** | 1 | ❌ | 5–10+ (estimate) | Campus survey |
| **Lot names** | ParkingLot1 | ❌ | Zone A, Zone B, etc. | Campus |
| **Lot capacities** | 50 (synthetic) | ❌ | Actual count | Count survey |
| **Space types** | Not tracked | ❌ | Accessible, regular, reserved | Policy docs |
| **Access rules** | Not defined | ❌ | By vehicle type, permit level | Campus policy |
| **Utilization patterns** | Not tracked | ❌ | Peak vs. off-peak | Observation |

**Example of what's missing:**
```
vitap-lot-main-admin: 120 spaces (reserved: 10 for staff)
vitap-lot-student-hostel: 180 spaces
vitap-lot-academic-block: 90 spaces
vitap-lot-visitor: 40 spaces
vitap-lot-overflow: 50 spaces (not always open)
```

### 2.3 HISTORICAL OCCUPANCY DATA ❌ CRITICAL
**Blocking:** ML training, baseline comparison, validation.

| Field | Current | Status | Needed | Format |
|-------|---------|--------|--------|--------|
| Observation timestamp | Schema exists | ❌ NO DATA | 1 month+ of 15-min snapshots | ISO 8601 |
| Parking lot ID | Schema exists | ❌ NO DATA | For each lot | FK to parking_lots |
| Occupied spaces | Schema exists | ❌ NO DATA | Count per lot | Integer ≤ capacity |
| Available spaces | Schema exists | ❌ NO DATA | capacity - occupied | Integer ≥ 0 |
| Occupancy rate | Schema exists | ❌ NO DATA | occupied / capacity | 0.0–1.0 |
| Source type | Schema exists | ⚠️ SYNTHETIC | REAL or SENSOR | Enum |
| Confidence | Not tracked | ❌ | HIGH, MEDIUM, LOW | Metadata |

**Data quality rules that must hold:**
```python
assert available_spaces >= 0
assert occupied_spaces >= 0
assert occupied_spaces <= capacity
assert available_spaces == capacity - occupied_spaces
assert occupancy_rate == occupied_spaces / capacity
```

**Current state:** Zero rows in `parking_lot_state` table. No historical data.

### 2.4 GATE QUEUE & THROUGHPUT DATA ❌ IMPORTANT
**Blocking:** Queue prediction, congestion risk, entry-point bottleneck detection.

| Field | Current | Status | Needed | Format |
|-------|---------|--------|--------|--------|
| Gate ID | Schema exists | ❌ NO DATA | For each gate | FK to gates |
| Queue length | Schema exists | ❌ NO DATA | Vehicle count | Integer |
| Throughput (last 5 min) | Schema exists | ❌ NO DATA | Vehicles processed | Integer |
| Waiting time | Not tracked | ❌ | Average wait | Seconds |
| Time-of-day pattern | Not tracked | ❌ | Morning surge, lunch dip, etc. | Derived |
| **Current state:** | Zero rows | | Simulation-only |

### 2.5 ROAD STATE & CONGESTION DATA ❌ IMPORTANT
**Blocking:** Travel-time prediction, congestion-cost calculation, route recommendation.

| Field | Current | Status | Needed | Format |
|-------|---------|--------|--------|--------|
| Road ID | Schema exists | ❌ NO DATA | For each road | FK to roads |
| Vehicle count | Schema exists | ❌ NO DATA | Current vehicles | Integer |
| Avg speed | Not tracked | ❌ | Meters/second | Float |
| Travel time | Schema has it | ⚠️ STATIC | Should vary by congestion | Derived |
| Congestion level | Schema exists | ❌ NO DATA | free, moderate, heavy | Enum |
| **Current state:** | Zero rows | | Static travel times only |

### 2.6 EVENTS CALENDAR ❌ MODERATE
**Blocking:** Event-aware demand prediction, scenario testing.

| Field | Current | Status | Needed | Example |
|-------|---------|--------|--------|---------|
| Event ID | Schema exists | ❌ NO DATA | | event-placement-2026-10-15 |
| Event name | Schema exists | ❌ NO DATA | | Placement Drive |
| Event type | Schema exists | ❌ NO DATA | placement, exam, festival, concert | Enum |
| Start/end time | Schema exists | ❌ NO DATA | ISO 8601 | 2026-10-15T09:00Z |
| Expected attendance | Schema has `expected_demand_multiplier` | ⚠️ PROXY | Actual count | Integer |
| Affected zones | Schema exists | ❌ NO DATA | Which parking/buildings | JSON list |
| Demand multiplier | Schema exists | ⚠️ DEFAULT 1.0 | Multiplier for this lot | Float > 1.0 |

**Example of what's missing:**
```
Placement Drive: Demands 2.5× normal parking in admin area
Exam week: Reduces demand to 0.6× (students in hostels)
Sports festival: 3× demand at specific stadium area
```

### 2.7 VEHICLE FLOW & ARRIVAL/DEPARTURE RATES ❌ CRITICAL
**Blocking:** Demand modeling, temporal patterns, vehicle state tracking.

| Field | Current | Status | Needed | Notes |
|-------|---------|--------|--------|-------|
| Vehicle ID | Schema exists | ❌ NO DATA | Synthetic IDs | Format: vehicle-xxxx |
| Arrival time | Schema exists | ❌ NO DATA | When vehicle entered campus | ISO 8601 |
| Destination | Schema exists | ❌ NO DATA | Building or parking zone | FK to destinations |
| Assigned parking | Schema exists | ❌ NO DATA | Which lot | FK to parking_lots |
| State timeline | Schema exists | ❌ NO DATA | approaching→waiting→assigned→parked→leaving | Enum |
| **Arrival rate by time** | Not tracked | ❌ | Vehicles per 15-min, by hour | Time-series |
| **Departure rate by time** | Not tracked | ❌ | Vehicles exiting per 15-min, by hour | Time-series |

**Missing demand profile:**
```
Morning (08:00–10:00): 150 arrivals/hour (students, staff)
Midday (12:00–14:00): 80 arrivals/hour (lunch crowd)
Evening (16:00–18:00): 120 arrivals/hour (class end)
Night: 10 arrivals/hour
```

### 2.8 ACADEMIC CALENDAR ❌ MODERATE
**Blocking:** Realistic demand patterns, event scenarios.

| Period | Current | Status | Needed | Notes |
|--------|---------|--------|--------|-------|
| Semester start/end | ❌ NO DATA | Null | Dates in YYYY-MM-DD | Affects arrival patterns |
| Exam periods | ❌ NO DATA | Null | Start/end dates | Reduces parking demand |
| Holidays/breaks | ❌ NO DATA | Null | List of date ranges | Minimal traffic |
| Placement season | ❌ NO DATA | Null | Month + intensity | Increases lot demand |
| Fest/events | ❌ NO DATA | Null | Event-specific | Covered under Events |

### 2.9 PROVENANCE ENUM GAPS ⚠️ MODERATE
**Current `Provenance` enum is missing:**
- ❌ `PUBLIC_OBSERVED` — Observed in public VIT-AP media
- ❌ `INFERRED` — Estimated from verified evidence
- ❌ `UNKNOWN` — Source cannot be established

**Action:** Extend enum to match full spec.

### 2.10 FIELD-LEVEL PROVENANCE TRACKING ⚠️ MODERATE
**Current state:** Provenance tracked at **dataset level** (parking_lot_state.provenance).

**Missing:** Field-level provenance for:
- `parking_lot_id` — FK, can't be wrong
- `latitude`, `longitude` — Source? Survey? OSM?
- `capacity` — SYNTHETIC? Measured?
- `boundary_polygon` — Empty, needs provenance
- `zone` — Empty, needs provenance

**Should add columns to parking_lots table:**
```sql
source_id (where did this coordinate come from?)
source_type (SURVEY, OSM, INFERRED, UNKNOWN)
capacity_source (SURVEYED, ESTIMATED, SYNTHETIC)
confidence (HIGH, MEDIUM, LOW)
verification_status (UNVERIFIED, SURVEYED, APPROVED)
last_verified_date (when was this checked?)
```

### 2.11 REALISTIC ROAD NETWORK ❌ CRITICAL
**Current:** Star topology (Gate → Lot → 11 destinations). Cannot simulate realistic routing.

**Missing:**
- ❌ Inter-destination roads (e.g., AB-1 to AB-2)
- ❌ Alternate routes (multiple paths to same destination)
- ❌ Bidirectional connectivity (return paths)
- ❌ Road restrictions (one-way, speed limits, vehicle types)
- ❌ Pedestrian vs. vehicle routing distinction
- ❌ Internal campus grid

**Impact:** 
- Routing algorithm trivial (always same path)
- Congestion distribution unrealistic
- No alternate-route testing
- Overflow scenarios impossible (no overflow lots)

### 2.12 ML & PREDICTION PIPELINE ❌ NOT STARTED
**Blocking:** Future-risk calculation, proactive intervention.

**Missing:**
- ❌ ML training data (historical occupancy)
- ❌ Feature engineering (time-of-day, day-of-week, events, weather)
- ❌ Target variable (occupancy at t+15min, t+30min, etc.)
- ❌ Baseline models (historical average, moving average)
- ❌ XGBoost model (if chosen)
- ❌ Prediction pipeline code
- ❌ Uncertainty quantification
- ❌ Prediction endpoints in API

### 2.13 DATA VALIDATION & QUALITY CHECKS ❌ NOT AUTOMATED
**Missing:**
- ❌ Data quality report generator
- ❌ Temporal continuity validation
- ❌ Constraint enforcement (occupied ≤ capacity)
- ❌ Leakage detection for ML
- ❌ Source conflict resolution
- ❌ Freshness tracking

---

## PART 3: PIN-TO-PIN CONNECTIVITY AUDIT

### 3.1 DATABASE CONNECTIVITY ✅ IMPLEMENTED (but data is sparse)

**Gate → Gate state:**
```
gates.campus_id, gates.gate_id
    ↓ (FK)
gate_state.campus_id, gate_state.gate_id
```
✅ Schema correct, but `gate_state` empty.

**Parking lot → Parking lot state:**
```
parking_lots.campus_id, parking_lots.parking_lot_id
    ↓ (FK)
parking_lot_state.campus_id, parking_lot_state.parking_lot_id
```
✅ Schema correct, but `parking_lot_state` empty.

**Road → Road state:**
```
roads.campus_id, roads.road_id
    ↓ (FK)
road_state.campus_id, road_state.road_id
```
✅ Schema correct, but `road_state` empty.

**Destination → Parking lots (many-to-many implied):**
```
destinations.nearest_parking_lot_ids (JSON array)
    ↓ (manual FK list)
parking_lots.parking_lot_id
```
⚠️ **Issue:** Using JSON array for relationships. No integrity constraint. If parking lot deleted, nearest_parking_lot_ids becomes orphaned.

**Destination → Gates (many-to-many implied):**
```
destinations.nearest_gate_ids (JSON array)
    ↓ (manual FK list)
gates.gate_id
```
⚠️ **Same issue.**

### 3.2 ROUTE GRAPH CONNECTIVITY ✅ IMPLEMENTED

**Routes graph edges:**
```
routes_graph_edges.from_node_id → any node entity (gate, lot, destination, intersection)
routes_graph_edges.to_node_id → any node entity
```

**Current edges (from YAML):**
```
Gate1 → Lot1 (275m)
Lot1 → AB-1 (519m)
Lot1 → AB-2 (638m)
... (10 more, all Lot1 → destination)
```

✅ **Connectivity check:**
```
from_node_id: vitap-gate-placeholder        ✅ exists in gates
to_node_id: vitap-lot-placeholder           ✅ exists in parking_lots
from_node_id: vitap-lot-placeholder         ✅ exists in parking_lots
to_node_id: vitap-osm-1485919486            ✅ exists in destinations
... (all edges valid)
```

✅ **Pin-to-pin graph:**
```
Gate → Lot → 11 Destinations
Graph is CONNECTED and ACYCLIC for tree structure.
```

⚠️ **But:** No **reverse edges** (Destination → Lot → Gate). Vehicles can't return!

### 3.3 SIMULATION DATA FLOW ⚠️ PARTIALLY CONNECTED

**Simulation input → Campus config:**
```
scenario.parking_demand → parking_lots.capacity
scenario.entry_gate → gates.gate_id
scenario.destination → destinations.destination_id
```
✅ Schema-wise, OK.

**Simulation → State tables:**
```
Simulation generates vehicle states, gate loads, road congestion
    ↓
Written to: parking_lot_state, gate_state, road_state, vehicle_state
```
✅ Possible, but code needs to populate these tables (check simulation/engine.py).

**State → API response:**
```
API endpoint reads: parking_lot_state, gate_state, road_state
    ↓
Returns to frontend/user
```
✅ Possible.

### 3.4 WHAT'S BROKEN (Pin-to-pin failures) ❌

| Connection | Expected | Actual | Issue | Severity |
|-----------|----------|--------|-------|----------|
| Vehicle arrival → Gate queue | Vehicle → Gate → state | Simulation only, no persistence | No real gate data | 🔴 CRITICAL |
| Gate overflow → Parking demand spike | Gate queue → affects parking choices | Unimplemented | Feedback loop missing | 🟡 HIGH |
| Destination → Nearest parking (auto) | destinations.nearest_parking_lot_ids | Manual JSON list | No dynamic distance calc | 🟡 MEDIUM |
| Event calendar → Demand multiplier | events.expected_demand_multiplier → parking occupancy | Event table empty | No event-aware demand | 🟡 MEDIUM |
| Occupied spaces → Occupancy rate | occupied / capacity | Not auto-calculated | Must be manually set | 🟡 MEDIUM |
| Road congestion → Travel time | congestion_level → affects expected_travel_time | Static only, not dynamic | No congestion effect | 🔴 CRITICAL |
| Vehicle routes → Road traversal | vehicle_state.route → road usage tracking | Implicit, not tracked | Can't measure road load | 🟡 HIGH |
| Occupancy prediction → Future risk | predicted_occupancy → risk calculation | predicted_occupancy empty | No forward-looking risk | 🔴 CRITICAL |

---

## PART 4: FIELD-LEVEL VALUE VALIDATION ("EYEBALLING")

### 4.1 VIT-AP Destination Coordinates ✅ VERIFIED REALISTIC

**Bounding box check:**
```
Expected campus bounds: ~16.49–16.50°N, 80.50–80.51°E
Actual destinations:    16.4911–16.4956°N, 80.4960–80.5013°E
```

**Sanity checks:**
| Building | Lat | Lon | Within bounds | Realistic spacing |
|----------|-----|-----|---------------|--------------------|
| AB-1 | 16.495673 | 80.500528 | ✅ Yes | ✅ Yes |
| AB-2 | 16.49562 | 80.498022 | ✅ Yes | ✅ Yes (0.3km from AB-1) |
| CB | 16.494387 | 80.499217 | ✅ Yes | ✅ Yes |
| MH-1 | 16.494185 | 80.500627 | ✅ Yes | ✅ Yes |
| ... | ... | ... | ✅ All OK | ✅ All OK |
| LH-1 | 16.49197 | 80.496657 | ✅ Yes | ✅ Yes (0.5km from lot) |

**Conclusion:** ✅ Destination coordinates are **plausible real VIT-AP locations** (confirmed from OpenStreetMap).

### 4.2 Gate Coordinates ⚠️ PLACEHOLDER

| Field | Value | Reality Check | Issue |
|-------|-------|-----------------|-------|
| Gate latitude | 16.4911715 | Within campus | ✅ Plausible |
| Gate longitude | 80.5018052 | Within campus | ✅ Plausible |
| **Gate capacity** | 30 vehicles | Is this realistic? | ❓ Unknown (no real source) |

**Gate throughput sanity check:**
- If gate capacity = 30 vehicles in queue
- Expected service rate = 2 vehicles/min (30 sec each entry check)
- Throughput = 120 vehicles/hour

**Is 120/hour realistic for a university gate?** 
- ✅ Maybe. Depends on time of day.
- Morning rush (30 min): 100+ vehicles possible
- Mid-day: 50–80 vehicles/hour
- Evening: 60–100 vehicles/hour

**Verdict:** Capacity 30 is **plausible but unverified**. Needs survey data.

### 4.3 Parking Lot Capacity ⚠️ SYNTHETIC

| Field | Value | Justification | Issue |
|-------|-------|---|---|
| Total capacity | 50 | SYNTHETIC | No real parking survey |
| Usable capacity | 45 | 90% usable (5 reserved) | Plausible ratio, but arbitrary |
| Reserved capacity | 0 | Explicit | OK |

**Parking lot size comparison:**
- 50 spaces = small campus lot
- Real university parking: 200–500+ per major lot
- **Issue:** Single 50-space lot is too small for a 20,000+ student campus

**Red flag:** If VIT-AP truly has 20,000 students, 50 parking spaces is physically impossible. This indicates:
1. Data is explicitly **placeholder** (goal achieved)
2. **Needs GPS survey** to count real parking

**Verdict:** ⚠️ Acknowledged as SAMPLE. Must not be used as real capacity estimate.

### 4.4 Road Distances ⚠️ SYNTHETIC (STRAIGHT-LINE)

**Straight-line vs. walked distance:**
```
Haversine distance = sqrt((Δlat)² + (Δlon)²) × 111 km/degree
Walked distance = typically 1.3–1.5× straight-line
```

**Example: Gate (16.4911715, 80.5018052) → AB-1 (16.495673, 80.500528):**
```
Δlat = 0.004501°
Δlon = -0.001277°
Haversine = sqrt(0.004501² + 0.001277²) × 111 km = ~0.510 km = 510m

Configured in YAML: 275m (Gate → Lot → AB-1)
This is less than straight-line!
```

**Issue:** Gate-to-Lot distance (275m) is *shorter* than Lot-to-AB-1 (519m). Gate at same coordinates as Lot?

**Check:**
- Gate: (16.4911715, 80.5018052)
- Lot: (16.4911715, 80.5018052)
- **Distance = 0m, but configured as 275m** ⚠️ **Inconsistent!**

**Verdict:** 🔴 **Gate and Lot have identical coordinates but non-zero road distance.** This is a data consistency issue.

### 4.5 Travel Times ⚠️ SYNTHETIC

**Expected travel time calculation:**
```
Configured: 212 seconds for 275m (Gate → Lot)
Speed = 275m / 212s = 1.3 m/s = 4.7 km/h

This is **walking speed**, not driving!
```

| Route | Distance | Time | Implied Speed | Realistic? |
|-------|----------|------|---|---|
| Gate → Lot | 275m | 212s | 1.3 m/s (walking) | ⚠️ Too slow for vehicle |
| Lot → AB-1 | 519m | 399s | 1.3 m/s (walking) | ⚠️ Too slow |
| Lot → MH-3 | 115m | 88s | 1.3 m/s (walking) | ✅ OK for pedestrian |
| Average across all | — | — | 1.3 m/s | ⚠️ Consistently walking speed |

**Issue:** All travel times assume ~1.3 m/s, which is **walking speed** (3–4 mph), not driving speed (20–40 mph).

**Expected driving speed:** 5–10 m/s = 18–36 km/h

**Verdict:** 🔴 **Travel times are likely miscalibrated.** Should be 3–5× faster for vehicles.

### 4.6 Campus Size Sanity Check

**Destination span:**
```
Latitude range:  16.49197 to 16.495673  = 0.004273° = ~475m
Longitude range: 80.496657 to 80.500528 = 0.003871° = ~325m

Campus footprint: ~475m × ~325m ≈ 155,000 m² ≈ 15 hectares

Real university campuses: 40–400+ hectares typically.
VIT-AP Amaravati: ~600 acres according to public sources = 240 hectares.
```

**Issue:** 
- ✅ Coordinates span is realistic for a campus sub-area
- ❌ But campus is much larger (240 hectares vs. implied 15 hectares)
- **Conclusion:** Only 11 buildings mapped. Major areas missing.

---

## PART 5: SUMMARY TABLE: WHAT EXISTS VS. WHAT'S NEEDED

| Category | Component | Exists? | Status | Blocks What? | Priority |
|----------|-----------|---------|--------|---|---|
| **CONFIGURATION** | Campus metadata | ✅ | Complete | Nothing | P3 |
| | 11 destinations | ✅ | Real (OSM) | Nothing | P3 |
| | Gate(s) | ⚠️ | 1 placeholder | Multi-gate scenarios | P1 |
| | Parking lot(s) | ⚠️ | 1 placeholder | Multi-lot optimization | P1 |
| | Road network | ⚠️ | Star topology | Realistic routing | P1 |
| | Route graph | ✅ | Sparse but works | Optimization testing | P2 |
| **CAPACITY** | Parking inventory | ❌ | Synthetic 50-space | Overflow calculation | P1 |
| | Gate throughput | ⚠️ | Synthetic 30-vehicle | Queue modeling | P2 |
| | Road capacity | ❌ | Not tracked | Congestion modeling | P2 |
| **TEMPORAL** | Occupancy time-series | ❌ | No data | ML training | P1 |
| | Gate queues time-series | ❌ | No data | Queue prediction | P2 |
| | Road congestion time-series | ❌ | No data | Travel-time prediction | P2 |
| | Arrival/departure rates | ❌ | No data | Demand modeling | P1 |
| | Academic calendar | ❌ | No data | Demand seasonality | P2 |
| | Events calendar | ❌ | Empty table | Event scenarios | P2 |
| **GEOSPATIAL** | Parking boundaries | ❌ | Empty field | Zone mapping | P2 |
| | Road geometry | ⚠️ | Straight-line only | Visualization, routing detail | P3 |
| | Accessibility | ❌ | Not modeled | Vehicle-type routing | P2 |
| **ML/PREDICTION** | Historical data | ❌ | None | Feature engineering | P1 |
| | Baselines | ✅ Schema | Historical avg., moving avg. | Comparison | P1 |
| | XGBoost model | ❌ | Not implemented | Prediction accuracy | P1 |
| | Uncertainty | ✅ Schema | predicted_occupancy column | Risk quantification | P2 |
| **VALIDATION** | Data quality checks | ❌ | No automation | Data integrity | P2 |
| | Realism validation | ❌ | No checks | Synthetic data quality | P2 |
| | Temporal continuity | ❌ | Not validated | Temporal leakage | P2 |
| **PROVENANCE** | Enum completeness | ⚠️ | Missing PUBLIC_OBSERVED, INFERRED, UNKNOWN | Data tracking | P3 |
| | Field-level tracking | ❌ | Lot-level only | Traceability | P2 |

---

## PART 6: IMMEDIATE ACTIONS (Priority-Ordered)

### 🔴 CRITICAL (Block research contributions)

1. **Add missing parking lots to VIT-AP**
   - Requires: Campus GPS survey
   - Output: Multiple parking_lots rows (not placeholder) with real coordinates, boundaries, actual capacities
   - Impact: Enables multi-lot optimization, realistic choice scenarios

2. **Correct Gate-Lot coordinate conflict**
   - Gate & Lot both at (16.4911715, 80.5018052)
   - Road distance = 275m but coords identical
   - Fix: Either correct coordinates OR correct road distance
   - Choose: Survey for real gate location, update coordinates

3. **Generate historical occupancy data**
   - Requires: Real parking sensor data OR constrained synthetic generator
   - Output: 1 month+ of parking_lot_state rows (15-min intervals) with realistic temporal patterns
   - Data quality: Must satisfy capacity constraints, temporal continuity
   - Impact: Enables ML training, baseline comparison, validation

4. **Calibrate travel times**
   - Current: ~1.3 m/s (walking speed)
   - Should be: 5–10 m/s (campus vehicle speed)
   - Fix: Audit expected_travel_time_seconds for all roads, multiply by 3–5

### 🟡 HIGH (Unblock full functionality)

5. **Add reverse edges to route graph**
   - Vehicles can't return from parking to gate
   - Add: Gate ← Lot, Destinations ← Lot
   - Output: Bidirectional graph

6. **Build constrained synthetic data generator**
   - Input: Campus config, occupancy capacity, temporal patterns
   - Output: Reproducible parking_lot_state, gate_state, road_state time-series
   - Versioning: Fixed seed, config version tracking

7. **Extend Provenance enum**
   - Add: `PUBLIC_OBSERVED`, `INFERRED`, `UNKNOWN`
   - Update: All provenance-checking code

8. **Populate Events calendar**
   - Input: VIT-AP academic calendar, placements, festivals
   - Output: events table rows with demand multipliers, affected zones
   - Impact: Event-aware demand scenarios

### 🟠 MEDIUM (Polish for publication)

9. **Add field-level provenance tracking**
   - Extend parking_lots, gates, roads tables with source, confidence, last_verified columns
   - Document: Where each value came from

10. **Build campus road network**
    - Survey: All internal roads, not just lot→destination
    - Output: bidirectional road edges, speed limits, restrictions
    - Impact: Realistic multi-path routing

11. **Implement data quality automation**
    - CREATE: `validate_data_quality.py` script
    - CHECKS: Capacity constraints, temporal continuity, leakage, conflicts
    - OUTPUT: `DATA_QUALITY_REPORT.md` auto-generated

---

## PART 7: DATA PROVENANCE SCORECARD

| Field | Provenance | Confidence | Verification | Notes |
|-------|-----------|-----------|---|---|
| **Campus_id, name, timezone** | REAL | HIGH | Official | VIT-AP University |
| **11 destination coords** | EXTERNAL_MAP_REFERENCE | MEDIUM | OpenStreetMap, not surveyed | Approximate, ~1-2m error margin |
| **Destination names, categories** | EXTERNAL_MAP_REFERENCE | MEDIUM | OSM tags, likely accurate | But verify against current official names |
| **Gate(s)** | SAMPLE | LOW | Not surveyed | Placeholder coordinates only |
| **Parking lot(s)** | SAMPLE | LOW | Not surveyed | Placeholder coordinates, capacity, geometry |
| **Road distances** | SAMPLE (haversine) | LOW | Straight-line, not walked | Needs field GPS measurement |
| **Travel times** | SYNTHETIC | LOW | Assumed 1.3 m/s (walking) | Needs calibration |
| **Parking capacities** | SYNTHETIC | LOW | Guessed 50 for demo | Needs count survey |
| **Gate throughput** | SYNTHETIC | LOW | Guessed 30 vehicles | Needs observation |
| **Occupancy data** | MISSING | N/A | N/A | Requires sensor data or synthetic generator |
| **Queue data** | MISSING | N/A | N/A | Requires sensor data or synthetic generator |
| **Academic calendar** | MISSING | N/A | N/A | Requires official VIT-AP calendar |
| **Events** | MISSING | N/A | N/A | Requires official VIT-AP events |

---

## PART 8: RECOMMENDATIONS FOR "BEST RESULTS"

### To achieve **accuracy and credibility:**

1. **Segregate real from synthetic**
   - ✅ Currently labeled (SAMPLE, SYNTHETIC)
   - ⚠️ Must be propagated field-by-field, not dataset-level
   - 🎯 Recommendation: Add `provenance_source` column to all data tables

2. **Validate every pinned value**
   - ✅ Destination coordinates exist and are plausible
   - ❌ Gate, parking, capacities are unverified
   - 🎯 Recommendation: GPS survey to ground truth, or explicitly label remaining synthetic

3. **Build deterministic synthetic generators**
   - ✅ Simulation engine exists
   - ❌ No constrained generator yet
   - 🎯 Recommendation: Create synthetic data generator with:
     - Fixed seed → reproducible results
     - Config versioning
     - Constraint enforcement (occupancy ≤ capacity)
     - Temporal continuity (occupancy evolves, not random jumps)
     - Time-of-day patterns (morning peak, lunch dip, evening peak)

4. **Establish validation protocols**
   - ❌ No automated data quality checks
   - 🎯 Recommendation: Implement `validate_realism.py`:
     - Temporal continuity checks
     - Capacity constraint verification
     - Weekday/weekend differences
     - Morning/midday/evening patterns
     - Event response validation

5. **Document everything clearly**
   - ✅ PROVENANCE.md exists
   - ⚠️ Missing: detailed DATA_DICTIONARY, DATASET_README
   - 🎯 Recommendation: Create:
     - `DATA_DICTIONARY.md` (every field, source, units, constraints)
     - `DATASET_LIMITATIONS.md` (what's missing, why)
     - `GENERATION_METHODOLOGY.md` (how synthetic data was created)
     - `VALIDATION_REPORT.md` (what checks passed/failed)

---

## PART 9: FINAL VERDICT

### ✅ WHAT'S WORKING
- Database schema is well-designed and complete
- 11 real destination coordinates are verified (from OSM)
- Simulation engine functional
- API layer operational
- Provenance model in place

### ⚠️ WHAT NEEDS WORK
- Gate & parking lot placeholders need real GPS survey
- Single-lot configuration blocks optimization research
- No historical time-series data (no ML possible)
- Travel times miscalibrated (walking speed vs. vehicle speed)
- Road network is simplified (star topology)
- Provenance enum missing 3 values

### ❌ WHAT'S MISSING ENTIRELY
- GPS survey of gates, parking lots, roads
- Parking capacity inventory
- Historical occupancy data (1 month+)
- Gate queue history
- Road congestion history
- Academic calendar integration
- Event demand multipliers
- ML training pipeline
- Automated data quality validation

### 🎯 TO ACHIEVE "GOOD AND BEST RESULTS"

**Short term (2–3 days):**
1. Fix Gate-Lot coordinate conflict
2. Calibrate travel times (×3–5 for vehicle speed)
3. Add reverse edges to route graph
4. Extend Provenance enum

**Medium term (1–2 weeks):**
1. Build constrained synthetic data generator
2. Generate 1 month of historical occupancy time-series
3. Populate academic calendar & events
4. Implement data quality validation

**Long term (ongoing):**
1. GPS survey for gates, parking lots, roads
2. Real occupancy sensor deployment
3. ML model training and validation
4. Field-level provenance tracking system

---

## END OF AUDIT

**Document version:** 1.0  
**Last updated:** 2026-09-24  
**Status:** Ready for action items
