from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_submission_gate_response.py"
BASELINE_SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_arxiv_delta_response.py"
LEDGER_PATH = ROOT / "references/papers/2026-08-05_paper1_submission_gate_arxiv_normalized.json"
FULL_OVERLAP_RAW_PATH = (
    ROOT / "references/papers/2026-08-05_paper1_submission_gate_arxiv_full_overlap_atom.xml"
)
EXACT_ID_RAW_PATH = (
    ROOT / "references/papers/2026-08-05_paper1_submission_gate_arxiv_exact_ids_atom.xml"
)
REPORT_PATH = ROOT / "reports/v0.4.2_paper1_submission_gate_2026-08-05.md"
NOTE_PATH = ROOT / "references/notes/v0.4.2_paper1_submission_gate_2026-08-05.md"
LEDGER_SHA256 = "ecfd6cc78c604c578ccd970ba1589d5e38262c74f8d806129f96d64f88be775e"
FULL_OVERLAP_RAW_SHA256 = "50bd487ce4aa0c2b34a7cb97e1097031758c4b3c2b1f29cf66af108d6d9d0df9"
EXACT_ID_RAW_SHA256 = "c6010e09756745faae531100ee27bd2196c6691ec93190a9874a8c650213928c"
BASELINE_SCRIPT_SHA256 = "4068b63080d79ac18fb42396759560399bf09a4b1742b934fd78d0598657f303"


def _load_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_normalize_v042_paper1_submission_gate_response_module",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


NORMALIZER = _load_normalizer()


def test_submission_gate_response_regenerates_exact_ledger() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER.BASELINE_NORMALIZER._canonical_bytes(ledger)

    assert LEDGER_PATH.read_bytes() == expected
    assert hashlib.sha256(expected).hexdigest() == LEDGER_SHA256
    assert ledger["raw_response"] == {
        "path": ("references/papers/2026-08-05_paper1_submission_gate_arxiv_full_overlap_atom.xml"),
        "sha256": FULL_OVERLAP_RAW_SHA256,
        "bytes": 1_091_452,
        "feed_updated_utc": "2026-08-05T11:31:24Z",
    }
    assert ledger["gate_status"] == (
        "CLOSED_NO_MATERIAL_DELTA_WITHIN_SUBMISSION_GATE_FULL_OVERLAP_AS_OF_2026-08-05T11:31:24Z"
    )
    assert ledger["response_entry_count"] == 556
    assert ledger["entries_published_in_submitted_date_window"] == 556
    assert ledger["entries_published_outside_submitted_date_window"] == 0
    assert ledger["entries_published_at_or_before_feed_cutoff"] == 556
    assert ledger["entries_published_after_feed_cutoff"] == 0
    assert ledger["screening"]["decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 533,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 23,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }
    assert ledger["screening"]["material_delta_ids"] == []
    assert ledger["submission_gate_recheck"]["authorization_boundary"] == (
        NORMALIZER.AUTHORIZATION_BOUNDARY
    )


def test_full_overlap_comparison_ignores_only_api_response_order() -> None:
    comparison = NORMALIZER.build_ledger()["submission_gate_recheck"]["full_overlap_comparison"]

    assert comparison["query_semantics_equal"] is True
    assert comparison["feed_title_text_equal"] is False
    assert comparison["baseline_response_entry_count"] == 556
    assert comparison["submission_gate_response_entry_count"] == 556
    assert comparison["added_ids"] == []
    assert comparison["missing_ids"] == []
    assert comparison["metadata_changed_ids"] == []
    assert comparison["screening_changed_ids"] == []
    assert comparison["version_pair_diagnostics"] == []
    assert comparison["response_order_equal"] is False
    assert comparison["response_order_moved_record_count"] == 553
    assert comparison["response_order_not_a_materiality_contract"] is True


def test_all_rule_triggered_candidates_are_rescreened_nonmaterial() -> None:
    ledger = NORMALIZER.build_ledger()
    rescreen = ledger["submission_gate_recheck"]["title_abstract_rescreen"]
    triggered = [record for record in ledger["records"] if record["screening"]["rule_matches"]]

    assert rescreen["records_screened"] == 556
    assert rescreen["rule_triggered_candidates"] == 23
    assert rescreen["candidate_ids"] == sorted(
        NORMALIZER.BASELINE_NORMALIZER.INSPECTED_NONMATERIAL_RATIONALES
    )
    assert rescreen["candidate_metadata_changed_ids"] == []
    assert rescreen["candidate_decision_changed_ids"] == []
    assert rescreen["material_delta_ids"] == []
    assert rescreen["status"] == "COMPLETED_NO_MATERIAL_DELTA"
    assert len(triggered) == 23
    assert all(
        record["screening"]["decision"] == "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5"
        and record["screening"]["decision_basis"]
        for record in triggered
    )


def test_exact_id_atom_response_binds_versions_and_updated_timestamps() -> None:
    exact = NORMALIZER.build_ledger()["submission_gate_recheck"]["exact_id_checks"]

    assert exact["raw_response"] == {
        "path": ("references/papers/2026-08-05_paper1_submission_gate_arxiv_exact_ids_atom.xml"),
        "sha256": EXACT_ID_RAW_SHA256,
        "bytes": 5_201,
        "feed_updated_utc": "2026-08-05T11:31:40Z",
    }
    assert exact["versions"] == {"2603.25503": "v1", "2607.26672": "v1"}
    assert exact["status"] == "BOTH_TRACKED_RECORDS_REMAIN_V1"
    by_id = {record["base_id"]: record for record in exact["records"]}
    assert by_id["2607.26672"]["updated_utc"] == "2026-07-29T09:28:18Z"
    assert by_id["2603.25503"]["updated_utc"] == "2026-03-26T14:41:23Z"


@pytest.mark.parametrize(
    "parameters",
    [
        "search_query=&id_list=2607.26672&start=0&max_results=2",
        "search_query=&id_list=2607.26672,2603.25503&start=1&max_results=2",
        "search_query=cpobc&id_list=2607.26672,2603.25503&start=0&max_results=2",
    ],
)
def test_exact_id_query_drift_fails_closed(parameters: str) -> None:
    with pytest.raises(ValueError):
        NORMALIZER._parse_exact_query(parameters, label="test")


def test_version_pair_diagnostic_exposes_update_without_classifying_materiality() -> None:
    baseline = [{"base_id": "2607.26672", "version": "v1"}]
    changed = [{"base_id": "2607.26672", "version": "v2"}]

    assert NORMALIZER._version_pair_diagnostics(baseline, changed) == [
        {
            "base_id": "2607.26672",
            "baseline_versions": ["v1"],
            "submission_gate_versions": ["v2"],
        }
    ]


@pytest.mark.parametrize(
    "delta_kind",
    ["added", "missing", "metadata_changed", "screening_changed"],
)
def test_each_full_overlap_delta_category_requires_sol_review(delta_kind: str) -> None:
    baseline = NORMALIZER._load_json(NORMALIZER.BASELINE_LEDGER)
    changed = copy.deepcopy(baseline)
    records = changed["records"]

    if delta_kind == "added":
        added = copy.deepcopy(records[0])
        added["response_index"] = len(records)
        added["arxiv_id"] = "9999.99999v1"
        added["base_id"] = "9999.99999"
        records.append(added)
    elif delta_kind == "missing":
        records.pop()
    elif delta_kind == "metadata_changed":
        records[0]["title"] += " changed"
    else:
        records[0]["screening"]["decision_basis"] += " changed"

    with pytest.raises(
        NORMALIZER.SubmissionGateReviewRequired,
        match="SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA",
    ):
        NORMALIZER._compare_full_overlap_or_require_review(baseline, changed)


@pytest.mark.parametrize("delta_kind", ["v2", "updated", "metadata"])
def test_each_exact_id_update_category_requires_sol_review(delta_kind: str) -> None:
    snapshot = NORMALIZER._exact_id_snapshot()
    records = copy.deepcopy(snapshot["records"])
    catalog = NORMALIZER._load_json(NORMALIZER.SOURCES)
    xu = next(record for record in records if record["base_id"] == "2607.26672")

    if delta_kind == "v2":
        xu["version"] = "v2"
        xu["arxiv_id"] = "2607.26672v2"
    elif delta_kind == "updated":
        xu["updated_utc"] = "2026-07-29T09:28:19Z"
    else:
        xu["title"] += " changed"

    with pytest.raises(
        NORMALIZER.SubmissionGateReviewRequired,
        match="SOL_REVIEW_REQUIRED_EXACT_ID_",
    ):
        NORMALIZER._validate_exact_id_records(records, catalog)


def test_status_and_feed_cutoff_are_not_runtime_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    original_status = NORMALIZER.GATE_STATUS
    monkeypatch.setattr(NORMALIZER, "GATE_STATUS", "CLOSED_WITHOUT_FEED_BINDING")
    with pytest.raises(ValueError, match="status is not derived"):
        NORMALIZER.build_ledger()

    monkeypatch.setattr(NORMALIZER, "GATE_STATUS", original_status)
    monkeypatch.setattr(NORMALIZER, "SNAPSHOT_FEED_UPDATED_UTC", "2026-08-05T11:31:25Z")
    with pytest.raises(ValueError, match="artifact-specific"):
        NORMALIZER.build_ledger()


def test_registry_bindings_and_baseline_normalizer_are_immutable() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER.BASELINE_NORMALIZER._canonical_bytes(ledger)

    NORMALIZER._validate_reference_bindings(ledger, expected)
    assert hashlib.sha256(BASELINE_SCRIPT_PATH.read_bytes()).hexdigest() == BASELINE_SCRIPT_SHA256
    assert hashlib.sha256(FULL_OVERLAP_RAW_PATH.read_bytes()).hexdigest() == (
        FULL_OVERLAP_RAW_SHA256
    )
    assert hashlib.sha256(EXACT_ID_RAW_PATH.read_bytes()).hexdigest() == EXACT_ID_RAW_SHA256


def test_owner_only_authorization_boundary_is_bound_everywhere() -> None:
    fragment = NORMALIZER.OWNER_ONLY_AUTHORIZATION_FRAGMENT
    ledger = NORMALIZER.build_ledger()
    source_catalog = NORMALIZER._load_json(NORMALIZER.SOURCES)
    manifest = NORMALIZER._load_json(NORMALIZER.ARCHIVE_MANIFEST)
    source = next(
        record for record in source_catalog["sources"] if record["id"] == NORMALIZER.SOURCE_ID
    )
    archived = next(
        record for record in manifest["records"] if record["id"] == NORMALIZER.SOURCE_ID
    )

    assert fragment in ledger["submission_gate_recheck"]["claim_boundary"]
    assert fragment in REPORT_PATH.read_text(encoding="utf-8")
    assert fragment in NOTE_PATH.read_text(encoding="utf-8")
    for record in (source, archived):
        assert fragment in record["claim_boundary"]
        assert record["dataset_snapshot"]["authorization_boundary"] == (
            NORMALIZER.AUTHORIZATION_BOUNDARY
        )
