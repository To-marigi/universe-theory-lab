"""Exact and independent checks for the SR2-V baseline observability audit."""

from __future__ import annotations

import hashlib
import itertools
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

from universe_lab.final_theory import weak_d2_observability_v042 as audit

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_baseline_observability_artifact_rebuilds_exactly() -> None:
    expected = audit.build_payload(ROOT)
    frozen = _load(audit.RESULT_PATH)
    assert frozen == expected
    assert frozen["passed"] is True
    assert frozen["verdict"] == audit.VERDICT
    assert frozen["search_terminal"] == audit.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == audit.semantic_digest(frozen)
    for relative, digest in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_exact_reachable_and_residual_visibility_counts() -> None:
    result = audit.build_payload(ROOT)
    reachable = result["reachable_inventory"]["summary"]
    assert reachable["path_count"] == 407
    assert reachable["endpoint_count"] == 87
    assert reachable["stage_counts"] == {"1": 1, "2": 2, "3": 5, "4": 16, "5": 63}
    assert reachable["all_same_endpoint_paths_give_same_state"] is True
    assert reachable["all_states_nonzero"] is True
    assert reachable["reachable_span_rank"] == 1

    residuals = result["residual_visibility"]
    gc = residuals["fixed_vector_GC"]
    assert gc["checked_path_pairs"] == 1529
    assert gc["operator_nonzero_residual_count"] == 986
    assert gc["fixed_state_nonzero_action_count"] == 0
    msr = residuals["reachable_state_MSR"]
    assert msr["checked_source_residuals"] == 24
    assert msr["operator_nonzero_residual_count"] == 24
    assert msr["source_state_nonzero_action_count"] == 0


def test_six_nonzero_commutators_are_invisible_on_every_declared_domain() -> None:
    result = audit.build_payload(ROOT)
    visibility = result["commutator_visibility"]
    assert visibility["all_six_operator_commutators_nonzero"] is True
    assert visibility["reachable_visible_on_any_compiled_cylinder_state"] is False
    assert visibility["all_six_annihilate_full_reachable_span"] is True
    assert len(visibility["records"]) == 6
    for record in visibility["records"]:
        assert record["operator_nonzero"] is True
        assert record["annihilates_full_reachable_span"] is True
        assert all(domain["nonzero_action_count"] == 0 for domain in record["domains"].values())


def test_audit_is_independent_of_the_original_witness_compiler() -> None:
    source = (
        ROOT / "src/universe_lab/final_theory/weak_d2_observability_v042.py"
    ).read_text(encoding="utf-8")
    assert "from universe_lab.final_theory import weak_d2_v04" not in source
    assert "from universe_lab.final_theory.weak_d2_v04" not in source
    assert "fractions import Fraction" in source


def test_semantic_tamper_of_frozen_Q_is_rejected(tmp_path: Path) -> None:
    for relative in (audit.WEAK_RESULT_PATH, audit.OPERATOR_GC_PATH, audit.CPOBC_PATH):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    weak_path = tmp_path / audit.WEAK_RESULT_PATH
    weak = json.loads(weak_path.read_text(encoding="utf-8"))
    weak["Q_inventory"][0]["matrix"][0][1] = "3"
    weak_path.write_text(json.dumps(weak), encoding="utf-8", newline="\n")
    with pytest.raises(AssertionError, match="Q reconstruction"):
        audit.build_payload(tmp_path)


def _oracle_transition(stage: int, source_rows: list[int], precursor: int) -> sp.Matrix:
    width = precursor.bit_count()
    maximal = sum(
        1
        for vertex, upper_vertices in enumerate(source_rows)
        if precursor & (1 << vertex) and not upper_vertices & precursor
    )
    probability = sp.Rational(2 ** (width - maximal), 2**stage)
    upper_right = sp.Rational(4, 2**stage) if precursor == 0 else sp.Rational(0)
    return sp.Matrix([[probability, upper_right], [0, 1]])


def _oracle_q(stage: int) -> sp.Matrix:
    return _oracle_transition(stage, [0] * stage, 0)


def test_independent_sympy_oracle_rebuilds_rank_and_commutator_actions() -> None:
    operator_gc = _load(audit.OPERATOR_GC_PATH)
    omega = sp.Matrix([1, 0])
    endpoint_states: dict[str, sp.Matrix] = {}
    path_count = 0
    for stage_paths in operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = sp.eye(2)
            for transition in path["transitions"]:
                product = _oracle_transition(
                    int(transition["stage"]),
                    [int(row) for row in transition["source_relation_rows"]],
                    int(transition["precursor_code"]),
                ) * product
            state = product * omega
            endpoint = str(path["endpoint_causet_id"])
            assert endpoint_states.setdefault(endpoint, state) == state
            path_count += 1

    assert path_count == 407
    assert len(endpoint_states) == 87
    state_matrix = sp.Matrix.hstack(*endpoint_states.values())
    assert state_matrix.rank() == 1
    assert all(state != sp.zeros(2, 1) for state in endpoint_states.values())

    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        left = _oracle_q(left_stage)
        right = _oracle_q(right_stage)
        commutator = left * right - right * left
        assert commutator != sp.zeros(2)
        assert all(commutator * state == sp.zeros(2, 1) for state in endpoint_states.values())
