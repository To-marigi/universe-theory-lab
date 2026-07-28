from __future__ import annotations

from universe_lab.final_theory.eq112_reduction_v033 import (
    VERDICT_NECESSARY,
    compile_eq112_reduction_n4,
    eq112_mutation_checks,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    SOURCE_VERDICT,
)


def test_all_twenty_G_generators_and_thirty_four_paths_are_reduced() -> None:
    result = compile_eq112_reduction_n4()
    assert result["passed"]
    assert result["verdict"] == VERDICT_NECESSARY
    assert result["semantic_profile"] == PAPER_STRONG_OPERATOR_PROFILE
    assert result["counts"]["non_antichain_G_generators"] == 20
    assert result["counts"]["atomisation_paths"] == 34
    assert result["counts"]["atomisation_square_instances"] == 76


def test_every_atomisation_square_is_derived_from_the_local_gc_basis() -> None:
    result = compile_eq112_reduction_n4()
    assert all(
        square["derivable_from_local_GC_basis"]
        for square in result["local_GC_atomisation_squares"]
    )
    assert all(
        square["semantic_profile"] == PAPER_STRONG_OPERATOR_PROFILE
        for square in result["local_GC_atomisation_squares"]
    )


def test_recursive_B_dependency_graph_is_complete_and_cycle_free() -> None:
    result = compile_eq112_reduction_n4()
    assert result["recursive_B_expansion"][
        "all_B_signatures_found_in_v032_reduction_map"
    ]
    assert result["counts"]["distinct_B_forward_definitions"] == 22
    assert result["counts"]["formal_B_inverse_auxiliaries"] == 22
    assert result["dependency_DAG"]["cycle_free"]
    assert result["dependency_DAG"]["cycles"] == []
    assert result["dependency_DAG"]["construction_time_cycle_observations"] == []


def test_eq113_branches_are_separate_and_literal_branch_exposes_Q5() -> None:
    result = compile_eq112_reduction_n4()
    assert result["source_index_audit"]["verdict"] == SOURCE_VERDICT
    branches = result["path_consistency_branches"]
    assert set(branches) == {"EQ113_QN_BRANCH", "EQ113_QN_PLUS_1_BRANCH"}
    assert len(branches["EQ113_QN_BRANCH"]) == 25
    assert len(branches["EQ113_QN_PLUS_1_BRANCH"]) == 25
    assert result["counts"]["literal_Qn_plus_1_relations_requiring_Q5"] == 24


def test_reduction_is_not_mislabelled_as_reverse_equivalent() -> None:
    result = compile_eq112_reduction_n4()
    obligations = result["equivalence_obligations"]
    assert obligations["forward"]["passed"]
    assert not obligations["reverse"]["passed"]
    assert obligations["presentation_status"] == "ONE_WAY_NECESSARY_REDUCTION"
    assert not result["recursive_B_expansion"]["auxiliary_minimality_proved"]


def test_eq112_critical_mutations_are_detected() -> None:
    checks = eq112_mutation_checks()
    assert checks
    assert all(checks.values())
