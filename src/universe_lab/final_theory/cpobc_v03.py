"""Conservative Track-A CPOBC tools for Final-Theory Bench v0.3.

This module has three deliberately separate jobs:

* a small exact regression of the conventions used in arXiv:2603.25503v1;
* a finite combinatorial compiler for Bell families through source stage four;
* a bounded exact search over explicitly declared matrix ansatz classes.

The relation compiler instantiates only the CPOBC relations in Eqs. (103)--(106).
It does not claim that its finite instances are independent algebraic relations,
and it does not reproduce the paper's TOBC/NTOBC arguments or full appendix.
Likewise, exhaustion of a finite representation ansatz is never promoted to a
dimension-wide no-representation statement.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Any

import sympy as sp

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    automorphisms,
    canonicalize,
    causet_id,
    downsets,
    enumerate_unlabeled_posets,
    maximal_elements_in_subset,
    precursor_orbit,
    relation_from_code,
)

PAPER_ID = "arXiv:2603.25503v1"
PAPER_LOCAL_TEXT = (
    "references/text/"
    "2603.25503v1_srivastava-surya_quantum-bell-causality-qsg.txt"
)
COMPILER_MAX_STAGE = 4


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.simplify(entry) == 0 for entry in matrix)


def _exact_string(value: Any) -> str:
    return str(sp.factor(sp.simplify(value)))


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [_exact_string(matrix[row, column]) for column in range(matrix.cols)]
        for row in range(matrix.rows)
    ]


def _matrix_certificate(matrix: sp.MatrixBase) -> dict[str, Any]:
    simplified = sp.Matrix(matrix).applyfunc(sp.simplify)
    record = _matrix_record(simplified)
    return {
        "matrix": record,
        "sha256": _stable_hash(record),
        "zero": _is_zero_matrix(simplified),
        "rank": int(simplified.rank()),
        "trace": _exact_string(sp.trace(simplified)),
        "determinant": _exact_string(simplified.det()),
    }


def _commutator(left: sp.MatrixBase, right: sp.MatrixBase) -> sp.Matrix:
    return sp.Matrix(left * right - right * left).applyfunc(sp.simplify)


def _pauli_matrices() -> tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    sigma_y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    return sigma_x, sigma_y, sigma_z


def _inverse_token(token: str) -> str:
    suffix = "^-1"
    return token[: -len(suffix)] if token.endswith(suffix) else token + suffix


def _free_reduce(word: tuple[str, ...]) -> tuple[str, ...]:
    reduced: list[str] = []
    for token in word:
        if reduced and reduced[-1] == _inverse_token(token):
            reduced.pop()
        else:
            reduced.append(token)
    return tuple(reduced)


@lru_cache(maxsize=1)
def _paper_regression_cached() -> dict[str, Any]:
    """Build the small, exact paper-convention regression."""

    sigma_x, sigma_y, sigma_z = _pauli_matrices()

    # Eq. (119), specialized to two Pauli directions, and Eq. (130).
    q1 = 2 * sigma_x
    q2 = 3 * sigma_y
    q3 = 5 * sigma_x
    q4 = 7 * sigma_y
    relation_119 = q2 * q1.inv() * q3 - q3 * q1.inv() * q2
    relation_130 = _commutator(q1 * q2.inv(), q1.inv() * q2)

    # The three-distinct-Pauli obstruction in Eq. (164).
    distinct_pauli = (
        sigma_x * sigma_z.inv() * sigma_y
        - sigma_y * sigma_z.inv() * sigma_x
    )

    # Eqs. (140), (141), (150), (151), (159), and (162), followed by
    # the representative two-path relation Eq. (163).
    identity_2 = sp.eye(2)
    a1_2 = (identity_2 - q1) * q2 * q1.inv()
    a2_2 = identity_2 - 2 * a1_2 - q2
    a1_3 = a1_2 * q3 * q2.inv()
    a2_3 = a2_2 * q3 * q2.inv()
    s1 = (
        (identity_2 - q1)
        * a2_2
        * q3
        * a2_2.inv()
        * q1.inv()
        * a2_3
    )
    s2 = (
        a2_2
        * a1_2
        * q3
        * a1_2.inv()
        * q2.inv()
        * a1_2
        * q3
        * q2.inv()
    )
    relation_163 = _commutator(s2.inv() * s1, q4)
    pauli_invertibility = {
        "Q1": _exact_string(q1.det()),
        "Q2": _exact_string(q2.det()),
        "Q3": _exact_string(q3.det()),
        "Q4": _exact_string(q4.det()),
        "I_minus_Q1": _exact_string((identity_2 - q1).det()),
        "A1_2": _exact_string(a1_2.det()),
        "A2_2": _exact_string(a2_2.det()),
        "S1": _exact_string(s1.det()),
        "S2": _exact_string(s2.det()),
    }
    pauli_all_invertible = all(
        sp.simplify(value.det()) != 0
        for value in (
            q1,
            q2,
            q3,
            q4,
            identity_2 - q1,
            a1_2,
            a2_2,
            s1,
            s2,
        )
    )

    # A separate rational fixture makes MSR, GC, and multiplication order
    # visible without relying on a Pauli identity.
    rational_q1 = sp.Matrix([[2, 1], [0, 3]])
    rational_q2 = sp.Matrix([[5, 0], [1, 7]])
    rational_identity = sp.eye(2)
    rational_a1_2 = (
        (rational_identity - rational_q1)
        * rational_q2
        * rational_q1.inv()
    )
    rational_a2_2 = rational_identity - 2 * rational_a1_2 - rational_q2
    rational_g2 = (
        (rational_identity - rational_q1)
        * rational_q2
        * (rational_identity - rational_q1).inv()
    )
    cpobc_residual = (
        rational_a1_2 * rational_q1
        - (rational_identity - rational_q1) * rational_q2
    )
    msr_residual = (
        rational_q2 + 2 * rational_a1_2 + rational_a2_2 - rational_identity
    )
    gc_residual = (
        rational_g2 * (rational_identity - rational_q1)
        - rational_a1_2 * rational_q1
    )
    reordered_a1_2 = (
        rational_q2
        * rational_q1.inv()
        * (rational_identity - rational_q1)
    )
    ordering_guard = rational_a1_2 - reordered_a1_2

    eq103_right_clearing = _free_reduce(
        ("A_m", "A_prime_n", "A_prime_m^-1", "A_prime_m")
    )
    eq106_left_clearing = _free_reduce(
        ("A_prime_m", "A_prime_m^-1", "A_prime_n", "A_m")
    )
    eq104_route = [
        ["A_prime_m", "A_m", "A_prime_n"],
        ["A_prime_m", "A_n", "A_prime_m"],
        ["A_prime_n", "A_m", "A_prime_m"],
    ]
    convention_pass = (
        eq103_right_clearing == ("A_m", "A_prime_n")
        and eq106_left_clearing == ("A_prime_n", "A_m")
        and eq104_route[-1]
        == ["A_prime_n", "A_m", "A_prime_m"]
    )

    passed = (
        convention_pass
        and _is_zero_matrix(relation_119)
        and _is_zero_matrix(relation_130)
        and not _is_zero_matrix(distinct_pauli)
        and pauli_all_invertible
        and not _is_zero_matrix(relation_163)
        and _is_zero_matrix(cpobc_residual)
        and _is_zero_matrix(msr_residual)
        and _is_zero_matrix(gc_residual)
        and not _is_zero_matrix(ordering_guard)
    )
    return {
        "schema_version": "final-theory-paper-regression-v0.3.0",
        "suite": "CPOBC v0.3 minimal paper regression",
        "source": {
            "paper": PAPER_ID,
            "local_extracted_text": PAPER_LOCAL_TEXT,
            "equations": [
                103,
                104,
                105,
                106,
                119,
                130,
                140,
                141,
                150,
                151,
                159,
                162,
                163,
                164,
            ],
        },
        "scope": {
            "included": [
                "precursor-cardinality ordering",
                "equal-cardinality second orientation and Eq. (104)",
                "right/left denominator clearing for Eqs. (105)/(106)",
                "one exact Eq. (119) and Eq. (130) fixture",
                "one exact S1/S2 Pauli rejection fixture for Eq. (163)",
                "stage-two MSR, GC, and noncommutative operator order",
            ],
            "excluded": [
                "TOBC and NTOBC reproductions",
                "continuous-parameter appendix elimination",
                "full transition-operator solution",
            ],
        },
        "precursor_size_convention": {
            "comparison": "cardinality of the two precursor sets",
            "strict_example": {
                "A_precursor": [0, 1],
                "A_prime_precursor": [0],
                "classification": "UNEQUAL_A_STRICTLY_LARGER",
            },
            "equal_example": {
                "A_precursor": [0],
                "A_prime_precursor": [1],
                "classification": "EQUAL_REQUIRES_BOTH_ORIENTATIONS",
            },
            "set_inclusion_is_not_used_as_the_order_key": True,
        },
        "equations_103_to_106": {
            "unequal": {
                "eq103": "A_n*A_prime_m = A_m*A_prime_n",
                "eq105": "A_n = A_m*A_prime_n*A_prime_m^-1",
                "right_cleared_word": list(eq103_right_clearing),
                "verified": eq103_right_clearing == ("A_m", "A_prime_n"),
            },
            "equal": {
                "first_orientation": "A_n*A_prime_m = A_m*A_prime_n",
                "second_orientation": "A_prime_m*A_n = A_prime_n*A_m",
                "eq106_alternative": (
                    "A_n = A_prime_m^-1*A_prime_n*A_m"
                ),
                "left_cleared_word": list(eq106_left_clearing),
                "eq104_rewrite_route": eq104_route,
                "eq104": (
                    "A_prime_m*A_m*A_prime_n = "
                    "A_prime_n*A_m*A_prime_m"
                ),
                "verified": convention_pass,
            },
            "noncommutative_order_preserved": True,
        },
        "representative_relations": {
            "eq119_two_pauli_directions": _matrix_certificate(relation_119),
            "eq130_commutator": _matrix_certificate(relation_130),
            "eq164_three_distinct_pauli_obstruction": _matrix_certificate(
                distinct_pauli
            ),
        },
        "s1_s2_pauli_fixture": {
            "dimension": 2,
            "role": "paper regression only; not v0.3 new representation search",
            "assignment": {
                "Q1": "2*sigma_x",
                "Q2": "3*sigma_y",
                "Q3": "5*sigma_x",
                "Q4": "7*sigma_y",
            },
            "S1": _matrix_record(s1),
            "S2": _matrix_record(s2),
            "A1_3": _matrix_record(a1_3),
            "A2_3": _matrix_record(a2_3),
            "determinants": pauli_invertibility,
            "all_required_operators_invertible": pauli_all_invertible,
            "eq163_commutator": _matrix_certificate(relation_163),
            "rejected_exactly": not _is_zero_matrix(relation_163),
        },
        "msr_gc_operator_order_fixture": {
            "assignment": {
                "Q1": _matrix_record(rational_q1),
                "Q2": _matrix_record(rational_q2),
            },
            "A1_2_ordered_as_eq140": _matrix_record(rational_a1_2),
            "A2_2_from_msr_eq141": _matrix_record(rational_a2_2),
            "G2_from_gc_eq142": _matrix_record(rational_g2),
            "cpobc_eq140_residual": _matrix_certificate(cpobc_residual),
            "msr_residual": _matrix_certificate(msr_residual),
            "gc_two_path_residual": _matrix_certificate(gc_residual),
            "incorrect_reordering_difference": _matrix_certificate(
                ordering_guard
            ),
            "ordered_product_is_detectably_noncommutative": (
                not _is_zero_matrix(ordering_guard)
            ),
        },
        "status": (
            "MINIMAL_EXACT_REGRESSION_PASS"
            if passed
            else "MINIMAL_EXACT_REGRESSION_FAIL"
        ),
        "paper_regression_status": (
            "PAPER_REGRESSION_PASS"
            if passed
            else "PAPER_REGRESSION_FAIL"
        ),
        "passed": passed,
        "claim_boundary": (
            "This is a small convention and fixture regression. It neither "
            "reproduces the full appendix nor strengthens the paper's claims."
        ),
    }


def paper_regression_benchmark() -> dict[str, Any]:
    """Return a deterministic, JSON-ready minimal CPOBC paper regression."""

    return copy.deepcopy(_paper_regression_cached())


def _vertices(mask: int, size: int) -> list[int]:
    return [vertex for vertex in range(size) if mask & (1 << vertex)]


def _mask_from_vertices(vertices: tuple[int, ...] | list[int]) -> int:
    result = 0
    for vertex in vertices:
        result |= 1 << vertex
    return result


def _mapped_mask(mask: int, permutation: tuple[int, ...]) -> int:
    result = 0
    for vertex, image in enumerate(permutation):
        if mask & (1 << vertex):
            result |= 1 << image
    return result


def _relation_code_for_order(
    relation: Relation,
    order: tuple[int, ...],
) -> int:
    size = len(relation)
    code = 0
    for new_lower, old_lower in enumerate(order):
        for new_upper, old_upper in enumerate(order):
            if relation[old_lower] & (1 << old_upper):
                code |= 1 << (new_lower * size + new_upper)
    return code


def _subset_for_order(mask: int, order: tuple[int, ...]) -> int:
    return sum(
        1 << new_vertex
        for new_vertex, old_vertex in enumerate(order)
        if mask & (1 << old_vertex)
    )


def _induced_relation(
    relation: Relation,
    selected_mask: int,
) -> tuple[Relation, int, int]:
    selected = _vertices(selected_mask, len(relation))
    old_to_new = {old: new for new, old in enumerate(selected)}
    rows = [0] * len(selected)
    for old_lower in selected:
        for old_upper in selected:
            if relation[old_lower] & (1 << old_upper):
                rows[old_to_new[old_lower]] |= 1 << old_to_new[old_upper]
    return tuple(rows), len(selected), selected_mask


def _local_mask(mask: int, selected_mask: int, size: int) -> int:
    selected = _vertices(selected_mask, size)
    return sum(
        1 << local
        for local, original in enumerate(selected)
        if mask & (1 << original)
    )


def _decorated_family_signature(
    relation: Relation,
    first_precursor: int,
    second_precursor: int,
) -> tuple[dict[str, Any], bool]:
    union = first_precursor | second_precursor
    core, core_size, _ = _induced_relation(relation, union)
    first_local = _local_mask(first_precursor, union, len(relation))
    second_local = _local_mask(second_precursor, union, len(relation))
    equal_size = first_precursor.bit_count() == second_precursor.bit_count()

    candidates: list[tuple[tuple[int, int, int], bool]] = []
    for order in itertools.permutations(range(core_size)):
        relation_code = _relation_code_for_order(core, order)
        first_code = _subset_for_order(first_local, order)
        second_code = _subset_for_order(second_local, order)
        candidates.append(((relation_code, first_code, second_code), False))
        if equal_size:
            candidates.append(
                ((relation_code, second_code, first_code), True)
            )
    signature_tuple, swapped = min(
        candidates,
        key=lambda item: (item[0], item[1]),
    )
    relation_code, first_code, second_code = signature_tuple
    signature = {
        "core_stage": core_size,
        "core_relation_code": relation_code,
        "core_relation_rows": list(
            relation_from_code(core_size, relation_code)
        ),
        "A_precursor_code": first_code,
        "A_prime_precursor_code": second_code,
        "A_precursor": _vertices(first_code, core_size),
        "A_prime_precursor": _vertices(second_code, core_size),
        "comparison": (
            "EQUAL_PRECURSOR_SIZE"
            if equal_size
            else "A_PRECURSOR_STRICTLY_LARGER"
        ),
    }
    return signature, swapped


def _oriented_pair_orbit(
    relation: Relation,
    first_precursor: int,
    second_precursor: int,
) -> tuple[tuple[int, int], tuple[tuple[int, int], ...]]:
    first_size = first_precursor.bit_count()
    second_size = second_precursor.bit_count()
    if first_size < second_size:
        first_precursor, second_precursor = (
            second_precursor,
            first_precursor,
        )
        first_size, second_size = second_size, first_size
    if first_size == second_size and first_precursor > second_precursor:
        first_precursor, second_precursor = (
            second_precursor,
            first_precursor,
        )

    images: set[tuple[int, int]] = set()
    for permutation in automorphisms(relation):
        first_image = _mapped_mask(first_precursor, permutation)
        second_image = _mapped_mask(second_precursor, permutation)
        if first_size == second_size and first_image > second_image:
            first_image, second_image = second_image, first_image
        images.add((first_image, second_image))
    orbit = tuple(sorted(images))
    return orbit[0], orbit


def _transition_occurrence(
    relation: Relation,
    precursor: int,
) -> dict[str, Any]:
    size = len(relation)
    all_vertices = (1 << size) - 1
    orbit = precursor_orbit(relation, precursor)
    orbit_representative = orbit[0]
    target = canonicalize(add_maximal(relation, precursor))
    source_id = causet_id(relation)
    target_id = causet_id(target)
    occurrence_payload = {
        "stage": size,
        "source": source_id,
        "target": target_id,
        "precursor_code": precursor,
    }
    orbit_payload = {
        "stage": size,
        "source": source_id,
        "target": causet_id(
            canonicalize(add_maximal(relation, orbit_representative))
        ),
        "precursor_orbit_representative": orbit_representative,
    }
    occurrence_hash = _stable_hash(occurrence_payload)
    orbit_hash = _stable_hash(orbit_payload)
    precursor_vertices = _vertices(precursor, size)
    spectator_vertices = _vertices(all_vertices ^ precursor, size)
    return {
        "id": f"cpobc-transition-{occurrence_hash[:20]}",
        "hash": occurrence_hash,
        "orbit_id": f"cpobc-transition-orbit-{orbit_hash[:20]}",
        "orbit_hash": orbit_hash,
        "operator_symbol": f"A_{size}_{occurrence_hash[:10]}",
        "stage": size,
        "source_id": source_id,
        "target_id": target_id,
        "precursor_code": precursor,
        "precursor": precursor_vertices,
        "spectator": spectator_vertices,
        "cardinalities": {
            "source": size,
            "precursor": len(precursor_vertices),
            "precursor_maximal_elements": len(
                maximal_elements_in_subset(relation, precursor)
            ),
            "spectator": len(spectator_vertices),
        },
        "automorphism_multiplicity": {
            "source_automorphism_order": len(automorphisms(relation)),
            "precursor_orbit_size": len(orbit),
            "precursor_stabilizer_order": (
                len(automorphisms(relation)) // len(orbit)
            ),
            "orbit_representative_precursor_code": orbit_representative,
        },
    }


def _source_partition_audit(relation: Relation) -> dict[str, Any]:
    seen: set[int] = set()
    orbit_sizes: list[int] = []
    for precursor in downsets(relation):
        orbit = precursor_orbit(relation, precursor)
        if orbit[0] in seen:
            continue
        seen.update(orbit)
        orbit_sizes.append(len(orbit))
    return {
        "source_id": causet_id(relation),
        "downset_transition_count": len(downsets(relation)),
        "transition_orbit_count": len(orbit_sizes),
        "orbit_multiplicity_sum": sum(orbit_sizes),
        "exact_partition": sum(orbit_sizes) == len(downsets(relation)),
    }


def _bell_pair_records(
    levels: tuple[tuple[Relation, ...], ...],
    max_n: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    transition_orbits: list[dict[str, Any]] = []
    pair_records: list[dict[str, Any]] = []
    for stage in range(1, max_n + 1):
        for relation in levels[stage]:
            seen_transitions: set[int] = set()
            for precursor in downsets(relation):
                transition_representative = precursor_orbit(
                    relation,
                    precursor,
                )[0]
                if transition_representative in seen_transitions:
                    continue
                seen_transitions.update(
                    precursor_orbit(relation, transition_representative)
                )
                transition_orbits.append(
                    _transition_occurrence(
                        relation,
                        transition_representative,
                    )
                )

            seen_pairs: set[tuple[int, int]] = set()
            for raw_first, raw_second in itertools.combinations(
                downsets(relation),
                2,
            ):
                pair_representative, pair_orbit = _oriented_pair_orbit(
                    relation,
                    raw_first,
                    raw_second,
                )
                if pair_representative in seen_pairs:
                    continue
                seen_pairs.update(pair_orbit)
                first, second = pair_representative
                family_signature, swap_for_family = (
                    _decorated_family_signature(relation, first, second)
                )
                identity_first, identity_second = first, second
                if swap_for_family:
                    first, second = second, first
                first_transition = _transition_occurrence(relation, first)
                second_transition = _transition_occurrence(relation, second)
                family_hash = _stable_hash(family_signature)
                family_id = f"cpobc-family-{family_hash[:20]}"
                pair_payload = {
                    "stage": stage,
                    "source": causet_id(relation),
                    "precursor_pair": sorted(
                        [identity_first, identity_second]
                    ),
                    "family_hash": family_hash,
                }
                pair_hash = _stable_hash(pair_payload)
                all_vertices = (1 << stage) - 1
                common_spectator = all_vertices ^ (first | second)
                pair_records.append(
                    {
                        "id": f"cpobc-bell-pair-{pair_hash[:20]}",
                        "hash": pair_hash,
                        "stage": stage,
                        "source_id": causet_id(relation),
                        "source_relation_rows": list(relation),
                        "transition_pair": {
                            "A": first_transition,
                            "A_prime": second_transition,
                        },
                        "family": {
                            "id": family_id,
                            "hash": family_hash,
                            "core_stage": family_signature["core_stage"],
                        },
                        "precursors": {
                            "A": _vertices(first, stage),
                            "A_prime": _vertices(second, stage),
                        },
                        "spectators": {
                            "A": _vertices(all_vertices ^ first, stage),
                            "A_prime": _vertices(
                                all_vertices ^ second,
                                stage,
                            ),
                            "common": _vertices(common_spectator, stage),
                        },
                        "cardinalities": {
                            "source": stage,
                            "A_precursor": first.bit_count(),
                            "A_prime_precursor": second.bit_count(),
                            "common_spectator": common_spectator.bit_count(),
                        },
                        "equal_vs_unequal": family_signature["comparison"],
                        "operator_order": (
                            "BOTH_ORIENTATIONS_AT_EQUAL_SIZE"
                            if first.bit_count() == second.bit_count()
                            else "A_WITH_LARGER_PRECURSOR_IS_LEFT_ORDER_KEY"
                        ),
                        "automorphism_multiplicities": {
                            "source_automorphism_order": len(
                                automorphisms(relation)
                            ),
                            "pair_orbit_size": len(pair_orbit),
                            "pair_stabilizer_order": (
                                len(automorphisms(relation))
                                // len(pair_orbit)
                            ),
                            "A_transition_orbit_size": len(
                                precursor_orbit(relation, first)
                            ),
                            "A_prime_transition_orbit_size": len(
                                precursor_orbit(relation, second)
                            ),
                        },
                        "family_root_signature": family_signature,
                        "family_role": (
                            "FAMILY_ROOT"
                            if common_spectator == 0
                            else "COMMON_SPECTATOR_EXTENSION"
                        ),
                        "definition_boundary": (
                            "The common-spectator-empty member is retained as "
                            "the n0 root of a Bell family; paper terminology "
                            "reserves a nonempty common spectator for a Bell "
                            "pair away from that root."
                        ),
                    }
                )
    transition_orbits.sort(
        key=lambda item: (
            item["stage"],
            item["source_id"],
            item["precursor_code"],
        )
    )
    pair_records.sort(
        key=lambda item: (
            item["stage"],
            item["source_id"],
            item["hash"],
        )
    )
    return transition_orbits, pair_records


def _family_records(
    pair_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pair_records:
        grouped[pair["family"]["id"]].append(pair)
    families: list[dict[str, Any]] = []
    for family_id in sorted(grouped):
        members = sorted(
            grouped[family_id],
            key=lambda item: (item["stage"], item["id"]),
        )
        signature = members[0]["family_root_signature"]
        stages = [member["stage"] for member in members]
        stage_counts = Counter(stages)
        cross_stage_routes = sum(
            1
            for first, second in itertools.combinations(members, 2)
            if first["stage"] != second["stage"]
        )
        families.append(
            {
                "id": family_id,
                "hash": members[0]["family"]["hash"],
                "core": signature,
                "equal_vs_unequal": signature["comparison"],
                "member_pair_ids": [member["id"] for member in members],
                "member_count": len(members),
                "stages": sorted(set(stages)),
                "stage_member_counts": {
                    str(stage): stage_counts[stage]
                    for stage in sorted(stage_counts)
                },
                "root_member_present": any(
                    member["family_role"] == "FAMILY_ROOT"
                    for member in members
                ),
                "cross_stage_relation_route_count": cross_stage_routes,
            }
        )
    return families


def _word_equation(
    equation_id: str,
    lhs: list[str],
    rhs: list[str],
) -> dict[str, Any]:
    return {
        "equation_id": equation_id,
        "lhs_word": lhs,
        "rhs_word": rhs,
        "residual_terms": [
            {"coefficient": 1, "word": lhs},
            {"coefficient": -1, "word": rhs},
        ],
        "display": f"{'*'.join(lhs)} - {'*'.join(rhs)} = 0",
    }


def _compiled_relation_record(
    high: dict[str, Any],
    low: dict[str, Any],
) -> dict[str, Any]:
    comparison = high["equal_vs_unequal"]
    high_a = high["transition_pair"]["A"]
    high_ap = high["transition_pair"]["A_prime"]
    low_a = low["transition_pair"]["A"]
    low_ap = low["transition_pair"]["A_prime"]
    aliases = {
        "A_n": high_a["id"],
        "A_prime_n": high_ap["id"],
        "A_m": low_a["id"],
        "A_prime_m": low_ap["id"],
    }
    cleared = [
        _word_equation(
            "eq103",
            ["A_n", "A_prime_m"],
            ["A_m", "A_prime_n"],
        )
    ]
    solved_forms = [
        {
            "equation_id": "eq105" if "STRICTLY" in comparison else "eq106a",
            "lhs": "A_n",
            "rhs_word": ["A_m", "A_prime_n", "A_prime_m^-1"],
            "display": "A_n = A_m*A_prime_n*A_prime_m^-1",
        }
    ]
    paper_equations = [103, 105]
    if comparison == "EQUAL_PRECURSOR_SIZE":
        cleared.extend(
            [
                _word_equation(
                    "equal_second_orientation",
                    ["A_prime_m", "A_n"],
                    ["A_prime_n", "A_m"],
                ),
                _word_equation(
                    "eq104",
                    ["A_prime_m", "A_m", "A_prime_n"],
                    ["A_prime_n", "A_m", "A_prime_m"],
                ),
            ]
        )
        solved_forms[0]["equation_id"] = "eq106a"
        solved_forms.append(
            {
                "equation_id": "eq106b",
                "lhs": "A_n",
                "rhs_word": [
                    "A_prime_m^-1",
                    "A_prime_n",
                    "A_m",
                ],
                "display": (
                    "A_n = A_prime_m^-1*A_prime_n*A_m"
                ),
            }
        )
        paper_equations = [103, 104, 106]

    relation_payload = {
        "family": high["family"]["id"],
        "high_pair": high["id"],
        "low_pair": low["id"],
        "comparison": comparison,
        "aliases": aliases,
        "cleared": cleared,
    }
    relation_hash = _stable_hash(relation_payload)
    high_relation = tuple(high["source_relation_rows"])
    low_relation = tuple(low["source_relation_rows"])
    record = {
        "id": f"cpobc-relation-{relation_hash[:20]}",
        "hash": relation_hash,
        "stages": {"n": high["stage"], "m": low["stage"]},
        "transition_pair": {
            "stage_n_pair_id": high["id"],
            "stage_m_pair_id": low["id"],
            "operator_aliases": aliases,
            "transition_hashes": {
                "A_n": high_a["hash"],
                "A_prime_n": high_ap["hash"],
                "A_m": low_a["hash"],
                "A_prime_m": low_ap["hash"],
            },
        },
        "family": {
            "id": high["family"]["id"],
            "hash": high["family"]["hash"],
            "core_stage": high["family"]["core_stage"],
        },
        "precursors": {
            "stage_n": high["precursors"],
            "stage_m": low["precursors"],
        },
        "spectators": {
            "stage_n": high["spectators"],
            "stage_m": low["spectators"],
        },
        "cardinalities": {
            "stage_n": high["cardinalities"],
            "stage_m": low["cardinalities"],
        },
        "equal_vs_unequal": comparison,
        "operator_order": {
            "key": "precursor cardinality",
            "A_is_larger_side": comparison
            == "A_PRECURSOR_STRICTLY_LARGER",
            "both_orientations_required": comparison
            == "EQUAL_PRECURSOR_SIZE",
            "commutative_reordering_permitted": False,
            "ordered_words": [
                equation["lhs_word"] for equation in cleared
            ]
            + [equation["rhs_word"] for equation in cleared],
        },
        "invertibility": {
            "paper_global_assumption": True,
            "transition_operator_ids": list(aliases.values()),
            "required_to_write_solved_forms": [aliases["A_prime_m"]],
            "required_for_denominator_cleared_forms": [],
        },
        "GC": {
            "used_to_generate_this_relation": False,
            "canonical_unlabeled_endpoints_recorded": True,
            "status": (
                "COMBINATORIAL_ENDPOINT_CANONICALIZATION_ONLY; "
                "NO_OPERATOR_PATH_IDENTITY_COMPILED"
            ),
        },
        "MSR": {
            "used_to_generate_this_relation": False,
            "stage_n_source_partition": _source_partition_audit(
                high_relation
            ),
            "stage_m_source_partition": _source_partition_audit(low_relation),
            "status": (
                "OUTGOING_DOWNSET_PARTITION_EXACT; "
                "NO_OPERATOR_SUM_ELIMINATION_COMPILED"
            ),
        },
        "automorphism_multiplicities": {
            "stage_n": high["automorphism_multiplicities"],
            "stage_m": low["automorphism_multiplicities"],
        },
        "generated_equation": {
            "operator_aliases": aliases,
            "solved_forms": solved_forms,
        },
        "denominator_cleared_form": {
            "noncommutative_polynomial_equations": cleared,
            "exact_integer_coefficients": True,
        },
        "paper_correspondence": {
            "paper": PAPER_ID,
            "equations": paper_equations,
            "classification": "FINITE_INSTANCE_OF_PAPER_CPOBC_RELATION",
        },
        "dependency": {
            "pair_ids": [high["id"], low["id"]],
            "family_id": high["family"]["id"],
            "axioms": [
                "finite causal-set maximal growth",
                "Bell-family common-spectator definition",
                "CPOBC precursor-cardinality ordering",
                "invertibility only for solved forms",
            ],
            "derivation_routes": [
                "transition graph -> decorated Bell family -> CPOBC axiom"
            ],
            "independent_derivation_route_count": 1,
            "exact_ideal_membership": "NOT_RUN",
        },
        "novelty": {
            "classification": (
                "FINITE_COMBINATORIAL_INSTANTIATION_NOT_NOVEL_RELATION"
            ),
            "independent_relation_claimed": False,
            "reason": (
                "No exact ideal-membership comparison and no second "
                "independent derivation route were supplied."
            ),
        },
    }
    return record


def _relation_records(
    pair_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pair_records:
        grouped[pair["family"]["id"]].append(pair)
    relations: list[dict[str, Any]] = []
    for family_id in sorted(grouped):
        members = sorted(
            grouped[family_id],
            key=lambda item: (item["stage"], item["id"]),
        )
        for first, second in itertools.combinations(members, 2):
            if first["stage"] == second["stage"]:
                continue
            high, low = (
                (first, second)
                if first["stage"] > second["stage"]
                else (second, first)
            )
            relations.append(_compiled_relation_record(high, low))
    relations.sort(
        key=lambda item: (
            item["stages"]["n"],
            item["stages"]["m"],
            item["family"]["id"],
            item["id"],
        )
    )
    return relations


@lru_cache(maxsize=COMPILER_MAX_STAGE + 1)
def _compile_cpobc_relations_cached(max_n: int) -> dict[str, Any]:
    levels = enumerate_unlabeled_posets(max_n + 1)
    transitions, pairs = _bell_pair_records(levels, max_n)
    families = _family_records(pairs)
    relations = _relation_records(pairs)
    stage_transition_counts = Counter(
        transition["stage"] for transition in transitions
    )
    stage_pair_counts = Counter(pair["stage"] for pair in pairs)
    all_msr_partitions_exact = all(
        relation["MSR"]["stage_n_source_partition"]["exact_partition"]
        and relation["MSR"]["stage_m_source_partition"]["exact_partition"]
        for relation in relations
    )
    digest_payload = {
        "max_n": max_n,
        "transition_hashes": [item["hash"] for item in transitions],
        "pair_hashes": [item["hash"] for item in pairs],
        "family_hashes": [item["hash"] for item in families],
        "relation_hashes": [item["hash"] for item in relations],
    }
    return {
        "schema_version": "final-theory-cpobc-compiler-v0.3.0",
        "suite": "CPOBC v0.3 finite relation compiler",
        "source": {
            "paper": PAPER_ID,
            "local_extracted_text": PAPER_LOCAL_TEXT,
            "compiled_equations": [103, 104, 105, 106],
        },
        "manifest": {
            "source_stage_min": 1,
            "source_stage_max": max_n,
            "child_stage_max": max_n + 1,
            "resource_limits": {
                "hard_max_source_stage": COMPILER_MAX_STAGE,
                "canonicalization": (
                    "exhaustive finite vertex permutations only"
                ),
                "symbolic_operator_elimination": "not run",
            },
            "causal_sets": (
                "all canonical unlabeled finite posets in the declared domain"
            ),
            "transitions": (
                "all down-set precursor transitions, quotiented by each "
                "source automorphism group"
            ),
            "bell_pair_instances": (
                "all distinct precursor pairs, quotiented by source "
                "automorphisms; the common-spectator-empty family root is kept"
            ),
            "family_key": (
                "SHA-256 of the canonically colored core relation obtained "
                "after deleting all common spectators"
            ),
            "arithmetic": "exact integers and finite permutations",
            "randomness": "none",
        },
        "transition_graph": {
            "level_node_counts": {
                str(stage): len(levels[stage])
                for stage in range(1, max_n + 2)
            },
            "stage_transition_orbit_counts": {
                str(stage): stage_transition_counts[stage]
                for stage in range(1, max_n + 1)
            },
            "transition_orbits": transitions,
        },
        "bell_pairs": pairs,
        "bell_families": families,
        "relations": relations,
        "counts": {
            "transition_orbits": len(transitions),
            "bell_pair_orbits": len(pairs),
            "bell_families": len(families),
            "compiled_cross_stage_relations": len(relations),
            "equal_size_relations": sum(
                item["equal_vs_unequal"] == "EQUAL_PRECURSOR_SIZE"
                for item in relations
            ),
            "unequal_size_relations": sum(
                item["equal_vs_unequal"]
                == "A_PRECURSOR_STRICTLY_LARGER"
                for item in relations
            ),
            "stage_bell_pair_orbits": {
                str(stage): stage_pair_counts[stage]
                for stage in range(1, max_n + 1)
            },
        },
        "compiler_digest_sha256": _stable_hash(digest_payload),
        "structural_checks": {
            "all_msr_orbit_partitions_exact": all_msr_partitions_exact,
            "all_relation_hashes_unique": len(
                {item["hash"] for item in relations}
            )
            == len(relations),
            "all_pair_hashes_unique": len({item["hash"] for item in pairs})
            == len(pairs),
            "json_ready": True,
        },
        "completeness": {
            "finite_combinatorics": (
                "EXACT_COMPLETE_WITHIN_DECLARED_UNLABELED_DOMAIN"
            ),
            "paper_operator_equations": (
                "INCOMPLETE_RELATIVE_TO_PAPER: only Eqs. (103)--(106) are "
                "instantiated. GC path equations, MSR operator eliminations, "
                "Eqs. (107)--(163), and appendix-wide dependencies are not "
                "compiled."
            ),
            "labeled_history_boundary": (
                "Unlabeled source representatives are used with exact "
                "automorphism orbit multiplicities; individual natural "
                "labelings are not enumerated as distinct physical states."
            ),
        },
        "novelty": {
            "independent_relations_claimed": 0,
            "exact_ideal_membership_runs": 0,
            "two_route_derivations": 0,
            "status": "NO_NOVEL_INDEPENDENT_RELATION_CLAIM",
        },
        "status": "EXACT_FINITE_PARTIAL_CPOBC_COMPILER",
        "cpobc_relation_status": "CPOBC_RELATION_COMPILER_PARTIAL",
        "completeness_scope": (
            f"all unlabeled transition and precursor-pair orbits through source n={max_n}; "
            "operator compilation limited to paper Eqs. 103-106"
        ),
        "resource_limits": [
            "compiler source cardinality is capped at n<=4",
            "noncommutative ideal membership and a second derivation route were not run",
            "paper Eqs. 107-163 and appendix dependencies are not compiled",
        ],
        "unresolved_items": [
            "compile GC and operator-valued MSR eliminations",
            "compile the remaining published CPOBC relations",
            "test dependency in a noncommutative ideal with an independent route",
        ],
        "passed": (
            all_msr_partitions_exact
            and len({item["hash"] for item in relations}) == len(relations)
            and len({item["hash"] for item in pairs}) == len(pairs)
        ),
    }


def compile_cpobc_relations(max_n: int = 4) -> dict[str, Any]:
    """Compile exact finite Bell-family instances of Eqs. (103)--(106).

    ``max_n`` is the largest source stage.  The v0.3 resource envelope is
    intentionally fixed at four; larger requests must use a separately audited
    compiler rather than silently broadening this finite certificate.
    """

    if isinstance(max_n, bool) or not isinstance(max_n, int):
        raise TypeError("max_n must be an integer")
    if not 1 <= max_n <= COMPILER_MAX_STAGE:
        raise ValueError(
            f"max_n must satisfy 1 <= max_n <= {COMPILER_MAX_STAGE}"
        )
    return copy.deepcopy(_compile_cpobc_relations_cached(max_n))


def _matrix_unit(dimension: int, row: int, column: int) -> sp.Matrix:
    matrix = sp.zeros(dimension)
    matrix[row, column] = 1
    return matrix


def _cyclic_shift(dimension: int) -> sp.Matrix:
    matrix = sp.zeros(dimension)
    for column in range(dimension):
        matrix[(column + 1) % dimension, column] = 1
    return matrix


def _block_diagonal_2_plus_1(
    block: sp.MatrixBase,
    scalar: sp.Expr | int,
) -> sp.Matrix:
    return sp.diag(sp.Matrix(block), sp.Matrix([[scalar]]))


def _candidate_payload(
    ansatz_id: str,
    field: str,
    parameters: dict[str, Any],
    generators: tuple[sp.Matrix, ...],
) -> dict[str, Any]:
    matrices = [_matrix_record(matrix) for matrix in generators]
    payload = {
        "ansatz_id": ansatz_id,
        "field": field,
        "parameters": parameters,
        "matrices": matrices,
    }
    candidate_hash = _stable_hash(payload)
    return {
        "id": f"cpobc-candidate-{candidate_hash[:20]}",
        "hash": candidate_hash,
        "ansatz_id": ansatz_id,
        "field": field,
        "parameters": parameters,
        "generators": generators,
    }


def _representation_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scalar_grid = ((2, 3, 5, 7), (3, 5, 7, 11))
    candidates: list[dict[str, Any]] = []

    # Commuting pipeline controls are reported separately from the
    # noncommutative search.
    for scalars in scalar_grid:
        diagonals = tuple(
            sp.diag(
                scalar,
                scalar + offset + 1,
                scalar + 2 * offset + 2,
            )
            for offset, scalar in enumerate(scalars)
        )
        candidates.append(
            _candidate_payload(
                "commuting_diagonal_control_d3",
                "Q",
                {"scalars": list(scalars)},
                diagonals,
            )
        )

    identity_3 = sp.eye(3)
    rational_patterns = (
        (
            _matrix_unit(3, 0, 1),
            _matrix_unit(3, 1, 2),
            _matrix_unit(3, 2, 0),
            _matrix_unit(3, 0, 2),
        ),
        (
            _matrix_unit(3, 1, 0),
            _matrix_unit(3, 2, 1),
            _matrix_unit(3, 0, 2),
            _matrix_unit(3, 2, 0),
        ),
    )
    for pattern_index, nilpotents in enumerate(rational_patterns):
        scalars = scalar_grid[pattern_index]
        generators = tuple(
            scalar * identity_3 + nilpotent
            for scalar, nilpotent in zip(scalars, nilpotents, strict=True)
        )
        candidates.append(
            _candidate_payload(
                "rational_affine_matrix_units_d3",
                "Q",
                {
                    "pattern": pattern_index,
                    "scalars": list(scalars),
                },
                generators,
            )
        )

    sigma_x, sigma_y, _sigma_z = _pauli_matrices()
    for scalars in scalar_grid:
        generators = tuple(
            scalar
            * _block_diagonal_2_plus_1(
                sigma_x if index % 2 == 0 else sigma_y,
                1,
            )
            for index, scalar in enumerate(scalars)
        )
        candidates.append(
            _candidate_payload(
                "reducible_pauli_block_lift_d3",
                "Q(i)",
                {"scalars": list(scalars), "pattern": ["X", "Y", "X", "Y"]},
                generators,
            )
        )

    shift_3 = _cyclic_shift(3)
    omega = -sp.Rational(1, 2) + sp.sqrt(3) * sp.I / 2
    clock_3 = sp.diag(1, omega, omega**2)
    for scalars in scalar_grid:
        generators = tuple(
            scalar * (shift_3 if index % 2 == 0 else clock_3)
            for index, scalar in enumerate(scalars)
        )
        candidates.append(
            _candidate_payload(
                "heisenberg_weyl_d3",
                "Q(sqrt(-3))",
                {
                    "scalars": list(scalars),
                    "pattern": ["shift", "clock", "shift", "clock"],
                },
                generators,
            )
        )

    sqrt_two_patterns = (
        _matrix_unit(3, 0, 1) + sp.sqrt(2) * _matrix_unit(3, 1, 2),
        _matrix_unit(3, 1, 0) + sp.sqrt(2) * _matrix_unit(3, 2, 1),
        _matrix_unit(3, 2, 0) + sp.sqrt(2) * _matrix_unit(3, 0, 2),
        _matrix_unit(3, 0, 2) + sp.sqrt(2) * _matrix_unit(3, 2, 1),
    )
    for scalars in scalar_grid:
        generators = tuple(
            scalar * identity_3 + pattern
            for scalar, pattern in zip(
                scalars,
                sqrt_two_patterns,
                strict=True,
            )
        )
        candidates.append(
            _candidate_payload(
                "quadratic_field_affine_d3",
                "Q(sqrt(2))",
                {"scalars": list(scalars)},
                generators,
            )
        )

    shift_4 = _cyclic_shift(4)
    clock_4 = sp.diag(1, sp.I, -1, -sp.I)
    for scalars in scalar_grid:
        generators = tuple(
            scalar * (shift_4 if index % 2 == 0 else clock_4)
            for index, scalar in enumerate(scalars)
        )
        candidates.append(
            _candidate_payload(
                "heisenberg_weyl_d4",
                "Q(i)",
                {
                    "scalars": list(scalars),
                    "pattern": ["shift", "clock", "shift", "clock"],
                },
                generators,
            )
        )

    companion = sp.Matrix([[0, 0, 1], [1, 0, -1], [0, 1, 1]])
    reverse_companion = companion.T
    for scalars in scalar_grid:
        generators = (
            scalars[0] * identity_3 + companion,
            scalars[1] * identity_3 + reverse_companion,
            scalars[2] * identity_3 + companion**2,
            scalars[3] * identity_3 + reverse_companion**2,
        )
        candidates.append(
            _candidate_payload(
                "rational_companion_words_d3",
                "Q",
                {"scalars": list(scalars)},
                generators,
            )
        )

    manifest = {
        "scalar_grid": [list(item) for item in scalar_grid],
        "ansatz_classes": {
            "commuting_diagonal_control_d3": {
                "dimension": 3,
                "field": "Q",
                "role": "pipeline control, excluded from noncommutative hits",
            },
            "rational_affine_matrix_units_d3": {
                "dimension": 3,
                "field": "Q",
                "patterns": 2,
            },
            "reducible_pauli_block_lift_d3": {
                "dimension": 3,
                "field": "Q(i)",
                "patterns": 1,
            },
            "heisenberg_weyl_d3": {
                "dimension": 3,
                "field": "Q(sqrt(-3))",
                "patterns": 1,
            },
            "quadratic_field_affine_d3": {
                "dimension": 3,
                "field": "Q(sqrt(2))",
                "patterns": 1,
            },
            "heisenberg_weyl_d4": {
                "dimension": 4,
                "field": "Q(i)",
                "patterns": 1,
            },
            "rational_companion_words_d3": {
                "dimension": 3,
                "field": "Q",
                "patterns": 1,
            },
        },
        "candidate_count": len(candidates),
        "exhaustive_within_listed_grid": True,
    }
    return candidates, manifest


def _centralizer_dimension(generators: tuple[sp.Matrix, ...]) -> int:
    dimension = generators[0].rows
    columns: list[sp.Matrix] = []
    for row in range(dimension):
        for column in range(dimension):
            basis = _matrix_unit(dimension, row, column)
            entries: list[sp.Expr] = []
            for generator in generators:
                entries.extend(list(basis * generator - generator * basis))
            columns.append(sp.Matrix(entries))
    coefficient_matrix = sp.Matrix.hstack(*columns)
    return dimension * dimension - int(coefficient_matrix.rank())


def _append_if_independent(
    basis: list[sp.Matrix],
    candidate: sp.MatrixBase,
) -> bool:
    simplified = sp.Matrix(candidate).applyfunc(sp.simplify)
    vectors = [sp.Matrix(list(item)) for item in basis]
    old_rank = len(basis)
    new_rank = int(sp.Matrix.hstack(*vectors, sp.Matrix(list(simplified))).rank())
    if new_rank > old_rank:
        basis.append(simplified)
        return True
    return False


def _generated_algebra_dimension(
    generators: tuple[sp.Matrix, ...],
) -> int:
    dimension = generators[0].rows
    basis = [sp.eye(dimension)]
    cursor = 0
    while cursor < len(basis) and len(basis) < dimension * dimension:
        current = basis[cursor]
        cursor += 1
        for generator in generators:
            _append_if_independent(basis, current * generator)
            if len(basis) == dimension * dimension:
                break
            _append_if_independent(basis, generator * current)
            if len(basis) == dimension * dimension:
                break
    return len(basis)


def _coordinate_invariant_subspace(
    generators: tuple[sp.Matrix, ...],
) -> list[int] | None:
    dimension = generators[0].rows
    for mask in range(1, (1 << dimension) - 1):
        selected = _vertices(mask, dimension)
        outside = [
            index for index in range(dimension) if index not in selected
        ]
        if all(
            sp.simplify(generator[row, column]) == 0
            for generator in generators
            for column in selected
            for row in outside
        ):
            return selected
    return None


def _jordan_stratum(matrix: sp.MatrixBase) -> dict[str, Any]:
    spectral_parameter = sp.Symbol("lambda")
    characteristic_expression = sp.expand(
        (
            spectral_parameter * sp.eye(matrix.rows) - matrix
        ).det(method="berkowitz")
    )
    polynomial = sp.Poly(
        characteristic_expression,
        spectral_parameter,
        domain=sp.EX,
    )
    repeated_factor = sp.gcd(polynomial, polynomial.diff())
    try:
        diagonalizable: bool | None = bool(matrix.is_diagonalizable())
    except (NotImplementedError, ValueError):
        diagonalizable = None
    if repeated_factor.degree() == 0:
        stratum = "SIMPLE_SPECTRUM"
    elif diagonalizable is True:
        stratum = "REPEATED_SEMISIMPLE"
    elif diagonalizable is False:
        stratum = "NONTRIVIAL_JORDAN"
    else:
        stratum = "UNRESOLVED_EXACT_JORDAN_STRATUM"
    return {
        "trace": _exact_string(sp.trace(matrix)),
        "determinant": _exact_string(matrix.det()),
        "characteristic_polynomial": _exact_string(polynomial.as_expr()),
        "repeated_factor_degree": int(repeated_factor.degree()),
        "diagonalizable_over_algebraic_closure": diagonalizable,
        "stratum": stratum,
    }


def _structural_analysis(
    generators: tuple[sp.Matrix, ...],
) -> dict[str, Any]:
    dimension = generators[0].rows
    commutators = []
    for left, right in itertools.combinations(range(4), 2):
        residual = _commutator(generators[left], generators[right])
        commutators.append(
            {
                "pair": [left + 1, right + 1],
                "zero": _is_zero_matrix(residual),
                "rank": int(residual.rank()),
                "trace": _exact_string(sp.trace(residual)),
            }
        )
    centralizer_dimension = _centralizer_dimension(generators)
    algebra_dimension = _generated_algebra_dimension(generators)
    invariant_subspace = _coordinate_invariant_subspace(generators)
    if invariant_subspace is not None:
        reducibility = "EXACT_REDUCIBLE_COORDINATE_SUBSPACE"
    elif algebra_dimension == dimension * dimension:
        reducibility = "EXACT_FULL_MATRIX_ALGEBRA_IRREDUCIBLE"
    else:
        reducibility = "INCONCLUSIVE_REDUCIBILITY"
    return {
        "dimension": dimension,
        "pairwise_commutators": commutators,
        "noncommuting": any(not item["zero"] for item in commutators),
        "joint_centralizer": {
            "dimension": centralizer_dimension,
            "scalar_only": centralizer_dimension == 1,
            "claim_boundary": (
                "A scalar joint centralizer is necessary but not by itself "
                "used as an irreducibility proof."
            ),
        },
        "generated_algebra_span": {
            "dimension": algebra_dimension,
            "ambient_dimension": dimension * dimension,
            "full_matrix_algebra": algebra_dimension
            == dimension * dimension,
        },
        "reducibility": {
            "status": reducibility,
            "coordinate_invariant_subspace": invariant_subspace,
        },
        "jordan_strata": [
            {"generator": index + 1, **_jordan_stratum(generator)}
            for index, generator in enumerate(generators)
        ],
        "generator_determinants": {
            f"Q{index + 1}": _exact_string(generator.det())
            for index, generator in enumerate(generators)
        },
        "generator_traces": {
            f"Q{index + 1}": _exact_string(sp.trace(generator))
            for index, generator in enumerate(generators)
        },
    }


def _relation_certificate(
    relation_id: str,
    source_equation: int,
    residual: sp.MatrixBase,
    route: str,
) -> dict[str, Any]:
    return {
        "relation_id": relation_id,
        "source_equation": source_equation,
        "route": route,
        "residual": _matrix_certificate(residual),
    }


def _evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    generators: tuple[sp.Matrix, ...] = candidate["generators"]
    dimension = generators[0].rows
    structural = _structural_analysis(generators)
    generator_matrices = [_matrix_record(item) for item in generators]
    exact_invertibility: dict[str, dict[str, Any]] = {}
    for index, generator in enumerate(generators):
        determinant = sp.simplify(generator.det())
        exact_invertibility[f"Q{index + 1}"] = {
            "determinant": _exact_string(determinant),
            "invertible": determinant != 0,
        }

    relation_certificates: list[dict[str, Any]] = []
    all_q_invertible = all(
        item["invertible"] for item in exact_invertibility.values()
    )
    if all_q_invertible:
        for indices in itertools.combinations(range(4), 3):
            k = min(indices)
            n, m = [index for index in indices if index != k]
            residual = (
                generators[n] * generators[k].inv() * generators[m]
                - generators[m] * generators[k].inv() * generators[n]
            )
            relation_certificates.append(
                _relation_certificate(
                    f"eq119_Q{n + 1}_Q{k + 1}_Q{m + 1}",
                    119,
                    residual,
                    "gregarious three-generator necessary relation",
                )
            )
        relation_certificates.append(
            _relation_certificate(
                "eq130",
                130,
                _commutator(
                    generators[0] * generators[1].inv(),
                    generators[0].inv() * generators[1],
                ),
                "Q1/Q2 commutator necessary relation",
            )
        )

    identity = sp.eye(dimension)
    construction_status = "NOT_ATTEMPTED_GENERATOR_SINGULAR"
    if all_q_invertible:
        a1_2 = (identity - generators[0]) * generators[1] * generators[0].inv()
        a2_2 = identity - 2 * a1_2 - generators[1]
        a1_3 = a1_2 * generators[2] * generators[1].inv()
        a2_3 = a2_2 * generators[2] * generators[1].inv()
        constructed = {
            "I_minus_Q1": identity - generators[0],
            "A1_2": a1_2,
            "A2_2": a2_2,
            "A1_3": a1_3,
            "A2_3": a2_3,
        }
        for name, matrix in constructed.items():
            determinant = sp.simplify(matrix.det())
            exact_invertibility[name] = {
                "determinant": _exact_string(determinant),
                "invertible": determinant != 0,
            }
        prerequisites = ("I_minus_Q1", "A1_2", "A2_2")
        if all(exact_invertibility[name]["invertible"] for name in prerequisites):
            s1 = (
                (identity - generators[0])
                * a2_2
                * generators[2]
                * a2_2.inv()
                * generators[0].inv()
                * a2_3
            )
            s2 = (
                a2_2
                * a1_2
                * generators[2]
                * a1_2.inv()
                * generators[1].inv()
                * a1_2
                * generators[2]
                * generators[1].inv()
            )
            for name, matrix in (("S1", s1), ("S2", s2)):
                determinant = sp.simplify(matrix.det())
                exact_invertibility[name] = {
                    "determinant": _exact_string(determinant),
                    "invertible": determinant != 0,
                }
            if exact_invertibility["S2"]["invertible"]:
                relation_certificates.append(
                    _relation_certificate(
                        "eq163",
                        163,
                        _commutator(
                            s2.inv() * s1,
                            generators[3],
                        ),
                        "S1/S2 two-atomisation necessary relation",
                    )
                )
                construction_status = "S1_S2_EQ163_EVALUATED"
            else:
                construction_status = "S2_SINGULAR"
        else:
            construction_status = "REQUIRED_INTERMEDIATE_SINGULAR"

    required_relation_ids = {
        "eq119_Q2_Q1_Q3",
        "eq119_Q2_Q1_Q4",
        "eq119_Q3_Q1_Q4",
        "eq119_Q3_Q2_Q4",
        "eq130",
        "eq163",
    }
    relation_by_id = {
        item["relation_id"]: item for item in relation_certificates
    }
    tested_necessary_relations_pass = (
        required_relation_ids <= relation_by_id.keys()
        and all(
            relation_by_id[relation_id]["residual"]["zero"]
            for relation_id in required_relation_ids
        )
    )
    is_control = candidate["ansatz_id"].endswith("_control_d3")
    noncommuting_admissible = (
        structural["noncommuting"]
        and all_q_invertible
        and tested_necessary_relations_pass
    )
    first_failure = next(
        (
            {
                "kind": "RELATION_RESIDUAL",
                "relation_id": item["relation_id"],
                "certificate_hash": item["residual"]["sha256"],
            }
            for item in relation_certificates
            if not item["residual"]["zero"]
        ),
        None,
    )
    if first_failure is None and construction_status != "S1_S2_EQ163_EVALUATED":
        first_failure = {
            "kind": "INVERTIBILITY_OR_CONSTRUCTION",
            "status": construction_status,
        }
    return {
        "id": candidate["id"],
        "hash": candidate["hash"],
        "ansatz_id": candidate["ansatz_id"],
        "role": "COMMUTING_CONTROL" if is_control else "NEW_D_GE_3_SEARCH",
        "dimension": dimension,
        "field": candidate["field"],
        "parameters": candidate["parameters"],
        "generators": generator_matrices,
        "exact_invertibility": exact_invertibility,
        "structural_analysis": structural,
        "relation_certificates": relation_certificates,
        "construction_status": construction_status,
        "tested_necessary_relations_pass": tested_necessary_relations_pass,
        "noncommuting_necessary_relation_survivor": noncommuting_admissible,
        "first_failure": first_failure,
        "full_compiled_relation_assignment_checked": False,
        "candidate_status": (
            "COMMUTING_PIPELINE_CONTROL"
            if is_control
            else (
                "NECESSARY_RELATION_SURVIVOR_INCONCLUSIVE"
                if noncommuting_admissible
                else "REJECTED_WITHIN_EXACT_ANSATZ_POINT"
            )
        ),
    }


@lru_cache(maxsize=1)
def _representation_search_cached() -> dict[str, Any]:
    candidates, ansatz_manifest = _representation_candidates()
    evaluated = [_evaluate_candidate(candidate) for candidate in candidates]
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in evaluated:
        grouped[candidate["ansatz_id"]].append(candidate)

    class_summaries: list[dict[str, Any]] = []
    for ansatz_id in sorted(grouped):
        records = grouped[ansatz_id]
        is_control = records[0]["role"] == "COMMUTING_CONTROL"
        survivors = [
            item
            for item in records
            if item["noncommuting_necessary_relation_survivor"]
        ]
        if is_control:
            result = (
                "CONTROL_PASS"
                if all(
                    item["tested_necessary_relations_pass"]
                    for item in records
                )
                else "CONTROL_FAIL"
            )
        elif survivors:
            result = "INCONCLUSIVE"
        else:
            result = "NO_CANDIDATE_IN_DECLARED_EXACT_GRID"
        class_summaries.append(
            {
                "ansatz_id": ansatz_id,
                "role": records[0]["role"],
                "dimension": records[0]["dimension"],
                "field": records[0]["field"],
                "candidate_count": len(records),
                "noncommuting_candidate_count": sum(
                    item["structural_analysis"]["noncommuting"]
                    for item in records
                ),
                "necessary_relation_survivor_count": len(survivors),
                "candidate_ids": [item["id"] for item in records],
                "exhaustive_within_manifest": True,
                "result": result,
                "claim_boundary": (
                    "This result quantifies only the finite matrices and "
                    "parameter values in the manifest."
                ),
            }
        )

    noncommuting_survivors = [
        item
        for item in evaluated
        if item["noncommuting_necessary_relation_survivor"]
    ]
    controls = [
        item for item in evaluated if item["role"] == "COMMUTING_CONTROL"
    ]
    controls_pass = bool(controls) and all(
        item["tested_necessary_relations_pass"] for item in controls
    )
    digest_payload = {
        "manifest": ansatz_manifest,
        "candidate_hashes": [item["hash"] for item in evaluated],
        "relation_hashes": [
            certificate["residual"]["sha256"]
            for item in evaluated
            for certificate in item["relation_certificates"]
        ],
    }
    return {
        "schema_version": "final-theory-cpobc-search-v0.3.0",
        "suite": "CPOBC v0.3 structured exact representation search",
        "source": {
            "paper": PAPER_ID,
            "necessary_relations": [119, 130, 163],
            "transition_constructions": [140, 141, 150, 151, 159, 162],
        },
        "manifest": {
            **ansatz_manifest,
            "new_work_dimensions": [3, 4],
            "new_work_minimum_dimension": 3,
            "exact_fields": [
                "Q",
                "Q(i)",
                "Q(sqrt(2))",
                "Q(sqrt(-3))",
            ],
            "comparison_with_v0_2": (
                "Adds field-structured Weyl, quadratic-field, block-lift, "
                "matrix-unit, and companion-word classes plus exact "
                "centralizer, trace, determinant, reducibility, generated-"
                "algebra, and Jordan-stratum diagnostics."
            ),
            "groebner_basis": (
                "NOT_RUN: no giant polynomial-system task is needed for this "
                "bounded pointwise exact audit"
            ),
            "randomness": "none",
            "candidate_generation": "deterministic finite grid",
            "resource_limits": {
                "maximum_dimension": 4,
                "exact_candidate_points": ansatz_manifest["candidate_count"],
                "continuous_parameter_elimination": "not run",
                "full_compiler_assignment_search": "not run",
                "large_groebner_basis": "prohibited for this bounded audit",
            },
            "requested_ansatz_coverage": {
                "dense_symbolic": "NOT_RUN_UNBOUNDED_POLYNOMIAL_SYSTEM",
                "block_diagonal": "REPRESENTATIVE_POINTS_TESTED",
                "block_upper_triangular": (
                    "REPRESENTATIVE_AFFINE_MATRIX_UNIT_POINTS_TESTED"
                ),
                "jordan_companion": (
                    "REPRESENTATIVE_COMPANION_AND_AFFINE_POINTS_TESTED"
                ),
                "weighted_shift": "NOT_RUN_AS_SEPARATE_PARAMETRIC_CLASS",
                "clock_shift_weyl": "REPRESENTATIVE_D3_D4_POINTS_TESTED",
                "permutation_plus_diagonal": (
                    "NOT_RUN_AS_SEPARATE_PARAMETRIC_CLASS"
                ),
                "rank_one_perturbation": (
                    "REPRESENTATIVE_AFFINE_MATRIX_UNIT_POINTS_TESTED"
                ),
                "non_normal": "REPRESENTATIVE_POINTS_TESTED",
                "reducible_but_indecomposable": (
                    "NOT_CLASSIFIED_AS_COMPLETE_STRATUM"
                ),
                "algebraic_number_entries": (
                    "REPRESENTATIVE_QUADRATIC_FIELD_POINTS_TESTED"
                ),
            },
        },
        "ansatz_class_summaries": class_summaries,
        "candidate_certificates": evaluated,
        "summary": {
            "candidate_count": len(evaluated),
            "commuting_control_count": len(controls),
            "commuting_controls_pass": controls_pass,
            "noncommuting_necessary_relation_survivor_count": len(
                noncommuting_survivors
            ),
            "full_compiled_relation_certificate_count": 0,
            "noncommutative_representation_found": False,
        },
        "search_digest_sha256": _stable_hash(digest_payload),
        "status": "CPOBC_REPRESENTATION_SEARCH_INCONCLUSIVE",
        "cpobc_representation_status": "CPOBC_SEARCH_INCONCLUSIVE",
        "completeness_scope": (
            "14 exact matrix points in d=3,4 over four declared fields; "
            "necessary relations 119, 130, and 163 only"
        ),
        "resource_limits": [
            "no dense symbolic Groebner or component decomposition",
            "no continuous parameter stratum is exhausted",
            "no full assignment of the 641 compiled transition relations",
        ],
        "unresolved_items": [
            "continuous parameter coverage for every requested ansatz stratum",
            "simultaneous-similarity quotient across all Jordan strata",
            "full generated relation assignment and exact residual certificate",
            (
                "a representation or a no-go theorem under mathematically "
                "complete assumptions"
            ),
        ],
        "prohibited_inference": (
            "No finite-grid failure is an ansatz-class or dimension-wide no-go "
            "theorem. NO_CANDIDATE_IN_DECLARED_EXACT_GRID means only the exact "
            "matrices and parameter points in the manifest; a necessary-relation survivor "
            "is not a representation until every compiled relation has an "
            "operator assignment and exact certificate."
        ),
        "claim_boundary": (
            "The search is exact but finite. It supplies structural and "
            "relation certificates, not a general representation theorem."
        ),
        "passed": controls_pass,
    }


def cpobc_representation_search() -> dict[str, Any]:
    """Run the deterministic exact d>=3 CPOBC ansatz search."""

    return copy.deepcopy(_representation_search_cached())
