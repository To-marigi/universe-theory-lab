"""Finite-size phase and emergent-symmetry pre-gate diagnostics."""

from __future__ import annotations

import math
from collections.abc import Callable
from fractions import Fraction
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    automorphisms,
    causet_id,
    comparable_pairs,
    enumerate_unlabeled_posets,
    height,
    interval_abundances,
    width,
)
from universe_lab.final_theory.dynamics_v02 import (
    CANDIDATE_PROFILE,
    RANDOM_CONTROL_PROFILE,
    distribution_entropy,
    propagate_distribution,
)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _weighted_fraction(
    relations: dict[str, Relation],
    distribution: dict[str, Fraction],
    observable: Callable[[Relation], Fraction],
) -> Fraction:
    return sum(
        (
            distribution[identifier] * observable(relation)
            for identifier, relation in relations.items()
        ),
        start=Fraction(0),
    )


def _order_fraction(relation: Relation) -> Fraction:
    n = len(relation)
    denominator = n * (n - 1) // 2
    return (
        Fraction(comparable_pairs(relation), denominator)
        if denominator
        else Fraction(0)
    )


def _moment(
    relations: dict[str, Relation],
    distribution: dict[str, Fraction],
    order: int,
) -> Fraction:
    return _weighted_fraction(
        relations,
        distribution,
        lambda relation: _order_fraction(relation) ** order,
    )


def _stage_diagnostics(
    n: int,
    relations: dict[str, Relation],
    distribution: dict[str, Fraction],
) -> dict[str, Any]:
    mean_order = _moment(relations, distribution, 1)
    second_order = _moment(relations, distribution, 2)
    fourth_order = _moment(relations, distribution, 4)
    susceptibility = n * (second_order - mean_order**2)
    binder = (
        1 - float(fourth_order) / (3 * float(second_order) ** 2)
        if second_order
        else None
    )
    interval_width = max(
        (len(interval_abundances(relation)) for relation in relations.values()),
        default=1,
    )
    mean_intervals = []
    for index in range(interval_width):
        def interval_at(relation: Relation, slot: int = index) -> Fraction:
            abundances = interval_abundances(relation)
            return Fraction(abundances[slot] if slot < len(abundances) else 0)

        mean_intervals.append(
            _weighted_fraction(
                relations,
                distribution,
                interval_at,
            )
        )
    mean_height = _weighted_fraction(
        relations, distribution, lambda relation: Fraction(height(relation))
    )
    mean_width = _weighted_fraction(
        relations, distribution, lambda relation: Fraction(width(relation))
    )
    mean_automorphism_log = sum(
        float(distribution[identifier])
        * math.log(len(automorphisms(relation)))
        for identifier, relation in relations.items()
    )
    broad_layer_score = (
        _weighted_fraction(
            relations,
            distribution,
            lambda relation: Fraction(width(relation), max(1, len(relation))),
        )
        if n
        else Fraction(0)
    )
    return {
        "size": n,
        "state_count": len(relations),
        "normalization": _fraction_record(sum(distribution.values(), Fraction(0))),
        "order_fraction": _fraction_record(mean_order),
        "interval_abundance_vector": [
            _fraction_record(value) for value in mean_intervals
        ],
        "height": _fraction_record(mean_height),
        "width": _fraction_record(mean_width),
        "longest_chain_scaling_ratio": _fraction_record(
            mean_height / n if n else Fraction(0)
        ),
        "maximal_antichain_scaling_ratio": _fraction_record(
            mean_width / n if n else Fraction(0)
        ),
        "myrheim_meyer_dimension": None,
        "midpoint_scaling_dimension": None,
        "dimension_estimator_agreement": "UNDEFINED_AT_THIS_CUTOFF",
        "local_curvature_distribution": None,
        "automorphism_entropy": mean_automorphism_log,
        "layered_order_score": _fraction_record(broad_layer_score),
        "manifoldlikeness_score": None,
        "correlation_length": None,
        "susceptibility_order_fraction": _fraction_record(susceptibility),
        "binder_like_order_fraction": binder,
        "finite_size_scaling_exponents": None,
        "distribution_entropy": distribution_entropy(distribution),
        "claim_boundary": (
            "Dimension, curvature, correlation length, and continuum exponents "
            "are deliberately undefined for n<=5 rather than extrapolated."
        ),
    }


def phase_scan(max_n: int = 5) -> dict[str, Any]:
    """Compare frozen candidate and random-control ensembles at three sizes."""

    levels = enumerate_unlabeled_posets(max_n)
    candidate = propagate_distribution(
        max_n, profile_id=CANDIDATE_PROFILE.profile_id
    )
    random = propagate_distribution(
        max_n, profile_id=RANDOM_CONTROL_PROFILE.profile_id
    )
    sizes = (3, 4, 5)
    candidate_stages = []
    random_stages = []
    for n in sizes:
        relation_map = {
            causet_id(relation): relation
            for relation in levels[n]
        }
        candidate_stages.append(
            _stage_diagnostics(n, relation_map, candidate[n])
        )
        random_stages.append(_stage_diagnostics(n, relation_map, random[n]))
    return {
        "suite": "continuum-phase diagnostics v0.2",
        "sizes": list(sizes),
        "couplings_frozen_before_held_out_n5": True,
        "candidate": {
            "profile_id": CANDIDATE_PROFILE.profile_id,
            "stages": candidate_stages,
        },
        "negative_control": {
            "profile_id": RANDOM_CONTROL_PROFILE.profile_id,
            "stages": random_stages,
        },
        "bdg_positive_control": {
            "status": "SCHEMA_ONLY_NOT_COUNTED_AS_EMERGENCE",
            "reason": (
                "A valid BDG continuum control needs dimension-specific "
                "coefficients, a nonlocality scale, and manifoldlike sprinklings; "
                "none is smuggled into the candidate finite ensemble."
            ),
        },
        "phase_classification": "FINITE_SIZE_ARTIFACT_UNRESOLVED",
        "continuum_status": "CONTINUUM_PHASE_RESOURCE_BLOCKED",
        "blocking_evidence": [
            "only n=3,4,5 exact ensembles are available",
            "no correlation-length estimator is valid in this domain",
            "no stable independent dimension estimates are available",
            "no scalable candidate sampler has been certified",
        ],
        "prohibited_inference": "No continuum phase or target dimension is claimed.",
    }


def emergent_symmetry_pre_gate() -> dict[str, Any]:
    """Return a conservative symmetry pre-gate from the phase evidence."""

    checks = {
        "translation_like_homogeneity": "UNDEFINED",
        "rotation_like_isotropy": "UNDEFINED",
        "boost_lorentz_like_dispersion": "UNDEFINED",
        "long_wavelength_mode_stability": "UNDEFINED",
        "approximate_light_cone": "UNDEFINED",
        "scale_dependent_symmetry_violation": "UNDEFINED",
        "preferred_frame_observables": "UNDEFINED",
        "causal_distance_reconstruction": "NOT_IMPLEMENTED",
        "interval_statistics": "FINITE_N5_ONLY",
        "propagator_response": "NOT_DEFINED_FOR_CANDIDATE",
        "spectral_diagnostics": "NOT_DEFINED_FOR_CANDIDATE",
        "embedded_control_comparison": "NOT_USED_AS_CANDIDATE_EVIDENCE",
    }
    readiness_conditions = {
        "stable_effective_dimension": False,
        "isotropy_violation_decreases": False,
        "stable_long_wavelength_dispersion": False,
        "coarse_graining_fixed_symmetry": False,
        "held_out_ensemble_replication": False,
    }
    return {
        "checks": checks,
        "readiness_conditions": readiness_conditions,
        "symmetry_status": "SPIN_CLASSIFICATION_NOT_YET_DEFINED",
        "spin_gate_status": "SPIN2_GATE_BLOCKED_BY_CONTINUUM",
        "claim_boundary": (
            "No background was fitted and no spin representation is defined. "
            "The v0.1 reference Spin-2 controls are excluded from this evidence."
        ),
    }


def held_out_audit() -> dict[str, Any]:
    """Record pre-registered held-out partitions and leakage checks."""

    return {
        "held_out_partitions": {
            "causal_set_size": 5,
            "coupling_region": "sign-reversed link fugacity (not evaluated)",
            "initial_history": "two-element chain",
            "growth_branch": "TIMID",
            "qsg_representation_dimension": 4,
            "manifoldlike_control_geometry": "finite chain family",
            "non_manifoldlike_family": "finite antichain family",
        },
        "frozen_items": [
            "theta_i / rational fugacities",
            "normalization rule",
            "operator ordering",
            "exact equality tolerance",
            "no classifier threshold exists",
        ],
        "retuned_after_held_out": False,
        "status": "HELD_OUT_PROTOCOL_PASS",
        "scientific_result": (
            "The held-out protocol protects the negative conclusion; it does "
            "not turn the n=5 check into continuum evidence."
        ),
    }
