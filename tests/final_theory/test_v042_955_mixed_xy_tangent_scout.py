"""Regression checks for the exact v0.4.2 mixed-x/y tangent scout."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from sympy import Rational, SparseMatrix

from universe_lab.final_theory import mixed_xy_nonneutral_scout_v042 as scout

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / scout.RESULT_PATH
MIXED_MANIFEST = ROOT / "results/v0.4.2_955_mixed_source_native_manifest.json"


@cache
def _compiled() -> dict[str, Any]:
    return scout.compile_mixed_xy_nonneutral_scout_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_diagonal_tangent_splits_into_upper_family_and_zero_lower_kernel() -> None:
    payload = _compiled()
    blocks = payload["exact_linear_blocks"]
    upper = blocks["upper"]
    lower = blocks["lower"]

    assert upper["row_counts"] == {
        "CPOBC": 783,
        "length_two_CPOBC": 712,
        "strong_GC_basis": 320,
        "reachable_MSR": 0,
        "profile_total": 1103,
    }
    assert upper["ranks"]["full_linearised_profile"] == 114
    assert upper["ranks"]["full_nullity"] == 17
    assert lower["ranks"]["CPOBC_plus_reachable_MSR"] == 131
    assert lower["ranks"]["length_two_CPOBC_plus_reachable_MSR"] == 131
    assert lower["ranks"]["full_linearised_profile"] == 131
    assert lower["ranks"]["full_nullity"] == 0

    tangent = payload["diagonal_base_tangent"]
    assert tangent["rank"] == 245
    assert tangent["nullity"] == 17
    assert tangent["lower_kernel_zero"] is True
    assert tangent["tangent_space_equals_upper_solution_space"] is True


def test_emitted_131_row_QQ_pivot_certificate_is_independently_rechecked() -> None:
    certificate = _compiled()["exact_linear_blocks"]["lower"]["full_column_rank_certificate"]
    variables = certificate["ordered_variables"]
    selected = certificate["selected_rows"]

    assert certificate["certificate_type"] == ("exact_QQ_normalized_sparse_row_echelon")
    assert len(variables) == 131
    assert len(selected) == 131
    assert certificate["selected_row_kind_counts"] == {
        "CPOBC": 108,
        "reachable_MSR": 23,
    }
    reconstructed = [
        (
            row["label"],
            {variable: Fraction(value) for variable, value in row["coefficients"]},
        )
        for row in selected
    ]
    assert scout._rank(reconstructed, variables) == 131
    positions = {variable: index for index, variable in enumerate(variables)}
    sympy_entries = {}
    for row_index, row in enumerate(selected):
        for variable, value in row["coefficients"]:
            coefficient = Fraction(value)
            sympy_entries[row_index, positions[variable]] = Rational(
                coefficient.numerator, coefficient.denominator
            )
    assert SparseMatrix(131, 131, sympy_entries).rank() == 131

    echelon = certificate["echelon_rows"]
    assert len(echelon) == 131
    assert [row["pivot_index"] for row in echelon] == list(range(131))
    assert all(row["coefficients"][0] == [row["pivot_variable"], "1"] for row in echelon)


def test_certificate_rows_are_the_y_jacobian_of_the_nonlinear_manifest() -> None:
    certificate = _compiled()["exact_linear_blocks"]["lower"]["full_column_rank_certificate"]
    manifest = json.loads(MIXED_MANIFEST.read_text(encoding="utf-8"))

    def constant_y_jacobian(polynomial: list[dict[str, Any]]) -> dict[str, Fraction]:
        row: dict[str, Fraction] = {}
        for term in polynomial:
            monomial = term["monomial"]
            y_factors = [factor for factor in monomial if str(factor["variable"]).startswith("y:")]
            if len(y_factors) != 1:
                continue
            assert len(monomial) == 1
            factor = y_factors[0]
            assert factor["exponent"] == 1
            row[str(factor["variable"])[2:]] = Fraction(str(term["coefficient"]))
        return row

    source_rows = {
        f"{record['relation_id']}:{record['equation_id']}": constant_y_jacobian(
            record["entries"]["10"]
        )
        for record in manifest["residual_blocks"]["CPOBC"]["records"]
    }
    source_rows.update(
        {
            f"{record['constraint_id']}:reachable-lower-linearisation": (
                constant_y_jacobian(record["entries"]["1"])
            )
            for record in manifest["residual_blocks"]["reachable_MSR_vector"]["records"]
        }
    )
    for selected in certificate["selected_rows"]:
        expected = {variable: Fraction(value) for variable, value in selected["coefficients"]}
        assert source_rows[selected["label"]] == expected


def test_lower_obstruction_is_universal_along_upper_family_but_not_global() -> None:
    transverse = _compiled()["transverse_to_upper_family"]

    assert transverse["upper_family"]["exact_dimension"] == 17
    assert transverse["lower_Jacobian_rank_at_every_upper_point"] == 131
    assert transverse["lower_Jacobian_nullity_at_every_upper_point"] == 0
    assert "unique local branch" in transverse["formal_local_consequence"]
    assert "does not exclude isolated or disconnected" in transverse["not_proved"]


def test_all_commutator_tangents_are_forced_and_N_is_globally_nonzero() -> None:
    payload = _compiled()
    assert payload["N_nonzero_gate"] == {
        "explicitly_guaranteed_throughout_ansatz": True,
        "source": "p1-0",
        "residual_form": "D_p1=[[0,x_Q1+x_T],[y_Q1+y_T,1]]",
        "reachable_MSR_first_column_condition": "y_Q1+y_T=0",
        "nonzero_entry_independent_of_x_y": "(D_p1)_{22}=1",
        "conclusion": "D_p1 is never the zero operator, including on every tangent slice",
    }
    assert payload["diagonal_base_tangent"]["all_six_Q_commutator_derivatives_forced_zero"] is True
    for block in payload["exact_linear_blocks"].values():
        commutators = block["Q_commutator_linearisation"]
        assert commutators["all_six_forced_zero"] is True
        assert len(commutators["records"]) == 6
        assert all(record["rank_increment"] == 0 for record in commutators["records"].values())


def test_verdict_remains_open_and_no_heavy_solver_was_run() -> None:
    payload = _compiled()
    search = payload["counterexample_search"]

    assert payload["verdict"] == scout.VERDICT
    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert search["exact_rational_candidate_found"] is False
    assert search["finite_field_runs"] == 0
    assert search["numerical_runs"] == 0
    assert search["Sage_runs"] == 0
    assert search["Groebner_or_saturation_runs"] == 0
    assert search["remaining_open_cover"] == "union of 131 patches y_[e]!=0"
