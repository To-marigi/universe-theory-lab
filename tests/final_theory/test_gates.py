from __future__ import annotations

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
    assert validate_gate_spec(gates) == []
    assert validate_candidate_registry(registry) == []
    assert len(registry["candidates"]) >= 3


def test_reference_oracle_cannot_fill_missing_candidate_evidence() -> None:
    registry = _load(PROGRAM / "candidates" / "candidate_registry.json")
    candidate = next(
        item for item in registry["candidates"] if item["id"] == "causal_information_v1"
    )
    result = evaluate_candidate(candidate)
    assert result["kinematics_defined"]
    assert not result["dynamics_defined"]
    assert not result["spin2_gate_passed"]
    assert "SPIN2_NOT_FOUND" in result["achieved_statuses"]
    assert result["scientific_status"] == "FINAL_THEORY_OPEN"


def test_full_v0_1_result_preserves_non_claims() -> None:
    result = run_final_theory_bench(ROOT)
    assert result["benchmark_integrity_passed"]
    assert result["reference_controls"]["passed"]
    assert not result["spin2_found"]
    assert not result["final_theory_completed"]
    assert result["scientific_status"] == "FINAL_THEORY_OPEN"
    assert "SPIN2_GATE_PASS" in result["prohibited_claims"]
