"""Exact raw-CPOBC audit of the SR2-V variable-harmonic sparse section.

The preceding two-row audit exhibited a root-zero harmonic coordinate ``k``
and solved two selected raw scalar rows after setting every beta to one and
leaving only two alpha coordinates nonzero.  This module first substitutes
that exact assignment into all 783 raw CPOBC operator equations.  It then
audits the corresponding two-alpha principal-open section symbolically.

Only exact sparse polynomial arithmetic over ``QQ`` and exact Gaussian
elimination are used.  Eq. (113) literal/derived branches and Eq. (139)
strict/completed domains remain separate and are not compiled here.  The
result is deliberately nonterminal for the full SR2-V search.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from universe_lab.final_theory import sr2v_variable_harmonic_two_row_audit_v042 as base

RESULT_PATH = "results/v0.4.2_sr2v_variable_harmonic_sparse_section_cpobc.json"
PREDECESSOR_PATH = "results/v0.4.2_sr2v_variable_harmonic_two_row_audit.json"

SCHEMA = "final-theory-v042-sr2v-variable-harmonic-sparse-section-cpobc-v1"
VERDICT = (
    "SR2V_VARIABLE_HARMONIC_TWO_ALPHA_PRINCIPAL_OPEN_CPOBC_"
    "UNIT_IDEAL_CERTIFIED_NONTERMINAL"
)
SEARCH_TERMINAL = "NOT_AN_SR2V_SEARCH_TERMINAL_SPARSE_SECTION_ONLY"

PINNED_INPUT_SHA256 = {
    **base.PINNED_INPUT_SHA256,
    PREDECESSOR_PATH: "481f7430adb807fc39405c183febdbc48d45e1f29fc4da8857b7d136e68c7163",
}
PINNED_PREDECESSOR_SEMANTIC_DIGEST = (
    "64a79807b4a19169517c5a9864b005c38a44593118987ed88e95dd2edb9cb84e"
)

EXPECTED_PIVOT_MINOR_DETERMINANT = (
    120710493008090868612664506823005578612575380982477722717033332736
)
EXPECTED_PIVOT_MINOR_FACTORIZATION = {"2": 192, "3": 9, "977": 1}

X_NAME = f"alpha:{base.ALPHA_E_ORBIT}"
Y_NAME = f"alpha:{base.BETA_V_ORBIT}"

Monomial = tuple[str, ...]
Polynomial = dict[Monomial, Fraction]
Matrix = tuple[tuple[Polynomial, Polynomial], tuple[Polynomial, Polynomial]]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON object required: {path}")
    return payload


def _records_digest(records: Any) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def _degree_census(polynomial: Polynomial) -> dict[str, Any]:
    degrees = [len(monomial) for monomial in polynomial]
    return {
        "term_count": len(polynomial),
        "minimum_total_degree": min(degrees, default=0),
        "maximum_total_degree": max(degrees, default=0),
        "constant_coefficient": str(polynomial.get((), Fraction(0))),
    }


def _find_equation(cpobc: dict[str, Any], relation_id: str, equation_id: str) -> dict[str, Any]:
    relation = next(
        relation for relation in cpobc["relations"] if relation["relation_id"] == relation_id
    )
    return next(
        equation
        for equation in relation["raw_noncommutative_relation"]
        if equation["equation_id"] == equation_id
    )


def _equation_residual(
    equation: dict[str, Any], occurrence_matrices: dict[str, Matrix]
) -> Matrix:
    operator_ids = equation["operator_ids"]
    lhs = base._matrix_word(
        [occurrence_matrices[str(operator_ids[token])] for token in equation["lhs_word"]]
    )
    rhs = base._matrix_word(
        [occurrence_matrices[str(operator_ids[token])] for token in equation["rhs_word"]]
    )
    return base._matrix_subtract(lhs, rhs)


def _escape_data(
    context: dict[str, Any], h: dict[str, Fraction]
) -> dict[str, Any]:
    terminals = sorted(
        endpoint
        for endpoint, stage in context["endpoint_stages"].items()
        if stage == 5
    )
    weights = base._root_weights(context)
    first = min(terminals, key=lambda endpoint: (weights[endpoint], endpoint))
    second = max(terminals, key=lambda endpoint: (weights[endpoint], endpoint))
    boundary = base._boundary_vector(
        terminals,
        first,
        weights[second],
        second,
        -weights[first],
    )
    k = base._harmonic_extension(context, boundary)
    if (first, weights[first], second, weights[second]) != (
        "p5-0000000",
        1,
        "p5-000008c",
        25,
    ):
        raise AssertionError("escape boundary support changed")
    if k["p1-0"] or base._harmonic_failures(context, k):
        raise AssertionError("escape k is not root-zero harmonic")
    if not any(
        h[left] * k[right] - k[left] * h[right]
        for left in terminals
        for right in terminals
    ):
        raise AssertionError("escape state assignment is not rank two")
    return {
        "terminals": terminals,
        "weights": weights,
        "first": first,
        "second": second,
        "boundary": boundary,
        "k": k,
    }


def _numeric_occurrence_matrices(
    context: dict[str, Any],
    h: dict[str, Fraction],
    k: dict[str, Fraction],
    values: dict[str, Fraction],
) -> dict[str, Matrix]:
    matrices: dict[str, Matrix] = {}
    for occurrence_id, orbit in context["occurrence_orbits"].items():
        edge = context["edges"][orbit]
        symbolic = base._state_native_matrix(
            (h[edge["source"]], k[edge["source"]]),
            (h[edge["target"]], k[edge["target"]]),
            orbit,
        )
        matrices[occurrence_id] = cast(
            Matrix,
            tuple(
                tuple(
                    base._constant(base._evaluate(symbolic[row][column], values))
                    for column in range(2)
                )
                for row in range(2)
            ),
        )
    return matrices


def _direct_point_census(
    cpobc: dict[str, Any], occurrence_matrices: dict[str, Matrix]
) -> dict[str, Any]:
    nonzero_records: list[dict[str, Any]] = []
    operator_equations_with_residual: set[tuple[str, str]] = set()
    entry_counter: Counter[str] = Counter()
    equation_counter: Counter[str] = Counter()
    operator_equation_count = 0
    for relation in cpobc["relations"]:
        relation_id = str(relation["relation_id"])
        for equation in relation["raw_noncommutative_relation"]:
            operator_equation_count += 1
            equation_id = str(equation["equation_id"])
            residual = _equation_residual(equation, occurrence_matrices)
            for row in range(2):
                for column in range(2):
                    polynomial = residual[row][column]
                    if not polynomial:
                        continue
                    if set(polynomial) != {()}:
                        raise AssertionError("numeric substitution left a symbolic variable")
                    value = polynomial[()]
                    nonzero_records.append(
                        {
                            "relation_id": relation_id,
                            "equation_id": equation_id,
                            "entry": [row, column],
                            "value": str(value),
                            "lhs_word_length": len(equation["lhs_word"]),
                            "rhs_word_length": len(equation["rhs_word"]),
                        }
                    )
                    operator_equations_with_residual.add((relation_id, equation_id))
                    entry_counter[f"{row},{column}"] += 1
                    equation_counter[equation_id] += 1
    scalar_entry_count = 4 * operator_equation_count
    return {
        "operator_equation_count": operator_equation_count,
        "scalar_entry_count": scalar_entry_count,
        "zero_scalar_entries": scalar_entry_count - len(nonzero_records),
        "nonzero_scalar_entries": len(nonzero_records),
        "operator_equations_with_nonzero_residual": len(operator_equations_with_residual),
        "operator_equations_vanishing_completely": (
            operator_equation_count - len(operator_equations_with_residual)
        ),
        "relations_with_nonzero_residual": len(
            {record["relation_id"] for record in nonzero_records}
        ),
        "nonzero_entry_census": dict(sorted(entry_counter.items())),
        "nonzero_equation_id_census": dict(sorted(equation_counter.items())),
        "nonzero_records": nonzero_records,
        "nonzero_records_digest_sha256": _records_digest(nonzero_records),
    }


def _root_zero_symbolic_harmonic(
    context: dict[str, Any], terminals: list[str], weights: dict[str, int]
) -> dict[str, Any]:
    reference = terminals[0]
    if weights[reference] != 1:
        raise AssertionError("root-zero coordinate chart expects a unit reference weight")
    free_terminals = terminals[1:]
    boundary: dict[str, Polynomial] = {
        terminal: base._variable(f"z:{terminal}") for terminal in free_terminals
    }
    boundary[reference] = {}
    for terminal in free_terminals:
        boundary[reference] = base._add(
            boundary[reference],
            base._scale(-Fraction(weights[terminal]), boundary[terminal]),
        )
    k = dict(boundary)
    for stage in range(4, 0, -1):
        for source in sorted(
            endpoint
            for endpoint in context["outgoing"]
            if context["endpoint_stages"][endpoint] == stage
        ):
            value: Polynomial = {}
            for term in context["outgoing"][source]:
                value = base._add(
                    value,
                    base._scale(
                        Fraction(term["multiplicity"]), k[term["target"]]
                    ),
                )
            k[source] = value
    if k["p1-0"]:
        raise AssertionError("symbolic harmonic chart is not root zero")
    return {
        "reference_terminal": reference,
        "free_terminals": free_terminals,
        "variable_order": [f"z:{terminal}" for terminal in free_terminals],
        "boundary": boundary,
        "k": k,
    }


def _alpha_zero_occurrence_matrices(
    context: dict[str, Any],
    h: dict[str, Fraction],
    k: dict[str, Polynomial],
) -> dict[str, Matrix]:
    matrices: dict[str, Matrix] = {}
    for occurrence_id, orbit in context["occurrence_orbits"].items():
        edge = context["edges"][orbit]
        source = edge["source"]
        target = edge["target"]
        h_source = h[source]
        h_target = h[target]
        bottom_left = base._scale(
            Fraction(1, 1) / h_source,
            base._subtract(k[target], k[source]),
        )
        matrices[occurrence_id] = (
            (base._constant(h_target / h_source), {}),
            (bottom_left, base._constant(1)),
        )
    return matrices


def _two_alpha_occurrence_matrices(
    context: dict[str, Any],
    h: dict[str, Fraction],
    k: dict[str, Polynomial],
) -> dict[str, Matrix]:
    replacements: dict[str, Polynomial] = {}
    for orbit in context["edges"]:
        replacements[f"beta:{orbit}"] = base._constant(1)
        replacements[f"alpha:{orbit}"] = {}
    replacements[X_NAME] = base._variable(X_NAME)
    replacements[Y_NAME] = base._variable(Y_NAME)

    matrices: dict[str, Matrix] = {}
    for occurrence_id, orbit in context["occurrence_orbits"].items():
        edge = context["edges"][orbit]
        symbolic = base._state_native_matrix_polynomial(
            h[edge["source"]],
            h[edge["target"]],
            k[edge["source"]],
            k[edge["target"]],
            orbit,
        )
        matrices[occurrence_id] = cast(
            Matrix,
            tuple(
                tuple(
                    base._substitute(symbolic[row][column], replacements)
                    for column in range(2)
                )
                for row in range(2)
            ),
        )
    return matrices


def _linear_coefficients(
    polynomial: Polynomial, variable_index: dict[str, int]
) -> dict[int, Fraction]:
    result: dict[int, Fraction] = {}
    for monomial, coefficient in polynomial.items():
        if len(monomial) != 1 or monomial[0] not in variable_index:
            raise AssertionError("expected a homogeneous root-kernel linear form")
        result[variable_index[monomial[0]]] = coefficient
    return result


def _permutation_sign(values: list[int]) -> int:
    inversions = sum(
        values[left] > values[right]
        for left in range(len(values))
        for right in range(left + 1, len(values))
    )
    return -1 if inversions % 2 else 1


def _alpha_zero_rank_certificate(
    cpobc: dict[str, Any],
    occurrence_matrices: dict[str, Matrix],
    variable_order: list[str],
) -> dict[str, Any]:
    variable_index = {variable: index for index, variable in enumerate(variable_order)}
    basis: dict[int, dict[int, Fraction]] = {}
    selected_rows: list[dict[str, Any]] = []
    selected_original_coefficients: list[dict[int, Fraction]] = []
    pivot_order: list[int] = []
    pivot_values: list[Fraction] = []
    nonzero_records: list[dict[str, Any]] = []
    scalar_entry_count = 0

    for relation in cpobc["relations"]:
        relation_id = str(relation["relation_id"])
        for equation in relation["raw_noncommutative_relation"]:
            equation_id = str(equation["equation_id"])
            residual = _equation_residual(equation, occurrence_matrices)
            for row in range(2):
                for column in range(2):
                    scalar_entry_count += 1
                    polynomial = residual[row][column]
                    if not polynomial:
                        continue
                    record = {
                        "relation_id": relation_id,
                        "equation_id": equation_id,
                        "entry": [row, column],
                        "polynomial": base._serialize_polynomial(polynomial),
                    }
                    nonzero_records.append(record)
                    original = _linear_coefficients(polynomial, variable_index)
                    reduced = dict(original)
                    while reduced:
                        pivot = min(reduced)
                        if pivot not in basis:
                            pivot_value = reduced[pivot]
                            basis[pivot] = {
                                index: coefficient / pivot_value
                                for index, coefficient in reduced.items()
                            }
                            pivot_order.append(pivot)
                            pivot_values.append(pivot_value)
                            selected_original_coefficients.append(original)
                            selected_rows.append(
                                {
                                    **record,
                                    "pivot_coordinate": variable_order[pivot],
                                    "pivot_value_after_previous_eliminations": str(
                                        pivot_value
                                    ),
                                }
                            )
                            break
                        factor = reduced[pivot]
                        for index, coefficient in basis[pivot].items():
                            updated = reduced.get(index, Fraction(0)) - factor * coefficient
                            if updated:
                                reduced[index] = updated
                            else:
                                reduced.pop(index, None)

    if len(basis) != len(variable_order):
        raise AssertionError("alpha-zero CPOBC linear system is not full rank")
    if set(pivot_order) != set(range(len(variable_order))):
        raise AssertionError("pivot coordinate coverage changed")
    determinant = Fraction(_permutation_sign(pivot_order))
    for pivot_value in pivot_values:
        determinant *= pivot_value
    if determinant.denominator != 1:
        raise AssertionError("expected an integral pivot-minor determinant")
    if determinant.numerator != EXPECTED_PIVOT_MINOR_DETERMINANT:
        raise AssertionError("rank-certificate determinant changed")

    coefficient_matrix = [
        [str(row.get(column, Fraction(0))) for column in range(len(variable_order))]
        for row in selected_original_coefficients
    ]
    return {
        "specialization": "all beta=1 and all alpha=0",
        "scalar_entry_count": scalar_entry_count,
        "zero_scalar_entries": scalar_entry_count - len(nonzero_records),
        "nonzero_scalar_entries": len(nonzero_records),
        "all_nonzero_entries_are_entry_1_0": all(
            record["entry"] == [1, 0] for record in nonzero_records
        ),
        "all_nonzero_entries_are_homogeneous_linear": True,
        "nonzero_records_digest_sha256": _records_digest(nonzero_records),
        "root_kernel_variable_count": len(variable_order),
        "linear_rank": len(basis),
        "nullity": len(variable_order) - len(basis),
        "rank_is_maximal": len(basis) == len(variable_order),
        "selected_row_count": len(selected_rows),
        "selected_row_count_is_rank_optimal": len(selected_rows) == len(variable_order),
        "variable_order": variable_order,
        "variable_order_digest_sha256": _records_digest(variable_order),
        "pivot_order": pivot_order,
        "pivot_order_variables": [variable_order[index] for index in pivot_order],
        "pivot_values": [str(value) for value in pivot_values],
        "selected_rows": selected_rows,
        "selected_rows_digest_sha256": _records_digest(selected_rows),
        "selected_coefficient_matrix": coefficient_matrix,
        "selected_coefficient_matrix_digest_sha256": _records_digest(
            coefficient_matrix
        ),
        "selected_minor_determinant": str(determinant),
        "selected_minor_factorization": EXPECTED_PIVOT_MINOR_FACTORIZATION,
        "conclusion": "the only root-zero harmonic k is k=0",
    }


def _evaluate_at_escape(
    polynomial: Polynomial,
    coordinate_chart: dict[str, Any],
    escape: dict[str, Any],
    *,
    x: Fraction = Fraction(0),
    y: Fraction = Fraction(0),
) -> Fraction:
    values = {
        variable: escape["boundary"][terminal]
        for variable, terminal in zip(
            coordinate_chart["variable_order"],
            coordinate_chart["free_terminals"],
            strict=True,
        )
    }
    values[X_NAME] = x
    values[Y_NAME] = y
    return base._evaluate(polynomial, values)


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_hashes = {path: _sha256(root / path) for path in PINNED_INPUT_SHA256}
    if input_hashes != PINNED_INPUT_SHA256:
        changed = sorted(
            path for path, digest in input_hashes.items() if digest != PINNED_INPUT_SHA256[path]
        )
        raise AssertionError(f"pinned sparse-section input changed: {changed}")

    predecessor = _load(root / PREDECESSOR_PATH)
    if (
        predecessor.get("semantic_digest_sha256")
        != PINNED_PREDECESSOR_SEMANTIC_DIGEST
        or predecessor.get("passed") is not True
    ):
        raise AssertionError("predecessor two-row certificate changed")

    cpobc = _load(root / base.CPOBC_PATH)
    reduction = _load(root / base.REDUCTION_PATH)
    gc = _load(root / base.GC_PATH)
    eq112 = _load(root / base.EQ112_PATH)
    weak = _load(root / base.WEAK_D2_PATH)
    context = base._build_context(cpobc, reduction)
    path_data = base._path_product_h(gc, context)
    h: dict[str, Fraction] = path_data["h"]
    escape = _escape_data(context, h)

    point_values = base._all_variable_values(context)
    point_values[X_NAME] = Fraction(5, 524)
    point_values[Y_NAME] = Fraction(-179, 6)
    point_matrices = _numeric_occurrence_matrices(
        context, h, escape["k"], point_values
    )
    point_census = _direct_point_census(cpobc, point_matrices)

    first_obstruction = point_census["nonzero_records"][0]
    if first_obstruction != {
        "relation_id": "cpobc-relation-0b2bbe81c6394d603f63",
        "equation_id": "eq103",
        "entry": [1, 0],
        "value": "-89/4",
        "lhs_word_length": 2,
        "rhs_word_length": 2,
    }:
        raise AssertionError("first raw-order point obstruction changed")

    f_point = next(
        record
        for record in point_census["nonzero_records"]
        if record["relation_id"] == base.F_RELATION
        and record["equation_id"] == base.EQUATION
        and record["entry"] == [0, 0]
    )
    if f_point["value"] != "-5/2096":
        raise AssertionError("selected-equation point obstruction changed")

    coordinate_chart = _root_zero_symbolic_harmonic(
        context, escape["terminals"], escape["weights"]
    )
    k_polynomial: dict[str, Polynomial] = coordinate_chart["k"]
    two_alpha_matrices = _two_alpha_occurrence_matrices(context, h, k_polynomial)
    f_equation = _find_equation(cpobc, base.F_RELATION, base.EQUATION)
    g_equation = _find_equation(cpobc, base.G_RELATION, base.EQUATION)
    f_residual = _equation_residual(f_equation, two_alpha_matrices)
    g_residual = _equation_residual(g_equation, two_alpha_matrices)

    expected_f_top_right = base._scale(Fraction(-1, 128), base._variable(X_NAME))
    expected_g_top_right = base._scale(Fraction(7, 8192), base._variable(Y_NAME))
    if f_residual[0][1] != expected_f_top_right:
        raise AssertionError("f top-right alpha-killer changed")
    if g_residual[0][1] != expected_g_top_right:
        raise AssertionError("g top-right alpha-killer changed")

    f_constant, f_coefficient = base._split_affine_coefficient(
        f_residual[1][0], X_NAME
    )
    g_constant, g_coefficient = base._split_affine_coefficient(
        g_residual[1][0], Y_NAME
    )
    forbidden_in_f = {
        variable
        for monomial in f_residual[1][0]
        for variable in monomial
        if variable == Y_NAME
    }
    forbidden_in_g = {
        variable
        for monomial in g_residual[1][0]
        for variable in monomial
        if variable == X_NAME
    }
    if forbidden_in_f or forbidden_in_g:
        raise AssertionError("two rational solve variables are no longer disjoint")

    section_evaluations = {
        "F0_escape": _evaluate_at_escape(f_constant, coordinate_chart, escape),
        "Cf_escape": _evaluate_at_escape(f_coefficient, coordinate_chart, escape),
        "G0_escape": _evaluate_at_escape(g_constant, coordinate_chart, escape),
        "Cg_escape": _evaluate_at_escape(g_coefficient, coordinate_chart, escape),
    }
    section_evaluations["Delta_escape"] = (
        section_evaluations["Cf_escape"] * section_evaluations["Cg_escape"]
    )
    if section_evaluations != {
        "F0_escape": Fraction(-5, 8),
        "Cf_escape": Fraction(131, 2),
        "G0_escape": Fraction(-179, 2),
        "Cg_escape": Fraction(-3),
        "Delta_escape": Fraction(-393, 2),
    }:
        raise AssertionError("two-row rational-section coefficients changed")
    delta_constant = f_coefficient.get((), Fraction(0)) * g_coefficient.get(
        (), Fraction(0)
    )
    if delta_constant:
        raise AssertionError("Delta must vanish at the rank-one origin k=0")

    alpha_zero_matrices = _alpha_zero_occurrence_matrices(
        context, h, k_polynomial
    )
    zero_alpha_replacements: dict[str, Polynomial] = {X_NAME: {}, Y_NAME: {}}
    two_alpha_to_zero_reduction_failures = [
        occurrence_id
        for occurrence_id in sorted(two_alpha_matrices)
        if cast(
            Matrix,
            tuple(
                tuple(
                    base._substitute(
                        two_alpha_matrices[occurrence_id][row][column],
                        zero_alpha_replacements,
                    )
                    for column in range(2)
                )
                for row in range(2)
            ),
        )
        != alpha_zero_matrices[occurrence_id]
    ]
    if two_alpha_to_zero_reduction_failures:
        raise AssertionError("two-alpha matrices do not reduce to the alpha-zero chart")
    rank_certificate = _alpha_zero_rank_certificate(
        cpobc, alpha_zero_matrices, coordinate_chart["variable_order"]
    )
    supplemental = base._supplemental_ledgers(eq112, weak)

    selected_f_value = _evaluate_at_escape(
        f_residual[1][0],
        coordinate_chart,
        escape,
        x=Fraction(5, 524),
        y=Fraction(-179, 6),
    )
    selected_g_value = _evaluate_at_escape(
        g_residual[1][0],
        coordinate_chart,
        escape,
        x=Fraction(5, 524),
        y=Fraction(-179, 6),
    )

    gates = {
        "all_six_input_SHA256_bindings_hold": input_hashes == PINNED_INPUT_SHA256,
        "predecessor_semantic_digest_is_pinned": (
            predecessor["semantic_digest_sha256"]
            == PINNED_PREDECESSOR_SEMANTIC_DIGEST
        ),
        "escape_assignment_solves_the_predecessor_two_selected_rows": (
            selected_f_value == 0 and selected_g_value == 0
        ),
        "all_783_raw_CPOBC_equations_were_directly_substituted": (
            point_census["operator_equation_count"] == 783
            and point_census["scalar_entry_count"] == 3132
        ),
        "escape_assignment_is_not_a_full_CPOBC_point": (
            point_census["nonzero_scalar_entries"] == 911
            and point_census["zero_scalar_entries"] == 2221
        ),
        "two_additional_top_right_rows_kill_both_selected_alphas": (
            f_residual[0][1] == expected_f_top_right
            and g_residual[0][1] == expected_g_top_right
        ),
        "two_alpha_chart_reduces_exactly_to_the_alpha_zero_linear_chart": (
            not two_alpha_to_zero_reduction_failures
        ),
        "alpha_zero_beta_one_root_kernel_system_has_exact_full_rank": (
            rank_certificate["linear_rank"] == 62
            and rank_certificate["nullity"] == 0
            and rank_certificate["selected_minor_determinant"]
            == str(EXPECTED_PIVOT_MINOR_DETERMINANT)
        ),
        "Delta_is_nonzero_somewhere_but_vanishes_at_the_forced_origin": (
            section_evaluations["Delta_escape"] != 0
            and delta_constant == 0
        ),
        "Delta_principal_open_lies_in_the_rank_two_state_locus": (
            h["p1-0"] == 1
            and not k_polynomial["p1-0"]
            and bool(f_coefficient)
            and bool(g_coefficient)
            and all(len(monomial) == 2 for monomial in f_coefficient)
            and all(len(monomial) == 2 for monomial in g_coefficient)
            and section_evaluations["Delta_escape"] != 0
        ),
        "Eq113_and_Eq139_semantic_branches_remain_separate": supplemental["Eq113"][
            "branches_kept_separate"
        ]
        and supplemental["Eq139"]["domains_kept_separate"],
    }
    if not all(gates.values()):
        failed = sorted(name for name, passed in gates.items() if not passed)
        raise AssertionError(f"sparse-section CPOBC gate failed: {failed}")

    nonzero_records = point_census.pop("nonzero_records")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_slice": (
            "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON__"
            "normalized_CSG_primary_h__variable_root_zero_harmonic_k__"
            "all_beta_one__two_selected_alpha_support"
        ),
        "input_artifacts": input_hashes,
        "predecessor_binding": {
            "path": PREDECESSOR_PATH,
            "semantic_digest_sha256": PINNED_PREDECESSOR_SEMANTIC_DIGEST,
            "predecessor_verdict": predecessor["verdict"],
        },
        "escape_point_full_raw_substitution": {
            "boundary_support": {
                escape["first"]: str(escape["boundary"][escape["first"]]),
                escape["second"]: str(escape["boundary"][escape["second"]]),
            },
            "assignment": {
                "all_beta": "1",
                "all_unlisted_alpha": "0",
                X_NAME: "5/524",
                Y_NAME: "-179/6",
            },
            "selected_f_entry_1_0_value": str(selected_f_value),
            "selected_g_entry_1_0_value": str(selected_g_value),
            **point_census,
            "nonzero_records": nonzero_records,
            "first_nonzero_in_raw_ledger_order": first_obstruction,
            "first_additional_entry_in_selected_f_equation": f_point,
            "point_unit_identity": (
                "1=(-2096/5)*R_f[0,0], because R_f[0,0]=-5/2096"
            ),
            "classification": "NOT_A_FULL_RAW_CPOBC_POINT",
        },
        "root_zero_harmonic_coordinate_chart": {
            "reference_terminal": coordinate_chart["reference_terminal"],
            "reference_boundary_formula": (
                "k(reference)=-sum_T root_weight(T)*z_T"
            ),
            "free_terminal_coordinate_count": len(
                coordinate_chart["free_terminals"]
            ),
            "variable_order": coordinate_chart["variable_order"],
            "variable_order_digest_sha256": _records_digest(
                coordinate_chart["variable_order"]
            ),
            "root_value": "0",
            "harmonic_extension": "exact backward triangular recurrence",
        },
        "two_alpha_principal_open_section": {
            "specialization": (
                "all beta=1; all alpha=0 except x=alpha_E and y=alpha_V"
            ),
            "x": X_NAME,
            "y": Y_NAME,
            "selected_row_equations": [
                "F0(k)+Cf(k)*x=0",
                "G0(k)+Cg(k)*y=0",
            ],
            "principal_open_polynomial": "Delta(k)=Cf(k)*Cg(k)",
            "rational_section": "x=-F0/Cf, y=-G0/Cg on Delta!=0",
            "rank_two_open_check": {
                "h_root": "1",
                "k_root": "0",
                "Delta_has_positive_homogeneous_degree": 4,
                "Delta_nonzero_implies_k_nonzero": True,
                "nonzero_root_zero_k_cannot_be_proportional_to_h": True,
                "conclusion": "Delta!=0 lies in the rank-two state locus",
            },
            "F0": base._serialize_polynomial(f_constant),
            "Cf": base._serialize_polynomial(f_coefficient),
            "G0": base._serialize_polynomial(g_constant),
            "Cg": base._serialize_polynomial(g_coefficient),
            "Delta": {
                "factorization": "Cf*Cg",
                "expanded": False,
                "reason_not_expanded": (
                    "the exact factored representation is smaller and sufficient"
                ),
            },
            "polynomial_records_digest_sha256": _records_digest(
                {
                    "F0": base._serialize_polynomial(f_constant),
                    "Cf": base._serialize_polynomial(f_coefficient),
                    "G0": base._serialize_polynomial(g_constant),
                    "Cg": base._serialize_polynomial(g_coefficient),
                    "Delta": "Cf*Cg",
                }
            ),
            "degree_census": {
                "F0": _degree_census(f_constant),
                "Cf": _degree_census(f_coefficient),
                "G0": _degree_census(g_constant),
                "Cg": _degree_census(g_coefficient),
                "Delta": {
                    "representation": "factored_Cf_times_Cg",
                    "minimum_total_degree": 4,
                    "maximum_total_degree": 4,
                    "constant_coefficient": "0",
                },
            },
            "escape_evaluation": {
                key: str(value) for key, value in section_evaluations.items()
            },
            "additional_raw_rows": {
                "f_entry_0_1": {
                    "relation_id": base.F_RELATION,
                    "equation_id": base.EQUATION,
                    "entry": [0, 1],
                    "polynomial": base._serialize_polynomial(f_residual[0][1]),
                    "formula": "-x/128",
                },
                "g_entry_0_1": {
                    "relation_id": base.G_RELATION,
                    "equation_id": base.EQUATION,
                    "entry": [0, 1],
                    "polynomial": base._serialize_polynomial(g_residual[0][1]),
                    "formula": "7*y/8192",
                },
                "consequence_over_Q": "raw CPOBC forces x=y=0",
            },
            "alpha_zero_matrix_reduction_failures": (
                two_alpha_to_zero_reduction_failures
            ),
        },
        "rank_optimal_linear_manifest": rank_certificate,
        "localized_unit_ideal_certificate": {
            "ring": "Q[z_1,...,z_62,x,y,tau]",
            "localizer": "tau*Delta(k)-1",
            "raw_generators_used": (
                "two top-right alpha-killers and 62 rank-optimal raw rows"
            ),
            "raw_generator_count_upper_bound": 64,
            "proof_steps": [
                "R_f[0,1]=-x/128 and R_g[0,1]=7*y/8192 put x,y in I.",
                (
                    "Modulo (x,y), the selected 62 raw rows are homogeneous linear "
                    "forms L_i(k) with the displayed nonzero determinant."
                ),
                "Therefore (L_1,...,L_62)=(z_1,...,z_62) and every z_j lies in I.",
                "Delta has zero constant term, hence Delta lies in (z_1,...,z_62) subset I.",
                "Together with tau*Delta-1, this gives 1 in I.",
            ],
            "selected_minor_determinant": rank_certificate[
                "selected_minor_determinant"
            ],
            "selected_minor_factorization": EXPECTED_PIVOT_MINOR_FACTORIZATION,
            "conclusion": (
                "the Delta!=0 two-alpha sparse section has empty raw-CPOBC locus"
            ),
            "includes_the_predecessor_rational_section": True,
        },
        "separate_unresolved_ledgers": supplemental,
        "scope_exclusions": {
            "beta_variables_beyond_beta_one": "UNRESOLVED",
            "other_129_alpha_coordinates": "UNRESOLVED",
            "other_normalized_primary_h": "UNRESOLVED",
            "full_CSG_h_fixed_P61_family": "NOT_CLASSIFIED",
            "all_rank2_state_assignments_Gr2_63_open": "NOT_COVERED",
            "supplemental_Q5": "UNRESOLVED_NOT_COMPILED",
            "Eq113_both_branches": "UNRESOLVED_NOT_COMPILED",
            "Eq139_both_domains": "UNRESOLVED_NOT_COMPILED",
            "commutativity_or_noncommutativity": "NOT_DECIDED",
            "SR2V_terminal_verdict": False,
        },
        "execution": {
            "solver": "NOT_RUN",
            "groebner": "NOT_RUN",
            "sage": "NOT_INVOKED",
            "finite_field": "NOT_RUN",
            "numerical": "NOT_RUN",
            "arithmetic": "EXACT_QQ_SPARSE_SYMBOLIC_AND_GAUSSIAN_ELIMINATION_ONLY",
        },
        "gates": gates,
        "passed": True,
        "verdict": VERDICT,
        "search_terminal": SEARCH_TERMINAL,
        "claim_boundary": (
            "The exact escape assignment solves the predecessor's two selected scalar "
            "rows but fails 911 of all 3,132 raw CPOBC scalar entries. More strongly, "
            "the entire Delta-nonzero beta=1 section with only those two alpha "
            "coordinates has unit raw-CPOBC ideal. This closes only that sparse "
            "section and is not a full SR2-V classification."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
