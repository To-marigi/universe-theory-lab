"""Fast guards for the auxiliary-ideal solver's pure-Python pieces.

None of these tests invoke Sage/Singular or touch the multi-hundred-MiB chart
ideal files; they are the preflight gate for this module, matching the bundle
module's own preflight test file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_solver_v042 as solver

ROOT = Path(__file__).resolve().parents[2]


def test_empty_polynomial_renders_as_zero() -> None:
    assert solver.sage_polynomial_string([], ["t1", "t2"]) == "0"


def test_signs_render_without_a_double_operator() -> None:
    terms = [[[[0, 2], [1, 1]], 3, 2], [[], -5, 1]]
    rendered = solver.sage_polynomial_string(terms, ["t1", "t2"])
    assert rendered == "(3/2)*t1^2*t2-5"
    assert "+-" not in rendered


def test_leading_negative_term_has_no_stray_plus() -> None:
    terms = [[[], -5, 1], [[[0, 1]], 1, 1]]
    rendered = solver.sage_polynomial_string(terms, ["t1", "t2"])
    assert rendered == "-5+1*t1"
    assert not rendered.startswith("+")


def test_exponent_one_is_not_written_with_a_caret() -> None:
    rendered = solver.sage_polynomial_string([[[[0, 1]], 1, 1]], ["t1"])
    assert rendered == "1*t1"
    assert "^" not in rendered


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
