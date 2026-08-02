"""Global Q5-free Schur reduction for the transverse weak/weak common core.

The certified 127-column unit block eliminates every non-Q upper-right
coordinate.  This successor proves, directly from the source inventory and an
independent symbolic compilation, that the external Q5 coefficient is absent
from every one of the 1,127 common-core rows and from all 127 pivot rows.
Consequently Schur elimination cannot create a Q5 coefficient.

The result is deliberately scoped to ``M0 = raw CPOBC + fixed-vector GC +
reachable-state MSR``.  Eq. (113) and Eq. (139) rows require a new Q5 audit if
they are later added branchwise.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import sr2v_transverse_common_core_unit_minor_v042 as unit_minor
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_transverse_common_core_q5_free.json"
SCHEMA = "final-theory-v042-sr2v-transverse-common-core-q5-free-v2"
VERDICT = "SR2V_TRANSVERSE_COMMON_CORE_Q5_FREE_SCHUR_REDUCTION_CERTIFIED_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_FULL_M0_POINTWISE_IDEAL_CERTIFICATES_REMAIN"

EXPECTED_UNIT_MINOR_SEMANTIC_DIGEST = (
    "286b2c8e0329dd585c33dee13c66e3a923a270d04822f3489186aad4ee1e45ac"
)
EXPECTED_M0_SOURCE_INDEX_DIGEST = "5305add80b371fda81ee189e24a5a6d13addcca0439c1de7a6dc36f871d18012"
EXPECTED_M0_ROW_LABEL_DIGEST = "7d13c8873f00ae2709ed7f3c8408adf2d3a02931fef89520b05fe561f83138f0"
EXPECTED_PIVOT_SOURCE_INDEX_DIGEST = (
    "b9800e6b358b6f24476f268d46d4bd12f9c263706281db05064396179bf546d0"
)
EXPECTED_PIVOT_ROW_LABEL_DIGEST = "36d81c06234bced8b11a256b6262c5d175e2181ef420a2ae9c9dd1ed3644fafc"
EXPECTED_Q5_ZERO_LEDGER_DIGEST = "8c350de36aafee6a449733f81dab1e26d02668f15c6a7fd9c16524b8e61a1fd0"
EXPECTED_FULL_SYMBOLIC_SUPPORT_LEDGER_DIGEST = (
    "fffd8dc361df49a22e07b6f2feefd10c647478d3aa18fdf08d5c230f888a70be"
)
EXPECTED_PIVOT_SYMBOLIC_SUPPORT_LEDGER_DIGEST = (
    "6b1bae9d77c5f6225f85644ede768fcc4472a4dfd924b79e43ccd9657a12ec73"
)
EXPECTED_POINT_RECORDS_DIGEST = "72515db27573409d1fb7b5767ad5ff08ffa2cddd28e8eeb79e0f746c0da21161"
EXPECTED_BLOCK_SYMBOLIC_SUPPORT_EDGES = {
    "raw_CPOBC": 2831,
    "fixed_vector_GC": 1677,
    "reachable_state_MSR": 191,
}

M0_SOURCES = (*range(783), *range(843, 1187))
PIVOT_SOURCES = (
    *unit_minor.CPOBC_ROWS,
    *(843 + offset for offset in unit_minor.GC_OFFSETS),
    *(1163 + offset for offset in unit_minor.MSR_OFFSETS),
)
POINT_FACTORS: dict[str, tuple[tuple[int, Fraction], ...]] = {
    "reference_equal": (),
    "g2_pair_rejection": (
        (12, Fraction(1)),
        (13, Fraction(2)),
        (15, Fraction(1)),
        (44, Fraction(3)),
        (45, Fraction(3)),
    ),
    "g3_pair_rejection": (
        (12, Fraction(1)),
        (13, Fraction(3)),
        (15, Fraction(1)),
        (44, Fraction(2)),
        (45, Fraction(2)),
    ),
    "three_pair_common_zero": (
        (12, Fraction(1)),
        (13, Fraction(1, 2)),
        (15, Fraction(1)),
        (44, Fraction(2)),
        (45, Fraction(2)),
    ),
}
EXPECTED_POINT_RANK_AND_NONZERO_SCHUR_ROWS = {
    "reference_equal": (127, 0),
    "g2_pair_rejection": (131, 597),
    "g3_pair_rejection": (131, 597),
    "three_pair_common_zero": (131, 582),
}

SparseExprRow = dict[str, sp.Expr]
SparseRow = dict[str, Fraction]


@dataclass(frozen=True)
class SymbolicRow:
    block: str
    joint_source: int
    coefficients: SparseExprRow


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _digest(semantic)


def _source_reference_census(context: torus.ScoutContext) -> dict[str, Any]:
    q5 = torus.Q5
    raw_occurrences = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            raw_occurrences.extend(equation["operator_ids"].values())

    path_variables = []
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                path_variables.append(
                    context.signature_variables[
                        (
                            int(signature["stage"]),
                            int(signature["source_relation_code"]),
                            int(signature["precursor_code"]),
                        )
                    ]
                )

    msr_variables = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        for term in constraint["terms"]:
            msr_variables.append(context.occurrence_variables[str(term["transition_id"])])

    return {
        "Q5_variable": q5,
        "Q5_context_index": context.variables.index(q5),
        "context_variable_count": len(context.variables),
        "Q5_is_an_occurrence_variable": q5 in set(context.occurrence_variables.values()),
        "Q5_is_a_signature_variable": q5 in set(context.signature_variables.values()),
        "raw_CPOBC": {
            "row_count": 783,
            "operator_reference_count": len(raw_occurrences),
            "references_resolving_to_Q5": sum(
                context.occurrence_variables[occurrence] == q5 for occurrence in raw_occurrences
            ),
        },
        "fixed_vector_GC": {
            "generator_count": len(context.operator_gc["generating_relation_basis"]),
            "path_transition_reference_count": len(path_variables),
            "references_resolving_to_Q5": path_variables.count(q5),
        },
        "reachable_state_MSR": {
            "constraint_count": len(context.cpobc["MSR_operator_constraints"]),
            "transition_reference_count": len(msr_variables),
            "references_resolving_to_Q5": msr_variables.count(q5),
            "anchor_paths_use_the_same_Q5_free_path_inventory": True,
        },
        "source_generation_provenance": {
            "context_builder": "weak_d2_visible_torus_scout_v042._build_context",
            "raw_CPOBC": (
                "cpobc.relations[*].raw_noncommutative_relation, resolved only "
                "through occurrence_variables"
            ),
            "fixed_vector_GC": (
                "operator_gc.generating_relation_basis over path_inventory, resolved "
                "only through signature_variables"
            ),
            "reachable_state_MSR": (
                "cpobc.MSR_operator_constraints multiplied by one endpoint anchor "
                "from the same operator_gc path_inventory"
            ),
            "Q_stage_selector_role": (
                "the q(stage) / _q_variable selector that can return external Q5 is "
                "not invoked by any of the three M0 source builders; it belongs to "
                "Eq113 token parsing, Eq139, commutator, and diagnostic builders"
            ),
        },
    }


def _semantic_branch_inheritance_certificate(
    context: torus.ScoutContext,
) -> dict[str, Any]:
    lower = locus.bottom_character(locus.NORMALIZED_COUPLINGS, locus.NORMALIZED_Q5)
    upper = locus.bottom_point(context, lower)
    joint_rows, _counts, _commutators, _paths = torus._linear_system(context, upper, lower)
    joint_labels, _blocks = transverse._joint_row_labels(context)
    branches = {}
    for branch_id, (eq113, eq139) in locus.BRANCH_SPECS.items():
        rows, _labels, source_indices, blocks = transverse._branch_matrix(
            context, upper, joint_rows, joint_labels, eq113, eq139
        )
        inherited_sources = [source for source in source_indices if source in M0_SOURCES]
        branches[branch_id] = {
            "Eq113_reading": eq113,
            "Eq139_reading": eq139,
            "row_count": len(rows),
            "row_block_counts": dict(Counter(blocks)),
            "row_construction": (
                "raw_CPOBC + selected Eq113 rows + selected Eq139 rows + "
                "fixed-vector GC + reachable-state MSR"
            ),
            "M0_source_order_digest_sha256": _digest(inherited_sources),
            "contains_all_1127_M0_rows_once_and_in_order": inherited_sources == list(M0_SOURCES),
        }
    return {
        "branch_count": len(branches),
        "branches": branches,
        "inheritance_rule": (
            "any pointwise commutativity conclusion proved from M0 alone is inherited "
            "by each semantic branch because every branch matrix is M0 plus rows"
        ),
        "non_converse_warning": (
            "Q5-freeness of M0 does not assert Q5-freeness of appended Eq113/Eq139 "
            "rows; those rows retain their existing branch-separated audit"
        ),
    }


def _symbolic_full_m0_rows(context: torus.ScoutContext) -> list[SymbolicRow]:
    upper = {variable: sp.Symbol(f"a{index}") for index, variable in enumerate(context.variables)}
    lower = {variable: sp.Symbol(f"b{index}") for index, variable in enumerate(context.variables)}

    def matrix(variable: str) -> unit_minor.SymbolicTriangular:
        return unit_minor.SymbolicTriangular(
            upper[variable], lower[variable], {variable: sp.Integer(1)}
        )

    occurrence_matrices = {
        occurrence: matrix(context.occurrence_variables[occurrence])
        for occurrence in context.occurrence_records
    }

    def from_signature(
        stage: int, relation_code: int, precursor: int
    ) -> unit_minor.SymbolicTriangular:
        return matrix(context.signature_variables[(stage, relation_code, precursor)])

    rows: list[SymbolicRow] = []
    raw_index = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            left = unit_minor._word(
                occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"]
            )
            right = unit_minor._word(
                occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
            )
            rows.append(
                SymbolicRow(
                    "raw_CPOBC",
                    raw_index,
                    unit_minor._add(
                        left.coefficients,
                        unit_minor._scale(-1, right.coefficients),
                    ),
                )
            )
            raw_index += 1

    path_matrices: dict[str, unit_minor.SymbolicTriangular] = {}
    path_records: dict[str, dict[str, Any]] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = unit_minor.SymbolicTriangular(sp.Integer(1), sp.Integer(1), {})
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                transition = from_signature(
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                product = unit_minor._multiply(transition, product)
            path_id = str(path["path_id"])
            path_matrices[path_id] = product
            path_records[path_id] = path

    for offset, relation in enumerate(context.operator_gc["generating_relation_basis"]):
        left = path_matrices[str(relation["lhs_path_id"])]
        right = path_matrices[str(relation["rhs_path_id"])]
        rows.append(
            SymbolicRow(
                "fixed_vector_GC",
                843 + offset,
                unit_minor._add(
                    left.coefficients,
                    unit_minor._scale(-1, right.coefficients),
                ),
            )
        )

    anchors: dict[str, unit_minor.SymbolicTriangular] = {}
    for path_id, path in sorted(path_records.items()):
        anchors.setdefault(str(path["endpoint_causet_id"]), path_matrices[path_id])
    for offset, constraint in enumerate(context.cpobc["MSR_operator_constraints"]):
        residual_upper_left = sp.Integer(int(constraint["identity_coefficient"]))
        residual_upper: defaultdict[str, sp.Expr] = defaultdict(lambda: sp.Integer(0))
        for term in constraint["terms"]:
            occurrence = str(term["transition_id"])
            coefficient = sp.Integer(int(term["coefficient"]))
            residual_upper_left += coefficient * occurrence_matrices[occurrence].upper_left
            for variable, value in occurrence_matrices[occurrence].coefficients.items():
                residual_upper[variable] += coefficient * value
        state = anchors[str(constraint["source_id"])]
        rows.append(
            SymbolicRow(
                "reachable_state_MSR",
                1163 + offset,
                unit_minor._add(
                    unit_minor._scale(residual_upper_left, state.coefficients),
                    unit_minor._scale(
                        state.lower_right,
                        unit_minor._clean(dict(residual_upper)),
                    ),
                ),
            )
        )

    if raw_index != 783 or [row.joint_source for row in rows] != list(M0_SOURCES):
        raise AssertionError("the full symbolic M0 inventory changed")
    return rows


def _symbolic_rows_equal(left: SparseExprRow, right: SparseExprRow) -> bool:
    return all(
        sp.cancel(left.get(variable, 0) - right.get(variable, 0)) == 0
        for variable in set(left) | set(right)
    )


def _symbolic_support_certificate(
    context: torus.ScoutContext,
) -> dict[str, Any]:
    labels, _blocks = transverse._joint_row_labels(context)
    rows = _symbolic_full_m0_rows(context)
    by_source = {row.joint_source: row.coefficients for row in rows}
    q5 = torus.Q5
    block_counts = Counter(row.block for row in rows)
    block_support_edges = Counter(
        {block: 0 for block in ("raw_CPOBC", "fixed_vector_GC", "reachable_state_MSR")}
    )
    for row in rows:
        block_support_edges[row.block] += len(row.coefficients)

    support_ledger = [
        {
            "joint_source": row.joint_source,
            "block": row.block,
            "row_id": labels[row.joint_source],
            "support": sorted(row.coefficients),
            "Q5_symbolic_coefficient": str(row.coefficients.get(q5, 0)),
        }
        for row in rows
    ]
    q5_zero_ledger = [
        {"joint_source": source, "Q5_symbolic_coefficient": "0"} for source in M0_SOURCES
    ]

    selected, _upper, _lower = unit_minor._symbolic_selected_rows(context)
    pivot_matches = all(
        _symbolic_rows_equal(selected[index], by_source[source])
        for index, source in enumerate(PIVOT_SOURCES)
    )
    pivot_support_ledger = [
        {
            "joint_source": source,
            "row_id": labels[source],
            "support": sorted(selected[index]),
            "Q5_symbolic_coefficient": str(selected[index].get(q5, 0)),
        }
        for index, source in enumerate(PIVOT_SOURCES)
    ]

    return {
        "M0_row_count": len(rows),
        "block_row_counts": dict(block_counts),
        "block_symbolic_support_edge_counts": dict(block_support_edges),
        "M0_source_index_digest_sha256": _digest(list(M0_SOURCES)),
        "M0_row_label_digest_sha256": _digest([labels[source] for source in M0_SOURCES]),
        "full_symbolic_support_ledger_digest_sha256": _digest(support_ledger),
        "Q5_zero_ledger_digest_sha256": _digest(q5_zero_ledger),
        "rows_with_Q5_support_key": sum(q5 in row.coefficients for row in rows),
        "rows_with_nonzero_Q5_symbolic_coefficient": sum(
            row.coefficients.get(q5, 0) != 0 for row in rows
        ),
        "pivot_row_count": len(selected),
        "pivot_source_index_digest_sha256": _digest(list(PIVOT_SOURCES)),
        "pivot_row_label_digest_sha256": _digest([labels[source] for source in PIVOT_SOURCES]),
        "pivot_symbolic_support_ledger_digest_sha256": _digest(pivot_support_ledger),
        "pivot_rows_with_Q5_support_key": sum(q5 in row for row in selected),
        "pivot_rows_with_nonzero_Q5_symbolic_coefficient": sum(
            row.get(q5, 0) != 0 for row in selected
        ),
        "selected_pivot_rows_match_full_symbolic_compiler": pivot_matches,
    }


def _schur_identity_certificate() -> dict[str, Any]:
    p11, p12, p21, p22 = sp.symbols("p11 p12 p21 p22")
    u11, u12, u21, u22 = sp.symbols("u11 u12 u21 u22")
    v1, v2, w1, w2 = sp.symbols("v1 v2 w1 w2")
    p = sp.Matrix([[p11, p12], [p21, p22]])
    u = sp.Matrix([[u11, u12], [u21, u22]])
    pivot = p.row_join(u).row_join(sp.zeros(2, 1))
    source = sp.Matrix([[v1, v2, w1, w2, 0]])
    reduced = source - sp.Matrix([[v1, v2]]) * p.inv() * pivot
    non_q_checks = [sp.factor(sp.cancel(reduced[index])) for index in range(2)]
    q5_check = sp.factor(sp.cancel(reduced[4]))
    if non_q_checks != [0, 0] or q5_check != 0:
        raise AssertionError("the generic Q5-free Schur identity changed")
    return {
        "dimension_free_block_form": {
            "pivot_rows": "[P U 0_Q5] with P 127 by 127",
            "arbitrary_M0_row": "[v w 0_Q5]",
            "reduction": ("[v w 0]-v*P^-1*[P U 0]=[0,w-v*P^-1*U,0]"),
            "only_denominator": "det(P), already certified as a global unit",
        },
        "generic_2_by_2_proxy_non_Q_residual_checks": [str(value) for value in non_q_checks],
        "generic_2_by_2_proxy_Q5_residual_check": str(q5_check),
        "conclusion": (
            "Q5-free source rows and Q5-free pivot rows imply Q5-free Schur rows "
            "on the entire declared base"
        ),
    }


def _kernel_has_nonzero_obstruction(
    matrix: sp.Matrix, obstruction_columns: tuple[int, ...]
) -> bool:
    return any(
        any(vector[column] != 0 for column in obstruction_columns) for vector in matrix.nullspace()
    )


def _pointwise_rank_contract_certificate() -> dict[str, Any]:
    non_aligned_examples = {
        "A_nonzero_rank2_safe": sp.Matrix([[1, 0], [0, 1]]),
        "A_nonzero_rank1_unsafe": sp.Matrix([[1, 1], [0, 0]]),
        "A_zero_B_rank1_safe": sp.Matrix([[0, 1], [0, 0]]),
        "A_zero_B_rank0_unsafe": sp.zeros(2, 2),
    }
    non_aligned_table = []
    for case_id, matrix in non_aligned_examples.items():
        a_nonzero = any(matrix[row, 0] != 0 for row in range(matrix.rows))
        obstruction_forced_zero = not _kernel_has_nonzero_obstruction(matrix, (1,))
        non_aligned_table.append(
            {
                "case_id": case_id,
                "A_nonzero": a_nonzero,
                "rank_T": int(matrix.rank()),
                "rank_B": int(matrix[:, 1:2].rank()),
                "w_forced_zero": obstruction_forced_zero,
            }
        )

    aligned_examples = {
        "A_nonzero_rank4_safe": sp.eye(4),
        "A_nonzero_rank3_unsafe": sp.diag(1, 1, 1, 0),
        "A_zero_B_rank3_safe": sp.Matrix([[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0]]),
        "A_zero_B_rank2_unsafe": sp.Matrix(
            [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        ),
    }
    aligned_table = []
    for case_id, matrix in aligned_examples.items():
        a_nonzero = any(matrix[row, 0] != 0 for row in range(matrix.rows))
        obstruction_forced_zero = not _kernel_has_nonzero_obstruction(matrix, (1, 2, 3))
        aligned_table.append(
            {
                "case_id": case_id,
                "A_nonzero": a_nonzero,
                "rank_T": int(matrix.rank()),
                "rank_B": int(matrix[:, 1:4].rank()),
                "w2_w3_w4_forced_zero": obstruction_forced_zero,
            }
        )

    expected_non_aligned = [
        (True, 2, 1, True),
        (True, 1, 1, False),
        (False, 1, 1, True),
        (False, 0, 0, False),
    ]
    actual_non_aligned = [
        (
            record["A_nonzero"],
            record["rank_T"],
            record["rank_B"],
            record["w_forced_zero"],
        )
        for record in non_aligned_table
    ]
    expected_aligned = [
        (True, 4, 3, True),
        (True, 3, 2, False),
        (False, 3, 3, True),
        (False, 2, 2, False),
    ]
    actual_aligned = [
        (
            record["A_nonzero"],
            record["rank_T"],
            record["rank_B"],
            record["w2_w3_w4_forced_zero"],
        )
        for record in aligned_table
    ]
    if actual_non_aligned != expected_non_aligned or actual_aligned != expected_aligned:
        raise AssertionError("the Q5-free pointwise rank equivalence changed")

    return {
        "coefficient_ring_scope": {
            "non_aligned": (
                "for chart k, R means the Eq120 chart ring S_k=R_base[g_k^-1]; "
                "over R_base, every displayed unit-ideal statement is equivalently "
                "read after saturation by g_k"
            ),
            "aligned": (
                "R means (R_base/(g2,g3,g4))[f^-1] with f=r1-1; over the "
                "unquotiented base, first add (g2,g3,g4) and then saturate by f"
            ),
        },
        "linear_algebra_truth_tables": {
            "non_aligned": non_aligned_table,
            "aligned": aligned_table,
        },
        "non_aligned_next_gate": {
            "matrix": "T=[A B] with one row for every Schur(M0) generator",
            "pointwise_equivalence": (
                "if some A_j is nonzero, w is forced to zero iff rank(T)=2; "
                "if every A_j is zero, w is forced to zero iff rank(B)=1"
            ),
            "open_conditions": ("for every j, certify (I2(T):A_j^infinity)=R on D(A_j)"),
            "closed_condition": (
                "certify <A_1,...,A_m,B_1,...,B_m>=R, equivalently B has rank one on V(A_1,...,A_m)"
            ),
            "equivalent_global_determinantal_contract": (
                "I1(T)=R and <A_1,...,A_m> is contained in sqrt(I2(T))"
            ),
            "equivalent_auxiliary_ideal_route": (
                "in R[h], certify J=<A_i*h+B_i : 1<=i<=m>=R[h]; this excludes "
                "every normalized bad solution w=1. If J_tilde is the "
                "denominator-cleared lift in R_base[h], certify equivalently "
                "(J_tilde:g_k^infinity)=R_base[h]"
            ),
            "status": "CONTRACT_ONLY_UNIT_IDEALS_NOT_COMPUTED",
        },
        "aligned_next_gate": {
            "matrix": ("T=[A B2 B3 B4], with B=[B2 B3 B4] and one row per Schur(M0) generator"),
            "pointwise_equivalence": (
                "if some A_j is nonzero, all three w coordinates are forced to zero "
                "iff rank(T)=4; if every A_j is zero, they are forced to zero iff "
                "rank(B)=3"
            ),
            "open_conditions": ("for every j, certify (I4(T):A_j^infinity)=R on D(A_j)"),
            "closed_condition": (
                "certify <A_1,...,A_m>+I3(B)=R, equivalently B has rank three on V(A_1,...,A_m)"
            ),
            "equivalent_global_determinantal_contract": (
                "I3(B)=R and <A_1,...,A_m> is contained in sqrt(I4(T))"
            ),
            "equivalent_auxiliary_ideal_route": (
                "for k=2,3,4, in R[h,w2,w3,w4] certify the ideal generated by "
                "A_i*h+B_i2*w2+B_i3*w3+B_i4*w4 and w_k-1 is the unit ideal; "
                "R is the equal-ratio quotient localized at f=r1-1"
            ),
            "status": "CONTRACT_ONLY_UNIT_IDEALS_NOT_COMPUTED",
        },
        "scout_only_row_hints": {
            "non_aligned_candidate_rows": [8, 11],
            "aligned_pure_B_candidate_rows": [8, 27, 97],
            "status": "SCOUT_ONLY_NOT_USED_BY_ANY_GATE",
        },
        "scope": (
            "these are pointwise determinantal contracts after the Q5-free lemma, "
            "not completed unit-ideal certificates and not global row-module identities"
        ),
    }


def _remainder(
    source: SparseRow,
    basis: dict[int, dict[int, Fraction]],
    variables: tuple[str, ...],
    q_variables: tuple[str, ...],
) -> SparseRow:
    positions = {variable: index for index, variable in enumerate(variables)}
    row = {positions[variable]: value for variable, value in source.items() if value}
    while row:
        pivot = min(row)
        if pivot not in basis:
            break
        scale = row[pivot]
        for column, value in basis[pivot].items():
            updated = row.get(column, Fraction(0)) - scale * value
            if updated:
                row[column] = updated
            else:
                row.pop(column, None)
    return {
        variable: row.get(positions[variable], Fraction(0))
        for variable in q_variables
        if row.get(positions[variable], Fraction(0))
    }


def _exact_point_cross_checks(
    context: torus.ScoutContext,
    operator_context: lattice.LatticeContext,
) -> dict[str, Any]:
    operator_rows, _counts = lattice._operator_lattice_rows(operator_context)
    kernel = lattice._integer_kernel_columns(operator_rows[:783], operator_context.variables)
    lower = locus.bottom_character(unit_minor.REFERENCE_COUPLINGS, unit_minor.REFERENCE_Q5)
    bottom = locus.bottom_point(context, lower)
    q_variables = tuple(torus._q_variable(context, stage) for stage in range(1, 5)) + (torus.Q5,)
    non_q = tuple(variable for variable in context.variables if variable not in q_variables)
    ordered_variables = (*non_q, *q_variables)
    records = []
    for point_id, factors in POINT_FACTORS.items():
        upper = dict(bottom)
        for column, base in factors:
            for variable_index, variable in enumerate(context.variables):
                upper[variable] *= base ** kernel[column][variable_index]
        joint, _row_counts, _commutators, _paths = torus._linear_system(context, upper, lower)
        pivot_echelon = transverse._tracked_row_echelon(
            [joint[source] for source in PIVOT_SOURCES], ordered_variables
        )
        basis = pivot_echelon["basis"]
        schur_rows = [
            _remainder(joint[source], basis, ordered_variables, q_variables)
            for source in M0_SOURCES
        ]
        m0_rank = int(
            transverse._tracked_row_echelon(
                [joint[source] for source in M0_SOURCES], context.variables
            )["rank"]
        )
        expected_rank, expected_nonzero = EXPECTED_POINT_RANK_AND_NONZERO_SCHUR_ROWS[point_id]
        record = {
            "point_id": point_id,
            "slice_factors": [
                {"kernel_column": column, "base": str(base)} for column, base in factors
            ],
            "pivot_rank": int(pivot_echelon["rank"]),
            "pivot_basis_is_exactly_the_127_non_Q_columns": set(basis) == set(range(127)),
            "M0_rank": m0_rank,
            "direct_M0_rows_with_nonzero_Q5": sum(
                bool(joint[source].get(torus.Q5, 0)) for source in M0_SOURCES
            ),
            "Schur_rows_with_nonzero_Q5": sum(bool(row.get(torus.Q5, 0)) for row in schur_rows),
            "nonzero_Schur_row_count": sum(bool(row) for row in schur_rows),
        }
        if (
            record["pivot_rank"] != 127
            or not record["pivot_basis_is_exactly_the_127_non_Q_columns"]
            or record["M0_rank"] != expected_rank
            or record["direct_M0_rows_with_nonzero_Q5"] != 0
            or record["Schur_rows_with_nonzero_Q5"] != 0
            or record["nonzero_Schur_row_count"] != expected_nonzero
        ):
            raise AssertionError(f"the exact Q5-free cross-check changed: {point_id}")
        records.append(record)
    return {
        "point_count": len(records),
        "records": records,
        "records_digest_sha256": _digest(records),
        "role": (
            "implementation cross-checks only; the global proof is the source support "
            "census plus the unit-block Schur identity"
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen_unit = _load(root / unit_minor.RESULT_PATH)
    unit_binding_passed = (
        frozen_unit.get("verdict") == unit_minor.VERDICT
        and frozen_unit.get("passed") is True
        and frozen_unit.get("semantic_digest_sha256") == EXPECTED_UNIT_MINOR_SEMANTIC_DIGEST
        and unit_minor.semantic_digest(frozen_unit) == EXPECTED_UNIT_MINOR_SEMANTIC_DIGEST
    )
    if not unit_binding_passed:
        raise AssertionError("the canonical common-core unit-minor binding failed")

    context = torus._build_context(root)
    operator_context = lattice._build_context(root)
    source_census = _source_reference_census(context)
    symbolic = _symbolic_support_certificate(context)
    schur = _schur_identity_certificate()
    pointwise_contract = _pointwise_rank_contract_certificate()
    branch_inheritance = _semantic_branch_inheritance_certificate(context)
    cross_checks = _exact_point_cross_checks(context, operator_context)

    source_maps_are_q5_free = (
        not source_census["Q5_is_an_occurrence_variable"]
        and not source_census["Q5_is_a_signature_variable"]
        and source_census["raw_CPOBC"]["references_resolving_to_Q5"] == 0
        and source_census["fixed_vector_GC"]["references_resolving_to_Q5"] == 0
        and source_census["reachable_state_MSR"]["references_resolving_to_Q5"] == 0
        and source_census["raw_CPOBC"]["operator_reference_count"] == 3061
        and source_census["fixed_vector_GC"]["path_transition_reference_count"] == 1564
        and source_census["reachable_state_MSR"]["transition_reference_count"] == 131
    )
    frozen_digests_pass = (
        symbolic["M0_source_index_digest_sha256"] == EXPECTED_M0_SOURCE_INDEX_DIGEST
        and symbolic["M0_row_label_digest_sha256"] == EXPECTED_M0_ROW_LABEL_DIGEST
        and symbolic["pivot_source_index_digest_sha256"] == EXPECTED_PIVOT_SOURCE_INDEX_DIGEST
        and symbolic["pivot_row_label_digest_sha256"] == EXPECTED_PIVOT_ROW_LABEL_DIGEST
        and symbolic["Q5_zero_ledger_digest_sha256"] == EXPECTED_Q5_ZERO_LEDGER_DIGEST
        and symbolic["full_symbolic_support_ledger_digest_sha256"]
        == EXPECTED_FULL_SYMBOLIC_SUPPORT_LEDGER_DIGEST
        and symbolic["pivot_symbolic_support_ledger_digest_sha256"]
        == EXPECTED_PIVOT_SYMBOLIC_SUPPORT_LEDGER_DIGEST
        and symbolic["block_symbolic_support_edge_counts"] == EXPECTED_BLOCK_SYMBOLIC_SUPPORT_EDGES
        and cross_checks["records_digest_sha256"] == EXPECTED_POINT_RECORDS_DIGEST
    )
    gates = {
        "canonical_unit_minor_semantic_binding_passes": unit_binding_passed,
        "source_maps_and_all_references_are_Q5_free": source_maps_are_q5_free,
        "full_M0_inventory_is_783_plus_320_plus_24": symbolic["M0_row_count"] == 1127
        and symbolic["block_row_counts"]
        == {"raw_CPOBC": 783, "fixed_vector_GC": 320, "reachable_state_MSR": 24},
        "all_frozen_source_and_zero_ledger_digests_match": frozen_digests_pass,
        "all_1127_symbolic_M0_rows_are_Q5_free": symbolic["rows_with_Q5_support_key"]
        == symbolic["rows_with_nonzero_Q5_symbolic_coefficient"]
        == 0,
        "all_127_symbolic_pivot_rows_are_Q5_free": symbolic["pivot_rows_with_Q5_support_key"]
        == symbolic["pivot_rows_with_nonzero_Q5_symbolic_coefficient"]
        == 0,
        "pivot_compiler_matches_the_full_M0_compiler": symbolic[
            "selected_pivot_rows_match_full_symbolic_compiler"
        ],
        "unit_block_Schur_identity_preserves_Q5_zero": schur[
            "generic_2_by_2_proxy_Q5_residual_check"
        ]
        == "0",
        "pointwise_rank_contract_truth_tables_are_exact": all(
            record["w_forced_zero"] == record["case_id"].endswith("_safe")
            for record in pointwise_contract["linear_algebra_truth_tables"]["non_aligned"]
        )
        and all(
            record["w2_w3_w4_forced_zero"] == record["case_id"].endswith("_safe")
            for record in pointwise_contract["linear_algebra_truth_tables"]["aligned"]
        ),
        "all_four_semantic_branches_contain_the_full_M0_core": branch_inheritance["branch_count"]
        == 4
        and all(
            branch["contains_all_1127_M0_rows_once_and_in_order"]
            for branch in branch_inheritance["branches"].values()
        ),
        "all_four_exact_implementation_cross_checks_are_Q5_free": cross_checks["point_count"] == 4
        and all(
            record["direct_M0_rows_with_nonzero_Q5"] == record["Schur_rows_with_nonzero_Q5"] == 0
            for record in cross_checks["records"]
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"common-core Q5-free gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_under_study": (
            "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON"
        ),
        "canonical_input_binding": {
            "path": unit_minor.RESULT_PATH,
            "binding_kind": "canonical_json_semantic_digest",
            "expected_semantic_digest_sha256": EXPECTED_UNIT_MINOR_SEMANTIC_DIGEST,
            "actual_semantic_digest_sha256": frozen_unit["semantic_digest_sha256"],
            "passed": unit_binding_passed,
        },
        "common_core_definition": {
            "symbol": "M0",
            "blocks": ["raw CPOBC", "fixed-vector GC", "reachable-state MSR"],
            "joint_source_intervals": ["0..782", "843..1162", "1163..1186"],
            "explicitly_excluded": ["Eq113 derived", "Eq113 literal", "Eq139"],
        },
        "source_native_Q5_census": source_census,
        "symbolic_support_certificate": symbolic,
        "global_Schur_identity_certificate": schur,
        "semantic_branch_inheritance_certificate": branch_inheritance,
        "pointwise_determinantal_next_gate_contract": pointwise_contract,
        "exact_point_cross_checks": cross_checks,
        "reduced_obligations": {
            "non_aligned": {
                "before": ["A", "B", "C_Q5"],
                "after_for_full_M0": ["A", "B"],
                "certified_identity": "C_Q5=0 for every Schur(M0) row",
            },
            "aligned": {
                "before": ["A", "B2", "B3", "B4", "C_Q5"],
                "after_for_full_M0": ["A", "B2", "B3", "B4"],
                "certified_identity": "C_Q5=0 for every aligned Schur(M0) row",
            },
            "external_Q5_direction": (
                "e_Q5 remains a free common-core cocycle direction but does not enter "
                "the Q1,...,Q4 commutators"
            ),
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "this proves only that full M0 and its globally reduced Schur rows have an "
            "identically zero external-Q5 coefficient on the declared 54-dimensional "
            "base. It proves neither the non-aligned two-column nor aligned "
            "four-column pointwise rank conditions, no global row-module membership, "
            "no witness, "
            "and no SR2-V terminal. Eq113 or Eq139 rows must be re-audited for Q5 if "
            "they are added after a common-core failure. The equal-ratio aligned "
            "remainder used in this Schur bookkeeping is not the structural "
            "ALIGNED_GLOBALLY_REDUCIBLE branch; Q5-freeness here is M0/transverse only"
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    payload = build_payload(root)
    output = root / RESULT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(payload["verdict"])
    print(payload["semantic_digest_sha256"])
    print(output)


if __name__ == "__main__":
    main()
