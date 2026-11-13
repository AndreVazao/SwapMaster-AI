"""Evidence metadata used to prevent estimates being presented as verified facts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvidenceLevel(StrEnum):
    """Strength of the evidence supporting an engineering value."""

    CONFIRMED = "confirmed"
    DOCUMENTED = "documented"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Evidence:
    """Traceability metadata for a measured or sourced engineering value."""

    level: EvidenceLevel
    source: str | None = None
    method: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.level is EvidenceLevel.CONFIRMED and not (self.source or self.method):
            raise ValueError("Confirmed evidence requires a source or measurement method.")
        if self.level is EvidenceLevel.UNKNOWN and (self.source or self.method):
            raise ValueError("Unknown evidence cannot claim a source or measurement method.")

    @property
    def requires_review(self) -> bool:
        """Whether this evidence is insufficient for an engineering approval."""
        return self.level is not EvidenceLevel.CONFIRMED
