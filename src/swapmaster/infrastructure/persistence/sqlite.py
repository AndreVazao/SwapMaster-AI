"""SQLite persistence for immutable engineering measurement revisions."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.measurement import (
    EngineeringDatum,
    MeasurementHistory,
    MeasurementUnit,
)


class RepositoryConflictError(RuntimeError):
    """Raised when a caller attempts to overwrite or skip a measurement revision."""


class SQLiteDatabase:
    """Owns a SQLite connection and applies ordered schema migrations on open."""

    CURRENT_SCHEMA_VERSION = 1

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._closed = False
        try:
            self.migrate()
        except Exception:
            self._connection.close()
            self._closed = True
            raise

    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the managed connection to repositories in this process."""
        if self._closed:
            raise RuntimeError("Database connection is closed.")
        return self._connection

    @property
    def schema_version(self) -> int:
        """Return SQLite's applied user schema version."""
        row = self.connection.execute("PRAGMA user_version").fetchone()
        return int(row[0])

    def migrate(self) -> None:
        """Apply pending migrations atomically; refuse databases from newer versions."""
        with self.connection:
            version = self.schema_version
            if version > self.CURRENT_SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema {version} is newer than supported "
                    f"version {self.CURRENT_SCHEMA_VERSION}."
                )
            if version == 0:
                self._apply_v1()

    def _apply_v1(self) -> None:
        connection = self.connection
        connection.execute(
            """
            CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE measurement_revisions (
                field_path TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK (revision >= 1),
                value REAL,
                unit TEXT NOT NULL CHECK (
                    unit IN ('mm', 'kg', 'kW', 'Nm', 'V', 'A', 'rpm', 'degC')
                ),
                evidence_level TEXT NOT NULL CHECK (
                    evidence_level IN ('confirmed', 'documented', 'estimated', 'unknown')
                ),
                evidence_source TEXT,
                evidence_method TEXT,
                evidence_notes TEXT,
                uncertainty REAL CHECK (uncertainty IS NULL OR uncertainty >= 0),
                recorded_at TEXT,
                recorded_by TEXT,
                source_reference TEXT,
                PRIMARY KEY (field_path, revision),
                CHECK (
                    (value IS NULL AND evidence_level = 'unknown' AND uncertainty IS NULL)
                    OR
                    (value IS NOT NULL AND evidence_level != 'unknown')
                ),
                CHECK (
                    evidence_level != 'confirmed'
                    OR evidence_source IS NOT NULL
                    OR evidence_method IS NOT NULL
                )
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX idx_measurement_revisions_field
            ON measurement_revisions (field_path, revision)
            """
        )
        connection.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (1, datetime.now(UTC).isoformat()),
        )
        connection.execute("PRAGMA user_version = 1")

    def close(self) -> None:
        """Close the managed connection once."""
        if not self._closed:
            self._connection.close()
            self._closed = True


class SQLiteMeasurementRepository:
    """Append-only repository for field-level engineering measurements."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, datum: EngineeringDatum) -> None:
        """Persist exactly the next revision; never update or delete an existing row."""
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            row = self._connection.execute(
                """
                SELECT revision, unit
                FROM measurement_revisions
                WHERE field_path = ?
                ORDER BY revision DESC
                LIMIT 1
                """,
                (datum.field_path,),
            ).fetchone()
            latest_revision = int(row["revision"]) if row is not None else 0
            expected_revision = latest_revision + 1
            if datum.revision != expected_revision:
                raise RepositoryConflictError(
                    f"Expected revision {expected_revision} for {datum.field_path!r}; "
                    f"received {datum.revision}."
                )
            if row is not None and datum.unit.value != str(row["unit"]):
                raise RepositoryConflictError(
                    "Unit changes require an explicit migration, not a new revision."
                )

            previous_timestamp_row = self._connection.execute(
                """
                SELECT recorded_at
                FROM measurement_revisions
                WHERE field_path = ? AND recorded_at IS NOT NULL
                ORDER BY revision DESC
                LIMIT 1
                """,
                (datum.field_path,),
            ).fetchone()
            if (
                datum.recorded_at is not None
                and previous_timestamp_row is not None
                and previous_timestamp_row["recorded_at"] is not None
            ):
                previous_timestamp = datetime.fromisoformat(
                    str(previous_timestamp_row["recorded_at"])
                )
                if datum.recorded_at < previous_timestamp:
                    raise RepositoryConflictError(
                        "Revision timestamps must be chronological."
                    )

            self._connection.execute(
                """
                INSERT INTO measurement_revisions (
                    field_path, revision, value, unit, evidence_level,
                    evidence_source, evidence_method, evidence_notes,
                    uncertainty, recorded_at, recorded_by, source_reference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datum.field_path,
                    datum.revision,
                    datum.value,
                    datum.unit.value,
                    datum.evidence.level.value,
                    datum.evidence.source,
                    datum.evidence.method,
                    datum.evidence.notes,
                    datum.uncertainty,
                    datum.recorded_at.isoformat() if datum.recorded_at else None,
                    datum.recorded_by,
                    datum.source_reference,
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def get_history(self, field_path: str) -> MeasurementHistory | None:
        """Load all revisions for one field in ascending revision order."""
        rows = self._connection.execute(
            """
            SELECT *
            FROM measurement_revisions
            WHERE field_path = ?
            ORDER BY revision ASC
            """,
            (field_path,),
        ).fetchall()
        if not rows:
            return None
        revisions = tuple(self._row_to_datum(row) for row in rows)
        return MeasurementHistory(field_path, revisions)

    def get_latest(self, field_path: str) -> EngineeringDatum | None:
        """Load only the latest revision for a field."""
        row = self._connection.execute(
            """
            SELECT *
            FROM measurement_revisions
            WHERE field_path = ?
            ORDER BY revision DESC
            LIMIT 1
            """,
            (field_path,),
        ).fetchone()
        return self._row_to_datum(row) if row is not None else None

    def list_field_paths(self) -> tuple[str, ...]:
        """Return distinct field paths in deterministic order."""
        rows = self._connection.execute(
            "SELECT DISTINCT field_path FROM measurement_revisions ORDER BY field_path"
        ).fetchall()
        return tuple(str(row["field_path"]) for row in rows)

    @staticmethod
    def _row_to_datum(row: sqlite3.Row) -> EngineeringDatum:
        recorded_at_raw = row["recorded_at"]
        recorded_at = (
            datetime.fromisoformat(str(recorded_at_raw))
            if recorded_at_raw is not None
            else None
        )
        evidence = Evidence(
            level=EvidenceLevel(str(row["evidence_level"])),
            source=str(row["evidence_source"]) if row["evidence_source"] is not None else None,
            method=str(row["evidence_method"]) if row["evidence_method"] is not None else None,
            notes=str(row["evidence_notes"]) if row["evidence_notes"] is not None else None,
        )
        return EngineeringDatum(
            field_path=str(row["field_path"]),
            value=float(row["value"]) if row["value"] is not None else None,
            unit=MeasurementUnit(str(row["unit"])),
            evidence=evidence,
            uncertainty=(
                float(row["uncertainty"]) if row["uncertainty"] is not None else None
            ),
            revision=int(row["revision"]),
            recorded_at=recorded_at,
            recorded_by=str(row["recorded_by"]) if row["recorded_by"] is not None else None,
            source_reference=(
                str(row["source_reference"]) if row["source_reference"] is not None else None
            ),
        )
