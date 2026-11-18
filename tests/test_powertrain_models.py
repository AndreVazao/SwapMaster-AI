import pytest

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.powertrain import (
    MechanicalInterface,
    PowerUnitSpec,
    PowertrainType,
    TransmissionType,
    GearboxSpec,
)


def confirmed() -> Evidence:
    return Evidence(EvidenceLevel.CONFIRMED, source="controlled test drawing")


def test_power_unit_requires_identity() -> None:
    with pytest.raises(ValueError, match="manufacturer"):
        PowerUnitSpec(
            "", "Unit", PowertrainType.ELECTRIC, None, None, None, None,
            (), None, confirmed(), "unit-1",
        )


def test_negative_mass_is_rejected() -> None:
    with pytest.raises(ValueError, match="mass_kg"):
        PowerUnitSpec(
            "Maker", "Unit", PowertrainType.ELECTRIC, None, -1, None, None,
            (), None, confirmed(), "unit-1",
        )


def test_gearbox_requires_identity() -> None:
    with pytest.raises(ValueError, match="manufacturer"):
        GearboxSpec(
            "", "Box", TransmissionType.MANUAL, None, None, None, None,
            (), confirmed(), "box-1",
        )


def test_interface_requires_coordinate_frame_and_holes() -> None:
    with pytest.raises(ValueError, match="coordinate system"):
        MechanicalInterface("Bellhousing", "", (), None, None, confirmed())
