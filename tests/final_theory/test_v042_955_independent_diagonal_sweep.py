"""Regression checks for the v0.4.2 955 independent-diagonal Lambda sweep."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_independent_diagonal_sweep_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_independent_diagonal_sweep_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_methodological_correction_is_recorded() -> None:
    correction = _compiled()["methodological_correction"]

    assert "vacuous" in correction["prior_error"]
    assert "never sets A:*:01" in correction["prior_error"]
    assert "Row-span membership test" in correction["correct_method"]


def test_eight_points_have_no_shared_combinatorial_pattern() -> None:
    points = {record["label"] for record in _compiled()["points"]}

    assert points == {label for label, _first, _second in gate.POINTS}
    for _label, first, second in gate.POINTS:
        assert first != (1, 1, 1, 1, 1) or second != (1, 1, 1, 1, 1)


def test_every_point_verifies_as_an_exact_core_point() -> None:
    for record in _compiled()["points"]:
        assert record["diagonal_only_residual_failures"] == 0


def test_seven_of_eight_points_have_nonzero_d() -> None:
    payload = _compiled()

    assert payload["aggregate"]["points_with_D_nonzero"] == 7
    assert payload["aggregate"]["points_with_D_zero"] == 1
    zero_d = [record for record in payload["points"] if record["D"] == "0"]
    assert len(zero_d) == 1
    assert zero_d[0]["label"] == "1_4_1_4_1__4_1_4_1_4"


def test_lambda_is_in_span_at_every_point_regardless_of_d() -> None:
    payload = _compiled()

    assert payload["aggregate"]["escapes"] == 0
    assert payload["aggregate"]["all_in_span"] is True
    for record in payload["points"]:
        assert record["status"] == "IN_SPAN"
        assert record["augmented_rank"] == record["L_rank"]
        assert record["L_shape"][0] == 1038


def test_l_rank_is_uniform_across_all_eight_points() -> None:
    payload = _compiled()

    assert payload["aggregate"]["L_rank_values"] == [114]


def test_exact_d_values_match_independent_cross_check() -> None:
    expected = {
        "swap_1_2_3_5_7__all_ones": "5/432",
        "2_3_5_7_11__1_3_2_5_4": "87/40670",
        "1_1_2_1_1__3_2_1_4_2": "6/385",
        "5_3_1_2_4__2_2_2_2_2": "-29/896",
        "1_4_1_4_1__4_1_4_1_4": "0",
        "7_5_3_2_1__1_1_3_5_7": "-287/5400",
        "1_1_1_1_2__2_1_1_1_1": "1/51",
        "pi_digits_3_1_4_1_5__9_2_6_5_3": "459/16720",
    }
    for record in _compiled()["points"]:
        assert record["D"] == expected[record["label"]]


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
