"""Reproduce and verify the v0.3.9 audit ref-portability release.

v0.3.9 reuses the v0.3.8 verification seam rather than reimplementing it.
``reproduce_v038.verify_v038`` already exposes ``check_release_manifest``, so the
line-ending bridge, the Phase 1 and Phase 2 certificates and the scope addendum
are checked by the code that has been verifying them since v0.3.8.  Only the
release manifest check is version-specific and is performed here against the
v0.3.9 manifest.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent
RELEASE_MANIFEST_PATH = "results/v0.3.9_release_manifest.json"


def _load_script_module(name: str, path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def verify_release_manifest(root: Path) -> dict[str, Any]:
    builder = _load_script_module(
        "build_v039_release_manifest",
        SCRIPTS_DIRECTORY / "build_v039_release_manifest.py",
    )
    stored_path = root / RELEASE_MANIFEST_PATH
    if not stored_path.is_file():
        raise FileNotFoundError(f"missing manifest: {RELEASE_MANIFEST_PATH}")
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    rebuilt = builder.build_manifest(root)
    audit = rebuilt["historical_v0.3.8_manifest_audit"]
    return {
        "artifact": RELEASE_MANIFEST_PATH,
        "file_count": rebuilt["file_count"],
        "semantic_digest_sha256": rebuilt["semantic_digest_sha256"],
        "self_excluded": RELEASE_MANIFEST_PATH
        not in {record["path"] for record in rebuilt["files"]},
        "baseline_pins_verified": audit["baseline_pins_verified"],
        "baseline_classification_counts": audit["classification_counts"],
        "undeclared_changes": audit["undeclared_changes"],
        "regenerated_exactly": stored == rebuilt,
        "passed": stored == rebuilt
        and not audit["undeclared_changes"]
        and audit["baseline_pins_verified"],
    }


def verify_v039(root: Path) -> dict[str, Any]:
    root = root.resolve()
    reproducer = _load_script_module(
        "reproduce_v038",
        SCRIPTS_DIRECTORY / "reproduce_v038.py",
    )
    inherited = reproducer.verify_v038(root, check_release_manifest=False)
    manifest = verify_release_manifest(root)
    passed = bool(inherited["passed"]) and manifest["passed"]
    return {
        "version": "0.3.9",
        "inherited_v038_verification": inherited,
        "release_manifest": manifest,
        "scientific_change": "NONE",
        "global_scientific_verdict": inherited["global_scientific_verdict"],
        "passed": passed,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    summary = verify_v039(arguments.root)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
