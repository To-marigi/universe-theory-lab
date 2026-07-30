"""Final-Theory Bench v0.2 orchestration and artifact generation."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp

from universe_lab.final_theory.causal_sets import enumeration_audit
from universe_lab.final_theory.dynamics_v02 import dynamics_benchmark
from universe_lab.final_theory.mutations_v02 import mutation_benchmark
from universe_lab.final_theory.phase_v02 import (
    emergent_symmetry_pre_gate,
    held_out_audit,
    phase_scan,
)
from universe_lab.final_theory.qsg_algebra import qsg_algebra_benchmark

BASELINE_COMMIT = "f542c6fa9be226f97364efe7718ddd9b9b4d0fb1"
BASELINE_TAG = "final-theory-bench-v0.1-open"
FROZEN_V01_HASHES = {
    "results/final_theory_bench_v0.1.json": (
        "57bfd93cde571b39d43f870d305cbe59f042f8de2efa1affbc1784483b3407ce"
    ),
    "Final-Theory-Program/requirements/final_theory_gates.yaml": (
        "8a10c947a9031e5dfe88ca1ad7e7a147ae2aab690f7fc29aa35150d09ec9bdb6"
    ),
    "Final-Theory-Program/candidates/candidate_registry.json": (
        "732d7e1e8a0b285263c447f2a09630285fc08c8d5cadcbe5fd20769896917506"
    ),
    "Final-Theory-Program/models/causal_information_v1/model_spec.json": (
        "c15a22edab4919b357d4019577bc96ecda750bcd836ebe0c0e5191cd0b0b35ed"
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _baseline_audit(root: Path) -> dict[str, Any]:
    records = []
    for relative, expected in FROZEN_V01_HASHES.items():
        actual = _sha256(root / relative)
        records.append(
            {
                "path": relative,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "unchanged": actual == expected,
            }
        )
    return {
        "commit": BASELINE_COMMIT,
        "annotated_tag": BASELINE_TAG,
        "files": records,
        "passed": all(record["unchanged"] for record in records),
    }


def run_final_theory_bench_v0_2(
    root: Path,
    *,
    production_commit: str = "UNCOMMITTED_WORKTREE",
) -> dict[str, Any]:
    """Run the conservative v0.2 dynamics and continuum pre-gates."""

    baseline = _baseline_audit(root)
    enumerator = enumeration_audit()
    dynamics = dynamics_benchmark()
    qsg = qsg_algebra_benchmark()
    phase = phase_scan()
    symmetry = emergent_symmetry_pre_gate()
    held_out = held_out_audit()
    mutations = mutation_benchmark()
    integrity = (
        baseline["passed"]
        and enumerator["passed"]
        and not dynamics["quantum_consistency"]["required_failures"]
        and qsg["reference_reproduction"]["core_checks_passed"]
        and held_out["retuned_after_held_out"] is False
        and mutations["passed"]
    )
    statuses = {
        "ENGINEERING_STATUS": "ENGINEERING_PASS" if integrity else "ENGINEERING_FAIL",
        "KINEMATICS_STATUS": "KINEMATICS_DEFINED",
        "DYNAMICS_STATUS": "DYNAMICS_CANDIDATE_DEFINED",
        "COVARIANCE_STATUS": "COVARIANT_MEASURE_PARTIAL",
        "QUANTUM_MEASURE_STATUS": "COVARIANT_MEASURE_PARTIAL",
        "BACKGROUND_INDEPENDENCE_STATUS": (
            "DYNAMICAL_BACKGROUND_INDEPENDENCE_CANDIDATE"
        ),
        "QSG_ALGEBRA_STATUS": qsg["qsg_algebra_status"],
        "PHASE_STATUS": phase["continuum_status"],
        "CONTINUUM_STATUS": phase["continuum_status"],
        "SYMMETRY_STATUS": symmetry["symmetry_status"],
        "SPIN_GATE_STATUS": symmetry["spin_gate_status"],
        "SCIENTIFIC_STATUS": "FINAL_THEORY_OPEN",
    }
    return {
        "suite": "Final-Theory Bench v0.2 / Quantum Dynamics and Continuum-Phase Gate",
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline": baseline,
        "production_commit": production_commit,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "sympy": sp.__version__,
            "gpu_available_for_declared_work": False,
            "gpu_used": False,
            "gpu_reason": (
                "The executed domain is exact combinatorics and symbolic/rational "
                "algebra. No certified large-ensemble GPU kernel was available."
            ),
        },
        "finite_causet_engine": enumerator,
        "dynamics_summary": {
            "status": dynamics["status"],
            "profile_id": dynamics["explicit_candidate"]["profile_id"],
            "quantum_consistency_status": dynamics["quantum_consistency"][
                "quantum_consistency_status"
            ],
            "covariance_status": dynamics["covariance_status"],
            "background_independence_status": dynamics[
                "background_independence_status"
            ],
        },
        "qsg_summary": {
            "reference_reproduction": qsg["reference_reproduction"]["status"],
            "search_status": qsg["qsg_algebra_status"],
            "representation_found": qsg["new_search"][
                "noncommutative_representation_found"
            ],
        },
        "phase_summary": {
            "classification": phase["phase_classification"],
            "continuum_status": phase["continuum_status"],
        },
        "symmetry_pre_gate": symmetry,
        "held_out": held_out,
        "mutations": mutations,
        "statuses": statuses,
        "benchmark_integrity_passed": integrity,
        "allowed_claims": [
            "KINEMATICS_DEFINED",
            "DYNAMICS_CANDIDATE_DEFINED",
            "COVARIANT_MEASURE_PARTIAL",
            "DYNAMICAL_BACKGROUND_INDEPENDENCE_CANDIDATE",
            "QSG_SEARCH_INCONCLUSIVE",
            "CONTINUUM_PHASE_RESOURCE_BLOCKED",
            "SPIN_CLASSIFICATION_NOT_YET_DEFINED",
            "SPIN2_GATE_BLOCKED_BY_CONTINUUM",
            "FINAL_THEORY_OPEN",
        ],
        "prohibited_claims": [
            "DYNAMICS_CONSISTENCY_PASS",
            "DYNAMICAL_BACKGROUND_INDEPENDENCE_PASS",
            "QSG_REFERENCE_RESULTS_REPRODUCED",
            "QSG_NONCOMMUTATIVE_REPRESENTATION_FOUND",
            "QSG_NO_REPRESENTATION_UP_TO_D",
            "CONTINUUM_PHASE_CANDIDATE",
            "SPIN_CLASSIFICATION_READY",
            "SPIN2_GATE_READY",
            "SPIN2_CANDIDATE",
            "SPIN2_GATE_PASS",
            "UNIVERSAL_COUPLING_PASS",
            "EINSTEIN_VERTEX_PASS",
            "FINAL_THEORY_COMPLETED",
        ],
        "stopping_reason": (
            "An explicit finite-cutoff Kraus growth candidate is defined and "
            "passes exact normalization, positivity, and label-covariance checks. "
            "Quantum Bell causality, covariant-event extension, scalable phase "
            "sampling, continuum diagnostics, and emergent symmetry remain open."
        ),
    }


def _source_hashes(root: Path) -> list[dict[str, Any]]:
    manifest = json.loads(
        (root / "references" / "manifest.json").read_text(encoding="utf-8")
    )
    wanted = {
        "arXiv:gr-qc/9904062v3",
        "arXiv:2003.11311v1",
        "arXiv:2603.25503v1",
        "arXiv:1001.2725v4",
        "DOI:10.1016/0370-2693(80)90212-9",
        "DOI:10.1103/PhysRev.135.B1049",
        "arXiv:gr-qc/0411023v3",
    }
    return [
        {
            "id": record["id"],
            "local_file": record["local_file"],
            "sha256": record["sha256"],
            "version": record["version"],
        }
        for record in manifest["records"]
        if record["id"] in wanted
    ]


def write_v0_2_artifacts(
    root: Path,
    *,
    production_commit: str = "UNCOMMITTED_WORKTREE",
) -> dict[str, Path]:
    """Write the five required v0.2 JSON artifacts."""

    result_dir = root / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    qsg = qsg_algebra_benchmark()
    dynamics = dynamics_benchmark()
    phase = phase_scan()
    final = run_final_theory_bench_v0_2(
        root, production_commit=production_commit
    )
    payloads = {
        "qsg_algebra_v0.2.json": qsg,
        "dynamics_v0.2.json": dynamics,
        "phase_scan_v0.2.json": phase,
        "final_theory_bench_v0.2.json": final,
    }
    written: dict[str, Path] = {}
    for name, payload in payloads.items():
        path = result_dir / name
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written[name] = path
    manifest = {
        "suite": "Final-Theory Bench v0.2 reproduction manifest",
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_commit": BASELINE_COMMIT,
        "production_commit": production_commit,
        "dependency_lock": {
            "path": "uv.lock",
            "sha256": _sha256(root / "uv.lock"),
        },
        "source_papers": _source_hashes(root),
        "seed_policy": {
            "randomness_used": False,
            "description": "all v0.2 production checks are exhaustive or deterministic",
        },
        "hardware": final["environment"],
        "exact_numerical_boundary": dynamics["exact_numerical_boundary"],
        "scientific_status": final["statuses"]["SCIENTIFIC_STATUS"],
        "artifact_hashes": [
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
            }
            for path in written.values()
        ],
    }
    manifest_path = result_dir / "reproduction_manifest_final_v0.2.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    written[manifest_path.name] = manifest_path
    return written
