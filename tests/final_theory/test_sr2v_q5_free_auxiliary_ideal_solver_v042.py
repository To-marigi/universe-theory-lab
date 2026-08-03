"""Fast guards for the auxiliary-ideal solver's pure-Python pieces.

None of these tests invoke Sage/Singular or touch the multi-hundred-MiB chart
ideal files; they are the preflight gate for this module, matching the bundle
module's own preflight test file.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_solver_v042 as solver

ROOT = Path(__file__).resolve().parents[2]


def _as_dict(terms: solver.GeneratorTerms, width: int) -> dict[tuple[int, ...], tuple[int, int]]:
    """Term list -> {exponent tuple: (numerator, denominator)}, for easy assertions."""

    out: dict[tuple[int, ...], tuple[int, int]] = {}
    for exponent_pairs, numerator, denominator in terms:
        exponent = [0] * width
        for index, power in exponent_pairs:
            exponent[index] = power
        out[tuple(exponent)] = (numerator, denominator)
    return out


def test_extend_terms_embeds_into_a_wider_ring_without_a_bump() -> None:
    terms = [[[[0, 2], [1, 1]], 3, 2], [[], -5, 1]]
    embedded = solver._extend_terms(terms, width=4, bump_index=None)  # noqa: SLF001
    assert embedded == {(2, 1, 0, 0): Fraction(3, 2), (0, 0, 0, 0): Fraction(-5)}


def test_extend_terms_bump_index_multiplies_by_the_auxiliary_variable() -> None:
    terms = [[[[0, 1]], 1, 1]]
    embedded = solver._extend_terms(terms, width=3, bump_index=2)  # noqa: SLF001
    assert embedded == {(1, 0, 1): Fraction(1)}


def test_merge_terms_sums_and_cancels() -> None:
    merged = solver._merge_terms(  # noqa: SLF001
        [{(0, 0): Fraction(1), (1, 0): Fraction(2)}, {(0, 0): Fraction(-1), (1, 0): Fraction(3)}]
    )
    assert merged == {(1, 0): Fraction(5)}
    assert (0, 0) not in merged, "an exact cancellation must not leave a zero entry"


def test_non_aligned_generator_terms_is_h_times_a_plus_b() -> None:
    a_terms = [[[[0, 1]], 1, 1]]  # t1 (using base index 0 in a 2-wide base)
    b_terms = [[[], 5, 1]]  # constant 5
    terms = solver._non_aligned_generator_terms(  # noqa: SLF001
        width=3, h_index=2, a_terms=a_terms, b_terms=b_terms
    )
    assert _as_dict(terms, width=3) == {(1, 0, 1): (1, 1), (0, 0, 0): (5, 1)}


def test_rabinowitsch_generator_terms_is_one_minus_z_times_localiser() -> None:
    localiser = [[[], 1, 1]]  # constant 1
    terms = solver._rabinowitsch_generator_terms(width=2, z_index=1, localiser_terms=localiser)  # noqa: SLF001
    assert _as_dict(terms, width=2) == {(0, 0): (1, 1), (0, 1): (-1, 1)}


def test_generator_terms_drop_exact_cancellations() -> None:
    a_terms = [[[[0, 1]], 3, 1], [[[0, 1]], -3, 1]]  # 3*t1 - 3*t1 cancels to zero
    b_terms = [[[], 7, 1]]
    terms = solver._non_aligned_generator_terms(  # noqa: SLF001
        width=3, h_index=2, a_terms=a_terms, b_terms=b_terms
    )
    assert _as_dict(terms, width=3) == {(0, 0, 0): (7, 1)}
    assert all(entry[1] != 0 for entry in terms)


def test_aligned_generator_terms_sums_constant_h_and_every_w() -> None:
    coefficients = {
        "constant": [[[], 1, 1]],
        "h": [[[], 2, 1]],
        "w3": [[[], 3, 1]],
        "w4": [[[], 4, 1]],
    }
    index_by_auxiliary = {"h": 2, "w3": 3, "w4": 4}
    terms = solver._aligned_generator_terms(  # noqa: SLF001
        width=5, index_by_auxiliary=index_by_auxiliary, coefficients=coefficients
    )
    assert _as_dict(terms, width=5) == {
        (0, 0, 0, 0, 0): (1, 1),  # constant
        (0, 0, 1, 0, 0): (2, 1),  # h
        (0, 0, 0, 1, 0): (3, 1),  # w3
        (0, 0, 0, 0, 1): (4, 1),  # w4
    }


@pytest.mark.parametrize(
    ("chart", "expected"),
    [("U2", "d2"), ("U3", "d3"), ("U4", "d4"), ("aligned_w2_equals_1", "f_tilde")],
)
def test_rabinowitsch_key_matches_the_execution_plan(chart: str, expected: str) -> None:
    assert solver._rabinowitsch_key(chart) == expected  # noqa: SLF001


def test_load_human_budget_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        solver.load_human_budget(tmp_path)


def _write_budget(tmp_path: Path, payload: dict[str, Any]) -> None:
    import json

    directory = tmp_path / "config"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "v0.4.2_sr2v_q5_free_auxiliary_ideal_budget.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_load_human_budget_rejects_unsupported_keys(tmp_path: Path) -> None:
    _write_budget(
        tmp_path,
        {
            "timeout_seconds_per_chart": 10,
            "total_wall_time_seconds": 100,
            "memory_limit_gib": 1,
            "extra": True,
        },
    )
    with pytest.raises(ValueError, match="unauthorised"):
        solver.load_human_budget(tmp_path)


def test_load_human_budget_rejects_timeout_exceeding_total(tmp_path: Path) -> None:
    _write_budget(
        tmp_path,
        {"timeout_seconds_per_chart": 200, "total_wall_time_seconds": 100, "memory_limit_gib": 1},
    )
    with pytest.raises(ValueError, match="cannot exceed"):
        solver.load_human_budget(tmp_path)


def test_load_human_budget_accepts_the_committed_campaign_budget() -> None:
    budget = solver.load_human_budget(ROOT)
    assert budget["timeout_seconds_per_chart"] == 3600
    assert budget["total_wall_time_seconds"] == 43200
    assert budget["memory_limit_gib"] == 8
    assert budget["timeout_seconds_per_chart"] <= budget["total_wall_time_seconds"]


def test_worker_script_is_syntactically_valid_python_after_sage_preparser_gaps() -> None:
    """Compile-check the embedded worker script.

    ``PolynomialRing``/``QQ``/``sage_eval``/``singular``/``sage`` are Sage
    globals injected by ``sage -c``, not Python builtins, so this only checks
    that the script parses -- it cannot run outside a Sage interpreter.
    """

    compile(solver._WORKER_SCRIPT, "<worker>", "exec")  # noqa: SLF001


def test_all_charts_are_exactly_the_six_from_the_execution_plan() -> None:
    assert set(solver.ALL_CHARTS) == {
        "U2",
        "U3",
        "U4",
        "aligned_w2_equals_1",
        "aligned_w3_equals_1",
        "aligned_w4_equals_1",
    }
    assert len(solver.ALL_CHARTS) == 6
