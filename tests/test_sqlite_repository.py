import sqlite3
from datetime import UTC, datetime
from pathlib import Path

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
        field_path=field_path, value=value, unit=unit, evidence=evidence,
        uncertainty=uncertainty, revision=revision,
        recorded_at=recorded_at or datetime(2026, 11, 15, 12, 0, tzinfo=UTC),
        recorded_by="workshop-user", source_reference="report://measurement/123",
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
    repository.save(make_datum(520.0))
    with pytest.raises(RepositoryConflictError, match="Unit changes"):
        repository.save(make_datum(0.52, revision=2, unit=MeasurementUnit.KILOGRAM))
    with pytest.raises(RepositoryConflictError, match="chronological"):
        repository.save(make_datum(
            519.0, revision=2,
            recorded_at=datetime(2026, 11, 14, 12, 0, tzinfo=UTC),
        ))
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
            """INSERT INTO measurement_revisions
            (field_path, revision, value, unit, evidence_level, uncertainty)
            VALUES (?, ?, ?, ?, ?, ?)""",
            ("vehicle.mass", 1, 1000.0, "kg", "unknown", None),
        )
    database.close()


def test_database_constraints_reject_unsupported_units() -> None:
    database = SQLiteDatabase(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        database.connection.execute(
            """INSERT INTO measurement_revisions
            (field_path, revision, value, unit, evidence_level, evidence_source, uncertainty)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
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


def test_backup_and_restore_preserve_full_measurement_history(tmp_path) -> None:
    source_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backups" / "measurements.sqlite"
    restored_path = tmp_path / "restored.sqlite"
    database = SQLiteDatabase(source_path)
    repository = SQLiteMeasurementRepository(database.connection)
    first = make_datum(520.0)
    second = make_datum(521.0, revision=2, uncertainty=0.1)
    repository.save(first)
    repository.save(second)
    assert database.backup_to(backup_path) == backup_path.resolve()
    database.close()
    assert SQLiteDatabase.restore_from(backup_path, restored_path) == restored_path.resolve()
    restored = SQLiteDatabase(restored_path)
    history = SQLiteMeasurementRepository(restored.connection).get_history(first.field_path)
    assert history is not None
    assert history.revisions == (first, second)
    restored.close()


def test_backup_supports_in_memory_database(tmp_path) -> None:
    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    datum = make_datum(520.0)
    repository.save(datum)
    backup = tmp_path / "memory-backup.sqlite"
    database.backup_to(backup)
    database.close()
    restored = SQLiteDatabase(backup)
    assert SQLiteMeasurementRepository(restored.connection).get_latest(datum.field_path) == datum
    restored.close()


def test_backup_rejects_same_path_and_live_wal_destination(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "database.sqlite")
    destination = tmp_path / "existing-backup.sqlite"
    destination.write_bytes(b"previous-backup")
    with pytest.raises(ValueError, match="must differ"):
        database.backup_to(tmp_path / "database.sqlite")
    sidecar = Path(f"{destination}-wal")
    sidecar.touch()
    try:
        with pytest.raises(RuntimeError, match="WAL sidecars"):
            database.backup_to(destination)
        assert destination.read_bytes() == b"previous-backup"
    finally:
        sidecar.unlink()
        database.close()


def test_restore_rejects_corrupt_backup_without_changing_destination(tmp_path) -> None:
    corrupt = tmp_path / "corrupt.sqlite"
    corrupt.write_bytes(b"not a sqlite database")
    destination = tmp_path / "destination.sqlite"
    destination.write_bytes(b"keep-this-file")
    with pytest.raises(sqlite3.DatabaseError):
        SQLiteDatabase.restore_from(corrupt, destination)
    assert destination.read_bytes() == b"keep-this-file"


def test_restore_rejects_unsupported_schema_without_changing_destination(tmp_path) -> None:
    invalid = tmp_path / "future.sqlite"
    connection = sqlite3.connect(invalid)
    connection.execute("PRAGMA user_version = 99")
    connection.commit()
    connection.close()
    destination = tmp_path / "destination.sqlite"
    destination.write_bytes(b"keep-this-file")
    with pytest.raises(RuntimeError, match="Unsupported database schema"):
        SQLiteDatabase.restore_from(invalid, destination)
    assert destination.read_bytes() == b"keep-this-file"


def test_restore_rejects_destination_with_wal_sidecars(tmp_path) -> None:
    source = SQLiteDatabase(tmp_path / "source.sqlite")
    backup = tmp_path / "backup.sqlite"
    source.backup_to(backup)
    source.close()
    destination = tmp_path / "destination.sqlite"
    sidecar = Path(f"{destination}-shm")
    sidecar.touch()
    try:
        with pytest.raises(RuntimeError, match="WAL sidecars"):
            SQLiteDatabase.restore_from(backup, destination)
        assert not destination.exists()
    finally:
        sidecar.unlink()


def test_repository_imports_histories_atomically_without_overwriting() -> None:
    from swapmaster.domain.measurement import MeasurementHistory

    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    existing = make_datum(500.0, field_path="vehicle.mass")
    repository.save(existing)
    incoming = MeasurementHistory(
        "vehicle.engine_bay.length",
        (make_datum(520.0, field_path="vehicle.engine_bay.length"),),
    )
    conflicting = MeasurementHistory("vehicle.mass", (existing,))
    with pytest.raises(RepositoryConflictError, match="already exists"):
        repository.import_histories((incoming, conflicting))
    assert repository.get_history("vehicle.engine_bay.length") is None
    assert repository.get_latest("vehicle.mass") == existing
    repository.import_histories((incoming,))
    assert repository.get_history("vehicle.engine_bay.length") == incoming
    database.close()


def test_repository_import_rejects_duplicate_and_empty_batches() -> None:
    from swapmaster.domain.measurement import MeasurementHistory

    database = SQLiteDatabase(":memory:")
    repository = SQLiteMeasurementRepository(database.connection)
    datum = make_datum(520.0)
    history = MeasurementHistory(datum.field_path, (datum,))
    with pytest.raises(ValueError, match="At least one"):
        repository.import_histories(())
    with pytest.raises(ValueError, match="duplicate field paths"):
        repository.import_histories((history, history))
    assert repository.list_field_paths() == ()
    database.close()
