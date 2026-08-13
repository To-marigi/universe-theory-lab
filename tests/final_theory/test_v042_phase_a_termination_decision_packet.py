from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = "results/v0.4.2_phase_a_termination_decision_packet.json"


def test_phase_a_packet_is_owner_pending_and_does_not_overclaim() -> None:
    packet = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert packet["status"] == "OWNER_DECISION_REQUIRED_PHASE_A_TERMINATION_PACKET_READY"
    assert packet["global_verdict"] == "FINAL_THEORY_OPEN"
    assert packet["recommended_choice"] == "FREEZE_BOTH_OPEN_RESOURCE_LIMIT_THEN_PHASE_C"
    assert packet["freeze_executed"] is False
    assert packet["dedicated_cas_authorized"] is False
    assert packet["complete_finite_on_semantics_lattice_claim_available"] is False
    assert packet["profiles"]["955"]["full_profile_resolved"] is False
    assert packet["profiles"]["721"]["full_profile_resolved"] is False


def test_phase_a_packet_preserves_the_721_corrected_measurement() -> None:
    packet = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    profile = packet["profiles"]["721"]

    assert profile["native_generators"] == 24
    assert profile["nonzero_residuals"] == 1967
    assert profile["newly_zero_after_inverse_relation_reduction"] == 0
    assert profile["corrected_groebner_preflight"] == {
        "one_complete_residual_unit_scalar_equations": 4,
        "one_unit_seconds": 1.078,
        "one_unit_basis_size": 30,
        "two_unit_timeout_seconds": 90,
        "full_profile_solver_run": False,
    }


def test_phase_a_packet_digest_is_self_consistent() -> None:
    packet = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = packet.pop("semantic_digest_sha256")

    assert stable_hash(packet) == digest
