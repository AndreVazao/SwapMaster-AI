"""Field-level engineering measurements and immutable revision history."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite

from swapmaster.domain.evidence import Evidence, EvidenceLevel


class MeasurementUnit(StrEnum):
    """Supported explicit units; values are never silently converted."""

    MILLIMETRE = "mm"
    KILOGRAM = "kg"
    KILOWATT = "kW"
    NEWTON_METRE = "Nm"
    VOLT = "V"
    AMPERE = "A"
    REVOLUTIONS_PER_MINUTE = "rpm"
    CELSIUS = "degC"


class DataReadiness(StrEnum):
    """Data gate outcome, not an engineering compatibility verdict."""

    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review_required"
    READY_FOR_ENGINEERING_REVIEW = "ready_for_engineering_review"


@dataclass(frozen=True, slots=True)
class EngineeringDatum:
    """One versioned field value with units, evidence, uncertainty and provenance."""

    field_path: str
    value: float | None
    unit: MeasurementUnit
    evidence: Evidence
    uncertainty: float | None = None
    revision: int = 1
    recorded_at: datetime | None = None
    recorded_by: str | None = None
    source_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.field_path.strip():
            raise ValueError("field_path cannot be empty.")
        if self.revision < 1:
            raise ValueError("revision must be a positive integer.")
        if self.value is None:
            if self.evidence.level is not EvidenceLevel.UNKNOWN:
                raise ValueError("A missing value must use UNKNOWN evidence.")
            if self.uncertainty is not None:
                raise ValueError("A missing value cannot have uncertainty.")
        else:
            if not isfinite(self.value):
                raise ValueError("value must be finite.")
            if self.evidence.level is EvidenceLevel.UNKNOWN:
                raise ValueError("A numeric value cannot use UNKNOWN evidence.")
            if self.uncertainty is not None:
                if not isfinite(self.uncertainty) or self.uncertainty < 0:
                    raise ValueError("uncertainty must be finite and non-negative.")
        if self.recorded_at is not None:
            if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
                raise ValueError("recorded_at must be timezone-aware.")
        for name in ("recorded_by", "source_reference"):
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise ValueError(f"{name} cannot be blank when supplied.")

    @property
    def uncertainty_interval(self) -> tuple[float, float] | None:
        """Return value ± absolute uncertainty in the declared unit, if known."""
        if self.value is None or self.uncertainty is None:
            return None
        return (self.value - self.uncertainty, self.value + self.uncertainty)


@dataclass(frozen=True, slots=True)
class MeasurementHistory:
    """Append-only revision sequence for one field; unit changes need explicit migration."""

    field_path: str
    revisions: tuple[EngineeringDatum, ...]

    def __post_init__(self) -> None:
        if not self.field_path.strip():
            raise ValueError("field_path cannot be empty.")
        if not self.revisions:
            raise ValueError("A measurement history requires at least one revision.")
        if any(item.field_path != self.field_path for item in self.revisions):
            raise ValueError("All revisions must refer to the history field_path.")
        if self.revisions[0].revision != 1:
            raise ValueError("Measurement history must begin at revision 1.")
        for expected, item in enumerate(self.revisions, start=1):
            if item.revision != expected:
                raise ValueError("Measurement revisions must be contiguous and ordered.")
        first_unit = self.revisions[0].unit
        if any(item.unit is not first_unit for item in self.revisions):
            raise ValueError("Unit changes require an explicit migration, not a new revision.")
        previous_time: datetime | None = None
        for item in self.revisions:
            if item.recorded_at is not None:
                if previous_time is not None and item.recorded_at < previous_time:
                    raise ValueError("Revision timestamps must be chronological.")
                previous_time = item.recorded_at

    @property
    def current(self) -> EngineeringDatum:
        """Return the latest immutable revision."""
        return self.revisions[-1]

    def append(self, datum: EngineeringDatum) -> MeasurementHistory:
        """Return a new history with the next revision; never mutate prior evidence."""
        if datum.field_path != self.field_path:
            raise ValueError("New revision field_path does not match this history.")
        if datum.revision != self.current.revision + 1:
            raise ValueError("New revision must increment the current revision by one.")
        if datum.unit is not self.current.unit:
            raise ValueError("Unit changes require an explicit migration.")
        return MeasurementHistory(self.field_path, (*self.revisions, datum))


@dataclass(frozen=True, slots=True)
class DataReadinessAssessment:
    status: DataReadiness
    missing_fields: tuple[str, ...]
    review_fields: tuple[str, ...]
    reasons: tuple[str, ...]


def assess_required_measurements(
    histories: Mapping[str, MeasurementHistory],
    required_fields: tuple[str, ...],
) -> DataReadinessAssessment:
    """Gate required inputs; never turn completeness into a fitment or safety approval."""
    if not required_fields:
        raise ValueError("At least one required field must be specified.")
    if len(required_fields) != len(set(required_fields)):
        raise ValueError("required_fields must not contain duplicates.")

    missing: list[str] = []
    review: list[str] = []
    for field_path in required_fields:
        history = histories.get(field_path)
        if history is None or history.current.value is None:
            missing.append(field_path)
            continue
        current = history.current
        if (
            current.evidence.level is not EvidenceLevel.CONFIRMED
            or current.uncertainty is None
        ):
            review.append(field_path)

    if missing:
        status = DataReadiness.BLOCKED
        reasons = ("Required engineering data is missing; positive assessment is blocked.",)
    elif review:
        status = DataReadiness.REVIEW_REQUIRED
        reasons = (
            "Some required values are not confirmed or have no stated uncertainty.",
            "Human engineering review remains mandatory.",
        )
    else:
        status = DataReadiness.READY_FOR_ENGINEERING_REVIEW
        reasons = (
            "Required fields have confirmed evidence and stated uncertainty.",
            "This is data readiness only, not fitment, structural, safety, or legal approval.",
        )

    return DataReadinessAssessment(status, tuple(missing), tuple(review), reasons)
