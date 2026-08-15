from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_large_n_runtime_audit_v042 import (
    REPORT_PATH,
    RESULT_PATH,
    build_audit,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_runtime_audit_rebuilds_exactly() -> None:
    payload = _tracked()
    assert build_audit(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_runtime_audit_digest_and_boundaries() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == (
        "PHASE_B_LARGE_N_RUNTIME_COMPONENT_AUDIT_COMPLETE_NON_PRODUCTION_"
        "PREFLIGHT_REQUIRED"
    )
    assert payload["bounded_domain"] == {
        "max_n": 5,
        "unlabeled_level_counts": [1, 1, 2, 5, 16, 63],
        "new_trajectories": 0,
        "solver_calls": 0,
    }
    assert payload["equivalence_audit"]["height_failures"] == []
    assert payload["equivalence_audit"]["downset_failures"] == []
    assert payload["equivalence_audit"]["relabeling_failures"] == []
    assert payload["fail_closed_audit"] == {
        "downset_cap_failure_detected": True,
        "float_weight_rejected": True,
        "oversized_counter_rejected": True,
    }
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["implementation_preflight_authorized"] is False
    assert payload["production_sampler_available"] is False
    assert payload["production_sampling_authorized"] is False
    assert payload["scientific_verdict_added"] is False


def test_runtime_audit_is_still_before_budget_gate() -> None:
    payload = _tracked()
    assert payload["next_gate"] == (
        "PHASE_B_LABELED_SAMPLER_AND_OBSERVABLE_EQUIVALENCE_"
        "COST_PREFLIGHT_BUDGET_APPROVAL"
    )
    assert payload["independent_large_n_replay_available"] is False
    assert payload["resource_budget_present"] is False

    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    runtime = state["affected_campaign"]["phase_B"]["runtime_component_audit"]
    assert runtime["artifact"] == RESULT_PATH.as_posix()
    assert runtime["semantic_digest_sha256"] == payload["semantic_digest_sha256"]
    assert runtime["all_equivalence_checks_passed"] is True
    assert runtime["all_fail_closed_checks_passed"] is True
    assert runtime["implementation_preflight_authorized"] is False
