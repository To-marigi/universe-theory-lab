"""Tests for the static v0.4.1 one-sided-profile inventory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from universe_lab.final_theory.one_sided_d2_v041 import (
    BUDGET_PATH,
    GLOBAL_VERDICT,
    HUMAN_BUDGET_PRESENT,
    HUMAN_BUDGET_REQUIRED,
    OFF_NATURALLY_LABELLED,
    ON_QUOTIENT,
    PINNED_ARTIFACT_HASHES,
    RESULT_PATH,
    VERDICT,
    budget_gate_v041,
    compile_one_sided_d2_v041,
    semantic_digest,
    write_one_sided_d2_v041_result,
)

ROOT = Path(__file__).resolve().parents[2]


def test_static_inventory_binds_hashes_and_exact_counts() -> None:
    inventory = compile_one_sided_d2_v041(ROOT)
    assert inventory["source_artifacts"] == PINNED_ARTIFACT_HASHES
    assert inventory["verdict"] == VERDICT
    assert inventory["global_scientific_verdict"] == GLOBAL_VERDICT
    assert set(inventory["profiles"]) == {
        "fixed_vector_GC__strong_MSR",
        "strong_GC__reachable_state_MSR",
    }
    assert all(
        set(profile["identification_modes"])
        == {
            ON_QUOTIENT,
            OFF_NATURALLY_LABELLED,
        }
        for profile in inventory["profiles"].values()
    )
    on = inventory["identification_modes"][ON_QUOTIENT]["counts"]
    assert on == {
        "quotient_transition_variables": 131,
        "reduction_records_or_aliases": 165,
        "CPOBC_records": 641,
        "CPOBC_raw_word_equations": 783,
        "CPOBC_inverse_rewrites": 712,
        "MSR_source_constraints": 24,
        "GC_spanning_tree_basis": 320,
        "GC_all_same_endpoint_pairs": 1529,
    }


def test_off_is_explicitly_labelled_and_never_claims_165() -> None:
    inventory = compile_one_sided_d2_v041(ROOT)
    off = inventory["identification_modes"][OFF_NATURALLY_LABELLED]
    assert off["counts"]["labelled_transition_occurrences"] == 406
    assert off["counts"]["source_nodes_by_stage"] == {"1": 1, "2": 2, "3": 7, "4": 40}
    assert off["counts"]["outgoing_transitions_by_source_stage"] == {
        "1": 2,
        "2": 7,
        "3": 40,
        "4": 357,
    }
    assert off["no_165_OFF_claim"]
    assert set(off["not_compiled"].values()) == {"NOT_YET_COMPILED"}


def test_relation_subsets_are_sorted_disjoint_and_conservative() -> None:
    inventory = compile_one_sided_d2_v041(ROOT)
    relations = inventory["q5_free_relation_inventory"]
    assert len(relations["q5_free_relation_ids"]["ids"]) == 976
    assert relations["fixed_vector_GC__strong_MSR"]["count"] == 721
    assert relations["strong_GC__reachable_state_MSR"]["count"] == 955
    families = relations["families"]
    assert set(families["CPOBC"]["ids"]).isdisjoint(families["LOCAL_OPERATOR_GC"]["ids"])
    assert set(families["CPOBC"]["ids"]).isdisjoint(families["STRONG_OPERATOR_MSR"]["ids"])
    assert not set(relations["fixed_vector_GC__strong_MSR"]["ids"]) & set(
        families["LOCAL_OPERATOR_GC"]["ids"]
    )
    assert not set(relations["strong_GC__reachable_state_MSR"]["ids"]) & set(
        families["STRONG_OPERATOR_MSR"]["ids"]
    )
    assert (
        inventory["ablation_core_interpretation"]["excluded_Eq112_path_family"][
            "relation_count_per_branch"
        ]
        == 25
    )
    assert all(values["ids"] == sorted(values["ids"]) for values in relations["families"].values())


def test_eq113_eq139_and_scout_domains_remain_separate() -> None:
    inventory = compile_one_sided_d2_v041(ROOT)
    gates = inventory["supplemental_full_profile_gates"]
    assert gates["Eq113"]["derived_branch"]["count"] == 25
    assert gates["Eq113"]["literal_branch"]["count"] == 25
    assert gates["Eq139"]["PRINTED_STRICT"]["count"] == 4
    assert gates["Eq139"]["EQ145_COMPLETED"]["count"] == 10
    assert inventory["triangular_scout"]["status"].endswith("NOT_GENERAL_D2_PROOF")


def test_budget_is_authorised_fails_closed_elsewhere_and_roundtrip_is_stable(
    tmp_path: Path,
) -> None:
    gate = budget_gate_v041(tmp_path)
    assert gate["expected_path"] == BUDGET_PATH
    assert gate["status"] == HUMAN_BUDGET_REQUIRED
    assert not gate["elimination_executed"]
    assert not gate["fallback_budget_used"]
    invalid_root = tmp_path / "invalid"
    (invalid_root / "config").mkdir(parents=True)
    (invalid_root / BUDGET_PATH).write_text(
        json.dumps(
            {
                "timeout_seconds_per_chart": 2,
                "total_wall_time_seconds": 1,
                "memory_limit_gib": 1,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cannot exceed"):
        budget_gate_v041(invalid_root)
    root_gate = budget_gate_v041(ROOT)
    assert root_gate["status"] == HUMAN_BUDGET_PRESENT
    assert root_gate["authorised_limits"] == {
        "timeout_seconds_per_chart": 3600,
        "total_wall_time_seconds": 43200,
        "memory_limit_gib": 8.0,
    }
    assert not root_gate["elimination_executed"]
    assert not root_gate["fallback_budget_used"]
    inventory = compile_one_sided_d2_v041(ROOT)
    assert inventory["budget_gate"]["status"] == HUMAN_BUDGET_PRESENT
    assert inventory["semantic_digest_sha256"] == semantic_digest(inventory)
    output_root = tmp_path / "roundtrip"
    output_root.mkdir()
    (output_root / "results").mkdir()
    output = write_one_sided_d2_v041_result(output_root, inventory)
    assert output == output_root / RESULT_PATH
    assert "\r\n" not in output.read_bytes().decode("utf-8")
    if (ROOT / RESULT_PATH).is_file():
        stored = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
        assert stored == inventory
