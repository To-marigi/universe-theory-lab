"""Regression checks for the unrestricted 955 CSG second-order audit."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_second_order_v042 as gate

ROOT = Path(__file__).resolve().parents[2]


@cache
def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_csg_second_order_v042(ROOT)


def test_frozen_result_regenerates_exactly_and_has_the_expected_digest() -> None:
    frozen = _load(gate.RESULT_PATH)

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "2c84fa6af833e320fe9e292a359808a7fcc162e225ce30edf038b5d352ae35f0"
    )
    assert frozen["verdict"] == gate.VERDICT


def test_predecessors_basepoint_and_tangent_kernel_are_frozen() -> None:
    payload = _compiled()
    basepoint = payload["basepoint_recheck"]
    kernel = payload["tangent_kernel"]

    assert payload["scope"]["field"] == "QQ"
    assert payload["scope"]["formal_order"] == 2
    assert basepoint == {
        "assignment_sha256": (
            "b3fab5af7ab110d3ab86215152e71132774deacc6c8dea430e1b99adb192eb93"
        ),
        "nonzero_slack_coordinates": 24,
        "all_131_matrices_equal_diag_p_e_1": True,
        "all_131_determinants_nonzero": True,
        "core_residual_failures": 0,
    }
    assert kernel["dimension"] == 49
    assert kernel["maximum_basis_vector_support"] == 158
    assert kernel["maximum_tangent_variables_in_one_ambient_coordinate"] == 12
    assert kernel["ambient_coordinates_zero_on_entire_tangent_kernel"] == 107
    assert kernel["basis_digest_sha256"] == (
        "6a16541866ac02b1c183bea412b6aa228659e0bbc96409cad33d01913e73075e"
    )


def test_all_3985_core_compatibility_forms_vanish() -> None:
    core = _compiled()["second_order_core_compatibility"]

    assert core["scalar_slots"] == 4412
    assert core["Jacobian_rank"] == core["independent_Jacobian_rows"] == 427
    assert core["dependent_Jacobian_rows"] == 3985
    assert core["basepoint_failures"] == core["restricted_linear_failures"] == 0
    assert core["raw_nonzero_compatibility_forms"] == 0
    assert core["raw_zero_compatibility_forms"] == 3985
    assert core["raw_compatibility_term_histogram"] == {"0": 3985}
    assert core["compatibility_quadratic_span_rank"] == 0
    assert core["every_first_order_tangent_lifts_through_second_order"] is True
    assert core["Jacobian_echelon_digest_sha256"] == (
        "e41c6382cba66e7d0deaaa8131bba1cd306f761a9c5f8a006008eac5dfd9ab52"
    )
    assert core["raw_compatibility_stream_digest_sha256"] == (
        "4ba14a1b2136e8fef7fa8dea6919b6e206d2b4483d63feda4046b36b452ad640"
    )


def test_all_Q_commutators_vanish_through_order_two_on_core_lifts() -> None:
    q = _compiled()["Q_second_order_modulo_core"]

    assert q["scalar_entry_slots"] == len(q["records"]) == 24
    assert q["basepoint_failures"] == 0
    assert q["first_order_Jacobian_remainder_failures"] == 0
    assert q["nonzero_intrinsic_quadratic_forms"] == 0
    assert q["intrinsic_quadratic_span_rank"] == 0
    assert q["compatibility_span_remainder_nonzero_forms"] == 0
    assert q["rank_modulo_core_compatibility_span"] == 0
    assert q["all_Q_second_order_forms_in_compatibility_span"] is True
    assert q["second_order_Q_escape_blocked_by_linear_span"] is True
    assert q["Q_commutators_vanish_through_order_two_on_every_core_lift"] is True
    assert all(
        record["intrinsic_quadratic_terms_after_core_Jacobian_elimination"] == 0
        and record["compatibility_span_remainder_terms"] == 0
        for record in q["records"]
    )


def test_the_sixteen_global_blind_directions_remain_silent_at_second_order() -> None:
    blind = _compiled()["terminal_slack_blind_directions"]

    assert blind["count"] == len(blind["ambient_coordinate_names"]) == 16
    assert blind["raw_core_quadratic_monomial_occurrences"] == 0
    assert blind["raw_Q_quadratic_monomial_occurrences"] == 0
    assert blind["compatibility_quadratic_monomial_occurrences"] == 0
    assert blind["Q_intrinsic_quadratic_monomial_occurrences"] == 0
    assert blind["remain_core_and_Q_silent_through_order_two"] is True
    assert all(name.startswith("u:p4-") for name in blind["ambient_coordinate_names"])


def test_quadratic_restriction_has_an_independent_two_variable_oracle() -> None:
    polynomial = {(0, 1): 1}
    assignment = [Fraction(2), Fraction(3)]
    tangent_coordinate_forms = [
        {0: Fraction(1), 1: Fraction(2)},
        {0: Fraction(-1), 1: Fraction(1)},
    ]

    assert gate._quadratic_restriction(
        polynomial, assignment, tangent_coordinate_forms
    ) == {
        (0, 0): Fraction(-1),
        (0, 1): Fraction(-1),
        (1, 1): Fraction(2),
    }


def test_only_a_streamed_third_order_formal_audit_is_authorised() -> None:
    payload = _compiled()
    resource = payload["resource_boundary"]
    decision = payload["execution_decision"]

    assert resource["ambient_Hessian_tensor_materialised"] is False
    assert resource["full_scalar_manifest_materialised"] is False
    assert resource["maximum_possible_quadratic_monomials"] == 1225
    assert decision["generic_solver_authorised"] is False
    assert decision["higher_order_formal_audit_authorised"] is True
    assert decision["next_gate"] == (
        "PREFLIGHT_THEN_STREAM_THE_THIRD_ORDER_CORE_COMPATIBILITY_AND_Q_"
        "ESCAPE_ON_THE_FULL_SECOND_ORDER_CSG_JET_FIBER"
    )
    assert payload["solver_status"] == {
        "exact_sparse_QQ_jet_linear_algebra_runs": 1,
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
