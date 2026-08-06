"""Build the Paper I v0.4.2 archive/submission-candidate PDF.

The repository's TeX source refers to a bibliography in a sibling paper
directory.  This helper therefore builds from a temporary repository-shaped
mirror instead of mounting the manuscript directory by itself.  The mirror is
removed on both success and failure, and the generated PDF is copied to its
host destination with an atomic replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, NamedTuple

IMAGE_REF = (
    "texlive/texlive:latest-medium@"
    "sha256:d79913b74afcf48a53ec2ad0d54b70ad3e36d65b4f1de13d811435883c2f1fd9"
)
PAPER_RELATIVE = Path("paper/v0.4.2_paper1_statewise_operator")
SHARED_BIB_RELATIVE = Path("paper/v0.3.9_d2_commutativity_short_report/references.bib")
DEFAULT_OUTPUT_RELATIVE = Path("output/pdf/paper1_statewise_operator_v0.4.2.pdf")
MIRROR_PARENT_RELATIVE = Path("tmp/pdfs")
CONTAINER_WORKDIR = f"/workspace/{PAPER_RELATIVE.as_posix()}"

TOOLCHAIN_MARKERS = {
    "latexmk": "PAPER1_TOOL_LATEXMK=",
    "pdftex": "PAPER1_TOOL_PDFTEX=",
    "bibtex": "PAPER1_TOOL_BIBTEX=",
}
CONTAINER_SCRIPT = """set -eu
printf 'PAPER1_TOOL_LATEXMK='
latexmk -v | sed -n '/./{p;q;}'
printf 'PAPER1_TOOL_PDFTEX='
pdftex --version | sed -n '/./{p;q;}'
printf 'PAPER1_TOOL_BIBTEX='
bibtex --version | sed -n '/./{p;q;}'
exec latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
"""

BLOCKING_LOG_PATTERNS = {
    "overfull_hbox": re.compile(r"Overfull\s+\\hbox\b", re.IGNORECASE),
    "undefined_reference_or_citation": re.compile(
        r"(?:reference|citation)s?.*undefined|undefined.*(?:reference|citation)s?",
        re.IGNORECASE,
    ),
    "latex_or_package_error": re.compile(
        r"(?:^!\s*)?(?:LaTeX|Package\b.*)\s+Error:",
        re.IGNORECASE,
    ),
}
UNDERFULL_BOX_PATTERN = re.compile(r"Underfull\s+\\[hv]box\b", re.IGNORECASE)
PDF_OUTPUT_PATTERN = re.compile(
    r"Output written on .*?\((\d+) pages?,\s*(\d+) bytes\)\.",
    re.DOTALL,
)
GENERATED_PAPER_FILES = {
    "main.aux",
    "main.bbl",
    "main.blg",
    "main.fdb_latexmk",
    "main.fls",
    "main.log",
    "main.out",
    "main.pdf",
    "main.run.xml",
    "main.synctex.gz",
    "main.toc",
}


class BuildError(RuntimeError):
    """A fail-closed PDF build or verification error."""


class BuildMirror(NamedTuple):
    root: Path
    paper_dir: Path


class LogInspection(NamedTuple):
    blocking_counts: dict[str, int]
    blocking_excerpts: dict[str, list[str]]
    underfull_box_count: int

    @property
    def blocking_total(self) -> int:
        return sum(self.blocking_counts.values())


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_sources(repository_root: Path) -> None:
    required = (
        repository_root / PAPER_RELATIVE / "main.tex",
        repository_root / PAPER_RELATIVE / "references.bib",
        repository_root / SHARED_BIB_RELATIVE,
    )
    missing = [path for path in required if not path.is_file()]
    if missing:
        rendered = ", ".join(path.as_posix() for path in missing)
        raise BuildError(f"required TeX build source is missing: {rendered}")


def _ignore_generated_paper_files(_directory: str, names: list[str]) -> set[str]:
    return GENERATED_PAPER_FILES.intersection(names)


@contextmanager
def prepared_build_mirror(
    repository_root: Path,
    mirror_parent: Path | None = None,
) -> Iterator[BuildMirror]:
    """Yield a clean repository-shaped mirror and remove it on every exit."""

    repository_root = repository_root.resolve()
    _validate_sources(repository_root)
    parent = (
        mirror_parent.resolve()
        if mirror_parent is not None
        else (repository_root / MIRROR_PARENT_RELATIVE).resolve()
    )
    if mirror_parent is None:
        try:
            parent.relative_to(repository_root)
        except ValueError as exc:
            raise BuildError("temporary PDF mirror parent escaped the repository") from exc
    parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="paper1-build-", dir=parent) as temporary:
        mirror_root = Path(temporary)
        paper_target = mirror_root / PAPER_RELATIVE
        shutil.copytree(
            repository_root / PAPER_RELATIVE,
            paper_target,
            ignore=_ignore_generated_paper_files,
        )
        shared_target = mirror_root / SHARED_BIB_RELATIVE
        shared_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository_root / SHARED_BIB_RELATIVE, shared_target)
        yield BuildMirror(root=mirror_root, paper_dir=paper_target)


def docker_command(mirror_root: Path) -> list[str]:
    """Return the exact digest-pinned Docker invocation for a prepared mirror."""

    mount_source = str(mirror_root.resolve())
    if "," in mount_source:
        raise BuildError("Docker --mount source paths containing commas are unsupported")
    command = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--mount",
        f"type=bind,src={mount_source},dst=/workspace",
        "--workdir",
        CONTAINER_WORKDIR,
    ]
    getuid: Callable[[], int] | None = getattr(os, "getuid", None)
    getgid: Callable[[], int] | None = getattr(os, "getgid", None)
    if os.name != "nt" and getuid is not None and getgid is not None:
        command.extend(
            [
                "--user",
                f"{getuid()}:{getgid()}",
                "--env",
                "HOME=/tmp",
            ]
        )
    command.extend([IMAGE_REF, "sh", "-c", CONTAINER_SCRIPT])
    return command


def inspect_log(log_text: str) -> LogInspection:
    """Classify final-main.log diagnostics that block a successful build."""

    excerpts: dict[str, list[str]] = {name: [] for name in BLOCKING_LOG_PATTERNS}
    underfull_count = 0
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        for name, pattern in BLOCKING_LOG_PATTERNS.items():
            if pattern.search(line):
                excerpts[name].append(line)
        if UNDERFULL_BOX_PATTERN.search(line):
            underfull_count += 1
    counts = {name: len(lines) for name, lines in excerpts.items()}
    return LogInspection(
        blocking_counts=counts,
        blocking_excerpts=excerpts,
        underfull_box_count=underfull_count,
    )


def parse_toolchain(container_output: str) -> dict[str, str]:
    toolchain: dict[str, str] = {}
    for line in container_output.splitlines():
        for name, marker in TOOLCHAIN_MARKERS.items():
            if line.startswith(marker):
                toolchain[name] = line.removeprefix(marker).strip()
    return toolchain


def parse_pdf_log_record(log_text: str) -> tuple[int | None, int | None]:
    matches = list(PDF_OUTPUT_PATTERN.finditer(log_text))
    if not matches:
        return None, None
    page_count, byte_count = matches[-1].groups()
    return int(page_count), int(byte_count)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as target, source.open("rb") as origin:
            shutil.copyfileobj(origin, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def _output_display_path(repository_root: Path, output_path: Path) -> str:
    resolved = output_path.resolve()
    try:
        return resolved.relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _failure_tail(container_output: str, limit: int = 40) -> str:
    return "\n".join(container_output.splitlines()[-limit:])


def build_pdf(
    repository_root: Path,
    output_path: Path,
    *,
    runner: Runner = subprocess.run,
    mirror_parent: Path | None = None,
) -> dict[str, Any]:
    """Build, inspect, and atomically publish the candidate PDF."""

    repository_root = repository_root.resolve()
    output_path = output_path.resolve()
    result: dict[str, Any]
    with prepared_build_mirror(repository_root, mirror_parent) as mirror:
        command = docker_command(mirror.root)
        try:
            completed = runner(
                command,
                cwd=repository_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise BuildError(f"cannot execute Docker: {exc}") from exc

        container_output = completed.stdout or ""
        log_path = mirror.paper_dir / "main.log"
        log_text = (
            log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
        )
        inspection = inspect_log(log_text)
        if completed.returncode != 0:
            tail = _failure_tail(container_output)
            raise BuildError(
                f"Dockerized latexmk failed with exit code {completed.returncode}\n{tail}"
            )
        if not log_path.is_file():
            raise BuildError("Dockerized latexmk exited successfully but final main.log is missing")
        if inspection.blocking_total:
            details = json.dumps(inspection.blocking_excerpts, ensure_ascii=False, sort_keys=True)
            raise BuildError(f"blocking TeX diagnostics found in final main.log: {details}")

        toolchain = parse_toolchain(container_output)
        missing_tools = sorted(set(TOOLCHAIN_MARKERS) - set(toolchain))
        if missing_tools:
            raise BuildError(f"container toolchain markers are missing: {missing_tools}")

        built_pdf = mirror.paper_dir / "main.pdf"
        if not built_pdf.is_file() or built_pdf.stat().st_size == 0:
            raise BuildError("Dockerized latexmk did not produce a nonempty main.pdf")
        with built_pdf.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise BuildError("generated main.pdf lacks a PDF header")

        page_count, logged_bytes = parse_pdf_log_record(log_text)
        actual_bytes = built_pdf.stat().st_size
        if logged_bytes is not None and logged_bytes != actual_bytes:
            raise BuildError(
                "main.log byte count does not match generated PDF: "
                f"logged={logged_bytes}, actual={actual_bytes}"
            )
        source_digest = _sha256(built_pdf)
        _atomic_copy(built_pdf, output_path)
        if _sha256(output_path) != source_digest:
            raise BuildError("atomic output copy failed SHA-256 verification")

        result = {
            "status": "OK",
            "image_ref": IMAGE_REF,
            "docker_exit_code": completed.returncode,
            "toolchain": toolchain,
            "page_count": page_count,
            "page_count_source": (
                "FINAL_MAIN_LOG" if page_count is not None else "UNAVAILABLE_FROM_FINAL_MAIN_LOG"
            ),
            "bytes": actual_bytes,
            "sha256": source_digest,
            "output_path": _output_display_path(repository_root, output_path),
            "blocking_diagnostics": inspection.blocking_counts,
            "blocking_diagnostic_total": inspection.blocking_total,
            "underfull_box_count": inspection.underfull_box_count,
            "working_mirror": "REMOVED_ON_CONTEXT_EXIT",
        }
    return result


def dry_run_payload(repository_root: Path, output_path: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    _validate_sources(repository_root)
    placeholder = repository_root / MIRROR_PARENT_RELATIVE / "paper1-build-TEMPORARY_ID"
    return {
        "status": "DRY_RUN",
        "image_ref": IMAGE_REF,
        "docker_command": docker_command(placeholder),
        "output_path": _output_display_path(repository_root, output_path),
        "mirror_parent": MIRROR_PARENT_RELATIVE.as_posix(),
        "docker_executed": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and verify the Paper I v0.4.2 PDF in a digest-pinned TeX container."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: inferred from this script)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_RELATIVE,
        help=f"output PDF path (default: {DEFAULT_OUTPUT_RELATIVE.as_posix()})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the pinned build plan as JSON without invoking Docker or writing a PDF",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repository_root = args.repository_root.resolve()
    output_path = args.output
    if not output_path.is_absolute():
        output_path = repository_root / output_path
    try:
        if args.dry_run:
            payload = dry_run_payload(repository_root, output_path)
        else:
            if shutil.which("docker") is None:
                raise BuildError("Docker is unavailable; the host TeX toolchain is not used")
            payload = build_pdf(repository_root, output_path)
    except (BuildError, OSError) as exc:
        print(
            json.dumps(
                {"status": "ERROR", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
