"""Saturate the eight 721 inverse tokens against their forward matrices.

Every prior 721 gate left the eight inverse tokens (``G_p2-2^-1``,
``G_p3-002^-1``, ``G_p3-006^-1``, ``G_p3-024^-1``, ``G_p3-026^-1``,
``Q_1^-1``, ``Q_2^-1``, ``Q_3^-1``) as scalar-independent matrix variables:
nothing tied ``M_<token>_INV_ij`` to ``M_<token>_ij``. This gate closes that
gap for a generic invertible 2x2 matrix ``A = [[a,b],[c,d]]`` using the
standard closed form ``A^-1 = (1/det A) * [[d,-b],[-c,a]]``:

- one fresh scalar variable ``D_<token>`` per inverse token, standing for
  ``1/det(A)``;
- the defining relation ``D_<token> * det(A) - 1 = 0`` (not asserted zero;
  this *is* the saturation relation each token must satisfy);
- the inverse matrix entries defined directly from ``a,b,c,d`` and
  ``D_<token>``, replacing the previously free ``M_<token>_INV_ij``
  variables.

What this gate proves, exactly and symbolically: with the inverse matrix
built this way, every off-diagonal entry of ``A * A^-1`` and ``A^-1 * A``
is the exact zero polynomial (no relation needed -- pure cancellation), and
every diagonal entry equals ``D_<token> * det(A)`` exactly as a raw
polynomial (so it reduces to 1 using nothing but the defining relation
itself). That is the finite content of "the two-sided inverse identity
holds" for a generic invertible matrix; it is linear algebra, not a search.

This gate does not yet substitute these definitions back into the already
compiled CPOBC/strong-MSR/GC scalar residuals from the earlier gates -- that
re-substitution, and whatever it does or does not close, is left to a
successor gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
    Scalar,
    ScalarMatrix,
    _identity_matrix,
    _matrix_multiply,
    _scalar_add,
    _scalar_multiply,
    _scalar_scale,
    _scalar_stats,
    _scalar_variable,
    _token_matrix,
    _token_name,
    compile_source_native_721_v042,
)

RESULT_PATH = "results/v0.4.2_721_inverse_saturation.json"
SCHEMA = "final-theory-v042-721-inverse-saturation-v1"
VERDICT = "V042_721_ALL_EIGHT_INVERSE_TOKENS_SATURATE_EXACTLY_GENERIC_2X2_MATRIX_IDENTITY_OPEN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _determinant(matrix: ScalarMatrix) -> Scalar:
    return _scalar_add(
        _scalar_multiply(matrix[0][0], matrix[1][1]),
        _scalar_scale(-1, _scalar_multiply(matrix[0][1], matrix[1][0])),
    )


def _defined_inverse_matrix(
    base_matrix: ScalarMatrix, det_inverse_variable: Scalar
) -> ScalarMatrix:
    a, b = base_matrix[0]
    c, d = base_matrix[1]
    return (
        (
            _scalar_multiply(det_inverse_variable, d),
            _scalar_scale(-1, _scalar_multiply(det_inverse_variable, b)),
        ),
        (
            _scalar_scale(-1, _scalar_multiply(det_inverse_variable, c)),
            _scalar_multiply(det_inverse_variable, a),
        ),
    )


def _matrix_minus(left: ScalarMatrix, right: ScalarMatrix) -> ScalarMatrix:
    return tuple(
        tuple(_scalar_add(left[row][col], _scalar_scale(-1, right[row][col])) for col in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def compile_inverse_saturation_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    source_result = compile_source_native_721_v042(root)
    inverse_tokens: list[str] = source_result["native_generators"]["used_inverse_tokens"]
    if len(inverse_tokens) != 8:
        raise AssertionError("the used inverse token count changed")
    slot_total = len(inverse_tokens) * 8
    if slot_total != source_result["occurrence_map"]["inverse_relation_entry_slots"]:
        raise AssertionError("inverse relation slot count disagrees with the preflight gate")

    records: list[dict[str, Any]] = []
    for inverse_token in sorted(inverse_tokens):
        if not inverse_token.endswith("^-1"):
            raise AssertionError(f"not an inverse token: {inverse_token}")
        base_token = inverse_token.removesuffix("^-1")
        base_matrix = _token_matrix(base_token)
        det = _determinant(base_matrix)
        det_inverse_variable = _scalar_variable(f"D_{_token_name(base_token)}")
        defining_relation = _scalar_add(
            _scalar_multiply(det_inverse_variable, det), _scalar_scale(-1, {(): 1})
        )

        defined_inverse = _defined_inverse_matrix(base_matrix, det_inverse_variable)
        identity = _identity_matrix()

        forward_then_inverse = _matrix_minus(
            _matrix_multiply(base_matrix, defined_inverse), identity
        )
        inverse_then_forward = _matrix_minus(
            _matrix_multiply(defined_inverse, base_matrix), identity
        )

        off_diagonal_zero = True
        diagonal_reduces_to_defining_relation = True
        entry_records: list[dict[str, Any]] = []
        for label, residual in (
            ("A_times_Ainv_minus_I", forward_then_inverse),
            ("Ainv_times_A_minus_I", inverse_then_forward),
        ):
            for row in range(2):
                for col in range(2):
                    entry = residual[row][col]
                    is_diagonal = row == col
                    if is_diagonal:
                        # On the diagonal, "residual == 0" is only true modulo the
                        # defining relation D*det - 1 = 0. What is checked here as
                        # a raw polynomial identity is the weaker, exact statement
                        # that residual + 1 == D * det, i.e. the diagonal entry of
                        # A*Ainv (or Ainv*A) is *exactly* D*det, term for term, with
                        # nothing else present. Combined with the defining relation
                        # this gives the two-sided inverse identity.
                        implied = _scalar_add(entry, {(): 1})
                        matches_d_det = implied == _scalar_multiply(det_inverse_variable, det)
                        diagonal_reduces_to_defining_relation &= matches_d_det
                        entry_records.append(
                            {
                                "relation": label,
                                "row": row,
                                "col": col,
                                "kind": "diagonal",
                                "exactly_D_times_det": matches_d_det,
                                "term_count": len(entry),
                            }
                        )
                    else:
                        is_zero = not entry
                        off_diagonal_zero &= is_zero
                        entry_records.append(
                            {
                                "relation": label,
                                "row": row,
                                "col": col,
                                "kind": "off_diagonal",
                                "raw_polynomial_zero": is_zero,
                                "term_count": len(entry),
                            }
                        )
        if len(entry_records) != 8:
            raise AssertionError("expected exactly 8 checked entries per inverse token")
        saturates = off_diagonal_zero and diagonal_reduces_to_defining_relation
        records.append(
            {
                "inverse_token": inverse_token,
                "base_token": base_token,
                "determinant": {
                    **_scalar_stats(det),
                },
                "defining_relation": {
                    "form": "D * det(A) - 1",
                    **_scalar_stats(defining_relation),
                },
                "off_diagonal_zero_both_orderings": off_diagonal_zero,
                "diagonal_reduces_to_defining_relation_both_orderings": (
                    diagonal_reduces_to_defining_relation
                ),
                "saturates": saturates,
                "checked_entries": entry_records,
            }
        )

    all_saturate = all(record["saturates"] for record in records)
    if not all_saturate:
        raise AssertionError("an inverse token failed to saturate against its forward matrix")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "fixed_vector_GC__strong_MSR",
        "scope": {
            "inverse_tokens": sorted(inverse_tokens),
            "closed_form": "A^-1 = (1/det A) * adj(A) for generic invertible 2x2 A",
            "field": "QQ generic 2x2 matrix entries with commutative scalar monomials",
            "what_is_new_per_token": "one fresh scalar D_<token> standing for 1/det(A)",
            "not_yet_done": (
                "substituting these definitions back into the already compiled "
                "CPOBC/strong-MSR/GC scalar residuals is left to a successor gate"
            ),
        },
        "source_artifact_sha256": {
            "input_native_ir_semantic_digest_sha256": source_result[
                "semantic_digest_sha256"
            ],
        },
        "compiler_source_sha256": _sha256(Path(__file__).resolve()),
        "inverse_tokens_checked": len(records),
        "matrix_entry_slots_checked": len(records) * 8,
        "records": records,
        "record_digest_sha256": stable_hash(records),
        "solver_status": {
            "generic_2x2_scalar_expansion": True,
            "inverse_saturation_runs": 8,
            "Groebner_or_saturation_runs": 0,
            "commutativity_decided": False,
        },
        "claim_boundary": [
            "This proves the generic 2x2 two-sided matrix inverse identity for "
            "each of the 8 tokens actually used; it is linear algebra, not a "
            "search or a numerical check.",
            "The defining relations D_<token> * det(A) - 1 = 0 are new "
            "constraints, not yet imposed on the CPOBC/strong-MSR/GC scalar "
            "inventories compiled by earlier gates.",
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


def write_inverse_saturation(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_inverse_saturation_v042(root), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    print(write_inverse_saturation(Path(__file__).resolve().parents[3]))
