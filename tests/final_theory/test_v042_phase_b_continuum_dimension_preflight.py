from __future__ import annotations

import json
from pathlib import Path

import pytest

from universe_lab.final_theory.continuum_observables_v042 import (
    correlation_length_record,
    minkowski_ordering_fraction,
    ordering_fraction_dimension,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_continuum_dimension_preflight_v042 import (
    NEXT_GATE as PREFLIGHT_NEXT_GATE,
)
from universe_lab.final_theory.phase_b_continuum_dimension_preflight_v042 import (
    REPORT_PATH,
    RESULT_PATH,
    build_preflight,
    render_report,
)
from universe_lab.final_theory.phase_b_large_n_sampler_extension_design_v042 import (
    NEXT_GATE as LARGE_N_NEXT_GATE,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_bounded_measurement_preflight_rebuilds_exactly() -> None:
    payload = _tracked()

    assert build_preflight(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_preflight_digest_and_claim_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == (
        "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_MEASUREMENT_PREFLIGHT_COMPLETE_"
        "PRODUCTION_EXTENSION_REQUIRED"
    )
    assert payload["all_preflight_checks_passed"] is True
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["scientific_evidence"] is False
    assert payload["continuum_phase_supported"] is False
    assert payload["dimension_claim_issued"] is False
    assert payload["production_sampling_authorized"] is False
    assert payload["solver_run_permitted"] is False
    assert payload["next_gate"] == PREFLIGHT_NEXT_GATE


def test_ordering_calibration_uses_independent_known_points() -> None:
    payload = _tracked()
    controls = payload["analytic_controls"]

    assert minkowski_ordering_fraction(2.0) == pytest.approx(0.5, abs=1e-15)
    assert minkowski_ordering_fraction(4.0) == pytest.approx(0.1, abs=1e-15)
    assert ordering_fraction_dimension(0.5) == pytest.approx(2.0, abs=1e-7)
    assert ordering_fraction_dimension(0.1) == pytest.approx(4.0, abs=1e-7)
    assert controls["ordering_anchor_expected"] == {"2": 0.5, "4": 0.1}
    assert controls["ordering_anchor_computed"] == {"2": 0.5, "4": 0.1}
    assert controls["ordering_anchor_max_abs_error"] == 0.0
    assert controls["control_scope"]["end_to_end_bdg_ensemble_control"] is False


def test_all_bounded_labels_and_transition_rows_pass() -> None:
    payload = _tracked()
    labels = payload["label_invariance"]
    controls = payload["analytic_controls"]

    assert labels["relations_checked"] == 88
    assert labels["permutations_checked"] == 7980
    assert labels["failed_permutation_count"] == 0
    assert labels["failed_relation_ids"] == []
    assert labels["passed"] is True
    assert controls["lazy_transition_rows_checked"] == 399
    assert controls["lazy_transition_row_failures"] == 0
    assert all(
        record["normalized_exactly"]
        for record in (
            *payload["candidate_measurements"],
            *payload["random_control_measurements"],
        )
    )


def test_correlation_schema_and_ensemble_aggregation_are_explicit() -> None:
    payload = _tracked()
    empty = correlation_length_record(())
    isolated = correlation_length_record((0,))
    chain = correlation_length_record((2, 0))

    assert set(empty) == set(isolated) == set(chain)
    assert empty["defined"] is False
    assert empty["graph_diameter"] == 0
    assert empty["xi"] is None
    assert chain["defined"] is True
    for record in (
        *payload["candidate_measurements"],
        *payload["random_control_measurements"],
    ):
        assert record["spectral_fit_steps"] == [2, 3, 4, 5]
        assert "spectral_component_diagnostics" in record
        assert "conditional_rms_correlation_length" in record
        assert "conditional_rms_correlation_length_over_diameter" in record


def test_large_n_and_positive_control_gaps_are_fail_closed() -> None:
    payload = _tracked()
    readiness = payload["readiness"]

    assert readiness["current_exact_max_n"] == 5
    assert readiness["planned_sizes"] == [8, 12, 18, 27, 40, 60]
    assert readiness["large_n_sampler_extension_available"] is False
    assert readiness["bdg_positive_control_ensemble_available"] is False
    assert readiness["versioned_production_budget_present"] is False
    assert readiness["production_sampling_authorized"] is False
    assert readiness["production_measurement_pipeline_validated"] is False
    assert payload["finite_size_diagnostics"]["protocol_sizes_available"] is False
    assert payload["resource_controls"]["hard_wall_time_supervisor_used"] is False
    assert payload["resource_controls"]["hard_memory_supervisor_used"] is False


def test_gate_authorization_and_capabilities_are_structured() -> None:
    payload = _tracked()
    budget = payload["budget"]
    capabilities = payload["capability_audit"]

    assert budget["authorizes_gate"] == (
        "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_MEASUREMENT_PREFLIGHT"
    )
    assert budget["authorization_relationship"][
        "production_authorization_unchanged"
    ] is True
    assert capabilities["passed"] is True
    assert capabilities["runtime_probe_records"]["candidate"][
        "transition_instrument_available"
    ] is True
    assert capabilities["runtime_probe_records"]["positive_control"][
        "expected_unsupported_error"
    ] is True


def test_live_state_preserves_preflight_after_large_n_design() -> None:
    payload = _tracked()
    state = json.loads((ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    phase_b = state["affected_campaign"]["phase_B"]
    preflight = phase_b["continuum_dimension_preflight"]

    assert phase_b["next_gate"] == LARGE_N_NEXT_GATE
    assert preflight["artifact"] == RESULT_PATH.as_posix()
    assert preflight["report"] == REPORT_PATH.as_posix()
    assert preflight["semantic_digest_sha256"] == payload[
        "semantic_digest_sha256"
    ]
    assert preflight["relabeling_permutations_checked"] == 7980
    assert preflight["all_preflight_checks_passed"] is True
    assert preflight["production_sampling_authorized"] is False
