"""Bounded exact solver campaign for the v0.3.4 d=2 strata.

The solver evaluates the hash-consed operator DAG *after* a stratum
substitution.  It never expands the full generic sixteen-coordinate system.
Runs are deliberately resource bounded; timeout or memory exhaustion is
reported as unresolved and never as a no-go result.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import platform
import subprocess
import sys
import time
import tracemalloc
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.atomisation_v033 import (
    _decorated_transition_signature,
    compile_atomisation_paths_n4,
)
from universe_lab.final_theory.cpobc_d2_v032 import generator_reduction_v032
from universe_lab.final_theory.cpobc_q_presentation_v033 import (
    compile_q_presentation_n4,
)
from universe_lab.final_theory.cpobc_v031 import compile_cpobc_relations_v031
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
    V033_DERIVED_BRANCH,
    V033_LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_rational_dag_v034 import (
    BRANCH,
    SOURCE_COMMIT,
)
from universe_lab.final_theory.d2_strata_v034 import (
    S1,
    S2,
    S3,
    StratumChart,
    stratum_charts,
)
from universe_lab.final_theory.eq112_reduction_v033 import (
    compile_eq112_reduction_n4,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    stable_hash,
)
from universe_lab.final_theory.operator_gc_v033 import (
    compile_local_operator_gc_n4,
)

VERDICT_PARTIAL = "CPOBC_D2_N4_PARTIAL"
EXACT_ZERO = sp.Integer(0)


def _matrix_cancel(matrix: sp.Matrix) -> sp.Matrix:
    return matrix.applyfunc(sp.cancel)


def _matrix_adjugate(matrix: sp.Matrix) -> sp.Matrix:
    return sp.Matrix(
        [
            [matrix[1, 1], -matrix[0, 1]],
            [-matrix[1, 0], matrix[0, 0]],
        ]
    )


def _zero_condition_substitution(
    conditions: Iterable[sp.Expr],
) -> dict[sp.Symbol, sp.Expr]:
    substitutions: dict[sp.Symbol, sp.Expr] = {}
    for condition in conditions:
        reduced = sp.expand(condition.subs(substitutions))
        if reduced == 0:
            continue
        symbols = sorted(reduced.free_symbols, key=str)
        if not symbols:
            raise ValueError(f"inconsistent chart equality: {condition}")
        target = symbols[-1]
        solutions = sp.solve(reduced, target, dict=False)
        if len(solutions) != 1:
            raise ValueError(f"chart equality is not uniquely solvable: {condition}")
        substitutions[target] = sp.cancel(solutions[0].subs(substitutions))
    return substitutions


def _chart_q_matrices(chart: StratumChart) -> tuple[dict[str, sp.Matrix], dict[sp.Symbol, sp.Expr]]:
    zero_substitutions = _zero_condition_substitution(chart.zero_conditions)
    matrices: dict[str, sp.Matrix] = {}
    for stage in chart.q_indices:
        matrix = sp.Matrix(
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
        ).subs(zero_substitutions)
        matrices[f"Q_{stage}"] = _matrix_cancel(matrix)
    return matrices, zero_substitutions


@dataclass
class SympyOperatorModel:
    """Stratum-specialised exact operator DAG."""

    chart: StratumChart
    definitions: dict[str, dict[str, Any]]
    q_matrices: dict[str, sp.Matrix]
    zero_substitutions: dict[sp.Symbol, sp.Expr]
    matrices: dict[str, sp.Matrix] = field(default_factory=dict)
    inverse_factors: dict[str, dict[str, Any]] = field(default_factory=dict)
    visiting: list[str] = field(default_factory=list)

    @classmethod
    def build(cls, chart: StratumChart) -> SympyOperatorModel:
        eq112 = compile_eq112_reduction_n4()
        definitions = {
            record["node_id"]: record
            for record in eq112["dependency_DAG"]["nodes"]
        }
        q_matrices, zero_substitutions = _chart_q_matrices(chart)
        model = cls(
            chart=chart,
            definitions=definitions,
            q_matrices=q_matrices,
            zero_substitutions=zero_substitutions,
        )
        return model

    def identity(self) -> sp.Matrix:
        return sp.eye(2)

    def inverse(
        self,
        matrix: sp.Matrix,
        *,
        inverse_site: str,
        stage: int,
    ) -> sp.Matrix:
        determinant = sp.factor(sp.cancel(matrix.det()))
        factor_id = stable_hash(
            {
                "chart": self.chart.chart_id,
                "inverse_site": inverse_site,
                "factor": sp.srepr(determinant),
            }
        )
        self.inverse_factors.setdefault(
            factor_id,
            {
                "factor_id": f"chart-factor-{factor_id[:20]}",
                "factor": str(determinant),
                "factor_srepr": sp.srepr(determinant),
                "origin": f"det({inverse_site})",
                "branch": self.chart.source_index_branch,
                "stage": stage,
                "required_by": [inverse_site],
                "square_free_form": str(sp.sqf_part(determinant)),
                "multiplicity": 1,
                "saturation_status": "REQUIRED",
            },
        )
        return _matrix_cancel(_matrix_adjugate(matrix) / determinant)

    def product(
        self,
        factors: Iterable[sp.Matrix],
    ) -> sp.Matrix:
        result = self.identity()
        for factor in factors:
            result = _matrix_cancel(result * factor)
        return result

    def evaluate(self, node_id: str) -> sp.Matrix:
        existing = self.matrices.get(node_id)
        if existing is not None:
            return existing
        if node_id in self.q_matrices:
            result = self.q_matrices[node_id]
            self.matrices[node_id] = result
            return result
        if node_id in self.visiting:
            raise RuntimeError(f"operator DAG cycle: {self.visiting + [node_id]}")
        definition = self.definitions[node_id]
        self.visiting.append(node_id)
        kind = definition["kind"]
        if kind == "Q_GENERATOR":
            result = self.q_matrices[node_id]
        elif kind == "Q_GENERATOR_INVERSE":
            base = node_id.removesuffix("^-1")
            result = self.inverse(
                self.q_matrices[base],
                inverse_site=node_id,
                stage=int(definition["stage"]),
            )
        elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
            result = sp.zeros(2)
            for term in definition["terms"]:
                word = self.product(
                    self.evaluate(item) for item in term["word_nodes"]
                )
                result = _matrix_cancel(
                    result + int(term["coefficient"]) * word
                )
        elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            result = self.inverse(
                self.evaluate(definition["inverse_of_node"]),
                inverse_site=node_id,
                stage=int(definition["stage"]),
            )
        elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
            result = self.product(
                self.evaluate(item) for item in definition["ordered_word"]
            )
        else:
            raise ValueError(f"unsupported node kind: {kind}")
        self.visiting.pop()
        self.matrices[node_id] = result
        return result

    def node(self, node_id: str) -> sp.Matrix:
        if node_id in self.q_matrices:
            return self.q_matrices[node_id]
        return self.evaluate(node_id)

    def expression(
        self,
        terms: list[dict[str, Any]],
    ) -> sp.Matrix:
        result = sp.zeros(2)
        for term in terms:
            word = self.product(self.node(item) for item in term["word"])
            result = _matrix_cancel(
                result + int(term["coefficient"]) * word
            )
        return result

    def word_residual(
        self,
        lhs_word: list[str],
        rhs_word: list[str],
    ) -> sp.Matrix:
        return _matrix_cancel(
            self.product(self.node(item) for item in lhs_word)
            - self.product(self.node(item) for item in rhs_word)
        )


def _relation_stage_maps() -> tuple[dict[tuple[str, str], int], dict[str, int]]:
    compiled = compile_cpobc_relations_v031()
    cpobc: dict[tuple[str, str], int] = {}
    for relation in compiled["relations"]:
        stage = max(int(relation["stage"]["n"]), int(relation["stage"]["m"]))
        for equation in relation["denominator_cleared_form"][
            "noncommutative_polynomial_equations"
        ]:
            cpobc[(relation["relation_id"], equation["equation_id"])] = stage
    msr = {
        record["constraint_id"]: int(record["source_id"].split("-", 1)[0][1:])
        for record in compiled["MSR_operator_constraints"]
    }
    return cpobc, msr


def _source_stage_from_causet(causet_id: str) -> int:
    return int(causet_id.split("-", 1)[0][1:])


def _specialised_relation_inventory(
    source_index_branch: str,
) -> list[dict[str, Any]]:
    presentation = compile_q_presentation_n4()
    inventory = presentation["relation_inventory"]
    cpobc_stages, msr_stages = _relation_stage_maps()
    relations: list[dict[str, Any]] = []
    for record in inventory["CPOBC_residuals"]:
        relations.append(
            {
                "relation_id": (
                    f"{record['relation_id']}:{record['equation_id']}"
                ),
                "family": "CPOBC",
                "source_stage": cpobc_stages[
                    (record["relation_id"], record["equation_id"])
                ],
                "expression": record["residual_expression"],
                "provenance": {
                    "v033_digest": record[
                        "Q_dependency_residual_sha256"
                    ]
                },
            }
        )
    for record in inventory["strong_MSR_residuals"]:
        relations.append(
            {
                "relation_id": record["constraint_id"],
                "family": "STRONG_OPERATOR_MSR",
                "source_stage": msr_stages[record["constraint_id"]],
                "expression": record["residual_expression"],
                "provenance": {
                    "v033_digest": record[
                        "Q_dependency_residual_sha256"
                    ]
                },
            }
        )
    for record in inventory["local_operator_GC_residuals"]:
        relations.append(
            {
                "relation_id": record["relation_id"],
                "family": "LOCAL_OPERATOR_GC",
                "source_stage": (
                    _source_stage_from_causet(record["endpoint_causet_id"])
                    - 1
                ),
                "expression": record["residual_expression"],
                "provenance": {
                    "v033_digest": record[
                        "Q_dependency_residual_sha256"
                    ]
                },
            }
        )
    v033_branch = (
        V033_DERIVED_BRANCH
        if source_index_branch == DERIVED_BRANCH
        else V033_LITERAL_BRANCH
    )
    for index, record in enumerate(
        presentation["source_index_branches"][v033_branch][
            "path_consistency_relations"
        ]
    ):
        relations.append(
            {
                "relation_id": (
                    f"eq113:{source_index_branch}:"
                    f"{record['causet_id']}:{index:03d}"
                ),
                "family": "EQ112_PATH_CONSISTENCY",
                "source_stage": _source_stage_from_causet(
                    record["causet_id"]
                ),
                "lhs_word": record["lhs_word"],
                "rhs_word": record["rhs_word"],
                "provenance": {
                    "v033_digest": record["word_equation_sha256"],
                    "outside_n4_Q_inventory": record[
                        "outside_n4_Q_inventory"
                    ],
                },
            }
        )
    return sorted(
        relations,
        key=lambda record: (
            record["source_stage"],
            record["family"],
            record["relation_id"],
        ),
    )


def _canonical_polynomial(
    expression: sp.Expr,
    variables: tuple[sp.Symbol, ...],
) -> tuple[sp.Expr, dict[str, Any]]:
    cancelled = sp.cancel(expression)
    numerator, denominator = sp.fraction(cancelled)
    numerator = sp.factor_terms(numerator)
    if numerator == 0:
        return EXACT_ZERO, {
            "denominator": str(denominator),
            "total_degree": 0,
            "monomial_count": 0,
        }
    polynomial = sp.Poly(numerator, *variables, domain=sp.QQ)
    primitive = polynomial.monic()
    return primitive.as_expr(), {
        "denominator": str(sp.factor(denominator)),
        "total_degree": primitive.total_degree(),
        "monomial_count": len(primitive.terms()),
    }


def run_chart_scout(
    source_index_branch: str,
    chart_id: str,
    *,
    maximum_source_stage: int = 2,
    relation_limit: int = 24,
    groebner_equation_limit: int = 12,
) -> dict[str, Any]:
    """Run one bounded, exact chart scout in the current process."""

    chart = next(
        chart
        for chart in stratum_charts(source_index_branch)
        if chart.chart_id == chart_id
    )
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    tracemalloc.start()
    model = SympyOperatorModel.build(chart)
    relations = [
        record
        for record in _specialised_relation_inventory(source_index_branch)
        if int(record["source_stage"]) <= maximum_source_stage
    ][:relation_limit]
    variables = tuple(
        symbol
        for symbol in chart.variables
        if symbol not in model.zero_substitutions
    )
    polynomials: dict[str, dict[str, Any]] = {}
    processed_relations = 0
    constant_contradiction: dict[str, Any] | None = None
    for relation in relations:
        if relation["family"] == "EQ112_PATH_CONSISTENCY":
            residual = model.word_residual(
                relation["lhs_word"],
                relation["rhs_word"],
            )
        else:
            residual = model.expression(relation["expression"])
        processed_relations += 1
        for row in range(2):
            for column in range(2):
                polynomial, metrics = _canonical_polynomial(
                    residual[row, column],
                    variables,
                )
                if polynomial == 0:
                    continue
                if not polynomial.free_symbols:
                    constant_contradiction = {
                        "relation_id": relation["relation_id"],
                        "matrix_entry": [row, column],
                        "constant": str(polynomial),
                    }
                digest = stable_hash(sp.srepr(polynomial))
                polynomials.setdefault(
                    digest,
                    {
                        "polynomial_id": f"poly-{digest[:20]}",
                        "polynomial": str(polynomial),
                        "polynomial_srepr": sp.srepr(polynomial),
                        "provenance": [],
                        **metrics,
                    },
                )["provenance"].append(
                    {
                        "relation_id": relation["relation_id"],
                        "family": relation["family"],
                        "matrix_entry": [row, column],
                    }
                )
        if constant_contradiction is not None:
            break

    groebner_records = list(polynomials.values())[:groebner_equation_limit]
    groebner_status = "NOT_RUN_NO_POLYNOMIALS"
    groebner_basis: list[str] = []
    if constant_contradiction is not None:
        groebner_status = "UNIT_IDEAL_CONSTANT_RELATION"
        groebner_basis = ["1"]
    elif groebner_records and variables:
        basis = sp.groebner(
            [
                sp.sympify(record["polynomial"])
                for record in groebner_records
            ],
            *variables,
            order="grevlex",
            method="f5b",
        )
        groebner_basis = [str(polynomial) for polynomial in basis.polys]
        groebner_status = (
            "UNIT_IDEAL"
            if len(basis.polys) == 1 and basis.polys[0].is_one
            else "NONUNIT_SCOUT_BASIS"
        )
    peak_current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    wall_time = time.perf_counter() - wall_start
    cpu_time = time.process_time() - cpu_start
    exact_unsat = groebner_status in {
        "UNIT_IDEAL",
        "UNIT_IDEAL_CONSTANT_RELATION",
    }
    return {
        "schema_version": "final-theory-d2-chart-scout-v0.3.4",
        "chart": chart.chart_id,
        "stratum": chart.stratum,
        "source_index_branch": source_index_branch,
        "maximum_source_stage": maximum_source_stage,
        "branch_assumptions": chart.serialisable_record(),
        "variables": [str(symbol) for symbol in variables],
        "equations": list(polynomials.values()),
        "denominator_factors": list(model.inverse_factors.values()),
        "saturation_method": "NOT_EXECUTED_IN_NUMERATOR_SCOUT",
        "solver": "SymPy exact Groebner scout",
        "solver_version": sp.__version__,
        "groebner_order": "grevlex",
        "prime_moduli": [],
        "time_limit_seconds": None,
        "memory_limit_bytes": None,
        "resource_usage": {
            "wall_time_seconds": wall_time,
            "CPU_time_seconds": cpu_time,
            "peak_tracemalloc_bytes": peak_memory,
            "current_tracemalloc_bytes": peak_current,
            "input_relation_count": len(relations),
            "processed_relation_count": processed_relations,
            "input_polynomial_count": len(polynomials),
            "variable_count": len(variables),
            "maximum_total_degree": max(
                (record["total_degree"] for record in polynomials.values()),
                default=0,
            ),
            "monomial_count": sum(
                record["monomial_count"] for record in polynomials.values()
            ),
            "denominator_factor_count": len(model.inverse_factors),
            "groebner_input_count": len(groebner_records),
        },
        "groebner_status": groebner_status,
        "groebner_basis": groebner_basis,
        "constant_contradiction": constant_contradiction,
        "exact_unsatisfiable_subset": exact_unsat,
        "full_chart_processed": (
            len(relations)
            == len(
                [
                    record
                    for record in _specialised_relation_inventory(
                        source_index_branch
                    )
                    if int(record["source_stage"]) <= maximum_source_stage
                ]
            )
            and groebner_equation_limit >= len(polynomials)
        ),
        "exit_status": "COMPLETED",
        "unresolved_component": (
            None
            if exact_unsat
            else "SCOUT_SUBSET_NONUNIT_OR_INCOMPLETE; NO SATURATED CONCLUSION"
        ),
        "exact_numeric_distinction": "EXACT",
        "verdict": (
            "EXACT_UNSATISFIABLE_SUBSET"
            if exact_unsat
            else "EXACT_SCOUT_PARTIAL"
        ),
    }


def _subprocess_chart_scout(
    root: Path,
    chart: StratumChart,
    *,
    timeout_seconds: int,
    maximum_source_stage: int,
    relation_limit: int,
    groebner_equation_limit: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "universe_lab.final_theory.d2_solver_v034",
        "--chart",
        chart.chart_id,
        "--source-index-branch",
        chart.source_index_branch,
        "--maximum-source-stage",
        str(maximum_source_stage),
        "--relation-limit",
        str(relation_limit),
        "--groebner-equation-limit",
        str(groebner_equation_limit),
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "chart": chart.chart_id,
            "stratum": chart.stratum,
            "source_index_branch": chart.source_index_branch,
            "solver": "SymPy exact chart subprocess",
            "solver_version": sp.__version__,
            "time_limit_seconds": timeout_seconds,
            "wall_time_seconds": time.perf_counter() - started,
            "exit_status": "TIMEOUT",
            "stdout_tail": (exc.stdout or "")[-1000:],
            "stderr_tail": (exc.stderr or "")[-1000:],
            "exact_unsatisfiable_subset": False,
            "full_chart_processed": False,
            "unresolved_component": "TIMEOUT",
            "verdict": "EXACT_SCOUT_PARTIAL",
        }
    if completed.returncode != 0:
        return {
            "chart": chart.chart_id,
            "stratum": chart.stratum,
            "source_index_branch": chart.source_index_branch,
            "solver": "SymPy exact chart subprocess",
            "solver_version": sp.__version__,
            "time_limit_seconds": timeout_seconds,
            "wall_time_seconds": time.perf_counter() - started,
            "exit_status": f"ERROR_{completed.returncode}",
            "stdout_tail": completed.stdout[-1000:],
            "stderr_tail": completed.stderr[-2000:],
            "exact_unsatisfiable_subset": False,
            "full_chart_processed": False,
            "unresolved_component": "SOLVER_ERROR",
            "verdict": "EXACT_SCOUT_PARTIAL",
        }
    result = json.loads(completed.stdout)
    result["time_limit_seconds"] = timeout_seconds
    return result


def cas_inventory(root: Path) -> dict[str, Any]:
    """Record local and already-configured container CAS availability."""

    inventory: dict[str, Any] = {
        "python": platform.python_version(),
        "sympy": sp.__version__,
        "python_flint": "UNKNOWN",
        "sage": "NOT_AVAILABLE",
        "singular": "NOT_AVAILABLE",
        "macaulay2": "NOT_AVAILABLE",
        "os": platform.platform(),
    }
    try:
        import flint

        inventory["python_flint"] = flint.__version__
    except ImportError:
        inventory["python_flint"] = "NOT_AVAILABLE"
    compose = root / "compose.yaml"
    if compose.is_file():
        command = [
            "docker",
            "compose",
            "exec",
            "-T",
            "sage",
            "sage",
            "-c",
            (
                "from sage.version import version; import json; "
                "print(json.dumps({'sage': version, "
                "'singular': singular.version().splitlines()[0]}))"
            ),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            completed = None
        if completed is not None and completed.returncode == 0:
            try:
                response = json.loads(
                    completed.stdout.strip().splitlines()[-1]
                )
            except (IndexError, json.JSONDecodeError):
                response = {}
            for name in ("sage", "singular"):
                value = response.get(name)
                if isinstance(value, str) and value:
                    inventory[name] = value
    return inventory


@dataclass
class ScalarS3Model:
    """Independent scalar specialisation of the v0.3.3 dependency records."""

    definitions: dict[str, dict[str, Any]]
    q_values: dict[str, sp.Rational]
    cache: dict[str, sp.Expr] = field(default_factory=dict)

    @classmethod
    def build(cls) -> ScalarS3Model:
        eq112 = compile_eq112_reduction_n4()
        return cls(
            definitions={
                record["node_id"]: record
                for record in eq112["dependency_DAG"]["nodes"]
            },
            q_values={
                "Q_1": sp.Rational(2),
                "Q_2": sp.Rational(3),
                "Q_3": sp.Rational(5),
                "Q_4": sp.Rational(7),
                "Q_5": sp.Rational(11),
            },
        )

    def evaluate(self, node_id: str) -> sp.Expr:
        existing = self.cache.get(node_id)
        if existing is not None:
            return existing
        if node_id in self.q_values:
            result: sp.Expr = self.q_values[node_id]
        else:
            definition = self.definitions[node_id]
            kind = definition["kind"]
            if kind == "Q_GENERATOR":
                result = self.q_values[node_id]
            elif kind == "Q_GENERATOR_INVERSE":
                result = 1 / self.q_values[node_id.removesuffix("^-1")]
            elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
                result = sum(
                    int(term["coefficient"])
                    * sp.prod(
                        self.evaluate(item) for item in term["word_nodes"]
                    )
                    for term in definition["terms"]
                )
            elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
                result = 1 / self.evaluate(definition["inverse_of_node"])
            elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
                result = sp.prod(
                    self.evaluate(item)
                    for item in definition["ordered_word"]
                )
            else:
                raise ValueError(f"unexpected scalar DAG node kind: {kind}")
        result = sp.cancel(result)
        self.cache[node_id] = result
        return result

    def word(self, word: Iterable[str]) -> sp.Expr:
        return sp.cancel(sp.prod(self.evaluate(item) for item in word))


def _scalar_token_node(token: str) -> str:
    inverse = token.endswith("^-1")
    base = token.removesuffix("^-1")
    if base.startswith("Q_"):
        return base + ("^-1" if inverse else "")
    if base.startswith("G_p"):
        return f"G:{base.removeprefix('G_')}" + (":INV" if inverse else "")
    raise ValueError(f"unexpected reduced generator token: {token}")


def scalar_s3_representation_certificate_v034() -> dict[str, Any]:
    """Directly verify a rational scalar 2 by 2 representation."""

    model = ScalarS3Model.build()
    reduction = generator_reduction_v032()
    occurrences: dict[str, sp.Expr] = {}
    occurrence_records: dict[str, dict[str, Any]] = {}
    for record in reduction["reduction_map"]:
        value = sp.cancel(
            sum(
                int(term["coefficient"])
                * sp.prod(
                    model.evaluate(_scalar_token_node(token))
                    for token in term["word"]
                )
                for term in record["reduced_expression"]
            )
        )
        occurrences[record["occurrence_id"]] = value
        occurrence_records[record["occurrence_id"]] = record

    compiled = compile_cpobc_relations_v031()
    cpobc_checks = []
    for relation in compiled["relations"]:
        aliases = {
            alias: transition["occurrence_id"]
            for alias, transition in relation["transition_orbit"].items()
        }
        for equation in relation["denominator_cleared_form"][
            "noncommutative_polynomial_equations"
        ]:
            lhs = sp.prod(
                occurrences[aliases[alias]]
                for alias in equation["lhs_word"]
            )
            rhs = sp.prod(
                occurrences[aliases[alias]]
                for alias in equation["rhs_word"]
            )
            residual = sp.cancel(lhs - rhs)
            cpobc_checks.append(
                {
                    "relation_id": relation["relation_id"],
                    "equation_id": equation["equation_id"],
                    "residual": str(residual),
                    "zero": residual == 0,
                }
            )

    msr_checks = []
    for constraint in compiled["MSR_operator_constraints"]:
        residual = sp.Integer(constraint["identity_coefficient"])
        residual += sum(
            int(term["coefficient"])
            * occurrences[term["transition_id"]]
            for term in constraint["terms"]
        )
        residual = sp.cancel(residual)
        msr_checks.append(
            {
                "constraint_id": constraint["constraint_id"],
                "residual": str(residual),
                "zero": residual == 0,
            }
        )

    signature_values: dict[tuple[tuple[str, int], ...], sp.Expr] = {}
    for occurrence_id, value in occurrences.items():
        record = occurrence_records[occurrence_id]
        signature = _decorated_transition_signature(
            tuple(record["source_relation_rows"]),
            int(record["precursor_code"]),
        )
        signature_values[tuple(sorted(signature.items()))] = value
    local_gc = compile_local_operator_gc_n4()
    local_path_values: dict[str, sp.Expr] = {}
    endpoint_paths: dict[str, list[str]] = {}
    for stage_paths in local_gc["path_inventory"].values():
        for path in stage_paths:
            symbols = {
                transition["quotient_operator_symbol"]: signature_values[
                    tuple(sorted(transition["quotient_signature"].items()))
                ]
                for transition in path["transitions"]
            }
            value = sp.prod(
                symbols[symbol]
                for symbol in path["ordered_operator_word_later_on_left"]
            )
            local_path_values[path["path_id"]] = sp.cancel(value)
            endpoint_paths.setdefault(path["endpoint_causet_id"], []).append(
                path["path_id"]
            )
    same_endpoint_checks = []
    for endpoint, path_ids in sorted(endpoint_paths.items()):
        for left_id, right_id in itertools.combinations(sorted(path_ids), 2):
            residual = sp.cancel(
                local_path_values[left_id] - local_path_values[right_id]
            )
            same_endpoint_checks.append(
                {
                    "endpoint_causet_id": endpoint,
                    "lhs_path_id": left_id,
                    "rhs_path_id": right_id,
                    "residual": str(residual),
                    "zero": residual == 0,
                }
            )

    basis_checks = []
    for relation in local_gc["generating_relation_basis"]:
        residual = sp.cancel(
            local_path_values[relation["lhs_path_id"]]
            - local_path_values[relation["rhs_path_id"]]
        )
        basis_checks.append(
            {
                "relation_id": relation["relation_id"],
                "residual": str(residual),
                "zero": residual == 0,
            }
        )

    eq112 = compile_eq112_reduction_n4()
    atomisation_checks = []
    for path in eq112["path_reductions"]:
        value = model.word(path["G_reduced_ordered_word"])
        expected = model.q_values[f"Q_{path['stage']}"]
        residual = sp.cancel(value - expected)
        atomisation_checks.append(
            {
                "path_id": path["path_id"],
                "causet_id": path["causet_id"],
                "value": str(value),
                "expected_Q_value": str(expected),
                "residual": str(residual),
                "zero": residual == 0,
            }
        )

    branch_checks: dict[str, list[dict[str, Any]]] = {}
    v033_branch_map = {
        DERIVED_BRANCH: "EQ113_QN_BRANCH",
        LITERAL_BRANCH: "EQ113_QN_PLUS_1_BRANCH",
    }
    for branch, v033_branch in v033_branch_map.items():
        records = []
        for index, relation in enumerate(
            eq112["path_consistency_branches"][v033_branch]
        ):
            residual = sp.cancel(
                model.word(relation["lhs_word"])
                - model.word(relation["rhs_word"])
            )
            records.append(
                {
                    "relation_index": index,
                    "causet_id": relation["causet_id"],
                    "Q_token": relation["Q_token"],
                    "residual": str(residual),
                    "zero": residual == 0,
                }
            )
        branch_checks[branch] = records

    inverse_checks = []
    for stage in range(1, 5):
        value = model.q_values[f"Q_{stage}"]
        inverse_checks.append(
            {
                "inverse_site": f"Q_{stage}^-1",
                "value": str(1 / value),
                "left_residual": str(sp.cancel((1 / value) * value - 1)),
                "right_residual": str(sp.cancel(value * (1 / value) - 1)),
                "determinant": str(value**2),
                "passed": value != 0,
            }
        )
    for node_id, definition in sorted(model.definitions.items()):
        if definition["kind"] != "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            continue
        forward = model.evaluate(definition["inverse_of_node"])
        inverse = model.evaluate(node_id)
        inverse_checks.append(
            {
                "inverse_site": node_id,
                "value": str(inverse),
                "left_residual": str(sp.cancel(inverse * forward - 1)),
                "right_residual": str(sp.cancel(forward * inverse - 1)),
                "determinant": str(forward**2),
                "passed": forward != 0,
            }
        )

    transition_records = [
        {
            "occurrence_id": occurrence_id,
            "operator_variable": occurrence_records[occurrence_id][
                "operator_variable"
            ],
            "stage": occurrence_records[occurrence_id]["stage"],
            "source_id": occurrence_records[occurrence_id]["source_id"],
            "target_id": occurrence_records[occurrence_id]["target_id"],
            "scalar_value": str(value),
            "matrix": [[str(value), "0"], ["0", str(value)]],
            "determinant": str(sp.cancel(value**2)),
            "nonsingular": value != 0,
        }
        for occurrence_id, value in sorted(occurrences.items())
    ]
    atomisation = compile_atomisation_paths_n4()
    passed = bool(
        len(cpobc_checks) == 783
        and all(record["zero"] for record in cpobc_checks)
        and len(msr_checks) == 24
        and all(record["zero"] for record in msr_checks)
        and len(basis_checks) == 320
        and all(record["zero"] for record in basis_checks)
        and len(same_endpoint_checks) == 1529
        and all(record["zero"] for record in same_endpoint_checks)
        and len(atomisation_checks) == 34
        and all(record["zero"] for record in atomisation_checks)
        and atomisation["counts"]["atomisation_steps"] == 76
        and all(
            record["zero"]
            for records in branch_checks.values()
            for record in records
        )
        and len(inverse_checks) == 26
        and all(record["passed"] for record in inverse_checks)
        and len(transition_records) == 165
        and all(record["nonsingular"] for record in transition_records)
    )
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-s3-scalar-representation-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "Q embedded in any characteristic-zero field",
        "stratum": S3,
        "chart": "S3_EXACT_SCALAR_PRIME_FIXTURE",
        "Q_assignment": {
            "Q_1": [["2", "0"], ["0", "2"]],
            "Q_2": [["3", "0"], ["0", "3"]],
            "Q_3": [["5", "0"], ["0", "5"]],
            "Q_4": [["7", "0"], ["0", "7"]],
            "Q_5_literal_branch_only": [["11", "0"], ["0", "11"]],
        },
        "transition_assignment": transition_records,
        "checks": {
            "original_CPOBC": cpobc_checks,
            "strong_operator_MSR": msr_checks,
            "local_operator_GC_basis": basis_checks,
            "all_same_endpoint_path_equalities": same_endpoint_checks,
            "atomisation_paths": atomisation_checks,
            "atomisation_step_count": atomisation["counts"][
                "atomisation_steps"
            ],
            "source_index_branches": branch_checks,
            "inverse_sites": inverse_checks,
        },
        "counts": {
            "original_CPOBC_relation_records": 641,
            "original_CPOBC_word_equations": len(cpobc_checks),
            "strong_operator_MSR_constraints": len(msr_checks),
            "local_operator_GC_basis_relations": len(basis_checks),
            "same_endpoint_path_equalities": len(same_endpoint_checks),
            "atomisation_paths": len(atomisation_checks),
            "atomisation_steps": atomisation["counts"]["atomisation_steps"],
            "transition_occurrences": len(transition_records),
            "inverse_sites": len(inverse_checks),
            "Eq113_relations_per_branch": {
                branch: len(records)
                for branch, records in branch_checks.items()
            },
        },
        "exact_commutator": {
            "all_transition_commutators_zero": True,
            "noncommutative_witness": None,
        },
        "saturation_method": (
            "explicit exact point; every denominator and determinant is "
            "evaluated nonzero directly"
        ),
        "exact_numeric_distinction": "EXACT_RATIONAL",
        "finite_scope_only": True,
        "infinite_extension_claimed": False,
        "passed": passed,
        "verdict": (
            "CPOBC_D2_N4_COMMUTATIVE_REPRESENTATION_CERTIFIED"
            if passed
            else "CPOBC_D2_N4_SCALAR_FIXTURE_FAILED"
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "Q_assignment": payload["Q_assignment"],
            "transition_values": [
                (record["occurrence_id"], record["scalar_value"])
                for record in transition_records
            ],
            "counts": payload["counts"],
            "verdict": payload["verdict"],
        }
    )
    return payload


def run_solver_campaign_v034(
    root: Path,
    *,
    timeout_seconds_per_chart: int = 20,
    representative_charts_per_stratum: int = 1,
    include_deep_scouts: bool = True,
) -> dict[str, Any]:
    """Run bounded exact representatives and record every unprocessed chart."""

    selected: list[StratumChart] = []
    all_charts: list[StratumChart] = []
    for source_index_branch in (DERIVED_BRANCH, LITERAL_BRANCH):
        charts = stratum_charts(source_index_branch)
        all_charts.extend(charts)
        for stratum in (S1, S2, S3):
            selected.extend(
                [
                    chart
                    for chart in charts
                    if chart.stratum == stratum
                ][:representative_charts_per_stratum]
            )
    runs = [
        _subprocess_chart_scout(
            root,
            chart,
            timeout_seconds=timeout_seconds_per_chart,
            maximum_source_stage=2,
            relation_limit=16,
            groebner_equation_limit=8,
        )
        for chart in selected
    ]
    if include_deep_scouts:
        deep_charts = [
            next(
                chart
                for chart in all_charts
                if chart.source_index_branch == source_index_branch
                and chart.stratum == stratum
            )
            for source_index_branch in (DERIVED_BRANCH, LITERAL_BRANCH)
            for stratum in (S1, S2)
        ]
        runs.extend(
            _subprocess_chart_scout(
                root,
                chart,
                timeout_seconds=max(timeout_seconds_per_chart, 45),
                maximum_source_stage=3,
                relation_limit=16,
                groebner_equation_limit=8,
            )
            for chart in deep_charts
        )
    attempted_ids = {run["chart"] for run in runs}
    unresolved = [
        {
            "chart": chart.chart_id,
            "stratum": chart.stratum,
            "source_index_branch": chart.source_index_branch,
            "reason": (
                "NOT_SELECTED_IN_BOUNDED_CAMPAIGN"
                if chart.chart_id not in attempted_ids
                else (
                    "ALL_ATTEMPTS_PARTIAL_OR_TIMED_OUT"
                    if all(
                        run["unresolved_component"] is not None
                        for run in runs
                        if run["chart"] == chart.chart_id
                    )
                    else None
                )
            ),
        }
        for chart in all_charts
        if chart.chart_id not in attempted_ids
        or all(
            run["unresolved_component"] is not None
            for run in runs
            if run["chart"] == chart.chart_id
        )
    ]
    run_counts = Counter(run["exit_status"] for run in runs)
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-solver-campaign-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "CAS_inventory": cas_inventory(root),
        "strategy": [
            "stratum substitution before expansion",
            "exact cancellation at each 2x2 matrix DAG node",
            "incremental source-stage subset",
            "bounded characteristic-zero Groebner scout",
        ],
        "runs": runs,
        "run_status_counts": dict(sorted(run_counts.items())),
        "all_chart_count": len(all_charts),
        "attempted_chart_count": len(attempted_ids),
        "solver_run_count": len(runs),
        "unresolved_components": unresolved,
        "complete_strata": [],
        "representation_candidates": [
            scalar_s3_representation_certificate_v034()
        ],
        "unit_ideal_certificates": [
            {
                "chart": run["chart"],
                "source_index_branch": run["source_index_branch"],
                "scope": (
                    f"relations through source stage "
                    f"{run.get('maximum_source_stage', 2)}"
                ),
                "certificate": run.get("groebner_basis", []),
                "saturation_executed": False,
            }
            for run in runs
            if run["exact_unsatisfiable_subset"]
        ],
        "finite_d2_verdict": VERDICT_PARTIAL,
        "global_conditional_verdict": None,
        "exact_numeric_distinction": "EXACT_BOUNDED_SCOUTS_ONLY",
        "passed": True,
        "verdict": VERDICT_PARTIAL,
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "runs": [
                {
                    "chart": run["chart"],
                    "exit_status": run["exit_status"],
                    "verdict": run["verdict"],
                    "exact_unsatisfiable_subset": run[
                        "exact_unsatisfiable_subset"
                    ],
                }
                for run in runs
            ],
            "unresolved": unresolved,
        }
    )
    return payload


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart")
    parser.add_argument("--source-index-branch")
    parser.add_argument("--maximum-source-stage", type=int, default=2)
    parser.add_argument("--relation-limit", type=int, default=24)
    parser.add_argument("--groebner-equation-limit", type=int, default=12)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _argument_parser().parse_args(argv)
    if not arguments.chart or not arguments.source_index_branch:
        raise SystemExit("--chart and --source-index-branch are required")
    result = run_chart_scout(
        arguments.source_index_branch,
        arguments.chart,
        maximum_source_stage=arguments.maximum_source_stage,
        relation_limit=arguments.relation_limit,
        groebner_equation_limit=arguments.groebner_equation_limit,
    )
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write(os.linesep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
