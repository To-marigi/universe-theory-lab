from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_exact_scaling_design_v042 import (
    NEXT_GATE as CURRENT_PHASE_B_NEXT_GATE,
)
from universe_lab.final_theory.phase_b_control_protocol_registry_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_registry,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_control_protocol_registry_rebuilds_exactly() -> None:
    payload = _tracked()

    assert build_registry(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_registry_digest_and_execution_gate_are_closed() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == (
        "PHASE_B_CONTROL_PROTOCOL_REGISTERED_EXECUTION_BLOCKED"
    )
    assert payload["all_structural_checks_passed"] is True
    assert payload["execution_gate_open"] is False
    assert payload["production_sampling_authorized"] is False
    assert payload["solver_run_permitted"] is False
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["next_gate"] == NEXT_GATE


def test_controls_cannot_become_candidate_evidence() -> None:
    payload = _tracked()
    controls = payload["control_protocol"]["registered_controls"]

    assert {control["id"] for control in controls} == {
        "random_growth_negative_control",
        "bdg_dimension_four_positive_control",
        "label_permutation_control",
    }
    assert all(control["candidate_evidence"] is False for control in controls)
    assert all(control["trajectories_recorded"] == 0 for control in controls)
    assert all(control["solver_calls"] == 0 for control in controls)
    assert payload["control_protocol"]["execution_status"] == "NOT_EXECUTED"


def test_unfrozen_statistics_and_spectral_rules_are_registered() -> None:
    payload = _tracked()

    assert payload["spectral_protocol"]["production_window_status"] == "NOT_FROZEN"
    assert payload["spectral_protocol"]["selection_algorithm_status"] == (
        "MUST_BE_MACHINE_REGISTERED_BEFORE_CONTROL_EXECUTION"
    )
    assert payload["statistical_protocol"]["production_status"] == "NOT_FROZEN"
    assert payload["statistical_protocol"]["simultaneous_interval_method"] == (
        "NOT_FROZEN"
    )
    assert "never pooled" in payload["statistical_protocol"]["sampling_unit"]
    assert payload["measurement_protocol"]["scaling_protocol"]["no_holdout_refit"]


def test_missing_controls_and_production_budget_are_explicit() -> None:
    payload = _tracked()
    positive = payload["control_protocol"]["positive_control_extension"]
    resources = payload["resource_and_promotion_protocol"]

    assert positive["geometric_dimension_control"]["current_status"] == (
        "NOT_IMPLEMENTED"
    )
    assert positive["bdg_weighted_ensemble"]["status"] == "UNDEFINED_BLOCKER"
    assert resources["production_measurement_budget_present"] is False
    assert resources["separate_owner_approval_required"] is True


def test_live_state_points_to_the_closed_control_gate() -> None:
    payload = _tracked()
    state = json.loads(
        (ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8")
    )
    phase_b = state["affected_campaign"]["phase_B"]
    record = phase_b["control_protocol_registry"]

    assert phase_b["next_gate"] == CURRENT_PHASE_B_NEXT_GATE
    assert phase_b["operational_next_gate"] == CURRENT_PHASE_B_NEXT_GATE
    assert record["artifact"] == RESULT_PATH.as_posix()
    assert record["semantic_digest_sha256"] == payload[
        "semantic_digest_sha256"
    ]
    assert record["execution_gate_open"] is False
    assert record["production_sampling_authorized"] is False
