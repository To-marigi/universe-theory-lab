"""Regression checks for the exact v0.4.2 955 global bilinear reduction."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_global_bilinear_reduction_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH
MIXED_MANIFEST = ROOT / gate.MIXED_MANIFEST_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_global_bilinear_reduction_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_cpobc_off_diagonal_is_globally_exactly_linear() -> None:
    census = _compiled()["global_exact_linearity"]["cpobc_bidegree_census"]

    assert census["01"]["bidegrees"] == {"1,0": 2831}
    assert census["10"]["bidegrees"] == {"0,1": 2831}
    assert census["00"]["bidegrees"] == {"1,1": 1642}
    assert census["11"]["bidegrees"] == {"1,1": 1642}


def test_bidegree_census_is_independently_rechecked_against_the_manifest() -> None:
    manifest = json.loads(MIXED_MANIFEST.read_text(encoding="utf-8"))
    expected = {"00": (1, 1), "01": (1, 0), "10": (0, 1), "11": (1, 1)}

    counted = dict.fromkeys(expected, 0)
    for record in manifest["residual_blocks"]["CPOBC"]["records"]:
        for entry, polynomial in record["entries"].items():
            for term in polynomial:
                assert gate._bidegree(term["monomial"]) == expected[entry]
                counted[entry] += 1
    assert counted == {"00": 1642, "01": 2831, "10": 2831, "11": 1642}


def test_both_kernels_are_23_dimensional_and_agree_with_the_frozen_tangent_ranks() -> None:
    kernels = _compiled()["cpobc_kernels"]

    for axis in ("x", "y"):
        assert kernels[axis]["matrix_shape"] == [783, 131]
        assert kernels[axis]["rank"] == 108
        assert kernels[axis]["nullity"] == 23
        assert len(kernels[axis]["primitive_integral_basis"]) == 23
        assert all(len(vector) == 131 for vector in kernels[axis]["primitive_integral_basis"])
        assert all(
            isinstance(value, int)
            for vector in kernels[axis]["primitive_integral_basis"]
            for value in vector
        )
    assert kernels["agreement_with_frozen_tangent_ranks"]["matches"] is True


def test_kernel_basis_is_independently_verified_against_the_manifest_rows() -> None:
    payload = _compiled()
    manifest = json.loads(MIXED_MANIFEST.read_text(encoding="utf-8"))
    names = manifest["variables"]["names"]
    orbits = sorted(name[2:] for name in names if name.startswith("x:"))
    position = {orbit: index for index, orbit in enumerate(orbits)}

    for entry, prefix, axis in (("01", "x:", "x"), ("10", "y:", "y")):
        basis = payload["cpobc_kernels"][axis]["primitive_integral_basis"]
        for record in manifest["residual_blocks"]["CPOBC"]["records"]:
            row = [Fraction(0)] * 131
            for term in record["entries"][entry]:
                variable = term["monomial"][0]["variable"]
                assert variable.startswith(prefix)
                row[position[variable[2:]]] += Fraction(str(term["coefficient"]))
            for vector in basis:
                assert sum(a * b for a, b in zip(row, vector, strict=True)) == 0


def test_off_diagonal_vanishing_self_check_covers_every_entry() -> None:
    check = _compiled()["off_diagonal_vanishing_self_check"]

    assert check["cpobc_off_diagonal_entries"] == 1566
    assert check["identically_zero_after_substitution"] == 1566
    assert check["failures"] == 0


def test_reduction_is_global_and_uses_no_localisation_or_solver() -> None:
    reduction = _compiled()["reduction"]

    assert reduction["parameters_before"] == 262
    assert reduction["parameters_after"] == 46
    assert reduction["coordinates"] == {"s": 23, "t": 23}
    assert reduction["effective_parameters_modulo_gauge"] == 45
    assert reduction["localisation_used"] is False
    assert reduction["patch_decomposition_used"] is False
    assert reduction["solver_used"] is False
    assert reduction["is_a_global_identity"] is True


def test_reduced_system_census_and_preserved_grading() -> None:
    system = _compiled()["reduced_system"]
    blocks = system["blocks"]

    assert len(system["variables"]) == 46
    assert system["surviving_entries"] == 1933
    assert system["total_terms"] == 9557
    assert system["maximum_total_degree"] == 4
    assert system["gauge_grading_preserved"] is True
    assert system["gauge_grading_violations"] == 0

    assert blocks["CPOBC"]["surviving_entries"] == 954
    assert blocks["CPOBC"]["total_terms"] == 1814
    assert blocks["CPOBC"]["degree_histogram"] == {"2": 954}
    assert blocks["CPOBC"]["largest_entry_term_count"] == 3
    assert blocks["strong_GC"]["surviving_entries"] == 932
    assert blocks["strong_GC"]["total_terms"] == 7150
    assert blocks["reachable_MSR_vector"]["surviving_entries"] == 47
    assert blocks["reachable_MSR_vector"]["total_terms"] == 593


def test_reduced_linear_part_has_rank_three_and_is_not_eliminated() -> None:
    linear = _compiled()["reduced_system"]["linear_part"]

    assert linear["row_count"] == 5
    assert linear["rank"] == 3
    assert linear["implied_upper_bound_on_remaining_parameters"] == 43
    assert linear["eliminated_here"] is False
    touched = {variable for row in linear["rows"] for variable, _coefficient in row["coefficients"]}
    assert touched == {"s19", "s21", "t19", "t21"}


def test_reduced_commutator_is_small_but_not_identically_zero() -> None:
    commutator = _compiled()["reduced_Q_commutator"]

    assert commutator["surviving_entries"] == 24
    assert commutator["total_terms"] == 60
    assert commutator["identically_zero"] is False


def test_gate_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()

    assert payload["verdict"] == gate.VERDICT
    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
    assert payload["solver_status"] == {
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
    assert any("Nonsingularity" in claim for claim in payload["claim_boundary"])
