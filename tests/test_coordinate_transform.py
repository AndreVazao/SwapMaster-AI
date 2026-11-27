"""Tests for explicit, validated coordinate-frame transformations."""

from math import isclose

import pytest

from swapmaster.domain.coordinate_transform import CoordinateTransform
from swapmaster.domain.evidence import Evidence, EvidenceLevel

CONFIRMED = Evidence(EvidenceLevel.CONFIRMED, source="surveyed datum")
IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
ROT_Z_90 = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def make_transform(
    source="engine",
    target="vehicle",
    rotation=IDENTITY,
    translation=(10.0, 20.0, 30.0),
    evidence=CONFIRMED,
):
    return CoordinateTransform(source, target, rotation, translation, evidence)


def test_translation_applies_in_millimetres():
    assert make_transform().apply((1.0, 2.0, 3.0)) == (11.0, 22.0, 33.0)


def test_rotation_uses_active_right_handed_column_vector_convention():
    result = make_transform(
        rotation=ROT_Z_90, translation=(0.0, 0.0, 0.0)
    ).apply((1.0, 0.0, 0.0))
    assert all(
        isclose(a, b, abs_tol=1e-9)
        for a, b in zip(result, (0.0, 1.0, 0.0), strict=True)
    )


def test_inverse_round_trip_recovers_original_point():
    original = (12.5, -8.0, 44.0)
    forward = make_transform(rotation=ROT_Z_90)
    recovered = forward.inverse().apply(forward.apply(original))
    assert all(
        isclose(a, b, abs_tol=1e-9)
        for a, b in zip(recovered, original, strict=True)
    )


def test_composition_matches_sequential_application():
    first = make_transform("engine", "vehicle", ROT_Z_90, (10.0, 0.0, 0.0))
    second = make_transform("vehicle", "world", IDENTITY, (0.0, 5.0, 0.0))
    point = (2.0, 3.0, 4.0)
    actual = first.then(second).apply(point)
    expected = second.apply(first.apply(point))
    assert all(
        isclose(a, b, abs_tol=1e-9)
        for a, b in zip(actual, expected, strict=True)
    )


def test_composition_rejects_disconnected_frames():
    with pytest.raises(ValueError, match="do not connect"):
        make_transform("engine", "vehicle").then(make_transform("gearbox", "world"))


def test_invalid_non_orthonormal_rotation_is_rejected():
    invalid = ((1.0, 0.1, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="orthonormal"):
        make_transform(rotation=invalid)


def test_reflection_is_rejected():
    reflection = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="determinant"):
        make_transform(rotation=reflection)


def test_non_finite_translation_and_points_are_rejected():
    with pytest.raises(ValueError, match="translation_mm"):
        make_transform(translation=(0.0, float("nan"), 0.0))
    with pytest.raises(ValueError, match="point_mm"):
        make_transform().apply((0.0, float("inf"), 0.0))


def test_frame_names_must_be_valid_and_distinct():
    with pytest.raises(ValueError, match="cannot be empty"):
        make_transform(source=" ")
    with pytest.raises(ValueError, match="different"):
        make_transform(source="vehicle", target="vehicle")


def test_inverse_preserves_frame_direction_and_evidence():
    forward = make_transform()
    inverse = forward.inverse()
    assert inverse.source_frame == "vehicle"
    assert inverse.target_frame == "engine"
    assert inverse.evidence == CONFIRMED
