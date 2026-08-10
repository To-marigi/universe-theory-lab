"""The span decision with the second diagonal actually varied.

Gate 13 decided the six upper-stratum commutator forms against the core row span
at sequential-growth points, and recorded one limitation as the thing that
mattered: the growth assignment pins every ``A:*:11`` to one, so it sweeps the
first diagonal and never the second -- and the second is exactly where the
upper-triangular form ``(a_i-d_i)b_j-(a_j-d_j)b_i`` stops being degenerate.

This module removes that limitation.  Two constructions produce exact points of
the scalar variety with a second diagonal that is not identically one:

* **constant** -- every ``A:*:11`` set to a rational ``c``;
* **two-character** -- ``A:*:00`` from growth couplings ``t`` and ``A:*:11`` from
  independent couplings ``t'``, which makes the second diagonal genuinely
  non-constant.

The construction that made this work is one line of the timid slack recurrence.
Solving ``u:c:1`` against a target of one -- the value the frozen basepoint
happens to have -- fails: earlier candidates drawn from the 42-dimensional
kernel of the binomial subsystem left 5 to 21 nonzero core residuals.  The
target has to be the timid orbit's own second-diagonal value.  With that
correction the same construction verifies exactly.  Every point is checked
fail-closed against all 4,152 streamed core entries before it is used.

Verdict strings come from ``reports/v0.4.2_955_commutator_span_gate_design.md``
and were fixed before any of this was measured.

No Groebner, saturation, finite-field or numerical computation is performed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_commutator_span_v042 as span
from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as stratum

SLACK_INVENTORY_PATH = span.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = span.MIXED_MANIFEST_PATH
REDUCTION_PATH = span.REDUCTION_PATH
COMMUTATOR_SPAN_PATH = span.RESULT_PATH
RESULT_PATH = "results/v0.4.2_955_second_diagonal_span.json"

SCHEMA = "final-theory-v042-955-second-diagonal-span-v1"
IN_SPAN_VERDICT = span.IN_SPAN_VERDICT
ESCAPE_VERDICT = span.ESCAPE_VERDICT
GLOBAL_VERDICT = span.GLOBAL_VERDICT

#: Deterministic constant second diagonals.  One is the frozen control.
CONSTANTS: tuple[tuple[str, tuple[int, int]], ...] = (
    ("constant_1_control", (1, 1)),
    ("constant_2", (2, 1)),
    ("constant_3", (3, 1)),
    ("constant_1_over_2", (1, 2)),
    ("constant_minus_1", (-1, 1)),
    ("constant_5_over_3", (5, 3)),
)

#: Deterministic second-diagonal couplings, paired against the all-ones first
#: diagonal.  The first entry makes both diagonals equal, which is the scalar
#: degeneration and is retained precisely because it must behave differently.
SECOND_COUPLINGS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("two_character_equal_scalar_degeneration", (1, 1, 1, 1, 1)),
    ("two_character_1_2_3_5_7", (1, 2, 3, 5, 7)),
    ("two_character_2_1_4_1_3", (2, 1, 4, 1, 3)),
    ("two_character_3_1_1_1_1", (3, 1, 1, 1, 1)),
)

FIRST_COUPLINGS = (1, 1, 1, 1, 1)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _evaluate(polynomial: terms.Polynomial, assignment: Sequence[Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in polynomial.items():
        value = Fraction(coefficient)
        for index in monomial:
            value *= assignment[index]
        total += value
    return total


def compile_second_diagonal_span_v042(root: Path) -> dict[str, Any]:
    """Decide the commutator forms at points whose second diagonal is not one."""

    root = root.resolve()
    paths = {
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        COMMUTATOR_SPAN_PATH: root / COMMUTATOR_SPAN_PATH,
    }
    slack = span._load(paths[SLACK_INVENTORY_PATH])
    mixed = span._load(paths[MIXED_MANIFEST_PATH])
    reduction = span._load(paths[REDUCTION_PATH])
    predecessor = span._load(paths[COMMUTATOR_SPAN_PATH])
    for name, artifact in (
        (SLACK_INVENTORY_PATH, slack),
        (MIXED_MANIFEST_PATH, mixed),
        (COMMUTATOR_SPAN_PATH, predecessor),
    ):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if predecessor.get("verdict") != span.GLOBAL_VERDICT:
        raise AssertionError("the commutator span predecessor is not at its certified verdict")

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

    def characters(couplings: Sequence[int]) -> dict[str, Fraction]:
        by_orbit = span._characters(reduction, [Fraction(value) for value in couplings])
        return {
            representative: by_orbit[orbit]
            for representative, orbit in representative_to_orbit.items()
        }

    ledger = terms.OperationLedger()
    core: list[terms.Polynomial] = []
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
                    core.append(residual)
                    if (row, column) == (0, 1):
                        upper_right.append(residual)
    occurring = {index for polynomial in core for monomial in polynomial for index in monomial}
    positive_indices = [
        index
        for index in sorted(
            set(families["A:01"]) | set(families["u:0"]), key=lambda item: names[item]
        )
        if index in occurring
    ]
    positive = {index: column for column, index in enumerate(positive_indices)}
    if len(positive) != predecessor["evaluated_points"][0]["L_shape"][1]:
        raise AssertionError("positive-weight column count disagrees with the predecessor")

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    stages = sorted(q_representatives)
    commutators: list[tuple[tuple[int, int], terms.Polynomial]] = []
    for position, left_stage in enumerate(stages):
        for right_stage in stages[position + 1 :]:
            left = matrices[q_representatives[left_stage]]
            right = matrices[q_representatives[right_stage]]
            product = terms._matrix_multiply(left, right, ledger)
            reverse = terms._matrix_multiply(right, left, ledger)
            commutators.append(
                (
                    (left_stage, right_stage),
                    terms._add(product[0][1], terms._scale(-1, reverse[0][1], ledger), ledger),
                )
            )

    def build(first: dict[str, Fraction], second: dict[str, Fraction]) -> list[Fraction]:
        assignment = [Fraction(0)] * len(names)
        for representative in non_timid:
            assignment[index_of[f"A:{representative}:00"]] = first[representative]
            assignment[index_of[f"A:{representative}:11"]] = second[representative]
        for record in slack["timid_slack_recurrences"]:
            source_id = str(record["source_id"])
            product = Fraction(1)
            for symbol in canonical_paths[source_id]:
                product *= first[terms._operator(symbol)]
            if not product:
                raise AssertionError(f"the reachable state vanished at {source_id}")
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

    def decide(
        label: str, assignment: list[Fraction], second: dict[str, Fraction]
    ) -> dict[str, Any]:
        residual_failures = sum(1 for polynomial in core if _evaluate(polynomial, assignment))
        if residual_failures:
            return {
                "label": label,
                "verified_as_core_point": False,
                "nonzero_core_entries": residual_failures,
                "streamed_core_entries": len(core),
            }
        rows = [
            span._linear_row(stratum._restrict(polynomial, lower), assignment, positive)[0]
            for polynomial in upper_right
        ]
        base_rank = span._rank(rows)
        pair_records = []
        escapes = 0
        for pair, polynomial in commutators:
            row, failed = span._linear_row(
                stratum._restrict(polynomial, lower), assignment, positive
            )
            if failed:
                raise AssertionError("a commutator entry was not linear in the positive family")
            augmented = span._rank([*rows, row])
            in_span = augmented == base_rank
            if not in_span:
                escapes += 1
            pair_records.append(
                {
                    "pair": list(pair),
                    "nonzero_columns_after_evaluation": len(row),
                    "augmented_rank": augmented,
                    "rank_increment": augmented - base_rank,
                    "status": "IN_SPAN" if in_span else "OUTSIDE_SPAN",
                }
            )
        values = {second[representative] for representative in non_timid}
        determinants = [
            assignment[index_of[f"A:{representative}:00"]]
            * assignment[index_of[f"A:{representative}:11"]]
            for representative in non_timid
        ]
        return {
            "label": label,
            "verified_as_core_point": True,
            "nonzero_core_entries": 0,
            "streamed_core_entries": len(core),
            "second_diagonal": {
                "distinct_values": len(values),
                "identically_one": values == {Fraction(1)},
                "sample_values": sorted(str(value) for value in values)[:8],
            },
            "singular_transitions": sum(1 for value in determinants if not value),
            "L_shape": [len(rows), len(positive)],
            "L_rank": base_rank,
            "fibre_dimension": len(positive) - base_rank,
            "pairs": pair_records,
            "escapes": escapes,
            "verdict": ESCAPE_VERDICT if escapes else IN_SPAN_VERDICT,
        }

    first_characters = characters(FIRST_COUPLINGS)
    evaluated: list[dict[str, Any]] = []
    for label, (numerator, denominator) in CONSTANTS:
        constant = Fraction(numerator, denominator)
        second = dict.fromkeys(first_characters, constant)
        evaluated.append(decide(label, build(first_characters, second), second))
    for label, couplings in SECOND_COUPLINGS:
        second = characters(couplings)
        evaluated.append(decide(label, build(first_characters, second), second))

    verified = [record for record in evaluated if record["verified_as_core_point"]]
    if len(verified) != len(evaluated):
        raise AssertionError("a declared point failed the fail-closed core verification")
    moved = [
        record
        for record in verified
        if not record["second_diagonal"]["identically_one"]
        and record["second_diagonal"]["distinct_values"] > 1
    ]
    total_escapes = sum(record["escapes"] for record in verified)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "gate_design": "reports/v0.4.2_955_commutator_span_gate_design.md",
        "verdict_strings_fixed_before_measurement": True,
        "closes_the_predecessor_limitation": (
            "Gate 13 recorded that the growth family never varies the second diagonal.  These "
            "points do vary it, constantly and non-constantly."
        ),
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "locus": "upper stratum of the unrestricted 476-coordinate chart",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            COMMUTATOR_SPAN_PATH: predecessor["semantic_digest_sha256"],
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
        },
        "construction": {
            "constant": "every A:*:11 set to one rational c",
            "two_character": "A:*:00 from couplings t, A:*:11 from independent couplings t'",
            "timid_slack_target": (
                "u:c:1 is solved so that the timid matrix's second diagonal equals that timid "
                "orbit's own second-diagonal value, not one."
            ),
            "why_that_matters": (
                "Solving against a target of one is what made earlier candidates from the "
                "42-dimensional binomial kernel fail with 5 to 21 nonzero core residuals.  The "
                "failure was the target, not an obstruction in the variety."
            ),
        },
        "evaluated_points": evaluated,
        "aggregate": {
            "points": len(evaluated),
            "verified_as_core_points": len(verified),
            "points_with_a_non_constant_second_diagonal": len(moved),
            "points_with_an_escape": sum(1 for record in verified if record["escapes"]),
            "total_escapes": total_escapes,
            "L_rank_values": sorted({record["L_rank"] for record in verified}),
            "maximum_distinct_second_diagonal_values": max(
                record["second_diagonal"]["distinct_values"] for record in verified
            ),
            "verdict": GLOBAL_VERDICT,
        },
        "scalar_degeneration_note": (
            "Taking the second couplings equal to the first makes every matrix a scalar "
            "multiple of the identity.  Its commutator rows are identically zero and its rank "
            "drops, which is the expected degenerate behaviour and is retained as a control."
        ),
        "scope_limits": [
            "The second diagonal is now varied, but only along constants and second growth "
            "characters; the full second-diagonal freedom of the scalar variety is not swept.",
            "Finitely many points cannot decide the stratum; a uniform statement still needs "
            "the membership proved symbolically or over a cover.",
            "The upper stratum is not the unrestricted 955 profile, and the gauge torus cannot "
            "degenerate a mixed point into it.",
            "An in-span outcome reaches none of the three declared 955 terminals.",
        ],
        "solver_status": {
            "exact_sparse_QQ_linear_algebra_runs": len(verified),
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
        "verdict": GLOBAL_VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_second_diagonal_span_v042(root: Path) -> Path:
    payload = compile_second_diagonal_span_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_second_diagonal_span_v042(repository_root))
