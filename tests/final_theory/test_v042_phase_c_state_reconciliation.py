from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_methods_scope_closure_v042 import (
    NEXT_GATE as CURRENT_SCOPE_NEXT_GATE,
)
from universe_lab.final_theory.phase_b_control_methods_scope_closure_v042 import (
    STATUS as CURRENT_PHASE_B_STATUS,
)

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "CURRENT_RESEARCH_STATE.json"
RECONCILIATION = (
    ROOT / "results/v0.4.2_phase_c_state_reconciliation_2026-08-14.json"
)


def test_reconciliation_artifact_is_self_consistent() -> None:
    artifact = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
    digest = artifact.pop("semantic_digest_sha256")

    assert stable_hash(artifact) == digest
    assert artifact["historical_artifacts_untouched"] is True
    assert artifact["live_index_reconciled"] is True
    assert artifact["preserved_boundaries"]["global_verdict"] == "FINAL_THEORY_OPEN"


def test_live_state_has_no_stale_phase_a_owner_fields() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    campaign = state["affected_campaign"]
    progress = campaign["721_source_native_progress"]

    assert state["updated"] == "2026-08-20"
    assert campaign["status"] == (
        "PHASE_A_FROZEN_BOTH_PROFILES_OPEN_RESOURCE_LIMIT_PHASE_C_COMPLETE_"
        f"{CURRENT_PHASE_B_STATUS}_FINAL_THEORY_OPEN"
    )
    assert campaign["next_gate"] == CURRENT_SCOPE_NEXT_GATE
    assert progress["955_freeze_decision_status"] == (
        "EXECUTED_OWNER_APPROVED_PHASE_A_FREEZE_2026-08-13_PHASE_C_COMPLETE"
    )
    assert "not_yet_done" not in progress["inverse_saturation_summary"]
    assert "not_yet_done" not in progress["inverse_resaturated_cpobc_msr_summary"]
    assert progress["inverse_resaturated_cpobc_msr_summary"][
        "msr_terms_unchanged_reason"
    ].startswith("monomial_to_monomial_substitution_coincidence")
    assert campaign["phase_C"]["state_reconciliation"]["live_index_reconciled"] is True


def test_reconciliation_preserves_non_claims() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = state["affected_campaign"]["phase_A_termination_packet"]
    progress = state["affected_campaign"]["721_source_native_progress"]

    assert state["global_verdict"] == "FINAL_THEORY_OPEN"
    assert packet["complete_finite_on_semantics_lattice_claim_available"] is False
    assert packet["dedicated_cas_authorized"] is False
    assert progress["commutativity_proved_for_full_profile"] is False
    assert progress["groebner_preflight_summary"]["solver_run_against_721_profile"] is False
