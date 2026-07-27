"""Infinite-extension audit for the v0.3 sparse Kraus growth profile.

The three objects requested by the benchmark are deliberately kept separate:

* the positive classical measure on recorded branch outcomes;
* a CP-instrument-valued measure with a common output space;
* the diagonal decoherence functional induced by the recorded outcomes.

Only the first and third admit a construction from the current repository
semantics.  The changing one-ray output spaces do not yet form the inductive
system needed for an infinite-time instrument-valued measure.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    causet_id,
    enumerate_unlabeled_posets,
)
from universe_lab.final_theory.dynamics_v02 import transition_instrument


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _branch_probability(branch: dict[str, Any]) -> Fraction:
    value = branch["probability"]
    return Fraction(value["numerator"], value["denominator"])


def _branch_id(branch: dict[str, Any]) -> str:
    move = branch["move"]
    precursor = ",".join(str(vertex) for vertex in move["precursor_set"])
    return (
        f"{move['source_history']}->{move['target_history']}"
        f"|{move['move_class']}|P[{precursor}]"
    )


def finite_path_distributions(
    max_n: int = 5,
) -> tuple[dict[tuple[str, ...], Fraction], ...]:
    """Return exact recorded-outcome path distributions through ``max_n``."""

    if max_n < 0:
        raise ValueError("max_n must be non-negative")
    levels = enumerate_unlabeled_posets(max_n)
    root_id = causet_id(levels[0][0])
    distributions: list[dict[tuple[str, ...], Fraction]] = [
        {(root_id,): Fraction(1)}
    ]
    for stage in range(max_n):
        relation_by_id: dict[str, Relation] = {
            causet_id(relation): relation for relation in levels[stage]
        }
        following: dict[tuple[str, ...], Fraction] = {}
        for path, path_probability in distributions[-1].items():
            source_id = path[-1].split("->")[-1].split("|")[0]
            for branch in transition_instrument(relation_by_id[source_id]):
                next_path = (*path, _branch_id(branch))
                following[next_path] = (
                    following.get(next_path, Fraction(0))
                    + path_probability * _branch_probability(branch)
                )
        if sum(following.values(), start=Fraction(0)) != 1:
            raise AssertionError(f"stage {stage + 1} path measure is not normalized")
        distributions.append(following)
    return tuple(distributions)


def _finite_variation_audit(max_n: int) -> dict[str, Any]:
    distributions = finite_path_distributions(max_n)
    variation = [
        sum((abs(value) for value in distribution.values()), start=Fraction(0))
        for distribution in distributions
    ]
    refinement_checks = []
    for stage in range(max_n):
        parent = distributions[stage]
        child = distributions[stage + 1]
        recovered = {path: Fraction(0) for path in parent}
        for child_path, probability in child.items():
            recovered[child_path[:-1]] += probability
        refinement_checks.append(
            {
                "from_stage": stage,
                "to_stage": stage + 1,
                "exact_marginal_match": recovered == parent,
            }
        )
    return {
        "stage_path_counts": [
            {"stage": stage, "count": len(distribution)}
            for stage, distribution in enumerate(distributions)
        ],
        "total_variation": [_fraction_record(value) for value in variation],
        "effect_measure_trace_norm_variation": [
            _fraction_record(value) for value in variation
        ],
        "diagonal_decoherence_semivariation": [
            _fraction_record(value) for value in variation
        ],
        "finite_refinement_consistency": refinement_checks,
        "finite_checks_passed": all(
            value == 1 for value in variation
        )
        and all(check["exact_marginal_match"] for check in refinement_checks),
        "finite_check_boundary": (
            "The displayed sequence is an exhaustive n<=max_n regression. "
            "The infinite classical result below follows from the all-stage "
            "kernel definition, not from extrapolating this finite sequence."
        ),
    }


def extension_benchmark(max_n: int = 5) -> dict[str, Any]:
    """Separate and certify the three v0.3 extension questions."""

    finite = _finite_variation_audit(max_n)
    return {
        "schema_version": "final-theory-extension-v0.3.0",
        "profile_id": "causal_information_v2_sparse_kraus",
        "assumptions": [
            "every finite causal set has finitely many down-set precursors",
            "all local candidate weights are strictly positive rational numbers",
            "each source instrument is normalized by its finite positive weight sum",
            "branch-orbit outcomes are physical records, as declared by the v0.2 profile",
            "events are in the sigma algebra generated by recorded-outcome cylinders",
        ],
        "complex_growth_control": {
            "source": "arXiv:2003.11311v1",
            "classification": "LITERATURE_LOCKED_REGRESSION_ONLY",
            "regression": (
                "For positive-real scalar transition weights, absolute variation "
                "equals probability variation; the bounded-variation control is "
                "therefore one. No transfer to noncommutative CP instruments is made."
            ),
            "paper_scope": (
                "The cited CHK/bounded-variation criterion is for complex-valued "
                "sequential-growth measures."
            ),
        },
        "finite_sequences": finite,
        "classical_outcome_measure": {
            "verdict": "CLASSICAL_OUTCOME_EXTENSION_PASS",
            "theorem": (
                "Ionescu-Tulcea/Kolmogorov extension for a countable sequence "
                "of finite discrete outcome spaces"
            ),
            "assumption_check": {
                "finite_discrete_stage_spaces": True,
                "nonnegative_kernels": True,
                "normalized_kernels": True,
                "all_stage_definition": True,
                "cylinder_consistency_exact_through_n5": finite[
                    "finite_checks_passed"
                ],
            },
            "proof_certificate": [
                "For each finite source, downsets form a finite nonempty set.",
                "The rational local weights are positive, so their finite sum is positive.",
                "Division by that sum defines an exactly normalized stochastic kernel.",
                "Recursive products define consistent finite cylinder probabilities.",
                "Finite discrete spaces are standard Borel; the extension theorem gives "
                "a unique countably additive probability measure on the product sigma algebra.",
                "Restriction to its label-invariant/covariant sub-sigma algebra remains "
                "a countably additive probability measure.",
            ],
            "scope": (
                "Recorded automorphism-orbit branch paths and the cylinder-generated "
                "sigma algebra. This is not a claim about arbitrary nonmeasurable sets "
                "or a continuum limit."
            ),
        },
        "operator_valued_instrument_measure": {
            "verdict": "INFINITE_EXTENSION_BLOCKED",
            "finite_effect_povm": (
                "The root-space effects reduce to p(h) times the one-dimensional "
                "identity and therefore extend only as a scalarized POVM."
            ),
            "blocking_defects": [
                "stage-dependent output Hilbert spaces",
                "no declared common output von Neumann/C-star algebra",
                "no isometric inductive embeddings between output spaces",
                "no normal CP reduction maps proving instrument consistency",
            ],
            "theorem_not_applied": (
                "A bounded-variation theorem for complex scalar measures cannot "
                "supply the missing Banach-space codomain and countable-additivity "
                "hypotheses for a CP-instrument-valued measure."
            ),
        },
        "decoherence_functional": {
            "verdict": "DECOHERENCE_FUNCTIONAL_EXTENSION_PASS",
            "construction": "D(A,B) = mu(A intersection B)",
            "derivation": (
                "The declared orthogonal branch record makes distinct recorded "
                "histories exactly decoherent. Applying the extended classical "
                "outcome measure to intersections is therefore the unique diagonal "
                "extension of the implemented finite functional."
            ),
            "certificates": {
                "hermiticity": "D(A,B)=D(B,A) is real",
                "biadditivity": "follows from countable additivity of mu",
                "normalization": "D(Omega,Omega)=mu(Omega)=1",
                "strong_positivity": (
                    "sum_ij conjugate(c_i)c_j mu(A_i intersection A_j) "
                    "equals the L2(mu) norm squared of sum_i c_i 1_A_i"
                ),
                "covariance_scope": (
                    "restriction to label-invariant events in the generated sigma algebra"
                ),
            },
            "claim_boundary": (
                "This is a level-1 classical diagonal decoherence functional. "
                "It does not establish nonzero quantum-geometric interference."
            ),
        },
        "counterexample_search": {
            "finite_n_boundedness_as_infinite_proof": "REJECTED_BY_THEOREM_GATE",
            "classical_extension_as_full_instrument_extension": (
                "REJECTED_BY_CODOMAIN_GATE"
            ),
            "coherent_kraus_sum_as_measure": "REJECTED_BY_OUTCOME_SEMANTICS_GATE",
        },
        "exact_numeric_distinction": {
            "exact": "all finite probabilities, variations, and marginal checks",
            "analytic": "all-stage positivity/normalization proof and extension theorem",
            "numeric": "none",
        },
        "completeness_scope": f"exhaustive finite regression through n={max_n}",
        "resource_limits": [
            "explicit path enumeration is intentionally limited to n<=5",
            "no common infinite-time output algebra is implemented",
        ],
        "verdict": "INFINITE_EXTENSION_BLOCKED",
        "unresolved_items": [
            "construct a common output algebra and compatible CP instrument maps",
            "prove a non-diagonal quantum-measure extension if a future profile has interference",
        ],
    }


def verify_extension_certificate(path: Path) -> dict[str, Any]:
    """Verify the checked-in classical/diagonal extension certificate."""

    certificate = json.loads(path.read_text(encoding="utf-8"))
    max_n = int(certificate["finite_regression"]["max_n"])
    benchmark = extension_benchmark(max_n)
    observed_counts = [
        item["count"]
        for item in benchmark["finite_sequences"]["stage_path_counts"]
    ]
    checks = {
        "profile_matches": certificate["profile_id"] == benchmark["profile_id"],
        "path_counts_match": (
            observed_counts
            == certificate["finite_regression"]["stage_path_counts"]
        ),
        "variations_are_exactly_one": all(
            item == {"numerator": 1, "denominator": 1}
            for item in benchmark["finite_sequences"]["total_variation"]
        ),
        "classical_verdict_matches": (
            certificate["classical_outcome_verdict"]
            == benchmark["classical_outcome_measure"]["verdict"]
        ),
        "diagonal_verdict_matches": (
            certificate["diagonal_decoherence_verdict"]
            == benchmark["decoherence_functional"]["verdict"]
        ),
        "full_instrument_remains_blocked": (
            certificate["full_instrument_verdict"]
            == benchmark["operator_valued_instrument_measure"]["verdict"]
        ),
        "proof_obligations_declared": all(
            certificate["proof_obligations"].values()
        ),
    }
    return {
        "certificate": path.as_posix(),
        "checks": checks,
        "passed": all(checks.values()),
    }
