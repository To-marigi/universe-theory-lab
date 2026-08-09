"""Regression checks for the exact 955 CSG third-order audit."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_third_order_v042 as gate

ROOT = Path(__file__).resolve().parents[2]


@cache
def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_csg_third_order_v042(ROOT)


def test_frozen_result_regenerates_exactly_and_has_the_expected_digest() -> None:
    frozen = _load(gate.RESULT_PATH)

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "53d7818f4bff6e5d3c556cdb137644feeae73a4bde50f74d5cb84feb8db16bfa"
    )
    assert frozen["verdict"] == gate.VERDICT_ALL_LIFT_Q_BLOCKED


def test_full_second_order_jet_fibre_is_rechecked_before_third_order() -> None:
    setup = _compiled()["basepoint_and_jet_fibre_recheck"]

    assert setup["assignment_sha256"] == (
        "b3fab5af7ab110d3ab86215152e71132774deacc6c8dea430e1b99adb192eb93"
    )
    assert setup["all_131_matrices_equal_diag_p_e_1"] is True
    assert setup["all_131_determinants_nonzero"] is True
    assert setup["tangent_variables_z"] == 49
    assert setup["second_order_fibre_variables_a"] == 49
    assert setup["weighted_third_monomial_dimension"] == 23226
    assert setup["particular_second_order_forms_digest_sha256"] == (
        "a9b48e13cdee32a524fe4fb0a53c1fae464d3b48bfffd8221b28b55f57e769cc"
    )


def test_all_3985_third_order_core_compatibility_forms_vanish() -> None:
    core = _compiled()["third_order_core_compatibility"]

    assert core["scalar_slots"] == 4412
    assert core["Jacobian_rank"] == core["independent_Jacobian_rows"] == 427
    assert core["dependent_Jacobian_rows"] == 3985
    assert core["raw_nonzero_compatibility_forms"] == 0
    assert core["raw_zero_compatibility_forms"] == 3985
    assert core["raw_compatibility_term_histogram"] == {"0": 3985}
    assert core["compatibility_span_rank"] == 0
    assert core["compatibility_basis_total_terms"] == 0
    assert core["all_second_order_core_jets_lift_through_third_order"] is True
    assert core["raw_compatibility_stream_digest_sha256"] == (
        "4ba14a1b2136e8fef7fa8dea6919b6e206d2b4483d63feda4046b36b452ad640"
    )
    assert core["Jacobian_third_forms_digest_sha256"] == (
        "d8586c8cc45d57bfa5d4c5d7ae71146378606762e5212f5b611f5df03c14d287"
    )


def test_all_Q_third_jets_reduce_to_zero_modulo_the_core() -> None:
    q = _compiled()["Q_third_order_modulo_core"]

    assert q["scalar_entry_slots"] == len(q["records"]) == 24
    assert q["raw_weighted_third_stream_recheck"]["stream_digest_sha256"] == (
        "654d27aa3211717c9de2a4692ed35f9274ed89aa5d24a40adf981229927a58a6"
    )
    assert sum(record["raw_weighted_terms"] > 0 for record in q["records"]) == 6
    assert sum(record["raw_weighted_terms"] for record in q["records"]) == 458
    assert q["first_order_Jacobian_remainder_failures"] == 0
    assert q["nonzero_intrinsic_weighted_third_forms"] == 0
    assert q["intrinsic_weighted_third_span_rank"] == 0
    assert q["nonzero_compatibility_span_remainders"] == 0
    assert q["rank_modulo_core_compatibility_span"] == 0
    assert q["Q_escape_blocked_through_order_three_by_linear_span"] is True
    assert q["Q_commutators_vanish_through_order_three_on_every_core_lift"] is True
    assert all(
        record["intrinsic_terms_after_core_Jacobian_jet_elimination"] == 0
        and record["terms_modulo_core_compatibility_span"] == 0
        for record in q["records"]
    )


def test_weighted_form_reduction_has_a_small_independent_oracle() -> None:
    cubic = (0, 0, 0, 0)
    bilinear = (1, 0, 0)
    basis = {cubic: {cubic: Fraction(1), bilinear: Fraction(2)}}

    assert gate._reduce_third_form(
        {cubic: Fraction(3), bilinear: Fraction(6)}, basis
    ) == {}
    assert gate._reduce_third_form(
        {cubic: Fraction(3), bilinear: Fraction(7)}, basis
    ) == {bilinear: Fraction(1)}


def test_terminal_blind_directions_remain_silent_through_third_order() -> None:
    blind = _compiled()["terminal_slack_blind_directions"]

    assert blind["count"] == len(blind["ambient_coordinate_names"]) == 16
    assert blind["raw_core_weighted_third_monomial_occurrences"] == 0
    assert blind["raw_Q_weighted_third_monomial_occurrences"] == 0
    assert blind["intrinsic_Q_weighted_third_monomial_occurrences"] == 0
    assert blind["Q_remainder_weighted_third_monomial_occurrences"] == 0
    assert blind["remain_core_and_Q_silent_through_order_three"] is True


def test_a_fourth_order_preflight_but_no_generic_solver_is_authorised() -> None:
    payload = _compiled()
    resource = payload["resource_usage"]
    boundary = payload["execution_boundary"]
    decision = payload["execution_decision"]

    assert resource["actual_Jacobian_basis_terms"] == 31761
    assert resource["actual_compatibility_basis_terms"] == 0
    assert resource["conservative_basis_memory_estimate_bytes"] == 553132544
    assert resource["below_hard_memory_limit"] is True
    assert resource["dense_23226_column_matrix_materialised"] is False
    assert boundary["dependent_core_compatibility_reductions"] == 3985
    assert boundary["Q_intrinsic_third_order_reductions"] == 24
    assert boundary["generic_solver_run"] is False
    assert decision == {
        "generic_solver_authorised": False,
        "higher_order_formal_audit_authorised": True,
        "next_gate": "DESIGN_THE_FOURTH_ORDER_FULL_THIRD_JET_FIBER_PREFLIGHT",
    }
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
