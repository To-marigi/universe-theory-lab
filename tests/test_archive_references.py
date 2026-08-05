from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "archive_references_under_test",
    ROOT / "scripts" / "archive_references.py",
)
assert SPEC is not None and SPEC.loader is not None
ARCHIVE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARCHIVE_MODULE)
build_archive: Any = ARCHIVE_MODULE.build_archive


def _write_catalog(root: Path, records: list[dict[str, Any]]) -> None:
    references = root / "references"
    references.mkdir(parents=True)
    (references / "sources.json").write_text(
        json.dumps({"sources": records}),
        encoding="utf-8",
    )


def _write_artifact(root: Path, relative_path: str, payload: bytes) -> None:
    artifact_path = root / "references" / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(payload)


def _artifact(role: str, relative_path: str, payload: bytes) -> dict[str, Any]:
    return {
        "role": role,
        "path": relative_path,
        "media_type": "application/octet-stream",
        "sha256": f"sha256:{hashlib.sha256(payload).hexdigest()}",
        "bytes": len(payload),
    }


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


def test_multiple_local_artifacts_are_validated_and_preserved_exactly(
    tmp_path: Path,
) -> None:
    raw_payload = b"archived raw response"
    ledger_payload = b'{"records": []}\n'
    artifacts = [
        _artifact("RAW_RESPONSE", "papers/query.xml", raw_payload),
        _artifact("NORMALIZED_LEDGER", "papers/query.json", ledger_payload),
    ]
    source = {
        "id": "dataset:example",
        "local_file": None,
        "local_artifacts": artifacts,
        "dataset_snapshot": {"entry_count": 0, "status": "SCREENED"},
    }
    _write_catalog(tmp_path, [source])
    _write_artifact(tmp_path, "papers/query.xml", raw_payload)
    _write_artifact(tmp_path, "papers/query.json", ledger_payload)

    record = build_archive(tmp_path, skip_text=True)["records"][0]

    assert record["archive_status"] == "LOCAL_ARTIFACTS"
    assert record["local_artifacts"] == artifacts
    assert record["dataset_snapshot"] == source["dataset_snapshot"]
    assert record["sha256"] is None
    assert record["bytes"] is None
    assert record["pages"] is None
    assert record["text_file"] is None


@pytest.mark.parametrize("unsafe_path_kind", ["absolute", "parent"])
def test_local_artifact_rejects_unsafe_paths(
    tmp_path: Path,
    unsafe_path_kind: str,
) -> None:
    payload = b"unsafe"
    unsafe_path = (
        str((tmp_path / "outside.bin").resolve())
        if unsafe_path_kind == "absolute"
        else "../outside.bin"
    )
    _write_catalog(
        tmp_path,
        [
            {
                "id": "dataset:unsafe",
                "local_file": None,
                "local_artifacts": [_artifact("RAW", unsafe_path, payload)],
            }
        ],
    )

    with pytest.raises(ValueError, match="unsafe local artifact path"):
        build_archive(tmp_path, skip_text=True)


def test_local_artifact_rejects_hash_mismatch(tmp_path: Path) -> None:
    payload = b"hash-bound"
    artifact = _artifact("RAW", "papers/raw.bin", payload)
    artifact["sha256"] = f"sha256:{'0' * 64}"
    _write_catalog(
        tmp_path,
        [{"id": "dataset:bad-hash", "local_file": None, "local_artifacts": [artifact]}],
    )
    _write_artifact(tmp_path, "papers/raw.bin", payload)

    with pytest.raises(ValueError, match="local artifact SHA-256 mismatch"):
        build_archive(tmp_path, skip_text=True)


def test_local_artifact_rejects_byte_count_mismatch(tmp_path: Path) -> None:
    payload = b"byte-bound"
    artifact = _artifact("RAW", "papers/raw.bin", payload)
    artifact["bytes"] = len(payload) + 1
    _write_catalog(
        tmp_path,
        [{"id": "dataset:bad-bytes", "local_file": None, "local_artifacts": [artifact]}],
    )
    _write_artifact(tmp_path, "papers/raw.bin", payload)

    with pytest.raises(ValueError, match="local artifact byte-count mismatch"):
        build_archive(tmp_path, skip_text=True)


@pytest.mark.parametrize(
    ("invalid_bytes", "payload"),
    [(True, b"x"), (False, b"")],
)
def test_local_artifact_rejects_boolean_byte_counts(
    tmp_path: Path,
    invalid_bytes: bool,
    payload: bytes,
) -> None:
    artifact = _artifact("RAW", "papers/raw.bin", payload)
    artifact["bytes"] = invalid_bytes
    _write_catalog(
        tmp_path,
        [{"id": "dataset:boolean-bytes", "local_file": None, "local_artifacts": [artifact]}],
    )
    _write_artifact(tmp_path, "papers/raw.bin", payload)

    with pytest.raises(ValueError, match="local artifact byte-count mismatch"):
        build_archive(tmp_path, skip_text=True)


@pytest.mark.parametrize("duplicate_field", ["role", "path"])
def test_local_artifact_rejects_duplicate_role_or_path(
    tmp_path: Path,
    duplicate_field: str,
) -> None:
    first_payload = b"first"
    second_payload = b"second"
    first = _artifact("RAW", "papers/first.bin", first_payload)
    if duplicate_field == "role":
        second = _artifact("RAW", "papers/second.bin", second_payload)
    else:
        second = _artifact("LEDGER", "papers/first.bin", first_payload)
    _write_catalog(
        tmp_path,
        [
            {
                "id": f"dataset:duplicate-{duplicate_field}",
                "local_file": None,
                "local_artifacts": [first, second],
            }
        ],
    )
    _write_artifact(tmp_path, "papers/first.bin", first_payload)
    if duplicate_field == "role":
        _write_artifact(tmp_path, "papers/second.bin", second_payload)

    with pytest.raises(ValueError, match="duplicate local artifact role or path"):
        build_archive(tmp_path, skip_text=True)


def test_local_artifact_rejects_unexpected_keys(tmp_path: Path) -> None:
    payload = b"strict schema"
    artifact = _artifact("RAW", "papers/raw.bin", payload)
    artifact["unexpected"] = "not allowed"
    _write_catalog(
        tmp_path,
        [
            {
                "id": "dataset:unexpected-key",
                "local_file": None,
                "local_artifacts": [artifact],
            }
        ],
    )

    with pytest.raises(ValueError, match="local artifact keys changed"):
        build_archive(tmp_path, skip_text=True)
