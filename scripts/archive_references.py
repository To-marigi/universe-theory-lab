"""Validate the local paper archive, extract searchable text, and record hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_text(pdf_path: Path, text_path: Path) -> tuple[int, str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required for text extraction; use --skip-text for hash-only mode"
        ) from exc
    reader = PdfReader(pdf_path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        printable = "".join(
            character if character in "\n\t" or ord(character) >= 32 else " "
            for character in raw_text
        )
        cleaned = "\n".join(line.rstrip() for line in printable.splitlines())
        pages.append(f"\n\n===== PAGE {number} =====\n\n{cleaned}")
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(
        "".join(pages).lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    return len(reader.pages), str(text_path)


def _page_count_from_extracted_text(text_path: Path) -> int | None:
    count = sum(
        line.startswith("===== PAGE ")
        for line in text_path.read_text(encoding="utf-8", errors="replace").splitlines()
    )
    return count or None


def build_archive(root: Path, *, skip_text: bool) -> dict[str, Any]:
    references = root / "references"
    source_catalog = json.loads(
        (references / "sources.json").read_text(encoding="utf-8")
    )
    previous_manifest_path = references / "manifest.json"
    previous_by_id: dict[str, dict[str, Any]] = {}
    if previous_manifest_path.exists():
        previous_manifest = json.loads(
            previous_manifest_path.read_text(encoding="utf-8")
        )
        previous_by_id = {
            str(record["id"]): record
            for record in previous_manifest.get("records", [])
            if isinstance(record, dict) and "id" in record
        }
    records = []
    for source in source_catalog["sources"]:
        record = dict(source)
        local_name = source.get("local_file")
        if local_name is None:
            record.update(
                {
                    "archive_status": "METADATA_ONLY",
                    "sha256": None,
                    "bytes": None,
                    "pages": None,
                    "text_file": None,
                }
            )
            records.append(record)
            continue
        pdf_path = references / local_name
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)
        if pdf_path.read_bytes()[:4] != b"%PDF":
            raise ValueError(f"not a PDF: {pdf_path}")
        text_path = references / "text" / f"{pdf_path.stem}.txt"
        pdf_hash = f"sha256:{_sha256(pdf_path)}"
        pages = None
        extracted = None
        if not skip_text:
            pages, extracted_path = _extract_text(pdf_path, text_path)
            extracted = str(Path(extracted_path).relative_to(references)).replace("\\", "/")
        elif text_path.exists():
            extracted = str(text_path.relative_to(references)).replace("\\", "/")
            previous = previous_by_id.get(str(source.get("id")))
            if previous is not None and previous.get("sha256") == pdf_hash:
                pages = previous.get("pages")
            if pages is None:
                pages = _page_count_from_extracted_text(text_path)
        record.update(
            {
                "archive_status": "PDF_AND_TEXT" if extracted else "PDF_ONLY",
                "sha256": pdf_hash,
                "bytes": pdf_path.stat().st_size,
                "pages": pages,
                "text_file": extracted,
            }
        )
        records.append(record)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "catalog": "references/sources.json",
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-text", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = build_archive(root, skip_text=args.skip_text)
    output = root / "references" / "manifest.json"
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Archived {len(manifest['records'])} references: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
