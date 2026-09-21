"""
Generates a synthetic-but-realistic parking/routing dataset for VIT-AP
University (Amaravati, Andhra Pradesh), matching the existing mock data
schema (mock_graph.json, mock_parking.json, mock_predictions.json).

What's real: entry gate names, block/hostel/food-court names, and the rough
relative layout of the campus (main gate near the front plaza, hostels and
academic blocks further in, food court central).

What's simulated: exact edge distances, parking capacities, occupancy, and
congestion values. No public live feed of VIT-AP parking/traffic exists, so
these are generated with a fixed random seed following believable patterns
(higher congestion near academic blocks/food court at class-change and lunch
hours; higher occupancy near the main gate and academic blocks) rather than
uniform noise. Swap this generator for a real sensor feed later without
changing the rest of the app, since the output schema is identical to the
existing mock files.

Usage:
    python generate_vitap_dataset.py [--time morning|midday|evening] [--seed N]
"""

import argparse
import json
import random
from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent

# Real, publicly-known VIT-AP landmarks used as node names.
GATES = ["MainGate", "Gate2", "Gate3"]

ROADS = [
    "RoadPlaza",        # Main Gate -> central plaza
    "RoadAcademic1",    # plaza -> Academic Block 1
    "RoadAcademic2",    # plaza -> Academic Block 2
    "RoadHostelZone",   # plaza -> Men's/Ladies hostel cluster
    "RoadFoodCourt",    # plaza -> food court
    "RoadSports",       # Gate2/Gate3 -> sports complex
]

PARKING_LOTS = [
    "ParkingMainGate",
    "ParkingAcademic1",
    "ParkingAcademic2",
    "ParkingHostelZone",
    "ParkingFoodCourt",
    "ParkingSports",
]

TIME_PROFILES = {
    # label: (base_occupancy_factor, congestion_hotspots)
    "morning": (0.55, {"RoadAcademic1": 0.85, "RoadAcademic2": 0.8, "RoadPlaza": 0.6}),
    "midday": (0.8, {"RoadFoodCourt": 0.9, "RoadPlaza": 0.7, "RoadAcademic1": 0.5}),
    "evening": (0.4, {"RoadSports": 0.6, "RoadHostelZone": 0.55, "RoadPlaza": 0.35}),
}


def build_graph():
    """Fixed campus topology: gates -> plaza road -> destination roads -> parking."""
    graph = {
        "MainGate": {"RoadPlaza": 120},
        "Gate2": {"RoadSports": 90, "RoadPlaza": 260},
        "Gate3": {"RoadSports": 70, "RoadHostelZone": 300},
        "RoadPlaza": {
            "MainGate": 120,
            "Gate2": 260,
            "RoadAcademic1": 180,
            "RoadAcademic2": 210,
            "RoadHostelZone": 340,
            "RoadFoodCourt": 150,
        },
        "RoadAcademic1": {
            "RoadPlaza": 180,
            "ParkingAcademic1": 60,
            "RoadFoodCourt": 130,
        },
        "RoadAcademic2": {
            "RoadPlaza": 210,
            "ParkingAcademic2": 70,
            "RoadFoodCourt": 160,
        },
        "RoadHostelZone": {
            "RoadPlaza": 340,
            "Gate3": 300,
            "ParkingHostelZone": 90,
        },
        "RoadFoodCourt": {
            "RoadPlaza": 150,
            "RoadAcademic1": 130,
            "RoadAcademic2": 160,
            "ParkingFoodCourt": 50,
        },
        "RoadSports": {
            "Gate2": 90,
            "Gate3": 70,
            "ParkingSports": 80,
        },
        "ParkingMainGate": {"MainGate": 40},
        "ParkingAcademic1": {"RoadAcademic1": 60},
        "ParkingAcademic2": {"RoadAcademic2": 70},
        "ParkingHostelZone": {"RoadHostelZone": 90},
        "ParkingFoodCourt": {"RoadFoodCourt": 50},
        "ParkingSports": {"RoadSports": 80},
    }
    # MainGate also has a short direct parking spur, mirroring real campuses
    # where a small visitor lot sits right at the entrance.
    graph["MainGate"]["ParkingMainGate"] = 40
    return graph


def build_parking(rng, base_occupancy_factor):
    capacities = {
        "ParkingMainGate": 60,
        "ParkingAcademic1": 220,
        "ParkingAcademic2": 200,
        "ParkingHostelZone": 150,
        "ParkingFoodCourt": 90,
        "ParkingSports": 70,
    }
    parking = {}
    for lot, capacity in capacities.items():
        noise = rng.uniform(-0.1, 0.1)
        factor = min(max(base_occupancy_factor + noise, 0.05), 0.98)
        parking[lot] = {
            "capacity": capacity,
            "occupied": round(capacity * factor),
        }
    return parking


def build_predictions(rng, hotspots):
    predictions = {}
    for road in ROADS:
        base = hotspots.get(road, 0.3)
        noise = rng.uniform(-0.07, 0.07)
        predictions[road] = round(min(max(base + noise, 0.05), 0.95), 2)
    return predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", choices=TIME_PROFILES.keys(), default="midday")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    base_occupancy_factor, hotspots = TIME_PROFILES[args.time]

    graph = build_graph()
    parking = build_parking(rng, base_occupancy_factor)
    predictions = build_predictions(rng, hotspots)

    outputs = {
        "vitap_graph.json": graph,
        "vitap_parking.json": parking,
        "vitap_predictions.json": predictions,
    }

    for filename, data in outputs.items():
        path = PROJECT_FOLDER / filename
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        print(f"Wrote {path.name}")

    print(f"\nGenerated with time profile '{args.time}', seed {args.seed}.")


if __name__ == "__main__":
    main()
