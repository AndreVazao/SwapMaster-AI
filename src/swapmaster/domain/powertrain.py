"""Typed vehicle, power-unit, gearbox and mechanical-interface models.

All dimensions use millimetres, mass uses kilograms, and torque uses newton-metres.
These models store supplied data; they do not imply that a vehicle conversion is safe.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence


class PowertrainType(StrEnum):
    ICE_PETROL = "ice_petrol"
    ICE_DIESEL = "ice_diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    OTHER = "other"


class TransmissionType(StrEnum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    DCT = "dct"
    CVT = "cvt"
    SINGLE_SPEED = "single_speed"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Coordinate3D:
    """Point in a named coordinate system, expressed in millimetres."""

    x_mm: float
    y_mm: float
    z_mm: float

    def __post_init__(self) -> None:
        for name in ("x_mm", "y_mm", "z_mm"):
            value = getattr(self, name)
            if value != value or abs(value) == float("inf"):
                raise ValueError(f"{name} must be finite.")


@dataclass(frozen=True, slots=True)
class BoltHole:
    """A hole centre and nominal diameter in a shared interface coordinate frame."""

    centre: Coordinate3D
    diameter_mm: float

    def __post_init__(self) -> None:
        if self.diameter_mm <= 0 or self.diameter_mm == float("inf"):
            raise ValueError("Hole diameter must be finite and greater than zero.")


@dataclass(frozen=True, slots=True)
class MechanicalInterface:
    """Mating interface definition; coordinates must share an agreed datum/frame."""

    name: str
    coordinate_system: str
    holes: tuple[BoltHole, ...]
    pilot_diameter_mm: float | None
    face_to_datum_mm: float | None
    evidence: Evidence

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Interface name cannot be empty.")
        if not self.coordinate_system.strip():
            raise ValueError("A coordinate system/datum is required.")
        if not self.holes:
            raise ValueError("At least one bolt hole is required.")
        if self.pilot_diameter_mm is not None and self.pilot_diameter_mm <= 0:
            raise ValueError("Pilot diameter must be greater than zero.")
        if self.face_to_datum_mm is not None and not (
            abs(self.face_to_datum_mm) < float("inf")
        ):
            raise ValueError("Face-to-datum distance must be finite.")


@dataclass(frozen=True, slots=True)
class MountingPoint:
    """Vehicle or component mounting point with traceable position and hole data."""

    name: str
    position: Coordinate3D
    coordinate_system: str
    hole_diameter_mm: float | None
    evidence: Evidence

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.coordinate_system.strip():
            raise ValueError("Mounting point name and coordinate system are required.")
        if self.hole_diameter_mm is not None and self.hole_diameter_mm <= 0:
            raise ValueError("Mounting hole diameter must be positive.")


@dataclass(frozen=True, slots=True)
class VehicleSpec:
    """Vehicle packaging and original mounting reference data."""

    manufacturer: str
    model: str
    generation: str | None
    model_year: int | None
    engine_bay: Envelope3D | None
    gearbox_space: Envelope3D | None
    body_mounting_points: tuple[MountingPoint, ...]
    evidence: Evidence
    identifier: str

    def __post_init__(self) -> None:
        if not self.manufacturer.strip() or not self.model.strip() or not self.identifier.strip():
            raise ValueError("Vehicle manufacturer, model and identifier are required.")
        if self.model_year is not None and not 1885 <= self.model_year <= 2200:
            raise ValueError("Model year is outside the supported range.")


@dataclass(frozen=True, slots=True)
class PowerUnitSpec:
    """Engine or electric drive unit specification."""

    manufacturer: str
    model: str
    powertrain_type: PowertrainType
    envelope: Envelope3D | None
    mass_kg: float | None
    peak_power_kw: float | None
    peak_torque_nm: float | None
    mounting_points: tuple[MountingPoint, ...]
    gearbox_interface: MechanicalInterface | None
    evidence: Evidence
    identifier: str

    def __post_init__(self) -> None:
        if not self.manufacturer.strip() or not self.model.strip() or not self.identifier.strip():
            raise ValueError("Power-unit manufacturer, model and identifier are required.")
        for name in ("mass_kg", "peak_power_kw", "peak_torque_nm"):
            value = getattr(self, name)
            if value is not None and (value < 0 or value == float("inf")):
                raise ValueError(f"{name} must be finite and non-negative.")


@dataclass(frozen=True, slots=True)
class GearboxSpec:
    """Transmission specification and mating interface."""

    manufacturer: str
    model: str
    transmission_type: TransmissionType
    envelope: Envelope3D | None
    mass_kg: float | None
    input_torque_limit_nm: float | None
    engine_interface: MechanicalInterface | None
    mounting_points: tuple[MountingPoint, ...]
    evidence: Evidence
    identifier: str

    def __post_init__(self) -> None:
        if not self.manufacturer.strip() or not self.model.strip() or not self.identifier.strip():
            raise ValueError("Gearbox manufacturer, model and identifier are required.")
        for name in ("mass_kg", "input_torque_limit_nm"):
            value = getattr(self, name)
            if value is not None and (value < 0 or value == float("inf")):
                raise ValueError(f"{name} must be finite and non-negative.")
