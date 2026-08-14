"""Machine-readable gate and candidate validation."""

from __future__ import annotations

from typing import Any

SCIENTIFIC_STATUSES = {
    "KINEMATICS_DEFINED",
    "DYNAMICS_DEFINED",
    "BACKGROUND_INDEPENDENCE_PASS",
    "CONTINUUM_PHASE_SUPPORTED",
    "SPIN2_NOT_FOUND",
    "SPIN2_CANDIDATE",
    "SPIN2_GATE_PASS",
    "UNIVERSAL_COUPLING_PASS",
    "EINSTEIN_VERTEX_PASS",
    "CANDIDATE_REJECTED",
    "FINAL_THEORY_OPEN",
}

SPIN2_EVIDENCE_FIELDS = (
    "derived_two_point_function",
    "massless_k2_pole",
    "spin2_residue",
    "two_physical_helicities",
    "ward_identity",
    "ghost_free",
    "universal_stress_tensor_coupling",
    "coarse_graining_stability",
    "held_out_causal_structure",
)


def validate_gate_spec(spec: dict[str, Any]) -> list[str]:
    """Return structural errors in the Final-Theory gate specification."""

    errors: list[str] = []
    declared = set(spec.get("scientific_statuses", []))
    if declared != SCIENTIFIC_STATUSES:
        errors.append("scientific_statuses must equal the frozen v0.1 status set")
    gate_ids = [gate.get("id") for gate in spec.get("gates", [])]
    if len(gate_ids) != len(set(gate_ids)):
        errors.append("gate ids must be unique")
    required_gates = {
        "microscopic_definition",
        "background_independence",
        "quantum_consistency",
        "continuum_3p1",
        "emergent_spin2",
        "universal_coupling",
        "einstein_vertex",
        "black_hole",
        "matter",
        "prediction",
    }
    if not required_gates.issubset(set(gate_ids)):
        errors.append("one or more mandatory final-theory gates are missing")
    if spec.get("completion_rule") != "ALL_GATES_REQUIRED":
        errors.append("completion_rule must be ALL_GATES_REQUIRED")
    return errors


def validate_candidate_registry(registry: dict[str, Any]) -> list[str]:
    """Return structural errors in the candidate registry."""

    errors: list[str] = []
    schema_version = registry.get("schema_version")
    if schema_version not in {"0.1", "0.2"}:
        errors.append("schema_version must be 0.1 or 0.2")
    candidates = registry.get("candidates", [])
    minimum_families = registry.get("candidate_policy", {}).get(
        "minimum_families", 3
    )
    family_count = len(
        {
            candidate.get("family")
            for candidate in candidates
            if candidate.get("family")
        }
    )
    if family_count < minimum_families:
        errors.append("at least three candidate families are required")
    identifiers = [candidate.get("id") for candidate in candidates]
    if len(identifiers) != len(set(identifiers)):
        errors.append("candidate ids must be unique")
    if registry.get("central_candidate") not in identifiers:
        errors.append("central_candidate must refer to a registered candidate")
    active_candidates = registry.get("active_candidates", {})
    if schema_version == "0.2":
        phase_b_candidate = active_candidates.get("PHASE_B")
        if phase_b_candidate not in identifiers:
            errors.append("active_candidates.PHASE_B must refer to a registered candidate")
    required = {
        "id",
        "name",
        "family",
        "role",
        "kinematics",
        "dynamics",
        "background_independence",
        "spin2_evidence",
        "kill_conditions",
        "claim_boundary",
    }
    for candidate in candidates:
        missing = required - set(candidate)
        if missing:
            errors.append(
                f"{candidate.get('id', '<unknown>')}: missing {sorted(missing)}"
            )
        evidence = candidate.get("spin2_evidence", {})
        unknown = set(evidence) - set(SPIN2_EVIDENCE_FIELDS)
        missing_evidence = set(SPIN2_EVIDENCE_FIELDS) - set(evidence)
        if unknown or missing_evidence:
            errors.append(
                f"{candidate.get('id', '<unknown>')}: spin2 evidence keys must "
                f"match the frozen field set; unknown={sorted(unknown)}, "
                f"missing={sorted(missing_evidence)}"
            )
        if schema_version == "0.2" and candidate.get("id") == active_candidates.get(
            "PHASE_B"
        ) and not candidate.get("candidate_version"):
            errors.append(
                f"{candidate.get('id', '<unknown>')}: active candidate_version is required"
            )
    return errors


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Evaluate only supplied candidate evidence; never import reference controls."""

    achieved: list[str] = []
    kinematics_defined = candidate["kinematics"].get("status") == "DEFINED"
    dynamics_defined = candidate["dynamics"].get("status") == "DEFINED"
    background_passed = (
        candidate["background_independence"].get("status") == "PASS"
    )
    if kinematics_defined:
        achieved.append("KINEMATICS_DEFINED")
    if dynamics_defined:
        achieved.append("DYNAMICS_DEFINED")
    if background_passed:
        achieved.append("BACKGROUND_INDEPENDENCE_PASS")

    evidence = candidate["spin2_evidence"]
    spin2_checks = {
        field: evidence.get(field) is True for field in SPIN2_EVIDENCE_FIELDS
    }
    spin2_passed = all(spin2_checks.values())
    if spin2_passed:
        achieved.extend(
            [
                "SPIN2_CANDIDATE",
                "SPIN2_GATE_PASS",
                "UNIVERSAL_COUPLING_PASS",
            ]
        )
    else:
        achieved.append("SPIN2_NOT_FOUND")

    contradicted = bool(evidence.get("derived_two_point_function")) and (
        evidence.get("ghost_free") is False
        or evidence.get("ward_identity") is False
    )
    if contradicted:
        achieved.append("CANDIDATE_REJECTED")
    achieved.append("FINAL_THEORY_OPEN")
    return {
        "candidate_id": candidate["id"],
        "achieved_statuses": achieved,
        "kinematics_defined": kinematics_defined,
        "dynamics_defined": dynamics_defined,
        "background_independence_passed": background_passed,
        "spin2_checks": spin2_checks,
        "spin2_gate_passed": spin2_passed,
        "rejected": contradicted,
        "scientific_status": "FINAL_THEORY_OPEN",
        "claim_boundary": (
            "SPIN2_NOT_FOUND means no qualifying evidence exists in this "
            "candidate artifact. It is not a theorem that the family can never "
            "produce spin 2."
        ),
    }
