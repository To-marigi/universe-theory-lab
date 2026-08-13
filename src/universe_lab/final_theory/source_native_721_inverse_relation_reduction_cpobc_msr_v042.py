"""Full CPOBC/strong-MSR sweep: reduce every residual modulo the 8 relations.

The bounded probe (``source_native_721_inverse_relation_reduction_probe_v042.py``)
measured a fast, correct reduction on a 24-residual sample (mean 3.5ms, max
15.5ms) and confirmed the worst known CPOBC equation (186,116 saturated
terms) reduces in 2.8s. This gate runs the same exact reduction --
rewriting ``D*a*d -> 1+D*b*c`` per token, binomial-expanded for repeated
occurrences, confluent because the 8 tokens' relation variables are
pairwise disjoint -- over the full 783 CPOBC and 24 strong-MSR word
equations, and asks: does actually using the defining relations (not just
substituting the inverse tokens) close any previously scalar-nonzero
residual?
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
    _compile_occurrences,
    _expression_digest,
    _load,
    _matrix_stats,
    compile_source_native_721_v042,
)
from universe_lab.final_theory.source_native_721_inverse_relation_reduction_probe_v042 import (
    _reduce_matrix,
)
from universe_lab.final_theory.source_native_721_inverse_resaturated_cpobc_msr_v042 import (
    RESULT_PATH as RESATURATION_RESULT_PATH,
)
from universe_lab.final_theory.source_native_721_inverse_resaturated_cpobc_msr_v042 import (
    _matrix_expression_saturated,
)
from universe_lab.final_theory.source_native_721_inverse_saturation_v042 import (
    RESULT_PATH as SATURATION_RESULT_PATH,
)
from universe_lab.final_theory.source_native_721_inverse_saturation_v042 import (
    compile_inverse_saturation_v042,
)
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    _cpobc_residuals,
    _msr_residuals,
    _scalar_matrix_digest,
)

RESULT_PATH = "results/v0.4.2_721_inverse_relation_reduction_cpobc_msr.json"
SCHEMA = "final-theory-v042-721-inverse-relation-reduction-cpobc-msr-v1"
VERDICT = "V042_721_CPOBC_MSR_REDUCED_MODULO_DEFINING_RELATIONS_NO_NEWLY_ZERO_OPEN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reduce_records(
    records: Iterator[tuple[str, str, Expression]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    materialised = list(records)
    record_keys = [(a, b) for a, b, _ in materialised]
    if len(record_keys) != len(set(record_keys)):
        raise AssertionError("duplicate reduction-gate equation id")
    materialised.sort(key=lambda record: (record[0], record[1]))

    output: list[dict[str, Any]] = []
    newly_zero_count = 0
    still_nonzero_count = 0
    unexpectedly_nonzero_count = 0
    total_reduced_terms = 0
    maximum_reduced_terms = 0
    maximum_reduced_degree = 0
    term_distribution: Counter[int] = Counter()

    for first_id, second_id, residual in materialised:
        word_identity = not residual
        saturated_matrix = _matrix_expression_saturated(residual)
        saturated_stats = _matrix_stats(saturated_matrix)
        reduced_matrix = _reduce_matrix(saturated_matrix)
        reduced_stats = _matrix_stats(reduced_matrix)

        saturated_zero = saturated_stats["nonzero_entry_count"] == 0
        reduced_zero = reduced_stats["nonzero_entry_count"] == 0
        if word_identity != saturated_zero:
            raise AssertionError(f"saturated zero status regressed: {first_id}/{second_id}")
        if reduced_zero and not saturated_zero:
            status = "NEWLY_ZERO_UNDER_REDUCTION"
            newly_zero_count += 1
        elif not reduced_zero and saturated_zero:
            status = "UNEXPECTEDLY_NONZERO_UNDER_REDUCTION"
            unexpectedly_nonzero_count += 1
        elif reduced_zero:
            status = "ZERO_BOTH"
        else:
            status = "NONZERO_BOTH"
            still_nonzero_count += 1

        output.append(
            {
                "first_id": first_id,
                "second_id": second_id,
                "word_identity": word_identity,
                "saturated_scalar_zero": saturated_zero,
                "reduced_scalar_zero": reduced_zero,
                "status": status,
                "reduced_scalar_matrix": reduced_stats,
                "reduced_scalar_matrix_sha256": _scalar_matrix_digest(reduced_matrix),
                "word_sha256": _expression_digest(residual),
            }
        )
        term_distribution[reduced_stats["total_scalar_term_count"]] += 1
        total_reduced_terms += reduced_stats["total_scalar_term_count"]
        maximum_reduced_terms = max(
            maximum_reduced_terms, reduced_stats["maximum_scalar_term_count"]
        )
        maximum_reduced_degree = max(
            maximum_reduced_degree, reduced_stats["maximum_monomial_degree"]
        )

    if unexpectedly_nonzero_count:
        raise AssertionError(
            "reduction made a previously-zero residual nonzero: "
            f"{unexpectedly_nonzero_count} occurrences"
        )

    return output, {
        "equation_count": len(output),
        "newly_zero_under_reduction_count": newly_zero_count,
        "still_nonzero_under_reduction_count": still_nonzero_count,
        "total_reduced_scalar_term_count": total_reduced_terms,
        "maximum_reduced_scalar_term_count": maximum_reduced_terms,
        "maximum_reduced_monomial_degree": maximum_reduced_degree,
        "total_reduced_scalar_term_distribution": {
            str(key): value for key, value in sorted(term_distribution.items())
        },
        "record_digest_sha256": stable_hash(output),
    }


def _reduce_msr_records(
    records: Iterator[tuple[str, Expression]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return _reduce_records((cid, "", residual) for cid, residual in records)


def compile_inverse_relation_reduction_cpobc_msr_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cpobc = _load(root, CPOBC_PATH)
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    saturation_result = compile_inverse_saturation_v042(root)
    if not all(record["saturates"] for record in saturation_result["records"]):
        raise AssertionError("inverse tokens do not saturate; refusing to reduce")
    occurrence_expressions, _, generator_summary = _compile_occurrences(reduction)
    if generator_summary["eq112_tokens_present"]:
        raise AssertionError("Eq.(112) B tokens leaked into reduction gate")

    cpobc_records, cpobc_summary = _reduce_records(
        _cpobc_residuals(cpobc, occurrence_expressions)
    )
    msr_records, msr_summary = _reduce_msr_records(
        _msr_residuals(cpobc, occurrence_expressions)
    )
    if cpobc_summary["equation_count"] != 783:
        raise AssertionError("CPOBC equation count changed")
    if msr_summary["equation_count"] != 24:
        raise AssertionError("strong MSR equation count changed")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "method": (
                "exact monomial rewriting D*a*d -> 1+D*b*c per token, "
                "binomial-expanded for repeated occurrences; the 8 tokens' "
                "relation variables are pairwise disjoint, so this is "
                "confluent without a general Groebner computation"
            ),
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
            "CPOBC": "reduced modulo the 8 defining relations",
            "strong_MSR": "reduced modulo the 8 defining relations",
            "fixed_vector_GC": "not reduced here; a separate bounded gate",
        },
        "source_artifact_sha256": {
            relative: _sha256(root / relative)
            for relative in (CPOBC_PATH, REDUCTION_PATH, LOCAL_GC_PATH)
        },
        "compiler_source_sha256": _sha256(Path(__file__).resolve()),
        "input_native_ir_semantic_digest_sha256": source_result[
            "semantic_digest_sha256"
        ],
        "input_inverse_saturation_sha256": _sha256(root / SATURATION_RESULT_PATH),
        "input_resaturated_cpobc_msr_sha256": _sha256(
            root / RESATURATION_RESULT_PATH
        ),
        "CPOBC": {
            "summary": cpobc_summary,
            "records": cpobc_records,
        },
        "strong_MSR": {
            "summary": msr_summary,
            "records": msr_records,
        },
        "fixed_vector_GC": {
            "reduced": False,
            "same_endpoint_pair_count": len(local_gc["all_pair_derivations"]),
            "reason": "1,529-pair reduction is a separate bounded gate",
        },
        "overall": {
            "total_newly_zero_under_reduction": (
                cpobc_summary["newly_zero_under_reduction_count"]
                + msr_summary["newly_zero_under_reduction_count"]
            ),
            "total_still_nonzero_under_reduction": (
                cpobc_summary["still_nonzero_under_reduction_count"]
                + msr_summary["still_nonzero_under_reduction_count"]
            ),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 8,
            "explicit_relation_reduction_runs": (
                cpobc_summary["equation_count"] + msr_summary["equation_count"]
            ),
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "CPOBC and strong-MSR residuals were reduced modulo the 8 "
            "D_<token>*det(A)-1=0 defining relations, not merely "
            "substituted; no previously-zero residual became nonzero "
            "(checked, fails closed otherwise).",
            "The fixed-vector GC pair inventory is not reduced by this gate.",
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


def write_inverse_relation_reduction_cpobc_msr(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(
            compile_inverse_relation_reduction_cpobc_msr_v042(root),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_inverse_relation_reduction_cpobc_msr(Path(__file__).resolve().parents[3]))
