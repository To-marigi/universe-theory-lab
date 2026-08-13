"""Worker process for the 721 Groebner preflight probe.

Invoked as a subprocess (with a hard wall-clock timeout imposed by the
parent driver) so a hang or blow-up in sympy.groebner() cannot stall the
session. Picks the N smallest-by-term-count nonzero reduced CPOBC
residuals, adds the defining relations for whichever of the 8 inverse
tokens actually appear among them, and runs sympy.groebner() once.

Not a production gate: no JSON schema, no digest, no CURRENT_RESEARCH_STATE
registration. This exists only to measure real cost before any owner
decision about a full/unbounded Groebner run.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

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


def _smallest_reduced_residuals(count: int) -> list[dict[tuple[str, ...], int]]:
    cpobc = _load(ROOT, CPOBC_PATH)
    reduction = _load(ROOT, REDUCTION_PATH)
    occurrence_expressions, _, _ = _compile_occurrences(reduction)

    scored: list[tuple[int, dict[tuple[str, ...], int]]] = []
    for _first, _second, residual in _cpobc_residuals(cpobc, occurrence_expressions):
        if not residual:
            continue
        saturated = _matrix_expression_saturated(residual)
        if _matrix_stats(saturated)["nonzero_entry_count"] == 0:
            continue
        reduced = _reduce_matrix(saturated)
        stats = _matrix_stats(reduced)
        if stats["nonzero_entry_count"] == 0:
            continue
        for entry in reduced:
            for scalar in entry:
                if scalar:
                    scored.append((sum(abs(v) for v in scalar.values()), scalar))

    scored.sort(key=lambda pair: pair[0])
    return [scalar for _weight, scalar in scored[:count]]


def _scalars_to_sympy(
    scalars: list[dict[tuple[str, ...], int]],
) -> tuple[list[sympy.Expr], set[str]]:
    variables: set[str] = set()
    polys: list[sympy.Expr] = []
    for scalar in scalars:
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
        if det_var not in present_variables and a not in present_variables:
            continue
        D, A, B, C, Dd = (sympy.Symbol(name) for name in (det_var, a, b, c, d))
        relations.append(D * (A * Dd - B * C) - 1)
    return relations


CACHE_PATH = ROOT / "scratch_v042_721_groebner_preflight_cache.json"


def _cached_smallest_residuals(count: int) -> list[dict[tuple[str, ...], int]]:
    import json

    if CACHE_PATH.exists():
        raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    else:
        scalars = _smallest_reduced_residuals(200)
        raw = [
            {"|".join(monomial): coeff for monomial, coeff in scalar.items()}
            for scalar in scalars
        ]
        CACHE_PATH.write_text(json.dumps(raw), encoding="utf-8", newline="\n")

    result: list[dict[tuple[str, ...], int]] = []
    for entry in raw[:count]:
        scalar: dict[tuple[str, ...], int] = {}
        for key, coeff in entry.items():
            monomial = tuple(key.split("|")) if key else ()
            scalar[monomial] = coeff
        result.append(scalar)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=True)
    args = parser.parse_args()

    scalars = _cached_smallest_residuals(args.count)
    polys, variables = _scalars_to_sympy(scalars)
    relation_polys = _relation_polys(variables)
    for relation in relation_polys:
        variables.update(str(sym) for sym in relation.free_symbols)

    symbols = sorted(variables)
    all_polys = polys + relation_polys

    print(f"count={args.count} residual_polys={len(polys)} "
          f"relation_polys={len(relation_polys)} variables={len(symbols)}",
          flush=True)

    start = time.time()
    basis = sympy.groebner(all_polys, *[sympy.Symbol(s) for s in symbols], order="grevlex")
    elapsed = time.time() - start
    print(f"DONE elapsed={elapsed:.3f}s basis_size={len(basis.polys)}", flush=True)


if __name__ == "__main__":
    main()
