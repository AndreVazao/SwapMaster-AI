"""Conservative comparison of mounting-point sets in a shared datum.

Coordinates are millimetres. This checks point geometry only; it is not a
transformation solver, mount design, load-path analysis, or structural approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from swapmaster.domain.catalog import MountingPoint
from swapmaster.domain.evidence import EvidenceLevel


class MountingGeometryStatus(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    DATUM_MISMATCH = "datum_mismatch"
    POINT_COUNT_MISMATCH = "point_count_mismatch"
    IDENTIFIER_MISMATCH = "identifier_mismatch"
    GEOMETRY_MISMATCH = "geometry_mismatch"
    MATCH_REQUIRES_REVIEW = "match_requires_review"
    PRELIMINARY_GEOMETRY_MATCH = "preliminary_geometry_match"


@dataclass(frozen=True, slots=True)
class MountingGeometryAssessment:
    status: MountingGeometryStatus
    reasons: tuple[str, ...]
    tolerance_mm: float


def assess_mounting_geometry(
    source: tuple[MountingPoint, ...] | None,
    target: tuple[MountingPoint, ...] | None,
    *,
    common_coordinate_frame: str | None = None,
    tolerance_mm: float = 1.0,
) -> MountingGeometryAssessment:
    """Compare named points after callers establish a common coordinate frame.

    No implicit rotation/translation is performed. Both point sets must declare
    the same frame, and that frame must match the caller's explicit common-frame
    declaration. IDs identify correspondence only; coordinate values are still
    compared and required to fall within tolerance.
    """
    if not isfinite(tolerance_mm) or tolerance_mm < 0:
        raise ValueError("tolerance_mm must be finite and non-negative.")
    if source is None or target or common_coordinate_frame is None:
        if source is None or target is None or not common_coordinate_frame:
            return MountingGeometryAssessment(
                MountingGeometryStatus.INSUFFICIENT_DATA,
                ("Both mounting-point sets and a declared common frame are required.",),
                tolerance_mm,
            )
    if not source or not target:
        return MountingGeometryAssessment(
            MountingGeometryStatus.INSUFFICIENT_DATA,
            ("Both mounting-point sets must contain at least one point.",),
            tolerance_mm,
        )
    frames = {point.coordinate_frame for point in source + target}
    if len(frames) != 1 or common_coordinate_frame not in frames:
        return MountingGeometryAssessment(
            MountingGeometryStatus.DATUM_MISMATCH,
            ("Point sets do not share the explicitly declared coordinate frame.",),
            tolerance_mm,
        )
    if len(source) != len(target):
        return MountingGeometryAssessment(
            MountingGeometryStatus.POINT_COUNT_MISMATCH,
            ("Mounting-point set sizes differ.",),
            tolerance_mm,
        )

    source_by_id = {point.identifier: point for point in source}
    target_by_id = {point.identifier: point for point in target}
    if source_by_id.keys() != target_by_id.keys():
        return MountingGeometryAssessment(
            MountingGeometryStatus.IDENTIFIER_MISMATCH,
            ("Mounting-point identifiers do not establish a complete correspondence.",),
            tolerance_mm,
        )

    for identifier in sorted(source_by_id):
        first, second = source_by_id[identifier], target_by_id[identifier]
        if any(
            abs(a - b) > tolerance_mm
            for a, b in (
                (first.x_mm, second.x_mm),
                (first.y_mm, second.y_mm),
                (first.z_mm, second.z_mm),
            )
        ):
            return MountingGeometryAssessment(
                MountingGeometryStatus.GEOMETRY_MISMATCH,
                (f"Mounting point {identifier!r} differs beyond tolerance.",),
                tolerance_mm,
            )

    if any(
        point.evidence.level is not EvidenceLevel.CONFIRMED
        for point in source + target
    ):
        return MountingGeometryAssessment(
            MountingGeometryStatus.MATCH_REQUIRES_REVIEW,
            (
                "Coordinates compare within tolerance, but not all points are confirmed.",
                "Position match does not establish mount strength, loads, fasteners, "
                "welds, fatigue, vibration, material suitability, or vehicle safety.",
            ),
            tolerance_mm,
        )
    return MountingGeometryAssessment(
        MountingGeometryStatus.PRELIMINARY_GEOMETRY_MATCH,
        (
            "Corresponding mounting points compare within the declared coordinate tolerance.",
            "No coordinate transformation was solved; the caller must supply points "
            "already registered to the same validated datum.",
            "Structural design, load paths, fasteners, welds, fatigue and dynamic "
            "clearances remain unassessed.",
        ),
        tolerance_mm,
    )
