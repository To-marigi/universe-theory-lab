from __future__ import annotations

from universe_lab.final_theory.cpobc_q_presentation_v033 import (
    OVERALL_VERDICT,
    PRESENTATION_VERDICT,
    READINESS_VERDICT,
    compile_q_presentation_n4,
    q_presentation_mutation_checks,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    REACHABLE_STATE_PROFILE,
)


def test_q_presentation_rewrites_the_frozen_v032_residual_inventory() -> None:
    result = compile_q_presentation_n4()
    assert result["passed"]
    counts = result["counts"]
    assert counts["original_transition_occurrences"] == 165
    assert counts["original_gregarious_generators"] == 24
    assert counts["antichain_Q_generators"] == 4
    assert counts["non_antichain_G_generators_forward_reduced"] == 20
    assert counts["CPOBC_identities_after_substitution"] == 83
    assert counts["CPOBC_nontrivial_residuals"] == 700
    assert counts["strong_MSR_identities_after_substitution"] == 3
    assert counts["strong_MSR_nontrivial_residuals"] == 21


def test_local_operator_gc_is_included_in_the_strong_profile_only() -> None:
    result = compile_q_presentation_n4()
    counts = result["counts"]
    assert result["semantic_profile"] == PAPER_STRONG_OPERATOR_PROFILE
    assert counts["local_operator_GC_basis_relations"] == 320
    assert (
        counts["local_operator_GC_identities_after_eq107_eq108"]
        + counts["local_operator_GC_nontrivial_residuals"]
        == 320
    )
    weak = result["separate_reachable_state_namespace"]
    assert weak["profile"] == REACHABLE_STATE_PROFILE
    assert weak["operator_GC_relations_in_ideal"] == 0
    assert weak["strong_MSR_relations_in_ideal"] == 0
    assert weak["not_mixed_with_presentation"]


def test_presentation_exposes_all_auxiliaries_and_invertibility_predicates() -> None:
    result = compile_q_presentation_n4()
    qn_branch = result["source_index_branches"]["EQ113_QN_BRANCH"]
    assert result["presentation_name"] == "Q_DOMINATED_PRESENTATION_WITH_AUXILIARIES"
    assert len(qn_branch["remaining_auxiliary_generators"]) == 22
    assert qn_branch["independent_matrix_generators"] == 26
    assert result["counts"]["abstract_d2_matrix_entry_unknowns_Qn_branch"] == 104
    assert result["invertibility_predicates"]["all_165_occurrences_preserved"]
    assert (
        len(
            result["invertibility_predicates"][
                "explicit_two_sided_inverse_predicates"
            ]
        )
        == 26
    )
    assert not result["minimality_status"]["minimal_claimed"]


def test_source_index_branches_are_not_merged() -> None:
    result = compile_q_presentation_n4()
    branches = result["source_index_branches"]
    assert set(branches) == {"EQ113_QN_BRANCH", "EQ113_QN_PLUS_1_BRANCH"}
    assert len(branches["EQ113_QN_BRANCH"]["path_consistency_relations"]) == 25
    literal = branches["EQ113_QN_PLUS_1_BRANCH"]
    assert len(literal["path_consistency_relations"]) == 25
    assert literal["outside_n4_Q_generator"] == "Q_5"
    assert sum(
        record["outside_n4_Q_inventory"]
        for record in literal["path_consistency_relations"]
    ) == 24


def test_readiness_remains_blocked_and_no_elimination_is_started() -> None:
    result = compile_q_presentation_n4()
    assert result["presentation_verdict"] == PRESENTATION_VERDICT
    assert result["readiness_verdict"] == READINESS_VERDICT
    assert result["overall_verdict"] == OVERALL_VERDICT
    assert not result["readiness_gate"]["Eq112_reduction_complete"]
    assert not result["readiness_gate"][
        "forward_reverse_equivalence_certified"
    ]
    assert not result["d2_scalarisation_boundary"]["dense_Groebner_executed"]
    assert (
        result["counts"]["solver_ready_scalar_polynomial_variable_count"]
        is None
    )


def test_q_presentation_critical_mutations_are_detected() -> None:
    checks = q_presentation_mutation_checks()
    assert checks
    assert all(checks.values())
