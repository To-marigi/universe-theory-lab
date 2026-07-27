from __future__ import annotations

import json

import pytest

from universe_lab.final_theory.cpobc_v03 import (
    compile_cpobc_relations,
    cpobc_representation_search,
    paper_regression_benchmark,
)


def test_minimal_paper_regression_preserves_noncommutative_order() -> None:
    result = paper_regression_benchmark()

    assert result["passed"]
    assert result["status"] == "MINIMAL_EXACT_REGRESSION_PASS"
    assert result["paper_regression_status"] == "PAPER_REGRESSION_PASS"
    assert result["precursor_size_convention"][
        "set_inclusion_is_not_used_as_the_order_key"
    ]
    assert result["equations_103_to_106"]["equal"]["verified"]
    assert result["representative_relations"]["eq119_two_pauli_directions"][
        "zero"
    ]
    assert result["representative_relations"]["eq130_commutator"]["zero"]
    assert not result["representative_relations"][
        "eq164_three_distinct_pauli_obstruction"
    ]["zero"]

    ordering = result["msr_gc_operator_order_fixture"]
    assert ordering["cpobc_eq140_residual"]["zero"]
    assert ordering["msr_residual"]["zero"]
    assert ordering["gc_two_path_residual"]["zero"]
    assert ordering["ordered_product_is_detectably_noncommutative"]


def test_pauli_fixture_is_reference_regression_not_new_d2_search() -> None:
    fixture = paper_regression_benchmark()["s1_s2_pauli_fixture"]

    assert fixture["dimension"] == 2
    assert fixture["all_required_operators_invertible"]
    assert fixture["rejected_exactly"]
    assert not fixture["eq163_commutator"]["zero"]
    assert "paper regression only" in fixture["role"]


def test_compiler_derives_exact_bell_families_through_stage_four() -> None:
    result = compile_cpobc_relations()

    assert result["passed"]
    assert result["status"] == "EXACT_FINITE_PARTIAL_CPOBC_COMPILER"
    assert result["cpobc_relation_status"] == "CPOBC_RELATION_COMPILER_PARTIAL"
    assert result["counts"] == {
        "transition_orbits": 131,
        "bell_pair_orbits": 373,
        "bell_families": 146,
        "compiled_cross_stage_relations": 641,
        "equal_size_relations": 71,
        "unequal_size_relations": 570,
        "stage_bell_pair_orbits": {
            "1": 1,
            "2": 7,
            "3": 44,
            "4": 321,
        },
    }
    assert result["transition_graph"]["level_node_counts"] == {
        "1": 1,
        "2": 2,
        "3": 5,
        "4": 16,
        "5": 63,
    }
    assert result["novelty"]["independent_relations_claimed"] == 0
    assert "INCOMPLETE_RELATIVE_TO_PAPER" in result["completeness"][
        "paper_operator_equations"
    ]


def test_compiled_records_expose_required_dependency_and_order_fields() -> None:
    result = compile_cpobc_relations(3)
    required = {
        "id",
        "hash",
        "stages",
        "transition_pair",
        "family",
        "precursors",
        "spectators",
        "cardinalities",
        "equal_vs_unequal",
        "operator_order",
        "invertibility",
        "GC",
        "MSR",
        "automorphism_multiplicities",
        "generated_equation",
        "denominator_cleared_form",
        "paper_correspondence",
        "dependency",
        "novelty",
    }

    assert result["relations"]
    assert all(required <= relation.keys() for relation in result["relations"])
    assert all(
        relation["MSR"]["stage_n_source_partition"]["exact_partition"]
        and relation["MSR"]["stage_m_source_partition"]["exact_partition"]
        for relation in result["relations"]
    )
    assert all(
        not relation["novelty"]["independent_relation_claimed"]
        and relation["dependency"]["exact_ideal_membership"] == "NOT_RUN"
        for relation in result["relations"]
    )


def test_equal_size_compilation_adds_second_orientation_and_eq104() -> None:
    result = compile_cpobc_relations(3)
    equal_relation = next(
        relation
        for relation in result["relations"]
        if relation["equal_vs_unequal"] == "EQUAL_PRECURSOR_SIZE"
    )
    cleared = equal_relation["denominator_cleared_form"][
        "noncommutative_polynomial_equations"
    ]

    assert equal_relation["operator_order"]["both_orientations_required"]
    assert [equation["equation_id"] for equation in cleared] == [
        "eq103",
        "equal_second_orientation",
        "eq104",
    ]
    assert equal_relation["paper_correspondence"]["equations"] == [
        103,
        104,
        106,
    ]
    assert len(equal_relation["generated_equation"]["solved_forms"]) == 2


def test_compiler_is_deterministic_json_ready_and_resource_bounded() -> None:
    first = compile_cpobc_relations(2)
    second = compile_cpobc_relations(2)

    assert first["compiler_digest_sha256"] == second["compiler_digest_sha256"]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    with pytest.raises(ValueError, match="1 <= max_n <= 4"):
        compile_cpobc_relations(5)
    with pytest.raises(TypeError, match="integer"):
        compile_cpobc_relations(2.0)  # type: ignore[arg-type]


def test_d_ge_3_search_is_exact_structured_and_claim_scoped() -> None:
    result = cpobc_representation_search()

    assert result["passed"]
    assert result["status"] == "CPOBC_REPRESENTATION_SEARCH_INCONCLUSIVE"
    assert result["cpobc_representation_status"] == "CPOBC_SEARCH_INCONCLUSIVE"
    assert result["manifest"]["new_work_minimum_dimension"] == 3
    assert result["manifest"]["new_work_dimensions"] == [3, 4]
    assert set(result["manifest"]["exact_fields"]) == {
        "Q",
        "Q(i)",
        "Q(sqrt(2))",
        "Q(sqrt(-3))",
    }
    assert result["manifest"]["exhaustive_within_listed_grid"]
    assert result["summary"]["commuting_controls_pass"]
    assert not result["summary"]["noncommutative_representation_found"]
    assert result["summary"]["full_compiled_relation_certificate_count"] == 0
    assert "dimension-wide no-go" in result["prohibited_inference"]
    assert json.dumps(result, sort_keys=True)


def test_ansatz_failures_are_class_scoped_with_structural_certificates() -> None:
    result = cpobc_representation_search()
    search_classes = [
        summary
        for summary in result["ansatz_class_summaries"]
        if summary["role"] == "NEW_D_GE_3_SEARCH"
    ]

    assert search_classes
    assert all(
        summary["result"]
        in {"NO_CANDIDATE_IN_DECLARED_EXACT_GRID", "INCONCLUSIVE"}
        for summary in search_classes
    )
    assert all(summary["exhaustive_within_manifest"] for summary in search_classes)
    for certificate in result["candidate_certificates"]:
        structural = certificate["structural_analysis"]
        assert certificate["dimension"] >= 3
        assert "joint_centralizer" in structural
        assert "generated_algebra_span" in structural
        assert "reducibility" in structural
        assert "jordan_strata" in structural
        assert "generator_determinants" in structural
        assert "generator_traces" in structural
