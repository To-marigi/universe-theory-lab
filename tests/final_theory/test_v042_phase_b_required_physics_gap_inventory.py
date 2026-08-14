from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_required_physics_gap_inventory_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_inventory,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_inventory_rebuilds_exactly() -> None:
    assert build_inventory(ROOT) == _tracked()


def test_inventory_digest_and_acceptance_checks() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["next_gate"] == NEXT_GATE
    assert all(
        check["passed"] for check in payload["acceptance_criteria"].values()
    )


def test_inventory_keeps_reference_controls_out_of_candidate_evidence() -> None:
    payload = _tracked()
    snapshot = payload["candidate_snapshot"]
    assert snapshot["evaluated_candidate_evidence"] is False
    spin2 = next(gap for gap in payload["gaps"] if gap["id"] == "emergent_spin2_response")
    assert spin2["reference_controls"]["passed"] is True
    assert spin2["reference_controls"]["candidate_evidence"] is False
    assert spin2["status"] == "SPIN2_NOT_FOUND"


def test_inventory_preserves_phase_a_and_solver_boundaries() -> None:
    payload = _tracked()
    assert payload["phase_a_boundary_preserved"] == {
        "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
        "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
        "both_full_profiles_resolved": False,
        "solver_run_permitted": False,
    }


def test_report_is_generated_from_machine_inventory() -> None:
    payload = _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(payload)
