"""Exact channel-level diagnostics for Kraus Bell causality.

The v0.2 dynamics stores one basis ray per *unlabeled* causal history and
aggregates labeled precursor moves into automorphism orbits.  That is enough to
construct completely positive finite instruments, but it does not supply a
spectator tensor factor, a partial trace, or a canonical map between the
full- and reduced-history Hilbert spaces.

This module therefore keeps two logically separate results:

* exhaustive, exact Bell-family and probability diagnostics through ``n <= 5``;
* an explicit ``KRAUS_BELL_CAUSALITY_UNDEFINED`` verdict for the missing
  channel-level spectator-reduction definition.

In particular, inverse-based CPOBC is never applied to the singular rank-one
matrix units used by the Kraus growth model.  Map comparisons use exact
probability vectors, superoperators, and Choi data rather than Kraus-list
strings.
"""

from __future__ import annotations

import copy
import itertools
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    automorphisms,
    causet_id,
    diamond_count,
    downsets,
    enumerate_unlabeled_posets,
    growth_moves,
    has_relation,
    link_count,
    precursor_orbit,
)
from universe_lab.final_theory.dynamics_v02 import CANDIDATE_PROFILE

KRAUS_BELL_CAUSALITY_UNDEFINED = "KRAUS_BELL_CAUSALITY_UNDEFINED"
_MAX_EXACT_SOURCE_N = 5


def _profile_fraction(name: str) -> Fraction:
    record = CANDIDATE_PROFILE.parameters[name]
    return Fraction(record["numerator"], record["denominator"])


_LINK_FUGACITY = _profile_fraction("link_fugacity")
_DIAMOND_FUGACITY = _profile_fraction("diamond_fugacity")
_PRECURSOR_FUGACITY = _profile_fraction("precursor_fugacity")


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _matrix_record(
    matrix: tuple[tuple[Fraction, ...], ...],
) -> list[list[dict[str, int]]]:
    return [
        [_fraction_record(value) for value in row]
        for row in matrix
    ]


def _mask(vertices: tuple[int, ...]) -> int:
    result = 0
    for vertex in vertices:
        result |= 1 << vertex
    return result


def _mapped_subset(subset: int, permutation: tuple[int, ...]) -> int:
    result = 0
    for vertex, image in enumerate(permutation):
        if subset & (1 << vertex):
            result |= 1 << image
    return result


def _unordered_pair(first: int, second: int) -> tuple[int, int]:
    return (first, second) if first <= second else (second, first)


def _relabel_relation(
    relation: Relation,
    permutation: tuple[int, ...],
) -> Relation:
    """Relabel a relation using an old-index to new-index permutation."""

    n = len(relation)
    if sorted(permutation) != list(range(n)):
        raise ValueError("permutation must contain every vertex exactly once")
    rows = [0] * n
    for old_lower in range(n):
        for old_upper in range(n):
            if has_relation(relation, old_lower, old_upper):
                rows[permutation[old_lower]] |= 1 << permutation[old_upper]
    return tuple(rows)


@cache
def _candidate_local_weight(relation: Relation, precursor: int) -> Fraction:
    """Return the exact per-labeled-precursor weight of the v0.2 candidate."""

    target = add_maximal(relation, precursor)
    delta_links = link_count(target) - link_count(relation)
    delta_diamonds = diamond_count(target) - diamond_count(relation)
    if delta_links < 0 or delta_diamonds < 0:
        raise AssertionError("maximal growth removed an order invariant")
    return (
        _LINK_FUGACITY**delta_links
        * _DIAMOND_FUGACITY**delta_diamonds
        * _PRECURSOR_FUGACITY**precursor.bit_count()
    )


@cache
def _source_normalization(relation: Relation) -> Fraction:
    return sum(
        (_candidate_local_weight(relation, precursor) for precursor in downsets(relation)),
        start=Fraction(0),
    )


@cache
def _orbit_representative(relation: Relation, precursor: int) -> int:
    return min(precursor_orbit(relation, precursor))


@cache
def _orbit_size(relation: Relation, precursor: int) -> int:
    return len(precursor_orbit(relation, precursor))


@dataclass(frozen=True)
class _BranchData:
    precursor: int
    target_history: str
    move_class: str
    multiplicity: int
    stabilizer_order: int
    automorphism_factor: Fraction
    local_weight: Fraction
    probability: Fraction


@dataclass(frozen=True)
class _SourceData:
    relation: Relation
    source_history: str
    normalization: Fraction
    branches: tuple[_BranchData, ...]


@cache
def _source_data(relation: Relation) -> _SourceData:
    normalization = _source_normalization(relation)
    if normalization <= 0:
        raise AssertionError("candidate instrument normalization is not positive")
    branches: list[_BranchData] = []
    for move in growth_moves(relation):
        precursor = _mask(move.precursor_set)
        local_weight = _candidate_local_weight(relation, precursor)
        probability = move.multiplicity * local_weight / normalization
        branches.append(
            _BranchData(
                precursor=precursor,
                target_history=move.target_history,
                move_class=move.move_class,
                multiplicity=move.multiplicity,
                stabilizer_order=move.stabilizer_order,
                automorphism_factor=move.automorphism_factor,
                local_weight=local_weight,
                probability=probability,
            )
        )
    if sum((branch.probability for branch in branches), Fraction(0)) != 1:
        raise AssertionError("exact instrument completeness failed")
    return _SourceData(
        relation=relation,
        source_history=causet_id(relation),
        normalization=normalization,
        branches=tuple(branches),
    )


def _outcome_id(source: _SourceData, branch: _BranchData) -> str:
    width = max(1, (len(source.relation) + 3) // 4)
    return (
        f"{source.source_history}->{branch.target_history}"
        f"@precursor-{branch.precursor:0{width}x}"
    )


def _diagonal_map_record(
    basis: list[str],
    diagonal: list[Fraction],
) -> dict[str, Any]:
    dimension = len(basis)
    return {
        "basis": basis,
        "probability_vector": [_fraction_record(value) for value in diagonal],
        "choi": {
            "shape": [dimension, dimension],
            "representation": "exact diagonal",
            "diagonal": [_fraction_record(value) for value in diagonal],
        },
        "superoperator": {
            "shape": [dimension * dimension, 1],
            "vectorization": "column-major",
            "nonzero_entries": [
                {
                    "row": index * (dimension + 1),
                    "column": 0,
                    "value": _fraction_record(value),
                }
                for index, value in enumerate(diagonal)
                if value
            ],
        },
    }


def _source_certificate(source: _SourceData) -> dict[str, Any]:
    branch_basis = [_outcome_id(source, branch) for branch in source.branches]
    branch_probabilities = [branch.probability for branch in source.branches]
    target_probabilities: dict[str, Fraction] = defaultdict(Fraction)
    for branch in source.branches:
        target_probabilities[branch.target_history] += branch.probability
    target_basis = sorted(target_probabilities)
    target_vector = [target_probabilities[target] for target in target_basis]
    group_order = len(automorphisms(source.relation))
    return {
        "source_history": source.source_history,
        "source_size": len(source.relation),
        "source_automorphism_order": group_order,
        "normalization": _fraction_record(source.normalization),
        "instrument_outcomes": [
            {
                "outcome_id": outcome,
                "target_history": branch.target_history,
                "precursor_size": branch.precursor.bit_count(),
                "precursor_mask": branch.precursor,
                "move_class": branch.move_class,
                "orbit_multiplicity": branch.multiplicity,
                "stabilizer_order": branch.stabilizer_order,
                "automorphism_factor": _fraction_record(
                    branch.automorphism_factor
                ),
                "local_weight": _fraction_record(branch.local_weight),
                "probability": _fraction_record(branch.probability),
                "outcome_choi": {
                    "shape": [1, 1],
                    "entries": [[_fraction_record(branch.probability)]],
                },
                "outcome_superoperator": {
                    "shape": [1, 1],
                    "entries": [[_fraction_record(branch.probability)]],
                },
                "completely_positive": branch.probability >= 0,
                "trace_nonincreasing": Fraction(0) <= branch.probability <= 1,
            }
            for outcome, branch in zip(
                branch_basis,
                source.branches,
                strict=True,
            )
        ],
        "instrument_map": {
            **_diagonal_map_record(branch_basis, branch_probabilities),
            "interpretation": (
                "classical move-record outcome register used by the implemented "
                "finite instrument schema"
            ),
            "trace_preserving": sum(branch_probabilities, Fraction(0)) == 1,
        },
        "history_channel": {
            **_diagonal_map_record(target_basis, target_vector),
            "interpretation": (
                "branches with the same unlabeled target ray are summed; no "
                "Kraus-list identity is used"
            ),
            "trace_preserving": sum(target_vector, Fraction(0)) == 1,
        },
    }


def _induced_subrelation(
    relation: Relation,
    keep: int,
) -> tuple[Relation, tuple[int, ...]]:
    vertices = tuple(
        vertex for vertex in range(len(relation)) if keep & (1 << vertex)
    )
    old_to_new = [-1] * len(relation)
    for new, old in enumerate(vertices):
        old_to_new[old] = new
    rows: list[int] = []
    for old_lower in vertices:
        row = 0
        for old_upper in vertices:
            if has_relation(relation, old_lower, old_upper):
                row |= 1 << old_to_new[old_upper]
        rows.append(row)
    return tuple(rows), tuple(old_to_new)


def _compress_subset(subset: int, old_to_new: tuple[int, ...]) -> int:
    result = 0
    for old, new in enumerate(old_to_new):
        if new >= 0 and subset & (1 << old):
            result |= 1 << new
    return result


@cache
def _pair_orbit(
    relation: Relation,
    first: int,
    second: int,
) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted(
            {
                _unordered_pair(
                    _mapped_subset(first, permutation),
                    _mapped_subset(second, permutation),
                )
                for permutation in automorphisms(relation)
            }
        )
    )


def _relation_code_under_relabeling(
    relation: Relation,
    permutation: tuple[int, ...],
) -> int:
    n = len(relation)
    result = 0
    for old_lower in range(n):
        for old_upper in range(n):
            if has_relation(relation, old_lower, old_upper):
                result |= 1 << (
                    permutation[old_lower] * n + permutation[old_upper]
                )
    return result


@cache
def _colored_pair_signature(
    relation: Relation,
    first: int,
    second: int,
) -> tuple[int, int, int, int]:
    """Canonicalize an unlabeled parent with an unordered precursor pair."""

    n = len(relation)
    candidates = []
    for permutation in itertools.permutations(range(n)):
        mapped_first, mapped_second = sorted(
            (
                _mapped_subset(first, permutation),
                _mapped_subset(second, permutation),
            )
        )
        candidates.append(
            (
                _relation_code_under_relabeling(relation, permutation),
                mapped_first,
                mapped_second,
            )
        )
    relation_code, mapped_first, mapped_second = min(candidates)
    return n, relation_code, mapped_first, mapped_second


def _family_id(signature: tuple[int, int, int, int]) -> str:
    n, relation_code, first, second = signature
    relation_width = max(1, (n * n + 3) // 4)
    subset_width = max(1, (n + 3) // 4)
    return (
        f"kb{n}-{relation_code:0{relation_width}x}-"
        f"{first:0{subset_width}x}-{second:0{subset_width}x}"
    )


def _scalar_product_comparison(
    left: Fraction,
    right: Fraction,
) -> dict[str, Any]:
    return {
        "left_probability": _fraction_record(left),
        "right_probability": _fraction_record(right),
        "probability_equal": left == right,
        "superoperators": {
            "left": [[_fraction_record(left)]],
            "right": [[_fraction_record(right)]],
            "exactly_equal": left == right,
        },
        "choi_matrices": {
            "left": [[_fraction_record(left)]],
            "right": [[_fraction_record(right)]],
            "exactly_equal": left == right,
        },
    }


def _probability_witness(
    *,
    relation: Relation,
    first: int,
    second: int,
    reduced: Relation,
    reduced_first: int,
    reduced_second: int,
    family_id: str,
) -> dict[str, Any]:
    full_normalization = _source_normalization(relation)
    reduced_normalization = _source_normalization(reduced)
    full_local_first = _candidate_local_weight(relation, first) / full_normalization
    full_local_second = (
        _candidate_local_weight(relation, second) / full_normalization
    )
    reduced_local_first = (
        _candidate_local_weight(reduced, reduced_first) / reduced_normalization
    )
    reduced_local_second = (
        _candidate_local_weight(reduced, reduced_second) / reduced_normalization
    )
    full_first_multiplicity = _orbit_size(relation, first)
    full_second_multiplicity = _orbit_size(relation, second)
    reduced_first_multiplicity = _orbit_size(reduced, reduced_first)
    reduced_second_multiplicity = _orbit_size(reduced, reduced_second)
    full_aggregate_first = full_first_multiplicity * full_local_first
    full_aggregate_second = full_second_multiplicity * full_local_second
    reduced_aggregate_first = reduced_first_multiplicity * reduced_local_first
    reduced_aggregate_second = reduced_second_multiplicity * reduced_local_second
    local_left = full_local_first * reduced_local_second
    local_right = full_local_second * reduced_local_first
    aggregate_left = full_aggregate_first * reduced_aggregate_second
    aggregate_right = full_aggregate_second * reduced_aggregate_first
    return {
        "family_id": family_id,
        "full_source": causet_id(relation),
        "reduced_source": causet_id(reduced),
        "full_source_size": len(relation),
        "reduced_source_size": len(reduced),
        "ordered_precursor_sizes": [
            first.bit_count(),
            second.bit_count(),
        ],
        "full_precursors": [
            [vertex for vertex in range(len(relation)) if first & (1 << vertex)],
            [vertex for vertex in range(len(relation)) if second & (1 << vertex)],
        ],
        "reduced_precursors": [
            [
                vertex
                for vertex in range(len(reduced))
                if reduced_first & (1 << vertex)
            ],
            [
                vertex
                for vertex in range(len(reduced))
                if reduced_second & (1 << vertex)
            ],
        ],
        "normalizations": {
            "full": _fraction_record(full_normalization),
            "reduced": _fraction_record(reduced_normalization),
        },
        "per_labeled_precursor_probabilities": {
            "full": [
                _fraction_record(full_local_first),
                _fraction_record(full_local_second),
            ],
            "reduced": [
                _fraction_record(reduced_local_first),
                _fraction_record(reduced_local_second),
            ],
        },
        "orbit_multiplicities": {
            "full": [full_first_multiplicity, full_second_multiplicity],
            "reduced": [
                reduced_first_multiplicity,
                reduced_second_multiplicity,
            ],
        },
        "orbit_aggregate_instrument_probabilities": {
            "full": [
                _fraction_record(full_aggregate_first),
                _fraction_record(full_aggregate_second),
            ],
            "reduced": [
                _fraction_record(reduced_aggregate_first),
                _fraction_record(reduced_aggregate_second),
            ],
        },
        "per_labeled_precursor_product_map": _scalar_product_comparison(
            local_left,
            local_right,
        ),
        "orbit_aggregate_product_map": _scalar_product_comparison(
            aggregate_left,
            aggregate_right,
        ),
        "absolute_probabilities_change": (
            full_local_first != reduced_local_first
            or full_local_second != reduced_local_second
        ),
        "claim_boundary": (
            "The aggregate inequality is an exact counterexample to a naive "
            "orbit-outcome probability-product test. It is not a QBC failure "
            "certificate because the required spectator reduction of Hilbert "
            "spaces and outcome algebras is not defined."
        ),
    }


def _zero_matrix(rows: int, columns: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _column in range(columns)] for _row in range(rows)]


def _choi_from_kraus(
    kraus: tuple[tuple[tuple[Fraction, ...], ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    output_dimension = len(kraus[0])
    input_dimension = len(kraus[0][0])
    dimension = output_dimension * input_dimension
    result = _zero_matrix(dimension, dimension)
    for operator in kraus:
        vector = [
            operator[row][column]
            for column in range(input_dimension)
            for row in range(output_dimension)
        ]
        for row in range(dimension):
            for column in range(dimension):
                result[row][column] += vector[row] * vector[column]
    return tuple(tuple(row) for row in result)


def _superoperator_from_kraus(
    kraus: tuple[tuple[tuple[Fraction, ...], ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    output_dimension = len(kraus[0])
    input_dimension = len(kraus[0][0])
    result = _zero_matrix(
        output_dimension * output_dimension,
        input_dimension * input_dimension,
    )
    for operator in kraus:
        for input_row in range(input_dimension):
            for input_column in range(input_dimension):
                source_index = input_row + input_column * input_dimension
                for output_row in range(output_dimension):
                    for output_column in range(output_dimension):
                        target_index = (
                            output_row + output_column * output_dimension
                        )
                        result[target_index][source_index] += (
                            operator[output_row][input_row]
                            * operator[output_column][input_column]
                        )
    return tuple(tuple(row) for row in result)


def _kraus_effect(
    kraus: tuple[tuple[tuple[Fraction, ...], ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    input_dimension = len(kraus[0][0])
    output_dimension = len(kraus[0])
    result = _zero_matrix(input_dimension, input_dimension)
    for operator in kraus:
        for row in range(input_dimension):
            for column in range(input_dimension):
                result[row][column] += sum(
                    operator[output][row] * operator[output][column]
                    for output in range(output_dimension)
                )
    return tuple(tuple(row) for row in result)


def _kraus_basis_invariance_audit() -> dict[str, Any]:
    zero = Fraction(0)
    one = Fraction(1)
    standard = (
        ((one, zero), (zero, zero)),
        ((zero, zero), (zero, one)),
    )
    rotated = (
        ((Fraction(3, 5), zero), (zero, Fraction(4, 5))),
        ((Fraction(-4, 5), zero), (zero, Fraction(3, 5))),
    )
    standard_choi = _choi_from_kraus(standard)
    rotated_choi = _choi_from_kraus(rotated)
    standard_superoperator = _superoperator_from_kraus(standard)
    rotated_superoperator = _superoperator_from_kraus(rotated)
    standard_effect = _kraus_effect(standard)
    rotated_effect = _kraus_effect(rotated)
    identity = ((one, zero), (zero, one))
    return {
        "control_channel": "qubit complete dephasing",
        "basis_change": (
            "exact orthogonal 3-4-5 rotation of the two Kraus operators"
        ),
        "standard_kraus": [
            _matrix_record(operator) for operator in standard
        ],
        "rotated_kraus": [
            _matrix_record(operator) for operator in rotated
        ],
        "kraus_lists_equal": standard == rotated,
        "choi": {
            "standard": _matrix_record(standard_choi),
            "rotated": _matrix_record(rotated_choi),
            "exactly_equal": standard_choi == rotated_choi,
        },
        "superoperator": {
            "standard": _matrix_record(standard_superoperator),
            "rotated": _matrix_record(rotated_superoperator),
            "exactly_equal": standard_superoperator == rotated_superoperator,
        },
        "trace_preservation_effect": {
            "standard": _matrix_record(standard_effect),
            "rotated": _matrix_record(rotated_effect),
            "both_identity": standard_effect == identity
            and rotated_effect == identity,
        },
        "false_kraus_string_test_detected": (
            standard != rotated
            and standard_choi == rotated_choi
            and standard_superoperator == rotated_superoperator
        ),
        "candidate_comparison_rule": (
            "compare instruments by labeled CP outcome maps and channels by "
            "their exact superoperators/Choi matrices, never by a Kraus list"
        ),
    }


def _relabel_covariance_audit(
    levels: tuple[tuple[Relation, ...], ...],
) -> dict[str, Any]:
    generator_checks = 0
    precursor_checks = 0
    failures: list[dict[str, Any]] = []
    for level in levels:
        for relation in level:
            n = len(relation)
            for adjacent in range(n - 1):
                permutation_list = list(range(n))
                permutation_list[adjacent], permutation_list[adjacent + 1] = (
                    permutation_list[adjacent + 1],
                    permutation_list[adjacent],
                )
                permutation = tuple(permutation_list)
                relabeled = _relabel_relation(relation, permutation)
                generator_checks += 1
                generator_pass = (
                    causet_id(relabeled) == causet_id(relation)
                    and _source_normalization(relabeled)
                    == _source_normalization(relation)
                )
                for precursor in downsets(relation):
                    precursor_checks += 1
                    mapped_precursor = _mapped_subset(precursor, permutation)
                    original_target = add_maximal(relation, precursor)
                    extended_permutation = (*permutation, n)
                    relabeled_target = _relabel_relation(
                        original_target,
                        extended_permutation,
                    )
                    expected_target = add_maximal(
                        relabeled,
                        mapped_precursor,
                    )
                    precursor_pass = (
                        mapped_precursor in downsets(relabeled)
                        and _candidate_local_weight(relation, precursor)
                        == _candidate_local_weight(
                            relabeled,
                            mapped_precursor,
                        )
                        and _orbit_size(relation, precursor)
                        == _orbit_size(relabeled, mapped_precursor)
                        and relabeled_target == expected_target
                    )
                    generator_pass &= precursor_pass
                if not generator_pass and len(failures) < 10:
                    failures.append(
                        {
                            "source_history": causet_id(relation),
                            "adjacent_transposition": [
                                adjacent,
                                adjacent + 1,
                            ],
                        }
                    )
    return {
        "history_count": sum(len(level) for level in levels),
        "generator_set": "all adjacent transpositions at every source",
        "adjacent_transposition_checks": generator_checks,
        "precursor_checks": precursor_checks,
        "transition_law_covariant": not failures,
        "family_signature_method": (
            "colored precursor pairs minimized over every vertex permutation"
        ),
        "family_signatures_relabel_covariant_by_construction": True,
        "failures": failures,
    }


def _omission_mutation(
    sources: list[_SourceData],
) -> tuple[dict[str, Any], bool]:
    factor_equivalence = True
    witness: dict[str, Any] | None = None
    for source in sources:
        group_order = len(automorphisms(source.relation))
        factor_normalization = sum(
            (
                branch.automorphism_factor * branch.local_weight
                for branch in source.branches
            ),
            start=Fraction(0),
        )
        factor_probabilities = [
            branch.automorphism_factor
            * branch.local_weight
            / factor_normalization
            for branch in source.branches
        ]
        correct_probabilities = [
            branch.probability for branch in source.branches
        ]
        factor_equivalence &= factor_probabilities == correct_probabilities

        omitted_normalization = sum(
            (branch.local_weight for branch in source.branches),
            start=Fraction(0),
        )
        omitted_probabilities = [
            branch.local_weight / omitted_normalization
            for branch in source.branches
        ]
        if witness is None and omitted_probabilities != correct_probabilities:
            basis = [_outcome_id(source, branch) for branch in source.branches]
            witness = {
                "source_history": source.source_history,
                "source_size": len(source.relation),
                "automorphism_group_order": group_order,
                "outcome_basis": basis,
                "correct_orbit_probability_vector": [
                    _fraction_record(value) for value in correct_probabilities
                ],
                "omitted_factor_probability_vector": [
                    _fraction_record(value) for value in omitted_probabilities
                ],
                "correct_map": _diagonal_map_record(
                    basis,
                    correct_probabilities,
                ),
                "omitted_map": _diagonal_map_record(
                    basis,
                    omitted_probabilities,
                ),
                "probability_vectors_equal": False,
                "choi_matrices_equal": False,
                "superoperators_equal": False,
            }
    return (
        {
            "mutation": (
                "replace orbit-size/automorphism-factor weighting by one "
                "unweighted representative per precursor orbit"
            ),
            "detected": witness is not None,
            "first_exact_witness": witness,
            "correct_orbit_size_and_automorphism_factor_normalizations_agree": (
                factor_equivalence
            ),
        },
        factor_equivalence,
    )


def _new_family_accumulator(
    family_id: str,
    reduced: Relation,
    reduced_first: int,
    reduced_second: int,
) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "base_source_history": causet_id(reduced),
        "base_source_size": len(reduced),
        "precursor_sizes": sorted(
            [reduced_first.bit_count(), reduced_second.bit_count()],
            reverse=True,
        ),
        "equal_precursor_size": (
            reduced_first.bit_count() == reduced_second.bit_count()
        ),
        "occurrence_count": 0,
        "base_occurrence_count": 0,
        "nontrivial_spectator_occurrence_count": 0,
        "aggregate_product_violation_count": 0,
        "reduced_outcome_collision_count": 0,
        "full_source_sizes": set(),
        "common_spectator_sizes": set(),
    }


def _finalize_family(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **{
            key: value
            for key, value in record.items()
            if key not in {"full_source_sizes", "common_spectator_sizes"}
        },
        "full_source_sizes": sorted(record["full_source_sizes"]),
        "common_spectator_sizes": sorted(record["common_spectator_sizes"]),
    }


@cache
def _benchmark_cached(max_n: int) -> dict[str, Any]:
    levels = enumerate_unlabeled_posets(max_n)
    sources = [
        _source_data(relation)
        for level in levels
        for relation in level
    ]
    source_certificates = [_source_certificate(source) for source in sources]

    channel_cp = True
    instrument_tp = True
    outcome_tni = True
    history_channel_tp = True
    minimum_probability = Fraction(1)
    history_channel_output_count = 0
    for source, certificate in zip(
        sources,
        source_certificates,
        strict=True,
    ):
        probabilities = [branch.probability for branch in source.branches]
        channel_cp &= all(probability >= 0 for probability in probabilities)
        instrument_tp &= sum(probabilities, Fraction(0)) == 1
        outcome_tni &= all(
            Fraction(0) <= probability <= 1
            for probability in probabilities
        )
        history_channel_tp &= certificate["history_channel"][
            "trace_preserving"
        ]
        history_channel_output_count += len(
            certificate["history_channel"]["basis"]
        )
        minimum_probability = min([minimum_probability, *probabilities])

    automorphism_branch_checks = 0
    automorphism_branch_pass = True
    for source in sources:
        group_order = len(automorphisms(source.relation))
        for branch in source.branches:
            automorphism_branch_checks += 1
            orbit_size = _orbit_size(source.relation, branch.precursor)
            automorphism_branch_pass &= (
                branch.precursor
                == _orbit_representative(source.relation, branch.precursor)
                and branch.multiplicity == orbit_size
                and branch.multiplicity * branch.stabilizer_order
                == group_order
                and branch.automorphism_factor
                == Fraction(branch.multiplicity, group_order)
            )

    level_counts: dict[str, dict[str, int]] = {
        str(n): {
            "history_count": len(level),
            "labeled_transition_count": sum(
                len(downsets(relation)) for relation in level
            ),
            "transition_orbit_count": sum(
                len(growth_moves(relation)) for relation in level
            ),
            "distinct_branch_pair_configuration_count": 0,
            "base_pair_count": 0,
            "nontrivial_spectator_configuration_count": 0,
            "all_configuration_strict_precursor_size_count": 0,
            "all_configuration_equal_precursor_size_count": 0,
            "strict_precursor_size_order_count": 0,
            "equal_precursor_size_count": 0,
            "aggregate_probability_product_violation_count": 0,
            "reduced_outcome_collision_count": 0,
        }
        for n, level in enumerate(levels)
    }

    families: dict[str, dict[str, Any]] = {}
    alignment_variants: dict[
        tuple[str, int, int],
        dict[str, Any],
    ] = {}
    pair_orbit_checks = 0
    pair_orbit_pass = True
    local_weight_dependence_violations = 0
    labeled_probability_product_violations = 0
    aggregate_probability_product_violations = 0
    absolute_probability_change_count = 0
    reduced_outcome_collision_count = 0
    first_probability_witness: dict[str, Any] | None = None

    for n, level in enumerate(levels):
        level_record = level_counts[str(n)]
        for relation in level:
            source = _source_data(relation)
            branch_representative = {
                precursor: _orbit_representative(relation, precursor)
                for precursor in downsets(relation)
            }
            branch_by_precursor = {
                branch.precursor: branch for branch in source.branches
            }
            seen_pairs: set[tuple[int, int]] = set()
            for first, second in itertools.combinations(downsets(relation), 2):
                first_branch = branch_representative[first]
                second_branch = branch_representative[second]
                if first_branch == second_branch:
                    continue
                pair_orbit = _pair_orbit(relation, first, second)
                representative = pair_orbit[0]
                if representative in seen_pairs:
                    continue
                seen_pairs.update(pair_orbit)
                first, second = representative
                pair_orbit_checks += 1
                group_order = len(automorphisms(relation))
                pair_multiplicity = len(pair_orbit)
                pair_stabilizer_order = sum(
                    _unordered_pair(
                        _mapped_subset(first, permutation),
                        _mapped_subset(second, permutation),
                    )
                    == representative
                    for permutation in automorphisms(relation)
                )
                pair_orbit_pass &= (
                    pair_multiplicity * pair_stabilizer_order == group_order
                )
                level_record[
                    "distinct_branch_pair_configuration_count"
                ] += 1

                if first.bit_count() < second.bit_count():
                    first, second = second, first
                elif (
                    first.bit_count() == second.bit_count()
                    and first > second
                ):
                    first, second = second, first

                union = first | second
                full_mask = (1 << n) - 1
                common_spectators = full_mask ^ union
                reduced, old_to_new = _induced_subrelation(relation, union)
                reduced_first = _compress_subset(first, old_to_new)
                reduced_second = _compress_subset(second, old_to_new)
                signature = _colored_pair_signature(
                    reduced,
                    reduced_first,
                    reduced_second,
                )
                family_id = _family_id(signature)
                family = families.setdefault(
                    family_id,
                    _new_family_accumulator(
                        family_id,
                        reduced,
                        reduced_first,
                        reduced_second,
                    ),
                )
                family["occurrence_count"] += 1
                family["full_source_sizes"].add(n)
                family["common_spectator_sizes"].add(
                    common_spectators.bit_count()
                )
                if first.bit_count() == second.bit_count():
                    level_record[
                        "all_configuration_equal_precursor_size_count"
                    ] += 1
                else:
                    level_record[
                        "all_configuration_strict_precursor_size_count"
                    ] += 1

                if not common_spectators:
                    level_record["base_pair_count"] += 1
                    family["base_occurrence_count"] += 1
                    continue

                level_record[
                    "nontrivial_spectator_configuration_count"
                ] += 1
                family["nontrivial_spectator_occurrence_count"] += 1
                if first.bit_count() == second.bit_count():
                    level_record["equal_precursor_size_count"] += 1
                else:
                    level_record[
                        "strict_precursor_size_order_count"
                    ] += 1

                full_weight_first = _candidate_local_weight(relation, first)
                full_weight_second = _candidate_local_weight(relation, second)
                reduced_weight_first = _candidate_local_weight(
                    reduced,
                    reduced_first,
                )
                reduced_weight_second = _candidate_local_weight(
                    reduced,
                    reduced_second,
                )
                if (
                    full_weight_first != reduced_weight_first
                    or full_weight_second != reduced_weight_second
                ):
                    local_weight_dependence_violations += 1

                full_local_first = (
                    full_weight_first / _source_normalization(relation)
                )
                full_local_second = (
                    full_weight_second / _source_normalization(relation)
                )
                reduced_local_first = (
                    reduced_weight_first / _source_normalization(reduced)
                )
                reduced_local_second = (
                    reduced_weight_second / _source_normalization(reduced)
                )
                labeled_left = full_local_first * reduced_local_second
                labeled_right = full_local_second * reduced_local_first
                if labeled_left != labeled_right:
                    labeled_probability_product_violations += 1
                if (
                    full_local_first != reduced_local_first
                    or full_local_second != reduced_local_second
                ):
                    absolute_probability_change_count += 1

                full_aggregate_first = (
                    _orbit_size(relation, first) * full_local_first
                )
                full_aggregate_second = (
                    _orbit_size(relation, second) * full_local_second
                )
                reduced_aggregate_first = (
                    _orbit_size(reduced, reduced_first) * reduced_local_first
                )
                reduced_aggregate_second = (
                    _orbit_size(reduced, reduced_second) * reduced_local_second
                )
                aggregate_left = (
                    full_aggregate_first * reduced_aggregate_second
                )
                aggregate_right = (
                    full_aggregate_second * reduced_aggregate_first
                )
                if aggregate_left != aggregate_right:
                    aggregate_probability_product_violations += 1
                    level_record[
                        "aggregate_probability_product_violation_count"
                    ] += 1
                    family["aggregate_product_violation_count"] += 1
                    if first_probability_witness is None:
                        first_probability_witness = _probability_witness(
                            relation=relation,
                            first=first,
                            second=second,
                            reduced=reduced,
                            reduced_first=reduced_first,
                            reduced_second=reduced_second,
                            family_id=family_id,
                        )

                reduced_collision = (
                    _orbit_representative(reduced, reduced_first)
                    == _orbit_representative(reduced, reduced_second)
                )
                if reduced_collision:
                    reduced_outcome_collision_count += 1
                    level_record["reduced_outcome_collision_count"] += 1
                    family["reduced_outcome_collision_count"] += 1

                alignment_key = (
                    source.source_history,
                    min(first_branch, second_branch),
                    max(first_branch, second_branch),
                )
                alignment = alignment_variants.setdefault(
                    alignment_key,
                    {
                        "source_history": source.source_history,
                        "source_size": n,
                        "branch_outcomes": [
                            _outcome_id(
                                source,
                                branch_by_precursor[
                                    min(first_branch, second_branch)
                                ],
                            ),
                            _outcome_id(
                                source,
                                branch_by_precursor[
                                    max(first_branch, second_branch)
                                ],
                            ),
                        ],
                        "configuration_count": 0,
                        "family_ids": set(),
                    },
                )
                alignment["configuration_count"] += 1
                alignment["family_ids"].add(family_id)

    ambiguous_alignments = [
        {
            "source_history": record["source_history"],
            "source_size": record["source_size"],
            "branch_outcomes": record["branch_outcomes"],
            "configuration_count": record["configuration_count"],
            "reduced_family_ids": sorted(record["family_ids"]),
        }
        for _key, record in sorted(alignment_variants.items())
        if record["configuration_count"] > 1
        or len(record["family_ids"]) > 1
    ]
    distinct_reduced_family_ambiguities = [
        record
        for record in ambiguous_alignments
        if len(record["reduced_family_ids"]) > 1
    ]

    family_catalog = [
        _finalize_family(families[family_id])
        for family_id in sorted(families)
    ]
    family_counts_by_base_size = {
        str(base_size): sum(
            family["base_source_size"] == base_size
            for family in family_catalog
        )
        for base_size in range(max_n + 1)
    }
    nontrivial_families_by_base_size = {
        str(base_size): sum(
            family["base_source_size"] == base_size
            and family["nontrivial_spectator_occurrence_count"] > 0
            for family in family_catalog
        )
        for base_size in range(max_n + 1)
    }

    omission_mutation, factor_equivalence = _omission_mutation(sources)
    relabel_audit = _relabel_covariance_audit(levels)
    kraus_basis_audit = _kraus_basis_invariance_audit()
    all_engineering_checks = (
        channel_cp
        and instrument_tp
        and outcome_tni
        and history_channel_tp
        and automorphism_branch_pass
        and pair_orbit_pass
        and factor_equivalence
        and relabel_audit["transition_law_covariant"]
        and kraus_basis_audit["false_kraus_string_test_detected"]
        and local_weight_dependence_violations == 0
        and labeled_probability_product_violations == 0
    )

    return {
        "schema_version": "final-theory-kraus-bell-v0.3.0",
        "suite": "Final-Theory Bench v0.3 Kraus Bell-causality diagnostics",
        "profile_id": CANDIDATE_PROFILE.profile_id,
        "max_source_n": max_n,
        "one_step_target_boundary": max_n + 1,
        "coverage": {
            "source_cardinalities": list(range(max_n + 1)),
            "unlabeled_history_counts": {
                str(n): len(level) for n, level in enumerate(levels)
            },
            "family_enumeration": (
                "exhaustive unordered pairs of distinct precursor-orbit "
                "instrument outcomes, including every inequivalent relative "
                "alignment under source automorphisms"
            ),
            "one_step_target_note": (
                "size n+1 children are canonicalized as needed; no complete "
                "enumeration or continuum claim is made at that level"
            ),
            "arithmetic": "exact integers and fractions; no floating point",
            "randomness_used": False,
        },
        "definition_audit": {
            "status": KRAUS_BELL_CAUSALITY_UNDEFINED,
            "combinatorial_spectator_deletion_for_a_labeled_pair": (
                "DEFINED_AS_INDUCED_SUBPOSET_DIAGNOSTIC"
            ),
            "implemented_history_hilbert_space": (
                "one orthonormal ray per unlabeled causal history"
            ),
            "canonical_spectator_tensor_factor_present": False,
            "canonical_partial_trace_present": False,
            "canonical_full_to_reduced_channel_present": False,
            "canonical_outcome_algebra_correspondence_present": False,
            "relative_alignment_ambiguous_branch_pair_count": len(
                distinct_reduced_family_ambiguities
            ),
            "reduced_pair_outcome_collision_count": (
                reduced_outcome_collision_count
            ),
            "inverse_based_cpobc_applied": False,
            "rank_one_global_matrix_units_treated_as_invertible": False,
            "reason": (
                "The unlabeled one-ray history construction has neither a "
                "spectator subsystem nor a canonical reduction channel. In "
                "addition, an orbit-level branch pair can lose the relative "
                "precursor alignment needed to select a unique reduced family."
            ),
        },
        "comparison_protocol": {
            "instrument_equality": (
                "same labeled outcome CP maps, tested by exact scalar "
                "superoperators/Choi matrices"
            ),
            "channel_equality": "exact superoperator and Choi equality",
            "kraus_list_or_string_equality_used": False,
            "cpobc_inverse_formula_used": False,
        },
        "channel_instrument_audit": {
            "source_count": len(sources),
            "instrument_outcome_count": sum(
                len(source.branches) for source in sources
            ),
            "history_channel_output_count": history_channel_output_count,
            "complete_positivity": channel_cp,
            "instrument_trace_preservation": instrument_tp,
            "outcome_trace_nonincrease": outcome_tni,
            "history_channel_trace_preservation": history_channel_tp,
            "choi_positive_semidefinite": channel_cp,
            "minimum_outcome_probability": _fraction_record(
                minimum_probability
            ),
            "source_certificates": source_certificates,
        },
        "automorphism_audit": {
            "branch_orbit_checks": automorphism_branch_checks,
            "branch_orbit_stabilizer_and_factor_pass": (
                automorphism_branch_pass
            ),
            "pair_orbit_checks": pair_orbit_checks,
            "pair_orbit_stabilizer_pass": pair_orbit_pass,
            "omission_mutation": omission_mutation,
        },
        "relabel_covariance_audit": relabel_audit,
        "kraus_basis_invariance_audit": kraus_basis_audit,
        "bell_family_audit": {
            "by_full_source_size": level_counts,
            "unique_family_count": len(family_catalog),
            "family_counts_by_base_size": family_counts_by_base_size,
            "nontrivial_families_by_base_size": (
                nontrivial_families_by_base_size
            ),
            "family_catalog": family_catalog,
            "nontrivial_spectator_configuration_count": sum(
                record["nontrivial_spectator_configuration_count"]
                for record in level_counts.values()
            ),
            "strict_precursor_size_order_count": sum(
                record["strict_precursor_size_order_count"]
                for record in level_counts.values()
            ),
            "equal_precursor_size_count": sum(
                record["equal_precursor_size_count"]
                for record in level_counts.values()
            ),
            "all_configuration_strict_precursor_size_count": sum(
                record["all_configuration_strict_precursor_size_count"]
                for record in level_counts.values()
            ),
            "all_configuration_equal_precursor_size_count": sum(
                record["all_configuration_equal_precursor_size_count"]
                for record in level_counts.values()
            ),
            "nontrivial_ordering_count_scope": (
                "strict_precursor_size_order_count and "
                "equal_precursor_size_count cover only configurations with "
                "at least one common spectator"
            ),
            "ordering_rule": (
                "larger precursor cardinality first; equal-size pairs remain "
                "physically unordered and use lexicographic order only for "
                "deterministic serialization"
            ),
            "equal_size_cpobc_order_available": False,
            "local_weight_spectator_dependence_violations": (
                local_weight_dependence_violations
            ),
            "per_labeled_precursor_product_violations": (
                labeled_probability_product_violations
            ),
            "absolute_probability_change_count": (
                absolute_probability_change_count
            ),
            "orbit_aggregate_product_violation_count": (
                aggregate_probability_product_violations
            ),
            "relative_alignment_ambiguities": {
                "count": len(distinct_reduced_family_ambiguities),
                "first_examples": distinct_reduced_family_ambiguities[:10],
            },
            "first_probability_dependence_counterexample": (
                first_probability_witness
            ),
        },
        "diagnostic_status": "EXACT_FINITE_DIAGNOSTICS_COMPLETE",
        "engineering_checks_passed": all_engineering_checks,
        "kraus_bell_status": KRAUS_BELL_CAUSALITY_UNDEFINED,
        "kraus_bell_causality_status": KRAUS_BELL_CAUSALITY_UNDEFINED,
        "claim_boundary": (
            "Exact finite CP/TP/TNI, covariance, automorphism, family, and "
            "probability diagnostics are complete through the declared source "
            "cutoff. They do not define a spectator reduction on the existing "
            "Hilbert spaces, so no Kraus Bell-causality pass or fail is issued."
        ),
    }


def kraus_bell_benchmark(max_n: int = 5) -> dict[str, Any]:
    """Return deterministic JSON-ready Kraus Bell-causality diagnostics.

    ``max_n`` is the largest *source* cardinality.  The exact v0.3 audit is
    intentionally bounded at five; one-step children at size ``max_n + 1`` are
    constructed only as needed to describe the transition maps.
    """

    if isinstance(max_n, bool) or not isinstance(max_n, int):
        raise TypeError("max_n must be an integer")
    if not 0 <= max_n <= _MAX_EXACT_SOURCE_N:
        raise ValueError("max_n must be between 0 and 5 inclusive")
    return copy.deepcopy(_benchmark_cached(max_n))
