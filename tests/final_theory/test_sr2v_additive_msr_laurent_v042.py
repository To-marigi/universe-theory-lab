"""Exact guards for the SR2-V additive-MSR Laurent certificate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_additive_msr_laurent_v042 as additive

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "53241bd2973c41153d145d6e2fee2f082c4631f7aeba76e30f0e89cca7df3b8b"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return additive.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(additive.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == additive.SCHEMA
    assert frozen["verdict"] == additive.VERDICT
    assert frozen["search_terminal"] == additive.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == additive.semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    for relative, binding in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == binding[
            "raw_sha256"
        ]


def test_all_additive_msr_equations_are_compiled_without_q5(rebuilt: dict[str, Any]) -> None:
    system = rebuilt["additive_MSR_system"]
    assert system["equation_count"] == 24
    assert system["source_stage_counts"] == {"p1": 1, "p2": 2, "p3": 5, "p4": 16}
    assert system["Q5_coordinate_occurs"] is False
    assert len(system["equations"]) == 24
    assert all(record["laurent_term_count"] >= 2 for record in system["equations"])
    for record in system["equations"]:
        for term in record["cleared_polynomial_terms"]:
            assert all(factor["exponent"] >= 0 for factor in term["monomial"])


def test_normalized_csg_point_is_exact_and_satisfies_all_24_rows(
    rebuilt: dict[str, Any],
) -> None:
    point = rebuilt["normalized_CSG_point"]
    assert point["base"] == 2
    assert len(point["torus_coordinate_exponents"]) == 29
    assert len(point["torus_coordinate_values"]) == 29
    assert len(point["transition_character_exponents_in_variable_order"]) == 132
    assert point["all_24_residuals"] == ["0"] * 24
    assert point["all_coordinates_nonzero"] is True


def test_additive_msr_jacobian_is_full_row_rank_at_the_csg_point(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["smooth_local_certificate"]
    assert certificate["jacobian_shape"] == [24, 29]
    assert certificate["jacobian_rank"] == 24
    assert len(certificate["independent_constraint_ids"]) == 24
    assert certificate["minor_row_indices"] == list(range(24))
    assert certificate["minor_column_indices"] == list(range(24))
    assert certificate["minor_determinant"] == "-5/35184372088832"
    assert certificate["local_dimension_inside_Gm29"] == 5
    assert certificate["tangent_kernel_rank"] == 5


def test_q5_is_one_exact_global_factor_and_four_actual_tangents_remain(
    rebuilt: dict[str, Any],
) -> None:
    parameterisation = rebuilt["laurent_parameterisation"]
    certificate = rebuilt["smooth_local_certificate"]
    assert parameterisation["cutoff_external_Q5_coordinate"] == "t:28"
    assert parameterisation["Q5_is_an_exact_global_Gm_factor_of_the_additive_MSR_locus"]
    assert certificate["pure_Q5_tangent_basis_indices"] == [4]
    assert certificate["actual_edge_scalar_tangent_dimension"] == 4


def test_claim_boundary_is_nonterminal_and_solver_free(rebuilt: dict[str, Any]) -> None:
    assert all(rebuilt["gates"].values())
    boundary = rebuilt["resource_and_claim_boundaries"]
    assert boundary["solver_status"] == "NOT_RUN"
    assert boundary["groebner_status"] == "NOT_RUN"
    assert boundary["global_additive_MSR_variety_classified"] is False
    assert boundary["upper_right_cocycle_fibre_solved"] is False
    assert rebuilt["witness"] is None
    assert "not a global classification" in rebuilt["claim_boundary"]


def test_semantic_digest_rejects_a_rank_mutation(rebuilt: dict[str, Any]) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["smooth_local_certificate"]["jacobian_rank"] = 23
    assert additive.semantic_digest(mutated) != rebuilt["semantic_digest_sha256"]
