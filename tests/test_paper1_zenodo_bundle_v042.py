"""Focused tests for the Paper I PDF-plus-supplement Zenodo layout."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ZENODO_DIRECTORY = REPOSITORY_ROOT / "zenodo" / "paper1-v0.4.2"
OWNER_DECISION_PDF_SHA256 = (
    "c112b987b4efb76312892481dd033598b939a0a8becfc4ac0e0eca4070dbfa2e"
)


def _module(name: str, path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder() -> ModuleType:
    return _module("build_paper1_bundle_v042", ZENODO_DIRECTORY / "build_paper1_bundle.py")


@pytest.fixture(scope="module")
def verifier() -> ModuleType:
    return _module("verify_paper1_bundle_v042", ZENODO_DIRECTORY / "verify_paper1_bundle.py")


def _utf16_pdf_literal(value: str) -> bytes:
    encoded = value.encode("utf-16-be")
    return b"\\376\\377" + b"".join(f"\\{byte:03o}".encode("ascii") for byte in encoded)


def _synthetic_root(builder: ModuleType, root: Path) -> tuple[object, ...]:
    claim = {"status": "SCOPED_MANUSCRIPT_ASSEMBLY_READY", "claims": [], "nonclaims": []}
    claim_bytes = (json.dumps(claim, indent=2) + "\n").encode("utf-8")
    claim_path = root / builder.CLAIM_LEDGER_PATH
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_bytes(claim_bytes)
    claim_raw_sha = hashlib.sha256(claim_bytes).hexdigest()
    claim_semantic_sha = builder._semantic_digest(claim)

    metadata = json.loads(
        (REPOSITORY_ROOT / builder.METADATA_TEMPLATE_PATH).read_text(encoding="utf-8")
    )
    metadata["claim_ledger_binding"] = {
        "path": builder.CLAIM_LEDGER_PATH,
        "raw_sha256": claim_raw_sha,
        "semantic_digest_sha256": claim_semantic_sha,
    }
    metadata_path = root / builder.METADATA_TEMPLATE_PATH
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    main = root / "paper/v0.4.2_paper1_statewise_operator/main.tex"
    main.parent.mkdir(parents=True, exist_ok=True)
    main_text = (
        "\\hypersetup{pdftitle={Synthetic Paper I},pdfauthor={Kenichi Osaki}}\n"
        "Claim-locked archive/submission candidate, Paper I v0.4.2.\n"
        "The theorem statements below are limited to C1--C5 and the explicit nonclaims N1--N6.\n"
        r"PAPER\_I\_SCOPED\_U2\_RESOURCE\_OPEN\_LIMITATION\_ACCEPTED"
        "\nhttps://github.com/To-marigi/universe-theory-lab\n"
        "OpenAI Codex (using the Luna and Sol agent scopes) was used for implementation\n"
        "Anthropic Claude was used for research-design discussion\n"
        "The AI systems are neither authors nor independent proof authorities.\n"
        "The human author selected the definitions, scope, budgets, evidence, and final wording\n"
        "Archive metadata, the exact repository commit, and any DOI are maintained externally\n"
    )
    main.write_text(main_text, encoding="utf-8", newline="\n")
    main_sha = hashlib.sha256(main.read_bytes()).hexdigest()

    pdf = root / builder.PDF_SOURCE_PATH
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = (
        b"%PDF-1.7\n"
        + b"/Author(" + _utf16_pdf_literal("Kenichi Osaki") + b")\n"
        + b"/Title(" + _utf16_pdf_literal("Synthetic Paper I") + b")\n"
        + b"\n".join(b"/Type /Page" for _ in range(18))
        + b"\n%%EOF\n"
    )
    pdf.write_bytes(pdf_bytes)
    pdf_sha = hashlib.sha256(pdf_bytes).hexdigest()

    original_owner_pdf_sha = OWNER_DECISION_PDF_SHA256
    owner_artifact = json.loads(
        (REPOSITORY_ROOT / builder.OWNER_DECISION_ARTIFACT_PATH).read_text(
            encoding="utf-8"
        )
    )
    owner_artifact["decisions"]["final_pdf"].update(
        {
            "sha256": pdf_sha,
            "bytes": len(pdf_bytes),
            "page_count": 18,
        }
    )
    owner_artifact.pop("semantic_digest_sha256", None)
    owner_artifact["semantic_digest_sha256"] = builder._semantic_digest(owner_artifact)
    owner_artifact_path = root / builder.OWNER_DECISION_ARTIFACT_PATH
    owner_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    owner_artifact_path.write_text(
        json.dumps(owner_artifact, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    owner_report_path = root / builder.OWNER_DECISION_REPORT_PATH
    owner_report_path.parent.mkdir(parents=True, exist_ok=True)
    owner_report = (
        REPOSITORY_ROOT / builder.OWNER_DECISION_REPORT_PATH
    ).read_text(encoding="utf-8").replace(original_owner_pdf_sha, pdf_sha)
    owner_report_path.write_text(owner_report, encoding="utf-8", newline="\n")
    builder.OWNER_DECISION_PDF_SHA256 = pdf_sha
    builder.OWNER_DECISION_PDF_BYTES = len(pdf_bytes)
    builder.OWNER_DECISION_PDF_PAGE_COUNT = 18
    verifier_module = sys.modules.get("verify_paper1_bundle_v042")
    if verifier_module is not None:
        verifier_module.OWNER_DECISION_PDF_SHA256 = pdf_sha
        verifier_module.OWNER_DECISION_PDF_BYTES = len(pdf_bytes)
        verifier_module.OWNER_DECISION_PDF_PAGE_COUNT = 18
    metadata["owner_decision_binding"] = {
        "path": builder.OWNER_DECISION_ARTIFACT_PATH,
        "report_path": builder.OWNER_DECISION_REPORT_PATH,
        "raw_sha256": hashlib.sha256(owner_artifact_path.read_bytes()).hexdigest(),
        "semantic_digest_sha256": owner_artifact["semantic_digest_sha256"],
        "report_raw_sha256": hashlib.sha256(owner_report_path.read_bytes()).hexdigest(),
        "decision_date": "2026-08-07",
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    report = root / builder.PDF_BUILD_REPORT_PATH
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "| Pages | 18 |\n"
        f"| Bytes | {len(pdf_bytes)} |\n"
        f"`{pdf_sha}`\n"
        "All 18 pages were rendered at 120 dpi and visually inspected.\n"
        f"`{main_sha}`\n"
        f"`{builder.PDF_SOURCE_PATH}`\n",
        encoding="utf-8",
        newline="\n",
    )
    report_sha = hashlib.sha256(report.read_bytes()).hexdigest()
    manifest = {
        "manuscript_files": [
            {
                "path": "paper/v0.4.2_paper1_statewise_operator/main.tex",
                "raw_sha256": main_sha,
            }
        ],
        "tex_build": {
            "pdf_status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
            "pdf_verified": True,
            "default_output_path": builder.PDF_SOURCE_PATH,
            "build_report": {
                "path": builder.PDF_BUILD_REPORT_PATH,
                "raw_sha256": report_sha,
            },
            "current_observation": {
                "main_tex_raw_sha256": main_sha,
                "pdf": {
                    "page_count": 18,
                    "bytes": len(pdf_bytes),
                    "raw_sha256": pdf_sha,
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
                "source_pdf_binding": {
                    "status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
                    "source_hash_matches_current_observation": True,
                    "report_hash_pinned": True,
                    "publication_authorized": False,
                },
            },
        },
        "publication_gates": {
            "pdf_source_rebind": {
                "status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
                "required_before_submission_or_deposit": True,
                "completed": True,
                "publication_authorized": False,
            }
        },
    }
    manifest_path = root / builder.MANUSCRIPT_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    witness = root / builder.WITNESS_SOURCE_PATH
    witness.parent.mkdir(parents=True, exist_ok=True)
    witness.write_text('{"records": []}\n', encoding="utf-8", newline="\n")

    reproducing = root / "paper/v0.4.2_paper1_statewise_operator/REPRODUCING.md"
    reproducing.write_text(
        "PAPER_I_SCOPED_ARCHIVE_SUBMISSION_CANDIDATE_NOT_FROZEN\n"
        "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED\n"
        "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED\n"
        "scripts/normalize_v042_paper1_zenodo_gate_20260806.py --check\n"
        "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py --check\n",
        encoding="utf-8",
        newline="\n",
    )

    for source_path in (
        builder.ZENODO_PREDRAFT_REPORT_PATH,
        builder.ZENODO_PREDRAFT_NOTE_PATH,
        builder.ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
        builder.ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
        builder.ZENODO_PREDRAFT_NORMALIZER_PATH,
        builder.ZENODO_PREDRAFT_LEDGER_PATH,
        builder.ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH,
        builder.ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH,
        builder.ZENODO_PREDRAFT_RECEIPT_PATH,
    ):
        source = REPOSITORY_ROOT / source_path
        destination = root / source_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    specs = (
        builder.FileSpec(
            "package/README.md",
            "source/readme.md",
            "package_readme",
        ),
        builder.FileSpec(
            "package/metadata.template.json",
            builder.METADATA_TEMPLATE_PATH,
            "metadata",
        ),
        builder.FileSpec(
            "package/owner_decision.json",
            builder.OWNER_DECISION_ARTIFACT_PATH,
            "owner_decision",
        ),
        builder.FileSpec(
            "paper/main.tex",
            "paper/v0.4.2_paper1_statewise_operator/main.tex",
            "paper_source",
        ),
        builder.FileSpec(
            builder.CLAIM_LEDGER_PATH,
            builder.CLAIM_LEDGER_PATH,
            "claim_ledger",
        ),
        builder.FileSpec(
            builder.MANUSCRIPT_MANIFEST_PATH,
            builder.MANUSCRIPT_MANIFEST_PATH,
            "manuscript_manifest",
        ),
        builder.FileSpec(
            builder.PDF_BUILD_REPORT_PATH,
            builder.PDF_BUILD_REPORT_PATH,
            "pdf_report",
        ),
        builder.FileSpec(
            builder.OWNER_DECISION_REPORT_PATH,
            builder.OWNER_DECISION_REPORT_PATH,
            "owner_decision_report",
        ),
        builder.FileSpec(
            builder.ZENODO_PREDRAFT_REPORT_PATH,
            builder.ZENODO_PREDRAFT_REPORT_PATH,
            "zenodo_predraft_report",
        ),
        builder.FileSpec(
            builder.ZENODO_PREDRAFT_NOTE_PATH,
            builder.ZENODO_PREDRAFT_NOTE_PATH,
            "zenodo_predraft_note",
        ),
        builder.FileSpec(
            builder.ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
            builder.ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH,
            "zenodo_predraft_predecessor_report",
        ),
        builder.FileSpec(
            builder.ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
            builder.ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH,
            "zenodo_predraft_predecessor_note",
        ),
    )
    (root / "source").mkdir(parents=True, exist_ok=True)
    (root / "source/readme.md").write_text("package\n", encoding="utf-8", newline="\n")
    return specs


def _commit_synthetic_sources(root: Path, specs: tuple[object, ...]) -> str:
    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )

    assert git("init", "--quiet").returncode == 0
    assert git("config", "user.name", "Paper I test").returncode == 0
    assert git("config", "user.email", "paper1-test@example.invalid").returncode == 0
    paths = [spec.source_path for spec in specs]  # type: ignore[attr-defined]
    paths.append("results/v0.4.2_paper1_witness_tables.json")
    assert git("add", *paths).returncode == 0
    assert git("commit", "--quiet", "-m", "final source fixture").returncode == 0
    resolved = git("rev-parse", "HEAD")
    assert resolved.returncode == 0
    return resolved.stdout.strip()


def _rewrite_supplement_manifest(
    builder: ModuleType,
    archive_path: Path,
    destination: Path,
    mutate: object,
) -> None:
    stage = destination.parent / "tampered-supplement-stage"
    stage.mkdir()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive.getmembers():
            relative = member.name.split(f"{builder.SUPPLEMENT_PREFIX}/", 1)[-1]
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = archive.extractfile(member)
            assert handle is not None
            target.write_bytes(handle.read())
    manifest_path = stage / builder.SUPPLEMENT_MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mutate(manifest)
    manifest.pop("semantic_digest_sha256", None)
    manifest["semantic_digest_sha256"] = builder._semantic_digest(manifest)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    builder._write_tar(stage, destination)


def test_pdf_and_supplement_output_is_deterministic_and_verifiable(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    first = tmp_path / "upload-first"
    second = tmp_path / "upload-second"

    first_summary = builder.build_upload_set(root, first, specs=specs, revision=commit)
    builder.build_upload_set(root, second, specs=specs, revision=commit)

    expected_names = {builder.UPLOAD_PDF_NAME, builder.UPLOAD_SUPPLEMENT_NAME}
    assert set(first_summary["files"]) == expected_names
    assert first_summary["layout"] == builder.PDF_AND_SUPPLEMENT_LAYOUT
    assert first_summary["zenodo_upload_files"] == [
        builder.UPLOAD_PDF_NAME,
        builder.UPLOAD_SUPPLEMENT_NAME,
    ]
    assert {path.name for path in first.iterdir()} == expected_names
    for name in expected_names:
        assert (first / name).read_bytes() == (second / name).read_bytes()

    verified = verifier.verify_upload_directory(first)
    assert verified["passed"]
    assert verified["supplement"]["passed"]
    assert verified["supplement"]["pdf_members"] == []
    assert verified["supplement"]["forbidden_members"] == []

    with tarfile.open(first / builder.UPLOAD_SUPPLEMENT_NAME, mode="r:gz") as archive:
        members = archive.getmembers()
    assert all(member.name.startswith(f"{builder.SUPPLEMENT_PREFIX}/") for member in members)
    assert all(member.mode == 0o644 for member in members)
    assert all((member.uid, member.gid) == (0, 0) for member in members)
    assert all((member.uname, member.gname) == ("", "") for member in members)
    assert all(member.mtime == 0 for member in members)
    assert first_summary["pdf_binding"]["pdf_page_count"] == 18


def test_owner_decision_fields_are_bound_into_the_default_supplement(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "upload"
    summary = builder.build_upload_set(root, output, specs=specs, revision=commit)
    assert summary["owner_decision_binding"]["path"] == builder.OWNER_DECISION_ARTIFACT_PATH
    assert summary["owner_decisions"]["license"]["paper"] == "CC BY 4.0"
    assert summary["owner_decisions"]["publication_date"]["value"] is None
    assert summary["owner_decisions"]["doi"]["value"] is None
    assert summary["owner_decisions"]["doi"]["draft_reservation_requested"] is False
    assert summary["owner_decisions"]["related_identifiers"]["value"] == []
    with tarfile.open(output / builder.UPLOAD_SUPPLEMENT_NAME, mode="r:gz") as archive:
        member = next(
            item for item in archive.getmembers() if item.name.endswith("/upload_checksums.json")
        )
        handle = archive.extractfile(member)
        assert handle is not None
        supplement_manifest = json.loads(handle.read().decode("utf-8"))
    assert supplement_manifest["owner_decisions"] == summary["owner_decisions"]
    assert verifier.verify_upload_directory(output)["passed"]


def test_predraft_gate_report_note_are_bound_and_raw_artifacts_excluded(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "upload"
    summary = builder.build_upload_set(root, output, specs=specs, revision=commit)
    gate = summary["zenodo_predraft_literature_gate"]
    assert gate["feed_cutoff_utc"] == "2026-08-06T23:16:23Z"
    assert gate["response_entry_count"] == 722
    assert gate["reviewed_title_abstract_count"] == 28
    assert gate["material_delta_count"] == 0
    assert gate["metadata_equal_by_id"] is True
    assert gate["reviewed_delta_contract"]["added_count"] == 0
    assert gate["reviewed_delta_contract"]["missing_count"] == 0
    assert gate["reviewed_delta_contract"]["version_pair_count"] == 0
    assert gate["historical_predecessor"]["source_id"] == (
        builder.ZENODO_PREDRAFT_PREDECESSOR_SOURCE_ID
    )
    with tarfile.open(output / builder.UPLOAD_SUPPLEMENT_NAME, mode="r:gz") as inner:
        member_names = {
            member.name.split(f"{builder.SUPPLEMENT_PREFIX}/", 1)[-1]
            for member in inner.getmembers()
        }
    assert builder.ZENODO_PREDRAFT_REPORT_PATH in member_names
    assert builder.ZENODO_PREDRAFT_NOTE_PATH in member_names
    assert builder.ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH in member_names
    assert builder.ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH in member_names
    assert builder.ZENODO_PREDRAFT_NORMALIZER_PATH not in member_names
    assert builder.ZENODO_PREDRAFT_LEDGER_PATH not in member_names
    assert builder.ZENODO_PREDRAFT_FULL_OVERLAP_ATOM_PATH not in member_names
    assert builder.ZENODO_PREDRAFT_EXACT_IDS_ATOM_PATH not in member_names
    assert builder.ZENODO_PREDRAFT_RECEIPT_PATH not in member_names
    assert verifier.verify_upload_directory(output)["passed"]


def test_predraft_gate_report_tamper_fails_closed(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    report_path = root / builder.ZENODO_PREDRAFT_REPORT_PATH
    report_path.write_text(
        report_path.read_text(encoding="utf-8").replace("722", "721", 1),
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(RuntimeError, match="Zenodo predraft gate artifact hash/size drifted"):
        builder.build_upload_set(root, tmp_path / "upload", specs=specs)


def test_predraft_gate_historical_predecessor_tamper_fails_closed(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    predecessor = root / builder.ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH
    predecessor.write_text(
        predecessor.read_text(encoding="utf-8") + "\nTampered.\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(
        RuntimeError,
        match="Zenodo predraft predecessor document hash/size drifted",
    ):
        builder.build_upload_set(root, tmp_path / "upload", specs=specs)


def test_owner_decision_license_tamper_fails_closed(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    owner_path = root / builder.OWNER_DECISION_ARTIFACT_PATH
    owner = json.loads(owner_path.read_text(encoding="utf-8"))
    owner["decisions"]["license"]["paper"] = "MIT"
    owner.pop("semantic_digest_sha256", None)
    owner["semantic_digest_sha256"] = builder._semantic_digest(owner)
    owner_path.write_text(
        json.dumps(owner, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(RuntimeError, match="owner decision license policy drifted"):
        builder.build_upload_set(root, tmp_path / "upload", specs=specs)


def test_default_layout_is_previewable_pdf_plus_supplement(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "default"
    summary = builder.build_upload_set(root, output, specs=specs, revision=commit)
    assert summary["layout"] == builder.PDF_AND_SUPPLEMENT_LAYOUT
    assert summary["historical_layout"] is False
    assert set(summary["files"]) == {builder.UPLOAD_PDF_NAME, builder.UPLOAD_SUPPLEMENT_NAME}
    assert verifier.verify_upload_directory(output)["passed"]


def test_unbound_preview_is_explicit_and_never_uploadable(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    output = tmp_path / "unbound"
    summary = builder.build_upload_set(root, output, specs=specs)
    assert summary["source_commit_binding"]["status"] == "UNBOUND_PREVIEW"
    assert summary["source_commit_binding"]["commit"] is None
    assert summary["packaged_commit"] is None
    with tarfile.open(output / builder.UPLOAD_SUPPLEMENT_NAME, mode="r:gz") as archive:
        member = next(
            item for item in archive.getmembers() if item.name.endswith("/upload_checksums.json")
        )
        handle = archive.extractfile(member)
        assert handle is not None
        manifest = json.loads(handle.read().decode("utf-8"))
    assert manifest["status"] == "UNBOUND_PREVIEW"
    assert manifest["source_commit_binding"]["commit"] is None
    assert manifest["source_commit_binding"]["tree_url"] is None
    verified = verifier.verify_upload_directory(output)
    assert verified["passed"] is False
    assert any(
        "UNBOUND_PREVIEW supplement is never eligible for upload" in error
        for error in verified["supplement"]["source_commit_binding_errors"]
    )


def test_embedded_source_commit_binding_tamper_fails_closed(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "upload"
    builder.build_upload_set(root, output, specs=specs, revision=commit)
    tampered = tmp_path / "tampered.tar.gz"

    def mutate(manifest: dict[str, object]) -> None:
        binding = manifest["source_commit_binding"]
        assert isinstance(binding, dict)
        checked = binding["checked_sources"]
        assert isinstance(checked, list)
        checked[0]["sha256"] = "0" * 64

    _rewrite_supplement_manifest(
        builder,
        output / builder.UPLOAD_SUPPLEMENT_NAME,
        tampered,
        mutate,
    )
    verified = verifier.verify_supplement_archive(
        tampered,
        standalone_pdf=output / builder.UPLOAD_PDF_NAME,
    )
    assert verified["passed"] is False
    assert (
        "production source binding checked_sources do not exactly match manifest.files"
        in verified["source_commit_binding_errors"]
    )


def test_historical_single_archive_is_integrity_checkable_but_root_rejects_it(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "historical"
    summary = builder.build_upload_set(
        root,
        output,
        specs=specs,
        revision=commit,
        layout=builder.SINGLE_ARCHIVE_LAYOUT,
    )
    assert summary["historical_layout"] is True
    archive = output / builder.UPLOAD_ARCHIVE_NAME
    assert verifier.verify_single_archive(archive)["passed"]
    strict = verifier.verify_upload_directory(output)
    assert strict["passed"] is False
    assert strict["integrity_passed"] is True
    assert "not an eligible Paper I Zenodo upload layout" in strict["error"]


def test_commit_binding_is_embedded_and_matches_manifest_files(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "upload"
    summary = builder.build_upload_set(root, output, specs=specs, revision=commit)
    assert summary["packaged_commit"] == commit
    binding = summary["source_commit_binding"]
    assert binding["status"] == "PRODUCTION_COMMIT_BOUND"
    assert binding["commit"] == commit
    assert len(binding["commit"]) == 40
    assert binding["repository_url"] == builder.REPOSITORY_URL
    assert binding["tree_url"] is None
    assert binding["remote_visibility"] == "NOT_VERIFIED_BY_BUILDER"
    assert binding["checked_source_count"] == len(specs) + 1
    assert builder.WITNESS_SOURCE_PATH in binding["automatic_sources"]
    assert any(
        record["source_path"] == builder.WITNESS_SOURCE_PATH
        for record in binding["checked_sources"]
    )
    with tarfile.open(output / builder.UPLOAD_SUPPLEMENT_NAME, mode="r:gz") as archive:
        manifest_member = next(
            member
            for member in archive.getmembers()
            if member.name.endswith("/upload_checksums.json")
        )
        handle = archive.extractfile(manifest_member)
        assert handle is not None
        manifest = json.loads(handle.read().decode("utf-8"))
    assert manifest["source_commit_binding"] == binding
    assert manifest["status"] == "OWNER_DECISIONS_RECORDED_RELEASE_ACTIONS_PENDING"
    projected = [
        {
            "source_path": record["source_path"],
            "sha256": record["sha256"],
            "size_bytes": record["size_bytes"],
        }
        for record in manifest["files"]
    ]
    assert binding["checked_sources"] == projected


def test_commit_binding_rejects_witness_table_mismatch(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    witness = root / builder.WITNESS_SOURCE_PATH
    witness.write_text('{"records": ["changed"]}\n', encoding="utf-8", newline="\n")
    with pytest.raises(RuntimeError, match="commit binding mismatch"):
        builder.build_upload_set(root, tmp_path / "upload", specs=specs, revision=commit)


def test_commit_binding_rejects_current_source_mismatch(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    (root / "source/readme.md").write_text("changed\n", encoding="utf-8", newline="\n")
    with pytest.raises(RuntimeError, match="commit binding mismatch"):
        builder.build_upload_set(root, tmp_path / "upload", specs=specs, revision=commit)


def test_commit_binding_rejects_allowlisted_source_missing_from_commit(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    missing = root / "source/not-in-commit.txt"
    missing.write_text("working tree only\n", encoding="utf-8", newline="\n")
    extended_specs = specs + (
        builder.FileSpec(
            "source/not-in-commit.txt",
            "source/not-in-commit.txt",
            "working_tree_only",
        ),
    )
    commit = _commit_synthetic_sources(root, specs)
    with pytest.raises(RuntimeError, match="not present in selected commit"):
        builder.build_upload_set(
            root,
            tmp_path / "upload",
            specs=extended_specs,
            revision=commit,
        )


def test_tampering_is_reported_without_touching_source_pdf(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    commit = _commit_synthetic_sources(root, specs)
    output = tmp_path / "upload"
    builder.build_upload_set(root, output, specs=specs, revision=commit)

    pdf = output / builder.UPLOAD_PDF_NAME
    pdf.write_bytes(pdf.read_bytes() + b"tampered\n")
    summary = verifier.verify_upload_directory(output)
    assert not summary["passed"]
    assert "standalone PDF SHA-256 mismatch" in summary["supplement"]["external_pdf_errors"]
    assert (root / builder.PDF_SOURCE_PATH).read_bytes().startswith(b"%PDF-1.7")


def test_source_allowlist_rejects_pdf_and_third_party_paths(
    builder: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    with pytest.raises(ValueError, match="standalone PDF"):
        builder._normalise_specs(
            [builder.FileSpec("paper/source.pdf", "source.pdf", "pdf")]
        )
    with pytest.raises(ValueError, match="third-party path"):
        builder._normalise_specs(
            [builder.FileSpec("references/papers/source.txt", "source.txt", "bad")]
        )


def test_default_allowlist_uses_final_pdf_and_zenodo_literature_documents(
    builder: ModuleType,
) -> None:
    specs = builder._normalise_specs(builder.DEFAULT_SOURCE_FILE_SPECS)
    paths = {spec.source_path for spec in specs}
    assert builder.PDF_SOURCE_PATH == "output/pdf/paper1_statewise_operator_v0.4.2.pdf"
    assert builder.PDF_BUILD_REPORT_PATH == "reports/v0.4.2_paper1_pdf_build_2026-08-07.md"
    assert "zenodo/paper1-v0.4.2/UPLOAD_CHECKLIST.md" in paths
    assert builder.ZENODO_FORM_VALUES_PATH in paths
    assert builder.ZENODO_SUBMISSION_POLICY_NOTE_PATH in paths
    assert builder.ZENODO_LITERATURE_REPORT_PATH in paths
    assert builder.ZENODO_LITERATURE_NOTE_PATH in paths
    assert builder.ZENODO_PREDRAFT_REPORT_PATH in paths
    assert builder.ZENODO_PREDRAFT_NOTE_PATH in paths
    assert builder.ZENODO_PREDRAFT_PREDECESSOR_REPORT_PATH in paths
    assert builder.ZENODO_PREDRAFT_PREDECESSOR_NOTE_PATH in paths
    assert builder.ZENODO_PREDRAFT_NORMALIZER_PATH not in paths
    assert builder.ZENODO_PREDRAFT_LEDGER_PATH not in paths
    assert not any(path.startswith("references/papers/") for path in paths)


def test_zenodo_form_values_match_metadata_and_no_reservation_policy(
    builder: ModuleType,
) -> None:
    metadata = json.loads(
        (REPOSITORY_ROOT / builder.METADATA_TEMPLATE_PATH).read_text(encoding="utf-8")
    )
    owner = json.loads(
        (REPOSITORY_ROOT / builder.OWNER_DECISION_ARTIFACT_PATH).read_text(
            encoding="utf-8"
        )
    )
    form_values = (REPOSITORY_ROOT / builder.ZENODO_FORM_VALUES_PATH).read_text(
        encoding="utf-8"
    )
    assert metadata["doi_policy"] == owner["decisions"]["doi"]
    availability = metadata["data_code_availability"]
    assert availability["exact_commit_recorded_in_supplement_manifest_at_build"] is True
    assert availability["exact_commit_recorded_in_external_receipt_at_build"] is True
    assert availability["remote_commit_visibility_verified_by_builder"] is False
    assert "exact_commit_recorded_in_external_zenodo_metadata_at_deposit" not in availability
    assert owner["decisions"]["doi"]["draft_reservation_requested"] is False
    assert all(value is False for value in owner["release_gates"].values())
    for value in (
        metadata["title"],
        metadata["description"],
        *metadata["keywords"],
        builder.UPLOAD_PDF_NAME,
        builder.UPLOAD_SUPPLEMENT_NAME,
        "No draft reservation; Zenodo assigns/registers DOI at publication.",
        "Technical info",
        "Other",
        "ZENODO_UPLOAD_RECEIPT.md",
    ):
        assert value in form_values
    assert "02f31f1a2135b97f00f794dff510309fb82f15d8" not in form_values


def test_cli_requires_commit_or_explicit_unbound_preview(builder: ModuleType) -> None:
    with pytest.raises(SystemExit):
        builder._parse_args(["--output-dir", "preview"])
    preview = builder._parse_args(
        ["--output-dir", "preview", "--unbound-preview"]
    )
    assert preview.revision is None
    assert preview.unbound_preview is True
    bound = builder._parse_args(
        ["--output-dir", "release", "--commit", "HEAD"]
    )
    assert bound.revision == "HEAD"
    assert bound.unbound_preview is False
    with pytest.raises(SystemExit):
        builder._parse_args(
            [
                "--output-dir",
                "release",
                "--commit",
                "HEAD",
                "--unbound-preview",
            ]
        )


def test_output_must_be_external(builder: ModuleType, tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    with pytest.raises(ValueError, match="outside the repository root"):
        builder.build_upload_set(root, root / "upload", specs=specs)


def test_output_dir_must_be_new_or_empty(builder: ModuleType, tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    output = tmp_path / "upload"
    output.mkdir()
    marker = output / "do-not-overwrite.txt"
    marker.write_text("sentinel\n", encoding="utf-8")
    with pytest.raises(ValueError, match="new or empty"):
        builder.build_upload_set(root, output, specs=specs)
    assert marker.read_text(encoding="utf-8") == "sentinel\n"


def test_candidate_source_gate_fails_closed_on_boundary_drift(
    builder: ModuleType, tmp_path: Path
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _synthetic_root(builder, root)
    main = root / "paper/v0.4.2_paper1_statewise_operator/main.tex"
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "Claim-locked archive/submission candidate, Paper I v0.4.2.",
            "Claim-locked candidate with an unreviewed boundary.",
        ),
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(RuntimeError, match="candidate source boundary is incomplete"):
        builder._validate_candidate_source(root)


def test_pdf_rebind_pending_is_a_single_fail_closed_error(
    builder: ModuleType, tmp_path: Path
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _synthetic_root(builder, root)
    manifest_path = root / builder.MANUSCRIPT_MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = manifest["tex_build"]["current_observation"]
    current["main_tex_raw_sha256"] = "0" * 64
    manifest["tex_build"]["pending_source_rebind"] = {
        "status": "PENDING_DOCKER_REBUILD_AND_VISUAL_QA",
        "current_source_raw_sha256": hashlib.sha256(
            (root / "paper/v0.4.2_paper1_statewise_operator/main.tex").read_bytes()
        ).hexdigest(),
        "publication_blocking": True,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(RuntimeError, match="PDF_REBIND_NOT_FINAL"):
        builder._validate_pdf_binding(root)


def test_final_rebind_status_is_packagable_without_hardcoded_hashes(
    builder: ModuleType, tmp_path: Path
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _synthetic_root(builder, root)
    manifest_path = root / builder.MANUSCRIPT_MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    main_sha = hashlib.sha256(
        (root / "paper/v0.4.2_paper1_statewise_operator/main.tex").read_bytes()
    ).hexdigest()
    manifest["tex_build"]["pending_source_rebind"] = {
        "status": "FINAL_VERIFIED_SOURCE_PDF_BINDING",
        "current_source_raw_sha256": main_sha,
        "source_pdf_binding_authorized": True,
        "publication_blocking": False,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    binding = builder._validate_pdf_binding(root)
    assert binding["pdf_source_main_sha256"] == main_sha
    assert binding["pdf_build_report_path"] == builder.PDF_BUILD_REPORT_PATH


def test_missing_final_source_binding_fails_closed(builder: ModuleType, tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    _synthetic_root(builder, root)
    manifest_path = root / builder.MANUSCRIPT_MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["tex_build"]["current_observation"]["source_pdf_binding"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(RuntimeError, match="PDF_REBIND_NOT_FINAL"):
        builder._validate_pdf_binding(root)
