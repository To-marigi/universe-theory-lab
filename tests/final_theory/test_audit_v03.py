from __future__ import annotations

from pathlib import Path

from universe_lab.final_theory.audit_v03 import (
    V02_ARTIFACT_FREEZE,
    baseline_audit,
    repository_inventory,
    source_manifest,
)

ROOT = Path(__file__).resolve().parents[2]


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
