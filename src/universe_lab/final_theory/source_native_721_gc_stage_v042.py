"""Stage-limited scalar expansion for one 721 fixed-vector GC endpoint.

This module deliberately expands only the smallest nontrivial endpoint block,
``p3-002`` (three paths and three same-endpoint pairs).  It is a calibration
gate for the larger GC inventory, not a claim about all 1,529 pairs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
    LOCAL_GC_PATH,
    REDUCTION_PATH,
    _add,
    _compile_occurrences,
    _expression_digest,
    _load,
    _matrix_expression,
    _matrix_stats,
    _multiply,
    _scale,
    compile_source_native_721_v042,
)
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    RESULT_PATH as SCALAR_GATE_RESULT_PATH,
)
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    _scalar_matrix_digest,
)

RESULT_PATH = "results/v0.4.2_721_gc_stage_p3-002.json"
SCHEMA = "final-theory-v042-721-gc-stage-p3-002-v1"
VERDICT = "V042_721_GC_STAGE_P3_002_SCALAR_COMPILED_OPEN"
TARGET_ENDPOINT = "p3-002"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_expression(
    path: dict[str, Any],
    by_signature: dict[tuple[int, int, int], dict[tuple[str, ...], int]],
) -> dict[tuple[str, ...], int]:
    product: dict[tuple[str, ...], int] = {(): 1}
    for transition in path["transitions"]:
        signature = transition["quotient_signature"]
        key = (
            int(signature["stage"]),
            int(signature["source_relation_code"]),
            int(signature["precursor_code"]),
        )
        # Later transitions act on the left, as frozen by the native IR gate.
        product = _multiply(by_signature[key], product)
    return product


def compile_gc_stage_p3_002(root: Path) -> dict[str, Any]:
    root = root.resolve()
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    occurrence_expressions, by_signature, _ = _compile_occurrences(reduction)
    del occurrence_expressions

    matching_paths = [
        path
        for stage_paths in local_gc["path_inventory"].values()
        for path in stage_paths
        if path["endpoint_causet_id"] == TARGET_ENDPOINT
    ]
    path_ids = [path["path_id"] for path in matching_paths]
    if len(path_ids) != len(set(path_ids)):
        raise AssertionError("duplicate calibration endpoint path id")
    paths = {path["path_id"]: path for path in matching_paths}
    if len(paths) != 3:
        raise AssertionError("the calibration endpoint path count changed")
    pair_records = sorted(
        [
            record
            for record in local_gc["all_pair_derivations"]
            if record["endpoint_causet_id"] == TARGET_ENDPOINT
        ],
        key=lambda record: (record["left_path_id"], record["right_path_id"]),
    )
    pair_ids = [
        (record["left_path_id"], record["right_path_id"])
        for record in pair_records
    ]
    if len(pair_ids) != len(set(pair_ids)):
        raise AssertionError("duplicate calibration endpoint pair")
    if len(pair_records) != 3:
        raise AssertionError("the calibration endpoint pair count changed")

    all_path_count = sum(
        len(stage_paths) for stage_paths in local_gc["path_inventory"].values()
    )
    all_pair_count = len(local_gc["all_pair_derivations"])
    if (all_path_count, all_pair_count) != (407, 1529):
        raise AssertionError("global GC inventory count changed")

    path_expressions = {
        path_id: _path_expression(path, by_signature)
        for path_id, path in paths.items()
    }
    path_records = []
    for path_id, path in sorted(paths.items()):
        expression = path_expressions[path_id]
        path_records.append(
            {
                "path_id": path_id,
                "path_length": int(path["path_length"]),
                "word_term_count": len(expression),
                "word_sha256": _expression_digest(expression),
            }
        )

    records = []
    word_identity_count = 0
    scalar_zero_count = 0
    total_scalar_terms = 0
    nonzero_scalar_entries = 0
    maximum_scalar_terms = 0
    maximum_monomial_degree = 0
    for pair in pair_records:
        residual = _add(
            path_expressions[pair["left_path_id"]],
            _scale(-1, path_expressions[pair["right_path_id"]]),
        )
        matrix = _matrix_expression(residual)
        stats = _matrix_stats(matrix)
        word_identity = not residual
        scalar_zero = stats["nonzero_entry_count"] == 0
        if word_identity != scalar_zero:
            raise AssertionError("GC scalar zero status disagrees with word status")
        word_identity_count += word_identity
        scalar_zero_count += scalar_zero
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
        records.append(
            {
                "endpoint_causet_id": TARGET_ENDPOINT,
                "left_path_id": pair["left_path_id"],
                "right_path_id": pair["right_path_id"],
                "basis_chain": pair["basis_chain"],
                "word_term_count": len(residual),
                "word_identity": word_identity,
                "word_sha256": _expression_digest(residual),
                "scalar_matrix": stats,
                "scalar_matrix_sha256": _scalar_matrix_digest(matrix),
            }
        )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "endpoint": TARGET_ENDPOINT,
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
            "path_product_convention": "later_transition_multiplies_on_left",
            "inverse_saturation": "not imposed; inverse tokens remain separate variables",
            "coverage": "one smallest nontrivial endpoint block only",
        },
        "source_artifact_sha256": {
            relative: _sha256(root / relative)
            for relative in (REDUCTION_PATH, LOCAL_GC_PATH)
        },
        "compiler_source_sha256": _sha256(Path(__file__).resolve()),
        "input_native_ir_semantic_digest_sha256": source_result[
            "semantic_digest_sha256"
        ],
        "input_scalar_gate_sha256": _sha256(root / SCALAR_GATE_RESULT_PATH),
        "paths": {
            "count": len(path_records),
            "records": path_records,
        },
        "pairs": {
            "count": len(records),
            "word_identity_count": word_identity_count,
            "scalar_zero_matrix_count": scalar_zero_count,
            "scalar_nonzero_matrix_count": len(records) - scalar_zero_count,
            "nonzero_scalar_entry_count": nonzero_scalar_entries,
            "total_scalar_term_count": total_scalar_terms,
            "maximum_scalar_term_count": maximum_scalar_terms,
            "maximum_monomial_degree": maximum_monomial_degree,
            "records": records,
            "record_digest_sha256": stable_hash(records),
        },
        "global_gc_boundary": {
            "all_inventory_path_count": all_path_count,
            "all_inventory_pair_count": all_pair_count,
            "expanded_here": "3 pairs only",
            "remaining_pair_count": all_pair_count - len(records),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 0,
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "Only endpoint p3-002 is scalar-expanded.",
            "The 1,526 unexpanded GC pairs are not inferred from this block.",
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


def write_gc_stage_p3_002(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_gc_stage_p3_002(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_gc_stage_p3_002(Path(__file__).resolve().parents[3]))
