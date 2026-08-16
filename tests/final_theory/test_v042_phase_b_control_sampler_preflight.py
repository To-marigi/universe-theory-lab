from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_sampler_preflight_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_preflight,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_sampler_preflight_rebuilds_exactly() -> None:
    payload = _tracked()

    assert build_preflight(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_sampler_preflight_digest_and_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["next_gate"] == NEXT_GATE
    assert payload["new_control_trajectories"] == 0
    assert payload["candidate_trajectories"] == 0
    assert payload["solver_calls"] == 0
    assert payload["control_measurement_authorized"] is False
    assert payload["production_sampling_authorized"] is False


def test_sampler_preflight_fixture_matrix_is_complete() -> None:
    payload = _tracked()
    plan = payload["fixture_plan"]

    assert plan["sizes"] == [1, 2, 3, 4, 5]
    assert plan["seeds"] == [101, 127]
    assert plan["trajectory_indices"] == [0, 1]
    assert plan["profiles"] == [
        "causal_information_v2_sparse_kraus",
        "random_growth_control",
    ]
    assert plan["fixture_count"] == 40
    assert len(payload["fixture_records"]) == 40
    assert payload["acceptance_checks"][
        "primary_and_independent_replay_match"
    ] is True


def test_sampler_preflight_has_fail_closed_cap_and_source_audits() -> None:
    payload = _tracked()

    assert payload["cap_audit"] == {
        "primary_cap_failed_closed": True,
        "replay_cap_failed_closed": True,
    }
    assert payload["acceptance_checks"][
        "large_n_forbidden_paths_are_absent"
    ] is True
    assert payload["acceptance_checks"][
        "no_scientific_evidence_or_candidate_access"
    ] is True
