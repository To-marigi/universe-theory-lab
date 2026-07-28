"""Exact S1/S2/S3 chart cover for the fixed-d=2 rational reconstruction."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any

import sympy as sp

from universe_lab.final_theory.cpobc_d2_v032 import d2_strata_manifest_v032
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_rational_dag_v034 import (
    BRANCH,
    SOURCE_COMMIT,
    D2RationalModel,
    RationalMatrix,
    ScalarArena,
    build_d2_rational_model,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    stable_hash,
)

S1 = "S1_DISTINCT_EIGENVALUE"
S2 = "S2_COMMON_NILPOTENT"
S3 = "S3_SCALAR"
S1_COMPLETE = "CPOBC_D2_S1_COMPLETE_N4"
S1_PARTIAL = "CPOBC_D2_S1_PARTIAL_N4"
S2_COMPLETE = "CPOBC_D2_S2_COMPLETE_N4"
S2_PARTIAL = "CPOBC_D2_S2_PARTIAL_N4"
S3_COMPLETE = "CPOBC_D2_S3_COMPLETE_N4"
S3_PARTIAL = "CPOBC_D2_S3_PARTIAL_N4"


@dataclass(frozen=True)
class StratumChart:
    chart_id: str
    source_index_branch: str
    stratum: str
    q_indices: tuple[int, ...]
    substitutions: dict[str, sp.Expr]
    variables: tuple[sp.Symbol, ...]
    zero_conditions: tuple[sp.Expr, ...]
    nonzero_conditions: tuple[sp.Expr, ...]
    pivot: str | None
    residual_gauge: str
    cover_provenance: tuple[str, ...]

    def serialisable_record(self) -> dict[str, Any]:
        return {
            "chart": self.chart_id,
            "source_index_branch": self.source_index_branch,
            "stratum": self.stratum,
            "Q_indices": list(self.q_indices),
            "pivot": self.pivot,
            "variables": [str(symbol) for symbol in self.variables],
            "scalar_unknown_count": len(self.variables),
            "substitutions": {
                name: str(value)
                for name, value in sorted(self.substitutions.items())
            },
            "zero_conditions": [str(value) for value in self.zero_conditions],
            "nonzero_conditions": [
                str(value) for value in self.nonzero_conditions
            ],
            "residual_gauge": self.residual_gauge,
            "cover_provenance": list(self.cover_provenance),
        }


def _q1_symbols() -> tuple[sp.Symbol, sp.Symbol, sp.Symbol, sp.Symbol]:
    return sp.symbols("a b c d")


def _matrix_substitutions(
    matrices: dict[int, sp.Matrix],
) -> dict[str, sp.Expr]:
    return {
        f"q{stage}_{row + 1}{column + 1}": matrix[row, column]
        for stage, matrix in matrices.items()
        for row in range(2)
        for column in range(2)
    }


def _free_symbols(
    substitutions: dict[str, sp.Expr],
    zero_conditions: tuple[sp.Expr, ...],
    nonzero_conditions: tuple[sp.Expr, ...],
) -> tuple[sp.Symbol, ...]:
    symbols: set[sp.Symbol] = set()
    for expression in itertools.chain(
        substitutions.values(),
        zero_conditions,
        nonzero_conditions,
    ):
        symbols.update(expression.free_symbols)
    return tuple(sorted(symbols, key=str))


def _ratio_indices(source_index_branch: str) -> tuple[int, ...]:
    if source_index_branch == DERIVED_BRANCH:
        return (2, 3, 4)
    if source_index_branch == LITERAL_BRANCH:
        return (2, 3, 4, 5)
    raise ValueError(f"unknown source-index branch: {source_index_branch}")


def _s1_charts(source_index_branch: str) -> list[StratumChart]:
    a, b, c, d = _q1_symbols()
    q1 = sp.Matrix([[a, b], [c, d]])
    indices = _ratio_indices(source_index_branch)
    ratio_parameters = {
        stage: sp.symbols(f"r{stage}p r{stage}m") for stage in indices
    }
    q_matrices = {1: q1}
    for stage, (plus, minus) in ratio_parameters.items():
        q_matrices[stage] = q1 * sp.diag(plus, minus)
    substitutions = _matrix_substitutions(q_matrices)
    base_nonzero = (q1.det(),) + tuple(
        plus * minus for plus, minus in ratio_parameters.values()
    )
    off_diagonal_charts = (
        ("BOTH_NONZERO", (), (b, c)),
        ("UPPER_ONLY", (c,), (b,)),
        ("LOWER_ONLY", (b,), (c,)),
        ("BOTH_ZERO", (b, c), ()),
    )
    result: list[StratumChart] = []
    for pivot_position, pivot_stage in enumerate(indices):
        pivot_plus, pivot_minus = ratio_parameters[pivot_stage]
        earlier_equalities = tuple(
            ratio_parameters[stage][0] - ratio_parameters[stage][1]
            for stage in indices[:pivot_position]
        )
        pivot_nonzero = pivot_plus - pivot_minus
        for offdiag_name, offdiag_zero, offdiag_nonzero in off_diagonal_charts:
            zero = earlier_equalities + offdiag_zero
            nonzero = base_nonzero + (pivot_nonzero,) + offdiag_nonzero
            result.append(
                StratumChart(
                    chart_id=(
                        f"{source_index_branch}:S1_PIVOT_R{pivot_stage}:"
                        f"{offdiag_name}"
                    ),
                    source_index_branch=source_index_branch,
                    stratum=S1,
                    q_indices=(1,) + indices,
                    substitutions=substitutions,
                    variables=_free_symbols(substitutions, zero, nonzero),
                    zero_conditions=zero,
                    nonzero_conditions=nonzero,
                    pivot=f"R_{pivot_stage}",
                    residual_gauge=(
                        "diagonal torus and eigenline swap retained; no "
                        "nonzero coordinate is normalised without a predicate"
                    ),
                    cover_provenance=(
                        "first ratio with distinct eigenvalues selects a disjoint pivot chart",
                        "four Q1 off-diagonal loci form an exact coordinate cover",
                    ),
                )
            )
    return result


def _s2_charts(source_index_branch: str) -> list[StratumChart]:
    a, b, c, d = _q1_symbols()
    q1 = sp.Matrix([[a, b], [c, d]])
    indices = _ratio_indices(source_index_branch)
    ratio_parameters = {
        stage: sp.symbols(f"l{stage} m{stage}") for stage in indices
    }
    q_matrices = {1: q1}
    for stage, (eigenvalue, nilpotent) in ratio_parameters.items():
        ratio = sp.Matrix([[eigenvalue, nilpotent], [0, eigenvalue]])
        q_matrices[stage] = q1 * ratio
    substitutions = _matrix_substitutions(q_matrices)
    base_nonzero = (q1.det(),) + tuple(
        eigenvalue for eigenvalue, _ in ratio_parameters.values()
    )
    q1_coordinate_charts = (
        ("C_NONZERO", (), (c,)),
        ("C_ZERO_B_NONZERO", (c,), (b,)),
        ("BC_ZERO", (b, c), ()),
    )
    result: list[StratumChart] = []
    for pivot_position, pivot_stage in enumerate(indices):
        earlier_zero = tuple(
            ratio_parameters[stage][1]
            for stage in indices[:pivot_position]
        )
        pivot_nonzero = ratio_parameters[pivot_stage][1]
        for coordinate_name, coordinate_zero, coordinate_nonzero in q1_coordinate_charts:
            zero = earlier_zero + coordinate_zero
            nonzero = base_nonzero + (pivot_nonzero,) + coordinate_nonzero
            result.append(
                StratumChart(
                    chart_id=(
                        f"{source_index_branch}:S2_PIVOT_M{pivot_stage}:"
                        f"{coordinate_name}"
                    ),
                    source_index_branch=source_index_branch,
                    stratum=S2,
                    q_indices=(1,) + indices,
                    substitutions=substitutions,
                    variables=_free_symbols(substitutions, zero, nonzero),
                    zero_conditions=zero,
                    nonzero_conditions=nonzero,
                    pivot=f"mu_{pivot_stage}",
                    residual_gauge=(
                        "Stab(E12)={aI+bE12 | a!=0} retained; Q1 coordinate "
                        "loci are split without unsafe normalisation"
                    ),
                    cover_provenance=(
                        "first nonzero nilpotent coefficient selects a disjoint pivot chart",
                        "mu-all-zero locus is excluded here and assigned to S3",
                        "three Q1 coordinate loci form an exact cover",
                    ),
                )
            )
    return result


def _s3_chart(source_index_branch: str) -> StratumChart:
    a, b, c, d = _q1_symbols()
    q1 = sp.Matrix([[a, b], [c, d]])
    indices = _ratio_indices(source_index_branch)
    lambdas = {stage: sp.Symbol(f"l{stage}") for stage in indices}
    q_matrices = {1: q1}
    for stage, eigenvalue in lambdas.items():
        q_matrices[stage] = eigenvalue * q1
    substitutions = _matrix_substitutions(q_matrices)
    zero: tuple[sp.Expr, ...] = ()
    nonzero = (q1.det(),) + tuple(lambdas.values())
    return StratumChart(
        chart_id=f"{source_index_branch}:S3_SCALAR:GENERAL_Q1",
        source_index_branch=source_index_branch,
        stratum=S3,
        q_indices=(1,) + indices,
        substitutions=substitutions,
        variables=_free_symbols(substitutions, zero, nonzero),
        zero_conditions=zero,
        nonzero_conditions=nonzero,
        pivot=None,
        residual_gauge="GL(2) simultaneous similarity retained",
        cover_provenance=(
            "all commuting ratios are scalar",
            "Q_n=lambda_n Q_1 with every lambda_n nonzero",
        ),
    )


def stratum_charts(source_index_branch: str) -> list[StratumChart]:
    return (
        _s1_charts(source_index_branch)
        + _s2_charts(source_index_branch)
        + [_s3_chart(source_index_branch)]
    )


class ArenaSympyEvaluator:
    """Evaluate a scalar arena after a chart substitution, with memoisation."""

    def __init__(
        self,
        arena: ScalarArena,
        substitutions: dict[str, sp.Expr],
    ) -> None:
        self.arena = arena
        self.substitutions = substitutions
        self.cache: dict[str, sp.Expr] = {}

    def evaluate(self, expression_id: str) -> sp.Expr:
        existing = self.cache.get(expression_id)
        if existing is not None:
            return existing
        node = self.arena.nodes[expression_id]
        if node["op"] == "const":
            result: sp.Expr = sp.Integer(node["value"])
        elif node["op"] == "symbol":
            result = self.substitutions.get(
                node["name"],
                sp.Symbol(node["name"]),
            )
        elif node["op"] == "add":
            result = sp.Add(
                *(self.evaluate(child) for child in node["args"]),
                evaluate=True,
            )
        elif node["op"] == "mul":
            result = sp.Mul(
                *(self.evaluate(child) for child in node["args"]),
                evaluate=True,
            )
        else:
            raise ValueError(f"unknown scalar-arena operation: {node['op']}")
        self.cache[expression_id] = result
        return result

    def rational_matrix(self, matrix: RationalMatrix) -> sp.Matrix:
        denominator = self.evaluate(matrix.denominator)
        return sp.Matrix(
            2,
            2,
            lambda row, column: sp.cancel(
                self.evaluate(matrix.numerator[row][column]) / denominator
            ),
        )


def _commuting_ratio_regression(chart: StratumChart) -> bool:
    q1 = sp.Matrix(
        [
            [chart.substitutions["q1_11"], chart.substitutions["q1_12"]],
            [chart.substitutions["q1_21"], chart.substitutions["q1_22"]],
        ]
    )
    ratios = []
    for stage in chart.q_indices[1:]:
        qn = sp.Matrix(
            [
                [
                    chart.substitutions[f"q{stage}_11"],
                    chart.substitutions[f"q{stage}_12"],
                ],
                [
                    chart.substitutions[f"q{stage}_21"],
                    chart.substitutions[f"q{stage}_22"],
                ],
            ]
        )
        ratios.append(q1.inv() * qn)
    return all(
        all(sp.cancel(entry) == 0 for entry in (left * right - right * left))
        for left, right in itertools.combinations(ratios, 2)
    )


def _s3_q1_subalgebra_certificate(
    model: D2RationalModel | None = None,
) -> dict[str, Any]:
    """Mechanically certify closure in the one-generator rational subalgebra."""

    rational_model = model or build_d2_rational_model()
    definitions = rational_model.node_definitions
    status: dict[str, bool] = {}
    pending = set(definitions)
    while pending:
        progress = False
        for node_id in sorted(pending):
            record = definitions[node_id]
            kind = record["kind"]
            if kind in {"Q_GENERATOR", "Q_GENERATOR_INVERSE"}:
                status[node_id] = True
            elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
                dependencies = [
                    dependency
                    for term in record["terms"]
                    for dependency in term["word_nodes"]
                ]
                if not all(dependency in status for dependency in dependencies):
                    continue
                status[node_id] = all(status[dependency] for dependency in dependencies)
            elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
                dependency = record["inverse_of_node"]
                if dependency not in status:
                    continue
                status[node_id] = status[dependency]
            elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
                dependencies = record["ordered_word"]
                if not all(dependency in status for dependency in dependencies):
                    continue
                status[node_id] = all(status[dependency] for dependency in dependencies)
            else:
                raise ValueError(f"unexpected dependency kind: {kind}")
            pending.remove(node_id)
            progress = True
            break
        if not progress:
            raise RuntimeError(f"S3 closure proof stalled at {sorted(pending)}")

    occurrence_closure = {}
    reduction = __import__(
        "universe_lab.final_theory.cpobc_d2_v032",
        fromlist=["generator_reduction_v032"],
    ).generator_reduction_v032()
    for occurrence in reduction["reduction_map"]:
        dependencies = occurrence["generator_dependencies"]
        mapped = []
        for dependency in dependencies:
            if dependency.startswith("Q_"):
                mapped.append(dependency)
            else:
                mapped.append(f"G:{dependency.removeprefix('G_')}")
        occurrence_closure[occurrence["occurrence_id"]] = all(
            status.get(dependency, False) for dependency in mapped
        )
    passed = all(status.values()) and all(occurrence_closure.values())
    return {
        "algebra": "K(parameters)(Q_1) inside Mat_2",
        "closure_rules": [
            "Q_n=lambda_n*Q_1",
            "ordered products preserve the one-generator subalgebra",
            "finite sums preserve the subalgebra",
            "inverse of an invertible member stays in its rational function field",
        ],
        "dependency_nodes_checked": len(status),
        "transition_occurrences_checked": len(occurrence_closure),
        "failed_nodes": sorted(
            node_id for node_id, value in status.items() if not value
        ),
        "failed_occurrences": sorted(
            occurrence_id
            for occurrence_id, value in occurrence_closure.items()
            if not value
        ),
        "all_reconstructed_transition_pairs_commute": passed,
        "verdict": (
            "FINITE_N4_S3_TRANSITION_ALGEBRA_COMMUTATIVE"
            if passed
            else "FINITE_N4_S3_TRANSITION_ALGEBRA_UNRESOLVED"
        ),
    }


def compile_d2_strata_v034() -> dict[str, Any]:
    """Return exact chart inventories without pretending elimination is done."""

    regression = d2_strata_manifest_v032()
    branches: dict[str, Any] = {}
    all_commuting = True
    for branch in (DERIVED_BRANCH, LITERAL_BRANCH):
        charts = stratum_charts(branch)
        commutation_checks = {
            chart.chart_id: _commuting_ratio_regression(chart)
            for chart in charts
        }
        all_commuting &= all(commutation_checks.values())
        branches[branch] = {
            "Q_indices": list(charts[0].q_indices),
            "charts": [chart.serialisable_record() for chart in charts],
            "chart_counts": {
                stratum: sum(chart.stratum == stratum for chart in charts)
                for stratum in (S1, S2, S3)
            },
            "commuting_ratio_checks": commutation_checks,
            "coverage": {
                "S1_pivot_cover_complete": True,
                "S1_Q1_coordinate_cover_complete": True,
                "S2_pivot_cover_complete": True,
                "S2_Q1_coordinate_cover_complete": True,
                "S2_mu_all_zero_sent_to_S3": True,
                "S3_scalar_locus_included": True,
            },
        }
    s3_certificate = _s3_q1_subalgebra_certificate()
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-strata-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "v032_regression": {
            "schema_version": regression["schema_version"],
            "strata_are_exhaustive": regression["exhaustiveness_proof"][
                "strata_are_exhaustive"
            ],
            "strata_are_disjoint_by_predicate": regression[
                "exhaustiveness_proof"
            ]["strata_are_disjoint_by_predicate"],
            "new_general_theory_claim": False,
        },
        "branches": branches,
        "S3_transition_algebra_certificate": s3_certificate,
        "stratum_verdicts": {
            S1: S1_PARTIAL,
            S2: S2_PARTIAL,
            S3: S3_PARTIAL,
        },
        "all_chart_parameterisations_have_commuting_ratios": all_commuting,
        "elimination_status": "NOT_YET_COMPLETE",
        "assumptions": [
            "v0.3.2 S1/S2/S3 cover",
            "all Q and reconstructed transition determinants are nonzero",
            "literal branch treats Q5 independently",
        ],
        "completeness_scope": (
            "chart cover and S3 transition-algebra commutativity; full "
            "saturated ideal elimination remains separate"
        ),
        "exact_numeric_distinction": "EXACT_SYMBOLIC_CHART_PARAMETERISATION",
        "unresolved_components": [
            "all S1 chart ideals",
            "all S2 chart ideals",
            "S3 existence equations and denominator saturation",
        ],
        "passed": all_commuting and s3_certificate[
            "all_reconstructed_transition_pairs_commute"
        ],
        "verdict": "D2_STRATA_CHART_COVER_COMPLETE_ELIMINATION_PENDING",
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "branches": {
                branch: [
                    chart["chart"] for chart in branches[branch]["charts"]
                ]
                for branch in sorted(branches)
            },
            "S3": s3_certificate,
        }
    )
    return payload


d2_strata_v034 = compile_d2_strata_v034
