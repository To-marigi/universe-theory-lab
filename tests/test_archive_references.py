from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "archive_references_under_test",
    ROOT / "scripts" / "archive_references.py",
)
assert SPEC is not None and SPEC.loader is not None
ARCHIVE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARCHIVE_MODULE)
build_archive: Any = ARCHIVE_MODULE.build_archive


def _write_catalog(root: Path, records: list[dict[str, str]]) -> None:
    references = root / "references"
    references.mkdir(parents=True)
    (references / "sources.json").write_text(
        json.dumps({"sources": records}),
        encoding="utf-8",
    )


def test_skip_text_preserves_existing_extraction_metadata(tmp_path: Path) -> None:
    pdf_bytes = b"%PDF existing fixture"
    relative_pdf = "papers/example.pdf"
    _write_catalog(
        tmp_path,
        [{"id": "example:v1", "local_file": relative_pdf}],
    )
    pdf_path = tmp_path / "references" / relative_pdf
    pdf_path.parent.mkdir()
    pdf_path.write_bytes(pdf_bytes)
    text_path = tmp_path / "references" / "text" / "example.txt"
    text_path.parent.mkdir()
    text_path.write_text(
        "===== PAGE 1 =====\nsearchable\n===== PAGE 2 =====\nmore",
        encoding="utf-8",
    )
    expected_hash = f"sha256:{hashlib.sha256(pdf_bytes).hexdigest()}"
    (tmp_path / "references" / "manifest.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "id": "example:v1",
                        "sha256": expected_hash,
                        "archive_status": "PDF_AND_TEXT",
                        "pages": 7,
                        "text_file": "text/example.txt",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    record = build_archive(tmp_path, skip_text=True)["records"][0]

    assert record["archive_status"] == "PDF_AND_TEXT"
    assert record["sha256"] == expected_hash
    assert record["pages"] == 7
    assert record["text_file"] == "text/example.txt"


def test_skip_text_recovers_page_count_from_existing_text(tmp_path: Path) -> None:
    pdf_bytes = b"%PDF existing fixture"
    relative_pdf = "papers/example.pdf"
    _write_catalog(
        tmp_path,
        [{"id": "example:v1", "local_file": relative_pdf}],
    )
    pdf_path = tmp_path / "references" / relative_pdf
    pdf_path.parent.mkdir()
    pdf_path.write_bytes(pdf_bytes)
    text_path = tmp_path / "references" / "text" / "example.txt"
    text_path.parent.mkdir()
    text_path.write_text(
        "===== PAGE 1 =====\none\n===== PAGE 2 =====\ntwo",
        encoding="utf-8",
    )
    (tmp_path / "references" / "manifest.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "id": "example:v1",
                        "sha256": f"sha256:{hashlib.sha256(pdf_bytes).hexdigest()}",
                        "pages": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    record = build_archive(tmp_path, skip_text=True)["records"][0]

    assert record["archive_status"] == "PDF_AND_TEXT"
    assert record["pages"] == 2


def test_skip_text_leaves_new_pdf_without_text_as_pdf_only(tmp_path: Path) -> None:
    relative_pdf = "papers/new.pdf"
    _write_catalog(
        tmp_path,
        [{"id": "new:v1", "local_file": relative_pdf}],
    )
    pdf_path = tmp_path / "references" / relative_pdf
    pdf_path.parent.mkdir()
    pdf_path.write_bytes(b"%PDF new fixture")

    record = build_archive(tmp_path, skip_text=True)["records"][0]

    assert record["archive_status"] == "PDF_ONLY"
    assert record["pages"] is None
    assert record["text_file"] is None
