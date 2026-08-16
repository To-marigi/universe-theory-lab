from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_implementation_preflight_v042 import (
    CONFIG_PATH,
    REPORT_PATH,
    RESULT_PATH,
    build_preflight,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_implementation_preflight_certificate_rebuilds_exactly() -> None:
    tracked = _tracked()
    rebuilt = build_preflight(ROOT)
    assert rebuilt["certificate_core"] == tracked["certificate_core"]
    assert rebuilt["semantic_digest_sha256"] == tracked[
        "semantic_digest_sha256"
    ]
    assert stable_hash(rebuilt["certificate_core"]) == rebuilt[
        "semantic_digest_sha256"
    ]
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        tracked
    )


def test_implementation_preflight_is_authorized_but_production_is_closed() -> None:
    tracked = _tracked()
    config = json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))
    assert tracked["all_acceptance_checks_passed"] is True
    assert tracked["implementation_preflight_authorized"] is True
    assert tracked["production_sampling_authorized"] is False
    assert tracked["new_trajectories"] == 0
    assert tracked["solver_calls"] == 0
    assert tracked["production_measurement_budget_still_required"] is True
    assert tracked["runtime_observation"]["max_child_tracemalloc_bytes"] > 0
    assert config["owner_approval_present"] is True
    assert config["limits"]["new_sampled_trajectories"] == 0
    assert config["limits"]["solver_calls"] == 0


def test_implementation_preflight_records_all_child_checks() -> None:
    checks = _tracked()["certificate_core"]["checks"]
    assert all(checks.values())
    assert checks["runtime_audit_rebuild_matches"] is True
    assert checks["cost_preflight_rebuild_matches"] is True
    assert checks["supervisor_rebuild_matches"] is True
    assert checks["large_n_forbidden_paths_absent"] is True
    assert checks["new_trajectories_zero"] is True
    assert checks["solver_calls_zero"] is True
