from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory.causal_sets import (
    causet_id,
    downsets,
    enumerate_unlabeled_posets,
)
from universe_lab.final_theory.commutative_csg_v031 import (
    ONE,
    PAPER_SHA256,
    REFERENCE_PARAMETERS,
    REFERENCE_T2,
    GaussianRational,
    certificate_payloads,
    commutative_csg_reference_benchmark,
    decoherence,
    endpoint_amplitude,
    lambda_value,
    quantum_measure,
    second_order_interference,
    transition_amplitude,
    verify_commutative_csg_certificate,
)

ROOT = Path(__file__).resolve().parents[2]


def _fraction(record: dict[str, int]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


@pytest.fixture(scope="module")
def benchmark() -> dict[str, Any]:
    return commutative_csg_reference_benchmark(5)


def test_reference_is_deterministic_exact_and_regression_only(
    benchmark: dict[str, Any],
) -> None:
    repeated = commutative_csg_reference_benchmark(5)
    assert json.dumps(benchmark, sort_keys=True) == json.dumps(
        repeated, sort_keys=True
    )
    assert benchmark["passed"]
    assert benchmark["verdict"] == "COMMUTATIVE_CSG_REFERENCE_PASS"
    assert benchmark["literature_classification"] == "REGRESSION_ONLY"
    assert benchmark["dimension"] == 1
    assert benchmark["field"] == "Q(i) exact specialization embedded in C"
    assert benchmark["exact_scope"]["floating_point_used"] is False
    assert benchmark["exact_scope"]["random_seed"] is None


def test_parameter_is_the_paper_claim_3_8_specialization(
    benchmark: dict[str, Any],
) -> None:
    assert REFERENCE_PARAMETERS.coupling(0) == ONE
    assert REFERENCE_PARAMETERS.coupling(1).is_zero()
    assert REFERENCE_PARAMETERS.coupling(2) == REFERENCE_T2
    assert REFERENCE_T2 == GaussianRational(Fraction(1), Fraction(1))
    assert REFERENCE_PARAMETERS.coupling(99).is_zero()

    theorem = benchmark["theorem_mapping"]
    assert theorem["source"]["sha256"] == PAPER_SHA256
    assert theorem["source"]["verified_pdf_pages"] == [8, 10, 17, 18]
    hypotheses = theorem["hypothesis_mapping"]
    assert all(hypotheses.values())
    polar = theorem["exact_specialization"]["paper_polar_notation"]
    assert polar["m_number_of_positive_index_nonzero_couplings"] == 1
    assert polar["k1"] == 2
    assert polar["s"] == "sqrt(2)"
    assert polar["phi"] == "pi/4"
    assert theorem["extension_applicability"]["bounded_variation"] == (
        "PASS_BY_CLAIM_3_8_ITEM_2"
    )
    assert theorem["extension_applicability"][
        "unique_sigma_algebra_extension"
    ] == "PASS_BY_THEOREM_2_1"
    assert not theorem["extension_applicability"][
        "finite_n_extrapolation_used"
    ]


def test_lambda_and_every_msr_source_are_exact(
    benchmark: dict[str, Any],
) -> None:
    for stage in range(1, 6):
        expected = GaussianRational(
            Fraction(1 + stage * (stage - 1) // 2),
            Fraction(stage * (stage - 1) // 2),
        )
        assert lambda_value(stage, 0) == expected
        assert not expected.is_zero()

    levels = enumerate_unlabeled_posets(5)
    for stage in range(1, 5):
        for relation in levels[stage]:
            total = GaussianRational(Fraction(0))
            for precursor in downsets(relation):
                total = total + transition_amplitude(relation, precursor)
            assert total == ONE

    audit = benchmark["transition_audit"]
    assert audit["source_count"] == 24
    assert audit["transition_orbit_count"] == 131
    assert audit["raw_labelled_transition_count"] == 172
    assert audit["all_denominators_nonzero"]
    assert audit["MSR_exact"]
    assert audit["automorphism_orbit_amplitude_covariance_exact"]
    assert audit["automorphism_orbit_target_covariance_exact"]
    assert all(
        record["equals_one_exactly"]
        for record in audit["MSR_source_certificates"]
    )
    assert len(benchmark["transition_catalog"]) == 131


def test_scalar_bell_causality_product_rule_is_exhaustive_through_n4(
    benchmark: dict[str, Any],
) -> None:
    bell = benchmark["scalar_bell_causality"]
    assert bell["pair_count"] == 489
    assert bell["nontrivial_common_spectator_pair_count"] == 413
    assert bell["ratio_form_eligible_pair_count"] > 0
    assert bell["zero_safe_product_rule_exact"]
    assert bell["ratio_form_exact_when_defined"]
    assert bell["passed"]
    assert bell["by_source_stage"] == {
        "1": {
            "all_distinct_non_timid_pairs": 0,
            "pairs_with_at_least_one_common_spectator": 0,
        },
        "2": {
            "all_distinct_non_timid_pairs": 4,
            "pairs_with_at_least_one_common_spectator": 3,
        },
        "3": {
            "all_distinct_non_timid_pairs": 46,
            "pairs_with_at_least_one_common_spectator": 37,
        },
        "4": {
            "all_distinct_non_timid_pairs": 439,
            "pairs_with_at_least_one_common_spectator": 373,
        },
    }
    first = bell["first_nontrivial_common_spectator_fixture"]
    assert GaussianRational.from_record(
        first["cross_product_residual"]
    ).is_zero()
    nonzero = bell["first_nonzero_cross_product_fixture"]
    assert nonzero is not None
    assert nonzero["left_cross_product"] == nonzero["right_cross_product"]


def test_gc_path_independence_normalization_and_quotient_are_exact(
    benchmark: dict[str, Any],
) -> None:
    audit = benchmark["general_covariance_path_and_quotient"]
    assert audit["passed"]
    assert audit["path_independence_exact"]
    assert audit["label_quotient_fibre_exact"]
    assert audit["normalization_exact_all_stages"]
    assert audit["direct_endpoint_amplitude_relabel_covariant_exact"]
    assert audit["arbitrary_vertex_permutations_checked"] == 7979
    assert [
        record["quotient_path_count"]
        for record in audit["stage_certificates"]
    ] == [1, 2, 6, 28, 195]
    assert [
        record["expanded_labelled_history_count"]
        for record in audit["stage_certificates"]
    ] == [1, 2, 7, 40, 357]
    assert all(
        GaussianRational.from_record(record["omega_amplitude"]) == ONE
        and record["normalized_exactly"]
        for record in audit["stage_certificates"]
    )

    levels = enumerate_unlabeled_posets(3)
    stage_three = {causet_id(item): item for item in levels[3]}
    assert endpoint_amplitude(stage_three["p3-000"]) == GaussianRational(
        Fraction(2, 5), Fraction(-1, 5)
    )
    assert endpoint_amplitude(stage_three["p3-024"]) == GaussianRational(
        Fraction(3, 5), Fraction(1, 5)
    )


def test_physical_covariant_events_have_exact_nonzero_D_and_I2(
    benchmark: dict[str, Any],
) -> None:
    witness = benchmark["decoherence_functional"][
        "physical_interference_witness"
    ]
    assert witness["stage"] == 3
    assert witness["events_are_exclusive"]
    assert witness["events_are_physically_distinct_unlabeled_geometries"]
    assert witness["not_a_natural_labelling_multiplicity_witness"]
    event_a = witness["event_A"]
    event_b = witness["event_B"]
    assert event_a["event_id"] == "E[p3-000]"
    assert event_a["canonical_relation_rows"] == [0, 0, 0]
    assert event_a["distinct_natural_birth_labelings"] == 1
    assert event_b["event_id"] == "E[p3-024]"
    assert event_b["canonical_relation_rows"] == [4, 4, 0]
    assert event_b["distinct_natural_birth_labelings"] == 1

    amplitude_a = GaussianRational.from_record(event_a["amplitude"])
    amplitude_b = GaussianRational.from_record(event_b["amplitude"])
    expected_d = GaussianRational(Fraction(1, 5), Fraction(1, 5))
    assert decoherence(amplitude_a, amplitude_b) == expected_d
    assert GaussianRational.from_record(witness["D_A_B"]) == expected_d
    assert second_order_interference(amplitude_a, amplitude_b) == Fraction(2, 5)
    assert _fraction(witness["I2_A_B"]) == Fraction(2, 5)
    assert quantum_measure(amplitude_a) == Fraction(1, 5)
    assert quantum_measure(amplitude_b) == Fraction(2, 5)
    assert _fraction(witness["mu_A_union_B"]) == 1


def test_Hermiticity_strong_positivity_grade2_and_normalization_are_exact(
    benchmark: dict[str, Any],
) -> None:
    functional = benchmark["decoherence_functional"]
    assert functional["passed"]
    assert functional["Hermiticity_exact"]
    assert functional["normalization_exact"]
    assert functional["strong_positivity_exact"]
    assert functional["grade2_sum_rule_exact"]
    assert functional["unordered_event_pairs_checked"] == 2084
    assert functional["pairwise_disjoint_event_triples_checked"] == 40281
    strong = functional["strong_positivity_certificate"]
    assert strong["rank_upper_bound"] == 1
    assert strong["all_diagonal_entries_nonnegative"]
    assert strong["all_two_by_two_principal_minors_zero"]
    final = functional["stage_certificates"][-1]
    assert final["covariant_singleton_event_count"] == 63
    assert final["unordered_event_pairs_checked"] == 1953
    assert final["pairwise_disjoint_event_triples_checked"] == 39711
    assert all(
        record["Hermiticity_exact"]
        and record["normalization_exact"]
        and record["strong_positivity_exact"]
        and record["grade2_exact"]
        for record in functional["stage_certificates"]
    )


def test_orthogonal_record_control_remains_distinct(
    benchmark: dict[str, Any],
) -> None:
    comparison = benchmark["orthogonal_record_baseline_comparison"]
    assert comparison["comparison_passed"]
    assert comparison["baseline_status"] == (
        "CLASSICAL_GEOMETRY_WITH_QUANTUM_MEMORY"
    )
    assert comparison["baseline_all_off_diagonals_zero"]
    assert comparison["baseline_all_I2_zero"]
    by_item = {record["item"]: record for record in comparison["comparison"]}
    assert by_item["environment record"]["COMMUTATIVE_CSG_REFERENCE"] == "none"
    assert "orthogonal record" in by_item["environment record"][
        "ORTHOGONAL_RECORD_CLASSICAL_BASELINE"
    ]
    assert by_item["Bell causality"][
        "ORTHOGONAL_RECORD_CLASSICAL_BASELINE"
    ] == "KRAUS_BELL_CAUSALITY_UNDEFINED"
    assert benchmark["mutation_guards"]["force_off_diagonal_D_to_zero"]
    assert benchmark["mutation_guards"][
        "misclassify_orthogonal_record_baseline_as_coherent"
    ]


def test_generated_certificate_payloads_recompute_exactly() -> None:
    payloads = certificate_payloads(5)
    assert set(payloads) == {
        "parameter_and_theorem_v0.3.1.json",
        "exact_finite_audit_v0.3.1.json",
        "physical_interference_witness_v0.3.1.json",
    }
    for payload in payloads.values():
        verification = verify_commutative_csg_certificate(payload)
        assert verification["passed"]
        assert all(verification["checks"].values())


def test_checked_in_certificates_and_result_verify() -> None:
    certificate_dir = ROOT / "certificates" / "commutative_csg_reference"
    expected_payloads = certificate_payloads(5)
    for filename, expected in expected_payloads.items():
        path = certificate_dir / filename
        actual = json.loads(path.read_text(encoding="utf-8"))
        assert {
            key: actual[key] for key in expected
        } == expected
        verification = verify_commutative_csg_certificate(actual)
        assert verification["passed"]

    result_path = ROOT / "results" / "v0.3.1_commutative_csg_reference.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["verdict"] == "COMMUTATIVE_CSG_REFERENCE_PASS"
    assert result["benchmark"]["passed"]
    assert result["benchmark"]["decoherence_functional"][
        "physical_witness_pass"
    ]
    assert len(result["certificate_hashes"]) == 3


@pytest.mark.parametrize("max_n", [0, 6, -1])
def test_finite_exact_domain_is_enforced(max_n: int) -> None:
    with pytest.raises(ValueError, match="1 <= max_n <= 5"):
        commutative_csg_reference_benchmark(max_n)


def test_boolean_and_noninteger_cardinality_are_rejected() -> None:
    with pytest.raises(TypeError, match="integer"):
        commutative_csg_reference_benchmark(True)
    with pytest.raises(TypeError, match="integer"):
        commutative_csg_reference_benchmark(3.0)  # type: ignore[arg-type]
