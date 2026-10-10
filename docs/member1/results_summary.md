# Results Summary — Member 1

**Generated:** 2026-10-10 19:58 UTC  
**Script:** `scripts/generate_results_summary.py`  
**Source:** `runs/{{scenario_id}}/{{strategy}}/seed_*/metrics.json`  
**Seeds:** 30 per scenario × strategy (seeds 0–29)  
**CI:** 95% (1.96 σ/√n)

---

## 5-Metric Table (mean ± 95%CI)

| Scenario | v | dur | St | search (min) | wait (min) | gq avg | gq max | overflow | travel_t (min) | travel_d (m) | rej |
|----------|---|-----|----|--------------|-----------:|-------:|-------:|---------:|---------------:|-------------:|----:|
| E1 normal_day | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E1 normal_day | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E1 normal_day | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E1 normal_day | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| E2 event_placement | 470 | 600 | B1 | 3.15±0.06 | 0.00±0.00 | 0.00±0.00 | 0.97 | 0.0±0.0 | 1.71±0.01 | 956±4 | 0.0 |
| E2 event_placement | 470 | 600 | B2 | 2.31±0.02 | 0.00±0.00 | 0.00±0.00 | 0.97 | 0.0±0.0 | 1.17±0.00 | 653±2 | 0.0 |
| E2 event_placement | 470 | 600 | B3 | 1.50±0.03 | 0.00±0.00 | 0.00±0.00 | 0.97 | 0.0±0.0 | 1.18±0.00 | 668±3 | 0.0 |
| E2 event_placement | 470 | 600 | B4 | 1.21±0.01 | 0.00±0.00 | 0.00±0.00 | 0.97 | 0.0±0.0 | 1.58±0.01 | 900±4 | 0.0 |
| E3 lot_closure | 400 | 600 | B1 | 2.81±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.76±0.01 | 971±5 | 0.0 |
| E3 lot_closure | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E3 lot_closure | 400 | 600 | B3 | 1.25±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.16±0.00 | 655±3 | 0.0 |
| E3 lot_closure | 400 | 600 | B4 | 1.18±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 930±5 | 0.0 |
| E4 gate_closure | 400 | 600 | B1 | 3.90±0.05 | 0.01±0.00 | 0.00±0.00 | 1.20 | 0.0±0.0 | 1.86±0.01 | 1041±5 | 0.0 |
| E4 gate_closure | 400 | 600 | B2 | 2.33±0.03 | 0.01±0.00 | 0.00±0.00 | 1.20 | 0.0±0.0 | 1.15±0.01 | 635±3 | 0.0 |
| E4 gate_closure | 400 | 600 | B3 | 1.49±0.03 | 0.01±0.00 | 0.00±0.00 | 1.20 | 0.0±0.0 | 1.15±0.00 | 645±2 | 0.0 |
| E4 gate_closure | 400 | 600 | B4 | 1.09±0.01 | 0.01±0.00 | 0.00±0.00 | 1.20 | 0.0±0.0 | 1.54±0.01 | 864±5 | 0.0 |
| E5 noise_0% | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E5 noise_0% | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E5 noise_0% | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E5 noise_0% | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| E5 noise_10% | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E5 noise_10% | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E5 noise_10% | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E5 noise_10% | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| E5 noise_20% | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E5 noise_20% | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E5 noise_20% | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E5 noise_20% | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| road_closure | 400 | 600 | B1 | 3.80±0.07 | 0.00±0.00 | 0.00±0.00 | 0.40 | 0.0±0.0 | 1.97±0.01 | 1062±5 | 0.0 |
| road_closure | 400 | 600 | B2 | 2.26±0.04 | 0.00±0.00 | 0.00±0.00 | 0.40 | 0.0±0.0 | 1.13±0.00 | 622±3 | 0.0 |
| road_closure | 400 | 600 | B3 | 1.20±0.02 | 0.00±0.00 | 0.00±0.00 | 0.40 | 0.0±0.0 | 1.16±0.00 | 642±3 | 0.0 |
| road_closure | 400 | 600 | B4 | 1.15±0.01 | 0.00±0.00 | 0.00±0.00 | 0.40 | 0.0±0.0 | 1.65±0.01 | 910±5 | 0.0 |
| parking_full | 600 | 90 | B1 | 2.36±0.02 | 8.80±0.23 | 34.87±1.32 | 120.53 | 22.2±4.6 | 2.74±0.11 | 818±33 | 22.2 |
| parking_full | 600 | 90 | B2 | 2.38±0.02 | 8.80±0.23 | 34.87±1.32 | 120.53 | 20.6±4.5 | 2.23±0.08 | 664±25 | 20.6 |
| parking_full | 600 | 90 | B3 | 2.35±0.02 | 8.80±0.23 | 34.87±1.32 | 120.53 | 16.3±4.7 | 2.08±0.06 | 626±18 | 16.3 |
| parking_full | 600 | 90 | B4 | 2.34±0.02 | 8.80±0.23 | 34.87±1.32 | 120.53 | 16.1±4.5 | 2.38±0.11 | 722±34 | 16.1 |
| E7_replay (synthetic) | 350 | 600 | B1 | 2.40±0.04 | 0.01±0.00 | 0.00±0.00 | 1.23 | 0.0±0.0 | 1.70±0.01 | 973±5 | 0.0 |
| E7_replay (synthetic) | 350 | 600 | B2 | 1.97±0.03 | 0.01±0.00 | 0.00±0.00 | 1.23 | 0.0±0.0 | 1.17±0.00 | 676±2 | 0.0 |
| E7_replay (synthetic) | 350 | 600 | B3 | 1.42±0.02 | 0.01±0.00 | 0.00±0.00 | 1.23 | 0.0±0.0 | 1.19±0.00 | 694±3 | 0.0 |
| E7_replay (synthetic) | 350 | 600 | B4 | 1.18±0.01 | 0.01±0.00 | 0.00±0.00 | 1.23 | 0.0±0.0 | 1.59±0.01 | 926±6 | 0.0 |
| E6 ablation_A | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E6 ablation_A | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E6 ablation_A | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E6 ablation_A | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| E6 ablation_B | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E6 ablation_B | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E6 ablation_B | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E6 ablation_B | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| E6 ablation_C | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E6 ablation_C | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E6 ablation_C | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E6 ablation_C | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |
| E6 ablation_D | 400 | 600 | B1 | 3.90±0.05 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.81±0.01 | 1010±5 | 0.0 |
| E6 ablation_D | 400 | 600 | B2 | 2.27±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.14±0.00 | 636±3 | 0.0 |
| E6 ablation_D | 400 | 600 | B3 | 1.23±0.03 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.17±0.00 | 657±3 | 0.0 |
| E6 ablation_D | 400 | 600 | B4 | 1.13±0.01 | 0.00±0.00 | 0.00±0.00 | 0.50 | 0.0±0.0 | 1.65±0.01 | 928±5 | 0.0 |

---

## Notes

**wait and gate-queue are identical for B1 and B2** in most scenarios because both strategies
only choose *which lot* to assign — they do not control *which gate* a vehicle uses.
Gate assignment is random (uniform over open gates). Wait time and gate queue are gate-level
metrics; they can only improve with gate guidance (Member 3's optimizer).

**parking_full** is a stress scenario with a non-standard duration (90 min vs 600 min for
E1-E5, E7, road_closure). Its search/travel numbers are not directly comparable to the others;
it is the only scenario with real rejections (overflow = rejected).

**B3 / B4 are demo stand-ins** (`demo_strategies.py`: PredictionOnly, ParkingNavXFull) that run
with no real forecast yet; their numbers show the harness works, not Member 3's final results.

**E6 ablation A-D match E1 exactly** for every strategy: the ablation flags (use_prediction,
use_optimization, ...) are stored in the scenario but are not read by the engine or by any current
strategy, so they take effect only once Member 3's strategies consume them.

**road_closure** - travel distance for vehicles arriving inside vs outside the closure
window (ticks 60-180), seeds 0-29:

| Strategy | In-window travel_d | Out-of-window travel_d | Delta |
|----------|-------------------|----------------------|-------|
| B1 | 1267 m | 978 m | +290 m (+30%) |
| B2 | 685 m | 596 m | +89 m (+15%) |
| B3 | 692 m | 621 m | +71 m (+11%) |
| B4 | 993 m | 877 m | +116 m (+13%) |

Rejections stay at 0 because alternative paths cover all demand.

**E5 noise equivalence (computed):**
B1: noise_0%=3.8957  noise_10%=3.8957  noise_20%=3.8957 (identical)
B2: noise_0%=2.2740  noise_10%=2.2740  noise_20%=2.2740 (identical)
B3: noise_0%=1.2343  noise_10%=1.2343  noise_20%=1.2343 (identical)
B4: noise_0%=1.1343  noise_10%=1.1343  noise_20%=1.1343 (identical)
Current strategies are reactive (no forecast), so the noise parameter has no effect. Results
become meaningful once Member 3's optimizer consumes the noisy forecast.

**E7_replay** results use synthetic observations (real counting day data pending Member 5).

---

*Regenerate with:* `python scripts/generate_results_summary.py`