"""Independent exact witness oracle for the v0.3.5 literal d=2 branch.

This script deliberately does not import the production Sage backend.  It
reads the frozen reduced operator system and evaluates every matrix relation
over exact SymPy rationals at one explicit S1 pivot-R5 assignment.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

LITERAL_BRANCH = "LITERAL_PRINTED_QN_PLUS_1_BRANCH"
CHART_SHAPES = ("BOTH_NONZERO", "UPPER_ONLY", "LOWER_ONLY")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def _matrix_record(matrix: sp.Matrix) -> list[list[str]]:
    return [
        [str(sp.cancel(matrix[row, column])) for column in range(2)]
        for row in range(2)
    ]


def verify(
    repo_root: Path,
    *,
    shape: str = "BOTH_NONZERO",
) -> dict[str, Any]:
    if shape not in CHART_SHAPES:
        raise ValueError(f"unsupported chart shape: {shape}")
    system_path = (
        repo_root
        / "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
    )
    system = json.loads(system_path.read_text(encoding="utf-8"))
    system_sha256 = hashlib.sha256(system_path.read_bytes()).hexdigest()
    polynomial_system_path = (
        repo_root / "results/v0.3.4_polynomial_systems.json"
    )
    polynomial_system_sha256 = hashlib.sha256(
        polynomial_system_path.read_bytes()
    ).hexdigest()
    polynomial_system = json.loads(
        polynomial_system_path.read_text(encoding="utf-8")
    )
    compact_arena_path = (
        repo_root
        / "certificates/d2_saturation/"
        "v0.3.5_compact_expression_arena.json.gz"
    )
    compact_arena_sha256 = hashlib.sha256(
        compact_arena_path.read_bytes()
    ).hexdigest()
    with gzip.open(compact_arena_path, "rt", encoding="utf-8") as stream:
        compact_arena = json.load(stream)
    values = {
        "a": sp.Integer(1 if shape == "BOTH_NONZERO" else 2),
        "b": sp.Integer(0 if shape == "LOWER_ONLY" else 1),
        "c": sp.Integer(0 if shape == "UPPER_ONLY" else 1),
        "d": sp.Integer(2 if shape == "BOTH_NONZERO" else 3),
        "r2m": sp.Integer(2),
        "r3m": sp.Integer(3),
        "r4m": sp.Integer(4),
        "r5m": sp.Integer(5),
        "r5p": sp.Integer(6),
    }
    q1 = sp.Matrix(
        [
            [values["a"], values["b"]],
            [values["c"], values["d"]],
        ]
    )
    q_matrices = {
        "Q_1": q1,
        "Q_2": values["r2m"] * q1,
        "Q_3": values["r3m"] * q1,
        "Q_4": values["r4m"] * q1,
        "Q_5": sp.Matrix(
            [
                [
                    values["a"] * values["r5p"],
                    values["b"] * values["r5m"],
                ],
                [
                    values["c"] * values["r5p"],
                    values["d"] * values["r5m"],
                ],
            ]
        ),
    }
    identity = sp.eye(2)
    definitions = {
        record["node_id"]: record
        for record in system["dependency_nodes"]
    }
    cache: dict[str, sp.Matrix] = dict(q_matrices)
    visiting: set[str] = set()

    def product(word: list[str]) -> sp.Matrix:
        result = identity
        for item in word:
            result = result * node(item)
        return result.applyfunc(sp.cancel)

    def linear_expression(terms: list[dict[str, Any]]) -> sp.Matrix:
        result = sp.zeros(2)
        for term in terms:
            result += sp.Integer(term["coefficient"]) * product(term["word"])
        return result.applyfunc(sp.cancel)

    def node(node_id: str) -> sp.Matrix:
        if node_id in cache:
            return cache[node_id]
        if node_id in visiting:
            raise RuntimeError(f"dependency cycle at {node_id}")
        visiting.add(node_id)
        definition = definitions[node_id]
        kind = definition["kind"]
        if kind == "Q_GENERATOR":
            result = q_matrices[node_id]
        elif kind == "Q_GENERATOR_INVERSE":
            result = q_matrices[node_id.removesuffix("^-1")].inv()
        elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
            result = sp.zeros(2)
            for term in definition["terms"]:
                result += sp.Integer(term["coefficient"]) * product(
                    term["word_nodes"]
                )
        elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            result = node(definition["inverse_of_node"]).inv()
        elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
            result = product(definition["ordered_word"])
        else:
            raise ValueError(f"unsupported dependency kind: {kind}")
        visiting.remove(node_id)
        cache[node_id] = result.applyfunc(sp.cancel)
        return cache[node_id]

    relation_residuals: list[dict[str, Any]] = []
    failed_relations: list[str] = []
    for relation in system["relations"][LITERAL_BRANCH]:
        if relation["family"] == "EQ112_PATH_CONSISTENCY":
            residual = product(relation["lhs_word"]) - product(
                relation["rhs_word"]
            )
        else:
            residual = linear_expression(relation["expression"])
        residual = residual.applyfunc(sp.cancel)
        zero = residual == sp.zeros(2)
        if not zero:
            failed_relations.append(relation["relation_id"])
        relation_residuals.append(
            {
                "relation_id": relation["relation_id"],
                "residual": _matrix_record(residual),
                "zero": zero,
            }
        )

    scalar_symbols: dict[str, int] = {}
    for q_name, matrix in q_matrices.items():
        q_index = q_name.removeprefix("Q_")
        for row in range(2):
            for column in range(2):
                scalar_symbols[
                    f"q{q_index}_{row + 1}{column + 1}"
                ] = int(matrix[row, column])
    arena_values: list[int] = []
    for operation, operand in compact_arena["nodes"]:
        if operation == 0:
            value = int(operand)
        elif operation == 1:
            value = scalar_symbols[operand]
        elif operation == 2:
            value = sum(arena_values[index] for index in operand)
        elif operation == 3:
            value = 1
            for index in operand:
                value *= arena_values[index]
        else:
            raise ValueError(f"unsupported compact operation: {operation}")
        arena_values.append(value)
    target_indices = compact_arena["target_indices"]
    scalar_equations = polynomial_system["systems"][LITERAL_BRANCH][
        "equations"
    ]
    scalar_residuals = [
        {
            "equation_id": equation["equation_id"],
            "residual": arena_values[
                target_indices[equation["canonical_expression_id"]]
            ],
        }
        for equation in scalar_equations
    ]
    failed_scalar_equations = [
        record["equation_id"]
        for record in scalar_residuals
        if record["residual"] != 0
    ]

    transition_records: list[dict[str, Any]] = []
    singular_transitions: list[str] = []
    for transition in system["reconstructed_transition_predicates"]:
        matrix = linear_expression(transition["reconstructed_expression"])
        determinant = sp.cancel(matrix.det())
        if determinant == 0:
            singular_transitions.append(transition["occurrence_id"])
        transition_records.append(
            {
                "occurrence_id": transition["occurrence_id"],
                "determinant": str(determinant),
                "nonsingular": determinant != 0,
            }
        )

    inverse_records: list[dict[str, Any]] = []
    failed_inverse_sites: list[str] = []
    inverse_nodes = {
        definition["inverse_of_node"]: definition["node_id"]
        for definition in system["dependency_nodes"]
        if definition["kind"] == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
    }
    for predicate in system["explicit_two_sided_inverse_predicates"]:
        base_id = predicate["inverse_of_node"]
        inverse_id = inverse_nodes.get(base_id, predicate["generator"])
        left = (node(inverse_id) * node(base_id)).applyfunc(sp.cancel)
        right = (node(base_id) * node(inverse_id)).applyfunc(sp.cancel)
        passed = left == identity and right == identity
        if not passed:
            failed_inverse_sites.append(base_id)
        inverse_records.append(
            {
                "inverse_of_node": base_id,
                "inverse_node": inverse_id,
                "left_identity": left == identity,
                "right_identity": right == identity,
            }
        )

    q_determinants = {
        name: str(sp.cancel(matrix.det()))
        for name, matrix in q_matrices.items()
    }
    chart_nonzero_values = {
        "det(Q_1)": q_matrices["Q_1"].det(),
        "r2m^2": values["r2m"] ** 2,
        "r3m^2": values["r3m"] ** 2,
        "r4m^2": values["r4m"] ** 2,
        "r5m*r5p": values["r5m"] * values["r5p"],
        "r5p-r5m": values["r5p"] - values["r5m"],
    }
    if shape in {"BOTH_NONZERO", "UPPER_ONLY"}:
        chart_nonzero_values["b"] = values["b"]
    if shape in {"BOTH_NONZERO", "LOWER_ONLY"}:
        chart_nonzero_values["c"] = values["c"]
    chart_zero_values = {}
    if shape == "UPPER_ONLY":
        chart_zero_values["c"] = values["c"]
    elif shape == "LOWER_ONLY":
        chart_zero_values["b"] = values["b"]
    chart_conditions_passed = all(
        value != 0 for value in chart_nonzero_values.values()
    ) and all(value == 0 for value in chart_zero_values.values())
    commutator = (
        q_matrices["Q_1"] * q_matrices["Q_5"]
        - q_matrices["Q_5"] * q_matrices["Q_1"]
    ).applyfunc(sp.cancel)
    q1_trace = sp.cancel(q_matrices["Q_1"].trace())
    outside_pauli_proportional_ansatz = q1_trace != 0
    passed = (
        system.get("passed") is True
        and len(relation_residuals) == 1001
        and len(scalar_residuals) == 2564
        and len(transition_records) == 165
        and len(inverse_records) == 26
        and compact_arena["source_artifact_sha256"]
        == polynomial_system_sha256
        and not failed_relations
        and not failed_scalar_equations
        and not singular_transitions
        and not failed_inverse_sites
        and all(sp.sympify(value) != 0 for value in q_determinants.values())
        and chart_conditions_passed
        and commutator != sp.zeros(2)
        and outside_pauli_proportional_ansatz
    )
    result: dict[str, Any] = {
        "schema_version": (
            "final-theory-d2-explicit-rational-witness-v0.3.5"
        ),
        "oracle_backend": f"SymPy {sp.__version__} exact rationals",
        "source_artifacts": {
            str(system_path.relative_to(repo_root)).replace(
                "\\", "/"
            ): system_sha256,
            str(polynomial_system_path.relative_to(repo_root)).replace(
                "\\", "/"
            ): polynomial_system_sha256,
            str(compact_arena_path.relative_to(repo_root)).replace(
                "\\", "/"
            ): compact_arena_sha256,
        },
        "source_semantic_digest_sha256": system[
            "semantic_digest_sha256"
        ],
        "source_index_branch": LITERAL_BRANCH,
        "chart": f"{LITERAL_BRANCH}:S1_PIVOT_R5:{shape}",
        "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
        "dimension": 2,
        "finite_scope": "n<=4",
        "coefficient_field": "QQ",
        "witness_parameters": {
            name: str(value) for name, value in values.items()
        },
        "Q_matrices": {
            name: _matrix_record(matrix)
            for name, matrix in q_matrices.items()
        },
        "Q_determinants": q_determinants,
        "chart_localisation_check": {
            "chart_nonzero_values": {
                name: str(value)
                for name, value in chart_nonzero_values.items()
            },
            "chart_zero_values": {
                name: str(value)
                for name, value in chart_zero_values.items()
            },
            "all_conditions_passed": chart_conditions_passed,
        },
        "nonzero_commutator": {
            "pair": ["Q_1", "Q_5"],
            "matrix": _matrix_record(commutator),
            "nonzero": commutator != sp.zeros(2),
        },
        "relation_check": {
            "count": len(relation_residuals),
            "failed_relation_ids": failed_relations,
            "all_zero": not failed_relations,
            "residuals_sha256": _stable_hash(relation_residuals),
        },
        "canonical_scalar_numerator_check": {
            "count": len(scalar_residuals),
            "failed_equation_ids": failed_scalar_equations,
            "all_zero": not failed_scalar_equations,
            "residuals_sha256": _stable_hash(scalar_residuals),
            "compact_arena_source_hash_matches": (
                compact_arena["source_artifact_sha256"]
                == polynomial_system_sha256
            ),
        },
        "transition_check": {
            "count": len(transition_records),
            "singular_occurrence_ids": singular_transitions,
            "all_nonsingular": not singular_transitions,
            "records": transition_records,
        },
        "two_sided_inverse_check": {
            "count": len(inverse_records),
            "failed_inverse_sites": failed_inverse_sites,
            "all_passed": not failed_inverse_sites,
            "records": inverse_records,
        },
        "pauli_proportional_ansatz_audit": {
            "Q_1_trace": str(q1_trace),
            "paper_ansatz_Q_matrices_are_traceless": True,
            "outside_paper_ansatz": outside_pauli_proportional_ansatz,
            "reason": (
                "Every scalar multiple of a Pauli matrix is traceless, "
                f"whereas this witness has tr(Q_1)={q1_trace}. "
                "Trace is preserved "
                "by simultaneous similarity."
            ),
        },
        "not_pauli_ansatz": outside_pauli_proportional_ansatz,
        "similarity_audit": {
            "single_orbit_representative": True,
            "nonzero_commutator_is_similarity_invariant": True,
            "not_a_commutative_similarity_duplicate": (
                commutator != sp.zeros(2)
            ),
            "reason": (
                "A simultaneous similarity conjugates each commutator. "
                "Therefore a nonzero [Q_1,Q_5] cannot be similar to any "
                "commutative representation."
            ),
        },
        "exact_numeric_distinction": "EXACT_RATIONAL_WITNESS",
        "completeness_scope": (
            "all 1001 literal-branch matrix relations, all 2564 canonical "
            "scalar numerator equations, all 165 reconstructed transition "
            "determinants, all 26 formal two-sided inverses, and an explicit "
            "nonzero commutator"
        ),
        "unresolved_components": [],
        "passed": passed,
        "verdict": (
            "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
            if passed
            else "CPOBC_D2_PARTIAL"
        ),
    }
    result["semantic_digest_sha256"] = _stable_hash(
        {
            "parameters": result["witness_parameters"],
            "relations": result["relation_check"],
            "scalar_numerators": result[
                "canonical_scalar_numerator_check"
            ],
            "transitions": result["transition_check"],
            "inverse": result["two_sided_inverse_check"],
            "chart_localisation": result["chart_localisation_check"],
            "commutator": result["nonzero_commutator"],
            "pauli_audit": result["pauli_proportional_ansatz_audit"],
            "similarity_audit": result["similarity_audit"],
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--shape",
        choices=CHART_SHAPES,
        default="BOTH_NONZERO",
    )
    arguments = parser.parse_args()
    result = verify(arguments.repo_root.resolve(), shape=arguments.shape)
    output = arguments.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
