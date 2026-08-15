"""Bounded audit artifact for the Phase-B large-N runtime primitives.

The audit exercises only the already certified exact n<=5 domain.  It records
implementation equivalence and fail-closed checks; it does not generate a new
trajectory, run a production sampler, or add scientific evidence.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import (
    downsets,
    enumerate_unlabeled_posets,
    height,
)
from universe_lab.final_theory.continuum_observables_v042 import relabel_relation
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_large_n_runtime_v042 import (
    CounterRngLimit,
    DownsetEnumerationLimit,
    draw_integer_ticket,
    height_longest_path,
    integer_ticket_weights,
    iter_downsets_limited,
    sha256_counter_bytes,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-large-n-runtime-audit-v1"
PREPARED = "2026-08-15"
MAX_N = 5
STATUS = (
    "PHASE_B_LARGE_N_RUNTIME_COMPONENT_AUDIT_COMPLETE_NON_PRODUCTION_"
    "PREFLIGHT_REQUIRED"
)
START_GATE = "PHASE_B_LABELED_SAMPLER_AND_OBSERVABLE_EQUIVALENCE_COMPONENT_AUDIT"
NEXT_GATE = "PHASE_B_LABELED_SAMPLER_AND_OBSERVABLE_EQUIVALENCE_COST_PREFLIGHT_BUDGET_APPROVAL"
RESULT_PATH = Path("results/v0.4.2_phase_b_large_n_runtime_audit.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_large_n_runtime_audit.md")
RUNTIME_PATH = Path("src/universe_lab/final_theory/phase_b_large_n_runtime_v042.py")
TEST_PATH = Path("tests/final_theory/test_v042_phase_b_large_n_runtime.py")
CAUSAL_SETS_PATH = Path("src/universe_lab/final_theory/causal_sets.py")
OBSERVABLES_PATH = Path(
    "src/universe_lab/final_theory/continuum_observables_v042.py"
)

STREAM_GOLDEN_HEX = (
    "55e22f73ca4dd43619a6f37494aa7445d664c3c769a674c10a4dd34671d4f0f8a"
    "2401bfacc6d1007958614e4934ed32626a4546325199f58c113fc31280fb1f6e2"
)


def _binding(root: Path, relative: Path) -> dict[str, Any]:
    raw = (root / relative).read_bytes()
    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode(
        "utf-8"
    )
    return {
        "path": relative.as_posix(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(canonical).hexdigest(),
        "size_bytes": len(raw),
        "strict_utf8_lf": "\r" not in text,
    }


def _bounded_equivalence_audit(
    levels: tuple[tuple[tuple[int, ...], ...], ...],
) -> dict[str, Any]:
    height_checks = 0
    height_failures: list[dict[str, Any]] = []
    downset_checks = 0
    downset_failures: list[dict[str, Any]] = []
    relabeling_checks = 0
    relabeling_failures: list[dict[str, Any]] = []
    for level in levels:
        for relation in level:
            expected_height = height(relation)
            observed_height = height_longest_path(relation)
            height_checks += 1
            if expected_height != observed_height and len(height_failures) < 3:
                height_failures.append(
                    {
                        "n": len(relation),
                        "expected": expected_height,
                        "observed": observed_height,
                    }
                )
            expected_downsets = downsets(relation)
            observed_downsets = tuple(
                iter_downsets_limited(
                    relation, max_downsets=1 << len(relation)
                )
            )
            downset_checks += 1
            if expected_downsets != observed_downsets and len(downset_failures) < 3:
                downset_failures.append(
                    {
                        "n": len(relation),
                        "expected_count": len(expected_downsets),
                        "observed": list(observed_downsets),
                    }
                )
            for permutation in itertools.permutations(range(len(relation))):
                relabeling_checks += 1
                relabeled = relabel_relation(relation, permutation)
                if height_longest_path(relabeled) != expected_height:
                    if len(relabeling_failures) < 3:
                        relabeling_failures.append(
                            {
                                "n": len(relation),
                                "permutation": list(permutation),
                            }
                        )
    return {
        "height_checks": height_checks,
        "height_failures": height_failures,
        "height_equivalence_passed": not height_failures,
        "downset_checks": downset_checks,
        "downset_failures": downset_failures,
        "downset_equivalence_passed": not downset_failures,
        "relabeling_checks": relabeling_checks,
        "relabeling_failures": relabeling_failures,
        "height_relabeling_passed": not relabeling_failures,
    }


def _fail_closed_audit(
    levels: tuple[tuple[tuple[int, ...], ...], ...],
) -> dict[str, Any]:
    antichain = levels[5][0]
    cap_failure_detected = False
    try:
        tuple(iter_downsets_limited(antichain, max_downsets=10))
    except DownsetEnumerationLimit as error:
        cap_failure_detected = error.code == "DOWNSET_ENUMERATION_LIMIT"

    float_rejected = False
    try:
        integer_ticket_weights((0.1, Fraction(1, 10)))  # type: ignore[arg-type]
    except TypeError:
        float_rejected = True

    oversized_counter_rejected = False
    try:
        sha256_counter_bytes(
            sampling_seed=0,
            trajectory_index=0,
            growth_step=0,
            ticket_index=0,
            rejection_attempt=0,
            byte_count=(1 << 20) + 1,
        )
    except CounterRngLimit:
        oversized_counter_rejected = True

    return {
        "downset_cap_failure_detected": cap_failure_detected,
        "float_weight_rejected": float_rejected,
        "oversized_counter_rejected": oversized_counter_rejected,
    }


def build_audit(root: Path) -> dict[str, Any]:
    levels = enumerate_unlabeled_posets(MAX_N)
    equivalence = _bounded_equivalence_audit(levels)
    fail_closed = _fail_closed_audit(levels)
    stream = sha256_counter_bytes(
        sampling_seed=7,
        trajectory_index=11,
        growth_step=3,
        ticket_index=5,
        rejection_attempt=0,
        byte_count=65,
    )
    ticket = draw_integer_ticket(
        37,
        sampling_seed=17,
        trajectory_index=2,
        growth_step=9,
        ticket_index=4,
    )
    checks = {
        "bounded_exact_domain_is_unchanged": [len(level) for level in levels]
        == [1, 1, 2, 5, 16, 63],
        "height_matches_exhaustive_oracle": equivalence[
            "height_equivalence_passed"
        ],
        "height_is_label_invariant": equivalence["height_relabeling_passed"],
        "downsets_match_exhaustive_oracle": equivalence[
            "downset_equivalence_passed"
        ],
        "portable_stream_golden_vector_matches": stream.hex() == STREAM_GOLDEN_HEX,
        "portable_ticket_golden_vector_matches": ticket.ticket == 29
        and ticket.rejection_attempt == 0,
        "fail_closed_boundaries_are_active": all(fail_closed.values()),
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "next_gate": NEXT_GATE,
        "scope": (
            "Deterministic runtime components only; no trajectories or "
            "production measurements."
        ),
        "bounded_domain": {
            "max_n": MAX_N,
            "unlabeled_level_counts": [len(level) for level in levels],
            "new_trajectories": 0,
            "solver_calls": 0,
        },
        "equivalence_audit": equivalence,
        "fail_closed_audit": fail_closed,
        "golden_vectors": {
            "sha256_counter_stream_hex": stream.hex(),
            "integer_ticket": ticket.ticket,
            "integer_ticket_rejection_attempt": ticket.rejection_attempt,
        },
        "checks": checks,
        "all_acceptance_checks_passed": all(checks.values()),
        "implementation_preflight_authorized": False,
        "production_sampler_available": False,
        "production_sampling_authorized": False,
        "independent_large_n_replay_available": False,
        "resource_budget_present": False,
        "source_bindings": [
            _binding(root, RUNTIME_PATH),
            _binding(root, TEST_PATH),
            _binding(root, CAUSAL_SETS_PATH),
            _binding(root, OBSERVABLES_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    equivalence = payload["equivalence_audit"]
    fail_closed = payload["fail_closed_audit"]
    return "\n".join(
        [
            "# Phase-B large-N runtime component audit",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            f"- Exact levels through n=5: `{payload['bounded_domain']['unlabeled_level_counts']}`",
            (
                f"- Height oracle checks: `{equivalence['height_checks']}`; "
                f"failures: `{len(equivalence['height_failures'])}`"
            ),
            (
                f"- Down-set oracle checks: `{equivalence['downset_checks']}`; "
                f"failures: `{len(equivalence['downset_failures'])}`"
            ),
            (
                f"- Height relabeling checks: `{equivalence['relabeling_checks']}`; "
                f"failures: `{len(equivalence['relabeling_failures'])}`"
            ),
            (
                "- Portable SHA-256 golden vector: "
                f"`{payload['golden_vectors']['sha256_counter_stream_hex']}`"
            ),
            "",
            (
                "The exact longest-path DP, capped order-ideal generator, exact "
                "ticket normalization, and portable counter stream passed the "
                "bounded audit. The test suite also verifies float rejection, "
                "rejection-cutoff behavior, and resource fail-closed boundaries."
            ),
            "",
            "## Boundary",
            "",
            (
                "No new trajectories, production sampling, approximate sampler, "
                "solver, BDG ensemble, or scientific verdict was added. The "
                "recursive down-set cap limits the number of emitted ideals but "
                "does not replace the required external wall-time, memory, disk, "
                "and process-tree supervisor."
            ),
            "",
            f"Fail-closed checks: `{fail_closed}`",
            "",
            f"Next gate: `{payload['next_gate']}`",
            "",
        ]
    )


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
    payload = build_audit(args.root)
    if not payload["all_acceptance_checks_passed"]:
        raise SystemExit("large-N runtime audit failed")
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked large-N runtime audit differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked large-N runtime report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
