"""Audit unrestricted 955 tangent escape at the nonsingular diagonal CSG point.

The streamed 476-coordinate slack presentation is pulled back to the exact
diagonal CSG solution.  This module reconstructs the unique slack coordinates
that make every source matrix ``diag(p_e, 1)``, verifies the full streamed core
there, and computes the exact QQ Jacobian of CPOBC plus strong GC.

The six pairwise commutators of the source-defined Q1,...,Q4 are differentiated
at the same point.  Comparing their rows with the core Jacobian row space tests
whether a first-order noncommutative escape exists.  Any emitted vector is only
a Zariski-tangent certificate; it is not promoted to a formal deformation or
an exact witness without higher-order lifting and all supplemental gates.

No Groebner basis, saturation, finite-field, numerical or Sage run is used.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from math import gcd, lcm
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

SLACK_INVENTORY_PATH = terms.SLACK_INVENTORY_PATH
TERM_PREFLIGHT_PATH = terms.RESULT_PATH
MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
RESULT_PATH = "results/v0.4.2_955_slack_csg_tangent.json"

SCHEMA = "final-theory-v042-955-slack-csg-tangent-v1"
VERDICT = "V042_955_SLACK_CSG_Q_TANGENT_ESCAPE_FIRST_ORDER_BLOCKED_CERTIFIED"

SparseRow = dict[int, Fraction]
NumericMatrix = tuple[
    tuple[Fraction, Fraction],
    tuple[Fraction, Fraction],
]


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


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _evaluate(polynomial: terms.Polynomial, assignment: list[Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in polynomial.items():
        value = Fraction(coefficient)
        for index in monomial:
            value *= assignment[index]
        total += value
    return total


def _value_and_gradient(
    polynomial: terms.Polynomial, assignment: list[Fraction]
) -> tuple[Fraction, SparseRow]:
    value = Fraction(0)
    gradient: SparseRow = {}
    for monomial, integer_coefficient in polynomial.items():
        coefficient = Fraction(integer_coefficient)
        factors = [assignment[index] for index in monomial]
        prefix = [Fraction(1)]
        for factor in factors:
            prefix.append(prefix[-1] * factor)
        suffix = [Fraction(1)] * (len(factors) + 1)
        for position in range(len(factors) - 1, -1, -1):
            suffix[position] = suffix[position + 1] * factors[position]
        value += coefficient * prefix[-1]
        for position, index in enumerate(monomial):
            derivative = coefficient * prefix[position] * suffix[position + 1]
            if derivative:
                updated = gradient.get(index, Fraction(0)) + derivative
                if updated:
                    gradient[index] = updated
                else:
                    gradient.pop(index, None)
    return value, gradient


def _numeric_matrix(polynomial: terms.Matrix, assignment: list[Fraction]) -> NumericMatrix:
    return tuple(
        tuple(_evaluate(polynomial[row][column], assignment) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _diagonal(value: Fraction) -> NumericMatrix:
    return ((value, Fraction(0)), (Fraction(0), Fraction(1)))


def _fraction_record(value: Fraction) -> str:
    return str(value)


def _row_record(row: SparseRow, names: list[str]) -> dict[str, str]:
    return {names[index]: str(value) for index, value in sorted(row.items())}


def _row_index_record(row: SparseRow) -> list[list[Any]]:
    return [[index, str(value)] for index, value in sorted(row.items())]


def _row_digest(rows: list[SparseRow]) -> str:
    return hashlib.sha256(
        _canonical_json([_row_index_record(row) for row in rows]).encode("utf-8")
    ).hexdigest()


def _reduce(row: SparseRow, basis: dict[int, SparseRow]) -> SparseRow:
    reduced = dict(row)
    for pivot in sorted(basis):
        factor = reduced.get(pivot, Fraction(0))
        if not factor:
            continue
        for index, value in basis[pivot].items():
            updated = reduced.get(index, Fraction(0)) - factor * value
            if updated:
                reduced[index] = updated
            else:
                reduced.pop(index, None)
    return reduced


def _extend_basis(basis: dict[int, SparseRow], rows: list[SparseRow]) -> dict[int, SparseRow]:
    result = {pivot: dict(row) for pivot, row in basis.items()}
    for source in rows:
        row = _reduce(source, result)
        if not row:
            continue
        pivot = min(row)
        scale = row[pivot]
        result[pivot] = {index: value / scale for index, value in row.items() if value}
    return result


def _echelon(rows: list[SparseRow]) -> dict[int, SparseRow]:
    return _extend_basis({}, rows)


def _echelon_digest(basis: dict[int, SparseRow]) -> str:
    return _row_digest([basis[pivot] for pivot in sorted(basis)])


def _dot(row: SparseRow, vector: SparseRow) -> Fraction:
    if len(row) > len(vector):
        row, vector = vector, row
    return sum(
        (value * vector.get(index, Fraction(0)) for index, value in row.items()), Fraction(0)
    )


def _kernel_vector_for_free_coordinate(
    basis: dict[int, SparseRow], variable_count: int, free_index: int
) -> SparseRow:
    pivots = set(basis)
    if free_index in pivots:
        raise AssertionError("kernel seed must be a free coordinate")
    vector: SparseRow = {free_index: Fraction(1)}
    for pivot in sorted(basis, reverse=True):
        row = basis[pivot]
        value = -sum(
            (
                coefficient * vector.get(index, Fraction(0))
                for index, coefficient in row.items()
                if index != pivot
            ),
            Fraction(0),
        )
        if value:
            vector[pivot] = value
    if any(_dot(row, vector) for row in basis.values()):
        raise AssertionError("back substitution failed to produce a kernel vector")
    if not 0 <= free_index < variable_count:
        raise AssertionError("free coordinate is outside the variable namespace")
    return vector


def _primitive_integer_vector(vector: SparseRow) -> dict[int, int]:
    common_denominator = 1
    for value in vector.values():
        common_denominator = lcm(common_denominator, value.denominator)
    integer = {
        index: value.numerator * (common_denominator // value.denominator)
        for index, value in vector.items()
        if value
    }
    common_divisor = 0
    for value in integer.values():
        common_divisor = gcd(common_divisor, abs(value))
    if common_divisor:
        integer = {index: value // common_divisor for index, value in integer.items()}
    if integer and integer[min(integer)] < 0:
        integer = {index: -value for index, value in integer.items()}
    return integer


def _build_csg_assignment(
    slack: dict[str, Any],
    mixed: dict[str, Any],
    matrices: dict[str, terms.Matrix],
    names: list[str],
) -> tuple[list[Fraction], dict[str, Any], dict[str, NumericMatrix]]:
    representative_to_orbit = {
        str(record["representative_occurrence_id"]): str(record["orbit_id"])
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    p_by_representative = {
        representative: Fraction(str(mixed["variables"]["CSG_diagonal_character"][orbit]))
        for representative, orbit in representative_to_orbit.items()
    }
    target = {
        representative: _diagonal(value) for representative, value in p_by_representative.items()
    }

    assignment = [Fraction(0)] * len(names)
    name_to_index = {name: index for index, name in enumerate(names)}
    timid = {
        str(record["timid_orbit_representative"]) for record in slack["timid_slack_recurrences"]
    }
    for representative in sorted(set(matrices) - timid):
        assignment[name_to_index[f"A:{representative}:00"]] = p_by_representative[representative]
        assignment[name_to_index[f"A:{representative}:11"]] = Fraction(1)

    paths = {
        str(record["source_id"]): list(record["operator_word_later_on_left"])
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    slack_values: dict[str, tuple[Fraction, Fraction]] = {}
    for record in slack["timid_slack_recurrences"]:
        source_id = str(record["source_id"])
        representative = str(record["timid_orbit_representative"])
        state_first = Fraction(1)
        for symbol in paths[source_id]:
            state_first *= p_by_representative[terms._operator(symbol)]
        if not state_first:
            raise AssertionError("the diagonal CSG reachable state became zero")

        base00 = Fraction(1)
        base11 = Fraction(1)
        for operator, coefficient in zip(
            record["non_timid_orbit_representatives"],
            record["non_timid_coefficients"],
            strict=True,
        ):
            base00 -= int(coefficient) * p_by_representative[str(operator)]
            base11 -= int(coefficient)
        difference00 = p_by_representative[representative] - base00
        difference10 = Fraction(0)
        if difference00 or difference10:
            raise AssertionError("CSG target is not compatible with the timid first column")
        u0 = Fraction(0)
        u1 = (Fraction(1) - base11) / state_first
        slack_values[source_id] = (u0, u1)
        assignment[name_to_index[f"u:{source_id}:0"]] = u0
        assignment[name_to_index[f"u:{source_id}:1"]] = u1

    matrix_failures = []
    determinant_values: dict[str, Fraction] = {}
    for representative, polynomial in sorted(matrices.items()):
        evaluated = _numeric_matrix(polynomial, assignment)
        if evaluated != target[representative]:
            matrix_failures.append(representative)
        determinant = evaluated[0][0] * evaluated[1][1] - evaluated[0][1] * evaluated[1][0]
        determinant_values[representative] = determinant
    if matrix_failures:
        raise AssertionError("slack inverse image does not reproduce every diagonal CSG matrix")
    if not all(determinant_values.values()):
        raise AssertionError("the diagonal CSG inverse image is singular")

    slack_records = [
        {
            "source_id": source_id,
            "u": [str(value[0]), str(value[1])],
            "nonzero_coordinates": sum(bool(coordinate) for coordinate in value),
        }
        for source_id, value in sorted(slack_values.items())
    ]
    nonzero_slack = [
        name
        for name, value in zip(names, assignment, strict=True)
        if name.startswith("u:") and value
    ]
    assignment_digest = hashlib.sha256(
        _canonical_json([str(value) for value in assignment]).encode("utf-8")
    ).hexdigest()
    return (
        assignment,
        {
            "coordinates": len(assignment),
            "assignment_sha256": assignment_digest,
            "slack_records": slack_records,
            "nonzero_slack_coordinates": nonzero_slack,
            "nonzero_slack_coordinate_count": len(nonzero_slack),
            "all_131_matrices_equal_diag_p_e_1": True,
            "all_131_determinants_nonzero": True,
            "determinant_value_histogram": {
                value: sum(str(determinant) == value for determinant in determinant_values.values())
                for value in sorted(
                    {str(determinant) for determinant in determinant_values.values()}
                )
            },
        },
        target,
    )


def _stream_jacobian_block(
    block_name: str,
    records: list[dict[str, Any]],
    identifier_keys: tuple[str, ...],
    matrices: dict[str, terms.Matrix],
    assignment: list[Fraction],
) -> tuple[list[SparseRow], dict[str, Any]]:
    ledger = terms.OperationLedger()
    census = terms.StreamCensus(block_name)
    rows: list[SparseRow] = []
    zero_gradient_entries = 0
    evaluation_failures: list[dict[str, Any]] = []
    gradient_digest = hashlib.sha256()
    for block_index, record in enumerate(records):
        left = terms._word_matrix(record["lhs_source_word"], matrices, ledger)
        right = terms._word_matrix(record["rhs_source_word"], matrices, ledger)
        for row in range(2):
            for column in range(2):
                residual = terms._add(
                    left[row][column],
                    terms._scale(-1, right[row][column], ledger),
                    ledger,
                )
                identifier = {
                    "block_index": block_index,
                    **{key: record[key] for key in identifier_keys if key in record},
                    "entry": f"{row}{column}",
                }
                census.add(identifier, residual)
                value, gradient = _value_and_gradient(residual, assignment)
                if value:
                    evaluation_failures.append({**identifier, "value": str(value)})
                if gradient:
                    rows.append(gradient)
                else:
                    zero_gradient_entries += 1
                gradient_digest.update(
                    _canonical_json([identifier, _row_index_record(gradient)]).encode("utf-8")
                )
                gradient_digest.update(b"\n")
    if evaluation_failures:
        raise AssertionError(f"diagonal CSG point fails {block_name}: {evaluation_failures[:3]}")
    return rows, {
        "scalar_entry_slots": census.scalar_entries,
        "polynomial_nonzero_entries": census.nonzero_entries,
        "jacobian_nonzero_rows": len(rows),
        "jacobian_zero_rows": zero_gradient_entries,
        "basepoint_residual_failures": 0,
        "polynomial_stream_digest_sha256": census.digest.hexdigest(),
        "gradient_stream_digest_sha256": gradient_digest.hexdigest(),
        "operation_ledger": ledger.serialize(),
    }


def _q_mapping(
    slack: dict[str, Any], mixed: dict[str, Any]
) -> tuple[dict[int, str], list[dict[str, Any]]]:
    orbit_to_representative = {
        str(record["orbit_id"]): str(record["representative_occurrence_id"])
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    q_orbits: dict[int, str] = {}
    records = mixed["Q_commutator_polynomials"]["records"]
    for record in records:
        for stage, orbit in zip(record["pair"], record["Q_orbits"], strict=True):
            previous = q_orbits.setdefault(int(stage), str(orbit))
            if previous != orbit:
                raise AssertionError("mixed predecessor assigns inconsistent source Q orbits")
    if set(q_orbits) != {1, 2, 3, 4}:
        raise AssertionError("source Q1,...,Q4 mapping is incomplete")
    return {stage: orbit_to_representative[orbit] for stage, orbit in q_orbits.items()}, records


def _q_commutator_jacobian(
    q_representatives: dict[int, str],
    matrices: dict[str, terms.Matrix],
    assignment: list[Fraction],
) -> tuple[list[SparseRow], list[dict[str, Any]], dict[str, Any]]:
    ledger = terms.OperationLedger()
    rows: list[SparseRow] = []
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for left in range(1, 5):
        for right in range(left + 1, 5):
            left_right = terms._matrix_multiply(
                matrices[q_representatives[left]],
                matrices[q_representatives[right]],
                ledger,
            )
            right_left = terms._matrix_multiply(
                matrices[q_representatives[right]],
                matrices[q_representatives[left]],
                ledger,
            )
            for row in range(2):
                for column in range(2):
                    polynomial = terms._add(
                        left_right[row][column],
                        terms._scale(-1, right_left[row][column], ledger),
                        ledger,
                    )
                    value, gradient = _value_and_gradient(polynomial, assignment)
                    if value:
                        raise AssertionError("source Q matrices do not commute at the CSG point")
                    identifier = {
                        "pair": [left, right],
                        "entry": f"{row}{column}",
                        "Q_representatives": [
                            q_representatives[left],
                            q_representatives[right],
                        ],
                    }
                    if gradient:
                        rows.append(gradient)
                    records.append(
                        {
                            **identifier,
                            "polynomial_terms": len(polynomial),
                            "gradient_nonzero": bool(gradient),
                            "gradient": _row_index_record(gradient),
                        }
                    )
                    digest.update(
                        _canonical_json([identifier, _row_index_record(gradient)]).encode("utf-8")
                    )
                    digest.update(b"\n")
    return (
        rows,
        records,
        {
            "commutator_pairs": 6,
            "scalar_entry_slots": 24,
            "nonzero_gradient_rows": len(rows),
            "zero_gradient_rows": 24 - len(rows),
            "gradient_stream_digest_sha256": digest.hexdigest(),
            "operation_ledger": ledger.serialize(),
        },
    )


def compile_slack_csg_tangent_v042(root: Path) -> dict[str, Any]:
    """Return the exact CSG-basepoint core and Q tangent comparison."""

    root = root.resolve()
    slack_path = root / SLACK_INVENTORY_PATH
    term_path = root / TERM_PREFLIGHT_PATH
    mixed_path = root / MIXED_MANIFEST_PATH
    slack = _load(slack_path)
    term_preflight = _load(term_path)
    mixed = _load(mixed_path)
    if slack.get(
        "schema_version"
    ) != "final-theory-v042-955-source-native-slack-compiler-v1" or slack.get(
        "semantic_digest_sha256"
    ) != terms._semantic_digest(slack):
        raise AssertionError("slack inventory predecessor binding failed")
    if (
        term_preflight.get("schema_version")
        != "final-theory-v042-955-slack-streamed-term-preflight-v1"
        or term_preflight.get("verdict")
        != "V042_955_SLACK_STREAMED_TERM_PREFLIGHT_CERTIFIED_NO_SOLVER"
        or term_preflight.get("semantic_digest_sha256") != terms._semantic_digest(term_preflight)
    ):
        raise AssertionError("term preflight predecessor binding failed")
    if (
        mixed.get("schema_version") != "final-theory-v042-955-mixed-source-native-manifest-v1"
        or mixed.get("verdict")
        != "V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN"
        or mixed.get("semantic_digest_sha256") != terms._semantic_digest(mixed)
    ):
        raise AssertionError("mixed CSG-character predecessor binding failed")

    names: list[str] = []
    matrices, _states, expansion = terms._compile_matrices(slack, names)
    if names != term_preflight["variable_namespace"]["names"]:
        raise AssertionError("tangent variable namespace differs from the term preflight")
    assignment, basepoint, target_matrices = _build_csg_assignment(slack, mixed, matrices, names)

    cpobc_rows, cpobc_profile = _stream_jacobian_block(
        "CPOBC",
        slack["raw_source_system"]["CPOBC_equations"],
        ("relation_id", "equation_id"),
        matrices,
        assignment,
    )
    gc_rows, gc_profile = _stream_jacobian_block(
        "strong_GC",
        slack["raw_source_system"]["strong_GC_basis"],
        ("relation_id", "endpoint_causet_id"),
        matrices,
        assignment,
    )
    if (
        cpobc_profile["polynomial_stream_digest_sha256"]
        != term_preflight["streamed_core_system"]["per_block"]["CPOBC"]["stream_digest_sha256"]
    ):
        raise AssertionError("CPOBC scalar stream drifted from the term preflight")
    if (
        gc_profile["polynomial_stream_digest_sha256"]
        != term_preflight["streamed_core_system"]["per_block"]["strong_GC"]["stream_digest_sha256"]
    ):
        raise AssertionError("strong-GC scalar stream drifted from the term preflight")

    cpobc_basis = _echelon(cpobc_rows)
    gc_basis = _echelon(gc_rows)
    core_rows = cpobc_rows + gc_rows
    core_basis = _echelon(core_rows)
    q_representatives, _mixed_q_records = _q_mapping(slack, mixed)
    q_rows, q_records, q_profile = _q_commutator_jacobian(q_representatives, matrices, assignment)
    q_basis = _echelon(q_rows)
    core_plus_q_basis = _extend_basis(core_basis, q_rows)
    q_modulo_core_rank = len(core_plus_q_basis) - len(core_basis)
    q_rowspace_remainder_failures = sum(bool(_reduce(row, core_basis)) for row in q_rows)
    if q_modulo_core_rank or q_rowspace_remainder_failures:
        raise AssertionError("source Q has an unexpected first-order tangent escape")

    escaped_q_row: SparseRow | None = None
    escaped_q_record: dict[str, Any] | None = None
    for record in q_records:
        gradient = {int(index): Fraction(value) for index, value in record["gradient"]}
        if gradient and _reduce(gradient, core_basis):
            escaped_q_row = gradient
            escaped_q_record = record
            break

    tangent_vector: SparseRow | None = None
    if escaped_q_row is not None:
        free_coordinates = sorted(set(range(len(names))) - set(core_basis))
        for free_index in free_coordinates:
            candidate = _kernel_vector_for_free_coordinate(core_basis, len(names), free_index)
            if _dot(escaped_q_row, candidate):
                tangent_vector = candidate
                break
        if tangent_vector is None:
            raise AssertionError("Q row escapes the core rowspace but no kernel vector detects it")

    blind_names = term_preflight["streamed_core_system"]["variable_support"][
        "coordinates_absent_from_entire_core"
    ]
    name_to_index = {name: index for index, name in enumerate(names)}
    blind_indices = [name_to_index[name] for name in blind_names]
    blind_core_failures = sum(
        any(row.get(index, Fraction(0)) for row in core_rows) for index in blind_indices
    )
    blind_q_failures = sum(
        any(row.get(index, Fraction(0)) for row in q_rows) for index in blind_indices
    )
    if blind_core_failures or blind_q_failures:
        raise AssertionError("a terminal slack blind direction unexpectedly affects core or Q")

    tangent_certificate: dict[str, Any] | None = None
    if tangent_vector is not None and escaped_q_record is not None:
        primitive = _primitive_integer_vector(tangent_vector)
        primitive_fraction = {index: Fraction(value) for index, value in primitive.items()}
        core_failures = sum(bool(_dot(row, primitive_fraction)) for row in core_rows)
        q_values = [_dot(row, primitive_fraction) for row in q_rows]
        if core_failures or not any(q_values):
            raise AssertionError("explicit tangent escape vector failed independent dot checks")
        tangent_certificate = {
            "selected_Q_entry": {
                key: escaped_q_record[key] for key in ("pair", "entry", "Q_representatives")
            },
            "support": len(primitive),
            "primitive_integer_coordinates": {
                names[index]: str(value) for index, value in sorted(primitive.items())
            },
            "coordinate_digest_sha256": hashlib.sha256(
                _canonical_json(
                    [[names[index], str(value)] for index, value in sorted(primitive.items())]
                ).encode("utf-8")
            ).hexdigest(),
            "core_Jacobian_rows_checked": len(core_rows),
            "core_directional_derivative_failures": core_failures,
            "Q_gradient_rows_checked": len(q_rows),
            "nonzero_Q_directional_derivatives": sum(bool(value) for value in q_values),
            "Q_directional_derivative_values": [str(value) for value in q_values],
            "selected_Q_directional_derivative": str(_dot(escaped_q_row, primitive_fraction)),
            "is_Zariski_tangent_only": True,
            "formal_or_exact_deformation_claimed": False,
        }

    determinant_values = []
    for _representative, polynomial in sorted(matrices.items()):
        matrix = _numeric_matrix(polynomial, assignment)
        determinant_values.append(matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0])
    if target_matrices.keys() != matrices.keys() or not all(determinant_values):
        raise AssertionError("basepoint nonsingularity self-check failed")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "basepoint": "diagonal CSG t_j=1 source matrices",
        },
        "input_bindings": {
            SLACK_INVENTORY_PATH: {
                "raw_sha256": _sha256(slack_path),
                "semantic_digest_sha256": slack["semantic_digest_sha256"],
            },
            TERM_PREFLIGHT_PATH: {
                "raw_sha256": _sha256(term_path),
                "semantic_digest_sha256": term_preflight["semantic_digest_sha256"],
            },
            MIXED_MANIFEST_PATH: {
                "raw_sha256": _sha256(mixed_path),
                "semantic_digest_sha256": mixed["semantic_digest_sha256"],
            },
        },
        "variable_namespace": {
            "coordinates": len(names),
            "names_sha256": term_preflight["variable_namespace"]["names_sha256"],
        },
        "basepoint_inverse_image": basepoint,
        "timid_expansion_recheck": {
            "expanded_matrices": expansion["expanded_matrix_count"],
            "expanded_states": expansion["expanded_state_count"],
            "operation_ledger": expansion["operation_ledger"],
        },
        "core_Jacobian": {
            "per_block": {
                "CPOBC": {
                    **cpobc_profile,
                    "rank": len(cpobc_basis),
                    "echelon_digest_sha256": _echelon_digest(cpobc_basis),
                },
                "strong_GC": {
                    **gc_profile,
                    "rank": len(gc_basis),
                    "echelon_digest_sha256": _echelon_digest(gc_basis),
                },
            },
            "combined_nonzero_rows": len(core_rows),
            "combined_rank": len(core_basis),
            "tangent_dimension": len(names) - len(core_basis),
            "combined_echelon_digest_sha256": _echelon_digest(core_basis),
            "basepoint_residual_failures": 0,
        },
        "Q_commutator_Jacobian": {
            "Q_representatives": {
                f"Q{stage}": representative
                for stage, representative in sorted(q_representatives.items())
            },
            **q_profile,
            "raw_rank": len(q_basis),
            "raw_echelon_digest_sha256": _echelon_digest(q_basis),
            "rank_after_appending_to_core": len(core_plus_q_basis),
            "rank_modulo_core_rowspace": q_modulo_core_rank,
            "nonzero_rowspace_remainders": q_rowspace_remainder_failures,
            "all_Q_gradients_in_core_rowspace": q_modulo_core_rank == 0,
            "first_order_Q_tangent_escape_exists": q_modulo_core_rank > 0,
            "records": q_records,
        },
        "terminal_slack_blind_directions": {
            "coordinates": blind_names,
            "count": len(blind_names),
            "all_standard_basis_directions_in_core_tangent_kernel": True,
            "all_Q_commutator_directional_derivatives_zero": True,
            "core_failures": blind_core_failures,
            "Q_failures": blind_q_failures,
            "interpretation": (
                "These global terminal-source freedoms preserve the common core but do not "
                "themselves move the source-defined Q commutators at first order."
            ),
        },
        "explicit_Q_tangent_escape_certificate": tangent_certificate,
        "open_conditions_at_basepoint": {
            "source_determinants_checked": len(determinant_values),
            "source_determinant_failures": sum(not value for value in determinant_values),
            "N_nonzero": basepoint["nonzero_slack_coordinate_count"] > 0,
            "nonzero_slack_coordinate_count": basepoint["nonzero_slack_coordinate_count"],
            "open_conditions_impose_no_linear_tangent_equations": True,
        },
        "execution_decision": {
            "generic_solver_authorised": False,
            "higher_order_lifting_authorised": q_modulo_core_rank > 0,
            "second_order_obstruction_audit_authorised": q_modulo_core_rank == 0,
            "next_gate": (
                "LIFT_THE_EXPLICIT_Q_ESCAPE_DIRECTION_TO_SECOND_ORDER_AND_TEST_"
                "SUPPLEMENTAL_EQ113_EQ139_ONLY_IF_THE_SECOND_ORDER_OBSTRUCTION_VANISHES"
                if q_modulo_core_rank > 0
                else "COMPUTE_THE_SECOND_ORDER_Q_OBSTRUCTION_ON_THE_CSG_TANGENT_KERNEL"
            ),
        },
        "solver_status": {
            "exact_sparse_QQ_linear_algebra_runs": 1,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "The basepoint is an exact nonsingular source-native 955 common-core solution.",
            "A tangent escape, if present, is first-order only and is not an exact witness.",
            "The 16 terminal slack blind directions are Q-silent at first order.",
            "Higher-order core lifting, Eq113, Eq139 and exact Q noncommutativity remain required.",
            "No unrestricted source-native 955 terminal verdict is claimed.",
        ],
        "unrestricted_source_native_955_status": "OPEN",
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_csg_tangent_v042(root: Path) -> Path:
    payload = compile_slack_csg_tangent_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_csg_tangent_v042(repository_root))
