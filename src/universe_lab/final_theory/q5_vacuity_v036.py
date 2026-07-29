"""Exact v0.3.6 proof that the literal-branch Q5 witness is vacuous.

The frozen literal system contains twelve canonical scalar numerators with a
Q5 dependency.  This module fixes the v0.3.5 witness values of Q1 through Q4,
leaves Q5 as a symbolic 2x2 matrix, and evaluates those exact compiled
numerators.  It also audits the source and implementation separation between
paper Eqs. (113) and (139).

No Sage, Singular, finite-field scout, Groebner basis, or stage-5 compiler is
used.  The result is an exact characteristic-zero symbolic identity.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.d2_localisation_v034 import LITERAL_BRANCH
from universe_lab.final_theory.d2_strata_v034 import S1, stratum_charts
from universe_lab.final_theory.eq112_reduction_v033 import (
    compile_eq112_reduction_n4,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.q5_closure_v036 import (
    BRANCH,
    COMPACT_ARENA_PATH,
    DIRECT_SYSTEM_PATH,
    PAPER_PATH,
    POLYNOMIAL_SYSTEM_PATH,
    WITNESS_PATH,
    compile_q5_closure_audit,
    compile_q5_constraint_census,
)

SCHEMA = "final-theory-q5-vacuity-proof-v0.3.6"
VERDICT = "LITERAL_Q5_UNCONSTRAINED"
LITERAL_VERDICT = (
    "CPOBC_D2_LITERAL_BRANCH_VACUOUS_UNCONSTRAINED_GENERATOR"
)
CENSUS_PATH = "results/v0.3.6_q5_constraint_census.json"
PROOF_PATH = "results/v0.3.6_q5_vacuity_proof.json"
CLASSIFICATION_PATH = "results/v0.3.5_d2_classification.json"
EQ112_SOURCE_PATH = "src/universe_lab/final_theory/eq112_reduction_v033.py"
EQ139_SOURCE_PATH = "src/universe_lab/final_theory/cpobc_v031.py"
ADDENDUM_HEADING = "## v0.3.6 addendum - Q5 vacuity correction"
OLD_ADDENDUM_HEADING = "## v0.3.6 addendum - Q5 boundary diagnosis"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _matrix_from_strings(entries: list[list[str]]) -> sp.Matrix:
    return sp.Matrix(
        [[sp.Rational(value) for value in row] for row in entries]
    )


def _exact(value: sp.Expr) -> str:
    return str(sp.factor(sp.cancel(value)))


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [_exact(sp.sympify(matrix[row, column])) for column in range(2)]
        for row in range(2)
    ]


def _zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.cancel(value) == 0 for value in matrix)


def _commutator(
    left: sp.MatrixBase,
    right: sp.MatrixBase,
) -> sp.Matrix:
    return sp.Matrix(left * right - right * left).applyfunc(sp.cancel)


class _CompactArenaEvaluator:
    """Evaluate selected v0.3.5 compact-arena nodes exactly in SymPy."""

    def __init__(
        self,
        nodes: list[list[Any]],
        substitutions: dict[str, sp.Expr],
    ) -> None:
        self.nodes = nodes
        self.substitutions = substitutions
        self.cache: dict[int, sp.Expr] = {}
        self.unresolved_symbol_names: set[str] = set()

    def evaluate(self, index: int) -> sp.Expr:
        existing = self.cache.get(index)
        if existing is not None:
            return existing
        operation, payload = self.nodes[index]
        if operation == 0:
            result: sp.Expr = sp.Rational(payload)
        elif operation == 1:
            if payload not in self.substitutions:
                self.unresolved_symbol_names.add(payload)
            result = self.substitutions.get(payload, sp.Symbol(payload))
        elif operation == 2:
            result = sp.Add(
                *(self.evaluate(int(child)) for child in payload),
                evaluate=True,
            )
        elif operation == 3:
            result = sp.Mul(
                *(self.evaluate(int(child)) for child in payload),
                evaluate=True,
            )
        else:
            raise ValueError(f"unsupported compact-arena operation: {operation}")
        self.cache[index] = result
        return result


def _witness_q_matrices(census: dict[str, Any]) -> dict[int, sp.Matrix]:
    return {
        int(name.split("_", 1)[1]): _matrix_from_strings(entries)
        for name, entries in census["witness_reconfirmation"][
            "Q_matrices"
        ].items()
    }


def _symbolic_q5_substitutions(
    q_matrices: dict[int, sp.Matrix],
) -> tuple[dict[str, sp.Expr], sp.Matrix, tuple[sp.Symbol, ...]]:
    a, b, c, d = sp.symbols("a b c d")
    q5 = sp.Matrix([[a, b], [c, d]])
    substitutions: dict[str, sp.Expr] = {}
    for stage in range(1, 5):
        matrix = q_matrices[stage]
        for row in range(2):
            for column in range(2):
                substitutions[f"q{stage}_{row + 1}{column + 1}"] = (
                    matrix[row, column]
                )
    for row in range(2):
        for column in range(2):
            substitutions[f"q5_{row + 1}{column + 1}"] = q5[row, column]
    return substitutions, q5, (a, b, c, d)


def _compiled_scalar_vacuity(
    root: Path,
    census: dict[str, Any],
) -> dict[str, Any]:
    systems = _load_json(root / POLYNOMIAL_SYSTEM_PATH)
    witness = _load_json(root / WITNESS_PATH)
    literal = systems["systems"][LITERAL_BRANCH]
    equation_index = {
        record["equation_id"]: record for record in literal["equations"]
    }
    with gzip.open(
        root / COMPACT_ARENA_PATH,
        "rt",
        encoding="utf-8",
    ) as handle:
        arena = json.load(handle)
    q_masks: list[int] = []
    for index, node in enumerate(arena["nodes"]):
        operation, node_payload = node
        if operation == 0:
            mask = 0
        elif operation == 1:
            name = str(node_payload)
            if name.startswith("q5_"):
                mask = 1 << 5
            else:
                mask = 0
        else:
            mask = 0
            for child in node_payload:
                child_index = int(child)
                if child_index >= index:
                    raise RuntimeError(
                        "compact arena is not topologically ordered"
                    )
                mask |= q_masks[child_index]
        q_masks.append(mask)
    q5_denominator_records = [
        record
        for record in systems["denominator_factors"]
        if q_masks[
            int(arena["target_indices"][record["factor_id"]])
        ]
        & (1 << 5)
    ]

    q_matrices = _witness_q_matrices(census)
    substitutions, q5, q5_symbols = _symbolic_q5_substitutions(q_matrices)
    evaluator = _CompactArenaEvaluator(arena["nodes"], substitutions)
    records: list[dict[str, Any]] = []
    for census_record in census["Q5_scalar_numerator_equations"]:
        equation_id = census_record["equation_id"]
        frozen_record = equation_index[equation_id]
        expression_id = frozen_record["canonical_expression_id"]
        if expression_id != census_record["canonical_expression_id"]:
            raise RuntimeError(
                f"census/system expression mismatch for {equation_id}"
            )
        expression = sp.cancel(
            evaluator.evaluate(int(arena["target_indices"][expression_id]))
        )
        records.append(
            {
                "equation_id": equation_id,
                "canonical_expression_id": expression_id,
                "provenance": census_record["provenance"],
                "after_Q1_through_Q4_witness_and_symbolic_Q5_substitution": (
                    _exact(expression)
                ),
                "remaining_free_symbols": sorted(
                    str(symbol) for symbol in expression.free_symbols
                ),
                "identically_zero": expression == 0,
            }
        )

    symbolic_commutator = _commutator(q_matrices[1], q5)
    sample_entries = (
        ((-2, 9), (8, -5)),
        ((2, 6), (9, -7)),
        ((-9, 6), (-1, 8)),
    )
    samples: list[dict[str, Any]] = []
    for entries in sample_entries:
        sample = sp.Matrix(entries)
        commutator = _commutator(q_matrices[1], sample)
        samples.append(
            {
                "Q5": _matrix_record(sample),
                "determinant": _exact(sample.det()),
                "invertible": sample.det() != 0,
                "commutator_Q1_Q5": _matrix_record(commutator),
                "noncommutative": not _zero_matrix(commutator),
                "all_twelve_compiled_Q5_equations_pass": all(
                    record["identically_zero"] for record in records
                ),
            }
        )

    total = int(literal["canonical_numerator_equation_count"])
    q5_count = len(records)
    background_count = total - q5_count
    background_exact = witness["canonical_scalar_numerator_check"]
    passed = bool(
        total == 2564
        and q5_count == 12
        and background_count == 2552
        and len(systems["denominator_factors"]) == 191
        and not q5_denominator_records
        and len(census["Q5_relation_ids"][
            "nonzero_relations_constraining_Q5"
        ])
        == 3
        and not evaluator.unresolved_symbol_names
        and all(record["identically_zero"] for record in records)
        and background_exact["count"] == total
        and background_exact["all_zero"]
        and not background_exact["failed_equation_ids"]
        and all(sample["invertible"] for sample in samples)
        and all(sample["noncommutative"] for sample in samples)
    )
    return {
        "frozen_literal_system": {
            "matrix_relation_count": literal["relation_count"],
            "canonical_scalar_numerator_count": total,
            "Q5_dependent_matrix_relation_count": 3,
            "Q5_dependent_canonical_scalar_numerator_count": q5_count,
            "Q5_independent_canonical_scalar_numerator_count": (
                background_count
            ),
            "frozen_denominator_factor_count": len(
                systems["denominator_factors"]
            ),
            "Q5_dependent_frozen_denominator_factor_count": len(
                q5_denominator_records
            ),
        },
        "symbolic_substitution": {
            "Q1_through_Q4": {
                f"Q_{stage}": _matrix_record(q_matrices[stage])
                for stage in range(1, 5)
            },
            "Q5": [["a", "b"], ["c", "d"]],
            "coefficient_domain": "QQ[a,b,c,d]",
            "arena_nodes_evaluated": len(evaluator.cache),
            "unresolved_symbol_names": sorted(
                evaluator.unresolved_symbol_names
            ),
        },
        "twelve_equation_records": records,
        "twelve_equations_identically_zero": all(
            record["identically_zero"] for record in records
        ),
        "remaining_2552_equations_argument": {
            "Q5_dependency": "none, by exact compact-arena dependency census",
            "fixed_base_point_check": {
                "source": WITNESS_PATH,
                "count": background_exact["count"],
                "all_2564_zero_at_frozen_witness": background_exact[
                    "all_zero"
                ],
                "failed_equation_ids": background_exact[
                    "failed_equation_ids"
                ],
                "residuals_sha256": background_exact["residuals_sha256"],
            },
            "conclusion": (
                "The 2,552 Q5-independent equations remain zero when Q5 "
                "varies because their expressions contain no Q5 symbol."
            ),
        },
        "all_2564_equations_zero_for_symbolic_Q5": passed,
        "symbolic_commutator_Q1_Q5": {
            "matrix": _matrix_record(symbolic_commutator),
            "zero_locus": ["c - b = 0", "d - a - b = 0"],
            "centralizer_dimension_in_A4": 2,
            "generic_Q5_noncommutative": True,
        },
        "ambient_localisation_boundary": {
            "polynomial_equation_ideal_in_Q5_coordinates": "zero ideal",
            "Q5_dependent_frozen_denominator_factors": (
                q5_denominator_records
            ),
            "affine_fiber_dimension": 4,
            "representation_domain": "GL(2), det(Q5)=a*d-b*c != 0",
            "invertibility_source": (
                "ambient invertible-generator hypothesis and exact d=2 "
                "chart nonzero conditions, not a frozen numerator equation"
            ),
            "invertibility_is_not_a_new_polynomial_Q5_relation": True,
        },
        "independent_integer_Q5_samples": samples,
        "passed": passed,
    }


def _antichain_transition(
    q_matrices: dict[int, sp.Matrix],
    n: int,
    k: int,
) -> sp.Matrix:
    """Paper Eq. (137), second line, with Q0=I and k>=1."""

    identity = sp.eye(2)
    return sum(
        (
            (-1) ** ell
            * math.comb(k, ell)
            * (identity - q_matrices[k - ell])
            * q_matrices[n]
            * q_matrices[k - ell].inv()
            for ell in range(k + 1)
        ),
        sp.zeros(2),
    ).applyfunc(sp.cancel)


def _paper_relation_checks(
    census: dict[str, Any],
) -> dict[str, Any]:
    q_matrices = _witness_q_matrices(census)
    q_matrices[0] = sp.eye(2)
    _, q5, _ = _symbolic_q5_substitutions(q_matrices)
    q_matrices[5] = q5

    eq120_records: list[dict[str, Any]] = []
    for n, m in itertools.combinations(range(1, 6), 2):
        for k in range(1, min(n, m)):
            residual = (
                q_matrices[n]
                * q_matrices[k].inv()
                * q_matrices[m]
                - q_matrices[m]
                * q_matrices[k].inv()
                * q_matrices[n]
            ).applyfunc(sp.cancel)
            eq120_records.append(
                {
                    "indices": {"n": n, "k": k, "m": m},
                    "involves_Q5": 5 in {n, k, m},
                    "residual": _matrix_record(residual),
                    "identically_zero": _zero_matrix(residual),
                }
            )

    eq130_residual = _commutator(
        q_matrices[1] * q_matrices[2].inv(),
        q_matrices[1].inv() * q_matrices[2],
    )
    antichain = {
        k: _antichain_transition(q_matrices, 4, k)
        for k in (1, 2, 3)
    }
    eq139_records: list[dict[str, Any]] = []
    for m, k in ((1, 2), (1, 3), (2, 3)):
        a_m = antichain[m]
        a_k = antichain[k]
        lhs = (
            a_m
            * a_k
            * q_matrices[5]
            * a_k.inv()
            * q_matrices[4].inv()
            * a_k
        )
        rhs = (
            a_k
            * a_m
            * q_matrices[5]
            * a_m.inv()
            * q_matrices[4].inv()
            * a_m
        )
        residual = sp.Matrix(lhs - rhs).applyfunc(sp.cancel)
        eq139_records.append(
            {
                "indices": {"n": 4, "m": m, "k": k},
                "residual": _matrix_record(residual),
                "identically_zero": _zero_matrix(residual),
            }
        )

    passed = bool(
        len(eq120_records) == 10
        and all(record["identically_zero"] for record in eq120_records)
        and _zero_matrix(eq130_residual)
        and all(record["identically_zero"] for record in eq139_records)
    )
    return {
        "paper_source": {
            "version": "arXiv:2603.25503v1",
            "Eq120": "PDF page 28",
            "Eq130": "PDF page 29",
            "Eq135_Eq137_Eq139": "PDF page 30",
            "Eq139_n2_expansion_Eq145": "PDF page 31",
        },
        "Eq120": {
            "instance_count": len(eq120_records),
            "Q5_instance_count": sum(
                record["involves_Q5"] for record in eq120_records
            ),
            "records": eq120_records,
            "all_identically_zero": all(
                record["identically_zero"] for record in eq120_records
            ),
        },
        "Eq130": {
            "residual": _matrix_record(eq130_residual),
            "identically_zero": _zero_matrix(eq130_residual),
        },
        "Eq137_A4_matrices": {
            f"A4^({k})": _matrix_record(matrix)
            for k, matrix in antichain.items()
        },
        "Eq139": {
            "instance_count": len(eq139_records),
            "records": eq139_records,
            "all_identically_zero": all(
                record["identically_zero"] for record in eq139_records
            ),
            "structural_reason": (
                "When Q1 through Q4 commute, A4^(1), A4^(2), A4^(3), "
                "and Q4 are rational expressions in the same commuting "
                "matrices. Thus Ak^-1*Q4^-1*Ak=Q4^-1 and Am*Ak=Ak*Am, "
                "so both sides agree for every Q5."
            ),
        },
        "passed": passed,
    }


def _msr_identity_audit() -> dict[str, Any]:
    sample_q = {
        0: sp.eye(2),
        1: sp.Matrix([[2, 1], [1, 1]]),
        2: sp.Matrix([[1, 2], [3, 5]]),
        3: sp.Matrix([[2, -1], [4, 3]]),
        4: sp.Matrix([[3, 2], [-1, 1]]),
        5: sp.Matrix([[1, 4], [2, 3]]),
    }
    msr_records: list[dict[str, Any]] = []
    for n in range(1, 6):
        residual = (
            sample_q[n]
            + sum(
                (
                    math.comb(n, k)
                    * _antichain_transition(sample_q, n, k)
                    for k in range(1, n + 1)
                ),
                sp.zeros(2),
            )
            - sp.eye(2)
        ).applyfunc(sp.cancel)
        msr_records.append(
            {
                "n": n,
                "residual": _matrix_record(residual),
                "identically_zero": _zero_matrix(residual),
            }
        )

    cpobc_failures: list[dict[str, Any]] = []
    for n, m in itertools.combinations(range(1, 6), 2):
        for k in range(1, min(n, m)):
            residual = (
                sample_q[n] * sample_q[k].inv() * sample_q[m]
                - sample_q[m] * sample_q[k].inv() * sample_q[n]
            ).applyfunc(sp.cancel)
            if not _zero_matrix(residual):
                cpobc_failures.append(
                    {
                        "indices": {"n": n, "k": k, "m": m},
                        "residual": _matrix_record(residual),
                    }
                )

    coefficient_checks: list[dict[str, Any]] = []
    for n in range(1, 6):
        for j in range(1, n + 1):
            coefficient = sum(
                math.comb(n, k)
                * (-1) ** (k - j)
                * math.comb(k, j)
                for k in range(j, n + 1)
            )
            coefficient_checks.append(
                {
                    "n": n,
                    "j": j,
                    "coefficient": coefficient,
                    "expected": 1 if j == n else 0,
                }
            )
    passed = bool(
        all(record["identically_zero"] for record in msr_records)
        and len(cpobc_failures) == 10
        and all(
            record["coefficient"] == record["expected"]
            for record in coefficient_checks
        )
    )
    return {
        "interpretation": (
            "After the antichain transitions are reconstructed with paper "
            "Eqs. (135)/(137), their multiplicity-weighted MSR residual is "
            "a binomial identity. It is not an independent CPOBC test."
        ),
        "formal_cancellation": (
            "sum_{k=j}^n C(n,k)(-1)^(k-j)C(k,j) "
            "= C(n,j)(1-1)^(n-j) = delta_{j,n}"
        ),
        "coefficient_checks_n1_through_n5": coefficient_checks,
        "deliberately_CPOBC_invalid_invertible_sample": {
            "Q_matrices": {
                f"Q_{stage}": _matrix_record(sample_q[stage])
                for stage in range(1, 6)
            },
            "Eq120_failure_count": len(cpobc_failures),
            "first_Eq120_failure": cpobc_failures[0],
        },
        "MSR_residuals_n1_through_n5": msr_records,
        "all_MSR_residuals_zero": all(
            record["identically_zero"] for record in msr_records
        ),
        "passed": passed,
    }


def _scalar_chain_operator_identity(
    root: Path,
    census: dict[str, Any],
) -> dict[str, Any]:
    direct = _load_json(root / DIRECT_SYSTEM_PATH)
    classification = _load_json(root / CLASSIFICATION_PATH)
    relation_ids = set(
        census["Q5_relation_ids"]["nonzero_relations_constraining_Q5"]
    )
    relations = [
        record
        for record in direct["relations"][LITERAL_BRANCH]
        if record["relation_id"] in relation_ids
    ]
    definitions = {
        record["node_id"]: record for record in direct["dependency_nodes"]
    }
    x, lambda_2, lambda_3, lambda_4 = sp.symbols(
        "x lambda_2 lambda_3 lambda_4",
        nonzero=True,
    )
    q_projection = {
        "Q_1": x,
        "Q_2": lambda_2 * x,
        "Q_3": lambda_3 * x,
        "Q_4": lambda_4 * x,
    }
    cache: dict[str, sp.Expr] = dict(q_projection)
    visiting: set[str] = set()

    def product(word: list[str]) -> sp.Expr:
        result = sp.Integer(1)
        for token in word:
            result = sp.cancel(result * node(token))
        return result

    def node(node_id: str) -> sp.Expr:
        existing = cache.get(node_id)
        if existing is not None:
            return existing
        if node_id in visiting:
            raise RuntimeError(f"operator DAG cycle at {node_id}")
        visiting.add(node_id)
        definition = definitions[node_id]
        kind = definition["kind"]
        if kind == "Q_GENERATOR":
            result = q_projection[node_id]
        elif kind == "Q_GENERATOR_INVERSE":
            result = 1 / q_projection[node_id.removesuffix("^-1")]
        elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
            result = sum(
                (
                    sp.Integer(term["coefficient"])
                    * product(term["word_nodes"])
                    for term in definition["terms"]
                ),
                sp.Integer(0),
            )
        elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            result = 1 / node(definition["inverse_of_node"])
        elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
            result = product(definition["ordered_word"])
        else:
            raise ValueError(f"unsupported dependency kind: {kind}")
        visiting.remove(node_id)
        result = sp.factor(sp.cancel(result))
        cache[node_id] = result
        return result

    records: list[dict[str, Any]] = []
    for relation in relations:
        if (
            relation["lhs_word"][-1] != "Q_5"
            or relation["rhs_word"][0] != "Q_5"
            or relation["lhs_word"][:-1] != relation["rhs_word"][1:]
        ):
            raise RuntimeError(
                f"unexpected path-commutator shape: {relation['relation_id']}"
            )
        commuting_word = relation["lhs_word"][:-1]
        projection = sp.factor(product(commuting_word))
        records.append(
            {
                "relation_id": relation["relation_id"],
                "source_stage": relation["source_stage"],
                "commuting_word": commuting_word,
                "scalar_chain_projection": _exact(projection),
                "projection_is_identity": projection == 1,
                "resulting_relation": "[I,Q5]=0",
            }
        )

    pivot_r5_charts = [
        chart
        for chart in stratum_charts(LITERAL_BRANCH)
        if chart.stratum == S1 and chart.pivot == "R_5"
    ]
    chart_records = [
        {
            "chart": chart.chart_id,
            "zero_conditions": [
                str(condition) for condition in chart.zero_conditions
            ],
        }
        for chart in pivot_r5_charts
    ]
    expected_scalar_equalities = {
        "-r2m + r2p",
        "-r3m + r3p",
        "-r4m + r4p",
    }
    charts_have_scalar_chain = all(
        expected_scalar_equalities.issubset(
            {str(condition) for condition in chart.zero_conditions}
        )
        for chart in pivot_r5_charts
    )
    surviving = classification["noncommutative_charts"]
    surviving_pivot_r5 = [
        chart_id for chart_id in surviving if ":S1_PIVOT_R5:" in chart_id
    ]
    passed = bool(
        len(records) == 3
        and all(record["projection_is_identity"] for record in records)
        and len(pivot_r5_charts) == 4
        and charts_have_scalar_chain
        and len(surviving_pivot_r5) == 3
    )
    return {
        "hypotheses": [
            "Q1 is invertible",
            "Q2=lambda_2*Q1, Q3=lambda_3*Q1, Q4=lambda_4*Q1",
            "lambda_2, lambda_3, lambda_4 are nonzero",
            "every frozen inverse site used by the three words is defined",
        ],
        "projection_domain": "QQ(x,lambda_2,lambda_3,lambda_4)",
        "relation_records": records,
        "dependency_nodes_evaluated": len(cache),
        "S1_pivot_R5_chart_evidence": {
            "chart_count": len(pivot_r5_charts),
            "charts": chart_records,
            "all_impose_R2_R3_R4_scalar": charts_have_scalar_chain,
            "v0.3.5_surviving_pivot_R5_chart_ids": surviving_pivot_r5,
        },
        "conditional_fiber_theorem": (
            "Over every frozen base solution with Q2=lambda_2 Q1, "
            "Q3=lambda_3 Q1, and Q4=lambda_4 Q1, the only three nonidentity "
            "Q5-dependent operator words reduce to [I,Q5]=0. Therefore the "
            "literal solution set has the full GL(2) Q5 fiber over that base "
            "locus. This does not assert that every scalar-chain base point "
            "satisfies the Q1-through-Q4 equations."
        ),
        "fiber": {
            "polynomial_coordinates": 4,
            "localised_domain": "GL(2)",
            "generic_noncommutativity_source": (
                "the complement of the 2-dimensional centralizer of a "
                "nonscalar Q1"
            ),
        },
        "passed": passed,
    }


def _eq139_call_sites(root: Path) -> list[dict[str, Any]]:
    source = (root / EQ139_SOURCE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    records: list[dict[str, Any]] = []
    for function in (
        node for node in tree.body if isinstance(node, ast.FunctionDef)
    ):
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_eq139"
            ):
                records.append(
                    {
                        "caller": function.name,
                        "line": node.lineno,
                        "arguments": [ast.unparse(argument) for argument in node.args],
                    }
                )
    return records


def compile_eq113_eq139_audit(root: Path) -> dict[str, Any]:
    """Separate the source equations and identify their project coverage."""

    eq112 = compile_eq112_reduction_n4()
    branches = eq112["path_consistency_branches"]
    derived = branches["EQ113_QN_BRANCH"]
    literal = branches["EQ113_QN_PLUS_1_BRANCH"]
    direct = _load_json(root / DIRECT_SYSTEM_PATH)
    literal_family_counts = Counter(
        record["family"] for record in direct["relations"][LITERAL_BRANCH]
    )
    call_sites = _eq139_call_sites(root)
    branch_summary = {
        "EQ113_QN_BRANCH": {
            "record_count": len(derived),
            "Q_token_counts": dict(
                sorted(Counter(record["Q_token"] for record in derived).items())
            ),
            "basis_counts": dict(
                sorted(Counter(record["basis"] for record in derived).items())
            ),
            "all_have_commutator_word_shape": all(
                record["lhs_word"][-1] == record["Q_token"]
                and record["rhs_word"][0] == record["Q_token"]
                and record["lhs_word"][:-1] == record["rhs_word"][1:]
                for record in derived
            ),
        },
        "EQ113_QN_PLUS_1_BRANCH": {
            "record_count": len(literal),
            "Q_token_counts": dict(
                sorted(Counter(record["Q_token"] for record in literal).items())
            ),
            "basis_counts": dict(
                sorted(Counter(record["basis"] for record in literal).items())
            ),
            "all_have_commutator_word_shape": all(
                record["lhs_word"][-1] == record["Q_token"]
                and record["rhs_word"][0] == record["Q_token"]
                and record["lhs_word"][:-1] == record["rhs_word"][1:]
                for record in literal
            ),
        },
    }
    passed = bool(
        len(derived) == len(literal) == 25
        and branch_summary["EQ113_QN_BRANCH"][
            "all_have_commutator_word_shape"
        ]
        and branch_summary["EQ113_QN_PLUS_1_BRANCH"][
            "all_have_commutator_word_shape"
        ]
        and literal_family_counts["EQ112_PATH_CONSISTENCY"] == 25
        and len(call_sites) == 1
        and call_sites[0]["caller"] == "_scaled_heisenberg_ansatz"
        and call_sites[0]["arguments"] == ["a1_2", "a2_2", "q3", "q2"]
        and "EQ139" not in literal_family_counts
    )
    payload: dict[str, Any] = {
        "schema_version": "final-theory-eq113-eq139-separation-v0.3.6",
        "paper_source": {
            "path": PAPER_PATH,
            "sha256": _sha256(root / PAPER_PATH),
            "version": "arXiv:2603.25503v1",
            "visual_verification": {
                "PDF_page_27": (
                    "Eq.(112) ends in S_alpha Q_n S_alpha^-1; printed "
                    "Eq.(113) is [S_alpha^-1 S_beta,Q_(n+1)]=0."
                ),
                "PDF_page_30": (
                    "Eq.(139) is a separate antichain-transition relation "
                    "and contains Q_(n+1)."
                ),
                "PDF_page_31": (
                    "The paper substitutes n=2 into Eq.(139); Eq.(145) "
                    "explicitly contains Q_3."
                ),
            },
        },
        "independent_derivation_from_Eq112": {
            "premise": (
                "G_n^(0)=S_alpha Q_n S_alpha^-1 is independent of alpha"
            ),
            "comparison": (
                "S_alpha Q_n S_alpha^-1="
                "S_beta Q_n S_beta^-1"
            ),
            "conclusion": "[S_alpha^-1 S_beta,Q_n]=0",
            "Q_n_plus_1_derivation_step_present": False,
            "interpretation": (
                "The printed Q_(n+1) in Eq.(113) is strongly suggestive of "
                "a typo, but this does not establish author intent."
            ),
        },
        "project_EQ112_PATH_CONSISTENCY_audit": {
            "source": EQ112_SOURCE_PATH,
            "source_sha256": _sha256(root / EQ112_SOURCE_PATH),
            "branch_summary": branch_summary,
            "direct_literal_family_count": literal_family_counts[
                "EQ112_PATH_CONSISTENCY"
            ],
            "implements": (
                "two explicit readings of Eq.(113), both as "
                "[S_alpha^-1 S_beta,Q]=0"
            ),
            "implements_Eq139": False,
            "Eq113_Eq139_conflation_detected": False,
        },
        "project_Eq139_audit": {
            "source": EQ139_SOURCE_PATH,
            "source_sha256": _sha256(root / EQ139_SOURCE_PATH),
            "explicit_helper_call_sites": call_sites,
            "n2_status": (
                "one exact Eq.(145)-from-Eq.(139) check inside the separate "
                "d=3 scaled-Heisenberg ansatz"
            ),
            "n3_status": "NO_SEPARATELY_MATERIALISED_GENERAL_RELATION",
            "n4_status": "NO_SEPARATELY_MATERIALISED_GENERAL_RELATION",
            "frozen_d2_named_EQ139_relation_count": 0,
            "claim_boundary": (
                "This audit establishes the absence of separately named "
                "general n=2,3,4 Eq.(139) relations. It does not decide "
                "whether every lower-stage consequence is already redundant "
                "in the full CPOBC/GC/MSR ideal. The n=4 Q5 form is not "
                "present through those core families, whose transitive Q5 "
                "dependency count is zero."
            ),
        },
        "source_classification": {
            "printed_Eq113_typo_suggested": True,
            "author_intent_confirmed": False,
            "classification": "SOURCE_AMBIGUITY",
            "both_branches_retained": True,
        },
        "unresolved_components": [
            (
                "Materialise general Eq.(139) at n=2,3,4 as an explicit "
                "redundancy/coverage audit, especially the n=4 Q5 relation."
            ),
            (
                "Resolve the printed Eq.(113) index by author clarification "
                "or an authoritative corrected source."
            ),
        ],
        "passed": passed,
        "verdict": (
            "EQ113_EQ139_SEPARATED_SOURCE_AMBIGUITY_RETAINED"
            if passed
            else "EQ113_EQ139_SEPARATION_AUDIT_FAILED"
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "paper_source": payload["paper_source"],
            "derivation": payload["independent_derivation_from_Eq112"],
            "path_audit": payload["project_EQ112_PATH_CONSISTENCY_audit"],
            "eq139_audit": payload["project_Eq139_audit"],
            "classification": payload["source_classification"],
            "verdict": payload["verdict"],
        }
    )
    return payload


def compile_q5_vacuity_proof(
    root: Path,
    *,
    census: dict[str, Any] | None = None,
    eq_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile the exact vacuity proof and revised literal-branch verdict."""

    exact_census = census or compile_q5_constraint_census(root)
    if not exact_census["passed"]:
        raise RuntimeError("Q5 constraint census did not pass")
    closure_audit = compile_q5_closure_audit(root, exact_census)
    compiled = _compiled_scalar_vacuity(root, exact_census)
    paper_checks = _paper_relation_checks(exact_census)
    msr = _msr_identity_audit()
    scalar_chain = _scalar_chain_operator_identity(root, exact_census)
    separation = eq_audit or compile_eq113_eq139_audit(root)
    passed = bool(
        compiled["passed"]
        and paper_checks["passed"]
        and msr["passed"]
        and scalar_chain["passed"]
        and separation["passed"]
        and not closure_audit[
            "requested_generator_symmetric_closure_established"
        ]
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "branch": BRANCH,
        "source_index_branch": LITERAL_BRANCH,
        "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
        "dimension": 2,
        "finite_scope": "frozen source stages n<=4",
        "source_artifacts": {
            DIRECT_SYSTEM_PATH: _sha256(root / DIRECT_SYSTEM_PATH),
            COMPACT_ARENA_PATH: _sha256(root / COMPACT_ARENA_PATH),
            POLYNOMIAL_SYSTEM_PATH: _sha256(
                root / POLYNOMIAL_SYSTEM_PATH
            ),
            WITNESS_PATH: _sha256(root / WITNESS_PATH),
            CLASSIFICATION_PATH: _sha256(root / CLASSIFICATION_PATH),
            PAPER_PATH: _sha256(root / PAPER_PATH),
        },
        "phase_0_independent_rechecks": {
            "paper_relations": paper_checks,
            "antichain_MSR_identity": msr,
            "closure_step_A": {
                "status": "NOT_RUN_INVALID_AND_UNNECESSARY",
                "invalid_generator_shift_rejected": not closure_audit[
                    "requested_generator_symmetric_closure_established"
                ],
                "reason": (
                    "The proposed shift is not a proved necessary subset, "
                    "and the compiled Q5 equations can be decided directly."
                ),
            },
        },
        "phase_1_compiled_system_vacuity": compiled,
        "phase_1_scalar_chain_structure": scalar_chain,
        "phase_2_verdict_reconstruction": {
            "v0.3.5_literal_verdict": (
                "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
            ),
            "v0.3.6_literal_verdict": LITERAL_VERDICT,
            "reason": (
                "Noncommutativity comes generically from a four-coordinate "
                "Q5 fiber on which the frozen equation ideal is zero; it was "
                "not generated by a constraining relation."
            ),
            "substantive_finite_result": (
                "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4"
            ),
            "paper_overturned": False,
        },
        "phase_3_eq113_eq139_separation": {
            "certificate_verdict": separation["verdict"],
            "semantic_digest_sha256": separation[
                "semantic_digest_sha256"
            ],
            "source_ambiguity_retained": True,
            "general_Eq139_n2_n3_n4_separately_compiled": False,
        },
        "execution": {
            "exact_symbolic_engine": f"SymPy {sp.__version__}",
            "Sage_runs": 0,
            "Singular_runs": 0,
            "finite_field_scout_runs": 0,
            "QQ_Groebner_runs": 0,
            "stage5_compiler_runs": 0,
            "budget_file_required": False,
            "budget_file_created": False,
            "genuine_stage5_construction_attempted": False,
        },
        "exact_numeric_distinction": (
            "EXACT_SYMBOLIC_CHARACTERISTIC_ZERO_IDENTITY; no modular "
            "evidence is used as proof"
        ),
        "claim_boundary": (
            "Q5 is unconstrained by polynomial equalities after the frozen "
            "Q1-through-Q4 witness substitution and, conditionally, over the "
            "scalar-chain base locus. The ambient representation still "
            "requires det(Q5) != 0. This finite diagnosis does not solve the "
            "weak profile or the infinite-QSG problem."
        ),
        "global_scientific_verdict": "FINAL_THEORY_OPEN",
        "unresolved_components": separation["unresolved_components"],
        "passed": passed,
        "verdict": VERDICT if passed else "LITERAL_Q5_VACUITY_PROOF_FAILED",
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "compiled": compiled,
            "paper_checks": paper_checks,
            "msr": msr,
            "scalar_chain": scalar_chain,
            "separation_digest": separation["semantic_digest_sha256"],
            "execution": payload["execution"],
            "verdict": payload["verdict"],
        }
    )
    return payload


def _replace_v035_addendum(path: Path, body: str) -> None:
    current = path.read_text(encoding="utf-8")
    cut_positions = [
        position
        for heading in (ADDENDUM_HEADING, OLD_ADDENDUM_HEADING)
        if (position := current.find(heading)) >= 0
    ]
    base = current[: min(cut_positions)].rstrip() if cut_positions else current.rstrip()
    path.write_text(
        f"{base}\n\n{ADDENDUM_HEADING}\n\n{body.rstrip()}\n",
        encoding="utf-8",
    )


def write_v036_reports(
    root: Path,
    proof: dict[str, Any],
    eq_audit: dict[str, Any],
) -> None:
    compiled = proof["phase_1_compiled_system_vacuity"]
    samples = compiled["independent_integer_Q5_samples"]
    sample_lines = "\n".join(
        f"- `Q5={record['Q5']}`, det={record['determinant']}, "
        f"`[Q1,Q5]={record['commutator_Q1_Q5']}`"
        for record in samples
    )
    _write_text(
        root / "reports/v0.3.6_q5_vacuity.md",
        f"""# Final-Theory Bench v0.3.6 - exact Q5 vacuity proof

The apparent literal-branch witness is not a constrained noncommutative
representation. After fixing the v0.3.5 values of Q1 through Q4 and leaving
`Q5=[[a,b],[c,d]]`, all twelve frozen canonical scalar numerators that contain
Q5 reduce identically to zero in `QQ[a,b,c,d]`.

The dependency census is exhaustive: the other 2,552 canonical numerators have
no Q5 symbol. They were already exactly zero at the same Q1-through-Q4 base
point, so all 2,564 equations remain zero for every Q5. The polynomial ideal in
the four Q5 coordinates is the zero ideal. None of the 191 frozen denominator
factors depends on Q5 either. The representation domain still retains the
ambient invertibility condition `det(Q5) != 0` through the d=2 chart cover, so
the actual fiber is the four-dimensional open set `GL(2)`.

The three nonidentity relation records found by the census do not become
constraints after base specialisation. Each of their pre-Q5 operator words
reduces to `I`, leaving `[I,Q5]=0`. More generally, this holds conditionally
over every frozen base solution of the form
`Q2=lambda2*Q1`, `Q3=lambda3*Q1`, `Q4=lambda4*Q1`. This is exactly the scalar
chain imposed before the R5 pivot in the S1 charts.

For the frozen `Q1=[[1,1],[1,2]]`,

`[Q1,Q5]=[[c-b,d-a-b],[a+c-d,b-c]]`.

Its commuting locus has dimension two (`c=b`, `d=a+b`), so a generic point of
the four-dimensional Q5 fiber is noncommutative. Three independent invertible
integer checks are:

{sample_lines}

Paper Eqs. (120) and (130), and all three Eq. (139) instances at `n=4`,
also vanish symbolically for the arbitrary Q5. The antichain MSR reconstructed
through Eqs. (135)/(137) is a binomial identity, including on a deliberately
CPOBC-invalid matrix sample; it supplies no independent Q5 constraint.

No Sage or Singular run was needed or performed. No budget file was created.

Verdict: `{proof['verdict']}`.
Literal classification: `{LITERAL_VERDICT}`.
Global verdict: `FINAL_THEORY_OPEN`.
""",
    )
    _write_text(
        root / "reports/v0.3.6_eq113_eq139_separation.md",
        f"""# v0.3.6 audit - separating Eq. (113) from Eq. (139)

The PDF source contains two different relations.

- On PDF page 27, Eq. (112) is
  `G_n^(0)=S_alpha Q_n S_alpha^-1`. Comparing two paths gives
  `[S_alpha^-1 S_beta,Q_n]=0` directly. The printed Eq. (113) instead displays
  `Q_(n+1)`; no intervening step changes the index.
- On PDF page 30, Eq. (139) is a separate antichain-transition relation and
  genuinely contains `Q_(n+1)`. On PDF page 31 the paper substitutes `n=2`,
  and Eq. (145) explicitly contains `Q_3`.

The project has not confused the two formulas inside the 25
`EQ112_PATH_CONSISTENCY` records. Those records are Eq. (113)-shaped
commutators. It deliberately compiles 25 `Q_n` records and 25 literal
`Q_(n+1)` records as separate source-index branches.

Eq. (139) is not separately materialised in the frozen general-d=2 relation
inventory. The only explicit `_eq139` call is the n=2 Eq. (145) check inside
the separate d=3 scaled-Heisenberg ansatz. General named n=3 and n=4 records
are absent. This is retained as a coverage gap, although the v0.3.5 scalar-chain
witness passes all n=4 Eq. (139) instances symbolically for arbitrary Q5.

The algebra strongly suggests that the `n+1` in printed Eq. (113) is a typo,
but author intent is not established. Classification remains
`SOURCE_AMBIGUITY`, and both branches remain preserved.

Audit verdict: `{eq_audit['verdict']}`.
""",
    )
    _write_text(
        root / "reports/v0.3.6_scientific_verdict.md",
        f"""# Final-Theory Bench v0.3.6 - scientific verdict

The v0.3.5 literal-branch `FOUND` classification is superseded by
`{LITERAL_VERDICT}`.

The exact compiled-system proof is decisive. Of 2,564 canonical scalar
numerators, twelve contain Q5. With Q1 through Q4 fixed to the witness base
point and Q5 left as four symbolic coordinates, all twelve are the zero
polynomial. The other 2,552 do not depend on Q5. Thus the noncommutativity was
not generated by the frozen relations: it is generic motion in a full
four-dimensional Q5 fiber, restricted only by ambient invertibility.

This does not overturn the paper. The substantive finite result remains the
derived-branch `CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4`, which classifies
the frozen general-d=2 problem under the strong operator profile and n<=4
scope, beyond the paper's Pauli-proportional test.

The rejected generator-shift closure, genuine stage-5 construction, Sage,
Singular, and a v0.3.6 budget file are all unnecessary for this diagnosis and
were not used. The Eq. (113) source-index ambiguity remains open, and general
Eq. (139) n=2,3,4 relations are not separately materialised in the frozen d=2
inventory.

v0.3.6 proof verdict: `{proof['verdict']}`.
Global verdict: `FINAL_THEORY_OPEN`.
""",
    )
    _write_text(
        root / "reports/v0.3.6_remaining_gaps.md",
        """# Final-Theory Bench v0.3.6 - remaining gaps

The literal Q5 witness no longer requires a stage-5 closure experiment: its
vacuity is proved directly in the frozen compiled system. The remaining gaps
are different in character:

1. Resolve the printed Eq. (113) `Q_n` versus `Q_(n+1)` author intent. The
   internal derivation supports `Q_n`, but `SOURCE_AMBIGUITY` remains.
2. Materialise general Eq. (139) relations at n=2,3,4 as an explicit coverage
   or redundancy audit. The current named implementation has only the n=2
   Eq. (145) check in a separate d=3 ansatz.
3. Repeat the classification under the weak occurrence-dependent operator
   profile.
4. Prove or refute a restriction theorem from arbitrary finite or infinite
   QSG representations to the n<=4 compiler.
5. Describe the general S3 solution locus; v0.3.5 only excludes S3
   noncommutativity.

None of these gaps changes the exact v0.3.6 diagnosis of the frozen literal Q5
fiber. The global programme remains `FINAL_THEORY_OPEN`.
""",
    )
    _replace_v035_addendum(
        root / "reports/v0.3.5_scientific_verdict.md",
        f"""The literal-branch existence wording is corrected by v0.3.6.
After fixing the v0.3.5 Q1-through-Q4 base point and leaving Q5 as a symbolic
2x2 matrix, all twelve canonical scalar numerators with Q5 dependency vanish
identically. The remaining 2,552 equations contain no Q5. The literal solution
therefore has a full four-coordinate Q5 fiber (with the ambient requirement
`det(Q5) != 0`), and generic points are noncommutative simply because the
centralizer of the nonscalar Q1 has dimension two.

The frozen v0.3.5 numerical certificates and their hashes are unchanged, but
the scientific interpretation `CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND`
is superseded by `{LITERAL_VERDICT}`. The substantive finite result remains
the derived-branch `CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4`. This correction
does not overturn the paper and leaves `FINAL_THEORY_OPEN` unchanged.""",
    )
    _replace_v035_addendum(
        root / "reports/v0.3.5_remaining_gaps.md",
        f"""The former request for a genuine stage-5 Q5 closure is no longer a
gap for interpreting the v0.3.5 literal witness. v0.3.6 proves directly in the
frozen 1,001-relation / 2,564-numerator system that the twelve Q5-dependent
numerators vanish identically on the witness base point. The corrected literal
classification is `{LITERAL_VERDICT}`.

The source ambiguity in printed Eq. (113) remains. Eq. (139) is a separate
relation that genuinely contains `Q_(n+1)`; general n=2,3,4 instances are not
separately materialised in the frozen d=2 inventory and should be added as a
coverage audit. The weak profile, infinite-QSG restriction problem, and general
S3 locus also remain open. `FINAL_THEORY_OPEN` is unchanged.""",
    )


def write_v036_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    census = compile_q5_constraint_census(root)
    if not census["passed"]:
        raise RuntimeError("Q5 constraint census failed")
    eq_audit = compile_eq113_eq139_audit(root)
    proof = compile_q5_vacuity_proof(
        root,
        census=census,
        eq_audit=eq_audit,
    )
    if not proof["passed"]:
        raise RuntimeError("Q5 vacuity proof failed")
    _write_json(root / CENSUS_PATH, census)
    _write_json(root / PROOF_PATH, proof)
    write_v036_reports(root, proof, eq_audit)
    return {
        "census": census,
        "proof": proof,
        "eq_audit": eq_audit,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    arguments = parser.parse_args(argv)
    payloads = write_v036_artifacts(arguments.root.resolve())
    print(
        json.dumps(
            {
                "census": payloads["census"]["verdict"],
                "vacuity": payloads["proof"]["verdict"],
                "literal_classification": LITERAL_VERDICT,
                "eq113_eq139": payloads["eq_audit"]["verdict"],
                "Sage_runs": payloads["proof"]["execution"]["Sage_runs"],
                "Singular_runs": payloads["proof"]["execution"][
                    "Singular_runs"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
