# legacy/flat_optimizer/ (archived, not part of the active test suite)

The original ParkingNav-X algorithmic core (Dijkstra routing + risk/cost
scoring + baseline comparisons), as received. Its modules import from an
`optimization.*` package path that was never actually present in this
flat checkout (`from optimization.constraints.gate_constraints import
is_gate_open`, etc.) — that mismatch predates this repo's reorganization
and is a pre-existing issue in the code as received, not something the
move caused.

`main.py` also reads its mock data from `data/mock/...`, but the actual
files live in `data/` directly (one level shallower) — same kind of
pre-existing path mismatch.

Its own tests are in `tests/`, run from inside this folder if needed —
they hit the same import issue.

See the top-level [README.md](../../README.md) for what this project
looked like originally, and
[../../docs/MEMBER1_SUBSYSTEM_REPORT.md](../../docs/MEMBER1_SUBSYSTEM_REPORT.md)
for the current, active system that superseded this.
