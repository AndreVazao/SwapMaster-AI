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
from swapmaster.domain.compatibility import (
    CompatibilityAssessment,
    CompatibilityStatus,
    CriterionAssessment,
    CriterionStatus,
    assess_powertrain_candidate,
)
from swapmaster.domain.dimensions import Envelope3D
from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.fitment import FitmentAssessment, FitmentStatus, assess_envelope
from swapmaster.domain.mounting_geometry import (\n    MountingGeometryAssessment,\n    MountingGeometryStatus,\n    assess_mounting_geometry,\n)\nfrom swapmaster.domain.measurement import (
    DataReadiness,
    DataReadinessAssessment,
    EngineeringDatum,
    MeasurementHistory,
    MeasurementUnit,
    assess_required_measurements,
)

__all__ = [
    "CompatibilityAssessment",
    "CompatibilityStatus",
    "CriterionAssessment",
    "CriterionStatus",
    "DataReadiness",
    "DataReadinessAssessment",
    "EngineeringDatum",
    "Envelope3D",
    "Evidence",
    "EvidenceLevel",
    "FitmentAssessment",
    "FitmentStatus",
    "InterfaceAssessment",
    "InterfaceKind",
    "InterfaceStatus",
    "MeasurementHistory",
    "MeasurementUnit",
    "MechanicalInterface",
    "MountingGeometryAssessment",\n    "MountingGeometryStatus",\n    "MountingPoint",
    "PowerUnit",
    "PropulsionType",
    "Transmission",
    "VehiclePlatform",
    "assess_envelope",
    "assess_required_measurements",
    "assess_interface_compatibility",\n    "assess_mounting_geometry",
    "assess_powertrain_candidate",
]
