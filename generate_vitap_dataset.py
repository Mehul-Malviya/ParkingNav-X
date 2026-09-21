"""
Generates the VIT-AP dataset (mock_graph.json / mock_parking.json /
mock_predictions.json schema) from vitap_real_destinations.json.

Provenance, spelled out plainly:

- Destination NAMES and COORDINATES (AB-1, AB-2, CB, MH-1..MH-7, LH-1,
  Food Street, MH-2 Food Store) are REAL VIT-AP locations, pulled from
  Jyothireddy-pula/Parking_nav_'s configs/campuses/vitap.yaml, which itself
  sourced them from public OpenStreetMap via the Overpass API on 2026-09-13.
  Provenance: EXTERNAL_MAP_REFERENCE (real-world names/coordinates, not yet
  physically GPS-surveyed or satellite-corrected).
- The GATE and PARKING LOT are fabricated placeholders (one of each), same
  as the source repo — VIT-AP's real gates and lots have not been surveyed
  publicly anywhere. Provenance: SAMPLE.
- ROAD DISTANCES are computed with the haversine formula on the real
  destination coordinates (straight-line, not a walked path) at a fixed
  walking speed, exactly the method the source repo documents for its own
  SAMPLE roads. Provenance: SAMPLE (a straight line is not a real path).
- PARKING CAPACITY/OCCUPANCY and CONGESTION values have no real VIT-AP
  source at all (none exists publicly - confirmed by search). They are
  seeded synthetic values with time-of-day shape, same as before.
  Provenance: SYNTHETIC.

No field in this dataset is claimed as REAL or VALIDATED. Only the
destination identity/location layer is EXTERNAL_MAP_REFERENCE; everything
connecting those points is SAMPLE or SYNTHETIC. See PROVENANCE.md.

Usage:
    python generate_vitap_dataset.py [--time morning|midday|evening] [--seed N]
"""

import argparse
import json
import math
import random
from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent
WALKING_SPEED_M_S = 1.3  # matches the source repo's haversine walking-speed assumption

TIME_PROFILES = {
    # label: (base_occupancy_factor, congestion_hotspot_categories)
    "morning": (0.55, {"academic_block": 0.85, "administrative_building": 0.6}),
    "midday": (0.8, {"cafeteria": 0.9, "academic_block": 0.5}),
    "evening": (0.4, {"hostel": 0.6, "cafeteria": 0.5}),
}


def load_real_destinations():
    path = PROJECT_FOLDER / "vitap_real_destinations.json"
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def haversine_meters(lat1, lng1, lat2, lng2):
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def build_graph(data):
    gate = data["gate_placeholder"]
    lot = data["parking_lot_placeholder"]
    destinations = data["destinations"]

    gate_node = "Gate1"
    lot_node = "ParkingLot1"

    # The source repo's gate and lot placeholders are ~275m apart at VIT-AP;
    # kept as a fixed short link since both are non-real placeholder points.
    graph = {
        gate_node: {lot_node: 275},
        lot_node: {gate_node: 275},
    }

    for dest in destinations:
        node = dest["name"]
        distance = round(haversine_meters(gate["lat"], gate["lng"], dest["lat"], dest["lng"]))
        graph[lot_node][node] = distance
        graph[node] = {lot_node: distance}

    return graph


def build_parking(rng, base_occupancy_factor, data):
    lot = data["parking_lot_placeholder"]
    capacity = lot["usable_capacity"]
    noise = rng.uniform(-0.1, 0.1)
    factor = min(max(base_occupancy_factor + noise, 0.05), 0.98)
    return {
        "ParkingLot1": {
            "capacity": capacity,
            "occupied": round(capacity * factor),
        }
    }


def build_predictions(rng, hotspots, data):
    predictions = {}
    for dest in data["destinations"]:
        base = hotspots.get(dest["category"], 0.3)
        noise = rng.uniform(-0.07, 0.07)
        predictions[dest["name"]] = round(min(max(base + noise, 0.05), 0.95), 2)
    return predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", choices=TIME_PROFILES.keys(), default="midday")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    base_occupancy_factor, hotspots = TIME_PROFILES[args.time]

    data = load_real_destinations()
    graph = build_graph(data)
    parking = build_parking(rng, base_occupancy_factor, data)
    predictions = build_predictions(rng, hotspots, data)

    outputs = {
        "vitap_graph.json": graph,
        "vitap_parking.json": parking,
        "vitap_predictions.json": predictions,
    }

    for filename, output_data in outputs.items():
        path = PROJECT_FOLDER / filename
        with open(path, "w", encoding="utf-8") as file:
            json.dump(output_data, file, indent=2)
        print(f"Wrote {path.name}")

    print(f"\nGenerated with time profile '{args.time}', seed {args.seed}.")
    print("Destination names/coordinates: EXTERNAL_MAP_REFERENCE (real OSM data).")
    print("Gate/lot/roads: SAMPLE. Capacity/occupancy/congestion: SYNTHETIC.")


if __name__ == "__main__":
    main()
