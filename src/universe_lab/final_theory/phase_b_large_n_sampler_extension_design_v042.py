"""Freeze the Phase-B large-N sampler extension design without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.dynamics_v02 import CANDIDATE_PROFILE
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-large-n-sampler-extension-design-v1"
PREPARED = "2026-08-15"
STATUS = (
    "PHASE_B_LARGE_N_SAMPLER_EXTENSION_DESIGN_FROZEN_"
    "IMPLEMENTATION_PREFLIGHT_BUDGET_REQUIRED"
)
START_GATE = "PHASE_B_CONTINUUM_DIMENSION_LARGE_N_SAMPLER_EXTENSION_DESIGN"
NEXT_GATE = (
    "PHASE_B_LABELED_SAMPLER_AND_OBSERVABLE_EQUIVALENCE_COST_PREFLIGHT_"
    "BUDGET_APPROVAL"
)
RESULT_PATH = Path("results/v0.4.2_phase_b_large_n_sampler_extension_design.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_large_n_sampler_extension_design.md")
CONFIG_PATH = Path("config/v0.4.2_phase_b_large_n_sampler_extension_design.json")
PREFLIGHT_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_continuum_dimension_preflight.json"
)
CONTINUUM_DESIGN_RESULT_PATH = Path(
    "results/v0.4.2_phase_b_continuum_dimension_design.json"
)
CAPABILITIES_PATH = Path(
    "config/v0.4.2_phase_b_continuum_dimension_capabilities.json"
)
DYNAMICS_PATH = Path("src/universe_lab/final_theory/dynamics_v02.py")
CAUSAL_SETS_PATH = Path("src/universe_lab/final_theory/causal_sets.py")
SAMPLER_PREFLIGHT_PATH = Path(
    "src/universe_lab/final_theory/phase_b_sampler_preflight_v042.py"
)
V2_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v2/model_spec.json")
BDG_SPEC_PATH = Path("Final-Theory-Program/models/bdg_control/model_spec.json")
MISSION_PATH = Path("MISSION.md")
HANDOFF_PATH = Path("HANDOFF.md")


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


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


def _profile_weight_record() -> dict[str, list[int]]:
    parameters = CANDIDATE_PROFILE.parameters
    return {
        "link_fugacity": [
            parameters["link_fugacity"]["numerator"],
            parameters["link_fugacity"]["denominator"],
        ],
        "diamond_fugacity": [
            parameters["diamond_fugacity"]["numerator"],
            parameters["diamond_fugacity"]["denominator"],
        ],
        "precursor_fugacity": [
            parameters["precursor_fugacity"]["numerator"],
            parameters["precursor_fugacity"]["denominator"],
        ],
    }


def build_design(root: Path) -> dict[str, Any]:
    config = _load_json(root, CONFIG_PATH)
    preflight = _load_json(root, PREFLIGHT_RESULT_PATH)
    continuum_design = _load_json(root, CONTINUUM_DESIGN_RESULT_PATH)
    capabilities = _load_json(root, CAPABILITIES_PATH)
    v2_spec = _load_json(root, V2_SPEC_PATH)
    bdg_spec = _load_json(root, BDG_SPEC_PATH)
    dynamics_source = (root / DYNAMICS_PATH).read_text(encoding="utf-8")
    causal_sets_source = (root / CAUSAL_SETS_PATH).read_text(encoding="utf-8")
    frozen_weights = _profile_weight_record()
    required_blockers = set(preflight["readiness"]["blocking_requirements"])
    blocker_mapping = {
        "large-N candidate and negative-control sampler": [
            "primary_exact_labeled_sampler",
            "large_n_observable_extension",
            "approximate_weighted_ideal_route",
        ],
        "fixed production spectral plateau window": [
            "spectral_protocol_extension"
        ],
        "executable BDG dimension-four ensemble": [
            "positive_control_extension"
        ],
        "independent replay implementation": ["independent_replay_design"],
        "hard wall-time and memory supervision": [
            "resource_supervision_design"
        ],
        "versioned production measurement budget": [
            "resource_supervision_design",
            "bounded_implementation_preflight",
        ],
    }
    checks = {
        "predecessor_preflight_is_complete_but_not_production_validated": {
            "passed": (
                preflight["all_preflight_checks_passed"] is True
                and preflight["readiness"][
                    "production_measurement_pipeline_validated"
                ]
                is False
                and preflight["production_sampling_authorized"] is False
            ),
            "evidence": preflight["semantic_digest_sha256"],
        },
        "frozen_candidate_weights_are_unchanged": {
            "passed": (
                config["candidate_profile_id"] == CANDIDATE_PROFILE.profile_id
                and v2_spec["model_id"] == CANDIDATE_PROFILE.profile_id
                and {
                    key: config["frozen_local_weights"][key]
                    for key in frozen_weights
                }
                == frozen_weights
                and Fraction(*frozen_weights["link_fugacity"]) == Fraction(2, 3)
                and Fraction(*frozen_weights["diamond_fugacity"])
                == Fraction(3, 2)
                and Fraction(*frozen_weights["precursor_fugacity"])
                == Fraction(4, 5)
            ),
            "evidence": frozen_weights,
        },
        "current_exact_kernel_bottleneck_is_recorded": {
            "passed": (
                "levels = enumerate_unlabeled_posets(len(relation) + 1)"
                in dynamics_source
                and "for order in itertools.permutations(range(len(relation)))"
                in causal_sets_source
                and "for subset in range(1 << len(relation))"
                in causal_sets_source
                and capabilities["candidate_profile"][
                    "production_sampler_available"
                ]
                is False
            ),
            "evidence": {
                "current_exact_max_n": capabilities["candidate_profile"][
                    "exact_enumeration_verified_max_n"
                ],
                "production_sampler_available": False,
            },
        },
        "labeled_quotient_route_preserves_frozen_semantics_by_design": {
            "passed": (
                "orbit_size*w(P)"
                in config["primary_exact_labeled_sampler"][
                    "unlabeled_quotient_argument"
                ]
                and config["primary_exact_labeled_sampler"][
                    "selection_arithmetic"
                ]
                == "integer ticket over exact rational weights"
                and config["primary_exact_labeled_sampler"]["branch_order"]
                == "ascending natural-label precursor bitmask"
                and config["primary_exact_labeled_sampler"]["portable_rng"][
                    "status"
                ]
                == "FROZEN_DESIGN_NOT_IMPLEMENTED"
                and "cutoff=R-(R mod M)"
                in config["primary_exact_labeled_sampler"]["portable_rng"][
                    "unbiased_ticket_rule"
                ]
                and config["primary_exact_labeled_sampler"]["overflow_behavior"]
                == "fail closed with DOWNSET_ENUMERATION_LIMIT; no approximate fallback"
            ),
            "evidence": config["primary_exact_labeled_sampler"],
        },
        "hidden_exponential_observable_path_is_recorded_and_replaced_by_design": {
            "passed": (
                "def height(relation: Relation) -> int:" in causal_sets_source
                and causal_sets_source.count("for subset in range(1 << n)") >= 2
                and "longest-path dynamic program"
                in config["large_n_observable_extension"]["height_replacement"]
                and config["large_n_observable_extension"][
                    "height_target_complexity"
                ]
                == "O(n^2) on relation bit rows"
                and "causet_id factorial canonicalization"
                in config["large_n_observable_extension"][
                    "forbidden_on_large_n_path"
                ]
            ),
            "evidence": config["large_n_observable_extension"],
        },
        "approximate_route_cannot_silently_replace_exact_sampling": {
            "passed": (
                config["approximate_weighted_ideal_route"]["status"]
                == "UNAUTHORIZED_RESEARCH_OPTION"
                and config["authorization_boundary"][
                    "approximate_sampler_authorized"
                ]
                is False
            ),
            "evidence": config["approximate_weighted_ideal_route"],
        },
        "every_preflight_blocker_has_a_design_owner": {
            "passed": set(blocker_mapping) == required_blockers,
            "evidence": blocker_mapping,
        },
        "independent_replay_and_control_leakage_are_fail_closed": {
            "passed": (
                "no calls to the primary generator"
                in config["independent_replay_design"][
                    "second_large_n_implementation"
                ]
                and config["independent_replay_design"]["failure_rule"]
                == "any discrepancy blocks artifact promotion; no retry with a replacement seed"
                and config["positive_control_extension"][
                    "candidate_tuning_forbidden"
                ]
                is True
                and config["positive_control_extension"][
                    "geometric_dimension_control"
                ]["id"]
                == "minkowski_4d_sprinkling_control"
                and config["positive_control_extension"][
                    "bdg_action_evaluation_control"
                ]["does_not_define_a_bdg_weighted_sampling_ensemble"]
                is True
                and config["positive_control_extension"][
                    "bdg_weighted_ensemble"
                ]["status"]
                == "UNDEFINED_BLOCKER"
                and bdg_spec["status"] == "SCHEMA_ONLY_IN_V0.2"
                and config["spectral_protocol_extension"][
                    "production_window_status"
                ]
                == "NOT_FROZEN"
            ),
            "evidence": {
                "replay": config["independent_replay_design"],
                "positive_control": config["positive_control_extension"],
            },
        },
        "production_statistics_and_claims_remain_unfrozen_and_bounded": {
            "passed": (
                config["statistical_protocol_extension"]["production_status"]
                == "NOT_FROZEN"
                and "never pooled"
                in config["statistical_protocol_extension"]["sampling_unit"]
                and config["statistical_protocol_extension"][
                    "simultaneous_interval_method"
                ]
                == "NOT_FROZEN"
                and "continuum limit established"
                in config["claim_boundary"]["forbidden_claims"]
                and "general relativity emerged"
                in config["claim_boundary"]["forbidden_claims"]
            ),
            "evidence": {
                "statistics": config["statistical_protocol_extension"],
                "claim_boundary": config["claim_boundary"],
            },
        },
        "implementation_requires_a_new_human_owned_budget": {
            "passed": (
                config["resource_supervision_design"][
                    "default_budget_forbidden"
                ]
                is True
                and config["bounded_implementation_preflight"][
                    "resource_budget_present"
                ]
                is False
                and config["authorization_boundary"][
                    "implementation_preflight_authorized"
                ]
                is False
            ),
            "evidence": config["resource_supervision_design"],
        },
        "no_sampling_solver_or_scientific_authorization_is_added": {
            "passed": (
                config["authorization_boundary"]["new_trajectories_authorized"]
                is False
                and config["authorization_boundary"][
                    "production_sampling_authorized"
                ]
                is False
                and config["authorization_boundary"]["solver_run_permitted"]
                is False
                and config["authorization_boundary"]["global_verdict"]
                == "FINAL_THEORY_OPEN"
            ),
            "evidence": config["authorization_boundary"],
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
            "Design-only replacement of factorial unlabeled-level sampling with "
            "a labeled down-set route. No new trajectories or production "
            "measurements are executed."
        ),
        "candidate": {
            "global_central_baseline": config["global_central_baseline"],
            "phase_b_active_candidate": config["candidate_profile_id"],
            "frozen_local_weights": config["frozen_local_weights"],
        },
        "predecessor_artifacts": {
            "continuum_design_digest": continuum_design[
                "semantic_digest_sha256"
            ],
            "bounded_preflight_digest": preflight["semantic_digest_sha256"],
        },
        "primary_exact_labeled_sampler": config[
            "primary_exact_labeled_sampler"
        ],
        "large_n_observable_extension": config[
            "large_n_observable_extension"
        ],
        "approximate_weighted_ideal_route": config[
            "approximate_weighted_ideal_route"
        ],
        "independent_replay_design": config["independent_replay_design"],
        "positive_control_extension": config["positive_control_extension"],
        "spectral_protocol_extension": config["spectral_protocol_extension"],
        "statistical_protocol_extension": config[
            "statistical_protocol_extension"
        ],
        "resource_supervision_design": config["resource_supervision_design"],
        "bounded_implementation_preflight": config[
            "bounded_implementation_preflight"
        ],
        "blocker_mapping": blocker_mapping,
        "stop_conditions": config["stop_conditions"],
        "claim_boundary": config["claim_boundary"],
        "authorization_boundary": config["authorization_boundary"],
        "acceptance_checks": checks,
        "all_acceptance_checks_passed": all(
            record["passed"] for record in checks.values()
        ),
        "production_sampler_available": False,
        "implementation_preflight_authorized": False,
        "production_sampling_authorized": False,
        "source_bindings": [
            _binding(root, CONFIG_PATH),
            _binding(root, PREFLIGHT_RESULT_PATH),
            _binding(root, CONTINUUM_DESIGN_RESULT_PATH),
            _binding(root, CAPABILITIES_PATH),
            _binding(root, DYNAMICS_PATH),
            _binding(root, CAUSAL_SETS_PATH),
            _binding(root, SAMPLER_PREFLIGHT_PATH),
            _binding(root, V2_SPEC_PATH),
            _binding(root, BDG_SPEC_PATH),
            _binding(root, MISSION_PATH),
            _binding(root, HANDOFF_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase-B large-N sampler extension design",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Decision",
            "",
            "The existing exact kernel cannot scale by enumerating every unlabeled",
            "poset and every vertex permutation. The frozen local rule can instead",
            "be evaluated on a naturally birth-labeled history by assigning exact",
            "rational weight to every down-set precursor. Summing labeled choices",
            "over an automorphism orbit reproduces the frozen orbit multiplicity.",
            "",
            "This is a design obligation, not yet an implementation certificate.",
            "Exact down-set enumeration remains exponential in the worst case and",
            "must fail closed at an owner-approved cap.",
            "The current exhaustive height and width helpers are also forbidden",
            "on the large-N path; height must use an exact longest-path dynamic",
            "program verified against the bounded oracle.",
            "The geometric dimension-four control and BDG action evaluation are",
            "separate; no BDG-weighted sampling ensemble is currently defined.",
            "",
            "## Production blockers mapped",
            "",
            *[
                f"- {blocker}: `{', '.join(owners)}`"
                for blocker, owners in payload["blocker_mapping"].items()
            ],
            "",
            "## Acceptance checks",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{name}` | `{record['passed']}` |"
                for name, record in payload["acceptance_checks"].items()
            ],
            "",
            "## Boundary",
            "",
            "No new trajectory, approximate sampler, BDG ensemble, production",
            "measurement, solver run, or scientific verdict is authorized. The",
            "next step requires a new human-owned resource budget.",
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
    payload = build_design(args.root)
    if not payload["all_acceptance_checks_passed"]:
        raise SystemExit("large-N sampler extension design failed")
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked large-N sampler design differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked large-N sampler report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
