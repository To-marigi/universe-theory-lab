from __future__ import annotations

from universe_lab.final_theory.spin2 import (
    barnes_rivers_reference_audit,
    fierz_pauli_ward_reference_audit,
    massless_helicity_reference_audit,
    run_spin2_reference_controls,
)


def test_barnes_rivers_spin2_projector_control() -> None:
    result = barnes_rivers_reference_audit()
    assert result["passed"]
    assert result["checks"]["off_shell_projector_rank_five"]
    assert "not the two-helicity" in result["claim_boundary"]


def test_massless_spin2_has_two_reference_helicities() -> None:
    result = massless_helicity_reference_audit()
    assert result["passed"]
    assert result["checks"]["two_independent_polarizations"]


def test_fierz_pauli_reference_obeys_ward_identities() -> None:
    result = fierz_pauli_ward_reference_audit()
    assert result["passed"]
    assert result["checks"]["four_gauge_directions_are_null"]
    assert result["checks"]["linearized_bianchi_identity"]


def test_reference_controls_are_not_candidate_evidence() -> None:
    result = run_spin2_reference_controls()
    assert result["passed"]
    assert result["candidate_evidence"] is False
