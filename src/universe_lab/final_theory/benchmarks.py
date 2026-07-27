"""Final-Theory Bench v0.1 runner."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from universe_lab.final_theory.gates import (
    evaluate_candidate,
    validate_candidate_registry,
    validate_gate_spec,
)
from universe_lab.final_theory.spin2 import run_spin2_reference_controls


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_final_theory_bench(root: Path) -> dict[str, Any]:
    """Run v0.1 structural gates and independent Spin-2 reference controls."""

    program = root / "Final-Theory-Program"
    gate_path = program / "requirements" / "final_theory_gates.yaml"
    registry_path = program / "candidates" / "candidate_registry.json"
    model_path = (
        program / "models" / "causal_information_v1" / "model_spec.json"
    )
    gate_spec = _load(gate_path)
    registry = _load(registry_path)
    model = _load(model_path)
    validation_errors = [
        *validate_gate_spec(gate_spec),
        *validate_candidate_registry(registry),
    ]
    if model.get("model_id") != "causal_information_v1":
        validation_errors.append("central model id must be causal_information_v1")

    controls = run_spin2_reference_controls()
    candidates = [
        evaluate_candidate(candidate) for candidate in registry["candidates"]
    ]
    central = next(
        result
        for result in candidates
        if result["candidate_id"] == registry["central_candidate"]
    )
    integrity = not validation_errors and controls["passed"]
    return {
        "suite": "Final-Theory Bench v0.1 / Emergent Spin-2 Gate",
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "gpu_required": False,
            "gpu_used": False,
            "gpu_reason": (
                "v0.1 uses small exact-structure and dense linear-algebra "
                "controls; GPU acceleration would not improve the evidence."
            ),
        },
        "inputs": [
            {"path": gate_path.relative_to(root).as_posix(), "sha256": _sha256(gate_path)},
            {
                "path": registry_path.relative_to(root).as_posix(),
                "sha256": _sha256(registry_path),
            },
            {
                "path": model_path.relative_to(root).as_posix(),
                "sha256": _sha256(model_path),
            },
        ],
        "validation_errors": validation_errors,
        "reference_controls": controls,
        "candidate_results": candidates,
        "central_candidate_result": central,
        "benchmark_integrity_passed": integrity,
        "spin2_found": central["spin2_gate_passed"],
        "final_theory_completed": False,
        "scientific_status": "FINAL_THEORY_OPEN",
        "allowed_claims": [
            "KINEMATICS_DEFINED",
            "SPIN2_NOT_FOUND",
            "FINAL_THEORY_OPEN",
        ],
        "prohibited_claims": [
            "DYNAMICS_DEFINED",
            "BACKGROUND_INDEPENDENCE_PASS",
            "CONTINUUM_PHASE_SUPPORTED",
            "SPIN2_CANDIDATE",
            "SPIN2_GATE_PASS",
            "UNIVERSAL_COUPLING_PASS",
            "EINSTEIN_VERTEX_PASS",
            "FINAL_THEORY_COMPLETED",
        ],
        "stopping_reason": (
            "The finite-cutoff kinematics are specified, but the microscopic "
            "measure, convergent dynamics, and candidate-derived two-point "
            "response are absent. The reference spin-2 controls cannot fill "
            "that evidentiary gap."
        ),
    }
