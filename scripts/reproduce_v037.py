"""Verify or explicitly rerun the exact Final-Theory Bench v0.3.7 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from universe_lab.final_theory.q5_free_elimination_v037 import (
    VERDICT_PROVED,
    load_human_budget_v037,
    verify_q5_free_campaign_v037,
)
from universe_lab.final_theory.scalar_chain_v037 import (
    LEMMA,
    verify_general_scalar_chain_lemma_v037,
)
from universe_lab.final_theory.scope_addendum_v037 import (
    VERDICT as ADDENDUM_VERDICT,
)
from universe_lab.final_theory.scope_addendum_v037 import (
    compile_scope_addendum_v037,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _run_module(root: Path, module: str, *arguments: str) -> None:
    subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=root,
        check=True,
    )


def _run_script(root: Path, relative: str, *arguments: str) -> None:
    subprocess.run(
        [sys.executable, str(root / relative), *arguments],
        cwd=root,
        check=True,
    )


def _verify_scalar_chain(
    root: Path,
) -> dict[str, Any]:
    aggregate_path = root / "results/v0.3.7_general_scalar_chain_fiber.json"
    verification = verify_general_scalar_chain_lemma_v037(root)
    return {
        "artifact": aggregate_path.relative_to(root).as_posix(),
        "artifact_sha256": _sha256(aggregate_path),
        "verdict": verification["verdict"],
        "certificate_role_counts": verification["certificate_role_counts"],
        "certificate_count": len(verification["branch_checks"]),
        "aggregate_checks": verification["aggregate_checks"],
        "branches": verification["branch_checks"],
        "passed": (verification["passed"] and verification["verdict"] == LEMMA),
    }


def _verify_release_manifest(root: Path) -> dict[str, Any]:
    builder_path = root / "scripts/build_v037_release_manifest.py"
    spec = importlib.util.spec_from_file_location(
        "build_v037_release_manifest_for_check",
        builder_path,
    )
    if spec is None or spec.loader is None:
        return {
            "passed": False,
            "error": "release manifest builder could not be loaded",
        }
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        rebuilt = module.build_manifest(root)
        saved = _load_json(root / module.RESULT_PATH)
    except Exception as error:  # pragma: no cover - failure report path
        return {
            "passed": False,
            "error": f"{type(error).__name__}: {error}",
        }
    return {
        "artifact": module.RESULT_PATH,
        "file_count": saved.get("file_count"),
        "semantic_digest_sha256": saved.get("semantic_digest_sha256"),
        "rebuild_matches_exactly": rebuilt == saved,
        "passed": rebuilt == saved,
    }


def verify_v037(root: Path) -> dict[str, Any]:
    budget = load_human_budget_v037(root)
    saved_partition = _load_json(root / "results/v0.3.7_q5_free_partition.json")

    saved_addendum = _load_json(root / "results/v0.3.7_scope_addendum.json")
    rebuilt_addendum = compile_scope_addendum_v037(root)
    addendum_passed = bool(
        rebuilt_addendum["passed"] is True
        and rebuilt_addendum["verdict"] == ADDENDUM_VERDICT
        and rebuilt_addendum["semantic_digest_sha256"] == saved_addendum["semantic_digest_sha256"]
    )
    phase1 = verify_q5_free_campaign_v037(root)
    partition_passed = phase1["aggregate_checks"]["partition_passed"]
    scalar_chain = _verify_scalar_chain(root)
    release_manifest = _verify_release_manifest(root)
    passed = bool(
        partition_passed
        and addendum_passed
        and phase1["passed"]
        and scalar_chain["passed"]
        and release_manifest["passed"]
    )
    return {
        "schema_version": "final-theory-v0.3.7-reproduction-check",
        "budget_file_sha256": budget["sha256"],
        "partition": {
            "verdict": saved_partition["verdict"],
            "passed": partition_passed,
        },
        "phase1": {
            "verdict": phase1["verdict"],
            "certificate_role_counts": phase1["certificate_role_counts"],
            "certificate_count": len(phase1["certificate_checks"]),
            "failed_certificate_checks": [
                record for record in phase1["certificate_checks"] if not record["passed"]
            ],
            "aggregate_checks": phase1["aggregate_checks"],
            "passed": (phase1["passed"] and phase1["verdict"] == VERDICT_PROVED),
        },
        "phase2": scalar_chain,
        "scope_addendum": {
            "verdict": saved_addendum["verdict"],
            "passed": addendum_passed,
        },
        "release_manifest": release_manifest,
        "global_scientific_verdict": "FINAL_THEORY_OPEN",
        "passed": passed,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify", action="store_true")
    action.add_argument("--run-phase1", action="store_true")
    action.add_argument("--run-phase2", action="store_true")
    action.add_argument("--all", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    load_human_budget_v037(root)
    if arguments.run_phase1 or arguments.all:
        _run_module(
            root,
            "universe_lab.final_theory.q5_free_elimination_v037",
            "--run-phase1",
        )
        _run_module(
            root,
            "universe_lab.final_theory.scope_addendum_v037",
            "--write",
        )
    if arguments.run_phase2 or arguments.all:
        _run_module(
            root,
            "universe_lab.final_theory.scalar_chain_v037",
            "--run",
        )
    if arguments.run_phase1 or arguments.run_phase2 or arguments.all:
        _run_script(
            root,
            "scripts/build_v037_release_manifest.py",
        )
    summary = verify_v037(root)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
