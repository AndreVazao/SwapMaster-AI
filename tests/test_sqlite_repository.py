from datetime import UTC, datetime
import sqlite3

import pytest

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.measurement import EngineeringDatum, MeasurementUnit
from swapmaster.infrastructure.persistence.sqlite import (
    RepositoryConflictError,
    SQLiteDatabase,
    SQLiteMeasurementRepository,
)

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="Calibrated workshop report")
UNKNOWN = Evidence(EvidenceLevel.UNKNOWN)


def make_datum(
    value: float | None,
    *,
    revision: int = 1,
    uncertainty: float | None = 0.2,
    evidence: Evidence = CONFIRMED,
    field_path: str = "vehicle.engine_bay.length",
    unit: MeasurementUnit = MeasurementUnit.MILLIMETRE,
    recorded_at: datetime | None = None,
) -> EngineeringDatum:
    return EngineeringDatum(
        field_path=field_path,
        value=value,
        unit=unit,
        evidence=evidence,
        uncertainty=uncertainty,
        revision=revision,
        recorded_at=recorded_at or datetime(2026, 11, 15, 12, 0, tzinfo=UTC),
        recorded_by="workshop-user",
        source_reference="report://measurement/123",
    )


def test_database_applies_v1_migration_and_is_idempotent(tmp_path) -> None:
    database_path = tmp_path / "data" / "swapmaster.sqlite"
    database = SQLiteDatabase(database_path)
    assert database.schema_version == 1
    database.migrate()
    assert database.schema_version == 1
    database.close()

    reopened = SQLiteDatabase(database_path)
    assert reopened.schema_version == 1
    reopened.close()


def test_repository_round_trips_measurement_history(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "measurements.sqlite")
    repository = SQLiteMeasurementRepository(database.connection)
    first = make_datum(520.0)
    second = make_datum(521.0, revision=2, uncertainty=0.1)

    repository.save(first)
    repository.save(second)

    history = repository.get_history(first.field_path)
    assert history is not None
    assert len(history.revisions) == 2
    assert history.current.value == 521.0
    assert history.current.recorded_by == "workshop-user"
    assert history.current.source_reference == "report://measurement/123"
    assert history.current.recorded_at == second.recorded_at
    assert repository.get_latest(first.field_path) == second
    assert repository.list_field_paths() == (first.field_path,)
    database.close()


def test_repository_rejects_overwrite_and_revision_gaps() -> None:
    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    first = make_datum(520.0)
    repository.save(first)

    with pytest.raises(RepositoryConflictError, match="Expected revision 2"):
        repository.save(first)
    with pytest.raises(RepositoryConflictError, match="Expected revision 2"):
        repository.save(make_datum(522.0, revision=3))

    history = repository.get_history(first.field_path)
    assert history is not None
    assert len(history.revisions) == 1
    database.close()


def test_repository_rejects_unit_changes_and_reversed_timestamps() -> None:
    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    first = make_datum(520.0)
    repository.save(first)

    with pytest.raises(RepositoryConflictError, match="Unit changes"):
        repository.save(make_datum(0.52, revision=2, unit=MeasurementUnit.KILOGRAM))
    with pytest.raises(RepositoryConflictError, match="chronological"):
        repository.save(
            make_datum(
                519.0,
                revision=2,
                recorded_at=datetime(2026, 11, 14, 12, 0, tzinfo=UTC),
            )
        )
    database.close()


def test_repository_persists_explicit_unknown_values() -> None:
    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    unknown = make_datum(None, uncertainty=None, evidence=UNKNOWN)

    repository.save(unknown)

    loaded = repository.get_latest(unknown.field_path)
    assert loaded == unknown
    assert loaded is not None
    assert loaded.evidence.level is EvidenceLevel.UNKNOWN
    database.close()


def test_database_constraints_reject_invalid_unknown_numeric_record() -> None:
    database = SQLiteDatabase(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        database.connection.execute(
            """
            INSERT INTO measurement_revisions (
                field_path, revision, value, unit, evidence_level, uncertainty
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("vehicle.mass", 1, 1000.0, "kg", "unknown", None),
        )
    database.close()


def test_database_constraints_reject_unsupported_units() -> None:
    database = SQLiteDatabase(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        database.connection.execute(
            """
            INSERT INTO measurement_revisions (
                field_path, revision, value, unit, evidence_level,
                evidence_source, uncertainty
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("vehicle.mass", 1, 1000.0, "furlong", "confirmed", "test source", 1.0),
        )
    database.close()


def test_repository_returns_none_for_unknown_field() -> None:
    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    assert repository.get_history("not.present") is None
    assert repository.get_latest("not.present") is None
    assert repository.list_field_paths() == ()
    database.close()
