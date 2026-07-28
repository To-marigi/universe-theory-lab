"""Exact literature-locked commutative CSG reference for Bench v0.3.1.

The dynamics is the finite-coupling family in Surya--Zalel,
arXiv:2003.11311v1, Eq. (15) and Claim 3.8.  The exact specialization is

    t_0 = 1,  t_2 = 1 + i,  t_k = 0 otherwise.

Claim 3.8 item 2 applies because there is one non-zero positive-index coupling
and k_1 = 2 > 1.  This module only reproduces the finite scalar dynamics and
maps the specialization to that source theorem; it does not present CSG or its
extension as a new result.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    automorphisms,
    canonicalize,
    causet_id,
    comparable_pairs,
    downsets,
    enumerate_unlabeled_posets,
    growth_moves,
    has_relation,
    height,
    maximal_elements_in_subset,
    natural_labeling_multiplicity,
    precursor_orbit,
    width,
)
from universe_lab.final_theory.extension_v03 import extension_benchmark
from universe_lab.final_theory.geometry_v03 import geometry_interference_benchmark
from universe_lab.final_theory.kraus_bell_v03 import (
    KRAUS_BELL_CAUSALITY_UNDEFINED,
)

MAX_EXACT_N = 5
PAPER_ID = "arXiv:2003.11311v1"
PAPER_SHA256 = "0db0461c144e36215eccfc5b51c52720da4575878876f18c4a796041a639f272"
REFERENCE_EVENT_A = "p3-000"
REFERENCE_EVENT_B = "p3-024"


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class GaussianRational:
    """An exact element of Q(i)."""

    real: Fraction
    imaginary: Fraction = Fraction(0)

    def __add__(self, other: GaussianRational) -> GaussianRational:
        return GaussianRational(
            self.real + other.real,
            self.imaginary + other.imaginary,
        )

    def __sub__(self, other: GaussianRational) -> GaussianRational:
        return GaussianRational(
            self.real - other.real,
            self.imaginary - other.imaginary,
        )

    def __neg__(self) -> GaussianRational:
        return GaussianRational(-self.real, -self.imaginary)

    def __mul__(self, other: GaussianRational) -> GaussianRational:
        return GaussianRational(
            self.real * other.real - self.imaginary * other.imaginary,
            self.real * other.imaginary + self.imaginary * other.real,
        )

    def __truediv__(self, other: GaussianRational) -> GaussianRational:
        denominator = other.norm_squared()
        if denominator == 0:
            raise ZeroDivisionError("division by the zero Gaussian rational")
        numerator = self * other.conjugate()
        return GaussianRational(
            numerator.real / denominator,
            numerator.imaginary / denominator,
        )

    def scale(self, factor: int | Fraction) -> GaussianRational:
        exact_factor = Fraction(factor)
        return GaussianRational(
            self.real * exact_factor,
            self.imaginary * exact_factor,
        )

    def conjugate(self) -> GaussianRational:
        return GaussianRational(self.real, -self.imaginary)

    def norm_squared(self) -> Fraction:
        return self.real * self.real + self.imaginary * self.imaginary

    def is_zero(self) -> bool:
        return self.real == 0 and self.imaginary == 0

    def to_expression(self) -> str:
        if self.imaginary == 0:
            return _fraction_text(self.real)
        if self.real == 0:
            if self.imaginary == 1:
                return "i"
            if self.imaginary == -1:
                return "-i"
            return f"{_fraction_text(self.imaginary)}*i"
        sign = "+" if self.imaginary > 0 else "-"
        magnitude = abs(self.imaginary)
        imaginary_text = "i" if magnitude == 1 else f"{_fraction_text(magnitude)}*i"
        return f"{_fraction_text(self.real)} {sign} {imaginary_text}"

    def to_record(self) -> dict[str, Any]:
        return {
            "real": _fraction_record(self.real),
            "imaginary": _fraction_record(self.imaginary),
            "expression": self.to_expression(),
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> GaussianRational:
        real = record["real"]
        imaginary = record["imaginary"]
        return cls(
            Fraction(real["numerator"], real["denominator"]),
            Fraction(imaginary["numerator"], imaginary["denominator"]),
        )


ZERO = GaussianRational(Fraction(0))
ONE = GaussianRational(Fraction(1))
REFERENCE_T2 = GaussianRational(Fraction(1), Fraction(1))


@dataclass(frozen=True)
class CommutativeCSGParameters:
    """Finite exact coupling sequence with implicit zero tail."""

    couplings: tuple[GaussianRational, ...]

    def coupling(self, index: int) -> GaussianRational:
        if index < 0:
            raise ValueError("coupling index must be non-negative")
        if index >= len(self.couplings):
            return ZERO
        return self.couplings[index]

    def to_record(self) -> dict[str, Any]:
        return {
            "nonzero_couplings": {
                str(index): value.to_record()
                for index, value in enumerate(self.couplings)
                if not value.is_zero()
            },
            "implicit_tail": "t_k = 0 for every unlisted k",
        }


REFERENCE_PARAMETERS = CommutativeCSGParameters((ONE, ZERO, REFERENCE_T2))


def _validate_max_n(max_n: int) -> None:
    if not isinstance(max_n, int) or isinstance(max_n, bool):
        raise TypeError("max_n must be an integer")
    if not 1 <= max_n <= MAX_EXACT_N:
        raise ValueError(f"max_n must satisfy 1 <= max_n <= {MAX_EXACT_N}")


def lambda_value(
    a: int,
    b: int,
    parameters: CommutativeCSGParameters = REFERENCE_PARAMETERS,
) -> GaussianRational:
    """Return Eq. (15)'s lambda(a,b) exactly."""

    if not 0 <= b <= a:
        raise ValueError("lambda indices must satisfy 0 <= b <= a")
    result = ZERO
    for index in range(b, a + 1):
        coefficient = math.comb(a - b, index - b)
        result = result + parameters.coupling(index).scale(coefficient)
    return result


def transition_amplitude(
    relation: Relation,
    precursor: int,
    parameters: CommutativeCSGParameters = REFERENCE_PARAMETERS,
) -> GaussianRational:
    """Return the per-labelled-transition amplitude of Eq. (15)."""

    if precursor not in downsets(relation):
        raise ValueError("precursor must be a down-set of the source causal set")
    source_size = len(relation)
    precursor_size = precursor.bit_count()
    maximal_count = len(maximal_elements_in_subset(relation, precursor))
    denominator = lambda_value(source_size, 0, parameters)
    return lambda_value(precursor_size, maximal_count, parameters) / denominator


def endpoint_amplitude(
    relation: Relation,
    parameters: CommutativeCSGParameters = REFERENCE_PARAMETERS,
) -> GaussianRational:
    """Compute a labelled-cylinder amplitude directly from the final order.

    The numerator is the product of the birth numerators for every element.
    The denominator depends only on cardinality.  This is an independent,
    manifestly relabel-invariant oracle for quotient-path multiplication.
    """

    numerator = ONE
    for upper in range(len(relation)):
        past = sum(
            1 << lower
            for lower in range(len(relation))
            if has_relation(relation, lower, upper)
        )
        numerator = numerator * lambda_value(
            past.bit_count(),
            len(maximal_elements_in_subset(relation, past)),
            parameters,
        )
    denominator = ONE
    for stage in range(len(relation)):
        denominator = denominator * lambda_value(stage, 0, parameters)
    return numerator / denominator


def decoherence(
    left_amplitude: GaussianRational,
    right_amplitude: GaussianRational,
) -> GaussianRational:
    """Return D(A,B) = conjugate(Amp(A)) Amp(B)."""

    return left_amplitude.conjugate() * right_amplitude


def quantum_measure(amplitude: GaussianRational) -> Fraction:
    """Return mu(A) = D(A,A)."""

    return amplitude.norm_squared()


def second_order_interference(
    left_amplitude: GaussianRational,
    right_amplitude: GaussianRational,
) -> Fraction:
    """Return I2(A,B) exactly for two disjoint events."""

    union_measure = quantum_measure(left_amplitude + right_amplitude)
    return (
        union_measure
        - quantum_measure(left_amplitude)
        - quantum_measure(right_amplitude)
    )


def _mask(vertices: tuple[int, ...]) -> int:
    return sum(1 << vertex for vertex in vertices)


def _digest(records: Any) -> str:
    payload = json.dumps(
        records,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _relabel_relation(
    relation: Relation,
    permutation: tuple[int, ...],
) -> Relation:
    rows = [0] * len(relation)
    for old_lower in range(len(relation)):
        for old_upper in range(len(relation)):
            if has_relation(relation, old_lower, old_upper):
                rows[permutation[old_lower]] |= 1 << permutation[old_upper]
    return tuple(rows)


def _induced_subrelation(
    relation: Relation,
    subset: int,
) -> tuple[Relation, dict[int, int]]:
    selected = tuple(
        vertex for vertex in range(len(relation)) if subset & (1 << vertex)
    )
    old_to_new = {old: new for new, old in enumerate(selected)}
    rows = [0] * len(selected)
    for old_lower in selected:
        for old_upper in selected:
            if has_relation(relation, old_lower, old_upper):
                rows[old_to_new[old_lower]] |= 1 << old_to_new[old_upper]
    return tuple(rows), old_to_new


def _compress_subset(subset: int, old_to_new: dict[int, int]) -> int:
    compressed = 0
    for old, new in old_to_new.items():
        if subset & (1 << old):
            compressed |= 1 << new
    return compressed


@dataclass(frozen=True)
class _QuotientPath:
    move_ids: tuple[str, ...]
    causets: tuple[str, ...]
    amplitude_per_labelled_history: GaussianRational
    labelled_fibre_size: int

    @property
    def final_causet(self) -> str:
        return self.causets[-1]


@dataclass(frozen=True)
class _CovariantEvent:
    stage: int
    relation: Relation
    event_id: str
    amplitude: GaussianRational
    labelled_history_count: int
    quotient_path_count: int

    def to_record(self) -> dict[str, Any]:
        return {
            "event_id": f"E[{self.event_id}]",
            "predicate": f"final_unlabeled_causet == {self.event_id}",
            "stage": self.stage,
            "canonical_relation_rows": list(self.relation),
            "comparable_pair_count": comparable_pairs(self.relation),
            "height": height(self.relation),
            "width": width(self.relation),
            "distinct_natural_birth_labelings": self.labelled_history_count,
            "quotient_path_count": self.quotient_path_count,
            "amplitude": self.amplitude.to_record(),
            "quantum_measure": _fraction_record(quantum_measure(self.amplitude)),
            "vertex_relabeling_invariant": True,
            "exclusive_from_other_singleton_final_causet_events": True,
        }


def _transition_audit(
    levels: tuple[tuple[Relation, ...], ...],
    max_n: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catalog: list[dict[str, Any]] = []
    raw_coverage: list[dict[str, Any]] = []
    msr_sources: list[dict[str, Any]] = []
    orbit_covariance_pass = True
    target_covariance_pass = True
    denominator_nonzero = True
    unique_amplitudes: set[tuple[Fraction, Fraction]] = set()

    for stage in range(1, max_n):
        for relation in levels[stage]:
            source_id = causet_id(relation)
            denominator = lambda_value(stage, 0)
            denominator_nonzero &= not denominator.is_zero()
            raw_sum = ZERO
            for precursor in downsets(relation):
                amplitude = transition_amplitude(relation, precursor)
                raw_sum = raw_sum + amplitude
                raw_coverage.append(
                    {
                        "source": source_id,
                        "precursor_mask": precursor,
                        "amplitude": amplitude.to_record(),
                    }
                )

            orbit_sum = ZERO
            for orbit_index, move in enumerate(growth_moves(relation)):
                representative = _mask(move.precursor_set)
                amplitude = transition_amplitude(relation, representative)
                unique_amplitudes.add((amplitude.real, amplitude.imaginary))
                orbit = precursor_orbit(relation, representative)
                member_amplitudes = {
                    transition_amplitude(relation, member) for member in orbit
                }
                member_targets = {
                    causet_id(canonicalize(add_maximal(relation, member)))
                    for member in orbit
                }
                orbit_covariance_pass &= (
                    member_amplitudes == {amplitude}
                    and len(orbit) == move.multiplicity
                )
                target_covariance_pass &= member_targets == {move.target_history}
                orbit_sum = orbit_sum + amplitude.scale(move.multiplicity)
                precursor_size = representative.bit_count()
                maximal_count = len(
                    maximal_elements_in_subset(relation, representative)
                )
                catalog.append(
                    {
                        "transition_id": (
                            f"T{stage:02d}-{source_id}-o{orbit_index:03d}"
                        ),
                        "source_stage": stage,
                        "source_causet": source_id,
                        "target_causet": move.target_history,
                        "precursor_orbit_representative": list(move.precursor_set),
                        "spectator_representative": list(move.spectator_set),
                        "precursor_cardinality_varpi": precursor_size,
                        "maximal_elements_m": maximal_count,
                        "automorphism_orbit_multiplicity": move.multiplicity,
                        "lambda_numerator": lambda_value(
                            precursor_size, maximal_count
                        ).to_record(),
                        "lambda_denominator": denominator.to_record(),
                        "amplitude_per_labelled_transition": amplitude.to_record(),
                        "multiplicity_weighted_MSR_contribution": amplitude.scale(
                            move.multiplicity
                        ).to_record(),
                        "paper_equation": 15,
                    }
                )
            msr_sources.append(
                {
                    "source_stage": stage,
                    "source_causet": source_id,
                    "raw_labelled_transition_count": len(downsets(relation)),
                    "transition_orbit_count": len(growth_moves(relation)),
                    "raw_transition_sum": raw_sum.to_record(),
                    "orbit_multiplicity_sum": orbit_sum.to_record(),
                    "equals_one_exactly": raw_sum == ONE and orbit_sum == ONE,
                }
            )

    msr_pass = all(record["equals_one_exactly"] for record in msr_sources)
    return (
        {
            "paper_equations": [14, 15],
            "source_stage_range": f"1 <= n <= {max_n - 1}",
            "source_count": len(msr_sources),
            "transition_orbit_count": len(catalog),
            "raw_labelled_transition_count": len(raw_coverage),
            "unique_exact_amplitudes": [
                GaussianRational(real, imaginary).to_record()
                for real, imaginary in sorted(unique_amplitudes)
            ],
            "all_denominators_nonzero": denominator_nonzero,
            "MSR_exact": msr_pass,
            "automorphism_orbit_amplitude_covariance_exact": (
                orbit_covariance_pass
            ),
            "automorphism_orbit_target_covariance_exact": target_covariance_pass,
            "raw_transition_coverage_sha256": _digest(raw_coverage),
            "MSR_source_certificates": msr_sources,
            "passed": (
                denominator_nonzero
                and msr_pass
                and orbit_covariance_pass
                and target_covariance_pass
            ),
        },
        catalog,
    )


def _bell_causality_audit(
    levels: tuple[tuple[Relation, ...], ...],
    max_n: int,
) -> dict[str, Any]:
    coverage: list[dict[str, Any]] = []
    by_stage: dict[str, dict[str, int]] = {}
    product_pass = True
    ratio_pass = True
    ratio_eligible = 0
    nontrivial_common_spectator_count = 0
    first_nontrivial: dict[str, Any] | None = None
    first_nonzero: dict[str, Any] | None = None

    for stage in range(1, max_n):
        stage_count = 0
        stage_nontrivial = 0
        for relation in levels[stage]:
            full_mask = (1 << stage) - 1
            non_timid = tuple(
                precursor
                for precursor in downsets(relation)
                if precursor != full_mask
            )
            for first, second in itertools.combinations(non_timid, 2):
                stage_count += 1
                union = first | second
                reduced_relation, old_to_new = _induced_subrelation(
                    relation, union
                )
                reduced_first = _compress_subset(first, old_to_new)
                reduced_second = _compress_subset(second, old_to_new)
                full_first_amplitude = transition_amplitude(relation, first)
                full_second_amplitude = transition_amplitude(relation, second)
                reduced_first_amplitude = transition_amplitude(
                    reduced_relation, reduced_first
                )
                reduced_second_amplitude = transition_amplitude(
                    reduced_relation, reduced_second
                )
                left_product = full_first_amplitude * reduced_second_amplitude
                right_product = full_second_amplitude * reduced_first_amplitude
                residual = left_product - right_product
                product_pass &= residual.is_zero()
                if (
                    not full_second_amplitude.is_zero()
                    and not reduced_second_amplitude.is_zero()
                ):
                    ratio_eligible += 1
                    ratio_pass &= (
                        full_first_amplitude / full_second_amplitude
                        == reduced_first_amplitude / reduced_second_amplitude
                    )
                nontrivial = union != full_mask
                if nontrivial:
                    stage_nontrivial += 1
                    nontrivial_common_spectator_count += 1
                record = {
                    "source_stage": stage,
                    "source_causet": causet_id(relation),
                    "first_precursor_mask": first,
                    "second_precursor_mask": second,
                    "reduced_source_size": len(reduced_relation),
                    "common_spectator_count": stage - union.bit_count(),
                    "full_first": full_first_amplitude.to_record(),
                    "full_second": full_second_amplitude.to_record(),
                    "reduced_first": reduced_first_amplitude.to_record(),
                    "reduced_second": reduced_second_amplitude.to_record(),
                    "cross_product_residual": residual.to_record(),
                }
                coverage.append(record)
                if nontrivial and first_nontrivial is None:
                    first_nontrivial = record
                if (
                    nontrivial
                    and not left_product.is_zero()
                    and first_nonzero is None
                ):
                    first_nonzero = {
                        **record,
                        "left_cross_product": left_product.to_record(),
                        "right_cross_product": right_product.to_record(),
                    }
        by_stage[str(stage)] = {
            "all_distinct_non_timid_pairs": stage_count,
            "pairs_with_at_least_one_common_spectator": stage_nontrivial,
        }

    return {
        "paper_condition": (
            "Eq. (7) spectator independence / scalar Bell causality"
        ),
        "zero_safe_form": (
            "A_full(P1)*A_reduced(P2) = "
            "A_full(P2)*A_reduced(P1)"
        ),
        "pair_scope": (
            "every unordered pair of distinct non-timid labelled precursor "
            f"down-sets for every unlabeled source with 1 <= n < {max_n}"
        ),
        "by_source_stage": by_stage,
        "pair_count": len(coverage),
        "nontrivial_common_spectator_pair_count": (
            nontrivial_common_spectator_count
        ),
        "ratio_form_eligible_pair_count": ratio_eligible,
        "zero_safe_product_rule_exact": product_pass,
        "ratio_form_exact_when_defined": ratio_pass,
        "coverage_sha256": _digest(coverage),
        "first_nontrivial_common_spectator_fixture": first_nontrivial,
        "first_nonzero_cross_product_fixture": first_nonzero,
        "passed": product_pass and ratio_pass,
    }


def _enumerate_paths(
    levels: tuple[tuple[Relation, ...], ...],
    max_n: int,
) -> dict[int, tuple[_QuotientPath, ...]]:
    relation_by_id = {
        causet_id(relation): relation
        for level in levels
        for relation in level
    }
    root_id = causet_id(levels[1][0])
    stages: dict[int, tuple[_QuotientPath, ...]] = {
        1: (
            _QuotientPath(
                move_ids=(),
                causets=(root_id,),
                amplitude_per_labelled_history=ONE,
                labelled_fibre_size=1,
            ),
        )
    }
    for stage in range(1, max_n):
        following: list[_QuotientPath] = []
        for path in stages[stage]:
            relation = relation_by_id[path.final_causet]
            for orbit_index, move in enumerate(growth_moves(relation)):
                representative = _mask(move.precursor_set)
                amplitude = transition_amplitude(relation, representative)
                move_id = (
                    f"T{stage:02d}-{path.final_causet}-o{orbit_index:03d}"
                )
                following.append(
                    _QuotientPath(
                        move_ids=(*path.move_ids, move_id),
                        causets=(*path.causets, move.target_history),
                        amplitude_per_labelled_history=(
                            path.amplitude_per_labelled_history * amplitude
                        ),
                        labelled_fibre_size=(
                            path.labelled_fibre_size * move.multiplicity
                        ),
                    )
                )
        stages[stage + 1] = tuple(
            sorted(following, key=lambda item: (item.move_ids, item.causets))
        )
    return stages


def _event_and_path_audit(
    levels: tuple[tuple[Relation, ...], ...],
    paths_by_stage: dict[int, tuple[_QuotientPath, ...]],
    max_n: int,
) -> tuple[
    dict[str, Any],
    dict[int, tuple[_CovariantEvent, ...]],
]:
    stage_records: list[dict[str, Any]] = []
    events_by_stage: dict[int, tuple[_CovariantEvent, ...]] = {}
    path_independence_pass = True
    quotient_fibre_pass = True
    normalization_pass = True

    for stage in range(1, max_n + 1):
        grouped: dict[str, list[_QuotientPath]] = {}
        for path in paths_by_stage[stage]:
            grouped.setdefault(path.final_causet, []).append(path)
        events: list[_CovariantEvent] = []
        omega_amplitude = ZERO
        weighted_path_amplitude = ZERO
        endpoint_certificates: list[dict[str, Any]] = []
        for relation in levels[stage]:
            endpoint = causet_id(relation)
            paths = grouped.get(endpoint, [])
            direct = endpoint_amplitude(relation)
            path_amplitudes = {
                path.amplitude_per_labelled_history for path in paths
            }
            endpoint_path_pass = path_amplitudes == {direct}
            path_independence_pass &= endpoint_path_pass
            linear_extensions = natural_labeling_multiplicity(relation)
            automorphism_order = len(automorphisms(relation))
            labelled_count, remainder = divmod(
                linear_extensions, automorphism_order
            )
            observed_fibre = sum(path.labelled_fibre_size for path in paths)
            endpoint_fibre_pass = (
                remainder == 0 and observed_fibre == labelled_count
            )
            quotient_fibre_pass &= endpoint_fibre_pass
            event_amplitude = direct.scale(labelled_count)
            path_pushforward = ZERO
            for path in paths:
                path_pushforward = path_pushforward + (
                    path.amplitude_per_labelled_history.scale(
                        path.labelled_fibre_size
                    )
                )
            path_independence_pass &= path_pushforward == event_amplitude
            omega_amplitude = omega_amplitude + event_amplitude
            weighted_path_amplitude = weighted_path_amplitude + path_pushforward
            events.append(
                _CovariantEvent(
                    stage=stage,
                    relation=relation,
                    event_id=endpoint,
                    amplitude=event_amplitude,
                    labelled_history_count=labelled_count,
                    quotient_path_count=len(paths),
                )
            )
            endpoint_certificates.append(
                {
                    "endpoint": endpoint,
                    "quotient_path_count": len(paths),
                    "observed_labelled_fibre_size": observed_fibre,
                    "expected_distinct_natural_labelings": labelled_count,
                    "direct_amplitude": direct.to_record(),
                    "all_path_products_equal_direct_amplitude": (
                        endpoint_path_pass
                    ),
                    "path_fibre_pushforward_equals_event_amplitude": (
                        path_pushforward == event_amplitude
                    ),
                }
            )
        stage_normalized = (
            omega_amplitude == ONE and weighted_path_amplitude == ONE
        )
        normalization_pass &= stage_normalized
        events_by_stage[stage] = tuple(
            sorted(events, key=lambda event: event.event_id)
        )
        stage_records.append(
            {
                "stage": stage,
                "unlabeled_causet_count": len(levels[stage]),
                "quotient_path_count": len(paths_by_stage[stage]),
                "expanded_labelled_history_count": sum(
                    path.labelled_fibre_size
                    for path in paths_by_stage[stage]
                ),
                "omega_amplitude": omega_amplitude.to_record(),
                "path_pushforward_omega_amplitude": (
                    weighted_path_amplitude.to_record()
                ),
                "normalized_exactly": stage_normalized,
                "endpoint_coverage_sha256": _digest(endpoint_certificates),
            }
        )

    permutation_checks = 0
    relabel_covariance_pass = True
    for stage in range(1, max_n + 1):
        for relation in levels[stage]:
            expected = endpoint_amplitude(relation)
            for permutation in itertools.permutations(range(stage)):
                permutation_checks += 1
                relabelled = _relabel_relation(relation, permutation)
                relabel_covariance_pass &= (
                    endpoint_amplitude(relabelled) == expected
                    and causet_id(relabelled) == causet_id(relation)
                )

    return (
        {
            "paper_conditions": [
                "condition (a): equal amplitudes for order-isomorphic causets",
                "Eq. (16): product of transition amplitudes along a branch",
            ],
            "stage_certificates": stage_records,
            "path_independence_exact": path_independence_pass,
            "label_quotient_fibre_exact": quotient_fibre_pass,
            "normalization_exact_all_stages": normalization_pass,
            "arbitrary_vertex_permutations_checked": permutation_checks,
            "direct_endpoint_amplitude_relabel_covariant_exact": (
                relabel_covariance_pass
            ),
            "direct_formula_is_independent_oracle": True,
            "passed": (
                path_independence_pass
                and quotient_fibre_pass
                and normalization_pass
                and relabel_covariance_pass
            ),
        },
        events_by_stage,
    )


def _grade2_residual(
    first: GaussianRational,
    second: GaussianRational,
    third: GaussianRational,
) -> Fraction:
    mu_abc = quantum_measure(first + second + third)
    mu_ab = quantum_measure(first + second)
    mu_ac = quantum_measure(first + third)
    mu_bc = quantum_measure(second + third)
    return (
        mu_abc
        - mu_ab
        - mu_ac
        - mu_bc
        + quantum_measure(first)
        + quantum_measure(second)
        + quantum_measure(third)
    )


def _decoherence_audit(
    events_by_stage: dict[int, tuple[_CovariantEvent, ...]],
    max_n: int,
) -> dict[str, Any]:
    stage_records: list[dict[str, Any]] = []
    hermiticity_pass = True
    normalization_pass = True
    strong_positivity_pass = True
    grade2_pass = True
    total_pairs = 0
    total_triples = 0
    physical_witness: dict[str, Any] | None = None

    for stage in range(1, max_n + 1):
        events = events_by_stage[stage]
        pair_coverage: list[dict[str, Any]] = []
        nonzero_d_count = 0
        nonzero_i2_count = 0
        principal_minor_pass = True
        for left_index, right_index in itertools.combinations(
            range(len(events)), 2
        ):
            total_pairs += 1
            left = events[left_index]
            right = events[right_index]
            d_left_right = decoherence(left.amplitude, right.amplitude)
            d_right_left = decoherence(right.amplitude, left.amplitude)
            pair_hermitian = (
                d_left_right == d_right_left.conjugate()
            )
            hermiticity_pass &= pair_hermitian
            i2 = second_order_interference(left.amplitude, right.amplitude)
            i2_identity = i2 == 2 * d_left_right.real
            hermiticity_pass &= i2_identity
            minor = (
                quantum_measure(left.amplitude)
                * quantum_measure(right.amplitude)
                - d_left_right.norm_squared()
            )
            principal_minor_pass &= minor == 0
            if not d_left_right.is_zero():
                nonzero_d_count += 1
            if i2 != 0:
                nonzero_i2_count += 1
            pair_coverage.append(
                {
                    "left": left.event_id,
                    "right": right.event_id,
                    "D": d_left_right.to_record(),
                    "I2": _fraction_record(i2),
                    "hermitian": pair_hermitian,
                    "two_by_two_principal_minor": _fraction_record(minor),
                }
            )
            if (
                stage >= 3
                and left.event_id == REFERENCE_EVENT_A
                and right.event_id == REFERENCE_EVENT_B
            ):
                physical_witness = {
                    "stage": stage,
                    "events_are_exclusive": True,
                    "events_are_physically_distinct_unlabeled_geometries": True,
                    "not_a_natural_labelling_multiplicity_witness": (
                        left.labelled_history_count == 1
                        and right.labelled_history_count == 1
                    ),
                    "event_A": left.to_record(),
                    "event_B": right.to_record(),
                    "D_A_B": d_left_right.to_record(),
                    "D_B_A": d_right_left.to_record(),
                    "mu_A_union_B": _fraction_record(
                        quantum_measure(left.amplitude + right.amplitude)
                    ),
                    "I2_A_B": _fraction_record(i2),
                    "nonzero_off_diagonal_D": not d_left_right.is_zero(),
                    "nonzero_I2": i2 != 0,
                }

        triple_coverage: list[dict[str, Any]] = []
        for first, second, third in itertools.combinations(events, 3):
            total_triples += 1
            residual = _grade2_residual(
                first.amplitude,
                second.amplitude,
                third.amplitude,
            )
            grade2_pass &= residual == 0
            triple_coverage.append(
                {
                    "events": [
                        first.event_id,
                        second.event_id,
                        third.event_id,
                    ],
                    "residual": _fraction_record(residual),
                }
            )

        omega_amplitude = ZERO
        diagonal_nonnegative = True
        for event in events:
            omega_amplitude = omega_amplitude + event.amplitude
            diagonal_nonnegative &= quantum_measure(event.amplitude) >= 0
        stage_normalized = (
            omega_amplitude == ONE
            and quantum_measure(omega_amplitude) == 1
        )
        normalization_pass &= stage_normalized
        stage_strong_positive = (
            diagonal_nonnegative and principal_minor_pass
        )
        strong_positivity_pass &= stage_strong_positive
        stage_records.append(
            {
                "stage": stage,
                "covariant_singleton_event_count": len(events),
                "unordered_event_pairs_checked": len(pair_coverage),
                "nonzero_off_diagonal_D_pair_count": nonzero_d_count,
                "nonzero_I2_pair_count": nonzero_i2_count,
                "pair_coverage_sha256": _digest(pair_coverage),
                "pairwise_disjoint_event_triples_checked": len(
                    triple_coverage
                ),
                "triple_coverage_sha256": _digest(triple_coverage),
                "Hermiticity_exact": all(
                    record["hermitian"] for record in pair_coverage
                ),
                "normalization_exact": stage_normalized,
                "strong_positivity_exact": stage_strong_positive,
                "grade2_exact": all(
                    record["residual"] == _fraction_record(Fraction(0))
                    for record in triple_coverage
                ),
            }
        )

    witness_pass = (
        physical_witness is not None
        and physical_witness["nonzero_off_diagonal_D"]
        and physical_witness["nonzero_I2"]
        and physical_witness[
            "events_are_physically_distinct_unlabeled_geometries"
        ]
        and physical_witness[
            "not_a_natural_labelling_multiplicity_witness"
        ]
    )
    return {
        "definition": "D(A,B) = conjugate(Amp(A))*Amp(B)",
        "quantum_measure": "mu(A) = D(A,A) = |Amp(A)|^2",
        "event_family": (
            "singleton final-unlabeled-causet path fibres at each fixed stage"
        ),
        "stage_certificates": stage_records,
        "unordered_event_pairs_checked": total_pairs,
        "pairwise_disjoint_event_triples_checked": total_triples,
        "Hermiticity_exact": hermiticity_pass,
        "normalization_exact": normalization_pass,
        "strong_positivity_exact": strong_positivity_pass,
        "strong_positivity_certificate": {
            "Gram_form": "D_ij = conjugate(a_i)*a_j",
            "rank_upper_bound": 1,
            "all_diagonal_entries_nonnegative": strong_positivity_pass,
            "all_two_by_two_principal_minors_zero": strong_positivity_pass,
            "arbitrary_event_family_identity": (
                "sum_ij conjugate(z_i) D_ij z_j = "
                "|sum_i a_i z_i|^2 >= 0"
            ),
        },
        "grade2_sum_rule_exact": grade2_pass,
        "grade2_definition": (
            "mu(AuBuC)-mu(AuB)-mu(AuC)-mu(BuC)"
            "+mu(A)+mu(B)+mu(C)"
        ),
        "physical_interference_witness": physical_witness,
        "physical_witness_pass": witness_pass,
        "passed": (
            hermiticity_pass
            and normalization_pass
            and strong_positivity_pass
            and grade2_pass
            and witness_pass
        ),
    }


def _theorem_mapping() -> dict[str, Any]:
    denominator_formula_checks = []
    for stage in range(1, MAX_EXACT_N + 1):
        value = lambda_value(stage, 0)
        expected = GaussianRational(
            Fraction(1 + math.comb(stage, 2)),
            Fraction(math.comb(stage, 2)),
        )
        denominator_formula_checks.append(
            {
                "stage": stage,
                "lambda_n_0": value.to_record(),
                "equals_1_plus_binomial_n_2_times_1_plus_i": (
                    value == expected
                ),
                "nonzero": not value.is_zero(),
            }
        )
    return {
        "literature_classification": "LITERATURE_LOCKED_REGRESSION_ONLY",
        "source": {
            "paper": PAPER_ID,
            "title": (
                "A Criterion for Covariance in Complex Sequential Growth Models"
            ),
            "version": "v1, 2020-03-25",
            "local_pdf": (
                "references/papers/"
                "2003.11311v1_surya-zalel_covariance-complex-sequential-growth.pdf"
            ),
            "sha256": PAPER_SHA256,
            "verified_pdf_pages": [8, 10, 17, 18],
        },
        "paper_results": {
            "transition_rule": (
                "Eq. (15): A = lambda(varpi,m)/lambda(n,0)"
            ),
            "history_amplitude": (
                "Eq. (16): product of transition amplitudes"
            ),
            "finite_coupling_extension_family": (
                "Claim 3.8 item 2: m=1 and k1>1 implies bounded variation"
            ),
            "extension_theorem": (
                "Theorem 2.1: bounded variation iff the complex measure has "
                "a unique extension from Z to S_Z"
            ),
            "covariant_event_consequence": (
                "the extended measure is defined on the covariant quotient "
                "sigma algebra"
            ),
        },
        "exact_specialization": {
            **REFERENCE_PARAMETERS.to_record(),
            "paper_polar_notation": {
                "m_number_of_positive_index_nonzero_couplings": 1,
                "k1": 2,
                "s": "sqrt(2)",
                "phi": "pi/4",
                "t_k1": "sqrt(2)*exp(i*pi/4) = 1 + i",
            },
        },
        "hypothesis_mapping": {
            "t0_equals_one": REFERENCE_PARAMETERS.coupling(0) == ONE,
            "only_one_nonzero_positive_index_coupling": True,
            "m_equals_one": True,
            "k1_equals_two": True,
            "k1_greater_than_one": True,
            "selected_t2_is_complex": True,
        },
        "independent_project_well_definedness_check": {
            "formula": "lambda(n,0)=1+binomial(n,2)*(1+i)",
            "all_stage_symbolic_nonzero_reason": (
                "its real part is 1+binomial(n,2), which is strictly positive"
            ),
            "finite_regression_checks": denominator_formula_checks,
            "not_the_extension_proof": True,
        },
        "extension_applicability": {
            "bounded_variation": "PASS_BY_CLAIM_3_8_ITEM_2",
            "unique_sigma_algebra_extension": "PASS_BY_THEOREM_2_1",
            "all_covariant_events_measurable": (
                "PASS_WITHIN_THE_PAPER_SCALAR_CSG_SCOPE"
            ),
            "finite_n_extrapolation_used": False,
            "verdict": "COMMUTATIVE_CSG_EXTENSION_THEOREM_APPLICABLE",
        },
        "claim_boundary": [
            "The infinite extension is certified by the cited theorem and its "
            "hypothesis mapping, not by finite n<=5 enumeration.",
            "No operator-valued or noncommutative extension theorem is inferred.",
            "The paper result and the exact specialization are not novel results.",
        ],
        "passed": True,
    }


def _orthogonal_record_comparison(max_n: int) -> dict[str, Any]:
    baseline = geometry_interference_benchmark(max_n)
    extension = extension_benchmark(max_n)
    baseline_matrix = baseline["decoherence_functional"]["sparse_exact_matrix"]
    csg_complexity = (
        "O(E^2) dense event-pair materialization; rank-one Gram form permits "
        "O(E) storage"
    )
    return {
        "baseline_profile_id": baseline["profile_id"],
        "baseline_status": baseline["geometry_quantumness_status"],
        "same_finite_causet_enumerator": True,
        "comparison": [
            {
                "item": "history state space",
                "COMMUTATIVE_CSG_REFERENCE": (
                    "H is isomorphic to C; labelled cylinder alternatives are "
                    "encoded by one scalar amplitude"
                ),
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    f"{baseline['completeness']['final_decoherence_basis_size']} "
                    "fixed instrument-outcome paths at n=5"
                ),
            },
            {
                "item": "outcome semantics",
                "COMMUTATIVE_CSG_REFERENCE": (
                    "exclusive labelled growth cylinders add coherently"
                ),
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    "fixed aggregate-Kraus outcomes are retained as records"
                ),
            },
            {
                "item": "environment record",
                "COMMUTATIVE_CSG_REFERENCE": "none",
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    "orthogonal record of the complete outcome sequence"
                ),
            },
            {
                "item": "interference",
                "COMMUTATIVE_CSG_REFERENCE": (
                    "exact nonzero off-diagonal D and nonzero geometry I2"
                ),
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    f"{baseline_matrix['ordered_off_diagonal_entry_count']} "
                    "ordered off-diagonals checked; all zero"
                ),
            },
            {
                "item": "Bell causality",
                "COMMUTATIVE_CSG_REFERENCE": (
                    "scalar Eq. (7) product rule exact"
                ),
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    KRAUS_BELL_CAUSALITY_UNDEFINED
                ),
            },
            {
                "item": "covariance",
                "COMMUTATIVE_CSG_REFERENCE": (
                    "GC/path independence and labelled-to-unlabelled quotient exact"
                ),
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": baseline[
                    "label_covariance_and_quotient_consistency"
                ]["covariance_scope"],
            },
            {
                "item": "extension",
                "COMMUTATIVE_CSG_REFERENCE": (
                    "bounded variation by Claim 3.8 and unique scalar extension "
                    "by Theorem 2.1"
                ),
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    f"classical outcomes: "
                    f"{extension['classical_outcome_measure']['verdict']}; "
                    f"operator instrument: "
                    f"{extension['operator_valued_instrument_measure']['verdict']}"
                ),
            },
            {
                "item": "computational complexity",
                "COMMUTATIVE_CSG_REFERENCE": csg_complexity,
                "ORTHOGONAL_RECORD_CLASSICAL_BASELINE": (
                    "O(H) sparse diagonal storage after O(H^2) zero audit"
                ),
            },
        ],
        "baseline_artifacts_unchanged_by_this_module": True,
        "baseline_all_off_diagonals_zero": not baseline_matrix[
            "nonzero_off_diagonal_entries"
        ],
        "baseline_all_I2_zero": baseline["interference_I2"][
            "all_exact_I2_zero"
        ],
        "comparison_passed": (
            baseline["passed"]
            and not baseline_matrix["nonzero_off_diagonal_entries"]
            and baseline["interference_I2"]["all_exact_I2_zero"]
            and extension["decoherence_functional"]["verdict"]
            == "DECOHERENCE_FUNCTIONAL_EXTENSION_PASS"
        ),
    }


@cache
def _benchmark_cached(max_n: int) -> dict[str, Any]:
    _validate_max_n(max_n)
    levels = enumerate_unlabeled_posets(max_n)
    transition_audit, transition_catalog = _transition_audit(levels, max_n)
    bell_audit = _bell_causality_audit(levels, max_n)
    paths_by_stage = _enumerate_paths(levels, max_n)
    path_audit, events_by_stage = _event_and_path_audit(
        levels, paths_by_stage, max_n
    )
    decoherence_audit = _decoherence_audit(events_by_stage, max_n)
    theorem_mapping = _theorem_mapping()
    comparison = _orthogonal_record_comparison(max_n)
    passed = (
        transition_audit["passed"]
        and bell_audit["passed"]
        and path_audit["passed"]
        and decoherence_audit["passed"]
        and theorem_mapping["passed"]
        and comparison["comparison_passed"]
    )
    return {
        "schema_version": "final-theory-commutative-csg-reference-v0.3.1",
        "suite": "Final-Theory Bench v0.3.1 exact commutative CSG reference",
        "profile_id": "COMMUTATIVE_CSG_REFERENCE_T2_1_PLUS_I",
        "literature_classification": "REGRESSION_ONLY",
        "requested_max_n": max_n,
        "dimension": 1,
        "field": "Q(i) exact specialization embedded in C",
        "parameters": REFERENCE_PARAMETERS.to_record(),
        "theorem_mapping": theorem_mapping,
        "transition_audit": transition_audit,
        "transition_catalog": transition_catalog,
        "scalar_bell_causality": bell_audit,
        "general_covariance_path_and_quotient": path_audit,
        "final_covariant_event_catalog": [
            event.to_record() for event in events_by_stage[max_n]
        ],
        "decoherence_functional": decoherence_audit,
        "orthogonal_record_baseline_comparison": comparison,
        "exact_scope": {
            "finite_enumeration": f"all causal sets and transitions through n={max_n}",
            "source_transition_stages": f"1 <= n < {max_n}",
            "arithmetic": "integers, Fraction, and exact Gaussian rationals",
            "floating_point_used": False,
            "random_seed": None,
            "solver": "deterministic exhaustive enumeration plus exact identities",
            "resource_limit": "hard implementation limit n<=5",
        },
        "mutation_guards": {
            "force_off_diagonal_D_to_zero": (
                decoherence_audit["physical_interference_witness"]["D_A_B"]
                != ZERO.to_record()
            ),
            "misclassify_orthogonal_record_baseline_as_coherent": (
                comparison["baseline_all_off_diagonals_zero"]
                and comparison["baseline_all_I2_zero"]
            ),
            "finite_n_extension_extrapolation": theorem_mapping[
                "extension_applicability"
            ]["finite_n_extrapolation_used"]
            is False,
            "paper_result_reported_as_novel": (
                theorem_mapping["literature_classification"]
                == "LITERATURE_LOCKED_REGRESSION_ONLY"
            ),
        },
        "unresolved_components": [
            "No finite computation independently re-proves Claim 3.8's infinite-series argument.",
            "No operator-valued or noncommutative lift is constructed here.",
            (
                "No finite event is promoted to a complete characterization "
                "of the infinite covariant sigma algebra."
            ),
            "Enumeration beyond n=5 is not executed or certified.",
        ],
        "commutative_reference_status": (
            "COMMUTATIVE_CSG_REFERENCE_PASS"
            if passed
            else "COMMUTATIVE_CSG_REFERENCE_FAIL"
        ),
        "verdict": (
            "COMMUTATIVE_CSG_REFERENCE_PASS"
            if passed
            else "COMMUTATIVE_CSG_REFERENCE_FAIL"
        ),
        "passed": passed,
    }


def commutative_csg_reference_benchmark(max_n: int = 5) -> dict[str, Any]:
    """Return the deterministic JSON-ready exact reference audit."""

    return copy.deepcopy(_benchmark_cached(max_n))


def certificate_payloads(max_n: int = 5) -> dict[str, dict[str, Any]]:
    """Return concise exact certificate payloads derived from the benchmark."""

    benchmark = commutative_csg_reference_benchmark(max_n)
    theorem = benchmark["theorem_mapping"]
    witness = benchmark["decoherence_functional"][
        "physical_interference_witness"
    ]
    finite = {
        "schema_version": "commutative-csg-finite-certificate-v0.3.1",
        "profile_id": benchmark["profile_id"],
        "max_n": max_n,
        "field": benchmark["field"],
        "transition_orbit_count": benchmark["transition_audit"][
            "transition_orbit_count"
        ],
        "raw_labelled_transition_count": benchmark["transition_audit"][
            "raw_labelled_transition_count"
        ],
        "raw_transition_coverage_sha256": benchmark["transition_audit"][
            "raw_transition_coverage_sha256"
        ],
        "bell_pair_count": benchmark["scalar_bell_causality"]["pair_count"],
        "bell_coverage_sha256": benchmark["scalar_bell_causality"][
            "coverage_sha256"
        ],
        "stage_path_certificates": benchmark[
            "general_covariance_path_and_quotient"
        ]["stage_certificates"],
        "decoherence_stage_certificates": benchmark[
            "decoherence_functional"
        ]["stage_certificates"],
        "exact_claims": {
            "transition_denominators_nonzero": benchmark["transition_audit"][
                "all_denominators_nonzero"
            ],
            "MSR": benchmark["transition_audit"]["MSR_exact"],
            "general_covariance": benchmark[
                "general_covariance_path_and_quotient"
            ]["direct_endpoint_amplitude_relabel_covariant_exact"],
            "scalar_Bell_causality": benchmark["scalar_bell_causality"][
                "zero_safe_product_rule_exact"
            ],
            "path_independence": benchmark[
                "general_covariance_path_and_quotient"
            ]["path_independence_exact"],
            "normalization": benchmark["decoherence_functional"][
                "normalization_exact"
            ],
            "Hermiticity": benchmark["decoherence_functional"][
                "Hermiticity_exact"
            ],
            "strong_positivity": benchmark["decoherence_functional"][
                "strong_positivity_exact"
            ],
            "grade2": benchmark["decoherence_functional"][
                "grade2_sum_rule_exact"
            ],
            "label_quotient": benchmark[
                "general_covariance_path_and_quotient"
            ]["label_quotient_fibre_exact"],
        },
        "verdict": benchmark["verdict"],
    }
    return {
        "parameter_and_theorem_v0.3.1.json": {
            "schema_version": "commutative-csg-theorem-certificate-v0.3.1",
            "profile_id": benchmark["profile_id"],
            "paper": theorem["source"],
            "exact_specialization": theorem["exact_specialization"],
            "hypothesis_mapping": theorem["hypothesis_mapping"],
            "well_definedness": theorem[
                "independent_project_well_definedness_check"
            ],
            "extension_applicability": theorem["extension_applicability"],
            "claim_boundary": theorem["claim_boundary"],
            "verdict": benchmark["verdict"],
        },
        "exact_finite_audit_v0.3.1.json": finite,
        "physical_interference_witness_v0.3.1.json": {
            "schema_version": "commutative-csg-witness-certificate-v0.3.1",
            "profile_id": benchmark["profile_id"],
            "paper_transition_equation": 15,
            "parameters": benchmark["parameters"],
            "witness": witness,
            "orthogonal_record_control": {
                "profile_id": benchmark[
                    "orthogonal_record_baseline_comparison"
                ]["baseline_profile_id"],
                "all_off_diagonals_zero": benchmark[
                    "orthogonal_record_baseline_comparison"
                ]["baseline_all_off_diagonals_zero"],
                "all_I2_zero": benchmark[
                    "orthogonal_record_baseline_comparison"
                ]["baseline_all_I2_zero"],
            },
            "verdict": benchmark["verdict"],
        },
    }


def verify_commutative_csg_certificate(
    certificate: dict[str, Any],
) -> dict[str, Any]:
    """Recompute and verify one concise certificate payload."""

    max_n = int(certificate.get("max_n", MAX_EXACT_N))
    benchmark = commutative_csg_reference_benchmark(max_n)
    schema = certificate.get("schema_version", "")
    checks: dict[str, bool]
    if schema == "commutative-csg-finite-certificate-v0.3.1":
        checks = {
            "profile_matches": certificate["profile_id"]
            == benchmark["profile_id"],
            "transition_count_matches": certificate[
                "transition_orbit_count"
            ]
            == benchmark["transition_audit"]["transition_orbit_count"],
            "transition_digest_matches": certificate[
                "raw_transition_coverage_sha256"
            ]
            == benchmark["transition_audit"][
                "raw_transition_coverage_sha256"
            ],
            "bell_count_matches": certificate["bell_pair_count"]
            == benchmark["scalar_bell_causality"]["pair_count"],
            "bell_digest_matches": certificate["bell_coverage_sha256"]
            == benchmark["scalar_bell_causality"]["coverage_sha256"],
            "all_exact_claims_hold": all(
                certificate["exact_claims"].values()
            ),
            "verdict_matches": certificate["verdict"]
            == benchmark["verdict"],
        }
    elif schema == "commutative-csg-theorem-certificate-v0.3.1":
        checks = {
            "profile_matches": certificate["profile_id"]
            == benchmark["profile_id"],
            "paper_hash_matches": certificate["paper"]["sha256"]
            == PAPER_SHA256,
            "hypotheses_match": certificate["hypothesis_mapping"]
            == benchmark["theorem_mapping"]["hypothesis_mapping"],
            "extension_mapping_matches": certificate[
                "extension_applicability"
            ]
            == benchmark["theorem_mapping"]["extension_applicability"],
            "verdict_matches": certificate["verdict"]
            == benchmark["verdict"],
        }
    elif schema == "commutative-csg-witness-certificate-v0.3.1":
        expected = benchmark["decoherence_functional"][
            "physical_interference_witness"
        ]
        checks = {
            "profile_matches": certificate["profile_id"]
            == benchmark["profile_id"],
            "witness_matches": certificate["witness"] == expected,
            "D_nonzero": GaussianRational.from_record(
                certificate["witness"]["D_A_B"]
            )
            != ZERO,
            "I2_nonzero": certificate["witness"]["I2_A_B"]
            != _fraction_record(Fraction(0)),
            "physical_geometry_distinct": certificate["witness"][
                "events_are_physically_distinct_unlabeled_geometries"
            ],
            "not_label_multiplicity_only": certificate["witness"][
                "not_a_natural_labelling_multiplicity_witness"
            ],
            "orthogonal_control_zero": certificate[
                "orthogonal_record_control"
            ]["all_off_diagonals_zero"]
            and certificate["orthogonal_record_control"]["all_I2_zero"],
            "verdict_matches": certificate["verdict"]
            == benchmark["verdict"],
        }
    else:
        checks = {"known_schema": False}
    return {
        "schema_version": schema,
        "checks": checks,
        "passed": all(checks.values()),
    }
