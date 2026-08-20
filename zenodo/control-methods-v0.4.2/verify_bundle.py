"""Strictly verify the control/methods Zenodo PDF-plus-supplement upload set."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any

UPLOAD_PDF_NAME = "finite_qsg_fail_closed_methods_v0.4.2.pdf"
UPLOAD_SUPPLEMENT_NAME = "finite_qsg_fail_closed_methods_v0.4.2_supplement.tar.gz"
SUPPLEMENT_ROOT = "finite_qsg_fail_closed_methods_v0.4.2_supplement"
MANIFEST_PATH = f"{SUPPLEMENT_ROOT}/upload_checksums.json"
SCHEMA_VERSION = "zenodo-control-methods-v0.4.2-upload-manifest-v1"
PDF_RESULT_SOURCE = "results/v0.4.2_control_methods_scoped_pdf_final_20260820.json"
METADATA_SOURCE = "zenodo/control-methods-v0.4.2/metadata.template.json"
RELEASE_SCOPE_SOURCE = "zenodo/control-methods-v0.4.2/release_scope.json"
EXPECTED_TITLE = (
    "Fail-closed reproducibility for finite quantum sequential growth: exact controls, "
    "independent replay, and resource boundaries"
)


class VerificationError(RuntimeError):
    """Raised when the upload layout cannot be inspected safely."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    return sha256_bytes(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )


def pdf_page_count(path: Path) -> int:
    """Return a parsed page count, with a dependency-free PDF syntax fallback."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        data = path.read_bytes()
        count = len(re.findall(rb"/Type\s*/Page\b", data))
        if count <= 0:
            raise VerificationError("cannot determine PDF page count") from exc
        return count
    return len(PdfReader(str(path)).pages)


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[0] == SUPPLEMENT_ROOT
        and "\\" not in name
    )


def _read_archive(path: Path) -> tuple[dict[str, bytes], list[str]]:
    raw = path.read_bytes()
    errors: list[str] = []
    if raw[:2] != b"\x1f\x8b":
        raise VerificationError("supplement lacks a gzip header")
    if len(raw) < 10 or raw[4:8] != b"\x00\x00\x00\x00":
        errors.append("gzip mtime is not zero")
    try:
        decompressed = gzip.decompress(raw)
    except OSError as exc:
        raise VerificationError(f"cannot decompress supplement: {exc}") from exc
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(decompressed), mode="r:") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                errors.append(f"non-regular tar member: {member.name}")
                continue
            if not _safe_member_name(member.name):
                errors.append(f"unsafe tar member: {member.name}")
                continue
            if member.name in files:
                errors.append(f"duplicate tar member: {member.name}")
                continue
            if member.mtime != 0:
                errors.append(f"nonzero tar mtime: {member.name}")
            if member.uid != 0 or member.gid != 0:
                errors.append(f"nonzero tar owner: {member.name}")
            if member.mode != 0o644:
                errors.append(f"unexpected tar mode: {member.name}")
            extracted = tar.extractfile(member)
            if extracted is None:
                errors.append(f"cannot read tar member: {member.name}")
                continue
            files[member.name] = extracted.read()
    return files, errors


def _json_member(files: dict[str, bytes], source_path: str) -> dict[str, Any]:
    archive_path = f"{SUPPLEMENT_ROOT}/{source_path}"
    data = files.get(archive_path)
    if data is None:
        raise VerificationError(f"required archive member is missing: {source_path}")
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"archive member is not a JSON object: {source_path}")
    return value


def verify_upload_directory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        raise VerificationError(f"upload directory does not exist: {root}")
    observed_names = sorted(path.name for path in root.iterdir())
    expected_names = sorted((UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME))
    if observed_names != expected_names:
        errors.append(
            f"upload directory must contain exactly {expected_names}; observed {observed_names}"
        )
    pdf_path = root / UPLOAD_PDF_NAME
    supplement_path = root / UPLOAD_SUPPLEMENT_NAME
    if not pdf_path.is_file() or pdf_path.read_bytes()[:5] != b"%PDF-":
        raise VerificationError("standalone PDF is missing or invalid")
    if not supplement_path.is_file():
        raise VerificationError("supplement is missing")

    files, archive_errors = _read_archive(supplement_path)
    errors.extend(archive_errors)
    manifest_data = files.get(MANIFEST_PATH)
    if manifest_data is None:
        raise VerificationError("supplement manifest is missing")
    manifest = json.loads(manifest_data.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise VerificationError("supplement manifest is not a JSON object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("manifest schema version mismatch")
    if manifest.get("status") != "PRODUCTION_COMMIT_BOUND":
        errors.append("manifest is not production commit-bound")
    if manifest.get("layout") != "pdf_and_supplement":
        errors.append("manifest layout mismatch")
    if manifest.get("upload_files") != [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME]:
        errors.append("manifest upload-file list mismatch")
    if manifest.get("title") != EXPECTED_TITLE:
        errors.append("manifest title mismatch")
    digest = manifest.get("semantic_digest_sha256")
    semantic = dict(manifest)
    semantic.pop("semantic_digest_sha256", None)
    if digest != stable_hash(semantic):
        errors.append("manifest semantic digest mismatch")

    binding = manifest.get("source_commit_binding", {})
    commit = binding.get("commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("manifest source commit is not a full SHA")
    if binding.get("status") != "PRODUCTION_COMMIT_BOUND":
        errors.append("source binding status mismatch")
    if binding.get("tree_url") is not None:
        errors.append("builder must not invent a remote tree URL")
    if binding.get("remote_visibility") != "NOT_VERIFIED_BY_BUILDER":
        errors.append("remote visibility boundary mismatch")

    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise VerificationError("manifest file list is empty or invalid")
    if binding.get("checked_source_count") != len(records):
        errors.append("checked source count mismatch")
    expected_members = {MANIFEST_PATH}
    seen_sources: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("invalid manifest file record")
            continue
        source_path = record.get("source_path")
        archive_path = record.get("archive_path")
        if not isinstance(source_path, str) or not isinstance(archive_path, str):
            errors.append("manifest file record lacks paths")
            continue
        if source_path in seen_sources:
            errors.append(f"duplicate manifest source: {source_path}")
        seen_sources.add(source_path)
        expected_archive_path = f"{SUPPLEMENT_ROOT}/{source_path}"
        if archive_path != expected_archive_path:
            errors.append(f"archive path mismatch for {source_path}")
        expected_members.add(archive_path)
        data = files.get(archive_path)
        if data is None:
            errors.append(f"manifest member missing: {archive_path}")
            continue
        if record.get("bytes") != len(data):
            errors.append(f"byte-count mismatch: {source_path}")
        if record.get("sha256") != sha256_bytes(data):
            errors.append(f"SHA-256 mismatch: {source_path}")
        if Path(source_path).suffix.lower() in {".bib", ".json", ".md", ".py", ".tex", ".txt"}:
            if b"\r" in data:
                errors.append(f"non-LF text member: {source_path}")
            try:
                data.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                errors.append(f"non-UTF-8 text member: {source_path}")
        if source_path.startswith(("references/papers/", "references/text/", "output/")):
            errors.append(f"forbidden archived source: {source_path}")
    if set(files) != expected_members:
        errors.append("tar member set does not exactly match the manifest")

    external = manifest.get("external_pdf", {})
    actual_pdf_hash = sha256_file(pdf_path)
    actual_pdf_bytes = pdf_path.stat().st_size
    try:
        actual_pages = pdf_page_count(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive parser boundary
        raise VerificationError(f"cannot parse standalone PDF: {exc}") from exc
    if external.get("filename") != UPLOAD_PDF_NAME:
        errors.append("external PDF filename mismatch")
    if external.get("sha256") != actual_pdf_hash:
        errors.append("external PDF SHA-256 mismatch")
    if external.get("bytes") != actual_pdf_bytes:
        errors.append("external PDF byte count mismatch")
    if external.get("pages") != actual_pages:
        errors.append("external PDF page count mismatch")
    if external.get("visual_qa") != "PASS_ALL_PAGES":
        errors.append("external PDF visual-QA status mismatch")

    pdf_result = _json_member(files, PDF_RESULT_SOURCE)
    if pdf_result.get("status") != "FINAL_PDF_VISUAL_QA_PASS_UPLOAD_CANDIDATE":
        errors.append("embedded final PDF result status mismatch")
    if pdf_result.get("pdf", {}).get("sha256") != actual_pdf_hash:
        errors.append("embedded final PDF result hash mismatch")
    if pdf_result.get("pdf", {}).get("bytes") != actual_pdf_bytes:
        errors.append("embedded final PDF result byte count mismatch")
    if pdf_result.get("pdf", {}).get("pages") != actual_pages:
        errors.append("embedded final PDF result page count mismatch")

    metadata = _json_member(files, METADATA_SOURCE)
    if metadata.get("title") != EXPECTED_TITLE:
        errors.append("metadata title mismatch")
    if metadata.get("publication_date") is not None or metadata.get("doi") is not None:
        errors.append("pre-publication metadata must not invent a date or DOI")
    if metadata.get("license") != "CC BY 4.0":
        errors.append("metadata manuscript license mismatch")
    description = metadata.get("description", "")
    for fragment in (
        "resource-limit observation, not an impossibility theorem",
        "No candidate production evidence",
        "4,097 down-sets",
    ):
        if fragment not in description:
            errors.append(f"metadata claim-boundary fragment missing: {fragment}")

    release_scope = _json_member(files, RELEASE_SCOPE_SOURCE)
    authorization = release_scope.get("authorization", {})
    if authorization.get("zenodo_file_upload") is not False:
        errors.append("release scope unexpectedly authorizes Zenodo upload")
    if authorization.get("publication") is not False:
        errors.append("release scope unexpectedly authorizes publication")
    if release_scope.get("global_verdict") != "FINAL_THEORY_OPEN":
        errors.append("release scope global verdict mismatch")

    return {
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "layout": "pdf_and_supplement",
        "source_commit": commit,
        "source_count": len(records),
        "pdf": {
            "filename": UPLOAD_PDF_NAME,
            "bytes": actual_pdf_bytes,
            "sha256": actual_pdf_hash,
            "pages": actual_pages,
        },
        "supplement": {
            "filename": UPLOAD_SUPPLEMENT_NAME,
            "bytes": supplement_path.stat().st_size,
            "sha256": sha256_file(supplement_path),
            "semantic_digest_sha256": digest,
            "member_count": len(files),
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Strictly verify the Zenodo upload set.")
    parser.add_argument("--root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        summary = verify_upload_directory(args.root)
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
