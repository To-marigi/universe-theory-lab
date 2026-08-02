"""Exact guards for the full-M0 Q5-free Schur reduction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_common_core_q5_free_v042 as result

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "d19b01460604c647dc290143bf3a5aba2986bc9e6be235fd1ebae3a7702c25a3"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return result.build_payload(ROOT)


def test_artifact_rebuilds_exactly_and_is_fail_closed(rebuilt: dict[str, Any]) -> None:
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
    binding = frozen["canonical_input_binding"]
    assert set(binding) == {
        "path",
        "binding_kind",
        "expected_semantic_digest_sha256",
        "actual_semantic_digest_sha256",
        "passed",
    }
    assert binding["binding_kind"] == "canonical_json_semantic_digest"
    assert binding["expected_semantic_digest_sha256"] == (
        result.EXPECTED_UNIT_MINOR_SEMANTIC_DIGEST
    )
    assert binding["actual_semantic_digest_sha256"] == (result.EXPECTED_UNIT_MINOR_SEMANTIC_DIGEST)
    assert binding["passed"] is True


def test_source_native_census_excludes_q5_from_every_m0_builder(
    rebuilt: dict[str, Any],
) -> None:
    census = rebuilt["source_native_Q5_census"]
    assert census["Q5_variable"] == "Q_5_EXTERNAL"
    assert census["Q5_context_index"] == 131
    assert census["context_variable_count"] == 132
    assert census["Q5_is_an_occurrence_variable"] is False
    assert census["Q5_is_a_signature_variable"] is False
    assert census["raw_CPOBC"] == {
        "row_count": 783,
        "operator_reference_count": 3061,
        "references_resolving_to_Q5": 0,
    }
    assert census["fixed_vector_GC"] == {
        "generator_count": 320,
        "path_transition_reference_count": 1564,
        "references_resolving_to_Q5": 0,
    }
    assert census["reachable_state_MSR"] == {
        "constraint_count": 24,
        "transition_reference_count": 131,
        "references_resolving_to_Q5": 0,
        "anchor_paths_use_the_same_Q5_free_path_inventory": True,
    }
    assert "not invoked" in census["source_generation_provenance"]["Q_stage_selector_role"]


def test_all_symbolic_m0_and_pivot_rows_are_q5_free(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["symbolic_support_certificate"]
    assert certificate["M0_row_count"] == 1127
    assert certificate["block_row_counts"] == {
        "raw_CPOBC": 783,
        "fixed_vector_GC": 320,
        "reachable_state_MSR": 24,
    }
    assert certificate["block_symbolic_support_edge_counts"] == (
        result.EXPECTED_BLOCK_SYMBOLIC_SUPPORT_EDGES
    )
    assert certificate["full_symbolic_support_ledger_digest_sha256"] == (
        result.EXPECTED_FULL_SYMBOLIC_SUPPORT_LEDGER_DIGEST
    )
    assert certificate["Q5_zero_ledger_digest_sha256"] == (result.EXPECTED_Q5_ZERO_LEDGER_DIGEST)
    assert certificate["rows_with_Q5_support_key"] == 0
    assert certificate["rows_with_nonzero_Q5_symbolic_coefficient"] == 0
    assert certificate["pivot_row_count"] == 127
    assert certificate["pivot_symbolic_support_ledger_digest_sha256"] == (
        result.EXPECTED_PIVOT_SYMBOLIC_SUPPORT_LEDGER_DIGEST
    )
    assert certificate["pivot_rows_with_Q5_support_key"] == 0
    assert certificate["pivot_rows_with_nonzero_Q5_symbolic_coefficient"] == 0
    assert certificate["selected_pivot_rows_match_full_symbolic_compiler"] is True


def test_schur_identity_preserves_the_zero_q5_column(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["global_Schur_identity_certificate"]
    block = certificate["dimension_free_block_form"]
    assert block["pivot_rows"] == "[P U 0_Q5] with P 127 by 127"
    assert block["arbitrary_M0_row"] == "[v w 0_Q5]"
    assert block["reduction"] == ("[v w 0]-v*P^-1*[P U 0]=[0,w-v*P^-1*U,0]")
    assert block["only_denominator"] == ("det(P), already certified as a global unit")
    assert certificate["generic_2_by_2_proxy_non_Q_residual_checks"] == ["0", "0"]
    assert certificate["generic_2_by_2_proxy_Q5_residual_check"] == "0"


def test_every_semantic_branch_contains_m0_once_and_in_order(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["semantic_branch_inheritance_certificate"]
    assert certificate["branch_count"] == 4
    assert {branch["row_count"] for branch in certificate["branches"].values()} == {
        1156,
        1162,
    }
    assert all(
        branch["contains_all_1127_M0_rows_once_and_in_order"]
        for branch in certificate["branches"].values()
    )
    assert {
        branch["M0_source_order_digest_sha256"] for branch in certificate["branches"].values()
    } == {result.EXPECTED_M0_SOURCE_INDEX_DIGEST}
    assert "does not assert Q5-freeness" in certificate["non_converse_warning"]


def test_four_exact_cross_checks_agree_with_the_global_identity(
    rebuilt: dict[str, Any],
) -> None:
    cross_checks = rebuilt["exact_point_cross_checks"]
    assert cross_checks["point_count"] == 4
    assert cross_checks["records_digest_sha256"] == result.EXPECTED_POINT_RECORDS_DIGEST
    records = {record["point_id"]: record for record in cross_checks["records"]}
    assert {
        point_id: (record["M0_rank"], record["nonzero_Schur_row_count"])
        for point_id, record in records.items()
    } == {
        "reference_equal": (127, 0),
        "g2_pair_rejection": (131, 597),
        "g3_pair_rejection": (131, 597),
        "three_pair_common_zero": (131, 582),
    }
    assert all(record["pivot_rank"] == 127 for record in records.values())
    assert all(
        record["pivot_basis_is_exactly_the_127_non_Q_columns"] for record in records.values()
    )
    assert all(
        record["direct_M0_rows_with_nonzero_Q5"] == record["Schur_rows_with_nonzero_Q5"] == 0
        for record in records.values()
    )


def test_next_gate_contracts_are_exact_but_unproved(
    rebuilt: dict[str, Any],
) -> None:
    contract = rebuilt["pointwise_determinantal_next_gate_contract"]
    ring_scope = contract["coefficient_ring_scope"]
    non_aligned = contract["non_aligned_next_gate"]
    aligned = contract["aligned_next_gate"]
    assert "S_k=R_base[g_k^-1]" in ring_scope["non_aligned"]
    assert "R_base/(g2,g3,g4)" in ring_scope["aligned"]
    assert non_aligned["matrix"] == ("T=[A B] with one row for every Schur(M0) generator")
    assert "I1(T)=R" in non_aligned["equivalent_global_determinantal_contract"]
    assert "J=<A_i*h+B_i" in non_aligned["equivalent_auxiliary_ideal_route"]
    assert "=R[h]" in non_aligned["equivalent_auxiliary_ideal_route"]
    assert "(J_tilde:g_k^infinity)=R_base[h]" in (
        non_aligned["equivalent_auxiliary_ideal_route"]
    )
    assert aligned["matrix"].startswith("T=[A B2 B3 B4]")
    assert "I3(B)=R" in aligned["equivalent_global_determinantal_contract"]
    assert "w_k-1" in aligned["equivalent_auxiliary_ideal_route"]
    assert non_aligned["status"] == "CONTRACT_ONLY_UNIT_IDEALS_NOT_COMPUTED"
    assert aligned["status"] == "CONTRACT_ONLY_UNIT_IDEALS_NOT_COMPUTED"
    assert contract["scout_only_row_hints"]["status"] == ("SCOUT_ONLY_NOT_USED_BY_ANY_GATE")
    assert rebuilt["search_terminal"] == (
        "NOT_A_SEARCH_TERMINAL_FULL_M0_POINTWISE_IDEAL_CERTIFICATES_REMAIN"
    )
    assert "ALIGNED_GLOBALLY_REDUCIBLE" in rebuilt["claim_boundary"]
