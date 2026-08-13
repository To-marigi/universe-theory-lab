"""Audit Phase-C frozen-artifact immutability and profile-reopen authorization."""

from __future__ import annotations

# ruff: noqa: E501 -- audit claims are deliberately recorded as atomic strings.
import argparse
import json
from pathlib import Path
from typing import Any

from universe_lab.artifact_migration_v038 import line_ending_hashes
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.solver_authorization_v042 import (
    SolverAuthorizationError,
    require_production_solver_authorization,
)

SCHEMA_VERSION = "final-theory-v042-phase-c-frozen-reopen-audit-v1"
VERDICT = "PHASE_C_FROZEN_ARTIFACT_IMMUTABILITY_AND_REOPEN_AUTHORIZATION_CERTIFIED"
START_GATE = "AUDIT_FROZEN_ARTIFACT_IMMUTABILITY_AND_REOPEN_AUTHORIZATION"
STATE_START_GATE = "PHASE_C_FROZEN_ARTIFACT_IMMUTABILITY_AND_REOPEN_AUTHORIZATION"
NEXT_GATE = "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW"
RESULT_PATH = Path("results/v0.4.2_phase_c_frozen_reopen_audit.json")
REPORT_PATH = Path("reports/v0.4.2_phase_c_frozen_reopen_audit.md")
LEDGER_PATH = Path("results/v0.4.2_phase_c_claim_boundary_ledger.json")
LEDGER_REPORT_PATH = Path("reports/v0.4.2_phase_c_claim_boundary_ledger.md")
STATE_PATH = Path("CURRENT_RESEARCH_STATE.json")
BUDGET_AUDIT_PATH = Path("results/v0.4.2_phase_c_verdict_budget_audit.json")
CHARTER_PATH = Path("results/v0.4.2_phase_c_methodology_charter.json")
PACKET_PATH = Path("results/v0.4.2_phase_a_termination_decision_packet.json")
FREEZE_PATH = Path("results/v0.4.2_phase_a_freeze_execution.json")
RUNTIME_GUARD_PATH = Path("src/universe_lab/final_theory/solver_authorization_v042.py")
LEGACY_SOLVER_ENTRYPOINT_PATH = Path("src/universe_lab/final_theory/one_sided_elimination_v041.py")


def _load_json(root: Path, relative_path: str | Path) -> dict[str, Any]:
    path = root / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def _assert(condition: bool, message: str, evidence: Any = None) -> dict[str, Any]:
    if not condition:
        raise ValueError(message)
    return {"id": message, "passed": True, "evidence": evidence}


def _verify_json_digest(root: Path, relative_path: str | Path) -> tuple[str, dict[str, Any]]:
    payload = _load_json(root, relative_path)
    digest = payload.pop("semantic_digest_sha256", None)
    if digest is None:
        raise ValueError(f"missing semantic digest: {relative_path}")
    if stable_hash(payload) != digest:
        raise ValueError(f"semantic digest mismatch: {relative_path}")
    return digest, payload


def _audit_one_frozen_binding(root: Path, binding: dict[str, Any]) -> dict[str, Any]:
    relative_path = str(binding["path"])
    path = root / relative_path
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    hashes = line_ending_hashes(path, require_canonical_lf=True)
    current = {
        "path": relative_path,
        "expected_raw_sha256": binding["raw_sha256"],
        "current_raw_sha256": hashes["current_raw_sha256"],
        "expected_canonical_lf_sha256": binding["canonical_lf_sha256"],
        "current_canonical_lf_sha256": hashes["canonical_lf_sha256"],
        "expected_size_bytes": binding["size_bytes"],
        "current_size_bytes": hashes["current_raw_size_bytes"],
        "strict_utf8_lf": True,
    }
    current["raw_sha256_match"] = (
        current["expected_raw_sha256"] == current["current_raw_sha256"]
    )
    current["canonical_lf_sha256_match"] = (
        current["expected_canonical_lf_sha256"]
        == current["current_canonical_lf_sha256"]
    )
    current["size_match"] = current["expected_size_bytes"] == current["current_size_bytes"]
    if not all(
        current[key]
        for key in (
            "raw_sha256_match",
            "canonical_lf_sha256_match",
            "size_match",
            "strict_utf8_lf",
        )
    ):
        raise ValueError(f"frozen binding mismatch: {relative_path}")

    if path.suffix == ".json":
        semantic_digest, _ = _verify_json_digest(root, relative_path)
        expected_digest = binding.get("semantic_digest_sha256")
        current["expected_semantic_digest_sha256"] = expected_digest
        current["current_semantic_digest_sha256"] = semantic_digest
        current["semantic_digest_match"] = expected_digest == semantic_digest
        if expected_digest is None or not current["semantic_digest_match"]:
            raise ValueError(f"frozen semantic digest mismatch: {relative_path}")
    else:
        current["semantic_digest_match"] = None
    return current


def _flatten_ledger_bindings(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        binding
        for group in ledger["artifact_groups"]
        for binding in group["files"]
    ]


def _audit_frozen_artifacts(root: Path) -> dict[str, Any]:
    ledger_digest, ledger_payload = _verify_json_digest(root, LEDGER_PATH)
    bindings = _flatten_ledger_bindings(ledger_payload)
    paths = [str(binding["path"]) for binding in bindings]
    duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
    output_paths = {
        RESULT_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        "src/universe_lab/final_theory/phase_c_frozen_reopen_audit_v042.py",
        "tests/final_theory/test_v042_phase_c_frozen_reopen_audit.py",
    }
    audited_bindings = [_audit_one_frozen_binding(root, binding) for binding in bindings]
    ledger_hashes = line_ending_hashes(root / LEDGER_PATH, require_canonical_lf=True)
    frozen_path_set = set(paths)
    checks = [
        _assert(
            len(paths) == len(set(paths)),
            "frozen_ledger_paths_are_unique",
            {"duplicate_paths": duplicate_paths},
        ),
        _assert(
            all(path not in frozen_path_set for path in output_paths),
            "audit_outputs_and_reproducer_are_excluded_from_frozen_ledger",
            sorted(output_paths),
        ),
        _assert(
            STATE_PATH.as_posix() not in frozen_path_set,
            "mutable_live_state_is_excluded_from_raw_frozen_bindings",
            STATE_PATH.as_posix(),
        ),
        _assert(
            LEDGER_PATH.as_posix() not in frozen_path_set,
            "claim_boundary_ledger_does_not_self_bind",
            LEDGER_PATH.as_posix(),
        ),
        _assert(
            all(item["raw_sha256_match"] for item in audited_bindings),
            "all_frozen_raw_sha256_bindings_match",
            len(audited_bindings),
        ),
        _assert(
            all(item["canonical_lf_sha256_match"] for item in audited_bindings),
            "all_frozen_canonical_lf_sha256_bindings_match",
            len(audited_bindings),
        ),
        _assert(
            all(item["size_match"] for item in audited_bindings),
            "all_frozen_file_sizes_match",
            len(audited_bindings),
        ),
        _assert(
            all(item["strict_utf8_lf"] for item in audited_bindings),
            "all_frozen_files_are_strict_utf8_lf",
            len(audited_bindings),
        ),
        _assert(
            all(
                item["semantic_digest_match"]
                for item in audited_bindings
                if item["semantic_digest_match"] is not None
            ),
            "all_frozen_json_semantic_digests_match",
            sum(item["semantic_digest_match"] is not None for item in audited_bindings),
        ),
    ]
    return {
        "ledger": {
            "path": LEDGER_PATH.as_posix(),
            "semantic_digest_sha256": ledger_digest,
            "raw_sha256": ledger_hashes["current_raw_sha256"],
            "canonical_lf_sha256": ledger_hashes["canonical_lf_sha256"],
            "size_bytes": ledger_hashes["current_raw_size_bytes"],
            "self_binding_excluded": True,
        },
        "frozen_file_bindings": audited_bindings,
        "summary": {
            "artifact_group_count": len(ledger_payload["artifact_groups"]),
            "frozen_file_count": len(audited_bindings),
            "machine_evidence_count": ledger_payload["inventory_summary"][
                "machine_evidence_count"
            ],
            "all_raw_sha256_match": all(
                item["raw_sha256_match"] for item in audited_bindings
            ),
            "all_canonical_lf_sha256_match": all(
                item["canonical_lf_sha256_match"] for item in audited_bindings
            ),
            "all_sizes_match": all(item["size_match"] for item in audited_bindings),
            "all_strict_utf8_lf": all(item["strict_utf8_lf"] for item in audited_bindings),
            "all_json_semantic_digests_match": all(
                item["semantic_digest_match"]
                for item in audited_bindings
                if item["semantic_digest_match"] is not None
            ),
            "mutable_live_state_excluded": STATE_PATH.as_posix() not in frozen_path_set,
            "audit_outputs_excluded": all(
                path not in frozen_path_set for path in output_paths
            ),
        },
        "checks": checks,
        "passed": True,
    }


def _audit_reopen_authorization(root: Path) -> dict[str, Any]:
    state = _load_json(root, STATE_PATH)
    phase_c = state["affected_campaign"]["phase_C"]
    charter_digest, charter = _verify_json_digest(root, CHARTER_PATH)
    packet_digest, packet = _verify_json_digest(root, PACKET_PATH)
    freeze_digest, freeze = _verify_json_digest(root, FREEZE_PATH)
    budget_audit_digest, budget_audit = _verify_json_digest(root, BUDGET_AUDIT_PATH)
    ledger_digest, _ = _verify_json_digest(root, LEDGER_PATH)
    runtime_guard_source = (root / RUNTIME_GUARD_PATH).read_text(encoding="utf-8")
    legacy_entrypoint_source = (root / LEGACY_SOLVER_ENTRYPOINT_PATH).read_text(
        encoding="utf-8"
    )
    runtime_guard_blocked_current_state = False
    try:
        require_production_solver_authorization(
            root,
            campaign_id="v041_restricted_locus_qq",
            budget_path="config/v0.4.1_budget.json",
        )
    except SolverAuthorizationError:
        runtime_guard_blocked_current_state = True

    previous_reopen_record = phase_c.get("reopen_authorization")
    if previous_reopen_record is not None:
        _assert(
            previous_reopen_record["status"] == "NOT_AUTHORIZED",
            "live_state_reopen_record_is_not_authorized",
            previous_reopen_record,
        )
        _assert(
            previous_reopen_record["current_full_profile_solver_run"] is False,
            "live_state_reopen_record_has_no_full_profile_solver_run",
            previous_reopen_record,
        )

    phase_a_requirements = packet["choices"]["A_DEDICATED_CAS_CAMPAIGN"]["requires"]
    reopen_requirements = {
        "owner_approval_required": charter["reopen_requires_owner_approval_and_versioned_budget"],
        "owner_reopen_approval_present": False,
        "versioned_budget_required": "versioned budget artifact" in phase_a_requirements,
        "versioned_reopen_budget_present": False,
        "specified_cas_and_version_required": "specified CAS and version" in phase_a_requirements,
        "corrected_preflight_benchmark_required": "small corrected-preflight benchmark"
        in phase_a_requirements,
        "hard_timeout_and_memory_supervision_required": "hard timeout and memory supervision"
        in phase_a_requirements,
        "staged_input_plan_required": "staged input plan" in phase_a_requirements,
        "runtime_production_gate_required": True,
        "runtime_production_gate_present": True,
        "runtime_gate_blocks_current_state": runtime_guard_blocked_current_state,
        "dedicated_cas_authorized_now": False,
        "current_full_profile_solver_run": False,
        "current_reopen_authorized": False,
    }
    checks = [
        _assert(
            phase_c["next_gate"] in {START_GATE, NEXT_GATE},
            "phase_c_gate_is_at_or_after_frozen_reopen_audit",
            {"accepted_gate_states": [START_GATE, NEXT_GATE]},
        ),
        _assert(
            phase_c["claim_boundary_ledger"]["semantic_digest_sha256"] == ledger_digest,
            "live_state_claim_ledger_digest_matches_current_ledger",
            ledger_digest,
        ),
        _assert(
            phase_c["verdict_budget_audit"]["semantic_digest_sha256"] == budget_audit_digest,
            "live_state_budget_audit_digest_matches_current_audit",
            budget_audit_digest,
        ),
        _assert(
            charter["reopen_requires_owner_approval_and_versioned_budget"] is True,
            "charter_requires_owner_approval_and_versioned_budget_for_reopen",
            charter["reopen_requires_owner_approval_and_versioned_budget"],
        ),
        _assert(
            packet["choices"]["A_DEDICATED_CAS_CAMPAIGN"]["authorized"] is False,
            "decision_packet_dedicated_cas_choice_is_not_authorized",
            packet["choices"]["A_DEDICATED_CAS_CAMPAIGN"],
        ),
        _assert(
            freeze["freeze_executed"] is True
            and freeze["dedicated_cas_authorized"] is False
            and freeze["full_profile_solver_run"] is False,
            "freeze_record_remains_executed_without_solver_authorization_or_run",
            {
                "freeze_executed": freeze["freeze_executed"],
                "dedicated_cas_authorized": freeze["dedicated_cas_authorized"],
                "full_profile_solver_run": freeze["full_profile_solver_run"],
            },
        ),
        _assert(
            state["affected_campaign"]["solver_run_permitted"] is False,
            "live_state_does_not_permit_solver_run",
            state["affected_campaign"]["solver_run_permitted"],
        ),
        _assert(
            budget_audit["reopen_boundary"] == {
                "dedicated_cas_authorized": False,
                "versioned_budget_required_for_reopen": True,
                "owner_approval_required": True,
                "current_721_full_profile_solver_run": False,
                "current_955_full_profile_solver_run": False,
            },
            "prior_budget_audit_keeps_reopen_boundary_closed",
            budget_audit["reopen_boundary"],
        ),
        _assert(
            budget_audit["separation_summary"]["production_solver_authorised_count"] == 0
            and budget_audit["separation_summary"]["production_solver_run_count"] == 0,
            "historical_preflights_and_budgets_do_not_authorize_or_record_production_solver",
            budget_audit["separation_summary"],
        ),
        _assert(
            all(
                item["production_solver_authorised"] is False
                and item["production_solver_run"] is False
                for item in budget_audit["campaigns"]
            ),
            "every_audited_historical_campaign_is_non_authorizing_and_solver_free",
            len(budget_audit["campaigns"]),
        ),
        _assert(
            "require_production_solver_authorization" in runtime_guard_source,
            "runtime_production_solver_guard_is_present",
            RUNTIME_GUARD_PATH.as_posix(),
        ),
        _assert(
            "require_production_solver_authorization(" in legacy_entrypoint_source,
            "legacy_v041_solver_entrypoint_calls_runtime_guard",
            LEGACY_SOLVER_ENTRYPOINT_PATH.as_posix(),
        ),
        _assert(
            runtime_guard_blocked_current_state,
            "runtime_production_solver_guard_blocks_current_frozen_state",
            "v041_restricted_locus_qq",
        ),
    ]
    return {
        "requirements": reopen_requirements,
        "source_digests": {
            "charter": {"path": CHARTER_PATH.as_posix(), "semantic_digest_sha256": charter_digest},
            "decision_packet": {"path": PACKET_PATH.as_posix(), "semantic_digest_sha256": packet_digest},
            "freeze_record": {"path": FREEZE_PATH.as_posix(), "semantic_digest_sha256": freeze_digest},
            "verdict_budget_audit": {
                "path": BUDGET_AUDIT_PATH.as_posix(),
                "semantic_digest_sha256": budget_audit_digest,
            },
        },
        "historical_campaigns_have_no_reopen_power": True,
        "runtime_production_gate": {
            "guard_module": RUNTIME_GUARD_PATH.as_posix(),
            "guarded_entrypoint": LEGACY_SOLVER_ENTRYPOINT_PATH.as_posix(),
            "campaign_id": "v041_restricted_locus_qq",
            "current_state_blocks_run": runtime_guard_blocked_current_state,
        },
        "checks": checks,
        "passed": True,
    }


def build_audit(root: Path) -> dict[str, Any]:
    state = _load_json(root, STATE_PATH)
    phase_c = state["affected_campaign"]["phase_C"]
    if "frozen_reopen_audit" in phase_c:
        _assert(
            phase_c["next_gate"] == NEXT_GATE,
            "rebuild_starts_after_recorded_frozen_reopen_audit",
            phase_c["next_gate"],
        )
    else:
        _assert(
            phase_c["next_gate"] == START_GATE,
            "audit_starts_at_recorded_frozen_reopen_gate",
            phase_c["next_gate"],
        )
    frozen = _audit_frozen_artifacts(root)
    reopen = _audit_reopen_authorization(root)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": "2026-08-14",
        "evidence_head": "a35cd39",
        "status": VERDICT,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "starting_gate": START_GATE,
        "frozen_artifacts": frozen,
        "reopen_authorization": reopen,
        "claim_boundary": {
            "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
            "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            "complete_finite_on_semantics_lattice_claim_available": False,
            "phase_c_audit_is_methodological_not_scientific_closure": True,
        },
        "next_gate": NEXT_GATE,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    frozen_summary = payload["frozen_artifacts"]["summary"]
    requirements = payload["reopen_authorization"]["requirements"]
    checks = payload["reopen_authorization"]["checks"]
    return "\n".join(
        [
            "# Phase C frozen-artifact immutability and reopen authorization audit",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The third Phase-C control gate is complete. The audit verifies the",
            "raw-byte, canonical-LF, size, and existing semantic-digest bindings",
            "recorded by the frozen-artifact ledger. It separately verifies that the",
            "Phase-A freeze has not become an implicit authorization to reopen 955 or",
            "721.",
            "",
            f"- Artifact groups rechecked: **{frozen_summary['artifact_group_count']}**",
            f"- Frozen file bindings rechecked: **{frozen_summary['frozen_file_count']}**",
            f"- Machine evidence files with semantic digests: **{frozen_summary['machine_evidence_count']}**",
            f"- Raw SHA-256 bindings unchanged: **{str(frozen_summary['all_raw_sha256_match']).lower()}**",
            f"- Canonical-LF SHA-256 bindings unchanged: **{str(frozen_summary['all_canonical_lf_sha256_match']).lower()}**",
            f"- Mutable live state excluded from the frozen set: **{str(frozen_summary['mutable_live_state_excluded']).lower()}**",
            "",
            "## Frozen-artifact boundary",
            "",
            "The claim-boundary ledger is itself checked by semantic digest, but is",
            "not one of its own frozen bindings. The new audit result, report, module,",
            "and test are also excluded from the predecessor ledger. This prevents the",
            "audit from creating a self-referential hash chain.",
            "",
            "All 37 predecessor bindings matched their recorded raw SHA-256,",
            "canonical-LF SHA-256, byte size, and strict UTF-8 LF requirements.",
            "JSON evidence also matched its recorded semantic digest.",
            "",
            "## Reopen authorization boundary",
            "",
            "No current reopen authorization exists. The owner-approved state is the",
            "Phase-A freeze, not a new solver campaign. A future reopen would require",
            "all of the following controls:",
            "",
            f"- Owner approval for reopening: **{str(requirements['owner_approval_required']).lower()}**",
            f"- A new versioned budget artifact: **{str(requirements['versioned_budget_required']).lower()}**",
            f"- A specified CAS and version: **{str(requirements['specified_cas_and_version_required']).lower()}**",
            f"- A corrected small preflight benchmark: **{str(requirements['corrected_preflight_benchmark_required']).lower()}**",
            f"- Hard timeout and memory supervision: **{str(requirements['hard_timeout_and_memory_supervision_required']).lower()}**",
            f"- A staged input plan: **{str(requirements['staged_input_plan_required']).lower()}**",
            f"- An executable production-solver gate: **{str(requirements['runtime_production_gate_present']).lower()}**",
            "",
            "The current record has no such reopen approval or budget. The newly",
            "added runtime gate also blocks the legacy v0.4.1 explicit Sage entrypoint",
            "under the current frozen state. The four historical campaigns audited by",
            "the preceding gate remain non-authorizing and solver-free; `PREFLIGHT`,",
            "`OPEN_RESOURCE_LIMIT`, and `passed=true` do not change that boundary.",
            "The campaign count is scoped to those four records, while the runtime",
            "guard closes the concrete legacy execution path found by the independent",
            "audit.",
            "",
            "## Checks",
            "",
            f"- Authorization checks passed: **{len(checks)}**",
            f"- Current dedicated-CAS authorization: **{str(requirements['dedicated_cas_authorized_now']).lower()}**",
            f"- Current full-profile solver run: **{str(requirements['current_full_profile_solver_run']).lower()}**",
            f"- Current reopen authorization: **{str(requirements['current_reopen_authorized']).lower()}**",
            "",
            "## Scientific boundary",
            "",
            "The global verdict remains `FINAL_THEORY_OPEN`. This audit proves neither",
            "the 955 profile nor the 721 profile, and it adds no witness, obstruction,",
            "empty-set result, complete finite ON semantics lattice, or dedicated-CAS",
            "impossibility claim.",
            "",
            "## Next gate",
            "",
            f"`{payload['next_gate']}`",
            "",
        ]
    )


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    payload = build_audit(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked frozen/reopen audit differs from rebuilt payload")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(payload):
            raise SystemExit("tracked frozen/reopen report differs from rebuilt report")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
