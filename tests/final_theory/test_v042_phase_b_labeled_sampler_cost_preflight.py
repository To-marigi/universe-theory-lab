from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.causal_sets import add_maximal
from universe_lab.final_theory.dynamics_v02 import _candidate_local_weight
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_labeled_sampler_cost_preflight_v042 import (
    CONFIG_PATH,
    REPORT_PATH,
    RESULT_PATH,
    _antichain,
    _capped_primary,
    _chain,
    _local_weights,
    build_preflight,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_cost_preflight_certificate_rebuilds_without_timing_binding() -> None:
    tracked = _tracked()
    rebuilt = build_preflight(ROOT)

    assert rebuilt["certificate_core"] == tracked["certificate_core"]
    assert rebuilt["semantic_digest_sha256"] == tracked["semantic_digest_sha256"]
    assert stable_hash(rebuilt["certificate_core"]) == rebuilt[
        "semantic_digest_sha256"
    ]
    assert (ROOT / REPORT_PATH).is_file()


def test_primary_and_independent_iterators_are_equivalent_or_fail_closed() -> None:
    payload = _tracked()
    fixtures = payload["certificate_core"]["fixtures"]

    complete = [item for item in fixtures if item["primary_status"] == "COMPLETE"]
    capped = [
        item
        for item in fixtures
        if item["primary_status"] == "DOWNSET_ENUMERATION_LIMIT"
    ]
    assert complete
    assert all(item["primary_independent_equivalent"] for item in complete)
    assert len(capped) == 1
    assert capped[0]["independent_status"] == "DOWNSET_ENUMERATION_LIMIT"
    assert capped[0]["downset_count"] is None


def test_cost_preflight_is_not_production_authorization() -> None:
    payload = _tracked()
    config = json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))

    assert payload["all_acceptance_checks_passed"] is True
    assert payload["cost_observation_within_versioned_budget"] is True
    assert payload["new_trajectories"] == 0
    assert payload["solver_calls"] == 0
    assert payload["production_sampler_available"] is False
    assert payload["production_sampling_authorized"] is False
    assert payload["scientific_verdict_added"] is False
    assert config["owner_approval_present"] is True
    assert config["limits"]["new_sampled_trajectories"] == 0
    assert config["limits"]["solver_calls"] == 0


def test_live_state_records_cost_preflight_without_reopening_production() -> None:
    state = json.loads(
        (ROOT / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8")
    )
    record = state["affected_campaign"]["phase_B"][
        "labeled_sampler_cost_preflight"
    ]

    assert record["semantic_digest_sha256"] == _tracked()[
        "semantic_digest_sha256"
    ]
    assert (
        record["pinned_container_replay_semantic_digest_sha256"]
        == record["semantic_digest_sha256"]
    )
    assert record["production_measurement_budget_still_required"] is True
    assert record["production_sampling_authorized"] is False


def test_cost_module_does_not_import_production_or_unlabeled_paths() -> None:
    source = (
        ROOT
        / "src/universe_lab/final_theory/phase_b_labeled_sampler_cost_preflight_v042.py"
    ).read_text(encoding="utf-8")

    assert "from universe_lab.final_theory.dynamics_v02" not in source
    assert "enumerate_" + "unlabeled_posets" not in source
    assert "transition_" + "instrument" not in source
    assert "propagate_" + "distribution" not in source
    assert "itertools." + "permutations" not in source
    assert "canonicalize" + "(" not in source
    assert "automorphisms" + "(" not in source


def test_frozen_weight_formula_matches_independent_candidate_formula() -> None:
    config = json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))
    for relation in (_chain(5), _antichain(5)):
        downsets, status = _capped_primary(relation, max_downsets=4096)
        assert status == "COMPLETE"
        assert downsets is not None
        observed, _tickets = _local_weights(relation, downsets, config)
        expected = tuple(
            _candidate_local_weight(
                relation,
                add_maximal(relation, precursor),
                precursor.bit_count(),
            )
            for precursor in downsets
        )
        assert observed == expected
