from __future__ import annotations

from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
    compile_localised_polynomial_systems_v034,
)


def test_localised_systems_keep_source_branches_separate() -> None:
    result = compile_localised_polynomial_systems_v034()
    assert result["passed"]
    assert not result["branch_relations_mixed"]
    assert set(result["systems"]) == {DERIVED_BRANCH, LITERAL_BRANCH}
    assert result["systems"][DERIVED_BRANCH]["maximum_Q_index"] == 4
    assert result["systems"][LITERAL_BRANCH]["maximum_Q_index"] == 5
    assert (
        result["systems"][DERIVED_BRANCH]["finite_classification_scope"]
        != result["systems"][LITERAL_BRANCH]["finite_classification_scope"]
    )


def test_denominator_clearing_is_not_reported_as_saturation() -> None:
    result = compile_localised_polynomial_systems_v034()
    plan = result["saturation_plan"]
    assert not plan["numerator_ideal_only_is_sufficient"]
    assert not plan["one_giant_product_expanded"]
    assert plan["status"] == "COMPILED_NOT_FULLY_EXECUTED"
    assert result["denominator_factors"]
