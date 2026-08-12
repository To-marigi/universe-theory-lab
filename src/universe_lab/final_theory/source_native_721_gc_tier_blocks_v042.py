"""Scalar expansion for one GC endpoint-size tier, generalised.

The 1,529 same-endpoint GC pairs are split by endpoint. Endpoints with the
same path count form a "tier"; three-path and four-path tiers were compiled
by dedicated predecessor gates
(``source_native_721_gc_small_blocks_v042.py``,
``source_native_721_gc_four_path_blocks_v042.py``). This module generalises
the same procedure to an arbitrary path count so the remaining tiers can be
swept without a bespoke module per size.

Unlike the two predecessor gates, this module does not hardcode the expected
endpoint/pair counts for each tier. Instead it derives the expected pair
count structurally: an endpoint with ``k`` paths contributes exactly
``C(k,2)`` same-endpoint pairs, so the selected-pair count must equal
``selected_endpoint_count * k * (k-1) // 2``. A mismatch means the local GC
inventory is not what this gate assumes and it fails closed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
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
    _scale,
    compile_source_native_721_v042,
)
from universe_lab.final_theory.source_native_721_gc_stage_v042 import (
    RESULT_PATH as CALIBRATION_STAGE_RESULT_PATH,
)
from universe_lab.final_theory.source_native_721_gc_stage_v042 import (
    _path_expression,
    _scalar_matrix_digest,
)

RESULT_PATH_TEMPLATE = "results/v0.4.2_721_gc_tier{path_count:02d}_blocks.json"
SCHEMA_TEMPLATE = "final-theory-v042-721-gc-tier-{path_count:02d}-blocks-v1"
VERDICT_TEMPLATE = "V042_721_GC_TIER_{path_count:02d}_BLOCKS_SCALAR_COMPILED_OPEN"


def result_path(path_count: int) -> str:
    return RESULT_PATH_TEMPLATE.format(path_count=path_count)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compile_gc_tier_blocks(root: Path, path_count: int) -> dict[str, Any]:
    if path_count < 2:
        raise AssertionError("a tier below two paths contributes no pairs")
    root = root.resolve()
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    _, by_signature, _ = _compile_occurrences(reduction)

    all_paths = [
        path
        for stage_paths in local_gc["path_inventory"].values()
        for path in stage_paths
    ]
    all_path_ids = [path["path_id"] for path in all_paths]
    if len(all_path_ids) != len(set(all_path_ids)):
        raise AssertionError("duplicate local GC path id")
    all_pair_count = len(local_gc["all_pair_derivations"])
    if (len(all_paths), all_pair_count) != (407, 1529):
        raise AssertionError("global GC inventory count changed")

    paths_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in all_paths:
        paths_by_endpoint[path["endpoint_causet_id"]].append(path)
    selected_endpoints = sorted(
        endpoint
        for endpoint, paths in paths_by_endpoint.items()
        if len(paths) == path_count
    )
    if not selected_endpoints:
        raise AssertionError(f"no endpoint has exactly {path_count} paths")
    selected_paths = {
        path["path_id"]: path
        for endpoint in selected_endpoints
        for path in paths_by_endpoint[endpoint]
    }
    selected_path_ids = list(selected_paths)
    if len(selected_path_ids) != len(set(selected_path_ids)):
        raise AssertionError("duplicate selected GC path id")

    selected_pairs = sorted(
        [
            pair
            for pair in local_gc["all_pair_derivations"]
            if pair["endpoint_causet_id"] in selected_endpoints
        ],
        key=lambda pair: (
            pair["endpoint_causet_id"],
            pair["left_path_id"],
            pair["right_path_id"],
        ),
    )
    pair_ids = [
        (pair["endpoint_causet_id"], pair["left_path_id"], pair["right_path_id"])
        for pair in selected_pairs
    ]
    if len(pair_ids) != len(set(pair_ids)):
        raise AssertionError("duplicate selected GC pair")
    expected_pair_count = len(selected_endpoints) * path_count * (path_count - 1) // 2
    if len(selected_pairs) != expected_pair_count:
        raise AssertionError(
            "selected pair count does not match the C(k,2) star-pair structure"
        )

    selected_basis = [
        relation
        for relation in local_gc["generating_relation_basis"]
        if relation["endpoint_causet_id"] in selected_endpoints
    ]
    basis_ids = {relation["relation_id"] for relation in selected_basis}
    if len(basis_ids) != len(selected_basis):
        raise AssertionError("duplicate selected basis relation id")

    path_expressions = {
        path_id: _path_expression(path, by_signature)
        for path_id, path in selected_paths.items()
    }
    path_records = [
        {
            "endpoint_causet_id": path["endpoint_causet_id"],
            "path_id": path_id,
            "path_length": int(path["path_length"]),
            "word_term_count": len(path_expressions[path_id]),
            "word_sha256": _expression_digest(path_expressions[path_id]),
        }
        for path_id, path in sorted(
            selected_paths.items(),
            key=lambda item: (item[1]["endpoint_causet_id"], item[0]),
        )
    ]

    records: list[dict[str, Any]] = []
    per_endpoint: dict[str, dict[str, Any]] = {
        endpoint: {
            "path_count": len(paths_by_endpoint[endpoint]),
            "pair_count": 0,
            "basis_relation_count": sum(
                relation["endpoint_causet_id"] == endpoint
                for relation in selected_basis
            ),
            "word_identity_count": 0,
            "scalar_zero_matrix_count": 0,
            "total_scalar_term_count": 0,
            "maximum_scalar_term_count": 0,
            "maximum_monomial_degree": 0,
        }
        for endpoint in selected_endpoints
    }
    for pair in selected_pairs:
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
        endpoint = pair["endpoint_causet_id"]
        summary = per_endpoint[endpoint]
        summary["pair_count"] += 1
        summary["word_identity_count"] += word_identity
        summary["scalar_zero_matrix_count"] += scalar_zero
        summary["total_scalar_term_count"] += stats["total_scalar_term_count"]
        summary["maximum_scalar_term_count"] = max(
            summary["maximum_scalar_term_count"],
            stats["maximum_scalar_term_count"],
        )
        summary["maximum_monomial_degree"] = max(
            summary["maximum_monomial_degree"],
            stats["maximum_monomial_degree"],
        )
        records.append(
            {
                "endpoint_causet_id": endpoint,
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

    term_distribution = Counter(
        record["scalar_matrix"]["total_scalar_term_count"] for record in records
    )
    total_scalar_terms = sum(term * count for term, count in term_distribution.items())
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_TEMPLATE.format(path_count=path_count),
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "selected_endpoint_rule": f"exactly {path_count} paths",
            "selected_endpoint_count": len(selected_endpoints),
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
            "path_product_convention": "later_transition_multiplies_on_left",
            "inverse_saturation": "not imposed; inverse tokens remain separate variables",
            "basis_strategy": "endpoint-wise star basis retained; all selected pairs checked",
            "pair_count_structural_check": (
                "selected_pairs == selected_endpoints * C(path_count, 2)"
            ),
        },
        "selected_endpoints": selected_endpoints,
        "source_artifact_sha256": {
            relative: _sha256(root / relative)
            for relative in (REDUCTION_PATH, LOCAL_GC_PATH)
        },
        "compiler_source_sha256": _sha256(Path(__file__).resolve()),
        "input_native_ir_semantic_digest_sha256": source_result[
            "semantic_digest_sha256"
        ],
        "input_calibration_stage_sha256": _sha256(
            root / CALIBRATION_STAGE_RESULT_PATH
        ),
        "paths": {
            "count": len(path_records),
            "records": path_records,
        },
        "basis": {
            "relation_count": len(selected_basis),
            "all_have_selected_endpoint": all(
                relation["endpoint_causet_id"] in selected_endpoints
                for relation in selected_basis
            ),
        },
        "pairs": {
            "count": len(records),
            "word_identity_count": sum(record["word_identity"] for record in records),
            "scalar_zero_matrix_count": sum(
                record["scalar_matrix"]["nonzero_entry_count"] == 0
                for record in records
            ),
            "nonzero_scalar_entry_count": sum(
                record["scalar_matrix"]["nonzero_entry_count"] for record in records
            ),
            "total_scalar_term_count": total_scalar_terms,
            "maximum_scalar_term_count": max(
                record["scalar_matrix"]["maximum_scalar_term_count"]
                for record in records
            ),
            "maximum_monomial_degree": max(
                record["scalar_matrix"]["maximum_monomial_degree"]
                for record in records
            ),
            "total_scalar_term_distribution": {
                str(key): value for key, value in sorted(term_distribution.items())
            },
            "record_digest_sha256": stable_hash(records),
        },
        "per_endpoint": per_endpoint,
        "global_gc_boundary": {
            "all_inventory_path_count": len(all_paths),
            "all_inventory_pair_count": all_pair_count,
            "expanded_here": len(records),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 0,
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            f"Only the endpoint blocks with exactly {path_count} paths are "
            "scalar-expanded.",
            "Path matrices are cached once per selected path before pair differences.",
            "GC pairs outside this tier are not inferred from this result.",
            "No full 721 commutativity theorem, witness, or obstruction is issued.",
        ],
        "unrestricted_721_status": "OPEN",
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT_TEMPLATE.format(path_count=path_count),
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def write_gc_tier_blocks(root: Path, path_count: int) -> Path:
    path = root / result_path(path_count)
    path.write_text(
        json.dumps(
            compile_gc_tier_blocks(root, path_count), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    import sys

    write_gc_tier_blocks(Path(__file__).resolve().parents[3], int(sys.argv[1]))
