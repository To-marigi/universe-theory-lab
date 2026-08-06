"""Verify the Paper I v0.4.2 Zenodo upload candidate offline.

The default verification target is one deterministic outer archive.  The
historical standalone-PDF plus supplement directory is accepted only when the
caller explicitly supplies the owner-waiver flag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SUPPLEMENT_SCHEMA_VERSION = "zenodo-paper1-supplement-manifest-v1"
OUTER_SCHEMA_VERSION = "zenodo-paper1-single-archive-manifest-v1"
SUPPLEMENT_PREFIX = "paper1-statewise-operator-v0.4.2-supplement"
OUTER_PREFIX = "paper1-statewise-operator-v0.4.2-upload"
SUPPLEMENT_MANIFEST_PATH = "upload_checksums.json"
OUTER_MANIFEST_PATH = "upload_checksums.json"
UPLOAD_PDF_NAME = "paper1_statewise_operator_v0.4.2.pdf"
UPLOAD_SUPPLEMENT_NAME = "paper1_statewise_operator_v0.4.2_supplement.tar.gz"
UPLOAD_ARCHIVE_NAME = "paper1_statewise_operator_v0.4.2_zenodo.tar.gz"
SINGLE_ARCHIVE_LAYOUT = "single_archive"
TWO_FILE_OWNER_WAIVER_LAYOUT = "two_file_owner_waiver"
PDF_SOURCE_PATH = "output/pdf/paper1_statewise_operator_v0.4.2.pdf"
PDF_BUILD_REPORT_PATH = "reports/v0.4.2_paper1_pdf_build_2026-08-06.md"
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
    "QQ",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "N1--N6",
    "SEARCH_OPEN_NO_TERMINAL",
    "SOFT_RESOURCE_LIMIT_NONTERMINAL",
    "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED",
    "third-party reference PDFs/texts",
    "human author is responsible",
    "AI systems are not authors",
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


def _metadata_binding_ok(contents: dict[str, bytes]) -> list[str]:
    errors: list[str] = []
    template_bytes = contents.get("package/metadata.template.json")
    ledger_bytes = contents.get("results/v0.4.2_paper1_claim_boundary.json")
    if template_bytes is None or ledger_bytes is None:
        return ["metadata template or claim ledger is missing"]
    try:
        template = json.loads(template_bytes.decode("utf-8"))
        ledger = json.loads(ledger_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"metadata/claim ledger JSON is invalid: {exc}"]
    if not isinstance(template, dict) or not isinstance(ledger, dict):
        return ["metadata template and claim ledger must be objects"]
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
    keywords = template.get("keywords")
    required_keywords = {
        "causal sets",
        "quantum sequential growth",
        "Bell causality",
        "statewise observability",
        "exact rational certificates",
        "noncommutative matrices",
    }
    if not isinstance(keywords, list) or not required_keywords <= set(keywords):
        errors.append("metadata scientific keywords are incomplete")
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
    return errors


def verify_supplement_archive(
    archive_path: Path,
    *,
    standalone_pdf: Path | None = None,
) -> dict[str, Any]:
    """Verify the supplement, and optionally its external standalone PDF."""

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

    metadata_errors = _metadata_binding_ok(contents)
    passed = bool(
        manifest.get("schema_version") == SUPPLEMENT_SCHEMA_VERSION
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
                inner_summary = verify_supplement_archive(
                    inner_path,
                    standalone_pdf=pdf_path,
                )
                inner_contents = _archive_contents(inner_path)
                inner_manifest = _manifest_from_contents(inner_contents, "inner supplement")
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


def verify_two_file_output(output_dir: Path) -> dict[str, Any]:
    """Verify the historical PDF + supplement layout after owner waiver."""

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
        "layout": TWO_FILE_OWNER_WAIVER_LAYOUT,
        "owner_waiver_required": True,
        "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
        "missing_files": missing,
        "unexpected_files": unexpected,
        "standalone_pdf_name_safe": pdf_name_safe,
        "supplement": supplement_summary,
    }


def verify_upload_directory(
    output_dir: Path,
    *,
    allow_two_file_owner_waiver: bool = False,
) -> dict[str, Any]:
    """Verify the default one-file directory, or an explicit two-file waiver."""

    output_dir = output_dir.resolve()
    if not output_dir.is_dir():
        raise FileNotFoundError(f"upload output directory is missing: {output_dir}")
    actual = {child.name for child in output_dir.iterdir()}
    if actual == {UPLOAD_ARCHIVE_NAME}:
        archive_summary = verify_single_archive(output_dir / UPLOAD_ARCHIVE_NAME)
        return {
            "passed": archive_summary["passed"],
            "output_dir": str(output_dir),
            "layout": SINGLE_ARCHIVE_LAYOUT,
            "zenodo_upload_files": [UPLOAD_ARCHIVE_NAME],
            "archive": archive_summary,
        }
    if actual == {UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME}:
        if not allow_two_file_owner_waiver:
            return {
                "passed": False,
                "output_dir": str(output_dir),
                "layout": TWO_FILE_OWNER_WAIVER_LAYOUT,
                "owner_waiver_required": True,
                "error": (
                    "two-file output requires explicit allow_two_file_owner_waiver=True"
                ),
                "zenodo_upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
            }
        return verify_two_file_output(output_dir)
    expected = {UPLOAD_ARCHIVE_NAME}
    return {
        "passed": False,
        "output_dir": str(output_dir),
        "layout": SINGLE_ARCHIVE_LAYOUT,
        "zenodo_upload_files": [UPLOAD_ARCHIVE_NAME],
        "missing_files": sorted(expected - actual),
        "unexpected_files": sorted(actual - expected),
        "error": "output directory must contain exactly one outer archive",
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--root",
        type=Path,
        help="upload output directory; strict default requires exactly one outer archive",
    )
    group.add_argument(
        "--archive",
        type=Path,
        help="single outer archive (or an inner supplement when --pdf is supplied)",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="standalone PDF for external binding when verifying an inner supplement",
    )
    parser.add_argument(
        "--allow-two-file-owner-waiver",
        action="store_true",
        help="explicitly permit verification of the historical two-file directory",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    if arguments.archive is not None:
        if arguments.pdf is not None:
            summary = verify_supplement_archive(
                arguments.archive,
                standalone_pdf=arguments.pdf,
            )
        else:
            summary = verify_single_archive(arguments.archive)
    else:
        summary = verify_upload_directory(
            arguments.root,
            allow_two_file_owner_waiver=arguments.allow_two_file_owner_waiver,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
