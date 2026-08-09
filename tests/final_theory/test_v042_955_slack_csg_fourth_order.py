"""Regression checks for the exact fourth-order 955 CSG jet audit."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_fourth_order_v042 as gate

ROOT = Path(__file__).resolve().parents[2]


@cache
def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_csg_fourth_order_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    frozen = _load(gate.RESULT_PATH)

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "f59d46a8d52210fe6b63757b8af10484654fbe8ef1483182dcd14c6fcfe817e4"
    )
    assert frozen["verdict"] == gate.VERDICT_ALL_LIFT_Q_BLOCKED
    assert frozen["scope"]["field"] == "QQ"
    basepoint = frozen["basepoint_and_jet_fibre_recheck"]
    assert basepoint["all_131_matrices_equal_diag_p_e_1"] is True
    assert basepoint["all_131_determinants_nonzero"] is True
    assert (
        basepoint["tangent_variables_z"],
        basepoint["second_order_fibre_variables_a"],
        basepoint["third_order_fibre_variables_b"],
    ) == (49, 49, 49)
    assert basepoint["weighted_fourth_monomial_dimension"] == 334376
    assert basepoint["particular_third_order_forms_digest_sha256"] == (
        "435bb9239f479ef5ac054de7a6f605e3161ddb073e4fd8a6cf49eee06f419c5e"
    )
    assert frozen["unrestricted_source_native_955_status"] == "OPEN"


def test_all_dependent_core_fourth_compatibility_forms_vanish() -> None:
    payload = _compiled()
    core = payload["fourth_order_core_compatibility"]
    raw = payload["raw_fourth_order_core_stream_recheck"]["combined"]

    assert raw["nonzero_fourth_forms"] == 2706
    assert raw["zero_fourth_forms"] == 1706
    assert raw["total_terms"] == 1647981
    assert (
        raw["z_quartic_terms"],
        raw["z_squared_times_a_terms"],
        raw["a_squared_terms"],
        raw["z_times_b_terms"],
    ) == (807387, 657142, 64286, 119166)
    assert raw["maximum_terms_one_form"] == 2376
    assert raw["stream_digest_sha256"] == (
        "08a74b02b2712bfcdf2b492716109588f6c4276ef56f325a29f8b00f078552ff"
    )

    assert core["scalar_slots"] == 4412
    assert core["Jacobian_rank"] == core["independent_Jacobian_rows"] == 427
    assert core["dependent_Jacobian_rows"] == 3985
    assert core["raw_nonzero_compatibility_forms"] == 0
    assert core["raw_zero_compatibility_forms"] == 3985
    assert core["raw_compatibility_term_histogram"] == {"0": 3985}
    assert core["compatibility_span_rank"] == 0
    assert core["compatibility_basis_total_terms"] == 0
    assert core["compatibility_basis_digest_sha256"] == (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    )
    assert core["all_third_order_core_jets_lift_through_fourth_order"] is True
    assert core["raw_compatibility_stream_digest_sha256"] == (
        "4ba14a1b2136e8fef7fa8dea6919b6e206d2b4483d63feda4046b36b452ad640"
    )
    assert core["Jacobian_fourth_forms_digest_sha256"] == (
        "aafa581432233835486f65de2bedf77bfe8c9d13524d7c47f2b78e1ed6aa11c1"
    )
    assert core["Jacobian_reduction_ledger"] == {
        "add_scaled_calls": 28788,
        "source_term_visits": 7524868,
        "maximum_source_terms_one_call": 1837,
    }


def test_Q_fourth_jets_vanish_intrinsically_after_core_elimination() -> None:
    q = _compiled()["Q_fourth_order_modulo_core"]
    raw = q["raw_weighted_fourth_stream_recheck"]

    assert q["scalar_entry_slots"] == 24
    assert raw["nonzero_fourth_forms"] == 6
    assert raw["total_terms"] == 2374
    assert raw["term_count_histogram_all_slots"] == {
        "0": 18,
        "308": 1,
        "335": 1,
        "342": 1,
        "433": 1,
        "478": 2,
    }
    assert raw["stream_digest_sha256"] == (
        "8a8028737161af61101e0fea19d710726e6582a8fbf4d9ec4f4fbc97db6ec8b3"
    )
    assert q["canonical_third_correction_residual_failures"] == 0
    assert q["first_order_Jacobian_remainder_failures"] == 0
    assert q["nonzero_intrinsic_weighted_fourth_forms"] == 0
    assert q["intrinsic_weighted_fourth_span_rank"] == 0
    assert q["nonzero_compatibility_span_remainders"] == 0
    assert q["rank_modulo_core_compatibility_span"] == 0
    assert q["Q_escape_blocked_through_order_four_by_linear_span"] is True
    assert q["Q_commutators_vanish_through_order_four_on_every_core_lift"] is True
    assert all(
        record["intrinsic_terms_after_core_Jacobian_jet_elimination"] == 0
        and record["terms_modulo_core_compatibility_span"] == 0
        for record in q["records"]
    )


def test_terminal_blind_directions_remain_silent_through_order_four() -> None:
    blind = _compiled()["terminal_slack_blind_directions"]

    assert blind["count"] == 16
    assert len(blind["weighted_coordinate_indices"]) == 48
    expected = sorted(
        offset + index for index in blind["tangent_coordinate_indices"] for offset in (0, 49, 98)
    )
    assert blind["weighted_coordinate_indices"] == expected
    assert blind["raw_core_weighted_fourth_monomial_occurrences"] == 0
    assert blind["raw_Q_weighted_fourth_monomial_occurrences"] == 0
    assert blind["intrinsic_Q_weighted_fourth_monomial_occurrences"] == 0
    assert blind["Q_remainder_weighted_fourth_monomial_occurrences"] == 0
    assert blind["remain_core_and_Q_silent_through_order_four"] is True


def test_only_the_bounded_sparse_audit_was_executed() -> None:
    payload = _compiled()
    boundary = payload["execution_boundary"]
    usage = payload["resource_usage"]

    assert boundary["exact_sparse_QQ_fourth_order_compatibility_audit_runs"] == 1
    assert boundary["dependent_core_compatibility_reductions"] == 3985
    assert boundary["Q_intrinsic_fourth_order_reductions"] == 24
    assert boundary["Groebner_or_saturation_runs"] == 0
    assert boundary["finite_field_runs"] == 0
    assert boundary["numerical_runs"] == 0
    assert boundary["Sage_runs"] == 0
    assert boundary["generic_solver_run"] is False
    assert usage["below_hard_memory_limit"] is True
    assert usage["actual_Jacobian_basis_terms"] == 135396
    assert usage["actual_compatibility_basis_terms"] == 0
    assert usage["actual_Jacobian_basis_form_overhead_bytes"] == 1748992
    assert usage["conservative_basis_memory_estimate_bytes"] == 607942656
    assert usage["raw_forms_streamed_and_discarded"] is True
    assert usage["dense_334376_column_matrix_materialised"] is False
    assert payload["execution_decision"] == {
        "generic_solver_authorised": False,
        "higher_order_full_jet_fibre_preflight_authorised": True,
        "next_gate": "DESIGN_THE_FIFTH_ORDER_FULL_FOURTH_JET_FIBER_PREFLIGHT",
    }
