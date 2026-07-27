"""Executable independent audit.

Run with:
    uv run python -m universe_lab.qgaudit.audit
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from universe_lab.qgaudit.mutations import run_all_mutations
from universe_lab.qgaudit.oracle import (
    causal_pair_values,
    causal_relation,
    discrete_kernel,
    sprinkle,
)
from universe_lab.qgaudit.resources import as_payload, estimate_resources
from universe_lab.qgaudit.statistics import binned_rmse, finite_size_fit, summarize

COUNTS = (225, 450, 900, 1800, 3600, 7200, 18_000)
EXECUTION_COUNTS = (225, 450, 900, 1800, 3600)
SEEDS = tuple(range(30_001, 30_031))
MASS = 4.0
RADIUS = 1.0
EPSILON = 0.25


def _git_state(root: Path) -> dict[str, str | None]:
    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    branch_result = git("symbolic-ref", "--short", "HEAD")
    commit_result = git("rev-parse", "--verify", "HEAD")
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else None
    return {
        "branch": branch,
        "commit": commit,
        "repository_state": "COMMITTED" if commit is not None else "UNBORN_BRANCH_NO_COMMIT",
    }


def _gpu_state() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"detected": False, "details": None, "used_by_audit": False}
    details = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return {"detected": bool(details), "details": details or None, "used_by_audit": False}


def _lock_sha256(root: Path) -> str | None:
    lock = root / "uv.lock"
    return hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None


def environment_payload(root: Path) -> dict[str, Any]:
    dependencies: dict[str, str | None] = {}
    for name in ("numpy", "scipy", "psutil", "pytest", "ruff"):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = None
    return {
        "git": _git_state(root),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "cpu": {
            "processor": platform.processor(),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
        },
        "gpu": _gpu_state(),
        "dependencies": dependencies,
        "uv_lock_sha256": _lock_sha256(root),
        "numpy_configuration": {
            "blas_lapack": "runtime-selected; see numpy.show_config in exact command log"
        },
        "process_id": os.getpid(),
    }


def _one_seed(count: int, seed: int) -> tuple[float, int]:
    sample = sprinkle(count, radius=RADIUS, epsilon=EPSILON, seed=seed)
    relation = causal_relation(sample.points)
    kernel = discrete_kernel(relation, mass=MASS, density=sample.density)
    tau, values = causal_pair_values(sample, kernel)
    rmse = binned_rmse(
        tau,
        values,
        mass=MASS,
        radius=RADIUS,
        bins=18,
        minimum_bin_count=10,
    )
    return rmse, int(len(tau))


def run_audit(root: Path) -> dict[str, Any]:
    calibration_start = time.perf_counter()
    _one_seed(1800, SEEDS[0])
    measured_seconds = time.perf_counter() - calibration_start
    preflight = {
        str(count): as_payload(
            estimate_resources(
                count,
                seeds=len(SEEDS),
                measured_count=1800,
                measured_seconds_per_seed=measured_seconds,
            )
        )
        for count in COUNTS
    }
    levels: list[dict[str, Any]] = []
    seed_rmse_by_level: list[list[float]] = []
    executed_counts: list[int] = []
    for count in COUNTS:
        estimate = preflight[str(count)]
        if count not in EXECUTION_COUNTS:
            reason = estimate["reason"] or (
                "not run: count exceeds the predeclared feasible audit profile; "
                "30-seed execution was not authorized by the 180 s per-level budget"
            )
            levels.append(
                {
                    "count": count,
                    "status": "RESOURCE_BLOCKED",
                    "seeds_requested": len(SEEDS),
                    "seeds_completed": 0,
                    "reason": reason,
                    "preflight": estimate,
                }
            )
            continue
        start = time.perf_counter()
        rmses: list[float] = []
        pair_counts: list[int] = []
        for seed in SEEDS:
            rmse, pair_count = _one_seed(count, seed)
            rmses.append(rmse)
            pair_counts.append(pair_count)
        summary = summarize(rmses)
        levels.append(
            {
                "count": count,
                "status": "NUMERICALLY_REPRODUCED",
                "seeds_requested": len(SEEDS),
                "seeds_completed": len(rmses),
                "seeds": list(SEEDS),
                "rmse_by_seed": rmses,
                "rmse_summary": asdict(summary),
                "pair_count_summary": asdict(summarize(pair_counts)),
                "elapsed_seconds": time.perf_counter() - start,
                "preflight": estimate,
            }
        )
        executed_counts.append(count)
        seed_rmse_by_level.append(rmses)
    scaling = finite_size_fit(executed_counts, seed_rmse_by_level, bootstrap_samples=500)
    mutations = run_all_mutations()
    mutation_pass = all(bool(value["detected"]) for value in mutations.values())
    executed_levels = [level for level in levels if level["status"] == "NUMERICALLY_REPRODUCED"]
    means = [float(level["rmse_summary"]["mean"]) for level in executed_levels]
    small_n_pass = mutation_pass and means[-1] < means[0]
    return {
        "suite": "QG-Bench v0.1 independent audit",
        "generated_at": datetime.now(UTC).isoformat(),
        "oracle_independence": {
            "imports_universe_lab_qgbench": False,
            "continuum_evaluator": "Gauss hypergeometric representation of P_nu",
            "discrete_evaluator": "independent topological ordering and triangular Volterra solve",
        },
        "environment": environment_payload(root),
        "configuration": {
            "counts_requested": list(COUNTS),
            "counts_executed": executed_counts,
            "mass": MASS,
            "curvature_radius": RADIUS,
            "epsilon": EPSILON,
            "seeds": list(SEEDS),
            "seed_count": len(SEEDS),
            "fixed_count_process": True,
        },
        "resource_preflight": {
            "calibration_count": 1800,
            "measured_seconds_per_seed": measured_seconds,
            "per_level_wall_time_budget_seconds": 180.0,
            "levels": preflight,
        },
        "levels": levels,
        "finite_size_scaling": scaling,
        "mutations": mutations,
        "verdicts": {
            "small_n": (
                "SMALL_N_REPRODUCTION_PASS" if small_n_pass else "FAIL"
            ),
            "paper_scale_n18000_x30": "RESOURCE_BLOCKED",
            "overall": "PARTIAL" if small_n_pass else "FAIL",
        },
        "claim_boundary": (
            "The independent audit tests a finite-size numerical reproduction only. "
            "N=18000 x 30 seeds was not executed and is not a PASS."
        ),
    }


def main() -> int:
    root = Path.cwd()
    result = run_audit(root)
    destination = root / "results" / "qgbench_v0.1_audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(destination)
    print(json.dumps(result["verdicts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
