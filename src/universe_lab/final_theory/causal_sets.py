"""Exact finite causal-set enumeration for Final-Theory Bench v0.2.

The production enumerator grows an unlabeled poset by adjoining one new maximal
element above a down-set.  Canonicalization is deliberately brute force: the v0.2
exact domain is n <= 5, where exhaustive permutations are small and auditable.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from functools import cache

Relation = tuple[int, ...]

KNOWN_UNLABELED_POSET_COUNTS = {0: 1, 1: 1, 2: 2, 3: 5, 4: 16, 5: 63}


def has_relation(relation: Relation, lower: int, upper: int) -> bool:
    """Return whether ``lower < upper`` in the strict partial order."""

    return bool(relation[lower] & (1 << upper))


def validate_relation(relation: Relation) -> list[str]:
    """Return exact strict-partial-order validation errors."""

    n = len(relation)
    errors: list[str] = []
    allowed = (1 << n) - 1
    for index, row in enumerate(relation):
        if row & ~allowed:
            errors.append(f"row {index} contains an out-of-range vertex")
        if row & (1 << index):
            errors.append(f"row {index} violates irreflexivity")
    for lower in range(n):
        for middle in range(n):
            if not has_relation(relation, lower, middle):
                continue
            for upper in range(n):
                if has_relation(relation, middle, upper) and not has_relation(
                    relation, lower, upper
                ):
                    errors.append(
                        f"transitive closure missing {lower}<{upper} via {middle}"
                    )
    return sorted(set(errors))


def _relation_code_for_order(relation: Relation, order: tuple[int, ...]) -> int:
    n = len(relation)
    code = 0
    for new_lower, old_lower in enumerate(order):
        for new_upper, old_upper in enumerate(order):
            if has_relation(relation, old_lower, old_upper):
                code |= 1 << (new_lower * n + new_upper)
    return code


def relation_from_code(n: int, code: int) -> Relation:
    """Decode the canonical row-major bit representation."""

    mask = (1 << n) - 1
    return tuple((code >> (row * n)) & mask for row in range(n))


@cache
def canonical_code(relation: Relation) -> int:
    """Return the lexicographically minimal code over every relabeling."""

    errors = validate_relation(relation)
    if errors:
        raise ValueError("; ".join(errors))
    if not relation:
        return 0
    return min(
        _relation_code_for_order(relation, order)
        for order in itertools.permutations(range(len(relation)))
    )


def canonicalize(relation: Relation) -> Relation:
    """Return a deterministic representative of an unlabeled finite poset."""

    return relation_from_code(len(relation), canonical_code(relation))


def causet_id(relation: Relation) -> str:
    """Return a stable finite-causet identifier."""

    n = len(relation)
    width = max(1, math.ceil(n * n / 4))
    return f"p{n}-{canonical_code(relation):0{width}x}"


@cache
def automorphisms(relation: Relation) -> tuple[tuple[int, ...], ...]:
    """Enumerate every order automorphism exactly."""

    n = len(relation)
    found = []
    for permutation in itertools.permutations(range(n)):
        if all(
            has_relation(relation, lower, upper)
            == has_relation(relation, permutation[lower], permutation[upper])
            for lower in range(n)
            for upper in range(n)
        ):
            found.append(permutation)
    return tuple(found)


@cache
def natural_labeling_multiplicity(relation: Relation) -> int:
    """Count linear extensions of the strict order."""

    n = len(relation)
    count = 0
    for order in itertools.permutations(range(n)):
        position = {vertex: index for index, vertex in enumerate(order)}
        if all(
            not has_relation(relation, lower, upper)
            or position[lower] < position[upper]
            for lower in range(n)
            for upper in range(n)
        ):
            count += 1
    return count


def is_downset(relation: Relation, subset: int) -> bool:
    """Return whether a vertex bit-set is past closed."""

    n = len(relation)
    for member in range(n):
        if not subset & (1 << member):
            continue
        for predecessor in range(n):
            if has_relation(relation, predecessor, member) and not subset & (
                1 << predecessor
            ):
                return False
    return True


def downsets(relation: Relation) -> tuple[int, ...]:
    """Enumerate all precursor sets in deterministic integer order."""

    return tuple(
        subset
        for subset in range(1 << len(relation))
        if is_downset(relation, subset)
    )


def add_maximal(relation: Relation, precursor: int) -> Relation:
    """Adjoin one maximal element whose complete past is ``precursor``."""

    if not is_downset(relation, precursor):
        raise ValueError("precursor must be a down-set")
    n = len(relation)
    rows = list(relation) + [0]
    for predecessor in range(n):
        if precursor & (1 << predecessor):
            rows[predecessor] |= 1 << n
    grown = tuple(rows)
    errors = validate_relation(grown)
    if errors:
        raise ValueError("; ".join(errors))
    return grown


def _mapped_subset(subset: int, permutation: tuple[int, ...]) -> int:
    result = 0
    for vertex, image in enumerate(permutation):
        if subset & (1 << vertex):
            result |= 1 << image
    return result


def precursor_orbit(relation: Relation, precursor: int) -> tuple[int, ...]:
    """Return the automorphism orbit of a precursor bit-set."""

    return tuple(
        sorted(
            {
                _mapped_subset(precursor, permutation)
                for permutation in automorphisms(relation)
            }
        )
    )


def maximal_elements_in_subset(relation: Relation, subset: int) -> tuple[int, ...]:
    """Return subset elements with no larger element inside the subset."""

    return tuple(
        vertex
        for vertex in range(len(relation))
        if subset & (1 << vertex)
        and not any(
            subset & (1 << other) and has_relation(relation, vertex, other)
            for other in range(len(relation))
        )
    )


@dataclass(frozen=True)
class ExactGrowthMove:
    """An automorphism-orbit of growth moves between unlabeled histories."""

    source_history: str
    target_history: str
    precursor_set: tuple[int, ...]
    spectator_set: tuple[int, ...]
    multiplicity: int
    automorphism_factor: Fraction
    stabilizer_order: int
    move_class: str

    def to_record(self) -> dict[str, object]:
        return {
            "source_history": self.source_history,
            "target_history": self.target_history,
            "precursor_set": list(self.precursor_set),
            "spectator_set": list(self.spectator_set),
            "multiplicity": self.multiplicity,
            "automorphism_factor": {
                "numerator": self.automorphism_factor.numerator,
                "denominator": self.automorphism_factor.denominator,
            },
            "stabilizer_order": self.stabilizer_order,
            "move_class": self.move_class,
        }


def growth_moves(relation: Relation) -> tuple[ExactGrowthMove, ...]:
    """Enumerate inequivalent precursor orbits and exact multiplicities."""

    n = len(relation)
    automorphism_count = len(automorphisms(relation))
    seen: set[int] = set()
    moves: list[ExactGrowthMove] = []
    for precursor in downsets(relation):
        orbit = precursor_orbit(relation, precursor)
        representative = orbit[0]
        if representative in seen:
            continue
        seen.update(orbit)
        target = canonicalize(add_maximal(relation, representative))
        precursor_vertices = tuple(
            vertex for vertex in range(n) if representative & (1 << vertex)
        )
        spectator_vertices = tuple(
            vertex for vertex in range(n) if not representative & (1 << vertex)
        )
        maximal_count = len(
            maximal_elements_in_subset(relation, representative)
        )
        if representative == 0:
            move_class = "GREGARIOUS"
        elif representative == (1 << n) - 1:
            move_class = "TIMID"
        else:
            move_class = (
                f"PRECURSOR_{len(precursor_vertices)}_MAXIMAL_{maximal_count}"
            )
        orbit_size = len(orbit)
        stabilizer_order = automorphism_count // orbit_size
        moves.append(
            ExactGrowthMove(
                source_history=causet_id(relation),
                target_history=causet_id(target),
                precursor_set=precursor_vertices,
                spectator_set=spectator_vertices,
                multiplicity=orbit_size,
                automorphism_factor=Fraction(orbit_size, automorphism_count),
                stabilizer_order=stabilizer_order,
                move_class=move_class,
            )
        )
    return tuple(
        sorted(
            moves,
            key=lambda move: (
                move.target_history,
                len(move.precursor_set),
                move.precursor_set,
            ),
        )
    )


@cache
def enumerate_unlabeled_posets(max_n: int) -> tuple[tuple[Relation, ...], ...]:
    """Grow all non-isomorphic finite posets through ``max_n``."""

    if max_n < 0:
        raise ValueError("max_n must be non-negative")
    levels: list[tuple[Relation, ...]] = [((),)]
    for _n in range(max_n):
        next_level: dict[int, Relation] = {}
        for source in levels[-1]:
            for precursor in downsets(source):
                target = canonicalize(add_maximal(source, precursor))
                next_level[canonical_code(target)] = target
        levels.append(tuple(next_level[code] for code in sorted(next_level)))
    return tuple(levels)


def brute_force_unlabeled_posets(n: int) -> tuple[Relation, ...]:
    """Independent small-n oracle based on all forward relation masks."""

    if n > 4:
        raise ValueError("the independent brute-force oracle is limited to n <= 4")
    pairs = tuple(itertools.combinations(range(n), 2))
    found: dict[int, Relation] = {}
    for mask in range(1 << len(pairs)):
        rows = [0] * n
        for index, (lower, upper) in enumerate(pairs):
            if mask & (1 << index):
                rows[lower] |= 1 << upper
        relation = tuple(rows)
        if validate_relation(relation):
            continue
        canonical = canonicalize(relation)
        found[canonical_code(canonical)] = canonical
    return tuple(found[code] for code in sorted(found))


def interval_abundances(relation: Relation) -> tuple[int, ...]:
    """Count comparable pairs by open-interval cardinality."""

    n = len(relation)
    counts = [0] * max(1, n - 1)
    for lower in range(n):
        for upper in range(n):
            if not has_relation(relation, lower, upper):
                continue
            between = sum(
                has_relation(relation, lower, middle)
                and has_relation(relation, middle, upper)
                for middle in range(n)
            )
            counts[between] += 1
    while len(counts) > 1 and counts[-1] == 0:
        counts.pop()
    return tuple(counts)


def comparable_pairs(relation: Relation) -> int:
    return sum(row.bit_count() for row in relation)


def link_count(relation: Relation) -> int:
    """Count cover relations."""

    n = len(relation)
    result = 0
    for lower in range(n):
        for upper in range(n):
            if not has_relation(relation, lower, upper):
                continue
            if not any(
                has_relation(relation, lower, middle)
                and has_relation(relation, middle, upper)
                for middle in range(n)
            ):
                result += 1
    return result


def diamond_count(relation: Relation) -> int:
    """Count four-element diamond intervals."""

    n = len(relation)
    result = 0
    for lower in range(n):
        for upper in range(n):
            if not has_relation(relation, lower, upper):
                continue
            middle = [
                vertex
                for vertex in range(n)
                if has_relation(relation, lower, vertex)
                and has_relation(relation, vertex, upper)
            ]
            if len(middle) == 2 and not (
                has_relation(relation, middle[0], middle[1])
                or has_relation(relation, middle[1], middle[0])
            ):
                result += 1
    return result


def _is_chain(relation: Relation, vertices: Iterable[int]) -> bool:
    selected = tuple(vertices)
    return all(
        lower == upper
        or has_relation(relation, lower, upper)
        or has_relation(relation, upper, lower)
        for lower in selected
        for upper in selected
    )


def _is_antichain(relation: Relation, vertices: Iterable[int]) -> bool:
    selected = tuple(vertices)
    return all(
        lower == upper
        or (
            not has_relation(relation, lower, upper)
            and not has_relation(relation, upper, lower)
        )
        for lower in selected
        for upper in selected
    )


def height(relation: Relation) -> int:
    """Return the maximum chain cardinality."""

    n = len(relation)
    return max(
        (
            subset.bit_count()
            for subset in range(1 << n)
            if _is_chain(
                relation,
                (vertex for vertex in range(n) if subset & (1 << vertex)),
            )
        ),
        default=0,
    )


def width(relation: Relation) -> int:
    """Return the maximum antichain cardinality."""

    n = len(relation)
    return max(
        (
            subset.bit_count()
            for subset in range(1 << n)
            if _is_antichain(
                relation,
                (vertex for vertex in range(n) if subset & (1 << vertex)),
            )
        ),
        default=0,
    )


def finite_causet_record(relation: Relation) -> dict[str, object]:
    """Build the required FiniteCausalHistory record."""

    return {
        "unlabeled_causal_set": causet_id(relation),
        "cardinality": len(relation),
        "canonical_relation_rows": list(relation),
        "automorphism_group": {
            "order": len(automorphisms(relation)),
            "permutations": [list(item) for item in automorphisms(relation)],
        },
        "natural_labeling_multiplicity": natural_labeling_multiplicity(relation),
        "interval_abundances": list(interval_abundances(relation)),
        "quantum_state_space": {
            "construction": "one orthonormal history basis ray",
            "basis_dimension": 1,
        },
        "evidence": {
            "method": "exhaustive permutation canonicalization",
            "arithmetic": "exact integer",
        },
    }


def enumeration_audit(max_n: int = 5) -> dict[str, object]:
    """Return production/oracle agreement and known-count certificates."""

    levels = enumerate_unlabeled_posets(max_n)
    counts = {str(n): len(level) for n, level in enumerate(levels)}
    known_count_pass = all(
        len(levels[n]) == expected
        for n, expected in KNOWN_UNLABELED_POSET_COUNTS.items()
        if n <= max_n
    )
    oracle_checks = {}
    for n in range(min(max_n, 4) + 1):
        production_codes = {canonical_code(item) for item in levels[n]}
        oracle_codes = {
            canonical_code(item) for item in brute_force_unlabeled_posets(n)
        }
        oracle_checks[str(n)] = {
            "production_count": len(production_codes),
            "oracle_count": len(oracle_codes),
            "exact_set_match": production_codes == oracle_codes,
        }
    transition_count = sum(
        len(growth_moves(relation))
        for level in levels[:-1]
        for relation in level
    )
    return {
        "max_n": max_n,
        "counts": counts,
        "known_count_certificate": known_count_pass,
        "independent_oracle": oracle_checks,
        "transition_orbit_count": transition_count,
        "deterministic_ordering": True,
        "arithmetic": "exact integer and Fraction",
        "resource_status": "EXACT_COMPLETE_WITHIN_DECLARED_DOMAIN",
        "passed": known_count_pass
        and all(check["exact_set_match"] for check in oracle_checks.values()),
    }
