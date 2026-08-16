from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_control_implementation_preflight_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_preflight,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_control_implementation_preflight_rebuilds_exactly() -> None:
    payload = _tracked()

    assert build_preflight(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_control_implementation_preflight_digest_and_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["next_gate"] == NEXT_GATE
    assert payload["new_control_trajectories"] == 0
    assert payload["candidate_trajectories"] == 0
    assert payload["solver_calls"] == 0
    assert payload["control_measurement_authorized"] is False
    assert payload["production_sampling_authorized"] is False


def test_minkowski_control_preflight_records_non_evidentiary_replay() -> None:
    payload = _tracked()
    control = payload["minkowski_control"]

    assert control["target_dimension"] == 4
    assert control["fixture_sizes"] == [1, 4, 8, 13]
    assert control["fixture_seeds"] == [101, 127]
    assert control["fixture_count"] == 8
    assert control["candidate_evidence"] is False
    assert control["anchor"]["passed"] is True
    assert payload["acceptance_checks"][
        "minkowski_primary_and_replay_match"
    ] is True
