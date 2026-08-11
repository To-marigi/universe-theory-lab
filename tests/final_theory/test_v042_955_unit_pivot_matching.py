"""Regression checks for the v0.4.2 955 unit-pivot matching gate."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_unit_pivot_matching_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_unit_pivot_matching_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_gate18_unmatched_columns_are_all_slack() -> None:
    layout = _compiled()["column_layout"]

    assert layout["matrix_columns_A_01"] == 107
    assert layout["slack_columns_u_0"] == 16
    assert layout["total"] == 123
    assert layout["gate18_unmatched_are_all_slack"] is True


def test_only_four_extra_pivots_are_required() -> None:
    required = _compiled()["required_pivot_rank"]

    assert required["non_q_columns"] == 119
    assert required["non_q_rank"] == 111
    assert required["monomial_matched_rank"] == 107
    assert required["gap"] == 4
    assert required["extra_pivot_columns"] == [
        "u:p2-2:0",
        "u:p3-006:0",
        "u:p3-024:0",
        "u:p3-026:0",
    ]
    assert required["same_columns_at_every_point"] is True
    assert len(required["points"]) == 3


def test_scalar_degeneration_is_excluded_from_the_rank_measurement() -> None:
    required = _compiled()["required_pivot_rank"]

    assert "scalar degeneration" in required["scalar_degeneration_excluded"]
    for record in required["points"]:
        assert not (
            record["first_couplings"] == [1, 1, 1, 1, 1]
            and record["second_couplings"] == [1, 1, 1, 1, 1]
        )
        assert record["non_q_rank"] == 111
        assert record["gap"] == 4


def test_eight_terminal_slack_columns_are_free_directions() -> None:
    free = _compiled()["free_slack_columns"]

    assert free["count"] == 8
    assert free["never_used_as_pivots"] is True
    assert free["all_at_terminal_p4_stage"] is True
    assert all(name.startswith("u:p4-") for name in free["columns"])


def test_each_extra_pivot_factors_into_localizer_units() -> None:
    factorisations = _compiled()["extra_pivot_factorisations"]

    assert len(factorisations) == 4
    assert {record["column"] for record in factorisations} == {
        "u:p2-2:0",
        "u:p3-006:0",
        "u:p3-024:0",
        "u:p3-026:0",
    }
    for record in factorisations:
        assert record["all_factors_are_localizer_units"] is True
        assert record["monomials"] >= 2


def test_unit_edge_matching_attains_the_required_rank_on_distinct_rows() -> None:
    matching = _compiled()["unit_edge_matching"]

    assert matching["columns_with_a_localizer_unit_row"] == 111
    assert matching["maximum_matching_size"] == 111
    assert matching["matches_required_rank"] is True
    assert matching["rows_are_distinct"] is True
    assert len(matching["unmatched_columns"]) == 8
    assert matching["unmatched_have_no_unit_row"] is True


def test_determinant_unit_is_explicitly_not_certified() -> None:
    status = _compiled()["determinant_unit_status"]

    assert status["certified"] is False
    assert "signed sum over permutations" in status["why_not"]
    assert status["sparse_first_selection_columns"] == 111
    assert status["strictly_triangular_steps"] == 98
    assert status["maximum_residual_support_at_selection"] == 2
    assert status["steps_short_of_triangular"] == 13


def test_gate_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()

    assert payload["verdict"] == gate.VERDICT
    assert "DETERMINANT_UNIT_NOT_CERTIFIED" in payload["verdict"]
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
    assert payload["solver_status"]["Groebner_or_saturation_runs"] == 0
    assert payload["solver_status"]["solver_run"] is False
    assert any("no localized row-module certificate" in c for c in payload["claim_boundary"])
