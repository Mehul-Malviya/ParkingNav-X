# Calibration Report — Real vs Simulated (Phase 10)
**Author:** Jyothi Reddy Pula | **Date:** 5 October 2026  
**Status:** Framework ready; calibration data TBD (Phase 10: Oct 26-Nov 1)

---

## EXECUTIVE SUMMARY

This report compares simulated occupancy curves (from Twin + Simulator) against real campus observations to answer: **"How closely does our simulation match reality?"**

**Planned outcome:** MAE < 5% on occupancy forecast = well-calibrated Twin

---

## 1. REAL DATA COLLECTION PROTOCOL

### **What We'll Observe (Oct 26 - Nov 1)**

**Duration:** 2 days minimum (1 normal day + 1 event day)
**Sample:** Gates G1, G2; Lots LA, LB, LC  
**Resolution:** 15-min intervals (aggregate counts, no personal data)

**CSV Template:**
```
timestamp,gate_id,vehicle_count,parking_lot_id,occupied_spaces,event_type,event_intensity,observer,confidence
2026-10-26 08:00:00,G1,42,LA,85,none,0,observer1,0.95
2026-10-26 08:15:00,G1,38,LA,82,none,0,observer1,0.90
...
2026-10-27 09:00:00,G1,120,LA,119,placement,1.8,observer2,0.92
```

**Data Quality:**
- Confidence score (0.80–1.00): only include ≥0.80
- Missing intervals: logged, not interpolated
- Observer names for validation

### **Data Cleaning & Validation**

```python
def validate_observations(df):
    errors = []
    
    # Check: occupancy ≤ capacity
    for _, row in df.iterrows():
        if row['occupied_spaces'] > lot_capacities[row['parking_lot_id']]:
            errors.append(f"Row {_}: occupancy > capacity")
    
    # Check: non-negative counts
    if (df['vehicle_count'] < 0).any() or (df['occupied_spaces'] < 0).any():
        errors.append("Negative counts found")
    
    # Check: monotonicity (occupancy changes by < 100/interval)
    # Check: timestamp order
    # Check: confidence ≥ 0.80
    
    return errors, df[df['confidence'] >= 0.80]
```

---

## 2. CALIBRATION PROCEDURE

### **Step 1: Estimate Base Arrival Rate λ(t)**

From gate observations, estimate vehicles/min per time interval:

```python
# Real observation: 42 vehicles in 15 min at G1
λ_G1(08:00-08:15) = 42 / 15 = 2.8 vehicles/min

# Fit to piecewise linear model
λ_fitted(t) = f(t; params)  # Minimize MSE
```

**Fitted arrival profile:**
```yaml
arrival_rate_profile:
  type: profile
  points:
    - time: 480    # 8:00 AM (measured from data)
      rate: X.X
    - time: 510    # 8:30 AM
      rate: X.X
    # ... fitted from real observations
```

### **Step 2: Estimate Dwell Parameters**

From occupancy → inflow/outflow, estimate dwell distribution:

```python
# Observation: occupancy rises 08:00-09:30, drops 09:30-11:00
# Implies: average dwell ≈ 90-120 minutes

# Fit: LogNormal(μ=X.X, σ=X.X)
# Use curve_fit from scipy.optimize
```

---

## 3. SIMULATION RUN

**With fitted parameters:**
```python
scenario_calibration = ScenarioConfig(
    campus_id='vitap',
    scenario_id='calibration_normal_day',
    duration_minutes=480,
    vehicle_count=1200,  # from observed aggregate
    arrival_rate_profile=λ_fitted,  # fitted above
    random_seed=42,  # reproducible
)

# Run 5 times with different seeds (42-46)
results = []
for seed in [42, 43, 44, 45, 46]:
    scenario_calibration.random_seed = seed
    result = engine.run(scenario_calibration, strategy=B2)
    results.append(result)

# Average across 5 runs
simulated_occupancy = mean([r.occupancy_timeline for r in results])
```

---

## 4. VALIDATION METRICS

### **Primary: Mean Absolute Error (MAE)**

```
MAE = mean(|simulated[t] - observed[t]|) / capacity
```

**Interpretation:**
- MAE < 0.05 (< 5% of capacity): ✅ **Well-calibrated**
- 0.05 ≤ MAE < 0.10: ⚠️ **Acceptable (minor differences)**
- MAE ≥ 0.10: ❌ **Needs adjustment**

### **Secondary: Root Mean Squared Error (RMSE)**

```
RMSE = sqrt(mean((simulated[t] - observed[t])²)) / capacity
```

Penalizes large deviations more than MAE.

### **Tertiary: Peak Timing Error**

```
peak_observed_time = argmax(observed_curve)
peak_simulated_time = argmax(simulated_curve)
timing_error_min = |peak_observed_time - peak_simulated_time|
```

**Interpretation:**
- < 15 min: ✅ Good peak timing
- 15–30 min: ⚠️ Acceptable
- > 30 min: ❌ Arrival or dwell model needs revision

---

## 5. RESULTS (TBD — Phase 10)

### **Normal Day (Expected)**

| Metric | Target | Simulated | Observed | MAE | Status |
|---|---|---|---|---|---|
| Lot A max occupancy | 120 | TBD | TBD | TBD | ? |
| Lot B max occupancy | 100 | TBD | TBD | TBD | ? |
| Lot C max occupancy | 80 | TBD | TBD | TBD | ? |
| Peak timing (Lot A) | 09:30 | TBD | TBD | TBD | ? |
| Average occupancy | TBD | TBD | TBD | TBD | ? |

**Visualization: (plot generated after Phase 10)**
```
Occupancy vs Time (Normal Day, Lot A)

100 |                    ___
    |                  /     \
 80 |  ___     ___    /       \_
    |     \   /   \  /
 60 |      \_/     \/
    |
 40 |
    |___________________________
    8:00   10:00   12:00   14:00
    
    — = Observed
    --- = Simulated (mean of 5 seeds)
    
MAE = X.X%, RMSE = X.X%, Peak timing error = ±X min
```

### **Event Day (Placement, Expected)**

| Metric | Target | Simulated | Observed | MAE | Status |
|---|---|---|---|---|---|
| Demand multiplier (observed) | 1.8× | TBD | TBD | TBD | ? |
| Lot A peak occupancy | ~150+ | TBD | TBD | TBD | ? |
| Overflow events | > 0 | TBD | TBD | TBD | ? |

---

## 6. ANALYSIS & HONEST ASSESSMENT

### **Where Simulation Agrees**

(To be filled after Phase 10)

- ✅ Timing of peak occupancy
- ✅ Magnitude of demand
- ✅ Rate of flow through gates
- *etc.*

### **Where Simulation Disagrees & Why**

(To be filled after Phase 10)

**Hypothesis A: Dwell Time Overestimated**
- If simulated occupancy stays high longer than observed
- → Adjust LogNormal(μ, σ) downward
- → Re-run validation

**Hypothesis B: Arrival Rate Underestimated**
- If simulated peak is lower than observed
- → Check gate count observations (may be wrong)
- → Calibrate λ(t) from lot inflow instead

**Hypothesis C: Search Time Underestimated**
- If simulated vehicles park faster than observed
- → Increase base_search_time in simulation_model.md
- → Re-calibrate

---

## 7. ADJUSTMENTS & RE-RUNS

If MAE > 5%, iterative refinement:

```
1. Identify parameter that most affects discrepancy
2. Adjust by ±10–20%
3. Re-run simulation with adjusted param
4. Measure MAE again
5. Repeat until MAE < 5%

Maximum 3 iterations (time constraint)
```

### **Refinement Log**

| Iteration | Parameter Changed | Old Value | New Value | MAE | Status |
|---|---|---|---|---|---|
| 0 | (baseline) | — | — | TBD | ? |
| 1 | dwell μ | 2.0 | TBD | TBD | ? |
| 2 | arrival_rate[peak] | 12.0 | TBD | TBD | ? |
| Final | — | — | — | TBD | ✓ |

---

## 8. COUNTERFACTUAL REPLAY (E7)

Once Twin is calibrated:

```python
# Run observed arrivals through Twin with two strategies
observed_arrivals = disaggregate(real_gate_counts, seed_stream)

# Baseline: B2 (Nearest Available)
result_b2 = run_simulation(
    scenario='E7_replay',
    arrivals=observed_arrivals,
    strategy=B2,
)

# Optimized: Member 3's algorithm (once ready)
result_p = run_simulation(
    scenario='E7_replay',
    arrivals=observed_arrivals,
    strategy=ParkingNavX,
)

# Compare
comparison = {
    'b2_search_time': result_b2.metrics['avg_search_time_min'],
    'p_search_time': result_p.metrics['avg_search_time_min'],
    'improvement_%': (1 - result_p/result_b2) * 100,
    'caveat': 'simulation-based estimate; not actual intervention result',
}
```

---

## 9. HONESTY & LIMITATIONS

### **What This Calibration Proves**
✅ Twin **matches observed patterns**  
✅ Arrival model is **realistically parameterized**  
✅ Dwell time distribution is **empirically grounded**

### **What It Does NOT Prove**
❌ Twin will **perfectly predict** new scenarios  
❌ Member 3's optimizer will **improve real system** (only estimated)  
❌ Simulation is **correct** for all edge cases  

### **Caveats (Always Stated)**

All E7 results (counterfactual replay) are labeled:
```
"These are simulation-based estimates of what ParkingNav-X 
 might achieve. They are NOT results from a real deployment. 
 Actual field performance may differ due to: (a) user behavior 
 variations, (b) external factors (weather, accidents), 
 (c) infrastructure constraints not modeled."
```

---

## 10. REFERENCE

- **Calibration date:** Oct 26 - Nov 1, 2026
- **Observers:** [names TBD]
- **Real data file:** `data/real_observations_cleaned.csv`
- **Fitted parameters file:** `configs/campuses/vitap_calibrated.yaml`
- **Simulation runs:** `runs/E7_replay/{B2,ParkingNavX}/seed_{0-29}/`

---

**Status:** Framework complete  
**Next:** Conduct real observations and calibration (W15: Oct 19-25)  
**Final:** Report complete by W16 (Oct 26-Nov 1)
