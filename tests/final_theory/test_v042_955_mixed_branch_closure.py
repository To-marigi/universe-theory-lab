"""Regression checks for the exact v0.4.2 955 mixed-ansatz closure."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_mixed_branch_closure_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH
PREDECESSOR = ROOT / gate.GLOBAL_REDUCTION_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_mixed_branch_closure_v042(ROOT)


@cache
def _predecessor() -> dict[str, Any]:
    return json.loads(PREDECESSOR.read_text(encoding="utf-8"))


def _rank_three_substitution() -> tuple[dict[str, gate.Polynomial], list[str]]:
    predecessor = _predecessor()
    variables = predecessor["reduced_system"]["variables"]
    index = {variable: column for column, variable in enumerate(variables)}
    rows = [
        {index[variable]: Fraction(coefficient) for variable, coefficient in record["coefficients"]}
        for record in predecessor["reduced_system"]["linear_part"]["rows"]
    ]
    substitution, _basis, free = gate._linear_parameterisation(rows, variables)
    return substitution, free


def _family_substitution() -> dict[str, gate.Polynomial]:
    _substitution, free = _rank_three_substitution()
    dependent = {
        "s11": {("s22",): Fraction(5, 4)},
        "s15": {("s22",): Fraction(1)},
        "s16": {("s22",): Fraction(1)},
        "s18": {("s22",): Fraction(7, 6)},
        "s21": {("s22",): Fraction(1, 12)},
    }
    result: dict[str, gate.Polynomial] = {}
    for variable in free:
        if variable.startswith("t"):
            result[variable] = {}
        elif variable in dependent:
            result[variable] = dependent[variable]
        else:
            result[variable] = {(variable,): Fraction(1)}
    return result


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_deferred_linear_rank_three_is_eliminated_exactly() -> None:
    linear = _compiled()["linear_rank_three_elimination"]

    assert linear["input_coordinates"] == 46
    assert linear["linear_entry_count"] == 5
    assert linear["rank"] == 3
    assert linear["pivot_coordinates"] == ["s19", "t19", "t21"]
    assert linear["output_coordinates"] == 43
    assert linear["substitution"] == {
        "s19": [
            {
                "coefficient": "3",
                "monomial": [{"variable": "s21", "exponent": 1}],
            }
        ],
        "t19": [],
        "t21": [],
    }


def test_linear_quotient_kills_every_reduced_Q_commutator_entry() -> None:
    quotient = _compiled()["Q_commutator_after_linear_elimination"]

    assert quotient["entries_before"] == 24
    assert quotient["terms_before"] == 60
    assert quotient["entries_checked"] == 24
    assert quotient["nonzero_remainders"] == 0
    assert quotient["identically_zero_on_the_rank_three_linear_locus"] is True

    predecessor = _predecessor()
    substitution, _free = _rank_three_substitution()
    checked = 0
    for record in predecessor["reduced_Q_commutator"]["records"]:
        for polynomial in record["entries"].values():
            checked += 1
            assert gate._substitute(gate._parse(polynomial), substitution) == {}
    assert checked == 24


def test_cpobc_collapses_to_five_scalar_monomial_equations() -> None:
    cpobc = _compiled()["CPOBC_after_linear_elimination"]

    assert cpobc["input_diagonal_entries"] == 954
    assert cpobc["identically_zero_entries"] == 870
    assert cpobc["surviving_scalar_monomial_instances"] == 84
    assert cpobc["surviving_terms"] == 84
    assert {
        record["monomial"]: record["instances"] for record in cpobc["unique_monomial_equations"]
    } == {
        "s21*t11": 16,
        "s21*t15": 13,
        "s21*t16": 13,
        "s21*t18": 30,
        "s21*t22": 12,
    }

    predecessor = _predecessor()
    substitution, _free = _rank_three_substitution()
    transformed = gate._transformed_entries(predecessor, substitution, "CPOBC")
    nonzero = [polynomial for _identifier, polynomial in transformed if polynomial]
    assert len(transformed) == 954
    assert len(nonzero) == 84
    assert all(len(polynomial) == 1 for polynomial in nonzero)
    assert {next(iter(polynomial)) for polynomial in nonzero} == {
        ("s21", "t11"),
        ("s21", "t15"),
        ("s21", "t16"),
        ("s21", "t18"),
        ("s21", "t22"),
    }


def test_both_cpobc_branches_join_one_17_dimensional_pure_upper_family() -> None:
    branches = _compiled()["exact_branch_closure"]
    nonzero = branches["s21_nonzero_branch"]
    zero = branches["s21_zero_branch"]

    assert nonzero["CPOBC_forces_zero"] == ["t11", "t15", "t16", "t18", "t22"]
    assert nonzero["combined_linear_rank"] == 21
    assert nonzero["closure_dimension"] == 17
    assert nonzero["remaining_residuals_after_linear_parameterisation"] == 0
    assert zero["combined_linear_rank"] == 26
    assert zero["dimension"] == 16
    assert zero["relation_to_nonzero_branch_closure"] == "the s22=0 hyperplane"

    classification = _compiled()["solution_classification"]
    assert classification["solution_set_inside_declared_mixed_ansatz"] == (
        "17_DIMENSIONAL_PURE_UPPER_LINEAR_FAMILY"
    )
    assert classification["free_parameter_count"] == 17
    assert classification["all_y_coordinates_zero"] is True
    assert classification["remote_or_disconnected_x_nonzero_y_nonzero_components"] == 0


def test_general_17_parameter_family_annihilates_all_1933_reduced_entries() -> None:
    predecessor = _predecessor()
    rank_three, _free = _rank_three_substitution()
    family = _family_substitution()

    checked = 0
    for block in gate.PROFILE_BLOCKS:
        for _identifier, polynomial in gate._transformed_entries(predecessor, rank_three, block):
            checked += 1
            assert gate._substitute(polynomial, family) == {}
    assert checked == 1933


def test_all_nonsingularity_factors_are_carried_and_become_nonzero_constants() -> None:
    localisations = _compiled()["nonsingularity_localisation"]

    assert localisations["raw_source_occurrences"] == 165
    assert localisations["distinct_ON_quotient_factors"] == 131
    assert localisations["automatic_after_rank_three_elimination"] == 88
    assert localisations["active_after_rank_three_elimination"] == 43
    assert localisations["active_raw_source_occurrences"] == 50
    assert localisations["unique_active_factor_polynomials"] == 26
    assert localisations["at_classified_solution_family"] == {
        "all_factors_equal_nonzero_p_e": True,
        "diagonal_character_histogram": {
            "1/16": 56,
            "1/2": 10,
            "1/4": 25,
            "1/8": 40,
        },
        "raw_occurrences_satisfied": 165,
        "failures": 0,
    }

    family = _family_substitution()
    constants = []
    for record in localisations["reduced_factors"]:
        remainder = gate._substitute(gate._parse(record["factor"]), family)
        assert set(remainder) == {()}
        assert remainder[()] != 0
        constants.append(remainder[()])
    assert len(constants) == 131


def test_gate_is_terminal_only_inside_the_declared_ansatz_and_runs_no_solver() -> None:
    payload = _compiled()

    assert payload["verdict"] == gate.VERDICT
    assert payload["commutativity_proved_for_955_profile_inside_declared_mixed_ansatz"] is True
    assert payload["commutativity_proved_for_unrestricted_source_native_955_profile"] is False
    assert payload["witness_certified"] is False
    assert payload["mixed_ansatz_search_terminal"] is True
    assert payload["full_955_search_terminal"] is False
    assert payload["solver_status"] == {
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
    assert any("unrestricted source-native slack" in claim for claim in payload["claim_boundary"])
