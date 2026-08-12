"""Source-native IR compiler for the 721 fixed-vector-GC profile.

This is the first native step after the Eq. (112) route was withdrawn.  The
v0.3.2 Eq. (107)/(108) occurrence map is retained, but the twenty
non-antichain gregarious generators are kept as independent atoms.  No
Eq. (112) conjugation, B auxiliary, or atomisation substitution is imported.

The compiler emits an exact, occurrence-identified free-reduced word
intermediate representation.  It deliberately does not run an elimination or
expand all 1,529 path pairs into generic 2-by-2 scalar polynomials.  The
fixed-vector GC obligations are retained as path-word residuals with the path
convention used by the existing verifier: each later transition is multiplied
on the left.  Scalar expansion is a separately bounded gate.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
LOCAL_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
RESULT_PATH = "results/v0.4.2_721_source_native_preflight.json"

SCHEMA = "final-theory-v042-721-source-native-preflight-v1"
VERDICT = "V042_721_SOURCE_NATIVE_EQ112_FREE_IR_COMPILED_OPEN"

type Word = tuple[str, ...]
type Expression = dict[Word, int]
type Scalar = dict[Word, int]
type ScalarMatrix = tuple[
    tuple[Scalar, Scalar],
    tuple[Scalar, Scalar],
]


def _load(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {relative}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inverse_token(token: str) -> str:
    return token.removesuffix("^-1") if token.endswith("^-1") else token + "^-1"


def _free_reduce(word: Word) -> Word:
    result: list[str] = []
    for token in word:
        if result and result[-1] == _inverse_token(token):
            result.pop()
        else:
            result.append(token)
    return tuple(result)


def _normalise(expression: Expression) -> Expression:
    return {
        word: coefficient
        for word, coefficient in sorted(expression.items())
        if coefficient
    }


def _add(left: Expression, right: Expression) -> Expression:
    result = dict(left)
    for word, coefficient in right.items():
        reduced = _free_reduce(word)
        result[reduced] = result.get(reduced, 0) + coefficient
    return _normalise(result)


def _scale(coefficient: int, expression: Expression) -> Expression:
    return _normalise(
        {word: coefficient * value for word, value in expression.items()}
    )


def _multiply(left: Expression, right: Expression) -> Expression:
    result: Expression = {}
    for left_word, left_coefficient in left.items():
        for right_word, right_coefficient in right.items():
            word = _free_reduce(left_word + right_word)
            result[word] = result.get(word, 0) + left_coefficient * right_coefficient
    return _normalise(result)


def _expression_from_record(terms: list[dict[str, Any]]) -> Expression:
    result: Expression = {}
    for term in terms:
        word = _free_reduce(tuple(str(token) for token in term["word"]))
        result[word] = result.get(word, 0) + int(term["coefficient"])
    return _normalise(result)


def _expression_record(expression: Expression) -> list[dict[str, Any]]:
    return [
        {"coefficient": coefficient, "word": list(word)}
        for word, coefficient in sorted(expression.items())
    ]


def _expression_digest(expression: Expression) -> str:
    return stable_hash(_expression_record(expression))


def _relation_code(rows: list[int] | tuple[int, ...]) -> int:
    size = len(rows)
    return sum(int(row) << (index * size) for index, row in enumerate(rows))


def _zero_scalar() -> Scalar:
    return {}


def _scalar_constant(value: int) -> Scalar:
    return {} if value == 0 else {(): value}


def _scalar_variable(name: str) -> Scalar:
    return {(name,): 1}


def _scalar_add(left: Scalar, right: Scalar) -> Scalar:
    result = dict(left)
    for monomial, coefficient in right.items():
        result[monomial] = result.get(monomial, 0) + coefficient
    return {
        monomial: coefficient
        for monomial, coefficient in sorted(result.items())
        if coefficient
    }


def _scalar_scale(coefficient: int, value: Scalar) -> Scalar:
    return {
        monomial: coefficient * value_coefficient
        for monomial, value_coefficient in value.items()
        if coefficient * value_coefficient
    }


def _scalar_multiply(left: Scalar, right: Scalar) -> Scalar:
    result: Scalar = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(sorted(left_monomial + right_monomial))
            result[monomial] = result.get(monomial, 0) + left_coefficient * right_coefficient
    return {
        monomial: coefficient
        for monomial, coefficient in sorted(result.items())
        if coefficient
    }


def _matrix_add(left: ScalarMatrix, right: ScalarMatrix) -> ScalarMatrix:
    return tuple(
        tuple(_scalar_add(left[row][column], right[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_scale(coefficient: int, value: ScalarMatrix) -> ScalarMatrix:
    return tuple(
        tuple(_scalar_scale(coefficient, value[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_multiply(left: ScalarMatrix, right: ScalarMatrix) -> ScalarMatrix:
    return tuple(
        tuple(
            _scalar_add(
                _scalar_multiply(left[row][0], right[0][column]),
                _scalar_multiply(left[row][1], right[1][column]),
            )
            for column in range(2)
        )
        for row in range(2)
    )  # type: ignore[return-value]


def _identity_matrix() -> ScalarMatrix:
    return (
        (_scalar_constant(1), _zero_scalar()),
        (_zero_scalar(), _scalar_constant(1)),
    )


def _token_name(token: str) -> str:
    return token.replace("^-1", "_INV").replace("-", "_")


def _token_matrix(token: str) -> ScalarMatrix:
    prefix = f"M_{_token_name(token)}"
    return (
        (_scalar_variable(f"{prefix}_00"), _scalar_variable(f"{prefix}_01")),
        (_scalar_variable(f"{prefix}_10"), _scalar_variable(f"{prefix}_11")),
    )


def _matrix_word(word: Word) -> ScalarMatrix:
    product = _identity_matrix()
    for token in word:
        product = _matrix_multiply(product, _token_matrix(token))
    return product


def _matrix_expression(expression: Expression) -> ScalarMatrix:
    result = (
        (_zero_scalar(), _zero_scalar()),
        (_zero_scalar(), _zero_scalar()),
    )
    for word, coefficient in expression.items():
        result = _matrix_add(result, _matrix_scale(coefficient, _matrix_word(word)))
    return result


def _vector_expression(expression: Expression) -> tuple[Scalar, Scalar]:
    matrix = _matrix_expression(expression)
    return matrix[0][0], matrix[1][0]


def _scalar_stats(value: Scalar) -> dict[str, Any]:
    return {
        "term_count": len(value),
        "max_monomial_degree": max((len(monomial) for monomial in value), default=0),
    }


def _matrix_stats(value: ScalarMatrix) -> dict[str, Any]:
    entries = [value[row][column] for row in range(2) for column in range(2)]
    return {
        "nonzero_entry_count": sum(bool(entry) for entry in entries),
        "total_scalar_term_count": sum(len(entry) for entry in entries),
        "maximum_scalar_term_count": max((len(entry) for entry in entries), default=0),
        "maximum_monomial_degree": max(
            (len(monomial) for entry in entries for monomial in entry),
            default=0,
        ),
    }


def _vector_stats(value: tuple[Scalar, Scalar]) -> dict[str, Any]:
    entries = list(value)
    return {
        "nonzero_component_count": sum(bool(entry) for entry in entries),
        "total_scalar_term_count": sum(len(entry) for entry in entries),
        "maximum_scalar_term_count": max((len(entry) for entry in entries), default=0),
        "maximum_monomial_degree": max(
            (len(monomial) for entry in entries for monomial in entry),
            default=0,
        ),
    }


def _counter_distribution(counter: Counter[int]) -> dict[str, int]:
    """Use string keys so the in-memory payload equals its JSON reload."""

    return {str(key): value for key, value in sorted(counter.items())}


def _compile_occurrences(
    reduction: dict[str, Any],
) -> tuple[
    dict[str, Expression],
    dict[tuple[int, int, int], Expression],
    dict[str, Any],
]:
    reduction_map = reduction["reduction_map"]
    occurrence_ids = [str(record["occurrence_id"]) for record in reduction_map]
    if len(occurrence_ids) != len(set(occurrence_ids)):
        raise AssertionError("duplicate transition occurrence id")
    expressions = {
        str(record["occurrence_id"]): _expression_from_record(record["reduced_expression"])
        for record in reduction_map
    }
    if len(expressions) != len(reduction_map):
        raise AssertionError("transition occurrence map lost an entry")
    by_signature: dict[tuple[int, int, int], Expression] = {}
    for record in reduction_map:
        key = (
            int(record["stage"]),
            _relation_code(record["source_relation_rows"]),
            int(record["precursor_code"]),
        )
        expression = expressions[str(record["occurrence_id"])]
        previous = by_signature.setdefault(key, expression)
        if previous != expression:
            raise AssertionError("one decorated transition signature has conflicting expressions")

    generators = [
        {
            "generator": record["generator"],
            "source_id": record["source_id"],
            "stage": int(record["stage"]),
            "kind": record["kind"],
            "retained_as_native_atom": record["kind"] == "CAUSET_GREGARIOUS",
        }
        for record in reduction["generator_inventory"]
    ]
    generator_names = [record["generator"] for record in generators]
    if len(generator_names) != len(set(generator_names)):
        raise AssertionError("duplicate native generator name")
    base_generators = {record["generator"] for record in generators}
    used_tokens = {
        token
        for expression in expressions.values()
        for word in expression
        for token in word
    }
    for token in used_tokens:
        base = token.removesuffix("^-1")
        if base not in base_generators:
            raise AssertionError(f"unknown native generator token: {token}")
    inverse_tokens = sorted(token for token in used_tokens if token.endswith("^-1"))
    return expressions, by_signature, {
        "generators": generators,
        "base_generator_count": len(base_generators),
        "non_antichain_generator_count": sum(
            record["kind"] == "CAUSET_GREGARIOUS" for record in generators
        ),
        "used_token_count": len(used_tokens),
        "used_inverse_token_count": len(inverse_tokens),
        "used_inverse_tokens": inverse_tokens,
        "eq112_tokens_present": any(
            token.startswith("BDEF:") or token.startswith("BINV:") for token in used_tokens
        ),
        "occurrence_count": len(expressions),
        "signature_count": len(by_signature),
    }


def _compile_cpobc(
    cpobc: dict[str, Any],
    reduction: dict[str, Any],
    occurrence_expressions: dict[str, Expression],
) -> dict[str, Any]:
    frozen = {
        (record["relation_id"], record["equation_id"]): record
        for record in reduction["rewritten_relation_inventory"]
    }
    records: list[dict[str, Any]] = []
    for relation in cpobc["relations"]:
        aliases = {
            alias: str(record["occurrence_id"])
            for alias, record in relation["transition_orbit"].items()
        }
        for equation in relation["raw_noncommutative_relation"]:
            lhs: Expression = {(): 1}
            for alias in equation["lhs_word"]:
                lhs = _multiply(lhs, occurrence_expressions[aliases[alias]])
            rhs: Expression = {(): 1}
            for alias in equation["rhs_word"]:
                rhs = _multiply(rhs, occurrence_expressions[aliases[alias]])
            residual = _add(lhs, _scale(-1, rhs))
            key = (relation["relation_id"], equation["equation_id"])
            expected = frozen[key]
            if (
                expected["reduced_term_count"] != len(residual)
                or expected["identity_after_reduction"] != (not residual)
                or expected["reduced_residual_sha256"] != _expression_digest(residual)
            ):
                raise AssertionError(f"CPOBC reduction mismatch: {key}")
            records.append(
                {
                    "relation_id": relation["relation_id"],
                    "equation_id": equation["equation_id"],
                    "free_word_term_count": len(residual),
                    "identity_after_free_reduction": not residual,
                    "free_word_sha256": _expression_digest(residual),
                }
            )
    identities = sum(record["identity_after_free_reduction"] for record in records)
    return {
        "source_relation_count": len(cpobc["relations"]),
        "word_equation_count": len(records),
        "free_word_identity_count": identities,
        "free_word_residual_count": len(records) - identities,
        "free_word_residual_term_distribution": _counter_distribution(
            Counter(
                record["free_word_term_count"]
                for record in records
                if record["free_word_term_count"]
            )
        ),
        "matches_v032_eq107_eq108_reduction": True,
    }


def _compile_msr(
    cpobc: dict[str, Any],
    reduction: dict[str, Any],
    occurrence_expressions: dict[str, Expression],
) -> dict[str, Any]:
    frozen = {
        record["constraint_id"]: record
        for record in reduction["rewritten_MSR_inventory"]
    }
    records: list[dict[str, Any]] = []
    for constraint in cpobc["MSR_operator_constraints"]:
        residual: Expression = {(): int(constraint["identity_coefficient"])}
        for term in constraint["terms"]:
            residual = _add(
                residual,
                _scale(int(term["coefficient"]), occurrence_expressions[term["transition_id"]]),
            )
        expected = frozen[constraint["constraint_id"]]
        if (
            expected["reduced_term_count"]
            if "reduced_term_count" in expected
            else len(expected["reduced_residual"])
        ) != len(residual):
            raise AssertionError(f"MSR term count mismatch: {constraint['constraint_id']}")
        if expected["reduced_residual_sha256"] != _expression_digest(residual):
            raise AssertionError(f"MSR reduction mismatch: {constraint['constraint_id']}")
        records.append(
            {
                "constraint_id": constraint["constraint_id"],
                "free_word_term_count": len(residual),
                "identity_after_free_reduction": not residual,
                "free_word_sha256": _expression_digest(residual),
            }
        )
    identities = sum(record["identity_after_free_reduction"] for record in records)
    return {
        "constraint_count": len(records),
        "free_word_identity_count": identities,
        "free_word_residual_count": len(records) - identities,
        "free_word_residual_term_distribution": _counter_distribution(
            Counter(
                record["free_word_term_count"]
                for record in records
                if record["free_word_term_count"]
            )
        ),
        "records": records,
    }


def _compile_fixed_vector_gc(
    local_gc: dict[str, Any],
    by_signature: dict[tuple[int, int, int], Expression],
) -> dict[str, Any]:
    path_expressions: dict[str, Expression] = {}
    path_term_counts: Counter[int] = Counter()
    for paths in local_gc["path_inventory"].values():
        for path in paths:
            if path["path_id"] in path_expressions:
                raise AssertionError(f"duplicate local GC path id: {path['path_id']}")
            product: Expression = {(): 1}
            for transition in path["transitions"]:
                signature = transition["quotient_signature"]
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                # This is deliberate: the later transition acts on the left.
                product = _multiply(by_signature[key], product)
            path_expressions[path["path_id"]] = product
            path_term_counts[len(product)] += 1

    operator_identity_count = 0
    operator_residual_term_counts: Counter[int] = Counter()
    for relation in local_gc["all_pair_derivations"]:
        residual = _add(
            path_expressions[relation["left_path_id"]],
            _scale(-1, path_expressions[relation["right_path_id"]]),
        )
        if not residual:
            operator_identity_count += 1
        else:
            operator_residual_term_counts[len(residual)] += 1
    return {
        "path_count": len(path_expressions),
        "path_term_count_distribution": _counter_distribution(path_term_counts),
        "basis_relation_count": len(local_gc["generating_relation_basis"]),
        "same_endpoint_pair_count": len(local_gc["all_pair_derivations"]),
        "operator_word_identity_pair_count": operator_identity_count,
        "operator_word_residual_pair_count": sum(operator_residual_term_counts.values()),
        "operator_word_residual_term_distribution": _counter_distribution(
            operator_residual_term_counts
        ),
        "path_product_convention": "later_transition_multiplies_on_left",
        "fixed_vector_action": {
            "compiled": False,
            "representation": "free-reduced path word residuals retained",
            "reason": "generic 2x2 scalar expansion is a separate bounded gate",
        },
    }


def compile_source_native_721_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cpobc = _load(root, CPOBC_PATH)
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    occurrence_expressions, by_signature, generator_summary = _compile_occurrences(reduction)
    if generator_summary["base_generator_count"] != 24:
        raise AssertionError("the native generator count changed")
    if generator_summary["non_antichain_generator_count"] != 20:
        raise AssertionError("the non-antichain generator count changed")
    if generator_summary["eq112_tokens_present"]:
        raise AssertionError("Eq.(112) B tokens leaked into the native IR")

    cpo = _compile_cpobc(cpobc, reduction, occurrence_expressions)
    msr = _compile_msr(cpobc, reduction, occurrence_expressions)
    gc = _compile_fixed_vector_gc(local_gc, by_signature)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "field": "QQ symbolic free-reduced word IR",
            "dimension": 2,
            "identification_mode": "ON quotient",
            "source_stages": "n<=4; same-endpoint GC paths through endpoint stage 5",
            "Eq107_Eq108": "retained",
            "Eq112": "excluded",
            "scalar_matrix_expansion": "deferred to a separate bounded gate",
        },
        "source_artifact_sha256": {
            relative: _sha256(root / relative)
            for relative in (CPOBC_PATH, REDUCTION_PATH, LOCAL_GC_PATH)
        },
        "native_generators": generator_summary,
        "occurrence_map": {
            "transition_occurrences": len(occurrence_expressions),
            "decorated_signatures": len(by_signature),
            "matrix_entry_variables_per_token": 4,
            "inverse_relation_entry_slots": generator_summary["used_inverse_token_count"] * 8,
            "occurrence_determinant_nonzero_predicates": len(occurrence_expressions),
        },
        "CPOBC": cpo,
        "strong_MSR": msr,
        "fixed_vector_GC": gc,
        "solver_status": {
            "symbolic_IR_compiled": True,
            "generic_2x2_scalar_expansion": False,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "The IR keeps the 20 non-antichain G generators as atoms and does not use Eq.(112).",
            "Eq.(107)/(108) occurrence reduction is retained and independently digest-checked.",
            "The fixed-vector GC records are source-native path-word obligations; "
            "scalar expansion and elimination are not claimed.",
            "No full 721 commutativity theorem or noncommutative witness is issued here.",
        ],
        "unrestricted_721_status": "OPEN",
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def write_source_native_721_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_source_native_721_v042(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_source_native_721_v042(Path(__file__).resolve().parents[3]))
