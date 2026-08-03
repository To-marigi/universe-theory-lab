"""Fail-closed guards for the two-tier Phase-A bundle freeze."""

from __future__ import annotations

import gzip
import json
import struct
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_bundle_v042 as bundle

ROOT = Path(__file__).resolve().parents[2]


def _records(count: int, *, terms_per_record: int = 3) -> list[dict[str, Any]]:
    records = []
    for identifier in range(count):
        terms = [
            [[[0, identifier], [1, index]], identifier + index + 1, 2]
            for index in range(terms_per_record)
        ]
        records.append(
            {
                "polynomial_id": identifier,
                "term_count": len(terms),
                "sha256": bundle._digest(terms),
                "terms": terms,
            }
        )
    return records


def _write(tmp_path: Path, name: str, records: list[dict[str, Any]], target: int) -> Any:
    return bundle.write_arena_chunks(tmp_path, "polynomial_arena", records, target_bytes=target)


def test_chunks_round_trip_every_record(tmp_path: Path) -> None:
    records = _records(40)
    chunks = _write(tmp_path, "a", records, 900)
    assert len(chunks) > 1, "the sample must exercise more than one chunk"
    restored = list(bundle.read_arena_chunks(tmp_path, [chunk.as_json() for chunk in chunks]))
    assert restored == records


def test_chunk_boundaries_respect_the_target_without_splitting_a_record(
    tmp_path: Path,
) -> None:
    records = _records(40)
    target = 900
    chunks = _write(tmp_path, "a", records, target)
    assert sum(chunk.record_count for chunk in chunks) == len(records)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    for index, chunk in enumerate(chunks):
        if index < len(chunks) - 1:
            assert chunk.uncompressed_bytes <= target
        assert chunk.first_polynomial_id <= chunk.last_polynomial_id
        assert chunk.last_polynomial_id - chunk.first_polynomial_id + 1 == chunk.record_count
    assert chunks[0].first_polynomial_id == 0
    assert chunks[-1].last_polynomial_id == len(records) - 1


def test_chunk_bytes_are_deterministic(tmp_path: Path) -> None:
    """Two writes of the same records must produce byte-identical archives."""

    records = _records(40)
    first = bundle.write_arena_chunks(
        tmp_path / "first", "polynomial_arena", records, target_bytes=900
    )
    second = bundle.write_arena_chunks(
        tmp_path / "second", "polynomial_arena", records, target_bytes=900
    )
    assert [chunk.as_json() for chunk in first] == [chunk.as_json() for chunk in second]
    for chunk in first:
        assert (tmp_path / "first" / chunk.path).read_bytes() == (
            tmp_path / "second" / chunk.path
        ).read_bytes()


def test_gzip_headers_carry_no_timestamp_or_filename(tmp_path: Path) -> None:
    """A wall-clock mtime or an embedded name would break byte reproducibility."""

    chunks = _write(tmp_path, "a", _records(8), 10_000)
    raw = (tmp_path / chunks[0].path).read_bytes()
    assert raw[:2] == b"\x1f\x8b"
    (mtime,) = struct.unpack("<I", raw[4:8])
    assert mtime == bundle.GZIP_MTIME == 0
    flags = raw[3]
    assert not flags & 0x08, "FNAME flag set: the archive embeds a filename"


def test_missing_chunk_is_reported(tmp_path: Path) -> None:
    chunks = _write(tmp_path, "a", _records(20), 700)
    ledger = [chunk.as_json() for chunk in chunks]
    (tmp_path / chunks[-1].path).unlink()
    with pytest.raises(FileNotFoundError):
        list(bundle.read_arena_chunks(tmp_path, ledger))


def test_tampered_archive_is_rejected(tmp_path: Path) -> None:
    chunks = _write(tmp_path, "a", _records(20), 700)
    ledger = [chunk.as_json() for chunk in chunks]
    target = tmp_path / chunks[0].path
    payload = gzip.decompress(target.read_bytes()).replace(b'"term_count":3', b'"term_count":4', 1)
    target.write_bytes(bundle._compress(payload))
    with pytest.raises(ValueError, match="gzip (byte count|digest)"):
        list(bundle.read_arena_chunks(tmp_path, ledger))

    # Even with the transport-level ledger entries repaired, the authoritative
    # uncompressed digest still refuses the altered canonical bytes.
    repacked = target.read_bytes()
    ledger[0]["gzip_bytes"] = len(repacked)
    ledger[0]["gzip_sha256"] = bundle.hashlib.sha256(repacked).hexdigest()
    with pytest.raises(ValueError, match="uncompressed (byte count|digest)"):
        list(bundle.read_arena_chunks(tmp_path, ledger))


def test_uncompressed_digest_is_the_authority(tmp_path: Path) -> None:
    """Repacking the same bytes keeps the archive valid; changing them does not."""

    chunks = _write(tmp_path, "a", _records(20), 700)
    ledger = [chunk.as_json() for chunk in chunks]
    target = tmp_path / chunks[0].path
    original = gzip.decompress(target.read_bytes())

    # A different gzip encoding of identical canonical bytes is a transport-level
    # difference: the ledger's gzip entry catches it, and the record is refused.
    target.write_bytes(gzip.compress(original, compresslevel=9, mtime=0))
    with pytest.raises(ValueError, match="gzip (byte count|digest)"):
        list(bundle.read_arena_chunks(tmp_path, ledger))

    # With the gzip ledger entry updated to the repacked archive, the
    # uncompressed digest still certifies the mathematical content.
    repacked = target.read_bytes()
    ledger[0]["gzip_bytes"] = len(repacked)
    ledger[0]["gzip_sha256"] = bundle.hashlib.sha256(repacked).hexdigest()
    restored = list(bundle.read_arena_chunks(tmp_path, ledger))
    assert len(restored) == sum(int(entry["record_count"]) for entry in ledger)


def test_record_count_mismatch_is_rejected(tmp_path: Path) -> None:
    chunks = _write(tmp_path, "a", _records(20), 700)
    ledger = [chunk.as_json() for chunk in chunks]
    ledger[0]["record_count"] = int(ledger[0]["record_count"]) + 1
    with pytest.raises(ValueError, match="record count"):
        list(bundle.read_arena_chunks(tmp_path, ledger))


def test_non_contiguous_identifiers_are_refused(tmp_path: Path) -> None:
    records = _records(6)
    records[3]["polynomial_id"] = 99
    with pytest.raises(AssertionError, match="not contiguous"):
        _write(tmp_path, "a", records, 10_000)


def _passing_verification(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "performed": True,
        "chunk_streaming_verified": True,
        "independent_recompilation_verified": True,
        "recompilation_checks": dict.fromkeys(bundle.REQUIRED_RECOMPILATION_CHECKS, True),
        "artifact_incomplete": False,
        "failures": [],
    }
    record.update(overrides)
    return record


def test_a_complete_verifier_pass_freezes() -> None:
    assert bundle._verdict_for(_passing_verification()) == bundle.FROZEN_VERDICT


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"performed": False}, id="never_run"),
        pytest.param({"chunk_streaming_verified": False}, id="chunks_unstreamed"),
        pytest.param({"independent_recompilation_verified": False}, id="not_recompiled"),
        pytest.param({"recompilation_checks": {}}, id="no_checks_recorded"),
    ],
)
def test_an_incomplete_verifier_pass_stays_unfrozen(overrides: dict[str, Any]) -> None:
    """Anything short of a full pass leaves the bundle a digest commitment."""

    assert bundle._verdict_for(_passing_verification(**overrides)) == bundle.OBSERVED_VERDICT


@pytest.mark.parametrize("missing", bundle.REQUIRED_RECOMPILATION_CHECKS)
def test_every_required_check_must_be_present_to_freeze(missing: str) -> None:
    """A check that was never recorded must not be read as a pass."""

    checks = dict.fromkeys(bundle.REQUIRED_RECOMPILATION_CHECKS, True)
    del checks[missing]
    assert (
        bundle._verdict_for(_passing_verification(recompilation_checks=checks))
        == bundle.OBSERVED_VERDICT
    )


@pytest.mark.parametrize("failing", bundle.REQUIRED_RECOMPILATION_CHECKS)
def test_any_failing_check_reports_an_incomplete_artifact(failing: str) -> None:
    checks = dict.fromkeys(bundle.REQUIRED_RECOMPILATION_CHECKS, True)
    checks[failing] = False
    assert (
        bundle._verdict_for(_passing_verification(recompilation_checks=checks))
        == bundle.INCOMPLETE_VERDICT
    )


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"artifact_incomplete": True}, id="declared_incomplete"),
        pytest.param({"failures": ["polynomial_arena: missing chunk"]}, id="recorded_failure"),
    ],
)
def test_a_damaged_artifact_is_reported_as_incomplete(overrides: dict[str, Any]) -> None:
    assert bundle._verdict_for(_passing_verification(**overrides)) == bundle.INCOMPLETE_VERDICT


def test_the_frozen_verdict_does_not_overclaim_byte_retention() -> None:
    """The bundle keeps the arenas and digests, not every byte of the manifest."""

    assert "DIGEST_AND_SOLVER_INPUTS_FROZEN" in bundle.FROZEN_VERDICT
    assert "NO_SOLVER_RUN" in bundle.FROZEN_VERDICT


def test_required_checks_cover_the_code_binding() -> None:
    """A recompilation under different sources must not certify this root."""

    assert "code_binding_hashes" in bundle.REQUIRED_RECOMPILATION_CHECKS


def test_regenerated_outputs_do_not_count_as_a_dirty_worktree() -> None:
    """The root and its report are rewritten by every run, so they prove nothing."""

    own = f" M {bundle.ROOT_RESULT_PATH}\n M {bundle.ROOT_REPORT_PATH}\n"
    assert bundle._dirty_paths_excluding_own_outputs(own) == []
    assert bundle._dirty_paths_excluding_own_outputs("") == []


def test_real_source_changes_still_mark_the_worktree_dirty() -> None:
    """Anything else uncommitted must keep the commit field honest."""

    status = (
        f" M {bundle.ROOT_RESULT_PATH}\n"
        f" M {bundle.COMPILER_MODULE_PATH}\n"
        "?? reports/some_new_report.md\n"
        'R  old/path.py -> "src/renamed module.py"\n'
    )
    assert bundle._dirty_paths_excluding_own_outputs(status) == [
        bundle.COMPILER_MODULE_PATH,
        "reports/some_new_report.md",
        "src/renamed module.py",
    ]


def test_bundle_arena_directory_is_not_tracked_in_git() -> None:
    """The arenas must stay out of the repository; only the root is tracked."""

    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "results/*" in ignore
    assert f"!{bundle.ROOT_RESULT_PATH}" in ignore
    assert not any(line.strip() == f"!{bundle.BUNDLE_DIRECTORY}" for line in ignore)
    assert not any(line.strip().startswith(f"!{bundle.BUNDLE_DIRECTORY}/") for line in ignore)


@pytest.mark.skipif(
    not (ROOT / bundle.ROOT_RESULT_PATH).is_file(),
    reason="the bundle root has not been produced in this working tree",
)
def test_committed_root_is_internally_consistent() -> None:
    manifest_root = json.loads((ROOT / bundle.ROOT_RESULT_PATH).read_text(encoding="utf-8"))
    assert manifest_root["schema_version"] == bundle.SCHEMA
    assert manifest_root["semantic_digest_sha256"] == bundle.semantic_digest(manifest_root)
    assert manifest_root["verdict"] in {
        bundle.FROZEN_VERDICT,
        bundle.OBSERVED_VERDICT,
        bundle.INCOMPLETE_VERDICT,
    }
    assert manifest_root["search_terminal"] == bundle.SEARCH_TERMINAL
    assert manifest_root["full_logical_payload"]["tracked_in_git"] is False
    assert manifest_root["chunk_ledger"]["tracked_in_git"] is False
    assert manifest_root["row_index"]["row_count"] == 1127
    assert manifest_root["chart_generator_ids"]["chart_count"] == 6

    ledger = manifest_root["chunk_ledger"]
    assert ledger["chunk_ledger_digest_sha256"] == bundle._digest(ledger["chunks"])
    for name in bundle.ARENA_NAMES:
        index = manifest_root["arena_index"][name]
        assert index["polynomial_id_to_sha256_digest_sha256"] == bundle._digest(
            index["polynomial_id_to_sha256"]
        )
        chunked = sum(
            int(chunk["record_count"]) for chunk in ledger["chunks"] if chunk["arena"] == name
        )
        assert chunked == index["record_count"]
    for chunk in ledger["chunks"]:
        assert chunk["authoritative_digest"] == "uncompressed_sha256"
        assert chunk["codec"] == bundle.CODEC
        assert chunk["codec_mtime"] == bundle.GZIP_MTIME

    if manifest_root["verdict"] == bundle.FROZEN_VERDICT:
        verification = manifest_root["verification"]
        assert verification["chunk_streaming_verified"] is True
        assert verification["independent_recompilation_verified"] is True
        assert not verification["failures"]


@pytest.mark.skipif(
    not (ROOT / bundle.ROOT_RESULT_PATH).is_file(),
    reason="the bundle root has not been produced in this working tree",
)
def test_committed_report_is_an_exact_LF_render_of_the_root() -> None:
    manifest_root = json.loads((ROOT / bundle.ROOT_RESULT_PATH).read_text(encoding="utf-8"))
    frozen = (ROOT / bundle.ROOT_REPORT_PATH).read_text(encoding="utf-8")
    assert frozen == bundle.render_root_report(manifest_root)
    assert "\r" not in frozen
