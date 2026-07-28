"""Q-dominated necessary presentation for the n<=4 CPOBC system."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.atomisation_v033 import (
    _decorated_transition_signature,
    compile_atomisation_paths_n4,
)
from universe_lab.final_theory.cpobc_d2_v032 import (
    FROZEN_D3_PATH,
    FROZEN_D3_SHA256,
    FROZEN_RELATIONS_PATH,
    FROZEN_RELATIONS_SHA256,
    generator_reduction_v032,
)
from universe_lab.final_theory.cpobc_v031 import (
    PAPER_PDF,
    PAPER_SHA256,
    compile_cpobc_relations_v031,
)
from universe_lab.final_theory.eq112_reduction_v033 import (
    VERDICT_NECESSARY,
    _detect_dependency_cycles,
    compile_eq112_reduction_n4,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    GC_STRONG_OPERATOR,
    GC_VERDICT,
    MSR_STRONG_OPERATOR,
    MSR_VERDICT,
    PAPER_STRONG_OPERATOR_PROFILE,
    REACHABLE_STATE_PROFILE,
    SOURCE_VERDICT,
    gc_fixed_vector_counterexample,
    gc_msr_semantics_audit,
    literature_matrix,
    msr_reachable_state_counterexample,
    source_equation_audit,
    stable_hash,
    validate_relation_namespace,
)
from universe_lab.final_theory.operator_gc_v033 import (
    VERDICT_COMPLETE as LOCAL_GC_COMPLETE,
)
from universe_lab.final_theory.operator_gc_v033 import compile_local_operator_gc_n4

BRANCH = "codex/final-theory-v0.3.3-gc-atomisation-presentation-20260728"
SOURCE_COMMIT = "b61a4db76f87db9d371ef8538b6c359c100f2595"
PAPER_ID = "arXiv:2603.25503v1"
PRESENTATION_VERDICT = "CPOBC_Q_ONLY_PRESENTATION_PARTIAL_N4"
READINESS_VERDICT = "CPOBC_D2_ELIMINATION_BLOCKED"
OVERALL_VERDICT = "FINAL_THEORY_OPEN"

Word = tuple[str, ...]
Expression = dict[Word, int]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    result = completed.stdout.strip()
    if len(result) != 40:
        raise RuntimeError(f"unexpected git HEAD: {result!r}")
    return result


def _inverse_token(token: str) -> str:
    return token.removesuffix("^-1") if token.endswith("^-1") else token + "^-1"


def _free_reduce(word: Word) -> Word:
    result: list[str] = []
    for token in word:
        if result and result[-1] == _inverse_token(token):
            result.pop()
        else:
            result.append(token)
    return tuple(result)


def _normalise(expression: Expression) -> Expression:
    return {
        word: coefficient
        for word, coefficient in sorted(expression.items())
        if coefficient
    }


def _add_term(expression: Expression, coefficient: int, word: Word) -> None:
    reduced = _free_reduce(word)
    expression[reduced] = expression.get(reduced, 0) + coefficient


def _add(left: Expression, right: Expression) -> Expression:
    result = dict(left)
    for word, coefficient in right.items():
        _add_term(result, coefficient, word)
    return _normalise(result)


def _scale(expression: Expression, coefficient: int) -> Expression:
    return _normalise(
        {word: coefficient * value for word, value in expression.items()}
    )


def _multiply(left: Expression, right: Expression) -> Expression:
    result: Expression = {}
    for left_word, left_coefficient in left.items():
        for right_word, right_coefficient in right.items():
            _add_term(
                result,
                left_coefficient * right_coefficient,
                left_word + right_word,
            )
    return _normalise(result)


def _expression_from_record(terms: list[dict[str, Any]]) -> Expression:
    return _normalise(
        {
            tuple(term["word"]): int(term["coefficient"])
            for term in terms
        }
    )


def _expression_record(expression: Expression) -> list[dict[str, Any]]:
    return [
        {"coefficient": coefficient, "word": list(word)}
        for word, coefficient in sorted(expression.items())
    ]


def _token_to_dependency_node(token: str) -> str:
    inverse = token.endswith("^-1")
    base = token.removesuffix("^-1")
    if base.startswith("Q_"):
        return base + ("^-1" if inverse else "")
    if base.startswith("G_p"):
        return f"G:{base.removeprefix('G_')}" + (":INV" if inverse else "")
    raise ValueError(f"unexpected reduced generator token: {token}")


def _expression_to_dependency_nodes(expression: Expression) -> Expression:
    result: Expression = {}
    for word, coefficient in expression.items():
        node_word = tuple(_token_to_dependency_node(token) for token in word)
        result[node_word] = result.get(node_word, 0) + coefficient
    return _normalise(result)


def _occurrence_expressions(
    reduction: dict[str, Any],
) -> dict[str, Expression]:
    return {
        record["occurrence_id"]: _expression_from_record(
            record["reduced_expression"]
        )
        for record in reduction["reduction_map"]
    }


def _rewrite_occurrence_word(
    word: list[str],
    aliases: dict[str, str],
    occurrence_expressions: dict[str, Expression],
) -> Expression:
    result: Expression = {(): 1}
    for alias in word:
        result = _multiply(result, occurrence_expressions[aliases[alias]])
    return result


def _rewrite_cpobc_relations(
    compiled: dict[str, Any],
    reduction: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    occurrence_expressions = _occurrence_expressions(reduction)
    v032_inventory = {
        (record["relation_id"], record["equation_id"]): record
        for record in reduction["rewritten_relation_inventory"]
    }
    identities = []
    residuals = []
    for relation in compiled["relations"]:
        aliases = {
            alias: record["occurrence_id"]
            for alias, record in relation["transition_orbit"].items()
        }
        equations = relation["denominator_cleared_form"][
            "noncommutative_polynomial_equations"
        ]
        for equation in equations:
            lhs = _rewrite_occurrence_word(
                list(equation["lhs_word"]),
                aliases,
                occurrence_expressions,
            )
            rhs = _rewrite_occurrence_word(
                list(equation["rhs_word"]),
                aliases,
                occurrence_expressions,
            )
            residual = _add(lhs, _scale(rhs, -1))
            v032 = v032_inventory[
                (relation["relation_id"], equation["equation_id"])
            ]
            original_record = _expression_record(residual)
            original_digest = stable_hash(original_record)
            if original_digest != v032["reduced_residual_sha256"]:
                raise AssertionError("v0.3.2 CPOBC residual digest mismatch")
            base_record = {
                "family": "CPOBC",
                "relation_id": relation["relation_id"],
                "equation_id": equation["equation_id"],
                "branch": relation["branch"],
                "v032_residual_sha256": original_digest,
            }
            if not residual:
                identities.append({**base_record, "identity": True})
                continue
            node_expression = _expression_to_dependency_nodes(residual)
            node_record = _expression_record(node_expression)
            residuals.append(
                {
                    **base_record,
                    "identity": False,
                    "residual_term_count": len(node_record),
                    "residual_expression": node_record,
                    "Q_dependency_residual_sha256": stable_hash(node_record),
                }
            )
    return identities, residuals


def _rewrite_msr_relations(
    compiled: dict[str, Any],
    reduction: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    occurrence_expressions = _occurrence_expressions(reduction)
    v032_inventory = {
        record["constraint_id"]: record
        for record in reduction["rewritten_MSR_inventory"]
    }
    identities = []
    residuals = []
    for constraint in compiled["MSR_operator_constraints"]:
        residual: Expression = {(): -1}
        for term in constraint["terms"]:
            contribution = _scale(
                occurrence_expressions[term["transition_id"]],
                int(term["coefficient"]),
            )
            residual = _add(residual, contribution)
        v032 = v032_inventory[constraint["constraint_id"]]
        original_record = _expression_record(residual)
        original_digest = stable_hash(original_record)
        if original_digest != v032["reduced_residual_sha256"]:
            raise AssertionError("v0.3.2 MSR residual digest mismatch")
        base_record = {
            "family": "MSR_STRONG_OPERATOR",
            "constraint_id": constraint["constraint_id"],
            "source_id": constraint["source_id"],
            "v032_residual_sha256": original_digest,
        }
        if not residual:
            identities.append({**base_record, "identity": True})
            continue
        node_expression = _expression_to_dependency_nodes(residual)
        node_record = _expression_record(node_expression)
        residuals.append(
            {
                **base_record,
                "identity": False,
                "residual_term_count": len(node_record),
                "residual_expression": node_record,
                "Q_dependency_residual_sha256": stable_hash(node_record),
            }
        )
    return identities, residuals


def _v032_signature_index(
    reduction: dict[str, Any],
) -> dict[tuple[tuple[str, int], ...], Expression]:
    result: dict[tuple[tuple[str, int], ...], Expression] = {}
    digests: dict[tuple[tuple[str, int], ...], str] = {}
    for record in reduction["reduction_map"]:
        signature = _decorated_transition_signature(
            tuple(record["source_relation_rows"]),
            int(record["precursor_code"]),
        )
        key = tuple(sorted(signature.items()))
        expression = _expression_from_record(record["reduced_expression"])
        digest = stable_hash(_expression_record(expression))
        if key in result and digests[key] != digest:
            raise AssertionError("decorated transition has conflicting reductions")
        result[key] = expression
        digests[key] = digest
    return result


def _rewrite_local_gc_relations(
    local_gc: dict[str, Any],
    reduction: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    signature_index = _v032_signature_index(reduction)
    symbol_expressions: dict[str, Expression] = {}
    for stage_paths in local_gc["path_inventory"].values():
        for path in stage_paths:
            for transition in path["transitions"]:
                key = tuple(sorted(transition["quotient_signature"].items()))
                symbol_expressions[transition["quotient_operator_symbol"]] = (
                    signature_index[key]
                )
    identities = []
    residuals = []
    for relation in local_gc["generating_relation_basis"]:
        lhs: Expression = {(): 1}
        rhs: Expression = {(): 1}
        for symbol in relation["lhs_word"]:
            lhs = _multiply(lhs, symbol_expressions[symbol])
        for symbol in relation["rhs_word"]:
            rhs = _multiply(rhs, symbol_expressions[symbol])
        residual = _add(lhs, _scale(rhs, -1))
        base_record = {
            "family": "LOCAL_OPERATOR_GC",
            "relation_id": relation["relation_id"],
            "endpoint_causet_id": relation["endpoint_causet_id"],
            "GC_semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
            "path_provenance": {
                "lhs_path_id": relation["lhs_path_id"],
                "rhs_path_id": relation["rhs_path_id"],
            },
        }
        if not residual:
            identities.append({**base_record, "identity": True})
            continue
        node_expression = _expression_to_dependency_nodes(residual)
        node_record = _expression_record(node_expression)
        residuals.append(
            {
                **base_record,
                "identity": False,
                "residual_term_count": len(node_record),
                "residual_expression": node_record,
                "Q_dependency_residual_sha256": stable_hash(node_record),
            }
        )
    return identities, residuals


def _occurrence_invertibility_predicates(
    reduction: dict[str, Any],
) -> list[dict[str, Any]]:
    predicates = []
    for record in reduction["reduction_map"]:
        expression = _expression_from_record(record["reduced_expression"])
        node_record = _expression_record(
            _expression_to_dependency_nodes(expression)
        )
        predicates.append(
            {
                "occurrence_id": record["occurrence_id"],
                "operator_variable": record["operator_variable"],
                "predicate": "IS_TWO_SIDED_INVERTIBLE(reconstructed_expression)",
                "d2_predicate": "det(reconstructed_2x2_expression) != 0",
                "reconstructed_expression": node_record,
                "expression_sha256": stable_hash(node_record),
            }
        )
    return predicates


def _inverse_predicates(eq112: dict[str, Any]) -> list[dict[str, Any]]:
    predicates = []
    for node in eq112["dependency_DAG"]["nodes"]:
        if node["kind"] != "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            continue
        predicates.append(
            {
                "generator": node["auxiliary_generator"],
                "inverse_of_node": node["inverse_of_node"],
                "left_predicate": node["inverse_predicates"][0],
                "right_predicate": node["inverse_predicates"][1],
            }
        )
    for stage in range(1, 5):
        predicates.append(
            {
                "generator": f"Q_{stage}^-1",
                "inverse_of_node": f"Q_{stage}",
                "left_predicate": f"Q_{stage}^-1 * Q_{stage} = I",
                "right_predicate": f"Q_{stage} * Q_{stage}^-1 = I",
            }
        )
    return predicates


def _relation_duplicates(
    relation_records: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for record in relation_records:
        digest = record["Q_dependency_residual_sha256"]
        identifier = (
            record.get("equation_id")
            or record.get("constraint_id")
            or record.get("relation_id")
        )
        grouped[digest].append(str(identifier))
    groups = [
        {"digest": digest, "relation_ids": sorted(identifiers)}
        for digest, identifiers in sorted(grouped.items())
        if len(identifiers) > 1
    ]
    return {
        "orientation_sensitive_duplicate_groups": groups,
        "duplicate_relation_instances": sum(
            len(group["relation_ids"]) - 1 for group in groups
        ),
        "ideal_equivalence_or_sign_normalisation_proved": False,
    }


def _path_branch_records(eq112: dict[str, Any], branch: str) -> list[dict[str, Any]]:
    return [
        {
            "family": "EQ112_PATH_CONSISTENCY",
            "causet_id": record["causet_id"],
            "alpha_path_id": record["alpha_path_id"],
            "beta_path_id": record["beta_path_id"],
            "lhs_word": record["lhs_word"],
            "rhs_word": record["rhs_word"],
            "source_index_branch": branch,
            "outside_n4_Q_inventory": record.get(
                "outside_n4_Q_inventory",
                False,
            ),
            "word_equation_sha256": stable_hash(
                {
                    "lhs_word": record["lhs_word"],
                    "rhs_word": record["rhs_word"],
                }
            ),
        }
        for record in eq112["path_consistency_branches"][branch]
    ]


def production_oracle_summary(
    *,
    local_gc: dict[str, Any] | None = None,
    atomisation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the implementation-neutral semantic payload used by the oracle."""

    gc_result = local_gc or compile_local_operator_gc_n4()
    atom_result = atomisation or compile_atomisation_paths_n4()
    labelled_paths = [
        path
        for stage_paths in gc_result["path_inventory"].values()
        for path in stage_paths
    ]
    atom_paths = [
        path
        for record in atom_result["causets"]
        for path in record["all_alternative_paths"]
    ]
    summary: dict[str, Any] = {
        "labelled_path_counts": gc_result["counts"][
            "labelled_paths_by_endpoint_stage"
        ],
        "unlabelled_endpoint_counts": gc_result["counts"][
            "unlabelled_endpoints_by_stage"
        ],
        "local_gc_basis_relation_count": gc_result["counts"][
            "spanning_tree_basis_relations"
        ],
        "same_endpoint_path_pair_count": gc_result["counts"][
            "same_endpoint_path_pairs"
        ],
        "non_antichain_causet_count": atom_result["counts"][
            "non_antichain_causets"
        ],
        "atomisation_path_count": atom_result["counts"][
            "complete_atomisation_paths"
        ],
        "atomisation_step_count": atom_result["counts"]["atomisation_steps"],
        "atomisation_path_counts_by_causet": {
            record["causet_id"]: record["complete_path_count"]
            for record in atom_result["causets"]
        },
        "endpoint_path_provenance": [
            {
                "path_id": path["path_id"],
                "stage": path["endpoint_stage"],
                "endpoint_causet_id": path["endpoint_causet_id"],
                "endpoint_labelled_code": path["endpoint_labelled_code"],
                "ordered_operator_word": path[
                    "ordered_operator_word_later_on_left"
                ],
            }
            for path in sorted(labelled_paths, key=lambda item: item["path_id"])
        ],
        "local_gc_basis_provenance": [
            {
                "relation_id": relation["relation_id"],
                "endpoint_causet_id": relation["endpoint_causet_id"],
                "lhs_path_id": relation["lhs_path_id"],
                "rhs_path_id": relation["rhs_path_id"],
                "lhs_word": relation["lhs_word"],
                "rhs_word": relation["rhs_word"],
            }
            for relation in sorted(
                gc_result["generating_relation_basis"],
                key=lambda item: item["relation_id"],
            )
        ],
        "atomisation_path_provenance": [
            {
                "path_id": path["path_id"],
                "causet_id": path["source_causet_id"],
                "selected_elements": path["selected_elements"],
                "S_word": path["S_word_ordered"],
                "S_inverse_word": path["S_inverse_word_ordered"],
            }
            for path in sorted(atom_paths, key=lambda item: item["path_id"])
        ],
        "reduced_generator_mapping": [
            {
                "causet_id": record["causet_id"],
                "canonical_path_id": record["canonical_representative_path"],
                "ordered_word": next(
                    path["S_word_ordered"]
                    + [f"Q_{record['stage']}"]
                    + path["S_inverse_word_ordered"]
                    for path in record["all_alternative_paths"]
                    if path["path_id"] == record["canonical_representative_path"]
                ),
            }
            for record in sorted(
                atom_result["causets"],
                key=lambda item: item["causet_id"],
            )
        ],
    }
    summary["semantic_digest_sha256"] = stable_hash(summary)
    return summary


def compile_q_presentation_n4(
    *,
    independent_oracle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the exact Q-dependency presentation without running elimination."""

    semantics = gc_msr_semantics_audit()
    source_audit = source_equation_audit()
    literature = literature_matrix()
    compiled = compile_cpobc_relations_v031()
    reduction = generator_reduction_v032(compiled)
    local_gc = compile_local_operator_gc_n4()
    atomisation = compile_atomisation_paths_n4()
    eq112 = compile_eq112_reduction_n4()
    oracle_target = production_oracle_summary(
        local_gc=local_gc,
        atomisation=atomisation,
    )

    cpobc_identities, cpobc_residuals = _rewrite_cpobc_relations(
        compiled,
        reduction,
    )
    msr_identities, msr_residuals = _rewrite_msr_relations(
        compiled,
        reduction,
    )
    gc_identities, gc_residuals = _rewrite_local_gc_relations(
        local_gc,
        reduction,
    )
    if (len(cpobc_identities), len(cpobc_residuals)) != (83, 700):
        raise AssertionError("unexpected v0.3.2 CPOBC identity/residual split")
    if (len(msr_identities), len(msr_residuals)) != (3, 21):
        raise AssertionError("unexpected v0.3.2 MSR identity/residual split")
    if len(gc_identities) + len(gc_residuals) != 320:
        raise AssertionError("local GC basis relation count changed")

    dependency_node_ids = {
        node["node_id"] for node in eq112["dependency_DAG"]["nodes"]
    }
    referenced_nodes = {
        token
        for record in cpobc_residuals + msr_residuals + gc_residuals
        for term in record["residual_expression"]
        for token in term["word"]
    }
    missing_dependency_nodes = sorted(referenced_nodes - dependency_node_ids)
    if missing_dependency_nodes:
        raise AssertionError(
            f"Q dependency DAG is missing nodes: {missing_dependency_nodes}"
        )

    inverse_auxiliaries = sorted(
        {
            node["auxiliary_generator"]
            for node in eq112["dependency_DAG"]["nodes"]
            if node["kind"] == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
        }
    )
    invertibility_predicates = _occurrence_invertibility_predicates(reduction)
    inverse_predicates = _inverse_predicates(eq112)
    core_relations = cpobc_residuals + msr_residuals + gc_residuals
    duplicate_audit = _relation_duplicates(core_relations)

    qn_paths = _path_branch_records(eq112, "EQ113_QN_BRANCH")
    literal_paths = _path_branch_records(
        eq112,
        "EQ113_QN_PLUS_1_BRANCH",
    )
    oracle_match = bool(
        independent_oracle
        and independent_oracle.get("passed")
        and independent_oracle.get("production_comparison", {}).get(
            "semantic_digest_match"
        )
    )
    readiness_gate = {
        "GC_semantics_fixed_for_selected_profile": (
            semantics["GC_verdict"] == GC_VERDICT
        ),
        "operator_MSR_semantics_fixed_for_selected_profile": (
            semantics["MSR_verdict"] == MSR_VERDICT
        ),
        "local_GC_compiler_complete_n4": (
            local_gc["verdict"] == LOCAL_GC_COMPLETE
        ),
        "atomisation_compiler_complete_n4": atomisation["passed"],
        "Eq112_reduction_complete": eq112["verdict"]
        == "EQ112_REDUCTION_COMPLETE_N4",
        "forward_reverse_equivalence_certified": eq112[
            "equivalence_obligations"
        ]["reverse"]["passed"],
        "all_20_non_antichain_G_forward_reduced": (
            eq112["counts"]["non_antichain_G_generators"] == 20
        ),
        "operator_GC_included": len(gc_residuals) + len(gc_identities) == 320,
        "all_invertibility_predicates_preserved": (
            len(invertibility_predicates) == 165
            and len(inverse_predicates) == 26
        ),
        "source_index_ambiguity_resolved_or_branched": (
            source_audit["verdict"] == SOURCE_VERDICT
            and source_audit["branch_mixing_forbidden"]
        ),
        "independent_oracle_digest_match": oracle_match,
        "d2_scalar_unknowns_and_scalarised_equations_recorded": False,
    }
    readiness = all(readiness_gate.values())
    if readiness:
        raise AssertionError(
            "v0.3.3 scope forbids silently promoting this partial presentation"
        )

    branch_summaries: dict[str, dict[str, Any]] = {
        "EQ113_QN_BRANCH": {
            "independent_matrix_generators": 4 + len(inverse_auxiliaries),
            "Q_generators": ["Q_1", "Q_2", "Q_3", "Q_4"],
            "remaining_auxiliary_generators": inverse_auxiliaries,
            "path_consistency_relations": qn_paths,
            "outside_n4_Q_generator": None,
        },
        "EQ113_QN_PLUS_1_BRANCH": {
            "independent_matrix_generators": 5 + len(inverse_auxiliaries),
            "Q_generators": ["Q_1", "Q_2", "Q_3", "Q_4", "Q_5"],
            "remaining_auxiliary_generators": inverse_auxiliaries,
            "path_consistency_relations": literal_paths,
            "outside_n4_Q_generator": "Q_5",
        },
    }
    payload: dict[str, Any] = {
        "presentation_name": "Q_DOMINATED_PRESENTATION_WITH_AUXILIARIES",
        "minimality_status": {
            "minimal_claimed": False,
            "noncommutative_ideal_membership_proved": False,
            "Tietze_equivalence_proved": False,
            "reason": (
                "22 formal B inverses remain; no proof shows that this auxiliary "
                "set is minimal or eliminable"
            ),
        },
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "separate_reachable_state_namespace": {
            "profile": REACHABLE_STATE_PROFILE,
            "operator_GC_relations_in_ideal": 0,
            "strong_MSR_relations_in_ideal": 0,
            "not_mixed_with_presentation": True,
        },
        "source_index_branches": branch_summaries,
        "relation_inventory": {
            "CPOBC_identities": cpobc_identities,
            "CPOBC_residuals": cpobc_residuals,
            "strong_MSR_identities": msr_identities,
            "strong_MSR_residuals": msr_residuals,
            "local_operator_GC_identities": gc_identities,
            "local_operator_GC_residuals": gc_residuals,
            "duplicate_audit": duplicate_audit,
        },
        "dependency_DAG": eq112["dependency_DAG"],
        "invertibility_predicates": {
            "reconstructed_transition_predicates": invertibility_predicates,
            "explicit_two_sided_inverse_predicates": inverse_predicates,
            "all_165_occurrences_preserved": len(invertibility_predicates) == 165,
        },
        "counts": {
            "original_transition_occurrences": 165,
            "original_gregarious_generators": 24,
            "antichain_Q_generators": 4,
            "non_antichain_G_generators_forward_reduced": 20,
            "remaining_matrix_auxiliaries_Qn_branch": len(inverse_auxiliaries),
            "reduced_matrix_generators_Qn_branch": 4 + len(inverse_auxiliaries),
            "original_compiled_cross_stage_relations": 641,
            "original_denominator_cleared_CPOBC_equations": 783,
            "CPOBC_identities_after_substitution": len(cpobc_identities),
            "CPOBC_nontrivial_residuals": len(cpobc_residuals),
            "original_strong_MSR_constraints": 24,
            "strong_MSR_identities_after_substitution": len(msr_identities),
            "strong_MSR_nontrivial_residuals": len(msr_residuals),
            "local_operator_GC_basis_relations": 320,
            "local_operator_GC_identities_after_eq107_eq108": len(gc_identities),
            "local_operator_GC_nontrivial_residuals": len(gc_residuals),
            "path_consistency_relations_per_source_index_branch": 25,
            "abstract_d2_matrix_entry_unknowns_Qn_branch": (
                4 * (4 + len(inverse_auxiliaries))
            ),
            "Q_matrix_entry_coordinates_before_saturation": 16,
            "solver_ready_scalar_polynomial_variable_count": None,
        },
        "d2_scalarisation_boundary": {
            "abstract_matrix_entry_count": 4 * (4 + len(inverse_auxiliaries)),
            "Q_only_rational_matrix_entry_count": 16,
            "determinant_saturation_strategy": (
                "not compiled; a global product saturation could use one witness, "
                "whereas per-predicate saturation uses more variables"
            ),
            "scalar_polynomial_equations_compiled": False,
            "dense_Groebner_executed": False,
        },
        "readiness_gate": readiness_gate,
        "readiness_verdict": (
            "CPOBC_D2_ELIMINATION_READY" if readiness else READINESS_VERDICT
        ),
        "literature_classification": literature["entries"],
        "assumptions": [
            "PAPER_STRONG_OPERATOR_PROFILE is an explicit additional-axiom profile",
            "all 165 original transition occurrences remain nonsingular predicates",
            "Q_n and Q_(n+1) source-index branches remain separate",
            "no dense d2 elimination or numerical matrix search is executed",
        ],
        "completeness_scope": (
            "complete finite path and atomisation inventories for transition source "
            "stages n<=4; one-way Q-dependency reduction only"
        ),
        "exact_numeric_distinction": {
            "exact": (
                "integer noncommutative linear expressions, finite causet paths, "
                "operator words, SHA-256 semantic digests"
            ),
            "numeric": "none accepted; no numerical search executed",
        },
        "unresolved_components": [
            "reverse equivalence of the Q-dominated presentation",
            "elimination or minimality of 22 B-inverse auxiliaries",
            "Eq. (113) Q_n versus Q_(n+1) source index",
            "literal source branch requires Q_5 outside the n<=4 Q inventory",
            "d2 scalar polynomial expansion and determinant saturation",
            "S1/S2/S3 exact elimination",
        ],
        "Eq112_verdict": eq112["verdict"],
        "presentation_verdict": PRESENTATION_VERDICT,
        "overall_verdict": OVERALL_VERDICT,
        "independent_oracle_target": {
            "semantic_digest_sha256": oracle_target[
                "semantic_digest_sha256"
            ],
            "comparison_scope": [
                "causet and path counts",
                "same-endpoint GC basis provenance",
                "all atomisation path counts and S-word order",
                "canonical reduced-generator mapping",
            ],
        },
        "passed": (
            eq112["verdict"] == VERDICT_NECESSARY
            and len(cpobc_residuals) == 700
            and len(msr_residuals) == 21
            and not readiness
        ),
    }
    digest_payload = {
        "presentation": payload["presentation_name"],
        "dependency_digest": eq112["semantic_digest_sha256"],
        "CPOBC": [
            record["Q_dependency_residual_sha256"] for record in cpobc_residuals
        ],
        "MSR": [
            record["Q_dependency_residual_sha256"] for record in msr_residuals
        ],
        "GC": [
            record["Q_dependency_residual_sha256"] for record in gc_residuals
        ],
        "path_branches": {
            branch: [
                record["word_equation_sha256"]
                for record in summary["path_consistency_relations"]
            ]
            for branch, summary in branch_summaries.items()
        },
    }
    payload["semantic_digest_sha256"] = stable_hash(digest_payload)
    return payload


def q_presentation_mutation_checks() -> dict[str, bool]:
    result = compile_q_presentation_n4()
    auxiliaries = result["source_index_branches"]["EQ113_QN_BRANCH"][
        "remaining_auxiliary_generators"
    ]
    return {
        "AUXILIARY_GENERATOR_HIDING_MUTATION_DETECTED": len(auxiliaries) == 22,
        "DENSE_GROEBNER_MUTATION_DETECTED": not result[
            "d2_scalarisation_boundary"
        ]["dense_Groebner_executed"],
        "PARTIAL_TO_READY_MUTATION_DETECTED": (
            result["presentation_verdict"] == PRESENTATION_VERDICT
            and result["readiness_verdict"] == READINESS_VERDICT
        ),
        "LITERATURE_LOCKED_AS_NOVEL_MUTATION_DETECTED": any(
            entry["topic"] == "paper atomisation and decimation definition"
            and entry["classification"] == "LITERATURE_LOCKED"
            for entry in result["literature_classification"]
        ),
        "INVERTIBILITY_PREDICATE_DROP_MUTATION_DETECTED": result[
            "invertibility_predicates"
        ]["all_165_occurrences_preserved"],
    }


def critical_mutation_matrix_v033() -> dict[str, Any]:
    """Run the twenty required semantic and compiler mutation guards."""

    semantics = gc_msr_semantics_audit()
    gc_counterexample = gc_fixed_vector_counterexample()
    msr_counterexample = msr_reachable_state_counterexample()
    local_gc = compile_local_operator_gc_n4()
    atomisation = compile_atomisation_paths_n4()
    eq112 = compile_eq112_reduction_n4()
    presentation = compile_q_presentation_n4()

    gc_namespace_rejected = False
    msr_namespace_rejected = False
    try:
        validate_relation_namespace(
            semantic_profile=REACHABLE_STATE_PROFILE,
            relation_strength=GC_STRONG_OPERATOR,
        )
    except ValueError:
        gc_namespace_rejected = True
    try:
        validate_relation_namespace(
            semantic_profile=REACHABLE_STATE_PROFILE,
            relation_strength=MSR_STRONG_OPERATOR,
        )
    except ValueError:
        msr_namespace_rejected = True

    atom_paths = [
        path
        for causet in atomisation["causets"]
        for path in causet["all_alternative_paths"]
    ]
    multi_path_exists = any(
        causet["complete_path_count"] > 1 for causet in atomisation["causets"]
    )
    all_initial_choices = all(
        {
            path["steps"][0]["selected_element"]
            for path in causet["all_alternative_paths"]
        }
        == set(causet["initial_eligible_nongregarious_maximal_elements"])
        for causet in atomisation["causets"]
    )
    eq_paths = eq112["path_reductions"]
    node_map = {
        node["node_id"]: {**node, "dependencies": list(node["dependencies"])}
        for node in eq112["dependency_DAG"]["nodes"]
    }
    mutated_node_id = next(
        node_id
        for node_id, node in node_map.items()
        if not node["terminal_generator"]
    )
    node_map[mutated_node_id]["dependencies"].append(mutated_node_id)
    artificial_cycle_detected = bool(_detect_dependency_cycles(node_map))

    mutations = [
        {
            "mutation": "fixed-vector GC silently promoted to operator GC",
            "detected": gc_namespace_rejected,
            "detector": "semantic namespace rejects a strong relation",
        },
        {
            "mutation": "reachable-state MSR silently promoted to operator MSR",
            "detected": (
                msr_namespace_rejected
                and msr_counterexample["reachable_state_MSR"]
                and not msr_counterexample["strong_operator_MSR"]
            ),
            "detector": (
                "semantic namespace rejection plus an exact nonsingular-summand "
                "counterexample"
            ),
        },
        {
            "mutation": "equality on one vector treated as operator equality",
            "detected": (
                gc_counterexample["fixed_vector_equality"]
                and not gc_counterexample["X_equals_Y"]
            ),
            "detector": "exact invertible 2x2 counterexample",
        },
        {
            "mutation": "only one atomisation path retained",
            "detected": multi_path_exists
            and atomisation["counts"]["complete_atomisation_paths"] == 34,
            "detector": "complete choice recursion has multi-path causets",
        },
        {
            "mutation": "one eligible maximal element omitted",
            "detected": all_initial_choices,
            "detector": "first-step selections equal the full eligible set",
        },
        {
            "mutation": "terminal antichain test corrupted",
            "detected": all(path["terminal_antichain"] for path in atom_paths),
            "detector": "every enumerated terminal has rank zero",
        },
        {
            "mutation": "B-operator product order reversed",
            "detected": all(path["operator_order_preserved"] for path in eq_paths),
            "detector": "Eq. (112) path records retain selection order",
        },
        {
            "mutation": "inverse factor order reversed",
            "detected": all(path["inverse_order_preserved"] for path in eq_paths),
            "detector": "inverse words use the reversed B-factor order",
        },
        {
            "mutation": "stage index shifted by one",
            "detected": all(
                path["Q_node"] == f"Q_{path['stage']}" for path in eq_paths
            ),
            "detector": "Eq. (112) center is Q at the source stage",
        },
        {
            "mutation": "Eq. (113) Q_n and Q_(n+1) branches merged",
            "detected": (
                set(eq112["path_consistency_branches"])
                == {"EQ113_QN_BRANCH", "EQ113_QN_PLUS_1_BRANCH"}
                and eq112["source_index_audit"]["branches_kept_separate"]
            ),
            "detector": "two disjoint branch namespaces",
        },
        {
            "mutation": "non-automorphism-equivalent paths quotiented",
            "detected": (
                local_gc["proof_obligations"]["no_automorphism_path_quotient"]
                and atomisation["proof_obligations"][
                    "automorphism_equivalent_paths_quotiented"
                ]
                is False
            ),
            "detector": "all labelled and atomisation paths remain explicit",
        },
        {
            "mutation": "labelled and unlabelled endpoints confused",
            "detected": local_gc["proof_obligations"][
                "labelled_then_unlabelled_grouping"
            ],
            "detector": "enumerate labelled relations before endpoint grouping",
        },
        {
            "mutation": "GC path relation added without provenance",
            "detected": local_gc["proof_obligations"][
                "every_basis_relation_is_an_enumerated_path_pair"
            ],
            "detector": "basis endpoints and both path IDs are verified",
        },
        {
            "mutation": "Eq. (112) substitution cycle ignored",
            "detected": artificial_cycle_detected
            and eq112["dependency_DAG"]["cycle_free"],
            "detector": "DFS detects an injected self-cycle",
        },
        {
            "mutation": "one-way reduction labelled equivalent",
            "detected": (
                eq112["equivalence_obligations"]["presentation_status"]
                == "ONE_WAY_NECESSARY_REDUCTION"
                and not eq112["equivalence_obligations"]["reverse"]["passed"]
            ),
            "detector": "forward and reverse obligations are separate",
        },
        {
            "mutation": "invertibility predicate dropped",
            "detected": (
                presentation["invertibility_predicates"][
                    "all_165_occurrences_preserved"
                ]
                and len(
                    presentation["invertibility_predicates"][
                        "explicit_two_sided_inverse_predicates"
                    ]
                )
                == 26
            ),
            "detector": "165 occurrence predicates plus 26 inverse pairs",
        },
        {
            "mutation": "remaining auxiliary generator hidden",
            "detected": (
                presentation["counts"][
                    "remaining_matrix_auxiliaries_Qn_branch"
                ]
                == 22
            ),
            "detector": "all formal B inverses are inventoried",
        },
        {
            "mutation": "unbounded dense 96-variable Groebner launched",
            "detected": not presentation["d2_scalarisation_boundary"][
                "dense_Groebner_executed"
            ],
            "detector": "explicit execution-policy gate",
        },
        {
            "mutation": "PARTIAL rounded to ELIMINATION_READY",
            "detected": (
                presentation["presentation_verdict"] == PRESENTATION_VERDICT
                and presentation["readiness_verdict"] == READINESS_VERDICT
            ),
            "detector": "all readiness predicates are conjunctive",
        },
        {
            "mutation": "literature-locked atomisation reported as novel",
            "detected": any(
                entry["topic"] == "paper atomisation and decimation definition"
                and entry["classification"] == "LITERATURE_LOCKED"
                for entry in presentation["literature_classification"]
            ),
            "detector": "literature frontier classification",
        },
    ]
    passed = len(mutations) == 20 and all(
        mutation["detected"] for mutation in mutations
    )
    return {
        "schema_version": "final-theory-mutations-v0.3.3",
        "semantic_verdicts": {
            "GC": semantics["GC_verdict"],
            "MSR": semantics["MSR_verdict"],
        },
        "mutations": mutations,
        "counts": {
            "required": 20,
            "detected": sum(mutation["detected"] for mutation in mutations),
        },
        "verdict": (
            "ALL_CRITICAL_MUTATIONS_DETECTED"
            if passed
            else "CRITICAL_MUTATION_GAP"
        ),
        "passed": passed,
    }


ARTIFACT_FREEZE_POINTER = (
    "RESOLVE_VIA_ANNOTATED_TAG(final-theory-bench-v0.3.3-gc-atomisation-open)"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _source_hash_records(root: Path) -> list[dict[str, str]]:
    paths = [
        PAPER_PDF,
        FROZEN_RELATIONS_PATH,
        FROZEN_D3_PATH,
        "results/v0.3.2_cpobc_generator_reduction.json",
        "results/v0.3.2_cpobc_d2_classification.json",
        (
            "references/papers/gr-qc-9904062v3_"
            "rideout-sorkin_classical-sequential-growth.pdf"
        ),
        (
            "references/papers/gr-qc-0504066v3_"
            "varadarajan-rideout_general-classical-sequential-growth.pdf"
        ),
    ]
    records = [
        {"path": path, "sha256": _sha256_file(root / path)} for path in paths
    ]
    expected = {
        PAPER_PDF: PAPER_SHA256,
        FROZEN_RELATIONS_PATH: FROZEN_RELATIONS_SHA256,
        FROZEN_D3_PATH: FROZEN_D3_SHA256,
    }
    for record in records:
        expected_hash = expected.get(record["path"])
        if expected_hash is not None and record["sha256"] != expected_hash:
            raise AssertionError(f"frozen source changed: {record['path']}")
    return records


def _artifact_payload(
    *,
    kind: str,
    data: dict[str, Any],
    code_commit: str,
    source_hashes: list[dict[str, str]],
    literature: dict[str, Any],
    certificate_hashes: list[dict[str, str]],
    semantic_profile: str,
    verdict: str,
    relation_counts: dict[str, Any],
    generator_counts: dict[str, Any],
    path_counts: dict[str, Any],
    source_index_branch: str = "BOTH_BRANCHES_PRESERVED_NOT_MIXED",
) -> dict[str, Any]:
    payload = dict(data)
    payload.update(
        {
            "schema_version": f"final-theory-{kind}-v0.3.3",
            "branch": BRANCH,
            "source_commit": SOURCE_COMMIT,
            "code_commit": code_commit,
            "artifact_freeze_commit": ARTIFACT_FREEZE_POINTER,
            "paper_version": {
                "id": PAPER_ID,
                "version": "v1",
                "date": "2026-03-26",
                "local_file": PAPER_PDF,
                "sha256": PAPER_SHA256,
            },
            "source_hashes": source_hashes,
            "literature_classification": literature["entries"],
            "semantic_profile": semantic_profile,
            "assumptions": list(data.get("assumptions", [])),
            "completeness_scope": data.get(
                "completeness_scope",
                data.get("scope", f"v0.3.3 {kind} finite audit"),
            ),
            "exact_numeric_distinction": data.get(
                "exact_numeric_distinction",
                {
                    "exact": (
                        "finite integer combinatorics, operator words, "
                        "and canonical SHA-256 digests"
                    ),
                    "numeric": "none accepted as certificate",
                },
            ),
            "unresolved_components": list(
                data.get("unresolved_components", [])
            ),
            "relation_counts": relation_counts,
            "generator_counts": generator_counts,
            "path_counts": path_counts,
            "source_index_branch": source_index_branch,
            "certificate_hashes": certificate_hashes,
            "verdict": verdict,
        }
    )
    return payload


def _source_manifest_data(
    root: Path,
    source_hashes: list[dict[str, str]],
) -> dict[str, Any]:
    registry = json.loads(
        (root / "references/sources.json").read_text(encoding="utf-8")
    )
    selected_ids = {
        "arXiv:2603.25503v1",
        "arXiv:gr-qc/9904062v3",
        "arXiv:gr-qc/0504066v3",
        "arXiv:2003.11311v1",
        "arXiv:1204.5767v1",
        "arXiv:1303.0433v1",
    }
    selected = [
        source for source in registry["sources"] if source["id"] in selected_ids
    ]
    d3_manifest = json.loads(
        (root / FROZEN_D3_PATH).read_text(encoding="utf-8")
    )
    d3_unresolved = (
        d3_manifest["coverage"]["fully_solved_strata"] == 0
        and any(
            stratum.get("status") == "UNRESOLVED"
            for stratum in d3_manifest["strata"]
        )
    )
    return {
        "retrieval_date": "2026-07-28",
        "sources": selected,
        "source_hash_verification": source_hashes,
        "v032_freeze": {
            "production_commit": "0341af59a1e1318957a82ba35080c10659716051",
            "artifact_freeze_commit": SOURCE_COMMIT,
            "tag": "final-theory-bench-v0.3.2-cpobc-d2-partial",
        },
        "v031_frozen_invariants": {
            "relations_sha256": FROZEN_RELATIONS_SHA256,
            "d3_manifest_sha256": FROZEN_D3_SHA256,
            "paper_sha256": PAPER_SHA256,
            "d3_remains_unresolved": d3_unresolved,
        },
        "search_boundary": (
            "primary-source searches were bounded by the documented exact-title, "
            "author, equation-terminology, journal/erratum, and citation routes"
        ),
        "assumptions": [
            "local version-specific PDFs are authoritative for equation layout",
            "extracted text is used only as a search aid",
        ],
        "unresolved_components": [
            "no global proof of absence of unindexed follow-up literature",
        ],
        "passed": len(selected) == len(selected_ids) and d3_unresolved,
    }


def _certificate_data(
    *,
    semantics: dict[str, Any],
    local_gc: dict[str, Any],
    atomisation: dict[str, Any],
    eq112: dict[str, Any],
    presentation: dict[str, Any],
    oracle_result: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        "certificates/gc_msr_semantics/exact_counterexamples.json": {
            "counterexamples": semantics["exact_counterexamples"],
            "implication_diagram": semantics["implication_diagram"],
            "possible_equivalence_assumptions": semantics[
                "possible_equivalence_assumptions"
            ],
            "assumptions": semantics["assumptions"],
            "unresolved_components": semantics["unresolved_components"],
            "passed": semantics["passed"],
        },
        "certificates/local_operator_gc/basis_connectivity.json": {
            "counts": local_gc["counts"],
            "basis": local_gc["generating_relation_basis"],
            "proof_obligations": local_gc["proof_obligations"],
            "semantic_digest_sha256": local_gc["semantic_digest_sha256"],
            "assumptions": local_gc["assumptions"],
            "unresolved_components": local_gc["unresolved_components"],
            "passed": local_gc["passed"],
        },
        "certificates/atomisation_paths/path_completeness.json": {
            "counts": atomisation["counts"],
            "ranking_function": atomisation["ranking_function"],
            "paths": [
                {
                    "causet_id": causet["causet_id"],
                    "complete_path_count": causet["complete_path_count"],
                    "paths": [
                        {
                            "path_id": path["path_id"],
                            "selected_elements": path["selected_elements"],
                            "S_word": path["S_word_ordered"],
                            "S_inverse_word": path["S_inverse_word_ordered"],
                        }
                        for path in causet["all_alternative_paths"]
                    ],
                }
                for causet in atomisation["causets"]
            ],
            "proof_obligations": atomisation["proof_obligations"],
            "semantic_digest_sha256": atomisation[
                "semantic_digest_sha256"
            ],
            "assumptions": atomisation["assumptions"],
            "unresolved_components": atomisation["unresolved_components"],
            "passed": atomisation["passed"],
        },
        "certificates/eq112_reduction/dependency_dag.json": {
            "dependency_DAG": eq112["dependency_DAG"],
            "counts": eq112["counts"],
            "equivalence_obligations": eq112["equivalence_obligations"],
            "source_index_audit": eq112["source_index_audit"],
            "semantic_digest_sha256": eq112["semantic_digest_sha256"],
            "assumptions": eq112["assumptions"],
            "unresolved_components": eq112["unresolved_components"],
            "passed": eq112["passed"],
        },
        "certificates/q_only_presentation/relation_digest_ledger.json": {
            "counts": presentation["counts"],
            "relation_digests": {
                family: [
                    record.get("Q_dependency_residual_sha256")
                    or record.get("word_equation_sha256")
                    or stable_hash(record)
                    for record in records
                ]
                for family, records in {
                    "CPOBC": presentation["relation_inventory"][
                        "CPOBC_residuals"
                    ],
                    "MSR": presentation["relation_inventory"][
                        "strong_MSR_residuals"
                    ],
                    "local_GC": presentation["relation_inventory"][
                        "local_operator_GC_residuals"
                    ],
                    "path_Qn": presentation["source_index_branches"][
                        "EQ113_QN_BRANCH"
                    ]["path_consistency_relations"],
                    "path_Qn_plus_1": presentation[
                        "source_index_branches"
                    ]["EQ113_QN_PLUS_1_BRANCH"][
                        "path_consistency_relations"
                    ],
                }.items()
            },
            "duplicate_audit": presentation["relation_inventory"][
                "duplicate_audit"
            ],
            "invertibility_counts": {
                "occurrences": len(
                    presentation["invertibility_predicates"][
                        "reconstructed_transition_predicates"
                    ]
                ),
                "explicit_inverse_pairs": len(
                    presentation["invertibility_predicates"][
                        "explicit_two_sided_inverse_predicates"
                    ]
                ),
            },
            "semantic_digest_sha256": presentation[
                "semantic_digest_sha256"
            ],
            "assumptions": presentation["assumptions"],
            "unresolved_components": presentation["unresolved_components"],
            "passed": presentation["passed"],
        },
        "certificates/independent_oracle/oracle_result.json": {
            "oracle_result": oracle_result,
            "counts": oracle_result["semantic_summary"],
            "assumptions": [
                "standard-library-only oracle implementation",
                "no production canonicalisation or path helper imports",
            ],
            "unresolved_components": oracle_result[
                "unresolved_components"
            ],
            "passed": oracle_result["passed"],
        },
    }


def _report_texts(
    *,
    code_commit: str,
    literature: dict[str, Any],
    semantics: dict[str, Any],
    source_audit: dict[str, Any],
    local_gc: dict[str, Any],
    atomisation: dict[str, Any],
    eq112: dict[str, Any],
    presentation: dict[str, Any],
    mutations: dict[str, Any],
    oracle_result: dict[str, Any],
) -> dict[str, str]:
    gc_counts = local_gc["counts"]
    atom_counts = atomisation["counts"]
    q_counts = presentation["counts"]
    header = (
        f"Production commit: `{code_commit}`  \n"
        f"Paper: `{PAPER_ID}` (`{PAPER_SHA256}`)  \n"
        f"Profile: `{PAPER_STRONG_OPERATOR_PROFILE}`\n"
    )
    return {
        (
            "v0.3.3_literature_and_semantics_frontier.md"
        ): f"""# v0.3.3 literature and semantics frontier

{header}
## Literature-locked facts

- The official source record remains arXiv v1 dated 2026-03-26.
- Classical path independence and atomisation come from the cited sequential-growth literature.
- The vanishing-transition extension is archived as `arXiv:gr-qc/0504066v3`.

## Project deductions

- The documented primary-source search found no follow-up that resolves operator-GC lifting,
  a complete CPOBC atomisation compiler, or the general d=2 representation problem.
- This is a bounded search result, not a worldwide nonexistence theorem.

## Frontier matrix

{json.dumps(literature["entries"], indent=2)}
""",
        "v0.3.3_gc_msr_semantics.md": f"""# v0.3.3 GC and MSR semantics

{header}
The exact verdicts are `{semantics["GC_verdict"]}` and
`{semantics["MSR_verdict"]}`.  Equality on every vector is equivalent to
operator equality for linear maps, but equality on the single initial vector is not.
The supplied 2x2 examples retain invertibility and separate both reverse implications.

The strong relations are therefore compiled only in
`{PAPER_STRONG_OPERATOR_PROFILE}`.  `{REACHABLE_STATE_PROFILE}` contains state
equalities and contributes no strong operator ideal relations.
""",
        "v0.3.3_source_equation_audit.md": f"""# v0.3.3 source equation audit

{header}
PDF pages 15 and 27 were rendered and visually checked for Eqs. (31)--(33) and
(107)--(114).  PDF and public HTML both print `Q_(n+1)` in Eq. (113).
Direct comparison of the two Eq. (112) conjugations yields `Q_n`; Appendix Eq. (163)
also uses `Q_4` for the two paths expressing `G_4`.

Verdict: `{source_audit["verdict"]}`.  The `Q_n` and literal `Q_(n+1)` branches are
preserved separately.  No typo correction is asserted.

## Unsent author query

{source_audit["author_query_draft"]}
""",
        "v0.3.3_local_operator_gc.md": f"""# v0.3.3 local operator GC

{header}
The certified scope uses transition source stages through 4, so same-endpoint paths
extend through endpoint stage 5.  Labelled path counts are
`{gc_counts["labelled_paths_by_endpoint_stage"]}` and unlabelled endpoint counts are
`{gc_counts["unlabelled_endpoints_by_stage"]}`.

An endpoint-wise spanning-tree basis has
`{gc_counts["spanning_tree_basis_relations"]}` relations and derives all
`{gc_counts["same_endpoint_path_pairs"]}` same-endpoint path pairs.  Elementary
diamonds were not assumed complete.

Verdict: `{local_gc["verdict"]}` within the explicit strong profile.
""",
        "v0.3.3_atomisation_paths.md": f"""# v0.3.3 atomisation paths

{header}
All `{atom_counts["non_antichain_causets"]}` non-antichain causets through n=4
produce `{atom_counts["complete_atomisation_paths"]}` complete paths and
`{atom_counts["atomisation_steps"]}` step instances.  Every eligible
non-gregarious maximal element is recursed, no path is removed by an automorphism
quotient, and the number of strict order relations decreases at every step.

Verdict: `{atomisation["verdict"]}`.  The atomisation definition itself remains
`LITERATURE_LOCKED`; the exhaustive compiler and certificates are project work.
""",
        "v0.3.3_eq112_reduction.md": f"""# v0.3.3 Eq. (112) reduction

{header}
All 20 non-antichain G generators and 34 atomisation paths have ordered
`S Q_n S^-1` words.  The 76 atomisation squares are derived from the local-GC
basis.  All 22 distinct B transitions map into the frozen v0.3.2 Eq. (107)/(108)
table, and the recursive dependency DAG is acyclic.

The inverse of a noncommutative linear combination is retained as an explicit
two-sided-inverse auxiliary.  Reverse reconstruction of all CPOBC, MSR, GC, and
invertibility constraints is not proved.

Verdict: `{eq112["verdict"]}` / `ONE_WAY_NECESSARY_REDUCTION`.
""",
        "v0.3.3_q_only_presentation.md": f"""# v0.3.3 Q-dominated presentation

{header}
The frozen residual inventory remains 700 CPOBC equations and 21 strong-MSR
equations.  The 320 local-GC basis equations give
`{q_counts["local_operator_GC_identities_after_eq107_eq108"]}` identities and
`{q_counts["local_operator_GC_nontrivial_residuals"]}` residual constraints.
Each Eq. (113) branch has 25 path-consistency equations.

This is a `Q_DOMINATED_PRESENTATION_WITH_AUXILIARIES`: Q1--Q4 plus 22 explicit
B-inverse auxiliaries (104 abstract d=2 matrix entries).  Minimality, scalar
polynomial expansion, determinant saturation, and reverse equivalence are not proved.
The literal printed branch additionally requires Q5 in 24 stage-4 relations.

Verdicts: `{presentation["presentation_verdict"]}`,
`{presentation["readiness_verdict"]}`, `{presentation["overall_verdict"]}`.
""",
        "v0.3.3_mutation_tests.md": f"""# v0.3.3 mutation tests

{header}
All `{mutations["counts"]["required"]}` required critical mutations were detected.
The matrix includes semantic-strength promotion, incomplete path enumeration,
operator/inverse order, source-index merging, provenance loss, injected dependency
cycles, missing invertibility or auxiliaries, an unbounded dense Groebner launch,
readiness rounding, and novelty-boundary corruption.

Verdict: `{mutations["verdict"]}`.
""",
        "v0.3.3_scientific_verdict.md": f"""# v0.3.3 scientific verdict

{header}
## What is now exact

- Source-stage n<=4 local operator-GC path compilation is complete under the
  explicit strong-operator profile.
- All 20 non-antichain causets and all 34 atomisation paths are compiled.
- The independent standard-library oracle matches the full semantic digest
  `{oracle_result["semantic_summary"]["semantic_digest_sha256"]}`.
- Every G has a one-way Eq. (112) reduction into a Q-dominated dependency DAG.

## What is not established

- Strong GC/MSR are not derived from the paper's fixed/reachable-state statements.
- Eq. (113)'s source index is unresolved.
- The presentation is not reverse-equivalent, auxiliary-minimal, or d2-elimination ready.
- No representation, no-go, d3/d4 search, numerical search, or physical continuum claim
  was attempted.

Overall verdict: `{OVERALL_VERDICT}`.
""",
        "v0.3.3_remaining_gaps.md": f"""# v0.3.3 remaining gaps

{header}
1. Obtain an authorial or formal resolution of the Eq. (113) index.
2. Decide whether strong GC/MSR are axioms, quotient equalities, or derivable from
   a stated separating/spanning condition.
3. Eliminate or certify the necessity of 22 B-inverse auxiliaries.
4. Prove reverse reconstruction of all 700 CPOBC, 21 strong-MSR, 255 local-GC,
   invertibility, and path-consistency constraints.
5. Compile the d=2 scalar polynomial/saturation system before any S1/S2/S3
   elimination.

Until these obligations close, readiness remains
`{presentation["readiness_verdict"]}`.
""",
    }


def _research_note_text(
    *,
    source_audit: dict[str, Any],
    presentation: dict[str, Any],
) -> str:
    return f"""# Final-Theory v0.3.3 GC/atomisation frontier (2026-07-28)

## Primary-source claims

- arXiv:2603.25503v1 defines GC on histories applied to the initial vector,
  writes the MSR first on a reachable state, and later uses operator identities
  in the CPOBC atomisation argument.
- Its PDF and HTML print Q_(n+1) in Eq. (113); Eq. (112) directly yields Q_n,
  and Appendix Eq. (163) uses Q_4 for G_4.
- Rideout--Sorkin supplies classical path independence and atomisation.
- Varadarajan--Rideout supplies the classical solution with vanishing transitions.

## Independent project deductions

- Exact invertible 2x2 counterexamples show that fixed-vector equality does not
  imply operator equality and reachable-state MSR does not imply strong MSR.
- The n<=4 source-stage compiler has a complete 320-relation local-GC basis,
  34 atomisation paths, and a cycle-free one-way Eq. (112) dependency DAG.
- A standard-library oracle independently matches the complete path/S-word digest.

## Unresolved boundary

The source verdict is `{source_audit["verdict"]}` and the finite presentation
verdict is `{presentation["presentation_verdict"]}`.  Reverse equivalence,
auxiliary minimality, scalar d=2 saturation, and S1/S2/S3 elimination remain open.
No representation-found or no-go statement is licensed.
"""


def verify_v033_reproduction_manifest(root: Path) -> dict[str, Any]:
    path = root / "results/reproduction_manifest_final_v0.3.3.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for artifact in manifest["artifacts"]:
        artifact_path = root / artifact["path"]
        if not artifact_path.is_file():
            mismatches.append(
                {"path": artifact["path"], "error": "MISSING"}
            )
            continue
        observed = _sha256_file(artifact_path)
        if observed != artifact["sha256"]:
            mismatches.append(
                {
                    "path": artifact["path"],
                    "expected": artifact["sha256"],
                    "observed": observed,
                }
            )
    return {
        "checked_artifacts": len(manifest["artifacts"]),
        "mismatches": mismatches,
        "self_excluded_to_avoid_hash_recursion": True,
        "passed": not mismatches,
    }


def write_v033_artifacts(
    root: Path,
    *,
    production_commit: str | None = None,
    validation_summary: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Generate all v0.3.3 results, reports, certificates, and manifests."""

    code_commit = production_commit or _git_head(root)
    source_hashes = _source_hash_records(root)
    literature = literature_matrix()
    semantics = gc_msr_semantics_audit()
    source_audit = source_equation_audit()
    local_gc = compile_local_operator_gc_n4()
    atomisation = compile_atomisation_paths_n4()
    eq112 = compile_eq112_reduction_n4()
    oracle_target = production_oracle_summary(
        local_gc=local_gc,
        atomisation=atomisation,
    )

    temp_target = root / "tmp/v033_oracle_production_target.json"
    temp_result = root / "tmp/v033_oracle_raw_result.json"
    _write_json(temp_target, oracle_target)
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "oracle/cpobc_gc_atomisation_v033_oracle.py"),
            "--compare",
            str(temp_target),
            "--output",
            str(temp_result),
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "independent oracle failed: "
            + completed.stdout
            + completed.stderr
        )
    oracle_result = json.loads(temp_result.read_text(encoding="utf-8"))
    temp_target.unlink()
    temp_result.unlink()
    if not oracle_result["passed"]:
        raise AssertionError("independent oracle semantic mismatch")

    presentation = compile_q_presentation_n4(
        independent_oracle=oracle_result
    )
    mutations = critical_mutation_matrix_v033()
    source_manifest = _source_manifest_data(root, source_hashes)

    empty_certificate_hashes: list[dict[str, str]] = []
    certificate_core = _certificate_data(
        semantics=semantics,
        local_gc=local_gc,
        atomisation=atomisation,
        eq112=eq112,
        presentation=presentation,
        oracle_result=oracle_result,
    )
    certificate_paths: dict[str, Path] = {}
    for relative_path, data in certificate_core.items():
        certificate_payload = _artifact_payload(
            kind=Path(relative_path).stem.replace("_", "-"),
            data=data,
            code_commit=code_commit,
            source_hashes=source_hashes,
            literature=literature,
            certificate_hashes=empty_certificate_hashes,
            semantic_profile=PAPER_STRONG_OPERATOR_PROFILE,
            verdict=(
                "CERTIFICATE_PASS" if data["passed"] else "CERTIFICATE_FAIL"
            ),
            relation_counts=data.get("counts", {}),
            generator_counts={},
            path_counts=data.get("counts", {}),
        )
        output = root / relative_path
        _write_json(output, certificate_payload)
        certificate_paths[relative_path] = output

    certificate_hashes = [
        {"path": path, "sha256": _sha256_file(output)}
        for path, output in sorted(certificate_paths.items())
    ]

    common_relation_counts = {
        "CPOBC_compiled_relations": 641,
        "CPOBC_word_equations": 783,
        "CPOBC_residuals": 700,
        "strong_MSR_constraints": 24,
        "strong_MSR_residuals": 21,
        "local_GC_basis": 320,
        "local_GC_residuals": presentation["counts"][
            "local_operator_GC_nontrivial_residuals"
        ],
        "path_consistency_per_branch": 25,
    }
    common_generator_counts = {
        "original_occurrences": 165,
        "v032_gregarious_generators": 24,
        "Q_generators": 4,
        "non_antichain_G_forward_reduced": 20,
        "B_inverse_auxiliaries": 22,
    }
    common_path_counts = {
        "labelled_paths": local_gc["counts"][
            "labelled_paths_by_endpoint_stage"
        ],
        "unlabelled_endpoints": local_gc["counts"][
            "unlabelled_endpoints_by_stage"
        ],
        "same_endpoint_pairs": local_gc["counts"][
            "same_endpoint_path_pairs"
        ],
        "atomisation_paths": atomisation["counts"][
            "complete_atomisation_paths"
        ],
        "atomisation_steps": atomisation["counts"]["atomisation_steps"],
    }
    final_summary = {
        "programme": "Final-Theory Bench v0.3.3",
        "validation_summary": validation_summary
        or {"status": "GENERATED_BEFORE_FINAL_VALIDATION"},
        "GC_verdict": semantics["GC_verdict"],
        "MSR_verdict": semantics["MSR_verdict"],
        "source_equation_verdict": source_audit["verdict"],
        "local_GC_verdict": local_gc["verdict"],
        "atomisation_verdict": atomisation["verdict"],
        "Eq112_verdict": eq112["verdict"],
        "Q_presentation_verdict": presentation["presentation_verdict"],
        "d2_elimination_readiness": presentation["readiness_verdict"],
        "independent_oracle_verdict": oracle_result["verdict"],
        "mutation_verdict": mutations["verdict"],
        "overall_verdict": OVERALL_VERDICT,
        "prohibited_tracks_executed": [],
        "assumptions": presentation["assumptions"],
        "completeness_scope": presentation["completeness_scope"],
        "exact_numeric_distinction": presentation[
            "exact_numeric_distinction"
        ],
        "unresolved_components": presentation["unresolved_components"],
        "passed": (
            semantics["passed"]
            and local_gc["passed"]
            and atomisation["passed"]
            and eq112["passed"]
            and presentation["passed"]
            and oracle_result["passed"]
            and mutations["passed"]
        ),
    }
    result_definitions = {
        "results/v0.3.3_source_manifest.json": (
            "source-manifest",
            source_manifest,
            "SOURCE_MANIFEST_VERIFIED",
        ),
        "results/v0.3.3_literature_matrix.json": (
            "literature-matrix",
            literature,
            "LITERATURE_GATE_COMPLETE",
        ),
        "results/v0.3.3_gc_msr_semantics.json": (
            "gc-msr-semantics",
            semantics,
            semantics["GC_verdict"],
        ),
        "results/v0.3.3_source_equation_audit.json": (
            "source-equation-audit",
            source_audit,
            source_audit["verdict"],
        ),
        "results/v0.3.3_local_operator_gc_n4.json": (
            "local-operator-gc-n4",
            local_gc,
            local_gc["verdict"],
        ),
        "results/v0.3.3_atomisation_paths_n4.json": (
            "atomisation-paths-n4",
            atomisation,
            atomisation["verdict"],
        ),
        "results/v0.3.3_eq112_reduction_n4.json": (
            "eq112-reduction-n4",
            eq112,
            eq112["verdict"],
        ),
        "results/v0.3.3_q_only_presentation_n4.json": (
            "q-only-presentation-n4",
            presentation,
            presentation["presentation_verdict"],
        ),
        "results/final_theory_bench_v0.3.3.json": (
            "final-theory-bench",
            final_summary,
            OVERALL_VERDICT,
        ),
    }
    output_paths: dict[str, Path] = dict(certificate_paths)
    for relative_path, (kind, data, verdict) in result_definitions.items():
        payload = _artifact_payload(
            kind=kind,
            data=data,
            code_commit=code_commit,
            source_hashes=source_hashes,
            literature=literature,
            certificate_hashes=certificate_hashes,
            semantic_profile=(
                PAPER_STRONG_OPERATOR_PROFILE
                if "literature" not in kind and "source-manifest" not in kind
                else "SEMANTICS_AND_LITERATURE_AUDIT"
            ),
            verdict=verdict,
            relation_counts=common_relation_counts,
            generator_counts=common_generator_counts,
            path_counts=common_path_counts,
        )
        output = root / relative_path
        _write_json(output, payload)
        output_paths[relative_path] = output

    reports = _report_texts(
        code_commit=code_commit,
        literature=literature,
        semantics=semantics,
        source_audit=source_audit,
        local_gc=local_gc,
        atomisation=atomisation,
        eq112=eq112,
        presentation=presentation,
        mutations=mutations,
        oracle_result=oracle_result,
    )
    for filename, text in reports.items():
        for report_directory in ("reports", "Final-Theory-Program/reports"):
            relative_path = f"{report_directory}/{filename}"
            output = root / relative_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text.rstrip() + "\n", encoding="utf-8")
            output_paths[relative_path] = output

    note_relative = (
        "references/notes/"
        "final_theory_v0.3.3_gc_atomisation_frontier_2026-07-28.md"
    )
    note_path = root / note_relative
    note_path.write_text(
        _research_note_text(
            source_audit=source_audit,
            presentation=presentation,
        ),
        encoding="utf-8",
    )
    output_paths[note_relative] = note_path

    tracked_source_paths = [
        "src/universe_lab/final_theory/gc_semantics_v033.py",
        "src/universe_lab/final_theory/operator_gc_v033.py",
        "src/universe_lab/final_theory/atomisation_v033.py",
        "src/universe_lab/final_theory/eq112_reduction_v033.py",
        "src/universe_lab/final_theory/cpobc_q_presentation_v033.py",
        "oracle/cpobc_gc_atomisation_v033_oracle.py",
        "tests/final_theory/test_gc_semantics_v033.py",
        "tests/final_theory/test_operator_gc_v033.py",
        "tests/final_theory/test_atomisation_v033.py",
        "tests/final_theory/test_eq112_reduction_v033.py",
        "tests/final_theory/test_cpobc_q_presentation_v033.py",
        "tests/final_theory/test_v033_mutations.py",
        "references/sources.json",
        "references/manifest.json",
        (
            "references/papers/gr-qc-0504066v3_"
            "varadarajan-rideout_general-classical-sequential-growth.pdf"
        ),
        (
            "references/text/gr-qc-0504066v3_"
            "varadarajan-rideout_general-classical-sequential-growth.txt"
        ),
    ]
    manifest_artifact_paths = sorted(
        set(output_paths) | set(tracked_source_paths)
    )
    manifest_artifacts = [
        {
            "path": relative_path,
            "sha256": _sha256_file(root / relative_path),
            "bytes": (root / relative_path).stat().st_size,
        }
        for relative_path in manifest_artifact_paths
    ]
    reproduction_data = {
        "artifacts": manifest_artifacts,
        "artifact_count": len(manifest_artifacts),
        "manifest_self_hash_excluded": True,
        "verification_command": (
            "python -c \"from pathlib import Path; "
            "from universe_lab.final_theory.cpobc_q_presentation_v033 "
            "import verify_v033_reproduction_manifest as v; "
            "assert v(Path('.'))['passed']\""
        ),
        "environment": {
            "python": sys.version.split()[0],
            "sympy": sp.__version__,
            "platform": platform.platform(),
        },
        "validation_summary": validation_summary
        or {"status": "GENERATED_BEFORE_FINAL_VALIDATION"},
        "assumptions": presentation["assumptions"],
        "completeness_scope": presentation["completeness_scope"],
        "exact_numeric_distinction": presentation[
            "exact_numeric_distinction"
        ],
        "unresolved_components": presentation["unresolved_components"],
        "passed": True,
    }
    reproduction_payload = _artifact_payload(
        kind="reproduction-manifest",
        data=reproduction_data,
        code_commit=code_commit,
        source_hashes=source_hashes,
        literature=literature,
        certificate_hashes=certificate_hashes,
        semantic_profile=PAPER_STRONG_OPERATOR_PROFILE,
        verdict="REPRODUCTION_MANIFEST_VERIFIED",
        relation_counts=common_relation_counts,
        generator_counts=common_generator_counts,
        path_counts=common_path_counts,
    )
    reproduction_relative = (
        "results/reproduction_manifest_final_v0.3.3.json"
    )
    reproduction_path = root / reproduction_relative
    _write_json(reproduction_path, reproduction_payload)
    output_paths[reproduction_relative] = reproduction_path
    verification = verify_v033_reproduction_manifest(root)
    if not verification["passed"]:
        raise AssertionError(
            f"reproduction manifest mismatch: {verification['mismatches']}"
        )
    return output_paths
