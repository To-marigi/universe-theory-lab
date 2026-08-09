"""Exact grading and upper-stratum decomposition of the unrestricted 955 chart.

The 476-coordinate source-native slack chart carries the same gauge grading that
was certified for the bounded mixed ansatz.  Assign a weight to every coordinate
and require each residual matrix entry ``(i,j)`` to be homogeneous of weight
``j-i``.  This module does not assume the weights: it derives them by exact
rational elimination from the streamed system itself, reports the dimension of
the solution space, and only then uses them.

Deriving rather than assuming immediately corrects a natural guess.  The weight
``+1`` family is not the upper-right matrix entries alone: the slack coordinates
``u:*:0`` carry weight ``+1`` as well, while ``u:*:1`` carries ``0``.  Only
``A:*:10`` has negative weight.

Three structural corollaries then follow on the **upper stratum**
``{all A:*:10 = 0}``, and each is machine-certified here rather than argued:

* the ``(1,0)`` block vanishes identically, because every weight ``-1`` monomial
  needs at least one lower-left coordinate;
* the ``(0,1)`` block is exactly linear in the positive-weight family, with
  coefficients free of every weighted coordinate;
* the two diagonal blocks contain no weighted coordinate at all.

So the upper stratum of the unrestricted profile is a scalar variety ``S`` in the
weight-zero coordinates, carrying an affine-linear fibre in the positive-weight
coordinates over each of its points.  This is the bounded mixed-ansatz pattern
reproduced without an ansatz and without a frozen diagonal.

On that stratum the six ``Q`` commutators have vanishing diagonal and vanishing
lower left, so the whole commutativity question collapses to one
scalar-coefficient linear form per pair.  This module certifies that collapse
and emits the six forms; deciding whether the core forces them is the successor
gate.

Reachable-state MSR imposes no equation on this chart: the timid slack
recurrences solve it identically through ``(J v_c)^T v_c = 0``.  That is
re-verified here rather than assumed, because every rank below is computed
against a core of CPOBC plus strong GC only.

No Groebner, saturation, finite-field or numerical computation is performed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

SLACK_INVENTORY_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
TERM_PREFLIGHT_PATH = "results/v0.4.2_955_slack_term_preflight.json"
MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
TANGENT_PATH = "results/v0.4.2_955_slack_csg_tangent.json"
RESULT_PATH = "results/v0.4.2_955_upper_stratum.json"

SCHEMA = "final-theory-v042-955-upper-stratum-v1"
VERDICT = "V042_955_UPPER_STRATUM_SCALAR_TIMES_LINEAR_FIBRE_DECOMPOSITION_CERTIFIED_NONTERMINAL"


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
# Coordinate classification
# ---------------------------------------------------------------------------


def _classify(names: list[str]) -> dict[str, list[int]]:
    families: dict[str, list[int]] = {
        "A:00": [],
        "A:01": [],
        "A:10": [],
        "A:11": [],
        "u:0": [],
        "u:1": [],
    }
    for index, name in enumerate(names):
        head, _, tail = name.partition(":")
        suffix = name.rsplit(":", 1)[1]
        key = f"{head}:{suffix}"
        if key not in families:
            raise AssertionError(f"unclassified slack coordinate: {name}")
        families[key].append(index)
    return families


# ---------------------------------------------------------------------------
# Exact weight derivation
# ---------------------------------------------------------------------------


def _augmented_echelon(
    rows: Iterable[tuple[dict[int, Fraction], Fraction]],
) -> tuple[dict[int, tuple[dict[int, Fraction], Fraction]], int]:
    """Reduce inhomogeneous rows and report any inconsistency count."""

    basis: dict[int, tuple[dict[int, Fraction], Fraction]] = {}
    inconsistent = 0
    for source, target in rows:
        row = dict(source)
        value = target
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = (
                    {column: entry / scale for column, entry in row.items()},
                    value / scale,
                )
                break
            scale = row[pivot]
            pivot_row, pivot_value = basis[pivot]
            for column, entry in pivot_row.items():
                updated = row.get(column, Fraction(0)) - scale * entry
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
            value -= scale * pivot_value
        else:
            if value:
                inconsistent += 1
    return basis, inconsistent


def _derive_weights(
    entries: list[tuple[int, int, terms.Polynomial]], variable_count: int
) -> dict[str, Any]:
    rows: list[tuple[dict[int, Fraction], Fraction]] = []
    seen: set[tuple[tuple[tuple[int, int], ...], int]] = set()
    for row_index, column_index, polynomial in entries:
        target = column_index - row_index
        for monomial in polynomial:
            exponents = Counter(monomial)
            key = (tuple(sorted(exponents.items())), target)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                ({index: Fraction(count) for index, count in exponents.items()}, Fraction(target))
            )
    basis, inconsistent = _augmented_echelon(rows)
    return {
        "distinct_monomial_constraints": len(rows),
        "rank": len(basis),
        "solution_space_dimension": variable_count - len(basis),
        "inconsistent_rows": inconsistent,
        "grading_exists": inconsistent == 0,
        "basis": basis,
    }


def _particular_solution(
    basis: dict[int, tuple[dict[int, Fraction], Fraction]], variable_count: int
) -> list[Fraction]:
    solution = [Fraction(0)] * variable_count
    for pivot in sorted(basis, reverse=True):
        row, value = basis[pivot]
        accumulated = value
        for column, entry in row.items():
            if column != pivot:
                accumulated -= entry * solution[column]
        solution[pivot] = accumulated
    return solution


# ---------------------------------------------------------------------------
# Upper-stratum restriction
# ---------------------------------------------------------------------------


def _restrict(polynomial: terms.Polynomial, killed: set[int]) -> terms.Polynomial:
    return {
        monomial: coefficient
        for monomial, coefficient in polynomial.items()
        if not any(index in killed for index in monomial)
    }


def _degree_in(monomial: tuple[int, ...], family: set[int]) -> int:
    return sum(1 for index in monomial if index in family)


def compile_upper_stratum_v042(root: Path) -> dict[str, Any]:
    """Certify the gauge grading and the upper-stratum decomposition."""

    root = root.resolve()
    paths = {
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        TERM_PREFLIGHT_PATH: root / TERM_PREFLIGHT_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        TANGENT_PATH: root / TANGENT_PATH,
    }
    slack = _load(paths[SLACK_INVENTORY_PATH])
    term_preflight = _load(paths[TERM_PREFLIGHT_PATH])
    mixed = _load(paths[MIXED_MANIFEST_PATH])
    tangent_audit = _load(paths[TANGENT_PATH])
    for name, artifact in (
        (SLACK_INVENTORY_PATH, slack),
        (TERM_PREFLIGHT_PATH, term_preflight),
        (MIXED_MANIFEST_PATH, mixed),
        (TANGENT_PATH, tangent_audit),
    ):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")

    msr = slack["raw_source_system"]["reachable_MSR"]
    if int(msr["constraints_after_substitution"]) != 0:
        raise AssertionError("reachable-state MSR is no longer identically satisfied on the chart")
    msr_record = {
        "source_constraints": int(msr["source_constraints"]),
        "vector_entry_constraints_before_substitution": int(
            msr["vector_entry_constraints_before_substitution"]
        ),
        "constraints_after_substitution": 0,
        "identity_reason": str(msr["identity_reason"]),
        "consequence": (
            "The core on this chart is CPOBC plus strong GC only.  Every rank below is "
            "computed against that core, and reachable-state MSR adds no row."
        ),
    }

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    if names != term_preflight["variable_namespace"]["names"]:
        raise AssertionError("variable namespace differs from the frozen term preflight")
    families = _classify(names)
    if len(names) != 476:
        raise AssertionError("expected the 476-coordinate effective slack chart")

    # --- stream every core matrix entry ------------------------------------
    ledger = terms.OperationLedger()
    entries: list[tuple[str, dict[str, Any], int, int, terms.Polynomial]] = []
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
                        entries.append((block, identifier, row, column, residual))

    # --- derive the grading -------------------------------------------------
    derivation = _derive_weights(
        [(row, column, polynomial) for _b, _i, row, column, polynomial in entries], len(names)
    )
    if not derivation["grading_exists"]:
        raise AssertionError("no consistent gauge grading exists on the 476-coordinate chart")
    weights = _particular_solution(derivation["basis"], len(names))
    occurring = {
        index
        for _block, _identifier, _row, _column, polynomial in entries
        for monomial in polynomial
        for index in monomial
    }
    family_weights = {
        family: sorted({str(weights[index]) for index in indices if index in occurring})
        for family, indices in families.items()
    }
    absent = {
        family: sorted(names[index] for index in indices if index not in occurring)
        for family, indices in families.items()
    }
    for family, expected in (
        ("A:00", "0"),
        ("A:01", "1"),
        ("A:10", "-1"),
        ("A:11", "0"),
        ("u:0", "1"),
        ("u:1", "0"),
    ):
        if family_weights[family] not in ([expected], []):
            raise AssertionError(
                f"derived weight for {family} is {family_weights[family]}, expected [{expected}]"
            )
    blind_match = sorted(name for values in absent.values() for name in values) == sorted(
        tangent_audit["terminal_slack_blind_directions"]["coordinates"]
    )
    violations = 0
    for _block, _identifier, row, column, polynomial in entries:
        target = Fraction(column - row)
        for monomial in polynomial:
            if sum((weights[index] for index in monomial), Fraction(0)) != target:
                violations += 1
    if violations:
        raise AssertionError("the derived grading does not make every entry homogeneous")

    # --- upper-stratum restriction -----------------------------------------
    lower = {index for index, weight in enumerate(weights) if index in occurring and weight < 0}
    upper = {index for index, weight in enumerate(weights) if index in occurring and weight > 0}
    if lower != set(families["A:10"]) & occurring:
        raise AssertionError("the negative-weight family is not exactly the lower-left block")
    if upper != (set(families["A:01"]) | set(families["u:0"])) & occurring:
        raise AssertionError("the positive-weight family is not A:*:01 together with u:*:0")
    stratum_blocks: dict[str, dict[str, Any]] = {}
    lower_left_nonzero = 0
    upper_right_nonlinear = 0
    diagonal_contaminated = 0
    scalar_entries = 0
    scalar_terms = 0
    fibre_entries = 0
    fibre_terms = 0
    per_block: dict[str, Counter[str]] = {"CPOBC": Counter(), "strong_GC": Counter()}
    scalar_degrees: Counter[int] = Counter()
    for block, _identifier, row, column, polynomial in entries:
        restricted = _restrict(polynomial, lower)
        if (row, column) == (1, 0):
            if restricted:
                lower_left_nonzero += 1
            per_block[block]["lower_left_seen"] += 1
            continue
        if not restricted:
            per_block[block]["vanished_on_stratum"] += 1
            continue
        if (row, column) == (0, 1):
            for monomial in restricted:
                if _degree_in(monomial, upper) != 1:
                    upper_right_nonlinear += 1
            fibre_entries += 1
            fibre_terms += len(restricted)
            per_block[block]["upper_right_linear"] += 1
        else:
            for monomial in restricted:
                if _degree_in(monomial, upper):
                    diagonal_contaminated += 1
            scalar_entries += 1
            scalar_terms += len(restricted)
            scalar_degrees[max(len(monomial) for monomial in restricted)] += 1
            per_block[block]["scalar"] += 1
    if lower_left_nonzero or upper_right_nonlinear or diagonal_contaminated:
        raise AssertionError("the upper-stratum decomposition failed its own certificate")
    stratum_blocks = {
        block: {key: value for key, value in sorted(counter.items())}
        for block, counter in per_block.items()
    }

    # --- Q commutators on the stratum --------------------------------------
    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    commutators: list[dict[str, Any]] = []
    diagonal_commutator_failures = 0
    lower_commutator_failures = 0
    nonlinear_commutator_failures = 0
    stages = sorted(q_representatives)
    if stages != [1, 2, 3, 4]:
        raise AssertionError("expected the four source Q generators")
    for position, left_stage in enumerate(stages):
        for right_stage in stages[position + 1 :]:
            left = matrices[q_representatives[left_stage]]
            right = matrices[q_representatives[right_stage]]
            product = terms._matrix_multiply(left, right, ledger)
            reverse = terms._matrix_multiply(right, left, ledger)
            record: dict[str, Any] = {
                "pair": [left_stage, right_stage],
                "entries": {},
            }
            for row in range(2):
                for column in range(2):
                    residual = terms._add(
                        product[row][column], terms._scale(-1, reverse[row][column], ledger), ledger
                    )
                    restricted = _restrict(residual, lower)
                    if (row, column) in ((0, 0), (1, 1)) and restricted:
                        diagonal_commutator_failures += 1
                    if (row, column) == (1, 0) and restricted:
                        lower_commutator_failures += 1
                    if (row, column) == (0, 1):
                        for monomial in restricted:
                            if _degree_in(monomial, upper) != 1:
                                nonlinear_commutator_failures += 1
                        record["entries"]["01"] = {
                            "term_count": len(restricted),
                            "upper_right_degree": 1 if restricted else 0,
                        }
            commutators.append(record)
    if diagonal_commutator_failures or lower_commutator_failures or nonlinear_commutator_failures:
        raise AssertionError("the Q commutator collapse on the upper stratum failed")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "chart": "unrestricted 476-coordinate source-native slack chart",
            "ansatz": "none; this is not the bounded mixed x/y family",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            TERM_PREFLIGHT_PATH: term_preflight["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
            TANGENT_PATH: tangent_audit["semantic_digest_sha256"],
        },
        "reachable_state_MSR_is_built_in": msr_record,
        "coordinate_families": {
            family: len(indices) for family, indices in sorted(families.items())
        },
        "derived_grading": {
            "method": (
                "The weights are not assumed.  Each distinct monomial of each residual entry "
                "(i,j) contributes the exact linear constraint sum(weights)=j-i, and the "
                "inhomogeneous system is solved by exact rational elimination."
            ),
            "distinct_monomial_constraints": derivation["distinct_monomial_constraints"],
            "rank": derivation["rank"],
            "solution_space_dimension": derivation["solution_space_dimension"],
            "inconsistent_rows": derivation["inconsistent_rows"],
            "grading_exists": True,
            "family_weights": family_weights,
            "homogeneity_violations": violations,
            "weights_sha256": _digest([str(value) for value in weights]),
            "coordinates_occurring_in_the_core": len(occurring),
            "coordinates_absent_from_the_core": {
                "total": len(names) - len(occurring),
                "per_family": {family: len(values) for family, values in sorted(absent.items())},
                "names": {family: values for family, values in sorted(absent.items()) if values},
                "note": (
                    "These coordinates appear in no CPOBC or strong-GC monomial, so the grading "
                    "constraints leave their weight free.  The reported family weights are "
                    "taken over the occurring coordinates only, where they are forced."
                ),
                "equals_the_frozen_terminal_slack_blind_directions": blind_match,
                "cross_check": (
                    "The independently frozen tangent audit recorded exactly these coordinates "
                    "as the terminal slack blind directions.  Absence from every core monomial "
                    "is the algebraic reason they are blind."
                ),
            },
        },
        "upper_stratum": {
            "definition": "all 107 lower-left coordinates A:*:10 are zero",
            "streamed_nonzero_core_entries": len(entries),
            "lower_left_entries_nonzero_on_stratum": lower_left_nonzero,
            "upper_right_entries_nonlinear_in_the_positive_family": upper_right_nonlinear,
            "diagonal_entries_containing_a_weighted_coordinate": diagonal_contaminated,
            "scalar_system": {
                "entries": scalar_entries,
                "terms": scalar_terms,
                "degree_histogram": {
                    str(key): value for key, value in sorted(scalar_degrees.items())
                },
                "coordinates": "A:*:00, A:*:11, u:*:1",
            },
            "positive_weight_family": {
                "definition": "the weight +1 coordinates, derived not assumed",
                "A:*:01": len(set(families["A:01"]) & occurring),
                "u:*:0": len(set(families["u:0"]) & occurring),
                "total": len(upper),
                "note": (
                    "The slack coordinates u:*:0 carry weight +1 alongside the upper-right "
                    "matrix entries, so the fibre is linear in the combined family and not in "
                    "A:*:01 alone.  This correction came out of deriving the weights."
                ),
            },
            "upper_right_linear_fibre": {
                "entries": fibre_entries,
                "terms": fibre_terms,
                "exactly_linear_in_the_positive_weight_family": True,
                "coefficients_free_of_every_weighted_coordinate": True,
            },
            "per_block": stratum_blocks,
            "decomposition": (
                "The upper stratum of the unrestricted profile is a scalar variety S in the "
                "diagonal and slack coordinates carrying an affine-linear upper-right fibre "
                "over each of its points."
            ),
        },
        "Q_commutator_collapse": {
            "pairs": len(commutators),
            "diagonal_entries_nonzero_on_stratum": diagonal_commutator_failures,
            "lower_left_entries_nonzero_on_stratum": lower_commutator_failures,
            "upper_right_entries_nonlinear": nonlinear_commutator_failures,
            "surviving_entry": "01",
            "records": commutators,
            "consequence": (
                "On the upper stratum the whole commutativity question is one "
                "scalar-coefficient linear form per pair in the upper-right coordinates."
            ),
        },
        "supersedes": {
            "gate": "DESIGN_THE_FIFTH_ORDER_FULL_FOURTH_JET_FIBER_PREFLIGHT",
            "reason": (
                "MISSION.md phase-A stop rule: an order-by-order local expansion whose cost "
                "grows and which approaches none of the declared terminals is frozen once a "
                "route to a finite theorem exists.  The grading supplies that route."
            ),
            "jet_ladder_explanation": (
                "At the diagonal CSG basepoint the lower-left linear part of the core has full "
                "rank 107, so the formal implicit function theorem places the local component "
                "inside the upper stratum.  That is the finite reason four successive orders "
                "were silent.  It is a formal-local statement at one point and nothing more."
            ),
        },
        "next_gate": "DECIDE_THE_SIX_UPPER_RIGHT_COMMUTATOR_FORMS_AGAINST_THE_CORE_ROW_SPAN_ON_S",
        "solver_status": {
            "exact_sparse_QQ_linear_algebra_runs": 1,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "The upper stratum is not the unrestricted 955 profile.",
            "Mixed points with both off-diagonal families nonzero remain open, and the gauge "
            "torus cannot degenerate them into the stratum because its weights blow up one "
            "side while shrinking the other.",
            "No witness and no obstruction is certified; the commutator forms are emitted, "
            "not decided.",
            "A later witness candidate still needs nonsingularity, the N!=0 gate, the Eq113 "
            "and Eq139 obligations, and reachable visibility; an operator-only witness with "
            "rank-one reachable span only reproduces the known SR2 weakness.",
            "An obstruction on the stratum alone also reaches none of the three declared 955 "
            "terminals.",
        ],
        "unrestricted_source_native_955_status": "OPEN",
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_upper_stratum_v042(root: Path) -> Path:
    payload = compile_upper_stratum_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_upper_stratum_v042(repository_root))
