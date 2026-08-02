"""Exact guards for the fail-closed Eq. (120) Schur-chart obligations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import (
    sr2v_transverse_eq120_schur_chart_obligations_v042 as result,
)

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "d7ac88daccd2328280ff10558979b2a520c0d9628b5b6637d2e12a7d6bb79bb6"


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


def test_predecessors_are_bound_without_semantic_branches(rebuilt: dict[str, Any]) -> None:
    binding = rebuilt["predecessor_bindings"]
    assert binding["global_non_Q_elimination_shape"] == [127, 127]
    assert binding["remaining_Schur_columns"] == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert binding["uses_no_Eq113_or_Eq139_rows_in_the_unit_minor"] is True
    assert rebuilt["gates"]["frozen_Eq120_four_locus_cover_is_bound"] is True
    assert rebuilt["gates"]["frozen_127_column_unit_minor_is_bound"] is True


def test_three_non_aligned_charts_have_exact_kernel_reconstruction(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["non_aligned_chart_certificate"]
    charts = certificate["three_non_aligned_charts"]
    assert [record["chart"] for record in charts] == [
        "U2=D(g2)",
        "U3=D(g3)",
        "U4=D(g4)",
    ]
    assert [record["target_commutator"] for record in charts] == ["c12", "c13", "c14"]
    for record in charts:
        assert set(
            record["parameter_reconstruction"]["reverse_numerator_identity_checks"].values()
        ) == {"0"}
        assert record["parameter_reconstruction"]["x_Q1_through_Q4"] == (
            "delta*h+(b/b1)*w"
        )
        assert record["commutativity_obstruction_coordinate"] == "w"
        assert "iff w=0" in record["unit_equivalence"]
    assert set(
        certificate["Eq120_rows"]["forward_parametrisation_checks"].values()
    ) == {"0"}
    assert set(
        certificate["all_six_commutators_on_the_chart_kernel"][
            "symbolic_difference_checks"
        ].values()
    ) == {"0"}


def test_generic_schur_row_keeps_q5_fail_closed(rebuilt: dict[str, Any]) -> None:
    certificate = rebuilt["non_aligned_chart_certificate"]
    restriction = certificate["generic_Schur_row_restriction"]
    assert restriction["restricted_equation"] == "A*h+B*w+C*q5"
    assert restriction["C"] == "rho5"
    assert restriction["symbolic_difference"] == "0"
    obligation = certificate["exact_localized_obligation"]
    assert "every residue-field Schur-kernel vector has w=0" in obligation[
        "pointwise_necessary_and_sufficient_condition"
    ]
    assert "e_w=(0,1,0) belongs" in obligation["strong_global_sufficient_condition"]
    assert "is not necessary" in obligation["strong_global_sufficient_condition"]
    assert obligation["Q5_free_pair_sufficient_condition"]["premise"] == "C_r=C_s=0"
    assert obligation["Q5_free_pair_sufficient_condition"]["identity_difference"] == "0"
    assert obligation["three_row_sufficient_condition"][
        "adjugate_w_identity_difference"
    ] == "0"


def test_visible_reference_changes_only_by_declared_units(rebuilt: dict[str, Any]) -> None:
    audit = rebuilt["non_aligned_chart_certificate"]["visible_reference_invariance"]
    records = audit["records"]
    assert [record["reference"] for record in records] == ["Q1", "Q2", "Q3", "Q4"]
    for record in records:
        assert record["parametrisation_difference_checks"] == ["0", "0", "0", "0"]
        assert record["B_scaling_difference"] == "0"
        assert record["pair_minor_scaling_difference"] == "0"
        assert record["scaling_is_a_declared_unit"] is True
    assert "creates no new repair divisor or global non-aligned region" in audit[
        "conclusion"
    ]
    assert "refine the cover" in audit["conclusion"]


def test_ab_minor_without_q5_control_is_rejected(rebuilt: dict[str, Any]) -> None:
    audit = rebuilt["non_aligned_chart_certificate"]["Q5_fail_closed_audit"]
    assert audit["naive_rows_ABC"] == [[1, 0, 1], [0, 1, 1]]
    assert audit["AB_minor"] == "1"
    assert audit["row_rank"] == 2
    assert audit["rank_after_adjoining_e_w"] == 3
    assert audit["kernel_generator_h_w_q5"] == ["-1", "-1", "1"]
    assert "does not isolate w" in audit["conclusion"]


def test_multivariate_gcd_is_not_a_cover_certificate(rebuilt: dict[str, Any]) -> None:
    audit = rebuilt["non_aligned_chart_certificate"]["gcd_fail_closed_audit"]
    assert audit["ring"] == "QQ[u^+-1,v^+-1]"
    assert audit["gcd"] == "1"
    assert audit["common_torus_zero"] == ["u=1", "v=1"]
    assert audit["Groebner_basis_contains_one"] is False
    assert "not a unit-ideal" in audit["conclusion"]


def test_row_membership_is_not_promoted_to_pointwise_necessity(
    rebuilt: dict[str, Any],
) -> None:
    audit = rebuilt["non_aligned_chart_certificate"]["row_module_strength_audit"]
    assert audit["ring"] == "S=QQ[u^+-1]"
    assert audit["rows_ABC"] == [["-(u-1)", "1", "0"], ["0", "u-1", "0"]]
    assert audit["pointwise_kernel_has_w_zero"] is True
    assert audit["special_fibre_u_equals_1_ranks_before_after_e_w"] == [1, 1]
    assert audit["generic_two_by_two_determinant"] == "-(u - 1)**2"
    assert audit["e_w_in_row_module"] is False
    assert "not a necessary consequence" in audit["conclusion"]


def test_aligned_locus_has_three_distinct_obstruction_coordinates(
    rebuilt: dict[str, Any],
) -> None:
    aligned = rebuilt["aligned_chart_certificate"]
    assert aligned["locus"] == "L=V(g2,g3,g4) intersect D(f), with f=r1-1"
    assert aligned["Eq120_effect"] == (
        "all three exterior rows vanish identically on g2=g3=g4=0"
    )
    assert set(aligned["star_commutators"]["symbolic_difference_checks"].values()) == {
        "0"
    }
    assert "w2=w3=w4=0" in aligned["star_commutators"]["unit_equivalence"]
    restriction = aligned["generic_Schur_row_restriction"]
    assert restriction["columns"] == ["A", "B2", "B3", "B4", "C"]
    assert restriction["symbolic_difference"] == "0"
    obligation = aligned["exact_localized_obligation"]
    assert "adjoining e_w2,e_w3,e_w4 does not" in obligation[
        "pointwise_necessary_and_sufficient_condition"
    ]
    assert "e_w2,e_w3,e_w4 all belong" in obligation[
        "strong_global_sufficient_condition"
    ]
    assert obligation["pure_quotient_minor_sufficient_condition"][
        "adjugate_identity_difference"
    ] == ["0", "0", "0"]


def test_four_loci_and_automatic_remainder_are_complete(rebuilt: dict[str, Any]) -> None:
    aligned = rebuilt["aligned_chart_certificate"]
    cover = aligned["cover_decomposition"]
    assert cover["non_aligned_opens"] == ["D(g2)", "D(g3)", "D(g4)"]
    assert cover["aligned_nonunit_locus"] == "V(g2,g3,g4) intersect D(f)"
    assert cover["automatic_remainder"] == "V(g2,g3,g4,f)"
    assert cover["cover_identity_checks"] == ["0", "0", "0"]
    assert "not a partition" in cover["overlap_note"]
    safe = aligned["automatic_safe_remainder"]
    assert safe["consequence"] == "r1=r2=r3=r4=1, hence delta_Q=0"
    assert set(safe["all_six_commutator_checks"].values()) == {"0"}
    assert safe["needs_no_repair_rows"] is True


def test_result_is_an_obligation_certificate_not_a_terminal(rebuilt: dict[str, Any]) -> None:
    contract = rebuilt["repair_certificate_contract"]
    assert set(contract) == {
        "U2",
        "U3",
        "U4",
        "aligned",
        "accepted_global_proof_forms",
        "rejected_promotions",
    }
    assert any("gcd" in item for item in contract["rejected_promotions"])
    assert any("Q5" in item for item in contract["rejected_promotions"])
    assert any("residue-field" in item for item in contract["rejected_promotions"])
    assert "no localized repair minor" in rebuilt["claim_boundary"]
    assert rebuilt["search_terminal"] == result.SEARCH_TERMINAL
