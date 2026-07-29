"""Exact v0.3.7 scalar-chain evaluation for both Eq.(113) branches."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_sage_backend_v035 import (
    DEFAULT_COMPACT_ARENA_PATH,
    _result_semantic_digest,
    build_chart_payload,
    run_sage_request,
)
from universe_lab.final_theory.d2_strata_v034 import stratum_charts
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.q5_free_elimination_v037 import (
    BUDGET_PATH,
    DIRECT_SYSTEM_PATH,
    SYSTEM_PATH,
    _memory_limit_matches_request,
    _result_wall_time_seconds,
    load_human_budget_v037,
)

BRANCH = "codex/final-theory-v0.3.7-publication-20260729"
SCHEMA_RESPONSE = "final-theory-scalar-chain-response-v0.3.7"
SCHEMA_LEMMA = "final-theory-general-scalar-chain-fiber-v0.3.7"
RESULT_PATH = "results/v0.3.7_general_scalar_chain_fiber.json"
CERTIFICATE_ROOT = "certificates/d2_saturation/scalar_chain_v037"
LEMMA = "LEMMA_GENERAL_SCALAR_CHAIN_FIBER_EXACT"
EXPECTED_RELATION_FAMILY_COUNTS = {
    "CPOBC": 700,
    "EQ112_PATH_CONSISTENCY": 25,
    "LOCAL_OPERATOR_GC": 255,
    "STRONG_OPERATOR_MSR": 21,
}
EXPECTED_CANONICAL_PROVENANCE_FAMILY_COUNTS = {
    "CPOBC": 700,
    "EQ112_PATH_CONSISTENCY": 3,
    "LOCAL_OPERATOR_GC": 255,
    "STRONG_OPERATOR_MSR": 21,
}
DIRECT_ROUTE = "direct_operator"
CANONICAL_ROUTE = "compact_arena"


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


def _request_semantic_digest(request: dict[str, Any]) -> str:
    return stable_hash(
        {
            key: value
            for key, value in request.items()
            if key
            not in {
                "request_id",
                "request_semantic_digest_sha256",
            }
        }
    )


def _base_scalar_chain_request(expression_source: str) -> dict[str, Any]:
    chart = next(chart for chart in stratum_charts(DERIVED_BRANCH) if chart.stratum == "S3_SCALAR")
    return build_chart_payload(
        DERIVED_BRANCH,
        chart.chart_id,
        coefficient_modulus=0,
        operation="compile",
        maximum_source_stage=4,
        saturation=False,
        check_noncommutativity=False,
        factor_denominators=True,
        expression_source=expression_source,
        include_all_transition_predicates=True,
        groebner_algorithm="libsingular:slimgb",
        groebner_strategy="none",
        progressive_batch_size=4,
        saturation_factor_order="forward",
    )


def _branch_relation_digest(
    direct: dict[str, Any],
    branch: str,
) -> str:
    return stable_hash(sorted(record["relation_id"] for record in direct["relations"][branch]))


def _branch_evaluated_relation_digest(
    direct: dict[str, Any],
    branch: str,
) -> str:
    return stable_hash([record["relation_id"] for record in direct["relations"][branch]])


def _branch_equation_digests(
    systems: dict[str, Any],
    branch: str,
) -> tuple[str, str]:
    equations = systems["systems"][branch]["equations"]
    return (
        stable_hash(sorted(record["equation_id"] for record in equations)),
        stable_hash(sorted(record["canonical_expression_id"] for record in equations)),
    )


def build_scalar_chain_request_v037(
    root: Path,
    branch: str,
    budget: dict[str, Any],
    *,
    expression_source: str = DIRECT_ROUTE,
) -> dict[str, Any]:
    """Build the seven- or eleven-variable exact identity request."""

    if branch not in {DERIVED_BRANCH, LITERAL_BRANCH}:
        raise ValueError(f"unknown source-index branch: {branch}")
    if expression_source not in {DIRECT_ROUTE, CANONICAL_ROUTE}:
        raise ValueError(f"unknown scalar-chain expression source: {expression_source}")
    direct = _load_json(root / DIRECT_SYSTEM_PATH)
    systems = _load_json(root / SYSTEM_PATH)
    request = _base_scalar_chain_request(expression_source)
    equation_digest, expression_digest = _branch_equation_digests(
        systems,
        branch,
    )
    direct_route = expression_source == DIRECT_ROUTE
    request.update(
        {
            "response_schema_version": SCHEMA_RESPONSE,
            "chart": (
                "GENERAL_SCALAR_CHAIN_LITERAL_Q5_FIBER"
                if branch == LITERAL_BRANCH
                else "GENERAL_SCALAR_CHAIN_DERIVED_BASE"
            ),
            "chart_cover_id": ("SYMBOLIC_SCALAR_CHAIN_NOT_A_COVER_CHART"),
            "chart_source_index_branch": DERIVED_BRANCH,
            "equation_source_index_branch": branch,
            "source_index_branch": branch,
            "selection_label": (
                "ALL_1001_DIRECT_MATRIX_RELATIONS_ACTUAL"
                if direct_route
                else "ALL_2564_CANONICAL_NUMERATORS_ACTUAL"
            ),
            "selection_certificate": (DIRECT_SYSTEM_PATH if direct_route else SYSTEM_PATH),
            "selection_certificate_semantic_digest_sha256": (
                direct["semantic_digest_sha256"]
                if direct_route
                else systems["semantic_digest_sha256"]
            ),
            "expected_selected_relation_count": (1001 if direct_route else 979),
            "expected_selected_relation_ids_sha256": (
                _branch_relation_digest(direct, branch) if direct_route else None
            ),
            "expected_evaluated_relation_ids_sha256": (
                _branch_evaluated_relation_digest(direct, branch) if direct_route else None
            ),
            "expected_relation_family_counts": (
                EXPECTED_RELATION_FAMILY_COUNTS
                if direct_route
                else EXPECTED_CANONICAL_PROVENANCE_FAMILY_COUNTS
            ),
            "expected_selected_canonical_equation_count": 2564,
            "expected_selected_equation_ids_sha256": equation_digest,
            "expected_selected_expression_ids_sha256": expression_digest,
            "expected_frozen_denominator_factor_count": 191,
            "memory_limit_bytes": budget["memory_limit_bytes"],
            "budget_file": BUDGET_PATH,
            "budget_file_sha256": budget["sha256"],
            "authorised_timeout_seconds_per_run": budget["timeout_seconds_per_chart"],
            "authorised_total_wall_time_seconds": budget["total_wall_time_seconds"],
        }
    )
    if direct_route:
        request["canonical_ideal_equivalence_certified"] = False
        request["expected_reconstructed_transition_count"] = 165
        request["expected_direct_system_file_sha256"] = _sha256(root / DIRECT_SYSTEM_PATH)
        request["expected_direct_system_semantic_digest_sha256"] = direct["semantic_digest_sha256"]
        for name in (
            "expected_selected_canonical_equation_count",
            "expected_selected_equation_ids_sha256",
            "expected_selected_expression_ids_sha256",
            "expected_frozen_denominator_factor_count",
        ):
            request.pop(name, None)
    if branch == LITERAL_BRANCH:
        request["q_substitutions"].update(
            {
                "q5_11": "e",
                "q5_12": "f",
                "q5_21": "g",
                "q5_22": "h",
            }
        )
        request["variables"] = [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "l2",
            "l3",
            "l4",
        ]
        request["chart_nonzero_conditions"].append("e*h - f*g")
    else:
        request["variables"] = [
            "a",
            "b",
            "c",
            "d",
            "l2",
            "l3",
            "l4",
        ]
    expected_q_indices = {1, 2, 3, 4}
    if branch == LITERAL_BRANCH:
        expected_q_indices.add(5)
    actual_q_indices = {int(name.split("_", 1)[0][1:]) for name in request["q_substitutions"]}
    if actual_q_indices != expected_q_indices:
        raise RuntimeError(f"scalar-chain generator inventory changed: {actual_q_indices}")
    request["request_semantic_digest_sha256"] = _request_semantic_digest(request)
    return request


def _certificate_path(
    root: Path,
    branch: str,
    expression_source: str,
    request: dict[str, Any],
) -> Path:
    label = "literal" if branch == LITERAL_BRANCH else "derived"
    route = "direct" if expression_source == DIRECT_ROUTE else "canonical"
    budget = request["budget_file_sha256"][:16]
    digest = request["request_semantic_digest_sha256"][:24]
    return root / CERTIFICATE_ROOT / f"budget-{budget}" / f"{label}_{route}_{digest}.json"


def _valid_direct_identity_result(
    result: dict[str, Any],
    request: dict[str, Any],
) -> bool:
    return bool(
        result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("exit_status") == "COMPLETED"
        and result.get("coefficient_field") == "QQ"
        and result.get("identity_proof_eligible") is True
        and result.get("proof_eligible") is False
        and result.get("source_index_branch") == request["source_index_branch"]
        and result.get("equation_source_index_branch") == request["equation_source_index_branch"]
        and result.get("variables") == request["variables"]
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and result.get("selection_certificate") == request["selection_certificate"]
        and result.get("selection_certificate_semantic_digest_sha256")
        == request["selection_certificate_semantic_digest_sha256"]
        and result.get("time_limit_seconds", 0) > 0
        and result.get("time_limit_seconds") <= request["authorised_timeout_seconds_per_run"]
        and result.get("expression_source") == "DIRECT_REDUCED_OPERATOR_WORDS"
        and result.get("selection_label") == "ALL_1001_DIRECT_MATRIX_RELATIONS_ACTUAL"
        and result.get("selected_matrix_relation_count") == 1001
        and result.get("relations_evaluated_count") == 1001
        and result.get("selected_relation_ids_sha256")
        == request["expected_selected_relation_ids_sha256"]
        and result.get("evaluated_relation_ids_sha256")
        == request["expected_evaluated_relation_ids_sha256"]
        and result.get("direct_system_path") == DIRECT_SYSTEM_PATH
        and result.get("direct_system_file_sha256") == request["expected_direct_system_file_sha256"]
        and result.get("direct_system_semantic_digest_sha256")
        == request["expected_direct_system_semantic_digest_sha256"]
        and result.get("direct_system_self_semantic_digest_valid") is True
        and result.get("selected_relation_family_counts") == EXPECTED_RELATION_FAMILY_COUNTS
        and result.get("relation_selection_checks_passed") is True
        and result.get("nonzero_specialised_equation_count") == 0
        and result.get("all_transition_predicates_requested") is True
        and result.get("reconstructed_transitions_checked") == 165
        and result.get("zero_required_factor") is False
        and result.get("factor_reduction_equivalence", {}).get(
            "all_source_factorisations_reconstructed_exactly"
        )
        is True
        and result.get("resource_usage", {}).get("memory_budget_satisfied") is True
        and _memory_limit_matches_request(result, request)
        and result.get("chart_verdict") == "SPECIALISATION_ONLY_NO_IDEAL_SOLVE"
    )


def _valid_canonical_identity_result(
    result: dict[str, Any],
    request: dict[str, Any],
) -> bool:
    return bool(
        result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("exit_status") == "COMPLETED"
        and result.get("coefficient_field") == "QQ"
        and result.get("identity_proof_eligible") is True
        and result.get("source_index_branch") == request["source_index_branch"]
        and result.get("equation_source_index_branch") == request["equation_source_index_branch"]
        and result.get("variables") == request["variables"]
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and result.get("time_limit_seconds", 0) > 0
        and result.get("time_limit_seconds") <= request["authorised_timeout_seconds_per_run"]
        and result.get("expression_source") == "FROZEN_COMPACT_EXPRESSION_ARENA"
        and result.get("selection_label") == "ALL_2564_CANONICAL_NUMERATORS_ACTUAL"
        and result.get("selected_canonical_equation_count") == 2564
        and result.get("zero_specialised_equation_count") == 2564
        and result.get("nonzero_specialised_canonical_equation_count") == 0
        and result.get("nonzero_specialised_equation_count") == 0
        and result.get("equation_deduplication_count") == 0
        and result.get("selected_equation_ids_sha256")
        == request["expected_selected_equation_ids_sha256"]
        and result.get("selected_expression_ids_sha256")
        == request["expected_selected_expression_ids_sha256"]
        and result.get("selected_matrix_relation_count") == 979
        and result.get("selected_relation_family_counts")
        == EXPECTED_CANONICAL_PROVENANCE_FAMILY_COUNTS
        and result.get("selected_denominator_record_count") == 191
        and result.get("canonical_selection_checks_passed") is True
        and result.get("zero_required_factor") is False
        and result.get("factor_reduction_equivalence", {}).get(
            "all_source_factorisations_reconstructed_exactly"
        )
        is True
        and result.get("resource_usage", {}).get("memory_budget_satisfied") is True
        and _memory_limit_matches_request(result, request)
        and result.get("chart_verdict") == "SPECIALISATION_ONLY_NO_IDEAL_SOLVE"
    )


def _bound_terminal_result(
    result: dict[str, Any],
    request: dict[str, Any],
) -> bool:
    """Accept a same-request terminal record for budget accounting only."""

    return bool(
        result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("chart") == request["chart"]
        and result.get("coefficient_field") == "QQ"
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and isinstance(result.get("exit_status"), str)
    )


@lru_cache(maxsize=4)
def _coverage_certificate(root: Path, branch: str) -> dict[str, Any]:
    direct_path = root / DIRECT_SYSTEM_PATH
    system_path = root / SYSTEM_PATH
    arena_path = root / DEFAULT_COMPACT_ARENA_PATH
    direct = _load_json(direct_path)
    systems = _load_json(system_path)
    with gzip.open(arena_path, "rt", encoding="utf-8") as handle:
        arena = json.load(handle)
    coverage = direct["relation_to_scalar_equation_coverage"][branch]
    relations = direct["relations"][branch]
    relation_by_id = {record["relation_id"]: record for record in relations}
    equations = systems["systems"][branch]["equations"]
    equation_ids = [record["equation_id"] for record in equations]
    canonical_expression_ids = [record["canonical_expression_id"] for record in equations]
    provenance_records: list[dict[str, Any]] = []
    provenance_errors: list[str] = []
    relation_entries: dict[str, set[tuple[int, int]]] = {}
    for equation in equations:
        equation_original_expression_ids: set[str] = set()
        if not equation["provenance"]:
            provenance_errors.append(f"equation has no provenance: {equation['equation_id']}")
        for provenance in equation["provenance"]:
            relation_id = provenance["relation_id"]
            relation = relation_by_id.get(relation_id)
            relation_provenance = provenance.get("relation_provenance")
            relation_provenance_digest = (
                relation_provenance.get(
                    "v033_Q_dependency_residual_sha256",
                    relation_provenance.get("word_equation_sha256"),
                )
                if isinstance(relation_provenance, dict)
                else None
            )
            raw_matrix_entry = provenance["matrix_entry"]
            if len(raw_matrix_entry) != 2:
                provenance_errors.append(f"invalid matrix-entry length: {relation_id}")
                continue
            matrix_entry = (
                int(raw_matrix_entry[0]),
                int(raw_matrix_entry[1]),
            )
            if relation is None:
                provenance_errors.append(f"unknown relation: {relation_id}")
            else:
                if provenance["family"] != relation["family"]:
                    provenance_errors.append(f"family mismatch: {relation_id}")
                if int(provenance["source_stage"]) != int(relation["source_stage"]):
                    provenance_errors.append(f"stage mismatch: {relation_id}")
                direct_v033_digest = relation.get("provenance", {}).get("v033_digest")
                if (
                    not isinstance(relation_provenance_digest, str)
                    or relation_provenance_digest != direct_v033_digest
                ):
                    provenance_errors.append(f"v0.3.3 provenance mismatch: {relation_id}")
            expected_source_index_branch = (
                branch if provenance["family"] == "EQ112_PATH_CONSISTENCY" else "SHARED_CORE"
            )
            if provenance["source_index_branch"] != expected_source_index_branch:
                provenance_errors.append(f"branch mismatch: {relation_id}")
            if matrix_entry not in {
                (0, 0),
                (0, 1),
                (1, 0),
                (1, 1),
            }:
                provenance_errors.append(f"invalid matrix entry: {relation_id}")
            relation_entries.setdefault(relation_id, set()).add(matrix_entry)
            equation_original_expression_ids.add(provenance["original_expression_id"])
            provenance_records.append(
                {
                    "equation_id": equation["equation_id"],
                    "canonical_expression_id": equation["canonical_expression_id"],
                    "relation_id": relation_id,
                    "family": provenance["family"],
                    "source_stage": int(provenance["source_stage"]),
                    "matrix_entry": list(matrix_entry),
                    "original_expression_id": provenance["original_expression_id"],
                    "relation_provenance_digest_sha256": (relation_provenance_digest),
                }
            )
        if equation.get("representative_expression_id") not in equation_original_expression_ids:
            provenance_errors.append(
                "representative expression is not one of the "
                f"provenance originals: {equation['equation_id']}"
            )
    direct_relation_ids = set(relation_by_id)
    represented_relation_ids = set(relation_entries)
    zero_path_relation_ids = set(coverage["identically_zero_path_relation_ids"])
    zero_path_relations_are_exact_path_family = all(
        relation_by_id.get(relation_id, {}).get("family") == "EQ112_PATH_CONSISTENCY"
        for relation_id in zero_path_relation_ids
    )
    expected_entries = {(0, 0), (0, 1), (1, 0), (1, 1)}
    represented_relations_have_all_entries = all(
        entries == expected_entries for entries in relation_entries.values()
    )
    arena_target_indices = arena.get("target_indices", {})
    arena_targets = set(arena_target_indices) if isinstance(arena_target_indices, dict) else set()
    referenced_expression_ids = set(canonical_expression_ids)
    arena_reference_complete = referenced_expression_ids <= arena_targets
    direct_source_path = root / direct.get("source_artifact", "")
    direct_source_binding_valid = bool(
        direct.get("schema_version") == "final-theory-d2-direct-operator-system-v0.3.5"
        and direct.get("passed") is True
        and direct_source_path.is_file()
        and direct.get("source_artifact_sha256") == _sha256(direct_source_path)
    )
    system_binding_valid = bool(
        systems.get("schema_version") == "final-theory-d2-localisation-v0.3.4"
        and systems.get("passed") is True
    )
    arena_nodes = arena.get("nodes", [])
    arena_counts_consistent = bool(
        isinstance(arena_nodes, list)
        and isinstance(arena_target_indices, dict)
        and arena.get("node_count") == len(arena_nodes)
        and arena.get("target_count") == len(arena_target_indices)
    )
    arena_target_indices_valid = bool(
        isinstance(arena_nodes, list)
        and isinstance(arena_target_indices, dict)
        and all(
            isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(arena_nodes)
            for index in arena_target_indices.values()
        )
    )
    arena_source_binding_valid = bool(
        arena.get("schema_version") == "final-theory-d2-compact-solver-arena-v0.3.5"
        and arena.get("source_artifact") == SYSTEM_PATH
        and arena.get("source_artifact_sha256") == _sha256(system_path)
    )
    passed = bool(
        direct_source_binding_valid
        and system_binding_valid
        and arena_source_binding_valid
        and arena_counts_consistent
        and arena_target_indices_valid
        and direct["counts"]["relations"].get(branch) == 1001
        and direct["counts"]["reconstructed_transition_predicates"] == 165
        and direct["counts"]["explicit_inverse_sites"] == 26
        and coverage.get("passed")
        and coverage.get("direct_matrix_relation_count") == 1001
        and coverage.get("relations_represented_in_nonzero_scalar_numerators") == 979
        and coverage.get("identically_zero_path_relation_count") == 22
        and len(coverage.get("identically_zero_path_relation_ids", [])) == 22
        and coverage.get("frozen_canonical_scalar_numerator_count") == 2564
        and coverage.get("all_frozen_provenance_relation_ids_covered") is True
        and len(relations) == 1001
        and len(relation_by_id) == 1001
        and len(equations) == 2564
        and len(set(equation_ids)) == 2564
        and len(set(canonical_expression_ids)) == 2564
        and len(provenance_records) == 3916
        and not provenance_errors
        and len(represented_relation_ids) == 979
        and represented_relation_ids == direct_relation_ids - zero_path_relation_ids
        and len(zero_path_relation_ids) == 22
        and zero_path_relations_are_exact_path_family
        and represented_relations_have_all_entries
        and arena_reference_complete
    )
    return {
        "path": DIRECT_SYSTEM_PATH,
        "sha256": _sha256(direct_path),
        "semantic_digest_sha256": direct["semantic_digest_sha256"],
        "system_path": SYSTEM_PATH,
        "system_sha256": _sha256(system_path),
        "compact_arena_path": DEFAULT_COMPACT_ARENA_PATH,
        "compact_arena_sha256": _sha256(arena_path),
        "direct_source_artifact": direct["source_artifact"],
        "direct_source_artifact_sha256": direct["source_artifact_sha256"],
        "direct_source_binding_valid": direct_source_binding_valid,
        "system_schema_and_status_valid": system_binding_valid,
        "compact_arena_source_binding_valid": (arena_source_binding_valid),
        "compact_arena_counts_consistent": arena_counts_consistent,
        "compact_arena_target_indices_valid": (arena_target_indices_valid),
        "direct_matrix_relation_count": coverage["direct_matrix_relation_count"],
        "relations_represented_in_nonzero_scalar_numerators": coverage[
            "relations_represented_in_nonzero_scalar_numerators"
        ],
        "identically_zero_path_relation_count": coverage["identically_zero_path_relation_count"],
        "identically_zero_path_relation_ids_sha256": stable_hash(
            sorted(coverage["identically_zero_path_relation_ids"])
        ),
        "frozen_canonical_scalar_numerator_count": coverage[
            "frozen_canonical_scalar_numerator_count"
        ],
        "all_frozen_provenance_relation_ids_covered": coverage[
            "all_frozen_provenance_relation_ids_covered"
        ],
        "reconstructed_transition_predicate_count": direct["counts"][
            "reconstructed_transition_predicates"
        ],
        "explicit_inverse_site_count": direct["counts"]["explicit_inverse_sites"],
        "canonical_equation_count": len(equations),
        "canonical_equation_ids_sha256": stable_hash(sorted(equation_ids)),
        "canonical_expression_ids_sha256": stable_hash(sorted(canonical_expression_ids)),
        "provenance_entry_count": len(provenance_records),
        "provenance_entries_sha256": stable_hash(
            sorted(
                provenance_records,
                key=lambda record: (
                    record["equation_id"],
                    record["relation_id"],
                    record["matrix_entry"],
                ),
            )
        ),
        "represented_relation_count": len(represented_relation_ids),
        "represented_relations_have_all_four_entries": (represented_relations_have_all_entries),
        "represented_relations_are_exact_complement_of_zero_paths": (
            represented_relation_ids == direct_relation_ids - zero_path_relation_ids
        ),
        "zero_path_relations_are_exact_path_family": (zero_path_relations_are_exact_path_family),
        "all_provenance_v033_digests_cross_bound": (
            not any(error.startswith("v0.3.3 provenance mismatch:") for error in provenance_errors)
        ),
        "all_representative_expression_ids_are_provenance_originals": (
            not any(
                error.startswith("representative expression is not one of")
                for error in provenance_errors
            )
        ),
        "provenance_errors": provenance_errors,
        "compact_arena_reference_complete": arena_reference_complete,
        "missing_compact_arena_expression_ids": sorted(referenced_expression_ids - arena_targets),
        "proof_rule": (
            "Every one of the 2,564 frozen canonical numerators has "
            "compiler provenance in one of 3,916 matrix entries of the "
            "979 represented relations. The remaining 22 of all 1,001 "
            "direct relations are independently checked to be exactly "
            "the path-consistency family. Direct relations and scalar "
            "provenance are cross-bound by their v0.3.3 digests; every "
            "representative expression is a recorded provenance "
            "original; and the compact arena is hash-bound to the "
            "frozen polynomial system. Therefore an exact zero residual "
            "for every one of the 1,001 directly evaluated matrix "
            "relations forces all 2,564 frozen canonical numerators to "
            "vanish."
        ),
        "passed": passed,
    }


def _factor_summary(result: dict[str, Any]) -> dict[str, Any]:
    factors = sorted(
        record["factor"]
        for record in result.get("factor_reduction_records", [])
        if record.get("factor")
    )
    return {
        "raw_required_factor_count": result.get("raw_required_factor_count"),
        "effective_irreducible_factor_count": len(factors),
        "effective_irreducible_factors": factors,
        "effective_irreducible_factor_ids_sha256": stable_hash(factors),
        "all_source_factorisations_reconstructed_exactly": result.get(
            "factor_reduction_equivalence", {}
        ).get("all_source_factorisations_reconstructed_exactly", False),
        "zero_required_factor": result.get("zero_required_factor"),
    }


def verify_general_scalar_chain_lemma_v037(
    root: Path,
    *,
    aggregate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild both direct requests and every static coverage binding."""

    budget = load_human_budget_v037(root)
    payload = _load_json(root / RESULT_PATH) if aggregate is None else aggregate
    expected_branches = {LITERAL_BRANCH, DERIVED_BRANCH}
    exact_runs = payload.get("exact_runs", {})
    exact_run_keys_match = set(exact_runs) == expected_branches
    branch_checks: dict[str, Any] = {}
    if exact_run_keys_match:
        for branch in (LITERAL_BRANCH, DERIVED_BRANCH):
            request = build_scalar_chain_request_v037(
                root,
                branch,
                budget,
                expression_source=DIRECT_ROUTE,
            )
            branch_record = exact_runs[branch]
            run_record = branch_record["direct_relation_evaluation"]
            certificate_path = _certificate_path(
                root,
                branch,
                DIRECT_ROUTE,
                request,
            )
            exists = certificate_path.is_file()
            certificate = _load_json(certificate_path) if exists else {}
            coverage = _coverage_certificate(root, branch)
            checks = {
                "certificate_exists": exists,
                "certificate_path_matches_request": (
                    certificate_path.relative_to(root).as_posix() == run_record.get("path")
                ),
                "certificate_sha256_matches": bool(
                    exists and _sha256(certificate_path) == run_record.get("sha256")
                ),
                "certificate_semantic_digest_recomputes": bool(
                    exists
                    and certificate.get("semantic_digest_sha256")
                    == _result_semantic_digest(
                        certificate,
                        selection_fields=(
                            "selection_label",
                            "selected_relation_ids_sha256",
                            "selected_equation_ids_sha256",
                        ),
                    )
                ),
                "request_binding_and_identity_gate_pass": bool(
                    exists
                    and _valid_direct_identity_result(
                        certificate,
                        request,
                    )
                ),
                "coverage_recomputes_exactly": (
                    coverage == branch_record.get("coverage_certificate")
                ),
                "coverage_passed": coverage["passed"] is True,
                "branch_aggregate_passed": branch_record.get("passed") is True,
            }
            checks["passed"] = all(checks.values())
            branch_checks[branch] = checks

    proof_routes = [
        "ACTUAL_1001_DIRECT_MATRIX_RELATION_EVALUATION",
        "EXHAUSTIVE_FROZEN_COMPILER_PROVENANCE_COVERAGE",
    ]
    literal_identity = payload.get("literal_identity", {})
    derived_comparison = payload.get("derived_comparison", {})
    budget_accounting = payload.get("budget_accounting", {})
    new_runtime = budget_accounting.get("new_invocation_elapsed_seconds")
    cached_runtime = budget_accounting.get("cached_authorised_runtime_seconds")
    expected_source_artifacts = {
        SYSTEM_PATH: _sha256(root / SYSTEM_PATH),
        DIRECT_SYSTEM_PATH: _sha256(root / DIRECT_SYSTEM_PATH),
        BUDGET_PATH: budget["sha256"],
    }
    aggregate_semantic_digest = stable_hash(
        {
            "runs": exact_runs,
            "literal_identity": literal_identity,
            "derived_comparison": derived_comparison,
            "claim_boundary": payload.get("claim_boundary"),
            "verdict": payload.get("verdict"),
        }
    )
    aggregate_checks = {
        "schema_matches": payload.get("schema_version") == SCHEMA_LEMMA,
        "source_artifact_copies_match": payload.get("source_artifacts")
        == expected_source_artifacts,
        "budget_copy_matches_human_file": payload.get("budget") == budget,
        "budget_accounting_binding_valid": (
            budget_accounting.get("authorised_total_wall_time_seconds")
            == budget["total_wall_time_seconds"]
            and budget_accounting.get("effective_workers") == 1
            and budget_accounting.get("worker_policy")
            == "SEQUENTIAL_EXACT_QQ_WITH_TOTAL_WALL_DEADLINE"
            and budget_accounting.get("same_budget_terminal_results_are_not_retried") is True
            and isinstance(new_runtime, (int, float))
            and 0 <= float(new_runtime) <= budget["total_wall_time_seconds"]
            and isinstance(cached_runtime, (int, float))
            and 0 <= float(cached_runtime) <= budget["total_wall_time_seconds"]
        ),
        "exact_run_keys_match": exact_run_keys_match,
        "certificate_role_count_is_2": len(branch_checks) == 2,
        "all_branch_checks_pass": bool(
            branch_checks and all(record["passed"] for record in branch_checks.values())
        ),
        "literal_direct_and_coverage_claims_exact": (
            literal_identity.get("all_1001_matrix_relations_directly_evaluated_and_zero") is True
            and literal_identity.get(
                "all_2564_canonical_numerators_deduced_zero_from_direct_relations_and_coverage"
            )
            is True
            and literal_identity.get("proof_routes") == proof_routes
            and literal_identity.get("distinct_proof_components") is True
            and literal_identity.get("distinct_evaluation_routes") is False
            and literal_identity.get("independent_implementation") is False
            and literal_identity.get("shared_backend_and_compiler_lineage") is True
            and literal_identity.get("Q5_equality_constraints_after_scalar_chain_substitution") == 0
        ),
        "derived_direct_and_coverage_claims_exact": (
            derived_comparison.get("all_1001_matrix_relations_directly_evaluated_and_zero") is True
            and derived_comparison.get(
                "all_2564_canonical_numerators_deduced_zero_from_direct_relations_and_coverage"
            )
            is True
            and derived_comparison.get("proof_routes") == proof_routes
            and derived_comparison.get("distinct_proof_components") is True
            and derived_comparison.get("distinct_evaluation_routes") is False
            and derived_comparison.get("independent_implementation") is False
            and derived_comparison.get("shared_backend_and_compiler_lineage") is True
        ),
        "aggregate_passed": payload.get("passed") is True,
        "verdict_exact": payload.get("verdict") == LEMMA,
        "global_verdict_open": payload.get("global_scientific_verdict") == "FINAL_THEORY_OPEN",
        "semantic_digest_recomputes": payload.get("semantic_digest_sha256")
        == aggregate_semantic_digest,
    }
    passed = all(aggregate_checks.values())
    return {
        "schema_version": ("final-theory-general-scalar-chain-verification-v0.3.7"),
        "budget_file_sha256": budget["sha256"],
        "certificate_role_counts": {"PHASE2_QQ_DIRECT_IDENTITY_EXACT": len(branch_checks)},
        "branch_checks": branch_checks,
        "aggregate_checks": aggregate_checks,
        "verdict": payload.get("verdict"),
        "global_scientific_verdict": payload.get("global_scientific_verdict"),
        "passed": passed,
    }


def run_general_scalar_chain_lemma_v037(root: Path) -> dict[str, Any]:
    """Evaluate both direct relations and frozen numerators over exact QQ."""

    budget = load_human_budget_v037(root)
    jobs: list[dict[str, Any]] = []
    for branch in (LITERAL_BRANCH, DERIVED_BRANCH):
        for expression_source in (DIRECT_ROUTE,):
            request = build_scalar_chain_request_v037(
                root,
                branch,
                budget,
                expression_source=expression_source,
            )
            path = _certificate_path(
                root,
                branch,
                expression_source,
                request,
            )
            validator = (
                _valid_direct_identity_result
                if expression_source == DIRECT_ROUTE
                else _valid_canonical_identity_result
            )
            jobs.append(
                {
                    "branch": branch,
                    "expression_source": expression_source,
                    "request": request,
                    "path": path,
                    "validator": validator,
                }
            )

    cached_results: dict[tuple[str, str], dict[str, Any]] = {}
    cached_authorised_runtime_seconds = 0.0
    for job in jobs:
        path = job["path"]
        request = job["request"]
        validator = job["validator"]
        result: dict[str, Any] | None = None
        if path.is_file():
            candidate = _load_json(path)
            if validator(candidate, request) or _bound_terminal_result(candidate, request):
                result = candidate
        if result is None:
            continue
        key = (job["branch"], job["expression_source"])
        cached_results[key] = result
        cached_authorised_runtime_seconds += _result_wall_time_seconds(result)

    remaining_authorised_seconds = max(
        0.0,
        float(budget["total_wall_time_seconds"]) - cached_authorised_runtime_seconds,
    )
    invocation_started = time.perf_counter()
    deadline = invocation_started + remaining_authorised_seconds
    certificates: dict[str, dict[str, Any]] = {
        LITERAL_BRANCH: {},
        DERIVED_BRANCH: {},
    }
    for job in jobs:
        branch = job["branch"]
        expression_source = job["expression_source"]
        request = job["request"]
        path = job["path"]
        validator = job["validator"]
        key = (branch, expression_source)
        result = cached_results.get(key)
        cached = result is not None
        if result is None:
            remaining = deadline - time.perf_counter()
            if remaining < 1.0:
                result = {
                    "schema_version": SCHEMA_RESPONSE,
                    "chart": request["chart"],
                    "source_index_branch": request["source_index_branch"],
                    "equation_source_index_branch": request["equation_source_index_branch"],
                    "coefficient_field": "QQ",
                    "budget_file_sha256": request["budget_file_sha256"],
                    "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
                    "exit_status": "NOT_RUN_TOTAL_BUDGET_EXHAUSTED",
                    "proof_eligible": False,
                }
            else:
                timeout = min(
                    int(budget["timeout_seconds_per_chart"]),
                    max(1, int(remaining)),
                )
                result = run_sage_request(
                    root,
                    request,
                    timeout_seconds=timeout,
                )
            _write_json(path, result)
        branch_certificates = certificates[branch]
        route_label = (
            "direct_relation_evaluation"
            if expression_source == DIRECT_ROUTE
            else "canonical_numerator_evaluation"
        )
        route_summary: dict[str, Any] = {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "sha256": _sha256(path),
            "cached": cached,
            "passed": validator(result, request),
            "exit_status": result.get("exit_status"),
            "budget_file_sha256": result.get("budget_file_sha256"),
            "request_semantic_digest_sha256": result.get("request_semantic_digest_sha256"),
            "backend_versions": result.get("backend_versions"),
            "variable_count": result.get("variable_count"),
            "variables": result.get("variables"),
            "expression_source": result.get("expression_source"),
            "proof_eligible": result.get("proof_eligible"),
            "identity_proof_eligible": result.get("identity_proof_eligible"),
            "direct_system_file_sha256": result.get("direct_system_file_sha256"),
            "direct_system_semantic_digest_sha256": result.get(
                "direct_system_semantic_digest_sha256"
            ),
            "wall_time_seconds": result.get("resource_usage", {}).get("wall_time_seconds"),
            "host_wall_time_seconds": result.get(
                "host_observed_wall_time_seconds",
                result.get("wall_time_seconds"),
            ),
            "peak_rss_bytes": result.get("resource_usage", {}).get("peak_rss_bytes"),
        }
        if expression_source == DIRECT_ROUTE:
            route_summary.update(
                {
                    "matrix_relation_count": result.get("selected_matrix_relation_count"),
                    "relations_evaluated_count": result.get("relations_evaluated_count"),
                    "relation_ids_sha256": result.get("selected_relation_ids_sha256"),
                    "evaluated_relation_ids_sha256": result.get("evaluated_relation_ids_sha256"),
                    "nonzero_residual_count": result.get("nonzero_specialised_equation_count"),
                    "reconstructed_transitions_checked": result.get(
                        "reconstructed_transitions_checked"
                    ),
                    "factor_domain": _factor_summary(result),
                }
            )
        else:
            route_summary.update(
                {
                    "canonical_numerator_count": result.get("selected_canonical_equation_count"),
                    "zero_specialised_canonical_numerator_count": (
                        result.get("zero_specialised_equation_count")
                    ),
                    "nonzero_specialised_canonical_numerator_count": (
                        result.get("nonzero_specialised_canonical_equation_count")
                    ),
                    "equation_ids_sha256": result.get("selected_equation_ids_sha256"),
                    "expression_ids_sha256": result.get("selected_expression_ids_sha256"),
                    "denominator_factor_count": result.get("selected_denominator_record_count"),
                    "factor_domain": _factor_summary(result),
                }
            )
        branch_certificates[route_label] = route_summary

    for branch in (LITERAL_BRANCH, DERIVED_BRANCH):
        branch_certificates = certificates[branch]
        coverage = _coverage_certificate(root, branch)
        branch_certificates["coverage_certificate"] = coverage
        branch_certificates["passed"] = bool(
            branch_certificates["direct_relation_evaluation"]["passed"] and coverage["passed"]
        )

    literal_passed = certificates[LITERAL_BRANCH]["passed"]
    derived_passed = certificates[DERIVED_BRANCH]["passed"]
    passed = literal_passed and derived_passed
    literal_factors = certificates[LITERAL_BRANCH]["direct_relation_evaluation"]["factor_domain"][
        "effective_irreducible_factors"
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_LEMMA,
        "branch": BRANCH,
        "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
        "finite_scope": "frozen source stages n<=4",
        "dimension": 2,
        "field": "QQ fraction field; characteristic zero",
        "source_artifacts": {
            SYSTEM_PATH: _sha256(root / SYSTEM_PATH),
            DIRECT_SYSTEM_PATH: _sha256(root / DIRECT_SYSTEM_PATH),
            BUDGET_PATH: budget["sha256"],
        },
        "budget": budget,
        "budget_accounting": {
            "cached_authorised_runtime_seconds": (cached_authorised_runtime_seconds),
            "new_invocation_elapsed_seconds": (time.perf_counter() - invocation_started),
            "authorised_total_wall_time_seconds": budget["total_wall_time_seconds"],
            "effective_workers": 1,
            "worker_policy": ("SEQUENTIAL_EXACT_QQ_WITH_TOTAL_WALL_DEADLINE"),
            "same_budget_terminal_results_are_not_retried": True,
        },
        "symbolic_bases": {
            LITERAL_BRANCH: {
                "variables": [
                    "a",
                    "b",
                    "c",
                    "d",
                    "lambda_2",
                    "lambda_3",
                    "lambda_4",
                    "e",
                    "f",
                    "g",
                    "h",
                ],
                "Q1": [["a", "b"], ["c", "d"]],
                "Q2_Q3_Q4": "Q_n=lambda_n Q1",
                "Q5": [["e", "f"], ["g", "h"]],
            },
            DERIVED_BRANCH: {
                "variables": [
                    "a",
                    "b",
                    "c",
                    "d",
                    "lambda_2",
                    "lambda_3",
                    "lambda_4",
                ],
                "Q1": [["a", "b"], ["c", "d"]],
                "Q2_Q3_Q4": "Q_n=lambda_n Q1",
                "Q5": "absent",
            },
        },
        "exact_runs": certificates,
        "literal_identity": {
            "all_1001_matrix_relations_directly_evaluated_and_zero": (
                certificates[LITERAL_BRANCH]["direct_relation_evaluation"]["passed"]
            ),
            "all_2564_canonical_numerators_deduced_zero_from_direct_relations_and_coverage": (
                certificates[LITERAL_BRANCH]["coverage_certificate"]["passed"]
                and certificates[LITERAL_BRANCH]["direct_relation_evaluation"]["passed"]
            ),
            "proof_routes": [
                "ACTUAL_1001_DIRECT_MATRIX_RELATION_EVALUATION",
                "EXHAUSTIVE_FROZEN_COMPILER_PROVENANCE_COVERAGE",
            ],
            "distinct_proof_components": True,
            "distinct_evaluation_routes": False,
            "independent_implementation": False,
            "shared_backend_and_compiler_lineage": True,
            "Q5_polynomial_coordinates": 4,
            "Q5_equality_constraints_after_scalar_chain_substitution": (
                0 if literal_passed else None
            ),
            "localised_nonzero_factor_count": len(literal_factors),
            "localised_nonzero_factors": literal_factors,
        },
        "derived_comparison": {
            "all_1001_matrix_relations_directly_evaluated_and_zero": (
                certificates[DERIVED_BRANCH]["direct_relation_evaluation"]["passed"]
            ),
            "all_2564_canonical_numerators_deduced_zero_from_direct_relations_and_coverage": (
                certificates[DERIVED_BRANCH]["coverage_certificate"]["passed"]
                and certificates[DERIVED_BRANCH]["direct_relation_evaluation"]["passed"]
            ),
            "proof_routes": [
                "ACTUAL_1001_DIRECT_MATRIX_RELATION_EVALUATION",
                "EXHAUSTIVE_FROZEN_COMPILER_PROVENANCE_COVERAGE",
            ],
            "distinct_proof_components": True,
            "distinct_evaluation_routes": False,
            "independent_implementation": False,
            "shared_backend_and_compiler_lineage": True,
            "scalar_chain_base_exists_on_recorded_open_domain": (derived_passed),
            "noncommutative_solution_on_scalar_chain": False,
        },
        "claim_boundary": (
            "The lemma is an exact identity on the open locus where every "
            "recorded specialised inverse/transition factor is nonzero. "
            "The 2,564-numerator statement is deduced from actual direct "
            "evaluation of all 1,001 matrix relations plus exhaustive "
            "verification of the frozen compiler provenance map; it is "
            "not reported as a second independent implementation. "
            "No assertion is made on excluded denominator loci."
        ),
        "exact_numeric_distinction": (
            "EXACT_QQ_DIRECT_RELATION_EVALUATION_PLUS_EXHAUSTIVE_"
            "FROZEN_COMPILER_COVERAGE; no finite-field result is used"
        ),
        "global_scientific_verdict": "FINAL_THEORY_OPEN",
        "unresolved_components": []
        if passed
        else [
            branch
            for branch in (LITERAL_BRANCH, DERIVED_BRANCH)
            if not certificates[branch]["passed"]
        ],
        "passed": passed,
        "verdict": LEMMA if passed else "SCALAR_CHAIN_IDENTITY_PARTIAL",
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "runs": certificates,
            "literal_identity": payload["literal_identity"],
            "derived_comparison": payload["derived_comparison"],
            "claim_boundary": payload["claim_boundary"],
            "verdict": payload["verdict"],
        }
    )
    _write_json(root / RESULT_PATH, payload)
    return payload


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _argument_parser().parse_args(argv)
    if not arguments.run:
        raise SystemExit("select --run")
    payload = run_general_scalar_chain_lemma_v037(Path.cwd())
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
