from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path

import pytest

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
)
from universe_lab.final_theory import q5_free_elimination_v037 as phase1_module
from universe_lab.final_theory import scope_addendum_v037 as scope_module
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_strata_v034 import S1, S2
from universe_lab.final_theory.q5_free_elimination_v037 import (
    EXPECTED_DENOMINATOR_DIGEST,
    EXPECTED_FREE_EQUATION_DIGEST,
    EXPECTED_FREE_EXPRESSION_DIGEST,
    EXPECTED_RELATION_FAMILY_COUNTS,
    SCHEMA_RESPONSE,
    VERDICT_PROVED,
    _backend_unavailable_summaries,
    _certificate_path,
    _core_s1_s2_charts,
    _memory_limit_matches_request,
    _qq_resolves_noncommutativity,
    _result_wall_time_seconds,
    _valid_cached_result,
    build_q5_free_chart_request_v037,
    compile_q5_free_partition_v037,
    load_human_budget_v037,
    verify_q5_free_campaign_v037,
)
from universe_lab.final_theory.scope_addendum_v037 import (
    VERDICT as ADDENDUM_VERDICT,
)
from universe_lab.final_theory.scope_addendum_v037 import (
    _v037_integrity,
    compile_scope_addendum_v037,
)

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = load_line_ending_bridge(ROOT / "results/v0.3.8_line_ending_bridge.json")
LEGACY_DIGESTS = LegacyRawDigestResolver(ROOT, BRIDGE)


@pytest.fixture(autouse=True)
def _bridge_legacy_raw_hashes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(phase1_module, "_sha256", LEGACY_DIGESTS.sha256)
    monkeypatch.setattr(scope_module, "_sha256", LEGACY_DIGESTS.sha256)


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha256(relative: str) -> str:
    return LEGACY_DIGESTS.sha256(ROOT / relative)


def _sha256_path(path: Path) -> str:
    return LEGACY_DIGESTS.sha256(path)


def test_budget_is_external_and_has_no_fallback(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="external budget file"):
        load_human_budget_v037(tmp_path)

    config = tmp_path / "config"
    config.mkdir()
    (config / "v0.3.7_budget.json").write_text(
        json.dumps(
            {
                "timeout_seconds_per_chart": 3600,
                "total_wall_time_seconds": 43200,
                "memory_limit_gib": 8,
            }
        ),
        encoding="utf-8",
    )
    budget = load_human_budget_v037(tmp_path)
    assert budget["provenance"] == (
        "EXTERNAL_REPOSITORY_BUDGET_FILE; NO_RUNTIME_DEFAULTS_OR_SELF_AUTHENTICATION"
    )
    assert budget["timeout_seconds_per_chart"] == 3600
    assert budget["total_wall_time_seconds"] == 43200
    assert budget["memory_limit_bytes"] == 8 * 1024**3

    (config / "v0.3.7_budget.json").write_text(
        json.dumps(
            {
                "timeout_seconds_per_chart": 3600,
                "total_wall_time_seconds": 43200,
                "memory_limit_gib": 8,
                "workers": 4,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported, unauthorised"):
        load_human_budget_v037(tmp_path)

    repository_budget = _load("config/v0.3.7_budget.json")
    assert set(repository_budget) == {
        "timeout_seconds_per_chart",
        "total_wall_time_seconds",
        "memory_limit_gib",
    }


def test_q5_free_partition_is_exact_and_rebuilds_identically() -> None:
    frozen = _load("results/v0.3.7_q5_free_partition.json")
    rebuilt = compile_q5_free_partition_v037(ROOT)
    assert rebuilt["passed"]
    assert rebuilt["semantic_digest_sha256"] == (frozen["semantic_digest_sha256"])

    partition = frozen["partition"]
    assert partition["literal_total"] == 2564
    assert partition["Q5_dependent_count"] == 12
    assert partition["Q5_independent_count"] == 2552
    assert partition["equation_ids_unique"]
    assert partition["canonical_expression_ids_unique"]
    assert partition["disjoint"]
    assert partition["union_complete"]
    assert partition["census_dependent_ID_set_matches"]
    assert not partition["compact_arena_missing_target_ids"]
    assert partition["Q5_independent_equation_ids_sha256"] == (EXPECTED_FREE_EQUATION_DIGEST)
    assert partition["Q5_independent_expression_ids_sha256"] == (EXPECTED_FREE_EXPRESSION_DIGEST)

    core = frozen["shared_core"]
    assert core["canonical_record_intersection_count"] == 2552
    assert core["intersection_is_exactly_Q5_independent_partition"]
    assert core["shared_records_byte_semantics_equal"]
    assert core["matrix_relation_count"] == 976
    assert core["relation_family_counts"] == (EXPECTED_RELATION_FAMILY_COUNTS)
    assert core["canonical_provenance_entry_count"] == 3904
    assert core["every_relation_has_all_four_matrix_entries"]
    assert core["path_provenance_count"] == 0
    assert core["direct_core_records_equal_between_branches"]

    excluded = frozen["excluded_path_family"]
    assert excluded["literal_path_relation_count"] == 25
    assert excluded["identically_zero_path_relation_count"] == 22
    assert excluded["nonzero_path_relation_count"] == 3
    assert frozen["denominators"]["factor_count"] == 191
    assert frozen["denominators"]["Q5_dependent_factor_count"] == 0
    assert frozen["denominators"]["factor_ids_sha256"] == (EXPECTED_DENOMINATOR_DIGEST)


def test_all_21_requests_use_core_geometry_and_no_q5() -> None:
    partition = _load("results/v0.3.7_q5_free_partition.json")
    budget = load_human_budget_v037(ROOT)
    charts = _core_s1_s2_charts()
    assert Counter(chart.stratum for chart in charts) == {
        S1: 12,
        S2: 9,
    }

    for chart in charts:
        request = build_q5_free_chart_request_v037(
            chart,
            partition,
            budget,
            coefficient_modulus=0,
        )
        assert request["chart_source_index_branch"] == DERIVED_BRANCH
        assert request["equation_source_index_branch"] == LITERAL_BRANCH
        assert request["source_index_branch"] == LITERAL_BRANCH
        assert request["expected_selected_canonical_equation_count"] == 2552
        assert request["expected_selected_relation_count"] == 976
        assert request["expected_frozen_denominator_factor_count"] == 191
        assert request["included_relation_families"] == sorted(EXPECTED_RELATION_FAMILY_COUNTS)
        assert request["forbidden_relation_families"] == ["EQ112_PATH_CONSISTENCY"]
        assert request["memory_limit_bytes"] == 8 * 1024**3
        assert not any(name.startswith("q5_") for name in request["q_substitutions"])
        assert all(5 not in component["pair"] for component in request["commutator_components"])


def test_phase1_exact_campaign_is_complete_and_scouts_agree() -> None:
    result = _load("results/v0.3.7_q5_free_elimination.json")
    assert result["verdict"] == VERDICT_PROVED
    assert result["phase1_proof_complete"]
    assert result["planned_run_count"] == 63
    assert result["completed_or_terminal_run_count"] == 63
    assert result["QQ_exact_resolved_chart_count"] == 21
    assert not result["shared_core_noncommutative_components"]
    assert not result["unresolved_S1_S2_charts"]
    assert result["GF_scout_campaign_complete"]
    assert result["GF_scout_agreement"]
    assert not result["GF_scout_disagreements"]
    assert result["global_scientific_verdict"] == "FINAL_THEORY_OPEN"

    fields = Counter(record["coefficient_field"] for record in result["runs"])
    assert fields == {"QQ": 21, "GF(32003)": 21, "GF(32009)": 21}
    qq = [record for record in result["runs"] if record["coefficient_field"] == "QQ"]
    assert all(record["proof_eligible"] for record in qq)
    assert all(
        record["selected_canonical_equation_count"] == 2552
        and record["selected_matrix_relation_count"] == 976
        and record["selected_denominator_record_count"] == 191
        and record["canonical_selection_checks_passed"]
        and record["final_localisation_complete"]
        and record["commutator_coverage_complete"]
        and record["memory_budget_satisfied"]
        for record in result["runs"]
    )
    assert result["S3_structural_certificate"]["passed"]
    assert result["complete_chart_cover"]["S1_S2_QQ_resolved_count"] == 21
    assert result["complete_chart_cover"]["S3_structurally_resolved"]
    implication = result["literal_forward_implication"]
    assert implication["Q5_free_shared_core_forces_Q1_Q4_commutativity"]
    assert implication["literal_full_system_is_subset_of_shared_core_variety"]
    assert implication["literal_full_system_Q1_Q4_commutativity"]
    assert not implication["Q5_behaviour_used"]


def test_phase1_strict_verifier_rebuilds_all_requests_and_roles() -> None:
    verification = verify_q5_free_campaign_v037(ROOT)
    assert verification["passed"]
    assert verification["certificate_role_counts"] == {
        "PHASE1_GF32003_SCOUT": 21,
        "PHASE1_GF32009_SCOUT": 21,
        "PHASE1_QQ_EXACT_PROOF": 21,
    }
    assert len(verification["certificate_checks"]) == 63
    assert all(
        record["semantic_digest_recomputes"]
        and record["request_binding_and_selection_gates_pass"]
        and record["raw_sha256_and_summary_match"]
        and record["exact_or_scout_role_gate_passes"]
        for record in verification["certificate_checks"]
    )

    mutated = copy.deepcopy(_load("results/v0.3.7_q5_free_elimination.json"))
    scout = next(
        record for record in mutated["runs"] if record["coefficient_field"].startswith("GF(")
    )
    scout["proof_eligible"] = True
    rejected = verify_q5_free_campaign_v037(
        ROOT,
        campaign=mutated,
    )
    assert not rejected["passed"]
    assert not rejected["aggregate_checks"]["all_certificate_checks_pass"]

    mutated = copy.deepcopy(_load("results/v0.3.7_q5_free_elimination.json"))
    mutated["budget"]["sha256"] = "0" * 64
    rejected = verify_q5_free_campaign_v037(
        ROOT,
        campaign=mutated,
    )
    assert not rejected["passed"]
    assert not rejected["aggregate_checks"]["budget_copy_matches_human_file"]


def test_only_completed_proof_eligible_qq_can_close_a_chart() -> None:
    baseline = {
        "coefficient_field": "QQ",
        "exit_status": "COMPLETED",
        "proof_eligible": True,
        "selected_canonical_equation_count": 2552,
        "selected_matrix_relation_count": 976,
        "selected_denominator_record_count": 191,
        "canonical_selection_checks_passed": True,
        "final_localisation_complete": True,
        "commutator_coverage_complete": True,
        "memory_budget_satisfied": True,
        "chart_verdict": "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART",
    }
    assert _qq_resolves_noncommutativity(baseline)
    for mutation in (
        {"coefficient_field": "GF(32003)"},
        {"exit_status": "TIMEOUT"},
        {"proof_eligible": False},
        {"final_localisation_complete": False},
        {"commutator_coverage_complete": False},
        {"memory_budget_satisfied": False},
    ):
        record = {**baseline, **mutation}
        assert not _qq_resolves_noncommutativity(record)


def test_cache_rejects_a_different_budget_binding(
    tmp_path: Path,
) -> None:
    partition = _load("results/v0.3.7_q5_free_partition.json")
    budget = load_human_budget_v037(ROOT)
    request = build_q5_free_chart_request_v037(
        _core_s1_s2_charts()[0],
        partition,
        budget,
        coefficient_modulus=0,
    )
    result = {
        "schema_version": SCHEMA_RESPONSE,
        "exit_status": "COMPLETED",
        "chart": request["chart"],
        "coefficient_field": "QQ",
        "budget_file_sha256": request["budget_file_sha256"],
        "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
        "time_limit_seconds": request["authorised_timeout_seconds_per_run"],
        "selection_label": "LITERAL_Q5_INDEPENDENT_2552",
        "selected_canonical_equation_count": 2552,
        "selected_matrix_relation_count": 976,
        "selected_equation_ids_sha256": request["expected_selected_equation_ids_sha256"],
        "selected_expression_ids_sha256": request["expected_selected_expression_ids_sha256"],
        "selected_denominator_record_count": 191,
        "canonical_selection_checks_passed": True,
        "saturation_requested": True,
        "final_localisation_complete": True,
        "commutator_coverage_complete": True,
        "resource_usage": {
            "memory_limit": {
                "requested": True,
                "resource": "RLIMIT_AS",
                "limit_bytes": request["memory_limit_bytes"],
                "effective_limit_bytes": request["memory_limit_bytes"],
                "applied": True,
            },
            "memory_budget_satisfied": True,
        },
    }
    path = tmp_path / "certificate.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    assert _valid_cached_result(path, request) == result
    result["budget_file_sha256"] = "0" * 64
    path.write_text(json.dumps(result), encoding="utf-8")
    assert _valid_cached_result(path, request) is None

    result["budget_file_sha256"] = request["budget_file_sha256"]
    result["resource_usage"]["memory_limit"]["effective_limit_bytes"] = request[
        "memory_limit_bytes"
    ]
    result["request_semantic_digest_sha256"] = "0" * 64
    path.write_text(json.dumps(result), encoding="utf-8")
    assert _valid_cached_result(path, request) is None

    result["request_semantic_digest_sha256"] = request["request_semantic_digest_sha256"]
    result["resource_usage"]["memory_limit"]["effective_limit_bytes"] = (
        request["memory_limit_bytes"] + 1
    )
    path.write_text(json.dumps(result), encoding="utf-8")
    assert _valid_cached_result(path, request) is None


def test_real_worker_memory_limit_record_matches_request_shape() -> None:
    partition = _load("results/v0.3.7_q5_free_partition.json")
    budget = load_human_budget_v037(ROOT)
    request = build_q5_free_chart_request_v037(
        _core_s1_s2_charts()[0],
        partition,
        budget,
        coefficient_modulus=0,
    )
    campaign = _load("results/v0.3.7_q5_free_elimination.json")
    certificate = _load(campaign["runs"][0]["certificate"])
    memory_limit = certificate["resource_usage"]["memory_limit"]
    assert isinstance(memory_limit, dict)
    assert memory_limit["resource"] == "RLIMIT_AS"
    assert _memory_limit_matches_request(certificate, request)


def test_backend_unavailable_preserves_bound_cache_summaries(
    tmp_path: Path,
) -> None:
    partition = _load("results/v0.3.7_q5_free_partition.json")
    budget = load_human_budget_v037(ROOT)
    request = build_q5_free_chart_request_v037(
        _core_s1_s2_charts()[0],
        partition,
        budget,
        coefficient_modulus=0,
    )
    path = _certificate_path(tmp_path, request)
    path.parent.mkdir(parents=True)
    result = {
        "chart": request["chart"],
        "chart_cover_id": request["chart_cover_id"],
        "stratum": request["stratum"],
        "coefficient_field": "QQ",
        "exit_status": "COMPLETED",
        "budget_file_sha256": request["budget_file_sha256"],
        "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
    }
    path.write_text(json.dumps(result), encoding="utf-8")
    key = (request["chart"], 0)
    summaries = _backend_unavailable_summaries(
        tmp_path,
        [request],
        {key: (result, path)},
    )
    assert len(summaries) == 1
    assert summaries[0]["cached"]
    assert summaries[0]["exit_status"] == "COMPLETED"
    assert summaries[0]["certificate_sha256"] == _sha256_path(path)

    path.unlink()
    summaries = _backend_unavailable_summaries(
        tmp_path,
        [request],
        {},
    )
    assert len(summaries) == 1
    assert not summaries[0]["cached"]
    assert summaries[0]["exit_status"] == "BACKEND_UNAVAILABLE"
    assert summaries[0]["certificate_sha256"] is None


def test_terminal_wall_time_counts_against_resumed_total_budget() -> None:
    assert _result_wall_time_seconds(
        {
            "exit_status": "TIMEOUT",
            "wall_time_seconds": 3599.5,
        }
    ) == pytest.approx(3599.5)
    assert _result_wall_time_seconds(
        {
            "host_observed_wall_time_seconds": 8.0,
            "wall_time_seconds": 7.0,
            "resource_usage": {"wall_time_seconds": 6.0},
        }
    ) == pytest.approx(8.0)
    assert _result_wall_time_seconds(
        {"resource_usage": {"wall_time_seconds": 5.0}}
    ) == pytest.approx(5.0)


def test_v034_v035_v036_frozen_evidence_remains_unchanged() -> None:
    assert _sha256("results/v0.3.4_polynomial_systems.json") == (
        "018c1dccc4e08102c6de1fbdd9baf6e8e89dcf818e302ebb175e23e59f5a1283"
    )
    assert _sha256("results/v0.3.5_full_stage4_campaign.json") == (
        "5295236d165d052c5d57a6fb2be7b9defab7a358fa8018e854c962c5fe667956"
    )
    assert _sha256("results/v0.3.5_d2_classification.json") == (
        "59abc7d234e6a814206c72beec851a7fc08c4082ce2452ed38f29b76a257c342"
    )
    assert _sha256("results/v0.3.6_q5_constraint_census.json") == (
        "6454bd06f373e9e3a04faba2c59f435acd3cfba0d20c167863438e243a6860ca"
    )
    assert _sha256("results/v0.3.6_q5_vacuity_proof.json") == (
        "67ad76c98d9a39a5b182267d59e93f4d80af25203c77c28c2265e3efed9097fb"
    )


def test_scope_addendum_corrects_claims_without_changing_numbers() -> None:
    frozen = _load("results/v0.3.7_scope_addendum.json")
    rebuilt = compile_scope_addendum_v037(ROOT)
    assert rebuilt["passed"]
    assert rebuilt["verdict"] == ADDENDUM_VERDICT
    assert rebuilt["semantic_digest_sha256"] == (frozen["semantic_digest_sha256"])
    historical = frozen["v0.3.5_historical_campaign"]
    assert historical["combined_S1_S2_chart_count"] == 49
    assert historical["combined_backend_run_count"] == 225
    assert not historical["frozen_numeric_results_changed"]
    assert historical["literal_full_solution_cover_claim_withdrawn"]
    retained = frozen["v0.3.6_retained_claim"]
    assert retained["Q5_dependency_partition"] == {
        "total": 2564,
        "Q5_dependent": 12,
        "Q5_independent": 2552,
    }
    replacement = frozen["v0.3.7_replacement_argument"]
    assert not replacement["Q5_and_R5_in_elimination"]
    assert replacement["Q5_free_canonical_numerator_count"] == 2552
    assert replacement["shared_matrix_relation_count"] == 976
    assert replacement["QQ_exact_resolved_chart_count"] == 21
    assert replacement["literal_Q1_Q4_commutativity_proved"]
    integrity = frozen["v0.3.7_artifact_integrity"]
    assert integrity["passed"]
    assert integrity["certificate_count"] == 63
    assert integrity["unique_certificate_path_count"] == 63
    assert integrity["all_certificate_bindings_passed"]
    assert frozen["global_scientific_verdict"] == "FINAL_THEORY_OPEN"


def test_scope_addendum_rejects_a_mutated_v037_run_binding() -> None:
    partition = _load("results/v0.3.7_q5_free_partition.json")
    elimination = _load("results/v0.3.7_q5_free_elimination.json")
    elimination["runs"][0]["certificate_sha256"] = "0" * 64
    integrity = _v037_integrity(ROOT, partition, elimination)
    assert not integrity["passed"]
    assert not integrity["all_certificate_bindings_passed"]

    elimination = _load("results/v0.3.7_q5_free_elimination.json")
    elimination["runs"][0]["proof_eligible"] = not elimination["runs"][0]["proof_eligible"]
    integrity = _v037_integrity(ROOT, partition, elimination)
    assert not integrity["passed"]
    assert not integrity["all_certificate_bindings_passed"]
    assert any(
        "proof_eligible" in record["summary_mismatch_fields"]
        for record in integrity["certificates"]
    )
