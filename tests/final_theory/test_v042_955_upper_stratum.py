"""Regression checks for the exact v0.4.2 955 upper-stratum decomposition."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_upper_stratum_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_reachable_state_msr_is_identically_satisfied_on_the_chart() -> None:
    record = _compiled()["reachable_state_MSR_is_built_in"]

    assert record["source_constraints"] == 24
    assert record["vector_entry_constraints_before_substitution"] == 48
    assert record["constraints_after_substitution"] == 0
    assert "v_c" in record["identity_reason"]


def test_grading_is_derived_consistently_and_not_assumed() -> None:
    grading = _compiled()["derived_grading"]

    assert grading["distinct_monomial_constraints"] == 47298
    assert grading["rank"] == 460
    assert grading["solution_space_dimension"] == 16
    assert grading["inconsistent_rows"] == 0
    assert grading["grading_exists"] is True
    assert grading["homogeneity_violations"] == 0
    assert grading["family_weights"] == {
        "A:00": ["0"],
        "A:01": ["1"],
        "A:10": ["-1"],
        "A:11": ["0"],
        "u:0": ["1"],
        "u:1": ["0"],
    }


def test_unconstrained_coordinates_are_exactly_the_frozen_blind_directions() -> None:
    absent = _compiled()["derived_grading"]["coordinates_absent_from_the_core"]
    frozen = json.loads((ROOT / gate.TANGENT_PATH).read_text(encoding="utf-8"))

    assert absent["total"] == 16
    assert absent["per_family"] == {
        "A:00": 0,
        "A:01": 0,
        "A:10": 0,
        "A:11": 0,
        "u:0": 8,
        "u:1": 8,
    }
    assert absent["equals_the_frozen_terminal_slack_blind_directions"] is True
    flattened = sorted(name for values in absent["names"].values() for name in values)
    assert flattened == sorted(frozen["terminal_slack_blind_directions"]["coordinates"])


def test_upper_stratum_decomposition_has_no_counterexample() -> None:
    stratum = _compiled()["upper_stratum"]

    assert stratum["streamed_nonzero_core_entries"] == 4152
    assert stratum["lower_left_entries_nonzero_on_stratum"] == 0
    assert stratum["upper_right_entries_nonlinear_in_the_positive_family"] == 0
    assert stratum["diagonal_entries_containing_a_weighted_coordinate"] == 0


def test_scalar_variety_and_linear_fibre_census() -> None:
    stratum = _compiled()["upper_stratum"]

    assert stratum["scalar_system"]["entries"] == 1814
    assert stratum["scalar_system"]["terms"] == 9673
    assert stratum["scalar_system"]["coordinates"] == "A:*:00, A:*:11, u:*:1"
    assert max(int(key) for key in stratum["scalar_system"]["degree_histogram"]) == 9

    positive = stratum["positive_weight_family"]
    assert positive["A:*:01"] == 107
    assert positive["u:*:0"] == 16
    assert positive["total"] == 123

    fibre = stratum["upper_right_linear_fibre"]
    assert fibre["entries"] == 1038
    assert fibre["terms"] == 16004
    assert fibre["exactly_linear_in_the_positive_weight_family"] is True


def test_six_commutators_collapse_to_four_term_linear_forms() -> None:
    collapse = _compiled()["Q_commutator_collapse"]

    assert collapse["pairs"] == 6
    assert collapse["diagonal_entries_nonzero_on_stratum"] == 0
    assert collapse["lower_left_entries_nonzero_on_stratum"] == 0
    assert collapse["upper_right_entries_nonlinear"] == 0
    assert collapse["surviving_entry"] == "01"
    assert [record["pair"] for record in collapse["records"]] == [
        [1, 2],
        [1, 3],
        [1, 4],
        [2, 3],
        [2, 4],
        [3, 4],
    ]
    for record in collapse["records"]:
        assert record["entries"]["01"]["term_count"] == 4
        assert record["entries"]["01"]["upper_right_degree"] == 1


def test_q_generators_match_the_frozen_tangent_mapping() -> None:
    slack = gate._load(ROOT / gate.SLACK_INVENTORY_PATH)
    mixed = gate._load(ROOT / gate.MIXED_MANIFEST_PATH)
    representatives, _records = tangent._q_mapping(slack, mixed)

    assert sorted(representatives) == [1, 2, 3, 4]


def test_fifth_order_preflight_is_recorded_as_superseded() -> None:
    superseded = _compiled()["supersedes"]

    assert superseded["gate"] == "DESIGN_THE_FIFTH_ORDER_FULL_FOURTH_JET_FIBER_PREFLIGHT"
    assert "stop rule" in superseded["reason"]
    assert "rank 107" in superseded["jet_ladder_explanation"]
    assert "formal-local" in superseded["jet_ladder_explanation"]


def test_gate_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()

    assert payload["verdict"] == gate.VERDICT
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
    assert payload["solver_status"]["Groebner_or_saturation_runs"] == 0
    assert payload["solver_status"]["solver_run"] is False
    assert any("not the unrestricted 955 profile" in claim for claim in payload["claim_boundary"])
    assert any("reachable visibility" in claim for claim in payload["claim_boundary"])
