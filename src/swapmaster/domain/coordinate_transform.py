"""Explicit rigid transforms between named engineering coordinate frames."""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite

from swapmaster.domain.evidence import Evidence

Vector3 = tuple[float, float, float]
Matrix3 = tuple[Vector3, Vector3, Vector3]
_ROTATION_TOLERANCE = 1e-6


def _validate_vector(vector: Vector3, field_name: str) -> None:
    if len(vector) != 3 or not all(isfinite(value) for value in vector):
        raise ValueError(f"{field_name} must contain three finite values.")


def _determinant(matrix: Matrix3) -> float:
    a, b, c = matrix
    return a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (
        b[0] * c[2] - b[2] * c[0]
    ) + a[2] * (b[0] * c[1] - b[1] * c[0])


def _validate_rotation(matrix: Matrix3) -> None:
    if len(matrix) != 3:
        raise ValueError("rotation must be a 3x3 matrix.")
    for row in matrix:
        _validate_vector(row, "rotation row")
    for i in range(3):
        for j in range(3):
            dot = sum(matrix[k][i] * matrix[k][j] for k in range(3))
            if not isclose(dot, 1.0 if i == j else 0.0, abs_tol=_ROTATION_TOLERANCE):
                raise ValueError("rotation must be orthonormal.")
    if not isclose(_determinant(matrix), 1.0, abs_tol=_ROTATION_TOLERANCE):
        raise ValueError("rotation must be right-handed with determinant +1.")


def _rotate(matrix: Matrix3, vector: Vector3) -> Vector3:
    return tuple(sum(matrix[row][col] * vector[col] for col in range(3)) for row in range(3))  # type: ignore[return-value]


def _multiply(first: Matrix3, second: Matrix3) -> Matrix3:
    return tuple(
        tuple(sum(first[row][k] * second[k][col] for k in range(3)) for col in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class CoordinateTransform:
    """Rigid transform p_target = R * p_source + t; translation is in mm."""

    source_frame: str
    target_frame: str
    rotation: Matrix3
    translation_mm: Vector3
    evidence: Evidence

    def __post_init__(self) -> None:
        if not self.source_frame.strip() or not self.target_frame.strip():
            raise ValueError("source_frame and target_frame cannot be empty.")
        if self.source_frame == self.target_frame:
            raise ValueError("source_frame and target_frame must be different.")
        _validate_rotation(self.rotation)
        _validate_vector(self.translation_mm, "translation_mm")

    def apply(self, point_mm: Vector3) -> Vector3:
        """Apply active right-handed rotation to a column vector, then translate."""
        _validate_vector(point_mm, "point_mm")
        rotated = _rotate(self.rotation, point_mm)
        return tuple(rotated[i] + self.translation_mm[i] for i in range(3))  # type: ignore[return-value]

    def inverse(self) -> CoordinateTransform:
        """Return rigid inverse using R transpose and -R transpose times t."""
        inverse_rotation: Matrix3 = tuple(
            tuple(self.rotation[col][row] for col in range(3)) for row in range(3)
        )  # type: ignore[assignment]
        inverse_translation = _rotate(
            inverse_rotation, tuple(-value for value in self.translation_mm)
        )
        return CoordinateTransform(
            self.target_frame, self.source_frame, inverse_rotation,
            inverse_translation, self.evidence
        )

    def then(self, following: CoordinateTransform) -> CoordinateTransform:
        """Compose this source->middle transform with middle->target."""
        if self.target_frame != following.source_frame:
            raise ValueError("Transform frames do not connect for composition.")
        rotation = _multiply(following.rotation, self.rotation)
        translated = _rotate(following.rotation, self.translation_mm)
        translation = tuple(translated[i] + following.translation_mm[i] for i in range(3))
        evidence = following.evidence if following.evidence.requires_review else self.evidence
        return CoordinateTransform(
            self.source_frame, following.target_frame, rotation, translation, evidence
        )
