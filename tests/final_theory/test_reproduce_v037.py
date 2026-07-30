from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
V037_BUILDER = ROOT / "scripts/build_v037_release_manifest.py"
V038_REPRODUCER = ROOT / "scripts/reproduce_v038.py"


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_v037_recomputes_all_integrity_gates() -> None:
    reproducer = _module("reproduce_v038_for_v037_regression", V038_REPRODUCER)
    bridge, resolver = reproducer.verify_bridge(ROOT)
    summary = reproducer.verify_scientific_artifacts(ROOT, resolver)
    assert bridge["passed"] is True
    assert summary["passed"] is True
    assert summary["phase1"]["verdict"] == ("LITERAL_Q1_Q4_COMMUTATIVITY_PROVED")
    assert summary["phase1"]["certificate_count"] == 63
    assert summary["phase1"]["certificate_role_counts"] == {
        "PHASE1_GF32003_SCOUT": 21,
        "PHASE1_GF32009_SCOUT": 21,
        "PHASE1_QQ_EXACT_PROOF": 21,
    }
    assert all(summary["phase1"]["aggregate_checks"].values())
    assert summary["phase2"]["verdict"] == ("LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT")
    assert summary["phase2"]["certificate_count"] == 2
    assert summary["scope_addendum"]["verdict"] == ("V037_SCOPE_ADDENDUM_CERTIFIED")
    assert summary["scientific_verdicts"]["global"] == "FINAL_THEORY_OPEN"
    assert summary["scientific_change"] == "NONE"


def test_release_manifest_is_preserved_and_audited_historically() -> None:
    saved = json.loads(
        (ROOT / "results/v0.3.7_release_manifest.json").read_text(encoding="utf-8")
    )
    v038 = json.loads(
        (ROOT / "results/v0.3.8_release_manifest.json").read_text(encoding="utf-8")
    )
    audit = v038["migration"]["historical_v0.3.7_manifest"]
    assert audit["passed"] is True
    assert audit["historical_semantic_digest_sha256"] == (
        saved["semantic_digest_sha256"]
    )
    assert audit["historical_file_count"] == saved["file_count"] == 159
    assert sum(audit["classification_counts"].values()) == saved["file_count"]
    assert set(audit["classification_counts"]) == {
        "CANONICAL_LF_WITH_LEGACY_CRLF_BRIDGE",
        "UNCHANGED_RAW_BYTES",
        "V038_INTENTIONAL_SUPPORT_OR_WRITER_UPDATE",
    }
    assert all(
        record["classification"] in audit["classification_counts"]
        for record in audit["records"]
    )
    assert not audit["unexpected_changes"]
    assert {role: record["count"] for role, record in saved["certificate_inventory"].items()} == {
        "NEGATIVE_TIMEOUT_RECORD_NOT_PROOF": 1,
        "PHASE1_GF32003_SCOUT": 21,
        "PHASE1_GF32009_SCOUT": 21,
        "PHASE1_QQ_EXACT_PROOF": 21,
        "PHASE2_QQ_DIRECT_IDENTITY_EXACT": 2,
    }
    assert saved["scientific_verdicts"] == {
        "phase1": "LITERAL_Q1_Q4_COMMUTATIVITY_PROVED",
        "phase2": "LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT",
        "global": "FINAL_THEORY_OPEN",
    }
    assert saved["budget"]["provenance"].endswith("NO_RUNTIME_DEFAULTS_OR_SELF_AUTHENTICATION")


def test_release_manifest_rejects_partial_or_wrong_role_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = _module(
        "build_v037_release_manifest_mutation_test",
        V037_BUILDER,
    )
    monkeypatch.setattr(
        builder,
        "verify_q5_free_campaign_v037",
        lambda _root: {
            "passed": False,
            "verdict": "LITERAL_Q5_FREE_ELIMINATION_PARTIAL",
        },
    )
    monkeypatch.setattr(
        builder,
        "verify_general_scalar_chain_lemma_v037",
        lambda _root: {
            "passed": True,
            "verdict": "LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT",
        },
    )
    with pytest.raises(RuntimeError, match="Phase 1"):
        builder._certificate_inventory(ROOT)

    monkeypatch.setattr(
        builder,
        "verify_q5_free_campaign_v037",
        lambda _root: {
            "passed": True,
            "verdict": "LITERAL_Q1_Q4_COMMUTATIVITY_PROVED",
        },
    )
    original_load = builder._load_json
    phase1 = copy.deepcopy(original_load(ROOT / "results/v0.3.7_q5_free_elimination.json"))
    phase1["runs"].append(copy.deepcopy(phase1["runs"][0]))

    def mutated_load(path: Path):
        if path.name == "v0.3.7_q5_free_elimination.json":
            return phase1
        return original_load(path)

    monkeypatch.setattr(builder, "_load_json", mutated_load)
    with pytest.raises(RuntimeError, match="certificate roles"):
        builder._certificate_inventory(ROOT)
