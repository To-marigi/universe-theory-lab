"""v0.3.9 release verification: manifest, declared changes and inherited gates."""

from __future__ import annotations

import importlib.util
import json
import sys
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
        "V039_NEW_RELEASE_SUPPORT",
    }
    assert set(audit["classification_counts"]) <= allowed
    assert audit["classification_counts"] == {
        "UNCHANGED_RAW_BYTES": 188,
        "V039_INTENTIONAL_AUDIT_PORTABILITY_CHANGE": 2,
        "V039_INTENTIONAL_HISTORICAL_TEST_REBASE": 1,
        "V039_INTENTIONAL_RELEASE_METADATA_UPDATE": 2,
    }


def test_declared_change_sets_are_disjoint_and_complete(builder: ModuleType) -> None:
    groups = (
        builder.AUDIT_PORTABILITY_PATHS,
        builder.RELEASE_METADATA_PATHS,
        builder.HISTORICAL_TEST_REBASE_PATHS,
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


def test_full_v039_verification_passes() -> None:
    reproducer = _module("reproduce_v039", SCRIPTS / "reproduce_v039.py")
    summary = reproducer.verify_v039(REPOSITORY_ROOT)
    assert summary["release_manifest"]["passed"]
    assert summary["release_manifest"]["regenerated_exactly"]
    assert summary["inherited_v038_verification"]["passed"]
    assert summary["scientific_change"] == "NONE"
    assert summary["global_scientific_verdict"] == "FINAL_THEORY_OPEN"
    assert summary["passed"]
