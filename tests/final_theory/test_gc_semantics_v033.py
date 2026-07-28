from __future__ import annotations

import pytest

from universe_lab.final_theory.gc_semantics_v033 import (
    GC_FIXED_VECTOR,
    GC_STRONG_OPERATOR,
    GC_VERDICT,
    MSR_STRONG_OPERATOR,
    MSR_VERDICT,
    PAPER_STRONG_OPERATOR_PROFILE,
    REACHABLE_STATE_PROFILE,
    SOURCE_VERDICT,
    gc_fixed_vector_counterexample,
    gc_msr_semantics_audit,
    literature_matrix,
    msr_reachable_state_counterexample,
    source_equation_audit,
    validate_relation_namespace,
)


def test_exact_gc_fixed_vector_counterexample_is_invertible() -> None:
    result = gc_fixed_vector_counterexample()
    assert result["fixed_vector_equality"]
    assert result["both_operators_invertible"]
    assert result["det_X"] == result["det_Y"] == 1
    assert not result["X_equals_Y"]


def test_exact_msr_reachable_state_counterexample_has_invertible_terms() -> None:
    result = msr_reachable_state_counterexample()
    assert result["reachable_state_MSR"]
    assert result["all_transition_summands_invertible"]
    assert result["det_A_1"] == 4
    assert result["det_A_2"] == 1
    assert not result["strong_operator_MSR"]


def test_semantic_profiles_are_namespaced() -> None:
    assert validate_relation_namespace(
        semantic_profile=REACHABLE_STATE_PROFILE,
        relation_strength=GC_FIXED_VECTOR,
    )
    assert validate_relation_namespace(
        semantic_profile=PAPER_STRONG_OPERATOR_PROFILE,
        relation_strength=GC_STRONG_OPERATOR,
    )
    with pytest.raises(ValueError, match="strong operator relation"):
        validate_relation_namespace(
            semantic_profile=REACHABLE_STATE_PROFILE,
            relation_strength=GC_STRONG_OPERATOR,
        )
    with pytest.raises(ValueError, match="strong operator relation"):
        validate_relation_namespace(
            semantic_profile=REACHABLE_STATE_PROFILE,
            relation_strength=MSR_STRONG_OPERATOR,
        )


def test_semantics_verdicts_do_not_infer_unstated_lifting_assumptions() -> None:
    result = gc_msr_semantics_audit()
    assert result["passed"]
    assert result["GC_verdict"] == GC_VERDICT
    assert result["MSR_verdict"] == MSR_VERDICT
    assumptions = result["possible_equivalence_assumptions"]
    assert all(not item["paper_explicit"] for item in assumptions)
    assert result["semantic_profiles"][REACHABLE_STATE_PROFILE][
        "operator_ideal_relations_emitted"
    ] is False


def test_source_equation_audit_preserves_both_eq113_branches() -> None:
    result = source_equation_audit()
    assert result["verdict"] == SOURCE_VERDICT
    assert result["equations"]["113"]["pdf_content"].endswith("Q_(n+1)] = 0")
    assert (
        result["independent_eq112_comparison"]["derived_index"]
        == "Q_n"
    )
    assert set(result["branches"]) == {
        "EQ113_QN_BRANCH",
        "EQ113_QN_PLUS_1_BRANCH",
    }
    assert result["branch_mixing_forbidden"]
    assert result["equations"]["163"]["content"].endswith(
        "for two paths expressing G_4"
    )


def test_literature_matrix_uses_only_permitted_frontier_classes() -> None:
    result = literature_matrix()
    assert result["passed"]
    by_topic = {entry["topic"]: entry for entry in result["entries"]}
    assert (
        by_topic["paper atomisation and decimation definition"][
            "classification"
        ]
        == "LITERATURE_LOCKED"
    )
    assert (
        by_topic[
            "general CPOBC d=2 representation and atomisation compiler follow-up"
        ]["classification"]
        == "OPEN_TARGET"
    )
