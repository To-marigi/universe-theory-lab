"""Exact naturally birth-labeled sampler and independent replay for Phase B.

This module implements only the control-gated sampler path.  It never calls
the finite unlabeled generator, factorial canonicalization, or an approximate
fallback.  The primary and replay implementations intentionally enumerate
the same exact down-sets by different algorithms and are compared before any
control measurement is promoted.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

from universe_lab.final_theory.causal_sets import Relation, validate_relation
from universe_lab.final_theory.dynamics_v02 import (
    CANDIDATE_PROFILE,
    RANDOM_CONTROL_PROFILE,
)
from universe_lab.final_theory.phase_b_large_n_runtime_v042 import (
    DownsetEnumerationLimit,
    draw_integer_ticket,
    height_longest_path,
    integer_ticket_weights,
    iter_downsets_limited,
)

SamplerImplementation = Literal["primary", "independent"]
ProfileId = Literal[
    "causal_information_v2_sparse_kraus",
    "random_growth_control",
]

MAX_N = 60
RELATION_WIRE_DOMAIN = b"universe-lab/v0.4.2/phase-b-relation-wire\0"
TRAJECTORY_DIGEST_DOMAIN = b"universe-lab/v0.4.2/phase-b-trajectory\0"


@dataclass(frozen=True)
class BranchRecord:
    precursor: int
    target: Relation
    weight: Fraction


@dataclass(frozen=True)
class TicketRecord:
    ticket: int
    rejection_attempt: int
    total_weight: int


@dataclass(frozen=True)
class Trajectory:
    profile_id: str
    sampling_seed: int
    trajectory_index: int
    relations: tuple[Relation, ...]
    precursors: tuple[int, ...]
    tickets: tuple[TicketRecord, ...]

    @property
    def relation_digests(self) -> tuple[str, ...]:
        return tuple(relation_digest(relation) for relation in self.relations)

    @property
    def semantic_digest(self) -> str:
        return trajectory_digest(self.relation_digests)


def _require_natural_relation(relation: Relation) -> None:
    if len(relation) > MAX_N:
        raise ValueError(f"relation cardinality exceeds {MAX_N}")
    errors = validate_relation(relation)
    if errors:
        raise ValueError("; ".join(errors))
    for lower, row in enumerate(relation):
        if row & ((1 << (lower + 1)) - 1):
            raise ValueError("natural birth labels require edges only to later labels")


def _append_maximal_primary(relation: Relation, precursor: int) -> Relation:
    n = len(relation)
    if precursor < 0 or precursor >= 1 << n:
        raise ValueError("precursor is outside the source vertex set")
    rows = list(relation) + [0]
    for predecessor in range(n):
        if precursor & (1 << predecessor):
            rows[predecessor] |= 1 << n
    grown = tuple(rows)
    errors = validate_relation(grown)
    if errors:
        raise ValueError("; ".join(errors))
    return grown


def _append_maximal_replay(relation: Relation, precursor: int) -> Relation:
    size = len(relation)
    if precursor >> size:
        raise ValueError("replay precursor contains an out-of-range vertex")
    new_rows = [row for row in relation]
    new_vertex = 1 << size
    for vertex, row in enumerate(relation):
        if precursor & (1 << vertex):
            new_rows[vertex] = row | new_vertex
    new_rows.append(0)
    grown = tuple(new_rows)
    if validate_relation(grown):
        raise ValueError("independent replay produced an invalid relation")
    return grown


def _link_count_primary(relation: Relation) -> int:
    result = 0
    for lower, row in enumerate(relation):
        for upper in range(len(relation)):
            if not row & (1 << upper):
                continue
            if not any(
                relation[lower] & (1 << middle)
                and relation[middle] & (1 << upper)
                for middle in range(len(relation))
            ):
                result += 1
    return result


def _link_count_replay(relation: Relation) -> int:
    edges = 0
    for _source, row in enumerate(relation):
        targets = row
        while targets:
            target_bit = targets & -targets
            intermediates = row
            covered = False
            while intermediates:
                middle_bit = intermediates & -intermediates
                middle = middle_bit.bit_length() - 1
                if relation[middle] & target_bit:
                    covered = True
                    break
                intermediates ^= middle_bit
            if not covered:
                edges += 1
            targets ^= target_bit
    return edges


def _diamond_count_primary(relation: Relation) -> int:
    result = 0
    for _lower, row in enumerate(relation):
        for upper in range(len(relation)):
            if not row & (1 << upper):
                continue
            middle = [
                vertex
                for vertex in range(len(relation))
                if row & (1 << vertex) and relation[vertex] & (1 << upper)
            ]
            if len(middle) == 2 and not (
                relation[middle[0]] & (1 << middle[1])
                or relation[middle[1]] & (1 << middle[0])
            ):
                result += 1
    return result


def _diamond_count_replay(relation: Relation) -> int:
    result = 0
    for _lower, row in enumerate(relation):
        upper_bits = row
        while upper_bits:
            upper_bit = upper_bits & -upper_bits
            upper = upper_bit.bit_length() - 1
            middle_bits = row & _predecessor_mask(relation, upper)
            if middle_bits.bit_count() == 2:
                first = middle_bits & -middle_bits
                second = middle_bits ^ first
                first_index = first.bit_length() - 1
                second_index = second.bit_length() - 1
                if not (
                    relation[first_index] & second
                    or relation[second_index] & first
                ):
                    result += 1
            upper_bits ^= upper_bit
    return result


def _predecessor_mask(relation: Relation, vertex: int) -> int:
    mask = 0
    bit = 1 << vertex
    for predecessor, row in enumerate(relation):
        if row & bit:
            mask |= 1 << predecessor
    return mask


def _primary_branches(
    relation: Relation, profile_id: str, max_downsets: int
) -> tuple[BranchRecord, ...]:
    _require_natural_relation(relation)
    precursors = tuple(
        sorted(iter_downsets_limited(relation, max_downsets=max_downsets))
    )
    source_links = _link_count_primary(relation)
    source_diamonds = _diamond_count_primary(relation)
    branches: list[BranchRecord] = []
    for precursor in precursors:
        target = _append_maximal_primary(relation, precursor)
        if profile_id == CANDIDATE_PROFILE.profile_id:
            weight = (
                Fraction(2, 3) ** (_link_count_primary(target) - source_links)
                * Fraction(3, 2)
                ** (_diamond_count_primary(target) - source_diamonds)
                * Fraction(4, 5) ** precursor.bit_count()
            )
        elif profile_id == RANDOM_CONTROL_PROFILE.profile_id:
            weight = Fraction(1)
        else:
            raise ValueError(f"unsupported sampler profile: {profile_id}")
        if weight <= 0:
            raise ValueError("branch weights must be positive")
        branches.append(BranchRecord(precursor, target, weight))
    return tuple(branches)


def _frontier_ideals(
    relation: Relation, *, max_downsets: int
) -> Iterator[int]:
    """Enumerate natural-label ideals by scanning a birth frontier.

    A natural labeling puts every predecessor of vertex i below i.  At each
    frontier position we therefore have exactly two legal choices: exclude i,
    or include i after all predecessors are already included.  Each ideal has
    one scan path, so no duplicate ideal is produced.
    """

    if type(max_downsets) is not int or max_downsets <= 0:
        raise ValueError("max_downsets must be a positive integer")
    _require_natural_relation(relation)
    predecessors = tuple(_predecessor_mask(relation, vertex) for vertex in range(len(relation)))
    yielded = 0

    def visit(frontier: int, included: int) -> Iterator[int]:
        nonlocal yielded
        if frontier == len(relation):
            if yielded >= max_downsets:
                raise DownsetEnumerationLimit(max_downsets)
            yielded += 1
            yield included
            return
        yield from visit(frontier + 1, included)
        if predecessors[frontier] & ~included == 0:
            yield from visit(frontier + 1, included | (1 << frontier))

    yield from visit(0, 0)


def _replay_branches(
    relation: Relation, profile_id: str, max_downsets: int
) -> tuple[BranchRecord, ...]:
    _require_natural_relation(relation)
    precursors = tuple(sorted(_frontier_ideals(relation, max_downsets=max_downsets)))
    source_links = _link_count_replay(relation)
    source_diamonds = _diamond_count_replay(relation)
    branches: list[BranchRecord] = []
    for precursor in precursors:
        target = _append_maximal_replay(relation, precursor)
        if profile_id == CANDIDATE_PROFILE.profile_id:
            weight = (
                Fraction(2, 3) ** (_link_count_replay(target) - source_links)
                * Fraction(3, 2)
                ** (_diamond_count_replay(target) - source_diamonds)
                * Fraction(4, 5) ** precursor.bit_count()
            )
        elif profile_id == RANDOM_CONTROL_PROFILE.profile_id:
            weight = Fraction(1)
        else:
            raise ValueError(f"unsupported replay profile: {profile_id}")
        if weight <= 0:
            raise ValueError("replay branch weights must be positive")
        branches.append(BranchRecord(precursor, target, weight))
    return tuple(branches)


def _branch_signature(branches: tuple[BranchRecord, ...]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            branch.precursor,
            branch.target,
            branch.weight.numerator,
            branch.weight.denominator,
        )
        for branch in branches
    )


def _select_branch(
    branches: tuple[BranchRecord, ...],
    *,
    sampling_seed: int,
    trajectory_index: int,
    growth_step: int,
) -> tuple[BranchRecord, TicketRecord]:
    weights = integer_ticket_weights(tuple(branch.weight for branch in branches))
    total = sum(weights)
    draw = draw_integer_ticket(
        total,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        growth_step=growth_step,
        ticket_index=0,
    )
    cumulative = 0
    for branch, weight in zip(branches, weights, strict=True):
        cumulative += weight
        if draw.ticket < cumulative:
            return branch, TicketRecord(
                ticket=draw.ticket,
                rejection_attempt=draw.rejection_attempt,
                total_weight=total,
            )
    raise AssertionError("integer ticket fell outside cumulative branch weights")


def sample_trajectory(
    target_n: int,
    *,
    sampling_seed: int,
    trajectory_index: int,
    profile_id: ProfileId = "causal_information_v2_sparse_kraus",
    implementation: SamplerImplementation = "primary",
    max_downsets: int = 4096,
) -> Trajectory:
    """Sample one exact natural-label trajectory under a selected profile."""

    if type(target_n) is not int or not 1 <= target_n <= MAX_N:
        raise ValueError(f"target_n must be in [1, {MAX_N}]")
    if type(sampling_seed) is not int or not 0 <= sampling_seed < 1 << 64:
        raise ValueError("sampling_seed must be an unsigned 64-bit integer")
    if type(trajectory_index) is not int or not 0 <= trajectory_index < 1 << 64:
        raise ValueError("trajectory_index must be an unsigned 64-bit integer")
    relation: Relation = ()
    relations: list[Relation] = [relation]
    precursors: list[int] = []
    tickets: list[TicketRecord] = []
    for growth_step in range(target_n):
        if implementation == "primary":
            branches = _primary_branches(relation, profile_id, max_downsets)
        elif implementation == "independent":
            branches = _replay_branches(relation, profile_id, max_downsets)
        else:
            raise ValueError(f"unsupported sampler implementation: {implementation}")
        branch, ticket = _select_branch(
            branches,
            sampling_seed=sampling_seed,
            trajectory_index=trajectory_index,
            growth_step=growth_step,
        )
        relation = branch.target
        relations.append(relation)
        precursors.append(branch.precursor)
        tickets.append(ticket)
    return Trajectory(
        profile_id=profile_id,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        relations=tuple(relations),
        precursors=tuple(precursors),
        tickets=tuple(tickets),
    )


def relation_digest(relation: Relation) -> str:
    """Hash the natural-label transitive-row wire representation."""

    _require_natural_relation(relation)
    encoded = bytearray(RELATION_WIRE_DOMAIN)
    encoded.extend(struct.pack(">I", len(relation)))
    for row in relation:
        encoded.extend(struct.pack(">Q", row))
    return hashlib.sha256(bytes(encoded)).hexdigest()


def trajectory_digest(relation_digests: tuple[str, ...] | list[str]) -> str:
    encoded = bytearray(TRAJECTORY_DIGEST_DOMAIN)
    for digest in relation_digests:
        if len(digest) != 64:
            raise ValueError("relation digest must be a SHA-256 hex string")
        encoded.extend(bytes.fromhex(digest))
    return hashlib.sha256(bytes(encoded)).hexdigest()


def measure_relation(relation: Relation, *, spectral_steps: int = 0) -> dict[str, Any]:
    """Return deterministic non-candidate observables for one relation."""

    _require_natural_relation(relation)
    n = len(relation)
    comparable = sum(row.bit_count() for row in relation)
    record: dict[str, Any] = {
        "n": n,
        "relation_digest": relation_digest(relation),
        "ordering_fraction": (
            {"numerator": comparable, "denominator": n * (n - 1) // 2}
            if n >= 2
            else None
        ),
        "height": height_longest_path(relation),
    }
    if spectral_steps:
        raise NotImplementedError(
            "spectral production path is not yet frozen; no spectral measurement executed"
        )
    return record


def compare_primary_and_replay(
    target_n: int,
    *,
    sampling_seed: int,
    trajectory_index: int,
    profile_id: ProfileId,
    max_downsets: int,
) -> dict[str, Any]:
    """Compare exact branch signatures and selected trajectory digests."""

    primary = sample_trajectory(
        target_n,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        profile_id=profile_id,
        implementation="primary",
        max_downsets=max_downsets,
    )
    replay = sample_trajectory(
        target_n,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        profile_id=profile_id,
        implementation="independent",
        max_downsets=max_downsets,
    )
    branch_checks = []
    for step, relation in enumerate(primary.relations[:-1]):
        left = _branch_signature(_primary_branches(relation, profile_id, max_downsets))
        right = _branch_signature(_replay_branches(relation, profile_id, max_downsets))
        branch_checks.append({"growth_step": step, "match": left == right})
    return {
        "target_n": target_n,
        "profile_id": profile_id,
        "sampling_seed": sampling_seed,
        "trajectory_index": trajectory_index,
        "branch_checks": branch_checks,
        "all_branch_checks_passed": all(item["match"] for item in branch_checks),
        "primary_trajectory_digest": primary.semantic_digest,
        "replay_trajectory_digest": replay.semantic_digest,
        "trajectory_digests_match": primary.semantic_digest == replay.semantic_digest,
        "new_trajectories": 0,
        "scientific_evidence": False,
    }
