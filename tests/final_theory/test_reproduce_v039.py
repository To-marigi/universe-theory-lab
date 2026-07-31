"""v0.3.9 release verification: manifest, declared changes and inherited gates."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY_ROOT / "scripts"
MANIFEST_PATH = REPOSITORY_ROOT / "results/v0.3.9_release_manifest.json"


def _module(name: str, path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder() -> ModuleType:
    return _module(
        "build_v039_release_manifest",
        SCRIPTS / "build_v039_release_manifest.py",
    )


@pytest.fixture(scope="module")
def manifest(builder: ModuleType) -> dict[str, Any]:
    return builder.build_manifest(REPOSITORY_ROOT)


def test_manifest_regenerates_exactly(manifest: dict[str, Any]) -> None:
    stored = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert stored == manifest


def test_manifest_excludes_itself(
    builder: ModuleType, manifest: dict[str, Any]
) -> None:
    paths = {record["path"] for record in manifest["files"]}
    assert builder.RESULT_PATH not in paths
    assert manifest["self_excluded_artifact"] == builder.RESULT_PATH


def test_v038_baseline_pins_are_verified(
    builder: ModuleType, manifest: dict[str, Any]
) -> None:
    audit = manifest["historical_v0.3.8_manifest_audit"]
    assert audit["baseline_schema_version"] == builder.BASELINE_SCHEMA_VERSION
    assert audit["baseline_file_count"] == builder.BASELINE_FILE_COUNT == 193
    assert audit["baseline_semantic_digest_sha256"] == builder.BASELINE_SEMANTIC_DIGEST
    assert audit["baseline_pins_verified"] is True


def test_every_baseline_entry_is_declared(manifest: dict[str, Any]) -> None:
    audit = manifest["historical_v0.3.8_manifest_audit"]
    assert audit["undeclared_changes"] == []
    assert len(audit["entries"]) == 193
    allowed = {
        "UNCHANGED_RAW_BYTES",
        "V039_INTENTIONAL_AUDIT_PORTABILITY_CHANGE",
        "V039_INTENTIONAL_RELEASE_METADATA_UPDATE",
        "V039_INTENTIONAL_HISTORICAL_TEST_REBASE",
        "V039_INTENTIONAL_AUTHOR_IDENTITY",
        "V039_NEW_RELEASE_SUPPORT",
    }
    assert set(audit["classification_counts"]) <= allowed
    assert audit["classification_counts"] == {
        "UNCHANGED_RAW_BYTES": 186,
        "V039_INTENTIONAL_AUDIT_PORTABILITY_CHANGE": 2,
        "V039_INTENTIONAL_AUTHOR_IDENTITY": 2,
        "V039_INTENTIONAL_HISTORICAL_TEST_REBASE": 1,
        "V039_INTENTIONAL_RELEASE_METADATA_UPDATE": 2,
    }


def test_declared_change_sets_are_disjoint_and_complete(builder: ModuleType) -> None:
    groups = (
        builder.AUDIT_PORTABILITY_PATHS,
        builder.RELEASE_METADATA_PATHS,
        builder.HISTORICAL_TEST_REBASE_PATHS,
        builder.AUTHOR_IDENTITY_PATHS,
        builder.NEW_RELEASE_SUPPORT_PATHS,
    )
    seen: set[str] = set()
    for group in groups:
        assert not seen & set(group), "declared change sets must be disjoint"
        seen |= set(group)
    assert set(builder.DECLARED_CHANGES) == seen


def test_baseline_manifest_is_carried_as_historical_support(
    builder: ModuleType, manifest: dict[str, Any]
) -> None:
    paths = {record["path"] for record in manifest["files"]}
    assert builder.BASELINE_PATH in paths
    assert builder.BASELINE_PATH in builder.NEW_RELEASE_SUPPORT_PATHS


def test_scientific_verdicts_are_inherited_unchanged(
    manifest: dict[str, Any],
) -> None:
    baseline = json.loads(
        (REPOSITORY_ROOT / "results/v0.3.8_release_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["scientific_verdicts"] == baseline["scientific_verdicts"]
    assert manifest["scientific_change"] == "NONE"
    modified = manifest["change"]["v0.3.8_artifacts_modified"]
    assert "unmodified" in modified
    assert "test harness is rescoped" in modified


def test_binary_entries_are_not_labelled_as_canonical_text(
    manifest: dict[str, Any],
) -> None:
    """Binary payloads must inherit v0.3.8's BINARY_RAW_BYTES label.

    The first v0.3.9 builder hardcoded ``CANONICAL_LF_UTF8`` for every entry,
    which claimed a gzip archive and a PDF were canonical LF text. Serialization
    is now delegated to the v0.3.8 classifier, which also rejects a text entry
    that is not valid UTF-8 or not canonical LF.
    """

    by_path = {record["path"]: record["serialization"] for record in manifest["files"]}
    expected_binary = {
        "certificates/d2_saturation/v0.3.5_compact_expression_arena.json.gz",
        "output/pdf/v0.3.7_d2_commutativity_short_report.pdf",
    }
    actual_binary = {
        path for path, kind in by_path.items() if kind == "BINARY_RAW_BYTES"
    }
    assert actual_binary == expected_binary
    assert set(by_path.values()) == {"CANONICAL_LF_UTF8", "BINARY_RAW_BYTES"}

    baseline = json.loads(
        (REPOSITORY_ROOT / "results/v0.3.8_release_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    baseline_binary = {
        record["path"]
        for record in baseline["files"]
        if record["serialization"] == "BINARY_RAW_BYTES"
    }
    assert actual_binary == baseline_binary


def test_builder_rejects_an_undeclared_change(
    builder: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Withdraw one declaration and confirm the real difference is refused.

    This is the negative case moved from ``test_reproduce_v038.py``. There it had
    become a false positive: on any post-v0.3.8 tree ``audit_v031.py`` already
    differs from its v0.3.8 record, so the v0.3.8 builder raised regardless of the
    simulated change the test injected. Here the file difference is genuine and
    only its declaration is removed, so the rejection is caused by exactly the
    condition under test.
    """

    withdrawn = "src/universe_lab/final_theory/audit_v031.py"
    assert withdrawn in builder.DECLARED_CHANGES
    remaining = {
        path: classification
        for path, classification in builder.DECLARED_CHANGES.items()
        if path != withdrawn
    }
    monkeypatch.setattr(builder, "DECLARED_CHANGES", remaining)

    with pytest.raises(RuntimeError, match="undeclared changes") as failure:
        builder.build_manifest(REPOSITORY_ROOT)
    assert withdrawn in str(failure.value)


def test_builder_rejects_a_moved_v038_baseline(
    builder: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pinned v0.3.8 baseline is checked, not merely loaded."""

    monkeypatch.setattr(builder, "BASELINE_FILE_COUNT", 192)
    with pytest.raises(RuntimeError, match="baseline file count mismatch"):
        builder.build_manifest(REPOSITORY_ROOT)


def test_bundle_verifier_accepts_a_faithful_bundle_and_rejects_tampering(
    manifest: dict[str, Any], tmp_path: Path
) -> None:
    """The offline bundle check is the only verification a deposit can carry."""

    import shutil

    verifier = _module("verify_bundle_v039", SCRIPTS / "verify_bundle_v039.py")
    bundle = tmp_path / "bundle"
    staged = [record["path"] for record in manifest["files"]]
    staged.append(verifier.MANIFEST_RELATIVE_PATH)
    for relative_path in staged:
        destination = bundle / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / relative_path, destination)

    summary = verifier.verify_bundle(bundle)
    assert summary["passed"]
    assert summary["manifest_semantic_digest_intact"]
    assert summary["missing_files"] == []
    assert summary["mismatched_files"] == []
    assert summary["unexpected_files"] == []
    assert summary["expected_file_count"] == len(manifest["files"]) + 1

    tampered = bundle / "REPRODUCING_v0.3.9.md"
    tampered.write_text(
        tampered.read_text(encoding="utf-8") + "\ntampered\n",
        encoding="utf-8",
        newline="\n",
    )
    (bundle / "unexpected_extra.txt").write_text("x\n", encoding="utf-8", newline="\n")
    after = verifier.verify_bundle(bundle)
    assert not after["passed"]
    assert [item["path"] for item in after["mismatched_files"]] == [
        "REPRODUCING_v0.3.9.md"
    ]
    assert after["unexpected_files"] == ["unexpected_extra.txt"]


@pytest.fixture(scope="module")
def packer() -> ModuleType:
    return _module(
        "build_v039_deposit_archive",
        SCRIPTS / "build_v039_deposit_archive.py",
    )


def _synthetic_release(packer: ModuleType, root: Path, timestamp: int) -> None:
    """A two-file stand-in for the release, so the byte contract is tested in ms.

    Packing the real 47.9 MiB bundle twice would dominate the suite, and the
    property under test is the member identity, not the payload.  The manifest's
    own digest is built with the packer's helper on purpose: restating the
    serialization here would let the fixture and the code under test disagree
    about something this test is not trying to check.
    """

    (root / "nested").mkdir(parents=True)
    (root / "alpha.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
    (root / "nested" / "beta.txt").write_text("beta\n", encoding="utf-8", newline="\n")

    files = []
    for relative_path in ("alpha.txt", "nested/beta.txt"):
        payload = (root / relative_path).read_bytes()
        files.append(
            {
                "path": relative_path,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "serialization": "CANONICAL_LF_UTF8",
                "role": "V039_NEW_RELEASE_SUPPORT",
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": packer.EXPECTED_SCHEMA_VERSION,
        "version": packer.EXPECTED_VERSION,
        "file_count": len(files),
        "files": files,
        "self_excluded_artifact": packer.MANIFEST_RELATIVE_PATH,
    }
    manifest["semantic_digest_sha256"] = packer._semantic_digest(manifest)

    destination = root / packer.MANIFEST_RELATIVE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    # An empty commit is enough: the builder packs the working tree and reads
    # only the author date from git.
    environment = {
        **os.environ,
        "GIT_AUTHOR_DATE": f"@{timestamp} +0000",
        "GIT_COMMITTER_DATE": f"@{timestamp} +0000",
    }
    for arguments in (
        ("init", "-q"),
        (
            "-c",
            "user.email=synthetic@example.invalid",
            "-c",
            "user.name=synthetic",
            "commit",
            "--allow-empty",
            "-q",
            "-m",
            "synthetic release",
        ),
    ):
        subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            env=environment,
        )


def test_deposit_archive_is_deterministic_and_bound_to_the_commit(
    packer: ModuleType, tmp_path: Path
) -> None:
    """Packaging must not depend on the machine that ran it.

    Every field a tar reader can see is fixed by the release, not by the
    filesystem: the digest moves only when the packaged commit or its contents
    move.  This is what lets a recorded SHA-256 mean anything to a third party.
    """

    root = tmp_path / "release"
    root.mkdir()
    timestamp = 1_700_000_000
    _synthetic_release(packer, root, timestamp)

    first = packer.build_archive(root, tmp_path / "first.tar.gz")
    second = packer.build_archive(root, tmp_path / "second.tar.gz")
    assert first["archive_sha256"] == second["archive_sha256"]
    assert (tmp_path / "first.tar.gz").read_bytes() == (
        tmp_path / "second.tar.gz"
    ).read_bytes()

    assert first["member_mtime"] == timestamp
    assert first["member_count"] == 3
    assert first["manifest_file_count"] == 2

    with tarfile.open(tmp_path / "first.tar.gz") as archive:
        members = archive.getmembers()
    assert [member.name for member in members] == [
        "final-theory-bench-v0.3.9/alpha.txt",
        "final-theory-bench-v0.3.9/nested/beta.txt",
        "final-theory-bench-v0.3.9/results/v0.3.9_release_manifest.json",
    ]
    for member in members:
        assert member.isfile()
        assert member.mode == 0o644
        assert (member.uid, member.gid) == (0, 0)
        assert (member.uname, member.gname) == ("", "")
        assert member.mtime == timestamp

    header = (tmp_path / "first.tar.gz").read_bytes()[:10]
    assert header[3] == 0, "gzip FLG must not announce a stored filename"
    assert header[4:8] == b"\x00\x00\x00\x00", "gzip MTIME must be zero"


def test_deposit_builder_refuses_a_tree_that_is_not_the_release(
    packer: ModuleType, tmp_path: Path
) -> None:
    """A stale or dirty checkout must not be archived under the release's name."""

    root = tmp_path / "release"
    root.mkdir()
    _synthetic_release(packer, root, 1_700_000_000)
    (root / "alpha.txt").write_text("tampered\n", encoding="utf-8", newline="\n")

    with pytest.raises(RuntimeError, match="does not match the release manifest"):
        packer.build_archive(root, tmp_path / "rejected.tar.gz")


def test_full_v039_verification_passes() -> None:
    reproducer = _module("reproduce_v039", SCRIPTS / "reproduce_v039.py")
    summary = reproducer.verify_v039(REPOSITORY_ROOT)
    assert summary["release_manifest"]["passed"]
    assert summary["release_manifest"]["regenerated_exactly"]
    assert summary["inherited_v038_verification"]["passed"]
    assert summary["scientific_change"] == "NONE"
    assert summary["global_scientific_verdict"] == "FINAL_THEORY_OPEN"
    assert summary["passed"]
