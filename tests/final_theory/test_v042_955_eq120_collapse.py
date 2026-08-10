"""Regression checks for the exact v0.4.2 955 Eq120 commutator-collapse lemma."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_eq120_collapse_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_eq120_collapse_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_eq120_zero_one_entry_equals_the_3x3_minor() -> None:
    a = {i: sympy.Symbol(f"a{i}") for i in (1, 2, 3, 4)}
    d = {i: sympy.Symbol(f"d{i}") for i in (1, 2, 3, 4)}
    b = {i: sympy.Symbol(f"b{i}") for i in (1, 2, 3, 4)}

    entry = gate._eq120_star_entry(a, b, d, 2, 3)
    minor = sympy.Matrix([[a[1], d[1], b[1]], [a[2], d[2], b[2]], [a[3], d[3], b[3]]]).det()
    assert sympy.expand(entry - minor) == 0


def test_star_has_only_two_independent_relations() -> None:
    star = _compiled()["star_rank_reduction"]

    assert star["raw_relations"] == ["E_23", "E_24", "E_34"]
    assert star["independent_relations"] == 2
    assert star["e34_is_an_automatic_consequence_of_e23_and_e24"] is True
    assert star["nonsingularity_required"] == "a_1*d_4 - a_4*d_1 != 0"


def test_all_six_commutators_collapse_to_multiples_of_lambda_with_clean_minors() -> None:
    lemma = _compiled()["collapse_lemma"]

    assert lemma["lambda_definition"] == "c_14 = (a_1-d_1)*b_4 - (a_4-d_4)*b_1"
    assert lemma["denominator"] == "a1*d4 - a4*d1"
    assert lemma["coefficients_times_denominator"] == {
        "12": "a1*d2 - a2*d1",
        "13": "a1*d3 - a3*d1",
        "14": "a1*d4 - a4*d1",
        "23": "a2*d3 - a3*d2",
        "24": "a2*d4 - a4*d2",
        "34": "a3*d4 - a4*d3",
    }
    assert lemma["verified_as_exact_polynomial_identity"] is True


def test_coefficients_are_exactly_2x2_minors_of_a_and_d() -> None:
    coefficients = _compiled()["collapse_lemma"]["coefficients_times_denominator"]
    a = {i: sympy.Symbol(f"a{i}") for i in (1, 2, 3, 4)}
    d = {i: sympy.Symbol(f"d{i}") for i in (1, 2, 3, 4)}

    for key, expected in coefficients.items():
        i, j = int(key[0]), int(key[1])
        minor = a[i] * d[j] - a[j] * d[i]
        assert sympy.expand(sympy.sympify(expected) - minor) == 0


def test_reproving_the_lemma_from_scratch_matches_the_stored_result() -> None:
    proof = gate._prove_collapse()

    assert proof["e34_is_automatic"] is True
    assert (
        sympy.simplify(
            proof["b2_solution"]
            - sympy.sympify("(a1*b4*d2 + a2*b1*d4 - a2*b4*d1 - a4*b1*d2)/(a1*d4 - a4*d1)")
        )
        == 0
    )


def test_numeric_cross_check_recomputes_lambda_independently_and_finds_zero() -> None:
    cross_check = _compiled()["numeric_cross_check"]

    assert cross_check["points_checked"] == 3
    assert cross_check["all_consistent"] is True
    for record in cross_check["records"]:
        assert record["lambda_value"] == "0"
        assert record["lambda_is_zero"] is True
        assert record["predecessor_escapes"] == 0
        assert record["consistent"] is True


def test_predecessor_binding_references_the_already_certified_eq120_provenance() -> None:
    payload = _compiled()
    binding = payload["predecessor_binding"][gate.EQ120_PATH]

    assert binding["verdict"] == "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED"
    assert payload["eq120_star_identity"]["already_proved_in"] == gate.EQ120_PATH


def test_reframed_next_gate_names_a_single_scalar_question() -> None:
    payload = _compiled()

    assert "Lambda" in payload["reframed_next_gate"]
    assert "one" in payload["reframed_next_gate"]
    assert any("a_1*d_4-a_4*d_1" in claim for claim in payload["claim_boundary"])


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
