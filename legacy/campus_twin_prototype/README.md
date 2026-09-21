# legacy/campus_twin_prototype/ (archived, not part of the active test suite)

An earlier, lighter Member 1 implementation — pure Python dataclasses,
no database or API — built before discovering this environment actually
has SQLite/FastAPI/networkx available. Superseded by `../../digital_twin/`
at the repo root, which has the real DB-backed, API-exposed
implementation. See
[../../docs/MEMBER1_SUBSYSTEM_REPORT.md](../../docs/MEMBER1_SUBSYSTEM_REPORT.md)
for why.

`dijkstra.py` and `parking_constraints.py` here are copies of the same
files in `../flat_optimizer/` — this prototype's `campus_twin/graph.py`
and `strategies.py` import them by bare name, and copying was simpler
than restructuring dead code.

Its own tests are self-contained and still pass. Run them from inside
this folder:

```bash
cd legacy/campus_twin_prototype
python -m pytest tests/ -v
```
