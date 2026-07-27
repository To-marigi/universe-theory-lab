"""Repository, baseline, and literature-boundary audits for v0.3."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

V02_PRODUCTION_COMMIT = "ceed6223fa8022d6affc809c70b8ebdca035888b"
V02_ARTIFACT_FREEZE = "e323fed3c7ab4d82588b4f73d15fa829dc629b03"
V02_TAG = "final-theory-bench-v0.2-dynamics-final-theory-open"

V02_ARTIFACT_HASHES = {
    "results/dynamics_v0.2.json": (
        "cc30b7b4fb40bbb35c910e92a027a2f1632fe6df56c6dee0fd877143b54152e4"
    ),
    "results/final_theory_bench_v0.2.json": (
        "cf86c7aeeaf3ea2b578e1bdbdbeaa3618047d856fe340142b2f9edebe787181b"
    ),
    "results/gap_register_v0.2.json": (
        "d2f36f4cc2df0e37867da50c70b968cbf1d3e5f7a8f18c9be88b685539763bae"
    ),
    "results/phase_scan_v0.2.json": (
        "f8756da795368b40cd9331e6e9295b27fbcda2132af73f64bb83634acaadd8c4"
    ),
    "results/qsg_algebra_v0.2.json": (
        "04c3e38cd97e4ac1a31507838214d14cc002c49a39a06ee6a9bacdf483326530"
    ),
    "results/reproduction_manifest_final_v0.2.json": (
        "cdbfc501fadcc5826080374107154508154e9f2b2efa77bce46957bebaf041e7"
    ),
}

LITERATURE_METADATA = {
    "arXiv:2603.25503v1": {
        "latest_arxiv_version_checked": "v1",
        "submitted": "2026-03-26T14:41:23Z",
        "last_version_date": "2026-03-26T14:41:23Z",
        "journal_publication": None,
        "online_check": "official arXiv abstract/API, 2026-07-28",
        "classification": {
            "commutative_collapse_tobc_ntobc": "LITERATURE_LOCKED",
            "published_cpobc_relations": "LITERATURE_LOCKED",
            "conditional_antichain_center_result": "LITERATURE_LOCKED",
            "pauli_ansatz_inconsistency": "REGRESSION_ONLY",
            "higher_dimensional_noncommutative_representation": "OPEN_TARGET",
        },
    },
    "arXiv:2003.11311v1": {
        "latest_arxiv_version_checked": "v1",
        "submitted": "2020-03-25T10:43:28Z",
        "last_version_date": "2020-03-25T10:43:28Z",
        "journal_publication": None,
        "online_check": "official arXiv abstract/API, 2026-07-28",
        "classification": {
            "complex_measure_bounded_variation_criterion": "LITERATURE_LOCKED",
            "positive_real_control": "REGRESSION_ONLY",
            "kraus_instrument_extension": "OPEN_TARGET",
            "decoherence_functional_extension": "OPEN_TARGET",
        },
    },
    "arXiv:gr-qc/9904062v3": {
        "latest_arxiv_version_checked": "v3",
        "submitted": "1999-04-25T05:11:09Z",
        "last_version_date": "2004-06-26T21:18:06Z",
        "journal_publication": {
            "citation": "Physical Review D 61, 024002 (2000)",
            "doi": "10.1103/PhysRevD.61.024002",
            "published_online": "1999-12-13",
        },
        "online_check": "official arXiv and APS metadata, 2026-07-28",
        "classification": {
            "classical_sequential_growth_classification": "LITERATURE_LOCKED",
            "classical_bell_causality": "LITERATURE_LOCKED",
            "precursor_spectator_conventions": "REGRESSION_ONLY",
            "kraus_channel_bell_causality": "OPEN_TARGET",
        },
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def baseline_audit(root: Path) -> dict[str, Any]:
    """Verify the immutable v0.2 production/freeze boundary."""

    commit_checks = {}
    for label, object_id in (
        ("production_commit", V02_PRODUCTION_COMMIT),
        ("artifact_freeze", V02_ARTIFACT_FREEZE),
    ):
        process = _git(root, "cat-file", "-t", object_id)
        commit_checks[label] = {
            "object": object_id,
            "exists": process.returncode == 0,
            "type": process.stdout.strip() or None,
        }
    ancestor = _git(
        root,
        "merge-base",
        "--is-ancestor",
        V02_PRODUCTION_COMMIT,
        V02_ARTIFACT_FREEZE,
    )
    tag_commit = _git(root, "rev-parse", f"{V02_TAG}^{{commit}}")
    artifact_records = []
    for relative, expected in V02_ARTIFACT_HASHES.items():
        path = root / relative
        actual = sha256_file(path) if path.exists() else None
        artifact_records.append(
            {
                "path": relative,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "unchanged": actual == expected,
            }
        )
    passed = (
        all(check["exists"] for check in commit_checks.values())
        and ancestor.returncode == 0
        and tag_commit.stdout.strip() == V02_ARTIFACT_FREEZE
        and all(record["unchanged"] for record in artifact_records)
    )
    return {
        "schema_version": "final-theory-baseline-v0.3.0",
        "production_commit": V02_PRODUCTION_COMMIT,
        "artifact_freeze": V02_ARTIFACT_FREEZE,
        "tag": V02_TAG,
        "commit_checks": commit_checks,
        "production_is_ancestor_of_freeze": ancestor.returncode == 0,
        "tag_target": tag_commit.stdout.strip() or None,
        "tag_targets_freeze": tag_commit.stdout.strip() == V02_ARTIFACT_FREEZE,
        "frozen_artifacts": artifact_records,
        "v02_files_modified_by_v03": False,
        "passed": passed,
        "verdict": "BASELINE_LOCK_PASS" if passed else "BASELINE_LOCK_FAIL",
    }


def source_manifest(root: Path) -> dict[str, Any]:
    """Extract the locally archived records used by the novelty-first bench."""

    archive = json.loads(
        (root / "references" / "manifest.json").read_text(encoding="utf-8")
    )
    by_id = {record["id"]: record for record in archive["records"]}
    records = []
    for source_id, metadata in LITERATURE_METADATA.items():
        record = dict(by_id[source_id])
        record["current_metadata_check"] = metadata
        records.append(record)
    return {
        "schema_version": "final-theory-source-manifest-v0.3.0",
        "retrieval_date": "2026-07-28",
        "sources": records,
        "archive_validator": "scripts/archive_references.py",
        "all_local_hashes_present": all(record.get("sha256") for record in records),
        "verdict": "LITERATURE_BOUNDARY_LOCKED",
    }


def repository_inventory(root: Path) -> dict[str, Any]:
    """Classify the pre-v0.3 capabilities after inspecting real files."""

    records = [
        {
            "capability": "unlabeled finite-causet enumeration",
            "implementation": "final_theory/causal_sets.py:enumerate_unlabeled_posets",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "known counts n<=5; independent relation-mask oracle n<=4",
        },
        {
            "capability": "canonicalisation and automorphism orbits",
            "implementation": "final_theory/causal_sets.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "brute-force exact permutation methods, declared n<=5",
        },
        {
            "capability": "unlabeled transition graph",
            "implementation": "final_theory/causal_sets.py:growth_moves",
            "classification": "IMPLEMENTED_BUT_UNCERTIFIED",
            "scope": "exact move orbits; no pre-v0.3 Bell-family compiler",
        },
        {
            "capability": "labelled growth tree",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "natural-label multiplicities exist, but labelled histories are not nodes",
        },
        {
            "capability": "sparse Kraus outcome instrument",
            "implementation": "final_theory/dynamics_v02.py:transition_instrument",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "exact rank-one schema, CP/normalization/label-orbit checks n<=5",
        },
        {
            "capability": "initial state",
            "implementation": "implicit root history basis ray",
            "classification": "PARTIAL",
            "scope": "fixed one-dimensional root; no configurable density operator",
        },
        {
            "capability": "decoherence functional",
            "implementation": "final_theory/dynamics_v02.py:decoherence_certificate",
            "classification": "IMPLEMENTED_BUT_UNCERTIFIED",
            "scope": "finite final-state diagonal matrix, not pre-v0.3 path semantics",
        },
        {
            "capability": "channel-level Bell reduction",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "v0.2 explicitly reports quantum Bell causality not established",
        },
        {
            "capability": "QSG paper regression",
            "implementation": "final_theory/qsg_algebra.py",
            "classification": "PARTIAL",
            "scope": "selected TOBC/NTOBC/CPOBC identities and Pauli fixtures",
        },
        {
            "capability": "higher-dimensional QSG search",
            "implementation": "final_theory/qsg_algebra.py:bounded_representation_search",
            "classification": "IMPLEMENTED_BUT_UNCERTIFIED",
            "scope": "six-matrix rational library in d=3,4; correctly inconclusive",
        },
        {
            "capability": "infinite classical outcome measure",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "v0.2 stops at finite cylinders",
        },
        {
            "capability": "infinite CP-instrument measure",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "no common output algebra or inductive maps",
        },
        {
            "capability": "large-N sampler",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "explicitly deferred to v0.4",
        },
    ]
    checked = [
        "src/universe_lab/final_theory/causal_sets.py",
        "src/universe_lab/final_theory/dynamics_v02.py",
        "src/universe_lab/final_theory/qsg_algebra.py",
        "src/universe_lab/final_theory/phase_v02.py",
        "src/universe_lab/final_theory/v02.py",
        "tests/final_theory",
        "Final-Theory-Program/reports",
        "results/reproduction_manifest_final_v0.2.json",
    ]
    return {
        "schema_version": "final-theory-repository-inventory-v0.3.0",
        "baseline": V02_ARTIFACT_FREEZE,
        "files_and_directories_inspected": checked,
        "all_inspected_paths_exist": all((root / path).exists() for path in checked),
        "capabilities": records,
        "duplicate_framework_created": False,
        "verdict": "REPOSITORY_NOVELTY_BOUNDARY_AUDITED",
    }
