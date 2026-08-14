"""Review and close the Phase-C methodology artifact chain."""

from __future__ import annotations

# ruff: noqa: E501 -- recorded acceptance claims are intentionally explicit.
import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from universe_lab.artifact_migration_v038 import line_ending_hashes
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_c_claim_boundary_ledger_v042 import (
    render_report as render_claim_boundary_report,
)
from universe_lab.final_theory.phase_c_frozen_reopen_audit_v042 import (
    render_report as render_frozen_reopen_report,
)
from universe_lab.final_theory.phase_c_verdict_budget_audit_v042 import (
    render_report as render_verdict_budget_report,
)

SCHEMA_VERSION = "final-theory-v042-phase-c-method-completion-v1"
VERDICT = "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW_CERTIFIED"
START_GATE = "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW"
NEXT_GATE = "PHASE_B_REQUIRED_PHYSICS_DERIVATION_GAP_INVENTORY"
RESULT_PATH = Path("results/v0.4.2_phase_c_method_completion.json")
REPORT_PATH = Path("reports/v0.4.2_phase_c_method_completion.md")
STATE_PATH = Path("CURRENT_RESEARCH_STATE.json")

CHARTER_PATH = Path("results/v0.4.2_phase_c_methodology_charter.json")
LEDGER_PATH = Path("results/v0.4.2_phase_c_claim_boundary_ledger.json")
VERDICT_BUDGET_PATH = Path("results/v0.4.2_phase_c_verdict_budget_audit.json")
FROZEN_REOPEN_PATH = Path("results/v0.4.2_phase_c_frozen_reopen_audit.json")

CHARTER_REPORT_PATH = Path("reports/v0.4.2_phase_c_methodology_charter.md")
LEDGER_REPORT_PATH = Path("reports/v0.4.2_phase_c_claim_boundary_ledger.md")
VERDICT_BUDGET_REPORT_PATH = Path("reports/v0.4.2_phase_c_verdict_budget_audit.md")
FROZEN_REOPEN_REPORT_PATH = Path("reports/v0.4.2_phase_c_frozen_reopen_audit.md")

TEST_PATHS = (
    "tests/final_theory/test_v042_phase_a_freeze_and_phase_c.py",
    "tests/final_theory/test_v042_phase_c_claim_boundary_ledger.py",
    "tests/final_theory/test_v042_phase_c_verdict_budget_audit.py",
    "tests/final_theory/test_v042_phase_c_frozen_reopen_audit.py",
    "tests/final_theory/test_v042_solver_authorization.py",
    "tests/final_theory/test_v042_phase_c_method_completion.py",
)


def _load_json(root: Path, relative_path: str | Path) -> dict[str, Any]:
    return json.loads((root / relative_path).read_text(encoding="utf-8"))


def _assert(condition: bool, message: str, evidence: Any = None) -> dict[str, Any]:
    if not condition:
        raise ValueError(message)
    return {"id": message, "passed": True, "evidence": evidence}


def _verified_json(root: Path, relative_path: str | Path) -> tuple[str, dict[str, Any]]:
    payload = _load_json(root, relative_path)
    digest = payload.pop("semantic_digest_sha256", None)
    if digest is None:
        raise ValueError(f"missing semantic digest: {relative_path}")
    if stable_hash(payload) != digest:
        raise ValueError(f"semantic digest mismatch: {relative_path}")
    return digest, payload


def _bind_text(root: Path, relative_path: str) -> dict[str, Any]:
    hashes = line_ending_hashes(root / relative_path, require_canonical_lf=True)
    return {
        "path": relative_path,
        "raw_sha256": hashes["current_raw_sha256"],
        "canonical_lf_sha256": hashes["canonical_lf_sha256"],
        "size_bytes": hashes["current_raw_size_bytes"],
        "strict_utf8_lf": True,
    }


def _artifact_record(
    root: Path,
    *,
    artifact_path: Path,
    report_path: Path,
    expected_status: str,
    renderer: Callable[[dict[str, Any]], str] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    digest, payload = _verified_json(root, artifact_path)
    if payload.get("status") != expected_status:
        raise ValueError(f"unexpected status in {artifact_path}")
    report = (root / report_path).read_text(encoding="utf-8")
    report_renderer_check_applied = renderer is not None
    if report_renderer_check_applied and report != renderer(
        {**payload, "semantic_digest_sha256": digest}
    ):
        raise ValueError(f"report is not generated from {artifact_path}")
    record = {
        "path": artifact_path.as_posix(),
        "report": report_path.as_posix(),
        "status": payload["status"],
        "semantic_digest_sha256": digest,
        "report_present": True,
        "report_renderer_check_applied": report_renderer_check_applied,
        "report_matches_machine_artifact": report_renderer_check_applied,
    }
    return record, payload


def _build_artifact_chain(root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    specs = (
        (
            "charter",
            CHARTER_PATH,
            CHARTER_REPORT_PATH,
            "PHASE_C_METHOD_CHARTER_ACTIVE",
            None,
        ),
        (
            "claim_boundary_ledger",
            LEDGER_PATH,
            LEDGER_REPORT_PATH,
            "PHASE_C_CLAIM_BOUNDARY_LEDGER_AND_FROZEN_ARTIFACT_INDEX_CERTIFIED",
            render_claim_boundary_report,
        ),
        (
            "verdict_budget_audit",
            VERDICT_BUDGET_PATH,
            VERDICT_BUDGET_REPORT_PATH,
            "PHASE_C_VERDICT_GRAMMAR_AND_PREFLIGHT_BUDGET_SEPARATION_CERTIFIED",
            render_verdict_budget_report,
        ),
        (
            "frozen_reopen_audit",
            FROZEN_REOPEN_PATH,
            FROZEN_REOPEN_REPORT_PATH,
            "PHASE_C_FROZEN_ARTIFACT_IMMUTABILITY_AND_REOPEN_AUTHORIZATION_CERTIFIED",
            render_frozen_reopen_report,
        ),
    )
    records: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, artifact_path, report_path, expected_status, renderer in specs:
        record, payload = _artifact_record(
            root,
            artifact_path=artifact_path,
            report_path=report_path,
            expected_status=expected_status,
            renderer=renderer,
        )
        record["id"] = name
        records.append(record)
        payloads[name] = payload
    return records, payloads


def build_review(root: Path) -> dict[str, Any]:
    state = _load_json(root, STATE_PATH)
    phase_c = state["affected_campaign"]["phase_C"]
    if "completion_review" in phase_c:
        _assert(
            phase_c["status"] == "COMPLETE"
            and phase_c["next_gate"] == START_GATE,
            "rebuild_starts_after_phase_c_completion_transition",
            {"status": phase_c["status"], "next_gate": phase_c["next_gate"]},
        )
    else:
        _assert(
            phase_c["status"] == "ACTIVE" and phase_c["next_gate"] == START_GATE,
            "completion_review_starts_at_phase_c_completion_gate",
            {"status": phase_c["status"], "next_gate": phase_c["next_gate"]},
        )

    chain, payloads = _build_artifact_chain(root)
    charter = payloads["charter"]
    ledger = payloads["claim_boundary_ledger"]
    budget = payloads["verdict_budget_audit"]
    frozen = payloads["frozen_reopen_audit"]
    ledger_summary = ledger["inventory_summary"]
    ledger_coverage = ledger["coverage_controls"]
    budget_summary = budget["separation_summary"]
    frozen_summary = frozen["frozen_artifacts"]["summary"]
    reopen = frozen["reopen_authorization"]

    checks = {
        "semantic_identity": [
            _assert(
                all(charter["controls"].values()),
                "charter_declares_semantic_identity_control",
                charter["controls"],
            ),
            _assert(
                ledger_summary["all_machine_semantic_digests_verified"] is True,
                "ledger_rechecks_all_machine_semantic_digests",
                ledger_summary["machine_evidence_count"],
            ),
            _assert(
                frozen_summary["all_json_semantic_digests_match"] is True,
                "frozen_reopen_audit_rechecks_json_semantic_digests",
                frozen_summary["frozen_file_count"],
            ),
        ],
        "claim_boundary_ledger": [
            _assert(
                all(ledger_coverage[key] for key in (
                    "all_charter_frozen_inputs_indexed",
                    "all_decision_packet_evidence_indexed",
                    "all_freeze_record_evidence_indexed",
                    "all_predecessor_group_ids_valid",
                )),
                "claim_boundary_ledger_has_complete_required_path_coverage",
                ledger_coverage,
            ),
            _assert(
                ledger["global_verdict"] == "FINAL_THEORY_OPEN"
                and ledger["scientific_verdict_added"] is False
                and ledger["complete_finite_on_semantics_lattice_claim_available"] is False,
                "claim_boundary_ledger_preserves_open_scientific_boundary",
                ledger["phase_a_boundaries"],
            ),
        ],
        "verdict_grammar": [
            _assert(
                budget["grammar"]["passed"] is True,
                "verdict_grammar_audit_passed",
                budget["grammar"]["rules"],
            ),
            _assert(
                "not witness" in budget["grammar"]["rules"]["OPEN_RESOURCE_LIMIT"],
                "resource_limit_is_not_promoted_to_witness",
                budget["grammar"]["rules"]["OPEN_RESOURCE_LIMIT"],
            ),
        ],
        "frozen_artifacts_and_budget_separation": [
            _assert(
                all(
                    frozen_summary[key]
                    for key in (
                        "all_raw_sha256_match",
                        "all_canonical_lf_sha256_match",
                        "all_sizes_match",
                        "all_strict_utf8_lf",
                        "mutable_live_state_excluded",
                        "audit_outputs_excluded",
                    )
                ),
                "frozen_artifact_bindings_are_immutable_and_non_self_referential",
                frozen_summary,
            ),
            _assert(
                budget_summary["production_solver_authorised_count"] == 0
                and budget_summary["production_solver_run_count"] == 0
                and budget_summary["no_default_budget_fallback_used"] is True,
                "preflight_and_budget_records_are_non_authorizing",
                budget_summary,
            ),
            _assert(
                reopen["requirements"]["runtime_gate_blocks_current_state"] is True
                and reopen["requirements"]["current_reopen_authorized"] is False,
                "runtime_reopen_gate_remains_closed",
                reopen["runtime_production_gate"],
            ),
        ],
        "global_boundary": [
            _assert(
                state["global_verdict"] == "FINAL_THEORY_OPEN",
                "live_global_verdict_remains_final_theory_open",
                state["global_verdict"],
            ),
            _assert(
                state["affected_campaign"]["solver_run_permitted"] is False,
                "live_solver_permission_remains_false",
                state["affected_campaign"]["solver_run_permitted"],
            ),
            _assert(
                all(
                    payload["global_verdict"] == "FINAL_THEORY_OPEN"
                    and payload["scientific_verdict_added"] is False
                    for payload in (ledger, budget, frozen)
                ),
                "phase_c_artifacts_add_no_scientific_verdict",
                [record["id"] for record in chain],
            ),
        ],
    }
    all_checks = [check for group in checks.values() for check in group]
    test_bindings = [_bind_text(root, path) for path in TEST_PATHS]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": "2026-08-14",
        "evidence_head": "e8c3d02",
        "status": VERDICT,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "artifact_chain": chain,
        "acceptance_criteria": {
            "semantic_identity": {
                "status": "SATISFIED",
                "checks": checks["semantic_identity"],
            },
            "claim_boundary_ledger": {
                "status": "SATISFIED",
                "checks": checks["claim_boundary_ledger"],
            },
            "verdict_grammar": {
                "status": "SATISFIED",
                "checks": checks["verdict_grammar"],
            },
            "frozen_artifacts_and_budget_separation": {
                "status": "SATISFIED",
                "checks": checks["frozen_artifacts_and_budget_separation"],
            },
        },
        "verification_surface": {
            "test_files": test_bindings,
            "test_file_count": len(test_bindings),
            "all_test_files_strict_utf8_lf": all(
                binding["strict_utf8_lf"] for binding in test_bindings
            ),
        },
        "phase_a_boundary_preserved": {
            "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
            "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            "both_full_profiles_resolved": False,
            "solver_run_permitted": False,
        },
        "phase_b_transition": {
            "phase_b_was_deferred_until_phase_c": charter["phase_b_deferred"],
            "phase_b_started_by_this_review": False,
            "scope": "required physics derivation audit, not deeper computation of frozen 955/721 profiles",
            "next_gate": NEXT_GATE,
        },
        "all_acceptance_checks_passed": all(check["passed"] for check in all_checks),
        "next_gate": NEXT_GATE,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    rows = []
    for name, criterion in payload["acceptance_criteria"].items():
        rows.append(f"| `{name}` | `{criterion['status']}` | {len(criterion['checks'])} |")
    return "\n".join(
        [
            "# Phase C method-artifact completion review",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The Phase-C methodology artifact is complete. This review closes the",
            "methods work only: it does not solve, reopen, or reinterpret the frozen",
            "955 and 721 scientific profiles.",
            "",
            "All four charter controls are satisfied by independently digest-checked",
            "artifacts, machine-readable claim boundaries, verdict grammar, frozen-file",
            "invariance, and preflight/budget separation.",
            "",
            "| acceptance criterion | status | checks |",
            "|---|---|---:|",
            *rows,
            "",
            "## Evidence chain",
            "",
            *[
                f"- `{record['id']}`: `{record['status']}`; digest `{record['semantic_digest_sha256']}`"
                for record in payload["artifact_chain"]
            ],
            "",
            "The completion review also verifies that the runtime production-solver",
            "gate remains closed. The live state still has `solver_run_permitted=false`,",
            "no reopen approval, no reopen budget, and no full-profile solver run.",
            "",
            "## Phase-B boundary",
            "",
            "Phase B is now the next phase, but it is not started by this packet. Its",
            "first gate is a gap inventory for the required physics derivations. It must",
            "not deepen the frozen finite 955/721 computation under a new name.",
            "",
            "## Scientific boundary",
            "",
            "The global verdict remains `FINAL_THEORY_OPEN`. No complete finite ON",
            "semantics lattice, witness, obstruction, empty-set result, or solver",
            "impossibility claim is added.",
            "",
            "## Next gate",
            "",
            f"`{payload['next_gate']}`",
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
    payload = build_review(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked Phase-C completion review differs from rebuilt payload")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(payload):
            raise SystemExit("tracked Phase-C completion report differs from rebuilt report")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
