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


def test_current_state_marks_phase_c_complete_and_phase_b_transition() -> None:
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    campaign = state["affected_campaign"]
    phase_c = campaign["phase_C"]
    review = phase_c["completion_review"]
    phase_b = campaign["phase_B"]

    assert campaign["status"] == (
        "PHASE_A_FROZEN_BOTH_PROFILES_OPEN_RESOURCE_LIMIT_PHASE_C_COMPLETE_"
        "PHASE_B_LARGE_N_SAMPLER_EXTENSION_DESIGN_FROZEN_IMPLEMENTATION_"
        "PREFLIGHT_BUDGET_REQUIRED_FINAL_THEORY_OPEN"
    )
    assert campaign["next_gate"] == (
        "PHASE_B_LABELED_SAMPLER_AND_OBSERVABLE_EQUIVALENCE_COST_PREFLIGHT_"
        "BUDGET_APPROVAL"
    )
    assert phase_c["status"] == "COMPLETE"
    assert phase_c["next_gate"] == START_GATE
    assert review["status"] == "PHASE_C_METHOD_ARTIFACT_COMPLETION_REVIEW_CERTIFIED"
    assert review["artifact"] == RESULT_PATH.as_posix()
    assert review["report"] == REPORT_PATH.as_posix()
    assert phase_b["status"] == (
        "LARGE_N_SAMPLER_EXTENSION_DESIGN_FROZEN_"
        "IMPLEMENTATION_PREFLIGHT_BUDGET_REQUIRED"
    )
    assert phase_b["global_central_candidate"] == "causal_information_v1"
    assert phase_b["active_candidate"] == "causal_information_v2_sparse_kraus"
    assert phase_b["started"] is True
    assert phase_b["starting_gate"] == NEXT_GATE
    assert phase_b["artifact"] == (
        "results/v0.4.2_phase_b_required_physics_gap_inventory.json"
    )
    assert phase_b["report"] == (
        "reports/v0.4.2_phase_b_required_physics_gap_inventory.md"
    )
    assert phase_b["all_acceptance_checks_passed"] is True
    assert phase_b["scientific_verdict_added"] is False
    assert phase_b["next_gate"] == (
        "PHASE_B_LABELED_SAMPLER_AND_OBSERVABLE_EQUIVALENCE_COST_PREFLIGHT_"
        "BUDGET_APPROVAL"
    )
    assert phase_b["continuum_dimension_design"]["all_acceptance_checks_passed"] is True
    assert phase_b["continuum_dimension_preflight"][
        "all_preflight_checks_passed"
    ] is True
    assert phase_b["continuum_dimension_preflight"][
        "production_measurement_pipeline_validated"
    ] is False
    assert state["global_verdict"] == "FINAL_THEORY_OPEN"


def test_report_is_generated_from_machine_review() -> None:
    payload = _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(payload)
