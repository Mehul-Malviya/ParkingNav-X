# Simulation Model — Member 1

**Owner:** Jyothi Reddy Pula (23BCE7882) · VIT-AP · ParkingNav-X

---

## Engine Type

Discrete-time engine, 1 tick = 1 minute. Same seed → identical output (deterministic).

---

## Arrival Model — Time-Varying Demand (Multinomial Sampling)

Rate varies with time of day:  
`λ(t)` = piecewise linear curve (morning peak, lunch, evening exit)

Event-aware rate:  
`λ_event(t) = λ(t) × demand_multiplier`  
(only zones affected by the event get extra demand)

**What the code does:** a fixed expected total (`vehicle_count`) is derived from the profile integral (∫λ(t)dt scaled to target demand). Arrival times are then sampled from the time-varying rate profile using weighted multinomial sampling (`rng.choices(ticks, weights=weights, k=vehicle_count)`). The weight for each tick is the interpolated rate at that tick, optionally scaled by the event multiplier. This is equivalent to conditioning on the total and drawing arrival times from the normalized rate curve — it is NOT Lewis–Shedler thinning.

---

## Dwell Time — Lognormal Distribution

How long a vehicle stays parked:  
`dwell ~ Lognormal(μ=4.8, σ=0.6)` → median ≈ 120 min, capped [30, 480] min  
Justified: most vehicles park for one class period (~90–120 min); a few stay all day.

---

## Gate Queue — Multi-Server FIFO

- Lanes = servers; service rate = 6 vehicles/min per lane (measured estimate)
- Vehicles queue FIFO; wait time = service_start − arrival_time
- Closed gate → vehicles diverted to nearest open gate (extra travel logged)

---

## Road Travel Time — BPR Function

Bureau of Public Roads formula:  
`t = t_free × (1 + 0.15 × (flow / capacity)^4)`

- `t_free` = free-flow travel time (length / free_speed)
- `flow` = current vehicle count on road
- `capacity` = road capacity in vehicles/hr
- At flow = capacity: travel time is 1.15× free-flow
- Parameters 0.15 and 4 are BPR standard values (empirically validated in traffic literature)

Route = shortest path by current travel time via Dijkstra (NetworkX).

---

## Parking Search Time

`search_time = base × (1 + α / (1 − occupancy + ε))`

- `base` = lot-specific base search time (0.5 min default)
- Grows sharply as lot fills toward 100%
- If lot full on arrival → vehicle cruises to next lot (overflow event logged)

---

## Driver Compliance

`compliance_rate = 0.85` (default)  
15% of drivers ignore the recommendation and go to their nearest preferred lot.  
Models realistic human behaviour without requiring RL or agents.

---

## Warm-Down Period

Every scenario YAML includes `warmdown_minutes: 30`. During the last 30 minutes of simulation time, **no new vehicle arrivals are generated**. Vehicles that have already entered the system complete their dwell and departure normally.

**Why:** Without warm-down, vehicles arriving near the simulation end would still be in mid-transit (route/parking_search state) when the clock stops, inflating the `in_system_vehicles` metric artificially. The warm-down allows all in-transit vehicles to reach a terminal state before metrics are recorded.

**Effect measured (E2, 30 seeds):** in_system at end-of-sim dropped from ~2.45% to ~1.05%. The residual ~1% are vehicles in the *departure* phase — they have parked, completed their dwell, and are driving out of campus. These are not stalled vehicles; they are completing the journey. Their presence is bounded by the minimum travel-out time (~1–2 min) and cannot be eliminated without extending warmdown further.

---

## Forecast Noise (E5) — Plumbing Ready, Results Pending Member 3

`prediction_error_injection_level` (0.0 / 0.10 / 0.20) is accepted by `ScenarioConfig` and stored in the YAML. The `ForecastNoiseInjector` in `digital_twin/simulation/forecast_noise.py` applies Gaussian noise to forecasts when invoked.

**Current status:** The engine passes `forecast=None` to `strategy.update_policy()`. Neither B1 (FirstAvailableStrategy) nor B2 (NearestAvailableStrategy) reads forecast data. As a result, E5_noise_0, E5_noise_10, and E5_noise_20 produce **identical B1/B2 results** — the noise parameter has no effect on the baselines.

**When E5 becomes meaningful:** once Member 3's optimizer reads `use_prediction` and consumes the noisy forecast, E5 will measure robustness degradation as noise increases. B1/B2 are noise-immune by construction (reactive, no forecast dependency), which is itself a useful baseline for comparison.

**Confirmed:** 30-seed run with seed override shows B1 search = 0.705 min and B2 search = 0.658 min for all three noise levels, bit-for-bit identical.

---

## Parameters Summary

| Parameter | Value | Source |
|-----------|-------|--------|
| Service rate (gate) | 6 veh/min/lane | Estimated |
| BPR α | 0.15 | Standard BPR |
| BPR β | 4 | Standard BPR |
| Dwell μ (lognormal) | 4.8 | Calibrated from observations |
| Dwell σ (lognormal) | 0.6 | Calibrated from observations |
| Compliance rate | 0.85 | Assumption (literature range 0.7–0.9) |
| Decision cycle | 5 min | Design choice |
| Warm-down | 30 min | Design choice (see section above) |
