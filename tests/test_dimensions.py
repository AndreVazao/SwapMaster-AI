import pytest

from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence, EvidenceLevel


def envelope(length: float, width: float, height: float) -> Envelope3D:
    return Envelope3D(
        length,
        width,
        height,
        Evidence(EvidenceLevel.CONFIRMED, source="test fixture"),
    )


def test_envelope_fits_with_clearance() -> None:
    assert envelope(90, 90, 90).fits_inside(envelope(100, 100, 100), 5)


def test_envelope_does_not_fit_when_clearance_exceeds_space() -> None:
    assert not envelope(91, 90, 90).fits_inside(envelope(100, 100, 100), 5)


def test_negative_clearance_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        envelope(10, 10, 10).fits_inside(envelope(20, 20, 20), -1)


def test_non_positive_dimension_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        envelope(0, 10, 10)
