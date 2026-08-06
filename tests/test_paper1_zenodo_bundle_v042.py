"""Focused tests for the Paper I single-archive upload and owner waiver."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ZENODO_DIRECTORY = REPOSITORY_ROOT / "zenodo" / "paper1-v0.4.2"


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
        "scripts/normalize_v042_paper1_zenodo_gate_20260806.py --check\n",
        encoding="utf-8",
        newline="\n",
    )

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


def test_single_archive_output_is_deterministic_and_verifiable(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    first = tmp_path / "upload-first"
    second = tmp_path / "upload-second"

    first_summary = builder.build_upload_set(root, first, specs=specs)
    builder.build_upload_set(root, second, specs=specs)

    expected_names = {builder.UPLOAD_ARCHIVE_NAME}
    assert set(first_summary["files"]) == expected_names
    assert first_summary["layout"] == builder.SINGLE_ARCHIVE_LAYOUT
    assert first_summary["zenodo_upload_files"] == [builder.UPLOAD_ARCHIVE_NAME]
    assert {path.name for path in first.iterdir()} == expected_names
    for name in expected_names:
        assert (first / name).read_bytes() == (second / name).read_bytes()

    verified = verifier.verify_upload_directory(first)
    assert verified["passed"]
    assert verified["archive"]["inner_supplement"]["passed"]
    assert verified["archive"]["inner_supplement"]["pdf_members"] == []
    assert verified["archive"]["inner_supplement"]["forbidden_members"] == []

    with tarfile.open(first / builder.UPLOAD_ARCHIVE_NAME, mode="r:gz") as archive:
        members = archive.getmembers()
    assert all(member.name.startswith(f"{builder.OUTER_PREFIX}/") for member in members)
    assert all(member.mode == 0o644 for member in members)
    assert all((member.uid, member.gid) == (0, 0) for member in members)
    assert all((member.uname, member.gname) == ("", "") for member in members)
    assert all(member.mtime == 0 for member in members)
    assert first_summary["pdf_binding"]["pdf_page_count"] == 18


def test_two_file_layout_requires_and_records_owner_waiver(
    builder: ModuleType,
    verifier: ModuleType,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    specs = _synthetic_root(builder, root)
    with pytest.raises(ValueError, match="owner_waiver"):
        builder.build_upload_set(root, tmp_path / "without-waiver", specs=specs, layout="two_file")
    output = tmp_path / "waived"
    summary = builder.build_upload_set(
        root,
        output,
        specs=specs,
        layout="two_file",
        owner_waiver=True,
    )
    assert summary["layout"] == builder.TWO_FILE_OWNER_WAIVER_LAYOUT
    assert summary["owner_waiver"] is True
    assert set(summary["files"]) == {builder.UPLOAD_PDF_NAME, builder.UPLOAD_SUPPLEMENT_NAME}
    assert not verifier.verify_upload_directory(output)["passed"]
    verified = verifier.verify_upload_directory(
        output,
        allow_two_file_owner_waiver=True,
    )
    assert verified["passed"]


def test_commit_binding_checks_all_allowlisted_source_bytes_and_stays_out_of_archive(
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
    assert summary["commit_binding"]["checked_source_count"] == len(specs) + 1
    assert builder.WITNESS_SOURCE_PATH in summary["commit_binding"]["automatic_sources"]
    assert any(
        record["path"] == builder.WITNESS_SOURCE_PATH
        for record in summary["commit_binding"]["checked_sources"]
    )
    with tarfile.open(output / builder.UPLOAD_ARCHIVE_NAME, mode="r:gz") as archive:
        manifest_member = next(
            member
            for member in archive.getmembers()
            if member.name.endswith("/upload_checksums.json")
        )
        handle = archive.extractfile(manifest_member)
        assert handle is not None
        manifest = json.loads(handle.read().decode("utf-8"))
    assert "commit" not in manifest
    assert "packaged_commit" not in manifest


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
    output = tmp_path / "upload"
    builder.build_upload_set(
        root,
        output,
        specs=specs,
        layout="two_file",
        owner_waiver=True,
    )

    pdf = output / builder.UPLOAD_PDF_NAME
    pdf.write_bytes(pdf.read_bytes() + b"tampered\n")
    summary = verifier.verify_upload_directory(
        output,
        allow_two_file_owner_waiver=True,
    )
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
    assert builder.PDF_BUILD_REPORT_PATH == "reports/v0.4.2_paper1_pdf_build_2026-08-06.md"
    assert "zenodo/paper1-v0.4.2/UPLOAD_CHECKLIST.md" in paths
    assert builder.ZENODO_LITERATURE_REPORT_PATH in paths
    assert builder.ZENODO_LITERATURE_NOTE_PATH in paths
    assert not any(path.startswith("references/papers/") for path in paths)


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
