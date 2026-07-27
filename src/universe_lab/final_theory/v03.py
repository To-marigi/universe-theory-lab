"""Novelty-first Final-Theory Bench v0.3 orchestration."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp

from universe_lab.final_theory.audit_v03 import (
    V02_ARTIFACT_FREEZE,
    V02_ARTIFACT_HASHES,
    baseline_audit,
    repository_inventory,
    sha256_file,
    source_manifest,
)
from universe_lab.final_theory.cpobc_v03 import (
    compile_cpobc_relations,
    cpobc_representation_search,
    paper_regression_benchmark,
)
from universe_lab.final_theory.extension_v03 import extension_benchmark
from universe_lab.final_theory.geometry_v03 import geometry_interference_benchmark
from universe_lab.final_theory.kraus_bell_v03 import kraus_bell_benchmark
from universe_lab.final_theory.validation_v03 import (
    held_out_audit_v0_3,
    mutation_benchmark_v0_3,
)

RESULT_NAMES = (
    "v0.3_source_manifest.json",
    "v0.3_repository_inventory.json",
    "v0.3_paper_regression.json",
    "v0.3_geometry_interference.json",
    "v0.3_kraus_bell.json",
    "v0.3_cpobc_relations.json",
    "v0.3_cpobc_search.json",
    "v0.3_extension.json",
    "final_theory_bench_v0.3.json",
)

REQUIRED_PROVENANCE_FIELDS = {
    "schema_version",
    "source_commit",
    "code_commit",
    "input_hashes",
    "source_paper_versions",
    "assumptions",
    "exact_numeric_distinction",
    "solver_and_version",
    "random_seeds",
    "completeness_scope",
    "resource_limits",
    "generated_artifact_hashes",
    "verdict",
    "unresolved_items",
}


def _solver_versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "sympy": sp.__version__,
        "numpy": np.__version__,
        "python_flint": importlib.metadata.version("python-flint"),
        "platform": platform.platform(),
    }


def _paper_versions(source_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": record["id"],
            "version": record["version"],
            "sha256": record["sha256"],
        }
        for record in source_data["sources"]
    ]


def _input_hashes(
    baseline: dict[str, Any], source_data: dict[str, Any]
) -> list[dict[str, str]]:
    result = [
        {
            "path": record["path"],
            "sha256": str(record["actual_sha256"]),
        }
        for record in baseline["frozen_artifacts"]
    ]
    result.extend(
        {
            "path": f"references/{record['local_file']}",
            "sha256": str(record["sha256"]).removeprefix("sha256:"),
        }
        for record in source_data["sources"]
    )
    return result


def _certificate_hashes(root: Path, category: str) -> list[dict[str, str]]:
    directory = root / "certificates" / category
    if not directory.exists():
        return []
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in directory.rglob("*") if item.is_file())
    ]


def _find_verdict(raw: dict[str, Any], fallback: str) -> str:
    for key in (
        "verdict",
        "geometry_quantumness_status",
        "kraus_bell_status",
        "paper_regression_status",
        "cpobc_relation_status",
        "cpobc_representation_status",
        "search_status",
        "status",
    ):
        value = raw.get(key)
        if isinstance(value, str):
            return value
    return fallback


def _envelope(
    raw: dict[str, Any],
    *,
    root: Path,
    source_data: dict[str, Any],
    baseline: dict[str, Any],
    code_commit: str,
    category: str,
    fallback_verdict: str,
) -> dict[str, Any]:
    payload = dict(raw)
    payload.update(
        {
            "schema_version": str(
                raw.get("schema_version", f"final-theory-{category}-v0.3.0")
            ),
            "source_commit": V02_ARTIFACT_FREEZE,
            "code_commit": code_commit,
            "input_hashes": _input_hashes(baseline, source_data),
            "source_paper_versions": _paper_versions(source_data),
            "assumptions": raw.get(
                "assumptions",
                [
                    "v0.2 artifact freeze is immutable",
                    "Track A invertible CPOBC and Track B Kraus channels are distinct",
                    "only exact or explicitly bounded results can pass a scientific gate",
                ],
            ),
            "exact_numeric_distinction": raw.get(
                "exact_numeric_distinction",
                {
                    "exact": "Fraction, integer combinatorics, and SymPy algebra",
                    "numeric": "no numeric residual is accepted as an exact certificate",
                },
            ),
            "solver_and_version": _solver_versions(),
            "random_seeds": raw.get(
                "random_seeds",
                {"used": False, "values": [], "policy": "deterministic production"},
            ),
            "completeness_scope": raw.get(
                "completeness_scope", "declared by the nested benchmark record"
            ),
            "resource_limits": raw.get(
                "resource_limits", ["see nested benchmark boundary"]
            ),
            "generated_artifact_hashes": _certificate_hashes(root, category),
            "verdict": _find_verdict(raw, fallback_verdict),
            "unresolved_items": raw.get("unresolved_items", []),
        }
    )
    return payload


def build_v0_3_payloads(
    root: Path,
    *,
    code_commit: str = "UNCOMMITTED_WORKTREE",
) -> dict[str, dict[str, Any]]:
    """Run all novelty-first v0.3 gates without writing artifacts."""

    baseline = baseline_audit(root)
    sources = source_manifest(root)
    inventory = repository_inventory(root)
    paper = paper_regression_benchmark()
    geometry = geometry_interference_benchmark(5)
    bell = kraus_bell_benchmark(5)
    relations = compile_cpobc_relations(4)
    search = cpobc_representation_search()
    extension = extension_benchmark(5)
    held_out = held_out_audit_v0_3()
    mutations = mutation_benchmark_v0_3()

    raw_payloads = {
        "v0.3_source_manifest.json": (sources, "source_manifest", sources["verdict"]),
        "v0.3_repository_inventory.json": (
            inventory,
            "repository_inventory",
            inventory["verdict"],
        ),
        "v0.3_paper_regression.json": (
            paper,
            "paper_regression",
            "PAPER_REGRESSION_PARTIAL",
        ),
        "v0.3_geometry_interference.json": (
            geometry,
            "geometry_interference",
            "GEOMETRY_INTERFERENCE_INCONCLUSIVE",
        ),
        "v0.3_kraus_bell.json": (
            bell,
            "kraus_bell",
            "KRAUS_BELL_CAUSALITY_INCONCLUSIVE",
        ),
        "v0.3_cpobc_relations.json": (
            relations,
            "cpobc_relation_dependencies",
            "CPOBC_RELATION_COMPILER_PARTIAL",
        ),
        "v0.3_cpobc_search.json": (
            search,
            "cpobc_representation",
            "CPOBC_SEARCH_INCONCLUSIVE",
        ),
        "v0.3_extension.json": (
            extension,
            "infinite_extension",
            "INFINITE_EXTENSION_BLOCKED",
        ),
    }
    payloads = {
        name: _envelope(
            raw,
            root=root,
            source_data=sources,
            baseline=baseline,
            code_commit=code_commit,
            category=category,
            fallback_verdict=fallback,
        )
        for name, (raw, category, fallback) in raw_payloads.items()
    }

    paper_status = payloads["v0.3_paper_regression.json"]["verdict"]
    geometry_status = payloads["v0.3_geometry_interference.json"]["verdict"]
    bell_status = payloads["v0.3_kraus_bell.json"]["verdict"]
    relation_status = payloads["v0.3_cpobc_relations.json"]["verdict"]
    search_status = payloads["v0.3_cpobc_search.json"]["verdict"]
    extension_status = payloads["v0.3_extension.json"]["verdict"]
    engineering_pass = (
        baseline["passed"]
        and paper["passed"]
        and geometry["passed"]
        and bell["engineering_checks_passed"]
        and relations["passed"]
        and search["passed"]
        and extension["finite_sequences"]["finite_checks_passed"]
        and mutations["passed"]
    )
    statuses = {
        "ENGINEERING_STATUS": (
            "ENGINEERING_PASS" if engineering_pass else "ENGINEERING_FAIL"
        ),
        "LITERATURE_BOUNDARY_STATUS": "LITERATURE_BOUNDARY_LOCKED",
        "PAPER_REGRESSION_STATUS": paper_status,
        "GEOMETRY_QUANTUMNESS_STATUS": geometry_status,
        "KRAUS_BELL_STATUS": bell_status,
        "CPOBC_RELATION_STATUS": relation_status,
        "CPOBC_REPRESENTATION_STATUS": search_status,
        "INFINITE_EXTENSION_STATUS": extension_status,
        "SCIENTIFIC_STATUS": "FINAL_THEORY_OPEN",
    }
    final_raw = {
        "suite": "Final-Theory Bench v0.3 / Novelty-First Quantum-Geometry Certification",
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline": baseline,
        "statuses": statuses,
        "question_answers": {
            "Q1_geometry_interference": geometry_status,
            "Q2_kraus_channel_bell": bell_status,
            "Q3_high_dimensional_cpobc": search_status,
            "Q4_infinite_extension": extension_status,
        },
        "paper_regression": paper_status,
        "relation_compiler": relation_status,
        "held_out": held_out,
        "mutations": mutations,
        "benchmark_integrity_passed": engineering_pass,
        "allowed_claims": sorted(set(statuses.values())),
        "prohibited_claims": [
            "CONTINUUM_PHASE_CANDIDATE",
            "EMERGENT_LORENTZ_SYMMETRY",
            "SPIN2_CANDIDATE",
            "SPIN2_GATE_PASS",
            "GRAVITON_FOUND",
            "EINSTEIN_DYNAMICS_RECOVERED",
            "FINAL_THEORY_COMPLETED",
            "QUANTUM_GEOMETRY_CANDIDATE",
            "KRAUS_BELL_CAUSALITY_PASS",
            "CPOBC_NONCOMMUTATIVE_REPRESENTATION_FOUND",
            "CPOBC_NO_REPRESENTATION_UNDER_ASSUMPTIONS",
            "OPERATOR_MEASURE_EXTENSION_PASS",
        ],
        "deferred_to_v0.4": [
            "large-N production sampler",
            "continuum scan and finite-size scaling",
            "dimension and correlation-length estimators",
            "coarse-graining and held-out symmetry reconstruction",
            "two-point, tensor, Spin, graviton, and Einstein gates",
        ],
        "verdict": "FINAL_THEORY_OPEN",
        "unresolved_items": [
            "nonzero Kraus-invariant geometric interference",
            "canonical spectator reduction if absent from the current Hilbert schema",
            "full finite-dimensional noncommutative CPOBC representation",
            "common-output infinite CP-instrument measure",
        ],
        "completeness_scope": (
            "exact finite causal-set work through n<=5; relation compilation n<=4; "
            "bounded structured d>=3 representation search"
        ),
        "resource_limits": [
            "brute-force causet canonicalisation is capped at n<=5",
            "no unbounded Groebner/component decomposition was attempted",
            "no continuum or large-N computation belongs to v0.3",
        ],
    }
    payloads["final_theory_bench_v0.3.json"] = _envelope(
        final_raw,
        root=root,
        source_data=sources,
        baseline=baseline,
        code_commit=code_commit,
        category="final_v0.3",
        fallback_verdict="FINAL_THEORY_OPEN",
    )
    return payloads


def write_v0_3_artifacts(
    root: Path,
    *,
    code_commit: str = "UNCOMMITTED_WORKTREE",
) -> dict[str, Path]:
    """Write all required v0.3 JSON artifacts and their hash manifest."""

    result_dir = root / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    payloads = build_v0_3_payloads(root, code_commit=code_commit)
    written: dict[str, Path] = {}
    for name in RESULT_NAMES:
        path = result_dir / name
        path.write_text(
            json.dumps(payloads[name], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written[name] = path

    source_data = payloads["v0.3_source_manifest.json"]
    baseline = payloads["final_theory_bench_v0.3.json"]["baseline"]
    artifact_hashes = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in written.values()
    ]
    manifest_raw = {
        "suite": "Final-Theory Bench v0.3 reproduction manifest",
        "generated_at": datetime.now(UTC).isoformat(),
        "dependency_lock": {
            "path": "uv.lock",
            "sha256": sha256_file(root / "uv.lock"),
        },
        "v02_artifact_hash_registry": V02_ARTIFACT_HASHES,
        "artifact_hashes": artifact_hashes,
        "test_commands": [
            "uv run ruff check .",
            "uv run pytest",
            "uv run mypy",
            "uv run finaltheory --version 0.3",
        ],
        "randomness_used": False,
        "verdict": "FINAL_THEORY_OPEN",
        "unresolved_items": payloads["final_theory_bench_v0.3.json"][
            "unresolved_items"
        ],
        "completeness_scope": payloads["final_theory_bench_v0.3.json"][
            "completeness_scope"
        ],
        "resource_limits": payloads["final_theory_bench_v0.3.json"][
            "resource_limits"
        ],
    }
    manifest = _envelope(
        manifest_raw,
        root=root,
        source_data=source_data,
        baseline=baseline,
        code_commit=code_commit,
        category="reproduction_manifest_final_v0.3",
        fallback_verdict="FINAL_THEORY_OPEN",
    )
    manifest["generated_artifact_hashes"] = artifact_hashes
    manifest_path = result_dir / "reproduction_manifest_final_v0.3.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    written[manifest_path.name] = manifest_path
    return written


def verify_v0_3_artifacts(root: Path) -> dict[str, Any]:
    """Verify required fields and hashes in the checked-in v0.3 artifacts."""

    result_dir = root / "results"
    manifest_path = result_dir / "reproduction_manifest_final_v0.3.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hash_records = manifest["artifact_hashes"]
    hash_checks = []
    for record in hash_records:
        path = root / record["path"]
        actual = sha256_file(path) if path.exists() else None
        hash_checks.append(
            {
                "path": record["path"],
                "expected_sha256": record["sha256"],
                "actual_sha256": actual,
                "matches": actual == record["sha256"],
            }
        )
    payloads = {
        name: json.loads((result_dir / name).read_text(encoding="utf-8"))
        for name in RESULT_NAMES
    }
    field_checks = {
        name: REQUIRED_PROVENANCE_FIELDS <= payload.keys()
        for name, payload in payloads.items()
    }
    code_commits = {
        payload["code_commit"] for payload in payloads.values()
    } | {manifest["code_commit"]}
    checks = {
        "artifact_name_set_exact": {
            record["path"].removeprefix("results/")
            for record in hash_records
        }
        == set(RESULT_NAMES),
        "artifact_hashes_match": all(item["matches"] for item in hash_checks),
        "required_fields_present": all(field_checks.values())
        and REQUIRED_PROVENANCE_FIELDS <= manifest.keys(),
        "single_code_commit": len(code_commits) == 1,
        "source_commit_frozen": all(
            payload["source_commit"] == V02_ARTIFACT_FREEZE
            for payload in payloads.values()
        )
        and manifest["source_commit"] == V02_ARTIFACT_FREEZE,
        "scientific_status_open": (
            payloads["final_theory_bench_v0.3.json"]["statuses"][
                "SCIENTIFIC_STATUS"
            ]
            == "FINAL_THEORY_OPEN"
            and manifest["verdict"] == "FINAL_THEORY_OPEN"
        ),
    }
    return {
        "manifest": manifest_path.relative_to(root).as_posix(),
        "hash_checks": hash_checks,
        "field_checks": field_checks,
        "code_commits": sorted(code_commits),
        "checks": checks,
        "passed": all(checks.values()),
    }
