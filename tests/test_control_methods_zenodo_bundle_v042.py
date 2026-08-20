from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder() -> ModuleType:
    return _load(
        "control_methods_bundle_builder",
        "zenodo/control-methods-v0.4.2/build_bundle.py",
    )


@pytest.fixture(scope="module")
def verifier() -> ModuleType:
    return _load(
        "control_methods_bundle_verifier",
        "zenodo/control-methods-v0.4.2/verify_bundle.py",
    )


def test_metadata_form_and_manuscript_are_scope_aligned() -> None:
    metadata = json.loads(
        (ROOT / "zenodo/control-methods-v0.4.2/metadata.template.json").read_text(
            encoding="utf-8"
        )
    )
    form = (ROOT / "zenodo/control-methods-v0.4.2/ZENODO_FORM_VALUES.md").read_text(
        encoding="utf-8"
    )
    manuscript = (
        ROOT / "paper/v0.4.2_control_methods_scoped/main.tex"
    ).read_text(encoding="utf-8")
    assert metadata["title"] in form
    assert "Fail-closed reproducibility for finite quantum sequential growth" in manuscript
    assert metadata["publication_date"] is None
    assert metadata["doi"] is None
    assert metadata["license"] == "CC BY 4.0"
    assert "resource-limit observation, not an impossibility theorem" in metadata[
        "description"
    ]
    assert "No candidate production evidence" in metadata["description"]
    assert "FINAL\\_THEORY\\_OPEN" in manuscript


def test_release_scope_leaves_account_actions_to_human() -> None:
    scope = json.loads(
        (ROOT / "zenodo/control-methods-v0.4.2/release_scope.json").read_text(
            encoding="utf-8"
        )
    )
    authorization = scope["authorization"]
    assert authorization["manuscript_finalization"] is True
    assert authorization["local_release_packaging"] is True
    assert authorization["zenodo_account_access"] is False
    assert authorization["zenodo_file_upload"] is False
    assert authorization["doi_reservation"] is False
    assert authorization["publication"] is False
    assert authorization["human_depositor_required"] is True
    assert scope["global_verdict"] == "FINAL_THEORY_OPEN"


def test_source_allowlist_is_safe_and_complete(builder: ModuleType) -> None:
    paths = builder.collect_source_paths(ROOT)
    assert len(paths) == len(set(paths))
    assert builder.PDF_SOURCE_PATH not in paths
    assert builder.PDF_RESULT_PATH in paths
    assert "paper/v0.4.2_control_methods_scoped/main.tex" in paths
    assert "zenodo/control-methods-v0.4.2/metadata.template.json" in paths
    assert "tests/test_control_methods_zenodo_bundle_v042.py" in paths
    assert not any(path.startswith("references/papers/") for path in paths)
    assert not any(path.startswith("references/text/") for path in paths)
    assert not any(path.startswith("output/") for path in paths)


def test_forbidden_or_unsafe_paths_fail_closed(builder: ModuleType) -> None:
    with pytest.raises(builder.BundleError, match="unsafe source path"):
        builder._normalise_source_path("../escape.txt")
    with pytest.raises(builder.BundleError, match="forbidden source path"):
        builder._normalise_source_path("references/papers/third-party.pdf")
    with pytest.raises(builder.BundleError, match="standalone PDF"):
        builder._normalise_source_path(builder.PDF_SOURCE_PATH)


def test_standalone_pdf_must_match_the_selected_commit(
    builder: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-current")
    monkeypatch.setattr(
        builder,
        "_git_blob",
        lambda root, commit, source_path: b"%PDF-current",
    )
    builder.validate_pdf_commit_binding(tmp_path, "a" * 40, pdf)

    monkeypatch.setattr(
        builder,
        "_git_blob",
        lambda root, commit, source_path: b"%PDF-stale",
    )
    with pytest.raises(builder.BundleError, match="differs from the selected"):
        builder.validate_pdf_commit_binding(tmp_path, "a" * 40, pdf)


def test_manifest_and_deterministic_archive_round_trip(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    data = b"scope\n"
    source_records = [
        {
            "source_path": "reports/scope.md",
            "archive_path": f"{builder.SUPPLEMENT_ROOT}/reports/scope.md",
            "sha256": builder.sha256_bytes(data),
            "bytes": len(data),
            "data": data,
        }
    ]
    pdf_record = {
        "pdf": {
            "sha256": "1" * 64,
            "bytes": 123,
            "pages": 7,
        }
    }
    manifest = builder.build_manifest("a" * 40, source_records, pdf_record)
    semantic = dict(manifest)
    digest = semantic.pop("semantic_digest_sha256")
    assert digest == builder.stable_hash(semantic)
    archive = tmp_path / "supplement.tar.gz"
    builder.write_supplement(archive, manifest, source_records)
    members, errors = verifier._read_archive(archive)
    assert errors == []
    assert set(members) == {
        f"{builder.SUPPLEMENT_ROOT}/{builder.MANIFEST_NAME}",
        f"{builder.SUPPLEMENT_ROOT}/reports/scope.md",
    }
    assert archive.read_bytes()[4:8] == b"\x00\x00\x00\x00"


def test_output_directory_must_be_external_and_empty(
    builder: ModuleType, tmp_path: Path
) -> None:
    with pytest.raises(builder.BundleError, match="outside the repository"):
        builder._validate_output_directory(ROOT, ROOT / "output/local-upload")
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "sentinel.txt").write_text("keep\n", encoding="utf-8")
    with pytest.raises(builder.BundleError, match="new or empty"):
        builder._validate_output_directory(ROOT, occupied)
    assert (occupied / "sentinel.txt").read_text(encoding="utf-8") == "keep\n"


def test_upload_file_names_match_form_and_checklist(builder: ModuleType) -> None:
    form = (ROOT / "zenodo/control-methods-v0.4.2/ZENODO_FORM_VALUES.md").read_text(
        encoding="utf-8"
    )
    checklist = (
        ROOT / "zenodo/control-methods-v0.4.2/UPLOAD_CHECKLIST.md"
    ).read_text(encoding="utf-8")
    for name in (builder.UPLOAD_PDF_NAME, builder.UPLOAD_SUPPLEMENT_NAME):
        assert name in form
        assert name in checklist
