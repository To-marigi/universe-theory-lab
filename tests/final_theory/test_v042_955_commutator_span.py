"""Regression checks for the exact v0.4.2 955 commutator row-span decision."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import source_native_955_commutator_span_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_commutator_span_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_verdict_strings_were_fixed_before_the_measurement() -> None:
    payload = _compiled()

    assert payload["verdict_strings_fixed_before_measurement"] is True
    assert payload["gate_design"] == "reports/v0.4.2_955_commutator_span_gate_design.md"
    assert (ROOT / payload["gate_design"]).exists()


def test_control_coupling_reproduces_the_frozen_growth_characters() -> None:
    reduction = gate._load(ROOT / gate.REDUCTION_PATH)
    mixed = gate._load(ROOT / gate.MIXED_MANIFEST_PATH)
    frozen = {
        orbit: Fraction(str(value))
        for orbit, value in mixed["variables"]["CSG_diagonal_character"].items()
    }

    characters = gate._characters(reduction, [Fraction(1)] * 5)
    assert characters == frozen
    assert sorted({str(value) for value in characters.values()}) == [
        "1/16",
        "1/2",
        "1/4",
        "1/8",
    ]


def test_general_couplings_give_genuinely_different_characters() -> None:
    reduction = gate._load(ROOT / gate.REDUCTION_PATH)

    frozen = gate._characters(reduction, [Fraction(1)] * 5)
    general = gate._characters(reduction, [Fraction(value) for value in (1, 2, 3, 5, 7)])
    assert general != frozen
    assert len({str(value) for value in general.values()}) > 1


def test_every_evaluated_point_is_an_exact_core_solution() -> None:
    points = _compiled()["evaluated_points"]

    assert len(points) == 4
    for record in points:
        assert record["nonzero_core_entries"] == 0
        assert record["streamed_core_entries"] == 4152
        assert record["L_shape"] == [1038, 123]


def test_all_six_forms_are_in_span_at_every_evaluated_point() -> None:
    payload = _compiled()

    for record in payload["evaluated_points"]:
        assert record["L_rank"] == 114
        assert record["fibre_dimension"] == 9
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
            assert entry["polynomial_monomials_before_evaluation"] == 4
            assert entry["nonzero_columns_after_evaluation"] == 2
            assert entry["rank_increment"] == 0
            assert entry["status"] == "IN_SPAN"

    assert payload["aggregate"]["points_verified_as_exact_core_solutions"] == 4
    assert payload["aggregate"]["total_escapes"] == 0
    assert payload["aggregate"]["L_rank_values"] == [114]
    assert payload["aggregate"]["fibre_dimension_values"] == [9]


def test_degenerate_couplings_are_rejected_with_their_exact_reason() -> None:
    rejected = {record["label"]: record for record in _compiled()["rejected_couplings"]}

    assert set(rejected) == {"degenerate_zero_odd", "degenerate_negative"}
    assert rejected["degenerate_zero_odd"]["stage"] == "assignment_construction"
    assert "reachable state became zero" in rejected["degenerate_zero_odd"]["reason"]
    assert rejected["degenerate_negative"]["stage"] == "character_construction"
    assert "not usable" in rejected["degenerate_negative"]["reason"]


def test_unusable_coupling_raises_rather_than_being_repaired() -> None:
    reduction = gate._load(ROOT / gate.REDUCTION_PATH)

    with pytest.raises(gate.UnusableCoupling):
        gate._characters(reduction, [Fraction(value) for value in (1, -2, 3, -4, 5)])


def test_commutator_shape_matches_the_upper_triangular_algebra() -> None:
    shape = _compiled()["commutator_shape"]

    assert shape["unevaluated_monomials_per_pair"] == 4
    assert shape["nonzero_columns_after_evaluating_the_diagonal"] == 2
    assert "(a_i-d_i)b_j-(a_j-d_j)b_i" in shape["reason"]


def test_scope_limits_name_the_frozen_second_diagonal() -> None:
    limits = _compiled()["scope_limits"]

    assert any("A:*:11 to one" in limit for limit in limits)
    assert any("Finitely many points" in limit for limit in limits)
    assert any("reachable visibility" in limit for limit in limits)


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
