"""Branch-separated numerator ideals and localisation data for v0.3.4."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from universe_lab.final_theory.cpobc_q_presentation_v033 import (
    compile_q_presentation_n4,
)
from universe_lab.final_theory.cpobc_v031 import compile_cpobc_relations_v031
from universe_lab.final_theory.d2_rational_dag_v034 import (
    BRANCH,
    SOURCE_COMMIT,
    D2RationalModel,
    RationalMatrix,
    build_d2_rational_model,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    SOURCE_VERDICT,
    stable_hash,
)

DERIVED_BRANCH = "DERIVED_APPENDIX_QN_BRANCH"
LITERAL_BRANCH = "LITERAL_PRINTED_QN_PLUS_1_BRANCH"
V033_DERIVED_BRANCH = "EQ113_QN_BRANCH"
V033_LITERAL_BRANCH = "EQ113_QN_PLUS_1_BRANCH"
SATURATION_METHOD = "SEQUENTIAL_RABINOWITSCH_FACTORS"


@dataclass(frozen=True)
class RationalRelation:
    relation_id: str
    family: str
    source_stage: int
    source_index_branch: str
    matrix: RationalMatrix
    provenance: dict[str, Any]


def _stage_from_causet_id(causet_id: str) -> int:
    prefix = causet_id.split("-", 1)[0]
    if not prefix.startswith("p"):
        raise ValueError(f"unexpected causet id: {causet_id}")
    return int(prefix[1:])


def _matrix_for_node(model: D2RationalModel, node_id: str) -> RationalMatrix:
    if node_id in model.matrices:
        return model.matrices[node_id]
    if node_id in model.q_matrices:
        return model.q_matrices[node_id]
    raise KeyError(f"rational DAG node not found: {node_id}")


def _matrix_from_expression(
    model: D2RationalModel,
    expression: list[dict[str, Any]],
    *,
    provenance: str,
) -> RationalMatrix:
    result = model.zero_matrix(f"{provenance}:ZERO")
    for term_index, term in enumerate(expression):
        word = model.product(
            (
                _matrix_for_node(model, node_id)
                for node_id in term["word"]
            ),
            provenance=f"{provenance}:TERM:{term_index}:WORD",
        )
        result = model.add(
            result,
            model.scale(
                int(term["coefficient"]),
                word,
                provenance=f"{provenance}:TERM:{term_index}:SCALE",
            ),
            provenance=f"{provenance}:TERM:{term_index}:ADD",
        )
    return result


def _matrix_from_word_equality(
    model: D2RationalModel,
    lhs_word: list[str],
    rhs_word: list[str],
    *,
    provenance: str,
) -> RationalMatrix:
    def inverse_token(token: str) -> str:
        if token.startswith("BDEF:"):
            return token.replace("BDEF:", "BINV:", 1)
        if token.startswith("BINV:"):
            return token.replace("BINV:", "BDEF:", 1)
        if token.startswith("G:"):
            return token.removesuffix(":INV") if token.endswith(":INV") else f"{token}:INV"
        if token.startswith("Q_"):
            return token.removesuffix("^-1") if token.endswith("^-1") else f"{token}^-1"
        raise ValueError(f"unknown invertible word token: {token}")

    def free_reduce(word: list[str]) -> list[str]:
        reduced: list[str] = []
        for token in word:
            if reduced and reduced[-1] == inverse_token(token):
                reduced.pop()
            else:
                reduced.append(token)
        return reduced

    lhs_reduced = free_reduce(lhs_word)
    rhs_reduced = free_reduce(rhs_word)
    lhs = model.product(
        (_matrix_for_node(model, node_id) for node_id in lhs_reduced),
        provenance=f"{provenance}:LHS",
    )
    rhs = model.product(
        (_matrix_for_node(model, node_id) for node_id in rhs_reduced),
        provenance=f"{provenance}:RHS",
    )
    return model.subtract(lhs, rhs, provenance=f"{provenance}:RESIDUAL")


def _cpobc_stage_index() -> dict[tuple[str, str], int]:
    compiled = compile_cpobc_relations_v031()
    result: dict[tuple[str, str], int] = {}
    for relation in compiled["relations"]:
        source_stage = max(
            int(relation["stage"]["n"]),
            int(relation["stage"]["m"]),
        )
        for equation in relation["denominator_cleared_form"][
            "noncommutative_polynomial_equations"
        ]:
            result[(relation["relation_id"], equation["equation_id"])] = source_stage
    return result


def build_localised_relations(
    model: D2RationalModel | None = None,
) -> tuple[D2RationalModel, dict[str, list[RationalRelation]]]:
    """Build the shared residuals and the two Eq.(113) branches separately."""

    rational_model = model or build_d2_rational_model()
    presentation = compile_q_presentation_n4()
    inventory = presentation["relation_inventory"]
    stage_index = _cpobc_stage_index()
    shared: list[RationalRelation] = []

    for record in inventory["CPOBC_residuals"]:
        identifier = f"{record['relation_id']}:{record['equation_id']}"
        shared.append(
            RationalRelation(
                relation_id=identifier,
                family="CPOBC",
                source_stage=stage_index[
                    (record["relation_id"], record["equation_id"])
                ],
                source_index_branch="SHARED_CORE",
                matrix=_matrix_from_expression(
                    rational_model,
                    record["residual_expression"],
                    provenance=identifier,
                ),
                provenance={
                    "relation_id": record["relation_id"],
                    "equation_id": record["equation_id"],
                    "v032_residual_sha256": record[
                        "v032_residual_sha256"
                    ],
                    "v033_Q_dependency_residual_sha256": record[
                        "Q_dependency_residual_sha256"
                    ],
                },
            )
        )
    for record in inventory["strong_MSR_residuals"]:
        identifier = record["constraint_id"]
        shared.append(
            RationalRelation(
                relation_id=identifier,
                family="STRONG_OPERATOR_MSR",
                source_stage=_stage_from_causet_id(record["source_id"]),
                source_index_branch="SHARED_CORE",
                matrix=_matrix_from_expression(
                    rational_model,
                    record["residual_expression"],
                    provenance=identifier,
                ),
                provenance={
                    "constraint_id": identifier,
                    "source_id": record["source_id"],
                    "v032_residual_sha256": record[
                        "v032_residual_sha256"
                    ],
                    "v033_Q_dependency_residual_sha256": record[
                        "Q_dependency_residual_sha256"
                    ],
                },
            )
        )
    for record in inventory["local_operator_GC_residuals"]:
        identifier = record["relation_id"]
        endpoint_stage = _stage_from_causet_id(
            record["endpoint_causet_id"]
        )
        shared.append(
            RationalRelation(
                relation_id=identifier,
                family="LOCAL_OPERATOR_GC",
                source_stage=endpoint_stage - 1,
                source_index_branch="SHARED_CORE",
                matrix=_matrix_from_expression(
                    rational_model,
                    record["residual_expression"],
                    provenance=identifier,
                ),
                provenance={
                    "relation_id": identifier,
                    "endpoint_causet_id": record["endpoint_causet_id"],
                    "path_provenance": record["path_provenance"],
                    "v033_Q_dependency_residual_sha256": record[
                        "Q_dependency_residual_sha256"
                    ],
                },
            )
        )

    branches: dict[str, list[RationalRelation]] = {}
    branch_mapping = {
        DERIVED_BRANCH: V033_DERIVED_BRANCH,
        LITERAL_BRANCH: V033_LITERAL_BRANCH,
    }
    for branch, v033_branch in branch_mapping.items():
        records = list(shared)
        for index, record in enumerate(
            presentation["source_index_branches"][v033_branch][
                "path_consistency_relations"
            ]
        ):
            identifier = (
                f"eq113:{branch}:{record['causet_id']}:{index:03d}"
            )
            records.append(
                RationalRelation(
                    relation_id=identifier,
                    family="EQ112_PATH_CONSISTENCY",
                    source_stage=_stage_from_causet_id(record["causet_id"]),
                    source_index_branch=branch,
                    matrix=_matrix_from_word_equality(
                        rational_model,
                        record["lhs_word"],
                        record["rhs_word"],
                        provenance=identifier,
                    ),
                    provenance={
                        "causet_id": record["causet_id"],
                        "alpha_path_id": record["alpha_path_id"],
                        "beta_path_id": record["beta_path_id"],
                        "word_equation_sha256": record[
                            "word_equation_sha256"
                        ],
                        "outside_n4_Q_inventory": record[
                            "outside_n4_Q_inventory"
                        ],
                    },
                )
            )
        branches[branch] = records
    return rational_model, branches


def _canonical_equation_id(model: D2RationalModel, expression_id: str) -> str:
    if expression_id == model.arena.zero:
        return expression_id
    negative = model.arena.neg(expression_id)
    return min(expression_id, negative)


def _equation_inventory(
    model: D2RationalModel,
    relations: Iterable[RationalRelation],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    representatives: dict[str, str] = {}
    for relation in relations:
        for row in range(2):
            for column in range(2):
                expression_id = relation.matrix.numerator[row][column]
                if expression_id == model.arena.zero:
                    continue
                canonical = _canonical_equation_id(model, expression_id)
                representatives.setdefault(canonical, expression_id)
                grouped[canonical].append(
                    {
                        "relation_id": relation.relation_id,
                        "family": relation.family,
                        "source_stage": relation.source_stage,
                        "source_index_branch": relation.source_index_branch,
                        "matrix_entry": [row, column],
                        "original_expression_id": expression_id,
                        "relation_provenance": relation.provenance,
                    }
                )
    equations = [
        {
            "equation_id": f"numerator-{digest.split(':', 1)[1][:20]}",
            "canonical_expression_id": digest,
            "representative_expression_id": representatives[digest],
            "provenance": grouped[digest],
            "minimum_source_stage": min(
                item["source_stage"] for item in grouped[digest]
            ),
            "maximum_source_stage": max(
                item["source_stage"] for item in grouped[digest]
            ),
        }
        for digest in sorted(grouped)
    ]
    return equations, grouped


@lru_cache(maxsize=1)
def compile_localised_polynomial_systems_v034() -> dict[str, Any]:
    """Compile branch-separated numerator ideals plus nonzero-factor ledgers."""

    model, branch_relations = build_localised_relations()
    systems: dict[str, Any] = {}
    stage_names = {
        2: "STAGE_1_2",
        3: "STAGE_1_3",
        4: "STAGE_1_4",
    }
    for branch, relations in branch_relations.items():
        equations, _ = _equation_inventory(model, relations)
        incremental = []
        for maximum_stage, stage_name in stage_names.items():
            selected_relations = [
                relation
                for relation in relations
                if relation.source_stage <= maximum_stage
            ]
            selected_equations, _ = _equation_inventory(
                model,
                selected_relations,
            )
            factor_records = [
                record
                for record in model.denominator_factors.values()
                if record["stage"] is None
                or int(record["stage"]) <= maximum_stage
            ]
            incremental.append(
                {
                    "stage_system": stage_name,
                    "maximum_source_stage": maximum_stage,
                    "relation_count": len(selected_relations),
                    "canonical_numerator_equation_count": len(
                        selected_equations
                    ),
                    "denominator_factor_count": len(factor_records),
                    "new_variables": (
                        [f"q{maximum_stage}_{i}{j}" for i in (1, 2) for j in (1, 2)]
                        if maximum_stage > 2
                        else [
                            f"q{stage}_{i}{j}"
                            for stage in (1, 2)
                            for i in (1, 2)
                            for j in (1, 2)
                        ]
                    ),
                    "first_inconsistency": "NOT_YET_SOLVED",
                    "surviving_components": "NOT_YET_SOLVED",
                }
            )
        q_indices = [1, 2, 3, 4]
        if branch == LITERAL_BRANCH:
            q_indices.append(5)
        systems[branch] = {
            "source_index_branch": branch,
            "generator_inventory": [f"Q_{stage}" for stage in q_indices],
            "maximum_Q_index": max(q_indices),
            "scalar_unknowns_before_stratum_substitution": 4 * len(q_indices),
            "relation_count": len(relations),
            "relation_family_counts": {
                family: sum(
                    relation.family == family for relation in relations
                )
                for family in sorted({relation.family for relation in relations})
            },
            "canonical_numerator_equation_count": len(equations),
            "equations": equations,
            "incremental_systems": incremental,
            "denominator_factor_count": len(model.denominator_factors),
            "finite_classification_scope": (
                "n<=4 Q1..Q4 finite operator system"
                if branch == DERIVED_BRANCH
                else (
                    "n<=4 source-stage system with independent Q5 only in "
                    "literal Eq.(113) path-consistency relations"
                )
            ),
        }
    branch_disjoint = not (
        {relation.relation_id for relation in branch_relations[DERIVED_BRANCH]}
        - {
            relation.relation_id
            for relation in branch_relations[DERIVED_BRANCH]
            if relation.source_index_branch == "SHARED_CORE"
        }
    ) & {
        relation.relation_id
        for relation in branch_relations[LITERAL_BRANCH]
        if relation.source_index_branch != "SHARED_CORE"
    }
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-localisation-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "source_index_audit": SOURCE_VERDICT,
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "systems": systems,
        "denominator_factors": list(model.denominator_factors.values()),
        "saturation_method": SATURATION_METHOD,
        "saturation_plan": {
            "numerator_ideal_only_is_sufficient": False,
            "one_giant_product_expanded": False,
            "method": (
                "sequential Rabinowitsch variables z_i*f_i-1 or CAS-native "
                "sequential saturation"
            ),
            "status": "COMPILED_NOT_FULLY_EXECUTED",
        },
        "branch_relations_mixed": not branch_disjoint,
        "assumptions": [
            "PAPER_STRONG_OPERATOR_PROFILE",
            "all rational denominators and reconstructed transition determinants nonzero",
            "Eq.(113) source-index branches are separate ideals",
        ],
        "completeness_scope": (
            "numerator and nonzero-factor compilation for both source-index "
            "branches; exact component elimination is a separate phase"
        ),
        "exact_numeric_distinction": "EXACT_STRUCTURAL_POLYNOMIAL_COMPILATION",
        "unresolved_components": [
            "sequential saturation has not been completed for every chart",
            "characteristic-zero primary decomposition is not complete",
        ],
        "passed": branch_disjoint,
        "verdict": (
            "D2_LOCALISED_SYSTEMS_COMPILED_BRANCH_SEPARATE"
            if branch_disjoint
            else "D2_LOCALISED_SYSTEMS_BRANCH_MIXING_ERROR"
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "systems": {
                branch: [
                    record["canonical_expression_id"]
                    for record in systems[branch]["equations"]
                ]
                for branch in sorted(systems)
            },
            "denominator_factors": [
                record["factor_id"]
                for record in payload["denominator_factors"]
            ],
            "saturation_method": SATURATION_METHOD,
        }
    )
    return payload


d2_localisation_v034 = compile_localised_polynomial_systems_v034
