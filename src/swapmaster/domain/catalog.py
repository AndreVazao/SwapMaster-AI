"""Evidence-aware vehicle and powertrain catalogue value objects.

All dimensions use millimetres, mass uses kilograms, power uses kilowatts,
torque uses newton-metres, and mounting coordinates use a vehicle-local frame.
These records describe inputs; they do not certify physical compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence, EvidenceLevel


def _required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")


def _non_negative_finite(value: float, field_name: str) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be finite and non-negative.")


def _positive_finite(value: float, field_name: str) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be finite and greater than zero.")


class PropulsionType(StrEnum):
    """Broad propulsion architecture; hybrid systems may contain multiple units."""

    COMBUSTION = "combustion"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    OTHER = "other"


class InterfaceKind(StrEnum):
    """Mechanical/electrical interface families; identifiers remain manufacturer-defined."""

    BELLHOUSING = "bellhousing"
    GEARBOX_OUTPUT = "gearbox_output"
    ENGINE_MOUNT = "engine_mount"
    MOTOR_MOUNT = "motor_mount"
    AXLE = "axle"
    HIGH_VOLTAGE = "high_voltage"
    LOW_VOLTAGE = "low_voltage"
    COOLING = "cooling"
    FUEL = "fuel"
    EXHAUST = "exhaust"
    OTHER = "other"


class InterfaceStatus(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    INCOMPATIBLE = "incompatible"
    MATCH_REQUIRES_REVIEW = "match_requires_review"
    PRELIMINARY_MATCH = "preliminary_match"


@dataclass(frozen=True, slots=True)
class MechanicalInterface:
    """A named mating interface; identifier must encode the relevant standard/revision."""

    kind: InterfaceKind
    identifier: str
    evidence: Evidence

    def __post_init__(self) -> None:
        _required_text(self.identifier, "identifier")


@dataclass(frozen=True, slots=True)
class MountingPoint:
    """A measured point in a named local coordinate frame, in millimetres."""

    identifier: str
    x_mm: float
    y_mm: float
    z_mm: float
    coordinate_frame: str
    evidence: Evidence

    def __post_init__(self) -> None:
        _required_text(self.identifier, "identifier")
        _required_text(self.coordinate_frame, "coordinate_frame")
        for name in ("x_mm", "y_mm", "z_mm"):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite.")


@dataclass(frozen=True, slots=True)
class VehiclePlatform:
    """Vehicle/platform packaging and interface reference data."""

    identifier: str
    manufacturer: str
    model: str
    model_year: int
    evidence: Evidence
    engine_bay: Envelope3D | None = None
    mounting_points: tuple[MountingPoint, ...] = ()
    interfaces: tuple[MechanicalInterface, ...] = ()

    def __post_init__(self) -> None:
        for name in ("identifier", "manufacturer", "model"):
            _required_text(getattr(self, name), name)
        if self.model_year < 1886:
            raise ValueError("model_year is outside the supported range.")
        _unique_ids(self.mounting_points, "mounting point")
        _unique_interfaces(self.interfaces)


@dataclass(frozen=True, slots=True)
class PowerUnit:
    """Combustion engine, electric motor, or a declared hybrid power unit."""

    identifier: str
    manufacturer: str
    model: str
    propulsion: PropulsionType
    evidence: Evidence
    envelope: Envelope3D | None = None
    mass_kg: float | None = None
    power_kw: float | None = None
    torque_nm: float | None = None
    interfaces: tuple[MechanicalInterface, ...] = ()

    def __post_init__(self) -> None:
        for name in ("identifier", "manufacturer", "model"):
            _required_text(getattr(self, name), name)
        for name in ("mass_kg", "power_kw", "torque_nm"):
            value = getattr(self, name)
            if value is not None:
                _positive_finite(value, name)
        _unique_interfaces(self.interfaces)


@dataclass(frozen=True, slots=True)
class Transmission:
    """Gearbox or reduction unit with declared mating interfaces."""

    identifier: str
    manufacturer: str
    model: str
    evidence: Evidence
    envelope: Envelope3D | None = None
    mass_kg: float | None = None
    input_torque_limit_nm: float | None = None
    interfaces: tuple[MechanicalInterface, ...] = ()

    def __post_init__(self) -> None:
        for name in ("identifier", "manufacturer", "model"):
            _required_text(getattr(self, name), name)
        for name in ("mass_kg", "input_torque_limit_nm"):
            value = getattr(self, name)
            if value is not None:
                _positive_finite(value, name)
        _unique_interfaces(self.interfaces)


@dataclass(frozen=True, slots=True)
class InterfaceAssessment:
    status: InterfaceStatus
    reasons: tuple[str, ...]


def assess_interface_compatibility(
    source: MechanicalInterface | None,
    target: MechanicalInterface | None,
) -> InterfaceAssessment:
    """Compare declared interface identity only; no geometric or load validation occurs."""
    if source is None or target is None:
        return InterfaceAssessment(
            InterfaceStatus.INSUFFICIENT_DATA,
            ("One or both interface definitions are missing.",),
        )
    if source.kind is not target.kind or source.identifier != target.identifier:
        return InterfaceAssessment(
            InterfaceStatus.INCOMPATIBLE,
            ("Interface family or declared identifier differs.",),
        )
    if (
        source.evidence.level is not EvidenceLevel.CONFIRMED
        or target.evidence.level is not EvidenceLevel.CONFIRMED
    ):
        return InterfaceAssessment(
            InterfaceStatus.MATCH_REQUIRES_REVIEW,
            ("Identifiers match, but at least one interface record is not confirmed.",),
        )
    return InterfaceAssessment(
        InterfaceStatus.PRELIMINARY_MATCH,
        (
            "Confirmed interface identifiers match.",
            "Geometry, tolerances, fasteners, loads, materials, and alignment remain unverified.",
        ),
    )


def _unique_ids(items: tuple[MountingPoint, ...], label: str) -> None:
    identifiers = [item.identifier for item in items]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{label} identifiers must be unique.")


def _unique_interfaces(items: tuple[MechanicalInterface, ...]) -> None:
    keys = [(item.kind, item.identifier) for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError("Interface definitions must be unique by kind and identifier.")
