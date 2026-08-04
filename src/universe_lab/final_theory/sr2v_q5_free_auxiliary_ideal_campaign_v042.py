"""Fail-closed host campaign for stage-specific SR2-V Sage attempts.

This is the control plane for the redesigned solver.  It authenticates and
scans the frozen arena into a lightweight term-count plan, creates an immutable
content-addressed attempt, and runs exactly one dedicated ``sage-solver``
container.  The container has no network, sees the repository read-only, and
is polled for state and memory while worker progress is durably hash-chained.

The supported mathematical routes are bounded non-aligned U2/U3/U4 pilots:
materialisation, sequential saturation, and a versioned determinantal CEGAR
scout.  A finite-field run is explicitly a scout; even a positive
determinantal condition remains direct-lift-pending.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Final

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as bottom_global
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_bundle_v042 as bundle
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_manifest_v042 as manifest
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_solver_v042 as legacy_solver
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_stage_plan_v042 as stage_plan
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_supervisor_v042 as supervisor
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker

SUPERVISED_DIRECTORY: Final = Path("results/v0.4.2_sr2v_q5_free_auxiliary_ideal_supervised")
ATTEMPTS_DIRECTORY: Final = SUPERVISED_DIRECTORY / "attempts"
METADATA_DIRECTORY: Final = SUPERVISED_DIRECTORY / "metadata"
WORKER_MODULE: Final = "universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_worker_v042"
CONTAINER_IMAGE: Final = "sagemath/sagemath:10.9"
CONTAINER_SERVICE: Final = "sage-solver"
CONTAINER_PREFIX: Final = "sr2v-aux-"
SOFT_RSS_GIB: Final = 7
MAX_LOADED_TERMS: Final = 5_000_000
MAX_LIVE_BASIS_TERMS: Final = 5_000_000
MAX_DETERMINANTAL_LIVE_BASIS_TERMS: Final = 100_000
MAX_DETERMINANTAL_ROUNDS: Final = 8
MAX_DETERMINANTAL_MINORS: Final = 64
MAX_GENERATED_MINOR_TERMS: Final = 40_000
MAX_DETERMINANTAL_CERTIFICATE_TERMS: Final = 100_000
MAX_DETERMINANTAL_CERTIFICATE_BYTES: Final = 8 * 1024**2
DEFAULT_PILOT_TIMEOUT_SECONDS: Final = 300
DEFAULT_POLL_SECONDS: Final = 15.0
FINALIZATION_RESERVE_SECONDS: Final = 120

_POLYNOMIAL_HEADER_RE = re.compile(
    rb'^\{"polynomial_id":([0-9]+),"sha256":"([0-9a-f]{64})",'
    rb'"term_count":([0-9]+),"terms":'
)
_MEMORY_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?i?B)$", re.IGNORECASE)


class CampaignError(RuntimeError):
    """A host-side campaign invariant failed."""


class CampaignFileLock:
    """One non-blocking OS lock spanning planning, execution, and finalization."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle: IO[bytes] | None = None

    def __enter__(self) -> CampaignFileLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            if os.name == "nt":
                msvcrt = __import__("msvcrt")
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl = __import__("fcntl")
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, ImportError) as error:
            handle.close()
            raise CampaignError("another supervised solver campaign holds the OS lock") from error
        self._handle = handle
        return self

    def __exit__(self, *_exc_info: object) -> None:
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                msvcrt = __import__("msvcrt")
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl = __import__("fcntl")
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _announce(event: str, **fields: object) -> None:
    message = {"event": event, "host_elapsed_seconds": fields.pop("host_elapsed_seconds", None)}
    message.update(fields)
    print(supervisor.canonical_json_bytes(message).decode("utf-8"), flush=True)


def _run_command(
    arguments: Sequence[str],
    *,
    root: Path,
    timeout: float = 30.0,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(arguments),
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CampaignError(f"command failed to run: {arguments[0]}: {error}") from error
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2000:]
        raise CampaignError(
            f"command exited {completed.returncode}: {' '.join(arguments[:4])}: {detail}"
        )
    return completed


def _read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CampaignError(f"{path}: JSON object required")
    return value


def _stream_sha256(path: Path) -> tuple[int, str]:
    size = 0
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


def _source_snapshot(repository_root: Path) -> dict[str, Any]:
    paths = [
        Path(__file__).resolve(),
        Path(worker.__file__).resolve(),
        Path(supervisor.__file__).resolve(),
        Path(stage_plan.__file__).resolve(),
        repository_root / "compose.yaml",
    ]
    records: dict[str, Any] = {}
    for path in paths:
        relative = path.relative_to(repository_root).as_posix()
        raw = path.read_bytes()
        records[relative] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "text": raw.decode("utf-8"),
        }
    return {"records": records, "schema_version": "sr2v-solver-source-snapshot-v1"}


def build_verified_arena_metadata_cache(
    repository_root: Path,
    frozen_root: Mapping[str, Any],
    *,
    progress_started: float | None = None,
) -> dict[str, Any]:
    """Scan authenticated chunk bytes and build the lightweight planning cache.

    Unlike the legacy iterator, this never JSON-decodes an irrelevant term
    array.  Per-record term counts are still authoritative because the complete
    uncompressed byte stream is checked against the frozen chunk ledger.
    """

    bindings = stage_plan._validate_root(frozen_root)  # noqa: SLF001
    expected = bindings["expected_polynomial_sha256"]
    directory = (repository_root / str(frozen_root["chunk_ledger"]["directory"])).resolve()
    if repository_root.resolve() not in (directory, *directory.parents):
        raise CampaignError("bundle directory escapes the repository")
    chunks = [
        record
        for record in frozen_root["chunk_ledger"]["chunks"]
        if record["arena"] == stage_plan.POLYNOMIAL_ARENA
    ]
    metadata: dict[int, dict[str, Any]] = {}
    total_terms = 0
    total_records = 0
    for chunk_index, chunk in enumerate(chunks):
        path = (directory / str(chunk["path"])).resolve()
        if directory not in (path, *path.parents):
            raise CampaignError(f"chunk path escapes its directory: {chunk['path']}")
        compressed_size, compressed_digest = _stream_sha256(path)
        if compressed_size != int(chunk["gzip_bytes"]):
            raise CampaignError(f"{chunk['path']}: gzip byte count mismatch")
        if compressed_digest != chunk["gzip_sha256"]:
            raise CampaignError(f"{chunk['path']}: gzip digest mismatch")
        raw_digest = hashlib.sha256()
        raw_size = 0
        chunk_records = 0
        with gzip.open(path, "rb") as handle:
            for line in handle:
                raw_digest.update(line)
                raw_size += len(line)
                chunk_records += 1
                match = _POLYNOMIAL_HEADER_RE.match(line)
                if match is None or not line.endswith(b"}\n"):
                    raise CampaignError(f"{chunk['path']}: noncanonical polynomial record")
                identifier = int(match.group(1))
                digest = match.group(2).decode("ascii")
                term_count = int(match.group(3))
                if expected.get(identifier) != digest:
                    raise CampaignError(
                        f"{chunk['path']}: polynomial {identifier} disagrees with the root"
                    )
                if identifier in metadata:
                    raise CampaignError(f"duplicate polynomial id in chunk stream: {identifier}")
                metadata[identifier] = {"sha256": digest, "term_count": term_count}
                total_terms += term_count
                total_records += 1
        if chunk_records != int(chunk["record_count"]):
            raise CampaignError(f"{chunk['path']}: record count mismatch")
        if raw_size != int(chunk["uncompressed_bytes"]):
            raise CampaignError(f"{chunk['path']}: uncompressed byte count mismatch")
        if raw_digest.hexdigest() != chunk["uncompressed_sha256"]:
            raise CampaignError(f"{chunk['path']}: uncompressed digest mismatch")
        elapsed = None if progress_started is None else time.monotonic() - progress_started
        _announce(
            "METADATA_CHUNK_VERIFIED",
            chunk_index=chunk_index,
            chunks_total=len(chunks),
            host_elapsed_seconds=elapsed,
            records_scanned=total_records,
            terms_indexed=total_terms,
        )
    if set(metadata) != set(expected):
        missing = sorted(set(expected) - set(metadata))
        raise CampaignError(f"metadata scan is incomplete; first missing id={missing[0]}")
    if total_records != int(bindings["record_count"]):
        raise CampaignError("metadata scan record total mismatch")
    if total_terms != int(bindings["term_count_total"]):
        raise CampaignError("metadata scan term total mismatch")

    ordered = [
        [identifier, metadata[identifier]["term_count"], metadata[identifier]["sha256"]]
        for identifier in sorted(metadata)
    ]
    cache_key = stage_plan.canonical_digest(
        {
            "arena": stage_plan.POLYNOMIAL_ARENA,
            "committed_arena_index_digest_sha256": bindings["arena_index_digest"],
            "committed_chunk_ledger_digest_sha256": bindings["chunk_ledger_digest"],
            "committed_root_semantic_digest_sha256": bindings["root_digest"],
        }
    )
    cache: dict[str, Any] = {
        "schema_version": stage_plan.ARENA_CACHE_SCHEMA_VERSION,
        "arena": stage_plan.POLYNOMIAL_ARENA,
        "committed_root_semantic_digest_sha256": bindings["root_digest"],
        "committed_chunk_ledger_digest_sha256": bindings["chunk_ledger_digest"],
        "committed_arena_index_digest_sha256": bindings["arena_index_digest"],
        "cache_key_sha256": cache_key,
        "record_count": total_records,
        "term_count_total": total_terms,
        "polynomial_metadata": {
            str(identifier): metadata[identifier] for identifier in sorted(metadata)
        },
        "polynomial_metadata_digest_sha256": stage_plan.canonical_digest(ordered),
    }
    cache["semantic_digest_sha256"] = stage_plan.canonical_digest(cache)
    stage_plan.validate_arena_metadata_cache(cache, frozen_root)
    return cache


def _load_budget(repository_root: Path) -> supervisor.CampaignBudget:
    path = repository_root / legacy_solver.BUDGET_PATH
    payload = _read_json_object(path)
    return supervisor.validate_budget(payload)


def _bottom_factor_records(repository_root: Path, frozen_root: Mapping[str, Any]) -> list[Any]:
    basis = manifest._lambda_factor_basis()  # noqa: SLF001
    ledger, _product = manifest._bottom_localization_ledger(  # noqa: SLF001
        manifest._load(repository_root / bottom_global.RESULT_PATH),  # noqa: SLF001
        basis,
    )
    records = ledger["factors"]
    if (
        ledger["factor_ledger_sha256"]
        != frozen_root["ring_binding"]["bottom_localization_factor_ledger_sha256"]
    ):
        raise CampaignError("rebuilt bottom localization ledger disagrees with frozen root")
    return records


def _selected_entry_positions(plan: Mapping[str, Any], stage: Mapping[str, Any]) -> list[int]:
    rows = {
        int(row["unique_row_index"]): int(row["source_position"])
        for row in plan["row_selection"]["rows"]
    }
    return [rows[int(index)] for index in stage["selected_unique_row_indices"]]


def determinantal_resource_caps(selected_count: int) -> tuple[int, int]:
    """Keep later candidate expansions under the audited stage-7 resource envelope."""

    if type(selected_count) is not int or selected_count <= 0:
        raise ValueError("selected_count must be a positive integer")
    if selected_count <= 1:
        return 10_000, 10_000
    if selected_count <= 4:
        return 50_000, 20_000
    return MAX_DETERMINANTAL_LIVE_BASIS_TERMS, MAX_GENERATED_MINOR_TERMS


def build_stage_request(
    repository_root: Path,
    *,
    frozen_root: Mapping[str, Any],
    plan: Mapping[str, Any],
    stage: Mapping[str, Any],
    budget: supervisor.CampaignBudget,
    chart: str,
    modulus: int,
    method: str,
    monomial_order: str,
    groebner_algorithm: str,
    factor_group_order: Sequence[str],
    incremental_batch_sizes: Sequence[int],
) -> dict[str, Any]:
    positions = _selected_entry_positions(plan, stage)
    entries = frozen_root["chart_generator_ids"]["charts"][chart]["generator_polynomial_ids"]
    rows = [[int(value) for value in entries[position]] for position in positions]
    quotient = legacy_solver.resolve_chart_quotient_ids_cached(repository_root)
    quotient_key = chart.lower().replace("u", "d")
    factor_id = int(quotient["resolved"]["cleared"][quotient_key])
    factor_sha256 = str(quotient["target_sha256"][f"cleared_{quotient_key}"])
    selected_count = len(positions)
    determinantal_basis_cap, determinantal_minor_term_cap = determinantal_resource_caps(
        selected_count
    )
    determinantal_policy: dict[str, Any] | None = None
    if method in worker.DETERMINANTAL_METHODS:
        determinantal_policy = {
            "schema_version": worker.DETERMINANTAL_POLICY_SCHEMA,
            "certificate_requirement": "EXACT_EXPONENT_MEMBERSHIP_DIRECT_LIFT_PENDING",
            "coefficient_scope": (
                "QQ_EXACT_CANDIDATE" if modulus == 0 else "FINITE_FIELD_SCOUT_ONLY"
            ),
            "max_certificate_bytes": MAX_DETERMINANTAL_CERTIFICATE_BYTES,
            "max_certificate_terms": MAX_DETERMINANTAL_CERTIFICATE_TERMS,
            "max_generated_minor_terms": determinantal_minor_term_cap,
            "max_minor_count": MAX_DETERMINANTAL_MINORS,
            "max_rounds": MAX_DETERMINANTAL_ROUNDS,
            "minor_pair_policy": "CHEAPEST_PIVOT_STAR_THEN_COST_PREFIXES_1_2_4",
            "radical_target_policy": "ALL_EFFECTIVE_SELECTED_A_COMPONENTS",
            "row_universe_sha256": worker.canonical_sha256(entries),
            "selected_entry_indices_sha256": worker.canonical_sha256(positions),
            "task_kind": (
                "INVENTORY_ONLY"
                if method == worker.DETERMINANTAL_INVENTORY_METHOD
                else "COMBINED_SUBSET_CERTIFICATE"
            ),
            "verification_mode": "LIBSINGULAR_SAT_WITH_EXP_AND_CONTAINMENT",
        }
        determinantal_policy["semantic_digest_sha256"] = worker.semantic_digest(
            determinantal_policy
        )
    payload: dict[str, Any] = {
        "schema_version": worker.REQUEST_SCHEMA,
        "bottom_factor_records": _bottom_factor_records(repository_root, frozen_root),
        "chart": chart,
        "chart_factor_polynomial_id": factor_id,
        "chart_factor_sha256": factor_sha256,
        "determinantal_policy": determinantal_policy,
        "expected_root_semantic_digest_sha256": frozen_root["semantic_digest_sha256"],
        "expected_worker_source_sha256": worker.worker_source_sha256(),
        "factor_group_order": list(factor_group_order),
        "groebner_algorithm": groebner_algorithm,
        "incremental_batch_sizes": list(incremental_batch_sizes),
        "max_live_basis_terms": (
            determinantal_basis_cap
            if method in worker.DETERMINANTAL_METHODS
            else MAX_LIVE_BASIS_TERMS
        ),
        "max_loaded_terms": MAX_LOADED_TERMS,
        "memory_limit_bytes": budget.memory_limit_bytes,
        "method": method,
        "modulus": modulus,
        "monomial_order": monomial_order,
        "root_manifest_path": Path(bundle.ROOT_RESULT_PATH).as_posix(),
        "selected_entry_indices": positions,
        "selected_generator_rows_sha256": worker.canonical_sha256(rows),
        "soft_rss_limit_bytes": SOFT_RSS_GIB * 1024**3,
        "stage_plan_sha256": plan["semantic_digest_sha256"],
    }
    worker.validate_request(payload)
    return payload


def parse_memory_quantity(value: str) -> int:
    """Parse Docker's IEC/SI memory quantities into bytes."""

    match = _MEMORY_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"unsupported Docker memory quantity: {value!r}")
    number = float(match.group(1))
    unit = match.group(2).lower()
    factors = {
        "b": 1,
        "kb": 1000,
        "kib": 1024,
        "mb": 1000**2,
        "mib": 1024**2,
        "gb": 1000**3,
        "gib": 1024**3,
        "tb": 1000**4,
        "tib": 1024**4,
    }
    result = number * factors[unit]
    if not math_is_finite_nonnegative(result):
        raise ValueError(f"invalid Docker memory quantity: {value!r}")
    return int(result)


def math_is_finite_nonnegative(value: float) -> bool:
    return value >= 0 and value != float("inf") and value == value


def _image_digest(repository_root: Path) -> str:
    completed = _run_command(
        ["docker", "image", "inspect", CONTAINER_IMAGE, "--format", "{{.Id}}"],
        root=repository_root,
    )
    digest = completed.stdout.strip()
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise CampaignError(f"unexpected image digest: {digest!r}")
    return digest


def _is_legacy_worker_process_line(line: str) -> bool:
    columns = line.split(maxsplit=5)
    if len(columns) >= 5 and columns[4] == "Singular":
        return True
    markers = (
        "sage-eval",
        "sr2v_q5_free_auxiliary_ideal_worker=",
        WORKER_MODULE,
        "sr2v_q5_free_auxiliary_ideal_worker_v042.py",
    )
    return any(marker in line for marker in markers)


def _legacy_worker_processes(repository_root: Path) -> list[str]:
    service_result = _run_command(
        ["docker", "compose", "ps", "-q", "sage"], root=repository_root, check=False
    )
    if service_result.returncode != 0:
        raise CampaignError("could not identify the long-lived Sage service")
    service = service_result.stdout.strip()
    if not service:
        return []
    process_table = _run_command(
        ["docker", "exec", service, "ps", "-eo", "pid,ppid,rss,etimes,comm,args"],
        root=repository_root,
        check=False,
    )
    if process_table.returncode != 0:
        raise CampaignError("could not audit the long-lived Sage service process table")
    return [
        line for line in process_table.stdout.splitlines() if _is_legacy_worker_process_line(line)
    ]


def _stale_solver_containers(repository_root: Path) -> list[str]:
    completed = _run_command(["docker", "ps", "-a", "--format", "{{.Names}}"], root=repository_root)
    return [name for name in completed.stdout.splitlines() if name.startswith(CONTAINER_PREFIX)]


def preflight_process_audit(repository_root: Path) -> None:
    stale = _stale_solver_containers(repository_root)
    legacy = _legacy_worker_processes(repository_root)
    if stale or legacy:
        raise CampaignError(
            f"worker preflight failed; stale_containers={stale}, legacy_processes={legacy}"
        )


class DurableTextLog:
    def __init__(self, path: Path) -> None:
        self._handle: IO[str] = path.open("x", encoding="utf-8", newline="\n")

    def append(self, line: str) -> None:
        self._handle.write(line.rstrip("\r\n") + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def close(self) -> None:
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()


@dataclass(slots=True)
class ContainerOutcome:
    status: str
    wall_time_seconds: float
    worker_result: dict[str, Any] | None
    process_returncode: int | None
    peak_memory_bytes: int
    cleanup_verified: bool
    container_contract_verified: bool
    final_container_state: dict[str, Any] | None
    host_process_termination_verified: bool
    postflight_audit_verified: bool
    postflight_legacy_processes: list[str]
    postflight_stale_containers: list[str]


def _reader_thread(
    stream_name: str,
    handle: IO[str],
    messages: queue.Queue[tuple[str, str | None]],
) -> None:
    try:
        for line in handle:
            messages.put((stream_name, line))
    finally:
        messages.put((stream_name, None))


def _terminate_host_process(process: subprocess.Popen[str] | None) -> bool:
    if process is None:
        return True
    try:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        return process.poll() is not None
    except (Exception, KeyboardInterrupt):
        return process.poll() is not None


def _inspect_container(repository_root: Path, name: str) -> dict[str, Any] | None:
    completed = _run_command(
        ["docker", "inspect", name], root=repository_root, check=False, timeout=15
    )
    if completed.returncode != 0:
        diagnostic = f"{completed.stdout}\n{completed.stderr}".lower()
        if "no such object" in diagnostic or "no such container" in diagnostic:
            return None
        raise CampaignError(f"docker inspect failed without proving absence: {diagnostic[-2000:]}")
    value = json.loads(completed.stdout)
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise CampaignError("docker inspect returned an unexpected payload")
    return value[0]


def _container_stopped_during_probe(completed: subprocess.CompletedProcess[str]) -> bool:
    diagnostic = f"{completed.stdout}\n{completed.stderr}".lower()
    return "container " in diagnostic and " is not running" in diagnostic


def _container_stats(repository_root: Path, name: str) -> dict[str, int | float] | None:
    completed = _run_command(
        ["docker", "stats", "--no-stream", "--format", "{{json .}}", name],
        root=repository_root,
        check=False,
        timeout=20,
    )
    if completed.returncode != 0 and _container_stopped_during_probe(completed):
        return None
    if completed.returncode != 0:
        raise CampaignError(f"docker stats failed: {completed.stderr[-2000:]}")
    if not completed.stdout.strip():
        raise CampaignError("docker stats returned no telemetry for a running container")
    payload = json.loads(completed.stdout.splitlines()[-1])
    usage = str(payload["MemUsage"]).split("/", 1)[0].strip()
    cpu_text = str(payload["CPUPerc"]).strip()
    if not cpu_text.endswith("%"):
        raise CampaignError("docker stats returned an invalid CPU percentage")
    cpu_percent = float(cpu_text[:-1])
    pids = int(payload["PIDs"])
    if not math_is_finite_nonnegative(cpu_percent) or pids < 0:
        raise CampaignError("docker stats returned invalid CPU/PID telemetry")
    return {
        "container_cpu_percent": cpu_percent,
        "container_pids": pids,
        "memory_bytes": parse_memory_quantity(usage),
    }


def _container_memory(repository_root: Path, name: str) -> int | None:
    stats = _container_stats(repository_root, name)
    return None if stats is None else int(stats["memory_bytes"])


def _container_process_audit(repository_root: Path, name: str) -> dict[str, Any] | None:
    completed = _run_command(
        ["docker", "exec", name, "ps", "-eo", "pid,ppid,rss,etimes,time,comm,args"],
        root=repository_root,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0 and _container_stopped_during_probe(completed):
        return None
    if completed.returncode != 0:
        raise CampaignError(f"container process audit failed: {completed.stderr[-2000:]}")
    text = completed.stdout[-8000:]
    return {
        "process_table_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "process_table_tail": text,
        "ps_returncode": completed.returncode,
    }


def _cleanup_container(repository_root: Path, name: str) -> bool:
    try:
        inspected = _inspect_container(repository_root, name)
        if inspected is not None and bool(inspected.get("State", {}).get("Running")):
            stopped = _run_command(
                ["docker", "stop", "--time", "10", name],
                root=repository_root,
                check=False,
                timeout=20,
            )
            if stopped.returncode != 0:
                raise CampaignError(f"docker stop failed: {stopped.stderr[-2000:]}")
        removed = _run_command(
            ["docker", "rm", "--force", name],
            root=repository_root,
            check=False,
            timeout=20,
        )
        if removed.returncode != 0:
            diagnostic = f"{removed.stdout}\n{removed.stderr}".lower()
            if "no such container" not in diagnostic:
                raise CampaignError(f"docker rm failed: {diagnostic[-2000:]}")
        return _inspect_container(repository_root, name) is None
    except CampaignError:
        return False


def execute_container_attempt(
    repository_root: Path,
    *,
    attempt: supervisor.AttemptDirectory,
    request_container_path: str,
    container_name: str,
    expected_image_digest: str,
    expected_request_payload_sha256: str,
    hard_memory_bytes: int,
    soft_memory_bytes: int,
    timeout_seconds: int,
    poll_seconds: float,
) -> ContainerOutcome:
    """Run, poll, durably log, and finally remove one named container."""

    command = [
        "docker",
        "compose",
        "run",
        "--no-deps",
        "-T",
        "--name",
        container_name,
        CONTAINER_SERVICE,
        "sage",
        "-python",
        "-m",
        WORKER_MODULE,
        "--request",
        request_container_path,
    ]
    messages: queue.Queue[tuple[str, str | None]] = queue.Queue()
    started = time.monotonic()
    worker_result: dict[str, Any] | None = None
    request_verified_count = 0
    worker_result_count = 0
    worker_message_count = 0
    protocol_error: str | None = None
    container_contract_verified = False
    peak_memory = 0
    terminal_reason: str | None = None
    final_state: dict[str, Any] | None = None
    streams_open = {"stdout", "stderr"}
    process: subprocess.Popen[str] | None = None
    cleanup_verified = False
    host_process_termination_verified = True
    postflight_audit_verified = False
    postflight_legacy: list[str] = []
    postflight_stale: list[str] = []
    with supervisor.HashChainJsonlWriter(attempt.events_path) as events:
        stdout_log = DurableTextLog(attempt.path / "stdout.log")
        stderr_log = DurableTextLog(attempt.path / "stderr.log")
        try:
            events.append(
                {
                    "event": "CONTAINER_LAUNCH_REQUESTED",
                    "container_name": container_name,
                    "timeout_seconds": timeout_seconds,
                }
            )
            process = subprocess.Popen(
                command,
                cwd=repository_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None and process.stderr is not None
            for stream_name, handle in (("stdout", process.stdout), ("stderr", process.stderr)):
                threading.Thread(
                    target=_reader_thread,
                    args=(stream_name, handle, messages),
                    daemon=True,
                ).start()
            supervisor.write_attempt_state(
                attempt,
                "RUNNING",
                {"container_name": container_name, "host_pid": process.pid},
            )
            next_poll = started
            while process.poll() is None or streams_open:
                now = time.monotonic()
                wait_for = max(0.05, min(1.0, next_poll - now))
                try:
                    stream_name, line = messages.get(timeout=wait_for)
                except queue.Empty:
                    stream_name = ""
                    line = ""
                if stream_name:
                    if line is None:
                        streams_open.discard(stream_name)
                    else:
                        (stdout_log if stream_name == "stdout" else stderr_log).append(line)
                        parsed: object | None = None
                        if stream_name == "stdout":
                            try:
                                parsed = json.loads(line)
                            except json.JSONDecodeError:
                                parsed = None
                        if isinstance(parsed, dict) and parsed.get("schema_version") == (
                            worker.WORKER_MESSAGE_SCHEMA
                        ):
                            worker_message_count += 1
                            if worker_result is not None:
                                protocol_error = "WORKER_MESSAGE_AFTER_RESULT"
                            message_type = parsed.get("message_type")
                            worker_event = parsed.get("event")
                            if message_type not in {"progress", "result"}:
                                protocol_error = "UNKNOWN_WORKER_MESSAGE_TYPE"
                            if worker_event == "REQUEST_VERIFIED":
                                request_verified_count += 1
                                if worker_message_count != 1:
                                    protocol_error = "REQUEST_VERIFIED_NOT_FIRST"
                                if (
                                    parsed.get("request_payload_sha256")
                                    != expected_request_payload_sha256
                                ):
                                    protocol_error = "WORKER_REQUEST_DIGEST_MISMATCH"
                            elif request_verified_count != 1:
                                protocol_error = "WORKER_MESSAGE_BEFORE_REQUEST_VERIFICATION"
                            events.append({"event": "WORKER_MESSAGE", "message": parsed})
                            _announce(
                                "WORKER_MESSAGE",
                                worker_event=parsed.get("event"),
                                worker_elapsed_seconds=parsed.get("elapsed_seconds"),
                            )
                            if message_type == "result":
                                worker_result_count += 1
                                if worker_result_count > 1:
                                    protocol_error = "MULTIPLE_WORKER_RESULTS"
                                elif worker_event not in {"WORKER_FINISHED", "WORKER_FAILED"}:
                                    protocol_error = "UNKNOWN_WORKER_RESULT_EVENT"
                                else:
                                    worker_result = parsed
                        else:
                            if stream_name == "stdout" and isinstance(parsed, dict):
                                protocol_error = "UNAUTHENTICATED_JSON_STDOUT"
                            events.append(
                                {
                                    "event": "RAW_PROCESS_LINE",
                                    "line": line.rstrip("\r\n")[-4000:],
                                    "stream": stream_name,
                                }
                            )

                now = time.monotonic()
                elapsed = now - started
                if terminal_reason is None and elapsed >= timeout_seconds:
                    terminal_reason = "TIMEOUT"
                    events.append({"event": "HOST_TIMEOUT_REACHED", "elapsed_seconds": elapsed})
                if terminal_reason is not None and process.poll() is None:
                    supervisor.write_attempt_state(
                        attempt,
                        "TERMINATING",
                        {"container_name": container_name, "reason": terminal_reason},
                    )
                    cleanup_verified = _cleanup_container(repository_root, container_name)
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                    continue

                if now < next_poll or process.poll() is not None:
                    continue
                next_poll = now + poll_seconds
                inspected = _inspect_container(repository_root, container_name)
                if inspected is None:
                    events.append(
                        {"event": "CONTAINER_NOT_YET_INSPECTABLE", "elapsed_seconds": elapsed}
                    )
                    continue
                state = inspected["State"]
                host_config = inspected["HostConfig"]
                image = str(inspected["Image"])
                configured_memory = int(host_config.get("Memory") or 0)
                configured_swap = int(host_config.get("MemorySwap") or 0)
                configured_pids = int(host_config.get("PidsLimit") or 0)
                network_mode = str(host_config.get("NetworkMode") or "")
                restart_name = str(host_config.get("RestartPolicy", {}).get("Name") or "")
                repository_mounts = [
                    mount
                    for mount in inspected.get("Mounts", [])
                    if mount.get("Destination") == "/home/sage/work"
                ]
                repository_read_only = bool(
                    len(repository_mounts) == 1 and repository_mounts[0].get("RW") is False
                )
                memory: int | None = None
                stats: dict[str, int | float] | None = None
                audit: dict[str, Any] | None = None
                runtime_telemetry_status = "container_already_exited"
                if bool(state.get("Running")):
                    stats = _container_stats(repository_root, container_name)
                    if stats is not None:
                        memory = int(stats["memory_bytes"])
                        peak_memory = max(peak_memory, memory)
                        audit = _container_process_audit(repository_root, container_name)
                    if stats is None or audit is None:
                        transitioned = _inspect_container(repository_root, container_name)
                        if transitioned is None or bool(
                            transitioned.get("State", {}).get("Running")
                        ):
                            raise CampaignError(
                                "runtime telemetry reported a stopped container but a "
                                "follow-up inspect did not authenticate that transition"
                            )
                        inspected = transitioned
                        state = inspected["State"]
                        runtime_telemetry_status = "exited_between_runtime_probes"
                    else:
                        runtime_telemetry_status = "complete"
                events.append(
                    {
                        "event": "CONTAINER_HEALTH",
                        "container_image_digest": image,
                        "configured_memory_bytes": configured_memory,
                        "configured_memory_swap_bytes": configured_swap,
                        "configured_pids_limit": configured_pids,
                        "container_cpu_percent": (
                            None if stats is None else stats["container_cpu_percent"]
                        ),
                        "container_pids": None if stats is None else stats["container_pids"],
                        "elapsed_seconds": elapsed,
                        "memory_bytes": memory,
                        "network_mode": network_mode,
                        "oom_killed": bool(state.get("OOMKilled")),
                        "peak_memory_bytes": peak_memory,
                        "repository_mount_read_only": repository_read_only,
                        "restart_policy": restart_name,
                        "runtime_telemetry_status": runtime_telemetry_status,
                        "running": bool(state.get("Running")),
                        **(audit or {}),
                    }
                )
                _announce(
                    "CONTAINER_HEALTH",
                    host_elapsed_seconds=elapsed,
                    cpu_percent=None if stats is None else stats["container_cpu_percent"],
                    memory_bytes=memory,
                    peak_memory_bytes=peak_memory,
                    running=bool(state.get("Running")),
                )
                if image != expected_image_digest:
                    terminal_reason = "ERROR_CONTAINER_IMAGE_MISMATCH"
                elif (
                    configured_memory != hard_memory_bytes
                    or configured_swap != hard_memory_bytes
                    or configured_pids != 256
                    or network_mode != "none"
                    or not repository_read_only
                    or restart_name not in {"", "no"}
                ):
                    terminal_reason = "ERROR_CONTAINER_CONTRACT"
                elif bool(state.get("OOMKilled")):
                    terminal_reason = "OOM"
                elif memory is not None and memory >= soft_memory_bytes:
                    terminal_reason = "SOFT_RESOURCE_LIMIT"
                else:
                    container_contract_verified = True

            if process is not None:
                process.wait(timeout=10)
            final_state = _inspect_container(repository_root, container_name)
            if final_state is not None and bool(final_state["State"].get("OOMKilled")):
                terminal_reason = "OOM"
            if not container_contract_verified and final_state is not None:
                final_host = final_state["HostConfig"]
                final_mounts = [
                    mount
                    for mount in final_state.get("Mounts", [])
                    if mount.get("Destination") == "/home/sage/work"
                ]
                container_contract_verified = bool(
                    final_state.get("Image") == expected_image_digest
                    and int(final_host.get("Memory") or 0) == hard_memory_bytes
                    and int(final_host.get("MemorySwap") or 0) == hard_memory_bytes
                    and int(final_host.get("PidsLimit") or 0) == 256
                    and final_host.get("NetworkMode") == "none"
                    and final_host.get("RestartPolicy", {}).get("Name") in {"", "no"}
                    and len(final_mounts) == 1
                    and final_mounts[0].get("RW") is False
                )
            if terminal_reason is None and not container_contract_verified:
                terminal_reason = "ERROR_CONTAINER_CONTRACT_UNVERIFIED"
            cleanup_verified = _cleanup_container(repository_root, container_name)
            if not cleanup_verified:
                terminal_reason = "KILL_UNVERIFIED"
            postflight_stale = _stale_solver_containers(repository_root)
            postflight_legacy = _legacy_worker_processes(repository_root)
            postflight_audit_verified = True
            events.append(
                {
                    "event": "POSTFLIGHT_SURVIVOR_AUDIT",
                    "legacy_processes": postflight_legacy,
                    "stale_containers": postflight_stale,
                    "verified_zero_survivors": not postflight_stale and not postflight_legacy,
                }
            )
            if postflight_stale or postflight_legacy:
                cleanup_verified = False
                terminal_reason = "KILL_UNVERIFIED"
            events.append(
                {
                    "event": "WORKER_PROTOCOL_EVALUATED",
                    "protocol_error": protocol_error,
                    "request_verified_count": request_verified_count,
                    "worker_message_count": worker_message_count,
                    "worker_result_count": worker_result_count,
                }
            )
            if terminal_reason is not None:
                status = terminal_reason
            elif protocol_error is not None:
                status = "ERROR_WORKER_PROTOCOL"
            elif worker_result is None:
                status = "EMPTY_BACKEND_RESPONSE"
            else:
                status = str(worker_result.get("status", "NON_JSON_BACKEND_RESPONSE"))
                expected_returncode = supervisor.exit_code_for_status(status)
                if process is None or process.returncode != expected_returncode:
                    status = "ERROR_WORKER_EXIT_STATUS_MISMATCH"
        except KeyboardInterrupt:
            terminal_reason = "HOST_INTERRUPTED"
            cleanup_verified = _cleanup_container(repository_root, container_name)
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            events.append(
                {
                    "event": "HOST_INTERRUPTED",
                    "cleanup_verified": cleanup_verified,
                }
            )
            status = "HOST_INTERRUPTED" if cleanup_verified else "KILL_UNVERIFIED"
        except Exception as error:  # noqa: BLE001 - cleanup must run for all host failures
            cleanup_verified = _cleanup_container(repository_root, container_name)
            events.append(
                {
                    "event": "SUPERVISOR_EXCEPTION",
                    "cleanup_verified": cleanup_verified,
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                }
            )
            status = "ERROR_SUPERVISOR_EXCEPTION" if cleanup_verified else "KILL_UNVERIFIED"
        finally:
            host_process_termination_verified = _terminate_host_process(process)
            events.append(
                {
                    "event": "HOST_PROCESS_TERMINATION_AUDIT",
                    "process_returncode": None if process is None else process.returncode,
                    "verified_not_running": host_process_termination_verified,
                }
            )
            if not host_process_termination_verified:
                cleanup_verified = False
                status = "KILL_UNVERIFIED"
            if not postflight_audit_verified:
                try:
                    postflight_stale = _stale_solver_containers(repository_root)
                    postflight_legacy = _legacy_worker_processes(repository_root)
                    postflight_audit_verified = True
                    events.append(
                        {
                            "event": "POSTFLIGHT_SURVIVOR_AUDIT",
                            "legacy_processes": postflight_legacy,
                            "stale_containers": postflight_stale,
                            "verified_zero_survivors": (
                                not postflight_stale and not postflight_legacy
                            ),
                        }
                    )
                    if postflight_stale or postflight_legacy:
                        cleanup_verified = False
                        status = "KILL_UNVERIFIED"
                except Exception as audit_error:  # noqa: BLE001 - failed audit is unsafe
                    cleanup_verified = False
                    status = "KILL_UNVERIFIED"
                    events.append(
                        {
                            "error_message": str(audit_error),
                            "error_type": type(audit_error).__name__,
                            "event": "POSTFLIGHT_SURVIVOR_AUDIT_FAILED",
                            "verified_zero_survivors": False,
                        }
                    )
            events.append(
                {
                    "cleanup_verified": cleanup_verified,
                    "container_contract_verified": container_contract_verified,
                    "event": "CONTAINER_ATTEMPT_FINISHED",
                    "host_process_termination_verified": host_process_termination_verified,
                    "postflight_audit_verified": postflight_audit_verified,
                    "process_returncode": None if process is None else process.returncode,
                    "status": status,
                }
            )
            stdout_log.close()
            stderr_log.close()
    return ContainerOutcome(
        status=status,
        wall_time_seconds=time.monotonic() - started,
        worker_result=worker_result,
        process_returncode=None if process is None else process.returncode,
        peak_memory_bytes=peak_memory,
        cleanup_verified=cleanup_verified,
        container_contract_verified=container_contract_verified,
        final_container_state=final_state,
        host_process_termination_verified=host_process_termination_verified,
        postflight_audit_verified=postflight_audit_verified,
        postflight_legacy_processes=postflight_legacy,
        postflight_stale_containers=postflight_stale,
    )


def _run_campaign_locked(
    repository_root: Path,
    *,
    campaign_started: float,
    chart: str,
    modulus: int,
    method: str,
    stage_size: int,
    timeout_seconds: int,
    poll_seconds: float,
    monomial_order: str,
    groebner_algorithm: str,
    factor_group_order: Sequence[str],
    incremental_batch_sizes: Sequence[int],
) -> int:
    repository_root = repository_root.resolve()
    budget = _load_budget(repository_root)
    if (
        type(timeout_seconds) is not int
        or not 0 < timeout_seconds <= budget.timeout_seconds_per_chart
    ):
        raise CampaignError("pilot timeout must be positive and within the committed chart budget")
    if type(stage_size) is not int or stage_size <= 0:
        raise CampaignError("stage size must be a positive integer")
    if poll_seconds <= 0 or poll_seconds > 60:
        raise CampaignError("poll interval must be in (0, 60] seconds")

    frozen_root = _read_json_object(repository_root / bundle.ROOT_RESULT_PATH)
    metadata = build_verified_arena_metadata_cache(
        repository_root, frozen_root, progress_started=campaign_started
    )
    metadata_path = (
        repository_root
        / METADATA_DIRECTORY
        / f"polynomial_arena.{frozen_root['semantic_digest_sha256']}.json"
    )
    if metadata_path.exists():
        if _read_json_object(metadata_path) != metadata:
            raise CampaignError("persisted arena metadata cache disagrees with a fresh chunk scan")
    else:
        supervisor.atomic_write_json(metadata_path, metadata)

    plan = stage_plan.build_stage_plan(
        frozen_root,
        chart,
        metadata,
        stage_sizes=(stage_size,),
    )
    stage = plan["stages"][0]
    request = build_stage_request(
        repository_root,
        frozen_root=frozen_root,
        plan=plan,
        stage=stage,
        budget=budget,
        chart=chart,
        modulus=modulus,
        method=method,
        monomial_order=monomial_order,
        groebner_algorithm=groebner_algorithm,
        factor_group_order=factor_group_order,
        incremental_batch_sizes=incremental_batch_sizes,
    )
    envelope = supervisor.create_recipe_envelope(request)
    verified_envelope = supervisor.verify_recipe_envelope(envelope)
    worker_source_digest = str(request["expected_worker_source_sha256"])

    preflight_process_audit(repository_root)
    image_digest = _image_digest(repository_root)
    source_snapshot = _source_snapshot(repository_root)
    source_bindings = {
        path: record["sha256"] for path, record in source_snapshot["records"].items()
    }
    worker_source_path = Path(worker.__file__).resolve().relative_to(repository_root).as_posix()
    if source_bindings.get(worker_source_path) != worker_source_digest:
        raise CampaignError("worker source changed while the immutable request was being built")
    execution_policy = {
        "factor_group_order": list(factor_group_order),
        "incremental_batch_sizes": list(incremental_batch_sizes),
        "method": method,
        "requested_timeout_seconds": timeout_seconds,
        "runtime_binding_schema": "sr2v-runtime-binding-v1",
        "single_worker": True,
        "source_bindings": source_bindings,
        "stage_size": stage_size,
    }
    fingerprint = supervisor.create_attempt_fingerprint(
        chart=chart,
        coefficient_modulus=modulus,
        recipe_payload_digest_sha256=verified_envelope.payload_digest_sha256,
        budget_payload_digest_sha256=budget.payload_sha256,
        worker_source_sha256=worker_source_digest,
        container_image_digest=image_digest,
        monomial_order=monomial_order,
        execution_policy=execution_policy,
    )
    attempts_root = repository_root / ATTEMPTS_DIRECTORY
    permission = supervisor.evaluate_attempt_permission(
        attempts_root,
        budget=budget,
        current_campaign_elapsed_seconds=time.monotonic() - campaign_started,
        finalization_reserve_seconds=FINALIZATION_RESERVE_SECONDS,
        fingerprint_sha256=fingerprint.sha256,
    )
    if not permission.allowed or permission.effective_timeout_seconds is None:
        _announce(
            "ATTEMPT_FORBIDDEN",
            aggregate_wall_time_seconds=permission.aggregate_wall_time_seconds,
            reason=permission.reason,
            remaining_wall_time_seconds=permission.remaining_wall_time_seconds,
        )
        return 2
    effective_timeout = min(timeout_seconds, permission.effective_timeout_seconds)
    attempt = supervisor.create_attempt_directory(attempts_root, fingerprint)
    container_name = (
        f"{CONTAINER_PREFIX}{chart.lower()}-{fingerprint.sha256[:12]}-"
        f"{attempt.attempt_id.rsplit('-', 1)[-1][:8]}"
    )
    phase = "ARTIFACT_WRITE"
    launch_may_have_occurred = False
    outcome: ContainerOutcome | None = None
    try:
        supervisor.atomic_write_json(attempt.path / "request.json", envelope)
        supervisor.atomic_write_json(attempt.path / "stage_plan.json", plan)
        supervisor.atomic_write_json(attempt.path / "arena_metadata.json", metadata)
        supervisor.atomic_write_json(attempt.path / "source_snapshot.json", source_snapshot)
        request_relative = (attempt.path / "request.json").relative_to(repository_root).as_posix()
        container_request = f"/home/sage/work/{request_relative}"
        _announce(
            "ATTEMPT_CREATED",
            attempt_path=str(attempt.path),
            container_name=container_name,
            effective_timeout_seconds=effective_timeout,
            fingerprint_sha256=fingerprint.sha256,
            selected_entry_indices=request["selected_entry_indices"],
            selected_generator_rows_sha256=request["selected_generator_rows_sha256"],
        )

        phase = "EXECUTE"
        launch_may_have_occurred = True
        outcome = execute_container_attempt(
            repository_root,
            attempt=attempt,
            request_container_path=container_request,
            container_name=container_name,
            expected_image_digest=image_digest,
            expected_request_payload_sha256=verified_envelope.payload_digest_sha256,
            hard_memory_bytes=budget.memory_limit_bytes,
            soft_memory_bytes=SOFT_RSS_GIB * 1024**3,
            timeout_seconds=effective_timeout,
            poll_seconds=poll_seconds,
        )
        phase = "POSTPROCESS"
        postflight_legacy = outcome.postflight_legacy_processes
        postflight_stale = outcome.postflight_stale_containers
        if (
            not outcome.postflight_audit_verified
            or postflight_legacy
            or postflight_stale
            or not outcome.cleanup_verified
        ):
            outcome.status = "KILL_UNVERIFIED"
            outcome.cleanup_verified = False
        total_wall = time.monotonic() - campaign_started
        event_summary = supervisor.verify_hash_chain_jsonl(attempt.events_path)
        details = {
            "cleanup_verified": outcome.cleanup_verified,
            "coefficient_scope": "EXACT_QQ" if modulus == 0 else "FINITE_FIELD_SCOUT_ONLY",
            "container_contract_verified": outcome.container_contract_verified,
            "container_image_digest": image_digest,
            "event_log_head_sha256": event_summary.head_sha256,
            "event_log_record_count": event_summary.record_count,
            "event_log_valid": True,
            "host_process_termination_verified": outcome.host_process_termination_verified,
            "peak_memory_bytes": outcome.peak_memory_bytes,
            "planning_and_execution_wall_time_seconds": total_wall,
            "postflight_audit_verified": outcome.postflight_audit_verified,
            "postflight_legacy_processes": postflight_legacy,
            "postflight_stale_containers": postflight_stale,
            "process_returncode": outcome.process_returncode,
            "request_payload_sha256": verified_envelope.payload_digest_sha256,
            "terminal_attempt_status": outcome.status,
            "terminal_cleanup_verified": outcome.cleanup_verified,
            "terminal_process_returncode": outcome.process_returncode,
            "worker_result": outcome.worker_result,
            "worker_source_sha256": worker_source_digest,
        }
        phase = "FINALIZE"
        supervisor.record_attempt_result(
            attempt,
            status=outcome.status,
            wall_time_seconds=total_wall,
            details=details,
        )
        supervisor.write_attempt_state(
            attempt,
            "FINISHED",
            {"cleanup_verified": outcome.cleanup_verified, "status": outcome.status},
        )
        _announce(
            "ATTEMPT_RECORDED",
            attempt_path=str(attempt.path),
            peak_memory_bytes=outcome.peak_memory_bytes,
            status=outcome.status,
            total_wall_time_seconds=total_wall,
        )
        return supervisor.exit_code_for_status(outcome.status)
    except (Exception, KeyboardInterrupt) as error:  # record every published attempt
        if attempt.result_path.is_file():
            recorded = supervisor.read_json_object(attempt.result_path)
            recorded_exit = recorded.get("recommended_exit_code")
            return recorded_exit if type(recorded_exit) is int else 3

        cleanup_verified = True
        if launch_may_have_occurred:
            try:
                cleanup_verified = _cleanup_container(repository_root, container_name)
            except (Exception, KeyboardInterrupt):  # finalizer must fail closed
                cleanup_verified = False
        postflight_audit_verified = False
        emergency_postflight_legacy: list[str] = []
        emergency_postflight_stale: list[str] = []
        try:
            emergency_postflight_stale = _stale_solver_containers(repository_root)
            emergency_postflight_legacy = _legacy_worker_processes(repository_root)
            postflight_audit_verified = True
        except (Exception, KeyboardInterrupt):  # inability to audit is itself unsafe
            cleanup_verified = False
        if emergency_postflight_stale or emergency_postflight_legacy:
            cleanup_verified = False
        emergency_host_process_verified = (
            not launch_may_have_occurred
            if outcome is None
            else outcome.host_process_termination_verified
        )
        if not emergency_host_process_verified:
            cleanup_verified = False

        event_log_valid = False
        event_log_head: str | None = None
        event_log_count: int | None = None
        if attempt.events_path.is_file():
            try:
                emergency_event_summary = supervisor.verify_hash_chain_jsonl(attempt.events_path)
                event_log_valid = True
                event_log_head = emergency_event_summary.head_sha256
                event_log_count = emergency_event_summary.record_count
            except (Exception, KeyboardInterrupt):  # invalid/unreadable logs stay untrusted
                pass

        if not cleanup_verified or not postflight_audit_verified:
            failure_status = "KILL_UNVERIFIED"
        elif isinstance(error, KeyboardInterrupt):
            failure_status = "HOST_INTERRUPTED"
        else:
            failure_status = f"ERROR_CAMPAIGN_{phase}"
        total_wall = time.monotonic() - campaign_started
        failure_details = {
            "cleanup_verified": cleanup_verified,
            "coefficient_scope": "EXACT_QQ" if modulus == 0 else "FINITE_FIELD_SCOUT_ONLY",
            "container_contract_verified": (
                False if outcome is None else outcome.container_contract_verified
            ),
            "container_image_digest": image_digest,
            "error_message": str(error),
            "error_type": type(error).__name__,
            "event_log_head_sha256": event_log_head,
            "event_log_record_count": event_log_count,
            "event_log_valid": event_log_valid,
            "failure_phase": phase,
            "host_process_termination_verified": emergency_host_process_verified,
            "launch_may_have_occurred": launch_may_have_occurred,
            "peak_memory_bytes": 0 if outcome is None else outcome.peak_memory_bytes,
            "planning_and_execution_wall_time_seconds": total_wall,
            "postflight_audit_verified": postflight_audit_verified,
            "postflight_legacy_processes": emergency_postflight_legacy,
            "postflight_stale_containers": emergency_postflight_stale,
            "process_returncode": None if outcome is None else outcome.process_returncode,
            "request_payload_sha256": verified_envelope.payload_digest_sha256,
            "terminal_attempt_status": None if outcome is None else outcome.status,
            "terminal_cleanup_verified": None if outcome is None else outcome.cleanup_verified,
            "terminal_process_returncode": (
                None if outcome is None else outcome.process_returncode
            ),
            "worker_result": None if outcome is None else outcome.worker_result,
            "worker_source_sha256": worker_source_digest,
        }
        supervisor.record_attempt_result(
            attempt,
            status=failure_status,
            wall_time_seconds=total_wall,
            details=failure_details,
        )
        supervisor.write_attempt_state(
            attempt,
            "FINISHED",
            {"cleanup_verified": cleanup_verified, "status": failure_status},
        )
        try:
            _announce(
                "ATTEMPT_RECORDED_AFTER_FAILURE",
                attempt_path=str(attempt.path),
                error_type=type(error).__name__,
                status=failure_status,
                total_wall_time_seconds=total_wall,
            )
        except OSError:
            pass
        return supervisor.exit_code_for_status(failure_status)


def run_campaign(
    repository_root: Path,
    *,
    chart: str,
    modulus: int,
    method: str,
    stage_size: int,
    timeout_seconds: int,
    poll_seconds: float,
    monomial_order: str,
    groebner_algorithm: str,
    factor_group_order: Sequence[str],
    incremental_batch_sizes: Sequence[int],
) -> int:
    campaign_started = time.monotonic()
    repository_root = repository_root.resolve()
    lock_path = repository_root / SUPERVISED_DIRECTORY / "campaign.lock"
    with CampaignFileLock(lock_path):
        return _run_campaign_locked(
            repository_root,
            campaign_started=campaign_started,
            chart=chart,
            modulus=modulus,
            method=method,
            stage_size=stage_size,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
            monomial_order=monomial_order,
            groebner_algorithm=groebner_algorithm,
            factor_group_order=factor_group_order,
            incremental_batch_sizes=incremental_batch_sizes,
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--chart", choices=sorted(worker.NON_ALIGNED_CHARTS), default="U2")
    parser.add_argument("--modulus", type=int, default=32003)
    parser.add_argument("--method", choices=sorted(worker.METHODS), default="build_only")
    parser.add_argument("--stage-size", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_PILOT_TIMEOUT_SECONDS)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument(
        "--monomial-order",
        choices=sorted(worker.MONOMIAL_ORDERS),
        default="degrevlex",
    )
    parser.add_argument(
        "--groebner-algorithm",
        choices=sorted(worker.GROEBNER_ALGORITHMS),
        default="libsingular:slimgb",
    )
    parser.add_argument(
        "--factor-group-order",
        nargs=3,
        default=["chart", "bottom", "torus"],
        metavar=("FIRST", "SECOND", "THIRD"),
    )
    parser.add_argument(
        "--incremental-batch-sizes",
        nargs="+",
        type=int,
        help=(
            "strictly increasing generator-prefix sizes; required to end at --stage-size "
            "and used only by incremental_native_saturation"
        ),
    )
    arguments = parser.parse_args(argv)
    if arguments.incremental_batch_sizes is not None:
        incremental_batch_sizes = arguments.incremental_batch_sizes
    elif arguments.method == "incremental_native_saturation" and arguments.stage_size > 6:
        incremental_batch_sizes = [6, arguments.stage_size]
    else:
        incremental_batch_sizes = [arguments.stage_size]
    try:
        return run_campaign(
            arguments.root,
            chart=arguments.chart,
            modulus=arguments.modulus,
            method=arguments.method,
            stage_size=arguments.stage_size,
            timeout_seconds=arguments.timeout_seconds,
            poll_seconds=arguments.poll_seconds,
            monomial_order=arguments.monomial_order,
            groebner_algorithm=arguments.groebner_algorithm,
            factor_group_order=arguments.factor_group_order,
            incremental_batch_sizes=incremental_batch_sizes,
        )
    except Exception as error:  # noqa: BLE001 - CLI must expose a nonzero operational failure
        _announce(
            "CAMPAIGN_FAILED_BEFORE_RESULT",
            error_message=str(error),
            error_type=type(error).__name__,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
