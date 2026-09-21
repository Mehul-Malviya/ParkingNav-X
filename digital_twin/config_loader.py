"""
Part 1: Campus Configuration loader.

Loads one campus's YAML config, validates it structurally, then upserts it
into SQLite keyed by (campus_id, entity_id) — running the loader twice on
the same file produces zero new rows. Validation never silently repairs a
problem; it raises ConfigError with a clear reason.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml

from digital_twin.models import ConfigError

LAT_RANGE = (-90.0, 90.0)
LNG_RANGE = (-180.0, 180.0)


def load_campus_yaml(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_campus_config(raw: dict) -> list:
    """Returns a list of error strings. Empty list = valid."""
    errors = []
    campus = raw.get("campus", {})
    campus_id = campus.get("campus_id")
    if not campus_id:
        return ["Missing campus.campus_id"]

    gates = raw.get("gates", [])
    roads = raw.get("roads", [])
    parking_lots = raw.get("parking_lots", [])
    destinations = raw.get("destinations", [])
    events = raw.get("events", [])
    edges = raw.get("edges", [])

    def _check_duplicates(items, id_field, label):
        seen = set()
        for item in items:
            item_id = item.get(id_field)
            if item_id in seen:
                errors.append(f"Duplicate {label} id within file: {item_id}")
            seen.add(item_id)

    _check_duplicates(gates, "gate_id", "gate")
    _check_duplicates(roads, "road_id", "road")
    _check_duplicates(parking_lots, "parking_lot_id", "parking lot")
    _check_duplicates(destinations, "destination_id", "destination")
    _check_duplicates(events, "event_id", "event")

    node_coords = {}  # node_id -> (lat, lng)
    node_ids = set()

    def _check_coords(lat, lng, label):
        if lat is None or lng is None:
            return
        if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1]):
            errors.append(f"{label}: latitude {lat} out of range")
        if not (LNG_RANGE[0] <= lng <= LNG_RANGE[1]):
            errors.append(f"{label}: longitude {lng} out of range")

    for g in gates:
        gate_id = g.get("gate_id")
        node_ids.add(gate_id)
        if g.get("capacity", 0) <= 0:
            errors.append(f"Gate '{gate_id}' has non-positive capacity.")
        lat, lng = g.get("latitude"), g.get("longitude")
        _check_coords(lat, lng, f"Gate '{gate_id}'")
        if lat is not None and lng is not None:
            node_coords[gate_id] = (lat, lng)

    for p in parking_lots:
        lot_id = p.get("parking_lot_id")
        node_ids.add(lot_id)
        total = p.get("total_capacity", 0)
        usable = p.get("usable_capacity", 0)
        reserved = p.get("reserved_capacity", 0)
        restricted = p.get("restricted_capacity", 0)
        unavailable = p.get("temporarily_unavailable_capacity", 0)
        if total <= 0:
            errors.append(f"ParkingLot '{lot_id}' has non-positive total_capacity.")
        if usable + reserved + restricted + unavailable > total:
            errors.append(
                f"ParkingLot '{lot_id}': usable+reserved+restricted+unavailable exceeds total_capacity."
            )
        lat, lng = p.get("latitude"), p.get("longitude")
        _check_coords(lat, lng, f"ParkingLot '{lot_id}'")
        if lat is not None and lng is not None:
            node_coords[lot_id] = (lat, lng)

    for d in destinations:
        dest_id = d.get("destination_id")
        node_ids.add(dest_id)
        lat, lng = d.get("latitude"), d.get("longitude")
        _check_coords(lat, lng, f"Destination '{dest_id}'")
        if lat is not None and lng is not None:
            node_coords[dest_id] = (lat, lng)
        for gate_id in d.get("nearest_gate_ids", []) or []:
            if gate_id not in {g.get("gate_id") for g in gates}:
                errors.append(f"Destination '{dest_id}' references unknown gate '{gate_id}'.")
        for lot_id in d.get("nearest_parking_lot_ids", []) or []:
            if lot_id not in {p.get("parking_lot_id") for p in parking_lots}:
                errors.append(f"Destination '{dest_id}' references unknown parking lot '{lot_id}'.")

    known_node_ids = node_ids
    for r in roads:
        road_id = r.get("road_id")
        start_id, end_id = r.get("start_node_id"), r.get("end_node_id")
        geometry = r.get("geometry", [])
        length = r.get("length_meters", 0)

        if length <= 0:
            errors.append(f"Road '{road_id}' has non-positive length_meters.")
        if start_id not in known_node_ids:
            errors.append(f"Road '{road_id}' start_node_id '{start_id}' does not exist in this campus.")
        if end_id not in known_node_ids:
            errors.append(f"Road '{road_id}' end_node_id '{end_id}' does not exist in this campus.")
        if len(geometry) < 2:
            errors.append(
                f"Road '{road_id}' geometry has fewer than 2 points; a road must have a real walked path, "
                "not just its two endpoints implied."
            )
        elif len(geometry) == 2:
            errors.append(
                f"Road '{road_id}' geometry has only its two endpoints; a straight line cannot represent "
                "a real curved path. Provide the walked/surveyed intermediate points."
            )
        else:
            first, last = geometry[0], geometry[-1]
            start_coords = node_coords.get(start_id)
            end_coords = node_coords.get(end_id)
            if start_coords and (round(first["lat"], 5), round(first["lng"], 5)) != (
                round(start_coords[0], 5), round(start_coords[1], 5)
            ):
                errors.append(f"Road '{road_id}' geometry's first point does not match start_node_id's coordinates.")
            if end_coords and (round(last["lat"], 5), round(last["lng"], 5)) != (
                round(end_coords[0], 5), round(end_coords[1], 5)
            ):
                errors.append(f"Road '{road_id}' geometry's last point does not match end_node_id's coordinates.")

    edge_connected_nodes = set()
    for e in edges:
        edge_connected_nodes.add(e.get("from_node_id"))
        edge_connected_nodes.add(e.get("to_node_id"))
        if e.get("from_node_id") not in known_node_ids:
            errors.append(f"Edge references unknown from_node_id '{e.get('from_node_id')}'.")
        if e.get("to_node_id") not in known_node_ids:
            errors.append(f"Edge references unknown to_node_id '{e.get('to_node_id')}'.")

    for node_id in node_ids:
        if node_id not in edge_connected_nodes:
            errors.append(f"Node '{node_id}' is not connected by any edge in ROUTES_GRAPH_EDGES (orphan node).")

    return errors


def load_campus_config(path, conn: sqlite3.Connection) -> str:
    """Validates and idempotently upserts a campus config YAML file into
    the DB. Returns the campus_id. Raises ConfigError on any validation
    failure — nothing is written if validation fails."""
    raw = load_campus_yaml(path)
    errors = validate_campus_config(raw)
    if errors:
        raise ConfigError(
            f"Campus config at '{path}' failed validation:\n" + "\n".join(f"- {e}" for e in errors)
        )

    campus = raw["campus"]
    campus_id = campus["campus_id"]
    config_version = campus.get("configuration_version", "V1")
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """INSERT INTO campuses (campus_id, name, description, timezone, active_configuration_version, created_at)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(campus_id) DO UPDATE SET
             name=excluded.name, description=excluded.description, timezone=excluded.timezone,
             active_configuration_version=excluded.active_configuration_version""",
        (campus_id, campus["name"], campus.get("description", ""), campus.get("timezone", "UTC"), config_version, now),
    )

    for g in raw.get("gates", []):
        conn.execute(
            """INSERT INTO gates (campus_id, gate_id, name, latitude, longitude, capacity, status, metadata, configuration_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(campus_id, gate_id) DO UPDATE SET
                 name=excluded.name, latitude=excluded.latitude, longitude=excluded.longitude,
                 capacity=excluded.capacity, status=excluded.status, metadata=excluded.metadata,
                 configuration_version=excluded.configuration_version""",
            (campus_id, g["gate_id"], g["name"], g.get("latitude"), g.get("longitude"),
             g["capacity"], g.get("status", "open"), json.dumps(g.get("metadata", {})), config_version),
        )

    for r in raw.get("roads", []):
        conn.execute(
            """INSERT INTO roads (campus_id, road_id, name, start_node_id, end_node_id, length_meters,
                 expected_travel_time_seconds, is_walkable, is_driveable, status, geometry, configuration_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(campus_id, road_id) DO UPDATE SET
                 name=excluded.name, start_node_id=excluded.start_node_id, end_node_id=excluded.end_node_id,
                 length_meters=excluded.length_meters, expected_travel_time_seconds=excluded.expected_travel_time_seconds,
                 is_walkable=excluded.is_walkable, is_driveable=excluded.is_driveable, status=excluded.status,
                 geometry=excluded.geometry, configuration_version=excluded.configuration_version""",
            (campus_id, r["road_id"], r["name"], r["start_node_id"], r["end_node_id"], r["length_meters"],
             r.get("expected_travel_time_seconds"), int(r.get("is_walkable", True)), int(r.get("is_driveable", True)),
             r.get("status", "open"), json.dumps(r["geometry"]), config_version),
        )

    for p in raw.get("parking_lots", []):
        conn.execute(
            """INSERT INTO parking_lots (campus_id, parking_lot_id, name, latitude, longitude, boundary_polygon,
                 zone, status, total_capacity, usable_capacity, reserved_capacity, restricted_capacity,
                 temporarily_unavailable_capacity, configuration_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(campus_id, parking_lot_id) DO UPDATE SET
                 name=excluded.name, latitude=excluded.latitude, longitude=excluded.longitude,
                 boundary_polygon=excluded.boundary_polygon, zone=excluded.zone, status=excluded.status,
                 total_capacity=excluded.total_capacity, usable_capacity=excluded.usable_capacity,
                 reserved_capacity=excluded.reserved_capacity, restricted_capacity=excluded.restricted_capacity,
                 temporarily_unavailable_capacity=excluded.temporarily_unavailable_capacity,
                 configuration_version=excluded.configuration_version""",
            (campus_id, p["parking_lot_id"], p["name"], p.get("latitude"), p.get("longitude"),
             json.dumps(p.get("boundary_polygon")) if p.get("boundary_polygon") else None,
             p.get("zone"), p.get("status", "open"), p["total_capacity"], p["usable_capacity"],
             p.get("reserved_capacity", 0), p.get("restricted_capacity", 0),
             p.get("temporarily_unavailable_capacity", 0), config_version),
        )

    for d in raw.get("destinations", []):
        conn.execute(
            """INSERT INTO destinations (campus_id, destination_id, name, category, latitude, longitude,
                 department_names, searchable_aliases, nearest_gate_ids, nearest_parking_lot_ids, configuration_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(campus_id, destination_id) DO UPDATE SET
                 name=excluded.name, category=excluded.category, latitude=excluded.latitude,
                 longitude=excluded.longitude, department_names=excluded.department_names,
                 searchable_aliases=excluded.searchable_aliases, nearest_gate_ids=excluded.nearest_gate_ids,
                 nearest_parking_lot_ids=excluded.nearest_parking_lot_ids,
                 configuration_version=excluded.configuration_version""",
            (campus_id, d["destination_id"], d["name"], d.get("category", "other"), d.get("latitude"), d.get("longitude"),
             json.dumps(d.get("department_names")) if d.get("department_names") else None,
             json.dumps(d.get("searchable_aliases", [])), json.dumps(d.get("nearest_gate_ids", [])),
             json.dumps(d.get("nearest_parking_lot_ids", [])), config_version),
        )

    for e in raw.get("events", []):
        conn.execute(
            """INSERT INTO events (campus_id, event_id, event_type, name, start_time, end_time,
                 expected_demand_multiplier, affected_zones, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(campus_id, event_id) DO UPDATE SET
                 event_type=excluded.event_type, name=excluded.name, start_time=excluded.start_time,
                 end_time=excluded.end_time, expected_demand_multiplier=excluded.expected_demand_multiplier,
                 affected_zones=excluded.affected_zones, status=excluded.status""",
            (campus_id, e["event_id"], e["event_type"], e["name"], e.get("start_time"), e.get("end_time"),
             e.get("expected_demand_multiplier", 1.0), json.dumps(e.get("affected_zones", [])), e.get("status", "scheduled")),
        )

    conn.execute("DELETE FROM routes_graph_edges WHERE campus_id = ?", (campus_id,))
    for e in raw.get("edges", []):
        conn.execute(
            """INSERT INTO routes_graph_edges (campus_id, from_node_id, to_node_id, road_id,
                 weight_time_seconds, weight_distance_meters, is_walkable, is_driveable, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (campus_id, e["from_node_id"], e["to_node_id"], e.get("road_id"),
             e["weight_time_seconds"], e["weight_distance_meters"],
             int(e.get("is_walkable", True)), int(e.get("is_driveable", True)), e.get("status", "open")),
        )

    conn.commit()
    return campus_id
