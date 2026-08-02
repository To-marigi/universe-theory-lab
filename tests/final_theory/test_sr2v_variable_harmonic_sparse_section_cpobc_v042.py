"""Exact guards for the SR2-V variable-harmonic sparse-section audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

from universe_lab.final_theory import (
    sr2v_variable_harmonic_sparse_section_cpobc_v042 as audit,
)

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "4c8a71689c69d4845344eb44e459b3a5256075188b1f2d71dabc5a7428235efe"
EXPECTED_POINT_RECORDS_DIGEST = (
    "d10b502d7c23434f5f761563dd509847d4c1928f87107e35b025591ee47c5eeb"
)
EXPECTED_SECTION_POLYNOMIAL_DIGEST = (
    "3db721429ca880f9fdaf230031e9dc3bf204b8e42b227549f5b509bd8d2a91a4"
)
EXPECTED_ALPHA_ZERO_RECORDS_DIGEST = (
    "b722ae9bf8568462733be4b2b71e3c3f8328aef74451384e801fb1462492ad0b"
)
EXPECTED_VARIABLE_ORDER_DIGEST = (
    "fbe59bd1e38691d3464529942dc47557e6ea0df694b80b609e2b90389dddff56"
)
EXPECTED_SELECTED_ROWS_DIGEST = (
    "405ccbbb8c9a407bc1fbe32e97e44f05a75261f6c2c13b884ce40d7c12ba4667"
)
EXPECTED_SELECTED_MATRIX_DIGEST = (
    "8fd09de12b13fc65ed09a2e2fd7380cfe8a42448f44a16a36d79f3616f5af499"
)


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return audit.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(audit.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == audit.SCHEMA
    assert frozen["verdict"] == audit.VERDICT
    assert frozen["search_terminal"] == audit.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert audit.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())
    for relative, digest in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_escape_point_is_directly_rejected_by_the_full_raw_ledger(
    rebuilt: dict[str, Any],
) -> None:
    point = rebuilt["escape_point_full_raw_substitution"]
    assert point["boundary_support"] == {
        "p5-0000000": "25",
        "p5-000008c": "-1",
    }
    assert point["selected_f_entry_1_0_value"] == "0"
    assert point["selected_g_entry_1_0_value"] == "0"
    assert point["operator_equation_count"] == 783
    assert point["scalar_entry_count"] == 3132
    assert point["nonzero_scalar_entries"] == 911
    assert point["zero_scalar_entries"] == 2221
    assert point["operator_equations_with_nonzero_residual"] == 676
    assert point["operator_equations_vanishing_completely"] == 107
    assert point["relations_with_nonzero_residual"] == 542
    assert point["nonzero_entry_census"] == {
        "0,0": 89,
        "0,1": 89,
        "1,0": 663,
        "1,1": 70,
    }
    assert point["nonzero_equation_id_census"] == {
        "eq103": 739,
        "eq104": 87,
        "equal_second_orientation": 85,
    }
    assert point["nonzero_records_digest_sha256"] == EXPECTED_POINT_RECORDS_DIGEST
    assert len(point["nonzero_records"]) == 911


def test_first_exact_point_obstructions_are_pinned(rebuilt: dict[str, Any]) -> None:
    point = rebuilt["escape_point_full_raw_substitution"]
    assert point["first_nonzero_in_raw_ledger_order"] == {
        "relation_id": "cpobc-relation-0b2bbe81c6394d603f63",
        "equation_id": "eq103",
        "entry": [1, 0],
        "value": "-89/4",
        "lhs_word_length": 2,
        "rhs_word_length": 2,
    }
    assert point["first_additional_entry_in_selected_f_equation"] == {
        "relation_id": "cpobc-relation-ecdf5451a0bcf06c8da5",
        "equation_id": "eq103",
        "entry": [0, 0],
        "value": "-5/2096",
        "lhs_word_length": 2,
        "rhs_word_length": 2,
    }
    assert point["point_unit_identity"] == (
        "1=(-2096/5)*R_f[0,0], because R_f[0,0]=-5/2096"
    )


def test_two_additional_rows_kill_the_sparse_alpha_coordinates(
    rebuilt: dict[str, Any],
) -> None:
    section = rebuilt["two_alpha_principal_open_section"]
    assert section["polynomial_records_digest_sha256"] == (
        EXPECTED_SECTION_POLYNOMIAL_DIGEST
    )
    assert section["escape_evaluation"] == {
        "F0_escape": "-5/8",
        "Cf_escape": "131/2",
        "G0_escape": "-179/2",
        "Cg_escape": "-3",
        "Delta_escape": "-393/2",
    }
    additional = section["additional_raw_rows"]
    assert additional["f_entry_0_1"]["formula"] == "-x/128"
    assert additional["g_entry_0_1"]["formula"] == "7*y/8192"
    assert additional["consequence_over_Q"] == "raw CPOBC forces x=y=0"
    assert section["alpha_zero_matrix_reduction_failures"] == []
    assert section["rank_two_open_check"] == {
        "h_root": "1",
        "k_root": "0",
        "Delta_has_positive_homogeneous_degree": 4,
        "Delta_nonzero_implies_k_nonzero": True,
        "nonzero_root_zero_k_cannot_be_proportional_to_h": True,
        "conclusion": "Delta!=0 lies in the rank-two state locus",
    }
    assert section["degree_census"] == {
        "F0": {
            "term_count": 56,
            "minimum_total_degree": 1,
            "maximum_total_degree": 1,
            "constant_coefficient": "0",
        },
        "Cf": {
            "term_count": 955,
            "minimum_total_degree": 2,
            "maximum_total_degree": 2,
            "constant_coefficient": "0",
        },
        "G0": {
            "term_count": 27,
            "minimum_total_degree": 1,
            "maximum_total_degree": 1,
            "constant_coefficient": "0",
        },
        "Cg": {
            "term_count": 186,
            "minimum_total_degree": 2,
            "maximum_total_degree": 2,
            "constant_coefficient": "0",
        },
        "Delta": {
            "representation": "factored_Cf_times_Cg",
            "minimum_total_degree": 4,
            "maximum_total_degree": 4,
            "constant_coefficient": "0",
        },
    }


def test_rank_optimal_linear_manifest_has_a_nonzero_exact_minor(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["rank_optimal_linear_manifest"]
    assert certificate["scalar_entry_count"] == 3132
    assert certificate["nonzero_scalar_entries"] == 783
    assert certificate["zero_scalar_entries"] == 2349
    assert certificate["all_nonzero_entries_are_entry_1_0"] is True
    assert certificate["all_nonzero_entries_are_homogeneous_linear"] is True
    assert certificate["root_kernel_variable_count"] == 62
    assert certificate["linear_rank"] == 62
    assert certificate["nullity"] == 0
    assert certificate["selected_row_count"] == 62
    assert certificate["selected_row_count_is_rank_optimal"] is True
    assert certificate["nonzero_records_digest_sha256"] == (
        EXPECTED_ALPHA_ZERO_RECORDS_DIGEST
    )
    assert certificate["variable_order_digest_sha256"] == EXPECTED_VARIABLE_ORDER_DIGEST
    assert certificate["selected_rows_digest_sha256"] == EXPECTED_SELECTED_ROWS_DIGEST
    assert certificate["selected_coefficient_matrix_digest_sha256"] == (
        EXPECTED_SELECTED_MATRIX_DIGEST
    )
    assert certificate["selected_minor_determinant"] == str(
        audit.EXPECTED_PIVOT_MINOR_DETERMINANT
    )
    assert certificate["selected_minor_factorization"] == {"2": 192, "3": 9, "977": 1}
    assert len(certificate["selected_coefficient_matrix"]) == 62
    assert all(len(row) == 62 for row in certificate["selected_coefficient_matrix"])
    matrix = sp.Matrix(
        [
            [sp.Rational(value) for value in row]
            for row in certificate["selected_coefficient_matrix"]
        ]
    )
    assert matrix.det(method="domain-ge") == audit.EXPECTED_PIVOT_MINOR_DETERMINANT


def test_localized_unit_ideal_is_exact_but_nonterminal(rebuilt: dict[str, Any]) -> None:
    certificate = rebuilt["localized_unit_ideal_certificate"]
    assert certificate["raw_generator_count_upper_bound"] == 64
    assert certificate["selected_minor_determinant"] == str(
        audit.EXPECTED_PIVOT_MINOR_DETERMINANT
    )
    assert certificate["includes_the_predecessor_rational_section"] is True
    assert certificate["conclusion"] == (
        "the Delta!=0 two-alpha sparse section has empty raw-CPOBC locus"
    )
    assert rebuilt["scope_exclusions"]["beta_variables_beyond_beta_one"] == "UNRESOLVED"
    assert rebuilt["scope_exclusions"]["other_129_alpha_coordinates"] == "UNRESOLVED"
    assert rebuilt["scope_exclusions"]["SR2V_terminal_verdict"] is False
    assert rebuilt["execution"] == {
        "solver": "NOT_RUN",
        "groebner": "NOT_RUN",
        "sage": "NOT_INVOKED",
        "finite_field": "NOT_RUN",
        "numerical": "NOT_RUN",
        "arithmetic": "EXACT_QQ_SPARSE_SYMBOLIC_AND_GAUSSIAN_ELIMINATION_ONLY",
    }


def test_supplemental_semantic_branches_remain_separate(rebuilt: dict[str, Any]) -> None:
    supplemental = rebuilt["separate_unresolved_ledgers"]
    assert supplemental["Eq113"]["derived_Qn_records"] == 25
    assert supplemental["Eq113"]["literal_Qn_plus_1_records"] == 25
    assert supplemental["Eq113"]["branches_kept_separate"] is True
    assert supplemental["Eq139"]["printed_strict_instances"] == 4
    assert supplemental["Eq139"]["Eq145_completed_instances"] == 10
    assert supplemental["Eq139"]["domains_kept_separate"] is True


def test_semantic_digest_rejects_a_rank_mutation(rebuilt: dict[str, Any]) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["rank_optimal_linear_manifest"]["linear_rank"] = 61
    assert audit.semantic_digest(mutated) != EXPECTED_SEMANTIC_DIGEST
