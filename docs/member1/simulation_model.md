# Simulation Model — Member 1

**Owner:** Jyothi Reddy Pula (23BCE7882) · VIT-AP · ParkingNav-X

---

## Engine Type

Discrete-time engine, 1 tick = 1 minute. Same seed → identical output (deterministic).

---

## Arrival Model — Non-Homogeneous Poisson Process (NHPP)

Rate varies with time of day:  
`λ(t)` = piecewise linear curve (morning peak, lunch, evening exit)

Event-aware rate:  
`λ_event(t) = λ(t) × demand_multiplier`  
(only zones affected by the event get extra demand)

**Thinning (Lewis–Shedler):** generate candidate arrivals at max rate λ_max, then accept each with probability `λ(t) / λ_max`. This gives a correct NHPP from a simple uniform sampler.

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
