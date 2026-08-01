"""Exact SR2-V observability audit for the frozen v0.4 weak witness.

This module is deliberately independent of :mod:`weak_d2_v04`.  It rebuilds
the transition formula, cylinder states, GC/MSR residual actions, and Q
commutators from frozen source inventories using only standard-library exact
``Fraction`` arithmetic.

The audit concerns operator action on genuine compiled cylinder states in the
common two-dimensional representation space.  It does *not* claim that a
mixed-stage word ``Q_i Q_j`` is itself a legal chronological growth path.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

WEAK_RESULT_PATH = "results/v0.4_weak_d2_classification.json"
OPERATOR_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
RESULT_PATH = "results/v0.4.2_sr2v_baseline_observability.json"

SCHEMA = "final-theory-v042-sr2v-baseline-observability-v1"
VERDICT = "SR2V_BASELINE_OBSERVABILITY_AUDIT_CERTIFIED"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_BASELINE_AUDIT_ONLY"

Matrix2 = tuple[
    tuple[Fraction, Fraction],
    tuple[Fraction, Fraction],
]
Vector2 = tuple[Fraction, Fraction]

ZERO_MATRIX: Matrix2 = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0)))
IDENTITY: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
OMEGA: Vector2 = (Fraction(1), Fraction(0))
ZERO_VECTOR: Vector2 = (Fraction(0), Fraction(0))


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


def _matrix_record(matrix: Matrix2) -> list[list[str]]:
    return [[str(entry) for entry in row] for row in matrix]


def _vector_record(vector: Vector2) -> list[str]:
    return [str(entry) for entry in vector]


def _matrix_from_record(value: Any) -> Matrix2:
    if not isinstance(value, list) or len(value) != 2:
        raise AssertionError("a serialized 2 by 2 matrix is required")
    rows = []
    for row in value:
        if not isinstance(row, list) or len(row) != 2:
            raise AssertionError("a serialized 2 by 2 matrix is required")
        rows.append((Fraction(str(row[0])), Fraction(str(row[1]))))
    return rows[0], rows[1]


def _add(left: Matrix2, right: Matrix2) -> Matrix2:
    return (
        (left[0][0] + right[0][0], left[0][1] + right[0][1]),
        (left[1][0] + right[1][0], left[1][1] + right[1][1]),
    )


def _subtract(left: Matrix2, right: Matrix2) -> Matrix2:
    return (
        (left[0][0] - right[0][0], left[0][1] - right[0][1]),
        (left[1][0] - right[1][0], left[1][1] - right[1][1]),
    )


def _scale(coefficient: int, matrix: Matrix2) -> Matrix2:
    scalar = Fraction(coefficient)
    return (
        (scalar * matrix[0][0], scalar * matrix[0][1]),
        (scalar * matrix[1][0], scalar * matrix[1][1]),
    )


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


def _apply(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def _commutator(left: Matrix2, right: Matrix2) -> Matrix2:
    return _subtract(_multiply(left, right), _multiply(right, left))


def _determinant_of_vectors(left: Vector2, right: Vector2) -> Fraction:
    return left[0] * right[1] - left[1] * right[0]


def _vector_rank(vectors: list[Vector2]) -> tuple[int, tuple[int, ...]]:
    nonzero = [index for index, vector in enumerate(vectors) if vector != ZERO_VECTOR]
    if not nonzero:
        return 0, ()
    first = nonzero[0]
    for second in nonzero[1:]:
        if _determinant_of_vectors(vectors[first], vectors[second]) != 0:
            return 2, (first, second)
    return 1, (first,)


def _maximal_precursor_count(source_rows: list[int], precursor: int) -> int:
    return sum(
        1
        for vertex, upper_vertices in enumerate(source_rows)
        if precursor & (1 << vertex) and not upper_vertices & precursor
    )


def _transition(stage: int, source_rows: list[int], precursor: int) -> Matrix2:
    width = precursor.bit_count()
    maximal_count = _maximal_precursor_count(source_rows, precursor)
    probability = Fraction(2 ** (width - maximal_count), 2**stage)
    upper_right = Fraction(4, 2**stage) if precursor == 0 else Fraction(0)
    return ((probability, upper_right), (Fraction(0), Fraction(1)))


def _q(stage: int) -> Matrix2:
    return _transition(stage, [0] * stage, 0)


def _path_matrix(path: dict[str, Any]) -> Matrix2:
    product = IDENTITY
    for transition in path["transitions"]:
        factor = _transition(
            int(transition["stage"]),
            [int(row) for row in transition["source_relation_rows"]],
            int(transition["precursor_code"]),
        )
        product = _multiply(factor, product)
    return product


def _build_reachable_inventory(operator_gc: dict[str, Any]) -> dict[str, Any]:
    paths = [
        path
        for stage_paths in operator_gc["path_inventory"].values()
        for path in stage_paths
    ]
    path_matrices = {str(path["path_id"]): _path_matrix(path) for path in paths}
    path_states = {
        path_id: _apply(matrix, OMEGA) for path_id, matrix in path_matrices.items()
    }

    endpoints: dict[str, dict[str, Any]] = {}
    for path in paths:
        path_id = str(path["path_id"])
        endpoint_id = str(path["endpoint_causet_id"])
        state = path_states[path_id]
        record = endpoints.setdefault(
            endpoint_id,
            {
                "endpoint_causet_id": endpoint_id,
                "endpoint_stage": int(path["endpoint_stage"]),
                "endpoint_relation_rows": [int(row) for row in path["endpoint_relation_rows"]],
                "state": state,
                "path_ids": [],
                "all_paths_equal": True,
            },
        )
        if record["state"] != state:
            record["all_paths_equal"] = False
        record["path_ids"].append(path_id)

    ordered = sorted(
        endpoints.values(),
        key=lambda item: (item["endpoint_stage"], item["endpoint_causet_id"]),
    )
    endpoint_states = [record["state"] for record in ordered]
    rank, basis_indices = _vector_rank(endpoint_states)
    serialized = [
        {
            "endpoint_causet_id": record["endpoint_causet_id"],
            "endpoint_stage": record["endpoint_stage"],
            "endpoint_relation_rows": record["endpoint_relation_rows"],
            "state": _vector_record(record["state"]),
            "path_count": len(record["path_ids"]),
            "anchor_path_id": record["path_ids"][0],
            "all_paths_equal": record["all_paths_equal"],
            "is_antichain": not any(record["endpoint_relation_rows"]),
        }
        for record in ordered
    ]
    return {
        "paths": paths,
        "path_matrices": path_matrices,
        "path_states": path_states,
        "endpoint_records_internal": ordered,
        "summary": {
            "path_count": len(paths),
            "endpoint_count": len(ordered),
            "stage_counts": {
                str(stage): sum(record["endpoint_stage"] == stage for record in ordered)
                for stage in range(1, 6)
            },
            "all_same_endpoint_paths_give_same_state": all(
                record["all_paths_equal"] for record in ordered
            ),
            "all_states_nonzero": all(state != ZERO_VECTOR for state in endpoint_states),
            "reachable_span_rank": rank,
            "rank_basis_endpoint_ids": [
                ordered[index]["endpoint_causet_id"] for index in basis_indices
            ],
            "unique_state_vectors": sorted(
                {
                    f"{_vector_record(state)[0]},{_vector_record(state)[1]}"
                    for state in endpoint_states
                }
            ),
        },
        "endpoints": serialized,
    }


def _gc_visibility(
    operator_gc: dict[str, Any],
    path_matrices: dict[str, Matrix2],
) -> dict[str, Any]:
    operator_nonzero = 0
    state_nonzero = 0
    first_operator_nonzero: dict[str, Any] | None = None
    for relation in operator_gc["all_pair_derivations"]:
        residual = _subtract(
            path_matrices[str(relation["left_path_id"])],
            path_matrices[str(relation["right_path_id"])],
        )
        action = _apply(residual, OMEGA)
        if residual != ZERO_MATRIX:
            operator_nonzero += 1
            if first_operator_nonzero is None:
                first_operator_nonzero = {
                    "endpoint_causet_id": relation["endpoint_causet_id"],
                    "left_path_id": relation["left_path_id"],
                    "right_path_id": relation["right_path_id"],
                    "operator_residual": _matrix_record(residual),
                    "action_on_Omega": _vector_record(action),
                }
        state_nonzero += action != ZERO_VECTOR
    return {
        "checked_path_pairs": len(operator_gc["all_pair_derivations"]),
        "operator_nonzero_residual_count": operator_nonzero,
        "fixed_state_nonzero_action_count": state_nonzero,
        "first_operator_nonzero_residual": first_operator_nonzero,
    }


def _msr_visibility(
    cpobc: dict[str, Any],
    assignments: dict[str, Matrix2],
    endpoint_states: dict[str, Vector2],
) -> dict[str, Any]:
    operator_nonzero = 0
    state_nonzero = 0
    records = []
    for constraint in cpobc["MSR_operator_constraints"]:
        residual = _scale(int(constraint["identity_coefficient"]), IDENTITY)
        for term in constraint["terms"]:
            residual = _add(
                residual,
                _scale(int(term["coefficient"]), assignments[str(term["transition_id"])]),
            )
        source_id = str(constraint["source_id"])
        state = endpoint_states[source_id]
        action = _apply(residual, state)
        operator_nonzero += residual != ZERO_MATRIX
        state_nonzero += action != ZERO_VECTOR
        records.append(
            {
                "constraint_id": constraint["constraint_id"],
                "source_id": source_id,
                "source_state": _vector_record(state),
                "operator_residual": _matrix_record(residual),
                "action_on_source_state": _vector_record(action),
                "operator_nonzero": residual != ZERO_MATRIX,
                "state_action_nonzero": action != ZERO_VECTOR,
            }
        )
    return {
        "checked_source_residuals": len(records),
        "operator_nonzero_residual_count": operator_nonzero,
        "source_state_nonzero_action_count": state_nonzero,
        "records": records,
    }


def _domain_action_record(
    commutator: Matrix2,
    domain: list[dict[str, Any]],
) -> dict[str, Any]:
    detected = [
        record for record in domain if _apply(commutator, record["state"]) != ZERO_VECTOR
    ]
    return {
        "tested_endpoint_count": len(domain),
        "nonzero_action_count": len(detected),
        "first_detecting_endpoint_id": None if not detected else detected[0]["endpoint_causet_id"],
    }


def _commutator_visibility(endpoint_records: list[dict[str, Any]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        commutator = _commutator(_q(left_stage), _q(right_stage))
        all_states = endpoint_records
        antichain_states = [
            record for record in all_states if not any(record["endpoint_relation_rows"])
        ]
        prefix_states = [
            record
            for record in all_states
            if record["endpoint_stage"] <= min(left_stage, right_stage)
        ]

        records.append(
            {
                "pair": [left_stage, right_stage],
                "commutator": _matrix_record(commutator),
                "operator_nonzero": commutator != ZERO_MATRIX,
                "domains": {
                    "ALL_COMPILED_CYLINDER_STATES_IN_COMMON_H": _domain_action_record(
                        commutator, all_states
                    ),
                    "ANTICHAIN_CYLINDER_STATES": _domain_action_record(
                        commutator, antichain_states
                    ),
                    "PRE_BOTH_STAGE_PREFIX_DIAGNOSTIC": _domain_action_record(
                        commutator, prefix_states
                    ),
                },
                "annihilates_full_reachable_span": all(
                    _apply(commutator, record["state"]) == ZERO_VECTOR
                    for record in all_states
                ),
            }
        )
    return {
        "records": records,
        "all_six_operator_commutators_nonzero": all(
            record["operator_nonzero"] for record in records
        ),
        "reachable_visible_on_any_compiled_cylinder_state": any(
            record["domains"]["ALL_COMPILED_CYLINDER_STATES_IN_COMMON_H"][
                "nonzero_action_count"
            ]
            for record in records
        ),
        "all_six_annihilate_full_reachable_span": all(
            record["annihilates_full_reachable_span"] for record in records
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_paths = {
        relative: root / relative
        for relative in (WEAK_RESULT_PATH, OPERATOR_GC_PATH, CPOBC_PATH)
    }
    weak = _load(input_paths[WEAK_RESULT_PATH])
    operator_gc = _load(input_paths[OPERATOR_GC_PATH])
    cpobc = _load(input_paths[CPOBC_PATH])
    if weak.get("verdict") != "WEAK_D2_NONCOMMUTATIVE_WITNESS_CERTIFIED" or not weak.get(
        "passed"
    ):
        raise AssertionError("the frozen v0.4 witness gate failed")

    reachable = _build_reachable_inventory(operator_gc)
    endpoint_records = reachable.pop("endpoint_records_internal")
    path_matrices = reachable.pop("path_matrices")
    reachable.pop("paths")
    reachable.pop("path_states")
    endpoint_states = {
        str(record["endpoint_causet_id"]): record["state"] for record in endpoint_records
    }

    assignments = {
        str(record["occurrence_id"]): _matrix_from_record(record["matrix"])
        for record in weak["transition_assignment"]["records"]
    }
    rebuilt_q = [_q(stage) for stage in range(1, 6)]
    frozen_q = [_matrix_from_record(record["matrix"]) for record in weak["Q_inventory"]]
    q_formula_matches = rebuilt_q == frozen_q
    if not q_formula_matches:
        raise AssertionError("the independent Q reconstruction differs from the frozen witness")

    gc = _gc_visibility(operator_gc, path_matrices)
    msr = _msr_visibility(cpobc, assignments, endpoint_states)
    commutators = _commutator_visibility(endpoint_records)
    summary = reachable["summary"]

    gates = {
        "frozen_weak_witness_valid": True,
        "independent_Q_formula_matches_frozen_inventory": q_formula_matches,
        "all_407_paths_reconstructed": summary["path_count"] == 407,
        "all_87_endpoint_states_reconstructed": summary["endpoint_count"] == 87,
        "fixed_vector_GC_holds_on_all_1529_pairs": (
            gc["checked_path_pairs"] == 1529 and gc["fixed_state_nonzero_action_count"] == 0
        ),
        "reachable_state_MSR_holds_at_all_24_sources": (
            msr["checked_source_residuals"] == 24
            and msr["source_state_nonzero_action_count"] == 0
        ),
        "reachable_span_rank_is_exactly_one": summary["reachable_span_rank"] == 1,
        "all_six_Q_commutators_are_operator_nonzero": commutators[
            "all_six_operator_commutators_nonzero"
        ],
        "no_Q_commutator_is_detected_on_any_compiled_cylinder_state": not commutators[
            "reachable_visible_on_any_compiled_cylinder_state"
        ],
    }
    if not all(gates.values()):
        raise AssertionError(f"SR2-V baseline observability gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-01",
        "field": "Q",
        "dimension": 2,
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: _sha256(path) for relative, path in sorted(input_paths.items())
        },
        "independence": {
            "imports_weak_d2_v04": False,
            "arithmetic": "fractions.Fraction only; no float or finite field",
            "transition_formula_reconstructed_from_source_metadata": True,
            "path_products_reconstructed_from_all_407_path_records": True,
        },
        "visibility_definition": {
            "primary_domain": "ALL_COMPILED_CYLINDER_STATES_IN_COMMON_H",
            "meaning": (
                "A commutator is reachable-visible when it acts nontrivially on at least one "
                "genuine compiled cylinder state in the common representation space."
            ),
            "chronology_nonclaim": (
                "This is operator action on a physical state, not a claim that mixed-stage "
                "Q_i Q_j is itself a legal chronological growth word."
            ),
            "metadata_preserved": [
                "endpoint_causet_id",
                "endpoint_stage",
                "endpoint_relation_rows",
            ],
            "secondary_domains": [
                "ANTICHAIN_CYLINDER_STATES",
                "PRE_BOTH_STAGE_PREFIX_DIAGNOSTIC",
            ],
        },
        "reachable_inventory": reachable,
        "residual_visibility": {
            "fixed_vector_GC": gc,
            "reachable_state_MSR": msr,
        },
        "commutator_visibility": commutators,
        "baseline_classification": {
            "operator_noncommutative": True,
            "reachable_span_rank": summary["reachable_span_rank"],
            "reachable_visible": commutators[
                "reachable_visible_on_any_compiled_cylinder_state"
            ],
            "label": "EXACT_OFF_REACHABLE_SECTOR_NONCOMMUTATIVITY",
        },
        "search_terminal": SEARCH_TERMINAL,
        "search_terminal_reason": (
            "This audits one frozen witness only; it neither constructs nor obstructs a "
            "rank-two reachable-visible witness in the full weak/weak profile."
        ),
        "gates": gates,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "The frozen SR2 witness has exact reachable rank one and all six nonzero Q "
            "commutators annihilate every compiled cylinder state. This does not imply that "
            "all weak/weak CPOBC representations share that property."
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
