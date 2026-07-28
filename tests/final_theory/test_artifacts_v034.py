from pathlib import Path

from universe_lab.final_theory.artifacts_v034 import (
    _is_v034_certificate,
    _normalise,
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


def test_v034_certificate_filter_preserves_unversioned_legacy_file(
    tmp_path: Path,
) -> None:
    generated = _touch(
        tmp_path,
        "certificates/d2_S1/chart_campaign.json",
    )
    versioned = _touch(
        tmp_path,
        "certificates/independent_oracle/v0.3.4_scalar_fixture.json",
    )
    legacy = _touch(
        tmp_path,
        "certificates/independent_oracle/oracle_result.json",
    )
    generated_paths = {generated.resolve()}

    assert _is_v034_certificate(generated, generated_paths)
    assert _is_v034_certificate(versioned, generated_paths)
    assert not _is_v034_certificate(legacy, generated_paths)


def test_normalise_preserves_domain_fields_and_updates_provenance() -> None:
    observed = _normalise(
        {
            "schema_version": "domain-v1",
            "source_index_branch": "DOMAIN_BRANCH",
            "production_commit": "old",
        },
        metadata={
            "schema_version": "common-v1",
            "source_index_branch": ["COMMON_BRANCH"],
            "production_commit": "new",
            "artifact_freeze_pointer": {"tag_name": "tag"},
        },
    )

    assert observed["schema_version"] == "domain-v1"
    assert observed["source_index_branch"] == "DOMAIN_BRANCH"
    assert observed["production_commit"] == "new"
    assert observed["artifact_freeze_pointer"] == {"tag_name": "tag"}
