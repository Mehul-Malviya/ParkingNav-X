"""CLI: python -m digital_twin.cli.validate_scenario --config <path>

Validates a scenario YAML without running a simulation, for quick iteration.
"""

import argparse
import sys

from digital_twin.db import get_connection
from digital_twin.simulation.scenario import ScenarioLoader, ScenarioValidator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--db", default=None)
    args = parser.parse_args()

    scenario = ScenarioLoader.load(args.config)
    conn = get_connection(args.db)
    errors = ScenarioValidator.validate(scenario, conn)

    if errors:
        print(f"Scenario '{scenario.scenario_id}' is INVALID:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"Scenario '{scenario.scenario_id}' is valid.")


if __name__ == "__main__":
    main()
