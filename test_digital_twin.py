import pytest

from campus_twin.digital_twin import DigitalTwin, GateState, ParkingState, StateError, VehicleState


def make_twin():
    twin = DigitalTwin("sample", "SAMPLE_CONFIG_V1")
    twin.initialize_state(
        parking_states=[ParkingState(parking_lot_id="lot-1", capacity=10, usable_capacity=10, occupied_spaces=0)],
        gate_states=[GateState(gate_id="gate-1")],
    )
    return twin


def test_parking_occupancy_update_and_available_spaces():
    twin = make_twin()
    twin.update_parking_state(ParkingState(parking_lot_id="lot-1", capacity=10, usable_capacity=10, occupied_spaces=3))
    state = twin.get_current_state()["parking"]["lot-1"]
    assert state.available_spaces == 7
    assert state.occupancy_percentage == 30.0


def test_negative_occupied_spaces_rejected():
    twin = make_twin()
    with pytest.raises(StateError):
        twin.update_parking_state(ParkingState(parking_lot_id="lot-1", capacity=10, usable_capacity=10, occupied_spaces=-1))


def test_occupied_exceeding_usable_capacity_rejected():
    twin = make_twin()
    with pytest.raises(StateError):
        twin.update_parking_state(ParkingState(parking_lot_id="lot-1", capacity=10, usable_capacity=10, occupied_spaces=11))


def test_negative_gate_queue_rejected():
    twin = make_twin()
    with pytest.raises(StateError):
        twin.update_gate_state(GateState(gate_id="gate-1", current_queue=-1))


def test_snapshot_and_restore_roundtrip():
    twin = make_twin()
    twin.update_parking_state(ParkingState(parking_lot_id="lot-1", capacity=10, usable_capacity=10, occupied_spaces=4))
    snapshot = twin.snapshot_now(timestamp="t=10")

    twin.update_parking_state(ParkingState(parking_lot_id="lot-1", capacity=10, usable_capacity=10, occupied_spaces=9))
    assert twin.get_current_state()["parking"]["lot-1"].occupied_spaces == 9

    twin.restore_snapshot(snapshot)
    assert twin.get_current_state()["parking"]["lot-1"].occupied_spaces == 4


def test_history_and_state_at_timestamp():
    twin = make_twin()
    twin.snapshot_now(timestamp="t=0")
    twin.snapshot_now(timestamp="t=5")
    assert len(twin.get_history()) == 2
    assert twin.get_state_at_timestamp("t=5").timestamp == "t=5"
    assert twin.get_state_at_timestamp("t=999") is None


def test_vehicle_lifecycle_valid_transition():
    twin = make_twin()
    twin.update_vehicle_state(VehicleState(vehicle_id="v1", campus_id="sample", state="ARRIVING"))
    twin.update_vehicle_state(VehicleState(vehicle_id="v1", campus_id="sample", state="WAITING_AT_GATE"))
    assert twin.get_current_state()["vehicles"]["v1"].state == "WAITING_AT_GATE"


def test_vehicle_lifecycle_invalid_transition_rejected():
    twin = make_twin()
    twin.update_vehicle_state(VehicleState(vehicle_id="v1", campus_id="sample", state="ARRIVING"))
    with pytest.raises(StateError):
        twin.update_vehicle_state(VehicleState(vehicle_id="v1", campus_id="sample", state="PARKED"))


def test_provenance_preserved_through_snapshot():
    twin = make_twin()
    snapshot = twin.snapshot_now(timestamp="t=0")
    assert snapshot.parking_states["lot-1"].provenance.value == "SYNTHETIC"


if __name__ == "__main__":
    test_parking_occupancy_update_and_available_spaces()
    test_snapshot_and_restore_roundtrip()
    test_history_and_state_at_timestamp()
    test_vehicle_lifecycle_valid_transition()
    print("Digital twin tests passed!")
