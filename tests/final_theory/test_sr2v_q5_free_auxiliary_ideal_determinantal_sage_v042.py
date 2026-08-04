"""Exact Sage integration checks for the bounded determinantal route."""

from __future__ import annotations

from typing import Any, cast

import pytest

sage = pytest.importorskip("sage.all")

from universe_lab.final_theory import (  # noqa: E402
    sr2v_q5_free_auxiliary_ideal_worker_v042 as worker,
)


class _RecordingEmitter:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, message_type: str, event: str, **fields: Any) -> None:
        self.events.append({"event": event, "message_type": message_type, **fields})


def _policy(scope: str = "QQ_EXACT_CANDIDATE") -> dict[str, Any]:
    return {
        "certificate_requirement": "EXACT_EXPONENT_MEMBERSHIP_DIRECT_LIFT_PENDING",
        "coefficient_scope": scope,
        "max_certificate_bytes": 8 * 1024**2,
        "max_certificate_terms": 100_000,
        "max_generated_minor_terms": 1_000_000,
        "max_minor_count": 64,
        "max_rounds": 8,
        "semantic_digest_sha256": "0" * 64,
        "task_kind": "COMBINED_SUBSET_CERTIFICATE",
    }


def _run(
    ring: Any,
    pairs: list[tuple[Any, Any]],
    *,
    factors: list[tuple[str, Any]] | None = None,
) -> dict[str, Any]:
    emitter = _RecordingEmitter()
    rows = [[index, 2 * index + 1, 2 * index + 2] for index in range(len(pairs))]
    result = worker._run_determinantal_cegar(  # noqa: SLF001
        algorithm="libsingular:slimgb",
        common={},
        emitter=cast(worker.Emitter, emitter),
        factors=[] if factors is None else factors,
        generator_pairs=pairs,
        max_live_basis_terms=10_000,
        policy=_policy(),
        ring=ring,
        rows=rows,
    )
    assert emitter.events[0]["event"] == "DETERMINANTAL_SUBSET_PLANNED"
    assert emitter.events[-1]["event"] == "DETERMINANTAL_ROUND_COMPLETED"
    return result


def test_localized_positive_example_matches_direct_auxiliary_ideal() -> None:
    ring = sage.PolynomialRing(sage.QQ, ["x", "y"], order="degrevlex")
    x, y = ring.gens()
    result = _run(ring, [(y, x), (-y, -x), (ring.zero(), y)], factors=[("x", x)])

    assert result["status"] == "DETERMINANTAL_CONDITIONS_CERTIFIED_DIRECT_LIFT_PENDING"
    assert result["determinantal_conditions_certified"] is True
    assert result["effective_row_count"] == 2
    assert len(result["row_unit_associate_relations"]) == 1
    assert result["entry_condition"]["is_unit_ideal"] is True
    targets = result["minor_prefix_trace"][-1]["radical_targets"]
    assert [target["radical_membership_verified"] for target in targets] == [True, True]

    extended = sage.PolynomialRing(sage.QQ, ["x", "y", "h"], order="degrevlex")
    ex, ey, h = extended.gens()
    direct = extended.ideal([ey * h + ex, -ey * h - ex, ey])
    localized, _exponent = direct.saturation(extended.ideal([ex]))
    assert list(localized.groebner_basis()) == [extended.one()]


def test_nonunit_subset_is_inconclusive_and_matches_direct_failure() -> None:
    ring = sage.PolynomialRing(sage.QQ, ["x", "y"], order="degrevlex")
    x, _y = ring.gens()
    result = _run(ring, [(x, ring.one()), (1 - x, ring.one())])

    assert result["status"] == "DETERMINANTAL_SUBSET_INCONCLUSIVE"
    assert result["determinantal_conditions_certified"] is False
    assert result["entry_condition"]["is_unit_ideal"] is True
    assert not all(
        target["radical_membership_verified"]
        for target in result["minor_prefix_trace"][-1]["radical_targets"]
    )

    extended = sage.PolynomialRing(sage.QQ, ["x", "h"], order="degrevlex")
    ex, h = extended.gens()
    direct = extended.ideal([ex * h + 1, (1 - ex) * h + 1])
    assert list(direct.groebner_basis()) != [extended.one()]


def test_localized_minor_unit_shortcut_is_detected() -> None:
    ring = sage.PolynomialRing(sage.QQ, ["s", "x"], order="degrevlex")
    s, _x = ring.gens()
    result = _run(ring, [(s, ring.zero()), (ring.zero(), s)], factors=[("s", s)])

    assert result["determinantal_conditions_certified"] is True
    assert result["minor_prefix_trace"][-1]["minor_condition"]["is_unit_ideal"] is True
    assert {
        target["membership_reason"]
        for target in result["minor_prefix_trace"][-1]["radical_targets"]
    } == {"MINOR_IDEAL_IS_UNIT", "ZERO_TARGET"}


def test_minor_cost_cap_stops_before_materializing_the_next_minor() -> None:
    ring = sage.PolynomialRing(sage.QQ, ["x"], order="degrevlex")
    (x,) = ring.gens()

    candidates, discarded, resource_limit = worker._determinantal_minor_candidates(  # noqa: SLF001
        [[0, 1, 2], [1, 3, 4]],
        [(x, ring.one()), (ring.one(), x)],
        [0, 1],
        max_generated_minor_terms=1,
    )

    assert candidates == []
    assert discarded == []
    assert resource_limit == {
        "generated_minor_cost_upper_bound": 0,
        "max_generated_minor_terms": 1,
        "next_minor_cost_upper_bound": 2,
        "next_schedule_index": 0,
        "projected_generated_minor_cost_upper_bound": 2,
        "reason": "MAX_GENERATED_MINOR_TERM_COST_BOUND_EXCEEDED",
    }
