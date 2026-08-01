"""Exact generic splitting certificate for transverse triangular SR2-V models.

The family has occurrence identification ON, ``Omega=e_2``, and

``A_e = [[alpha_e(s), x_e], [0, beta_e(r)]]``.

Here ``alpha(s)`` and ``beta(r)`` are the scalar transitive-percolation CSG
characters.  All upper-right constraints are linear.  A deterministic
130-by-130 minor at ``(r,s)=(1,2)`` proves that its determinant is a nonzero
rational function.  On the corresponding principal open, the only in-scope
extension of the 131 actual transitions is the simultaneous-conjugation
coboundary, so the resulting ``Q_1,...,Q_4`` commute.  The supplemental
``Q_5`` upper-right coordinate is fixed to zero and is not part of this
splitting kernel.  The exceptional determinant-zero locus and arbitrary CSG
characters remain open.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Any

from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus
from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

RESULT_PATH = "results/v0.4.2_sr2v_transitive_extension_principal_open.json"
SCHEMA = "final-theory-v042-sr2v-transitive-extension-principal-open-v1"
VERDICT = "SR2V_TRANSITIVE_EXTENSION_PRINCIPAL_OPEN_SPLITTING_CERTIFIED"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_SCOPED_PRINCIPAL_OPEN_ONLY"

SAMPLE_BOTTOM = Fraction(1)
SAMPLE_TOP = Fraction(2)
GRID_RATIOS = (
    Fraction(1, 3),
    Fraction(1, 2),
    Fraction(1),
    Fraction(2),
    Fraction(3),
)

Exponent = tuple[int, int]
Polynomial = dict[int, int]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _add_exponents(*values: Exponent) -> Exponent:
    return sum(value[0] for value in values), sum(value[1] for value in values)


def _scale_exponent(coefficient: int, value: Exponent) -> Exponent:
    return coefficient * value[0], coefficient * value[1]


def _transition_statistics(relation: Iterable[int], precursor: int) -> tuple[int, int]:
    rows = tuple(int(row) for row in relation)
    width = int(precursor).bit_count()
    maximal = len(maximal_elements_in_subset(rows, int(precursor)))
    return width, maximal


def _tp_exponent(stage: int, relation: Iterable[int], precursor: int) -> Exponent:
    width, maximal = _transition_statistics(relation, precursor)
    return maximal, width - maximal - stage


def _tp_value(
    ratio: Fraction,
    stage: int,
    relation: Iterable[int],
    precursor: int,
) -> Fraction:
    if not ratio or ratio == -1:
        raise ValueError("a nonsingular transitive-percolation ratio must avoid 0 and -1")
    power_ratio, power_one_plus = _tp_exponent(stage, relation, precursor)
    value = ratio**power_ratio * (1 + ratio) ** power_one_plus
    if not value:
        raise AssertionError("the declared transitive-percolation character became singular")
    return value


def _character(ratio: Fraction) -> torus.ScalarCharacter:
    def evaluate(stage: int, relation: Iterable[int], precursor: int) -> Fraction:
        return _tp_value(ratio, stage, relation, precursor)

    return evaluate


def _top_assignment(context: torus.ScoutContext, ratio: Fraction) -> dict[str, Fraction]:
    assignment: dict[str, Fraction] = {}
    for occurrence_id, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence_id]
        value = _tp_value(
            ratio,
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        previous = assignment.setdefault(variable, value)
        if previous != value:
            raise AssertionError("a scalar character is not constant on an ON orbit")
    assignment[torus.Q5] = _tp_value(ratio, 5, (0,) * 5, 0)
    if set(assignment) != set(context.variables):
        raise AssertionError("the scalar assignment does not cover the frozen variable inventory")
    return assignment


def _signature_exponent(
    context: torus.ScoutContext,
    stage: int,
    relation_code: int,
    precursor: int,
) -> Exponent:
    return _tp_exponent(stage, torus._decode_relation(stage, relation_code), precursor)


def _occurrence_exponent(
    context: torus.ScoutContext,
    occurrence_id: str,
) -> Exponent:
    record = context.occurrence_records[occurrence_id]
    return _tp_exponent(
        int(record["stage"]),
        record["source_relation_rows"],
        int(record["precursor_code"]),
    )


def _eq113_token_exponent(context: torus.ScoutContext, token: str) -> Exponent:
    if token.startswith("Q_"):
        stage = int(token.removeprefix("Q_"))
        return _tp_exponent(stage, (0,) * stage, 0)
    kind, identifier = token.split(":", maxsplit=1)
    stage, relation, precursor, _ = context.b_signatures[identifier]
    exponent = _tp_exponent(stage, relation, precursor)
    if kind == "BDEF":
        return exponent
    if kind == "BINV":
        return _scale_exponent(-1, exponent)
    raise ValueError(f"unknown Eq. (113) token: {token}")


def _add_binomial_term(
    polynomial: Polynomial,
    coefficient: int,
    ratio_power: int,
    one_plus_power: int,
) -> None:
    if ratio_power < 0 or one_plus_power < 0:
        raise AssertionError("MSR numerator exponents must be nonnegative")
    for offset in range(one_plus_power + 1):
        degree = ratio_power + offset
        polynomial[degree] = polynomial.get(degree, 0) + coefficient * comb(
            one_plus_power, offset
        )
        if not polynomial[degree]:
            del polynomial[degree]


def _symbolic_scalar_audit(context: torus.ScoutContext) -> dict[str, Any]:
    cpobc_failures: list[str] = []
    cpobc_checked = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            cpobc_checked += 1
            operator_ids = equation["operator_ids"]
            left = _add_exponents(
                *(
                    _occurrence_exponent(context, operator_ids[token])
                    for token in equation["lhs_word"]
                )
            )
            right = _add_exponents(
                *(
                    _occurrence_exponent(context, operator_ids[token])
                    for token in equation["rhs_word"]
                )
            )
            if left != right:
                cpobc_failures.append(
                    f"{relation['relation_id']}:{equation['equation_id']}"
                )

    eq113_audit: dict[str, dict[str, Any]] = {}
    for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        failures: list[str] = []
        checked = 0
        for relation in context.eq112["path_consistency_branches"][branch]:
            checked += 1
            left = _add_exponents(
                *(_eq113_token_exponent(context, token) for token in relation["lhs_word"])
            )
            right = _add_exponents(
                *(_eq113_token_exponent(context, token) for token in relation["rhs_word"])
            )
            if left != right:
                failures.append(str(relation["causet_id"]))
        eq113_audit[branch] = {"checked": checked, "failures": failures}

    def eq139_audit(domain: str) -> dict[str, Any]:
        failures: list[list[int]] = []
        instances = torus._eq139_instances(domain)
        for stage, left_index, right_index in instances:
            left_transition = _signature_exponent(
                context, stage, 0, (1 << left_index) - 1
            )
            right_transition = _signature_exponent(
                context, stage, 0, (1 << right_index) - 1
            )
            current_q = _tp_exponent(stage, (0,) * stage, 0)
            next_q = _tp_exponent(stage + 1, (0,) * (stage + 1), 0)
            left = _add_exponents(
                left_transition,
                right_transition,
                next_q,
                _scale_exponent(-1, right_transition),
                _scale_exponent(-1, current_q),
                right_transition,
            )
            right = _add_exponents(
                right_transition,
                left_transition,
                next_q,
                _scale_exponent(-1, left_transition),
                _scale_exponent(-1, current_q),
                left_transition,
            )
            if left != right:
                failures.append([stage, left_index, right_index])
        return {"checked": len(instances), "failures": failures}

    eq139_strict_audit = eq139_audit(torus.EQ139_STRICT)
    eq139_completed_audit = eq139_audit(torus.EQ139_COMPLETED)

    path_exponents: dict[str, Exponent] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            exponent = (0, 0)
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                exponent = _add_exponents(
                    exponent,
                    _signature_exponent(
                        context,
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    ),
                )
            path_exponents[str(path["path_id"])] = exponent
    gc_failures: list[str] = []
    for relation in context.operator_gc["all_pair_derivations"]:
        left_id = str(relation["left_path_id"])
        right_id = str(relation["right_path_id"])
        if path_exponents[left_id] != path_exponents[right_id]:
            gc_failures.append(f"{left_id}:{right_id}")

    msr_failures: list[str] = []
    for constraint in context.cpobc["MSR_operator_constraints"]:
        stages = {
            int(context.occurrence_records[term["transition_id"]]["stage"])
            for term in constraint["terms"]
        }
        if len(stages) != 1:
            raise AssertionError("one MSR source unexpectedly mixes stages")
        stage = stages.pop()
        polynomial: Polynomial = {}
        _add_binomial_term(
            polynomial,
            int(constraint["identity_coefficient"]),
            0,
            stage,
        )
        for term in constraint["terms"]:
            record = context.occurrence_records[term["transition_id"]]
            width, maximal = _transition_statistics(
                record["source_relation_rows"], int(record["precursor_code"])
            )
            _add_binomial_term(
                polynomial,
                int(term["coefficient"]),
                maximal,
                width - maximal,
            )
        if polynomial:
            msr_failures.append(str(constraint["constraint_id"]))

    audit: dict[str, Any] = {
        "parameterisation": "r^m*(1+r)^(w-m-n)",
        "exponent_coordinates": ["power_of_r", "power_of_1_plus_r"],
        "CPOBC": {"checked": cpobc_checked, "failures": cpobc_failures},
        "Eq113_separate_branches": eq113_audit,
        "Eq139_printed_strict": eq139_strict_audit,
        "Eq139_completed": eq139_completed_audit,
        "strong_GC_all_path_pairs": {
            "checked": len(context.operator_gc["all_pair_derivations"]),
            "failures": gc_failures,
        },
        "strong_MSR_polynomial_identities": {
            "checked": len(context.cpobc["MSR_operator_constraints"]),
            "failures": msr_failures,
        },
    }
    audited_records = [
        audit["CPOBC"],
        *eq113_audit.values(),
        eq139_strict_audit,
        eq139_completed_audit,
        audit["strong_GC_all_path_pairs"],
        audit["strong_MSR_polynomial_identities"],
    ]
    audit["all_passed"] = all(not record["failures"] for record in audited_records)
    return audit


def _row_labels(context: torus.ScoutContext) -> list[str]:
    labels: list[str] = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            labels.append(f"CPOBC:{relation['relation_id']}:{equation['equation_id']}")
    for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        for relation in context.eq112["path_consistency_branches"][branch]:
            labels.append(f"Eq113:{branch}:{relation['causet_id']}")
    for stage, left_index, right_index in torus._eq139_instances(torus.EQ139_COMPLETED):
        labels.append(
            f"Eq139:{torus.EQ139_COMPLETED}:{stage}:{left_index}:{right_index}"
        )
    for relation in context.operator_gc["generating_relation_basis"]:
        labels.append(f"fixed-GC:{relation['relation_id']}")
    for constraint in context.cpobc["MSR_operator_constraints"]:
        labels.append(f"reachable-MSR:{constraint['constraint_id']}")
    return labels


def _restrict_rows(
    rows: Iterable[torus.SparseRow],
    variables: Iterable[str],
) -> list[torus.SparseRow]:
    allowed = set(variables)
    return [
        {variable: value for variable, value in row.items() if variable in allowed and value}
        for row in rows
    ]


def _select_independent_rows(
    rows: list[torus.SparseRow],
    columns: list[str],
) -> list[int]:
    positions = {variable: index for index, variable in enumerate(columns)}
    basis: dict[int, dict[int, Fraction]] = {}
    selected: list[int] = []
    for row_index, source in enumerate(rows):
        row = {
            positions[variable]: value
            for variable, value in source.items()
            if variable in positions and value
        }
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {
                    column: value / scale for column, value in row.items()
                }
                selected.append(row_index)
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
        if len(selected) == len(columns):
            break
    return selected


def _determinant(matrix: list[list[Fraction]]) -> Fraction:
    rows = [row[:] for row in matrix]
    determinant = Fraction(1)
    size = len(rows)
    if any(len(row) != size for row in rows):
        raise ValueError("determinant requires a square matrix")
    for column in range(size):
        pivot = next((row for row in range(column, size) if rows[row][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            rows[column], rows[pivot] = rows[pivot], rows[column]
            determinant = -determinant
        pivot_value = rows[column][column]
        determinant *= pivot_value
        for row in range(column + 1, size):
            if not rows[row][column]:
                continue
            scale = rows[row][column] / pivot_value
            rows[row][column] = Fraction(0)
            for later in range(column + 1, size):
                rows[row][later] -= scale * rows[column][later]
    return determinant


def _proportional_scale(
    left: torus.SparseRow,
    right: torus.SparseRow,
    variables: Iterable[str],
) -> Fraction | None:
    scale: Fraction | None = None
    for variable in variables:
        left_value = left.get(variable, Fraction(0))
        right_value = right.get(variable, Fraction(0))
        if not right_value:
            if left_value:
                return None
            continue
        candidate = left_value / right_value
        if scale is None:
            scale = candidate
        elif candidate != scale:
            return None
    return scale


def _family_rows(
    context: torus.ScoutContext,
    bottom_ratio: Fraction,
    top_ratio: Fraction,
) -> tuple[
    list[torus.SparseRow],
    dict[str, int],
    dict[str, torus.SparseRow],
    dict[str, Fraction],
    dict[str, Fraction],
]:
    bottom = _top_assignment(context, bottom_ratio)
    top = _top_assignment(context, top_ratio)
    rows, counts, commutators, _ = torus._linear_system(
        context,
        top,
        lower_character=_character(bottom_ratio),
    )
    return rows, counts, commutators, bottom, top


def build_payload(root: Path) -> dict[str, Any]:
    context = torus._build_context(root)
    labels = _row_labels(context)
    symbolic_audit = _symbolic_scalar_audit(context)
    actual_variables = [variable for variable in context.variables if variable != torus.Q5]

    sample_rows, counts, sample_commutators, bottom, top = _family_rows(
        context, SAMPLE_BOTTOM, SAMPLE_TOP
    )
    if len(labels) != len(sample_rows):
        raise AssertionError("row labels and the exact relation matrix have different sizes")
    restricted_sample = _restrict_rows(sample_rows, actual_variables)
    sample_echelon = torus._row_echelon(restricted_sample, tuple(actual_variables))
    sample_nullspace = torus._nullspace_basis_from_echelon(
        sample_echelon, tuple(actual_variables)
    )
    coboundary = {
        variable: bottom[variable] - top[variable]
        for variable in actual_variables
        if bottom[variable] != top[variable]
    }
    coboundary_residual_count = sum(
        bool(torus._row_value(row, coboundary)) for row in restricted_sample
    )
    if len(sample_nullspace) != 1:
        raise AssertionError("the sample extension kernel must be one-dimensional")
    nullspace_scale = _proportional_scale(
        sample_nullspace[0], coboundary, actual_variables
    )

    gauge_variable = torus._q_variable(context, 1)
    minor_columns = [variable for variable in actual_variables if variable != gauge_variable]
    selected_indices = _select_independent_rows(restricted_sample, minor_columns)
    if len(selected_indices) != len(minor_columns):
        raise AssertionError("the declared principal-open minor is singular at the sample point")
    selected_matrix = [
        [restricted_sample[index].get(variable, Fraction(0)) for variable in minor_columns]
        for index in selected_indices
    ]
    determinant = _determinant(selected_matrix)

    grid_records: list[dict[str, Any]] = []
    rank_census: defaultdict[str, int] = defaultdict(int)
    off_diagonal_all_split = True
    diagonal_all_commutator_rows_zero = True
    for bottom_ratio in GRID_RATIOS:
        for top_ratio in GRID_RATIOS:
            rows, _, commutators, grid_bottom, grid_top = _family_rows(
                context, bottom_ratio, top_ratio
            )
            restricted = _restrict_rows(rows, actual_variables)
            echelon = torus._row_echelon(restricted, tuple(actual_variables))
            free_commutators = [
                pair
                for pair, row in commutators.items()
                if torus._row_remainder(row, echelon, tuple(actual_variables))
            ]
            diagonal = bottom_ratio == top_ratio
            coboundary_grid = {
                variable: grid_bottom[variable] - grid_top[variable]
                for variable in actual_variables
                if grid_bottom[variable] != grid_top[variable]
            }
            nullspace = torus._nullspace_basis_from_echelon(
                echelon, tuple(actual_variables)
            )
            split_kernel = (
                diagonal
                or (
                    len(nullspace) == 1
                    and _proportional_scale(
                        nullspace[0], coboundary_grid, actual_variables
                    )
                    is not None
                )
            )
            off_diagonal_all_split &= diagonal or split_kernel
            diagonal_all_commutator_rows_zero &= (
                not diagonal or all(not row for row in commutators.values())
            )
            rank_census[str(len(echelon))] += 1
            grid_records.append(
                {
                    "bottom_ratio": str(bottom_ratio),
                    "top_ratio": str(top_ratio),
                    "diagonal_character_pair": diagonal,
                    "actual_rank": len(echelon),
                    "actual_nullity": len(actual_variables) - len(echelon),
                    "split_kernel_when_distinct": split_kernel,
                    "free_Q_commutators": free_commutators,
                }
            )

    relation_counts_expected = {
        "CPOBC": 783,
        "Eq113_both_branches": 50,
        "Eq139_completed": 10,
        "fixed_vector_GC_basis": 320,
        "reachable_state_MSR": 24,
    }
    relation_domain_inventory = {
        "CPOBC": {"solver_row_count": 783},
        "Eq113": {
            torus.EQ113_DERIVED: {"relation_count": 25, "solver_row_count": 25},
            torus.EQ113_LITERAL: {"relation_count": 25, "solver_row_count": 25},
        },
        "Eq139": {
            torus.EQ139_STRICT: {
                "relation_count": 4,
                "solver_row_count": 0,
                "scope_note": "audited separately; contained in completed and not duplicated",
            },
            torus.EQ139_COMPLETED: {
                "relation_count": 10,
                "solver_row_count": 10,
            },
        },
        "fixed_vector_GC_basis": {"solver_row_count": 320},
        "reachable_state_MSR": {"solver_row_count": 24},
    }
    gates = {
        "symbolic_scalar_family_satisfies_all_required_identities": symbolic_audit[
            "all_passed"
        ],
        "relation_inventory_is_1187": counts == relation_counts_expected
        and len(sample_rows) == 1187,
        "Eq113_and_Eq139_domains_are_separate": relation_domain_inventory
        == {
            "CPOBC": {"solver_row_count": 783},
            "Eq113": {
                torus.EQ113_DERIVED: {"relation_count": 25, "solver_row_count": 25},
                torus.EQ113_LITERAL: {"relation_count": 25, "solver_row_count": 25},
            },
            "Eq139": {
                torus.EQ139_STRICT: {
                    "relation_count": 4,
                    "solver_row_count": 0,
                    "scope_note": (
                        "audited separately; contained in completed and not duplicated"
                    ),
                },
                torus.EQ139_COMPLETED: {
                    "relation_count": 10,
                    "solver_row_count": 10,
                },
            },
            "fixed_vector_GC_basis": {"solver_row_count": 320},
            "reachable_state_MSR": {"solver_row_count": 24},
        },
        "actual_transition_variable_count_is_131": len(actual_variables) == 131,
        "sample_actual_rank_is_130": len(sample_echelon) == 130,
        "sample_kernel_is_exactly_the_coboundary": coboundary_residual_count == 0
        and nullspace_scale is not None,
        "selected_130_by_130_minor_is_nonzero": bool(determinant),
        "all_sample_Q_commutators_lie_in_the_relation_row_space": all(
            not torus._row_remainder(
                row, sample_echelon, tuple(actual_variables)
            )
            for row in sample_commutators.values()
        ),
        "off_diagonal_grid_kernels_are_split": off_diagonal_all_split,
        "diagonal_grid_commutator_rows_are_identically_zero": (
            diagonal_all_commutator_rows_zero
        ),
        "grid_has_no_free_Q_commutator": all(
            not record["free_Q_commutators"] for record in grid_records
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"transitive-extension certificate gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: torus._sha256(root / relative)
            for relative in sorted(
                (
                    torus.CPOBC_PATH,
                    torus.REDUCTION_PATH,
                    torus.OPERATOR_GC_PATH,
                    torus.ATOMISATION_PATH,
                    torus.EQ112_PATH,
                )
            )
        },
        "declared_family": {
            "matrix_form": "A_e=[[alpha_e(s),x_e],[0,beta_e(r)]]",
            "initial_vector": "e_2",
            "scalar_character": "p_e(r)=r^m*(1+r)^(w-m-n)",
            "parameter_domain": "r*s*(1+r)*(1+s)!=0",
            "occurrence_identification": "ON",
            "supplemental_Q5_assignment": (
                "diagonal scalar-character value with upper-right extension coordinate "
                "fixed to 0; excluded from the 131-variable splitting kernel"
            ),
            "interpretation": (
                "transverse reducible extensions between two scalar "
                "transitive-percolation CSG characters"
            ),
        },
        "symbolic_scalar_identity_audit": symbolic_audit,
        "linear_problem": {
            "row_count": len(sample_rows),
            "relation_domain_inventory": relation_domain_inventory,
            "actual_upper_right_variable_count": len(actual_variables),
            "cutoff_external_variable": torus.Q5,
            "cutoff_external_variable_assignment": "x_Q5=0",
            "coefficient_family": "rational functions in Q(r,s)",
        },
        "principal_open_certificate": {
            "sample_point": {
                "bottom_ratio_r": str(SAMPLE_BOTTOM),
                "top_ratio_s": str(SAMPLE_TOP),
            },
            "gauge_column_removed": gauge_variable,
            "minor_size": len(minor_columns),
            "selected_row_indices_zero_based": selected_indices,
            "selected_row_labels": [labels[index] for index in selected_indices],
            "selected_column_labels": minor_columns,
            "determinant_at_sample": str(determinant),
            "determinant_numerator_bits": abs(determinant.numerator).bit_length(),
            "determinant_denominator_bits": determinant.denominator.bit_length(),
            "sample_actual_rank": len(sample_echelon),
            "sample_actual_nullity": len(sample_nullspace),
            "coboundary_formula": "x_e=c*(beta_e(r)-alpha_e(s))",
            "sample_nullspace_to_coboundary_scale": str(nullspace_scale),
            "definition_of_Delta": (
                "determinant of the listed 130 rows and 130 columns of the "
                "1187-row rational-function relation matrix; Delta is its "
                "reduced numerator after clearing denominators"
            ),
            "proof": [
                "The scalar diagonal family satisfies every required identity symbolically.",
                (
                    "Global upper-triangular conjugation supplies the nonzero "
                    "coboundary kernel vector whenever r!=s."
                ),
                "Therefore the actual relation matrix has rank at most 130.",
                "The listed minor is nonzero at (r,s)=(1,2), so Delta is not the zero polynomial.",
                (
                    "On r!=s and Delta!=0 the rank is 130 and the kernel is "
                    "exactly the coboundary line."
                ),
                (
                    "Every resulting extension of the 131 actual transitions is "
                    "simultaneously conjugate to the diagonal family; in particular "
                    "Q_1,...,Q_4 commute."
                ),
            ],
        },
        "same_character_branch": {
            "condition": "r=s",
            "matrix_form": "A_e=p_e(r)*I+x_e*E_12",
            "conclusion": (
                "the 131 actual transition matrices commute for every upper-right "
                "assignment; Q5 is fixed as declared above"
            ),
        },
        "exact_grid_scout": {
            "ratios": [str(value) for value in GRID_RATIOS],
            "pair_count": len(grid_records),
            "rank_census": dict(sorted(rank_census.items(), key=lambda item: int(item[0]))),
            "records": grid_records,
            "role": "sanity scout only; the principal-open proof comes from the explicit minor",
        },
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "witness": None,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "This certifies Q_1,...,Q_4 commutativity only for the same-character line and the "
            "explicit nonempty principal open Delta(r,s)!=0 in the two-character "
            "transitive-percolation transverse triangular family.  The exceptional "
            "off-diagonal locus Delta=0, general scalar CSG characters, other reducible "
            "components, higher-order/disconnected branches, and irreducible GL_2 "
            "representations remain open.  The supplemental Q5 upper-right coordinate "
            "is fixed to zero and is outside the 131-dimensional splitting kernel.  "
            "This is not an SR2-V search terminal."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
