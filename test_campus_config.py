from pathlib import Path

import pytest

from campus_twin.config import ConfigError, load_campus_config, validate_campus_config

PROJECT_FOLDER = Path(__file__).resolve().parent
CONFIGS = PROJECT_FOLDER / "data" / "campus_configs"


def test_vitap_campus_loads():
    config = load_campus_config(CONFIGS / "vitap.json")
    assert config.campus_id == "vitap"
    assert len(config.destinations) == 11
    assert len(config.gates) == 1
    assert len(config.parking_lots) == 1


def test_sample_campus_loads():
    config = load_campus_config(CONFIGS / "sample.json")
    assert config.campus_id == "sample"
    assert len(config.parking_lots) == 2


def test_destination_provenance_is_external_map_reference():
    config = load_campus_config(CONFIGS / "vitap.json")
    for destination in config.destinations:
        assert destination.provenance.value == "EXTERNAL_MAP_REFERENCE"


def test_gate_and_lot_provenance_is_sample():
    config = load_campus_config(CONFIGS / "vitap.json")
    assert config.gates[0].provenance.value == "SAMPLE"
    assert config.parking_lots[0].provenance.value == "SAMPLE"


def test_duplicate_gate_id_is_rejected():
    config = load_campus_config(CONFIGS / "sample.json")
    config.gates.append(config.gates[0])
    errors = validate_campus_config(config)
    assert any("Duplicate gate_id" in e for e in errors)


def test_parking_lot_cannot_have_external_map_reference_provenance():
    from campus_twin.config import ParkingLot

    with pytest.raises(ConfigError):
        ParkingLot(
            parking_lot_id="bad-lot", campus_id="x", name="Bad Lot",
            vehicle_access_point="x", capacity=10, usable_capacity=10,
            provenance="EXTERNAL_MAP_REFERENCE",
        )


def test_usable_capacity_cannot_exceed_physical_capacity():
    from campus_twin.config import ParkingLot

    with pytest.raises(ConfigError):
        ParkingLot(
            parking_lot_id="bad-lot", campus_id="x", name="Bad Lot",
            vehicle_access_point="x", capacity=10, usable_capacity=20,
        )


if __name__ == "__main__":
    test_vitap_campus_loads()
    test_sample_campus_loads()
    test_destination_provenance_is_external_map_reference()
    test_gate_and_lot_provenance_is_sample()
    test_duplicate_gate_id_is_rejected()
    print("Campus config tests passed!")
