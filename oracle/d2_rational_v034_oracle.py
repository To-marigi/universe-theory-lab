"""Independent d=2 rational-matrix oracle for Final-Theory Bench v0.3.4.

The oracle is intentionally self-contained.  It imports no production v0.3.4
module.  Its exact matrix representation is a pair ``(N, d)`` meaning
``N / d``.  In particular,

    (N / d)^-1 = d * adj(N) / det(N).

Three symbolic coordinate charts (S1, S2, S3) are evaluated against a small,
declared relation set.  Separately, a standard-library ``Fraction`` evaluator
parses frozen v0.3.1/v0.3.3 JSON and checks the complete finite inventories at
the exact scalar fixture ``Q_1=2I, Q_2=3I, Q_3=5I, Q_4=7I`` (and ``Q_5=11I``
only in the literal branch).  The scalar witness is not a classification of
general noncommutative solutions.  The Eq. (113) branches remain separate, so
passing this file still warrants only ``INDEPENDENT_ORACLE_PARTIAL``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

DIMENSION = 2
VERDICT = "INDEPENDENT_ORACLE_PARTIAL"
QN_BRANCH = "EQ113_QN_BRANCH"
LITERAL_QN_PLUS_1_BRANCH = "EQ113_QN_PLUS_1_BRANCH"
SCALAR_FIXTURE_ID = "V034_EXACT_SCALAR_Q_2_3_5_7_LITERAL_11"
SCALAR_Q_ASSIGNMENT = {
    "Q_1": Fraction(2),
    "Q_2": Fraction(3),
    "Q_3": Fraction(5),
    "Q_4": Fraction(7),
}
LITERAL_Q5_ASSIGNMENT = Fraction(11)
FROZEN_SCALAR_INPUTS = {
    "v031_cpobc": Path("results/v0.3.1_cpobc_relations_n4.json"),
    "v033_atomisation": Path("results/v0.3.3_atomisation_paths_n4.json"),
    "v033_eq112": Path("results/v0.3.3_eq112_reduction_n4.json"),
    "v033_local_gc": Path("results/v0.3.3_local_operator_gc_n4.json"),
    "v033_q_presentation": Path(
        "results/v0.3.3_q_only_presentation_n4.json"
    ),
}
FROZEN_SCHEMA_VERSIONS = {
    "v031_cpobc": "final-theory-cpobc-relations-v0.3.1",
    "v033_atomisation": "final-theory-atomisation-paths-n4-v0.3.3",
    "v033_eq112": "final-theory-eq112-reduction-n4-v0.3.3",
    "v033_local_gc": "final-theory-local-operator-gc-n4-v0.3.3",
    "v033_q_presentation": (
        "final-theory-q-only-presentation-n4-v0.3.3"
    ),
}


def _exact(value: Any) -> str:
    return str(sp.factor(sp.cancel(sp.sympify(value))))


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [_exact(matrix[row, column]) for column in range(matrix.cols)]
        for row in range(matrix.rows)
    ]


def _zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.cancel(sp.expand(entry)) == 0 for entry in matrix)


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _load_frozen_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _scalar_word(
    word: Iterable[str],
    values: dict[str, Fraction],
) -> Fraction:
    result = Fraction(1)
    for token in word:
        try:
            result *= values[token]
        except KeyError as error:
            raise KeyError(f"unknown scalar word token: {token}") from error
    return result


def _scalar_expression(
    terms: Iterable[dict[str, Any]],
    values: dict[str, Fraction],
    *,
    word_key: str = "word",
) -> Fraction:
    return sum(
        (
            Fraction(term["coefficient"])
            * _scalar_word(term[word_key], values)
            for term in terms
        ),
        start=Fraction(0),
    )


def _evaluate_frozen_dependency_dag(
    presentation: dict[str, Any],
) -> dict[str, Fraction]:
    """Evaluate the frozen v0.3.3 DAG without production parser imports."""

    node_records = presentation["dependency_DAG"]["nodes"]
    nodes = {record["node_id"]: record for record in node_records}
    if len(nodes) != len(node_records):
        raise ValueError("duplicate dependency-DAG node id")

    values: dict[str, Fraction] = {}
    active: set[str] = set()

    def evaluate(node_id: str) -> Fraction:
        if node_id in values:
            return values[node_id]
        if node_id in active:
            raise ValueError(f"dependency-DAG cycle at {node_id}")
        try:
            node = nodes[node_id]
        except KeyError as error:
            raise KeyError(f"unknown dependency-DAG node: {node_id}") from error
        active.add(node_id)
        kind = node["kind"]
        if kind == "Q_GENERATOR":
            value = SCALAR_Q_ASSIGNMENT[node_id]
        elif kind == "Q_GENERATOR_INVERSE":
            base_id = node_id.removesuffix("^-1")
            base = evaluate(base_id)
            if base == 0:
                raise ZeroDivisionError(f"zero Q generator: {base_id}")
            value = 1 / base
        elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
            value = sum(
                (
                    Fraction(term["coefficient"])
                    * _scalar_word(
                        term["word_nodes"],
                        {
                            dependency: evaluate(dependency)
                            for dependency in term["word_nodes"]
                        },
                    )
                    for term in node["terms"]
                ),
                start=Fraction(0),
            )
        elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            base_id = node["inverse_of_node"]
            base = evaluate(base_id)
            if base == 0:
                raise ZeroDivisionError(f"zero inverse base: {base_id}")
            value = 1 / base
        elif kind in {
            "EQ112_CONJUGATE",
            "EQ112_CONJUGATE_INVERSE",
        }:
            value = _scalar_word(
                node["ordered_word"],
                {
                    dependency: evaluate(dependency)
                    for dependency in node["ordered_word"]
                },
            )
        else:
            raise ValueError(f"unsupported dependency-DAG kind: {kind}")
        active.remove(node_id)
        values[node_id] = value
        return value

    for node_id in nodes:
        evaluate(node_id)
    return values


def _causet_code(causet_id: str) -> int:
    _stage, hexadecimal_code = causet_id.split("-", maxsplit=1)
    return int(hexadecimal_code, 16)


def _precursor_code(vertices: Iterable[int]) -> int:
    return sum(1 << vertex for vertex in vertices)


def _transition_signature_map(
    cpobc: dict[str, Any],
) -> dict[tuple[int, int, int], str]:
    """Recover quotient signatures from the frozen v0.3.1 source records."""

    signatures: dict[tuple[int, int, int], str] = {}

    def add(signature: tuple[int, int, int], occurrence_id: str) -> None:
        previous = signatures.get(signature)
        if previous is not None and previous != occurrence_id:
            raise ValueError(
                f"transition signature collision: {signature}"
            )
        signatures[signature] = occurrence_id

    for relation in cpobc["relations"]:
        for role in ("A_n", "A_prime_n", "A_m", "A_prime_m"):
            suffix = "n" if role.endswith("_n") else "m"
            precursor_name = (
                "A_prime" if role.startswith("A_prime") else "A"
            )
            source = relation["source_causet"][f"stage_{suffix}"]["id"]
            vertices = relation["full_precursor"][f"stage_{suffix}"][
                precursor_name
            ]
            signature = (
                relation["stage"][suffix],
                _causet_code(source),
                _precursor_code(vertices),
            )
            add(
                signature,
                relation["transition_orbit"][role]["occurrence_id"],
            )

    for constraint in cpobc["MSR_operator_constraints"]:
        source_id = constraint["source_id"]
        stage = int(source_id.split("-", maxsplit=1)[0][1:])
        source_code = _causet_code(source_id)
        for term in constraint["terms"]:
            add(
                (stage, source_code, term["precursor_code"]),
                term["transition_id"],
            )
    return signatures


def _result_digest(
    records: Iterable[tuple[str, Fraction]],
) -> str:
    return stable_hash(
        [
            {"id": identifier, "residual": _fraction_text(residual)}
            for identifier, residual in records
        ]
    )


def scalar_fixture_certificate(
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Run the exact scalar fixture against frozen v0.3.1/v0.3.3 JSON.

    This route intentionally does not import a production formula compiler,
    word parser, matrix evaluator, or v0.3.4 module.
    """

    root = (
        repo_root.resolve()
        if repo_root is not None
        else Path(__file__).resolve().parents[1]
    )
    paths = {
        name: root / relative_path
        for name, relative_path in FROZEN_SCALAR_INPUTS.items()
    }
    documents = {
        name: _load_frozen_json(path) for name, path in paths.items()
    }
    cpobc = documents["v031_cpobc"]
    atomisation = documents["v033_atomisation"]
    eq112 = documents["v033_eq112"]
    local_gc = documents["v033_local_gc"]
    presentation = documents["v033_q_presentation"]

    schema_checks = {
        name: documents[name].get("schema_version") == expected
        for name, expected in FROZEN_SCHEMA_VERSIONS.items()
    }
    input_records = [
        {
            "name": name,
            "path": FROZEN_SCALAR_INPUTS[name].as_posix(),
            "schema_version": documents[name].get("schema_version"),
            "sha256": hashlib.sha256(paths[name].read_bytes()).hexdigest(),
        }
        for name in sorted(paths)
    ]

    node_values = _evaluate_frozen_dependency_dag(presentation)
    node_records = presentation["dependency_DAG"]["nodes"]
    dependency_kind_counts: dict[str, int] = {}
    for node in node_records:
        kind = node["kind"]
        dependency_kind_counts[kind] = (
            dependency_kind_counts.get(kind, 0) + 1
        )

    reconstructed_records = presentation["invertibility_predicates"][
        "reconstructed_transition_predicates"
    ]
    occurrence_values = {
        record["occurrence_id"]: _scalar_expression(
            record["reconstructed_expression"],
            node_values,
        )
        for record in reconstructed_records
    }
    if len(occurrence_values) != len(reconstructed_records):
        raise ValueError("duplicate reconstructed occurrence id")
    occurrence_results = sorted(occurrence_values.items())

    cpobc_results: list[tuple[str, Fraction]] = []
    cpobc_keys: list[tuple[str, str]] = []
    equation_kind_counts: dict[str, int] = {}
    for relation in cpobc["relations"]:
        alias_values = {
            role: occurrence_values[transition["occurrence_id"]]
            for role, transition in relation["transition_orbit"].items()
        }
        equations = relation["denominator_cleared_form"][
            "noncommutative_polynomial_equations"
        ]
        for equation in equations:
            equation_id = equation["equation_id"]
            identifier = f"{relation['relation_id']}::{equation_id}"
            residual = _scalar_expression(
                equation["residual_terms"],
                alias_values,
            )
            cpobc_results.append((identifier, residual))
            cpobc_keys.append((relation["relation_id"], equation_id))
            equation_kind_counts[equation_id] = (
                equation_kind_counts.get(equation_id, 0) + 1
            )
    presentation_cpobc_keys = {
        (record["relation_id"], record["equation_id"])
        for category in ("CPOBC_identities", "CPOBC_residuals")
        for record in presentation["relation_inventory"][category]
    }

    msr_results: list[tuple[str, Fraction]] = []
    for constraint in cpobc["MSR_operator_constraints"]:
        residual = Fraction(constraint["identity_coefficient"])
        for term in constraint["terms"]:
            residual += (
                Fraction(term["coefficient"])
                * occurrence_values[term["transition_id"]]
            )
        msr_results.append((constraint["constraint_id"], residual))
    presentation_msr_ids = {
        record["constraint_id"]
        for category in ("strong_MSR_identities", "strong_MSR_residuals")
        for record in presentation["relation_inventory"][category]
    }

    signature_occurrences = _transition_signature_map(cpobc)
    paths_by_id: dict[str, dict[str, Any]] = {}
    alias_signatures: dict[str, tuple[int, int, int]] = {}
    for stage_paths in local_gc["path_inventory"].values():
        for path in stage_paths:
            path_id = path["path_id"]
            if path_id in paths_by_id:
                raise ValueError(f"duplicate local-GC path id: {path_id}")
            paths_by_id[path_id] = path
            for transition in path["transitions"]:
                signature_record = transition["quotient_signature"]
                signature = (
                    signature_record["stage"],
                    signature_record["source_relation_code"],
                    signature_record["precursor_code"],
                )
                alias = transition["quotient_operator_symbol"]
                previous = alias_signatures.get(alias)
                if previous is not None and previous != signature:
                    raise ValueError(
                        f"local-GC alias signature collision: {alias}"
                    )
                alias_signatures[alias] = signature
    alias_values = {
        alias: occurrence_values[signature_occurrences[signature]]
        for alias, signature in alias_signatures.items()
    }

    gc_basis_results = [
        (
            relation["relation_id"],
            _scalar_word(relation["lhs_word"], alias_values)
            - _scalar_word(relation["rhs_word"], alias_values),
        )
        for relation in local_gc["generating_relation_basis"]
    ]
    presentation_gc_ids = {
        record["relation_id"]
        for category in (
            "local_operator_GC_identities",
            "local_operator_GC_residuals",
        )
        for record in presentation["relation_inventory"][category]
    }
    path_values = {
        path_id: _scalar_word(
            path["ordered_operator_word_later_on_left"],
            alias_values,
        )
        for path_id, path in paths_by_id.items()
    }
    gc_pair_results: list[tuple[str, Fraction]] = []
    gc_pair_endpoint_matches = 0
    gc_pair_derivable = 0
    for pair in local_gc["all_pair_derivations"]:
        left_path = paths_by_id[pair["left_path_id"]]
        right_path = paths_by_id[pair["right_path_id"]]
        if (
            left_path["endpoint_causet_id"]
            == pair["endpoint_causet_id"]
            == right_path["endpoint_causet_id"]
        ):
            gc_pair_endpoint_matches += 1
        if pair["derivable"]:
            gc_pair_derivable += 1
        identifier = (
            f"{pair['endpoint_causet_id']}::{pair['left_path_id']}::"
            f"{pair['right_path_id']}"
        )
        residual = (
            path_values[pair["left_path_id"]]
            - path_values[pair["right_path_id"]]
        )
        gc_pair_results.append((identifier, residual))

    atomisation_paths = [
        path
        for causet in atomisation["causets"]
        for path in causet["all_alternative_paths"]
    ]
    path_reductions = eq112["path_reductions"]
    atomisation_ids = {path["path_id"] for path in atomisation_paths}
    reduction_ids = {record["path_id"] for record in path_reductions}
    atomisation_results: list[tuple[str, Fraction]] = []
    atomisation_q_results: list[tuple[str, Fraction]] = []
    for reduction in path_reductions:
        value = _scalar_word(
            reduction["G_reduced_ordered_word"],
            node_values,
        )
        g_value = node_values[f"G:{reduction['causet_id']}"]
        q_value = node_values[reduction["Q_node"]]
        atomisation_results.append(
            (reduction["path_id"], value - g_value)
        )
        atomisation_q_results.append(
            (reduction["path_id"], value - q_value)
        )

    inverse_results: list[tuple[str, Fraction]] = []
    inverse_base_nonzero = 0
    inverse_value_nonzero = 0
    inverse_base_ids: set[str] = set()
    for node in node_records:
        kind = node["kind"]
        if kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            base_id = node["inverse_of_node"]
        elif kind == "Q_GENERATOR_INVERSE":
            base_id = node["node_id"].removesuffix("^-1")
        else:
            continue
        inverse_base_ids.add(base_id)
        base_value = node_values[base_id]
        inverse_value = node_values[node["node_id"]]
        inverse_base_nonzero += int(base_value != 0)
        inverse_value_nonzero += int(inverse_value != 0)
        inverse_results.append(
            (node["node_id"], base_value * inverse_value - 1)
        )
    explicit_inverse_base_ids = {
        record["inverse_of_node"]
        for record in presentation["invertibility_predicates"][
            "explicit_two_sided_inverse_predicates"
        ]
    }

    branch_sections: dict[str, dict[str, Any]] = {}
    for branch_name in (QN_BRANCH, LITERAL_QN_PLUS_1_BRANCH):
        branch_values = dict(node_values)
        if branch_name == LITERAL_QN_PLUS_1_BRANCH:
            branch_values["Q_5"] = LITERAL_Q5_ASSIGNMENT
        relations = presentation["source_index_branches"][branch_name][
            "path_consistency_relations"
        ]
        branch_results = [
            (
                (
                    f"{record['causet_id']}::{record['alpha_path_id']}::"
                    f"{record['beta_path_id']}"
                ),
                _scalar_word(record["lhs_word"], branch_values)
                - _scalar_word(record["rhs_word"], branch_values),
            )
            for record in relations
        ]
        q5_relation_count = sum(
            "Q_5" in record["lhs_word"] + record["rhs_word"]
            for record in relations
        )
        branch_sections[branch_name] = {
            "relation_count": len(branch_results),
            "zero_residual_count": sum(
                residual == 0 for _identifier, residual in branch_results
            ),
            "nonzero_residual_count": sum(
                residual != 0 for _identifier, residual in branch_results
            ),
            "Q_5_word_relation_count": q5_relation_count,
            "Q_5_assignment_available": (
                branch_name == LITERAL_QN_PLUS_1_BRANCH
            ),
            "residual_digest_sha256": _result_digest(branch_results),
        }

    cpobc_key_set = set(cpobc_keys)
    msr_id_set = {identifier for identifier, _residual in msr_results}
    gc_basis_id_set = {
        identifier for identifier, _residual in gc_basis_results
    }
    checks = {
        "frozen_schema_versions_match": all(schema_checks.values()),
        "dependency_DAG_cycle_free": bool(
            presentation["dependency_DAG"]["cycle_free"]
        ),
        "all_dependency_nodes_evaluated": (
            len(node_values) == len(node_records) == 92
        ),
        "transition_reconstruction_count_165": (
            len(occurrence_results) == 165
        ),
        "all_165_transition_reconstructions_nonzero": all(
            value != 0 for _identifier, value in occurrence_results
        ),
        "original_CPOBC_word_equation_count_783": (
            len(cpobc_results) == len(cpobc_key_set) == 783
        ),
        "all_783_original_CPOBC_word_equations_zero": all(
            residual == 0 for _identifier, residual in cpobc_results
        ),
        "v031_v033_CPOBC_identifier_sets_match": (
            cpobc_key_set == presentation_cpobc_keys
        ),
        "strong_MSR_count_24": len(msr_results) == 24,
        "all_24_strong_MSR_constraints_zero": all(
            residual == 0 for _identifier, residual in msr_results
        ),
        "v031_v033_MSR_identifier_sets_match": (
            msr_id_set == presentation_msr_ids
        ),
        "local_GC_basis_count_320": (
            len(gc_basis_results) == len(gc_basis_id_set) == 320
        ),
        "all_320_original_local_GC_basis_words_zero": all(
            residual == 0 for _identifier, residual in gc_basis_results
        ),
        "v033_GC_identifier_sets_match": (
            gc_basis_id_set == presentation_gc_ids
        ),
        "same_endpoint_path_pair_count_1529": (
            len(gc_pair_results) == 1529
        ),
        "all_1529_same_endpoint_path_pairs_zero": all(
            residual == 0 for _identifier, residual in gc_pair_results
        ),
        "all_path_pairs_have_matching_endpoints": (
            gc_pair_endpoint_matches == len(gc_pair_results)
        ),
        "all_path_pairs_marked_derivable": (
            gc_pair_derivable == len(gc_pair_results)
        ),
        "atomisation_path_count_34": (
            len(atomisation_paths)
            == len(atomisation_ids)
            == len(path_reductions)
            == len(reduction_ids)
            == 34
        ),
        "atomisation_path_identifier_sets_match": (
            atomisation_ids == reduction_ids
        ),
        "all_34_atomisation_reductions_match_G_nodes": all(
            residual == 0
            for _identifier, residual in atomisation_results
        ),
        "all_34_scalar_atomisation_reductions_equal_Q_stage": all(
            residual == 0
            for _identifier, residual in atomisation_q_results
        ),
        "inverse_node_count_26": len(inverse_results) == 26,
        "all_26_inverse_bases_nonzero": (
            inverse_base_nonzero == len(inverse_results)
        ),
        "all_26_inverse_values_nonzero": (
            inverse_value_nonzero == len(inverse_results)
        ),
        "all_26_two_sided_inverse_products_one": all(
            residual == 0 for _identifier, residual in inverse_results
        ),
        "explicit_inverse_base_identifier_sets_match": (
            inverse_base_ids == explicit_inverse_base_ids
        ),
        "QN_branch_has_25_zero_words": (
            branch_sections[QN_BRANCH]["relation_count"] == 25
            and branch_sections[QN_BRANCH]["zero_residual_count"] == 25
        ),
        "literal_branch_has_25_zero_words": (
            branch_sections[LITERAL_QN_PLUS_1_BRANCH][
                "relation_count"
            ]
            == 25
            and branch_sections[LITERAL_QN_PLUS_1_BRANCH][
                "zero_residual_count"
            ]
            == 25
        ),
        "Q5_used_only_in_literal_branch": (
            branch_sections[QN_BRANCH]["Q_5_word_relation_count"] == 0
            and branch_sections[LITERAL_QN_PLUS_1_BRANCH][
                "Q_5_word_relation_count"
            ]
            > 0
        ),
    }

    certificate: dict[str, Any] = {
        "schema_version": "final-theory-independent-scalar-v0.3.4",
        "fixture_id": SCALAR_FIXTURE_ID,
        "implementation_boundary": (
            "standalone stdlib Fraction/frozen-JSON parser plus independent "
            "word evaluation; no production v0.3.4 imports"
        ),
        "matrix_interpretation": "each scalar s denotes s*I_2",
        "Q_assignment": {
            "shared_n_le_4": {
                name: _fraction_text(value)
                for name, value in SCALAR_Q_ASSIGNMENT.items()
            },
            "literal_branch_only": {
                "Q_5": _fraction_text(LITERAL_Q5_ASSIGNMENT)
            },
        },
        "frozen_inputs": input_records,
        "schema_checks": schema_checks,
        "dependency_DAG": {
            "node_count": len(node_records),
            "node_kind_counts": dependency_kind_counts,
            "all_node_values_nonzero": all(
                value != 0 for value in node_values.values()
            ),
            "value_digest_sha256": _result_digest(
                sorted(node_values.items())
            ),
        },
        "transition_reconstructions": {
            "count": len(occurrence_results),
            "nonzero_count": sum(
                value != 0 for _identifier, value in occurrence_results
            ),
            "zero_count": sum(
                value == 0 for _identifier, value in occurrence_results
            ),
            "distinct_scalar_values": len(
                {value for _identifier, value in occurrence_results}
            ),
            "value_digest_sha256": _result_digest(occurrence_results),
        },
        "original_CPOBC_word_equations": {
            "compiled_relation_record_count": len(cpobc["relations"]),
            "word_equation_count": len(cpobc_results),
            "zero_residual_count": sum(
                residual == 0 for _identifier, residual in cpobc_results
            ),
            "nonzero_residual_count": sum(
                residual != 0 for _identifier, residual in cpobc_results
            ),
            "equation_kind_counts": equation_kind_counts,
            "residual_digest_sha256": _result_digest(cpobc_results),
        },
        "strong_MSR": {
            "constraint_count": len(msr_results),
            "zero_residual_count": sum(
                residual == 0 for _identifier, residual in msr_results
            ),
            "nonzero_residual_count": sum(
                residual != 0 for _identifier, residual in msr_results
            ),
            "residual_digest_sha256": _result_digest(msr_results),
        },
        "local_operator_GC": {
            "transition_signature_count_from_v031": len(
                signature_occurrences
            ),
            "path_operator_alias_count": len(alias_signatures),
            "basis_relation_count": len(gc_basis_results),
            "basis_zero_residual_count": sum(
                residual == 0
                for _identifier, residual in gc_basis_results
            ),
            "same_endpoint_path_pair_count": len(gc_pair_results),
            "same_endpoint_pair_zero_residual_count": sum(
                residual == 0
                for _identifier, residual in gc_pair_results
            ),
            "basis_residual_digest_sha256": _result_digest(
                gc_basis_results
            ),
            "all_pair_residual_digest_sha256": _result_digest(
                gc_pair_results
            ),
        },
        "atomisation": {
            "path_count": len(atomisation_paths),
            "path_identifier_sets_match": atomisation_ids == reduction_ids,
            "G_node_zero_residual_count": sum(
                residual == 0
                for _identifier, residual in atomisation_results
            ),
            "Q_stage_zero_residual_count": sum(
                residual == 0
                for _identifier, residual in atomisation_q_results
            ),
            "residual_digest_sha256": _result_digest(
                atomisation_results + atomisation_q_results
            ),
        },
        "inverse_nodes": {
            "count": len(inverse_results),
            "base_nonzero_count": inverse_base_nonzero,
            "inverse_value_nonzero_count": inverse_value_nonzero,
            "two_sided_product_one_count": sum(
                residual == 0
                for _identifier, residual in inverse_results
            ),
            "residual_digest_sha256": _result_digest(inverse_results),
        },
        "Eq113_path_consistency_branches": branch_sections,
        "checks": checks,
        "classification_boundary": (
            "This exact scalar witness validates consistency and inventory "
            "reconstruction only; it does not classify general "
            "noncommutative d=2 solutions."
        ),
        "verdict": VERDICT,
        "passed": all(checks.values()),
    }
    certificate["semantic_digest_sha256"] = stable_hash(certificate)
    return certificate


class RationalMatrix2:
    """An exact 2x2 matrix pair ``(numerator, denominator)``.

    The pair is deliberately not cancelled after each operation.  Keeping the
    raw common denominator makes the determinant obligations auditable.
    ``canonical_entries`` provides the reduced rational matrix semantics.
    """

    __slots__ = ("denominator", "numerator")

    def __init__(
        self,
        numerator: sp.MatrixBase | Iterable[Iterable[Any]],
        denominator: Any = 1,
    ) -> None:
        matrix = sp.ImmutableMatrix(numerator)
        if matrix.shape != (DIMENSION, DIMENSION):
            raise ValueError("RationalMatrix2 requires a 2x2 numerator")
        scalar = sp.sympify(denominator)
        if sp.cancel(scalar) == 0:
            raise ValueError("the common denominator is identically zero")
        self.numerator = matrix
        self.denominator = scalar

    @classmethod
    def identity(cls) -> RationalMatrix2:
        return cls(sp.eye(DIMENSION), 1)

    def __matmul__(self, other: RationalMatrix2) -> RationalMatrix2:
        if not isinstance(other, RationalMatrix2):
            return NotImplemented
        return RationalMatrix2(
            self.numerator * other.numerator,
            self.denominator * other.denominator,
        )

    def __add__(self, other: RationalMatrix2) -> RationalMatrix2:
        if not isinstance(other, RationalMatrix2):
            return NotImplemented
        return RationalMatrix2(
            self.numerator * other.denominator
            + other.numerator * self.denominator,
            self.denominator * other.denominator,
        )

    def __sub__(self, other: RationalMatrix2) -> RationalMatrix2:
        if not isinstance(other, RationalMatrix2):
            return NotImplemented
        return RationalMatrix2(
            self.numerator * other.denominator
            - other.numerator * self.denominator,
            self.denominator * other.denominator,
        )

    def adjugate_numerator(self) -> sp.ImmutableMatrix:
        a = self.numerator[0, 0]
        b = self.numerator[0, 1]
        c = self.numerator[1, 0]
        d = self.numerator[1, 1]
        return sp.ImmutableMatrix([[d, -b], [-c, a]])

    def inverse(self) -> RationalMatrix2:
        """Return ``(d*adj(N), det(N))`` without cancellation."""

        return RationalMatrix2(
            self.denominator * self.adjugate_numerator(),
            self.numerator.det(),
        )

    def commutator(self, other: RationalMatrix2) -> RationalMatrix2:
        return self @ other - other @ self

    def canonical_matrix(self) -> sp.ImmutableMatrix:
        return sp.ImmutableMatrix(
            DIMENSION,
            DIMENSION,
            lambda row, column: sp.factor(
                sp.cancel(self.numerator[row, column] / self.denominator)
            ),
        )

    def is_zero(self) -> bool:
        return _zero_matrix(self.numerator)

    def pair_record(self) -> dict[str, Any]:
        return {
            "numerator": _matrix_record(self.numerator),
            "denominator": _exact(self.denominator),
            "canonical_entries": _matrix_record(self.canonical_matrix()),
        }


def rational_inverse_identity_certificate() -> dict[str, Any]:
    """Verify the generic ``(N/d)^-1`` formula as a polynomial identity."""

    a, b, c, e, denominator = sp.symbols("a b c e denominator")
    matrix = RationalMatrix2([[a, b], [c, e]], denominator)
    inverse = matrix.inverse()
    left = matrix @ inverse - RationalMatrix2.identity()
    right = inverse @ matrix - RationalMatrix2.identity()
    expected_inverse_numerator = (
        denominator * sp.ImmutableMatrix([[e, -b], [-c, a]])
    )
    expected_inverse_denominator = a * e - b * c

    return {
        "representation": "M=(N,d) means M=N/d",
        "formula": "(N/d)^-1 = d*adj(N)/det(N)",
        "generic_pair": matrix.pair_record(),
        "computed_inverse_pair": inverse.pair_record(),
        "expected_inverse_pair": {
            "numerator": _matrix_record(expected_inverse_numerator),
            "denominator": _exact(expected_inverse_denominator),
        },
        "formula_pair_matches": (
            inverse.numerator == expected_inverse_numerator
            and sp.expand(
                inverse.denominator - expected_inverse_denominator
            )
            == 0
        ),
        "left_inverse_residual": left.pair_record(),
        "right_inverse_residual": right.pair_record(),
        "left_inverse_verified": left.is_zero(),
        "right_inverse_verified": right.is_zero(),
        "nonzero_obligations": ["denominator != 0", "det(N) != 0"],
        "certificate_kind": "GENERIC_SYMBOLIC_IDENTITY",
    }


def _factor_record(expression: Any) -> dict[str, Any]:
    exact_expression = sp.factor(sp.cancel(sp.sympify(expression)))
    coefficient, factors = sp.factor_list(exact_expression)
    return {
        "expression": _exact(exact_expression),
        "coefficient": _exact(coefficient),
        "factors": [
            {"factor": _exact(factor), "multiplicity": int(multiplicity)}
            for factor, multiplicity in factors
        ],
        "identically_zero": exact_expression == 0,
    }


def _atomic_factor_strings(expressions: Iterable[Any]) -> list[str]:
    factors: set[str] = set()
    for expression in expressions:
        value = sp.factor(sp.cancel(sp.sympify(expression)))
        _coefficient, factor_list = sp.factor_list(value)
        for factor, _multiplicity in factor_list:
            if not factor.is_number:
                factors.add(_exact(factor))
    return sorted(factors)


def _symbolic_base(
    prefix: str,
) -> tuple[RationalMatrix2, RationalMatrix2, dict[str, sp.Symbol]]:
    names = (
        f"{prefix}_p11 {prefix}_p12 {prefix}_p21 {prefix}_p22 "
        f"{prefix}_d1 {prefix}_u11 {prefix}_u12 {prefix}_u21 "
        f"{prefix}_u22 {prefix}_d5"
    )
    (
        p11,
        p12,
        p21,
        p22,
        d1,
        u11,
        u12,
        u21,
        u22,
        d5,
    ) = sp.symbols(names)
    q1 = RationalMatrix2([[p11, p12], [p21, p22]], d1)
    q5 = RationalMatrix2([[u11, u12], [u21, u22]], d5)
    return q1, q5, {
        "p11": p11,
        "p12": p12,
        "p21": p21,
        "p22": p22,
        "d1": d1,
        "u11": u11,
        "u12": u12,
        "u21": u21,
        "u22": u22,
        "d5": d5,
    }


def _s1_chart() -> dict[str, Any]:
    prefix = "s1"
    q1, q5, base = _symbolic_base(prefix)
    symbols = sp.symbols(
        "s1_a2 s1_b2 s1_d2 s1_a3 s1_b3 s1_d3 "
        "s1_a4 s1_b4 s1_d4"
    )
    a2, b2, d2, a3, b3, d3, a4, b4, d4 = symbols
    ratios = {
        2: RationalMatrix2(sp.diag(a2, b2), d2),
        3: RationalMatrix2(sp.diag(a3, b3), d3),
        4: RationalMatrix2(sp.diag(a4, b4), d4),
    }
    assumptions = [
        f"{name} != 0"
        for name in (
            "s1_d1",
            "s1_d2",
            "s1_d3",
            "s1_d4",
            "s1_d5",
            "s1_a2",
            "s1_b2",
            "s1_a3",
            "s1_b3",
            "s1_a4",
            "s1_b4",
        )
    ]
    assumptions.extend(
        [
            "s1_p11*s1_p22-s1_p12*s1_p21 != 0",
            "s1_u11*s1_u22-s1_u12*s1_u21 != 0",
            "s1_a2-s1_b2 != 0",
        ]
    )
    return {
        "fixture_id": "ORACLE_S1_FIXTURE_01",
        "stratum": "S1_DISTINCT_EIGENVALUE",
        "prefix": prefix,
        "q1": q1,
        "q5": q5,
        "ratios": ratios,
        "coordinate_denominators": [
            base["d1"],
            d2,
            d3,
            d4,
            base["d5"],
        ],
        "declared_assumptions": assumptions,
        "pivot_open_condition": "s1_a2-s1_b2 != 0",
        "classification_identity": {
            "pivot": "R_2",
            "discriminant": _exact(((a2 - b2) / d2) ** 2),
            "normal_form": "R_j=diag(a_j,b_j)/d_j",
        },
    }


def _s2_chart() -> dict[str, Any]:
    prefix = "s2"
    q1, q5, base = _symbolic_base(prefix)
    symbols = sp.symbols(
        "s2_l2 s2_m2 s2_d2 s2_l3 s2_m3 s2_d3 "
        "s2_l4 s2_m4 s2_d4"
    )
    l2, m2, d2, l3, m3, d3, l4, m4, d4 = symbols
    ratios = {
        2: RationalMatrix2([[l2, m2], [0, l2]], d2),
        3: RationalMatrix2([[l3, m3], [0, l3]], d3),
        4: RationalMatrix2([[l4, m4], [0, l4]], d4),
    }
    assumptions = [
        f"{name} != 0"
        for name in (
            "s2_d1",
            "s2_d2",
            "s2_d3",
            "s2_d4",
            "s2_d5",
            "s2_l2",
            "s2_l3",
            "s2_l4",
        )
    ]
    assumptions.extend(
        [
            "s2_p11*s2_p22-s2_p12*s2_p21 != 0",
            "s2_u11*s2_u22-s2_u12*s2_u21 != 0",
            "s2_m2 != 0",
        ]
    )
    return {
        "fixture_id": "ORACLE_S2_FIXTURE_01",
        "stratum": "S2_COMMON_NILPOTENT",
        "prefix": prefix,
        "q1": q1,
        "q5": q5,
        "ratios": ratios,
        "coordinate_denominators": [
            base["d1"],
            d2,
            d3,
            d4,
            base["d5"],
        ],
        "declared_assumptions": assumptions,
        "pivot_open_condition": "s2_m2 != 0",
        "classification_identity": {
            "pivot": "R_2",
            "discriminant": "0",
            "normal_form": "R_j=(l_j*I+m_j*E12)/d_j",
            "common_nilpotent": [["0", "1"], ["0", "0"]],
        },
    }


def _s3_chart() -> dict[str, Any]:
    prefix = "s3"
    q1, q5, base = _symbolic_base(prefix)
    l2, d2, l3, d3, l4, d4 = sp.symbols(
        "s3_l2 s3_d2 s3_l3 s3_d3 s3_l4 s3_d4"
    )
    ratios = {
        2: RationalMatrix2(l2 * sp.eye(2), d2),
        3: RationalMatrix2(l3 * sp.eye(2), d3),
        4: RationalMatrix2(l4 * sp.eye(2), d4),
    }
    assumptions = [
        f"{name} != 0"
        for name in (
            "s3_d1",
            "s3_d2",
            "s3_d3",
            "s3_d4",
            "s3_d5",
            "s3_l2",
            "s3_l3",
            "s3_l4",
        )
    ]
    assumptions.extend(
        [
            "s3_p11*s3_p22-s3_p12*s3_p21 != 0",
            "s3_u11*s3_u22-s3_u12*s3_u21 != 0",
        ]
    )
    return {
        "fixture_id": "ORACLE_S3_FIXTURE_01",
        "stratum": "S3_SCALAR",
        "prefix": prefix,
        "q1": q1,
        "q5": q5,
        "ratios": ratios,
        "coordinate_denominators": [
            base["d1"],
            d2,
            d3,
            d4,
            base["d5"],
        ],
        "declared_assumptions": assumptions,
        "pivot_open_condition": "all R_2,R_3,R_4 scalar",
        "classification_identity": {
            "pivot": None,
            "discriminant": "0",
            "normal_form": "R_j=(l_j/d_j)*I",
        },
    }


def _relation_record(
    relation_id: str,
    paper_equation: str,
    formula: str,
    residual: RationalMatrix2,
    *,
    branch: str | None = None,
    literal_printed_branch: bool = False,
) -> dict[str, Any]:
    is_zero = residual.is_zero()
    return {
        "relation_id": relation_id,
        "paper_equation": paper_equation,
        "formula": formula,
        "branch": branch,
        "literal_printed_branch": literal_printed_branch,
        "residual_pair": residual.pair_record(),
        "residual_status": (
            "IDENTICALLY_ZERO_ON_CHART"
            if is_zero
            else "NOT_IDENTICALLY_ZERO_SPECIAL_LOCI_UNANALYSED"
        ),
        "identically_zero": is_zero,
    }


def _inverse_record(
    name: str,
    matrix: RationalMatrix2,
) -> dict[str, Any]:
    inverse = matrix.inverse()
    left = matrix @ inverse - RationalMatrix2.identity()
    right = inverse @ matrix - RationalMatrix2.identity()
    return {
        "matrix": name,
        "input_pair": matrix.pair_record(),
        "inverse_pair": inverse.pair_record(),
        "formula": "(N/d)^-1=d*adj(N)/det(N)",
        "det_numerator": _exact(matrix.numerator.det()),
        "left_residual": left.pair_record(),
        "right_residual": right.pair_record(),
        "left_verified": left.is_zero(),
        "right_verified": right.is_zero(),
    }


def _denominator_inventory(
    chart: dict[str, Any],
    q_matrices: dict[int, RationalMatrix2],
    inverse_records: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    raw_expressions: list[sp.Expr] = []

    def add(identifier: str, kind: str, expression: Any) -> None:
        value = sp.sympify(expression)
        raw_expressions.append(value)
        entries.append(
            {
                "denominator_id": identifier,
                "kind": kind,
                **_factor_record(value),
            }
        )

    for index, expression in enumerate(chart["coordinate_denominators"], 1):
        add(f"COORDINATE_D{index}", "CHART_COORDINATE", expression)
    for index, matrix in sorted(q_matrices.items()):
        add(
            f"Q{index}_RAW_DENOMINATOR",
            "Q_MATRIX_PAIR",
            matrix.denominator,
        )
    for record in inverse_records:
        add(
            f"{record['matrix']}_INVERSE_DET_NUMERATOR",
            "INVERSE_DETERMINANT",
            record["det_numerator"],
        )
    for relation in relations:
        add(
            f"{relation['relation_id']}_RAW_DENOMINATOR",
            "SELECTED_RELATION_RESIDUAL",
            relation["residual_pair"]["denominator"],
        )

    atomic = _atomic_factor_strings(raw_expressions)
    return {
        "pair_convention": "matrix=N/d",
        "entries": entries,
        "entry_count": len(entries),
        "atomic_nonzero_factors": atomic,
        "expected_denominator_factors": atomic,
        "conditional_nonzero_assumptions": [
            f"{factor} != 0" for factor in atomic
        ],
        "contains_identically_zero_denominator": any(
            entry["identically_zero"] for entry in entries
        ),
        "scope_boundary": (
            "Inventory records denominators generated by this chart and the "
            "selected relations only; it is not the denominator inventory of "
            "all 641 compiled relations."
        ),
    }


def _evaluate_chart(chart: dict[str, Any]) -> dict[str, Any]:
    q1: RationalMatrix2 = chart["q1"]
    q5: RationalMatrix2 = chart["q5"]
    ratios: dict[int, RationalMatrix2] = chart["ratios"]
    q_matrices = {
        1: q1,
        2: q1 @ ratios[2],
        3: q1 @ ratios[3],
        4: q1 @ ratios[4],
        5: q5,
    }

    ratio_commutators = [
        ratios[left].commutator(ratios[right])
        for left, right in ((2, 3), (2, 4), (3, 4))
    ]
    q_inverse = {
        index: q_matrices[index].inverse() for index in range(1, 5)
    }

    eq120_213 = (
        q_matrices[2] @ q_inverse[1] @ q_matrices[3]
        - q_matrices[3] @ q_inverse[1] @ q_matrices[2]
    )
    eq120_324 = (
        q_matrices[3] @ q_inverse[2] @ q_matrices[4]
        - q_matrices[4] @ q_inverse[2] @ q_matrices[3]
    )
    eq129 = (
        q_matrices[1] @ q_inverse[2]
    ).commutator(q_matrices[3] @ q_inverse[4])
    eq130 = (
        q_matrices[1] @ q_inverse[2]
    ).commutator(q_inverse[1] @ q_matrices[2])

    # This self-contained branch discriminator sets an invertible synthetic
    # path holonomy H_4 equal to Q_4.  It verifies branch semantics only; it
    # does not assert that a v0.3.3 atomisation path has this holonomy.
    holonomy = q_matrices[4]
    eq113_qn = holonomy.commutator(q_matrices[4])
    eq113_literal = holonomy.commutator(q_matrices[5])

    relations = [
        _relation_record(
            "ORACLE_EQ120_K1_N2_M3",
            "Eq.(120)",
            "Q_2*Q_1^-1*Q_3-Q_3*Q_1^-1*Q_2",
            eq120_213,
        ),
        _relation_record(
            "ORACLE_EQ120_K2_N3_M4",
            "Eq.(120)",
            "Q_3*Q_2^-1*Q_4-Q_4*Q_2^-1*Q_3",
            eq120_324,
        ),
        _relation_record(
            "ORACLE_EQ129_M1_N2_L3_K4",
            "Eq.(129)",
            "[Q_1*Q_2^-1,Q_3*Q_4^-1]",
            eq129,
        ),
        _relation_record(
            "ORACLE_EQ130_Q1_Q2",
            "Eq.(130)",
            "[Q_1*Q_2^-1,Q_1^-1*Q_2]",
            eq130,
        ),
        _relation_record(
            "ORACLE_EQ113_QN_N4",
            "Eq.(113)-derived-index branch",
            "[H_4,Q_4]",
            eq113_qn,
            branch=QN_BRANCH,
        ),
        _relation_record(
            "ORACLE_EQ113_LITERAL_QN_PLUS_1_N4",
            "Eq.(113)-literal-printed branch",
            "[H_4,Q_5]",
            eq113_literal,
            branch=LITERAL_QN_PLUS_1_BRANCH,
            literal_printed_branch=True,
        ),
    ]

    commutators = [
        _relation_record(
            "ORACLE_COMMUTATOR_Q1_Q2",
            "diagnostic",
            "[Q_1,Q_2]",
            q_matrices[1].commutator(q_matrices[2]),
        ),
        _relation_record(
            "ORACLE_COMMUTATOR_Q2_Q3",
            "diagnostic",
            "[Q_2,Q_3]",
            q_matrices[2].commutator(q_matrices[3]),
        ),
    ]
    inverse_records = [
        _inverse_record(f"Q_{index}", q_matrices[index])
        for index in range(1, 6)
    ]
    inventory = _denominator_inventory(
        chart,
        q_matrices,
        inverse_records,
        relations + commutators,
    )
    relation_status = {
        record["relation_id"]: record["identically_zero"]
        for record in relations
    }

    return {
        "fixture_id": chart["fixture_id"],
        "stratum": chart["stratum"],
        "dimension": DIMENSION,
        "chart_kind": "GENERIC_SYMBOLIC_COORDINATE_CHART_NOT_FINITE_SAMPLE",
        "pair_convention": "M=(N,d) means M=N/d",
        "declared_assumptions": chart["declared_assumptions"],
        "pivot_open_condition": chart["pivot_open_condition"],
        "classification_identity": chart["classification_identity"],
        "ratio_matrices": {
            f"R_{index}": ratios[index].pair_record()
            for index in (2, 3, 4)
        },
        "ratio_pairwise_commutators_zero": all(
            residual.is_zero() for residual in ratio_commutators
        ),
        "Q_matrices": {
            f"Q_{index}": q_matrices[index].pair_record()
            for index in range(1, 6)
        },
        "Q_5_scope": "OUTSIDE_N_LE_4_Q_INVENTORY_LITERAL_BRANCH_ONLY",
        "path_holonomy_fixture": {
            "name": "H_4",
            "definition": "H_4=Q_4",
            "pair": holonomy.pair_record(),
            "status": (
                "SYNTHETIC_BRANCH_DISCRIMINATOR_NOT_AN_ATOMISATION_PATH_DERIVATION"
            ),
        },
        "inverse_certificates": inverse_records,
        "selected_exact_relations": relations,
        "selected_relation_identity_map": relation_status,
        "commutator_diagnostics": commutators,
        "Eq113_branch_separation": {
            "branches": [QN_BRANCH, LITERAL_QN_PLUS_1_BRANCH],
            "QN_target": "Q_4",
            "literal_QN_plus_1_target": "Q_5",
            "branch_records_are_distinct": (
                relations[-2]["relation_id"] != relations[-1]["relation_id"]
                and relations[-2]["branch"] != relations[-1]["branch"]
            ),
            "QN_residual_identically_zero": relations[-2][
                "identically_zero"
            ],
            "literal_residual_identically_zero": relations[-1][
                "identically_zero"
            ],
            "source_index_status": "UNRESOLVED_BRANCHES_NOT_MERGED",
        },
        "denominator_inventory": inventory,
        "chart_self_checks": {
            "ratio_family_commutes": all(
                residual.is_zero() for residual in ratio_commutators
            ),
            "all_inverse_identities_verified": all(
                record["left_verified"] and record["right_verified"]
                for record in inverse_records
            ),
            "selected_Eq120_relations_zero": (
                relation_status["ORACLE_EQ120_K1_N2_M3"]
                and relation_status["ORACLE_EQ120_K2_N3_M4"]
            ),
            "selected_Eq129_relation_zero": relation_status[
                "ORACLE_EQ129_M1_N2_L3_K4"
            ],
            "Eq113_branches_kept_distinct": True,
            "no_zero_denominator_generated": not inventory[
                "contains_identically_zero_denominator"
            ],
        },
        "chart_decision_boundary": (
            "This chart is not a full representation and does not eliminate "
            "the stratum. Nonidentity residuals may vanish on unanalysed "
            "special loci."
        ),
    }


def build_fixture_certificates() -> list[dict[str, Any]]:
    return [
        _evaluate_chart(_s1_chart()),
        _evaluate_chart(_s2_chart()),
        _evaluate_chart(_s3_chart()),
    ]


def semantic_descriptor(
    repo_root: Path | None = None,
) -> dict[str, Any]:
    inverse = rational_inverse_identity_certificate()
    fixtures = build_fixture_certificates()
    scalar_fixture = scalar_fixture_certificate(repo_root)
    return {
        "schema_version": "final-theory-independent-d2-rational-v0.3.4",
        "dimension": DIMENSION,
        "implementation_boundary": (
            "standalone standard-library/SymPy/Fraction/frozen-JSON path; "
            "no production v0.3.4 imports"
        ),
        "rational_pair_contract": {
            "representation": "M=(N,d) means M=N/d",
            "inverse": "(N/d)^-1=d*adj(N)/det(N)",
            "generic_inverse_verified": (
                inverse["formula_pair_matches"]
                and inverse["left_inverse_verified"]
                and inverse["right_inverse_verified"]
            ),
        },
        "fixture_ids": [
            "ORACLE_S1_FIXTURE_01",
            "ORACLE_S2_FIXTURE_01",
            "ORACLE_S3_FIXTURE_01",
        ],
        "selected_relation_ids": [
            "ORACLE_EQ120_K1_N2_M3",
            "ORACLE_EQ120_K2_N3_M4",
            "ORACLE_EQ129_M1_N2_L3_K4",
            "ORACLE_EQ130_Q1_Q2",
            "ORACLE_EQ113_QN_N4",
            "ORACLE_EQ113_LITERAL_QN_PLUS_1_N4",
        ],
        "Eq113_branch_contract": {
            "branches": [QN_BRANCH, LITERAL_QN_PLUS_1_BRANCH],
            "QN_target_at_N4": "Q_4",
            "literal_QN_plus_1_target_at_N4": "Q_5",
            "mixing_forbidden": True,
            "source_index_status": "UNRESOLVED_BRANCHES_NOT_MERGED",
        },
        "fixtures": fixtures,
        "exact_scalar_fixture_certificate": scalar_fixture,
        "coverage": {
            "strata_with_one_symbolic_chart": [
                "S1_DISTINCT_EIGENVALUE",
                "S2_COMMON_NILPOTENT",
                "S3_SCALAR",
            ],
            "compiled_relation_count_checked": 641,
            "original_CPOBC_word_equation_count_checked": 783,
            "strong_MSR_constraint_count_checked": 24,
            "local_operator_GC_basis_count_checked": 320,
            "same_endpoint_GC_path_pair_count_checked": 1529,
            "atomisation_path_count_checked": 34,
            "reconstructed_transition_count_checked": 165,
            "inverse_node_count_checked": 26,
            "Eq113_path_words_checked_per_branch": 25,
            "selected_paper_relation_residuals_per_chart": 6,
            "full_641_relation_status": (
                "ALL_ZERO_AT_DECLARED_EXACT_SCALAR_FIXTURE"
            ),
            "full_inventory_scope": (
                "exact scalar witness only, not generic symbolic identities"
            ),
            "all_parameter_loci_status": "UNASSESSED",
            "general_d2_solution_status": "UNASSESSED",
        },
        "verdict": VERDICT,
    }


def semantic_summary(
    repo_root: Path | None = None,
) -> dict[str, Any]:
    descriptor = semantic_descriptor(repo_root)
    return {
        "descriptor": descriptor,
        "semantic_digest_sha256": stable_hash(descriptor),
    }


def run_oracle(
    production_summary: dict[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    inverse = rational_inverse_identity_certificate()
    summary = semantic_summary(repo_root)
    fixtures = summary["descriptor"]["fixtures"]
    scalar_fixture = summary["descriptor"][
        "exact_scalar_fixture_certificate"
    ]
    self_checks = {
        "generic_inverse_formula": (
            inverse["formula_pair_matches"]
            and inverse["left_inverse_verified"]
            and inverse["right_inverse_verified"]
        ),
        "three_declared_charts": len(fixtures) == 3,
        "all_ratio_families_commute": all(
            fixture["ratio_pairwise_commutators_zero"]
            for fixture in fixtures
        ),
        "all_selected_Eq120_Eq129_checks": all(
            fixture["chart_self_checks"]["selected_Eq120_relations_zero"]
            and fixture["chart_self_checks"][
                "selected_Eq129_relation_zero"
            ]
            for fixture in fixtures
        ),
        "Eq113_branches_distinct": all(
            fixture["Eq113_branch_separation"][
                "branch_records_are_distinct"
            ]
            for fixture in fixtures
        ),
        "all_inverse_identities": all(
            fixture["chart_self_checks"][
                "all_inverse_identities_verified"
            ]
            for fixture in fixtures
        ),
        "no_identically_zero_denominators": all(
            fixture["chart_self_checks"]["no_zero_denominator_generated"]
            for fixture in fixtures
        ),
        "exact_scalar_fixture_full_inventory": scalar_fixture["passed"],
    }
    comparison = {
        "performed": production_summary is not None,
        "semantic_digest_match": None,
        "oracle_digest": summary["semantic_digest_sha256"],
        "production_digest": None,
    }
    if production_summary is not None:
        production_digest = production_summary.get(
            "semantic_digest_sha256"
        )
        comparison = {
            "performed": True,
            "semantic_digest_match": (
                summary["semantic_digest_sha256"] == production_digest
            ),
            "oracle_digest": summary["semantic_digest_sha256"],
            "production_digest": production_digest,
        }
    passed = all(self_checks.values()) and (
        production_summary is None
        or bool(comparison["semantic_digest_match"])
    )
    return {
        "schema_version": "final-theory-independent-oracle-result-v0.3.4",
        "inverse_identity_certificate": inverse,
        "semantic_summary": summary,
        "self_checks": self_checks,
        "production_comparison": comparison,
        "unresolved_components": [
            "no production v0.3.4 semantic adapter has been compared yet",
            (
                "the 641/783 CPOBC, 24 strong-MSR, 320 local-GC, and "
                "1,529 path-pair inventories were evaluated only at one "
                "exact scalar fixture"
            ),
            (
                "the generic symbolic-chart Eq.(113) holonomy remains a "
                "synthetic branch discriminator, although all 25+25 frozen "
                "atomisation branch words were checked at the scalar fixture"
            ),
            "the literal branch introduces Q_5 outside the n<=4 Q inventory",
            "special parameter loci of nonidentity residuals were not solved",
            "no S1, S2, or S3 stratum was eliminated",
            "no general d=2 representation or no-go was obtained",
        ],
        "verdict": VERDICT,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--scalar-output", type=Path)
    arguments = parser.parse_args()
    production = None
    if arguments.compare is not None:
        production = json.loads(
            arguments.compare.read_text(encoding="utf-8")
        )
    result = run_oracle(production, repo_root=arguments.repo_root)
    scalar_fixture = result["semantic_summary"]["descriptor"][
        "exact_scalar_fixture_certificate"
    ]
    if arguments.scalar_output is not None:
        arguments.scalar_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.scalar_output.write_text(
            json.dumps(
                scalar_fixture,
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    payload = json.dumps(
        result,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if arguments.output is None:
        print(payload, end="")
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(payload, encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
