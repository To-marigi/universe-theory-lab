"""Fail-closed runtime primitives for the Phase-B large-N design.

This module contains only deterministic implementation components.  It does
not sample trajectories, enumerate unlabeled causets, or evaluate a production
observable.  The functions are deliberately independent of the finite
unlabeled kernel so they can be tested against that kernel without importing
its factorial canonicalization path.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from math import gcd, lcm

from universe_lab.final_theory.causal_sets import Relation, validate_relation

_UINT64_LIMIT = 1 << 64
_SHA256_BYTES = hashlib.sha256().digest_size
_RNG_DOMAIN = b"universe-lab/v0.4.2/phase-b-labeled-sampler\0"
MAX_COUNTER_BYTES = 1 << 20
MAX_REJECTION_ATTEMPTS = 1 << 20


class DownsetEnumerationLimit(RuntimeError):
    """Raised when an exact down-set enumeration exceeds its hard cap."""

    code = "DOWNSET_ENUMERATION_LIMIT"

    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"{self.code}: exact down-set count exceeds {limit}")


class CounterRngLimit(RuntimeError):
    """Raised when the portable counter stream reaches its safety boundary."""

    code = "COUNTER_STREAM_LIMIT"


def _relation_masks(
    relation: Relation, *, validate: bool
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if validate:
        errors = validate_relation(relation)
        if errors:
            raise ValueError("; ".join(errors))
    n = len(relation)
    allowed = (1 << n) - 1
    if any(row & ~allowed or row & (1 << index) for index, row in enumerate(relation)):
        raise ValueError("relation contains an out-of-range or reflexive edge")
    predecessors = [0] * n
    for lower, row in enumerate(relation):
        upper = row
        while upper:
            bit = upper & -upper
            predecessors[bit.bit_length() - 1] |= 1 << lower
            upper ^= bit
    return tuple(predecessors), tuple(relation)


def height_longest_path(relation: Relation) -> int:
    """Return maximum chain cardinality using an exact O(n^2) dynamic program.

    The relation is a transitive closure and is assumed to be a valid causal
    relation by the large-N runtime contract.  A Kahn ordering is used rather
    than sorting by birth labels, so relabeling does not change the result.  It
    also detects directed cycles without the O(n^3) full relation validator.
    """

    predecessors, _successors = _relation_masks(relation, validate=False)
    if not relation:
        return 0
    remaining = (1 << len(relation)) - 1
    order: list[int] = []
    while remaining:
        ready = tuple(
            vertex
            for vertex in range(len(relation))
            if remaining & (1 << vertex)
            and not predecessors[vertex] & remaining
        )
        if not ready:
            raise ValueError("relation contains a directed cycle")
        order.extend(ready)
        for vertex in ready:
            remaining ^= 1 << vertex
    depths = [1] * len(relation)
    for vertex in order:
        pending = predecessors[vertex]
        best = 0
        while pending:
            bit = pending & -pending
            predecessor = bit.bit_length() - 1
            best = max(best, depths[predecessor])
            pending ^= bit
        depths[vertex] = best + 1 if best else 1
    return max(depths)


def _iter_order_ideal_masks(
    predecessors: tuple[int, ...], successors: tuple[int, ...]
) -> Iterator[int]:
    """Yield every order ideal once, in ascending integer-mask order.

    The recursion decides the highest still-undecided vertex.  Excluding it
    forces all of its successors out; including it forces all predecessors in.
    Those closure operations partition the ideals without visiting non-ideal
    masks, unlike a scan over ``range(1 << n)``.
    """

    n = len(predecessors)
    full = (1 << n) - 1

    def visit(included: int, excluded: int) -> Iterator[int]:
        if included & excluded:
            return
        undecided = full & ~(included | excluded)
        if not undecided:
            yield included
            return
        vertex_bit = 1 << (undecided.bit_length() - 1)
        vertex = vertex_bit.bit_length() - 1

        successor_closure = successors[vertex]
        if not included & successor_closure:
            yield from visit(
                included,
                excluded | vertex_bit | successor_closure,
            )

        predecessor_closure = predecessors[vertex]
        if not excluded & predecessor_closure:
            yield from visit(
                included | vertex_bit | predecessor_closure,
                excluded,
            )

    yield from visit(0, 0)


def iter_downsets_limited(
    relation: Relation, *, max_downsets: int
) -> Iterator[int]:
    """Yield exact down-sets in ascending mask order, then fail closed.

    ``max_downsets`` is a count of yielded ideals, not a scan bound.  If the
    relation has more ideals than the cap, the iterator raises
    :class:`DownsetEnumerationLimit` before yielding the first over-cap ideal.
    """

    if type(max_downsets) is not int or max_downsets <= 0:
        raise ValueError("max_downsets must be a positive integer")
    predecessors, successors = _relation_masks(relation, validate=True)
    yielded = 0
    for subset in _iter_order_ideal_masks(predecessors, successors):
        if yielded >= max_downsets:
            raise DownsetEnumerationLimit(max_downsets)
        yielded += 1
        yield subset


def collect_downsets_limited(
    relation: Relation, *, max_downsets: int
) -> tuple[int, ...]:
    """Collect a complete capped enumeration or return no partial result."""

    return tuple(iter_downsets_limited(relation, max_downsets=max_downsets))


def _exact_fraction(value: Fraction | int) -> Fraction:
    if type(value) is Fraction:
        return value
    if type(value) is int:
        return Fraction(value)
    raise TypeError("ticket weights must be exact Fraction or int values")


def integer_ticket_weights(
    weights: Sequence[Fraction | int],
) -> tuple[int, ...]:
    """Normalize positive exact rational weights to primitive integer tickets."""

    values = tuple(_exact_fraction(value) for value in weights)
    if not values:
        raise ValueError("at least one weight is required")
    if any(value <= 0 for value in values):
        raise ValueError("ticket weights must be positive")
    common_denominator = reduce(lcm, (value.denominator for value in values), 1)
    scaled = tuple(value.numerator * (common_denominator // value.denominator) for value in values)
    common_factor = reduce(gcd, scaled)
    return tuple(value // common_factor for value in scaled)


def _u64_bytes(name: str, value: int) -> bytes:
    if type(value) is not int:
        raise TypeError(f"{name} must be an unsigned 64-bit integer")
    if not 0 <= value < _UINT64_LIMIT:
        raise ValueError(f"{name} must be in [0, 2**64)")
    return struct.pack(">Q", value)


def sha256_counter_bytes(
    *,
    sampling_seed: int,
    trajectory_index: int,
    growth_step: int,
    ticket_index: int,
    rejection_attempt: int,
    byte_count: int,
) -> bytes:
    """Return deterministic counter-stream bytes from the frozen wire format."""

    if type(byte_count) is not int or byte_count <= 0:
        raise ValueError("byte_count must be a positive integer")
    if byte_count > MAX_COUNTER_BYTES:
        raise CounterRngLimit(
            f"{CounterRngLimit.code}: byte_count exceeds {MAX_COUNTER_BYTES}"
        )
    coordinates = b"".join(
        (
            _u64_bytes("sampling_seed", sampling_seed),
            _u64_bytes("trajectory_index", trajectory_index),
            _u64_bytes("growth_step", growth_step),
            _u64_bytes("ticket_index", ticket_index),
            _u64_bytes("rejection_attempt", rejection_attempt),
        )
    )
    block_count = (byte_count + _SHA256_BYTES - 1) // _SHA256_BYTES
    if block_count >= _UINT64_LIMIT:
        raise CounterRngLimit(
            f"{CounterRngLimit.code}: block index exceeds uint64"
        )
    stream = b"".join(
        hashlib.sha256(
            _RNG_DOMAIN + coordinates + _u64_bytes("block_index", block_index)
        ).digest()
        for block_index in range(block_count)
    )
    return stream[:byte_count]


@dataclass(frozen=True)
class TicketDraw:
    """The selected zero-based ticket and the accepted rejection attempt."""

    ticket: int
    rejection_attempt: int


def draw_integer_ticket(
    total_weight: int,
    *,
    sampling_seed: int,
    trajectory_index: int,
    growth_step: int,
    ticket_index: int,
) -> TicketDraw:
    """Draw one unbiased integer ticket using the portable counter stream."""

    if type(total_weight) is not int or total_weight <= 0:
        raise ValueError("total_weight must be a positive integer")
    byte_count = max(1, (total_weight.bit_length() + 7) // 8)
    range_size = 256**byte_count
    cutoff = range_size - (range_size % total_weight)
    rejection_attempt = 0
    while True:
        if rejection_attempt >= MAX_REJECTION_ATTEMPTS:
            raise CounterRngLimit(
                f"{CounterRngLimit.code}: rejection attempts exceed "
                f"{MAX_REJECTION_ATTEMPTS}"
            )
        raw = sha256_counter_bytes(
            sampling_seed=sampling_seed,
            trajectory_index=trajectory_index,
            growth_step=growth_step,
            ticket_index=ticket_index,
            rejection_attempt=rejection_attempt,
            byte_count=byte_count,
        )
        value = int.from_bytes(raw, "big")
        if value < cutoff:
            return TicketDraw(value % total_weight, rejection_attempt)
        rejection_attempt += 1
