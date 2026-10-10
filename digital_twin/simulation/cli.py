"""
CLI entry point for the Digital Twin simulation layer.

Usage:
    python -m digital_twin.simulation.cli run --campus vitap --scenario E1_normal_day --strategy nearest --seed 7
    python -m digital_twin.simulation.cli validate --campus vitap --scenario E1_normal_day
    python -m digital_twin.simulation.cli make-dataset --scenarios E1_normal_day,E2_event_placement --seeds 0-4 --output data/ml_dataset.csv

All subcommands are thin wrappers over digital_twin.api_functions — no new
simulation logic lives here.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from digital_twin.config_loader import (  # noqa: E402
    load_campus_config,
    load_campus_yaml,
    validate_campus_config,
)
from digital_twin.db import apply_migrations, get_connection  # noqa: E402
from digital_twin.simulation.engine import SimulationEngine  # noqa: E402
from digital_twin.simulation.scenario import ScenarioLoader, ScenarioValidator  # noqa: E402
from digital_twin.simulation.strategy import (  # noqa: E402
    FirstAvailableStrategy,
    NearestAvailableStrategy,
)

STRATEGY_MAP = {
    "first": FirstAvailableStrategy,
    "nearest": NearestAvailableStrategy,
}

CAMPUS_DIR = ROOT / "configs" / "campus"
SCENARIO_DIR = ROOT / "configs" / "scenarios"


def _resolve_campus_yaml(campus_id: str) -> Path:
    # support both configs/campus/ and configs/campuses/
    for d in [CAMPUS_DIR, ROOT / "configs" / "campuses"]:
        p = d / f"{campus_id}.yaml"
        if p.exists():
            return p
    raise FileNotFoundError(f"Campus config not found for '{campus_id}'. Looked in {CAMPUS_DIR}")


def _resolve_scenario_yaml(campus_id: str, scenario_id: str) -> Path:
    p = SCENARIO_DIR / campus_id / f"{scenario_id}.yaml"
    if p.exists():
        return p
    # fallback: any subdirectory
    for found in SCENARIO_DIR.rglob(f"{scenario_id}.yaml"):
        return found
    raise FileNotFoundError(f"Scenario '{scenario_id}' not found under {SCENARIO_DIR}")


def _parse_seeds(seeds_str: str) -> list[int]:
    """Parse '0-4' → [0,1,2,3,4] or '0,2,5' → [0,2,5]."""
    if "-" in seeds_str and "," not in seeds_str:
        start, end = seeds_str.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(s.strip()) for s in seeds_str.split(",")]


# ── subcommand: run ──────────────────────────────────────────────────────────

def cmd_run(args):
    campus_yaml = _resolve_campus_yaml(args.campus)
    scenario_yaml = _resolve_scenario_yaml(args.campus, args.scenario)

    strategy_key = args.strategy.lower()
    if strategy_key not in STRATEGY_MAP:
        print(f"Unknown strategy '{args.strategy}'. Choose from: {', '.join(STRATEGY_MAP)}")
        sys.exit(1)

    conn = get_connection(":memory:")
    apply_migrations(conn)
    load_campus_config(campus_yaml, conn)

    scenario = ScenarioLoader.load(scenario_yaml)
    scenario.random_seed = args.seed

    strategy = STRATEGY_MAP[strategy_key]()
    engine = SimulationEngine()
    result = engine.run(scenario, strategy, conn)

    print(json.dumps(result.metrics, indent=2))

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.metrics, indent=2))
        print(f"\nMetrics saved to {out}")


# ── subcommand: validate-campus ──────────────────────────────────────────────

def cmd_validate_campus(args):
    """Validate a campus YAML alone, print counts, and exit 0/1."""
    campus_yaml = _resolve_campus_yaml(args.campus)
    raw = load_campus_yaml(campus_yaml)

    # Reuse existing validation — no second path
    errors = validate_campus_config(raw)
    if errors:
        print(f"INVALID — campus '{args.campus}' failed validation:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    # Count entities from the raw YAML (works for both schema variants)
    gates       = raw.get("gates", []) or []
    lots        = raw.get("parking_lots", raw.get("lots", [])) or []
    roads       = raw.get("roads", []) or []
    edges       = raw.get("edges", []) or []
    destinations= raw.get("destinations", []) or []
    zones       = raw.get("zones", []) or []
    # Node count: gates + lots + destinations + junction nodes referenced in edges
    edge_nodes  = set()
    for e in edges:
        edge_nodes.add(e.get("from_node_id"))
        edge_nodes.add(e.get("to_node_id"))
    all_node_ids = (
        {g.get("gate_id") or g.get("id") for g in gates}
        | {p.get("parking_lot_id") or p.get("id") for p in lots}
        | {d.get("destination_id") or d.get("id") for d in destinations}
        | {z.get("id") for z in zones}
        | edge_nodes
    )
    all_node_ids.discard(None)

    campus_id = (raw.get("campus") or {}).get("campus_id") or (raw.get("campus") or {}).get("id")
    print(f"Campus valid — '{campus_id}'")
    print(f"  gates       : {len(gates)}")
    print(f"  lots        : {len(lots)}")
    print(f"  roads       : {len(roads)}")
    print(f"  nodes       : {len(all_node_ids)}")
    if destinations:
        print(f"  destinations: {len(destinations)}")
    if edges:
        print(f"  edges       : {len(edges)}")


# ── subcommand: validate ─────────────────────────────────────────────────────

def cmd_validate(args):
    campus_yaml = _resolve_campus_yaml(args.campus)
    scenario_yaml = _resolve_scenario_yaml(args.campus, args.scenario)

    conn = get_connection(":memory:")
    apply_migrations(conn)
    load_campus_config(campus_yaml, conn)

    scenario = ScenarioLoader.load(scenario_yaml)
    errors = ScenarioValidator.validate(scenario, conn)

    if errors:
        print("INVALID — errors found:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print(f"OK — scenario '{scenario.scenario_id}' is valid.")
        print(f"  campus_id        : {scenario.campus_id}")
        print(f"  duration_minutes : {scenario.duration_minutes}")
        print(f"  vehicle_count    : {scenario.vehicle_count}")
        print(f"  random_seed      : {scenario.random_seed}")
        print(f"  ablation flags   : use_prediction={scenario.use_prediction}, "
              f"use_optimization={scenario.use_optimization}, "
              f"use_uncertainty={scenario.use_uncertainty}, "
              f"proactive={scenario.proactive}")


# ── subcommand: make-dataset ─────────────────────────────────────────────────

def cmd_make_dataset(args):
    from digital_twin import api_functions

    campus_yaml = _resolve_campus_yaml(args.campus)
    conn = get_connection(":memory:")
    apply_migrations(conn)
    load_campus_config(campus_yaml, conn)

    # wire api_functions global state
    api_functions._conn = conn

    scenario_ids = [s.strip() for s in args.scenarios.split(",")]
    seeds = _parse_seeds(args.seeds)
    scenario_paths = [
        str(_resolve_scenario_yaml(args.campus, sid)) for sid in scenario_ids
    ]

    result = api_functions.make_dataset(
        campus_id=args.campus,
        scenario_paths=scenario_paths,
        seeds=seeds,
        output_path=args.output,
    )
    print(f"Dataset written: {result['rows']} rows × {len(result['columns'])} columns → {result['path']}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="python -m digital_twin.simulation.cli",
        description="ParkingNav-X Digital Twin CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Run one simulation and print metrics")
    p_run.add_argument("--campus",   required=True, help="Campus id (e.g. vitap)")
    p_run.add_argument("--scenario", required=True, help="Scenario id (e.g. E1_normal_day)")
    p_run.add_argument("--strategy", required=True, choices=list(STRATEGY_MAP), help="first | nearest")
    p_run.add_argument("--seed",     required=True, type=int, help="Random seed")
    p_run.add_argument("--output",   default=None,  help="Optional path to save metrics JSON")

    # validate-campus
    p_vc = sub.add_parser("validate-campus", help="Validate a campus YAML and print entity counts")
    p_vc.add_argument("--campus", required=True, help="Campus id (e.g. vitap, toy_small)")

    # validate
    p_val = sub.add_parser("validate", help="Validate a scenario YAML against a loaded campus")
    p_val.add_argument("--campus",   required=True)
    p_val.add_argument("--scenario", required=True)

    # make-dataset
    p_ds = sub.add_parser("make-dataset", help="Export ML training dataset (for Member 2)")
    p_ds.add_argument("--campus",    required=True)
    p_ds.add_argument("--scenarios", required=True, help="Comma-separated scenario ids")
    p_ds.add_argument("--seeds",     required=True, help="Seed range (e.g. 0-29) or list (0,1,5)")
    p_ds.add_argument("--output",    required=True, help="Output CSV path")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "validate-campus":
        cmd_validate_campus(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "make-dataset":
        cmd_make_dataset(args)


if __name__ == "__main__":
    main()
