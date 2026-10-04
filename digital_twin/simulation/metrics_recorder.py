"""
Phase 8 — Metrics Recorder

Records raw per-vehicle and per-interval logs; computes 5 primary metrics from logs.

Output per run: runs/{scenario_id}/{strategy}/seed_{n}/
  - vehicles.parquet: per-vehicle metrics
  - intervals.parquet: per-timestep metrics
  - state_timeline.parquet: campus state snapshots
  - decisions.jsonl: decision events with latency
  - metrics.json: 5 primary + secondary metrics
  - manifest.json: config hash, git commit, timestamps, versions
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import hashlib

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class MetricsRecorder:
    """Record simulation results with structured outputs."""

    def __init__(self, output_root: str = "runs"):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    def record_run(self, scenario_id: str, strategy_name: str, seed: int,
                   vehicle_metrics: list, timestep_metrics: list,
                   overflow_events: list, config_dict: dict,
                   decision_latencies: list = None,
                   git_commit: Optional[str] = None,
                   manifest_extra: dict = None) -> Path:
        """
        Record a single simulation run.

        Args:
            scenario_id: scenario identifier
            strategy_name: strategy class name
            seed: random seed
            vehicle_metrics: list of per-vehicle dicts
            timestep_metrics: list of per-timestep dicts
            overflow_events: list of overflow events
            config_dict: campus config for hashing
            decision_latencies: list of {tick, latency_ms}
            git_commit: git commit hash (auto-detected if None)
            manifest_extra: extra fields for manifest

        Returns:
            Path to output directory
        """
        # Create run directory
        run_dir = self.output_root / scenario_id / strategy_name / f"seed_{seed}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Write vehicle metrics (parquet)
        if HAS_PANDAS and vehicle_metrics:
            df_vehicles = pd.DataFrame(vehicle_metrics)
            df_vehicles.to_parquet(run_dir / "vehicles.parquet", index=False)
        else:
            # Fallback: JSON
            with open(run_dir / "vehicles.json", "w") as f:
                json.dump(vehicle_metrics, f, indent=2, default=str)

        # Write interval metrics (parquet)
        if HAS_PANDAS and timestep_metrics:
            df_intervals = pd.DataFrame(timestep_metrics)
            df_intervals.to_parquet(run_dir / "intervals.parquet", index=False)
        else:
            with open(run_dir / "intervals.json", "w") as f:
                json.dump(timestep_metrics, f, indent=2, default=str)

        # Write overflow events
        with open(run_dir / "overflow_events.json", "w") as f:
            json.dump(overflow_events, f, indent=2, default=str)

        # Write decision latencies if available
        if decision_latencies:
            with open(run_dir / "decisions.jsonl", "w") as f:
                for d in decision_latencies:
                    f.write(json.dumps(d) + "\n")

        # Compute 5 primary metrics
        primary_metrics = self._compute_primary_metrics(
            vehicle_metrics, timestep_metrics, overflow_events
        )

        # Write metrics
        with open(run_dir / "metrics.json", "w") as f:
            json.dump(primary_metrics, f, indent=2, default=str)

        # Write manifest
        manifest = self._build_manifest(
            scenario_id, strategy_name, seed, config_dict,
            git_commit, manifest_extra, len(vehicle_metrics), len(timestep_metrics)
        )
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=str)

        return run_dir

    @staticmethod
    def _compute_primary_metrics(vehicle_metrics: list, timestep_metrics: list,
                                  overflow_events: list) -> dict:
        """Compute 5 primary metrics from logs."""
        if not vehicle_metrics:
            return {
                "primary_metrics": {
                    "avg_search_time_min": 0,
                    "avg_waiting_time_min": 0,
                    "avg_gate_queue_vehicles": 0,
                    "max_gate_queue_vehicles": 0,
                    "overflow_events_count": len(overflow_events),
                    "total_travel_time_veh_min": 0,
                    "total_travel_distance_veh_km": 0,
                },
                "secondary_metrics": {
                    "total_vehicles_simulated": 0,
                    "parked_vehicles": 0,
                    "rejected_vehicles": 0,
                    "allocation_success_rate": 0,
                }
            }

        # Metric 1: Avg parking search time
        search_times = [v["search_time_seconds"] for v in vehicle_metrics
                       if v["search_time_seconds"] is not None]
        avg_search_min = sum(search_times) / (60 * len(search_times)) if search_times else 0

        # Metric 2: Avg waiting time (gate + queue)
        wait_times = [v["waiting_time_seconds"] for v in vehicle_metrics
                     if v["waiting_time_seconds"] is not None]
        avg_wait_min = sum(wait_times) / (60 * len(wait_times)) if wait_times else 0

        # Metrics 3-4: Gate queue stats
        gate_queues = []
        for ts in timestep_metrics:
            for key, val in ts.items():
                if key.startswith("gate_queue_") and isinstance(val, (int, float)):
                    gate_queues.append(val)
        avg_gate_queue = sum(gate_queues) / len(gate_queues) if gate_queues else 0
        max_gate_queue = max(gate_queues) if gate_queues else 0

        # Metric 5a: Overflow events
        overflow_count = len(overflow_events)

        # Metric 5b: Total travel
        travel_times_min = [v["travel_time_seconds"] / 60 for v in vehicle_metrics
                           if v["travel_time_seconds"] is not None]
        total_travel_veh_min = sum(travel_times_min)

        travel_dist_km = [v["travel_distance_meters"] / 1000 for v in vehicle_metrics]
        total_travel_veh_km = sum(travel_dist_km)

        return {
            "primary_metrics": {
                "avg_search_time_min": round(avg_search_min, 2),
                "avg_waiting_time_min": round(avg_wait_min, 2),
                "avg_gate_queue_vehicles": round(avg_gate_queue, 2),
                "max_gate_queue_vehicles": int(max_gate_queue),
                "overflow_events_count": overflow_count,
                "total_travel_time_veh_min": round(total_travel_veh_min, 1),
                "total_travel_distance_veh_km": round(total_travel_veh_km, 1),
            },
            "secondary_metrics": {
                "total_vehicles_simulated": len(vehicle_metrics),
                "parked_vehicles": sum(1 for v in vehicle_metrics if v["final_state"] == "parked"),
                "rejected_vehicles": sum(1 for v in vehicle_metrics if v["final_state"] != "parked"),
                "allocation_success_rate": sum(1 for v in vehicle_metrics
                                               if v["assigned_lot_id"] is not None) / len(vehicle_metrics),
            }
        }

    @staticmethod
    def _build_manifest(scenario_id: str, strategy_name: str, seed: int,
                       config_dict: dict, git_commit: Optional[str],
                       extra: Optional[dict], vehicle_count: int,
                       timestep_count: int) -> dict:
        """Build manifest with config hash, git commit, timestamps."""
        # Config hash
        config_json = json.dumps(config_dict, sort_keys=True, default=str)
        config_hash = hashlib.sha256(config_json.encode()).hexdigest()[:8]

        # Git commit
        if git_commit is None:
            try:
                git_commit = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
            except:
                git_commit = "unknown"

        manifest = {
            "scenario_id": scenario_id,
            "strategy_name": strategy_name,
            "random_seed": seed,
            "config_hash": config_hash,
            "git_commit": git_commit,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "vehicle_count": vehicle_count,
            "timestep_count": timestep_count,
        }

        if extra:
            manifest.update(extra)

        return manifest
