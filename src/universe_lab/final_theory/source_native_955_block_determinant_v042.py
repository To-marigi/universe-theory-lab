"""The unit-minor route to the 955 row-module certificate does not close.

The unit-pivot gate showed that all 111 required non-Q pivot columns admit
coefficients that are units after localizing at the 131 source determinants,
and that a maximum matching over those unit edges attains exactly rank 111 on
distinct rows.  What it could not show is that the resulting 111-by-111
determinant is a unit, since a matching of unit entries only makes the
determinant a signed sum over permutations.

This module settles that question with the Dulmage-Mendelsohn decomposition
and returns a negative answer for the route as posed.

Building the digraph on matched columns and taking strongly connected
components gives the canonical irreducible block structure -- canonical because
the SCCs of the matched digraph do not depend on which perfect matching was
chosen.  There are 60 blocks: 39 singletons, and non-trivial blocks of sizes up
to 15.  The determinant of the whole submatrix is the product of the block
determinants, so singletons contribute unit factors and the question reduces to
the non-trivial blocks.

Computing the determinants of every block of size at most three -- 19 of the 21
non-trivial blocks -- shows that **none of them is a unit**.  They carry
genuinely new irreducible factors such as ``v52 - v55``, ``v199*v71 -
v367*v79`` and ``v172*v315 + v175*v427 - v315``, none of which is a source
matrix diagonal entry.  Localizing at the 131 source determinants therefore
does not invert them.

The route is not logically dead: each block column has many alternative unit
rows, so a different matching could in principle give unit block determinants.
But the search space is recorded here and it is not a plan -- the size-15 block
alone admits roughly 1.4e29 alternative matchings, and no structural reason has
emerged why a unit choice should exist among them.

This module runs the blocks of size at most three only.  The size-7 and size-15
determinants are left unevaluated and their choice counts are reported instead,
because the negative answer is already established by the small blocks and
evaluating the large ones would not change it.

No Groebner, saturation, finite-field or numerical computation is performed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as fibre
from universe_lab.final_theory import source_native_955_unit_pivot_matching_v042 as pivots
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as upper

UNIT_PIVOT_PATH = pivots.RESULT_PATH
RESULT_PATH = "results/v0.4.2_955_block_determinant.json"

SCHEMA = "final-theory-v042-955-block-determinant-v1"
VERDICT = (
    "V042_955_UNIT_MINOR_ROUTE_DOES_NOT_CLOSE_IRREDUCIBLE_BLOCK_DETERMINANTS_ARE_"
    "NOT_LOCALIZER_UNITS_FULL_S_OPEN"
)

MAX_TERMS_TESTED = 8
#: Blocks larger than this are inventoried but their determinants are not evaluated.
MAX_BLOCK_EVALUATED = 3


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(unsigned).encode("utf-8")).hexdigest()


def _strongly_connected(adjacency: dict[int, set[int]], vertices: list[int]) -> list[list[int]]:
    index: dict[int, int] = {}
    low: dict[int, int] = {}
    on_stack: dict[int, bool] = {}
    stack: list[int] = []
    components: list[list[int]] = []
    counter = [0]

    def strongconnect(start: int) -> None:
        work = [(start, iter(sorted(adjacency[start])))]
        index[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on_stack[start] = True
        while work:
            vertex, iterator = work[-1]
            advanced = False
            for successor in iterator:
                if successor not in index:
                    index[successor] = low[successor] = counter[0]
                    counter[0] += 1
                    stack.append(successor)
                    on_stack[successor] = True
                    work.append((successor, iter(sorted(adjacency[successor]))))
                    advanced = True
                    break
                if on_stack.get(successor):
                    low[vertex] = min(low[vertex], index[successor])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[vertex])
            if low[vertex] == index[vertex]:
                component = []
                while True:
                    popped = stack.pop()
                    on_stack[popped] = False
                    component.append(popped)
                    if popped == vertex:
                        break
                components.append(component)

    for vertex in vertices:
        if vertex not in index:
            strongconnect(vertex)
    return components


def compile_block_determinant_v042(root: Path) -> dict[str, Any]:
    """Decide whether the unit-matched 111x111 minor has a unit determinant."""

    sys.setrecursionlimit(10000)
    root = root.resolve()
    unit_pivot_path = root / UNIT_PIVOT_PATH
    unit_pivot = _load(unit_pivot_path)
    if unit_pivot.get("verdict") != pivots.VERDICT:
        raise AssertionError("the unit-pivot predecessor is not at its certified verdict")

    context = fibre._prepare(root)
    names = context["names"]
    positive = context["positive"]
    lower = set(context["lower"])
    symbol = {index: sympy.Symbol(f"v{index}") for index in range(len(names))}
    q_columns = {
        positive[context["index_of"][f"A:{representative}:01"]]
        for representative in context["q_representatives"].values()
    }
    non_q = set(range(123)) - q_columns

    unit_keys: set[str] = set()
    for matrix in context["matrices"].values():
        for cell in (matrix[0][0], matrix[1][1]):
            expression = sympy.expand(
                sum(
                    sympy.Integer(coefficient)
                    * sympy.prod([symbol[index] for index in monomial])
                    if monomial
                    else sympy.Integer(coefficient)
                    for monomial, coefficient in upper._restrict(cell, lower).items()
                )
            )
            unit_keys.add(sympy.srepr(sympy.expand(expression)))
            unit_keys.add(sympy.srepr(sympy.expand(-expression)))

    def is_localizer_unit(expression: sympy.Expr) -> bool:
        if expression == 0:
            return False
        factored = sympy.factor(sympy.expand(expression))
        factors = factored.as_ordered_factors() if factored.is_Mul else [factored]
        for factor in factors:
            base = factor.base if factor.is_Pow else factor
            if base.is_Integer or base.is_Symbol:
                continue
            if sympy.srepr(sympy.expand(base)) in unit_keys:
                continue
            return False
        return True

    def coefficient_terms(row_index: int) -> dict[int, list[tuple[tuple[int, ...], int]]]:
        restricted = upper._restrict(context["upper_right"][row_index], lower)
        collected: dict[int, list[tuple[tuple[int, ...], int]]] = defaultdict(list)
        for monomial, coefficient in restricted.items():
            carried = [index for index in monomial if index in positive]
            if len(carried) != 1:
                continue
            column = positive[carried[0]]
            if column not in non_q:
                continue
            remainder = list(monomial)
            remainder.remove(carried[0])
            collected[column].append((tuple(sorted(remainder)), int(coefficient)))
        return collected

    def to_expression(terms: list[tuple[tuple[int, ...], int]]) -> sympy.Expr:
        return sympy.expand(
            sum(
                sympy.Integer(coefficient) * sympy.prod([symbol[index] for index in monomial])
                if monomial
                else sympy.Integer(coefficient)
                for monomial, coefficient in terms
            )
        )

    unit_edge: dict[int, set[int]] = defaultdict(set)
    row_columns: dict[int, set[int]] = defaultdict(set)
    for row_index in range(len(context["upper_right"])):
        for column, terms in coefficient_terms(row_index).items():
            row_columns[row_index].add(column)
            if len(terms) > MAX_TERMS_TESTED:
                continue
            if is_localizer_unit(to_expression(terms)):
                unit_edge[column].add(row_index)

    matched_row: dict[int, int] = {}

    def augment(column: int, seen: set[int]) -> bool:
        for row_index in sorted(unit_edge[column]):
            if row_index in seen:
                continue
            seen.add(row_index)
            if row_index not in matched_row or augment(matched_row[row_index], seen):
                matched_row[row_index] = column
                return True
        return False

    for column in sorted(unit_edge, key=lambda item: (len(unit_edge[item]), item)):
        augment(column, set())
    matched_column = {column: row for row, column in matched_row.items()}
    chosen = set(matched_column)
    if len(chosen) != 111:
        raise AssertionError(f"expected a 111 matching, got {len(chosen)}")

    adjacency: dict[int, set[int]] = defaultdict(set)
    for column in chosen:
        row_index = matched_column[column]
        for other in row_columns[row_index] & chosen:
            if other != column:
                adjacency[column].add(other)
    components = _strongly_connected(adjacency, sorted(chosen))
    sizes = sorted((len(component) for component in components), reverse=True)
    non_trivial = sorted((c for c in components if len(c) > 1), key=len)

    degrees = {column: len(unit_edge[column]) for column in chosen}

    evaluated: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    new_factors: set[str] = set()
    for component in non_trivial:
        columns = sorted(component)
        choice_product = 1
        for column in columns:
            choice_product *= degrees[column]
        if len(columns) > MAX_BLOCK_EVALUATED:
            deferred.append(
                {
                    "size": len(columns),
                    "alternative_matchings_upper_bound": str(choice_product),
                    "determinant_evaluated": False,
                }
            )
            continue
        rows = [matched_column[column] for column in columns]
        matrix = sympy.zeros(len(columns), len(columns))
        for i, row_index in enumerate(rows):
            terms_by_column = coefficient_terms(row_index)
            for j, column in enumerate(columns):
                matrix[i, j] = to_expression(terms_by_column.get(column, []))
        determinant = sympy.factor(sympy.expand(matrix.det(method="berkowitz")))
        unit = is_localizer_unit(determinant)
        if not unit and determinant != 0:
            factored = (
                determinant.as_ordered_factors() if determinant.is_Mul else [determinant]
            )
            for factor in factored:
                base = factor.base if factor.is_Pow else factor
                if base.is_Integer or base.is_Symbol:
                    continue
                if sympy.srepr(sympy.expand(base)) in unit_keys:
                    continue
                new_factors.add(str(base))
        evaluated.append(
            {
                "size": len(columns),
                "alternative_matchings_upper_bound": str(choice_product),
                "determinant_evaluated": True,
                "determinant": str(determinant),
                "is_localizer_unit": unit,
            }
        )
    if any(record["is_localizer_unit"] for record in evaluated):
        raise AssertionError("a block determinant unexpectedly became a unit")

    total_space = 1
    for component in non_trivial:
        for column in component:
            total_space *= degrees[column]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "locus": "upper stratum of the unrestricted 476-coordinate chart",
        },
        "source_artifact_sha256": {UNIT_PIVOT_PATH: _sha256(unit_pivot_path)},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            UNIT_PIVOT_PATH: unit_pivot["semantic_digest_sha256"],
        },
        "question": (
            "The unit-pivot gate matched all 111 required non-Q columns to distinct rows with "
            "localizer-unit coefficients. A unit-entry matching does not make the determinant "
            "a unit, so is the 111-by-111 determinant a unit or not."
        ),
        "dulmage_mendelsohn": {
            "matched_columns": len(chosen),
            "components": len(components),
            "singleton_components": sum(1 for size in sizes if size == 1),
            "non_trivial_components": len(non_trivial),
            "block_sizes_descending": sizes[:25],
            "largest_block": sizes[0],
            "structure_is_matching_independent": (
                "The strongly connected components of the matched digraph are canonical for "
                "the bipartite support; a different perfect matching gives the same block "
                "structure, though not the same block determinants."
            ),
        },
        "block_determinants": {
            "max_block_size_evaluated": MAX_BLOCK_EVALUATED,
            "evaluated": evaluated,
            "deferred": deferred,
            "evaluated_count": len(evaluated),
            "deferred_count": len(deferred),
            "any_evaluated_block_is_a_unit": False,
            "why_deferred": (
                "The negative answer is already established by the small blocks; evaluating "
                "the size-7 and size-15 determinants would not change it."
            ),
        },
        "new_non_unit_factors": {
            "count": len(new_factors),
            "factors": sorted(new_factors),
            "none_is_a_source_diagonal_entry": True,
            "consequence": (
                "Localizing at the 131 source determinants does not invert these, so the "
                "elimination is not valid over that localization with this matching."
            ),
        },
        "remaining_search_space": {
            "every_column_has_alternative_unit_rows": all(
                degree >= 2 for degree in degrees.values()
            ),
            "max_unit_rows_for_one_column": max(degrees.values()),
            "alternative_matchings_upper_bound_over_non_trivial_blocks": str(total_space),
            "size_15_block_alone": next(
                (
                    record["alternative_matchings_upper_bound"]
                    for record in deferred
                    if record["size"] == 15
                ),
                None,
            ),
            "assessment": (
                "The route is not logically dead -- a different matching could give unit block "
                "determinants -- but the space is enormous and no structural reason has "
                "emerged why a unit choice should exist in it."
            ),
        },
        "claim_boundary": [
            "This is a negative result about one route, not about the 955 profile.",
            "It does not prove that no unit-determinant matching exists.",
            "It does not decide whether Lambda is forced to vanish.",
            "The upper stratum is not the unrestricted 955 profile.",
        ],
        "solver_status": {
            "symbolic_block_determinants": len(evaluated),
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "unrestricted_source_native_955_status": "OPEN",
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_block_determinant_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_block_determinant_v042(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_block_determinant_v042(repository_root))
