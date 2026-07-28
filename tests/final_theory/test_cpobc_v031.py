from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from universe_lab.final_theory.cpobc_v031 import (
    brute_force_bell_family_oracle,
    compile_cpobc_relations_v0_3_1,
    compiler_mutation_checks_v031,
    cpobc_dependency_graph_v031,
    d3_representation_search_v0_3_1,
    free_reduce_word,
    structural_algebra_benchmark_v0_3_1,
)


@pytest.fixture(scope="module")
def compiled() -> dict[str, object]:
    return compile_cpobc_relations_v0_3_1()


def test_complete_n4_compiler_matches_independent_oracle(
    compiled: dict[str, object],
) -> None:
    counts = compiled["counts"]
    assert isinstance(counts, dict)
    assert counts["transition_orbits"] == 131
    assert counts["bell_pair_orbits"] == 373
    assert counts["bell_families"] == 146
    assert counts["compiled_cross_stage_relations"] == 641
    assert counts["equal_size_relations"] == 71
    assert counts["unequal_size_relations"] == 570
    assert counts["denominator_cleared_word_equations"] == 783
    assert counts["d3_matrix_entry_polynomial_equations"] == 7047
    assert counts["d3_inverse_entry_polynomial_constraints"] == 11538
    assert counts["MSR_operator_constraints"] == 24
    assert counts["d3_MSR_entry_polynomial_equations"] == 216
    assert counts["canonical_word_classes"] == 2

    verification = compiled["independent_brute_force_verification"]
    assert isinstance(verification, dict)
    assert verification["exact_match"]
    assert verification["route_representative_digest_match"]
    assert (
        verification["production_semantic_descriptor_sha256"]
        == verification["oracle"]["semantic_descriptor_sha256"]
        == "9c97fe86470f0da307d3418e192f55e3ca1f05e7cbd0d18f053a20f28d593bab"
    )
    assert (
        verification["production_family_stage_descriptor_sha256"]
        == verification["oracle"]["family_stage_descriptor_sha256"]
    )
    assert compiled["passed"]
    assert compiled["verdict"] == "CPOBC_COMPILER_COMPLETE_N4"


def test_independent_oracle_uses_a_separate_enumeration_route() -> None:
    oracle = brute_force_bell_family_oracle()

    assert oracle["shared_production_code_paths"] == []
    assert "forward-relation-mask" in oracle["method"]
    assert oracle["poset_counts"] == {"1": 1, "2": 2, "3": 5, "4": 16}
    assert oracle["transition_orbits"] == 131
    assert oracle["bell_pair_orbits"] == 373
    assert oracle["bell_families"] == 146
    assert oracle["compiled_cross_stage_relations"] == 641
    assert oracle["semantic_descriptor_count"] == 641


def test_every_relation_has_requested_operator_and_provenance_fields(
    compiled: dict[str, object],
) -> None:
    required = {
        "relation_id",
        "stage",
        "source_causet",
        "target_causet",
        "canonical_causet_hash",
        "transition_orbit",
        "Bell_partner",
        "Bell_pair",
        "Bell_family",
        "full_precursor",
        "reduced_precursor",
        "spectator_set",
        "precursor_cardinalities",
        "branch",
        "branch_normalisation",
        "CPOBC_operator_ordering",
        "equal_size_auxiliary_relation",
        "MSR_dependency",
        "GC_dependency",
        "invertibility_dependency",
        "automorphism_multiplicity",
        "raw_noncommutative_relation",
        "canonical_word_form",
        "inverse_containing_form",
        "denominator_cleared_form",
        "matrix_entry_polynomial_form",
        "paper_equation_correspondence",
        "dependency_status",
        "completeness_scope",
    }
    relations = compiled["relations"]
    assert isinstance(relations, list)
    assert len(relations) == 641
    assert all(required <= relation.keys() for relation in relations)
    assert all(
        relation["dependency_status"]["classification"]
        == "GENERATED_EQUIVALENT_TO_PAPER"
        and not relation["dependency_status"]["new_relation_claim"]
        for relation in relations
    )
    assert all(
        relation["matrix_entry_polynomial_form"]["entry_equation_count"]
        == (
            27 if relation["branch"] == "EQUAL" else 9
        )
        for relation in relations
    )
    nonroot_low = next(
        relation
        for relation in relations
        if relation["stage"]["m"] > relation["Bell_family"]["core_stage"]
    )
    assert (
        nonroot_low["reduced_precursor"]["canonical_reduced_source"][
            "canonical_causet_hash"
        ]
        != ""
    )
    assert "need not be the selected lower-stage" in nonroot_low[
        "reduced_precursor"
    ]["interpretation"]


def test_noncommutative_order_inverse_and_equal_branch_are_guarded(
    compiled: dict[str, object],
) -> None:
    relations = compiled["relations"]
    assert isinstance(relations, list)
    unequal = next(item for item in relations if item["branch"] == "GREATER")
    equal = next(item for item in relations if item["branch"] == "EQUAL")

    unequal_words = unequal["raw_noncommutative_relation"][0]
    assert unequal_words["lhs_word"] == ["A_n", "A_prime_m"]
    assert unequal_words["rhs_word"] == ["A_m", "A_prime_n"]
    assert equal["equal_size_auxiliary_relation"]["equation_ids"] == [
        "equal_second_orientation",
        "eq104",
    ]
    assert len(
        unequal["inverse_containing_form"]["two_sided_inverse_constraints"]
    ) == 2
    assert (
        unequal["inverse_containing_form"]["matrix_entry_constraint_count"]
        == 18
    )
    assert (
        unequal["inverse_containing_form"]["inverse_encoding"]
        == "METHOD_A_EXPLICIT_TWO_SIDED_INVERSE_VARIABLES"
    )
    assert free_reduce_word(("X", "Y", "X^-1")) == ("X", "Y", "X^-1")
    assert free_reduce_word(("X", "X^-1", "Y")) == ("Y",)


def test_dependency_graph_is_typed_and_keeps_partial_ideal_boundary(
    compiled: dict[str, object],
) -> None:
    graph = cpobc_dependency_graph_v031(compiled)

    assert graph["passed"]
    assert graph["counts"]["compiled_relation_nodes"] == 641
    assert graph["counts"]["Bell_pair_nodes"] == 373
    assert graph["counts"]["Bell_family_nodes"] == 146
    assert graph["counts"]["MSR_constraint_nodes"] == 24
    assert graph["dependency_tests"]["all_compiled_relations_have_CPOBC_edge"]
    assert graph["dependency_tests"]["equal_size_relations_have_eq104"]
    assert graph["dependency_tests"]["independent_ideal_membership"] == "NOT_RUN"
    assert graph["verdict"] == "CPOBC_DEPENDENCY_GRAPH_PARTIAL_EXACT"


def test_all_required_d3_strata_are_declared_without_false_exhaustion() -> None:
    manifest = structural_algebra_benchmark_v0_3_1()
    expected = {
        "D3_SCALAR",
        "D3_THREE_DISTINCT_EIGENVALUES",
        "D3_REPEATED_DIAGONALISABLE",
        "D3_JORDAN_2_PLUS_1",
        "D3_JORDAN_3",
        "D3_BLOCK_REDUCIBLE",
        "D3_REDUCIBLE_INDECOMPOSABLE",
    }

    assert {item["stratum"] for item in manifest["strata"]} == expected
    assert manifest["coverage"]["fully_solved_strata"] == 0
    assert manifest["coverage"]["partially_searched_strata"] == 2
    assert "overlap" in manifest["coverage"]["overlap_note"]
    assert all(
        {
            "gauge_choice",
            "residual_gauge_group",
            "variables",
            "equations",
            "invertibility_conditions",
            "noncommutativity_condition",
            "excluded_loci",
            "solver",
            "completeness_scope",
            "timeout",
            "memory_limit",
            "unresolved_components",
        }
        <= item.keys()
        for item in manifest["strata"]
    )


def test_exact_scaled_heisenberg_ansatz_no_go_is_strictly_scoped() -> None:
    search = d3_representation_search_v0_3_1()
    ansatz = search["executed_ansatz"]

    assert search["CPOBC_D3_STATUS"] == "CPOBC_D3_SEARCH_INCONCLUSIVE"
    assert (
        search["BOUNDED_ANSATZ_STATUS"]
        == "CPOBC_D3_NO_GO_UNDER_ASSUMPTIONS"
    )
    assert search["verdict"] == "CPOBC_D3_SEARCH_INCONCLUSIVE"
    assert "Q_j=q_j*[[1,j*t,0]" in ansatz["definition"]
    assert (
        ansatz["noncommutativity"]["witness_polynomial"] == "-6*t"
    )
    assert (
        ansatz["noncommutativity"]["commutator_Q1_Q2"]["sha256"]
        == "876ce4a4bbf8630bb79fe9e2bbf768b515fa710777b516543db9a9a2f16666dd"
    )
    assert ansatz["bounded_no_go"]["eq145_polynomial"] == "-5*t/2"
    assert ansatz["bounded_no_go"]["groebner_basis"] == ["1"]
    assert ansatz["bounded_no_go"]["unit_ideal"]
    assert all(
        certificate["zero"]
        for certificate in ansatz["necessary_relation_family"]["eq119"].values()
    )
    assert ansatz["necessary_relation_family"]["eq130"]["zero"]
    assert ansatz["necessary_relation_family"]["eq163"]["zero"]
    assert not ansatz["necessary_relation_family"][
        "eq145_generated_from_eq139"
    ]["zero"]
    assert ansatz["exact_invertibility"]["all_determinants_nonzero_polynomials"]
    assert not ansatz["full_compiled_relation_assignment_checked"]
    assert not ansatz["MSR_checked"]
    assert not ansatz["GC_checked"]
    assert not ansatz["CPOBC_representation_found"]
    assert "not a no-go" in search["prohibited_inference"]
    assert search["CPOBC_D4_STATUS"] == "CPOBC_HIGHER_DIMENSION_NOT_EXECUTED"


def test_eq145_mutation_catches_false_necessary_relation_survivor() -> None:
    ansatz = d3_representation_search_v0_3_1()["executed_ansatz"]
    point = ansatz["t_equals_1_mutation_witness"]

    assert all(
        certificate["zero"]
        for certificate in point["relation_residuals"]["eq119"].values()
    )
    assert point["relation_residuals"]["eq130"]["zero"]
    assert point["relation_residuals"]["eq163"]["zero"]
    assert not point["relation_residuals"]["eq145"]["zero"]
    assert point["detected_by_eq145"]


def test_critical_compiler_mutations_are_detected(
    compiled: dict[str, object],
) -> None:
    result = compiler_mutation_checks_v031(compiled)

    assert result["passed"]
    assert result["detected_count"] == result["critical_mutation_count"]
    assert result["critical_mutation_count"] >= 16
    assert all(result["checks"].values())


def test_public_apis_are_deterministic_and_resource_bounded() -> None:
    first = compile_cpobc_relations_v0_3_1(2)
    second = compile_cpobc_relations_v0_3_1(2)

    assert first["compiler_digest_sha256"] == second["compiler_digest_sha256"]
    assert json.dumps(first, sort_keys=True) != ""
    with pytest.raises(ValueError, match="1 <= max_n <= 4"):
        compile_cpobc_relations_v0_3_1(5)
    with pytest.raises(TypeError, match="integer"):
        compile_cpobc_relations_v0_3_1(2.0)  # type: ignore[arg-type]


def test_checked_in_phase_c_to_e_artifacts_and_certificate_hashes() -> None:
    root = Path(__file__).resolve().parents[2]
    result_names = [
        "v0.3.1_cpobc_relations_n4.json",
        "v0.3.1_cpobc_dependency_graph.json",
        "v0.3.1_d3_strata_manifest.json",
        "v0.3.1_d3_representation_search.json",
    ]
    report_names = [
        "v0.3.1_cpobc_compiler.md",
        "v0.3.1_structural_algebra.md",
        "v0.3.1_d3_representation_search.md",
    ]

    for name in result_names:
        payload = json.loads((root / "results" / name).read_text(encoding="utf-8"))
        assert payload["schema_version"].endswith("v0.3.1")
        assert payload["branch"].startswith("codex/final-theory-v0.3.1")
        assert payload["source_commit"] == (
            "3ccbc66cc2cf868bf2a33ab96d4dd46e729d5f09"
        )
        assert payload["certificate_hashes"]
        assert payload["unresolved_components"]
        for record in payload["certificate_hashes"]:
            certificate = root / record["path"]
            assert certificate.is_file()
            assert hashlib.sha256(certificate.read_bytes()).hexdigest() == record[
                "sha256"
            ]

    report_dir = root / "Final-Theory-Program" / "reports"
    assert all((report_dir / name).is_file() for name in report_names)
