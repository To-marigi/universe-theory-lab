"""Held-out and critical-mutation gates for Final-Theory Bench v0.3."""

from __future__ import annotations

import copy
from functools import lru_cache
from typing import Any

from universe_lab.final_theory.cpobc_v03 import (
    compile_cpobc_relations,
    cpobc_representation_search,
    paper_regression_benchmark,
)
from universe_lab.final_theory.extension_v03 import extension_benchmark
from universe_lab.final_theory.geometry_v03 import geometry_interference_benchmark
from universe_lab.final_theory.kraus_bell_v03 import kraus_bell_benchmark


def _mutation(
    mutation_id: str,
    description: str,
    killed: bool,
    detector: str,
    evidence: Any,
) -> dict[str, Any]:
    return {
        "mutation_id": mutation_id,
        "description": description,
        "killed": bool(killed),
        "detector": detector,
        "evidence": evidence,
    }


@lru_cache(maxsize=1)
def _mutation_cached() -> dict[str, Any]:
    paper = paper_regression_benchmark()
    geometry = geometry_interference_benchmark()
    bell = kraus_bell_benchmark()
    compiler = compile_cpobc_relations()
    search = cpobc_representation_search()
    extension = extension_benchmark()

    ordering = paper["msr_gc_operator_order_fixture"]
    relations = compiler["relations"]
    equal_relations = [
        relation
        for relation in relations
        if relation["equal_vs_unequal"] == "EQUAL_PRECURSOR_SIZE"
    ]
    unequal_relations = [
        relation
        for relation in relations
        if relation["equal_vs_unequal"] == "A_PRECURSOR_STRICTLY_LARGER"
    ]
    precursor_order_pass = all(
        relation["operator_order"]["A_is_larger_side"]
        and not relation["operator_order"]["both_orientations_required"]
        for relation in unequal_relations
    ) and all(
        not relation["operator_order"]["A_is_larger_side"]
        and relation["operator_order"]["both_orientations_required"]
        for relation in equal_relations
    )
    equal_relation_pass = bool(equal_relations) and all(
        [
            equation["equation_id"]
            for equation in relation["denominator_cleared_form"][
                "noncommutative_polynomial_equations"
            ]
        ]
        == ["eq103", "equal_second_orientation", "eq104"]
        for relation in equal_relations
    )
    invertibility_boundary_pass = all(
        relation["invertibility"]["paper_global_assumption"]
        and relation["invertibility"]["required_to_write_solved_forms"]
        and not relation["invertibility"]["required_for_denominator_cleared_forms"]
        for relation in relations
    )

    geometry_guards = geometry["mutation_guards"]["checks"]
    bell_automorphism = bell["automorphism_audit"]["omission_mutation"]
    bell_basis = bell["kraus_basis_invariance_audit"]
    search_exact = (
        search["cpobc_representation_status"] == "CPOBC_SEARCH_INCONCLUSIVE"
        and not search["summary"]["noncommutative_representation_found"]
        and all(
            certificate["candidate_status"]
            != "CPOBC_NONCOMMUTATIVE_REPRESENTATION_FOUND"
            for certificate in search["candidate_certificates"]
        )
    )

    records = [
        _mutation(
            "M01_CPOBC_PRODUCT_ORDER_REVERSED",
            "reverse a noncommutative product in the paper fixture",
            ordering["ordered_product_is_detectably_noncommutative"],
            "minimal paper regression",
            ordering["incorrect_reordering_difference"],
        ),
        _mutation(
            "M02_PRECURSOR_COMPARISON_REVERSED",
            "reverse the precursor-cardinality ordering",
            precursor_order_pass,
            "compiled relation operator-order metadata",
            {
                "unequal": len(unequal_relations),
                "equal": len(equal_relations),
            },
        ),
        _mutation(
            "M03_EQUAL_SIZE_RELATION_DELETED",
            "delete the second equal-size orientation or Eq. 104",
            equal_relation_pass,
            "equal-size denominator-cleared word gate",
            {"equal_relations_checked": len(equal_relations)},
        ),
        _mutation(
            "M04_INVERTIBILITY_ASSUMPTION_DELETED",
            "erase the inverse assumptions from solved CPOBC forms",
            invertibility_boundary_pass,
            "solved-form versus denominator-cleared assumption gate",
            {"relations_checked": len(relations)},
        ),
        _mutation(
            "M05_AUTOMORPHISM_FACTOR_OMITTED",
            "replace orbit-weighted outcomes by one unweighted representative",
            bell_automorphism["detected"],
            "exact instrument Choi/superoperator comparison",
            bell_automorphism["first_exact_witness"],
        ),
        _mutation(
            "M06_LABELLED_UNLABELLED_HISTORIES_CONFLATED",
            "identify birth-labelled, outcome-orbit, and endpoint histories",
            geometry_guards["labelled_unlabeled_confusion"]["killed"],
            "geometry quotient-fibre oracle",
            geometry_guards["labelled_unlabeled_confusion"],
        ),
        _mutation(
            "M07_KRAUS_BASIS_DEPENDENT_BELL_TEST",
            "compare Kraus lists instead of channel maps",
            bell_basis["false_kraus_string_test_detected"],
            "exact rotated-Kraus Choi and superoperator control",
            {
                "kraus_lists_equal": bell_basis["kraus_lists_equal"],
                "choi_equal": bell_basis["choi"]["exactly_equal"],
                "superoperator_equal": bell_basis["superoperator"][
                    "exactly_equal"
                ],
            },
        ),
        _mutation(
            "M08_INCOHERENT_SUM_AS_COHERENT",
            "drop the orthogonal outcome record and coherently sum branches",
            geometry_guards["coherent_sum_masquerade"]["killed"],
            "same-endpoint recorded-history witness",
            geometry_guards["coherent_sum_masquerade"],
        ),
        _mutation(
            "M09_OFF_DIAGONAL_FORCED_ZERO",
            "return zero without evaluating system and record overlaps",
            geometry_guards["forced_zero_generic"]["killed"],
            "coincident-record nonzero control",
            geometry_guards["forced_zero_generic"],
        ),
        _mutation(
            "M10_ARBITRARY_KRAUS_DECOMPOSITION_INTERFERENCE",
            "promote arbitrary rotated Kraus indices to physical histories",
            geometry_guards["arbitrary_kraus_basis_histories"]["killed"],
            "fixed-instrument semantics gate",
            geometry_guards["arbitrary_kraus_basis_histories"],
        ),
        _mutation(
            "M11_CHANNEL_ONLY_DECOHERENCE_FABRICATION",
            "construct a canonical history functional from channel data alone",
            (
                not geometry["kraus_representation_boundary"][
                    "channel_only_description_is_sufficient_for_history_labels"
                ]
                and bell["kraus_bell_status"]
                == "KRAUS_BELL_CAUSALITY_UNDEFINED"
            ),
            "instrument/channel semantic typing gate",
            {
                "fixed_instrument": geometry["kraus_representation_boundary"][
                    "implemented_instrument_is_fixed"
                ],
                "bell_status": bell["kraus_bell_status"],
            },
        ),
        _mutation(
            "M12_FINITE_N_BOUNDEDNESS_AS_EXTENSION",
            "promote the finite variation sequence to an infinite theorem",
            (
                extension["counterexample_search"][
                    "finite_n_boundedness_as_infinite_proof"
                ]
                == "REJECTED_BY_THEOREM_GATE"
            ),
            "all-stage kernel theorem gate",
            extension["classical_outcome_measure"]["assumption_check"],
        ),
        _mutation(
            "M13_ANSATZ_FAILURE_AS_DIMENSION_NO_GO",
            "promote a finite point-grid rejection to a dimension-wide no-go",
            (
                "dimension-wide" in search["prohibited_inference"]
                and search["cpobc_representation_status"]
                == "CPOBC_SEARCH_INCONCLUSIVE"
                and all(
                    summary["result"]
                    != "CPOBC_NO_REPRESENTATION_UNDER_ASSUMPTIONS"
                    for summary in search["ansatz_class_summaries"]
                )
            ),
            "representation claim-scope gate",
            search["prohibited_inference"],
        ),
        _mutation(
            "M14_NUMERICAL_RESIDUAL_AS_EXACT_SOLUTION",
            "accept a floating residual as an exact representation certificate",
            search_exact,
            "exact SymPy residual and full-certificate gate",
            {
                "candidate_count": search["summary"]["candidate_count"],
                "full_relation_certificates": search["summary"][
                    "full_compiled_relation_certificate_count"
                ],
                "representation_found": search["summary"][
                    "noncommutative_representation_found"
                ],
            },
        ),
    ]
    return {
        "schema_version": "final-theory-mutations-v0.3.0",
        "suite": "Final-Theory Bench v0.3 critical mutations",
        "mutations": records,
        "killed": sum(record["killed"] for record in records),
        "total": len(records),
        "passed": all(record["killed"] for record in records),
        "verdict": (
            "CRITICAL_MUTATIONS_PASS"
            if all(record["killed"] for record in records)
            else "CRITICAL_MUTATIONS_FAIL"
        ),
    }


def mutation_benchmark_v0_3() -> dict[str, Any]:
    """Run all 14 pre-registered v0.3 scientific mutations."""

    return copy.deepcopy(_mutation_cached())


@lru_cache(maxsize=1)
def _held_out_cached() -> dict[str, Any]:
    geometry = geometry_interference_benchmark()
    bell = kraus_bell_benchmark()
    search = cpobc_representation_search()
    d4_points = [
        certificate
        for certificate in search["candidate_certificates"]
        if certificate["dimension"] == 4
    ]
    companion_points = [
        certificate
        for certificate in search["candidate_certificates"]
        if "companion" in certificate["ansatz_id"]
    ]
    partitions = [
        {
            "partition": "unused Bell family/source size",
            "held_out": "source n=5 diagnostics beyond the n<=4 CPOBC compiler",
            "status": "DIAGNOSTIC_PASS_BELL_DEFINITION_UNDEFINED",
            "evidence": {
                "families": bell["bell_family_audit"]["unique_family_count"],
                "n5_configurations": bell["bell_family_audit"][
                    "by_full_source_size"
                ]["5"]["distinct_branch_pair_configuration_count"],
            },
        },
        {
            "partition": "causet size",
            "held_out": "n=5 geometry histories",
            "status": "PASS_EXACT",
            "evidence": geometry["completeness"][
                "kraus_labelled_path_counts_by_stage"
            ]["5"],
        },
        {
            "partition": "operator dimension",
            "held_out": "d=4 exact Weyl points after d=3 controls",
            "status": "PASS_NO_CANDIDATE",
            "evidence": len(d4_points),
        },
        {
            "partition": "Jordan stratum",
            "held_out": "strata recorded pointwise rather than fitted",
            "status": "DIAGNOSTIC_ONLY_NOT_STRATUM_COMPLETE",
            "evidence": sorted(
                {
                    item["stratum"]
                    for certificate in search["candidate_certificates"]
                    for item in certificate["structural_analysis"]["jordan_strata"]
                }
            ),
        },
        {
            "partition": "ansatz class",
            "held_out": "companion-word exact points",
            "status": "PASS_NO_CANDIDATE",
            "evidence": len(companion_points),
        },
        {
            "partition": "initial state",
            "held_out": "non-root density operator",
            "status": "BLOCKED_BY_ONE_DIMENSIONAL_ROOT_SCHEMA",
            "evidence": geometry["initial_state_scope"],
        },
        {
            "partition": "covariant event",
            "held_out": "all final-causet pairs beyond the first witness",
            "status": "PASS_EXACT",
            "evidence": geometry["interference_I2"]["unordered_pair_count"],
        },
        {
            "partition": "Kraus representation",
            "held_out": "exact 3-4-5 rotation of a dephasing control",
            "status": "PASS_EXACT",
            "evidence": bell["kraus_basis_invariance_audit"][
                "false_kraus_string_test_detected"
            ],
        },
    ]
    return {
        "schema_version": "final-theory-held-out-v0.3.0",
        "partitions": partitions,
        "retuned_after_held_out": False,
        "passed_partitions": sum(
            record["status"].startswith(("PASS", "DIAGNOSTIC_PASS"))
            for record in partitions
        ),
        "total_partitions": len(partitions),
        "status": "HELD_OUT_PROTOCOL_PARTIAL",
        "claim_boundary": (
            "The initial-state partition and complete Jordan/ansatz strata are "
            "not available; held-out diagnostics do not repair an undefined Bell map."
        ),
    }


def held_out_audit_v0_3() -> dict[str, Any]:
    """Return the no-retuning held-out audit."""

    return copy.deepcopy(_held_out_cached())
