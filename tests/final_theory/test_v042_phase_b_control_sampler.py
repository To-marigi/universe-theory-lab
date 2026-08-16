from __future__ import annotations

import pytest

from universe_lab.final_theory.causal_sets import validate_relation
from universe_lab.final_theory.phase_b_control_sampler_v042 import (
    DownsetEnumerationLimit,
    _frontier_ideals,
    _primary_branches,
    _replay_branches,
    compare_primary_and_replay,
    measure_relation,
    relation_digest,
    sample_trajectory,
)


@pytest.mark.parametrize(
    "profile_id",
    ["causal_information_v2_sparse_kraus", "random_growth_control"],
)
@pytest.mark.parametrize("target_n", [1, 2, 3, 4, 5])
def test_primary_and_independent_replay_match_on_bounded_domain(
    profile_id: str, target_n: int
) -> None:
    comparison = compare_primary_and_replay(
        target_n,
        sampling_seed=101,
        trajectory_index=7,
        profile_id=profile_id,  # type: ignore[arg-type]
        max_downsets=4096,
    )

    assert comparison["all_branch_checks_passed"] is True
    assert comparison["trajectory_digests_match"] is True
    assert comparison["scientific_evidence"] is False


def test_sampler_replay_is_deterministic_and_natural() -> None:
    first = sample_trajectory(
        8,
        sampling_seed=127,
        trajectory_index=3,
        profile_id="random_growth_control",
        implementation="primary",
        max_downsets=4096,
    )
    second = sample_trajectory(
        8,
        sampling_seed=127,
        trajectory_index=3,
        profile_id="random_growth_control",
        implementation="primary",
        max_downsets=4096,
    )

    assert first == second
    assert all(not validate_relation(relation) for relation in first.relations)
    assert all(
        all(row & ((1 << (index + 1)) - 1) == 0 for index, row in enumerate(relation))
        for relation in first.relations
    )
    assert len(first.semantic_digest) == 64


def test_downset_cap_fails_closed_in_both_implementations() -> None:
    antichain = (0,) * 13
    with pytest.raises(DownsetEnumerationLimit):
        _primary_branches(antichain, "random_growth_control", 4096)
    with pytest.raises(DownsetEnumerationLimit):
        _replay_branches(antichain, "random_growth_control", 4096)
    with pytest.raises(DownsetEnumerationLimit):
        tuple(_frontier_ideals(antichain, max_downsets=4096))


def test_observable_path_is_exact_and_non_evidentiary() -> None:
    trajectory = sample_trajectory(
        5,
        sampling_seed=17,
        trajectory_index=2,
        profile_id="causal_information_v2_sparse_kraus",
        implementation="primary",
        max_downsets=4096,
    )
    record = measure_relation(trajectory.relations[-1])

    assert record["n"] == 5
    assert record["relation_digest"] == relation_digest(trajectory.relations[-1])
    assert record["height"] >= 1
    assert record["ordering_fraction"] is not None


def test_spectral_path_is_closed_until_window_is_frozen() -> None:
    trajectory = sample_trajectory(
        4,
        sampling_seed=29,
        trajectory_index=0,
        profile_id="random_growth_control",
        implementation="primary",
        max_downsets=4096,
    )

    with pytest.raises(NotImplementedError, match="spectral production path"):
        measure_relation(trajectory.relations[-1], spectral_steps=4)
