from datetime import UTC, datetime

import pytest

from swapmaster.application.measurement_service import MeasurementService

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.measurement import (
    DataReadiness,
    EngineeringDatum,
    MeasurementUnit,
)
from swapmaster.infrastructure.persistence.sqlite import (
    RepositoryConflictError,
    SQLiteDatabase,
    SQLiteMeasurementRepository,
)

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="Calibrated workshop report")


def datum(value: float, revision: int = 1) -> EngineeringDatum:
    return EngineeringDatum(
        field_path="vehicle.engine_bay.length",
        value=value,
        unit=MeasurementUnit.MILLIMETRE,
        evidence=CONFIRMED,
        uncertainty=0.2,
        revision=revision,
        recorded_at=datetime(2026, 11, 17, 6, 0, tzinfo=UTC),
        recorded_by="workshop",
    )


def make_service() -> tuple[SQLiteDatabase, MeasurementService]:
    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    return database, MeasurementService(repository)


def test_service_records_and_appends_measurement_revisions() -> None:
    database, service = make_service()
    first = datum(520.0)
    second = datum(521.0, revision=2)

    original = service.record(first)
    updated = service.record(second)

    assert original.revisions == (first,)
    assert updated.revisions == (first, second)
    assert service.get_history(first.field_path) == updated
    database.close()


def test_service_rejects_invalid_revision_before_persistence() -> None:
    database, service = make_service()
    first = datum(520.0)
    service.record(first)

    with pytest.raises(ValueError, match="increment"):
        service.record(datum(521.0, revision=3))

    assert service.get_history(first.field_path) is not None
    assert len(service.get_history(first.field_path).revisions) == 1
    database.close()


def test_service_rejects_first_revision_gap() -> None:
    database, service = make_service()
    with pytest.raises(ValueError, match="first measurement revision"):
        service.record(datum(520.0, revision=2))
    assert service.get_history("vehicle.engine_bay.length") is None
    database.close()


def test_service_exports_and_imports_json_without_overwriting() -> None:
    source_db, source_service = make_service()
    first = datum(520.0)
    source_service.record(first)
    source_service.record(datum(521.0, revision=2))
    payload = source_service.export_json()

    target_db, target_service = make_service()
    imported = target_service.import_json(payload)
    assert imported == (source_service.get_history(first.field_path),)
    assert target_service.export_json() == payload

    with pytest.raises(RepositoryConflictError, match="already exists"):
        target_service.import_json(payload)
    source_db.close()
    target_db.close()


def test_service_readiness_is_data_gate_not_engineering_approval() -> None:
    database, service = make_service()
    service.record(datum(520.0))
    result = service.assess_readiness(("vehicle.engine_bay.length", "vehicle.mass"))
    assert result.status is DataReadiness.BLOCKED
    assert result.missing_fields == ("vehicle.mass",)
    database.close()


def test_service_rejects_blank_field_path() -> None:
    database, service = make_service()
    with pytest.raises(ValueError, match="cannot be empty"):
        service.get_history(" ")
    database.close()
