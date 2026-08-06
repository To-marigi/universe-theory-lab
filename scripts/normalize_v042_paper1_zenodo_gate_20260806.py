"""Archive and verify the 2026-08-06 Paper I Zenodo literature gate.

The earlier 2026-08-05 normalizers remain immutable evidence.  This dated
wrapper reuses their parsing and screening contracts, archives a new official
arXiv response with a bounded expanded submittedDate window, and fails closed
on every ID-keyed or metadata change.  ``--fetch`` is deliberately separate
from ``--check``: it is the only network action and it never overwrites an
archived response.

The resulting closed technical gate is not permission to freeze, submit,
deposit, or publish anything.  Those decisions remain owner-only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SCREENING_NORMALIZER_PATH = ROOT / "scripts/normalize_v042_paper1_arxiv_delta_response.py"
PREVIOUS_GATE_NORMALIZER_PATH = ROOT / "scripts/normalize_v042_paper1_submission_gate_response.py"
PREVIOUS_GATE_LEDGER = Path(
    "references/papers/2026-08-05_paper1_submission_gate_arxiv_normalized.json"
)
RAW_RESPONSE = Path(
    "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_full_overlap_atom.xml"
)
EXACT_ID_RESPONSE = Path(
    "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_exact_ids_atom.xml"
)
RETRIEVAL_RECEIPT = Path(
    "references/papers/2026-08-06_paper1_zenodo_gate_arxiv_retrieval.json"
)
OUTPUT_LEDGER = Path("references/papers/2026-08-06_paper1_zenodo_gate_arxiv_normalized.json")
SOURCES = Path("references/sources.json")
ARCHIVE_MANIFEST = Path("references/manifest.json")
SOURCE_ID = "arXiv:PaperI-zenodo-gate-recheck-2026-08-06"
PREVIOUS_SOURCE_ID = "arXiv:PaperI-submission-gate-recheck-2026-08-05T113124Z"
NORMALIZER_PATH = "scripts/normalize_v042_paper1_zenodo_gate_20260806.py"
CHECK_COMMAND = (
    ".venv\\Scripts\\python.exe scripts/normalize_v042_paper1_zenodo_gate_20260806.py --check"
)
FETCH_COMMAND = (
    ".venv\\Scripts\\python.exe scripts/normalize_v042_paper1_zenodo_gate_20260806.py --fetch"
)
QUERY_WINDOW_START = "202607311500"
QUERY_WINDOW_END = "202608062359"
QUERY_CATEGORIES = [
    "gr-qc",
    "quant-ph",
    "math-ph",
    "math.OA",
    "math.RA",
    "math.AC",
    "math.FA",
    "math.CO",
]
QUERY_MAX_RESULTS = 2000
FULL_OVERLAP_REQUEST_URL = (
    "https://arxiv.org/api/query?search_query=submittedDate:%22202607311500+TO+"
    "202608062359%22+AND+(cat:gr-qc+OR+(cat:quant-ph+OR+(cat:math-ph+OR+"
    "(cat:math.OA+OR+(cat:math.RA+OR+(cat:math.AC+OR+(cat:math.FA+OR+"
    "cat:math.CO)))))))&start=0&max_results=2000&id_list="
)
EXACT_ID_REQUEST_URL = (
    "https://arxiv.org/api/query?id_list=2607.26672,2603.25503&start=0&max_results=2"
)
EXPECTED_EXACT_IDS = ["2607.26672", "2603.25503"]
EXPECTED_EXACT_VERSIONS = {"2607.26672": "v1", "2603.25503": "v1"}
USER_AGENT = "universe-theory-lab/0.4.2 (Paper I Zenodo literature gate)"
OWNER_ONLY_AUTHORIZATION_FRAGMENT = (
    "This artifact closes only a technical literature-delta gate. It does not authorize "
    "manuscript freeze, submission, deposit, or publication; all such actions are "
    "owner-only and remain unapproved."
)
AUTHORIZATION_BOUNDARY = {
    "technical_literature_gate_only": True,
    "manuscript_freeze_authorized": False,
    "submission_authorized": False,
    "deposit_authorized": False,
    "publication_authorized": False,
    "owner_only": True,
}
VERSIONED_ID_RE = re.compile(r"^(?P<base>[0-9]{4}\.[0-9]{4,5})(?P<version>v[1-9][0-9]*)$")


class ZenodoGateReviewRequired(ValueError):
    """A changed literature record must be assessed before this gate can close."""


def _load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load normalizer: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


SCREENING_NORMALIZER = _load_module(
    SCREENING_NORMALIZER_PATH, "v042_paper1_zenodo_gate_screening_normalizer"
)
PREVIOUS_GATE_NORMALIZER = _load_module(
    PREVIOUS_GATE_NORMALIZER_PATH, "v042_paper1_zenodo_gate_previous_normalizer"
)
ATOM = SCREENING_NORMALIZER.ATOM
OPENSEARCH = SCREENING_NORMALIZER.OPENSEARCH
NS = SCREENING_NORMALIZER.NS


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _required_text(parent: ET.Element, path: str, *, label: str) -> str:
    value = parent.findtext(path, namespaces=NS)
    if value is None or not value.strip():
        raise ValueError(f"missing {label}")
    return value.strip()


def _parse_utc(value: str, *, label: str) -> datetime:
    return SCREENING_NORMALIZER._parse_utc(value, label=label)


def _compact_minute_to_utc(value: str, *, label: str) -> datetime:
    return SCREENING_NORMALIZER._compact_minute_to_utc(value, label=label)


def _response_feed_updated(path: Path, *, label: str) -> str:
    root = ET.fromstring((ROOT / path).read_bytes())
    if root.tag != f"{{{ATOM}}}feed":
        raise ValueError(f"unexpected {label} Atom root tag: {root.tag}")
    value = _required_text(root, "atom:updated", label=f"{label} feed updated timestamp")
    _parse_utc(value, label=f"{label} feed updated timestamp")
    return value


def _gate_status(feed_updated_utc: str) -> str:
    return f"CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_GATE_FULL_OVERLAP_AS_OF_{feed_updated_utc}"


def _configure_screening_normalizer(feed_updated_utc: str) -> None:
    normalizer = cast(Any, SCREENING_NORMALIZER)
    normalizer.RAW_RESPONSE = RAW_RESPONSE
    normalizer.OUTPUT_LEDGER = OUTPUT_LEDGER
    normalizer.SOURCE_ID = SOURCE_ID
    normalizer.GATE_STATUS = _gate_status(feed_updated_utc)
    normalizer.QUERY_FIELD = "submittedDate"
    normalizer.QUERY_WINDOW_START = QUERY_WINDOW_START
    normalizer.QUERY_WINDOW_END = QUERY_WINDOW_END
    normalizer.QUERY_CATEGORIES = QUERY_CATEGORIES
    normalizer.QUERY_START = 0
    normalizer.QUERY_MAX_RESULTS = QUERY_MAX_RESULTS


def _parse_exact_query(parameters: str, *, label: str) -> dict[str, Any]:
    return PREVIOUS_GATE_NORMALIZER._parse_exact_query(parameters, label=label)


def _exact_id_snapshot() -> dict[str, Any]:
    path = ROOT / EXACT_ID_RESPONSE
    raw = path.read_bytes()
    root = ET.fromstring(raw)
    if root.tag != f"{{{ATOM}}}feed":
        raise ValueError(f"unexpected exact-ID Atom root tag: {root.tag}")

    title = _required_text(root, "atom:title", label="exact-ID feed title")
    prefix = "arXiv Query: "
    if not title.startswith(prefix):
        raise ValueError(f"unexpected exact-ID feed title: {title!r}")
    title_query = _parse_exact_query(title.removeprefix(prefix), label="feed title")
    links = [
        link for link in root.findall("atom:link", NS) if link.get("type") == "application/atom+xml"
    ]
    if len(links) != 1 or set(links[0].attrib) != {"href", "type"}:
        raise ValueError("expected exactly one exact-ID Atom response query link")
    self_link = links[0].get("href")
    if not isinstance(self_link, str) or not self_link:
        raise ValueError("exact-ID response query link has no href")
    parsed_url = urlparse(self_link)
    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc != "arxiv.org"
        or parsed_url.path != "/api/query"
        or parsed_url.fragment
    ):
        raise ValueError(f"unexpected exact-ID Atom query URL: {self_link!r}")
    link_query = _parse_exact_query(parsed_url.query, label="feed link")
    if link_query != title_query:
        raise ValueError("exact-ID feed title and query link disagree")

    total_results = int(
        _required_text(root, "opensearch:totalResults", label="exact-ID totalResults")
    )
    start_index = int(_required_text(root, "opensearch:startIndex", label="exact-ID startIndex"))
    items_per_page = int(
        _required_text(root, "opensearch:itemsPerPage", label="exact-ID itemsPerPage")
    )
    entries = root.findall("atom:entry", NS)
    if (total_results, start_index, items_per_page, len(entries)) != (2, 0, 2, 2):
        raise ValueError("exact-ID OpenSearch counts drifted")

    records = []
    for entry in entries:
        entry_url = _required_text(entry, "atom:id", label="exact-ID entry ID")
        parsed_entry_url = urlparse(entry_url)
        if parsed_entry_url.netloc != "arxiv.org" or not parsed_entry_url.path.startswith("/abs/"):
            raise ValueError(f"unexpected exact-ID entry URL: {entry_url!r}")
        versioned_id = parsed_entry_url.path.removeprefix("/abs/")
        match = VERSIONED_ID_RE.fullmatch(versioned_id)
        if match is None:
            raise ValueError(f"invalid exact-ID versioned identifier: {versioned_id!r}")
        summary = SCREENING_NORMALIZER._normalized_text(
            _required_text(entry, "atom:summary", label=f"{versioned_id} abstract")
        )
        records.append(
            {
                "arxiv_id": versioned_id,
                "base_id": match.group("base"),
                "version": match.group("version"),
                "updated_utc": _required_text(
                    entry, "atom:updated", label=f"{versioned_id} updated timestamp"
                ),
                "published_utc": _required_text(
                    entry, "atom:published", label=f"{versioned_id} published timestamp"
                ),
                "title": SCREENING_NORMALIZER._normalized_text(
                    _required_text(entry, "atom:title", label=f"{versioned_id} title")
                ),
                "authors": [
                    _required_text(author, "atom:name", label=f"{versioned_id} author")
                    for author in entry.findall("atom:author", NS)
                ],
                "abstract_sha256": _sha256_bytes(summary.encode("utf-8")),
            }
        )
    records.sort(key=lambda record: record["base_id"])
    catalog = _load_json(SOURCES)
    try:
        PREVIOUS_GATE_NORMALIZER._validate_exact_id_records(records, catalog)
    except PREVIOUS_GATE_NORMALIZER.SubmissionGateReviewRequired as exc:
        raise ZenodoGateReviewRequired(str(exc)) from exc
    return {
        "raw_response": {
            "path": EXACT_ID_RESPONSE.as_posix(),
            "sha256": _sha256_bytes(raw),
            "bytes": len(raw),
            "feed_updated_utc": _required_text(
                root, "atom:updated", label="exact-ID feed updated timestamp"
            ),
        },
        "effective_response_query": {
            "authority": "ARCHIVED_ATOM_FEED_TITLE_AND_QUERY_LINK",
            **title_query,
            "feed_title": title,
            "self_link": self_link,
        },
        "opensearch": {
            "total_results": total_results,
            "start_index": start_index,
            "items_per_page": items_per_page,
        },
        "response_entry_count": len(records),
        "records": records,
    }


def _record_map(records: list[dict[str, Any]], transform: Any) -> dict[str, Any]:
    return PREVIOUS_GATE_NORMALIZER._record_map(records, transform)


def _compare_expanded_window_or_require_review(
    previous: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    previous_query = previous["effective_response_query"]
    query = current["effective_response_query"]
    unchanged_keys = ["field", "categories", "start", "max_results", "id_list"]
    changed_query_fields = [
        key for key in unchanged_keys if previous_query.get(key) != query.get(key)
    ]
    previous_start = _compact_minute_to_utc(
        previous_query["window_start_compact_utc"], label="previous submittedDate start"
    )
    current_start = _compact_minute_to_utc(
        query["window_start_compact_utc"], label="current submittedDate start"
    )
    previous_end = _compact_minute_to_utc(
        previous_query["window_end_compact_utc"], label="previous submittedDate end"
    )
    current_end = _compact_minute_to_utc(
        query["window_end_compact_utc"], label="current submittedDate end"
    )
    previous_feed = _parse_utc(
        previous["raw_response"]["feed_updated_utc"], label="previous feed cutoff"
    )
    current_feed = _parse_utc(
        current["raw_response"]["feed_updated_utc"], label="current feed cutoff"
    )
    if changed_query_fields or current_start > previous_start or current_end < previous_end:
        raise ZenodoGateReviewRequired(
            "SOL_REVIEW_REQUIRED_QUERY_SCOPE_DRIFT: expanded Zenodo gate does not preserve "
            "the prior scope; "
            f"changed={changed_query_fields}, start={current_start}, end={current_end}"
        )
    if current_feed < previous_feed:
        raise ZenodoGateReviewRequired(
            "SOL_REVIEW_REQUIRED_NONMONOTONE_FEED_CUTOFF: current feed predates prior gate"
        )

    previous_records = previous["records"]
    records = current["records"]
    previous_metadata = _record_map(
        previous_records, PREVIOUS_GATE_NORMALIZER._metadata_without_order_or_screening
    )
    metadata = _record_map(records, PREVIOUS_GATE_NORMALIZER._metadata_without_order_or_screening)
    previous_screening = _record_map(previous_records, lambda record: record["screening"])
    screening = _record_map(records, lambda record: record["screening"])
    previous_ids = set(previous_metadata)
    ids = set(metadata)
    added_ids = sorted(ids - previous_ids)
    missing_ids = sorted(previous_ids - ids)
    metadata_changed_ids = sorted(
        arxiv_id
        for arxiv_id in ids & previous_ids
        if metadata[arxiv_id] != previous_metadata[arxiv_id]
    )
    screening_changed_ids = sorted(
        arxiv_id
        for arxiv_id in ids & previous_ids
        if screening[arxiv_id] != previous_screening[arxiv_id]
    )
    version_pair_diagnostics = PREVIOUS_GATE_NORMALIZER._version_pair_diagnostics(
        previous_records, records
    )
    previous_positions = {
        record["arxiv_id"]: record["response_index"] for record in previous_records
    }
    positions = {record["arxiv_id"]: record["response_index"] for record in records}
    moved_ids = sorted(
        arxiv_id
        for arxiv_id in ids & previous_ids
        if positions[arxiv_id] != previous_positions[arxiv_id]
    )
    if added_ids or missing_ids or metadata_changed_ids or screening_changed_ids:
        raise ZenodoGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: Zenodo gate literature change must not "
            "be classified automatically: "
            f"added={added_ids}, missing={missing_ids}, metadata={metadata_changed_ids}, "
            f"screening={screening_changed_ids}, version_pairs={version_pair_diagnostics}"
        )
    return {
        "prior_scope_preserved": True,
        "window_start_not_later_than_prior": True,
        "window_end_not_earlier_than_prior": True,
        "feed_cutoff_monotone": True,
        "prior_window_start_compact_utc": previous_query["window_start_compact_utc"],
        "prior_window_end_compact_utc": previous_query["window_end_compact_utc"],
        "current_window_start_compact_utc": query["window_start_compact_utc"],
        "current_window_end_compact_utc": query["window_end_compact_utc"],
        "prior_feed_updated_utc": previous["raw_response"]["feed_updated_utc"],
        "current_feed_updated_utc": current["raw_response"]["feed_updated_utc"],
        "previous_response_entry_count": len(previous_records),
        "zenodo_gate_response_entry_count": len(records),
        "added_ids": added_ids,
        "missing_ids": missing_ids,
        "metadata_changed_ids": metadata_changed_ids,
        "screening_changed_ids": screening_changed_ids,
        "version_pair_diagnostics": version_pair_diagnostics,
        "response_order_equal": not moved_ids,
        "response_order_moved_record_count": len(moved_ids),
        "response_order_not_a_materiality_contract": True,
        "metadata_by_id_sha256": SCREENING_NORMALIZER._compact_digest(metadata),
        "screening_by_id_sha256": SCREENING_NORMALIZER._compact_digest(screening),
    }


def _retrieval_receipt() -> dict[str, Any]:
    receipt = _load_json(RETRIEVAL_RECEIPT)
    required = {
        "schema_version",
        "user_agent",
        "authorization_boundary",
        "retrievals",
        "claim_boundary",
    }
    if set(receipt) != required:
        raise ValueError("retrieval receipt schema drifted")
    if receipt["schema_version"] != "1.0" or receipt["user_agent"] != USER_AGENT:
        raise ValueError("retrieval receipt identity drifted")
    if receipt["authorization_boundary"] != AUTHORIZATION_BOUNDARY:
        raise ValueError("retrieval receipt authorization boundary drifted")
    if OWNER_ONLY_AUTHORIZATION_FRAGMENT not in receipt["claim_boundary"]:
        raise ValueError("retrieval receipt claim boundary drifted")
    retrievals = receipt["retrievals"]
    if set(retrievals) != {"full_overlap", "exact_ids"}:
        raise ValueError("retrieval receipt endpoints drifted")
    expected = {
        "full_overlap": (FULL_OVERLAP_REQUEST_URL, RAW_RESPONSE),
        "exact_ids": (EXACT_ID_REQUEST_URL, EXACT_ID_RESPONSE),
    }
    for name, (url, path) in expected.items():
        entry = retrievals[name]
        required_entry = {
            "requested_url",
            "request_started_utc",
            "retrieved_utc",
            "http_status",
            "content_type",
            "path",
            "sha256",
            "bytes",
        }
        if set(entry) != required_entry:
            raise ValueError(f"retrieval receipt {name} fields drifted")
        if entry["requested_url"] != url or entry["path"] != path.as_posix():
            raise ValueError(f"retrieval receipt {name} request identity drifted")
        if entry["http_status"] != 200:
            raise ValueError(f"retrieval receipt {name} was not HTTP 200")
        started = _parse_utc(entry["request_started_utc"], label=f"{name} request start")
        retrieved = _parse_utc(entry["retrieved_utc"], label=f"{name} retrieval")
        if retrieved < started:
            raise ValueError(f"retrieval receipt {name} completed before it started")
        raw = (ROOT / path).read_bytes()
        if entry["sha256"] != _sha256_bytes(raw) or entry["bytes"] != len(raw):
            raise ValueError(f"retrieval receipt {name} raw hash binding drifted")
    return receipt


def _fetch_one(url: str, path: Path) -> tuple[bytes, dict[str, Any]]:
    started = _utc_now()
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.1",
        },
    )
    with urlopen(request, timeout=90) as response:  # noqa: S310 - fixed official HTTPS endpoint
        payload = response.read()
        status = response.status
        content_type = response.headers.get_content_type()
    retrieved = _utc_now()
    if status != 200 or not payload:
        raise RuntimeError(f"arXiv retrieval failed: status={status}, bytes={len(payload)}")
    return payload, {
        "requested_url": url,
        "request_started_utc": started,
        "retrieved_utc": retrieved,
        "http_status": status,
        "content_type": content_type,
        "path": path.as_posix(),
        "sha256": _sha256_bytes(payload),
        "bytes": len(payload),
    }


def fetch() -> None:
    targets = [ROOT / RAW_RESPONSE, ROOT / EXACT_ID_RESPONSE, ROOT / RETRIEVAL_RECEIPT]
    existing = [str(path.relative_to(ROOT)) for path in targets if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite Zenodo-gate evidence; inspect or deliberately preserve "
            f"the existing artifacts: {existing}"
        )
    full_payload, full_receipt = _fetch_one(FULL_OVERLAP_REQUEST_URL, RAW_RESPONSE)
    time.sleep(3)
    exact_payload, exact_receipt = _fetch_one(EXACT_ID_REQUEST_URL, EXACT_ID_RESPONSE)
    receipt = {
        "schema_version": "1.0",
        "user_agent": USER_AGENT,
        "authorization_boundary": AUTHORIZATION_BOUNDARY,
        "retrievals": {"full_overlap": full_receipt, "exact_ids": exact_receipt},
        "claim_boundary": (
            "This receipt records two official arXiv API HTTP responses and their local "
            "hashes. It supplies no literature, novelty, priority, absence, or publication "
            "claim. "
            + OWNER_ONLY_AUTHORIZATION_FRAGMENT
        ),
    }
    for path, payload in (
        (ROOT / RAW_RESPONSE, full_payload),
        (ROOT / EXACT_ID_RESPONSE, exact_payload),
        (ROOT / RETRIEVAL_RECEIPT, _canonical_bytes(receipt)),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"Archived official arXiv Zenodo-gate responses: {RAW_RESPONSE}, {EXACT_ID_RESPONSE}")


def build_ledger() -> dict[str, Any]:
    receipt = _retrieval_receipt()
    feed_updated = _response_feed_updated(RAW_RESPONSE, label="full-overlap")
    _configure_screening_normalizer(feed_updated)
    try:
        ledger = SCREENING_NORMALIZER.build_ledger()
    except ValueError as exc:
        raise ZenodoGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: screening normalizer failed closed"
        ) from exc
    expected_status = _gate_status(feed_updated)
    if ledger["gate_status"] != expected_status:
        raise ValueError("Zenodo-gate status is not derived from the archived feed cutoff")
    previous = _load_json(PREVIOUS_GATE_LEDGER)
    comparison = _compare_expanded_window_or_require_review(previous, ledger)
    try:
        exact_ids = _exact_id_snapshot()
    except ZenodoGateReviewRequired:
        raise
    except ValueError as exc:
        raise ZenodoGateReviewRequired(
            "SOL_REVIEW_REQUIRED_EXACT_ID_UPDATE: tracked version or metadata changed"
        ) from exc
    exact_versions = {record["base_id"]: record["version"] for record in exact_ids["records"]}
    if exact_versions != EXPECTED_EXACT_VERSIONS:
        raise ZenodoGateReviewRequired("SOL_REVIEW_REQUIRED_EXACT_ID_VERSION_UPDATE")
    candidate_ids = sorted(ledger["screening"]["inspected_candidate_ids"])
    previous_candidates = sorted(previous["screening"]["inspected_candidate_ids"])
    if candidate_ids != previous_candidates:
        raise ZenodoGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: candidate membership changed"
        )

    ledger["schema_version"] = "1.2"
    ledger["coverage_boundary"] = {
        "archived_submitted_date_snapshot_only": True,
        "general_pre_window_version_updates_covered": False,
        "tracked_exact_id_version_checks_archived_with_gate": [
            "arXiv:2607.26672",
            "arXiv:2603.25503",
        ],
        "minimum_pre_zenodo_contract": [
            "archive and rescreen a submittedDate response beginning no later than the baseline",
            "end no earlier than the immediately prior gate and retain a monotone feed cutoff",
            "repeat exact-ID version checks for arXiv:2607.26672 and arXiv:2603.25503",
            "compare all normalized metadata and screening decisions to the prior gate by ID",
        ],
        "minimum_pre_zenodo_contract_status": "SATISFIED_BY_THIS_ARCHIVE",
    }
    ledger["reconciliation"] = {
        "status": "EXPANDED_WINDOW_PRIOR_GATE_RECHECK_COMPLETED",
        "previous_source_id": PREVIOUS_SOURCE_ID,
        "id_set_equal": True,
        "metadata_equal_by_id": True,
        "screening_decisions_equal_by_id": True,
        "materiality_reassessment_status": "COMPLETED_NO_MATERIAL_DELTA",
    }
    ledger["zenodo_gate_recheck"] = {
        "authorization_boundary": dict(AUTHORIZATION_BOUNDARY),
        "previous_gate": {
            "source_id": PREVIOUS_SOURCE_ID,
            "normalized_ledger_path": PREVIOUS_GATE_LEDGER.as_posix(),
            "raw_response_path": previous["raw_response"]["path"],
            "raw_response_sha256": previous["raw_response"]["sha256"],
            "feed_updated_utc": previous["raw_response"]["feed_updated_utc"],
            "response_entry_count": previous["response_entry_count"],
        },
        "retrieval_receipt": {
            "path": RETRIEVAL_RECEIPT.as_posix(),
            "sha256": _sha256_bytes((ROOT / RETRIEVAL_RECEIPT).read_bytes()),
            "bytes": (ROOT / RETRIEVAL_RECEIPT).stat().st_size,
            "retrievals": receipt["retrievals"],
        },
        "full_overlap_comparison": comparison,
        "title_abstract_rescreen": {
            "records_screened": len(ledger["records"]),
            "rule_triggered_candidates": len(candidate_ids),
            "candidate_ids": candidate_ids,
            "candidate_metadata_changed_ids": comparison["metadata_changed_ids"],
            "candidate_decision_changed_ids": comparison["screening_changed_ids"],
            "material_delta_ids": ledger["screening"]["material_delta_ids"],
            "status": "COMPLETED_NO_MATERIAL_DELTA",
        },
        "exact_id_checks": {
            **exact_ids,
            "versions": exact_versions,
            "status": "BOTH_TRACKED_RECORDS_REMAIN_V1",
        },
        "claim_boundary": (
            "This gate proves only that its archived expanded-window submittedDate response "
            "has the same ID set, normalized title/abstract metadata, and C1--C5 screening "
            "decisions as the immediately prior gate, and that the two separately queried "
            "tracked IDs remain at v1. It does not establish exhaustive literature coverage, "
            "novelty, priority, absence, or general pre-window update coverage. "
            + OWNER_ONLY_AUTHORIZATION_FRAGMENT
        ),
    }
    return ledger


def _dataset_snapshot(ledger: dict[str, Any]) -> dict[str, Any]:
    recheck = ledger["zenodo_gate_recheck"]
    exact_checks = recheck["exact_id_checks"]
    exact_summary = {
        "raw_response": exact_checks["raw_response"],
        "effective_response_query": exact_checks["effective_response_query"],
        "response_entry_count": exact_checks["response_entry_count"],
        "versions": exact_checks["versions"],
        "status": exact_checks["status"],
    }
    return {
        "gate_status": ledger["gate_status"],
        "full_overlap_feed_updated_utc": ledger["raw_response"]["feed_updated_utc"],
        "effective_response_query": ledger["effective_response_query"],
        "normalizer": NORMALIZER_PATH,
        "fetch_command": FETCH_COMMAND,
        "check_command": CHECK_COMMAND,
        "response_entry_count": ledger["response_entry_count"],
        "entries_published_in_submitted_date_window": ledger[
            "entries_published_in_submitted_date_window"
        ],
        "entries_published_outside_submitted_date_window": ledger[
            "entries_published_outside_submitted_date_window"
        ],
        "entries_published_at_or_before_feed_cutoff": ledger[
            "entries_published_at_or_before_feed_cutoff"
        ],
        "entries_published_after_feed_cutoff": ledger["entries_published_after_feed_cutoff"],
        "minimum_published_utc": ledger["minimum_published_utc"],
        "maximum_published_utc": ledger["maximum_published_utc"],
        "ordered_arxiv_ids_sha256": f"sha256:{ledger['ordered_arxiv_ids_sha256']}",
        "records_sha256": f"sha256:{ledger['records_sha256']}",
        "screening_decision_counts": ledger["screening"]["decision_counts"],
        "authorization_boundary": recheck["authorization_boundary"],
        "retrieval_receipt": recheck["retrieval_receipt"],
        "full_overlap_comparison": recheck["full_overlap_comparison"],
        "title_abstract_rescreen": recheck["title_abstract_rescreen"],
        "exact_id_checks": exact_summary,
    }


def source_record(ledger: dict[str, Any], ledger_bytes: bytes) -> dict[str, Any]:
    receipt_bytes = (ROOT / RETRIEVAL_RECEIPT).read_bytes()
    exact_raw = ledger["zenodo_gate_recheck"]["exact_id_checks"]["raw_response"]
    return {
        "id": SOURCE_ID,
        "title": "Official arXiv API responses: Paper I Zenodo preparation gate",
        "authors": ["arXiv"],
        "url": ledger["effective_response_query"]["self_link"],
        "exact_id_url": EXACT_ID_REQUEST_URL,
        "retrieved_on": "2026-08-06",
        "local_file": None,
        "local_artifacts": [
            {
                "role": "FULL_OVERLAP_RAW_API_RESPONSE",
                "path": RAW_RESPONSE.relative_to("references").as_posix(),
                "media_type": "application/atom+xml",
                "sha256": f"sha256:{ledger['raw_response']['sha256']}",
                "bytes": ledger["raw_response"]["bytes"],
            },
            {
                "role": "EXACT_ID_RAW_API_RESPONSE",
                "path": EXACT_ID_RESPONSE.relative_to("references").as_posix(),
                "media_type": "application/atom+xml",
                "sha256": f"sha256:{exact_raw['sha256']}",
                "bytes": exact_raw["bytes"],
            },
            {
                "role": "RETRIEVAL_PROVENANCE",
                "path": RETRIEVAL_RECEIPT.relative_to("references").as_posix(),
                "media_type": "application/json",
                "sha256": f"sha256:{_sha256_bytes(receipt_bytes)}",
                "bytes": len(receipt_bytes),
            },
            {
                "role": "NORMALIZED_SCREENING_LEDGER",
                "path": OUTPUT_LEDGER.relative_to("references").as_posix(),
                "media_type": "application/json",
                "sha256": f"sha256:{_sha256_bytes(ledger_bytes)}",
                "bytes": len(ledger_bytes),
            },
        ],
        "dataset_snapshot": _dataset_snapshot(ledger),
        "version": (
            "official arXiv API Atom responses archived for the 2026-08-06 Zenodo preparation "
            f"gate; full-overlap feed timestamp {ledger['raw_response']['feed_updated_utc']}; "
            f"exact-ID feed timestamp {exact_raw['feed_updated_utc']}"
        ),
        "relationship": "SEARCH_DATASET",
        "used_for": [
            "Paper I Zenodo preparation full-overlap submittedDate gate for C1--C5",
            "ID-keyed comparison with the immediately prior 2026-08-05 Paper I gate",
            "exact-ID version and updated-metadata checks for arXiv:2607.26672 and "
            "arXiv:2603.25503",
        ],
        "claim_boundary": (
            "This artifact-specific 2026-08-06 gate establishes only that the archived "
            "expanded submittedDate response begins no later than and ends no earlier than the "
            "prior gate, has the same versioned IDs, normalized title/abstract metadata, and "
            "C1--C5 screening decisions when compared by ID, and that the separately queried "
            "Xu and Srivastava--Surya records remain at v1. It does not establish exhaustive "
            "literature coverage, novelty, priority, absence, or general coverage of updates "
            "to records submitted before the window. The changed arXiv API response order is "
            "not a materiality signal. A future gate requires a new date-stamped archive, "
            "source ID, and window-aware normalizer. "
            + OWNER_ONLY_AUTHORIZATION_FRAGMENT
        ),
    }


def _record_by_id(path: Path, collection_key: str) -> dict[str, Any]:
    document = _load_json(path)
    matches = [record for record in document[collection_key] if record.get("id") == SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {SOURCE_ID} record in {path}")
    return matches[0]


def _validate_reference_bindings(ledger: dict[str, Any], ledger_bytes: bytes) -> None:
    expected = source_record(ledger, ledger_bytes)
    source = _record_by_id(SOURCES, "sources")
    archived = _record_by_id(ARCHIVE_MANIFEST, "records")
    for label, record in (("source catalog", source), ("archive manifest", archived)):
        for field in expected:
            if record.get(field) != expected[field]:
                raise ValueError(f"{label} {field} binding drifted")
    if not (
        archived.get("archive_status") == "LOCAL_ARTIFACTS"
        and archived.get("sha256") is None
        and archived.get("bytes") is None
        and archived.get("pages") is None
        and archived.get("text_file") is None
    ):
        raise ValueError("archive manifest non-PDF dataset archive status drifted")


def _print_source_record() -> None:
    ledger = build_ledger()
    output = ROOT / OUTPUT_LEDGER
    if output.exists():
        ledger_bytes = output.read_bytes()
    else:
        ledger_bytes = _canonical_bytes(ledger)
    print(json.dumps(source_record(ledger, ledger_bytes), ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fetch", action="store_true", help="archive new official API responses once"
    )
    parser.add_argument("--write", action="store_true", help="write the normalized ledger")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify artifacts, ledger, and source/manifest bindings",
    )
    parser.add_argument(
        "--print-source-record",
        action="store_true",
        help="print the exact source-catalog record to add with apply_patch",
    )
    args = parser.parse_args()
    if not any((args.fetch, args.write, args.check, args.print_source_record)):
        parser.error("choose at least one of --fetch, --write, --check, or --print-source-record")
    if args.fetch:
        fetch()
    if args.write:
        ledger = build_ledger()
        output = ROOT / OUTPUT_LEDGER
        if output.exists():
            raise FileExistsError(f"refusing to overwrite normalized ledger: {OUTPUT_LEDGER}")
        output.write_bytes(_canonical_bytes(ledger))
        print(f"Wrote normalized Paper I Zenodo-gate ledger: {OUTPUT_LEDGER}")
    if args.print_source_record:
        _print_source_record()
    if args.check:
        ledger = build_ledger()
        expected = _canonical_bytes(ledger)
        output = ROOT / OUTPUT_LEDGER
        if not output.exists():
            print(f"missing Zenodo-gate ledger: {output}", file=sys.stderr)
            return 1
        if output.read_bytes() != expected:
            print(f"Zenodo-gate ledger drift: {output}", file=sys.stderr)
            return 1
        _validate_reference_bindings(ledger, expected)
        print(f"OK: normalized Paper I Zenodo-gate ledger ({OUTPUT_LEDGER})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
