"""Exact bounded scout for the v0.4.2 mixed ``x/y`` transition ansatz.

The ansatz is

    A_e = [[p_e, x_[e]], [y_[e], 1]],

where ``p_e`` is the rational CSG character with ``t_j=1`` and ``[e]`` is
one of the 131 ON transition orbits.  The module computes exact tangent and
transverse-linearisation ranks over ``QQ``.  On the bounded ``x=0`` pure-lower
family those same equations are exact linear equations and give a global
family-specific no-go.  Neither result is promoted to a global nonlinear
classification of the mixed ansatz or the full 955 profile.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

from universe_lab.final_theory.causal_sets import maximal_elements_in_subset

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
LOCAL_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
SOURCE_COMPILER_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
RESULT_PATH = "results/v0.4.2_955_mixed_xy_tangent_scout.json"

VERDICT = "V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN"
PURE_LOWER_VERDICT = "V042_955_PURE_LOWER_TRIANGULAR_GLOBAL_NO_GO_PROVED"
SCHEMA = "final-theory-v042-955-mixed-xy-tangent-scout-v2"

type Row = dict[str, Fraction]
type Orientation = Literal["upper", "lower"]


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


def _relation_code(relation: Iterable[int]) -> int:
    rows = tuple(int(row) for row in relation)
    return sum(row << (index * len(rows)) for index, row in enumerate(rows))


def _signature(record: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(record["stage"]),
        _relation_code(record["source_relation_rows"]),
        int(record["precursor_code"]),
    )


def _probability(record: dict[str, Any]) -> Fraction:
    stage = int(record["stage"])
    relation = tuple(int(row) for row in record["source_relation_rows"])
    precursor = int(record["precursor_code"])
    width = precursor.bit_count()
    maximal_count = len(maximal_elements_in_subset(relation, precursor))
    return Fraction(2 ** (width - maximal_count), 2**stage)


def _add_scaled(target: defaultdict[str, Fraction], source: Row, scale: Fraction) -> None:
    for variable, value in source.items():
        target[variable] += scale * value


def _row_subtract(left: Row, right: Row) -> Row:
    result: defaultdict[str, Fraction] = defaultdict(Fraction)
    _add_scaled(result, left, Fraction(1))
    _add_scaled(result, right, Fraction(-1))
    return {variable: value for variable, value in result.items() if value}


@dataclass(frozen=True)
class _OffDiagonalLinear:
    upper_left: Fraction
    lower_right: Fraction
    coefficients: Row
    orientation: Orientation


def _matrix(record: dict[str, Any], orientation: Orientation) -> _OffDiagonalLinear:
    return _OffDiagonalLinear(
        _probability(record),
        Fraction(1),
        {str(record["orbit_id"]): Fraction(1)},
        orientation,
    )


def _identity(orientation: Orientation) -> _OffDiagonalLinear:
    return _OffDiagonalLinear(Fraction(1), Fraction(1), {}, orientation)


def _multiply(left: _OffDiagonalLinear, right: _OffDiagonalLinear) -> _OffDiagonalLinear:
    if left.orientation != right.orientation:
        raise AssertionError("cannot multiply different tangent blocks")
    coefficients: defaultdict[str, Fraction] = defaultdict(Fraction)
    if left.orientation == "upper":
        _add_scaled(coefficients, right.coefficients, left.upper_left)
        _add_scaled(coefficients, left.coefficients, right.lower_right)
    else:
        _add_scaled(coefficients, left.coefficients, right.upper_left)
        _add_scaled(coefficients, right.coefficients, left.lower_right)
    return _OffDiagonalLinear(
        left.upper_left * right.upper_left,
        left.lower_right * right.lower_right,
        {variable: value for variable, value in coefficients.items() if value},
        left.orientation,
    )


def _word(
    factors: Iterable[_OffDiagonalLinear],
    orientation: Orientation,
    *,
    later_on_left: bool = False,
) -> _OffDiagonalLinear:
    product = _identity(orientation)
    for factor in factors:
        product = _multiply(factor, product) if later_on_left else _multiply(product, factor)
    return product


def _residual(left: _OffDiagonalLinear, right: _OffDiagonalLinear) -> Row:
    if left.upper_left != right.upper_left or left.lower_right != right.lower_right:
        raise AssertionError("the diagonal CSG character violates a frozen identity")
    return _row_subtract(left.coefficients, right.coefficients)


def _rank_certificate(
    labelled_rows: Iterable[tuple[str, Row]], variables: list[str]
) -> tuple[int, list[str], dict[int, dict[int, Fraction]]]:
    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    selected: list[str] = []
    for label, source in labelled_rows:
        row = {positions[variable]: Fraction(value) for variable, value in source.items() if value}
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                selected.append(label)
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return len(basis), selected, basis


def _rank(labelled_rows: Iterable[tuple[str, Row]], variables: list[str]) -> int:
    return _rank_certificate(labelled_rows, variables)[0]


def _rows_digest(labelled_rows: Iterable[tuple[str, Row]]) -> str:
    serialised = [
        [label, [[variable, str(value)] for variable, value in sorted(row.items())]]
        for label, row in labelled_rows
    ]
    return hashlib.sha256(_canonical_json(serialised).encode("utf-8")).hexdigest()


def _compile_orientation(
    cpobc: dict[str, Any],
    reduction: dict[str, Any],
    local_gc: dict[str, Any],
    orientation: Orientation,
) -> dict[str, Any]:
    records = reduction["reduction_map"]
    by_occurrence = {str(record["occurrence_id"]): record for record in records}
    signature_to_record: dict[tuple[int, int, int], dict[str, Any]] = {}
    for record in records:
        key = _signature(record)
        previous = signature_to_record.setdefault(key, record)
        if str(previous["orbit_id"]) != str(record["orbit_id"]):
            raise AssertionError(f"signature has conflicting ON orbits: {key}")
    variables = sorted({str(record["orbit_id"]) for record in records})
    occurrence_matrices = {
        occurrence: _matrix(record, orientation) for occurrence, record in by_occurrence.items()
    }

    cpobc_rows: list[tuple[str, Row]] = []
    length_two_rows: list[tuple[str, Row]] = []
    for relation in cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operators = equation["operator_ids"]
            lhs = _word(
                (occurrence_matrices[operators[token]] for token in equation["lhs_word"]),
                orientation,
            )
            rhs = _word(
                (occurrence_matrices[operators[token]] for token in equation["rhs_word"]),
                orientation,
            )
            labelled = (
                f"{relation['relation_id']}:{equation['equation_id']}",
                _residual(lhs, rhs),
            )
            cpobc_rows.append(labelled)
            if len(equation["lhs_word"]) == len(equation["rhs_word"]) == 2:
                length_two_rows.append(labelled)

    path_matrices: dict[str, _OffDiagonalLinear] = {}
    for paths in local_gc["path_inventory"].values():
        for path in paths:
            factors = []
            for transition in path["transitions"]:
                signature = transition["quotient_signature"]
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                factors.append(_matrix(signature_to_record[key], orientation))
            path_matrices[str(path["path_id"])] = _word(factors, orientation, later_on_left=True)
    gc_rows = [
        (
            str(relation["relation_id"]),
            _residual(
                path_matrices[str(relation["lhs_path_id"])],
                path_matrices[str(relation["rhs_path_id"])],
            ),
        )
        for relation in local_gc["generating_relation_basis"]
    ]

    canonical_states: dict[str, _OffDiagonalLinear] = {}
    for stage in range(1, 5):
        paths = local_gc["path_inventory"][str(stage)]
        endpoints = {str(path["endpoint_causet_id"]) for path in paths}
        for endpoint in endpoints:
            chosen = min(
                (path for path in paths if str(path["endpoint_causet_id"]) == endpoint),
                key=lambda path: str(path["path_id"]),
            )
            factors = []
            for transition in chosen["transitions"]:
                signature = transition["quotient_signature"]
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                factors.append(_matrix(signature_to_record[key], orientation))
            canonical_states[endpoint] = _word(factors, orientation, later_on_left=True)

    reachable_rows: list[tuple[str, Row]] = []
    reachable_by_stage: dict[int, list[tuple[str, Row]]] = defaultdict(list)
    if orientation == "lower":
        for constraint in cpobc["MSR_operator_constraints"]:
            source_id = str(constraint["source_id"])
            state = canonical_states[source_id]
            multiplicity_residual = Fraction(int(constraint["identity_coefficient"]))
            probability_residual = Fraction(int(constraint["identity_coefficient"]))
            reachable_row: defaultdict[str, Fraction] = defaultdict(Fraction)
            for term in constraint["terms"]:
                coefficient = Fraction(int(term["coefficient"]))
                multiplicity_residual += coefficient
                probability_residual += (
                    coefficient * occurrence_matrices[str(term["transition_id"])].upper_left
                )
                _add_scaled(
                    reachable_row,
                    occurrence_matrices[str(term["transition_id"])].coefficients,
                    state.upper_left * coefficient,
                )
            if probability_residual != 0:
                raise AssertionError(f"the CSG diagonal violates reachable MSR at {source_id}")
            _add_scaled(reachable_row, state.coefficients, multiplicity_residual)
            labelled = (
                f"{constraint['constraint_id']}:reachable-lower-linearisation",
                {variable: value for variable, value in reachable_row.items() if value},
            )
            reachable_rows.append(labelled)
            first_transition = by_occurrence[str(constraint["terms"][0]["transition_id"])]
            reachable_by_stage[int(first_transition["stage"])].append(labelled)

    def q_matrix(stage: int) -> _OffDiagonalLinear:
        return _matrix(signature_to_record[(stage, 0, 0)], orientation)

    commutator_rows: dict[str, Row] = {}
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        left = q_matrix(left_stage)
        right = q_matrix(right_stage)
        commutator_rows[f"Q{left_stage}_Q{right_stage}"] = _residual(
            _multiply(left, right), _multiply(right, left)
        )

    cpobc_rank = _rank(cpobc_rows, variables)
    profile_rows = cpobc_rows + gc_rows + reachable_rows
    profile_rank, selected, _profile_echelon = _rank_certificate(profile_rows, variables)
    commutators = {}
    for pair, commutator_row in commutator_rows.items():
        augmented = _rank(profile_rows + [(f"comm:{pair}", commutator_row)], variables)
        commutators[pair] = {
            "augmented_rank": augmented,
            "rank_increment": augmented - profile_rank,
            "forced_zero_in_linearised_profile": augmented == profile_rank,
        }

    rank_ladder: dict[str, int] = {}
    if orientation == "lower":
        accumulated: list[tuple[str, Row]] = []
        for stage in range(1, 5):
            accumulated.extend(reachable_by_stage[stage])
            rank_ladder[f"through_source_stage_{stage}"] = _rank(
                length_two_rows + accumulated, variables
            )

    transverse_certificate: dict[str, Any] | None = None
    if orientation == "lower":
        transverse_rows = length_two_rows + reachable_rows
        transverse_rank, transverse_selected, transverse_echelon = _rank_certificate(
            transverse_rows, variables
        )
        if transverse_rank != len(variables) or set(transverse_echelon) != set(
            range(len(variables))
        ):
            raise AssertionError("the lower transverse system lost full column rank")
        rows_by_label = {label: row for label, row in transverse_rows}
        selected_rows = [
            {
                "label": label,
                "coefficients": [
                    [variable, str(value)]
                    for variable, value in sorted(rows_by_label[label].items())
                ],
            }
            for label in transverse_selected
        ]
        echelon_rows = [
            {
                "pivot_index": pivot,
                "pivot_variable": variables[pivot],
                "coefficients": [
                    [variables[column], str(value)]
                    for column, value in sorted(transverse_echelon[pivot].items())
                ],
            }
            for pivot in sorted(transverse_echelon)
        ]
        if any(transverse_echelon[pivot].get(pivot) != 1 for pivot in transverse_echelon):
            raise AssertionError("normalized echelon pivot certificate is malformed")
        transverse_certificate = {
            "certificate_type": "exact_QQ_normalized_sparse_row_echelon",
            "input_rows": (
                "712 length-two CPOBC lower-left rows plus 24 reachable-MSR lower Jacobian rows"
            ),
            "input_row_count": len(transverse_rows),
            "ordered_variables": variables,
            "column_count": len(variables),
            "rank": transverse_rank,
            "selected_independent_row_count": len(transverse_selected),
            "selected_row_kind_counts": {
                "CPOBC": sum(
                    "reachable-lower-linearisation" not in label for label in transverse_selected
                ),
                "reachable_MSR": sum(
                    "reachable-lower-linearisation" in label for label in transverse_selected
                ),
            },
            "selected_rows": selected_rows,
            "selected_rows_sha256": hashlib.sha256(
                _canonical_json(selected_rows).encode("utf-8")
            ).hexdigest(),
            "echelon_pivot_count": len(echelon_rows),
            "echelon_rows": echelon_rows,
            "echelon_rows_sha256": hashlib.sha256(
                _canonical_json(echelon_rows).encode("utf-8")
            ).hexdigest(),
            "all_131_columns_are_pivots": True,
            "verification_rule": (
                "Recompile the selected exact rows in ordered_variables order and perform "
                "QQ elimination; the emitted normalized echelon has one unit pivot in every column."
            ),
        }

    return {
        "orientation": orientation,
        "variable_count": len(variables),
        "row_counts": {
            "CPOBC": len(cpobc_rows),
            "length_two_CPOBC": len(length_two_rows),
            "strong_GC_basis": len(gc_rows),
            "reachable_MSR": len(reachable_rows),
            "profile_total": len(profile_rows),
        },
        "ranks": {
            "CPOBC": cpobc_rank,
            "length_two_CPOBC": _rank(length_two_rows, variables),
            "strong_GC_basis_alone": _rank(gc_rows, variables),
            "CPOBC_plus_strong_GC": _rank(cpobc_rows + gc_rows, variables),
            "CPOBC_plus_reachable_MSR": _rank(cpobc_rows + reachable_rows, variables),
            "length_two_CPOBC_plus_reachable_MSR": _rank(
                length_two_rows + reachable_rows, variables
            ),
            "full_linearised_profile": profile_rank,
            "full_nullity": len(variables) - profile_rank,
        },
        "reachable_rank_ladder": rank_ladder,
        "selected_independent_rows": {
            "count": len(selected),
            "labels_sha256": hashlib.sha256(_canonical_json(selected).encode("utf-8")).hexdigest(),
        },
        "full_column_rank_certificate": transverse_certificate,
        "row_system_sha256": _rows_digest(profile_rows),
        "Q_commutator_linearisation": {
            "records": commutators,
            "all_six_forced_zero": all(
                record["forced_zero_in_linearised_profile"] for record in commutators.values()
            ),
        },
    }


def compile_mixed_xy_nonneutral_scout_v042(root: Path) -> dict[str, Any]:
    """Compile the exact bounded tangent obstruction and open-boundary ledger."""

    paths = {
        CPOBC_PATH: root / CPOBC_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        LOCAL_GC_PATH: root / LOCAL_GC_PATH,
        SOURCE_COMPILER_PATH: root / SOURCE_COMPILER_PATH,
    }
    cpobc = _load(paths[CPOBC_PATH])
    reduction = _load(paths[REDUCTION_PATH])
    local_gc = _load(paths[LOCAL_GC_PATH])
    source_compiler = _load(paths[SOURCE_COMPILER_PATH])
    if not (
        source_compiler.get("verdict")
        == "V042_955_SOURCE_NATIVE_SLACK_INVENTORY_READY_NO_SOLVER_RUN"
        and source_compiler.get("passed") is True
        and source_compiler.get("semantic_digest_sha256") == _semantic_digest(source_compiler)
    ):
        raise AssertionError("the source-native 955 compiler is not at its frozen ready gate")
    if len(reduction.get("reduction_map", [])) != 165:
        raise AssertionError("expected 165 source occurrences")
    if len({record["orbit_id"] for record in reduction["reduction_map"]}) != 131:
        raise AssertionError("expected 131 ON quotient orbits")
    if len(cpobc.get("MSR_operator_constraints", [])) != 24:
        raise AssertionError("expected 24 source MSR constraints")
    if local_gc.get("counts", {}).get("same_endpoint_path_pairs") != 1529:
        raise AssertionError("expected 1529 strong-GC path pairs")

    upper = _compile_orientation(cpobc, reduction, local_gc, "upper")
    lower = _compile_orientation(cpobc, reduction, local_gc, "lower")
    if upper["ranks"]["full_linearised_profile"] != 114:
        raise AssertionError("upper tangent rank changed")
    if lower["ranks"]["full_linearised_profile"] != 131:
        raise AssertionError("lower tangent obstruction changed")
    lower_certificate = lower["full_column_rank_certificate"]
    if not isinstance(lower_certificate, dict) or lower_certificate.get("rank") != 131:
        raise AssertionError("the pure-lower exact forcing certificate is unavailable")

    p1_constraint = next(
        constraint
        for constraint in cpobc["MSR_operator_constraints"]
        if constraint["source_id"] == "p1-0"
    )
    by_occurrence = {str(record["occurrence_id"]): record for record in reduction["reduction_map"]}
    p1_upper_left = Fraction(int(p1_constraint["identity_coefficient"]))
    p1_lower_right = Fraction(int(p1_constraint["identity_coefficient"]))
    for term in p1_constraint["terms"]:
        coefficient = Fraction(int(term["coefficient"]))
        p1_upper_left += coefficient * _probability(by_occurrence[str(term["transition_id"])])
        p1_lower_right += coefficient
    if (p1_upper_left, p1_lower_right) != (Fraction(0), Fraction(1)):
        raise AssertionError("the global N!=0 p1 residual check changed")

    base_determinants = [_probability(record) for record in reduction["reduction_map"]]
    if any(value == 0 for value in base_determinants):
        raise AssertionError("the diagonal base point must be nonsingular")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_stages": "n<=4",
            "dimension": 2,
            "field": "QQ for every reported rank",
            "identification_mode": "ON_QUOTIENT",
            "ansatz": "A_e=[[p_e,x_[e]],[y_[e],1]], p_e=CSG(t_j=1)",
            "scalar_variables": {"x": 131, "y": 131, "total": 262},
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "N_nonzero_gate": {
            "explicitly_guaranteed_throughout_ansatz": True,
            "source": "p1-0",
            "residual_form": "D_p1=[[0,x_Q1+x_T],[y_Q1+y_T,1]]",
            "reachable_MSR_first_column_condition": "y_Q1+y_T=0",
            "nonzero_entry_independent_of_x_y": "(D_p1)_{22}=1",
            "conclusion": "D_p1 is never the zero operator, including on every tangent slice",
        },
        "nonsingularity": {
            "mixed_condition": "det(A_e)=p_e-x_[e]*y_[e] != 0 for all 165 occurrences",
            "diagonal_base_all_165_nonzero": True,
            "minimum_base_determinant": str(min(base_determinants)),
            "no_full_mixed_candidate_tested": True,
        },
        "exact_linear_blocks": {"upper": upper, "lower": lower},
        "bounded_family_global_results": {
            "pure_lower_triangular": {
                "ansatz": "A_e=[[p_e,0],[y_[e],1]]",
                "field": "QQ",
                "identification_mode": "ON_QUOTIENT",
                "variable_count": 131,
                "exact_linearity": {
                    "CPOBC": True,
                    "strong_GC": True,
                    "reachable_state_MSR": True,
                    "reason": [
                        (
                            "Products of matrices [[p,0],[y,1]] remain lower "
                            "triangular and their lower-left entries are QQ-linear in y."
                        ),
                        (
                            "Every reachable vector has form (alpha,L(y)) with alpha "
                            "fixed by p and L QQ-linear in y."
                        ),
                        (
                            "For D_c=[[0,0],[S_c(y),m_c]], the reachable-MSR lower "
                            "entry is alpha_c*S_c(y)+m_c*L_c(y), again exactly linear."
                        ),
                    ],
                    "discarded_higher_order_terms": 0,
                },
                "exact_equation_counts": {
                    "CPOBC": 783,
                    "strong_GC_spanning_basis": 320,
                    "strong_GC_same_endpoint_pairs_derived": 1529,
                    "reachable_state_MSR": 24,
                },
                "minimal_forcing_system": {
                    "length_two_CPOBC_rows": 712,
                    "reachable_state_MSR_rows": 24,
                    "rank_over_QQ": lower["ranks"]["length_two_CPOBC_plus_reachable_MSR"],
                    "nullity": 0,
                    "strong_GC_needed_for_rank_131": False,
                    "certificate_reused_from": (
                        "exact_linear_blocks.lower.full_column_rank_certificate"
                    ),
                    "selected_row_count": lower_certificate["selected_independent_row_count"],
                    "selected_rows_sha256": lower_certificate["selected_rows_sha256"],
                    "echelon_rows_sha256": lower_certificate["echelon_rows_sha256"],
                    "all_131_columns_are_pivots": lower_certificate["all_131_columns_are_pivots"],
                },
                "unique_solution": {
                    "assignment": "y_[e]=0 for all 131 ON orbits",
                    "proved_globally_within_this_bounded_family": True,
                    "resulting_operators": "A_e=diag(p_e,1)",
                    "all_Q1_through_Q4_diagonal": True,
                    "all_six_Q_commutators_zero": True,
                },
                "N_nonzero": {
                    "source": "p1-0",
                    "residual_at_unique_solution": "D_p1=diag(0,1)",
                    "reachable_equality": "D_p1*e1=0",
                    "operator_residual_nonzero": True,
                },
                "nonsingularity": {
                    "determinant": "det(A_e)=p_e",
                    "all_165_occurrences_nonzero": True,
                },
                "scope_boundary": (
                    "Global only for x=0 in the declared mixed-x/y ansatz; it is not "
                    "a theorem for x!=0,y!=0, general GL2, or the full 955 profile."
                ),
                "verdict": PURE_LOWER_VERDICT,
            }
        },
        "diagonal_base_tangent": {
            "rank": upper["ranks"]["full_linearised_profile"]
            + lower["ranks"]["full_linearised_profile"],
            "nullity": 262
            - upper["ranks"]["full_linearised_profile"]
            - lower["ranks"]["full_linearised_profile"],
            "decomposition": "upper and lower off-diagonal blocks decouple at x=y=0",
            "lower_kernel_zero": True,
            "tangent_space_equals_upper_solution_space": True,
            "all_six_Q_commutator_derivatives_forced_zero": (
                upper["Q_commutator_linearisation"]["all_six_forced_zero"]
                and lower["Q_commutator_linearisation"]["all_six_forced_zero"]
            ),
        },
        "transverse_to_upper_family": {
            "upper_family": {
                "exact_dimension": upper["ranks"]["full_nullity"],
                "equations_are_exactly_linear_in_x": True,
                "all_six_Q_commutators_zero_within_family": True,
            },
            "lower_Jacobian_rank_at_every_upper_point": lower["ranks"]["full_linearised_profile"],
            "lower_Jacobian_nullity_at_every_upper_point": lower["ranks"]["full_nullity"],
            "universal_reason": [
                (
                    "The lower-left derivative of a product of upper-triangular "
                    "background matrices depends only on p and y, never on x."
                ),
                (
                    "The lower component of the reachable-MSR derivative has the "
                    "same x-independent property."
                ),
                (
                    "The CPOBC plus reachable-MSR lower block already has rank 131, "
                    "before strong GC is added."
                ),
            ],
            "proved_scope": (
                "There is no first-order lower deformation at any point of the exact "
                "17-dimensional upper family."
            ),
            "formal_local_consequence": (
                "Because the selected 131-by-131 y-Jacobian minor is a nonzero QQ "
                "constant along the upper family and y=0 is already an exact solution, "
                "the formal/algebraic implicit-function argument gives y=0 as the unique "
                "local branch through every upper-family point.  That local branch "
                "therefore reduces to the upper scout and has commuting Q_1,...,Q_4."
            ),
            "not_proved": (
                "This does not exclude isolated or disconnected nonlinear mixed solutions "
                "with y!=0."
            ),
        },
        "counterexample_search": {
            "exact_rational_candidate_found": False,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "Groebner_or_saturation_runs": 0,
            "principal_patch_status": "DEFERRED_NO_SURVIVING_TANGENT_DIRECTION",
            "remaining_open_cover": "union of 131 patches y_[e]!=0",
            "reason_for_stopping": (
                "The bounded counterexample-first gate found no infinitesimal direction "
                "from the upper component into a mixed branch."
            ),
        },
        "full_witness_gates_not_run": {
            "CPOBC": 783,
            "strong_GC_same_endpoint_pairs": 1529,
            "reachable_MSR": 24,
            "determinants": 165,
            "Eq113_branches": "not run; required only for a full witness",
            "Eq139_domains": "not run; required only for a full witness",
        },
        "open_boundary": [
            "nonlinear mixed solutions disconnected from the y=0 upper family",
            "the 131 principal patches y_[e]!=0",
            "exact rational lifting if a later finite-field scout finds a candidate",
            "the unrestricted 572-scalar source-native slack system outside this ansatz",
        ],
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_mixed_xy_nonneutral_scout_v042(root: Path) -> Path:
    payload = compile_mixed_xy_nonneutral_scout_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_mixed_xy_nonneutral_scout_v042(repository_root))
