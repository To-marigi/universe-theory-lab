"""v0.3.7 Q5-free elimination for the literal d=2 branch.

The decisive system is the 976-relation shared core.  Its 2,552 frozen
canonical scalar numerators are exactly the Q5-independent part of the
literal 2,564-numerator system.  The chart geometry is the already certified
three-ratio cover for R2, R3, R4; R5 and Q5 never occur in these requests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_sage_backend_v035 import (
    _result_semantic_digest,
    build_chart_payload,
    detect_sage_backend,
    run_sage_request,
)
from universe_lab.final_theory.d2_strata_v034 import S1, S2, stratum_charts
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.q5_closure_v036 import (
    _compact_arena_q_masks,
)

BRANCH = "codex/final-theory-v0.3.7-publication-20260729"
SCHEMA_PARTITION = "final-theory-q5-free-partition-v0.3.7"
SCHEMA_REQUEST = "final-theory-q5-free-sage-request-v0.3.7"
SCHEMA_RESPONSE = "final-theory-q5-free-sage-response-v0.3.7"
SCHEMA_CAMPAIGN = "final-theory-q5-free-campaign-v0.3.7"
VERDICT_PROVED = "LITERAL_Q1_Q4_COMMUTATIVITY_PROVED"
VERDICT_FOUND = "LITERAL_NONCOMMUTATIVE_Q1_Q4_FOUND"
VERDICT_PARTIAL = "LITERAL_Q5_FREE_ELIMINATION_PARTIAL"
SHARED_CORE = "Q5_FREE_SHARED_CORE"

BUDGET_PATH = "config/v0.3.7_budget.json"
SYSTEM_PATH = "results/v0.3.4_polynomial_systems.json"
CENSUS_PATH = "results/v0.3.6_q5_constraint_census.json"
DIRECT_SYSTEM_PATH = "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
PARTITION_PATH = "results/v0.3.7_q5_free_partition.json"
CAMPAIGN_PATH = "results/v0.3.7_q5_free_elimination.json"
CERTIFICATE_ROOT = "certificates/d2_saturation/q5_free_v037"
COMPACT_PREFLIGHT_PATH = (
    "certificates/d2_saturation/q5_free_v037/preflight_compact_arena_timeout.json"
)

EXPECTED_FREE_EQUATION_DIGEST = "55c4362e61696800fc4e52ce28bc0e4eb1220fd4eac351bf846a9692c47e5a73"
EXPECTED_FREE_EXPRESSION_DIGEST = "dca28b92a2a85a4eee7f31f67a9bd2633b87ae4c1d6d523307def5d1f748cade"
EXPECTED_DENOMINATOR_DIGEST = "590225322705bd7580c5b25e1339fb69aecdd0c11452b62de8bf1d814511b70e"
EXPECTED_RELATION_FAMILY_COUNTS = {
    "CPOBC": 700,
    "LOCAL_OPERATOR_GC": 255,
    "STRONG_OPERATOR_MSR": 21,
}
SCOUT_MODULI = (32003, 32009)


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


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
        newline="\n",
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


def load_human_budget_v037(root: Path) -> dict[str, Any]:
    """Read the external budget file without inventing fallback values."""

    path = root / BUDGET_PATH
    if not path.is_file():
        raise FileNotFoundError(f"external budget file is required: {BUDGET_PATH}")
    supplied = _load_json(path)
    required = {
        "timeout_seconds_per_chart",
        "total_wall_time_seconds",
        "memory_limit_gib",
    }
    missing = sorted(required - supplied.keys())
    if missing:
        raise ValueError(f"budget is missing required keys: {missing}")
    unsupported = sorted(supplied.keys() - required)
    if unsupported:
        raise ValueError(f"budget has unsupported, unauthorised keys: {unsupported}")
    values: dict[str, float] = {}
    for name in sorted(required):
        value = supplied[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"budget {name} must be numeric")
        if not math.isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"budget {name} must be positive and finite")
        values[name] = float(value)
    timeout = values["timeout_seconds_per_chart"]
    total = values["total_wall_time_seconds"]
    if timeout > total:
        raise ValueError("timeout_seconds_per_chart cannot exceed total_wall_time_seconds")
    budget: dict[str, Any] = {
        "provenance": (
            "EXTERNAL_REPOSITORY_BUDGET_FILE; NO_RUNTIME_DEFAULTS_OR_SELF_AUTHENTICATION"
        ),
        "path": BUDGET_PATH,
        "sha256": _sha256(path),
        "timeout_seconds_per_chart": int(timeout),
        "total_wall_time_seconds": int(total),
        "memory_limit_gib": values["memory_limit_gib"],
        "memory_limit_bytes": int(values["memory_limit_gib"] * 1024 * 1024 * 1024),
    }
    return budget


def compile_q5_free_partition_v037(root: Path) -> dict[str, Any]:
    """Certify the exact 12/2,552 canonical-numerator partition."""

    system_path = root / SYSTEM_PATH
    census_path = root / CENSUS_PATH
    direct_path = root / DIRECT_SYSTEM_PATH
    systems = _load_json(system_path)
    census = _load_json(census_path)
    direct = _load_json(direct_path)
    target_masks, arena_metadata = _compact_arena_q_masks(root)

    literal = systems["systems"][LITERAL_BRANCH]["equations"]
    derived = systems["systems"][DERIVED_BRANCH]["equations"]
    q5_bit = 1 << 5
    missing_targets = sorted(
        record["canonical_expression_id"]
        for record in literal
        if record["canonical_expression_id"] not in target_masks
    )
    q5_dependent = [
        record for record in literal if target_masks[record["canonical_expression_id"]] & q5_bit
    ]
    q5_free = [
        record for record in literal if not target_masks[record["canonical_expression_id"]] & q5_bit
    ]
    q5_dependent_ids = sorted(record["equation_id"] for record in q5_dependent)
    q5_free_ids = sorted(record["equation_id"] for record in q5_free)
    q5_dependent_expression_ids = sorted(
        record["canonical_expression_id"] for record in q5_dependent
    )
    q5_free_expression_ids = sorted(record["canonical_expression_id"] for record in q5_free)

    literal_by_id = {record["equation_id"]: record for record in literal}
    derived_by_id = {record["equation_id"]: record for record in derived}
    shared_ids = sorted(literal_by_id.keys() & derived_by_id.keys())
    shared_records_equal = all(
        literal_by_id[equation_id] == derived_by_id[equation_id] for equation_id in shared_ids
    )

    relation_entries: defaultdict[str, set[tuple[int, int]]] = defaultdict(set)
    relation_families: dict[str, str] = {}
    provenance_count = 0
    for equation in q5_free:
        for provenance in equation["provenance"]:
            provenance_count += 1
            relation_id = provenance["relation_id"]
            matrix_entry = provenance["matrix_entry"]
            if len(matrix_entry) != 2:
                raise RuntimeError(f"invalid matrix entry for relation {relation_id}")
            relation_entries[relation_id].add((int(matrix_entry[0]), int(matrix_entry[1])))
            previous = relation_families.setdefault(
                relation_id,
                provenance["family"],
            )
            if previous != provenance["family"]:
                raise RuntimeError(f"inconsistent family for relation {relation_id}")
    relation_family_counts = dict(sorted(Counter(relation_families.values()).items()))
    all_relations_have_four_entries = all(
        entries == {(0, 0), (0, 1), (1, 0), (1, 1)} for entries in relation_entries.values()
    )

    literal_direct = direct["relations"][LITERAL_BRANCH]
    derived_direct = direct["relations"][DERIVED_BRANCH]
    literal_core = [
        record for record in literal_direct if record["family"] != "EQ112_PATH_CONSISTENCY"
    ]
    derived_core = [
        record for record in derived_direct if record["family"] != "EQ112_PATH_CONSISTENCY"
    ]
    literal_core_by_id = {record["relation_id"]: record for record in literal_core}
    derived_core_by_id = {record["relation_id"]: record for record in derived_core}
    direct_core_ids = sorted(literal_core_by_id)
    direct_core_records_equal = literal_core_by_id.keys() == derived_core_by_id.keys() and all(
        literal_core_by_id[relation_id] == derived_core_by_id[relation_id]
        for relation_id in literal_core_by_id
    )
    literal_path = [
        record for record in literal_direct if record["family"] == "EQ112_PATH_CONSISTENCY"
    ]
    coverage = direct["relation_to_scalar_equation_coverage"][LITERAL_BRANCH]
    zero_path_ids = sorted(coverage["identically_zero_path_relation_ids"])

    denominator_records = systems["denominator_factors"]
    missing_denominator_targets = sorted(
        record["factor_id"]
        for record in denominator_records
        if record["factor_id"] not in target_masks
    )
    q5_denominators = sorted(
        record["factor_id"]
        for record in denominator_records
        if target_masks[record["factor_id"]] & q5_bit
    )
    denominator_ids = sorted(record["factor_id"] for record in denominator_records)

    census_dependent_ids = sorted(
        record["equation_id"] for record in census["Q5_scalar_numerator_equations"]
    )
    equation_ids_unique = len({record["equation_id"] for record in literal}) == len(literal)
    expression_ids_unique = len({record["canonical_expression_id"] for record in literal}) == len(
        literal
    )
    partition_disjoint = not (set(q5_dependent_ids) & set(q5_free_ids))
    partition_union_complete = set(q5_dependent_ids) | set(q5_free_ids) == {
        record["equation_id"] for record in literal
    }
    free_equation_digest = stable_hash(q5_free_ids)
    free_expression_digest = stable_hash(q5_free_expression_ids)
    denominator_digest = stable_hash(denominator_ids)

    passed = bool(
        census.get("passed")
        and not missing_targets
        and not missing_denominator_targets
        and len(literal) == len(derived) == 2564
        and len(q5_dependent) == 12
        and len(q5_free) == 2552
        and equation_ids_unique
        and expression_ids_unique
        and partition_disjoint
        and partition_union_complete
        and q5_dependent_ids == census_dependent_ids
        and shared_ids == q5_free_ids
        and shared_records_equal
        and len(relation_families) == 976
        and provenance_count == 3904
        and relation_family_counts == EXPECTED_RELATION_FAMILY_COUNTS
        and all_relations_have_four_entries
        and "EQ112_PATH_CONSISTENCY" not in set(relation_families.values())
        and len(literal_core) == len(derived_core) == 976
        and direct_core_records_equal
        and set(direct_core_ids) == set(relation_families)
        and len(literal_path) == 25
        and len(zero_path_ids) == 22
        and len(denominator_records) == 191
        and not q5_denominators
        and free_equation_digest == EXPECTED_FREE_EQUATION_DIGEST
        and free_expression_digest == EXPECTED_FREE_EXPRESSION_DIGEST
        and denominator_digest == EXPECTED_DENOMINATOR_DIGEST
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_PARTITION,
        "branch": BRANCH,
        "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
        "finite_scope": "frozen source stages n<=4",
        "source_artifacts": {
            SYSTEM_PATH: _sha256(system_path),
            CENSUS_PATH: _sha256(census_path),
            DIRECT_SYSTEM_PATH: _sha256(direct_path),
            arena_metadata["path"]: arena_metadata["sha256"],
        },
        "canonicalisation_boundary": (
            "Canonical numerators identify structurally equal expressions "
            "and sign reversals and omit exact zero entries. They are not "
            "claimed to be a minimal generating set or a Groebner basis."
        ),
        "partition": {
            "literal_total": len(literal),
            "Q5_dependent_count": len(q5_dependent),
            "Q5_independent_count": len(q5_free),
            "equation_ids_unique": equation_ids_unique,
            "canonical_expression_ids_unique": expression_ids_unique,
            "disjoint": partition_disjoint,
            "union_complete": partition_union_complete,
            "Q5_dependent_equation_ids": q5_dependent_ids,
            "Q5_dependent_expression_ids": q5_dependent_expression_ids,
            "Q5_independent_equation_ids": q5_free_ids,
            "Q5_independent_expression_ids": q5_free_expression_ids,
            "Q5_dependent_equation_ids_sha256": stable_hash(q5_dependent_ids),
            "Q5_dependent_expression_ids_sha256": stable_hash(q5_dependent_expression_ids),
            "Q5_independent_equation_ids_sha256": free_equation_digest,
            "Q5_independent_expression_ids_sha256": (free_expression_digest),
            "census_dependent_ID_set_matches": (q5_dependent_ids == census_dependent_ids),
            "compact_arena_missing_target_ids": missing_targets,
        },
        "shared_core": {
            "canonical_record_intersection_count": len(shared_ids),
            "intersection_is_exactly_Q5_independent_partition": (shared_ids == q5_free_ids),
            "shared_records_byte_semantics_equal": shared_records_equal,
            "matrix_relation_count": len(relation_families),
            "matrix_relation_ids": sorted(relation_families),
            "matrix_relation_ids_sha256": stable_hash(sorted(relation_families)),
            "relation_family_counts": relation_family_counts,
            "canonical_provenance_entry_count": provenance_count,
            "every_relation_has_all_four_matrix_entries": (all_relations_have_four_entries),
            "path_provenance_count": sum(
                family == "EQ112_PATH_CONSISTENCY" for family in relation_families.values()
            ),
            "direct_core_records_equal_between_branches": (direct_core_records_equal),
        },
        "excluded_path_family": {
            "literal_path_relation_count": len(literal_path),
            "identically_zero_path_relation_count": len(zero_path_ids),
            "nonzero_path_relation_count": len(literal_path) - len(zero_path_ids),
            "canonical_numerator_count": len(q5_dependent),
            "exact_count_identities": [
                "1001 = 976 shared-core relations + 25 path relations",
                "2564 = 2552 shared-core numerators + 12 path numerators",
                "25 path relations = 22 exact-zero + 3 nonzero",
            ],
        },
        "denominators": {
            "factor_count": len(denominator_records),
            "factor_ids_sha256": denominator_digest,
            "Q5_dependent_factor_count": len(q5_denominators),
            "Q5_dependent_factor_ids": q5_denominators,
            "compact_arena_missing_factor_ids": (missing_denominator_targets),
        },
        "forward_implication": {
            "premise": (
                "Every literal-system solution satisfies every equation in "
                "the 2,552-equation shared core."
            ),
            "rule": (
                "If the shared core forces [Q_i,Q_j]=0 for 1<=i<j<=4, "
                "then the literal system does as well."
            ),
            "reverse_implication_used": False,
            "Q5_behaviour_needed": False,
        },
        "exact_numeric_distinction": ("EXACT_FROZEN_DAG_DEPENDENCY_PARTITION"),
        "unresolved_components": []
        if passed
        else ["one or more frozen partition invariants failed"],
        "passed": passed,
        "verdict": ("Q5_FREE_2552_PARTITION_CERTIFIED" if passed else VERDICT_PARTIAL),
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "partition": payload["partition"],
            "shared_core": payload["shared_core"],
            "excluded_path_family": payload["excluded_path_family"],
            "denominators": payload["denominators"],
            "forward_implication": payload["forward_implication"],
            "verdict": payload["verdict"],
        }
    )
    return payload


def _core_s1_s2_charts() -> list[Any]:
    charts = [chart for chart in stratum_charts(DERIVED_BRANCH) if chart.stratum in {S1, S2}]
    if len(charts) != 21:
        raise RuntimeError(f"expected 21 core S1/S2 charts, got {len(charts)}")
    if Counter(chart.stratum for chart in charts) != Counter({S1: 12, S2: 9}):
        raise RuntimeError("unexpected S1/S2 core chart distribution")
    return charts


def _campaign_chart_id(cover_chart_id: str) -> str:
    _, suffix = cover_chart_id.split(":", 1)
    return f"{SHARED_CORE}:{suffix}"


def build_q5_free_chart_request_v037(
    chart: Any,
    partition: dict[str, Any],
    budget: dict[str, Any],
    *,
    coefficient_modulus: int,
) -> dict[str, Any]:
    """Separate core chart geometry from the literal equation source."""

    request = build_chart_payload(
        DERIVED_BRANCH,
        chart.chart_id,
        coefficient_modulus=coefficient_modulus,
        operation="solve",
        maximum_source_stage=4,
        saturation=True,
        check_noncommutativity=True,
        factor_denominators=True,
        expression_source="direct_operator",
        include_all_transition_predicates=True,
        groebner_algorithm="libsingular:slimgb",
        groebner_strategy="progressive",
        progressive_batch_size=4,
        saturation_factor_order="forward",
    )
    selected = partition["partition"]
    request.update(
        {
            "schema_version": SCHEMA_REQUEST,
            "response_schema_version": SCHEMA_RESPONSE,
            "chart": _campaign_chart_id(chart.chart_id),
            "chart_cover_id": chart.chart_id,
            "chart_source_index_branch": DERIVED_BRANCH,
            "equation_source_index_branch": LITERAL_BRANCH,
            "source_index_branch": LITERAL_BRANCH,
            "selection_label": "LITERAL_Q5_INDEPENDENT_2552",
            "selection_certificate": PARTITION_PATH,
            "selection_certificate_semantic_digest_sha256": partition["semantic_digest_sha256"],
            "excluded_equation_ids": selected["Q5_dependent_equation_ids"],
            "expected_excluded_equation_count": 12,
            "expected_selected_canonical_equation_count": 2552,
            "expected_selected_equation_ids_sha256": selected["Q5_independent_equation_ids_sha256"],
            "expected_selected_expression_ids_sha256": selected[
                "Q5_independent_expression_ids_sha256"
            ],
            "expected_selected_relation_count": 976,
            "expected_selected_relation_ids_sha256": partition["shared_core"][
                "matrix_relation_ids_sha256"
            ],
            "expected_relation_family_counts": (EXPECTED_RELATION_FAMILY_COUNTS),
            "included_relation_families": sorted(EXPECTED_RELATION_FAMILY_COUNTS),
            "forbidden_relation_families": ["EQ112_PATH_CONSISTENCY"],
            "forbidden_provenance_families": ["EQ112_PATH_CONSISTENCY"],
            "canonical_ideal_equivalence_certified": True,
            "expected_frozen_denominator_factor_count": 191,
            "memory_limit_bytes": budget["memory_limit_bytes"],
            "budget_file": BUDGET_PATH,
            "budget_file_sha256": budget["sha256"],
            "authorised_timeout_seconds_per_run": budget["timeout_seconds_per_chart"],
            "authorised_total_wall_time_seconds": budget["total_wall_time_seconds"],
        }
    )
    if any(name.startswith("q5_") for name in request["q_substitutions"]):
        raise RuntimeError("Q5 variable leaked into a Q5-free chart request")
    if any(5 in component["pair"] for component in request["commutator_components"]):
        raise RuntimeError("Q5 commutator leaked into a core chart request")
    request["request_semantic_digest_sha256"] = _request_semantic_digest(request)
    return request


def _certificate_path(
    root: Path,
    request: dict[str, Any],
) -> Path:
    modulus = int(request["coefficient_modulus"])
    field = "QQ" if modulus == 0 else f"GF{modulus}"
    budget = request["budget_file_sha256"][:16]
    digest = request["request_semantic_digest_sha256"][:24]
    return root / CERTIFICATE_ROOT / f"budget-{budget}" / field / f"{digest}.json"


def _memory_limit_matches_request(
    result: dict[str, Any],
    request: dict[str, Any],
) -> bool:
    memory_limit = result.get("resource_usage", {}).get("memory_limit")
    if not isinstance(memory_limit, dict):
        return False
    requested = int(request["memory_limit_bytes"])
    effective = memory_limit.get("effective_limit_bytes")
    return bool(
        memory_limit.get("requested") is True
        and memory_limit.get("applied") is True
        and memory_limit.get("resource") == "RLIMIT_AS"
        and memory_limit.get("limit_bytes") == requested
        and isinstance(effective, int)
        and 0 < effective <= requested
    )


def _valid_cached_result(
    path: Path,
    request: dict[str, Any],
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        result = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    expected_field = (
        "QQ"
        if int(request["coefficient_modulus"]) == 0
        else f"GF({request['coefficient_modulus']})"
    )
    if (
        result.get("exit_status") == "COMPLETED"
        and result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("chart") == request["chart"]
        and result.get("coefficient_field") == expected_field
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and result.get("time_limit_seconds", 0) > 0
        and result.get("time_limit_seconds") <= request["authorised_timeout_seconds_per_run"]
        and _memory_limit_matches_request(result, request)
        and result.get("selection_label") == "LITERAL_Q5_INDEPENDENT_2552"
        and result.get("selected_canonical_equation_count") == 2552
        and result.get("selected_matrix_relation_count") == 976
        and result.get("selected_equation_ids_sha256")
        == request["expected_selected_equation_ids_sha256"]
        and result.get("selected_expression_ids_sha256")
        == request["expected_selected_expression_ids_sha256"]
        and result.get("selected_denominator_record_count") == 191
        and result.get("canonical_selection_checks_passed") is True
        and result.get("saturation_requested") is True
        and result.get("final_localisation_complete") is True
        and result.get("commutator_coverage_complete") is True
        and result.get("resource_usage", {}).get("memory_budget_satisfied") is True
    ):
        return result
    return None


def _bound_terminal_result(
    path: Path,
    request: dict[str, Any],
) -> dict[str, Any] | None:
    """Reuse a same-budget terminal result without silently retrying it."""

    if not path.is_file():
        return None
    try:
        result = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    expected_field = (
        "QQ"
        if int(request["coefficient_modulus"]) == 0
        else f"GF({request['coefficient_modulus']})"
    )
    if (
        result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("chart") == request["chart"]
        and result.get("coefficient_field") == expected_field
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and isinstance(result.get("exit_status"), str)
    ):
        return result
    return None


def _result_wall_time_seconds(result: dict[str, Any]) -> float:
    for value in (
        result.get("host_observed_wall_time_seconds"),
        result.get("wall_time_seconds"),
        result.get("resource_usage", {}).get("wall_time_seconds"),
    ):
        if value is not None:
            return float(value)
    return 0.0


def _run_summary(
    root: Path,
    result: dict[str, Any],
    path: Path,
    *,
    cached: bool,
) -> dict[str, Any]:
    return {
        "chart": result.get("chart"),
        "chart_cover_id": result.get("chart_cover_id"),
        "stratum": result.get("stratum"),
        "coefficient_field": result.get("coefficient_field"),
        "exit_status": result.get("exit_status"),
        "chart_verdict": result.get("chart_verdict"),
        "proof_eligible": result.get("proof_eligible", False),
        "selected_canonical_equation_count": result.get("selected_canonical_equation_count"),
        "selected_matrix_relation_count": result.get("selected_matrix_relation_count"),
        "selected_denominator_record_count": result.get("selected_denominator_record_count"),
        "canonical_selection_checks_passed": result.get("canonical_selection_checks_passed", False),
        "saturated_unit_ideal": result.get("saturated_unit_ideal", False),
        "final_localisation_complete": result.get("final_localisation_complete", False),
        "commutator_component_count": result.get("commutator_component_count"),
        "covered_commutator_component_count": result.get("covered_commutator_component_count"),
        "commutator_coverage_complete": result.get("commutator_coverage_complete", False),
        "surviving_noncommutative_component_count": result.get(
            "surviving_noncommutative_component_count"
        ),
        "worker_wall_time_seconds": result.get("resource_usage", {}).get("wall_time_seconds"),
        "host_wall_time_seconds": result.get(
            "host_observed_wall_time_seconds",
            result.get(
                "wall_time_seconds",
                result.get("resource_usage", {}).get("wall_time_seconds"),
            ),
        ),
        "peak_rss_bytes": result.get("resource_usage", {}).get("peak_rss_bytes"),
        "memory_budget_satisfied": result.get("resource_usage", {}).get(
            "memory_budget_satisfied", False
        ),
        "cached": cached,
        "certificate": str(path.relative_to(root)).replace("\\", "/"),
        "certificate_sha256": _sha256(path) if path.is_file() else None,
        "budget_file_sha256": result.get("budget_file_sha256"),
        "request_semantic_digest_sha256": result.get("request_semantic_digest_sha256"),
        "semantic_digest_sha256": result.get("semantic_digest_sha256"),
    }


def _backend_unavailable_summaries(
    root: Path,
    requests: list[dict[str, Any]],
    cached_results: dict[
        tuple[str, int],
        tuple[dict[str, Any], Path],
    ],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for request in requests:
        key = (
            request["chart"],
            int(request["coefficient_modulus"]),
        )
        path = _certificate_path(root, request)
        cached_entry = cached_results.get(key)
        if cached_entry is not None:
            result, cached_path = cached_entry
            summaries.append(
                _run_summary(
                    root,
                    result,
                    cached_path,
                    cached=True,
                )
            )
            continue
        result = {
            "schema_version": SCHEMA_RESPONSE,
            "chart": request["chart"],
            "chart_cover_id": request["chart_cover_id"],
            "stratum": request["stratum"],
            "coefficient_field": (
                "QQ"
                if int(request["coefficient_modulus"]) == 0
                else f"GF({request['coefficient_modulus']})"
            ),
            "budget_file_sha256": request["budget_file_sha256"],
            "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
            "exit_status": "BACKEND_UNAVAILABLE",
            "chart_verdict": VERDICT_PARTIAL,
            "proof_eligible": False,
        }
        summaries.append(
            _run_summary(
                root,
                result,
                path,
                cached=False,
            )
        )
    return summaries


def _qq_resolves_noncommutativity(record: dict[str, Any]) -> bool:
    return bool(
        record["coefficient_field"] == "QQ"
        and record["exit_status"] == "COMPLETED"
        and record["proof_eligible"]
        and record["selected_canonical_equation_count"] == 2552
        and record["selected_matrix_relation_count"] == 976
        and record["selected_denominator_record_count"] == 191
        and record["canonical_selection_checks_passed"]
        and record["final_localisation_complete"]
        and record["commutator_coverage_complete"]
        and record["memory_budget_satisfied"]
        and record["chart_verdict"]
        in {
            "EXACT_EMPTY_CHART",
            "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART",
        }
    )


def _s3_structural_certificate(root: Path) -> dict[str, Any]:
    chart = next(chart for chart in stratum_charts(DERIVED_BRANCH) if chart.stratum == "S3_SCALAR")
    descriptor = build_chart_payload(
        DERIVED_BRANCH,
        chart.chart_id,
        expression_source="compact_arena",
    )
    passed = bool(
        chart.q_indices == (1, 2, 3, 4)
        and not descriptor["commutator_components"]
        and all(f"q{stage}_11" in descriptor["q_substitutions"] for stage in range(1, 5))
        and not any(name.startswith("q5_") for name in descriptor["q_substitutions"])
    )
    return {
        "chart_cover_id": chart.chart_id,
        "stratum": chart.stratum,
        "Q_indices": list(chart.q_indices),
        "substitution": ("Q2=lambda_2 Q1, Q3=lambda_3 Q1, Q4=lambda_4 Q1"),
        "commutator_component_count": len(descriptor["commutator_components"]),
        "proof_rule": (
            "Every Q_i for 1<=i<=4 is a scalar multiple of Q1, so all "
            "pairwise commutators vanish identically."
        ),
        "backend_run_required": False,
        "source_artifact": ("results/v0.3.2_cpobc_d2_classification.json"),
        "source_artifact_sha256": _sha256(root / "results/v0.3.2_cpobc_d2_classification.json"),
        "passed": passed,
    }


def verify_q5_free_campaign_v037(
    root: Path,
    *,
    campaign: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild every Phase 1 request and reject any unbound certificate."""

    budget = load_human_budget_v037(root)
    saved_partition = _load_json(root / PARTITION_PATH)
    partition_semantic_digest = stable_hash(
        {
            "partition": saved_partition.get("partition"),
            "shared_core": saved_partition.get("shared_core"),
            "excluded_path_family": saved_partition.get("excluded_path_family"),
            "denominators": saved_partition.get("denominators"),
            "forward_implication": saved_partition.get("forward_implication"),
            "verdict": saved_partition.get("verdict"),
        }
    )
    source_artifacts = saved_partition.get("source_artifacts", {})
    source_hashes_match = bool(
        len(source_artifacts) == 4
        and all(
            (root / path).is_file() and _sha256(root / path) == expected
            for path, expected in source_artifacts.items()
        )
    )
    partition_passed = bool(
        saved_partition.get("passed") is True
        and saved_partition.get("verdict") == "Q5_FREE_2552_PARTITION_CERTIFIED"
        and saved_partition.get("semantic_digest_sha256") == partition_semantic_digest
        and source_hashes_match
        and saved_partition.get("partition", {}).get("Q5_independent_count") == 2552
        and saved_partition.get("partition", {}).get("Q5_dependent_count") == 12
        and saved_partition.get("partition", {}).get("Q5_independent_equation_ids_sha256")
        == EXPECTED_FREE_EQUATION_DIGEST
        and saved_partition.get("partition", {}).get("Q5_independent_expression_ids_sha256")
        == EXPECTED_FREE_EXPRESSION_DIGEST
        and saved_partition.get("shared_core", {}).get("relation_family_counts")
        == EXPECTED_RELATION_FAMILY_COUNTS
        and saved_partition.get("denominators", {}).get("factor_ids_sha256")
        == EXPECTED_DENOMINATOR_DIGEST
    )
    aggregate = _load_json(root / CAMPAIGN_PATH) if campaign is None else campaign
    charts = _core_s1_s2_charts()
    requests = [
        build_q5_free_chart_request_v037(
            chart,
            saved_partition,
            budget,
            coefficient_modulus=modulus,
        )
        for modulus in (0, *SCOUT_MODULI)
        for chart in charts
    ]
    field_to_modulus = {
        "QQ": 0,
        **{f"GF({modulus})": modulus for modulus in SCOUT_MODULI},
    }
    runs = aggregate.get("runs", [])
    run_keys = [
        (
            record.get("chart"),
            field_to_modulus.get(record.get("coefficient_field")),
        )
        for record in runs
    ]
    run_keys_unique = len(run_keys) == len(set(run_keys))
    run_by_key = {
        key: record for key, record in zip(run_keys, runs, strict=True) if key[1] is not None
    }

    certificate_checks: list[dict[str, Any]] = []
    roles: Counter[str] = Counter()
    for request in requests:
        modulus = int(request["coefficient_modulus"])
        key = (request["chart"], modulus)
        run_record = run_by_key.get(key)
        path = _certificate_path(root, request)
        expected_relative = path.relative_to(root).as_posix()
        exists = path.is_file()
        certificate = _load_json(path) if exists else {}
        expected_role = "PHASE1_QQ_EXACT_PROOF" if modulus == 0 else f"PHASE1_GF{modulus}_SCOUT"
        roles[expected_role] += 1
        semantic_digest_matches = bool(
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
        )
        cached_gate_passes = bool(exists and _valid_cached_result(path, request) is not None)
        reconstructed_summary = (
            _run_summary(
                root,
                certificate,
                path,
                cached=bool(run_record.get("cached")),
            )
            if exists and run_record is not None
            else None
        )
        if modulus == 0:
            proof_role_passes = bool(
                certificate.get("proof_eligible") is True
                and certificate.get("identity_proof_eligible", False) is False
                and reconstructed_summary is not None
                and _qq_resolves_noncommutativity(reconstructed_summary)
            )
        else:
            proof_role_passes = bool(
                certificate.get("proof_eligible") is False
                and certificate.get("identity_proof_eligible", False) is False
            )
        summary_matches = reconstructed_summary == run_record
        checks = {
            "role": expected_role,
            "chart": request["chart"],
            "coefficient_modulus": modulus,
            "path": expected_relative,
            "certificate_exists": exists,
            "aggregate_record_exists": run_record is not None,
            "aggregate_path_matches": bool(
                run_record is not None and run_record.get("certificate") == expected_relative
            ),
            "raw_sha256_and_summary_match": summary_matches,
            "request_binding_and_selection_gates_pass": cached_gate_passes,
            "semantic_digest_recomputes": semantic_digest_matches,
            "exact_or_scout_role_gate_passes": proof_role_passes,
        }
        checks["passed"] = all(
            value
            for name, value in checks.items()
            if name
            not in {
                "role",
                "chart",
                "coefficient_modulus",
                "path",
            }
        )
        certificate_checks.append(checks)

    expected_keys = {
        (request["chart"], int(request["coefficient_modulus"])) for request in requests
    }
    actual_keys = {key for key in run_keys if key[1] is not None}
    expected_roles = Counter(
        {
            "PHASE1_QQ_EXACT_PROOF": 21,
            f"PHASE1_GF{SCOUT_MODULI[0]}_SCOUT": 21,
            f"PHASE1_GF{SCOUT_MODULI[1]}_SCOUT": 21,
        }
    )
    s3 = _s3_structural_certificate(root)
    budget_accounting = aggregate.get("budget_accounting", {})
    new_runtime = budget_accounting.get("new_invocation_elapsed_seconds")
    cached_runtime = budget_accounting.get("cached_authorised_runtime_seconds")
    aggregate_semantic_digest = stable_hash(
        {
            "partition": saved_partition["semantic_digest_sha256"],
            "runs": runs,
            "scout_agreement": aggregate.get("GF_scout_agreement"),
            "S3": aggregate.get("S3_structural_certificate"),
            "forward_implication": aggregate.get("literal_forward_implication"),
            "verdict": aggregate.get("verdict"),
        }
    )
    aggregate_checks = {
        "schema_matches": aggregate.get("schema_version") == SCHEMA_CAMPAIGN,
        "partition_passed": partition_passed,
        "budget_copy_matches_human_file": aggregate.get("budget") == budget,
        "selection_certificate_binding_matches": (
            aggregate.get("selection_certificate") == PARTITION_PATH
            and aggregate.get("selection_certificate_sha256") == _sha256(root / PARTITION_PATH)
        ),
        "budget_accounting_binding_valid": (
            budget_accounting.get("authorised_total_wall_time_seconds")
            == budget["total_wall_time_seconds"]
            and budget_accounting.get("effective_workers") == 1
            and budget_accounting.get("worker_policy")
            == "SEQUENTIAL_QQ_FIRST_FOR_BUDGET_AND_MEMORY_AUDIT"
            and budget_accounting.get("same_budget_terminal_results_are_not_retried") is True
            and budget_accounting.get("QQ_scheduled_first") is True
            and isinstance(new_runtime, (int, float))
            and 0 <= float(new_runtime) <= budget["total_wall_time_seconds"]
            and isinstance(cached_runtime, (int, float))
            and 0 <= float(cached_runtime) <= budget["total_wall_time_seconds"]
        ),
        "planned_run_count_is_63": aggregate.get("planned_run_count") == 63,
        "terminal_run_count_is_63": aggregate.get("completed_or_terminal_run_count") == 63,
        "run_count_is_63": len(runs) == 63,
        "run_keys_unique": run_keys_unique,
        "request_key_set_exact": actual_keys == expected_keys,
        "certificate_roles_exact": roles == expected_roles,
        "all_certificate_checks_pass": all(record["passed"] for record in certificate_checks),
        "QQ_exact_resolved_chart_count_is_21": aggregate.get("QQ_exact_resolved_chart_count") == 21,
        "phase1_proof_complete": aggregate.get("phase1_proof_complete") is True,
        "GF_scout_campaign_complete": aggregate.get("GF_scout_campaign_complete") is True,
        "GF_scout_agreement": aggregate.get("GF_scout_agreement") is True,
        "GF_scout_disagreements_empty": not aggregate.get("GF_scout_disagreements"),
        "S3_recomputes_exactly": aggregate.get("S3_structural_certificate") == s3,
        "forward_implication_proved_without_Q5": aggregate.get("literal_forward_implication")
        == {
            "Q5_free_shared_core_forces_Q1_Q4_commutativity": True,
            "literal_full_system_is_subset_of_shared_core_variety": True,
            "literal_full_system_Q1_Q4_commutativity": True,
            "Q5_behaviour_used": False,
        },
        "verdict_proved": aggregate.get("verdict") == VERDICT_PROVED,
        "global_verdict_open": aggregate.get("global_scientific_verdict") == "FINAL_THEORY_OPEN",
        "aggregate_semantic_digest_recomputes": aggregate.get("semantic_digest_sha256")
        == aggregate_semantic_digest,
    }
    passed = all(aggregate_checks.values())
    return {
        "schema_version": "final-theory-q5-free-verification-v0.3.7",
        "budget_file_sha256": budget["sha256"],
        "partition_semantic_digest_sha256": saved_partition["semantic_digest_sha256"],
        "certificate_role_counts": dict(sorted(roles.items())),
        "certificate_checks": certificate_checks,
        "aggregate_checks": aggregate_checks,
        "verdict": aggregate.get("verdict"),
        "global_scientific_verdict": aggregate.get("global_scientific_verdict"),
        "passed": passed,
    }


def run_q5_free_campaign_v037(root: Path) -> dict[str, Any]:
    """Run QQ first, then two finite-field scouts, within the human budget."""

    budget = load_human_budget_v037(root)
    partition = compile_q5_free_partition_v037(root)
    _write_json(root / PARTITION_PATH, partition)
    if not partition["passed"]:
        raise RuntimeError("Q5-free partition certificate failed")
    charts = _core_s1_s2_charts()
    backend = detect_sage_backend(root)
    aggregate_path = root / CAMPAIGN_PATH
    requests = [
        build_q5_free_chart_request_v037(
            chart,
            partition,
            budget,
            coefficient_modulus=modulus,
        )
        for modulus in (0, *SCOUT_MODULI)
        for chart in charts
    ]

    cached_results: dict[tuple[str, int], tuple[dict[str, Any], Path]] = {}
    consumed_previous_seconds = 0.0
    compact_preflight_path = root / COMPACT_PREFLIGHT_PATH
    compact_preflight_seconds = 0.0
    if compact_preflight_path.is_file():
        compact_preflight = _load_json(compact_preflight_path)
        compact_preflight_seconds = float(compact_preflight.get("wall_time_seconds", 0.0) or 0.0)
    for request in requests:
        path = _certificate_path(root, request)
        cached = _valid_cached_result(path, request)
        if cached is None:
            cached = _bound_terminal_result(path, request)
        if cached is None:
            continue
        key = (request["chart"], int(request["coefficient_modulus"]))
        cached_results[key] = (cached, path)
        consumed_previous_seconds += _result_wall_time_seconds(cached)

    remaining_authorised_seconds = max(
        0.0,
        float(budget["total_wall_time_seconds"])
        - consumed_previous_seconds
        - compact_preflight_seconds,
    )
    started = time.perf_counter()
    deadline = started + remaining_authorised_seconds
    summaries: list[dict[str, Any]] = []

    def write_progress() -> None:
        qq = [record for record in summaries if record["coefficient_field"] == "QQ"]
        exact_resolved = [record["chart"] for record in qq if _qq_resolves_noncommutativity(record)]
        survivor = [
            record["chart"]
            for record in qq
            if record["chart_verdict"] == "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
        ]
        unresolved = [
            _campaign_chart_id(chart.chart_id)
            for chart in charts
            if _campaign_chart_id(chart.chart_id) not in exact_resolved
        ]
        payload = {
            "schema_version": SCHEMA_CAMPAIGN,
            "branch": BRANCH,
            "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
            "finite_scope": "frozen source stages n<=4",
            "backend": backend,
            "budget": budget,
            "budget_accounting": {
                "cached_authorised_runtime_seconds": (consumed_previous_seconds),
                "compact_preflight_timeout_seconds": (compact_preflight_seconds),
                "compact_preflight_certificate": (
                    COMPACT_PREFLIGHT_PATH if compact_preflight_path.is_file() else None
                ),
                "new_invocation_elapsed_seconds": (time.perf_counter() - started),
                "authorised_total_wall_time_seconds": budget["total_wall_time_seconds"],
                "effective_workers": 1,
                "worker_policy": ("SEQUENTIAL_QQ_FIRST_FOR_BUDGET_AND_MEMORY_AUDIT"),
                "same_budget_terminal_results_are_not_retried": True,
                "QQ_scheduled_first": True,
            },
            "selection_certificate": PARTITION_PATH,
            "selection_certificate_sha256": _sha256(root / PARTITION_PATH),
            "chart_geometry": {
                "source": DERIVED_BRANCH,
                "ratio_indices": [2, 3, 4],
                "R5_included": False,
                "Q5_variable_introduced": False,
                "S1_chart_count": 12,
                "S2_chart_count": 9,
                "S1_S2_chart_count": 21,
                "chart_cover_ids": [chart.chart_id for chart in charts],
            },
            "equation_system": {
                "source_branch": LITERAL_BRANCH,
                "canonical_numerator_count": 2552,
                "matrix_relation_count": 976,
                "relation_family_counts": (EXPECTED_RELATION_FAMILY_COUNTS),
                "excluded_path_relation_count": 25,
                "excluded_Q5_dependent_canonical_numerator_count": 12,
                "denominator_factor_count": 191,
            },
            "coefficient_fields": {
                "proof_field": "QQ",
                "scout_fields": [f"GF({modulus})" for modulus in SCOUT_MODULI],
                "GF_results_are_proof": False,
            },
            "planned_run_count": len(requests),
            "completed_or_terminal_run_count": len(summaries),
            "runs": sorted(
                summaries,
                key=lambda record: (
                    0 if record["coefficient_field"] == "QQ" else 1,
                    record["coefficient_field"] or "",
                    record["chart"] or "",
                ),
            ),
            "QQ_exact_resolved_chart_count": len(exact_resolved),
            "QQ_exact_resolved_charts": sorted(exact_resolved),
            "shared_core_noncommutative_components": sorted(survivor),
            "unresolved_S1_S2_charts": sorted(unresolved),
            "phase1_proof_complete": len(exact_resolved) == len(charts),
            "exact_numeric_distinction": (
                "Only completed proof-eligible QQ certificates decide the "
                "theorem; both finite fields are scouts."
            ),
            "global_scientific_verdict": "FINAL_THEORY_OPEN",
            "verdict": (VERDICT_PROVED if len(exact_resolved) == len(charts) else VERDICT_PARTIAL),
        }
        payload["semantic_digest_sha256"] = stable_hash(
            {
                "selection_certificate_sha256": payload["selection_certificate_sha256"],
                "runs": payload["runs"],
                "QQ_exact_resolved_charts": payload["QQ_exact_resolved_charts"],
                "unresolved": payload["unresolved_S1_S2_charts"],
                "verdict": payload["verdict"],
            }
        )
        _write_json(aggregate_path, payload)

    if not backend.get("available"):
        summaries.extend(
            _backend_unavailable_summaries(
                root,
                requests,
                cached_results,
            )
        )
        write_progress()
    execution_requests = requests if backend.get("available") else []

    for request in execution_requests:
        key = (request["chart"], int(request["coefficient_modulus"]))
        cached_entry = cached_results.get(key)
        if cached_entry is not None:
            result, path = cached_entry
            summaries.append(_run_summary(root, result, path, cached=True))
            write_progress()
            continue

        remaining = deadline - time.perf_counter()
        path = _certificate_path(root, request)
        if remaining < 1.0:
            result = {
                "schema_version": SCHEMA_RESPONSE,
                "chart": request["chart"],
                "chart_cover_id": request["chart_cover_id"],
                "stratum": request["stratum"],
                "coefficient_field": (
                    "QQ"
                    if int(request["coefficient_modulus"]) == 0
                    else f"GF({request['coefficient_modulus']})"
                ),
                "exit_status": "NOT_RUN_TOTAL_BUDGET_EXHAUSTED",
                "chart_verdict": VERDICT_PARTIAL,
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
        summary = _run_summary(root, result, path, cached=False)
        summaries.append(summary)
        write_progress()
        print(
            f"[{len(summaries)}/{len(requests)}] "
            f"{summary['coefficient_field']} {summary['chart']} "
            f"{summary['exit_status']} {summary['chart_verdict']}",
            flush=True,
        )

    final = _load_json(aggregate_path)
    field_maps = {
        field: {
            record["chart"]: record["chart_verdict"]
            for record in final["runs"]
            if record["coefficient_field"] == field and record["exit_status"] == "COMPLETED"
        }
        for field in (f"GF({SCOUT_MODULI[0]})", f"GF({SCOUT_MODULI[1]})")
    }
    all_chart_ids = {_campaign_chart_id(chart.chart_id) for chart in charts}
    scout_complete = all(set(records) == all_chart_ids for records in field_maps.values())
    disagreements = sorted(
        chart_id
        for chart_id in all_chart_ids
        if field_maps[f"GF({SCOUT_MODULI[0]})"].get(chart_id)
        != field_maps[f"GF({SCOUT_MODULI[1]})"].get(chart_id)
    )
    s3 = _s3_structural_certificate(root)
    theorem_proved = bool(final["phase1_proof_complete"] and s3["passed"] and partition["passed"])
    final.update(
        {
            "GF_scout_campaign_complete": scout_complete,
            "GF_scout_agreement": scout_complete and not disagreements,
            "GF_scout_disagreements": disagreements,
            "S3_structural_certificate": s3,
            "complete_chart_cover": {
                "S1_S2_QQ_resolved_count": final["QQ_exact_resolved_chart_count"],
                "S3_structurally_resolved": s3["passed"],
                "Q5_or_R5_used": False,
                "all_R2_R3_R4_commuting_ratio_strata_covered": (theorem_proved),
            },
            "literal_forward_implication": {
                "Q5_free_shared_core_forces_Q1_Q4_commutativity": (theorem_proved),
                "literal_full_system_is_subset_of_shared_core_variety": True,
                "literal_full_system_Q1_Q4_commutativity": theorem_proved,
                "Q5_behaviour_used": False,
            },
            "phase1_proof_complete": theorem_proved,
            "unresolved_components": (
                []
                if theorem_proved
                else [
                    *final["unresolved_S1_S2_charts"],
                    *([] if s3["passed"] else ["S3 structural certificate"]),
                ]
            ),
            "verdict": VERDICT_PROVED if theorem_proved else VERDICT_PARTIAL,
        }
    )
    final["semantic_digest_sha256"] = stable_hash(
        {
            "partition": partition["semantic_digest_sha256"],
            "runs": final["runs"],
            "scout_agreement": final["GF_scout_agreement"],
            "S3": s3,
            "forward_implication": final["literal_forward_implication"],
            "verdict": final["verdict"],
        }
    )
    _write_json(aggregate_path, final)
    return final


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-partition", action="store_true")
    parser.add_argument("--run-campaign", action="store_true")
    parser.add_argument("--run-phase1", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _argument_parser().parse_args(argv)
    root = Path.cwd()
    if arguments.compile_partition:
        payload = compile_q5_free_partition_v037(root)
        _write_json(root / PARTITION_PATH, payload)
        return 0 if payload["passed"] else 1
    if arguments.run_campaign or arguments.run_phase1:
        payload = run_q5_free_campaign_v037(root)
        return 0 if payload["verdict"] == VERDICT_PROVED else 1
    raise SystemExit("select --compile-partition or --run-campaign")


if __name__ == "__main__":
    raise SystemExit(main())
