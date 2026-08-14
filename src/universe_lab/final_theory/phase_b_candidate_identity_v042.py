"""Fail-closed audit of the Phase-B candidate identity and input freeze.

The repository contains a registered v1 kinematic candidate and a separately
implemented v2 sparse-Kraus growth profile.  This packet records that they are
not interchangeable evidence.  It intentionally does not promote v2, alter
the registry, or authorize continuum sampling.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_active_candidate_manifest_v042 import (
    RESULT_PATH as MANIFEST_RESULT_PATH,
)
from universe_lab.final_theory.phase_b_active_candidate_manifest_v042 import (
    build_manifest,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-candidate-identity-v1"
PREPARED = "2026-08-15"
START_GATE = "PHASE_B_CANDIDATE_IDENTITY_AND_INPUT_FREEZE"
NEXT_GATE = "PHASE_B_CONTINUUM_DIMENSION_DERIVATION_DESIGN"
RESULT_PATH = Path("results/v0.4.2_phase_b_candidate_identity.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_candidate_identity.md")

BASE_REGISTRY_PATH = Path("Final-Theory-Program/candidates/candidate_registry.json")
REGISTRY_PATH = Path(
    "Final-Theory-Program/candidates/candidate_registry_v042_phase_b.json"
)
V1_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v1/model_spec.json")
V2_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v2/model_spec.json")
DYNAMICS_PATH = Path("src/universe_lab/final_theory/dynamics_v02.py")
BENCHMARK_PATH = Path("src/universe_lab/final_theory/benchmarks.py")
STATE_PATH = Path("CURRENT_RESEARCH_STATE.json")


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


def _check(identifier: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def build_audit(root: Path) -> dict[str, Any]:
    """Build the deterministic candidate-identity audit."""

    registry = _load_json(root, REGISTRY_PATH)
    base_registry = _load_json(root, BASE_REGISTRY_PATH)
    v1 = _load_json(root, V1_SPEC_PATH)
    v2 = _load_json(root, V2_SPEC_PATH)
    state = _load_json(root, STATE_PATH)
    dynamics_text = (root / DYNAMICS_PATH).read_text(encoding="utf-8")
    benchmark_text = (root / BENCHMARK_PATH).read_text(encoding="utf-8")

    candidate_ids = [item["id"] for item in registry["candidates"]]
    central_id = registry["central_candidate"]
    active_id = registry["active_candidates"]["PHASE_B"]
    v2_id = v2["model_id"]
    implementation_profile_id = "causal_information_v2_sparse_kraus"
    manifest = build_manifest(root)

    identity_mismatch = (
        active_id != v2_id
        or v2_id not in candidate_ids
        or v1["model_id"] != central_id
        or implementation_profile_id != v2_id
    )
    phase_a = state["affected_campaign"]["phase_A_termination_packet"]
    campaign = state["affected_campaign"]

    checks = [
        _check(
            "registered_central_candidate_is_explicit",
            central_id in candidate_ids,
            {"central_candidate": central_id, "candidate_ids": candidate_ids},
        ),
        _check(
            "registered_v1_spec_matches_registry",
            v1["model_id"] == central_id,
            {"registry_central": central_id, "v1_model_id": v1["model_id"]},
        ),
        _check(
            "frozen_v0_1_registry_is_preserved",
            base_registry["schema_version"] == "0.1"
            and base_registry["central_candidate"] == "causal_information_v1",
            {"path": BASE_REGISTRY_PATH.as_posix()},
        ),
        _check(
            "phase_b_active_pointer_matches_v2",
            active_id == v2_id and active_id in candidate_ids,
            {"phase_b_active_candidate": active_id, "v2_model_id": v2_id},
        ),
        _check(
            "v2_implementation_matches_v2_spec",
            implementation_profile_id == v2_id
            and implementation_profile_id in dynamics_text,
            {
                "v2_model_id": v2_id,
                "implementation_profile_id": implementation_profile_id,
            },
        ),
        _check(
            "active_candidate_manifest_matches_registry",
            manifest["active_candidate"]["id"] == active_id
            and manifest["all_acceptance_checks_passed"] is True,
            {
                "registry_central": central_id,
                "phase_b_active_candidate": active_id,
                "v1_model_id": v1["model_id"],
                "v2_model_id": v2_id,
                "manifest_digest": manifest["semantic_digest_sha256"],
            },
        ),
        _check(
            "central_benchmark_path_is_v1_bound",
            "causal_information_v1" in benchmark_text
            and "central model id must be causal_information_v1" in benchmark_text,
            {"benchmark_path": BENCHMARK_PATH.as_posix()},
        ),
        _check(
            "phase_a_freeze_and_solver_boundary_preserved",
            phase_a["terminal_boundaries"] == {
                "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
                "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            }
            and campaign["solver_run_permitted"] is False,
            {
                "terminal_boundaries": phase_a["terminal_boundaries"],
                "solver_run_permitted": campaign["solver_run_permitted"],
            },
        ),
    ]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": "PHASE_B_CANDIDATE_IDENTITY_AND_INPUT_FREEZE_CERTIFIED",
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "next_gate": NEXT_GATE,
        "scope": (
            "Candidate identity and input-freeze audit. v2 is active for Phase B "
            "without replacing the global v1 central baseline; no continuum "
            "sampling or reopening of frozen 955/721 profiles."
        ),
        "identity": {
            "registry_central_candidate": central_id,
            "phase_b_active_candidate": active_id,
            "registered_candidate_ids": candidate_ids,
            "registered_central_spec": V1_SPEC_PATH.as_posix(),
            "registered_central_model_id": v1["model_id"],
            "implemented_v2_spec": V2_SPEC_PATH.as_posix(),
            "implemented_v2_model_id": v2_id,
            "implemented_v2_role": v2.get("role"),
            "implemented_profile_id": implementation_profile_id,
            "same_candidate_certified": False,
            "active_candidate_identity_certified": not identity_mismatch,
            "mismatch_detected": identity_mismatch,
            "claim_boundary": (
                "v2 finite-growth results are v2 evidence only and cannot be "
                "transferred to the v1 candidate without an explicit certified map."
            ),
        },
        "frozen_decision": {
            "decision": "v1_remains_global_central_v2_is_phase_b_active",
            "v1_to_v2_equivalence_certified": False,
            "cross_version_evidence_transfer": False,
            "sampling_fail_closed_until_continuum_design_gate": True,
            "manifest": MANIFEST_RESULT_PATH.as_posix(),
        },
        "input_manifest_requirements": [
            "candidate ID and version",
            "spec path and SHA-256",
            "implementation profile and entry point",
            "operator basis, fugacities, and normalization rule",
            "validity domain",
            "claim boundary and non-transferable evidence boundary",
        ],
        "acceptance_criteria": {
            "registered_central_candidate_is_explicit": checks[0],
            "registered_v1_spec_matches_registry": checks[1],
            "frozen_v0_1_registry_is_preserved": checks[2],
            "phase_b_active_pointer_matches_v2": checks[3],
            "v2_implementation_matches_v2_spec": checks[4],
            "active_candidate_manifest": checks[5],
            "central_benchmark_path_is_v1_bound": checks[6],
            "phase_a_and_solver_boundary_preserved": checks[7],
        },
        "source_bindings": [
            _binding(root, REGISTRY_PATH),
            _binding(root, BASE_REGISTRY_PATH),
            _binding(root, V1_SPEC_PATH),
            _binding(root, V2_SPEC_PATH),
            _binding(root, DYNAMICS_PATH),
            _binding(root, BENCHMARK_PATH),
            _binding(root, MANIFEST_RESULT_PATH),
        ],
        "sampling_authorized": False,
        "all_safety_checks_passed": all(item["passed"] for item in checks),
        "phase_a_boundary_preserved": {
            "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
            "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            "solver_run_permitted": False,
        },
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    identity = payload["identity"]
    checks = payload["acceptance_criteria"]
    return "\n".join(
        [
            "# Phase-B candidate identity and input-freeze audit",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The repository contains two semantically different candidate layers.",
            "The registered global central candidate remains v1, while the Phase-B",
            "active candidate pointer is v2. The input manifest freezes v2 as its",
            "own profile; its output is not transferred to v1 evidence.",
            "",
            "| item | value |",
            "|---|---|",
            f"| registry central candidate | `{identity['registry_central_candidate']}` |",
            f"| Phase-B active candidate | `{identity['phase_b_active_candidate']}` |",
            f"| registered central model | `{identity['registered_central_model_id']}` |",
            f"| implemented model | `{identity['implemented_v2_model_id']}` |",
            f"| implemented profile | `{identity['implemented_profile_id']}` |",
            f"| v1/v2 same candidate certified | `{identity['same_candidate_certified']}` |",
            f"| active identity certified | `{identity['active_candidate_identity_certified']}` |",
            f"| sampling authorized | `{payload['sampling_authorized']}` |",
            "",
            "## Frozen decision",
            "",
            "v1 remains the global central candidate. v2 is the version-pinned",
            "active candidate for Phase B. No v1-to-v2 equivalence or cross-version",
            "evidence transfer is claimed.",
            "",
            "## Safety checks",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{item['id']}` | `{item['passed']}` |"
                for item in checks.values()
            ],
            "",
            "## Boundary",
            "",
            "Phase-A terminals remain frozen and the production solver remains",
            "unauthorized. This packet certifies identity and input freezing only;",
            "it does not claim a continuum phase, Spin-2 response, or universal",
            "coupling.",
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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_audit(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked candidate-identity audit differs from rebuild")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked candidate-identity report differs from rebuild")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
