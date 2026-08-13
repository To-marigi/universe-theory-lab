"""Bounded probe: reduce a small residual sample modulo the 8 defining relations.

Direct substitution of the saturated inverse tokens
(``source_native_721_inverse_resaturated_cpobc_msr_v042.py``,
``source_native_721_gc_tier_resaturated_v042.py``) closed none of the 1,967
previously scalar-nonzero residuals. That only ever *substituted* each
inverse token's matrix; it never *used* the 8 defining relations
``D_<token> * det(A_<token>) - 1 = 0`` to simplify anything.

This module implements that missing step exactly, with no external solver:
each defining relation rewrites ``D * a * d`` (the token's ``D`` times the
two diagonal entries of its base matrix) to ``1 + D * b * c`` wherever that
exact product of three distinct variables occurs as a factor of a monomial,
repeated for every independent occurrence in a monomial (binomial
expansion of ``(1 + D*b*c)^n``). Because the 8 tokens' variable sets
(``D``, ``a``, ``b``, ``c``, ``d`` for one base generator each) are
pairwise disjoint, applying the 8 relations in any order is confluent: no
relation's rewrite can ever reintroduce a pattern another relation (or
itself) still needs to consume. This is a genuine, terminating reduction
modulo an ideal with an obvious Groebner basis (the 8 relations themselves,
on disjoint variables) -- not a general Buchberger computation, and not a
CAS/solver run.

This is a bounded probe, not the full 1,967-residual sweep: it measures
correctness and real per-residual cost on a small, explicit sample before
any commitment to scale it up.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from math import comb
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
    CPOBC_PATH,
    LOCAL_GC_PATH,
    REDUCTION_PATH,
    Scalar,
    ScalarMatrix,
    _add,
    _compile_occurrences,
    _load,
    _matrix_stats,
    _scale,
    _token_name,
    compile_source_native_721_v042,
)
from universe_lab.final_theory.source_native_721_gc_stage_v042 import _path_expression
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
    _scalar_matrix_digest,
)

RESULT_PATH = "results/v0.4.2_721_inverse_relation_reduction_probe.json"
SCHEMA = "final-theory-v042-721-inverse-relation-reduction-probe-v1"
VERDICT = "V042_721_INVERSE_RELATION_REDUCTION_PROBE_BOUNDED_SAMPLE_OPEN"

INVERSE_BASE_TOKENS = (
    "G_p2-2",
    "G_p3-002",
    "G_p3-006",
    "G_p3-024",
    "G_p3-026",
    "Q_1",
    "Q_2",
    "Q_3",
)

# Sample size for this bounded probe, chosen before looking at any timing.
CPOBC_SAMPLE_SIZE = 12
GC_SAMPLE_SIZE = 12


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _token_relation_variables(base_token: str) -> tuple[str, str, str, str, str]:
    name = _token_name(base_token)
    return (
        f"D_{name}",
        f"M_{name}_00",
        f"M_{name}_01",
        f"M_{name}_10",
        f"M_{name}_11",
    )


RELATIONS = [_token_relation_variables(token) for token in INVERSE_BASE_TOKENS]


def _reduce_monomial(
    monomial: tuple[str, ...], relation: tuple[str, str, str, str, str]
) -> dict[tuple[str, ...], int]:
    det_variable, a, b, c, d = relation
    counts = Counter(monomial)
    n = min(counts[det_variable], counts[a], counts[d])
    if n == 0:
        return {monomial: 1}
    remaining = Counter(monomial)
    remaining[det_variable] -= n
    remaining[a] -= n
    remaining[d] -= n
    base = tuple(
        variable for variable, count in remaining.items() for _ in range(count)
    )
    result: dict[tuple[str, ...], int] = {}
    for k in range(n + 1):
        coefficient = comb(n, k)
        extra = (det_variable, b, c) * k
        new_monomial = tuple(sorted(base + extra))
        result[new_monomial] = result.get(new_monomial, 0) + coefficient
    return result


def _reduce_scalar(value: Scalar, relations: list[tuple[str, str, str, str, str]]) -> Scalar:
    current: Scalar = dict(value)
    for relation in relations:
        next_value: Scalar = {}
        for monomial, coefficient in current.items():
            for new_monomial, multiplier in _reduce_monomial(monomial, relation).items():
                next_value[new_monomial] = (
                    next_value.get(new_monomial, 0) + coefficient * multiplier
                )
        current = {
            monomial: coefficient
            for monomial, coefficient in next_value.items()
            if coefficient
        }
    return current


def _reduce_matrix(matrix: ScalarMatrix) -> ScalarMatrix:
    return tuple(
        tuple(_reduce_scalar(matrix[row][col], RELATIONS) for col in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _probe_one(
    identifier: str, residual: dict[tuple[str, ...], int]
) -> dict[str, Any]:
    saturated_matrix = _matrix_expression_saturated(residual)
    saturated_stats = _matrix_stats(saturated_matrix)
    start = time.time()
    reduced_matrix = _reduce_matrix(saturated_matrix)
    elapsed = time.time() - start
    reduced_stats = _matrix_stats(reduced_matrix)
    newly_zero = (
        saturated_stats["nonzero_entry_count"] > 0
        and reduced_stats["nonzero_entry_count"] == 0
    )
    return {
        "id": identifier,
        "saturated_scalar_matrix": saturated_stats,
        "reduced_scalar_matrix": reduced_stats,
        "reduced_scalar_matrix_sha256": _scalar_matrix_digest(reduced_matrix),
        "newly_zero_under_reduction": newly_zero,
        "reduction_seconds": elapsed,
    }


def compile_inverse_relation_reduction_probe_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cpobc = _load(root, CPOBC_PATH)
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    saturation_result = compile_inverse_saturation_v042(root)
    if not all(record["saturates"] for record in saturation_result["records"]):
        raise AssertionError("inverse tokens do not saturate; refusing to probe")
    occurrence_expressions, by_signature, _ = _compile_occurrences(reduction)

    # A tiny hand-checkable sanity case before touching real residuals: a
    # monomial equal to exactly one relation's own left-hand side must
    # reduce so that its constant term is exactly 1 (the defining relation
    # says D*a*d = 1 + D*b*c, so reducing D*a*d alone must yield {(): 1,
    # (D,b,c): 1}).
    det_variable, a, b, c, d = RELATIONS[0]
    sanity_input: Scalar = {tuple(sorted((det_variable, a, d))): 1}
    sanity_output = _reduce_scalar(sanity_input, RELATIONS)
    expected_sanity = {(): 1, tuple(sorted((det_variable, b, c))): 1}
    if sanity_output != expected_sanity:
        raise AssertionError(
            f"reduction sanity check failed: {sanity_output} != {expected_sanity}"
        )

    cpobc_sample_source = [
        (f"{relation_id}/{equation_id}", residual)
        for relation_id, equation_id, residual in _cpobc_residuals(
            cpobc, occurrence_expressions
        )
        if residual
    ][:CPOBC_SAMPLE_SIZE]

    all_paths = [
        path
        for stage_paths in local_gc["path_inventory"].values()
        for path in stage_paths
    ]
    path_expressions = {
        path["path_id"]: _path_expression(path, by_signature) for path in all_paths
    }
    gc_sample_source: list[tuple[str, dict[tuple[str, ...], int]]] = []
    for pair in local_gc["all_pair_derivations"]:
        residual = _add(
            path_expressions[pair["left_path_id"]],
            _scale(-1, path_expressions[pair["right_path_id"]]),
        )
        if residual:
            gc_sample_source.append(
                (
                    f"{pair['endpoint_causet_id']}/{pair['left_path_id']}|"
                    f"{pair['right_path_id']}",
                    residual,
                )
            )
        if len(gc_sample_source) >= GC_SAMPLE_SIZE:
            break

    cpobc_records = [
        _probe_one(identifier, residual) for identifier, residual in cpobc_sample_source
    ]
    gc_records = [
        _probe_one(identifier, residual) for identifier, residual in gc_sample_source
    ]
    all_records = cpobc_records + gc_records

    total_reduction_seconds = sum(record["reduction_seconds"] for record in all_records)
    newly_zero_count = sum(record["newly_zero_under_reduction"] for record in all_records)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "purpose": (
                "measure real, per-residual cost of reducing modulo the 8 "
                "D_<token>*det(A)-1=0 defining relations, on a small "
                "explicit sample, before deciding whether to run it over "
                "the full 1,961-residual inventory"
            ),
            "method": (
                "exact monomial rewriting D*a*d -> 1 + D*b*c per token, "
                "binomial-expanded for repeated occurrences; the 8 tokens' "
                "relation variables are pairwise disjoint so this is "
                "confluent without needing a general Groebner computation"
            ),
            "cpobc_sample_size": len(cpobc_records),
            "gc_sample_size": len(gc_records),
            "sanity_check": "D*a*d reduces to {1, D*b*c} exactly, verified before sampling",
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
        "CPOBC_sample": cpobc_records,
        "GC_sample": gc_records,
        "measurement": {
            "total_reduction_seconds": total_reduction_seconds,
            "mean_reduction_seconds_per_residual": (
                total_reduction_seconds / len(all_records) if all_records else 0.0
            ),
            "maximum_reduction_seconds_single_residual": max(
                (record["reduction_seconds"] for record in all_records), default=0.0
            ),
            "newly_zero_under_reduction_count": newly_zero_count,
            "sample_size": len(all_records),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 8,
            "explicit_relation_reduction_runs": len(all_records),
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "This is a bounded sample (12 CPOBC + 12 GC residuals), not the "
            "full 1,961-residual inventory.",
            "The measured per-residual time is the basis for deciding "
            "whether a full sweep is feasible, not itself a full result.",
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


def write_inverse_relation_reduction_probe(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(
            compile_inverse_relation_reduction_probe_v042(root),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_inverse_relation_reduction_probe(Path(__file__).resolve().parents[3]))
