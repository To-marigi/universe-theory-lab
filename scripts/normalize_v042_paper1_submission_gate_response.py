"""Normalize and verify the 2026-08-05T11:31Z Paper I submission-gate snapshot.

The committed 2026-08-05 literature-delta normalizer remains the screening
authority.  This thin wrapper points that offline normalizer at a newly
archived full-overlap response, compares it to the committed baseline by
arXiv ID rather than unstable API response order, and binds two exact-ID
version checks retained in a separate Atom response.

This is an artifact-specific checker, not a reusable future retriever.  A
later submission requires a new source ID, raw response, and window-aware
normalizer proving start <= the baseline start, end >= the baseline end, and a
monotone feed cutoff.  Replacing this raw response with a later feed fails.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_NORMALIZER_PATH = ROOT / "scripts/normalize_v042_paper1_arxiv_delta_response.py"
BASELINE_LEDGER = Path("references/papers/2026-08-05_paper1_arxiv_delta_query_normalized.json")
RAW_RESPONSE = Path(
    "references/papers/2026-08-05_paper1_submission_gate_arxiv_full_overlap_atom.xml"
)
EXACT_ID_RESPONSE = Path(
    "references/papers/2026-08-05_paper1_submission_gate_arxiv_exact_ids_atom.xml"
)
OUTPUT_LEDGER = Path("references/papers/2026-08-05_paper1_submission_gate_arxiv_normalized.json")
SOURCES = Path("references/sources.json")
ARCHIVE_MANIFEST = Path("references/manifest.json")
SOURCE_ID = "arXiv:PaperI-submission-gate-recheck-2026-08-05T113124Z"
BASELINE_SOURCE_ID = "arXiv:PaperI-literature-delta-query-2026-08-05"
GATE_STATUS = (
    "CLOSED_NO_MATERIAL_DELTA_WITHIN_SUBMISSION_GATE_FULL_OVERLAP_AS_OF_2026-08-05T11:31:24Z"
)
SNAPSHOT_FEED_UPDATED_UTC = "2026-08-05T11:31:24Z"
NORMALIZER_PATH = "scripts/normalize_v042_paper1_submission_gate_response.py"
CHECK_COMMAND = (
    ".venv\\Scripts\\python.exe scripts/normalize_v042_paper1_submission_gate_response.py --check"
)
FULL_OVERLAP_REQUEST_URL = (
    "https://arxiv.org/api/query?search_query=submittedDate:%22202607311500+TO+"
    "202608052359%22+AND+(cat:gr-qc+OR+(cat:quant-ph+OR+(cat:math-ph+OR+"
    "(cat:math.OA+OR+(cat:math.RA+OR+(cat:math.AC+OR+(cat:math.FA+OR+"
    "cat:math.CO)))))))&start=0&max_results=2000&id_list="
)
EXACT_ID_REQUEST_URL = (
    "https://arxiv.org/api/query?id_list=2607.26672,2603.25503&start=0&max_results=2"
)
FULL_OVERLAP_REQUEST_STARTED_UTC = "2026-08-05T11:31:20.124Z"
FULL_OVERLAP_RETRIEVED_UTC = "2026-08-05T11:31:26.068Z"
EXACT_ID_REQUEST_STARTED_UTC = "2026-08-05T11:31:39.649Z"
EXACT_ID_RETRIEVED_UTC = "2026-08-05T11:31:40.486Z"
EXPECTED_EXACT_IDS = ["2607.26672", "2603.25503"]
EXPECTED_EXACT_VERSIONS = {"2607.26672": "v1", "2603.25503": "v1"}
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
QUERY_SEMANTIC_KEYS = [
    "field",
    "window_start_compact_utc",
    "window_end_compact_utc",
    "categories",
    "start",
    "max_results",
    "id_list",
    "window_start_utc",
    "window_end_minute_utc",
    "window_end_exclusive_utc",
    "self_link",
]
VERSIONED_ID_RE = re.compile(r"^(?P<base>[0-9]{4}\.[0-9]{4,5})(?P<version>v[1-9][0-9]*)$")


class SubmissionGateReviewRequired(ValueError):
    """An unclassified literature change prevents automatic gate closure."""


def _load_baseline_normalizer() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "v042_paper1_literature_delta_normalizer",
        BASELINE_NORMALIZER_PATH,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load baseline normalizer: {BASELINE_NORMALIZER_PATH}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


BASELINE_NORMALIZER = _load_baseline_normalizer()
ATOM = BASELINE_NORMALIZER.ATOM
OPENSEARCH = BASELINE_NORMALIZER.OPENSEARCH
NS = BASELINE_NORMALIZER.NS


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _required_text(parent: ET.Element, path: str, *, label: str) -> str:
    value = parent.findtext(path, namespaces=NS)
    if value is None or not value.strip():
        raise ValueError(f"missing {label}")
    return value.strip()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _parse_exact_query(parameters: str, *, label: str) -> dict[str, Any]:
    parsed = parse_qs(parameters, keep_blank_values=True, strict_parsing=True)
    required = {"search_query", "id_list", "start", "max_results"}
    if set(parsed) != required or any(len(values) != 1 for values in parsed.values()):
        raise ValueError(f"invalid {label} exact-ID query parameters")
    if parsed["search_query"] != [""]:
        raise ValueError(f"{label} exact-ID query has a nonempty search_query")
    ids = parsed["id_list"][0].split(",")
    if ids != EXPECTED_EXACT_IDS:
        raise ValueError(f"{label} exact-ID list drifted: {ids!r}")
    try:
        start = int(parsed["start"][0])
        max_results = int(parsed["max_results"][0])
    except ValueError as exc:
        raise ValueError(f"invalid {label} exact-ID pagination") from exc
    if start != 0 or max_results != len(EXPECTED_EXACT_IDS):
        raise ValueError(f"{label} exact-ID pagination drifted")
    return {
        "search_query": "",
        "id_list": ids,
        "start": start,
        "max_results": max_results,
    }


def _validate_exact_id_records(
    records: list[dict[str, Any]],
    catalog: dict[str, Any],
) -> None:
    versions = {record["base_id"]: record["version"] for record in records}
    if versions != EXPECTED_EXACT_VERSIONS:
        raise SubmissionGateReviewRequired(
            f"SOL_REVIEW_REQUIRED_EXACT_ID_VERSION_UPDATE: tracked versions changed: {versions!r}"
        )

    for record in records:
        source_id = f"arXiv:{record['arxiv_id']}"
        matches = [source for source in catalog["sources"] if source.get("id") == source_id]
        if len(matches) != 1:
            raise SubmissionGateReviewRequired(
                f"SOL_REVIEW_REQUIRED_EXACT_ID_METADATA_UPDATE: missing source {source_id}"
            )
        source = matches[0]
        expected_fields = {
            "title": record["title"],
            "authors": record["authors"],
            "first_submitted": record["published_utc"],
            "last_revised": record["updated_utc"],
        }
        changed_fields = sorted(
            key for key, value in expected_fields.items() if source.get(key) != value
        )
        if changed_fields:
            raise SubmissionGateReviewRequired(
                "SOL_REVIEW_REQUIRED_EXACT_ID_METADATA_UPDATE: "
                f"{source_id} changed fields={changed_fields}"
            )


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
        base_id = match.group("base")
        version = match.group("version")
        summary = BASELINE_NORMALIZER._normalized_text(
            _required_text(entry, "atom:summary", label=f"{versioned_id} abstract")
        )
        records.append(
            {
                "arxiv_id": versioned_id,
                "base_id": base_id,
                "version": version,
                "updated_utc": _required_text(
                    entry, "atom:updated", label=f"{versioned_id} updated timestamp"
                ),
                "published_utc": _required_text(
                    entry, "atom:published", label=f"{versioned_id} published timestamp"
                ),
                "title": BASELINE_NORMALIZER._normalized_text(
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
    _validate_exact_id_records(records, catalog)

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


def _metadata_without_order_or_screening(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in record.items() if key not in {"response_index", "screening"}
    }


def _record_map(records: list[dict[str, Any]], transform: Any) -> dict[str, Any]:
    result = {record["arxiv_id"]: transform(record) for record in records}
    if len(result) != len(records):
        raise ValueError("duplicate arXiv ID in normalized response")
    return result


def _version_pair_diagnostics(
    baseline_records: list[dict[str, Any]],
    submission_gate_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def versions(records: list[dict[str, Any]]) -> dict[str, list[str]]:
        result: dict[str, set[str]] = {}
        for record in records:
            result.setdefault(record["base_id"], set()).add(record["version"])
        return {base_id: sorted(values) for base_id, values in result.items()}

    baseline = versions(baseline_records)
    submission_gate = versions(submission_gate_records)
    return [
        {
            "base_id": base_id,
            "baseline_versions": baseline.get(base_id, []),
            "submission_gate_versions": submission_gate.get(base_id, []),
        }
        for base_id in sorted(set(baseline) | set(submission_gate))
        if baseline.get(base_id, []) != submission_gate.get(base_id, [])
    ]


def _compare_full_overlap_or_require_review(
    baseline: dict[str, Any],
    submission_gate: dict[str, Any],
) -> dict[str, Any]:
    baseline_records = baseline["records"]
    records = submission_gate["records"]
    baseline_metadata = _record_map(baseline_records, _metadata_without_order_or_screening)
    metadata = _record_map(records, _metadata_without_order_or_screening)
    baseline_screening = _record_map(baseline_records, lambda record: record["screening"])
    screening = _record_map(records, lambda record: record["screening"])
    baseline_ids = set(baseline_metadata)
    ids = set(metadata)

    added_ids = sorted(ids - baseline_ids)
    missing_ids = sorted(baseline_ids - ids)
    metadata_changed_ids = sorted(
        arxiv_id
        for arxiv_id in ids & baseline_ids
        if metadata[arxiv_id] != baseline_metadata[arxiv_id]
    )
    screening_changed_ids = sorted(
        arxiv_id
        for arxiv_id in ids & baseline_ids
        if screening[arxiv_id] != baseline_screening[arxiv_id]
    )
    version_pair_diagnostics = _version_pair_diagnostics(baseline_records, records)
    baseline_positions = {
        record["arxiv_id"]: record["response_index"] for record in baseline_records
    }
    positions = {record["arxiv_id"]: record["response_index"] for record in records}
    moved_ids = sorted(
        arxiv_id
        for arxiv_id in ids & baseline_ids
        if positions[arxiv_id] != baseline_positions[arxiv_id]
    )
    baseline_query = baseline["effective_response_query"]
    query = submission_gate["effective_response_query"]
    query_semantics_equal = all(baseline_query[key] == query[key] for key in QUERY_SEMANTIC_KEYS)
    if not query_semantics_equal:
        raise SubmissionGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: full-overlap query semantics changed"
        )
    if added_ids or missing_ids or metadata_changed_ids or screening_changed_ids:
        raise SubmissionGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: submission-gate literature change "
            "must not be auto-classified as material or nonmaterial: "
            f"added={added_ids}, missing={missing_ids}, metadata={metadata_changed_ids}, "
            f"screening={screening_changed_ids}, version_pairs={version_pair_diagnostics}"
        )

    return {
        "query_semantics_equal": query_semantics_equal,
        "feed_title_text_equal": baseline_query["feed_title"] == query["feed_title"],
        "baseline_response_entry_count": len(baseline_records),
        "submission_gate_response_entry_count": len(records),
        "added_ids": added_ids,
        "missing_ids": missing_ids,
        "metadata_changed_ids": metadata_changed_ids,
        "screening_changed_ids": screening_changed_ids,
        "version_pair_diagnostics": version_pair_diagnostics,
        "response_order_equal": not moved_ids,
        "response_order_moved_record_count": len(moved_ids),
        "response_order_not_a_materiality_contract": True,
        "metadata_by_id_sha256": BASELINE_NORMALIZER._compact_digest(metadata),
        "screening_by_id_sha256": BASELINE_NORMALIZER._compact_digest(screening),
    }


def _configure_baseline_normalizer() -> None:
    normalizer = cast(Any, BASELINE_NORMALIZER)
    normalizer.RAW_RESPONSE = RAW_RESPONSE
    normalizer.OUTPUT_LEDGER = OUTPUT_LEDGER
    normalizer.SOURCE_ID = SOURCE_ID
    normalizer.GATE_STATUS = GATE_STATUS


def build_ledger() -> dict[str, Any]:
    baseline = _load_json(BASELINE_LEDGER)
    _configure_baseline_normalizer()
    try:
        ledger = BASELINE_NORMALIZER.build_ledger()
    except ValueError as exc:
        raise SubmissionGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: baseline normalizer failed closed"
        ) from exc
    feed_updated = ledger["raw_response"]["feed_updated_utc"]
    if feed_updated != SNAPSHOT_FEED_UPDATED_UTC:
        raise ValueError(
            "artifact-specific submission-gate feed cutoff changed; create a new source ID, "
            "raw response, and window-aware normalizer"
        )
    expected_status = (
        f"CLOSED_NO_MATERIAL_DELTA_WITHIN_SUBMISSION_GATE_FULL_OVERLAP_AS_OF_{feed_updated}"
    )
    if ledger["gate_status"] != expected_status:
        raise ValueError("submission-gate status is not derived from the archived feed cutoff")

    records = ledger["records"]
    comparison = _compare_full_overlap_or_require_review(baseline, ledger)

    try:
        exact_ids = _exact_id_snapshot()
    except SubmissionGateReviewRequired:
        raise
    except ValueError as exc:
        raise SubmissionGateReviewRequired(
            "SOL_REVIEW_REQUIRED_EXACT_ID_UPDATE: tracked version or metadata changed"
        ) from exc
    exact_versions = {record["base_id"]: record["version"] for record in exact_ids["records"]}
    candidate_ids = sorted(ledger["screening"]["inspected_candidate_ids"])
    baseline_candidates = sorted(baseline["screening"]["inspected_candidate_ids"])
    if candidate_ids != baseline_candidates:
        raise ValueError("submission-gate candidate membership drifted")

    ledger["schema_version"] = "1.1"
    ledger["coverage_boundary"] = {
        "archived_submitted_date_snapshot_only": True,
        "general_pre_window_version_updates_covered": False,
        "tracked_exact_id_version_checks_archived_with_gate": [
            "arXiv:2607.26672",
            "arXiv:2603.25503",
        ],
        "minimum_pre_submission_contract": [
            "archive and rescreen a full-overlap submittedDate response",
            "repeat exact-ID version checks for arXiv:2607.26672 and arXiv:2603.25503",
            "compare all normalized metadata and screening decisions to the baseline by ID",
        ],
        "minimum_pre_submission_contract_status": "SATISFIED_BY_THIS_ARCHIVE",
    }
    ledger["reconciliation"] = {
        "status": "FULL_OVERLAP_BASELINE_RECHECK_COMPLETED",
        "baseline_source_id": BASELINE_SOURCE_ID,
        "query_semantics_equal": True,
        "id_set_equal": True,
        "metadata_equal_by_id": True,
        "screening_decisions_equal_by_id": True,
        "response_order_equal": comparison["response_order_equal"],
        "response_order_not_a_materiality_contract": True,
        "materiality_reassessment_status": "COMPLETED_NO_MATERIAL_DELTA",
    }
    ledger["submission_gate_recheck"] = {
        "authorization_boundary": dict(AUTHORIZATION_BOUNDARY),
        "baseline": {
            "source_id": BASELINE_SOURCE_ID,
            "normalized_ledger_path": BASELINE_LEDGER.as_posix(),
            "raw_response_path": baseline["raw_response"]["path"],
            "raw_response_sha256": baseline["raw_response"]["sha256"],
            "feed_updated_utc": baseline["raw_response"]["feed_updated_utc"],
            "response_entry_count": baseline["response_entry_count"],
        },
        "retrievals": {
            "full_overlap": {
                "requested_url": FULL_OVERLAP_REQUEST_URL,
                "request_started_utc": FULL_OVERLAP_REQUEST_STARTED_UTC,
                "retrieved_utc": FULL_OVERLAP_RETRIEVED_UTC,
                "http_status": 200,
            },
            "exact_ids": {
                "requested_url": EXACT_ID_REQUEST_URL,
                "request_started_utc": EXACT_ID_REQUEST_STARTED_UTC,
                "retrieved_utc": EXACT_ID_RETRIEVED_UTC,
                "http_status": 200,
            },
        },
        "full_overlap_comparison": comparison,
        "title_abstract_rescreen": {
            "records_screened": len(records),
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
            "This gate proves only that the archived full-overlap submittedDate response "
            "has the same ID set, normalized title/abstract metadata, and C1--C5 screening "
            "decisions as the committed baseline, and that the two separately queried "
            "tracked IDs remain at v1. It does not establish exhaustive literature "
            "coverage, novelty, priority, absence, or general pre-window update coverage. "
            + OWNER_ONLY_AUTHORIZATION_FRAGMENT
        ),
    }
    return ledger


def _record_by_id(path: Path, collection_key: str) -> dict[str, Any]:
    document = _load_json(path)
    matches = [record for record in document[collection_key] if record.get("id") == SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {SOURCE_ID} record in {path}")
    return matches[0]


def _dataset_snapshot(ledger: dict[str, Any]) -> dict[str, Any]:
    recheck = ledger["submission_gate_recheck"]
    return {
        "gate_status": ledger["gate_status"],
        "full_overlap_feed_updated_utc": ledger["raw_response"]["feed_updated_utc"],
        "effective_response_query": ledger["effective_response_query"],
        "normalizer": NORMALIZER_PATH,
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
        "retrievals": recheck["retrievals"],
        "full_overlap_comparison": recheck["full_overlap_comparison"],
        "title_abstract_rescreen": recheck["title_abstract_rescreen"],
        "exact_id_checks": recheck["exact_id_checks"],
    }


def _validate_reference_bindings(ledger: dict[str, Any], ledger_bytes: bytes) -> None:
    source = _record_by_id(SOURCES, "sources")
    archived = _record_by_id(ARCHIVE_MANIFEST, "records")
    exact_raw = ledger["submission_gate_recheck"]["exact_id_checks"]["raw_response"]
    expected_artifacts = [
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
            "role": "NORMALIZED_SCREENING_LEDGER",
            "path": OUTPUT_LEDGER.relative_to("references").as_posix(),
            "media_type": "application/json",
            "sha256": f"sha256:{_sha256_bytes(ledger_bytes)}",
            "bytes": len(ledger_bytes),
        },
    ]
    expected_snapshot = _dataset_snapshot(ledger)
    for label, record in (("source catalog", source), ("archive manifest", archived)):
        if record.get("url") != ledger["effective_response_query"]["self_link"]:
            raise ValueError(f"{label} full-overlap query URL drifted")
        if record.get("exact_id_url") != EXACT_ID_REQUEST_URL:
            raise ValueError(f"{label} exact-ID query URL drifted")
        if record.get("local_artifacts") != expected_artifacts:
            raise ValueError(f"{label} local-artifact binding drifted")
        if record.get("dataset_snapshot") != expected_snapshot:
            raise ValueError(f"{label} dataset snapshot drifted")
        if OWNER_ONLY_AUTHORIZATION_FRAGMENT not in record.get("claim_boundary", ""):
            raise ValueError(f"{label} owner-only authorization boundary drifted")
    if not (
        archived.get("archive_status") == "LOCAL_ARTIFACTS"
        and archived.get("sha256") is None
        and archived.get("bytes") is None
        and archived.get("pages") is None
        and archived.get("text_file") is None
    ):
        raise ValueError("submission-gate dataset must retain separate artifact hashes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless the archived responses, ledger, and registry bindings agree",
    )
    args = parser.parse_args()
    expected = BASELINE_NORMALIZER._canonical_bytes(build_ledger())
    output = ROOT / OUTPUT_LEDGER
    if args.check:
        if not output.exists():
            print(f"missing submission-gate ledger: {output}", file=sys.stderr)
            return 1
        if output.read_bytes() != expected:
            print(f"submission-gate ledger drift: {output}", file=sys.stderr)
            return 1
        _validate_reference_bindings(json.loads(expected), expected)
        print(f"OK: normalized Paper I submission-gate ledger ({output})")
        return 0
    output.write_bytes(expected)
    print(f"Wrote normalized Paper I submission-gate ledger: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
