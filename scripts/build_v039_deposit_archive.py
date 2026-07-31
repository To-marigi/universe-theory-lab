"""Build the deterministic v0.3.9 deposit archive.

The archive is the artifact offered for external deposit.  Until this script
existed it was produced by hand, which left packaging as the one step of the
release that could only be performed on the author's machine — the same shape
of defect that the CRLF hash bridge, the unpublished freeze refs, the shallow
checkout and the bare-branch resolution each cost a release to remove.  Given
the repository at a stated commit, a third party now regenerates the archive
and obtains the same SHA-256, byte for byte.

Contents
--------
Exactly the files named by ``results/v0.3.9_release_manifest.json``, plus that
manifest, which excludes itself from its own file list.  Nothing else.  The
third-party material under ``references/`` and ``oracle/sage_periods/vendor/``
is outside the manifest deliberately: ``references/sources.json`` records no
licence field for any of its entries, and this repository's MIT ``LICENSE``
does not extend to them.  See REPRODUCING_v0.3.9.md.

Determinism
-----------
Members are emitted in sorted path order and carry a fixed identity: mode
0644, uid/gid 0, empty uname/gname, and an ``mtime`` taken from the author date
of the packaged commit rather than from the filesystem.  The gzip wrapper
stores neither a filename nor a timestamp.  The output therefore depends on the
packaged commit and on nothing else about the machine that produced it.

Because ``mtime`` is the commit's author date, the archive digest is bound to a
commit.  A recorded digest is only meaningful when quoted together with the
commit it was built from.

The archive is never written inside the repository by default; ``--output`` is
required, so a 7 MiB deposit artifact cannot appear as an untracked file by
accident.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path
from typing import Any

MANIFEST_RELATIVE_PATH = "results/v0.3.9_release_manifest.json"
EXPECTED_VERSION = "0.3.9"
EXPECTED_SCHEMA_VERSION = "final-theory-release-manifest-v0.3.9"

# Fixed member identity.  Nothing here may be read from the filesystem.
MEMBER_MODE = 0o644
MEMBER_UID = 0
MEMBER_GID = 0
MEMBER_UNAME = ""
MEMBER_GNAME = ""

TAR_FORMAT = tarfile.PAX_FORMAT
GZIP_COMPRESSLEVEL = 9
GZIP_MTIME = 0

READ_BLOCK_BYTES = 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(READ_BLOCK_BYTES), b""):
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


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def packaged_commit(root: Path, revision: str) -> tuple[str, int]:
    """Resolve a revision to its commit id and author-date timestamp."""

    commit = _git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
    timestamp = int(_git(root, "log", "-1", "--format=%at", commit))
    return commit, timestamp


def load_manifest(root: Path) -> dict[str, Any]:
    """Load the release manifest and check it is the release this script packs."""

    path = root / MANIFEST_RELATIVE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"missing release manifest: {MANIFEST_RELATIVE_PATH}")
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    if manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise RuntimeError(
            "release manifest schema mismatch: "
            f"{manifest.get('schema_version')!r} != {EXPECTED_SCHEMA_VERSION!r}"
        )
    if manifest.get("version") != EXPECTED_VERSION:
        raise RuntimeError(
            f"release manifest version mismatch: "
            f"{manifest.get('version')!r} != {EXPECTED_VERSION!r}"
        )

    recorded_digest = manifest.get("semantic_digest_sha256")
    without_digest = {
        key: value
        for key, value in manifest.items()
        if key != "semantic_digest_sha256"
    }
    if _semantic_digest(without_digest) != recorded_digest:
        raise RuntimeError("release manifest semantic digest does not recompute")

    files = manifest["files"]
    if manifest.get("file_count") != len(files):
        raise RuntimeError("release manifest file_count disagrees with its file list")
    if manifest.get("self_excluded_artifact") != MANIFEST_RELATIVE_PATH:
        raise RuntimeError(
            "release manifest does not declare itself as the self-excluded artifact"
        )
    if any(record["path"] == MANIFEST_RELATIVE_PATH for record in files):
        raise RuntimeError("the release manifest must exclude itself from its own list")
    return manifest


def archive_members(manifest: dict[str, Any]) -> list[str]:
    """The packed paths: every manifest entry plus the self-excluded manifest."""

    paths = [record["path"] for record in manifest["files"]]
    paths.append(MANIFEST_RELATIVE_PATH)
    if len(set(paths)) != len(paths):
        raise RuntimeError("duplicate path in the release manifest")
    return sorted(paths)


def verify_tree(root: Path, manifest: dict[str, Any]) -> None:
    """Refuse to pack a tree that is not the release the manifest describes.

    Packaging reads the working tree, not the git object store, so a stale or
    dirty checkout would otherwise be archived under the release's name and the
    difference would only surface in whoever verified the deposit.
    """

    missing: list[str] = []
    mismatched: list[str] = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.is_file():
            missing.append(record["path"])
            continue
        if _sha256(path) != record["sha256"]:
            mismatched.append(record["path"])

    if missing:
        raise FileNotFoundError(f"release files are missing: {sorted(missing)}")
    if mismatched:
        raise RuntimeError(
            "working tree does not match the release manifest: "
            f"{sorted(mismatched)}"
        )


def _member(name: str, size: int, mtime: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.type = tarfile.REGTYPE
    info.size = size
    info.mtime = mtime
    info.mode = MEMBER_MODE
    info.uid = MEMBER_UID
    info.gid = MEMBER_GID
    info.uname = MEMBER_UNAME
    info.gname = MEMBER_GNAME
    return info


def build_archive(
    root: Path,
    destination: Path,
    revision: str = "HEAD",
) -> dict[str, Any]:
    root = root.resolve()
    destination = destination.resolve()

    manifest = load_manifest(root)
    verify_tree(root, manifest)
    members = archive_members(manifest)
    commit, mtime = packaged_commit(root, revision)
    prefix = f"final-theory-bench-v{manifest['version']}"

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw:
        # ``filename=""`` suppresses the gzip FNAME field, which would otherwise
        # be taken from the destination's name and bind the digest to it.
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=GZIP_COMPRESSLEVEL,
            fileobj=raw,
            mtime=GZIP_MTIME,
        ) as compressed:
            with tarfile.open(
                fileobj=compressed,
                mode="w",
                format=TAR_FORMAT,
            ) as archive:
                for relative_path in members:
                    source = root / relative_path
                    info = _member(
                        f"{prefix}/{relative_path}",
                        source.stat().st_size,
                        mtime,
                    )
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)

    return {
        "archive": str(destination),
        "archive_sha256": _sha256(destination),
        "archive_size_bytes": destination.stat().st_size,
        "packaged_commit": commit,
        "member_mtime": mtime,
        "member_prefix": prefix,
        "member_count": len(members),
        "manifest_file_count": manifest["file_count"],
        "manifest_semantic_digest_sha256": manifest["semantic_digest_sha256"],
        "excluded_scope": (
            "third-party material outside the release manifest: references/, "
            "oracle/sage_periods/vendor/ and the ignored files under results/"
        ),
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="where to write the archive; required, so it never lands in the repository",
    )
    parser.add_argument(
        "--commit",
        default="HEAD",
        help="revision whose author date fixes every member mtime (default: HEAD)",
    )
    parser.add_argument(
        "--expect-sha256",
        help="fail unless the archive hashes to this value",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    summary = build_archive(arguments.root, arguments.output, arguments.commit)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    expected = arguments.expect_sha256
    if expected is not None and summary["archive_sha256"] != expected:
        print(
            f"archive sha256 mismatch: {summary['archive_sha256']} != {expected}",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
