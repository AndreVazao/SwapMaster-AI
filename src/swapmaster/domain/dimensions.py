"""Validated metric dimensions for preliminary packaging checks."""

from __future__ import annotations

from dataclasses import dataclass

from swapmaster.domain.evidence import Evidence


@dataclass(frozen=True, slots=True)
class Envelope3D:
    """Axis-aligned rectangular envelope, expressed in millimetres."""

    length_mm: float
    width_mm: float
    height_mm: float
    evidence: Evidence

    def __post_init__(self) -> None:
        for field_name in ("length_mm", "width_mm", "height_mm"):
            value = getattr(self, field_name)
            if value <= 0:
                raise ValueError(f"{field_name} must be greater than zero.")
            if not float(value) < float("inf"):
                raise ValueError(f"{field_name} must be finite.")

    def fits_inside(self, available: Envelope3D, clearance_mm: float = 0.0) -> bool:
        """Return whether this envelope fits within another axis-aligned envelope."""
        if clearance_mm < 0:
            raise ValueError("clearance_mm cannot be negative.")
        return (
            self.length_mm + 2 * clearance_mm <= available.length_mm
            and self.width_mm + 2 * clearance_mm <= available.width_mm
            and self.height_mm + 2 * clearance_mm <= available.height_mm
        )
