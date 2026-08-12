"""Bounded generic 2-by-2 scalar expansion for the 721 native IR.

The source-native compiler first freezes exact free-reduced word IR.  This
gate expands only the finite CPOBC and strong-MSR word equations into generic
2-by-2 commutative scalar polynomials.  The 1,529 fixed-vector GC pairs are
intentionally not expanded in one batch: their path products are a separate,
stage-limited gate.

Only canonical per-equation digests and size statistics are written.  The
potentially multi-million-term polynomial bodies are recomputed on demand and
are not copied into the repository artifact.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
    CPOBC_PATH,
    LOCAL_GC_PATH,
    REDUCTION_PATH,
    _add,
    _compile_cpobc,
    _compile_msr,
    _compile_occurrences,
    _expression_digest,
    _load,
    _matrix_expression,
    _matrix_stats,
    _scale,
    compile_source_native_721_v042,
)

RESULT_PATH = "results/v0.4.2_721_scalar_gate.json"
SCHEMA = "final-theory-v042-721-scalar-gate-v1"
VERDICT = "V042_721_SCALAR_CPOBC_MSR_COMPILED_GC_STAGED_OPEN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cpobc_residuals(
    cpobc: dict[str, Any],
    occurrence_expressions: dict[str, dict[tuple[str, ...], int]],
) -> Iterator[tuple[str, str, dict[tuple[str, ...], int]]]:
    for relation in cpobc["relations"]:
        aliases = {
            alias: str(record["occurrence_id"])
            for alias, record in relation["transition_orbit"].items()
        }
        for equation in relation["raw_noncommutative_relation"]:
            yield (
                str(relation["relation_id"]),
                str(equation["equation_id"]),
                _exact_cpobc_residuals(
                    equation,
                    aliases,
                    occurrence_expressions,
                ),
            )


def _exact_cpobc_residuals(
    equation: dict[str, Any],
    aliases: dict[str, str],
    occurrence_expressions: dict[str, dict[tuple[str, ...], int]],
) -> dict[tuple[str, ...], int]:
    """Build one CPOBC residual with the compiler's exact free reduction."""

    # Imported lazily to keep the public import list above readable and to make
    # this call-site visibly auditable against the predecessor implementation.
    from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
        _multiply,
    )

    lhs: dict[tuple[str, ...], int] = {(): 1}
    for alias in equation["lhs_word"]:
        lhs = _multiply(lhs, occurrence_expressions[aliases[alias]])
    rhs: dict[tuple[str, ...], int] = {(): 1}
    for alias in equation["rhs_word"]:
        rhs = _multiply(rhs, occurrence_expressions[aliases[alias]])
    return _add(lhs, _scale(-1, rhs))


def _msr_residuals(
    cpobc: dict[str, Any],
    occurrence_expressions: dict[str, dict[tuple[str, ...], int]],
) -> Iterator[tuple[str, dict[tuple[str, ...], int]]]:
    for constraint in cpobc["MSR_operator_constraints"]:
        residual: dict[tuple[str, ...], int] = {
            (): int(constraint["identity_coefficient"])
        }
        for term in constraint["terms"]:
            residual = _add(
                residual,
                _scale(
                    int(term["coefficient"]),
                    occurrence_expressions[term["transition_id"]],
                ),
            )
        yield str(constraint["constraint_id"]), residual


def _scalar_matrix_digest(value: tuple[tuple[dict[tuple[str, ...], int], ...], ...]) -> str:
    entries = []
    for row in range(2):
        row_entries = []
        for column in range(2):
            row_entries.append(
                [
                    {"coefficient": coefficient, "monomial": list(monomial)}
                    for monomial, coefficient in sorted(value[row][column].items())
                ]
            )
        entries.append(row_entries)
    return stable_hash(entries)


def _expand_records(
    records: Iterator[tuple[str, str, dict[tuple[str, ...], int]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    materialised = list(records)
    record_keys = [(first_id, second_id) for first_id, second_id, _ in materialised]
    if len(record_keys) != len(set(record_keys)):
        raise AssertionError("duplicate scalar-gate equation id")
    materialised.sort(key=lambda record: (record[0], record[1]))
    output: list[dict[str, Any]] = []
    term_distribution: Counter[int] = Counter()
    total_scalar_terms = 0
    nonzero_scalar_entries = 0
    maximum_scalar_terms = 0
    maximum_monomial_degree = 0
    scalar_zero_count = 0
    word_identity_count = 0
    for first_id, second_id, residual in materialised:
        matrix = _matrix_expression(residual)
        stats = _matrix_stats(matrix)
        word_identity = not residual
        scalar_zero = stats["nonzero_entry_count"] == 0
        if word_identity:
            word_identity_count += 1
        if scalar_zero:
            scalar_zero_count += 1
        if word_identity != scalar_zero:
            raise AssertionError(
                f"generic scalarisation changed zero status: {first_id}/{second_id}"
            )
        output.append(
            {
                "first_id": first_id,
                "second_id": second_id,
                "word_term_count": len(residual),
                "word_identity": word_identity,
                "scalar_matrix": stats,
                "scalar_matrix_sha256": _scalar_matrix_digest(matrix),
                "word_sha256": _expression_digest(residual),
            }
        )
        term_distribution[stats["total_scalar_term_count"]] += 1
        total_scalar_terms += stats["total_scalar_term_count"]
        nonzero_scalar_entries += stats["nonzero_entry_count"]
        maximum_scalar_terms = max(
            maximum_scalar_terms,
            stats["maximum_scalar_term_count"],
        )
        maximum_monomial_degree = max(
            maximum_monomial_degree,
            stats["maximum_monomial_degree"],
        )
    return output, {
        "equation_count": len(output),
        "word_identity_count": word_identity_count,
        "scalar_zero_matrix_count": scalar_zero_count,
        "scalar_nonzero_matrix_count": len(output) - scalar_zero_count,
        "nonzero_scalar_entry_count": nonzero_scalar_entries,
        "total_scalar_term_count": total_scalar_terms,
        "maximum_scalar_term_count": maximum_scalar_terms,
        "maximum_monomial_degree": maximum_monomial_degree,
        "total_scalar_term_distribution": {
            str(key): value for key, value in sorted(term_distribution.items())
        },
        "record_digest_sha256": stable_hash(output),
    }


def _expand_msr_records(
    records: Iterator[tuple[str, dict[tuple[str, ...], int]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return _expand_records(
        (constraint_id, "", residual)
        for constraint_id, residual in records
    )


def compile_scalar_gate_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cpobc = _load(root, CPOBC_PATH)
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    occurrence_expressions, _, generator_summary = _compile_occurrences(reduction)
    if source_result["verdict"] != "V042_721_SOURCE_NATIVE_EQ112_FREE_IR_COMPILED_OPEN":
        raise AssertionError("scalar gate input verdict changed")
    if generator_summary["eq112_tokens_present"]:
        raise AssertionError("Eq.(112) B tokens leaked into scalar gate")

    # Re-run the predecessor's frozen word checks before any scalar expansion.
    cpobc_word_summary = _compile_cpobc(
        cpobc,
        reduction,
        occurrence_expressions,
    )
    msr_word_summary = _compile_msr(
        cpobc,
        reduction,
        occurrence_expressions,
    )
    cpobc_records, cpobc_scalar_summary = _expand_records(
        _cpobc_residuals(cpobc, occurrence_expressions)
    )
    msr_records, msr_scalar_summary = _expand_msr_records(
        _msr_residuals(cpobc, occurrence_expressions)
    )
    if cpobc_scalar_summary["equation_count"] != cpobc_word_summary["word_equation_count"]:
        raise AssertionError("CPOBC scalar count diverged from word count")
    if msr_scalar_summary["equation_count"] != msr_word_summary["constraint_count"]:
        raise AssertionError("MSR scalar count diverged from word count")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
            "dimension": 2,
            "input_ir": "v0.4.2 source-native free-reduced words",
            "CPOBC": "expanded",
            "strong_MSR": "expanded",
            "fixed_vector_GC": "not expanded; staged gate required",
            "inverse_saturation": "not imposed; inverse tokens remain separate variables",
            "elimination": "not performed",
        },
        "source_artifact_sha256": {
            relative: _sha256(root / relative)
            for relative in (CPOBC_PATH, REDUCTION_PATH, LOCAL_GC_PATH)
        },
        "compiler_source_sha256": _sha256(Path(__file__).resolve()),
        "input_native_ir_semantic_digest_sha256": source_result[
            "semantic_digest_sha256"
        ],
        "word_precheck": {
            "CPOBC": cpobc_word_summary,
            "strong_MSR": msr_word_summary,
        },
        "CPOBC": {
            "summary": cpobc_scalar_summary,
            "records": cpobc_records,
        },
        "strong_MSR": {
            "summary": msr_scalar_summary,
            "records": msr_records,
        },
        "fixed_vector_GC": {
            "expanded": False,
            "same_endpoint_pair_count": len(local_gc["all_pair_derivations"]),
            "path_count": sum(
                len(paths) for paths in local_gc["path_inventory"].values()
            ),
            "next_gate": "stage-limited path-pair scalar expansion",
            "reason": (
                "one-batch expansion is intentionally excluded after the bounded "
                "CPOBC/MSR measurement; no GC result is inferred"
            ),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 0,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "CPOBC and strong-MSR word equations were expanded and digest-checked "
            "as generic 2x2 scalar polynomials.",
            "The scalar representation does not impose matrix inverse equations "
            "or determinant nonzero saturation.",
            "The fixed-vector GC pair inventory is not scalar-expanded by this gate.",
            "No full 721 commutativity theorem, witness, or obstruction is issued.",
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


def write_scalar_gate_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_scalar_gate_v042(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_scalar_gate_v042(Path(__file__).resolve().parents[3]))
