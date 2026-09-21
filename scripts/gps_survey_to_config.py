"""CLI: python scripts/gps_survey_to_config.py --gpx survey.gpx --waypoints waypoints.csv
    --campus-id vitap --campus-name "VIT-AP University" [--timezone Asia/Kolkata]
    [--configuration-version V1] --output configs/campuses/vitap.generated.yaml

Converts a GPX survey + waypoint mapping CSV into a campus YAML config.
Road geometry comes directly from the walked GPX track, in original point
order -- never straightened or reordered.
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from digital_twin.gps_survey_import import gps_survey_to_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpx", required=True)
    parser.add_argument("--waypoints", required=True)
    parser.add_argument("--campus-id", required=True)
    parser.add_argument("--campus-name", required=True)
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--configuration-version", default="V1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    config = gps_survey_to_config(
        args.gpx, args.waypoints, campus_id=args.campus_id, campus_name=args.campus_name,
        timezone=args.timezone, configuration_version=args.configuration_version,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    print(f"Wrote {output_path} ({len(config['roads'])} roads, "
          f"{len(config['gates']) + len(config['parking_lots']) + len(config['destinations'])} point entities)")


if __name__ == "__main__":
    main()
