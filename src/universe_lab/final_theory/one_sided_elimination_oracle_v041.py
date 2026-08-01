"""Independent verifier for the completed v0.4.1 restricted-locus QQ campaign.

This module intentionally does not import the v0.4.1 campaign driver.  It
reconstructs the two selected relation sets directly from the frozen direct
operator system, then binds the manifest, campaign summary, and every stored
QQ certificate.  The historical manifest and campaign are accepted solely as
arithmetic inputs: their full-profile forward implication and theorem verdict
are explicitly withdrawn.  Every newly emitted oracle payload is fail-closed
to the frozen Q-reconstruction-image loci.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

DIRECT_PATH = "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
HISTORICAL_MANIFEST_PATH = "results/v0.4.1_one_sided_elimination_manifest.json"
HISTORICAL_CAMPAIGN_PATH = "results/v0.4.1_one_sided_elimination.json"
HISTORICAL_RESULT_PATH = "results/v0.4.1_one_sided_elimination_oracle.json"
MANIFEST_PATH = "results/v0.4.1_one_sided_restricted_locus_manifest.json"
CAMPAIGN_PATH = "results/v0.4.1_one_sided_restricted_locus_campaign.json"
HISTORICAL_CERTIFICATE_ROOT = "certificates/d2_saturation/one_sided_v041"
CERTIFICATE_ROOT = "certificates/d2_saturation/one_sided_v041_restricted_locus"
RESULT_PATH = "results/v0.4.1_one_sided_restricted_locus_oracle.json"

WITHDRAWN_FULL_PROFILE_VERDICT = "WEAK_D2_ON_ONE_SIDED_COMMUTATIVITY_PROVED"
RESTRICTED_MANIFEST_VERDICT = "V041_RESTRICTED_LOCUS_QQ_MANIFEST_READY_SOLVER_NOT_RUN"
RESTRICTED_CAMPAIGN_VERDICT = "V041_ON_Q_RECONSTRUCTION_RESTRICTED_LOCUS_COMMUTATIVITY_PROVED"
RESTRICTED_ORACLE_VERDICT = "V041_RESTRICTED_LOCUS_QQ_INDEPENDENT_ORACLE_PASSED"
SEMANTIC_SCOPE_ID = "V041_FROZEN_Q_RECONSTRUCTION_IMAGE_RESTRICTED_LOCUS"
SOURCE_MODE_HISTORICAL = "HISTORICAL_WITHDRAWN_FULL_PROFILE_CLAIM"
SOURCE_MODE_CURRENT = "CURRENT_RESTRICTED_LOCUS"

PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "fixed_vector_GC__strong_MSR": {
        "families": ("CPOBC", "STRONG_OPERATOR_MSR"),
        "counts": {"CPOBC": 700, "STRONG_OPERATOR_MSR": 21},
        "relation_count": 721,
        "selection_label": "CPOBC_PLUS_STRONG_MSR_721",
    },
    "strong_GC__reachable_state_MSR": {
        "families": ("CPOBC", "LOCAL_OPERATOR_GC"),
        "counts": {"CPOBC": 700, "LOCAL_OPERATOR_GC": 255},
        "relation_count": 955,
        "selection_label": "CPOBC_PLUS_STRONG_GC_955",
    },
}
RESPONSE_SCHEMA = "final-theory-one-sided-d2-qq-response-v0.4.1"
ALLOWED_TERMINAL_VERDICTS = {
    "EXACT_EMPTY_CHART",
    "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART",
}


def _semantic_scope_record() -> dict[str, Any]:
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


def validate_current_oracle_scope_v041(payload: dict[str, Any]) -> None:
    """Fail closed if an emitted oracle payload revives the withdrawn claim."""

    scope = payload.get("semantic_scope")
    required = _semantic_scope_record()
    if not isinstance(scope, dict) or any(
        scope.get(key) != value for key, value in required.items()
    ):
        raise ValueError("v0.4.1 oracle lacks the fail-closed restricted-locus scope")
    for key in ("verdict", "terminal_verdict"):
        if payload.get(key) == WITHDRAWN_FULL_PROFILE_VERDICT:
            raise ValueError(f"withdrawn full-profile verdict cannot be emitted as {key}")
    profiles = payload.get("profile_results", {})
    if not isinstance(profiles, dict):
        raise ValueError("v0.4.1 oracle profile_results must be a mapping")
    for profile, record in profiles.items():
        if not isinstance(record, dict):
            raise ValueError(f"v0.4.1 oracle profile_results.{profile} must be a mapping")
        if record.get("full_profile_forward_implication_permitted") is not False:
            raise ValueError(f"v0.4.1 oracle {profile} permits full-profile implication")
        if record.get("profile_native_coverage_certified") is not False:
            raise ValueError(f"v0.4.1 oracle {profile} claims profile-native coverage")
        if record.get("full_profile_commutativity_proved_by_forward_implication", False):
            raise ValueError(f"v0.4.1 oracle {profile} revives the withdrawn theorem")


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _select_source_artifacts(root: Path) -> tuple[str, str, str]:
    """Prefer a complete current pair, otherwise audit the immutable legacy pair."""

    current_manifest = (root / MANIFEST_PATH).is_file()
    current_campaign = (root / CAMPAIGN_PATH).is_file()
    if current_campaign and not current_manifest:
        raise ValueError("current restricted-locus campaign lacks its manifest")
    if current_manifest and current_campaign:
        return MANIFEST_PATH, CAMPAIGN_PATH, SOURCE_MODE_CURRENT
    if (root / HISTORICAL_MANIFEST_PATH).is_file() and (root / HISTORICAL_CAMPAIGN_PATH).is_file():
        return HISTORICAL_MANIFEST_PATH, HISTORICAL_CAMPAIGN_PATH, SOURCE_MODE_HISTORICAL
    raise FileNotFoundError("no complete v0.4.1 manifest/campaign pair is available")


def _verify_source_semantic_scope(
    manifest: dict[str, Any], campaign: dict[str, Any], source_mode: str
) -> None:
    """Accept the withdrawn verdict only as a marked historical input."""

    if source_mode == SOURCE_MODE_HISTORICAL:
        _require(
            manifest.get("finite_scope") == "ON quotient; n<=4; d=2; exact QQ only",
            "historical manifest scope",
        )
        _require(
            manifest.get("verdict") == "V041_QQ_MANIFEST_READY_SOLVER_NOT_RUN",
            "historical manifest verdict",
        )
        _require(
            campaign.get("verdict") == WITHDRAWN_FULL_PROFILE_VERDICT,
            "historical withdrawn campaign verdict",
        )
        return
    _require(source_mode == SOURCE_MODE_CURRENT, "unknown v0.4.1 oracle source mode")
    required = _semantic_scope_record()
    for label, artifact in (("manifest", manifest), ("campaign", campaign)):
        scope = artifact.get("semantic_scope")
        _require(
            isinstance(scope, dict)
            and all(scope.get(key) == value for key, value in required.items()),
            f"current {label} restricted-locus scope",
        )
        _require(
            artifact.get("verdict") != WITHDRAWN_FULL_PROFILE_VERDICT,
            f"current {label} withdrawn verdict exclusion",
        )
    _require(manifest.get("verdict") == RESTRICTED_MANIFEST_VERDICT, "current manifest verdict")
    _require(campaign.get("verdict") == RESTRICTED_CAMPAIGN_VERDICT, "current campaign verdict")


def _semantic_digest_matches(payload: dict[str, Any]) -> bool:
    expected = payload.get("semantic_digest_sha256")
    return isinstance(expected, str) and expected == _stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def _request_digest_matches(request: dict[str, Any]) -> bool:
    expected = request.get("request_semantic_digest_sha256")
    actual = _stable_hash(
        {
            key: value
            for key, value in request.items()
            if key not in {"request_id", "request_semantic_digest_sha256"}
        }
    )
    return isinstance(expected, str) and expected == actual


def _result_digest_matches(result: dict[str, Any]) -> bool:
    """Reimplement the backend result digest without importing its helper."""

    try:
        semantic = {
            "chart": result["chart"],
            "field": result["coefficient_field"],
            "initial_basis": result["initial_groebner_basis"],
            "saturation_trace": result["saturation_trace"],
            "noncommutativity_checks": result["noncommutativity_checks"],
            "selection_label": result.get("selection_label"),
            "selected_relation_ids_sha256": result.get("selected_relation_ids_sha256"),
            "selected_equation_ids_sha256": result.get("selected_equation_ids_sha256"),
            "request_semantic_digest_sha256": result.get("request_semantic_digest_sha256"),
        }
    except KeyError:
        return False
    return result.get("semantic_digest_sha256") == _stable_hash(semantic)


def _direct_relation_cores(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    direct = _load(root / DIRECT_PATH)
    branch = "LITERAL_PRINTED_QN_PLUS_1_BRANCH"
    records = direct["relations"][branch]
    _require(isinstance(records, list), "literal direct relation list missing")
    direct_digest = _stable_hash(
        {
            "dependency_nodes": direct["dependency_nodes"],
            "relations": direct["relations"],
            "transitions": direct["reconstructed_transition_predicates"],
        }
    )
    _require(direct.get("semantic_digest_sha256") == direct_digest, "direct-system semantic digest")
    # The raw n<=4 direct system has exactly the 25 Eq.112 records outside the
    # Q5-free shared core.  Do not obtain this selection from the v0.4.1 driver.
    shared = sorted(
        record["relation_id"]
        for record in records
        if record.get("family") != "EQ112_PATH_CONSISTENCY"
    )
    by_id = {record["relation_id"]: record for record in records}
    family_counts = Counter(by_id[identifier]["family"] for identifier in shared)
    _require(
        family_counts
        == Counter({"CPOBC": 700, "LOCAL_OPERATOR_GC": 255, "STRONG_OPERATOR_MSR": 21}),
        "raw direct-system Q5-free family partition",
    )
    _require(len(shared) == 976, "raw direct-system Q5-free relation count")
    cores: dict[str, dict[str, Any]] = {}
    for profile, spec in PROFILE_SPECS.items():
        identifiers = sorted(
            identifier for identifier in shared if by_id[identifier]["family"] in spec["families"]
        )
        counts = dict(
            sorted(Counter(by_id[identifier]["family"] for identifier in identifiers).items())
        )
        _require(len(identifiers) == spec["relation_count"], f"{profile} raw relation count")
        _require(counts == spec["counts"], f"{profile} raw family count")
        cores[profile] = {
            "ids": identifiers,
            "sha256": _stable_hash(identifiers),
            "family_counts": counts,
        }
    return {
        "file_sha256": _sha256(root / DIRECT_PATH),
        "semantic_digest_sha256": direct_digest,
        "literal_relation_count": len(records),
        "q5_free_shared_relation_count": len(shared),
    }, cores


def _certificate_path(root: Path, request: dict[str, Any], certificate_root: str) -> Path:
    return (
        root
        / certificate_root
        / f"budget-{request['budget_file_sha256'][:16]}"
        / request["profile"]
        / "QQ"
        / f"{request['request_semantic_digest_sha256'][:24]}.json"
    )


def _bound_run_certificate_path(
    root: Path,
    request: dict[str, Any],
    run: dict[str, Any],
    source_mode: str,
) -> Path:
    historical = _certificate_path(root, request, HISTORICAL_CERTIFICATE_ROOT)
    current = _certificate_path(root, request, CERTIFICATE_ROOT)
    reported = run.get("certificate")
    if not isinstance(reported, str):
        raise ValueError("campaign certificate path")
    reported_path = (root / reported).resolve()
    allowed = (
        {historical.resolve()}
        if source_mode == SOURCE_MODE_HISTORICAL
        else {
            historical.resolve(),
            current.resolve(),
        }
    )
    _require(reported_path in allowed, "campaign certificate path is outside allowed roots")
    return reported_path


def _verify_certificate(
    certificate: dict[str, Any],
    request: dict[str, Any],
    direct: dict[str, Any],
    core: dict[str, Any],
) -> None:
    _require(certificate.get("schema_version") == RESPONSE_SCHEMA, "response schema")
    _require(certificate.get("exit_status") == "COMPLETED", "completed terminal status")
    _require(certificate.get("coefficient_field") == "QQ", "QQ coefficient field")
    _require(certificate.get("coefficient_modulus") == 0, "QQ coefficient modulus")
    _require(certificate.get("proof_eligible") is True, "proof eligibility")
    _require(_result_digest_matches(certificate), "certificate result semantic digest")
    time_limit = certificate.get("time_limit_seconds")
    _require(
        isinstance(time_limit, (int, float))
        and not isinstance(time_limit, bool)
        and 0 < time_limit <= request["authorised_timeout_seconds_per_run"],
        "certificate time limit",
    )
    for key in ("chart", "chart_cover_id", "stratum", "selection_label", "budget_file_sha256"):
        _require(certificate.get(key) == request.get(key), f"certificate/request {key}")
    _require(
        certificate.get("request_semantic_digest_sha256")
        == request["request_semantic_digest_sha256"],
        "certificate/request digest",
    )
    _require(
        certificate.get("direct_system_file_sha256") == direct["file_sha256"], "direct file hash"
    )
    _require(
        certificate.get("direct_system_semantic_digest_sha256") == direct["semantic_digest_sha256"],
        "direct semantic hash",
    )
    _require(
        certificate.get("direct_system_self_semantic_digest_valid") is True, "direct self digest"
    )
    _require(
        certificate.get("selected_matrix_relation_count")
        == request["expected_selected_relation_count"],
        "selection count",
    )
    _require(
        certificate.get("selected_relation_ids_sha256") == core["sha256"], "selection ID digest"
    )
    _require(
        certificate.get("selected_relation_family_counts") == core["family_counts"],
        "selection family counts",
    )
    _require(certificate.get("relation_selection_checks_passed") is True, "selection checks")
    _require(certificate.get("saturation_requested") is True, "saturation requested")
    _require(certificate.get("final_localisation_complete") is True, "final localisation")
    _require(certificate.get("final_resaturates_pre_stage4_factors") is True, "final re-saturation")
    _require(certificate.get("commutator_coverage_complete") is True, "commutator coverage")
    if certificate.get("saturated_unit_ideal") is not True:
        _require(
            certificate.get("covered_commutator_component_count")
            == certificate.get("commutator_component_count"),
            "commutator component count",
        )
    if certificate.get("saturated_unit_ideal") is not True:
        checks = certificate.get("noncommutativity_checks")
        if not isinstance(checks, list):
            raise ValueError("non-unit chart commutator checks")
        _require(
            all(item.get("unit_ideal") is True for item in checks), "non-unit commutator ideals"
        )
    resource = certificate.get("resource_usage", {})
    limit = resource.get("memory_limit", {}) if isinstance(resource, dict) else {}
    _require(resource.get("memory_budget_satisfied") is True, "memory budget flag")
    _require(
        limit.get("requested") is True
        and limit.get("applied") is True
        and limit.get("resource") == "RLIMIT_AS"
        and limit.get("limit_bytes") == 8 * 1024**3
        and limit.get("effective_limit_bytes") == 8 * 1024**3,
        "RLIMIT_AS 8 GiB",
    )
    _require(certificate.get("chart_verdict") in ALLOWED_TERMINAL_VERDICTS, "terminal verdict")
    _require(
        certificate.get("surviving_noncommutative_component_count") == 0, "surviving component"
    )


def compile_one_sided_elimination_oracle_v041(root: Path) -> dict[str, Any]:
    """Return a fail-closed independent audit of all 42 completed QQ charts."""

    root = root.resolve()
    manifest_path, campaign_path, source_mode = _select_source_artifacts(root)
    manifest = _load(root / manifest_path)
    campaign = _load(root / campaign_path)
    _require(_semantic_digest_matches(manifest), "manifest semantic digest")
    _require(_semantic_digest_matches(campaign), "campaign semantic digest")
    _verify_source_semantic_scope(manifest, campaign, source_mode)
    _require(manifest.get("planned_run_count") == 42, "manifest run count")
    _require(campaign.get("planned_run_count") == 42, "campaign planned run count")
    _require(campaign.get("completed_or_terminal_run_count") == 42, "campaign terminal run count")
    _require(campaign.get("global_scientific_verdict") == "FINAL_THEORY_OPEN", "claim boundary")
    _require(
        campaign.get("manifest", {}).get("semantic_digest_sha256")
        == manifest["semantic_digest_sha256"],
        "manifest binding",
    )
    _require(
        campaign.get("manifest", {}).get("path") == manifest_path,
        "manifest path binding",
    )
    budget_path = root / "config/v0.4.1_budget.json"
    _require(budget_path.is_file(), "budget file")
    _require(manifest.get("budget", {}).get("sha256") == _sha256(budget_path), "budget file hash")
    _require(campaign.get("budget") == manifest.get("budget"), "campaign budget binding")
    _require(manifest.get("budget", {}).get("memory_limit_bytes") == 8 * 1024**3, "manifest 8 GiB")
    _require(manifest.get("budget", {}).get("timeout_seconds_per_chart") == 3600, "chart budget")
    _require(manifest.get("budget", {}).get("total_wall_time_seconds") == 43200, "total budget")
    _require(manifest.get("coefficient_fields", {}).get("scheduled") == ["QQ"], "scheduled QQ")
    _require(
        manifest.get("coefficient_fields", {}).get("finite_field_fallback_permitted") is False,
        "no finite field fallback",
    )
    _require(
        manifest.get("coefficient_fields", {}).get("finite_field_scouts_scheduled") is False,
        "no finite field scout schedule",
    )
    _require(manifest.get("chart_cover", {}).get("S1_S2_chart_count") == 21, "21-chart cover")
    _require(
        manifest.get("chart_cover", {}).get("S3_structural_certificate", {}).get("passed") is True,
        "S3",
    )
    _require(
        manifest.get("chart_cover", {}).get("Eq120_ratio_commutation_identity", {}).get("verified")
        is True,
        "Eq120",
    )
    accounting = campaign.get("budget_accounting", {})
    cached_seconds = accounting.get("cached_authorised_runtime_seconds")
    invocation_seconds = accounting.get("new_invocation_elapsed_seconds")
    _require(
        isinstance(cached_seconds, (int, float))
        and not isinstance(cached_seconds, bool)
        and cached_seconds >= 0
        and isinstance(invocation_seconds, (int, float))
        and not isinstance(invocation_seconds, bool)
        and invocation_seconds >= 0
        and cached_seconds + invocation_seconds <= 43200,
        "shared total wall-time budget",
    )
    _require(accounting.get("effective_workers") == 1, "sequential worker budget")
    _require(accounting.get("finite_field_fallback_permitted") is False, "campaign QQ only")
    direct, cores = _direct_relation_cores(root)
    _require(
        manifest.get("inventory", {}).get("sha256")
        == _sha256(root / "results/v0.4.1_one_sided_inventory.json"),
        "inventory file hash",
    )
    _require(
        manifest.get("inventory", {}).get("semantic_digest_sha256")
        == _load(root / "results/v0.4.1_one_sided_inventory.json")["semantic_digest_sha256"],
        "inventory semantic hash",
    )
    requests = manifest.get("requests")
    runs = campaign.get("runs")
    if not isinstance(requests, list) or not isinstance(runs, list):
        raise ValueError("request/run lists")
    _require(len(requests) == len(runs) == 42, "all 42 request/run records")
    request_by_chart = {request.get("chart"): request for request in requests}
    run_by_chart = {run.get("chart"): run for run in runs}
    _require(len(request_by_chart) == len(run_by_chart) == 42, "unique chart/profile matrix")
    profile_summary: dict[str, dict[str, Any]] = {}
    certificate_hashes: dict[str, str] = {}
    referenced_certificate_paths: set[Path] = set()
    for profile, spec in PROFILE_SPECS.items():
        profile_requests = [request for request in requests if request.get("profile") == profile]
        _require(len(profile_requests) == 21, f"{profile} 21 charts")
        manifest_profile = manifest.get("profiles", {}).get(profile, {})
        _require(
            manifest_profile.get("core_relation_count") == spec["relation_count"],
            f"{profile} manifest count",
        )
        if source_mode == SOURCE_MODE_CURRENT:
            _require(
                manifest_profile.get("profile_native_coverage_certified") is False,
                f"{profile} manifest profile-native boundary",
            )
            _require(
                manifest_profile.get("full_profile_forward_implication_permitted") is False,
                f"{profile} manifest forward boundary",
            )
            _require(
                manifest_profile.get("full_profile_commutativity_proved_by_forward_implication")
                is False,
                f"{profile} manifest full-profile theorem exclusion",
            )
            _require("forward_rule" not in manifest_profile, f"{profile} obsolete forward rule")
        strata = Counter(request.get("stratum") for request in profile_requests)
        _require(
            strata == Counter({"S1_DISTINCT_EIGENVALUE": 12, "S2_COMMON_NILPOTENT": 9}),
            f"{profile} 12+9 cover",
        )
        closed = 0
        for request in profile_requests:
            _require(_request_digest_matches(request), "request semantic digest")
            _require(request.get("coefficient_modulus") == 0, "request QQ modulus")
            _require(request.get("profile") == profile, "request profile")
            _require(
                request.get("budget_file") == "config/v0.4.1_budget.json",
                "request budget path",
            )
            _require(
                request.get("budget_file_sha256") == manifest["budget"]["sha256"],
                "request budget hash",
            )
            _require(request.get("memory_limit_bytes") == 8 * 1024**3, "request 8 GiB")
            _require(request.get("finite_field_fallback_permitted") is False, "request QQ only")
            _require(
                request.get("authorised_timeout_seconds_per_run") == 3600,
                "request chart budget",
            )
            _require(
                request.get("authorised_total_wall_time_seconds") == 43200,
                "request total budget",
            )
            _require(
                request.get("selection_label") == spec["selection_label"], "request selection label"
            )
            _require(
                request.get("expected_selected_relation_count") == spec["relation_count"],
                "request selected count",
            )
            _require(
                request.get("expected_selected_relation_ids_sha256") == cores[profile]["sha256"],
                "request ID digest",
            )
            _require(
                request.get("expected_relation_family_counts") == cores[profile]["family_counts"],
                "request family count",
            )
            _require(
                request.get("expected_direct_system_file_sha256") == direct["file_sha256"],
                "request direct hash",
            )
            _require(
                request.get("expected_direct_system_semantic_digest_sha256")
                == direct["semantic_digest_sha256"],
                "request direct semantic hash",
            )
            _require(
                not any(str(name).startswith("q5_") for name in request.get("q_substitutions", {})),
                "Q5 exclusion",
            )
            _require(
                not any(
                    5 in component.get("pair", [])
                    for component in request.get("commutator_components", [])
                ),
                "Q5 commutator exclusion",
            )
            run = run_by_chart.get(request["chart"])
            if not isinstance(run, dict):
                raise ValueError("campaign run missing")
            path = _bound_run_certificate_path(root, request, run, source_mode)
            _require(path.is_file(), f"missing certificate {path}")
            referenced_certificate_paths.add(path.resolve())
            certificate = _load(path)
            _verify_certificate(certificate, request, direct, cores[profile])
            certificate_hashes[request["chart"]] = _sha256(path)
            _require(run.get("profile") == request["profile"], "run/request profile")
            for key in (
                "chart",
                "chart_cover_id",
                "stratum",
                "coefficient_field",
                "exit_status",
                "chart_verdict",
                "selected_matrix_relation_count",
                "selected_relation_ids_sha256",
                "selected_relation_family_counts",
                "budget_file_sha256",
                "request_semantic_digest_sha256",
                "semantic_digest_sha256",
            ):
                _require(run.get(key) == certificate.get(key), f"run/certificate {key}")
            _require(
                run.get("certificate_sha256") == certificate_hashes[request["chart"]],
                "run certificate hash",
            )
            _require(run.get("exact_chart_closed") is True, "run exact closure")
            _require(run.get("relation_selection_checks_passed") is True, "run selection")
            _require(run.get("final_localisation_complete") is True, "run localisation")
            _require(run.get("commutator_coverage_complete") is True, "run coverage")
            _require(run.get("memory_budget_satisfied") is True, "run memory")
            closed += 1
        profile_result = campaign.get("profile_results", {}).get(profile, {})
        _require(profile_result.get("QQ_exact_resolved_chart_count") == 21, "profile closure count")
        _require(
            set(profile_result.get("QQ_exact_resolved_charts", []))
            == {request["chart"] for request in profile_requests},
            "profile closure chart set",
        )
        _require(profile_result.get("core_commutativity_proved") is True, "core theorem")
        if source_mode == SOURCE_MODE_HISTORICAL:
            _require(
                profile_result.get("full_profile_commutativity_proved_by_forward_implication")
                is True,
                "historical withdrawn forward implication",
            )
        else:
            _require(
                profile_result.get("restricted_locus_commutativity_proved") is True,
                "restricted-locus theorem",
            )
            _require(
                profile_result.get("profile_native_coverage_certified") is False,
                "profile-native boundary",
            )
            _require(
                profile_result.get("full_profile_forward_implication_permitted") is False,
                "forward implication boundary",
            )
            _require(
                profile_result.get("full_profile_commutativity_proved_by_forward_implication")
                is False,
                "full-profile theorem exclusion",
            )
        profile_summary[profile] = {
            "chart_count": len(profile_requests),
            "exact_closed": closed,
            "core": cores[profile],
            "restricted_locus_commutativity_proved": True,
            "profile_native_coverage_certified": False,
            "full_profile_forward_implication_permitted": False,
            "full_profile_commutativity_proved_by_forward_implication": False,
            "full_profile_status": "OPEN_PROFILE_NATIVE_COVERAGE_REQUIRED",
        }
    expected_historical_paths = {
        _certificate_path(root, request, HISTORICAL_CERTIFICATE_ROOT).resolve()
        for request in requests
    }
    actual_historical_paths = {
        path.resolve() for path in (root / HISTORICAL_CERTIFICATE_ROOT).rglob("*.json")
    }
    _require(
        actual_historical_paths == expected_historical_paths,
        "historical certificate set equals the 42 immutable requests",
    )
    expected_current_paths = {
        _certificate_path(root, request, CERTIFICATE_ROOT).resolve() for request in requests
    }
    actual_current_paths = {path.resolve() for path in (root / CERTIFICATE_ROOT).rglob("*.json")}
    _require(actual_current_paths <= expected_current_paths, "current certificate root has extras")
    if source_mode == SOURCE_MODE_HISTORICAL:
        _require(
            referenced_certificate_paths == expected_historical_paths,
            "historical campaign references exactly the 42 immutable certificates",
        )
    else:
        _require(
            actual_current_paths == (referenced_certificate_paths & expected_current_paths),
            "current certificate set equals its campaign references",
        )
    payload: dict[str, Any] = {
        "schema_version": (
            "final-theory-one-sided-d2-qq-restricted-locus-independent-oracle-v0.4.1"
        ),
        "finite_scope": (
            "ON quotient frozen Q-reconstruction image only; n<=4; d=2; exact QQ only"
        ),
        "semantic_scope": _semantic_scope_record(),
        "driver_independence": (
            "Does not import one_sided_elimination_v041 or call qq_resolves_noncommutativity_v041."
        ),
        "source_artifact_mode": source_mode,
        "historical_claim_handling": {
            "withdrawn_full_profile_verdict_encountered": (source_mode == SOURCE_MODE_HISTORICAL),
            "status": "ARITHMETIC_INPUT_ONLY_FULL_PROFILE_INFERENCE_REJECTED",
        },
        "source_files": {
            DIRECT_PATH: _sha256(root / DIRECT_PATH),
            manifest_path: _sha256(root / manifest_path),
            campaign_path: _sha256(root / campaign_path),
        },
        "raw_direct_system": direct,
        "profile_results": profile_summary,
        "verified_certificate_count": len(certificate_hashes),
        "certificate_sha256_by_chart": dict(sorted(certificate_hashes.items())),
        "terminal_verdict": RESTRICTED_CAMPAIGN_VERDICT,
        "claim_boundary": (
            "Neither full one-sided profile nor occurrence-wise OFF/lifted semantics is "
            "certified; profile-native coverage remains open."
        ),
        "verdict": RESTRICTED_ORACLE_VERDICT,
    }
    validate_current_oracle_scope_v041(payload)
    payload["semantic_digest_sha256"] = _stable_hash(payload)
    return payload


def write_one_sided_elimination_oracle_v041(root: Path, payload: dict[str, Any]) -> Path:
    validate_current_oracle_scope_v041(payload)
    if payload.get("semantic_digest_sha256") != _stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    ):
        raise ValueError("v0.4.1 restricted-locus oracle semantic digest does not recompute")
    path = root.resolve() / RESULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return path
