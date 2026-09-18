# Parking Nav X

Parking Nav X is a Python-based smart parking recommendation system.

It helps a driver choose the best parking area by considering:

- the shortest route from an entry gate;
- road congestion;
- parking occupancy;
- blocked roads;
- closed gates;
- parking availability.

The project currently uses mock JSON data. It is designed so real parking and traffic data can be connected later.

## Features

- Finds shortest routes using a custom Dijkstra algorithm.
- Re-routes when roads are blocked.
- Rejects unavailable or full parking areas.
- Rejects closed entry gates.
- Calculates congestion and parking-overflow risk.
- Scores parking options using distance, congestion, and overflow risk.
- Recommends the lowest-scoring parking option.
- Compares the optimizer against simpler baseline methods.
- Includes tests for each main component.

## Project structure

ParkingNav_X/
│
├── data/
│   └── mock/
│       ├── mock_graph.json
│       ├── mock_parking.json
│       └── mock_predictions.json
│
├── optimization/
│   ├── baselines/
│   │   ├── first_available.py
│   │   └── nearest_available.py
│   │
│   ├── constraints/
│   │   ├── gate_constraints.py
│   │   ├── parking_constraints.py
│   │   └── road_constraints.py
│   │
│   ├── evaluation/
│   │   ├── comparison.py
│   │   ├── metrics.py
│   │   └── robustness.py
│   │
│   ├── objectives/
│   │   ├── cost_function.py
│   │   └── weights.py
│   │
│   ├── optimizer/
│   │   └── parking_optimizer.py
│   │
│   ├── recommendation/
│   │   └── recommendation.py
│   │
│   ├── risk/
│   │   ├── congestion_risk.py
│   │   └── overflow_risk.py
│   │
│   └── routing/
│       ├── dijkstra.py
│       ├── rerouting.py
│       └── route_cost.py
│
├── tests/
│   └── optimization/
│       ├── test_baselines.py
│       ├── test_constraints.py
│       ├── test_dijkstra.py
│       ├── test_evaluation.py
│       ├── test_objective.py
│       ├── test_optimizer.py
│       ├── test_recommendation.py
│       ├── test_rerouting.py
│       ├── test_risk.py
│       └── test_route_cost.py
│
├── main.py
├── README.md
└── requirements.txt


## Mock data

### Campus graph

`data/mock/mock_graph.json` represents the campus road network.

Each location is a graph node, and each number is the travel cost between two connected locations.

Example:

"Gate1": {
  "RoadA": 2,
  "RoadB": 5
}

This means:

Gate1 → RoadA costs 2
Gate1 → RoadB costs 5

### Parking data

`data/mock/mock_parking.json` stores the capacity and occupied spaces for every parking area.

Example:

"ParkingB": {
  "capacity": 80,
  "occupied": 72
}

ParkingB is 90% full.

### Congestion predictions

`data/mock/mock_predictions.json` stores congestion-risk values between `0` and `1`.

"RoadD": 0.9

A value of `0.9` means RoadD has high congestion.

## How the recommendation works

1. The app starts from a gate, such as `Gate1`.
2. It checks whether that gate is open.
3. It ignores full parking areas.
4. It finds the shortest route to every available parking area.
5. It calculates route congestion risk.
6. It calculates parking overflow risk.
7. It combines those values into one total score.
8. It recommends the parking option with the lowest score.

The score is calculated as:

total score =
route cost × distance weight
+ congestion risk × congestion weight
+ overflow risk × overflow weight


Lower score means a better parking recommendation.

## Running the application in VS Code

1. Open the `ParkingNav_X` folder in VS Code.
2. Open `main.py`.
3. Click the normal ▶ Run button.

Expected output:

--- Parking Nav X ---
Recommended parking: ParkingA
Route: Gate1 → RoadA → RoadC → ParkingA
Route cost: 9
Overall score: 15.0


## Running tests in VS Code

Each test file can be run directly.

1. Open a file inside `tests/optimization/`.
2. Click the normal ▶ Run button.

For example:

test_dijkstra.py
test_optimizer.py
test_rerouting.py


A successful test prints a message such as:

Parking optimizer tests passed! ✅

## Technologies used

This project currently uses Python’s built-in modules:

- `json` for reading mock data;
- `pathlib` for locating project files;
- `sys` to allow direct test execution in VS Code.

The routing and optimization algorithms are implemented manually in Python. No external graph library, such as NetworkX, is currently required.

## Future improvements

Possible future upgrades include:

- real-time traffic and parking data;
- machine-learning-based congestion prediction;
- a web or mobile user interface;
- map visualization;
- GPS-based route input;
- live updates for blocked roads and full parking lots.

## Author

Parking Nav X project team.