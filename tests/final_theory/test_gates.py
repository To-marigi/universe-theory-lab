from __future__ import annotations

import copy
import json
from pathlib import Path

from universe_lab.final_theory.benchmarks import run_final_theory_bench
from universe_lab.final_theory.gates import (
    evaluate_candidate,
    validate_candidate_registry,
    validate_gate_spec,
)

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / "Final-Theory-Program"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gate_spec_and_candidate_registry_are_valid() -> None:
    gates = _load(PROGRAM / "requirements" / "final_theory_gates.yaml")
    registry = _load(PROGRAM / "candidates" / "candidate_registry.json")
    phase_b_registry = _load(
        PROGRAM / "candidates" / "candidate_registry_v042_phase_b.json"
    )
    assert validate_gate_spec(gates) == []
    assert validate_candidate_registry(registry) == []
    assert validate_candidate_registry(phase_b_registry) == []
    assert len(registry["candidates"]) >= 3


def test_reference_oracle_cannot_fill_missing_candidate_evidence() -> None:
    registry = _load(PROGRAM / "candidates" / "candidate_registry.json")
    phase_b_registry = _load(
        PROGRAM / "candidates" / "candidate_registry_v042_phase_b.json"
    )
    historical_v1 = next(
        item for item in registry["candidates"] if item["id"] == "causal_information_v1"
    )
    result = evaluate_candidate(historical_v1)
    assert result["kinematics_defined"]
    assert not result["dynamics_defined"]
    assert not result["spin2_gate_passed"]
    assert "SPIN2_NOT_FOUND" in result["achieved_statuses"]
    assert result["scientific_status"] == "FINAL_THEORY_OPEN"

    active_v2 = next(
        item
        for item in phase_b_registry["candidates"]
        if item["id"] == "causal_information_v2_sparse_kraus"
    )
    active_result = evaluate_candidate(active_v2)
    assert active_result["kinematics_defined"]
    assert active_result["dynamics_defined"]
    assert not active_result["spin2_gate_passed"]
    assert active_result["scientific_status"] == "FINAL_THEORY_OPEN"


def test_v2_is_the_versioned_phase_b_active_candidate() -> None:
    registry = _load(
        PROGRAM / "candidates" / "candidate_registry_v042_phase_b.json"
    )
    assert registry["central_candidate"] == "causal_information_v1"
    assert registry["active_candidates"]["PHASE_B"] == (
        "causal_information_v2_sparse_kraus"
    )
    assert registry["schema_version"] == "0.2"
    assert registry["candidate_policy"]["v1_v2_equivalence_certified"] is False
    assert registry["candidate_policy"]["cross_version_evidence_transfer"] is False


def test_active_phase_b_pointer_is_fail_closed() -> None:
    registry = _load(
        PROGRAM / "candidates" / "candidate_registry_v042_phase_b.json"
    )
    broken = copy.deepcopy(registry)
    broken["active_candidates"]["PHASE_B"] = "missing_candidate"
    errors = validate_candidate_registry(broken)
    assert any("active_candidates.PHASE_B" in error for error in errors)


def test_active_candidate_requires_a_version_and_complete_spin2_schema() -> None:
    registry = _load(
        PROGRAM / "candidates" / "candidate_registry_v042_phase_b.json"
    )
    broken = copy.deepcopy(registry)
    active_id = broken["active_candidates"]["PHASE_B"]
    active = next(item for item in broken["candidates"] if item["id"] == active_id)
    active.pop("candidate_version")
    active["spin2_evidence"].pop("ghost_free")
    errors = validate_candidate_registry(broken)
    assert any("candidate_version is required" in error for error in errors)
    assert any("missing=['ghost_free']" in error for error in errors)


def test_full_v0_1_result_preserves_non_claims() -> None:
    result = run_final_theory_bench(ROOT)
    assert result["benchmark_integrity_passed"]
    assert result["reference_controls"]["passed"]
    assert not result["spin2_found"]
    assert not result["final_theory_completed"]
    assert result["scientific_status"] == "FINAL_THEORY_OPEN"
    assert "SPIN2_GATE_PASS" in result["prohibited_claims"]
