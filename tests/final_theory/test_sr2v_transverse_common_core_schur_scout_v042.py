"""Exact guards for the finite five-Q common-core Schur scout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_common_core_schur_scout_v042 as result

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "b977d2a21444beae5d853680c0945dd74fef1504f4b3045f587c509936b4a35a"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return result.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(result.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == result.SCHEMA
    assert frozen["verdict"] == result.VERDICT
    assert frozen["search_terminal"] == result.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert result.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert frozen["witness"] is None
    assert all(frozen["gates"].values())
    for relative, binding in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == binding["raw_sha256"]


def test_second_fixed_four_passes_81_then_is_rejected(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["scout_certificate"]
    candidate = certificate["second_fixed_four_candidate"]
    assert candidate["joint_sources"] == [23, 147, 154, 688]
    assert candidate["passes_all_81_exact_points"] is True
    assert candidate["global_candidate_status"] == "REJECTED_BY_EXACT_ADVERSARIAL_POINT"
    assert candidate["rank_census_candidate_star_augmented"] == {
        "0/0/0": 37,
        "1/0/1": 3,
        "2/1/2": 5,
        "3/1/3": 3,
        "3/3/3": 2,
        "4/1/4": 2,
        "4/3/4": 29,
    }
    assert candidate["each_single_row_removal_failure_counts"] == {
        "23": 35,
        "147": 31,
        "154": 31,
        "688": 31,
    }


def test_third_fixed_four_passes_82_then_is_rejected(
    rebuilt: dict[str, Any],
) -> None:
    candidate = rebuilt["scout_certificate"]["third_fixed_four_candidate"]
    assert candidate["joint_sources"] == [23, 31, 147, 688]
    assert candidate["passes_original_81_exact_points"] is True
    assert candidate["passes_preceding_82_point_ledger"] is True
    assert (
        candidate["rank_at_second_candidate_adversarial_point"],
        candidate["augmented_rank_at_second_candidate_adversarial_point"],
    ) == (4, 4)
    assert candidate["global_candidate_status"] == (
        "REJECTED_BY_83RD_EXACT_ADVERSARIAL_POINT"
    )
    assert candidate["rank_census_over_original_81_candidate_star_augmented"] == {
        "0/0/0": 39,
        "1/0/1": 1,
        "2/1/2": 5,
        "3/1/3": 3,
        "3/3/3": 2,
        "4/1/4": 2,
        "4/3/4": 29,
    }


def test_sample_ledger_has_all_single_and_F7_supports(rebuilt: dict[str, Any]) -> None:
    ledger = rebuilt["scout_certificate"]["sample_ledger"]
    assert ledger["original_evaluation_count"] == 81
    assert ledger["total_evaluations_including_adversarial"] == 83
    assert ledger["distinct_point_count"] == 82
    assert ledger["families"] == {
        "reference_equal": 1,
        "all_49_single_directions": 49,
        "all_31_nonempty_F7_supports": 31,
        "direct_exact_adversarial_evaluations": 2,
    }
    assert ledger["adversarial_record_ids"] == [
        "ADV2_exact_rank_test_point",
        "ADV3_exact_rank_test_point",
    ]
    assert len(ledger["records"]) == 81
    assert all(record["candidate_spans_star"] for record in ledger["records"])
    assert all(
        record["candidate_rank_minor"]["nonzero_when_positive_rank"]
        for record in ledger["records"]
    )


def test_undercovered_predecessor_candidate_is_rejected(rebuilt: dict[str, Any]) -> None:
    rejected = rebuilt["scout_certificate"]["rejected_predecessor_candidate"]
    assert rejected["joint_sources"] == [83, 147, 154, 688]
    assert rejected["failure_count"] == 5
    assert rejected["must_not_be_reused"] is True


def test_fixed_four_is_rejected_but_full_M0_holds_at_adversarial_point(
    rebuilt: dict[str, Any],
) -> None:
    adversarial = rebuilt["scout_certificate"][
        "second_fixed_four_adversarial_rejection"
    ]
    assert "targeted_symbolic_hypersurface" not in adversarial
    assert adversarial["delta_Q"] == ["1/2", "1/6", "-1/112", "1/82"]
    assert (
        adversarial["candidate_rank"],
        adversarial["star_rank"],
        adversarial["candidate_plus_star_rank"],
    ) == (3, 3, 4)
    assert adversarial["candidate_fails_to_span_star"] is True
    assert (
        adversarial["full_M0_rank"],
        adversarial["full_M0_plus_star_rank"],
        adversarial["full_M0_plus_all_six_commutators_rank"],
    ) == (131, 131, 131)
    assert adversarial["full_M0_has_no_escape_at_this_point"] is True
    assert all(
        branch["rank"] == branch["rank_with_all_six_commutators"] == 131
        and branch["escape"] is False
        for branch in adversarial["four_semantic_branches"].values()
    )


def test_third_fixed_four_has_certified_positive_rational_escape(
    rebuilt: dict[str, Any],
) -> None:
    adversarial = rebuilt["scout_certificate"][
        "third_fixed_four_adversarial_rejection"
    ]
    assert adversarial["exact_slice_point"] == {
        "u12": "1/2",
        "u13": "1",
        "u15": "1",
        "u44": "1",
        "u45": "2",
    }
    assert adversarial["sample_id"] == "ADV3_exact_rank_test_point"
    assert adversarial["family"] == "direct_exact_adversarial_evaluation"
    assert adversarial["certification_scope"] == (
        "direct exact-rational Schur-row reconstruction and rank calculation at "
        "this stored slice point only"
    )
    assert "symbolic_determinant_numerator" not in adversarial
    assert {
        "total_degree",
        "term_count",
        "degree_in_u12",
        "factorization_over_Q",
    }.isdisjoint(adversarial)
    assert adversarial["delta_Q"] == ["-1/8", "0", "-1/64", "-1/164"]
    assert adversarial["candidate_schur_rows"] == [
        ["5/192", "0", "0", "0", "0"],
        ["1/32", "0", "-1/4", "0", "0"],
        ["1/82", "0", "0", "-1/4", "0"],
        ["0", "0", "0", "0", "0"],
    ]
    assert adversarial["star_schur_rows_c12_c13_c14"] == [
        ["0", "-1/8", "0", "0", "0"],
        ["1/64", "0", "-1/8", "0", "0"],
        ["1/164", "0", "0", "-1/8", "0"],
    ]
    assert (
        adversarial["candidate_rank"],
        adversarial["star_rank"],
        adversarial["candidate_plus_star_rank"],
    ) == (3, 3, 4)
    assert adversarial["escaping_Q_vector"] == ["0", "1", "0", "0", "0"]
    assert adversarial["candidate_evaluations_on_escape"] == ["0", "0", "0", "0"]
    assert adversarial["star_evaluations_on_escape"] == ["-1/8", "0", "0"]
    assert adversarial["fixed5_patch"] == {
        "joint_sources": [23, 31, 147, 154, 688],
        "rank": 4,
        "row154_schur_residual": ["19/1640", "153/3280", "-32/205", "-1/4", "0"],
        "status": "POINTWISE_PATCH_ONLY_NOT_A_GLOBAL_CANDIDATE",
    }
    assert adversarial["full_common_core_check"] == {
        "rank": 131,
        "rank_with_star": 131,
        "rank_with_all_six_commutators": 131,
        "escape": False,
    }
    assert all(
        branch["rank"] == branch["rank_with_all_six_commutators"] == 131
        and branch["escape"] is False
        for branch in adversarial["four_branch_checks"].values()
    )


def test_four_is_minimal_only_on_the_frozen_sample_ledger(
    rebuilt: dict[str, Any],
) -> None:
    minimality = rebuilt["scout_certificate"]["fixed_three_row_sample_minimality"]
    assert minimality["star_rank_three_sample_count"] == 31
    assert minimality["all_1127_common_core_sources_filtered"] is True
    assert minimality[
        "eligible_sources_nonzero_and_inside_star_at_all_rank_three_points"
    ] == [29, 147, 548]
    assert minimality["unique_eligible_triple_failure_count_over_81"] == 41
    assert minimality["no_fixed_three_or_smaller_set_can_pass_this_ledger"] is True
    assert minimality["claim_scope"] == "finite 81-point ledger only"


def test_scout_remains_nonterminal(rebuilt: dict[str, Any]) -> None:
    assert rebuilt["search_terminal"] == "NOT_A_SEARCH_TERMINAL_83_EXACT_EVALUATIONS_ONLY"
    assert "rejected" in rebuilt["claim_boundary"]
    assert rebuilt["scout_certificate"]["full_common_core_witnesses_found"] == 0
