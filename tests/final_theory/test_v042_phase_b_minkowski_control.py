from __future__ import annotations

import pytest

from universe_lab.final_theory.causal_sets import validate_relation
from universe_lab.final_theory.phase_b_minkowski_control_v042 import (
    compare_control_replay,
    independent_anchor_audit,
    sprinkle_4d_control,
)


@pytest.mark.parametrize("target_n", [1, 4, 8, 13])
def test_minkowski_control_primary_and_replay_match(target_n: int) -> None:
    record = compare_control_replay(
        target_n, sampling_seed=101, trajectory_index=3
    )

    assert record["points_match"] is True
    assert record["relation_digest_match"] is True
    assert record["target_dimension"] == 4
    assert record["candidate_evidence"] is False


def test_minkowski_control_is_fixed_cardinality_and_natural() -> None:
    control = sprinkle_4d_control(
        13,
        sampling_seed=127,
        trajectory_index=0,
        implementation="primary",
    )

    assert len(control.points) == 13
    assert len(control.relation) == 13
    assert not validate_relation(control.relation)
    assert all(
        point.time >= 0.0
        and point.time <= 1.0
        and point.x * point.x + point.y * point.y + point.z * point.z
        <= min(point.time, 1.0 - point.time) ** 2 + 1e-12
        for point in control.points
    )
    assert all(
        row & ((1 << (index + 1)) - 1) == 0
        for index, row in enumerate(control.relation)
    )


def test_minkowski_anchor_is_independent_and_non_evidentiary() -> None:
    audit = independent_anchor_audit()

    assert audit["passed"] is True
    assert audit["dimension"] == 4
    assert audit["candidate_evidence"] is False


def test_minkowski_control_rejects_invalid_size() -> None:
    with pytest.raises(ValueError):
        sprinkle_4d_control(0, sampling_seed=1, trajectory_index=0)
