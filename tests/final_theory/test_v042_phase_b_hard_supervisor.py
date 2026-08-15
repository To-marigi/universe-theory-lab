from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_supervisor_v042 import (
    CONFIG_PATH,
    MODULE_PATH,
    REPORT_PATH,
    RESULT_PATH,
    TEST_PATH,
    build_preflight,
    run_fixture,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def _config() -> dict[str, object]:
    return json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))


def test_supervisor_certificate_rebuilds_without_timing_binding() -> None:
    tracked = _tracked()
    rebuilt = build_preflight(ROOT)

    assert rebuilt["certificate_core"] == tracked["certificate_core"]
    assert rebuilt["semantic_digest_sha256"] == tracked[
        "semantic_digest_sha256"
    ]
    assert stable_hash(rebuilt["certificate_core"]) == rebuilt[
        "semantic_digest_sha256"
    ]
    assert (ROOT / REPORT_PATH).is_file()


def test_timeout_terminates_child_tree_without_promotion(tmp_path: Path) -> None:
    config = _config()
    final_path = tmp_path / "timeout.json"
    result = run_fixture(
        ROOT,
        "tree_timeout",
        config["fixtures"]["tree_timeout"],
        final_path,
    )

    assert result["outcome"] == {
        "mode": "tree_timeout",
        "status": "RESOURCE_LIMIT_OPEN",
        "reason": "RESOURCE_LIMIT_OPEN_WALL_TIME",
        "promoted": False,
        "process_tree_terminated": True,
        "attempt_count": 1,
    }
    assert result["runtime"]["child_pid"] is not None
    assert result["runtime"]["live_process_ids_after_cleanup"] == []
    assert not final_path.exists()


def test_atomic_promotion_requires_independent_digest_validation(
    tmp_path: Path,
) -> None:
    config = _config()
    success_path = tmp_path / "success.json"
    success = run_fixture(
        ROOT,
        "success",
        config["fixtures"]["success"],
        success_path,
    )
    assert success["outcome"]["status"] == "COMPLETED"
    assert success["outcome"]["promoted"] is True
    assert success_path.is_file()
    promoted = json.loads(success_path.read_text(encoding="utf-8"))
    assert promoted["semantic_digest_sha256"]

    invalid_path = tmp_path / "invalid.json"
    invalid = run_fixture(
        ROOT,
        "invalid_certificate",
        config["fixtures"]["invalid_certificate"],
        invalid_path,
    )
    assert invalid["outcome"]["status"] == "ERROR"
    assert invalid["outcome"]["reason"] == "INVALID_CERTIFICATE"
    assert invalid["outcome"]["promoted"] is False
    assert not invalid_path.exists()


def test_memory_and_disk_caps_fail_closed_without_retries(tmp_path: Path) -> None:
    config = _config()
    memory = run_fixture(
        ROOT,
        "memory_limit",
        config["fixtures"]["memory_limit"],
        tmp_path / "memory.json",
    )
    disk = run_fixture(
        ROOT,
        "disk_limit",
        config["fixtures"]["disk_limit"],
        tmp_path / "disk.json",
    )

    assert memory["outcome"]["reason"] == "RESOURCE_LIMIT_OPEN_MEMORY"
    assert disk["outcome"]["reason"] == "RESOURCE_LIMIT_OPEN_DISK"
    assert memory["outcome"]["attempt_count"] == 1
    assert disk["outcome"]["attempt_count"] == 1
    assert not (tmp_path / "memory.json").exists()
    assert not (tmp_path / "disk.json").exists()


def test_live_state_records_hard_supervisor_without_production_authorization() -> None:
    state = json.loads(
        (ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8")
    )
    record = state["affected_campaign"]["phase_B"][
        "hard_supervisor_preflight"
    ]
    tracked = _tracked()

    assert record["semantic_digest_sha256"] == tracked[
        "semantic_digest_sha256"
    ]
    assert record["pinned_container_replay_semantic_digest_sha256"] == tracked[
        "semantic_digest_sha256"
    ]
    assert record["host_replay_check_passed"] is True
    assert record["pinned_container_replay_check_passed"] is True
    assert record["production_sampling_authorized"] is False
    assert record["new_trajectories"] == 0
    assert record["solver_calls"] == 0


def test_supervisor_module_is_not_a_production_or_unlabeled_path() -> None:
    source = (ROOT / MODULE_PATH).read_text(encoding="utf-8")

    assert "dynamics_v02" not in source
    assert "enumerate_" + "unlabeled_posets" not in source
    assert "transition_" + "instrument" not in source
    assert "propagate_" + "distribution" not in source
    assert "itertools." + "permutations" not in source
    assert (ROOT / TEST_PATH).is_file()
