"""Exact guards for the transverse commutator kernel and nested loci."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "da062443965d679dc936dd4263f150c6d413deea7f5425790d039e099c89ac30"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return locus.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(locus.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == locus.SCHEMA
    assert frozen["verdict"] == locus.VERDICT
    assert frozen["search_terminal"] == locus.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert locus.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert frozen["witness"] is None
    assert all(frozen["gates"].values())
    for relative, binding in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == binding["raw_sha256"]


def test_it_answers_the_gate_the_transverse_certificate_declared(
    rebuilt: dict[str, Any],
) -> None:
    bound = rebuilt["bound_transverse_conclusion"]
    assert bound["verdict"] == transverse.VERDICT
    assert "determinant-zero loci" in bound["next_exact_gate_it_declared"]


def test_universal_commutator_template_is_exact(rebuilt: dict[str, Any]) -> None:
    identity = rebuilt["universal_commutator_identity"]
    assert identity["chart"] == "Q_i=[[a_i,x_i],[0,b_i]]"
    assert identity["template"] == "x_j*(a_i - b_i) - x_i*(a_j - b_j)"
    assert identity["difference"] == "0"
    assert identity["other_commutator_entries_are_zero"] is True
    assert identity["equal_eigenvalue_specialisation_is_identically_zero"] is True
    assert identity["coboundary_specialisation_is_identically_zero"] is True
    assert identity["commuting_subspace"] == "K_delta=ker C(delta) in QQ^4"
    assert identity["nonzero_delta_commuting_subspace"] == "K_delta=span(delta)"
    assert identity["zero_delta_commuting_subspace"] == "K_0=QQ^4"
    assert "rank[M;C]>rank M" in identity["witness_criterion"]


def test_coboundary_is_a_conjugation_and_survives_every_operator_row(
    rebuilt: dict[str, Any],
) -> None:
    coboundary = rebuilt["universal_coboundary_identity"]
    assert coboundary["substitution"] == "x_e = beta_e = a_e - b_e"
    assert coboundary["conjugator"] == "C=[[1,-1],[0,1]]"
    assert coboundary["generator_failures"] == []
    assert coboundary["inverted_word_residual"] == "0"
    assert len(coboundary["checked_words"]) == 6
    for word in coboundary["checked_words"]:
        assert word["upper_right_minus_A_minus_B"] == "0"
    assert "bottom scalar locus" in coboundary["membership_criterion"]


def test_general_bottom_character_is_pinned_to_the_shipped_normalized_one(
    rebuilt: dict[str, Any],
) -> None:
    general = rebuilt["general_bottom_character"]
    assert general["normalized_specialisation"] == "t1=t2=t3=t4=1, q5=1/32"
    assert general["occurrence_signature_failures"] == []
    assert general["Q_stage_failures"] == []
    assert general["agrees_with_the_shipped_csg_at_the_normalized_point"] is True
    assert general["shipped_eq139_row_hardcodes_the_normalized_bottom"] is True
    assert general["eq139_row_mismatches_at_the_normalized_point"] == []
    assert general["general_bottom_eq139_builder_reproduces_the_shipped_rows"] is True
    assert general["eq139_instances_compared"] == [
        list(instance) for instance in torus._eq139_instances(torus.EQ139_STRICT)
    ]


def test_equal_eigenvalue_stratum_has_rank_127_and_the_bottom_tangent_kernel(
    rebuilt: dict[str, Any],
) -> None:
    stratum = rebuilt["full_diagonal_locus"]
    assert stratum["name"] == "full-diagonal locus"
    assert stratum["definition"] == "E={a_e=b_e for all 132 coordinates}"
    assert stratum["dimension"] == 5
    assert stratum["codimension_in_the_transverse_scalar_base"] == 49
    assert stratum["contained_in_every_branch_determinant_zero_locus"] is True
    assert stratum["exact_rank_at_every_certified_sample"] == 127
    assert stratum["exact_nullity_at_every_certified_sample"] == 5
    assert stratum["rank_drop_from_the_generic_derived_rank"] == 4
    assert stratum["stratum_wide_rank_constancy_proved"] is False
    assert stratum["witness_conclusion_is_stratum_wide"] is True
    assert "delta_Q=0 on all of E" in stratum["witness_conclusion_argument"]
    assert "Z_Q={delta_Q=0}" in stratum["relation_to_equal_Q_spectrum_locus"]
    assert len(stratum["samples"]) == 3
    for sample in stratum["samples"]:
        assert sample["all_843_operator_monomial_rows_hold"] is True
        assert sample["delta_Q"] == {"1": "0", "2": "0", "3": "0", "4": "0"}
        assert sample["delta_Q_is_zero"] is True
        assert sample["all_six_commutator_rows_vanish_identically"] is True
        assert sample["bottom_tangent_rank"] == 5
        assert set(sample["branches"]) == set(locus.BRANCH_SPECS)
        for branch in sample["branches"].values():
            assert branch["rank"] == 127
            assert branch["nullity"] == 5
            assert branch["rank_with_commutator_rows"] == 127
            assert branch["commutator_rows_leave_the_row_space"] is False
        for report in sample["bottom_tangent_row_violations"].values():
            assert set(report) == set(locus.BOTTOM_PARAMETERS)
            assert all(count == 0 for count in report.values())


def test_two_scalar_nonzero_delta_samples_have_rank_130_and_the_coboundary_kernel(
    rebuilt: dict[str, Any],
) -> None:
    stratum = rebuilt["two_scalar_locus"]
    assert stratum["dimension"] == 10
    assert stratum["codimension_in_the_transverse_scalar_base"] == 44
    assert stratum["meets_delta_nonzero"] is True
    assert stratum["name"] == "two-scalar locus"
    assert stratum["exact_rank_at_every_certified_nonzero_delta_sample"] == 130
    assert stratum["exact_nullity_at_every_certified_nonzero_delta_sample"] == 2
    assert stratum["stratum_wide_rank_constancy_proved"] is False
    assert stratum["universal_nullity_lower_bound_on_S_minus_E"] == 1
    assert stratum["witness_conclusion_is_stratum_wide"] is False
    assert stratum["kernel_identification_at_every_certified_nonzero_delta_sample"] == (
        "ker M = span(beta, e_Q5)"
    )
    assert len(stratum["samples"]) == 4
    for sample in stratum["samples"]:
        assert sample["all_843_operator_monomial_rows_hold"] is True
        assert sample["all_320_fixed_vector_GC_monomial_rows_hold"] is True
        assert sample["delta_Q_is_zero"] is False
        assert set(sample["six_commutator_forms_on_beta"]) == {
            "Q1_Q2",
            "Q1_Q3",
            "Q1_Q4",
            "Q2_Q3",
            "Q2_Q4",
            "Q3_Q4",
        }
        assert all(value == "0" for value in sample["six_commutator_forms_on_beta"].values())
        for name, _start, _stop in locus.ROW_BLOCKS:
            assert sample["beta_violations_per_row_block"][name]["violations"] == 0
        for branch in sample["branches"].values():
            assert branch["rank"] == 130
            assert branch["nullity"] == 2
            assert branch["rank_with_commutator_rows"] == 130
            assert branch["commutator_rows_leave_the_row_space"] is False
        for report in sample["kernel_reports"].values():
            assert report["beta_row_violations"] == 0
            assert report["rows_with_a_nonzero_Q5_column"] == 0
            assert report["dimension_of_span_beta_e_Q5"] == 2
            assert report["rank_after_appending_both_directions"] == 132


def test_two_scalar_locus_contains_a_distinct_q5_only_delta_zero_subfamily(
    rebuilt: dict[str, Any],
) -> None:
    stratum = rebuilt["two_scalar_locus"]
    assert stratum["also_contains_delta_zero_points_outside_E"] is True
    subfamily = stratum["same_couplings_independent_Q5_subfamily"]
    assert subfamily["symbol"] == "T"
    assert subfamily["dimension"] == 6
    assert subfamily["witness_conclusion_is_subfamily_wide"] is True
    assert "exactly T" in subfamily["delta_Q_zero_part_of_S"]
    sample = subfamily["sample"]
    assert sample["lower_cutoff_external_q5"] != sample["upper_cutoff_external_q5"]
    assert sample["differing_coordinates"] == [torus.Q5]
    assert sample["delta_Q"] == {"1": "0", "2": "0", "3": "0", "4": "0"}
    assert sample["delta_Q_is_zero"] is True
    assert sample["all_six_commutator_rows_vanish_identically"] is True
    assert sample["upper_bottom_tangent_rank"] == 5
    for branch in sample["branches"].values():
        assert branch["rank"] == 127
        assert branch["nullity"] == 5
        assert branch["rank_with_commutator_rows"] == 127
        assert branch["commutator_rows_leave_the_row_space"] is False
    for report in sample["upper_bottom_tangent_row_violations"].values():
        assert set(report) == set(locus.BOTTOM_PARAMETERS)
        assert all(count == 0 for count in report.values())


def test_full_rank_opens_now_exist_over_non_normalized_bottom_characters(
    rebuilt: dict[str, Any],
) -> None:
    records = rebuilt["off_normalized_principal_opens"]
    assert len(records) == 2
    assert {record["label"] for record in records} == {"generic-upper-A", "generic-upper-B"}
    for record in records:
        assert record["couplings"] != ["1", "1", "1", "1"]
        assert record["all_843_operator_monomial_rows_hold"] is True
        assert record["delta_Q_is_zero"] is False
        assert len(record["upper_torus_coordinates"]) == 49
        for branch_id, branch in record["branches"].items():
            assert branch["rank"] == locus.EXPECTED_GENERIC_RANKS[branch_id]
            assert branch["commutator_rows_leave_the_row_space"] is False
        dichotomy = record["coboundary_dichotomy"]
        assert dichotomy["conjugation_invariant_blocks_are_satisfied"] is True
        assert dichotomy["omega_dependent_blocks_are_violated"] is True
        blocks = record["beta_violations_per_row_block"]
        for name in locus.CONJUGATION_INVARIANT_BLOCKS:
            assert blocks[name]["violations"] == 0
        assert blocks["fixed_vector_GC_basis"]["violations"] > 0
        assert blocks["reachable_state_MSR"]["violations"] == 24


def test_deterministic_scan_is_bounded_and_witness_free(rebuilt: dict[str, Any]) -> None:
    scan = rebuilt["deterministic_degeneracy_scan"]
    assert scan["point_count"] == len(locus.SCAN_DIRECTIONS) * len(locus.SCAN_SCALARS)
    assert scan["directions"] == list(locus.SCAN_DIRECTIONS)
    assert scan["witnesses"] == []
    assert scan["rank_profile_agrees_at_all_four_recorded_scalars_for_each_direction"] is True
    assert scan["commutator_rows_stay_inside_the_row_space_at_every_scanned_point"] is True
    assert scan["scan_status"] == "BOUNDED_DETERMINISTIC_SCAN_NOT_A_GLOBAL_OBSTRUCTION"
    assert sum(scan["rank_profile_census"].values()) == scan["point_count"]
    for record in scan["records"]:
        assert record["rank_profile"] == record["augmented_rank_profile"]
        assert record["any_branch_admits_a_visible_witness"] is False


def test_span_beta_q5_is_recorded_as_the_wrong_invariant(
    rebuilt: dict[str, Any],
) -> None:
    note = rebuilt["span_beta_e_Q5_is_not_the_right_invariant"]
    assert note["direction"] == locus.COUNTEREXAMPLE_DIRECTION
    assert note["scalar"] == str(locus.COUNTEREXAMPLE_SCALAR)
    assert note["upper_is_a_bottom_character"] is False
    assert note["beta_row_violations"] > 0
    assert note["kernel_indices_outside_span_beta_e_Q5"] != []
    assert note["nullity"] == 132 - note["rank"]
    assert len(note["six_commutator_forms_on_each_kernel_vector"]) == note["nullity"]
    for record in note["six_commutator_forms_on_each_kernel_vector"]:
        assert set(record) == {"Q1_Q2", "Q1_Q3", "Q1_Q4", "Q2_Q3", "Q2_Q4", "Q3_Q4"}
        assert all(value == "0" for value in record.values())
    assert note["all_commutator_forms_vanish_on_the_whole_kernel"] is True
    assert "Q-projection of ker M" in note["lesson"]


def test_claim_is_scoped_away_from_the_unsolved_loci(rebuilt: dict[str, Any]) -> None:
    boundary = rebuilt["resource_and_claim_boundaries"]
    assert boundary["solver_status"] == "NOT_RUN"
    assert boundary["groebner_status"] == "NOT_RUN"
    assert boundary["determinants_expanded_over_54_base_parameters"] is False
    assert boundary["four_determinant_zero_loci_solved"] is False
    assert boundary["degeneracy_locus_fully_stratified"] is False
    assert boundary["transverse_chart_globally_obstructed"] is False
    assert boundary["pair_or_triple_irreducible_branch_touched"] is False
    assert boundary["aligned_branch_or_Delta_align_touched"] is False
    assert boundary["state_native_D12_manifest_touched"] is False
    assert boundary["global_weak_weak_obstruction_claimed"] is False
    assert "K_delta=ker C(delta_Q)" in boundary["next_exact_gate"]
    assert "delta_Q!=0" in boundary["next_exact_gate"]
    assert "K_0=QQ^4" in boundary["next_exact_gate"]
    assert "do not defend span(beta,e_q5)" in boundary["next_exact_gate"].lower()
    assert "issues no SR2-V terminal" in rebuilt["claim_boundary"]
    assert "bounded deterministic search" in rebuilt["claim_boundary"]


def test_semantic_digest_rejects_a_stratum_rank_mutation(rebuilt: dict[str, Any]) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["full_diagonal_locus"]["exact_rank_at_every_certified_sample"] = 128
    assert locus.semantic_digest(mutated) != EXPECTED_SEMANTIC_DIGEST
