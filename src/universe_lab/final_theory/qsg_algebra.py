"""Exact and bounded-ansatz audits for operator-valued QSG.

The implementation keeps reference reproduction separate from new search.  A
failed finite matrix-library search is always reported as inconclusive, never as
a no-representation theorem.
"""

from __future__ import annotations

import itertools
from functools import cache, lru_cache
from typing import Any

import sympy as sp


def _is_zero(matrix: sp.MatrixBase) -> bool:
    return all(sp.simplify(entry) == 0 for entry in matrix)


def _commutator(left: sp.MatrixBase, right: sp.MatrixBase) -> sp.Matrix:
    return sp.Matrix(left * right - right * left)


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [str(sp.simplify(entry)) for entry in matrix.row(row)]
        for row in range(matrix.rows)
    ]


def pauli_matrices() -> tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    """Return the exact Pauli matrices."""

    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    sigma_y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    return sigma_x, sigma_y, sigma_z


def time_ordered_reference_audit() -> dict[str, Any]:
    """Verify the algebraic implication used in the TOBC commutativity proof."""

    q1 = sp.Matrix([[2, 1], [0, 3]])
    qn = sp.Matrix([[5, 0], [1, 7]])
    inverse_residual = q1.inv() * qn - qn * q1.inv()
    commutator = _commutator(q1, qn)
    implication_identity = sp.simplify(q1 * inverse_residual * q1 + commutator)
    return {
        "ordering": "TOBC",
        "source_equations": [49, 64, 65, 69, 70],
        "verified_identity": "Q1*R*Q1 = -[Q1,Qn]",
        "identity_residual": _matrix_record(implication_identity),
        "identity_exact": _is_zero(implication_identity),
        "noncommuting_probe_rejected": not _is_zero(inverse_residual),
        "result_boundary": (
            "This verifies the invertible-matrix implication used by the "
            "induction; the paper's all-stage combinatorial induction is "
            "tracked as a source theorem rather than re-proved by enumeration."
        ),
    }


def non_time_ordered_reference_audit() -> dict[str, Any]:
    """Verify the n=2 NTOBC relation that forces [Q1,Q2]=0."""

    q1 = sp.Matrix([[2, 1], [0, 3]])
    q2 = sp.Matrix([[5, 0], [1, 7]])
    identity = sp.eye(2)
    a1 = q1.inv() * q2 - q2
    a2 = identity - 2 * q1.inv() * q2 + q2
    relation_91_residual = _commutator(a1 * q2.inv(), a2 * q2.inv())
    commuting_q1 = sp.diag(2, 3)
    commuting_q2 = sp.diag(5, 7)
    commuting_a1 = commuting_q1.inv() * commuting_q2 - commuting_q2
    commuting_a2 = (
        identity - 2 * commuting_q1.inv() * commuting_q2 + commuting_q2
    )
    commuting_residual = _commutator(
        commuting_a1 * commuting_q2.inv(),
        commuting_a2 * commuting_q2.inv(),
    )
    return {
        "ordering": "NTOBC",
        "source_equations": [71, 83, 91, 92, 93, 95, 98],
        "noncommuting_probe_relation_91_residual": _matrix_record(
            relation_91_residual
        ),
        "noncommuting_probe_rejected": not _is_zero(relation_91_residual),
        "commuting_probe_passes": _is_zero(commuting_residual),
        "result_boundary": (
            "The exact n=2 forcing relation is reproduced. The paper's "
            "subsequent induction is recorded separately as a source result."
        ),
    }


def causal_past_pauli_reference_audit() -> dict[str, Any]:
    """Reproduce exact Pauli obstructions from CPOBC necessary relations."""

    sigma_x, sigma_y, sigma_z = pauli_matrices()
    lhs = sigma_x * sigma_z.inv() * sigma_y
    rhs = sigma_y * sigma_z.inv() * sigma_x
    triple_residual = sp.simplify(lhs - rhs)

    q1 = 2 * sigma_x
    q2 = 3 * sigma_y
    q3 = 5 * sigma_x
    q4 = 7 * sigma_y
    identity = sp.eye(2)
    a12 = (identity - q1) * q2 * q1.inv()
    a22 = identity - 2 * a12 - q2
    a23 = a22 * q3 * q2.inv()
    s1 = (
        (identity - q1)
        * a22
        * q3
        * a22.inv()
        * q1.inv()
        * a23
    )
    s2 = (
        a22
        * a12
        * q3
        * a12.inv()
        * q2.inv()
        * a12
        * q3
        * q2.inv()
    )
    path_residual = _commutator(s2.inv() * s1, q4)
    invertibility = {
        "Q1": q1.det() != 0,
        "Q2": q2.det() != 0,
        "Q3": q3.det() != 0,
        "Q4": q4.det() != 0,
        "I-Q1": (identity - q1).det() != 0,
        "A1_2": a12.det() != 0,
        "A2_2": a22.det() != 0,
        "S1": s1.det() != 0,
        "S2": s2.det() != 0,
    }
    return {
        "ordering": "CPOBC",
        "source_equations": [114, 119, 137, 140, 141, 150, 151, 159, 162, 163, 164],
        "three_distinct_pauli": {
            "lhs": _matrix_record(lhs),
            "rhs": _matrix_record(rhs),
            "residual": _matrix_record(triple_residual),
            "necessary_relation_violated": not _is_zero(triple_residual),
        },
        "two_pauli_path_probe": {
            "scalars": [2, 3, 5, 7],
            "pattern": ["sigma_x", "sigma_y", "sigma_x", "sigma_y"],
            "invertibility": invertibility,
            "equation_163_residual": _matrix_record(path_residual),
            "rejected_exactly": all(invertibility.values())
            and not _is_zero(path_residual),
        },
        "reproduction_status": "PARTIAL_EXACT_REPRODUCTION",
        "unreproduced_reference_scope": (
            "A continuous-parameter elimination for every two-Pauli assignment "
            "listed in the appendix has not been independently completed."
        ),
    }


def _ansatz_library(dimension: int) -> tuple[sp.Matrix, ...]:
    identity = sp.eye(dimension)
    diagonal_a = sp.diag(*range(2, dimension + 2))
    diagonal_b = sp.diag(*range(dimension + 2, 2 * dimension + 2))
    upper = 2 * identity
    lower = 3 * identity
    for index in range(dimension - 1):
        upper[index, index + 1] = 1
        lower[index + 1, index] = 1
    cycle = sp.zeros(dimension)
    for index in range(dimension):
        cycle[index, (index + 1) % dimension] = 1
    cycle = cycle + 2 * identity
    reverse = sp.zeros(dimension)
    for index in range(dimension):
        reverse[index, dimension - index - 1] = 1
    reverse = reverse + 3 * identity
    return diagonal_a, diagonal_b, upper, lower, cycle, reverse


def _cpo_core_relations(generators: tuple[sp.Matrix, ...]) -> bool:
    for n, k, m in itertools.permutations(range(len(generators)), 3):
        if not _is_zero(
            generators[n] * generators[k].inv() * generators[m]
            - generators[m] * generators[k].inv() * generators[n]
        ):
            return False
    q1, q2 = generators[:2]
    if not _is_zero(
        _commutator(q1 * q2.inv(), q1.inv() * q2)
    ):
        return False
    return True


@cache
def bounded_representation_search(dimension: int) -> dict[str, Any]:
    """Search a declared finite rational matrix library exactly."""

    library = _ansatz_library(dimension)
    tested = 0
    noncommuting_tested = 0
    core_survivors: list[tuple[int, ...]] = []
    for indices in itertools.product(range(len(library)), repeat=4):
        tested += 1
        generators = tuple(library[index] for index in indices)
        if all(
            _is_zero(_commutator(generators[left], generators[right]))
            for left in range(4)
            for right in range(left + 1, 4)
        ):
            continue
        noncommuting_tested += 1
        if _cpo_core_relations(generators):
            core_survivors.append(indices)
    return {
        "dimension": dimension,
        "ansatz": (
            "ordered four-tuples from six exact rational matrices: two "
            "diagonal, upper/lower Jordan, shifted cycle, shifted reversal"
        ),
        "tuple_count": tested,
        "noncommuting_tuple_count": noncommuting_tested,
        "core_relation_survivor_count": len(core_survivors),
        "core_relation_survivor_sample": [
            list(item) for item in core_survivors[:20]
        ],
        "full_relation_certificate_count": 0,
        "exact_arithmetic": True,
        "search_result": (
            "NO_CANDIDATE_IN_DECLARED_ANSATZ"
            if not core_survivors
            else "CORE_RELATION_CANDIDATES_REQUIRE_FULL_RELATION_AUDIT"
        ),
        "claim_boundary": (
            "This finite library is not complete in dimension "
            f"{dimension}; absence of a survivor is not a no-go theorem."
        ),
    }


@lru_cache(maxsize=1)
def qsg_algebra_benchmark() -> dict[str, Any]:
    """Run reference audits and bounded d=3/d=4 exploration."""

    time_ordered = time_ordered_reference_audit()
    non_time_ordered = non_time_ordered_reference_audit()
    causal_past = causal_past_pauli_reference_audit()
    searches = [
        bounded_representation_search(3),
        bounded_representation_search(4),
    ]
    reference_core_pass = (
        time_ordered["identity_exact"]
        and time_ordered["noncommuting_probe_rejected"]
        and non_time_ordered["noncommuting_probe_rejected"]
        and non_time_ordered["commuting_probe_passes"]
        and causal_past["three_distinct_pauli"]["necessary_relation_violated"]
        and causal_past["two_pauli_path_probe"]["rejected_exactly"]
    )
    core_candidates = any(
        search["core_relation_survivor_count"] for search in searches
    )
    return {
        "suite": "QSG algebra v0.2",
        "source": "arXiv:2603.25503v1",
        "reference_reproduction": {
            "time_ordered": time_ordered,
            "non_time_ordered": non_time_ordered,
            "causal_past_ordered": causal_past,
            "core_checks_passed": reference_core_pass,
            "status": "PARTIAL_EXACT_REPRODUCTION",
        },
        "new_search": {
            "dimensions": searches,
            "core_relation_candidates_found": core_candidates,
            "noncommutative_representation_found": False,
            "status": "QSG_SEARCH_INCONCLUSIVE",
        },
        "qsg_algebra_status": "QSG_SEARCH_INCONCLUSIVE",
        "prohibited_inference": (
            "The search does not justify QSG_NO_REPRESENTATION_UP_TO_D."
        ),
    }
