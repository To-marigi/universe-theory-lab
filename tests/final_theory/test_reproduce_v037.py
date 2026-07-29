from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/reproduce_v037.py"


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_v037_recomputes_all_integrity_gates() -> None:
    summary = _module("reproduce_v037", SCRIPT).verify_v037(ROOT)
    assert summary["passed"] is True
    assert summary["phase1"]["verdict"] == ("LITERAL_Q1_Q4_COMMUTATIVITY_PROVED")
    assert summary["phase1"]["certificate_count"] == 63
    assert summary["phase1"]["certificate_role_counts"] == {
        "PHASE1_GF32003_SCOUT": 21,
        "PHASE1_GF32009_SCOUT": 21,
        "PHASE1_QQ_EXACT_PROOF": 21,
    }
    assert not summary["phase1"]["failed_certificate_checks"]
    assert summary["phase2"]["verdict"] == ("LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT")
    assert summary["phase2"]["certificate_count"] == 2
    assert summary["scope_addendum"]["verdict"] == ("V037_SCOPE_ADDENDUM_CERTIFIED")
    assert summary["release_manifest"]["passed"] is True
    assert summary["global_scientific_verdict"] == "FINAL_THEORY_OPEN"


def test_release_manifest_recomputes_exactly() -> None:
    builder = _module(
        "build_v037_release_manifest",
        ROOT / "scripts/build_v037_release_manifest.py",
    )
    saved = json.loads((ROOT / builder.RESULT_PATH).read_text(encoding="utf-8"))
    assert builder.build_manifest(ROOT) == saved
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
        ROOT / "scripts/build_v037_release_manifest.py",
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
