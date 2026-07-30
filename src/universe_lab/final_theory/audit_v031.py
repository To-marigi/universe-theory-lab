"""Immutable v0.3 baseline and repository capability audit for v0.3.1."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from universe_lab.final_theory.audit_v03 import sha256_file

V03_PRODUCTION_COMMIT = "f05d3b12c26f027e83de0bb4a1c354a058dc4581"
V03_ARTIFACT_FREEZE = "3ccbc66cc2cf868bf2a33ab96d4dd46e729d5f09"
V03_TAG = "final-theory-bench-v0.3-novelty-first-open"
V03_BRANCH = "codex/final-theory-v0.3-novelty-first-20260728"
V031_BRANCH = "codex/final-theory-v0.3.1-literature-locked-qsg-lift-20260728"

V03_ARTIFACT_HASHES = {
    "results/v0.3_source_manifest.json": (
        "70790ee24392dfb8a642bf18e2bf37ab9c146ca07d5fca9e1e272a1b0e68966f"
    ),
    "results/v0.3_repository_inventory.json": (
        "8c07ca7234cf272d101c1e84771b3f5c69a782152b273c400476b555240d05a8"
    ),
    "results/v0.3_paper_regression.json": (
        "62641debd58a3aff0467e291c0cad7619f7eec009deb36f25adb1636c48f5605"
    ),
    "results/v0.3_geometry_interference.json": (
        "6798775761305776401b34f215b951295db55f316bd3439fda629ad8d49a93d1"
    ),
    "results/v0.3_kraus_bell.json": (
        "986c20af591464ee667d246b05086b281a737c749c8a729a0c71ba5df482e23f"
    ),
    "results/v0.3_cpobc_relations.json": (
        "486daad731347fa946d48ce47b74ee8dcc762cb6135b140d92d9b26e69eee8cb"
    ),
    "results/v0.3_cpobc_search.json": (
        "fa87db4b5156d7411d05fcc587e8fc043673ebae46c896b09fa5b64ce499be85"
    ),
    "results/v0.3_extension.json": (
        "13143e5509d65eb8d7fa88e2dfdff19809a5afb1abb5ff030740e1479a18e328"
    ),
    "results/final_theory_bench_v0.3.json": (
        "8cb90dc2863b62ed0c79fe60554feb9d8675794464ef453cb98b70e17a2d9e5c"
    ),
    "results/reproduction_manifest_final_v0.3.json": (
        "0fa49ac39af5404fb85859086398267f1460873668c605a1f3c59e5ce843137b"
    ),
}


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _object_check(root: Path, object_id: str) -> dict[str, Any]:
    process = _git(root, "cat-file", "-t", object_id)
    return {
        "object": object_id,
        "exists": process.returncode == 0,
        "type": process.stdout.strip() or None,
    }


def resolve_frozen_branch(root: Path, branch: str) -> subprocess.CompletedProcess[str]:
    """Resolve a frozen branch name in a fresh clone as well as in a working copy.

    ``git clone`` and ``actions/checkout`` create a local head only for the ref
    they check out.  Every other branch exists solely as
    ``refs/remotes/origin/<branch>``, and git's revision rules do not fall back
    to a remote-tracking ref for a bare name, so ``git rev-parse <branch>``
    fails in any clone and succeeds only where that head was created by hand.

    Try the bare name first, so a checked-out working copy keeps its existing
    behaviour, then the remote-tracking ref.  Both paths resolve to the same
    commit, so the recorded audit values are unchanged.
    """

    process = _git(root, "rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}")
    if process.returncode == 0 and process.stdout.strip():
        return process
    return _git(
        root,
        "rev-parse",
        "--verify",
        "--quiet",
        f"refs/remotes/origin/{branch}^{{commit}}",
    )


def baseline_audit_v0_3_1(
    root: Path,
    *,
    check_remote: bool = False,
) -> dict[str, Any]:
    """Verify the frozen v0.3 boundary without changing it."""

    production = _object_check(root, V03_PRODUCTION_COMMIT)
    freeze = _object_check(root, V03_ARTIFACT_FREEZE)
    ancestor = _git(
        root,
        "merge-base",
        "--is-ancestor",
        V03_PRODUCTION_COMMIT,
        V03_ARTIFACT_FREEZE,
    )
    tag_target = _git(root, "rev-parse", f"{V03_TAG}^{{commit}}")
    branch_target = resolve_frozen_branch(root, V03_BRANCH)
    status = _git(root, "status", "--porcelain")

    artifact_records: list[dict[str, Any]] = []
    for relative, expected in V03_ARTIFACT_HASHES.items():
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

    remote: dict[str, Any] = {
        "checked": check_remote,
        "remote": "universe",
        "branch": None,
        "tag_object": None,
        "tag_target": None,
        "passed": None,
    }
    if check_remote:
        process = _git(
            root,
            "ls-remote",
            "--heads",
            "--tags",
            "universe",
            V03_BRANCH,
            V03_TAG,
            f"{V03_TAG}^{{}}",
        )
        remote["returncode"] = process.returncode
        if process.returncode == 0:
            refs = {
                ref: object_id
                for line in process.stdout.splitlines()
                if line.strip()
                for object_id, ref in [line.split(maxsplit=1)]
            }
            remote["branch"] = refs.get(f"refs/heads/{V03_BRANCH}")
            remote["tag_object"] = refs.get(f"refs/tags/{V03_TAG}")
            remote["tag_target"] = refs.get(f"refs/tags/{V03_TAG}^{{}}")
            remote["passed"] = (
                remote["branch"] == V03_ARTIFACT_FREEZE
                and remote["tag_target"] == V03_ARTIFACT_FREEZE
                and remote["tag_object"] is not None
            )
        else:
            remote["passed"] = False
            remote["stderr"] = process.stderr.strip()

    passed = (
        production["exists"]
        and production["type"] == "commit"
        and freeze["exists"]
        and freeze["type"] == "commit"
        and ancestor.returncode == 0
        and tag_target.stdout.strip() == V03_ARTIFACT_FREEZE
        and branch_target.stdout.strip() == V03_ARTIFACT_FREEZE
        and all(record["unchanged"] for record in artifact_records)
        and (not check_remote or remote["passed"] is True)
    )
    return {
        "schema_version": "final-theory-baseline-v0.3.1",
        "production_commit": V03_PRODUCTION_COMMIT,
        "artifact_freeze": V03_ARTIFACT_FREEZE,
        "tag": V03_TAG,
        "frozen_branch": V03_BRANCH,
        "working_branch": V031_BRANCH,
        "commit_checks": {
            "production_commit": production,
            "artifact_freeze": freeze,
        },
        "production_is_ancestor_of_freeze": ancestor.returncode == 0,
        "tag_target": tag_target.stdout.strip() or None,
        "tag_targets_freeze": tag_target.stdout.strip() == V03_ARTIFACT_FREEZE,
        "frozen_branch_target": branch_target.stdout.strip() or None,
        "frozen_branch_targets_freeze": (
            branch_target.stdout.strip() == V03_ARTIFACT_FREEZE
        ),
        "frozen_artifacts": artifact_records,
        "v03_artifacts_unchanged": all(
            record["unchanged"] for record in artifact_records
        ),
        "working_tree_clean_at_audit": status.stdout == "",
        "working_tree_porcelain": status.stdout.splitlines(),
        "remote": remote,
        "passed": passed,
        "verdict": "V0_3_BASELINE_LOCK_PASS" if passed else "V0_3_BASELINE_LOCK_FAIL",
    }


def repository_inventory_v0_3_1(root: Path) -> dict[str, Any]:
    """Classify capabilities inherited from the frozen v0.3 implementation."""

    records = [
        {
            "capability": "causet generation",
            "implementation": "src/universe_lab/final_theory/causal_sets.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "all unlabeled finite posets through n<=5",
        },
        {
            "capability": "labelled / unlabelled canonicalisation",
            "implementation": "src/universe_lab/final_theory/causal_sets.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "exact permutation canonicalisation and quotient metadata",
        },
        {
            "capability": "automorphism handling",
            "implementation": "src/universe_lab/final_theory/causal_sets.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "exact finite automorphism orbits and multiplicities",
        },
        {
            "capability": "transition graph",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "131 transition orbits through source n<=4",
        },
        {
            "capability": "Bell partners, pairs, and families",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "373 Bell-pair orbits and 146 families through source n<=4",
        },
        {
            "capability": "precursor / spectator extraction",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "exact orbit-level precursor and common-spectator metadata",
        },
        {
            "capability": "CPOBC equation generation",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_BUT_PARTIAL",
            "scope": "641 cross-stage instances; paper operator compilation only Eqs. 103-106",
        },
        {
            "capability": "noncommutative word representation",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_BUT_PARTIAL",
            "scope": "ordered word lists and free inverse cancellation; no full dependency ideal",
        },
        {
            "capability": "matrix substitution and inverse handling",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_BUT_PARTIAL",
            "scope": "exact SymPy for finite fixtures and necessary relations",
        },
        {
            "capability": "exact arithmetic",
            "implementation": "src/universe_lab/final_theory",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "integers, Fraction, exact SymPy algebra",
        },
        {
            "capability": "d=3 / d=4 search",
            "implementation": "src/universe_lab/final_theory/cpobc_v03.py",
            "classification": "IMPLEMENTED_BUT_SCIENTIFICALLY_MISLABELLED",
            "scope": (
                "14 exact matrix points are valid diagnostics, but not a Jordan-stratum "
                "search or full compiled-relation representation search"
            ),
        },
        {
            "capability": "Kraus profile",
            "implementation": "src/universe_lab/final_theory/kraus_bell_v03.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "FORMULATION_MISMATCH retained as a separate track",
        },
        {
            "capability": "decoherence functional",
            "implementation": "src/universe_lab/final_theory/geometry_v03.py",
            "classification": "IMPLEMENTED_AND_CERTIFIED",
            "scope": "orthogonal-record diagonal history functional only",
        },
        {
            "capability": "extendible commutative CSG positive control",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "required by v0.3.1 as literature-locked regression",
        },
        {
            "capability": "full n<=4 operator/dependency compiler",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "v0.3 explicitly records GC/MSR/dependency gaps",
        },
        {
            "capability": "complete d=3 Jordan-stratum solver",
            "implementation": None,
            "classification": "ABSENT",
            "scope": "no complete component decomposition or saturation",
        },
    ]
    inspected = [
        "src/universe_lab/final_theory/causal_sets.py",
        "src/universe_lab/final_theory/cpobc_v03.py",
        "src/universe_lab/final_theory/geometry_v03.py",
        "src/universe_lab/final_theory/kraus_bell_v03.py",
        "src/universe_lab/final_theory/extension_v03.py",
        "tests/final_theory",
        "Final-Theory-Program/reports/v0.3_cpobc_relation_compiler.md",
        "results/final_theory_bench_v0.3.json",
        "results/reproduction_manifest_final_v0.3.json",
    ]
    return {
        "schema_version": "final-theory-repository-inventory-v0.3.1",
        "baseline": V03_ARTIFACT_FREEZE,
        "files_and_directories_inspected": inspected,
        "all_inspected_paths_exist": all((root / path).exists() for path in inspected),
        "capabilities": records,
        "classification_vocabulary": [
            "IMPLEMENTED_AND_CERTIFIED",
            "IMPLEMENTED_BUT_PARTIAL",
            "IMPLEMENTED_BUT_SCIENTIFICALLY_MISLABELLED",
            "DUPLICATED",
            "STUB",
            "ABSENT",
        ],
        "duplicate_framework_created": False,
        "verdict": "V0_3_1_REPOSITORY_BOUNDARY_AUDITED",
    }
