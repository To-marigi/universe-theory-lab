"""Critical scientific mutation gates for Final-Theory Bench v0.3.1."""

from __future__ import annotations

import copy
from functools import lru_cache
from typing import Any

from universe_lab.final_theory.commutative_csg_v031 import (
    commutative_csg_reference_benchmark,
)
from universe_lab.final_theory.cpobc_v031 import compiler_mutation_checks_v031


def _record(
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
    compiler = compiler_mutation_checks_v031()
    csg = commutative_csg_reference_benchmark(5)
    checks = compiler["checks"]
    csg_guards = csg["mutation_guards"]

    compiler_specs = [
        (
            "M01_CPOBC_PRODUCT_ORDER_REVERSED",
            "reverse the CPOBC noncommutative product order",
            "CPOBC_product_order_reversal",
        ),
        (
            "M02_PRECURSOR_COMPARISON_REVERSED",
            "reverse greater/equal precursor-cardinality selection",
            "precursor_comparison_reversal",
        ),
        (
            "M03_EQUAL_SIZE_AUXILIARY_DELETED",
            "delete the equal-size second orientation and auxiliary relation",
            "equal_size_auxiliary_deletion",
        ),
        (
            "M04_INVERSE_CANCELLATION_MISAPPLIED",
            "cancel non-adjacent inverse tokens in a free noncommutative word",
            "incorrect_inverse_cancellation",
        ),
        (
            "M05_INVERTIBILITY_CONSTRAINT_DELETED",
            "drop the two-sided inverse-variable equations",
            "invertibility_constraint_deletion",
        ),
        (
            "M06_GC_RELATION_DELETED",
            "erase general-covariance path dependencies",
            "GC_dependency_deletion",
        ),
        (
            "M07_MSR_RELATION_DELETED",
            "erase Markov-sum-rule dependencies",
            "MSR_dependency_deletion",
        ),
        (
            "M08_AUTOMORPHISM_MULTIPLICITY_OMITTED",
            "replace exact transition orbit multiplicities by one",
            "automorphism_multiplicity_deletion",
        ),
        (
            "M09_LABELLED_UNLABELLED_CONFLATED",
            "identify labelled occurrences with unlabeled transition orbits",
            "labelled_unlabelled_confusion",
        ),
        (
            "M10_COMMUTATIVE_WORD_NORMALISATION",
            "sort a genuinely noncommutative operator word",
            "commutative_word_normalisation",
        ),
        (
            "M11_SIMILARITY_SOLUTION_DUPLICATED",
            "count a simultaneously similar representation twice",
            "similarity_equivalent_solution_duplicate",
        ),
        (
            "M12_FINITE_GRID_AS_D3_NO_GO",
            "promote bounded search failure to a dimension-wide theorem",
            "finite_grid_no_go_overclaim",
        ),
        (
            "M13_NUMERICAL_RESIDUAL_AS_EXACT_ZERO",
            "accept a floating residual as an exact solution",
            "numerical_zero_as_exact",
        ),
        (
            "M14_SINGULAR_AS_NONSINGULAR",
            "accept a singular transition matrix under nonsingular CPOBC",
            "singular_as_nonsingular",
        ),
    ]
    records = [
        _record(
            mutation_id,
            description,
            checks[key],
            "v0.3.1 exact CPOBC compiler/search scientific gate",
            {"guard": key, "detected": checks[key]},
        )
        for mutation_id, description, key in compiler_specs
    ]
    records.extend(
        [
            _record(
                "M15_CSG_OFF_DIAGONAL_FORCED_ZERO",
                "force the commutative CSG off-diagonal decoherence entry to zero",
                csg_guards["force_off_diagonal_D_to_zero"],
                "exact physically distinct covariant-event witness",
                csg["decoherence_functional"]["physical_interference_witness"],
            ),
            _record(
                "M16_ORTHOGONAL_RECORD_BASELINE_CALLED_COHERENT",
                "misreport the v0.3 orthogonal-record diagonal baseline as coherent",
                csg_guards[
                    "misclassify_orthogonal_record_baseline_as_coherent"
                ],
                "commutative-CSG versus orthogonal-record semantic comparison",
                csg["orthogonal_record_baseline_comparison"],
            ),
            _record(
                "M17_PAPER_RESULT_REPORTED_AS_NEW",
                "count a literature-locked scalar CSG result as project novelty",
                csg_guards["paper_result_reported_as_novel"]
                and checks["paper_result_reported_as_new"],
                "literature-classification and novelty gate",
                {
                    "csg_classification": csg["literature_classification"],
                    "compiler_guard": checks["paper_result_reported_as_new"],
                },
            ),
            _record(
                "M18_EQ145_OMITTED_FALSE_SURVIVOR",
                "promote the scaled-Heisenberg necessary-relation survivor after omitting Eq.145",
                checks["omit_eq145_false_survivor"],
                "exact Eq.145 saturation/Groebner certificate",
                {"guard": "omit_eq145_false_survivor", "detected": True},
            ),
        ]
    )
    passed = all(record["killed"] for record in records)
    return {
        "schema_version": "final-theory-mutations-v0.3.1",
        "suite": "Final-Theory Bench v0.3.1 critical scientific mutations",
        "mandatory_mutation_count": 17,
        "additional_mutation_count": 1,
        "mutations": records,
        "killed": sum(record["killed"] for record in records),
        "total": len(records),
        "passed": passed,
        "verdict": (
            "CRITICAL_MUTATIONS_PASS"
            if passed
            else "CRITICAL_MUTATIONS_FAIL"
        ),
    }


def mutation_benchmark_v0_3_1() -> dict[str, Any]:
    """Return all mandated mutations plus the Eq.145 scoped-no-go guard."""

    return copy.deepcopy(_mutation_cached())
