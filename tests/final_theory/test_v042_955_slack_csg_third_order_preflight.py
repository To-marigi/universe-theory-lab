"""Regression checks for the 955 CSG full-jet-fibre third-order preflight."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import (
    source_native_955_slack_csg_third_order_preflight_v042 as gate,
)

ROOT = Path(__file__).resolve().parents[2]


@cache
def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_csg_third_order_preflight_v042(ROOT)


def test_frozen_result_regenerates_exactly_and_has_the_expected_digest() -> None:
    frozen = _load(gate.RESULT_PATH)

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "a7cac5ae64b3debdc8c98e5df18ba739b87b37fca91715f9c5236f14b56cf490"
    )
    assert frozen["verdict"] == gate.VERDICT


def test_full_second_order_jet_fibre_and_particular_correction_are_exact() -> None:
    fibre = _compiled()["full_second_order_jet_fibre"]
    particular = fibre["particular_second_order_correction"]

    assert fibre["first_order_tangent_variables_z"] == 49
    assert fibre["second_order_homogeneous_fibre_variables_a"] == 49
    assert fibre["coordinate_model"] == "w=w_particular(z)+K*a"
    assert fibre["z_cubic_monomial_dimension"] == 20825
    assert fibre["z_times_a_monomial_dimension"] == 2401
    assert fibre["total_weighted_third_monomial_dimension"] == 23226
    assert particular["nonzero_particular_coordinate_forms"] == 268
    assert particular["total_particular_quadratic_terms"] == 5111
    assert particular["maximum_terms_one_particular_coordinate"] == 62
    assert particular["maximum_coefficient_bits"] == 13
    assert particular["forms_digest_sha256"] == (
        "a9b48e13cdee32a524fe4fb0a53c1fae464d3b48bfffd8221b28b55f57e769cc"
    )


def test_all_raw_core_third_jets_are_streamed_with_frozen_sparse_counts() -> None:
    stream = _compiled()["raw_third_order_core_stream"]
    combined = stream["combined"]

    assert combined["scalar_slots"] == 4412
    assert combined["nonzero_third_forms"] == 2706
    assert combined["zero_third_forms"] == 1706
    assert combined["total_terms"] == 371687
    assert combined["z_cubic_terms"] == 252521
    assert combined["z_times_a_terms"] == 119166
    assert combined["maximum_terms_one_form"] == 502
    assert combined["portable_compact_storage_model_bytes_if_all_retained"] == 12281223
    assert combined["stream_digest_sha256"] == (
        "ae7512ad365722e4e5322de17d171ab5feb069ffd62d6c8a51dd262856eb3786"
    )
    assert stream["all_raw_forms_retained"] is False

    cpobc = stream["per_block"]["CPOBC"]
    strong_gc = stream["per_block"]["strong_GC"]
    assert (cpobc["scalar_slots"], cpobc["total_terms"], cpobc["maximum_terms_one_form"]) == (
        3132,
        260509,
        421,
    )
    assert (
        strong_gc["scalar_slots"],
        strong_gc["total_terms"],
        strong_gc["maximum_terms_one_form"],
    ) == (1280, 111178, 502)


def test_independent_jacobian_third_jet_basis_is_small_and_bound() -> None:
    basis = _compiled()["independent_Jacobian_basis_third_jet_preflight"]

    assert basis["Jacobian_rank"] == basis["independent_rows"] == 427
    assert basis["dependent_rows_not_compatibility_reduced"] == 3985
    assert basis["basis_total_weighted_terms"] == 31761
    assert basis["basis_maximum_terms_one_form"] == 421
    assert basis["basis_portable_compact_storage_model_bytes"] == 1046458
    assert basis["basis_conservative_python_storage_estimate_bytes"] == 18010624
    assert basis["predicted_dependent_add_scaled_calls"] == 26271
    assert basis["predicted_dependent_source_term_visits"] == 1602836
    assert basis["maximum_predicted_source_term_visits_one_dependent"] == 5012
    assert basis["dependent_compatibility_forms_actually_reduced"] == 0
    assert basis["basis_forms_digest_sha256"] == (
        "d8586c8cc45d57bfa5d4c5d7ae71146378606762e5212f5b611f5df03c14d287"
    )


def test_raw_Q_third_jets_are_counted_but_not_interpreted() -> None:
    q = _compiled()["raw_Q_third_order_stream"]

    assert q["scalar_slots"] == 24
    assert q["nonzero_third_forms"] == 6
    assert q["total_terms"] == 458
    assert q["z_cubic_terms"] == 332
    assert q["z_times_a_terms"] == 126
    assert q["maximum_terms_one_form"] == 87
    assert q["stream_digest_sha256"] == (
        "654d27aa3211717c9de2a4692ed35f9274ed89aa5d24a40adf981229927a58a6"
    )
    assert q["intrinsic_Q_reduction_executed"] is False


def test_weighted_third_restriction_has_an_independent_two_factor_oracle() -> None:
    polynomial = {(0, 1): 1}
    assignment = [Fraction(2), Fraction(3)]
    tangent_forms = [{0: Fraction(1)}, {1: Fraction(1)}]
    particular_forms = [
        {(0, 0): Fraction(1)},
        {(1, 1): Fraction(2)},
    ]

    assert gate._third_order_restriction(
        polynomial, assignment, tangent_forms, particular_forms
    ) == {
        (0, 0, 0, 1): Fraction(1),
        (0, 0, 1, 1): Fraction(2),
        (1, 0, 1): Fraction(1),
        (1, 1, 0): Fraction(1),
    }


def test_only_a_fail_closed_streamed_third_order_audit_is_authorised() -> None:
    payload = _compiled()
    decision = payload["resource_decision"]
    boundary = payload["execution_boundary"]

    assert decision["basis_estimate_below_soft_memory_limit"] is True
    assert decision["bounded_audit_conservative_peak_estimate_bytes"] == 5673132544
    assert decision["bounded_audit_estimate_below_hard_memory_limit"] is True
    assert decision["unbounded_dense_compatibility_basis_worst_case_bytes"] == 47925343232
    assert decision["unbounded_dense_strategy_rejected"] is True
    assert decision["fail_closed_streamed_third_order_audit_authorised"] is True
    assert decision["generic_solver_authorised"] is False
    assert decision["next_gate"] == (
        "RUN_FAIL_CLOSED_STREAMED_THIRD_ORDER_CORE_COMPATIBILITY_AND_Q_ESCAPE_AUDIT"
    )
    assert boundary["dependent_core_compatibility_reductions"] == 0
    assert boundary["Q_intrinsic_third_order_reductions"] == 0
    assert boundary["dense_23226_column_matrix_materialised"] is False
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
