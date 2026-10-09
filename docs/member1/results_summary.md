# Results Summary — Member 1

**Generated:** 2026-10-09 09:46 UTC  
**Script:** `scripts/generate_results_summary.py`  
**Source:** `runs/{{scenario_id}}/{{strategy}}/seed_*/metrics.json`  
**Seeds:** 30 per scenario × strategy (seeds 0–29)  
**CI:** 95% (1.96 σ/√n)

---

## 5-Metric Table (mean ± 95%CI)

| Scenario | v | dur | St | search (min) | wait (min) | gq avg | gq max | overflow | travel_t (min) | travel_d (m) | rej |
|----------|---|-----|----|--------------|-----------:|-------:|-------:|---------:|---------------:|-------------:|----:|
| E1 normal_day | 400 | 600 | B1 | 2.50±0.01 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 1004±5 | 0.0 |
| E1 normal_day | 400 | 600 | B2 | 2.50±0.01 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 830±3 | 0.0 |
| E2 event_placement | 470 | 600 | B1 | 2.45±0.01 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 678±4 | 0.0 |
| E2 event_placement | 470 | 600 | B2 | 2.45±0.01 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 640±3 | 0.0 |
| E3 lot_closure | 400 | 600 | B1 | 2.45±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 741±11 | 0.0 |
| E3 lot_closure | 400 | 600 | B2 | 2.45±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 665±7 | 0.0 |
| E4 gate_closure | 400 | 600 | B1 | 2.45±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 741±11 | 0.0 |
| E4 gate_closure | 400 | 600 | B2 | 2.45±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 665±7 | 0.0 |
| E5 noise_0% | 400 | 600 | B1 | 2.44±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 751±15 | 0.0 |
| E5 noise_0% | 400 | 600 | B2 | 2.44±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 668±10 | 0.0 |
| E5 noise_10% | 400 | 600 | B1 | 2.44±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 751±15 | 0.0 |
| E5 noise_10% | 400 | 600 | B2 | 2.44±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 668±10 | 0.0 |
| E5 noise_20% | 400 | 600 | B1 | 2.44±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 751±15 | 0.0 |
| E5 noise_20% | 400 | 600 | B2 | 2.44±0.03 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 668±10 | 0.0 |
| gate_congestion | 400 | 180 | B1 | 6.44±0.23 | 0.24±0.05 | 0.27±0.05 | 7.27 | 74.5±4.7 | 2.04±0.03 | 843±10 | 0.0 |
| gate_congestion | 400 | 180 | B2 | 5.68±0.25 | 0.24±0.05 | 0.27±0.05 | 7.27 | 35.2±3.6 | 1.45±0.02 | 611±8 | 0.0 |
| high_traffic | 550 | 600 | B1 | 11.19±0.33 | 0.00±0.00 | 0.00±0.00 | 0.70 | 36.4±2.5 | 1.81±0.01 | 985±4 | 0.0 |
| high_traffic | 550 | 600 | B2 | 3.81±0.10 | 0.00±0.00 | 0.00±0.00 | 0.70 | 11.9±1.3 | 1.18±0.00 | 647±2 | 0.0 |
| road_closure | 400 | 600 | B1 | 5.17±0.32 | 0.00±0.00 | 0.00±0.00 | 0.37 | 4.3±1.2 | 1.96±0.01 | 1059±5 | 0.0 |
| road_closure | 400 | 600 | B2 | 2.90±0.18 | 0.00±0.00 | 0.00±0.00 | 0.37 | 3.1±0.7 | 1.13±0.00 | 620±3 | 0.0 |
| parking_full | 600 | 90 | B1 | 5.70±0.15 | 8.73±0.21 | 34.90±1.28 | 120.78 | 302.1±21.6 | 2.79±0.10 | 824±29 | 20.9 |
| parking_full | 600 | 90 | B2 | 5.84±0.16 | 8.73±0.22 | 34.94±1.32 | 121.03 | 227.7±17.1 | 2.35±0.08 | 693±24 | 18.7 |
| peak_hour | 350 | 120 | B1 | 5.01±0.16 | 0.10±0.02 | 0.15±0.03 | 3.97 | 79.2±5.5 | 2.13±0.03 | 747±11 | 0.0 |
| peak_hour | 350 | 120 | B2 | 4.66±0.19 | 0.10±0.02 | 0.15±0.03 | 3.97 | 34.3±3.2 | 1.48±0.02 | 522±8 | 0.0 |
| E7_replay (synthetic) | 350 | 600 | B1 | 2.50±0.01 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 1003±4 | 0.0 |
| E7_replay (synthetic) | 350 | 600 | B2 | 2.50±0.01 | 0.00±0.00 | 0.00±0.00 | 0.00 | 0.0±0.0 | — | 861±2 | 0.0 |

---

## Notes

**wait and gate-queue are identical for B1 and B2** in most scenarios because both strategies
only choose *which lot* to assign — they do not control *which gate* a vehicle uses.
Gate assignment is random (uniform over open gates). Wait time and gate queue are gate-level
metrics; they can only improve with gate guidance (Member 3's optimizer).

**gate_congestion, parking_full, peak_hour** are stress scenarios with non-standard durations
(180 min, 90 min, 120 min vs E1–E5's 600 min). Their search/travel numbers are not directly
comparable to E1–E5.

**road_closure** — inside vs outside closure window (ticks 60–180, 10-seed average):

| Strategy | In-window travel_d | Out-of-window travel_d | Δ |
|----------|-------------------|----------------------|---|
| B1 | 1273 m | 974 m | +299 m (+31%) |
| B2 | 682 m  | 594 m | +88 m  (+15%) |

B1 sends vehicles to academic-main (450 m) normally. During closure, it falls back to hostel
(380 m from gate but different route), admin (520 m), or sports (534 m). The mean detour is
+299 m. B2 was already routing to nearer lots (hostel / overflow), so the closure adds only
+88 m. Zero rejections in both cases — alternative paths cover all demand.

**E5 noise equivalence (confirmed):**
B1: noise_0%=6.6468  noise_10%=6.6468  noise_20%=6.6468 (bit-for-bit identical)
B2: noise_0%=3.2039  noise_10%=3.2039  noise_20%=3.2039
B1/B2 are reactive (no forecast); noise parameter has no effect. Results become meaningful
once Member 3's optimizer consumes the noisy forecast.

**E7_replay** results use synthetic observations (real counting day data pending Member 5).

---

*Regenerate with:* `python scripts/generate_results_summary.py`