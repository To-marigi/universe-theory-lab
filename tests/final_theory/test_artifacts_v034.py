from pathlib import Path

from universe_lab.final_theory.artifacts_v034 import (
    _reproduction_artifact_paths,
)


def _touch(root: Path, relative: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    return path


def test_reproduction_collector_accepts_both_version_spellings(
    tmp_path: Path,
) -> None:
    source = _touch(
        tmp_path,
        "src/universe_lab/final_theory/example_v034.py",
    )
    report = _touch(tmp_path, "reports/example_v0.3.4.md")
    result = _touch(tmp_path, "results/example_v0.3.4.json")
    certificate = _touch(tmp_path, "certificates/example/certificate.json")
    manifest = _touch(
        tmp_path,
        "results/reproduction_manifest_final_v0.3.4.json",
    )

    observed = _reproduction_artifact_paths(tmp_path, [certificate])

    assert source.resolve() in observed
    assert report.resolve() in observed
    assert result.resolve() in observed
    assert certificate.resolve() in observed
    assert manifest.resolve() not in observed
