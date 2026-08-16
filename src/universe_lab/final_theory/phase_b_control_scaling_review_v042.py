"""Audit the exact Phase-B control sampler's first large-N cap boundary.

This review repeats one fixed random-control path with the primary and
independent replay implementations.  It records where the versioned exact
down-set cap is reached; it does not raise the cap, use an approximation, or
promote a trajectory to a scientific measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_sampler_v042 import (
    RANDOM_CONTROL_PROFILE,
    _primary_branches,
    _replay_branches,
    _select_branch,
    relation_digest,
    trajectory_digest,
)
from universe_lab.final_theory.phase_b_large_n_runtime_v042 import (
    DownsetEnumerationLimit,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-control-scaling-review-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_CONTROL_SAMPLER_SCALING_REVIEW_COMPLETE_RESOURCE_LIMIT_OPEN"
START_GATE = "PHASE_B_CONTROL_SAMPLER_SCALING_REVIEW"
NEXT_GATE = "PHASE_B_CONTROL_EXACT_SCALING_DESIGN"
PROBE_TARGET_N = 60
PROBE_SEED = 101
PROBE_TRAJECTORY_INDEX = 0
DOWNSET_CAP = 4096
BUDGET_CERTIFICATE_PATH = Path(
    "results/v0.4.2_phase_b_control_measurement_budget_20260816.json"
)
COST_PREFLIGHT_PATH = Path(
    "results/v0.4.2_phase_b_control_cost_preflight_20260816.json"
)
SAMPLER_MODULE_PATH = Path("src/universe_lab/final_theory/phase_b_control_sampler_v042.py")
RUNTIME_MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_large_n_runtime_v042.py"
)
RESULT_PATH = Path("results/v0.4.2_phase_b_control_scaling_review_20260816.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_control_scaling_review_2026-08-16.md")

Implementation = Literal["primary", "independent"]


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


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


def _run_probe(implementation: Implementation) -> tuple[dict[str, Any], list[str]]:
    relation: tuple[int, ...] = ()
    relation_digests = [relation_digest(relation)]
    branch_counts: list[int] = []
    cap: dict[str, Any] | None = None

    for growth_step in range(PROBE_TARGET_N):
        try:
            if implementation == "primary":
                branches = _primary_branches(
                    relation,
                    RANDOM_CONTROL_PROFILE.profile_id,
                    DOWNSET_CAP,
                )
            else:
                branches = _replay_branches(
                    relation,
                    RANDOM_CONTROL_PROFILE.profile_id,
                    DOWNSET_CAP,
                )
        except DownsetEnumerationLimit as error:
            cap = {
                "growth_step": growth_step,
                "source_n": len(relation),
                "code": error.code,
                "limit": error.limit,
                "downset_count_lower_bound": error.limit + 1,
            }
            break

        branch_counts.append(len(branches))
        branch, _ticket = _select_branch(
            branches,
            sampling_seed=PROBE_SEED,
            trajectory_index=PROBE_TRAJECTORY_INDEX,
            growth_step=growth_step,
        )
        relation = branch.target
        relation_digests.append(relation_digest(relation))

    if cap is None:
        raise RuntimeError("scaling probe unexpectedly reached its target without a cap")

    tail_start = max(0, len(branch_counts) - 8)
    result = {
        "implementation": implementation,
        "completed_n": len(relation),
        "completed_relation_digest": relation_digests[-1],
        "trajectory_digest_through_completed_n": trajectory_digest(relation_digests),
        "successful_growth_steps": len(branch_counts),
        "branch_count_trace_tail": [
            {"source_n": source_n, "exact_downset_count": branch_counts[source_n]}
            for source_n in range(tail_start, len(branch_counts))
        ],
        "last_successful_source_n": len(branch_counts) - 1,
        "last_successful_exact_downset_count": branch_counts[-1],
        "cap": cap,
        "candidate_evidence": False,
    }
    return result, relation_digests


def build_review(root: Path) -> dict[str, Any]:
    budget = _load_json(root, BUDGET_CERTIFICATE_PATH)
    cost = _load_json(root, COST_PREFLIGHT_PATH)
    primary, primary_digests = _run_probe("primary")
    replay, replay_digests = _run_probe("independent")
    cost_n60 = next(
        item
        for item in cost["certificate_core"]["outcomes"]
        if item["case_id"] == "random_growth_control_n60"
    )

    checks = {
        "budget_certificate_is_accepted": (
            budget["all_acceptance_checks_passed"] is True
            and budget["control_measurement_authorized"] is True
        ),
        "prior_cost_probe_recorded_the_same_n60_cap": (
            cost_n60["status"] == "RESOURCE_LIMIT_OPEN"
            and cost_n60["reason"] == "DOWNSET_ENUMERATION_LIMIT"
            and cost_n60["limit"] == DOWNSET_CAP
        ),
        "primary_replay_cap_boundary_matches": (
            primary["cap"] == replay["cap"]
            and primary["completed_n"] == replay["completed_n"]
        ),
        "primary_replay_trajectory_matches_through_boundary": (
            primary_digests == replay_digests
            and primary["trajectory_digest_through_completed_n"]
            == replay["trajectory_digest_through_completed_n"]
        ),
        "cap_is_reached_at_source_n38": (
            primary["cap"]["source_n"] == 38
            and primary["cap"]["growth_step"] == 38
            and primary["completed_n"] == 38
        ),
        "n37_exact_count_and_n38_lower_bound_are_recorded": (
            primary["last_successful_source_n"] == 37
            and primary["last_successful_exact_downset_count"] == 3791
            and primary["cap"]["downset_count_lower_bound"] == DOWNSET_CAP + 1
        ),
        "no_cap_increase_or_approximate_fallback": (
            primary["cap"]["limit"] == DOWNSET_CAP
            and cost_n60["approximate_fallback_used"] is False
        ),
        "no_candidate_evidence_or_solver": (
            primary["candidate_evidence"] is False
            and replay["candidate_evidence"] is False
        ),
    }
    certificate_core = {
        "schema_version": SCHEMA_VERSION,
        "budget_semantic_digest_sha256": budget["semantic_digest_sha256"],
        "cost_preflight_semantic_digest_sha256": cost["semantic_digest_sha256"],
        "probe": {
            "profile_id": RANDOM_CONTROL_PROFILE.profile_id,
            "target_n": PROBE_TARGET_N,
            "sampling_seed": PROBE_SEED,
            "trajectory_index": PROBE_TRAJECTORY_INDEX,
            "exact_downset_cap": DOWNSET_CAP,
        },
        "implementations": {
            "primary": primary,
            "independent": replay,
        },
        "checks": checks,
        "authorization_boundary": {
            "scaling_review_only": True,
            "cap_increase_applied": False,
            "approximate_fallback_used": False,
            "control_training_promoted": False,
            "candidate_trajectories": 0,
            "solver_calls": 0,
            "scientific_verdict_added": False,
            "global_verdict": "FINAL_THEORY_OPEN",
        },
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
            "A bounded exact scaling review of one fixed random-growth control "
            "path. It identifies the first down-set cap boundary without "
            "relaxing exactness or promoting measurements."
        ),
        "certificate_core": certificate_core,
        "all_acceptance_checks_passed": all(checks.values()),
        "control_fixture_attempts": 2,
        "completed_control_fixtures": 2,
        "resource_limit_open_cases": 2,
        "new_control_trajectories": 0,
        "candidate_trajectories": 0,
        "solver_calls": 0,
        "control_training_promoted": False,
        "production_sampling_authorized": False,
        "semantic_digest_sha256": stable_hash(certificate_core),
        "source_bindings": [
            _binding(root, BUDGET_CERTIFICATE_PATH),
            _binding(root, COST_PREFLIGHT_PATH),
            _binding(root, SAMPLER_MODULE_PATH),
            _binding(root, RUNTIME_MODULE_PATH),
        ],
    }
    if not payload["all_acceptance_checks_passed"]:
        raise RuntimeError("control scaling review failed closed")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    core = payload["certificate_core"]
    implementations = core["implementations"]
    primary = implementations["primary"]
    cap = primary["cap"]
    return "\n".join(
        [
            "# Phase-B control sampler scaling review",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            (
                "The fixed random-growth control path reaches the exact "
                f"down-set cap at source n=`{cap['source_n']}` while attempting "
                f"growth step `{cap['growth_step']}`. The previous source level "
                f"n=`{primary['last_successful_source_n']}` has exactly "
                f"`{primary['last_successful_exact_downset_count']}` down-sets; "
                f"the capped level has at least `{cap['downset_count_lower_bound']}`."
            ),
            "",
            "| implementation | completed n | cap source n | last exact count |",
            "|---|---:|---:|---:|",
            *[
                f"| `{name}` | `{record['completed_n']}` | "
                f"`{record['cap']['source_n']}` | "
                f"`{record['last_successful_exact_downset_count']}` |"
                for name, record in implementations.items()
            ],
            "",
            (
                "Primary and independent replay have the same cap boundary and "
                "the same trajectory digest through n=38. This separates a "
                "structural exact-enumeration boundary from a merely slow run."
            ),
            "",
            "## Boundary",
            "",
            (
                "No cap increase, approximate sampler, candidate trajectory, "
                "solver call, or scientific verdict was added."
            ),
            (
                "The control route therefore remains `RESOURCE_LIMIT_OPEN` "
                "until an exact scaling design is reviewed."
            ),
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_review(args.root)
    if args.check:
        tracked = _load_json(args.root, RESULT_PATH)
        if tracked["certificate_core"] != payload["certificate_core"]:
            raise SystemExit("tracked control scaling certificate differs")
        if tracked["semantic_digest_sha256"] != payload["semantic_digest_sha256"]:
            raise SystemExit("tracked control scaling digest differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            tracked
        ):
            raise SystemExit("tracked control scaling report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
