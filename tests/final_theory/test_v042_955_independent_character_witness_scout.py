"""Regression checks for the bounded independent-character witness scout."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import (
    source_native_955_independent_character_witness_scout_v042 as gate,
)

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_independent_character_witness_scout_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_grid_is_small_and_deterministic() -> None:
    payload = _compiled()
    assert payload["scope"]["first_grid_size"] == 8
    assert payload["scope"]["second_grid_size"] == 8
    assert payload["scope"]["maximum_product_points"] == 64
    assert payload["search"]["points_attempted"] == 64


def test_every_point_passes_core_and_source_localizers() -> None:
    search = _compiled()["search"]
    assert search["points_verified_core"] == 64
    assert search["core_failure_points"] == 0
    assert search["source_singular_points"] == 0


def test_no_lambda_escape_on_nonzero_d_points() -> None:
    payload = _compiled()
    search = payload["search"]
    assert search["D14_nonzero_points"] == 54
    assert search["lambda_escape_candidates"] == []
    assert all(
        record["status"] == "NO_ESCAPE"
        for record in search["records"]
        if record["D14"] != "0"
    )


def test_scout_stays_open_and_does_not_claim_a_witness() -> None:
    payload = _compiled()
    assert payload["verdict"] == gate.NO_ESCAPE_VERDICT
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_candidate_found"] is False
    assert payload["witness_certified"] is False
    assert payload["search_terminal"] is False
    assert payload["solver_status"]["solver_run"] is False
