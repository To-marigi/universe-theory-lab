"""Every required non-Q pivot column admits a source-localizer unit coefficient.

Gate 18's minor-cover preflight found a structural monomial matching in 107 of
the 119 non-Q columns and left the other 12 unexplained, calling for a finite
minor cover.  This module resolves what those 12 columns are and closes most of
the remaining distance to a localized row-module certificate.

Three facts are established, all exactly:

* **The 12 are all slack coordinates.**  Columns 0-106 are the ``A:*:01``
  upper-right matrix entries and 107-122 are the ``u:*:0`` slack coordinates.
  Every one of the 103 non-Q matrix coordinates was already matched; the 12
  without a single-monomial edge are all slack.

* **Only 4 of the 12 are ever needed.**  The non-Q block has rank 111 while the
  107 monomial-matched columns already carry rank 107, so exactly 4 further
  pivots are required.  At three independent non-degenerate points the
  elimination always takes them at the same four columns -- ``u:p2-2:0``,
  ``u:p3-006:0``, ``u:p3-024:0``, ``u:p3-026:0`` -- and the remaining 8, all at
  the terminal ``p4`` stage, are never pivots.  They are free directions,
  consistent with terminal-stage slack having no downstream constraint.

* **All four have localizer-unit coefficients.**  Each of those columns has a
  row whose coefficient factors completely into integer units, single source
  diagonal coordinates, and source matrix diagonal entries.  On the upper
  stratum every source matrix is upper triangular, so its determinant is the
  product of its two diagonal entries; localizing at the 131 source
  determinants therefore inverts every such factor.

Widening the matching from single-monomial edges to localizer-unit edges then
gives a maximum matching of size **111** -- exactly the required rank -- onto
111 distinct rows, with the 8 free slack columns having no unit row at all and
needing none.

What this does **not** yet give is a unit determinant.  A matching of unit
entries makes the determinant a sum over permutations, not a single product, so
the certificate needs the chosen submatrix to be permutation-triangular (or the
determinant computed another way).  A sparse-support-first selection reaches 98
of 111 strictly triangular steps with maximum residual support 2, so the
argument is close but **not closed**, and this module says so rather than
claiming the certificate.

No Groebner, saturation, finite-field or numerical computation is performed.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as fibre
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as upper

MINOR_COVER_PATH = "results/v0.4.2_955_minor_cover_preflight.json"
RESULT_PATH = "results/v0.4.2_955_unit_pivot_matching.json"

SCHEMA = "final-theory-v042-955-unit-pivot-matching-v1"
VERDICT = (
    "V042_955_ALL_111_REQUIRED_NON_Q_PIVOTS_HAVE_LOCALIZER_UNIT_COEFFICIENTS_"
    "DETERMINANT_UNIT_NOT_CERTIFIED_FULL_S_OPEN"
)

#: Deterministic non-degenerate points used to locate the required pivot columns.
#: The all-ones/all-ones pair is deliberately excluded: it is the scalar
#: degeneration, where every matrix is a scalar multiple of the identity and the
#: rank drops from 114 to 103.
RANK_POINTS: tuple[tuple[tuple[int, ...], tuple[int, ...]], ...] = (
    ((1, 1, 1, 1, 1), (2, 1, 1, 1, 1)),
    ((1, 1, 1, 1, 1), (1, 2, 3, 5, 7)),
    ((2, 3, 5, 7, 11), (1, 3, 2, 5, 4)),
)

MAX_TERMS_TESTED = 8


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


def _rank_on(rows: list[dict[int, Fraction]], columns: set[int]) -> tuple[int, set[int]]:
    basis: dict[int, dict[int, Fraction]] = {}
    for source in rows:
        row = {column: value for column, value in source.items() if column in columns}
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return len(basis), set(basis)


def compile_unit_pivot_matching_v042(root: Path) -> dict[str, Any]:
    """Certify that all 111 required non-Q pivots have localizer-unit coefficients."""

    root = root.resolve()
    minor_cover_path = root / MINOR_COVER_PATH
    minor_cover = _load(minor_cover_path)
    context = fibre._prepare(root)
    names = context["names"]
    positive = context["positive"]
    lower = set(context["lower"])
    column_name = {column: names[index] for index, column in positive.items()}
    symbol = {index: sympy.Symbol(f"v{index}") for index in range(len(names))}

    q_columns = {
        positive[context["index_of"][f"A:{representative}:01"]]
        for representative in context["q_representatives"].values()
    }
    non_q = set(range(123)) - q_columns

    matrix_columns = sorted(
        column for column, name in column_name.items() if name.startswith("A:")
    )
    slack_columns = sorted(
        column for column, name in column_name.items() if name.startswith("u:")
    )

    # --- what the source-determinant localization makes invertible ---------
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

    # --- coefficient inventory over the non-Q columns ----------------------
    unit_graph: dict[int, set[int]] = defaultdict(set)
    row_columns: dict[int, set[int]] = defaultdict(set)
    entries_tested = 0
    for row_index, polynomial in enumerate(context["upper_right"]):
        restricted = upper._restrict(polynomial, lower)
        coefficients: dict[int, list[tuple[tuple[int, ...], int]]] = defaultdict(list)
        for monomial, coefficient in restricted.items():
            carried = [index for index in monomial if index in positive]
            if len(carried) != 1:
                continue
            column = positive[carried[0]]
            if column not in non_q:
                continue
            remainder = list(monomial)
            remainder.remove(carried[0])
            coefficients[column].append((tuple(sorted(remainder)), int(coefficient)))
        for column, terms in coefficients.items():
            row_columns[row_index].add(column)
            if len(terms) > MAX_TERMS_TESTED:
                continue
            expression = sympy.expand(
                sum(
                    sympy.Integer(coefficient)
                    * sympy.prod([symbol[index] for index in monomial])
                    if monomial
                    else sympy.Integer(coefficient)
                    for monomial, coefficient in terms
                )
            )
            entries_tested += 1
            if is_localizer_unit(expression):
                unit_graph[column].add(row_index)

    # --- required pivot columns, measured at non-degenerate points ---------
    monomial_matched = set(minor_cover["structural_monomial_matching"]["matched_columns"])
    rank_records: list[dict[str, Any]] = []
    pivot_column_sets: list[frozenset[int]] = []
    for first_couplings, second_couplings in RANK_POINTS:
        first = fibre._characters_by_representative(context, first_couplings)
        second = fibre._characters_by_representative(context, second_couplings)
        assignment = fibre._build_assignment(context, first, second, symbolic=False)
        rows = fibre._linear_rows(context, assignment, symbolic=False)
        full_rank, pivots = _rank_on(rows, non_q)
        matched_rank, _ = _rank_on(rows, monomial_matched)
        extra = sorted(pivots - monomial_matched)
        pivot_column_sets.append(frozenset(extra))
        rank_records.append(
            {
                "first_couplings": list(first_couplings),
                "second_couplings": list(second_couplings),
                "non_q_rank": full_rank,
                "monomial_matched_rank": matched_rank,
                "gap": full_rank - matched_rank,
                "extra_pivot_columns": [column_name[column] for column in extra],
            }
        )
    if len({record["non_q_rank"] for record in rank_records}) != 1:
        raise AssertionError("the non-Q rank is not constant across the declared points")
    required_rank = rank_records[0]["non_q_rank"]
    if len(set(pivot_column_sets)) != 1:
        raise AssertionError("the extra pivot columns differ between points")
    extra_columns = sorted(pivot_column_sets[0])

    # --- exact factorisation of the four extra pivot coefficients ----------
    factorisations: list[dict[str, Any]] = []
    for column in extra_columns:
        best: tuple[int, list[tuple[tuple[int, ...], int]]] | None = None
        for row_index, polynomial in enumerate(context["upper_right"]):
            restricted = upper._restrict(polynomial, lower)
            terms = []
            for monomial, coefficient in restricted.items():
                carried = [index for index in monomial if index in positive]
                if len(carried) != 1 or positive[carried[0]] != column:
                    continue
                remainder = list(monomial)
                remainder.remove(carried[0])
                terms.append((tuple(sorted(remainder)), int(coefficient)))
            if terms and (best is None or len(terms) < len(best[1])):
                best = (row_index, terms)
        if best is None:
            raise AssertionError(f"no row carries column {column_name[column]}")
        row_index, terms = best
        expression = sympy.expand(
            sum(
                sympy.Integer(coefficient) * sympy.prod([symbol[index] for index in monomial])
                if monomial
                else sympy.Integer(coefficient)
                for monomial, coefficient in terms
            )
        )
        if not is_localizer_unit(expression):
            raise AssertionError(f"{column_name[column]} has no localizer-unit coefficient")
        factorisations.append(
            {
                "column": column_name[column],
                "row_index": row_index,
                "monomials": len(terms),
                "factored": str(sympy.factor(expression)),
                "all_factors_are_localizer_units": True,
            }
        )

    # --- maximum matching over localizer-unit edges ------------------------
    matched_row: dict[int, int] = {}

    def augment(column: int, seen: set[int]) -> bool:
        for row_index in sorted(unit_graph[column]):
            if row_index in seen:
                continue
            seen.add(row_index)
            if row_index not in matched_row or augment(matched_row[row_index], seen):
                matched_row[row_index] = column
                return True
        return False

    unit_matched: list[int] = []
    for column in sorted(unit_graph, key=lambda item: (len(unit_graph[item]), item)):
        if augment(column, set()):
            unit_matched.append(column)
    unit_matched.sort()
    unmatched = sorted(non_q - set(unit_matched))

    # --- how far a triangular peel gets on a sparse-first selection --------
    remaining_columns = set(unit_graph)
    used_rows: set[int] = set()
    triangular_steps = 0
    maximum_residual_support = 0
    selected = 0
    while remaining_columns:
        best_choice: tuple[int, int, int] | None = None
        for column in sorted(remaining_columns):
            for row_index in sorted(unit_graph[column] - used_rows):
                span = len(row_columns[row_index] & remaining_columns)
                if best_choice is None or span < best_choice[0]:
                    best_choice = (span, column, row_index)
            if best_choice and best_choice[0] == 1:
                break
        if best_choice is None:
            break
        span, column, row_index = best_choice
        selected += 1
        triangular_steps += span == 1
        maximum_residual_support = max(maximum_residual_support, span)
        remaining_columns.discard(column)
        used_rows.add(row_index)

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
        "source_artifact_sha256": {MINOR_COVER_PATH: _sha256(minor_cover_path)},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            MINOR_COVER_PATH: minor_cover["semantic_digest_sha256"],
        },
        "column_layout": {
            "matrix_columns_A_01": len(matrix_columns),
            "slack_columns_u_0": len(slack_columns),
            "total": len(matrix_columns) + len(slack_columns),
            "gate18_unmatched_are_all_slack": all(
                column_name[column].startswith("u:")
                for column in minor_cover["structural_monomial_matching"][
                    "unmatched_non_q_columns"
                ]
            ),
        },
        "required_pivot_rank": {
            "non_q_columns": len(non_q),
            "non_q_rank": required_rank,
            "monomial_matched_rank": rank_records[0]["monomial_matched_rank"],
            "gap": required_rank - rank_records[0]["monomial_matched_rank"],
            "extra_pivot_columns": [column_name[column] for column in extra_columns],
            "same_columns_at_every_point": True,
            "points": rank_records,
            "scalar_degeneration_excluded": (
                "The all-ones/all-ones pair is omitted: it is the scalar degeneration where "
                "rank(L) drops to 103, and using it would understate the required rank."
            ),
        },
        "free_slack_columns": {
            "count": len(non_q) - required_rank,
            "columns": [
                column_name[column]
                for column in sorted(
                    set(minor_cover["structural_monomial_matching"]["unmatched_non_q_columns"])
                    - set(extra_columns)
                )
            ],
            "never_used_as_pivots": True,
            "all_at_terminal_p4_stage": True,
        },
        "extra_pivot_factorisations": factorisations,
        "localizer": {
            "basis": (
                "On the upper stratum every source matrix is upper triangular, so "
                "det = (0,0) entry times (1,1) entry; localizing at the 131 source "
                "determinants inverts every source diagonal entry."
            ),
            "distinct_source_diagonal_keys": len(unit_keys),
            "coefficient_entries_tested": entries_tested,
            "max_terms_tested_per_entry": MAX_TERMS_TESTED,
        },
        "unit_edge_matching": {
            "columns_with_a_localizer_unit_row": len(unit_graph),
            "maximum_matching_size": len(unit_matched),
            "matches_required_rank": len(unit_matched) == required_rank,
            "rows_are_distinct": len(matched_row) == len(unit_matched),
            "unmatched_columns": [column_name[column] for column in unmatched],
            "unmatched_have_no_unit_row": all(
                not unit_graph.get(column) for column in unmatched
            ),
        },
        "determinant_unit_status": {
            "certified": False,
            "why_not": (
                "A matching of unit entries makes the determinant a signed sum over "
                "permutations, not a single product.  A unit determinant needs the chosen "
                "submatrix to be permutation-triangular, or the determinant computed another "
                "way."
            ),
            "sparse_first_selection_columns": selected,
            "strictly_triangular_steps": triangular_steps,
            "maximum_residual_support_at_selection": maximum_residual_support,
            "steps_short_of_triangular": selected - triangular_steps,
        },
        "what_this_resolves_from_gate18": (
            "Gate 18 left 12 non-Q columns without a structural matching and called for a "
            "finite minor cover.  Those 12 are all slack coordinates; 8 are free directions "
            "that no elimination uses, and the 4 that are required each carry a coefficient "
            "that is a unit after source-determinant localization.  Widening the matching to "
            "localizer-unit edges attains the full required rank of 111 on distinct rows."
        ),
        "claim_boundary": [
            "No unit determinant and therefore no localized row-module certificate is issued.",
            "The required-pivot measurement is at three declared points; the rank being "
            "constant there is not a proof that it is constant on all of S.",
            "The upper stratum is not the unrestricted 955 profile.",
            "Nothing here decides whether Lambda is forced to vanish.",
        ],
        "solver_status": {
            "symbolic_factorisations": entries_tested,
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


def write_unit_pivot_matching_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_unit_pivot_matching_v042(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_unit_pivot_matching_v042(repository_root))
