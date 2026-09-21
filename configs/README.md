# configs/

- **`campuses/*.yaml`** — one file per campus: gates, roads, parking
  lots, destinations, events, graph edges. Loaded via
  `python scripts/load_campus_config.py --config configs/campuses/<id>.yaml`.
  `sample.yaml` is fully fabricated (`SAMPLE`) for development;
  `vitap.yaml`'s destination names/coordinates are real (pulled from
  public OpenStreetMap — see `../docs/PROVENANCE.md`), everything else
  in it is `SAMPLE` pending a physical survey.

- **`scenarios/<campus_id>/*.yaml`** — simulation scenarios for that
  campus. Validate without running: `python -m digital_twin.cli.validate_scenario --config <path>`.
  Every scenario here is `SYNTHETIC`.
