from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_c_claim_boundary_ledger_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_ledger,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_tracked_ledger_rebuilds_exactly() -> None:
    assert build_ledger(ROOT) == _tracked()


def test_ledger_digest_and_frozen_inventory_are_self_consistent() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")
    summary = payload["inventory_summary"]

    assert stable_hash(payload) == digest
    assert summary["group_count"] == 12
    assert summary["file_binding_count"] == 37
    assert summary["machine_evidence_count"] == 21
    assert summary["all_paths_unique"] is True
    assert summary["duplicate_paths"] == []
    assert summary["all_frozen_files_strict_utf8_lf"] is True
    assert summary["all_machine_semantic_digests_verified"] is True
    assert summary["self_reference_excluded"] is True
    assert summary["mutable_live_state_excluded_from_raw_freeze"] is True


def test_claim_boundaries_and_corrections_do_not_overclaim() -> None:
    payload = _tracked()
    groups = {group["id"]: group for group in payload["artifact_groups"]}
    corrections = {item["id"]: item for item in payload["correction_records"]}
    coverage = payload["coverage_controls"]

    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["complete_finite_on_semantics_lattice_claim_available"] is False
    assert payload["phase_a_boundaries"]["both_full_profiles_resolved"] is False
    assert groups["955_block_determinant"]["terminality"] == (
        "supports_owner_resource_limit_boundary"
    )
    assert groups["721_corrected_groebner_preflight"]["terminality"] == (
        "supports_owner_resource_limit_boundary"
    )
    assert corrections["721_groebner_residual_unit_correction"][
        "superseded_commit"
    ] == "e989dff"
    assert corrections["721_groebner_residual_unit_correction"][
        "correcting_commit"
    ] == "077c721"
    assert coverage["missing_required_paths"] == {
        "charter_frozen_inputs": [],
        "decision_packet_evidence": [],
        "freeze_record_evidence": [],
    }
    assert coverage["all_charter_frozen_inputs_indexed"] is True
    assert coverage["all_decision_packet_evidence_indexed"] is True
    assert coverage["all_freeze_record_evidence_indexed"] is True
    assert coverage["all_predecessor_group_ids_valid"] is True
    assert payload["next_gate"] == NEXT_GATE


def test_report_is_generated_from_the_machine_ledger() -> None:
    payload = _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(payload)


def test_current_state_points_to_the_completed_phase_c_gate() -> None:
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    phase_c = state["affected_campaign"]["phase_C"]

    assert phase_c["claim_boundary_ledger"]["artifact"] == RESULT_PATH.as_posix()
    assert phase_c["claim_boundary_ledger"]["report"] == REPORT_PATH.as_posix()
    assert phase_c["claim_boundary_ledger"]["status"] == (
        "PHASE_C_CLAIM_BOUNDARY_LEDGER_AND_FROZEN_ARTIFACT_INDEX_CERTIFIED"
    )
    assert phase_c["claim_boundary_ledger"]["next_gate"] == NEXT_GATE
