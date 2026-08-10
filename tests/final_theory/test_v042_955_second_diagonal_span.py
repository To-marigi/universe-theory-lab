"""Regression checks for the v0.4.2 955 span decision with a varied second diagonal."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_second_diagonal_span_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_second_diagonal_span_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_every_declared_point_verifies_as_an_exact_core_point() -> None:
    payload = _compiled()

    assert payload["aggregate"]["points"] == 10
    assert payload["aggregate"]["verified_as_core_points"] == 10
    for record in payload["evaluated_points"]:
        assert record["verified_as_core_point"] is True
        assert record["nonzero_core_entries"] == 0
        assert record["streamed_core_entries"] == 4152
        assert record["singular_transitions"] == 0


def test_the_second_diagonal_is_genuinely_moved() -> None:
    payload = _compiled()
    points = {record["label"]: record for record in payload["evaluated_points"]}

    assert points["constant_1_control"]["second_diagonal"]["identically_one"] is True
    for label in ("constant_2", "constant_3", "constant_1_over_2", "constant_minus_1"):
        assert points[label]["second_diagonal"]["identically_one"] is False
        assert points[label]["second_diagonal"]["distinct_values"] == 1

    assert payload["aggregate"]["points_with_a_non_constant_second_diagonal"] == 4
    assert payload["aggregate"]["maximum_distinct_second_diagonal_values"] == 13
    assert points["two_character_1_2_3_5_7"]["second_diagonal"]["distinct_values"] == 13


def test_no_escape_at_any_verified_point() -> None:
    payload = _compiled()

    assert payload["aggregate"]["total_escapes"] == 0
    assert payload["aggregate"]["points_with_an_escape"] == 0
    for record in payload["evaluated_points"]:
        assert record["escapes"] == 0
        assert record["verdict"] == gate.IN_SPAN_VERDICT
        assert [entry["pair"] for entry in record["pairs"]] == [
            [1, 2],
            [1, 3],
            [1, 4],
            [2, 3],
            [2, 4],
            [3, 4],
        ]
        for entry in record["pairs"]:
            assert entry["rank_increment"] == 0
            assert entry["status"] == "IN_SPAN"


def test_scalar_degeneration_behaves_differently_and_is_kept_as_a_control() -> None:
    points = {record["label"]: record for record in _compiled()["evaluated_points"]}
    degenerate = points["two_character_equal_scalar_degeneration"]

    assert degenerate["L_rank"] == 103
    assert degenerate["fibre_dimension"] == 20
    assert all(entry["nonzero_columns_after_evaluation"] == 0 for entry in degenerate["pairs"])
    assert _compiled()["aggregate"]["L_rank_values"] == [103, 114]


def test_non_degenerate_points_all_share_the_same_rank_and_fibre() -> None:
    points = [
        record
        for record in _compiled()["evaluated_points"]
        if record["label"] != "two_character_equal_scalar_degeneration"
    ]

    assert len(points) == 9
    assert {record["L_rank"] for record in points} == {114}
    assert {record["fibre_dimension"] for record in points} == {9}
    assert {tuple(record["L_shape"]) for record in points} == {(1038, 123)}


def test_the_timid_target_correction_is_recorded() -> None:
    construction = _compiled()["construction"]

    assert "not one" in construction["timid_slack_target"]
    assert "5 to 21 nonzero core residuals" in construction["why_that_matters"]
    assert "not an obstruction in the variety" in construction["why_that_matters"]


def test_scope_limits_survive_the_stronger_result() -> None:
    payload = _compiled()

    assert payload["verdict_strings_fixed_before_measurement"] is True
    assert any("full second-diagonal freedom" in limit for limit in payload["scope_limits"])
    assert any("Finitely many points" in limit for limit in payload["scope_limits"])
    assert any("none of the three declared" in limit for limit in payload["scope_limits"])


def test_gate_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()

    assert payload["verdict"] == gate.GLOBAL_VERDICT
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
    assert payload["solver_status"]["Groebner_or_saturation_runs"] == 0
    assert payload["solver_status"]["solver_run"] is False
