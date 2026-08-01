"""Focused checks for the v0.4.2 source-native 955 slack inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from universe_lab.final_theory.source_native_955_slack_compiler_v042 import (
    EQ120_PATH,
    RESULT_PATH,
    VERDICT,
    _canonical_json,
    compile_source_native_955_slack_v042,
    write_source_native_955_slack_v042,
)

ROOT = Path(__file__).resolve().parents[2]


def _digest(payload: dict[str, object]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def test_timid_source_recurrences_make_reachable_msr_an_identity() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)
    recurrences = payload["timid_slack_recurrences"]

    assert len(recurrences) == 24
    assert {record["timid_occurrence_id"] for record in recurrences}
    assert all(
        record["reachable_MSR_after_substitution"]
        == {
            "residual": (
                f"u:{record['source_id']}*(J*v:{record['source_id']})^T*v:{record['source_id']}"
            ),
            "identity": "u_c*(-v_2*v_1+v_1*v_2)=0",
            "constraint_emitted": False,
        }
        for record in recurrences
    )
    assert payload["raw_source_system"]["reachable_MSR"] == {
        "source_constraints": 24,
        "vector_entry_constraints_before_substitution": 48,
        "constraints_after_substitution": 0,
        "identity_reason": "(Jv_c)^T v_c=0 for every source c",
    }


def test_full_occurrence_and_orbit_accounting_is_exact() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)
    namespace = payload["operator_namespace"]

    assert namespace["raw_occurrences"] == 165
    assert namespace["ON_quotient_orbits"] == 131
    assert namespace["alias_occurrences"] == 34
    assert namespace["all_165_occurrences_covered"] is True
    assert len(namespace["orbit_inventory"]) == 131
    assert sum(record["alias_count"] for record in namespace["orbit_inventory"]) == 165
    assert payload["source_state_recurrence"]["derived_state_symbols"] == 24
    assert len(payload["source_state_recurrence"]["canonical_paths"]) == 24


def test_strong_gc_basis_connectivity_is_recomputed_endpoint_by_endpoint() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)
    graph = payload["source_state_recurrence"]["path_independence_enforced_by"][
        "endpoint_graph_connectivity"
    ]

    assert graph["path_count"] == 407
    assert graph["endpoint_count"] == 87
    assert graph["unordered_same_endpoint_pair_count"] == 1529
    assert graph["basis_edge_count"] == 320
    assert graph["all_endpoint_graphs_connected"] is True
    assert len(graph["endpoint_evidence"]) == 87
    assert all(
        item["connected"] is True
        and item["component_count"] == 1
        and item["basis_edge_count"] == item["tree_edge_count"]
        for item in graph["endpoint_evidence"]
    )
    assert len(graph["connectivity_evidence_sha256"]) == 64


def test_u_zero_recovers_only_the_source_strong_msr_slice() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)

    assert payload["legacy_slice"] == {
        "u_zero_at_all_24_sources": True,
        "recovered_semantics": "raw source strong-operator MSR",
        "not_claimed": "recovery of the frozen Eq.(108)-expanded Q presentation",
    }
    assert all(
        record["legacy_u_zero_recovery"]["timid_definition"] == "T_c=I-sum_non_timid(A)"
        for record in payload["timid_slack_recurrences"]
    )


def test_nonzero_slack_open_cover_and_equation_counts_are_search_ready() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)
    inventory = payload["search_ready_inventory"]

    assert inventory["base_scalar_unknowns"] == {
        "ON_quotient_operator_matrix_entries": 524,
        "slack_coordinates": 48,
        "total": 572,
        "excluded": [
            "fixed initial vector Omega",
            "derived reachable-state symbols v:c",
            "localisation inverse auxiliaries",
        ],
    }
    assert inventory["matrix_equation_blocks"] == {
        "raw_CPOBC": 783,
        "strong_GC_spanning_basis": 320,
        "timid_source_definitions": 24,
        "total": 1127,
        "dimension_two_scalar_entry_equations": 4508,
    }
    patches = inventory["N_nonzero_open_cover"]
    assert patches["coordinate_patches"] == 48
    assert patches["solver_runs"] == 0
    assert len(payload["raw_source_system"]["CPOBC_equations"]) == 783
    assert len(payload["raw_source_system"]["strong_GC_basis"]) == 320


def test_eq120_binding_and_forbidden_old_coordinate_boundary_are_explicit() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)
    binding = payload["Eq120_source_native_reuse"]
    boundary = payload["forbidden_or_retained_boundaries"]

    assert binding["path"] == EQ120_PATH
    assert binding["verdict"] == "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED"
    assert binding["counts"] == {
        "raw_CPOBC_relations": 6,
        "k1_Eq120_instances": 3,
        "selected_direct_CPOBC_relations": 700,
    }
    assert boundary["dependency_audit"] == {
        "Eq108_to_MSR_edge_present": True,
        "occurrences_requiring_Eq108_in_frozen_reduction": 141,
        "Eq112_eliminated_nonantichain_generators": 20,
    }
    assert (
        "paper Eq.(108) operator-MSR elimination" in boundary["forbidden_as_coordinate_definitions"]
    )
    assert (
        "Eq.(112) B-factor reconstruction and its 20 eliminated non-antichain generators"
        in boundary["forbidden_as_coordinate_definitions"]
    )


def test_supplemental_eq113_eq139_gates_are_bound_and_never_merged() -> None:
    payload = compile_source_native_955_slack_v042(ROOT)
    ledger = payload["supplemental_gate_ledger"]

    assert ledger["Eq113"] == {
        "derived_Qn_branch_records": 25,
        "literal_Qn_plus_1_branch_records": 25,
        "branches_kept_separate": True,
        "source_status": "SOURCE_AMBIGUITY",
        "source_native_role": "VALIDATION_ONLY_FAIL_CLOSED",
        "reason": (
            "The stored path records use Eq.(112) B definitions; no source-native "
            "weak-MSR derivation is compiled here."
        ),
    }
    assert ledger["Eq139"]["printed_strict_instances"] == 4
    assert ledger["Eq139"]["Eq145_completed_instances"] == 10
    assert ledger["Eq139"]["domains_kept_separate"] is True
    assert ledger["Eq139"]["source_native_role"] == (
        "VALIDATION_ONLY_FAIL_CLOSED_FOR_FULL_N4_DOMAIN"
    )
    assert ledger["Eq139"]["stage_coverage_boundary"]["n=4"] == (
        "requires endpoint stage 6; absent from the n<=4 compiler"
    )
    assert (
        ledger["downstream_witness_validation"]["included_as_source_coordinate_equations"] is False
    )


def test_result_artifact_is_reproducible_and_never_claims_commutativity() -> None:
    destination = write_source_native_955_slack_v042(ROOT)
    assert destination == ROOT / RESULT_PATH
    stored = json.loads(destination.read_text(encoding="utf-8"))

    assert stored == compile_source_native_955_slack_v042(ROOT)
    assert stored["verdict"] == VERDICT
    assert stored["passed"] is True
    assert stored["solver_status"] == "NOT_RUN"
    assert stored["sage_status"] == "NOT_INVOKED"
    assert stored["semantic_digest_sha256"] == _digest(stored)
    assert all(
        "commutativity" not in claim.lower() or "does not" in claim.lower()
        for claim in stored["claim_boundary"]
    )
    assert any("scalar-polynomial solver manifest" in claim for claim in stored["claim_boundary"])
    assert any("global chart cover" in claim for claim in stored["claim_boundary"])
