from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from universe_lab.final_theory.fixed_vector_gc_strong_msr_escape_v042 import (
    RESULT_PATH,
    VERDICT,
    compile_fixed_vector_gc_strong_msr_escape_v042,
)

ROOT = Path(__file__).resolve().parents[2]


def test_exact_fixed_vector_gc_strong_msr_escape_closes_every_source_gate() -> None:
    result = compile_fixed_vector_gc_strong_msr_escape_v042(ROOT)

    assert result["verdict"] == VERDICT
    assert result["counts"] == {
        "transition_occurrences": 165,
        "transition_orbits": 131,
        "CPOBC_word_equations": 783,
        "CPOBC_inverse_forms": 712,
        "strong_MSR_constraints": 24,
        "same_endpoint_GC_path_pairs": 1529,
    }
    assert result["nonsingularity"] == {
        "checked_occurrences": 165,
        "zero_determinant_count": 0,
        "all_nonzero": True,
    }

    substitution = result["direct_substitution"]
    assert substitution["CPOBC"] == {
        "checked_equations": 783,
        "failure_count": 0,
        "all_zero": True,
    }
    assert substitution["CPOBC_inverse_forms"] == {
        "checked_equations": 712,
        "failure_count": 0,
        "all_zero": True,
    }
    assert substitution["strong_MSR"] == {
        "checked_constraints": 24,
        "failure_count": 0,
        "all_zero": True,
    }

    gc = substitution["fixed_vector_GC"]
    assert gc["checked_same_endpoint_path_pairs"] == 1529
    assert gc["all_fixed_vector_equalities_hold"]
    assert gc["fixed_vector_failure_count"] == 0
    assert not gc["all_strong_operator_equalities_hold"]
    assert gc["strong_operator_failure_count"] == 510
    assert gc["first_strong_operator_failure"] == {
        "endpoint_causet_id": "p3-002",
        "left_path_id": "lgc-path-73192a6770fa82828f12",
        "right_path_id": "lgc-path-fc1eafd06aa0360d6535",
        "operator_residual": [["0", "0"], ["0", "-2/27"]],
        "fixed_vector_residual": ["0", "0"],
        "strong_operator_zero": False,
        "fixed_vector_zero": True,
    }


def test_p2_2_perturbation_is_an_explicit_eq112_escape() -> None:
    result = compile_fixed_vector_gc_strong_msr_escape_v042(ROOT)
    escape = result["direct_substitution"]["Eq112_escape"]

    assert escape["causet_id"] == "p2-2"
    assert escape["frozen_reduction_word"][1] == "Q_2"
    assert escape["actual_G_p2_2"] == [["1/4", "0"], ["0", "2/9"]]
    assert escape["predicted_B_Q2_B_inverse"] == [["1/4", "0"], ["0", "1/9"]]
    assert escape["operator_residual"] == [["0", "0"], ["0", "1/9"]]
    assert escape["nonzero"]

    q_matrices = {
        record["source_id"]: record["matrix"]
        for record in result["occurrence_assignments"]
        if record["source_id"] in {"p1-0", "p2-0", "p3-000", "p4-0000"}
        and record["precursor_code"] == 0
    }
    assert q_matrices == {
        "p1-0": [["1/2", "0"], ["0", "1/3"]],
        "p2-0": [["1/4", "0"], ["0", "1/9"]],
        "p3-000": [["1/8", "0"], ["0", "1/27"]],
        "p4-0000": [["1/16", "0"], ["0", "1/81"]],
    }

    # The escape closes the missing provenance evidence but is deliberately
    # not a noncommutative witness: all four displayed Q matrices are diagonal.
    assert all(matrix[0][1] == "0" and matrix[1][0] == "0" for matrix in q_matrices.values())
    assert Fraction(escape["operator_residual"][1][1]) == Fraction(1, 9)


def test_checked_in_certificate_recompiles_byte_for_byte() -> None:
    expected = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    assert compile_fixed_vector_gc_strong_msr_escape_v042(ROOT) == expected
