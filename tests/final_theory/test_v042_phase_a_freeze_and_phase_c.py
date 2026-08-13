from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

ROOT = Path(__file__).resolve().parents[2]
FREEZE_RESULT = ROOT / "results/v0.4.2_phase_a_freeze_execution.json"
CHARTER_RESULT = ROOT / "results/v0.4.2_phase_c_methodology_charter.json"
STATE = ROOT / "CURRENT_RESEARCH_STATE.json"


def test_freeze_record_is_explicit_and_does_not_overclaim() -> None:
    record = json.loads(FREEZE_RESULT.read_text(encoding="utf-8"))
    digest = record.pop("semantic_digest_sha256")

    assert stable_hash(record) == digest
    assert record["freeze_executed"] is True
    assert record["dedicated_cas_authorized"] is False
    assert record["full_profile_solver_run"] is False
    assert record["global_verdict"] == "FINAL_THEORY_OPEN"
    assert record["complete_finite_on_semantics_lattice_claim_available"] is False
    assert record["profiles"]["955"]["terminal_boundary"] == (
        "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT"
    )
    assert record["profiles"]["721"]["terminal_boundary"] == (
        "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT"
    )
    assert record["profiles"]["955"]["obstruction_claimed"] is False
    assert record["profiles"]["721"]["witness_claimed"] is False


def test_phase_c_charter_digest_and_controls_are_valid() -> None:
    charter = json.loads(CHARTER_RESULT.read_text(encoding="utf-8"))
    digest = charter.pop("semantic_digest_sha256")

    assert stable_hash(charter) == digest
    assert all(charter["controls"].values())
    assert charter["phase_b_deferred"] is True
    assert charter["reopen_requires_owner_approval_and_versioned_budget"] is True


def test_current_state_records_the_executed_transition() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = state["affected_campaign"]["phase_A_termination_packet"]

    assert packet["freeze_executed"] is True
    assert packet["owner_decision_required"] is False
    assert packet["dedicated_cas_authorized"] is False
    assert packet["execution_record"] == (
        "results/v0.4.2_phase_a_freeze_execution.json"
    )
    assert state["affected_campaign"]["phase_C"]["status"] == "ACTIVE"
