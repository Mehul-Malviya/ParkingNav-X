# Assumptions — Member 1

**Owner:** Jyothi Reddy Pula (23BCE7882) · VIT-AP · ParkingNav-X

All numbers that are not directly measured are listed here with their source and impact.

---

| # | Assumption | Value | Source | Impact if Wrong | How Tested |
|---|-----------|-------|--------|----------------|------------|
| 1 | Gate service rate | 6 veh/min/lane | Estimated (observed gate ~10 sec/vehicle) | Queue length over/under estimated | Calibration vs real gate counts |
| 2 | Dwell time distribution | Lognormal, median 120 min | Estimated from class schedule (90-min slots) | Lot occupancy curve shape changes | Dwell distribution test |
| 3 | Driver compliance rate | 0.85 | Literature (0.70–0.92 range for guidance systems) | Overflow events change ±10% | E6 ablation |
| 4 | BPR parameters (0.15, β=4) | Standard values | Bureau of Public Roads standard | Travel time estimates off | Unit test at flow=0 and flow=capacity |
| 5 | Lot capacities (VIT-AP) | See vitap.yaml | Estimated from satellite imagery + campus map | Overflow timing shifts | Real observation calibration |
| 6 | Road free speeds | 20 km/h internal | Estimated (campus speed limit) | Travel times off ±15% | Calibration |
| 7 | Event demand multiplier (placement) | 1.8× | Assumed; placement drives bring external visitors | E2 results scale with this | Statistical verification test |
| 8 | Arrival profile shape | Piecewise linear, peak 8–10 AM | Observed informally; calibrated later | Arrival timing off | Arrival timing statistical test (multinomial sampling from rate profile) |
| 9 | Reserved spaces (accessible/staff) | See vitap.yaml | Campus policy estimate | Effective capacity slightly off | Config validator |
| 10 | Decision cycle period | 5 min | Design choice (balance responsiveness vs cost) | Faster = more accurate, slower = cheaper | Ablation (proactive flag) |
| 11 | Warm-down period | 30 min | Design choice: no new arrivals in last 30 min so in-transit vehicles reach terminal state | in_system metric inflated without warm-down | Re-measured at 10 s tick (E2, 30 seeds): in_system 0.26% with or without warm-down; warm-down removes the 5 mid-transit vehicles (36 -> all departing). Residual are departure-phase vehicles exiting campus |
| 12 | Gate service rate (main) | 6 veh/min (2 lanes × 3 veh/min/lane) | ASSUMED — no physical measurement available; 3 veh/min/lane ≈ 20 s/vehicle is typical for swipe/RFID gates | Gate queue and waiting_time_seconds scale with this; underestimating rate inflates queue length | Gate congestion scenario shows non-zero queue when arrival rate exceeds 6 veh/min |
| 13 | Gate service rate (visitor) | 3 veh/min (1 lane × 3 veh/min/lane) | ASSUMED — same basis as assumption 12; visitor gate is single-lane | Same impact as assumption 12 | Same |
| 14 | Sports lot driveable road | 534 m, 107 s from main gate | Estimated from satellite image (straight-line ~400 m, road factor ×1.33) | Sports lot always at 0% occupancy without this road | Fix 4: added vitap-road-main-gate-to-sports-lot; verified by graph-reachability test |
| 15 | Dwell time cap | [30, 480] min; median ~120 min (Lognormal μ=4.8, σ=0.6) | Code: `DWELL_MINUTES_RANGE=(30,480)`; median from lognormal params | **Limitation:** real event visitors may stay 6–10 h (concerts, sports); the 480-min hard cap means all event vehicles depart by tick 480 even if they arrived at tick 75. This drives the post-event lot recovery visible in E2. If extended dwell were modelled, academic-main would stay full longer and post-event search times would remain elevated. | Checked: no vehicle in 30-seed run has dwell > 480 min |
| 16 | Simulation tick | 10 s (spec default), set per scenario by `time_step_sec` (1–60, must divide 60) | Spec: tick = time_step_sec, default 10 s | Scenario YAML times (arrival profiles, timed closures, warm-down) stay in minutes and are converted by the engine. Logged `tick` fields and the per-minute `timesteps` stay in minutes (Member 2's frozen contract); traces additionally carry `t_sec`. Gate service accumulates `capacity x dt` credit per tick (6 veh/min = 1 vehicle per 10 s tick; 3 veh/min = 1 per 20 s). Sub-minute arrival time is spread evenly across a minute's ticks (no extra RNG draws). BPR flow is counted per simulated minute. | Runs take ~3.5 s (400 veh); `test_part5`-style tests that need every vehicle terminal must treat a departing vehicle as terminal |
| 17 | Parking search time | base 0.5 min + 5.5 min x occ^2 | Spec formula (k chosen so full lot = 6 min) | Search is analytic, added to metrics and to the trace PARKED tick; it is not simulated tick by tick | test_phase7_scenarios search-time growth test |
| 18 | Overflow event | Logged only when a vehicle is REJECTED_OVERFLOW | Spec: "no feasible lot -> overflow event++" | Reassignments after a lot fills mid-transit are tracked in reassigned_count, not as overflow | overflow_events_count == rejected on forced-closure run |
| 19 | Dwell time by event | Global lognormal (median ~120 min) unless `event_conditions.dwell_median_minutes` / `dwell_sigma` are set; then vehicles arriving inside the event window use them | Spec says dwell varies by vehicle type / event. No vehicle-type model exists and no event dwell values are calibrated, so no YAML sets the override yet (all results use the global distribution) | Event visitors probably stay longer; post-event lot recovery in E2 would be slower | `test_dwell_override.py` (override applies only inside the window, default unchanged) |

---

---

## `data/synthetic_observations.csv` — Changes Made

| Change | Detail | Why |
|--------|--------|-----|
| Lot ID remap: `vitap-lot-1` → `vitap-lot-academic-main` | Original placeholder IDs did not match vitap.yaml v2 parking_lot_ids | vitap.yaml was updated to descriptive IDs in v2; validate_observations.py checks against vitap.yaml, so old IDs failed validation |
| Lot ID remap: `vitap-lot-2` → `vitap-lot-sports` | Same reason as above | Same |
| Overflow rows capped at `total_capacity` (120) | Four rows in Day 1 had `occupied_spaces` of 122, 130, 127, 123 — exceeding `total_capacity=120` | validator check #4 rejects `occupied_spaces > total_capacity`; the original values were used to represent physical overflow (vehicles parked illegally/on grass); the `notes` column retains the original intent ("At capacity - overflow vehicles redirected") |

**All synthetic data is labelled "SYNTHETIC" in run manifests. Counterfactual results are labelled "simulation-based estimate."**

**`data/synthetic_observations.csv` is synthetic data generated to match realistic VIT-AP campus patterns (dates 15–16 Oct 2026 are future dates at time of writing). A real counting day using 15-minute aggregate gate counts is planned before final submission. Once collected, this file will be replaced and E7 re-run.**
