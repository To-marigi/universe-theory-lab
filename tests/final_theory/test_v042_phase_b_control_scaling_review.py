from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_scaling_review_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_review,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_scaling_review_rebuilds_certificate_core() -> None:
    payload = _tracked()
    rebuilt = build_review(ROOT)

    assert rebuilt["certificate_core"] == payload["certificate_core"]
    assert rebuilt["semantic_digest_sha256"] == payload["semantic_digest_sha256"]
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_scaling_review_digest_and_boundary() -> None:
    payload = _tracked()
    assert stable_hash(payload["certificate_core"]) == payload[
        "semantic_digest_sha256"
    ]
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["next_gate"] == NEXT_GATE
    assert payload["control_training_promoted"] is False
    assert payload["candidate_trajectories"] == 0
    assert payload["solver_calls"] == 0


def test_primary_and_independent_replay_share_first_cap_boundary() -> None:
    payload = _tracked()
    implementations = payload["certificate_core"]["implementations"]
    primary = implementations["primary"]
    replay = implementations["independent"]

    assert primary["completed_n"] == replay["completed_n"] == 38
    assert primary["cap"] == replay["cap"]
    assert primary["cap"]["source_n"] == 38
    assert primary["cap"]["growth_step"] == 38
    assert primary["cap"]["downset_count_lower_bound"] == 4097
    assert primary["last_successful_exact_downset_count"] == 3791
    assert primary["trajectory_digest_through_completed_n"] == replay[
        "trajectory_digest_through_completed_n"
    ]


def test_scaling_review_does_not_relax_exactness() -> None:
    payload = _tracked()
    boundary = payload["certificate_core"]["authorization_boundary"]

    assert boundary["cap_increase_applied"] is False
    assert boundary["approximate_fallback_used"] is False
    assert boundary["global_verdict"] == "FINAL_THEORY_OPEN"
