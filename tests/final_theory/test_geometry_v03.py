from __future__ import annotations

import json
from fractions import Fraction
from typing import Any

import pytest

from universe_lab.final_theory.dynamics_v02 import propagate_distribution
from universe_lab.final_theory.geometry_v03 import geometry_interference_benchmark


def _fraction(record: dict[str, int]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


@pytest.fixture(scope="module")
def geometry_result() -> dict[str, Any]:
    return geometry_interference_benchmark()


def test_benchmark_is_deterministic_exact_and_json_serializable(
    geometry_result: dict[str, Any],
) -> None:
    repeated = geometry_interference_benchmark()
    assert json.dumps(geometry_result, sort_keys=True) == json.dumps(
        repeated, sort_keys=True
    )
    assert geometry_result["passed"]
    assert geometry_result["gate_status"] == "PASS_EXACT_CONSERVATIVE_CLASSIFICATION"
    assert geometry_result["completeness"]["arithmetic"].startswith("exact")
    assert geometry_result["completeness"]["kraus_labelled_path_counts_by_stage"] == {
        "0": 1,
        "1": 1,
        "2": 2,
        "3": 6,
        "4": 28,
        "5": 195,
    }


def test_paths_endpoints_and_vertex_label_fibres_are_not_conflated(
    geometry_result: dict[str, Any],
) -> None:
    completeness = geometry_result["completeness"]
    assert completeness["unlabeled_causet_counts_by_stage"]["5"] == 63
    assert completeness["kraus_labelled_path_counts_by_stage"]["5"] == 195
    assert completeness["expanded_birth_labelled_history_counts_by_stage"]["5"] == 357

    semantics = geometry_result["implemented_semantics"]
    assert semantics["represented_labelled_histories"] == (
        "Kraus/outcome-labelled quotient paths only"
    )
    assert "vertex birth-labelled causal-set histories" in semantics[
        "not_represented_as_basis_histories"
    ]
    quotient = geometry_result["label_covariance_and_quotient_consistency"]
    assert quotient["passed"]
    assert quotient["precursor_orbits_partition_raw_downsets"]
    assert quotient["all_orbit_members_have_same_unlabeled_target"]
    assert quotient["path_fibres_match_natural_labeling_oracle"]


def test_path_pushforward_is_the_existing_exact_instrument_distribution(
    geometry_result: dict[str, Any],
) -> None:
    pushed_forward: dict[str, Fraction] = {}
    for path in geometry_result["paths_by_stage"]["5"]:
        endpoint = path["final_unlabeled_causet"]
        pushed_forward[endpoint] = pushed_forward.get(endpoint, Fraction(0)) + _fraction(
            path["path_probability"]
        )
    assert pushed_forward == propagate_distribution(5)[-1]
    assert sum(pushed_forward.values(), start=Fraction(0)) == 1


def test_every_off_diagonal_entry_and_quantum_measure_axiom_is_certified(
    geometry_result: dict[str, Any],
) -> None:
    functional = geometry_result["decoherence_functional"]
    matrix = functional["sparse_exact_matrix"]
    assert len(functional["basis"]) == 195
    assert matrix["ordered_off_diagonal_entry_count"] == 195 * 194
    assert matrix["nonzero_off_diagonal_entries"] == []
    assert len(matrix["diagonal_entries"]) == 195

    certificates = functional["certificates"]
    assert certificates["hermiticity"]["passed"]
    assert certificates["biadditivity"]["passed"]
    assert certificates["strong_positivity"]["passed"]
    assert certificates["normalization"]["passed"]
    assert _fraction(certificates["normalization"]["D_omega_omega"]) == 1
    assert all(
        audit["all_off_diagonal_entries_exactly_zero"]
        and audit["normalization_exact"]
        and audit["hermiticity_exact"]
        and audit["strong_positivity_exact"]
        for audit in geometry_result["stage_decoherence_audits"]
    )


def test_i2_and_grade2_are_exhaustive_on_final_causet_events(
    geometry_result: dict[str, Any],
) -> None:
    interference = geometry_result["interference_I2"]
    assert interference["unordered_pair_count"] == 63 * 62 // 2
    assert interference["unordered_pair_count"] == interference[
        "expected_complete_pair_count"
    ]
    assert interference["all_exact_I2_zero"]
    assert all(_fraction(record["I2"]) == 0 for record in interference["pair_results"])

    grade2 = geometry_result["grade2_sum_rule"]
    assert grade2["pairwise_disjoint_final_event_triples_checked"] == 63 * 62 * 61 // 6
    assert grade2["pairwise_disjoint_final_event_triples_checked"] == grade2[
        "expected_complete_triple_count"
    ]
    assert grade2["passed_exactly"]
    assert _fraction(grade2["witness"]["grade2_residual"]) == 0


def test_semantic_mutants_are_rejected_for_the_right_reasons(
    geometry_result: dict[str, Any],
) -> None:
    guards = geometry_result["mutation_guards"]
    assert guards["passed"]
    assert guards["checks"]["coherent_sum_masquerade"]["killed"]
    assert (
        guards["checks"]["coherent_sum_masquerade"]["coherent_sum_mutant_I2"][
            "square_root_radicand"
        ]["numerator"]
        > 0
    )
    assert guards["checks"]["forced_zero_generic"]["killed"]
    assert _fraction(
        guards["checks"]["forced_zero_generic"]["coincident_ray_and_record_control"]
    ) == Fraction(1, 2)
    assert guards["checks"]["arbitrary_kraus_basis_histories"]["killed"]
    assert guards["checks"]["labelled_unlabeled_confusion"]["killed"]

    boundary = geometry_result["kraus_representation_boundary"]
    assert boundary["unitary_kraus_mixing_may_preserve_channel"]
    assert not boundary["unitary_kraus_mixing_preserves_fixed_outcome_events"]
    assert not boundary["arbitrary_kraus_basis_histories_accepted"]


def test_conservative_classification_and_scope_are_explicit(
    geometry_result: dict[str, Any],
) -> None:
    assert geometry_result["geometry_quantumness_status"] == (
        "CLASSICAL_GEOMETRY_WITH_QUANTUM_MEMORY"
    )
    assert geometry_result["classification"]["geometry"] == (
        "CLASSICAL_GEOMETRY_WITH_QUANTUM_MEMORY"
    )
    assert geometry_result["classification"]["interference"].startswith("NO_NONZERO")
    assert not geometry_result["initial_state_scope"][
        "arbitrary_initial_superpositions_certified"
    ]
    assert geometry_result["resource_boundary"]["beyond_n5"] == "NOT_RUN_AND_NOT_CERTIFIED"
    assert geometry_result["unresolved_items"]


@pytest.mark.parametrize("bad_max_n", [-1, 6])
def test_resource_boundary_rejects_out_of_domain_cardinality(bad_max_n: int) -> None:
    with pytest.raises(ValueError, match="0 <= max_n <= 5"):
        geometry_interference_benchmark(bad_max_n)
