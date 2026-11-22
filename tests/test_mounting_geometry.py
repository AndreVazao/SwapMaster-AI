import pytest

from swapmaster.domain.catalog import MountingPoint
from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.mounting_geometry import (
    MountingGeometryStatus,
    assess_mounting_geometry,
)

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="measured and datum-registered")
ESTIMATED = Evidence(EvidenceLevel.ESTIMATED, method="estimated coordinates")


def points(offset: float = 0.0, evidence: Evidence = CONFIRMED, frame: str = "common-datum"):
    return (
        MountingPoint("left", 10 + offset, 20, 30, frame, evidence),
        MountingPoint("right", 110 + offset, 20, 30, frame, evidence),
        MountingPoint("rear", 60 + offset, -40, 30, frame, evidence),
    )


DEFAULT_POINTS = points()


def assess(first=DEFAULT_POINTS, second=DEFAULT_POINTS, frame="common-datum", tolerance=1.0):
    return assess_mounting_geometry(
        first, second, common_coordinate_frame=frame, tolerance_mm=tolerance
    )


def test_same_registered_points_are_preliminary_match_only():
    result = assess()
    assert result.status is MountingGeometryStatus.PRELIMINARY_GEOMETRY_MATCH
    assert "remain unassessed" in result.reasons[2]


def test_offset_beyond_tolerance_is_geometry_mismatch():
    result = assess(second=points(offset=2.0))
    assert result.status is MountingGeometryStatus.GEOMETRY_MISMATCH


def test_offset_within_tolerance_matches_preliminarily():
    result = assess(second=points(offset=0.5), tolerance=1.0)
    assert result.status is MountingGeometryStatus.PRELIMINARY_GEOMETRY_MATCH


def test_different_frames_block_comparison():
    result = assess(second=points(frame="engine-local"))
    assert result.status is MountingGeometryStatus.DATUM_MISMATCH


def test_frame_must_be_explicitly_declared_common_frame():
    result = assess(frame="vehicle-datum")
    assert result.status is MountingGeometryStatus.DATUM_MISMATCH


def test_missing_point_set_or_common_frame_blocks():
    result = assess(first=None)
    assert result.status is MountingGeometryStatus.INSUFFICIENT_DATA
    result = assess(frame=None)
    assert result.status is MountingGeometryStatus.INSUFFICIENT_DATA


def test_point_count_mismatch_is_detected():
    result = assess(second=points()[:2])
    assert result.status is MountingGeometryStatus.POINT_COUNT_MISMATCH


def test_identifiers_are_correspondence_not_geometry_proof():
    changed = (
        MountingPoint("left", 10, 20, 30, "common-datum", CONFIRMED),
        MountingPoint("right", 110, 20, 30, "common-datum", CONFIRMED),
        MountingPoint("rear", 60, -40, 31.1, "common-datum", CONFIRMED),
    )
    result = assess(second=changed)
    assert result.status is MountingGeometryStatus.GEOMETRY_MISMATCH


def test_different_ids_require_review_of_correspondence():
    changed = tuple(
        MountingPoint(f"new-{p.identifier}", p.x_mm, p.y_mm, p.z_mm, p.coordinate_frame, p.evidence)
        for p in points()
    )
    result = assess(second=changed)
    assert result.status is MountingGeometryStatus.IDENTIFIER_MISMATCH


def test_estimated_coordinates_require_review():
    result = assess(second=points(evidence=ESTIMATED))
    assert result.status is MountingGeometryStatus.MATCH_REQUIRES_REVIEW


def test_invalid_tolerance_rejected():
    with pytest.raises(ValueError, match="tolerance_mm"):
        assess(tolerance=float("nan"))
