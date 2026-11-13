"""Core domain models and deterministic engineering rules."""

from swapmaster.domain.catalog import (
    InterfaceAssessment,
    InterfaceKind,
    InterfaceStatus,
    MechanicalInterface,
    MountingPoint,
    PowerUnit,
    PropulsionType,
    Transmission,
    VehiclePlatform,
    assess_interface_compatibility,
)
from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.fitment import FitmentAssessment, FitmentStatus, assess_envelope

__all__ = [
    "Envelope3D",
    "Evidence",
    "EvidenceLevel",
    "FitmentAssessment",
    "FitmentStatus",
    "InterfaceAssessment",
    "InterfaceKind",
    "InterfaceStatus",
    "MechanicalInterface",
    "MountingPoint",
    "PowerUnit",
    "PropulsionType",
    "Transmission",
    "VehiclePlatform",
    "assess_envelope",
    "assess_interface_compatibility",
]
