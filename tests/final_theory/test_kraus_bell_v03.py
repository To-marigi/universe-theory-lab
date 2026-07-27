from __future__ import annotations

import json
from fractions import Fraction
from typing import Any

import pytest

from universe_lab.final_theory.kraus_bell_v03 import (
    KRAUS_BELL_CAUSALITY_UNDEFINED,
    kraus_bell_benchmark,
)


def _fraction(record: dict[str, int]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


@pytest.fixture(scope="module")
def benchmark() -> dict[str, Any]:
    return kraus_bell_benchmark()


def test_result_is_json_ready_and_keeps_missing_definition_explicit(
    benchmark: dict[str, Any],
) -> None:
    encoded = json.dumps(benchmark, sort_keys=True)
    definition = benchmark["definition_audit"]
    assert benchmark["kraus_bell_status"] == KRAUS_BELL_CAUSALITY_UNDEFINED
    assert benchmark["kraus_bell_causality_status"] == (
        KRAUS_BELL_CAUSALITY_UNDEFINED
    )
    assert definition["status"] == KRAUS_BELL_CAUSALITY_UNDEFINED
    assert not definition["canonical_spectator_tensor_factor_present"]
    assert not definition["canonical_partial_trace_present"]
    assert not definition["canonical_full_to_reduced_channel_present"]
    assert not definition["inverse_based_cpobc_applied"]
    assert not definition["rank_one_global_matrix_units_treated_as_invertible"]
    assert "DEFINITION_FIXED" not in encoded


def test_all_source_channels_are_exact_cp_tp_and_outcomes_are_tni(
    benchmark: dict[str, Any],
) -> None:
    audit = benchmark["channel_instrument_audit"]
    assert audit["source_count"] == 88
    assert audit["instrument_outcome_count"] == 708
    assert audit["complete_positivity"]
    assert audit["instrument_trace_preservation"]
    assert audit["outcome_trace_nonincrease"]
    assert audit["history_channel_trace_preservation"]
    assert audit["choi_positive_semidefinite"]

    for source in audit["source_certificates"]:
        instrument = source["instrument_map"]
        history_channel = source["history_channel"]
        assert sum(
            (_fraction(value) for value in instrument["probability_vector"]),
            start=Fraction(0),
        ) == 1
        assert instrument["choi"]["diagonal"] == instrument[
            "probability_vector"
        ]
        assert sum(
            (
                _fraction(value)
                for value in history_channel["probability_vector"]
            ),
            start=Fraction(0),
        ) == 1
        assert history_channel["choi"]["diagonal"] == history_channel[
            "probability_vector"
        ]


def test_exhaustive_bell_family_counts_and_ordering_cases(
    benchmark: dict[str, Any],
) -> None:
    audit = benchmark["bell_family_audit"]
    by_n = audit["by_full_source_size"]
    assert [
        by_n[str(n)]["distinct_branch_pair_configuration_count"]
        for n in range(6)
    ] == [0, 1, 6, 40, 298, 2659]
    assert [
        by_n[str(n)]["nontrivial_spectator_configuration_count"]
        for n in range(6)
    ] == [0, 0, 2, 20, 189, 1940]
    assert audit["unique_family_count"] == 865
    assert audit["nontrivial_spectator_configuration_count"] == 2151
    assert audit["strict_precursor_size_order_count"] == 1944
    assert audit["equal_precursor_size_count"] == 207
    assert audit["all_configuration_strict_precursor_size_count"] == 2734
    assert audit["all_configuration_equal_precursor_size_count"] == 270
    assert not audit["equal_size_cpobc_order_available"]
    assert audit["local_weight_spectator_dependence_violations"] == 0
    assert audit["per_labeled_precursor_product_violations"] == 0
    assert audit["orbit_aggregate_product_violation_count"] == 798
    assert audit["relative_alignment_ambiguities"]["count"] == 88


def test_automorphism_factor_omission_is_killed_by_map_data(
    benchmark: dict[str, Any],
) -> None:
    automorphism = benchmark["automorphism_audit"]
    mutation = automorphism["omission_mutation"]
    witness = mutation["first_exact_witness"]
    assert automorphism["branch_orbit_stabilizer_and_factor_pass"]
    assert automorphism["pair_orbit_stabilizer_pass"]
    assert mutation["detected"]
    assert mutation[
        "correct_orbit_size_and_automorphism_factor_normalizations_agree"
    ]
    assert witness["source_history"] == "p2-0"
    assert witness["correct_orbit_probability_vector"] != witness[
        "omitted_factor_probability_vector"
    ]
    assert not witness["choi_matrices_equal"]
    assert not witness["superoperators_equal"]
    assert sum(
        (
            _fraction(value)
            for value in witness["correct_orbit_probability_vector"]
        ),
        start=Fraction(0),
    ) == 1
    assert sum(
        (
            _fraction(value)
            for value in witness["omitted_factor_probability_vector"]
        ),
        start=Fraction(0),
    ) == 1


def test_kraus_list_equality_false_test_is_rejected(
    benchmark: dict[str, Any],
) -> None:
    audit = benchmark["kraus_basis_invariance_audit"]
    assert not audit["kraus_lists_equal"]
    assert audit["choi"]["exactly_equal"]
    assert audit["superoperator"]["exactly_equal"]
    assert audit["trace_preservation_effect"]["both_identity"]
    assert audit["false_kraus_string_test_detected"]
    assert not benchmark["comparison_protocol"][
        "kraus_list_or_string_equality_used"
    ]


def test_probability_counterexample_has_exact_map_boundary(
    benchmark: dict[str, Any],
) -> None:
    witness = benchmark["bell_family_audit"][
        "first_probability_dependence_counterexample"
    ]
    labeled = witness["per_labeled_precursor_product_map"]
    aggregate = witness["orbit_aggregate_product_map"]
    assert witness["absolute_probabilities_change"]
    assert labeled["probability_equal"]
    assert labeled["superoperators"]["exactly_equal"]
    assert labeled["choi_matrices"]["exactly_equal"]
    assert not aggregate["probability_equal"]
    assert not aggregate["superoperators"]["exactly_equal"]
    assert not aggregate["choi_matrices"]["exactly_equal"]
    assert "not a QBC failure certificate" in witness["claim_boundary"]


def test_relabel_covariance_is_checked_on_every_source(
    benchmark: dict[str, Any],
) -> None:
    audit = benchmark["relabel_covariance_audit"]
    assert audit["history_count"] == 88
    assert audit["adjacent_transposition_checks"] == 312
    assert audit["precursor_checks"] == 3532
    assert audit["transition_law_covariant"]
    assert audit["family_signatures_relabel_covariant_by_construction"]
    assert audit["failures"] == []


@pytest.mark.parametrize("max_n", [-1, 6])
def test_declared_exact_domain_is_enforced(max_n: int) -> None:
    with pytest.raises(ValueError, match="between 0 and 5"):
        kraus_bell_benchmark(max_n)
