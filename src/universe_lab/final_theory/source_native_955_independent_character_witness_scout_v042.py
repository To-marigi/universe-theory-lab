"""Fast exact witness-first scout on independent diagonal character families.

This is intentionally a finite scout, not a no-go proof.  It reuses the
source-native growth-character construction for the first and second diagonal
independently, then applies the cheapest exact filters in order:

1. all 4,152 scalar core entries;
2. all 131 source determinants;
3. ``D_14``;
4. the pure-Q row-module remainder of ``Lambda_14``.

The scout stops on the first ``D_14 != 0`` and ``Lambda_14`` escape.  If no
escape occurs, the unrestricted 955 profile remains open and the next useful
step is a localized certificate rather than a larger unstructured grid.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as fibre

RESULT_PATH = "results/v0.4.2_955_independent_character_witness_scout.json"
SCHEMA = "final-theory-v042-955-independent-character-witness-scout-v1"
NO_ESCAPE_VERDICT = "V042_955_INDEPENDENT_CHARACTER_SCOUT_NO_LAMBDA_ESCAPE_FULL_S_OPEN"
ESCAPE_VERDICT = "V042_955_INDEPENDENT_CHARACTER_SCOUT_LAMBDA_ESCAPE_CANDIDATE_FULL_S_OPEN"


COUPLING_GRID = (
    (1, 1, 1, 1, 1),
    (1, 1, 1, 1, 2),
    (1, 1, 1, 1, 3),
    (1, 1, 1, 2, 1),
    (1, 1, 2, 1, 1),
    (1, 2, 1, 2, 1),
    (1, 2, 3, 5, 7),
    (2, 1, 4, 1, 3),
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


def _lambda_on_kernel(
    context: dict[str, Any], assignment: list[Fraction], kernel_q: dict[int, Fraction]
) -> Fraction:
    q = context["q_representatives"]
    index_of = context["index_of"]
    a1 = assignment[index_of[f"A:{q[1]}:00"]]
    d1 = assignment[index_of[f"A:{q[1]}:11"]]
    a4 = assignment[index_of[f"A:{q[4]}:00"]]
    d4 = assignment[index_of[f"A:{q[4]}:11"]]
    return (a1 - d1) * kernel_q[4] - (a4 - d4) * kernel_q[1]


def compile_independent_character_witness_scout_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    context = fibre._prepare(root)
    q_columns = {
        stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
        for stage, representative in context["q_representatives"].items()
    }
    point_records: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    attempted = 0
    core_failure_points = 0
    determinant_failure_points = 0
    d_nonzero_points = 0
    for first_couplings in COUPLING_GRID:
        first = fibre._characters_by_representative(context, first_couplings)
        for second_couplings in COUPLING_GRID:
            attempted += 1
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
                point_records.append(
                    {
                        "first": list(first_couplings),
                        "second": list(second_couplings),
                        "status": "CORE_REJECTED",
                        "core_failures": core_failures,
                    }
                )
                continue
            determinant_failures = _source_determinant_failures(context, assignment)
            if determinant_failures:
                determinant_failure_points += 1
                point_records.append(
                    {
                        "first": list(first_couplings),
                        "second": list(second_couplings),
                        "status": "SOURCE_SINGULAR_REJECTED",
                        "core_failures": 0,
                        "source_determinant_failures": determinant_failures,
                    }
                )
                continue
            rows = fibre._linear_rows(context, assignment, symbolic=False)
            pure = fibre._pure_q_elimination(rows, q_columns, symbolic=False)
            q = context["q_representatives"]
            index_of = context["index_of"]
            a1 = assignment[index_of[f"A:{q[1]}:00"]]
            d1 = assignment[index_of[f"A:{q[1]}:11"]]
            a4 = assignment[index_of[f"A:{q[4]}:00"]]
            d4 = assignment[index_of[f"A:{q[4]}:11"]]
            denominator = a1 * d4 - a4 * d1
            if denominator:
                d_nonzero_points += 1
            _, _lambda_row, remainder = fibre._lambda_remainder(
                context, assignment, pure, symbolic=False
            )
            kernel_q: dict[int, Fraction] | None = None
            lambda_on_kernel: Fraction | None = None
            if denominator and remainder:
                try:
                    kernel_q = fibre._numeric_kernel_q_vector(rows, q_columns)
                    lambda_on_kernel = _lambda_on_kernel(context, assignment, kernel_q)
                except AssertionError:
                    kernel_q = None
            is_candidate = bool(denominator and lambda_on_kernel)
            record: dict[str, Any] = {
                "first": list(first_couplings),
                "second": list(second_couplings),
                "status": "LAMBDA_ESCAPE_CANDIDATE" if is_candidate else "NO_ESCAPE",
                "core_failures": 0,
                "source_determinant_failures": 0,
                "D14": str(denominator),
                "rows": len(rows),
                "non_q_rank": pure["non_q_rank"],
                "pure_q_rank": pure["pure_q_rank"],
                "lambda_row_remainder_terms": len(remainder),
                "lambda_on_Q_visible_kernel": (
                    str(lambda_on_kernel) if lambda_on_kernel is not None else None
                ),
            }
            if kernel_q is not None:
                record["q_visible_kernel"] = {
                    str(stage): str(value) for stage, value in kernel_q.items()
                }
            point_records.append(record)
            if is_candidate:
                candidates.append(record)
                break
        if candidates:
            break

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
            "locus": "upper stratum source-native independent growth-character diagonal families",
            "first_grid_size": len(COUPLING_GRID),
            "second_grid_size": len(COUPLING_GRID),
            "maximum_product_points": len(COUPLING_GRID) * len(COUPLING_GRID),
            "field": "QQ",
            "full_S_claim": False,
            "stop_on_first_escape": True,
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "q_stage_mapping": {
            str(stage): representative
            for stage, representative in sorted(context["q_representatives"].items())
        },
        "search": {
            "coupling_grid": [list(values) for values in COUPLING_GRID],
            "normalization": "first coupling fixed to 1",
            "points_attempted": attempted,
            "points_verified_core": attempted - core_failure_points - determinant_failure_points,
            "core_failure_points": core_failure_points,
            "source_singular_points": determinant_failure_points,
            "D14_nonzero_points": d_nonzero_points,
            "lambda_escape_candidates": candidates,
            "records": point_records,
        },
        "interpretation": {
            "proved": [
                (
                    "Every completed point was checked against all 4,152 core entries "
                    "before fibre elimination."
                ),
                "The source determinant and Lambda filters were exact over QQ.",
            ],
            "not_proved": [
                "The scout does not cover the full scalar variety S.",
                "A no-escape result is not an obstruction theorem.",
                (
                    "A candidate still requires N, Eq113/Eq139, reachable visibility, "
                    "and nonsingularity checks."
                ),
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
        "witness_candidate_found": bool(candidates),
        "witness_certified": False,
        "commutativity_proved_for_full_profile": False,
        "search_terminal": False,
        "passed": True,
        "verdict": ESCAPE_VERDICT if candidates else NO_ESCAPE_VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_independent_character_witness_scout_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(
            compile_independent_character_witness_scout_v042(root),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_independent_character_witness_scout_v042(repository_root))
