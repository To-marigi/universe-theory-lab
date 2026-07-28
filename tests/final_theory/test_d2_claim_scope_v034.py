from __future__ import annotations

from universe_lab.final_theory.d2_claim_scope_v034 import (
    RECONSTRUCTION_EQUIVALENT,
    RECONSTRUCTION_PARTIAL,
    claim_allowed,
    compile_claim_scope_v034,
    compile_reconstruction_equivalence_v034,
    compile_source_branch_analysis_v034,
)


def test_reconstruction_equivalence_is_not_overclaimed() -> None:
    result = compile_reconstruction_equivalence_v034()
    assert result["verdict"] == RECONSTRUCTION_PARTIAL
    assert result["obligations"]["inverse_sites"]["count"] == 26
    assert result["obligations"]["inverse_sites"][
        "all_two_sided_in_localisation"
    ]
    assert not result["equivalence_claim_allowed"]
    assert not claim_allowed(RECONSTRUCTION_EQUIVALENT, result["evidence"])


def test_source_index_branches_remain_distinct() -> None:
    result = compile_source_branch_analysis_v034()
    assert not result["branches_mixed"]
    derived = result["branches"]["DERIVED_APPENDIX_QN_BRANCH"]
    literal = result["branches"]["LITERAL_PRINTED_QN_PLUS_1_BRANCH"]
    assert derived["maximum_Q_index"] == 4
    assert literal["maximum_Q_index"] == 5
    assert literal["relations_requiring_Q5"] == 24
    assert not literal["Q5_identified_with_Q4"]


def test_claim_scope_stays_partial_and_final_theory_open() -> None:
    result = compile_claim_scope_v034()
    assert result["finite_d2_verdict"] == "CPOBC_D2_N4_PARTIAL"
    assert result["verdict"] == "FINAL_THEORY_OPEN"
    assert (
        "CPOBC_D2_N4_COMMUTATIVE_REPRESENTATION_CERTIFIED"
        in result["allowed_claims"]
    )
    assert (
        "CPOBC_D2_N4_NONCOMMUTATIVE_REPRESENTATION_FOUND"
        in result["forbidden_claims"]
    )
