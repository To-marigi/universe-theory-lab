"""Exact checks for the weak/weak state-native rank-two chart."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_state_native_rank2_v042 as chart

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return chart.build_payload(ROOT)


def test_frozen_state_native_chart_rebuilds_exactly(
    rebuilt: dict[str, Any],
) -> None:
    frozen = _load(chart.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == chart.semantic_digest(frozen)
    assert frozen["verdict"] == chart.VERDICT
    assert frozen["search_terminal"] == chart.SEARCH_TERMINAL
    assert frozen["passed"] is True


def test_growth_graph_and_alias_inventory_are_frozen(
    rebuilt: dict[str, Any],
) -> None:
    graph = rebuilt["growth_graph"]
    assert graph["endpoint_count"] == 87
    assert graph["endpoint_stage_histogram"] == {
        "1": 1,
        "2": 2,
        "3": 5,
        "4": 16,
        "5": 63,
    }
    assert graph["source_count"] == 24
    assert graph["terminal_count"] == 63
    assert graph["actual_ON_edge_count"] == 131
    assert graph["occurrence_alias_count"] == 165
    assert graph["orbit_alias_size_histogram"] == {
        "1": 104,
        "2": 22,
        "3": 3,
        "4": 2,
    }


def test_harmonic_boundary_slice_has_exact_rank_two(
    rebuilt: dict[str, Any],
) -> None:
    harmonic = rebuilt["harmonic_rank2_state_slice"]
    assert harmonic["initial_vector"] == ["1", "0"]
    assert harmonic["raw_h_root_before_normalisation"] == "357"
    assert harmonic["terminal_root_weight_sum"] == 357
    assert harmonic["terminal_root_weight_min"] == 1
    assert harmonic["terminal_root_weight_max"] == 25
    assert harmonic["reachable_span_rank"] == 2
    assert harmonic["support_state_determinant"] != "0"
    assert len(harmonic["endpoint_states"]) == 87
    assert all(rebuilt["gates"].values())


def test_affine_frames_build_in_gc_msr_and_reduce_nonsingularity_to_beta(
    rebuilt: dict[str, Any],
) -> None:
    frame = rebuilt["local_frame_parameterisation"]
    assert frame["full_actual_parameter_count"] == 262
    assert frame["shear_parameter_count"] == 131
    assert frame["determinant_formula"] == "det(A_e)=(h_target/h_source)*beta_e"

    validation = rebuilt["exact_sample_semantic_validation"]
    assert validation["path_actions_checked"] == 407
    assert validation["fixed_GC_pairs_checked"] == 1529
    assert validation["reachable_MSR_sources_checked"] == 24
    assert validation["occurrence_determinants_checked"] == 165
    assert all(not failures for failures in validation["failures"].values())


def test_remaining_operator_relations_stay_separate_and_nonterminal(
    rebuilt: dict[str, Any],
) -> None:
    manifest = rebuilt["remaining_operator_relation_manifest"]
    assert manifest["CPOBC_raw"] == 783
    assert manifest["CPOBC_word_length_pairs"] == {"2x2": 712, "3x3": 71}
    assert manifest["Eq113_separate_branches"] == {
        "EQ113_QN_BRANCH": 25,
        "EQ113_QN_PLUS_1_BRANCH": 25,
    }
    assert manifest["Eq139_strict"] == 4
    assert manifest["Eq139_completed"] == 10
    assert manifest["inverse_rewrites_for_final_candidate"] == 712
    assert rebuilt["witness"] is None
    assert rebuilt["search_terminal"].startswith("NOT_A_SEARCH_TERMINAL")
