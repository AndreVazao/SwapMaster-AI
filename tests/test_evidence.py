import pytest

from swapmaster.domain.evidence import Evidence, EvidenceLevel


def test_confirmed_evidence_requires_traceability() -> None:
    with pytest.raises(ValueError, match="requires a source"):
        Evidence(level=EvidenceLevel.CONFIRMED)


def test_unknown_evidence_cannot_claim_source() -> None:
    with pytest.raises(ValueError, match="cannot claim"):
        Evidence(level=EvidenceLevel.UNKNOWN, source="somewhere")


def test_estimated_evidence_requires_review() -> None:
    evidence = Evidence(level=EvidenceLevel.ESTIMATED, method="rough estimate")
    assert evidence.requires_review
