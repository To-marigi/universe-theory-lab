"""Regression checks for the 955 CSG full-jet-fibre fourth-order preflight."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import (
    source_native_955_slack_csg_fourth_order_preflight_v042 as gate,
)

ROOT = Path(__file__).resolve().parents[2]


@cache
def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_csg_fourth_order_preflight_v042(ROOT)


def test_weighted_fourth_monomial_dimensions_are_exact() -> None:
    assert gate.QUARTIC_MONOMIALS == 270725
    assert gate.Z_SQUARED_A_MONOMIALS == 60025
    assert gate.A_SQUARED_MONOMIALS == 1225
    assert gate.Z_TIMES_B_MONOMIALS == 2401
    assert gate.WEIGHTED_MONOMIALS == 334376


def test_weighted_fourth_restriction_has_an_independent_two_factor_oracle() -> None:
    assignment = [Fraction(2), Fraction(3)]
    tangent_forms = [{0: Fraction(1)}, {1: Fraction(1)}]
    particular_second = [
        {(0, 0): Fraction(1)},
        {(1, 1): Fraction(2)},
    ]
    particular_third: list[gate.ThirdForm] = [{}, {}]
    factors = gate._coordinate_factor_series(
        assignment, tangent_forms, particular_second, particular_third
    )

    third_residual, fourth = gate._weighted_third_and_fourth_restriction({(0, 1): 1}, factors)

    assert third_residual == {
        (0, 0, 1): Fraction(1),
        (0, gate.A_OFFSET + 1): Fraction(1),
        (0, 1, 1): Fraction(2),
        (1, gate.A_OFFSET): Fraction(1),
        (gate.B_OFFSET,): Fraction(3),
        (gate.B_OFFSET + 1,): Fraction(2),
    }
    assert fourth == {
        (0, 0, 1, 1): Fraction(2),
        (0, 0, gate.A_OFFSET + 1): Fraction(1),
        (1, 1, gate.A_OFFSET): Fraction(2),
        (gate.A_OFFSET, gate.A_OFFSET + 1): Fraction(1),
        (0, gate.B_OFFSET + 1): Fraction(1),
        (1, gate.B_OFFSET): Fraction(1),
    }


def test_frozen_result_regenerates_exactly_and_stays_inside_the_budget() -> None:
    frozen = _load(gate.RESULT_PATH)
    compiled = _compiled()

    assert frozen == compiled
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "688641d2e301d154542ab0296aaff4a1f1d5c5abc32c67f594a679baffd4e6b7"
    )
    assert frozen["verdict"] == gate.VERDICT
    assert frozen["scope"]["field"] == "QQ"
    assert (
        frozen["raw_fourth_order_core_stream"]["canonical_third_correction_residual_failures"] == 0
    )
    assert frozen["raw_Q_fourth_order_stream"]["canonical_third_correction_residual_failures"] == 0
    assert frozen["resource_decision"]["fail_closed_streamed_fourth_order_audit_authorised"] is True
    assert frozen["execution_boundary"]["dependent_core_compatibility_reductions"] == 0
    assert frozen["execution_boundary"]["Q_intrinsic_fourth_order_reductions"] == 0
    assert frozen["execution_boundary"]["dense_334376_column_matrix_materialised"] is False
    assert frozen["unrestricted_source_native_955_status"] == "OPEN"


def test_canonical_particular_third_correction_is_frozen() -> None:
    fibre = _compiled()["full_third_order_jet_fibre"]
    particular = fibre["particular_third_order_correction"]

    assert fibre["coordinate_model"] == "v=v_particular(z,a)+K*b"
    assert fibre["first_order_tangent_variables_z"] == 49
    assert fibre["second_order_homogeneous_fibre_variables_a"] == 49
    assert fibre["third_order_homogeneous_fibre_variables_b"] == 49
    assert fibre["total_weighted_fourth_monomial_dimension"] == 334376
    assert particular["nonzero_particular_coordinate_forms"] == 268
    assert particular["total_particular_weighted_third_terms"] == 28033
    assert particular["maximum_terms_one_particular_coordinate"] == 360
    assert particular["maximum_coefficient_bits"] == 19
    assert particular["forms_digest_sha256"] == (
        "435bb9239f479ef5ac054de7a6f605e3161ddb073e4fd8a6cf49eee06f419c5e"
    )


def test_all_raw_core_fourth_jets_are_streamed_with_frozen_sparse_counts() -> None:
    stream = _compiled()["raw_fourth_order_core_stream"]
    combined = stream["combined"]

    assert combined["scalar_slots"] == 4412
    assert combined["nonzero_fourth_forms"] == 2706
    assert combined["zero_fourth_forms"] == 1706
    assert combined["total_terms"] == 1647981
    assert combined["z_quartic_terms"] == 807387
    assert combined["z_squared_times_a_terms"] == 657142
    assert combined["a_squared_terms"] == 64286
    assert combined["z_times_b_terms"] == 119166
    assert combined["maximum_terms_one_form"] == 2376
    assert combined["portable_compact_storage_model_bytes_if_all_retained"] == 59340860
    assert combined["stream_digest_sha256"] == (
        "08a74b02b2712bfcdf2b492716109588f6c4276ef56f325a29f8b00f078552ff"
    )
    assert stream["all_raw_forms_retained"] is False

    cpobc = stream["per_block"]["CPOBC"]
    strong_gc = stream["per_block"]["strong_GC"]
    assert (
        cpobc["scalar_slots"],
        cpobc["total_terms"],
        cpobc["maximum_terms_one_form"],
    ) == (3132, 1139255, 1837)
    assert (
        strong_gc["scalar_slots"],
        strong_gc["total_terms"],
        strong_gc["maximum_terms_one_form"],
    ) == (1280, 508726, 2376)


def test_independent_jacobian_fourth_jet_basis_is_small_and_bound() -> None:
    basis = _compiled()["independent_Jacobian_basis_fourth_jet_preflight"]

    assert basis["Jacobian_rank"] == basis["independent_rows"] == 427
    assert basis["dependent_rows_not_compatibility_reduced"] == 3985
    assert basis["basis_total_weighted_terms"] == 135396
    assert basis["basis_maximum_terms_one_form"] == 1837
    assert basis["basis_portable_compact_storage_model_bytes"] == 4856782
    assert basis["basis_conservative_python_storage_estimate_bytes"] == 71071744
    assert basis["predicted_dependent_add_scaled_calls"] == 26271
    assert basis["predicted_dependent_source_term_visits"] == 6797996
    assert basis["maximum_predicted_source_term_visits_one_dependent"] == 21120
    assert basis["dependent_compatibility_forms_actually_reduced"] == 0
    assert basis["basis_forms_digest_sha256"] == (
        "aafa581432233835486f65de2bedf77bfe8c9d13524d7c47f2b78e1ed6aa11c1"
    )


def test_raw_Q_fourth_jets_are_counted_but_not_interpreted() -> None:
    q = _compiled()["raw_Q_fourth_order_stream"]

    assert q["scalar_slots"] == 24
    assert q["nonzero_fourth_forms"] == 6
    assert q["total_terms"] == 2374
    assert q["z_quartic_terms"] == 1240
    assert q["z_squared_times_a_terms"] == 945
    assert q["a_squared_terms"] == 63
    assert q["z_times_b_terms"] == 126
    assert q["maximum_terms_one_form"] == 478
    assert q["stream_digest_sha256"] == (
        "8a8028737161af61101e0fea19d710726e6582a8fbf4d9ec4f4fbc97db6ec8b3"
    )
    assert q["intrinsic_Q_reduction_executed"] is False


def test_only_a_fail_closed_streamed_fourth_order_audit_is_authorised() -> None:
    payload = _compiled()
    decision = payload["resource_decision"]

    assert decision["basis_estimate_below_soft_memory_limit"] is True
    assert decision["bounded_audit_conservative_peak_estimate_bytes"] == 5726193664
    assert decision["bounded_audit_estimate_below_hard_memory_limit"] is True
    assert decision["unbounded_dense_compatibility_basis_worst_case_terms"] == 1332488360
    assert decision["unbounded_dense_compatibility_basis_worst_case_bytes"] == 682770911232
    assert decision["unbounded_dense_strategy_rejected"] is True
    assert decision["fail_closed_streamed_fourth_order_audit_authorised"] is True
    assert decision["generic_solver_authorised"] is False
    assert decision["next_gate"] == (
        "RUN_FAIL_CLOSED_STREAMED_FOURTH_ORDER_CORE_COMPATIBILITY_AND_Q_ESCAPE_AUDIT"
    )
