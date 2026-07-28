from __future__ import annotations

from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    REACHABLE_STATE_PROFILE,
)
from universe_lab.final_theory.operator_gc_v033 import (
    VERDICT_COMPLETE,
    compile_local_operator_gc_n4,
    enumerate_labelled_growth_paths,
    local_gc_mutation_checks,
)


def test_naturally_labelled_growth_path_inventory() -> None:
    levels = enumerate_labelled_growth_paths()
    assert {stage: len(paths) for stage, paths in levels.items()} == {
        1: 1,
        2: 2,
        3: 7,
        4: 40,
        5: 357,
    }
    assert all(
        path["path_length"] == stage - 1
        for stage, paths in levels.items()
        for path in paths
    )


def test_operator_words_put_later_transitions_on_the_left() -> None:
    levels = enumerate_labelled_growth_paths()
    for paths in levels.values():
        for path in paths:
            expected = [
                transition["quotient_operator_symbol"]
                for transition in reversed(path["transitions"])
            ]
            assert path["ordered_operator_word_later_on_left"] == expected


def test_spanning_tree_basis_generates_every_same_endpoint_pair() -> None:
    result = compile_local_operator_gc_n4()
    assert result["passed"]
    assert result["verdict"] == VERDICT_COMPLETE
    assert result["counts"]["unlabelled_endpoints_by_stage"] == {
        "1": 1,
        "2": 2,
        "3": 5,
        "4": 16,
        "5": 63,
    }
    assert result["counts"]["spanning_tree_basis_relations"] == 320
    assert result["counts"]["same_endpoint_path_pairs"] == 1529
    assert all(item["derivable"] for item in result["all_pair_derivations"])
    assert result["proof_obligations"]["basis_connectivity"]["passed"]


def test_strong_and_reachable_state_profiles_never_share_an_operator_ideal() -> None:
    result = compile_local_operator_gc_n4()
    strong = result["semantic_profiles"][PAPER_STRONG_OPERATOR_PROFILE]
    weak = result["semantic_profiles"][REACHABLE_STATE_PROFILE]
    assert len(strong["operator_ideal_relations"]) == 320
    assert weak["operator_ideal_relations"] == []
    assert len(weak["state_path_equalities"]) == 320


def test_operator_gc_critical_mutations_are_detected() -> None:
    checks = local_gc_mutation_checks()
    assert checks
    assert all(checks.values())
