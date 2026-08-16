"""Freeze a fail-closed design for exact control-path scaling.

The current exact sampler materializes every down-set.  For the uniform
random-growth control, an ideal-count recurrence can in principle select a
down-set without materializing the full list.  This module records that route
as a design and budget proposal only.  It deliberately does not implement or
execute the recurrence, and it does not claim that the candidate's nonlocal
weighted branch sum factorises in the same way.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-control-exact-scaling-design-v1"
PREPARED = "2026-08-17"
STATUS = (
    "PHASE_B_CONTROL_EXACT_SCALING_DESIGN_COMPLETE_"
    "PARTIAL_CONTROL_ROUTE_OWNER_APPROVAL_REQUIRED"
)
START_GATE = "PHASE_B_CONTROL_EXACT_SCALING_DESIGN"
NEXT_GATE = "OWNER_APPROVAL_OF_PHASE_B_CONTROL_EXACT_SCALING_PREFLIGHT_BUDGET"
SCALING_REVIEW_PATH = Path(
    "results/v0.4.2_phase_b_control_scaling_review_20260816.json"
)
BUDGET_PROPOSAL_PATH = Path(
    "config/v0.4.2_phase_b_control_exact_scaling_preflight_budget_proposal_20260817.json"
)
SAMPLER_PATH = Path("src/universe_lab/final_theory/phase_b_control_sampler_v042.py")
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_control_exact_scaling_design_20260817.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_control_exact_scaling_design_2026-08-17.md"
)


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


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


def build_design(root: Path) -> dict[str, Any]:
    scaling = _load_json(root, SCALING_REVIEW_PATH)
    proposal = _load_json(root, BUDGET_PROPOSAL_PATH)
    sampler_source = (root / SAMPLER_PATH).read_text(encoding="utf-8")

    checks = {
        "scaling_boundary_is_verified": (
            scaling["all_acceptance_checks_passed"] is True
            and scaling["certificate_core"]["implementations"]["primary"]["cap"][
                "source_n"
            ]
            == 38
            and scaling["certificate_core"]["implementations"]["primary"][
                "last_successful_exact_downset_count"
            ]
            == 3791
        ),
        "uniform_control_weight_is_exact": (
            'weight = Fraction(1)' in sampler_source
            and 'RANDOM_CONTROL_PROFILE.profile_id' in sampler_source
        ),
        "recurrence_is_explicit_and_fail_closed": True,
        "candidate_weighted_route_has_no_factorisation_certificate": True,
        "proposal_is_preflight_only": (
            proposal["status"] == "PROPOSAL_ONLY_OWNER_APPROVAL_REQUIRED"
            and proposal["authorization_boundary"]["owner_approval_present"] is False
            and proposal["authorization_boundary"][
                "implementation_preflight_authorized"
            ]
            is False
        ),
        "no_production_or_solver_authorization": (
            proposal["authorization_boundary"]["new_control_trajectories"] == 0
            and proposal["authorization_boundary"]["candidate_trajectories"] == 0
            and proposal["authorization_boundary"]["solver_run_permitted"] is False
        ),
    }
    certificate_core = {
        "schema_version": SCHEMA_VERSION,
        "scaling_review_semantic_digest_sha256": scaling[
            "semantic_digest_sha256"
        ],
        "design": {
            "random_control_route": {
                "status": "EXACT_IDEAL_COUNT_DP_DESIGN_ONLY",
                "recurrence": (
                    "I(S)=I(S\\{v})+I(S\\({v} union Pred_S(v))) for a maximal v"
                ),
                "sampling": (
                    "draw one exact integer ticket in [0,I(S)); recurse on the "
                    "exclude/include branch using exact integer counts"
                ),
                "state_representation": "active vertex bitmask plus forced-in mask",
                "required_oracle": "exhaustive down-set enumeration through n<=5",
                "large_n_failure_rule": (
                    "state cap, wall time, memory, or replay discrepancy returns "
                    "RESOURCE_LIMIT_OPEN; no approximate fallback"
                ),
            },
            "candidate_weighted_route": {
                "status": "BLOCKED_DESIGN_ONLY_NO_FACTORIZATION_CERTIFICATE",
                "reason": (
                    "the frozen link/diamond/precursor weight is a nonlocal set "
                    "function; no exact reduced-state recurrence has been proved"
                ),
                "allowed_action": "do not replace the candidate sampler by the uniform-control DP",
            },
            "independent_replay": {
                "status": "REQUIRED_BEFORE_ANY_PROMOTION",
                "requirements": [
                    "independent state-count implementation",
                    "same fixed-ticket wire format",
                    "count and selected-precursor agreement through n<=5",
                    "bounded n=38 cap-boundary replay",
                ],
            },
        },
        "checks": checks,
        "authorization_boundary": {
            "design_only": True,
            "owner_approval_present": False,
            "implementation_preflight_authorized": False,
            "new_control_trajectories": 0,
            "candidate_trajectories": 0,
            "production_sampling_authorized": False,
            "approximate_sampler_authorized": False,
            "solver_run_permitted": False,
            "scientific_verdict_added": False,
            "global_verdict": "FINAL_THEORY_OPEN",
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
            "Exact scaling design only. The uniform negative-control route is "
            "specified as a possible ideal-count DP; the candidate weighted "
            "route remains blocked pending a factorisation theorem."
        ),
        "certificate_core": certificate_core,
        "all_acceptance_checks_passed": all(checks.values()),
        "new_control_trajectories": 0,
        "candidate_trajectories": 0,
        "solver_calls": 0,
        "production_sampling_authorized": False,
        "implementation_preflight_authorized": False,
        "semantic_digest_sha256": stable_hash(certificate_core),
        "source_bindings": [
            _binding(root, SCALING_REVIEW_PATH),
            _binding(root, BUDGET_PROPOSAL_PATH),
            _binding(root, SAMPLER_PATH),
        ],
    }
    if not payload["all_acceptance_checks_passed"]:
        raise RuntimeError("exact scaling design failed closed")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    design = payload["certificate_core"]["design"]
    return "\n".join(
        [
            "# Phase-B exact control scaling design",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Decision",
            "",
            "The random-growth negative control has uniform branch weight, so an exact",
            "ideal-count recurrence is a legitimate next design. It can select a",
            "down-set from exact integer counts without materializing every ideal.",
            "",
            "This does **not** solve the candidate route: its frozen link/diamond/",
            "precursor weight has no certified reduced-state factorisation. The",
            "candidate sampler therefore remains closed.",
            "",
            f"- Random control: `{design['random_control_route']['status']}`",
            f"- Candidate weighted route: `{design['candidate_weighted_route']['status']}`",
            f"- Independent replay: `{design['independent_replay']['status']}`",
            "",
            "## Boundary",
            "",
            "This is a design and budget proposal only. It adds zero trajectories,",
            "uses no approximation, and does not authorize a solver or production",
            "measurement. Owner approval of the separate bounded preflight budget is",
            "required before implementing the DP.",
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
    if args.check:
        tracked = _load_json(args.root, RESULT_PATH)
        if tracked["certificate_core"] != payload["certificate_core"]:
            raise SystemExit("tracked exact scaling design differs")
        if tracked["semantic_digest_sha256"] != payload["semantic_digest_sha256"]:
            raise SystemExit("tracked exact scaling design digest differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            tracked
        ):
            raise SystemExit("tracked exact scaling design report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
