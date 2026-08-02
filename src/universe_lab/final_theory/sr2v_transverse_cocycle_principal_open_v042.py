"""Branch-separated transverse SR2-V cocycle principal-open certificates.

Eq. (113)'s derived and literal readings are alternative semantic branches.
Eq. (139)'s printed-strict and Eq. (145)-completed domains are likewise kept
separate.  This module therefore builds four different homogeneous cocycle
matrices rather than imposing the alternative readings simultaneously.

At the exact ``basis-plus-20`` upper scalar point and normalized finite-CSG
bottom point, both literal-Eq. (113) matrices have rank 132.  Their fixed
132-row determinants are nonzero.  The two derived-Eq. (113) matrices have
rank 131, but their cutoff-external ``Q5`` column vanishes universally and
their 131 actual-transition columns have fixed nonzero minors.  Thus all four
semantic branches have separate nonempty principal opens on which the actual
transition cocycle is zero and ``Q1,...,Q4`` commute.  Only the literal
branches also force the supplemental ``Q5`` cocycle coordinate to zero.

No conclusion is drawn from the auxiliary matrix that imposes all alternative
readings simultaneously.  Pair/triple-irreducible and state-native D12 work is
also outside this certificate.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as bottom_global
from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_transverse_cocycle_principal_open.json"

SCHEMA = "final-theory-v042-sr2v-transverse-cocycle-principal-open-v2"
VERDICT = (
    "SR2V_TRANSVERSE_ALL_FOUR_SEMANTIC_BRANCHES_Q1_Q4_SPLITTING_"
    "PRINCIPAL_OPENS_CERTIFIED_NONTERMINAL"
)
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_TRANSVERSE_PRINCIPAL_OPENS_ONLY"

UPPER_BASIS_COLUMN = 20

DERIVED_STRICT = "derived_Eq113__strict_Eq139"
DERIVED_COMPLETED = "derived_Eq113__completed_Eq139"
LITERAL_STRICT = "literal_Eq113__strict_Eq139"
LITERAL_COMPLETED = "literal_Eq113__completed_Eq139"

COMMON_SELECTED_CPOBC = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    11,
    14,
    17,
    18,
    19,
    20,
    24,
    25,
    26,
    30,
    31,
    37,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
    67,
    70,
    73,
    76,
    79,
    82,
    85,
    91,
    94,
    97,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    135,
    136,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    144,
    145,
    146,
    149,
    154,
    155,
    164,
    172,
    203,
    204,
    205,
    206,
    215,
    216,
    217,
    218,
    223,
    224,
    225,
    226,
    231,
    232,
    233,
    234,
    235,
    236,
    393,
    399,
    695,
    696,
    697,
    698,
)

EXPECTED_SOURCE_SELECTIONS = {
    DERIVED_STRICT: (
        *COMMON_SELECTED_CPOBC,
        802,
        838,
        846,
        849,
        860,
        869,
        983,
        *range(1171, 1187),
    ),
    DERIVED_COMPLETED: (
        *COMMON_SELECTED_CPOBC,
        802,
        835,
        839,
        846,
        849,
        860,
        869,
        983,
        *range(1172, 1187),
    ),
    LITERAL_STRICT: (
        *COMMON_SELECTED_CPOBC,
        827,
        838,
        843,
        846,
        849,
        860,
        869,
        983,
        *range(1171, 1187),
    ),
    LITERAL_COMPLETED: (
        *COMMON_SELECTED_CPOBC,
        827,
        835,
        839,
        843,
        846,
        849,
        860,
        869,
        983,
        *range(1172, 1187),
    ),
}

EXPECTED_RANKS = {
    DERIVED_STRICT: 131,
    DERIVED_COMPLETED: 131,
    LITERAL_STRICT: 132,
    LITERAL_COMPLETED: 132,
}
EXPECTED_DETERMINANTS = {
    LITERAL_STRICT: Fraction(-52543903820625, 2**299),
    LITERAL_COMPLETED: Fraction(5517109901165625, 2**296),
}
EXPECTED_ACTUAL_131_DETERMINANTS = {
    DERIVED_STRICT: Fraction(52543903820625, 2**298),
    DERIVED_COMPLETED: Fraction(5517109901165625, 2**295),
}

SparseRow = dict[str, Fraction]


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _digest(semantic)


def _fraction_product(values: Any) -> Fraction:
    product = Fraction(1)
    for value in values:
        product *= Fraction(value)
    return product


def _operator_kernel(payload: dict[str, Any]) -> list[list[int]]:
    columns = payload["operator_scalar_block"]["integer_kernel"]["basis_columns"]
    if len(columns) != 49 or any(len(column) != 132 for column in columns):
        raise AssertionError("the primitive G_m^49 kernel shape changed")
    return [[int(value) for value in column] for column in columns]


def _upper_point(
    context: torus.ScoutContext,
    operator_kernel: list[list[int]],
) -> tuple[dict[str, Fraction], tuple[int, ...]]:
    exponents = tuple(operator_kernel[UPPER_BASIS_COLUMN])
    point = {
        variable: Fraction(2) ** exponent
        for variable, exponent in zip(context.variables, exponents, strict=True)
    }
    if not all(point.values()):
        raise AssertionError("the upper scalar point left its torus")
    return point, exponents


def _bottom_point(context: torus.ScoutContext) -> dict[str, Fraction]:
    point: dict[str, Fraction] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        value = torus._csg(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        previous = point.setdefault(variable, value)
        if previous != value:
            raise AssertionError("the normalized bottom CSG value changed on an ON orbit")
    point[torus.Q5] = torus._csg(5, (0,) * 5, 0)
    if point[torus.Q5] != Fraction(1, 32) or not all(point.values()):
        raise AssertionError("the exact bottom scalar point changed")
    return point


def _evaluate_monomial_row(
    row: lattice.SparseIntegerRow,
    point: dict[str, Fraction],
) -> Fraction:
    return _fraction_product(
        point[variable] ** exponent for variable, exponent in row.items()
    )


def _joint_row_labels(context: torus.ScoutContext) -> tuple[list[str], dict[str, Any]]:
    labels: list[str] = []
    blocks: dict[str, Any] = {}

    cpobc = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            label = f"CPOBC:{relation['relation_id']}:{equation['equation_id']}"
            labels.append(label)
            cpobc.append(label)
    blocks["CPOBC"] = {"count": len(cpobc), "row_ids": cpobc}

    eq113: dict[str, Any] = {}
    for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        branch_labels = []
        for relation in context.eq112["path_consistency_branches"][branch]:
            label = f"Eq113:{branch}:{relation['causet_id']}"
            labels.append(label)
            branch_labels.append(label)
        eq113[branch] = {"count": len(branch_labels), "row_ids": branch_labels}
    blocks["Eq113_alternative_branches"] = eq113

    completed_instances = torus._eq139_instances(torus.EQ139_COMPLETED)
    completed_labels = [
        f"Eq139:{torus.EQ139_COMPLETED}:{stage}:{left}:{right}"
        for stage, left, right in completed_instances
    ]
    labels.extend(completed_labels)
    strict_instances = torus._eq139_instances(torus.EQ139_STRICT)
    strict_labels = [
        f"Eq139:{torus.EQ139_STRICT}:{stage}:{left}:{right}"
        for stage, left, right in strict_instances
    ]
    blocks["Eq139_alternative_domains"] = {
        "printed_strict": {"count": len(strict_labels), "row_ids": strict_labels},
        "eq145_completed": {
            "count": len(completed_labels),
            "row_ids": completed_labels,
        },
    }

    gc = [
        f"fixed-GC:{relation['relation_id']}"
        for relation in context.operator_gc["generating_relation_basis"]
    ]
    labels.extend(gc)
    blocks["fixed_vector_GC_basis"] = {"count": len(gc), "row_ids": gc}

    msr = [
        f"MSR:{constraint['constraint_id']}"
        for constraint in context.cpobc["MSR_operator_constraints"]
    ]
    labels.extend(msr)
    blocks["reachable_state_MSR"] = {"count": len(msr), "row_ids": msr}
    if len(labels) != 1187:
        raise AssertionError("the auxiliary joint row inventory changed")
    return labels, blocks


def _eq139_row(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
    instance: tuple[int, int, int],
) -> SparseRow:
    def transition(stage: int, relation_code: int, precursor: int) -> torus.TriangularLinear:
        variable = context.signature_variables[(stage, relation_code, precursor)]
        relation = torus._decode_relation(stage, relation_code)
        return torus._linear_matrix(
            upper[variable],
            torus._csg(stage, relation, precursor),
            variable,
        )

    def q(stage: int) -> torus.TriangularLinear:
        variable = torus._q_variable(context, stage)
        return torus._linear_matrix(
            upper[variable],
            torus._csg(stage, (0,) * stage, 0),
            variable,
        )

    stage, left_index, right_index = instance
    left_transition = transition(stage, 0, (1 << left_index) - 1)
    right_transition = transition(stage, 0, (1 << right_index) - 1)
    current_q = q(stage)
    next_q = q(stage + 1)
    left = torus._linear_word(
        (
            left_transition,
            right_transition,
            next_q,
            torus._linear_inverse(right_transition),
            torus._linear_inverse(current_q),
            right_transition,
        )
    )
    right = torus._linear_word(
        (
            right_transition,
            left_transition,
            next_q,
            torus._linear_inverse(left_transition),
            torus._linear_inverse(current_q),
            left_transition,
        )
    )
    return torus._operator_residual(left, right)


def _universal_q5_decoupling_certificate(
    context: torus.ScoutContext,
) -> dict[str, Any]:
    """Certify that the derived-Eq. (113) branches never couple external Q5.

    The common CPOBC, fixed-vector-GC, and reachable-MSR builders use only
    actual transition variables.  Derived Eq. (113) contains Q3/Q4 but no Q5.
    Eq. (139) can mention Q5 as ``Q_(n+1)`` at stage four; the coefficient of
    that factor is nevertheless the same on its two word sides as a universal
    rational identity, so it cancels before any scalar specialization.
    """

    if context.variables[-1] != torus.Q5 or torus.Q5 in set(
        context.occurrence_variables.values()
    ):
        raise AssertionError("the cutoff-external coordinate inventory changed")

    cpobc_q5_failures = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            for occurrence_id in equation["operator_ids"].values():
                if context.occurrence_variables[str(occurrence_id)] == torus.Q5:
                    cpobc_q5_failures.append(str(occurrence_id))

    path_q5_failures = []
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                variable = context.signature_variables[
                    (
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    )
                ]
                if variable == torus.Q5:
                    path_q5_failures.append(str(path["path_id"]))

    msr_q5_failures = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        for term in constraint["terms"]:
            variable = context.occurrence_variables[str(term["transition_id"])]
            if variable == torus.Q5:
                msr_q5_failures.append(str(constraint["constraint_id"]))

    eq113_q5_counts = {}
    eq113_q_tokens = {}
    for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        tokens = []
        for relation in context.eq112["path_consistency_branches"][branch]:
            tokens.extend(relation["lhs_word"])
            tokens.extend(relation["rhs_word"])
        eq113_q5_counts[branch] = tokens.count("Q_5")
        eq113_q_tokens[branch] = sorted(
            {str(token) for token in tokens if str(token).startswith("Q_")}
        )

    (
        a_left,
        b_left,
        a_right,
        b_right,
        a_q,
        b_q,
        a_next,
        b_next,
        x_left,
        x_right,
        x_q,
        x_next,
    ) = sp.symbols(
        "a_left b_left a_right b_right a_q b_q "
        "a_next b_next x_left x_right x_q x_next",
        nonzero=True,
    )

    def matrix(a: Any, b: Any, x: Any) -> sp.Matrix:
        return sp.Matrix(((a, x), (0, b)))

    left_transition = matrix(a_left, b_left, x_left)
    right_transition = matrix(a_right, b_right, x_right)
    current_q = matrix(a_q, b_q, x_q)
    next_q = matrix(a_next, b_next, x_next)
    lhs = (
        left_transition
        * right_transition
        * next_q
        * right_transition.inv()
        * current_q.inv()
        * right_transition
    )
    rhs = (
        right_transition
        * left_transition
        * next_q
        * left_transition.inv()
        * current_q.inv()
        * left_transition
    )
    lhs_coefficient = sp.factor(sp.diff(lhs[0, 1], x_next))
    rhs_coefficient = sp.factor(sp.diff(rhs[0, 1], x_next))
    difference = sp.factor(lhs_coefficient - rhs_coefficient)
    expected_coefficient = a_left * a_right / b_q
    if (
        sp.simplify(lhs_coefficient - expected_coefficient) != 0
        or sp.simplify(rhs_coefficient - expected_coefficient) != 0
        or difference != 0
    ):
        raise AssertionError("the universal Eq139 Q_(n+1) cancellation changed")

    strict_stage_four = [
        list(instance)
        for instance in torus._eq139_instances(torus.EQ139_STRICT)
        if instance[0] == 4
    ]
    completed_stage_four = [
        list(instance)
        for instance in torus._eq139_instances(torus.EQ139_COMPLETED)
        if instance[0] == 4
    ]
    common_failures = {
        "CPOBC": cpobc_q5_failures,
        "fixed_vector_GC_paths": path_q5_failures,
        "reachable_state_MSR": msr_q5_failures,
    }
    derived_universally_decoupled = (
        not any(common_failures.values())
        and eq113_q5_counts[torus.EQ113_DERIVED] == 0
        and difference == 0
    )
    if not derived_universally_decoupled:
        raise AssertionError("the derived branch no longer universally decouples Q5")
    return {
        "coordinate": torus.Q5,
        "column": len(context.variables) - 1,
        "actual_transition_column_count": len(context.variables) - 1,
        "common_source_Q5_failures": common_failures,
        "Eq113_Q5_token_occurrences": eq113_q5_counts,
        "Eq113_Q_tokens": eq113_q_tokens,
        "Eq139_stage_four_instances_where_next_Q_is_Q5": {
            "printed_strict": strict_stage_four,
            "eq145_completed": completed_stage_four,
        },
        "Eq139_universal_next_Q_coefficient_template": {
            "lhs": str(lhs_coefficient),
            "rhs": str(rhs_coefficient),
            "difference": str(difference),
            "localisation_denominator": "b_q",
        },
        "derived_Eq113_strict_universal_Q5_column_is_zero": True,
        "derived_Eq113_completed_universal_Q5_column_is_zero": True,
        "literal_Eq113_contains_Q5_and_is_not_decoupled_by_this_argument": True,
    }


def _serialize_sparse_row(
    row: SparseRow,
    positions: dict[str, int],
) -> list[dict[str, Any]]:
    return [
        {"column": positions[variable], "variable": variable, "coefficient": str(value)}
        for variable, value in sorted(row.items(), key=lambda item: positions[item[0]])
        if value
    ]


def _tracked_row_echelon(
    rows: list[SparseRow],
    variables: tuple[str, ...],
) -> dict[str, Any]:
    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    selected_indices: list[int] = []
    raw_pivots: list[Fraction] = []
    for row_index, source in enumerate(rows):
        row = {
            positions[variable]: Fraction(value)
            for variable, value in source.items()
            if value
        }
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                selected_indices.append(row_index)
                raw_pivots.append(scale)
                basis[pivot] = {
                    column: value / scale for column, value in row.items()
                }
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    pivot_sequence = tuple(basis)
    inversions = sum(
        pivot_sequence[left] > pivot_sequence[right]
        for left, right in itertools.combinations(range(len(pivot_sequence)), 2)
    )
    return {
        "rank": len(basis),
        "basis": basis,
        "selected_indices": tuple(selected_indices),
        "pivot_sequence": pivot_sequence,
        "raw_pivots": tuple(raw_pivots),
        "column_permutation_inversion_parity": inversions % 2,
    }


def _kernel_vector(
    basis: dict[int, dict[int, Fraction]],
    width: int,
) -> tuple[Fraction, ...]:
    free = [column for column in range(width) if column not in basis]
    if len(free) != 1:
        raise AssertionError("a rank-131 branch must have one kernel coordinate")
    coordinates: dict[int, Fraction] = {free[0]: Fraction(1)}
    for pivot in sorted(basis, reverse=True):
        coordinates[pivot] = -sum(
            (
                coefficient * coordinates.get(column, Fraction(0))
                for column, coefficient in basis[pivot].items()
                if column != pivot
            ),
            start=Fraction(0),
        )
    return tuple(coordinates.get(column, Fraction(0)) for column in range(width))


def _branch_matrix(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
    joint_rows: list[SparseRow],
    joint_labels: list[str],
    eq113_branch: str,
    eq139_domain: str,
) -> tuple[list[SparseRow], list[str], list[int], list[str]]:
    rows = list(joint_rows[:783])
    labels = list(joint_labels[:783])
    source_indices = list(range(783))
    blocks = ["CPOBC"] * 783

    eq113_range = range(783, 808) if eq113_branch == torus.EQ113_DERIVED else range(808, 833)
    rows.extend(joint_rows[index] for index in eq113_range)
    labels.extend(joint_labels[index] for index in eq113_range)
    source_indices.extend(eq113_range)
    blocks.extend([eq113_branch] * 25)

    completed_instances = torus._eq139_instances(torus.EQ139_COMPLETED)
    if eq139_domain == torus.EQ139_STRICT:
        instances = torus._eq139_instances(torus.EQ139_STRICT)
        for instance in instances:
            source_index = 833 + completed_instances.index(instance)
            rows.append(_eq139_row(context, upper, instance))
            labels.append(
                f"Eq139:{torus.EQ139_STRICT}:{instance[0]}:{instance[1]}:{instance[2]}"
            )
            source_indices.append(source_index)
            blocks.append(torus.EQ139_STRICT)
    elif eq139_domain == torus.EQ139_COMPLETED:
        for source_index in range(833, 843):
            rows.append(joint_rows[source_index])
            labels.append(joint_labels[source_index])
            source_indices.append(source_index)
            blocks.append(torus.EQ139_COMPLETED)
    else:
        raise ValueError(f"unknown Eq139 domain: {eq139_domain}")

    rows.extend(joint_rows[843:1163])
    labels.extend(joint_labels[843:1163])
    source_indices.extend(range(843, 1163))
    blocks.extend(["fixed_vector_GC_basis"] * 320)
    rows.extend(joint_rows[1163:1187])
    labels.extend(joint_labels[1163:1187])
    source_indices.extend(range(1163, 1187))
    blocks.extend(["reachable_state_MSR"] * 24)
    return rows, labels, source_indices, blocks


def _branch_certificate(
    branch_id: str,
    context: torus.ScoutContext,
    rows: list[SparseRow],
    labels: list[str],
    source_indices: list[int],
    blocks: list[str],
    eq113_branch: str,
    eq139_domain: str,
    q5_decoupling: dict[str, Any],
) -> dict[str, Any]:
    expected_rows = 1156 if eq139_domain == torus.EQ139_STRICT else 1162
    if not (len(rows) == len(labels) == len(source_indices) == len(blocks) == expected_rows):
        raise AssertionError("one semantic branch matrix has the wrong shape")
    positions = {variable: index for index, variable in enumerate(context.variables)}
    elimination = _tracked_row_echelon(rows, context.variables)
    rank = int(elimination["rank"])
    selected_local = tuple(int(index) for index in elimination["selected_indices"])
    selected_sources = tuple(source_indices[index] for index in selected_local)
    if rank != EXPECTED_RANKS[branch_id]:
        raise AssertionError(f"the exact rank changed for {branch_id}")
    if selected_sources != EXPECTED_SOURCE_SELECTIONS[branch_id]:
        raise AssertionError(f"the selected row certificate changed for {branch_id}")

    selected_records = []
    selected_block_counts: Counter[str] = Counter()
    for selected_row, local_index in enumerate(selected_local):
        block = blocks[local_index]
        selected_block_counts[block] += 1
        selected_records.append(
            {
                "selected_row": selected_row,
                "branch_matrix_row": local_index,
                "source_joint_inventory_row": source_indices[local_index],
                "row_id": labels[local_index],
                "block": block,
                "coefficients": _serialize_sparse_row(rows[local_index], positions),
            }
        )

    matrix_records = [
        [labels[index], _serialize_sparse_row(row, positions)]
        for index, row in enumerate(rows)
    ]
    result: dict[str, Any] = {
        "branch_id": branch_id,
        "Eq113_branch": eq113_branch,
        "Eq139_domain": eq139_domain,
        "matrix_shape": [len(rows), len(context.variables)],
        "matrix_row_digest_sha256": _digest(matrix_records),
        "rank_at_exact_base_point": rank,
        "nullity_at_exact_base_point": len(context.variables) - rank,
        "selected_independent_row_count": len(selected_local),
        "selected_source_joint_inventory_rows": list(selected_sources),
        "selected_row_block_counts": dict(selected_block_counts),
        "selected_rows": selected_records,
        "selected_rows_digest_sha256": _digest(selected_records),
        "pivot_columns": list(elimination["pivot_sequence"]),
        "all_131_actual_transition_columns_are_pivots": set(range(131)).issubset(
            elimination["pivot_sequence"]
        ),
        "all_132_columns_are_pivots": sorted(elimination["pivot_sequence"])
        == list(range(132)),
    }

    if rank == 132:
        selected_matrix = sp.zeros(132, 132)
        for selected_row, local_index in enumerate(selected_local):
            for variable, value in rows[local_index].items():
                selected_matrix[selected_row, positions[variable]] = sp.Rational(
                    value.numerator,
                    value.denominator,
                )
        direct = sp.Rational(selected_matrix.det())
        determinant = Fraction(int(direct.p), int(direct.q))
        pivot_product = _fraction_product(elimination["raw_pivots"])
        if elimination["column_permutation_inversion_parity"]:
            pivot_product = -pivot_product
        expected_determinant = EXPECTED_DETERMINANTS[branch_id]
        if determinant != pivot_product or determinant != expected_determinant:
            raise AssertionError(f"the full-rank determinant changed for {branch_id}")
        result["full_rank_minor"] = {
            "tracked_elimination_determinant": str(pivot_product),
            "direct_sympy_determinant": str(determinant),
            "column_permutation_inversion_parity": elimination[
                "column_permutation_inversion_parity"
            ],
            "prime_factorisation": {
                "sign": -1 if determinant < 0 else 1,
                "numerator_prime_powers": {
                    str(prime): exponent
                    for prime, exponent in sp.factorint(abs(determinant.numerator)).items()
                },
                "denominator_prime_powers": {
                    str(prime): exponent
                    for prime, exponent in sp.factorint(determinant.denominator).items()
                },
            },
            "selected_matrix_digest_sha256": _digest(
                [
                    [str(selected_matrix[row, column]) for column in range(132)]
                    for row in range(132)
                ]
            ),
        }
        result["formal_principal_open"] = {
            "formal_minor": f"Delta_trans[{branch_id}]",
            "minor_shape": [132, 132],
            "columns": "all 131 actual transitions plus cutoff-external Q5",
            "exact_nonzero_evaluation": str(determinant),
            "principal_open_is_nonempty": True,
            "rank_on_principal_open": 132,
            "unique_kernel": "x=0",
            "actual_transition_cocycle": "x_actual=0",
            "cutoff_external_Q5_cocycle": "x_Q5=0",
            "Q1_through_Q4_conclusion": "diagonal and pairwise commuting",
        }
        result["branch_status"] = "FULL_RANK_PRINCIPAL_OPEN_CERTIFIED"
    else:
        kernel = _kernel_vector(elimination["basis"], 132)
        failures = []
        for row_index, row in enumerate(rows):
            residual = sum(
                (
                    coefficient * kernel[positions[variable]]
                    for variable, coefficient in row.items()
                ),
                start=Fraction(0),
            )
            if residual:
                failures.append(row_index)
        if failures:
            raise AssertionError(f"the rank-131 kernel check failed for {branch_id}")
        kernel_record = [
            {"column": index, "variable": context.variables[index], "coefficient": str(value)}
            for index, value in enumerate(kernel)
            if value
        ]
        result["rank_131_base_point_kernel"] = {
            "normalisation": "unique free coordinate set to 1",
            "nonzero_coordinates": kernel_record,
            "direct_row_failures": failures,
            "digest_sha256": _digest(kernel_record),
        }
        if eq113_branch != torus.EQ113_DERIVED:
            raise AssertionError("only a derived Eq113 branch may use the Q5 decoupling")
        q5_key = (
            "derived_Eq113_strict_universal_Q5_column_is_zero"
            if eq139_domain == torus.EQ139_STRICT
            else "derived_Eq113_completed_universal_Q5_column_is_zero"
        )
        if not q5_decoupling[q5_key]:
            raise AssertionError("the rank-131 branch lacks universal Q5 decoupling")
        actual_matrix = sp.zeros(131, 131)
        for selected_row, local_index in enumerate(selected_local):
            for variable, value in rows[local_index].items():
                column = positions[variable]
                if column < 131:
                    actual_matrix[selected_row, column] = sp.Rational(
                        value.numerator,
                        value.denominator,
                    )
                elif value:
                    raise AssertionError("the specialized derived Q5 column is nonzero")
        direct = sp.Rational(actual_matrix.det())
        determinant = Fraction(int(direct.p), int(direct.q))
        pivot_product = _fraction_product(elimination["raw_pivots"])
        if elimination["column_permutation_inversion_parity"]:
            pivot_product = -pivot_product
        expected_determinant = EXPECTED_ACTUAL_131_DETERMINANTS[branch_id]
        if determinant != pivot_product or determinant != expected_determinant:
            raise AssertionError(f"the actual-column determinant changed for {branch_id}")
        result["actual_131_column_minor"] = {
            "tracked_elimination_determinant": str(pivot_product),
            "direct_sympy_determinant": str(determinant),
            "column_permutation_inversion_parity": elimination[
                "column_permutation_inversion_parity"
            ],
            "prime_factorisation": {
                "sign": -1 if determinant < 0 else 1,
                "numerator_prime_powers": {
                    str(prime): exponent
                    for prime, exponent in sp.factorint(abs(determinant.numerator)).items()
                },
                "denominator_prime_powers": {
                    str(prime): exponent
                    for prime, exponent in sp.factorint(determinant.denominator).items()
                },
            },
            "selected_matrix_digest_sha256": _digest(
                [
                    [str(actual_matrix[row, column]) for column in range(131)]
                    for row in range(131)
                ]
            ),
        }
        result["formal_principal_open"] = {
            "formal_minor": f"Delta_actual[{branch_id}]",
            "minor_shape": [131, 131],
            "columns": "all 131 actual transition coordinates; Q5 omitted",
            "exact_nonzero_evaluation": str(determinant),
            "principal_open_is_nonempty": True,
            "rank_on_principal_open": 131,
            "kernel_on_principal_open": "span(e_Q5)",
            "actual_transition_cocycle": "x_actual=0",
            "cutoff_external_Q5_cocycle": "free and universally decoupled",
            "Q1_through_Q4_conclusion": "diagonal and pairwise commuting",
        }
        result["branch_status"] = (
            "ACTUAL_131_COLUMN_FULL_RANK_PRINCIPAL_OPEN_CERTIFIED_Q5_FREE_DECOUPLED"
        )
    return result


def build_payload(root: Path) -> dict[str, Any]:
    """Rebuild all four semantic cocycle branches and their exact certificates."""

    root = root.resolve()
    frozen_lattice = _load(root / lattice.RESULT_PATH)
    frozen_bottom = _load(root / bottom_global.RESULT_PATH)
    if (
        frozen_lattice.get("verdict") != lattice.VERDICT
        or frozen_lattice.get("semantic_digest_sha256")
        != lattice.semantic_digest(frozen_lattice)
        or frozen_lattice != lattice.build_payload(root)
    ):
        raise AssertionError("the primitive scalar-lattice binding failed")
    if (
        frozen_bottom.get("verdict") != bottom_global.VERDICT
        or frozen_bottom.get("semantic_digest_sha256")
        != bottom_global.semantic_digest(frozen_bottom)
        or frozen_bottom != bottom_global.build_payload(root)
    ):
        raise AssertionError("the global bottom-MSR/CSG binding failed")

    context = torus._build_context(root)
    operator_kernel = _operator_kernel(frozen_lattice)
    upper, upper_exponents = _upper_point(context, operator_kernel)
    bottom = _bottom_point(context)
    lattice_context = lattice._build_context(root)
    operator_rows, _ = lattice._operator_lattice_rows(lattice_context)
    fixed_gc_rows = lattice._fixed_gc_rows(lattice_context)
    upper_monomial_failures = [
        label for label, row in operator_rows if _evaluate_monomial_row(row, upper) != 1
    ]
    bottom_monomial_failures = [
        label
        for label, row in [*operator_rows, *fixed_gc_rows]
        if _evaluate_monomial_row(row, bottom) != 1
    ]
    bottom_msr_failures = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        residual = Fraction(int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            variable = context.occurrence_variables[str(term["transition_id"])]
            residual += Fraction(int(term["coefficient"])) * bottom[variable]
        if residual:
            bottom_msr_failures.append(str(constraint["constraint_id"]))
    occurrence_determinant_failures = []
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        if not upper[variable] * bottom[variable]:
            occurrence_determinant_failures.append(str(record["occurrence_id"]))
    q5_determinant = upper[torus.Q5] * bottom[torus.Q5]
    if (
        upper_monomial_failures
        or bottom_monomial_failures
        or bottom_msr_failures
        or occurrence_determinant_failures
        or not q5_determinant
    ):
        raise AssertionError("the exact scalar base point failed")

    joint_rows, joint_counts, commutators, _ = torus._linear_system(context, upper)
    joint_labels, provenance = _joint_row_labels(context)
    q5_decoupling = _universal_q5_decoupling_certificate(context)
    if joint_counts != {
        "CPOBC": 783,
        "Eq113_both_branches": 50,
        "Eq139_completed": 10,
        "fixed_vector_GC_basis": 320,
        "reachable_state_MSR": 24,
    }:
        raise AssertionError("the auxiliary joint matrix inventory changed")

    branch_specs = {
        DERIVED_STRICT: (torus.EQ113_DERIVED, torus.EQ139_STRICT),
        DERIVED_COMPLETED: (torus.EQ113_DERIVED, torus.EQ139_COMPLETED),
        LITERAL_STRICT: (torus.EQ113_LITERAL, torus.EQ139_STRICT),
        LITERAL_COMPLETED: (torus.EQ113_LITERAL, torus.EQ139_COMPLETED),
    }
    branches = {}
    for branch_id, (eq113_branch, eq139_domain) in branch_specs.items():
        branch_rows, branch_labels, source_indices, blocks = _branch_matrix(
            context,
            upper,
            joint_rows,
            joint_labels,
            eq113_branch,
            eq139_domain,
        )
        branches[branch_id] = _branch_certificate(
            branch_id,
            context,
            branch_rows,
            branch_labels,
            source_indices,
            blocks,
            eq113_branch,
            eq139_domain,
            q5_decoupling,
        )

    positions = {variable: index for index, variable in enumerate(context.variables)}
    joint_records = [
        [joint_labels[index], _serialize_sparse_row(row, positions)]
        for index, row in enumerate(joint_rows)
    ]
    joint_elimination = _tracked_row_echelon(joint_rows, context.variables)
    commutator_records = {
        pair: _serialize_sparse_row(row, positions)
        for pair, row in sorted(commutators.items())
    }

    nonzero_upper = [
        {"variable": variable, "base_2_exponent": exponent, "value": str(upper[variable])}
        for variable, exponent in zip(context.variables, upper_exponents, strict=True)
        if exponent
    ]
    bottom_records = [
        {"variable": variable, "value": str(bottom[variable])}
        for variable in context.variables
    ]

    gates = {
        "exact_scalar_base_point_is_nonsingular_and_on_both_scalar_loci": not (
            upper_monomial_failures
            or bottom_monomial_failures
            or bottom_msr_failures
            or occurrence_determinant_failures
        )
        and bool(q5_determinant),
        "four_alternative_semantic_matrices_are_built_separately": set(branches)
        == set(branch_specs),
        "derived_branches_have_exact_base_rank_131": branches[DERIVED_STRICT][
            "rank_at_exact_base_point"
        ]
        == 131
        and branches[DERIVED_COMPLETED]["rank_at_exact_base_point"] == 131,
        "literal_branches_have_exact_base_rank_132": branches[LITERAL_STRICT][
            "rank_at_exact_base_point"
        ]
        == 132
        and branches[LITERAL_COMPLETED]["rank_at_exact_base_point"] == 132,
        "derived_branches_universally_decouple_cutoff_external_Q5": all(
            q5_decoupling[key]
            for key in (
                "derived_Eq113_strict_universal_Q5_column_is_zero",
                "derived_Eq113_completed_universal_Q5_column_is_zero",
            )
        ),
        "all_four_branches_have_independent_nonzero_splitting_minors": all(
            branches[key]["formal_principal_open"]["principal_open_is_nonempty"]
            for key in branch_specs
        ),
        "derived_actual_131_columns_are_full_rank_on_certified_opens": all(
            branches[key]["all_131_actual_transition_columns_are_pivots"]
            and branches[key]["formal_principal_open"]["rank_on_principal_open"]
            == 131
            for key in (DERIVED_STRICT, DERIVED_COMPLETED)
        ),
        "literal_full_132_columns_are_full_rank_on_certified_opens": all(
            branches[key]["all_132_columns_are_pivots"]
            and branches[key]["formal_principal_open"]["rank_on_principal_open"]
            == 132
            for key in (LITERAL_STRICT, LITERAL_COMPLETED)
        ),
        "joint_all_readings_matrix_is_auxiliary_only": joint_elimination["rank"] == 132,
    }
    if not all(gates.values()):
        raise AssertionError(f"branch-separated cocycle gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "finite_scope": "n<=4",
        "dimension": 2,
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "semantic_branch_rule": {
            "Eq113": "derived and literal readings are alternative branches, never simultaneous",
            "Eq139": "printed-strict and Eq145-completed domains are alternative branches",
            "matrix_count": 4,
            "joint_all_readings_inference_forbidden": True,
        },
        "declared_chart": {
            "matrix_form": "A_e=[[a_e,x_e],[0,b_e]]",
            "initial_vector": "e_2",
            "interpretation": "globally reducible line transverse to the initial vector",
            "upper_scalar_base": "primitive operator G_m^49",
            "bottom_scalar_base": "global normalized finite-CSG bottom locus of dimension 5",
            "joint_scalar_base_dimension": 54,
            "upper_right_coordinates": 132,
        },
        "field": {
            "base_point_and_matrices": "QQ",
            "formal_matrix_coefficients": (
                "regular Laurent/rational functions on the declared scalar base"
            ),
            "floating_point_used": False,
            "finite_field_used": False,
            "groebner_used": False,
            "sage_used": False,
        },
        "input_artifacts": {
            lattice.RESULT_PATH: {
                "raw_sha256": _sha256(root / lattice.RESULT_PATH),
                "semantic_digest_sha256": frozen_lattice["semantic_digest_sha256"],
            },
            bottom_global.RESULT_PATH: {
                "raw_sha256": _sha256(root / bottom_global.RESULT_PATH),
                "semantic_digest_sha256": frozen_bottom["semantic_digest_sha256"],
            },
            **{
                relative: {"raw_sha256": _sha256(root / relative)}
                for relative in (
                    torus.CPOBC_PATH,
                    torus.REDUCTION_PATH,
                    torus.OPERATOR_GC_PATH,
                    torus.ATOMISATION_PATH,
                    torus.EQ112_PATH,
                )
            },
        },
        "exact_scalar_base_point": {
            "upper": {
                "candidate_id": "basis-plus-20",
                "primitive_kernel_column": UPPER_BASIS_COLUMN,
                "base": 2,
                "exponents_in_variable_order": list(upper_exponents),
                "nonzero_exponent_coordinates": nonzero_upper,
                "all_843_operator_monomial_rows_hold": not upper_monomial_failures,
            },
            "bottom": {
                "family": "normalized finite CSG t0=t1=t2=t3=t4=1",
                "cutoff_external_Q5": "1/32",
                "coordinates_in_variable_order": bottom_records,
                "all_1163_bottom_monomial_rows_hold": not bottom_monomial_failures,
                "all_24_additive_MSR_rows_hold": not bottom_msr_failures,
            },
            "nonsingularity": {
                "occurrences_checked": len(context.occurrence_records),
                "occurrence_determinant_failures": occurrence_determinant_failures,
                "supplemental_Q5_determinant": str(q5_determinant),
                "all_165_occurrences_and_Q5_are_nonsingular": not (
                    occurrence_determinant_failures
                )
                and bool(q5_determinant),
            },
        },
        "row_provenance": {
            "common_counts": {
                "CPOBC": 783,
                "fixed_vector_GC_basis": 320,
                "reachable_state_MSR": 24,
            },
            "alternative_counts": {
                "Eq113_derived": 25,
                "Eq113_literal": 25,
                "Eq139_printed_strict": 4,
                "Eq139_completed": 10,
            },
            "full_row_id_ledgers": provenance,
            "Eq113_branches_merged": False,
            "Eq139_domains_merged": False,
        },
        "universal_cutoff_Q5_decoupling": q5_decoupling,
        "semantic_branch_certificates": branches,
        "all_four_branch_principal_open_conclusion": {
            "branches_covered_separately": list(branch_specs),
            "formal_minors": [
                branches[key]["formal_principal_open"]["formal_minor"]
                for key in branch_specs
            ],
            "each_principal_open_is_nonempty": True,
            "actual_transition_kernel_on_each_open": "x_actual=0",
            "operator_conclusion_on_each_open": (
                "Q1,Q2,Q3,Q4 are diagonal and pairwise commuting"
            ),
            "cutoff_external_Q5_distinction": (
                "free decoupled direction on each derived branch open; zero on each "
                "literal branch open"
            ),
        },
        "literal_branch_principal_open_conclusion": {
            "Eq139_domains_covered_separately": [
                torus.EQ139_STRICT,
                torus.EQ139_COMPLETED,
            ],
            "formal_minors": [
                branches[LITERAL_STRICT]["formal_principal_open"]["formal_minor"],
                branches[LITERAL_COMPLETED]["formal_principal_open"]["formal_minor"],
            ],
            "each_principal_open_is_nonempty": True,
            "kernel_on_each_open": "x=0",
            "operator_conclusion_on_each_open": (
                "Q1,Q2,Q3,Q4 are diagonal and pairwise commuting"
            ),
            "possible_literal_transverse_noncommutative_loci": [
                f"Delta_trans[{LITERAL_STRICT}]=0",
                f"Delta_trans[{LITERAL_COMPLETED}]=0",
            ],
        },
        "derived_branch_status": {
            "strict_rank_at_base_point": 131,
            "completed_rank_at_base_point": 131,
            "full_132_column_principal_open_certified": False,
            "actual_131_column_principal_opens_certified": True,
            "universal_kernel_direction": "cutoff-external Q5",
            "Q1_through_Q4_splitting_on_each_open": True,
            "interpretation": (
                "the universal Q5 column is zero; each nonzero actual-column minor "
                "forces all 131 actual transition cocycles to zero while Q5 remains free"
            ),
        },
        "joint_all_readings_auxiliary": {
            "matrix_shape": [len(joint_rows), len(context.variables)],
            "rank_at_base_point": joint_elimination["rank"],
            "matrix_row_digest_sha256": _digest(joint_records),
            "semantic_status": (
                "AUXILIARY_OVERCONSTRAINED_INTERSECTION_ONLY_NO_BRANCH_INFERENCE"
            ),
            "used_for_any_principal_open_conclusion": False,
        },
        "commutator_rows": {
            "count": len(commutator_records),
            "rows": commutator_records,
            "zero_cocycle_forces_all_six_rows_zero": True,
        },
        "resource_and_claim_boundaries": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "determinants_expanded_over_54_base_parameters": False,
            "literal_determinant_zero_hypersurfaces_solved": False,
            "derived_actual_determinant_zero_hypersurfaces_solved": False,
            "derived_Eq113_branches_globally_solved": False,
            "full_transverse_scalar_base_obstructed": False,
            "pair_or_triple_irreducible_branch_touched": False,
            "state_native_D12_manifest_touched": False,
            "global_weak_weak_obstruction_claimed": False,
            "next_exact_gate": (
                "analyse the four branch-specific determinant-zero loci without "
                "combining the alternative Eq113 or Eq139 semantics"
            ),
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "This exact certificate proves four separate nonempty splitting principal "
            "opens, one for each alternative Eq113/Eq139 semantic combination.  In the "
            "derived Eq113 branches the cutoff-external Q5 column is universally zero, "
            "and a nonzero 131-by-131 actual-transition minor forces Q1 through Q4 to be "
            "diagonal and commuting while Q5 remains free.  In the literal branches a "
            "nonzero full 132-by-132 minor also fixes Q5.  It never combines alternative "
            "semantic readings.  It does not solve the four determinant-zero boundaries, "
            "obstruct the full transverse chart or weak/weak profile, touch pair/triple-"
            "irreducible or state-native D12 branches, certify a witness, or issue an "
            "SR2-V terminal."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    result = run()
    print(result["verdict"])
    print(result["semantic_digest_sha256"])
