from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from universe_lab.final_theory.d2_sage_backend_v035 import _result_semantic_digest
from universe_lab.final_theory.d2_strata_v034 import S1, S2
from universe_lab.final_theory.one_sided_elimination_v041 import (
    CAMPAIGN_PATH,
    CERTIFICATE_ROOT,
    HISTORICAL_CERTIFICATE_ROOT,
    MANIFEST_PATH,
    PROFILE_STRONG_GC,
    PROFILE_STRONG_MSR,
    PROFILES,
    VERDICT_MANIFEST_READY,
    VERDICT_RESTRICTED_LOCUS_PROVED,
    WITHDRAWN_FULL_PROFILE_VERDICT,
    _campaign_payload,
    _certificate_path,
    _historical_certificate_path,
    _memory_limit_matches,
    _request_digest,
    _result_wall_time_seconds,
    compile_one_sided_qq_manifest_v041,
    load_human_budget_v041,
    qq_resolves_noncommutativity_v041,
    validate_current_semantic_scope_v041,
    write_one_sided_qq_manifest_v041,
)

ROOT = Path(__file__).resolve().parents[2]


def test_budget_is_external_and_has_no_v037_fallback(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="external budget file"):
        load_human_budget_v041(tmp_path)
    config = tmp_path / "config"
    config.mkdir()
    (config / "v0.4.1_budget.json").write_text(
        json.dumps(
            {
                "timeout_seconds_per_chart": 3600,
                "total_wall_time_seconds": 43200,
                "memory_limit_gib": 8,
            }
        ),
        encoding="utf-8",
    )
    budget = load_human_budget_v041(tmp_path)
    assert budget["timeout_seconds_per_chart"] == 3600
    assert budget["total_wall_time_seconds"] == 43200
    assert budget["memory_limit_bytes"] == 8 * 1024**3


def test_dry_manifest_is_qq_only_and_covers_both_cores() -> None:
    manifest = compile_one_sided_qq_manifest_v041(ROOT)
    assert manifest["verdict"] == VERDICT_MANIFEST_READY
    assert manifest["verdict"] != WITHDRAWN_FULL_PROFILE_VERDICT
    assert manifest["semantic_scope"]["classification"] == "RESTRICTED_LOCUS_ONLY"
    assert manifest["semantic_scope"]["profile_native_coverage_certified"] is False
    assert manifest["semantic_scope"]["full_profile_forward_implication_permitted"] is False
    assert manifest["planned_run_count"] == 42
    assert manifest["coefficient_fields"] == {
        "scheduled": ["QQ"],
        "finite_field_scouts_scheduled": False,
        "finite_field_fallback_permitted": False,
        "proof_field": "QQ",
    }
    assert manifest["chart_cover"]["S1_chart_count"] == 12
    assert manifest["chart_cover"]["S2_chart_count"] == 9
    assert manifest["chart_cover"]["S3_structural_certificate"]["passed"] is True
    assert manifest["chart_cover"]["Eq120_ratio_commutation_identity"]["verified"] is True
    assert set(manifest["profiles"]) == set(PROFILES)
    assert manifest["profiles"][PROFILE_STRONG_MSR]["core_relation_count"] == 721
    assert manifest["profiles"][PROFILE_STRONG_GC]["core_relation_count"] == 955
    for profile in manifest["profiles"].values():
        assert "forward_rule" not in profile
        assert profile["profile_native_coverage_certified"] is False
        assert profile["full_profile_forward_implication_permitted"] is False
        assert profile["full_profile_commutativity_proved_by_forward_implication"] is False
    assert all(request["coefficient_modulus"] == 0 for request in manifest["requests"])
    for request in manifest["requests"]:
        assert not any(name.startswith("q5_") for name in request["q_substitutions"])


def test_current_manifest_write_uses_new_path_and_rejects_withdrawn_verdict(
    tmp_path: Path,
) -> None:
    manifest = compile_one_sided_qq_manifest_v041(ROOT)
    written = write_one_sided_qq_manifest_v041(tmp_path, manifest)
    assert written == tmp_path / MANIFEST_PATH
    assert "restricted_locus" in written.name
    poisoned = dict(manifest)
    poisoned["verdict"] = WITHDRAWN_FULL_PROFILE_VERDICT
    with pytest.raises(ValueError, match="withdrawn full-profile verdict"):
        validate_current_semantic_scope_v041(poisoned)
    with pytest.raises(ValueError, match="withdrawn full-profile verdict"):
        write_one_sided_qq_manifest_v041(tmp_path, poisoned)


def test_campaign_summary_can_only_emit_restricted_locus_theorem() -> None:
    manifest = compile_one_sided_qq_manifest_v041(ROOT)
    historical = json.loads(
        (ROOT / "results/v0.4.1_one_sided_elimination.json").read_text(encoding="utf-8")
    )
    payload = _campaign_payload(
        ROOT,
        manifest,
        {"available": True, "test_fixture": True},
        historical["runs"],
        cached_seconds=0.0,
        started=time.perf_counter(),
    )
    assert CAMPAIGN_PATH.endswith("restricted_locus_campaign.json")
    assert payload["verdict"] == VERDICT_RESTRICTED_LOCUS_PROVED
    assert payload["verdict"] != WITHDRAWN_FULL_PROFILE_VERDICT
    for profile in payload["profile_results"].values():
        assert profile["restricted_locus_commutativity_proved"] is True
        assert profile["profile_native_coverage_certified"] is False
        assert profile["full_profile_forward_implication_permitted"] is False
        assert profile["full_profile_commutativity_proved_by_forward_implication"] is False


def test_compiled_request_has_bound_direct_subset() -> None:
    manifest = compile_one_sided_qq_manifest_v041(ROOT, profiles=(PROFILE_STRONG_GC,))
    request = manifest["requests"][0]
    assert request["stratum"] in {S1, S2}
    assert request["selection_label"] == "CPOBC_PLUS_STRONG_GC_955"
    assert request["expected_selected_relation_count"] == 955
    assert request["expected_relation_family_counts"] == {"CPOBC": 700, "LOCAL_OPERATOR_GC": 255}
    assert request["request_semantic_digest_sha256"] == _request_digest(request)
    assert request["finite_field_fallback_permitted"] is False
    assert "expected_direct_file_sha256" not in request
    assert request["expected_direct_system_file_sha256"]
    assert request["expected_direct_system_semantic_digest_sha256"]
    certificate = _certificate_path(ROOT, request)
    historical_certificate = _historical_certificate_path(ROOT, request)
    assert CERTIFICATE_ROOT in certificate.as_posix()
    assert HISTORICAL_CERTIFICATE_ROOT in historical_certificate.as_posix()
    assert certificate != historical_certificate
    assert historical_certificate.is_file()
    assert certificate.parts[-3:] == (
        PROFILE_STRONG_GC,
        "QQ",
        certificate.name,
    )


def test_only_complete_bound_qq_certificate_closes_chart() -> None:
    manifest = compile_one_sided_qq_manifest_v041(ROOT, profiles=(PROFILE_STRONG_MSR,))
    request = manifest["requests"][0]
    result = {
        "schema_version": "final-theory-one-sided-d2-qq-response-v0.4.1",
        "exit_status": "COMPLETED",
        "coefficient_field": "QQ",
        "coefficient_modulus": 0,
        "proof_eligible": True,
        "chart": request["chart"],
        "budget_file_sha256": request["budget_file_sha256"],
        "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
        "selection_label": request["selection_label"],
        "direct_system_file_sha256": request["expected_direct_system_file_sha256"],
        "direct_system_semantic_digest_sha256": request[
            "expected_direct_system_semantic_digest_sha256"
        ],
        "direct_system_self_semantic_digest_valid": True,
        "selected_matrix_relation_count": 721,
        "selected_relation_ids_sha256": request["expected_selected_relation_ids_sha256"],
        "selected_relation_family_counts": {"CPOBC": 700, "STRONG_OPERATOR_MSR": 21},
        "relation_selection_checks_passed": True,
        "saturation_requested": True,
        "final_localisation_complete": True,
        "commutator_coverage_complete": True,
        "chart_verdict": "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART",
        "initial_groebner_basis": {},
        "saturation_trace": [],
        "noncommutativity_checks": [],
        "resource_usage": {
            "memory_budget_satisfied": True,
            "memory_limit": {
                "requested": True,
                "applied": True,
                "resource": "RLIMIT_AS",
                "limit_bytes": request["memory_limit_bytes"],
                "effective_limit_bytes": request["memory_limit_bytes"],
            },
        },
    }
    result["semantic_digest_sha256"] = _result_semantic_digest(
        result,
        selection_fields=(
            "selection_label",
            "selected_relation_ids_sha256",
            "selected_equation_ids_sha256",
        ),
    )
    assert _memory_limit_matches(result, request)
    assert qq_resolves_noncommutativity_v041(result, request)
    result["coefficient_field"] = "GF(32003)"
    assert not qq_resolves_noncommutativity_v041(result, request)


def test_terminal_runtime_prefers_host_measurement() -> None:
    result = {"host_observed_wall_time_seconds": 8.0, "wall_time_seconds": 7.0}
    assert _result_wall_time_seconds(result) == 8.0
    assert _result_wall_time_seconds({"resource_usage": {"wall_time_seconds": 5.0}}) == 5.0
