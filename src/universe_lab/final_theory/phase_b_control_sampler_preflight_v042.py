"""Bounded implementation and independent-replay preflight for Phase B.

The preflight uses deterministic fixture trajectories only.  It is a gate for
control execution and never promotes a candidate or freezes a scientific
threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_measurement_budget_v042 import (
    build_certificate,
)
from universe_lab.final_theory.phase_b_control_sampler_v042 import (
    compare_primary_and_replay,
    sample_trajectory,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-control-sampler-preflight-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_CONTROL_SAMPLER_IMPLEMENTATION_REPLAY_PREFLIGHT_COMPLETE_NON_EVIDENTIARY"
START_GATE = "PHASE_B_CONTROL_IMPLEMENTATION_AND_REPLAY_PREFLIGHT"
NEXT_GATE = "PHASE_B_CONTROL_EXECUTION_PRECONDITIONS_REVIEW"
MODULE_PATH = Path("src/universe_lab/final_theory/phase_b_control_sampler_v042.py")
BUDGET_MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_control_measurement_budget_v042.py"
)
BUDGET_CERTIFICATE_PATH = Path(
    "results/v0.4.2_phase_b_control_measurement_budget_20260816.json"
)
RESULT_PATH = Path("results/v0.4.2_phase_b_control_sampler_preflight_20260816.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_control_sampler_preflight_2026-08-16.md")

FIXTURE_SIZES = (1, 2, 3, 4, 5)
FIXTURE_SEEDS = (101, 127)
FIXTURE_TRAJECTORY_INDICES = (0, 1)
PROFILES = (
    "causal_information_v2_sparse_kraus",
    "random_growth_control",
)
FORBIDDEN_SOURCE_TOKENS = (
    "enumerate_unlabeled_posets",
    "transition_instrument",
    "propagate_distribution",
    "canonicalize(",
    "automorphisms(",
    "causet_id(",
)


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


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


def _source_forbidden_tokens_absent(root: Path) -> bool:
    source = (root / MODULE_PATH).read_text(encoding="utf-8")
    return not any(token in source for token in FORBIDDEN_SOURCE_TOKENS)


def _fixture_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for profile_id in PROFILES:
        for target_n in FIXTURE_SIZES:
            for seed in FIXTURE_SEEDS:
                for trajectory_index in FIXTURE_TRAJECTORY_INDICES:
                    records.append(
                        compare_primary_and_replay(
                            target_n,
                            sampling_seed=seed,
                            trajectory_index=trajectory_index,
                            profile_id=profile_id,  # type: ignore[arg-type]
                            max_downsets=4096,
                        )
                    )
    return records


def _determinism_audit() -> dict[str, Any]:
    first = sample_trajectory(
        5,
        sampling_seed=101,
        trajectory_index=0,
        profile_id="causal_information_v2_sparse_kraus",
        implementation="primary",
        max_downsets=4096,
    )
    second = sample_trajectory(
        5,
        sampling_seed=101,
        trajectory_index=0,
        profile_id="causal_information_v2_sparse_kraus",
        implementation="primary",
        max_downsets=4096,
    )
    return {
        "primary_repeat_equal": first == second,
        "primary_digest": first.semantic_digest,
        "repeated_digest": second.semantic_digest,
    }


def _cap_audit() -> dict[str, Any]:
    from universe_lab.final_theory.phase_b_control_sampler_v042 import (
        DownsetEnumerationLimit,
        _primary_branches,
        _replay_branches,
    )

    antichain = (0,) * 13
    primary_failed_closed = False
    replay_failed_closed = False
    try:
        _primary_branches(antichain, "random_growth_control", 4096)
    except DownsetEnumerationLimit:
        primary_failed_closed = True
    try:
        _replay_branches(antichain, "random_growth_control", 4096)
    except DownsetEnumerationLimit:
        replay_failed_closed = True
    return {
        "primary_cap_failed_closed": primary_failed_closed,
        "replay_cap_failed_closed": replay_failed_closed,
    }


def build_preflight(root: Path) -> dict[str, Any]:
    budget = build_certificate(root)
    tracked_budget = _load_json(root, BUDGET_CERTIFICATE_PATH)
    records = _fixture_records()
    determinism = _determinism_audit()
    cap_audit = _cap_audit()
    checks = {
        "budget_certificate_rebuilds_and_passes": (
            budget == tracked_budget
            and budget["all_acceptance_checks_passed"] is True
            and budget["control_measurement_authorized"] is True
        ),
        "fixture_scope_is_bounded": (
            max(FIXTURE_SIZES) <= 5
            and len(records)
            == len(PROFILES)
            * len(FIXTURE_SIZES)
            * len(FIXTURE_SEEDS)
            * len(FIXTURE_TRAJECTORY_INDICES)
        ),
        "primary_and_independent_replay_match": all(
            item["all_branch_checks_passed"]
            and item["trajectory_digests_match"]
            for item in records
        ),
        "repeated_primary_fixture_is_deterministic": determinism[
            "primary_repeat_equal"
        ],
        "downset_caps_fail_closed_in_both_paths": all(cap_audit.values()),
        "large_n_forbidden_paths_are_absent": _source_forbidden_tokens_absent(root),
        "no_scientific_evidence_or_candidate_access": all(
            item["scientific_evidence"] is False for item in records
        ),
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
            "Deterministic n<=5 implementation and independent-replay fixtures "
            "for both candidate and negative-control sampler profiles. No control "
            "production trajectory or scientific threshold is promoted."
        ),
        "budget_certificate": {
            "path": BUDGET_CERTIFICATE_PATH.as_posix(),
            "semantic_digest_sha256": tracked_budget["semantic_digest_sha256"],
        },
        "fixture_plan": {
            "sizes": list(FIXTURE_SIZES),
            "seeds": list(FIXTURE_SEEDS),
            "trajectory_indices": list(FIXTURE_TRAJECTORY_INDICES),
            "profiles": list(PROFILES),
            "fixture_count": len(records),
        },
        "fixture_records": records,
        "determinism_audit": determinism,
        "cap_audit": cap_audit,
        "acceptance_checks": checks,
        "all_acceptance_checks_passed": all(checks.values()),
        "fixture_trajectories": len(records),
        "new_control_trajectories": 0,
        "candidate_trajectories": 0,
        "solver_calls": 0,
        "control_measurement_authorized": False,
        "production_sampling_authorized": False,
        "source_bindings": [
            _binding(root, BUDGET_CERTIFICATE_PATH),
            _binding(root, BUDGET_MODULE_PATH),
            _binding(root, MODULE_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    checks = payload["acceptance_checks"]
    plan = payload["fixture_plan"]
    return "\n".join(
        [
            "# Phase-B control sampler implementation/replay preflight",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Scope",
            "",
            "This certificate compares the primary and independent sampler paths",
            "on deterministic n<=5 fixtures for the candidate and negative-control",
            "profiles. It is not a production measurement and adds no candidate",
            "or control scientific evidence.",
            "",
            f"- Fixture sizes: `{plan['sizes']}`",
            f"- Fixture seeds: `{plan['seeds']}`",
            f"- Fixture count: `{plan['fixture_count']}`",
            "- New control trajectories: `0`",
            "- Candidate trajectories: `0`",
            "- Solver calls: `0`",
            "",
            "## Acceptance checks",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{name}` | `{passed}` |"
                for name, passed in checks.items()
            ],
            "",
            "## Boundary",
            "",
            "The next step is a precondition review before control-only execution.",
            "Any mismatch, cap failure, or hard-supervisor failure blocks promotion",
            "with no replacement seed and no approximate fallback.",
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
    payload = build_preflight(args.root)
    if not payload["all_acceptance_checks_passed"]:
        raise SystemExit("control sampler preflight failed")
    if args.check:
        tracked = _load_json(args.root, RESULT_PATH)
        if tracked != payload:
            raise SystemExit("tracked control sampler preflight differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked control sampler report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
