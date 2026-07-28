"""Scientific precondition gates after the v0.3.1 CPOBC representation search."""

from __future__ import annotations

from typing import Any


def _representation_found(search: dict[str, Any]) -> bool:
    summary = search.get("summary", {})
    return bool(
        summary.get("noncommutative_representation_found")
        or summary.get("exact_representation_found")
        or search.get("representation_found")
        or search.get("cpobc_d3_status")
        == "CPOBC_D3_NONCOMMUTATIVE_REPRESENTATION_FOUND"
    )


def noncommutative_qsg_certification(
    representation_search: dict[str, Any],
) -> dict[str, Any]:
    """Apply the Phase-F precondition without inventing a channel conversion.

    A necessary-relation survivor is deliberately not accepted here.  Physical
    certification starts only after a full exact n<=4 CPOBC representation
    certificate exists.
    """

    found = _representation_found(representation_search)
    full_relation_certificate = bool(
        representation_search.get("summary", {}).get(
            "full_compiled_relation_certificate_count", 0
        )
    )
    exact_representation_gate = found and full_relation_certificate
    if not exact_representation_gate:
        return {
            "schema_version": "final-theory-noncommutative-qsg-v0.3.1",
            "phase": "PHASE_F_PHYSICAL_QSG_CERTIFICATION",
            "precondition": {
                "exact_finite_dimensional_representation_found": found,
                "full_n4_compiled_relation_certificate": full_relation_certificate,
                "passed": False,
            },
            "execution": "NOT_EXECUTED",
            "vector_measure_constructed": False,
            "decoherence_functional_constructed": False,
            "kraus_channel_conversion_attempted": False,
            "finite_additivity": "NOT_ASSESSED",
            "MSR": "NOT_ASSESSED",
            "GC": "NOT_ASSESSED",
            "CPOBC": "NOT_ASSESSED",
            "normalization": "NOT_ASSESSED",
            "hermiticity": "NOT_ASSESSED",
            "strong_positivity": "NOT_ASSESSED",
            "label_covariance": "NOT_ASSESSED",
            "quotient_consistency": "NOT_ASSESSED",
            "path_consistency": "NOT_ASSESSED",
            "initial_vector_dependence": "NOT_ASSESSED",
            "scalar_commutative_limit": "NOT_ASSESSED",
            "off_diagonal_geometry_interference": "NOT_ASSESSED",
            "geometry_interference_status": "NOT_ASSESSED_NO_REPRESENTATION",
            "status": "NOT_EXECUTED_NO_REPRESENTATION",
            "verdict": "NOT_EXECUTED_NO_REPRESENTATION",
            "claim_boundary": (
                "Exact survivors of selected necessary relations, finite grids, "
                "or bounded ansatz diagnostics are not representations of the full "
                "CPOBC/MSR/GC system."
            ),
            "unresolved_items": [
                "full exact operator assignment for every compiled n<=4 relation",
                "MSR and GC certificates for that assignment",
                "finite-stage vector measure and covariant-event interference",
            ],
        }

    physical = representation_search.get("physical_certification")
    if not isinstance(physical, dict):
        return {
            "schema_version": "final-theory-noncommutative-qsg-v0.3.1",
            "phase": "PHASE_F_PHYSICAL_QSG_CERTIFICATION",
            "precondition": {
                "exact_finite_dimensional_representation_found": True,
                "full_n4_compiled_relation_certificate": True,
                "passed": True,
            },
            "execution": "EXECUTED_CERTIFICATE_MISSING",
            "vector_measure_constructed": False,
            "kraus_channel_conversion_attempted": False,
            "geometry_interference_status": "NOT_ASSESSED",
            "status": "NONCOMMUTATIVE_QSG_CERTIFICATION_INCONCLUSIVE",
            "verdict": "NONCOMMUTATIVE_QSG_CERTIFICATION_INCONCLUSIVE",
            "claim_boundary": (
                "A representation alone cannot certify a physical QSG without an "
                "independently verified vector-measure and decoherence certificate."
            ),
            "unresolved_items": [
                "construct and independently verify the finite vector measure",
            ],
        }

    required = (
        "finite_additivity",
        "MSR",
        "GC",
        "CPOBC",
        "normalization",
        "hermiticity",
        "strong_positivity",
        "label_covariance",
        "quotient_consistency",
        "path_consistency",
        "exact_nonzero_covariant_interference",
        "independent_verification",
    )
    passed = all(physical.get(name) is True for name in required)
    return {
        "schema_version": "final-theory-noncommutative-qsg-v0.3.1",
        "phase": "PHASE_F_PHYSICAL_QSG_CERTIFICATION",
        "precondition": {
            "exact_finite_dimensional_representation_found": True,
            "full_n4_compiled_relation_certificate": True,
            "passed": True,
        },
        "execution": "EXECUTED",
        "checks": {name: bool(physical.get(name)) for name in required},
        "physical_certificate": physical,
        "kraus_channel_conversion_attempted": False,
        "geometry_interference_status": (
            "EXACT_NONZERO_COVARIANT_GEOMETRY_INTERFERENCE"
            if passed
            else "GEOMETRY_INTERFERENCE_NOT_CERTIFIED"
        ),
        "status": (
            "NONCOMMUTATIVE_QSG_MICRODYNAMICS_CANDIDATE"
            if passed
            else "NONCOMMUTATIVE_QSG_CERTIFICATION_INCONCLUSIVE"
        ),
        "verdict": (
            "NONCOMMUTATIVE_QSG_MICRODYNAMICS_CANDIDATE"
            if passed
            else "NONCOMMUTATIVE_QSG_CERTIFICATION_INCONCLUSIVE"
        ),
        "claim_boundary": (
            "The gate reports only the supplied independently verified exact "
            "finite-stage certificate; it makes no continuum or infinite-extension claim."
        ),
        "unresolved_items": [] if passed else [
            name for name in required if physical.get(name) is not True
        ],
    }


def noncommutative_extension_boundary(
    qsg_certification: dict[str, Any],
) -> dict[str, Any]:
    """Keep the literature-locked scalar extension separate from a future lift."""

    representation_available = (
        qsg_certification.get("precondition", {}).get(
            "exact_finite_dimensional_representation_found"
        )
        is True
    )
    if not representation_available:
        status = "NONCOMMUTATIVE_EXTENSION_NOT_ASSESSED"
        missing = [
            "exact noncommutative CPOBC representation",
            "associated finite vector pre-measure",
        ]
    else:
        status = "NONCOMMUTATIVE_EXTENSION_BLOCKED"
        missing = [
            "uniform total-variation or semivariation bound",
            "all weak scalarisations and cylinder consistency",
            "a verified applicable vector-measure extension theorem",
        ]
    return {
        "schema_version": "final-theory-extension-boundary-v0.3.1",
        "commutative_csg_extension": {
            "classification": "LITERATURE_LOCKED",
            "source": "arXiv:2003.11311v1",
            "statement": (
                "Bounded variation is the paper criterion for extension of the "
                "complex scalar CSG measure; the selected positive control is a "
                "regression fixture."
            ),
        },
        "noncommutative_vector_measure": {
            "representation_available": representation_available,
            "associated_vector_pre_measure": "NOT_CONSTRUCTED",
            "total_variation": "NOT_ASSESSED",
            "semivariation": "NOT_ASSESSED",
            "weak_scalarisations": "NOT_ASSESSED",
            "cylinder_consistency": "NOT_ASSESSED",
            "applicable_theorem": "NOT_IDENTIFIED",
            "missing_assumptions": missing,
        },
        "finite_n_boundedness_is_infinite_proof": False,
        "status": status,
        "verdict": status,
        "prohibited_verdict": "INFINITE_EXTENSION_PASS",
        "claim_boundary": (
            "No scalar bounded-variation theorem is transferred to an "
            "operator-valued vector measure without its codomain and hypotheses."
        ),
        "unresolved_items": missing,
    }


def kraus_track_boundary() -> dict[str, Any]:
    """Record the deferred CP-channel branch without conflating causal notions."""

    return {
        "schema_version": "final-theory-kraus-boundary-v0.3.1",
        "v0_3_baseline_preserved": True,
        "classification": "FORMULATION_MISMATCH",
        "distinct_notions": [
            "Quantum Causal Histories causality",
            "semicausal/no-signalling quantum channels",
            "Rideout-Sorkin Bell causality",
            "CPOBC for nonsingular transition operators",
        ],
        "equivalence_theorem_found": False,
        "new_channel_bell_definition_introduced": False,
        "deferred_target": (
            "Kraus-channel spectator reduction on a separate branch and version"
        ),
        "verdict": "FORMULATION_MISMATCH",
    }
