import pytest

from swapmaster.domain.catalog import (
    InterfaceKind,
    InterfaceStatus,
    MechanicalInterface,
    MountingPoint,
    PowerUnit,
    PropulsionType,
    Transmission,
    VehiclePlatform,
    assess_interface_compatibility,
)
from swapmaster.domain.evidence import Evidence, EvidenceLevel


CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="OEM service manual")
ESTIMATED = Evidence(EvidenceLevel.ESTIMATED, method="visual estimate")


def test_vehicle_platform_rejects_duplicate_mounting_point_ids() -> None:
    point = MountingPoint("left", 1.0, 2.0, 3.0, "vehicle-local", CONFIRMED)
    with pytest.raises(ValueError, match="must be unique"):
        VehiclePlatform(
            "platform-1", "Maker", "Model", 2020, CONFIRMED,
            mounting_points=(point, point),
        )


def test_vehicle_platform_rejects_invalid_year() -> None:
    with pytest.raises(ValueError, match="model_year"):
        VehiclePlatform("p1", "Maker", "Model", 1800, CONFIRMED)


def test_power_unit_validates_physical_values() -> None:
    with pytest.raises(ValueError, match="power_kw"):
        PowerUnit("u1", "Maker", "Unit", PropulsionType.ELECTRIC, CONFIRMED, power_kw=float("inf"))


def test_transmission_validates_torque_limit() -> None:
    with pytest.raises(ValueError, match="input_torque_limit_nm"):
        Transmission("t1", "Maker", "Box", CONFIRMED, input_torque_limit_nm=0)


def test_matching_confirmed_interfaces_are_only_a_preliminary_match() -> None:
    left = MechanicalInterface(InterfaceKind.BELLHOUSING, "SAE-X/rev-A", CONFIRMED)
    right = MechanicalInterface(InterfaceKind.BELLHOUSING, "SAE-X/rev-A", CONFIRMED)
    result = assess_interface_compatibility(left, right)
    assert result.status is InterfaceStatus.PRELIMINARY_MATCH
    assert "loads" in result.reasons[1]


def test_matching_estimated_interfaces_require_review() -> None:
    left = MechanicalInterface(InterfaceKind.ENGINE_MOUNT, "mount-42", ESTIMATED)
    right = MechanicalInterface(InterfaceKind.ENGINE_MOUNT, "mount-42", CONFIRMED)
    assert assess_interface_compatibility(left, right).status is InterfaceStatus.MATCH_REQUIRES_REVIEW


def test_different_interface_ids_are_incompatible() -> None:
    left = MechanicalInterface(InterfaceKind.BELLHOUSING, "pattern-A", CONFIRMED)
    right = MechanicalInterface(InterfaceKind.BELLHOUSING, "pattern-B", CONFIRMED)
    assert assess_interface_compatibility(left, right).status is InterfaceStatus.INCOMPATIBLE


def test_missing_interface_is_insufficient_data() -> None:
    assert assess_interface_compatibility(None, None).status is InterfaceStatus.INSUFFICIENT_DATA


def test_duplicate_interface_definitions_are_rejected() -> None:
    interface = MechanicalInterface(InterfaceKind.COOLING, "hose-A", CONFIRMED)
    with pytest.raises(ValueError, match="must be unique"):
        PowerUnit(
            "u1", "Maker", "Unit", PropulsionType.COMBUSTION, CONFIRMED,
            interfaces=(interface, interface),
        )
