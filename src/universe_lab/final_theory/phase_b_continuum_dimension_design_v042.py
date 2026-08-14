"""Freeze the Phase-B continuum and dimension measurement design.

This packet is a preregistration artifact, not a continuum measurement.  It
audits the exact v2 domain through n=5 only to catch normalization, identity,
and observable-construction errors before any larger sampler is considered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import (
    causet_id,
    comparable_pairs,
    enumerate_unlabeled_posets,
    height,
)
from universe_lab.final_theory.continuum_observables_v042 import (
    minkowski_ordering_fraction,
    ordering_fraction_dimension,
)
from universe_lab.final_theory.dynamics_v02 import (
    CANDIDATE_PROFILE,
    RANDOM_CONTROL_PROFILE,
    dynamics_benchmark,
    propagate_distribution,
)
from universe_lab.final_theory.gates import validate_candidate_registry
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_active_candidate_manifest_v042 import (
    build_manifest,
)
from universe_lab.final_theory.phase_b_candidate_identity_v042 import build_audit

SCHEMA_VERSION = "final-theory-v042-phase-b-continuum-dimension-design-v1"
PREPARED = "2026-08-15"
STATUS = (
    "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_DESIGN_FROZEN_"
    "PRODUCTION_EXTENSION_REQUIRED_NO_SAMPLING_AUTHORIZATION"
)
START_GATE = "PHASE_B_CONTINUUM_DIMENSION_DERIVATION_DESIGN"
NEXT_GATE = "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_MEASUREMENT_PREFLIGHT"
RESULT_PATH = Path("results/v0.4.2_phase_b_continuum_dimension_design.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_continuum_dimension_design.md")
CONFIG_PATH = Path("config/v0.4.2_phase_b_continuum_dimension_design.json")
REGISTRY_PATH = Path(
    "Final-Theory-Program/candidates/candidate_registry_v042_phase_b.json"
)
V2_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v2/model_spec.json")
DYNAMICS_PATH = Path("src/universe_lab/final_theory/dynamics_v02.py")
CAUSAL_SETS_PATH = Path("src/universe_lab/final_theory/causal_sets.py")
GATE_SPEC_PATH = Path("Final-Theory-Program/requirements/final_theory_gates.yaml")
MANIFEST_RESULT_PATH = Path("results/v0.4.2_phase_b_active_candidate_manifest.json")
IDENTITY_RESULT_PATH = Path("results/v0.4.2_phase_b_candidate_identity.json")
OBSERVABLES_PATH = Path(
    "src/universe_lab/final_theory/continuum_observables_v042.py"
)
SOURCES_LEDGER_PATH = Path("references/sources.json")
CALIBRATION_NOTE_PATH = Path(
    "references/notes/v0.4.2_myrheim_meyer_calibration_audit_2026-08-15.md"
)


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


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _ordering_fraction(relation: tuple[int, ...]) -> Fraction | None:
    n = len(relation)
    if n < 2:
        return None
    return Fraction(comparable_pairs(relation), n * (n - 1) // 2)


def _ordering_dimension(value: Fraction | None) -> float | None:
    return ordering_fraction_dimension(value)


def _weighted_integer_mean(
    distribution: dict[str, Fraction],
    relation_by_id: dict[str, tuple[int, ...]],
    observable: Any,
) -> Fraction:
    return sum(
        (probability * observable(relation_by_id[history])
         for history, probability in distribution.items()),
        start=Fraction(0),
    )


def _exact_pilot(root: Path, max_n: int) -> dict[str, Any]:
    levels = enumerate_unlabeled_posets(max_n)
    candidate_stages = propagate_distribution(
        max_n, profile_id=CANDIDATE_PROFILE.profile_id
    )
    random_stages = propagate_distribution(
        max_n, profile_id=RANDOM_CONTROL_PROFILE.profile_id
    )
    size_records: list[dict[str, Any]] = []
    for n, level in enumerate(levels):
        relation_by_id = {causet_id(relation): relation for relation in level}
        candidate = candidate_stages[n]
        random_control = random_stages[n]
        candidate_order = (
            _weighted_integer_mean(
                candidate,
                relation_by_id,
                lambda relation: _ordering_fraction(relation) or Fraction(0),
            )
            if n >= 2
            else None
        )
        random_order = (
            _weighted_integer_mean(
                random_control,
                relation_by_id,
                lambda relation: _ordering_fraction(relation) or Fraction(0),
            )
            if n >= 2
            else None
        )
        candidate_height = _weighted_integer_mean(candidate, relation_by_id, height)
        random_height = _weighted_integer_mean(
            random_control, relation_by_id, height
        )
        size_records.append(
            {
                "n": n,
                "state_count": len(level),
                "candidate_normalized": sum(candidate.values(), start=Fraction(0))
                == 1,
                "random_control_normalized": sum(
                    random_control.values(), start=Fraction(0)
                )
                == 1,
                "candidate_expected_ordering_fraction": (
                    _fraction_record(candidate_order)
                    if candidate_order is not None
                    else None
                ),
                "random_expected_ordering_fraction": (
                    _fraction_record(random_order)
                    if random_order is not None
                    else None
                ),
                "candidate_ordering_dimension": _ordering_dimension(candidate_order),
                "random_ordering_dimension": _ordering_dimension(random_order),
                "candidate_expected_height": _fraction_record(candidate_height),
                "random_expected_height": _fraction_record(random_height),
            }
        )
    return {
        "max_n": max_n,
        "level_counts": [len(level) for level in levels],
        "candidate_profile_id": CANDIDATE_PROFILE.profile_id,
        "random_control_profile_id": RANDOM_CONTROL_PROFILE.profile_id,
        "size_records": size_records,
        "non_evidentiary": True,
        "claim_boundary": (
            "Exact n<=5 pilot values are regression data only. They do not "
            "measure a continuum phase, a limiting dimension, or a gravitational "
            "response."
        ),
    }


def _design_checks(
    config: dict[str, Any],
    registry: dict[str, Any],
    v2_spec: dict[str, Any],
    manifest: dict[str, Any],
    identity: dict[str, Any],
    benchmark: dict[str, Any],
    state: dict[str, Any],
    pilot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scaling = config["scaling_protocol"]
    planned_sizes = scaling["planned_sizes"]
    controls = config["controls"]
    ordering_estimator = next(
        estimator
        for estimator in config["dimension_estimators"]
        if estimator["id"] == "ordering_fraction_inverse"
    )
    spectral_estimator = next(
        estimator
        for estimator in config["dimension_estimators"]
        if estimator["id"] == "spectral_return_plateau"
    )
    calibration_anchors = ordering_estimator["calibration_anchor_values"]
    phase_b = state["affected_campaign"]["phase_B"]
    return {
        "active_candidate_identity_is_frozen": {
            "passed": (
                registry["central_candidate"] == "causal_information_v1"
                and registry["active_candidates"]["PHASE_B"]
                == CANDIDATE_PROFILE.profile_id
                and manifest["all_acceptance_checks_passed"] is True
                and identity["all_safety_checks_passed"] is True
            ),
            "evidence": {
                "central_candidate": registry["central_candidate"],
                "active_candidate": registry["active_candidates"]["PHASE_B"],
            },
        },
        "phase_b_registry_is_structurally_valid": {
            "passed": not validate_candidate_registry(registry),
            "evidence": validate_candidate_registry(registry),
        },
        "exact_pilot_domain_is_independently_normalized": {
            "passed": (
                pilot["level_counts"]
                == config["exact_pilot_domain"]["known_unlabeled_poset_counts"]
                and all(
                    record["candidate_normalized"]
                    and record["random_control_normalized"]
                    for record in pilot["size_records"]
                )
            ),
            "evidence": pilot["level_counts"],
        },
        "dimension_estimators_are_preregistered": {
            "passed": len(config["dimension_estimators"])
            >= config["acceptance_rules"]["dimension_estimator_count_required"]
            and [
                estimator["id"] for estimator in config["dimension_estimators"]
            ]
            == config["acceptance_rules"]["dimension_estimator_ids"]
            and all(
                estimator.get("candidate_evidence") is True
                for estimator in config["dimension_estimators"][:2]
            ),
            "evidence": [item["id"] for item in config["dimension_estimators"]],
        },
        "ordering_calibration_matches_source_anchors": {
            "passed": (
                ordering_estimator["calibration"]
                == "f(d)=Gamma(d+1)*Gamma(d/2)/(2*Gamma(3*d/2))"
                and calibration_anchors == {"2": 0.5, "4": 0.1}
                and all(
                    abs(minkowski_ordering_fraction(float(dimension)) - expected)
                    <= 1e-12
                    for dimension, expected in calibration_anchors.items()
                )
            ),
            "evidence": calibration_anchors,
        },
        "bounded_measurement_aggregation_is_explicit": {
            "passed": (
                spectral_estimator["bounded_preflight_fit"]["walk_time_steps"]
                == [2, 3, 4, 5]
                and spectral_estimator["production_plateau_window_frozen"] is False
                and config["correlation_length_observable"][
                    "ensemble_aggregation"
                ]
                == "conditional root-mean-square sqrt(E[xi^2 | xi defined])"
                and config["correlation_length_observable"][
                    "minimum_defined_probability_mass_for_candidate_evidence"
                ]
                == 0.95
            ),
            "evidence": {
                "spectral_preflight_steps": spectral_estimator[
                    "bounded_preflight_fit"
                ]["walk_time_steps"],
                "correlation_ensemble_aggregation": config[
                    "correlation_length_observable"
                ]["ensemble_aggregation"],
            },
        },
        "production_design_gaps_are_fail_closed": {
            "passed": (
                spectral_estimator["production_plateau_window_frozen"] is False
                and "fixed production spectral plateau window"
                in config["production_design_gaps"]
                and "executable BDG dimension-four ensemble"
                in config["production_design_gaps"]
                and config["authorization_boundary"][
                    "production_sampling_authorized"
                ]
                is False
            ),
            "evidence": config["production_design_gaps"],
        },
        "scaling_and_holdout_are_disjoint_and_separated": {
            "passed": (
                len(planned_sizes) >= scaling["minimum_distinct_sizes"]
                and planned_sizes[-1] / planned_sizes[0]
                >= scaling["minimum_max_to_min_size_ratio"]
                and min(
                    later / earlier
                    for earlier, later in zip(
                        planned_sizes, planned_sizes[1:], strict=False
                    )
                )
                >= scaling["minimum_adjacent_size_ratio"]
                and set(scaling["training_sizes"]).isdisjoint(
                    scaling["holdout_sizes"]
                )
                and set(scaling["training_sizes"]) | set(scaling["holdout_sizes"])
                == set(planned_sizes)
                and scaling["no_holdout_refit"] is True
            ),
            "evidence": {
                "planned_sizes": planned_sizes,
                "training_sizes": scaling["training_sizes"],
                "holdout_sizes": scaling["holdout_sizes"],
            },
        },
        "controls_are_separated_from_candidate_evidence": {
            "passed": (
                {control["id"] for control in controls}
                == {
                    "random_growth_negative_control",
                    "bdg_dimension_four_positive_control",
                    "label_permutation_control",
                }
                and all(control["candidate_evidence"] is False for control in controls)
            ),
            "evidence": controls,
        },
        "target_dimension_is_not_in_candidate_path": {
            "passed": (
                benchmark["explicit_candidate"]["target_dimension_present"] is False
                and "target_dimension" not in CANDIDATE_PROFILE.parameters
                and v2_spec["forbidden_inputs"]["target_3_plus_1_dimension"]
                is False
            ),
            "evidence": benchmark["explicit_candidate"],
        },
        "authorization_remains_fail_closed": {
            "passed": (
                config["authorization_boundary"]["production_sampling_authorized"]
                is False
                and config["authorization_boundary"]["solver_run_permitted"] is False
                and state["affected_campaign"]["solver_run_permitted"] is False
                and phase_b["sampler_preflight"]["sampling_authorized"] is False
            ),
            "evidence": {
                "sampling_authorized": phase_b["sampler_preflight"][
                    "sampling_authorized"
                ],
                "solver_run_permitted": state["affected_campaign"][
                    "solver_run_permitted"
                ],
            },
        },
    }


def build_design(root: Path) -> dict[str, Any]:
    config = _load_json(root, CONFIG_PATH)
    registry = _load_json(root, REGISTRY_PATH)
    v2_spec = _load_json(root, V2_SPEC_PATH)
    state = _load_json(root, Path("CURRENT_RESEARCH_STATE.json"))
    manifest = build_manifest(root)
    identity = build_audit(root)
    benchmark = dynamics_benchmark()
    pilot = _exact_pilot(root, config["exact_pilot_domain"]["max_n"])
    checks = _design_checks(
        config, registry, v2_spec, manifest, identity, benchmark, state, pilot
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "next_gate": NEXT_GATE,
        "candidate": {
            "global_central_baseline": registry["central_candidate"],
            "phase_b_active_candidate": registry["active_candidates"]["PHASE_B"],
            "v1_v2_equivalence_certified": registry["candidate_policy"][
                "v1_v2_equivalence_certified"
            ],
            "cross_version_evidence_transfer": registry["candidate_policy"][
                "cross_version_evidence_transfer"
            ],
        },
        "design_config": CONFIG_PATH.as_posix(),
        "design_scope": (
            "Preregistered relational dimension, correlation-length, scaling, "
            "control, and holdout protocol. The exact n<=5 pilot is a regression "
            "check only and does not authorize larger sampling."
        ),
        "dimension_estimators": config["dimension_estimators"],
        "correlation_length_observable": config["correlation_length_observable"],
        "scaling_protocol": config["scaling_protocol"],
        "acceptance_rules": config["acceptance_rules"],
        "controls": config["controls"],
        "stop_conditions": config["stop_conditions"],
        "production_design_gaps": config["production_design_gaps"],
        "exact_pilot": pilot,
        "acceptance_checks": checks,
        "all_acceptance_checks_passed": all(
            item["passed"] for item in checks.values()
        ),
        "authorization_boundary": config["authorization_boundary"],
        "source_bindings": [
            _binding(root, CONFIG_PATH),
            _binding(root, REGISTRY_PATH),
            _binding(root, V2_SPEC_PATH),
            _binding(root, DYNAMICS_PATH),
            _binding(root, CAUSAL_SETS_PATH),
            _binding(root, GATE_SPEC_PATH),
            _binding(root, MANIFEST_RESULT_PATH),
            _binding(root, IDENTITY_RESULT_PATH),
            _binding(root, OBSERVABLES_PATH),
            _binding(root, SOURCES_LEDGER_PATH),
            _binding(root, CALIBRATION_NOTE_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    checks = payload["acceptance_checks"]
    pilot = payload["exact_pilot"]
    return "\n".join(
        [
            "# Phase-B continuum and dimension derivation design",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Decision",
            "",
            "The v2 sparse-Kraus profile is the active Phase-B input while v1",
            "remains the global central baseline. This packet freezes the bounded",
            "preflight definitions and records unresolved production-protocol gaps;",
            "it does not authorize production sampling or transfer evidence between",
            "versions.",
            "",
            "## Preregistered measurements",
            "",
            "| estimator or observable | definition |",
            "|---|---|",
            *[
                f"| `{item['id']}` | {item['observable']} |"
                for item in payload["dimension_estimators"]
            ],
            "| `correlation_length` | "
            f"{payload['correlation_length_observable']['spectral_gap_proxy']} |",
            "",
            "The planned size set is "
            f"`{payload['scaling_protocol']['planned_sizes']}` with training sizes "
            f"`{payload['scaling_protocol']['training_sizes']}` and holdout sizes "
            f"`{payload['scaling_protocol']['holdout_sizes']}`. Holdout refitting is",
            "forbidden.",
            "",
            "## Exact pilot boundary",
            "",
            f"The pilot covers n≤{pilot['max_n']} with level counts "
            f"`{pilot['level_counts']}`. Candidate and random-control distributions",
            "are exactly normalized at every level. These values are regression data",
            "only, not evidence for a continuum phase or limiting dimension.",
            "",
            "| n | candidate order fraction | candidate height |",
            "|---:|---:|---:|",
            *[
                "| "
                f"{record['n']} | "
                + (
                    f"{record['candidate_expected_ordering_fraction']['numerator']}"
                    f"/{record['candidate_expected_ordering_fraction']['denominator']}"
                    if record["candidate_expected_ordering_fraction"] is not None
                    else "undefined"
                )
                + " | "
                + f"{record['candidate_expected_height']['numerator']}"
                + f"/{record['candidate_expected_height']['denominator']} |"
                for record in pilot["size_records"]
            ],
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
            "## Production extension gaps",
            "",
            *[f"- {gap}" for gap in payload["production_design_gaps"]],
            "",
            "## Boundary",
            "",
            "The next gate is a separately budgeted bounded measurement preflight.",
            "A failed normalization, replay, control, holdout, or scaling check",
            "freezes Phase B without a scientific completion verdict.",
            "The global verdict remains `FINAL_THEORY_OPEN` and the solver remains",
            "unauthorized.",
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
        raise SystemExit("continuum dimension design acceptance failed")
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked continuum dimension design differs from rebuild")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked continuum dimension report differs from rebuild")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
