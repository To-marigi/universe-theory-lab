"""Build a deterministic PDF-plus-supplement Zenodo upload set."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

UPLOAD_PDF_NAME = "finite_qsg_fail_closed_methods_v0.4.2.pdf"
UPLOAD_SUPPLEMENT_NAME = "finite_qsg_fail_closed_methods_v0.4.2_supplement.tar.gz"
SUPPLEMENT_ROOT = "finite_qsg_fail_closed_methods_v0.4.2_supplement"
MANIFEST_NAME = "upload_checksums.json"
PDF_SOURCE_PATH = "output/pdf/finite_qsg_fail_closed_methods_v0.4.2.pdf"
PDF_RESULT_PATH = "results/v0.4.2_control_methods_scoped_pdf_final_20260820.json"
PDF_REPORT_PATH = "reports/v0.4.2_control_methods_scoped_pdf_final_2026-08-20.md"
REPOSITORY_URL = "https://github.com/To-marigi/universe-theory-lab"
SCHEMA_VERSION = "zenodo-control-methods-v0.4.2-upload-manifest-v1"
FINAL_PDF_STATUS = "FINAL_PDF_VISUAL_QA_PASS_UPLOAD_CANDIDATE"

EVIDENCE_PAIRS = (
    (
        "results/v0.4.2_phase_c_method_completion.json",
        "reports/v0.4.2_phase_c_method_completion.md",
    ),
    (
        "results/v0.4.2_phase_b_sampler_preflight.json",
        "reports/v0.4.2_phase_b_sampler_preflight.md",
    ),
    (
        "results/v0.4.2_phase_b_control_sampler_preflight_20260816.json",
        "reports/v0.4.2_phase_b_control_sampler_preflight_2026-08-16.md",
    ),
    (
        "results/v0.4.2_phase_b_control_implementation_preflight_20260816.json",
        "reports/v0.4.2_phase_b_control_implementation_preflight_2026-08-16.md",
    ),
    (
        "results/v0.4.2_phase_b_control_cost_preflight_20260816.json",
        "reports/v0.4.2_phase_b_control_cost_preflight_2026-08-16.md",
    ),
    (
        "results/v0.4.2_phase_b_control_scaling_review_20260816.json",
        "reports/v0.4.2_phase_b_control_scaling_review_2026-08-16.md",
    ),
    (
        "results/v0.4.2_phase_b_control_exact_scaling_design_20260817.json",
        "reports/v0.4.2_phase_b_control_exact_scaling_design_2026-08-17.md",
    ),
    (
        "results/v0.4.2_phase_b_hard_supervisor_preflight_20260816.json",
        "reports/v0.4.2_phase_b_hard_supervisor_preflight_2026-08-16.md",
    ),
    (
        "results/v0.4.2_phase_b_candidate_identity.json",
        "reports/v0.4.2_phase_b_candidate_identity.md",
    ),
    (
        "results/v0.4.2_phase_b_control_methods_scope_closure_20260820.json",
        "reports/v0.4.2_phase_b_control_methods_scope_closure_2026-08-20.md",
    ),
)

BASE_SOURCE_PATHS = (
    "paper/v0.4.2_control_methods_scoped/main.tex",
    "paper/v0.4.2_control_methods_scoped/references.bib",
    "paper/v0.4.2_control_methods_scoped/REPRODUCING.md",
    "zenodo/control-methods-v0.4.2/README.md",
    "zenodo/control-methods-v0.4.2/LICENSE-PAPER.md",
    "zenodo/control-methods-v0.4.2/release_scope.json",
    "zenodo/control-methods-v0.4.2/metadata.template.json",
    "zenodo/control-methods-v0.4.2/ZENODO_FORM_VALUES.md",
    "zenodo/control-methods-v0.4.2/UPLOAD_CHECKLIST.md",
    "zenodo/control-methods-v0.4.2/build_bundle.py",
    "zenodo/control-methods-v0.4.2/verify_bundle.py",
    "scripts/build_v042_control_methods_pdf.py",
    "src/universe_lab/final_theory/phase_b_control_methods_scope_closure_v042.py",
    "tests/final_theory/test_v042_phase_b_control_methods_scope_closure.py",
    "tests/test_control_methods_zenodo_bundle_v042.py",
    "references/notes/v0.4.2_control_methods_zenodo_submission_policy_2026-08-20.md",
    "CURRENT_RESEARCH_STATE.json",
    "LICENSE",
    PDF_RESULT_PATH,
    PDF_REPORT_PATH,
)

TEXT_SUFFIXES = {".bib", ".json", ".md", ".py", ".tex", ".txt"}
FORBIDDEN_PREFIXES = (
    ".git/",
    "output/",
    "references/papers/",
    "references/text/",
    "vendor/",
    "tmp/",
)


class BundleError(RuntimeError):
    """Raised when a release package cannot be certified."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def _run_git(root: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() if text else completed.stderr.decode(errors="replace")
        raise BundleError(f"git {' '.join(args)} failed: {error}")
    return completed.stdout


def resolve_commit(root: Path, revision: str) -> str:
    value = str(_run_git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise BundleError(f"revision did not resolve to a full commit: {value}")
    return value


def _normalise_source_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise BundleError(f"unsafe source path: {value}")
    normalised = path.as_posix()
    if normalised == PDF_SOURCE_PATH:
        raise BundleError("standalone PDF must not be duplicated in the supplement")
    if any(normalised.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        raise BundleError(f"forbidden source path: {normalised}")
    return normalised


def _walk_named_lists(value: Any, names: set[str]) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in names and isinstance(child, list):
                for record in child:
                    if isinstance(record, dict) and isinstance(record.get("path"), str):
                        yield record["path"]
            yield from _walk_named_lists(child, names)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_named_lists(child, names)


def collect_source_paths(root: Path) -> list[str]:
    paths = set(BASE_SOURCE_PATHS)
    for result_path, report_path in EVIDENCE_PAIRS:
        paths.update((result_path, report_path))
        artifact = json.loads((root / result_path).read_text(encoding="utf-8"))
        paths.update(_walk_named_lists(artifact, {"source_bindings", "test_files"}))
    return sorted(_normalise_source_path(path) for path in paths)


def _git_blob(root: Path, commit: str, source_path: str) -> bytes:
    value = _run_git(root, "show", f"{commit}:{source_path}", text=False)
    if not isinstance(value, bytes):
        raise BundleError("binary git read unexpectedly returned text")
    return value


def _validate_text(source_path: str, data: bytes) -> None:
    if Path(source_path).suffix.lower() not in TEXT_SUFFIXES:
        return
    if b"\r" in data:
        raise BundleError(f"text source is not strict LF: {source_path}")
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise BundleError(f"text source is not UTF-8: {source_path}") from exc


def collect_committed_sources(
    root: Path, commit: str, source_paths: Iterable[str]
) -> list[dict[str, Any]]:
    records = []
    for source_path in source_paths:
        worktree_path = root / Path(source_path)
        if not worktree_path.is_file():
            raise BundleError(f"source file is missing: {source_path}")
        worktree_data = worktree_path.read_bytes()
        commit_data = _git_blob(root, commit, source_path)
        if worktree_data != commit_data:
            raise BundleError(f"worktree differs from selected commit: {source_path}")
        _validate_text(source_path, commit_data)
        archive_path = f"{SUPPLEMENT_ROOT}/{source_path}"
        records.append(
            {
                "source_path": source_path,
                "archive_path": archive_path,
                "sha256": sha256_bytes(commit_data),
                "bytes": len(commit_data),
                "data": commit_data,
            }
        )
    return records


def load_final_pdf_record(root: Path) -> tuple[dict[str, Any], Path]:
    record = json.loads((root / PDF_RESULT_PATH).read_text(encoding="utf-8"))
    if record.get("status") != FINAL_PDF_STATUS:
        raise BundleError("final PDF result is not an upload candidate")
    if record.get("visual_qa", {}).get("status") != "PASS_ALL_PAGES":
        raise BundleError("final PDF all-page visual QA is not recorded as passed")
    pdf = root / PDF_SOURCE_PATH
    if not pdf.is_file() or pdf.read_bytes()[:5] != b"%PDF-":
        raise BundleError("final standalone PDF is missing or invalid")
    expected = record.get("pdf", {})
    if expected.get("path") != PDF_SOURCE_PATH:
        raise BundleError("final PDF result path mismatch")
    if expected.get("sha256") != sha256_file(pdf):
        raise BundleError("final PDF SHA-256 does not match its result artifact")
    if expected.get("bytes") != pdf.stat().st_size:
        raise BundleError("final PDF byte count does not match its result artifact")
    if not isinstance(expected.get("pages"), int) or expected["pages"] <= 0:
        raise BundleError("final PDF page count is missing")
    return record, pdf


def validate_pdf_commit_binding(root: Path, commit: str, pdf: Path) -> None:
    """Require the standalone PDF bytes to be present in the selected commit."""

    committed = _git_blob(root, commit, PDF_SOURCE_PATH)
    current = pdf.read_bytes()
    if committed != current:
        raise BundleError("final PDF differs from the selected source commit")


def build_manifest(
    commit: str,
    source_records: list[dict[str, Any]],
    pdf_record: dict[str, Any],
) -> dict[str, Any]:
    public_records = [
        {key: value for key, value in record.items() if key != "data"}
        for record in source_records
    ]
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "PRODUCTION_COMMIT_BOUND",
        "layout": "pdf_and_supplement",
        "upload_files": [UPLOAD_PDF_NAME, UPLOAD_SUPPLEMENT_NAME],
        "title": (
            "Fail-closed reproducibility for finite quantum sequential growth: "
            "exact controls, independent replay, and resource boundaries"
        ),
        "version": "0.4.2",
        "source_commit_binding": {
            "status": "PRODUCTION_COMMIT_BOUND",
            "commit": commit,
            "repository_url": REPOSITORY_URL,
            "tree_url": None,
            "remote_visibility": "NOT_VERIFIED_BY_BUILDER",
            "checked_source_count": len(public_records),
        },
        "external_pdf": {
            "filename": UPLOAD_PDF_NAME,
            "sha256": pdf_record["pdf"]["sha256"],
            "bytes": pdf_record["pdf"]["bytes"],
            "pages": pdf_record["pdf"]["pages"],
            "visual_qa": "PASS_ALL_PAGES",
        },
        "files": public_records,
        "licenses": {"manuscript": "CC BY 4.0", "software": "MIT"},
        "scientific_boundary": {
            "global_verdict": "FINAL_THEORY_OPEN",
            "candidate_production_evidence": False,
            "continuum_limit_claimed": False,
            "solver_impossibility_claimed": False,
        },
    }
    manifest["semantic_digest_sha256"] = stable_hash(manifest)
    return manifest


def _tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=name)
    info.size = size
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mode = 0o644
    return info


def write_supplement(
    path: Path,
    manifest: dict[str, Any],
    source_records: list[dict[str, Any]],
) -> None:
    manifest_data = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
                manifest_path = f"{SUPPLEMENT_ROOT}/{MANIFEST_NAME}"
                tar.addfile(_tar_info(manifest_path, len(manifest_data)), io.BytesIO(manifest_data))
                for record in source_records:
                    data = record["data"]
                    tar.addfile(
                        _tar_info(record["archive_path"], len(data)), io.BytesIO(data)
                    )


def _validate_output_directory(root: Path, output: Path) -> None:
    root = root.resolve()
    output = output.resolve()
    if output == root or output.is_relative_to(root):
        raise BundleError("output directory must be outside the repository")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise BundleError("output directory must be new or empty")
    output.parent.mkdir(parents=True, exist_ok=True)


def _receipt_path(output: Path) -> Path:
    return output.parent / f"{output.name}_ZENODO_UPLOAD_RECEIPT.md"


def _write_receipt(
    path: Path,
    commit: str,
    pdf: Path,
    supplement: Path,
    manifest: dict[str, Any],
) -> None:
    content = f"""# Zenodo upload receipt: control/methods v0.4.2

Status: `UPLOAD_BYTES_BUILT_STRICT_VERIFICATION_REQUIRED`

| Field | Value |
| --- | --- |
| Source commit | `{commit}` |
| Commit status | `PRODUCTION_COMMIT_BOUND` |
| Remote visibility | `NOT_VERIFIED_BY_BUILDER` |
| PDF | `{UPLOAD_PDF_NAME}` |
| PDF bytes | `{pdf.stat().st_size}` |
| PDF SHA-256 | `{sha256_file(pdf)}` |
| PDF pages | `{manifest['external_pdf']['pages']}` |
| Supplement | `{UPLOAD_SUPPLEMENT_NAME}` |
| Supplement bytes | `{supplement.stat().st_size}` |
| Supplement SHA-256 | `{sha256_file(supplement)}` |
| Supplement semantic digest | `{manifest['semantic_digest_sha256']}` |

Upload exactly the two files listed above. This receipt stays outside the
upload directory to avoid a circular archive hash. Zenodo upload and
publication remain human actions.
"""
    path.write_text(content, encoding="utf-8", newline="\n")


def build_upload_set(root: Path, output: Path, revision: str) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    _validate_output_directory(root, output)
    commit = resolve_commit(root, revision)
    pdf_record, pdf_source = load_final_pdf_record(root)
    validate_pdf_commit_binding(root, commit, pdf_source)
    source_paths = collect_source_paths(root)
    source_records = collect_committed_sources(root, commit, source_paths)
    manifest = build_manifest(commit, source_records, pdf_record)
    with tempfile.TemporaryDirectory(prefix="control-methods-upload-", dir=output.parent) as tmp:
        tmp_root = Path(tmp)
        tmp_pdf = tmp_root / UPLOAD_PDF_NAME
        tmp_supplement = tmp_root / UPLOAD_SUPPLEMENT_NAME
        tmp_pdf.write_bytes(pdf_source.read_bytes())
        write_supplement(tmp_supplement, manifest, source_records)
        output.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_pdf, output / UPLOAD_PDF_NAME)
        os.replace(tmp_supplement, output / UPLOAD_SUPPLEMENT_NAME)
    receipt = _receipt_path(output)
    _write_receipt(
        receipt,
        commit,
        output / UPLOAD_PDF_NAME,
        output / UPLOAD_SUPPLEMENT_NAME,
        manifest,
    )
    return {
        "status": "BUILT_STRICT_VERIFICATION_REQUIRED",
        "layout": "pdf_and_supplement",
        "output_directory": str(output),
        "receipt": str(receipt),
        "source_commit": commit,
        "source_count": len(source_records),
        "manifest_semantic_digest_sha256": manifest["semantic_digest_sha256"],
        "files": {
            UPLOAD_PDF_NAME: {
                "bytes": (output / UPLOAD_PDF_NAME).stat().st_size,
                "sha256": sha256_file(output / UPLOAD_PDF_NAME),
            },
            UPLOAD_SUPPLEMENT_NAME: {
                "bytes": (output / UPLOAD_SUPPLEMENT_NAME).stat().st_size,
                "sha256": sha256_file(output / UPLOAD_SUPPLEMENT_NAME),
            },
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Zenodo upload set.")
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repository_root.resolve()
    output = args.output_dir
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    try:
        summary = build_upload_set(root, output, args.commit)
    except (BundleError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
