"""Reduce one GC endpoint-size tier modulo the 8 defining relations.

Generalises ``source_native_721_inverse_relation_reduction_cpobc_msr_v042.py``'s
exact reduction (``D*a*d -> 1+D*b*c`` per token, binomial-expanded,
confluent because the 8 tokens' relation variables are pairwise disjoint)
to an arbitrary GC endpoint-size tier, mirroring
``source_native_721_gc_tier_resaturated_v042.py``'s structural self-check
(selected pairs must equal ``endpoints * C(k,2)``).

For each same-endpoint pair this reduces the saturated scalar matrix
modulo the 8 relations and records whether that newly closes a previously
scalar-nonzero pair. Fails closed if reduction ever makes a previously-zero
pair nonzero.
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
from universe_lab.final_theory.source_native_721_inverse_relation_reduction_probe_v042 import (
    _reduce_matrix,
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

RESULT_PATH_TEMPLATE = "results/v0.4.2_721_gc_tier{path_count:02d}_relation_reduced.json"
SCHEMA_TEMPLATE = "final-theory-v042-721-gc-tier-{path_count:02d}-relation-reduced-v1"
VERDICT_TEMPLATE = (
    "V042_721_GC_TIER_{path_count:02d}_RELATION_REDUCED_NO_NEWLY_ZERO_PAIR_OPEN"
)


def result_path(path_count: int) -> str:
    return RESULT_PATH_TEMPLATE.format(path_count=path_count)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compile_gc_tier_relation_reduced(root: Path, path_count: int) -> dict[str, Any]:
    if path_count < 2:
        raise AssertionError("a tier below two paths contributes no pairs")
    root = root.resolve()
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    saturation_result = compile_inverse_saturation_v042(root)
    if not all(record["saturates"] for record in saturation_result["records"]):
        raise AssertionError("inverse tokens do not saturate; refusing to reduce")
    _, by_signature, _ = _compile_occurrences(reduction)

    all_paths = [
        path
        for stage_paths in local_gc["path_inventory"].values()
        for path in stage_paths
    ]
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
    expected_pair_count = len(selected_endpoints) * path_count * (path_count - 1) // 2
    if len(selected_pairs) != expected_pair_count:
        raise AssertionError(
            "selected pair count does not match the C(k,2) star-pair structure"
        )

    path_expressions = {
        path_id: _path_expression(path, by_signature)
        for path_id, path in selected_paths.items()
    }

    records: list[dict[str, Any]] = []
    newly_zero_count = 0
    still_nonzero_count = 0
    unexpectedly_nonzero_count = 0
    term_distribution: Counter[int] = Counter()
    total_reduced_terms = 0
    maximum_reduced_terms = 0
    maximum_reduced_degree = 0

    for pair in selected_pairs:
        residual = _add(
            path_expressions[pair["left_path_id"]],
            _scale(-1, path_expressions[pair["right_path_id"]]),
        )
        word_identity = not residual
        saturated_matrix = _matrix_expression_saturated(residual)
        saturated_stats = _matrix_stats(saturated_matrix)
        reduced_matrix = _reduce_matrix(saturated_matrix)
        reduced_stats = _matrix_stats(reduced_matrix)

        saturated_zero = saturated_stats["nonzero_entry_count"] == 0
        reduced_zero = reduced_stats["nonzero_entry_count"] == 0
        if word_identity != saturated_zero:
            raise AssertionError("GC saturated zero status disagrees with word status")
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

        term_distribution[reduced_stats["total_scalar_term_count"]] += 1
        total_reduced_terms += reduced_stats["total_scalar_term_count"]
        maximum_reduced_terms = max(
            maximum_reduced_terms, reduced_stats["maximum_scalar_term_count"]
        )
        maximum_reduced_degree = max(
            maximum_reduced_degree, reduced_stats["maximum_monomial_degree"]
        )
        records.append(
            {
                "endpoint_causet_id": pair["endpoint_causet_id"],
                "left_path_id": pair["left_path_id"],
                "right_path_id": pair["right_path_id"],
                "word_identity": word_identity,
                "saturated_scalar_zero": saturated_zero,
                "reduced_scalar_zero": reduced_zero,
                "status": status,
                "reduced_scalar_matrix": reduced_stats,
                "reduced_scalar_matrix_sha256": _scalar_matrix_digest(reduced_matrix),
                "word_sha256": _expression_digest(residual),
            }
        )

    if unexpectedly_nonzero_count:
        raise AssertionError(
            "reduction made a previously-zero GC pair nonzero: "
            f"{unexpectedly_nonzero_count} occurrences in tier {path_count}"
        )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_TEMPLATE.format(path_count=path_count),
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "selected_endpoint_rule": f"exactly {path_count} paths",
            "selected_endpoint_count": len(selected_endpoints),
            "method": "D*a*d -> 1+D*b*c per token, confluent on disjoint token variables",
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
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
        "input_inverse_saturation_sha256": _sha256(root / SATURATION_RESULT_PATH),
        "pairs": {
            "count": len(records),
            "newly_zero_under_reduction_count": newly_zero_count,
            "still_nonzero_under_reduction_count": still_nonzero_count,
            "total_reduced_scalar_term_count": total_reduced_terms,
            "maximum_reduced_scalar_term_count": maximum_reduced_terms,
            "maximum_reduced_monomial_degree": maximum_reduced_degree,
            "total_reduced_scalar_term_distribution": {
                str(key): value for key, value in sorted(term_distribution.items())
            },
            "record_digest_sha256": stable_hash(records),
        },
        "global_gc_boundary": {
            "all_inventory_path_count": len(all_paths),
            "all_inventory_pair_count": all_pair_count,
            "reduced_here": len(records),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 8,
            "explicit_relation_reduction_runs": len(records),
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            f"Only the endpoint blocks with exactly {path_count} paths are "
            "reduced here.",
            "No previously-zero pair became nonzero under reduction "
            "(checked, fails closed otherwise).",
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


def write_gc_tier_relation_reduced(root: Path, path_count: int) -> Path:
    path = root / result_path(path_count)
    path.write_text(
        json.dumps(
            compile_gc_tier_relation_reduced(root, path_count),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    import sys

    write_gc_tier_relation_reduced(Path(__file__).resolve().parents[3], int(sys.argv[1]))
