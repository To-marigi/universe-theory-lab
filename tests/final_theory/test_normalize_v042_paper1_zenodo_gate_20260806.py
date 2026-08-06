from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_zenodo_gate_20260806.py"
LEDGER_PATH = ROOT / "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_normalized.json"
FULL_OVERLAP_RAW_PATH = (
    ROOT / "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_full_overlap_atom.xml"
)
EXACT_ID_RAW_PATH = (
    ROOT / "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_exact_ids_atom.xml"
)
RECEIPT_PATH = ROOT / "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_retrieval.json"
LEDGER_SHA256 = "3b8f474592ec6c5ed31a2463e2a1fd924afee7bcea90da44c8b3e22052b9642a"
FULL_OVERLAP_RAW_SHA256 = "c2b42041557a012f2847b069c3f217863a0b435249422cc8c2f35a4cd7fdf9e4"
EXACT_ID_RAW_SHA256 = "d95502ec8339d3f378080a60adfdde70b59f5942519e2aad6ce0d69d4b97166d"
RECEIPT_SHA256 = "434da49c430eed3790e389fd513575b6c57ef7d04b787d29dd3a568805bdf41d"


def _load_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_normalize_v042_paper1_zenodo_gate_20260806_module",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


NORMALIZER = _load_normalizer()


def test_zenodo_gate_regenerates_exact_ledger_and_archived_hashes() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER._canonical_bytes(ledger)

    assert LEDGER_PATH.read_bytes() == expected
    assert hashlib.sha256(expected).hexdigest() == LEDGER_SHA256
    assert hashlib.sha256(FULL_OVERLAP_RAW_PATH.read_bytes()).hexdigest() == FULL_OVERLAP_RAW_SHA256
    assert hashlib.sha256(EXACT_ID_RAW_PATH.read_bytes()).hexdigest() == EXACT_ID_RAW_SHA256
    assert hashlib.sha256(RECEIPT_PATH.read_bytes()).hexdigest() == RECEIPT_SHA256
    assert ledger["gate_status"] == (
        "CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_GATE_FULL_OVERLAP_AS_OF_2026-08-06T00:47:37Z"
    )
    assert ledger["response_entry_count"] == 556
    assert ledger["entries_published_in_submitted_date_window"] == 556
    assert ledger["entries_published_outside_submitted_date_window"] == 0
    assert ledger["entries_published_after_feed_cutoff"] == 0
    assert ledger["screening"]["decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 533,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 23,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }


def test_expanded_window_comparison_preserves_prior_scope_and_records() -> None:
    comparison = NORMALIZER.build_ledger()["zenodo_gate_recheck"]["full_overlap_comparison"]

    assert comparison["prior_scope_preserved"] is True
    assert comparison["window_start_not_later_than_prior"] is True
    assert comparison["window_end_not_earlier_than_prior"] is True
    assert comparison["feed_cutoff_monotone"] is True
    assert comparison["prior_window_start_compact_utc"] == "202607311500"
    assert comparison["prior_window_end_compact_utc"] == "202608052359"
    assert comparison["current_window_start_compact_utc"] == "202607311500"
    assert comparison["current_window_end_compact_utc"] == "202608062359"
    assert comparison["previous_response_entry_count"] == 556
    assert comparison["zenodo_gate_response_entry_count"] == 556
    assert comparison["added_ids"] == []
    assert comparison["missing_ids"] == []
    assert comparison["metadata_changed_ids"] == []
    assert comparison["screening_changed_ids"] == []
    assert comparison["version_pair_diagnostics"] == []
    assert comparison["response_order_equal"] is False
    assert comparison["response_order_moved_record_count"] == 401


@pytest.mark.parametrize("delta_kind", ["start", "end", "category", "feed"])
def test_scope_or_cutoff_regression_requires_sol_review(delta_kind: str) -> None:
    previous = NORMALIZER._load_json(NORMALIZER.PREVIOUS_GATE_LEDGER)
    current = NORMALIZER.build_ledger()
    changed = copy.deepcopy(current)

    if delta_kind == "start":
        changed["effective_response_query"]["window_start_compact_utc"] = "202607311501"
    elif delta_kind == "end":
        changed["effective_response_query"]["window_end_compact_utc"] = "202608052358"
    elif delta_kind == "category":
        changed["effective_response_query"]["categories"] = ["gr-qc"]
    else:
        changed["raw_response"]["feed_updated_utc"] = "2026-08-05T11:31:23Z"

    with pytest.raises(NORMALIZER.ZenodoGateReviewRequired, match="SOL_REVIEW_REQUIRED"):
        NORMALIZER._compare_expanded_window_or_require_review(previous, changed)


@pytest.mark.parametrize("delta_kind", ["added", "missing", "metadata", "screening"])
def test_record_delta_requires_sol_review(delta_kind: str) -> None:
    previous = NORMALIZER._load_json(NORMALIZER.PREVIOUS_GATE_LEDGER)
    changed = NORMALIZER.build_ledger()
    changed = copy.deepcopy(changed)
    records = changed["records"]

    if delta_kind == "added":
        added = copy.deepcopy(records[0])
        added["response_index"] = len(records)
        added["arxiv_id"] = "9999.99999v1"
        added["base_id"] = "9999.99999"
        records.append(added)
    elif delta_kind == "missing":
        records.pop()
    elif delta_kind == "metadata":
        records[0]["title"] += " changed"
    else:
        records[0]["screening"]["decision_basis"] += " changed"

    with pytest.raises(
        NORMALIZER.ZenodoGateReviewRequired,
        match="SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA",
    ):
        NORMALIZER._compare_expanded_window_or_require_review(previous, changed)


def test_exact_ids_candidates_and_owner_boundary_remain_bound() -> None:
    ledger = NORMALIZER.build_ledger()
    recheck = ledger["zenodo_gate_recheck"]

    assert recheck["exact_id_checks"]["versions"] == {"2603.25503": "v1", "2607.26672": "v1"}
    assert recheck["exact_id_checks"]["status"] == "BOTH_TRACKED_RECORDS_REMAIN_V1"
    assert recheck["title_abstract_rescreen"]["rule_triggered_candidates"] == 23
    assert recheck["title_abstract_rescreen"]["material_delta_ids"] == []
    assert recheck["authorization_boundary"] == NORMALIZER.AUTHORIZATION_BOUNDARY
    assert NORMALIZER.OWNER_ONLY_AUTHORIZATION_FRAGMENT in recheck["claim_boundary"]


def test_source_and_generated_manifest_bind_every_artifact() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER._canonical_bytes(ledger)

    NORMALIZER._validate_reference_bindings(ledger, expected)
