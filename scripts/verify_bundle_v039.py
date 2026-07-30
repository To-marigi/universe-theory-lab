"""Offline integrity check for the v0.3.9 deposit bundle.

What this verifies
------------------
That every file named by ``results/v0.3.9_release_manifest.json`` is present in
the bundle and matches its recorded SHA-256, that the manifest's own semantic
digest is intact, and that no extra file has been added.  In other words: the
archive you hold is byte-identical to the archive that was deposited.

What this does not verify
-------------------------
Anything requiring git.  ``scripts/reproduce_v039.py`` regenerates the
line-ending bridge from ``git ls-files``, and the frozen baseline audits resolve
commits, annotated tags and a branch.  None of that is possible from a file
archive, no matter how many files it contains — this was measured, not assumed:
staging the manifest, every bridge target and every bridge consumer, 335 files
and 121.5 MiB, still fails at bridge regeneration because the tracked-file set
itself comes from git.

Full reproduction therefore requires the repository, not this bundle.  See
REPRODUCING_v0.3.9.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_RELATIVE_PATH = "results/v0.3.9_release_manifest.json"


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


def verify_bundle(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise FileNotFoundError(f"bundle is missing {MANIFEST_RELATIVE_PATH}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    recorded_digest = manifest.get("semantic_digest_sha256")
    without_digest = {
        key: value
        for key, value in manifest.items()
        if key != "semantic_digest_sha256"
    }
    digest_intact = _semantic_digest(without_digest) == recorded_digest

    missing: list[str] = []
    mismatched: list[dict[str, str]] = []
    expected = {record["path"]: record for record in manifest["files"]}
    for relative_path, record in sorted(expected.items()):
        path = root / relative_path
        if not path.is_file():
            missing.append(relative_path)
            continue
        actual = _sha256(path)
        if actual != record["sha256"]:
            mismatched.append(
                {
                    "path": relative_path,
                    "recorded_sha256": record["sha256"],
                    "actual_sha256": actual,
                }
            )

    permitted = set(expected) | {MANIFEST_RELATIVE_PATH}
    present = {
        item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file()
    }
    unexpected = sorted(present - permitted)

    passed = (
        digest_intact and not missing and not mismatched and not unexpected
    )
    return {
        "bundle_root": str(root),
        "manifest": MANIFEST_RELATIVE_PATH,
        "manifest_semantic_digest_sha256": recorded_digest,
        "manifest_semantic_digest_intact": digest_intact,
        "expected_file_count": len(expected) + 1,
        "verified_file_count": len(expected) - len(missing) - len(mismatched),
        "missing_files": missing,
        "mismatched_files": mismatched,
        "unexpected_files": unexpected,
        "verification_scope": (
            "byte integrity of the deposited files only; git-dependent bridge "
            "regeneration and frozen-baseline audits require the repository"
        ),
        "passed": passed,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="directory the bundle was extracted into",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    summary = verify_bundle(arguments.root)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
