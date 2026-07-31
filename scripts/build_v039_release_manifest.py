"""Build the v0.3.9 release manifest for the audit ref-portability change.

v0.3.9 carries one behavioural change: ``audit_v031.resolve_frozen_branch``
accepts the remote-tracking ref that every clone has, so the frozen v0.3 branch
no longer has to be materialised as a local head by hand or by CI.

The v0.3.8 release manifest is the baseline.  Every entry in it must be either
byte-identical or a member of one explicitly declared change set.  Anything else
fails the build, which is the same discipline the v0.3.8 builder applied against
v0.3.7.  Nothing in the v0.3.8 release is edited, and no scientific artifact,
certificate or verdict is touched.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent

RESULT_PATH = "results/v0.3.9_release_manifest.json"
BASELINE_PATH = "results/v0.3.8_release_manifest.json"

# The v0.3.8 baseline is pinned, not merely loaded.  If any of these three
# values moves, the baseline is not the release this manifest claims to extend.
BASELINE_SCHEMA_VERSION = "final-theory-release-manifest-v0.3.8"
BASELINE_FILE_COUNT = 193
BASELINE_SEMANTIC_DIGEST = (
    "e4b50d41263e296860fd8a0e39aa3490510b40b48e99c8848fa035b8da7eed01"
)

AUDIT_PORTABILITY_PATHS = (
    ".github/workflows/ci.yml",
    "src/universe_lab/final_theory/audit_v031.py",
)

RELEASE_METADATA_PATHS = (
    ".zenodo.json",
    "CITATION.cff",
)

HISTORICAL_TEST_REBASE_PATHS = (
    "tests/final_theory/test_reproduce_v038.py",
)

NEW_RELEASE_SUPPORT_PATHS = (
    "REPRODUCING_v0.3.9.md",
    "reports/v0.3.9_audit_ref_portability.md",
    "reports/v0.3.9_publication_readiness.md",
    "results/v0.3.9_publication_readiness.json",
    "scripts/build_v039_deposit_archive.py",
    "scripts/build_v039_release_manifest.py",
    "scripts/reproduce_v039.py",
    "scripts/verify_bundle_v039.py",
    "tests/final_theory/test_audit_ref_portability_v039.py",
    "tests/final_theory/test_reproduce_v039.py",
    # The v0.3.8 manifest is carried as the historical baseline of this release.
    BASELINE_PATH,
)

CLASSIFICATION_AUDIT = "V039_INTENTIONAL_AUDIT_PORTABILITY_CHANGE"
CLASSIFICATION_METADATA = "V039_INTENTIONAL_RELEASE_METADATA_UPDATE"
CLASSIFICATION_TEST_REBASE = "V039_INTENTIONAL_HISTORICAL_TEST_REBASE"
CLASSIFICATION_SUPPORT = "V039_NEW_RELEASE_SUPPORT"
CLASSIFICATION_UNCHANGED = "UNCHANGED_RAW_BYTES"

DECLARED_CHANGES = {
    **{path: CLASSIFICATION_AUDIT for path in AUDIT_PORTABILITY_PATHS},
    **{path: CLASSIFICATION_METADATA for path in RELEASE_METADATA_PATHS},
    **{path: CLASSIFICATION_TEST_REBASE for path in HISTORICAL_TEST_REBASE_PATHS},
    **{path: CLASSIFICATION_SUPPORT for path in NEW_RELEASE_SUPPORT_PATHS},
}


@lru_cache(maxsize=1)
def _v038_builder() -> ModuleType:
    """Reuse the v0.3.8 serialization classifier instead of restating it.

    ``_serialization`` does not merely label a file: it rejects a text entry
    that is not valid UTF-8 or not canonical LF, and it recognises the binary
    suffixes that must never be decoded. Duplicating either would let the two
    releases disagree.
    """

    path = SCRIPTS_DIRECTORY / "build_v038_release_manifest.py"
    specification = importlib.util.spec_from_file_location(
        "build_v038_release_manifest_for_v039",
        path,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def serialization_of(root: Path, relative_path: str) -> str:
    return str(_v038_builder()._serialization(root / relative_path, relative_path))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _semantic_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_pinned_baseline(root: Path) -> dict[str, Any]:
    baseline = _load_json(root / BASELINE_PATH)
    if baseline.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise RuntimeError(
            "v0.3.8 baseline schema mismatch: "
            f"{baseline.get('schema_version')!r} != {BASELINE_SCHEMA_VERSION!r}"
        )
    if baseline.get("file_count") != BASELINE_FILE_COUNT:
        raise RuntimeError(
            "v0.3.8 baseline file count mismatch: "
            f"{baseline.get('file_count')!r} != {BASELINE_FILE_COUNT!r}"
        )
    if baseline.get("semantic_digest_sha256") != BASELINE_SEMANTIC_DIGEST:
        raise RuntimeError(
            "v0.3.8 baseline semantic digest mismatch: "
            f"{baseline.get('semantic_digest_sha256')!r} != {BASELINE_SEMANTIC_DIGEST!r}"
        )
    if len(baseline.get("files", [])) != BASELINE_FILE_COUNT:
        raise RuntimeError("v0.3.8 baseline file list does not match its own count")
    return baseline


def _baseline_audit(root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    unexpected: list[str] = []

    for record in baseline["files"]:
        relative_path = record["path"]
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"v0.3.8 release file is missing: {relative_path}")
        current_digest = _sha256(path)
        recorded_digest = record["sha256"]
        if current_digest == recorded_digest:
            classification = CLASSIFICATION_UNCHANGED
        elif relative_path in DECLARED_CHANGES:
            classification = DECLARED_CHANGES[relative_path]
        else:
            classification = "UNEXPECTED_CHANGE"
            unexpected.append(relative_path)
        counts[classification] += 1
        records.append(
            {
                "path": relative_path,
                "v0.3.8_recorded_sha256": recorded_digest,
                "v0.3.9_current_sha256": current_digest,
                "classification": classification,
            }
        )

    if unexpected:
        raise RuntimeError(
            f"undeclared changes relative to the v0.3.8 manifest: {sorted(unexpected)}"
        )

    return {
        "baseline_artifact": BASELINE_PATH,
        "baseline_schema_version": BASELINE_SCHEMA_VERSION,
        "baseline_file_count": BASELINE_FILE_COUNT,
        "baseline_semantic_digest_sha256": BASELINE_SEMANTIC_DIGEST,
        "baseline_pins_verified": True,
        "entries": records,
        "classification_counts": dict(sorted(counts.items())),
        "undeclared_changes": [],
    }


def build_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    baseline = _load_pinned_baseline(root)
    audit = _baseline_audit(root, baseline)

    baseline_paths = [record["path"] for record in baseline["files"]]
    role_by_path = {record["path"]: record["role"] for record in baseline["files"]}
    paths = sorted(set(baseline_paths) | set(NEW_RELEASE_SUPPORT_PATHS))
    if RESULT_PATH in paths:
        raise RuntimeError("the v0.3.9 manifest must exclude itself")

    missing = [path for path in paths if not (root / path).is_file()]
    if missing:
        raise FileNotFoundError(f"v0.3.9 release files are missing: {missing}")

    files = [
        {
            "path": path,
            "sha256": _sha256(root / path),
            "size_bytes": (root / path).stat().st_size,
            "serialization": serialization_of(root, path),
            "role": DECLARED_CHANGES.get(
                path,
                role_by_path.get(path, CLASSIFICATION_SUPPORT),
            ),
        }
        for path in paths
    ]

    payload: dict[str, Any] = {
        "schema_version": "final-theory-release-manifest-v0.3.9",
        "version": "0.3.9",
        "status": "LOCAL_RELEASE_CANDIDATE_NOT_EXTERNALLY_DEPOSITED",
        "publication_readiness": "BLOCKED_PENDING_EXTERNAL_CI_AND_HUMAN_MATURITY_REVIEW",
        "change": {
            "kind": "AUDIT_REF_RESOLUTION_PORTABILITY",
            "summary": (
                "audit_v031.resolve_frozen_branch accepts the remote-tracking ref "
                "that a clone provides, so the frozen v0.3 branch no longer needs a "
                "hand-created or CI-created local head."
            ),
            "resolver_boundary": (
                "The fallback is refs/remotes/origin/<branch>. A full clone with the "
                "conventional remote name 'origin' is in scope; other remote names "
                "are not generalised over."
            ),
            "removed_workaround": (
                "The v0.3.8 CI step that created the local head is deleted, and the "
                "matching prerequisite section is absent from REPRODUCING_v0.3.9.md."
            ),
            "regression_test": (
                "tests/final_theory/test_audit_ref_portability_v039.py"
            ),
            "v0.3.8_artifacts_modified": (
                "The recorded v0.3.8 manifest, its certificates and every "
                "scientific artifact are unmodified. Only the current test "
                "harness is rescoped: test_reproduce_v038.py no longer rebuilds "
                "the v0.3.8 manifest from a tree that is no longer v0.3.8, and "
                "its undeclared-change negative case moved to the v0.3.9 builder "
                "where the rejection is genuinely exercised."
            ),
        },
        "scientific_verdicts": baseline["scientific_verdicts"],
        "scientific_change": "NONE",
        "claim_boundary": (
            "v0.3.9 changes how one git ref is resolved during the v0.3 baseline "
            "audit. It reruns no solver, alters no certificate, and moves no verdict."
        ),
        "historical_v0.3.8_manifest_audit": audit,
        "file_count": len(files),
        "total_size_bytes": sum(int(record["size_bytes"]) for record in files),
        "files": files,
        "self_excluded_artifact": RESULT_PATH,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the stored manifest regenerates exactly, without writing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    root = arguments.root.resolve()
    manifest = build_manifest(root)
    destination = root / RESULT_PATH

    if arguments.check:
        if not destination.is_file():
            raise SystemExit(f"missing manifest: {RESULT_PATH}")
        stored = _load_json(destination)
        if stored != manifest:
            raise SystemExit(f"{RESULT_PATH} does not regenerate exactly")
        print(f"{destination}: regenerates exactly, {manifest['file_count']} files")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{destination}: {manifest['file_count']} files, "
        f"{manifest['semantic_digest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
