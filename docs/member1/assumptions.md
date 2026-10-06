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
| 8 | Arrival profile shape | Piecewise linear, peak 8–10 AM | Observed informally; calibrated later | Arrival timing off | NHPP statistical test |
| 9 | Reserved spaces (accessible/staff) | See vitap.yaml | Campus policy estimate | Effective capacity slightly off | Config validator |
| 10 | Decision cycle period | 5 min | Design choice (balance responsiveness vs cost) | Faster = more accurate, slower = cheaper | Ablation (proactive flag) |

---

**All synthetic data is labelled "SYNTHETIC" in run manifests. Counterfactual results are labelled "simulation-based estimate."**
