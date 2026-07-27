from __future__ import annotations

import pytest

from universe_lab.stringbench.iut import (
    CrossUniverseComparisonError,
    FrameAddress,
    MorphismCertificate,
    MorphismValidationError,
    UniverseTagged,
    compare_after_transport,
)


def test_raw_cross_universe_equality_is_forbidden_even_for_equal_values() -> None:
    left = UniverseTagged("u1", "f-theory", "m1", 7)
    right = UniverseTagged("u2", "heterotic", "m2", 7)

    with pytest.raises(CrossUniverseComparisonError, match="explicit"):
        _ = left == right


def test_raw_cross_frame_ordering_is_forbidden() -> None:
    left = UniverseTagged("u1", "f-theory", "m1", 2)
    right = UniverseTagged("u1", "heterotic", "m1", 3)

    with pytest.raises(CrossUniverseComparisonError):
        _ = left < right


def test_certified_transport_records_preserved_and_forgotten_structure() -> None:
    source_address = FrameAddress("u1", "f-theory", "k3-presentation")
    target_address = FrameAddress("u2", "vacuum-ir", "invariant-presentation")
    source = UniverseTagged(
        "u1",
        "f-theory",
        "k3-presentation",
        {"rank": 18},
        frozenset({"f-to-ir"}),
    )
    target = UniverseTagged("u2", "vacuum-ir", "invariant-presentation", 18)
    certificate = MorphismCertificate(
        morphism_id="f-to-ir",
        source=source_address,
        target=target_address,
        preserved_structure=("lattice_rank",),
        forgotten_structure=("raw_weierstrass_coordinates",),
        evidence_status="EXACT_SYMBOLIC",
        source_reference="benchmark duality certificate",
    )

    assert compare_after_transport(source, target, certificate, lambda value: value["rank"])


def test_unlisted_morphism_is_rejected() -> None:
    source_address = FrameAddress("u1", "f-theory", "m1")
    certificate = MorphismCertificate(
        "forbidden",
        source_address,
        FrameAddress("u2", "ir", "m2"),
        ("rank",),
        (),
        "EXACT_SYMBOLIC",
        "test fixture",
    )

    with pytest.raises(MorphismValidationError, match="does not permit"):
        certificate.transport(
            UniverseTagged("u1", "f-theory", "m1", 1),
            lambda value: value,
        )


def test_same_address_comparison_remains_available() -> None:
    address = FrameAddress("u1", "ir", "m1")
    assert UniverseTagged(
        address.universe_id,
        address.frame_id,
        address.arithmetic_model_id,
        5,
    ) == UniverseTagged(
        address.universe_id,
        address.frame_id,
        address.arithmetic_model_id,
        5,
    )
