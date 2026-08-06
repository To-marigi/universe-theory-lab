from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py"
LEDGER_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_normalized.json"
)
FULL_OVERLAP_RAW_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_full_overlap_atom.xml"
)
EXACT_ID_RAW_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_exact_ids_atom.xml"
)
RECEIPT_PATH = (
    ROOT
    / "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_retrieval.json"
)
LEDGER_SHA256 = "084e69f06f31c93e5f7b9394da15e088733b45074dc7d59920e86507c516c456"
FULL_OVERLAP_RAW_SHA256 = "5755490b293f9cd8e78217de7ea01e4799ffbb1df04daa0d4f411974caf7b373"
EXACT_ID_RAW_SHA256 = "eff76a847e3b02a01041fd8185e38bbaba93ec769ca037c903719f0062b920eb"
RECEIPT_SHA256 = "fbe9b22defc23e84627339f9844ea8c8078ce96e563c6dfca0f559c57b933523"


def _load_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z_module",
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
    assert len(expected) == 655_325
    for path, expected_hash, expected_size in (
        (FULL_OVERLAP_RAW_PATH, FULL_OVERLAP_RAW_SHA256, 1_422_899),
        (EXACT_ID_RAW_PATH, EXACT_ID_RAW_SHA256, 5_201),
        (RECEIPT_PATH, RECEIPT_SHA256, 2_004),
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
        assert path.stat().st_size == expected_size
    assert ledger["source_id"] == "arXiv:PaperI-zenodo-predraft-gate-2026-08-06T2315Z"
    assert ledger["gate_status"] == (
        "CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_PREDRAFT_GATE_AS_OF_"
        "2026-08-06T23:16:23Z"
    )
    assert ledger["response_entry_count"] == 722
    assert ledger["screening"]["decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 694,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 28,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }


def test_fresh_predraft_zero_delta_and_exact_versions_are_fail_closed_contracts() -> None:
    ledger = NORMALIZER.build_ledger()
    recheck = ledger["predraft_gate_recheck"]
    comparison = recheck["full_overlap_comparison"]

    assert comparison["query_semantics_equal"] is True
    assert comparison["feed_cutoff_monotone"] is True
    assert comparison["id_set_equal"] is True
    for key in (
        "added_ids",
        "missing_ids",
        "metadata_changed_ids",
        "screening_changed_ids",
        "version_pair_diagnostics",
        "material_delta_ids",
    ):
        assert comparison[key] == []
    assert comparison["reviewed_delta_contract"] == NORMALIZER.EXPECTED_REVIEWED_DELTA
    assert ledger["reconciliation"]["metadata_equal_by_id"] is True
    assert ledger["reconciliation"]["reviewed_metadata_changed_ids"] == []
    assert recheck["title_abstract_rescreen"]["candidate_metadata_changed_ids"] == []
    assert recheck["title_abstract_rescreen"]["candidate_decision_changed_ids"] == []
    assert recheck["exact_id_checks"]["versions"] == {
        "2603.25503": "v1",
        "2607.26672": "v1",
    }
    assert recheck["exact_id_checks"]["status"] == "BOTH_TRACKED_RECORDS_REMAIN_V1"


@pytest.mark.parametrize("mutation", ["query", "candidate", "metadata"])
def test_unclassified_fresh_delta_or_scope_drift_fails_closed(mutation: str) -> None:
    prior = NORMALIZER._load_json(NORMALIZER.PRIOR_GATE_LEDGER)
    current = copy.deepcopy(NORMALIZER.build_ledger())
    if mutation == "query":
        current["effective_response_query"]["categories"] = ["gr-qc"]
        match = "SOL_REVIEW_REQUIRED_QUERY_SCOPE_DRIFT"
    elif mutation == "candidate":
        current["records"] = [
            record for record in current["records"] if record["arxiv_id"] != "2608.05077v1"
        ]
        match = "SOL_REVIEW_REQUIRED_REVIEWED_DELTA_DRIFT"
    else:
        current["records"][0]["title"] += " changed"
        match = "SOL_REVIEW_REQUIRED_SHARED_METADATA_DRIFT"

    with pytest.raises(NORMALIZER.PredraftGateReviewRequired, match=match):
        NORMALIZER._reviewed_delta_decisions(prior, current)


def test_fresh_gate_source_catalog_and_manifest_bind_its_artifacts() -> None:
    ledger = NORMALIZER.build_ledger()
    NORMALIZER._validate_reference_bindings(ledger, NORMALIZER._canonical_bytes(ledger))
