# Data provenance — VIT-AP dataset

This project cannot claim a real VIT-AP parking/traffic dataset exists,
because none is publicly available. This document says exactly what is
real and what isn't, field by field, instead of leaving that implicit.

## What was searched

- VIT-AP parking dataset / occupancy / CSV / JSON / GitHub / Kaggle / Zenodo /
  HuggingFace / ResearchGate — no public dataset found anywhere.
- "Real-Time Parking Spot Detection... 396 parking spots" (Ajith V. /
  Manimaran Aridoss, claimed VIT-AP affiliation) — **could not locate this
  paper** via search. Manimaran Aridoss is a real VIT-AP faculty member
  (School of Advanced Sciences), but no matching publication or dataset
  was found. Status: `NOT_FOUND` — not confirmed to exist as a public,
  discoverable paper.
- "An Intelligent Raspberry-Pi-Based Parking Slot Identification System"
  (Agarwal, Sharma, Singh, Nair, Daga, Venkata Lakshmi — VIT-AP SCOPE) —
  **real, published paper**
  ([EAI Endorsed Transactions](https://eudl.eu/doi/10.4108/eetinis.v10i4.4294)).
  No dataset, source code, or Firebase export is linked publicly.
  Status: `DISCOVERED`, not `ACCESSIBLE`.

## What was pulled in, and its real provenance

The 11 destination names and coordinates in
[`vitap_real_destinations.json`](vitap_real_destinations.json) (AB-1, AB-2,
CB, MH-1/2/3/6/7, LH-1, Food Street, MH-2 Food Store) are copied from
[Jyothireddy-pula/Parking_nav_](https://github.com/Jyothireddy-pula/Parking_nav_)'s
`configs/campuses/vitap.yaml`, which itself pulled them from public
OpenStreetMap via the Overpass API on 2026-09-13.

| Field | Provenance | Meaning |
|---|---|---|
| Destination names/coordinates | `EXTERNAL_MAP_REFERENCE` | Real VIT-AP locations from public OSM data. Not yet physically GPS-surveyed or satellite-corrected — treat coordinates as approximate. |
| Gate (`Gate1`), parking lot (`ParkingLot1`) | `SAMPLE` | Fabricated placeholders. VIT-AP's real gates and parking lots have not been surveyed or published anywhere the source repo or this search could find. |
| Road distances in `vitap_graph.json` | `SAMPLE` | Haversine straight-line distance between the gate/lot placeholder and each real destination — not a walked path. |
| Parking capacity/occupancy (`vitap_parking.json`) | `SYNTHETIC` | No real VIT-AP occupancy data exists publicly. Seeded, time-of-day-shaped values. |
| Congestion values (`vitap_predictions.json`) | `SYNTHETIC` | Same as above — no real source exists. |

**Consequence of only having one real gate/lot pair:** with a single
`ParkingLot1`, the optimizer has nothing to choose between — every route
resolves to the same lot. The routing/optimization/risk-scoring code all
still runs correctly end to end (verified), but the *choice* part of
"parking optimizer" isn't meaningfully exercised until either a second
real lot is surveyed, or additional `SAMPLE` lots are added back for demo
variety (clearly labeled as such, not as VIT-AP real).

## What would upgrade a field to `REAL`

Per the source repo's own methodology (`docs/DATA.md` there): a physical
GPS walk of VIT-AP's gates, parking lot perimeters, and roads, followed by
satellite-imagery correction. That fieldwork has not been done by either
repo as of this writing — `EXTERNAL_MAP_REFERENCE` is the ceiling for
anything derived from OSM alone.
