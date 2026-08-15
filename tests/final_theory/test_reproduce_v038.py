from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
    raw_sha256,
    virtual_crlf_sha256,
)

ROOT = Path(__file__).resolve().parents[2]
REPRODUCER_PATH = ROOT / "scripts/reproduce_v038.py"
MANIFEST_PATH = ROOT / "results/v0.3.8_release_manifest.json"
BRIDGE_PATH = ROOT / "results/v0.3.8_line_ending_bridge.json"


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explicit_legacy_resolver_is_path_based() -> None:
    bridge = load_line_ending_bridge(BRIDGE_PATH)
    resolver = LegacyRawDigestResolver(ROOT, bridge)
    target_path = ROOT / bridge["targets"][0]["path"]
    non_target_path = REPRODUCER_PATH

    assert resolver.strategy(target_path) == (
        "VIRTUAL_CRLF_FOR_LEGACY_LEDGER_TARGET"
    )
    assert resolver.sha256(target_path) == virtual_crlf_sha256(target_path)
    assert resolver.strategy(non_target_path) == "CURRENT_RAW_BYTES"
    assert resolver.sha256(non_target_path) == raw_sha256(non_target_path)


def test_v038_reproducer_passes_all_frozen_scientific_gates() -> None:
    # Release-relative by nature: rebuilding the v0.3.8 manifest from the current
    # tree is only meaningful while that tree *is* v0.3.8. Since v0.3.9 declares
    # changes to audit_v031.py and ci.yml, that check moved to the v0.3.9 builder,
    # which classifies every v0.3.8 entry and rejects undeclared ones. What is
    # asserted here is what stays true for every later release: the bridge and the
    # frozen scientific gates.
    summary = _module("reproduce_v038_test", REPRODUCER_PATH).verify_v038(
        ROOT,
        check_release_manifest=False,
    )
    assert summary["passed"] is True
    assert summary["bridge"]["regenerated_exactly"] is True
    assert summary["science"]["digest_resolver"] == {
        "ledger_target_strategy": "VIRTUAL_CRLF_FOR_LEGACY_LEDGER_TARGET",
        "non_target_strategy": "CURRENT_RAW_BYTES",
        "ledger_target_count": 206,
    }
    assert summary["science"]["phase1"]["passed"] is True
    assert summary["science"]["phase1"]["certificate_count"] == 63
    assert all(summary["science"]["phase1"]["aggregate_checks"].values())
    assert summary["science"]["phase2"]["passed"] is True
    assert summary["science"]["phase2"]["certificate_count"] == 2
    assert all(summary["science"]["phase2"]["aggregate_checks"].values())
    assert summary["science"]["scope_addendum"]["passed"] is True
    assert summary["science"]["scientific_verdicts"] == {
        "phase1": "LITERAL_Q1_Q4_COMMUTATIVITY_PROVED",
        "phase2": "LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT",
        "global": "FINAL_THEORY_OPEN",
    }
    assert summary["scientific_change"] == "NONE"


def test_v038_manifest_is_canonical_complete_and_self_excluding() -> None:
    # Assertions about the recorded v0.3.8 artifact, which is immutable. The
    # rebuild-from-current-tree assertion that used to open this test is
    # release-relative and now lives in tests/final_theory/test_reproduce_v039.py.
    saved = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert saved["migration"]["historical_v0.3.7_manifest"][
        "classification_counts"
    ] == {
        "CANONICAL_LF_WITH_LEGACY_CRLF_BRIDGE": 81,
        "UNCHANGED_RAW_BYTES": 52,
        "V038_INTENTIONAL_SUPPORT_OR_WRITER_UPDATE": 26,
    }
    paths = {record["path"] for record in saved["files"]}
    assert "results/v0.3.8_release_manifest.json" not in paths
    assert {
        "results/v0.3.8_line_ending_bridge.json",
        "scripts/build_v038_release_manifest.py",
        "scripts/reproduce_v038.py",
        "src/universe_lab/artifact_migration_v038.py",
        "tests/final_theory/test_reproduce_v038.py",
        "reports/v0.3.8_line_ending_migration.md",
        "reports/v0.3.8_publication_readiness.md",
        "results/v0.3.8_publication_readiness.json",
        "REPRODUCING_v0.3.8.md",
    } <= paths
    assert all(
        record["serialization"] == "CANONICAL_LF_UTF8"
        for record in saved["files"]
        if record["serialization"] != "BINARY_RAW_BYTES"
    )
    assert saved["scientific_change"] == "NONE"


# The negative case that used to live here — simulating an unclassified change
# and asserting the historical audit refuses it — moved to
# tests/final_theory/test_reproduce_v039.py. On a post-v0.3.8 tree it had become
# a false positive: audit_v031.py already differs from its v0.3.8 record, so the
# v0.3.8 builder raises whether or not the simulated LICENSE change is injected,
# and the test would pass without exercising what it claims to. The v0.3.9
# version withdraws a declaration instead, so the rejection it observes is
# caused by the condition under test.
