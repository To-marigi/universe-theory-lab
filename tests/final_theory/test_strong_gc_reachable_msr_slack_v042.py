"""Focused exact tests for the v0.4.2 955-side local slack design."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from universe_lab.final_theory.strong_gc_reachable_msr_slack_v042 import (
    VERDICT,
    _matvec,
    _sub,
    _zero_matrix,
    compile_strong_gc_reachable_msr_slack_v042,
    recover_slack_parameter,
    slack_matrix,
)

ROOT = Path(__file__).resolve().parents[2]
F = Fraction


@pytest.mark.parametrize("v", [(F(1), F(0)), (F(0), F(1)), (F(2), F(-3))])
@pytest.mark.parametrize("u", [(F(0), F(0)), (F(4), F(-1))])
def test_slack_always_annihilates_its_reachable_vector(
    v: tuple[Fraction, Fraction], u: tuple[Fraction, Fraction]
) -> None:
    assert _matvec(slack_matrix(u, v), v) == (F(0), F(0))


@pytest.mark.parametrize(
    ("v", "matrix"),
    [
        ((F(1), F(0)), ((F(0), F(3)), (F(0), F(-2)))),
        ((F(0), F(1)), ((F(5), F(0)), (F(-7), F(0)))),
        ((F(2), F(-3)), ((F(9), F(6)), (F(-12), F(-8)))),
    ],
)
def test_parameterisation_exhausts_exact_kernel_rows(
    v: tuple[Fraction, Fraction],
    matrix: tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]],
) -> None:
    u = recover_slack_parameter(matrix, v)
    assert slack_matrix(u, v) == matrix


def test_invalid_or_zero_reachable_vector_fails_closed() -> None:
    with pytest.raises(ValueError, match="nonzero"):
        recover_slack_parameter(_zero_matrix(), (F(0), F(0)))
    with pytest.raises(ValueError, match="does not annihilate"):
        recover_slack_parameter(((F(1), F(0)), (F(0), F(0))), (F(1), F(0)))


def test_zero_slack_is_exactly_the_legacy_strong_msr_slice() -> None:
    v = (F(2), F(-5))
    assert slack_matrix((F(0), F(0)), v) == _zero_matrix()
    assert _sub(slack_matrix((F(0), F(0)), v), _zero_matrix()) == _zero_matrix()


def test_static_ledger_counts_sources_and_fails_closed_on_global_reuse() -> None:
    payload = compile_strong_gc_reachable_msr_slack_v042(ROOT)
    assert payload["verdict"] == VERDICT
    assert payload["counts"]["source_causets"] == 24
    assert payload["counts"]["new_scalar_parameters"] == 48
    assert len(payload["source_slack_coordinates"]) == 24
    assert payload["assumption_ledger"]["not_assumed"] == [
        "strong operator MSR",
        "paper Eq.(108) as an operator definition",
        "the frozen Q reconstruction is a cover of this profile",
    ]
    assert payload["recursive_effects"]["eq107"]["affected_frozen_occurrences"] == 117
    assert payload["recursive_effects"]["eq108"]["affected_frozen_occurrences"] == 141
    assert payload["chart_cover_assessment"]["frozen_Q_chart_solver"] == "NOT_REUSABLE"
    assert payload["global_compiler_status"] == "NOT_COMPILED_FAIL_CLOSED"
