"""Verify the Paper I v0.4.2 Zenodo upload candidate offline.

The default verification target is the directly previewable standalone PDF
plus its deterministic reproduction supplement.  The historical outer archive
remains verifiable for integrity comparison but is not the recommended layout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SUPPLEMENT_SCHEMA_VERSION = "zenodo-paper1-supplement-manifest-v1"
OUTER_SCHEMA_VERSION = "zenodo-paper1-single-archive-manifest-v1"
OWNER_DECISION_SCHEMA_VERSION = "zenodo-paper1-owner-decision-v1"
SUPPLEMENT_PREFIX = "paper1-statewise-operator-v0.4.2-supplement"
OUTER_PREFIX = "paper1-statewise-operator-v0.4.2-upload"
SUPPLEMENT_MANIFEST_PATH = "upload_checksums.json"
OUTER_MANIFEST_PATH = "upload_checksums.json"
UPLOAD_PDF_NAME = "paper1_statewise_operator_v0.4.2.pdf"
UPLOAD_SUPPLEMENT_NAME = "paper1_statewise_operator_v0.4.2_supplement.tar.gz"
UPLOAD_ARCHIVE_NAME = "paper1_statewise_operator_v0.4.2_zenodo.tar.gz"
SINGLE_ARCHIVE_LAYOUT = "single_archive"
PDF_AND_SUPPLEMENT_LAYOUT = "pdf_and_supplement"
PDF_SOURCE_PATH = "output/pdf/paper1_statewise_operator_v0.4.2.pdf"
WITNESS_SOURCE_PATH = "results/v0.4.2_paper1_witness_tables.json"
PDF_BUILD_REPORT_PATH = "reports/v0.4.2_paper1_pdf_build_2026-08-07.md"
REPOSITORY_URL = "https://github.com/To-marigi/universe-theory-lab"
OWNER_DECISION_ARTIFACT_PATH = "zenodo/paper1-v0.4.2/owner_decision.json"
PREVIOUS_OWNER_DECISION_REPORT_PATH = (
    "reports/v0.4.2_paper1_owner_decision_2026-08-06.md"
)
OWNER_DECISION_REPORT_PATH = (
    "reports/v0.4.2_paper1_owner_decision_amendment_2026-08-07.md"
)
# Kept in step with the builder: the 2026-08-07 amendment also supersedes the
# final-PDF source binding, because the PDF was rebuilt after the wording audit.
OWNER_DECISION_AMENDMENT_SCOPE = [
    "upload_layout",
    "doi_handling",
    "final_pdf_source_binding",
]
DOI_POLICY = "NO_DRAFT_RESERVATION_ZENODO_REGISTERS_DOI_AT_PUBLICATION"
DOI_STATUS = "NO_DRAFT_RESERVATION_DOI_PENDING_PUBLICATION"
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
    "c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e"
)
OWNER_DECISION_PDF_BYTES = 428286
OWNER_DECISION_PDF_PAGE_COUNT = 18
WITNESS_MEMBER_PATH = f"witness/{UPLOAD_PDF_NAME.removesuffix('.pdf')}_witness_tables.json"
MEMBER_MODE = 0o644
MEMBER_UID = 0
MEMBER_GID = 0
MEMBER_UNAME = ""
MEMBER_GNAME = ""
MEMBER_MTIME = 0
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
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


def _without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}


def _safe_relative(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and not any(
        part in {"", ".", ".."} for part in path.parts
    )


def _read_member(
    archive: tarfile.TarFile,
    member: tarfile.TarInfo,
    *,
    archive_label: str = "archive",
) -> bytes:
    if not member.isfile():
        raise RuntimeError(f"{archive_label} member is not a regular file: {member.name}")
    if (
        member.mode != MEMBER_MODE
        or member.uid != MEMBER_UID
        or member.gid != MEMBER_GID
        or member.uname != MEMBER_UNAME
        or member.gname != MEMBER_GNAME
        or member.mtime != MEMBER_MTIME
    ):
        raise RuntimeError(f"{archive_label} member metadata is not canonical: {member.name}")
    handle = archive.extractfile(member)
    if handle is None:
        raise RuntimeError(f"{archive_label} member cannot be read: {member.name}")
    return handle.read()


def _archive_contents(
    archive_path: Path,
    *,
    prefix: str = SUPPLEMENT_PREFIX,
    archive_label: str = "supplement",
) -> dict[str, bytes]:
    raw = archive_path.read_bytes()
    if len(raw) < 10 or raw[3] != 0 or raw[4:8] != b"\x00\x00\x00\x00":
        raise RuntimeError(f"{archive_label} gzip header has a filename or timestamp")
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise RuntimeError(f"{archive_label} contains duplicate member names")
        prefix = f"{prefix}/"
        contents: dict[str, bytes] = {}
        for member in members:
            if not member.name.startswith(prefix):
                raise RuntimeError(
                    f"{archive_label} member is outside package prefix: {member.name}"
                )
            relative = member.name[len(prefix) :]
            if not _safe_relative(relative):
                raise RuntimeError(f"{archive_label} member has unsafe path: {member.name}")
            contents[relative] = _read_member(
                archive,
                member,
                archive_label=archive_label,
            )
        return contents


def _metadata_binding_ok(
    contents: dict[str, bytes],
    *,
    pdf_binding: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    template_bytes = contents.get("package/metadata.template.json")
    ledger_bytes = contents.get("results/v0.4.2_paper1_claim_boundary.json")
    owner_bytes = contents.get("package/owner_decision.json")
    owner_report_bytes = contents.get(OWNER_DECISION_REPORT_PATH)
    if template_bytes is None or ledger_bytes is None:
        return ["metadata template or claim ledger is missing"]
    if owner_bytes is None or owner_report_bytes is None:
        return ["owner decision artifact or report is missing"]
    try:
        template = json.loads(template_bytes.decode("utf-8"))
        ledger = json.loads(ledger_bytes.decode("utf-8"))
        owner = json.loads(owner_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"metadata/claim ledger/owner decision JSON is invalid: {exc}"]
    if (
        not isinstance(template, dict)
        or not isinstance(ledger, dict)
        or not isinstance(owner, dict)
    ):
        return ["metadata, claim ledger, and owner decision must be objects"]
    description = template.get("description")
    if not isinstance(description, str):
        errors.append("metadata description is not text")
    else:
        errors.extend(
            f"metadata description lacks {fragment!r}"
            for fragment in REQUIRED_DESCRIPTION_FRAGMENTS
            if fragment not in description
        )
    if template.get("template_role") != "UI worksheet only; not a Zenodo API payload":
        errors.append("metadata template role is not worksheet-only")
    if template.get("upload_type_ui_worksheet") != "Publication / Preprint":
        errors.append("metadata worksheet recommendation drifted")
    if template.get("related_identifiers") != []:
        errors.append("metadata relation list is not empty by default")
    if template.get("status") != "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING":
        errors.append("metadata owner-decision status drifted")
    if template.get("publication_date") is not None:
        errors.append("metadata publication_date is not null")
    if template.get("license") != "CC BY 4.0":
        errors.append("metadata Paper I license is not CC BY 4.0")
    if template.get("doi") is not None:
        errors.append("metadata DOI is not null until Zenodo publication")
    if template.get("final_commit") is not None:
        errors.append("metadata final_commit is not null before external binding")
    keywords = template.get("keywords")
    required_keywords = {
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
    if not isinstance(keywords, list) or not required_keywords <= set(keywords):
        errors.append("metadata scientific keywords are incomplete")
    additional = template.get("additional_descriptions")
    if not isinstance(additional, list) or len(additional) != 2:
        errors.append("metadata additional descriptions must have two public UI entries")
    else:
        technical, ai_note = additional
        if not isinstance(technical, dict) or technical.get("type") != "Technical info":
            errors.append("metadata technical claim-boundary description drifted")
        elif not isinstance(technical.get("description"), str) or not all(
            fragment in technical["description"]
            for fragment in (
                "C1", "C2", "C3", "C4", "C5", "N1--N6",
                "SEARCH_OPEN_NO_TERMINAL", "SOFT_RESOURCE_LIMIT_NONTERMINAL",
                "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED",
            )
        ):
            errors.append("metadata technical claim-boundary content is incomplete")
        if not isinstance(ai_note, dict) or ai_note.get("type") != "Other":
            errors.append("metadata AI additional-description type drifted")
        elif not isinstance(ai_note.get("description"), str) or not all(
            fragment in ai_note["description"]
            for fragment in (
                "human author is responsible", "AI systems are not authors",
                "not proof authorities",
            )
        ):
            errors.append("metadata AI additional-description content is incomplete")
    ai_disclosure = template.get("ai_disclosure")
    if not isinstance(ai_disclosure, dict):
        errors.append("metadata AI disclosure is missing")
    else:
        if ai_disclosure.get("ai_systems_are_authors") is not False:
            errors.append("metadata AI systems are not explicitly non-authors")
        if ai_disclosure.get("ai_systems_are_proof_authorities") is not False:
            errors.append("metadata AI systems are not explicitly outside proof authority")
    data_code = template.get("data_code_availability")
    if not isinstance(data_code, dict) or data_code.get("repository_url") != (
        "https://github.com/To-marigi/universe-theory-lab"
    ):
        errors.append("metadata data/code repository URL is missing or drifted")
    elif any(
        data_code.get(key) is not value
        for key, value in {
            "exact_commit_recorded_in_supplement_manifest_at_build": True,
            "exact_commit_recorded_in_external_receipt_at_build": True,
            "remote_commit_visibility_verified_by_builder": False,
        }.items()
    ):
        errors.append("metadata data/code commit-provenance policy drifted")
    elif "exact_commit_recorded_in_external_zenodo_metadata_at_deposit" in data_code:
        errors.append("metadata retains the superseded external-metadata commit policy")
    binding = template.get("claim_ledger_binding")
    if not isinstance(binding, dict):
        errors.append("metadata claim ledger binding is missing")
    else:
        raw_sha = _sha256_bytes(ledger_bytes)
        semantic_sha = _semantic_digest(ledger)
        if binding.get("raw_sha256") != raw_sha:
            errors.append("metadata claim ledger raw digest drifted")
        if binding.get("semantic_digest_sha256") != semantic_sha:
            errors.append("metadata claim ledger semantic digest drifted")
    owner_semantic = owner.get("semantic_digest_sha256")
    if owner.get("schema_version") != OWNER_DECISION_SCHEMA_VERSION:
        errors.append("owner decision schema version drifted")
    if not isinstance(owner_semantic, str) or _semantic_digest(
        {key: value for key, value in owner.items() if key != "semantic_digest_sha256"}
    ) != owner_semantic:
        errors.append("owner decision semantic digest drifted")
    owner_decisions = owner.get("decisions")
    expected_pdf = {
        "accepted": True,
        "source_path": PDF_SOURCE_PATH,
        "sha256": OWNER_DECISION_PDF_SHA256,
        "bytes": OWNER_DECISION_PDF_BYTES,
        "page_count": OWNER_DECISION_PDF_PAGE_COUNT,
        "status": "CURRENT_FINAL_VERIFIED_PDF_ACCEPTED",
    }
    expected_decisions = {
        "final_pdf": expected_pdf,
        "upload_layout": {
            "accepted": PDF_AND_SUPPLEMENT_LAYOUT,
            "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
            "pdf_preview_required": True,
            "legacy_single_archive_historical_only": True,
            "status": "PDF_AND_SUPPLEMENT_PREPRINT_LAYOUT_ACCEPTED",
        },
        "license": {
            "paper": "CC BY 4.0",
            "repository_software": "MIT",
            "status": "PAPER_LICENSE_APPROVED_SOFTWARE_LICENSE_UNCHANGED",
        },
        "publication_date": {
            "policy": "actual_zenodo_publication_date",
            "value": None,
            "status": "VALUE_PENDING_PUBLICATION",
        },
        "doi": {
            "policy": DOI_POLICY,
            "draft_reservation_requested": False,
            "value": None,
            "status": DOI_STATUS,
        },
        "related_identifiers": {
            "initial": [],
            "value": [],
            "status": "INITIAL_EMPTY_LIST_APPROVED",
        },
        "final_commit": {
            "policy": "external_at_deposit_build_cycle",
            "value": None,
            "status": "VALUE_PENDING_SELECTED_COMMIT",
        },
    }
    if owner_decisions != expected_decisions:
        errors.append("owner decision choices drifted")
    if owner.get("decision_date") != "2026-08-07":
        errors.append("owner decision date drifted")
    if owner.get("status") != "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING":
        errors.append("owner decision release status drifted")
    authority = owner.get("authority")
    if not isinstance(authority, dict) or (
        authority.get("release_actions_not_authorized") is not True
    ):
        errors.append("owner decision release actions are not kept unauthorized")
    elif authority.get("amends_report") != PREVIOUS_OWNER_DECISION_REPORT_PATH:
        errors.append("owner decision amendment provenance drifted")
    elif authority.get("amendment_scope") != OWNER_DECISION_AMENDMENT_SCOPE:
        errors.append("owner decision amendment scope drifted")
    expected_gates = {
        "draft_created": False,
        "doi_reserved": False,
        "freeze_executed": False,
        "submission_approved": False,
        "deposit_executed": False,
        "published": False,
    }
    if owner.get("release_gates") != expected_gates:
        errors.append("owner decision release gates drifted")
    owner_binding = template.get("owner_decision_binding")
    expected_binding = {
        "path": OWNER_DECISION_ARTIFACT_PATH,
        "report_path": OWNER_DECISION_REPORT_PATH,
        "raw_sha256": _sha256_bytes(owner_bytes),
        "semantic_digest_sha256": owner_semantic,
        "report_raw_sha256": _sha256_bytes(owner_report_bytes),
        "decision_date": "2026-08-07",
    }
    if owner_binding != expected_binding:
        errors.append("metadata owner decision binding drifted")
    if template.get("publication_date") != expected_decisions["publication_date"]["value"]:
        errors.append("metadata publication-date value disagrees with owner decision")
    if template.get("license") != expected_decisions["license"]["paper"]:
        errors.append("metadata license value disagrees with owner decision")
    if template.get("doi") != expected_decisions["doi"]["value"]:
        errors.append("metadata DOI value disagrees with owner decision")
    if template.get("doi_policy") != expected_decisions["doi"]:
        errors.append("metadata DOI policy disagrees with owner decision")
    if template.get("related_identifiers") != expected_decisions["related_identifiers"]["value"]:
        errors.append("metadata relations disagree with owner decision")
    if template.get("final_commit") != expected_decisions["final_commit"]["value"]:
        errors.append("metadata final commit value disagrees with owner decision")
    if pdf_binding is not None:
        if (
            pdf_binding.get("pdf_sha256") != expected_pdf["sha256"]
            or pdf_binding.get("pdf_bytes") != expected_pdf["bytes"]
            or pdf_binding.get("pdf_page_count") != expected_pdf["page_count"]
        ):
            errors.append("PDF binding disagrees with accepted owner decision")
    report_text = owner_report_bytes.decode("utf-8", errors="replace")
    for fragment in (
        "# Paper I v0.4.2 owner decision amendment — 2026-08-07",
        OWNER_DECISION_PDF_SHA256,
        "CC BY 4.0",
        "supersedes only the upload-layout, DOI",
        "final-PDF source-binding portions of the earlier record",
        "The final PDF was rebuilt twice on this date",
        "the owner completed its all-page visual QA",
        "The owner directed the second change and its rebuild.",
        "an owner acceptance of these exact bytes is not yet recorded",
        "The production upload list is",
        "exactly `paper1_statewise_operator_v0.4.2.pdf`",
        "paper1_statewise_operator_v0.4.2.pdf",
        "paper1_statewise_operator_v0.4.2_supplement.tar.gz",
        "DOI policy is **no draft reservation**",
        "No, I need one",
        "Zenodo assigns/registers the DOI at publication",
        "No Zenodo form value or file was submitted or saved.",
        "Draft creation,",
        "publication have not been",
        "No DOI reservation is requested.",
    ):
        if fragment not in report_text:
            errors.append(f"owner decision report lacks {fragment!r}")
    return errors


def _source_commit_binding_errors(
    manifest: dict[str, Any],
    records: Any,
) -> list[str]:
    """Fail closed on the embedded production or unbound source binding."""

    errors: list[str] = []
    binding = manifest.get("source_commit_binding")
    if not isinstance(binding, dict):
        return ["source_commit_binding is missing"]

    status = binding.get("status")
    expected_automatic = [WITNESS_SOURCE_PATH]
    optional = binding.get("optional_untracked_sources")
    if not isinstance(optional, list) or any(
        not isinstance(path, str) or not _safe_relative(path) for path in optional
    ):
        errors.append("source_commit_binding optional_untracked_sources is malformed")
    elif len(optional) != len(set(optional)):
        errors.append("source_commit_binding optional_untracked_sources has duplicates")

    if status == "UNBOUND_PREVIEW":
        if manifest.get("status") != "UNBOUND_PREVIEW":
            errors.append("UNBOUND_PREVIEW source binding requires UNBOUND_PREVIEW manifest status")
        if binding.get("commit") is not None:
            errors.append("UNBOUND_PREVIEW source binding commit must be null")
        if binding.get("repository_url") != REPOSITORY_URL:
            errors.append("UNBOUND_PREVIEW repository URL drifted")
        if binding.get("tree_url") is not None:
            errors.append("UNBOUND_PREVIEW tree URL must be null")
        if binding.get("remote_visibility") != "NOT_VERIFIED_BY_BUILDER":
            errors.append("UNBOUND_PREVIEW remote visibility status drifted")
        if binding.get("checked_source_count") != 0:
            errors.append("UNBOUND_PREVIEW checked_source_count must be zero")
        if binding.get("checked_sources") != []:
            errors.append("UNBOUND_PREVIEW checked_sources must be empty")
        if binding.get("automatic_sources") != expected_automatic:
            errors.append("UNBOUND_PREVIEW automatic witness binding drifted")
        errors.append("UNBOUND_PREVIEW supplement is never eligible for upload")
        return errors

    if status != "PRODUCTION_COMMIT_BOUND":
        errors.append("source_commit_binding status is not production-bound")
    if manifest.get("status") != "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING":
        errors.append("production source binding requires the owner-pending manifest status")
    commit = binding.get("commit")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        errors.append("production source binding commit must be a full 40-hex revision")
    if binding.get("repository_url") != REPOSITORY_URL:
        errors.append("production source binding repository URL drifted")
    if binding.get("tree_url") is not None:
        errors.append(
            "production source binding tree URL must remain null until remote verification"
        )
    if binding.get("remote_visibility") != "NOT_VERIFIED_BY_BUILDER":
        errors.append("production source binding remote visibility status drifted")

    checked = binding.get("checked_sources")
    count = binding.get("checked_source_count")
    if not isinstance(checked, list) or isinstance(count, bool) or not isinstance(count, int):
        errors.append("production source binding checked sources/count are malformed")
        checked = []
    elif count != len(checked):
        errors.append(
            "production source binding checked_source_count does not match checked_sources"
        )

    normalised_checked: list[dict[str, Any]] = []
    if isinstance(checked, list):
        for item in checked:
            if not isinstance(item, dict) or set(item) != {"source_path", "sha256", "size_bytes"}:
                errors.append("production source binding checked_sources record is malformed")
                continue
            source_path = item["source_path"]
            sha256 = item["sha256"]
            size_bytes = item["size_bytes"]
            if not isinstance(source_path, str) or not _safe_relative(source_path):
                errors.append("production source binding checked source path is unsafe")
            if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
                errors.append("production source binding checked source SHA-256 is malformed")
            if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
                errors.append("production source binding checked source size is malformed")
            normalised_checked.append(
                {
                    "source_path": source_path,
                    "sha256": sha256,
                    "size_bytes": size_bytes,
                }
            )

    manifest_projection: list[dict[str, Any]] = []
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict):
                errors.append("supplement manifest files contains a non-object record")
                continue
            manifest_projection.append(
                {
                    "source_path": record.get("source_path"),
                    "sha256": record.get("sha256"),
                    "size_bytes": record.get("size_bytes"),
                }
            )
    else:
        errors.append("supplement manifest files must be a list for source binding")
    if normalised_checked != manifest_projection:
        errors.append(
            "production source binding checked_sources do not exactly match manifest.files"
        )
    checked_paths = {item.get("source_path") for item in normalised_checked}
    if isinstance(optional, list) and any(
        path in checked_paths for path in optional if isinstance(path, str)
    ):
        errors.append("production source binding optional sources overlap checked sources")

    if binding.get("automatic_sources") != expected_automatic:
        errors.append("production source binding automatic witness list drifted")
    witness_records = [
        record
        for record in records
        if isinstance(record, dict) and record.get("source_path") == WITNESS_SOURCE_PATH
    ] if isinstance(records, list) else []
    if len(witness_records) != 1 or witness_records[0].get("role") != "compact_witness_table":
        errors.append("production source binding automatic witness record is missing")
    if not any(
        item.get("source_path") == WITNESS_SOURCE_PATH for item in normalised_checked
    ):
        errors.append("production source binding checked_sources omit the automatic witness")
    return errors


def _predraft_predecessor_binding() -> dict[str, Any]:
    """Return the immutable 1123Z documents retained as supplemental history."""

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


def _predraft_gate_errors(
    contents: dict[str, bytes],
    gate_binding: Any,
) -> list[str]:
    """Verify the report/note binding and excluded-artifact contract."""

    errors: list[str] = []
    if not isinstance(gate_binding, dict):
        return ["Zenodo predraft literature gate binding is missing"]
    expected_scalars = {
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
        "tracked_exact_ids": ["arXiv:2607.26672", "arXiv:2603.25503"],
        "reviewed_delta_contract": ZENODO_PREDRAFT_DELTA_CONTRACT,
    }
    for key, expected in expected_scalars.items():
        if gate_binding.get(key) != expected:
            errors.append(f"Zenodo predraft binding drifted: {key}")

    expected_documents = (
        ("report", ZENODO_PREDRAFT_REPORT_PATH, "HUMAN_REPORT_INCLUDED_IN_ZENODO_SUPPLEMENT"),
        ("research_note", ZENODO_PREDRAFT_NOTE_PATH, "RESEARCH_NOTE_INCLUDED_IN_ZENODO_SUPPLEMENT"),
    )
    report_text: str | None = None
    note_text: str | None = None
    for key, path, expected_role in expected_documents:
        record = gate_binding.get(key)
        if not isinstance(record, dict):
            errors.append(f"Zenodo predraft {key} binding is missing")
            continue
        if record.get("path") != path or record.get("role") != expected_role:
            errors.append(f"Zenodo predraft {key} path/role drifted")
        expected_sha, expected_bytes = ZENODO_PREDRAFT_ARTIFACT_HASHES[path]
        if record.get("raw_sha256") != expected_sha or record.get("bytes") != expected_bytes:
            errors.append(f"Zenodo predraft {key} hash/size drifted")
        payload = contents.get(path)
        if payload is None:
            errors.append(f"Zenodo predraft {key} is missing from supplement")
        else:
            if _sha256_bytes(payload) != expected_sha or len(payload) != expected_bytes:
                errors.append(f"Zenodo predraft {key} bytes do not match binding")
            text = payload.decode("utf-8", errors="replace")
            if key == "report":
                report_text = text
            else:
                note_text = text

    predecessor = _predraft_predecessor_binding()
    if gate_binding.get("historical_predecessor") != predecessor:
        errors.append("Zenodo predraft historical predecessor binding drifted")
    for key in ("report", "research_note"):
        record = predecessor[key]
        path = record["path"]
        payload = contents.get(path)
        if payload is None:
            errors.append(f"Zenodo predraft historical {key} is missing from supplement")
        elif (
            _sha256_bytes(payload) != record["raw_sha256"]
            or len(payload) != record["bytes"]
        ):
            errors.append(f"Zenodo predraft historical {key} bytes do not match binding")

    normalizer = gate_binding.get("normalizer")
    expected_normalizer_sha, expected_normalizer_bytes = ZENODO_PREDRAFT_ARTIFACT_HASHES[
        ZENODO_PREDRAFT_NORMALIZER_PATH
    ]
    if not isinstance(normalizer, dict) or normalizer != {
        "path": ZENODO_PREDRAFT_NORMALIZER_PATH,
        "raw_sha256": expected_normalizer_sha,
        "bytes": expected_normalizer_bytes,
        "check_command": (
            ".venv\\Scripts\\python.exe "
            "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py "
            "--check"
        ),
        "role": "REPOSITORY_REPRODUCTION_SCRIPT_NOT_INCLUDED_IN_SUPPLEMENT",
    }:
        errors.append("Zenodo predraft normalizer binding drifted")

    expected_excluded = [
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
    if gate_binding.get("excluded_artifacts") != expected_excluded:
        errors.append("Zenodo predraft excluded-artifact bindings drifted")
    for record in expected_excluded:
        if record["path"] in contents:
            errors.append(
                "Zenodo predraft raw/derived artifact must be excluded from supplement: "
                f"{record['path']}"
            )
    expected_policy = {
        "current_authority_paths": [ZENODO_PREDRAFT_REPORT_PATH, ZENODO_PREDRAFT_NOTE_PATH],
        "historical_predecessor_paths": [
            ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
            ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
        ],
        "excluded_raw_and_derived_paths": [record["path"] for record in expected_excluded],
    }
    if gate_binding.get("supplement_member_policy") != expected_policy:
        errors.append("Zenodo predraft supplement member policy drifted")

    if report_text is not None:
        for fragment in (
            ZENODO_PREDRAFT_GATE_STATUS,
            ZENODO_PREDRAFT_SOURCE_ID,
            "Versioned-ID additions: none.  Missing versioned IDs: none.",
            "Title deltas: none.  Abstract-hash deltas: none.  Category deltas: none.",
            "Version replacements: none.  Screening-decision deltas: none.",
            "arXiv:2603.25503v1",
            "arXiv:2607.26672v1",
        ):
            if fragment not in report_text:
                errors.append(f"Zenodo predraft report lacks {fragment!r}")
    if note_text is not None:
        for fragment in (
            ZENODO_PREDRAFT_SOURCE_ID,
            ZENODO_PREDRAFT_FEED_CUTOFF,
            "no added or missing versioned ID",
            "same 28 rule-triggered title/abstract records",
        ):
            if fragment not in note_text:
                errors.append(f"Zenodo predraft research note lacks {fragment!r}")
    return errors


def verify_supplement_archive(
    archive_path: Path,
    *,
    standalone_pdf: Path | None = None,
    allow_legacy_historical: bool = False,
) -> dict[str, Any]:
    """Verify the supplement, optionally in explicit legacy-integrity mode."""

    archive_path = archive_path.resolve()
    contents = _archive_contents(archive_path)
    manifest_bytes = contents.get(SUPPLEMENT_MANIFEST_PATH)
    if manifest_bytes is None:
        raise RuntimeError("supplement is missing upload_checksums.json")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"upload_checksums.json is invalid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("upload_checksums.json must be an object")
    recorded_digest = manifest.get("semantic_digest_sha256")
    digest_intact = (
        isinstance(recorded_digest, str)
        and _semantic_digest(_without_digest(manifest)) == recorded_digest
    )
    records = manifest.get("files")
    external = manifest.get("external_files")
    if not isinstance(records, list) or not isinstance(external, list):
        raise RuntimeError("upload_checksums.json files/external_files must be lists")
    expected: dict[str, dict[str, Any]] = {}
    malformed: list[str] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            malformed.append(repr(record))
            continue
        path = record["path"]
        if not _safe_relative(path) or path in expected:
            malformed.append(path)
            continue
        expected[path] = record
    missing = sorted(set(expected) - (set(contents) - {SUPPLEMENT_MANIFEST_PATH}))
    unexpected = sorted(set(contents) - set(expected) - {SUPPLEMENT_MANIFEST_PATH})
    mismatched: list[dict[str, Any]] = []
    forbidden: list[str] = []
    for path, record in sorted(expected.items()):
        if path.startswith(FORBIDDEN_ARCHIVE_PREFIXES) or path.lower().endswith(".pdf"):
            forbidden.append(path)
        if path not in contents:
            continue
        actual = contents[path]
        actual_sha = _sha256_bytes(actual)
        if record.get("sha256") != actual_sha or record.get("size_bytes") != len(actual):
            mismatched.append(
                {
                    "path": path,
                    "recorded_sha256": record.get("sha256"),
                    "actual_sha256": actual_sha,
                    "recorded_size_bytes": record.get("size_bytes"),
                    "actual_size_bytes": len(actual),
                }
            )
    external_errors: list[str] = []
    if len(external) != 1 or not isinstance(external[0], dict):
        external_errors.append("exactly one standalone PDF external record is required")
    else:
        pdf_record = external[0]
        if pdf_record.get("path") != UPLOAD_PDF_NAME:
            external_errors.append("standalone PDF external path drifted")
        pdf_binding = manifest.get("pdf_binding")
        if not isinstance(pdf_binding, dict):
            external_errors.append("PDF binding record is missing")
        else:
            if pdf_binding.get("source_path") != PDF_SOURCE_PATH:
                external_errors.append("PDF source path drifted")
            if pdf_binding.get("output_path") != PDF_SOURCE_PATH:
                external_errors.append("PDF output path drifted")
            if pdf_binding.get("pdf_build_report_path") != PDF_BUILD_REPORT_PATH:
                external_errors.append("PDF build report path drifted")
        if standalone_pdf is not None:
            if not standalone_pdf.is_file():
                external_errors.append("standalone PDF file is missing")
            else:
                actual_size = standalone_pdf.stat().st_size
                actual_sha = _sha256(standalone_pdf)
                if pdf_record.get("size_bytes") != actual_size:
                    external_errors.append("standalone PDF byte count mismatch")
                if pdf_record.get("sha256") != actual_sha:
                    external_errors.append("standalone PDF SHA-256 mismatch")
        else:
            external_errors.append("standalone PDF was not supplied for external binding")

    if allow_legacy_historical:
        metadata_errors: list[str] = []
        predraft_gate_errors: list[str] = []
        source_commit_binding_errors: list[str] = []
    else:
        metadata_errors = _metadata_binding_ok(
            contents,
            pdf_binding=manifest.get("pdf_binding")
            if isinstance(manifest.get("pdf_binding"), dict)
            else None,
        )
        predraft_gate_errors = _predraft_gate_errors(
            contents,
            manifest.get("zenodo_predraft_literature_gate"),
        )
        source_commit_binding_errors = _source_commit_binding_errors(manifest, records)
    owner_bytes = contents.get("package/owner_decision.json")
    owner_report_bytes = contents.get(OWNER_DECISION_REPORT_PATH)
    if not allow_legacy_historical and owner_bytes is not None and owner_report_bytes is not None:
        try:
            owner = json.loads(owner_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            owner = None
        if isinstance(owner, dict):
            expected_owner_binding = {
                "path": OWNER_DECISION_ARTIFACT_PATH,
                "report_path": OWNER_DECISION_REPORT_PATH,
                "raw_sha256": _sha256_bytes(owner_bytes),
                "semantic_digest_sha256": owner.get("semantic_digest_sha256"),
                "report_raw_sha256": _sha256_bytes(owner_report_bytes),
                "decision_date": owner.get("decision_date"),
            }
            if manifest.get("owner_decision_binding") != expected_owner_binding:
                metadata_errors.append("supplement owner decision binding drifted")
            if manifest.get("owner_decisions") != owner.get("decisions"):
                metadata_errors.append("supplement owner decisions drifted")
            if manifest.get("owner_release_gates") != owner.get("release_gates"):
                metadata_errors.append("supplement owner release gates drifted")
    passed = bool(
        manifest.get("schema_version") == SUPPLEMENT_SCHEMA_VERSION
        and manifest.get("status")
        == "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING"
        and manifest.get("self_excluded_artifact") == SUPPLEMENT_MANIFEST_PATH
        and manifest.get("file_count") == len(expected)
        and manifest.get("recommended_upload_type") == "Publication / Preprint"
        and manifest.get("primary_resource") == "Paper I preprint"
        and digest_intact
        and not malformed
        and not missing
        and not unexpected
        and not mismatched
        and not forbidden
        and not external_errors
        and not metadata_errors
        and not predraft_gate_errors
        and not source_commit_binding_errors
        and SUPPLEMENT_MANIFEST_PATH not in expected
    )
    return {
        "passed": passed,
        "archive": str(archive_path),
        "manifest_semantic_digest_sha256": recorded_digest,
        "manifest_semantic_digest_intact": digest_intact,
        "expected_file_count": len(expected) + 1,
        "verified_file_count": len(expected) - len(missing) - len(mismatched),
        "missing_files": missing,
        "mismatched_files": mismatched,
        "unexpected_files": unexpected,
        "malformed_records": malformed,
        "forbidden_members": forbidden,
        "pdf_members": sorted(
            path for path in contents if path.lower().endswith(".pdf")
        ),
        "external_pdf_errors": external_errors,
        "metadata_errors": metadata_errors,
        "zenodo_predraft_gate_errors": predraft_gate_errors,
        "source_commit_binding_errors": source_commit_binding_errors,
        "historical_integrity_only": allow_legacy_historical,
    }


def _manifest_from_contents(contents: dict[str, bytes], label: str) -> dict[str, Any]:
    manifest_bytes = contents.get(SUPPLEMENT_MANIFEST_PATH)
    if manifest_bytes is None:
        raise RuntimeError(f"{label} is missing upload_checksums.json")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} upload_checksums.json is invalid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError(f"{label} upload_checksums.json must be an object")
    return manifest


def verify_single_archive(archive_path: Path) -> dict[str, Any]:
    """Verify one deterministic outer archive containing PDF + supplement."""

    archive_path = archive_path.resolve()
    try:
        contents = _archive_contents(
            archive_path,
            prefix=OUTER_PREFIX,
            archive_label="outer archive",
        )
    except (OSError, RuntimeError, tarfile.TarError) as exc:
        return {
            "passed": False,
            "archive": str(archive_path),
            "error": str(exc),
        }
    try:
        manifest = _manifest_from_contents(contents, "outer archive")
    except RuntimeError as exc:
        return {
            "passed": False,
            "archive": str(archive_path),
            "error": str(exc),
        }

    recorded_digest = manifest.get("semantic_digest_sha256")
    digest_intact = (
        isinstance(recorded_digest, str)
        and _semantic_digest(_without_digest(manifest)) == recorded_digest
    )
    records = manifest.get("files")
    malformed: list[str] = []
    expected: dict[str, dict[str, Any]] = {}
    if not isinstance(records, list):
        malformed.append("files is not a list")
    else:
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                malformed.append(repr(record))
                continue
            path = record["path"]
            if not _safe_relative(path) or path in expected:
                malformed.append(path)
                continue
            expected[path] = record
    actual_members = set(contents) - {OUTER_MANIFEST_PATH}
    missing = sorted(set(expected) - actual_members)
    unexpected = sorted(actual_members - set(expected))
    mismatched: list[dict[str, Any]] = []
    forbidden: list[str] = []
    for path, record in sorted(expected.items()):
        if path.startswith(FORBIDDEN_ARCHIVE_PREFIXES):
            forbidden.append(path)
        if path.lower().endswith(".pdf") and path != UPLOAD_PDF_NAME:
            forbidden.append(path)
        if path not in contents:
            continue
        actual = contents[path]
        actual_sha = _sha256_bytes(actual)
        if record.get("sha256") != actual_sha or record.get("size_bytes") != len(actual):
            mismatched.append(
                {
                    "path": path,
                    "recorded_sha256": record.get("sha256"),
                    "actual_sha256": actual_sha,
                    "recorded_size_bytes": record.get("size_bytes"),
                    "actual_size_bytes": len(actual),
                }
            )
    pdf_members = sorted(path for path in actual_members if path.lower().endswith(".pdf"))
    if pdf_members != [UPLOAD_PDF_NAME]:
        forbidden.extend(pdf_members)

    binding_errors: list[str] = []
    if manifest.get("schema_version") != OUTER_SCHEMA_VERSION:
        binding_errors.append("outer manifest schema version drifted")
    if manifest.get("status") != "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING":
        binding_errors.append("outer owner-decision status drifted")
    if manifest.get("layout") != SINGLE_ARCHIVE_LAYOUT:
        binding_errors.append("outer manifest layout is not single_archive")
    if manifest.get("zenodo_upload_files") != [UPLOAD_ARCHIVE_NAME]:
        binding_errors.append("outer Zenodo upload file list drifted")
    if manifest.get("self_excluded_artifact") != OUTER_MANIFEST_PATH:
        binding_errors.append("outer self-excluded artifact drifted")
    if manifest.get("file_count") != len(expected):
        binding_errors.append("outer file_count does not match its records")
    if manifest.get("recommended_upload_type") != "Publication / Preprint":
        binding_errors.append("outer recommended upload type drifted")
    if manifest.get("primary_resource") != "Paper I preprint":
        binding_errors.append("outer primary resource drifted")
    if manifest.get("commit_binding_embedded") is not False:
        binding_errors.append("outer manifest must not embed a commit binding")
    for forbidden_key in ("commit", "packaged_commit", "commit_binding"):
        if forbidden_key in manifest:
            binding_errors.append(f"outer manifest embeds forbidden key: {forbidden_key}")

    inner_summary: dict[str, Any]
    inner_binding_errors: list[str] = []
    inner_manifest: dict[str, Any] | None = None
    inner_bytes = contents.get(UPLOAD_SUPPLEMENT_NAME)
    pdf_bytes = contents.get(UPLOAD_PDF_NAME)
    if inner_bytes is None or pdf_bytes is None:
        inner_summary = {
            "passed": False,
            "error": "outer archive must contain both final PDF and supplement archive",
        }
    else:
        with tempfile.TemporaryDirectory(prefix="paper1-verify-outer-") as temporary:
            temp_root = Path(temporary)
            inner_path = temp_root / UPLOAD_SUPPLEMENT_NAME
            pdf_path = temp_root / UPLOAD_PDF_NAME
            inner_path.write_bytes(inner_bytes)
            pdf_path.write_bytes(pdf_bytes)
            try:
                inner_contents = _archive_contents(inner_path)
                inner_manifest = _manifest_from_contents(inner_contents, "inner supplement")
                inner_summary = verify_supplement_archive(
                    inner_path,
                    standalone_pdf=pdf_path,
                    allow_legacy_historical="source_commit_binding" not in inner_manifest,
                )
            except (OSError, RuntimeError, tarfile.TarError) as exc:
                inner_summary = {"passed": False, "error": str(exc)}
        inner_binding = manifest.get("inner_supplement_binding")
        if not isinstance(inner_binding, dict):
            inner_binding_errors.append("inner supplement binding is missing")
        else:
            if inner_binding.get("path") != UPLOAD_SUPPLEMENT_NAME:
                inner_binding_errors.append("inner supplement path drifted")
            if inner_binding.get("size_bytes") != len(inner_bytes):
                inner_binding_errors.append("inner supplement byte count mismatch")
            if inner_binding.get("sha256") != _sha256_bytes(inner_bytes):
                inner_binding_errors.append("inner supplement SHA-256 mismatch")
            if inner_manifest is not None:
                if inner_binding.get("schema_version") != inner_manifest.get("schema_version"):
                    inner_binding_errors.append("inner supplement schema binding drifted")
                if inner_binding.get("manifest_semantic_digest_sha256") != inner_manifest.get(
                    "semantic_digest_sha256"
                ):
                    inner_binding_errors.append("inner supplement manifest digest mismatch")
        if inner_manifest is not None:
            outer_pdf_binding = manifest.get("pdf_binding")
            if outer_pdf_binding != inner_manifest.get("pdf_binding"):
                inner_binding_errors.append("outer and inner PDF bindings differ")
            if "inner_commit_binding_embedded" in manifest:
                expected_inner_binding = isinstance(
                    inner_manifest.get("source_commit_binding"), dict
                )
                if manifest.get("inner_commit_binding_embedded") is not expected_inner_binding:
                    inner_binding_errors.append(
                        "outer inner_commit_binding_embedded flag disagrees with inner manifest"
                    )
                if manifest.get("commit_binding_location") != (
                    "inner_supplement.source_commit_binding"
                ):
                    inner_binding_errors.append("outer commit binding location drifted")
            for owner_key in (
                "owner_decision_binding",
                "owner_decisions",
                "owner_release_gates",
                "zenodo_predraft_literature_gate",
            ):
                if manifest.get(owner_key) != inner_manifest.get(owner_key):
                    inner_binding_errors.append(f"outer and inner {owner_key} differ")

    passed = bool(
        digest_intact
        and not malformed
        and not missing
        and not unexpected
        and not mismatched
        and not forbidden
        and not binding_errors
        and not inner_binding_errors
        and inner_summary.get("passed") is True
    )
    return {
        "passed": passed,
        "archive": str(archive_path),
        "layout": manifest.get("layout"),
        "zenodo_upload_files": manifest.get("zenodo_upload_files"),
        "manifest_semantic_digest_sha256": recorded_digest,
        "manifest_semantic_digest_intact": digest_intact,
        "expected_file_count": len(expected) + 1,
        "verified_file_count": len(expected) - len(missing) - len(mismatched),
        "missing_files": missing,
        "mismatched_files": mismatched,
        "unexpected_files": unexpected,
        "malformed_records": malformed,
        "forbidden_members": sorted(set(forbidden)),
        "pdf_members": pdf_members,
        "binding_errors": binding_errors + inner_binding_errors,
        "inner_supplement": inner_summary,
    }


def verify_pdf_and_supplement_output(output_dir: Path) -> dict[str, Any]:
    """Verify the default standalone Preprint PDF plus supplement layout."""

    output_dir = output_dir.resolve()
    if not output_dir.is_dir():
        raise FileNotFoundError(f"upload output directory is missing: {output_dir}")
    expected = {UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME}
    actual = {child.name for child in output_dir.iterdir()}
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    pdf_name_safe = "draft" not in UPLOAD_PDF_NAME.lower()
    supplement_summary: dict[str, Any]
    if missing:
        supplement_summary = {
            "passed": False,
            "missing_files": missing,
            "unexpected_files": unexpected,
        }
    else:
        supplement_summary = verify_supplement_archive(
            output_dir / UPLOAD_SUPPLEMENT_NAME,
            standalone_pdf=output_dir / UPLOAD_PDF_NAME,
        )
    passed = bool(
        not missing
        and not unexpected
        and pdf_name_safe
        and supplement_summary["passed"]
    )
    return {
        "passed": passed,
        "output_dir": str(output_dir),
        "layout": PDF_AND_SUPPLEMENT_LAYOUT,
        "historical_layout": False,
        "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
        "missing_files": missing,
        "unexpected_files": unexpected,
        "standalone_pdf_name_safe": pdf_name_safe,
        "supplement": supplement_summary,
    }


def verify_upload_directory(output_dir: Path) -> dict[str, Any]:
    """Verify the default PDF-plus-supplement directory or a legacy archive."""

    output_dir = output_dir.resolve()
    if not output_dir.is_dir():
        raise FileNotFoundError(f"upload output directory is missing: {output_dir}")
    actual = {child.name for child in output_dir.iterdir()}
    if actual == {UPLOAD_ARCHIVE_NAME}:
        archive_summary = verify_single_archive(output_dir / UPLOAD_ARCHIVE_NAME)
        return {
            "passed": False,
            "integrity_passed": archive_summary["passed"],
            "output_dir": str(output_dir),
            "layout": SINGLE_ARCHIVE_LAYOUT,
            "historical_layout": True,
            "zenodo_upload_files": [UPLOAD_ARCHIVE_NAME],
            "error": (
                "historical single archive is integrity-checkable but is not an "
                "eligible Paper I Zenodo upload layout; use --archive for an "
                "explicit offline integrity check"
            ),
            "archive": archive_summary,
        }
    if actual == {UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME}:
        return verify_pdf_and_supplement_output(output_dir)
    expected = {UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME}
    return {
        "passed": False,
        "output_dir": str(output_dir),
        "layout": PDF_AND_SUPPLEMENT_LAYOUT,
        "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
        "missing_files": sorted(expected - actual),
        "unexpected_files": sorted(actual - expected),
        "error": "output directory must contain exactly the standalone PDF and supplement archive",
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--root",
        type=Path,
        help="upload output directory; strict default requires the PDF and supplement archive",
    )
    group.add_argument(
        "--archive",
        type=Path,
        help="historical outer archive (or an inner supplement when --pdf is supplied)",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="standalone PDF for external binding when verifying an inner supplement",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    if arguments.archive is not None:
        if arguments.pdf is not None:
            archive_contents = _archive_contents(arguments.archive)
            archive_manifest = _manifest_from_contents(archive_contents, "supplement")
            summary = verify_supplement_archive(
                arguments.archive,
                standalone_pdf=arguments.pdf,
                allow_legacy_historical="source_commit_binding" not in archive_manifest,
            )
        else:
            summary = verify_single_archive(arguments.archive)
    else:
        summary = verify_upload_directory(arguments.root)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
