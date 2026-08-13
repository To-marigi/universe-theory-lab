"""Worker process for the corrected 721 Groebner preflight probe.

Invoked as a subprocess (with a hard wall-clock timeout imposed by the
parent driver) so a hang or blow-up in sympy.groebner() cannot stall the
session. Picks the N smallest-by-total-term-count nonzero reduced CPOBC
residual units. A residual unit is one complete 2-by-2 residual: all of its
nonzero scalar entries are passed together to sympy.groebner(). This avoids
the predecessor bug that counted individual scalar entries as if they were
whole residuals. The defining relations for whichever of the 8 inverse
tokens actually appear are added, and sympy.groebner() is run once.

Not a production gate: no JSON schema, no digest, no CURRENT_RESEARCH_STATE
registration. This exists only to measure real cost before any owner
decision about a full/unbounded Groebner run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import sympy  # noqa: E402

from universe_lab.final_theory.source_native_721_inverse_relation_reduction_cpobc_msr_v042 import (  # noqa: E402
    CPOBC_PATH,
    REDUCTION_PATH,
    _compile_occurrences,
    _cpobc_residuals,
    _load,
    _matrix_expression_saturated,
    _matrix_stats,
    _reduce_matrix,
)
from universe_lab.final_theory.source_native_721_inverse_relation_reduction_probe_v042 import (  # noqa: E402
    INVERSE_BASE_TOKENS,
    _token_relation_variables,
)

type Scalar = dict[tuple[str, ...], int]
type ScalarMatrix = tuple[tuple[Scalar, Scalar], tuple[Scalar, Scalar]]


def _smallest_reduced_residual_units(count: int) -> list[dict[str, Any]]:
    cpobc = _load(ROOT, CPOBC_PATH)
    reduction = _load(ROOT, REDUCTION_PATH)
    occurrence_expressions, _, _ = _compile_occurrences(reduction)

    scored: list[dict[str, Any]] = []
    for first_id, second_id, residual in _cpobc_residuals(
        cpobc, occurrence_expressions
    ):
        if not residual:
            continue
        saturated = _matrix_expression_saturated(residual)
        if _matrix_stats(saturated)["nonzero_entry_count"] == 0:
            continue
        reduced = _reduce_matrix(saturated)
        stats = _matrix_stats(reduced)
        if stats["nonzero_entry_count"] == 0:
            continue
        nonzero_entries = [
            scalar
            for row in reduced
            for scalar in row
            if scalar
        ]
        if not nonzero_entries:
            continue
        stats = _matrix_stats(reduced)
        scored.append(
            {
                "first_id": first_id,
                "second_id": second_id,
                "selection_key": (
                    stats["total_scalar_term_count"],
                    stats["maximum_scalar_term_count"],
                    stats["maximum_monomial_degree"],
                    first_id,
                    second_id,
                ),
                "matrix_stats": stats,
                "entries": [
                    {
                        "row": row,
                        "column": column,
                        "scalar": reduced[row][column],
                    }
                    for row in range(2)
                    for column in range(2)
                    if reduced[row][column]
                ],
            }
        )

    scored.sort(key=lambda record: record["selection_key"])
    return scored[:count]


def _scalars_to_sympy(
    units: list[dict[str, Any]],
) -> tuple[list[sympy.Expr], set[str]]:
    variables: set[str] = set()
    polys: list[sympy.Expr] = []
    for unit in units:
        for entry in unit["entries"]:
            scalar: Scalar = {
                tuple(monomial.split("|")) if monomial else (): int(coefficient)
                for monomial, coefficient in entry["scalar"].items()
            }
            expr = sympy.Integer(0)
            for monomial, coefficient in scalar.items():
                variables.update(monomial)
                term = sympy.Integer(coefficient)
                for var in monomial:
                    term *= sympy.Symbol(var)
                expr += term
            polys.append(expr)
    return polys, variables


def _relation_polys(present_variables: set[str]) -> list[sympy.Expr]:
    relations: list[sympy.Expr] = []
    for token in INVERSE_BASE_TOKENS:
        det_var, a, b, c, d = _token_relation_variables(token)
        if not any(
            variable in present_variables
            for variable in (det_var, a, b, c, d)
        ):
            continue
        D, A, B, C, Dd = (sympy.Symbol(name) for name in (det_var, a, b, c, d))
        relations.append(D * (A * Dd - B * C) - 1)
    return relations


CACHE_PATH = ROOT / "scratch_v042_721_groebner_preflight_residual_units.json"


def _cached_smallest_residual_units(count: int) -> list[dict[str, Any]]:
    if not CACHE_PATH.exists():
        raise RuntimeError(
            f"missing residual-unit cache: build it first with {CACHE_PATH.name}"
        )
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or len(raw) < count:
        raise RuntimeError("residual-unit cache has insufficient entries")
    result: list[dict[str, Any]] = []
    for unit in raw[:count]:
        if not isinstance(unit, dict) or "entries" not in unit:
            raise RuntimeError("cache is not in residual-unit format")
        result.append(unit)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=True)
    args = parser.parse_args()

    units = _cached_smallest_residual_units(args.count)
    polys, variables = _scalars_to_sympy(units)
    relation_polys = _relation_polys(variables)
    for relation in relation_polys:
        variables.update(str(sym) for sym in relation.free_symbols)

    symbols = sorted(variables)
    all_polys = polys + relation_polys

    print(
        f"count={args.count} residual_units={len(units)} "
        f"residual_polys={len(polys)} relation_polys={len(relation_polys)} "
        f"variables={len(symbols)}",
        flush=True,
    )

    start = time.time()
    basis = sympy.groebner(all_polys, *[sympy.Symbol(s) for s in symbols], order="grevlex")
    elapsed = time.time() - start
    print(f"DONE elapsed={elapsed:.3f}s basis_size={len(basis.polys)}", flush=True)


if __name__ == "__main__":
    main()
