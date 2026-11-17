"""Strict, versioned JSON interchange for measurement histories."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from math import isfinite
from typing import NoReturn

from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.measurement import EngineeringDatum, MeasurementHistory, MeasurementUnit

FORMAT_NAME = "swapmaster.measurement-histories"
SCHEMA_VERSION = 1


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key!r}.")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ValueError(f"Non-finite JSON number is not allowed: {value}.")


def _object_with_keys(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} must contain exactly these keys: {sorted(expected)}.")
    return value


def _optional_text(value: object, label: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{label} must be a string or null.")
    return value


def export_measurement_histories(histories: Iterable[MeasurementHistory]) -> str:
    """Serialize histories as deterministic, versioned JSON."""
    ordered = tuple(sorted(histories, key=lambda history: history.field_path))
    paths = tuple(history.field_path for history in ordered)
    if len(paths) != len(set(paths)):
        raise ValueError("Export contains duplicate field paths.")
    document = {
        "format": FORMAT_NAME,
        "schema_version": SCHEMA_VERSION,
        "histories": [
            {
                "field_path": history.field_path,
                "revisions": [
                    {
                        "field_path": datum.field_path,
                        "value": datum.value,
                        "unit": datum.unit.value,
                        "evidence": {
                            "level": datum.evidence.level.value,
                            "source": datum.evidence.source,
                            "method": datum.evidence.method,
                            "notes": datum.evidence.notes,
                        },
                        "uncertainty": datum.uncertainty,
                        "revision": datum.revision,
                        "recorded_at": (
                            datum.recorded_at.isoformat()
                            if datum.recorded_at is not None else None
                        ),
                        "recorded_by": datum.recorded_by,
                        "source_reference": datum.source_reference,
                    }
                    for datum in history.revisions
                ],
            }
            for history in ordered
        ],
    }
    return json.dumps(
        document, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True
    ) + "\n"


def import_measurement_histories(payload: str) -> tuple[MeasurementHistory, ...]:
    """Parse strict schema-v1 JSON and validate records through domain models."""
    if not isinstance(payload, str):
        raise ValueError("JSON payload must be text.")
    try:
        raw = json.loads(
            payload, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
        root = _object_with_keys(raw, {"format", "schema_version", "histories"}, "Document")
        if root["format"] != FORMAT_NAME:
            raise ValueError("Unrecognized measurement export format.")
        version = root["schema_version"]
        if type(version) is not int or version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported measurement schema version: {version!r}.")
        raw_histories = root["histories"]
        if not isinstance(raw_histories, list):
            raise ValueError("histories must be an array.")

        histories: list[MeasurementHistory] = []
        seen_paths: set[str] = set()
        for hi, raw_history in enumerate(raw_histories):
            label = f"histories[{hi}]"
            history_data = _object_with_keys(raw_history, {"field_path", "revisions"}, label)
            field_path = history_data["field_path"]
            if not isinstance(field_path, str) or not field_path.strip():
                raise ValueError(f"{label}.field_path must be non-empty text.")
            if field_path in seen_paths:
                raise ValueError(f"Duplicate field path in import: {field_path!r}.")
            seen_paths.add(field_path)
            raw_revisions = history_data["revisions"]
            if not isinstance(raw_revisions, list) or not raw_revisions:
                raise ValueError(f"{label}.revisions must be a non-empty array.")

            revisions: list[EngineeringDatum] = []
            for ri, raw_datum in enumerate(raw_revisions):
                datum_label = f"{label}.revisions[{ri}]"
                datum = _object_with_keys(
                    raw_datum,
                    {
                        "field_path", "value", "unit", "evidence", "uncertainty",
                        "revision", "recorded_at", "recorded_by", "source_reference",
                    },
                    datum_label,
                )
                if datum["field_path"] != field_path:
                    raise ValueError(f"{datum_label}.field_path does not match its history.")
                value = datum["value"]
                if value is not None:
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise ValueError(
                            f"{datum_label}.value must be a finite number or null."
                        )
                    if not isfinite(value):
                        raise ValueError(
                            f"{datum_label}.value must be a finite number or null."
                        )
                uncertainty = datum["uncertainty"]
                if uncertainty is not None:
                    if isinstance(uncertainty, bool) or not isinstance(
                        uncertainty, (int, float)
                    ):
                        raise ValueError(
                            f"{datum_label}.uncertainty must be a finite number or null."
                        )
                    if not isfinite(uncertainty):
                        raise ValueError(
                            f"{datum_label}.uncertainty must be a finite number or null."
                        )
                revision = datum["revision"]
                if type(revision) is not int:
                    raise ValueError(f"{datum_label}.revision must be an integer.")
                unit = datum["unit"]
                if not isinstance(unit, str):
                    raise ValueError(f"{datum_label}.unit must be text.")
                evidence_data = _object_with_keys(
                    datum["evidence"], {"level", "source", "method", "notes"},
                    f"{datum_label}.evidence",
                )
                level = evidence_data["level"]
                if not isinstance(level, str):
                    raise ValueError(f"{datum_label}.evidence.level must be text.")
                timestamp = datum["recorded_at"]
                if timestamp is not None and not isinstance(timestamp, str):
                    raise ValueError(f"{datum_label}.recorded_at must be text or null.")
                revisions.append(
                    EngineeringDatum(
                        field_path=field_path,
                        value=float(value) if value is not None else None,
                        unit=MeasurementUnit(unit),
                        evidence=Evidence(
                            level=EvidenceLevel(level),
                            source=_optional_text(evidence_data["source"], "evidence.source"),
                            method=_optional_text(evidence_data["method"], "evidence.method"),
                            notes=_optional_text(evidence_data["notes"], "evidence.notes"),
                        ),
                        uncertainty=float(uncertainty) if uncertainty is not None else None,
                        revision=revision,
                        recorded_at=(
                            datetime.fromisoformat(timestamp)
                            if timestamp is not None else None
                        ),
                        recorded_by=_optional_text(datum["recorded_by"], "recorded_by"),
                        source_reference=_optional_text(
                            datum["source_reference"], "source_reference"
                        ),
                    )
                )
            histories.append(MeasurementHistory(field_path, tuple(revisions)))
        return tuple(sorted(histories, key=lambda history: history.field_path))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid measurement export JSON: {error.msg}.") from error
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError(f"Invalid measurement export: {error}.") from error
    except ValueError as error:
        if str(error).startswith("Invalid measurement export"):
            raise
        raise ValueError(f"Invalid measurement export: {error}") from error
