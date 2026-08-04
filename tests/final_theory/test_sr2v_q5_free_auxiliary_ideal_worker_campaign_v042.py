"""Fast host-side guards for the isolated stage worker and campaign."""

from __future__ import annotations

import gzip
import hashlib
import subprocess
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_campaign_v042 as campaign
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_stage_plan_v042 as stage_plan
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_supervisor_v042 as supervisor
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker


def _request() -> dict[str, Any]:
    factors = [
        {
            "aliases": [f"lambda({index},0)"],
            "expression": f"t1 + {index + 1}",
            "factor_id": f"lambda_{index}_0",
            "polynomial": [[[], index + 1, 1]],
        }
        for index in range(14)
    ]
    return {
        "schema_version": worker.REQUEST_SCHEMA,
        "bottom_factor_records": factors,
        "chart": "U2",
        "chart_factor_polynomial_id": 4,
        "chart_factor_sha256": "a" * 64,
        "expected_root_semantic_digest_sha256": "b" * 64,
        "expected_worker_source_sha256": "c" * 64,
        "factor_group_order": ["chart", "bottom", "torus"],
        "groebner_algorithm": "libsingular:slimgb",
        "incremental_batch_sizes": [1],
        "max_live_basis_terms": 5_000_000,
        "max_loaded_terms": 5_000_000,
        "memory_limit_bytes": 8 * 1024**3,
        "method": "build_only",
        "modulus": 32003,
        "monomial_order": "degrevlex",
        "root_manifest_path": "results/root.json",
        "selected_entry_indices": [1],
        "selected_generator_rows_sha256": "d" * 64,
        "soft_rss_limit_bytes": 7 * 1024**3,
        "stage_plan_sha256": "e" * 64,
    }


def test_request_envelope_round_trip_is_canonical_and_strict(tmp_path: Path) -> None:
    request = _request()
    envelope = supervisor.create_recipe_envelope(request)
    path = tmp_path / "request.json"
    path.write_bytes(supervisor.canonical_json_bytes(envelope) + b"\n")

    assert worker.load_verified_request(path) == request

    tampered = dict(request)
    tampered["modulus"] = True
    bad_envelope = supervisor.create_recipe_envelope(tampered)
    path.write_bytes(supervisor.canonical_json_bytes(bad_envelope) + b"\n")
    with pytest.raises(worker.WorkerInputError, match="modulus"):
        worker.load_verified_request(path)


def test_request_rejects_factor_omission_and_unsafe_paths() -> None:
    request = _request()
    request["factor_group_order"] = ["chart", "chart", "torus"]
    with pytest.raises(worker.WorkerInputError, match="permutation"):
        worker.validate_request(request)

    request = _request()
    request["root_manifest_path"] = "../root.json"
    with pytest.raises(worker.WorkerInputError, match="escape"):
        worker.validate_request(request)


def test_incremental_batches_must_be_strict_nested_prefixes_ending_at_stage() -> None:
    request = _request()
    request["method"] = "incremental_native_saturation"
    request["selected_entry_indices"] = [1, 2, 3]
    request["incremental_batch_sizes"] = [1, 3]
    worker.validate_request(request)

    request["incremental_batch_sizes"] = [1, 2]
    with pytest.raises(worker.WorkerInputError, match="end at"):
        worker.validate_request(request)

    request["incremental_batch_sizes"] = [2, 1, 3]
    with pytest.raises(worker.WorkerInputError, match="increase strictly"):
        worker.validate_request(request)


def test_redundancy_audit_uses_the_nonincremental_full_stage_contract() -> None:
    request = _request()
    request["method"] = "redundancy_audit"
    worker.validate_request(request)


@pytest.mark.parametrize("method", ["libsingular_ab_saturation", "libsingular_system_saturation"])
def test_direct_libsingular_methods_use_the_nonincremental_contract(method: str) -> None:
    request = _request()
    request["method"] = method
    worker.validate_request(request)


def test_selected_rows_are_derived_from_the_root_not_supplied_as_polynomials() -> None:
    root = {
        "chart_generator_ids": {
            "charts": {
                "U2": {
                    "generator_polynomial_ids": [
                        [0, 0, 0],
                        [1, 4, 5],
                        [2, 6, 7],
                    ]
                }
            }
        }
    }
    request = _request()
    request["selected_entry_indices"] = [2, 1]
    request["selected_generator_rows_sha256"] = worker.canonical_sha256([[2, 6, 7], [1, 4, 5]])

    assert worker.selected_generator_rows(root, request) == [[2, 6, 7], [1, 4, 5]]

    request["selected_generator_rows_sha256"] = "0" * 64
    with pytest.raises(worker.WorkerInputError, match="disagree"):
        worker.selected_generator_rows(root, request)


def _arena_record(identifier: int, terms: list[Any]) -> dict[str, Any]:
    return {
        "polynomial_id": identifier,
        "sha256": stage_plan.canonical_digest(terms),
        "term_count": len(terms),
        "terms": terms,
    }


def test_metadata_scan_authenticates_chunks_without_full_arena_materialisation(
    tmp_path: Path,
) -> None:
    records = [
        _arena_record(0, []),
        _arena_record(1, [[[[0, 1]], 1, 1], [[], 2, 1]]),
    ]
    raw = b"".join(worker.canonical_json_bytes(record) + b"\n" for record in records)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    directory = tmp_path / "bundle"
    directory.mkdir()
    (directory / "polynomial.jsonl.gz").write_bytes(compressed)
    correspondence = [[record["polynomial_id"], record["sha256"]] for record in records]
    chunks = [
        {
            "arena": "polynomial_arena",
            "gzip_bytes": len(compressed),
            "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
            "path": "polynomial.jsonl.gz",
            "record_count": len(records),
            "uncompressed_bytes": len(raw),
            "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        }
    ]
    root: dict[str, Any] = {
        "arena_index": {
            "polynomial_arena": {
                "polynomial_id_to_sha256": correspondence,
                "polynomial_id_to_sha256_digest_sha256": stage_plan.canonical_digest(
                    correspondence
                ),
                "record_count": len(records),
                "term_count_total": 2,
            }
        },
        "chunk_ledger": {
            "chunks": chunks,
            "chunk_ledger_digest_sha256": stage_plan.canonical_digest(chunks),
            "directory": "bundle",
        },
    }
    root["semantic_digest_sha256"] = stage_plan.canonical_digest(root)

    cache = campaign.build_verified_arena_metadata_cache(tmp_path, root)

    assert cache["polynomial_metadata"]["1"]["term_count"] == 2
    assert stage_plan.validate_arena_metadata_cache(cache, root)[1]["term_count"] == 2


@pytest.mark.parametrize(
    ("text", "expected"),
    [("0B", 0), ("1KiB", 1024), ("1.5MiB", 1572864), ("8GiB", 8 * 1024**3)],
)
def test_docker_memory_parser(text: str, expected: int) -> None:
    assert campaign.parse_memory_quantity(text) == expected


def test_docker_memory_parser_rejects_unknown_units() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        campaign.parse_memory_quantity("12 elephants")


def test_docker_stats_parser_records_cpu_memory_and_pids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def stats(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            ["docker", "stats"],
            0,
            stdout='{"CPUPerc":"101.25%","PIDs":"2","MemUsage":"1.5MiB / 8GiB"}\n',
            stderr="",
        )

    monkeypatch.setattr(campaign, "_run_command", stats)

    assert campaign._container_stats(tmp_path, "worker") == {  # noqa: SLF001
        "container_cpu_percent": 101.25,
        "container_pids": 2,
        "memory_bytes": 1572864,
    }


def test_legacy_process_audit_recognises_the_module_worker_command() -> None:
    assert campaign._is_legacy_worker_process_line(  # noqa: SLF001
        "7 1 python3 -m universe_lab.final_theory."
        "sr2v_q5_free_auxiliary_ideal_worker_v042 --request request.json"
    )
    assert not campaign._is_legacy_worker_process_line(  # noqa: SLF001
        "1 0 sage-jupyter --no-browser"
    )


def test_host_process_termination_escalates_and_verifies_exit() -> None:
    class StubbornProcess:
        returncode: int | None = None
        terminated = False
        killed = False

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True

        def kill(self) -> None:
            self.killed = True
            self.returncode = 137

        def wait(self, timeout: int) -> int:
            if not self.killed:
                raise subprocess.TimeoutExpired("docker compose run", timeout)
            assert timeout == 5
            return 137

    process = StubbornProcess()

    assert campaign._terminate_host_process(process) is True  # type: ignore[arg-type]  # noqa: SLF001
    assert process.terminated is True
    assert process.killed is True


def test_campaign_file_lock_rejects_a_concurrent_holder(tmp_path: Path) -> None:
    lock_path = tmp_path / "campaign.lock"

    with campaign.CampaignFileLock(lock_path):
        with pytest.raises(campaign.CampaignError, match="holds the OS lock"):
            with campaign.CampaignFileLock(lock_path):
                pytest.fail("a second campaign acquired the single-worker lock")

    with campaign.CampaignFileLock(lock_path):
        assert lock_path.is_file()


def test_docker_daemon_failure_is_not_misclassified_as_container_absence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def daemon_down(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            ["docker", "inspect"],
            1,
            stdout="",
            stderr="Cannot connect to the Docker daemon",
        )

    monkeypatch.setattr(campaign, "_run_command", daemon_down)

    with pytest.raises(campaign.CampaignError, match="without proving absence"):
        campaign._inspect_container(tmp_path, "missing")  # noqa: SLF001
    assert campaign._cleanup_container(tmp_path, "missing") is False  # noqa: SLF001


def test_docker_explicit_no_such_container_is_authenticated_absence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_such(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            ["docker", "inspect"],
            1,
            stdout="",
            stderr="Error: No such object: definitely-absent",
        )

    monkeypatch.setattr(campaign, "_run_command", no_such)

    assert campaign._inspect_container(tmp_path, "definitely-absent") is None  # noqa: SLF001


@pytest.mark.parametrize(
    "probe",
    [campaign._container_memory, campaign._container_process_audit],  # noqa: SLF001
)
def test_runtime_probe_accepts_only_authenticated_normal_exit_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    probe: Any,
) -> None:
    def stopped(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            ["docker", "probe"],
            1,
            stdout="",
            stderr="Error response from daemon: container abc is not running",
        )

    monkeypatch.setattr(campaign, "_run_command", stopped)

    assert probe(tmp_path, "abc") is None


@pytest.mark.parametrize(
    "probe",
    [campaign._container_memory, campaign._container_process_audit],  # noqa: SLF001
)
def test_runtime_probe_does_not_hide_daemon_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    probe: Any,
) -> None:
    def daemon_down(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            ["docker", "probe"],
            1,
            stdout="",
            stderr="Cannot connect to the Docker daemon",
        )

    monkeypatch.setattr(campaign, "_run_command", daemon_down)

    with pytest.raises(campaign.CampaignError):
        probe(tmp_path, "abc")
