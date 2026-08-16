"""Record a bounded control-path cost probe before full control training."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_sampler_v042 import (
    DownsetEnumerationLimit,
    sample_trajectory,
)
from universe_lab.final_theory.phase_b_minkowski_control_v042 import (
    sprinkle_4d_control,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-control-cost-preflight-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_CONTROL_COST_PREFLIGHT_COMPLETE_RESOURCE_LIMIT_OBSERVED"
START_GATE = "PHASE_B_CONTROL_TRAINING_EXECUTION"
NEXT_GATE = "PHASE_B_CONTROL_SAMPLER_SCALING_REVIEW"
BUDGET_CERTIFICATE_PATH = Path(
    "results/v0.4.2_phase_b_control_measurement_budget_20260816.json"
)
SAMPLER_MODULE_PATH = Path("src/universe_lab/final_theory/phase_b_control_sampler_v042.py")
MINKOWSKI_MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_minkowski_control_v042.py"
)
RESULT_PATH = Path("results/v0.4.2_phase_b_control_cost_preflight_20260816.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_control_cost_preflight_2026-08-16.md")


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


def _run_case(case_id: str) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    if case_id == "random_growth_control_n27":
        trajectory = sample_trajectory(
            27,
            sampling_seed=101,
            trajectory_index=0,
            profile_id="random_growth_control",
            implementation="primary",
            max_downsets=4096,
        )
        return (
            {
                "case_id": case_id,
                "status": "COMPLETED_COST_FIXTURE",
                "target_n": 27,
                "profile_id": "random_growth_control",
                "trajectory_digest": trajectory.semantic_digest,
                "relation_digest": trajectory.relation_digests[-1],
                "candidate_evidence": False,
            },
            time.perf_counter() - started,
        )
    if case_id == "minkowski_4d_control_n27":
        control = sprinkle_4d_control(
            27,
            sampling_seed=101,
            trajectory_index=0,
            implementation="primary",
        )
        return (
            {
                "case_id": case_id,
                "status": "COMPLETED_COST_FIXTURE",
                "target_n": 27,
                "target_dimension": 4,
                "relation_digest": control.relation_digest,
                "candidate_evidence": False,
            },
            time.perf_counter() - started,
        )
    if case_id == "random_growth_control_n60":
        try:
            trajectory = sample_trajectory(
                60,
                sampling_seed=101,
                trajectory_index=0,
                profile_id="random_growth_control",
                implementation="primary",
                max_downsets=4096,
            )
        except DownsetEnumerationLimit as error:
            return (
                {
                    "case_id": case_id,
                    "status": "RESOURCE_LIMIT_OPEN",
                    "target_n": 60,
                    "profile_id": "random_growth_control",
                    "reason": error.code,
                    "limit": error.limit,
                    "approximate_fallback_used": False,
                    "candidate_evidence": False,
                },
                time.perf_counter() - started,
            )
        return (
            {
                "case_id": case_id,
                "status": "COMPLETED_COST_FIXTURE",
                "target_n": 60,
                "profile_id": "random_growth_control",
                "trajectory_digest": trajectory.semantic_digest,
                "relation_digest": trajectory.relation_digests[-1],
                "candidate_evidence": False,
            },
            time.perf_counter() - started,
        )
    raise ValueError(f"unknown cost case: {case_id}")


def build_preflight(root: Path) -> dict[str, Any]:
    budget = _load_json(root, BUDGET_CERTIFICATE_PATH)
    case_ids = (
        "random_growth_control_n27",
        "minkowski_4d_control_n27",
        "random_growth_control_n60",
    )
    outcomes: list[dict[str, Any]] = []
    runtimes: list[dict[str, Any]] = []
    for case_id in case_ids:
        outcome, elapsed = _run_case(case_id)
        outcomes.append(outcome)
        runtimes.append({"case_id": case_id, "elapsed_seconds": elapsed})
    core_outcomes = [
        {key: value for key, value in outcome.items() if key != "relation_digest"}
        | ({"relation_digest": outcome["relation_digest"]} if "relation_digest" in outcome else {})
        for outcome in outcomes
    ]
    checks = {
        "budget_certificate_is_accepted": (
            budget["all_acceptance_checks_passed"] is True
            and budget["control_measurement_authorized"] is True
        ),
        "n27_random_growth_cost_fixture_completed": outcomes[0]["status"]
        == "COMPLETED_COST_FIXTURE",
        "n27_minkowski_cost_fixture_completed": outcomes[1]["status"]
        == "COMPLETED_COST_FIXTURE",
        "n60_random_growth_fails_closed_at_exact_cap": (
            outcomes[2]["status"] == "RESOURCE_LIMIT_OPEN"
            and outcomes[2]["reason"] == "DOWNSET_ENUMERATION_LIMIT"
            and outcomes[2]["limit"] == 4096
        ),
        "no_approximate_fallback_or_candidate_evidence": (
            outcomes[2]["approximate_fallback_used"] is False
            and all(outcome["candidate_evidence"] is False for outcome in outcomes)
        ),
        "no_solver_or_candidate_measurement": True,
    }
    certificate_core = {
        "schema_version": SCHEMA_VERSION,
        "budget_semantic_digest_sha256": budget["semantic_digest_sha256"],
        "case_ids": list(case_ids),
        "outcomes": core_outcomes,
        "checks": checks,
        "authorization_boundary": {
            "cost_probe_only": True,
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
            "A bounded cost probe for the two control paths. The N=60 exact "
            "negative-control cap failure is recorded as RESOURCE_LIMIT_OPEN; "
            "no approximate fallback or scientific evidence is added."
        ),
        "certificate_core": certificate_core,
        "runtime_observation": {
            "cases": runtimes,
            "total_elapsed_seconds": sum(
                item["elapsed_seconds"] for item in runtimes
            ),
        },
        "all_acceptance_checks_passed": all(checks.values()),
        "control_fixture_attempts": len(outcomes),
        "completed_control_fixtures": sum(
            outcome["status"] == "COMPLETED_COST_FIXTURE" for outcome in outcomes
        ),
        "resource_limit_open_cases": sum(
            outcome["status"] == "RESOURCE_LIMIT_OPEN" for outcome in outcomes
        ),
        "new_control_trajectories": 0,
        "candidate_trajectories": 0,
        "solver_calls": 0,
        "control_training_promoted": False,
        "production_sampling_authorized": False,
        "semantic_digest_sha256": stable_hash(certificate_core),
        "source_bindings": [
            _binding(root, BUDGET_CERTIFICATE_PATH),
            _binding(root, SAMPLER_MODULE_PATH),
            _binding(root, MINKOWSKI_MODULE_PATH),
        ],
    }
    if not payload["all_acceptance_checks_passed"]:
        raise RuntimeError("control cost preflight failed closed")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    core = payload["certificate_core"]
    observation = payload["runtime_observation"]
    return "\n".join(
        [
            "# Phase-B control cost preflight",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The N=27 random-growth and four-dimensional Minkowski control fixtures",
            "complete. The N=60 exact random-growth path reaches the versioned",
            "4096 down-set cap and returns `RESOURCE_LIMIT_OPEN`; no approximate",
            "fallback is used.",
            "",
            "| case | status | reason |",
            "|---|---|---|",
            *[
                f"| `{outcome['case_id']}` | `{outcome['status']}` | "
                f"`{outcome.get('reason', 'NONE')}` |"
                for outcome in core["outcomes"]
            ],
            "",
            "## Runtime observation",
            "",
            *[
                f"- `{item['case_id']}`: `{item['elapsed_seconds']:.6f}` s"
                for item in observation["cases"]
            ],
            f"- Total: `{observation['total_elapsed_seconds']:.6f}` s",
            "",
            "## Boundary",
            "",
            "This is a cost-only control probe, not a training result. The N=60",
            "cap failure must be addressed by an exact scaling strategy or the",
            "control route remains open; no cap increase or approximate sampler is",
            "silently applied.",
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
    if args.check:
        tracked = _load_json(args.root, RESULT_PATH)
        if tracked["certificate_core"] != payload["certificate_core"]:
            raise SystemExit("tracked control cost certificate differs")
        if tracked["semantic_digest_sha256"] != payload["semantic_digest_sha256"]:
            raise SystemExit("tracked control cost digest differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            tracked
        ):
            raise SystemExit("tracked control cost report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
