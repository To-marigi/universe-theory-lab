"""Exact checks for the fixed-harmonic state-native CPOBC obstruction."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import (
    weak_d2_state_native_fixed_harmonic_cpobc_obstruction_v042 as obstruction,
)

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "d5514f31bf6caef5ca102ef8ce78f0bcf137e72922c0f230c716386f22cffc7d"


def _load(relative: str) -> dict[str, Any]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return obstruction.build_payload(ROOT)


def test_frozen_obstruction_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(obstruction.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == obstruction.semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert frozen["verdict"] == obstruction.VERDICT
    assert frozen["search_terminal"] == obstruction.SEARCH_TERMINAL
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())


def test_only_raw_ledgers_are_mathematical_inputs(rebuilt: dict[str, Any]) -> None:
    bindings = rebuilt["input_bindings"]
    assert bindings["mathematical_inputs"] == {
        obstruction.CPOBC_PATH: obstruction.PINNED_INPUT_SHA256[obstruction.CPOBC_PATH],
        obstruction.REDUCTION_PATH: obstruction.PINNED_INPUT_SHA256[
            obstruction.REDUCTION_PATH
        ],
    }
    for relative, expected in obstruction.PINNED_INPUT_SHA256.items():
        assert _sha256(relative) == expected
    comparison = bindings["manifest_comparison_only"]
    assert comparison["not_used_to_construct_graph_states_matrices_or_residuals"] is True
    assert rebuilt["independent_reconstruction"]["imports_D12_polynomial_helpers"] is False
    source = Path(obstruction.__file__).read_text(encoding="utf-8")
    assert "weak_d2_state_native_shear_pair_open_v042" not in source


def test_full_262_parameter_chart_is_reconstructed_over_QQ(
    rebuilt: dict[str, Any],
) -> None:
    reconstruction = rebuilt["independent_reconstruction"]
    assert reconstruction["occurrence_count"] == 165
    assert reconstruction["ON_orbit_count"] == 131
    assert reconstruction["endpoint_state_count"] == 87
    assert reconstruction["nonterminal_source_count"] == 24
    assert reconstruction["harmonic_failures"] == []
    assert Fraction(reconstruction["support_determinant"]) != 0
    assert reconstruction["alpha_coordinate_count"] == 131
    assert reconstruction["beta_coordinate_count"] == 131
    assert reconstruction["full_affine_coordinate_count"] == 262
    assert reconstruction["nonsingular_subdomain"] == "product_e(beta_e)!=0"
    assert reconstruction["Q5_coordinate_count"] == 0
    assert reconstruction["D12_localization_coordinate_count"] == 0
    assert reconstruction["budget_input_count"] == 0


def test_full_alpha_beta_core_is_the_exact_constant_two_over_117(
    rebuilt: dict[str, Any],
) -> None:
    core = rebuilt["full_alpha_beta_core_unit_generator"]
    assert core["relation_id"] == "cpobc-relation-0ca7a22bed9cdf4bc14a"
    assert core["equation_id"] == "eq103"
    assert core["entry"] == [0, 0]
    assert core["raw_display"] == "A_n*A_prime_m - A_m*A_prime_n = 0"
    assert core["lhs_word"] == ["A_n", "A_prime_m"]
    assert core["rhs_word"] == ["A_m", "A_prime_n"]
    assert obstruction._deserialize_polynomial(core["lhs_core_entry"]) == {
        (): Fraction(5, 117)
    }
    assert obstruction._deserialize_polynomial(core["rhs_core_entry"]) == {
        (): Fraction(1, 39)
    }
    assert obstruction._deserialize_polynomial(core["residual_core_entry"]) == {
        (): Fraction(2, 117)
    }
    assert core["exact_constant_value"] == "2/117"
    assert core["unit_multiplier"] == "117/2"
    assert Fraction(core["unit_multiplier"]) * Fraction(core["exact_constant_value"]) == 1
    assert core["polynomial_variable_support"] == []


def test_full_alpha_beta_constant_census_is_exact(rebuilt: dict[str, Any]) -> None:
    census = rebuilt["full_alpha_beta_constant_residual_census"]
    assert census["raw_operator_equations"] == 783
    assert census["raw_scalar_entries"] == 3132
    assert census["pure_nonzero_constant_entries"] == 95
    assert census["relations_with_a_pure_nonzero_constant_entry"] == 95
    assert census["entry_position_histogram"] == {"00": 95}
    assert len(census["records"]) == 95
    assert census["records_digest_sha256"] == (
        "0b32fd734dc5b6bc84efdb16c4905cce72ec8669f9640bcc2ca3b064792ced13"
    )
    assert census["records_digest_sha256"] == obstruction._records_digest(
        census["records"]
    )


def test_beta1_shear_census_and_core_match_the_D12_manifest(
    rebuilt: dict[str, Any],
) -> None:
    shear = rebuilt["beta1_shear_crosscheck"]
    assert shear["pure_nonzero_constant_entries"] == 178
    assert shear["relations_with_a_pure_nonzero_constant_entry"] == 171
    assert shear["entry_position_histogram"] == {"00": 95, "10": 83}
    assert shear["independent_records_digest_sha256"] == (
        "df55b36d50ae69dfdac6767bbc84f2613252ea132c3de8d7b1a62638b5128e4a"
    )
    assert shear["manifest_records_digest_sha256"] == shear[
        "independent_records_digest_sha256"
    ]
    assert shear["manifest_records_equal_independent_records"] is True

    core = shear["core_unit_generator"]
    assert core["relation_id"] == "cpobc-relation-1decb1e77431d5355ada"
    assert core["equation_id"] == "eq103"
    assert core["entry"] == [1, 0]
    assert obstruction._deserialize_polynomial(core["residual_core_entry"]) == {
        (): Fraction(7, 663)
    }
    assert Fraction(core["unit_multiplier"]) * Fraction(core["exact_constant_value"]) == 1


def test_unit_ideal_conclusion_is_solver_free_and_localization_stable(
    rebuilt: dict[str, Any],
) -> None:
    conclusion = rebuilt["algebraic_conclusion"]
    assert conclusion["raw_CPOBC_ideal"] == "UNIT_IDEAL"
    assert conclusion["relation_variety_for_this_fixed_state_assignment"] == "EMPTY"
    assert conclusion["nonsingular_beta_localization_can_restore_a_point"] is False
    assert conclusion["D12_localization_can_restore_a_point"] is False
    assert conclusion["Q5_localization_can_restore_a_point"] is False
    assert conclusion["solver_required"] is False

    execution = rebuilt["execution_boundary"]
    assert execution == {
        "solver_status": "NOT_RUN",
        "groebner_status": "NOT_RUN",
        "sage_status": "NOT_INVOKED",
        "finite_field_status": "NOT_RUN",
        "numerical_status": "NOT_RUN",
        "budget_consumed": False,
        "witness": None,
    }


def test_scope_stops_at_one_fixed_harmonic_state_assignment(
    rebuilt: dict[str, Any],
) -> None:
    scope = rebuilt["scope_exclusions"]
    assert scope["this_fixed_harmonic_262_parameter_alpha_beta_chart"] == "COVERED_EMPTY"
    assert scope["other_rank_two_state_assignments"] == "NOT_COVERED"
    assert scope["all_rank_two_state_assignments"] == "NOT_COVERED"
    assert scope["weak_GC_weak_MSR_full_profile"] == "NOT_COVERED"
    assert scope["all_SR2V_branches"] == "NOT_COVERED"
    assert scope["SR2V_terminal_verdict"] is False
    assert scope["global_commutativity_or_noncommutativity_claim"] is False
    assert "one fixed harmonic rank-two state assignment" in rebuilt["claim_boundary"]


def test_input_drift_fails_closed(tmp_path: Path) -> None:
    for relative in obstruction.PINNED_INPUT_SHA256:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    target = tmp_path / obstruction.REDUCTION_PATH
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(AssertionError, match="pinned obstruction input changed"):
        obstruction.build_payload(tmp_path)
