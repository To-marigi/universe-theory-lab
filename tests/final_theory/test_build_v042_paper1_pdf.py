from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT_PATH = ROOT / "scripts/build_v042_paper1_pdf.py"
PINNED_IMAGE = (
    "texlive/texlive:latest-medium@"
    "sha256:d79913b74afcf48a53ec2ad0d54b70ad3e36d65b4f1de13d811435883c2f1fd9"
)


def _load_builder() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_build_v042_paper1_pdf_module",
        BUILD_SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _fake_repository(root: Path) -> Path:
    paper = root / "paper/v0.4.2_paper1_statewise_operator"
    shared = root / "paper/v0.3.9_d2_commutativity_short_report"
    paper.mkdir(parents=True)
    shared.mkdir(parents=True)
    (paper / "main.tex").write_text(
        r"\bibliography{../v0.3.9_d2_commutativity_short_report/references,references}",
        encoding="utf-8",
    )
    (paper / "references.bib").write_text("@misc{Local, year={2026}}\n", encoding="utf-8")
    (paper / "REPRODUCING.md").write_text("fixture\n", encoding="utf-8")
    (paper / "main.log").write_text("stale log\n", encoding="utf-8")
    (paper / "main.pdf").write_bytes(b"stale PDF")
    (shared / "references.bib").write_text("@misc{Shared, year={2026}}\n", encoding="utf-8")
    return root


def _successful_runner(repository_root: Path, pdf_bytes: bytes):
    def run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        mirrors = list((repository_root / "tmp/pdfs").glob("paper1-build-*"))
        assert len(mirrors) == 1
        paper = mirrors[0] / "paper/v0.4.2_paper1_statewise_operator"
        (paper / "main.pdf").write_bytes(pdf_bytes)
        (paper / "main.log").write_text(
            f"Output written on main.pdf (10 pages, {len(pdf_bytes)} bytes).\n",
            encoding="utf-8",
        )
        output = "\n".join(
            (
                "PAPER1_TOOL_LATEXMK=Latexmk, Version 4.88",
                "PAPER1_TOOL_PDFTEX=pdfTeX 1.40.29 (TeX Live 2026)",
                "PAPER1_TOOL_BIBTEX=BibTeX 0.99e (TeX Live 2026)",
            )
        )
        return subprocess.CompletedProcess(command, 0, stdout=output)

    return run


def test_digest_pinned_docker_plan_and_dry_run_contract(tmp_path: Path) -> None:
    builder = _load_builder()
    repository_root = _fake_repository(tmp_path / "unicode-宇宙")
    mirror = repository_root / "tmp/pdfs/paper1-build-TEMPORARY_ID"

    command = builder.docker_command(mirror)
    assert builder.IMAGE_REF == PINNED_IMAGE
    assert PINNED_IMAGE in command
    assert "texlive/texlive:latest-medium" not in command
    assert "--rm" in command
    assert "--network=none" in command
    assert builder.CONTAINER_WORKDIR in command
    mount = command[command.index("--mount") + 1]
    assert str(mirror.resolve()) in mount
    assert "dst=/workspace" in mount

    output = repository_root / "output/pdf/draft.pdf"
    payload = builder.dry_run_payload(repository_root, output)
    assert payload["status"] == "DRY_RUN"
    assert payload["image_ref"] == PINNED_IMAGE
    assert payload["docker_executed"] is False
    assert payload["output_path"] == "output/pdf/draft.pdf"
    assert not output.exists()
    assert "--dry-run" in builder._parser().format_help()


@pytest.mark.parametrize(
    ("line", "diagnostic"),
    [
        (r"Overfull \hbox (11.65pt too wide) in paragraph", "overfull_hbox"),
        (
            "LaTeX Warning: Citation `Missing' on page 1 undefined on input line 8.",
            "undefined_reference_or_citation",
        ),
        (
            "LaTeX Warning: There were undefined references.",
            "undefined_reference_or_citation",
        ),
        ("! LaTeX Error: Something broke.", "latex_or_package_error"),
        ("! Package hyperref Error: Bad option.", "latex_or_package_error"),
    ],
)
def test_final_log_blocking_diagnostics_are_fail_closed(line: str, diagnostic: str) -> None:
    builder = _load_builder()
    inspection = builder.inspect_log(line)
    assert inspection.blocking_total == 1
    assert inspection.blocking_counts[diagnostic] == 1


def test_clean_log_page_record_and_underfull_count() -> None:
    builder = _load_builder()
    log = "Output written on main.pdf (10 pages, 371899 bytes).\n"
    inspection = builder.inspect_log(log)
    assert inspection.blocking_total == 0
    assert inspection.underfull_box_count == 0
    assert builder.parse_pdf_log_record(log) == (10, 371899)
    assert builder.parse_pdf_log_record("no final PDF record") == (None, None)


def test_repository_shaped_mirror_is_cleaned_after_success_and_failure(tmp_path: Path) -> None:
    builder = _load_builder()
    repository_root = _fake_repository(tmp_path / "repository")
    mirror_parent = tmp_path / "mirrors"

    with builder.prepared_build_mirror(repository_root, mirror_parent) as mirror:
        successful_root = mirror.root
        assert (mirror.paper_dir / "main.tex").is_file()
        assert not (mirror.paper_dir / "main.log").exists()
        assert not (mirror.paper_dir / "main.pdf").exists()
        assert (mirror.root / builder.SHARED_BIB_RELATIVE).is_file()
    assert not successful_root.exists()

    failed_root: Path | None = None
    with pytest.raises(RuntimeError, match="synthetic failure"):
        with builder.prepared_build_mirror(repository_root, mirror_parent) as mirror:
            failed_root = mirror.root
            raise RuntimeError("synthetic failure")
    assert failed_root is not None
    assert not failed_root.exists()
    assert not list(mirror_parent.glob("paper1-build-*"))


def test_mocked_build_atomically_publishes_verified_json_contract(tmp_path: Path) -> None:
    builder = _load_builder()
    repository_root = _fake_repository(tmp_path / "repository")
    output = repository_root / "output/pdf/draft.pdf"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"previous output")
    pdf_bytes = b"%PDF-1.4\nmock draft\n%%EOF\n"

    payload = builder.build_pdf(
        repository_root,
        output,
        runner=_successful_runner(repository_root, pdf_bytes),
    )

    assert output.read_bytes() == pdf_bytes
    assert payload == {
        "status": "OK",
        "image_ref": PINNED_IMAGE,
        "docker_exit_code": 0,
        "toolchain": {
            "latexmk": "Latexmk, Version 4.88",
            "pdftex": "pdfTeX 1.40.29 (TeX Live 2026)",
            "bibtex": "BibTeX 0.99e (TeX Live 2026)",
        },
        "page_count": 10,
        "page_count_source": "FINAL_MAIN_LOG",
        "bytes": len(pdf_bytes),
        "sha256": builder._sha256(output),
        "output_path": "output/pdf/draft.pdf",
        "blocking_diagnostics": {
            "overfull_hbox": 0,
            "undefined_reference_or_citation": 0,
            "latex_or_package_error": 0,
        },
        "blocking_diagnostic_total": 0,
        "underfull_box_count": 0,
        "working_mirror": "REMOVED_ON_CONTEXT_EXIT",
    }
    assert not list((repository_root / "tmp/pdfs").glob("paper1-build-*"))
    assert not list(output.parent.glob(".draft.pdf.*.tmp"))
    json.dumps(payload)


def test_mocked_build_rejects_log_blockers_and_docker_failure(tmp_path: Path) -> None:
    builder = _load_builder()
    repository_root = _fake_repository(tmp_path / "repository")
    output = repository_root / "output/pdf/draft.pdf"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"preserve me")
    pdf_bytes = b"%PDF-1.4\nmock draft\n%%EOF\n"

    def blocked_runner(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        completed = _successful_runner(repository_root, pdf_bytes)(command)
        mirror = next((repository_root / "tmp/pdfs").glob("paper1-build-*"))
        (mirror / builder.PAPER_RELATIVE / "main.log").write_text(
            "Overfull \\hbox (1.0pt too wide)\n"
            f"Output written on main.pdf (10 pages, {len(pdf_bytes)} bytes).\n",
            encoding="utf-8",
        )
        return completed

    with pytest.raises(builder.BuildError, match="blocking TeX diagnostics"):
        builder.build_pdf(repository_root, output, runner=blocked_runner)
    assert output.read_bytes() == b"preserve me"
    assert not list((repository_root / "tmp/pdfs").glob("paper1-build-*"))

    def failed_runner(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 17, stdout="latexmk failed")

    with pytest.raises(builder.BuildError, match="exit code 17"):
        builder.build_pdf(repository_root, output, runner=failed_runner)
    assert output.read_bytes() == b"preserve me"
    assert not list((repository_root / "tmp/pdfs").glob("paper1-build-*"))
