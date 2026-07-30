from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FALLBACK_TEXT_SUFFIXES = {
    ".bib",
    ".cff",
    ".csv",
    ".example",
    ".json",
    ".jsonl",
    ".lock",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".sage",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}
FALLBACK_TEXT_FILENAMES = {
    ".gitattributes",
    ".gitignore",
    ".python-version",
    "LICENSE",
}
FALLBACK_IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "outreach",
    "tmp",
}


def _git_tracked_text_paths(root: Path) -> list[Path] | None:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--eol", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None

    paths: list[Path] = []
    for raw_record in completed.stdout.split(b"\0"):
        if not raw_record:
            continue
        metadata, separator, raw_path = raw_record.partition(b"\t")
        if not separator:
            raise AssertionError(f"unexpected git ls-files --eol record: {raw_record!r}")
        index_eol = metadata.split(maxsplit=1)[0]
        if index_eol == b"i/-text":
            continue
        path = root / raw_path.decode("utf-8")
        if path.is_file():
            paths.append(path)
    return paths


def _fallback_text_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for directory, directory_names, filenames in root.walk():
        directory_names[:] = [
            name for name in directory_names if name not in FALLBACK_IGNORED_DIRECTORIES
        ]
        for filename in filenames:
            path = directory / filename
            if (
                path.name in FALLBACK_TEXT_FILENAMES
                or path.suffix.lower() in FALLBACK_TEXT_SUFFIXES
            ):
                paths.append(path)
    return paths


def _text_paths(root: Path) -> Iterable[Path]:
    tracked = _git_tracked_text_paths(root)
    return tracked if tracked is not None else _fallback_text_paths(root)


def test_tracked_text_files_contain_no_carriage_returns() -> None:
    offenders: list[str] = []
    for path in _text_paths(ROOT):
        if b"\r" in path.read_bytes():
            offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, (
        "tracked text files must use LF only; CRLF and lone CR bytes found in: "
        + ", ".join(sorted(offenders))
    )


def test_wheels_are_explicitly_binary_in_gitattributes() -> None:
    rules = {
        tuple(line.split())
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert ("*.whl", "binary") in rules
