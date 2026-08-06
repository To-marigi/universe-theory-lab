from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T1123Z.py"
LEDGER_PATH = (
    ROOT
    / "references/papers/2026-08-06_paper1_zenodo_predraft_20260806T1123Z_"
    "arxiv_normalized.json"
)
FULL_OVERLAP_RAW_PATH = (
    ROOT
    / "references/papers/2026-08-06_paper1_zenodo_predraft_20260806T1123Z_"
    "arxiv_full_overlap_atom.xml"
)
EXACT_ID_RAW_PATH = (
    ROOT
    / "references/papers/2026-08-06_paper1_zenodo_predraft_20260806T1123Z_"
    "arxiv_exact_ids_atom.xml"
)
RECEIPT_PATH = (
    ROOT
    / "references/papers/2026-08-06_paper1_zenodo_predraft_20260806T1123Z_"
    "arxiv_retrieval.json"
)
REPORT_PATH = ROOT / "reports/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-06T1123Z.md"
NOTE_PATH = (
    ROOT / "references/notes/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-06T1123Z.md"
)
LEDGER_SHA256 = "4066604659f286dcdb134e295bd2c31c1736c7583a4ac2c8d51d65eeb9a84f6b"
FULL_OVERLAP_RAW_SHA256 = "a7e0bef901b70998fa64d3f4f6f7e8882ee8b7508ea935f9cafc664ce1218cf4"
EXACT_ID_RAW_SHA256 = "fbe8a6498392001e23a85ca9cd6765fc404de1f915acc0a4d4fd4761b8bdba43"
RECEIPT_SHA256 = "0b56aa1a0cc49f023110d8f19e3ef7772f22eda92848403f1f624daaa8784428"


def _load_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_normalize_v042_paper1_zenodo_predraft_gate_20260806T1123Z_module",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


NORMALIZER = _load_normalizer()


def _record_by_id(records: list[dict[str, object]], arxiv_id: str) -> dict[str, object]:
    matches = [record for record in records if record["arxiv_id"] == arxiv_id]
    assert len(matches) == 1
    return matches[0]


def test_predraft_gate_regenerates_ledger_hashes_and_closed_result() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER._canonical_bytes(ledger)

    assert LEDGER_PATH.read_bytes() == expected
    assert hashlib.sha256(expected).hexdigest() == LEDGER_SHA256
    assert len(expected) == 700_160
    assert hashlib.sha256(FULL_OVERLAP_RAW_PATH.read_bytes()).hexdigest() == FULL_OVERLAP_RAW_SHA256
    assert FULL_OVERLAP_RAW_PATH.stat().st_size == 1_422_899
    assert hashlib.sha256(EXACT_ID_RAW_PATH.read_bytes()).hexdigest() == EXACT_ID_RAW_SHA256
    assert EXACT_ID_RAW_PATH.stat().st_size == 5_201
    assert hashlib.sha256(RECEIPT_PATH.read_bytes()).hexdigest() == RECEIPT_SHA256
    assert RECEIPT_PATH.stat().st_size == 2_004
    assert ledger["gate_status"] == (
        "CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_PREDRAFT_GATE_AS_OF_2026-08-06T11:28:07Z"
    )
    assert ledger["response_entry_count"] == 722
    assert ledger["entries_published_in_submitted_date_window"] == 722
    assert ledger["entries_published_outside_submitted_date_window"] == 0
    assert ledger["entries_published_at_or_before_feed_cutoff"] == 722
    assert ledger["entries_published_after_feed_cutoff"] == 0
    assert ledger["screening"]["decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 694,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 28,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }


def test_sol_reviewed_delta_contract_and_exact_versions_are_bound() -> None:
    ledger = NORMALIZER.build_ledger()
    recheck = ledger["predraft_gate_recheck"]
    comparison = recheck["full_overlap_comparison"]
    reviewed = recheck["reviewed_versioned_id_delta"]

    assert comparison["query_semantics_equal"] is True
    assert comparison["feed_cutoff_monotone"] is True
    assert comparison["prior_feed_updated_utc"] == "2026-08-06T00:47:37Z"
    assert comparison["predraft_feed_updated_utc"] == "2026-08-06T11:28:07Z"
    assert comparison["prior_response_entry_count"] == 556
    assert comparison["predraft_response_entry_count"] == 722
    assert comparison["reviewed_delta_contract"] == NORMALIZER.EXPECTED_REVIEWED_DELTA
    assert comparison["material_delta_ids"] == []
    reconciliation = ledger["reconciliation"]
    assert reconciliation["metadata_equal_by_id"] is False
    assert reconciliation["metadata_equal_by_id"] is (not comparison["metadata_changed_ids"])
    assert reconciliation["metadata_changes_reviewed"] is True
    assert reconciliation["reviewed_metadata_changed_ids"] == comparison["metadata_changed_ids"]
    assert reviewed["sol_title_abstract_review_required"] is True
    assert reviewed["sol_title_abstract_review_completed"] is True
    assert reviewed["full_text_or_pdf_required"] is False
    assert reviewed["manuscript_change_required"] is False
    assert recheck["title_abstract_rescreen"]["status"] == "COMPLETED_REVIEWED_NO_MATERIAL_DELTA"
    assert recheck["exact_id_checks"]["versions"] == {"2603.25503": "v1", "2607.26672": "v1"}
    assert recheck["exact_id_checks"]["status"] == "BOTH_TRACKED_RECORDS_REMAIN_V1"
    assert recheck["authorization_boundary"] == NORMALIZER.AUTHORIZATION_BOUNDARY
    assert NORMALIZER.OWNER_ONLY_AUTHORIZATION_FRAGMENT in recheck["claim_boundary"]


def test_every_sol_rationale_is_bound_to_ledger_report_and_research_note() -> None:
    ledger = NORMALIZER.build_ledger()
    reviewed = ledger["predraft_gate_recheck"]["reviewed_versioned_id_delta"]
    report = REPORT_PATH.read_text(encoding="utf-8")
    note = NOTE_PATH.read_text(encoding="utf-8")

    new_trigger_records = reviewed["new_rule_triggered_nonmaterial"]
    version_records = reviewed["version_replacement_nonmaterial"]
    metadata_records = reviewed["shared_versioned_metadata_nonmaterial"]
    assert len(new_trigger_records) == 5
    assert len(version_records) == 12
    assert len(metadata_records) == 2
    assert [record["arxiv_id"] for record in new_trigger_records] == sorted(
        NORMALIZER.PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES
    )
    assert [record["base_id"] for record in version_records] == sorted(
        NORMALIZER.PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES
    )
    assert [record["arxiv_id"] for record in metadata_records] == sorted(
        NORMALIZER.PREDRAFT_REVIEWED_SHARED_METADATA_RATIONALES
    )

    for record in new_trigger_records + version_records + metadata_records:
        rationale = record["rationale"]
        assert rationale in report
        assert rationale in note

    for arxiv_id, rationale in NORMALIZER.PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES.items():
        screening = _record_by_id(ledger["records"], arxiv_id)["screening"]
        assert screening["decision"] == "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5"
        assert screening["decision_basis"] == rationale


@pytest.mark.parametrize("mutation", ["query", "new_candidate", "shared_metadata"])
def test_unreviewed_predraft_delta_or_scope_drift_fails_closed(mutation: str) -> None:
    prior = NORMALIZER._load_json(NORMALIZER.PRIOR_GATE_LEDGER)
    current = copy.deepcopy(NORMALIZER.build_ledger())

    if mutation == "query":
        current["effective_response_query"]["categories"] = ["gr-qc"]
        match = "SOL_REVIEW_REQUIRED_QUERY_SCOPE_DRIFT"
    elif mutation == "new_candidate":
        current["records"] = [
            record for record in current["records"] if record["arxiv_id"] != "2608.05077v1"
        ]
        match = "SOL_REVIEW_REQUIRED_CANDIDATE_SET_DRIFT"
    else:
        record = _record_by_id(current["records"], "2608.02182v1")
        record["title"] += " changed"
        match = "SOL_REVIEW_REQUIRED_SHARED_METADATA_SHAPE_DRIFT"

    with pytest.raises(NORMALIZER.PredraftGateReviewRequired, match=match):
        NORMALIZER._reviewed_delta_decisions(prior, current)


def test_metadata_reconciliation_requires_the_exact_sol_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = NORMALIZER._reviewed_delta_decisions

    def incomplete_review(
        prior: dict[str, object], current: dict[str, object]
    ) -> tuple[dict[str, object], dict[str, object]]:
        comparison, reviewed = original(prior, current)
        changed_reviewed = copy.deepcopy(reviewed)
        changed_reviewed["shared_versioned_metadata_nonmaterial"] = []
        return comparison, changed_reviewed

    monkeypatch.setattr(NORMALIZER, "_reviewed_delta_decisions", incomplete_review)
    with pytest.raises(
        NORMALIZER.PredraftGateReviewRequired,
        match="SOL_REVIEW_REQUIRED_RECONCILIATION_DRIFT",
    ):
        NORMALIZER.build_ledger()


def test_source_catalog_and_generated_manifest_bind_predraft_artifacts() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER._canonical_bytes(ledger)

    NORMALIZER._validate_reference_bindings(ledger, expected)
    source_record = NORMALIZER.source_record(ledger, expected)
    snapshot = source_record["dataset_snapshot"]
    assert snapshot["reviewed_versioned_id_delta"]["complete_per_record_rationales"] == {
        "path": NORMALIZER.OUTPUT_LEDGER.as_posix(),
        "field": "predraft_gate_recheck.reviewed_versioned_id_delta",
    }
    assert snapshot["metadata_reconciliation"] == {
        "metadata_equal_by_id": False,
        "metadata_changes_reviewed": True,
        "reviewed_metadata_changed_ids": ["2608.02182v1", "2608.02458v1"],
    }
