from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_cost_preflight_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_preflight,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_control_cost_preflight_rebuilds_certificate_core() -> None:
    payload = _tracked()
    rebuilt = build_preflight(ROOT)

    assert rebuilt["certificate_core"] == payload["certificate_core"]
    assert rebuilt["semantic_digest_sha256"] == payload["semantic_digest_sha256"]
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_control_cost_digest_and_boundary() -> None:
    payload = _tracked()

    assert stable_hash(payload["certificate_core"]) == payload[
        "semantic_digest_sha256"
    ]
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["next_gate"] == NEXT_GATE
    assert payload["control_training_promoted"] is False
    assert payload["candidate_trajectories"] == 0
    assert payload["solver_calls"] == 0


def test_n60_exact_cap_failure_is_recorded_not_silently_relaxed() -> None:
    payload = _tracked()
    outcomes = payload["certificate_core"]["outcomes"]
    n60 = next(item for item in outcomes if item["case_id"] == "random_growth_control_n60")

    assert n60["status"] == "RESOURCE_LIMIT_OPEN"
    assert n60["reason"] == "DOWNSET_ENUMERATION_LIMIT"
    assert n60["limit"] == 4096
    assert n60["approximate_fallback_used"] is False
    assert payload["resource_limit_open_cases"] == 1


def test_cost_fixture_keeps_trajectory_and_relation_digests_distinct() -> None:
    payload = _tracked()
    n27 = next(
        item
        for item in payload["certificate_core"]["outcomes"]
        if item["case_id"] == "random_growth_control_n27"
    )

    assert len(n27["trajectory_digest"]) == 64
    assert len(n27["relation_digest"]) == 64
    assert n27["trajectory_digest"] != n27["relation_digest"]
