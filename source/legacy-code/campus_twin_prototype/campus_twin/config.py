"""
Module 1: Campus Configuration.

What physically exists on a campus, and how it's connected — loaded from
JSON, never hard-coded. See data/campus_configs/*.json for examples.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Provenance(str, Enum):
    REAL = "REAL"
    HISTORICAL = "HISTORICAL"
    EXTERNAL = "EXTERNAL"
    EXTERNAL_MAP_REFERENCE = "EXTERNAL_MAP_REFERENCE"
    SAMPLE = "SAMPLE"
    SYNTHETIC = "SYNTHETIC"
    PREDICTION = "PREDICTION"
    DERIVED = "DERIVED"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    UNVERIFIED = "UNVERIFIED"


class VerificationState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    SURVEYED = "SURVEYED"
    CROSS_CHECKED = "CROSS_CHECKED"
    AUTHORIZED = "AUTHORIZED"
    ACTIVE = "ACTIVE"


class EntityStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


class ConfigError(ValueError):
    """Raised when a campus configuration fails validation. Never silently repaired."""


@dataclass
class Gate:
    gate_id: str
    campus_id: str
    name: str
    coordinates: Optional[dict] = None
    gate_type: str = "vehicle"
    status: EntityStatus = EntityStatus.OPEN
    vehicle_entry_allowed: bool = True
    vehicle_exit_allowed: bool = True
    pedestrian_entry_allowed: bool = True
    capacity: Optional[int] = None
    queue_capacity: Optional[int] = None
    provenance: Provenance = Provenance.SAMPLE
    verification_state: VerificationState = VerificationState.UNVERIFIED


@dataclass
class Road:
    road_id: str
    campus_id: str
    name: str
    start_node_id: str
    end_node_id: str
    length_meters: float
    geometry: Optional[list] = None
    speed_limit: Optional[float] = None
    driveable: bool = True
    walkable: bool = True
    one_way: bool = False
    capacity: Optional[int] = None
    status: EntityStatus = EntityStatus.OPEN
    provenance: Provenance = Provenance.SAMPLE
    verification_state: VerificationState = VerificationState.UNVERIFIED

    def __post_init__(self):
        if self.length_meters <= 0:
            raise ConfigError(f"Road '{self.road_id}' has non-positive length_meters.")


@dataclass
class ParkingLot:
    parking_lot_id: str
    campus_id: str
    name: str
    vehicle_access_point: str  # node_id it connects to
    capacity: int
    usable_capacity: int
    reserved_capacity: int = 0
    restricted_capacity: int = 0
    temporarily_unavailable_capacity: int = 0
    parking_type: str = "general"
    status: EntityStatus = EntityStatus.OPEN
    allowed_vehicle_types: list = field(default_factory=lambda: ["car"])
    destination_links: list = field(default_factory=list)
    pedestrian_access_point: Optional[str] = None
    provenance: Provenance = Provenance.SAMPLE
    verification_state: VerificationState = VerificationState.UNVERIFIED

    def __post_init__(self):
        if self.usable_capacity > self.capacity:
            raise ConfigError(
                f"ParkingLot '{self.parking_lot_id}' usable_capacity exceeds physical capacity."
            )
        if self.provenance == Provenance.EXTERNAL_MAP_REFERENCE:
            raise ConfigError(
                f"ParkingLot '{self.parking_lot_id}' capacity cannot come from a map "
                "reference alone; provenance EXTERNAL_MAP_REFERENCE is not allowed for lots."
            )


@dataclass
class Destination:
    destination_id: str
    campus_id: str
    name: str
    category: str
    coordinates: Optional[dict] = None
    aliases: list = field(default_factory=list)
    entrance_id: Optional[str] = None
    pedestrian_access_point: Optional[str] = None
    nearest_parking_lots: list = field(default_factory=list)
    status: EntityStatus = EntityStatus.OPEN
    provenance: Provenance = Provenance.SAMPLE
    verification_state: VerificationState = VerificationState.UNVERIFIED


@dataclass
class CampusConfig:
    campus_id: str
    name: str
    configuration_version: str
    timezone: str = "UTC"
    description: str = ""
    boundary: Optional[dict] = None
    status: EntityStatus = EntityStatus.OPEN
    gates: list = field(default_factory=list)       # list[Gate]
    roads: list = field(default_factory=list)        # list[Road]
    parking_lots: list = field(default_factory=list)  # list[ParkingLot]
    destinations: list = field(default_factory=list)  # list[Destination]


def _entity_status(value):
    return EntityStatus(value) if value else EntityStatus.UNKNOWN


def load_campus_config(path) -> CampusConfig:
    """Load and validate a campus configuration from a JSON file. Raises
    ConfigError on any structural problem — never guesses a missing field."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)

    campus_id = raw["campus_id"]

    gates = [
        Gate(
            gate_id=g["gate_id"],
            campus_id=campus_id,
            name=g["name"],
            coordinates=g.get("coordinates"),
            gate_type=g.get("gate_type", "vehicle"),
            status=_entity_status(g.get("status", "OPEN")),
            vehicle_entry_allowed=g.get("vehicle_entry_allowed", True),
            vehicle_exit_allowed=g.get("vehicle_exit_allowed", True),
            pedestrian_entry_allowed=g.get("pedestrian_entry_allowed", True),
            capacity=g.get("capacity"),
            queue_capacity=g.get("queue_capacity"),
            provenance=Provenance(g.get("provenance", "SAMPLE")),
            verification_state=VerificationState(g.get("verification_state", "UNVERIFIED")),
        )
        for g in raw.get("gates", [])
    ]

    roads = [
        Road(
            road_id=r["road_id"],
            campus_id=campus_id,
            name=r["name"],
            start_node_id=r["start_node_id"],
            end_node_id=r["end_node_id"],
            length_meters=r["length_meters"],
            geometry=r.get("geometry"),
            speed_limit=r.get("speed_limit"),
            driveable=r.get("driveable", True),
            walkable=r.get("walkable", True),
            one_way=r.get("one_way", False),
            capacity=r.get("capacity"),
            status=_entity_status(r.get("status", "OPEN")),
            provenance=Provenance(r.get("provenance", "SAMPLE")),
            verification_state=VerificationState(r.get("verification_state", "UNVERIFIED")),
        )
        for r in raw.get("roads", [])
    ]

    parking_lots = [
        ParkingLot(
            parking_lot_id=p["parking_lot_id"],
            campus_id=campus_id,
            name=p["name"],
            vehicle_access_point=p["vehicle_access_point"],
            capacity=p["capacity"],
            usable_capacity=p["usable_capacity"],
            reserved_capacity=p.get("reserved_capacity", 0),
            restricted_capacity=p.get("restricted_capacity", 0),
            temporarily_unavailable_capacity=p.get("temporarily_unavailable_capacity", 0),
            parking_type=p.get("parking_type", "general"),
            status=_entity_status(p.get("status", "OPEN")),
            allowed_vehicle_types=p.get("allowed_vehicle_types", ["car"]),
            destination_links=p.get("destination_links", []),
            pedestrian_access_point=p.get("pedestrian_access_point"),
            provenance=Provenance(p.get("provenance", "SAMPLE")),
            verification_state=VerificationState(p.get("verification_state", "UNVERIFIED")),
        )
        for p in raw.get("parking_lots", [])
    ]

    destinations = [
        Destination(
            destination_id=d["destination_id"],
            campus_id=campus_id,
            name=d["name"],
            category=d.get("category", "unknown"),
            coordinates=d.get("coordinates"),
            aliases=d.get("aliases", []),
            entrance_id=d.get("entrance_id"),
            pedestrian_access_point=d.get("pedestrian_access_point", d.get("vehicle_access_point")),
            nearest_parking_lots=d.get("nearest_parking_lots", []),
            status=_entity_status(d.get("status", "OPEN")),
            provenance=Provenance(d.get("provenance", "SAMPLE")),
            verification_state=VerificationState(d.get("verification_state", "UNVERIFIED")),
        )
        for d in raw.get("destinations", [])
    ]

    config = CampusConfig(
        campus_id=campus_id,
        name=raw["name"],
        configuration_version=raw["configuration_version"],
        timezone=raw.get("timezone", "UTC"),
        description=raw.get("description", ""),
        boundary=raw.get("boundary"),
        status=_entity_status(raw.get("status", "OPEN")),
        gates=gates,
        roads=roads,
        parking_lots=parking_lots,
        destinations=destinations,
    )

    errors = validate_campus_config(config)
    if errors:
        raise ConfigError(
            f"Campus config '{campus_id}' failed validation:\n" + "\n".join(errors)
        )

    return config


def validate_campus_config(config: CampusConfig) -> list:
    """Structural validation. Returns a list of error strings (empty = valid).
    Never silently repairs — the caller decides what to do with errors."""
    errors = []

    seen_gate_ids = set()
    for g in config.gates:
        if g.gate_id in seen_gate_ids:
            errors.append(f"Duplicate gate_id: {g.gate_id}")
        seen_gate_ids.add(g.gate_id)

    seen_lot_ids = set()
    for p in config.parking_lots:
        if p.parking_lot_id in seen_lot_ids:
            errors.append(f"Duplicate parking_lot_id: {p.parking_lot_id}")
        seen_lot_ids.add(p.parking_lot_id)

    seen_dest_ids = set()
    for d in config.destinations:
        if d.destination_id in seen_dest_ids:
            errors.append(f"Duplicate destination_id: {d.destination_id}")
        seen_dest_ids.add(d.destination_id)

    seen_road_ids = set()
    node_ids = seen_gate_ids | seen_lot_ids | seen_dest_ids
    node_ids |= {r.start_node_id for r in config.roads} | {r.end_node_id for r in config.roads}

    for r in config.roads:
        if r.road_id in seen_road_ids:
            errors.append(f"Duplicate road_id: {r.road_id}")
        seen_road_ids.add(r.road_id)

    for p in config.parking_lots:
        if p.vehicle_access_point not in node_ids:
            errors.append(
                f"ParkingLot '{p.parking_lot_id}' vehicle_access_point "
                f"'{p.vehicle_access_point}' does not reference a known node."
            )

    connected_nodes = set()
    for r in config.roads:
        connected_nodes.add(r.start_node_id)
        connected_nodes.add(r.end_node_id)

    for g in config.gates:
        if g.gate_id not in connected_nodes and config.roads:
            errors.append(f"Gate '{g.gate_id}' has no road connection (orphan node).")

    for p in config.parking_lots:
        if p.vehicle_access_point not in connected_nodes and config.roads:
            errors.append(
                f"ParkingLot '{p.parking_lot_id}' access point is not connected by any road."
            )

    return errors
