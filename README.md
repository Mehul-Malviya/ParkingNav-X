# ParkingNav-X — Digital Twin + Simulation (Member 1)

**B.Tech Capstone 2026–27 · VIT-AP**  
**Owner:** Jyothi Reddy Pula (23BCE7882)  
**Module:** Member 1 — Digital Twin State Manager + Simulation Engine

A **predictive digital twin** for smart campus parking. Simulates real-time parking dynamics with event-aware demand, realistic physics, and deterministic reproducibility.

---

## **Quick Start**

### Run all tests (153 tests — including validation, E5, E7, failure cases)
```bash
pytest tests/ -v
```

### Run a simulation
```bash
python -c "
from pathlib import Path
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader
from digital_twin.simulation.strategy import FirstAvailableStrategy
from digital_twin.db import get_connection, apply_migrations
from digital_twin.config_loader import load_campus_config

conn = get_connection(':memory:')
apply_migrations(conn)
load_campus_config(Path('configs/campuses/sample.yaml'), conn)
engine = SimulationEngine()
scenario = ScenarioLoader.load('configs/scenarios/vitap/normal_day.yaml')
result = engine.run(scenario, FirstAvailableStrategy(), conn)
print(f'Parked: {sum(1 for v in result.vehicles if v[\"final_state\"] == \"parked\")}')
"
```

---

## **Folder Structure**

```
ParkingNav-X/
│
├── README.md                              ← You are here
│
├── digital_twin/                          Main simulation module
│   ├── config_loader.py                   Campus YAML validation
│   ├── graph_service.py                   Campus graph (NetworkX)
│   ├── twin_service.py                    Digital Twin state manager
│   ├── db.py                              SQLite schema
│   ├── models.py                          Enums & constants
│   │
│   ├── simulation/
│   │   ├── engine.py                      Main simulator (discrete-event)
│   │   ├── scenario.py                    Scenario config
│   │   ├── strategy.py                    Strategy interface (B1, B2)
│   │   ├── forecast_noise.py              Robustness: noise injection
│   │   ├── metrics_recorder.py            Output metrics to disk
│   │   └── state_snapshot.py              StateSnapshot for Member 3
│   │
│   ├── api_functions.py                   FastAPI functions for Member 4
│   │
│   └── validation/
│       └── calibration.py                 Real-data calibration
│
├── configs/
│   ├── campuses/
│   │   ├── sample.yaml                    Test campus (1 gate, 2 lots)
│   │   ├── vitap.yaml                     Real VIT-AP (2 gates, 5 lots)
│   │   └── synthetic_large.yaml           Large campus (3 gates, 6 lots)
│   │
│   └── scenarios/
│       ├── sample/                        Sample scenarios
│       └── vitap/                         VIT-AP scenarios
│           ├── normal_day.yaml            E1: baseline
│           ├── E2_event_placement.yaml    E2: placement event
│           ├── E3_lot_closure.yaml        E3: lot closure
│           ├── E4_gate_closure.yaml       E4: gate closure
│           └── E5_noise_{0,10,20}.yaml    E5: robustness
│
├── docs/
│   └── SYSTEM_ARCHITECTURE.html           Complete system explanation
│
├── member1/
│   ├── simulation_model.md                Complete formal specification
│   ├── interfaces.md                      Handshake with Members 2, 3, 4
│   └── OBSERVATION_PROTOCOL.md            Real-data collection (Phase 10)
│
├── scripts/
│   ├── export_campus_graph_png.py         Visualize campus
│   └── load_campus_config.py              Load campus CLI
│
├── tests/                                 153 tests (all passing)
│   ├── test_part1_campus_config.py        13 tests
│   ├── test_part2_campus_graph.py         7 tests
│   ├── test_part3_event_demand.py         11 tests
│   ├── test_part3_twin_properties.py      5 tests
│   ├── test_part4_part5_simulation.py     30 tests
│   ├── test_part5_baseline_strategies.py  4 tests
│   ├── test_part6_scenarios.py            9 tests
│   ├── test_decision_cycle.py             4 tests
│   ├── test_phase7_scenarios.py           10 tests
│   ├── test_phase8_metrics_recorder.py    5 tests
│   ├── test_phase9_interfaces.py          8 tests
│   ├── test_phase10_validation.py         10 tests
│   ├── test_config_validation.py          13 tests (invalid configs)
│   ├── test_statistical_verification.py   8 tests (NHPP, dwell, compliance)
│   ├── test_failure_cases.py              11 tests (edge cases, robustness)
│   ├── test_e5_robustness.py              8 tests (forecast noise)
│   ├── test_e7_counterfactual_replay.py   11 tests (real-data validation)
│   ├── test_e6_ablation.py                5 tests (ablation flags)
│   └── test_scalability.py                7 tests (500-1000 vehicles)
│
├── runs/                                  Simulation outputs (auto-created)
│   └── {scenario}/{strategy}/seed_{n}/    → metrics.json, vehicles.parquet
│
├── migrations/                            SQLite schema
├── pytest.ini                             Test config
└── requirements.txt                       Python dependencies
```

---

## **What This Module Does**

### **Phase 1: Campus Configuration**
- Load campus topology from YAML (gates, roads, lots, zones)
- Validate with 13-point error checker
- Build NetworkX graph for routing

### **Phase 2: Digital Twin State Manager**
- Track live state of all campus entities
- State transitions with invariant checking
- Snapshot/restore for what-if simulation
- Fork for independent copies

### **Phase 3: Demand Model**
- Non-homogeneous Poisson arrivals
- Event-aware multipliers (placement, exam, fest)
- Driver compliance behavior (85% follow strategy, 15% nearest)
- Deterministic per-seed

### **Phase 4: Physical Models**
- Gate queues (FIFO, multi-server)
- BPR road congestion formula
- Parking search time curves
- Reserved capacity handling

### **Phase 5: Simulation Engine**
- Discrete-event simulator (heapq-based)
- Seed discipline (same seed = identical results)
- Decision cycle every 5 minutes
- Latency measurement

### **Phase 6: Strategy Interface**
- B1 (First-Available) baseline
- B2 (Nearest-Available) baseline
- Adapter pattern: timeout + fallback + feasibility guard

### **Phase 7: Scenarios & Disruptions**
- Multiple test scenarios (E1–E5)
- Event-aware demand spikes
- Gate/lot closures
- Forecast-noise injector (robustness)

### **Phase 8: Metrics Recorder**
- 5 primary metrics (search time, wait time, queues, overflow, travel)
- Parquet/JSON export
- Manifest with config hash + git commit

### **Phase 9: Interfaces**
- StateSnapshot JSON for Member 3
- 8 FastAPI functions for Member 4
- ML dataset schema for Member 2

### **Phase 10: Validation**
- Calibration framework (real vs simulated)
- Counterfactual replay
- Honest error reporting

---

## **Key Metrics**

Every simulation reports:
1. **Avg search time (min)** — time to find parking
2. **Avg wait time (min)** — gate queue delays
3. **Avg gate queue** — peak demand indicator
4. **Max gate queue** — bottleneck
5. **Overflow events** — failed assignments
+ Travel time, distance, success rate

---

## **Run Tests**

```bash
# All tests
pytest tests/ -v

# Specific phase
pytest tests/test_part5_baseline_strategies.py -v

# With coverage
pytest tests/ --cov=digital_twin --cov-report=html
```

---

## **Documentation**

- **[SYSTEM_ARCHITECTURE.html](docs/SYSTEM_ARCHITECTURE.html)** — Complete system explanation (how data flows, what each component does, why it's designed this way)
- **[viva.md](docs/member1/viva.md)** — 12 viva questions with detailed answers (use for viva preparation)
- **[simulation_model.md](docs/member1/simulation_model.md)** — All formulas, parameters, justifications
- **[interfaces.md](docs/member1/interfaces.md)** — Data contracts with teammates (Member 2, 3, 4)
- **[OBSERVATION_PROTOCOL.md](docs/member1/OBSERVATION_PROTOCOL.md)** — Real-data collection process

---

## **Status: DEFINITION OF DONE COMPLETE** ✅

✅ **153 tests passing** (all phases + validation + E5 + E7 + failure cases)  
✅ **All 19 Definition of Done items ticked**  
✅ **Config validator rejects all invalid configs**  
✅ **Statistical verification: NHPP, dwell, compliance**  
✅ **Forecast-noise robustness (E5: 0/10/20% noise)**  
✅ **Failure cases tested & demo-able**  
✅ **Real-data counterfactual replay (E7)**  
✅ **Viva answers written (12 Q&A)**  
✅ **Ready for Final Review 17–21 November 2026**

---

**Present with confidence.** This is production-ready capstone code.
