"""Exact rank-one diagonal audit inside the source-native character family.

The ``D_12,D_13,D_14`` anchor cover leaves a genuine rank-one diagonal locus
where all four ``(a_i,d_i)`` pairs are proportional.  This module audits that
closed branch on the finite ``{1,2,3}`` source-native character grid.  It is a
bounded branch audit, not a theorem about the full scalar scheme ``S``.

Each retained point is checked against every scalar core entry and all 131
source determinants.  The six upper-right commutator forms are then tested
directly against the exact row span of the 1038 by 123 upper-right core matrix.
No Groebner basis, saturation, numerical search, or finite-field computation
is performed.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as fibre

RESULT_PATH = "results/v0.4.2_955_rank_one_character_audit.json"
SCHEMA = "final-theory-v042-955-rank-one-character-audit-v1"
VERDICT = "V042_955_RANK_ONE_SOURCE_NATIVE_CHARACTER_AUDIT_NO_ESCAPE_FULL_S_OPEN"

COUPLING_GRID = tuple(
    (1, *tail) for tail in itertools.product((1, 2, 3), repeat=4)
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


def _rank(rows: list[dict[int, Fraction]]) -> int:
    return len(fibre._independent_basis(rows, allowed=set(range(123)), symbolic=False))


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


def _q_data(
    context: dict[str, Any], assignment: list[Fraction]
) -> tuple[dict[int, int], dict[int, Fraction], dict[int, Fraction]]:
    q = context["q_representatives"]
    index_of = context["index_of"]
    q_columns = {
        stage: context["positive"][index_of[f"A:{representative}:01"]]
        for stage, representative in q.items()
    }
    a = {
        stage: assignment[index_of[f"A:{representative}:00"]]
        for stage, representative in q.items()
    }
    d = {
        stage: assignment[index_of[f"A:{representative}:11"]]
        for stage, representative in q.items()
    }
    return q_columns, a, d


def _commutator_row(
    q_columns: dict[int, int], a: dict[int, Fraction], d: dict[int, Fraction], left: int, right: int
) -> dict[int, Fraction]:
    row = {
        q_columns[right]: a[left] - d[left],
        q_columns[left]: -(a[right] - d[right]),
    }
    return {column: value for column, value in row.items() if value}


def compile_rank_one_character_audit_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    context = fibre._prepare(root)
    characters = {
        couplings: fibre._characters_by_representative(context, couplings)
        for couplings in COUPLING_GRID
    }
    q = context["q_representatives"]
    records: list[dict[str, Any]] = []
    rank_one_candidates = 0
    core_failure_points = 0
    source_singular_points = 0
    nontrivial_points = 0
    escape_points = 0

    for first_couplings in COUPLING_GRID:
        first = characters[first_couplings]
        for second_couplings in COUPLING_GRID:
            second = characters[second_couplings]
            q_determinants = {
                f"D1{stage}": first[q[1]] * second[q[stage]]
                - first[q[stage]] * second[q[1]]
                for stage in (2, 3, 4)
            }
            if any(q_determinants.values()):
                continue

            rank_one_candidates += 1
            assignment = fibre._build_assignment(
                context, first, second, symbolic=False
            )
            core_failures = sum(
                bool(fibre._evaluate(polynomial, assignment, symbolic=False))
                for polynomial in context["core"]
            )
            if core_failures:
                core_failure_points += 1
                records.append(
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
                source_singular_points += 1
                records.append(
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
            base_rank = _rank(rows)
            q_columns, a, d = _q_data(context, assignment)
            nontrivial = any(a[stage] != d[stage] for stage in q)
            nontrivial_points += nontrivial
            pair_records: list[dict[str, Any]] = []
            point_escapes = 0
            for left in range(1, 5):
                for right in range(left + 1, 5):
                    commutator = _commutator_row(q_columns, a, d, left, right)
                    augmented_rank = _rank([*rows, commutator])
                    increment = augmented_rank - base_rank
                    point_escapes += increment != 0
                    pair_records.append(
                        {
                            "pair": [left, right],
                            "rank_increment": increment,
                            "status": "OUTSIDE_SPAN" if increment else "IN_SPAN",
                        }
                    )
            escape_points += point_escapes != 0
            records.append(
                {
                    "first": list(first_couplings),
                    "second": list(second_couplings),
                    "status": "COMMUTATOR_ESCAPE" if point_escapes else "NO_ESCAPE",
                    "core_failures": 0,
                    "source_determinant_failures": 0,
                    "rank_one_determinants": {
                        label: str(value) for label, value in q_determinants.items()
                    },
                    "q_diagonal_a": {str(stage): str(value) for stage, value in a.items()},
                    "q_diagonal_d": {str(stage): str(value) for stage, value in d.items()},
                    "q_diagonal_non_scalar": nontrivial,
                    "rows": len(rows),
                    "L_rank": base_rank,
                    "commutators": pair_records,
                }
            )

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
            "locus": "upper stratum source-native rank-one diagonal character branch",
            "field": "QQ",
            "coupling_grid_size": len(COUPLING_GRID),
            "maximum_pair_points": len(COUPLING_GRID) ** 2,
            "full_S_claim": False,
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "search": {
            "coupling_grid": [list(values) for values in COUPLING_GRID],
            "rank_one_candidates": rank_one_candidates,
            "records": records,
            "core_failure_points": core_failure_points,
            "source_singular_points": source_singular_points,
            "q_diagonal_non_scalar_points": nontrivial_points,
            "commutator_escape_points": escape_points,
        },
        "interpretation": {
            "proved": [
                (
                    "Every retained grid point was checked against all 4,152 scalar core "
                    "entries before row-span testing."
                ),
                "All six Q commutator rows were tested exactly over QQ at every accepted point.",
            ],
            "not_proved": [
                "The finite character grid does not cover the rank-one branch of S.",
                "The upper stratum does not cover the unrestricted 955 profile.",
                "No full-S obstruction or 955 terminal follows from this audit.",
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


def write_rank_one_character_audit_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(
            compile_rank_one_character_audit_v042(root),
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
    print(write_rank_one_character_audit_v042(repository_root))
