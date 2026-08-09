"""Exact row-span decision for the six 955 upper-stratum commutator forms.

The upper-stratum gate reduced the commutativity question on the unrestricted
476-coordinate chart to this: over a point ``s`` of the scalar variety ``S``, the
core's ``(0,1)`` block is a homogeneous linear system ``L(s)`` in the 123
positive-weight coordinates, and each of the six ``Q`` commutators is a four-term
linear form ``c_k(s)`` in the same coordinates.  Every point of the fibre over
``s`` has commuting ``Q`` exactly when all six forms lie in the row span of
``L(s)``.

This module decides that membership at exact rational points of ``S`` supplied by
the classical sequential-growth family with general couplings ``t_0,...,t_4``.
Each candidate point is first verified to be an exact core solution -- every
CPOBC and strong-GC matrix entry must evaluate to zero -- and a coupling whose
point fails that check, or whose construction is undefined, is recorded with its
exact reason rather than repaired.

The verdict strings were fixed before any measurement, in
``reports/v0.4.2_955_commutator_span_gate_design.md``.  Both branches are
terminal-shaped: an escape is a witness candidate carrying explicit unmet
obligations, and an in-span result is obstruction evidence that reaches none of
the three declared 955 terminals.

Scope limit worth stating at the top: the sequential-growth family fixes the
second diagonal entry of every transition to one, so it varies ``A:*:00`` across
couplings but never ``A:*:11``.  Points of ``S`` with a genuinely free second
diagonal are outside what this gate samples.

No Groebner, saturation, finite-field or numerical computation is performed.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as stratum
from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

SLACK_INVENTORY_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
UPPER_STRATUM_PATH = "results/v0.4.2_955_upper_stratum.json"
RESULT_PATH = "results/v0.4.2_955_commutator_span.json"

SCHEMA = "final-theory-v042-955-commutator-span-v1"

IN_SPAN_VERDICT = "V042_955_UPPER_STRATUM_COMMUTATOR_FORMS_IN_CORE_ROW_SPAN_AT_POINT_CERTIFIED"
ESCAPE_VERDICT = "V042_955_UPPER_STRATUM_COMMUTATOR_ESCAPE_AT_POINT_CERTIFIED"
GLOBAL_VERDICT = "V042_955_UPPER_STRATUM_SPAN_POINTWISE_EVIDENCE_ONLY_NONTERMINAL"

#: Deterministic coupling list.  The all-ones entry is the frozen basepoint and
#: acts as the control; the rest are generic positive rationals plus two
#: deliberately degenerate choices retained for their exact rejection reasons.
COUPLINGS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("control_all_ones", (1, 1, 1, 1, 1)),
    ("generic_1_2_3_5_7", (1, 2, 3, 5, 7)),
    ("generic_2_1_4_1_3", (2, 1, 4, 1, 3)),
    ("generic_3_1_1_1_1", (3, 1, 1, 1, 1)),
    ("degenerate_zero_odd", (1, 0, 1, 0, 1)),
    ("degenerate_negative", (1, -2, 3, -4, 5)),
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


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# General-coupling sequential-growth characters
# ---------------------------------------------------------------------------


class UnusableCoupling(Exception):
    """Raised when a coupling choice makes the growth characters undefined."""


def _lambda(upper: int, lower: int, couplings: Sequence[Fraction]) -> Fraction:
    """Eq. (15)'s ``lambda(a,b)``, matching ``commutative_csg_v031.lambda_value``."""

    if not 0 <= lower <= upper:
        raise ValueError("lambda indices must satisfy 0 <= b <= a")
    total = Fraction(0)
    for index in range(lower, upper + 1):
        total += math.comb(upper - lower, index - lower) * couplings[index]
    return total


def _characters(reduction: dict[str, Any], couplings: Sequence[Fraction]) -> dict[str, Fraction]:
    """Return the exact growth character of every ON orbit for these couplings."""

    values: dict[str, Fraction] = {}
    for record in reduction["reduction_map"]:
        orbit = str(record["orbit_id"])
        relation = tuple(int(row) for row in record["source_relation_rows"])
        precursor = int(record["precursor_code"])
        source_size = len(relation)
        denominator = _lambda(source_size, 0, couplings)
        if not denominator:
            raise UnusableCoupling(f"lambda({source_size},0)=0; the coupling is not usable")
        maximal_count = len(maximal_elements_in_subset(relation, precursor))
        value = _lambda(precursor.bit_count(), maximal_count, couplings) / denominator
        previous = values.setdefault(orbit, value)
        if previous != value:
            raise AssertionError(f"orbit {orbit} has two distinct growth characters")
    if len(values) != 131:
        raise AssertionError("expected 131 ON orbit characters")
    return values


def _mixed_with_characters(
    mixed: dict[str, Any], characters: dict[str, Fraction]
) -> dict[str, Any]:
    variables = dict(mixed["variables"])
    variables["CSG_diagonal_character"] = {
        orbit: str(value) for orbit, value in sorted(characters.items())
    }
    replaced = dict(mixed)
    replaced["variables"] = variables
    return replaced


# ---------------------------------------------------------------------------
# Exact rational linear algebra
# ---------------------------------------------------------------------------


def _rank(rows: Sequence[dict[int, Fraction]]) -> int:
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


def _linear_row(
    polynomial: terms.Polynomial,
    assignment: list[Fraction],
    positive: dict[int, int],
) -> tuple[dict[int, Fraction], int]:
    """Evaluate the weight-zero part of a stratum-restricted linear entry."""

    row: dict[int, Fraction] = {}
    violations = 0
    for monomial, coefficient in polynomial.items():
        carried = [index for index in monomial if index in positive]
        if len(carried) != 1:
            violations += 1
            continue
        column = positive[carried[0]]
        value = Fraction(coefficient)
        seen = False
        for index in monomial:
            if index == carried[0] and not seen:
                seen = True
                continue
            value *= assignment[index]
        if value:
            row[column] = row.get(column, Fraction(0)) + value
            if not row[column]:
                row.pop(column)
    return row, violations


def _evaluate(polynomial: terms.Polynomial, assignment: list[Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in polynomial.items():
        value = Fraction(coefficient)
        for index in monomial:
            value *= assignment[index]
        total += value
    return total


def compile_commutator_span_v042(root: Path) -> dict[str, Any]:
    """Decide the six upper-stratum commutator forms at general-coupling points."""

    root = root.resolve()
    paths = {
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        UPPER_STRATUM_PATH: root / UPPER_STRATUM_PATH,
    }
    slack = _load(paths[SLACK_INVENTORY_PATH])
    mixed = _load(paths[MIXED_MANIFEST_PATH])
    reduction = _load(paths[REDUCTION_PATH])
    upper = _load(paths[UPPER_STRATUM_PATH])
    for name, artifact in (
        (SLACK_INVENTORY_PATH, slack),
        (MIXED_MANIFEST_PATH, mixed),
        (UPPER_STRATUM_PATH, upper),
    ):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if upper.get("verdict") != stratum.VERDICT:
        raise AssertionError("the upper-stratum predecessor is not at its certified verdict")

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    families = stratum._classify(names)
    lower_indices = set(families["A:10"])
    positive_names = sorted(
        set(families["A:01"]) | set(families["u:0"]),
        key=lambda index: names[index],
    )
    frozen_positive = upper["upper_stratum"]["positive_weight_family"]["total"]

    # The frozen upper-stratum gate counts only the positive-weight coordinates
    # that actually occur in the core.  Recover exactly that set here.
    ledger = terms.OperationLedger()
    core_records: list[tuple[str, dict[str, Any], int, int, terms.Polynomial]] = []
    for block, records, identifier_keys in (
        ("CPOBC", slack["raw_source_system"]["CPOBC_equations"], ("relation_id", "equation_id")),
        (
            "strong_GC",
            slack["raw_source_system"]["strong_GC_basis"],
            ("relation_id", "endpoint_causet_id"),
        ),
    ):
        for record in records:
            left = terms._word_matrix(record["lhs_source_word"], matrices, ledger)
            right = terms._word_matrix(record["rhs_source_word"], matrices, ledger)
            identifier = {key: record[key] for key in identifier_keys if key in record}
            for row in range(2):
                for column in range(2):
                    residual = terms._add(
                        left[row][column], terms._scale(-1, right[row][column], ledger), ledger
                    )
                    if residual:
                        core_records.append((block, identifier, row, column, residual))
    occurring = {
        index
        for _b, _i, _r, _c, polynomial in core_records
        for monomial in polynomial
        for index in monomial
    }
    positive_indices = [index for index in positive_names if index in occurring]
    if len(positive_indices) != frozen_positive:
        raise AssertionError("positive-weight family disagrees with the frozen upper-stratum gate")
    positive = {index: column for column, index in enumerate(positive_indices)}

    upper_right = [
        (block, identifier, polynomial)
        for block, identifier, row, column, polynomial in core_records
        if (row, column) == (0, 1)
    ]
    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    stages = sorted(q_representatives)
    commutator_entries: list[tuple[tuple[int, int], terms.Polynomial]] = []
    for position, left_stage in enumerate(stages):
        for right_stage in stages[position + 1 :]:
            left = matrices[q_representatives[left_stage]]
            right = matrices[q_representatives[right_stage]]
            product = terms._matrix_multiply(left, right, ledger)
            reverse = terms._matrix_multiply(right, left, ledger)
            residual = terms._add(product[0][1], terms._scale(-1, reverse[0][1], ledger), ledger)
            commutator_entries.append(((left_stage, right_stage), residual))

    frozen_characters = {
        orbit: Fraction(str(value))
        for orbit, value in mixed["variables"]["CSG_diagonal_character"].items()
    }

    evaluated: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for label, integers in COUPLINGS:
        couplings = [Fraction(value) for value in integers]
        try:
            characters = _characters(reduction, couplings)
        except UnusableCoupling as error:
            rejected.append(
                {
                    "label": label,
                    "couplings": [str(value) for value in couplings],
                    "stage": "character_construction",
                    "reason": str(error),
                }
            )
            continue
        if label == "control_all_ones" and characters != frozen_characters:
            raise AssertionError("the all-ones couplings do not reproduce the frozen characters")
        try:
            assignment, _basepoint, _target = tangent._build_csg_assignment(
                slack, _mixed_with_characters(mixed, characters), matrices, names
            )
        except AssertionError as error:
            rejected.append(
                {
                    "label": label,
                    "couplings": [str(value) for value in couplings],
                    "stage": "assignment_construction",
                    "reason": str(error),
                }
            )
            continue
        if any(assignment[index] for index in lower_indices):
            raise AssertionError("the growth assignment left the upper stratum")

        residual_failures = sum(
            1 for _b, _i, _r, _c, polynomial in core_records if _evaluate(polynomial, assignment)
        )
        if residual_failures:
            rejected.append(
                {
                    "label": label,
                    "couplings": [str(value) for value in couplings],
                    "stage": "core_verification",
                    "reason": "the point is not an exact core solution",
                    "nonzero_core_entries": residual_failures,
                    "streamed_core_entries": len(core_records),
                }
            )
            continue

        rows: list[dict[int, Fraction]] = []
        violations = 0
        for _block, _identifier, polynomial in upper_right:
            restricted = stratum._restrict(polynomial, lower_indices)
            row, failed = _linear_row(restricted, assignment, positive)
            violations += failed
            rows.append(row)
        if violations:
            raise AssertionError("a stratum (0,1) entry was not linear in the positive family")
        base_rank = _rank(rows)

        pair_records = []
        escapes = 0
        for pair, polynomial in commutator_entries:
            restricted = stratum._restrict(polynomial, lower_indices)
            row, failed = _linear_row(restricted, assignment, positive)
            if failed:
                raise AssertionError("a commutator entry was not linear in the positive family")
            augmented = _rank([*rows, row])
            in_span = augmented == base_rank
            if not in_span:
                escapes += 1
            pair_records.append(
                {
                    "pair": list(pair),
                    "polynomial_monomials_before_evaluation": len(restricted),
                    "nonzero_columns_after_evaluation": len(row),
                    "augmented_rank": augmented,
                    "rank_increment": augmented - base_rank,
                    "status": "IN_SPAN" if in_span else "OUTSIDE_SPAN",
                }
            )
        evaluated.append(
            {
                "label": label,
                "couplings": [str(value) for value in couplings],
                "characters_sha256": _digest(
                    {orbit: str(value) for orbit, value in sorted(characters.items())}
                ),
                "distinct_characters": sorted({str(value) for value in characters.values()}),
                "streamed_core_entries": len(core_records),
                "nonzero_core_entries": 0,
                "L_shape": [len(rows), len(positive_indices)],
                "L_rank": base_rank,
                "fibre_dimension": len(positive_indices) - base_rank,
                "pairs": pair_records,
                "escapes": escapes,
                "verdict": ESCAPE_VERDICT if escapes else IN_SPAN_VERDICT,
            }
        )

    if not evaluated:
        raise AssertionError("no coupling produced an exact core point")
    total_escapes = sum(record["escapes"] for record in evaluated)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "gate_design": "reports/v0.4.2_955_commutator_span_gate_design.md",
        "verdict_strings_fixed_before_measurement": True,
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "chart": "unrestricted 476-coordinate source-native slack chart",
            "locus": "upper stratum, all 107 lower-left coordinates zero",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            UPPER_STRATUM_PATH: upper["semantic_digest_sha256"],
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
        },
        "commutator_shape": {
            "unevaluated_monomials_per_pair": 4,
            "nonzero_columns_after_evaluating_the_diagonal": 2,
            "reason": (
                "For upper-triangular Q_i=[[a_i,b_i],[0,d_i]] the (0,1) commutator entry is "
                "(a_i-d_i)b_j-(a_j-d_j)b_i.  Four monomials collapse onto the two columns b_i "
                "and b_j once the weight-zero diagonal is evaluated at the point."
            ),
        },
        "question": (
            "Over a point s of the scalar variety S the core (0,1) block is a homogeneous "
            "linear system L(s) in the 123 positive-weight coordinates and each Q commutator "
            "is a four-term linear form.  Every fibre point over s has commuting Q exactly "
            "when all six forms lie in the row span of L(s)."
        ),
        "growth_characters": {
            "formula": "A = lambda(varpi,m)/lambda(n,0) with lambda(a,b)=sum_k C(a-b,k-b) t_k",
            "reference_implementation": (
                "src/universe_lab/final_theory/commutative_csg_v031.py: lambda_value and "
                "transition_amplitude"
            ),
            "control_reproduces_frozen_characters": True,
            "couplings_used": 5,
        },
        "evaluated_points": evaluated,
        "rejected_couplings": rejected,
        "aggregate": {
            "points_verified_as_exact_core_solutions": len(evaluated),
            "points_with_an_escape": sum(1 for record in evaluated if record["escapes"]),
            "total_escapes": total_escapes,
            "L_rank_values": sorted({record["L_rank"] for record in evaluated}),
            "fibre_dimension_values": sorted({record["fibre_dimension"] for record in evaluated}),
            "verdict": GLOBAL_VERDICT,
        },
        "scope_limits": [
            "The growth family fixes A:*:11 to one at every transition, so these points vary "
            "the first diagonal entry across couplings but never the second.  Points of S "
            "with a free second diagonal are not sampled here.",
            "Finitely many points of S cannot decide the stratum; a uniform statement needs "
            "the membership proved symbolically or over a cover of S.",
            "The upper stratum is not the unrestricted 955 profile, and the gauge torus "
            "cannot degenerate a mixed point into it.",
            "An in-span outcome reaches none of the three declared 955 terminals.",
            "An escape would be a witness candidate only, still owing nonsingularity, the "
            "N!=0 gate, the Eq113 and Eq139 branches, exact rationality and above all "
            "reachable visibility.",
        ],
        "solver_status": {
            "exact_sparse_QQ_linear_algebra_runs": len(evaluated),
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


def write_commutator_span_v042(root: Path) -> Path:
    payload = compile_commutator_span_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_commutator_span_v042(repository_root))
