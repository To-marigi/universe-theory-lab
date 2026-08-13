"""Re-expand CPOBC and strong-MSR under the saturated inverse tokens.

``source_native_721_scalar_gate_v042.py`` expanded all 783 CPOBC and 24
strong-MSR word equations into generic 2x2 scalar matrices, but every
inverse token was a scalar-free variable with no tie to its forward
generator. ``source_native_721_inverse_saturation_v042.py`` then gave each
of the 8 inverse tokens exact algebraic content: ``A^-1 = (1/det A) *
adj(A)`` via one fresh ``D_<token> = 1/det(A)`` variable per token.

This gate re-expands the same 807 residuals with every inverse-token matrix
replaced by that closed-form definition, and compares each equation's
scalar-zero status before and after substitution. The scientific question
this answers: does saturating the inverse tokens close any previously-open
(scalar-nonzero) CPOBC or strong-MSR residual, or introduce a new one?
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
    Expression,
    ScalarMatrix,
    _compile_cpobc,
    _compile_msr,
    _compile_occurrences,
    _expression_digest,
    _identity_matrix,
    _load,
    _matrix_add,
    _matrix_expression,
    _matrix_multiply,
    _matrix_scale,
    _matrix_stats,
    _scalar_variable,
    _token_matrix,
    _token_name,
    compile_source_native_721_v042,
)
from universe_lab.final_theory.source_native_721_inverse_saturation_v042 import (
    RESULT_PATH as SATURATION_RESULT_PATH,
)
from universe_lab.final_theory.source_native_721_inverse_saturation_v042 import (
    _defined_inverse_matrix,
    compile_inverse_saturation_v042,
)
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    RESULT_PATH as SCALAR_GATE_RESULT_PATH,
)
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    _cpobc_residuals,
    _msr_residuals,
    _scalar_matrix_digest,
)

RESULT_PATH = "results/v0.4.2_721_inverse_resaturated_cpobc_msr.json"
SCHEMA = "final-theory-v042-721-inverse-resaturated-cpobc-msr-v1"
VERDICT = "V042_721_CPOBC_MSR_RESATURATED_NO_NEWLY_ZERO_RESIDUAL_OPEN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _token_matrix_saturated(token: str) -> ScalarMatrix:
    if not token.endswith("^-1"):
        return _token_matrix(token)
    base_token = token.removesuffix("^-1")
    base_matrix = _token_matrix(base_token)
    det_inverse_variable = _scalar_variable(f"D_{_token_name(base_token)}")
    return _defined_inverse_matrix(base_matrix, det_inverse_variable)


def _matrix_word_saturated(word: tuple[str, ...]) -> ScalarMatrix:
    product = _identity_matrix()
    for token in word:
        product = _matrix_multiply(product, _token_matrix_saturated(token))
    return product


def _matrix_expression_saturated(expression: Expression) -> ScalarMatrix:
    result = (
        ({}, {}),
        ({}, {}),
    )
    for word, coefficient in expression.items():
        result = _matrix_add(result, _matrix_scale(coefficient, _matrix_word_saturated(word)))
    return result


def _expand_with_saturation(
    records: Iterator[tuple[str, str, Expression]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    materialised = list(records)
    record_keys = [(first_id, second_id) for first_id, second_id, _ in materialised]
    if len(record_keys) != len(set(record_keys)):
        raise AssertionError("duplicate resaturated-gate equation id")
    materialised.sort(key=lambda record: (record[0], record[1]))

    output: list[dict[str, Any]] = []
    newly_zero_count = 0
    still_nonzero_count = 0
    unexpectedly_nonzero_count = 0
    total_saturated_terms = 0
    maximum_saturated_terms = 0
    maximum_saturated_degree = 0
    term_distribution: Counter[int] = Counter()

    for first_id, second_id, residual in materialised:
        word_identity = not residual
        unsaturated_matrix = _matrix_expression(residual)
        unsaturated_stats = _matrix_stats(unsaturated_matrix)
        saturated_matrix = _matrix_expression_saturated(residual)
        saturated_stats = _matrix_stats(saturated_matrix)

        unsaturated_zero = unsaturated_stats["nonzero_entry_count"] == 0
        saturated_zero = saturated_stats["nonzero_entry_count"] == 0
        if word_identity != unsaturated_zero:
            raise AssertionError(f"unsaturated zero status regressed: {first_id}/{second_id}")
        if saturated_zero and not unsaturated_zero:
            status = "NEWLY_ZERO_UNDER_SATURATION"
            newly_zero_count += 1
        elif not saturated_zero and unsaturated_zero:
            status = "UNEXPECTEDLY_NONZERO_UNDER_SATURATION"
            unexpectedly_nonzero_count += 1
        elif saturated_zero:
            status = "ZERO_BOTH"
        else:
            status = "NONZERO_BOTH"
            still_nonzero_count += 1

        output.append(
            {
                "first_id": first_id,
                "second_id": second_id,
                "word_identity": word_identity,
                "unsaturated_scalar_zero": unsaturated_zero,
                "saturated_scalar_zero": saturated_zero,
                "status": status,
                "saturated_scalar_matrix": saturated_stats,
                "saturated_scalar_matrix_sha256": _scalar_matrix_digest(saturated_matrix),
                "word_sha256": _expression_digest(residual),
            }
        )
        term_distribution[saturated_stats["total_scalar_term_count"]] += 1
        total_saturated_terms += saturated_stats["total_scalar_term_count"]
        maximum_saturated_terms = max(
            maximum_saturated_terms, saturated_stats["maximum_scalar_term_count"]
        )
        maximum_saturated_degree = max(
            maximum_saturated_degree, saturated_stats["maximum_monomial_degree"]
        )

    if unexpectedly_nonzero_count:
        raise AssertionError(
            "saturation made a previously-zero residual nonzero: "
            f"{unexpectedly_nonzero_count} occurrences"
        )

    return output, {
        "equation_count": len(output),
        "newly_zero_under_saturation_count": newly_zero_count,
        "still_nonzero_under_saturation_count": still_nonzero_count,
        "total_saturated_scalar_term_count": total_saturated_terms,
        "maximum_saturated_scalar_term_count": maximum_saturated_terms,
        "maximum_saturated_monomial_degree": maximum_saturated_degree,
        "total_saturated_scalar_term_distribution": {
            str(key): value for key, value in sorted(term_distribution.items())
        },
        "record_digest_sha256": stable_hash(output),
    }


def _expand_msr_with_saturation(
    records: Iterator[tuple[str, Expression]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return _expand_with_saturation(
        (constraint_id, "", residual) for constraint_id, residual in records
    )


def compile_inverse_resaturated_cpobc_msr_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cpobc = _load(root, CPOBC_PATH)
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    saturation_result = compile_inverse_saturation_v042(root)
    if not all(record["saturates"] for record in saturation_result["records"]):
        raise AssertionError("inverse tokens do not saturate; refusing to resaturate")
    occurrence_expressions, _, generator_summary = _compile_occurrences(reduction)
    if generator_summary["eq112_tokens_present"]:
        raise AssertionError("Eq.(112) B tokens leaked into resaturated gate")

    cpobc_word_summary = _compile_cpobc(cpobc, reduction, occurrence_expressions)
    msr_word_summary = _compile_msr(cpobc, reduction, occurrence_expressions)

    cpobc_records, cpobc_summary = _expand_with_saturation(
        _cpobc_residuals(cpobc, occurrence_expressions)
    )
    msr_records, msr_summary = _expand_msr_with_saturation(
        _msr_residuals(cpobc, occurrence_expressions)
    )
    if cpobc_summary["equation_count"] != cpobc_word_summary["word_equation_count"]:
        raise AssertionError("CPOBC resaturated count diverged from word count")
    if msr_summary["equation_count"] != msr_word_summary["constraint_count"]:
        raise AssertionError("MSR resaturated count diverged from word count")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
            "inverse_definition": "A^-1 = (1/det A) * adj(A) via one D_<token> per token",
            "CPOBC": "re-expanded under saturated inverse tokens",
            "strong_MSR": "re-expanded under saturated inverse tokens",
            "fixed_vector_GC": "not re-expanded here; a separate bounded gate",
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
        "input_scalar_gate_sha256": _sha256(root / SCALAR_GATE_RESULT_PATH),
        "input_inverse_saturation_sha256": _sha256(root / SATURATION_RESULT_PATH),
        "CPOBC": {
            "summary": cpobc_summary,
            "records": cpobc_records,
        },
        "strong_MSR": {
            "summary": msr_summary,
            "records": msr_records,
        },
        "fixed_vector_GC": {
            "resaturated": False,
            "same_endpoint_pair_count": len(local_gc["all_pair_derivations"]),
            "reason": "1,529-pair resaturation is a separate bounded gate",
        },
        "overall": {
            "total_newly_zero_under_saturation": (
                cpobc_summary["newly_zero_under_saturation_count"]
                + msr_summary["newly_zero_under_saturation_count"]
            ),
            "total_still_nonzero_under_saturation": (
                cpobc_summary["still_nonzero_under_saturation_count"]
                + msr_summary["still_nonzero_under_saturation_count"]
            ),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 8,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "CPOBC and strong-MSR were re-expanded with every inverse token "
            "replaced by its closed-form definition; no previously-zero "
            "residual became nonzero (checked, fails closed otherwise).",
            "The fixed-vector GC pair inventory is not resaturated by this gate.",
            "No elimination combining the D_<token>*det-1=0 relations with the "
            "residuals themselves has been attempted.",
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


def write_inverse_resaturated_cpobc_msr(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(
            compile_inverse_resaturated_cpobc_msr_v042(root), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_inverse_resaturated_cpobc_msr(Path(__file__).resolve().parents[3]))
