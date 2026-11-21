from datetime import UTC, datetime

import pytest

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.measurement import EngineeringDatum, MeasurementHistory, MeasurementUnit
from swapmaster.infrastructure.persistence.measurement_json import (
    FORMAT_NAME,
    export_measurement_histories,
    import_measurement_histories,
)

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="Calibrated report")
UNKNOWN = Evidence(EvidenceLevel.UNKNOWN)


def make_history(
    field_path: str = "vehicle.engine_bay.length",
    value: float | None = 520.0,
    evidence: Evidence = CONFIRMED,
) -> MeasurementHistory:
    datum = EngineeringDatum(
        field_path=field_path, value=value, unit=MeasurementUnit.MILLIMETRE,
        evidence=evidence, uncertainty=0.2 if value is not None else None,
        revision=1, recorded_at=datetime(2026, 11, 17, 6, 0, tzinfo=UTC),
        recorded_by="operator", source_reference="doc://source/42",
    )
    return MeasurementHistory(field_path, (datum,))


def test_export_import_round_trip_preserves_measurement_history() -> None:
    original = make_history()
    encoded = export_measurement_histories((original,))
    assert import_measurement_histories(encoded) == (original,)
    assert encoded.endswith("\n")
    assert FORMAT_NAME in encoded


def test_export_is_deterministic_and_sorts_histories() -> None:
    first = make_history("vehicle.mass", 1200.0)
    second = make_history("vehicle.engine_bay.length", 520.0)
    forward = export_measurement_histories((first, second))
    reverse = export_measurement_histories((second, first))
    assert forward == reverse
    assert tuple(item.field_path for item in import_measurement_histories(forward)) == (
        "vehicle.engine_bay.length", "vehicle.mass"
    )


def test_unknown_measurement_round_trips_without_inventing_value() -> None:
    unknown = make_history(value=None, evidence=UNKNOWN)
    assert import_measurement_histories(export_measurement_histories((unknown,))) == (unknown,)


def test_import_rejects_duplicate_json_keys() -> None:
    payload = (
        '{"format":"swapmaster.measurement-histories",'
        '"format":"swapmaster.measurement-histories",'
        '"schema_version":1,"histories":[]}'
    )
    with pytest.raises(ValueError, match="Duplicate JSON object key"):
        import_measurement_histories(payload)


def test_import_rejects_unknown_schema_version() -> None:
    payload = export_measurement_histories((make_history(),)).replace(
        '"schema_version": 1', '"schema_version": 2'
    )
    with pytest.raises(ValueError, match="Unsupported measurement schema version"):
        import_measurement_histories(payload)


def test_import_rejects_extra_keys_and_non_finite_numbers() -> None:
    payload = export_measurement_histories((make_history(),))
    with pytest.raises(ValueError, match="exactly these keys"):
        import_measurement_histories(payload.replace(
            '"format":', '"unexpected": true,\n  "format":', 1
        ))
    with pytest.raises(ValueError, match="Non-finite JSON number"):
        import_measurement_histories(payload.replace('"value": 520.0', '"value": NaN'))


def test_import_rejects_boolean_as_numeric_value() -> None:
    payload = export_measurement_histories((make_history(),)).replace(
        '"value": 520.0', '"value": true'
    )
    with pytest.raises(ValueError, match="finite number"):
        import_measurement_histories(payload)


def test_import_rejects_duplicate_field_paths() -> None:
    document = export_measurement_histories((make_history(),))
    history_object = document.split('"histories": [\n', 1)[1].rsplit('\n  ]', 1)[0]
    duplicated = document.replace(
        history_object, history_object + ',\n' + history_object, 1
    )
    with pytest.raises(ValueError, match="Duplicate field path"):
        import_measurement_histories(duplicated)


def test_import_rejects_naive_timestamp() -> None:
    payload = export_measurement_histories((make_history(),)).replace(
        '"2026-11-17T06:00:00+00:00"', '"2026-11-17T06:00:00"'
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        import_measurement_histories(payload)


def test_export_rejects_duplicate_histories() -> None:
    history = make_history()
    with pytest.raises(ValueError, match="duplicate field paths"):
        export_measurement_histories((history, history))


def test_import_rejects_empty_timestamp_instead_of_treating_it_as_missing() -> None:
    payload = export_measurement_histories((make_history(),)).replace(
        '"2026-11-17T06:00:00+00:00"', '""'
    )
    with pytest.raises(ValueError, match="Invalid isoformat string"):
        import_measurement_histories(payload)
