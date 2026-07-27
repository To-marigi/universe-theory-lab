from __future__ import annotations

from fractions import Fraction

from universe_lab.final_theory.causal_sets import enumerate_unlabeled_posets
from universe_lab.final_theory.dynamics_v02 import (
    CANDIDATE_PROFILE,
    decoherence_certificate,
    dynamics_benchmark,
    propagate_distribution,
    quantum_consistency_audit,
    transition_instrument,
)


def _fraction(record: dict[str, int]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


def test_each_finite_instrument_is_exactly_complete() -> None:
    for level in enumerate_unlabeled_posets(5)[:-1]:
        for relation in level:
            branches = transition_instrument(relation)
            assert sum(
                (_fraction(branch["probability"]) for branch in branches),
                start=Fraction(0),
            ) == 1
            assert all(_fraction(branch["probability"]) >= 0 for branch in branches)


def test_recursive_distribution_is_normalized() -> None:
    for distribution in propagate_distribution(5):
        assert sum(distribution.values(), start=Fraction(0)) == 1


def test_finite_decoherence_functional_is_strongly_positive() -> None:
    distribution = propagate_distribution(5)[-1]
    result = decoherence_certificate(distribution)
    assert result["strong_positivity"]
    assert _fraction(result["normalization"]) == 1
    assert result["extension_status"] == "FINITE_CYLINDER_EVENTS_ONLY"


def test_candidate_has_no_forbidden_gravity_target() -> None:
    result = dynamics_benchmark()
    candidate = result["explicit_candidate"]
    assert candidate["profile_id"] == CANDIDATE_PROFILE.profile_id
    assert not candidate["forbidden_inputs_present"]
    assert not candidate["spin2_objective_present"]
    assert not candidate["fixed_metric_present"]
    assert not candidate["target_dimension_present"]


def test_quantum_consistency_remains_partial() -> None:
    result = quantum_consistency_audit()
    assert result["required_failures"] == []
    assert result["quantum_consistency_status"] == "PARTIAL"
    assert result["dynamics_status"] == "DYNAMICS_CANDIDATE_DEFINED"
    assert result["checks"]["quantum_bell_causality"].startswith("NOT_ESTABLISHED")
