"""Exact guards for the corrected CSG fixed-(h,k) rank-two obstruction."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import (
    weak_d2_state_native_corrected_csg_rank2_v042 as corrected,
)

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "2b6c8483598cf73bbf9dd2365dd2c7828c10bc0aedb72c58a84c47142c215b7f"


def _load(relative: str) -> dict[str, Any]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return corrected.build_payload(ROOT)


def test_frozen_corrected_obstruction_rebuilds_exactly(
    rebuilt: dict[str, Any],
) -> None:
    frozen = _load(corrected.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == corrected.semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert frozen["verdict"] == corrected.VERDICT
    assert frozen["search_terminal"] == corrected.SEARCH_TERMINAL
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())


def test_all_exact_inputs_are_raw_SHA_bound(rebuilt: dict[str, Any]) -> None:
    assert rebuilt["input_artifacts"] == corrected.PINNED_INPUT_SHA256
    for relative, expected in corrected.PINNED_INPUT_SHA256.items():
        assert _sha256(relative) == expected


def test_normalized_CSG_character_and_all_path_products_are_exact(
    rebuilt: dict[str, Any],
) -> None:
    character = rebuilt["normalized_CSG_character"]
    assert character["couplings"] == "t_j=1"
    assert character["actual_edge_count"] == 131
    assert character["all_nonzero"] is True
    assert len(character["records"]) == 131
    assert all(Fraction(record["p_e"]) for record in character["records"])
    assert character["records_digest_sha256"] == (
        "59f8ff458268b47f80249e6843d6cf1ec56551d2df49f9e96983f55d43fbfbbc"
    )

    paths = rebuilt["path_product_coordinate_h"]
    assert paths["path_count"] == 407
    assert paths["endpoint_count"] == 87
    assert paths["path_counts_by_stage"] == {"1": 1, "2": 2, "3": 7, "4": 40, "5": 357}
    assert paths["path_independence_failures"] == {}
    assert paths["root"] == "p1-0"
    assert paths["root_value"] == "1"
    assert paths["zero_values"] == []
    assert paths["edge_character_failures"] == []
    assert paths["harmonic_failures"] == []
    assert paths["CSG_MSR_failures"] == []
    assert paths["path_records_digest_sha256"] == (
        "11ecb4b2403e9574a3df75e01543b643a2a34777504480976ce0494327459467"
    )


def test_selected_independent_harmonic_k_gives_exact_rank_two(
    rebuilt: dict[str, Any],
) -> None:
    k = rebuilt["independent_harmonic_coordinate_k"]
    assert k["root_value"] == "0"
    assert k["support_terminals"] == ["p5-0000000", "p5-0000002"]
    assert k["terminal_root_weights"]["p5-0000000"] == 1
    assert k["terminal_root_weights"]["p5-0000002"] == 10
    assert k["harmonic_failures"] == []

    states = rebuilt["reachable_states"]
    assert len(states["records"]) == 87
    assert states["rank"] == 2
    assert states["support_pair"] == k["support_terminals"]
    assert states["support_determinant"] == "-11/1024"
    assert states["initial_vector"] == ["1", "0"]
    assert states["records_digest_sha256"] == (
        "92c2a052f413cfeedd8d26b622dceb991116d685970ef0de30c37c2ecf7592da"
    )


def test_complete_matrix_fibres_and_determinants_are_certified(
    rebuilt: dict[str, Any],
) -> None:
    fibres = rebuilt["complete_state_native_matrix_fibres"]
    assert fibres["frame"] == "F_c=[[h_c,0],[k_c,1]]"
    assert fibres["actual_edge_count"] == 131
    assert fibres["alpha_coordinates"] == 131
    assert fibres["beta_coordinates"] == 131
    assert fibres["total_affine_coordinates"] == 262
    assert "uniquely equals [[1,alpha],[0,beta]]" in fibres["coverage_proof"]
    assert fibres["frame_inverse_failures"] == []
    assert fibres["edge_mapping_failures"] == []
    assert fibres["determinant_formula"] == "det(A_e)=p_e*beta_e"
    assert fibres["determinant_failures"] == []
    assert fibres["nonsingular_iff"] == "beta_e!=0 because p_e!=0"


def test_fixed_vector_GC_and_reachable_state_MSR_are_built_in(
    rebuilt: dict[str, Any],
) -> None:
    semantics = rebuilt["built_in_semantics"]
    gc = semantics["fixed_vector_GC"]
    assert gc["path_count"] == 407
    assert gc["same_endpoint_pair_count"] == 1529
    assert gc["path_state_failures"] == []
    assert gc["pair_failures"] == []
    msr = semantics["reachable_state_MSR"]
    assert msr["source_count"] == 24
    assert msr["failures"] == []


def test_full_262_variable_raw_CPOBC_manifest_removes_old_constant_unit(
    rebuilt: dict[str, Any],
) -> None:
    manifest = rebuilt["raw_CPOBC_full_alpha_beta_manifest"]
    assert manifest["variable_count"] == 262
    assert manifest["Q5_included"] is False
    assert manifest["equation_count"] == 783
    assert len(manifest["records"]) == 783
    assert manifest["records_digest_sha256"] == (
        "72453d5ae56640949d9ff43ef37fc696f8b0e69e0679a3aa3fe422d04cc5ca0c"
    )
    assert manifest["term_census"] == {
        "scalar_entries": 3132,
        "zero_entries": 442,
        "nonzero_entries": 2690,
        "total_terms": 12860,
        "maximum_terms_in_one_entry": 23,
        "maximum_total_degree": 3,
        "entries_with_nonzero_constant_coefficient": 180,
        "pure_nonzero_constant_entries": 0,
    }
    assert manifest["pure_constant_records"] == []
    assert manifest["pure_constant_records_digest_sha256"] == (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    )
    old = manifest["old_uniform_terminal_full_chart_unit_entry_after_correction"]
    assert old["relation_id"] == "cpobc-relation-0ca7a22bed9cdf4bc14a"
    assert old["equation_id"] == "eq103"
    assert old["entry"] == [0, 0]
    assert old["constant_coefficient"] == "0"
    assert old["is_zero_polynomial"] is True
    assert manifest["unrestricted_singular_relation_solution_exists"] == "UNRESOLVED"


def test_two_alpha_free_rows_and_beta_localizer_generate_one_exactly(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["nonsingular_two_row_unit_obstruction"]
    assert certificate["beta_u_orbit"] == corrected.BETA_U_ORBIT
    assert certificate["beta_v_orbit"] == corrected.BETA_V_ORBIT
    assert certificate["p_u"] == "1/8"
    assert certificate["p_v"] == "1/16"
    assert certificate["determinant_at_v"] == (
        "1/16*beta:cpobc-transition-orbit-983362874bc6f5900920"
    )
    assert certificate["nonsingularity_requires_beta_v_nonzero"] is True

    f = corrected._deserialize_polynomial(certificate["row_f"]["polynomial"])
    g = corrected._deserialize_polynomial(certificate["row_g"]["polynomial"])
    beta_u = f"beta:{corrected.BETA_U_ORBIT}"
    beta_v = f"beta:{corrected.BETA_V_ORBIT}"
    assert certificate["row_f"]["relation_id"] == "cpobc-relation-ecdf5451a0bcf06c8da5"
    assert certificate["row_f"]["entry"] == [1, 0]
    assert certificate["row_f"]["contains_alpha"] is False
    assert f == {(): Fraction(1, 8), (beta_u,): Fraction(1)}
    assert certificate["row_g"]["relation_id"] == "cpobc-relation-8c0a09869cf24abeac93"
    assert certificate["row_g"]["entry"] == [1, 0]
    assert certificate["row_g"]["contains_alpha"] is False
    assert g == {(beta_v,): Fraction(8), tuple(sorted((beta_u, beta_v))): Fraction(-64)}

    identity = certificate["unit_identity"]
    assert identity["display"] == "1=(rho/16)*g+4*rho*beta_v*f-(rho*beta_v-1)"
    assert corrected._deserialize_polynomial(identity["reconstructed_result"]) == {
        (): Fraction(1)
    }
    assert identity["result_is_one"] is True
    assert certificate["localized_CPOBC_ideal"] == "UNIT_IDEAL"
    assert certificate[
        "nonsingular_relation_variety_on_selected_fixed_hk_slice"
    ] == "EMPTY"
    assert certificate["solver_required"] is False


def test_all_alpha_free_rows_have_the_exact_primitive_exponent_lattice(
    rebuilt: dict[str, Any],
) -> None:
    lattice = rebuilt["alpha_free_raw_CPOBC_lattice_diagnostic"]
    assert lattice["row_count"] == 327
    assert lattice["variable_count"] == 131
    assert lattice["all_rows_binomial"] is True
    assert lattice["total_terms"] == 654
    assert lattice["maximum_degree_histogram"] == {"1": 22, "2": 303, "3": 2}
    assert len(lattice["variable_order"]) == 131
    assert len(lattice["exponent_difference_matrix"]) == 327
    assert all(len(row) == 131 for row in lattice["exponent_difference_matrix"])
    assert lattice["variable_order_digest_sha256"] == (
        "34ce26e270a7e58ed71219aa16be544769704b5bf535c48aa7050b59c5dc205b"
    )
    assert lattice["exponent_difference_matrix_digest_sha256"] == (
        "29ccc8f815d01c0c159b862cdacb531fb4a88a01a3315e33b549f179961a74a4"
    )
    assert lattice["audited_rows_digest_sha256"] == (
        "7e860a6c3d445bdd734c019a65bd2b72a2b8ddc84a367f86e9c00a6b2a888ae4"
    )
    assert lattice["rank"] == 89
    assert lattice["nullity"] == 42
    assert lattice["smith_nonzero_diagonal"] == [1] * 89
    assert lattice["smith_factor_histogram"] == {"1": 89}


def test_beta1_shear_remains_obstructed_and_old_D12_is_not_reused(
    rebuilt: dict[str, Any],
) -> None:
    diagnostic = rebuilt["beta1_shear_diagnostic"]
    assert diagnostic["role"] == "DIAGNOSTIC_ONLY_DO_NOT_REUSE_OR_RERUN_OLD_D12_SHEAR"
    assert diagnostic["term_census"]["scalar_entries"] == 3132
    assert diagnostic["term_census"]["pure_nonzero_constant_entries"] == 151
    assert diagnostic["pure_constant_records_digest_sha256"] == (
        "5fb4e9980f226166e74b37b0918d326f1689dfb4762d9094db9d53c2feef7a17"
    )
    assert diagnostic["first_pure_nonzero_constant"] == {
        "relation_id": "cpobc-relation-0744145e3fa7b1f240ee",
        "equation_id": "eq103",
        "entry": [1, 0],
        "value": "15/2",
    }
    assert diagnostic["relation_variety_on_beta1_slice"].startswith("EMPTY_BY")
    assert diagnostic["D12_compiled_or_solved"] is False


def test_Q5_Eq113_and_Eq139_remain_separate_unresolved_ledgers(
    rebuilt: dict[str, Any],
) -> None:
    ledgers = rebuilt["separate_unresolved_ledgers"]
    assert ledgers["supplemental_Q5"]["coordinate_count"] == 4
    assert ledgers["supplemental_Q5"]["status"] == "SEPARATE_NOT_COMPILED_NOT_SOLVED"
    assert ledgers["Eq113"] == {
        "derived_Qn_records": 25,
        "literal_Qn_plus_1_records": 25,
        "branches_kept_separate": True,
        "status_on_corrected_chart": "UNRESOLVED_NOT_COMPILED",
    }
    assert ledgers["Eq139"] == {
        "printed_strict_instances": 4,
        "Eq145_completed_instances": 10,
        "domains_kept_separate": True,
        "status_on_corrected_chart": "UNRESOLVED_NOT_COMPILED",
    }


def test_no_solver_and_scope_stops_at_selected_fixed_hk_slice(
    rebuilt: dict[str, Any],
) -> None:
    boundary = rebuilt["execution_and_claim_boundary"]
    assert boundary == {
        "solver_status": "NOT_RUN",
        "groebner_status": "NOT_RUN",
        "sage_status": "NOT_INVOKED",
        "finite_field_status": "NOT_RUN",
        "numerical_status": "NOT_RUN",
        "unrestricted_singular_relation_solution": "UNRESOLVED",
        "nonsingular_relation_solution_on_selected_fixed_hk_slice": "IMPOSSIBLE",
        "witness": None,
    }
    scope = rebuilt["scope_exclusions"]
    assert scope["selected_corrected_CSG_fixed_hk_nonsingular_slice"] == "COVERED_EMPTY"
    assert scope["all_rank2_state_assignments"] == "NOT_COVERED"
    assert scope["global_chart_cover"] == "NOT_COVERED"
    assert scope["SR2V_terminal_verdict"] is False


def test_input_drift_fails_closed(tmp_path: Path) -> None:
    for relative in corrected.PINNED_INPUT_SHA256:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    target = tmp_path / corrected.GC_PATH
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(AssertionError, match="pinned corrected-chart input changed"):
        corrected.build_payload(tmp_path)
