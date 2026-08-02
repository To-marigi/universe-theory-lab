"""Fail-closed guards for the Phase-A auxiliary-ideal resource checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_manifest_v042 as result

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "357d739091d2bf36740895f35c9227ba912e69f8d455f9e91dd8a6ea7ce6c605"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return result.build_resource_open_payload(ROOT)


def test_checkpoint_rebuilds_exactly_and_remains_nonterminal(
    rebuilt: dict[str, Any],
) -> None:
    frozen = _load(result.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == result.SCHEMA
    assert frozen["verdict"] == result.OPEN_VERDICT
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert result.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is False
    assert frozen["search_terminal"] == result.SEARCH_TERMINAL


def test_canonical_inputs_and_bottom_localization_are_bound(
    rebuilt: dict[str, Any],
) -> None:
    assert len(rebuilt["predecessor_bindings"]) == 4
    assert all(
        record["canonical_semantic_binding_passed"]
        for record in rebuilt["predecessor_bindings"].values()
    )
    machine_scope = rebuilt["machine_certified_scope"]
    localization = machine_scope["bottom_localization_ledger"]
    assert localization["factor_count"] == 14
    assert localization["passed"] is True
    assert all(localization["gates"].values())
    assert "F_lambda" in machine_scope["active_ring"]
    assert machine_scope["pure_Laurent_52_torus_claimed"] is False

    base = machine_scope["lightweight_base_ring_certificate"]
    assert base["upper_kernel_storage_shape"] == [49, 132]
    assert base["Q5_context_index"] == 131
    assert base["Q5_only_upper_columns"] == [48]
    assert base["Q5_only_upper_column_support"] == [131]
    assert base["bottom_q5_violation_count"] == 0
    assert base["dropped_spectator_names"] == ["bottom_q5", "s48"]
    assert base["active_variable_count"] == 52
    assert base["active_variables"] == [
        "t1",
        "t2",
        "t3",
        "t4",
        *(f"s{index}" for index in range(48)),
    ]
    assert base["reconstructed_active_ring"] == result.ACTIVE_RING
    assert base["declared_active_ring"] == result.ACTIVE_RING
    assert base["passed"] is True
    assert all(base["gates"].values())


def test_resource_attempt_is_manual_and_fail_closed(
    rebuilt: dict[str, Any],
) -> None:
    provenance = rebuilt["resource_attempt_provenance"]
    assert provenance["classification"] == "MANUALLY_RECORDED_LOCAL_OBSERVATION"
    for unavailable in (
        "attempt_provenance_machine_reproducible",
        "source_snapshot_available",
        "source_snapshot_sha256_available",
        "raw_monitor_log_available",
        "timeout_exit_record_available",
        "file_probe_record_available",
        "stdout_sha256_available",
        "stderr_sha256_available",
        "current_command_reproduces_attempt",
        "partial_source_rebuild_progress_machine_certified",
        "partial_pivot_progress_machine_certified",
        "partial_Schur_row_progress_machine_certified",
    ):
        assert provenance[unavailable] is False
    assert provenance["certified_partial_completion_count"] is None

    attempt = rebuilt["bounded_attempt"]
    assert attempt["provenance"] == "MANUALLY_RECORDED_LOCAL_OBSERVATION"
    assert attempt["declared_hard_request_limit_seconds"] == 3600
    assert attempt["partial_progress_claimed"] is False
    assert "hard_request_limit_enforced" not in rebuilt["gates"]
    assert rebuilt["gates"]["full_1127_source_Schur_ledger_generated"] is False
    assert rebuilt["gates"]["full_six_chart_generator_manifests_generated"] is False
    assert rebuilt["gates"]["denominator_inverse_reconstruction_ledger_completed"] is False


def test_no_solver_or_mathematical_terminal_is_claimed(rebuilt: dict[str, Any]) -> None:
    solver = rebuilt["manually_recorded_solver_observation"]
    assert solver["provenance"] == "MANUALLY_RECORDED_LOCAL_OBSERVATION"
    assert not any(value for key, value in solver.items() if key != "provenance")
    assert rebuilt["gates"]["no_solver_or_unit_ideal_claim"] is True
    boundary = rebuilt["claim_boundary"]
    for excluded in (
        "only the canonical bound inputs",
        "manually recorded local observations",
        "Groebner/unit-ideal claims",
        "witness claims",
        "commutativity claims",
        "every SR2-V terminal remain open",
    ):
        assert excluded.lower() in boundary.lower()


def test_report_is_an_exact_LF_render_of_the_payload(rebuilt: dict[str, Any]) -> None:
    frozen = (ROOT / result.REPORT_PATH).read_text(encoding="utf-8")
    assert frozen == result.render_resource_open_report(rebuilt)
    assert "\r" not in frozen
