from __future__ import annotations

import itertools
from fractions import Fraction

import pytest

from universe_lab.final_theory.causal_sets import (
    downsets,
    enumerate_unlabeled_posets,
    height,
)
from universe_lab.final_theory.continuum_observables_v042 import relabel_relation
from universe_lab.final_theory.phase_b_large_n_runtime_v042 import (
    CounterRngLimit,
    DownsetEnumerationLimit,
    TicketDraw,
    collect_downsets_limited,
    draw_integer_ticket,
    height_longest_path,
    integer_ticket_weights,
    iter_downsets_limited,
    sha256_counter_bytes,
)


def test_height_dynamic_program_matches_exhaustive_oracle_through_n5() -> None:
    for level in enumerate_unlabeled_posets(5):
        for relation in level:
            assert height_longest_path(relation) == height(relation)


def test_height_dynamic_program_is_label_invariant_through_n4() -> None:
    for level in enumerate_unlabeled_posets(4):
        for relation in level:
            expected = height_longest_path(relation)
            for permutation in itertools.permutations(range(len(relation))):
                assert height_longest_path(
                    relabel_relation(relation, permutation)
                ) == expected


def test_height_dynamic_program_rejects_a_cycle() -> None:
    with pytest.raises(ValueError, match="directed cycle"):
        height_longest_path((2, 1))


def test_order_ideal_generator_matches_exhaustive_downsets_through_n5() -> None:
    for level in enumerate_unlabeled_posets(5):
        for relation in level:
            observed = tuple(
                iter_downsets_limited(
                    relation, max_downsets=1 << len(relation)
                )
            )
            assert observed == downsets(relation)
            assert observed == tuple(sorted(observed))


def test_order_ideal_generator_fails_closed_after_cap() -> None:
    antichain = enumerate_unlabeled_posets(5)[5][0]
    iterator = iter_downsets_limited(antichain, max_downsets=10)
    assert list(itertools.islice(iterator, 10)) == list(range(10))
    with pytest.raises(DownsetEnumerationLimit) as raised:
        next(iterator)
    assert raised.value.code == "DOWNSET_ENUMERATION_LIMIT"
    assert raised.value.limit == 10


def test_collect_downsets_does_not_return_partial_results() -> None:
    antichain = enumerate_unlabeled_posets(5)[5][0]
    with pytest.raises(DownsetEnumerationLimit):
        collect_downsets_limited(antichain, max_downsets=10)
    assert collect_downsets_limited(antichain, max_downsets=32) == tuple(
        range(32)
    )


def test_integer_ticket_weights_are_exact_and_primitive() -> None:
    assert integer_ticket_weights(
        (Fraction(1, 2), Fraction(3, 4), Fraction(5, 6))
    ) == (6, 9, 10)
    assert integer_ticket_weights((Fraction(2, 3), Fraction(4, 9))) == (3, 2)
    for invalid in ((0.1, Fraction(1, 10)), ("1/2", Fraction(1, 2)), (True, 1)):
        with pytest.raises(TypeError):
            integer_ticket_weights(invalid)  # type: ignore[arg-type]


def test_counter_stream_is_replayable_and_coordinate_bound() -> None:
    arguments = {
        "sampling_seed": 7,
        "trajectory_index": 11,
        "growth_step": 3,
        "ticket_index": 5,
        "rejection_attempt": 0,
        "byte_count": 65,
    }
    first = sha256_counter_bytes(**arguments)
    assert first.hex() == (
        "55e22f73ca4dd43619a6f37494aa7445d664c3c769a674c10a4dd34671d4f0f8a"
        "2401bfacc6d1007958614e4934ed32626a4546325199f58c113fc31280fb1f6e2"
    )
    assert first == sha256_counter_bytes(**arguments)
    changed = dict(arguments, ticket_index=6)
    assert first != sha256_counter_bytes(**changed)
    with pytest.raises(ValueError):
        sha256_counter_bytes(**dict(arguments, sampling_seed=-1))
    with pytest.raises(ValueError):
        sha256_counter_bytes(**dict(arguments, rejection_attempt=-1))


def test_counter_stream_rejects_unsafe_sizes_and_coordinate_types() -> None:
    arguments = {
        "sampling_seed": 7,
        "trajectory_index": 11,
        "growth_step": 3,
        "ticket_index": 5,
        "rejection_attempt": 0,
        "byte_count": 65,
    }
    with pytest.raises(CounterRngLimit):
        sha256_counter_bytes(**dict(arguments, byte_count=1 << 20 | 1))
    with pytest.raises(TypeError):
        sha256_counter_bytes(**dict(arguments, sampling_seed=True))
    with pytest.raises(TypeError):
        sha256_counter_bytes(**dict(arguments, ticket_index=1.0))


def test_integer_ticket_draw_is_replayable_and_in_range() -> None:
    arguments = {
        "total_weight": 37,
        "sampling_seed": 17,
        "trajectory_index": 2,
        "growth_step": 9,
        "ticket_index": 4,
    }
    first = draw_integer_ticket(**arguments)
    assert first.ticket == 29
    assert first.rejection_attempt == 0
    assert first == draw_integer_ticket(**arguments)
    assert 0 <= first.ticket < arguments["total_weight"]
    assert first.rejection_attempt >= 0


def test_integer_ticket_draw_uses_rejection_cutoff() -> None:
    draw = draw_integer_ticket(
        47,
        sampling_seed=1,
        trajectory_index=0,
        growth_step=0,
        ticket_index=47,
    )
    assert draw == TicketDraw(ticket=37, rejection_attempt=1)


def test_integer_ticket_draw_fails_closed_after_rejection_cap(monkeypatch) -> None:
    from universe_lab.final_theory import phase_b_large_n_runtime_v042 as runtime

    monkeypatch.setattr(runtime, "MAX_REJECTION_ATTEMPTS", 3)
    monkeypatch.setattr(runtime, "sha256_counter_bytes", lambda **_kwargs: b"\xff")
    with pytest.raises(CounterRngLimit):
        draw_integer_ticket(
            47,
            sampling_seed=1,
            trajectory_index=0,
            growth_step=0,
            ticket_index=47,
        )
