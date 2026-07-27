from __future__ import annotations

import pytest

from universe_lab.stringbench.j30_locus import J30Point, certify_j30_point


@pytest.mark.parametrize(
    ("name", "role", "values"),
    [
        ("j30-training-001", "training", (1, 2, 3, 6, 12, 1)),
        ("j30-validation-001", "validation", (1, -1, 4, -2, -16, 2)),
        ("j30-held-out-001", "held_out", (3, 1, 2, -20, 48, -2)),
    ],
)
def test_exact_j30_fixtures(name: str, role: str, values: tuple[int, ...]) -> None:
    point = J30Point(*values, name, role)
    certificate = certify_j30_point(point)
    assert certificate["status"] == "J30_EXACT_LOCUS_PASS"
    assert certificate["passed"]
    assert certificate["minimal_k3_certificate"]
    assert len(certificate["four_fibrations"]) == 4


def test_weighted_projective_scaling_preserves_j30_certificate() -> None:
    point = J30Point(3, 1, 2, -20, 48, -2, "held-out", "held_out")
    scaled = certify_j30_point(point.weighted_scale(2), include_fibrations=False)
    assert scaled["passed"]
    assert scaled["checks"]["oracle_a_disc_D_zero"]
    assert scaled["checks"]["oracle_b_disc_d_zero"]


@pytest.mark.parametrize(
    "point",
    [
        J30Point(1, 2, 3, 6, 13, 1, "simple-root", "negative"),
        J30Point(1, 2, -9, -18, 0, 1, "triple-root", "negative"),
        J30Point(1, -1, -1, 2, 3, -1, "resultant-intersection", "negative"),
        J30Point(-1, -2, -2, 4, -2, -1, "a-intersection", "negative"),
        J30Point(1, 2, 0, 0, 9, 1, "j4-intersection", "negative"),
        J30Point(1, 2, 3, 6, 0, 1, "j6-zero", "negative"),
    ],
)
def test_non_generic_or_non_j30_points_are_rejected(point: J30Point) -> None:
    certificate = certify_j30_point(point, include_fibrations=False)
    assert not certificate["passed"]
    assert certificate["status"] == "J30_FAIL"


def test_oracle_b_is_required() -> None:
    point = J30Point(1, 2, 3, 6, 12, 1, "training", "mutation")
    certificate = certify_j30_point(point, include_fibrations=False)
    mutated = dict(certificate["checks"])
    mutated["oracle_b_disc_d_zero"] = False
    assert not all(mutated.values())
