"""Measured bolt-pattern comparison for mating drivetrain interfaces.

This module compares two patterns only when their coordinates use the same datum.
It is a geometric screening aid, not an adapter design or fitment approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from swapmaster.domain.evidence import Evidence, EvidenceLevel


@dataclass(frozen=True, slots=True)
class HoleCentre:
    """Bolt-hole centre and nominal diameter in millimetres."""

    x_mm: float
    y_mm: float
    diameter_mm: float

    def __post_init__(self) -> None:
        if not all(isfinite(v) for v in (self.x_mm, self.y_mm, self.diameter_mm)):
            raise ValueError("Hole coordinates and diameter must be finite.")
        if self.diameter_mm <= 0:
            raise ValueError("Hole diameter must be greater than zero.")


@dataclass(frozen=True, slots=True)
class InterfaceGeometry:
    """Measured 2D mating-face geometry in a documented coordinate frame."""

    interface_id: str
    coordinate_frame: str
    holes: tuple[HoleCentre, ...]
    pilot_diameter_mm: float | None
    evidence: Evidence

    def __post_init__(self) -> None:
        if not self.interface_id.strip() or not self.coordinate_frame.strip():
            raise ValueError("Interface ID and coordinate frame are required.")
        if not self.holes:
            raise ValueError("At least one bolt hole is required.")
        if self.pilot_diameter_mm is not None and (
            not isfinite(self.pilot_diameter_mm) or self.pilot_diameter_mm <= 0
        ):
            raise ValueError("Pilot diameter must be finite and greater than zero.")


class GeometryMatchStatus(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    DATUM_MISMATCH = "datum_mismatch"
    HOLE_COUNT_MISMATCH = "hole_count_mismatch"
    HOLE_PATTERN_MISMATCH = "hole_pattern_mismatch"
    PILOT_MISMATCH = "pilot_mismatch"
    MATCH_REQUIRES_REVIEW = "match_requires_review"
    PRELIMINARY_GEOMETRY_MATCH = "preliminary_geometry_match"


@dataclass(frozen=True, slots=True)
class GeometryMatchAssessment:
    status: GeometryMatchStatus
    reasons: tuple[str, ...]
    tolerance_mm: float


def _near(first: float, second: float, tolerance: float) -> bool:
    return abs(first - second) <= tolerance


def assess_interface_geometry(
    source: InterfaceGeometry | None,
    target: InterfaceGeometry | None,
    tolerance_mm: float = 0.1,
) -> GeometryMatchAssessment:
    """Compare hole positions/diameters and pilot; no rotation/translation is inferred."""
    if not isfinite(tolerance_mm) or tolerance_mm < 0:
        raise ValueError("Tolerance must be finite and non-negative.")
    if source is None or target is None:
        return GeometryMatchAssessment(
            GeometryMatchStatus.INSUFFICIENT_DATA,
            ("Both measured mating-interface geometries are required.",),
            tolerance_mm,
        )
    if source.coordinate_frame != target.coordinate_frame:
        return GeometryMatchAssessment(
            GeometryMatchStatus.DATUM_MISMATCH,
            ("Coordinate frames differ; establish and validate a common datum first.",),
            tolerance_mm,
        )
    if len(source.holes) != len(target.holes):
        return GeometryMatchAssessment(
            GeometryMatchStatus.HOLE_COUNT_MISMATCH,
            ("The two patterns have different hole counts.",),
            tolerance_mm,
        )

    unmatched = list(target.holes)
    for hole in source.holes:
        match = next(
            (
                index for index, candidate in enumerate(unmatched)
                if _near(hole.x_mm, candidate.x_mm, tolerance_mm)
                and _near(hole.y_mm, candidate.y_mm, tolerance_mm)
                and _near(hole.diameter_mm, candidate.diameter_mm, tolerance_mm)
            ),
            None,
        )
        if match is None:
            return GeometryMatchAssessment(
                GeometryMatchStatus.HOLE_PATTERN_MISMATCH,
                ("At least one hole centre or diameter differs beyond tolerance.",),
                tolerance_mm,
            )
        unmatched.pop(match)

    if (source.pilot_diameter_mm is None) != (target.pilot_diameter_mm is None):
        return GeometryMatchAssessment(
            GeometryMatchStatus.INSUFFICIENT_DATA,
            ("Pilot diameter is missing from one interface.",),
            tolerance_mm,
        )
    if (
        source.pilot_diameter_mm is not None
        and target.pilot_diameter_mm is not None
        and not _near(source.pilot_diameter_mm, target.pilot_diameter_mm, tolerance_mm)
    ):
        return GeometryMatchAssessment(
            GeometryMatchStatus.PILOT_MISMATCH,
            ("Pilot diameters differ beyond tolerance.",),
            tolerance_mm,
        )

    if (
        source.evidence.level is not EvidenceLevel.CONFIRMED
        or target.evidence.level is not EvidenceLevel.CONFIRMED
    ):
        return GeometryMatchAssessment(
            GeometryMatchStatus.MATCH_REQUIRES_REVIEW,
            ("Geometry compares within tolerance, but one or both records are not confirmed.",),
            tolerance_mm,
        )
    return GeometryMatchAssessment(
        GeometryMatchStatus.PRELIMINARY_GEOMETRY_MATCH,
        (
            "Measured hole centres, nominal diameters and supplied pilot diameter match.",
            "Crankshaft/input-shaft alignment, axial stack, clutch, starter, strength and loads remain unverified.",
        ),
        tolerance_mm,
    )
