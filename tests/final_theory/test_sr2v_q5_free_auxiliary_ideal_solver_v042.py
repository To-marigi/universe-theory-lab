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


# -- Escalation: try the smallest generators first, since <S> subseteq J means a
# -- Groebner basis of [1] on any subset already proves the whole ideal is [1].


def test_a_cached_recipe_from_an_older_schema_is_not_reused() -> None:
    """A stale recipe must be regenerated, not handed to the worker to choke on.

    The cache key originally covered only the frozen root digest and the
    modulus, so a recipe written before a field existed was reused and the
    worker died on the missing key inside the container.
    """

    import inspect

    source = inspect.getsource(solver.write_chart_recipe_file)
    assert "recipe_schema_version" in source
    assert "RECIPE_SCHEMA_VERSION" in source


def test_recipe_schema_version_is_a_positive_integer() -> None:
    assert isinstance(solver.RECIPE_SCHEMA_VERSION, int)
    assert solver.RECIPE_SCHEMA_VERSION > 0


def test_default_escalation_sizes_are_increasing() -> None:
    """Each stage before the full-set marker must be strictly larger than the last."""

    finite_sizes = [size for size in solver.DEFAULT_ESCALATION_SIZES if size is not None]
    assert finite_sizes == sorted(finite_sizes)
    assert len(set(finite_sizes)) == len(finite_sizes)
    assert all(size > 0 for size in finite_sizes)


def test_default_escalation_sizes_end_with_a_full_set_marker() -> None:
    """``None`` means "every remaining generator" -- a chart that never reaches
    ``[1]`` on a proper subset must still get a complete result for the full
    ideal, so the marker must appear, and only once, at the very end."""

    assert solver.DEFAULT_ESCALATION_SIZES[-1] is None
    assert solver.DEFAULT_ESCALATION_SIZES.count(None) == 1


@pytest.mark.parametrize("chart", solver.NON_ALIGNED_CHARTS)
def test_required_generator_count_is_zero_on_non_aligned_charts(chart: str) -> None:
    assert solver._required_generator_count(chart) == 0  # noqa: SLF001


@pytest.mark.parametrize("chart", solver.ALIGNED_CHARTS)
def test_required_generator_count_reserves_the_three_equal_ratio_relations(chart: str) -> None:
    """The aligned charts must always keep d2, d3, and d4 pinned into every stage."""

    assert solver._required_generator_count(chart) == 3  # noqa: SLF001


def test_build_chart_recipe_accepts_an_escalation_sizes_override() -> None:
    """The recipe, not only the module default, can set the escalation plan."""

    import inspect

    signature = inspect.signature(solver.build_chart_recipe)
    assert "escalation_sizes" in signature.parameters
    assert signature.parameters["escalation_sizes"].default is None


@pytest.mark.parametrize("total_optional", [0, 1, 15, 16, 17, 255, 256, 257, 543, 10_000])
def test_escalation_stage_plan_last_stage_always_covers_every_optional_generator(
    total_optional: int,
) -> None:
    """The full set must always be attempted -- that is what makes a negative
    result on the last stage authoritative for the whole ideal."""

    plan = solver._escalation_stage_plan(solver.DEFAULT_ESCALATION_SIZES, total_optional)  # noqa: SLF001
    assert plan[-1][1] == total_optional


@pytest.mark.parametrize("total_optional", [0, 1, 15, 16, 17, 255, 256, 257, 543, 10_000])
def test_escalation_stage_plan_effective_sizes_are_nested_and_never_repeat(
    total_optional: int,
) -> None:
    """Each stage's generators are a superset of the previous stage's, and no
    two stages compute the identical subset."""

    plan = solver._escalation_stage_plan(solver.DEFAULT_ESCALATION_SIZES, total_optional)  # noqa: SLF001
    effective_sizes = [effective for _, effective in plan]
    assert effective_sizes == sorted(set(effective_sizes))


def test_escalation_stage_plan_collapses_stages_past_the_optional_count() -> None:
    """A chart with fewer optional generators than the largest configured size
    must not repeat the identical full-set Groebner call twice."""

    plan = solver._escalation_stage_plan((16, 32, 64, None), 20)  # noqa: SLF001
    assert plan == [(16, 16), (32, 20)]


def test_escalation_stage_plan_collapses_to_one_stage_when_nothing_is_optional() -> None:
    plan = solver._escalation_stage_plan(solver.DEFAULT_ESCALATION_SIZES, 0)  # noqa: SLF001
    assert plan == [(16, 0)]


def test_escalation_stage_plan_keeps_every_size_when_the_optional_count_is_huge() -> None:
    plan = solver._escalation_stage_plan(solver.DEFAULT_ESCALATION_SIZES, 10_000)  # noqa: SLF001
    assert plan == [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (None, 10_000)]


def test_worker_script_clamp_expression_matches_the_pure_python_plan_helper() -> None:
    """The embedded Sage planner and the tested pure-Python mirror must agree.

    They cannot literally share code across the container process boundary --
    the worker runs as Sage source in a separate container -- so this pins them
    to the same clamping expression, character for character, as the next best
    thing to one shared implementation.
    """

    import inspect

    source = inspect.getsource(solver._escalation_stage_plan)  # noqa: SLF001
    clamp_expression = (
        "total_optional if target_size is None else min(int(target_size), total_optional)"
    )
    assert clamp_expression in source
    assert clamp_expression in solver._WORKER_SCRIPT  # noqa: SLF001


def test_worker_script_replaces_the_single_groebner_call_with_escalation() -> None:
    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "groebner_basis()" in script
    assert "groebner_started" not in script
    assert "groebner_complete" not in script
    assert "escalation_stage_started" in script
    assert "escalation_stage_complete" in script


def test_worker_script_unions_the_required_generators_into_every_stage() -> None:
    """``required_gens`` must prefix every stage's ideal, never just some of them."""

    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert script.count("required_gens + optional_sorted[:effective_size]") == 1


def test_worker_script_takes_nested_prefixes_of_one_fixed_sorted_list() -> None:
    """Escalation stages must be nested: a later stage is a strict superset.

    ``optional_sorted`` is sorted exactly once, before the stage loop, and
    every stage slices a prefix of that same list -- so stage N's generators
    are always a subset of stage N+1's, never a differently chosen set.
    """

    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert script.count("optional_sorted = sorted(") == 1
    assert "optional_sorted[:effective_size]" in script


def test_worker_script_sorts_optional_generators_by_term_count_ascending() -> None:
    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "key=lambda polynomial: polynomial.number_of_terms()" in script


def test_worker_script_stops_at_the_first_stage_that_reaches_the_unit_ideal() -> None:
    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "if stage_is_unit_ideal:" in script
    assert "break" in script


def test_worker_script_pins_rabinowitsch_and_equal_ratio_relations_as_required() -> None:
    """``required_flags`` must mark the trailing d2/d3/d4 slots and the
    Rabinowitsch relation, never a row-derived generator sorted for escalation."""

    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "required_generator_count" in script
    assert "required_flags.append(spec_index >= required_from_index)" in script
    assert "required_flags.append(True)" in script


def test_worker_script_groebner_seconds_is_the_total_across_stages() -> None:
    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert "gb_seconds += stage_seconds" in script


def test_worker_script_records_the_escalation_provenance_fields() -> None:
    script = solver._WORKER_SCRIPT  # noqa: SLF001
    for field in (
        "escalation_sizes_configured",
        "escalation_sizes_attempted",
        "escalation_stages",
        "escalation_successful_size",
        "escalation_successful_generator_count",
    ):
        assert f'"{field}"' in script


def test_worker_script_still_stops_after_build_before_any_groebner_call() -> None:
    """``stage_only == "build"`` must return before the escalation loop runs."""

    script = solver._WORKER_SCRIPT  # noqa: SLF001
    assert 'if stage_only != "build":' in script
    build_guard_index = script.index('if stage_only != "build":')
    assert script.index("groebner_basis()") > build_guard_index
