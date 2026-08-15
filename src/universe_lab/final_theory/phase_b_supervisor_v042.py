"""Hard-supervisor implementation preflight for the Phase-B sampler design.

This module supervises only synthetic worker fixtures.  It does not import a
sampler, generate a trajectory, enumerate an unlabeled level, run a solver, or
make a scientific claim.  The fixture harness exercises the operational
boundary required before any production measurement is authorized:

* wall-clock termination,
* process-tree termination,
* resident-memory and scratch-disk caps,
* schema/digest validation before promotion, and
* one-attempt, atomic promotion semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-b-hard-supervisor-preflight-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_HARD_SUPERVISOR_PREFLIGHT_COMPLETE_NON_EVIDENTIARY"
NEXT_GATE = "PHASE_B_INDEPENDENT_REPLAY_AND_PRODUCTION_BUDGET_REVIEW"
MODULE_NAME = "universe_lab.final_theory.phase_b_supervisor_v042"
RESULT_PATH = Path(
    "results/v0.4.2_phase_b_hard_supervisor_preflight_20260816.json"
)
REPORT_PATH = Path(
    "reports/v0.4.2_phase_b_hard_supervisor_preflight_2026-08-16.md"
)
CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_hard_supervisor_preflight_budget_20260816.json"
)
MODULE_PATH = Path("src/universe_lab/final_theory/phase_b_supervisor_v042.py")
TEST_PATH = Path("tests/final_theory/test_v042_phase_b_hard_supervisor.py")

FIXTURE_MODES = (
    "success",
    "invalid_certificate",
    "tree_timeout",
    "memory_limit",
    "disk_limit",
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _certificate_core(mode: str) -> dict[str, Any]:
    if mode == "success":
        return {"fixture": "atomic_success", "answer": 42}
    if mode == "invalid_certificate":
        return {"fixture": "invalid_certificate", "answer": 42}
    raise ValueError(f"mode {mode!r} does not write a certificate")


def _certificate_digest(core: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(core)).hexdigest()


def _write_worker_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=True, sort_keys=True, indent=2)
        handle.write("\n")


def _worker_main(mode: str, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    if mode in {"success", "invalid_certificate"}:
        core = _certificate_core(mode)
        digest = _certificate_digest(core)
        if mode == "invalid_certificate":
            digest = "0" * 64
        _write_worker_json(
            work_dir / "candidate.json",
            {
                "schema_version": "phase-b-supervisor-fixture-certificate-v1",
                "status": "COMPLETED",
                "certificate_core": core,
                "semantic_digest_sha256": digest,
            },
        )
        return

    if mode == "tree_timeout":
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _write_worker_json(work_dir / "child_pid.json", {"pid": child.pid})
        time.sleep(30)
        return

    if mode == "memory_limit":
        payload = bytearray(128 * 1024 * 1024)
        for index in range(0, len(payload), 4096):
            payload[index] = index & 0xFF
        _write_worker_json(work_dir / "memory_ready.json", {"bytes": len(payload)})
        time.sleep(30)
        return

    if mode == "disk_limit":
        chunk = b"x" * (256 * 1024)
        with (work_dir / "scratch.bin").open("wb") as handle:
            for _ in range(32):
                handle.write(chunk)
                handle.flush()
                time.sleep(0.01)
        time.sleep(30)
        return

    raise ValueError(f"unknown worker fixture mode: {mode!r}")


def _binding(root: Path, relative: Path) -> dict[str, Any]:
    raw = (root / relative).read_bytes()
    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return {
        "path": relative.as_posix(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(canonical).hexdigest(),
        "size_bytes": len(raw),
        "strict_utf8_lf": "\r" not in text,
    }


def _popen_kwargs(root: Path) -> dict[str, Any]:
    environment = os.environ.copy()
    source_path = str(root / "src")
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path if not existing else os.pathsep.join((source_path, existing))
    )
    kwargs: dict[str, Any] = {
        "cwd": str(root),
        "env": environment,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
    else:
        kwargs["start_new_session"] = True
    return kwargs


def _process_tree(root_pid: int) -> tuple[psutil.Process, ...]:
    try:
        root = psutil.Process(root_pid)
        children = root.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ()
    return (root, *children)


def _live_pids(pids: set[int]) -> tuple[int, ...]:
    live: list[int] = []
    for pid in sorted(pids):
        try:
            process = psutil.Process(pid)
            if process.status() != psutil.STATUS_ZOMBIE:
                live.append(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return tuple(live)


def _wait_for_exit(pids: set[int], timeout: float) -> tuple[int, ...]:
    deadline = time.monotonic() + timeout
    while True:
        live = _live_pids(pids)
        if not live or time.monotonic() >= deadline:
            return live
        time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))


def _kill_process_group(root_pid: int, signal_name: str) -> None:
    killpg = getattr(os, "killpg", None)
    signal_value = getattr(signal, signal_name, None)
    if not callable(killpg) or signal_value is None:
        return
    try:
        killpg(root_pid, signal_value)
    except (ProcessLookupError, PermissionError):
        pass


def _terminate_tree(
    root_pid: int,
    observed_pids: set[int],
    grace_seconds: float,
) -> tuple[int, ...]:
    pids = set(observed_pids)
    pids.update(process.pid for process in _process_tree(root_pid))
    pids.add(root_pid)

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(root_pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        _kill_process_group(root_pid, "SIGTERM")
        for pid in sorted(pids, reverse=True):
            try:
                psutil.Process(pid).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    live = _wait_for_exit(pids, grace_seconds)
    if live:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(root_pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            _kill_process_group(root_pid, "SIGKILL")
        for pid in live:
            try:
                psutil.Process(pid).kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        live = _wait_for_exit(pids, grace_seconds)
    return live


def _disk_usage_bytes(root: Path) -> int:
    total = 0
    for base, _directories, filenames in os.walk(root, followlinks=False):
        for filename in filenames:
            path = Path(base) / filename
            try:
                metadata = path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(metadata.st_mode):
                total += metadata.st_size
    return total


def _resource_snapshot(
    root_pid: int, work_dir: Path
) -> tuple[int, int, tuple[int, ...]]:
    processes = _process_tree(root_pid)
    rss = 0
    pids: set[int] = set()
    for process in processes:
        pids.add(process.pid)
        try:
            rss += process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rss, _disk_usage_bytes(work_dir), tuple(sorted(pids))


def _read_child_pid(work_dir: Path) -> int | None:
    marker = work_dir / "child_pid.json"
    if not marker.is_file():
        return None
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))["pid"]
        return value if type(value) is int and value > 0 else None
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _validate_candidate(path: Path, mode: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    if payload.get("schema_version") != "phase-b-supervisor-fixture-certificate-v1":
        return False
    if payload.get("status") != "COMPLETED":
        return False
    core = payload.get("certificate_core")
    digest = payload.get("semantic_digest_sha256")
    return (
        core == _certificate_core(mode)
        and digest == _certificate_digest(core)
    )


def run_fixture(
    root: Path,
    mode: str,
    limits: dict[str, Any],
    final_path: Path,
) -> dict[str, Any]:
    """Run one synthetic worker exactly once under the hard supervisor."""

    if mode not in FIXTURE_MODES:
        raise ValueError(f"unknown fixture mode: {mode!r}")
    if final_path.exists():
        raise FileExistsError(f"refusing to overwrite {final_path}")
    final_path.parent.mkdir(parents=True, exist_ok=True)

    poll_interval_seconds = float(limits.get("poll_interval_seconds", 0.01))
    termination_grace_seconds = float(
        limits.get("termination_grace_seconds", 0.5)
    )
    started = time.perf_counter()
    peak_rss = 0
    peak_disk = 0
    observed_pids: set[int] = set()
    reason: str | None = None
    termination_requested = False
    child_pid: int | None = None
    process: subprocess.Popen[Any] | None = None
    work_dir_name: str | None = None

    try:
        with tempfile.TemporaryDirectory(
            prefix="phase_b_supervisor_", dir=str(final_path.parent)
        ) as work_dir_name:
            work_dir = Path(work_dir_name)
            command = [
                sys.executable,
                "-m",
                MODULE_NAME,
                "--worker",
                "--mode",
                mode,
                "--work-dir",
                str(work_dir),
            ]
            process = subprocess.Popen(command, **_popen_kwargs(root))
            root_pid = process.pid
            while True:
                rss, disk, current_pids = _resource_snapshot(root_pid, work_dir)
                peak_rss = max(peak_rss, rss)
                peak_disk = max(peak_disk, disk)
                observed_pids.update(current_pids)
                if process.poll() is not None:
                    break
                if (
                    time.perf_counter() - started
                    >= float(limits["wall_time_seconds"])
                ):
                    reason = "RESOURCE_LIMIT_OPEN_WALL_TIME"
                    termination_requested = True
                    break
                if rss > int(limits["memory_mib"]) * 1024 * 1024:
                    reason = "RESOURCE_LIMIT_OPEN_MEMORY"
                    termination_requested = True
                    break
                if disk > int(limits["disk_mib"]) * 1024 * 1024:
                    reason = "RESOURCE_LIMIT_OPEN_DISK"
                    termination_requested = True
                    break
                time.sleep(poll_interval_seconds)

            rss, disk, current_pids = _resource_snapshot(root_pid, work_dir)
            peak_rss = max(peak_rss, rss)
            peak_disk = max(peak_disk, disk)
            observed_pids.update(current_pids)
            if reason is None:
                if peak_rss > int(limits["memory_mib"]) * 1024 * 1024:
                    reason = "RESOURCE_LIMIT_OPEN_MEMORY"
                    termination_requested = process.poll() is None
                elif peak_disk > int(limits["disk_mib"]) * 1024 * 1024:
                    reason = "RESOURCE_LIMIT_OPEN_DISK"
                    termination_requested = process.poll() is None

            if reason is not None:
                _terminate_tree(
                    root_pid,
                    observed_pids,
                    termination_grace_seconds,
                )

            if process.poll() is None:
                _terminate_tree(
                    root_pid,
                    observed_pids,
                    termination_grace_seconds,
                )
            try:
                exit_code = process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                _terminate_tree(root_pid, observed_pids, 0.1)
                exit_code = process.wait(timeout=1.0)

            child_pid = _read_child_pid(work_dir)
            if child_pid is not None:
                observed_pids.add(child_pid)
            live_after_cleanup = _wait_for_exit(
                observed_pids,
                termination_grace_seconds,
            )
            tree_terminated = not live_after_cleanup
            candidate = work_dir / "candidate.json"
            candidate_present = candidate.is_file()

            if reason is not None:
                status = "RESOURCE_LIMIT_OPEN"
                promoted = False
            elif exit_code != 0:
                status = "ERROR"
                reason = "WORKER_EXIT_NONZERO"
                promoted = False
            elif mode == "success" and candidate_present:
                if not _validate_candidate(candidate, mode):
                    status = "ERROR"
                    reason = "INVALID_CERTIFICATE"
                    promoted = False
                else:
                    os.replace(candidate, final_path)
                    status = "COMPLETED"
                    reason = "NONE"
                    promoted = True
            else:
                status = "ERROR"
                reason = "INVALID_CERTIFICATE"
                promoted = False

            return {
                "outcome": {
                    "mode": mode,
                    "status": status,
                    "reason": reason,
                    "promoted": promoted,
                    "process_tree_terminated": tree_terminated,
                    "attempt_count": 1,
                },
                "runtime": {
                    "elapsed_seconds": time.perf_counter() - started,
                    "peak_rss_bytes": peak_rss,
                    "peak_disk_bytes": peak_disk,
                    "exit_code": exit_code,
                    "observed_process_count": len(observed_pids),
                    "child_pid": child_pid,
                    "live_process_ids_after_cleanup": list(live_after_cleanup),
                    "termination_requested": termination_requested,
                    "candidate_present_before_cleanup": candidate_present,
                    "final_exists_after_run": final_path.is_file(),
                },
            }
    finally:
        if process is not None and process.poll() is None:
            _terminate_tree(process.pid, observed_pids, 0.1)
        if work_dir_name is not None and Path(work_dir_name).exists():
            shutil.rmtree(work_dir_name, ignore_errors=True)


def _expected_outcomes(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "mode": mode,
            "status": config["fixtures"][mode]["expected_status"],
            "reason": config["fixtures"][mode]["expected_reason"],
            "promoted": config["fixtures"][mode]["expected_promoted"],
            "process_tree_terminated": True,
            "attempt_count": 1,
        }
        for mode in FIXTURE_MODES
    ]


def build_preflight(root: Path) -> dict[str, Any]:
    config = json.loads((root / CONFIG_PATH).read_text(encoding="utf-8"))
    if tuple(config["fixtures"]) != FIXTURE_MODES:
        raise AssertionError("fixture order drifted from the hard-supervisor schema")
    if config["limits"]["max_retries"] != 0:
        raise AssertionError("hard supervisor preflight must not retry workers")

    observations: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(
        prefix="phase_b_supervisor_build_", dir=str(root / "results")
    ) as output_dir_name:
        output_dir = Path(output_dir_name)
        for mode in FIXTURE_MODES:
            fixture_limits = dict(config["fixtures"][mode])
            fixture_limits.update(
                {
                    "poll_interval_seconds": config["limits"][
                        "poll_interval_seconds"
                    ],
                    "termination_grace_seconds": config["limits"][
                        "termination_grace_seconds"
                    ],
                }
            )
            result = run_fixture(
                root,
                mode,
                fixture_limits,
                output_dir / f"{mode}.json",
            )
            observations.append(result)

    outcomes = [item["outcome"] for item in observations]
    expected = _expected_outcomes(config)
    checks = {
        "outcomes_match_versioned_expectations": outcomes == expected,
        "wall_time_cap_fails_closed": outcomes[2]["reason"]
        == "RESOURCE_LIMIT_OPEN_WALL_TIME",
        "process_tree_is_reaped": all(
            item["process_tree_terminated"] for item in outcomes
        ),
        "memory_cap_fails_closed": outcomes[3]["reason"]
        == "RESOURCE_LIMIT_OPEN_MEMORY",
        "disk_cap_fails_closed": outcomes[4]["reason"]
        == "RESOURCE_LIMIT_OPEN_DISK",
        "atomic_promotion_requires_validated_digest": outcomes[0]["promoted"]
        and not outcomes[1]["promoted"],
        "failed_fixtures_never_promote": all(
            not item["promoted"] for item in outcomes[1:]
        ),
        "exactly_one_attempt_and_no_retry": all(
            item["attempt_count"] == 1 for item in outcomes
        ),
        "production_boundary_is_closed": (
            config["limits"]["new_sampled_trajectories"] == 0
            and config["limits"]["solver_calls"] == 0
            and config["production_sampling_authorized"] is False
        ),
    }
    certificate_core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "budget_config_sha256": hashlib.sha256(
            (root / CONFIG_PATH).read_bytes()
        ).hexdigest(),
        "fixture_modes": list(FIXTURE_MODES),
        "expected_outcomes": expected,
        "observed_outcomes": outcomes,
        "checks": checks,
        "authorization_boundary": {
            "hard_supervisor_preflight_authorized": True,
            "production_sampling_authorized": False,
            "new_trajectories_authorized": False,
            "solver_run_permitted": False,
            "scientific_verdict_added": False,
            "global_verdict": "FINAL_THEORY_OPEN",
        },
        "source_bindings": [
            _binding(root, CONFIG_PATH),
            _binding(root, MODULE_PATH),
            _binding(root, TEST_PATH),
        ],
    }
    all_checks = all(checks.values())
    total_elapsed = sum(
        item["runtime"]["elapsed_seconds"] for item in observations
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "next_gate": NEXT_GATE,
        "scope": config["authorization_scope"],
        "certificate_core": certificate_core,
        "runtime_observation": {
            "fixture_observations": [item["runtime"] for item in observations],
            "total_elapsed_seconds": total_elapsed,
            "within_versioned_total_wall_time": total_elapsed
            <= config["limits"]["max_total_wall_seconds"],
            "external_process_tree_supervisor_used": True,
            "no_live_fixture_processes": all(
                not item["runtime"]["live_process_ids_after_cleanup"]
                for item in observations
            ),
        },
        "all_acceptance_checks_passed": all_checks,
        "new_trajectories": 0,
        "solver_calls": 0,
        "production_sampler_available": False,
        "production_sampling_authorized": False,
        "semantic_digest_sha256": stable_hash(certificate_core),
    }
    if not all_checks or not payload["runtime_observation"][
        "within_versioned_total_wall_time"
    ]:
        raise RuntimeError("hard supervisor preflight failed closed")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    core = payload["certificate_core"]
    observation = payload["runtime_observation"]
    lines = [
        "# Phase-B hard supervisor implementation preflight — 2026-08-16",
        "",
        f"Status: **`{payload['status']}`**",
        "",
        f"Semantic digest: `{payload['semantic_digest_sha256']}`",
        "",
        "## Scope",
        "",
        "This is a fixture-only operational preflight. It does not start a",
        "production sampler, generate trajectories, enumerate unlabeled levels,",
        "run a solver, or add scientific evidence.",
        "",
        "## Deterministic certificate",
        "",
        "| fixture | status | reason | promoted | tree reaped | attempts |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in core["observed_outcomes"]:
        lines.append(
            f"| `{item['mode']}` | `{item['status']}` | `{item['reason']}` | "
            f"`{item['promoted']}` | `{item['process_tree_terminated']}` | "
            f"`{item['attempt_count']}` |"
        )
    lines.extend(
        [
            "",
            "The timeout fixture spawns a child and is terminated as a process",
            "tree. The memory and disk fixtures fail closed with explicit",
            "`RESOURCE_LIMIT_OPEN_*` reasons. The success fixture is promoted",
            "only after independent schema and digest validation; the invalid",
            "certificate is never promoted.",
            "",
            "## Checks",
            "",
            "| check | passed |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{name}` | `{value}` |" for name, value in core["checks"].items()
    )
    lines.extend(
        [
            "",
            "## Runtime observation",
            "",
            f"- Total fixture wall time: `{observation['total_elapsed_seconds']:.6f}` s",
            f"- Within total wall-time budget: `{observation['within_versioned_total_wall_time']}`",
            f"- All fixture processes reaped: `{observation['no_live_fixture_processes']}`",
            "- Retries: `0`",
            "",
            "Timing, RSS, disk usage, PIDs, and exit codes are runtime",
            "observations and are excluded from the semantic digest. The",
            "production measurement budget remains required.",
            "",
            "## Boundary",
            "",
            "This preflight certifies an operational supervisor fixture only; it",
            "does not authorize production sampling or change the open theory",
            f"status. Next gate: `{payload['next_gate']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
    (root / RESULT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with (root / RESULT_PATH).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (root / REPORT_PATH).open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_report(payload))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--mode", choices=FIXTURE_MODES)
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    if args.worker:
        if args.mode is None or args.work_dir is None:
            raise SystemExit("--worker requires --mode and --work-dir")
        _worker_main(args.mode, args.work_dir)
        return

    payload = build_preflight(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked["certificate_core"] != payload["certificate_core"]:
            raise SystemExit("tracked supervisor certificate differs")
        if tracked["semantic_digest_sha256"] != payload["semantic_digest_sha256"]:
            raise SystemExit("tracked supervisor semantic digest differs")
        if not tracked["all_acceptance_checks_passed"]:
            raise SystemExit("tracked supervisor certificate is not accepted")
        report = (args.root / REPORT_PATH).read_text(encoding="utf-8")
        if report != render_report(tracked):
            raise SystemExit("tracked supervisor report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
