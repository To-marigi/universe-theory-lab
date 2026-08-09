"""Regression checks for the unrestricted 955 CSG-basepoint tangent audit."""

from __future__ import annotations

import json
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as gate
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_csg_tangent_v042(ROOT)


@cache
def _raw_audit() -> tuple[
    list[str],
    list[gate.SparseRow],
    list[gate.SparseRow],
    dict[int, gate.SparseRow],
]:
    slack = _load(gate.SLACK_INVENTORY_PATH)
    mixed = _load(gate.MIXED_MANIFEST_PATH)
    names: list[str] = []
    matrices, _states, _profile = terms._compile_matrices(slack, names)
    assignment, _basepoint, _targets = gate._build_csg_assignment(slack, mixed, matrices, names)
    cpobc, _cpobc_profile = gate._stream_jacobian_block(
        "CPOBC",
        slack["raw_source_system"]["CPOBC_equations"],
        ("relation_id", "equation_id"),
        matrices,
        assignment,
    )
    strong_gc, _gc_profile = gate._stream_jacobian_block(
        "strong_GC",
        slack["raw_source_system"]["strong_GC_basis"],
        ("relation_id", "endpoint_causet_id"),
        matrices,
        assignment,
    )
    q_representatives, _records = gate._q_mapping(slack, mixed)
    q_rows, _q_records, _q_profile = gate._q_commutator_jacobian(
        q_representatives, matrices, assignment
    )
    return names, cpobc + strong_gc, q_rows, gate._echelon(cpobc + strong_gc)


def test_frozen_result_regenerates_exactly_and_has_the_expected_digest() -> None:
    frozen = _load(gate.RESULT_PATH)

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "3182718cc0424dcc7837c8f2cc3dd03e6b27c0c106f9dbbb378b936c5e50e382"
    )
    assert frozen["verdict"] == gate.VERDICT


def test_diagonal_csg_point_has_a_unique_n_nonzero_slack_inverse_image() -> None:
    basepoint = _compiled()["basepoint_inverse_image"]

    assert basepoint["coordinates"] == 476
    assert basepoint["assignment_sha256"] == (
        "b3fab5af7ab110d3ab86215152e71132774deacc6c8dea430e1b99adb192eb93"
    )
    assert basepoint["all_131_matrices_equal_diag_p_e_1"] is True
    assert basepoint["all_131_determinants_nonzero"] is True
    assert basepoint["determinant_value_histogram"] == {
        "1/16": 56,
        "1/2": 10,
        "1/4": 25,
        "1/8": 40,
    }
    assert basepoint["nonzero_slack_coordinate_count"] == 24
    assert all(record["u"][0] == "0" for record in basepoint["slack_records"])
    assert all(Fraction(record["u"][1]) != 0 for record in basepoint["slack_records"])
    assert next(record for record in basepoint["slack_records"] if record["source_id"] == "p1-0")[
        "u"
    ] == ["0", "1"]


def test_full_core_vanishes_and_has_rank_427_at_the_csg_point() -> None:
    jacobian = _compiled()["core_Jacobian"]
    cpobc = jacobian["per_block"]["CPOBC"]
    strong_gc = jacobian["per_block"]["strong_GC"]

    assert cpobc["scalar_entry_slots"] == 3132
    assert cpobc["jacobian_nonzero_rows"] == 2870
    assert cpobc["rank"] == 381
    assert cpobc["basepoint_residual_failures"] == 0
    assert strong_gc["scalar_entry_slots"] == 1280
    assert strong_gc["jacobian_nonzero_rows"] == 1020
    assert strong_gc["rank"] == 180
    assert strong_gc["basepoint_residual_failures"] == 0
    assert jacobian["combined_nonzero_rows"] == 3890
    assert jacobian["combined_rank"] == 427
    assert jacobian["tangent_dimension"] == 49
    assert jacobian["combined_echelon_digest_sha256"] == (
        "e41c6382cba66e7d0deaaa8131bba1cd306f761a9c5f8a006008eac5dfd9ab52"
    )


def test_all_Q_commutator_gradients_lie_in_the_core_jacobian_rowspace() -> None:
    q = _compiled()["Q_commutator_Jacobian"]

    assert q["commutator_pairs"] == 6
    assert q["scalar_entry_slots"] == 24
    assert q["nonzero_gradient_rows"] == 12
    assert q["raw_rank"] == 6
    assert q["rank_after_appending_to_core"] == 427
    assert q["rank_modulo_core_rowspace"] == 0
    assert q["nonzero_rowspace_remainders"] == 0
    assert q["all_Q_gradients_in_core_rowspace"] is True
    assert q["first_order_Q_tangent_escape_exists"] is False
    assert q["gradient_stream_digest_sha256"] == (
        "328487a8d3b22b23cf4e2a045ba03643f3ecaa193e25b4cb79c239cc8135cff4"
    )
    assert _compiled()["explicit_Q_tangent_escape_certificate"] is None


def test_Q_rowspace_containment_is_independently_reduced_against_the_raw_core() -> None:
    names, core_rows, q_rows, core_basis = _raw_audit()

    assert len(names) == 476
    assert len(core_rows) == 3890
    assert len(core_basis) == 427
    assert len(q_rows) == 12
    assert all(gate._reduce(row, core_basis) == {} for row in q_rows)
    assert len(gate._extend_basis(core_basis, q_rows)) == len(core_basis)


def test_the_sixteen_global_blind_directions_are_core_and_Q_silent() -> None:
    blind = _compiled()["terminal_slack_blind_directions"]

    assert blind["count"] == 16
    assert blind["all_standard_basis_directions_in_core_tangent_kernel"] is True
    assert blind["all_Q_commutator_directional_derivatives_zero"] is True
    assert blind["core_failures"] == blind["Q_failures"] == 0
    assert all(name.startswith("u:p4-") for name in blind["coordinates"])


def test_open_conditions_hold_but_only_a_second_order_audit_is_authorised() -> None:
    payload = _compiled()
    open_conditions = payload["open_conditions_at_basepoint"]
    decision = payload["execution_decision"]

    assert open_conditions == {
        "source_determinants_checked": 131,
        "source_determinant_failures": 0,
        "N_nonzero": True,
        "nonzero_slack_coordinate_count": 24,
        "open_conditions_impose_no_linear_tangent_equations": True,
    }
    assert decision["generic_solver_authorised"] is False
    assert decision["higher_order_lifting_authorised"] is False
    assert decision["second_order_obstruction_audit_authorised"] is True
    assert payload["solver_status"] == {
        "exact_sparse_QQ_linear_algebra_runs": 1,
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
