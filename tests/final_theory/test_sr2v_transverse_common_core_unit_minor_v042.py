"""Exact guards for the global common-core non-Q unit minor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_common_core_unit_minor_v042 as result

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "286b2c8e0329dd585c33dee13c66e3a923a270d04822f3489186aad4ee1e45ac"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return result.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(result.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == result.SCHEMA
    assert frozen["verdict"] == result.VERDICT
    assert frozen["search_terminal"] == result.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert result.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert frozen["witness"] is None
    assert all(frozen["gates"].values())
    for relative, binding in frozen["input_artifacts"].items():
        assert binding["binding_kind"] == "canonical_json_semantic_digest"
        assert "raw_sha256" not in binding
        assert result.semantic_digest(_load(relative)) == binding["semantic_digest_sha256"]


def test_minor_is_common_core_only_and_has_the_declared_shape(rebuilt: dict[str, Any]) -> None:
    certificate = rebuilt["unit_minor_certificate"]
    assert certificate["matrix_shape"] == [127, 127]
    assert certificate["row_block_counts"] == {
        "CPOBC": 83,
        "fixed_vector_GC": 20,
        "reachable_state_MSR": 24,
    }
    assert {record["block"] for record in certificate["row_selection"]} == {
        "CPOBC",
        "fixed_vector_GC",
        "reachable_state_MSR",
    }
    assert certificate["explicitly_excluded_blocks"] == [
        "Eq113_derived",
        "Eq113_literal",
        "Eq139",
    ]
    assert certificate["column_selection_digest_sha256"] == (
        "a7d10f686478c127b89d69fda1cb9ee6768995b5c60b7b1d04dadc58eaee50a4"
    )


def test_safe_support_supergraph_has_a_unique_perfect_matching(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["unit_minor_certificate"]
    assert certificate["independent_diagonal_symbolic_support_edges"] == 559
    assert certificate["CSG_base_safe_symbolic_supergraph_edges"] == 554
    vanished = certificate["bottom_CSG_identically_vanishing_edges"]
    assert len(vanished) == 5
    assert {(record["offset"], record["row"], record["column"]) for record in vanished} == {
        (0, 83, 84),
        (0, 83, 92),
        (6, 87, 54),
        (9, 88, 97),
        (21, 93, 42),
    }
    assert {record["block"] for record in vanished} == {"fixed_vector_GC"}
    assert certificate["perfect_matching_is_unique"] is True
    assert certificate["alternating_digraph_is_acyclic"] is True
    assert certificate["matching_permutation_inversions"] == 3918
    assert certificate["matching_permutation_is_even"] is True
    assert certificate["matched_coefficient_type_counts"] == {
        "contains_upper_diagonal_symbols": 14,
        "bottom_only": 112,
        "constant": 1,
    }


def test_determinant_is_a_global_laurent_unit(rebuilt: dict[str, Any]) -> None:
    determinant = rebuilt["unit_minor_certificate"]["determinant_formula"]
    assert determinant["coefficient"] == "-1"
    assert determinant["upper_torus_exponents_s0_through_s48"] == list(
        result.EXPECTED_UPPER_EXPONENTS
    )
    assert determinant["upper_torus_exponent_digest_sha256"] == (
        "8477c3abdebbf2bffbccd054fc3d0ff6853f14b5c07dfe0a81aee6530ea5d1a6"
    )
    assert determinant["bottom_lambda_exponents"] == result.EXPECTED_LAMBDA_EXPONENTS
    assert determinant["q5_exponent"] == 0
    assert determinant["is_a_unit_on_the_declared_base"] is True


def test_direct_reference_determinant_matches_symbolic_formula(
    rebuilt: dict[str, Any],
) -> None:
    cross_check = rebuilt["unit_minor_certificate"]["reference_cross_check"]
    assert cross_check["direct_exact_rank"] == 127
    assert cross_check["direct_exact_determinant"] == str(
        result.EXPECTED_REFERENCE_DETERMINANT
    )
    assert cross_check["symbolic_unit_formula_value"] == str(
        result.EXPECTED_REFERENCE_DETERMINANT
    )
    assert cross_check["direct_and_symbolic_values_agree"] is True


def test_claim_boundary_remains_nonterminal(rebuilt: dict[str, Any]) -> None:
    assert rebuilt["search_terminal"] == (
        "NOT_A_SEARCH_TERMINAL_FIVE_Q_COLUMN_SCHUR_PROBLEM_REMAINS"
    )
    assert rebuilt["next_gate"]["ambient_columns_after_global_elimination"] == [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
    ]
    assert rebuilt["next_gate"]["branch_count_if_common_core_succeeds"] == 0
