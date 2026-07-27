from __future__ import annotations

from universe_lab.final_theory.phase_v02 import (
    emergent_symmetry_pre_gate,
    held_out_audit,
    phase_scan,
)


def test_phase_scan_uses_three_frozen_sizes() -> None:
    result = phase_scan()
    assert result["sizes"] == [3, 4, 5]
    assert result["couplings_frozen_before_held_out_n5"]
    assert [stage["state_count"] for stage in result["candidate"]["stages"]] == [
        5,
        16,
        63,
    ]


def test_continuum_is_resource_blocked_not_claimed_absent() -> None:
    result = phase_scan()
    assert result["continuum_status"] == "CONTINUUM_PHASE_RESOURCE_BLOCKED"
    assert result["phase_classification"] == "FINITE_SIZE_ARTIFACT_UNRESOLVED"


def test_symmetry_and_spin_gates_remain_blocked() -> None:
    result = emergent_symmetry_pre_gate()
    assert result["symmetry_status"] == "SPIN_CLASSIFICATION_NOT_YET_DEFINED"
    assert result["spin_gate_status"] == "SPIN2_GATE_BLOCKED_BY_CONTINUUM"
    assert not any(result["readiness_conditions"].values())


def test_held_out_protocol_has_no_retuning() -> None:
    result = held_out_audit()
    assert result["held_out_partitions"]["qsg_representation_dimension"] == 4
    assert not result["retuned_after_held_out"]
    assert result["status"] == "HELD_OUT_PROTOCOL_PASS"
