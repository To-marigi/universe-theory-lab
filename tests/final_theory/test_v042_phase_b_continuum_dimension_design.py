from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_continuum_dimension_design_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_design,
    render_report,
)
from universe_lab.final_theory.phase_b_control_exact_scaling_design_v042 import (
    NEXT_GATE as HISTORICAL_PHASE_B_NEXT_GATE,
)
from universe_lab.final_theory.phase_b_control_methods_scope_closure_v042 import (
    NEXT_GATE as CURRENT_PHASE_B_NEXT_GATE,
)
from universe_lab.final_theory.phase_b_control_methods_scope_closure_v042 import (
    STATUS as CURRENT_PHASE_B_STATUS,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_continuum_dimension_design_rebuilds_exactly() -> None:
    payload = _tracked()
    assert build_design(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_design_digest_and_acceptance_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == (
        "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_DESIGN_FROZEN_"
        "PRODUCTION_EXTENSION_REQUIRED_NO_SAMPLING_AUTHORIZATION"
    )
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["next_gate"] == NEXT_GATE
    assert payload["authorization_boundary"] == {
        "design_frozen": True,
        "bounded_measurement_preflight_authorized": False,
        "production_sampling_authorized": False,
        "solver_run_permitted": False,
        "global_verdict": "FINAL_THEORY_OPEN",
    }


def test_pilot_is_exactly_finite_and_non_evidentiary() -> None:
    payload = _tracked()
    pilot = payload["exact_pilot"]

    assert pilot["max_n"] == 5
    assert pilot["level_counts"] == [1, 1, 2, 5, 16, 63]
    assert pilot["non_evidentiary"] is True
    assert pilot["size_records"][0]["candidate_expected_ordering_fraction"] is None
    assert pilot["size_records"][1]["candidate_expected_ordering_fraction"] is None
    assert all(
        row["candidate_normalized"] and row["random_control_normalized"]
        for row in pilot["size_records"]
    )


def test_dimension_design_separates_controls_and_holdout() -> None:
    payload = _tracked()
    assert len(payload["dimension_estimators"]) == 3
    assert payload["scaling_protocol"]["no_holdout_refit"] is True
    assert payload["scaling_protocol"]["training_sizes"] == [8, 12, 18, 27]
    assert payload["scaling_protocol"]["holdout_sizes"] == [40, 60]
    assert all(
        control["candidate_evidence"] is False
        for control in payload["controls"]
    )
    assert payload["candidate"]["global_central_baseline"] == (
        "causal_information_v1"
    )
    assert payload["candidate"]["phase_b_active_candidate"] == (
        "causal_information_v2_sparse_kraus"
    )


def test_ordering_calibration_is_source_anchored() -> None:
    payload = _tracked()
    estimator = payload["dimension_estimators"][0]

    assert estimator["calibration"] == (
        "f(d)=Gamma(d+1)*Gamma(d/2)/(2*Gamma(3*d/2))"
    )
    assert estimator["calibration_anchor_values"] == {"2": 0.5, "4": 0.1}
    assert payload["acceptance_checks"][
        "ordering_calibration_matches_source_anchors"
    ]["passed"] is True


def test_bounded_design_keeps_production_protocol_fail_closed() -> None:
    payload = _tracked()
    spectral = payload["dimension_estimators"][2]

    assert spectral["bounded_preflight_fit"]["walk_time_steps"] == [2, 3, 4, 5]
    assert spectral["production_plateau_window_frozen"] is False
    assert "fixed production spectral plateau window" in payload[
        "production_design_gaps"
    ]
    assert "executable BDG dimension-four ensemble" in payload[
        "production_design_gaps"
    ]
    assert payload["authorization_boundary"]["production_sampling_authorized"] is False


def test_live_state_preserves_design_after_large_n_extension_design() -> None:
    payload = _tracked()
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    phase_b = state["affected_campaign"]["phase_B"]

    assert phase_b["status"] == CURRENT_PHASE_B_STATUS
    assert phase_b["next_gate"] == CURRENT_PHASE_B_NEXT_GATE
    assert phase_b["operational_next_gate"] == CURRENT_PHASE_B_NEXT_GATE
    assert phase_b["control_exact_scaling_design"]["next_gate"] == (
        HISTORICAL_PHASE_B_NEXT_GATE
    )
    assert phase_b["continuum_dimension_design"]["artifact"] == RESULT_PATH.as_posix()
    assert phase_b["continuum_dimension_design"]["semantic_digest_sha256"] == payload[
        "semantic_digest_sha256"
    ]
    assert phase_b["continuum_dimension_design"]["production_sampling_authorized"] is False
