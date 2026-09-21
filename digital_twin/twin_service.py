"""
Part 3: Digital Twin State -- the live, continuously-updating state of the
campus. This represents STATE (occupied/available/freshness), not the map.
Everyone reads from this; Member 2's data collection writes real
observations into it through the same validated update_* methods this
module's simulation engine uses (distinguished only by provenance/source).
"""

import json
from datetime import datetime, timezone

from digital_twin.models import FRESHNESS_THRESHOLDS_MINUTES, FreshnessState


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def compute_freshness(observation_timestamp: str, entity_type: str, now: datetime = None) -> str:
    if not observation_timestamp:
        return FreshnessState.UNKNOWN.value
    now = now or datetime.now(timezone.utc)
    age_minutes = (now - _parse_ts(observation_timestamp)).total_seconds() / 60.0
    fresh_below, aging_below = FRESHNESS_THRESHOLDS_MINUTES.get(entity_type, (10, 30))
    if age_minutes < fresh_below:
        return FreshnessState.FRESH.value
    if age_minutes < aging_below:
        return FreshnessState.AGING.value
    return FreshnessState.STALE.value


class DigitalTwinService:
    def initialize_state(self, campus_id: str, conn):
        """Sets every entity for this campus to no-data (deletes any
        existing current-state rows; history/snapshots are untouched)."""
        for table in ("parking_lot_state", "gate_state", "road_state", "vehicle_state"):
            conn.execute(f"DELETE FROM {table} WHERE campus_id=?", (campus_id,))
        conn.commit()

    def update_parking_state(self, campus_id, lot_id, occupied_spaces, source, provenance,
                              observation_timestamp, conn, now: datetime = None):
        if not source or not provenance:
            raise ValueError("Both 'source' and 'provenance' are required for a parking state update.")

        lot = conn.execute(
            "SELECT usable_capacity FROM parking_lots WHERE campus_id=? AND parking_lot_id=?",
            (campus_id, lot_id),
        ).fetchone()
        if not lot:
            raise ValueError(f"Unknown parking lot '{lot_id}' for campus '{campus_id}'.")

        usable_capacity = lot["usable_capacity"]
        if occupied_spaces > usable_capacity:
            raise ValueError(
                f"Rejected: occupied_spaces ({occupied_spaces}) exceeds usable_capacity "
                f"({usable_capacity}) for parking lot '{lot_id}'. State was NOT changed."
            )
        if occupied_spaces < 0:
            raise ValueError(f"Rejected: occupied_spaces cannot be negative for parking lot '{lot_id}'.")

        available_spaces = usable_capacity - occupied_spaces
        occupancy_percentage = round(100 * occupied_spaces / usable_capacity, 2) if usable_capacity else 0.0
        ingestion_timestamp = (now or datetime.now(timezone.utc)).isoformat()

        conn.execute(
            """INSERT INTO parking_lot_state (campus_id, parking_lot_id, occupied_spaces, available_spaces,
                 occupancy_percentage, predicted_occupancy, status, observation_timestamp, ingestion_timestamp,
                 source, provenance)
               VALUES (?, ?, ?, ?, ?, NULL, 'open', ?, ?, ?, ?)
               ON CONFLICT(campus_id, parking_lot_id) DO UPDATE SET
                 occupied_spaces=excluded.occupied_spaces, available_spaces=excluded.available_spaces,
                 occupancy_percentage=excluded.occupancy_percentage,
                 observation_timestamp=excluded.observation_timestamp,
                 ingestion_timestamp=excluded.ingestion_timestamp,
                 source=excluded.source, provenance=excluded.provenance""",
            (campus_id, lot_id, occupied_spaces, available_spaces, occupancy_percentage,
             observation_timestamp, ingestion_timestamp, source, provenance),
        )
        conn.commit()
        return self.get_parking_state(campus_id, lot_id, conn, now=now)

    def update_gate_state(self, campus_id, gate_id, current_queue_length, throughput_last_5min,
                           source, provenance, observation_timestamp, conn, now: datetime = None):
        if not source or not provenance:
            raise ValueError("Both 'source' and 'provenance' are required for a gate state update.")
        if current_queue_length < 0:
            raise ValueError(f"Rejected: current_queue_length cannot be negative for gate '{gate_id}'.")

        gate = conn.execute(
            "SELECT gate_id FROM gates WHERE campus_id=? AND gate_id=?", (campus_id, gate_id)
        ).fetchone()
        if not gate:
            raise ValueError(f"Unknown gate '{gate_id}' for campus '{campus_id}'.")

        ingestion_timestamp = (now or datetime.now(timezone.utc)).isoformat()
        conn.execute(
            """INSERT INTO gate_state (campus_id, gate_id, current_queue_length, throughput_last_5min,
                 status, observation_timestamp, ingestion_timestamp, source, provenance)
               VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?)
               ON CONFLICT(campus_id, gate_id) DO UPDATE SET
                 current_queue_length=excluded.current_queue_length,
                 throughput_last_5min=excluded.throughput_last_5min,
                 observation_timestamp=excluded.observation_timestamp,
                 ingestion_timestamp=excluded.ingestion_timestamp,
                 source=excluded.source, provenance=excluded.provenance""",
            (campus_id, gate_id, current_queue_length, throughput_last_5min,
             observation_timestamp, ingestion_timestamp, source, provenance),
        )
        conn.commit()
        return self._gate_state_row(campus_id, gate_id, conn, now=now)

    def update_road_state(self, campus_id, road_id, current_load, congestion_level,
                           source, provenance, observation_timestamp, conn, now: datetime = None):
        if not source or not provenance:
            raise ValueError("Both 'source' and 'provenance' are required for a road state update.")
        if current_load < 0:
            raise ValueError(f"Rejected: current_load cannot be negative for road '{road_id}'.")

        ingestion_timestamp = (now or datetime.now(timezone.utc)).isoformat()
        conn.execute(
            """INSERT INTO road_state (campus_id, road_id, current_load, congestion_level,
                 status, observation_timestamp, ingestion_timestamp, source, provenance)
               VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?)
               ON CONFLICT(campus_id, road_id) DO UPDATE SET
                 current_load=excluded.current_load, congestion_level=excluded.congestion_level,
                 observation_timestamp=excluded.observation_timestamp,
                 ingestion_timestamp=excluded.ingestion_timestamp,
                 source=excluded.source, provenance=excluded.provenance""",
            (campus_id, road_id, current_load, congestion_level,
             observation_timestamp, ingestion_timestamp, source, provenance),
        )
        conn.commit()

    def update_vehicle_state(self, campus_id, vehicle_id, state, source, timestamp, conn,
                              destination_id=None, assigned_parking_lot_id=None,
                              current_node_id=None, route=None, arrival_time=None):
        conn.execute(
            """INSERT INTO vehicle_state (campus_id, vehicle_id, arrival_time, destination_id,
                 assigned_parking_lot_id, current_node_id, route, state, source, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(campus_id, vehicle_id) DO UPDATE SET
                 destination_id=excluded.destination_id, assigned_parking_lot_id=excluded.assigned_parking_lot_id,
                 current_node_id=excluded.current_node_id, route=excluded.route, state=excluded.state,
                 source=excluded.source, timestamp=excluded.timestamp""",
            (campus_id, vehicle_id, arrival_time, destination_id, assigned_parking_lot_id,
             current_node_id, json.dumps(route) if route else None, state, source, timestamp),
        )
        conn.commit()

    def get_parking_state(self, campus_id, lot_id, conn, now: datetime = None):
        row = conn.execute(
            "SELECT * FROM parking_lot_state WHERE campus_id=? AND parking_lot_id=?", (campus_id, lot_id)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["freshness_state"] = compute_freshness(d["observation_timestamp"], "parking", now=now)
        return d

    def _gate_state_row(self, campus_id, gate_id, conn, now: datetime = None):
        row = conn.execute(
            "SELECT * FROM gate_state WHERE campus_id=? AND gate_id=?", (campus_id, gate_id)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["freshness_state"] = compute_freshness(d["observation_timestamp"], "gate", now=now)
        return d

    def get_current_state(self, campus_id, conn, now: datetime = None):
        parking = [
            {**dict(r), "freshness_state": compute_freshness(r["observation_timestamp"], "parking", now=now)}
            for r in conn.execute("SELECT * FROM parking_lot_state WHERE campus_id=?", (campus_id,))
        ]
        gates = [
            {**dict(r), "freshness_state": compute_freshness(r["observation_timestamp"], "gate", now=now)}
            for r in conn.execute("SELECT * FROM gate_state WHERE campus_id=?", (campus_id,))
        ]
        roads = [
            {**dict(r), "freshness_state": compute_freshness(r["observation_timestamp"], "road", now=now)}
            for r in conn.execute("SELECT * FROM road_state WHERE campus_id=?", (campus_id,))
        ]
        vehicles = [dict(r) for r in conn.execute("SELECT * FROM vehicle_state WHERE campus_id=?", (campus_id,))]
        return {"campus_id": campus_id, "parking": parking, "gates": gates, "roads": roads, "vehicles": vehicles}

    def get_state_history(self, campus_id, from_ts, to_ts, conn):
        query = "SELECT * FROM campus_state_snapshot WHERE campus_id=?"
        params = [campus_id]
        if from_ts:
            query += " AND timestamp >= ?"
            params.append(from_ts)
        if to_ts:
            query += " AND timestamp <= ?"
            params.append(to_ts)
        query += " ORDER BY timestamp ASC"
        rows = conn.execute(query, params).fetchall()
        return [{**dict(r), "full_state": json.loads(r["full_state"])} for r in rows]

    def snapshot_now(self, campus_id, conn, timestamp: str = None):
        timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        state = self.get_current_state(campus_id, conn)
        config_version_row = conn.execute(
            "SELECT active_configuration_version FROM campuses WHERE campus_id=?", (campus_id,)
        ).fetchone()
        config_version = config_version_row["active_configuration_version"] if config_version_row else None

        cursor = conn.execute(
            """INSERT INTO campus_state_snapshot (campus_id, timestamp, configuration_version, full_state)
               VALUES (?, ?, ?, ?)""",
            (campus_id, timestamp, config_version, json.dumps(state)),
        )
        conn.commit()
        return cursor.lastrowid

    def reset_state(self, campus_id, conn):
        """Testing/demo resets only."""
        for table in ("parking_lot_state", "gate_state", "road_state", "vehicle_state", "campus_state_snapshot"):
            conn.execute(f"DELETE FROM {table} WHERE campus_id=?", (campus_id,))
        conn.commit()
