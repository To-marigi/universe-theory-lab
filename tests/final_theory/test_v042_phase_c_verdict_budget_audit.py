from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_c_verdict_budget_audit_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_audit,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_audit_rebuilds_exactly() -> None:
    assert build_audit(ROOT) == _tracked()


def test_audit_digest_and_separation_summary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")
    summary = payload["separation_summary"]

    assert stable_hash(payload) == digest
    assert summary == {
        "campaign_count": 4,
        "versioned_budget_campaign_count": 3,
        "bounded_probe_without_production_budget_count": 1,
        "production_solver_authorised_count": 0,
        "production_solver_run_count": 0,
        "all_campaign_checks_passed": True,
        "budget_files_raw_bound": True,
        "no_default_budget_fallback_used": True,
    }
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False


def test_grammar_and_reopen_boundary_do_not_overclaim() -> None:
    payload = _tracked()
    grammar = payload["grammar"]
    reopen = payload["reopen_boundary"]

    assert grammar["passed"] is True
    assert grammar["rules"]["passed"].startswith("internal artifact validation")
    assert "not witness" in grammar["rules"]["OPEN_RESOURCE_LIMIT"]
    assert reopen == {
        "dedicated_cas_authorized": False,
        "versioned_budget_required_for_reopen": True,
        "owner_approval_required": True,
        "current_721_full_profile_solver_run": False,
        "current_955_full_profile_solver_run": False,
    }
    assert payload["next_gate"] == NEXT_GATE


def test_721_and_d12_records_keep_distinct_boundaries() -> None:
    payload = _tracked()
    campaigns = {item["id"]: item for item in payload["campaigns"]}

    probe = campaigns["721_corrected_complete_unit_groebner_preflight"]
    cancelled = campaigns["sr2v_d12_historical_cancelled_budget"]
    assert probe["versioned_budget_required"] is False
    assert probe["bounded_limits"] == {
        "solver_timeout_seconds": 90,
        "cache_build_timeout_seconds": 180,
    }
    assert cancelled["versioned_budget_required"] is True
    assert cancelled["execution_cancelled"] is True
    assert cancelled["production_solver_run"] is False


def test_reports_are_generated_from_machine_audit() -> None:
    payload = _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(payload)


def test_current_state_points_to_next_phase_c_gate() -> None:
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    phase_c = state["affected_campaign"]["phase_C"]
    audit = phase_c["verdict_budget_audit"]

    assert audit["status"] == (
        "PHASE_C_VERDICT_GRAMMAR_AND_PREFLIGHT_BUDGET_SEPARATION_CERTIFIED"
    )
    assert audit["artifact"] == RESULT_PATH.as_posix()
    assert audit["report"] == REPORT_PATH.as_posix()
    assert audit["next_gate"] == NEXT_GATE
    assert phase_c["next_gate"] == "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW"
