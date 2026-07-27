from __future__ import annotations

from fractions import Fraction

import pytest

from universe_lab.final_theory.causal_sets import (
    automorphisms,
    brute_force_unlabeled_posets,
    canonical_code,
    enumerate_unlabeled_posets,
    enumeration_audit,
    growth_moves,
    natural_labeling_multiplicity,
    validate_relation,
)


def test_exact_unlabeled_counts_through_five() -> None:
    levels = enumerate_unlabeled_posets(5)
    assert [len(level) for level in levels] == [1, 1, 2, 5, 16, 63]


@pytest.mark.parametrize("n", range(5))
def test_independent_oracle_matches_production(n: int) -> None:
    production = {
        canonical_code(relation) for relation in enumerate_unlabeled_posets(4)[n]
    }
    oracle = {
        canonical_code(relation) for relation in brute_force_unlabeled_posets(n)
    }
    assert production == oracle


def test_every_production_relation_is_a_poset() -> None:
    for level in enumerate_unlabeled_posets(5):
        assert all(validate_relation(relation) == [] for relation in level)


def test_orbit_stabilizer_and_precursor_partition() -> None:
    for relation in enumerate_unlabeled_posets(4)[3]:
        group_order = len(automorphisms(relation))
        for move in growth_moves(relation):
            assert move.multiplicity * move.stabilizer_order == group_order
            assert move.automorphism_factor == Fraction(
                move.multiplicity, group_order
            )
            assert set(move.precursor_set).isdisjoint(move.spectator_set)
            assert set(move.precursor_set) | set(move.spectator_set) == set(
                range(len(relation))
            )


def test_natural_labelings_are_not_physical_state_multiplicity() -> None:
    level = enumerate_unlabeled_posets(3)[3]
    antichain = next(relation for relation in level if sum(relation) == 0)
    chain = next(
        relation for relation in level if sum(row.bit_count() for row in relation) == 3
    )
    assert len(level) == 5
    assert natural_labeling_multiplicity(antichain) == 6
    assert natural_labeling_multiplicity(chain) == 1


def test_enumeration_audit_passes() -> None:
    result = enumeration_audit()
    assert result["passed"]
    assert result["resource_status"] == "EXACT_COMPLETE_WITHIN_DECLARED_DOMAIN"
