from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_measurement_budget_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_certificate,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_control_measurement_budget_certificate_rebuilds_exactly() -> None:
    payload = _tracked()

    assert build_certificate(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_budget_digest_and_control_only_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["control_measurement_authorized"] is True
    assert payload["candidate_trajectories_authorized"] is False
    assert payload["production_sampling_authorized"] is False
    assert payload["solver_run_permitted"] is False
    assert payload["scientific_verdict_added"] is False
    assert payload["next_gate"] == NEXT_GATE


def test_budget_matches_preregistered_sizes_seeds_and_count() -> None:
    payload = _tracked()
    scope = payload["control_scope"]

    assert scope["planned_sizes"] == [8, 12, 18, 27, 40, 60]
    assert scope["training_sizes"] == [8, 12, 18, 27]
    assert scope["holdout_sizes"] == [40, 60]
    assert scope["training_seeds"] == [101, 103, 107, 109, 113]
    assert scope["holdout_seeds"] == [127, 131, 137]
    assert scope["trajectories_per_seed_and_size"] == 4096
    assert scope["authorized_control_trajectory_count"] == 212992


def test_budget_has_zero_retry_and_zero_candidate_solver_limits() -> None:
    payload = _tracked()
    limits = payload["limits"]

    assert limits["max_retries"] == 0
    assert limits["max_active_workers"] == 1
    assert limits["candidate_trajectories"] == 0
    assert limits["solver_calls"] == 0
    assert payload["acceptance_checks"][
        "candidate_access_and_solver_are_forbidden"
    ]["passed"] is True


def test_owner_approval_and_proposal_binding_are_recorded() -> None:
    payload = _tracked()
    budget = json.loads(
        (ROOT / "config/v0.4.2_phase_b_control_measurement_budget_20260816.json")
        .read_text(encoding="utf-8")
    )

    assert budget["owner_approval_present"] is True
    assert budget["owner_instruction_source"] == "current chat instruction"
    assert payload["proposal_sha256"] == budget["approved_from_proposal_sha256"]
