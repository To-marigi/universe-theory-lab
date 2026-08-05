"""Validate the proof-complete, non-frozen Paper I v0.4.2 release candidate.

The validator is deliberately read-only.  It verifies the manuscript snapshot,
its bibliography closure, and the claim/publication boundaries without
building a PDF or changing any research artifact.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from validate_v042_paper1_claim_boundary import validate_claim_boundary

from universe_lab.final_theory import (
    sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042 as bounded_scout_fixtures,
)

MANIFEST_PATH = Path("results/v0.4.2_paper1_manuscript_manifest.json")
MANUSCRIPT_ROOT = Path("paper/v0.4.2_paper1_statewise_operator")
CLAIM_LEDGER_PATH = Path("results/v0.4.2_paper1_claim_boundary.json")
EXPECTED_MANUSCRIPT_PATHS = {
    MANUSCRIPT_ROOT / "main.tex",
    MANUSCRIPT_ROOT / "REPRODUCING.md",
    MANUSCRIPT_ROOT / "references.bib",
}
WITNESS_EXTRACTOR_PATH = Path("scripts/extract_v042_paper1_witness_tables.py")
WITNESS_EXTRACTOR_SHA256 = "f71790c5ce3d7d239100981666a5327716f6c5529c3491a13c1c0d9cc46710dd"
WITNESS_RESULT_PATH = Path("results/v0.4.2_paper1_witness_tables.json")
WITNESS_RESULT_SHA256 = "7608f8f987352fd297ae4e5911a65e018700a5c187b3d60e7a0677f72e3700f7"
WITNESS_RESULT_SCHEMA = "final-theory-v042-paper1-witness-tables-v1"
WITNESS_RESULT_SEMANTIC_SHA256 = "6e3aff10dcf855617973b3b83bece809f00ef39f9568471475e58c1ab5fca542"
WITNESS_TEST_PATH = Path("tests/final_theory/test_extract_v042_paper1_witness_tables.py")
WITNESS_TEST_SHA256 = "b2825147db27a2bf0a76bd39b656835b8de7b7e4c7c4aa55a55aa02ca6617a3a"
WEAK_AUTHORITY_PATH = Path("results/v0.4_weak_d2_classification.json")
WEAK_AUTHORITY_SHA256 = "18e71f439913896fb370944c6479fc358d4d6d0d127162809ba46822ccd2fe65"
WEAK_ORACLE_PATH = Path("tests/final_theory/test_weak_d2_v04_oracle.py")
WEAK_ORACLE_SHA256 = "54c5ec91fd3af0c824b153e451caa4695036e39d3915e68e76618ee2f455b324"
OBSERVABILITY_AUTHORITY_PATH = Path("results/v0.4.2_sr2v_baseline_observability.json")
OBSERVABILITY_AUTHORITY_SHA256 = "4f57805e871c0589560669c5aa65181c29ca41cdf722420729279945770710de"
OBSERVABILITY_SCHEMA = "final-theory-v042-sr2v-baseline-observability-v1"
OBSERVABILITY_SEMANTIC_SHA256 = "73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62"
Q5_FREE_AUTHORITY_PATH = Path("results/v0.3.7_q5_free_elimination.json")
Q5_FREE_AUTHORITY_SHA256 = "4c394fd5e4b864f3bb34debee51d536b1828c0f9a0d3a64b1d09142ef3b3ff14"
Q5_FREE_SCHEMA = "final-theory-q5-free-campaign-v0.3.7"
Q5_FREE_RECORDED_SEMANTIC_SHA256 = (
    "42dcd4f095f4d9ba87478716e1ed8e3639a823b0179cebd230f00feaedc0e47a"
)
Q5_FREE_ORACLE_PATH = Path("tests/final_theory/test_q5_free_elimination_v037.py")
Q5_FREE_ORACLE_SHA256 = "5f3e06535de65e63e483f5930e22d522881a5ea15138e401dca60c71bd72f6e7"
SELF_EXCLUDING_SEMANTIC_DIGEST_METHOD = (
    "sha256(UTF-8 canonical JSON after excluding top-level semantic_digest_sha256: "
    "ensure_ascii=true, sort_keys=true, separators=(',', ':'))"
)
PROOF_COMPLETE_STATUS = "PROOF_COMPLETE_RELEASE_CANDIDATE_NOT_FROZEN"
PDF_BUILD_HELPER_PATH = Path("scripts/build_v042_paper1_pdf.py")
PDF_BUILD_HELPER_SHA256 = "f131bbfe76304f1445afe162af5d731c7c3c4d31ba1b7dced4e83a0fb87c91d4"
PDF_BUILD_REPORT_PATH = Path("reports/v0.4.2_paper1_pdf_build_2026-08-05.md")
PDF_BUILD_REPORT_SHA256 = "5c4230d39d8db58fb58cccfdf4f7ce48b20716fe37dfa2e854c7f3b0eadb0c52"
PDF_BUILD_IMAGE = (
    "texlive/texlive:latest-medium@"
    "sha256:d79913b74afcf48a53ec2ad0d54b70ad3e36d65b4f1de13d811435883c2f1fd9"
)
PDF_BUILD_OUTPUT_PATH = Path("output/pdf/paper1_statewise_operator_draft_v0.4.2.pdf")
PDF_BUILD_MAIN_SHA256 = "41823e65e16187f9832782fbf3d45f95556b938aac7b5e6ee20d5ebf20854b87"
PDF_BUILD_OBSERVED_SHA256 = "92c7fd5ba1bdcb5f16ec3827e3377027217fe41f61eafed10afcc49e8d6cc506"
PDF_BUILD_PRIOR_MAIN_SHA256 = "6cf9855b1822f0c16a9ab2b3fff1fc37cd87395cbf8352e2b8322885f195cdbd"
PDF_BUILD_PRIOR_OBSERVED_SHA256 = "cf8c4c01210b010127ce29750165031a7a83788aa4cd525a829f7dddfd1adaca"
PDF_BUILD_REPORT_REQUIRED_FRAGMENTS = (
    "Status: `CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED`.",
    "All 18 pages were rendered at 120 dpi and visually inspected.",
    "No clipping, overlap, table collision, or unnatural page break was found",
    "the added prose moves the reference and evidence floats by one page",
    "retained only as prior-source history",
    "The generated PDF is an untracked local observation.",
    "it is not a required reproducibility-contract hash",
)
EXPECTED_CLAIM_LABELS = ["C1", "C2", "C3", "C4", "C5"]
EXPECTED_NONCLAIM_LABELS = ["N1", "N2", "N3", "N4", "N5", "N6"]
EXPECTED_DRAFT_MARKER_CONTRACT: dict[str, Any] = {
    "status": "CLOSED",
    "forbidden_token": "DRAFT PROOF INSERT REQUIRED.",
    "expected_invocations": 0,
    "expected_token_occurrences": 0,
    "expected_macro_definitions": 0,
    "reappearance_policy": "FAIL_CLOSED",
    "required_tex_fragments": [
        "Claim-locked proof-complete source.",
        (
            "Proof completion and machine audit do not authorise submission, deposit, "
            "or manuscript freeze."
        ),
        "proof-complete, machine-audited release-candidate source",
    ],
}
C3_SOURCE_RELATION_IDS = (
    "cpobc-relation-0b2bbe81c6394d603f63",
    "cpobc-relation-49726b7f352ba79916e5",
    "cpobc-relation-6002781cceb198b6edfd",
    "cpobc-relation-1d7b3a88785401c6531b",
    "cpobc-relation-01e29996483e2c4f342c",
    "cpobc-relation-17e9d7ae74c8bed62194",
)
C3_RAW_IDENTITIES = (
    r"B_2Q_1=B_1Q_2",
    r"B_3Q_1=B_1Q_3",
    r"B_3Q_2=B_2Q_3",
    r"B_4Q_1=B_1Q_4",
    r"B_4Q_2=B_2Q_4",
    r"B_4Q_3=B_3Q_4",
)
C3_REQUIRED_PROOF_FRAGMENTS = (
    r"\cite[Eqs.~(103), (105), and (115)--(120)]{SrivastavaSurya2026}",
    "Only associativity and adjacent unit cancellation were used",
    r"Neither GC nor MSR, Eq.~(108), Eq.~(112), B-reduction, \(d=2\), or \(Q_5\)",
    "arbitrary point of the direct system",
    r"R_i:=Q_1^{-1}Q_i",
)
C5_REQUIRED_PROOF_FRAGMENTS = (
    r"\ker(\operatorname{ev}_V)=\{0\}",
    r"\(DP=0\)",
    r"kernel dimension \(2\)",
    r"rank \(4\) and zero kernel",
    r"\mathcal R=\operatorname{span}\{I,E_{21}\}",
    "Independent non-scalar",
    r"b^2,\qquad c^2,\qquad -(a-d)^2",
    "Cyclicity does not imply separation.",
    "general linear-algebra counterexamples",
    "solution of the CPOBC equations",
    "same-residual multi-probe data",
    "each source and for each declared GC and MSR residual family",
    "has not been proved by the current artifacts",
    "all declared GC and MSR residuals",
    "frozen occurrence-ON",
)
MANIFEST_SCHEMA = "final-theory-v042-paper1-manuscript-manifest-v1"
CLAIM_LEDGER_SCHEMA = "final-theory-v042-paper1-claim-boundary-v1"
BOUNDED_SCOUT_MANIFEST_PATH = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json"
)
BOUNDED_SCOUT_EXPECTATIONS_PATH = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)
BOUNDED_SCOUT_MANIFEST_SCHEMA = "sr2v-q5-free-bounded-scout-reproduction-input-manifest-v1"
BOUNDED_SCOUT_EXPECTATIONS_SCHEMA = "sr2v-q5-free-bounded-scout-expectations-v1"
BOUNDED_SCOUT_EXPECTATION_NAMES = ["row185_normal_form", "candidate_minor_only"]
BOUNDED_SCOUT_PENDING_STATUS = "PENDING_BOUNDED_SAGE_RECOMPUTATION"
BOUNDED_SCOUT_FINAL_STATUS = "PINNED"
BOUNDED_SCOUT_EXPECTATIONS_RAW_SHA256 = (
    "346aa987d9e29babc13b16c95fb088ea0c566a6e0704f8ae82c126e13a4e3f60"
)
BOUNDED_SCOUT_EXPECTATIONS_SEMANTIC_DIGEST_SHA256 = (
    "fd4a7fb3c9734abb324bf7d2e4bcb6c4296c3bb7e15f0c218b408a46f7f745da"
)
BOUNDED_SCOUT_EXPECTED_CORE_DIGESTS = {
    "row185_normal_form": "bd2d390ea996ea5149578bb569d6bba98fecbcb96b1b00d0fe8ff7b365f00deb",
    "candidate_minor_only": "cb9252dbc9d1610d3d0410f0d8f111a862b341cee59a4ced20bb8527c66a1c87",
}
LEGACY_OBSERVATION_STATUS = "NONDETERMINISTIC_LEGACY_OBSERVATION_NOT_A_REPRODUCTION_EXPECTATION"
LITERATURE_DELTA_STATUS = (
    "CLOSED_NO_MATERIAL_DELTA_WITHIN_ARCHIVED_SUBMITTEDDATE_SCOPE_AS_OF_2026-08-05T04:52:45Z"
)
LITERATURE_AUDIT_REPORT_PATH = Path("reports/v0.4.2_paper1_literature_delta_2026-08-05.md")
LITERATURE_NOTE_PATH = Path("references/notes/v0.4.2_paper1_literature_delta_2026-08-05.md")
LITERATURE_SOURCES_PATH = Path("references/sources.json")
LITERATURE_ARCHIVE_MANIFEST_PATH = Path("references/manifest.json")
LITERATURE_AUDIT_REPORT_SHA256 = "8040c4a537f707b29eba06af06710aa981efc3bd12f4e43a8ea24f652c5d0676"
LITERATURE_NOTE_SHA256 = "0712c516933ec4850591e5afc0e709205023a918abe5d315fe48392a77f6d76a"
LITERATURE_RAW_RESPONSE_PATH = Path(
    "references/papers/2026-08-05_paper1_arxiv_delta_query_atom.xml"
)
LITERATURE_RAW_RESPONSE_SHA256 = "8f1b253e2eebaa4788f19616c15ef4cc250da80bfc0d640eea4bd01b7eee08a3"
LITERATURE_RAW_RESPONSE_BYTES = 1091434
LITERATURE_NORMALIZED_LEDGER_PATH = Path(
    "references/papers/2026-08-05_paper1_arxiv_delta_query_normalized.json"
)
LITERATURE_NORMALIZED_LEDGER_SHA256 = (
    "39e12901c8db41a63070cb4ea1794a1da415aeea8c8df0160df79d7224a42c29"
)
LITERATURE_NORMALIZED_LEDGER_BYTES = 497237
LITERATURE_NORMALIZER_PATH = Path("scripts/normalize_v042_paper1_arxiv_delta_response.py")
LITERATURE_NORMALIZER_SHA256 = "4068b63080d79ac18fb42396759560399bf09a4b1742b934fd78d0598657f303"
LITERATURE_NORMALIZER_TEST_PATH = Path(
    "tests/final_theory/test_normalize_v042_paper1_arxiv_delta_response.py"
)
LITERATURE_NORMALIZER_TEST_SHA256 = (
    "afb5b38483f2acb25f92afdc3efdd7ba539659199c3970e027fdfa6399fcac16"
)
LITERATURE_NORMALIZER_CHECK_COMMAND = (
    r".venv\Scripts\python.exe scripts/normalize_v042_paper1_arxiv_delta_response.py --check"
)
LITERATURE_FEED_UPDATED_UTC = "2026-08-05T04:52:45Z"
LITERATURE_ORDERED_IDS_SHA256 = "5f8a03534e8ce34f289f0bccf7457ee6e808e6dc8efccb41cb54e8515d99c18d"
LITERATURE_RECORDS_SHA256 = "1d53423d64956f4901980d315dee87ef834c775d17cacaefa3f6440778b14bb3"
LITERATURE_DECISION_COUNTS = {
    "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 533,
    "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 23,
    "MATERIAL_DELTA_TO_C1_C5": 0,
}
LITERATURE_CATEGORY_API_URL = (
    "https://arxiv.org/api/query?search_query="
    "submittedDate:%22202607311500+TO+202608052359%22+AND+"
    "(cat:gr-qc+OR+(cat:quant-ph+OR+(cat:math-ph+OR+(cat:math.OA+OR+"
    "(cat:math.RA+OR+(cat:math.AC+OR+(cat:math.FA+OR+cat:math.CO)))))))"
    "&start=0&max_results=2000&id_list="
)
LITERATURE_SOURCE_RECORD_IDS = [
    "arXiv:PaperI-literature-delta-query-2026-08-05",
    "arXiv:2608.03273v1",
    "arXiv:2608.02166v1",
]
LITERATURE_REFERENCE_ARCHIVE = {
    "sources_path": LITERATURE_SOURCES_PATH.as_posix(),
    "manifest_path": LITERATURE_ARCHIVE_MANIFEST_PATH.as_posix(),
    "status": "HASH_ONLY_SKIP_TEXT_PYPDF_UNAVAILABLE",
    "command": "scripts/archive_references.py --skip-text",
    "query_archive_status": "LOCAL_ARTIFACTS",
    "excluded_hit_archive_status": "METADATA_ONLY",
    "excluded_hit_ids": ["arXiv:2608.03273v1", "arXiv:2608.02166v1"],
}
LITERATURE_SEARCH_WINDOW = {
    "field": "submittedDate",
    "window_start_utc": "2026-07-31T15:00:00Z",
    "window_end_minute_utc": "2026-08-05T23:59:00Z",
    "window_end_exclusive_utc": "2026-08-06T00:00:00Z",
    "feed_cutoff_utc": LITERATURE_FEED_UPDATED_UTC,
}
LITERATURE_SCREENED_CATEGORIES = [
    "gr-qc",
    "quant-ph",
    "math-ph",
    "math.OA",
    "math.RA",
    "math.AC",
    "math.FA",
    "math.CO",
]
LITERATURE_EFFECTIVE_RESPONSE_QUERY = {
    "authority": "ARCHIVED_ATOM_FEED_TITLE_AND_QUERY_LINK",
    "field": "submittedDate",
    "window_start_compact_utc": "202607311500",
    "window_end_compact_utc": "202608052359",
    "categories": LITERATURE_SCREENED_CATEGORIES,
    "start": 0,
    "max_results": 2000,
    "id_list": [],
    "window_start_utc": "2026-07-31T15:00:00Z",
    "window_end_minute_utc": "2026-08-05T23:59:00Z",
    "window_end_exclusive_utc": "2026-08-06T00:00:00Z",
    "feed_title": (
        'arXiv Query: search_query=submittedDate:"202607311500 TO 202608052359" '
        "AND (cat:gr-qc OR cat:quant-ph OR cat:math-ph OR cat:math.OA OR cat:math.RA "
        "OR cat:math.AC OR cat:math.FA OR cat:math.CO)&id_list=&start=0&max_results=2000"
    ),
    "self_link": LITERATURE_CATEGORY_API_URL,
}
LITERATURE_COVERAGE_BOUNDARY = {
    "archived_submitted_date_snapshot_only": True,
    "general_pre_window_version_updates_covered": False,
    "minimum_pre_submission_contract": [
        "archive and rescreen a full-overlap submittedDate response",
        "repeat exact-ID version checks for arXiv:2607.26672 and arXiv:2603.25503",
        "retain general pre-window version-update coverage as an explicit editorial decision",
    ],
    "tracked_exact_id_version_checks_recorded_outside_this_ledger": [
        "arXiv:2607.26672",
        "arXiv:2603.25503",
    ],
}
LITERATURE_RECONCILIATION = {
    "comparison_to_archived_556_authorized": False,
    "historical_524_id_membership_known": False,
    "historical_524_query_provenance_known": False,
    "historical_reported_screened_record_count": 524,
    "materiality_reassessment_status": "COMPLETED_ON_ARCHIVED_556_RESPONSE",
    "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
}
LITERATURE_REPORT_REQUIRED_FRAGMENTS = [
    f"Status: `{LITERATURE_DELTA_STATUS}`",
    "556-entry Atom snapshot",
    LITERATURE_RAW_RESPONSE_SHA256,
    LITERATURE_NORMALIZED_LEDGER_SHA256,
    "23 title/abstract candidates",
    "zero C1--C5 material deltas",
    "effective response query is a `submittedDate` window",
    "does not close a general later-version-update gate",
    "does not compare it to, subtract it from",
    "No inference is drawn from that unavailable response.",
    "succeeded without retry",
    "full-overlap `submittedDate` response beginning",
    "2026-07-31T15:00:00Z",
    "arXiv:PaperI-literature-delta-query-2026-08-05",
    "arXiv:2608.03273v1",
    "arXiv:2608.02166v1",
    "repeat the exact-ID version checks for Xu",
]
LITERATURE_NOTE_REQUIRED_FRAGMENTS = [
    f"Status: `{LITERATURE_DELTA_STATUS}`",
    "locally archived 556-entry arXiv Atom",
    LITERATURE_RAW_RESPONSE_SHA256,
    LITERATURE_NORMALIZED_LEDGER_SHA256,
    "Of 556 records, 533",
    "23 triggered candidates",
    "This closure covers the archived `submittedDate` response only.",
    "General pre-window version-update coverage",
    "is not compared with the archived 556 response",
    "later HTTP 429 response was unavailable and is likewise not evidence",
    "new full-overlap `submittedDate` snapshot beginning",
    "2026-07-31T15:00:00Z",
    "arXiv:PaperI-literature-delta-query-2026-08-05",
    "arXiv:2608.03273v1",
    "arXiv:2608.02166v1",
    "Immediately before public submission",
]
CANONICAL_LEDGER_DIGEST_METHOD = (
    "sha256(UTF-8 canonical JSON: ensure_ascii=true, sort_keys=true, separators=(',', ':'))"
)
BEGIN_END_PATTERN = re.compile(r"\\(begin|end)\{([^{}]+)\}")
CITATION_PATTERN = re.compile(r"\\cite[a-zA-Z*]*(?:\[[^\]]*\]){0,2}\{([^{}]+)\}")
BIB_ENTRY_PATTERN = re.compile(r"(?m)^\s*@\w+\s*\{\s*([^,\s]+)\s*,")
TEX_COMMENT_PATTERN = re.compile(r"(?<!\\)%[^\n]*")
NONCLAIM_ENUMERATION_PATTERN = re.compile(
    r"\\begin\{enumerate\}\[label=N\\arabic\*\.\](.*?)\\end\{enumerate\}", re.DOTALL
)
ITEM_PATTERN = re.compile(r"(?m)^\s*\\item\b")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _self_excluding_json_sha256(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _canonical_json_sha256(semantic)


def _compact_utf8_json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json_object(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {label}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object")
        return None
    return payload


def _strip_tex_comments(source: str) -> str:
    return TEX_COMMENT_PATTERN.sub("", source)


def _normalise_whitespace(source: str) -> str:
    return " ".join(_strip_tex_comments(source).split())


def _validate_environment_balance(source: str, errors: list[str]) -> None:
    stack: list[str] = []
    for match in BEGIN_END_PATTERN.finditer(_strip_tex_comments(source)):
        action, environment = match.groups()
        if action == "begin":
            stack.append(environment)
        elif not stack:
            errors.append(f"unexpected \\end{{{environment}}}")
        elif stack[-1] != environment:
            errors.append(
                "environment nesting mismatch: "
                f"expected \\end{{{stack[-1]}}}, got \\end{{{environment}}}"
            )
            stack.pop()
        else:
            stack.pop()
    for environment in reversed(stack):
        errors.append(f"unclosed \\begin{{{environment}}}")


def _citation_keys(source: str) -> set[str]:
    keys: set[str] = set()
    for match in CITATION_PATTERN.finditer(_strip_tex_comments(source)):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return keys


def _bibliography_key_counts(path: Path, errors: list[str]) -> Counter[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read bibliography {path.as_posix()}: {exc}")
        return Counter()
    return Counter(BIB_ENTRY_PATTERN.findall(source))


def _validate_citation_closure(
    tex: str,
    bibliography_key_counts: tuple[Counter[str], ...],
    errors: list[str],
) -> None:
    cited = _citation_keys(tex)
    _require(bool(cited), "TeX source has no citation keys", errors)

    combined_counts: Counter[str] = Counter()
    for key_counts in bibliography_key_counts:
        combined_counts.update(key_counts)

    missing = sorted(cited - set(combined_counts))
    _require(
        not missing,
        f"citation keys absent from configured bibliographies: {missing}",
        errors,
    )
    duplicates = sorted(key for key, count in combined_counts.items() if count > 1)
    _require(
        not duplicates,
        f"bibliography entry keys occur more than once across configured resources: {duplicates}",
        errors,
    )


def _manifest_file_records(
    manifest: dict[str, Any], errors: list[str]
) -> dict[Path, dict[str, Any]]:
    records = manifest.get("manuscript_files")
    if not isinstance(records, list):
        errors.append("manifest manuscript_files must be a list")
        return {}

    by_path: dict[Path, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            errors.append("manifest manuscript_files entry must be an object")
            continue
        path_value = record.get("path")
        if not isinstance(path_value, str):
            errors.append("manifest manuscript_files entry has no string path")
            continue
        path = Path(path_value)
        if path in by_path:
            errors.append(f"manifest repeats manuscript file {path.as_posix()}")
            continue
        by_path[path] = record

    _require(
        set(by_path) == EXPECTED_MANUSCRIPT_PATHS,
        "manifest must pin exactly main.tex, REPRODUCING.md, and references.bib",
        errors,
    )
    return by_path


def _validate_manifest_hashes(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    for relative, record in _manifest_file_records(manifest, errors).items():
        path = root / relative
        _require(path.is_file(), f"missing manuscript file: {relative.as_posix()}", errors)
        expected = record.get("raw_sha256")
        _require(
            isinstance(expected, str) and len(expected) == 64,
            f"invalid manuscript SHA-256 for {relative.as_posix()}",
            errors,
        )
        if path.is_file() and isinstance(expected, str):
            _require(
                _sha256(path) == expected,
                f"raw SHA-256 mismatch for {relative.as_posix()}",
                errors,
            )

    ledger_binding = manifest.get("claim_ledger")
    if not isinstance(ledger_binding, dict):
        errors.append("manifest claim_ledger must be an object")
        return
    _require(
        ledger_binding.get("path") == CLAIM_LEDGER_PATH.as_posix(),
        "manifest claim ledger path changed",
        errors,
    )
    ledger_path = root / CLAIM_LEDGER_PATH
    expected_raw = ledger_binding.get("raw_sha256")
    _require(
        isinstance(expected_raw, str) and len(expected_raw) == 64,
        "manifest claim ledger raw SHA-256 is invalid",
        errors,
    )
    if ledger_path.is_file() and isinstance(expected_raw, str):
        _require(
            _sha256(ledger_path) == expected_raw,
            "claim ledger raw SHA-256 mismatch",
            errors,
        )


def _expected_electronic_supplement() -> dict[str, Any]:
    return {
        "status": "PINNED_COMPACT_AUTHENTICATED_INDEX",
        "policy": {
            "complete_weak_ledger_remains_authority": True,
            "compact_result_replaces_complete_ledger": False,
            "embed_all_3283_records_in_pdf": False,
            "ordinary_reproduction_mode": "--check",
            "write_requires_review_and_manifest_rebinding": True,
        },
        "extractor": {
            "path": WITNESS_EXTRACTOR_PATH.as_posix(),
            "raw_sha256": WITNESS_EXTRACTOR_SHA256,
            "check_mode": "--check",
        },
        "result": {
            "path": WITNESS_RESULT_PATH.as_posix(),
            "schema_version": WITNESS_RESULT_SCHEMA,
            "raw_sha256": WITNESS_RESULT_SHA256,
            "semantic_digest_method": SELF_EXCLUDING_SEMANTIC_DIGEST_METHOD,
            "semantic_digest_sha256": WITNESS_RESULT_SEMANTIC_SHA256,
            "expected_total_top_level_records": 3283,
            "transition_occurrence_count": 165,
            "transition_orbit_count": 131,
        },
        "dedicated_test": {
            "path": WITNESS_TEST_PATH.as_posix(),
            "raw_sha256": WITNESS_TEST_SHA256,
        },
        "source_authorities": [
            {
                "path": WEAK_AUTHORITY_PATH.as_posix(),
                "raw_sha256": WEAK_AUTHORITY_SHA256,
                "role": "complete_electronic_ledger_authority",
            },
            {
                "path": OBSERVABILITY_AUTHORITY_PATH.as_posix(),
                "raw_sha256": OBSERVABILITY_AUTHORITY_SHA256,
                "schema_version": OBSERVABILITY_SCHEMA,
                "semantic_digest_sha256": OBSERVABILITY_SEMANTIC_SHA256,
                "role": "independent_exact_rational_observability_authority",
            },
            {
                "path": WEAK_ORACLE_PATH.as_posix(),
                "raw_sha256": WEAK_ORACLE_SHA256,
                "role": "independent_exact_arithmetic_oracle_code",
            },
        ],
        "q5_free_elimination_authority": {
            "result": {
                "path": Q5_FREE_AUTHORITY_PATH.as_posix(),
                "raw_sha256": Q5_FREE_AUTHORITY_SHA256,
                "schema_version": Q5_FREE_SCHEMA,
                "recorded_semantic_digest_sha256": Q5_FREE_RECORDED_SEMANTIC_SHA256,
            },
            "oracle_test": {
                "path": Q5_FREE_ORACLE_PATH.as_posix(),
                "raw_sha256": Q5_FREE_ORACLE_SHA256,
            },
        },
    }


def _validate_electronic_supplement(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    contract = manifest.get("electronic_supplement")
    _require(
        contract == _expected_electronic_supplement(),
        "electronic supplement contract changed",
        errors,
    )

    for path, expected_hash, label in (
        (WITNESS_EXTRACTOR_PATH, WITNESS_EXTRACTOR_SHA256, "witness-table extractor"),
        (WITNESS_RESULT_PATH, WITNESS_RESULT_SHA256, "witness-table result"),
        (WITNESS_TEST_PATH, WITNESS_TEST_SHA256, "witness-table dedicated test"),
        (WEAK_AUTHORITY_PATH, WEAK_AUTHORITY_SHA256, "complete weak ledger"),
        (OBSERVABILITY_AUTHORITY_PATH, OBSERVABILITY_AUTHORITY_SHA256, "observability authority"),
        (WEAK_ORACLE_PATH, WEAK_ORACLE_SHA256, "weak exact-arithmetic oracle"),
        (Q5_FREE_AUTHORITY_PATH, Q5_FREE_AUTHORITY_SHA256, "q5-free elimination result"),
        (Q5_FREE_ORACLE_PATH, Q5_FREE_ORACLE_SHA256, "q5-free elimination oracle test"),
    ):
        absolute = root / path
        _require(absolute.is_file(), f"missing {label}: {path.as_posix()}", errors)
        if absolute.is_file():
            _require(_sha256(absolute) == expected_hash, f"{label} raw SHA-256 mismatch", errors)

    witness = _read_json_object(root / WITNESS_RESULT_PATH, errors, "witness-table result")
    if witness is not None:
        _require(
            witness.get("schema_version") == WITNESS_RESULT_SCHEMA,
            "witness-table result schema changed",
            errors,
        )
        _require(witness.get("passed") is True, "witness-table result is not passing", errors)
        _require(
            witness.get("verdict") == "PAPER1_WITNESS_TABLES_EXTRACTED_FROM_BOUND_AUTHORITIES",
            "witness-table result verdict changed",
            errors,
        )
        _require(
            witness.get("semantic_digest_sha256") == WITNESS_RESULT_SEMANTIC_SHA256,
            "witness-table recorded semantic digest changed",
            errors,
        )
        _require(
            _self_excluding_json_sha256(witness) == WITNESS_RESULT_SEMANTIC_SHA256,
            "witness-table semantic digest does not recompute",
            errors,
        )
        census = witness.get("family_census")
        _require(isinstance(census, dict), "witness-table family census is absent", errors)
        if isinstance(census, dict):
            _require(
                census.get("derived_total_top_level_records") == 3283
                and census.get("expected_total_top_level_records") == 3283,
                "witness-table family census changed",
                errors,
            )
        transitions = witness.get("transition_tables")
        _require(isinstance(transitions, dict), "witness transition table is absent", errors)
        if isinstance(transitions, dict):
            _require(
                transitions.get("occurrence_count") == 165
                and transitions.get("orbit_count") == 131,
                "witness transition occurrence/orbit census changed",
                errors,
            )

    observability = _read_json_object(
        root / OBSERVABILITY_AUTHORITY_PATH,
        errors,
        "observability authority",
    )
    if observability is not None:
        _require(
            observability.get("schema_version") == OBSERVABILITY_SCHEMA,
            "observability authority schema changed",
            errors,
        )
        _require(
            observability.get("semantic_digest_sha256") == OBSERVABILITY_SEMANTIC_SHA256
            and _self_excluding_json_sha256(observability) == OBSERVABILITY_SEMANTIC_SHA256,
            "observability semantic digest changed",
            errors,
        )

    q5_free = _read_json_object(
        root / Q5_FREE_AUTHORITY_PATH,
        errors,
        "q5-free elimination result",
    )
    if q5_free is not None:
        _require(
            q5_free.get("schema_version") == Q5_FREE_SCHEMA,
            "q5-free elimination schema changed",
            errors,
        )
        _require(
            q5_free.get("semantic_digest_sha256") == Q5_FREE_RECORDED_SEMANTIC_SHA256,
            "q5-free elimination recorded semantic digest changed",
            errors,
        )
        _require(
            q5_free.get("phase1_proof_complete") is True
            and q5_free.get("verdict") == "LITERAL_Q1_Q4_COMMUTATIVITY_PROVED",
            "q5-free elimination proof boundary changed",
            errors,
        )


def _validate_claim_ledger(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> dict[str, Any] | None:
    for error in validate_claim_boundary(root):
        errors.append(f"claim-boundary validator: {error}")

    ledger_path = root / CLAIM_LEDGER_PATH
    if not ledger_path.is_file():
        errors.append(f"missing claim ledger: {CLAIM_LEDGER_PATH.as_posix()}")
        return None
    ledger = _read_json_object(ledger_path, errors, "claim ledger")
    if ledger is None:
        return None

    binding = manifest.get("claim_ledger")
    if not isinstance(binding, dict):
        return ledger
    _require(
        binding.get("schema_version") == CLAIM_LEDGER_SCHEMA
        and ledger.get("schema_version") == CLAIM_LEDGER_SCHEMA,
        "claim ledger schema binding changed",
        errors,
    )
    _require(
        binding.get("semantic_digest_method") == CANONICAL_LEDGER_DIGEST_METHOD,
        "claim ledger semantic digest method changed",
        errors,
    )
    _require(
        binding.get("semantic_digest_sha256") == _canonical_json_sha256(ledger),
        "claim ledger semantic digest mismatch",
        errors,
    )
    _require(
        binding.get("ledger_status") == "SCOPED_MANUSCRIPT_ASSEMBLY_READY"
        and ledger.get("status") == "SCOPED_MANUSCRIPT_ASSEMBLY_READY",
        "claim ledger status changed",
        errors,
    )

    claims = ledger.get("claims")
    labels = (
        [
            item.get("id", "").split("_", 1)[0]
            for item in claims
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        if isinstance(claims, list)
        else []
    )
    _require(labels == EXPECTED_CLAIM_LABELS, "claim ledger C1--C5 labels changed", errors)
    _require(
        manifest.get("claim_labels") == EXPECTED_CLAIM_LABELS,
        "manifest C1--C5 labels changed",
        errors,
    )

    nonclaims = ledger.get("nonclaims")
    nonclaim_labels = (
        [
            item.get("id", "").split("_", 1)[0]
            for item in nonclaims
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        if isinstance(nonclaims, list)
        else []
    )
    _require(
        nonclaim_labels == EXPECTED_NONCLAIM_LABELS,
        "claim ledger N1--N6 nonclaims changed",
        errors,
    )
    _require(
        manifest.get("nonclaim_labels") == EXPECTED_NONCLAIM_LABELS,
        "manifest N1--N6 nonclaims changed",
        errors,
    )
    return ledger


def _validate_completed_c3_c5_proofs(tex: str, errors: list[str]) -> None:
    source = _strip_tex_comments(tex)

    def section(start: str, end: str, label: str) -> str:
        start_index = source.find(start)
        end_index = source.find(end, start_index + len(start)) if start_index >= 0 else -1
        if start_index < 0 or end_index < 0:
            errors.append(f"cannot isolate completed {label} proof section")
            return ""
        return source[start_index:end_index]

    c3 = section(r"\subsection{C3:", r"\subsection{C4:", "C3")
    c5 = section(r"\subsection{C5:", r"\section{Proof roadmap", "C5")
    recovery = section(
        r"\section{Recovery conditions and their boundary}",
        r"\section{Explicit nonclaims}",
        "C5 recovery boundary",
    )

    _require(r"\draftmarker{" not in c3, "completed C3 proof retains a DRAFT marker", errors)
    _require(r"\draftmarker{" not in c5, "completed C5 proof retains a DRAFT marker", errors)
    _require(
        r"\draftmarker{" not in recovery,
        "completed C5 recovery boundary retains a DRAFT marker",
        errors,
    )
    for relation_id in C3_SOURCE_RELATION_IDS:
        _require(
            c3.count(relation_id) == 1,
            f"C3 must contain exactly one complete relation ID: {relation_id}",
            errors,
        )
    for identity in C3_RAW_IDENTITIES:
        _require(identity in c3, f"C3 raw relation identity is absent: {identity}", errors)
    normalised_c3 = _normalise_whitespace(c3)
    for fragment in C3_REQUIRED_PROOF_FRAGMENTS:
        _require(
            _normalise_whitespace(fragment) in normalised_c3,
            f"C3 proof boundary is absent: {fragment!r}",
            errors,
        )

    c5_evidence = c5 + "\n" + recovery
    normalised_c5 = _normalise_whitespace(c5_evidence)
    for fragment in C5_REQUIRED_PROOF_FRAGMENTS:
        _require(
            _normalise_whitespace(fragment) in normalised_c5,
            f"C5 proof boundary is absent: {fragment!r}",
            errors,
        )


def _validate_draft_marker_contract(tex: str, markers: object, errors: list[str]) -> None:
    if not isinstance(markers, dict):
        errors.append("manifest draft_markers must be an object")
        return
    _require(
        markers == EXPECTED_DRAFT_MARKER_CONTRACT,
        "closed DRAFT-marker contract changed",
        errors,
    )
    invocation_count = len(re.findall(r"\\draftmarker\s*\{", tex))
    token_count = tex.count(str(EXPECTED_DRAFT_MARKER_CONTRACT["forbidden_token"]))
    macro_definition_count = len(
        re.findall(
            r"\\(?:newcommand|renewcommand|providecommand)\*?\s*"
            r"(?:\{\s*)?\\draftmarker\b",
            tex,
        )
    )
    for label, actual, field in (
        ("invocation", invocation_count, "expected_invocations"),
        ("token occurrence", token_count, "expected_token_occurrences"),
        ("macro definition", macro_definition_count, "expected_macro_definitions"),
    ):
        expected = EXPECTED_DRAFT_MARKER_CONTRACT[field]
        _require(
            actual == expected,
            f"DRAFT marker {label} count mismatch: expected {expected}, got {actual}",
            errors,
        )
    normalised_tex = _normalise_whitespace(tex)
    for fragment in EXPECTED_DRAFT_MARKER_CONTRACT["required_tex_fragments"]:
        _require(
            isinstance(fragment, str) and _normalise_whitespace(fragment) in normalised_tex,
            f"proof-complete boundary text is absent: {fragment!r}",
            errors,
        )


def _validate_bibliography_and_tex(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    tex_path = root / MANUSCRIPT_ROOT / "main.tex"
    if not tex_path.is_file():
        errors.append(f"missing TeX source: {tex_path.as_posix()}")
        return
    try:
        tex = tex_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read TeX source: {exc}")
        return

    _validate_environment_balance(tex, errors)
    bibliography = manifest.get("bibliography")
    if not isinstance(bibliography, dict):
        errors.append("manifest bibliography must be an object")
        return
    expected_entries = bibliography.get("tex_entries")
    _require(
        expected_entries == ["../v0.3.9_d2_commutativity_short_report/references", "references"],
        "manifest bibliography TeX entries changed",
        errors,
    )
    matches = re.findall(r"\\bibliography\{([^{}]+)\}", _strip_tex_comments(tex))
    _require(len(matches) == 1, "TeX source must contain exactly one bibliography command", errors)
    entries = [part.strip() for part in matches[0].split(",")] if len(matches) == 1 else []
    _require(entries == expected_entries, "TeX bibliography entries do not match manifest", errors)

    shared_relative = Path("paper/v0.3.9_d2_commutativity_short_report/references.bib")
    local_relative = MANUSCRIPT_ROOT / "references.bib"
    _require(
        bibliography.get("shared_bib_path") == shared_relative.as_posix(),
        "shared bibliography path changed",
        errors,
    )
    _require(
        bibliography.get("local_bib_path") == local_relative.as_posix(),
        "local bibliography path changed",
        errors,
    )
    _require((root / shared_relative).is_file(), "shared bibliography file is missing", errors)
    _require((root / local_relative).is_file(), "local bibliography file is missing", errors)

    shared_key_counts = _bibliography_key_counts(root / shared_relative, errors)
    local_key_counts = _bibliography_key_counts(root / local_relative, errors)
    _validate_citation_closure(tex, (shared_key_counts, local_key_counts), errors)
    shared_keys = set(shared_key_counts)
    local_keys = set(local_key_counts)
    _require("Xu2026Relational" in local_keys, "local bibliography lacks Xu2026Relational", errors)
    _require(
        {"RideoutSorkin2000", "SrivastavaSurya2026"} <= shared_keys,
        "shared bibliography lacks manuscript baseline citations",
        errors,
    )
    _validate_completed_c3_c5_proofs(tex, errors)

    for label in EXPECTED_CLAIM_LABELS:
        _require(f"\\subsection{{{label}:" in tex, f"TeX source lacks {label} subsection", errors)
        _require(f"[{label}:" in tex, f"TeX source lacks {label} theorem/lemma label", errors)
    _require(
        "\\begin{enumerate}[label=N\\arabic*.]" in tex,
        "TeX source lacks the N1--N6 nonclaim enumeration",
        errors,
    )
    nonclaim_requirements = manifest.get("nonclaim_text_requirements")
    if not isinstance(nonclaim_requirements, list):
        errors.append("manifest nonclaim_text_requirements must be a list")
    else:
        requirement_ids = [
            item.get("id") for item in nonclaim_requirements if isinstance(item, dict)
        ]
        _require(
            requirement_ids == EXPECTED_NONCLAIM_LABELS,
            "manifest nonclaim text requirements must map N1--N6 in order",
            errors,
        )
        nonclaim_matches = NONCLAIM_ENUMERATION_PATTERN.findall(_strip_tex_comments(tex))
        _require(
            len(nonclaim_matches) == 1,
            "TeX source must contain exactly one N1--N6 nonclaim enumeration",
            errors,
        )
        item_count = len(ITEM_PATTERN.findall(nonclaim_matches[0])) if nonclaim_matches else 0
        _require(item_count == 6, "N1--N6 nonclaim enumeration must contain six items", errors)
        normalised_tex = _normalise_whitespace(tex)
        for requirement in nonclaim_requirements:
            if not isinstance(requirement, dict):
                errors.append("nonclaim text requirement must be an object")
                continue
            identifier = requirement.get("id")
            fragment = requirement.get("required_fragment")
            _require(
                isinstance(fragment, str) and fragment in normalised_tex,
                f"TeX source lacks explicit {identifier} nonclaim boundary",
                errors,
            )

    _validate_draft_marker_contract(tex, manifest.get("draft_markers"), errors)


def _validate_state_boundary_text(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    requirements = manifest.get("state_boundary_text")
    if not isinstance(requirements, dict):
        errors.append("manifest state_boundary_text must be an object")
        return

    documents = {
        "main_tex_required_fragments": root / MANUSCRIPT_ROOT / "main.tex",
        "reproducing_required_fragments": root / MANUSCRIPT_ROOT / "REPRODUCING.md",
    }
    for field, path in documents.items():
        fragments = requirements.get(field)
        if not isinstance(fragments, list) or not fragments:
            errors.append(f"manifest {field} must be a nonempty list")
            continue
        try:
            source = _normalise_whitespace(path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"cannot read state-boundary document {path.as_posix()}: {exc}")
            continue
        for fragment in fragments:
            _require(
                isinstance(fragment, str) and fragment in source,
                f"state-boundary text missing from {path.name}: {fragment!r}",
                errors,
            )

    forbidden = requirements.get("reproducing_forbidden_fragments")
    if not isinstance(forbidden, list):
        errors.append("manifest reproducing_forbidden_fragments must be a list")
        return
    reproducing_path = root / MANUSCRIPT_ROOT / "REPRODUCING.md"
    try:
        reproducing_source = _normalise_whitespace(reproducing_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"cannot read state-boundary document {reproducing_path.as_posix()}: {exc}")
        return
    for fragment in forbidden:
        _require(
            isinstance(fragment, str) and fragment not in reproducing_source,
            f"forbidden reproduction-expectation text remains in REPRODUCING.md: {fragment!r}",
            errors,
        )


def _validate_bounded_scout_reproduction(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    """Require a pinned mathematical core without binding timing observations.

    The input manifest M authenticates the scripts, fixtures, and Sage image.
    The self-bound expectations artifact E records the two deterministic
    certificate-core digests after bounded Sage recomputation.  The Paper I
    manifest F then externally pins E's raw bytes, self semantic digest, and
    both core digests.  This acyclic M -> E -> F contract rejects a changed E
    even if E is self-rebound; timing observations remain outside the cores.
    """

    contract = manifest.get("bounded_scout_reproduction")
    if not isinstance(contract, dict):
        errors.append("manifest bounded_scout_reproduction must be an object")
        return

    expected_contract_keys = {
        "input_manifest",
        "expectations",
        "legacy_observation_status",
    }
    _require(
        set(contract) == expected_contract_keys,
        "bounded-scout reproduction contract keys changed",
        errors,
    )
    _require(
        contract.get("input_manifest")
        == {
            "path": BOUNDED_SCOUT_MANIFEST_PATH.as_posix(),
            "schema_version": BOUNDED_SCOUT_MANIFEST_SCHEMA,
        },
        "bounded-scout input-manifest binding changed",
        errors,
    )
    _require(
        contract.get("expectations")
        == {
            "path": BOUNDED_SCOUT_EXPECTATIONS_PATH.as_posix(),
            "schema_version": BOUNDED_SCOUT_EXPECTATIONS_SCHEMA,
            "pending_status": BOUNDED_SCOUT_PENDING_STATUS,
            "required_final_status": BOUNDED_SCOUT_FINAL_STATUS,
            "certificate_core_names": BOUNDED_SCOUT_EXPECTATION_NAMES,
            "raw_sha256": BOUNDED_SCOUT_EXPECTATIONS_RAW_SHA256,
            "semantic_digest_sha256": BOUNDED_SCOUT_EXPECTATIONS_SEMANTIC_DIGEST_SHA256,
            "certificate_core_digests": BOUNDED_SCOUT_EXPECTED_CORE_DIGESTS,
        },
        "bounded-scout expectations binding changed",
        errors,
    )
    _require(
        contract.get("legacy_observation_status") == LEGACY_OBSERVATION_STATUS,
        "legacy bounded-scout observations are not explicitly non-deterministic",
        errors,
    )

    try:
        input_manifest = bounded_scout_fixtures.validate_bounded_scout_reproduction_inputs(root)
        expectations = bounded_scout_fixtures.load_bounded_scout_expectations(
            root,
            str(input_manifest["semantic_digest_sha256"]),
        )
    except (OSError, RuntimeError, ValueError) as exc:
        errors.append(f"bounded-scout reproduction validation: {exc}")
        return

    _require(
        input_manifest.get("schema_version") == BOUNDED_SCOUT_MANIFEST_SCHEMA,
        "bounded-scout input-manifest schema changed",
        errors,
    )
    _require(
        expectations.get("schema_version") == BOUNDED_SCOUT_EXPECTATIONS_SCHEMA,
        "bounded-scout expectations schema changed",
        errors,
    )
    _require(
        _sha256(root / BOUNDED_SCOUT_EXPECTATIONS_PATH) == BOUNDED_SCOUT_EXPECTATIONS_RAW_SHA256,
        "bounded-scout expectations raw SHA-256 mismatch",
        errors,
    )
    _require(
        expectations.get("semantic_digest_sha256")
        == BOUNDED_SCOUT_EXPECTATIONS_SEMANTIC_DIGEST_SHA256,
        "bounded-scout expectations self semantic digest mismatch",
        errors,
    )
    _require(
        expectations.get("input_manifest_semantic_digest_sha256")
        == input_manifest.get("semantic_digest_sha256"),
        "bounded-scout expectations no longer bind the authenticated input manifest",
        errors,
    )
    _require(
        expectations.get("legacy_observation_status") == LEGACY_OBSERVATION_STATUS,
        "bounded-scout legacy result digests are not labelled as non-deterministic observations",
        errors,
    )

    core_digests = expectations.get("certificate_core_digests")
    legacy_digests = expectations.get("legacy_full_result_semantic_digests")
    if not isinstance(core_digests, dict):
        errors.append("bounded-scout certificate_core_digests must be an object")
        return
    if not isinstance(legacy_digests, dict):
        errors.append("bounded-scout legacy_full_result_semantic_digests must be an object")
        return
    _require(
        set(core_digests) == set(BOUNDED_SCOUT_EXPECTATION_NAMES),
        "bounded-scout certificate-core names changed",
        errors,
    )
    _require(
        core_digests == BOUNDED_SCOUT_EXPECTED_CORE_DIGESTS,
        "bounded-scout certificate-core digests differ from the Paper I binding",
        errors,
    )
    _require(
        set(legacy_digests) == set(BOUNDED_SCOUT_EXPECTATION_NAMES),
        "bounded-scout legacy result names changed",
        errors,
    )
    _require(
        not (set(core_digests.values()) & set(legacy_digests.values())),
        "legacy full-result digests must not serve as certificate-core expectations",
        errors,
    )

    status = expectations.get("status")
    _require(
        status in {BOUNDED_SCOUT_PENDING_STATUS, BOUNDED_SCOUT_FINAL_STATUS},
        "bounded-scout expectations status is unsupported",
        errors,
    )
    _require(
        status == BOUNDED_SCOUT_FINAL_STATUS,
        "bounded-scout certificate-core expectations remain "
        "PENDING_BOUNDED_SAGE_RECOMPUTATION; final Paper I validation requires PINNED",
        errors,
    )


def _expected_literature_archived_snapshot() -> dict[str, Any]:
    return {
        "authority_status": "AUTHORITATIVE_ARCHIVED_556_RESPONSE",
        "feed_updated_utc": LITERATURE_FEED_UPDATED_UTC,
        "raw_response": {
            "path": LITERATURE_RAW_RESPONSE_PATH.as_posix(),
            "raw_sha256": LITERATURE_RAW_RESPONSE_SHA256,
            "bytes": LITERATURE_RAW_RESPONSE_BYTES,
            "media_type": "application/atom+xml",
            "role": "RAW_API_RESPONSE",
        },
        "normalized_ledger": {
            "path": LITERATURE_NORMALIZED_LEDGER_PATH.as_posix(),
            "schema_version": "1.0",
            "source_id": LITERATURE_SOURCE_RECORD_IDS[0],
            "raw_sha256": LITERATURE_NORMALIZED_LEDGER_SHA256,
            "bytes": LITERATURE_NORMALIZED_LEDGER_BYTES,
            "media_type": "application/json",
            "role": "NORMALIZED_SCREENING_LEDGER",
        },
        "normalizer": {
            "path": LITERATURE_NORMALIZER_PATH.as_posix(),
            "raw_sha256": LITERATURE_NORMALIZER_SHA256,
            "check_command": LITERATURE_NORMALIZER_CHECK_COMMAND,
        },
        "dedicated_test": {
            "path": LITERATURE_NORMALIZER_TEST_PATH.as_posix(),
            "raw_sha256": LITERATURE_NORMALIZER_TEST_SHA256,
        },
        "effective_response_query": LITERATURE_EFFECTIVE_RESPONSE_QUERY,
        "response_entry_count": 556,
        "entries_published_in_submitted_date_window": 556,
        "entries_published_outside_submitted_date_window": 0,
        "entries_published_at_or_before_feed_cutoff": 556,
        "entries_published_after_feed_cutoff": 0,
        "minimum_published_utc": "2026-07-31T15:01:28Z",
        "maximum_published_utc": "2026-08-04T17:59:09Z",
        "screening_decision_counts": LITERATURE_DECISION_COUNTS,
        "coverage_boundary": LITERATURE_COVERAGE_BOUNDARY,
        "reconciliation": LITERATURE_RECONCILIATION,
        "ordered_arxiv_ids_sha256": LITERATURE_ORDERED_IDS_SHA256,
        "records_sha256": LITERATURE_RECORDS_SHA256,
    }


def _validate_literature_snapshot_files(root: Path, errors: list[str]) -> None:
    for path, expected_hash, expected_bytes, label in (
        (
            LITERATURE_RAW_RESPONSE_PATH,
            LITERATURE_RAW_RESPONSE_SHA256,
            LITERATURE_RAW_RESPONSE_BYTES,
            "literature raw Atom response",
        ),
        (
            LITERATURE_NORMALIZED_LEDGER_PATH,
            LITERATURE_NORMALIZED_LEDGER_SHA256,
            LITERATURE_NORMALIZED_LEDGER_BYTES,
            "literature normalized ledger",
        ),
        (
            LITERATURE_NORMALIZER_PATH,
            LITERATURE_NORMALIZER_SHA256,
            None,
            "literature normalizer",
        ),
        (
            LITERATURE_NORMALIZER_TEST_PATH,
            LITERATURE_NORMALIZER_TEST_SHA256,
            None,
            "literature normalizer dedicated test",
        ),
    ):
        absolute = root / path
        _require(absolute.is_file(), f"missing {label}: {path.as_posix()}", errors)
        if not absolute.is_file():
            continue
        _require(_sha256(absolute) == expected_hash, f"{label} raw SHA-256 mismatch", errors)
        if expected_bytes is not None:
            _require(
                absolute.stat().st_size == expected_bytes,
                f"{label} byte count mismatch",
                errors,
            )

    ledger = _read_json_object(
        root / LITERATURE_NORMALIZED_LEDGER_PATH,
        errors,
        "literature normalized ledger",
    )
    if ledger is None:
        return
    expected_headers = {
        "schema_version": "1.0",
        "source_id": LITERATURE_SOURCE_RECORD_IDS[0],
        "gate_status": LITERATURE_DELTA_STATUS,
        "effective_response_query": LITERATURE_EFFECTIVE_RESPONSE_QUERY,
        "response_entry_count": 556,
        "entries_published_in_submitted_date_window": 556,
        "entries_published_outside_submitted_date_window": 0,
        "entries_published_at_or_before_feed_cutoff": 556,
        "entries_published_after_feed_cutoff": 0,
        "minimum_published_utc": "2026-07-31T15:01:28Z",
        "maximum_published_utc": "2026-08-04T17:59:09Z",
        "coverage_boundary": LITERATURE_COVERAGE_BOUNDARY,
        "reconciliation": LITERATURE_RECONCILIATION,
    }
    for field, expected in expected_headers.items():
        _require(
            ledger.get(field) == expected,
            f"literature normalized ledger header changed: {field}",
            errors,
        )
    _require(
        ledger.get("raw_response")
        == {
            "path": LITERATURE_RAW_RESPONSE_PATH.as_posix(),
            "sha256": LITERATURE_RAW_RESPONSE_SHA256,
            "bytes": LITERATURE_RAW_RESPONSE_BYTES,
            "feed_updated_utc": LITERATURE_FEED_UPDATED_UTC,
        },
        "literature normalized ledger raw-response binding changed",
        errors,
    )
    records = ledger.get("records")
    _require(isinstance(records, list), "literature normalized records must be a list", errors)
    if isinstance(records, list):
        ordered_ids = [
            record.get("arxiv_id") if isinstance(record, dict) else None for record in records
        ]
        _require(
            len(records) == 556
            and all(isinstance(identifier, str) for identifier in ordered_ids)
            and _compact_utf8_json_sha256(ordered_ids) == LITERATURE_ORDERED_IDS_SHA256,
            "literature normalized ordered-ID digest changed",
            errors,
        )
        _require(
            _compact_utf8_json_sha256(records) == LITERATURE_RECORDS_SHA256,
            "literature normalized complete-record digest changed",
            errors,
        )
    _require(
        ledger.get("ordered_arxiv_ids_sha256") == LITERATURE_ORDERED_IDS_SHA256
        and ledger.get("records_sha256") == LITERATURE_RECORDS_SHA256,
        "literature normalized recorded content digests changed",
        errors,
    )
    screening = ledger.get("screening")
    _require(isinstance(screening, dict), "literature normalized screening is absent", errors)
    if isinstance(screening, dict):
        _require(
            screening.get("decision_counts") == LITERATURE_DECISION_COUNTS
            and screening.get("material_delta_ids") == [],
            "literature normalized screening decisions changed",
            errors,
        )
    _require(
        ledger.get("reconciliation") == LITERATURE_RECONCILIATION,
        "literature normalized historical-observation reconciliation changed",
        errors,
    )


def _validate_literature_source_archive(root: Path, errors: list[str]) -> None:
    """Authenticate the archived query dataset and two metadata-only hits."""

    _validate_literature_snapshot_files(root, errors)

    catalog = _read_json_object(root / LITERATURE_SOURCES_PATH, errors, "reference source catalog")
    archive = _read_json_object(
        root / LITERATURE_ARCHIVE_MANIFEST_PATH,
        errors,
        "reference archive manifest",
    )
    if catalog is None or archive is None:
        return
    _require(
        catalog.get("schema_version") == "1.0" and catalog.get("retrieved_on") == "2026-08-05",
        "reference source catalog schema or retrieval date changed",
        errors,
    )
    source_records = catalog.get("sources")
    archive_records = archive.get("records")
    if not isinstance(source_records, list):
        errors.append("reference source catalog sources must be a list")
        return
    if not isinstance(archive_records, list):
        errors.append("reference archive manifest records must be a list")
        return

    def by_id(records: list[Any], label: str) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                errors.append(f"{label} has a malformed record")
                continue
            identifier = record["id"]
            if identifier in indexed:
                errors.append(f"{label} repeats record {identifier}")
                continue
            indexed[identifier] = record
        return indexed

    catalog_by_id = by_id(source_records, "reference source catalog")
    archive_by_id = by_id(archive_records, "reference archive manifest")
    _require(
        archive.get("schema_version") == "1.0"
        and archive.get("catalog") == LITERATURE_SOURCES_PATH.as_posix(),
        "reference archive manifest schema or catalog binding changed",
        errors,
    )
    for identifier in LITERATURE_SOURCE_RECORD_IDS:
        _require(
            identifier in catalog_by_id,
            f"reference source catalog lacks literature-delta record {identifier}",
            errors,
        )
        _require(
            identifier in archive_by_id,
            f"reference archive manifest lacks literature-delta record {identifier}",
            errors,
        )
        if identifier not in catalog_by_id or identifier not in archive_by_id:
            continue
        source = catalog_by_id[identifier]
        archived = archive_by_id[identifier]
        expected_archive_status = (
            "LOCAL_ARTIFACTS" if identifier == LITERATURE_SOURCE_RECORD_IDS[0] else "METADATA_ONLY"
        )
        _require(
            archived.get("archive_status") == expected_archive_status
            and archived.get("sha256") is None
            and archived.get("bytes") is None
            and archived.get("pages") is None
            and archived.get("text_file") is None,
            f"literature-delta archive role changed for {identifier}",
            errors,
        )
        archived_source = {
            key: value
            for key, value in archived.items()
            if key not in {"archive_status", "sha256", "bytes", "pages", "text_file"}
        }
        _require(
            archived_source == source,
            f"reference archive manifest differs from source catalog for {identifier}",
            errors,
        )

    query = catalog_by_id.get(LITERATURE_SOURCE_RECORD_IDS[0])
    if query is not None:
        _require(
            query.get("url") == LITERATURE_CATEGORY_API_URL
            and query.get("title")
            == "Official arXiv API response: bounded Paper I submittedDate screen"
            and query.get("relationship") == "SEARCH_DATASET"
            and query.get("local_file") is None,
            "literature-delta official query provenance changed",
            errors,
        )
        _require(
            query.get("used_for")
            == [
                "bounded Paper I submittedDate-window gate for C1--C5",
                (
                    "screening records submitted in the archived 2026-07-31T15:00Z "
                    "through 2026-08-05T23:59Z response scope"
                ),
                (
                    "deterministic title-and-abstract rescreen of all 556 records in the "
                    "archived response"
                ),
            ],
            "literature-delta official query use boundary changed",
            errors,
        )
        expected_local_artifacts = [
            {
                "role": "RAW_API_RESPONSE",
                "path": LITERATURE_RAW_RESPONSE_PATH.relative_to("references").as_posix(),
                "media_type": "application/atom+xml",
                "sha256": f"sha256:{LITERATURE_RAW_RESPONSE_SHA256}",
                "bytes": LITERATURE_RAW_RESPONSE_BYTES,
            },
            {
                "role": "NORMALIZED_SCREENING_LEDGER",
                "path": LITERATURE_NORMALIZED_LEDGER_PATH.relative_to("references").as_posix(),
                "media_type": "application/json",
                "sha256": f"sha256:{LITERATURE_NORMALIZED_LEDGER_SHA256}",
                "bytes": LITERATURE_NORMALIZED_LEDGER_BYTES,
            },
        ]
        expected_dataset_snapshot = {
            "gate_status": LITERATURE_DELTA_STATUS,
            "feed_updated_utc": LITERATURE_FEED_UPDATED_UTC,
            "effective_response_query": LITERATURE_EFFECTIVE_RESPONSE_QUERY,
            "normalizer": LITERATURE_NORMALIZER_PATH.as_posix(),
            "check_command": LITERATURE_NORMALIZER_CHECK_COMMAND,
            "response_entry_count": 556,
            "entries_published_in_submitted_date_window": 556,
            "entries_published_outside_submitted_date_window": 0,
            "entries_published_at_or_before_feed_cutoff": 556,
            "entries_published_after_feed_cutoff": 0,
            "minimum_published_utc": "2026-07-31T15:01:28Z",
            "maximum_published_utc": "2026-08-04T17:59:09Z",
            "ordered_arxiv_ids_sha256": f"sha256:{LITERATURE_ORDERED_IDS_SHA256}",
            "records_sha256": f"sha256:{LITERATURE_RECORDS_SHA256}",
            "screening_decision_counts": LITERATURE_DECISION_COUNTS,
        }
        _require(
            query.get("local_artifacts") == expected_local_artifacts,
            "literature-delta query local-artifact bindings changed",
            errors,
        )
        _require(
            query.get("dataset_snapshot") == expected_dataset_snapshot,
            "literature-delta query dataset snapshot changed",
            errors,
        )
        _require(
            query.get("historical_unarchived_observation")
            == {
                "reported_screened_record_count": 524,
                "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
                "query_provenance_known": False,
                "membership_known": False,
                "comparison_to_archived_556_authorized": False,
            },
            "literature-delta historical 524 observation changed",
            errors,
        )
        _require(
            isinstance(query.get("claim_boundary"), str)
            and "within the submittedDate window" in query["claim_boundary"]
            and "general coverage of later versions" in query["claim_boundary"]
            and "neither known query provenance nor known membership" in query["claim_boundary"]
            and "explicit editorial decision" in query["claim_boundary"]
            and "No local PDF applies" in query["claim_boundary"],
            "literature-delta official query claim boundary changed",
            errors,
        )

    expected_hits = {
        "arXiv:2608.03273v1": {
            "title": (
                "On the Asymptotic of Coupled Spherical Integrals: An Operator-Valued "
                "Extension of the Free Fourier Transform"
            ),
            "authors": ["Levi-Pascal V. G. Bohnacker", "Ralf R. Müller"],
            "url": "https://arxiv.org/abs/2608.03273v1",
            "pdf_url": "https://arxiv.org/pdf/2608.03273v1",
            "version": "v1, 2026-08-04",
        },
        "arXiv:2608.02166v1": {
            "title": (
                "Generalized Temporal Coupled Mode Theory (g-TCMT) applied to Coupled "
                "Resonator Optical Waveguides with Exchange Symmetry (CROWe)"
            ),
            "authors": ["Tianrui Li", "Matthew P. Halsall", "Iain F. Crowe"],
            "url": "https://arxiv.org/abs/2608.02166v1",
            "pdf_url": "https://arxiv.org/pdf/2608.02166v1",
            "version": "v1, 2026-08-03",
        },
    }
    for identifier, expected in expected_hits.items():
        record = catalog_by_id.get(identifier)
        if record is None:
            continue
        _require(
            all(record.get(key) == value for key, value in expected.items())
            and record.get("retrieved_on") == "2026-08-05"
            and record.get("relationship") == "SCREENED_NONMATERIAL"
            and record.get("local_file") is None,
            f"nonmaterial literature-hit metadata changed: {identifier}",
            errors,
        )
        _require(
            isinstance(record.get("claim_boundary"), str)
            and "no local PDF or extracted text is retained" in record["claim_boundary"],
            f"nonmaterial literature-hit PDF-retention boundary changed: {identifier}",
            errors,
        )


def _validate_literature_delta_search(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    """Fail closed on the bounded Paper I literature-delta record.

    The record is deliberately a dated screening gate, not an absence or
    priority assertion.  Both the detailed report and the required research
    note are byte-pinned because their interpretive boundary affects whether
    the draft may proceed to its still-owner-gated publication steps.
    """

    literature = manifest.get("literature_delta_search")
    if not isinstance(literature, dict):
        errors.append("manifest literature_delta_search must be an object")
        return

    expected_keys = {
        "since",
        "search_window",
        "status",
        "completed",
        "audit_report",
        "note_path",
        "note_raw_sha256",
        "official_repository",
        "screened_record_count",
        "archived_snapshot",
        "screened_categories",
        "targeted_categories",
        "tracked_source_versions",
        "keyword_hits_not_material",
        "companion_public_arxiv_record_located",
        "post_completion_requery",
        "source_catalog_record_ids",
        "reference_archive",
        "material_delta_for_claim_labels",
        "recheck_before_submission",
        "full_overlap_recheck_before_submission",
        "priority_or_absolute_absence_claimed",
    }
    _require(
        set(literature) == expected_keys,
        "literature delta search keys changed",
        errors,
    )
    _require(literature.get("since") == "2026-08-01", "literature delta baseline changed", errors)
    _require(
        literature.get("search_window") == LITERATURE_SEARCH_WINDOW,
        "literature delta search window changed",
        errors,
    )
    _require(
        literature.get("status") == LITERATURE_DELTA_STATUS,
        "literature delta status is not the closed 2026-08-05 result",
        errors,
    )
    _require(literature.get("completed") is True, "literature delta search is incomplete", errors)
    _require(
        literature.get("official_repository") == "arXiv",
        "literature delta official repository changed",
        errors,
    )
    _require(
        literature.get("screened_record_count") == 556,
        "literature delta screened-record count changed",
        errors,
    )
    _require(
        literature.get("archived_snapshot") == _expected_literature_archived_snapshot(),
        "literature delta archived-snapshot contract changed",
        errors,
    )
    _require(
        literature.get("screened_categories") == LITERATURE_SCREENED_CATEGORIES,
        "literature delta screened categories changed",
        errors,
    )
    _require(
        literature.get("targeted_categories") == ["math.PR", "physics.*"],
        "literature delta targeted categories changed",
        errors,
    )
    _require(
        literature.get("tracked_source_versions")
        == {"arXiv:2607.26672": "v1", "arXiv:2603.25503": "v1"},
        "literature delta direct version checks changed",
        errors,
    )
    _require(
        literature.get("keyword_hits_not_material") == ["arXiv:2608.03273", "arXiv:2608.02166"],
        "literature delta keyword-hit boundary changed",
        errors,
    )
    _require(
        literature.get("companion_public_arxiv_record_located") is False,
        "literature delta companion-record boundary changed",
        errors,
    )
    _require(
        literature.get("post_completion_requery")
        == {
            "historical_unarchived_observation": {
                "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
                "screened_record_count": 524,
                "query_provenance_known": False,
                "id_membership_known": False,
                "comparison_to_archived_556_authorized": False,
                "authoritative": False,
            },
            "historical_http_429": {
                "status": "NO_RESPONSE_RETAINED_NOT_EVIDENCE",
                "affects_archived_screening": False,
            },
            "archival_retrieval": {
                "status": "SUCCESS_NO_RETRY",
                "feed_updated_utc": LITERATURE_FEED_UPDATED_UTC,
            },
        },
        "literature delta retrieval/prior-observation record changed",
        errors,
    )
    _require(
        literature.get("source_catalog_record_ids") == LITERATURE_SOURCE_RECORD_IDS,
        "literature delta source-catalog record IDs changed",
        errors,
    )
    _require(
        literature.get("reference_archive") == LITERATURE_REFERENCE_ARCHIVE,
        "literature delta reference-archive validation boundary changed",
        errors,
    )
    _require(
        literature.get("material_delta_for_claim_labels") == [],
        "literature delta no longer records an empty C1--C5 material delta",
        errors,
    )
    _require(
        literature.get("recheck_before_submission") is True,
        "literature delta must require a pre-submission recheck",
        errors,
    )
    _require(
        literature.get("full_overlap_recheck_before_submission") is True,
        "literature delta must require a full-overlap pre-submission recheck",
        errors,
    )
    _require(
        literature.get("priority_or_absolute_absence_claimed") is False,
        "literature delta must not make priority or absolute-absence claims",
        errors,
    )

    report_binding = literature.get("audit_report")
    _require(
        report_binding
        == {
            "path": LITERATURE_AUDIT_REPORT_PATH.as_posix(),
            "raw_sha256": LITERATURE_AUDIT_REPORT_SHA256,
        },
        "literature delta audit-report binding changed",
        errors,
    )
    _require(
        literature.get("note_path") == LITERATURE_NOTE_PATH.as_posix(),
        "literature delta research-note path changed",
        errors,
    )
    _require(
        literature.get("note_raw_sha256") == LITERATURE_NOTE_SHA256,
        "literature delta research-note SHA-256 changed",
        errors,
    )

    for path, expected_hash, fragments, label in (
        (
            LITERATURE_AUDIT_REPORT_PATH,
            LITERATURE_AUDIT_REPORT_SHA256,
            LITERATURE_REPORT_REQUIRED_FRAGMENTS,
            "literature delta audit report",
        ),
        (
            LITERATURE_NOTE_PATH,
            LITERATURE_NOTE_SHA256,
            LITERATURE_NOTE_REQUIRED_FRAGMENTS,
            "literature delta research note",
        ),
    ):
        absolute = root / path
        _require(absolute.is_file(), f"missing {label}: {path.as_posix()}", errors)
        if not absolute.is_file():
            continue
        _require(
            _sha256(absolute) == expected_hash,
            f"raw SHA-256 mismatch for {label}",
            errors,
        )
        try:
            source = absolute.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot read {label}: {exc}")
            continue
        normalised_source = " ".join(source.split())
        for fragment in fragments:
            _require(
                " ".join(fragment.split()) in normalised_source,
                f"{label} lacks required boundary text: {fragment!r}",
                errors,
            )

    _validate_literature_source_archive(root, errors)


def _expected_tex_build() -> dict[str, Any]:
    return {
        "toolchain_status": "HOST_ABSENT_PINNED_CONTAINER_AVAILABLE",
        "pdf_status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
        "pdf_verified": True,
        "submission_ready": False,
        "pinned_container_image": PDF_BUILD_IMAGE,
        "build_helper": {
            "path": PDF_BUILD_HELPER_PATH.as_posix(),
            "raw_sha256": PDF_BUILD_HELPER_SHA256,
        },
        "build_report": {
            "path": PDF_BUILD_REPORT_PATH.as_posix(),
            "raw_sha256": PDF_BUILD_REPORT_SHA256,
        },
        "default_output_path": PDF_BUILD_OUTPUT_PATH.as_posix(),
        "generated_pdf": {
            "tracked": False,
            "required_for_manifest_validation": False,
            "raw_sha256_role": "DATED_OBSERVATION_NOT_REPRODUCIBILITY_CONTRACT",
        },
        "current_observation": {
            "date": "2026-08-05",
            "main_tex_raw_sha256": PDF_BUILD_MAIN_SHA256,
            "pdf": {
                "page_count": 18,
                "bytes": 409760,
                "raw_sha256": PDF_BUILD_OBSERVED_SHA256,
            },
            "toolchain": {
                "tex_live": "2026",
                "latexmk": "4.88",
                "pdftex": "1.40.29",
                "bibtex": "0.99e",
            },
            "diagnostics": {
                "blocking_total": 0,
                "overfull_hbox": 0,
                "undefined_reference_or_citation": 0,
                "latex_or_package_error": 0,
                "underfull_box": 0,
            },
            "visual_qa": {
                "render_dpi": 120,
                "pages_inspected": 18,
                "all_pages_inspected": True,
                "clipping_or_overlap_found": False,
                "intentional_draft_boxes_remain": False,
            },
        },
        "prior_observations": [
            {
                "status": "PRIOR_SOURCE_OBSERVATION_NOT_CURRENT_BINDING",
                "date": "2026-08-05",
                "main_tex_raw_sha256": PDF_BUILD_PRIOR_MAIN_SHA256,
                "pdf": {
                    "page_count": 10,
                    "bytes": 371899,
                    "raw_sha256": PDF_BUILD_PRIOR_OBSERVED_SHA256,
                },
                "diagnostics": {
                    "blocking_total": 0,
                    "overfull_hbox": 0,
                    "undefined_reference_or_citation": 0,
                    "latex_or_package_error": 0,
                    "underfull_box": 0,
                },
                "visual_qa": {
                    "pages_inspected": 10,
                    "all_pages_inspected": True,
                    "clipping_or_overlap_found": False,
                    "intentional_draft_boxes_remain": True,
                },
            }
        ],
    }


def _validate_tex_build(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    tex_build = manifest.get("tex_build")
    if not isinstance(tex_build, dict):
        errors.append("manifest tex_build must be an object")
        return
    _require(
        tex_build == _expected_tex_build(),
        "TeX/PDF build contract or dated observation changed",
        errors,
    )

    for path, expected_hash, label in (
        (PDF_BUILD_HELPER_PATH, PDF_BUILD_HELPER_SHA256, "PDF build helper"),
        (PDF_BUILD_REPORT_PATH, PDF_BUILD_REPORT_SHA256, "PDF build report"),
    ):
        absolute = root / path
        _require(absolute.is_file(), f"missing {label}: {path.as_posix()}", errors)
        if absolute.is_file():
            _require(_sha256(absolute) == expected_hash, f"{label} SHA-256 mismatch", errors)

    report = root / PDF_BUILD_REPORT_PATH
    if report.is_file():
        try:
            source = _normalise_whitespace(report.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"cannot read PDF build report: {exc}")
        else:
            for fragment in PDF_BUILD_REPORT_REQUIRED_FRAGMENTS:
                _require(
                    fragment in source,
                    f"PDF build report boundary is absent: {fragment!r}",
                    errors,
                )


def _validate_status_boundaries(
    manifest: dict[str, Any], ledger: dict[str, Any] | None, errors: list[str]
) -> None:
    _require(
        manifest.get("schema_version") == MANIFEST_SCHEMA,
        "unexpected manuscript manifest schema_version",
        errors,
    )
    _require(
        manifest.get("status") == PROOF_COMPLETE_STATUS,
        "manuscript is not marked as a proof-complete, non-frozen release candidate",
        errors,
    )
    freeze = manifest.get("freeze")
    if not isinstance(freeze, dict):
        errors.append("manifest freeze must be an object")
    else:
        _require(freeze.get("status") == "NOT_FROZEN", "freeze status changed", errors)
        _require(freeze.get("frozen") is False, "manuscript must remain unfrozen", errors)
        _require(
            freeze.get("authorized") is False,
            "manuscript freeze must remain unauthorized",
            errors,
        )

    gates = manifest.get("publication_gates")
    if not isinstance(gates, dict):
        errors.append("manifest publication_gates must be an object")
    else:
        for gate_name in ("submission", "deposit"):
            gate = gates.get(gate_name)
            if not isinstance(gate, dict):
                errors.append(f"manifest {gate_name} gate must be an object")
                continue
            _require(
                gate.get("status") == "OWNER_ONLY_NOT_AUTHORIZED",
                f"{gate_name} is not owner-only and unauthorized",
                errors,
            )
            _require(gate.get("owner_only") is True, f"{gate_name} must remain owner-only", errors)
            _require(
                gate.get("authorized") is False,
                f"{gate_name} must remain unauthorized",
                errors,
            )

    boundary = manifest.get("version_boundary")
    if not isinstance(boundary, dict):
        errors.append("manifest version_boundary must be an object")
        return
    _require(
        boundary.get("global_sr2v_status") == "SEARCH_OPEN_NO_TERMINAL",
        "global SR2-V status changed",
        errors,
    )
    _require(
        boundary.get("u2_role") == "SUBROUTE_ONLY_NONTERMINAL",
        "U2 must remain a subroute-only nonterminal boundary",
        errors,
    )
    _require(
        boundary.get("u2_is_global_terminal") is False,
        "U2 cannot be a global terminal",
        errors,
    )
    reproducibility = manifest.get("reproducibility_boundary")
    if not isinstance(reproducibility, dict):
        errors.append("manifest reproducibility_boundary must be an object")
    else:
        expected_reproducibility = {
            "stage7_fixture_inputs_tracked": True,
            "bounded_scout_subset_fixture_tracked": True,
            "bounded_scouts_clone_portable": True,
            "full_3161_record_polynomial_arena_tracked": False,
            "full_bundle_clone_reproducible": False,
            "stage7_worker_reexecution": False,
            "derived_bounded_scout_calculation": True,
            "raw_stage8_event_replay_available": False,
            "sage_free_fixture_selection_test_available": True,
            "certificate_core_expectations_final_status": BOUNDED_SCOUT_FINAL_STATUS,
        }
        for field, expected in expected_reproducibility.items():
            _require(
                reproducibility.get(field) == expected,
                f"reproducibility boundary changed: {field}",
                errors,
            )
    if ledger is not None:
        version_lanes = ledger.get("version_lanes")
        if not isinstance(version_lanes, dict):
            errors.append("claim ledger version_lanes must be an object")
        else:
            _require(
                version_lanes.get("sr2v_global_status") == "SEARCH_OPEN_NO_TERMINAL",
                "claim ledger global SR2-V status changed",
                errors,
            )
            _require(
                version_lanes.get("u2_subroute_is_not_sr2v_terminal") is True,
                "claim ledger no longer marks U2 as subroute-only",
                errors,
            )


def validate_paper1_manuscript(root: Path) -> list[str]:
    """Return validation errors; an empty list means the draft boundary holds."""

    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH
    _require(manifest_path.is_file(), f"missing manuscript manifest: {MANIFEST_PATH}", errors)
    if errors:
        return errors
    manifest = _read_json_object(manifest_path, errors, "manuscript manifest")
    if manifest is None:
        return errors

    _validate_manifest_hashes(root, manifest, errors)
    ledger = _validate_claim_ledger(root, manifest, errors)
    _validate_bibliography_and_tex(root, manifest, errors)
    _validate_electronic_supplement(root, manifest, errors)
    _validate_state_boundary_text(root, manifest, errors)
    _validate_bounded_scout_reproduction(root, manifest, errors)
    _validate_literature_delta_search(root, manifest, errors)
    _validate_tex_build(root, manifest, errors)
    _validate_status_boundaries(manifest, ledger, errors)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_paper1_manuscript(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("paper1_manuscript=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
