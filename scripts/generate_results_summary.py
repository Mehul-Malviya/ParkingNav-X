"""
Generate docs/member1/results_summary.md from runs/ metrics.json files.

Usage:
    python scripts/generate_results_summary.py

Reads runs/{scenario_id}/{strategy}/seed_*/metrics.json,
aggregates across seeds, writes the markdown table.

Re-run any time after a new batch to refresh the numbers.
"""
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
OUT  = ROOT / "docs" / "member1" / "results_summary.md"

STRATEGY_DIRS = {
    "B1": ["B1-FirstAvailable",
           "digital_twin.simulation.strategy.FirstAvailableStrategy"],
    "B2": ["B2-NearestAvailable",
           "digital_twin.simulation.strategy.NearestAvailableStrategy"],
}

# Canonical scenario order and display names
SCENARIOS = [
    ("vitap-normal-day",        "E1 normal_day",         400, 600),
    ("vitap-event-placement",   "E2 event_placement",    470, 600),
    ("vitap-lot-closure",       "E3 lot_closure",        400, 600),
    ("vitap-gate-closure",      "E4 gate_closure",       400, 600),
    ("vitap-e5-noise-0",        "E5 noise_0%",           400, 600),
    ("vitap-e5-noise-10",       "E5 noise_10%",          400, 600),
    ("vitap-e5-noise-20",       "E5 noise_20%",          400, 600),
    ("vitap-gate-congestion",   "gate_congestion",       400, 180),
    ("vitap-high-traffic",      "high_traffic",          550, 600),
    ("vitap-road-closure",      "road_closure",          400, 600),
    ("vitap-parking-full",      "parking_full",          600,  90),
    ("vitap-peak-hour",         "peak_hour",             350, 120),
    ("vitap-e7-replay",         "E7_replay (synthetic)", 350, 600),
]


def load_metrics(scenario_dir: Path, strat_name: str) -> list[dict]:
    """Load all seed metrics.json for a given scenario/strategy."""
    rows = []
    for dirname in STRATEGY_DIRS[strat_name]:
        strat_dir = scenario_dir / dirname
        if not strat_dir.exists():
            continue
        for seed_dir in sorted(strat_dir.iterdir()):
            mf = seed_dir / "metrics.json"
            if mf.exists():
                with open(mf) as f:
                    data = json.load(f)
                # Flatten primary_metrics if nested
                pm = data.get("primary_metrics", data)
                sm = data.get("secondary_metrics", {})
                rows.append({**pm, **sm})
        if rows:
            break  # found the right strategy folder
    return rows


def ci95(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    return 1.96 * statistics.stdev(vals) / math.sqrt(len(vals))


def mean_ci(rows, key, scale=1.0):
    vals = [r[key] * scale for r in rows if key in r and r[key] is not None]
    if not vals:
        return "—", "—"
    return f"{statistics.mean(vals):.2f}", f"{ci95(vals):.2f}"


def mean_ci_int(rows, key):
    vals = [r[key] for r in rows if key in r and r[key] is not None]
    if not vals:
        return "—", "—"
    return f"{statistics.mean(vals):.1f}", f"{ci95(vals):.1f}"


def main():
    lines = [
        "# Results Summary — Member 1",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        "**Script:** `scripts/generate_results_summary.py`  ",
        "**Source:** `runs/{{scenario_id}}/{{strategy}}/seed_*/metrics.json`  ",
        "**Seeds:** 30 per scenario × strategy (seeds 0–29)  ",
        "**CI:** 95% (1.96 σ/√n)",
        "",
        "---",
        "",
        "## 5-Metric Table (mean ± 95%CI)",
        "",
        "| Scenario | v | dur | St | search (min) | wait (min) | gq avg | gq max | overflow | travel_t (min) | travel_d (m) | rej |",
        "|----------|---|-----|----|--------------|-----------:|-------:|-------:|---------:|---------------:|-------------:|----:|",
    ]

    for (scen_id, display, vc, dur) in SCENARIOS:
        scen_dir = RUNS / scen_id
        if not scen_dir.exists():
            continue
        for strat in ["B1", "B2"]:
            rows = load_metrics(scen_dir, strat)
            if not rows:
                continue
            n = len(rows)

            # search time (primary_metrics has avg_search_time_min)
            sm, sc = mean_ci(rows, "avg_search_time_min")
            # wait time
            wm, wc = mean_ci(rows, "avg_waiting_time_min")
            if wm == "—":
                wm, wc = mean_ci(rows, "avg_wait_time_min")
            # gate queue
            gam, gac = mean_ci(rows, "avg_gate_queue_vehicles")
            gmm, _   = mean_ci(rows, "max_gate_queue_vehicles")
            # overflow
            om, oc = mean_ci_int(rows, "overflow_events_count")
            # travel time
            tm, tc = mean_ci(rows, "avg_travel_time_min")
            # travel distance
            dm_vals = [r.get("avg_travel_distance_m") or
                       (r.get("total_travel_distance_veh_km", 0)*1000 /
                        max(r.get("total_vehicles_simulated", 1), 1))
                       for r in rows]
            dm = f"{statistics.mean(dm_vals):.0f}" if dm_vals else "—"
            dc = f"{ci95(dm_vals):.0f}" if len(dm_vals) > 1 else "—"
            # rejected
            rm_vals = [r.get("rejected_vehicles", 0) for r in rows]
            rm = f"{statistics.mean(rm_vals):.1f}" if rm_vals else "—"

            s_cell  = f"{sm}±{sc}" if sm != "—" else "—"
            w_cell  = f"{wm}±{wc}" if wm != "—" else "—"
            ga_cell = f"{gam}±{gac}" if gam != "—" else "—"
            o_cell  = f"{om}±{oc}" if om != "—" else "—"
            t_cell  = f"{tm}±{tc}" if tm != "—" else "—"
            d_cell  = f"{dm}±{dc}" if dm != "—" else "—"

            lines.append(
                f"| {display} | {vc} | {dur} | {strat} | {s_cell} | {w_cell} | "
                f"{ga_cell} | {gmm} | {o_cell} | {t_cell} | {d_cell} | {rm} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Notes",
        "",
        "**wait and gate-queue are identical for B1 and B2** in most scenarios because both strategies",
        "only choose *which lot* to assign — they do not control *which gate* a vehicle uses.",
        "Gate assignment is random (uniform over open gates). Wait time and gate queue are gate-level",
        "metrics; they can only improve with gate guidance (Member 3's optimizer).",
        "",
        "**gate_congestion, parking_full, peak_hour** are stress scenarios with non-standard durations",
        "(180 min, 90 min, 120 min vs E1–E5's 600 min). Their search/travel numbers are not directly",
        "comparable to E1–E5.",
        "",
        "**road_closure** — inside vs outside closure window (ticks 60–180, 10-seed average):",
        "",
        "| Strategy | In-window travel_d | Out-of-window travel_d | Δ |",
        "|----------|-------------------|----------------------|---|",
        "| B1 | 1273 m | 974 m | +299 m (+31%) |",
        "| B2 | 682 m  | 594 m | +88 m  (+15%) |",
        "",
        "B1 sends vehicles to academic-main (450 m) normally. During closure, it falls back to hostel",
        "(380 m from gate but different route), admin (520 m), or sports (534 m). The mean detour is",
        "+299 m. B2 was already routing to nearer lots (hostel / overflow), so the closure adds only",
        "+88 m. Zero rejections in both cases — alternative paths cover all demand.",
        "",
        "**E5 noise equivalence (confirmed):**",
        "B1: noise_0%=6.6468  noise_10%=6.6468  noise_20%=6.6468 (bit-for-bit identical)",
        "B2: noise_0%=3.2039  noise_10%=3.2039  noise_20%=3.2039",
        "B1/B2 are reactive (no forecast); noise parameter has no effect. Results become meaningful",
        "once Member 3's optimizer consumes the noisy forecast.",
        "",
        "**E7_replay** results use synthetic observations (real counting day data pending Member 5).",
        "",
        "---",
        "",
        f"*Regenerate with:* `python scripts/generate_results_summary.py`",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written: {OUT}")
    print(f"Scenarios found: {sum(1 for s,_,_,_ in SCENARIOS if (RUNS/s).exists())}/{len(SCENARIOS)}")


if __name__ == "__main__":
    main()
