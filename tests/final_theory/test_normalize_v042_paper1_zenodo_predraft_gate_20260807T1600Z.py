from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z.py"
LEDGER_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_normalized.json"
)
FULL_OVERLAP_RAW_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_full_overlap_atom.xml"
)
EXACT_ID_RAW_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_exact_ids_atom.xml"
)
RECEIPT_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_retrieval.json"
)
LEDGER_SHA256 = "3b3d664c6841fef3e400be3246b8ed99063e104cc5195d29b2b1b5248b7a7e88"
FULL_OVERLAP_RAW_SHA256 = "31b5f30d6b5f2fbda9ecf2c1240db3ecc1af9dba6377ac8d79468f0b685d8326"
EXACT_ID_RAW_SHA256 = "c69bfb3502f2a4dd054e2a7de2b0e95cfb65d288cef4b90aeccd99db829501d9"
RECEIPT_SHA256 = "618e86b82b23eb1645c62bd00f744fd6449d46f1603b10fa5de228eb5915a0c5"


def _load_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z_module",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


NORMALIZER = _load_normalizer()


def test_fresh_predraft_gate_regenerates_its_hash_bound_closed_ledger() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER._canonical_bytes(ledger)

    assert LEDGER_PATH.read_bytes() == expected
    assert hashlib.sha256(expected).hexdigest() == LEDGER_SHA256
    for path, expected_hash in (
        (FULL_OVERLAP_RAW_PATH, FULL_OVERLAP_RAW_SHA256),
        (EXACT_ID_RAW_PATH, EXACT_ID_RAW_SHA256),
        (RECEIPT_PATH, RECEIPT_SHA256),
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
    assert ledger["source_id"] == "arXiv:PaperI-zenodo-predraft-gate-2026-08-07T1600Z"
    assert ledger["gate_status"] == (
        "CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_PREDRAFT_GATE_AS_OF_"
        "2026-08-07T15:52:17Z"
    )
    assert ledger["response_entry_count"] == 908
    assert ledger["screening"]["decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 874,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 34,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }


def test_fresh_predraft_reviewed_nonzero_delta_and_exact_versions_are_fail_closed() -> None:
    """Unlike the zero-delta 2315Z gate, this gate's window accumulated real
    arXiv index catch-up (908 vs. 722 entries) since the prior gate. The
    contract asserted here is therefore a reviewed, nonzero delta: every
    added, missing, version-replaced, or newly rule-triggered ID was
    individually classified nonmaterial, not simply absent."""

    ledger = NORMALIZER.build_ledger()
    recheck = ledger["predraft_gate_recheck"]
    comparison = recheck["full_overlap_comparison"]

    assert comparison["query_semantics_equal"] is True
    assert comparison["feed_cutoff_monotone"] is True
    assert comparison["id_set_equal"] is False
    assert len(comparison["added_ids"]) == 200
    assert len(comparison["missing_ids"]) == 14
    assert comparison["metadata_changed_ids"] == []
    assert comparison["screening_changed_ids"] == []
    assert comparison["material_delta_ids"] == []
    contract = comparison["reviewed_delta_contract"]
    assert {key: contract[key] for key in NORMALIZER.EXPECTED_REVIEWED_DELTA} == (
        NORMALIZER.EXPECTED_REVIEWED_DELTA
    )
    assert set(contract["new_rule_triggered_ids"]) == set(
        NORMALIZER.PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES
    )
    assert set(contract["replacement_base_ids"]) == set(
        NORMALIZER.PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES
    )
    assert ledger["reconciliation"]["metadata_equal_by_id"] is True
    assert ledger["reconciliation"]["reviewed_metadata_changed_ids"] == []
    assert recheck["title_abstract_rescreen"]["candidate_metadata_changed_ids"] == []
    assert recheck["title_abstract_rescreen"]["candidate_decision_changed_ids"] == []
    assert recheck["exact_id_checks"]["versions"] == {
        "2603.25503": "v1",
        "2607.26672": "v1",
    }
    assert recheck["exact_id_checks"]["status"] == "BOTH_TRACKED_RECORDS_REMAIN_V1"


@pytest.mark.parametrize("mutation", ["query", "candidate", "metadata", "new_trigger"])
def test_unclassified_fresh_delta_or_scope_drift_fails_closed(mutation: str) -> None:
    prior = NORMALIZER._load_json(NORMALIZER.PRIOR_GATE_LEDGER)
    current = copy.deepcopy(NORMALIZER.build_ledger())
    if mutation == "query":
        current["effective_response_query"]["categories"] = ["gr-qc"]
        match = "SOL_REVIEW_REQUIRED_QUERY_SCOPE_DRIFT"
    elif mutation == "candidate":
        current["records"] = [
            record for record in current["records"] if record["arxiv_id"] != "2608.06235v1"
        ]
        match = "SOL_REVIEW_REQUIRED_CANDIDATE_SET_DRIFT"
    elif mutation == "new_trigger":
        # Simulate a genuinely new rule-triggered ID never reviewed by Sol.
        template = next(
            record for record in current["records"] if record["arxiv_id"] == "2608.06235v1"
        )
        forged = copy.deepcopy(template)
        forged["arxiv_id"] = "9999.99999v1"
        forged["base_id"] = "9999.99999"
        current["records"].append(forged)
        match = "SOL_REVIEW_REQUIRED_CANDIDATE_SET_DRIFT"
    else:
        prior_ids = {record["arxiv_id"] for record in prior["records"]}
        shared = next(
            record for record in current["records"] if record["arxiv_id"] in prior_ids
        )
        shared["title"] += " changed"
        match = "SOL_REVIEW_REQUIRED_SHARED_METADATA_DRIFT"

    with pytest.raises(NORMALIZER.PredraftGateReviewRequired, match=match):
        NORMALIZER._reviewed_delta_decisions(prior, current)


def test_every_reviewed_candidate_and_replacement_has_a_nonempty_rationale() -> None:
    for arxiv_id, rationale in NORMALIZER.PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES.items():
        assert rationale, arxiv_id
        assert "Claude title/abstract review (2026-08-07 assistant session)" in rationale
    for base_id, rationale in NORMALIZER.PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES.items():
        assert rationale, base_id
        assert "Claude title/abstract review (2026-08-07 assistant session)" in rationale


def test_fresh_gate_source_catalog_and_manifest_bind_its_artifacts() -> None:
    ledger = NORMALIZER.build_ledger()
    NORMALIZER._validate_reference_bindings(ledger, NORMALIZER._canonical_bytes(ledger))
