"""Phase-B required-physics derivation gap inventory.

This module records the first Phase-B gate without reopening the frozen 955 or
721 campaigns.  It deliberately separates candidate-derived evidence from
known-theory reference controls and keeps the scientific verdict open.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gates import (
    evaluate_candidate,
    validate_candidate_registry,
    validate_gate_spec,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.spin2 import run_spin2_reference_controls

SCHEMA_VERSION = "final-theory-v042-phase-b-required-physics-gap-inventory-v1"
PREPARED = "2026-08-14"
EVIDENCE_HEAD = "91287f0"
START_GATE = "PHASE_B_REQUIRED_PHYSICS_DERIVATION_GAP_INVENTORY"
NEXT_GATE = "PHASE_B_CONTINUUM_DIMENSION_DERIVATION_DESIGN"
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_required_physics_gap_inventory.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_required_physics_gap_inventory.md"
)

EVIDENCE_PATHS = (
    Path("MISSION.md"),
    Path("Final-Theory-Program/requirements/final_theory_gates.yaml"),
    Path("Final-Theory-Program/models/causal_information_v1/model_spec.json"),
    Path("Final-Theory-Program/candidates/candidate_registry.json"),
    Path("Final-Theory-Program/benchmarks/continuum_phase/README.md"),
    Path("Final-Theory-Program/benchmarks/emergent_spin2/README.md"),
    Path("Final-Theory-Program/reports/continuum_phase_analysis.md"),
    Path("Final-Theory-Program/reports/emergent_symmetry_pre_gate.md"),
    Path("Final-Theory-Program/reports/no_go_assumption_ledger.md"),
    Path("Final-Theory-Program/reports/dynamics_source_audit.md"),
    Path("src/universe_lab/final_theory/spin2.py"),
    Path("tests/final_theory/test_spin2.py"),
    Path("src/universe_lab/final_theory/gates.py"),
)

SPIN2_FIELD_BY_REQUIREMENT = {
    "derived two-point response": "derived_two_point_function",
    "1/(k^2+i0) pole": "massless_k2_pole",
    "Spin-2 residue": "spin2_residue",
    "two physical helicities in D=4": "two_physical_helicities",
    "Ward identity": "ward_identity",
    "no scalar or vector ghost": "ghost_free",
    "coarse-graining stability": "coarse_graining_stability",
    "held-out causal-structure replication": "held_out_causal_structure",
}


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _binding(root: Path, relative: Path) -> dict[str, Any]:
    """Return raw and canonical-LF bindings for one evidence file."""

    path = root / relative
    raw = path.read_bytes()
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


def _check(identifier: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def _gate(spec: dict[str, Any], identifier: str) -> dict[str, Any]:
    return next(gate for gate in spec["gates"] if gate["id"] == identifier)


def _evidence_matrix(
    required: list[str], present_by_name: dict[str, bool]
) -> list[dict[str, Any]]:
    return [
        {
            "requirement": name,
            "present": bool(present_by_name.get(name, False)),
        }
        for name in required
    ]


def _central_candidate_result(registry: dict[str, Any]) -> dict[str, Any]:
    candidate = next(
        item for item in registry["candidates"] if item["id"] == registry["central_candidate"]
    )
    evaluated = evaluate_candidate(candidate)
    return {
        "candidate_id": candidate["id"],
        "kinematics_status": candidate["kinematics"]["status"],
        "dynamics_status": candidate["dynamics"]["status"],
        "background_independence_status": candidate[
            "background_independence"
        ]["status"],
        "spin2_evidence": dict(candidate["spin2_evidence"]),
        "evaluated_scientific_status": evaluated["scientific_status"],
        "evaluated_spin2_gate_passed": evaluated["spin2_gate_passed"],
        "evaluated_candidate_evidence": evaluated["spin2_gate_passed"],
    }


def build_inventory(root: Path) -> dict[str, Any]:
    """Build the deterministic Phase-B gap inventory from repository evidence."""

    mission = (root / "MISSION.md").read_text(encoding="utf-8")
    gate_spec = _load_json(
        root, Path("Final-Theory-Program/requirements/final_theory_gates.yaml")
    )
    model = _load_json(
        root, Path("Final-Theory-Program/models/causal_information_v1/model_spec.json")
    )
    registry = _load_json(
        root, Path("Final-Theory-Program/candidates/candidate_registry.json")
    )
    continuum_report = (
        root / "Final-Theory-Program/reports/continuum_phase_analysis.md"
    ).read_text(encoding="utf-8")
    symmetry_report = (
        root / "Final-Theory-Program/reports/emergent_symmetry_pre_gate.md"
    ).read_text(encoding="utf-8")
    no_go_report = (
        root / "Final-Theory-Program/reports/no_go_assumption_ledger.md"
    ).read_text(encoding="utf-8")
    reference_controls = run_spin2_reference_controls()
    central = _central_candidate_result(registry)

    continuum_gate = _gate(gate_spec, "continuum_3p1")
    spin2_gate = _gate(gate_spec, "emergent_spin2")
    coupling_gate = _gate(gate_spec, "universal_coupling")

    current_state = _load_json(root, Path("CURRENT_RESEARCH_STATE.json"))
    campaign = current_state["affected_campaign"]
    phase_a = campaign["phase_A_termination_packet"]
    phase_c = campaign["phase_C"]

    bindings = [_binding(root, path) for path in EVIDENCE_PATHS]

    continuum_present = {name: False for name in continuum_gate["required_evidence"]}
    spin2_present = {
        name: central["spin2_evidence"].get(field, False)
        for name, field in SPIN2_FIELD_BY_REQUIREMENT.items()
    }
    coupling_present = {name: False for name in coupling_gate["required_evidence"]}

    checks = [
        _check(
            "mission_declares_phase_b_physics_targets",
            "連続極限と次元の創発" in mission
            and "spin-2 自由度の出現条件と2偏極・ゴースト不在" in mission
            and "全エネルギー運動量への普遍結合" in mission,
            "Phase B target list is present in MISSION.md",
        ),
        _check(
            "gate_spec_is_structurally_valid",
            not validate_gate_spec(gate_spec),
            validate_gate_spec(gate_spec),
        ),
        _check(
            "candidate_registry_is_structurally_valid",
            not validate_candidate_registry(registry),
            validate_candidate_registry(registry),
        ),
        _check(
            "continuum_gate_is_blocked_without_overclaim",
            "CONTINUUM_PHASE_RESOURCE_BLOCKED" in continuum_report
            and "not strong enough to exclude" in continuum_report
            and model["variable_structure_dynamics"]["status"] == "ANSATZ_ONLY"
            and {
                "measure dmu_G over channels and states",
                "renormalization/coarse-graining transformation",
            }.issubset(
                set(model["variable_structure_dynamics"]["undefined_components"])
            ),
            {
                "status": "CONTINUUM_PHASE_RESOURCE_BLOCKED",
                "exclusion_claim": False,
                "candidate_dynamics_status": model["variable_structure_dynamics"][
                    "status"
                ],
            },
        ),
        _check(
            "candidate_and_reference_spin2_evidence_are_separated",
            reference_controls["passed"]
            and reference_controls["candidate_evidence"] is False
            and central["evaluated_candidate_evidence"] is False
            and "SPIN2_GATE_BLOCKED_BY_CONTINUUM" in symmetry_report,
            {
                "reference_controls_passed": reference_controls["passed"],
                "reference_controls_candidate_evidence": reference_controls[
                    "candidate_evidence"
                ],
                "central_candidate_evidence": central[
                    "evaluated_candidate_evidence"
                ],
            },
        ),
        _check(
            "stress_tensor_and_universal_coupling_are_not_invented",
            "local conserved stress tensor" in no_go_report
            and "UNDEFINED" in no_go_report
            and "universal coupling" in no_go_report,
            "The existing ledger keeps the stress tensor and universal coupling undefined.",
        ),
        _check(
            "phase_a_boundary_and_solver_gate_remain_closed",
            phase_a["terminal_boundaries"] == {
                "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
                "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            }
            and campaign["solver_run_permitted"] is False
            and phase_c["reopen_authorization"]["status"] == "NOT_AUTHORIZED",
            {
                "terminal_boundaries": phase_a["terminal_boundaries"],
                "solver_run_permitted": campaign["solver_run_permitted"],
                "reopen_authorization": phase_c["reopen_authorization"][
                    "status"
                ],
            },
        ),
        _check(
            "evidence_bindings_are_strict_utf8_lf",
            all(binding["strict_utf8_lf"] for binding in bindings),
            {"file_count": len(bindings)},
        ),
    ]

    gaps = [
        {
            "id": "continuum_3p1_dimension",
            "required_gate": "continuum_3p1",
            "status": "CONTINUUM_PHASE_RESOURCE_BLOCKED",
            "classification": "MISSING_DYNAMICAL_LIMIT_AND_DIMENSION_OBSERVABLE",
            "required_evidence": _evidence_matrix(
                continuum_gate["required_evidence"], continuum_present
            ),
            "current_finite_observables": [
                "order fraction",
                "interval abundances",
                "height",
                "width",
                "automorphism entropy",
                "susceptibility",
                "Binder-like order-fraction cumulant",
            ],
            "evidence_paths": [
                "Final-Theory-Program/requirements/final_theory_gates.yaml",
                "Final-Theory-Program/models/causal_information_v1/model_spec.json",
                "Final-Theory-Program/benchmarks/continuum_phase/README.md",
                "Final-Theory-Program/reports/continuum_phase_analysis.md",
                "Final-Theory-Program/reports/dynamics_source_audit.md",
            ],
            "claim_boundary": (
                "The finite sizes 3, 4, and 5 do not establish a continuum phase; "
                "the current resource boundary also does not exclude one."
            ),
            "next_task": (
                "Define a preregistered dimension estimator, correlation-length "
                "observable, ensemble/measure, finite-size scaling protocol, "
                "controls, and held-out test before any bounded sampling."
            ),
        },
        {
            "id": "emergent_spin2_response",
            "required_gate": "emergent_spin2",
            "status": "SPIN2_NOT_FOUND",
            "classification": "NO_QUALIFYING_CANDIDATE_DERIVED_RESPONSE",
            "required_evidence": _evidence_matrix(
                spin2_gate["required_evidence"], spin2_present
            ),
            "reference_controls": {
                "passed": reference_controls["passed"],
                "candidate_evidence": reference_controls["candidate_evidence"],
                "control_count": len(reference_controls["controls"]),
            },
            "evidence_paths": [
                "Final-Theory-Program/requirements/final_theory_gates.yaml",
                "Final-Theory-Program/benchmarks/emergent_spin2/README.md",
                "Final-Theory-Program/reports/emergent_symmetry_pre_gate.md",
                "Final-Theory-Program/candidates/candidate_registry.json",
                "src/universe_lab/final_theory/spin2.py",
                "tests/final_theory/test_spin2.py",
            ],
            "claim_boundary": (
                "SPIN2_NOT_FOUND means no qualifying candidate-derived evidence "
                "is present in the evaluated artifact. It is not a no-go theorem "
                "for the candidate family."
            ),
            "next_task": (
                "After a continuum candidate is defined, specify and derive the "
                "candidate two-point response, then test pole, residue, Ward, "
                "helicity, ghost, coarse-graining, and held-out conditions."
            ),
        },
        {
            "id": "universal_stress_tensor_coupling",
            "required_gate": "universal_coupling",
            "status": "UNDEFINED",
            "classification": "NO_CANDIDATE_STRESS_TENSOR_OR_SOURCE_RESPONSE",
            "required_evidence": _evidence_matrix(
                coupling_gate["required_evidence"], coupling_present
            ),
            "dependency": {
                "requires_continuum_local_observables": True,
                "requires_candidate_derived_response": True,
            },
            "evidence_paths": [
                "Final-Theory-Program/requirements/final_theory_gates.yaml",
                "Final-Theory-Program/models/causal_information_v1/model_spec.json",
                "Final-Theory-Program/candidates/candidate_registry.json",
                "Final-Theory-Program/reports/no_go_assumption_ledger.md",
                "Final-Theory-Program/reports/dynamics_source_audit.md",
            ],
            "claim_boundary": (
                "A conserved local stress tensor, a universal coupling, and "
                "self-energy inclusion are currently undefined; no Einstein or "
                "Deser coupling is imported as candidate evidence."
            ),
            "next_task": (
                "Define the candidate source observable and its conservation law; "
                "only then compare one coupling across all source sectors, including "
                "self-energy, with an explicit field/observable map."
            ),
        },
    ]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "evidence_head": EVIDENCE_HEAD,
        "status": "PHASE_B_REQUIRED_PHYSICS_DERIVATION_GAP_INVENTORY_COMPLETE",
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "next_gate": NEXT_GATE,
        "scope": (
            "Required physics derivation audit; no deeper computation or reopening "
            "of frozen 955/721 profiles."
        ),
        "method": {
            "classification_rule": (
                "Separate measured candidate evidence, reference controls, missing "
                "derivation, and resource-boundary statements. Never promote a "
                "reference control or a finite sample to candidate evidence."
            ),
            "dependency_order": [
                "continuum_3p1_dimension",
                "emergent_spin2_response",
                "universal_stress_tensor_coupling",
            ],
            "solver_reopen": "not part of this gate",
        },
        "candidate_snapshot": central,
        "gaps": gaps,
        "acceptance_criteria": {
            "mission_scope": checks[0],
            "gate_spec": checks[1],
            "candidate_registry": checks[2],
            "continuum_boundary": checks[3],
            "candidate_reference_separation": checks[4],
            "coupling_boundary": checks[5],
            "phase_a_and_solver_boundary": checks[6],
            "evidence_bindings": checks[7],
        },
        "evidence_bindings": bindings,
        "phase_a_boundary_preserved": {
            "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
            "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            "both_full_profiles_resolved": False,
            "solver_run_permitted": False,
        },
        "phase_b_transition": {
            "started_by_this_inventory": True,
            "inventory_gate_complete": True,
            "next_gate": NEXT_GATE,
        },
        "all_acceptance_checks_passed": all(
            item["passed"] for item in checks
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    rows = []
    for gap in payload["gaps"]:
        missing = sum(
            not item["present"] for item in gap["required_evidence"]
        )
        total = len(gap["required_evidence"])
        rows.append(
            f"| `{gap['id']}` | `{gap['status']}` | "
            f"`{gap['classification']}` | {missing}/{total} |"
        )

    return "\n".join(
        [
            "# Phase-B required physics derivation gap inventory",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Scope",
            "",
            "This packet starts Phase B at its required first gate: an evidence-bound",
            "inventory of the missing physics derivations. It does not reopen or",
            "recompute the frozen 955 and 721 profiles.",
            "",
            "The global scientific verdict remains `FINAL_THEORY_OPEN`; no new",
            "scientific completion verdict is issued.",
            "",
            "## Inventory",
            "",
            "| target | current status | classification | missing required evidence |",
            "|---|---|---|---:|",
            *rows,
            "",
            "### Continuum and dimension",
            "",
            "The finite benchmark records several order-theoretic observables at",
            "sizes 3, 4, and 5, but leaves dimension, correlation length, and",
            "continuum exponents undefined. The candidate model also lacks a",
            "defined infinite-cutoff measure, normalization prescription, and",
            "coarse-graining map. This is a resource/missing-observable boundary,",
            "not evidence that a continuum phase is impossible.",
            "",
            "### Emergent Spin-2",
            "",
            "The Barnes-Rivers, massless-helicity, and Fierz-Pauli checks pass as",
            "independent reference controls. Their own machine output says",
            "`candidate_evidence: false`. The central candidate has no derived",
            "two-point response, pole, residue, helicity, Ward, ghost, stability,",
            "or held-out evidence, so its status remains `SPIN2_NOT_FOUND`.",
            "",
            "### Universal coupling",
            "",
            "The current ledger marks the local conserved stress tensor and universal",
            "coupling as `UNDEFINED`. The required source, single-coupling, and",
            "self-energy checks therefore cannot be evaluated yet. No Einstein or",
            "Deser coupling is imported as candidate evidence.",
            "",
            "## Dependency and next gate",
            "",
            "The working order is continuum/dimension -> candidate Spin-2 response ->",
            "universal stress-tensor coupling. The next finite task is:",
            "",
            f"`{payload['next_gate']}`",
            "",
            "That task must define a preregistered dimension estimator, correlation",
            "length observable, ensemble/measure, scaling protocol, controls, and",
            "held-out test before bounded sampling is authorized.",
            "",
            "## Boundary checks",
            "",
            "- Phase-A terminals remain `REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT` and",
            "  `FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT`.",
            "- `solver_run_permitted` remains `false`; this inventory grants no reopen",
            "  authorization or solver budget.",
            "- Reference controls remain separate from candidate-derived evidence.",
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
    payload = build_inventory(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked Phase-B inventory differs from rebuilt payload")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked Phase-B report differs from rebuilt report")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
