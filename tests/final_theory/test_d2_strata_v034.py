from __future__ import annotations

from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_strata_v034 import (
    S1,
    S2,
    S3,
    compile_d2_strata_v034,
)


def test_s1_s2_s3_chart_cover_is_branch_specific_and_complete() -> None:
    result = compile_d2_strata_v034()
    assert result["passed"]
    assert result["all_chart_parameterisations_have_commuting_ratios"]
    assert result["branches"][DERIVED_BRANCH]["chart_counts"] == {
        S1: 12,
        S2: 9,
        S3: 1,
    }
    assert result["branches"][LITERAL_BRANCH]["chart_counts"] == {
        S1: 16,
        S2: 12,
        S3: 1,
    }
    assert result["branches"][DERIVED_BRANCH]["Q_indices"] == [1, 2, 3, 4]
    assert result["branches"][LITERAL_BRANCH]["Q_indices"] == [1, 2, 3, 4, 5]


def test_s2_zero_nilpotent_locus_is_sent_to_s3() -> None:
    result = compile_d2_strata_v034()
    for branch in result["branches"].values():
        coverage = branch["coverage"]
        assert coverage["S2_mu_all_zero_sent_to_S3"]
        assert coverage["S3_scalar_locus_included"]


def test_s3_reconstructed_transition_algebra_is_commutative() -> None:
    result = compile_d2_strata_v034()
    certificate = result["S3_transition_algebra_certificate"]
    assert certificate["dependency_nodes_checked"] == 92
    assert certificate["transition_occurrences_checked"] == 165
    assert certificate["all_reconstructed_transition_pairs_commute"]
    assert (
        certificate["verdict"]
        == "FINITE_N4_S3_TRANSITION_ALGEBRA_COMMUTATIVE"
    )
