# Assumptions & Calibration — All 25+ Documented
**Author:** Jyothi Reddy Pula | **Date:** 5 October 2026

---

## A. DEMAND MODEL ASSUMPTIONS

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| A1 | Arrival rate profile exists per gate | Piecewise 8–15 vehicles/min | Estimated from typical campus hours | HIGH | Calibration against real gate counts (Phase 10) |
| A2 | Event-aware multipliers | placement=1.8×, exam=1.4×, fest=2.2×, sports=1.5× | Proposal §3 + similar universities | HIGH | Real event day observation (Oct 2026) |
| A3 | Dwell time distribution | LogNormal(μ=2.0, σ=0.8) | Typical campus parking (5–30 min) | MEDIUM | Real lot exit counts, curve fit |
| A4 | Compliance rate (default) | 0.85 (85% follow recommendations) | Typical tech adoption | MEDIUM | Ablation test: vary 0.5→1.0 (E6) |
| A5 | Non-compliant drivers go to nearest lot | Yes | Rational behavior model | MEDIUM | Failure case test (test_failure_cases.py) |
| A6 | Destination zone weights (no event) | 40% academic, 30% admin, 20% sports, 10% hostel | Estimated from campus map | LOW | Compare simulated vs real zone distribution (Phase 10) |

---

## B. PHYSICAL MODEL ASSUMPTIONS

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| B1 | Gate service rate | 6.0 vehicles/min per gate | Measured from traffic flow (assumed) | HIGH | Arrival time vs gate queue fit |
| B2 | Gate service time ~ Exponential | Mean = 1/6 min ≈ 10 sec | Standard queueing theory | MEDIUM | Not directly observable; structural assumption |
| B3 | BPR congestion model parameters | α=0.15, β=4.0 | Standard traffic engineering | HIGH | Road travel time vs flow rate calibration |
| B4 | Free speed (roads) | 20 kmph on-campus roads | Google Maps typical campus speed | MEDIUM | Measured from satellite view |
| B5 | Road capacity (roads) | 600 vehicles/hour typical | Typical 2-lane campus road | MEDIUM | Not directly observed; estimated |
| B6 | Base parking search time | 0.5 minutes | Typical empty lot search | LOW | Observed from video (requires permission) |
| B7 | Search time formula exponent | α=2.0 | Cruising behavior study | LOW | Real lot search videos |
| B8 | Reserved spaces respected | Yes (accessible + staff not available) | Legal requirement (ADA) | HIGH | Manual verification (all lots have reserves) |
| B9 | Reserved capacity sizes | Accessible: 4–6 per lot, Staff: 15–20 per lot | Campus parking policy | MEDIUM | Count from campus visit |

---

## C. TOPOLOGY ASSUMPTIONS

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| C1 | Campus graph nodes = gates + lots + junctions | 15 nodes (2 gates, 5 lots, 8 junctions) | VIT-AP map | HIGH | Audit against campus map (Sept 2026) |
| C2 | Road lengths measured from satellite | ±50m accuracy | Google Maps satellite | MEDIUM | Measured 8 roads; manual sampling |
| C3 | Road network is weakly connected | Yes (all lots reachable from all gates) | By design | HIGH | NetworkX connectivity check (test_part2_campus_graph.py) |
| C4 | Gates and lots are distinct node types | Yes | Model design | HIGH | Type checking in config loader |
| C5 | All lots have walk-time to academic | Yes, 2–9 minutes | Estimated from campus map | LOW | Observed during campus visit |

---

## D. SIMULATION ENGINE ASSUMPTIONS

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| D1 | Simulation is discrete-event, not fixed time-step | Yes (event queue with heapq) | Proposal §5 | HIGH | Engine structure (heapq-based) |
| D2 | One master seed → independent child streams | Yes (SeedSequence.spawn) | Proposal §5 | HIGH | test_part4_part5_simulation.py::test_determinism_hash |
| D3 | Same seed ⇒ identical demand across all strategies | Yes | Proposal §5 | HIGH | test_part4_part5_simulation.py::test_strategy_independent_demand |
| D4 | Decision cycle every 5 minutes | Yes | Proposal §4 (5-min cycle) | HIGH | engine.py line 157 (tick % 5 == 0) |
| D5 | Decision latency timeout = 1000ms | Yes | Proposal §9 | MEDIUM | StrategyAdapter.py timeout logic |
| D6 | Strategy fallback on timeout = B2 (NearestAvailable) | Yes | Proposal §9 | MEDIUM | adapter.py fallback implementation |
| D7 | No vehicle is processed twice per tick | Yes | Engine loop is serial | HIGH | Invariant: by_id dict, no duplicates |

---

## E. VALIDATION ASSUMPTIONS

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| E1 | Real observations collected 2–3 gates, 2–3 lots | Yes (planned) | Proposal §10 | HIGH | Campus access Sept–Oct 2026 |
| E2 | Real data aggregated at 15-min intervals | Yes | Proposal §10 (no privacy concerns) | HIGH | Data collection protocol |
| E3 | Simulated arrivals can be disaggregated to match real intervals | Yes (seeded thinning) | NHPP invertibility | HIGH | E7_replay scenario (test_e7_*.py) |
| E4 | Counterfactual results labeled "simulation-based estimates" | Yes | Proposal §14 (honesty rule) | HIGH | All E7 output files have disclaimer |

---

## F. SCALING & PERFORMANCE ASSUMPTIONS

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| F1 | Scalability target: 500 vehicles < 10 sec | Yes | Proposal §14 | MEDIUM | test_scalability.py::test_500_vehicles_performance |
| F2 | Scalability target: 1000 vehicles < 30 sec per seed | Yes | Proposal §14 | MEDIUM | test_scalability.py::test_1000_vehicles_performance |
| F3 | 30 seeds × 4 strategies × 7 scenarios is feasible | ~840 runs, ~40 CPU-hours total | Parallel multiprocessing | MEDIUM | Batch runner with pool.map |
| F4 | Decision latency p95 < 50ms (typical case) | ~15ms observed B2 | Proposal §9 | MEDIUM | Decision cycle timing test |

---

## G. CONFIGURATION & GENERALIZATION

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| G1 | New campus topology loads with zero code changes | Yes | Proposal §1 (generalization) | HIGH | test_part1_campus_config.py::test_synthetic_large_campus_loads |
| G2 | Campus YAML schema is fixed (no subtype changes) | Yes | Version 1.0 | MEDIUM | CampusConfigSchema pydantic model |
| G3 | Scenario YAML can reference any campus | Yes | ScenarioConfig.campus_id is a string | HIGH | E.g., E1_normal.yaml → sample.yaml OR vitap.yaml |
| G4 | Config validation never silently repairs errors | Yes (raise ConfigError on any issue) | Proposal §1 (honesty rule) | HIGH | test_part1_campus_config.py error cases |

---

## H. TEAM INTERFACES

| # | Assumption | Value | Source | Impact | Validation |
|---|---|---|---|---|---|
| H1 | Member 2 receives ML dataset with no data leakage | Yes (targets shifted forward, features from past only) | Proposal §9 | HIGH | test_phase9_interfaces.py::test_ml_dataset_schema |
| H2 | Member 3 receives StateSnapshot + fork capability | Yes (JSON serializable, deep copy) | Proposal §9 | HIGH | test_part3_twin_properties.py::test_snapshot_restore_fork |
| H3 | Member 4 receives pure Python functions (no DB coupling) | Yes (run_simulation returns SimulationResult dict) | Proposal §9 | HIGH | digital_twin/api_functions.py |
| H4 | All results are deterministically reproducible | Yes (seed-driven, no random global state) | Proposal §1 | HIGH | test_part4_part5_simulation.py::test_determinism_hash |

---

## SUMMARY: ASSUMPTION IMPACT DISTRIBUTION

- **HIGH impact (change result significantly):** A2, B1, B3, C1, C3, D1–D7, E1, E4, F1–F2, G1, H4
- **MEDIUM impact (affect secondary metrics):** A3, A4, B2, B6, C2, F3–F4
- **LOW impact (edge cases):** A6, B7, C5

**Total documented:** 45 assumptions  
**Validated by:** Config tests (13), simulation tests (30+), viva Q&A (all 12)  
**Calibration plan:** Phase 10 (Phase 10: October 26 - November 1)

---

## CHANGES REQUIRING GUIDE APPROVAL

If any of these change, consult guide:
1. Event multipliers (A2) — affects demand model accuracy
2. Gate service rate (B1) — affects queue depth validation
3. BPR parameters (B3) — affects travel time accuracy
4. Campus topology (C1) — requires new site survey
5. Decision cycle (D4) — changes optimization window
6. Compliance rate (A4) — affects adoption modeling

All others can be refined via calibration without model restructuring.

---

**See also:** 
- `twin_design.md` — entity model validation
- `simulation_model.md` — formula justification
- `calibration_report.md` — Phase 10 results (TBD)
- `viva.md` — Q&A on these assumptions
