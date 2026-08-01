"""Exact checks for the SR2-V invariant-line tangent obstruction."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_visible_tangent_v042 as tangent
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return tangent.build_payload(ROOT)


def test_frozen_tangent_certificate_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(tangent.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == tangent.semantic_digest(frozen)
    assert frozen["verdict"] == tangent.VERDICT
    assert frozen["search_terminal"] == tangent.SEARCH_TERMINAL
    assert frozen["passed"] is True


def test_pure_lower_and_full_matrix_tangent_ranks(rebuilt: dict[str, Any]) -> None:
    problems = rebuilt["tangent_problem"]
    pure = problems["pure_lower"]
    assert pure["variable_count"] == 132
    assert pure["rank"] == 131
    assert pure["nullity"] == 1
    assert pure["nullspace_basis"] == [{torus.Q5: "1"}]
    assert pure["in_scope_lower_coordinates_with_kernel_support"] == []

    full = problems["full_matrix"]
    assert full["variable_count"] == 528
    assert full["rank"] == 455
    assert full["nullity"] == 73
    assert full["in_scope_lower_coordinates_with_kernel_support"] == []
    assert full["lower_coordinates_with_kernel_support"] == [f"{torus.Q5}:10"]


def test_invariant_line_breaking_subsystem_is_global_in_upper_coordinate(
    rebuilt: dict[str, Any],
) -> None:
    problems = rebuilt["tangent_problem"]
    pure = problems["pure_lower"]["invariant_line_breaking_subsystem"]
    full = problems["full_matrix"]["invariant_line_breaking_subsystem"]
    zero = problems["zero_upper_full_matrix_control"][
        "invariant_line_breaking_subsystem"
    ]
    assert pure["row_count"] == 1187
    assert pure["rank"] == 131
    assert pure["nullity"] == 1
    assert pure["nullspace_basis"] == [{torus.Q5: "1"}]
    assert (
        pure["normalised_rows_sha256"]
        == full["normalised_rows_sha256"]
        == zero["normalised_rows_sha256"]
        == "dc8f354ac3726532365d48144024fcc1ca53d84957c777f190350d4f45a4ea9c"
    )


def test_no_first_order_reachable_or_visibility_escape(rebuilt: dict[str, Any]) -> None:
    for problem_name in ("pure_lower", "full_matrix"):
        problem = rebuilt["tangent_problem"][problem_name]
        assert problem["path_count"] == 407
        assert problem["reachable_lower_components_not_forced_zero"] == 0
        assert len(problem["commutator_actions"]) == 6
        assert all(
            record["tested_action_components"] == 814
            and record["first_order_actions_not_forced_zero"] == 0
            for record in problem["commutator_actions"].values()
        )


def test_dual_inverse_has_exact_zero_first_order_residual() -> None:
    matrix: tangent.DualMatrix = (
        (tangent.Dual(Fraction(2), {"a": Fraction(1)}), tangent._constant(3)),
        (tangent.Dual(Fraction(0), {"c": Fraction(1)}), tangent._constant(5)),
    )
    product = tangent._matrix_multiply(matrix, tangent._matrix_inverse(matrix))
    identity = tangent._identity()
    assert product == identity
