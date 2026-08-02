"""Global unit minor for the SR2-V weak/weak common core.

The common core consists only of raw CPOBC, fixed-vector GC and
reachable-state MSR.  In particular, neither reading of Eq. (113) nor any
Eq. (139) row is used here.

This module certifies a fixed 127 by 127 minor on all non-Q upper-right
coordinates.  After the normalized finite-CSG bottom parametrisation is
substituted, its symbolic support graph has a unique perfect matching.  Every
matched coefficient is a Laurent monomial and the determinant is therefore a
single global unit on the declared 54-dimensional transverse base.  The
remaining commutativity question is reduced, without localization, to the
five Q upper-right coordinates.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import networkx as nx
import sympy as sp

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as bottom_global
from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_transverse_common_core_unit_minor.json"
SCHEMA = "final-theory-v042-sr2v-transverse-common-core-unit-minor-v1"
VERDICT = "SR2V_TRANSVERSE_COMMON_CORE_GLOBAL_UNIT_MINOR_CERTIFIED_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_FIVE_Q_COLUMN_SCHUR_PROBLEM_REMAINS"

# Joint-inventory indices.  The selected rows use no Eq. (113) or Eq. (139).
CPOBC_ROWS = (
    0, 1, 2, 3, 4, 5, 6, 7, 17, 18, 19, 24, 25, 26, 42, 43, 44, 45,
    46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
    62, 63, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145,
    146, 203, 204, 205, 206, 215, 216, 217, 218, 223, 224, 225, 226,
    231, 232, 233, 234, 235, 236, 695, 696, 697, 698,
)
GC_OFFSETS = (0, 3, 4, 5, 6, 9, 10, 11, 17, 19, 21, 23, 26, 35, 38, 71, 74, 84, 140, 141)
MSR_OFFSETS = tuple(range(24))

EXPECTED_UPPER_EXPONENTS = (
    0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0,
    0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, -1, 1, 1, 0,
    0, 0, 2, 0, 0, -1, 0, 0, 1, 0, 6, -1, 0, 1, 0,
)
EXPECTED_LAMBDA_EXPONENTS = {
    "lambda(1,0)": -67,
    "lambda(1,1)": 58,
    "lambda(2,0)": -69,
    "lambda(2,1)": 18,
    "lambda(2,2)": 20,
    "lambda(3,0)": -51,
    "lambda(3,1)": 4,
    "lambda(3,2)": 4,
    "lambda(3,3)": 2,
}
REFERENCE_COUPLINGS = (Fraction(3), Fraction(5), Fraction(7), Fraction(11))
REFERENCE_Q5 = Fraction(13, 4)
EXPECTED_REFERENCE_DETERMINANT = -Fraction(5**28 * 7**2, 2**482 * 41**4)

SparseExprRow = dict[str, sp.Expr]
SparseRow = dict[str, Fraction]


@dataclass(frozen=True)
class SymbolicTriangular:
    upper_left: sp.Expr
    lower_right: sp.Expr
    coefficients: SparseExprRow


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


def _clean(row: dict[str, sp.Expr]) -> SparseExprRow:
    return {variable: sp.factor(value) for variable, value in row.items() if value != 0}


def _add(*rows: SparseExprRow) -> SparseExprRow:
    result: defaultdict[str, sp.Expr] = defaultdict(lambda: sp.Integer(0))
    for row in rows:
        for variable, value in row.items():
            result[variable] += value
    return _clean(dict(result))


def _scale(coefficient: sp.Expr | int, row: SparseExprRow) -> SparseExprRow:
    return _clean({variable: coefficient * value for variable, value in row.items()})


def _multiply(left: SymbolicTriangular, right: SymbolicTriangular) -> SymbolicTriangular:
    return SymbolicTriangular(
        sp.factor(left.upper_left * right.upper_left),
        sp.factor(left.lower_right * right.lower_right),
        _add(
            _scale(left.upper_left, right.coefficients),
            _scale(right.lower_right, left.coefficients),
        ),
    )


def _word(factors: Any) -> SymbolicTriangular:
    product = SymbolicTriangular(sp.Integer(1), sp.Integer(1), {})
    for factor in factors:
        product = _multiply(product, factor)
    return product


def _symbolic_selected_rows(
    context: torus.ScoutContext,
) -> tuple[list[SparseExprRow], dict[str, sp.Symbol], dict[str, sp.Symbol]]:
    """Build the fixed 127 common-core rows over independent diagonal symbols."""

    upper = {
        variable: sp.Symbol(f"a{index}") for index, variable in enumerate(context.variables)
    }
    lower = {
        variable: sp.Symbol(f"b{index}") for index, variable in enumerate(context.variables)
    }

    def matrix(variable: str) -> SymbolicTriangular:
        return SymbolicTriangular(
            upper[variable], lower[variable], {variable: sp.Integer(1)}
        )

    occurrence_matrices = {
        occurrence: matrix(context.occurrence_variables[occurrence])
        for occurrence in context.occurrence_records
    }

    def from_signature(stage: int, relation_code: int, precursor: int) -> SymbolicTriangular:
        return matrix(context.signature_variables[(stage, relation_code, precursor)])

    rows: list[SparseExprRow] = []
    wanted_cpobc = set(CPOBC_ROWS)
    raw_index = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            if raw_index in wanted_cpobc:
                operator_ids = equation["operator_ids"]
                left = _word(
                    occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"]
                )
                right = _word(
                    occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
                )
                rows.append(_add(left.coefficients, _scale(-1, right.coefficients)))
            raw_index += 1
    if raw_index != 783 or len(rows) != len(CPOBC_ROWS):
        raise AssertionError("the selected raw CPOBC inventory changed")

    path_matrices: dict[str, SymbolicTriangular] = {}
    path_records: dict[str, dict[str, Any]] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = SymbolicTriangular(sp.Integer(1), sp.Integer(1), {})
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                transition = from_signature(
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                product = _multiply(transition, product)
            path_id = str(path["path_id"])
            path_matrices[path_id] = product
            path_records[path_id] = path

    generating = context.operator_gc["generating_relation_basis"]
    for offset in GC_OFFSETS:
        relation = generating[offset]
        left = path_matrices[str(relation["lhs_path_id"])]
        right = path_matrices[str(relation["rhs_path_id"])]
        rows.append(_add(left.coefficients, _scale(-1, right.coefficients)))

    anchors: dict[str, SymbolicTriangular] = {}
    for path_id, path in sorted(path_records.items()):
        anchors.setdefault(str(path["endpoint_causet_id"]), path_matrices[path_id])
    for constraint in context.cpobc["MSR_operator_constraints"]:
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
            _add(
                _scale(residual_upper_left, state.coefficients),
                _scale(state.lower_right, _clean(dict(residual_upper))),
            )
        )
    if len(rows) != 127:
        raise AssertionError("the common-core minor no longer has 127 rows")
    return rows, upper, lower


def _bottom_formulas(
    context: torus.ScoutContext,
) -> tuple[dict[str, sp.Expr], tuple[sp.Symbol, ...], sp.Symbol]:
    t1, t2, t3, t4, q5 = sp.symbols("t1 t2 t3 t4 q5", nonzero=True)
    couplings: tuple[sp.Expr, ...] = (sp.Integer(1), t1, t2, t3, t4)
    values: dict[str, sp.Expr] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        formula = bottom_global._csg_formula(record, couplings)
        previous = values.setdefault(variable, formula)
        if sp.cancel(previous - formula) != 0:
            raise AssertionError("the symbolic CSG formula is not constant on an ON orbit")
    values[torus.Q5] = q5
    return values, (t1, t2, t3, t4), q5


def _actual_substitutions(
    context: torus.ScoutContext,
    operator_context: lattice.LatticeContext,
    upper_symbols: dict[str, sp.Symbol],
    lower_symbols: dict[str, sp.Symbol],
) -> tuple[dict[sp.Symbol, sp.Expr], list[list[int]], tuple[sp.Symbol, ...]]:
    rows, _counts = lattice._operator_lattice_rows(operator_context)
    kernel = lattice._integer_kernel_columns(rows[:783], operator_context.variables)
    if len(kernel) != 49:
        raise AssertionError("the CPOBC scalar kernel is no longer rank 49")
    bottom, _couplings, _q5 = _bottom_formulas(context)
    parameters = sp.symbols("s0:49", nonzero=True)
    substitutions: dict[sp.Symbol, sp.Expr] = {}
    for variable_index, variable in enumerate(context.variables):
        substitutions[lower_symbols[variable]] = bottom[variable]
        # The primitive kernel coordinates parametrise the upper character
        # itself.  Exact scouts based at ``a=b`` multiply these coordinates by
        # a fixed bottom-character coordinate vector, but their determinant
        # ratios have the same exponent vector.
        upper_character = sp.prod(
            parameters[column] ** kernel[column][variable_index]
            for column in range(len(kernel))
        )
        substitutions[upper_symbols[variable]] = sp.factor(upper_character)
    return substitutions, kernel, parameters


def _ordered_perfect_matching(
    support: list[list[int]],
) -> tuple[list[int], bool, int]:
    row_nodes = [f"r{row}" for row in range(len(support))]
    column_nodes = [f"c{column}" for column in range(len(support))]
    graph = nx.Graph()
    graph.add_nodes_from(row_nodes, bipartite=0)
    graph.add_nodes_from(column_nodes, bipartite=1)
    for row, columns in enumerate(support):
        for column in columns:
            graph.add_edge(row_nodes[row], column_nodes[column])
    matching = nx.algorithms.bipartite.maximum_matching(graph, top_nodes=row_nodes)
    if len(matching) // 2 != len(support):
        raise AssertionError("the symbolic support lost its perfect matching")
    selected = [int(str(matching[row_nodes[row]]).removeprefix("c")) for row in range(len(support))]

    # A perfect matching is unique iff its alternating digraph is acyclic.
    owner = {column: row for row, column in enumerate(selected)}
    alternating = nx.DiGraph()
    alternating.add_nodes_from(range(len(support)))
    for row, columns in enumerate(support):
        for column in columns:
            if column != selected[row]:
                alternating.add_edge(row, owner[column])
    unique = nx.is_directed_acyclic_graph(alternating)
    inversions = sum(
        selected[left] > selected[right]
        for left, right in itertools.combinations(range(len(selected)), 2)
    )
    return selected, unique, inversions


def _monomial_powers(
    expression: sp.Expr,
    symbols: set[sp.Symbol],
) -> tuple[sp.Expr, dict[sp.Symbol, int]]:
    powers = expression.as_powers_dict()
    exponents = {symbol: int(powers.get(symbol, 0)) for symbol in symbols if powers.get(symbol, 0)}
    coefficient = expression
    for symbol, exponent in exponents.items():
        coefficient /= symbol**exponent
    coefficient = sp.factor(coefficient)
    if coefficient.free_symbols & symbols:
        raise AssertionError("a matched coefficient is not a Laurent monomial")
    return coefficient, exponents


def _exact_determinant(rows: list[SparseRow], columns: tuple[str, ...]) -> tuple[int, Fraction]:
    positions = {variable: index for index, variable in enumerate(columns)}
    matrix = [
        {
            positions[variable]: value
            for variable, value in row.items()
            if variable in positions and value
        }
        for row in rows
    ]
    determinant = Fraction(1)
    sign = 1
    rank = 0
    for column in range(len(columns)):
        pivot = next((row for row in range(rank, len(matrix)) if matrix[row].get(column)), None)
        if pivot is None:
            continue
        if pivot != rank:
            matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
            sign *= -1
        pivot_value = matrix[rank][column]
        determinant *= pivot_value
        pivot_row = {key: value / pivot_value for key, value in matrix[rank].items()}
        for row in range(rank + 1, len(matrix)):
            scale = matrix[row].get(column, Fraction(0))
            if not scale:
                continue
            for key, value in pivot_row.items():
                updated = matrix[row].get(key, Fraction(0)) - scale * value
                if updated:
                    matrix[row][key] = updated
                else:
                    matrix[row].pop(key, None)
        rank += 1
    return rank, determinant * sign if rank == len(columns) else Fraction(0)


def unit_minor_certificate(
    root: Path,
    context: torus.ScoutContext,
    operator_context: lattice.LatticeContext,
) -> dict[str, Any]:
    rows, upper_symbols, lower_symbols = _symbolic_selected_rows(context)
    q_variables = tuple(torus._q_variable(context, stage) for stage in range(1, 5)) + (torus.Q5,)
    non_q = tuple(variable for variable in context.variables if variable not in q_variables)
    substitutions, kernel, _parameters = _actual_substitutions(
        context, operator_context, upper_symbols, lower_symbols
    )

    independent_edges = []
    actual_support: list[list[int]] = []
    vanished_edges = []
    for row_index, row in enumerate(rows):
        support_row = []
        for column_index, variable in enumerate(non_q):
            expression = row.get(variable, sp.Integer(0))
            if expression == 0:
                continue
            independent_edges.append((row_index, column_index))
            actual = sp.cancel(expression.subs(substitutions, simultaneous=True))
            if actual == 0:
                block = (
                    {"block": "CPOBC", "offset": CPOBC_ROWS[row_index]}
                    if row_index < len(CPOBC_ROWS)
                    else {
                        "block": "fixed_vector_GC",
                        "offset": GC_OFFSETS[row_index - len(CPOBC_ROWS)],
                    }
                    if row_index < len(CPOBC_ROWS) + len(GC_OFFSETS)
                    else {"block": "reachable_state_MSR", "offset": row_index - 103}
                )
                vanished_edges.append(
                    {
                        "row": row_index,
                        "column": column_index,
                        "variable": variable,
                        **block,
                        "independent_diagonal_formula": str(sp.factor(expression)),
                    }
                )
            else:
                support_row.append(column_index)
        actual_support.append(support_row)

    matching, unique, inversions = _ordered_perfect_matching(actual_support)
    symbol_set = set(upper_symbols.values()) | set(lower_symbols.values())
    coefficient = sp.Integer(-1 if inversions % 2 else 1)
    upper_variable_exponents = {variable: 0 for variable in context.variables}
    lower_variable_exponents = {variable: 0 for variable in context.variables}
    matched_records = []
    upper_lookup = {symbol: variable for variable, symbol in upper_symbols.items()}
    lower_lookup = {symbol: variable for variable, symbol in lower_symbols.items()}
    matched_types: defaultdict[str, int] = defaultdict(int)
    for row_index, column_index in enumerate(matching):
        variable = non_q[column_index]
        entry = sp.factor(rows[row_index][variable])
        entry_coefficient, entry_powers = _monomial_powers(entry, symbol_set)
        coefficient *= entry_coefficient
        if any(symbol in upper_lookup for symbol in entry_powers):
            matched_types["contains_upper_diagonal_symbols"] += 1
        elif any(symbol in lower_lookup for symbol in entry_powers):
            matched_types["bottom_only"] += 1
        else:
            matched_types["constant"] += 1
        for symbol, exponent in entry_powers.items():
            if symbol in upper_lookup:
                upper_variable_exponents[upper_lookup[symbol]] += exponent
            elif symbol in lower_lookup:
                lower_variable_exponents[lower_lookup[symbol]] += exponent
        matched_records.append(
            {
                "row": row_index,
                "column": column_index,
                "variable": variable,
                "coefficient": str(entry),
            }
        )
    coefficient = sp.factor(coefficient)

    upper_exponents = tuple(
        sum(
            kernel[column][variable_index] * upper_variable_exponents[variable]
            for variable_index, variable in enumerate(context.variables)
        )
        for column in range(len(kernel))
    )
    bottom_variable_exponents = dict(lower_variable_exponents)
    signatures = locus._variable_signatures(context)
    lambda_exponents: defaultdict[str, int] = defaultdict(int)
    q5_exponent = bottom_variable_exponents[torus.Q5]
    for variable, exponent in bottom_variable_exponents.items():
        if not exponent or variable == torus.Q5:
            continue
        stage, relation, precursor = signatures[variable]
        width, maximal = locus._shape(stage, relation, precursor)
        lambda_exponents[f"lambda({width},{maximal})"] += exponent
        lambda_exponents[f"lambda({stage},0)"] -= exponent
    lambda_exponents = defaultdict(
        int,
        {
            key: value
            for key, value in lambda_exponents.items()
            if value and key != "lambda(0,0)"
        },
    )

    lower = locus.bottom_character(REFERENCE_COUPLINGS, REFERENCE_Q5)
    upper = locus.bottom_point(context, lower)
    joint, _counts, _commutators, _paths = torus._linear_system(context, upper, lower)
    numeric_rows = (
        [joint[index] for index in CPOBC_ROWS]
        + [joint[843 + offset] for offset in GC_OFFSETS]
        + [joint[1163 + offset] for offset in MSR_OFFSETS]
    )
    reference_rank, reference_determinant = _exact_determinant(numeric_rows, non_q)

    lambda_values: dict[str, Fraction] = {}
    couplings = (Fraction(1), *REFERENCE_COUPLINGS)
    for width in range(5):
        for maximal in range(width + 1):
            lambda_values[f"lambda({width},{maximal})"] = Fraction(
                sum(
                    sp.binomial(width - maximal, index - maximal) * couplings[index]
                    for index in range(maximal, width + 1)
                )
            )
    formula_reference = Fraction(int(coefficient))
    for variable, exponent in upper_variable_exponents.items():
        formula_reference *= upper[variable] ** exponent
    for key, exponent in lambda_exponents.items():
        formula_reference *= lambda_values[key] ** exponent

    if (
        len(independent_edges) != 559
        or sum(map(len, actual_support)) != 554
        or len(vanished_edges) != 5
        or not unique
        or inversions != 3918
        or coefficient != -1
        or dict(matched_types)
        != {
            "contains_upper_diagonal_symbols": 14,
            "bottom_only": 112,
            "constant": 1,
        }
        or upper_exponents != EXPECTED_UPPER_EXPONENTS
        or dict(lambda_exponents) != EXPECTED_LAMBDA_EXPONENTS
        or q5_exponent != 0
        or reference_rank != 127
        or reference_determinant != EXPECTED_REFERENCE_DETERMINANT
        or formula_reference != reference_determinant
    ):
        raise AssertionError(
            "the common-core global unit minor certificate changed: "
            f"edges={len(independent_edges)}/{sum(map(len, actual_support))}, "
            f"vanished={len(vanished_edges)}, unique={unique}, inversions={inversions}, "
            f"coefficient={coefficient}, upper={upper_exponents}, "
            f"lambda={dict(lambda_exponents)}, q5={q5_exponent}, "
            f"reference={reference_rank}/{reference_determinant}, formula={formula_reference}"
        )

    row_selection = [
        *({"block": "CPOBC", "joint_index": index} for index in CPOBC_ROWS),
        *(
            {"block": "fixed_vector_GC", "joint_index": 843 + offset, "offset": offset}
            for offset in GC_OFFSETS
        ),
        *(
            {"block": "reachable_state_MSR", "joint_index": 1163 + offset, "offset": offset}
            for offset in MSR_OFFSETS
        ),
    ]
    return {
        "common_core": "raw CPOBC + fixed-vector GC + reachable-state MSR",
        "explicitly_excluded_blocks": ["Eq113_derived", "Eq113_literal", "Eq139"],
        "matrix_shape": [127, 127],
        "row_block_counts": {"CPOBC": 83, "fixed_vector_GC": 20, "reachable_state_MSR": 24},
        "row_selection": row_selection,
        "row_selection_digest_sha256": _digest(row_selection),
        "column_selection": list(non_q),
        "column_selection_digest_sha256": _digest(list(non_q)),
        "excluded_Q_columns": list(q_variables),
        "independent_diagonal_symbolic_support_edges": len(independent_edges),
        "CSG_base_safe_symbolic_supergraph_edges": sum(map(len, actual_support)),
        "bottom_CSG_identically_vanishing_edges": vanished_edges,
        "bottom_CSG_identically_vanishing_edge_digest_sha256": _digest(vanished_edges),
        "perfect_matching": matching,
        "perfect_matching_digest_sha256": _digest(matching),
        "perfect_matching_is_unique": unique,
        "alternating_digraph_is_acyclic": unique,
        "matching_permutation_inversions": inversions,
        "matching_permutation_is_even": inversions % 2 == 0,
        "matched_coefficient_type_counts": dict(matched_types),
        "matched_coefficient_records_digest_sha256": _digest(matched_records),
        "determinant_formula": {
            "coefficient": str(coefficient),
            "upper_torus_exponents_s0_through_s48": list(upper_exponents),
            "upper_torus_exponent_digest_sha256": _digest(list(upper_exponents)),
            "bottom_lambda_exponents": dict(lambda_exponents),
            "q5_exponent": q5_exponent,
            "display": (
                "-s7*s13*s22*s25*s28*s29*s31*s32*s36^2*s42*s44^6*s47/"
                "(s30*s39*s45) * lambda(1,1)^58*lambda(2,1)^18*"
                "lambda(2,2)^20*lambda(3,1)^4*lambda(3,2)^4*lambda(3,3)^2/"
                "(lambda(1,0)^67*lambda(2,0)^69*lambda(3,0)^51)"
            ),
            "is_a_unit_on_the_declared_base": True,
            "unit_reason": (
                "every s_j is a Laurent coordinate and every displayed lambda factor is "
                "inverted on the normalized finite-CSG principal open"
            ),
        },
        "reference_cross_check": {
            "couplings": [str(value) for value in REFERENCE_COUPLINGS],
            "q5": str(REFERENCE_Q5),
            "direct_exact_rank": reference_rank,
            "direct_exact_determinant": str(reference_determinant),
            "symbolic_unit_formula_value": str(formula_reference),
            "direct_and_symbolic_values_agree": formula_reference == reference_determinant,
        },
        "global_conclusion": (
            "the selected non-Q block is invertible at every point of the full "
            "54-dimensional transverse base; the common-core kernel has dimension at most "
            "five and is determined by its Q1,...,Q5 coordinates"
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen_lattice = _load(root / lattice.RESULT_PATH)
    frozen_bottom = _load(root / bottom_global.RESULT_PATH)
    if (
        frozen_lattice.get("verdict") != lattice.VERDICT
        or frozen_lattice.get("semantic_digest_sha256") != lattice.semantic_digest(frozen_lattice)
        or frozen_bottom.get("verdict") != bottom_global.VERDICT
        or frozen_bottom.get("semantic_digest_sha256")
        != bottom_global.semantic_digest(frozen_bottom)
    ):
        raise AssertionError("a frozen scalar-base predecessor binding failed")
    context = torus._build_context(root)
    operator_context = lattice._build_context(root)
    certificate = unit_minor_certificate(root, context, operator_context)
    gates = {
        "common_core_uses_no_Eq113_or_Eq139_rows": {
            record["block"] for record in certificate["row_selection"]
        }
        == {"CPOBC", "fixed_vector_GC", "reachable_state_MSR"},
        "fixed_non_Q_minor_is_127_by_127": certificate["matrix_shape"] == [127, 127],
        "CSG_support_has_a_unique_perfect_matching": certificate[
            "perfect_matching_is_unique"
        ],
        "the_five_extra_independent_bottom_edges_vanish_identically": len(
            certificate["bottom_CSG_identically_vanishing_edges"]
        )
        == 5,
        "determinant_is_a_global_localized_unit": certificate["determinant_formula"][
            "is_a_unit_on_the_declared_base"
        ],
        "direct_reference_determinant_matches_the_symbolic_formula": certificate[
            "reference_cross_check"
        ]["direct_and_symbolic_values_agree"],
    }
    if not all(gates.values()):
        raise AssertionError(f"common-core unit-minor gate failed: {gates}")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_under_study": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: {
                "raw_sha256": _sha256(root / relative),
                "semantic_digest_sha256": _load(root / relative).get("semantic_digest_sha256"),
            }
            for relative in (lattice.RESULT_PATH, bottom_global.RESULT_PATH)
        },
        "unit_minor_certificate": certificate,
        "next_gate": {
            "ambient_columns_after_global_elimination": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "task": (
                "compute the common-core Schur row module on these five columns and prove "
                "that it contains the three globally minimal star commutator rows"
            ),
            "branch_count_if_common_core_succeeds": 0,
            "why": "Eq113 and Eq139 were not used in the globally invertible block",
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "this proves a global rank-127 common-core minor and a lossless five-Q-column "
            "reduction; it does not yet prove that the three star commutator rows lie in "
            "the remaining Schur row module and therefore does not issue an SR2-V terminal"
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    payload = build_payload(root)
    output = root / RESULT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["verdict"])
    print(payload["semantic_digest_sha256"])
    print(output)


if __name__ == "__main__":
    main()
