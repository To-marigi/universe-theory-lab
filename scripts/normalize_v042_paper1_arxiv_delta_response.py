"""Normalize the archived Paper I arXiv Atom response into an ID ledger.

This script is deliberately offline.  It never repeats the network request; it
only authenticates and normalizes the versioned response retained in the
reference archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
RAW_RESPONSE = Path("references/papers/2026-08-05_paper1_arxiv_delta_query_atom.xml")
OUTPUT_LEDGER = Path("references/papers/2026-08-05_paper1_arxiv_delta_query_normalized.json")
SOURCES = Path("references/sources.json")
ARCHIVE_MANIFEST = Path("references/manifest.json")
SOURCE_ID = "arXiv:PaperI-literature-delta-query-2026-08-05"
GATE_STATUS = (
    "CLOSED_NO_MATERIAL_DELTA_WITHIN_ARCHIVED_SUBMITTEDDATE_SCOPE_AS_OF_2026-08-05T04:52:45Z"
)
QUERY_FIELD = "submittedDate"
QUERY_WINDOW_START = "202607311500"
QUERY_WINDOW_END = "202608052359"
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
QUERY_START = 0
QUERY_MAX_RESULTS = 2000
HISTORICAL_REPORTED_COUNT = 524

EXACT_SCREENING_TERMS = [
    "bell causality",
    "quantum sequential growth",
    "cpobc",
    "relational quantum causal",
    "statewise commutativity",
    "on-state commutativity",
    "operator covariance",
    "martingale residual",
    "reachable-state",
    "reachable state",
    "separating vector",
    "simultaneous triangularization",
    "common invariant subspace",
    "non-self-adjoint nonsingular",
    "causal set",
    "causet",
]
COMPOUND_SCREENING_RULES = [
    (
        "causal AND (sequential OR growth OR operator OR covariance OR process OR Bell "
        "OR quantum gravity)"
    ),
    (
        "(commutat* OR noncommutat* OR non-commutat*) AND (matrix OR matrices OR "
        "operator OR state OR representation OR triangular OR invariant subspace)"
    ),
    "triangular AND (matrix OR matrices OR operator OR representation OR simultaneous)",
    "invariant subspace AND (matrix OR matrices OR operator)",
    "Bell AND (causal OR nonlocal*)",
]

# Every rule-triggered record in the archived 556-entry response was reread at
# title/abstract level.  The exact ID set is asserted below so that a changed
# response or changed screening rule cannot silently inherit these judgments.
INSPECTED_NONMATERIAL_RATIONALES = {
    "2608.03897v1": (
        "Bounds the Frobenius norm of a q-deformed commutator for generic complex "
        "matrices; it contains no CPOBC relations, growth semantics, or promotion theorem."
    ),
    "2608.03825v1": (
        "Studies CNOT circuit complexity using unitriangular matrices over GF(2), not "
        "operator-valued causal-set growth or C1--C5."
    ),
    "2608.03755v1": (
        "Uses multi-copy commutation symmetries to witness non-Gaussian quantum states; "
        "it does not study CPOBC, reachable-state MSR, or finite growth rigidity."
    ),
    "2608.03552v1": (
        "Reports an optical quantum-causal-network nonclassicality experiment; the "
        "Bell/nonlocality setting is unrelated to causal-set CPOBC matrix relations."
    ),
    "2608.03526v1": (
        "Derives spectral approximation bounds for finite-range operators using a "
        "localisation commutator estimate, with no CPOBC or state/operator semantic claim."
    ),
    "2608.03427v1": (
        "Develops Hom-Poisson superalgebra structures; super-commutativity terminology "
        "does not overlap the finite CPOBC representation problem."
    ),
    "2608.03334v1": (
        "Studies nearly invariant subspaces for weighted truncated Toeplitz operators; "
        "it has no causal-growth relation system or C1--C5 theorem."
    ),
    "2608.02861v1": (
        "Introduces a noncommutative transform for path signatures and topological "
        "recursion, not CPOBC transition matrices or statewise promotion."
    ),
    "2608.02473v1": (
        "The triangular match refers to a triangular-lattice tensor-network simulation; "
        "it is not matrix triangularization or causal-set growth."
    ),
    "2608.02459v1": (
        "Uses causal tempered distributions in Liouville Brownian-motion response "
        "calculus; it contains no causal-set or CPOBC semantics."
    ),
    "2608.02262v1": (
        "Uses path-ordered operator calculus and graded commutators in supersymmetric "
        "Yang--Mills loop equations, unrelated to CPOBC or C1--C5."
    ),
    "2608.01831v1": (
        "Studies SLD commutator compatibility in multiparameter quantum sensing, not "
        "growth-transition commutativity or statewise-to-operator recovery."
    ),
    "2608.01689v1": (
        "Concerns harmonic-analysis commutators on Orlicz-Hardy spaces; it is outside "
        "finite matrix CPOBC and causal-set growth."
    ),
    "2608.01650v1": (
        "Proposes a commutative-ring field model for an emergent coordinate continuum; "
        "it does not formulate the CPOBC relations or any C1--C5 result."
    ),
    "2608.01485v1": (
        "Constructs antitriangular matrices from finite-field representation theory; "
        "the matrices are unrelated to CPOBC transition operators."
    ),
    "2608.01424v1": (
        "Determines noncommutative Bohnenblust--Hille growth for Pauli expansions; it "
        "does not address Bell-causal sequential growth or statewise semantics."
    ),
    "2608.01376v1": (
        "Develops noncommutative Hom-Poisson superalgebras; the algebraic terminology "
        "does not overlap the CPOBC presentation or claims C1--C5."
    ),
    "2608.01317v1": (
        "Gives a Bell-functional separation of qubit measurement models and a "
        "noncommutative sum-of-squares certificate, not a CPOBC growth result."
    ),
    "2608.01293v1": (
        "Uses commuting deformation operators and Lax commutators for integrable PDEs; "
        "it is unrelated to causal-set transitions and C1--C5."
    ),
    "2608.01114v1": (
        "Optimizes quantum-metrology strategies with indefinite causal order; it does "
        "not study causal-set sequential growth or the CPOBC matrix equations."
    ),
    "2608.01110v1": (
        "Builds a spectral triple for a fuzzy torus using commutators; it contains no "
        "CPOBC, reachable-state MSR, or promotion theorem."
    ),
    "2608.00297v1": (
        "The causal-envelope language concerns cosmological black-hole growth and "
        "entropy, not causal-set operator growth."
    ),
    "2608.00159v1": (
        "The causal-future language concerns de Sitter tunnelling geometry, not CPOBC "
        "transition relations or state/operator semantics."
    ),
}

ATOM = "http://www.w3.org/2005/Atom"
ARXIV = "http://arxiv.org/schemas/atom"
OPENSEARCH = "http://a9.com/-/spec/opensearch/1.1/"
NS = {"atom": ATOM, "arxiv": ARXIV, "opensearch": OPENSEARCH}
ARXIV_VERSION_RE = re.compile(r"^(?P<base>.+)v(?P<version>[1-9][0-9]*)$")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def _compact_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return _sha256_bytes(payload)


def _normalized_text(value: str | None) -> str:
    return " ".join((value or "").split())


def _parse_utc(value: str, *, label: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError(f"{label} is not an explicit UTC timestamp: {value!r}")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError(f"{label} did not parse as UTC: {value!r}")
    return parsed


def _required_text(parent: ET.Element, path: str, *, label: str) -> str:
    value = parent.findtext(path, namespaces=NS)
    if value is None or not value.strip():
        raise ValueError(f"missing {label}")
    return value.strip()


def _compact_minute_to_utc(value: str, *, label: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y%m%d%H%M").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value!r}") from exc


def _utc_text(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_search_expression(expression: str, *, label: str) -> dict[str, Any]:
    match = re.fullmatch(
        r'(?P<field>[A-Za-z][A-Za-z0-9]*):"(?P<start>[0-9]{12}) TO '
        r'(?P<end>[0-9]{12})" AND (?P<categories>.+)',
        expression,
    )
    if match is None:
        raise ValueError(f"invalid {label} search expression: {expression!r}")
    category_expression = match.group("categories")
    categories = re.findall(r"cat:([A-Za-z0-9.-]+)", category_expression)
    residue = re.sub(r"cat:[A-Za-z0-9.-]+", "", category_expression)
    residue = re.sub(r"\bOR\b", "", residue)
    residue = re.sub(r"[()\s]", "", residue)
    if residue or not categories or len(categories) != len(set(categories)):
        raise ValueError(f"invalid {label} category expression: {category_expression!r}")
    return {
        "field": match.group("field"),
        "window_start_compact_utc": match.group("start"),
        "window_end_compact_utc": match.group("end"),
        "categories": categories,
    }


def _parse_query_parameters(parameters: str, *, label: str) -> dict[str, Any]:
    parsed = parse_qs(parameters, keep_blank_values=True, strict_parsing=True)
    required_keys = {"search_query", "id_list", "start", "max_results"}
    if set(parsed) != required_keys or any(len(values) != 1 for values in parsed.values()):
        raise ValueError(f"invalid {label} query parameters")
    if parsed["id_list"] != [""]:
        raise ValueError(f"{label} id_list is not empty")
    try:
        start = int(parsed["start"][0])
        max_results = int(parsed["max_results"][0])
    except ValueError as exc:
        raise ValueError(f"invalid {label} pagination") from exc
    return {
        **_parse_search_expression(parsed["search_query"][0], label=label),
        "start": start,
        "max_results": max_results,
        "id_list": [],
    }


def _effective_response_query(root: ET.Element) -> dict[str, Any]:
    title = _required_text(root, "atom:title", label="feed query title")
    title_prefix = "arXiv Query: "
    if not title.startswith(title_prefix):
        raise ValueError(f"unexpected feed query title: {title!r}")
    title_query = _parse_query_parameters(title.removeprefix(title_prefix), label="feed title")

    links = [
        link for link in root.findall("atom:link", NS) if link.get("type") == "application/atom+xml"
    ]
    if len(links) != 1 or set(links[0].attrib) != {"href", "type"}:
        raise ValueError("expected exactly one unambiguous Atom response query link")
    self_link = links[0].get("href")
    if not isinstance(self_link, str) or not self_link:
        raise ValueError("Atom response query link has no href")
    parsed_url = urlparse(self_link)
    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc != "arxiv.org"
        or parsed_url.path != "/api/query"
        or parsed_url.fragment
    ):
        raise ValueError(f"unexpected Atom response query URL: {self_link!r}")
    link_query = _parse_query_parameters(parsed_url.query, label="feed link")

    expected = {
        "field": QUERY_FIELD,
        "window_start_compact_utc": QUERY_WINDOW_START,
        "window_end_compact_utc": QUERY_WINDOW_END,
        "categories": QUERY_CATEGORIES,
        "start": QUERY_START,
        "max_results": QUERY_MAX_RESULTS,
        "id_list": [],
    }
    if title_query != expected:
        raise ValueError(f"feed title query contract drifted: {title_query!r}")
    if link_query != expected:
        raise ValueError(f"feed link query contract drifted: {link_query!r}")

    window_start = _compact_minute_to_utc(QUERY_WINDOW_START, label="submittedDate window start")
    window_end_minute = _compact_minute_to_utc(QUERY_WINDOW_END, label="submittedDate window end")
    return {
        "authority": "ARCHIVED_ATOM_FEED_TITLE_AND_QUERY_LINK",
        **expected,
        "window_start_utc": _utc_text(window_start),
        "window_end_minute_utc": _utc_text(window_end_minute),
        "window_end_exclusive_utc": _utc_text(window_end_minute + timedelta(minutes=1)),
        "feed_title": title,
        "self_link": self_link,
    }


def _record_by_id(path: Path, collection_key: str) -> dict[str, Any]:
    document = json.loads((ROOT / path).read_text(encoding="utf-8"))
    matches = [record for record in document[collection_key] if record.get("id") == SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {SOURCE_ID} record in {path}")
    return matches[0]


def _source_query_url() -> str:
    url = _record_by_id(SOURCES, "sources").get("url")
    if not isinstance(url, str) or not url:
        raise ValueError(f"source record {SOURCE_ID} has no exact query URL")
    return url


def _validate_reference_bindings(ledger: dict[str, Any], ledger_bytes: bytes) -> None:
    source = _record_by_id(SOURCES, "sources")
    archived = _record_by_id(ARCHIVE_MANIFEST, "records")
    effective_query = ledger["effective_response_query"]
    expected_artifacts = [
        {
            "role": "RAW_API_RESPONSE",
            "path": RAW_RESPONSE.relative_to("references").as_posix(),
            "media_type": "application/atom+xml",
            "sha256": f"sha256:{ledger['raw_response']['sha256']}",
            "bytes": ledger["raw_response"]["bytes"],
        },
        {
            "role": "NORMALIZED_SCREENING_LEDGER",
            "path": OUTPUT_LEDGER.relative_to("references").as_posix(),
            "media_type": "application/json",
            "sha256": f"sha256:{_sha256_bytes(ledger_bytes)}",
            "bytes": len(ledger_bytes),
        },
    ]
    expected_snapshot = {
        "gate_status": ledger["gate_status"],
        "feed_updated_utc": ledger["raw_response"]["feed_updated_utc"],
        "effective_response_query": effective_query,
        "normalizer": "scripts/normalize_v042_paper1_arxiv_delta_response.py",
        "check_command": (
            ".venv\\Scripts\\python.exe "
            "scripts/normalize_v042_paper1_arxiv_delta_response.py --check"
        ),
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
    }
    expected_history = {
        "reported_screened_record_count": HISTORICAL_REPORTED_COUNT,
        "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
        "query_provenance_known": False,
        "membership_known": False,
        "comparison_to_archived_556_authorized": False,
    }
    if _source_query_url() != effective_query["self_link"]:
        raise ValueError("reference source URL is not the archived effective query link")
    if archived.get("url") != effective_query["self_link"]:
        raise ValueError("reference archive URL is not the archived effective query link")
    if source.get("local_artifacts") != expected_artifacts:
        raise ValueError("reference source catalog local-artifact binding drifted")
    if archived.get("local_artifacts") != expected_artifacts:
        raise ValueError("reference archive manifest local-artifact binding drifted")
    if source.get("dataset_snapshot") != expected_snapshot:
        raise ValueError("reference source catalog dataset snapshot drifted")
    if archived.get("dataset_snapshot") != expected_snapshot:
        raise ValueError("reference archive manifest dataset snapshot drifted")
    if source.get("historical_unarchived_observation") != expected_history:
        raise ValueError("reference source catalog historical boundary drifted")
    if archived.get("historical_unarchived_observation") != expected_history:
        raise ValueError("reference archive manifest historical boundary drifted")
    if not (
        archived.get("archive_status") == "LOCAL_ARTIFACTS"
        and archived.get("sha256") is None
        and archived.get("bytes") is None
        and archived.get("pages") is None
        and archived.get("text_file") is None
    ):
        raise ValueError("non-PDF dataset must retain separate hash fields")


def _screening_rule_matches(title: str, summary: str) -> list[str]:
    text = f"{title} {summary}".lower()
    matches = [f"exact:{term}" for term in EXACT_SCREENING_TERMS if term in text]
    if "causal" in text and any(
        term in text
        for term in (
            "sequential",
            "growth",
            "operator",
            "covarian",
            "process",
            "bell",
            "quantum gravity",
        )
    ):
        matches.append("compound:causal")
    if any(term in text for term in ("commutat", "noncommut", "non-commut")) and any(
        term in text
        for term in (
            "matrix",
            "matrices",
            "operator",
            "state",
            "representation",
            "triangular",
            "invariant subspace",
        )
    ):
        matches.append("compound:commutativity")
    if "triangular" in text and any(
        term in text
        for term in ("matrix", "matrices", "operator", "representation", "simultaneous")
    ):
        matches.append("compound:triangular")
    if "invariant subspace" in text and any(
        term in text for term in ("matrix", "matrices", "operator")
    ):
        matches.append("compound:invariant-subspace")
    if "bell" in text and any(term in text for term in ("causal", "nonlocal")):
        matches.append("compound:bell-causal")
    return sorted(set(matches))


def build_ledger() -> dict[str, Any]:
    raw_path = ROOT / RAW_RESPONSE
    raw = raw_path.read_bytes()
    root = ET.fromstring(raw)
    if root.tag != f"{{{ATOM}}}feed":
        raise ValueError(f"unexpected Atom root tag: {root.tag}")

    effective_query = _effective_response_query(root)
    feed_updated = _required_text(root, "atom:updated", label="feed updated timestamp")
    feed_updated_at = _parse_utc(feed_updated, label="feed updated timestamp")
    total_results = int(_required_text(root, "opensearch:totalResults", label="totalResults"))
    start_index = int(_required_text(root, "opensearch:startIndex", label="startIndex"))
    items_per_page = int(_required_text(root, "opensearch:itemsPerPage", label="itemsPerPage"))
    if start_index != effective_query["start"]:
        raise ValueError(f"OpenSearch startIndex does not match query: startIndex={start_index}")
    if items_per_page != effective_query["max_results"]:
        raise ValueError(
            f"OpenSearch itemsPerPage does not match query: itemsPerPage={items_per_page}"
        )

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for response_index, entry in enumerate(root.findall("atom:entry", NS)):
        id_url = _required_text(entry, "atom:id", label=f"entry {response_index} id")
        arxiv_id = id_url.rstrip("/").rsplit("/", 1)[-1]
        match = ARXIV_VERSION_RE.fullmatch(arxiv_id)
        if match is None:
            raise ValueError(f"entry {response_index} has no versioned arXiv ID: {arxiv_id}")
        if arxiv_id in seen_ids:
            raise ValueError(f"duplicate arXiv ID in response: {arxiv_id}")
        seen_ids.add(arxiv_id)

        updated = _required_text(entry, "atom:updated", label=f"entry {arxiv_id} updated timestamp")
        published = _required_text(
            entry, "atom:published", label=f"entry {arxiv_id} published timestamp"
        )
        _parse_utc(updated, label=f"entry {arxiv_id} updated timestamp")
        _parse_utc(published, label=f"entry {arxiv_id} published timestamp")
        title = _normalized_text(entry.findtext("atom:title", namespaces=NS))
        summary = _normalized_text(entry.findtext("atom:summary", namespaces=NS))
        primary = entry.find("arxiv:primary_category", NS)
        primary_category = primary.get("term") if primary is not None else None
        categories = sorted(
            {
                category.get("term", "")
                for category in entry.findall("atom:category", NS)
                if category.get("term")
            }
        )
        if primary_category not in categories:
            raise ValueError(f"entry {arxiv_id} primary category is absent from its category set")
        authors = [
            _normalized_text(author.findtext("atom:name", namespaces=NS))
            for author in entry.findall("atom:author", NS)
        ]
        if not title or not summary or not authors:
            raise ValueError(f"entry {arxiv_id} lacks title, abstract, or authors")

        rule_matches = _screening_rule_matches(title, summary)
        if rule_matches:
            rationale = INSPECTED_NONMATERIAL_RATIONALES.get(arxiv_id)
            if rationale is None:
                raise ValueError(
                    f"rule-triggered record lacks an explicit materiality decision: {arxiv_id}"
                )
            screening = {
                "rule_matches": rule_matches,
                "decision": "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5",
                "decision_basis": rationale,
            }
        else:
            screening = {
                "rule_matches": [],
                "decision": "NO_REPORT_DEFINED_TARGET_RULE_MATCH",
                "decision_basis": (
                    "No exact query phrase or compound CPOBC/state-operator/finite-matrix "
                    "relevance rule matched the normalized title and abstract."
                ),
            }

        records.append(
            {
                "response_index": response_index,
                "arxiv_id": arxiv_id,
                "base_id": match.group("base"),
                "version": f"v{match.group('version')}",
                "updated_utc": updated,
                "published_utc": published,
                "primary_category": primary_category,
                "categories": categories,
                "title": title,
                "authors": authors,
                "abstract_sha256": _sha256_bytes(summary.encode("utf-8")),
                "screening": screening,
            }
        )

    if total_results != len(records):
        raise ValueError(
            f"Atom totalResults={total_results} but response contains {len(records)} entries"
        )
    if items_per_page < len(records):
        raise ValueError(
            f"response is truncated: itemsPerPage={items_per_page}, entries={len(records)}"
        )

    window_start = _parse_utc(
        effective_query["window_start_utc"], label="submittedDate window start"
    )
    window_end_exclusive = _parse_utc(
        effective_query["window_end_exclusive_utc"],
        label="submittedDate window exclusive end",
    )
    published_in_window = [
        record
        for record in records
        if window_start
        <= _parse_utc(record["published_utc"], label="record published timestamp")
        < window_end_exclusive
    ]
    published_outside_window = len(records) - len(published_in_window)
    published_at_or_before_feed = [
        record
        for record in records
        if _parse_utc(record["published_utc"], label="record published timestamp")
        <= feed_updated_at
    ]
    published_after_feed = len(records) - len(published_at_or_before_feed)
    published_values = [record["published_utc"] for record in records]
    ordered_ids = [record["arxiv_id"] for record in records]
    triggered_ids = [
        record["arxiv_id"] for record in records if record["screening"]["rule_matches"]
    ]
    expected_triggered_ids = set(INSPECTED_NONMATERIAL_RATIONALES)
    if set(triggered_ids) != expected_triggered_ids:
        missing = sorted(expected_triggered_ids - set(triggered_ids))
        unexpected = sorted(set(triggered_ids) - expected_triggered_ids)
        raise ValueError(
            f"screened candidate set drifted: missing={missing}, unexpected={unexpected}"
        )

    return {
        "schema_version": "1.0",
        "source_id": SOURCE_ID,
        "gate_status": GATE_STATUS,
        "effective_response_query": effective_query,
        "raw_response": {
            "path": RAW_RESPONSE.as_posix(),
            "sha256": _sha256_bytes(raw),
            "bytes": len(raw),
            "feed_updated_utc": feed_updated,
        },
        "opensearch": {
            "total_results": total_results,
            "start_index": start_index,
            "items_per_page": items_per_page,
        },
        "response_entry_count": len(records),
        "entries_published_in_submitted_date_window": len(published_in_window),
        "entries_published_outside_submitted_date_window": published_outside_window,
        "entries_published_at_or_before_feed_cutoff": len(published_at_or_before_feed),
        "entries_published_after_feed_cutoff": published_after_feed,
        "minimum_published_utc": min(published_values),
        "maximum_published_utc": max(published_values),
        "ordered_arxiv_ids_sha256": _compact_digest(ordered_ids),
        "records_sha256": _compact_digest(records),
        "screening": {
            "scope": "normalized Atom title and abstract for every response entry",
            "exact_terms": EXACT_SCREENING_TERMS,
            "compound_rules": COMPOUND_SCREENING_RULES,
            "decision_counts": {
                "NO_REPORT_DEFINED_TARGET_RULE_MATCH": len(records) - len(triggered_ids),
                "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": len(triggered_ids),
                "MATERIAL_DELTA_TO_C1_C5": 0,
            },
            "inspected_candidate_ids": triggered_ids,
            "material_delta_ids": [],
            "claim_boundary": (
                "This is a bounded title/abstract screen within the archived "
                "submittedDate response, not an exhaustive literature-absence, novelty, "
                "priority, or general later-version-update determination."
            ),
        },
        "coverage_boundary": {
            "archived_submitted_date_snapshot_only": True,
            "general_pre_window_version_updates_covered": False,
            "tracked_exact_id_version_checks_recorded_outside_this_ledger": [
                "arXiv:2607.26672",
                "arXiv:2603.25503",
            ],
            "minimum_pre_submission_contract": [
                "archive and rescreen a full-overlap submittedDate response",
                "repeat exact-ID version checks for arXiv:2607.26672 and arXiv:2603.25503",
                (
                    "retain general pre-window version-update coverage as an explicit "
                    "editorial decision"
                ),
            ],
        },
        "reconciliation": {
            "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
            "historical_reported_screened_record_count": HISTORICAL_REPORTED_COUNT,
            "historical_524_query_provenance_known": False,
            "historical_524_id_membership_known": False,
            "comparison_to_archived_556_authorized": False,
            "materiality_reassessment_status": "COMPLETED_ON_ARCHIVED_556_RESPONSE",
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless the tracked normalized ledger equals the archived response",
    )
    args = parser.parse_args()
    expected = _canonical_bytes(build_ledger())
    output = ROOT / OUTPUT_LEDGER
    if args.check:
        if not output.exists():
            print(f"missing normalized ledger: {output}", file=sys.stderr)
            return 1
        if output.read_bytes() != expected:
            print(f"normalized ledger drift: {output}", file=sys.stderr)
            return 1
        _validate_reference_bindings(json.loads(expected), expected)
        print(f"OK: normalized Paper I arXiv ledger ({output})")
        return 0
    output.write_bytes(expected)
    print(f"Wrote normalized Paper I arXiv ledger: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
