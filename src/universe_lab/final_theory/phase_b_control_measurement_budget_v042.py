"""Validate the owner-approved Phase-B control-only measurement budget.

The budget is intentionally narrower than candidate production.  This module
only checks the budget, its provenance, and its compatibility with the frozen
control protocol.  It never starts a sampler, trajectory, solver, or control
measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-control-measurement-budget-certificate-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_CONTROL_MEASUREMENT_BUDGET_CERTIFIED_CONTROL_ONLY"
START_GATE = "OWNER_APPROVAL_OF_PHASE_B_PRODUCTION_MEASUREMENT_BUDGET_AND_CONTROL_EXECUTION"
NEXT_GATE = "PHASE_B_CONTROL_IMPLEMENTATION_AND_REPLAY_PREFLIGHT"
BUDGET_PATH = Path(
    "config/v0.4.2_phase_b_control_measurement_budget_20260816.json"
)
PROPOSAL_PATH = Path(
    "config/v0.4.2_phase_b_control_measurement_budget_proposal_20260816.json"
)
CONTINUUM_CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_continuum_dimension_design.json"
)
LARGE_N_CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_large_n_sampler_extension_design.json"
)
REGISTRY_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_protocol_registry_20260816.json"
)
IMPLEMENTATION_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_implementation_preflight_20260816.json"
)
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_measurement_budget_20260816.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_control_measurement_budget_2026-08-16.md"
)

STRUCTURAL_KEYS = (
    "authorization_scope",
    "source_design",
    "source_continuum_design",
    "basis",
    "control_scope",
    "limits",
    "required_preconditions",
    "allowed_operations",
    "forbidden_operations",
    "promotion_boundary",
    "authorization_boundary",
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


def _without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "semantic_digest_sha256"
    }


def _structural_part(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in STRUCTURAL_KEYS}


def _expected_trajectory_count(control_scope: dict[str, Any]) -> int:
    training = len(control_scope["training_sizes"]) * len(
        control_scope["training_seeds"]
    )
    holdout = len(control_scope["holdout_sizes"]) * len(
        control_scope["holdout_seeds"]
    )
    return 2 * (training + holdout) * control_scope["trajectories_per_seed_and_size"]


def _build_checks(
    budget: dict[str, Any],
    proposal: dict[str, Any],
    continuum_config: dict[str, Any],
    large_n_config: dict[str, Any],
    registry: dict[str, Any],
    implementation: dict[str, Any],
    proposal_sha256: str,
) -> dict[str, dict[str, Any]]:
    scope = budget["control_scope"]
    limits = budget["limits"]
    design_scaling = continuum_config["scaling_protocol"]
    geometric = large_n_config["positive_control_extension"][
        "geometric_dimension_control"
    ]
    expected_controls = {
        "random_growth_negative_control",
        "minkowski_4d_sprinkling_control",
        "label_permutation_control",
    }
    expected_authorized_count = _expected_trajectory_count(scope)
    return {
        "proposal_hash_matches_approved_budget": {
            "passed": budget["approved_from_proposal_sha256"] == proposal_sha256,
            "evidence": {
                "approved": budget["approved_from_proposal_sha256"],
                "computed": proposal_sha256,
            },
        },
        "approved_budget_preserves_proposal_scope": {
            "passed": _structural_part(budget) == _structural_part(proposal),
            "evidence": list(STRUCTURAL_KEYS),
        },
        "owner_approval_and_gate_are_explicit": {
            "passed": (
                budget["owner_approval_present"] is True
                and budget["authorizes_gate"]
                == "PHASE_B_CONTROL_ONLY_IMPLEMENTATION_AND_MEASUREMENT"
                and budget["owner_instruction_source"] == "current chat instruction"
            ),
            "evidence": {
                "owner_approval_present": budget["owner_approval_present"],
                "authorizes_gate": budget["authorizes_gate"],
                "owner_approved_at": budget["owner_approved_at"],
            },
        },
        "size_seed_and_trajectory_plan_matches_frozen_design": {
            "passed": (
                scope["planned_sizes"] == design_scaling["planned_sizes"]
                and scope["training_sizes"] == design_scaling["training_sizes"]
                and scope["holdout_sizes"] == design_scaling["holdout_sizes"]
                and scope["training_seeds"]
                == design_scaling["planned_training_seeds"]
                and scope["holdout_seeds"]
                == design_scaling["planned_holdout_seeds"]
                and scope["trajectories_per_seed_and_size"]
                == design_scaling["planned_trajectories_per_seed"]
            ),
            "evidence": {
                "planned_sizes": scope["planned_sizes"],
                "training_sizes": scope["training_sizes"],
                "holdout_sizes": scope["holdout_sizes"],
                "trajectories_per_seed_and_size": scope[
                    "trajectories_per_seed_and_size"
                ],
            },
        },
        "training_and_holdout_namespaces_are_disjoint": {
            "passed": (
                set(scope["training_sizes"]).isdisjoint(scope["holdout_sizes"])
                and set(scope["training_seeds"]).isdisjoint(scope["holdout_seeds"])
                and set(scope["training_sizes"]) | set(scope["holdout_sizes"])
                == set(scope["planned_sizes"])
            ),
            "evidence": {
                "training_seeds": scope["training_seeds"],
                "holdout_seeds": scope["holdout_seeds"],
            },
        },
        "control_ids_and_candidate_evidence_boundary_are_correct": {
            "passed": (
                set(scope["control_ids"]) == expected_controls
                and scope["candidate_evidence_for_controls"] is False
                and geometric["candidate_evidence"] is False
            ),
            "evidence": {
                "registered_control_ids": scope["control_ids"],
                "geometric_control_id": geometric["id"],
                "candidate_evidence_for_controls": scope[
                    "candidate_evidence_for_controls"
                ],
            },
        },
        "authorized_trajectory_count_is_exactly_derived": {
            "passed": scope["authorized_control_trajectory_count"]
            == expected_authorized_count,
            "evidence": {
                "declared": scope["authorized_control_trajectory_count"],
                "computed": expected_authorized_count,
                "formula": scope["trajectory_count_formula"],
            },
        },
        "hard_limits_are_positive_and_non_retrying": {
            "passed": (
                limits["max_n"] == 60
                and limits["max_downsets_per_relation"] == 4096
                and limits["max_weighted_branches"] == 4096
                and limits["max_total_wall_seconds"] == 1800
                and limits["max_worker_wall_seconds"] == 300
                and limits["max_memory_mib"] == 2048
                and limits["max_disk_mib"] == 1024
                and limits["max_active_workers"] == 1
                and limits["max_retries"] == 0
                and all(
                    value > 0
                    for key, value in limits.items()
                    if key not in {"max_retries", "candidate_trajectories", "solver_calls"}
                )
            ),
            "evidence": limits,
        },
        "registry_and_implementation_boundaries_remain_closed": {
            "passed": (
                stable_hash(_without_digest(registry))
                == registry["semantic_digest_sha256"]
                and registry["all_structural_checks_passed"] is True
                and registry["execution_gate_open"] is False
                and implementation["new_trajectories"] == 0
                and implementation["solver_calls"] == 0
                and implementation["production_sampling_authorized"] is False
            ),
            "evidence": {
                "registry_digest": registry["semantic_digest_sha256"],
                "execution_gate_open": registry["execution_gate_open"],
                "implementation_new_trajectories": implementation[
                    "new_trajectories"
                ],
                "implementation_solver_calls": implementation["solver_calls"],
            },
        },
        "candidate_access_and_solver_are_forbidden": {
            "passed": (
                budget["promotion_boundary"]["candidate_access_after_controls"]
                is False
                and budget["promotion_boundary"][
                    "separate_candidate_measurement_budget_required"
                ]
                is True
                and budget["authorization_boundary"][
                    "candidate_trajectories_authorized"
                ]
                is False
                and budget["authorization_boundary"]["production_sampling_authorized"]
                is False
                and budget["authorization_boundary"]["solver_run_permitted"] is False
                and budget["limits"]["candidate_trajectories"] == 0
                and budget["limits"]["solver_calls"] == 0
            ),
            "evidence": budget["authorization_boundary"],
        },
        "control_budget_is_not_a_scientific_verdict": {
            "passed": (
                budget["promotion_boundary"]["scientific_verdict_added"] is False
                and budget["promotion_boundary"]["global_verdict"]
                == "FINAL_THEORY_OPEN"
                and budget["forbidden_operations"][-1].startswith("issue a continuum")
            ),
            "evidence": budget["promotion_boundary"],
        },
    }


def build_certificate(root: Path) -> dict[str, Any]:
    budget = _load_json(root, BUDGET_PATH)
    proposal = _load_json(root, PROPOSAL_PATH)
    continuum_config = _load_json(root, CONTINUUM_CONFIG_PATH)
    large_n_config = _load_json(root, LARGE_N_CONFIG_PATH)
    registry = _load_json(root, REGISTRY_RESULT_PATH)
    implementation = _load_json(root, IMPLEMENTATION_RESULT_PATH)
    proposal_sha256 = hashlib.sha256((root / PROPOSAL_PATH).read_bytes()).hexdigest()
    checks = _build_checks(
        budget,
        proposal,
        continuum_config,
        large_n_config,
        registry,
        implementation,
        proposal_sha256,
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "next_gate": NEXT_GATE,
        "scope": (
            "Owner-approved control-only budget certificate. It authorizes the "
            "implementation and measurement of preregistered controls, but not "
            "candidate production, solver calls, or scientific promotion."
        ),
        "budget_path": BUDGET_PATH.as_posix(),
        "budget_sha256": hashlib.sha256((root / BUDGET_PATH).read_bytes()).hexdigest(),
        "proposal_path": PROPOSAL_PATH.as_posix(),
        "proposal_sha256": proposal_sha256,
        "control_scope": budget["control_scope"],
        "limits": budget["limits"],
        "authorization_boundary": budget["authorization_boundary"],
        "promotion_boundary": budget["promotion_boundary"],
        "acceptance_checks": checks,
        "all_acceptance_checks_passed": all(
            record["passed"] for record in checks.values()
        ),
        "control_measurement_authorized": True,
        "candidate_trajectories_authorized": False,
        "production_sampling_authorized": False,
        "solver_run_permitted": False,
        "new_control_trajectories_executed_by_certificate": 0,
        "solver_calls_executed_by_certificate": 0,
        "source_bindings": [
            _binding(root, BUDGET_PATH),
            _binding(root, PROPOSAL_PATH),
            _binding(root, CONTINUUM_CONFIG_PATH),
            _binding(root, LARGE_N_CONFIG_PATH),
            _binding(root, REGISTRY_RESULT_PATH),
            _binding(root, IMPLEMENTATION_RESULT_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    checks = payload["acceptance_checks"]
    scope = payload["control_scope"]
    limits = payload["limits"]
    return "\n".join(
        [
            "# Phase-B control measurement budget certificate",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Authorization",
            "",
            "This certificate records the owner-approved recommended budget for",
            "control implementation and control-only measurement. It does not",
            "authorize candidate trajectories, solver calls, or a scientific",
            "verdict. A separate candidate measurement budget remains required.",
            "",
            f"- Candidate profile: `{scope['candidate_profile_id']}`",
            f"- Sizes: `{scope['planned_sizes']}`",
            f"- Training seeds: `{scope['training_seeds']}`",
            f"- Holdout seeds: `{scope['holdout_seeds']}`",
            f"- Trajectories per seed and size: `{scope['trajectories_per_seed_and_size']}`",
            f"- Authorized control trajectories: `{scope['authorized_control_trajectory_count']}`",
            f"- Candidate trajectories: `{limits['candidate_trajectories']}`",
            f"- Solver calls: `{limits['solver_calls']}`",
            "",
            "## Hard limits",
            "",
            f"- Total wall time: `{limits['max_total_wall_seconds']}` s",
            f"- Worker wall time: `{limits['max_worker_wall_seconds']}` s",
            f"- Memory: `{limits['max_memory_mib']}` MiB",
            f"- Disk: `{limits['max_disk_mib']}` MiB",
            f"- Retries: `{limits['max_retries']}`",
            "- Timeout, OOM, disk exhaustion, or replay mismatch stops promotion.",
            "",
            "## Acceptance checks",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{name}` | `{record['passed']}` |"
                for name, record in checks.items()
            ],
            "",
            "## Boundary",
            "",
            "Controls are not candidate evidence. Training data may determine",
            "preregistered thresholds; holdout data may validate them only, with",
            "no refit. The global verdict remains `FINAL_THEORY_OPEN`.",
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
    payload = build_certificate(args.root)
    if not payload["all_acceptance_checks_passed"]:
        raise SystemExit("control measurement budget checks failed")
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked control budget certificate differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked control budget report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
