from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_exact_scaling_design_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_design,
    render_report,
)
from universe_lab.final_theory.phase_b_control_methods_scope_closure_v042 import (
    NEXT_GATE as CURRENT_SCOPE_NEXT_GATE,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_exact_scaling_design_rebuilds_certificate_core() -> None:
    payload = _tracked()
    rebuilt = build_design(ROOT)

    assert rebuilt["certificate_core"] == payload["certificate_core"]
    assert rebuilt["semantic_digest_sha256"] == payload["semantic_digest_sha256"]
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_exact_scaling_design_is_partial_and_fail_closed() -> None:
    payload = _tracked()
    assert stable_hash(payload["certificate_core"]) == payload[
        "semantic_digest_sha256"
    ]
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["next_gate"] == NEXT_GATE
    assert payload["new_control_trajectories"] == 0
    assert payload["candidate_trajectories"] == 0
    assert payload["solver_calls"] == 0
    assert payload["production_sampling_authorized"] is False


def test_candidate_route_is_not_silently_replaced_by_uniform_dp() -> None:
    payload = _tracked()
    candidate = payload["certificate_core"]["design"]["candidate_weighted_route"]
    random_control = payload["certificate_core"]["design"]["random_control_route"]

    assert random_control["status"] == "EXACT_IDEAL_COUNT_DP_DESIGN_ONLY"
    assert candidate["status"] == (
        "BLOCKED_DESIGN_ONLY_NO_FACTORIZATION_CERTIFICATE"
    )


def test_live_state_points_to_owner_approval_gate() -> None:
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    campaign = state["affected_campaign"]
    phase_b = campaign["phase_B"]
    record = phase_b["control_exact_scaling_design"]

    assert campaign["next_gate"] == CURRENT_SCOPE_NEXT_GATE
    assert phase_b["next_gate"] == CURRENT_SCOPE_NEXT_GATE
    assert phase_b["operational_next_gate"] == CURRENT_SCOPE_NEXT_GATE
    assert record["artifact"] == RESULT_PATH.as_posix()
    assert record["semantic_digest_sha256"] == _tracked()[
        "semantic_digest_sha256"
    ]
    assert record["next_gate"] == NEXT_GATE
    assert record["owner_approval_present"] is False
    assert record["implementation_preflight_authorized"] is False
