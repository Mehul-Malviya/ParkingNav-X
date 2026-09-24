# Stage 6-8 Development Roadmap
## Prediction → Risk → Optimization Pipeline

**Branch:** `feature/stage6-prediction-risk-optimization`  
**Start Date:** 2026-09-24  
**Target Duration:** 2 weeks (7-10 days of actual work)  
**Goal:** Move from 35% → 60% completion

---

## Phase Overview

This branch implements the **intelligence layer** of ParkingNav-X:

```
HISTORICAL DATA (✅ Done: 34,590 records)
        ↓
    STAGE 6: PREDICTION (← This branch)
        ↓
    STAGE 7: RISK CALCULATION
        ↓
    STAGE 8: OPTIMIZATION
        ↓
INTEGRATED SIMULATION (Stage 10 enhancement)
        ↓
METRICS & EXPERIMENTS (Stage 11-12)
```

---

## STAGE 6: PREDICTION PIPELINE

### Goal
Build ML models to predict occupancy, queue length, and congestion 15 minutes ahead with confidence intervals.

### File Structure
```
source/digital-twin/models/
├── __init__.py
├── prediction.py          ← CREATE (new)
├── prediction_features.py ← CREATE (new)
└── prediction_validation.py ← CREATE (new)
```

### Implementation Checklist

#### 6.1 Feature Engineering (1 day)
- [ ] Create `prediction_features.py`
- [ ] Extract temporal features
  - [ ] Hour of day (0-23)
  - [ ] Day of week (0-6)
  - [ ] Is weekend? (bool)
  - [ ] Academic calendar event? (bool)
  - [ ] Major event multiplier (0.05-1.50)
- [ ] Extract historical lags
  - [ ] t-1 occupancy (15 min ago)
  - [ ] t-2 occupancy (30 min ago)
  - [ ] t-4 occupancy (60 min ago)
  - [ ] t-96 occupancy (24 hours ago - same time yesterday)
- [ ] Handle missing values (forward fill for early days)
- [ ] Normalize features (0-1 scale)

**Test case:**
```python
from prediction_features import OccupancyFeatureExtractor
extractor = OccupancyFeatureExtractor('data/production/vitap_occupancy_data_complete_30days.csv')
features = extractor.extract(parking_lot_id='vitap-lot-1', timestamp='2026-09-15 14:30')
assert len(features) > 5  # At least 5 features
assert all(0 <= f <= 1 for f in features.values())
```

#### 6.2 Model Training (1.5 days)
- [ ] Create `prediction.py` with `OccupancyPredictor` class
- [ ] Load historical data from database
- [ ] Train/test split (70% / 30%, chronological)
- [ ] Train Random Forest model
  - [ ] n_estimators=100
  - [ ] max_depth=15
  - [ ] min_samples_split=5
- [ ] Train LSTM model (optional, for better accuracy)
  - [ ] Sequence length = 4 (60 minutes of history)
  - [ ] Hidden units = 64
  - [ ] Dropout = 0.2
- [ ] Store trained model in `database/models/`
- [ ] Evaluate on test set
  - [ ] MAE (mean absolute error)
  - [ ] RMSE (root mean squared error)
  - [ ] MAPE (mean absolute percentage error)
  - [ ] Directional accuracy (did we get trend right?)

**Test case:**
```python
from prediction import OccupancyPredictor
predictor = OccupancyPredictor()
predictor.train('digital_twin.db', parking_lot_id='vitap-lot-1')
predictions = predictor.predict(features_dict)
assert 0 <= predictions['occupancy'] <= 120  # Within capacity
assert 0 <= predictions['confidence'] <= 1
print(f"Predicted: {predictions['occupancy']} ± {predictions['std_dev']}")
```

#### 6.3 Prediction API Integration (0.5 days)
- [ ] Add method to `twin_service.py` to call predictor
- [ ] Implement prediction caching (cache for 5 minutes)
- [ ] Handle prediction failures gracefully (fallback to current occupancy)
- [ ] Store predictions in `prediction_history` table (new)

**Test case:**
```python
from digital_twin.twin_service import TwinService
service = TwinService('digital_twin.db')
pred = service.predict_occupancy('vitap-lot-1')
assert pred is not None
assert 'occupancy' in pred and 'confidence' in pred
```

#### 6.4 Validation & Testing (0.5 days)
- [ ] Create `tests/test_prediction.py`
- [ ] Test: predictions are within capacity bounds
- [ ] Test: confidence decreases with time horizon
- [ ] Test: predictions follow expected patterns (peak in evening, etc.)
- [ ] Test: model accuracy on full test set

---

## STAGE 7: RISK CALCULATION

### Goal
Calculate overflow risk, congestion risk, and wait time risk based on predictions.

### File Structure
```
source/digital-twin/models/
├── risk.py              ← CREATE (new)
└── risk_models.py       ← CREATE (new)
```

### Implementation Checklist

#### 7.1 Risk Functions (1 day)
- [ ] Create `risk.py` with risk calculators
- [ ] **Overflow Risk** (per parking lot)
  - [ ] P(occupancy > capacity) based on prediction distribution
  - [ ] Formula: `risk = (predicted_occupancy / capacity) ^ 2`
  - [ ] If confidence low: risk += 0.1 * (1 - confidence)
- [ ] **Congestion Risk** (per road)
  - [ ] P(travel_time > threshold)
  - [ ] Formula: `risk = 1 - e^(-congestion_level)`
  - [ ] Scale by vehicle count
- [ ] **Queue Risk** (per gate)
  - [ ] P(queue > threshold)
  - [ ] Formula: `risk = queue_length / gate_capacity`
- [ ] **Wait Time Risk** (combined)
  - [ ] Expected wait = queueing model(queue_length, capacity)

**Test case:**
```python
from risk import OverflowRisk, CongestionRisk
overflow = OverflowRisk()
risk = overflow.calculate(
    predicted_occupancy=95,
    capacity=100,
    confidence=0.85
)
assert 0 <= risk <= 1
assert risk > 0.5  # High risk when near capacity
```

#### 7.2 Risk Integration with Prediction (0.5 days)
- [ ] Link prediction confidence to risk bounds
- [ ] Use confidence intervals (e.g., 68%, 95%)
- [ ] Higher uncertainty → higher risk penalty
- [ ] Handle edge cases (all lots full, prediction unavailable)

#### 7.3 Event-Aware Risk (0.5 days)
- [ ] Check academic calendar for active events
- [ ] Check major events list
- [ ] Apply multipliers to risk
  - [ ] Placement drive: risk ×1.5 (more vehicles)
  - [ ] Exam period: risk ×0.6 (fewer vehicles)
  - [ ] Sports festival: risk ×1.3

#### 7.4 Testing (0.5 days)
- [ ] Create `tests/test_risk.py`
- [ ] Test: risk increases with occupancy
- [ ] Test: risk is zero when empty
- [ ] Test: event multipliers apply correctly
- [ ] Test: all risks in [0, 1] range

---

## STAGE 8: MULTI-OBJECTIVE OPTIMIZATION

### Goal
Implement ParkingNav-X strategy that balances distance, congestion, and overflow risk.

### File Structure
```
source/digital-twin/simulation/
├── demo_strategies.py    ← EXTEND (add ParkingNavXStrategy)
└── scoring.py            ← CREATE (new)
```

### Implementation Checklist

#### 8.1 Scoring Function (1 day)
- [ ] Create `scoring.py` with score calculation
- [ ] **Base Score Formula:**
  ```
  score = distance_score × w_distance
        + congestion_score × w_congestion
        + overflow_score × w_overflow
  
  where:
    w_distance = 0.3
    w_congestion = 0.3
    w_overflow = 0.4
  ```

- [ ] **Distance Score** (normalized 0-1)
  ```python
  max_distance = max distance from gate to any lot
  distance_score = (distance_to_lot / max_distance)
  ```

- [ ] **Congestion Score** (0-1)
  ```python
  congestion_score = congestion_risk_from_stage7
  ```

- [ ] **Overflow Score** (0-1)
  ```python
  overflow_score = overflow_risk_from_stage7
  ```

- [ ] Handle constraints
  - [ ] If lot full: score = infinity (exclude)
  - [ ] If gate closed: cannot use (exclude)
  - [ ] If road blocked: add penalty to distance
  - [ ] If prediction unavailable: use current occupancy

**Test case:**
```python
from scoring import ParkingNavXScorer
scorer = ParkingNavXScorer(w_dist=0.3, w_cong=0.3, w_over=0.4)
score = scorer.score(
    parking_lot_id='vitap-lot-1',
    distance=250,
    congestion_risk=0.3,
    overflow_risk=0.6,
    is_available=True
)
assert 0 <= score <= 2.0  # Valid range
```

#### 8.2 ParkingNavXStrategy Class (1 day)
- [ ] Create `ParkingNavXStrategy` in `demo_strategies.py`
- [ ] Implement `recommend()` method
  - [ ] Get all available parking lots
  - [ ] Get current occupancy & prediction
  - [ ] Calculate risk for each lot
  - [ ] Score each lot
  - [ ] Return lot with lowest score
  - [ ] Return confidence (based on score spread)
- [ ] Implement `evaluate()` for simulation
  - [ ] Track metrics per vehicle
  - [ ] Log scores for analysis

**Test case:**
```python
from demo_strategies import ParkingNavXStrategy
from digital_twin.models import Campus, Vehicle, Gate

campus = Campus.load('vitap')
vehicle = Vehicle(...)
entry_gate = campus.get_gate('vitap-gate-main')

strategy = ParkingNavXStrategy(campus)
recommendation = strategy.recommend(
    vehicle=vehicle,
    entry_gate=entry_gate,
    current_timestamp='2026-09-15 14:30'
)
assert recommendation['parking_lot_id'] in [lot.id for lot in campus.parking_lots]
assert 0 <= recommendation['score'] <= 2.0
```

#### 8.3 Tie-Breaking & Fallbacks (0.5 days)
- [ ] If multiple lots have same score (within ε=0.01)
  - [ ] Prefer nearest lot
  - [ ] Then prefer least congested road
  - [ ] Then prefer lowest overflow risk
- [ ] If all lots full
  - [ ] Return None with guidance to overflow parking
  - [ ] Suggest alternative times
- [ ] If all gates closed
  - [ ] Return None with error message

#### 8.4 Testing (1 day)
- [ ] Create `tests/test_optimization.py`
- [ ] Test: ParkingNavXStrategy scores correctly
- [ ] Test: all 5 scenarios run without error
- [ ] Test: tie-breaking works
- [ ] Test: constraints are enforced
- [ ] Test: handles edge cases (all full, all closed, etc.)
- [ ] Compare vs baselines (First Available, Nearest Available)

---

## Integration & Testing

### 9.1 End-to-End Integration (1 day)
- [ ] Update simulation engine to use predictions
  ```python
  # In engine.py, at each timestep:
  for lot in campus.parking_lots:
      prediction = predictor.predict(lot.id)
      lot.predicted_occupancy = prediction['occupancy']
      lot.prediction_confidence = prediction['confidence']
  ```

- [ ] Update strategy to use predictions
  ```python
  # In ParkingNavXStrategy.recommend():
  prediction = self.predictor.predict(lot.id)
  overflow_risk = calculator.overflow_risk(prediction, lot.capacity)
  ```

- [ ] Run simulation with ParkingNav-X
  ```bash
  python -m digital_twin.cli.run \
    --campus vitap \
    --scenario configs/scenarios/vitap/normal_day.yaml \
    --strategy digital_twin.simulation.demo_strategies.ParkingNavXStrategy
  ```

### 9.2 Baseline Comparison (1 day)
- [ ] Run simulation with all 3 strategies
  - [ ] First Available (naive)
  - [ ] Nearest Available (simple)
  - [ ] ParkingNav-X (optimized)
- [ ] Run on all 5 scenarios
  - [ ] normal_day.yaml
  - [ ] high_demand_event.yaml
  - [ ] parking_closure.yaml
  - [ ] gate_closure.yaml
  - [ ] road_closure.yaml
- [ ] Collect metrics:
  - [ ] Wait time per vehicle
  - [ ] Success rate (% that found parking)
  - [ ] Overflow frequency (% of time all lots full)
  - [ ] Congestion exposure (vehicle-hours in congestion)

### 9.3 Metrics Calculation (1 day)
- [ ] Create `automation/scripts/calculate_metrics.py`
- [ ] Read simulation output
- [ ] Calculate per-strategy metrics
- [ ] Generate comparison tables
- [ ] Create plots (wait time distribution, success rate, etc.)

---

## Milestones & Checkpoints

### Checkpoint 1: Feature Engineering (Day 2)
```
✓ prediction_features.py complete
✓ Tests passing
✓ Features extracted from 34,590 records
Status: Ready for model training
```

### Checkpoint 2: Prediction Model (Day 4)
```
✓ OccupancyPredictor training
✓ MAE < 10 spaces (5 lots × ~100-150 capacity)
✓ Confidence intervals working
Status: Ready for integration
```

### Checkpoint 3: Risk Calculation (Day 6)
```
✓ RiskCalculator complete
✓ Overflow/congestion/queue risks in [0,1]
✓ Event multipliers working
Status: Ready for optimization
```

### Checkpoint 4: ParkingNav-X Strategy (Day 8)
```
✓ ParkingNavXStrategy.recommend() working
✓ All 5 scenarios run successfully
✓ vs baselines: expect 10-20% wait time improvement
Status: Ready for production testing
```

### Checkpoint 5: Metrics & Comparison (Day 10)
```
✓ Baseline vs optimization comparison complete
✓ Result tables generated
✓ Plots created
Status: Ready for publication
```

---

## Success Criteria

### Must Have (to merge to main)
- [x] Prediction: MAE < 10 spaces on test set
- [x] Risk: All risks in [0,1], reasonable distributions
- [x] Optimization: Scores sensible, tie-breaking works
- [x] Integration: All 5 scenarios run without crashes
- [x] Comparison: Show >10% improvement on one metric
- [x] Tests: >90% code coverage, all passing

### Nice to Have
- [ ] LSTM model (more accurate than Random Forest)
- [ ] Hyperparameter tuning (GridSearchCV)
- [ ] Real-time prediction API endpoint
- [ ] Visualization dashboard
- [ ] Robustness to sensor failures

---

## File Checklist

### New Files to Create
- [ ] `source/digital-twin/models/__init__.py`
- [ ] `source/digital-twin/models/prediction.py`
- [ ] `source/digital-twin/models/prediction_features.py`
- [ ] `source/digital-twin/models/prediction_validation.py`
- [ ] `source/digital-twin/models/risk.py`
- [ ] `source/digital-twin/models/risk_models.py`
- [ ] `source/digital-twin/simulation/scoring.py`
- [ ] `tests/test_prediction.py`
- [ ] `tests/test_risk.py`
- [ ] `tests/test_optimization.py`
- [ ] `automation/scripts/calculate_metrics.py`
- [ ] `automation/scripts/run_comparison.py`

### Files to Modify
- [ ] `source/digital-twin/simulation/demo_strategies.py` (add ParkingNavXStrategy)
- [ ] `source/digital-twin/twin_service.py` (add predict_occupancy method)
- [ ] `source/digital-twin/simulation/engine.py` (integrate predictions)
- [ ] `database/migrations/0005_prediction_history.sql` (new table for predictions)

### Documentation to Create
- [ ] `documentation/architecture/PREDICTION_MODEL_REPORT.md`
- [ ] `documentation/architecture/RISK_CALCULATION_REPORT.md`
- [ ] `documentation/architecture/OPTIMIZATION_STRATEGY_REPORT.md`

---

## Deployment Checklist

Before merging to `main`:

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] No linting errors (`flake8 source/`)
- [ ] Code coverage >90%
- [ ] Comparison shows improvement vs baselines
- [ ] Documentation complete
- [ ] README updated with new features
- [ ] Branch reviewed and approved
- [ ] Conflicts resolved
- [ ] Commit messages clear and descriptive

---

## Next Phases (After This Branch)

### Phase 2: Metrics & Experiments (Branch: `feature/stage11-12-metrics`)
- Run systematic experiments
- Generate result tables
- Create publication plots
- Statistical significance testing

### Phase 3: Robustness & Ablation (Branch: `feature/stage13-robustness`)
- Ablation studies (which components matter?)
- Sensitivity analysis (parameter tuning)
- Failure case analysis
- Worst-case scenarios

### Phase 4: Real Validation (Long-term)
- Deploy to VIT-AP campus
- Collect real data
- Validate predictions
- Measure acceptance

### Phase 5: Publication (At the end)
- Write research paper
- Create submission-ready figures
- Prepare code/data for reproducibility

---

**Branch Status:** 🚀 Ready to start  
**Expected Completion:** 2026-10-01 (7-10 days)  
**Next Review:** 2026-09-30  

