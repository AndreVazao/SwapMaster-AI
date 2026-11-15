from datetime import datetime

import pytest

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.measurement import (
    DataReadiness,
    EngineeringDatum,
    MeasurementHistory,
    MeasurementUnit,
    assess_required_measurements,
)

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="Calibrated measurement report")
ESTIMATED = Evidence(EvidenceLevel.ESTIMATED, method="Preliminary estimate")
UNKNOWN = Evidence(EvidenceLevel.UNKNOWN)


def datum(
    value: float | None,
    *,
    revision: int = 1,
    evidence: Evidence = CONFIRMED,
    uncertainty: float | None = 0.5,
    unit: MeasurementUnit = MeasurementUnit.MILLIMETRE,
    field_path: str = "vehicle.engine_bay.length",
) -> EngineeringDatum:
    return EngineeringDatum(
        field_path=field_path,
        value=value,
        unit=unit,
        evidence=evidence,
        uncertainty=uncertainty,
        revision=revision,
    )


def test_datum_calculates_uncertainty_interval() -> None:
    measured = datum(100.0, uncertainty=1.25)
    assert measured.uncertainty_interval == (98.75, 101.25)


def test_datum_without_uncertainty_has_no_interval() -> None:
    assert datum(100.0, uncertainty=None).uncertainty_interval is None


def test_missing_value_requires_unknown_evidence() -> None:
    with pytest.raises(ValueError, match="UNKNOWN"):
        datum(None)


def test_unknown_evidence_cannot_claim_numeric_value() -> None:
    with pytest.raises(ValueError, match="UNKNOWN"):
        datum(10.0, evidence=UNKNOWN)


def test_non_finite_values_and_negative_uncertainty_are_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        datum(float("inf"))
    with pytest.raises(ValueError, match="uncertainty"):
        datum(10.0, uncertainty=-0.1)


def test_timestamp_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        EngineeringDatum(
            "vehicle.mass",
            1000.0,
            MeasurementUnit.KILOGRAM,
            CONFIRMED,
            recorded_at=datetime(2026, 1, 1),
        )


def test_history_requires_contiguous_revisions_and_same_unit() -> None:
    first = datum(100.0)
    second = datum(101.0, revision=2)
    history = MeasurementHistory(first.field_path, (first, second))
    assert history.current.value == 101.0

    with pytest.raises(ValueError, match="contiguous"):
        MeasurementHistory(first.field_path, (first, datum(102.0, revision=3)))

    changed_unit = datum(
        1.0,
        revision=2,
        unit=MeasurementUnit.KILOGRAM,
    )
    with pytest.raises(ValueError, match="Unit changes"):
        MeasurementHistory(first.field_path, (first, changed_unit))


def test_append_returns_new_immutable_history() -> None:
    first = datum(100.0)
    history = MeasurementHistory(first.field_path, (first,))
    updated = history.append(datum(99.5, revision=2))
    assert len(history.revisions) == 1
    assert len(updated.revisions) == 2
    assert updated.current.value == 99.5


def test_append_rejects_wrong_revision_or_field() -> None:
    first = datum(100.0)
    history = MeasurementHistory(first.field_path, (first,))
    with pytest.raises(ValueError, match="increment"):
        history.append(datum(101.0))
    with pytest.raises(ValueError, match="field_path"):
        history.append(datum(101.0, revision=2, field_path="vehicle.mass"))


def test_missing_required_measurement_blocks_readiness() -> None:
    history = MeasurementHistory(
        "vehicle.engine_bay.length",
        (datum(200.0),),
    )
    result = assess_required_measurements(
        {"vehicle.engine_bay.length": history},
        ("vehicle.engine_bay.length", "vehicle.engine_bay.width"),
    )
    assert result.status is DataReadiness.BLOCKED
    assert result.missing_fields == ("vehicle.engine_bay.width",)


def test_estimated_or_uncertainty_free_data_requires_review() -> None:
    length = MeasurementHistory(
        "vehicle.engine_bay.length",
        (datum(100.0, evidence=ESTIMATED),),
    )
    width = MeasurementHistory(
        "vehicle.engine_bay.width",
        (datum(50.0, uncertainty=None, field_path="vehicle.engine_bay.width"),),
    )
    result = assess_required_measurements(
        {
            "vehicle.engine_bay.length": length,
            "vehicle.engine_bay.width": width,
        },
        ("vehicle.engine_bay.length", "vehicle.engine_bay.width"),
    )
    assert result.status is DataReadiness.REVIEW_REQUIRED
    assert result.review_fields == (
        "vehicle.engine_bay.length",
        "vehicle.engine_bay.width",
    )


def test_confirmed_data_is_ready_only_for_engineering_review() -> None:
    history = MeasurementHistory(
        "vehicle.engine_bay.length",
        (datum(100.0),),
    )
    result = assess_required_measurements(
        {"vehicle.engine_bay.length": history},
        ("vehicle.engine_bay.length",),
    )
    assert result.status is DataReadiness.READY_FOR_ENGINEERING_REVIEW
    assert "not fitment" in result.reasons[1]


def test_required_fields_must_be_non_empty_and_unique() -> None:
    with pytest.raises(ValueError, match="At least one"):
        assess_required_measurements({}, ())
    with pytest.raises(ValueError, match="duplicates"):
        assess_required_measurements({}, ("vehicle.mass", "vehicle.mass"))
