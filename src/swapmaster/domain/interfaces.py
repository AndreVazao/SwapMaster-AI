"""Conservative comparison of engine-to-gearbox mating interfaces."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from swapmaster.domain.evidence import EvidenceLevel
from swapmaster.domain.powertrain import MechanicalInterface


class InterfaceStatus(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    DATUM_MISMATCH = "datum_mismatch"
    HOLE_COUNT_MISMATCH = "hole_count_mismatch"
    HOLE_PATTERN_MISMATCH = "hole_pattern_mismatch"
    PILOT_DIAMETER_MISMATCH = "pilot_diameter_mismatch"
    AXIAL_DATUM_MISMATCH = "axial_datum_mismatch"
    GEOMETRY_MATCH_REQUIRES_REVIEW = "geometry_match_requires_review"
    PRELIMINARY_GEOMETRY_MATCH = "preliminary_geometry_match"


@dataclass(frozen=True, slots=True)
class InterfaceAssessment:
    status: InterfaceStatus
    reasons: tuple[str, ...]
    disclaimer: str = (
        "This compares nominal interface geometry only. It does not validate clutch, "
        "flywheel, starter, input shaft, concentricity, strength, fasteners or operation."
    )


def _close(a: float, b: float, tolerance_mm: float) -> bool:
    return abs(a - b) <= tolerance_mm


def _hole_matches(a: object, b: object, tolerance_mm: float) -> bool:
    """Compare hole centre and diameter without assuming arbitrary coordinate transforms."""
    first = a
    second = b
    return (
        _close(first.centre.x_mm, second.centre.x_mm, tolerance_mm)
        and _close(first.centre.y_mm, second.centre.y_mm, tolerance_mm)
        and _close(first.centre.z_mm, second.centre.z_mm, tolerance_mm)
        and _close(first.diameter_mm, second.diameter_mm, tolerance_mm)
    )


def assess_interface_pair(
    power_unit_side: MechanicalInterface | None,
    gearbox_side: MechanicalInterface | None,
    tolerance_mm: float = 0.1,
) -> InterfaceAssessment:
    """Compare two interfaces already expressed in the same datum and coordinate frame."""
    if tolerance_mm < 0:
        raise ValueError("tolerance_mm cannot be negative.")
    if power_unit_side is None or gearbox_side is None:
        return InterfaceAssessment(
            InterfaceStatus.INSUFFICIENT_DATA,
            ("One or both mating-interface definitions are missing.",),
        )
    if power_unit_side.coordinate_system != gearbox_side.coordinate_system:
        return InterfaceAssessment(
            InterfaceStatus.DATUM_MISMATCH,
            ("Interfaces use different coordinate systems; transform and datum validation are required.",),
        )
    if len(power_unit_side.holes) != len(gearbox_side.holes):
        return InterfaceAssessment(
            InterfaceStatus.HOLE_COUNT_MISMATCH,
            ("The mating interfaces contain different numbers of bolt holes.",),
        )

    unmatched = list(gearbox_side.holes)
    for hole in power_unit_side.holes:
        match_index = next(
            (i for i, other in enumerate(unmatched) if _hole_matches(hole, other, tolerance_mm)),
            None,
        )
        if match_index is None:
            return InterfaceAssessment(
                InterfaceStatus.HOLE_PATTERN_MISMATCH,
                ("At least one hole centre or nominal diameter differs beyond tolerance.",),
            )
        unmatched.pop(match_index)

    pilot_a = power_unit_side.pilot_diameter_mm
    pilot_b = gearbox_side.pilot_diameter_mm
    if (pilot_a is None) != (pilot_b is None):
        return InterfaceAssessment(
            InterfaceStatus.INSUFFICIENT_DATA,
            ("Pilot diameter is missing on one side.",),
        )
    if pilot_a is not None and pilot_b is not None and not _close(pilot_a, pilot_b, tolerance_mm):
        return InterfaceAssessment(
            InterfaceStatus.PILOT_DIAMETER_MISMATCH,
            ("Pilot diameters differ beyond tolerance.",),
        )

    axial_a = power_unit_side.face_to_datum_mm
    axial_b = gearbox_side.face_to_datum_mm
    if (axial_a is None) != (axial_b is None):
        return InterfaceAssessment(
            InterfaceStatus.INSUFFICIENT_DATA,
            ("Axial face-to-datum measurement is missing on one side.",),
        )
    if axial_a is not None and axial_b is not None and not _close(axial_a, axial_b, tolerance_mm):
        return InterfaceAssessment(
            InterfaceStatus.AXIAL_DATUM_MISMATCH,
            ("Axial face-to-datum measurements differ beyond tolerance.",),
        )

    if (
        power_unit_side.evidence.level is not EvidenceLevel.CONFIRMED
        or gearbox_side.evidence.level is not EvidenceLevel.CONFIRMED
    ):
        return InterfaceAssessment(
            InterfaceStatus.GEOMETRY_MATCH_REQUIRES_REVIEW,
            ("Nominal geometry matches, but at least one input is not confirmed.",),
        )
    return InterfaceAssessment(
        InterfaceStatus.PRELIMINARY_GEOMETRY_MATCH,
        (
            "Nominal hole pattern and supplied pilot/axial dimensions match within tolerance.",
            "A preliminary match is not a validated gearbox conversion.",
        ),
    )
