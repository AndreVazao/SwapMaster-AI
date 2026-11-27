"""Application use cases for evidence-aware measurement workflows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from swapmaster.domain.measurement import (
    DataReadinessAssessment,
    EngineeringDatum,
    MeasurementHistory,
    assess_required_measurements,
)
from swapmaster.infrastructure.persistence.measurement_json import (
    export_measurement_histories,
    import_measurement_histories,
)


class MeasurementRepository(Protocol):
    """Persistence contract required by the measurement application service."""

    def save(self, datum: EngineeringDatum) -> None: ...

    def get_history(self, field_path: str) -> MeasurementHistory | None: ...

    def list_field_paths(self) -> tuple[str, ...]: ...

    def import_histories(self, histories: tuple[MeasurementHistory, ...]) -> None: ...


class MeasurementService:
    """Orchestrate measurement use cases without exposing SQLite to the UI."""

    def __init__(self, repository: MeasurementRepository) -> None:
        self._repository = repository

    def record(self, datum: EngineeringDatum) -> MeasurementHistory:
        """Append one revision after validating it against the current domain history."""
        history = self._repository.get_history(datum.field_path)
        if history is not None:
            history.append(datum)
        elif datum.revision != 1:
            raise ValueError("The first measurement revision must be 1.")
        self._repository.save(datum)
        saved = self._repository.get_history(datum.field_path)
        if saved is None:
            raise RuntimeError("Repository did not return the measurement it saved.")
        return saved

    def get_history(self, field_path: str) -> MeasurementHistory | None:
        """Retrieve the complete immutable history for one field."""
        if not field_path.strip():
            raise ValueError("field_path cannot be empty.")
        return self._repository.get_history(field_path)

    def export_json(self) -> str:
        """Export every stored history in deterministic schema-v1 JSON."""
        histories = tuple(
            history
            for field_path in self._repository.list_field_paths()
            if (history := self._repository.get_history(field_path)) is not None
        )
        return export_measurement_histories(histories)

    def import_json(self, payload: str) -> tuple[MeasurementHistory, ...]:
        """Validate and import a complete JSON document without overwriting existing data."""
        histories = import_measurement_histories(payload)
        if histories:
            self._repository.import_histories(histories)
        return histories

    def assess_readiness(
        self, required_fields: tuple[str, ...]
    ) -> DataReadinessAssessment:
        """Assess completeness/evidence only; this is not a fitment or safety approval."""
        histories: Mapping[str, MeasurementHistory] = {
            field_path: history
            for field_path in required_fields
            if (history := self._repository.get_history(field_path)) is not None
        }
        return assess_required_measurements(histories, required_fields)
