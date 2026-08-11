"""Regression checks for the finite localized-minor preflight."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_minor_cover_preflight_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_minor_cover_preflight_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_structural_matching_is_not_full() -> None:
    matching = _compiled()["structural_monomial_matching"]
    assert matching["non_q_columns"] == 119
    assert matching["columns_with_monomial_edges"] == 107
    assert matching["monomial_matching_size"] == 107
    assert matching["matching_is_full"] is False
    assert len(matching["unmatched_non_q_columns"]) == 12
    assert matching["matching_factor_occurrences"] == 112
    assert matching["matching_max_factor_degree"] == 3
    assert matching["matching_coefficients_abs_one"] is True
    assert matching["all_matching_factors_are_source_diagonal"] is True
    assert matching["source_determinants_all_nonzero"] is True
    assert matching["matching_factors_appear_in_source_localizer_support"] is True
    assert matching["matching_factor_names_not_in_source_localizers"] == []
    assert matching["unit_minor_certificate_issued"] is False


def test_sample_points_are_exact_and_anchor_separated() -> None:
    sample = _compiled()["sample"]
    assert sample["points_attempted"] == 38
    assert sample["points_verified_core"] == 38
    assert sample["core_failure_points"] == 0
    assert sample["source_singular_points"] == 0
    assert sample["rank_one_points"] == 4
    assert sample["rank_two_points"] == 34
    cover = _compiled()["finite_sample_cover_by_anchor"]
    assert cover["D14"]["sample_points"] == 32
    assert cover["D12"]["sample_points"] == 1
    assert cover["D13"]["sample_points"] == 1


def test_finite_sample_cover_is_not_promoted_to_a_certificate() -> None:
    payload = _compiled()
    d14_cover = payload["finite_sample_cover_by_anchor"]["D14"]["cover"]
    assert d14_cover["minimum_cover_size_on_sample"] == 2
    assert d14_cover["sample_cover_certified"] is False
    contract = payload["localized_certificate_contract"]
    assert contract["source_determinant_localization_used"] is False
    assert contract["scalar_core_ideal_used"] is False
    assert contract["full_S_minor_cover_issued"] is False


def test_preflight_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()
    assert payload["verdict"] == gate.VERDICT
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_certified"] is False
    assert payload["search_terminal"] is False
    assert payload["solver_status"]["solver_run"] is False
