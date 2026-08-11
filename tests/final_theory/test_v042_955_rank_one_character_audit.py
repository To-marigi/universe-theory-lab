"""Regression checks for the source-native rank-one branch audit."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_rank_one_character_audit_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_rank_one_character_audit_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_rank_one_grid_counts_are_exact() -> None:
    search = _compiled()["search"]
    assert search["rank_one_candidates"] == 93
    assert search["core_failure_points"] == 0
    assert search["source_singular_points"] == 0
    assert search["q_diagonal_non_scalar_points"] == 12


def test_all_six_commutators_stay_in_span() -> None:
    payload = _compiled()
    records = payload["search"]["records"]
    assert payload["search"]["commutator_escape_points"] == 0
    accepted = [record for record in records if record["status"] == "NO_ESCAPE"]
    assert len(accepted) == 93
    assert {record["L_rank"] for record in accepted} == {103, 114}
    for record in accepted:
        assert {item["status"] for item in record["commutators"]} == {"IN_SPAN"}


def test_audit_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()
    assert payload["verdict"] == gate.VERDICT
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_certified"] is False
    assert payload["search_terminal"] is False
    assert payload["solver_status"]["solver_run"] is False
