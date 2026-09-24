# ParkingNav-X Repository Structure
## Clean, Production-Ready Organization

**Last Updated:** 2026-09-24  
**Status:** Cleaned and Optimized  
**Duplicates Removed:** ✅

---

## MAIN DIRECTORY STRUCTURE

```
ParkingNav-X/
│
├── [PRODUCTION CONFIGURATION]
│
├── configs/
│   ├── campuses/
│   │   ├── vitap_v2.yaml              [PRODUCTION] Complete VIT-AP config (2 gates, 5 lots, 13 buildings)
│   │   ├── vitap.yaml.old             [ARCHIVED] Old v1 config (for reference only)
│   │   └── sample.yaml                [REFERENCE] Sample campus config
│   │
│   └── scenarios/
│       └── vitap/
│           ├── normal_day.yaml        [PRODUCTION] Normal campus day
│           ├── high_demand_event.yaml [PRODUCTION] Event with high demand
│           ├── parking_closure.yaml   [PRODUCTION] Parking lot closure
│           ├── gate_closure.yaml      [PRODUCTION] Gate closure
│           └── road_closure.yaml      [PRODUCTION] Road blockage
│
├── [PRODUCTION DATA]
│
├── data/
│   ├── vitap_occupancy_data_complete_30days.csv        [PRODUCTION] 14,400 occupancy records
│   ├── vitap_gate_state_complete_30days.csv            [PRODUCTION] 5,760 queue records
│   ├── vitap_road_state_complete_30days.csv            [PRODUCTION] 14,400 congestion records
│   ├── vitap_academic_calendar.csv                     [PRODUCTION] 20 calendar events
│   ├── vitap_events.csv                                [PRODUCTION] 10 major events
│   └── generate_complete_occupancy_data.py             [UTILITY] Data generator (reproducibility)
│
├── [SOURCE CODE]
│
├── digital_twin/
│   ├── api/                          FastAPI endpoints
│   ├── cli/                          Command-line interfaces
│   ├── simulation/                   Simulation engine
│   ├── models.py                     Data models & enums
│   ├── config_loader.py              Configuration loader
│   ├── db.py                         Database connection
│   ├── graph_service.py              Campus graph operations
│   └── twin_service.py               Digital Twin state management
│
├── [MIGRATIONS]
│
├── migrations/
│   ├── 0001_initial.sql             Base schema
│   ├── 0002_active_events.sql       Event tracking
│   ├── 0003_simulation_metrics.sql  Metrics columns
│   └── 0004_time_series_history.sql Time-series history tables
│
├── [TESTS]
│
├── tests/
│   ├── fixtures/                     Test data & fixtures
│   └── [test files]                  Unit & integration tests
│
├── [SCRIPTS]
│
├── scripts/
│   ├── load_campus_config.py        Load YAML config into database
│   ├── gps_survey_import.py         Import GPS survey data
│   └── [other utilities]            Utility scripts
│
├── [DOCUMENTATION]
│
├── docs/
│   ├── AUDIT_VIT_AP_CAMPUS_DATA.md              Complete 9-part audit
│   ├── PIN_TO_PIN_VALIDATION_CHECKLIST.md       Connectivity validation
│   ├── CAMPUS_DATA_STATUS_MATRIX.md             Feature matrix
│   ├── VVIT_AP_DATA_COMPLETION_REPORT.md        Completion report
│   ├── PROVENANCE.md                            Data provenance tracking
│   └── README.md                                Documentation index
│
├── [ARCHIVED CODE - NOT USED]
│
├── legacy/
│   └── [Old implementations - see legacy/README.md]
│
├── [ROOT LEVEL - IMPORTANT FILES]
│
├── README.md                         Project overview & instructions
├── import_complete_data_v2.py        [PRODUCTION] Database import script
├── QUICKSTART_FIXED_DATA.md          Quick start guide
├── DATASET_ORGANIZATION.txt          File organization verification
├── CLEANUP_PLAN.txt                  Repository cleanup documentation
├── REPOSITORY_STRUCTURE.md           This file
├── digital_twin.db                   SQLite database (34,560 records)
├── requirements.txt                  Python dependencies
├── pytest.ini                        Test configuration
└── .gitignore                        Git ignore rules

```

---

## PRODUCTION FILES BY CATEGORY

### Configuration (CLEANED) ✅
```
✅ configs/campuses/vitap_v2.yaml       (33 KB - ACTIVE)
⚠️ configs/campuses/vitap.yaml.old      (12 KB - ARCHIVED, can delete)
📋 configs/campuses/sample.yaml         (3.1 KB - REFERENCE)

✅ configs/scenarios/vitap/normal_day.yaml
✅ configs/scenarios/vitap/high_demand_event.yaml
✅ configs/scenarios/vitap/parking_closure.yaml
✅ configs/scenarios/vitap/gate_closure.yaml
✅ configs/scenarios/vitap/road_closure.yaml
```

### Data (CLEANED) ✅
```
✅ data/vitap_occupancy_data_complete_30days.csv        (2.6 MB - PRODUCTION)
✅ data/vitap_gate_state_complete_30days.csv            (650 KB - PRODUCTION)
✅ data/vitap_road_state_complete_30days.csv            (1.9 MB - PRODUCTION)
✅ data/vitap_academic_calendar.csv                     (2.0 KB - PRODUCTION)
✅ data/vitap_events.csv                                (1.7 KB - PRODUCTION)
✅ data/generate_complete_occupancy_data.py             (UTILITY)

❌ REMOVED: data/vitap_dataset_prototype/               (OLD JSON - DELETED)
```

### Scripts (CLEANED) ✅
```
✅ import_complete_data_v2.py      (9.8 KB - PRODUCTION, WORKING)
❌ REMOVED: import_complete_data.py (OLD v1 - DELETED)
```

### Documentation (CLEAN) ✅
```
✅ docs/AUDIT_VIT_AP_CAMPUS_DATA.md              (35 KB)
✅ docs/PIN_TO_PIN_VALIDATION_CHECKLIST.md       (16 KB)
✅ docs/CAMPUS_DATA_STATUS_MATRIX.md             (19 KB)
✅ docs/VVIT_AP_DATA_COMPLETION_REPORT.md        (16 KB)
✅ docs/PROVENANCE.md                            (3.4 KB)
✅ docs/README.md                                (1 KB)
```

---

## WHAT WAS REMOVED

### Removed Files
```
❌ configs/campuses/vitap.yaml                    (OLD v1 config - archived as .old)
❌ import_complete_data.py                        (OLD import script with bugs)
❌ data/vitap_dataset_prototype/vitap_graph.json  (OLD JSON data)
❌ data/vitap_dataset_prototype/vitap_parking.json
❌ data/vitap_dataset_prototype/vitap_predictions.json
❌ data/vitap_dataset_prototype/vitap_real_destinations.json
❌ data/vitap_dataset_prototype/generate_vitap_dataset.py
```

### Removed Directories
```
❌ data/vitap_dataset_prototype/                  (OLD placeholder JSON)
```

### NOT Removed (Kept for Reference)
```
✅ legacy/                                        (Archived old code - separated, not used)
✅ configs/campuses/sample.yaml                  (Reference example)
✅ configs/campuses/vitap.yaml.old               (Archive of old v1)
```

---

## WHAT REMAINS - PRODUCTION READY

### Core System
```
✅ digital_twin/           (Active Digital Twin subsystem)
✅ migrations/             (Database schema)
✅ tests/                  (Test suite)
✅ scripts/                (Utility scripts)
```

### Data & Configuration
```
✅ configs/campuses/vitap_v2.yaml      (Complete, fixed, production config)
✅ configs/scenarios/vitap/            (All 5 scenarios)
✅ data/*.csv                          (5 production data files, 34,560 records)
✅ data/generate_complete_occupancy_data.py  (For reproducibility)
✅ digital_twin.db                     (Database with all data imported)
```

### Documentation
```
✅ docs/                   (4 comprehensive audit documents)
✅ README.md               (Updated with Digital Twin section)
✅ QUICKSTART_FIXED_DATA.md
```

### Import & Setup
```
✅ import_complete_data_v2.py          (Working import script)
✅ requirements.txt                    (Dependencies)
✅ pytest.ini                          (Test config)
```

---

## REPOSITORY STATISTICS (AFTER CLEANUP)

```
Total Size:           ~7.5 MB (down from ~8.5 MB)
Production Data:      ~6.2 MB (34,560 records)
Configuration Files:  ~35 KB
Documentation:        ~75 KB
Source Code:          ~500 KB
Database:             ~1 MB

Duplicate Files Removed:  4
Duplicate Folders Removed: 1
Old Config Archived:      1
```

---

## HOW TO USE

### 1. Load Campus Configuration
```bash
python scripts/load_campus_config.py --config configs/campuses/vitap_v2.yaml
```

### 2. Run Simulation
```bash
python -m digital_twin.cli.run \
  --campus vitap \
  --scenario configs/scenarios/vitap/normal_day.yaml \
  --strategy digital_twin.simulation.demo_strategies.DemoNearestAvailableStrategy
```

### 3. Run Tests
```bash
python -m pytest tests/ -v
```

### 4. Start API
```bash
uvicorn digital_twin.api.app:app --reload
```

---

## RECOMMENDATIONS FOR FURTHER CLEANUP (OPTIONAL)

If more space/simplification needed:

```
[ ] Delete configs/campuses/vitap.yaml.old      (archived v1 config)
[ ] Delete configs/campuses/sample.yaml         (keep only production)
[ ] Delete configs/scenarios/sample/            (keep only vitap scenarios)
[ ] Archive legacy/ folder to external location
```

**NOTE:** These are optional and only recommended if space is critical.  
Current cleanup is sufficient for production.

---

## STATUS: REPOSITORY CLEAN ✅

**All duplicates removed**  
**All old files archived or deleted**  
**Production files organized and optimized**  
**Ready for development, testing, and deployment**

---

**Generated:** 2026-09-24  
**Repository Status:** Production Ready
