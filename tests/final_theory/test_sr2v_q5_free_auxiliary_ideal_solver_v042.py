"""Fast guards for the auxiliary-ideal solver's pure-Python pieces.

None of these tests invoke Sage/Singular or stream the committed arena chunks;
they are the preflight gate for this module, matching the bundle module's own
preflight test file. Run them before spending Sage time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_solver_v042 as solver

ROOT = Path(__file__).resolve().parents[2]


def test_duplicate_rows_are_dropped_keeping_first_appearance() -> None:
    """Repeating a generator cannot change the ideal, so duplicates are removed."""

    rows = [(1, 2), (3, 4), (1, 2), (5, 6), (3, 4)]
    assert solver._unique_preserving_order(rows) == [(1, 2), (3, 4), (5, 6)]  # noqa: SLF001


def test_unique_preserving_order_keeps_distinct_rows_untouched() -> None:
    rows = [(9, 1), (2, 2), (4, 7)]
    assert solver._unique_preserving_order(rows) == rows  # noqa: SLF001


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

    ``PolynomialRing``/``QQ``/``GF``/``singular``/``sage`` are Sage globals
    injected by ``sage -c``, not Python builtins, so this only checks that the
    script parses -- it cannot run outside a Sage interpreter.
    """

    compile(solver._WORKER_SCRIPT, "<worker>", "exec")  # noqa: SLF001


def test_worker_script_verifies_chunk_digests() -> None:
    """The worker streams chunks itself, so it must do its own fail-closed check."""

    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "uncompressed_sha256" in script
    assert "record count does not match the ledger" in script
    assert "uncompressed digest does not match the ledger" in script


def test_worker_is_tagged_so_a_timeout_can_actually_kill_it() -> None:
    """A run once survived its own timeout because the kill pattern missed it.

    ``sage -c`` shows up in the container's process table as ``sage-eval``, so
    matching on ``"sage -c"`` killed nothing and the worker kept a full core
    and 6.6 GiB for eleven minutes past the approved limit. The worker now
    carries a per-request tag in argv, which is what the kill matches on.
    """

    assert solver._WORKER_TAG  # noqa: SLF001
    assert "sage -c" not in solver._WORKER_TAG  # noqa: SLF001
    tagged = solver._tagged_worker_script("deadbeef")  # noqa: SLF001
    assert tagged.startswith(f"# {solver._WORKER_TAG}=deadbeef\n")  # noqa: SLF001
    compile(tagged, "<worker>", "exec")


def test_the_tag_rides_inside_the_script_not_as_a_trailing_argument() -> None:
    """``sage -c`` concatenates trailing argv onto the script and then fails.

    Passing the tag as its own argument produced ``IndentationError`` on the
    appended line, so the tag has to travel as a first-line comment instead.
    """

    tagged = solver._tagged_worker_script("abc123")  # noqa: SLF001
    first_line = tagged.splitlines()[0]
    assert first_line.startswith("#"), "the tag must be inert Python"
    assert "abc123" in first_line


def test_progress_records_survive_a_killed_request() -> None:
    """Stage markers go to stderr precisely so a timeout still reports progress."""

    stderr_text = (
        "some unrelated warning\n"
        '{"stage": "recipe_loaded", "chart": "U2", "elapsed": 0.1}\n'
        "not json at all\n"
        '{"stage": "chunk_verified", "chunk_index": 3, "elapsed": 42.0}\n'
        '{"no_stage_key": true}\n'
    )
    records = solver._progress_records(stderr_text)  # noqa: SLF001
    assert [record["stage"] for record in records] == ["recipe_loaded", "chunk_verified"]
    assert records[-1]["chunk_index"] == 3


def test_progress_records_tolerate_empty_output() -> None:
    assert solver._progress_records("") == []  # noqa: SLF001


def test_worker_script_streams_chunks_line_by_line() -> None:
    """Materialising a whole chunk is what exhausted the 8 GiB limit before.

    The small recipe is still read whole -- that one is a few KiB -- but the
    gzip chunks, which hold the 19.1 million arena terms, must never be.
    """

    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "for line in handle:" in script, "chunks must be streamed line by line"
    assert ".readlines()" not in script
    assert "handle.read()" not in script


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
