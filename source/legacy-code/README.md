# Archived / superseded code

Both folders here are kept for reference, not active development. Neither
is part of the current test suite run from the repo root
(`python -m pytest tests/`).

## `flat_optimizer/`

The original ParkingNav-X algorithmic core (Dijkstra + risk/cost scoring +
baselines). As inherited, its modules import from an `optimization.*`
package path that was never actually present in this flat checkout
(`from optimization.constraints.gate_constraints import is_gate_open`,
etc.) — that mismatch predates this reorganization and is unrelated to the
file move; it's a pre-existing issue in the code as received.

## `campus_twin_prototype/`

An earlier, lighter Member 1 implementation (pure Python dataclasses, no
database or API) built before discovering that this environment actually
has SQLite/FastAPI/networkx available. Superseded by `digital_twin/` at
the repo root, which has the real DB-backed, API-exposed implementation.
See `docs/MEMBER1_SUBSYSTEM_REPORT.md` for why.

Its tests (`tests/`) run against its own `data/campus_configs/` and its
own `campus_twin/` package, both local to this folder — run them from
inside `legacy/campus_twin_prototype/` if you need to, e.g.:

```bash
cd legacy/campus_twin_prototype
python -m pytest tests/ -v
```

## `data/vitap_dataset_prototype/` (at the repo root's `data/`, not under `legacy/`)

An early synthetic VIT-AP dataset generator built for the flat optimizer,
before the `digital_twin/` subsystem's `configs/campuses/vitap.yaml`
became the real, current VIT-AP config. Kept for its documented
provenance research (see `docs/PROVENANCE.md`), not for active use.
