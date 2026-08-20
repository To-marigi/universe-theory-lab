"""Build the v0.4.2 control/methods preprint in a pinned TeX container."""

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
PAPER_RELATIVE = Path("paper/v0.4.2_control_methods_scoped")
DEFAULT_OUTPUT_RELATIVE = Path("output/pdf/finite_qsg_fail_closed_methods_v0.4.2.pdf")
MIRROR_PARENT_RELATIVE = Path("tmp/pdfs")
CONTAINER_WORKDIR = "/workspace"
GENERATED_NAMES = {
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
TOOL_MARKERS = {
    "latexmk": "CONTROL_METHODS_TOOL_LATEXMK=",
    "pdftex": "CONTROL_METHODS_TOOL_PDFTEX=",
    "bibtex": "CONTROL_METHODS_TOOL_BIBTEX=",
}
CONTAINER_SCRIPT = """set -eu
export HOME=/tmp
printf 'CONTROL_METHODS_TOOL_LATEXMK='
latexmk -v | sed -n '/./{p;q;}'
printf 'CONTROL_METHODS_TOOL_PDFTEX='
pdftex --version | sed -n '/./{p;q;}'
printf 'CONTROL_METHODS_TOOL_BIBTEX='
bibtex --version | sed -n '/./{p;q;}'
exec latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
"""
DIAGNOSTIC_PATTERNS = {
    "overfull_box": re.compile(r"Overfull\s+\\[hv]box\b", re.IGNORECASE),
    "underfull_box": re.compile(r"Underfull\s+\\[hv]box\b", re.IGNORECASE),
    "undefined_reference_or_citation": re.compile(
        r"(?:reference|citation)s?.*undefined|undefined.*(?:reference|citation)s?",
        re.IGNORECASE,
    ),
    "latex_or_package_error": re.compile(
        r"(?:^!\s*)?(?:LaTeX|Package\b.*)\s+Error:", re.IGNORECASE
    ),
}
PDF_OUTPUT_PATTERN = re.compile(
    r"Output written on .*?\((\d+) pages?,\s*(\d+) bytes\)\.", re.DOTALL
)


class BuildError(RuntimeError):
    """Raised when the PDF build cannot be certified."""


class BuildMirror(NamedTuple):
    root: Path
    paper_dir: Path


Runner = Callable[..., subprocess.CompletedProcess[str]]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_bindings(repository_root: Path) -> list[dict[str, Any]]:
    bindings = []
    for name in ("main.tex", "references.bib", "REPRODUCING.md"):
        path = repository_root / PAPER_RELATIVE / name
        if not path.is_file():
            raise BuildError(f"required source is missing: {path}")
        data = path.read_bytes()
        if b"\r" in data:
            raise BuildError(f"source is not strict UTF-8 LF: {path}")
        data.decode("utf-8", errors="strict")
        bindings.append(
            {
                "path": (PAPER_RELATIVE / name).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return bindings


def _ignore_generated(_directory: str, names: list[str]) -> set[str]:
    return GENERATED_NAMES.intersection(names)


@contextmanager
def prepared_build_mirror(
    repository_root: Path,
    mirror_parent: Path | None = None,
) -> Iterator[BuildMirror]:
    repository_root = repository_root.resolve()
    _source_bindings(repository_root)
    parent = (
        mirror_parent.resolve()
        if mirror_parent is not None
        else (repository_root / MIRROR_PARENT_RELATIVE).resolve()
    )
    if mirror_parent is None and not parent.is_relative_to(repository_root):
        raise BuildError("temporary PDF mirror escaped the repository")
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="control-methods-build-", dir=parent) as tmp:
        root = Path(tmp)
        paper_dir = root / "paper"
        shutil.copytree(
            repository_root / PAPER_RELATIVE,
            paper_dir,
            ignore=_ignore_generated,
        )
        yield BuildMirror(root=root, paper_dir=paper_dir)


def docker_command(mirror: BuildMirror) -> list[str]:
    source = str(mirror.paper_dir.resolve())
    if "," in source:
        raise BuildError("Docker mount source paths containing commas are unsupported")
    command = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,size=512m",
        "--mount",
        f"type=bind,src={source},dst=/workspace",
        "--workdir",
        CONTAINER_WORKDIR,
    ]
    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    if os.name != "nt" and getuid is not None and getgid is not None:
        command.extend(["--user", f"{getuid()}:{getgid()}"])
    command.extend([IMAGE_REF, "sh", "-c", CONTAINER_SCRIPT])
    return command


def inspect_log(log_text: str) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {name: [] for name in DIAGNOSTIC_PATTERNS}
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        for name, pattern in DIAGNOSTIC_PATTERNS.items():
            if pattern.search(line):
                findings[name].append(line)
    return findings


def _parse_tools(output: str) -> dict[str, str]:
    tools: dict[str, str] = {}
    for line in output.splitlines():
        for name, marker in TOOL_MARKERS.items():
            if line.startswith(marker):
                tools[name] = line.removeprefix(marker).strip()
    return tools


def _parse_pdf_record(log_text: str) -> tuple[int | None, int | None]:
    matches = list(PDF_OUTPUT_PATTERN.finditer(log_text))
    if not matches:
        return None, None
    pages, byte_count = matches[-1].groups()
    return int(pages), int(byte_count)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as target, source.open("rb") as origin:
            shutil.copyfileobj(origin, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def build_pdf(
    repository_root: Path,
    output_path: Path,
    *,
    runner: Runner = subprocess.run,
    mirror_parent: Path | None = None,
) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    output_path = output_path.resolve()
    source_bindings = _source_bindings(repository_root)
    with prepared_build_mirror(repository_root, mirror_parent) as mirror:
        try:
            completed = runner(
                docker_command(mirror),
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
        output = completed.stdout or ""
        log_path = mirror.paper_dir / "main.log"
        log_text = (
            log_path.read_text(encoding="utf-8", errors="replace")
            if log_path.is_file()
            else ""
        )
        if completed.returncode != 0:
            tail = "\n".join(output.splitlines()[-50:])
            raise BuildError(
                f"Dockerized latexmk failed with exit code {completed.returncode}\n{tail}"
            )
        if not log_path.is_file():
            raise BuildError("latexmk succeeded but main.log is missing")
        diagnostics = inspect_log(log_text)
        if any(diagnostics.values()):
            raise BuildError(
                "TeX diagnostics block release: "
                + json.dumps(diagnostics, ensure_ascii=False, sort_keys=True)
            )
        tools = _parse_tools(output)
        if set(tools) != set(TOOL_MARKERS):
            raise BuildError(f"container tool markers are incomplete: {sorted(tools)}")
        built_pdf = mirror.paper_dir / "main.pdf"
        if not built_pdf.is_file() or built_pdf.stat().st_size == 0:
            raise BuildError("latexmk did not produce a nonempty main.pdf")
        if built_pdf.read_bytes()[:5] != b"%PDF-":
            raise BuildError("generated main.pdf lacks a PDF header")
        pages, logged_bytes = _parse_pdf_record(log_text)
        actual_bytes = built_pdf.stat().st_size
        if pages is None or logged_bytes != actual_bytes:
            raise BuildError(
                f"final PDF log record mismatch: pages={pages}, "
                f"logged_bytes={logged_bytes}, actual_bytes={actual_bytes}"
            )
        pdf_hash = sha256_file(built_pdf)
        _atomic_copy(built_pdf, output_path)
        if sha256_file(output_path) != pdf_hash:
            raise BuildError("atomic PDF copy failed hash verification")
    return {
        "status": "PASS",
        "image_ref": IMAGE_REF,
        "network_disabled": True,
        "container_root_read_only": True,
        "toolchain": tools,
        "source_bindings": source_bindings,
        "output_path": output_path.relative_to(repository_root).as_posix(),
        "page_count": pages,
        "bytes": actual_bytes,
        "sha256": pdf_hash,
        "diagnostic_counts": {name: 0 for name in DIAGNOSTIC_PATTERNS},
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the scoped control/methods PDF in a pinned container."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_RELATIVE)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repository_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        if shutil.which("docker") is None:
            raise BuildError("Docker is unavailable; host TeX is not accepted")
        payload = build_pdf(root, output)
    except (BuildError, OSError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
