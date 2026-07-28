"""Logical direction and claim-ceiling gates for Final-Theory Bench v0.3.4."""

from __future__ import annotations

from typing import Any

import sympy as sp

from universe_lab.final_theory.atomisation_v033 import (
    compile_atomisation_paths_n4,
)
from universe_lab.final_theory.cpobc_q_presentation_v033 import (
    compile_q_presentation_n4,
)
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_rational_dag_v034 import (
    BRANCH,
    SOURCE_COMMIT,
    build_d2_rational_model,
)
from universe_lab.final_theory.d2_solver_v034 import (
    VERDICT_PARTIAL,
    scalar_s3_representation_certificate_v034,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    REACHABLE_STATE_PROFILE,
    SOURCE_VERDICT,
    stable_hash,
)
from universe_lab.final_theory.operator_gc_v033 import (
    compile_local_operator_gc_n4,
)

RECONSTRUCTION_EQUIVALENT = "D2_RATIONAL_RECONSTRUCTION_EQUIVALENT_N4"
RECONSTRUCTION_NECESSARY = "D2_RATIONAL_RECONSTRUCTION_NECESSARY_ONLY_N4"
RECONSTRUCTION_SUFFICIENT = "D2_RATIONAL_RECONSTRUCTION_SUFFICIENT_ONLY_N4"
RECONSTRUCTION_PARTIAL = "D2_RATIONAL_RECONSTRUCTION_PARTIAL_N4"
OVERALL = "FINAL_THEORY_OPEN"

FORBIDDEN_PHYSICAL_CLAIMS = (
    "NONCOMMUTATIVE_QSG_MICRODYNAMICS_CANDIDATE",
    "QUANTUM_GEOMETRY_CANDIDATE",
    "CONTINUUM_PHASE_CANDIDATE",
    "SPIN2_CANDIDATE",
    "GRAVITON_FOUND",
    "FINAL_THEORY_COMPLETED",
)


def claim_allowed(claim: str, evidence: dict[str, Any]) -> bool:
    """Pure conservative gate used by production reports and mutation tests."""

    if claim == RECONSTRUCTION_EQUIVALENT:
        return bool(
            evidence.get("forward_retraction_certificate")
            and evidence.get("reverse_original_relation_substitution")
            and evidence.get("all_inverse_sites_covered")
            and evidence.get("all_atomisation_cancellations_certified")
            and evidence.get("localisation_predicates_complete")
        )
    if claim == "CPOBC_D2_N4_NONCOMMUTATIVE_REPRESENTATION_FOUND":
        return bool(
            evidence.get("exact_noncommutative_candidate")
            and evidence.get("all_original_relations_zero")
            and evidence.get("all_denominators_nonzero")
            and evidence.get("independent_oracle_pass")
        )
    if claim == "CPOBC_D2_N4_ONLY_COMMUTATIVE_SOLUTIONS":
        return bool(
            evidence.get("S1_complete")
            and evidence.get("S2_complete")
            and evidence.get("S3_complete")
            and evidence.get("all_source_branches_complete")
            and not evidence.get("any_timeout")
        )
    if claim == "CPOBC_D2_N4_NO_REPRESENTATION":
        return bool(
            evidence.get("forward_retraction_certificate")
            and evidence.get("all_strata_no_representation")
            and evidence.get("all_source_branches_complete")
            and evidence.get("all_saturations_complete")
        )
    if claim == "CPOBC_D2_INFINITE_NO_GO_UNDER_STRONG_PROFILE":
        return bool(
            evidence.get("finite_no_representation")
            and evidence.get("infinite_restriction_lemma")
            and evidence.get("same_semantic_profile")
            and evidence.get("same_nonsingularity_assumption")
            and evidence.get("finite_axiom_instances_included")
        )
    if claim in FORBIDDEN_PHYSICAL_CLAIMS:
        return False
    raise ValueError(f"unknown claim gate token: {claim}")


def _localised_identity_check(
    numerator: tuple[tuple[str, str], tuple[str, str]],
    denominator: str,
    zero: str,
) -> bool:
    return numerator == ((denominator, zero), (zero, denominator))


def _generic_adjugate_identity_passes() -> bool:
    a, b, c, d = sp.symbols("a b c d")
    numerator = sp.Matrix([[a, b], [c, d]])
    adjugate = sp.Matrix([[d, -b], [-c, a]])
    determinant = a * d - b * c
    return bool(
        numerator * adjugate == determinant * sp.eye(2)
        and adjugate * numerator == determinant * sp.eye(2)
    )


def compile_reconstruction_equivalence_v034() -> dict[str, Any]:
    """Audit all currently available forward/reverse equivalence obligations."""

    model = build_d2_rational_model()
    zero = model.arena.zero
    generic_adjugate_identity = _generic_adjugate_identity_passes()
    inverse_checks = []
    for stage in range(1, 5):
        forward_id = f"Q_{stage}"
        inverse_id = f"Q_{stage}^-1"
        forward = model.matrices[forward_id]
        inverse = model.matrices[inverse_id]
        left = model.multiply(
            inverse,
            forward,
            provenance=f"EQUIVALENCE:{inverse_id}:LEFT",
        )
        right = model.multiply(
            forward,
            inverse,
            provenance=f"EQUIVALENCE:{inverse_id}:RIGHT",
        )
        inverse_checks.append(
            {
                "inverse_site": inverse_id,
                "inverse_of_node": forward_id,
                "left_identity_in_localisation": _localised_identity_check(
                    left.numerator,
                    left.denominator,
                    zero,
                ),
                "right_identity_in_localisation": _localised_identity_check(
                    right.numerator,
                    right.denominator,
                    zero,
                ),
                "determinant_factor_registered": bool(
                    inverse.required_nonzero_factors
                ),
            }
        )
    for node_id, definition in sorted(model.node_definitions.items()):
        if definition["kind"] != "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            continue
        forward_id = definition["inverse_of_node"]
        forward = model.matrices[forward_id]
        inverse = model.matrices[node_id]
        reconstructed_inverse = model.inverse(
            forward,
            provenance=f"{node_id}:FIXED_D2_ADJUGATE",
            stage=int(definition["stage"]),
        )
        construction_match = bool(
            reconstructed_inverse.numerator == inverse.numerator
            and reconstructed_inverse.denominator == inverse.denominator
        )
        inverse_checks.append(
            {
                "inverse_site": node_id,
                "inverse_of_node": forward_id,
                "adjugate_construction_matches": construction_match,
                "left_identity_in_localisation": (
                    construction_match and generic_adjugate_identity
                ),
                "right_identity_in_localisation": (
                    construction_match and generic_adjugate_identity
                ),
                "determinant_factor_registered": bool(
                    inverse.required_nonzero_factors
                ),
            }
        )
    presentation = compile_q_presentation_n4()
    local_gc = compile_local_operator_gc_n4()
    atomisation = compile_atomisation_paths_n4()
    counts = presentation["counts"]
    obligations = {
        "CPOBC": {
            "original_relation_records": 641,
            "original_word_equations": 783,
            "identities_after_pullback": counts[
                "CPOBC_identities_after_substitution"
            ],
            "nontrivial_pullback_residuals": counts[
                "CPOBC_nontrivial_residuals"
            ],
            "inventory_complete": (
                counts["CPOBC_identities_after_substitution"]
                + counts["CPOBC_nontrivial_residuals"]
                == 783
            ),
            "logical_status": (
                "necessary_and_sufficient_on_the_reconstruction_image"
            ),
        },
        "strong_operator_MSR": {
            "original_constraints": 24,
            "identities_after_pullback": counts[
                "strong_MSR_identities_after_substitution"
            ],
            "nontrivial_pullback_residuals": counts[
                "strong_MSR_nontrivial_residuals"
            ],
            "inventory_complete": (
                counts["strong_MSR_identities_after_substitution"]
                + counts["strong_MSR_nontrivial_residuals"]
                == 24
            ),
            "reachable_state_profile_equivalence_claimed": False,
        },
        "strong_operator_GC": {
            "basis_relations": 320,
            "same_endpoint_path_equalities": 1529,
            "basis_connectivity_complete": (
                local_gc["counts"]["spanning_tree_basis_relations"] == 320
                and local_gc["counts"]["same_endpoint_path_pairs"] == 1529
            ),
            "identities_after_pullback": counts[
                "local_operator_GC_identities_after_eq107_eq108"
            ],
            "nontrivial_pullback_residuals": counts[
                "local_operator_GC_nontrivial_residuals"
            ],
            "fixed_vector_profile_equivalence_claimed": False,
        },
        "atomisation": {
            "complete_paths": atomisation["counts"][
                "complete_atomisation_paths"
            ],
            "square_instances": atomisation["counts"]["atomisation_steps"],
            "square_cancellation_certificate": (
                "MISSING_EXPLICIT_76_SITE_LOCALISATION_CANCELLATION"
            ),
        },
        "transition_reconstruction": {
            "occurrences": len(model.occurrence_matrices),
            "all_rationally_reconstructed": (
                len(model.occurrence_matrices) == 165
            ),
            "forward_retraction_on_all_occurrences": (
                "MISSING_EXPLICIT_165_SITE_COMPOSITE_IDENTITY"
            ),
        },
        "inverse_sites": {
            "count": len(inverse_checks),
            "checks": inverse_checks,
            "all_two_sided_in_localisation": all(
                record["left_identity_in_localisation"]
                and record["right_identity_in_localisation"]
                and record["determinant_factor_registered"]
                for record in inverse_checks
            ),
        },
    }
    evidence = {
        "forward_retraction_certificate": False,
        "reverse_original_relation_substitution": True,
        "all_inverse_sites_covered": obligations["inverse_sites"][
            "all_two_sided_in_localisation"
        ],
        "all_atomisation_cancellations_certified": False,
        "localisation_predicates_complete": False,
    }
    equivalent_allowed = claim_allowed(RECONSTRUCTION_EQUIVALENT, evidence)
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-reconstruction-equivalence-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "separate_reachable_state_profile": REACHABLE_STATE_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "obligations": obligations,
        "forward_direction": {
            "status": "PROVED_ONE_WAY_REDUCTION_NOT_RETRACTION",
            "basis": [
                "v0.3.2 Eq.(107)/(108) occurrence reduction",
                "v0.3.3 strong-GC atomisation Eq.(112) reduction",
                "fixed-d2 adjugate elimination at 26 inverse sites",
            ],
            "missing": [
                "165-site extraction/reconstruction composite identity",
                "76-site explicit cancellation certificate",
            ],
        },
        "reverse_direction": {
            "status": "CONDITIONAL_PULLBACK_SUFFICIENCY",
            "basis": [
                "700+83 cover all 783 CPOBC word equations",
                "21+3 cover all 24 strong-MSR constraints",
                "255+65 cover the 320 strong-GC basis relations",
                "all 165 transition occurrences are explicitly reconstructed",
            ],
            "condition": (
                "all numerator equations and every registered nonzero "
                "predicate hold in the selected source-index branch"
            ),
            "missing": [
                "full sequential saturation certificate",
                "literal branch has no extraction of independent Q5 from the n<=4 occurrence set",
            ],
        },
        "equivalence_claim_allowed": equivalent_allowed,
        "evidence": evidence,
        "assumptions": [
            "PAPER_STRONG_OPERATOR_PROFILE",
            "all necessary transition operators are nonsingular",
            "fixed matrix dimension d=2",
            "source-index branches are not mixed",
        ],
        "completeness_scope": (
            "complete inventory-level pullback audit; incomplete machine "
            "Tietze/retraction and saturation proof"
        ),
        "exact_numeric_distinction": "EXACT_STRUCTURAL_AUDIT",
        "unresolved_components": [
            "165-site forward retraction certificate",
            "76 atomisation-square cancellation certificates",
            "full branch/chart saturation",
            "literal Q5 extraction mismatch",
        ],
        "passed": True,
        "verdict": RECONSTRUCTION_PARTIAL,
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "obligations": obligations,
            "evidence": evidence,
            "verdict": payload["verdict"],
        }
    )
    return payload


def compile_source_branch_analysis_v034() -> dict[str, Any]:
    presentation = compile_q_presentation_n4()
    scalar_witness = scalar_s3_representation_certificate_v034()
    branches = {
        DERIVED_BRANCH: {
            "generator_inventory": ["Q_1", "Q_2", "Q_3", "Q_4"],
            "maximum_Q_index": 4,
            "relation_count": 25,
            "literal_source_basis": [
                "direct comparison of Eq.(112)",
                "Appendix Eq.(163)",
            ],
            "finite_classification_scope": "n<=4 Q1..Q4",
            "scalar_fixture_passed": scalar_witness["passed"],
            "verdict": "DERIVED_APPENDIX_QN_BRANCH_PARTIAL",
        },
        LITERAL_BRANCH: {
            "generator_inventory": ["Q_1", "Q_2", "Q_3", "Q_4", "Q_5"],
            "maximum_Q_index": 5,
            "relation_count": 25,
            "relations_requiring_Q5": presentation["counts"][
                "path_consistency_relations_per_source_index_branch"
            ]
            - 1,
            "literal_source_basis": ["printed PDF/HTML Eq.(113)"],
            "finite_classification_scope": (
                "n<=4 source-stage core plus independent Q5 path constraints"
            ),
            "Q5_identified_with_Q4": False,
            "scalar_fixture_passed": scalar_witness["passed"],
            "verdict": "LITERAL_PRINTED_QN_PLUS_1_BRANCH_PARTIAL",
        },
    }
    return {
        "schema_version": "final-theory-d2-source-branches-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "source_index_audit": SOURCE_VERDICT,
        "branches": branches,
        "branches_mixed": False,
        "author_confirmed_typo": False,
        "unresolved_components": [
            "authorial resolution of Q_n versus Q_(n+1)",
            "full exact classification in each branch",
        ],
        "verdict": SOURCE_VERDICT,
    }


def compile_claim_scope_v034(
    solver_campaign: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scalar_witness = scalar_s3_representation_certificate_v034()
    any_timeout = bool(
        solver_campaign
        and any(
            run["exit_status"] == "TIMEOUT"
            for run in solver_campaign["runs"]
        )
    )
    evidence = {
        "exact_commutative_finite_representation": scalar_witness["passed"],
        "exact_noncommutative_candidate": False,
        "S1_complete": False,
        "S2_complete": False,
        "S3_complete": False,
        "all_source_branches_complete": False,
        "any_timeout": any_timeout,
        "finite_no_representation": False,
        "early_noncommutativity_propagation_theorem": False,
    }
    return {
        "schema_version": "final-theory-d2-claim-scope-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "evidence": evidence,
        "allowed_claims": [
            "D2_RATIONAL_DAG_COMPLETE",
            "ALL_B_AUXILIARIES_DEFINITIONAL_D2",
            "CPOBC_D2_N4_COMMUTATIVE_REPRESENTATION_CERTIFIED",
            "FINITE_N4_S3_TRANSITION_ALGEBRA_COMMUTATIVE",
            RECONSTRUCTION_PARTIAL,
            VERDICT_PARTIAL,
            OVERALL,
        ],
        "forbidden_claims": list(FORBIDDEN_PHYSICAL_CLAIMS)
        + [
            "CPOBC_D2_N4_NONCOMMUTATIVE_REPRESENTATION_FOUND",
            "CPOBC_D2_N4_ONLY_COMMUTATIVE_SOLUTIONS",
            "CPOBC_D2_N4_NO_REPRESENTATION",
            "CPOBC_D2_INFINITE_NO_GO_UNDER_STRONG_PROFILE",
            RECONSTRUCTION_EQUIVALENT,
        ],
        "finite_d2_verdict": VERDICT_PARTIAL,
        "global_conditional_verdict": None,
        "physical_claim_ceiling": (
            "exact algebraic finite n<=4 representation certificate only"
        ),
        "unresolved_components": [
            "S1 exact saturated elimination",
            "S2 exact saturated elimination",
            "general S3 solution-locus elimination",
            "both source-index branch completions",
            "machine-certified rational reconstruction equivalence",
        ],
        "passed": True,
        "verdict": OVERALL,
    }
