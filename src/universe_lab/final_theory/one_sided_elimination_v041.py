"""Exact QQ-only elimination campaign for two restricted v0.4.1 loci.

The 721- and 955-relation systems are selected directly from the frozen
reduced-operator system.  They do *not* materialise the two weak vector
semantics: Eq. (112) and Eq. (108), respectively, retain strong assumptions in
the Q-coordinate reconstruction.  Consequently their exact computations
certify commutativity only on the corresponding frozen Q-reconstruction image,
not on either full one-sided profile.

The worker is deliberately invoked only through
:func:`run_one_sided_qq_campaign_v041`; manifest compilation never starts Sage,
Singular, or a finite-field scout.  Historical artifacts bearing the withdrawn
full-profile verdict remain at their original paths; all new writes use the
``restricted_locus`` paths below.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter
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
from universe_lab.final_theory.solver_authorization_v042 import (
    require_production_solver_authorization,
)

SCHEMA_MANIFEST = "final-theory-one-sided-d2-qq-restricted-locus-manifest-v0.4.1"
SCHEMA_REQUEST = "final-theory-one-sided-d2-qq-request-v0.4.1"
SCHEMA_RESPONSE = "final-theory-one-sided-d2-qq-response-v0.4.1"
SCHEMA_CAMPAIGN = "final-theory-one-sided-d2-qq-restricted-locus-campaign-v0.4.1"
BUDGET_PATH = "config/v0.4.1_budget.json"
INVENTORY_PATH = "results/v0.4.1_one_sided_inventory.json"
HISTORICAL_MANIFEST_PATH = "results/v0.4.1_one_sided_elimination_manifest.json"
HISTORICAL_CAMPAIGN_PATH = "results/v0.4.1_one_sided_elimination.json"
MANIFEST_PATH = "results/v0.4.1_one_sided_restricted_locus_manifest.json"
CAMPAIGN_PATH = "results/v0.4.1_one_sided_restricted_locus_campaign.json"
HISTORICAL_CERTIFICATE_ROOT = "certificates/d2_saturation/one_sided_v041"
CERTIFICATE_ROOT = "certificates/d2_saturation/one_sided_v041_restricted_locus"

PROFILE_STRONG_MSR = "fixed_vector_GC__strong_MSR"
PROFILE_STRONG_GC = "strong_GC__reachable_state_MSR"
PROFILES = (PROFILE_STRONG_MSR, PROFILE_STRONG_GC)
PROFILE_SPECS: dict[str, dict[str, Any]] = {
    PROFILE_STRONG_MSR: {
        "selection_label": "CPOBC_PLUS_STRONG_MSR_721",
        "families": ("CPOBC", "STRONG_OPERATOR_MSR"),
        "family_counts": {"CPOBC": 700, "STRONG_OPERATOR_MSR": 21},
        "relation_count": 721,
        "restricted_locus_rule": (
            "The 721 relations are certified only on the frozen Q-reconstruction "
            "image; Eq. (112) retains strong-GC structure, so no implication to "
            "the full fixed-vector-GC plus strong-MSR profile is permitted."
        ),
        "hidden_reduction_dependency": "Eq. (112) / strong-GC path consistency",
    },
    PROFILE_STRONG_GC: {
        "selection_label": "CPOBC_PLUS_STRONG_GC_955",
        "families": ("CPOBC", "LOCAL_OPERATOR_GC"),
        "family_counts": {"CPOBC": 700, "LOCAL_OPERATOR_GC": 255},
        "relation_count": 955,
        "restricted_locus_rule": (
            "The 955 relations are certified only on the frozen Q-reconstruction "
            "image; Eq. (108) retains strong-MSR structure, so no implication to "
            "the full strong-GC plus reachable-state-MSR profile is permitted."
        ),
        "hidden_reduction_dependency": "Eq. (108) / strong-operator MSR elimination",
    },
}

WITHDRAWN_FULL_PROFILE_VERDICT = "WEAK_D2_ON_ONE_SIDED_COMMUTATIVITY_PROVED"
VERDICT_MANIFEST_READY = "V041_RESTRICTED_LOCUS_QQ_MANIFEST_READY_SOLVER_NOT_RUN"
VERDICT_RESTRICTED_LOCUS_PROVED = "V041_ON_Q_RECONSTRUCTION_RESTRICTED_LOCUS_COMMUTATIVITY_PROVED"
VERDICT_RESTRICTED_SELECTED_LOCUS_PROVED = (
    "V041_ON_Q_RECONSTRUCTION_SELECTED_RESTRICTED_LOCUS_COMMUTATIVITY_PROVED"
)
VERDICT_RESTRICTED_PROFILE_PROVED = "V041_ON_Q_RECONSTRUCTION_PROFILE_LOCUS_PROVED"
VERDICT_OPEN = "V041_RESTRICTED_LOCUS_OPEN_RESOURCE_LIMIT"
VERDICT_COMPONENT_SURVIVES = "V041_RESTRICTED_LOCUS_COMPONENT_SURVIVES_NOT_A_WITNESS"

SEMANTIC_SCOPE_ID = "V041_FROZEN_Q_RECONSTRUCTION_IMAGE_RESTRICTED_LOCUS"


def _semantic_scope_record() -> dict[str, Any]:
    """Return the mandatory fail-closed scope declaration for new artifacts."""

    return {
        "scope_id": SEMANTIC_SCOPE_ID,
        "classification": "RESTRICTED_LOCUS_ONLY",
        "profile_native_coverage_certified": False,
        "full_profile_forward_implication_permitted": False,
        "full_profile_commutativity_claimed": False,
        "full_profile_theorem_status": "WITHDRAWN_AND_OPEN",
        "withdrawn_legacy_verdict": WITHDRAWN_FULL_PROFILE_VERDICT,
        "withdrawn_legacy_verdict_status": "HISTORICAL_ONLY_NOT_CURRENT_OR_TERMINAL",
        "scope_statement": (
            "Only the intersections of the intended one-sided profiles with the "
            "frozen v0.3.5 Q-reconstruction image are covered."
        ),
    }


def validate_current_semantic_scope_v041(payload: dict[str, Any]) -> None:
    """Reject any new payload that could be read as a full-profile theorem."""

    scope = payload.get("semantic_scope")
    required = _semantic_scope_record()
    if not isinstance(scope, dict) or any(
        scope.get(key) != value for key, value in required.items()
    ):
        raise ValueError("v0.4.1 current artifact lacks the fail-closed restricted-locus scope")
    for key in ("verdict", "terminal_verdict"):
        if payload.get(key) == WITHDRAWN_FULL_PROFILE_VERDICT:
            raise ValueError(f"withdrawn full-profile verdict cannot be emitted as {key}")
    for container_name in ("profiles", "profile_results"):
        container = payload.get(container_name, {})
        if not isinstance(container, dict):
            raise ValueError(f"v0.4.1 {container_name} must be a mapping")
        for profile, record in container.items():
            if not isinstance(record, dict):
                raise ValueError(f"v0.4.1 {container_name}.{profile} must be a mapping")
            if record.get("full_profile_forward_implication_permitted") is not False:
                raise ValueError(f"v0.4.1 {profile} does not forbid full-profile implication")
            if record.get("profile_native_coverage_certified") is not False:
                raise ValueError(f"v0.4.1 {profile} incorrectly claims profile-native coverage")
            if record.get("full_profile_commutativity_proved_by_forward_implication", False):
                raise ValueError(f"v0.4.1 {profile} reintroduces the withdrawn forward theorem")


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


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


def _request_digest(request: dict[str, Any]) -> str:
    return stable_hash(
        {
            key: value
            for key, value in request.items()
            if key not in {"request_id", "request_semantic_digest_sha256"}
        }
    )


def load_human_budget_v041(root: Path) -> dict[str, Any]:
    """Read the v0.4.1 human budget, with no inherited default."""

    path = root.resolve() / BUDGET_PATH
    if not path.is_file():
        raise FileNotFoundError(f"external budget file is required: {BUDGET_PATH}")
    supplied = _load_json(path)
    required = {
        "timeout_seconds_per_chart",
        "total_wall_time_seconds",
        "memory_limit_gib",
    }
    missing = sorted(required - supplied.keys())
    unsupported = sorted(supplied.keys() - required)
    if missing:
        raise ValueError(f"v0.4.1 budget is missing required keys: {missing}")
    if unsupported:
        raise ValueError(f"v0.4.1 budget has unsupported keys: {unsupported}")
    values: dict[str, float] = {}
    for name in sorted(required):
        value = supplied[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"v0.4.1 budget {name} must be numeric")
        if not math.isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"v0.4.1 budget {name} must be positive and finite")
        values[name] = float(value)
    if values["timeout_seconds_per_chart"] > values["total_wall_time_seconds"]:
        raise ValueError("v0.4.1 per-chart timeout cannot exceed total wall time")
    return {
        "provenance": "EXTERNAL_REPOSITORY_BUDGET_FILE; NO_RUNTIME_DEFAULTS_OR_SELF_AUTHENTICATION",
        "path": BUDGET_PATH,
        "sha256": _sha256(path),
        "timeout_seconds_per_chart": int(values["timeout_seconds_per_chart"]),
        "total_wall_time_seconds": int(values["total_wall_time_seconds"]),
        "memory_limit_gib": values["memory_limit_gib"],
        "memory_limit_bytes": int(values["memory_limit_gib"] * 1024**3),
    }


def _core_charts() -> list[Any]:
    charts = [chart for chart in stratum_charts(DERIVED_BRANCH) if chart.stratum in {S1, S2}]
    distribution = Counter(chart.stratum for chart in charts)
    if len(charts) != 21 or distribution != Counter({S1: 12, S2: 9}):
        raise RuntimeError("the frozen R2--R4 S1/S2 cover is not the expected 21-chart cover")
    return charts


def _campaign_chart_id(profile: str, cover_chart_id: str) -> str:
    _, suffix = cover_chart_id.split(":", 1)
    return f"{profile}:{suffix}"


def _load_inventory_core(root: Path, profile: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if profile not in PROFILE_SPECS:
        raise ValueError(f"unknown v0.4.1 profile: {profile}")
    inventory_path = root / INVENTORY_PATH
    if not inventory_path.is_file():
        raise FileNotFoundError(f"v0.4.1 inventory is required: {INVENTORY_PATH}")
    inventory = _load_json(inventory_path)
    if inventory.get("schema_version") != "final-theory-one-sided-d2-v0.4.1":
        raise ValueError("unexpected v0.4.1 inventory schema")
    expected_digest = inventory.get("semantic_digest_sha256")
    actual_digest = stable_hash(
        {key: value for key, value in inventory.items() if key != "semantic_digest_sha256"}
    )
    if expected_digest != actual_digest:
        raise ValueError("v0.4.1 inventory semantic digest does not recompute")
    source_hashes = inventory.get("source_artifacts", {})
    direct_path = "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
    if source_hashes.get(direct_path) != _sha256(root / direct_path):
        raise ValueError("frozen direct-operator system hash no longer matches v0.4.1 inventory")
    relation_record = inventory["q5_free_relation_inventory"].get(profile)
    if not isinstance(relation_record, dict):
        raise ValueError(f"inventory lacks relation set for {profile}")
    ids = sorted(str(value) for value in relation_record.get("ids", []))
    spec = PROFILE_SPECS[profile]
    if (
        len(ids) != spec["relation_count"]
        or relation_record.get("count") != spec["relation_count"]
        or relation_record.get("sha256") != stable_hash(ids)
    ):
        raise ValueError(f"inventory relation set integrity failed for {profile}")
    direct = _load_json(root / direct_path)
    direct_semantic_digest = stable_hash(
        {
            "dependency_nodes": direct["dependency_nodes"],
            "relations": direct["relations"],
            "transitions": direct["reconstructed_transition_predicates"],
        }
    )
    if direct.get("semantic_digest_sha256") != direct_semantic_digest:
        raise ValueError("frozen direct-operator system semantic digest does not recompute")
    records = direct["relations"][LITERAL_BRANCH]
    by_id = {record["relation_id"]: record for record in records}
    if set(ids) - set(by_id):
        raise ValueError(
            f"inventory relation IDs absent from frozen literal direct system: {profile}"
        )
    selected_counts = dict(
        sorted(Counter(by_id[identifier]["family"] for identifier in ids).items())
    )
    if selected_counts != spec["family_counts"]:
        raise ValueError(f"inventory family partition failed for {profile}")
    return inventory, {
        "ids": ids,
        "sha256": stable_hash(ids),
        "family_counts": selected_counts,
        "direct_system_semantic_digest_sha256": direct_semantic_digest,
    }


def build_one_sided_chart_request_v041(
    root: Path,
    profile: str,
    chart: Any,
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Build one bounded direct-operator QQ request without executing it."""

    inventory, core = _load_inventory_core(root, profile)
    spec = PROFILE_SPECS[profile]
    request = build_chart_payload(
        DERIVED_BRANCH,
        chart.chart_id,
        coefficient_modulus=0,
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
    request.update(
        {
            "schema_version": SCHEMA_REQUEST,
            "response_schema_version": SCHEMA_RESPONSE,
            "chart": _campaign_chart_id(profile, chart.chart_id),
            "chart_cover_id": chart.chart_id,
            "chart_source_index_branch": DERIVED_BRANCH,
            "equation_source_index_branch": LITERAL_BRANCH,
            "source_index_branch": LITERAL_BRANCH,
            "profile": profile,
            "selection_label": spec["selection_label"],
            # The direct worker's historical ``selection_certificate`` field
            # means a *canonical-numerator* equivalence assertion.  These
            # requests intentionally select the direct matrix relations
            # themselves, so bind the inventory under distinct names instead.
            "inventory_path": INVENTORY_PATH,
            "inventory_semantic_digest_sha256": inventory["semantic_digest_sha256"],
            "included_relation_families": list(spec["families"]),
            "forbidden_relation_families": sorted(
                {"CPOBC", "LOCAL_OPERATOR_GC", "STRONG_OPERATOR_MSR"} - set(spec["families"])
                | {"EQ112_PATH_CONSISTENCY"}
            ),
            "expected_selected_relation_count": spec["relation_count"],
            "expected_selected_relation_ids_sha256": core["sha256"],
            "expected_relation_family_counts": spec["family_counts"],
            "expected_direct_system_file_sha256": inventory["source_artifacts"][
                "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
            ],
            "expected_direct_system_semantic_digest_sha256": core[
                "direct_system_semantic_digest_sha256"
            ],
            "memory_limit_bytes": budget["memory_limit_bytes"],
            "budget_file": BUDGET_PATH,
            "budget_file_sha256": budget["sha256"],
            "authorised_timeout_seconds_per_run": budget["timeout_seconds_per_chart"],
            "authorised_total_wall_time_seconds": budget["total_wall_time_seconds"],
            "finite_field_fallback_permitted": False,
        }
    )
    if any(name.startswith("q5_") for name in request["q_substitutions"]):
        raise RuntimeError("Q5 leaked into a v0.4.1 R2--R4 chart request")
    if any(5 in component["pair"] for component in request["commutator_components"]):
        raise RuntimeError("Q5 commutator leaked into a v0.4.1 R2--R4 chart request")
    if request["coefficient_modulus"] != 0:
        raise RuntimeError("v0.4.1 one-sided campaign must be QQ-only")
    request["request_semantic_digest_sha256"] = _request_digest(request)
    return request


def _s3_structural_certificate() -> dict[str, Any]:
    """Bind the scalar-ratio chart that needs no ideal computation."""

    chart = next(chart for chart in stratum_charts(DERIVED_BRANCH) if chart.stratum == "S3_SCALAR")
    descriptor = build_chart_payload(
        DERIVED_BRANCH,
        chart.chart_id,
        expression_source="direct_operator",
    )
    passed = bool(
        chart.q_indices == (1, 2, 3, 4)
        and not descriptor["commutator_components"]
        and all(f"q{stage}_11" in descriptor["q_substitutions"] for stage in range(1, 5))
        and not any(name.startswith("q5_") for name in descriptor["q_substitutions"])
    )
    if not passed:
        raise RuntimeError("the frozen scalar-ratio chart is not structurally resolved")
    return {
        "chart_cover_id": chart.chart_id,
        "stratum": chart.stratum,
        "Q_indices": list(chart.q_indices),
        "substitution": "Q2=lambda_2 Q1, Q3=lambda_3 Q1, Q4=lambda_4 Q1",
        "commutator_component_count": len(descriptor["commutator_components"]),
        "proof_rule": (
            "Every Q_i for 1<=i<=4 is a scalar multiple of Q1, so all pairwise "
            "commutators vanish identically."
        ),
        "backend_run_required": False,
        "passed": True,
    }


def compile_one_sided_qq_manifest_v041(
    root: Path,
    *,
    profiles: tuple[str, ...] = PROFILES,
) -> dict[str, Any]:
    """Compile the exact-Q-only schedule.  This function has no solver side effect."""

    root = root.resolve()
    budget = load_human_budget_v041(root)
    charts = _core_charts()
    if not profiles or set(profiles) - set(PROFILES) or len(set(profiles)) != len(profiles):
        raise ValueError("profiles must be a nonempty duplicate-free subset of the v0.4.1 profiles")
    requests = [
        build_one_sided_chart_request_v041(root, profile, chart, budget)
        for profile in profiles
        for chart in charts
    ]
    inventory, _ = _load_inventory_core(root, profiles[0])
    chart_reuse = inventory["chart_reuse_boundary"]["ON_QUOTIENT"]
    exact_check = chart_reuse["independent_exact_check"]
    if not (
        exact_check["Eq120_ratio_commutation_identity"]["verified"] is True
        and exact_check["all_R2_R3_R4_commuting_ratio_strata_covered"] is True
        and chart_reuse["chart_count"] == 21
    ):
        raise ValueError("v0.4.1 inventory does not certify reuse of the 21-chart ON cover")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_MANIFEST,
        "finite_scope": (
            "ON quotient frozen Q-reconstruction image only; n<=4; d=2; exact QQ only"
        ),
        "semantic_scope": _semantic_scope_record(),
        "budget": budget,
        "inventory": {
            "path": INVENTORY_PATH,
            "sha256": _sha256(root / INVENTORY_PATH),
            "semantic_digest_sha256": inventory["semantic_digest_sha256"],
        },
        "chart_cover": {
            "chart_source_index_branch": DERIVED_BRANCH,
            "ratio_indices": [2, 3, 4],
            "S1_chart_count": 12,
            "S2_chart_count": 9,
            "S1_S2_chart_count": 21,
            "Eq120_ratio_commutation_identity": exact_check["Eq120_ratio_commutation_identity"],
            "S3_structural_certificate": _s3_structural_certificate(),
        },
        "profiles": {
            profile: {
                "core_relation_count": PROFILE_SPECS[profile]["relation_count"],
                "included_relation_families": list(PROFILE_SPECS[profile]["families"]),
                "relation_family_counts": PROFILE_SPECS[profile]["family_counts"],
                "restricted_locus_rule": PROFILE_SPECS[profile]["restricted_locus_rule"],
                "hidden_reduction_dependency": PROFILE_SPECS[profile][
                    "hidden_reduction_dependency"
                ],
                "profile_native_coverage_certified": False,
                "full_profile_forward_implication_permitted": False,
                "full_profile_commutativity_proved_by_forward_implication": False,
            }
            for profile in profiles
        },
        "coefficient_fields": {
            "scheduled": ["QQ"],
            "finite_field_scouts_scheduled": False,
            "finite_field_fallback_permitted": False,
            "proof_field": "QQ",
        },
        "requests": requests,
        "planned_run_count": len(requests),
        "execution": {
            "solver_invoked": False,
            "explicit_execution_flag_required": "--run-qq",
            "worker_policy": "SEQUENTIAL_QQ_ONLY_ACROSS_BOTH_PROFILES",
            "same_budget_terminal_results_are_not_retried": True,
        },
        "verdict": VERDICT_MANIFEST_READY,
    }
    validate_current_semantic_scope_v041(payload)
    payload["semantic_digest_sha256"] = stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )
    return payload


def write_one_sided_qq_manifest_v041(root: Path, payload: dict[str, Any]) -> Path:
    validate_current_semantic_scope_v041(payload)
    expected_digest = stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )
    if payload.get("semantic_digest_sha256") != expected_digest:
        raise ValueError("v0.4.1 restricted-locus manifest semantic digest does not recompute")
    path = root.resolve() / MANIFEST_PATH
    _write_json(path, payload)
    return path


def _certificate_path_for_root(root: Path, request: dict[str, Any], certificate_root: str) -> Path:
    budget = request["budget_file_sha256"][:16]
    digest = request["request_semantic_digest_sha256"][:24]
    return (
        root / certificate_root / f"budget-{budget}" / request["profile"] / "QQ" / f"{digest}.json"
    )


def _certificate_path(root: Path, request: dict[str, Any]) -> Path:
    """Return the write target for scope-corrected campaign certificates."""

    return _certificate_path_for_root(root, request, CERTIFICATE_ROOT)


def _historical_certificate_path(root: Path, request: dict[str, Any]) -> Path:
    """Return the immutable legacy-cache path used only for bound reads."""

    return _certificate_path_for_root(root, request, HISTORICAL_CERTIFICATE_ROOT)


def _memory_limit_matches(result: dict[str, Any], request: dict[str, Any]) -> bool:
    limit = result.get("resource_usage", {}).get("memory_limit")
    if not isinstance(limit, dict):
        return False
    requested = int(request["memory_limit_bytes"])
    effective = limit.get("effective_limit_bytes")
    return bool(
        limit.get("requested") is True
        and limit.get("applied") is True
        and limit.get("resource") == "RLIMIT_AS"
        and limit.get("limit_bytes") == requested
        and isinstance(effective, int)
        and 0 < effective <= requested
    )


def _bound_terminal_result(path: Path, request: dict[str, Any]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        result = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    if (
        result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("chart") == request["chart"]
        and result.get("coefficient_field") == "QQ"
        and result.get("coefficient_modulus") == 0
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and result.get("selection_label") == request["selection_label"]
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
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            return float(value)
    return 0.0


def _result_semantic_digest_matches(result: dict[str, Any]) -> bool:
    """Reject a certificate whose bound result fields were later changed."""

    try:
        recomputed = _result_semantic_digest(
            result,
            selection_fields=(
                "selection_label",
                "selected_relation_ids_sha256",
                "selected_equation_ids_sha256",
            ),
        )
    except KeyError:
        return False
    return result.get("semantic_digest_sha256") == recomputed


def qq_resolves_noncommutativity_v041(result: dict[str, Any], request: dict[str, Any]) -> bool:
    """A chart closes only under a complete, bound, exact QQ certificate."""

    return bool(
        result.get("schema_version") == SCHEMA_RESPONSE
        and result.get("exit_status") == "COMPLETED"
        and result.get("coefficient_field") == "QQ"
        and result.get("coefficient_modulus") == 0
        and result.get("proof_eligible") is True
        and _result_semantic_digest_matches(result)
        and result.get("chart") == request["chart"]
        and result.get("budget_file_sha256") == request["budget_file_sha256"]
        and result.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"]
        and result.get("selection_label") == request["selection_label"]
        and result.get("direct_system_file_sha256") == request["expected_direct_system_file_sha256"]
        and result.get("direct_system_semantic_digest_sha256")
        == request["expected_direct_system_semantic_digest_sha256"]
        and result.get("direct_system_self_semantic_digest_valid") is True
        and result.get("selected_matrix_relation_count")
        == request["expected_selected_relation_count"]
        and result.get("selected_relation_ids_sha256")
        == request["expected_selected_relation_ids_sha256"]
        and result.get("selected_relation_family_counts")
        == request["expected_relation_family_counts"]
        and result.get("relation_selection_checks_passed") is True
        and result.get("saturation_requested") is True
        and result.get("final_localisation_complete") is True
        and result.get("commutator_coverage_complete") is True
        and result.get("resource_usage", {}).get("memory_budget_satisfied") is True
        and _memory_limit_matches(result, request)
        and result.get("chart_verdict")
        in {"EXACT_EMPTY_CHART", "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART"}
    )


def _run_summary(
    root: Path, result: dict[str, Any], path: Path, request: dict[str, Any], *, cached: bool
) -> dict[str, Any]:
    return {
        "profile": request["profile"],
        "chart": request["chart"],
        "chart_cover_id": request["chart_cover_id"],
        "stratum": request["stratum"],
        "coefficient_field": result.get("coefficient_field", "QQ"),
        "exit_status": result.get("exit_status"),
        "chart_verdict": result.get("chart_verdict"),
        "exact_chart_closed": qq_resolves_noncommutativity_v041(result, request),
        "saturated_unit_ideal": result.get("saturated_unit_ideal", False),
        "selected_matrix_relation_count": result.get("selected_matrix_relation_count"),
        "selected_relation_ids_sha256": result.get("selected_relation_ids_sha256"),
        "selected_relation_family_counts": result.get("selected_relation_family_counts"),
        "relation_selection_checks_passed": result.get("relation_selection_checks_passed", False),
        "final_localisation_complete": result.get("final_localisation_complete", False),
        "commutator_coverage_complete": result.get("commutator_coverage_complete", False),
        "surviving_noncommutative_component_count": result.get(
            "surviving_noncommutative_component_count"
        ),
        "worker_wall_time_seconds": result.get("resource_usage", {}).get("wall_time_seconds"),
        "peak_rss_bytes": result.get("resource_usage", {}).get("peak_rss_bytes"),
        "memory_budget_satisfied": result.get("resource_usage", {}).get(
            "memory_budget_satisfied", False
        ),
        "cached": cached,
        "certificate": path.relative_to(root).as_posix(),
        "certificate_sha256": _sha256(path) if path.is_file() else None,
        "budget_file_sha256": result.get("budget_file_sha256"),
        "request_semantic_digest_sha256": result.get("request_semantic_digest_sha256"),
        "semantic_digest_sha256": result.get("semantic_digest_sha256"),
    }


def _not_run_result(request: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_RESPONSE,
        "chart": request["chart"],
        "chart_cover_id": request["chart_cover_id"],
        "stratum": request["stratum"],
        "profile": request["profile"],
        "coefficient_field": "QQ",
        "coefficient_modulus": 0,
        "budget_file_sha256": request["budget_file_sha256"],
        "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
        "selection_label": request["selection_label"],
        "exit_status": status,
        "chart_verdict": VERDICT_OPEN,
        "proof_eligible": False,
    }


def _profile_status(
    profile: str, requests: list[dict[str, Any]], summaries: list[dict[str, Any]]
) -> dict[str, Any]:
    profile_requests = [request for request in requests if request["profile"] == profile]
    by_chart = {summary["chart"]: summary for summary in summaries if summary["profile"] == profile}
    closed = [
        request["chart"]
        for request in profile_requests
        if by_chart.get(request["chart"], {}).get("exact_chart_closed")
    ]
    survivors = [
        request["chart"]
        for request in profile_requests
        if by_chart.get(request["chart"], {}).get("chart_verdict")
        == "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
    ]
    unresolved = sorted(set(request["chart"] for request in profile_requests) - set(closed))
    proved = len(closed) == len(profile_requests)
    return {
        "profile": profile,
        "QQ_exact_resolved_chart_count": len(closed),
        "QQ_exact_resolved_charts": sorted(closed),
        "noncommutative_component_survivor_charts": sorted(survivors),
        "unresolved_S1_S2_charts": unresolved,
        "S3_structurally_resolved": True,
        "core_commutativity_proved": proved,
        "restricted_locus_commutativity_proved": proved,
        "profile_native_coverage_certified": False,
        "full_profile_forward_implication_permitted": False,
        "full_profile_commutativity_proved_by_forward_implication": False,
        "full_profile_status": "OPEN_PROFILE_NATIVE_COVERAGE_REQUIRED",
        "verdict": (
            VERDICT_RESTRICTED_PROFILE_PROVED
            if proved
            else (VERDICT_COMPONENT_SURVIVES if survivors else VERDICT_OPEN)
        ),
    }


def _campaign_payload(
    root: Path,
    manifest: dict[str, Any],
    backend: dict[str, Any],
    summaries: list[dict[str, Any]],
    *,
    cached_seconds: float,
    started: float,
) -> dict[str, Any]:
    requests = manifest["requests"]
    profile_results = {
        profile: _profile_status(profile, requests, summaries) for profile in manifest["profiles"]
    }
    all_proved = all(record["core_commutativity_proved"] for record in profile_results.values())
    any_survivor = any(
        record["noncommutative_component_survivor_charts"] for record in profile_results.values()
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_CAMPAIGN,
        "finite_scope": manifest["finite_scope"],
        "semantic_scope": _semantic_scope_record(),
        "manifest": {
            "path": MANIFEST_PATH,
            "semantic_digest_sha256": manifest["semantic_digest_sha256"],
        },
        "inventory": manifest["inventory"],
        "budget": manifest["budget"],
        "backend": backend,
        "budget_accounting": {
            "cached_authorised_runtime_seconds": cached_seconds,
            "new_invocation_elapsed_seconds": time.perf_counter() - started,
            "authorised_total_wall_time_seconds": manifest["budget"]["total_wall_time_seconds"],
            "effective_workers": 1,
            "worker_policy": "SEQUENTIAL_QQ_ONLY_ACROSS_BOTH_PROFILES",
            "same_budget_terminal_results_are_not_retried": True,
            "finite_field_fallback_permitted": False,
        },
        "coefficient_fields": manifest["coefficient_fields"],
        "planned_run_count": manifest["planned_run_count"],
        "completed_or_terminal_run_count": len(summaries),
        "runs": sorted(summaries, key=lambda item: (item["profile"], item["chart"])),
        "profile_results": profile_results,
        "exact_numeric_distinction": (
            "Only completed, bound QQ saturation certificates can close a chart; "
            "no finite-field run or fallback is present."
        ),
        "noncommutative_component_claim_boundary": (
            "A surviving saturated QQ component is not a certified rational matrix witness; "
            "it triggers a separate exact witness-extraction task."
        ),
        "verdict": (
            (
                VERDICT_RESTRICTED_LOCUS_PROVED
                if set(manifest["profiles"]) == set(PROFILES)
                else VERDICT_RESTRICTED_SELECTED_LOCUS_PROVED
            )
            if all_proved
            else (VERDICT_COMPONENT_SURVIVES if any_survivor else VERDICT_OPEN)
        ),
        "global_scientific_verdict": "FINAL_THEORY_OPEN",
    }
    validate_current_semantic_scope_v041(payload)
    payload["semantic_digest_sha256"] = stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )
    return payload


def run_one_sided_qq_campaign_v041(
    root: Path,
    *,
    profiles: tuple[str, ...] = PROFILES,
) -> dict[str, Any]:
    """Run the explicitly requested exact QQ campaign under the shared budget."""

    root = root.resolve()
    require_production_solver_authorization(
        root,
        campaign_id="v041_restricted_locus_qq",
        budget_path=BUDGET_PATH,
    )
    manifest = compile_one_sided_qq_manifest_v041(root, profiles=profiles)
    write_one_sided_qq_manifest_v041(root, manifest)
    requests = manifest["requests"]
    cached: dict[str, tuple[dict[str, Any], Path]] = {}
    cached_seconds = 0.0
    for request in requests:
        for path in (
            _certificate_path(root, request),
            _historical_certificate_path(root, request),
        ):
            result = _bound_terminal_result(path, request)
            if result is not None:
                cached[request["chart"]] = (result, path)
                cached_seconds += _result_wall_time_seconds(result)
                break
    remaining_budget = max(
        0.0, float(manifest["budget"]["total_wall_time_seconds"]) - cached_seconds
    )
    backend = detect_sage_backend(root)
    started = time.perf_counter()
    summaries: list[dict[str, Any]] = []

    def write_progress() -> None:
        _write_json(
            root / CAMPAIGN_PATH,
            _campaign_payload(
                root,
                manifest,
                backend,
                summaries,
                cached_seconds=cached_seconds,
                started=started,
            ),
        )

    if not backend.get("available"):
        for request in requests:
            result = _not_run_result(request, "BACKEND_UNAVAILABLE")
            summaries.append(
                _run_summary(root, result, _certificate_path(root, request), request, cached=False)
            )
        write_progress()
        return _load_json(root / CAMPAIGN_PATH)

    deadline = started + remaining_budget
    for request in requests:
        cached_entry = cached.get(request["chart"])
        path = _certificate_path(root, request)
        if cached_entry is not None:
            result, cached_path = cached_entry
            summaries.append(_run_summary(root, result, cached_path, request, cached=True))
            write_progress()
            continue
        remaining = deadline - time.perf_counter()
        if remaining < 1.0:
            result = _not_run_result(request, "NOT_RUN_TOTAL_BUDGET_EXHAUSTED")
        else:
            timeout = min(
                int(manifest["budget"]["timeout_seconds_per_chart"]), max(1, int(remaining))
            )
            result = run_sage_request(root, request, timeout_seconds=timeout)
        _write_json(path, result)
        summary = _run_summary(root, result, path, request, cached=False)
        summaries.append(summary)
        write_progress()
        print(
            f"[{len(summaries)}/{len(requests)}] {summary['profile']} "
            f"{summary['chart']} {summary['exit_status']} {summary['chart_verdict']}",
            flush=True,
        )
    return _load_json(root / CAMPAIGN_PATH)
