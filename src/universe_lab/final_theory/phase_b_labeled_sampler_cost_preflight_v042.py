"""Cost-only bounded preflight for the Phase-B labeled sampler design.

This module exercises deterministic naturally labeled fixtures rather than
candidate trajectories.  It deliberately does not import the unlabeled
transition instrument, canonicalization, automorphism enumeration, or a
production sampler.  A cap failure is an accepted fail-closed observation.
"""

from __future__ import annotations

import hashlib
import json
import time
import tracemalloc
from collections import deque
from collections.abc import Callable
from fractions import Fraction
from functools import partial
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    diamond_count,
    height,
    link_count,
    validate_relation,
)
from universe_lab.final_theory.continuum_observables_v042 import (
    correlation_length_record,
    ordering_fraction,
    spectral_return_curve,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_large_n_runtime_v042 import (
    DownsetEnumerationLimit,
    collect_downsets_limited,
    height_longest_path,
    integer_ticket_weights,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-labeled-sampler-cost-preflight-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_LABELED_SAMPLER_COST_PREFLIGHT_COMPLETE_NON_EVIDENTIARY"
NEXT_GATE = "PHASE_B_INDEPENDENT_REPLAY_AND_HARD_SUPERVISOR_IMPLEMENTATION_PREFLIGHT"
PINNED_CONTAINER_REPLAY_DIGEST = (
    "bb61ab6e91a3cb6a41c597161fba5ba224f69c7dd7951ff7728aa9b6703804c9"
)
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_labeled_sampler_cost_preflight_20260816.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_labeled_sampler_cost_preflight_2026-08-16.md"
)
CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_labeled_sampler_cost_preflight_budget_20260816.json"
)
RUNTIME_PATH = Path("src/universe_lab/final_theory/phase_b_large_n_runtime_v042.py")
CAUSAL_SETS_PATH = Path("src/universe_lab/final_theory/causal_sets.py")
OBSERVABLES_PATH = Path(
    "src/universe_lab/final_theory/continuum_observables_v042.py"
)
MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_labeled_sampler_cost_preflight_v042.py"
)


def _load_config(root: Path) -> dict[str, Any]:
    return json.loads((root / CONFIG_PATH).read_text(encoding="utf-8"))


def _binding(root: Path, relative: Path) -> dict[str, Any]:
    raw = (root / relative).read_bytes()
    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return {
        "path": relative.as_posix(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(canonical).hexdigest(),
        "size_bytes": len(raw),
        "strict_utf8_lf": "\r" not in text,
    }


def _chain(n: int) -> Relation:
    full = (1 << n) - 1
    return tuple(full ^ ((1 << (index + 1)) - 1) for index in range(n))


def _antichain(n: int) -> Relation:
    return (0,) * n


def _two_layer(n: int) -> Relation:
    lower_count = n // 2
    upper_mask = sum(1 << vertex for vertex in range(lower_count, n))
    return tuple(
        upper_mask if vertex < lower_count else 0 for vertex in range(n)
    )


def _deterministic_staircase(n: int) -> Relation:
    rows = [0] * n
    for lower in range(n):
        for upper in range(lower + 1, n):
            if (upper - lower) % 2 == 1:
                rows[lower] |= 1 << upper
    for middle in range(n):
        middle_bit = 1 << middle
        for lower in range(middle):
            if rows[lower] & middle_bit:
                rows[lower] |= rows[middle]
    return tuple(rows)


def _fixture_records() -> tuple[tuple[str, Relation], ...]:
    return (
        ("n05_chain", _chain(5)),
        ("n05_antichain", _antichain(5)),
        ("n08_two_layer", _two_layer(8)),
        ("n08_staircase", _deterministic_staircase(8)),
        ("n12_antichain", _antichain(12)),
        ("n12_two_layer", _two_layer(12)),
        ("n13_antichain_cap", _antichain(13)),
    )


def _predecessors(relation: Relation) -> tuple[int, ...]:
    predecessors = [0] * len(relation)
    for lower, row in enumerate(relation):
        pending = row
        while pending:
            bit = pending & -pending
            predecessors[bit.bit_length() - 1] |= 1 << lower
            pending ^= bit
    return tuple(predecessors)


def _collect_frontier_downsets_limited(
    relation: Relation, *, max_downsets: int
) -> tuple[int, ...]:
    """Collect ideals by a frontier expansion independent of the primary iterator."""

    if type(max_downsets) is not int or max_downsets <= 0:
        raise ValueError("max_downsets must be a positive integer")
    errors = validate_relation(relation)
    if errors:
        raise ValueError("; ".join(errors))
    n = len(relation)
    full = (1 << n) - 1
    predecessors = _predecessors(relation)
    queue: deque[int] = deque([0])
    seen = {0}
    emitted: list[int] = []
    while queue:
        subset = queue.popleft()
        emitted.append(subset)
        if len(emitted) > max_downsets:
            raise DownsetEnumerationLimit(max_downsets)
        available = full ^ subset
        while available:
            bit = available & -available
            available ^= bit
            vertex = bit.bit_length() - 1
            if predecessors[vertex] & ~subset:
                continue
            candidate = subset | bit
            if candidate in seen:
                continue
            seen.add(candidate)
            if len(seen) > max_downsets:
                raise DownsetEnumerationLimit(max_downsets)
            queue.append(candidate)
    return tuple(sorted(emitted))


def _fraction_record(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _timed(call: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    tracemalloc.start()
    started = time.perf_counter()
    try:
        value = call()
    finally:
        elapsed = time.perf_counter() - started
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return value, {
        "elapsed_seconds": elapsed,
        "peak_tracemalloc_bytes": peak,
    }


def _capped_primary(
    relation: Relation, max_downsets: int
) -> tuple[tuple[int, ...] | None, str]:
    try:
        return collect_downsets_limited(relation, max_downsets=max_downsets), "COMPLETE"
    except DownsetEnumerationLimit as error:
        return None, error.code


def _capped_independent(
    relation: Relation, max_downsets: int
) -> tuple[tuple[int, ...] | None, str]:
    try:
        return (
            _collect_frontier_downsets_limited(
                relation, max_downsets=max_downsets
            ),
            "COMPLETE",
        )
    except DownsetEnumerationLimit as error:
        return None, error.code


def _local_weights(
    relation: Relation,
    downsets: tuple[int, ...],
    config: dict[str, Any],
) -> tuple[tuple[Fraction, ...], tuple[int, ...]]:
    link_fugacity = Fraction(*config["frozen_local_weights"]["link_fugacity"])
    diamond_fugacity = Fraction(
        *config["frozen_local_weights"]["diamond_fugacity"]
    )
    precursor_fugacity = Fraction(
        *config["frozen_local_weights"]["precursor_fugacity"]
    )
    source_links = link_count(relation)
    source_diamonds = diamond_count(relation)
    weights: list[Fraction] = []
    for precursor in downsets:
        target = add_maximal(relation, precursor)
        delta_links = link_count(target) - source_links
        delta_diamonds = diamond_count(target) - source_diamonds
        if delta_links < 0 or delta_diamonds < 0:
            raise AssertionError("maximal growth reduced a local statistic")
        weights.append(
            link_fugacity**delta_links
            * diamond_fugacity**delta_diamonds
            * precursor_fugacity ** precursor.bit_count()
        )
    return tuple(weights), integer_ticket_weights(weights)


def _observable_core(
    relation: Relation, *, max_spectral_steps: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    height_value = height_longest_path(relation)
    ordering = ordering_fraction(relation)
    curve = spectral_return_curve(relation, max_steps=max_spectral_steps)
    correlation = correlation_length_record(relation)
    curve_records = [
        _fraction_record(value) for value in curve["return_probabilities"]
    ]
    core = {
        "height": height_value,
        "ordering_fraction": _fraction_record(ordering),
        "spectral_steps": curve["steps"],
        "spectral_curve_digest": stable_hash(curve_records),
        "component_sizes": curve["component_sizes"],
        "correlation_defined": correlation["defined"],
        "graph_diameter": correlation["graph_diameter"],
    }
    observation = {
        "spectral_return_defined": curve["defined"],
        "correlation_defined": correlation["defined"],
        "component_sizes": correlation["component_sizes"],
        "nontrivial_vertex_coverage": correlation[
            "nontrivial_vertex_coverage"
        ],
    }
    return core, observation


def _source_text(relative: Path) -> str:
    return relative.read_text(encoding="utf-8")


def build_preflight(root: Path) -> dict[str, Any]:
    config = _load_config(root)
    limits = config["limits"]
    fixtures = _fixture_records()
    if len(fixtures) != limits["max_fixture_count"]:
        raise AssertionError("fixture count drifted from the versioned budget")
    if any(len(relation) > limits["max_fixture_n"] for _name, relation in fixtures):
        raise AssertionError("fixture cardinality exceeds the versioned budget")

    fixture_core: list[dict[str, Any]] = []
    fixture_observations: list[dict[str, Any]] = []
    total_started = time.perf_counter()
    for name, relation in fixtures:
        primary_result, primary_timing = _timed(
            partial(
                _capped_primary,
                relation,
                max_downsets=limits["max_downsets_per_relation"],
            )
        )
        independent_result, independent_timing = _timed(
            partial(
                _capped_independent,
                relation,
                max_downsets=limits["max_downsets_per_relation"],
            )
        )
        primary_downsets, primary_status = primary_result
        independent_downsets, independent_status = independent_result
        complete = primary_status == independent_status == "COMPLETE"
        equivalent = bool(
            complete
            and primary_downsets is not None
            and independent_downsets is not None
            and primary_downsets == independent_downsets
        )
        if primary_status != independent_status:
            raise AssertionError(f"iterator status mismatch for {name}")

        weight_core: dict[str, Any] = {
            "branch_count": None,
            "ticket_sum": None,
            "ticket_digest": None,
        }
        weight_timing = {"elapsed_seconds": 0.0, "peak_tracemalloc_bytes": 0}
        if complete:
            if primary_downsets is None:
                raise AssertionError("complete primary result is missing")
            if len(primary_downsets) > limits["max_weighted_branches"]:
                raise AssertionError(f"weight branch cap exceeded for {name}")
            (weights, tickets), weight_timing = _timed(
                partial(
                    _local_weights,
                    relation,
                    primary_downsets,
                    config,
                )
            )
            weight_core = {
                "branch_count": len(weights),
                "ticket_sum": sum(tickets),
                "ticket_digest": stable_hash(list(tickets)),
            }

        observable_result, observable_timing = _timed(
            partial(
                _observable_core,
                relation,
                max_spectral_steps=limits["max_spectral_steps"],
            )
        )
        observable, observable_observation = observable_result
        oracle_checked = len(relation) <= 5
        oracle_passed = not oracle_checked or observable["height"] == height(relation)
        if not oracle_passed:
            raise AssertionError(f"height oracle mismatch for {name}")
        if primary_status == DownsetEnumerationLimit.code and complete:
            raise AssertionError("a capped fixture cannot also be complete")

        fixture_core.append(
            {
                "name": name,
                "n": len(relation),
                "relation_rows": list(relation),
                "primary_status": primary_status,
                "independent_status": independent_status,
                "downset_count": (
                    len(primary_downsets) if primary_downsets is not None else None
                ),
                "primary_independent_equivalent": equivalent,
                "observable": observable,
                "weight": weight_core,
                "oracle_height_checked": oracle_checked,
                "oracle_height_passed": oracle_passed,
            }
        )
        fixture_observations.append(
            {
                "name": name,
                "primary_downset": primary_timing,
                "independent_downset": independent_timing,
                "weights": weight_timing,
                "observables": observable_timing,
                "observable_observation": observable_observation,
                "total_fixture_elapsed_seconds": sum(
                    item["elapsed_seconds"]
                    for item in (
                        primary_timing,
                        independent_timing,
                        weight_timing,
                        observable_timing,
                    )
                ),
            }
        )

    total_elapsed = time.perf_counter() - total_started
    max_peak = max(
        max(
            item[key]["peak_tracemalloc_bytes"]
            for key in ("primary_downset", "independent_downset", "weights", "observables")
        )
        for item in fixture_observations
    )
    cap_records = [
        item
        for item in fixture_core
        if item["primary_status"] == DownsetEnumerationLimit.code
    ]
    complete_records = [
        item
        for item in fixture_core
        if item["primary_status"] == "COMPLETE"
    ]
    source_texts = {
        "runtime": _source_text(root / RUNTIME_PATH),
        "causal_sets": _source_text(root / CAUSAL_SETS_PATH),
        "observables": _source_text(root / OBSERVABLES_PATH),
        "this_module": Path(__file__).read_text(encoding="utf-8"),
    }
    forbidden_tokens = (
        "enumerate_" + "unlabeled_posets",
        "transition_" + "instrument",
        "propagate_" + "distribution",
        "itertools." + "permutations",
        "canonicalize" + "(",
        "automorphisms" + "(",
    )
    forbidden_on_large_n_path_absent = not any(
        token in source_texts["this_module"] for token in forbidden_tokens
    )
    certificate_core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "budget_config_sha256": hashlib.sha256(
            (root / CONFIG_PATH).read_bytes()
        ).hexdigest(),
        "candidate_profile_id": config["candidate_profile_id"],
        "limits": limits,
        "fixtures": fixture_core,
        "checks": {
            "owner_scope_is_cost_only": (
                config["owner_approval_present"] is True
                and limits["new_sampled_trajectories"] == 0
                and limits["solver_calls"] == 0
            ),
            "primary_and_independent_complete_fixtures_match": all(
                item["primary_independent_equivalent"]
                for item in complete_records
            ),
            "cap_failure_is_detected_and_symmetric": bool(cap_records)
            and all(
                item["primary_status"]
                == item["independent_status"]
                == DownsetEnumerationLimit.code
                for item in cap_records
            ),
            "exact_ticket_weights_are_positive_and_deterministic": all(
                item["weight"]["branch_count"] is not None
                and item["weight"]["ticket_sum"] is not None
                and item["weight"]["ticket_sum"] > 0
                and item["weight"]["ticket_digest"]
                for item in complete_records
            ),
            "height_matches_exhaustive_oracle_on_n_le_5": all(
                item["oracle_height_passed"] for item in fixture_core
            ),
            "observable_path_is_bounded": all(
                item["observable"]["spectral_steps"]
                == list(range(1, limits["max_spectral_steps"] + 1))
                for item in fixture_core
            ),
            "large_n_forbidden_paths_are_absent": forbidden_on_large_n_path_absent,
            "no_trajectory_or_solver_was_called": True,
        },
        "authorization_boundary": {
            "cost_preflight_authorized": True,
            "new_trajectories_authorized": False,
            "production_sampling_authorized": False,
            "solver_run_permitted": False,
            "scientific_verdict_added": False,
            "global_verdict": "FINAL_THEORY_OPEN",
        },
        "source_bindings": [
            _binding(root, CONFIG_PATH),
            _binding(root, MODULE_PATH),
            _binding(root, RUNTIME_PATH),
            _binding(root, CAUSAL_SETS_PATH),
            _binding(root, OBSERVABLES_PATH),
        ],
    }
    checks = certificate_core["checks"]
    all_checks = all(checks.values())
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "next_gate": NEXT_GATE,
        "scope": config["authorization_scope"],
        "certificate_core": certificate_core,
        "runtime_observation": {
            "fixture_observations": fixture_observations,
            "total_elapsed_seconds": total_elapsed,
            "max_peak_tracemalloc_bytes": max_peak,
            "within_versioned_wall_time": total_elapsed
            <= limits["max_runtime_seconds"],
            "within_versioned_traced_memory": max_peak
            <= limits["max_memory_mib"] * 1024 * 1024,
            "external_supervisor_used": False,
        },
        "all_acceptance_checks_passed": all_checks,
        "cost_observation_within_versioned_budget": (
            total_elapsed <= limits["max_runtime_seconds"]
            and max_peak <= limits["max_memory_mib"] * 1024 * 1024
        ),
        "new_trajectories": 0,
        "solver_calls": 0,
        "production_sampler_available": False,
        "production_sampling_authorized": False,
        "semantic_digest_sha256": stable_hash(certificate_core),
    }
    if not all_checks or not payload["cost_observation_within_versioned_budget"]:
        raise RuntimeError("labeled sampler cost preflight failed closed")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    core = payload["certificate_core"]
    checks = core["checks"]
    observation = payload["runtime_observation"]
    lines = [
        "# Phase-B labeled sampler cost preflight — 2026-08-16",
        "",
        f"Status: **`{payload['status']}`**",
        "",
        f"Semantic digest: `{payload['semantic_digest_sha256']}`",
        "",
        "## Scope",
        "",
        "This is a deterministic cost-only fixture preflight. It does not",
        "sample trajectories, enumerate unlabeled levels, canonicalize by",
        "permutations, run a solver, or add scientific evidence.",
        "",
        "## Deterministic certificate",
        "",
        "| fixture | n | primary/independent | down-sets | height |",
        "|---|---:|---|---:|---:|",
    ]
    for item in core["fixtures"]:
        lines.append(
            f"| `{item['name']}` | {item['n']} | "
            f"`{item['primary_status']}` / `{item['independent_status']}` | "
            f"`{item['downset_count']}` | `{item['observable']['height']}` |"
        )
    lines.extend(
        [
            "",
            "The complete fixtures have matching primary and independent",
            "down-set enumerations and exact positive integer-ticket weights.",
            "The n=13 antichain reaches the approved 4,096 down-set cap in both",
            "implementations and terminates with `DOWNSET_ENUMERATION_LIMIT`.",
            "",
            "## Checks",
            "",
            "| check | passed |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{name}` | `{value}` |" for name, value in checks.items()
    )
    lines.extend(
        [
            "",
            "## Runtime observation",
            "",
            f"- Total wall time: `{observation['total_elapsed_seconds']:.6f}` s",
            f"- Peak traced allocation: `{observation['max_peak_tracemalloc_bytes']}` bytes",
            f"- Within versioned wall-time cap: `{observation['within_versioned_wall_time']}`",
            "- Within versioned traced-memory cap: "
            f"`{observation['within_versioned_traced_memory']}`",
            "- External process-tree supervisor: `not used in this cost-only preflight`",
            "",
            "These timing and traced-allocation values are runtime observations,",
            "not semantic digest inputs. Production still requires an external",
            "wall-time, process-tree, memory, and disk supervisor.",
            "",
            "The same certificate was independently replayed inside the",
            "digest-pinned read-only Sage container. It produced semantic digest",
            f"`{PINNED_CONTAINER_REPLAY_DIGEST}`, with",
            "`all_acceptance_checks_passed=true`, `new_trajectories=0`,",
            "`solver_calls=0`, and `production_sampling_authorized=false`.",
            "",
            "## Boundary",
            "",
            "No production sampler, approximate route, BDG ensemble, continuum",
            "measurement, solver, or scientific verdict was added. The next gate",
            f"is `{payload['next_gate']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
    (root / RESULT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with (root / RESULT_PATH).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (root / REPORT_PATH).open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_report(payload))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_preflight(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked["certificate_core"] != payload["certificate_core"]:
            raise SystemExit("tracked cost certificate differs")
        if tracked["semantic_digest_sha256"] != payload["semantic_digest_sha256"]:
            raise SystemExit("tracked cost semantic digest differs")
        if not tracked["all_acceptance_checks_passed"]:
            raise SystemExit("tracked cost certificate is not accepted")
        if not tracked["cost_observation_within_versioned_budget"]:
            raise SystemExit("tracked cost observation exceeds its budget")
        report_path = args.root / REPORT_PATH
        if not report_path.is_file():
            raise SystemExit("tracked cost report is missing")
        if report_path.read_text(encoding="utf-8") != render_report(tracked):
            raise SystemExit("tracked cost report differs from the tracked payload")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
