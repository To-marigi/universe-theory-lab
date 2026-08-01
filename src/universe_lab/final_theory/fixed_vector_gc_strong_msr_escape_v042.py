"""Exact source-level escape from Eq. (112) for the 721 one-sided profile.

The witness is diagonal.  Its first character is the classical sequential
growth character with ``t_j = 1``.  Its second character is reconstructed
from the exact Eq. (107)/Eq. (108) reduction map using the ``t_j = 2**j``
gregarious values, except that ``G_p2-2`` is doubled.  The resulting point
satisfies every frozen CPOBC and strong-MSR source equation, and fixed-vector
GC on ``Omega = e_1``, but it violates operator GC and Eq. (112).

This is an escape-point certificate.  All matrices are diagonal, so it is not
a noncommutative witness and makes no claim about the truth value of the full
721 commutativity problem.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.weak_d2_v04 import (
    IDENTITY,
    OMEGA,
    ZERO,
    Matrix2,
    _csg_diagonal,
    _determinant,
    _evaluate_cpobc,
    _evaluate_cpobc_inverse_forms,
    _evaluate_msr,
    _matrix_apply,
    _matrix_multiply,
    _matrix_record,
    _matrix_subtract,
    _vector_record,
)

SCHEMA_VERSION = "final-theory-fixed-vector-gc-strong-msr-escape-v0.4.2"
VERSION = "0.4.2"
VERDICT = "FIXED_VECTOR_GC_STRONG_MSR_ESCAPE_CERTIFIED"
RESULT_PATH = "results/v0.4.2_fixed_vector_gc_strong_msr_escape.json"

_CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
_REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
_EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
_SOURCE_PATHS = (_CPOBC_PATH, _REDUCTION_PATH, _GC_PATH, _EQ112_PATH)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fraction(value: Fraction | int) -> str:
    return str(Fraction(value))


def _relation_code(relation: tuple[int, ...]) -> int:
    size = len(relation)
    return sum(row << (index * size) for index, row in enumerate(relation))


def _generator_assignments(reduction: dict[str, Any]) -> dict[str, Fraction]:
    assignments = {
        str(record["generator"]): Fraction(1, 3 ** int(record["stage"]))
        for record in reduction["generator_inventory"]
    }
    if assignments.get("G_p2-2") != Fraction(1, 9):
        raise AssertionError("the frozen p2-2 gregarious generator changed")
    assignments["G_p2-2"] = Fraction(2, 9)
    return assignments


def _evaluate_scalar_word(word: list[str], generators: dict[str, Fraction]) -> Fraction:
    product = Fraction(1)
    for token in word:
        inverse = token.endswith("^-1")
        generator = token.removesuffix("^-1")
        value = generators[generator]
        product = product / value if inverse else product * value
    return product


def _transition_assignments(
    reduction: dict[str, Any],
) -> tuple[
    dict[str, Matrix2],
    dict[str, Matrix2],
    dict[tuple[int, int, int], str],
]:
    generators = _generator_assignments(reduction)
    by_occurrence: dict[str, Matrix2] = {}
    by_orbit_sets: defaultdict[str, set[Matrix2]] = defaultdict(set)
    signature_to_orbit: dict[tuple[int, int, int], str] = {}

    for record in reduction["reduction_map"]:
        lower_right = sum(
            (
                Fraction(int(summand["coefficient"]))
                * _evaluate_scalar_word(summand["word"], generators)
                for summand in record["reduced_expression"]
            ),
            Fraction(0),
        )
        upper_left = _csg_diagonal(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
            coupling_ratio=None,
        )
        matrix: Matrix2 = (
            (upper_left, Fraction(0)),
            (Fraction(0), lower_right),
        )
        occurrence_id = str(record["occurrence_id"])
        orbit_id = str(record["orbit_id"])
        by_occurrence[occurrence_id] = matrix
        by_orbit_sets[orbit_id].add(matrix)

        signature = (
            int(record["stage"]),
            _relation_code(tuple(int(row) for row in record["source_relation_rows"])),
            int(record["precursor_code"]),
        )
        previous = signature_to_orbit.setdefault(signature, orbit_id)
        if previous != orbit_id:
            raise AssertionError("one decorated signature maps to multiple quotient orbits")

    inconsistent = {orbit: values for orbit, values in by_orbit_sets.items() if len(values) != 1}
    if inconsistent:
        raise AssertionError("the scalar reconstruction is inconsistent on an ON quotient orbit")
    by_orbit = {orbit: next(iter(values)) for orbit, values in by_orbit_sets.items()}
    return by_occurrence, by_orbit, signature_to_orbit


def _evaluate_gc(
    operator_gc: dict[str, Any],
    by_orbit: dict[str, Matrix2],
    signature_to_orbit: dict[tuple[int, int, int], str],
) -> dict[str, Any]:
    path_matrices: dict[str, Matrix2] = {}
    for paths in operator_gc["path_inventory"].values():
        for path in paths:
            product = IDENTITY
            for transition in path["transitions"]:
                signature_record = transition["quotient_signature"]
                signature = (
                    int(signature_record["stage"]),
                    int(signature_record["source_relation_code"]),
                    int(signature_record["precursor_code"]),
                )
                factor = by_orbit[signature_to_orbit[signature]]
                product = _matrix_multiply(factor, product)
            path_matrices[str(path["path_id"])] = product

    records = []
    for relation in operator_gc["all_pair_derivations"]:
        left = path_matrices[relation["left_path_id"]]
        right = path_matrices[relation["right_path_id"]]
        residual = _matrix_subtract(left, right)
        fixed_residual = _matrix_apply(residual, OMEGA)
        records.append(
            {
                "endpoint_causet_id": relation["endpoint_causet_id"],
                "left_path_id": relation["left_path_id"],
                "right_path_id": relation["right_path_id"],
                "operator_residual": _matrix_record(residual),
                "fixed_vector_residual": _vector_record(fixed_residual),
                "strong_operator_zero": residual == ZERO,
                "fixed_vector_zero": fixed_residual == (Fraction(0), Fraction(0)),
            }
        )
    failures = [record for record in records if not record["strong_operator_zero"]]
    return {
        "checked_same_endpoint_path_pairs": len(records),
        "all_fixed_vector_equalities_hold": all(record["fixed_vector_zero"] for record in records),
        "fixed_vector_failure_count": sum(not record["fixed_vector_zero"] for record in records),
        "all_strong_operator_equalities_hold": not failures,
        "strong_operator_failure_count": len(failures),
        "first_strong_operator_failure": failures[0] if failures else None,
    }


def _find_gregarious_matrix(
    reduction: dict[str, Any], assignments: dict[str, Matrix2], source_id: str
) -> Matrix2:
    matches = [
        assignments[record["occurrence_id"]]
        for record in reduction["reduction_map"]
        if record["source_id"] == source_id
        and int(record["precursor_code"]) == 0
        and record["transition_kind"] == "GREGARIOUS"
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one gregarious occurrence at {source_id}")
    return matches[0]


def _eq112_escape(
    eq112: dict[str, Any],
    reduction: dict[str, Any],
    assignments: dict[str, Matrix2],
) -> dict[str, Any]:
    records = [record for record in eq112["path_reductions"] if record["causet_id"] == "p2-2"]
    if len(records) != 1:
        raise AssertionError("the frozen p2-2 Eq. (112) path reduction changed")
    record = records[0]
    word = record["G_reduced_ordered_word"]
    if len(word) != 3 or not word[0].startswith("BDEF:") or word[1] != "Q_2":
        raise AssertionError("the p2-2 Eq. (112) word is no longer B Q_2 B^-1")
    if word[2] != "BINV:" + word[0].removeprefix("BDEF:"):
        raise AssertionError("the p2-2 Eq. (112) inverse factor changed")

    actual = _find_gregarious_matrix(reduction, assignments, "p2-2")
    q2 = _find_gregarious_matrix(reduction, assignments, "p2-0")
    # Every witness factor is diagonal.  Hence any Eq. (112) B word is
    # diagonal and B Q_2 B^-1 is exactly Q_2.
    residual = _matrix_subtract(actual, q2)
    return {
        "causet_id": "p2-2",
        "frozen_reduction_word": word,
        "actual_G_p2_2": _matrix_record(actual),
        "predicted_B_Q2_B_inverse": _matrix_record(q2),
        "operator_residual": _matrix_record(residual),
        "nonzero": residual != ZERO,
        "justification": (
            "All witness transitions are nonsingular diagonal matrices, so the frozen "
            "B word commutes with Q_2 and B Q_2 B^-1 = Q_2."
        ),
    }


def compile_fixed_vector_gc_strong_msr_escape_v042(root: Path) -> dict[str, Any]:
    """Compile and directly verify the exact QQ escape point."""

    root = root.resolve()
    source_hashes = {relative: _sha256(root / relative) for relative in _SOURCE_PATHS}
    cpobc = _load_json(root / _CPOBC_PATH)
    reduction = _load_json(root / _REDUCTION_PATH)
    operator_gc = _load_json(root / _GC_PATH)
    eq112 = _load_json(root / _EQ112_PATH)

    assignments, by_orbit, signature_to_orbit = _transition_assignments(reduction)
    cpobc_check = _evaluate_cpobc(cpobc, assignments)
    inverse_check = _evaluate_cpobc_inverse_forms(cpobc, assignments)
    msr_check = _evaluate_msr(cpobc, assignments)
    gc_check = _evaluate_gc(operator_gc, by_orbit, signature_to_orbit)
    eq112_check = _eq112_escape(eq112, reduction, assignments)

    determinants = {identifier: _determinant(matrix) for identifier, matrix in assignments.items()}
    expected_counts = {
        "transition_occurrences": 165,
        "transition_orbits": 131,
        "CPOBC_word_equations": 783,
        "CPOBC_inverse_forms": 712,
        "strong_MSR_constraints": 24,
        "same_endpoint_GC_path_pairs": 1529,
    }
    actual_counts = {
        "transition_occurrences": len(assignments),
        "transition_orbits": len(by_orbit),
        "CPOBC_word_equations": cpobc_check["checked_equations"],
        "CPOBC_inverse_forms": inverse_check["checked_inverse_containing_equations"],
        "strong_MSR_constraints": msr_check["checked_constraints"],
        "same_endpoint_GC_path_pairs": gc_check["checked_same_endpoint_path_pairs"],
    }
    if actual_counts != expected_counts:
        raise AssertionError("the frozen finite source inventory count changed")

    certified = (
        all(determinant != 0 for determinant in determinants.values())
        and cpobc_check["all_zero"]
        and inverse_check["all_zero"]
        and msr_check["all_strong_operator_equalities_hold"]
        and gc_check["all_fixed_vector_equalities_hold"]
        and not gc_check["all_strong_operator_equalities_hold"]
        and eq112_check["nonzero"]
    )
    if not certified:
        raise AssertionError("the exact 721 escape-point obligations did not all close")

    occurrence_records = []
    reduction_by_occurrence = {
        record["occurrence_id"]: record for record in reduction["reduction_map"]
    }
    for occurrence_id in sorted(assignments):
        record = reduction_by_occurrence[occurrence_id]
        occurrence_records.append(
            {
                "occurrence_id": occurrence_id,
                "orbit_id": record["orbit_id"],
                "source_id": record["source_id"],
                "stage": int(record["stage"]),
                "precursor_code": int(record["precursor_code"]),
                "matrix": _matrix_record(assignments[occurrence_id]),
                "determinant": _fraction(determinants[occurrence_id]),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "verdict": VERDICT,
        "finite_scope": "ON quotient, source stages n<=4, d=2, GL_2(QQ)",
        "source_artifacts": source_hashes,
        "construction": {
            "initial_vector": ["1", "0"],
            "matrix_form": "diag(p_e, r_e)",
            "upper_character": "classical sequential growth with t_j=1",
            "lower_character_rule": (
                "Evaluate the frozen Eq.(107)/Eq.(108) reduction map at "
                "Q_n=3^-n and G_c=3^-stage(c), except G_p2-2=2/9."
            ),
            "uses_Eq112": False,
            "uses_solver": False,
            "uses_floating_point": False,
        },
        "counts": actual_counts,
        "nonsingularity": {
            "checked_occurrences": len(determinants),
            "zero_determinant_count": sum(value == 0 for value in determinants.values()),
            "all_nonzero": all(value != 0 for value in determinants.values()),
        },
        "direct_substitution": {
            "CPOBC": {
                "checked_equations": cpobc_check["checked_equations"],
                "failure_count": sum(not record["zero"] for record in cpobc_check["records"]),
                "all_zero": cpobc_check["all_zero"],
            },
            "CPOBC_inverse_forms": {
                "checked_equations": inverse_check["checked_inverse_containing_equations"],
                "failure_count": sum(not record["zero"] for record in inverse_check["records"]),
                "all_zero": inverse_check["all_zero"],
            },
            "strong_MSR": {
                "checked_constraints": msr_check["checked_constraints"],
                "failure_count": msr_check["strong_operator_failure_count"],
                "all_zero": msr_check["all_strong_operator_equalities_hold"],
            },
            "fixed_vector_GC": gc_check,
            "Eq112_escape": eq112_check,
        },
        "occurrence_assignments": occurrence_records,
        "interpretation": {
            "proved": (
                "The fixed-vector-GC/strong-MSR source profile contains exact nonsingular "
                "points outside the frozen strong-GC Eq.(112) reconstruction locus."
            ),
            "not_proved": (
                "The witness is diagonal and does not decide whether the full 721 profile "
                "forces Q_1,...,Q_4 to commute."
            ),
        },
        "passed": True,
    }


def write_fixed_vector_gc_strong_msr_escape_v042(root: Path) -> Path:
    result = compile_fixed_vector_gc_strong_msr_escape_v042(root)
    target = root.resolve() / RESULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_fixed_vector_gc_strong_msr_escape_v042(repository_root))
