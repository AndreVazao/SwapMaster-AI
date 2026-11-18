from swapmaster.domain.evidence import Evidence, EvidenceLevel
from swapmaster.domain.interfaces import InterfaceStatus, assess_interface_pair
from swapmaster.domain.powertrain import BoltHole, Coordinate3D, MechanicalInterface


def evidence(level: EvidenceLevel = EvidenceLevel.CONFIRMED) -> Evidence:
    return Evidence(level, source="verified drawing" if level is EvidenceLevel.CONFIRMED else None)


def interface(x: float = 0, level: EvidenceLevel = EvidenceLevel.CONFIRMED) -> MechanicalInterface:
    return MechanicalInterface(
        name="Engine bellhousing",
        coordinate_system="SAE-test-datum",
        holes=(
            BoltHole(Coordinate3D(x, 0, 0), 12),
            BoltHole(Coordinate3D(100, 0, 0), 12),
        ),
        pilot_diameter_mm=80,
        face_to_datum_mm=25,
        evidence=evidence(level),
    )


def test_matching_confirmed_interface_is_only_preliminary() -> None:
    result = assess_interface_pair(interface(), interface())
    assert result.status is InterfaceStatus.PRELIMINARY_GEOMETRY_MATCH


def test_different_coordinate_frames_are_not_compared() -> None:
    other = MechanicalInterface(
        "Gearbox face", "different-datum", interface().holes, 80, 25, evidence()
    )
    assert assess_interface_pair(interface(), other).status is InterfaceStatus.DATUM_MISMATCH


def test_hole_pattern_mismatch_is_detected() -> None:
    assert assess_interface_pair(interface(), interface(2)).status is InterfaceStatus.HOLE_PATTERN_MISMATCH


def test_estimated_dimensions_require_review() -> None:
    result = assess_interface_pair(
        interface(level=EvidenceLevel.ESTIMATED),
        interface(),
    )
    assert result.status is InterfaceStatus.GEOMETRY_MATCH_REQUIRES_REVIEW


def test_missing_interface_is_insufficient_data() -> None:
    assert assess_interface_pair(None, interface()).status is InterfaceStatus.INSUFFICIENT_DATA
