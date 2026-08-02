"""Exact additive-MSR equations on the SR2-V ``G_m^29`` scalar torus.

The scalar-lattice certificate supplies a primitive 29-coordinate Laurent
parameterisation of the observed diagonal character.  This module substitutes
that map into all 24 source-matched additive MSR equations.  It then certifies
an exact normalized-CSG rational point and the full logarithmic Jacobian rank
there.

The result is local algebraic geometry, not a global classification.  It does
not solve the upper-right cocycle fibre, run a solver, or issue an SR2-V search
terminal.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

RESULT_PATH = "results/v0.4.2_sr2v_additive_msr_laurent.json"
SCHEMA = "final-theory-v042-sr2v-additive-msr-laurent-v1"
VERDICT = "SR2V_ADDITIVE_MSR_LAURENT_SMOOTH_CSG_POINT_CERTIFIED_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_LOCAL_SCALAR_GEOMETRY_ONLY"

EXPECTED_EQUATION_COUNT = 24
EXPECTED_JACOBIAN_RANK = 24
EXPECTED_LOCAL_DIMENSION = 5
EXPECTED_MINOR_DETERMINANT = Fraction(-5, 2**45)

Exponent = tuple[int, ...]
LaurentPolynomial = dict[Exponent, Fraction]


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


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _fraction(value: sp.Expr) -> Fraction:
    rational = sp.Rational(value)
    return Fraction(int(rational.p), int(rational.q))


def _csg_exponent(record: dict[str, Any]) -> int:
    stage = int(record["stage"])
    relation = tuple(int(row) for row in record["source_relation_rows"])
    precursor = int(record["precursor_code"])
    return (
        precursor.bit_count()
        - len(maximal_elements_in_subset(relation, precursor))
        - stage
    )


def _normalized_csg_exponents(
    context: lattice.LatticeContext,
) -> dict[str, int]:
    result: dict[str, int] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        exponent = _csg_exponent(record)
        previous = result.setdefault(variable, exponent)
        if previous != exponent:
            raise AssertionError("the normalized CSG character is not constant on an ON orbit")
    result[lattice.Q5] = -5
    return result


def _kernel_matrix(payload: dict[str, Any]) -> sp.Matrix:
    columns = payload["observed_bottom_plus_fixed_GC_block"]["integer_kernel"][
        "basis_columns"
    ]
    matrix = sp.Matrix.hstack(*(sp.Matrix(column) for column in columns))
    if matrix.shape != (132, 29) or matrix.rank() != 29:
        raise AssertionError("the primitive G_m^29 kernel shape changed")
    return matrix


def _parameter_exponents(kernel: sp.Matrix, point: sp.Matrix) -> tuple[int, ...]:
    solution_set = sp.linsolve((kernel, point))
    if len(solution_set) != 1:
        raise AssertionError("the CSG point has no unique G_m^29 coordinate lift")
    solution = tuple(next(iter(solution_set)))
    if len(solution) != kernel.cols or any(value.free_symbols for value in solution):
        raise AssertionError("the CSG Laurent-coordinate lift is not unique")
    fractions = tuple(_fraction(value) for value in solution)
    if any(value.denominator != 1 for value in fractions):
        raise AssertionError("the CSG Laurent-coordinate lift is not integral")
    return tuple(value.numerator for value in fractions)


def _clean(polynomial: dict[Exponent, Fraction]) -> LaurentPolynomial:
    return {exponent: value for exponent, value in polynomial.items() if value}


def _add_term(
    polynomial: defaultdict[Exponent, Fraction],
    exponent: Exponent,
    coefficient: Fraction | int,
) -> None:
    polynomial[exponent] += Fraction(coefficient)


def _equations(
    context: lattice.LatticeContext,
    kernel: sp.Matrix,
) -> list[tuple[str, str, LaurentPolynomial]]:
    positions = {variable: index for index, variable in enumerate(context.variables)}
    zero = (0,) * kernel.cols
    equations: list[tuple[str, str, LaurentPolynomial]] = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        polynomial: defaultdict[Exponent, Fraction] = defaultdict(Fraction)
        _add_term(polynomial, zero, int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            variable = context.occurrence_variables[str(term["transition_id"])]
            row = positions[variable]
            exponent = tuple(int(kernel[row, column]) for column in range(kernel.cols))
            _add_term(polynomial, exponent, int(term["coefficient"]))
        equations.append(
            (
                str(constraint["constraint_id"]),
                str(constraint["source_id"]),
                _clean(dict(polynomial)),
            )
        )
    if len(equations) != EXPECTED_EQUATION_COUNT:
        raise AssertionError("the additive MSR equation count changed")
    return equations


def _evaluate_at_power_point(
    polynomial: LaurentPolynomial,
    parameter_exponents: tuple[int, ...],
) -> Fraction:
    total = Fraction(0)
    for exponent, coefficient in polynomial.items():
        power = sum(
            left * right
            for left, right in zip(exponent, parameter_exponents, strict=True)
        )
        total += coefficient * (Fraction(2) ** power)
    return total


def _logarithmic_jacobian(
    equations: list[tuple[str, str, LaurentPolynomial]],
    parameter_exponents: tuple[int, ...],
) -> sp.Matrix:
    rows: list[list[sp.Rational]] = []
    for _, _, polynomial in equations:
        row = [Fraction(0) for _ in parameter_exponents]
        for exponent, coefficient in polynomial.items():
            power = sum(
                left * right
                for left, right in zip(exponent, parameter_exponents, strict=True)
            )
            value = coefficient * (Fraction(2) ** power)
            for column, monomial_power in enumerate(exponent):
                row[column] += value * monomial_power
        rows.append(
            [sp.Rational(value.numerator, value.denominator) for value in row]
        )
    return sp.Matrix(rows)


def _serialize_vector(vector: sp.Matrix, names: tuple[str, ...]) -> list[dict[str, str]]:
    return [
        {"coordinate": names[index], "coefficient": str(_fraction(value))}
        for index, value in enumerate(vector)
        if value
    ]


def _serialize_polynomial(
    polynomial: LaurentPolynomial,
    names: tuple[str, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": str(polynomial[exponent]),
            "monomial": [
                {"coordinate": names[index], "exponent": power}
                for index, power in enumerate(exponent)
                if power
            ],
        }
        for exponent in sorted(polynomial)
    ]


def _cleared_polynomial(polynomial: LaurentPolynomial) -> tuple[Exponent, LaurentPolynomial]:
    width = len(next(iter(polynomial)))
    shift = tuple(
        max(0, -min(exponent[index] for exponent in polynomial))
        for index in range(width)
    )
    cleared = {
        tuple(value + shift[index] for index, value in enumerate(exponent)): coefficient
        for exponent, coefficient in polynomial.items()
    }
    return shift, _clean(cleared)


def build_payload(root: Path) -> dict[str, Any]:
    """Compile and certify the 24 additive equations on ``G_m^29``."""

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

    csg_exponents = _normalized_csg_exponents(context)
    point = sp.Matrix([csg_exponents.get(variable, 0) for variable in context.variables])
    parameter_exponents = _parameter_exponents(kernel, point)
    if kernel * sp.Matrix(parameter_exponents) != point:
        raise AssertionError("the displayed Laurent point does not map to the CSG character")

    coordinate_names = tuple(f"t:{index:02d}" for index in range(kernel.cols))
    equations = _equations(context, kernel)
    residuals = [
        _evaluate_at_power_point(polynomial, parameter_exponents)
        for _, _, polynomial in equations
    ]
    if any(residuals):
        raise AssertionError("the normalized CSG point violates additive MSR")

    jacobian = _logarithmic_jacobian(equations, parameter_exponents)
    jacobian_rank = int(jacobian.rank())
    column_pivots = tuple(int(value) for value in jacobian.rref()[1])
    row_pivots = tuple(int(value) for value in jacobian.T.rref()[1])
    minor = jacobian.extract(row_pivots, column_pivots)
    minor_determinant = _fraction(minor.det())
    tangent_basis = jacobian.nullspace()
    mapped_tangents = [kernel * vector for vector in tangent_basis]
    q5_position = context.variables.index(lattice.Q5)
    pure_q5 = [
        index
        for index, vector in enumerate(mapped_tangents)
        if vector[q5_position]
        and all(not vector[row] for row in range(len(context.variables)) if row != q5_position)
    ]
    actual_tangent_count = len(tangent_basis) - len(pure_q5)

    equation_records: list[dict[str, Any]] = []
    all_support: set[int] = set()
    for (constraint_id, source_id, polynomial), residual in zip(
        equations,
        residuals,
        strict=True,
    ):
        shift, cleared = _cleared_polynomial(polynomial)
        support = sorted(
            {
                index
                for exponent in polynomial
                for index, value in enumerate(exponent)
                if value
            }
        )
        all_support.update(support)
        equation_records.append(
            {
                "constraint_id": constraint_id,
                "source_id": source_id,
                "laurent_terms": _serialize_polynomial(polynomial, coordinate_names),
                "laurent_term_count": len(polynomial),
                "clearing_monomial": [
                    {"coordinate": coordinate_names[index], "exponent": value}
                    for index, value in enumerate(shift)
                    if value
                ],
                "cleared_polynomial_terms": _serialize_polynomial(
                    cleared,
                    coordinate_names,
                ),
                "residual_at_normalized_CSG_point": str(residual),
            }
        )

    stage_counts = Counter(source_id.split("-", maxsplit=1)[0] for _, source_id, _ in equations)
    q5_coordinate = coordinate_names[-1]
    q5_absent = (kernel[q5_position, kernel.cols - 1] == 1) and all(
        kernel[row, kernel.cols - 1] == 0
        for row in range(kernel.rows)
        if row != q5_position
    ) and (kernel.cols - 1 not in all_support)

    gates = {
        "primitive_Gm29_lattice_is_bound": kernel.shape == (132, 29),
        "all_24_additive_MSR_equations_are_compiled": len(equations) == 24,
        "source_stage_counts_are_1_2_5_16": dict(sorted(stage_counts.items()))
        == {"p1": 1, "p2": 2, "p3": 5, "p4": 16},
        "normalized_CSG_point_is_exact_rational_and_satisfies_all_equations": not any(
            residuals
        ),
        "logarithmic_Jacobian_has_full_row_rank_24": jacobian_rank
        == EXPECTED_JACOBIAN_RANK,
        "selected_24_minor_is_exact_nonzero": minor_determinant
        == EXPECTED_MINOR_DETERMINANT,
        "local_dimension_inside_Gm29_is_5": kernel.cols - jacobian_rank
        == EXPECTED_LOCAL_DIMENSION,
        "one_tangent_and_global_factor_is_cutoff_external_Q5": len(pure_q5) == 1
        and q5_absent,
        "four_actual_edge_scalar_tangent_directions_remain": actual_tangent_count == 4,
    }
    if not all(gates.values()):
        raise AssertionError(f"additive-MSR Laurent gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "finite_scope": "n<=4",
        "dimension": 2,
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "field": {
            "equations_and_point": "QQ Laurent arithmetic",
            "exponent_lattice": "ZZ",
            "jacobian_rank": "QQ",
            "floating_point_used": False,
            "finite_field_used": False,
        },
        "input_artifacts": {
            lattice.RESULT_PATH: {
                "raw_sha256": _sha256(root / lattice.RESULT_PATH),
                "semantic_digest_sha256": frozen_lattice["semantic_digest_sha256"],
            },
            lattice.CPOBC_PATH: {"raw_sha256": _sha256(root / lattice.CPOBC_PATH)},
            lattice.REDUCTION_PATH: {"raw_sha256": _sha256(root / lattice.REDUCTION_PATH)},
        },
        "laurent_parameterisation": {
            "ambient_locus": "split G_m^29",
            "source_kernel_shape": [kernel.rows, kernel.cols],
            "coordinate_names": list(coordinate_names),
            "map": "p_e=product_j t_j^K_ej using the bound primitive kernel",
            "cutoff_external_Q5_coordinate": q5_coordinate,
            "Q5_is_an_exact_global_Gm_factor_of_the_additive_MSR_locus": q5_absent,
        },
        "additive_MSR_system": {
            "equation_count": len(equations),
            "source_stage_counts": dict(sorted(stage_counts.items())),
            "Q5_coordinate_occurs": kernel.cols - 1 in all_support,
            "equations": equation_records,
            "system_digest_sha256": hashlib.sha256(
                _canonical_json(equation_records).encode("utf-8")
            ).hexdigest(),
        },
        "normalized_CSG_point": {
            "base": 2,
            "torus_coordinate_exponents": list(parameter_exponents),
            "torus_coordinate_values": [str(Fraction(2) ** value) for value in parameter_exponents],
            "transition_character_exponents_in_variable_order": [
                csg_exponents.get(variable, 0) for variable in context.variables
            ],
            "all_24_residuals": [str(value) for value in residuals],
            "all_coordinates_nonzero": True,
        },
        "smooth_local_certificate": {
            "logarithmic_derivative": "t_j*d/dt_j",
            "jacobian_shape": [jacobian.rows, jacobian.cols],
            "jacobian_rank": jacobian_rank,
            "independent_constraint_ids": [equations[index][0] for index in row_pivots],
            "minor_row_indices": list(row_pivots),
            "minor_column_indices": list(column_pivots),
            "minor_coordinates": [coordinate_names[index] for index in column_pivots],
            "minor_determinant": str(minor_determinant),
            "local_dimension_inside_Gm29": kernel.cols - jacobian_rank,
            "tangent_kernel_rank": len(tangent_basis),
            "tangent_basis": [
                _serialize_vector(vector, coordinate_names) for vector in tangent_basis
            ],
            "pure_Q5_tangent_basis_indices": pure_q5,
            "actual_edge_scalar_tangent_dimension": actual_tangent_count,
            "interpretation": (
                "the 24 additive equations cut a smooth codimension-24 locus at the "
                "normalized CSG point; the local dimension is 5, with one exact "
                "global G_m factor belonging only to cutoff-external Q5"
            ),
        },
        "resource_and_claim_boundaries": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "sage_status": "NOT_INVOKED",
            "global_additive_MSR_variety_classified": False,
            "upper_right_cocycle_fibre_solved": False,
            "commutator_open_tested": False,
            "next_exact_gate": (
                "use the four actual-edge tangent directions to choose structured local "
                "coordinates, or classify the cleared Laurent system globally before "
                "coupling it to upper-right cocycle and visibility equations"
            ),
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "This exact certificate compiles all 24 additive MSR equations on the bound "
            "primitive G_m^29 scalar torus and proves a smooth rational point of local "
            "dimension five, including the cutoff-external Q5 factor.  It is not a global "
            "classification of the additive locus, does not solve the upper-right cocycle "
            "fibre, and is not a commutativity theorem, witness, obstruction, chart cover, "
            "solver result, or SR2-V terminal."
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
