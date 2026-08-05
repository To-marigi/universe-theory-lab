from __future__ import annotations

import copy
import hashlib
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/normalize_v042_paper1_arxiv_delta_response.py"
LEDGER_PATH = ROOT / "references/papers/2026-08-05_paper1_arxiv_delta_query_normalized.json"
RAW_PATH = ROOT / "references/papers/2026-08-05_paper1_arxiv_delta_query_atom.xml"
LEDGER_SHA256 = "39e12901c8db41a63070cb4ea1794a1da415aeea8c8df0160df79d7224a42c29"
RAW_SHA256 = "8f1b253e2eebaa4788f19616c15ef4cc250da80bfc0d640eea4bd01b7eee08a3"


def _load_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_normalize_v042_paper1_arxiv_delta_response_module",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


NORMALIZER = _load_normalizer()


def test_archived_response_regenerates_exact_screened_ledger() -> None:
    ledger = NORMALIZER.build_ledger()
    expected = NORMALIZER._canonical_bytes(ledger)
    assert LEDGER_PATH.read_bytes() == expected
    assert hashlib.sha256(expected).hexdigest() == LEDGER_SHA256
    assert ledger["raw_response"]["sha256"] == RAW_SHA256
    assert ledger["gate_status"] == (
        "CLOSED_NO_MATERIAL_DELTA_WITHIN_ARCHIVED_SUBMITTEDDATE_SCOPE_AS_OF_2026-08-05T04:52:45Z"
    )
    assert ledger["effective_response_query"] == {
        "authority": "ARCHIVED_ATOM_FEED_TITLE_AND_QUERY_LINK",
        "field": "submittedDate",
        "window_start_compact_utc": "202607311500",
        "window_end_compact_utc": "202608052359",
        "categories": [
            "gr-qc",
            "quant-ph",
            "math-ph",
            "math.OA",
            "math.RA",
            "math.AC",
            "math.FA",
            "math.CO",
        ],
        "start": 0,
        "max_results": 2000,
        "id_list": [],
        "window_start_utc": "2026-07-31T15:00:00Z",
        "window_end_minute_utc": "2026-08-05T23:59:00Z",
        "window_end_exclusive_utc": "2026-08-06T00:00:00Z",
        "feed_title": (
            'arXiv Query: search_query=submittedDate:"202607311500 TO 202608052359" '
            "AND (cat:gr-qc OR cat:quant-ph OR cat:math-ph OR cat:math.OA OR "
            "cat:math.RA OR cat:math.AC OR cat:math.FA OR cat:math.CO)&id_list="
            "&start=0&max_results=2000"
        ),
        "self_link": (
            "https://arxiv.org/api/query?search_query=submittedDate:%22202607311500+TO+"
            "202608052359%22+AND+(cat:gr-qc+OR+(cat:quant-ph+OR+(cat:math-ph+OR+"
            "(cat:math.OA+OR+(cat:math.RA+OR+(cat:math.AC+OR+(cat:math.FA+OR+"
            "cat:math.CO)))))))&start=0&max_results=2000&id_list="
        ),
    }
    assert ledger["opensearch"] == {
        "total_results": 556,
        "start_index": 0,
        "items_per_page": 2000,
    }
    assert ledger["response_entry_count"] == 556
    assert ledger["entries_published_in_submitted_date_window"] == 556
    assert ledger["entries_published_outside_submitted_date_window"] == 0
    assert ledger["entries_published_at_or_before_feed_cutoff"] == 556
    assert ledger["entries_published_after_feed_cutoff"] == 0
    assert ledger["minimum_published_utc"] == "2026-07-31T15:01:28Z"
    assert ledger["maximum_published_utc"] == "2026-08-04T17:59:09Z"
    assert ledger["screening"]["decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 533,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 23,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }
    assert ledger["screening"]["material_delta_ids"] == []
    assert ledger["coverage_boundary"]["general_pre_window_version_updates_covered"] is False
    assert ledger["reconciliation"] == {
        "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
        "historical_reported_screened_record_count": 524,
        "historical_524_query_provenance_known": False,
        "historical_524_id_membership_known": False,
        "comparison_to_archived_556_authorized": False,
        "materiality_reassessment_status": "COMPLETED_ON_ARCHIVED_556_RESPONSE",
    }
    NORMALIZER._validate_reference_bindings(ledger, expected)


def test_every_triggered_candidate_has_an_explicit_nonmaterial_rationale() -> None:
    ledger = NORMALIZER.build_ledger()
    triggered = [record for record in ledger["records"] if record["screening"]["rule_matches"]]
    assert len(triggered) == 23
    assert {record["arxiv_id"] for record in triggered} == set(
        NORMALIZER.INSPECTED_NONMATERIAL_RATIONALES
    )
    assert all(
        record["screening"]["decision"] == "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5"
        and record["screening"]["decision_basis"]
        for record in triggered
    )


def _raw_feed() -> ET.Element:
    return ET.fromstring(RAW_PATH.read_bytes())


def test_archived_feed_title_and_query_link_independently_bind_effective_scope() -> None:
    query = NORMALIZER._effective_response_query(_raw_feed())

    assert query["field"] == "submittedDate"
    assert query["window_start_compact_utc"] == "202607311500"
    assert query["window_end_compact_utc"] == "202608052359"
    assert query["categories"] == NORMALIZER.QUERY_CATEGORIES
    assert query["start"] == 0
    assert query["max_results"] == 2000
    assert query["id_list"] == []


@pytest.mark.parametrize(
    ("component", "old", "new"),
    [
        ("title", "submittedDate", "updatedDate"),
        ("link", "202607311500", "202607311501"),
        ("title", "cat:math.CO", "cat:math.PR"),
        ("link", "start=0", "start=1"),
        ("title", "max_results=2000", "max_results=1999"),
    ],
)
def test_archived_feed_query_semantic_drift_fails_closed(
    component: str,
    old: str,
    new: str,
) -> None:
    root = copy.deepcopy(_raw_feed())
    if component == "title":
        title = root.find("atom:title", NORMALIZER.NS)
        assert title is not None and title.text is not None
        title.text = title.text.replace(old, new)
    else:
        links = root.findall("atom:link", NORMALIZER.NS)
        assert len(links) == 1
        href = links[0].get("href")
        assert href is not None
        links[0].set("href", href.replace(old, new))

    with pytest.raises(ValueError):
        NORMALIZER._effective_response_query(root)
