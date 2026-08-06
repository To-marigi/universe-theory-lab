"""Build the owner-gated Paper I v0.4.2 Zenodo upload candidate.

The default candidate is a standalone final PDF plus a deterministic source /
reproduction supplement archive.  Zenodo can therefore preview the Preprint
PDF directly while the supplement records that PDF as an external-file hash
binding, without duplicating the PDF bytes inside the supplement.

The historical one-archive candidate is retained only for offline integrity
verification and explicit legacy comparisons; it is not the recommended
Paper I Zenodo layout.

The final verified generated PDF is read-only input.  Before copying it, this
builder fail-closes on the current manuscript manifest, PDF build report, and
the PDF's title/author metadata.  A pending source/PDF rebind is never
packaged.  No root metadata, public operation, or frozen v0.3.9 artifact is
changed.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import tarfile
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SUPPLEMENT_SCHEMA_VERSION = "zenodo-paper1-supplement-manifest-v1"
OUTER_SCHEMA_VERSION = "zenodo-paper1-single-archive-manifest-v1"
OWNER_DECISION_SCHEMA_VERSION = "zenodo-paper1-owner-decision-v1"
BUNDLE_VERSION = "0.4.2"
SUPPLEMENT_PREFIX = "paper1-statewise-operator-v0.4.2-supplement"
OUTER_PREFIX = "paper1-statewise-operator-v0.4.2-upload"
SUPPLEMENT_MANIFEST_PATH = "upload_checksums.json"
OUTER_MANIFEST_PATH = "upload_checksums.json"
PAPER_TITLE = (
    "Statewise versus operator Bell causality in finite quantum sequential "
    "growth: exact separation and recovery at dimension two"
)

PDF_SOURCE_PATH = "output/pdf/paper1_statewise_operator_v0.4.2.pdf"
WITNESS_SOURCE_PATH = "results/v0.4.2_paper1_witness_tables.json"
MANUSCRIPT_MANIFEST_PATH = "results/v0.4.2_paper1_manuscript_manifest.json"
CLAIM_LEDGER_PATH = "results/v0.4.2_paper1_claim_boundary.json"
PDF_BUILD_REPORT_PATH = "reports/v0.4.2_paper1_pdf_build_2026-08-06.md"
REPOSITORY_URL = "https://github.com/To-marigi/universe-theory-lab"
OWNER_DECISION_ARTIFACT_PATH = "zenodo/paper1-v0.4.2/owner_decision.json"
PREVIOUS_OWNER_DECISION_REPORT_PATH = (
    "reports/v0.4.2_paper1_owner_decision_2026-08-06.md"
)
OWNER_DECISION_REPORT_PATH = (
    "reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md"
)
METADATA_TEMPLATE_PATH = "zenodo/paper1-v0.4.2/metadata.template.json"
ZENODO_FORM_VALUES_PATH = "zenodo/paper1-v0.4.2/ZENODO_FORM_VALUES.md"
ZENODO_SUBMISSION_POLICY_NOTE_PATH = (
    "references/notes/v0.4.2_paper1_zenodo_submission_policy_2026-08-07.md"
)
DOI_POLICY = "NO_DRAFT_RESERVATION_ZENODO_REGISTERS_DOI_AT_PUBLICATION"
DOI_STATUS = "NO_DRAFT_RESERVATION_DOI_PENDING_PUBLICATION"
ZENODO_LITERATURE_REPORT_PATH = "reports/v0.4.2_paper1_zenodo_literature_gate_2026-08-06.md"
ZENODO_LITERATURE_NOTE_PATH = (
    "references/notes/v0.4.2_paper1_zenodo_literature_gate_2026-08-06.md"
)
ZENODO_PREDRAFT_REPORT_PATH = (
    "reports/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-07_20260806T2315Z.md"
)
ZENODO_PREDRAFT_NOTE_PATH = (
    "references/notes/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-07_20260806T2315Z.md"
)
ZENODO_PREDRAFT_NORMALIZER_PATH = (
    "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py"
)
ZENODO_PREDRAFT_LEDGER_PATH = (
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_arxiv_normalized.json"
)
ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH = (
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_arxiv_full_overlap_atom.xml"
)
ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH = (
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_arxiv_exact_ids_atom.xml"
)
ZENODO_PREDRAFT_RECEIPT_PATH = (
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_arxiv_retrieval.json"
)
ZENODO_PREDRAFT_SOURCE_ID = "arXiv:PaperI-zenodo-predraft-gate-2026-08-06T2315Z"
ZENODO_PREDRAFT_GATE_STATUS = (
    "CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_PREDRAFT_GATE_AS_OF_2026-08-06T23:16:23Z"
)
ZENODO_PREDRAFT_GATE_TRIGGER_UTC = "2026-08-06T23:15:00Z"
ZENODO_PREDRAFT_FEED_CUTOFF = "2026-08-06T23:16:23Z"
ZENODO_PREDRAFT_ARTIFACT_HASHES = {
    ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH: (
        "5755490b293f9cd8e78217de7ea01e4799ffbb1df04daa0d4f411974caf7b373",
        1422899,
    ),
    ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH: (
        "eff76a847e3b02a01041fd8185e38bbaba93ec769ca037c903719f0062b920eb",
        5201,
    ),
    ZENODO_PREDRAFT_RECEIPT_PATH: (
        "fbe9b22defc23e84627339f9844ea8c8078ce96e563c6dfca0f559c57b933523",
        2004,
    ),
    ZENODO_PREDRAFT_LEDGER_PATH: (
        "084e69f06f31c93e5f7b9394da15e088733b45074dc7d59920e86507c516c456",
        655325,
    ),
    ZENODO_PREDRAFT_NORMALIZER_PATH: (
        "a1e5280ef034b95cd43c5fb3a91c3af43404d7f7e7c44c6acf36568ae9d24d44",
        44269,
    ),
    ZENODO_PREDRAFT_REPORT_PATH: (
        "9910c0df61ffc64d19fbe3a1eacc4fbdfe8c7335e4cc21912460dbe8b7243901",
        3580,
    ),
    ZENODO_PREDRAFT_NOTE_PATH: (
        "aca9b76bf484e0467d32b7b66e4f3ccc9ee2cf077937996ab1c43e2b4bd7002b",
        1675,
    ),
}
ZENODO_PREDRAFT_PREDECESSOR_SOURCE_ID = (
    "arXiv:PaperI-zenodo-predraft-gate-2026-08-06T1123Z"
)
ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH = (
    "reports/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-06T1123Z.md"
)
ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH = (
    "references/notes/v0.4.2_paper1_zenodo_predraft_literature_gate_2026-08-06T1123Z.md"
)
ZENODO_PREDRAFT_PREDECESSOR_DOCUMENT_HASHES = {
    ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH: (
        "2d6557fb5e01c02fb2d9ca050440118305153013622b8716733ed8fa036623e9",
        9590,
    ),
    ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH: (
        "48e0dce188b74abdc7a5b1d8c02f49286eccc164406cefd3827236ec5a916764",
        8015,
    ),
}
ZENODO_PREDRAFT_DELTA_CONTRACT = {
    "added_count": 0,
    "added_ids_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
    "missing_count": 0,
    "missing_ids_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
    "version_pair_count": 0,
    "version_pairs_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
    "replacement_base_ids": [],
    "new_no_target_count": 0,
    "new_rule_triggered_ids": [],
    "new_rule_triggered_ids_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
    "prior_candidate_count": 28,
    "predraft_candidate_count": 28,
    "shared_metadata_changed_ids": [],
    "shared_screening_changed_ids": [],
    "shared_metadata_review_ids_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
}
FINAL_REBIND_STATUSES = frozenset(
    {
        "FINAL_VERIFIED_SOURCE_PDF_BINDING",
        "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
    }
)
OWNER_DECISION_PDF_SHA256 = (
    "9f58867d91673c09229077cd651a35d16d10e90c618cc6ef6083fd4fb644fd43"
)
OWNER_DECISION_PDF_BYTES = 427745
OWNER_DECISION_PDF_PAGE_COUNT = 18
# Kept empty deliberately: even the owner-editable metadata worksheet must
# exist in the selected final commit when commit binding is requested.
COMMIT_UNTRACKED_OPTIONAL_PATHS = frozenset()

UPLOAD_PDF_NAME = "paper1_statewise_operator_v0.4.2.pdf"
UPLOAD_SUPPLEMENT_NAME = "paper1_statewise_operator_v0.4.2_supplement.tar.gz"
UPLOAD_ARCHIVE_NAME = "paper1_statewise_operator_v0.4.2_zenodo.tar.gz"
SINGLE_ARCHIVE_LAYOUT = "single_archive"
PDF_AND_SUPPLEMENT_LAYOUT = "pdf_and_supplement"
WITNESS_MEMBER_PATH = f"witness/{UPLOAD_PDF_NAME.removesuffix('.pdf')}_witness_tables.json"

MEMBER_MODE = 0o644
MEMBER_UID = 0
MEMBER_GID = 0
MEMBER_UNAME = ""
MEMBER_GNAME = ""
MEMBER_MTIME = 0
GZIP_MTIME = 0
GZIP_COMPRESSLEVEL = 9
READ_BLOCK_BYTES = 1024 * 1024

FORBIDDEN_ARCHIVE_PREFIXES = (
    "references/papers/",
    "references/text/",
    "oracle/sage_periods/vendor/",
)
REQUIRED_DESCRIPTION_FRAGMENTS = (
    "finite",
    "nonsingular",
    "occurrence-ON",
    "d=2",
    "n<=4",
    "five ledger-bound results",
    "strong/strong commutativity baseline",
    "fixed-vector/general-covariance",
    "Eq. (120)",
    "proper reconstruction slice",
    "statewise-to-operator recovery",
    "955 or 721 profiles",
    "U2 auxiliary-ideal",
    "not as a unit-ideal theorem",
)
REQUIRED_METADATA_KEYWORDS = {
    "causal sets",
    "quantum sequential growth",
    "finite quantum sequential growth",
    "Bell causality",
    "CPOBC",
    "statewise observability",
    "statewise-to-operator recovery",
    "exact rational certificates",
    "noncommutative matrices",
}
REQUIRED_MAIN_TEX_FRAGMENTS = (
    "Claim-locked archive/submission candidate, Paper I v0.4.2.",
    "C1--C5 and the explicit nonclaims N1--N6",
    r"PAPER\_I\_SCOPED\_U2\_RESOURCE\_OPEN\_LIMITATION\_ACCEPTED",
    "https://github.com/To-marigi/universe-theory-lab",
    "OpenAI Codex (using the Luna and Sol agent scopes) was used for implementation",
    "Anthropic Claude was used for research-design discussion",
    "The AI systems are neither authors nor independent proof authorities.",
    "The human author selected the definitions, scope, budgets, evidence, and final wording",
    "Archive metadata, the exact repository commit, and any DOI are maintained externally",
)
REQUIRED_REPRODUCING_FRAGMENTS = (
    "PAPER_I_SCOPED_ARCHIVE_SUBMISSION_CANDIDATE_NOT_FROZEN",
    "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED",
    "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
    "scripts/normalize_v042_paper1_zenodo_gate_20260806.py --check",
    "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py --check",
)


@dataclass(frozen=True, slots=True)
class FileSpec:
    """One repository source file and its stable supplement path and role."""

    archive_path: str
    source_path: str
    role: str


# The standalone PDF and compact witness table are intentionally absent here;
# the witness is added as a separate member and the PDF as an external record.
DEFAULT_SOURCE_FILE_SPECS: tuple[FileSpec, ...] = (
    FileSpec(
        "package/README.md",
        "zenodo/paper1-v0.4.2/README.md",
        "package_scope_and_upload_instructions",
    ),
    FileSpec(
        "package/UPLOAD_CHECKLIST.md",
        "zenodo/paper1-v0.4.2/UPLOAD_CHECKLIST.md",
        "owner_gated_manual_upload_checklist",
    ),
    FileSpec(
        "package/ZENODO_FORM_VALUES.md",
        ZENODO_FORM_VALUES_PATH,
        "copy_paste_zenodo_form_values",
    ),
    FileSpec(
        ZENODO_SUBMISSION_POLICY_NOTE_PATH,
        ZENODO_SUBMISSION_POLICY_NOTE_PATH,
        "current_zenodo_submission_policy_source_note",
    ),
    FileSpec(
        "package/metadata.template.json",
        METADATA_TEMPLATE_PATH,
        "owner_editable_zenodo_metadata_worksheet_not_api_payload",
    ),
    FileSpec(
        "package/owner_decision.json",
        OWNER_DECISION_ARTIFACT_PATH,
        "machine_readable_owner_decision_binding",
    ),
    FileSpec(
        "paper/v0.4.2_paper1_statewise_operator/main.tex",
        "paper/v0.4.2_paper1_statewise_operator/main.tex",
        "paper_source",
    ),
    FileSpec(
        "paper/v0.4.2_paper1_statewise_operator/REPRODUCING.md",
        "paper/v0.4.2_paper1_statewise_operator/REPRODUCING.md",
        "reproduction_protocol",
    ),
    FileSpec(
        "paper/v0.4.2_paper1_statewise_operator/references.bib",
        "paper/v0.4.2_paper1_statewise_operator/references.bib",
        "paper_local_bibliography",
    ),
    FileSpec(
        "paper/v0.3.9_d2_commutativity_short_report/references.bib",
        "paper/v0.3.9_d2_commutativity_short_report/references.bib",
        "paper_shared_bibliography",
    ),
    FileSpec(
        "scripts/build_v042_paper1_pdf.py",
        "scripts/build_v042_paper1_pdf.py",
        "pinned_pdf_build_helper",
    ),
    FileSpec(
        CLAIM_LEDGER_PATH,
        CLAIM_LEDGER_PATH,
        "claim_boundary_ledger",
    ),
    FileSpec(
        MANUSCRIPT_MANIFEST_PATH,
        MANUSCRIPT_MANIFEST_PATH,
        "manuscript_manifest",
    ),
    FileSpec(
        "reports/v0.4.2_paper1_claim_boundary_2026-08-05.md",
        "reports/v0.4.2_paper1_claim_boundary_2026-08-05.md",
        "claim_boundary_report",
    ),
    FileSpec(
        "reports/v0.4.2_paper1_editorial_disposition_2026-08-06.md",
        "reports/v0.4.2_paper1_editorial_disposition_2026-08-06.md",
        "editorial_two_layer_gate_authority",
    ),
    FileSpec(
        "reports/v0.4.2_paper1_submission_gate_2026-08-05.md",
        "reports/v0.4.2_paper1_submission_gate_2026-08-05.md",
        "submission_gate_report",
    ),
    FileSpec(
        "reports/v0.4.2_paper1_literature_delta_2026-08-05.md",
        "reports/v0.4.2_paper1_literature_delta_2026-08-05.md",
        "literature_delta_report_without_raw_feed",
    ),
    FileSpec(
        PDF_BUILD_REPORT_PATH,
        PDF_BUILD_REPORT_PATH,
        "pdf_build_report",
    ),
    FileSpec(
        OWNER_DECISION_REPORT_PATH,
        OWNER_DECISION_REPORT_PATH,
        "dated_human_owner_decision_amendment",
    ),
    FileSpec(
        PREVIOUS_OWNER_DECISION_REPORT_PATH,
        PREVIOUS_OWNER_DECISION_REPORT_PATH,
        "superseded_historical_owner_decision_report",
    ),
    FileSpec(
        "reports/v0.4.2_sr2v_auxiliary_ideal_determinantal_pilot_2026-08-05.md",
        "reports/v0.4.2_sr2v_auxiliary_ideal_determinantal_pilot_2026-08-05.md",
        "u2_resource_open_limitation_report",
    ),
    FileSpec(
        "references/notes/v0.4.2_paper1_literature_delta_2026-08-05.md",
        "references/notes/v0.4.2_paper1_literature_delta_2026-08-05.md",
        "literature_gate_note_without_raw_feed",
    ),
    FileSpec(
        ZENODO_LITERATURE_REPORT_PATH,
        ZENODO_LITERATURE_REPORT_PATH,
        "zenodo_literature_gate_report_without_raw_feed",
    ),
    FileSpec(
        ZENODO_LITERATURE_NOTE_PATH,
        ZENODO_LITERATURE_NOTE_PATH,
        "zenodo_literature_gate_note_without_raw_feed",
    ),
    FileSpec(
        ZENODO_PREDRAFT_REPORT_PATH,
        ZENODO_PREDRAFT_REPORT_PATH,
        "current_zenodo_predraft_literature_gate_report_without_raw_feed",
    ),
    FileSpec(
        ZENODO_PREDRAFT_NOTE_PATH,
        ZENODO_PREDRAFT_NOTE_PATH,
        "current_zenodo_predraft_literature_gate_note_without_raw_feed",
    ),
    FileSpec(
        ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
        ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
        "historical_zenodo_predraft_predecessor_report_without_raw_feed",
    ),
    FileSpec(
        ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
        ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
        "historical_zenodo_predraft_predecessor_note_without_raw_feed",
    ),
)

EXCLUDED_SCOPE = {
    "repository_root_readme": "README.md",
    "third_party_reference_pdfs": "references/papers/",
    "third_party_extracted_text": "references/text/",
    "vendored_archives": "oracle/sage_periods/vendor/",
    "raw_literature_query_artifacts": (
        "references/papers/2026-08-05_paper1_arxiv_delta_query_*, "
        "references/papers/2026-08-06_paper1_zenodo_gate_*, and "
        "references/papers/2026-08-06_paper1_zenodo_predraft_*, and "
        "references/papers/2026-08-07_paper1_zenodo_predraft_*"
    ),
    "pdf_in_supplement": PDF_SOURCE_PATH,
    "repository_snapshot": "all files outside this explicit supplement manifest",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(READ_BLOCK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _semantic_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def _relative_posix(value: str, label: str) -> str:
    if not value or "\\" in value:
        raise ValueError(f"{label} must be a POSIX relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must not escape its root: {value!r}")
    return value


def _is_forbidden(path: str) -> bool:
    return path.startswith(FORBIDDEN_ARCHIVE_PREFIXES)


def _normalise_specs(specs: Iterable[FileSpec]) -> list[FileSpec]:
    selected = list(specs)
    seen: set[str] = set()
    for spec in selected:
        _relative_posix(spec.archive_path, "archive_path")
        _relative_posix(spec.source_path, "source_path")
        if not spec.role:
            raise ValueError(f"file role is empty for {spec.archive_path!r}")
        if spec.archive_path in seen:
            raise ValueError(f"duplicate archive path: {spec.archive_path}")
        if _is_forbidden(spec.archive_path) or _is_forbidden(spec.source_path):
            raise ValueError(f"third-party path is outside the upload allowlist: {spec}")
        if spec.archive_path.lower().endswith(".pdf") or spec.source_path.lower().endswith(
            ".pdf"
        ):
            raise ValueError("the standalone PDF must not be duplicated in the supplement")
        if spec.source_path == WITNESS_SOURCE_PATH:
            raise ValueError(
                "the compact witness table is added automatically and must not "
                "appear in source specs"
            )
        seen.add(spec.archive_path)
    if SUPPLEMENT_MANIFEST_PATH in seen or WITNESS_MEMBER_PATH in seen:
        raise ValueError("reserved supplement member path appears in source specs")
    return sorted(selected, key=lambda item: item.archive_path)


def _decode_pdf_literal(payload: bytes) -> str | None:
    decoded = re.sub(
        rb"\\([0-7]{3})",
        lambda match: bytes((int(match.group(1), 8),)),
        payload,
    )
    if decoded.startswith(b"\xfe\xff"):
        return decoded[2:].decode("utf-16-be", errors="strict")
    return decoded.decode("latin-1", errors="strict")


def _pdf_metadata(pdf_bytes: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in ("Title", "Author"):
        match = re.search(rb"/" + key.encode("ascii") + rb"\s*\((.*?)\)", pdf_bytes, re.DOTALL)
        if match is None:
            raise RuntimeError(f"PDF metadata is missing /{key}")
        value = _decode_pdf_literal(match.group(1))
        if value is None:
            raise RuntimeError(f"PDF metadata /{key} cannot be decoded")
        result[key.lower()] = value
    return result


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return value


def _normalise_whitespace(value: str) -> str:
    return " ".join(value.split())


def _validate_owner_decision(
    root: Path,
    pdf_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the dated owner decision without authorizing release actions."""

    artifact_path = root / OWNER_DECISION_ARTIFACT_PATH
    report_path = root / OWNER_DECISION_REPORT_PATH
    artifact = _load_json(artifact_path, "owner decision artifact")
    if artifact.get("schema_version") != OWNER_DECISION_SCHEMA_VERSION:
        raise RuntimeError("owner decision artifact schema version drifted")
    recorded_semantic = artifact.get("semantic_digest_sha256")
    if not isinstance(recorded_semantic, str) or _semantic_digest(
        {key: value for key, value in artifact.items() if key != "semantic_digest_sha256"}
    ) != recorded_semantic:
        raise RuntimeError("owner decision artifact semantic digest is invalid")
    if artifact.get("decision_date") != "2026-08-07":
        raise RuntimeError("owner decision date drifted")
    if artifact.get("status") != "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING":
        raise RuntimeError("owner decision artifact status drifted")
    authority = artifact.get("authority")
    if not isinstance(authority, dict) or (
        authority.get("release_actions_not_authorized") is not True
    ):
        raise RuntimeError("owner decision artifact must keep release actions unauthorized")
    if authority.get("amends_report") != PREVIOUS_OWNER_DECISION_REPORT_PATH:
        raise RuntimeError("owner decision amendment provenance drifted")
    if authority.get("amendment_scope") != ["upload_layout", "doi_handling"]:
        raise RuntimeError("owner decision amendment scope drifted")
    decisions = artifact.get("decisions")
    if not isinstance(decisions, dict):
        raise RuntimeError("owner decision artifact decisions are missing")
    final_pdf = decisions.get("final_pdf")
    expected_pdf = {
        "accepted": True,
        "source_path": PDF_SOURCE_PATH,
        "sha256": OWNER_DECISION_PDF_SHA256,
        "bytes": OWNER_DECISION_PDF_BYTES,
        "page_count": OWNER_DECISION_PDF_PAGE_COUNT,
        "status": "CURRENT_FINAL_VERIFIED_PDF_ACCEPTED",
    }
    if final_pdf != expected_pdf:
        raise RuntimeError("owner decision final PDF acceptance drifted")
    if pdf_binding is not None:
        if (
            pdf_binding.get("pdf_sha256") != final_pdf["sha256"]
            or pdf_binding.get("pdf_bytes") != final_pdf["bytes"]
            or pdf_binding.get("pdf_page_count") != final_pdf["page_count"]
        ):
            raise RuntimeError(
                "owner decision final PDF acceptance does not match current PDF binding"
            )
    layout = decisions.get("upload_layout")
    if layout != {
        "accepted": PDF_AND_SUPPLEMENT_LAYOUT,
        "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
        "pdf_preview_required": True,
        "legacy_single_archive_historical_only": True,
        "status": "PDF_AND_SUPPLEMENT_PREPRINT_LAYOUT_ACCEPTED",
    }:
        raise RuntimeError("owner decision upload layout drifted")
    if decisions.get("license") != {
        "paper": "CC BY 4.0",
        "repository_software": "MIT",
        "status": "PAPER_LICENSE_APPROVED_SOFTWARE_LICENSE_UNCHANGED",
    }:
        raise RuntimeError("owner decision license policy drifted")
    if decisions.get("publication_date") != {
        "policy": "actual_zenodo_publication_date",
        "value": None,
        "status": "VALUE_PENDING_PUBLICATION",
    }:
        raise RuntimeError("owner decision publication-date policy drifted")
    if decisions.get("doi") != {
        "policy": DOI_POLICY,
        "draft_reservation_requested": False,
        "value": None,
        "status": DOI_STATUS,
    }:
        raise RuntimeError("owner decision DOI policy drifted")
    if decisions.get("related_identifiers") != {
        "initial": [],
        "value": [],
        "status": "INITIAL_EMPTY_LIST_APPROVED",
    }:
        raise RuntimeError("owner decision related-identifiers policy drifted")
    if decisions.get("final_commit") != {
        "policy": "external_at_deposit_build_cycle",
        "value": None,
        "status": "VALUE_PENDING_SELECTED_COMMIT",
    }:
        raise RuntimeError("owner decision final-commit policy drifted")
    expected_gates = {
        "draft_created": False,
        "doi_reserved": False,
        "freeze_executed": False,
        "submission_approved": False,
        "deposit_executed": False,
        "published": False,
    }
    if artifact.get("release_gates") != expected_gates:
        raise RuntimeError("owner decision release gates must remain unexecuted")
    try:
        report = report_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"owner decision report cannot be read: {exc}") from exc
    required_report_fragments = (
        "# Paper I v0.4.2 owner decision amendment — 2026-08-07",
        OWNER_DECISION_PDF_SHA256,
        "CC BY 4.0",
        "supersedes only the upload-layout and DOI",
        "The production upload list is",
        "exactly `paper1_statewise_operator_v0.4.2.pdf`",
        "paper1_statewise_operator_v0.4.2.pdf",
        "paper1_statewise_operator_v0.4.2_supplement.tar.gz",
        "actual first-public Zenodo date",
        "DOI policy is **no draft reservation**",
        "No, I need one",
        "Zenodo assigns/registers the DOI at publication",
        "Initial related identifiers remain the approved empty list (`[]`).",
        "exact source commit remains an external deposit/build-cycle value",
        "No Zenodo form value or file was submitted or saved.",
        "Draft creation,",
        "publication have not been",
        "No DOI reservation is requested.",
    )
    missing_report_fragments = [
        fragment for fragment in required_report_fragments if fragment not in report
    ]
    if missing_report_fragments:
        raise RuntimeError(
            f"owner decision report binding drifted: {missing_report_fragments}"
        )
    return {
        "path": OWNER_DECISION_ARTIFACT_PATH,
        "raw_sha256": _sha256(artifact_path),
        "semantic_digest_sha256": recorded_semantic,
        "report_path": OWNER_DECISION_REPORT_PATH,
        "report_raw_sha256": _sha256(report_path),
        "decision_date": artifact["decision_date"],
        "status": artifact["status"],
        "decisions": decisions,
        "release_gates": expected_gates,
    }


def _validate_candidate_source(root: Path) -> dict[str, Any]:
    """Require the externally readable candidate boundary before PDF binding."""

    checks = {
        "main.tex": (
            root / "paper/v0.4.2_paper1_statewise_operator/main.tex",
            REQUIRED_MAIN_TEX_FRAGMENTS,
        ),
        "REPRODUCING.md": (
            root / "paper/v0.4.2_paper1_statewise_operator/REPRODUCING.md",
            REQUIRED_REPRODUCING_FRAGMENTS,
        ),
    }
    missing: dict[str, list[str]] = {}
    for label, (path, fragments) in checks.items():
        try:
            source = _normalise_whitespace(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise RuntimeError(f"candidate source {label} cannot be read: {exc}") from exc
        absent = [
            fragment
            for fragment in fragments
            if _normalise_whitespace(fragment) not in source
        ]
        if absent:
            missing[label] = absent
    if missing:
        raise RuntimeError(f"candidate source boundary is incomplete: {missing}")
    main_path = checks["main.tex"][0]
    return {
        "main_tex_raw_sha256": _sha256(main_path),
        "required_main_fragments": list(REQUIRED_MAIN_TEX_FRAGMENTS),
        "required_reproducing_fragments": list(REQUIRED_REPRODUCING_FRAGMENTS),
    }


def _validate_metadata_template(
    root: Path,
    owner_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner_decision = (
        _validate_owner_decision(root) if owner_decision is None else owner_decision
    )
    template = _load_json(root / METADATA_TEMPLATE_PATH, "metadata template")
    description = template.get("description")
    if not isinstance(description, str):
        raise RuntimeError("metadata template description is not text")
    missing = [
        fragment
        for fragment in REQUIRED_DESCRIPTION_FRAGMENTS
        if fragment not in description
    ]
    if missing:
        raise RuntimeError(f"metadata description is missing required fragments: {missing}")
    if template.get("status") != "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING":
        raise RuntimeError("metadata template owner-decision status drifted")
    if template.get("template_role") != "UI worksheet only; not a Zenodo API payload":
        raise RuntimeError("metadata template is not marked as a non-API worksheet")
    if template.get("upload_type_ui_worksheet") != "Publication / Preprint":
        raise RuntimeError("metadata worksheet must recommend Publication / Preprint")
    if template.get("title") != PAPER_TITLE or template.get("version") != "0.4.2":
        raise RuntimeError("metadata worksheet title/version drifted")
    if template.get("upload_type") != "publication" or template.get("access_right") != "open":
        raise RuntimeError("metadata worksheet resource/access type drifted")
    if template.get("language") != "English":
        raise RuntimeError("metadata worksheet language must be English")
    if template.get("communities") != [] or template.get("funding") != []:
        raise RuntimeError("metadata worksheet must not invent communities or funding")
    if template.get("creators") != [
        {
            "name": "Osaki, Kenichi",
            "affiliation": "Independent researcher",
            "orcid": "0009-0003-9256-7089",
        }
    ]:
        raise RuntimeError("metadata worksheet creator identity drifted")
    if template.get("related_identifiers") != []:
        raise RuntimeError("metadata worksheet must leave related_identifiers empty")
    if template.get("publication_date") is not None:
        raise RuntimeError("metadata publication_date must remain null before Zenodo publication")
    if template.get("license") != "CC BY 4.0":
        raise RuntimeError("Paper I metadata license must be CC BY 4.0")
    if template.get("doi") is not None:
        raise RuntimeError("metadata DOI must remain null until Zenodo publication")
    if template.get("final_commit") is not None:
        raise RuntimeError("metadata final_commit must remain null until the external build cycle")
    keywords = template.get("keywords")
    if not isinstance(keywords, list) or not REQUIRED_METADATA_KEYWORDS <= set(keywords):
        raise RuntimeError(
            "metadata worksheet keywords must include the Paper I scientific vocabulary"
        )
    additional = template.get("additional_descriptions")
    if not isinstance(additional, list) or len(additional) != 2:
        raise RuntimeError("metadata additional descriptions must have two public UI entries")
    technical, ai_note = additional
    if not isinstance(technical, dict) or technical.get("type") != "Technical info":
        raise RuntimeError("metadata technical claim-boundary description drifted")
    if not isinstance(ai_note, dict) or ai_note.get("type") != "Other":
        raise RuntimeError("metadata AI additional-description type drifted")
    technical_description = technical.get("description")
    ai_description = ai_note.get("description")
    if not isinstance(technical_description, str) or not all(
        fragment in technical_description
        for fragment in (
            "C1", "C2", "C3", "C4", "C5", "N1--N6",
            "SEARCH_OPEN_NO_TERMINAL", "SOFT_RESOURCE_LIMIT_NONTERMINAL",
            "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED",
        )
    ):
        raise RuntimeError("metadata technical claim-boundary content is incomplete")
    if not isinstance(ai_description, str) or not all(
        fragment in ai_description
        for fragment in (
            "human author is responsible", "AI systems are not authors",
            "not proof authorities",
        )
    ):
        raise RuntimeError("metadata AI additional-description content is incomplete")
    ai_disclosure = template.get("ai_disclosure")
    if not isinstance(ai_disclosure, dict) or (
        ai_disclosure.get("ai_systems_are_authors") is not False
    ):
        raise RuntimeError("metadata worksheet AI disclosure must keep AI systems non-author")
    if ai_disclosure.get("ai_systems_are_proof_authorities") is not False:
        raise RuntimeError(
            "metadata worksheet AI disclosure must keep AI systems outside proof authority"
        )
    data_code = template.get("data_code_availability")
    if not isinstance(data_code, dict):
        raise RuntimeError("metadata worksheet data/code availability is missing")
    if data_code.get("repository_url") != "https://github.com/To-marigi/universe-theory-lab":
        raise RuntimeError("metadata worksheet repository URL drifted")
    expected_commit_provenance = {
        "exact_commit_recorded_in_supplement_manifest_at_build": True,
        "exact_commit_recorded_in_external_receipt_at_build": True,
        "remote_commit_visibility_verified_by_builder": False,
    }
    if any(
        data_code.get(key) is not value
        for key, value in expected_commit_provenance.items()
    ):
        raise RuntimeError("metadata worksheet commit-provenance policy drifted")
    if "exact_commit_recorded_in_external_zenodo_metadata_at_deposit" in data_code:
        raise RuntimeError("metadata worksheet retains the superseded external-metadata policy")

    ledger_path = root / CLAIM_LEDGER_PATH
    ledger = _load_json(ledger_path, "claim boundary ledger")
    binding = template.get("claim_ledger_binding")
    if not isinstance(binding, dict):
        raise RuntimeError("metadata worksheet lacks claim_ledger_binding")
    raw_sha = _sha256(ledger_path)
    semantic_sha = _semantic_digest(ledger)
    if binding.get("path") != CLAIM_LEDGER_PATH:
        raise RuntimeError("metadata claim ledger path binding drifted")
    if (
        binding.get("raw_sha256") != raw_sha
        or binding.get("semantic_digest_sha256") != semantic_sha
    ):
        raise RuntimeError("metadata claim ledger digest binding drifted")
    owner_binding = template.get("owner_decision_binding")
    if not isinstance(owner_binding, dict):
        raise RuntimeError("metadata worksheet lacks owner_decision_binding")
    expected_owner_binding = {
        "path": owner_decision["path"],
        "report_path": owner_decision["report_path"],
        "raw_sha256": owner_decision["raw_sha256"],
        "semantic_digest_sha256": owner_decision["semantic_digest_sha256"],
        "report_raw_sha256": owner_decision["report_raw_sha256"],
        "decision_date": owner_decision["decision_date"],
    }
    if owner_binding != expected_owner_binding:
        raise RuntimeError("metadata owner decision binding drifted")
    decisions = owner_decision["decisions"]
    if template.get("publication_date") != decisions["publication_date"]["value"]:
        raise RuntimeError("metadata publication_date disagrees with owner decision")
    if template.get("license") != decisions["license"]["paper"]:
        raise RuntimeError("metadata license disagrees with owner decision")
    if template.get("doi") != decisions["doi"]["value"]:
        raise RuntimeError("metadata DOI disagrees with owner decision")
    if template.get("doi_policy") != decisions["doi"]:
        raise RuntimeError("metadata DOI policy disagrees with owner decision")
    if template.get("related_identifiers") != decisions["related_identifiers"]["value"]:
        raise RuntimeError("metadata relations disagree with owner decision")
    if template.get("final_commit") != decisions["final_commit"]["value"]:
        raise RuntimeError("metadata final_commit disagrees with owner decision")
    return {
        "template_raw_sha256": _sha256(root / METADATA_TEMPLATE_PATH),
        "claim_ledger_raw_sha256": raw_sha,
        "claim_ledger_semantic_digest_sha256": semantic_sha,
        "description_fragments_checked": list(REQUIRED_DESCRIPTION_FRAGMENTS),
        "metadata_keywords_checked": sorted(REQUIRED_METADATA_KEYWORDS),
        "owner_decision_binding": expected_owner_binding,
        "owner_decision_status": owner_decision["status"],
        "owner_decisions": decisions,
        "owner_release_gates": owner_decision["release_gates"],
    }


def _predraft_predecessor_binding() -> dict[str, Any]:
    """Return the immutable 1123Z evidence retained only as supplement history."""

    def document(path: str, role: str) -> dict[str, Any]:
        sha256, bytes_count = ZENODO_PREDRAFT_PREDECESSOR_DOCUMENT_HASHES[path]
        return {
            "path": path,
            "raw_sha256": sha256,
            "bytes": bytes_count,
            "role": role,
        }

    return {
        "source_id": ZENODO_PREDRAFT_PREDECESSOR_SOURCE_ID,
        "gate_trigger_utc": "2026-08-06T11:23:00Z",
        "feed_cutoff_utc": "2026-08-06T11:28:07Z",
        "report": document(
            ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
            "HISTORICAL_PREDECESSOR_REPORT_INCLUDED_IN_ZENODO_SUPPLEMENT",
        ),
        "research_note": document(
            ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
            "HISTORICAL_PREDECESSOR_NOTE_INCLUDED_IN_ZENODO_SUPPLEMENT",
        ),
    }


def _validate_zenodo_predraft_gate(root: Path) -> dict[str, Any]:
    """Fail closed on the current 2315Z gate and its historical document context."""

    paths = {path: root / Path(path) for path in ZENODO_PREDRAFT_ARTIFACT_HASHES}
    for source_path, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Zenodo predraft gate artifact is missing: {source_path}")
        expected_sha, expected_bytes = ZENODO_PREDRAFT_ARTIFACT_HASHES[source_path]
        if (_sha256(path), path.stat().st_size) != (expected_sha, expected_bytes):
            raise RuntimeError(
                "Zenodo predraft gate artifact hash/size drifted: "
                f"{source_path} ({_sha256(path)}, {path.stat().st_size})"
            )
    for source_path, (expected_sha, expected_bytes) in (
        ZENODO_PREDRAFT_PREDECESSOR_DOCUMENT_HASHES.items()
    ):
        path = root / source_path
        if not path.is_file():
            raise FileNotFoundError(
                f"Zenodo predraft predecessor document is missing: {source_path}"
            )
        if (_sha256(path), path.stat().st_size) != (expected_sha, expected_bytes):
            raise RuntimeError(
                "Zenodo predraft predecessor document hash/size drifted: "
                f"{source_path} ({_sha256(path)}, {path.stat().st_size})"
            )

    ledger = _load_json(paths[ZENODO_PREDRAFT_LEDGER_PATH], "Zenodo predraft ledger")
    if (
        ledger.get("schema_version") != "1.4"
        or ledger.get("source_id") != ZENODO_PREDRAFT_SOURCE_ID
        or ledger.get("gate_status") != ZENODO_PREDRAFT_GATE_STATUS
    ):
        raise RuntimeError("Zenodo predraft ledger identity/status drifted")
    expected_raw = {
        "path": ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH,
        "sha256": ZENODO_PREDRAFT_ARTIFACT_HASHES[
            ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH
        ][0],
        "bytes": ZENODO_PREDRAFT_ARTIFACT_HASHES[
            ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH
        ][1],
        "feed_updated_utc": ZENODO_PREDRAFT_FEED_CUTOFF,
    }
    if ledger.get("raw_response") != expected_raw:
        raise RuntimeError("Zenodo predraft full-overlap response binding drifted")
    if (
        ledger.get("response_entry_count") != 722
        or ledger.get("entries_published_in_submitted_date_window") != 722
        or ledger.get("entries_published_outside_submitted_date_window") != 0
        or ledger.get("entries_published_at_or_before_feed_cutoff") != 722
        or ledger.get("entries_published_after_feed_cutoff") != 0
    ):
        raise RuntimeError("Zenodo predraft response-count contract drifted")
    screening = ledger.get("screening")
    if not isinstance(screening, dict) or (
        screening.get("decision_counts")
        != {
            "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 694,
            "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 28,
            "MATERIAL_DELTA_TO_C1_C5": 0,
        }
        or screening.get("material_delta_ids") != []
        or len(screening.get("inspected_candidate_ids", [])) != 28
    ):
        raise RuntimeError("Zenodo predraft screening/candidate contract drifted")
    reconciliation = ledger.get("reconciliation")
    expected_reconciliation = {
        "id_set_equal": True,
        "metadata_equal_by_id": True,
        "metadata_changes_reviewed": True,
        "reviewed_metadata_changed_ids": [],
        "screening_decisions_equal_by_shared_versioned_id": True,
        "materiality_reassessment_status": "COMPLETED_REVIEWED_NO_MATERIAL_DELTA",
    }
    if not isinstance(reconciliation, dict) or any(
        reconciliation.get(key) != value for key, value in expected_reconciliation.items()
    ):
        raise RuntimeError("Zenodo predraft zero-delta reconciliation drifted")

    predraft = ledger.get("predraft_gate_recheck")
    if not isinstance(predraft, dict) or (
        predraft.get("gate_trigger_utc") != ZENODO_PREDRAFT_GATE_TRIGGER_UTC
    ):
        raise RuntimeError("Zenodo predraft gate trigger/recheck drifted")
    exact_checks = predraft.get("exact_id_checks")
    expected_exact_raw = {
        "path": ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH,
        "sha256": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH][0],
        "bytes": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH][1],
        "feed_updated_utc": "2026-08-06T23:16:27Z",
    }
    expected_exact = {
        "raw_response": expected_exact_raw,
        "response_entry_count": 2,
        "versions": {"2603.25503": "v1", "2607.26672": "v1"},
        "status": "BOTH_TRACKED_RECORDS_REMAIN_V1",
    }
    if not isinstance(exact_checks, dict) or any(
        exact_checks.get(key) != value for key, value in expected_exact.items()
    ):
        raise RuntimeError("Zenodo predraft exact-ID version contract drifted")
    comparison = predraft.get("full_overlap_comparison")
    expected_zero_lists = {
        "added_ids": [],
        "missing_ids": [],
        "metadata_changed_ids": [],
        "screening_changed_ids": [],
        "version_pair_diagnostics": [],
        "material_delta_ids": [],
    }
    if not isinstance(comparison, dict) or (
        comparison.get("query_semantics_equal") is not True
        or comparison.get("feed_cutoff_monotone") is not True
        or comparison.get("id_set_equal") is not True
        or comparison.get("reviewed_delta_contract") != ZENODO_PREDRAFT_DELTA_CONTRACT
        or any(comparison.get(key) != value for key, value in expected_zero_lists.items())
    ):
        raise RuntimeError("Zenodo predraft zero-delta comparison contract drifted")
    title_abstract = predraft.get("title_abstract_rescreen")
    if not isinstance(title_abstract, dict) or (
        title_abstract.get("records_screened") != 722
        or title_abstract.get("rule_triggered_candidates") != 28
        or title_abstract.get("candidate_ids_sha256")
        != "7ebcd847c96b580085620402edef3c4e6c0560054c5587c54ebc9b5b6898a77f"
        or title_abstract.get("candidate_metadata_changed_ids") != []
        or title_abstract.get("candidate_decision_changed_ids") != []
        or title_abstract.get("material_delta_ids") != []
        or title_abstract.get("status") != "COMPLETED_REVIEWED_NO_MATERIAL_DELTA"
    ):
        raise RuntimeError("Zenodo predraft title/abstract zero-delta contract drifted")
    receipt = _load_json(paths[ZENODO_PREDRAFT_RECEIPT_PATH], "Zenodo predraft receipt")
    retrievals = receipt.get("retrievals")
    expected_retrievals = {
        "full_overlap": (
            ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH,
            ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH],
        ),
        "exact_ids": (
            ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH,
            ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH],
        ),
    }
    if not isinstance(retrievals, dict):
        raise RuntimeError("Zenodo predraft retrieval receipt is malformed")
    for key, (path, (sha, size)) in expected_retrievals.items():
        record = retrievals.get(key)
        if not isinstance(record, dict) or (
            record.get("path") != path
            or record.get("sha256") != sha
            or record.get("bytes") != size
            or record.get("http_status") != 200
        ):
            raise RuntimeError(f"Zenodo predraft retrieval receipt binding drifted: {key}")

    report_text = paths[ZENODO_PREDRAFT_REPORT_PATH].read_text(encoding="utf-8")
    note_text = paths[ZENODO_PREDRAFT_NOTE_PATH].read_text(encoding="utf-8")
    required_text = {
        "report": (
            report_text,
            (
                ZENODO_PREDRAFT_GATE_STATUS,
                ZENODO_PREDRAFT_SOURCE_ID,
                "Versioned-ID additions: none.  Missing versioned IDs: none.",
                "Title deltas: none.  Abstract-hash deltas: none.  Category deltas: none.",
                "Version replacements: none.  Screening-decision deltas: none.",
                "arXiv:2603.25503v1",
                "arXiv:2607.26672v1",
            ),
        ),
        "research note": (
            note_text,
            (
                ZENODO_PREDRAFT_SOURCE_ID,
                ZENODO_PREDRAFT_FEED_CUTOFF,
                "no added or missing versioned ID",
                "same 28 rule-triggered title/abstract records",
            ),
        ),
    }
    for label, (text, fragments) in required_text.items():
        missing = [fragment for fragment in fragments if fragment not in text]
        if missing:
            raise RuntimeError(f"Zenodo predraft {label} binding drifted: {missing}")

    excluded_artifacts = [
        {
            "path": path,
            "raw_sha256": ZENODO_PREDRAFT_ARTIFACT_HASHES[path][0],
            "bytes": ZENODO_PREDRAFT_ARTIFACT_HASHES[path][1],
            "role": "EXCLUDED_FROM_ZENODO_SUPPLEMENT",
        }
        for path in (
            ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH,
            ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH,
            ZENODO_PREDRAFT_RECEIPT_PATH,
            ZENODO_PREDRAFT_LEDGER_PATH,
        )
    ]
    predecessor = _predraft_predecessor_binding()
    return {
        "source_id": ZENODO_PREDRAFT_SOURCE_ID,
        "status": ZENODO_PREDRAFT_GATE_STATUS,
        "gate_trigger_utc": ZENODO_PREDRAFT_GATE_TRIGGER_UTC,
        "feed_cutoff_utc": ZENODO_PREDRAFT_FEED_CUTOFF,
        "response_entry_count": 722,
        "reviewed_title_abstract_count": 28,
        "material_delta_count": 0,
        "metadata_equal_by_id": True,
        "metadata_changes_reviewed": True,
        "reviewed_metadata_changed_ids": [],
        "report": {
            "path": ZENODO_PREDRAFT_REPORT_PATH,
            "raw_sha256": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_REPORT_PATH][0],
            "bytes": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_REPORT_PATH][1],
            "role": "HUMAN_REPORT_INCLUDED_IN_ZENODO_SUPPLEMENT",
        },
        "research_note": {
            "path": ZENODO_PREDRAFT_NOTE_PATH,
            "raw_sha256": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_NOTE_PATH][0],
            "bytes": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_NOTE_PATH][1],
            "role": "RESEARCH_NOTE_INCLUDED_IN_ZENODO_SUPPLEMENT",
        },
        "historical_predecessor": predecessor,
        "normalizer": {
            "path": ZENODO_PREDRAFT_NORMALIZER_PATH,
            "raw_sha256": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_NORMALIZER_PATH][0],
            "bytes": ZENODO_PREDRAFT_ARTIFACT_HASHES[ZENODO_PREDRAFT_NORMALIZER_PATH][1],
            "check_command": (
                ".venv\\Scripts\\python.exe "
                "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py "
                "--check"
            ),
            "role": "REPOSITORY_REPRODUCTION_SCRIPT_NOT_INCLUDED_IN_SUPPLEMENT",
        },
        "excluded_artifacts": excluded_artifacts,
        "reviewed_delta_contract": ZENODO_PREDRAFT_DELTA_CONTRACT,
        "tracked_exact_ids": ["arXiv:2607.26672", "arXiv:2603.25503"],
        "supplement_member_policy": {
            "current_authority_paths": [ZENODO_PREDRAFT_REPORT_PATH, ZENODO_PREDRAFT_NOTE_PATH],
            "historical_predecessor_paths": [
                ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
                ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
            ],
            "excluded_raw_and_derived_paths": [item["path"] for item in excluded_artifacts],
        },
    }


def _is_final_rebind(pending_rebind: dict[str, Any]) -> bool:
    """Return whether a formerly pending rebind is explicitly final and nonblocking."""

    return bool(
        pending_rebind.get("status") in FINAL_REBIND_STATUSES
        and pending_rebind.get("source_pdf_binding_authorized") is True
        and pending_rebind.get("publication_blocking") is False
    )


def _validate_pdf_binding(root: Path) -> dict[str, Any]:
    """Fail closed if PDF, TeX source, manifest, or build report drifted."""

    pdf_path = root / PDF_SOURCE_PATH
    if not pdf_path.is_file():
        raise FileNotFoundError(f"standalone PDF input is missing: {PDF_SOURCE_PATH}")
    manifest_path = root / MANUSCRIPT_MANIFEST_PATH
    report_path = root / PDF_BUILD_REPORT_PATH
    manuscript = _load_json(manifest_path, "manuscript manifest")
    tex_build = manuscript.get("tex_build", {})
    if not isinstance(tex_build, dict):
        raise RuntimeError("manuscript manifest tex_build is not an object")
    pending_rebind = tex_build.get("pending_source_rebind")
    if pending_rebind is not None:
        if not isinstance(pending_rebind, dict) or not _is_final_rebind(pending_rebind):
            raise RuntimeError(
                "PDF_REBIND_NOT_FINAL: manifest still carries a pending source/PDF "
                "rebind; require FINAL_VERIFIED_SOURCE_PDF_BINDING before packaging"
            )
    if tex_build.get("pdf_verified") is not True:
        raise RuntimeError("PDF_REBIND_NOT_FINAL: manifest does not mark the PDF verified")
    if tex_build.get("pdf_status") not in FINAL_REBIND_STATUSES:
        raise RuntimeError(
            "PDF_REBIND_NOT_FINAL: manifest PDF status is not a final verified build"
        )
    report = report_path.read_text(encoding="utf-8")
    current = tex_build.get("current_observation", {})
    expected_pdf = current.get("pdf")
    if not isinstance(expected_pdf, dict):
        raise RuntimeError("manuscript manifest has no current PDF observation")
    expected_output = tex_build.get("default_output_path")
    if expected_output != PDF_SOURCE_PATH:
        raise RuntimeError("manuscript manifest PDF output path drifted")
    main_path = root / "paper/v0.4.2_paper1_statewise_operator/main.tex"
    main_sha = _sha256(main_path)
    expected_main_sha = current.get("main_tex_raw_sha256")
    if expected_main_sha != main_sha:
        raise RuntimeError(
            "PDF_REBIND_NOT_FINAL: main.tex SHA-256 does not match the final PDF observation"
        )
    pdf_bytes = pdf_path.read_bytes()
    pdf_sha = _sha256_bytes(pdf_bytes)
    if expected_pdf.get("raw_sha256") != pdf_sha:
        raise RuntimeError("PDF SHA-256 does not match manuscript manifest")
    if expected_pdf.get("bytes") != len(pdf_bytes):
        raise RuntimeError("PDF byte count does not match manuscript manifest")
    page_count = expected_pdf.get("page_count")
    if not isinstance(page_count, int) or page_count <= 0:
        raise RuntimeError("manuscript manifest has no positive PDF page count")
    visual_qa = current.get("visual_qa", {})
    render_dpi = visual_qa.get("render_dpi") if isinstance(visual_qa, dict) else None
    if not isinstance(render_dpi, int) or render_dpi <= 0:
        raise RuntimeError("manuscript manifest has no positive visual-QA render DPI")
    expected_diagnostics = {
        "blocking_total": 0,
        "overfull_hbox": 0,
        "undefined_reference_or_citation": 0,
        "latex_or_package_error": 0,
        "underfull_box": 0,
    }
    if current.get("diagnostics") != expected_diagnostics:
        raise RuntimeError("PDF_REBIND_NOT_FINAL: PDF diagnostics are not all zero")
    if not (
        isinstance(visual_qa, dict)
        and visual_qa.get("pages_inspected") == page_count
        and visual_qa.get("all_pages_inspected") is True
        and visual_qa.get("clipping_or_overlap_found") is False
        and visual_qa.get("intentional_draft_boxes_remain") is False
    ):
        raise RuntimeError("PDF_REBIND_NOT_FINAL: all-page visual QA is incomplete")
    if current.get("source_pdf_binding") != {
        "status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
        "source_hash_matches_current_observation": True,
        "report_hash_pinned": True,
        "publication_authorized": False,
    }:
        raise RuntimeError("PDF_REBIND_NOT_FINAL: final source/PDF binding is incomplete")
    publication_gate = manuscript.get("publication_gates", {}).get("pdf_source_rebind")
    if publication_gate != {
        "status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
        "required_before_submission_or_deposit": True,
        "completed": True,
        "publication_authorized": False,
    }:
        raise RuntimeError("PDF_REBIND_NOT_FINAL: publication gate lacks a completed rebind")

    report_binding = tex_build.get("build_report", {})
    if report_binding.get("path") != PDF_BUILD_REPORT_PATH:
        raise RuntimeError("manuscript manifest build-report path drifted")
    report_sha = _sha256(report_path)
    if report_binding.get("raw_sha256") != report_sha:
        raise RuntimeError("PDF build report SHA-256 does not match manuscript manifest")
    report_fragments = (
        f"| Pages | {page_count} |",
        f"| Bytes | {len(pdf_bytes)} |",
        f"`{pdf_sha}`",
        f"All {page_count} pages were rendered at {render_dpi} dpi and visually inspected",
        f"`{main_sha}`",
        f"`{PDF_SOURCE_PATH}`",
    )
    missing_report_fragments = [fragment for fragment in report_fragments if fragment not in report]
    if missing_report_fragments:
        raise RuntimeError(f"PDF build report binding drifted: {missing_report_fragments}")

    metadata = _pdf_metadata(pdf_bytes)
    source_text = main_path.read_text(encoding="utf-8")
    title_match = re.search(r"pdftitle=\{([^{}]+)\}", source_text)
    author_match = re.search(r"pdfauthor=\{([^{}]+)\}", source_text)
    if title_match is None or author_match is None:
        raise RuntimeError("main.tex has no pdftitle/pdfauthor metadata source")
    if metadata["title"] != title_match.group(1) or metadata["author"] != author_match.group(1):
        raise RuntimeError("PDF title/author metadata does not match main.tex")
    return {
        "source_path": PDF_SOURCE_PATH,
        "upload_name": UPLOAD_PDF_NAME,
        "output_path": expected_output,
        "pdf_sha256": pdf_sha,
        "pdf_bytes": len(pdf_bytes),
        "pdf_page_count": page_count,
        "pdf_metadata": metadata,
        "pdf_source_main_sha256": main_sha,
        "pdf_build_report_path": PDF_BUILD_REPORT_PATH,
        "pdf_build_report_sha256": report_sha,
        "manuscript_manifest_sha256": _sha256(manifest_path),
    }


def _source_records(root: Path, specs: Iterable[FileSpec]) -> list[dict[str, Any]]:
    selected = _normalise_specs(specs)
    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for spec in selected:
        source = root / Path(spec.source_path)
        if not source.is_file():
            missing.append(spec.source_path)
            continue
        records.append(
            {
                "path": spec.archive_path,
                "source_path": spec.source_path,
                "role": spec.role,
                "size_bytes": source.stat().st_size,
                "sha256": _sha256(source),
            }
        )
    if missing:
        raise FileNotFoundError(f"Paper I supplement inputs are missing: {sorted(missing)}")
    witness = root / WITNESS_SOURCE_PATH
    records.append(
        {
            "path": WITNESS_MEMBER_PATH,
            "source_path": WITNESS_SOURCE_PATH,
            "role": "compact_witness_table",
            "size_bytes": witness.stat().st_size,
            "sha256": _sha256(witness),
        }
    )
    return sorted(records, key=lambda record: record["path"])


def _supplement_manifest(
    root: Path,
    pdf_binding: dict[str, Any],
    metadata_binding: dict[str, Any],
    predraft_gate_binding: dict[str, Any],
    specs: Iterable[FileSpec] | None,
    source_commit_binding: dict[str, Any],
) -> dict[str, Any]:
    records = _source_records(
        root,
        DEFAULT_SOURCE_FILE_SPECS if specs is None else specs,
    )
    preview = source_commit_binding.get("status") == "UNBOUND_PREVIEW"
    payload: dict[str, Any] = {
        "schema_version": SUPPLEMENT_SCHEMA_VERSION,
        "bundle_version": BUNDLE_VERSION,
        "status": "UNBOUND_PREVIEW"
        if preview
        else "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING",
        "title": PAPER_TITLE,
        "primary_resource": "Paper I preprint",
        "recommended_upload_type": "Publication / Preprint",
        "archive_role": "source_reproduction_witness_and_checksums",
        "file_count": len(records),
        "files": records,
        "external_files": [
            {
                "path": UPLOAD_PDF_NAME,
                "source_path": PDF_SOURCE_PATH,
                "role": "standalone_pdf_preview",
                "size_bytes": pdf_binding["pdf_bytes"],
                "sha256": pdf_binding["pdf_sha256"],
            }
        ],
        "pdf_binding": pdf_binding,
        "metadata_binding": metadata_binding,
        "zenodo_predraft_literature_gate": predraft_gate_binding,
        "source_commit_binding": source_commit_binding,
        "owner_decision_binding": metadata_binding["owner_decision_binding"],
        "owner_decisions": metadata_binding["owner_decisions"],
        "owner_release_gates": metadata_binding["owner_release_gates"],
        "self_excluded_artifact": SUPPLEMENT_MANIFEST_PATH,
        "excluded_scope": EXCLUDED_SCOPE,
        "owner_field_values": {
            "publication_date": None,
            "license": None,
            "final_commit": None,
            "doi": None,
            "related_identifiers": [],
        },
        "full_reproduction_requires_repository": True,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def _outer_manifest(
    pdf_binding: dict[str, Any],
    metadata_binding: dict[str, Any],
    predraft_gate_binding: dict[str, Any],
    inner_supplement: dict[str, Any],
    inner_supplement_size: int,
    inner_supplement_sha256: str,
) -> dict[str, Any]:
    """Create the self-excluding manifest for a historical single archive.

    The outer manifest deliberately records the inner archive as a member and
    the final PDF as a member.  The inner manifest remains authoritative for
    its source allowlist, metadata checks, and ``source_commit_binding``;
    this layer binds those bytes to the historical single file.  The wrapper
    itself therefore remains commit-binding-free for legacy compatibility.
    """

    files = [
        {
            "path": UPLOAD_PDF_NAME,
            "source_path": PDF_SOURCE_PATH,
            "role": "final_standalone_pdf",
            "size_bytes": pdf_binding["pdf_bytes"],
            "sha256": pdf_binding["pdf_sha256"],
        },
        {
            "path": UPLOAD_SUPPLEMENT_NAME,
            "source_path": UPLOAD_SUPPLEMENT_NAME,
            "role": "inner_source_reproduction_supplement_archive",
            "size_bytes": inner_supplement_size,
            "sha256": inner_supplement_sha256,
        },
    ]
    payload: dict[str, Any] = {
        "schema_version": OUTER_SCHEMA_VERSION,
        "bundle_version": BUNDLE_VERSION,
        "status": "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING",
        "layout": SINGLE_ARCHIVE_LAYOUT,
        "zenodo_upload_files": [UPLOAD_ARCHIVE_NAME],
        "title": PAPER_TITLE,
        "primary_resource": "Paper I preprint",
        "recommended_upload_type": "Publication / Preprint",
        "archive_role": "single_archive_final_pdf_and_source_reproduction",
        "file_count": len(files),
        "files": files,
        "pdf_binding": pdf_binding,
        "metadata_binding": metadata_binding,
        "zenodo_predraft_literature_gate": predraft_gate_binding,
        "owner_decision_binding": metadata_binding["owner_decision_binding"],
        "owner_decisions": metadata_binding["owner_decisions"],
        "owner_release_gates": metadata_binding["owner_release_gates"],
        "inner_supplement_binding": {
            "path": UPLOAD_SUPPLEMENT_NAME,
            "size_bytes": inner_supplement_size,
            "sha256": inner_supplement_sha256,
            "schema_version": SUPPLEMENT_SCHEMA_VERSION,
            "manifest_semantic_digest_sha256": inner_supplement[
                "semantic_digest_sha256"
            ],
        },
        "self_excluded_artifact": OUTER_MANIFEST_PATH,
        "excluded_scope": EXCLUDED_SCOPE,
        # The historical wrapper itself remains commit-binding-free; the
        # current binding lives in the embedded supplement manifest.
        "commit_binding_embedded": False,
        "inner_commit_binding_embedded": isinstance(
            inner_supplement.get("source_commit_binding"), dict
        ),
        "commit_binding_location": "inner_supplement.source_commit_binding",
        "owner_field_values": {
            "publication_date": None,
            "license": None,
            "final_commit": None,
            "doi": None,
            "related_identifiers": [],
        },
        "full_reproduction_requires_repository": True,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def _stage_supplement(root: Path, stage: Path, manifest: dict[str, Any]) -> None:
    for record in manifest["files"]:
        source = root / Path(record["source_path"])
        destination = stage / Path(record["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    manifest_path = stage / SUPPLEMENT_MANIFEST_PATH
    manifest_path.write_bytes(_json_bytes(manifest))


def _write_tar(
    stage: Path,
    destination: Path,
    *,
    prefix: str = SUPPLEMENT_PREFIX,
    allow_pdf: bool = False,
) -> None:
    members = sorted(
        path.relative_to(stage).as_posix()
        for path in stage.rglob("*")
        if path.is_file()
    )
    if any(_is_forbidden(member) for member in members):
        raise RuntimeError("archive staging contains a forbidden member")
    pdf_members = [member for member in members if member.lower().endswith(".pdf")]
    if pdf_members and (not allow_pdf or pdf_members != [UPLOAD_PDF_NAME]):
        raise RuntimeError("archive staging contains an unexpected PDF member")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=GZIP_COMPRESSLEVEL,
            fileobj=raw,
            mtime=GZIP_MTIME,
        ) as compressed:
            with tarfile.open(
                fileobj=compressed,
                mode="w",
                format=tarfile.PAX_FORMAT,
            ) as archive:
                for relative in members:
                    source = stage / Path(relative)
                    info = tarfile.TarInfo(f"{prefix}/{relative}")
                    info.type = tarfile.REGTYPE
                    info.size = source.stat().st_size
                    info.mtime = MEMBER_MTIME
                    info.mode = MEMBER_MODE
                    info.uid = MEMBER_UID
                    info.gid = MEMBER_GID
                    info.uname = MEMBER_UNAME
                    info.gname = MEMBER_GNAME
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)


def _validate_output_dir(output_dir: Path, root: Path) -> None:
    """Refuse to overwrite an existing output tree or a file."""

    try:
        output_dir.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("--output-dir must point outside the repository root")
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError("--output-dir exists but is not a directory")
        if any(output_dir.iterdir()):
            raise ValueError(
                "--output-dir must be new or empty; refusing to overwrite existing files"
            )


def _git_blob_at_commit(root: Path, commit: str, source_path: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{source_path}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        return None
    return completed.stdout


def _validate_commit_binding(
    root: Path,
    revision: str,
    specs: Iterable[FileSpec],
) -> dict[str, Any]:
    """Bind every supplement source byte to a caller-selected Git commit.

    The compact witness table is not part of ``DEFAULT_SOURCE_FILE_SPECS``
    because it is appended by ``_source_records``.  It is appended here too,
    so a production ``--commit`` build cannot leave that automatically added
    member unbound.
    """

    commit = _resolve_commit(root, revision)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("resolved production commit is not a full 40-hex revision")
    checked: list[dict[str, Any]] = []
    optional_untracked: list[str] = []
    selected_specs = list(specs)
    if any(spec.source_path == WITNESS_SOURCE_PATH for spec in selected_specs):
        raise ValueError(
            "the compact witness table is added automatically and must not "
            "appear in commit-binding specs"
        )
    selected_specs.append(
        FileSpec(
            WITNESS_MEMBER_PATH,
            WITNESS_SOURCE_PATH,
            "compact_witness_table",
        )
    )
    for spec in selected_specs:
        if spec.source_path in COMMIT_UNTRACKED_OPTIONAL_PATHS:
            optional_untracked.append(spec.source_path)
            continue
        source = root / Path(spec.source_path)
        if not source.is_file():
            raise FileNotFoundError(
                f"commit binding source is missing from the working tree: {spec.source_path}"
            )
        blob = _git_blob_at_commit(root, commit, spec.source_path)
        if blob is None:
            raise RuntimeError(
                "commit binding source is not present in selected commit: "
                f"{spec.source_path}"
            )
        current = source.read_bytes()
        if current != blob:
            raise RuntimeError(
                "commit binding mismatch for allowlisted source: "
                f"{spec.source_path}"
            )
        checked.append(
            {
                "archive_path": spec.archive_path,
                "source_path": spec.source_path,
                "sha256": _sha256_bytes(current),
                "size_bytes": len(current),
            }
        )
    return {
        "status": "PRODUCTION_COMMIT_BOUND",
        "commit": commit,
        "repository_url": REPOSITORY_URL,
        "tree_url": None,
        "remote_visibility": "NOT_VERIFIED_BY_BUILDER",
        "checked_source_count": len(checked),
        "checked_sources": [
            {
                key: record[key]
                for key in ("source_path", "sha256", "size_bytes")
            }
            for record in sorted(checked, key=lambda item: item["archive_path"])
        ],
        "automatic_sources": [WITNESS_SOURCE_PATH],
        "optional_untracked_sources": optional_untracked,
    }


def _unbound_preview_source_binding() -> dict[str, Any]:
    """Return the explicit, non-uploadable source-binding sentinel."""

    return {
        "status": "UNBOUND_PREVIEW",
        "commit": None,
        "repository_url": REPOSITORY_URL,
        "tree_url": None,
        "remote_visibility": "NOT_VERIFIED_BY_BUILDER",
        "checked_source_count": 0,
        "checked_sources": [],
        "automatic_sources": [WITNESS_SOURCE_PATH],
        "optional_untracked_sources": sorted(COMMIT_UNTRACKED_OPTIONAL_PATHS),
    }


def build_upload_set(
    root: Path,
    output_dir: Path,
    *,
    revision: str | None = None,
    specs: Iterable[FileSpec] | None = None,
    layout: str = PDF_AND_SUPPLEMENT_LAYOUT,
) -> dict[str, Any]:
    """Create the default PDF + supplement set or an explicit legacy archive.

    ``pdf_and_supplement`` is the Paper I default because it gives Zenodo a
    directly previewable Preprint PDF without duplicating that PDF inside the
    reproducibility archive.  ``single_archive`` is retained only as an
    explicit historical candidate for offline comparison.
    """

    root = root.resolve()
    output_dir = output_dir.resolve()
    layout = {
        "pdf-and-supplement": PDF_AND_SUPPLEMENT_LAYOUT,
        "pdf_and_supplement": PDF_AND_SUPPLEMENT_LAYOUT,
        "two-file": PDF_AND_SUPPLEMENT_LAYOUT,
        "two_file": PDF_AND_SUPPLEMENT_LAYOUT,
        "single-archive": SINGLE_ARCHIVE_LAYOUT,
        "single_archive": SINGLE_ARCHIVE_LAYOUT,
    }.get(layout, layout)
    if layout not in {PDF_AND_SUPPLEMENT_LAYOUT, SINGLE_ARCHIVE_LAYOUT}:
        raise ValueError(f"unknown upload layout: {layout!r}")
    _validate_output_dir(output_dir, root)
    selected_specs = _normalise_specs(
        DEFAULT_SOURCE_FILE_SPECS if specs is None else specs
    )
    candidate_source_binding = _validate_candidate_source(root)
    pdf_binding = _validate_pdf_binding(root)
    owner_decision = _validate_owner_decision(root, pdf_binding)
    metadata_binding = _validate_metadata_template(root, owner_decision)
    predraft_gate_binding = _validate_zenodo_predraft_gate(root)
    source_commit_binding = (
        _validate_commit_binding(root, revision, selected_specs)
        if revision
        else _unbound_preview_source_binding()
    )
    packaged_commit = source_commit_binding["commit"]
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_bytes = (root / PDF_SOURCE_PATH).read_bytes()
    manifest = _supplement_manifest(
        root,
        pdf_binding,
        metadata_binding,
        predraft_gate_binding,
        selected_specs,
        source_commit_binding,
    )
    with tempfile.TemporaryDirectory(prefix="paper1-supplement-") as temporary:
        temporary_path = Path(temporary)
        _stage_supplement(root, temporary_path / "inner", manifest)
        inner_supplement_temp = temporary_path / "inner-supplement.tar.gz"
        _write_tar(temporary_path / "inner", inner_supplement_temp)
        inner_supplement_bytes = inner_supplement_temp.read_bytes()
        inner_supplement_sha = _sha256_bytes(inner_supplement_bytes)

        if layout == PDF_AND_SUPPLEMENT_LAYOUT:
            # Copy only after all fail-closed checks pass; this is a copy,
            # never a move.  The PDF remains external to the supplement and
            # is bound by the supplement manifest's PDF hash record.
            pdf_destination = output_dir / UPLOAD_PDF_NAME
            supplement_destination = output_dir / UPLOAD_SUPPLEMENT_NAME
            pdf_destination.write_bytes(pdf_bytes)
            supplement_destination.write_bytes(inner_supplement_bytes)
            return {
                "output_dir": str(output_dir),
                "layout": PDF_AND_SUPPLEMENT_LAYOUT,
                "historical_layout": False,
                "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
                "files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
                "standalone_pdf_sha256": _sha256(pdf_destination),
                "standalone_pdf_bytes": pdf_destination.stat().st_size,
                "supplement_sha256": _sha256(supplement_destination),
                "supplement_bytes": supplement_destination.stat().st_size,
                "supplement_manifest_semantic_digest_sha256": manifest[
                    "semantic_digest_sha256"
                ],
                "supplement_member_count": manifest["file_count"] + 1,
                "pdf_binding": pdf_binding,
                "metadata_binding": metadata_binding,
                "zenodo_predraft_literature_gate": predraft_gate_binding,
                "owner_decision_binding": metadata_binding["owner_decision_binding"],
                "owner_decisions": metadata_binding["owner_decisions"],
                "owner_release_gates": metadata_binding["owner_release_gates"],
                "candidate_source_binding": candidate_source_binding,
                "source_commit_binding": source_commit_binding,
                "commit_binding": source_commit_binding,
                "packaged_commit": packaged_commit,
                "status": manifest["status"],
                "owner_confirmation_required": [
                    "publication_date",
                    "doi",
                    "final_commit",
                ],
            }

        outer_manifest = _outer_manifest(
            pdf_binding,
            metadata_binding,
            predraft_gate_binding,
            manifest,
            len(inner_supplement_bytes),
            inner_supplement_sha,
        )
        outer_stage = temporary_path / "outer"
        outer_stage.mkdir(parents=True, exist_ok=True)
        (outer_stage / UPLOAD_PDF_NAME).write_bytes(pdf_bytes)
        (outer_stage / UPLOAD_SUPPLEMENT_NAME).write_bytes(inner_supplement_bytes)
        (outer_stage / OUTER_MANIFEST_PATH).write_bytes(_json_bytes(outer_manifest))
        outer_destination = output_dir / UPLOAD_ARCHIVE_NAME
        _write_tar(
            outer_stage,
            outer_destination,
            prefix=OUTER_PREFIX,
            allow_pdf=True,
        )

    return {
        "output_dir": str(output_dir),
        "layout": SINGLE_ARCHIVE_LAYOUT,
        "historical_layout": True,
        "zenodo_upload_files": [UPLOAD_ARCHIVE_NAME],
        "files": [UPLOAD_ARCHIVE_NAME],
        "outer_archive_sha256": _sha256(outer_destination),
        "outer_archive_bytes": outer_destination.stat().st_size,
        "outer_manifest_semantic_digest_sha256": outer_manifest[
            "semantic_digest_sha256"
        ],
        "standalone_pdf_sha256": pdf_binding["pdf_sha256"],
        "standalone_pdf_bytes": pdf_binding["pdf_bytes"],
        "supplement_sha256": inner_supplement_sha,
        "supplement_bytes": len(inner_supplement_bytes),
        "supplement_manifest_semantic_digest_sha256": manifest[
            "semantic_digest_sha256"
        ],
        "supplement_member_count": manifest["file_count"] + 1,
        "pdf_binding": pdf_binding,
        "metadata_binding": metadata_binding,
        "zenodo_predraft_literature_gate": predraft_gate_binding,
        "owner_decision_binding": metadata_binding["owner_decision_binding"],
        "owner_decisions": metadata_binding["owner_decisions"],
        "owner_release_gates": metadata_binding["owner_release_gates"],
        "candidate_source_binding": candidate_source_binding,
        "source_commit_binding": source_commit_binding,
        "commit_binding": source_commit_binding,
        "packaged_commit": packaged_commit,
        "status": manifest["status"],
        "owner_confirmation_required": [
            "publication_date",
            "doi",
            "final_commit",
        ],
    }


def _resolve_commit(root: Path, revision: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"git revision resolution failed for {revision!r}: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "new or empty external directory; default layout contains the "
            "standalone Preprint PDF and its supplement archive"
        ),
    )
    parser.add_argument(
        "--layout",
        choices=("pdf-and-supplement", "single-archive"),
        default="pdf-and-supplement",
        help=(
            "pdf-and-supplement (default, directly previewable Preprint PDF) "
            "or an explicit historical single-archive candidate"
        ),
    )
    binding_group = parser.add_mutually_exclusive_group(required=True)
    binding_group.add_argument(
        "--commit",
        dest="revision",
        help=(
            "owner-approved final commit; every allowlisted source byte, including "
            "the automatically added witness table, must match its Git blob"
        ),
    )
    binding_group.add_argument(
        "--unbound-preview",
        action="store_true",
        help=(
            "explicitly allow a local unbound preview build; never use this for "
            "production or Zenodo upload"
        ),
    )
    parser.add_argument(
        "--expect-supplement-sha256",
        help="fail unless the inner supplement archive has this SHA-256",
    )
    parser.add_argument(
        "--expect-pdf-sha256",
        help="fail unless the standalone PDF has this SHA-256",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    summary = build_upload_set(
        arguments.root,
        arguments.output_dir,
        revision=arguments.revision,
        layout=arguments.layout,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    expected = arguments.expect_supplement_sha256
    if expected is not None and summary["supplement_sha256"] != expected:
        print(
            "supplement sha256 mismatch: "
            f"{summary['supplement_sha256']} != {expected}"
        )
        return 1
    expected_pdf = arguments.expect_pdf_sha256
    if expected_pdf is not None:
        actual_pdf = summary.get("standalone_pdf_sha256")
        if actual_pdf != expected_pdf:
            print(f"standalone PDF sha256 mismatch: {actual_pdf} != {expected_pdf}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
