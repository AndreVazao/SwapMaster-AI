import pytest

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.interface_geometry import (
    GeometryMatchStatus,
    HoleCentre,
    InterfaceGeometry,
    assess_interface_geometry,
)


CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="measured inspection drawing")
ESTIMATED = Evidence(EvidenceLevel.ESTIMATED, method="unverified estimate")


def geometry(
    shift: float = 0.0,
    evidence: Evidence = CONFIRMED,
    frame: str = "bellhousing-face-A",
) -> InterfaceGeometry:
    return InterfaceGeometry(
        "engine-to-gearbox",
        frame,
        (
            HoleCentre(0 + shift, 0, 10),
            HoleCentre(100 + shift, 0, 10),
            HoleCentre(50 + shift, 80, 10),
        ),
        75,
        evidence,
    )


def test_identical_measured_patterns_are_only_preliminary_match() -> None:
    result = assess_interface_geometry(geometry(), geometry())
    assert result.status is GeometryMatchStatus.PRELIMINARY_GEOMETRY_MATCH
    assert "remain unverified" in result.reasons[1]


def test_hole_pattern_difference_is_detected() -> None:
    result = assess_interface_geometry(geometry(), geometry(shift=1.0))
    assert result.status is GeometryMatchStatus.HOLE_PATTERN_MISMATCH


def test_different_datums_are_not_compared() -> None:
    result = assess_interface_geometry(geometry(), geometry(frame="other-datum"))
    assert result.status is GeometryMatchStatus.DATUM_MISMATCH


def test_missing_pilot_measurement_blocks_match() -> None:
    target = InterfaceGeometry(
        "engine-to-gearbox", "bellhousing-face-A", geometry().holes, None, CONFIRMED
    )
    result = assess_interface_geometry(geometry(), target)
    assert result.status is GeometryMatchStatus.INSUFFICIENT_DATA


def test_estimated_geometry_requires_review() -> None:
    result = assess_interface_geometry(geometry(evidence=ESTIMATED), geometry())
    assert result.status is GeometryMatchStatus.MATCH_REQUIRES_REVIEW


def test_tolerance_must_be_finite_and_non_negative() -> None:
    with pytest.raises(ValueError, match="Tolerance"):
        assess_interface_geometry(geometry(), geometry(), float("nan"))
