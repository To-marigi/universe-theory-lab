"""Phase-A compiler and resource checkpoint for the SR2-V Q5-free campaign.

This module performs no Sage, Singular, Groebner-basis, saturation, or
unit-ideal calculation.  It independently rebuilds the 1,127 common-core
source rows, reconstructs the certified 127 pivot rows, performs exact Schur
elimination over a sparse localized representation and is intended to freeze
the six auxiliary-ideal inputs required by the execution plan.  The bounded
full run did not finish, so ``main`` emits the nonterminal resource checkpoint;
``build_payload`` remains the incomplete-duration full compiler entry point.

The two sampled row sets ``(8, 11)`` and ``(8, 27, 97)`` are retained only as
scout metadata.  They do not replace the complete 1,127-row manifests and are
not consumed by any terminal gate.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import networkx as nx
import sympy as sp
from sympy.matrices.normalforms import smith_normal_form
from sympy.polys.domains import QQ, ZZ
from sympy.polys.fields import FracElement, field
from sympy.polys.rings import PolyElement

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as bottom_global
from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import sr2v_transverse_common_core_q5_free_v042 as q5_free
from universe_lab.final_theory import sr2v_transverse_common_core_unit_minor_v042 as unit_minor
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import (
    sr2v_transverse_eq120_schur_chart_obligations_v042 as obligations,
)
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_manifest.json"
REPORT_PATH = "reports/v0.4.2_sr2v_q5_free_auxiliary_ideal_manifest.md"
PLAN_PATH = "reports/v0.4.2_sr2v_q5_free_auxiliary_ideal_execution_plan.md"

SCHEMA = "final-theory-v042-sr2v-q5-free-auxiliary-ideal-manifest-v2"
VERDICT = "SR2V_Q5_FREE_AUXILIARY_IDEAL_FULL_MANIFEST_READY_NO_SOLVER_RUN"
OPEN_VERDICT = "SR2V_Q5_FREE_AUXILIARY_IDEAL_MANIFEST_OPEN_RESOURCE_LIMIT_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_NO_GROEBNER_OR_UNIT_IDEAL_CERTIFICATE"
ACTIVE_RING = "R52=QQ[t1,t2,t3,t4,s0,...,s47][(F_lambda*product(s0,...,s47))^-1]"

EXPECTED_PREDECESSORS = {
    bottom_global.RESULT_PATH: "d7978cac841bf725baa03df99aa661183a5c96367a2979b245b978f7d5dd08a4",
    unit_minor.RESULT_PATH: "286b2c8e0329dd585c33dee13c66e3a923a270d04822f3489186aad4ee1e45ac",
    q5_free.RESULT_PATH: "d19b01460604c647dc290143bf3a5aba2986bc9e6be235fd1ebae3a7702c25a3",
    obligations.RESULT_PATH: "c040fa5f4a1542becf5ba4579a2cefb5b0f224b910da1ec2da42bb77df44d644",
}

M0_SOURCES = q5_free.M0_SOURCES
PIVOT_SOURCES = q5_free.PIVOT_SOURCES
NON_ALIGNED_SCOUT_ROWS = (8, 11)
ALIGNED_SCOUT_ROWS = (8, 27, 97)

FullExponent = tuple[int, ...]
T_SYMBOLS = sp.symbols("t1:5")
BOTTOM_Q5_SYMBOL = sp.Symbol("bottom_q5")

#: Every Laurent coefficient produced by this compiler is an element of the
#: rational function field ``QQ(t1,t2,t3,t4)``.  Representing it as a sparse
#: ``FracElement`` instead of a generic ``sp.Expr`` keeps each value in reduced
#: form by construction, so the per-operation ``sp.cancel`` that dominated the
#: bounded Phase-A attempt is no longer needed anywhere.
COEFFICIENT_FIELD = field("t1,t2,t3,t4", QQ)[0]
COEFFICIENT_RING = COEFFICIENT_FIELD.ring
COEFFICIENT_ZERO = COEFFICIENT_FIELD.zero
COEFFICIENT_ONE = COEFFICIENT_FIELD.one

#: ``FracElement`` carries no static type information, so the alias documents the
#: intent while remaining ``Any`` to the type checker.
type Coefficient = Any
LaurentPolynomial = dict[FullExponent, Coefficient]
FractionPolynomial = dict[FullExponent, Fraction]
SymbolicRow = dict[str, sp.Expr]
BaseRow = dict[str, LaurentPolynomial]


#: Optional observer invoked once per compiled row.  It receives the stage name,
#: the number of rows finished, the total, and the digest that pins the row, so a
#: long Phase-A run can be followed and, on a rerun, checked row by row instead of
#: only at the end.
ProgressCallback = Callable[[str, int, int, str], None] | None


def _progress_reporter(progress: ProgressCallback) -> Callable[[str, int, int, str], None]:
    if progress is None:
        return lambda _stage, _done, _total, _digest: None
    return progress


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _digest_canonical_json(canonical: str) -> str:
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest(value: Any) -> str:
    return _digest_canonical_json(_canonical_json(value))


def semantic_digest(payload: dict[str, Any]) -> str:
    return _digest(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _normalised_text_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _serial_fraction(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _serial_exponent(exponent: FullExponent) -> list[list[int]]:
    return [[index, value] for index, value in enumerate(exponent) if value]


def _serial_ring_polynomial(polynomial: PolyElement) -> list[list[Any]]:
    return [
        [
            _serial_exponent(tuple(int(value) for value in monomial)),
            int(QQ.numer(coefficient)),
            int(QQ.denom(coefficient)),
        ]
        for monomial, coefficient in polynomial.terms()
    ]


def _serial_qq_polynomial(expression: sp.Expr) -> list[list[Any]]:
    return _serial_ring_polynomial(COEFFICIENT_RING.from_expr(sp.expand(expression)))


def _normal_coefficient(expression: Coefficient | sp.Expr | Fraction | int) -> Coefficient:
    """Land any admissible scalar in ``QQ(t1,t2,t3,t4)``, already in reduced form."""

    if isinstance(expression, FracElement):
        if expression.field is not COEFFICIENT_FIELD:
            raise AssertionError("a coefficient escaped the declared QQ(t) fraction field")
        return expression
    if isinstance(expression, Fraction):
        return COEFFICIENT_FIELD(QQ(expression.numerator, expression.denominator))
    if isinstance(expression, PolyElement | int):
        return COEFFICIENT_FIELD(expression)
    return COEFFICIENT_FIELD.from_expr(sp.sympify(expression))


_SERIAL_COEFFICIENT_CACHE: dict[Coefficient, dict[str, Any]] = {}


def _serial_coefficient(coefficient: Coefficient) -> dict[str, Any]:
    """Serialise a reduced coefficient as a denominator-monic numerator/denominator pair."""

    cached = _SERIAL_COEFFICIENT_CACHE.get(coefficient)
    if cached is not None:
        return cached
    numerator, denominator = coefficient.numer, coefficient.denom
    leading = denominator.LC
    serial = {
        "numerator": _serial_ring_polynomial(numerator.quo_ground(leading)),
        "denominator": _serial_ring_polynomial(denominator.quo_ground(leading)),
    }
    _SERIAL_COEFFICIENT_CACHE[coefficient] = serial
    return serial


def _serial_polynomial(polynomial: LaurentPolynomial) -> list[list[Any]]:
    return [
        [_serial_exponent(exponent), _serial_coefficient(coefficient)]
        for exponent, coefficient in sorted(polynomial.items())
    ]


def _coefficient_free_symbols(coefficient: Coefficient) -> set[sp.Symbol]:
    """Symbols actually occurring in a coefficient, read off its sparse support."""

    present: set[sp.Symbol] = set()
    for polynomial in (coefficient.numer, coefficient.denom):
        for monomial in polynomial.monoms():
            for index, power in enumerate(monomial):
                if power:
                    present.add(T_SYMBOLS[index])
    return present


def _serial_fraction_polynomial(polynomial: FractionPolynomial) -> list[list[Any]]:
    return [
        [_serial_exponent(exponent), coefficient.numerator, coefficient.denominator]
        for exponent, coefficient in sorted(polynomial.items())
    ]


def _poly_digest(polynomial: LaurentPolynomial) -> str:
    return _digest(_serial_polynomial(polynomial))


def _clean(polynomial: Mapping[FullExponent, Coefficient]) -> LaurentPolynomial:
    """Drop vanishing terms.  Fraction-field values are reduced already."""

    return {exponent: value for exponent, value in polynomial.items() if value}


def _constant(width: int, value: Coefficient | sp.Expr | Fraction | int) -> LaurentPolynomial:
    coefficient = _normal_coefficient(value)
    return {} if not coefficient else {(0,) * width: coefficient}


def _monomial(
    width: int,
    exponent: FullExponent,
    coefficient: Coefficient | sp.Expr | Fraction | int = 1,
) -> LaurentPolynomial:
    if len(exponent) != width:
        raise AssertionError("Laurent exponent width mismatch")
    value = _normal_coefficient(coefficient)
    return {} if not value else {exponent: value}


def _add(left: LaurentPolynomial, right: LaurentPolynomial) -> LaurentPolynomial:
    if not left:
        return dict(right)
    if not right:
        return dict(left)
    result = dict(left)
    for exponent, value in right.items():
        current = result.get(exponent)
        if current is None:
            result[exponent] = value
            continue
        total = current + value
        if total:
            result[exponent] = total
        else:
            del result[exponent]
    return result


def _neg(polynomial: LaurentPolynomial) -> LaurentPolynomial:
    return {exponent: -value for exponent, value in polynomial.items()}


def _sub(left: LaurentPolynomial, right: LaurentPolynomial) -> LaurentPolynomial:
    if not right:
        return dict(left)
    result = dict(left)
    for exponent, value in right.items():
        current = result.get(exponent)
        if current is None:
            result[exponent] = -value
            continue
        total = current - value
        if total:
            result[exponent] = total
        else:
            del result[exponent]
    return result


def _mul(left: LaurentPolynomial, right: LaurentPolynomial) -> LaurentPolynomial:
    if not left or not right:
        return {}
    if len(left) == 1:
        ((shift, scalar),) = left.items()
        return {
            tuple(a + b for a, b in zip(exponent, shift, strict=True)): coefficient * scalar
            for exponent, coefficient in right.items()
        }
    if len(right) == 1:
        ((shift, scalar),) = right.items()
        return {
            tuple(a + b for a, b in zip(exponent, shift, strict=True)): coefficient * scalar
            for exponent, coefficient in left.items()
        }
    result: LaurentPolynomial = {}
    for left_exponent, left_value in left.items():
        for right_exponent, right_value in right.items():
            exponent = tuple(a + b for a, b in zip(left_exponent, right_exponent, strict=True))
            product = left_value * right_value
            current = result.get(exponent)
            if current is None:
                result[exponent] = product
                continue
            total = current + product
            if total:
                result[exponent] = total
            else:
                del result[exponent]
    return result


def _scale_shift(
    polynomial: LaurentPolynomial,
    scalar: Coefficient | sp.Expr | Fraction | int,
    shift: FullExponent,
) -> LaurentPolynomial:
    value = _normal_coefficient(scalar)
    if not polynomial or not value:
        return {}
    return {
        tuple(a + b for a, b in zip(exponent, shift, strict=True)): coefficient * value
        for exponent, coefficient in polynomial.items()
    }


def _divide_by_monomial(
    polynomial: LaurentPolynomial,
    divisor: LaurentPolynomial,
) -> LaurentPolynomial:
    if len(divisor) != 1:
        raise AssertionError("division is permitted only by a Laurent monomial")
    ((exponent, coefficient),) = divisor.items()
    return _scale_shift(
        polynomial,
        COEFFICIENT_ONE / coefficient,
        tuple(-value for value in exponent),
    )


def _evaluate_ring_polynomial(polynomial: PolyElement, point: Sequence[Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in polynomial.terms():
        term = Fraction(int(QQ.numer(coefficient)), int(QQ.denom(coefficient)))
        for value, power in zip(point, monomial, strict=True):
            if power:
                term *= value**power
        total += term
    return total


def _evaluate(polynomial: LaurentPolynomial, point: Sequence[Fraction]) -> Fraction:
    bottom = point[:4]
    total = Fraction(0)
    for exponent, coefficient in polynomial.items():
        denominator = _evaluate_ring_polynomial(coefficient.denom, bottom)
        if not denominator:
            raise ZeroDivisionError("localized coefficient denominator vanished at the point")
        term = _evaluate_ring_polynomial(coefficient.numer, bottom) / denominator
        for value, power in zip(point, exponent, strict=True):
            if not power:
                continue
            if not value and power < 0:
                raise ZeroDivisionError("Laurent variable evaluated at zero")
            term *= value**power
        total += term
    return total


def _row_digest(row: Mapping[str, LaurentPolynomial]) -> str:
    return _digest(
        [[variable, _serial_polynomial(row[variable])] for variable in sorted(row) if row[variable]]
    )


def _row_equal(
    left: Mapping[str, LaurentPolynomial], right: Mapping[str, LaurentPolynomial]
) -> bool:
    return all(
        _clean(left.get(variable, {})) == _clean(right.get(variable, {}))
        for variable in set(left) | set(right)
    )


def _row_add_scaled(
    target: BaseRow,
    row: Mapping[str, LaurentPolynomial],
    scalar: LaurentPolynomial,
    *,
    subtract: bool,
) -> None:
    for variable, coefficient in row.items():
        update = _mul(scalar, coefficient)
        target[variable] = (
            _sub(target.get(variable, {}), update)
            if subtract
            else _add(target.get(variable, {}), update)
        )
        if not target[variable]:
            target.pop(variable)


def _sympy_monomial(
    expression: sp.Expr,
    symbols: tuple[sp.Symbol, ...],
) -> tuple[Fraction, FullExponent]:
    powers = expression.as_powers_dict()
    exponents: list[int] = []
    residual = expression
    for symbol in symbols:
        power = powers.get(symbol, 0)
        if not bool(getattr(power, "is_integer", False)):
            raise AssertionError(f"nonintegral Laurent exponent: {power}")
        integer = int(power)
        exponents.append(integer)
        if integer:
            residual /= symbol**integer
    residual = sp.cancel(residual)
    if residual.free_symbols:
        raise AssertionError(f"nonmonomial denominator or unresolved symbol: {residual}")
    if not residual.is_Rational:
        raise AssertionError(f"nonrational Laurent coefficient: {residual}")
    return Fraction(int(residual.p), int(residual.q)), tuple(exponents)


def _expression_to_base(
    expression: sp.Expr,
    diagonal_monomials: Mapping[sp.Symbol, LaurentPolynomial],
    width: int,
) -> LaurentPolynomial:
    if expression == 0:
        return {}
    result: LaurentPolynomial = {}
    for term in sp.Add.make_args(sp.expand(expression)):
        powers = term.as_powers_dict()
        residual = term
        product = _constant(width, 1)
        for symbol, monomial in diagonal_monomials.items():
            power = powers.get(symbol, 0)
            if not power:
                continue
            if not bool(getattr(power, "is_integer", False)) or int(power) < 0:
                raise AssertionError("source row is not polynomial in diagonal symbols")
            integer = int(power)
            residual /= symbol**integer
            for _ in range(integer):
                product = _mul(product, monomial)
        residual = sp.cancel(residual)
        if residual.free_symbols or not residual.is_Rational:
            raise AssertionError(f"unresolved diagonal expression: {residual}")
        coefficient = COEFFICIENT_FIELD(QQ(int(residual.p), int(residual.q)))
        result = _add(result, _scale_shift(product, coefficient, (0,) * width))
    return result


def _rebuild_symbolic_m0_rows(
    context: torus.ScoutContext,
) -> tuple[list[q5_free.SymbolicRow], dict[str, sp.Symbol], dict[str, sp.Symbol]]:
    """Rebuild M0 directly from the source inventories, independently of JSON."""

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

    rows: list[q5_free.SymbolicRow] = []
    raw_index = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operators = equation["operator_ids"]
            left = unit_minor._word(  # noqa: SLF001
                occurrence_matrices[operators[token]] for token in equation["lhs_word"]
            )
            right = unit_minor._word(  # noqa: SLF001
                occurrence_matrices[operators[token]] for token in equation["rhs_word"]
            )
            rows.append(
                q5_free.SymbolicRow(
                    "raw_CPOBC",
                    raw_index,
                    unit_minor._add(left.coefficients, unit_minor._scale(-1, right.coefficients)),  # noqa: SLF001
                )
            )
            raw_index += 1

    path_matrices: dict[str, unit_minor.SymbolicTriangular] = {}
    path_records: dict[str, dict[str, Any]] = {}
    for paths in context.operator_gc["path_inventory"].values():
        for path in paths:
            product = unit_minor.SymbolicTriangular(sp.Integer(1), sp.Integer(1), {})
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                transition = from_signature(
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                product = unit_minor._multiply(transition, product)  # noqa: SLF001
            path_id = str(path["path_id"])
            path_matrices[path_id] = product
            path_records[path_id] = path

    for offset, relation in enumerate(context.operator_gc["generating_relation_basis"]):
        left = path_matrices[str(relation["lhs_path_id"])]
        right = path_matrices[str(relation["rhs_path_id"])]
        rows.append(
            q5_free.SymbolicRow(
                "fixed_vector_GC",
                843 + offset,
                unit_minor._add(left.coefficients, unit_minor._scale(-1, right.coefficients)),  # noqa: SLF001
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
            q5_free.SymbolicRow(
                "reachable_state_MSR",
                1163 + offset,
                unit_minor._add(  # noqa: SLF001
                    unit_minor._scale(residual_upper_left, state.coefficients),  # noqa: SLF001
                    unit_minor._scale(  # noqa: SLF001
                        state.lower_right,
                        unit_minor._clean(dict(residual_upper)),  # noqa: SLF001
                    ),
                ),
            )
        )
    if raw_index != 783 or [row.joint_source for row in rows] != list(M0_SOURCES):
        raise AssertionError("independent M0 source inventory changed")
    return rows, upper, lower


def _symbolic_rows_equal(left: Mapping[str, sp.Expr], right: Mapping[str, sp.Expr]) -> bool:
    return all(
        sp.cancel(left.get(variable, 0) - right.get(variable, 0)) == 0
        for variable in set(left) | set(right)
    )


@dataclass(frozen=True)
class BaseCoordinates:
    full_names: tuple[str, ...]
    full_symbols: tuple[sp.Symbol, ...]
    active_indices: tuple[int, ...]
    active_names: tuple[str, ...]
    dropped_indices: tuple[int, int]
    diagonal_monomials: dict[sp.Symbol, LaurentPolynomial]
    upper_monomials: dict[str, LaurentPolynomial]
    lower_monomials: dict[str, LaurentPolynomial]
    kernel: list[list[int]]


def _base_coordinates(
    context: torus.ScoutContext,
    operator_context: lattice.LatticeContext,
    upper_symbols: Mapping[str, sp.Symbol],
    lower_symbols: Mapping[str, sp.Symbol],
) -> BaseCoordinates:
    operator_rows, _counts = lattice._operator_lattice_rows(operator_context)  # noqa: SLF001
    kernel = lattice._integer_kernel_columns(operator_rows[:783], operator_context.variables)  # noqa: SLF001
    if len(kernel) != 49 or len(kernel[0]) != len(context.variables):
        raise AssertionError("upper torus kernel shape changed")
    q5_index = context.variables.index(torus.Q5)
    q5_only = [
        index
        for index, column in enumerate(kernel)
        if [i for i, value in enumerate(column) if value] == [q5_index]
    ]
    if q5_only != [48] or kernel[48][q5_index] != 1:
        raise AssertionError("the upper Q5-only kernel coordinate changed")

    t_symbols = T_SYMBOLS
    bottom_q5 = BOTTOM_Q5_SYMBOL
    s_symbols = sp.symbols("s0:49", nonzero=True)
    full_symbols = (*t_symbols, bottom_q5, *s_symbols)
    full_names = tuple(str(symbol) for symbol in full_symbols)
    width = len(full_names)
    if width != 54:
        raise AssertionError("the transverse scalar base is no longer 54-dimensional")

    bottom_values, predecessor_t, predecessor_q5 = unit_minor._bottom_formulas(context)  # noqa: SLF001
    bottom_substitution = {predecessor_t[index]: t_symbols[index] for index in range(4)} | {
        predecessor_q5: bottom_q5
    }
    lower_monomials: dict[str, LaurentPolynomial] = {}
    for variable in context.variables:
        expression = sp.cancel(bottom_values[variable].subs(bottom_substitution, simultaneous=True))
        if variable == torus.Q5:
            lower_exponent = [0] * width
            lower_exponent[4] = 1
            lower_monomials[variable] = _monomial(width, tuple(lower_exponent))
        else:
            if expression.free_symbols - set(T_SYMBOLS):
                raise AssertionError("bottom CSG coefficient has an unexpected symbol")
            lower_monomials[variable] = _constant(width, expression)

    upper_monomials: dict[str, LaurentPolynomial] = {}
    for variable_index, variable in enumerate(context.variables):
        exponent = (0, 0, 0, 0, 0, *(kernel[column][variable_index] for column in range(49)))
        upper_monomials[variable] = _monomial(width, tuple(exponent))

    diagonal_monomials = {
        **{upper_symbols[variable]: upper_monomials[variable] for variable in context.variables},
        **{lower_symbols[variable]: lower_monomials[variable] for variable in context.variables},
    }
    dropped = (4, 53)
    active = tuple(index for index in range(width) if index not in dropped)
    active_names = tuple(full_names[index] for index in active)
    if active_names != (*map(str, t_symbols), *(f"s{index}" for index in range(48))):
        raise AssertionError("the 52-variable active order changed")
    return BaseCoordinates(
        full_names,
        full_symbols,
        active,
        active_names,
        dropped,
        diagonal_monomials,
        upper_monomials,
        lower_monomials,
        kernel,
    )


def _project_active(
    polynomial: LaurentPolynomial, coordinates: BaseCoordinates
) -> LaurentPolynomial:
    for exponent in polynomial:
        if any(exponent[index] for index in coordinates.dropped_indices):
            raise AssertionError("a purported spectator occurs in a Laurent polynomial")
    return {
        tuple(exponent[index] for index in coordinates.active_indices): coefficient
        for exponent, coefficient in polynomial.items()
    }


def _lift_active(polynomial: LaurentPolynomial, coordinates: BaseCoordinates) -> LaurentPolynomial:
    result: LaurentPolynomial = {}
    for exponent, coefficient in polynomial.items():
        full = [0] * len(coordinates.full_names)
        for active_index, full_index in enumerate(coordinates.active_indices):
            full[full_index] = exponent[active_index]
        result[tuple(full)] = coefficient
    return result


def _convert_symbolic_row(
    row: Mapping[str, sp.Expr],
    coordinates: BaseCoordinates,
) -> BaseRow:
    converted = {
        variable: _expression_to_base(
            expression,
            coordinates.diagonal_monomials,
            len(coordinates.full_names),
        )
        for variable, expression in row.items()
    }
    return {variable: polynomial for variable, polynomial in converted.items() if polynomial}


def _pivot_system(
    context: torus.ScoutContext,
    source_rows: Mapping[int, BaseRow],
    q_variables: tuple[str, ...],
) -> dict[str, Any]:
    non_q = tuple(variable for variable in context.variables if variable not in q_variables)
    pivot_rows = [source_rows[source] for source in PIVOT_SOURCES]
    support = [
        [index for index, variable in enumerate(non_q) if row.get(variable)] for row in pivot_rows
    ]
    matching, unique, inversions = unit_minor._ordered_perfect_matching(support)  # noqa: SLF001
    if not unique:
        raise AssertionError("the pivot support matching is no longer unique")
    owner = {column: row for row, column in enumerate(matching)}
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(pivot_rows)))
    for row_index, columns in enumerate(support):
        for column in columns:
            if column != matching[row_index]:
                graph.add_edge(row_index, owner[column])
    if not nx.is_directed_acyclic_graph(graph):
        raise AssertionError("the unique-matching elimination graph is cyclic")
    elimination_order = tuple(nx.lexicographical_topological_sort(graph, key=lambda value: value))
    order_position = {row: index for index, row in enumerate(elimination_order)}

    normalized: dict[int, BaseRow] = {}
    diagonals: dict[int, LaurentPolynomial] = {}
    for row_index, row in enumerate(pivot_rows):
        variable = non_q[matching[row_index]]
        diagonal = row.get(variable, {})
        if len(diagonal) != 1:
            raise AssertionError("a matched pivot entry is not a Laurent monomial")
        normalized[row_index] = {
            name: _divide_by_monomial(polynomial, diagonal) for name, polynomial in row.items()
        }
        if normalized[row_index].get(variable) != _constant(len(next(iter(diagonal))), 1):
            raise AssertionError("pivot normalization failed")
        diagonals[row_index] = diagonal
        for column in support[row_index]:
            other = owner[column]
            if other != row_index and order_position[other] <= order_position[row_index]:
                raise AssertionError("pivot row is not triangular in the elimination order")

    return {
        "non_q": non_q,
        "rows": pivot_rows,
        "support": support,
        "matching": tuple(matching),
        "unique": unique,
        "inversions": inversions,
        "graph_edges": tuple(sorted(graph.edges())),
        "elimination_order": elimination_order,
        "normalized": normalized,
        "diagonals": diagonals,
    }


def _schur_reduce(
    source: BaseRow,
    pivot: Mapping[str, Any],
    q_variables: tuple[str, ...],
) -> tuple[BaseRow, dict[int, LaurentPolynomial], bool]:
    work = dict(source)
    combination: dict[int, LaurentPolynomial] = {}
    non_q: tuple[str, ...] = pivot["non_q"]
    matching: tuple[int, ...] = pivot["matching"]
    for pivot_index in pivot["elimination_order"]:
        variable = non_q[matching[pivot_index]]
        scale = work.get(variable, {})
        if not scale:
            continue
        combination[pivot_index] = _divide_by_monomial(scale, pivot["diagonals"][pivot_index])
        _row_add_scaled(work, pivot["normalized"][pivot_index], scale, subtract=True)
    if any(work.get(variable) for variable in non_q):
        raise AssertionError("the unit pivot block did not eliminate every non-Q column")
    schur = {variable: work[variable] for variable in q_variables if work.get(variable)}

    reconstructed = dict(schur)
    for pivot_index, coefficient in combination.items():
        _row_add_scaled(reconstructed, pivot["rows"][pivot_index], coefficient, subtract=False)
    return schur, combination, _row_equal(reconstructed, source)


class LocalizedArena:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self._by_json: dict[str, int] = {}

    def intern(self, polynomial: LaurentPolynomial) -> int:
        serial = _serial_polynomial(polynomial)
        key = _canonical_json(serial)
        existing = self._by_json.get(key)
        if existing is not None:
            return existing
        identifier = len(self.records)
        self._by_json[key] = identifier
        self.records.append(
            {
                "polynomial_id": identifier,
                "term_count": len(polynomial),
                "sha256": _digest_canonical_json(key),
                "terms": serial,
            }
        )
        return identifier


class PolynomialArena:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self._by_json: dict[str, int] = {}
        self._polynomials: list[FractionPolynomial] = []

    def intern(self, polynomial: FractionPolynomial) -> int:
        serial = _serial_fraction_polynomial(polynomial)
        key = _canonical_json(serial)
        existing = self._by_json.get(key)
        if existing is not None:
            return existing
        identifier = len(self.records)
        self._by_json[key] = identifier
        self._polynomials.append(polynomial)
        self.records.append(
            {
                "polynomial_id": identifier,
                "term_count": len(polynomial),
                "sha256": _digest_canonical_json(key),
                "terms": serial,
            }
        )
        return identifier

    def polynomial(self, identifier: int) -> FractionPolynomial:
        return self._polynomials[identifier]


def _normal_polynomial_factor(expression: sp.Expr) -> sp.Expr:
    polynomial = sp.Poly(sp.expand(expression), *T_SYMBOLS, domain=sp.QQ)
    return sp.expand(polynomial.as_expr() / polynomial.LC())


def _lambda_factor_basis() -> dict[str, dict[str, Any]]:
    couplings: tuple[sp.Expr, ...] = (sp.Integer(1), *T_SYMBOLS)
    by_key: dict[str, dict[str, Any]] = {}
    for width in range(5):
        for maximal in range(width + 1):
            expression = sp.factor(bottom_global._lambda_polynomial(width, maximal, couplings))  # noqa: SLF001
            if expression == 1:
                continue
            normal = _normal_polynomial_factor(expression)
            key = _canonical_json(_serial_qq_polynomial(normal))
            record = by_key.setdefault(
                key,
                {
                    "factor_id": f"lambda_{width}_{maximal}",
                    "expression": str(normal),
                    "polynomial": normal,
                    "ring_polynomial": COEFFICIENT_RING.from_expr(normal),
                    "aliases": [],
                },
            )
            record["aliases"].append(f"lambda({width},{maximal})")
    _assert_factor_basis_is_irreducible(by_key)
    return by_key


def _assert_factor_basis_is_irreducible(factor_basis: Mapping[str, Mapping[str, Any]]) -> None:
    """Trial division may replace factorisation only over an irreducible basis.

    ``_denominator_factorisation`` divides denominators by the basis factors
    instead of running ``sp.factor_list`` on every coefficient.  That agrees
    with full factorisation exactly when each basis element is irreducible over
    ``QQ``, so the property is checked once, here, rather than assumed.
    """

    for record in factor_basis.values():
        unit, factors = sp.factor_list(record["polynomial"], *T_SYMBOLS)
        if not sp.sympify(unit).is_Rational or len(factors) != 1 or int(factors[0][1]) != 1:
            raise AssertionError(f"reducible lambda factor in the basis: {record['factor_id']}")


_DENOMINATOR_FACTORISATION_CACHE: dict[PolyElement, tuple[dict[str, int], bool, list[str]]] = {}

#: Rational unit left over once a denominator has been divided by its certified
#: lambda factors.  ``_materialize_over_qq`` needs it to clear denominators by
#: multiplication instead of polynomial division.
_DENOMINATOR_GROUND_UNIT_CACHE: dict[PolyElement, Any] = {}


def _factorise_denominator_polynomial(
    denominator: PolyElement,
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, int], bool, list[str]]:
    """Split a denominator into certified lambda factors by exact trial division.

    Because the basis is irreducible (see ``_assert_factor_basis_is_irreducible``)
    and ``QQ[t1..t4]`` is a UFD, dividing out the basis factors yields the same
    multiplicities as ``sp.factor_list`` while avoiding it entirely.  Only a
    residual that is not a ground constant needs real factorisation, and that is
    exactly the case the audit reports as an unknown factor.
    """

    cached = _DENOMINATOR_FACTORISATION_CACHE.get(denominator)
    if cached is not None:
        return cached
    work = denominator
    exponents: defaultdict[str, int] = defaultdict(int)
    for record in factor_basis.values():
        factor = record["ring_polynomial"]
        while True:
            quotient, remainder = divmod(work, factor)
            if remainder:
                break
            work = quotient
            exponents[str(record["factor_id"])] += 1
    unknown: list[str] = []
    if work.is_ground:
        _DENOMINATOR_GROUND_UNIT_CACHE[denominator] = work.LC
    else:
        unit, residual_factors = sp.factor_list(work.as_expr(), *T_SYMBOLS)
        if not sp.sympify(unit).is_Rational:
            rejected: tuple[dict[str, int], bool, list[str]] = ({}, False, [str(unit)])
            _DENOMINATOR_FACTORISATION_CACHE[denominator] = rejected
            return rejected
        unknown = [str(_normal_polynomial_factor(factor)) for factor, _ in residual_factors]
    result = (dict(exponents), not unknown, unknown)
    _DENOMINATOR_FACTORISATION_CACHE[denominator] = result
    return result


def _denominator_factorisation(
    coefficient: Coefficient,
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, int], bool, list[str]]:
    return _factorise_denominator_polynomial(
        _normal_coefficient(coefficient).denom,
        factor_basis,
    )


_FACTOR_PRODUCT_CACHE: dict[tuple[tuple[str, int], ...], tuple[PolyElement, sp.Expr]] = {}


def _certified_denominator_product(
    exponents: Mapping[str, int],
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> tuple[PolyElement, sp.Expr]:
    """Return the clearing product both as a ring element and as a report expression."""

    key = tuple(sorted(exponents.items()))
    cached = _FACTOR_PRODUCT_CACHE.get(key)
    if cached is None:
        by_id = {str(record["factor_id"]): record for record in factor_basis.values()}
        ring_product = COEFFICIENT_RING.one
        for factor_id, exponent in key:
            ring_product = ring_product * by_id[factor_id]["ring_polynomial"] ** exponent
        cached = (ring_product, _factor_product(exponents, factor_basis))
        _FACTOR_PRODUCT_CACHE[key] = cached
    return cached


def _factor_product(
    exponents: Mapping[str, int],
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> sp.Expr:
    by_id = {str(record["factor_id"]): record for record in factor_basis.values()}
    return sp.factor(
        sp.prod(
            by_id[factor_id]["polynomial"] ** exponent for factor_id, exponent in exponents.items()
        )
    )


def _localized_bottom_unit_certificate(
    coefficient: Coefficient,
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    value = _normal_coefficient(coefficient)
    numerator_factors, numerator_certified, numerator_unknown = _factorise_denominator_polynomial(
        (COEFFICIENT_ONE / value).denom,
        factor_basis,
    )
    (
        denominator_factors,
        denominator_certified,
        denominator_unknown,
    ) = _factorise_denominator_polynomial(value.denom, factor_basis)
    return {
        "numerator_factor_exponents": dict(sorted(numerator_factors.items())),
        "denominator_factor_exponents": dict(sorted(denominator_factors.items())),
        "unknown_numerator_factors": sorted(numerator_unknown),
        "unknown_denominator_factors": sorted(denominator_unknown),
        "is_unit_in_certified_bottom_localization": numerator_certified and denominator_certified,
    }


def _materialize_over_qq(
    polynomial: LaurentPolynomial,
    denominator_exponents: Mapping[str, int],
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> FractionPolynomial:
    """Clear denominators against the certified lambda product, by multiplication only.

    The clearing product is the factorwise maximum over the whole coefficient
    family, so for each coefficient it is a multiple of that coefficient's own
    denominator.  Multiplying by the complementary factor product and dividing by
    the leftover rational unit is therefore exact, and replaces a multivariate
    polynomial division per term.
    """

    result: defaultdict[FullExponent, Fraction] = defaultdict(Fraction)
    cleared_numerators: dict[Coefficient, PolyElement] = {}
    for exponent, coefficient in polynomial.items():
        cleared = cleared_numerators.get(coefficient)
        if cleared is None:
            factors, certified, _unknown = _denominator_factorisation(coefficient, factor_basis)
            if not certified:
                raise AssertionError(
                    f"certified denominator product did not clear {coefficient}",
                )
            complement, _expression = _certified_denominator_product(
                {
                    factor_id: exponent_bound - factors.get(factor_id, 0)
                    for factor_id, exponent_bound in denominator_exponents.items()
                },
                factor_basis,
            )
            unit = _DENOMINATOR_GROUND_UNIT_CACHE[coefficient.denom]
            cleared = (coefficient.numer * complement).quo_ground(unit)
            cleared_numerators[coefficient] = cleared
        for t_exponent, value in cleared.terms():
            full = list(exponent)
            for index, power in enumerate(t_exponent):
                full[index] += int(power)
            result[tuple(full)] += Fraction(int(QQ.numer(value)), int(QQ.denom(value)))
    return {exponent: value for exponent, value in result.items() if value}


def _fraction_to_localized(polynomial: FractionPolynomial) -> LaurentPolynomial:
    """Fold the four bottom exponents of a QQ presentation back into the coefficients.

    The bottom part of every Laurent exponent is collected per upper monomial and
    converted in one step, so each coefficient is built by a single fraction-field
    construction instead of one per term.
    """

    grouped: dict[FullExponent, dict[tuple[int, ...], Fraction]] = defaultdict(dict)
    for exponent, coefficient in polynomial.items():
        grouped[(0, 0, 0, 0, *exponent[4:])][exponent[:4]] = coefficient

    result: LaurentPolynomial = {}
    for base, bottom_terms in grouped.items():
        shift = tuple(
            min(0, min(exponent[index] for exponent in bottom_terms)) for index in range(4)
        )
        numerator = COEFFICIENT_RING.from_dict(
            {
                tuple(value - offset for value, offset in zip(exponent, shift, strict=True)): QQ(
                    coefficient.numerator, coefficient.denominator
                )
                for exponent, coefficient in bottom_terms.items()
            }
        )
        if not numerator:
            continue
        if any(shift):
            # The shift is the per-variable minimum, so the numerator is not
            # divisible by the denominator monomial and the pair is already reduced.
            value = COEFFICIENT_FIELD.new(
                numerator,
                COEFFICIENT_RING.from_dict({tuple(-offset for offset in shift): QQ.one}),
            )
        else:
            value = COEFFICIENT_FIELD(numerator)
        if value:
            result[base] = value
    return result


def _shift_and_scale(
    polynomial: FractionPolynomial,
    shift: FullExponent | None,
    factor: Fraction | int,
) -> FractionPolynomial:
    """Translate exponents and rescale coefficients, skipping either when trivial."""

    if shift is None:
        if factor == 1:
            return dict(polynomial)
        return {exponent: coefficient * factor for exponent, coefficient in polynomial.items()}
    return {
        tuple(a + b for a, b in zip(exponent, shift, strict=True)): coefficient * factor
        for exponent, coefficient in polynomial.items()
    }


def _reconstructs_original(
    restored: Mapping[FullExponent, Coefficient],
    original: Mapping[FullExponent, Coefficient],
    denominator_product: PolyElement,
) -> bool:
    """Check that undoing the clearing returns the original coefficients exactly.

    ``restored`` still carries the certified denominator product, so instead of
    dividing it back out — which would cost a gcd per term — the identity
    ``restored * original.denom == original.numer * product * restored.denom``
    is verified by polynomial multiplication alone.
    """

    if set(restored) != set(original):
        return False
    for exponent, coefficient in original.items():
        value = restored[exponent]
        left = value.numer * coefficient.denom
        right = coefficient.numer * denominator_product * value.denom
        if left != right:
            return False
    return True


def _clearing_certificate(
    coefficients: Mapping[str, LaurentPolynomial],
    localized_arena: LocalizedArena,
    arena: PolynomialArena,
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    nonzero = [polynomial for polynomial in coefficients.values() if polynomial]
    width = len(next(iter(next(iter(nonzero)).keys()))) if nonzero else 52
    denominator_exponents: defaultdict[str, int] = defaultdict(int)
    factor_records = []
    all_certified = True
    unknown_factors: set[str] = set()
    for name, polynomial in coefficients.items():
        for exponent, coefficient in sorted(polynomial.items()):
            factors, certified, unknown = _denominator_factorisation(coefficient, factor_basis)
            all_certified = all_certified and certified
            unknown_factors.update(unknown)
            for factor_id, multiplicity in factors.items():
                denominator_exponents[factor_id] = max(
                    denominator_exponents[factor_id], multiplicity
                )
            factor_records.append(
                {
                    "coefficient": name,
                    "Laurent_exponent": _serial_exponent(exponent),
                    "denominator_factor_exponents": factors,
                    "all_factors_certified_CSG_units": certified,
                    "unknown_factors": unknown,
                }
            )
    ring_denominator_product, denominator_product = _certified_denominator_product(
        denominator_exponents, factor_basis
    )
    materialized = {
        name: _materialize_over_qq(polynomial, denominator_exponents, factor_basis)
        for name, polynomial in coefficients.items()
    }
    minima = [0] * width
    scalar = 1
    nonzero_materialized = [polynomial for polynomial in materialized.values() if polynomial]
    if nonzero_materialized:
        first = True
        for polynomial in nonzero_materialized:
            for exponent, coefficient in polynomial.items():
                if first:
                    minima = list(exponent)
                    first = False
                else:
                    for index, value in enumerate(exponent):
                        if value < minima[index]:
                            minima[index] = value
                scalar = math.lcm(scalar, coefficient.denominator)
    shift = tuple(max(0, -value) for value in minima)
    shifting = any(shift)
    cleared = {
        name: _shift_and_scale(polynomial, shift if shifting else None, scalar)
        for name, polynomial in materialized.items()
    }
    unshifted = {
        name: _shift_and_scale(
            polynomial,
            tuple(-value for value in shift) if shifting else None,
            Fraction(1, scalar),
        )
        for name, polynomial in cleared.items()
    }
    reconstructed = {
        name: _fraction_to_localized(polynomial) for name, polynomial in unshifted.items()
    }
    nonnegative = all(
        min(exponent) >= 0 for polynomial in cleared.values() for exponent in polynomial
    )
    integral = all(
        coefficient.denominator == 1
        for polynomial in cleared.values()
        for coefficient in polynomial.values()
    )
    return {
        "coefficient_polynomial_ids": {
            name: localized_arena.intern(polynomial) for name, polynomial in coefficients.items()
        },
        "cleared_coefficient_polynomial_ids": {
            name: arena.intern(polynomial) for name, polynomial in cleared.items()
        },
        "clearing_scalar": scalar,
        "clearing_monomial": _serial_exponent(shift),
        "bottom_polynomial_clearing_exponent": list(shift[:4]),
        "upper_Laurent_clearing_exponent": list(shift[4:]),
        "certified_CSG_denominator_factor_exponents": dict(sorted(denominator_exponents.items())),
        "certified_CSG_denominator_product": str(denominator_product),
        "denominator_factor_ledger_sha256": _digest(factor_records),
        "denominator_factor_record_count": len(factor_records),
        "unknown_denominator_factors": sorted(unknown_factors),
        (
            "denominator_is_product_of_rational_Laurent_monomial_and_certified_CSG_factors"
        ): all_certified,
        "cleared_exponents_are_nonnegative": nonnegative,
        "cleared_coefficients_are_integers": integral,
        "inverse_reconstruction_verified": all(
            _reconstructs_original(reconstructed[name], polynomial, ring_denominator_product)
            for name, polynomial in coefficients.items()
        ),
    }


def _combine(polynomials: Iterable[LaurentPolynomial]) -> LaurentPolynomial:
    total: LaurentPolynomial = {}
    for polynomial in polynomials:
        total = _add(total, polynomial)
    return total


def _chart_polynomials(
    context: torus.ScoutContext,
    coordinates: BaseCoordinates,
) -> dict[str, LaurentPolynomial]:
    q_variables = tuple(torus._q_variable(context, stage) for stage in range(1, 5))
    upper = {
        variable: _project_active(coordinates.upper_monomials[variable], coordinates)
        for variable in q_variables
    }
    lower = {
        variable: _project_active(coordinates.lower_monomials[variable], coordinates)
        for variable in q_variables
    }
    a1 = upper[q_variables[0]]
    b1 = lower[q_variables[0]]
    result = {"f_tilde": _sub(a1, b1)}
    for index in range(1, 4):
        result[f"d{index + 1}"] = _sub(
            _mul(a1, lower[q_variables[index]]),
            _mul(upper[q_variables[index]], b1),
        )
    return result


def _restriction_coefficients(
    schur: Mapping[str, LaurentPolynomial],
    q_variables: tuple[str, ...],
    upper: Mapping[str, LaurentPolynomial],
    lower: Mapping[str, LaurentPolynomial],
) -> tuple[dict[str, LaurentPolynomial], dict[str, LaurentPolynomial]]:
    b1 = lower[q_variables[0]]
    non_aligned_a: LaurentPolynomial = {}
    non_aligned_b: LaurentPolynomial = {}
    aligned_a: LaurentPolynomial = {}
    aligned_bs: list[LaurentPolynomial] = []
    for index, variable in enumerate(q_variables):
        rho = schur.get(variable, {})
        delta = _sub(upper[variable], lower[variable])
        non_aligned_a = _add(non_aligned_a, _mul(rho, delta))
        visible = _divide_by_monomial(lower[variable], b1)
        non_aligned_b = _add(non_aligned_b, _mul(rho, visible))
        aligned_a = _add(aligned_a, _mul(rho, lower[variable]))
        if index:
            aligned_bs.append(_mul(rho, lower[variable]))
    if len(aligned_bs) != 3:
        raise AssertionError("aligned restriction column count changed")
    return (
        {"A": non_aligned_a, "B": non_aligned_b},
        {
            "A": aligned_a,
            "B2": aligned_bs[0],
            "B3": aligned_bs[1],
            "B4": aligned_bs[2],
        },
    )


def _localization_polynomial(
    cleared_chart: FractionPolynomial,
    width: int,
    bottom_localising_product: sp.Expr,
) -> FractionPolynomial:
    if width != 52:
        raise AssertionError("the active polynomial presentation is no longer 52-dimensional")
    result = _fraction_mul(
        _qq_t_expression_to_fraction_polynomial(bottom_localising_product, width),
        cleared_chart,
    )
    return _fraction_shift(result, (0, 0, 0, 0, *(1 for _ in range(48))))


def _fraction_mul(
    left: FractionPolynomial,
    right: FractionPolynomial,
) -> FractionPolynomial:
    if not left or not right:
        return {}
    result: defaultdict[FullExponent, Fraction] = defaultdict(Fraction)
    for left_exponent, left_value in left.items():
        for right_exponent, right_value in right.items():
            exponent = tuple(a + b for a, b in zip(left_exponent, right_exponent, strict=True))
            result[exponent] += left_value * right_value
    return {exponent: value for exponent, value in result.items() if value}


def _fraction_shift(
    polynomial: FractionPolynomial,
    shift: FullExponent,
) -> FractionPolynomial:
    return {
        tuple(a + b for a, b in zip(exponent, shift, strict=True)): coefficient
        for exponent, coefficient in polynomial.items()
    }


def _qq_t_expression_to_fraction_polynomial(
    expression: sp.Expr,
    width: int,
) -> FractionPolynomial:
    polynomial = sp.Poly(sp.expand(expression), *T_SYMBOLS, domain=sp.QQ)
    result: FractionPolynomial = {}
    for t_exponent, coefficient in polynomial.terms():
        exponent = (*map(int, t_exponent), *(0 for _ in range(width - 4)))
        result[exponent] = Fraction(int(coefficient.p), int(coefficient.q))
    return result


def _snf_audit(
    chart_polynomials: Mapping[str, LaurentPolynomial],
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    rows: list[list[int]] = []
    binomial_term_digests: dict[str, str] = {}
    coefficient_unit_certificates: dict[str, list[dict[str, Any]]] = {}
    for name in ("d2", "d3", "d4"):
        polynomial = chart_polynomials[name]
        if len(polynomial) != 2:
            return {
                "computed": False,
                "reduction_performed": False,
                "reason": f"{name} is not a two-term Laurent binomial",
            }
        terms = sorted(polynomial.items())
        exponents = [term[0] for term in terms]
        if any(exponent[:4] != (0, 0, 0, 0) for exponent in exponents):
            raise AssertionError("bottom parameters leaked into the upper exponent lattice")
        rows.append([a - b for a, b in zip(exponents[0][4:], exponents[1][4:], strict=True)])
        coefficient_unit_certificates[name] = [
            _localized_bottom_unit_certificate(coefficient, factor_basis)
            for _exponent, coefficient in terms
        ]
        binomial_term_digests[name] = _poly_digest(polynomial)
    matrix = sp.Matrix(rows)
    smith = smith_normal_form(matrix, domain=ZZ)
    invariants = [
        abs(int(smith[index, index])) for index in range(min(smith.shape)) if smith[index, index]
    ]
    rank = int(matrix.rank())
    all_coefficients_are_units = all(
        record["is_unit_in_certified_bottom_localization"]
        for records in coefficient_unit_certificates.values()
        for record in records
    )
    permitted = rank == 3 and invariants == [1, 1, 1] and all_coefficients_are_units
    return {
        "computed": True,
        "coefficient_ring": "QQ[t1,t2,t3,t4][F_lambda^-1]",
        "exponent_variables": [f"s{index}" for index in range(48)],
        "exponent_variable_count": 48,
        "exponent_difference_matrix": rows,
        "rank": rank,
        "smith_invariant_factors": invariants,
        "primitive_rank_three_lattice": permitted,
        "bottom_coefficients_are_certified_localized_units": all_coefficients_are_units,
        "bottom_coefficient_unit_certificates": coefficient_unit_certificates,
        "binomial_polynomial_sha256": binomial_term_digests,
        "reduction_performed": False,
        "forward_inverse_exponent_round_trip_certified": False,
        "retained_base_variable_count": 52,
        "reason": (
            "upper-48 invariants and bottom-unit coefficients permit a future 52-to-49 "
            "quotient parametrisation, but Phase A "
            "retains the unreduced presentation because no unimodular forward/inverse map "
            "is frozen in this manifest"
            if permitted
            else "rank/primitivity gate does not permit quotient elimination"
        ),
    }


def _rational_prime_valuations(value: Fraction) -> dict[int, int]:
    result: defaultdict[int, int] = defaultdict(int)
    for prime, exponent in sp.factorint(abs(value.numerator)).items():
        result[int(prime)] += int(exponent)
    for prime, exponent in sp.factorint(value.denominator).items():
        result[int(prime)] -= int(exponent)
    return dict(result)


def _torus_parameters_for_character(
    target: Mapping[str, Fraction],
    variables: Sequence[str],
    kernel: Sequence[Sequence[int]],
) -> tuple[Fraction, ...]:
    columns = kernel[:48]
    matrix = sp.Matrix(
        [[columns[column][index] for column in range(48)] for index in range(len(variables))]
    )
    _rref, pivot_rows = matrix.T.rref()
    selected_rows = list(pivot_rows)
    if len(selected_rows) != 48:
        raise AssertionError("the non-Q upper torus lost rank 48")
    square = matrix[selected_rows, :]
    if abs(int(square.det())) != 1:
        raise AssertionError("the selected upper-torus coordinate minor is not unimodular")
    valuations = [_rational_prime_valuations(target[variable]) for variable in variables]
    primes = sorted({prime for record in valuations for prime in record})
    coordinates = [Fraction(1) for _ in range(48)]
    inverse = square.inv()
    for prime in primes:
        rhs = sp.Matrix([valuations[index].get(prime, 0) for index in selected_rows])
        solution = inverse * rhs
        if any(value.q != 1 for value in solution):
            raise AssertionError(
                "a rational torus point did not have integral parameter valuations"
            )
        for index, exponent in enumerate(solution):
            integer = int(exponent)
            coordinates[index] *= (
                Fraction(prime**integer) if integer >= 0 else Fraction(1, prime ** (-integer))
            )
    for variable_index, variable in enumerate(variables):
        reconstructed = Fraction(1)
        for column, coordinate in enumerate(coordinates):
            reconstructed *= coordinate ** columns[column][variable_index]
        if reconstructed != target[variable]:
            raise AssertionError("upper-torus parameter reconstruction failed")
    return tuple(coordinates)


def _numeric_schur_rows(
    context: torus.ScoutContext,
    upper: Mapping[str, Fraction],
    lower: Any,
    q_variables: tuple[str, ...],
) -> dict[int, dict[str, Fraction]]:
    joint, _counts, _commutators, _paths = torus._linear_system(context, dict(upper), lower)  # noqa: SLF001
    ordered = (
        tuple(variable for variable in context.variables if variable not in q_variables)
        + q_variables
    )
    pivot_echelon = transverse._tracked_row_echelon(  # noqa: SLF001
        [joint[source] for source in PIVOT_SOURCES],
        ordered,
    )
    if int(pivot_echelon["rank"]) != 127 or set(pivot_echelon["basis"]) != set(range(127)):
        raise AssertionError("frozen rational point left the unit pivot chart")
    return {
        source: q5_free._remainder(  # noqa: SLF001
            joint[source],
            pivot_echelon["basis"],
            ordered,
            q_variables,
        )
        for source in M0_SOURCES
    }


def _frozen_point_cross_checks(
    context: torus.ScoutContext,
    coordinates: BaseCoordinates,
    schur_rows: Mapping[int, Mapping[str, LaurentPolynomial]],
    restrictions: Mapping[
        int, tuple[Mapping[str, LaurentPolynomial], Mapping[str, LaurentPolynomial]]
    ],
    chart_polynomials: Mapping[str, LaurentPolynomial],
) -> dict[str, Any]:
    q_variables = tuple(torus._q_variable(context, stage) for stage in range(1, 5))
    lower_callable = locus.bottom_character(
        tuple(Fraction(1) for _ in range(4)),
        Fraction(1, 32),
    )
    lower_point = locus.bottom_point(context, lower_callable)
    non_q_variables = context.variables[:-1]
    base_s = _torus_parameters_for_character(
        {variable: lower_point[variable] for variable in non_q_variables},
        non_q_variables,
        coordinates.kernel,
    )
    aligned_direction = {12: 1, 13: 1, 25: -1}
    q_positions = [context.variables.index(variable) for variable in q_variables]
    if [
        sum(
            coordinates.kernel[column][position] * exponent
            for column, exponent in aligned_direction.items()
        )
        for position in q_positions
    ] != [1, 1, 1, 1]:
        raise AssertionError("the frozen aligned torus direction changed")

    point_specs = [
        ("U2_direction_13", "U2", {13: Fraction(2)}),
        ("U3_direction_15", "U3", {15: Fraction(2)}),
        ("U4_direction_12", "U4", {12: Fraction(2)}),
        *(
            (
                f"aligned_scale_{str(scale).replace('/', '_over_')}",
                "aligned",
                {index: scale**power for index, power in aligned_direction.items()},
            )
            for scale in (Fraction(2), Fraction(3), Fraction(1, 2))
        ),
    ]
    records = []
    for point_id, chart, multipliers in point_specs:
        s_values = list(base_s)
        for index, multiplier in multipliers.items():
            s_values[index] *= multiplier
        active_point = (Fraction(1), Fraction(1), Fraction(1), Fraction(1), *s_values)
        upper: dict[str, Fraction] = {}
        for variable_index, variable in enumerate(context.variables):
            value = Fraction(1)
            for column, parameter in enumerate((*s_values, Fraction(1))):
                value *= parameter ** coordinates.kernel[column][variable_index]
            upper[variable] = value
        numeric_schur = _numeric_schur_rows(context, upper, lower_callable, q_variables)
        schur_mismatches = 0
        restriction_mismatches = 0
        evaluated_restrictions = []
        for source in M0_SOURCES:
            expected = {
                variable: _evaluate(schur_rows[source].get(variable, {}), active_point)
                for variable in q_variables
            }
            actual = {
                variable: numeric_schur[source].get(variable, Fraction(0))
                for variable in q_variables
            }
            if expected != actual:
                schur_mismatches += 1
            non_aligned, aligned = restrictions[source]
            if chart == "aligned":
                expected_coefficients = {
                    name: _evaluate(value, active_point) for name, value in aligned.items()
                }
                actual_coefficients = {
                    "A": sum(actual[variable] * lower_point[variable] for variable in q_variables),
                    "B2": actual[q_variables[1]] * lower_point[q_variables[1]],
                    "B3": actual[q_variables[2]] * lower_point[q_variables[2]],
                    "B4": actual[q_variables[3]] * lower_point[q_variables[3]],
                }
            else:
                expected_coefficients = {
                    name: _evaluate(value, active_point) for name, value in non_aligned.items()
                }
                b1 = lower_point[q_variables[0]]
                actual_coefficients = {
                    "A": sum(
                        actual[variable] * (upper[variable] - lower_point[variable])
                        for variable in q_variables
                    ),
                    "B": sum(
                        actual[variable] * lower_point[variable] / b1 for variable in q_variables
                    ),
                }
            if expected_coefficients != actual_coefficients:
                restriction_mismatches += 1
            evaluated_restrictions.append(
                [
                    source,
                    *(
                        _serial_fraction(expected_coefficients[name])
                        for name in sorted(expected_coefficients)
                    ),
                ]
            )
        chart_values = {
            name: _evaluate(polynomial, active_point)
            for name, polynomial in chart_polynomials.items()
        }
        if chart == "aligned":
            point_in_chart = (
                chart_values["d2"] == chart_values["d3"] == chart_values["d4"] == 0
                and chart_values["f_tilde"] != 0
            )
        else:
            point_in_chart = chart_values[f"d{chart[-1]}"] != 0
        records.append(
            {
                "point_id": point_id,
                "chart": chart,
                "active_base_values": [str(value) for value in active_point],
                "active_base_values_sha256": _digest([str(value) for value in active_point]),
                "chart_function_values": {name: str(value) for name, value in chart_values.items()},
                "point_is_in_declared_chart": point_in_chart,
                "Schur_row_mismatch_count": schur_mismatches,
                "restriction_row_mismatch_count": restriction_mismatches,
                "evaluated_restriction_digest_sha256": _digest(evaluated_restrictions),
            }
        )
    return {
        "point_count": len(records),
        "records": records,
        "records_digest_sha256": _digest(records),
        "all_points_in_declared_charts": all(
            record["point_is_in_declared_chart"] for record in records
        ),
        "all_Schur_rows_match_live_exact_system": all(
            record["Schur_row_mismatch_count"] == 0 for record in records
        ),
        "all_restrictions_match_live_exact_system": all(
            record["restriction_row_mismatch_count"] == 0 for record in records
        ),
        "scope": "exact rational regression points only; not a coverage proof",
    }


def _predecessor_bindings(root: Path) -> dict[str, Any]:
    modules = {
        bottom_global.RESULT_PATH: bottom_global,
        unit_minor.RESULT_PATH: unit_minor,
        q5_free.RESULT_PATH: q5_free,
        obligations.RESULT_PATH: obligations,
    }
    records = {}
    for relative, expected in EXPECTED_PREDECESSORS.items():
        payload = _load(root / relative)
        actual = modules[relative].semantic_digest(payload)
        records[relative] = {
            "schema_version": payload.get("schema_version"),
            "declared_semantic_digest_sha256": payload.get("semantic_digest_sha256"),
            "recomputed_semantic_digest_sha256": actual,
            "expected_semantic_digest_sha256": expected,
            "canonical_semantic_binding_passed": actual
            == expected
            == payload.get("semantic_digest_sha256"),
        }
    return {
        "records": records,
        "all_canonical_semantic_bindings_passed": all(
            record["canonical_semantic_binding_passed"] for record in records.values()
        ),
        "execution_plan": {
            "path": PLAN_PATH,
            "normalised_LF_text_sha256": _normalised_text_digest(root / PLAN_PATH),
            "binding_kind": "NORMALISED_UTF8_TEXT_BECAUSE_THE_AUTHORITY_IS_MARKDOWN_NOT_JSON",
        },
    }


def _bottom_localization_ledger(
    payload: Mapping[str, Any],
    factor_basis: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], sp.Expr]:
    domain = payload["finite_CSG_identification"]["parameter_domain"]
    factor_records = [
        {
            "factor_id": str(record["factor_id"]),
            "aliases": sorted(record["aliases"]),
            "expression": str(record["polynomial"]),
            "polynomial": _serial_qq_polynomial(record["polynomial"]),
        }
        for record in sorted(factor_basis.values(), key=lambda value: str(value["factor_id"]))
    ]
    declared_factors = {
        _canonical_json(
            _serial_qq_polynomial(
                _normal_polynomial_factor(
                    sp.sympify(expression, locals={str(symbol): symbol for symbol in T_SYMBOLS})
                )
            )
        )
        for expression in domain["nontrivial_lambda_factors"]
    }
    rebuilt_factors = set(factor_basis)
    factor_exponents = {str(record["factor_id"]): 1 for record in factor_basis.values()}
    rebuilt_monic_product = _factor_product(factor_exponents, factor_basis)
    q5 = sp.Symbol("q5")
    declared_product = sp.sympify(
        domain["localising_product"],
        locals={str(symbol): symbol for symbol in (*T_SYMBOLS, q5)},
    )
    active_declared_product = sp.factor(declared_product.subs(q5, 1))
    declared_to_monic_scalar = sp.cancel(active_declared_product / rebuilt_monic_product)
    gates = {
        "fourteen_unique_nontrivial_lambda_factors": len(factor_records) == 14,
        "rebuilt_factor_set_matches_bound_bottom_certificate": declared_factors == rebuilt_factors,
        "active_product_matches_bound_product_after_q5_spectator_drop_up_to_QQ_unit": (
            bool(declared_to_monic_scalar.is_Rational) and declared_to_monic_scalar != 0
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"bottom localization ledger mismatch: {gates}")
    return (
        {
            "coefficient_ring": "QQ[t1,t2,t3,t4][F_lambda^-1]",
            "factor_count": len(factor_records),
            "factors": factor_records,
            "factor_ledger_sha256": _digest(factor_records),
            "F_lambda": str(active_declared_product),
            "F_lambda_polynomial": _serial_qq_polynomial(active_declared_product),
            "F_lambda_polynomial_sha256": _digest(_serial_qq_polynomial(active_declared_product)),
            "rebuilt_monic_factor_product": str(rebuilt_monic_product),
            "declared_to_rebuilt_monic_QQ_unit": str(declared_to_monic_scalar),
            "bound_R54_localising_product": str(declared_product),
            "q5_spectator_removed_product": str(active_declared_product),
            "gates": gates,
            "passed": all(gates.values()),
        },
        active_declared_product,
    )


def build_payload(root: Path, *, progress: ProgressCallback = None) -> dict[str, Any]:
    root = root.resolve()
    report = _progress_reporter(progress)
    predecessors = _predecessor_bindings(root)
    factor_basis = _lambda_factor_basis()
    bottom_localization, active_bottom_localising_product = _bottom_localization_ledger(
        _load(root / bottom_global.RESULT_PATH),
        factor_basis,
    )
    context = torus._build_context(root)  # noqa: SLF001
    operator_context = lattice._build_context(root)  # noqa: SLF001
    # The second return value indexes row labels by block name, not by joint
    # source, so the per-row block is read off the rebuilt symbolic rows below.
    labels = transverse._joint_row_labels(context)[0]  # noqa: SLF001

    independent_rows, upper_symbols, lower_symbols = _rebuild_symbolic_m0_rows(context)
    predecessor_rows = q5_free._symbolic_full_m0_rows(context)  # noqa: SLF001
    independent_match = all(
        left.block == right.block
        and left.joint_source == right.joint_source
        and _symbolic_rows_equal(left.coefficients, right.coefficients)
        for left, right in zip(independent_rows, predecessor_rows, strict=True)
    )
    selected_pivots, _selected_upper, _selected_lower = unit_minor._symbolic_selected_rows(context)  # noqa: SLF001
    by_source_symbolic = {row.joint_source: row.coefficients for row in independent_rows}
    pivots_match = all(
        _symbolic_rows_equal(selected_pivots[index], by_source_symbolic[source])
        for index, source in enumerate(PIVOT_SOURCES)
    )
    if not independent_match or not pivots_match:
        raise AssertionError("independent source or pivot reconstruction failed")

    coordinates = _base_coordinates(
        context,
        operator_context,
        upper_symbols,
        lower_symbols,
    )
    q_variables = tuple(torus._q_variable(context, stage) for stage in range(1, 5))
    q_with_external = (*q_variables, torus.Q5)
    source_rows = {
        row.joint_source: _convert_symbolic_row(row.coefficients, coordinates)
        for row in independent_rows
    }
    source_q5_zero = all(not row.get(torus.Q5) for row in source_rows.values())
    pivot = _pivot_system(context, source_rows, q_with_external)
    frozen_minor = _load(root / unit_minor.RESULT_PATH)["unit_minor_certificate"]
    matching_matches = list(pivot["matching"]) == frozen_minor["perfect_matching"]
    columns_match = list(pivot["non_q"]) == frozen_minor["column_selection"]
    if not matching_matches or not columns_match:
        raise AssertionError("the independently rebuilt pivot matching changed")

    localized_arena = LocalizedArena()
    arena = PolynomialArena()
    reconstruction_ledger = []
    schur_rows_active: dict[int, BaseRow] = {}
    full_spectator_violations = 0
    for symbolic in independent_rows:
        source = symbolic.joint_source
        schur_full, combination, reconstructed = _schur_reduce(
            source_rows[source],
            pivot,
            q_with_external,
        )
        if not reconstructed:
            raise AssertionError(f"Schur reconstruction failed at source {source}")
        if schur_full.get(torus.Q5):
            raise AssertionError(f"Q5 appeared after Schur elimination at source {source}")
        all_polynomials = [
            *source_rows[source].values(),
            *combination.values(),
            *schur_full.values(),
        ]
        spectator_free = all(
            not any(exponent[index] for index in coordinates.dropped_indices)
            for polynomial in all_polynomials
            for exponent in polynomial
        )
        if not spectator_free:
            full_spectator_violations += 1
        schur_active = {
            variable: _project_active(polynomial, coordinates)
            for variable, polynomial in schur_full.items()
            if variable != torus.Q5
        }
        if any(
            _lift_active(polynomial, coordinates) != schur_full[variable]
            for variable, polynomial in schur_active.items()
        ):
            raise AssertionError("52-variable projection failed its inverse round trip")
        schur_rows_active[source] = schur_active
        combination_commitment = []
        for pivot_index, polynomial in sorted(combination.items()):
            combination_commitment.append(
                {
                    "pivot_position": pivot_index,
                    "pivot_joint_source": PIVOT_SOURCES[pivot_index],
                    "coefficient_polynomial_id": localized_arena.intern(polynomial),
                    "coefficient_polynomial_sha256": _poly_digest(polynomial),
                    "coefficient_term_count": len(polynomial),
                }
            )
        reconstruction_ledger.append(
            {
                "joint_source": source,
                "row_id": labels[source],
                "block": symbolic.block,
                "source_row_sha256": _row_digest(source_rows[source]),
                "pivot_combination_nonzero_count": len(combination),
                "pivot_combination_commitment": combination_commitment,
                "pivot_combination_sha256": _digest(combination_commitment),
                "Schur_Q1_Q4_polynomial_ids": {
                    variable: localized_arena.intern(schur_active.get(variable, {}))
                    for variable in q_variables
                },
                "Schur_row_sha256": _row_digest(schur_active),
                "source_equals_pivot_combination_plus_Schur_row": reconstructed,
                "Q5_coefficient_before_elimination_is_zero": not source_rows[source].get(torus.Q5),
                "Q5_coefficient_after_elimination_is_zero": not schur_full.get(torus.Q5),
                "dropped_spectators_absent": spectator_free,
            }
        )
        report(
            "schur_row",
            len(reconstruction_ledger),
            len(independent_rows),
            str(reconstruction_ledger[-1]["Schur_row_sha256"]),
        )

    spectator_drop_passed = full_spectator_violations == 0
    if not spectator_drop_passed:
        raise AssertionError("the 54-to-52 spectator drop is not certified")

    upper_active = {
        variable: _project_active(coordinates.upper_monomials[variable], coordinates)
        for variable in q_variables
    }
    lower_active = {
        variable: _project_active(coordinates.lower_monomials[variable], coordinates)
        for variable in q_variables
    }
    restrictions: dict[
        int,
        tuple[dict[str, LaurentPolynomial], dict[str, LaurentPolynomial]],
    ] = {}
    non_aligned_rows = []
    aligned_base_rows = []
    denominator_records = []
    for source in M0_SOURCES:
        non_aligned, aligned = _restriction_coefficients(
            schur_rows_active[source],
            q_variables,
            upper_active,
            lower_active,
        )
        restrictions[source] = (non_aligned, aligned)
        non_aligned_clearing = _clearing_certificate(
            non_aligned,
            localized_arena,
            arena,
            factor_basis,
        )
        aligned_clearing = _clearing_certificate(
            aligned,
            localized_arena,
            arena,
            factor_basis,
        )
        denominator_records.extend(
            [
                {"joint_source": source, "family": "non_aligned", **non_aligned_clearing},
                {"joint_source": source, "family": "aligned", **aligned_clearing},
            ]
        )
        non_aligned_rows.append(
            {
                "joint_source": source,
                "row_id": labels[source],
                "coefficient_order": ["A", "B"],
                **non_aligned_clearing,
            }
        )
        aligned_base_rows.append(
            {
                "joint_source": source,
                "row_id": labels[source],
                "coefficient_order": ["A", "B2", "B3", "B4"],
                **aligned_clearing,
            }
        )
        report(
            "restriction_row",
            len(non_aligned_rows),
            len(M0_SOURCES),
            _digest([non_aligned_clearing, aligned_clearing]),
        )

    chart_polynomials = _chart_polynomials(context, coordinates)
    chart_records = {
        name: _clearing_certificate(
            {name: polynomial},
            localized_arena,
            arena,
            factor_basis,
        )
        for name, polynomial in chart_polynomials.items()
    }
    for name, record in chart_records.items():
        denominator_records.append({"chart_polynomial": name, **record})
    width = len(coordinates.active_names)
    localization_polynomials = {}
    for name in ("d2", "d3", "d4", "f_tilde"):
        cleared_id = chart_records[name]["cleared_coefficient_polynomial_ids"][name]
        cleared = arena.polynomial(cleared_id)
        localization_polynomials[name] = arena.intern(
            _localization_polynomial(
                cleared,
                width,
                active_bottom_localising_product,
            )
        )

    non_aligned_charts = {}
    for stage in (2, 3, 4):
        chart_name = f"U{stage}"
        manifest_core = {
            "chart": chart_name,
            "ring": f"R0[d{stage}^-1][h]",
            "active_base_variable_count": width,
            "auxiliary_variables": ["h"],
            "generator_count_from_full_M0": len(non_aligned_rows),
            "generators": non_aligned_rows,
            "chart_polynomial": f"d{stage}",
            "chart_polynomial_record": chart_records[f"d{stage}"],
            "planned_Rabinowitsch_localization_polynomial_id": localization_polynomials[
                f"d{stage}"
            ],
            "planned_solver_generator_count_including_Rabinowitsch": len(non_aligned_rows) + 1,
        }
        manifest_core["generator_manifest_sha256"] = _digest(manifest_core["generators"])
        manifest_core["chart_manifest_sha256"] = _digest(manifest_core)
        non_aligned_charts[chart_name] = manifest_core

    aligned_charts = {}
    for fixed in (2, 3, 4):
        other = [stage for stage in (2, 3, 4) if stage != fixed]
        generators = []
        for row in aligned_base_rows:
            coefficient_ids = row["cleared_coefficient_polynomial_ids"]
            generator = {
                "joint_source": row["joint_source"],
                "row_id": row["row_id"],
                "normalization": f"w{fixed}=1",
                "auxiliary_coefficients": {
                    "h": coefficient_ids["A"],
                    f"w{other[0]}": coefficient_ids[f"B{other[0]}"],
                    f"w{other[1]}": coefficient_ids[f"B{other[1]}"],
                    "constant": coefficient_ids[f"B{fixed}"],
                },
                "clearing_scalar": row["clearing_scalar"],
                "clearing_monomial": row["clearing_monomial"],
                "inverse_reconstruction_verified": row["inverse_reconstruction_verified"],
            }
            generators.append(generator)
        chart_name = f"aligned_w{fixed}_equals_1"
        manifest_core = {
            "chart": chart_name,
            "ring": "(R0/(d2,d3,d4))[f_tilde^-1][h,"
            + ",".join(f"w{stage}" for stage in other)
            + "]",
            "active_base_variable_count": width,
            "auxiliary_variables": ["h", *(f"w{stage}" for stage in other)],
            "normalised_obstruction_coordinate": f"w{fixed}=1",
            "generator_count_from_full_M0": len(generators),
            "generators": generators,
            "equal_ratio_quotient_polynomials": {
                name: chart_records[name] for name in ("d2", "d3", "d4")
            },
            "localization_polynomial": "f_tilde",
            "localization_polynomial_record": chart_records["f_tilde"],
            "planned_Rabinowitsch_localization_polynomial_id": localization_polynomials["f_tilde"],
            "planned_solver_generator_count_including_quotient_and_Rabinowitsch": len(generators)
            + 4,
        }
        manifest_core["generator_manifest_sha256"] = _digest(manifest_core["generators"])
        manifest_core["chart_manifest_sha256"] = _digest(manifest_core)
        aligned_charts[chart_name] = manifest_core

    denominator_audit = {
        "record_count": len(denominator_records),
        "records_digest_sha256": _digest(denominator_records),
        "all_denominators_factor_over_rational_upper_Laurent_and_certified_lambda_units": all(
            record["denominator_is_product_of_rational_Laurent_monomial_and_certified_CSG_factors"]
            for record in denominator_records
        ),
        "unknown_denominator_factor_count": sum(
            len(record["unknown_denominator_factors"]) for record in denominator_records
        ),
        "all_bottom_polynomial_clearing_exponents_are_zero": all(
            record["bottom_polynomial_clearing_exponent"] == [0, 0, 0, 0]
            for record in denominator_records
        ),
        "all_cleared_exponents_are_nonnegative": all(
            record["cleared_exponents_are_nonnegative"] for record in denominator_records
        ),
        "all_inverse_reconstructions_verified": all(
            record["inverse_reconstruction_verified"] for record in denominator_records
        ),
        "records": denominator_records,
    }

    cross_checks = _frozen_point_cross_checks(
        context,
        coordinates,
        schur_rows_active,
        restrictions,
        chart_polynomials,
    )

    block_by_source = {row.joint_source: row.block for row in independent_rows}
    source_inventory = [
        {
            "joint_source": source,
            "row_id": labels[source],
            "block": block_by_source[source],
        }
        for source in M0_SOURCES
    ]
    pivot_inventory = [
        {
            "pivot_position": index,
            "joint_source": source,
            "row_id": labels[source],
            "matched_non_Q_column": pivot["non_q"][pivot["matching"][index]],
            "matched_column_index": pivot["matching"][index],
            "diagonal_polynomial_sha256": _poly_digest(pivot["diagonals"][index]),
        }
        for index, source in enumerate(PIVOT_SOURCES)
    ]

    gates = {
        "canonical_semantic_predecessor_bindings": predecessors[
            "all_canonical_semantic_bindings_passed"
        ],
        "independent_1127_source_rebuild_matches_predecessor_compiler": independent_match,
        "independent_127_pivot_rebuild_matches_selected_builder": pivots_match,
        "unique_matching_and_frozen_column_binding_match": matching_matches and columns_match,
        "all_1127_source_equals_pivot_combination_plus_Schur_identities": all(
            record["source_equals_pivot_combination_plus_Schur_row"]
            for record in reconstruction_ledger
        ),
        "Q5_zero_before_and_after_elimination": source_q5_zero
        and all(
            record["Q5_coefficient_after_elimination_is_zero"] for record in reconstruction_ledger
        ),
        "54_to_52_spectator_drop_certified": spectator_drop_passed,
        "bound_fourteen_factor_bottom_localization_ledger_verified": bottom_localization["passed"],
        "denominator_fail_closed_audit_passed": denominator_audit[
            "all_denominators_factor_over_rational_upper_Laurent_and_certified_lambda_units"
        ]
        and denominator_audit["unknown_denominator_factor_count"] == 0
        and denominator_audit["all_bottom_polynomial_clearing_exponents_are_zero"]
        and denominator_audit["all_cleared_exponents_are_nonnegative"]
        and denominator_audit["all_inverse_reconstructions_verified"],
        "three_non_aligned_full_generator_manifests_present": set(non_aligned_charts)
        == {"U2", "U3", "U4"}
        and all(
            chart["generator_count_from_full_M0"] == 1127 for chart in non_aligned_charts.values()
        ),
        "three_aligned_full_generator_manifests_present": len(aligned_charts) == 3
        and all(chart["generator_count_from_full_M0"] == 1127 for chart in aligned_charts.values()),
        "frozen_exact_rational_cross_checks_passed": cross_checks["all_points_in_declared_charts"]
        and cross_checks["all_Schur_rows_match_live_exact_system"]
        and cross_checks["all_restrictions_match_live_exact_system"],
        "candidate_rows_are_scout_only_and_not_terminal_inputs": True,
        "no_solver_or_unit_ideal_claim": True,
    }
    if not all(gates.values()):
        raise AssertionError(f"Phase-A auxiliary manifest gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "finite_scope": {"n_max": 4, "d": 2, "field": "QQ", "nonsingular": True},
        "profile_under_study": "fixed-vector GC plus reachable-state MSR transverse common core M0",
        "authority": predecessors["execution_plan"],
        "predecessor_bindings": predecessors["records"],
        "source_inventory": {
            "M0_row_count": len(source_inventory),
            "block_counts": dict(Counter(record["block"] for record in source_inventory)),
            "source_index_digest_sha256": _digest(list(M0_SOURCES)),
            "row_label_digest_sha256": _digest([labels[source] for source in M0_SOURCES]),
            "inventory_digest_sha256": _digest(source_inventory),
            "rows": source_inventory,
            "independent_rebuild": {
                "builder": "this module's direct CPOBC/path-GC/reachable-MSR traversal",
                "does_not_read_frozen_rows_from_JSON": True,
                "matches_predecessor_source_compiler_row_by_row": independent_match,
            },
        },
        "pivot_inventory": {
            "pivot_row_count": len(pivot_inventory),
            "pivot_source_index_digest_sha256": _digest(list(PIVOT_SOURCES)),
            "pivot_row_label_digest_sha256": _digest([labels[source] for source in PIVOT_SOURCES]),
            "perfect_matching": list(pivot["matching"]),
            "perfect_matching_digest_sha256": _digest(list(pivot["matching"])),
            "unique_perfect_matching": pivot["unique"],
            "alternating_DAG_edges": [list(edge) for edge in pivot["graph_edges"]],
            "alternating_DAG_edges_digest_sha256": _digest(
                [list(edge) for edge in pivot["graph_edges"]]
            ),
            "elimination_order": list(pivot["elimination_order"]),
            "elimination_order_digest_sha256": _digest(list(pivot["elimination_order"])),
            "records": pivot_inventory,
        },
        "base_ring": {
            "initial_dimension": 54,
            "initial_variables": list(coordinates.full_names),
            "dropped_spectators": [
                {"variable": "bottom_q5", "reason": "M0 has no lower external-Q5 source reference"},
                {"variable": "s48", "reason": "the 49th upper-torus kernel column is Q5-only"},
            ],
            "spectator_violation_count": full_spectator_violations,
            "drop_certified": spectator_drop_passed,
            "active_dimension": len(coordinates.active_names),
            "active_variables": list(coordinates.active_names),
            "active_variable_digest_sha256": _digest(list(coordinates.active_names)),
            "active_ring": ("R52=QQ[t1,t2,t3,t4,s0,...,s47][(F_lambda*product(s0,...,s47))^-1]"),
            "bottom_coefficient_ring": "QQ[t1,t2,t3,t4][F_lambda^-1]",
            "bottom_localization_ledger": bottom_localization,
            "pure_Laurent_52_torus_claimed": False,
            "scope_correction": (
                "the 54-dimensional transverse base and its 52-dimensional spectator "
                "quotient are localized rational principal opens, not pure Laurent tori"
            ),
            "projection_inverse_round_trip_verified_for_every_Schur_coefficient": True,
        },
        "Schur_reconstruction": {
            "identity": "source row = sum(pivot coefficient * original pivot row) + Schur row",
            "row_count": len(reconstruction_ledger),
            "all_identities_verified": all(
                record["source_equals_pivot_combination_plus_Schur_row"]
                for record in reconstruction_ledger
            ),
            "Q5_zero_before_count": sum(
                record["Q5_coefficient_before_elimination_is_zero"]
                for record in reconstruction_ledger
            ),
            "Q5_zero_after_count": sum(
                record["Q5_coefficient_after_elimination_is_zero"]
                for record in reconstruction_ledger
            ),
            "ledger_digest_sha256": _digest(reconstruction_ledger),
            "ledger": reconstruction_ledger,
        },
        "chart_cover": {
            "determinant_forms": {name: chart_records[name] for name in ("d2", "d3", "d4")},
            "aligned_open_form": {"f_tilde": chart_records["f_tilde"]},
            "cover": "D(d2) union D(d3) union D(d4) union V(d2,d3,d4)",
            "aligned_split": (
                "D(f_tilde) is active; V(f_tilde) is the predecessor-certified delta_Q=0 safe locus"
            ),
            "ratio_functions_are_declared_unit_equivalent_to_determinant_forms": True,
            "claim_boundary": (
                "cover identity is inherited from the bound Eq120 obligation certificate"
            ),
        },
        "aligned_equal_ratio_SNF_audit": _snf_audit(chart_polynomials, factor_basis),
        "denominator_audit": denominator_audit,
        "localized_coefficient_arena": {
            "upper_Laurent_variable_order": list(coordinates.active_names[4:]),
            "bottom_coefficient_variables": list(coordinates.active_names[:4]),
            "polynomial_count": len(localized_arena.records),
            "records_digest_sha256": _digest(localized_arena.records),
            "records": localized_arena.records,
        },
        "polynomial_arena": {
            "variable_order": list(coordinates.active_names),
            "ring": "QQ[t1,t2,t3,t4,s0,...,s47]",
            "polynomial_count": len(arena.records),
            "records_digest_sha256": _digest(arena.records),
            "records": arena.records,
        },
        "non_aligned_charts": non_aligned_charts,
        "aligned_obstruction_charts": aligned_charts,
        "frozen_exact_rational_cross_checks": cross_checks,
        "scout_only_rows": {
            "non_aligned_candidate_rows": list(NON_ALIGNED_SCOUT_ROWS),
            "aligned_candidate_rows": list(ALIGNED_SCOUT_ROWS),
            "status": "SCOUT_ONLY_NOT_A_GENERATING_SET_NOT_USED_BY_ANY_TERMINAL_GATE",
            "permitted_uses": ["ordering", "factor scouting", "incidence statistics"],
            "terminal_aggregator_input": False,
        },
        "solver_execution": {
            "Sage_started": False,
            "Singular_started": False,
            "Groebner_basis_computed": False,
            "saturation_computed": False,
            "unit_ideal_claimed": False,
            "rational_witness_claimed": False,
            "status": "NO_SOLVER_RUN_PHASE_A_MANIFEST_ONLY",
        },
        "gates": gates,
        "passed": all(gates.values()),
        "verdict": VERDICT,
        "search_terminal": SEARCH_TERMINAL,
        "claim_boundary": (
            "This is a no-Sage Phase-A input manifest. It independently reconstructs and "
            "Schur-reduces all 1,127 M0 rows, certifies Q5-freeness and the 54-to-52 "
            "spectator drop, and freezes six complete auxiliary-generator inputs. It "
            "computes no Groebner basis, saturation, unit ideal, witness, commutativity "
            "theorem, or SR2-V terminal. The aligned 52-to-49 quotient reduction is not "
            "performed because no unimodular forward/inverse map is frozen here."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def render_report(payload: Mapping[str, Any]) -> str:
    cross = payload["frozen_exact_rational_cross_checks"]
    snf = payload["aligned_equal_ratio_SNF_audit"]
    lines = [
        "# SR2-V Q5-free auxiliary-ideal Phase-A manifest",
        "",
        f"Date: {payload['date']}",
        "",
        f"Verdict: `{payload['verdict']}`",
        "",
        f"Semantic digest: `{payload['semantic_digest_sha256']}`",
        "",
        "## Result",
        "",
        "The no-Sage compiler independently rebuilt all 1,127 M0 source rows and the",
        "127-row unit pivot block. Every source row was verified exactly as a pivot",
        "combination plus its four-Q Schur remainder. Q5 is zero before and after",
        "elimination, and the bottom-Q5 and upper Q5-only scalar directions are absent",
        "from every relevant Laurent coefficient; the active base is therefore 52-dimensional.",
        "",
        "The complete generator manifests are frozen for `U2`, `U3`, `U4` and the three",
        "aligned affine obstruction charts. No row sample replaces the full 1,127-row list.",
        "",
        "## Exact gates",
        "",
        f"- Source reconstruction rows: {payload['source_inventory']['M0_row_count']}",
        f"- Pivot rows: {payload['pivot_inventory']['pivot_row_count']}",
        f"- Laurent polynomial arena entries: {payload['polynomial_arena']['polynomial_count']}",
        f"- Denominator records: {payload['denominator_audit']['record_count']}",
        f"- Frozen rational points: {cross['point_count']} (all mismatch counts zero)",
        (
            "- Aligned exponent-lattice rank/invariants: "
            f"{snf.get('rank')} / {snf.get('smith_invariant_factors')}"
        ),
        f"- Aligned 52-to-49 reduction performed: {snf['reduction_performed']}",
        "",
        "## Scope boundary",
        "",
        payload["claim_boundary"],
        "",
        "Rows `(8,11)` and `(8,27,97)` remain scout-only metadata for ordering or",
        "factor/incidence exploration. They are not a generating-set, completeness, or",
        "global claim.",
        "",
    ]
    return "\n".join(lines)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Stream the payload to disk.

    ``json.dumps`` materialises every chunk in a list before joining it, which
    exhausts memory on the full 1,127-row manifest.  ``json.dump`` writes the
    same bytes incrementally.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _lightweight_base_ring_certificate(root: Path) -> dict[str, Any]:
    """Rebuild only the transverse scalar coordinates, never the 1,127 rows."""

    context = torus._build_context(root)  # noqa: SLF001
    operator_context = lattice._build_context(root)  # noqa: SLF001
    upper_symbols = {
        variable: sp.Symbol(f"base_a{index}") for index, variable in enumerate(context.variables)
    }
    lower_symbols = {
        variable: sp.Symbol(f"base_b{index}") for index, variable in enumerate(context.variables)
    }
    coordinates = _base_coordinates(
        context,
        operator_context,
        upper_symbols,
        lower_symbols,
    )
    q5_index = context.variables.index(torus.Q5)
    kernel_supports = [
        [index for index, value in enumerate(column) if value] for column in coordinates.kernel
    ]
    q5_only_columns = [
        index for index, support in enumerate(kernel_supports) if support == [q5_index]
    ]
    bottom_q5_violations = [
        variable
        for variable, polynomial in coordinates.lower_monomials.items()
        if variable != torus.Q5
        and (
            any(exponent[4] for exponent in polynomial)
            or any(
                BOTTOM_Q5_SYMBOL in _coefficient_free_symbols(coefficient)
                for coefficient in polynomial.values()
            )
        )
    ]
    expected_active_names = (*map(str, T_SYMBOLS), *(f"s{index}" for index in range(48)))
    reconstructed_ring = (
        "R52=QQ["
        + ",".join(coordinates.active_names[:4])
        + ",s0,...,s47][(F_lambda*product(s0,...,s47))^-1]"
    )
    gates = {
        "upper_kernel_has_shape_49_by_132": len(coordinates.kernel) == 49
        and all(len(column) == 132 for column in coordinates.kernel),
        "unique_Q5_only_upper_column_is_48": q5_only_columns == [48],
        "Q5_only_upper_column_support_is_Q5_index": kernel_supports[48] == [q5_index],
        "non_Q5_bottom_formulas_are_bottom_q5_free": not bottom_q5_violations,
        "active_names_are_exactly_t1_to_t4_then_s0_to_s47": coordinates.active_names
        == expected_active_names,
        "spectator_indices_are_exactly_bottom_q5_and_s48": coordinates.dropped_indices == (4, 53),
        "reconstructed_active_ring_equals_declared_R52": reconstructed_ring == ACTIVE_RING,
    }
    if not all(gates.values()):
        raise AssertionError(f"lightweight base-ring certificate failed: {gates}")
    return {
        "builder_scope": "scalar coordinates only; no M0 source-row compiler invoked",
        "upper_kernel_storage_shape": [len(coordinates.kernel), len(coordinates.kernel[0])],
        "context_variable_count": len(context.variables),
        "Q5_context_index": q5_index,
        "Q5_only_upper_columns": q5_only_columns,
        "Q5_only_upper_column_support": kernel_supports[48],
        "bottom_q5_violation_count": len(bottom_q5_violations),
        "bottom_q5_violations": bottom_q5_violations,
        "full_variable_count": len(coordinates.full_names),
        "dropped_spectator_indices": list(coordinates.dropped_indices),
        "dropped_spectator_names": [
            coordinates.full_names[index] for index in coordinates.dropped_indices
        ],
        "active_variable_count": len(coordinates.active_names),
        "active_variables": list(coordinates.active_names),
        "active_variable_digest_sha256": _digest(list(coordinates.active_names)),
        "reconstructed_active_ring": reconstructed_ring,
        "declared_active_ring": ACTIVE_RING,
        "gates": gates,
        "passed": all(gates.values()),
    }


def build_resource_open_payload(root: Path) -> dict[str, Any]:
    """Freeze machine-certified inputs and a non-certified local attempt observation."""

    root = root.resolve()
    predecessors = _predecessor_bindings(root)
    factor_basis = _lambda_factor_basis()
    bottom_localization, _active_product = _bottom_localization_ledger(
        _load(root / bottom_global.RESULT_PATH),
        factor_basis,
    )
    base_ring_certificate = _lightweight_base_ring_certificate(root)
    gates = {
        "canonical_semantic_predecessor_bindings": predecessors[
            "all_canonical_semantic_bindings_passed"
        ],
        "bound_fourteen_factor_bottom_localization_ledger_verified": bottom_localization["passed"],
        "lightweight_spectator_and_R52_base_certificate": base_ring_certificate["passed"],
        "full_1127_source_Schur_ledger_generated": False,
        "full_six_chart_generator_manifests_generated": False,
        "denominator_inverse_reconstruction_ledger_completed": False,
        "no_solver_or_unit_ideal_claim": True,
    }
    attempt_provenance = {
        "classification": "MANUALLY_RECORDED_LOCAL_OBSERVATION",
        "attempt_provenance_machine_reproducible": False,
        "source_snapshot_available": False,
        "source_snapshot_sha256_available": False,
        "raw_monitor_log_available": False,
        "timeout_exit_record_available": False,
        "file_probe_record_available": False,
        "stdout_sha256_available": False,
        "stderr_sha256_available": False,
        "current_command_reproduces_attempt": False,
        "partial_source_rebuild_progress_machine_certified": False,
        "partial_pivot_progress_machine_certified": False,
        "partial_Schur_row_progress_machine_certified": False,
        "certified_partial_completion_count": None,
        "reason": (
            "no immutable source snapshot/hash, raw monitor log, timeout exit record, "
            "file-probe transcript, or stdout/stderr hashes were preserved; the module's "
            "current main writes this checkpoint and does not rerun the observed full build"
        ),
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "finite_scope": {"n_max": 4, "d": 2, "field": "QQ", "nonsingular": True},
        "profile_under_study": (
            "fixed-vector GC plus reachable-state MSR transverse common core M0"
        ),
        "authority": predecessors["execution_plan"],
        "predecessor_bindings": predecessors["records"],
        "machine_certified_scope": {
            "scope": (
                "canonical predecessor bindings, the bound fourteen-factor bottom "
                "localization, and the independently rebuilt lightweight spectator/R52 gate"
            ),
            "bottom_localization_ledger": bottom_localization,
            "lightweight_base_ring_certificate": base_ring_certificate,
            "active_ring": ACTIVE_RING,
            "pure_Laurent_52_torus_claimed": False,
        },
        "resource_attempt_provenance": attempt_provenance,
        "bounded_attempt": {
            "provenance": "MANUALLY_RECORDED_LOCAL_OBSERVATION",
            "kind": "NO_SAGE_FULL_1127_ROW_PHASE_A_MANIFEST_BUILD",
            "manually_recorded_command": (
                "uv run python -m universe_lab.final_theory."
                "sr2v_q5_free_auxiliary_ideal_manifest_v042"
            ),
            "current_module_command_behavior": (
                "the same command now invokes checkpoint main and does not reproduce "
                "the manually observed full-build attempt"
            ),
            "manually_recorded_started_at": "2026-08-02T22:46:56+09:00",
            "manually_recorded_stopped_at": "2026-08-02T23:46:58+09:00",
            "declared_hard_request_limit_seconds": 3600,
            "manually_observed_wall_seconds_at_stop": 3602,
            "manually_observed_last_CPU_seconds": "3517.109375",
            "manually_observed_last_working_set_bytes": 688783360,
            "manually_observed_process_id": 42216,
            "manual_status": (
                "the process was manually observed to remain active near the declared "
                "limit and was stopped after the polling boundary; enforcement is not "
                "machine-certified by this artifact"
            ),
            "partial_progress_claimed": False,
        },
        "manually_recorded_solver_observation": {
            "provenance": "MANUALLY_RECORDED_LOCAL_OBSERVATION",
            "Sage_started": False,
            "Singular_started": False,
            "Groebner_basis_computed": False,
            "saturation_computed": False,
            "unit_ideal_claimed": False,
            "rational_witness_claimed": False,
        },
        "gates": gates,
        "passed": False,
        "verdict": OPEN_VERDICT,
        "search_terminal": SEARCH_TERMINAL,
        "claim_boundary": (
            "Only the canonical bound inputs, fourteen-factor bottom localization, and "
            "lightweight spectator/corrected-R52 reconstruction are machine-certified. "
            "All resource-attempt times, CPU/RSS values, process state, and solver/file "
            "observations are manually recorded local observations without a source "
            "snapshot or raw audit transcript. The complete 1,127-row Schur ledger, six "
            "generator manifests, denominator inverse ledger, Groebner/unit-ideal claims, "
            "witness claims, commutativity claims, and every SR2-V terminal remain open. "
            "The manual timeout observation is not a mathematical counterexample or a "
            "machine-reproducible resource certificate."
        ),
        "recommended_next_step": (
            "add deterministic row checkpoints and replace per-operation SymPy cancel "
            "with a cached fraction-field representation before rerunning Phase A"
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def render_resource_open_report(payload: Mapping[str, Any]) -> str:
    attempt = payload["bounded_attempt"]
    return "\n".join(
        [
            "# SR2-V Q5-free auxiliary-ideal Phase-A resource checkpoint",
            "",
            f"Date: {payload['date']}",
            "",
            f"Verdict: `{payload['verdict']}`",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Outcome",
            "",
            "The canonical inputs, fourteen-factor bottom localization, and lightweight",
            "spectator/R52 reconstruction are machine-certified. The attempted full-build",
            "resource metrics below are manually recorded local observations only.",
            "This is a resource-open status, not a resource certificate, mathematical",
            "failure, counterexample, or witness.",
            "",
            "## Manually recorded local observation",
            "",
            f"- Start: `{attempt['manually_recorded_started_at']}`",
            f"- Stop: `{attempt['manually_recorded_stopped_at']}`",
            (
                "- Manually observed wall time: "
                f"{attempt['manually_observed_wall_seconds_at_stop']} s"
            ),
            (
                "- Manually observed last CPU time: "
                f"{attempt['manually_observed_last_CPU_seconds']} s"
            ),
            (
                "- Manually observed last working set: "
                f"{attempt['manually_observed_last_working_set_bytes']} bytes"
            ),
            "- Immutable source snapshot/hash: unavailable",
            "- Raw monitor/timeout/file-probe transcript: unavailable",
            "- stdout/stderr hashes: unavailable",
            "- Current module command reproduces the attempt: false",
            "- Partial source, pivot, or Schur progress machine-certified: false",
            "",
            "## Scope boundary",
            "",
            str(payload["claim_boundary"]),
            "",
            "## Next implementation gate",
            "",
            str(payload["recommended_next_step"]),
            "",
        ]
    )


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    payload = build_resource_open_payload(root)
    _write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(
        render_resource_open_report(payload),
        encoding="utf-8",
        newline="\n",
    )
    print(
        _canonical_json(
            {
                "verdict": payload["verdict"],
                "semantic_digest_sha256": payload["semantic_digest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
