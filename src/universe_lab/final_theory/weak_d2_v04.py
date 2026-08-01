"""Exact v0.4 weak-semantics audit for the finite CPOBC ``d=2`` system.

The module deliberately starts from a rational counterexample rather than an
elimination campaign.  Every frozen CPOBC word equation, fixed-vector GC path
pair, reachable-state MSR constraint, both Eq. (113) index branches, and both
literal readings of the Eq. (139) index domain is evaluated directly.

The witness is upper triangular.  This is a construction, not an ansatz used
to claim completeness: exact triangular linear algebra is reported separately
and labelled as a bounded scout for the two one-sided semantic profiles.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

VERDICT = "WEAK_D2_NONCOMMUTATIVE_WITNESS_CERTIFIED"
EQ139_PRINTED_STRICT = "EQ139_PRINTED_STRICT_M_K_LT_N"
EQ139_EQ145_COMPLETED = "EQ139_EQ145_COMPLETED_M_K_LE_N"
EQ113_DERIVED = "EQ113_QN_BRANCH"
EQ113_LITERAL = "EQ113_QN_PLUS_1_BRANCH"

Matrix2 = tuple[
    tuple[Fraction, Fraction],
    tuple[Fraction, Fraction],
]
Vector2 = tuple[Fraction, Fraction]

ZERO: Matrix2 = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0)))
IDENTITY: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
OMEGA: Vector2 = (Fraction(1), Fraction(0))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fraction(value: Fraction | int) -> str:
    return str(Fraction(value))


def _matrix_record(matrix: Matrix2) -> list[list[str]]:
    return [[_fraction(entry) for entry in row] for row in matrix]


def _vector_record(vector: Vector2) -> list[str]:
    return [_fraction(entry) for entry in vector]


def _matrix_add(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(left[row][column] + right[row][column] for column in range(2)) for row in range(2)
    )  # type: ignore[return-value]


def _matrix_subtract(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(2)) for row in range(2)
    )  # type: ignore[return-value]


def _matrix_scale(coefficient: Fraction | int, matrix: Matrix2) -> Matrix2:
    scalar = Fraction(coefficient)
    return tuple(tuple(scalar * matrix[row][column] for column in range(2)) for row in range(2))  # type: ignore[return-value]


def _matrix_multiply(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(
            sum(
                (left[row][middle] * right[middle][column] for middle in range(2)),
                Fraction(0),
            )
            for column in range(2)
        )
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_word(factors: Iterable[Matrix2]) -> Matrix2:
    product = IDENTITY
    for factor in factors:
        product = _matrix_multiply(product, factor)
    return product


def _determinant(matrix: Matrix2) -> Fraction:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _matrix_inverse(matrix: Matrix2) -> Matrix2:
    determinant = _determinant(matrix)
    if determinant == 0:
        raise ZeroDivisionError("the witness unexpectedly contains a singular matrix")
    return (
        (matrix[1][1] / determinant, -matrix[0][1] / determinant),
        (-matrix[1][0] / determinant, matrix[0][0] / determinant),
    )


def _matrix_apply(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def _commutator(left: Matrix2, right: Matrix2) -> Matrix2:
    return _matrix_subtract(
        _matrix_multiply(left, right),
        _matrix_multiply(right, left),
    )


def _relation_code(relation: tuple[int, ...]) -> int:
    size = len(relation)
    return sum(row << (index * size) for index, row in enumerate(relation))


def _csg_diagonal(
    stage: int,
    source_relation_rows: Iterable[int],
    precursor_code: int,
    *,
    coupling_ratio: int | None,
) -> Fraction:
    """Return a CSG transition probability.

    ``coupling_ratio=None`` means ``t_j=1`` and gives
    ``2**(w-m)/2**n``.  A positive integer ``r`` means ``t_j=r**j`` and
    gives ``r**m * (1+r)**(w-m) / (1+r)**n``.
    """

    relation = tuple(int(row) for row in source_relation_rows)
    width = precursor_code.bit_count()
    maximal_count = len(maximal_elements_in_subset(relation, precursor_code))
    if coupling_ratio is None:
        return Fraction(2 ** (width - maximal_count), 2**stage)
    ratio = coupling_ratio
    return Fraction(
        ratio**maximal_count * (1 + ratio) ** (width - maximal_count),
        (1 + ratio) ** stage,
    )


def transition_witness(
    stage: int,
    source_relation_rows: Iterable[int],
    precursor_code: int,
) -> Matrix2:
    """Return the exact rational transition used by the counterexample."""

    probability = _csg_diagonal(
        stage,
        source_relation_rows,
        precursor_code,
        coupling_ratio=None,
    )
    gregarious_entry = Fraction(4, 2**stage) if precursor_code == 0 else Fraction(0)
    return ((probability, gregarious_entry), (Fraction(0), Fraction(1)))


def q_witness(stage: int) -> Matrix2:
    return transition_witness(stage, (0,) * stage, 0)


def antichain_transition_witness(stage: int, precursor_size: int) -> Matrix2:
    if not 0 <= precursor_size <= stage:
        raise ValueError("the precursor size must lie between zero and the stage")
    return transition_witness(stage, (0,) * stage, (1 << precursor_size) - 1)


def eq139_instances(domain: str) -> tuple[tuple[int, int, int], ...]:
    """Enumerate Eq. (139) without merging its inconsistent source readings."""

    instances: list[tuple[int, int, int]] = []
    for stage in (2, 3, 4):
        if domain == EQ139_PRINTED_STRICT:
            indices = range(1, stage)
        elif domain == EQ139_EQ145_COMPLETED:
            indices = range(1, stage + 1)
        else:
            raise ValueError(f"unknown Eq. (139) domain: {domain}")
        instances.extend((stage, left, right) for left, right in itertools.combinations(indices, 2))
    return tuple(instances)


def _eq139_residual(stage: int, left_index: int, right_index: int) -> Matrix2:
    left_transition = antichain_transition_witness(stage, left_index)
    right_transition = antichain_transition_witness(stage, right_index)
    current_q = q_witness(stage)
    next_q = q_witness(stage + 1)
    left = _matrix_word(
        (
            left_transition,
            right_transition,
            next_q,
            _matrix_inverse(right_transition),
            _matrix_inverse(current_q),
            right_transition,
        )
    )
    right = _matrix_word(
        (
            right_transition,
            left_transition,
            next_q,
            _matrix_inverse(left_transition),
            _matrix_inverse(current_q),
            left_transition,
        )
    )
    return _matrix_subtract(left, right)


def _transition_assignments(reduction: dict[str, Any]) -> dict[str, Matrix2]:
    return {
        record["occurrence_id"]: transition_witness(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        for record in reduction["reduction_map"]
    }


def _evaluate_cpobc(
    cpobc: dict[str, Any],
    assignments: dict[str, Matrix2],
) -> dict[str, Any]:
    records = []
    for relation in cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            lhs = _matrix_word(assignments[operator_ids[token]] for token in equation["lhs_word"])
            rhs = _matrix_word(assignments[operator_ids[token]] for token in equation["rhs_word"])
            residual = _matrix_subtract(lhs, rhs)
            records.append(
                {
                    "relation_id": relation["relation_id"],
                    "equation_id": equation["equation_id"],
                    "residual": _matrix_record(residual),
                    "zero": residual == ZERO,
                }
            )
    return {
        "checked_equations": len(records),
        "expected_equations": cpobc["counts"]["denominator_cleared_word_equations"],
        "records": records,
        "all_zero": all(record["zero"] for record in records),
    }


def _evaluate_cpobc_inverse_forms(
    cpobc: dict[str, Any],
    assignments: dict[str, Matrix2],
) -> dict[str, Any]:
    """Directly check the inverse-containing Eqs. (105)/(106) rewrites."""

    records = []
    for relation in cpobc["relations"]:
        operator_ids: dict[str, str] = {}
        for raw_equation in relation["raw_noncommutative_relation"]:
            operator_ids.update(raw_equation["operator_ids"])
        for equation in relation["inverse_containing_form"]["forms"]:
            residual = ZERO
            for term in equation["residual_terms"]:
                factors = []
                for token in term["word"]:
                    inverse = token.endswith("^-1")
                    alias = token.removesuffix("^-1")
                    factor = assignments[operator_ids[alias]]
                    factors.append(_matrix_inverse(factor) if inverse else factor)
                residual = _matrix_add(
                    residual,
                    _matrix_scale(int(term["coefficient"]), _matrix_word(factors)),
                )
            records.append(
                {
                    "relation_id": relation["relation_id"],
                    "equation_id": equation["equation_id"],
                    "residual": _matrix_record(residual),
                    "zero": residual == ZERO,
                }
            )
    return {
        "checked_inverse_containing_equations": len(records),
        "records": records,
        "all_zero": all(record["zero"] for record in records),
    }


def _evaluate_msr(
    cpobc: dict[str, Any],
    assignments: dict[str, Matrix2],
) -> dict[str, Any]:
    records = []
    for constraint in cpobc["MSR_operator_constraints"]:
        total = ZERO
        for term in constraint["terms"]:
            total = _matrix_add(
                total,
                _matrix_scale(
                    int(term["coefficient"]),
                    assignments[term["transition_id"]],
                ),
            )
        total = _matrix_add(
            total,
            _matrix_scale(int(constraint["identity_coefficient"]), IDENTITY),
        )
        reachable_residual = _matrix_apply(total, OMEGA)
        records.append(
            {
                "constraint_id": constraint["constraint_id"],
                "source_id": constraint["source_id"],
                "operator_residual": _matrix_record(total),
                "reachable_state_residual_on_omega_ray": _vector_record(reachable_residual),
                "strong_operator_zero": total == ZERO,
                "reachable_state_zero": reachable_residual == (Fraction(0), Fraction(0)),
            }
        )
    return {
        "checked_constraints": len(records),
        "records": records,
        "all_reachable_state_equalities_hold": all(
            record["reachable_state_zero"] for record in records
        ),
        "all_strong_operator_equalities_hold": all(
            record["strong_operator_zero"] for record in records
        ),
        "strong_operator_failure_count": sum(
            not record["strong_operator_zero"] for record in records
        ),
    }


def _path_matrix(path: dict[str, Any]) -> Matrix2:
    product = IDENTITY
    for transition in path["transitions"]:
        factor = transition_witness(
            int(transition["stage"]),
            transition["source_relation_rows"],
            int(transition["precursor_code"]),
        )
        product = _matrix_multiply(factor, product)
    return product


def _evaluate_gc(operator_gc: dict[str, Any]) -> dict[str, Any]:
    paths = {
        path["path_id"]: path
        for stage_paths in operator_gc["path_inventory"].values()
        for path in stage_paths
    }
    path_matrices = {path_id: _path_matrix(path) for path_id, path in paths.items()}
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
    return {
        "checked_same_endpoint_path_pairs": len(records),
        "records": records,
        "all_fixed_vector_equalities_hold": all(record["fixed_vector_zero"] for record in records),
        "all_strong_operator_equalities_hold": all(
            record["strong_operator_zero"] for record in records
        ),
        "strong_operator_failure_count": sum(
            not record["strong_operator_zero"] for record in records
        ),
    }


def _b_factor_assignments(atomisation: dict[str, Any]) -> dict[str, Matrix2]:
    assignments: dict[str, Matrix2] = {}
    for causet in atomisation["causets"]:
        for path in causet["all_alternative_paths"]:
            for factor in path["B_operator_factors"]:
                token = factor["B_occurrence_id"].removeprefix("B-occurrence-")
                matrix = transition_witness(
                    int(factor["paper_stage_index"]),
                    factor["source_relation_rows"],
                    int(factor["precursor_code"]),
                )
                previous = assignments.setdefault(token, matrix)
                if previous != matrix:
                    raise AssertionError("one B token acquired inconsistent transition data")
    return assignments


def _eq113_token_matrix(token: str, b_factors: dict[str, Matrix2]) -> Matrix2:
    if token.startswith("Q_"):
        return q_witness(int(token.removeprefix("Q_")))
    kind, identifier = token.split(":", maxsplit=1)
    if kind == "BDEF":
        return b_factors[identifier]
    if kind == "BINV":
        return _matrix_inverse(b_factors[identifier])
    raise ValueError(f"unknown Eq. (113) word token: {token}")


def _evaluate_eq113(
    eq112: dict[str, Any],
    atomisation: dict[str, Any],
) -> dict[str, Any]:
    b_factors = _b_factor_assignments(atomisation)
    branches = {}
    for branch_name in (EQ113_DERIVED, EQ113_LITERAL):
        records = []
        for relation in eq112["path_consistency_branches"][branch_name]:
            lhs = _matrix_word(
                _eq113_token_matrix(token, b_factors) for token in relation["lhs_word"]
            )
            rhs = _matrix_word(
                _eq113_token_matrix(token, b_factors) for token in relation["rhs_word"]
            )
            residual = _matrix_subtract(lhs, rhs)
            records.append(
                {
                    "causet_id": relation["causet_id"],
                    "alpha_path_id": relation["alpha_path_id"],
                    "beta_path_id": relation["beta_path_id"],
                    "Q_token": relation["Q_token"],
                    "operator_residual": _matrix_record(residual),
                    "zero": residual == ZERO,
                }
            )
        branches[branch_name] = {
            "checked_relations": len(records),
            "records": records,
            "all_zero": all(record["zero"] for record in records),
        }
    return {
        "branches_kept_separate": True,
        "branches": branches,
        "both_branches_hold_as_operator_equalities": all(
            branch["all_zero"] for branch in branches.values()
        ),
    }


def _evaluate_eq139() -> dict[str, Any]:
    branches = {}
    for domain in (EQ139_PRINTED_STRICT, EQ139_EQ145_COMPLETED):
        records = []
        for stage, left_index, right_index in eq139_instances(domain):
            residual = _eq139_residual(stage, left_index, right_index)
            records.append(
                {
                    "stage_n": stage,
                    "m": left_index,
                    "k": right_index,
                    "operator_residual": _matrix_record(residual),
                    "zero": residual == ZERO,
                }
            )
        branches[domain] = {
            "instance_count": len(records),
            "counts_by_stage": {
                str(stage): sum(record["stage_n"] == stage for record in records)
                for stage in (2, 3, 4)
            },
            "records": records,
            "all_zero": all(record["zero"] for record in records),
        }
    return {
        "source_discrepancy": {
            "printed_text": "m,k<n",
            "immediate_specialisation_eq145": "n=2 with A_2^(1) and A_2^(2)",
            "resolution": "PRESERVE_TWO_DOMAINS_WITHOUT_MERGING",
        },
        "branches": branches,
        "both_domains_hold_as_operator_equalities": all(
            branch["all_zero"] for branch in branches.values()
        ),
    }


@dataclass(frozen=True)
class _TriangularLinear:
    """Upper-triangular matrix with one linear upper-right entry."""

    upper_left: Fraction
    lower_right: Fraction
    coefficients: dict[str, Fraction]


def _linear_matrix(
    upper_left: Fraction,
    lower_right: Fraction,
    variable: str | None = None,
) -> _TriangularLinear:
    coefficients = {} if variable is None else {variable: Fraction(1)}
    return _TriangularLinear(upper_left, lower_right, coefficients)


def _linear_multiply(
    left: _TriangularLinear,
    right: _TriangularLinear,
) -> _TriangularLinear:
    coefficients: defaultdict[str, Fraction] = defaultdict(Fraction)
    for variable, coefficient in right.coefficients.items():
        coefficients[variable] += left.upper_left * coefficient
    for variable, coefficient in left.coefficients.items():
        coefficients[variable] += right.lower_right * coefficient
    return _TriangularLinear(
        left.upper_left * right.upper_left,
        left.lower_right * right.lower_right,
        {variable: value for variable, value in coefficients.items() if value},
    )


def _linear_word(factors: Iterable[_TriangularLinear]) -> _TriangularLinear:
    product = _linear_matrix(Fraction(1), Fraction(1))
    for factor in factors:
        product = _linear_multiply(product, factor)
    return product


def _linear_inverse(matrix: _TriangularLinear) -> _TriangularLinear:
    coefficients = {
        variable: -coefficient / (matrix.upper_left * matrix.lower_right)
        for variable, coefficient in matrix.coefficients.items()
    }
    return _TriangularLinear(
        Fraction(1, 1) / matrix.upper_left,
        Fraction(1, 1) / matrix.lower_right,
        coefficients,
    )


def _linear_residual(
    left: _TriangularLinear,
    right: _TriangularLinear,
) -> dict[str, Fraction]:
    if left.upper_left != right.upper_left or left.lower_right != right.lower_right:
        raise AssertionError("the two exact CSG diagonal characters violate an identity")
    variables = set(left.coefficients) | set(right.coefficients)
    return {
        variable: left.coefficients.get(variable, Fraction(0))
        - right.coefficients.get(variable, Fraction(0))
        for variable in variables
        if left.coefficients.get(variable, Fraction(0))
        != right.coefficients.get(variable, Fraction(0))
    }


def _row_echelon(
    rows: Iterable[dict[str, Fraction]],
    variables: list[str],
) -> dict[int, dict[int, Fraction]]:
    """Return a normalized sparse row-echelon basis over ``QQ``."""

    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    for source_row in rows:
        row = {
            positions[variable]: Fraction(value) for variable, value in source_row.items() if value
        }
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                break
            pivot_row = basis[pivot]
            scale = row[pivot]
            for column, value in pivot_row.items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return basis


def _row_rank(rows: Iterable[dict[str, Fraction]], variables: list[str]) -> int:
    """Exact sparse Gaussian rank over ``QQ``."""

    return len(_row_echelon(rows, variables))


def _nullspace_basis(
    rows: Iterable[dict[str, Fraction]],
    variables: list[str],
) -> list[dict[str, Fraction]]:
    """Return an exact sparse basis for the homogeneous right nullspace."""

    echelon = _row_echelon(rows, variables)
    free_columns = [column for column in range(len(variables)) if column not in echelon]
    vectors = []
    for free_column in free_columns:
        coordinates: dict[int, Fraction] = {free_column: Fraction(1)}
        for pivot in sorted(echelon, reverse=True):
            row = echelon[pivot]
            coordinates[pivot] = -sum(
                (
                    coefficient * coordinates.get(column, Fraction(0))
                    for column, coefficient in row.items()
                    if column != pivot
                ),
                Fraction(0),
            )
        vectors.append({variables[column]: value for column, value in coordinates.items() if value})
    return vectors


def _row_value(row: dict[str, Fraction], vector: dict[str, Fraction]) -> Fraction:
    return sum(
        (coefficient * vector.get(variable, Fraction(0)) for variable, coefficient in row.items()),
        Fraction(0),
    )


def _signature_key(
    stage: int,
    source_relation_rows: Iterable[int],
    precursor_code: int,
) -> tuple[int, int, int]:
    relation = tuple(int(row) for row in source_relation_rows)
    return stage, _relation_code(relation), precursor_code


def _triangular_scout(
    cpobc: dict[str, Any],
    reduction: dict[str, Any],
    operator_gc: dict[str, Any],
) -> dict[str, Any]:
    """Perform exact linear scouts; never promote them to a general proof."""

    occurrence_records = {record["occurrence_id"]: record for record in reduction["reduction_map"]}
    signature_to_orbit: dict[tuple[int, int, int], str] = {}
    for record in reduction["reduction_map"]:
        key = _signature_key(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        previous = signature_to_orbit.setdefault(key, record["orbit_id"])
        if previous != record["orbit_id"]:
            raise AssertionError("one decorated transition signature has two orbit IDs")

    variables = sorted({record["orbit_id"] for record in reduction["reduction_map"]})
    variables.append("Q_5_EXTERNAL")

    def transition(record: dict[str, Any]) -> _TriangularLinear:
        return _linear_matrix(
            _csg_diagonal(
                int(record["stage"]),
                record["source_relation_rows"],
                int(record["precursor_code"]),
                coupling_ratio=None,
            ),
            _csg_diagonal(
                int(record["stage"]),
                record["source_relation_rows"],
                int(record["precursor_code"]),
                coupling_ratio=2,
            ),
            record["orbit_id"],
        )

    def transition_from_signature(signature: dict[str, Any]) -> _TriangularLinear:
        stage = int(signature["stage"])
        source_code = int(signature["source_relation_code"])
        precursor_code = int(signature["precursor_code"])
        key = (stage, source_code, precursor_code)
        orbit = signature_to_orbit[key]
        size = stage
        mask = (1 << size) - 1
        relation = tuple((source_code >> (row * size)) & mask for row in range(size))
        return _linear_matrix(
            _csg_diagonal(stage, relation, precursor_code, coupling_ratio=None),
            _csg_diagonal(stage, relation, precursor_code, coupling_ratio=2),
            orbit,
        )

    occurrence_matrices = {
        occurrence: transition(record) for occurrence, record in occurrence_records.items()
    }

    cpobc_rows = []
    cpobc_row_labels = []
    for relation in cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            lhs = _linear_word(
                occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"]
            )
            rhs = _linear_word(
                occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
            )
            cpobc_rows.append(_linear_residual(lhs, rhs))
            cpobc_row_labels.append(f"{relation['relation_id']}:{equation['equation_id']}")

    msr_rows = []
    msr_labels = []
    for constraint in cpobc["MSR_operator_constraints"]:
        coefficients: defaultdict[str, Fraction] = defaultdict(Fraction)
        upper_left = Fraction(int(constraint["identity_coefficient"]))
        lower_right = Fraction(int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            matrix = occurrence_matrices[term["transition_id"]]
            coefficient = Fraction(int(term["coefficient"]))
            upper_left += coefficient * matrix.upper_left
            lower_right += coefficient * matrix.lower_right
            for variable, value in matrix.coefficients.items():
                coefficients[variable] += coefficient * value
        if upper_left or lower_right:
            raise AssertionError("the two CSG characters must satisfy strong MSR diagonally")
        msr_rows.append({key: value for key, value in coefficients.items() if value})
        msr_labels.append(constraint["constraint_id"])

    path_linear_matrices: dict[str, _TriangularLinear] = {}
    for paths in operator_gc["path_inventory"].values():
        for path in paths:
            product = _linear_matrix(Fraction(1), Fraction(1))
            for transition_record in path["transitions"]:
                factor = transition_from_signature(transition_record["quotient_signature"])
                product = _linear_multiply(factor, product)
            path_linear_matrices[path["path_id"]] = product

    gc_rows = []
    gc_labels = []
    for relation in operator_gc["generating_relation_basis"]:
        gc_rows.append(
            _linear_residual(
                path_linear_matrices[relation["lhs_path_id"]],
                path_linear_matrices[relation["rhs_path_id"]],
            )
        )
        gc_labels.append(relation["relation_id"])

    def q_linear(stage: int) -> _TriangularLinear:
        if stage == 5:
            variable = "Q_5_EXTERNAL"
        else:
            variable = signature_to_orbit[(stage, 0, 0)]
        return _linear_matrix(
            Fraction(1, 2**stage),
            Fraction(1, 3**stage),
            variable,
        )

    commutator_rows = {}
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        left = q_linear(left_stage)
        right = q_linear(right_stage)
        commutator_rows[f"Q{left_stage}_Q{right_stage}"] = _linear_residual(
            _linear_multiply(left, right),
            _linear_multiply(right, left),
        )

    base_nullspace = _nullspace_basis(cpobc_rows, variables)

    def restriction(row: dict[str, Fraction]) -> tuple[Fraction, ...]:
        return tuple(_row_value(row, vector) for vector in base_nullspace)

    commutator_restrictions = [restriction(row) for row in commutator_rows.values()]
    target_restriction = next(values for values in commutator_restrictions if any(values))

    def proportional_to_commutator(row: dict[str, Fraction]) -> bool:
        values = restriction(row)
        pivot = next(index for index, value in enumerate(target_restriction) if value)
        ratio = values[pivot] / target_restriction[pivot]
        return ratio != 0 and all(
            value == ratio * target
            for value, target in zip(values, target_restriction, strict=True)
        )

    single_msr_forcers = [
        label
        for label, row in zip(msr_labels, msr_rows, strict=True)
        if proportional_to_commutator(row)
    ]
    single_gc_forcers = [
        label
        for label, row in zip(gc_labels, gc_rows, strict=True)
        if proportional_to_commutator(row)
    ]

    def profile_record(extra_rows: list[dict[str, Fraction]]) -> dict[str, Any]:
        rows = cpobc_rows + extra_rows
        rank = _row_rank(rows, variables)
        joint_augmented_rank = _row_rank(rows + list(commutator_rows.values()), variables)
        commutators = {}
        for pair, functional in commutator_rows.items():
            augmented_rank = _row_rank(rows + [functional], variables)
            commutators[pair] = {
                "augmented_rank": augmented_rank,
                "forced_zero_within_ansatz": augmented_rank == rank,
            }
        return {
            "rank": rank,
            "nullity": len(variables) - rank,
            "joint_commutator_augmented_rank": joint_augmented_rank,
            "independent_commutator_conditions_remaining": joint_augmented_rank - rank,
            "all_Q1_through_Q4_commutators_forced_zero_within_ansatz": all(
                record["forced_zero_within_ansatz"] for record in commutators.values()
            ),
            "commutators": commutators,
        }

    eq139_rows = {}
    for stage, left_index, right_index in eq139_instances(EQ139_EQ145_COMPLETED):
        left_transition = transition_from_signature(
            {
                "stage": stage,
                "source_relation_code": 0,
                "precursor_code": (1 << left_index) - 1,
            }
        )
        right_transition = transition_from_signature(
            {
                "stage": stage,
                "source_relation_code": 0,
                "precursor_code": (1 << right_index) - 1,
            }
        )
        current_q = q_linear(stage)
        next_q = q_linear(stage + 1)
        lhs = _linear_word(
            (
                left_transition,
                right_transition,
                next_q,
                _linear_inverse(right_transition),
                _linear_inverse(current_q),
                right_transition,
            )
        )
        rhs = _linear_word(
            (
                right_transition,
                left_transition,
                next_q,
                _linear_inverse(left_transition),
                _linear_inverse(current_q),
                left_transition,
            )
        )
        eq139_rows[(stage, left_index, right_index)] = _linear_residual(lhs, rhs)

    base_rank = _row_rank(cpobc_rows, variables)
    individual_eq139 = []
    for instance, row in sorted(eq139_rows.items()):
        augmented = _row_rank(cpobc_rows + [row], variables)
        nonimplication_vector: dict[str, Fraction] | None = None
        for candidate in base_nullspace:
            value = _row_value(row, candidate)
            if value:
                nonimplication_vector = {
                    variable: coefficient / value for variable, coefficient in candidate.items()
                }
                break
        if augmented > base_rank and nonimplication_vector is None:
            raise AssertionError("rank increment lacks a CPOBC nullspace witness")
        if nonimplication_vector is not None:
            if any(_row_value(base_row, nonimplication_vector) for base_row in cpobc_rows):
                raise AssertionError("Eq. (139) nonimplication witness violates CPOBC")
            if _row_value(row, nonimplication_vector) != 1:
                raise AssertionError("Eq. (139) nonimplication witness is not normalized")
        individual_eq139.append(
            {
                "stage_n": instance[0],
                "m": instance[1],
                "k": instance[2],
                "rank_increment_over_CPOBC": augmented - base_rank,
                "classification_within_declared_ansatz": (
                    "ADDITIONAL" if augmented > base_rank else "REDUNDANT"
                ),
                "nonimplication_witness": (
                    None
                    if nonimplication_vector is None
                    else {
                        "unspecified_variables": "0",
                        "nonzero_upper_right_assignments": {
                            variable: _fraction(value)
                            for variable, value in sorted(nonimplication_vector.items())
                        },
                        "all_783_CPOBC_upper_right_residuals": "0",
                        "target_Eq139_upper_right_residual": "1",
                        "all_determinants_nonzero": True,
                    }
                ),
            }
        )

    family_rank_increments = {}
    for domain in (EQ139_PRINTED_STRICT, EQ139_EQ145_COMPLETED):
        rows = [eq139_rows[instance] for instance in eq139_instances(domain)]
        family_rank_increments[domain] = _row_rank(cpobc_rows + rows, variables) - base_rank

    return {
        "classification": "EXACT_QQ_LINEAR_SCOUT_NOT_GENERAL_D2_PROOF",
        "ansatz": {
            "matrix_form": "[[p_e,x_e],[0,q_e]]",
            "first_diagonal_character": "CSG t_j=1",
            "second_diagonal_character": "CSG t_j=2^j",
            "upper_right_variables": "identified by transition orbit",
            "occurrence_identification": "ON",
        },
        "variable_count": len(variables),
        "relation_counts": {
            "CPOBC": len(cpobc_rows),
            "strong_MSR": len(msr_rows),
            "strong_GC_basis": len(gc_rows),
        },
        "profiles": {
            "fixed_vector_GC__reachable_state_MSR": profile_record([]),
            "fixed_vector_GC__strong_MSR": profile_record(msr_rows),
            "strong_GC__reachable_state_MSR": profile_record(gc_rows),
            "strong_GC__strong_MSR": profile_record(msr_rows + gc_rows),
        },
        "ansatz_local_minimal_relation_groups": {
            "target": "all six Q1-through-Q4 commutators",
            "CPOBC_commutator_quotient_dimension": (
                _row_rank(cpobc_rows + list(commutator_rows.values()), variables) - base_rank
            ),
            "single_strong_MSR_relations_that_suffice": single_msr_forcers,
            "single_strong_GC_relations_that_suffice": single_gc_forcers,
            "minimal_cardinality_if_either_list_is_nonempty": 1,
            "claim_boundary": (
                "Exact only in the declared occurrence-identified triangular two-character "
                "family; this is not the globally smallest relation group in arbitrary d=2."
            ),
        },
        "eq139_additionality": {
            "base_CPOBC_rank": base_rank,
            "individual_instances": individual_eq139,
            "family_rank_increments": family_rank_increments,
            "claim_boundary": (
                "Rank classifications are exact only inside the declared triangular "
                "two-character family; strong GC makes the corresponding Eq. (139) "
                "square semantically redundant without this ansatz."
            ),
        },
        "labels": {
            "CPOBC": cpobc_row_labels,
            "strong_MSR": msr_labels,
            "strong_GC_basis": gc_labels,
        },
    }


def _assignment_inventory(
    reduction: dict[str, Any],
    assignments: dict[str, Matrix2],
) -> dict[str, Any]:
    records = []
    by_orbit: dict[str, Matrix2] = {}
    for transition in reduction["reduction_map"]:
        occurrence = transition["occurrence_id"]
        matrix = assignments[occurrence]
        orbit = transition["orbit_id"]
        previous = by_orbit.setdefault(orbit, matrix)
        if previous != matrix:
            raise AssertionError("the witness violates occurrence-orbit identification")
        records.append(
            {
                "occurrence_id": occurrence,
                "orbit_id": orbit,
                "stage": transition["stage"],
                "source_id": transition["source_id"],
                "source_relation_rows": transition["source_relation_rows"],
                "precursor_code": transition["precursor_code"],
                "matrix": _matrix_record(matrix),
                "determinant": _fraction(_determinant(matrix)),
                "nonsingular": _determinant(matrix) != 0,
            }
        )
    inverse_checks = []
    for record in records:
        matrix = assignments[record["occurrence_id"]]
        inverse = _matrix_inverse(matrix)
        left_residual = _matrix_subtract(_matrix_multiply(inverse, matrix), IDENTITY)
        right_residual = _matrix_subtract(_matrix_multiply(matrix, inverse), IDENTITY)
        inverse_checks.append(
            {
                "occurrence_id": record["occurrence_id"],
                "left_inverse_residual": _matrix_record(left_residual),
                "right_inverse_residual": _matrix_record(right_residual),
                "both_zero": left_residual == ZERO and right_residual == ZERO,
            }
        )
    return {
        "occurrence_count": len(records),
        "orbit_count": len(by_orbit),
        "occurrence_identification_ON": True,
        "occurrence_identification_OFF": (
            "also certified because an ON assignment is a valid special case of OFF"
        ),
        "all_occurrences_nonsingular": all(record["nonsingular"] for record in records),
        "records": records,
        "two_sided_inverse_checks": {
            "site_count": len(inverse_checks),
            "matrix_equation_count": 2 * len(inverse_checks),
            "records": inverse_checks,
            "all_zero": all(record["both_zero"] for record in inverse_checks),
        },
    }


def compile_v04(root: Path) -> dict[str, Any]:
    """Compile the exact v0.4 witness and all bounded audits."""

    root = root.resolve()
    paths = {
        "v039_release_manifest": root / "results/v0.3.9_release_manifest.json",
        "cpobc": root / "results/v0.3.1_cpobc_relations_n4.json",
        "reduction": root / "results/v0.3.2_cpobc_generator_reduction.json",
        "operator_gc": root / "results/v0.3.3_local_operator_gc_n4.json",
        "atomisation": root / "results/v0.3.3_atomisation_paths_n4.json",
        "eq112": root / "results/v0.3.3_eq112_reduction_n4.json",
        "source_pdf": root
        / "references/papers/2603.25503v1_srivastava-surya_quantum-bell-causality-qsg.pdf",
    }
    v039_release_manifest = _load_json(paths["v039_release_manifest"])
    if (
        v039_release_manifest["version"] != "0.3.9"
        or v039_release_manifest["semantic_digest_sha256"]
        != "eb9eb81d911f194fe2b6c18dfe81389e3a6fc0856a1bae3a767d46753f348e47"
    ):
        raise AssertionError("the pinned local v0.3.9 baseline manifest changed")
    cpobc = _load_json(paths["cpobc"])
    reduction = _load_json(paths["reduction"])
    operator_gc = _load_json(paths["operator_gc"])
    atomisation = _load_json(paths["atomisation"])
    eq112 = _load_json(paths["eq112"])
    assignments = _transition_assignments(reduction)

    assignment_inventory = _assignment_inventory(reduction, assignments)
    cpobc_audit = _evaluate_cpobc(cpobc, assignments)
    cpobc_inverse_audit = _evaluate_cpobc_inverse_forms(cpobc, assignments)
    gc_audit = _evaluate_gc(operator_gc)
    msr_audit = _evaluate_msr(cpobc, assignments)
    eq113_audit = _evaluate_eq113(eq112, atomisation)
    eq139_audit = _evaluate_eq139()
    scout = _triangular_scout(cpobc, reduction, operator_gc)

    commutators = []
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        residual = _commutator(q_witness(left_stage), q_witness(right_stage))
        expected = (
            (Fraction(0), Fraction(4) * (Fraction(1, 2**left_stage) - Fraction(1, 2**right_stage))),
            (Fraction(0), Fraction(0)),
        )
        if residual != expected:
            raise AssertionError("closed commutator formula failed")
        commutators.append(
            {
                "pair": [left_stage, right_stage],
                "commutator": _matrix_record(residual),
                "nonzero": residual != ZERO,
            }
        )

    q_records = [
        {
            "stage": stage,
            "matrix": _matrix_record(q_witness(stage)),
            "determinant": _fraction(_determinant(q_witness(stage))),
            "nonsingular": _determinant(q_witness(stage)) != 0,
        }
        for stage in range(1, 6)
    ]

    gates = {
        "all_783_CPOBC_word_equations": cpobc_audit["all_zero"],
        "all_712_CPOBC_inverse_containing_rewrites": cpobc_inverse_audit["all_zero"],
        "all_1529_fixed_vector_GC_path_pairs": gc_audit["all_fixed_vector_equalities_hold"],
        "all_24_reachable_state_MSR_constraints": msr_audit["all_reachable_state_equalities_hold"],
        "Eq113_derived_branch_operator_equalities": eq113_audit["branches"][EQ113_DERIVED][
            "all_zero"
        ],
        "Eq113_literal_branch_operator_equalities": eq113_audit["branches"][EQ113_LITERAL][
            "all_zero"
        ],
        "Eq139_printed_strict_operator_equalities": eq139_audit["branches"][EQ139_PRINTED_STRICT][
            "all_zero"
        ],
        "Eq139_eq145_completed_operator_equalities": eq139_audit["branches"][EQ139_EQ145_COMPLETED][
            "all_zero"
        ],
        "all_165_transition_determinants_nonzero": assignment_inventory[
            "all_occurrences_nonsingular"
        ],
        "all_330_two_sided_transition_inverse_equations": assignment_inventory[
            "two_sided_inverse_checks"
        ]["all_zero"],
        "Q1_through_Q5_determinants_nonzero": all(record["nonsingular"] for record in q_records),
        "all_six_Q1_through_Q4_commutators_nonzero": all(
            record["nonzero"] for record in commutators
        ),
        "strong_GC_is_not_accidentally_satisfied": not gc_audit[
            "all_strong_operator_equalities_hold"
        ],
        "strong_MSR_is_not_accidentally_satisfied": not msr_audit[
            "all_strong_operator_equalities_hold"
        ],
    }
    passed = all(gates.values())
    if not passed:
        raise AssertionError(f"v0.4 witness gate failed: {gates}")

    return {
        "schema_version": "final-theory-weak-d2-v0.4",
        "version": "0.4",
        "date": "2026-07-31",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "transition source stages n<=4; Q5 only where a source formula requests it",
        "public_baseline": {
            "version": "0.3.9",
            "zenodo_record": "https://zenodo.org/records/21720863",
            "doi": "10.5281/zenodo.21720863",
            "concept_doi": "10.5281/zenodo.21720862",
            "git_commit": "cba86eae795e1e985c4ba1bcd3dabe4eb2773fab",
            "local_release_manifest_semantic_digest_sha256": (
                "eb9eb81d911f194fe2b6c18dfe81389e3a6fc0856a1bae3a767d46753f348e47"
            ),
            "deposited_file": {
                "filename": "final-theory-bench-v0.3.9.tar.gz",
                "bytes": 7210462,
                "md5": "9d35096cea4b904190551d8034f5bbd0",
            },
        },
        "source_inputs": {
            str(path.relative_to(root)).replace("\\", "/"): _sha256(path) for path in paths.values()
        },
        "witness_definition": {
            "initial_vector": _vector_record(OMEGA),
            "transition_formula": (
                "A_e=[[2^(w_e-m_e)/2^n, (4/2^n if precursor is empty else 0)],[0,1]]"
            ),
            "w_e": "precursor cardinality",
            "m_e": "number of maximal precursor elements",
            "Q_n_formula": "[[2^-n,4*2^-n],[0,1]]",
            "reachable_states": "nonzero rational multiples of omega=(1,0)^T",
            "exactness": "all calculations use fractions.Fraction; no floating point",
        },
        "Q_inventory": q_records,
        "transition_assignment": assignment_inventory,
        "direct_substitution": {
            "CPOBC": cpobc_audit,
            "CPOBC_inverse_forms": cpobc_inverse_audit,
            "GC": gc_audit,
            "MSR": msr_audit,
            "Eq113": eq113_audit,
            "Eq139": eq139_audit,
        },
        "noncommutativity": {
            "closed_formula": ("[Q_i,Q_j]=[[0,4*(2^-i-2^-j)],[0,0]] for 1<=i<j<=4"),
            "records": commutators,
        },
        "Eq139_coverage": {
            "coverage_verdict": "EQ139_TWO_SOURCE_DOMAINS_COMPLETE_N4",
            "printed_strict_instances": [
                list(instance) for instance in eq139_instances(EQ139_PRINTED_STRICT)
            ],
            "eq145_completed_instances": [
                list(instance) for instance in eq139_instances(EQ139_EQ145_COMPLETED)
            ],
            "strong_operator_semantics": (
                "Each instance is the right-multiplied form of its corresponding strong-GC "
                "square and is therefore redundant when that square is assumed."
            ),
            "frozen_local_GC_direct_stage_coverage": {
                "n=2": "covered: endpoint stage 4",
                "n=3": "covered: endpoint stage 5",
                "n=4": "not covered: would require endpoint stage 6",
            },
            "weak_semantics_operator_additionality_scout": scout["eq139_additionality"],
        },
        "semantic_profiles": {
            "strong_GC__strong_MSR": {
                "occurrence_identification_ON": (
                    "Q1..Q4 commutativity already proved by the v0.3.5 derived branch and "
                    "v0.3.7 literal Q5-free theorem"
                ),
                "occurrence_identification_OFF": "OPEN_NOT_COVERED_BY_V0.3_THEOREMS",
            },
            "fixed_vector_GC__strong_MSR": {
                "general_d2": "OPEN",
                "triangular_exact_scout_occurrence_identification_ON": scout["profiles"][
                    "fixed_vector_GC__strong_MSR"
                ],
            },
            "strong_GC__reachable_state_MSR": {
                "general_d2": "OPEN",
                "triangular_exact_scout_occurrence_identification_ON": scout["profiles"][
                    "strong_GC__reachable_state_MSR"
                ],
            },
            "fixed_vector_GC__reachable_state_MSR": {
                "general_d2": VERDICT,
                "occurrence_identification_ON": "CERTIFIED_BY_THIS_WITNESS",
                "occurrence_identification_OFF": "CERTIFIED_BY_THE_SAME_WITNESS",
                "triangular_exact_scout_occurrence_identification_ON": scout["profiles"][
                    "fixed_vector_GC__reachable_state_MSR"
                ],
            },
        },
        "triangular_profile_scout": scout,
        "minimal_semantic_recovery": {
            "MSR": (
                "For each source c, if the states on which the MSR residual is tested span "
                "K^2, then the residual operator is zero. Two linearly independent states "
                "are sufficient and worst-case necessary in d=2."
            ),
            "GC": (
                "For each path-pair residual D, evaluation must separate the declared residual "
                "space. Testing D on a basis of K^2 is sufficient; for unrestricted End(K^2), "
                "one vector is never separating."
            ),
            "exact_residual_space_condition": (
                "The evaluation map D -> (D v)_{v in V} must be injective on the linear span "
                "of the relevant GC or MSR residual family."
            ),
            "one_sided_axiom_minimality": "OPEN_GENERAL_D2",
            "smallest_relation_group": (
                "NOT_CERTIFIED_GLOBALLY; the exact triangular scouts are not promoted to a "
                "full d=2 minimality theorem"
            ),
            "triangular_ansatz_local_result": scout["ansatz_local_minimal_relation_groups"],
        },
        "elimination": {
            "executed": False,
            "reason": "an exact rational noncommutative witness was found first",
            "unit_ideal_or_saturation_claim": "NONE",
        },
        "gates": gates,
        "verdict": VERDICT,
        "passed": passed,
        "claim_boundary": (
            "This certifies noncommutativity for fixed-vector GC plus reachable-state MSR in "
            "the frozen finite n<=4 presentation, with occurrence identification either ON or "
            "OFF. It does not classify either one-sided weak profile in general d=2 and does "
            "not lift to n=5, d=3, or an infinite CPOBC system."
        ),
    }


def semantic_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def write_v04_result(root: Path, payload: dict[str, Any]) -> Path:
    path = root.resolve() / "results/v0.4_weak_d2_classification.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
