"""Regression checks for the solver-free localized-module preflight."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import (
    source_native_955_localized_row_module_preflight_v042 as gate,
)

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_localized_row_module_preflight_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_scalar_and_fibre_manifest_is_exact() -> None:
    scalar = _compiled()["scalar_core_manifest"]
    fibre = _compiled()["upper_right_linear_fibre_manifest"]

    assert scalar["scalar_coordinates"] == 246
    assert scalar["nonzero_scalar_core_entries"] == 1814
    assert scalar["distinct_nonzero_scalar_core_entries"] == 1504
    assert fibre["rows"] == 1038
    assert fibre["fibre_columns"] == 123
    assert fibre["non_q_columns"] == 119
    assert fibre["direct_q_only_rows"] == 0
    assert fibre["exactly_linear_in_fibre"] is True


def test_localizers_and_rank_two_anchor_cover_are_only_preflight_data() -> None:
    payload = _compiled()
    localizers = payload["source_determinant_localization_manifest"]
    anchors = payload["anchor_forms"]
    contract = payload["localized_certificate_contract"]

    assert localizers["count"] == 131
    assert localizers["distinct_count"] == 131
    assert localizers["maximum_terms"] == 145
    assert localizers["maximum_degree"] == 5
    assert localizers["product_materialized"] is False
    assert anchors["rank_two_cover"] == [
        "D14 != 0",
        "D14 = 0 and D12 != 0",
        "D14 = D12 = 0 and D13 != 0",
    ]
    assert anchors["rank_one_branch_certified"] is False
    assert contract["finite_minor_cover_status"] == "FINITE_MINOR_COVER_REQUIRED"
    assert contract["certificate_issued"] is False


def test_pointwise_pivots_do_not_close_the_profile() -> None:
    payload = _compiled()
    points = payload["pointwise_pivot_preflight"]["points"]

    assert len(points) == 4
    assert {point["candidate_minor_size"] for point in points} == {111}
    assert all(point["certificate_scope"] == "pointwise pivot only" for point in points)
    assert payload["scope"]["full_S_claim"] is False
    assert payload["declared_955_terminal_reached"] is False
    assert payload["solver_status"]["solver_run"] is False
    assert payload["search_terminal"] is False
