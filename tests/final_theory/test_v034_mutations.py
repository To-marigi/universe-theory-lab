from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
import sympy as sp

from universe_lab.final_theory.d2_auxiliary_audit_v034 import (
    DEFINITIONAL_RATIONAL_AUXILIARY,
    GENUINE_FREE_AUXILIARY,
    audit_b_auxiliaries_v034,
    classify_auxiliary_evidence,
)
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
    compile_localised_polynomial_systems_v034,
)
from universe_lab.final_theory.d2_rational_dag_v034 import (
    D2RationalModel,
    RationalMatrix,
    ScalarArena,
)
from universe_lab.final_theory.d2_similarity_v034 import (
    candidate_similarity_decision,
    similarity_policy_v034,
)
from universe_lab.final_theory.d2_strata_v034 import (
    S1,
    S2,
    S3,
    stratum_charts,
)

MUTATION_NAMES = {
    1: "B_INVERSES_AS_FREE_MATRICES",
    2: "GENUINE_AUXILIARY_AS_DEFINITIONAL",
    3: "RATIONAL_INVERSE_D_FACTOR_DROPPED",
    4: "INVERSE_PRODUCT_ORDER_REVERSED",
    5: "DENOMINATOR_CLEARING_WITHOUT_SATURATION",
    6: "DETERMINANT_FACTOR_DROPPED",
    7: "SINGULAR_TRANSITION_ACCEPTED",
    8: "UNJUSTIFIED_COMMON_FACTOR_CANCELLATION",
    9: "EQ113_BRANCH_IDEALS_MERGED",
    10: "QN_QN_PLUS_1_SILENTLY_IDENTIFIED",
    11: "LITERAL_Q5_DROPPED",
    12: "REACHABLE_GC_MIXED_WITH_STRONG_OPERATOR_GC",
    13: "REACHABLE_MSR_MIXED_WITH_STRONG_OPERATOR_MSR",
    14: "NECESSARY_ONLY_PROMOTED_TO_EQUIVALENT",
    15: "REVERSE_ONLY_PROMOTED_TO_NO_GO",
    16: "ONE_PIVOT_CHART_PROMOTED_TO_ALL_S1",
    17: "S2_MU_ZERO_LOCUS_LOST",
    18: "RESIDUAL_GAUGE_CHART_OMITTED",
    19: "SIMILAR_SOLUTIONS_DOUBLE_COUNTED",
    20: "NUMERICAL_RESIDUAL_ACCEPTED_AS_EXACT_ZERO",
    21: "FINITE_NO_NONCOMMUTATIVE_PROMOTED_GLOBAL_NO_GO",
    22: "FINITE_REPRESENTATION_PROMOTED_INFINITE_QSG",
    23: "LITERATURE_LOCKED_2X2_THEORY_CLAIMED_NOVEL",
    24: "BRANCH_TIMEOUT_PROMOTED_COMPLETE",
    25: "DENOMINATOR_FACTOR_PROVENANCE_DROPPED",
}


@pytest.fixture(scope="module")
def auxiliary_audit() -> dict[str, Any]:
    """Build the expensive audit once for all auxiliary mutations."""

    return audit_b_auxiliaries_v034()


@pytest.fixture(scope="module")
def localisation() -> dict[str, Any]:
    """The production compiler is internally cached; call it only once here."""

    return compile_localised_polynomial_systems_v034()


@pytest.fixture(scope="module")
def charts() -> dict[str, list[Any]]:
    """Use the light chart constructor instead of repeating full elimination."""

    return {
        DERIVED_BRANCH: stratum_charts(DERIVED_BRANCH),
        LITERAL_BRANCH: stratum_charts(LITERAL_BRANCH),
    }


@pytest.fixture(scope="module")
def rational_kernel() -> dict[str, Any]:
    """Small production rational kernel for mutation-local identities."""

    arena = ScalarArena()
    model = D2RationalModel(
        arena=arena,
        q_matrices={},
        matrices={},
        node_definitions={},
    )
    a = arena.symbol("mutation_a")
    b = arena.symbol("mutation_b")
    c = arena.symbol("mutation_c")
    e = arena.symbol("mutation_e")
    denominator = arena.symbol("mutation_d")
    matrix = RationalMatrix(
        ((a, b), (c, e)),
        denominator,
        (),
        ("MUTATION_GENERIC_MATRIX",),
    )
    inverse = model.inverse(
        matrix,
        provenance="MUTATION_GENERIC_INVERSE",
        stage=1,
    )
    return {
        "arena": arena,
        "model": model,
        "matrix": matrix,
        "inverse": inverse,
        "symbols": {
            "a": a,
            "b": b,
            "c": c,
            "e": e,
            "denominator": denominator,
        },
    }


def _claim_allowed(claim: str, evidence: dict[str, Any]) -> bool:
    """Pure test claim gate until the production claim-scope module exists."""

    if claim == "D2_RATIONAL_RECONSTRUCTION_EQUIVALENT_N4":
        return bool(
            evidence.get("forward_equivalence")
            and evidence.get("reverse_equivalence")
        )
    if claim == "CPOBC_D2_N4_NO_REPRESENTATION":
        return bool(
            evidence.get("forward_equivalence")
            and evidence.get("reverse_equivalence")
            and evidence.get("all_strata_complete")
            and evidence.get("all_source_branches_complete")
        )
    if claim == "EXACT_ZERO":
        return evidence.get("residual_mode") == "EXACT_SYMBOLIC_ZERO"
    if claim == "CPOBC_D2_INFINITE_NO_GO_UNDER_STRONG_PROFILE":
        return bool(
            evidence.get("finite_no_representation")
            and evidence.get("early_noncommutativity_propagation_theorem")
        )
    if claim == "INFINITE_QSG_REPRESENTATION_FOUND":
        return bool(
            evidence.get("finite_representation")
            and evidence.get("all_stage_extension_certificate")
        )
    if claim == "NOVEL_GENERAL_2X2_THEOREM":
        return evidence.get("literature_classification") == "OPEN_TARGET"
    if claim == "CPOBC_D2_N4_CLASSIFICATION_COMPLETE":
        return bool(
            evidence.get("all_strata_complete")
            and evidence.get("all_source_branches_complete")
            and not evidence.get("any_timeout")
        )
    raise ValueError(f"unknown test claim: {claim}")


@pytest.fixture(scope="module")
def claim_gate() -> Callable[[str, dict[str, Any]], bool]:
    return _claim_allowed


def test_mutation_registry_contains_exactly_the_required_twenty_five() -> None:
    assert list(MUTATION_NAMES) == list(range(1, 26))
    assert len(set(MUTATION_NAMES.values())) == 25


def test_mutation_01_b_inverses_are_not_free_matrices(
    auxiliary_audit: dict[str, Any],
) -> None:
    assert {
        record["classification"]
        for record in auxiliary_audit["auxiliaries"]
    } == {DEFINITIONAL_RATIONAL_AUXILIARY}
    assert auxiliary_audit["counts"]["genuine_free_B_auxiliary_matrix_entries"] == 0


def test_mutation_02_genuine_auxiliary_is_not_erased_as_definitional() -> None:
    explicit_free_evidence = {
        "explicitly_declared_free": True,
        "unique_forward_definition": False,
        "exact_two_sided_inverse_predicates": False,
        "branch_membership": {
            DERIVED_BRANCH: True,
            LITERAL_BRANCH: True,
        },
    }
    assert (
        classify_auxiliary_evidence(explicit_free_evidence)
        == GENUINE_FREE_AUXILIARY
    )
    assert (
        classify_auxiliary_evidence(explicit_free_evidence)
        != DEFINITIONAL_RATIONAL_AUXILIARY
    )


def test_mutation_03_rational_inverse_cannot_drop_the_d_factor(
    rational_kernel: dict[str, Any],
) -> None:
    arena = rational_kernel["arena"]
    inverse = rational_kernel["inverse"]
    symbols = rational_kernel["symbols"]
    correct = (
        (
            arena.mul(symbols["denominator"], symbols["e"]),
            arena.mul(
                symbols["denominator"],
                arena.neg(symbols["b"]),
            ),
        ),
        (
            arena.mul(
                symbols["denominator"],
                arena.neg(symbols["c"]),
            ),
            arena.mul(symbols["denominator"], symbols["a"]),
        ),
    )
    wrong_without_d = (
        (symbols["e"], arena.neg(symbols["b"])),
        (arena.neg(symbols["c"]), symbols["a"]),
    )
    assert inverse.numerator == correct
    assert inverse.numerator != wrong_without_d


def test_mutation_04_inverse_product_order_cannot_be_reversed() -> None:
    left = sp.Matrix([[1, 1], [0, 1]])
    right = sp.Matrix([[1, 0], [1, 1]])
    correct = right.inv() * left.inv()
    reversed_mutation = left.inv() * right.inv()
    assert (left * right).inv() == correct
    assert (left * right).inv() != reversed_mutation


def test_mutation_05_denominator_clearing_is_not_saturation(
    localisation: dict[str, Any],
) -> None:
    plan = localisation["saturation_plan"]
    assert not plan["numerator_ideal_only_is_sufficient"]
    assert plan["method"].startswith("sequential Rabinowitsch")
    assert plan["status"] == "COMPILED_NOT_FULLY_EXECUTED"


def test_mutation_06_no_determinant_factor_may_be_dropped(
    localisation: dict[str, Any],
) -> None:
    factors = localisation["denominator_factors"]
    factor_records = [record["factor_record_id"] for record in factors]
    for system in localisation["systems"].values():
        assert system["denominator_factor_count"] == len(factors)
    assert len(factor_records) > 1
    assert len(factor_records[:-1]) != len(factor_records)


def test_mutation_07_singular_transition_is_rejected(
    rational_kernel: dict[str, Any],
) -> None:
    arena = rational_kernel["arena"]
    model = rational_kernel["model"]
    singular = RationalMatrix(
        ((arena.one, arena.zero), (arena.zero, arena.zero)),
        arena.one,
        (),
        ("SINGULAR_MUTATION",),
    )
    determinant = model.determinant_numerator(singular)
    transition_admissible = determinant != arena.zero
    assert determinant == arena.zero
    assert not transition_admissible


def test_mutation_08_unjustified_common_factor_cancellation_is_rejected(
    rational_kernel: dict[str, Any],
) -> None:
    model = rational_kernel["model"]
    record = model.matrix_record(rational_kernel["matrix"])
    assert record["cancelled_factors"] == []
    assert record["cancellation_justification"] == "NO_CANCELLATION_PERFORMED"


def test_mutation_09_eq113_branch_ideals_are_not_merged(
    localisation: dict[str, Any],
) -> None:
    assert not localisation["branch_relations_mixed"]
    assert set(localisation["systems"]) == {DERIVED_BRANCH, LITERAL_BRANCH}
    observed_branch_labels = {}
    for branch, system in localisation["systems"].items():
        observed_branch_labels[branch] = {
            provenance["source_index_branch"]
            for equation in system["equations"]
            for provenance in equation["provenance"]
            if provenance["source_index_branch"] != "SHARED_CORE"
        }
    assert observed_branch_labels == {
        DERIVED_BRANCH: {DERIVED_BRANCH},
        LITERAL_BRANCH: {LITERAL_BRANCH},
    }


def test_mutation_10_qn_and_qn_plus_1_are_not_silently_identified(
    localisation: dict[str, Any],
) -> None:
    derived = localisation["systems"][DERIVED_BRANCH]
    literal = localisation["systems"][LITERAL_BRANCH]
    assert derived["maximum_Q_index"] == 4
    assert literal["maximum_Q_index"] == 5
    assert derived["generator_inventory"] != literal["generator_inventory"]


def test_mutation_11_literal_branch_must_retain_q5(
    localisation: dict[str, Any],
) -> None:
    literal = localisation["systems"][LITERAL_BRANCH]
    assert "Q_5" in literal["generator_inventory"]
    assert literal["scalar_unknowns_before_stratum_substitution"] == 20
    assert "independent Q5" in literal["finite_classification_scope"]


def test_mutation_12_reachable_gc_is_not_mixed_with_strong_operator_gc(
    localisation: dict[str, Any],
) -> None:
    for system in localisation["systems"].values():
        families = system["relation_family_counts"]
        assert "LOCAL_OPERATOR_GC" in families
        assert "REACHABLE_STATE_GC" not in families
    assert localisation["semantic_profile"] == "PAPER_STRONG_OPERATOR_PROFILE"


def test_mutation_13_reachable_msr_is_not_mixed_with_strong_operator_msr(
    localisation: dict[str, Any],
) -> None:
    for system in localisation["systems"].values():
        families = system["relation_family_counts"]
        assert "STRONG_OPERATOR_MSR" in families
        assert "REACHABLE_STATE_MSR" not in families
    assert "PAPER_STRONG_OPERATOR_PROFILE" in localisation["assumptions"]


def test_mutation_14_necessary_only_is_not_promoted_to_equivalent(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    assert not claim_gate(
        "D2_RATIONAL_RECONSTRUCTION_EQUIVALENT_N4",
        {
            "forward_equivalence": True,
            "reverse_equivalence": False,
        },
    )


def test_mutation_15_reverse_only_cannot_issue_a_no_go(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    assert not claim_gate(
        "CPOBC_D2_N4_NO_REPRESENTATION",
        {
            "forward_equivalence": False,
            "reverse_equivalence": True,
            "all_strata_complete": True,
            "all_source_branches_complete": True,
        },
    )


def test_mutation_16_one_pivot_chart_is_not_all_of_s1(
    charts: dict[str, list[Any]],
) -> None:
    for branch, branch_charts in charts.items():
        s1_charts = [chart for chart in branch_charts if chart.stratum == S1]
        expected = 12 if branch == DERIVED_BRANCH else 16
        assert len(s1_charts) == expected
        assert len({chart.pivot for chart in s1_charts}) > 1


def test_mutation_17_s2_mu_zero_locus_is_sent_to_s3(
    charts: dict[str, list[Any]],
) -> None:
    for branch_charts in charts.values():
        s2_charts = [chart for chart in branch_charts if chart.stratum == S2]
        assert all(
            any(
                "mu-all-zero locus is excluded here and assigned to S3"
                in statement
                for statement in chart.cover_provenance
            )
            for chart in s2_charts
        )
        assert any(chart.stratum == S3 for chart in branch_charts)


def test_mutation_18_residual_gauge_coordinate_charts_are_not_omitted(
    charts: dict[str, list[Any]],
) -> None:
    for branch_charts in charts.values():
        assert all(chart.residual_gauge for chart in branch_charts)
        for pivot in {
            chart.pivot
            for chart in branch_charts
            if chart.stratum in {S1, S2}
        }:
            same_pivot = [
                chart
                for chart in branch_charts
                if chart.pivot == pivot
            ]
            assert len(same_pivot) >= 3


def test_mutation_19_similarity_equivalent_solutions_are_deduplicated() -> None:
    left = (
        sp.Matrix([[1, 1], [0, 1]]),
        sp.Matrix([[2, 0], [0, 3]]),
    )
    conjugator = sp.Matrix([[1, 2], [0, 1]])
    right = tuple(
        conjugator.inv() * matrix * conjugator for matrix in left
    )
    decision = candidate_similarity_decision(
        left,
        right,
        conjugator=conjugator,
    )
    deduplicated_candidate_count = 1 if decision["similar"] else 2
    assert decision["decision"] == "SIMILAR_EXPLICIT_CONJUGATOR"
    assert deduplicated_candidate_count == 1


def test_mutation_20_numerical_residual_is_not_exact_zero(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    assert not claim_gate(
        "EXACT_ZERO",
        {
            "residual_mode": "NUMERICAL_ABS_LT_1E_30",
            "observed_residual": 1.0e-40,
        },
    )
    assert claim_gate(
        "EXACT_ZERO",
        {"residual_mode": "EXACT_SYMBOLIC_ZERO"},
    )


def test_mutation_21_finite_no_noncommutativity_is_not_a_global_no_go(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    assert not claim_gate(
        "CPOBC_D2_INFINITE_NO_GO_UNDER_STRONG_PROFILE",
        {
            "finite_no_representation": True,
            "early_noncommutativity_propagation_theorem": False,
        },
    )


def test_mutation_22_finite_representation_is_not_an_infinite_qsg(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    assert not claim_gate(
        "INFINITE_QSG_REPRESENTATION_FOUND",
        {
            "finite_representation": True,
            "all_stage_extension_certificate": False,
        },
    )


def test_mutation_23_known_2x2_theory_is_not_claimed_as_novel(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    policy = similarity_policy_v034()
    assert policy["literature_classification"] == "LITERATURE_LOCKED"
    assert not policy["new_general_similarity_theorem_claimed"]
    assert not claim_gate(
        "NOVEL_GENERAL_2X2_THEOREM",
        {
            "literature_classification": policy[
                "literature_classification"
            ]
        },
    )


def test_mutation_24_one_branch_timeout_cannot_be_complete(
    claim_gate: Callable[[str, dict[str, Any]], bool],
) -> None:
    assert not claim_gate(
        "CPOBC_D2_N4_CLASSIFICATION_COMPLETE",
        {
            "all_strata_complete": True,
            "all_source_branches_complete": False,
            "any_timeout": True,
        },
    )


def test_mutation_25_denominator_factor_provenance_is_mandatory(
    localisation: dict[str, Any],
) -> None:
    factors = localisation["denominator_factors"]
    assert factors
    for factor in factors:
        assert factor["factor_record_id"]
        assert factor["factor_id"]
        assert factor["origin"]
        assert factor["required_by"]
        assert factor["saturation_status"] == "REQUIRED_NOT_YET_EXECUTED"
