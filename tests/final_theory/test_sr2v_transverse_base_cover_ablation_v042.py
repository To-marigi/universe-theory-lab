"""Exact guards for the transverse-base cover and semantic-block ablations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_base_cover_ablation_v042 as result
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "005d9a5492bd379f5ac51d1d17b7d31df4acaa175fc9089ef4a138b761f23f6e"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return result.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(result.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == result.SCHEMA
    assert frozen["verdict"] == result.VERDICT
    assert frozen["search_terminal"] == result.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert result.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert frozen["witness"] is None
    assert all(frozen["gates"].values())
    for relative, binding in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == binding["raw_sha256"]


def test_scalar_base_is_intrinsic_to_cpobc(rebuilt: dict[str, Any]) -> None:
    audit = rebuilt["scalar_base_audit"]
    assert audit["row_counts"] == {
        "CPOBC": 783,
        "derived_Eq113": 25,
        "literal_Eq113": 25,
        "completed_Eq139": 10,
    }
    assert set(audit["QQ_ranks"].values()) == {83}
    assert audit["CPOBC_smith_nonzero_invariants"] == [1] * 83
    assert audit["CPOBC_integer_row_lattice_is_saturated"] is True
    assert audit["both_Eq113_scalar_readings_are_redundant_over_the_CPOBC_integer_lattice"] is True
    assert audit["all_completed_Eq139_scalar_rows_are_identically_zero"] is True
    assert audit["upper_torus_dimension"] == 49
    assert audit["transverse_scalar_base_dimension"] == 54
    assert audit["Q_ratio_character_rank"] == 4
    assert audit["primitive_kernel_coordinate_columns"] == {
        "Q1": 44,
        "Q2": 13,
        "Q3": 15,
        "Q4": 12,
    }


def test_ratio_coordinates_give_a_complete_five_piece_cover(rebuilt: dict[str, Any]) -> None:
    cover = rebuilt["ratio_normalized_cover"]
    assert cover["symbolic_difference"] == "0"
    assert cover["u_coordinates"] == "u_i=r_Qi-1"
    assert cover["equal_Q_spectrum_locus_dimension"] == 50
    assert cover["equal_Q_spectrum_locus_is_split_smooth"] is True
    assert cover["equal_Q_spectrum_locus_is_witness_free"] is True
    assert cover["complete_base_cover"] == [
        "Z_Q",
        "D(u1)",
        "D(u2)",
        "D(u3)",
        "D(u4)",
    ]
    assert cover["remaining_three_rows_follow_after_inverting_u_k"] is True


def test_strict_eq139_controls_completed_without_merging_eq113(rebuilt: dict[str, Any]) -> None:
    inclusion = rebuilt["strict_to_completed_Eq139_inclusion"]
    assert inclusion["strict_completed_instance_positions"] == [1, 4, 5, 7]
    assert inclusion["both_domains_are_built_by_the_same_constructor"] is True
    assert inclusion["derived_and_literal_Eq113_are_not_combined"] is True
    assert set(inclusion["branch_local_row_inclusion_maps"]) == {
        torus.EQ113_DERIVED,
        torus.EQ113_LITERAL,
    }
    assert rebuilt["remaining_exact_obligations"]["obligation_count"] == 8
    assert len(rebuilt["remaining_exact_obligations"]["obligations"]) == 8


def test_source_native_eq120_reduces_six_commutators_to_a_minimal_star(
    rebuilt: dict[str, Any],
) -> None:
    reduction = rebuilt["source_native_Eq120_star_commutator_reduction"]
    assert reduction["source_row_indices_zero_based"] == {
        "F21": 0,
        "F31": 4,
        "F32": 29,
        "F41": 44,
        "F42": 147,
        "F43": 548,
    }
    assert reduction["each_Eq120_row_uses_exactly_three_raw_CPOBC_rows"] is True
    assert set(reduction["six_to_star_identities"].values()) == {"0"}
    assert set(reduction["arbitrary_base_symbolic_row_combination_differences"].values()) == {"0"}
    assert reduction["identity_template"] == "c_mn=E_mn+c_1n-c_1m"
    assert len(reduction["sharper_complete_cover"]) == 4
    assert [len(item["target_rows"]) for item in reduction["sharper_complete_cover"]] == [
        1,
        1,
        1,
        3,
    ]
    assert reduction["three_star_rows_are_globally_minimal"]["point"] == ("r1=r2=r3=r4=r with r!=1")


def test_each_semantic_block_ablation_has_a_common_four_branch_witness(
    rebuilt: dict[str, Any],
) -> None:
    ablations = rebuilt["semantic_block_ablations"]
    assert set(ablations) == {result.OMIT_GC, result.OMIT_MSR}
    for record in ablations.values():
        assert record["upper_character"]["all_843_operator_scalar_rows_hold"] is True
        assert record["strongest_union"]["augmented_rank"] == (
            record["strongest_union"]["rank"] + 1
        )
        assert any(value != "0" for value in record["commutator_values_on_witness"].values())
        assert len(record["branches"]) == 4
        geometry = record["normalized_Q_geometry"]
        assert set(geometry["Eq120_rows"].values()) == {"0"}
        assert geometry["commutator_obstruction_h_equals_slope_plus_intercept"] != "0"
        for branch in record["branches"].values():
            assert branch["ablated_augmented_rank"] == branch["ablated_rank"] + 1
            assert branch["full_profile_rank"] == branch["full_profile_augmented_rank"]
            assert branch["full_profile_has_no_escape_at_this_point"] is True


def test_ablation_witnesses_pass_the_declared_direct_substitutions(
    rebuilt: dict[str, Any],
) -> None:
    for ablation_id, record in rebuilt["semantic_block_ablations"].items():
        direct = record["direct_certificate"]
        substitutions = direct["direct_substitution"]
        assert substitutions["CPOBC"] == {"checked": 783, "failures": []}
        assert all(value["checked"] == 25 for value in substitutions["Eq113"].values())
        assert all(not value["failures"] for value in substitutions["Eq113"].values())
        assert substitutions["Eq139"][torus.EQ139_STRICT] == {
            "checked": 4,
            "failures": [],
        }
        assert substitutions["Eq139"][torus.EQ139_COMPLETED] == {
            "checked": 10,
            "failures": [],
        }
        assert direct["all_132_assigned_matrices_are_nonsingular"] is True
        assert direct["all_path_state_span_rank"] == 2
        assert direct["some_nonzero_commutator_is_reachable_path_visible"] is True
        assert any(item["visible_path_count"] == 407 for item in direct["commutators"])
        if ablation_id == result.OMIT_MSR:
            assert substitutions["fixed_vector_GC"]["checked"] == 1529
            assert substitutions["fixed_vector_GC"]["failures"] == []
            assert len(substitutions["reachable_state_MSR"]["failures"]) == 24
            assert direct["all_same_endpoint_paths_give_same_state"] is True
            assert direct["upper_right_support"] == 28
        else:
            assert len(substitutions["fixed_vector_GC"]["failures"]) == 510
            assert substitutions["reachable_state_MSR"]["checked"] == 24
            assert substitutions["reachable_state_MSR"]["failures"] == []
            assert (
                substitutions["reachable_state_MSR"]["all_source_reaching_path_state_checks"] == 50
            )
            assert (
                substitutions["reachable_state_MSR"]["all_source_reaching_path_state_failures"]
                == []
            )
            assert direct["all_same_endpoint_paths_give_same_state"] is False
            assert direct["upper_right_support"] == 79
