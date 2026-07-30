"""Verify the v0.3.8 canonical-LF migration without rerunning Sage."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
    verify_line_ending_bridge,
)
from universe_lab.final_theory import q5_free_elimination_v037 as phase1_module
from universe_lab.final_theory import scalar_chain_v037 as phase2_module
from universe_lab.final_theory import scope_addendum_v037 as scope_module
from universe_lab.final_theory.q5_free_elimination_v037 import VERDICT_PROVED
from universe_lab.final_theory.scalar_chain_v037 import LEMMA
from universe_lab.final_theory.scope_addendum_v037 import (
    VERDICT as SCOPE_ADDENDUM_VERDICT,
)

BRIDGE_PATH = "results/v0.3.8_line_ending_bridge.json"
RELEASE_MANIFEST_PATH = "results/v0.3.8_release_manifest.json"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return payload


def _load_script_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_bridge(root: Path) -> tuple[dict[str, Any], LegacyRawDigestResolver]:
    """Rebuild and strictly verify the frozen line-ending bridge."""

    bridge_path = root / BRIDGE_PATH
    saved = load_line_ending_bridge(bridge_path)
    strict_verification = verify_line_ending_bridge(root, saved)
    builder = _load_script_module(
        "build_v038_line_ending_bridge_for_reproduction",
        root / "scripts/build_v038_line_ending_bridge.py",
    )
    rebuilt = builder.build_ledger(root)
    regenerated_exactly = bool(
        rebuilt == saved and builder.render_ledger(rebuilt) == bridge_path.read_bytes()
    )
    summary = {
        **strict_verification,
        "artifact": BRIDGE_PATH,
        "regenerated_exactly": regenerated_exactly,
    }
    summary["passed"] = bool(strict_verification["passed"] and regenerated_exactly)
    return summary, LegacyRawDigestResolver(root, saved)


@contextmanager
def _legacy_digest_mode(
    resolver: LegacyRawDigestResolver,
) -> Iterator[None]:
    """Temporarily adapt frozen verifiers to their declared byte serialization."""

    modules = (phase1_module, phase2_module, scope_module)
    original_hashers = [module._sha256 for module in modules]
    try:
        for module in modules:
            module._sha256 = resolver.sha256
        yield
    finally:
        for module, original in zip(modules, original_hashers, strict=True):
            module._sha256 = original


def verify_scientific_artifacts(
    root: Path,
    resolver: LegacyRawDigestResolver,
) -> dict[str, Any]:
    """Run the frozen semantic/gate checks using explicit legacy-byte resolution."""

    saved_addendum = _load_json(root / "results/v0.3.7_scope_addendum.json")
    with _legacy_digest_mode(resolver):
        phase1 = phase1_module.verify_q5_free_campaign_v037(root)
        phase2 = phase2_module.verify_general_scalar_chain_lemma_v037(root)
        rebuilt_addendum = scope_module.compile_scope_addendum_v037(root)

    phase1_passed = bool(phase1["passed"] and phase1["verdict"] == VERDICT_PROVED)
    phase2_passed = bool(phase2["passed"] and phase2["verdict"] == LEMMA)
    scope_passed = bool(
        rebuilt_addendum["passed"] is True
        and rebuilt_addendum["verdict"] == SCOPE_ADDENDUM_VERDICT
        and rebuilt_addendum["semantic_digest_sha256"]
        == saved_addendum["semantic_digest_sha256"]
    )
    return {
        "digest_resolver": {
            "ledger_target_strategy": "VIRTUAL_CRLF_FOR_LEGACY_LEDGER_TARGET",
            "non_target_strategy": "CURRENT_RAW_BYTES",
            "ledger_target_count": len(resolver.virtual_crlf_targets),
        },
        "phase1": {
            "verdict": phase1["verdict"],
            "certificate_count": len(phase1["certificate_checks"]),
            "certificate_role_counts": phase1["certificate_role_counts"],
            "aggregate_checks": phase1["aggregate_checks"],
            "passed": phase1_passed,
        },
        "phase2": {
            "verdict": phase2["verdict"],
            "certificate_count": len(phase2["branch_checks"]),
            "certificate_role_counts": phase2["certificate_role_counts"],
            "aggregate_checks": phase2["aggregate_checks"],
            "passed": phase2_passed,
        },
        "scope_addendum": {
            "verdict": rebuilt_addendum["verdict"],
            "semantic_digest_matches_frozen": (
                rebuilt_addendum["semantic_digest_sha256"]
                == saved_addendum["semantic_digest_sha256"]
            ),
            "passed": scope_passed,
        },
        "scientific_verdicts": {
            "phase1": phase1["verdict"],
            "phase2": phase2["verdict"],
            "global": phase1["global_scientific_verdict"],
        },
        "scientific_change": "NONE",
        "passed": bool(phase1_passed and phase2_passed and scope_passed),
    }


def verify_release_manifest(root: Path) -> dict[str, Any]:
    """Rebuild the v0.3.8 release manifest and compare it byte-for-byte."""

    path = root / RELEASE_MANIFEST_PATH
    if not path.is_file():
        return {
            "artifact": RELEASE_MANIFEST_PATH,
            "passed": False,
            "error": "release manifest is missing",
        }
    builder = _load_script_module(
        "build_v038_release_manifest_for_reproduction",
        root / "scripts/build_v038_release_manifest.py",
    )
    saved = _load_json(path)
    rebuilt = builder.build_manifest(root)
    regenerated_exactly = bool(
        rebuilt == saved and builder.render_manifest(rebuilt) == path.read_bytes()
    )
    return {
        "artifact": RELEASE_MANIFEST_PATH,
        "file_count": saved.get("file_count"),
        "semantic_digest_sha256": saved.get("semantic_digest_sha256"),
        "self_excluded": all(
            record.get("path") != RELEASE_MANIFEST_PATH
            for record in saved.get("files", [])
        ),
        "regenerated_exactly": regenerated_exactly,
        "passed": regenerated_exactly,
    }


def verify_v038(root: Path, *, check_release_manifest: bool = True) -> dict[str, Any]:
    """Verify migration integrity and unchanged v0.3.7 scientific verdicts."""

    root = root.resolve()
    bridge, resolver = verify_bridge(root)
    science = verify_scientific_artifacts(root, resolver)
    manifest = (
        verify_release_manifest(root)
        if check_release_manifest
        else {"passed": True, "check_skipped": True}
    )
    passed = bool(bridge["passed"] and science["passed"] and manifest["passed"])
    return {
        "schema_version": "final-theory-v0.3.8-reproduction-check",
        "version": "0.3.8",
        "migration_kind": "BYTE_SERIALIZATION_ONLY_CRLF_TO_CANONICAL_LF",
        "bridge": bridge,
        "science": science,
        "release_manifest": manifest,
        "global_scientific_verdict": science["scientific_verdicts"]["global"],
        "scientific_change": "NONE",
        "passed": passed,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--skip-release-manifest",
        action="store_true",
        help="verify bridge and science before the v0.3.8 manifest is generated",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = verify_v038(
        args.root,
        check_release_manifest=not args.skip_release_manifest,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
