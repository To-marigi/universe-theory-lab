from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
)
from universe_lab.final_theory import audit_v03 as audit_module
from universe_lab.final_theory.audit_v03 import (
    V02_ARTIFACT_FREEZE,
    baseline_audit,
    repository_inventory,
    source_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
LEGACY_DIGESTS = LegacyRawDigestResolver(
    ROOT,
    load_line_ending_bridge(ROOT / "results/v0.3.8_line_ending_bridge.json"),
)


@pytest.fixture(scope="module", autouse=True)
def _bridge_legacy_raw_hashes() -> Iterator[None]:
    original = audit_module.sha256_file
    audit_module.sha256_file = LEGACY_DIGESTS.sha256
    try:
        yield
    finally:
        audit_module.sha256_file = original


def test_v02_baseline_commit_tag_and_hashes_remain_frozen() -> None:
    result = baseline_audit(ROOT)
    assert result["passed"]
    assert result["tag_target"] == V02_ARTIFACT_FREEZE
    assert all(item["unchanged"] for item in result["frozen_artifacts"])


def test_literature_manifest_uses_versioned_local_archives() -> None:
    result = source_manifest(ROOT)
    assert result["all_local_hashes_present"]
    assert len(result["sources"]) == 3
    assert all("v" in source["version"] for source in result["sources"])
    qsg = next(
        source for source in result["sources"] if source["id"].startswith("arXiv:2603")
    )
    assert (
        qsg["current_metadata_check"]["classification"][
            "higher_dimensional_noncommutative_representation"
        ]
        == "OPEN_TARGET"
    )


def test_repository_inventory_keeps_absent_features_explicit() -> None:
    result = repository_inventory(ROOT)
    assert result["all_inspected_paths_exist"]
    classifications = {
        item["capability"]: item["classification"] for item in result["capabilities"]
    }
    assert classifications["channel-level Bell reduction"] == "ABSENT"
    assert classifications["large-N sampler"] == "ABSENT"
