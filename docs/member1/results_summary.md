# Results Summary — Member 1

**Generated:** 2026-10-10 18:37 UTC  
**Script:** `scripts/generate_results_summary.py`  
**Source:** `runs/{{scenario_id}}/{{strategy}}/seed_*/metrics.json`  
**Seeds:** 30 per scenario × strategy (seeds 0–29)  
**CI:** 95% (1.96 σ/√n)

---

## 5-Metric Table (mean ± 95%CI)

| Scenario | v | dur | St | search (min) | wait (min) | gq avg | gq max | overflow | travel_t (min) | travel_d (m) | rej |
|----------|---|-----|----|--------------|-----------:|-------:|-------:|---------:|---------------:|-------------:|----:|
| E1 normal_day | 400 | 600 | B1 | 3.88±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1009±5 | 0.0 |
| E1 normal_day | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 635±3 | 0.0 |
| E2 event_placement | 470 | 600 | B1 | 3.15±0.06 | 0.00±0.00 | 0.00±0.00 | 0.97 | 0.0±0.0 | 1.70±0.01 | 954±4 | 0.0 |
| E2 event_placement | 470 | 600 | B2 | 2.30±0.02 | 0.00±0.00 | 0.00±0.00 | 0.97 | 0.0±0.0 | 1.15±0.00 | 648±2 | 0.0 |
| E3 lot_closure | 400 | 600 | B1 | 2.81±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.76±0.01 | 970±5 | 0.0 |
| E3 lot_closure | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 635±3 | 0.0 |
| E4 gate_closure | 400 | 600 | B1 | 3.89±0.05 | 0.01±0.00 | 0.00±0.00 | 1.20 | 0.0±0.0 | 1.86±0.00 | 1039±5 | 0.0 |
| E4 gate_closure | 400 | 600 | B2 | 2.32±0.03 | 0.01±0.00 | 0.00±0.00 | 1.20 | 0.0±0.0 | 1.14±0.01 | 632±3 | 0.0 |
| E5 noise_0% | 400 | 600 | B1 | 3.88±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1009±5 | 0.0 |
| E5 noise_0% | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 635±3 | 0.0 |
| E5 noise_10% | 400 | 600 | B1 | 3.88±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1009±5 | 0.0 |
| E5 noise_10% | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 635±3 | 0.0 |
| E5 noise_20% | 400 | 600 | B1 | 3.88±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1009±5 | 0.0 |
| E5 noise_20% | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 635±3 | 0.0 |
| road_closure | 400 | 600 | B1 | 3.79±0.07 | 0.00±0.00 | 0.00±0.00 | 0.37 | 0.0±0.0 | 1.96±0.01 | 1059±5 | 0.0 |
| road_closure | 400 | 600 | B2 | 2.25±0.04 | 0.00±0.00 | 0.00±0.00 | 0.37 | 0.0±0.0 | 1.13±0.00 | 620±3 | 0.0 |
| parking_full | 600 | 90 | B1 | 2.33±0.02 | 8.72±0.23 | 34.78±1.32 | 120.47 | 21.6±5.2 | 2.79±0.10 | 822±30 | 21.6 |
| parking_full | 600 | 90 | B2 | 2.35±0.02 | 8.72±0.23 | 34.78±1.32 | 120.47 | 19.4±5.3 | 2.35±0.08 | 691±24 | 19.4 |
| E7_replay (synthetic) | 350 | 600 | B1 | 2.39±0.04 | 0.01±0.00 | 0.00±0.00 | 1.17 | 0.0±0.0 | 1.70±0.01 | 972±5 | 0.0 |
| E7_replay (synthetic) | 350 | 600 | B2 | 1.96±0.02 | 0.01±0.00 | 0.00±0.00 | 1.17 | 0.0±0.0 | 1.16±0.00 | 673±2 | 0.0 |

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