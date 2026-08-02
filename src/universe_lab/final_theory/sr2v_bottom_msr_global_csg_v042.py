"""Global exact classification of the SR2-V bottom-scalar MSR locus.

The primitive scalar-lattice certificate identifies the observed diagonal
character with a split ``G_m^29``.  This module substitutes that Laurent map
into all 24 source-matched additive MSR equations and proves that the resulting
system is globally triangular on the torus.  Its solution is a smooth
five-dimensional principal open: four normalized finite-CSG coupling
coordinates and the cutoff-external ``Q5`` factor.

This supersedes the *local-classification boundary* of
``sr2v_additive_msr_laurent_v042``.  It does not supersede that artifact's
independent rational-point and Jacobian regression data.  The upper operator
character ``G_m^49``, the upper-right cocycle fibre, and all commutator opens
remain separate problems.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

RESULT_PATH = "results/v0.4.2_sr2v_bottom_msr_global_csg.json"
LOCAL_CERTIFICATE_PATH = "results/v0.4.2_sr2v_additive_msr_laurent.json"

SCHEMA = "final-theory-v042-sr2v-bottom-msr-global-csg-v1"
VERDICT = "SR2V_BOTTOM_MSR_GLOBAL_CSG_PARAMETERISATION_CERTIFIED_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_BOTTOM_SCALAR_PROJECTION_ONLY"

PIVOT_INDICES = (
    24,
    22,
    20,
    11,
    19,
    16,
    15,
    27,
    0,
    4,
    17,
    10,
    2,
    8,
    12,
    9,
    6,
    23,
    7,
    13,
    14,
    5,
    1,
    3,
)
FREE_INDICES = (18, 21, 25, 26, 28)
ACTUAL_FREE_INDICES = FREE_INDICES[:-1]

Exponent = tuple[int, ...]
LaurentPolynomial = dict[Exponent, Fraction]
LabelledEquation = tuple[str, str, LaurentPolynomial]


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


def _fraction(value: sp.Expr) -> Fraction:
    rational = sp.Rational(value)
    return Fraction(int(rational.p), int(rational.q))


def _kernel_matrix(payload: dict[str, Any]) -> sp.Matrix:
    columns = payload["observed_bottom_plus_fixed_GC_block"]["integer_kernel"][
        "basis_columns"
    ]
    matrix = sp.Matrix.hstack(*(sp.Matrix(column) for column in columns))
    if matrix.shape != (132, 29) or matrix.rank() != 29:
        raise AssertionError("the primitive bottom scalar kernel changed")
    return matrix


def _compile_equations(
    context: lattice.LatticeContext,
    kernel: sp.Matrix,
) -> list[LabelledEquation]:
    positions = {variable: index for index, variable in enumerate(context.variables)}
    zero = (0,) * kernel.cols
    equations: list[LabelledEquation] = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        polynomial: defaultdict[Exponent, Fraction] = defaultdict(Fraction)
        polynomial[zero] += Fraction(int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            variable = context.occurrence_variables[str(term["transition_id"])]
            row = positions[variable]
            exponent = tuple(int(kernel[row, column]) for column in range(kernel.cols))
            polynomial[exponent] += Fraction(int(term["coefficient"]))
        equations.append(
            (
                str(constraint["constraint_id"]),
                str(constraint["source_id"]),
                {exponent: value for exponent, value in polynomial.items() if value},
            )
        )
    if len(equations) != 24:
        raise AssertionError("the source-matched additive MSR inventory changed")
    return equations


def _serialize_laurent(polynomial: LaurentPolynomial) -> list[dict[str, Any]]:
    return [
        {"coefficient": str(coefficient), "exponents": list(exponent)}
        for exponent, coefficient in sorted(polynomial.items())
    ]


def _clear_laurent(polynomial: LaurentPolynomial) -> tuple[Exponent, LaurentPolynomial]:
    shift = tuple(
        max(0, -min(exponent[index] for exponent in polynomial))
        for index in range(len(next(iter(polynomial))))
    )
    cleared = {
        tuple(exponent[index] + shift[index] for index in range(len(shift))): coefficient
        for exponent, coefficient in polynomial.items()
    }
    return shift, {exponent: value for exponent, value in cleared.items() if value}


def _sympy_polynomial(polynomial: LaurentPolynomial, symbols: tuple[sp.Symbol, ...]) -> sp.Expr:
    return sp.Add(
        *(
            sp.Rational(coefficient.numerator, coefficient.denominator)
            * sp.prod(symbol**power for symbol, power in zip(symbols, exponent, strict=True))
            for exponent, coefficient in polynomial.items()
        )
    )


def _expression_record(expression: sp.Expr, symbols: tuple[sp.Symbol, ...]) -> dict[str, Any]:
    numerator, denominator = sp.fraction(sp.factor(expression))
    return {
        "display": str(sp.factor(expression)),
        "numerator": str(numerator),
        "denominator": str(denominator),
        "free_coordinates": [
            str(symbol) for symbol in symbols if symbol in expression.free_symbols
        ],
        "operation_count": int(sp.count_ops(expression)),
    }


def _free_original_rows(
    context: lattice.LatticeContext,
    operator_rows: list[lattice.LabelledRow],
    fixed_gc_rows: list[lattice.LabelledRow],
) -> tuple[int, ...]:
    echelon = lattice._row_echelon([*operator_rows, *fixed_gc_rows], context.variables)
    free = tuple(index for index in range(len(context.variables)) if index not in echelon)
    if len(free) != 29:
        raise AssertionError("the bottom scalar lattice free-coordinate count changed")
    return free


def _triangular_certificate(
    equations: list[LabelledEquation],
    symbols: tuple[sp.Symbol, ...],
) -> tuple[dict[sp.Symbol, sp.Expr], dict[str, Any]]:
    cleared_expressions = []
    for _, _, polynomial in equations:
        _, cleared = _clear_laurent(polynomial)
        cleared_expressions.append(sp.factor(_sympy_polynomial(cleared, symbols)))

    pivots = tuple(symbols[index] for index in PIVOT_INDICES)
    free_symbols = tuple(symbols[index] for index in FREE_INDICES)
    solutions: dict[sp.Symbol, sp.Expr] = {}
    records: list[dict[str, Any]] = []
    sequential_reduced_coefficients: list[sp.Expr] = []

    for equation_index, ((constraint_id, source_id, _), pivot) in enumerate(
        zip(equations, pivots, strict=True)
    ):
        reduced = sp.factor(cleared_expressions[equation_index].subs(solutions))
        future = set(pivots[equation_index + 1 :])
        if reduced.free_symbols & future:
            raise AssertionError("the proposed MSR ordering is not triangular")
        if sp.degree(reduced, pivot) != 1:
            raise AssertionError("an MSR pivot equation is not linear")
        coefficient = sp.factor(sp.diff(reduced, pivot))
        remainder = sp.factor(reduced.subs(pivot, 0))
        if pivot in coefficient.free_symbols or pivot in remainder.free_symbols:
            raise AssertionError("the displayed pivot extraction failed")
        solution = sp.factor(sp.cancel(-remainder / coefficient))
        if solution.free_symbols - set(free_symbols):
            raise AssertionError("a solved coordinate still depends on a pivot")
        solutions[pivot] = solution
        sequential_reduced_coefficients.append(coefficient)

        if equation_index == 0:
            unit_reason = (
                "equation rewrites coefficient*s24=s25*s26; both the pivot and "
                "right side are torus units"
            )
        elif equation_index == 1:
            unit_reason = (
                "equation rewrites coefficient*s22=s18*s21; both the pivot and "
                "right side are torus units"
            )
        elif equation_index == 2:
            unit_reason = (
                "the preceding p2-0 equation forces the displayed denominator "
                "to be a quotient-ring unit; the remaining factors are Laurent units"
            )
        else:
            unit_reason = "the pivot coefficient is a Laurent monomial unit"
        records.append(
            {
                "order": equation_index,
                "constraint_id": constraint_id,
                "source_id": source_id,
                "pivot_index": PIVOT_INDICES[equation_index],
                "pivot_coordinate": str(pivot),
                "reduced_cleared_equation": str(reduced),
                "pivot_coefficient": str(coefficient),
                "right_side": str(-remainder),
                "solution": _expression_record(solution, symbols),
                "coefficient_is_forced_nonzero_on_torus_solutions": True,
                "unit_reason": unit_reason,
            }
        )

    if set(solutions) != set(pivots):
        raise AssertionError("the triangular solve did not cover all 24 pivots")
    if any(sp.cancel(expression.subs(solutions)) != 0 for expression in cleared_expressions):
        raise AssertionError("the triangular formula does not solve all 24 equations")

    jacobian = sp.Matrix(
        [
            [sp.diff(expression, pivot) for pivot in pivots]
            for expression in cleared_expressions
        ]
    )
    if any(jacobian[row, column] != 0 for row in range(24) for column in range(row + 1, 24)):
        raise AssertionError("the pivot Jacobian is not lower triangular")
    determinant = sp.factor(jacobian.det())
    expected_determinant = sp.factor(
        symbols[18] ** 21
        * symbols[22]
        * symbols[26]
        * (symbols[18] * symbols[21] + symbols[25] * symbols[26])
        * (
            symbols[18] * symbols[21]
            + symbols[18] * symbols[26]
            + 2 * symbols[25] * symbols[26]
        )
    )
    if determinant != expected_determinant:
        raise AssertionError("the global pivot-Jacobian determinant changed")
    quotient_unit = sp.factor(
        symbols[18] ** 22
        * symbols[21]
        * symbols[25]
        * symbols[26] ** 2
        / symbols[24]
    )
    if sp.cancel(determinant.subs(solutions) - quotient_unit.subs(solutions)) != 0:
        raise AssertionError("the pivot determinant is not the claimed quotient unit")

    certificate = {
        "pivot_indices": list(PIVOT_INDICES),
        "pivot_coordinates": [str(symbol) for symbol in pivots],
        "free_indices": list(FREE_INDICES),
        "free_coordinates": [str(symbol) for symbol in free_symbols],
        "actual_edge_free_coordinates": [
            str(symbols[index]) for index in ACTUAL_FREE_INDICES
        ],
        "cutoff_external_free_coordinate": str(symbols[FREE_INDICES[-1]]),
        "records": records,
        "all_24_back_substitutions_are_zero": True,
        "pivot_jacobian": {
            "shape": [jacobian.rows, jacobian.cols],
            "strictly_above_diagonal_is_zero": True,
            "diagonal": [str(jacobian[index, index]) for index in range(24)],
            "sequential_reduced_pivot_coefficients": [
                str(value) for value in sequential_reduced_coefficients
            ],
            "determinant": str(determinant),
            "quotient_ring_unit_form": str(quotient_unit),
            "rank_on_every_torus_solution": 24,
        },
    }
    certificate["records_digest_sha256"] = _digest(records)
    return solutions, certificate


def _lambda_polynomial(
    width: int,
    maximal: int,
    couplings: tuple[sp.Expr, ...],
) -> sp.Expr:
    return sp.factor(
        sum(
            sp.Integer(comb(width - maximal, index - maximal)) * couplings[index]
            for index in range(maximal, width + 1)
        )
    )


def _csg_formula(
    record: dict[str, Any],
    couplings: tuple[sp.Expr, ...],
) -> sp.Expr:
    stage = int(record["stage"])
    precursor = int(record["precursor_code"])
    relation = tuple(int(row) for row in record["source_relation_rows"])
    width = precursor.bit_count()
    maximal = len(maximal_elements_in_subset(relation, precursor))
    denominator = _lambda_polynomial(stage, 0, couplings)
    return sp.factor(_lambda_polynomial(width, maximal, couplings) / denominator)


def _evaluate_monomial_row(
    row: lattice.SparseIntegerRow,
    values: dict[str, sp.Expr],
) -> sp.Expr:
    product = sp.prod(
        values[variable] ** exponent for variable, exponent in row.items()
    )
    return sp.cancel(product - 1)


def _csg_certificate(
    context: lattice.LatticeContext,
    kernel: sp.Matrix,
    free_rows: tuple[int, ...],
    equations: list[LabelledEquation],
    solutions: dict[sp.Symbol, sp.Expr],
    symbols: tuple[sp.Symbol, ...],
    operator_rows: list[lattice.LabelledRow],
    fixed_gc_rows: list[lattice.LabelledRow],
) -> dict[str, Any]:
    t1, t2, t3, t4, q5 = sp.symbols("t1 t2 t3 t4 q5")
    couplings: tuple[sp.Expr, ...] = (sp.Integer(1), t1, t2, t3, t4)

    records_by_variable: dict[str, dict[str, Any]] = {}
    values: dict[str, sp.Expr] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        formula = _csg_formula(record, couplings)
        if variable in values and sp.cancel(values[variable] - formula) != 0:
            raise AssertionError("the CSG formula is not constant on an ON orbit")
        values[variable] = formula
        records_by_variable.setdefault(variable, record)
    values[lattice.Q5] = q5

    monomial_failures = [
        label
        for label, row in [*operator_rows, *fixed_gc_rows]
        if _evaluate_monomial_row(row, values) != 0
    ]
    if monomial_failures:
        raise AssertionError("the finite CSG family violates the bottom monomial lattice")

    msr_failures = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        residual = sp.Integer(int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            variable = context.occurrence_variables[str(term["transition_id"])]
            residual += int(term["coefficient"]) * values[variable]
        if sp.cancel(residual) != 0:
            msr_failures.append(str(constraint["constraint_id"]))
    if msr_failures:
        raise AssertionError("the finite CSG family violates additive MSR")

    torus_from_couplings = tuple(values[context.variables[row]] for row in free_rows)
    if len(torus_from_couplings) != 29 or torus_from_couplings[-1] != q5:
        raise AssertionError("the CSG-to-Laurent coordinate map changed")

    positions = {variable: index for index, variable in enumerate(context.variables)}
    coordinate_failures = []
    coordinate_records = []
    for variable in context.variables:
        row = positions[variable]
        reconstructed = sp.factor(
            sp.prod(
                torus_from_couplings[column] ** int(kernel[row, column])
                for column in range(kernel.cols)
            )
        )
        if sp.cancel(reconstructed - values[variable]) != 0:
            coordinate_failures.append(variable)
        coordinate_records.append(
            {
                "variable": variable,
                "formula": str(values[variable]),
                "laurent_reconstruction": str(reconstructed),
            }
        )
    if coordinate_failures:
        raise AssertionError("the primitive Laurent map does not reproduce all CSG coordinates")

    r, u, v, w = (symbols[index] for index in ACTUAL_FREE_INDICES)
    inverse = {
        t1: sp.factor(v * w / (r * u)),
        t2: sp.factor(w / u),
        t3: sp.factor(-(r * u + 3 * r * w + 3 * v * w - w) / (r * u)),
        t4: sp.factor((3 * r * u + 6 * r * w + r + 8 * v * w - 4 * w) / (r * u)),
        q5: symbols[28],
    }
    forward_free = {
        symbols[index]: torus_from_couplings[index] for index in FREE_INDICES
    }
    if any(
        sp.cancel(expression.subs(forward_free) - parameter) != 0
        for parameter, expression in inverse.items()
    ):
        raise AssertionError("the displayed CSG inverse is not a left inverse")
    if any(
        sp.cancel(torus_from_couplings[index].subs(inverse) - symbols[index]) != 0
        for index in FREE_INDICES
    ):
        raise AssertionError("the displayed CSG inverse is not a right inverse")

    if any(
        sp.cancel(torus_from_couplings[index].subs(inverse) - symbols[index]) != 0
        for index in ACTUAL_FREE_INDICES
    ):
        raise AssertionError("the four selected Laurent coordinates are not independent")

    lambda_factors = [
        _lambda_polynomial(width, maximal, couplings)
        for width in range(5)
        for maximal in range(width + 1)
    ]
    nontrivial_lambda_factors = sorted(
        {str(sp.factor(value)) for value in lambda_factors if value != 1}
    )
    domain_product = sp.factor(sp.prod(lambda_factors) * q5)

    # The triangular solution and the CSG map agree because they have the same
    # four free coordinates and both solve the globally unique pivot system.
    triangular_csg_failures = []
    for pivot, solution in solutions.items():
        expected = torus_from_couplings[int(str(pivot).removeprefix("s"))]
        if sp.cancel(solution.subs(forward_free) - expected) != 0:
            triangular_csg_failures.append(str(pivot))
    if triangular_csg_failures:
        raise AssertionError("the triangular and CSG parameterisations disagree")

    unique_actual_formulas = {str(value) for key, value in values.items() if key != lattice.Q5}
    certificate = {
        "normalisation": "t0=1",
        "coupling_parameters": ["t1", "t2", "t3", "t4"],
        "cutoff_external_parameter": "q5",
        "lambda_formula": (
            "lambda(width,maximal)=sum_{k=maximal}^width "
            "binomial(width-maximal,k-maximal)*t_k"
        ),
        "transition_formula": "b_e=lambda(width(e),maximal(e))/lambda(stage(e),0)",
        "parameter_domain": {
            "description": (
                "principal open where q5 and every lambda(width,maximal), "
                "0<=maximal<=width<=4, are nonzero"
            ),
            "nontrivial_lambda_factors": nontrivial_lambda_factors,
            "localising_product": str(domain_product),
        },
        "forward_map_to_selected_laurent_coordinates": {
            str(symbols[index]): str(torus_from_couplings[index])
            for index in FREE_INDICES
        },
        "inverse_map": {
            str(parameter): str(expression) for parameter, expression in inverse.items()
        },
        "direct_symbolic_checks": {
            "operator_monomial_rows": len(operator_rows),
            "fixed_vector_GC_monomial_rows": len(fixed_gc_rows),
            "combined_monomial_rows": len(operator_rows) + len(fixed_gc_rows),
            "monomial_failures": monomial_failures,
            "additive_MSR_rows": len(equations),
            "additive_MSR_failures": msr_failures,
            "primitive_Laurent_coordinates_reconstructed": len(context.variables),
            "coordinate_failures": coordinate_failures,
            "actual_transition_coordinates_matching_CSG": len(context.variables) - 1,
            "distinct_actual_transition_formulas": len(unique_actual_formulas),
            "triangular_CSG_failures": triangular_csg_failures,
        },
        "all_132_coordinate_identities_digest_sha256": _digest(coordinate_records),
        "classification": (
            "the full nonzero bottom-MSR Laurent locus is isomorphic to the declared "
            "normalized finite-CSG principal open times G_m(q5)"
        ),
        "scheme_properties": {
            "dimension": 5,
            "codimension_inside_Gm29": 24,
            "smooth": True,
            "irreducible": True,
            "rational": True,
        },
    }
    certificate["parameterisation_digest_sha256"] = _digest(certificate)
    return certificate


def build_payload(root: Path) -> dict[str, Any]:
    """Rebuild the global bottom-scalar MSR/CSG classification."""

    root = root.resolve()
    frozen_lattice = _load(root / lattice.RESULT_PATH)
    if (
        frozen_lattice.get("verdict") != lattice.VERDICT
        or frozen_lattice.get("passed") is not True
        or frozen_lattice.get("semantic_digest_sha256")
        != lattice.semantic_digest(frozen_lattice)
        or frozen_lattice != lattice.build_payload(root)
    ):
        raise AssertionError("the frozen primitive scalar-lattice binding failed")

    context = lattice._build_context(root)
    if tuple(frozen_lattice["variable_namespace"]["ordered_variables"]) != context.variables:
        raise AssertionError("the scalar-lattice variable order changed")
    kernel = _kernel_matrix(frozen_lattice)
    operator_rows, relation_scope = lattice._operator_lattice_rows(context)
    fixed_gc_rows = lattice._fixed_gc_rows(context)
    free_rows = _free_original_rows(context, operator_rows, fixed_gc_rows)
    for column, row in enumerate(free_rows):
        if any(kernel[row, index] != int(index == column) for index in range(kernel.cols)):
            raise AssertionError("the displayed torus coordinate is not the expected free row")

    symbols = tuple(sp.symbols("s0:29"))
    equations = _compile_equations(context, kernel)
    solutions, triangular = _triangular_certificate(equations, symbols)
    csg = _csg_certificate(
        context,
        kernel,
        free_rows,
        equations,
        solutions,
        symbols,
        operator_rows,
        fixed_gc_rows,
    )

    equation_records = []
    term_counts = []
    degrees = []
    support_counts = []
    all_exponents: list[int] = []
    for constraint_id, source_id, polynomial in equations:
        shift, cleared = _clear_laurent(polynomial)
        term_counts.append(len(polynomial))
        degrees.append(max(sum(exponent) for exponent in cleared))
        support = {
            index
            for exponent in polynomial
            for index, value in enumerate(exponent)
            if value
        }
        support_counts.append(len(support))
        all_exponents.extend(value for exponent in polynomial for value in exponent)
        equation_records.append(
            {
                "constraint_id": constraint_id,
                "source_id": source_id,
                "laurent_terms": _serialize_laurent(polynomial),
                "clearing_shift": list(shift),
                "cleared_terms": _serialize_laurent(cleared),
                "laurent_term_count": len(polynomial),
                "cleared_total_degree": max(sum(exponent) for exponent in cleared),
                "parameter_support_count": len(support),
            }
        )

    stage_counts = Counter(source.split("-", maxsplit=1)[0] for _, source, _ in equations)
    degree_counts = Counter(degrees)
    term_histogram = Counter(term_counts)
    q5_absent = all(
        exponent[28] == 0 for _, _, polynomial in equations for exponent in polynomial
    )
    system_digest = _digest(
        [
            [constraint_id, source_id, _serialize_laurent(polynomial)]
            for constraint_id, source_id, polynomial in equations
        ]
    )
    cleared_digest = _digest(
        [
            [constraint_id, _serialize_laurent(_clear_laurent(polynomial)[1])]
            for constraint_id, _, polynomial in equations
        ]
    )
    distinct_equation_count = len(
        {
            _canonical_json(_serialize_laurent(polynomial))
            for _, _, polynomial in equations
        }
    )

    gates = {
        "bound_bottom_locus_is_primitive_Gm29": kernel.shape == (132, 29),
        "all_24_source_MSR_equations_are_distinct_and_nonzero": len(equations) == 24
        and distinct_equation_count == 24
        and all(polynomial for _, _, polynomial in equations),
        "source_stage_census_is_1_2_5_16": dict(sorted(stage_counts.items()))
        == {"p1": 1, "p2": 2, "p3": 5, "p4": 16},
        "Laurent_term_census_is_145": sum(term_counts) == 145,
        "cleared_degree_census_is_3_cubic_21_quadratic": dict(sorted(degree_counts.items()))
        == {2: 21, 3: 3},
        "Laurent_exponents_are_only_minus1_0_1": min(all_exponents) == -1
        and max(all_exponents) == 1,
        "each_equation_has_at_most_8_terms_and_8_parameters": max(term_counts) == 8
        and max(support_counts) == 8,
        "cutoff_external_Q5_is_absent": q5_absent,
        "triangular_partition_is_24_plus_5": sorted(PIVOT_INDICES + FREE_INDICES)
        == list(range(29)),
        "all_triangular_back_substitutions_vanish": triangular[
            "all_24_back_substitutions_are_zero"
        ],
        "pivot_Jacobian_rank_is_globally_24": triangular["pivot_jacobian"][
            "rank_on_every_torus_solution"
        ]
        == 24,
        "finite_CSG_parameterisation_and_inverse_are_exact": not csg[
            "direct_symbolic_checks"
        ]["coordinate_failures"]
        and not csg["direct_symbolic_checks"]["triangular_CSG_failures"],
        "all_1163_monomial_and_24_additive_rows_hold_symbolically": csg[
            "direct_symbolic_checks"
        ]["combined_monomial_rows"]
        == 1163
        and not csg["direct_symbolic_checks"]["monomial_failures"]
        and not csg["direct_symbolic_checks"]["additive_MSR_failures"],
        "global_locus_is_smooth_irreducible_rational_dimension_5": csg[
            "scheme_properties"
        ]
        == {
            "dimension": 5,
            "codimension_inside_Gm29": 24,
            "smooth": True,
            "irreducible": True,
            "rational": True,
        },
    }
    if not all(gates.values()):
        raise AssertionError(f"global bottom-MSR classification gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "finite_scope": "n<=4",
        "dimension": 2,
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "field": {
            "coefficient_field": "QQ",
            "exponent_lattice": "ZZ",
            "symbolic_ring": "QQ Laurent/rational function arithmetic",
            "floating_point_used": False,
            "finite_field_used": False,
            "groebner_used": False,
        },
        "input_artifacts": {
            lattice.RESULT_PATH: {
                "raw_sha256": _sha256(root / lattice.RESULT_PATH),
                "semantic_digest_sha256": frozen_lattice["semantic_digest_sha256"],
            },
            lattice.CPOBC_PATH: {"raw_sha256": _sha256(root / lattice.CPOBC_PATH)},
            lattice.REDUCTION_PATH: {"raw_sha256": _sha256(root / lattice.REDUCTION_PATH)},
        },
        "laurent_map": {
            "ambient_locus": "observed-bottom plus fixed-vector-GC split G_m^29",
            "kernel_shape": [kernel.rows, kernel.cols],
            "coordinate_names": [str(symbol) for symbol in symbols],
            "free_original_row_indices": list(free_rows),
            "free_original_variables": [context.variables[index] for index in free_rows],
            "map": "b_i=product_j s_j^K_ij",
            "operator_Gm49_role": (
                "separate upper diagonal character; reachable-state MSR does not impose "
                "these 24 standalone equations on it"
            ),
        },
        "additive_MSR_system": {
            "raw_coordinate_form": "-1+sum_e multiplicity(c,e)*b_e=0",
            "laurent_coordinate_form": "24 Laurent polynomials after b_i=product_j s_j^K_ij",
            "equation_count": len(equations),
            "source_stage_counts": dict(sorted(stage_counts.items())),
            "all_equations_distinct": distinct_equation_count == 24,
            "identically_zero_equations": [],
            "Q5_coordinate_occurs": not q5_absent,
            "laurent_term_count": sum(term_counts),
            "term_count_histogram": {
                str(key): value for key, value in sorted(term_histogram.items())
            },
            "exponent_range": [min(all_exponents), max(all_exponents)],
            "maximum_parameter_support_per_equation": max(support_counts),
            "cleared_degree_histogram": {
                str(key): value for key, value in sorted(degree_counts.items())
            },
            "system_digest_sha256": system_digest,
            "cleared_system_digest_sha256": cleared_digest,
            "equations": equation_records,
        },
        "global_triangular_classification": triangular,
        "finite_CSG_identification": csg,
        "supersession": {
            "local_certificate": LOCAL_CERTIFICATE_PATH,
            "superseded_boundary": "global_additive_MSR_variety_classified=False",
            "preserved_local_results": [
                "normalized exact CSG point",
                "logarithmic Jacobian rank 24",
                "selected minor -5/2^45",
                "local tangent decomposition 4+Q5",
            ],
            "new_global_result": (
                "the entire nonzero bottom-scalar Laurent locus is classified and "
                "identified with the normalized finite-CSG principal open times G_m(Q5)"
            ),
        },
        "resource_and_claim_boundaries": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "sage_status": "NOT_INVOKED",
            "global_bottom_scalar_locus_classified": True,
            "upper_operator_Gm49_classified_beyond_monomial_lattice": False,
            "upper_right_cocycle_fibre_solved": False,
            "commutator_principal_open_tested": False,
            "state_native_D12_manifest_modified_or_used": False,
            "next_exact_gate": (
                "form the transverse scalar base G_m^49 times this five-dimensional "
                "bottom locus, then analyse the 1187-by-132 homogeneous cocycle system; "
                "keep pair-irreducible D12 work separate"
            ),
        },
        "relation_scope": {
            "CPOBC": relation_scope["CPOBC"],
            "Eq113_branches_kept_separate": relation_scope["Eq113"],
            "Eq139_domains_kept_separate": relation_scope["Eq139"],
            "fixed_vector_GC_basis": len(fixed_gc_rows),
            "reachable_state_MSR_sources": len(equations),
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "This exact certificate globally classifies only the nonzero observed-bottom "
            "scalar projection in the transverse reducible ON chart.  It proves that the "
            "24 additive reachable-MSR equations cut the primitive G_m^29 locus down to "
            "the smooth rational normalized finite-CSG principal open times the independent "
            "cutoff-external Q5 factor.  It does not constrain the separate upper G_m^49 "
            "character by strong MSR, solve the upper-right cocycle fibre, meet a commutator "
            "open, decide the pair-irreducible D12 branch, produce a witness or obstruction "
            "for the full weak/weak profile, or issue an SR2-V terminal."
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
