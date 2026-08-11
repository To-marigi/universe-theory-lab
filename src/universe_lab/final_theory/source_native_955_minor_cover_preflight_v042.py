"""Finite-sample preflight for the upper-stratum localized minor cover.

Gate18 measured the ring, the 1038 by 123 linear fibre, and the three
diagonal anchors, but did not test whether a small collection of exact pivot
minors can cover even a deterministic source-native sample.  This module does
that lightweight measurement only:

* build the structural monomial matching in the 119 non-Q columns;
* trace exact non-Q pivot signatures at a 4-by-10 diagonal-character sample;
* test each distinct sample minor against the other points in its anchor open;
* report the greedy and exact minimum cover sizes on that finite sample.

The sample cover is not a cover of ``S``.  No determinant product, Groebner
basis, saturation, numerical search, or finite-field computation is run.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as fibre
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as upper

RESULT_PATH = "results/v0.4.2_955_minor_cover_preflight.json"
SCHEMA = "final-theory-v042-955-minor-cover-preflight-v1"
VERDICT = "V042_955_LOCALIZED_MINOR_COVER_PREFLIGHT_FINITE_SAMPLE_NOT_CERTIFIED_FULL_S_OPEN"

FIRST_COUPLINGS = (
    (1, 1, 1, 1, 1),
    (1, 2, 3, 5, 7),
    (2, 1, 4, 1, 3),
    (3, 1, 1, 1, 1),
)
SECOND_COUPLINGS = (
    (1, 1, 1, 1, 1),
    (2, 1, 1, 1, 1),
    (3, 1, 1, 1, 1),
    (1, 2, 3, 5, 7),
    (2, 1, 4, 1, 3),
    (1, 1, 1, 1, 2),
    (1, 1, 1, 1, 3),
    (1, 1, 1, 1, 5),
    (1, 1, 1, 1, 7),
)
EXTRA_COUPLING_PAIRS = (
    ((1, 1, 1, 1, 1), (1, 3, 2, 1, 3)),
    ((1, 1, 1, 2, 1), (1, 2, 1, 3, 3)),
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(unsigned).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_determinant_failures(
    context: dict[str, Any], assignment: list[Fraction]
) -> int:
    failures = 0
    for matrix in context["matrices"].values():
        evaluated = [
            [fibre._evaluate(cell, assignment, symbolic=False) for cell in row]
            for row in matrix
        ]
        determinant = evaluated[0][0] * evaluated[1][1] - evaluated[0][1] * evaluated[1][0]
        failures += not bool(determinant)
    return failures


def _q_values(
    context: dict[str, Any], assignment: list[Fraction]
) -> tuple[dict[int, Fraction], dict[int, Fraction]]:
    q = context["q_representatives"]
    index_of = context["index_of"]
    a = {
        stage: assignment[index_of[f"A:{representative}:00"]]
        for stage, representative in q.items()
    }
    d = {
        stage: assignment[index_of[f"A:{representative}:11"]]
        for stage, representative in q.items()
    }
    return a, d


def _anchor(a: dict[int, Fraction], d: dict[int, Fraction]) -> tuple[str, dict[str, str]]:
    determinants = {
        f"D1{stage}": a[1] * d[stage] - a[stage] * d[1]
        for stage in (2, 3, 4)
    }
    if determinants["D14"]:
        label = "D14"
    elif determinants["D12"]:
        label = "D12"
    elif determinants["D13"]:
        label = "D13"
    else:
        label = "RANK1"
    return label, {key: str(value) for key, value in determinants.items()}


def _trace_non_q_pivots(
    rows: list[dict[int, Fraction]], q_columns: dict[int, int]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    non_q = set(range(123)) - set(q_columns.values())
    basis: dict[int, dict[int, Fraction]] = {}
    pivot_rows: dict[int, int] = {}
    for row_index, source in enumerate(rows):
        row = dict(source)
        while True:
            pivot = min((column for column in row if column in non_q), default=None)
            if pivot is None:
                break
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {
                    column: value / scale for column, value in row.items()
                }
                pivot_rows[pivot] = row_index
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    columns = tuple(sorted(basis))
    return tuple(pivot_rows[column] for column in columns), columns


def _structural_monomial_matching(
    context: dict[str, Any]
) -> dict[str, Any]:
    lower = set(context["lower"])
    positive = context["positive"]
    q_columns = {
        stage: positive[context["index_of"][f"A:{representative}:01"]]
        for stage, representative in context["q_representatives"].items()
    }
    non_q = set(range(123)) - set(q_columns.values())
    graph: dict[int, set[int]] = defaultdict(set)
    edge_terms: dict[tuple[int, int], tuple[tuple[int, ...], int]] = {}
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
            coefficients[column].append((tuple(remainder), int(coefficient)))
        for column, terms_at_edge in coefficients.items():
            if len(terms_at_edge) == 1:
                graph[column].add(row_index)
                edge_terms[(column, row_index)] = terms_at_edge[0]

    matched_row_to_column: dict[int, int] = {}

    def augment(column: int, seen: set[int]) -> bool:
        for row_index in sorted(graph[column]):
            if row_index in seen:
                continue
            seen.add(row_index)
            if row_index not in matched_row_to_column or augment(
                matched_row_to_column[row_index], seen
            ):
                matched_row_to_column[row_index] = column
                return True
        return False

    matched_columns: list[int] = []
    for column in sorted(graph, key=lambda item: (len(graph[item]), item)):
        if augment(column, set()):
            matched_columns.append(column)
    matched_columns.sort()
    source_diagonal_names = {
        name
        for representative in context["matrices"]
        for name in (f"A:{representative}:00", f"A:{representative}:11")
    }
    matching_edges: list[dict[str, Any]] = []
    factor_occurrences = 0
    all_factors_are_source_diagonal = True
    coefficient_abs_one = True
    for row_index, column in sorted(
        ((row_index, column) for row_index, column in matched_row_to_column.items()),
        key=lambda item: item[1],
    ):
        monomial, coefficient = next(
            terms_at_edge
            for (edge_column, edge_row), terms_at_edge in edge_terms.items()
            if edge_column == column and edge_row == row_index
        )
        names = [context["names"][index] for index in monomial]
        factor_occurrences += len(names)
        coefficient_abs_one &= abs(coefficient) == 1
        all_factors_are_source_diagonal &= set(names) <= source_diagonal_names
        matching_edges.append(
            {
                "column": column,
                "row": row_index,
                "coefficient": coefficient,
                "monomial": names,
            }
        )

    ledger = terms.OperationLedger()
    source_localizer_support_names: set[str] = set()
    source_determinants_all_nonzero = True
    for matrix in context["matrices"].values():
        determinant = terms._add(
            terms._multiply(matrix[0][0], matrix[1][1], ledger),
            terms._scale(
                -1, terms._multiply(matrix[0][1], matrix[1][0], ledger), ledger
            ),
            ledger,
        )
        restricted = upper._restrict(determinant, set(context["lower"]))
        source_determinants_all_nonzero &= bool(restricted)
        for monomial in restricted:
            source_localizer_support_names.update(
                context["names"][index] for index in monomial
            )

    return {
        "non_q_columns": len(non_q),
        "columns_with_monomial_edges": len(graph),
        "monomial_matching_size": len(matched_columns),
        "matched_columns": matched_columns,
        "unmatched_non_q_columns": sorted(non_q - set(matched_columns)),
        "matching_is_full": len(matched_columns) == len(non_q),
        "matching_edges": matching_edges,
        "matching_factor_occurrences": factor_occurrences,
        "matching_max_factor_degree": max(
            (len(edge["monomial"]) for edge in matching_edges), default=0
        ),
        "matching_coefficients_abs_one": coefficient_abs_one,
        "all_matching_factors_are_source_diagonal": all_factors_are_source_diagonal,
        "source_determinants_all_nonzero": source_determinants_all_nonzero,
        "matching_factors_appear_in_source_localizer_support": set(
            name for edge in matching_edges for name in edge["monomial"]
        ) <= source_localizer_support_names,
        "matching_factor_names_not_in_source_localizers": sorted(
            set(name for edge in matching_edges for name in edge["monomial"])
            - source_localizer_support_names
        ),
        "unit_minor_certificate_issued": False,
    }


def _restricted_rank(
    rows: list[dict[int, Fraction]],
    candidate_rows: tuple[int, ...],
    candidate_columns: tuple[int, ...],
) -> int:
    restricted: list[dict[int, Fraction]] = []
    for row_index in candidate_rows:
        source = rows[row_index]
        restricted.append(
            {
                new_column: source[column]
                for new_column, column in enumerate(candidate_columns)
                if source.get(column, Fraction(0))
            }
        )
    return len(
        fibre._independent_basis(
            restricted,
            allowed=set(range(len(candidate_columns))),
            symbolic=False,
        )
    )


def _minimum_sample_cover(
    points: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> dict[str, Any]:
    coverage: list[set[int]] = []
    for candidate in candidates:
        covered = {
            point_index
            for point_index, point in enumerate(points)
            if _restricted_rank(
                point["rows"], candidate["rows"], candidate["columns"]
            )
            == len(candidate["columns"])
        }
        coverage.append(covered)

    best: tuple[int, ...] | None = None
    for size in range(1, len(candidates) + 1):
        for combination in itertools.combinations(range(len(candidates)), size):
            union: set[int] = set()
            for candidate_index in combination:
                union.update(coverage[candidate_index])
            if len(union) == len(points):
                best = combination
                break
        if best is not None:
            break

    remaining = set(range(len(points)))
    greedy: list[int] = []
    while remaining:
        candidate_index = max(
            range(len(candidates)),
            key=lambda item: (len(coverage[item] & remaining), -item),
        )
        gain = coverage[candidate_index] & remaining
        if not gain:
            break
        greedy.append(candidate_index)
        remaining.difference_update(gain)
    return {
        "candidate_count": len(candidates),
        "coverage_counts": [len(values) for values in coverage],
        "minimum_cover_size_on_sample": len(best) if best is not None else None,
        "minimum_cover_candidate_indices": list(best) if best is not None else None,
        "greedy_candidate_indices": greedy,
        "greedy_uncovered_point_indices": sorted(remaining),
        "sample_cover_certified": False,
    }


def compile_minor_cover_preflight_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    context = fibre._prepare(root)
    q_columns = {
        stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
        for stage, representative in context["q_representatives"].items()
    }
    structural = _structural_monomial_matching(context)
    base_pairs = tuple(itertools.product(FIRST_COUPLINGS, SECOND_COUPLINGS))
    sample_pairs = tuple(dict.fromkeys((*base_pairs, *EXTRA_COUPLING_PAIRS)))
    points: list[dict[str, Any]] = []
    core_failure_points = 0
    source_singular_points = 0
    for first_couplings, second_couplings in sample_pairs:
        first = fibre._characters_by_representative(context, first_couplings)
        second = fibre._characters_by_representative(context, second_couplings)
        assignment = fibre._build_assignment(
            context, first, second, symbolic=False
        )
        core_failures = sum(
            bool(fibre._evaluate(polynomial, assignment, symbolic=False))
            for polynomial in context["core"]
        )
        if core_failures:
            core_failure_points += 1
            continue
        determinant_failures = _source_determinant_failures(context, assignment)
        if determinant_failures:
            source_singular_points += 1
            continue
        rows = fibre._linear_rows(context, assignment, symbolic=False)
        a, d = _q_values(context, assignment)
        anchor, determinants = _anchor(a, d)
        pivot_rows, pivot_columns = _trace_non_q_pivots(rows, q_columns)
        points.append(
            {
                "first": list(first_couplings),
                "second": list(second_couplings),
                "anchor": anchor,
                "D": determinants,
                "rows": rows,
                "pivot_rows": pivot_rows,
                "pivot_columns": pivot_columns,
                "non_q_rank": len(pivot_columns),
            }
        )

    serial_points: list[dict[str, Any]] = []
    for point in points:
        serial_points.append(
            {
                key: value
                for key, value in point.items()
                if key not in {"rows", "pivot_rows", "pivot_columns"}
            }
            | {
                "pivot_signature": {
                    "rows": list(point["pivot_rows"]),
                    "columns": list(point["pivot_columns"]),
                }
            }
        )

    cover_by_anchor: dict[str, Any] = {}
    for anchor in ("D14", "D12", "D13"):
        anchor_points = [point for point in points if point["anchor"] == anchor]
        signature_to_candidate: dict[tuple[tuple[int, ...], tuple[int, ...]], dict[str, Any]] = {}
        for point in anchor_points:
            signature = (point["pivot_rows"], point["pivot_columns"])
            signature_to_candidate.setdefault(
                signature,
                {
                    "rows": list(point["pivot_rows"]),
                    "columns": list(point["pivot_columns"]),
                    "source": {
                        "first": point["first"],
                        "second": point["second"],
                    },
                },
            )
        candidates = list(signature_to_candidate.values())
        cover_by_anchor[anchor] = {
            "sample_points": len(anchor_points),
            "distinct_pivot_signatures": len(candidates),
            "candidates": candidates,
            "cover": _minimum_sample_cover(anchor_points, candidates)
            if candidates
            else {
                "candidate_count": 0,
                "coverage_counts": [],
                "minimum_cover_size_on_sample": 0,
                "minimum_cover_candidate_indices": [],
                "greedy_candidate_indices": [],
                "greedy_uncovered_point_indices": [],
                "sample_cover_certified": False,
            },
        }

    paths = {
        "results/v0.4.2_955_source_native_slack_compiler.json": root
        / "results/v0.4.2_955_source_native_slack_compiler.json",
        "results/v0.4.2_955_mixed_source_native_manifest.json": root
        / "results/v0.4.2_955_mixed_source_native_manifest.json",
        "results/v0.3.2_cpobc_generator_reduction.json": root
        / "results/v0.3.2_cpobc_generator_reduction.json",
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "locus": "upper stratum source-native diagonal-character finite preflight",
            "field": "QQ",
            "first_grid_size": len(FIRST_COUPLINGS),
            "second_grid_size": len(SECOND_COUPLINGS),
            "maximum_product_points": len(FIRST_COUPLINGS) * len(SECOND_COUPLINGS),
            "extra_anchor_pairs": [
                {"first": list(first), "second": list(second)}
                for first, second in EXTRA_COUPLING_PAIRS
            ],
            "full_S_claim": False,
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "structural_monomial_matching": structural,
        "sample": {
            "points_attempted": len(sample_pairs),
            "points_verified_core": len(points),
            "core_failure_points": core_failure_points,
            "source_singular_points": source_singular_points,
            "rank_one_points": sum(point["anchor"] == "RANK1" for point in points),
            "rank_two_points": sum(point["anchor"] != "RANK1" for point in points),
            "points": serial_points,
        },
        "finite_sample_cover_by_anchor": cover_by_anchor,
        "localized_certificate_contract": {
            "source_determinant_localization_used": False,
            "scalar_core_ideal_used": False,
            "determinant_product_materialized": False,
            "full_S_minor_cover_issued": False,
            "status": "FINITE_SAMPLE_ONLY_NOT_A_CERTIFICATE",
        },
        "interpretation": {
            "proved": [
                (
                    "The structural non-Q support has an exact monomial matching of the "
                    "recorded size over the scalar polynomial support."
                ),
                (
                    "Every accepted sample point was checked against all 4,152 core "
                    "entries and all 131 source determinants."
                ),
                "Candidate pivot minors were tested exactly over QQ on the declared sample.",
            ],
            "not_proved": [
                "A finite minor cover over S or its source determinant localization.",
                "A row-module certificate for Lambda on any anchor open.",
                "The rank-one closed branch or the unrestricted 955 profile.",
            ],
        },
        "solver_status": {
            "Groebner_runs": 0,
            "saturation_runs": 0,
            "numerical_search_runs": 0,
            "finite_field_runs": 0,
            "solver_run": False,
        },
        "unrestricted_source_native_955_status": "OPEN",
        "witness_certified": False,
        "commutativity_proved_for_full_profile": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_minor_cover_preflight_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    payload = compile_minor_cover_preflight_v042(root)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_minor_cover_preflight_v042(repository_root))
