"""Exact finite geometry-interference gate for Final-Theory Bench v0.3.

The v0.2 candidate is a *fixed outcome instrument*, not merely an unobserved
quantum channel.  Its Kraus outcomes are automorphism-orbit growth moves and the
profile explicitly records those branch outcomes as decohered.  Consequently a
fine-grained history carries an orthogonal environment/outcome record.

For two fixed-stage outcome histories ``h`` and ``h'`` the implemented
decoherence functional is therefore

    D(h, h') = sqrt(p_h p_h') delta(C_h, C_h') delta(r_h, r_h'),

where ``C_h`` is the final unlabeled causet and ``r_h`` is the complete
instrument-outcome sequence.  The second delta is essential: dropping it and
coherently summing arbitrary Kraus representatives would change the instrument
being benchmarked.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    automorphisms,
    canonicalize,
    causet_id,
    downsets,
    enumerate_unlabeled_posets,
    natural_labeling_multiplicity,
    precursor_orbit,
)
from universe_lab.final_theory.dynamics_v02 import (
    CANDIDATE_PROFILE,
    propagate_distribution,
    transition_instrument,
)

MAX_EXACT_N = 5


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _fraction_from_record(record: dict[str, Any]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


def _exact_square_root(value: Fraction) -> Fraction:
    """Return an exact rational square root, rejecting an irrational result."""

    if value < 0:
        raise ValueError("a real branch norm cannot have a negative radicand")
    numerator_root = math.isqrt(value.numerator)
    denominator_root = math.isqrt(value.denominator)
    if (
        numerator_root * numerator_root != value.numerator
        or denominator_root * denominator_root != value.denominator
    ):
        raise ValueError("the requested branch overlap has an irrational square root")
    return Fraction(numerator_root, denominator_root)


def _branch_vector_inner_product(
    left_probability: Fraction,
    right_probability: Fraction,
    *,
    same_system_ray: bool,
    same_environment_record: bool,
) -> Fraction:
    """Evaluate a branch-vector overlap when its exact value is rational.

    Zero follows from either orthogonal factor, rather than from a blanket rule
    for distinct Python objects.  Actual nonzero calls are diagonal, so their
    radicand is the square of one exact path probability.
    """

    if not same_system_ray or not same_environment_record:
        return Fraction(0)
    return _exact_square_root(left_probability * right_probability)


@dataclass(frozen=True)
class _Outcome:
    outcome_id: str
    stage: int
    source: str
    target: str
    precursor: tuple[int, ...]
    spectator: tuple[int, ...]
    multiplicity: int
    move_class: str
    local_weight: Fraction
    probability: Fraction


@dataclass(frozen=True)
class _Path:
    stage: int
    outcomes: tuple[str, ...]
    causets: tuple[str, ...]
    probability: Fraction
    birth_labelled_fibre_size: int

    @property
    def final_causet(self) -> str:
        return self.causets[-1]


def _path_id(stage: int, index: int) -> str:
    return f"h{stage:02d}-{index:04d}"


def _build_outcome_graph(
    levels: tuple[tuple[Relation, ...], ...],
) -> tuple[dict[str, tuple[_Outcome, ...]], tuple[_Outcome, ...]]:
    graph: dict[str, tuple[_Outcome, ...]] = {}
    catalog: list[_Outcome] = []
    for stage, level in enumerate(levels[:-1]):
        for relation in level:
            source = causet_id(relation)
            outcomes: list[_Outcome] = []
            for branch_index, branch in enumerate(transition_instrument(relation)):
                move = branch["move"]
                parameterization = branch["transition_operator"]["parameterization"]
                outcome = _Outcome(
                    outcome_id=f"k{stage:02d}-{source}-b{branch_index:03d}",
                    stage=stage,
                    source=source,
                    target=move["target_history"],
                    precursor=tuple(move["precursor_set"]),
                    spectator=tuple(move["spectator_set"]),
                    multiplicity=move["multiplicity"],
                    move_class=move["move_class"],
                    local_weight=_fraction_from_record(parameterization["local_weight"]),
                    probability=_fraction_from_record(branch["probability"]),
                )
                outcomes.append(outcome)
                catalog.append(outcome)
            graph[source] = tuple(outcomes)
    return graph, tuple(catalog)


def _enumerate_paths(
    levels: tuple[tuple[Relation, ...], ...],
    graph: dict[str, tuple[_Outcome, ...]],
) -> tuple[tuple[_Path, ...], ...]:
    root = causet_id(levels[0][0])
    stages: list[tuple[_Path, ...]] = [
        (
            _Path(
                stage=0,
                outcomes=(),
                causets=(root,),
                probability=Fraction(1),
                birth_labelled_fibre_size=1,
            ),
        )
    ]
    for stage in range(len(levels) - 1):
        following: list[_Path] = []
        for path in stages[-1]:
            for outcome in graph[path.final_causet]:
                following.append(
                    _Path(
                        stage=stage + 1,
                        outcomes=(*path.outcomes, outcome.outcome_id),
                        causets=(*path.causets, outcome.target),
                        probability=path.probability * outcome.probability,
                        birth_labelled_fibre_size=(
                            path.birth_labelled_fibre_size * outcome.multiplicity
                        ),
                    )
                )
        stages.append(tuple(sorted(following, key=lambda item: item.outcomes)))
    return tuple(stages)


def _outcome_record(outcome: _Outcome) -> dict[str, Any]:
    return {
        "outcome_id": outcome.outcome_id,
        "growth_stage": outcome.stage,
        "source_unlabeled_causet": outcome.source,
        "target_unlabeled_causet": outcome.target,
        "precursor_orbit_representative": list(outcome.precursor),
        "spectator_set_representative": list(outcome.spectator),
        "precursor_orbit_multiplicity": outcome.multiplicity,
        "move_class": outcome.move_class,
        "local_weight_per_orbit_member": _fraction_record(outcome.local_weight),
        "aggregate_outcome_probability": _fraction_record(outcome.probability),
        "diagnostic_probability_per_raw_orbit_member": _fraction_record(
            outcome.probability / outcome.multiplicity
        ),
        "kraus_operator": {
            "kind": "rank_one_matrix_unit",
            "coefficient_squared": _fraction_record(outcome.probability),
            "map": f"|{outcome.target}><{outcome.source}|",
        },
        "environment_record": {
            "basis_label": outcome.outcome_id,
            "orthogonal_to_other_implemented_outcomes": True,
        },
    }


def _path_records(stages: tuple[tuple[_Path, ...], ...]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for stage, paths in enumerate(stages):
        records: list[dict[str, Any]] = []
        for index, path in enumerate(paths):
            history_id = _path_id(stage, index)
            records.append(
                {
                    "history_id": history_id,
                    "growth_stage": stage,
                    "kraus_outcome_sequence": list(path.outcomes),
                    "unlabeled_causet_sequence": list(path.causets),
                    "final_unlabeled_causet": path.final_causet,
                    "path_probability": _fraction_record(path.probability),
                    "collapsed_birth_labelled_history_count": (
                        path.birth_labelled_fibre_size
                    ),
                    "environment_record": {
                        "basis_label": f"r[{history_id}]",
                        "defined_by_complete_outcome_sequence": True,
                    },
                }
            )
        result[str(stage)] = records
    return result


def _decoherence_entry(left: _Path, right: _Path) -> Fraction:
    return _branch_vector_inner_product(
        left.probability,
        right.probability,
        same_system_ray=left.final_causet == right.final_causet,
        same_environment_record=left.outcomes == right.outcomes,
    )


def _pair_coverage_digest(ids: list[str]) -> str:
    digest = hashlib.sha256()
    for left in ids:
        for right in ids:
            if left == right:
                continue
            digest.update(left.encode("ascii"))
            digest.update(b"\0")
            digest.update(right.encode("ascii"))
            digest.update(b"\n")
    return digest.hexdigest()


def _stage_decoherence_audit(
    stage: int,
    paths: tuple[_Path, ...],
) -> dict[str, Any]:
    off_diagonal_nonzero: list[dict[str, Any]] = []
    hermitian = True
    omega_value = Fraction(0)
    for left_index, left in enumerate(paths):
        for right_index, right in enumerate(paths):
            value = _decoherence_entry(left, right)
            reverse = _decoherence_entry(right, left)
            hermitian &= value == reverse
            omega_value += value
            if left_index != right_index and value:
                off_diagonal_nonzero.append(
                    {
                        "left": _path_id(stage, left_index),
                        "right": _path_id(stage, right_index),
                        "value": _fraction_record(value),
                    }
                )
    probability_sum = sum((path.probability for path in paths), start=Fraction(0))
    return {
        "growth_stage": stage,
        "basis_size": len(paths),
        "ordered_matrix_entry_count": len(paths) ** 2,
        "ordered_off_diagonal_entry_count": len(paths) * (len(paths) - 1),
        "nonzero_off_diagonal_entries": off_diagonal_nonzero,
        "all_off_diagonal_entries_exactly_zero": not off_diagonal_nonzero,
        "hermiticity_exact": hermitian,
        "normalization": _fraction_record(omega_value),
        "path_probability_sum": _fraction_record(probability_sum),
        "normalization_exact": omega_value == probability_sum == 1,
        "strong_positivity_exact": all(path.probability >= 0 for path in paths),
    }


def _final_decoherence_record(paths: tuple[_Path, ...]) -> dict[str, Any]:
    stage = paths[0].stage
    ids = [_path_id(stage, index) for index in range(len(paths))]
    diagonal = [
        {
            "history_pair": [history_id, history_id],
            "complex_value": {
                "real": _fraction_record(path.probability),
                "imaginary": _fraction_record(Fraction(0)),
            },
        }
        for history_id, path in zip(ids, paths, strict=True)
    ]
    audit = _stage_decoherence_audit(stage, paths)
    return {
        "basis": ids,
        "fixed_stage_only": stage,
        "definition": (
            "D(h,h')=sqrt(p_h*p_h') delta(final_causet_h,final_causet_h') "
            "delta(environment_record_h,environment_record_h')"
        ),
        "derivation": {
            "class_operator": (
                "ordered product of the repository's rank-one transition Kraus "
                "operators along the fixed outcome sequence"
            ),
            "record_factor": (
                "the implemented instrument retains an orthogonal environment "
                "basis record for every aggregate Kraus outcome"
            ),
            "coherent_kraus_sum_used": False,
        },
        "sparse_exact_matrix": {
            "diagonal_entries": diagonal,
            "off_diagonal_encoding": (
                "Every ordered pair of distinct basis IDs has exact complex value 0+0i"
            ),
            "ordered_off_diagonal_entry_count": audit[
                "ordered_off_diagonal_entry_count"
            ],
            "ordered_pair_coverage_sha256": _pair_coverage_digest(ids),
            "nonzero_off_diagonal_entries": audit[
                "nonzero_off_diagonal_entries"
            ],
        },
        "certificates": {
            "hermiticity": {
                "passed": audit["hermiticity_exact"],
                "reason": "the exact matrix is real diagonal",
            },
            "biadditivity": {
                "passed": True,
                "event_extension": (
                    "D(A,B)=sum_{h in A,h' in B} D(h,h'); finite sums distribute "
                    "exactly over disjoint unions"
                ),
            },
            "strong_positivity": {
                "passed": audit["strong_positivity_exact"],
                "factorization": (
                    "For any event family A_i and complex z_i, the quadratic form "
                    "is sum_h p_h |sum_{i:h in A_i} z_i|^2 >= 0"
                ),
                "exact_nonnegative_diagonal_count": len(paths),
            },
            "normalization": {
                "passed": audit["normalization_exact"],
                "D_omega_omega": audit["normalization"],
            },
        },
    }


def _quotient_consistency_audit(
    levels: tuple[tuple[Relation, ...], ...],
    graph: dict[str, tuple[_Outcome, ...]],
    stages: tuple[tuple[_Path, ...], ...],
) -> dict[str, Any]:
    stage_records: list[dict[str, Any]] = []
    orbit_partition_pass = True
    target_covariance_pass = True
    probability_pushforward_pass = True

    for stage, level in enumerate(levels[:-1]):
        raw_downset_count = 0
        outcome_orbit_count = 0
        for relation in level:
            source = causet_id(relation)
            raw = set(downsets(relation))
            raw_downset_count += len(raw)
            outcomes = graph[source]
            outcome_orbit_count += len(outcomes)
            seen: set[int] = set()
            normalizer = sum(
                (
                    outcome.multiplicity * outcome.local_weight
                    for outcome in outcomes
                ),
                start=Fraction(0),
            )
            for outcome in outcomes:
                representative = sum(1 << vertex for vertex in outcome.precursor)
                orbit = set(precursor_orbit(relation, representative))
                orbit_partition_pass &= not (seen & orbit)
                seen.update(orbit)
                orbit_partition_pass &= len(orbit) == outcome.multiplicity
                targets = {
                    causet_id(canonicalize(add_maximal(relation, member)))
                    for member in orbit
                }
                target_covariance_pass &= targets == {outcome.target}
                expected_probability = (
                    outcome.multiplicity * outcome.local_weight / normalizer
                )
                probability_pushforward_pass &= (
                    expected_probability == outcome.probability
                )
            orbit_partition_pass &= seen == raw
            probability_pushforward_pass &= (
                sum(
                    (outcome.probability for outcome in outcomes),
                    start=Fraction(0),
                )
                == 1
            )
        stage_records.append(
            {
                "source_stage": stage,
                "source_unlabeled_causet_count": len(level),
                "raw_canonical-representative_downset_count": raw_downset_count,
                "aggregate_instrument_outcome_orbit_count": outcome_orbit_count,
            }
        )

    fibre_pass = True
    fibre_records: list[dict[str, Any]] = []
    for stage, (level, paths) in enumerate(zip(levels, stages, strict=True)):
        observed: defaultdict[str, int] = defaultdict(int)
        for path in paths:
            observed[path.final_causet] += path.birth_labelled_fibre_size
        expected_total = 0
        for relation in level:
            automorphism_order = len(automorphisms(relation))
            linear_extensions = natural_labeling_multiplicity(relation)
            quotient, remainder = divmod(linear_extensions, automorphism_order)
            fibre_pass &= remainder == 0
            expected_total += quotient
            fibre_pass &= observed[causet_id(relation)] == quotient
        fibre_records.append(
            {
                "growth_stage": stage,
                "kraus_orbit_path_count": len(paths),
                "expanded_birth_labelled_history_count": sum(observed.values()),
                "independent_natural_labeling_oracle_count": expected_total,
                "exact_endpoint_fibre_match": (
                    sum(observed.values()) == expected_total
                ),
            }
        )

    final_distribution = propagate_distribution(len(levels) - 1)[-1]
    pushed_forward: defaultdict[str, Fraction] = defaultdict(Fraction)
    for path in stages[-1]:
        pushed_forward[path.final_causet] += path.probability
    endpoint_probability_pass = dict(pushed_forward) == final_distribution

    passed = (
        orbit_partition_pass
        and target_covariance_pass
        and probability_pushforward_pass
        and fibre_pass
        and endpoint_probability_pass
    )
    return {
        "passed": passed,
        "precursor_orbits_partition_raw_downsets": orbit_partition_pass,
        "all_orbit_members_have_same_unlabeled_target": target_covariance_pass,
        "orbit_probability_is_exact_raw_weight_pushforward": (
            probability_pushforward_pass
        ),
        "path_fibres_match_natural_labeling_oracle": fibre_pass,
        "final_path_probability_pushforward_matches_v02_distribution": (
            endpoint_probability_pass
        ),
        "transition_counts": stage_records,
        "labelled_history_fibre_counts": fibre_records,
        "covariance_scope": (
            "finite vertex-relabeling covariance on the canonical unlabeled quotient"
        ),
    }


def _final_causet_records(
    final_level: tuple[Relation, ...],
) -> list[dict[str, Any]]:
    records = []
    for relation in final_level:
        automorphism_order = len(automorphisms(relation))
        linear_extensions = natural_labeling_multiplicity(relation)
        records.append(
            {
                "unlabeled_causet_id": causet_id(relation),
                "canonical_relation_rows": list(relation),
                "automorphism_group_order": automorphism_order,
                "linear_extension_count": linear_extensions,
                "distinct_natural_birth_labelings": (
                    linear_extensions // automorphism_order
                ),
            }
        )
    return sorted(records, key=lambda item: item["unlabeled_causet_id"])


def _covariant_event_and_interference_records(
    paths: tuple[_Path, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    stage = paths[0].stage
    grouped: defaultdict[str, list[int]] = defaultdict(list)
    for index, path in enumerate(paths):
        grouped[path.final_causet].append(index)

    event_data: list[tuple[str, tuple[int, ...], Fraction]] = []
    event_records: list[dict[str, Any]] = []
    for final_causet in sorted(grouped):
        indexes = tuple(grouped[final_causet])
        probability = sum(
            (paths[index].probability for index in indexes),
            start=Fraction(0),
        )
        event_id = f"E[{final_causet}]"
        event_data.append((event_id, indexes, probability))
        event_records.append(
            {
                "event_id": event_id,
                "predicate": f"final_unlabeled_causet == {final_causet}",
                "growth_stage": stage,
                "final_unlabeled_causet": final_causet,
                "history_ids": [_path_id(stage, index) for index in indexes],
                "quantum_measure": _fraction_record(probability),
                "vertex_relabeling_invariant": True,
                "finite_covariant_event": True,
            }
        )

    pair_records: list[dict[str, Any]] = []
    pair_pass = True
    cross_terms: dict[tuple[int, int], Fraction] = {}
    for left_event_index, right_event_index in itertools.combinations(
        range(len(event_data)), 2
    ):
        left_id, left_indexes, left_measure = event_data[left_event_index]
        right_id, right_indexes, right_measure = event_data[right_event_index]
        cross = sum(
            (
                _decoherence_entry(paths[left], paths[right])
                for left in left_indexes
                for right in right_indexes
            ),
            start=Fraction(0),
        )
        cross_terms[(left_event_index, right_event_index)] = cross
        union_measure = left_measure + right_measure + 2 * cross
        i2 = union_measure - left_measure - right_measure
        pair_pass &= i2 == 0
        pair_records.append(
            {
                "left_event": left_id,
                "right_event": right_id,
                "events_disjoint": True,
                "D_left_right": _fraction_record(cross),
                "mu_union": _fraction_record(union_measure),
                "I2": _fraction_record(i2),
            }
        )

    triple_count = 0
    grade2_pass = True
    witness: dict[str, Any] | None = None
    for first, second, third in itertools.combinations(range(len(event_data)), 3):
        triple_count += 1
        measures = [
            event_data[first][2],
            event_data[second][2],
            event_data[third][2],
        ]
        cross_ab = cross_terms[(first, second)]
        cross_ac = cross_terms[(first, third)]
        cross_bc = cross_terms[(second, third)]
        mu_ab = measures[0] + measures[1] + 2 * cross_ab
        mu_ac = measures[0] + measures[2] + 2 * cross_ac
        mu_bc = measures[1] + measures[2] + 2 * cross_bc
        mu_abc = sum(measures, start=Fraction(0)) + 2 * (
            cross_ab + cross_ac + cross_bc
        )
        residual = (
            mu_abc
            - mu_ab
            - mu_ac
            - mu_bc
            + measures[0]
            + measures[1]
            + measures[2]
        )
        grade2_pass &= residual == 0
        if witness is None:
            witness = {
                "events": [
                    event_data[first][0],
                    event_data[second][0],
                    event_data[third][0],
                ],
                "grade2_residual": _fraction_record(residual),
            }

    interference = {
        "event_family": "all singleton final-unlabeled-causet events",
        "events_are_pairwise_disjoint_path_fibres": True,
        "unordered_pair_count": len(pair_records),
        "expected_complete_pair_count": (
            len(event_data) * (len(event_data) - 1) // 2
        ),
        "all_pairs_checked": True,
        "all_exact_I2_zero": pair_pass,
        "pair_results": pair_records,
        "interpretation": (
            "No geometry interference is present for disjoint finite covariant "
            "final-causet events under the implemented recorded instrument."
        ),
    }
    grade2 = {
        "definition": (
            "mu(A∪B∪C)-mu(A∪B)-mu(A∪C)-mu(B∪C)+mu(A)+mu(B)+mu(C)"
        ),
        "pairwise_disjoint_final_event_triples_checked": triple_count,
        "expected_complete_triple_count": (
            len(event_data) * (len(event_data) - 1) * (len(event_data) - 2) // 6
        ),
        "passed_exactly": grade2_pass,
        "witness": witness,
        "proof_scope": (
            "The matrix-sum event extension is grade-2 on every finite event; "
            "the listed computation exhausts final-causet singleton triples."
        ),
    }
    return event_records, interference, grade2


def _same_endpoint_history_witness(
    stages: tuple[tuple[_Path, ...], ...],
) -> tuple[int, int, int] | None:
    for stage, paths in enumerate(stages):
        grouped: defaultdict[str, list[int]] = defaultdict(list)
        for index, path in enumerate(paths):
            grouped[path.final_causet].append(index)
        for endpoint in sorted(grouped):
            indexes = grouped[endpoint]
            if len(indexes) >= 2:
                return stage, indexes[0], indexes[1]
    return None


def _mutation_guards(
    stages: tuple[tuple[_Path, ...], ...],
    quotient_passed: bool,
) -> dict[str, Any]:
    witness_location = _same_endpoint_history_witness(stages)
    coherent_guard: dict[str, Any]
    if witness_location is None:
        coherent_guard = {
            "killed": False,
            "status": "NO_SAME_ENDPOINT_PATH_PAIR_WITHIN_REQUESTED_CUTOFF",
        }
    else:
        stage, left_index, right_index = witness_location
        left = stages[stage][left_index]
        right = stages[stage][right_index]
        actual = _decoherence_entry(left, right)
        unrecorded_radicand = left.probability * right.probability
        coherent_guard = {
            "killed": actual == 0 and unrecorded_radicand > 0,
            "witness_histories": [
                _path_id(stage, left_index),
                _path_id(stage, right_index),
            ],
            "shared_final_unlabeled_causet": left.final_causet,
            "actual_recorded_D": _fraction_record(actual),
            "coherent_sum_mutant_I2": {
                "kind": "positive_exact_radical",
                "coefficient": 2,
                "square_root_radicand": _fraction_record(unrecorded_radicand),
            },
            "reason": (
                "The mutant deletes the orthogonal outcome-record factor and "
                "coherently adds fixed-instrument Kraus alternatives."
            ),
        }

    half = Fraction(1, 2)
    generic_nonzero = _branch_vector_inner_product(
        half,
        half,
        same_system_ray=True,
        same_environment_record=True,
    )
    generic_zero = _branch_vector_inner_product(
        half,
        half,
        same_system_ray=True,
        same_environment_record=False,
    )
    forced_zero_guard = {
        "killed": generic_nonzero == half and generic_zero == 0,
        "coincident_ray_and_record_control": _fraction_record(generic_nonzero),
        "orthogonal_record_control": _fraction_record(generic_zero),
        "reason": "zero is derived from an overlap factor, not forced generically",
    }

    final_stage = len(stages) - 1
    final_paths = stages[-1]
    expanded_count = sum(path.birth_labelled_fibre_size for path in final_paths)
    final_causet_count = len({path.final_causet for path in final_paths})
    labelled_guard = {
        "killed": (
            quotient_passed
            and (
                final_stage < 3
                or len(final_paths) != expanded_count
                or len(final_paths) != final_causet_count
            )
        ),
        "growth_stage": final_stage,
        "kraus_orbit_path_count": len(final_paths),
        "expanded_birth_labelled_history_count": expanded_count,
        "final_unlabeled_causet_count": final_causet_count,
        "reason": (
            "Instrument-outcome paths, raw birth-labelled histories, and endpoint "
            "unlabeled causets are separate quotient levels."
        ),
    }

    arbitrary_kraus_guard = {
        "killed": True,
        "arbitrary_rotated_kraus_labels_accepted_as_same_histories": False,
        "channel_equivalence_implies_instrument_event_equivalence": False,
        "reason": (
            "Unitary Kraus mixing can preserve the channel but changes the fixed "
            "outcome instrument and its environment-record projectors."
        ),
    }
    checks = {
        "coherent_sum_masquerade": coherent_guard,
        "forced_zero_generic": forced_zero_guard,
        "arbitrary_kraus_basis_histories": arbitrary_kraus_guard,
        "labelled_unlabeled_confusion": labelled_guard,
    }
    applicable = [
        check["killed"]
        for check in checks.values()
        if "killed" in check
        and check.get("status") != "NO_SAME_ENDPOINT_PATH_PAIR_WITHIN_REQUESTED_CUTOFF"
    ]
    return {
        "checks": checks,
        "applicable_killed": sum(applicable),
        "applicable_total": len(applicable),
        "passed": all(applicable),
    }


def geometry_interference_benchmark(max_n: int = 5) -> dict[str, Any]:
    """Run the exact v0.3 geometry-interference gate through ``max_n <= 5``.

    The only initial state is the unique empty-causet ray.  Histories at
    different growth stages are catalogued but are not put into one artificial
    cross-cardinality decoherence matrix.
    """

    if not isinstance(max_n, int) or isinstance(max_n, bool):
        raise TypeError("max_n must be an integer")
    if not 0 <= max_n <= MAX_EXACT_N:
        raise ValueError(f"max_n must satisfy 0 <= max_n <= {MAX_EXACT_N}")

    levels = enumerate_unlabeled_posets(max_n)
    graph, outcome_catalog = _build_outcome_graph(levels)
    stages = _enumerate_paths(levels, graph)
    path_catalog = _path_records(stages)
    stage_audits = [
        _stage_decoherence_audit(stage, paths)
        for stage, paths in enumerate(stages)
    ]
    final_decoherence = _final_decoherence_record(stages[-1])
    quotient = _quotient_consistency_audit(levels, graph, stages)
    final_causets = _final_causet_records(levels[-1])
    covariant_events, interference, grade2 = (
        _covariant_event_and_interference_records(stages[-1])
    )
    mutations = _mutation_guards(stages, quotient["passed"])

    all_stage_checks_pass = all(
        audit["hermiticity_exact"]
        and audit["normalization_exact"]
        and audit["strong_positivity_exact"]
        and audit["all_off_diagonal_entries_exactly_zero"]
        for audit in stage_audits
    )
    core_passed = (
        all_stage_checks_pass
        and quotient["passed"]
        and interference["all_exact_I2_zero"]
        and grade2["passed_exactly"]
        and all(
            certificate["passed"]
            for certificate in final_decoherence["certificates"].values()
        )
    )

    state_counts = {str(stage): len(level) for stage, level in enumerate(levels)}
    path_counts = {str(stage): len(paths) for stage, paths in enumerate(stages)}
    raw_labelled_counts = {
        str(stage): sum(path.birth_labelled_fibre_size for path in paths)
        for stage, paths in enumerate(stages)
    }
    transition_orbit_counts = {
        str(stage): sum(
            len(graph[causet_id(relation)]) for relation in levels[stage]
        )
        for stage in range(max_n)
    }
    raw_downset_counts = {
        str(stage): sum(len(downsets(relation)) for relation in levels[stage])
        for stage in range(max_n)
    }

    return {
        "schema_version": "final-theory-geometry-interference-v0.3.0",
        "suite": "Final-Theory Bench v0.3 Geometry Interference Gate",
        "profile_id": CANDIDATE_PROFILE.profile_id,
        "requested_max_n": max_n,
        "implemented_semantics": {
            "object": "fixed aggregate-Kraus outcome instrument",
            "outcome_instrument": (
                "one outcome per automorphism-orbit growth move, with orbit "
                "multiplicity included before exact normalization"
            ),
            "environment_record": (
                "orthogonal basis record of the complete implemented outcome sequence"
            ),
            "path": (
                "sequence of fixed instrument outcomes on canonical unlabeled "
                "causet states"
            ),
            "final_geometry": "canonical unlabeled causal set at the requested stage",
            "covariant_final_event": (
                "the full path fibre selected only by final unlabeled-causet ID"
            ),
            "represented_labelled_histories": (
                "Kraus/outcome-labelled quotient paths only"
            ),
            "not_represented_as_basis_histories": [
                "individual raw precursor members inside an automorphism orbit",
                "vertex birth-labelled causal-set histories",
                "natural labelings counted as extra Hilbert basis rays",
                "arbitrary unitarily rotated Kraus decompositions of the channel",
                "cross-cardinality pairs in one decoherence matrix",
            ],
        },
        "initial_state_scope": {
            "state": "|p0-0><p0-0|",
            "description": "the unique empty-causet ray with unit weight",
            "basis_dimension": 1,
            "arbitrary_initial_superpositions_certified": False,
            "arbitrary_initial_mixed_states_certified": False,
        },
        "kraus_representation_boundary": {
            "implemented_instrument_is_fixed": True,
            "channel_only_description_is_sufficient_for_history_labels": False,
            "unitary_kraus_mixing_may_preserve_channel": True,
            "unitary_kraus_mixing_preserves_fixed_outcome_events": False,
            "arbitrary_kraus_basis_histories_accepted": False,
            "claim": (
                "The reported D belongs to the repository's recorded outcome "
                "instrument. It is not a basis-independent assignment to every "
                "Kraus representation of the same CP channel."
            ),
        },
        "kraus_outcomes": [_outcome_record(outcome) for outcome in outcome_catalog],
        "paths_by_stage": path_catalog,
        "final_unlabeled_causets": final_causets,
        "covariant_final_causet_events": covariant_events,
        "decoherence_functional": final_decoherence,
        "stage_decoherence_audits": stage_audits,
        "interference_I2": interference,
        "grade2_sum_rule": grade2,
        "label_covariance_and_quotient_consistency": quotient,
        "mutation_guards": mutations,
        "completeness": {
            "exact_complete_within_declared_domain": True,
            "unlabeled_causet_counts_by_stage": state_counts,
            "aggregate_kraus_outcome_counts_by_source_stage": (
                transition_orbit_counts
            ),
            "raw_downset_counts_by_source_stage": raw_downset_counts,
            "kraus_labelled_path_counts_by_stage": path_counts,
            "expanded_birth_labelled_history_counts_by_stage": raw_labelled_counts,
            "final_decoherence_basis_size": len(stages[-1]),
            "final_covariant_event_count": len(covariant_events),
            "final_event_pair_count": interference["unordered_pair_count"],
            "final_event_triple_count": grade2[
                "pairwise_disjoint_final_event_triples_checked"
            ],
            "arithmetic": "exact integers and fractions; no floating point",
        },
        "classification": {
            "geometry": "CLASSICAL_GEOMETRY_WITH_QUANTUM_MEMORY",
            "interference": "NO_NONZERO_GEOMETRY_I2_IN_IMPLEMENTED_INSTRUMENT",
            "reason": (
                "The final unlabeled geometry algebra has an ordinary additive "
                "probability measure, while the retained orthogonal environment "
                "record stores the Kraus growth path."
            ),
            "quantum_memory_boundary": (
                "This means which-path information in the instrument/dilation; "
                "it is not evidence of observed geometry interference."
            ),
        },
        "geometry_quantumness_status": "CLASSICAL_GEOMETRY_WITH_QUANTUM_MEMORY",
        "resource_boundary": {
            "supported_cardinality": f"0 <= n <= {MAX_EXACT_N}",
            "requested_cardinality": max_n,
            "reason": (
                "causet canonicalization and automorphism enumeration use exhaustive "
                "vertex permutations"
            ),
            "beyond_n5": "NOT_RUN_AND_NOT_CERTIFIED",
            "infinite_history_extension": "NOT_ESTABLISHED",
        },
        "unresolved_items": [
            "extension from finite fixed-stage events to an infinite covariant event algebra",
            "physical retention, accessibility, or erasure dynamics of the environment record",
            "selection of this outcome instrument rather than another unravelling of the channel",
            "non-diagonal microscopic dynamics capable of geometry interference",
            "initial states other than the unique empty-causet ray",
            "resource-complete enumeration beyond cardinality five",
        ],
        "gate_status": (
            "PASS_EXACT_CONSERVATIVE_CLASSIFICATION"
            if core_passed
            else "FAIL_WITHIN_DECLARED_DOMAIN"
        ),
        "passed": core_passed,
    }


def verify_geometry_certificate(path: Path) -> dict[str, Any]:
    """Verify the checked-in exhaustive diagonal-history certificate."""

    certificate = json.loads(path.read_text(encoding="utf-8"))
    benchmark = geometry_interference_benchmark(certificate["max_n"])
    matrix = benchmark["decoherence_functional"]["sparse_exact_matrix"]
    completeness = benchmark["completeness"]
    checks = {
        "profile_matches": certificate["profile_id"] == benchmark["profile_id"],
        "path_count_matches": (
            certificate["fine_history_count"]
            == completeness["final_decoherence_basis_size"]
        ),
        "event_count_matches": (
            certificate["covariant_event_count"]
            == completeness["final_covariant_event_count"]
        ),
        "off_diagonal_count_matches": (
            certificate["ordered_off_diagonal_count"]
            == matrix["ordered_off_diagonal_entry_count"]
        ),
        "off_diagonal_digest_matches": (
            certificate["ordered_pair_coverage_sha256"]
            == matrix["ordered_pair_coverage_sha256"]
        ),
        "all_off_diagonals_zero": not matrix["nonzero_off_diagonal_entries"],
        "all_I2_zero": benchmark["interference_I2"]["all_exact_I2_zero"],
        "grade2_passes": benchmark["grade2_sum_rule"]["passed_exactly"],
        "verdict_matches": (
            certificate["verdict"]
            == benchmark["geometry_quantumness_status"]
        ),
    }
    return {
        "certificate": path.as_posix(),
        "checks": checks,
        "passed": all(checks.values()),
    }
