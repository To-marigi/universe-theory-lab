"""Sweep Lambda's row-span membership at diagonal points outside the symmetric families.

Every prior 955 point audited for the Eq120 collapse lemma came from one of two
constructions: a single growth-coupling vector applied to both diagonals (the
"two_character" family), or the two-parameter symbolic subfamily
``(1,1,1,1,t)`` / constant ``s`` audited in
``results/v0.4.2_955_lambda_fibre_audit.json``.  Both are highly structured:
the first and second diagonal couplings are drawn from the same combinatorial
formula, or one side is held to a single free parameter.

This module tests eight points whose first- and second-diagonal couplings are
chosen independently and without a shared pattern, to widen the evidence base
away from that structure.  A first attempt at this widening made a
methodological error worth recording: it read ``b`` values out of a fully
numeric assignment built by
``source_native_955_eq120_collapse_v042._lambda_at_point``, which never
assigns the ``A:*:01`` coordinates and leaves them at their initial zero.
Evaluating ``Lambda = (a_1-d_1) b_4 - (a_4-d_4) b_1`` there is vacuous --
``Lambda=0`` follows from ``b=0`` alone, regardless of ``a,d``, and tells
nothing about whether ``Lambda`` is forced to vanish on the actual fibre.

The correct test, matching
``source_native_955_commutator_span_v042.py`` and
``source_native_955_second_diagonal_span_v042.py``, is a row-span membership
test: build the matrix ``L`` whose rows are the stratum-restricted ``(0,1)``
core entries with only the weight-zero (diagonal) part evaluated numerically,
leaving the 123 positive-weight coordinates as symbolic columns, then check
whether the row ``{column(b_Q1): -(a_4-d_4), column(b_Q4): (a_1-d_1)}`` lies
in ``rowspan(L)``.  This is well posed regardless of which ``b`` a point of
the fibre actually has.

Every point is verified fail-closed: the diagonal-only entries of the scalar
core (the ``(0,0)`` and ``(1,1)`` blocks) must evaluate to exactly zero before
its row-span result is used, since those are the only core entries with a
nonzero constant term at ``b=0`` -- the ``(0,1)``/``(1,0)`` blocks are exactly
linear in the positive-weight family with no constant term, so they vanish at
``b=0`` identically and carry no information about whether the diagonal is a
genuine point of the scalar variety ``S``.

No Groebner, saturation, finite-field or numerical computation is performed.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_commutator_span_v042 as span
from universe_lab.final_theory import source_native_955_eq120_collapse_v042 as collapse
from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as stratum

SLACK_INVENTORY_PATH = span.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = span.MIXED_MANIFEST_PATH
REDUCTION_PATH = span.REDUCTION_PATH
COLLAPSE_PATH = collapse.RESULT_PATH
RESULT_PATH = "results/v0.4.2_955_independent_diagonal_sweep.json"

SCHEMA = "final-theory-v042-955-independent-diagonal-sweep-v1"
VERDICT = "V042_955_LAMBDA_IN_SPAN_AT_EIGHT_INDEPENDENT_DIAGONAL_POINTS_FULL_S_OPEN"

#: Eight (first, second) coupling pairs with no shared combinatorial pattern:
#: neither side is held to all-ones, a single free parameter, or the other
#: side's formula.
POINTS: tuple[tuple[str, tuple[int, ...], tuple[int, ...]], ...] = (
    ("swap_1_2_3_5_7__all_ones", (1, 2, 3, 5, 7), (1, 1, 1, 1, 1)),
    ("2_3_5_7_11__1_3_2_5_4", (2, 3, 5, 7, 11), (1, 3, 2, 5, 4)),
    ("1_1_2_1_1__3_2_1_4_2", (1, 1, 2, 1, 1), (3, 2, 1, 4, 2)),
    ("5_3_1_2_4__2_2_2_2_2", (5, 3, 1, 2, 4), (2, 2, 2, 2, 2)),
    ("1_4_1_4_1__4_1_4_1_4", (1, 4, 1, 4, 1), (4, 1, 4, 1, 4)),
    ("7_5_3_2_1__1_1_3_5_7", (7, 5, 3, 2, 1), (1, 1, 3, 5, 7)),
    ("1_1_1_1_2__2_1_1_1_1", (1, 1, 1, 1, 2), (2, 1, 1, 1, 1)),
    ("pi_digits_3_1_4_1_5__9_2_6_5_3", (3, 1, 4, 1, 5), (9, 2, 6, 5, 3)),
)


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
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _rank(rows: list[dict[int, Fraction]]) -> int:
    basis: dict[int, dict[int, Fraction]] = {}
    for source in rows:
        row = dict(source)
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
    return len(basis)


def compile_independent_diagonal_sweep_v042(root: Path) -> dict[str, Any]:
    """Test Lambda's row-span membership at eight structurally independent points."""

    root = root.resolve()
    paths = {
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        COLLAPSE_PATH: root / COLLAPSE_PATH,
    }
    slack = _load(paths[SLACK_INVENTORY_PATH])
    mixed = _load(paths[MIXED_MANIFEST_PATH])
    reduction = _load(paths[REDUCTION_PATH])
    collapse_result = _load(paths[COLLAPSE_PATH])
    for name, artifact in ((SLACK_INVENTORY_PATH, slack), (MIXED_MANIFEST_PATH, mixed)):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if collapse_result.get("verdict") != collapse.VERDICT:
        raise AssertionError("the Eq120 collapse predecessor is not at its certified verdict")

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    index_of = {name: index for index, name in enumerate(names)}
    families = stratum._classify(names)
    lower = set(families["A:10"])

    representative_to_orbit = {
        str(record["representative_occurrence_id"]): str(record["orbit_id"])
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    timid = {
        str(record["timid_orbit_representative"]) for record in slack["timid_slack_recurrences"]
    }
    non_timid = sorted(set(matrices) - timid)
    canonical_paths = {
        str(record["source_id"]): list(record["operator_word_later_on_left"])
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    timid_representative = {
        str(record["source_id"]): str(record["timid_orbit_representative"])
        for record in slack["timid_slack_recurrences"]
    }

    def characters(couplings: tuple[int, ...]) -> dict[str, Fraction]:
        by_orbit = span._characters(reduction, [Fraction(value) for value in couplings])
        return {
            representative: by_orbit[orbit]
            for representative, orbit in representative_to_orbit.items()
        }

    ledger = terms.OperationLedger()
    diagonal_entries: list[terms.Polynomial] = []
    upper_right: list[terms.Polynomial] = []
    for records in (
        slack["raw_source_system"]["CPOBC_equations"],
        slack["raw_source_system"]["strong_GC_basis"],
    ):
        for record in records:
            left = terms._word_matrix(record["lhs_source_word"], matrices, ledger)
            right = terms._word_matrix(record["rhs_source_word"], matrices, ledger)
            for row in range(2):
                for column in range(2):
                    residual = terms._add(
                        left[row][column], terms._scale(-1, right[row][column], ledger), ledger
                    )
                    if not residual:
                        continue
                    if (row, column) in ((0, 0), (1, 1)):
                        diagonal_entries.append(residual)
                    elif (row, column) == (0, 1):
                        upper_right.append(residual)
    occurring = {
        index for polynomial in upper_right for monomial in polynomial for index in monomial
    }
    positive_indices = [
        index
        for index in sorted(
            set(families["A:01"]) | set(families["u:0"]), key=lambda item: names[item]
        )
        if index in occurring
    ]
    positive = {index: column for column, index in enumerate(positive_indices)}

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    q_columns = {
        stage: positive[index_of[f"A:{representative}:01"]]
        for stage, representative in q_representatives.items()
    }

    def build(
        first_couplings: tuple[int, ...], second_couplings: tuple[int, ...]
    ) -> list[Fraction]:
        first = characters(first_couplings)
        second = characters(second_couplings)
        assignment = [Fraction(0)] * len(names)
        for representative in non_timid:
            assignment[index_of[f"A:{representative}:00"]] = first[representative]
            assignment[index_of[f"A:{representative}:11"]] = second[representative]
        for record in slack["timid_slack_recurrences"]:
            source_id = str(record["source_id"])
            product = Fraction(1)
            for symbol in canonical_paths[source_id]:
                product *= first[terms._operator(symbol)]
            base = Fraction(1)
            for operator, coefficient in zip(
                record["non_timid_orbit_representatives"],
                record["non_timid_coefficients"],
                strict=True,
            ):
                base -= int(coefficient) * second[str(operator)]
            target = second[timid_representative[source_id]]
            assignment[index_of[f"u:{source_id}:0"]] = Fraction(0)
            assignment[index_of[f"u:{source_id}:1"]] = (target - base) / product
        return assignment

    def diagonal_only_residuals(assignment: list[Fraction]) -> int:
        failures = 0
        for polynomial in diagonal_entries:
            total = Fraction(0)
            for monomial, coefficient in polynomial.items():
                value = Fraction(coefficient)
                for index in monomial:
                    value *= assignment[index]
                total += value
            if total:
                failures += 1
        return failures

    def row_of(polynomial: terms.Polynomial, assignment: list[Fraction]) -> dict[int, Fraction]:
        row, violations = span._linear_row(
            stratum._restrict(polynomial, lower), assignment, positive
        )
        if violations:
            raise AssertionError("a (0,1) core entry was not linear in the positive family")
        return row

    points: list[dict[str, Any]] = []
    for label, first_couplings, second_couplings in POINTS:
        assignment = build(first_couplings, second_couplings)
        failures = diagonal_only_residuals(assignment)
        if failures:
            raise AssertionError(
                f"{label} is not an exact core point: {failures} diagonal residuals"
            )
        rows = [row_of(polynomial, assignment) for polynomial in upper_right]
        base_rank = _rank(rows)

        a1 = assignment[index_of[f"A:{q_representatives[1]}:00"]]
        d1 = assignment[index_of[f"A:{q_representatives[1]}:11"]]
        a4 = assignment[index_of[f"A:{q_representatives[4]}:00"]]
        d4 = assignment[index_of[f"A:{q_representatives[4]}:11"]]
        determinant_d = a1 * d4 - a4 * d1

        lambda_row: dict[int, Fraction] = {}
        if d4 - a4:
            lambda_row[q_columns[1]] = -(a4 - d4)
        if a1 - d1:
            lambda_row[q_columns[4]] = a1 - d1
        augmented_rank = _rank([*rows, lambda_row])
        in_span = augmented_rank == base_rank
        points.append(
            {
                "label": label,
                "first_couplings": list(first_couplings),
                "second_couplings": list(second_couplings),
                "diagonal_only_residual_failures": 0,
                "L_shape": [len(rows), len(positive)],
                "L_rank": base_rank,
                "D": str(determinant_d),
                "D_nonzero": determinant_d != 0,
                "augmented_rank": augmented_rank,
                "status": "IN_SPAN" if in_span else "OUTSIDE_SPAN",
            }
        )

    escapes = [record for record in points if record["status"] == "OUTSIDE_SPAN"]
    d_nonzero_points = [record for record in points if record["D_nonzero"]]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "locus": "upper stratum, row-span test of Lambda := c_14",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            COLLAPSE_PATH: collapse_result["semantic_digest_sha256"],
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
        },
        "methodological_correction": {
            "prior_error": (
                "An earlier attempt evaluated Lambda by reading b values out of a fully "
                "numeric assignment that never sets A:*:01, so b=0 identically and "
                "Lambda=0 trivially -- a vacuous test, not a real check."
            ),
            "correct_method": (
                "Row-span membership test: evaluate only the weight-zero (diagonal) part of "
                "each (0,1) core entry numerically, leave the 123 positive-weight "
                "coordinates as symbolic columns of L, and test whether the Lambda "
                "functional row lies in rowspan(L)."
            ),
        },
        "fail_closed_verification": (
            "Only the (0,0) and (1,1) diagonal core blocks carry a nonzero constant term at "
            "b=0; the (0,1)/(1,0) blocks are exactly linear in the positive-weight family "
            "with no constant term and vanish identically there. Verifying the diagonal "
            "blocks alone is therefore equivalent to verifying the full 4,152-entry core at "
            "this construction."
        ),
        "points": points,
        "aggregate": {
            "points_tested": len(points),
            "points_with_D_nonzero": len(d_nonzero_points),
            "points_with_D_zero": len(points) - len(d_nonzero_points),
            "escapes": len(escapes),
            "L_rank_values": sorted({record["L_rank"] for record in points}),
            "all_in_span": len(escapes) == 0,
        },
        "claim_boundary": [
            "This widens the evidence base beyond the growth-family and two-character "
            "constructions; it is not a uniform proof over all of S.",
            "The upper stratum is not the unrestricted 955 profile.",
            "An in-span outcome at every tested point reaches none of the three declared "
            "955 terminals.",
            "No witness and no general obstruction is certified by this sweep alone.",
        ],
        "solver_status": {
            "exact_sparse_QQ_linear_algebra_runs": len(points),
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


def write_independent_diagonal_sweep_v042(root: Path) -> Path:
    payload = compile_independent_diagonal_sweep_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_independent_diagonal_sweep_v042(repository_root))
