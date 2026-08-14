from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_sampler_preflight_v042 import (
    REPORT_PATH,
    RESULT_PATH,
    build_preflight,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_sampler_preflight_rebuilds_exactly() -> None:
    assert build_preflight(ROOT) == _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        _tracked()
    )


def test_sampler_preflight_digest_and_regression_checks() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == (
        "PHASE_B_BOUNDED_SAMPLER_PREFLIGHT_COMPLETE_NON_EVIDENTIARY"
    )
    assert payload["configuration"] == {
        "max_n": 3,
        "trajectories_per_seed": 1024,
        "seeds": [7, 17, 29, 43, 71],
        "selection_rule": "integer ticket over exact Fraction branch weights",
        "floating_point_in_dynamics": False,
    }
    assert payload["exact_baseline"]["enumeration_counts"] == [1, 1, 2, 5]
    assert payload["exact_baseline"]["terminal_state_count"] == 5
    assert payload["route_and_normalization_audit"][
        "all_normalized_exactly"
    ]
    assert payload["route_and_normalization_audit"][
        "all_targets_in_next_level"
    ]
    assert payload["route_and_normalization_audit"][
        "all_growth_move_target_sets_match"
    ]
    assert all(payload["replay_digest_matches"])
    assert all(
        comparison["passed"]
        for comparison in payload["exact_distribution_comparisons"]
    )


def test_sampler_preflight_is_not_promoted_to_scientific_evidence() -> None:
    payload = _tracked()
    assert payload["candidate_identity_mismatch_present"] is False
    assert payload["candidate_identity_certified"] is True
    assert payload["sampling_authorized"] is False
    assert payload["scientific_verdict_added"] is False
    assert payload["all_acceptance_checks_passed"] is True
    assert "does not establish" in payload["claim_boundary"]
