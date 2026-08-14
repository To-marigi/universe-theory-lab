from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_large_n_sampler_extension_design_v042 import (
    NEXT_GATE,
    REPORT_PATH,
    RESULT_PATH,
    build_design,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_large_n_sampler_extension_design_rebuilds_exactly() -> None:
    payload = _tracked()

    assert build_design(ROOT) == payload
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        payload
    )


def test_design_digest_and_authorization_boundary() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["status"] == (
        "PHASE_B_LARGE_N_SAMPLER_EXTENSION_DESIGN_FROZEN_"
        "IMPLEMENTATION_PREFLIGHT_BUDGET_REQUIRED"
    )
    assert payload["all_acceptance_checks_passed"] is True
    assert payload["global_verdict"] == "FINAL_THEORY_OPEN"
    assert payload["scientific_verdict_added"] is False
    assert payload["next_gate"] == NEXT_GATE
    assert payload["production_sampler_available"] is False
    assert payload["implementation_preflight_authorized"] is False
    assert payload["production_sampling_authorized"] is False
    assert payload["authorization_boundary"] == {
        "design_authorized": True,
        "implementation_preflight_authorized": False,
        "new_trajectories_authorized": False,
        "production_sampling_authorized": False,
        "approximate_sampler_authorized": False,
        "solver_run_permitted": False,
        "global_verdict": "FINAL_THEORY_OPEN",
    }


def test_exact_labeled_route_preserves_weights_but_not_cost() -> None:
    payload = _tracked()
    candidate = payload["candidate"]
    route = payload["primary_exact_labeled_sampler"]

    assert candidate["frozen_local_weights"] == {
        "link_fugacity": [2, 3],
        "diamond_fugacity": [3, 2],
        "precursor_fugacity": [4, 5],
        "precursor_weight": (
            "w(P)=(2/3)^Delta_links*(3/2)^Delta_diamonds*(4/5)^|P|"
        ),
    }
    assert "orbit_size*w(P)" in route["unlabeled_quotient_argument"]
    assert route["selection_arithmetic"] == (
        "integer ticket over exact rational weights"
    )
    assert route["branch_order"] == (
        "ascending natural-label precursor bitmask"
    )
    assert route["portable_rng"]["status"] == (
        "FROZEN_DESIGN_NOT_IMPLEMENTED"
    )
    assert "cutoff=R-(R mod M)" in route["portable_rng"][
        "unbiased_ticket_rule"
    ]
    assert "2^n" in route["worst_case_boundary"]
    assert route["overflow_behavior"] == (
        "fail closed with DOWNSET_ENUMERATION_LIMIT; no approximate fallback"
    )


def test_scalability_and_replay_gaps_remain_fail_closed() -> None:
    payload = _tracked()
    approximate = payload["approximate_weighted_ideal_route"]
    replay = payload["independent_replay_design"]
    bounded = payload["bounded_implementation_preflight"]

    assert approximate["status"] == "UNAUTHORIZED_RESEARCH_OPTION"
    assert "mixing" in approximate["missing_certificate"]
    assert "no calls to the primary generator" in replay[
        "second_large_n_implementation"
    ]
    assert bounded["resource_budget_present"] is False
    assert bounded["new_trajectories_authorized"] is False
    assert payload["spectral_protocol_extension"][
        "production_window_status"
    ] == "NOT_FROZEN"
    controls = payload["positive_control_extension"]
    assert controls["geometric_dimension_control"]["current_status"] == (
        "NOT_IMPLEMENTED"
    )
    assert controls["bdg_weighted_ensemble"]["status"] == (
        "UNDEFINED_BLOCKER"
    )
    statistics = payload["statistical_protocol_extension"]
    assert statistics["production_status"] == "NOT_FROZEN"
    assert statistics["simultaneous_interval_method"] == "NOT_FROZEN"


def test_hidden_exponential_observable_path_is_fail_closed() -> None:
    payload = _tracked()
    observables = payload["large_n_observable_extension"]

    assert "2^n" in observables["current_height_bottleneck"]
    assert "longest-path dynamic program" in observables[
        "height_replacement"
    ]
    assert observables["height_target_complexity"] == (
        "O(n^2) on relation bit rows"
    )
    assert "causet_id factorial canonicalization" in observables[
        "forbidden_on_large_n_path"
    ]
    assert payload["acceptance_checks"][
        "hidden_exponential_observable_path_is_recorded_and_replaced_by_design"
    ]["passed"] is True


def test_every_preflight_blocker_has_a_design_owner() -> None:
    payload = _tracked()

    assert set(payload["blocker_mapping"]) == {
        "large-N candidate and negative-control sampler",
        "fixed production spectral plateau window",
        "executable BDG dimension-four ensemble",
        "independent replay implementation",
        "hard wall-time and memory supervision",
        "versioned production measurement budget",
    }
    assert payload["acceptance_checks"][
        "every_preflight_blocker_has_a_design_owner"
    ]["passed"] is True


def test_live_state_points_to_budget_approval_gate() -> None:
    payload = _tracked()
    state = json.loads(
        (ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8")
    )
    campaign = state["affected_campaign"]
    phase_b = campaign["phase_B"]
    design = phase_b["large_n_sampler_extension_design"]

    assert campaign["next_gate"] == NEXT_GATE
    assert phase_b["next_gate"] == NEXT_GATE
    assert design["artifact"] == RESULT_PATH.as_posix()
    assert design["report"] == REPORT_PATH.as_posix()
    assert design["semantic_digest_sha256"] == payload[
        "semantic_digest_sha256"
    ]
    assert design["all_acceptance_checks_passed"] is True
    assert design["production_sampler_available"] is False
    assert design["implementation_preflight_authorized"] is False
    assert design["production_sampling_authorized"] is False
