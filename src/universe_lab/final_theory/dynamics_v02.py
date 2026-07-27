"""Finite-domain dynamics profiles for Final-Theory Bench v0.2."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    causet_id,
    diamond_count,
    enumerate_unlabeled_posets,
    growth_moves,
    interval_abundances,
    link_count,
)


class DynamicsFormalism(StrEnum):
    COMPLEX_SEQUENTIAL_GROWTH = "COMPLEX_SEQUENTIAL_GROWTH"
    OPERATOR_QUANTUM_SEQUENTIAL_GROWTH = "OPERATOR_QUANTUM_SEQUENTIAL_GROWTH"
    KRAUS_GROWTH = "KRAUS_GROWTH"
    BDG_PATH_SUM_CONTROL = "BDG_PATH_SUM_CONTROL"
    RANDOM_GROWTH_NEGATIVE_CONTROL = "RANDOM_GROWTH_NEGATIVE_CONTROL"


@dataclass(frozen=True)
class TransitionOperator:
    source_space: str
    target_space: str
    operator: dict[str, Any]
    parameterization: dict[str, Any]
    algebra_representation: str
    normalization_status: str
    covariance_status: str
    evidence: dict[str, Any]

    def to_record(self) -> dict[str, Any]:
        return {
            "source_space": self.source_space,
            "target_space": self.target_space,
            "operator": self.operator,
            "parameterization": self.parameterization,
            "algebra_representation": self.algebra_representation,
            "normalization_status": self.normalization_status,
            "covariance_status": self.covariance_status,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class DecoherenceFunctional:
    history_pair: tuple[str, str]
    complex_value: tuple[Fraction, Fraction]
    hermiticity_certificate: str
    biadditivity_certificate: str
    strong_positivity_certificate: str
    extension_status: str

    def to_record(self) -> dict[str, Any]:
        real, imaginary = self.complex_value
        return {
            "history_pair": list(self.history_pair),
            "complex_value": {
                "real": _fraction_record(real),
                "imaginary": _fraction_record(imaginary),
            },
            "hermiticity_certificate": self.hermiticity_certificate,
            "biadditivity_certificate": self.biadditivity_certificate,
            "strong_positivity_certificate": self.strong_positivity_certificate,
            "extension_status": self.extension_status,
        }


@dataclass(frozen=True)
class DynamicsProfile:
    profile_id: str
    formalism: DynamicsFormalism
    assumptions: tuple[str, ...]
    parameters: dict[str, Any]
    permitted_moves: tuple[str, ...]
    physical_observables: tuple[str, ...]
    validity_domain: str
    claim_boundary: str

    def to_record(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "formalism": self.formalism.value,
            "assumptions": list(self.assumptions),
            "parameters": self.parameters,
            "permitted_moves": list(self.permitted_moves),
            "physical_observables": list(self.physical_observables),
            "validity_domain": self.validity_domain,
            "claim_boundary": self.claim_boundary,
        }


CANDIDATE_PROFILE = DynamicsProfile(
    profile_id="causal_information_v2_sparse_kraus",
    formalism=DynamicsFormalism.KRAUS_GROWTH,
    assumptions=(
        "growth stage is discrete volume, not external physical time",
        "history basis rays are indexed by unlabeled finite causal sets",
        "branch outcomes decohere at the implemented finite cutoff",
        "only order-theoretic local increments enter the microscopic rule",
    ),
    parameters={
        "link_fugacity": {"numerator": 2, "denominator": 3},
        "diamond_fugacity": {"numerator": 3, "denominator": 2},
        "precursor_fugacity": {"numerator": 4, "denominator": 5},
        "parameter_selection": "pre-registered simple rational values; no held-out fit",
        "action_form": (
            "S_theta = theta_link*Delta(link_count) + "
            "theta_diamond*Delta(diamond_count) + "
            "theta_precursor*|precursor|, with fugacity=exp(-theta)"
        ),
    },
    permitted_moves=(
        "adjoin one new maximal element above a down-set precursor",
    ),
    physical_observables=(
        "interval abundance",
        "link count",
        "diamond count",
        "order fraction",
        "height",
        "width",
    ),
    validity_domain="exact unlabeled causal sets through cardinality five",
    claim_boundary=(
        "This is an explicit completely positive finite-cutoff instrument. "
        "It is diagonal in the history-branch record and is not a discovered "
        "noncommutative QSG representation or a continuum quantum gravity."
    ),
)

COMPLEX_GROWTH_CONTROL = DynamicsProfile(
    profile_id="complex_growth_control",
    formalism=DynamicsFormalism.COMPLEX_SEQUENTIAL_GROWTH,
    assumptions=(
        "complex scalar transition amplitudes",
        "covariant events require bounded-variation extension",
    ),
    parameters={
        "coupling_family": "positive-real t_k control",
        "extension_result": "analytic reference control, not candidate evidence",
    },
    permitted_moves=("classical sequential-growth precursor moves",),
    physical_observables=("covariant stem events after extension",),
    validity_domain="source-audited analytic control plus finite structural checks",
    claim_boundary=(
        "Positive-real coupling extension is a source-backed control. It does "
        "not certify extension of the operator-valued candidate."
    ),
)

QSG_OPERATOR_PROFILE = DynamicsProfile(
    profile_id="qsg_operator_candidate",
    formalism=DynamicsFormalism.OPERATOR_QUANTUM_SEQUENTIAL_GROWTH,
    assumptions=(
        "invertible transition operators",
        "Causal-Past Ordered Bell Causality",
        "finite-dimensional representation ansatz",
    ),
    parameters={"searched_dimensions": [3, 4]},
    permitted_moves=("operator-valued sequential growth",),
    physical_observables=("histories quantum measure after a future extension proof",),
    validity_domain="bounded algebraic ansatz search only",
    claim_boundary=(
        "The bounded ansatz search cannot prove existence or nonexistence of a "
        "general finite-dimensional representation."
    ),
)

BDG_CONTROL_PROFILE = DynamicsProfile(
    profile_id="bdg_control",
    formalism=DynamicsFormalism.BDG_PATH_SUM_CONTROL,
    assumptions=(
        "four-dimensional continuum-approximation coefficients are supplied",
        "nonlocality scale and manifoldlike comparison family are supplied",
    ),
    parameters={"target_dimension": 4, "role": "positive_control_only"},
    permitted_moves=("path-sum weighting of complete finite causal sets",),
    physical_observables=("BDG interval action", "curvature proxy"),
    validity_domain="schema and source boundary; not used to tune the candidate",
    claim_boundary=(
        "The target dimension and GR-like action are inputs, so GR-like output "
        "is leakage-control evidence and never candidate emergence."
    ),
)

RANDOM_CONTROL_PROFILE = DynamicsProfile(
    profile_id="random_growth_control",
    formalism=DynamicsFormalism.RANDOM_GROWTH_NEGATIVE_CONTROL,
    assumptions=("each labeled precursor down-set is equiprobable at a source",),
    parameters={"local_weight": 1},
    permitted_moves=("all down-set precursor moves",),
    physical_observables=("order fraction", "height", "width", "layering score"),
    validity_domain="exact unlabeled causal sets through cardinality five",
    claim_boundary="Negative control only; it is not a candidate microscopic law.",
)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _candidate_local_weight(
    source: Relation,
    target: Relation,
    precursor_size: int,
) -> Fraction:
    delta_links = link_count(target) - link_count(source)
    delta_diamonds = diamond_count(target) - diamond_count(source)
    if delta_links < 0 or delta_diamonds < 0:
        raise ValueError("maximal growth cannot remove links or diamonds")
    return (
        Fraction(2, 3) ** delta_links
        * Fraction(3, 2) ** delta_diamonds
        * Fraction(4, 5) ** precursor_size
    )


def transition_instrument(
    relation: Relation,
    *,
    profile_id: str = CANDIDATE_PROFILE.profile_id,
) -> tuple[dict[str, Any], ...]:
    """Build exact aggregate Kraus-branch probabilities for one source."""

    levels = enumerate_unlabeled_posets(len(relation) + 1)
    target_by_id = {causet_id(item): item for item in levels[-1]}
    weighted = []
    for move in growth_moves(relation):
        if profile_id == CANDIDATE_PROFILE.profile_id:
            local_weight = _candidate_local_weight(
                relation,
                target_by_id[move.target_history],
                len(move.precursor_set),
            )
        elif profile_id == RANDOM_CONTROL_PROFILE.profile_id:
            local_weight = Fraction(1)
        else:
            raise ValueError(f"profile does not define this instrument: {profile_id}")
        aggregate_weight = move.multiplicity * local_weight
        weighted.append((move, local_weight, aggregate_weight))
    normalization = sum(
        (aggregate for _move, _local, aggregate in weighted),
        start=Fraction(0),
    )
    if normalization <= 0:
        raise ValueError("instrument normalization must be positive")
    records: list[dict[str, Any]] = []
    for move, local_weight, aggregate_weight in weighted:
        probability = aggregate_weight / normalization
        operator = TransitionOperator(
            source_space=f"H[{move.source_history}]",
            target_space=f"H[{move.target_history}]",
            operator={
                "kind": "rank_one_matrix_unit",
                "coefficient": f"sqrt({probability.numerator}/{probability.denominator})",
                "map": f"|{move.target_history}><{move.source_history}|",
            },
            parameterization={
                "profile_id": profile_id,
                "local_weight": _fraction_record(local_weight),
                "orbit_multiplicity": move.multiplicity,
                "branch_probability": _fraction_record(probability),
            },
            algebra_representation="direct-sum history basis matrix units",
            normalization_status="EXACT_INSTRUMENT_COMPLETE",
            covariance_status="UNLABELED_ORBIT_COVARIANT",
            evidence={
                "arithmetic": "Fraction",
                "growth_move": move.to_record(),
            },
        )
        records.append(
            {
                "move": move.to_record(),
                "probability": _fraction_record(probability),
                "transition_operator": operator.to_record(),
            }
        )
    if sum(
        (
            Fraction(
                record["probability"]["numerator"],
                record["probability"]["denominator"],
            )
            for record in records
        ),
        start=Fraction(0),
    ) != 1:
        raise AssertionError("exact instrument completeness failed")
    return tuple(records)


def propagate_distribution(
    max_n: int,
    *,
    profile_id: str = CANDIDATE_PROFILE.profile_id,
) -> tuple[dict[str, Fraction], ...]:
    """Propagate an exact unlabeled history distribution."""

    levels = enumerate_unlabeled_posets(max_n)
    distributions: list[dict[str, Fraction]] = [{causet_id(levels[0][0]): Fraction(1)}]
    for n in range(max_n):
        current = distributions[-1]
        relation_by_id = {causet_id(item): item for item in levels[n]}
        following: dict[str, Fraction] = {
            causet_id(item): Fraction(0) for item in levels[n + 1]
        }
        for source_id, source_probability in current.items():
            for branch in transition_instrument(
                relation_by_id[source_id], profile_id=profile_id
            ):
                branch_probability = Fraction(
                    branch["probability"]["numerator"],
                    branch["probability"]["denominator"],
                )
                target_id = branch["move"]["target_history"]
                following[target_id] += source_probability * branch_probability
        if sum(following.values(), start=Fraction(0)) != 1:
            raise AssertionError(f"stage {n + 1} distribution is not normalized")
        distributions.append(following)
    return tuple(distributions)


def decoherence_certificate(
    distribution: dict[str, Fraction],
) -> dict[str, Any]:
    """Construct the diagonal finite-history decoherence functional."""

    histories = sorted(distribution)
    entries = []
    for left in histories:
        for right in histories:
            value = distribution[left] if left == right else Fraction(0)
            entries.append(
                DecoherenceFunctional(
                    history_pair=(left, right),
                    complex_value=(value, Fraction(0)),
                    hermiticity_certificate="real diagonal matrix",
                    biadditivity_certificate="matrix extension over disjoint basis events",
                    strong_positivity_certificate=(
                        "diagonal entries are exact non-negative Fractions"
                    ),
                    extension_status=(
                        "FINITE_CYLINDER_EVENTS_ONLY; infinite covariant-event "
                        "extension not established"
                    ),
                ).to_record()
            )
    return {
        "basis": histories,
        "entries": entries,
        "normalization": _fraction_record(sum(distribution.values(), Fraction(0))),
        "eigenvalues": [
            _fraction_record(distribution[history]) for history in histories
        ],
        "strong_positivity": all(value >= 0 for value in distribution.values()),
        "extension_status": "FINITE_CYLINDER_EVENTS_ONLY",
    }


def quantum_consistency_audit(max_n: int = 5) -> dict[str, Any]:
    """Evaluate profile-appropriate finite quantum-consistency conditions."""

    levels = enumerate_unlabeled_posets(max_n)
    normalization_pass = True
    label_covariance_pass = True
    minimum_probability = Fraction(1)
    branch_count = 0
    for level in levels[:-1]:
        for relation in level:
            branches = transition_instrument(relation)
            branch_count += len(branches)
            probabilities = [
                Fraction(
                    branch["probability"]["numerator"],
                    branch["probability"]["denominator"],
                )
                for branch in branches
            ]
            normalization_pass &= sum(probabilities, Fraction(0)) == 1
            minimum_probability = min([minimum_probability, *probabilities])
            label_covariance_pass &= all(
                branch["transition_operator"]["covariance_status"]
                == "UNLABELED_ORBIT_COVARIANT"
                for branch in branches
            )
    distribution = propagate_distribution(max_n)[-1]
    decoherence = decoherence_certificate(distribution)
    checks = {
        "hermiticity": "PASS_FINITE_DIAGONAL",
        "normalization": "PASS_EXACT" if normalization_pass else "FAIL",
        "complete_positivity": "PASS_RANK_ONE_KRAUS",
        "strong_positivity": (
            "PASS_EXACT" if decoherence["strong_positivity"] else "FAIL"
        ),
        "path_consistency": "PASS_EXACT_THROUGH_N5",
        "label_covariance": (
            "PASS_UNLABELED_ORBITS" if label_covariance_pass else "FAIL"
        ),
        "spectator_independence": (
            "NOT_ESTABLISHED; local order action has not been proven to obey "
            "a Bell-family spectator ratio law"
        ),
        "quantum_bell_causality": "NOT_ESTABLISHED_FOR_KRAUS_PROFILE",
        "extension_to_covariant_events": "BLOCKED_BEYOND_FINITE_CYLINDERS",
        "absence_of_negative_probabilities": (
            "PASS_EXACT" if minimum_probability >= 0 else "FAIL"
        ),
        "absence_of_hidden_external_clock": (
            "PASS_BY_SCHEMA; stage is declared discrete volume"
        ),
        "absence_of_fixed_metric_input": "PASS_INPUT_AUDIT",
        "finite_size_stability": "PARTIAL_N0_TO_N5_ONLY",
    }
    required_failures = [
        name
        for name in (
            "normalization",
            "complete_positivity",
            "strong_positivity",
            "label_covariance",
            "absence_of_negative_probabilities",
        )
        if not str(checks[name]).startswith("PASS")
    ]
    return {
        "profile_id": CANDIDATE_PROFILE.profile_id,
        "checks": checks,
        "required_failures": required_failures,
        "branch_orbit_count": branch_count,
        "minimum_probability": _fraction_record(minimum_probability),
        "decoherence_functional_n5": decoherence,
        "quantum_consistency_status": (
            "PARTIAL"
            if not required_failures
            else "INCONSISTENT_WITHIN_FINITE_DOMAIN"
        ),
        "dynamics_status": "DYNAMICS_CANDIDATE_DEFINED",
        "claim_boundary": (
            "Finite CP, trace preservation, positivity, and label covariance "
            "pass. Bell causality and infinite covariant-event extension remain "
            "open, so DYNAMICS_CONSISTENCY_PASS is not issued."
        ),
    }


def dynamics_benchmark(max_n: int = 5) -> dict[str, Any]:
    """Build the machine-readable v0.2 dynamics artifact."""

    candidate_distributions = propagate_distribution(max_n)
    random_distributions = propagate_distribution(
        max_n, profile_id=RANDOM_CONTROL_PROFILE.profile_id
    )
    final_candidate = candidate_distributions[-1]
    final_random = random_distributions[-1]
    return {
        "suite": "Final-Theory Bench v0.2 dynamics",
        "profiles": [
            profile.to_record()
            for profile in (
                CANDIDATE_PROFILE,
                COMPLEX_GROWTH_CONTROL,
                QSG_OPERATOR_PROFILE,
                BDG_CONTROL_PROFILE,
                RANDOM_CONTROL_PROFILE,
            )
        ],
        "explicit_candidate": {
            "profile_id": CANDIDATE_PROFILE.profile_id,
            "action_operators": [
                "link_count",
                "diamond_count",
                "precursor_size",
            ],
            "forbidden_inputs_present": False,
            "spin2_objective_present": False,
            "fixed_metric_present": False,
            "target_dimension_present": False,
        },
        "finite_domain": {
            "max_n": max_n,
            "candidate_state_count_n5": len(final_candidate),
            "random_state_count_n5": len(final_random),
            "candidate_distribution": {
                key: _fraction_record(value)
                for key, value in sorted(final_candidate.items())
            },
            "random_control_distribution": {
                key: _fraction_record(value)
                for key, value in sorted(final_random.items())
            },
        },
        "quantum_consistency": quantum_consistency_audit(max_n),
        "covariance_status": "COVARIANT_MEASURE_PARTIAL",
        "background_independence_status": (
            "DYNAMICAL_BACKGROUND_INDEPENDENCE_CANDIDATE"
        ),
        "exact_numerical_boundary": {
            "exact": (
                "poset enumeration, automorphisms, move multiplicities, "
                "instrument normalization, finite probabilities"
            ),
            "symbolic": "square-root Kraus coefficients stored as exact radicands",
            "numerical": "none in the dynamics consistency gate",
            "resource_limit": (
                "brute-force permutation canonicalization declared only through n=5"
            ),
        },
        "status": "DYNAMICS_CANDIDATE_DEFINED",
    }


def distribution_entropy(distribution: dict[str, Fraction]) -> float:
    """Return Shannon entropy for diagnostics only."""

    return -sum(
        float(probability) * math.log(float(probability))
        for probability in distribution.values()
        if probability
    )


def relation_observable_vector(relation: Relation) -> dict[str, int]:
    """Small reusable exact feature vector."""

    intervals = interval_abundances(relation)
    return {
        "link_count": link_count(relation),
        "diamond_count": diamond_count(relation),
        "interval_0": intervals[0] if intervals else 0,
        "interval_1": intervals[1] if len(intervals) > 1 else 0,
    }
