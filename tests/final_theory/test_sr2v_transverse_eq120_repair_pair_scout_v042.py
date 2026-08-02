"""Exact guards for the two rejected Eq. (120) repair-row pairs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_eq120_repair_pair_scout_v042 as result

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "f14853252dfadf4f2335f4f25a2388731ad821739f8b9534988cf31b5ac1bf18"


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
        assert binding["binding_kind"] == "canonical_json_semantic_digest"
        assert "raw_sha256" not in binding
        assert result.semantic_digest(_load(relative)) == binding["semantic_digest_sha256"]


@pytest.mark.parametrize(
    (
        "chart_id",
        "point",
        "ratio_g_value",
        "determinant_d_value",
        "sources",
        "row_digest",
        "repair_minor",
    ),
    [
        (
            "g2",
            {"u12": "1", "u13": "2", "u15": "1", "u44": "3", "u45": "3"},
            "1",
            "-1/48",
            [29, 147, 32, 120],
            "243a781a3a8e85286cd22972f94a09a151f16fdc26d75ad462ecd46e5fdfb970",
            "975/2048",
        ),
        (
            "g3",
            {"u12": "1", "u13": "3", "u15": "1", "u44": "2", "u45": "2"},
            "-1/2",
            "1/256",
            [29, 548, 424, 544],
            "c90087f1ff56a1cda32d6c2d4d368a0cff070546a346358f41c3d6c01e4f4d73",
            "225/4096",
        ),
    ],
)
def test_repair_pair_is_rejected_at_exact_chart_open_point(
    rebuilt: dict[str, Any],
    chart_id: str,
    point: dict[str, str],
    ratio_g_value: str,
    determinant_d_value: str,
    sources: list[int],
    row_digest: str,
    repair_minor: str,
) -> None:
    record = rebuilt["older_repair_pair_rejections"][chart_id]
    assert record["exact_positive_rational_slice_point"] == point
    assert record["ratio_chart_g_value"] == ratio_g_value
    assert record["determinant_form_d_value"] == determinant_d_value
    assert record["chart_function_unit_relation_residual"] == "0"
    assert record["D_d_equals_D_g_on_declared_nonsingular_base"] is True
    assert record["point_membership_in_D_d_agrees_with_D_g"] is True
    assert record["point_is_inside_ratio_chart_D_g"] is True
    assert record["point_is_inside_determinant_open_D_d"] is True
    assert record["ratio_chart_function"].startswith(f"{chart_id}=r_Q")
    assert record["determinant_form_function"].startswith(f"d{chart_id.removeprefix('g')}=a_Q1*b_Q")
    assert record["chart_function_unit_relation"].endswith(f"*{chart_id}")
    assert (
        record["declared_diagonal_unit_values"]
        == {
            "g2": {"b_Q1": "1/4", "b_Q2": "1/12"},
            "g3": {"b_Q1": "1/4", "b_Q3": "1/32"},
        }[chart_id]
    )
    assert record["all_joint_sources"] == sources
    assert record["row_id_digest_sha256"] == row_digest
    assert record["pivot_rank"] == 127
    assert (
        record["candidate_rank"],
        record["star_rank"],
        record["candidate_plus_star_rank"],
    ) == (3, 1, 4)
    assert record["pair_is_rejected_on_its_declared_chart"] is True
    assert record["all_candidate_Q5_components_are_zero"] is True
    repair = record["pointwise_eq120_kernel_repair_by_sources_8_14"]
    assert repair["joint_sources"] == [8, 14]
    assert repair["pair_minor_D_AB"] == repair_minor
    assert repair["all_C_Q5_coefficients_are_zero"] is True
    assert (
        repair["candidate_rank"],
        repair["target_e_w_rank"],
        repair["candidate_plus_target_e_w_rank"],
    ) == (2, 1, 2)
    assert repair["target_e_w_is_spanned"] is True


def test_g2_residual_rows_are_frozen(rebuilt: dict[str, Any]) -> None:
    record = rebuilt["older_repair_pair_rejections"]["g2"]
    assert record["candidate_schur_rows"] == [
        ["5/32", "-3/16", "-3/4", "0", "0"],
        ["3/82", "0", "0", "-3/4", "0"],
        ["0", "0", "0", "0", "0"],
        ["185/738", "5/41", "-80/123", "-10", "0"],
    ]
    assert record["star_schur_rows_c12_c13_c14"] == [
        ["-1/12", "0", "0", "0", "0"],
        ["1/48", "0", "0", "0", "0"],
        ["0", "0", "0", "0", "0"],
    ]


def test_g3_residual_rows_are_frozen(rebuilt: dict[str, Any]) -> None:
    record = rebuilt["older_repair_pair_rejections"]["g3"]
    assert record["candidate_schur_rows"] == [
        ["5/32", "-3/32", "-1", "0", "0"],
        ["-3/656", "0", "0", "3/32", "0"],
        ["-125/1312", "-45/1312", "-15/82", "15/4", "0"],
        ["0", "0", "0", "0", "0"],
    ]
    assert record["star_schur_rows_c12_c13_c14"] == [
        ["-1/6", "0", "0", "0", "0"],
        ["1/64", "0", "0", "0", "0"],
        ["0", "0", "0", "0", "0"],
    ]


def test_full_common_core_survives_both_pair_rejections(
    rebuilt: dict[str, Any],
) -> None:
    records = [
        *rebuilt["older_repair_pair_rejections"].values(),
        rebuilt["three_pair_minor_common_zero"],
    ]
    for record in records:
        assert record["full_M0_rank"] == 131
        assert record["full_M0_plus_all_six_commutators_rank"] == 131
        assert record["full_M0_has_no_escape_at_this_point"] is True


def test_third_point_is_a_common_zero_inside_two_charts(
    rebuilt: dict[str, Any],
) -> None:
    common = rebuilt["three_pair_minor_common_zero"]
    assert common["exact_positive_rational_slice_point"] == {
        "u12": "1",
        "u13": "1/2",
        "u15": "1",
        "u44": "2",
        "u45": "2",
    }
    assert common["ratio_chart_g_values"] == {
        "g2": "-1/2",
        "g3": "-1/2",
        "g4": "0",
    }
    assert common["determinant_form_d_values"] == {
        "d2": "1/96",
        "d3": "1/256",
        "d4": "0",
    }
    for relation in common["chart_function_unit_relations"].values():
        assert relation["identity_residual"] == "0"
        assert relation["D_d_equals_D_g_on_declared_nonsingular_base"] is True
        assert relation["point_membership_agrees"] is True
    assert common["lies_in_D_g2_intersect_D_g3"] is True
    assert common["lies_on_V_g4"] is True
    assert common["g4_eq120_base_sources"] == [147, 548]
    assert common["star_schur_rows_c12_c13_c14"] == [
        ["1/24", "0", "0", "0", "0"],
        ["1/64", "0", "0", "0", "0"],
        ["0", "0", "0", "0", "0"],
    ]


def test_all_three_pair_minor_opens_miss_the_third_point(
    rebuilt: dict[str, Any],
) -> None:
    common = rebuilt["three_pair_minor_common_zero"]
    expected_q_rows = {
        "32_120": [
            ["0", "0", "0", "0", "0"],
            ["5/1312", "15/164", "-15/82", "-5/16", "0"],
        ],
        "424_544": [
            ["25/1312", "-45/1312", "45/164", "-15/16", "0"],
            ["0", "0", "0", "0", "0"],
        ],
        "8_14": [
            ["0", "0", "0", "0", "0"],
            ["-1/8", "9/16", "0", "0", "0"],
        ],
    }
    expected_abc = {
        "32_120": [["0", "0", "0"], ["-5/5248", "-5/1312", "0"]],
        "424_544": [["-15/5248", "-5/1312", "0"], ["0", "0", "0"]],
        "8_14": [["0", "0", "0"], ["-3/128", "1/16", "0"]],
    }
    for key, record in common["pair_minor_records"].items():
        assert record["Q_schur_rows"] == expected_q_rows[key]
        assert record["restriction_rows_ABC"] == expected_abc[key]
        assert record["pair_minor_D_AB"] == "0"
        assert record["all_C_Q5_coefficients_are_zero"] is True
        assert (
            record["candidate_rank"],
            record["target_e_w_rank"],
            record["candidate_plus_target_e_w_rank"],
        ) == (1, 1, 2)
        assert (
            record["Q_candidate_rank"],
            record["Q_star_rank"],
            record["Q_candidate_plus_star_rank"],
        ) == (1, 1, 2)
        assert record["target_e_w_is_spanned"] is False
        assert record["Q_star_is_not_spanned"] is True
    assert common["all_three_pair_minors_vanish"] is True
    assert common["all_three_pair_restrictions_fail_to_span_e_w"] is True
    assert common["proposed_pair_minor_opens_do_not_cover_D_g2_or_D_g3"] is True


def test_result_is_explicitly_nonterminal(rebuilt: dict[str, Any]) -> None:
    assert rebuilt["search_terminal"] == (
        "NOT_A_SEARCH_TERMINAL_THREE_PAIR_MINOR_SUBCOVER_REJECTION_ONLY"
    )
    assert "not an Eq. (120) chart" in rebuilt["claim_boundary"]
    assert all(
        record["targeting_rationale_is_not_a_global_factorization_certificate"]
        for record in rebuilt["older_repair_pair_rejections"].values()
    )
