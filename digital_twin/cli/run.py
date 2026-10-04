"""
CLI: python -m digital_twin.cli.run --campus <campus_id> --scenario <path> --strategy <module.ClassName> [--seed N]

Writes experiments/runs/{run_id}/vehicles.parquet and timesteps.parquet.
"""

import argparse
import importlib
from pathlib import Path

import pandas as pd

from digital_twin.db import init_db
from digital_twin.simulation.engine import SimulationEngine
from digital_twin.simulation.scenario import ScenarioLoader, ScenarioValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = PROJECT_ROOT / "experiments" / "runs"


def _import_strategy(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    strategy_class = getattr(module, class_name)
    return strategy_class()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campus", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--strategy", required=True, help="module.ClassName, e.g. digital_twin.simulation.strategy.FixedLotStrategy")
    parser.add_argument("--seed", type=int, default=None, help="Override the scenario's random_seed")
    parser.add_argument("--db", default=None)
    args = parser.parse_args()

    scenario = ScenarioLoader.load(args.scenario)
    if scenario.campus_id != args.campus:
        raise SystemExit(f"Scenario campus_id '{scenario.campus_id}' does not match --campus '{args.campus}'.")
    if args.seed is not None:
        scenario.random_seed = args.seed

    conn = init_db(args.db)
    errors = ScenarioValidator.validate(scenario, conn)
    if errors:
        raise SystemExit("Scenario invalid:\n" + "\n".join(f"- {e}" for e in errors))

    strategy = _import_strategy(args.strategy)
    engine = SimulationEngine()
    result = engine.run(scenario, strategy, conn)

    run_dir = RUNS_DIR / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(result.vehicles).to_parquet(run_dir / "vehicles.parquet", index=False)
    pd.DataFrame(result.timesteps).to_parquet(run_dir / "timesteps.parquet", index=False)

    print(f"Run '{result.run_id}' complete. Output: {run_dir}")


if __name__ == "__main__":
    main()
