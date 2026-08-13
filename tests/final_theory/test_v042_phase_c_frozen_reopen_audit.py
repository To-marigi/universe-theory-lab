from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_c_frozen_reopen_audit_v042 import (
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


def test_audit_digest_and_frozen_inventory() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")
    frozen = payload["frozen_artifacts"]
    summary = frozen["summary"]

    assert stable_hash(payload) == digest
    assert summary == {
        "artifact_group_count": 12,
        "frozen_file_count": 37,
        "machine_evidence_count": 21,
        "all_raw_sha256_match": True,
        "all_canonical_lf_sha256_match": True,
        "all_sizes_match": True,
        "all_strict_utf8_lf": True,
        "all_json_semantic_digests_match": True,
        "mutable_live_state_excluded": True,
        "audit_outputs_excluded": True,
    }
    assert len(frozen["frozen_file_bindings"]) == 37
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False


def test_self_reference_and_mutable_state_boundaries() -> None:
    payload = _tracked()
    frozen = payload["frozen_artifacts"]
    paths = {item["path"] for item in frozen["frozen_file_bindings"]}

    assert "CURRENT_RESEARCH_STATE.json" not in paths
    assert RESULT_PATH.as_posix() not in paths
    assert REPORT_PATH.as_posix() not in paths
    assert frozen["ledger"]["self_binding_excluded"] is True
    assert frozen["summary"]["audit_outputs_excluded"] is True


def test_reopen_authorization_stays_closed() -> None:
    payload = _tracked()
    requirements = payload["reopen_authorization"]["requirements"]

    assert requirements["owner_approval_required"] is True
    assert requirements["owner_reopen_approval_present"] is False
    assert requirements["versioned_budget_required"] is True
    assert requirements["versioned_reopen_budget_present"] is False
    assert requirements["specified_cas_and_version_required"] is True
    assert requirements["hard_timeout_and_memory_supervision_required"] is True
    assert requirements["staged_input_plan_required"] is True
    assert requirements["runtime_production_gate_required"] is True
    assert requirements["runtime_production_gate_present"] is True
    assert requirements["runtime_gate_blocks_current_state"] is True
    assert requirements["dedicated_cas_authorized_now"] is False
    assert requirements["current_full_profile_solver_run"] is False
    assert requirements["current_reopen_authorized"] is False
    assert payload["reopen_authorization"]["historical_campaigns_have_no_reopen_power"] is True
    assert payload["reopen_authorization"]["runtime_production_gate"][
        "current_state_blocks_run"
    ] is True
    assert payload["next_gate"] == NEXT_GATE


def test_current_state_points_to_completion_review() -> None:
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    phase_c = state["affected_campaign"]["phase_C"]
    audit = phase_c["frozen_reopen_audit"]

    assert audit["status"] == (
        "PHASE_C_FROZEN_ARTIFACT_IMMUTABILITY_AND_REOPEN_AUTHORIZATION_CERTIFIED"
    )
    assert audit["artifact"] == RESULT_PATH.as_posix()
    assert audit["report"] == REPORT_PATH.as_posix()
    assert phase_c["next_gate"] == NEXT_GATE
    assert state["affected_campaign"]["next_gate"] == NEXT_GATE
    assert phase_c["reopen_authorization"]["status"] == "NOT_AUTHORIZED"
    assert phase_c["reopen_authorization"]["runtime_gate_blocks_current_state"] is True


def test_report_is_generated_from_machine_audit() -> None:
    payload = _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(payload)
