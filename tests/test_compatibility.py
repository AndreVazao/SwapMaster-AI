import pytest

from swapmaster.domain.catalog import (
    InterfaceKind,
    MechanicalInterface,
    PowerUnit,
    PropulsionType,
    Transmission,
    VehiclePlatform,
)
from swapmaster.domain.compatibility import (
    CompatibilityStatus,
    CriterionStatus,
    assess_powertrain_candidate,
)
from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence, EvidenceLevel

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="verified engineering drawing")
ESTIMATED = Evidence(EvidenceLevel.ESTIMATED, method="unverified estimate")


def make_candidate(
    *,
    torque: float | None = 250.0,
    torque_limit: float | None = 300.0,
    engine_envelope: Envelope3D | None = None,
    bay: Envelope3D | None = None,
    engine_evidence: Evidence = CONFIRMED,
    gearbox_evidence: Evidence = CONFIRMED,
    engine_interface: str | None = "pattern-A/rev-1",
    gearbox_interface: str | None = "pattern-A/rev-1",
):
    vehicle = VehiclePlatform("v1", "Maker", "Model", 2020, CONFIRMED, engine_bay=bay)
    engine_interfaces = (
        (MechanicalInterface(InterfaceKind.BELLHOUSING, engine_interface, engine_evidence),)
        if engine_interface is not None
        else ()
    )
    gearbox_interfaces = (
        (MechanicalInterface(InterfaceKind.BELLHOUSING, gearbox_interface, gearbox_evidence),)
        if gearbox_interface is not None
        else ()
    )
    engine = PowerUnit(
        "e1",
        "Maker",
        "Engine",
        PropulsionType.COMBUSTION,
        engine_evidence,
        envelope=engine_envelope,
        torque_nm=torque,
        interfaces=engine_interfaces,
    )
    gearbox = Transmission(
        "g1",
        "Maker",
        "Gearbox",
        gearbox_evidence,
        input_torque_limit_nm=torque_limit,
        interfaces=gearbox_interfaces,
    )
    return vehicle, engine, gearbox


def test_candidate_requires_review_when_mounting_and_transmission_are_unassessed():
    bay = Envelope3D(800, 700, 600, CONFIRMED)
    engine = Envelope3D(700, 600, 500, CONFIRMED)
    result = assess_powertrain_candidate(*make_candidate(bay=bay, engine_envelope=engine))
    assert result.status is CompatibilityStatus.ENGINEERING_REVIEW_REQUIRED
    assert any(c.status is CriterionStatus.NOT_ASSESSED for c in result.criteria)


def test_engine_envelope_exceeding_bay_is_incompatible():
    bay = Envelope3D(500, 500, 500, CONFIRMED)
    engine = Envelope3D(700, 500, 500, CONFIRMED)
    result = assess_powertrain_candidate(*make_candidate(bay=bay, engine_envelope=engine))
    assert result.status is CompatibilityStatus.INCOMPATIBLE
    criterion = next(c for c in result.criteria if c.name == "engine_bay_envelope")
    assert criterion.status is CriterionStatus.FAIL


def test_missing_engine_envelope_is_insufficient_data():
    result = assess_powertrain_candidate(*make_candidate())
    assert result.status is CompatibilityStatus.INSUFFICIENT_DATA


def test_mismatched_bellhousing_is_incompatible():
    result = assess_powertrain_candidate(
        *make_candidate(engine_interface="pattern-A", gearbox_interface="pattern-B")
    )
    assert result.status is CompatibilityStatus.INCOMPATIBLE


def test_missing_bellhousing_blocks_positive_screening():
    result = assess_powertrain_candidate(*make_candidate(engine_interface=None))
    assert result.status is CompatibilityStatus.INSUFFICIENT_DATA


def test_torque_above_gearbox_limit_is_incompatible():
    result = assess_powertrain_candidate(*make_candidate(torque=350, torque_limit=300))
    assert result.status is CompatibilityStatus.INCOMPATIBLE


def test_missing_torque_data_is_insufficient():
    result = assess_powertrain_candidate(*make_candidate(torque=None))
    assert result.status is CompatibilityStatus.INSUFFICIENT_DATA


def test_estimated_torque_data_requires_review():
    result = assess_powertrain_candidate(
        *make_candidate(engine_evidence=ESTIMATED, gearbox_evidence=ESTIMATED)
    )
    assert result.status is CompatibilityStatus.ENGINEERING_REVIEW_REQUIRED
    criterion = next(c for c in result.criteria if c.name == "input_torque_limit")
    assert criterion.status is CriterionStatus.REQUIRES_REVIEW


@pytest.mark.parametrize("clearance", [-1.0, float("nan"), float("inf")])
def test_invalid_clearance_is_rejected(clearance: float):
    vehicle, engine, gearbox = make_candidate()
    with pytest.raises(ValueError, match="clearance_mm"):
        assess_powertrain_candidate(vehicle, engine, gearbox, clearance_mm=clearance)
