"""Preflight the control implementations before control-only execution."""

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
from universe_lab.final_theory.phase_b_control_sampler_preflight_v042 import (
    build_preflight as build_sampler_preflight,
)
from universe_lab.final_theory.phase_b_minkowski_control_v042 import (
    compare_control_replay,
    independent_anchor_audit,
    sprinkle_4d_control,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-control-implementation-preflight-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_CONTROL_IMPLEMENTATION_PREFLIGHT_COMPLETE_NON_EVIDENTIARY"
START_GATE = "PHASE_B_CONTROL_EXECUTION_PRECONDITIONS_REVIEW"
NEXT_GATE = "PHASE_B_CONTROL_TRAINING_EXECUTION"
BUDGET_CERTIFICATE_PATH = Path(
    "results/v0.4.2_phase_b_control_measurement_budget_20260816.json"
)
SAMPLER_PREFLIGHT_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_sampler_preflight_20260816.json"
)
MINKOWSKI_MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_minkowski_control_v042.py"
)
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_implementation_preflight_20260816.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_control_implementation_preflight_2026-08-16.md"
)

FIXTURE_SIZES = (1, 4, 8, 13)
FIXTURE_SEEDS = (101, 127)


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


def _records() -> list[dict[str, Any]]:
    return [
        compare_control_replay(
            target_n,
            sampling_seed=seed,
            trajectory_index=0,
        )
        for target_n in FIXTURE_SIZES
        for seed in FIXTURE_SEEDS
    ]


def build_preflight(root: Path) -> dict[str, Any]:
    budget = build_certificate(root)
    tracked_budget = _load_json(root, BUDGET_CERTIFICATE_PATH)
    sampler = build_sampler_preflight(root)
    tracked_sampler = _load_json(root, SAMPLER_PREFLIGHT_RESULT_PATH)
    records = _records()
    anchor = independent_anchor_audit()
    relation_validity = True
    for record in records:
        control = sprinkle_4d_control(
            int(record["target_n"]),
            sampling_seed=int(record["sampling_seed"]),
            trajectory_index=int(record["trajectory_index"]),
            implementation="primary",
        )
        relation_validity &= len(control.relation) == int(record["target_n"])
    checks = {
        "budget_certificate_rebuilds_and_passes": (
            budget == tracked_budget
            and budget["all_acceptance_checks_passed"] is True
        ),
        "sampler_preflight_rebuilds_and_passes": (
            sampler == tracked_sampler
            and sampler["all_acceptance_checks_passed"] is True
        ),
        "minkowski_primary_and_replay_match": all(
            record["points_match"] and record["relation_digest_match"]
            for record in records
        ),
        "minkowski_fixed_cardinality_is_preserved": relation_validity,
        "independent_dimension_four_anchor_passes": (
            anchor["passed"] is True and anchor["candidate_evidence"] is False
        ),
        "controls_remain_non_evidentiary": all(
            record["candidate_evidence"] is False for record in records
        ),
        "no_production_or_solver_execution": True,
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
            "Bounded implementation and independent-replay preflight for the "
            "random-growth and four-dimensional Minkowski controls. No production "
            "control trajectories or candidate measurements are executed."
        ),
        "budget_certificate": {
            "path": BUDGET_CERTIFICATE_PATH.as_posix(),
            "semantic_digest_sha256": tracked_budget["semantic_digest_sha256"],
        },
        "sampler_preflight": {
            "path": SAMPLER_PREFLIGHT_RESULT_PATH.as_posix(),
            "semantic_digest_sha256": tracked_sampler["semantic_digest_sha256"],
        },
        "minkowski_control": {
            "target_dimension": 4,
            "fixture_sizes": list(FIXTURE_SIZES),
            "fixture_seeds": list(FIXTURE_SEEDS),
            "fixture_count": len(records),
            "candidate_evidence": False,
            "anchor": anchor,
            "records": records,
        },
        "acceptance_checks": checks,
        "all_acceptance_checks_passed": all(checks.values()),
        "new_control_trajectories": 0,
        "candidate_trajectories": 0,
        "solver_calls": 0,
        "control_measurement_authorized": False,
        "production_sampling_authorized": False,
        "source_bindings": [
            _binding(root, BUDGET_CERTIFICATE_PATH),
            _binding(root, SAMPLER_PREFLIGHT_RESULT_PATH),
            _binding(root, MINKOWSKI_MODULE_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    checks = payload["acceptance_checks"]
    control = payload["minkowski_control"]
    return "\n".join(
        [
            "# Phase-B control implementation preflight",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Scope",
            "",
            "The exact sampler/replay and fixed-cardinality four-dimensional",
            "Minkowski control paths were exercised on bounded fixtures. The",
            "dimension-four input is a positive-control input and is excluded from",
            "candidate evidence.",
            "",
            f"- Minkowski fixture sizes: `{control['fixture_sizes']}`",
            f"- Fixture seeds: `{control['fixture_seeds']}`",
            f"- Fixture count: `{control['fixture_count']}`",
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
            "The next gate is control-training execution under the approved",
            "control-only budget. This preflight does not freeze a spectral window",
            "or a statistical interval method and issues no scientific verdict.",
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
        raise SystemExit("control implementation preflight failed")
    if args.check:
        tracked = _load_json(args.root, RESULT_PATH)
        if tracked != payload:
            raise SystemExit("tracked control implementation preflight differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked control implementation report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
