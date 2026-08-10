"""Audit the Lambda row-span question on nontrivial upper-stratum fibres.

The preceding Eq. (120) gate reduced the six upper-right commutators to one
scalar ``Lambda`` on the open set

    D = a_1*d_4 - a_4*d_1 != 0.

Its stored numerical cross-check used the zero section of the positive-weight
fibre (all ``A:*:01`` coordinates were zero), so it did not test Lambda on a
nonzero fibre vector.  This gate closes that bookkeeping gap without claiming
the unrestricted theorem.

It performs two exact audits:

* four rational points of the growth upper-stratum family, where a nonzero
  vector in ``ker L`` is reconstructed and the pure-Q elimination is done over
  ``QQ``;
* a two-parameter symbolic family with first diagonal couplings
  ``(1,1,1,1,t)`` and constant second diagonal ``s``.  The whole 4,152-entry
  scalar core and the pure-Q elimination are checked over ``QQ(t,s)``.

In both audits the non-Q elimination has rank 111, the pure-Q residual space
has rank 3, and the Lambda row has zero remainder.  This is a uniform result
  on the declared two-parameter subfamily and pointwise evidence on the four
fibres.  The full scalar variety S is larger; no density, irreducibility, or
global row-module certificate is asserted here.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_commutator_span_v042 as span
from universe_lab.final_theory import source_native_955_growth_family_identity_v042 as growth
from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as stratum

SLACK_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
MIXED_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
RESULT_PATH = "results/v0.4.2_955_lambda_fibre_audit.json"

SCHEMA = "final-theory-v042-955-lambda-fibre-audit-v1"
VERDICT = "V042_955_LAMBDA_ZERO_ON_CERTIFIED_FIBRE_FAMILY_FULL_S_OPEN"

POINT_COUPLINGS = (
    ("control_all_ones", (1, 1, 1, 1, 1)),
    ("general_1_2_3_5_7", (1, 2, 3, 5, 7)),
    ("general_2_1_4_1_3", (2, 1, 4, 1, 3)),
    ("general_3_1_1_1_1", (3, 1, 1, 1, 1)),
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


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


def _prepare(root: Path) -> dict[str, Any]:
    slack = _load(root / SLACK_PATH)
    mixed = _load(root / MIXED_PATH)
    reduction = _load(root / REDUCTION_PATH)
    for name, artifact in ((SLACK_PATH, slack), (MIXED_PATH, mixed)):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    families = stratum._classify(names)
    lower = set(families["A:10"])
    occurring: set[int] = set()
    core: list[terms.Polynomial] = []
    upper_right: list[terms.Polynomial] = []
    ledger = terms.OperationLedger()
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
                        left[row][column],
                        terms._scale(-1, right[row][column], ledger),
                        ledger,
                    )
                    if not residual:
                        continue
                    core.append(residual)
                    occurring.update(index for monomial in residual for index in monomial)
                    if (row, column) == (0, 1):
                        upper_right.append(residual)

    positive_indices = [
        index
        for index in sorted(
            set(families["A:01"]) | set(families["u:0"]), key=lambda item: names[item]
        )
        if index in occurring
    ]
    if len(names) != 476 or len(core) != 4152 or len(upper_right) != 1038:
        raise AssertionError("the upper-stratum source system shape changed")
    if len(positive_indices) != 123:
        raise AssertionError("the positive-weight fibre dimension changed")

    representative_to_orbit = {
        str(record["representative_occurrence_id"]): str(record["orbit_id"])
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    timid = {
        str(record["timid_orbit_representative"])
        for record in slack["timid_slack_recurrences"]
    }
    canonical_paths = {
        str(record["source_id"]): list(record["operator_word_later_on_left"])
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    timid_representative = {
        str(record["source_id"]): str(record["timid_orbit_representative"])
        for record in slack["timid_slack_recurrences"]
    }
    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    if q_representatives != {
        1: "cpobc-transition-7137acaa934673cc789d",
        2: "cpobc-transition-3b93b9f523031a23c77f",
        3: "cpobc-transition-779d09aa463a38abdba6",
        4: "cpobc-transition-9fabc20614d5b2aa595d",
    }:
        raise AssertionError("the source-native Q stage mapping changed")

    return {
        "slack": slack,
        "mixed": mixed,
        "reduction": reduction,
        "names": names,
        "index_of": {name: index for index, name in enumerate(names)},
        "matrices": matrices,
        "families": families,
        "lower": lower,
        "positive_indices": positive_indices,
        "positive": {index: column for column, index in enumerate(positive_indices)},
        "core": core,
        "upper_right": upper_right,
        "representative_to_orbit": representative_to_orbit,
        "timid": timid,
        "canonical_paths": canonical_paths,
        "timid_representative": timid_representative,
        "q_representatives": q_representatives,
    }


def _characters_by_representative(
    context: dict[str, Any], couplings: tuple[int, ...]
) -> dict[str, Fraction]:
    orbit_values = span._characters(
        context["reduction"], [Fraction(value) for value in couplings]
    )
    return {
        representative: orbit_values[orbit]
        for representative, orbit in context["representative_to_orbit"].items()
    }


def _build_assignment(
    context: dict[str, Any],
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    symbolic: bool,
) -> list[Any]:
    names = context["names"]
    index_of = context["index_of"]
    assignment: list[Any] = [sympy.Integer(0) if symbolic else Fraction(0)] * len(names)
    for representative in set(context["matrices"]) - context["timid"]:
        assignment[index_of[f"A:{representative}:00"]] = first[representative]
        assignment[index_of[f"A:{representative}:11"]] = second[representative]

    for record in context["slack"]["timid_slack_recurrences"]:
        source_id = str(record["source_id"])
        product: Any = sympy.Integer(1) if symbolic else Fraction(1)
        for symbol in context["canonical_paths"][source_id]:
            product *= first[terms._operator(symbol)]
        if product == 0:
            raise AssertionError(f"the reachable state vanished at {source_id}")
        base: Any = sympy.Integer(1) if symbolic else Fraction(1)
        for operator, coefficient in zip(
            record["non_timid_orbit_representatives"],
            record["non_timid_coefficients"],
            strict=True,
        ):
            base -= int(coefficient) * second[str(operator)]
        target = second[context["timid_representative"][source_id]]
        value = (target - base) / product
        assignment[index_of[f"u:{source_id}:0"]] = (
            sympy.Integer(0) if symbolic else Fraction(0)
        )
        assignment[index_of[f"u:{source_id}:1"]] = sympy.cancel(value) if symbolic else value
    return assignment


def _evaluate(polynomial: terms.Polynomial, assignment: list[Any], *, symbolic: bool) -> Any:
    total: Any = sympy.Integer(0) if symbolic else Fraction(0)
    for monomial, coefficient in polynomial.items():
        value: Any = sympy.Integer(coefficient) if symbolic else Fraction(coefficient)
        for index in monomial:
            value *= assignment[index]
        total += value
    return sympy.cancel(total) if symbolic else total


def _linear_rows(
    context: dict[str, Any], assignment: list[Any], *, symbolic: bool
) -> list[dict[int, Any]]:
    rows: list[dict[int, Any]] = []
    positive = context["positive"]
    for polynomial in context["upper_right"]:
        restricted = stratum._restrict(polynomial, context["lower"])
        row: dict[int, Any] = {}
        for monomial, coefficient in restricted.items():
            carried = [index for index in monomial if index in positive]
            if len(carried) != 1:
                raise AssertionError("an upper-right core entry is not linear in the fibre")
            carried_index = carried[0]
            value: Any = sympy.Integer(coefficient) if symbolic else Fraction(coefficient)
            seen = False
            for index in monomial:
                if index == carried_index and not seen:
                    seen = True
                    continue
                value *= assignment[index]
            value = sympy.cancel(value) if symbolic else value
            column = positive[carried_index]
            updated = row.get(column, sympy.Integer(0) if symbolic else Fraction(0)) + value
            updated = sympy.cancel(updated) if symbolic else updated
            if updated:
                row[column] = updated
            else:
                row.pop(column, None)
        rows.append(row)
    return rows


def _subtract(
    row: dict[int, Any], basis_row: dict[int, Any], scale: Any, *, symbolic: bool
) -> None:
    zero = sympy.Integer(0) if symbolic else Fraction(0)
    for column, value in basis_row.items():
        updated = row.get(column, zero) - scale * value
        updated = sympy.cancel(updated) if symbolic else updated
        if updated:
            row[column] = updated
        else:
            row.pop(column, None)


def _independent_basis(
    rows: list[dict[int, Any]], *, allowed: set[int], symbolic: bool
) -> dict[int, dict[int, Any]]:
    basis: dict[int, dict[int, Any]] = {}
    for source in rows:
        row = dict(source)
        while True:
            pivot = min((column for column in row if column in allowed), default=None)
            if pivot is None:
                break
            if pivot not in basis:
                scale = row[pivot]
                row = {
                    column: sympy.cancel(value / scale) if symbolic else value / scale
                    for column, value in row.items()
                }
                basis[pivot] = row
                break
            _subtract(row, basis[pivot], row[pivot], symbolic=symbolic)
    return basis


def _pure_q_elimination(
    rows: list[dict[int, Any]], q_columns: dict[int, int], *, symbolic: bool
) -> dict[str, Any]:
    q_set = set(q_columns.values())
    non_q = set(range(123)) - q_set
    non_q_basis: dict[int, dict[int, Any]] = {}
    pure_rows: list[dict[int, Any]] = []
    for source in rows:
        row = dict(source)
        while True:
            pivot = min((column for column in row if column in non_q), default=None)
            if pivot is None:
                break
            if pivot not in non_q_basis:
                scale = row[pivot]
                row = {
                    column: sympy.cancel(value / scale) if symbolic else value / scale
                    for column, value in row.items()
                }
                non_q_basis[pivot] = row
                break
            _subtract(row, non_q_basis[pivot], row[pivot], symbolic=symbolic)
        if not any(column in non_q for column in row):
            q_row = {column: value for column, value in row.items() if column in q_set}
            if q_row:
                pure_rows.append(q_row)

    pure_basis = _independent_basis(pure_rows, allowed=q_set, symbolic=symbolic)
    return {
        "non_q_rank": len(non_q_basis),
        "pure_rows": len(pure_rows),
        "pure_q_rank": len(pure_basis),
        "pure_basis": pure_basis,
    }


def _lambda_remainder(
    context: dict[str, Any], assignment: list[Any], pure: dict[str, Any], *, symbolic: bool
) -> tuple[Any, dict[int, Any], dict[int, Any]]:
    index_of = context["index_of"]
    q = context["q_representatives"]
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
    lambda_row = {
        q_columns[1]: d[4] - a[4],
        q_columns[4]: a[1] - d[1],
    }
    remainder = dict(lambda_row)
    for pivot in sorted(pure["pure_basis"]):
        if pivot not in remainder:
            continue
        _subtract(remainder, pure["pure_basis"][pivot], remainder[pivot], symbolic=symbolic)
    denominator = a[1] * d[4] - a[4] * d[1]
    return denominator, lambda_row, remainder


def _numeric_kernel_q_vector(
    rows: list[dict[int, Fraction]], q_columns: dict[int, int]
) -> dict[int, Fraction]:
    """Return one exact nonzero Q-visible vector in the kernel of L."""

    basis = _independent_basis(rows, allowed=set(range(123)), symbolic=False)
    pivots = sorted(basis)
    free = [column for column in range(123) if column not in basis]
    q_set = set(q_columns.values())
    for free_column in free:
        vector: dict[int, Fraction] = {free_column: Fraction(1)}
        for pivot in reversed(pivots):
            value = sum(
                basis[pivot].get(column, Fraction(0)) * vector.get(column, Fraction(0))
                for column in basis[pivot]
                if column != pivot
            )
            if value:
                vector[pivot] = -value
        if any(vector.get(column, Fraction(0)) for column in q_set):
            for row in rows:
                if sum(value * vector.get(column, Fraction(0)) for column, value in row.items()):
                    break
            else:
                return {
                    stage: vector.get(column, Fraction(0))
                    for stage, column in q_columns.items()
                }
    raise AssertionError("no Q-visible fibre kernel vector was found")


def compile_lambda_fibre_audit_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    context = _prepare(root)
    point_records: list[dict[str, Any]] = []
    for label, coupling_values in POINT_COUPLINGS:
        first = _characters_by_representative(context, coupling_values)
        second = {representative: Fraction(1) for representative in first}
        assignment = _build_assignment(context, first, second, symbolic=False)
        core_failures = sum(
            bool(_evaluate(polynomial, assignment, symbolic=False))
            for polynomial in context["core"]
        )
        rows = _linear_rows(context, assignment, symbolic=False)
        pure = _pure_q_elimination(rows, {
            stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
            for stage, representative in context["q_representatives"].items()
        }, symbolic=False)
        denominator, lambda_row, remainder = _lambda_remainder(
            context, assignment, pure, symbolic=False
        )
        q_columns = {
            stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
            for stage, representative in context["q_representatives"].items()
        }
        kernel_q = _numeric_kernel_q_vector(rows, q_columns)
        lambda_on_kernel = (
            (assignment[context["index_of"][f"A:{context['q_representatives'][1]}:00"]]
             - assignment[context["index_of"][f"A:{context['q_representatives'][1]}:11"]])
            * kernel_q[4]
            - (assignment[context["index_of"][f"A:{context['q_representatives'][4]}:00"]]
               - assignment[context["index_of"][f"A:{context['q_representatives'][4]}:11"]])
            * kernel_q[1]
        )
        if core_failures or denominator == 0 or remainder or lambda_on_kernel:
            raise AssertionError(f"numeric Lambda audit failed at {label}")
        point_records.append(
            {
                "label": label,
                "couplings": [str(value) for value in coupling_values],
                "core_failures": core_failures,
                "rows": len(rows),
                "non_q_rank": pure["non_q_rank"],
                "pure_rows": pure["pure_rows"],
                "pure_q_rank": pure["pure_q_rank"],
                "D": str(denominator),
                "lambda_row_remainder_terms": len(remainder),
                "q_visible_kernel": {str(stage): str(value) for stage, value in kernel_q.items()},
                "kernel_q_is_nonzero": any(kernel_q.values()),
                "lambda_on_kernel": str(lambda_on_kernel),
            }
        )

    # The Eq120 collapse used D != 0 as a pivot.  Audit one exact point on the
    # complementary D = 0 locus separately, without dividing by D.  This is a
    # branch sample only; it is not a claim about the whole degenerate locus.
    degenerate_couplings = (1, 1, 1, 1, -13)
    degenerate_first = _characters_by_representative(context, degenerate_couplings)
    degenerate_second = {
        representative: Fraction(2) for representative in degenerate_first
    }
    degenerate_assignment = _build_assignment(
        context, degenerate_first, degenerate_second, symbolic=False
    )
    degenerate_core_failures = sum(
        bool(_evaluate(polynomial, degenerate_assignment, symbolic=False))
        for polynomial in context["core"]
    )
    degenerate_rows = _linear_rows(context, degenerate_assignment, symbolic=False)
    degenerate_q_columns = {
        stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
        for stage, representative in context["q_representatives"].items()
    }
    degenerate_pure = _pure_q_elimination(
        degenerate_rows, degenerate_q_columns, symbolic=False
    )
    degenerate_D, _degenerate_lambda, degenerate_remainder = _lambda_remainder(
        context, degenerate_assignment, degenerate_pure, symbolic=False
    )
    degenerate_kernel_q = _numeric_kernel_q_vector(
        degenerate_rows, degenerate_q_columns
    )
    degenerate_lambda_on_kernel = (
        (degenerate_assignment[
            context["index_of"][
                f"A:{context['q_representatives'][1]}:00"
            ]
        ] - degenerate_assignment[
            context["index_of"][
                f"A:{context['q_representatives'][1]}:11"
            ]
        ])
        * degenerate_kernel_q[4]
        - (degenerate_assignment[
            context["index_of"][
                f"A:{context['q_representatives'][4]}:00"
            ]
        ] - degenerate_assignment[
            context["index_of"][
                f"A:{context['q_representatives'][4]}:11"
            ]
        ])
        * degenerate_kernel_q[1]
    )
    degenerate_determinants = []
    for matrix in context["matrices"].values():
        evaluated = [
            [_evaluate(cell, degenerate_assignment, symbolic=False) for cell in row]
            for row in matrix
        ]
        degenerate_determinants.append(
            evaluated[0][0] * evaluated[1][1]
            - evaluated[0][1] * evaluated[1][0]
        )
    degenerate_determinant_failures = sum(
        not determinant for determinant in degenerate_determinants
    )
    if (
        degenerate_core_failures
        or degenerate_D
        or degenerate_remainder
        or degenerate_lambda_on_kernel
        or degenerate_determinant_failures
    ):
        raise AssertionError("the D=0 Lambda branch audit failed")

    parameter, second_parameter = sympy.symbols("t s")
    first_orbit, _denominators = growth._symbolic_characters(
        context["reduction"], (1, 1, 1, 1, parameter)
    )
    first_symbolic = {
        representative: first_orbit[orbit]
        for representative, orbit in context["representative_to_orbit"].items()
    }
    second_symbolic = {
        representative: second_parameter for representative in first_symbolic
    }
    symbolic_assignment = _build_assignment(
        context, first_symbolic, second_symbolic, symbolic=True
    )
    symbolic_core_failures = sum(
        bool(_evaluate(polynomial, symbolic_assignment, symbolic=True))
        for polynomial in context["core"]
    )
    symbolic_rows = _linear_rows(context, symbolic_assignment, symbolic=True)
    symbolic_q_columns = {
        stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
        for stage, representative in context["q_representatives"].items()
    }
    symbolic_pure = _pure_q_elimination(
        symbolic_rows, symbolic_q_columns, symbolic=True
    )
    symbolic_D, _symbolic_lambda, symbolic_remainder = _lambda_remainder(
        context, symbolic_assignment, symbolic_pure, symbolic=True
    )
    if symbolic_core_failures or symbolic_D == 0 or symbolic_remainder:
        raise AssertionError("the symbolic two-parameter Lambda audit failed")

    paths = {
        SLACK_PATH: root / SLACK_PATH,
        MIXED_PATH: root / MIXED_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "locus": "upper stratum fibre over the scalar core scheme S",
            "positive_fibre_coordinates": 123,
            "core_entries": 4152,
            "upper_right_rows": 1038,
            "field": "QQ for points; QQ(t,s) for the symbolic subfamily",
            "full_S_claim": False,
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "q_stage_mapping": {
            str(stage): representative
            for stage, representative in sorted(context["q_representatives"].items())
        },
        "numeric_nonzero_fibre_audit": {
            "points": point_records,
            "all_core_failures_zero": True,
            "all_D_nonzero": True,
            "all_lambda_row_remainders_zero": True,
            "all_kernel_vectors_Q_visible": True,
        },
        "D_zero_branch_audit": {
            "label": "growth_t_minus_13_constant_second_diagonal_2",
            "couplings": [str(value) for value in degenerate_couplings],
            "core_failures": degenerate_core_failures,
            "rows": len(degenerate_rows),
            "non_q_rank": degenerate_pure["non_q_rank"],
            "pure_rows": degenerate_pure["pure_rows"],
            "pure_q_rank": degenerate_pure["pure_q_rank"],
            "D": str(degenerate_D),
            "lambda_row_remainder_terms": len(degenerate_remainder),
            "q_visible_kernel": {
                str(stage): str(value) for stage, value in degenerate_kernel_q.items()
            },
            "kernel_q_is_nonzero": any(degenerate_kernel_q.values()),
            "lambda_on_kernel": str(degenerate_lambda_on_kernel),
            "source_determinants_checked": len(degenerate_determinants),
            "source_determinant_failures": degenerate_determinant_failures,
            "nonsingular_source_fibre": True,
            "D_zero_branch_sample_only": True,
        },
        "symbolic_subfamily_audit": {
            "first_diagonal": "growth characters at (1,1,1,1,t)",
            "second_diagonal": "constant s at every source transition",
            "field": "QQ(t,s)",
            "core_failures": symbolic_core_failures,
            "rows": len(symbolic_rows),
            "non_q_rank": symbolic_pure["non_q_rank"],
            "pure_rows": symbolic_pure["pure_rows"],
            "pure_q_rank": symbolic_pure["pure_q_rank"],
            "D_nonzero_as_rational_function": True,
            "D": str(sympy.factor(symbolic_D)),
            "lambda_row_remainder_terms": len(symbolic_remainder),
            "lambda_row_remainder_zero": True,
        },
        "interpretation": {
            "proved": [
                "Lambda is in the pure-Q row module at four exact nonzero-fibre points.",
                (
                    "Lambda is in the pure-Q row module identically on the declared "
                    "two-parameter family."
                ),
                (
                    "At one exact nonsingular D=0 branch point, Lambda is in the "
                    "pure-Q row module without using the D pivot."
                ),
                (
                    "The four numeric kernel vectors have nonzero Q components, so the "
                    "audit is not a zero-section check."
                ),
            ],
            "not_proved": [
                "Lambda=0 on the entire scalar variety S.",
                "S is irreducible, reduced, or covered by the growth family.",
                (
                    "A global localized row-module certificate or a nonsingular "
                    "Lambda-nonzero witness."
                ),
            ],
        },
        "next_gate": (
            "CERTIFY_LAMBDA_IN_THE_LOCALIZED_ROW_MODULE_OVER_ALL_OF_S_OR_FIND_A_"
            "D_NONZERO_LAMBDA_NONZERO_CORE_FIBRE"
        ),
        "solver_status": {
            "exact_QQ_linear_elimination_runs": len(point_records) + 1,
            "exact_QQ_ts_symbolic_linear_elimination_runs": 1,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_search_runs": 0,
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


def write_lambda_fibre_audit_v042(root: Path) -> Path:
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(compile_lambda_fibre_audit_v042(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_lambda_fibre_audit_v042(repository_root))
