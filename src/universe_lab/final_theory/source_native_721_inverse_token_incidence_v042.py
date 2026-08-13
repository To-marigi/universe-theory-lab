"""Count how many of the 1,967 nonzero 721 residuals actually contain an
inverse token.

Direct substitution of the 8 saturated inverse tokens
(``source_native_721_inverse_resaturated_cpobc_msr_v042.py``,
``source_native_721_gc_tier_resaturated_v042.py``) closed none of the 1,967
previously scalar-nonzero CPOBC/strong-MSR/GC residuals. Before attempting
any heavier elimination combining the 8 ``D_<token>*det(A)-1=0`` defining
relations with the residual system, this gate answers a purely structural,
free-word-level question that bounds what any such elimination could ever
touch: of those 1,967 residuals, how many even contain an inverse token in
the first place?

A residual whose free-reduced word never mentions an inverse token cannot
be affected by any manipulation of the inverse-token relations at all --
substitution, elimination, or otherwise -- because there is nothing in the
residual for those relations to act on. This is not a search or a cost
estimate; it is a finite count over the free-word representation already
frozen by earlier gates, using no scalar expansion.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
    CPOBC_PATH,
    LOCAL_GC_PATH,
    REDUCTION_PATH,
    Expression,
    _add,
    _compile_occurrences,
    _expression_digest,
    _load,
    _scale,
    compile_source_native_721_v042,
)
from universe_lab.final_theory.source_native_721_gc_stage_v042 import _path_expression
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    _cpobc_residuals,
    _msr_residuals,
)

RESULT_PATH = "results/v0.4.2_721_inverse_token_incidence.json"
SCHEMA = "final-theory-v042-721-inverse-token-incidence-v1"
VERDICT = "V042_721_INVERSE_TOKEN_INCIDENCE_COUNTED_STRUCTURAL_ELIMINATION_CEILING_OPEN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _contains_inverse_token(residual: Expression) -> bool:
    return any(
        token.endswith("^-1")
        for word, coefficient in residual.items()
        if coefficient
        for token in word
    )


def _count_inventory(
    residuals: list[tuple[str, str, Expression]],
) -> dict[str, Any]:
    nonzero = [(a, b, r) for a, b, r in residuals if r]
    with_inverse = [(a, b, r) for a, b, r in nonzero if _contains_inverse_token(r)]
    without_inverse = [(a, b, r) for a, b, r in nonzero if not _contains_inverse_token(r)]
    return {
        "total_count": len(residuals),
        "nonzero_count": len(nonzero),
        "nonzero_containing_inverse_token_count": len(with_inverse),
        "nonzero_without_inverse_token_count": len(without_inverse),
        "structurally_unreachable_by_any_inverse_elimination": [
            {"first_id": a, "second_id": b, "word_sha256": _expression_digest(r)}
            for a, b, r in sorted(without_inverse)[:5]
        ],
    }


def compile_inverse_token_incidence_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cpobc = _load(root, CPOBC_PATH)
    reduction = _load(root, REDUCTION_PATH)
    local_gc = _load(root, LOCAL_GC_PATH)
    source_result = compile_source_native_721_v042(root)
    occurrence_expressions, by_signature, generator_summary = _compile_occurrences(
        reduction
    )
    if generator_summary["eq112_tokens_present"]:
        raise AssertionError("Eq.(112) B tokens leaked into incidence gate")

    cpobc_residuals = [
        (a, b, r) for a, b, r in _cpobc_residuals(cpobc, occurrence_expressions)
    ]
    if len(cpobc_residuals) != 783:
        raise AssertionError("CPOBC equation count changed")
    msr_residuals = [
        (cid, "", r) for cid, r in _msr_residuals(cpobc, occurrence_expressions)
    ]
    if len(msr_residuals) != 24:
        raise AssertionError("strong MSR equation count changed")

    all_paths = [
        path
        for stage_paths in local_gc["path_inventory"].values()
        for path in stage_paths
    ]
    if len(all_paths) != 407:
        raise AssertionError("GC path count changed")
    path_expressions = {
        path["path_id"]: _path_expression(path, by_signature) for path in all_paths
    }
    gc_pairs = local_gc["all_pair_derivations"]
    if len(gc_pairs) != 1529:
        raise AssertionError("GC pair count changed")
    gc_residuals = [
        (
            pair["endpoint_causet_id"],
            f"{pair['left_path_id']}|{pair['right_path_id']}",
            _add(
                path_expressions[pair["left_path_id"]],
                _scale(-1, path_expressions[pair["right_path_id"]]),
            ),
        )
        for pair in gc_pairs
    ]

    cpobc_counts = _count_inventory(cpobc_residuals)
    msr_counts = _count_inventory(msr_residuals)
    gc_counts = _count_inventory(gc_residuals)

    if cpobc_counts["nonzero_count"] != 700:
        raise AssertionError("CPOBC nonzero count disagrees with the scalar gate")
    if msr_counts["nonzero_count"] != 21:
        raise AssertionError("strong MSR nonzero count disagrees with the scalar gate")
    if gc_counts["nonzero_count"] != 1246:
        raise AssertionError("GC nonzero count disagrees with the resaturated tiers")

    total_nonzero = (
        cpobc_counts["nonzero_count"]
        + msr_counts["nonzero_count"]
        + gc_counts["nonzero_count"]
    )
    total_with_inverse = (
        cpobc_counts["nonzero_containing_inverse_token_count"]
        + msr_counts["nonzero_containing_inverse_token_count"]
        + gc_counts["nonzero_containing_inverse_token_count"]
    )
    total_without_inverse = total_nonzero - total_with_inverse

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "question": (
                "of the 1,967 previously scalar-nonzero residuals, how many "
                "even contain an inverse token, at the free-word level, "
                "before any scalar expansion"
            ),
            "why_this_bounds_elimination": (
                "a residual whose free-reduced word never mentions an "
                "inverse token cannot be affected by any manipulation of "
                "the 8 D_<token>*det(A)-1=0 relations, substitution or "
                "elimination alike -- there is nothing for those relations "
                "to act on"
            ),
            "method": "free-word token scan; no scalar expansion performed",
        },
        "source_artifact_sha256": {
            relative: _sha256(root / relative)
            for relative in (CPOBC_PATH, REDUCTION_PATH, LOCAL_GC_PATH)
        },
        "compiler_source_sha256": _sha256(Path(__file__).resolve()),
        "input_native_ir_semantic_digest_sha256": source_result[
            "semantic_digest_sha256"
        ],
        "CPOBC": cpobc_counts,
        "strong_MSR": msr_counts,
        "fixed_vector_GC": gc_counts,
        "overall": {
            "total_nonzero_residuals": total_nonzero,
            "containing_inverse_token": total_with_inverse,
            "structurally_unreachable_by_inverse_elimination": total_without_inverse,
            "elimination_ceiling_fraction_of_total": (
                f"{total_with_inverse}/{total_nonzero}"
            ),
        },
        "solver_status": {
            "generic_2x2_scalar_expansion": False,
            "inverse_saturation_runs": 8,
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "This is a finite free-word count, not a scalar computation and "
            "not a search; it establishes a hard ceiling on what any "
            "inverse-relation elimination could possibly touch.",
            "It does not itself decide whether an elimination over the "
            "reachable residuals would close them.",
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


def write_inverse_token_incidence(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(
            compile_inverse_token_incidence_v042(root), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_inverse_token_incidence(Path(__file__).resolve().parents[3]))
