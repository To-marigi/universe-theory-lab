from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_c_method_completion_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    START_GATE,
    build_review,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_completion_review_rebuilds_exactly() -> None:
    assert build_review(ROOT) == _tracked()


def test_completion_review_digest_and_four_controls() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["all_acceptance_checks_passed"] is True
    assert set(payload["acceptance_criteria"]) == {
        "semantic_identity",
        "claim_boundary_ledger",
        "verdict_grammar",
        "frozen_artifacts_and_budget_separation",
    }
    assert all(
        criterion["status"] == "SATISFIED"
        for criterion in payload["acceptance_criteria"].values()
    )
    assert len(payload["artifact_chain"]) == 4
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["next_gate"] == NEXT_GATE


def test_completion_review_keeps_phase_a_open_boundaries() -> None:
    payload = _tracked()
    boundary = payload["phase_a_boundary_preserved"]

    assert boundary == {
        "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
        "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
        "both_full_profiles_resolved": False,
        "solver_run_permitted": False,
    }
    assert payload["phase_b_transition"]["phase_b_started_by_this_review"] is False


def test_current_state_marks_phase_c_complete_and_phase_b_next() -> None:
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    campaign = state["affected_campaign"]
    phase_c = campaign["phase_C"]
    review = phase_c["completion_review"]
    phase_b = campaign["phase_B"]

    assert campaign["status"] == (
        "PHASE_A_FROZEN_BOTH_PROFILES_OPEN_RESOURCE_LIMIT_PHASE_C_COMPLETE_PHASE_B_READY_FINAL_THEORY_OPEN"
    )
    assert campaign["next_gate"] == NEXT_GATE
    assert phase_c["status"] == "COMPLETE"
    assert phase_c["next_gate"] == START_GATE
    assert review["status"] == "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW_CERTIFIED"
    assert review["artifact"] == RESULT_PATH.as_posix()
    assert review["report"] == REPORT_PATH.as_posix()
    assert phase_b["status"] == "READY_NOT_STARTED"
    assert phase_b["next_gate"] == NEXT_GATE
    assert state["global_verdict"] == "FINAL_THEORY_OPEN"


def test_report_is_generated_from_machine_review() -> None:
    payload = _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(payload)
