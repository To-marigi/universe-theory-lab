from __future__ import annotations

import pytest

from universe_lab.final_theory.atomisation_v033 import (
    VERDICT_COMPLETE,
    atomisation_mutation_checks,
    atomise_element,
    compile_atomisation_paths_n4,
    eligible_nongregarious_maximal_elements,
    is_antichain,
    relation_rank,
)


def test_atomisation_step_requires_a_nongregarious_maximal_element() -> None:
    chain = (2, 0)
    assert eligible_nongregarious_maximal_elements(chain) == (1,)
    atomised = atomise_element(chain, 1)
    assert is_antichain(atomised)
    assert relation_rank(atomised) < relation_rank(chain)
    with pytest.raises(ValueError, match="non-gregarious maximal"):
        atomise_element(chain, 0)


def test_all_twenty_non_antichain_causets_and_all_paths_are_compiled() -> None:
    result = compile_atomisation_paths_n4()
    assert result["passed"]
    assert result["verdict"] == VERDICT_COMPLETE
    assert result["counts"]["non_antichain_causets"] == 20
    assert result["counts"]["non_antichain_causets_by_stage"] == {
        "1": 0,
        "2": 1,
        "3": 4,
        "4": 15,
    }
    assert result["counts"]["complete_atomisation_paths"] == 34


def test_every_choice_is_retained_and_every_path_terminates() -> None:
    result = compile_atomisation_paths_n4()
    assert result["proof_obligations"]["all_eligible_choices_recursed"]
    assert result["proof_obligations"]["all_terminals_antichains"]
    assert result["proof_obligations"]["ranking_strictly_decreases"]
    for record in result["causets"]:
        assert len(record["all_alternative_paths"]) == record["complete_path_count"]
        for path in record["all_alternative_paths"]:
            assert path["terminal_antichain"]
            assert all(
                step["ranking_decrease"] > 0 for step in path["steps"]
            )


def test_B_factors_reconstruct_both_sides_of_each_atomisation_square() -> None:
    result = compile_atomisation_paths_n4()
    assert result["proof_obligations"]["B_and_gregarious_targets_reconstructed"]
    for record in result["causets"]:
        for path in record["all_alternative_paths"]:
            assert len(path["B_operator_factors"]) == path["path_length"]
            assert path["S_word_ordered"] == [
                factor["B_operator_symbol"]
                for factor in path["B_operator_factors"]
            ]
            assert path["S_inverse_word_ordered"] == [
                f"{factor['B_operator_symbol']}^-1"
                for factor in reversed(path["B_operator_factors"])
            ]


def test_atomisation_automorphism_paths_are_recorded_without_quotienting() -> None:
    result = compile_atomisation_paths_n4()
    assert not result["proof_obligations"][
        "automorphism_equivalent_paths_quotiented"
    ]
    assert all(
        not path["automorphism_orbit"]["quotiented"]
        for record in result["causets"]
        for path in record["all_alternative_paths"]
    )


def test_atomisation_critical_mutations_are_detected() -> None:
    checks = atomisation_mutation_checks()
    assert checks
    assert all(checks.values())
