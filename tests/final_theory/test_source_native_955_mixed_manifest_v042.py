"""Focused tests for the source-native mixed 955 polynomial manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.source_native_955_mixed_manifest_v042 import (
    RESULT_PATH,
    VERDICT,
    compile_source_native_955_mixed_manifest_v042,
    semantic_digest,
)

ROOT = Path(__file__).resolve().parents[2]


def _compiled() -> dict[str, Any]:
    return compile_source_native_955_mixed_manifest_v042(ROOT)


def test_full_raw_source_residual_census_is_expanded() -> None:
    payload = _compiled()
    blocks = payload["residual_blocks"]
    assert isinstance(blocks, dict)
    assert blocks["CPOBC"]["count"] == 783
    assert blocks["strong_GC"]["count"] == 320
    assert blocks["reachable_MSR_operator"]["count"] == 24
    assert blocks["reachable_MSR_vector"]["count"] == 24
    assert len(blocks["CPOBC"]["records"]) == 783
    assert len(blocks["strong_GC"]["records"]) == 320
    assert len(blocks["reachable_MSR_vector"]["records"]) == 24
    assert all(len(value) == 64 for value in payload["residual_content_digests"].values())


def test_reachable_state_path_ids_belong_to_the_recorded_source_fibres() -> None:
    payload = _compiled()
    gc = json.loads((ROOT / "results/v0.3.3_local_operator_gc_n4.json").read_text(encoding="utf-8"))
    path_endpoints = {
        str(path["path_id"]): str(path["endpoint_causet_id"])
        for paths_at_stage in gc["path_inventory"].values()
        for path in paths_at_stage
    }
    for record in payload["residual_blocks"]["reachable_MSR_vector"]["records"]:
        assert path_endpoints[record["canonical_state_from_path"]] == record["source_id"]


def test_variables_localisations_and_uniform_n_nonzero_certificate() -> None:
    payload = _compiled()
    variables = payload["variables"]
    localisations = payload["nonsingularity_localisation"]
    certificate = payload["N_nonzero_certificate"]

    assert variables["x_coordinates"] == 131
    assert variables["y_coordinates"] == 131
    assert variables["total"] == 262
    assert len(localisations["raw_occurrence_factors"]) == 165
    assert localisations["distinct_ON_quotient_factors"] == 131
    assert certificate["source_id"] == "p1-0"
    assert certificate["operator_residual_entry"] == [1, 1]
    assert certificate["polynomial"] == [{"coefficient": "1", "monomial": []}]
    observed_terms = sum(
        block["term_census"]["total_terms"] for block in payload["residual_blocks"].values()
    )
    assert payload["resource_limits"]["observed_total_manifest_terms"] == observed_terms
    assert observed_terms <= payload["resource_limits"]["maximum_total_manifest_terms"]


def test_eq120_routing_and_supplemental_gates_are_not_reused_as_old_charts() -> None:
    payload = _compiled()
    eq120 = payload["Eq120_source_native_binding"]
    routing = payload["future_ratio_chart_routing"]
    supplemental = payload["supplemental_validation_ledger"]

    assert eq120["pairwise_ratio_prerequisites"] == ["R2_R3", "R2_R4", "R3_R4"]
    assert eq120["old_chart_ideal_reused"] is False
    assert routing["routes"] == ["S1", "S2", "S3"]
    assert routing["old_21_chart_ideals_reused"] is False
    assert supplemental["Eq113"]["derived_Qn_records"] == 25
    assert supplemental["Eq113"]["literal_Qn_plus_1_records"] == 25
    assert supplemental["Eq139"]["printed_strict_instances"] == 4
    assert supplemental["Eq139"]["Eq145_completed_instances"] == 10


def test_checked_in_artifact_is_reproducible_and_open() -> None:
    stored = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    assert stored == _compiled()
    assert stored["verdict"] == VERDICT
    assert stored["passed"] is True
    assert stored["solver_status"] == "NOT_RUN"
    assert stored["sage_status"] == "NOT_INVOKED"
    assert stored["semantic_digest_sha256"] == semantic_digest(stored)
    assert any("not a solver result" in claim.lower() for claim in stored["claim_boundary"])
    assert any("validation-only" in claim.lower() for claim in stored["claim_boundary"])
