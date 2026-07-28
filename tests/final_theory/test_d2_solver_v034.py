from __future__ import annotations

from universe_lab.final_theory.d2_solver_v034 import (
    scalar_s3_representation_certificate_v034,
)


def test_exact_scalar_s3_fixture_satisfies_every_original_finite_relation() -> None:
    result = scalar_s3_representation_certificate_v034()
    assert result["passed"]
    assert (
        result["verdict"]
        == "CPOBC_D2_N4_COMMUTATIVE_REPRESENTATION_CERTIFIED"
    )
    assert result["counts"] == {
        "original_CPOBC_relation_records": 641,
        "original_CPOBC_word_equations": 783,
        "strong_operator_MSR_constraints": 24,
        "local_operator_GC_basis_relations": 320,
        "same_endpoint_path_equalities": 1529,
        "atomisation_paths": 34,
        "atomisation_steps": 76,
        "transition_occurrences": 165,
        "inverse_sites": 26,
        "Eq113_relations_per_branch": {
            "DERIVED_APPENDIX_QN_BRANCH": 25,
            "LITERAL_PRINTED_QN_PLUS_1_BRANCH": 25,
        },
    }
    assert all(
        record["nonsingular"]
        for record in result["transition_assignment"]
    )
    assert result["exact_commutator"]["all_transition_commutators_zero"]
    assert result["exact_commutator"]["noncommutative_witness"] is None


def test_scalar_fixture_is_finite_only() -> None:
    result = scalar_s3_representation_certificate_v034()
    assert result["finite_scope_only"]
    assert not result["infinite_extension_claimed"]
    assert result["exact_numeric_distinction"] == "EXACT_RATIONAL"
