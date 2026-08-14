"""Freeze the versioned Phase-B input manifest for the v2 candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.dynamics_v02 import CANDIDATE_PROFILE
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-active-candidate-manifest-v1"
PREPARED = "2026-08-15"
ACTIVE_CANDIDATE_ID = "causal_information_v2_sparse_kraus"
RESULT_PATH = Path("results/v0.4.2_phase_b_active_candidate_manifest.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_active_candidate_manifest.md")

BASE_REGISTRY_PATH = Path("Final-Theory-Program/candidates/candidate_registry.json")
REGISTRY_PATH = Path(
    "Final-Theory-Program/candidates/candidate_registry_v042_phase_b.json"
)
V1_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v1/model_spec.json")
V2_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v2/model_spec.json")
DYNAMICS_PATH = Path("src/universe_lab/final_theory/dynamics_v02.py")


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


def build_manifest(root: Path) -> dict[str, Any]:
    """Build a fail-closed manifest from the registered active candidate."""

    base_registry = _load_json(root, BASE_REGISTRY_PATH)
    registry = _load_json(root, REGISTRY_PATH)
    v1 = _load_json(root, V1_SPEC_PATH)
    v2 = _load_json(root, V2_SPEC_PATH)
    dynamics_text = (root / DYNAMICS_PATH).read_text(encoding="utf-8")
    active_candidate_id = registry["active_candidates"]["PHASE_B"]
    active = next(
        candidate
        for candidate in registry["candidates"]
        if candidate["id"] == active_candidate_id
    )
    spec_fugacities = v2["action"]["fugacities"]
    profile_fugacities = {
        "link": CANDIDATE_PROFILE.parameters["link_fugacity"],
        "diamond": CANDIDATE_PROFILE.parameters["diamond_fugacity"],
        "precursor": CANDIDATE_PROFILE.parameters["precursor_fugacity"],
    }
    normalized_spec_fugacities = {
        name: {"numerator": values[0], "denominator": values[1]}
        for name, values in spec_fugacities.items()
    }
    checks = {
        "registry_central_v1_preserved": registry["central_candidate"]
        == "causal_information_v1",
        "v0_1_registry_is_unchanged_baseline": base_registry["schema_version"]
        == "0.1"
        and base_registry["central_candidate"] == "causal_information_v1",
        "phase_b_active_pointer_is_v2": active_candidate_id
        == ACTIVE_CANDIDATE_ID,
        "phase_b_active_candidate_is_registered": active_candidate_id
        == active["id"],
        "v2_spec_id_matches_active_id": v2["model_id"] == ACTIVE_CANDIDATE_ID,
        "implementation_profile_matches_active_id": CANDIDATE_PROFILE.profile_id
        == ACTIVE_CANDIDATE_ID
        and ACTIVE_CANDIDATE_ID in dynamics_text,
        "spec_and_implementation_fugacities_match": normalized_spec_fugacities
        == profile_fugacities,
        "target_dimension_is_forbidden_input": v2["forbidden_inputs"][
            "target_3_plus_1_dimension"
        ]
        is False,
        "v1_is_preserved_without_evidence_transfer": v1["model_id"]
        == "causal_information_v1"
        and active["lineage"]["evidence_transfer_from_predecessor"] is False,
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": "PHASE_B_ACTIVE_CANDIDATE_INPUT_MANIFEST_FROZEN",
        "scientific_status": "FINAL_THEORY_OPEN",
        "active_candidate": {
            "id": ACTIVE_CANDIDATE_ID,
            "registry_role": active["role"],
            "spec_path": V2_SPEC_PATH.as_posix(),
            "implementation_path": DYNAMICS_PATH.as_posix(),
            "entry_points": [
                "universe_lab.final_theory.dynamics_v02:CANDIDATE_PROFILE",
                "universe_lab.final_theory.dynamics_v02:transition_instrument",
                "universe_lab.final_theory.dynamics_v02:propagate_distribution",
            ],
            "formalism": v2["formalism"],
            "state_space": v2["state_space"],
            "validity_domain": v2["validity_domain"],
            "parameters": CANDIDATE_PROFILE.parameters,
            "operator_basis": v2["action"]["operators"],
            "normalization_rule": (
                "per-source aggregate orbit multiplicity times exact rational local "
                "weight, divided by the exact positive source sum"
            ),
        },
        "predecessor_boundary": {
            "id": v1["model_id"],
            "spec_path": V1_SPEC_PATH.as_posix(),
            "relation": "preserved_historical_kinematic_baseline",
            "equivalence_to_active_candidate_certified": False,
            "evidence_transfer_to_active_candidate": False,
        },
        "measurement_boundary": {
            "next_gate": "PHASE_B_CONTINUUM_DIMENSION_DERIVATION_DESIGN",
            "sampling_authorized_by_manifest": False,
            "required_before_sampling": [
                "preregistered dimension estimators",
                "correlation-length observable",
                "finite-size scaling protocol",
                "positive and negative controls",
                "held-out partition",
                "sampler normalization and independent replay",
            ],
        },
        "claim_boundary": (
            "This manifest authorizes only identity and input freezing for the "
            "v2 Phase-B candidate. It does not establish a continuum phase, target "
            "dimension, Spin-2 response, universal coupling, or equivalence to v1."
        ),
        "acceptance_checks": checks,
        "all_acceptance_checks_passed": all(checks.values()),
        "source_bindings": [
            _binding(root, BASE_REGISTRY_PATH),
            _binding(root, REGISTRY_PATH),
            _binding(root, V1_SPEC_PATH),
            _binding(root, V2_SPEC_PATH),
            _binding(root, DYNAMICS_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    checks = payload["acceptance_checks"]
    active = payload["active_candidate"]
    return "\n".join(
        [
            "# Phase-B active candidate input manifest",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Frozen candidate",
            "",
            f"- ID: `{active['id']}`",
            f"- spec: `{active['spec_path']}`",
            f"- implementation: `{active['implementation_path']}`",
            f"- formalism: `{active['formalism']}`",
            f"- validity domain: `{active['validity_domain']}`",
            "",
            "The v2 candidate is now the active Phase-B candidate. v1 remains",
            "a preserved historical kinematic baseline; no cross-version evidence",
            "transfer is certified.",
            "",
            "## Sampling boundary",
            "",
            "The manifest freezes inputs but does not authorize continuum sampling.",
            "The next gate must first freeze the dimension, correlation-length,",
            "scaling, control, held-out, and sampler validation protocol.",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{name}` | `{value}` |"
                for name, value in checks.items()
            ],
            "",
            f"Next gate: `{payload['measurement_boundary']['next_gate']}`",
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
    payload = build_manifest(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked active-candidate manifest differs from rebuild")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked active-candidate report differs from rebuild")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
