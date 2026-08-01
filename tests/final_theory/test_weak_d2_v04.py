"""Exact regression and mutation tests for the v0.4 weak d=2 witness."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path

from universe_lab.final_theory import weak_d2_v04 as v04

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = REPOSITORY_ROOT / "results/v0.4_weak_d2_classification.json"


@cache
def _compiled() -> dict[str, object]:
    return v04.compile_v04(REPOSITORY_ROOT)


def test_frozen_artifact_regenerates_exactly() -> None:
    assert json.loads(RESULT_PATH.read_text(encoding="utf-8")) == _compiled()


def test_exact_witness_closes_every_required_direct_substitution_gate() -> None:
    result = _compiled()
    direct = result["direct_substitution"]
    assert direct["CPOBC"]["checked_equations"] == 783
    assert direct["CPOBC"]["all_zero"] is True
    assert direct["CPOBC_inverse_forms"]["checked_inverse_containing_equations"] == 712
    assert direct["CPOBC_inverse_forms"]["all_zero"] is True
    assert direct["GC"]["checked_same_endpoint_path_pairs"] == 1529
    assert direct["GC"]["all_fixed_vector_equalities_hold"] is True
    assert direct["MSR"]["checked_constraints"] == 24
    assert direct["MSR"]["all_reachable_state_equalities_hold"] is True
    assert result["passed"] is True
    assert result["verdict"] == v04.VERDICT


def test_witness_is_genuinely_weak_and_not_an_accidental_strong_solution() -> None:
    result = _compiled()
    direct = result["direct_substitution"]
    assert direct["GC"]["strong_operator_failure_count"] == 986
    assert direct["MSR"]["strong_operator_failure_count"] == 24
    assert direct["GC"]["all_strong_operator_equalities_hold"] is False
    assert direct["MSR"]["all_strong_operator_equalities_hold"] is False


def test_both_eq113_branches_remain_separate_and_hold_operator_wise() -> None:
    eq113 = _compiled()["direct_substitution"]["Eq113"]
    assert eq113["branches_kept_separate"] is True
    assert set(eq113["branches"]) == {v04.EQ113_DERIVED, v04.EQ113_LITERAL}
    assert eq113["branches"][v04.EQ113_DERIVED]["checked_relations"] == 25
    assert eq113["branches"][v04.EQ113_LITERAL]["checked_relations"] == 25
    assert eq113["both_branches_hold_as_operator_equalities"] is True


def test_eq139_source_domain_discrepancy_is_not_silently_merged() -> None:
    assert _compiled()["Eq139_coverage"]["coverage_verdict"] == (
        "EQ139_TWO_SOURCE_DOMAINS_COMPLETE_N4"
    )
    assert v04.eq139_instances(v04.EQ139_PRINTED_STRICT) == (
        (3, 1, 2),
        (4, 1, 2),
        (4, 1, 3),
        (4, 2, 3),
    )
    assert v04.eq139_instances(v04.EQ139_EQ145_COMPLETED) == (
        (2, 1, 2),
        (3, 1, 2),
        (3, 1, 3),
        (3, 2, 3),
        (4, 1, 2),
        (4, 1, 3),
        (4, 1, 4),
        (4, 2, 3),
        (4, 2, 4),
        (4, 3, 4),
    )
    eq139 = _compiled()["direct_substitution"]["Eq139"]
    assert eq139["branches"][v04.EQ139_PRINTED_STRICT]["counts_by_stage"] == {
        "2": 0,
        "3": 1,
        "4": 3,
    }
    assert eq139["branches"][v04.EQ139_EQ145_COMPLETED]["counts_by_stage"] == {
        "2": 1,
        "3": 3,
        "4": 6,
    }
    assert eq139["both_domains_hold_as_operator_equalities"] is True

    additionality = _compiled()["Eq139_coverage"]["weak_semantics_operator_additionality_scout"][
        "individual_instances"
    ]
    assert len(additionality) == 10
    assert all(record["rank_increment_over_CPOBC"] == 1 for record in additionality)
    assert all(
        record["nonimplication_witness"]["all_783_CPOBC_upper_right_residuals"] == "0"
        and record["nonimplication_witness"]["target_Eq139_upper_right_residual"] == "1"
        for record in additionality
    )


def test_every_transition_is_nonsingular_and_orbit_identification_is_on() -> None:
    assignment = _compiled()["transition_assignment"]
    assert assignment["occurrence_count"] == 165
    assert assignment["orbit_count"] == 131
    assert assignment["all_occurrences_nonsingular"] is True
    assert assignment["occurrence_identification_ON"] is True
    assert assignment["two_sided_inverse_checks"]["matrix_equation_count"] == 330
    assert assignment["two_sided_inverse_checks"]["all_zero"] is True


def test_all_six_Q_commutators_have_the_claimed_nonzero_closed_form() -> None:
    records = _compiled()["noncommutativity"]["records"]
    assert len(records) == 6
    assert all(record["nonzero"] for record in records)
    assert records[0] == {
        "pair": [1, 2],
        "commutator": [["0", "1"], ["0", "0"]],
        "nonzero": True,
    }
    for record in records:
        left, right = record["pair"]
        expected = 4 * (Fraction(1, 2**left) - Fraction(1, 2**right))
        assert record["commutator"][0][1] == str(expected)


def test_exact_triangular_scout_does_not_get_promoted_to_general_profiles() -> None:
    result = _compiled()
    profiles = result["semantic_profiles"]
    assert profiles["fixed_vector_GC__strong_MSR"]["general_d2"] == "OPEN"
    assert profiles["strong_GC__reachable_state_MSR"]["general_d2"] == "OPEN"
    scout = result["triangular_profile_scout"]
    assert scout["classification"] == "EXACT_QQ_LINEAR_SCOUT_NOT_GENERAL_D2_PROOF"
    assert scout["profiles"]["fixed_vector_GC__reachable_state_MSR"]["rank"] == 108
    assert scout["profiles"]["fixed_vector_GC__strong_MSR"]["rank"] == 130
    assert scout["profiles"]["strong_GC__reachable_state_MSR"]["rank"] == 114
    assert scout["profiles"]["strong_GC__strong_MSR"]["rank"] == 130
    local_minimality = scout["ansatz_local_minimal_relation_groups"]
    assert local_minimality["CPOBC_commutator_quotient_dimension"] == 1
    assert local_minimality["single_strong_MSR_relations_that_suffice"] == [
        "msr:p1-0",
        "msr:p2-0",
        "msr:p2-2",
    ]
    assert len(local_minimality["single_strong_GC_relations_that_suffice"]) == 168
    assert local_minimality["minimal_cardinality_if_either_list_is_nonempty"] == 1


def test_mutating_Q1_is_detected_by_the_frozen_cpobc_inventory() -> None:
    cpobc = v04._load_json(REPOSITORY_ROOT / "results/v0.3.1_cpobc_relations_n4.json")
    reduction = v04._load_json(REPOSITORY_ROOT / "results/v0.3.2_cpobc_generator_reduction.json")
    assignments = v04._transition_assignments(reduction)
    q1_occurrence = next(
        record["occurrence_id"]
        for record in reduction["reduction_map"]
        if record["stage"] == 1 and record["precursor_code"] == 0
    )
    original = assignments[q1_occurrence]
    assignments[q1_occurrence] = (
        (original[0][0], original[0][1] + 1),
        original[1],
    )
    assert v04._evaluate_cpobc(cpobc, assignments)["all_zero"] is False
