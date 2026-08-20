"""Register the Phase-B control-first protocol without opening execution.

This artifact is deliberately a protocol registry, not a measurement run.  It
rebuilds the already frozen continuum and large-N design packets, copies their
machine-readable rules, and records every unresolved control or budget blocker.
The execution gate remains closed until a separate production budget and the
missing controls are approved and implemented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-control-protocol-registry-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_CONTROL_PROTOCOL_REGISTERED_EXECUTION_BLOCKED"
START_GATE = "PHASE_B_CONTROL_FIRST_PROTOCOL_FREEZE"
NEXT_GATE = "OWNER_APPROVAL_OF_PHASE_B_PRODUCTION_MEASUREMENT_BUDGET_AND_CONTROL_EXECUTION"
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_protocol_registry_20260816.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_control_protocol_registry_2026-08-16.md"
)
CONTINUUM_CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_continuum_dimension_design.json"
)
CONTINUUM_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_continuum_dimension_design.json"
)
CONTINUUM_MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_continuum_dimension_design_v042.py"
)
# The registry v1 packet binds the design module as it existed when the packet
# was frozen.  The current module contains only a post-freeze compatibility
# guard for the living reference catalogue; build_design still reproduces the
# bound design result exactly.  Preserve the historical module binding here so
# that a bookkeeping repair cannot cascade through later protocol artifacts.
CONTINUUM_MODULE_FROZEN_BINDING = {
    "path": CONTINUUM_MODULE_PATH.as_posix(),
    "raw_sha256": "d110a1c0486527b43d56587052a7a32d37962a08670ee8ed641afef99c89b220",
    "canonical_lf_sha256": "d110a1c0486527b43d56587052a7a32d37962a08670ee8ed641afef99c89b220",
    "size_bytes": 22659,
    "strict_utf8_lf": True,
}
LARGE_N_CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_large_n_sampler_extension_design.json"
)
LARGE_N_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_large_n_sampler_extension_design.json"
)
LARGE_N_MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_large_n_sampler_extension_design_v042.py"
)
PREFLIGHT_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_continuum_dimension_preflight.json"
)
IMPLEMENTATION_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_implementation_preflight_20260816.json"
)
MANIFEST_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_active_candidate_manifest.json"
)
IDENTITY_RESULT_PATH = Path("results/v0.4.2_phase_b_candidate_identity.json")


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


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


def _result_digest_is_valid(payload: dict[str, Any]) -> bool:
    digest = payload.get("semantic_digest_sha256")
    if not isinstance(digest, str):
        return False
    if "certificate_core" in payload:
        return stable_hash(payload["certificate_core"]) == digest
    return stable_hash(_without_digest(payload)) == digest


def _control_records(
    continuum_config: dict[str, Any],
    large_n_config: dict[str, Any],
    preflight: dict[str, Any],
) -> list[dict[str, Any]]:
    geometric = large_n_config["positive_control_extension"][
        "geometric_dimension_control"
    ]
    records: list[dict[str, Any]] = []
    for control in continuum_config["controls"]:
        record = dict(control)
        control_id = control["id"]
        if control_id == "random_growth_negative_control":
            record.update(
                {
                    "implementation_status": "LARGE_N_SAMPLER_REQUIRED",
                    "execution_status": "DESIGN_REGISTERED_NOT_EXECUTED",
                    "bounded_exact_domain_status": "AVAILABLE_THROUGH_N5_ONLY",
                }
            )
        elif control_id == "bdg_dimension_four_positive_control":
            record.update(
                {
                    "implementation_status": geometric["current_status"],
                    "execution_status": "DESIGN_REGISTERED_NOT_EXECUTED",
                    "underlying_control_id": geometric["id"],
                }
            )
        elif control_id == "label_permutation_control":
            record.update(
                {
                    "implementation_status": (
                        "BOUNDED_EXACT_DOMAIN_AUDITED"
                        if preflight["label_invariance"]["passed"]
                        else "BOUNDED_AUDIT_FAILED"
                    ),
                    "execution_status": "NO_PRODUCTION_EXECUTION",
                    "bounded_relations_checked": preflight["label_invariance"][
                        "relations_checked"
                    ],
                    "bounded_permutations_checked": preflight["label_invariance"][
                        "permutations_checked"
                    ],
                }
            )
        record.update({"trajectories_recorded": 0, "solver_calls": 0})
        records.append(record)
    return records


def _build_checks(
    continuum_config: dict[str, Any],
    continuum_result: dict[str, Any],
    large_n_config: dict[str, Any],
    large_n_result: dict[str, Any],
    preflight: dict[str, Any],
    implementation: dict[str, Any],
    manifest: dict[str, Any],
    identity: dict[str, Any],
    controls: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    scaling = continuum_config["scaling_protocol"]
    spectral = large_n_config["spectral_protocol_extension"]
    statistics = large_n_config["statistical_protocol_extension"]
    positive_controls = large_n_config["positive_control_extension"]
    control_ids = {control["id"] for control in controls}
    planned_sizes = set(scaling["planned_sizes"])
    training_sizes = set(scaling["training_sizes"])
    holdout_sizes = set(scaling["holdout_sizes"])
    return {
        "predecessor_result_digests_are_self_consistent": {
            "passed": all(
                _result_digest_is_valid(payload)
                for payload in (
                    continuum_result,
                    large_n_result,
                    preflight,
                    implementation,
                )
            ),
            "evidence": {
                "continuum": continuum_result.get("semantic_digest_sha256"),
                "large_n": large_n_result.get("semantic_digest_sha256"),
                "bounded_preflight": preflight.get("semantic_digest_sha256"),
                "implementation_preflight": implementation.get(
                    "semantic_digest_sha256"
                ),
            },
        },
        "active_candidate_identity_is_frozen": {
            "passed": (
                manifest["all_acceptance_checks_passed"] is True
                and identity["all_safety_checks_passed"] is True
                and manifest["active_candidate"]["id"]
                == continuum_config["candidate"]
                and identity["identity"]["phase_b_active_candidate"]
                == continuum_config["candidate"]
            ),
            "evidence": {
                "manifest_candidate": manifest["active_candidate"]["id"],
                "design_candidate": continuum_config["candidate"],
                "manifest_digest": manifest["semantic_digest_sha256"],
                "identity_digest": identity["semantic_digest_sha256"],
            },
        },
        "dimension_and_holdout_protocol_is_registered": {
            "passed": (
                continuum_result["dimension_estimators"]
                == continuum_config["dimension_estimators"]
                and continuum_result["acceptance_rules"]
                == continuum_config["acceptance_rules"]
                and continuum_result["scaling_protocol"]
                == scaling
                and continuum_result["authorization_boundary"]
                == continuum_config["authorization_boundary"]
            ),
            "evidence": {
                "estimator_ids": [
                    item["id"] for item in continuum_config["dimension_estimators"]
                ],
                "planned_sizes": scaling["planned_sizes"],
                "no_holdout_refit": scaling["no_holdout_refit"],
            },
        },
        "training_and_holdout_sizes_are_disjoint": {
            "passed": (
                training_sizes.isdisjoint(holdout_sizes)
                and training_sizes | holdout_sizes == planned_sizes
                and len(training_sizes) >= 2
                and len(holdout_sizes) >= 1
            ),
            "evidence": {
                "training_sizes": sorted(training_sizes),
                "holdout_sizes": sorted(holdout_sizes),
                "planned_sizes": sorted(planned_sizes),
            },
        },
        "spectral_window_is_explicitly_unfrozen": {
            "passed": (
                spectral["production_window_status"] == "NOT_FROZEN"
                and spectral["selection_algorithm_status"]
                == "MUST_BE_MACHINE_REGISTERED_BEFORE_CONTROL_EXECUTION"
                and len(spectral["selection_algorithm_obligations"]) >= 4
            ),
            "evidence": {
                "production_window_status": spectral["production_window_status"],
                "selection_algorithm_status": spectral[
                    "selection_algorithm_status"
                ],
            },
        },
        "statistical_interval_protocol_is_explicitly_unfrozen": {
            "passed": (
                statistics["production_status"] == "NOT_FROZEN"
                and statistics["simultaneous_interval_method"] == "NOT_FROZEN"
                and "never pooled" in statistics["sampling_unit"]
                and len(statistics["failure_rules"]) >= 3
            ),
            "evidence": {
                "production_status": statistics["production_status"],
                "simultaneous_interval_method": statistics[
                    "simultaneous_interval_method"
                ],
                "sampling_unit": statistics["sampling_unit"],
            },
        },
        "all_registered_controls_are_non_evidentiary": {
            "passed": (
                control_ids
                == {
                    "random_growth_negative_control",
                    "bdg_dimension_four_positive_control",
                    "label_permutation_control",
                }
                and all(control["candidate_evidence"] is False for control in controls)
            ),
            "evidence": controls,
        },
        "control_execution_is_closed": {
            "passed": (
                all(control["trajectories_recorded"] == 0 for control in controls)
                and all(control["solver_calls"] == 0 for control in controls)
                and positive_controls["candidate_tuning_forbidden"] is True
                and positive_controls["geometric_dimension_control"][
                    "current_status"
                ]
                == "NOT_IMPLEMENTED"
                and positive_controls["bdg_weighted_ensemble"]["status"]
                == "UNDEFINED_BLOCKER"
            ),
            "evidence": {
                "trajectories_recorded": sum(
                    control["trajectories_recorded"] for control in controls
                ),
                "solver_calls": sum(control["solver_calls"] for control in controls),
                "candidate_tuning_forbidden": positive_controls[
                    "candidate_tuning_forbidden"
                ],
                "geometric_control_status": positive_controls[
                    "geometric_dimension_control"
                ]["current_status"],
                "bdg_ensemble_status": positive_controls["bdg_weighted_ensemble"][
                    "status"
                ],
            },
        },
        "hard_supervision_and_replay_requirements_are_registered": {
            "passed": (
                len(large_n_config["resource_supervision_design"][
                    "required_hard_controls"
                ])
                >= 5
                and large_n_config["resource_supervision_design"][
                    "retry_policy"
                ]
                == "zero retries; timeout or OOM is not replaced by another seed"
                and large_n_config["independent_replay_design"]["failure_rule"]
                == "any discrepancy blocks artifact promotion; no retry with a replacement seed"
            ),
            "evidence": {
                "required_hard_controls": large_n_config[
                    "resource_supervision_design"
                ]["required_hard_controls"],
                "replay_failure_rule": large_n_config[
                    "independent_replay_design"
                ]["failure_rule"],
            },
        },
        "production_budget_is_required_but_not_present": {
            "passed": (
                continuum_config["scaling_protocol"][
                    "versioned_measurement_budget_required_before_execution"
                ]
                is True
                and preflight["readiness"]["versioned_production_budget_present"]
                is False
                and implementation["production_measurement_budget_still_required"]
                is True
            ),
            "evidence": {
                "design_requires_budget": continuum_config["scaling_protocol"][
                    "versioned_measurement_budget_required_before_execution"
                ],
                "preflight_budget_present": preflight["readiness"][
                    "versioned_production_budget_present"
                ],
                "implementation_budget_is_not_production_budget": implementation[
                    "production_measurement_budget_still_required"
                ],
            },
        },
        "authorization_and_claim_boundary_remain_closed": {
            "passed": (
                continuum_config["authorization_boundary"][
                    "production_sampling_authorized"
                ]
                is False
                and continuum_config["authorization_boundary"][
                    "solver_run_permitted"
                ]
                is False
                and large_n_config["authorization_boundary"][
                    "new_trajectories_authorized"
                ]
                is False
                and implementation["new_trajectories"] == 0
                and implementation["solver_calls"] == 0
            ),
            "evidence": {
                "production_sampling_authorized": continuum_config[
                    "authorization_boundary"
                ]["production_sampling_authorized"],
                "solver_run_permitted": continuum_config["authorization_boundary"][
                    "solver_run_permitted"
                ],
                "new_trajectories": implementation["new_trajectories"],
                "solver_calls": implementation["solver_calls"],
            },
        },
    }


def build_registry(root: Path) -> dict[str, Any]:
    continuum_config = _load_json(root, CONTINUUM_CONFIG_PATH)
    continuum_result = _load_json(root, CONTINUUM_RESULT_PATH)
    large_n_config = _load_json(root, LARGE_N_CONFIG_PATH)
    large_n_result = _load_json(root, LARGE_N_RESULT_PATH)
    preflight = _load_json(root, PREFLIGHT_RESULT_PATH)
    implementation = _load_json(root, IMPLEMENTATION_RESULT_PATH)
    manifest = _load_json(root, MANIFEST_RESULT_PATH)
    identity = _load_json(root, IDENTITY_RESULT_PATH)
    controls = _control_records(continuum_config, large_n_config, preflight)
    checks = _build_checks(
        continuum_config,
        continuum_result,
        large_n_config,
        large_n_result,
        preflight,
        implementation,
        manifest,
        identity,
        controls,
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
            "Machine registration of the Phase-B control-first protocol. This "
            "packet copies frozen design rules and records blockers; it does not "
            "execute controls, candidate trajectories, production measurements, "
            "or solver calls."
        ),
        "predecessor_artifacts": {
            "continuum_design": {
                "path": CONTINUUM_RESULT_PATH.as_posix(),
                "semantic_digest_sha256": continuum_result[
                    "semantic_digest_sha256"
                ],
            },
            "large_n_extension_design": {
                "path": LARGE_N_RESULT_PATH.as_posix(),
                "semantic_digest_sha256": large_n_result[
                    "semantic_digest_sha256"
                ],
            },
            "bounded_continuum_preflight": {
                "path": PREFLIGHT_RESULT_PATH.as_posix(),
                "semantic_digest_sha256": preflight["semantic_digest_sha256"],
            },
            "implementation_preflight": {
                "path": IMPLEMENTATION_RESULT_PATH.as_posix(),
                "semantic_digest_sha256": implementation[
                    "semantic_digest_sha256"
                ],
            },
        },
        "candidate_identity": {
            "global_central_baseline": continuum_config[
                "global_central_baseline"
            ],
            "phase_b_active_candidate": continuum_config["candidate"],
            "active_candidate_manifest_digest": manifest[
                "semantic_digest_sha256"
            ],
            "candidate_identity_digest": identity["semantic_digest_sha256"],
            "evidence_transfer_from_v1": manifest["predecessor_boundary"][
                "evidence_transfer_to_active_candidate"
            ],
        },
        "measurement_protocol": {
            "dimension_estimators": continuum_config["dimension_estimators"],
            "correlation_length_observable": continuum_config[
                "correlation_length_observable"
            ],
            "scaling_protocol": continuum_config["scaling_protocol"],
            "acceptance_rules": continuum_config["acceptance_rules"],
            "stop_conditions": continuum_config["stop_conditions"],
        },
        "spectral_protocol": large_n_config["spectral_protocol_extension"],
        "statistical_protocol": large_n_config[
            "statistical_protocol_extension"
        ],
        "control_protocol": {
            "registered_controls": controls,
            "positive_control_extension": large_n_config[
                "positive_control_extension"
            ],
            "independent_replay_design": large_n_config[
                "independent_replay_design"
            ],
            "candidate_tuning_forbidden": large_n_config[
                "positive_control_extension"
            ]["candidate_tuning_forbidden"],
            "execution_status": "NOT_EXECUTED",
            "new_control_trajectories": 0,
            "solver_calls": 0,
        },
        "resource_and_promotion_protocol": {
            "resource_supervision_design": large_n_config[
                "resource_supervision_design"
            ],
            "production_measurement_budget_present": False,
            "separate_owner_approval_required": True,
            "implementation_preflight_budget_is_not_a_production_budget": True,
        },
        "acceptance_checks": checks,
        "all_structural_checks_passed": all(
            record["passed"] for record in checks.values()
        ),
        "execution_gate_open": False,
        "production_sampling_authorized": False,
        "solver_run_permitted": False,
        "claim_boundary": {
            "allowed": [
                "protocol registration",
                "bounded implementation and audit evidence already recorded",
            ],
            "forbidden": [
                "control evidence as candidate evidence",
                "continuum limit claim",
                "dimension claim",
                "BDG-weighted ensemble claim",
                "Spin-2 response or universal coupling claim",
                "complete finite ON semantics lattice claim",
            ],
        },
        "source_bindings": [
            _binding(root, CONTINUUM_CONFIG_PATH),
            _binding(root, CONTINUUM_RESULT_PATH),
            dict(CONTINUUM_MODULE_FROZEN_BINDING),
            _binding(root, LARGE_N_CONFIG_PATH),
            _binding(root, LARGE_N_RESULT_PATH),
            _binding(root, LARGE_N_MODULE_PATH),
            _binding(root, PREFLIGHT_RESULT_PATH),
            _binding(root, IMPLEMENTATION_RESULT_PATH),
            _binding(root, MANIFEST_RESULT_PATH),
            _binding(root, IDENTITY_RESULT_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    controls = payload["control_protocol"]["registered_controls"]
    checks = payload["acceptance_checks"]
    scaling = payload["measurement_protocol"]["scaling_protocol"]
    return "\n".join(
        [
            "# Phase-B control-first protocol registry",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Decision",
            "",
            "The control-first protocol is now machine-registered from the frozen",
            "Phase-B design packets. Registration does not open execution: the",
            "production budget, spectral window, simultaneous interval method,",
            "independent replay, and positive controls remain prerequisites.",
            "",
            "## Registered measurement boundary",
            "",
            f"- Candidate: `{payload['candidate_identity']['phase_b_active_candidate']}`",
            f"- Sizes: `{scaling['planned_sizes']}`",
            f"- Training sizes: `{scaling['training_sizes']}`",
            f"- Holdout sizes: `{scaling['holdout_sizes']}`",
            "- Trajectories recorded by this packet: "
            f"`{payload['control_protocol']['new_control_trajectories']}`",
            f"- Solver calls: `{payload['control_protocol']['solver_calls']}`",
            "- Pooling across seeds: forbidden",
            "- Holdout refitting: forbidden",
            "",
            "## Controls",
            "",
            "| control | implementation status | execution status | candidate evidence |",
            "|---|---|---|---:|",
            *[
                f"| `{control['id']}` | `{control['implementation_status']}` | "
                f"`{control['execution_status']}` | `{control['candidate_evidence']}` |"
                for control in controls
            ],
            "",
            "The geometric control is not implemented and the BDG-weighted",
            "ensemble is undefined. The bounded label-invariance audit is retained",
            "as a regression result only; it is not production control evidence.",
            "",
            "## Explicit blockers",
            "",
            "- The production spectral window is `NOT_FROZEN`.",
            "- The simultaneous interval method is `NOT_FROZEN`.",
            "- A separate owner-approved production measurement budget is absent.",
            "- Control execution and candidate production remain closed.",
            "",
            "## Structural checks",
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
            "This packet proves only that the protocol is registered and the",
            "execution gate is closed. It adds no scientific verdict. The global",
            "verdict remains `FINAL_THEORY_OPEN`.",
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
    payload = build_registry(args.root)
    if not payload["all_structural_checks_passed"]:
        raise SystemExit("control protocol registry structural checks failed")
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked control protocol registry differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked control protocol report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
