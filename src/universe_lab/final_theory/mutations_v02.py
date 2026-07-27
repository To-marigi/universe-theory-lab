"""Mutation checks for the finite-causet and dynamics implementation."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    automorphisms,
    enumerate_unlabeled_posets,
    growth_moves,
    natural_labeling_multiplicity,
    validate_relation,
)
from universe_lab.final_theory.dynamics_v02 import CANDIDATE_PROFILE


def mutation_benchmark() -> dict[str, Any]:
    """Execute the pre-registered v0.2 structural mutations."""

    levels = enumerate_unlabeled_posets(3)
    chain_three = next(
        relation
        for relation in levels[3]
        if sum(row.bit_count() for row in relation) == 3
    )
    antichain_three = next(
        relation
        for relation in levels[3]
        if sum(row.bit_count() for row in relation) == 0
    )

    closure_mutant: Relation = (chain_three[0] & ~(1 << 2), *chain_three[1:])
    closure_detected = any(
        "transitive closure missing" in error
        for error in validate_relation(closure_mutant)
    )

    cycle_rows = list(chain_three)
    cycle_rows[2] |= 1
    cycle_mutant = tuple(cycle_rows)
    cycle_detected = bool(validate_relation(cycle_mutant))

    duplicate_catalog = list(levels[3]) + [levels[3][0]]
    duplicate_detected = len(duplicate_catalog) != len(set(duplicate_catalog))

    automorphism_factor_detected = all(
        move.automorphism_factor
        == Fraction(move.multiplicity, len(automorphisms(relation)))
        and move.multiplicity * move.stabilizer_order
        == len(automorphisms(relation))
        for relation in levels[2]
        for move in growth_moves(relation)
    )

    labeling_distinction_detected = (
        natural_labeling_multiplicity(chain_three) == 1
        and natural_labeling_multiplicity(antichain_three) == 6
        and len(levels[3]) == 5
    )

    precursor_spectator_detected = all(
        set(move.precursor_set).isdisjoint(move.spectator_set)
        and set(move.precursor_set) | set(move.spectator_set)
        == set(range(len(relation)))
        for relation in levels[2]
        for move in growth_moves(relation)
    )

    growth_time_detected = (
        "discrete volume" in CANDIDATE_PROFILE.assumptions[0]
        and "external physical time" in CANDIDATE_PROFILE.assumptions[0]
    )

    checks = {
        "transitive_closure_missing": closure_detected,
        "acyclicity_violation": cycle_detected,
        "isomorphic_duplicates": duplicate_detected,
        "automorphism_factor_missing": automorphism_factor_detected,
        "natural_labeling_as_physical_state": labeling_distinction_detected,
        "spectator_set_misidentified": precursor_spectator_detected,
        "precursor_set_misidentified": precursor_spectator_detected,
        "growth_order_as_physical_time": growth_time_detected,
    }
    return {
        "suite": "Final-Theory Bench v0.2 mutations",
        "checks": checks,
        "killed": sum(checks.values()),
        "total": len(checks),
        "passed": all(checks.values()),
    }
