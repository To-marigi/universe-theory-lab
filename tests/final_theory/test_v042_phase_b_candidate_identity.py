from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_candidate_identity_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_audit,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_candidate_identity_audit_rebuilds_exactly() -> None:
    assert build_audit(ROOT) == _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        _tracked()
    )


def test_candidate_identity_digest_and_fail_closed_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == "PHASE_B_CANDIDATE_IDENTITY_AND_INPUT_FREEZE_CERTIFIED"
    assert payload["identity"]["registry_central_candidate"] == (
        "causal_information_v1"
    )
    assert payload["identity"]["phase_b_active_candidate"] == (
        "causal_information_v2_sparse_kraus"
    )
    assert payload["identity"]["implemented_v2_model_id"] == (
        "causal_information_v2_sparse_kraus"
    )
    assert payload["identity"]["mismatch_detected"] is False
    assert payload["identity"]["active_candidate_identity_certified"] is True
    assert payload["identity"]["same_candidate_certified"] is False
    assert payload["sampling_authorized"] is False
    assert payload["next_gate"] == NEXT_GATE
    assert payload["all_safety_checks_passed"] is True


def test_candidate_identity_audit_preserves_phase_a_and_solver_boundaries() -> None:
    payload = _tracked()
    assert payload["phase_a_boundary_preserved"] == {
        "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
        "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
        "solver_run_permitted": False,
    }
