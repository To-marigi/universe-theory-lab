"""Regression checks for the v0.4.2 955 block-determinant negative result."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_block_determinant_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_block_determinant_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_dulmage_mendelsohn_block_structure() -> None:
    decomposition = _compiled()["dulmage_mendelsohn"]

    assert decomposition["matched_columns"] == 111
    assert decomposition["components"] == 60
    assert decomposition["singleton_components"] == 39
    assert decomposition["non_trivial_components"] == 21
    assert decomposition["largest_block"] == 15
    assert "matching" in decomposition["structure_is_matching_independent"]


def test_no_evaluated_block_determinant_is_a_unit() -> None:
    blocks = _compiled()["block_determinants"]

    assert blocks["evaluated_count"] == 19
    assert blocks["deferred_count"] == 2
    assert blocks["any_evaluated_block_is_a_unit"] is False
    for record in blocks["evaluated"]:
        assert record["determinant_evaluated"] is True
        assert record["is_localizer_unit"] is False
        assert record["size"] <= gate.MAX_BLOCK_EVALUATED


def test_large_blocks_are_deferred_with_a_stated_reason() -> None:
    blocks = _compiled()["block_determinants"]

    sizes = sorted(record["size"] for record in blocks["deferred"])
    assert sizes == [7, 15]
    for record in blocks["deferred"]:
        assert record["determinant_evaluated"] is False
    assert "already established" in blocks["why_deferred"]


def test_new_non_unit_factors_are_reported_explicitly() -> None:
    factors = _compiled()["new_non_unit_factors"]

    assert factors["count"] == 10
    assert factors["none_is_a_source_diagonal_entry"] is True
    assert "v52 - v55" in factors["factors"]
    assert "v271 - v283" in factors["factors"]
    assert "does not invert these" in factors["consequence"]


def test_search_space_is_recorded_as_the_obstacle() -> None:
    space = _compiled()["remaining_search_space"]

    assert space["every_column_has_alternative_unit_rows"] is True
    assert space["max_unit_rows_for_one_column"] > 1
    assert int(space["size_15_block_alone"]) > 10**28
    assert "not logically dead" in space["assessment"]


def test_result_is_scoped_as_a_route_failure_not_a_profile_statement() -> None:
    payload = _compiled()

    assert "UNIT_MINOR_ROUTE_DOES_NOT_CLOSE" in payload["verdict"]
    assert any("one route" in claim for claim in payload["claim_boundary"])
    assert any(
        "does not prove that no unit-determinant matching exists" in claim
        for claim in payload["claim_boundary"]
    )


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
