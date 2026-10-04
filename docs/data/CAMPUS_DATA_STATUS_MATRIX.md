# VIT-AP CAMPUS DATA — STATUS MATRIX
## Quick Visual Summary: WHAT EXISTS ✅ vs WHAT'S MISSING ❌

---

## FEATURE COMPLETENESS SCORECARD

```
TOTAL COMPONENTS NEEDED: 30
✅ IMPLEMENTED: 12 (40%)
⚠️  PARTIAL: 6 (20%)
❌ MISSING: 12 (40%)

Overall readiness: 40% for research-grade work
```

---

## DETAILED FEATURE MATRIX

### CAMPUS CONFIGURATION
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Campus metadata (name, tz)  │   ✅   │     1     │ Complete             │
│ Destinations (11 buildings) │   ✅   │    11     │ Real (OSM)           │
│ Gates                       │   ⚠️   │     1     │ Placeholder only     │
│ Parking lots                │   ⚠️   │     1     │ Placeholder only     │
│ Roads                       │   ⚠️   │    12     │ Star topology, slow  │
│ Route graph edges           │   ✅   │    12     │ Sparse but valid     │
│ Parking boundary polygons   │   ❌   │     0     │ Empty field          │
│ Road geometry (line strings)│   ⚠️   │    12     │ Interpolated, not GPS│
│ Access restrictions         │   ❌   │   N/A     │ Not modeled          │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### OCCUPANCY & CAPACITY
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Parking capacity inventory  │   ⚠️   │     1     │ Single 50-space lot  │
│ Parking zone definitions    │   ⚠️   │     1     │ One generic zone     │
│ Gate throughput capacity    │   ⚠️   │     1     │ Synthetic 30 vehicles│
│ Historical occupancy        │   ❌   │     0     │ CRITICAL: No data    │
│ Real-time occupancy state   │   ⚠️   │     0     │ Schema exists, empty │
│ Occupancy rate calculation  │   ❌   │   N/A     │ Manual, not auto     │
│ Availability calculation    │   ⚠️   │   N/A     │ Available = cap - occ│
│ Overflow detection rules    │   ⚠️   │   N/A     │ Threshold undefined  │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### TEMPORAL DATA
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Academic calendar           │   ❌   │     0     │ CRITICAL: Empty      │
│ Exam periods                │   ❌   │     0     │ Not tracked          │
│ Semester dates              │   ❌   │     0     │ Not tracked          │
│ Holiday calendar            │   ❌   │     0     │ Not tracked          │
│ Event calendar              │   ⚠️   │     0     │ Schema exists, empty │
│ Event demand multipliers    │   ❌   │     0     │ Not defined          │
│ Arrival rate by time        │   ❌   │     0     │ CRITICAL: No profile │
│ Departure rate by time      │   ❌   │     0     │ CRITICAL: No profile │
│ Gate queue history          │   ❌   │     0     │ CRITICAL: No data    │
│ Road congestion history     │   ❌   │     0     │ CRITICAL: No data    │
│ Weather history             │   ❌   │     0     │ Not collected        │
│ Day-of-week patterns        │   ⚠️   │   N/A     │ Can be derived       │
│ Hour-of-day patterns        │   ⚠️   │   N/A     │ Can be derived       │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### TRAFFIC & MOVEMENT
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Vehicle arrival model       │   ⚠️   │   N/A     │ Simulation only      │
│ Vehicle departure model     │   ⚠️   │   N/A     │ Simulation only      │
│ Vehicle state transitions   │   ✅   │   N/A     │ Defined (7 states)   │
│ Route planning              │   ✅   │   N/A     │ Dijkstra implemented │
│ Travel time matrix          │   ⚠️   │    11×11  │ Limited (star only)  │
│ Inter-destination roads     │   ❌   │     0     │ Missing ~20 roads    │
│ Road speed calibration      │   ❌   │   N/A     │ All 1.3 m/s (wrong)  │
│ Queue length tracking       │   ⚠️   │     0     │ Schema exists, empty │
│ Queue waiting time          │   ❌   │   N/A     │ Not calculated       │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### ML & PREDICTION
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Historical training data    │   ❌   │     0     │ CRITICAL: No data    │
│ Feature engineering         │   ❌   │   N/A     │ Not implemented      │
│ Target variable definition  │   ✅   │   N/A     │ Defined (occ @ t+15) │
│ Baseline (historical avg)   │   ✅   │   N/A     │ Implemented          │
│ Baseline (moving avg)       │   ✅   │   N/A     │ Implemented          │
│ XGBoost model               │   ❌   │   N/A     │ Not implemented      │
│ Prediction uncertainty      │   ⚠️   │   N/A     │ Schema, not populated│
│ Prediction confidence       │   ❌   │   N/A     │ Not tracked          │
│ Cross-validation splits     │   ❌   │   N/A     │ Not implemented      │
│ Prediction API endpoint     │   ❌   │   N/A     │ Not built            │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### DATA QUALITY & VALIDATION
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Data quality checks         │   ❌   │   N/A     │ No automation        │
│ Capacity constraint enforce │   ❌   │   N/A     │ Manual validation     │
│ Temporal continuity checks  │   ❌   │   N/A     │ Not implemented      │
│ Leakage detection           │   ❌   │   N/A     │ Not tested           │
│ Data freshness tracking     │   ✅   │   N/A     │ Schema defined       │
│ Provenance annotation       │   ⚠️   │   N/A     │ Enum incomplete      │
│ Source conflict resolution  │   ❌   │   N/A     │ Not handled          │
│ Missing value handling      │   ❌   │   N/A     │ No explicit strategy │
│ Data quality report gen     │   ❌   │   N/A     │ Not automated        │
│ Realism validation report   │   ❌   │   N/A     │ Not automated        │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### SIMULATION & EXPERIMENTS
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Simulation engine           │   ✅   │   N/A     │ Fully implemented    │
│ Scenario definition         │   ✅   │   N/A     │ YAML-based config    │
│ Random seed support         │   ✅   │   N/A     │ Reproducible         │
│ Vehicle model               │   ✅   │   N/A     │ Arrival/departure    │
│ Parking assignment          │   ✅   │   N/A     │ First available, etc │
│ Queue simulation            │   ✅   │   N/A     │ Implemented          │
│ Congestion modeling         │   ⚠️   │   N/A     │ Static, not dynamic  │
│ Event scenario support      │   ⚠️   │   N/A     │ Schema, needs events │
│ Road closure scenario       │   ✅   │   N/A     │ Configurable         │
│ Baseline strategy 1         │   ✅   │   N/A     │ First Available      │
│ Baseline strategy 2         │   ✅   │   N/A     │ Nearest Available    │
│ Proposed strategy (ParkNav) │   ✅   │   N/A     │ Optimization-based   │
│ Experiment reproducibility  │   ✅   │   N/A     │ Run ID tracking      │
│ Experiment metadata         │   ✅   │   N/A     │ Full traceability    │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

### API & INTEGRATION
```
┌─────────────────────────────┬────────┬───────────┬──────────────────────┐
│ Feature                     │ Status │ Data rows │ Notes                │
├─────────────────────────────┼────────┼───────────┼──────────────────────┤
│ Campus config API           │   ✅   │   N/A     │ Fully functional     │
│ Parking state API           │   ✅   │   N/A     │ Fully functional     │
│ Gate state API              │   ✅   │   N/A     │ Fully functional     │
│ Road state API              │   ✅   │   N/A     │ Fully functional     │
│ Route planning API          │   ✅   │   N/A     │ Fully functional     │
│ Recommendation API          │   ⚠️   │   N/A     │ Works, but limited   │
│ Prediction API              │   ❌   │   N/A     │ Not implemented      │
│ Event query API             │   ❌   │   N/A     │ No endpoint          │
│ Historical data API         │   ❌   │   N/A     │ No endpoint          │
└─────────────────────────────┴────────┴───────────┴──────────────────────┘
```

---

## BLOCKING ISSUE SUMMARY

### 🔴 CRITICAL (Research Cannot Proceed Without These)

1. **Single parking lot**
   - Current: 1 placeholder lot (50 spaces)
   - Needed: 3–5 real/realistic lots
   - Impact: Can't test multi-lot optimization, no meaningful choice for algorithm
   - Blocking: Entire value proposition of parking optimizer

2. **No occupancy history**
   - Current: 0 data rows
   - Needed: 1 month × 96 15-min snapshots = 2,880 rows minimum
   - Impact: Can't train ML models, can't compare vs baselines, can't validate
   - Blocking: ML pipeline, baseline comparison, validation

3. **Gate & Lot coordinate conflict**
   - Current: Same coordinates (16.4911715, 80.5018052) but 275m road distance
   - Needed: Real gate location OR documentation of why placeholder
   - Impact: Impossible geometry, confuses route planning
   - Blocking: Realistic scenario testing

4. **Travel time miscalibration**
   - Current: 1.3 m/s (walking speed)
   - Needed: 5–10 m/s (vehicle speed), multiply times by 4–5
   - Impact: Route recommendations are unrealistic (no urgency factor)
   - Blocking: Realistic decision latency measurement

### 🟡 HIGH (Needed for Full Functionality)

5. **No temporal demand patterns**
   - Needed: Arrival/departure rates by hour/day/week
   - Impact: Can't model realistic demand, every scenario same
   - Blocking: Event-aware prediction

6. **Missing inter-destination roads**
   - Needed: 20+ roads between buildings
   - Impact: Star topology, unrealistic routing
   - Blocking: Multi-path testing, congestion distribution

7. **No event calendar**
   - Needed: Exam dates, placement season, festivals
   - Impact: Can't test event-aware demand prediction
   - Blocking: Real-world scenario validation

8. **No academic calendar**
   - Needed: Semester dates, breaks, exam periods
   - Impact: Can't model semester demand variation
   - Blocking: Seasonal pattern validation

### 🟠 MEDIUM (Needed for Polish/Publication)

9. **No data quality automation**
   - Needed: Validate constraints, temporal continuity, leakage
   - Impact: Manual validation only, error-prone
   - Blocking: Research reproducibility claims

10. **Field-level provenance missing**
    - Needed: Track source of each value (not just dataset)
    - Impact: Can't trace where a suspicious value came from
    - Blocking: Audit trail, academic rigor

---

## QUICK REFERENCE: WHERE TO FIND DATA

```
Campus Configuration:
  └── configs/campuses/vitap.yaml          [✅ Complete, but placeholder lots/gates]

Current State Data:
  └── digital_twin.db (empty tables)
      ├── parking_lot_state             [❌ 0 rows]
      ├── gate_state                    [❌ 0 rows]
      ├── road_state                    [❌ 0 rows]
      └── vehicle_state                 [❌ 0 rows until simulation runs]

Historical Data:
  └── (does not exist)                   [❌ Missing entirely]

Time-Series Data:
  └── (does not exist)                   [❌ Missing entirely]

Simulation Output:
  └── experiments/runs/                  [✅ Exists after simulation]

Exported Data:
  └── experiments/csv_export/            [✅ CSVs of current state]

Documentation:
  └── docs/PROVENANCE.md                 [✅ Exists, explains what's synthetic]
```

---

## DATA VOLUME TARGETS

To approach "best results" for research publication, aim for:

| Data Component | Current | Target | Growth |
|---|---|---|---|
| Destinations | 11 | 20+ | 2× |
| Parking lots | 1 | 5 | 5× |
| Gates | 1 | 2–3 | 2–3× |
| Roads | 12 | 40+ | 3× |
| Occupancy observations (monthly) | 0 | 2,880 | ∞ |
| Gate queue observations (monthly) | 0 | 2,880 | ∞ |
| Road state observations (monthly) | 0 | 2,880 | ∞ |
| Event records | 0 | 15–20 | ∞ |
| Academic calendar entries | 0 | 6–8 | ∞ |
| Vehicle simulation records per run | 0 | 500–1000 | ∞ |

---

## SUCCESS CRITERIA FOR "GOOD AND BEST RESULTS"

### Phase 1: Good Results (Minimum Viable)
- [ ] Multiple parking lots (3+) with distinct capacities
- [ ] 1 month of synthetic occupancy data
- [ ] Travel times calibrated to vehicle speeds
- [ ] Temporal demand patterns (morning peak, etc.)
- [ ] Data quality validation script
- [ ] Clear provenance labeling (REAL vs SYNTHETIC)

### Phase 2: Best Results (Full Featured)
- [ ] GPS-surveyed campus configuration
- [ ] Real historical occupancy data (3+ months)
- [ ] Real gate queue observations
- [ ] Complete academic calendar
- [ ] Event demand multipliers
- [ ] ML model trained & validated
- [ ] Automated data quality reports
- [ ] Field-level provenance tracking
- [ ] Published research article with validation

---

## NEXT STEPS (IMMEDIATE)

**Do these first (1–2 days):**

1. [ ] Fix Gate-Lot coordinate conflict
2. [ ] Calibrate travel times (×4–5)
3. [ ] Add reverse edges to graph
4. [ ] Generate 1 month synthetic occupancy

**Then (1 week):**

5. [ ] Add 2–3 more parking lots
6. [ ] Populate events calendar
7. [ ] Add academic calendar
8. [ ] Build data quality validation

**Then (ongoing):**

9. [ ] GPS survey for real data
10. [ ] Train ML models
11. [ ] Publish validation results

---

## END OF STATUS MATRIX

**Document version:** 1.0  
**Last updated:** 2026-09-24  
**Status:** Ready to act on
