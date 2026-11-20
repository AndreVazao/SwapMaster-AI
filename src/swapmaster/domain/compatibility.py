"""Multi-criteria, evidence-aware preliminary powertrain screening.

A preliminary candidate is not an installation approval. Unimplemented checks
are explicitly reported as not assessed and force engineering review.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from swapmaster.domain.catalog import (
    InterfaceKind,
    InterfaceStatus,
    MechanicalInterface,
    PowerUnit,
    Transmission,
    VehiclePlatform,
    assess_interface_compatibility,
)
from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import EvidenceLevel
from swapmaster.domain.fitment import FitmentStatus, assess_envelope


class CriterionStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT_DATA = "insufficient_data"
    REQUIRES_REVIEW = "requires_review"
    NOT_ASSESSED = "not_assessed"


class CompatibilityStatus(StrEnum):
    INCOMPATIBLE = "incompatible"
    INSUFFICIENT_DATA = "insufficient_data"
    ENGINEERING_REVIEW_REQUIRED = "engineering_review_required"
    PRELIMINARY_CANDIDATE = "preliminary_candidate"


@dataclass(frozen=True, slots=True)
class CriterionAssessment:
    name: str
    status: CriterionStatus
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompatibilityAssessment:
    status: CompatibilityStatus
    criteria: tuple[CriterionAssessment, ...]
    disclaimer: str = (
        "Screening only. This is not proof of physical fitment, structural integrity, "
        "drivetrain alignment, roadworthiness, legal compliance, or permission to manufacture."
    )


def assess_powertrain_candidate(
    vehicle: VehiclePlatform,
    power_unit: PowerUnit,
    transmission: Transmission,
    clearance_mm: float = 0.0,
) -> CompatibilityAssessment:
    """Screen a vehicle/engine/gearbox combination without overstating fitment."""
    if not isfinite(clearance_mm) or clearance_mm < 0:
        raise ValueError("clearance_mm must be finite and non-negative.")

    criteria = (
        _assess_engine_bay(vehicle.engine_bay, power_unit.envelope, clearance_mm),
        _assess_bellhousing(power_unit, transmission),
        _assess_torque(power_unit, transmission),
        CriterionAssessment(
            "mounting_geometry",
            CriterionStatus.NOT_ASSESSED,
            (
                "Vehicle-to-power-unit mounting transformations and load paths "
                "are not implemented in this screening increment.",
            ),
        ),
        CriterionAssessment(
            "transmission_packaging",
            CriterionStatus.NOT_ASSESSED,
            (
                "No transmission-tunnel envelope or installed drivetrain placement "
                "model is available.",
            ),
        ),
    )

    statuses = {item.status for item in criteria}
    if CriterionStatus.FAIL in statuses:
        overall = CompatibilityStatus.INCOMPATIBLE
    elif CriterionStatus.INSUFFICIENT_DATA in statuses:
        overall = CompatibilityStatus.INSUFFICIENT_DATA
    elif (
        CriterionStatus.REQUIRES_REVIEW in statuses
        or CriterionStatus.NOT_ASSESSED in statuses
    ):
        overall = CompatibilityStatus.ENGINEERING_REVIEW_REQUIRED
    else:
        overall = CompatibilityStatus.PRELIMINARY_CANDIDATE

    return CompatibilityAssessment(overall, criteria)


def _assess_engine_bay(
    available: Envelope3D | None,
    component: Envelope3D | None,
    clearance_mm: float,
) -> CriterionAssessment:
    result = assess_envelope(component, available, clearance_mm)
    mapping = {
        FitmentStatus.INSUFFICIENT_DATA: CriterionStatus.INSUFFICIENT_DATA,
        FitmentStatus.GEOMETRY_EXCEEDS_ENVELOPE: CriterionStatus.FAIL,
        FitmentStatus.GEOMETRY_WITHIN_ENVELOPE_REQUIRES_REVIEW: (
            CriterionStatus.REQUIRES_REVIEW
        ),
        FitmentStatus.PRELIMINARY_GEOMETRY_PASS: CriterionStatus.PASS,
    }
    return CriterionAssessment("engine_bay_envelope", mapping[result.status], result.reasons)


def _find_bellhousing(
    unit: PowerUnit | Transmission,
) -> MechanicalInterface | None:
    return next(
        (item for item in unit.interfaces if item.kind is InterfaceKind.BELLHOUSING),
        None,
    )


def _assess_bellhousing(
    power_unit: PowerUnit, transmission: Transmission
) -> CriterionAssessment:
    result = assess_interface_compatibility(
        _find_bellhousing(power_unit),
        _find_bellhousing(transmission),
    )
    mapping = {
        InterfaceStatus.INSUFFICIENT_DATA: CriterionStatus.INSUFFICIENT_DATA,
        InterfaceStatus.INCOMPATIBLE: CriterionStatus.FAIL,
        InterfaceStatus.MATCH_REQUIRES_REVIEW: CriterionStatus.REQUIRES_REVIEW,
        InterfaceStatus.PRELIMINARY_MATCH: CriterionStatus.PASS,
    }
    return CriterionAssessment("bellhousing_interface", mapping[result.status], result.reasons)


def _assess_torque(
    power_unit: PowerUnit, transmission: Transmission
) -> CriterionAssessment:
    torque = power_unit.torque_nm
    limit = transmission.input_torque_limit_nm
    if torque is None or limit is None:
        return CriterionAssessment(
            "input_torque_limit",
            CriterionStatus.INSUFFICIENT_DATA,
            ("Power-unit torque or transmission input torque limit is missing.",),
        )
    if torque > limit:
        return CriterionAssessment(
            "input_torque_limit",
            CriterionStatus.FAIL,
            (f"Declared torque {torque:g} Nm exceeds limit {limit:g} Nm.",),
        )
    if (
        power_unit.evidence.level is not EvidenceLevel.CONFIRMED
        or transmission.evidence.level is not EvidenceLevel.CONFIRMED
    ):
        return CriterionAssessment(
            "input_torque_limit",
            CriterionStatus.REQUIRES_REVIEW,
            ("Torque values are within the declared limit but are not both confirmed.",),
        )
    return CriterionAssessment(
        "input_torque_limit",
        CriterionStatus.PASS,
        (f"Declared torque {torque:g} Nm is within the {limit:g} Nm input limit.",),
    )
