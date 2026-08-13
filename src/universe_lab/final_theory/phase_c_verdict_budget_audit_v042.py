"""Audit Phase-C verdict grammar and preflight/budget separation."""

from __future__ import annotations

# ruff: noqa: E501 -- audit messages are deliberately atomic recorded claims.
import argparse
import json
from pathlib import Path
from typing import Any

from universe_lab.artifact_migration_v038 import line_ending_hashes
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-c-verdict-budget-audit-v1"
VERDICT = "PHASE_C_VERDICT_GRAMMAR_AND_PREFLIGHT_BUDGET_SEPARATION_CERTIFIED"
NEXT_GATE = "AUDIT_FROZEN_ARTIFACT_IMMUTABILITY_AND_REOPEN_AUTHORIZATION"
RESULT_PATH = Path("results/v0.4.2_phase_c_verdict_budget_audit.json")
REPORT_PATH = Path("reports/v0.4.2_phase_c_verdict_budget_audit.md")
LEDGER_PATH = Path("results/v0.4.2_phase_c_claim_boundary_ledger.json")


CAMPAIGN_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "955_csg_third_order_fail_closed",
        "profile": "955_strong_GC_reachable_state_MSR_local_CSG_audit",
        "kind": "versioned_budget_fail_closed_audit",
        "budget": "config/v0.4.2_955_slack_csg_third_order_budget.json",
        "preflight": "results/v0.4.2_955_slack_csg_third_order_preflight.json",
        "audit": "results/v0.4.2_955_slack_csg_third_order.json",
        "report": "reports/v0.4.2_955_slack_csg_third_order_preflight.md",
        "expected_budget_campaign": "955_CSG_FULL_SECOND_ORDER_JET_FIBER_THIRD_ORDER",
    },
    {
        "id": "955_csg_fourth_order_fail_closed",
        "profile": "955_strong_GC_reachable_state_MSR_local_CSG_audit",
        "kind": "versioned_budget_fail_closed_audit",
        "budget": "config/v0.4.2_955_slack_csg_fourth_order_budget.json",
        "preflight": "results/v0.4.2_955_slack_csg_fourth_order_preflight.json",
        "audit": "results/v0.4.2_955_slack_csg_fourth_order.json",
        "report": "reports/v0.4.2_955_slack_csg_fourth_order_preflight.md",
        "expected_budget_campaign": "955_CSG_FULL_THIRD_ORDER_JET_FIBER_FOURTH_ORDER",
    },
    {
        "id": "721_corrected_complete_unit_groebner_preflight",
        "profile": "721_fixed_vector_GC_strong_MSR",
        "kind": "bounded_probe_without_production_budget",
        "budget": None,
        "preflight": None,
        "audit": None,
        "report": "reports/v0.4.2_721_groebner_preflight.md",
        "driver": "scripts/run_v042_721_groebner_preflight.py",
        "worker": "scripts/probe_v042_721_groebner_preflight_worker.py",
        "test": "tests/final_theory/test_v042_721_groebner_preflight.py",
    },
    {
        "id": "sr2v_d12_historical_cancelled_budget",
        "profile": "SR2V_state_native_shear_D12_historical_preflight",
        "kind": "versioned_budget_historical_cancelled",
        "budget": "config/v0.4.2_sr2v_state_native_shear_D12_budget.json",
        "preflight": "results/v0.4.2_sr2v_state_native_shear_D12_preflight.json",
        "audit": None,
        "report": "reports/v0.4.2_sr2v_state_native_shear_D12_preflight.md",
        "manifest": "results/v0.4.2_sr2v_state_native_shear_D12_manifest.json",
        "superseding_result": "results/v0.4.2_sr2v_fixed_harmonic_cpobc_obstruction.json",
    },
)


def _load_json(root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((root / relative_path).read_text(encoding="utf-8"))


def _bind_file(
    root: Path,
    relative_path: str,
    *,
    require_semantic_digest: bool = False,
) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    hashes = line_ending_hashes(path, require_canonical_lf=True)
    binding: dict[str, Any] = {
        "path": relative_path,
        "kind": "budget_input" if "/config/" in f"/{relative_path}" else path.suffix,
        "raw_sha256": hashes["current_raw_sha256"],
        "canonical_lf_sha256": hashes["canonical_lf_sha256"],
        "size_bytes": hashes["current_raw_size_bytes"],
        "strict_utf8_lf": True,
    }
    if path.suffix == ".json":
        payload = _load_json(root, relative_path)
        digest = payload.pop("semantic_digest_sha256", None)
        if digest is None:
            if require_semantic_digest:
                raise ValueError(f"missing semantic digest: {relative_path}")
            binding["semantic_digest_verified"] = False
            binding["digest_policy"] = "raw_sha256_only_budget_input"
        else:
            if stable_hash(payload) != digest:
                raise ValueError(f"semantic digest mismatch: {relative_path}")
            binding["semantic_digest_sha256"] = digest
            binding["semantic_digest_verified"] = True
            binding["digest_policy"] = "semantic_and_raw_verified"
        binding["schema_version"] = payload.get("schema_version")
        binding["verdict_or_status"] = payload.get("verdict", payload.get("status"))
    return binding


def _assert(condition: bool, message: str, evidence: Any = None) -> dict[str, Any]:
    if not condition:
        raise ValueError(message)
    return {"id": message, "passed": True, "evidence": evidence}


def _audit_budget_campaign(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    budget = _load_json(root, spec["budget"])
    preflight = _load_json(root, spec["preflight"])
    audit = _load_json(root, spec["audit"])
    budget_binding = _bind_file(root, spec["budget"])
    preflight_binding = _bind_file(root, spec["preflight"], require_semantic_digest=True)
    audit_binding = _bind_file(root, spec["audit"], require_semantic_digest=True)
    report_binding = _bind_file(root, spec["report"])

    embedded_budget = preflight["resource_decision"]["versioned_budget"]
    checks = [
        _assert(
            budget == embedded_budget,
            "budget_file_equals_embedded_versioned_budget",
            spec["id"],
        ),
        _assert(
            budget["campaign"] == spec["expected_budget_campaign"],
            "budget_campaign_name_matches_expected_campaign",
            budget["campaign"],
        ),
        _assert(
            budget["execution_rule"].startswith("AUTHORISE_ONLY_IF_PREFLIGHT"),
            "budget_requires_preflight_before_authorised_audit",
            budget["execution_rule"],
        ),
        _assert(
            "GENERIC_GROEBNER_OR_SATURATION" in budget["not_authorised"],
            "generic_solver_is_not_authorised_by_budget",
            budget["not_authorised"],
        ),
        _assert(
            preflight["resource_decision"]["generic_solver_authorised"] is False,
            "preflight_does_not_authorise_generic_solver",
            preflight["resource_decision"],
        ),
        _assert(
            preflight["execution_boundary"]["generic_solver_run"] is False,
            "preflight_did_not_run_generic_solver",
            preflight["execution_boundary"],
        ),
        _assert(
            audit["execution_boundary"]["generic_solver_run"] is False,
            "authorised_fail_closed_audit_did_not_run_generic_solver",
            audit["execution_boundary"],
        ),
        _assert(
            audit["execution_boundary"]["Groebner_or_saturation_runs"] == 0,
            "authorised_fail_closed_audit_has_zero_groebner_or_saturation_runs",
            audit["execution_boundary"],
        ),
        _assert(
            "preflight" in preflight["verdict"].lower()
            and "preflight" in report_binding["path"].lower()
            or "preflight" in (root / spec["report"]).read_text(encoding="utf-8").lower(),
            "campaign_is_labelled_as_preflight",
            preflight["verdict"],
        ),
    ]
    return {
        "id": spec["id"],
        "profile": spec["profile"],
        "kind": spec["kind"],
        "budget_binding": budget_binding,
        "preflight_binding": preflight_binding,
        "audit_binding": audit_binding,
        "report_binding": report_binding,
        "budget_embedded_matches": True,
        "production_solver_authorised": False,
        "production_solver_run": False,
        "checks": checks,
        "passed": True,
    }


def _audit_721_preflight(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    report = (root / spec["report"]).read_text(encoding="utf-8")
    driver = (root / spec["driver"]).read_text(encoding="utf-8")
    worker = (root / spec["worker"]).read_text(encoding="utf-8")
    bindings = [
        _bind_file(root, spec["report"]),
        _bind_file(root, spec["driver"]),
        _bind_file(root, spec["worker"]),
        _bind_file(root, spec["test"]),
    ]
    checks = [
        _assert(
            "preflight only" in report.lower()
            and "no solver run against the 721 profile" in report.lower(),
            "721_report_declares_preflight_only_and_no_profile_solver",
            "reports/v0.4.2_721_groebner_preflight.md",
        ),
        _assert(
            "Not a production gate" in driver,
            "721_driver_declares_not_a_production_gate",
            "scripts/run_v042_721_groebner_preflight.py",
        ),
        _assert(
            "TIMEOUT_SECONDS = 90" in driver
            and "BUILD_TIMEOUT_SECONDS = 180" in driver,
            "721_driver_has_bounded_timeouts",
            {"solver_timeout_seconds": 90, "cache_build_timeout_seconds": 180},
        ),
        _assert(
            "timeout=TIMEOUT_SECONDS" in driver
            and "timeout=BUILD_TIMEOUT_SECONDS" in driver,
            "721_driver_applies_both_hard_timeouts",
            "subprocess.run timeout arguments",
        ),
        _assert(
            "groebner" in worker.lower(),
            "721_worker_contains_measured_groebner_call",
            "scripts/probe_v042_721_groebner_preflight_worker.py",
        ),
        _assert(
            "full profile solver run" in report.lower()
            or "full 721 residual inventory" in report.lower(),
            "721_report_separates_probe_from_full_profile",
            "bounded probe interpretation",
        ),
    ]
    return {
        "id": spec["id"],
        "profile": spec["profile"],
        "kind": spec["kind"],
        "file_bindings": bindings,
        "versioned_budget_required": False,
        "production_solver_authorised": False,
        "production_solver_run": False,
        "bounded_limits": {
            "solver_timeout_seconds": 90,
            "cache_build_timeout_seconds": 180,
        },
        "checks": checks,
        "passed": True,
    }


def _audit_cancelled_d12(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    budget = _load_json(root, spec["budget"])
    preflight = _load_json(root, spec["preflight"])
    manifest = _load_json(root, spec["manifest"])
    budget_binding = _bind_file(root, spec["budget"])
    preflight_binding = _bind_file(root, spec["preflight"], require_semantic_digest=True)
    manifest_binding = _bind_file(root, spec["manifest"], require_semantic_digest=True)
    report_binding = _bind_file(root, spec["report"])
    superseding_binding = _bind_file(root, spec["superseding_result"], require_semantic_digest=True)
    campaign_budget = preflight["input_bindings"]["campaign_budget"]
    execution = preflight["execution_and_claim_boundary"]
    checks = [
        _assert(
            campaign_budget["path"] == spec["budget"],
            "D12_campaign_budget_path_is_explicit",
            campaign_budget["path"],
        ),
        _assert(
            campaign_budget["raw_sha256"] == budget_binding["raw_sha256"],
            "D12_campaign_budget_raw_hash_matches_bound_file",
            campaign_budget["raw_sha256"],
        ),
        _assert(
            campaign_budget["solver_executed"] is False,
            "D12_campaign_budget_records_solver_not_executed",
            campaign_budget,
        ),
        _assert(
            campaign_budget["authorised_limits"]["timeout_seconds_per_chart"]
            == budget["timeout_seconds_per_chart"]
            and campaign_budget["authorised_limits"]["total_wall_time_seconds"]
            == budget["total_wall_time_seconds"]
            and campaign_budget["authorised_limits"]["memory_limit_gib"]
            == budget["memory_limit_gib"],
            "D12_embedded_budget_limits_match_versioned_file",
            campaign_budget["authorised_limits"],
        ),
        _assert(
            execution["execution_authorised"] is False
            and execution["solver_status"] == "NOT_RUN"
            and execution["execution_cancellation"]
            == "EXECUTION_CANCELLED_BY_LATER_UNIT_IDEAL",
            "D12_execution_is_cancelled_and_solver_free",
            execution,
        ),
        _assert(
            preflight["gates"]["no_budget_fallback_or_solver_execution"] is True,
            "D12_has_no_budget_fallback_or_solver_execution",
            preflight["gates"],
        ),
        _assert(
            manifest_binding["raw_sha256"]
            == preflight["input_bindings"]["D12_manifest"]["raw_sha256"],
            "D12_manifest_raw_hash_matches_bound_file",
            manifest_binding["raw_sha256"],
        ),
        _assert(
            manifest["search_terminal"] == "NOT_A_SEARCH_TERMINAL_POLYNOMIAL_MANIFEST_ONLY",
            "D12_manifest_is_not_a_profile_terminal",
            manifest["search_terminal"],
        ),
        _assert(
            superseding_binding["semantic_digest_sha256"]
            == preflight["input_bindings"]["superseding_fixed_state_unit_ideal_obstruction"][
                "semantic_digest_sha256"
            ],
            "D12_superseding_result_digest_is_bound",
            superseding_binding["semantic_digest_sha256"],
        ),
    ]
    return {
        "id": spec["id"],
        "profile": spec["profile"],
        "kind": spec["kind"],
        "budget_binding": budget_binding,
        "preflight_binding": preflight_binding,
        "manifest_binding": manifest_binding,
        "report_binding": report_binding,
        "superseding_result_binding": superseding_binding,
        "versioned_budget_required": True,
        "production_solver_authorised": False,
        "production_solver_run": False,
        "execution_cancelled": True,
        "checks": checks,
        "passed": True,
    }


def build_audit(root: Path) -> dict[str, Any]:
    ledger = _load_json(root, LEDGER_PATH.as_posix())
    ledger_digest = ledger.pop("semantic_digest_sha256", None)
    if ledger_digest is None or stable_hash(ledger) != ledger_digest:
        raise ValueError("claim-boundary ledger semantic digest mismatch")
    state = _load_json(root, "CURRENT_RESEARCH_STATE.json")
    phase_c = state["affected_campaign"]["phase_C"]
    starting_gate = (
        "AUDIT_VERDICT_GRAMMAR_AND_PREFLIGHT_BUDGET_SEPARATION"
        if "verdict_budget_audit" in phase_c
        else phase_c["next_gate"]
    )
    packet = _load_json(root, "results/v0.4.2_phase_a_termination_decision_packet.json")
    freeze = _load_json(root, "results/v0.4.2_phase_a_freeze_execution.json")
    campaign_results = []
    for spec in CAMPAIGN_SPECS:
        if spec["kind"] == "versioned_budget_fail_closed_audit":
            campaign_results.append(_audit_budget_campaign(root, spec))
        elif spec["kind"] == "bounded_probe_without_production_budget":
            campaign_results.append(_audit_721_preflight(root, spec))
        elif spec["kind"] == "versioned_budget_historical_cancelled":
            campaign_results.append(_audit_cancelled_d12(root, spec))
        else:
            raise ValueError(f"unknown campaign kind: {spec['kind']}")

    grammar_checks = [
        _assert(
            state["global_verdict"] == "FINAL_THEORY_OPEN",
            "global_scientific_verdict_remains_final_theory_open",
            state["global_verdict"],
        ),
        _assert(
            state["affected_campaign"]["solver_run_permitted"] is False,
            "live_state_does_not_permit_solver_run",
            state["affected_campaign"]["solver_run_permitted"],
        ),
        _assert(
            freeze["dedicated_cas_authorized"] is False
            and freeze["full_profile_solver_run"] is False,
            "phase_a_freeze_did_not_authorise_or_run_dedicated_cas",
            freeze,
        ),
        _assert(
            packet["complete_finite_on_semantics_lattice_claim_available"] is False,
            "owner_packet_does_not_claim_complete_lattice",
            packet["complete_finite_on_semantics_lattice_claim_available"],
        ),
        _assert(
            starting_gate == "AUDIT_VERDICT_GRAMMAR_AND_PREFLIGHT_BUDGET_SEPARATION",
            "audit_starts_from_recorded_phase_c_gate",
            starting_gate,
        ),
    ]
    grammar = {
        "rules": {
            "CERTIFIED": "machine-checked within the artifact's declared scope; not automatic profile promotion",
            "PREFLIGHT": "bounded feasibility or structure measurement; not production solver authorization",
            "OPEN": "unresolved scope remains",
            "OPEN_RESOURCE_LIMIT": "recorded resource/theorem-path boundary; not witness, obstruction, empty set, or solver impossibility",
            "SUPERSEDED_OR_CANCELLED": "historical record with no reauthorization power",
            "OWNER_APPROVED": "state-transition authorization only; not a scientific verdict",
            "passed": "internal artifact validation status; not a scientific terminal claim",
        },
        "checks": grammar_checks,
        "passed": True,
    }
    budget_campaigns = [
        item for item in campaign_results if item["kind"].startswith("versioned_budget")
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": "2026-08-14",
        "evidence_head": "333ab67",
        "status": VERDICT,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "claim_boundary_ledger": {
            "path": LEDGER_PATH.as_posix(),
            "semantic_digest_sha256": ledger_digest,
            "scope": "Phase-C first-gate ledger input; not mutable live state",
        },
        "grammar": grammar,
        "campaigns": campaign_results,
        "separation_summary": {
            "campaign_count": len(campaign_results),
            "versioned_budget_campaign_count": len(budget_campaigns),
            "bounded_probe_without_production_budget_count": sum(
                item["kind"] == "bounded_probe_without_production_budget"
                for item in campaign_results
            ),
            "production_solver_authorised_count": sum(
                item["production_solver_authorised"] for item in campaign_results
            ),
            "production_solver_run_count": sum(
                item["production_solver_run"] for item in campaign_results
            ),
            "all_campaign_checks_passed": all(
                item["passed"] for item in campaign_results
            ),
            "budget_files_raw_bound": all(
                "budget_binding" in item for item in budget_campaigns
            ),
            "no_default_budget_fallback_used": True,
        },
        "reopen_boundary": {
            "dedicated_cas_authorized": False,
            "versioned_budget_required_for_reopen": True,
            "owner_approval_required": True,
            "current_721_full_profile_solver_run": False,
            "current_955_full_profile_solver_run": False,
        },
        "next_gate": NEXT_GATE,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    rows = []
    for item in payload["campaigns"]:
        rows.append(
            "| `{}` | `{}` | `{}` | {} | {} |".format(
                item["id"],
                item["kind"],
                item["profile"],
                str(item["production_solver_authorised"]).lower(),
                str(item["production_solver_run"]).lower(),
            )
        )
    summary = payload["separation_summary"]
    return "\n".join(
        [
            "# Phase C verdict grammar and preflight/budget separation audit",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The second Phase-C gate is complete. The audit distinguishes scoped",
            "machine validation, bounded preflight, versioned budget, owner approval,",
            "and scientific verdicts. It found no authorised or executed production",
            "solver campaign in the audited records.",
            "",
            f"- Campaigns audited: **{summary['campaign_count']}**",
            f"- Versioned-budget campaigns: **{summary['versioned_budget_campaign_count']}**",
            f"- Bounded probes without production budget: **{summary['bounded_probe_without_production_budget_count']}**",
            f"- Production solver authorisations: **{summary['production_solver_authorised_count']}**",
            f"- Production solver runs: **{summary['production_solver_run_count']}**",
            "",
            "## Campaign separation",
            "",
            "| campaign | kind | profile | solver authorised | solver run |",
            "|---|---|---|---:|---:|",
            *rows,
            "",
            "## Grammar rules enforced",
            "",
            "- `CERTIFIED` is scoped machine validation, not automatic full-profile promotion.",
            "- `PREFLIGHT` is bounded measurement, not production solver authorization.",
            "- `OPEN_RESOURCE_LIMIT` is a recorded boundary, not witness, obstruction,",
            "  empty-set, commutativity, or solver-impossibility proof.",
            "- `SUPERSEDED_OR_CANCELLED` records have no reauthorization power.",
            "- `passed=true` means the artifact's internal checks passed; it is not a",
            "  scientific terminal verdict.",
            "",
            "## Important bug/correction checks",
            "",
            "- 955 third/fourth-order budgets are compared structurally exactly",
            "  with the embedded versioned budgets in their preflight results.",
            "- Their generic Gröbner/saturation operations are explicitly unauthorized",
            "  and their execution boundaries record zero such runs.",
            "- 721 uses a corrected complete-residual-unit probe with hard 90-second",
            "  solver and 180-second cache-build timeouts; it has no production budget",
            "  and no full-profile solver result.",
            "- D12 binds the campaign budget raw hash, records cancellation by a later",
            "  unit-ideal result, and records solver status `NOT_RUN`.",
            "",
            "## Scientific boundary",
            "",
            "The global verdict remains `FINAL_THEORY_OPEN`. No complete finite ON",
            "semantics lattice, full-profile witness, full-profile obstruction, or",
            "dedicated-CAS impossibility is added by this methodology audit.",
            "",
            "## Next gate",
            "",
            f"`{payload['next_gate']}`",
            "",
        ]
    )


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
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
            raise SystemExit("tracked verdict/budget audit differs from rebuilt payload")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(payload):
            raise SystemExit("tracked verdict/budget report differs from rebuilt report")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
