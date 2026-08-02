"""Exact non-solver manifest for the SR2-V state-native shear ``D12`` open.

The frozen rank-two harmonic state slice is taken from
``weak_d2_state_native_rank2_v042``.  Every actual ON transition edge is
specialised to

``A_e = F_target * [[1, alpha_e], [0, 1]] * F_source^-1``.

Thus fixed-vector GC, reachable-state MSR, reachable rank two, and all 165
actual occurrence determinants are built in.  The supplemental cutoff
operator ``Q5`` remains a separate generic four-coordinate matrix.  This
module substitutes the complete frozen operator ledgers into exact sparse
polynomials over ``QQ`` and certifies that

``D12 = det([Q1,Q2])``

is a nonzero polynomial on the ambient shear chart.  It deliberately does
not call a solver and does not claim that the ``D12`` open meets the relation
variety.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from universe_lab.final_theory import weak_d2_state_native_rank2_v042 as chart
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_state_native_shear_D12_manifest.json"
SCHEMA = "final-theory-v042-sr2v-state-native-shear-D12-manifest-v1"
VERDICT = "SR2V_STATE_NATIVE_SHEAR_D12_MANIFEST_CERTIFIED_NO_SOLVER_RUN"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_POLYNOMIAL_MANIFEST_ONLY"

Monomial = tuple[int, ...]
Polynomial = dict[Monomial, Fraction]
Matrix = tuple[tuple[Polynomial, Polynomial], tuple[Polynomial, Polynomial]]
Vector = tuple[Polynomial, Polynomial]
RationalMatrix = tuple[
    tuple[Fraction, Fraction],
    tuple[Fraction, Fraction],
]

MAX_ENTRY_TERMS = 100_000
MAX_TOTAL_TERMS = 5_000_000


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"JSON object required: {path}")
    return payload


def _constant(value: Fraction | int) -> Polynomial:
    scalar = Fraction(value)
    return {} if not scalar else {(): scalar}


def _variable(index: int) -> Polynomial:
    return {(index,): Fraction(1)}


def _add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        updated = result.get(monomial, Fraction(0)) + coefficient
        if updated:
            result[monomial] = updated
        else:
            result.pop(monomial, None)
    return result


def _negate(value: Polynomial) -> Polynomial:
    return {monomial: -coefficient for monomial, coefficient in value.items()}


def _subtract(left: Polynomial, right: Polynomial) -> Polynomial:
    return _add(left, _negate(right))


def _scale(coefficient: Fraction | int, value: Polynomial) -> Polynomial:
    scalar = Fraction(coefficient)
    return {} if not scalar else {monomial: scalar * item for monomial, item in value.items()}


def _multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(sorted(left_monomial + right_monomial))
            updated = result.get(monomial, Fraction(0)) + left_coefficient * right_coefficient
            if updated:
                result[monomial] = updated
            else:
                result.pop(monomial, None)
    if len(result) > MAX_ENTRY_TERMS:
        raise RuntimeError("one sparse polynomial exceeded the declared term limit")
    return result


def _matrix_constant(value: RationalMatrix) -> Matrix:
    return tuple(
        tuple(_constant(value[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _identity() -> Matrix:
    return ((_constant(1), _constant(0)), (_constant(0), _constant(1)))


def _zero_matrix() -> Matrix:
    return ((_constant(0), _constant(0)), (_constant(0), _constant(0)))


def _matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(_add(left[row][column], right[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(_subtract(left[row][column], right[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_scale(coefficient: Fraction | int, value: Matrix) -> Matrix:
    return tuple(
        tuple(_scale(coefficient, value[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(
            _add(
                _multiply(left[row][0], right[0][column]),
                _multiply(left[row][1], right[1][column]),
            )
            for column in range(2)
        )
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_word(factors: Iterable[Matrix]) -> Matrix:
    product = _identity()
    for factor in factors:
        product = _matrix_multiply(product, factor)
    return product


def _matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
    return (
        _add(_multiply(matrix[0][0], vector[0]), _multiply(matrix[0][1], vector[1])),
        _add(_multiply(matrix[1][0], vector[0]), _multiply(matrix[1][1], vector[1])),
    )


def _vector_subtract(left: Vector, right: Vector) -> Vector:
    return (_subtract(left[0], right[0]), _subtract(left[1], right[1]))


def _determinant(matrix: Matrix) -> Polynomial:
    return _subtract(
        _multiply(matrix[0][0], matrix[1][1]),
        _multiply(matrix[0][1], matrix[1][0]),
    )


def _inverse_with_constant_determinant(matrix: Matrix) -> Matrix:
    determinant = _determinant(matrix)
    if set(determinant) != {()} or not determinant[()]:
        raise AssertionError("the shear edge inverse requires a nonzero constant determinant")
    reciprocal = Fraction(1, 1) / determinant[()]
    return (
        (
            _scale(reciprocal, matrix[1][1]),
            _scale(-reciprocal, matrix[0][1]),
        ),
        (
            _scale(-reciprocal, matrix[1][0]),
            _scale(reciprocal, matrix[0][0]),
        ),
    )


def _matrix_entries(matrix: Matrix) -> list[Polynomial]:
    return [matrix[row][column] for row in range(2) for column in range(2)]


def _vector_entries(vector: Vector) -> list[Polynomial]:
    return [vector[0], vector[1]]


def _serialize_polynomial(value: Polynomial, names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": str(coefficient),
            "monomial": [
                {"variable": names[index], "exponent": monomial.count(index)}
                for index in sorted(set(monomial))
            ],
        }
        for monomial, coefficient in sorted(value.items())
    ]


def _serialize_matrix(value: Matrix, names: list[str]) -> dict[str, list[dict[str, Any]]]:
    return {
        f"{row}{column}": _serialize_polynomial(value[row][column], names)
        for row in range(2)
        for column in range(2)
    }


def _serialize_vector(value: Vector, names: list[str]) -> dict[str, list[dict[str, Any]]]:
    return {
        str(index): _serialize_polynomial(value[index], names)
        for index in range(2)
    }


def _records_digest(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def _polynomial_digest(value: Polynomial, names: list[str]) -> str:
    return hashlib.sha256(
        _canonical_json(_serialize_polynomial(value, names)).encode("utf-8")
    ).hexdigest()


def _term_census(values: list[Polynomial]) -> dict[str, Any]:
    terms = [len(value) for value in values]
    degrees = [len(monomial) for value in values for monomial in value]
    degree_histogram = Counter(degrees)
    return {
        "scalar_entries": len(values),
        "zero_entries": sum(not value for value in values),
        "nonzero_entries": sum(bool(value) for value in values),
        "total_terms": sum(terms),
        "maximum_terms_in_one_entry": max(terms, default=0),
        "maximum_total_degree": max(degrees, default=0),
        "nonzero_monomial_degree_histogram": {
            str(degree): count for degree, count in sorted(degree_histogram.items())
        },
    }


def _evaluate(value: Polynomial, assignment: dict[int, Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in value.items():
        term = coefficient
        for index in monomial:
            term *= assignment.get(index, Fraction(0))
        total += term
    return total


def _evaluate_matrix(matrix: Matrix, assignment: dict[int, Fraction]) -> RationalMatrix:
    return tuple(
        tuple(_evaluate(matrix[row][column], assignment) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _rational_multiply(left: RationalMatrix, right: RationalMatrix) -> RationalMatrix:
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def _rational_subtract(left: RationalMatrix, right: RationalMatrix) -> RationalMatrix:
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _rational_determinant(matrix: RationalMatrix) -> Fraction:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _rational_matrix_record(matrix: RationalMatrix) -> list[list[str]]:
    return [[str(value) for value in row] for row in matrix]


def _block(
    records: list[dict[str, Any]],
    entries: list[Polynomial],
) -> dict[str, Any]:
    return {
        "count": len(records),
        "records": records,
        "term_census": _term_census(entries),
        "content_digest_sha256": _records_digest(records),
    }


def _nonzero_point(
    polynomial: Polynomial,
    *,
    alpha_indices: list[int],
) -> tuple[dict[int, Fraction], Fraction]:
    support = sorted({index for monomial in polynomial for index in monomial})
    if not set(support).issubset(alpha_indices):
        raise AssertionError("D12 unexpectedly depends on a non-alpha coordinate")
    values = (Fraction(0), Fraction(1), Fraction(-1), Fraction(2), Fraction(-2))
    for candidate in itertools.product(values, repeat=len(support)):
        assignment = dict(zip(support, candidate, strict=True))
        result = _evaluate(polynomial, assignment)
        if result:
            return assignment, result
    raise AssertionError("bounded exact grid did not find a D12 principal-open point")


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    context = torus._build_context(root)
    graph = chart._endpoint_graph(context)
    harmonic = chart._harmonic_states(graph)
    states: dict[str, chart.Vector2] = harmonic["states"]

    frozen_chart = _load(root / chart.RESULT_PATH)
    if (
        frozen_chart.get("verdict") != chart.VERDICT
        or frozen_chart.get("passed") is not True
        or frozen_chart.get("semantic_digest_sha256") != chart.semantic_digest(frozen_chart)
    ):
        raise AssertionError("the frozen state-native rank-two chart binding failed")

    actual_orbits = sorted(graph["edges"])
    if len(actual_orbits) != 131:
        raise AssertionError("expected 131 actual ON transition orbits")
    alpha_names = [f"alpha:{orbit}" for orbit in actual_orbits]
    q5_names = ["Q5:00", "Q5:01", "Q5:10", "Q5:11"]
    saturation_name = "rho:D12"
    variable_names = alpha_names + q5_names + [saturation_name]
    alpha_index = {orbit: index for index, orbit in enumerate(actual_orbits)}
    q5_index = {entry: len(alpha_names) + offset for offset, entry in enumerate(q5_names)}
    rho_index = len(alpha_names) + len(q5_names)

    edge_matrices: dict[str, Matrix] = {}
    edge_inverses: dict[str, Matrix] = {}
    edge_determinants: dict[str, Fraction] = {}
    inverse_identity_failures: list[str] = []
    for orbit in actual_orbits:
        edge = graph["edges"][orbit]
        family = chart._affine_edge_family(
            states[edge["source"]],
            states[edge["target"]],
        )
        variable = _variable(alpha_index[orbit])
        matrix = cast(
            Matrix,
            tuple(
                tuple(
                    _add(
                        _constant(
                            family["constant"][row][column]
                            + family["beta"][row][column]
                        ),
                        _scale(family["alpha"][row][column], variable),
                    )
                    for column in range(2)
                )
                for row in range(2)
            ),
        )
        determinant = _determinant(matrix)
        if set(determinant) != {()} or not determinant[()]:
            raise AssertionError("a shear edge determinant is not a nonzero constant")
        inverse = _inverse_with_constant_determinant(matrix)
        if (
            _matrix_multiply(matrix, inverse) != _identity()
            or _matrix_multiply(inverse, matrix) != _identity()
        ):
            inverse_identity_failures.append(orbit)
        edge_matrices[orbit] = matrix
        edge_inverses[orbit] = inverse
        edge_determinants[orbit] = determinant[()]

    occurrence_matrices = {
        occurrence_id: edge_matrices[context.occurrence_variables[occurrence_id]]
        for occurrence_id in context.occurrence_records
    }
    occurrence_inverses = {
        occurrence_id: edge_inverses[context.occurrence_variables[occurrence_id]]
        for occurrence_id in context.occurrence_records
    }

    q5_matrix: Matrix = (
        (_variable(q5_index["Q5:00"]), _variable(q5_index["Q5:01"])),
        (_variable(q5_index["Q5:10"]), _variable(q5_index["Q5:11"])),
    )
    q5_determinant = _determinant(q5_matrix)

    def q(stage: int) -> Matrix:
        return q5_matrix if stage == 5 else edge_matrices[torus._q_variable(context, stage)]

    def from_signature(stage: int, relation_code: int, precursor: int) -> Matrix:
        return edge_matrices[context.signature_variables[(stage, relation_code, precursor)]]

    def inverse_from_signature(stage: int, relation_code: int, precursor: int) -> Matrix:
        return edge_inverses[context.signature_variables[(stage, relation_code, precursor)]]

    # Raw denominator-cleared CPOBC operator equations.
    cpobc_records: list[dict[str, Any]] = []
    cpobc_entries: list[Polynomial] = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            identifiers = equation["operator_ids"]
            lhs = _matrix_word(
                occurrence_matrices[identifiers[token]] for token in equation["lhs_word"]
            )
            rhs = _matrix_word(
                occurrence_matrices[identifiers[token]] for token in equation["rhs_word"]
            )
            residual = _matrix_subtract(lhs, rhs)
            matrix_entries = _matrix_entries(residual)
            cpobc_entries.extend(matrix_entries)
            cpobc_records.append(
                {
                    "relation_id": str(relation["relation_id"]),
                    "equation_id": str(equation["equation_id"]),
                    "lhs_word_length": len(equation["lhs_word"]),
                    "rhs_word_length": len(equation["rhs_word"]),
                    "entries": _serialize_matrix(residual, variable_names),
                }
            )

    # The 712 solved inverse rewrites are retained as their own ledger.
    inverse_rewrite_records: list[dict[str, Any]] = []
    inverse_rewrite_entries: list[Polynomial] = []
    for relation in context.cpobc["relations"]:
        aliases = relation["transition_orbit"]

        def inverse_word(tokens: list[str], aliases: dict[str, Any] = aliases) -> Matrix:
            factors = []
            for token in tokens:
                is_inverse = token.endswith("^-1")
                alias = token.removesuffix("^-1")
                occurrence_id = str(aliases[alias]["occurrence_id"])
                factors.append(
                    occurrence_inverses[occurrence_id]
                    if is_inverse
                    else occurrence_matrices[occurrence_id]
                )
            return _matrix_word(factors)

        for form in relation["inverse_containing_form"]["forms"]:
            residual = _zero_matrix()
            for term in form["residual_terms"]:
                residual = _matrix_add(
                    residual,
                    _matrix_scale(int(term["coefficient"]), inverse_word(term["word"])),
                )
            matrix_entries = _matrix_entries(residual)
            inverse_rewrite_entries.extend(matrix_entries)
            inverse_rewrite_records.append(
                {
                    "relation_id": str(relation["relation_id"]),
                    "equation_id": str(form["equation_id"]),
                    "entries": _serialize_matrix(residual, variable_names),
                }
            )

    def eq113_token(token: str) -> Matrix:
        if token.startswith("Q_"):
            return q(int(token.removeprefix("Q_")))
        kind, identifier = token.split(":", maxsplit=1)
        stage, relation_rows, precursor, orbit = context.b_signatures[identifier]
        del stage, relation_rows, precursor
        if kind == "BDEF":
            return edge_matrices[orbit]
        if kind == "BINV":
            return edge_inverses[orbit]
        raise ValueError(f"unknown Eq. (113) token: {token}")

    eq113_blocks: dict[str, tuple[list[dict[str, Any]], list[Polynomial]]] = {}
    for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        records: list[dict[str, Any]] = []
        branch_entries: list[Polynomial] = []
        for index, relation in enumerate(context.eq112["path_consistency_branches"][branch]):
            lhs = _matrix_word(eq113_token(token) for token in relation["lhs_word"])
            rhs = _matrix_word(eq113_token(token) for token in relation["rhs_word"])
            residual = _matrix_subtract(lhs, rhs)
            branch_entries.extend(_matrix_entries(residual))
            records.append(
                {
                    "record_index": index,
                    "causet_id": str(relation["causet_id"]),
                    "entries": _serialize_matrix(residual, variable_names),
                }
            )
        eq113_blocks[branch] = (records, branch_entries)

    def eq139_residual(stage: int, left_index: int, right_index: int) -> Matrix:
        left_transition = from_signature(stage, 0, (1 << left_index) - 1)
        right_transition = from_signature(stage, 0, (1 << right_index) - 1)
        left_inverse = inverse_from_signature(stage, 0, (1 << left_index) - 1)
        right_inverse = inverse_from_signature(stage, 0, (1 << right_index) - 1)
        current_q_inverse = edge_inverses[torus._q_variable(context, stage)]
        next_q = q(stage + 1)
        lhs = _matrix_word(
            (
                left_transition,
                right_transition,
                next_q,
                right_inverse,
                current_q_inverse,
                right_transition,
            )
        )
        rhs = _matrix_word(
            (
                right_transition,
                left_transition,
                next_q,
                left_inverse,
                current_q_inverse,
                left_transition,
            )
        )
        return _matrix_subtract(lhs, rhs)

    eq139_blocks: dict[str, tuple[list[dict[str, Any]], list[Polynomial]]] = {}
    for domain in (torus.EQ139_STRICT, torus.EQ139_COMPLETED):
        records = []
        entries = []
        for stage, left_index, right_index in torus._eq139_instances(domain):
            residual = eq139_residual(stage, left_index, right_index)
            entries.extend(_matrix_entries(residual))
            records.append(
                {
                    "stage": stage,
                    "left_index": left_index,
                    "right_index": right_index,
                    "entries": _serialize_matrix(residual, variable_names),
                }
            )
        eq139_blocks[domain] = (records, entries)

    # Fixed-vector GC: build every path state and substitute all 1,529 pairs.
    omega: Vector = (_constant(1), _constant(0))
    path_states: dict[str, Vector] = {}
    path_endpoint: dict[str, str] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = _identity()
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                product = _matrix_multiply(
                    from_signature(
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    ),
                    product,
                )
            path_id = str(path["path_id"])
            path_states[path_id] = _matrix_vector(product, omega)
            path_endpoint[path_id] = str(path["endpoint_causet_id"])

    gc_records: list[dict[str, Any]] = []
    gc_entries: list[Polynomial] = []
    for relation in context.operator_gc["all_pair_derivations"]:
        left_id = str(relation["left_path_id"])
        right_id = str(relation["right_path_id"])
        gc_residual = _vector_subtract(path_states[left_id], path_states[right_id])
        gc_entries.extend(_vector_entries(gc_residual))
        gc_records.append(
            {
                "left_path_id": left_id,
                "right_path_id": right_id,
                "endpoint_causet_id": path_endpoint[left_id],
                "entries": _serialize_vector(gc_residual, variable_names),
            }
        )

    # Reachable-state MSR: use the frozen harmonic source state directly.
    msr_records: list[dict[str, Any]] = []
    msr_entries: list[Polynomial] = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        residual = _matrix_scale(int(constraint["identity_coefficient"]), _identity())
        for term in constraint["terms"]:
            residual = _matrix_add(
                residual,
                _matrix_scale(
                    int(term["coefficient"]),
                    occurrence_matrices[str(term["transition_id"])],
                ),
            )
        source = str(constraint["source_id"])
        source_state: Vector = (
            _constant(states[source][0]),
            _constant(states[source][1]),
        )
        vector_residual = _matrix_vector(residual, source_state)
        msr_entries.extend(_vector_entries(vector_residual))
        msr_records.append(
            {
                "constraint_id": str(constraint["constraint_id"]),
                "source_id": source,
                "entries": _serialize_vector(vector_residual, variable_names),
            }
        )

    q1_orbit = torus._q_variable(context, 1)
    q2_orbit = torus._q_variable(context, 2)
    q1 = edge_matrices[q1_orbit]
    q2 = edge_matrices[q2_orbit]
    commutator12 = _matrix_subtract(
        _matrix_multiply(q1, q2),
        _matrix_multiply(q2, q1),
    )
    d12 = _determinant(commutator12)
    if not d12:
        raise AssertionError("D12 vanished identically on the shear chart")
    d12_assignment, d12_value = _nonzero_point(
        d12,
        alpha_indices=list(range(len(alpha_names))),
    )
    full_assignment = dict(d12_assignment)
    full_assignment.update(
        {
            q5_index["Q5:00"]: Fraction(1),
            q5_index["Q5:01"]: Fraction(0),
            q5_index["Q5:10"]: Fraction(0),
            q5_index["Q5:11"]: Fraction(1),
            rho_index: Fraction(1, 1) / d12_value,
        }
    )
    saturation = _subtract(
        _multiply(_variable(rho_index), d12),
        _constant(1),
    )
    if _evaluate(saturation, full_assignment):
        raise AssertionError("the exact principal-open point misses rho*D12-1")

    q1_point = _evaluate_matrix(q1, full_assignment)
    q2_point = _evaluate_matrix(q2, full_assignment)
    commutator_point = _rational_subtract(
        _rational_multiply(q1_point, q2_point),
        _rational_multiply(q2_point, q1_point),
    )
    direct_d12 = _rational_determinant(commutator_point)
    if direct_d12 != d12_value:
        raise AssertionError("direct and sparse-polynomial D12 evaluations disagree")

    raw_blocks_internal = {
        "CPOBC_raw": cpobc_entries,
        "CPOBC_inverse_rewrites": inverse_rewrite_entries,
        "Eq113_derived_Qn": eq113_blocks[torus.EQ113_DERIVED][1],
        "Eq113_literal_Qn_plus_1": eq113_blocks[torus.EQ113_LITERAL][1],
        "Eq139_printed_strict": eq139_blocks[torus.EQ139_STRICT][1],
        "Eq139_completed": eq139_blocks[torus.EQ139_COMPLETED][1],
        "fixed_vector_GC_all_pairs": gc_entries,
        "reachable_state_MSR": msr_entries,
    }
    point_residuals = {
        name: {
            "scalar_entries": len(entries),
            "nonzero_scalar_entries": sum(
                bool(_evaluate(entry, full_assignment)) for entry in entries
            ),
        }
        for name, entries in raw_blocks_internal.items()
    }
    point_is_relation_solution = all(
        record["nonzero_scalar_entries"] == 0 for record in point_residuals.values()
    )

    residual_blocks = {
        "CPOBC_raw": _block(cpobc_records, cpobc_entries),
        "CPOBC_inverse_rewrites": _block(
            inverse_rewrite_records,
            inverse_rewrite_entries,
        ),
        "Eq113": {
            "branches_kept_separate": True,
            torus.EQ113_DERIVED: _block(*eq113_blocks[torus.EQ113_DERIVED]),
            torus.EQ113_LITERAL: _block(*eq113_blocks[torus.EQ113_LITERAL]),
        },
        "Eq139": {
            "domains_kept_separate": True,
            torus.EQ139_STRICT: _block(*eq139_blocks[torus.EQ139_STRICT]),
            torus.EQ139_COMPLETED: _block(*eq139_blocks[torus.EQ139_COMPLETED]),
        },
        "fixed_vector_GC_all_pairs": _block(gc_records, gc_entries),
        "reachable_state_MSR": _block(msr_records, msr_entries),
    }

    all_manifest_entries = [
        *cpobc_entries,
        *inverse_rewrite_entries,
        *eq113_blocks[torus.EQ113_DERIVED][1],
        *eq113_blocks[torus.EQ113_LITERAL][1],
        *eq139_blocks[torus.EQ139_STRICT][1],
        *eq139_blocks[torus.EQ139_COMPLETED][1],
        *gc_entries,
        *msr_entries,
        q5_determinant,
        d12,
        saturation,
    ]
    total_terms = sum(len(value) for value in all_manifest_entries)
    if total_terms > MAX_TOTAL_TERMS:
        raise RuntimeError("the shear manifest exceeded its declared total term limit")

    d12_support = sorted({index for monomial in d12 for index in monomial})
    d12_leading_monomial = max(d12, key=lambda monomial: (len(monomial), monomial))
    actual_occurrence_determinants = [
        {
            "occurrence_id": occurrence_id,
            "orbit_id": context.occurrence_variables[occurrence_id],
            "constant_determinant": str(
                edge_determinants[context.occurrence_variables[occurrence_id]]
            ),
        }
        for occurrence_id in sorted(context.occurrence_records)
    ]

    gates = {
        "frozen_state_native_chart_is_bound": frozen_chart["semantic_digest_sha256"]
        == "3bf3b56c97ef73fcce3ff089f5229191b9d1ade04e217706ac51abe11eaebe6c",
        "actual_shear_parameter_count_is_131": len(alpha_names) == 131,
        "supplemental_Q5_has_four_separate_coordinates": len(q5_names) == 4,
        "all_actual_edge_inverse_identities_hold": not inverse_identity_failures,
        "all_165_actual_occurrence_determinants_are_constant_nonzero": len(
            actual_occurrence_determinants
        )
        == 165
        and all(
            Fraction(record["constant_determinant"])
            for record in actual_occurrence_determinants
        ),
        "raw_CPOBC_count_is_783": len(cpobc_records) == 783,
        "inverse_rewrite_count_is_712": len(inverse_rewrite_records) == 712,
        "Eq113_branches_are_25_and_25": len(eq113_blocks[torus.EQ113_DERIVED][0]) == 25
        and len(eq113_blocks[torus.EQ113_LITERAL][0]) == 25,
        "Eq139_domains_are_4_and_10": len(eq139_blocks[torus.EQ139_STRICT][0]) == 4
        and len(eq139_blocks[torus.EQ139_COMPLETED][0]) == 10,
        "all_1529_fixed_vector_GC_residuals_are_zero": len(gc_records) == 1529
        and not any(gc_entries),
        "all_24_reachable_state_MSR_residuals_are_zero": len(msr_records) == 24
        and not any(msr_entries),
        "D12_is_a_nonzero_sparse_polynomial": bool(d12),
        "D12_exact_principal_open_point_is_nonempty": bool(d12_value)
        and not _evaluate(saturation, full_assignment),
        "D12_direct_matrix_evaluation_matches": direct_d12 == d12_value,
        "ambient_open_point_is_not_promoted_to_relation_solution": not point_is_relation_solution,
        "manifest_term_budget_not_exceeded": total_terms <= MAX_TOTAL_TERMS,
    }
    if not all(gates.values()):
        raise AssertionError(f"state-native shear manifest gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: torus._sha256(root / relative)
            for relative in sorted(
                (
                    torus.CPOBC_PATH,
                    torus.REDUCTION_PATH,
                    torus.OPERATOR_GC_PATH,
                    torus.ATOMISATION_PATH,
                    torus.EQ112_PATH,
                    chart.RESULT_PATH,
                )
            )
        },
        "state_native_chart_binding": {
            "path": chart.RESULT_PATH,
            "semantic_digest_sha256": frozen_chart["semantic_digest_sha256"],
            "reachable_endpoint_count": len(states),
            "reachable_span_rank": 2,
            "initial_vector": ["1", "0"],
            "support_terminals": harmonic["support_terminals"],
            "support_state_determinant": str(harmonic["support_determinant"]),
        },
        "variables": {
            "actual_edge_shear_coordinates": len(alpha_names),
            "supplemental_Q5_coordinates": len(q5_names),
            "ambient_chart_coordinates": len(alpha_names) + len(q5_names),
            "D12_open_inverse_coordinate": saturation_name,
            "saturated_chart_coordinates": len(variable_names),
            "names": variable_names,
        },
        "shear_parameterisation": {
            "formula": "A_e=F_target*[[1,alpha_e],[0,1]]*F_source^-1",
            "actual_edge_count": len(edge_matrices),
            "actual_occurrence_count": len(context.occurrence_records),
            "actual_occurrence_determinants": actual_occurrence_determinants,
            "two_sided_inverse_identities_checked": 2 * len(edge_matrices),
            "inverse_identity_failures": inverse_identity_failures,
            "supplemental_Q5": {
                "matrix": "[[Q5:00,Q5:01],[Q5:10,Q5:11]]",
                "determinant_polynomial": _serialize_polynomial(
                    q5_determinant,
                    variable_names,
                ),
                "determinant_digest_sha256": _polynomial_digest(
                    q5_determinant,
                    variable_names,
                ),
                "nonsingularity_is_a_separate_solver_localisation": True,
            },
        },
        "residual_blocks": residual_blocks,
        "D12_pair_open_certificate": {
            "pair": [1, 2],
            "Q_orbits": [q1_orbit, q2_orbit],
            "definition": "D12=det([Q1,Q2])",
            "commutator_entries": _serialize_matrix(commutator12, variable_names),
            "polynomial": _serialize_polynomial(d12, variable_names),
            "polynomial_content_digest_sha256": _polynomial_digest(d12, variable_names),
            "term_count": len(d12),
            "total_degree": max(len(monomial) for monomial in d12),
            "variable_support": [variable_names[index] for index in d12_support],
            "leading_term_certificate": {
                "coefficient": str(d12[d12_leading_monomial]),
                "monomial": [
                    {
                        "variable": variable_names[index],
                        "exponent": d12_leading_monomial.count(index),
                    }
                    for index in sorted(set(d12_leading_monomial))
                ],
            },
            "saturation_equation": {
                "display": "rho:D12*D12-1=0",
                "polynomial": _serialize_polynomial(saturation, variable_names),
                "content_digest_sha256": _polynomial_digest(saturation, variable_names),
            },
            "exact_nonempty_ambient_open_point": {
                "nonzero_or_support_assignments": {
                    variable_names[index]: str(value)
                    for index, value in sorted(full_assignment.items())
                    if value or index in q5_index.values() or index == rho_index
                },
                "all_unlisted_alpha_coordinates": "0",
                "D12_value": str(d12_value),
                "rho_value": str(full_assignment[rho_index]),
                "Q1": _rational_matrix_record(q1_point),
                "Q2": _rational_matrix_record(q2_point),
                "commutator": _rational_matrix_record(commutator_point),
                "direct_commutator_determinant": str(direct_d12),
                "Q5": [["1", "0"], ["0", "1"]],
                "Q5_determinant": "1",
                "required_relation_residuals_at_this_point": point_residuals,
                "is_required_relation_solution": point_is_relation_solution,
                "role": (
                    "nonemptiness of the ambient D12 principal open only; this point "
                    "is not a CPOBC/GC/MSR witness"
                ),
            },
            "pair_irreducible_scope": (
                "D12!=0 makes [Q1,Q2] invertible.  A common invariant line for "
                "Q1,Q2 would triangularise both and force determinant zero, so the "
                "pair is irreducible over the algebraic closure on this open."
            ),
            "reachable_visibility_scope": (
                "The frozen reachable states span Q^2 and are nonzero.  An invertible "
                "commutator acts nontrivially on every reachable state, hence D12!=0 "
                "is stronger than the requested reachable-visible condition."
            ),
        },
        "sparse_manifest_inventory": {
            "required_operator_matrix_ledgers": {
                "CPOBC_raw": 783,
                "CPOBC_inverse_rewrites": 712,
                "Eq113_derived_Qn": 25,
                "Eq113_literal_Qn_plus_1": 25,
                "Eq139_printed_strict": 4,
                "Eq139_completed": 10,
            },
            "required_state_vector_ledgers": {
                "fixed_vector_GC_all_pairs": 1529,
                "reachable_state_MSR": 24,
            },
            "Eq113_branches_merged": False,
            "Eq139_domains_merged": False,
            "global_term_census": _term_census(all_manifest_entries),
            "observed_total_terms": total_terms,
        },
        "resource_and_claim_boundaries": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "sage_status": "NOT_INVOKED",
            "finite_field_status": "NOT_RUN",
            "fixed_harmonic_state_slice_is_a_global_state_cover": False,
            "D12_open_meets_relation_variety": "UNRESOLVED",
            "other_five_Q_pair_opens": "NOT_COMPILED_IN_THIS_ARTIFACT",
            "det_commutator_zero_locus": "NOT_COVERED",
            "supplemental_Q5_nonsingularity": "REMAINS_A_SEPARATE_LOCALISATION",
            "next_solver_input": (
                "the listed sparse relation blocks plus rho:D12*D12-1 and a "
                "Q5-determinant localisation, under the approved resource cap"
            ),
            "resource_limit_outcome_rule": (
                "a capped or incomplete future elimination remains OPEN_RESOURCE_LIMIT; "
                "finite-field or numerical output is scout-only"
            ),
        },
        "resource_limits": {
            "maximum_terms_per_entry": MAX_ENTRY_TERMS,
            "maximum_total_manifest_terms": MAX_TOTAL_TERMS,
            "observed_total_manifest_terms": total_terms,
            "limit_exceeded": False,
        },
        "gates": gates,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "This is an exact sparse QQ substitution manifest and a nonempty ambient "
            "D12 principal-open certificate.  It is not a solver result, does not "
            "show that the relation variety intersects D12!=0, and is not an SR2-V "
            "witness, obstruction, chart cover, or terminal verdict."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
