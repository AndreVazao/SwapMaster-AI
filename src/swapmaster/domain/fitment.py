"""Conservative preliminary envelope comparison; not a vehicle fitment approval."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import EvidenceLevel


class FitmentStatus(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    GEOMETRY_EXCEEDS_ENVELOPE = "geometry_exceeds_envelope"
    GEOMETRY_WITHIN_ENVELOPE_REQUIRES_REVIEW = "geometry_within_envelope_requires_review"
    PRELIMINARY_GEOMETRY_PASS = "preliminary_geometry_pass"


@dataclass(frozen=True, slots=True)
class FitmentAssessment:
    status: FitmentStatus
    reasons: tuple[str, ...]
    disclaimer: str = (
        "A packaging-envelope comparison is not proof of fitment, structural safety, "
        "drivetrain alignment, serviceability, roadworthiness, or legal compliance."
    )


def assess_envelope(
    component: Envelope3D | None,
    available_space: Envelope3D | None,
    clearance_mm: float = 0.0,
) -> FitmentAssessment:
    """Compare bounding boxes only; any non-confirmed evidence forces review."""
    if component is None or available_space is None:
        return FitmentAssessment(
            FitmentStatus.INSUFFICIENT_DATA,
            ("Component or available-space dimensions are missing.",),
        )

    if not component.fits_inside(available_space, clearance_mm):
        return FitmentAssessment(
            FitmentStatus.GEOMETRY_EXCEEDS_ENVELOPE,
            ("The component bounding box exceeds at least one available dimension.",),
        )

    if (
        component.evidence.level is not EvidenceLevel.CONFIRMED
        or available_space.evidence.level is not EvidenceLevel.CONFIRMED
    ):
        return FitmentAssessment(
            FitmentStatus.GEOMETRY_WITHIN_ENVELOPE_REQUIRES_REVIEW,
            ("Bounding boxes compare within limits, but one or both inputs are not confirmed.",),
        )

    return FitmentAssessment(
        FitmentStatus.PRELIMINARY_GEOMETRY_PASS,
        (
            "Confirmed axis-aligned dimensions fit with the requested clearance.",
            "All other mechanical, structural, thermal, electrical, and legal checks remain open.",
        ),
    )
