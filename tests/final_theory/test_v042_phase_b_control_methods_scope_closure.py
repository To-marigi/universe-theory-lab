from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_methods_scope_closure_v042 import (
    NEXT_GATE,
    OUTLINE_PATH,
    REPORT_PATH,
    RESULT_PATH,
    STATUS,
    build_scope_closure,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_scope_closure_rebuilds_and_matches_report() -> None:
    payload = _tracked()
    assert build_scope_closure(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_scope_closure_digest_and_claim_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == STATUS
    assert payload["next_gate"] == NEXT_GATE
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["decision"]["candidate_route"] == "EXCLUDED_NOT_EVALUATED"
    assert payload["execution_boundary"] == {
        "new_control_trajectories": 0,
        "candidate_trajectories": 0,
        "solver_calls": 0,
        "production_sampling_authorized": False,
        "approximate_sampler_authorized": False,
        "scientific_verdict_added": False,
    }


def test_scope_closure_references_outline_and_preserves_paper_i() -> None:
    payload = _tracked()
    assert (ROOT / OUTLINE_PATH).exists()
    outline = (ROOT / OUTLINE_PATH).read_text(encoding="utf-8")

    assert "control-and-methods" in outline.lower()
    assert "does not evaluate the candidate physical model" in payload["scope"]
    assert payload["decision"]["paper_i_publication"] == "PRESERVED_IMMUTABLE"
    assert payload["reopen_policy"]["existing_paper_i_record_must_not_be_mutated"]
