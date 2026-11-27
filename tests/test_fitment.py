from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.fitment import FitmentStatus, assess_envelope


def dimensions(level: EvidenceLevel, source: str | None = None) -> Envelope3D:
    return Envelope3D(
        400,
        300,
        250,
        Evidence(level=level, source=source),
    )


def test_missing_dimensions_are_not_compatible() -> None:
    result = assess_envelope(None, dimensions(EvidenceLevel.CONFIRMED, "vehicle scan"))
    assert result.status is FitmentStatus.INSUFFICIENT_DATA


def test_oversized_component_is_rejected() -> None:
    component = dimensions(EvidenceLevel.CONFIRMED, "datasheet")
    space = Envelope3D(
        350,
        300,
        250,
        Evidence(EvidenceLevel.CONFIRMED, source="measured bay"),
    )
    assert assess_envelope(component, space).status is FitmentStatus.GEOMETRY_EXCEEDS_ENVELOPE


def test_estimated_dimensions_never_produce_confirmed_pass() -> None:
    result = assess_envelope(
        dimensions(EvidenceLevel.ESTIMATED),
        dimensions(EvidenceLevel.CONFIRMED, "measured bay"),
    )
    assert result.status is FitmentStatus.GEOMETRY_WITHIN_ENVELOPE_REQUIRES_REVIEW


def test_confirmed_envelope_comparison_is_only_preliminary() -> None:
    result = assess_envelope(
        dimensions(EvidenceLevel.CONFIRMED, "manufacturer drawing"),
        dimensions(EvidenceLevel.CONFIRMED, "3D measurement"),
    )
    assert result.status is FitmentStatus.PRELIMINARY_GEOMETRY_PASS
    assert "not proof of fitment" in result.disclaimer
