"""Exact bounded scout for a reachable-visible weak/weak CPOBC witness.

The scout treats occurrence identification as ON and works in the reducible,
transverse upper-triangular chart

``A_e = [[a_e, x_e], [0, b_e]],  Omega = e_2``.

The lower diagonal ``b_e`` is the normalized ``t_j=1`` CSG character.  The
upper diagonal is sampled from exact rational points of the full scalar torus
defined by the frozen CPOBC, Eq. (113), and Eq. (139) monomial relations.  At
each point all remaining constraints are homogeneous linear equations in the
upper-right coordinates ``x_e`` and are solved exactly over ``QQ``.

A successful point is promoted only after direct substitution into every raw
CPOBC equation, both Eq. (113) branches, both Eq. (139) domains, all compiled
same-endpoint path pairs, and every source-matched reachable-state MSR
constraint.  A negative result is only a finite scout, never a global no-go.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
OPERATOR_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
ATOMISATION_PATH = "results/v0.3.3_atomisation_paths_n4.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
RESULT_PATH = "results/v0.4.2_sr2v_visible_torus_scout.json"

SCHEMA = "final-theory-v042-sr2v-visible-torus-scout-v1"
NO_WITNESS_VERDICT = "SR2V_VISIBLE_TORUS_SCOUT_NO_WITNESS_OPEN"
WITNESS_VERDICT = "REACHABLE_VISIBLE_NONCOMMUTATIVE_WITNESS_CERTIFIED"
NO_WITNESS_TERMINAL = "NOT_A_SEARCH_TERMINAL_BOUNDED_ANSATZ_ONLY"
WITNESS_TERMINAL = "REACHABLE_VISIBLE_NONCOMMUTATIVE_WITNESS_CERTIFIED"

EQ113_DERIVED = "EQ113_QN_BRANCH"
EQ113_LITERAL = "EQ113_QN_PLUS_1_BRANCH"
EQ139_STRICT = "EQ139_PRINTED_STRICT_M_K_LT_N"
EQ139_COMPLETED = "EQ139_EQ145_COMPLETED_M_K_LE_N"
Q5 = "Q_5_EXTERNAL"

SparseRow = dict[str, Fraction]
Matrix2 = tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]
Vector2 = tuple[Fraction, Fraction]
ScalarCharacter = Callable[[int, Iterable[int], int], Fraction]

ZERO_MATRIX: Matrix2 = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0)))
IDENTITY: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
OMEGA: Vector2 = (Fraction(0), Fraction(1))
ZERO_VECTOR: Vector2 = (Fraction(0), Fraction(0))


@dataclass(frozen=True)
class TriangularLinear:
    """Upper-triangular matrix with a linear upper-right coordinate."""

    upper_left: Fraction
    lower_right: Fraction
    coefficients: SparseRow


@dataclass(frozen=True)
class ScoutContext:
    cpobc: dict[str, Any]
    reduction: dict[str, Any]
    operator_gc: dict[str, Any]
    atomisation: dict[str, Any]
    eq112: dict[str, Any]
    occurrence_records: dict[str, dict[str, Any]]
    occurrence_variables: dict[str, str]
    signature_variables: dict[tuple[int, int, int], str]
    b_signatures: dict[str, tuple[int, tuple[int, ...], int, str]]
    variables: tuple[str, ...]


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


def _relation_code(relation: Iterable[int]) -> int:
    rows = tuple(int(row) for row in relation)
    size = len(rows)
    return sum(row << (index * size) for index, row in enumerate(rows))


def _signature(stage: int, relation: Iterable[int], precursor: int) -> tuple[int, int, int]:
    return stage, _relation_code(relation), precursor


def _decode_relation(stage: int, relation_code: int) -> tuple[int, ...]:
    mask = (1 << stage) - 1
    return tuple((relation_code >> (row * stage)) & mask for row in range(stage))


def _csg(stage: int, relation: Iterable[int], precursor: int) -> Fraction:
    rows = tuple(int(row) for row in relation)
    width = precursor.bit_count()
    maximal = len(maximal_elements_in_subset(rows, precursor))
    return Fraction(2 ** (width - maximal), 2**stage)


def _csg_exponent(stage: int, relation: Iterable[int], precursor: int) -> int:
    rows = tuple(int(row) for row in relation)
    return precursor.bit_count() - len(maximal_elements_in_subset(rows, precursor)) - stage


def _clean(row: dict[str, Fraction | int]) -> SparseRow:
    return {variable: Fraction(value) for variable, value in row.items() if value}


def _add_rows(*rows: SparseRow) -> SparseRow:
    result: defaultdict[str, Fraction] = defaultdict(Fraction)
    for row in rows:
        for variable, value in row.items():
            result[variable] += value
    return _clean(dict(result))


def _scale_row(coefficient: Fraction | int, row: SparseRow) -> SparseRow:
    scalar = Fraction(coefficient)
    return _clean({variable: scalar * value for variable, value in row.items()})


def _linear_matrix(
    upper_left: Fraction,
    lower_right: Fraction,
    variable: str | None = None,
) -> TriangularLinear:
    return TriangularLinear(
        upper_left,
        lower_right,
        {} if variable is None else {variable: Fraction(1)},
    )


def _linear_multiply(left: TriangularLinear, right: TriangularLinear) -> TriangularLinear:
    return TriangularLinear(
        left.upper_left * right.upper_left,
        left.lower_right * right.lower_right,
        _add_rows(
            _scale_row(left.upper_left, right.coefficients),
            _scale_row(right.lower_right, left.coefficients),
        ),
    )


def _linear_word(factors: Iterable[TriangularLinear]) -> TriangularLinear:
    product = _linear_matrix(Fraction(1), Fraction(1))
    for factor in factors:
        product = _linear_multiply(product, factor)
    return product


def _linear_inverse(matrix: TriangularLinear) -> TriangularLinear:
    if not matrix.upper_left or not matrix.lower_right:
        raise ZeroDivisionError("a torus point unexpectedly contains a zero diagonal")
    return TriangularLinear(
        Fraction(1, 1) / matrix.upper_left,
        Fraction(1, 1) / matrix.lower_right,
        _scale_row(
            -Fraction(1, 1) / (matrix.upper_left * matrix.lower_right),
            matrix.coefficients,
        ),
    )


def _operator_residual(left: TriangularLinear, right: TriangularLinear) -> SparseRow:
    if left.upper_left != right.upper_left or left.lower_right != right.lower_right:
        raise AssertionError("sampled diagonal point violates an operator identity")
    return _add_rows(left.coefficients, _scale_row(-1, right.coefficients))


def _fixed_vector_residual(left: TriangularLinear, right: TriangularLinear) -> SparseRow:
    if left.lower_right != right.lower_right:
        raise AssertionError("the normalized lower character violates fixed-vector GC")
    return _add_rows(left.coefficients, _scale_row(-1, right.coefficients))


def _row_echelon(
    rows: Iterable[SparseRow],
    variables: tuple[str, ...],
) -> dict[int, dict[int, Fraction]]:
    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    for source in rows:
        row = {positions[variable]: value for variable, value in source.items() if value}
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return basis


def _row_remainder(
    source: SparseRow,
    echelon: dict[int, dict[int, Fraction]],
    variables: tuple[str, ...],
) -> dict[int, Fraction]:
    positions = {variable: index for index, variable in enumerate(variables)}
    row = {positions[variable]: value for variable, value in source.items() if value}
    while row:
        pivot = min(row)
        if pivot not in echelon:
            return row
        scale = row[pivot]
        for column, value in echelon[pivot].items():
            updated = row.get(column, Fraction(0)) - scale * value
            if updated:
                row[column] = updated
            else:
                row.pop(column, None)
    return {}


def _nullspace_basis_from_echelon(
    echelon: dict[int, dict[int, Fraction]],
    variables: tuple[str, ...],
) -> list[SparseRow]:
    free_columns = [column for column in range(len(variables)) if column not in echelon]
    result = []
    for free in free_columns:
        coordinates: dict[int, Fraction] = {free: Fraction(1)}
        for pivot in sorted(echelon, reverse=True):
            coordinates[pivot] = -sum(
                (
                    coefficient * coordinates.get(column, Fraction(0))
                    for column, coefficient in echelon[pivot].items()
                    if column != pivot
                ),
                Fraction(0),
            )
        result.append(
            {
                variables[column]: value
                for column, value in coordinates.items()
                if value
            }
        )
    return result


def _row_value(row: SparseRow, vector: SparseRow) -> Fraction:
    return sum(
        (coefficient * vector.get(variable, Fraction(0)) for variable, coefficient in row.items()),
        Fraction(0),
    )


def _eq139_instances(domain: str) -> tuple[tuple[int, int, int], ...]:
    instances: list[tuple[int, int, int]] = []
    for stage in (2, 3, 4):
        if domain == EQ139_STRICT:
            indices = range(1, stage)
        elif domain == EQ139_COMPLETED:
            indices = range(1, stage + 1)
        else:
            raise ValueError(f"unknown Eq. (139) domain: {domain}")
        instances.extend((stage, left, right) for left, right in itertools.combinations(indices, 2))
    return tuple(instances)


def _build_context(root: Path) -> ScoutContext:
    artifacts = {
        CPOBC_PATH: _load(root / CPOBC_PATH),
        REDUCTION_PATH: _load(root / REDUCTION_PATH),
        OPERATOR_GC_PATH: _load(root / OPERATOR_GC_PATH),
        ATOMISATION_PATH: _load(root / ATOMISATION_PATH),
        EQ112_PATH: _load(root / EQ112_PATH),
    }
    reduction = artifacts[REDUCTION_PATH]
    occurrence_records = {
        str(record["occurrence_id"]): record for record in reduction["reduction_map"]
    }
    occurrence_variables = {
        occurrence: str(record["orbit_id"])
        for occurrence, record in occurrence_records.items()
    }
    signature_variables: dict[tuple[int, int, int], str] = {}
    for record in occurrence_records.values():
        key = _signature(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        variable = str(record["orbit_id"])
        previous_signature = signature_variables.setdefault(key, variable)
        if previous_signature != variable:
            raise AssertionError("one transition signature has two ON orbit variables")

    b_signatures: dict[str, tuple[int, tuple[int, ...], int, str]] = {}
    for causet in artifacts[ATOMISATION_PATH]["causets"]:
        for path in causet["all_alternative_paths"]:
            for factor in path["B_operator_factors"]:
                identifier = str(factor["B_occurrence_id"]).removeprefix("B-occurrence-")
                stage = int(factor["paper_stage_index"])
                canonical_signature = factor["B_transition_signature"]
                canonical_stage = int(canonical_signature["stage"])
                canonical_code = int(canonical_signature["source_relation_code"])
                canonical_precursor = int(canonical_signature["precursor_code"])
                rows = _decode_relation(canonical_stage, canonical_code)
                variable = signature_variables[
                    (
                        canonical_stage,
                        canonical_code,
                        canonical_precursor,
                    )
                ]
                if stage != canonical_stage:
                    raise AssertionError("B factor and canonical signature disagree on stage")
                value = (canonical_stage, rows, canonical_precursor, variable)
                previous_b_signature = b_signatures.setdefault(identifier, value)
                if previous_b_signature != value:
                    raise AssertionError("one Eq. (113) B token has two signatures")

    variables = tuple(sorted(set(occurrence_variables.values())) + [Q5])
    if len(variables) != 132:
        raise AssertionError("the frozen ON inventory must contain 131 orbit variables plus Q5")
    return ScoutContext(
        cpobc=artifacts[CPOBC_PATH],
        reduction=reduction,
        operator_gc=artifacts[OPERATOR_GC_PATH],
        atomisation=artifacts[ATOMISATION_PATH],
        eq112=artifacts[EQ112_PATH],
        occurrence_records=occurrence_records,
        occurrence_variables=occurrence_variables,
        signature_variables=signature_variables,
        b_signatures=b_signatures,
        variables=variables,
    )


def _q_variable(context: ScoutContext, stage: int) -> str:
    return Q5 if stage == 5 else context.signature_variables[(stage, 0, 0)]


def _token_exponents(context: ScoutContext, token: str) -> SparseRow:
    if token.startswith("Q_"):
        return {_q_variable(context, int(token.removeprefix("Q_"))): Fraction(1)}
    kind, identifier = token.split(":", maxsplit=1)
    variable = context.b_signatures[identifier][3]
    if kind == "BDEF":
        return {variable: Fraction(1)}
    if kind == "BINV":
        return {variable: Fraction(-1)}
    raise ValueError(f"unknown Eq. (113) token: {token}")


def _scalar_torus_rows(context: ScoutContext) -> tuple[list[SparseRow], dict[str, int]]:
    rows: list[SparseRow] = []
    counts: dict[str, int] = {}
    start = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            left = _add_rows(
                *(
                    {context.occurrence_variables[operator_ids[token]]: Fraction(1)}
                    for token in equation["lhs_word"]
                )
            )
            right = _add_rows(
                *(
                    {context.occurrence_variables[operator_ids[token]]: Fraction(1)}
                    for token in equation["rhs_word"]
                )
            )
            rows.append(_add_rows(left, _scale_row(-1, right)))
    counts["CPOBC"] = len(rows) - start
    start = len(rows)

    for branch in (EQ113_DERIVED, EQ113_LITERAL):
        for relation in context.eq112["path_consistency_branches"][branch]:
            left = _add_rows(*(_token_exponents(context, token) for token in relation["lhs_word"]))
            right = _add_rows(*(_token_exponents(context, token) for token in relation["rhs_word"]))
            rows.append(_add_rows(left, _scale_row(-1, right)))
    counts["Eq113_both_branches"] = len(rows) - start
    start = len(rows)

    # Each Eq. (139) word has the same scalar multiset.  Retain ten explicit
    # zero rows so coverage is visible and cannot silently change.
    rows.extend({} for _ in _eq139_instances(EQ139_COMPLETED))
    counts["Eq139_completed"] = len(rows) - start
    return rows, counts


def _bottom_exponent_point(context: ScoutContext) -> dict[str, int]:
    point: dict[str, int] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        exponent = _csg_exponent(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        previous = point.setdefault(variable, exponent)
        if previous != exponent:
            raise AssertionError("the normalized CSG character is not constant on an ON orbit")
    point[Q5] = -5
    return point


def _candidate_points(
    exponent_basis: list[SparseRow],
    bottom_point: dict[str, int],
    variables: tuple[str, ...],
) -> list[dict[str, Any]]:
    integer_basis: list[dict[str, int]] = []
    for vector in exponent_basis:
        if any(value.denominator != 1 for value in vector.values()):
            raise AssertionError("the frozen torus basis unexpectedly has denominators")
        integer_basis.append({variable: value.numerator for variable, value in vector.items()})

    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, tuple[int, ...]]] = set()

    def add(identifier: str, base: int, point: dict[str, int], origin: str) -> None:
        cleaned = {variable: int(value) for variable, value in point.items() if value}
        key = base, tuple(cleaned.get(variable, 0) for variable in variables)
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            {
                "candidate_id": identifier,
                "base": base,
                "exponents": cleaned,
                "origin": origin,
            }
        )

    def combine(
        coefficients: dict[int, int],
        offset: dict[str, int] | None = None,
    ) -> dict[str, int]:
        point: defaultdict[str, int] = defaultdict(int)
        if offset is not None:
            point.update(offset)
        for index, coefficient in coefficients.items():
            for variable, value in integer_basis[index].items():
                point[variable] += coefficient * value
        return {variable: value for variable, value in point.items() if value}

    add("constant-character", 2, {}, "zero exponent point")
    add("normalized-lower-character", 2, bottom_point, "upper diagonal equals lower CSG")
    for index in range(len(integer_basis)):
        add(f"basis-plus-{index:02d}", 2, combine({index: 1}), "torus basis vector")
        add(
            f"lower-plus-basis-{index:02d}",
            2,
            combine({index: 1}, bottom_point),
            "normalized lower character plus torus basis vector",
        )

    rng = random.Random(0x5A17)
    random_combinations: list[dict[int, int]] = []
    for _ in range(48):
        support = sorted(rng.sample(range(len(integer_basis)), k=4))
        random_combinations.append({index: rng.choice((-1, 1)) for index in support})
    for index, coefficients in enumerate(random_combinations):
        add(
            f"sparse-random-{index:02d}",
            2,
            combine(coefficients),
            "seeded four-basis combination",
        )
    for index, coefficients in enumerate(random_combinations[:16]):
        add(
            f"lower-plus-random-{index:02d}",
            2,
            combine(coefficients, bottom_point),
            "normalized lower character plus seeded combination",
        )
    for index, coefficients in enumerate(random_combinations[:8]):
        add(
            f"signed-base-random-{index:02d}",
            -2,
            combine(coefficients),
            "signed rational torus point",
        )
        add(
            f"base-three-random-{index:02d}",
            3,
            combine(coefficients),
            "independent positive rational base",
        )
    return candidates


def _power(base: int, exponent: int) -> Fraction:
    if not base:
        raise ValueError("a torus base must be nonzero")
    if exponent >= 0:
        return Fraction(base**exponent)
    return Fraction(1, base ** (-exponent))


def _top_assignment(candidate: dict[str, Any], variables: tuple[str, ...]) -> dict[str, Fraction]:
    base = int(candidate["base"])
    exponents = candidate["exponents"]
    return {variable: _power(base, int(exponents.get(variable, 0))) for variable in variables}


def _linear_system(
    context: ScoutContext,
    top: dict[str, Fraction],
    lower_character: ScalarCharacter | None = None,
) -> tuple[list[SparseRow], dict[str, int], dict[str, SparseRow], dict[str, TriangularLinear]]:
    lower = _csg if lower_character is None else lower_character

    def transition(
        stage: int,
        relation: Iterable[int],
        precursor: int,
        variable: str,
    ) -> TriangularLinear:
        rows = tuple(int(row) for row in relation)
        return _linear_matrix(top[variable], lower(stage, rows, precursor), variable)

    def occurrence(occurrence_id: str) -> TriangularLinear:
        record = context.occurrence_records[occurrence_id]
        return transition(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
            context.occurrence_variables[occurrence_id],
        )

    def from_signature(stage: int, relation_code: int, precursor: int) -> TriangularLinear:
        variable = context.signature_variables[(stage, relation_code, precursor)]
        return transition(stage, _decode_relation(stage, relation_code), precursor, variable)

    def q(stage: int) -> TriangularLinear:
        variable = _q_variable(context, stage)
        return _linear_matrix(
            top[variable],
            lower(stage, (0,) * stage, 0),
            variable,
        )

    occurrence_matrices = {
        occurrence_id: occurrence(occurrence_id)
        for occurrence_id in context.occurrence_records
    }
    rows: list[SparseRow] = []
    counts: dict[str, int] = {}
    start = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            left = _linear_word(
                occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"]
            )
            right = _linear_word(
                occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
            )
            rows.append(_operator_residual(left, right))
    counts["CPOBC"] = len(rows) - start
    start = len(rows)

    def eq113_token(token: str) -> TriangularLinear:
        if token.startswith("Q_"):
            return q(int(token.removeprefix("Q_")))
        kind, identifier = token.split(":", maxsplit=1)
        stage, relation, precursor, variable = context.b_signatures[identifier]
        matrix = transition(stage, relation, precursor, variable)
        if kind == "BDEF":
            return matrix
        if kind == "BINV":
            return _linear_inverse(matrix)
        raise ValueError(f"unknown Eq. (113) token: {token}")

    for branch in (EQ113_DERIVED, EQ113_LITERAL):
        for relation in context.eq112["path_consistency_branches"][branch]:
            left = _linear_word(eq113_token(token) for token in relation["lhs_word"])
            right = _linear_word(eq113_token(token) for token in relation["rhs_word"])
            rows.append(_operator_residual(left, right))
    counts["Eq113_both_branches"] = len(rows) - start
    start = len(rows)

    for stage, left_index, right_index in _eq139_instances(EQ139_COMPLETED):
        left_transition = from_signature(stage, 0, (1 << left_index) - 1)
        right_transition = from_signature(stage, 0, (1 << right_index) - 1)
        current_q = q(stage)
        next_q = q(stage + 1)
        left = _linear_word(
            (
                left_transition,
                right_transition,
                next_q,
                _linear_inverse(right_transition),
                _linear_inverse(current_q),
                right_transition,
            )
        )
        right = _linear_word(
            (
                right_transition,
                left_transition,
                next_q,
                _linear_inverse(left_transition),
                _linear_inverse(current_q),
                left_transition,
            )
        )
        rows.append(_operator_residual(left, right))
    counts["Eq139_completed"] = len(rows) - start
    start = len(rows)

    path_matrices: dict[str, TriangularLinear] = {}
    path_records: dict[str, dict[str, Any]] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = _linear_matrix(Fraction(1), Fraction(1))
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                matrix = from_signature(
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                product = _linear_multiply(matrix, product)
            path_id = str(path["path_id"])
            path_matrices[path_id] = product
            path_records[path_id] = path

    for relation in context.operator_gc["generating_relation_basis"]:
        rows.append(
            _fixed_vector_residual(
                path_matrices[relation["lhs_path_id"]],
                path_matrices[relation["rhs_path_id"]],
            )
        )
    counts["fixed_vector_GC_basis"] = len(rows) - start
    start = len(rows)

    anchors: dict[str, TriangularLinear] = {}
    for path_id, path in sorted(path_records.items()):
        anchors.setdefault(str(path["endpoint_causet_id"]), path_matrices[path_id])
    for constraint in context.cpobc["MSR_operator_constraints"]:
        residual_upper_left = Fraction(int(constraint["identity_coefficient"]))
        residual_upper: defaultdict[str, Fraction] = defaultdict(Fraction)
        residual_lower_right = Fraction(int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            matrix = occurrence_matrices[term["transition_id"]]
            coefficient = Fraction(int(term["coefficient"]))
            residual_upper_left += coefficient * matrix.upper_left
            residual_lower_right += coefficient * matrix.lower_right
            for variable, value in matrix.coefficients.items():
                residual_upper[variable] += coefficient * value
        if residual_lower_right:
            raise AssertionError("the normalized lower CSG character violates strong MSR")
        state = anchors[str(constraint["source_id"])]
        statewise_row = _add_rows(
            _scale_row(residual_upper_left, state.coefficients),
            _scale_row(state.lower_right, _clean(dict(residual_upper))),
        )
        rows.append(statewise_row)
    counts["reachable_state_MSR"] = len(rows) - start

    commutators = {}
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        commutators[f"Q{left_stage}_Q{right_stage}"] = _fixed_vector_residual(
            _linear_multiply(q(left_stage), q(right_stage)),
            _linear_multiply(q(right_stage), q(left_stage)),
        )
    return rows, counts, commutators, path_matrices


def _matrix(upper_left: Fraction, upper_right: Fraction, lower_right: Fraction) -> Matrix2:
    return ((upper_left, upper_right), (Fraction(0), lower_right))


def _multiply(left: Matrix2, right: Matrix2) -> Matrix2:
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


def _word(factors: Iterable[Matrix2]) -> Matrix2:
    product = IDENTITY
    for factor in factors:
        product = _multiply(product, factor)
    return product


def _subtract(left: Matrix2, right: Matrix2) -> Matrix2:
    return (
        (left[0][0] - right[0][0], left[0][1] - right[0][1]),
        (left[1][0] - right[1][0], left[1][1] - right[1][1]),
    )


def _inverse(matrix: Matrix2) -> Matrix2:
    determinant = matrix[0][0] * matrix[1][1]
    if not determinant:
        raise ZeroDivisionError("a certified candidate unexpectedly became singular")
    return (
        (Fraction(1, 1) / matrix[0][0], -matrix[0][1] / determinant),
        (Fraction(0), Fraction(1, 1) / matrix[1][1]),
    )


def _apply(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][1] * vector[1],
    )


def _vector_rank(vectors: Iterable[Vector2]) -> int:
    values = [vector for vector in vectors if vector != ZERO_VECTOR]
    if not values:
        return 0
    first = values[0]
    if any(first[0] * other[1] - first[1] * other[0] for other in values[1:]):
        return 2
    return 1


def _direct_certificate(
    context: ScoutContext,
    candidate: dict[str, Any],
    top: dict[str, Fraction],
    coordinates: SparseRow,
    lower_character: ScalarCharacter | None = None,
) -> dict[str, Any]:
    lower = _csg if lower_character is None else lower_character

    def transition(stage: int, relation: Iterable[int], precursor: int, variable: str) -> Matrix2:
        return _matrix(
            top[variable],
            coordinates.get(variable, Fraction(0)),
            lower(stage, relation, precursor),
        )

    def from_signature(stage: int, relation_code: int, precursor: int) -> Matrix2:
        variable = context.signature_variables[(stage, relation_code, precursor)]
        return transition(stage, _decode_relation(stage, relation_code), precursor, variable)

    def q(stage: int) -> Matrix2:
        variable = _q_variable(context, stage)
        return _matrix(
            top[variable],
            coordinates.get(variable, Fraction(0)),
            lower(stage, (0,) * stage, 0),
        )

    occurrence_matrices = {}
    for occurrence_id, record in context.occurrence_records.items():
        occurrence_matrices[occurrence_id] = transition(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
            context.occurrence_variables[occurrence_id],
        )

    cpobc_failures = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            left = _word(occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"])
            right = _word(
                occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
            )
            if left != right:
                cpobc_failures.append(f"{relation['relation_id']}:{equation['equation_id']}")

    def eq113_token(token: str) -> Matrix2:
        if token.startswith("Q_"):
            return q(int(token.removeprefix("Q_")))
        kind, identifier = token.split(":", maxsplit=1)
        stage, relation, precursor, variable = context.b_signatures[identifier]
        matrix = transition(stage, relation, precursor, variable)
        return _inverse(matrix) if kind == "BINV" else matrix

    eq113 = {}
    for branch in (EQ113_DERIVED, EQ113_LITERAL):
        failures = []
        for relation in context.eq112["path_consistency_branches"][branch]:
            left = _word(eq113_token(token) for token in relation["lhs_word"])
            right = _word(eq113_token(token) for token in relation["rhs_word"])
            if left != right:
                failures.append(str(relation["causet_id"]))
        eq113[branch] = {
            "checked": len(context.eq112["path_consistency_branches"][branch]),
            "failures": failures,
        }

    eq139 = {}
    for domain in (EQ139_STRICT, EQ139_COMPLETED):
        eq139_failures: list[list[int]] = []
        for stage, left_index, right_index in _eq139_instances(domain):
            left_transition = from_signature(stage, 0, (1 << left_index) - 1)
            right_transition = from_signature(stage, 0, (1 << right_index) - 1)
            current_q = q(stage)
            next_q = q(stage + 1)
            left = _word(
                (
                    left_transition,
                    right_transition,
                    next_q,
                    _inverse(right_transition),
                    _inverse(current_q),
                    right_transition,
                )
            )
            right = _word(
                (
                    right_transition,
                    left_transition,
                    next_q,
                    _inverse(left_transition),
                    _inverse(current_q),
                    left_transition,
                )
            )
            if left != right:
                eq139_failures.append([stage, left_index, right_index])
        eq139[domain] = {
            "checked": len(_eq139_instances(domain)),
            "failures": eq139_failures,
        }

    path_matrices: dict[str, Matrix2] = {}
    path_records: dict[str, dict[str, Any]] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = IDENTITY
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                product = _multiply(
                    from_signature(
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    ),
                    product,
                )
            path_id = str(path["path_id"])
            path_matrices[path_id] = product
            path_records[path_id] = path

    gc_failures = []
    for relation in context.operator_gc["all_pair_derivations"]:
        residual = _subtract(
            path_matrices[relation["left_path_id"]],
            path_matrices[relation["right_path_id"]],
        )
        if _apply(residual, OMEGA) != ZERO_VECTOR:
            gc_failures.append(
                f"{relation['left_path_id']}:{relation['right_path_id']}"
            )

    endpoint_states: dict[str, Vector2] = {}
    all_paths_state_consistent = True
    for path_id, path in path_records.items():
        state = _apply(path_matrices[path_id], OMEGA)
        endpoint = str(path["endpoint_causet_id"])
        previous = endpoint_states.setdefault(endpoint, state)
        all_paths_state_consistent &= previous == state

    msr_failures = []
    operator_msr_nonzero = 0
    for constraint in context.cpobc["MSR_operator_constraints"]:
        total = tuple(tuple(Fraction(0) for _ in range(2)) for _ in range(2))
        total = (total[0], total[1])
        identity_coefficient = Fraction(int(constraint["identity_coefficient"]))
        total = (
            (identity_coefficient, Fraction(0)),
            (Fraction(0), identity_coefficient),
        )
        for term in constraint["terms"]:
            coefficient = Fraction(int(term["coefficient"]))
            matrix = occurrence_matrices[term["transition_id"]]
            total = (
                (
                    total[0][0] + coefficient * matrix[0][0],
                    total[0][1] + coefficient * matrix[0][1],
                ),
                (
                    total[1][0] + coefficient * matrix[1][0],
                    total[1][1] + coefficient * matrix[1][1],
                ),
            )
        operator_msr_nonzero += int(total != ZERO_MATRIX)
        source_state = endpoint_states[str(constraint["source_id"])]
        if _apply(total, source_state) != ZERO_VECTOR:
            msr_failures.append(str(constraint["constraint_id"]))

    commutators = []
    any_visible = False
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        residual = _subtract(
            _multiply(q(left_stage), q(right_stage)),
            _multiply(q(right_stage), q(left_stage)),
        )
        visible_endpoints = [
            endpoint
            for endpoint, state in endpoint_states.items()
            if _apply(residual, state) != ZERO_VECTOR
        ]
        any_visible |= bool(visible_endpoints)
        commutators.append(
            {
                "pair": [left_stage, right_stage],
                "matrix": [[str(entry) for entry in row] for row in residual],
                "operator_nonzero": residual != ZERO_MATRIX,
                "visible_endpoint_count": len(visible_endpoints),
                "first_visible_endpoint": visible_endpoints[0] if visible_endpoints else None,
            }
        )

    determinants_nonzero = all(
        matrix[0][0] * matrix[1][1] for matrix in occurrence_matrices.values()
    )
    passed = all(
        (
            not cpobc_failures,
            all(not record["failures"] for record in eq113.values()),
            all(not record["failures"] for record in eq139.values()),
            not gc_failures,
            all_paths_state_consistent,
            not msr_failures,
            determinants_nonzero,
            any(record["operator_nonzero"] for record in commutators),
            any_visible,
            _vector_rank(endpoint_states.values()) == 2,
        )
    )
    if not passed:
        raise AssertionError("a linear hit failed full direct certification")
    return {
        "candidate_id": candidate["candidate_id"],
        "top_base": candidate["base"],
        "top_nonzero_exponents": {
            variable: int(value) for variable, value in sorted(candidate["exponents"].items())
        },
        "upper_right_nonzero_coordinates": {
            variable: str(value) for variable, value in sorted(coordinates.items()) if value
        },
        "direct_substitution": {
            "CPOBC": {"checked": 783, "failures": cpobc_failures},
            "Eq113": eq113,
            "Eq139": eq139,
            "fixed_vector_GC": {
                "checked": len(context.operator_gc["all_pair_derivations"]),
                "failures": gc_failures,
            },
            "reachable_state_MSR": {
                "checked": len(context.cpobc["MSR_operator_constraints"]),
                "failures": msr_failures,
                "operator_nonzero_residual_count": operator_msr_nonzero,
            },
        },
        "nonsingular_transition_assignments": determinants_nonzero,
        "reachable_endpoint_count": len(endpoint_states),
        "reachable_span_rank": _vector_rank(endpoint_states.values()),
        "all_same_endpoint_paths_give_same_state": all_paths_state_consistent,
        "commutators": commutators,
        "reachable_visible": any_visible,
        "passed": True,
    }


def build_payload(root: Path) -> dict[str, Any]:
    context = _build_context(root)
    scalar_rows, scalar_counts = _scalar_torus_rows(context)
    scalar_echelon = _row_echelon(scalar_rows, context.variables)
    exponent_basis = _nullspace_basis_from_echelon(scalar_echelon, context.variables)
    bottom_point = _bottom_exponent_point(context)
    bottom_fraction_point = {key: Fraction(value) for key, value in bottom_point.items()}
    if any(_row_value(row, bottom_fraction_point) for row in scalar_rows):
        raise AssertionError("the normalized lower character is not on the scalar torus")
    candidates = _candidate_points(exponent_basis, bottom_point, context.variables)

    records = []
    witness = None
    rank_census: defaultdict[str, int] = defaultdict(int)
    maximum_nullity = 0
    for candidate in candidates:
        top = _top_assignment(candidate, context.variables)
        rows, counts, commutators, _ = _linear_system(context, top)
        echelon = _row_echelon(rows, context.variables)
        rank = len(echelon)
        nullity = len(context.variables) - rank
        maximum_nullity = max(maximum_nullity, nullity)
        rank_census[str(rank)] += 1
        free_commutators = [
            pair
            for pair, row in commutators.items()
            if _row_remainder(row, echelon, context.variables)
        ]
        records.append(
            {
                "candidate_id": candidate["candidate_id"],
                "base": candidate["base"],
                "origin": candidate["origin"],
                "max_absolute_exponent": max(
                    (abs(int(value)) for value in candidate["exponents"].values()),
                    default=0,
                ),
                "linear_rank": rank,
                "linear_nullity": nullity,
                "free_Q_commutators": free_commutators,
            }
        )
        if free_commutators and witness is None:
            target = commutators[free_commutators[0]]
            nullspace = _nullspace_basis_from_echelon(echelon, context.variables)
            coordinates = next(vector for vector in nullspace if _row_value(target, vector))
            scale = _row_value(target, coordinates)
            normalized = _scale_row(Fraction(1, 1) / scale, coordinates)
            witness = _direct_certificate(context, candidate, top, normalized)
            break

    relation_counts = counts
    if relation_counts != {
        "CPOBC": 783,
        "Eq113_both_branches": 50,
        "Eq139_completed": 10,
        "fixed_vector_GC_basis": 320,
        "reachable_state_MSR": 24,
    }:
        raise AssertionError(f"the frozen linear relation inventory changed: {relation_counts}")

    found = witness is not None
    gates = {
        "scalar_relation_count_is_843": sum(scalar_counts.values()) == 843,
        "scalar_torus_rank_is_83": len(scalar_echelon) == 83,
        "scalar_torus_dimension_is_49": len(exponent_basis) == 49,
        "all_candidates_are_exact_nonzero_rational_points": all(
            all(_top_assignment(candidate, context.variables).values()) for candidate in candidates
        ),
        "linear_relation_inventory_is_complete_for_declared_chart": (
            sum(relation_counts.values()) == 1187
        ),
        "witness_directly_certified_if_found": witness is None or witness["passed"],
    }
    if not all(gates.values()):
        raise AssertionError(f"visible torus scout gate failed: {gates}")

    verdict = WITNESS_VERDICT if found else NO_WITNESS_VERDICT
    terminal = WITNESS_TERMINAL if found else NO_WITNESS_TERMINAL
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-01",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: _sha256(root / relative)
            for relative in sorted(
                (CPOBC_PATH, REDUCTION_PATH, OPERATOR_GC_PATH, ATOMISATION_PATH, EQ112_PATH)
            )
        },
        "declared_chart": {
            "matrix_form": "[[a_e,x_e],[0,b_e]]",
            "initial_vector": "e_2",
            "upper_diagonal": "sampled rational points of the full frozen scalar monomial torus",
            "lower_diagonal": "normalized CSG t_j=1 character",
            "upper_right_coordinates": "one per ON transition orbit plus Q5",
            "occurrence_identification": "ON",
            "interpretation": "common invariant line transverse to the initial vector",
        },
        "scalar_torus": {
            "variable_count": len(context.variables),
            "raw_relation_counts": scalar_counts,
            "exact_QQ_rank": len(scalar_echelon),
            "exact_QQ_dimension": len(exponent_basis),
            "integer_nullspace_basis": all(
                value.denominator == 1 for vector in exponent_basis for value in vector.values()
            ),
        },
        "linear_problem": {
            "variable_count": len(context.variables),
            "relation_counts": relation_counts,
            "arithmetic": "fractions.Fraction only; no floats or finite fields",
        },
        "candidate_campaign": {
            "planned_candidate_count": len(candidates),
            "evaluated_candidate_count": len(records),
            "stopped_on_first_certified_witness": found,
            "rank_census": dict(sorted(rank_census.items(), key=lambda item: int(item[0]))),
            "maximum_linear_nullity": maximum_nullity,
            "candidate_records": records,
        },
        "witness": witness,
        "search_terminal": terminal,
        "gates": gates,
        "passed": True,
        "verdict": verdict,
        "claim_boundary": (
            "A certified hit is a genuine exact weak/weak witness because every frozen relation "
            "is directly rechecked.  If no hit is found, the result excludes only the listed "
            "finite rational torus sample in the declared reducible transverse ON chart; it is "
            "not an obstruction for the full chart or arbitrary GL_2."
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
    print(f"{result['verdict']} {result['semantic_digest_sha256']}")
