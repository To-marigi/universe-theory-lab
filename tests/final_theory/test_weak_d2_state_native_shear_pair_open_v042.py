"""Exact checks for the SR2-V state-native shear ``D12`` manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_state_native_shear_pair_open_v042 as shear

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return shear.build_payload(ROOT)


def test_frozen_shear_manifest_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(shear.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == shear.semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "82cd51ddd29e5923b003c8cf8f75a5a26cf5a36edf68728ad58d298d3f573090"
    )
    assert frozen["verdict"] == shear.VERDICT
    assert frozen["search_terminal"] == shear.SEARCH_TERMINAL
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())


def test_shear_and_supplemental_coordinate_inventory(rebuilt: dict[str, Any]) -> None:
    variables = rebuilt["variables"]
    assert variables["actual_edge_shear_coordinates"] == 131
    assert variables["supplemental_Q5_coordinates"] == 4
    assert variables["ambient_chart_coordinates"] == 135
    assert variables["saturated_chart_coordinates"] == 136
    assert len(variables["names"]) == 136

    parameterisation = rebuilt["shear_parameterisation"]
    assert parameterisation["actual_edge_count"] == 131
    assert parameterisation["actual_occurrence_count"] == 165
    assert parameterisation["two_sided_inverse_identities_checked"] == 262
    assert parameterisation["inverse_identity_failures"] == []
    assert all(
        record["constant_determinant"] != "0"
        for record in parameterisation["actual_occurrence_determinants"]
    )
    assert parameterisation["supplemental_Q5"]["determinant_digest_sha256"] == (
        "81da7f043537e1b7a7943135e03e9e7be3edfb3119ba064243df4e6304256124"
    )


def test_every_operator_ledger_is_substituted_without_branch_merging(
    rebuilt: dict[str, Any],
) -> None:
    blocks = rebuilt["residual_blocks"]
    assert blocks["CPOBC_raw"]["count"] == 783
    assert blocks["CPOBC_inverse_rewrites"]["count"] == 712
    assert blocks["CPOBC_raw"]["content_digest_sha256"] == (
        "7a9a6df3298a5d6acae016d2402bfe31961f59957106fa16a33fadd4a9b5da46"
    )
    assert blocks["CPOBC_inverse_rewrites"]["content_digest_sha256"] == (
        "2499eaec5bdb6fccc24d4608204724b5310a8b5c3c7e68b030d25314e4957af5"
    )

    eq113 = blocks["Eq113"]
    assert eq113["branches_kept_separate"] is True
    assert eq113["EQ113_QN_BRANCH"]["count"] == 25
    assert eq113["EQ113_QN_PLUS_1_BRANCH"]["count"] == 25
    assert eq113["EQ113_QN_BRANCH"]["content_digest_sha256"] == (
        "ab5857c273954a587c1ae25e52a165a69c2cbcf1e8395ac6795c4218761ea793"
    )
    assert eq113["EQ113_QN_PLUS_1_BRANCH"]["content_digest_sha256"] == (
        "14590fe9433200c383e09a3d9a3b5c6252d1e15aed375c0675b8f63f49426749"
    )

    eq139 = blocks["Eq139"]
    assert eq139["domains_kept_separate"] is True
    assert eq139["EQ139_PRINTED_STRICT_M_K_LT_N"]["count"] == 4
    assert eq139["EQ139_EQ145_COMPLETED_M_K_LE_N"]["count"] == 10
    assert eq139["EQ139_PRINTED_STRICT_M_K_LT_N"]["content_digest_sha256"] == (
        "aa56515be333320b00fb8b490edb7f9c90278c5aa6efd01ca24fa0adc5a232f8"
    )
    assert eq139["EQ139_EQ145_COMPLETED_M_K_LE_N"]["content_digest_sha256"] == (
        "8eabbcd2f3bb28d15e2c3e206acf198c502459b131c4f7f55b0972168221d9b0"
    )


def test_gc_msr_are_exact_identities_on_the_rank_two_slice(
    rebuilt: dict[str, Any],
) -> None:
    blocks = rebuilt["residual_blocks"]
    gc = blocks["fixed_vector_GC_all_pairs"]
    msr = blocks["reachable_state_MSR"]
    assert gc["count"] == 1529
    assert gc["term_census"]["scalar_entries"] == 3058
    assert gc["term_census"]["zero_entries"] == 3058
    assert gc["term_census"]["total_terms"] == 0
    assert msr["count"] == 24
    assert msr["term_census"]["scalar_entries"] == 48
    assert msr["term_census"]["zero_entries"] == 48
    assert msr["term_census"]["total_terms"] == 0
    assert rebuilt["state_native_chart_binding"]["reachable_span_rank"] == 2


def test_D12_is_nonzero_and_has_an_exact_ambient_open_point(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["D12_pair_open_certificate"]
    assert certificate["pair"] == [1, 2]
    assert certificate["term_count"] == 7
    assert certificate["total_degree"] == 3
    assert certificate["variable_support"] == [
        "alpha:cpobc-transition-orbit-74b3519240acc75a0c55",
        "alpha:cpobc-transition-orbit-9fb0da3749caf7b75239",
    ]
    assert certificate["polynomial_content_digest_sha256"] == (
        "66716220b6f2851e700b260b9e082501914ba50dab1502f21da9f7584fcaa289"
    )
    assert certificate["saturation_equation"]["content_digest_sha256"] == (
        "cb9abb1f1c825a2629b7019c0920fae68110052a6990edca920a0f4818a459e5"
    )
    point = certificate["exact_nonempty_ambient_open_point"]
    assert point["D12_value"] == "155389/220996566"
    assert point["direct_commutator_determinant"] == point["D12_value"]
    assert point["Q5_determinant"] == "1"
    assert point["is_required_relation_solution"] is False
    assert point["required_relation_residuals_at_this_point"]["CPOBC_raw"][
        "nonzero_scalar_entries"
    ] > 0


def test_manifest_is_sparse_nonterminal_and_solver_free(rebuilt: dict[str, Any]) -> None:
    inventory = rebuilt["sparse_manifest_inventory"]
    assert inventory["Eq113_branches_merged"] is False
    assert inventory["Eq139_domains_merged"] is False
    assert inventory["observed_total_terms"] == 29994
    assert inventory["global_term_census"]["maximum_terms_in_one_entry"] == 64
    assert inventory["global_term_census"]["maximum_total_degree"] == 6

    boundary = rebuilt["resource_and_claim_boundaries"]
    assert boundary["solver_status"] == "NOT_RUN"
    assert boundary["groebner_status"] == "NOT_RUN"
    assert boundary["sage_status"] == "NOT_INVOKED"
    assert boundary["finite_field_status"] == "NOT_RUN"
    assert boundary["D12_open_meets_relation_variety"] == "UNRESOLVED"
    assert rebuilt["witness"] is None
    assert rebuilt["search_terminal"].startswith("NOT_A_SEARCH_TERMINAL")
