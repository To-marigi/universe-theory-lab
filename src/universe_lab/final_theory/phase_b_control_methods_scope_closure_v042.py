"""Record the finite control/methods closure route for the scoped paper.

This module deliberately records a publication scope decision only.  It does
not implement the proposed ideal-count DP, run a sampler, access the
candidate, invoke a solver, or create production trajectories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-control-methods-scope-closure-v2"
PREPARED = "2026-08-20"
STATUS = "PHASE_B_CONTROL_METHODS_SCOPED_MANUSCRIPT_FINALIZED_UPLOAD_PACKAGING_ACTIVE"
START_GATE = "CONTROL_METHODS_SCOPED_MANUSCRIPT_ASSEMBLY"
NEXT_GATE = "ZENODO_UPLOAD_BUNDLE_BUILD_AND_STRICT_VERIFICATION"
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_methods_scope_closure_20260820.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_control_methods_scope_closure_2026-08-20.md"
)
OUTLINE_PATH = Path(
    "reports/v0.4.2_control_methods_scoped_paper_outline_2026-08-17.md"
)
MANUSCRIPT_PATH = Path("paper/v0.4.2_control_methods_scoped/main.tex")

EVIDENCE_PATHS = (
    ("phase_c_completion", "results/v0.4.2_phase_c_method_completion.json"),
    ("bounded_sampler_preflight", "results/v0.4.2_phase_b_sampler_preflight.json"),
    (
        "control_implementation_preflight",
        "results/v0.4.2_phase_b_control_implementation_preflight_20260816.json",
    ),
    (
        "control_cost_preflight",
        "results/v0.4.2_phase_b_control_cost_preflight_20260816.json",
    ),
    (
        "control_scaling_review",
        "results/v0.4.2_phase_b_control_scaling_review_20260816.json",
    ),
    (
        "exact_scaling_design",
        "results/v0.4.2_phase_b_control_exact_scaling_design_20260817.json",
    ),
    (
        "scoped_paper_final_pdf",
        "results/v0.4.2_control_methods_scoped_pdf_final_20260820.json",
    ),
    (
        "hard_supervisor_preflight",
        "results/v0.4.2_phase_b_hard_supervisor_preflight_20260816.json",
    ),
    (
        "candidate_identity_audit",
        "results/v0.4.2_phase_b_candidate_identity.json",
    ),
)


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def build_scope_closure(root: Path) -> dict[str, Any]:
    evidence_chain = []
    for label, relative in EVIDENCE_PATHS:
        artifact = _load_json(root, relative)
        digest = artifact.get("semantic_digest_sha256")
        if not isinstance(digest, str) or not digest:
            raise ValueError(f"{relative} has no semantic digest")
        evidence_chain.append(
            {
                "id": label,
                "artifact": relative,
                "semantic_digest_sha256": digest,
            }
        )

    checks = {
        "phase_c_method_artifact_is_complete": (
            _load_json(
                root, "results/v0.4.2_phase_c_method_completion.json"
            )["verdict"]
            == "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW_CERTIFIED"
        ),
        "bounded_control_replay_is_non_evidentiary": (
            _load_json(root, EVIDENCE_PATHS[1][1])["scientific_verdict_added"]
            is False
        ),
        "minkowski_control_is_preflight_only": (
            _load_json(root, EVIDENCE_PATHS[2][1])["production_sampling_authorized"]
            is False
        ),
        "scaling_boundary_has_primary_independent_match": (
            _load_json(root, EVIDENCE_PATHS[4][1])["certificate_core"]["checks"][
                "primary_replay_cap_boundary_matches"
            ]
            is True
        ),
        "candidate_route_has_no_access": (
            _load_json(root, EVIDENCE_PATHS[8][1])["sampling_authorized"] is False
        ),
        "manuscript_source_exists": (root / MANUSCRIPT_PATH).is_file(),
        "scoped_final_pdf_passed_all_page_qa": (
            _load_json(root, EVIDENCE_PATHS[6][1])["status"]
            == "FINAL_PDF_VISUAL_QA_PASS_UPLOAD_CANDIDATE"
            and _load_json(root, EVIDENCE_PATHS[6][1])["visual_qa"]["status"]
            == "PASS_ALL_PAGES"
        ),
        "no_new_execution_is_recorded": True,
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
            "A control-and-methods-scoped manuscript closure. The paper records "
            "bounded exact controls, replay, supervision, and scaling boundaries; "
            "it does not evaluate the candidate physical model or claim a final "
            "theory."
        ),
        "decision": {
            "methods_scope": "FINALIZED_FOR_UPLOAD_PACKAGING",
            "candidate_route": "EXCLUDED_NOT_EVALUATED",
            "exact_scaling_extension": "DESIGN_ONLY_NOT_EXECUTED",
            "production_measurement": "NOT_AUTHORIZED",
            "solver": "NOT_AUTHORIZED",
            "paper_i_publication": "PRESERVED_IMMUTABLE",
            "manuscript_source": MANUSCRIPT_PATH.as_posix(),
            "pdf_preflight": "PASS_FINAL_UPLOAD_CANDIDATE_NOT_PUBLISHED",
        },
        "claims_supported": [
            "Phase-C claim-boundary and budget-separation controls are complete.",
            "Bounded exact sampler fixtures and independent replay are reproducible.",
            (
                "The Minkowski positive-control implementation preflight is "
                "bounded and non-evidentiary."
            ),
            "Runtime guards and hard-supervisor fixtures fail closed at their declared boundaries.",
            (
                "The random-growth scaling review reaches an exact n=38 down-set "
                "cap boundary with primary/independent agreement."
            ),
            (
            "The candidate weighted route has no certified reduced-state "
                "factorisation and is excluded from this manuscript."
            ),
        ],
        "claims_excluded": [
            "candidate physical validity or continuum-limit evidence",
            "N=60 production control completion",
            "production spectral-dimension or statistical acceptance",
            "BDG weighted-ensemble or action result",
            "full 955/721 resolution or complete finite occurrence-ON semantics lattice",
            "solver impossibility and FINAL_THEORY closure",
        ],
        "checks": checks,
        "evidence_chain": evidence_chain,
        "execution_boundary": {
            "new_control_trajectories": 0,
            "candidate_trajectories": 0,
            "solver_calls": 0,
            "production_sampling_authorized": False,
            "approximate_sampler_authorized": False,
            "scientific_verdict_added": False,
        },
        "reopen_policy": {
            "requires_new_owner_scope": True,
            "requires_versioned_budget": True,
            "requires_independent_replay": True,
            "candidate_route_requires_factorisation_certificate": True,
            "existing_paper_i_record_must_not_be_mutated": True,
        },
        "all_acceptance_checks_passed": all(checks.values()),
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    if not payload["all_acceptance_checks_passed"]:
        raise RuntimeError("control methods scope closure did not pass")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase-B control/methods scope closure",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Decision",
            "",
            "Phase B is closed for assembly of a scoped control-and-methods "
            "manuscript. This is an operational publication-scope decision, "
            "not a physical verdict on the candidate model.",
            "",
            "The exact ideal-count scaling route remains design-only and is not "
            "implemented. The candidate weighted route is excluded because no "
            "certified reduced-state factorisation exists.",
            "",
            "## Supported claims",
            "",
            *[f"- {claim}" for claim in payload["claims_supported"]],
            "",
            "## Explicit non-claims",
            "",
            *[f"- {claim}" for claim in payload["claims_excluded"]],
            "",
            "## Execution boundary",
            "",
            "No new control or candidate trajectories and no solver calls are "
            "created by this packet. Production sampling and approximate "
            "fallbacks remain unauthorized.",
            "",
            "The final manuscript PDF passes a digest-pinned, network-disabled "
            "Docker build and all-page visual QA. It is written locally for "
            "packaging but is not uploaded or published by this packet.",
            "",
            "## Reproducibility and reopening",
            "",
            "The evidence chain is digest-bound to the existing bounded artifacts. "
            "Reopening requires a new owner-approved scope, a versioned budget, "
            "and independent replay; the published Paper I record remains immutable.",
            "",
            f"Manuscript draft: `{MANUSCRIPT_PATH.as_posix()}`",
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
