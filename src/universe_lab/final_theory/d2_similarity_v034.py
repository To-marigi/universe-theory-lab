"""Conservative exact similarity signatures for fixed 2 by 2 candidates.

The classification theory is literature-locked.  This module uses standard
trace/determinant word invariants as filters and never treats a signature
collision as a proof of conjugacy in a non-semisimple case.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import sympy as sp

from universe_lab.final_theory.d2_rational_dag_v034 import (
    BRANCH,
    SOURCE_COMMIT,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SIMILARITY_SOURCE = "arXiv:0809.3032"
TRACE_SOURCE = "arXiv:math/0603049"


def _exact_string(expression: sp.Expr) -> str:
    return sp.sstr(sp.cancel(expression), order="lex")


def simultaneous_similarity_signature(
    matrices: Iterable[sp.Matrix],
) -> dict[str, Any]:
    """Return exact single, pair-word, and triple-word invariants."""

    items = tuple(matrices)
    if any(matrix.shape != (2, 2) for matrix in items):
        raise ValueError("similarity signatures require 2 by 2 matrices")
    singles = [
        {
            "index": index,
            "trace": _exact_string(matrix.trace()),
            "determinant": _exact_string(matrix.det()),
        }
        for index, matrix in enumerate(items)
    ]
    pairs = [
        {
            "word": [left, right],
            "trace": _exact_string((items[left] * items[right]).trace()),
        }
        for left in range(len(items))
        for right in range(len(items))
    ]
    triples = [
        {
            "word": [first, second, third],
            "trace": _exact_string(
                (items[first] * items[second] * items[third]).trace()
            ),
        }
        for first in range(len(items))
        for second in range(len(items))
        for third in range(len(items))
    ]
    payload = {
        "matrix_count": len(items),
        "single_matrix_invariants": singles,
        "pair_word_traces": pairs,
        "triple_word_traces": triples,
    }
    payload["signature_sha256"] = stable_hash(payload)
    return payload


def verify_explicit_conjugator(
    left: Iterable[sp.Matrix],
    right: Iterable[sp.Matrix],
    conjugator: sp.Matrix,
) -> dict[str, Any]:
    """Verify P^-1 X_i P=Y_i exactly, including det(P) != 0."""

    left_items = tuple(left)
    right_items = tuple(right)
    if len(left_items) != len(right_items):
        return {
            "passed": False,
            "reason": "TUPLE_LENGTH_MISMATCH",
            "residuals": [],
        }
    determinant = sp.factor(conjugator.det())
    if determinant == 0:
        return {
            "passed": False,
            "reason": "SINGULAR_CONJUGATOR",
            "determinant": "0",
            "residuals": [],
        }
    residuals = []
    inverse = conjugator.inv()
    passed = True
    for index, (left_matrix, right_matrix) in enumerate(
        zip(left_items, right_items, strict=True)
    ):
        residual = (inverse * left_matrix * conjugator - right_matrix).applyfunc(
            sp.cancel
        )
        zero = residual == sp.zeros(2)
        passed &= zero
        residuals.append(
            {
                "index": index,
                "residual": [
                    [_exact_string(residual[row, column]) for column in range(2)]
                    for row in range(2)
                ],
                "zero": zero,
            }
        )
    return {
        "passed": passed,
        "reason": "EXPLICIT_CONJUGATOR_VERIFIED" if passed else "NONZERO_RESIDUAL",
        "determinant": _exact_string(determinant),
        "residuals": residuals,
    }


def candidate_similarity_decision(
    left: Iterable[sp.Matrix],
    right: Iterable[sp.Matrix],
    *,
    conjugator: sp.Matrix | None = None,
) -> dict[str, Any]:
    """Make only decisions justified by exact equality or an exact conjugator."""

    left_items = tuple(left)
    right_items = tuple(right)
    left_signature = simultaneous_similarity_signature(left_items)
    right_signature = simultaneous_similarity_signature(right_items)
    if len(left_items) == len(right_items) and all(
        left_matrix == right_matrix
        for left_matrix, right_matrix in zip(
            left_items,
            right_items,
            strict=True,
        )
    ):
        return {
            "decision": "SIMILAR_IDENTICAL_TUPLE",
            "similar": True,
            "signature_match": True,
            "proof": "identity conjugator",
        }
    signature_match = (
        left_signature["signature_sha256"]
        == right_signature["signature_sha256"]
    )
    if conjugator is not None:
        verification = verify_explicit_conjugator(
            left_items,
            right_items,
            conjugator,
        )
        return {
            "decision": (
                "SIMILAR_EXPLICIT_CONJUGATOR"
                if verification["passed"]
                else "NOT_SIMILAR_UNDER_PROPOSED_CONJUGATOR"
            ),
            "similar": True if verification["passed"] else None,
            "signature_match": signature_match,
            "verification": verification,
        }
    if not signature_match:
        return {
            "decision": "NOT_SIMILAR_INVARIANT_MISMATCH",
            "similar": False,
            "signature_match": False,
        }
    return {
        "decision": "SIGNATURE_COLLISION_REQUIRES_CANONICAL_FORM_OR_CONJUGATOR",
        "similar": None,
        "signature_match": True,
        "reason": (
            "trace-word signatures alone are not promoted to a complete "
            "non-semisimple similarity test"
        ),
    }


def similarity_policy_v034() -> dict[str, Any]:
    return {
        "schema_version": "final-theory-d2-similarity-policy-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "dimension": 2,
        "literature_classification": "LITERATURE_LOCKED",
        "sources": [SIMILARITY_SOURCE, TRACE_SOURCE],
        "invariants_used": [
            "trace",
            "determinant",
            "ordered pair-word traces",
            "ordered triple-word traces",
        ],
        "deduplication_rules": [
            "invariant mismatch proves non-similarity",
            "identical tuples are duplicates",
            "an exact nonsingular conjugator proves similarity",
            (
                "a signature collision alone does not prove similarity in "
                "non-semisimple cases"
            ),
        ],
        "new_general_similarity_theorem_claimed": False,
        "verdict": "D2_SIMILARITY_DEDUPLICATION_POLICY_CONSERVATIVE",
    }
