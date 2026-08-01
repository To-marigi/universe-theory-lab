"""Exact lower-left tangent audit at the frozen weak/weak SR2 witness.

Every ON transition is deformed as

``A_e(epsilon) = A_e(0) + epsilon*y_e*E_21``

around the exact v0.4 witness.  Dual-number arithmetic retains the full first
derivative of products, inverses, source cylinder states, and source-matched
MSR actions.  This is a Zariski-tangent calculation at one point, not a global
obstruction to reachable-visible witnesses.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_baseline_lower_tangent.json"
TORUS_RESULT_PATH = torus.RESULT_PATH

SCHEMA = "final-theory-v042-sr2v-baseline-lower-tangent-v1"
VERDICT = "SR2V_BASELINE_LOWER_TANGENT_VISIBILITY_OBSTRUCTED"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_SINGLE_POINT_TANGENT_ONLY"

SparseRow = dict[str, Fraction]
Deformation = Literal["pure_lower", "full_matrix"]


@dataclass(frozen=True)
class Dual:
    value: Fraction
    derivative: SparseRow


DualMatrix = tuple[tuple[Dual, Dual], tuple[Dual, Dual]]
DualVector = tuple[Dual, Dual]


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


def _constant(value: Fraction | int) -> Dual:
    return Dual(Fraction(value), {})


def _variable(name: str) -> Dual:
    return Dual(Fraction(0), {name: Fraction(1)})


def _add(left: Dual, right: Dual) -> Dual:
    return Dual(left.value + right.value, torus._add_rows(left.derivative, right.derivative))


def _negate(value: Dual) -> Dual:
    return Dual(-value.value, torus._scale_row(-1, value.derivative))


def _subtract(left: Dual, right: Dual) -> Dual:
    return _add(left, _negate(right))


def _scale(coefficient: Fraction | int, value: Dual) -> Dual:
    scalar = Fraction(coefficient)
    return Dual(scalar * value.value, torus._scale_row(scalar, value.derivative))


def _multiply(left: Dual, right: Dual) -> Dual:
    return Dual(
        left.value * right.value,
        torus._add_rows(
            torus._scale_row(left.value, right.derivative),
            torus._scale_row(right.value, left.derivative),
        ),
    )


def _inverse_scalar(value: Dual) -> Dual:
    if not value.value:
        raise ZeroDivisionError("dual inverse requires a nonzero base value")
    return Dual(
        Fraction(1, 1) / value.value,
        torus._scale_row(-Fraction(1, 1) / value.value**2, value.derivative),
    )


def _zero_matrix() -> DualMatrix:
    zero = _constant(0)
    return ((zero, zero), (zero, zero))


def _identity() -> DualMatrix:
    zero = _constant(0)
    one = _constant(1)
    return ((one, zero), (zero, one))


def _matrix_add(left: DualMatrix, right: DualMatrix) -> DualMatrix:
    return (
        (_add(left[0][0], right[0][0]), _add(left[0][1], right[0][1])),
        (_add(left[1][0], right[1][0]), _add(left[1][1], right[1][1])),
    )


def _matrix_subtract(left: DualMatrix, right: DualMatrix) -> DualMatrix:
    return (
        (_subtract(left[0][0], right[0][0]), _subtract(left[0][1], right[0][1])),
        (_subtract(left[1][0], right[1][0]), _subtract(left[1][1], right[1][1])),
    )


def _matrix_scale(coefficient: Fraction | int, matrix: DualMatrix) -> DualMatrix:
    return (
        (_scale(coefficient, matrix[0][0]), _scale(coefficient, matrix[0][1])),
        (_scale(coefficient, matrix[1][0]), _scale(coefficient, matrix[1][1])),
    )


def _matrix_multiply(left: DualMatrix, right: DualMatrix) -> DualMatrix:
    entries = []
    for row in range(2):
        output_row = []
        for column in range(2):
            output_row.append(
                _add(
                    _multiply(left[row][0], right[0][column]),
                    _multiply(left[row][1], right[1][column]),
                )
            )
        entries.append(tuple(output_row))
    return entries[0], entries[1]  # type: ignore[return-value]


def _matrix_word(factors: Any) -> DualMatrix:
    product = _identity()
    for factor in factors:
        product = _matrix_multiply(product, factor)
    return product


def _matrix_inverse(matrix: DualMatrix) -> DualMatrix:
    determinant = _subtract(
        _multiply(matrix[0][0], matrix[1][1]),
        _multiply(matrix[0][1], matrix[1][0]),
    )
    inverse_determinant = _inverse_scalar(determinant)
    return (
        (
            _multiply(inverse_determinant, matrix[1][1]),
            _multiply(inverse_determinant, _negate(matrix[0][1])),
        ),
        (
            _multiply(inverse_determinant, _negate(matrix[1][0])),
            _multiply(inverse_determinant, matrix[0][0]),
        ),
    )


def _apply_to_omega(matrix: DualMatrix) -> DualVector:
    return matrix[0][0], matrix[1][0]


def _apply_matrix(matrix: DualMatrix, vector: DualVector) -> DualVector:
    return (
        _add(_multiply(matrix[0][0], vector[0]), _multiply(matrix[0][1], vector[1])),
        _add(_multiply(matrix[1][0], vector[0]), _multiply(matrix[1][1], vector[1])),
    )


def _derivative_rows_of_zero_matrix(matrix: DualMatrix) -> list[SparseRow]:
    rows = []
    for row in matrix:
        for entry in row:
            if entry.value:
                raise AssertionError("the frozen base point violates an operator equality")
            rows.append(entry.derivative)
    return rows


def _derivative_rows_of_zero_vector(vector: DualVector) -> list[SparseRow]:
    rows = []
    for entry in vector:
        if entry.value:
            raise AssertionError("the frozen base point violates a statewise equality")
        rows.append(entry.derivative)
    return rows


def _independent_labels(
    labelled_rows: list[tuple[str, SparseRow]],
    variables: tuple[str, ...],
) -> list[str]:
    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    selected = []
    for label, source in labelled_rows:
        row = {positions[variable]: value for variable, value in source.items() if value}
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                selected.append(label)
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return selected


def _label_is_lower_component(label: str) -> bool:
    if label.startswith(("CPOBC:", "Eq113:", "Eq139:")):
        return label.endswith(":2")
    if label.startswith(("fixed-GC:", "reachable-MSR:")):
        return label.endswith(":1")
    raise ValueError(f"unknown tangent row label: {label}")


def _normalised_lower_row(row: SparseRow, deformation: Deformation) -> SparseRow:
    if deformation == "pure_lower":
        return dict(row)
    return {
        variable.removesuffix(":10"): value
        for variable, value in row.items()
        if variable.endswith(":10") and value
    }


def _labelled_rows_digest(labelled_rows: list[tuple[str, SparseRow]]) -> str:
    serialised = [
        [label, [[variable, str(value)] for variable, value in sorted(row.items())]]
        for label, row in labelled_rows
    ]
    return hashlib.sha256(_canonical_json(serialised).encode("utf-8")).hexdigest()


def _transition(
    stage: int,
    relation: tuple[int, ...],
    precursor: int,
    variable: str,
    deformation: Deformation,
    upper_coordinates: dict[str, Fraction] | None = None,
) -> DualMatrix:
    probability = torus._csg(stage, relation, precursor)
    if upper_coordinates is None:
        upper_right = Fraction(4, 2**stage) if precursor == 0 else Fraction(0)
    else:
        upper_right = upper_coordinates.get(variable, Fraction(0))
    if deformation == "pure_lower":
        return (
            (_constant(probability), _constant(upper_right)),
            (_variable(variable), _constant(1)),
        )
    if deformation != "full_matrix":
        raise ValueError(f"unknown deformation: {deformation}")
    return (
        (
            _add(_constant(probability), _variable(f"{variable}:00")),
            _add(_constant(upper_right), _variable(f"{variable}:01")),
        ),
        (
            _variable(f"{variable}:10"),
            _add(_constant(1), _variable(f"{variable}:11")),
        ),
    )


def _compile(
    root: Path,
    deformation: Deformation = "pure_lower",
    upper_coordinates: dict[str, Fraction] | None = None,
) -> dict[str, Any]:
    context = torus._build_context(root)

    def occurrence(occurrence_id: str) -> DualMatrix:
        record = context.occurrence_records[occurrence_id]
        return _transition(
            int(record["stage"]),
            tuple(int(row) for row in record["source_relation_rows"]),
            int(record["precursor_code"]),
            context.occurrence_variables[occurrence_id],
            deformation,
            upper_coordinates,
        )

    def from_signature(stage: int, relation_code: int, precursor: int) -> DualMatrix:
        variable = context.signature_variables[(stage, relation_code, precursor)]
        return _transition(
            stage,
            torus._decode_relation(stage, relation_code),
            precursor,
            variable,
            deformation,
            upper_coordinates,
        )

    def q(stage: int) -> DualMatrix:
        variable = torus._q_variable(context, stage)
        return _transition(
            stage,
            (0,) * stage,
            0,
            variable,
            deformation,
            upper_coordinates,
        )

    occurrence_matrices = {
        occurrence_id: occurrence(occurrence_id)
        for occurrence_id in context.occurrence_records
    }
    labelled_rows: list[tuple[str, SparseRow]] = []
    group_counts: dict[str, int] = {}
    start = 0

    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            left = _matrix_word(
                occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"]
            )
            right = _matrix_word(
                occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
            )
            residual = _matrix_subtract(left, right)
            for entry_index, row in enumerate(_derivative_rows_of_zero_matrix(residual)):
                labelled_rows.append(
                    (
                        f"CPOBC:{relation['relation_id']}:{equation['equation_id']}:{entry_index}",
                        row,
                    )
                )
    group_counts["CPOBC_operator"] = len(labelled_rows) - start
    start = len(labelled_rows)

    def eq113_token(token: str) -> DualMatrix:
        if token.startswith("Q_"):
            return q(int(token.removeprefix("Q_")))
        kind, identifier = token.split(":", maxsplit=1)
        stage, relation, precursor, variable = context.b_signatures[identifier]
        matrix = _transition(
            stage,
            relation,
            precursor,
            variable,
            deformation,
            upper_coordinates,
        )
        return _matrix_inverse(matrix) if kind == "BINV" else matrix

    for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        for relation in context.eq112["path_consistency_branches"][branch]:
            residual = _matrix_subtract(
                _matrix_word(eq113_token(token) for token in relation["lhs_word"]),
                _matrix_word(eq113_token(token) for token in relation["rhs_word"]),
            )
            for entry_index, row in enumerate(_derivative_rows_of_zero_matrix(residual)):
                labelled_rows.append(
                    (f"Eq113:{branch}:{relation['causet_id']}:{entry_index}", row)
                )
    group_counts["Eq113_operator_both_branches"] = len(labelled_rows) - start
    start = len(labelled_rows)

    for stage, left_index, right_index in torus._eq139_instances(torus.EQ139_COMPLETED):
        left_transition = from_signature(stage, 0, (1 << left_index) - 1)
        right_transition = from_signature(stage, 0, (1 << right_index) - 1)
        current_q = q(stage)
        next_q = q(stage + 1)
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
        residual = _matrix_subtract(left, right)
        for entry_index, row in enumerate(_derivative_rows_of_zero_matrix(residual)):
            labelled_rows.append((f"Eq139:{stage}:{left_index}:{right_index}:{entry_index}", row))
    group_counts["Eq139_operator_completed"] = len(labelled_rows) - start
    start = len(labelled_rows)

    path_matrices: dict[str, DualMatrix] = {}
    path_records: dict[str, dict[str, Any]] = {}
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
            path_matrices[path_id] = product
            path_records[path_id] = path

    for relation in context.operator_gc["generating_relation_basis"]:
        residual = _matrix_subtract(
            path_matrices[relation["lhs_path_id"]],
            path_matrices[relation["rhs_path_id"]],
        )
        for component, row in enumerate(
            _derivative_rows_of_zero_vector(_apply_to_omega(residual))
        ):
            labelled_rows.append((f"fixed-GC:{relation['relation_id']}:{component}", row))
    group_counts["fixed_vector_GC_basis"] = len(labelled_rows) - start
    start = len(labelled_rows)

    anchors: dict[str, DualMatrix] = {}
    for path_id, path in sorted(path_records.items()):
        anchors.setdefault(str(path["endpoint_causet_id"]), path_matrices[path_id])
    for constraint in context.cpobc["MSR_operator_constraints"]:
        residual = _matrix_scale(int(constraint["identity_coefficient"]), _identity())
        for term in constraint["terms"]:
            residual = _matrix_add(
                residual,
                _matrix_scale(int(term["coefficient"]), occurrence_matrices[term["transition_id"]]),
            )
        source_state = _apply_to_omega(anchors[str(constraint["source_id"])])
        action = _apply_matrix(residual, source_state)
        for component, row in enumerate(_derivative_rows_of_zero_vector(action)):
            labelled_rows.append((f"reachable-MSR:{constraint['constraint_id']}:{component}", row))
    group_counts["reachable_state_MSR"] = len(labelled_rows) - start

    if deformation == "pure_lower":
        variables = context.variables
    else:
        variables = tuple(
            f"{variable}:{entry}"
            for variable in context.variables
            for entry in ("00", "01", "10", "11")
        )
    rows = [row for _, row in labelled_rows]
    echelon = torus._row_echelon(rows, variables)
    selected_labels = _independent_labels(labelled_rows, variables)
    nullspace = torus._nullspace_basis_from_echelon(echelon, variables)

    lower_component_rows = [
        (label, _normalised_lower_row(row, deformation))
        for label, row in labelled_rows
        if _label_is_lower_component(label)
    ]
    lower_component_echelon = torus._row_echelon(
        (row for _, row in lower_component_rows),
        context.variables,
    )
    lower_component_kernel = torus._nullspace_basis_from_echelon(
        lower_component_echelon,
        context.variables,
    )

    prefix_ranks = {}
    end = 0
    for group, count in group_counts.items():
        end += count
        prefix_ranks[group] = len(torus._row_echelon(rows[:end], variables))

    reach_rows: list[SparseRow] = []
    for matrix in path_matrices.values():
        reach_rows.append(matrix[1][0].derivative)
    reachable_free = [
        index
        for index, row in enumerate(reach_rows)
        if torus._row_remainder(row, echelon, variables)
    ]

    commutator_actions = {}
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        commutator = _matrix_subtract(
            _matrix_multiply(q(left_stage), q(right_stage)),
            _matrix_multiply(q(right_stage), q(left_stage)),
        )
        free_actions = 0
        for state in path_matrices.values():
            action = _apply_matrix(commutator, _apply_to_omega(state))
            for row in _derivative_rows_of_zero_vector(action):
                free_actions += int(bool(torus._row_remainder(row, echelon, variables)))
        commutator_actions[f"Q{left_stage}_Q{right_stage}"] = {
            "tested_action_components": 2 * len(path_matrices),
            "first_order_actions_not_forced_zero": free_actions,
        }

    if deformation == "pure_lower":
        lower_coordinates = set(variables)
        external_lower_coordinate = torus.Q5
    else:
        lower_coordinates = {variable for variable in variables if variable.endswith(":10")}
        external_lower_coordinate = f"{torus.Q5}:10"
    lower_kernel_support = sorted(
        {
            variable
            for vector in nullspace
            for variable, value in vector.items()
            if value and variable in lower_coordinates
        }
    )
    in_scope_lower_kernel_support = [
        variable for variable in lower_kernel_support if variable != external_lower_coordinate
    ]

    return {
        "context": context,
        "deformation": deformation,
        "variable_count": len(variables),
        "group_counts": group_counts,
        "prefix_ranks": prefix_ranks,
        "rank": len(echelon),
        "nullity": len(variables) - len(echelon),
        "nullspace_basis": [
            {variable: str(value) for variable, value in sorted(vector.items())}
            for vector in nullspace
        ],
        "lower_coordinate_count": len(lower_coordinates),
        "lower_coordinates_with_kernel_support": lower_kernel_support,
        "in_scope_lower_coordinates_with_kernel_support": in_scope_lower_kernel_support,
        "selected_labels": selected_labels,
        "invariant_line_breaking_subsystem": {
            "row_count": len(lower_component_rows),
            "rank": len(lower_component_echelon),
            "nullity": len(context.variables) - len(lower_component_echelon),
            "nullspace_basis": [
                {variable: str(value) for variable, value in sorted(vector.items())}
                for vector in lower_component_kernel
            ],
            "selected_labels": _independent_labels(
                lower_component_rows,
                context.variables,
            ),
            "normalised_rows_sha256": _labelled_rows_digest(lower_component_rows),
        },
        "path_count": len(path_matrices),
        "reachable_lower_component_functionals": len(reach_rows),
        "reachable_lower_components_not_forced_zero": len(reachable_free),
        "commutator_actions": commutator_actions,
    }


def build_payload(root: Path) -> dict[str, Any]:
    pure_lower = _compile(root, "pure_lower")
    full_matrix = _compile(root, "full_matrix")
    zero_upper_full_matrix = _compile(root, "full_matrix", {})
    pure_context: torus.ScoutContext = pure_lower.pop("context")
    full_context: torus.ScoutContext = full_matrix.pop("context")
    zero_upper_context: torus.ScoutContext = zero_upper_full_matrix.pop("context")
    if not (
        pure_context.variables
        == full_context.variables
        == zero_upper_context.variables
    ):
        raise AssertionError("the tangent compilers used different ON inventories")
    pure_breaking = pure_lower["invariant_line_breaking_subsystem"]
    full_breaking = full_matrix["invariant_line_breaking_subsystem"]
    zero_upper_breaking = zero_upper_full_matrix["invariant_line_breaking_subsystem"]
    gates = {
        "ON_transition_variable_count_is_132_including_Q5": (
            len(pure_context.variables) == 132
        ),
        "pure_lower_rank_is_131_with_only_external_Q5_kernel": (
            pure_lower["rank"] == 131
            and pure_lower["nullity"] == 1
            and pure_lower["lower_coordinates_with_kernel_support"] == [torus.Q5]
        ),
        "full_matrix_rank_is_455_with_73_dimensional_tangent": (
            full_matrix["rank"] == 455 and full_matrix["nullity"] == 73
        ),
        "no_in_scope_lower_coordinate_occurs_in_either_kernel": (
            not pure_lower["in_scope_lower_coordinates_with_kernel_support"]
            and not full_matrix["in_scope_lower_coordinates_with_kernel_support"]
        ),
        "invariant_line_breaking_subsystem_has_rank_131": (
            pure_breaking["row_count"] == 1187
            and pure_breaking["rank"] == 131
            and pure_breaking["nullspace_basis"] == [{torus.Q5: "1"}]
        ),
        "normalised_lower_rows_are_identical_across_deformation_and_upper_base": (
            pure_breaking["normalised_rows_sha256"]
            == full_breaking["normalised_rows_sha256"]
            == zero_upper_breaking["normalised_rows_sha256"]
        ),
        "no_first_order_reachable_rank_escape_in_either_problem": all(
            problem["reachable_lower_components_not_forced_zero"] == 0
            for problem in (pure_lower, full_matrix)
        ),
        "no_first_order_commutator_visibility_escape_in_either_problem": all(
            record["first_order_actions_not_forced_zero"] == 0
            for problem in (pure_lower, full_matrix)
            for record in problem["commutator_actions"].values()
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"baseline lower tangent audit changed: {gates}")
    input_paths = (
        torus.CPOBC_PATH,
        torus.REDUCTION_PATH,
        torus.OPERATOR_GC_PATH,
        torus.ATOMISATION_PATH,
        torus.EQ112_PATH,
        TORUS_RESULT_PATH,
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-01",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {relative: _sha256(root / relative) for relative in sorted(input_paths)},
        "base_point": {
            "source": "frozen v0.4 exact SR2 witness formula",
            "matrix": "[[p_e,g_e],[0,1]]",
            "initial_vector": "e_1",
            "deformation": "A_e + epsilon*y_e*E_21, epsilon^2=0",
        },
        "tangent_problem": {
            "arithmetic": "exact Fraction dual numbers over QQ",
            "pure_lower": pure_lower,
            "full_matrix": full_matrix,
            "zero_upper_full_matrix_control": {
                "rank": zero_upper_full_matrix["rank"],
                "nullity": zero_upper_full_matrix["nullity"],
                "in_scope_lower_coordinates_with_kernel_support": zero_upper_full_matrix[
                    "in_scope_lower_coordinates_with_kernel_support"
                ],
                "reachable_lower_components_not_forced_zero": zero_upper_full_matrix[
                    "reachable_lower_components_not_forced_zero"
                ],
                "invariant_line_breaking_subsystem": zero_upper_breaking,
            },
            "upper_right_independence_lemma": {
                "statement": (
                    "At an upper-triangular base [[p,x],[0,1]], the lower-left component "
                    "of a product derivative uses only p, 1, and lower-left derivatives; "
                    "the corresponding inverse derivative is -dy/p. Hence the extracted "
                    "1187-row subsystem is independent of every base upper-right x."
                ),
                "machine_guard": (
                    "The normalized row digest agrees for pure-lower and full-matrix "
                    "differentiation and for the frozen noncommutative and zero-upper bases."
                ),
                "normalised_rows_sha256": pure_breaking["normalised_rows_sha256"],
            },
        },
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "The pure-lower tangent has only the out-of-cutoff Q5 direction. Even after all "
            "four entries of every matrix are allowed to vary, no in-scope lower-left "
            "coordinate occurs in the exact tangent kernel, and every first-order "
            "reachable-rank and commutator-visibility functional vanishes. This excludes a "
            "visible first-order escape through the frozen point only; it does not exclude "
            "higher-order branching, another component, another base point, or arbitrary GL_2."
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
