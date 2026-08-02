"""Exact guards for the variable-harmonic SR2-V two-row audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_variable_harmonic_two_row_audit_v042 as audit

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "64a79807b4a19169517c5a9864b005c38a44593118987ed88e95dd2edb9cb84e"
EXPECTED_ROOT_WEIGHTS_DIGEST = "a2f091d72673df4de48deaa454d35bcd86ecc3f6eabb06c5ade8e1b57e26e8af"
EXPECTED_ROOT_KERNEL_DIGEST = "4ddc075f5e37b6fc6ea2f8246381da1ce0edcb6d8fd092cd728f2d2aafb5bbd4"
EXPECTED_UNIVERSAL_FORMULA_DIGEST = (
    "2badb9cc4b96d2731e573e0c78a8fc1276180f521ebecd0ef814409f9bc91fde"
)


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return audit.build_payload(ROOT)


def test_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(audit.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == audit.SCHEMA
    assert frozen["verdict"] == audit.VERDICT
    assert frozen["search_terminal"] == audit.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert audit.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())
    for relative, digest in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_harmonic_space_dimension_and_root_kernel_are_exact(
    rebuilt: dict[str, Any],
) -> None:
    harmonic = rebuilt["exact_harmonic_space"]
    assert harmonic["endpoint_count"] == 87
    assert harmonic["nonterminal_recurrence_count"] == 24
    assert harmonic["terminal_boundary_coordinate_count"] == 63
    assert harmonic["dimension_H"] == 63
    assert harmonic["dimension_kernel_ev_root"] == 62
    assert harmonic["identity_coefficients"] == [-1]
    assert harmonic["transition_multiplicities_are_positive"] is True
    assert harmonic["root_weight_reconstruction_failures"] == []
    assert harmonic["root_kernel_basis_count"] == 62
    assert harmonic["root_weight_records_digest_sha256"] == EXPECTED_ROOT_WEIGHTS_DIGEST
    assert harmonic["root_kernel_basis_digest_sha256"] == EXPECTED_ROOT_KERNEL_DIGEST
    assert harmonic["root_weight_records"][0] == {
        "terminal": "p5-0000000",
        "root_path_multiplicity": 1,
    }
    assert harmonic["root_weight_records"][8] == {
        "terminal": "p5-000008c",
        "root_path_multiplicity": 25,
    }


def test_rank_two_dimension_and_gauge_ledger(rebuilt: dict[str, Any]) -> None:
    ledger = rebuilt["dimension_and_gauge_ledger"]
    assert ledger["ordered_root_normalized_pair"]["dimension"] == 124
    assert ledger["global_basis_gauge_preserving_Omega_e1"] == {
        "action": "h -> h+a*k, k -> b*k",
        "parameters": "a in G_a, b in G_m",
        "dimension": 2,
    }
    assert ledger["all_rank2_state_assignment_moduli"] == {
        "identification": "open subset of Gr(2,H)=Gr(2,63)",
        "dimension": 122,
    }
    assert ledger["CSG_h_fixed_family"]["dimension_after_scaling"] == 61
    assert ledger["CSG_h_fixed_family"]["covers_all_rank2_state_assignments"] is False


def test_fixed_k_two_rows_have_the_exact_localized_unit_identity(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["fixed_k_localized_obstruction"]
    assert certificate["boundary_support"] == {
        "p5-0000000": "10",
        "p5-0000002": "-1",
    }
    assert certificate["f_raw_row"]["relation_id"] == audit.F_RELATION
    assert certificate["f_raw_row"]["polynomial"] == [
        {"coefficient": "1/8", "monomial": []},
        {
            "coefficient": "1",
            "monomial": [
                {"variable": f"beta:{audit.BETA_U_ORBIT}", "exponent": 1}
            ],
        },
    ]
    assert certificate["g_raw_row"]["relation_id"] == audit.G_RELATION
    assert certificate["unit_identity"] == (
        "1=(rho/16)*g+4*rho*beta_v*f-localizer"
    )
    assert certificate["unit_identity_residual"] == []


def test_escape_k_solves_the_same_rows_on_the_beta_torus(
    rebuilt: dict[str, Any],
) -> None:
    escape = rebuilt["escape_k_certificate"]
    assert escape["boundary_support"] == {
        "p5-0000000": "25",
        "p5-000008c": "-1",
    }
    assert escape["assignment"] == {
        "all_beta": "1",
        "all_unlisted_alpha": "0",
        f"alpha:{audit.ALPHA_E_ORBIT}": "5/524",
        f"alpha:{audit.BETA_V_ORBIT}": "-179/6",
    }
    assert escape["f_value"] == "0"
    assert escape["g_value"] == "0"
    assert escape["all_131_beta_values_nonzero"] is True
    assert escape["selected_two_row_localized_ideal_is_proper"] is True
    assert escape["full_CPOBC_solution_claimed"] is False


def test_a_nonempty_open_family_escapes_the_fixed_k_mechanism(
    rebuilt: dict[str, Any],
) -> None:
    open_certificate = rebuilt[
        "nonempty_Zariski_open_failure_of_the_fixed_k_mechanism"
    ]
    assert open_certificate["f_constant_at_escape"] == "-5/8"
    assert open_certificate["coefficient_of_alpha_E_at_escape"] == "131/2"
    assert open_certificate["g_constant_at_escape"] == "-179/2"
    assert open_certificate["coefficient_of_alpha_V_at_escape"] == "-3"
    assert open_certificate["diagonal_coefficient_determinant_at_escape"] == "-393/2"
    assert open_certificate["cross_support_failures"] == []
    universal = open_certificate["universal_small_formula"]
    assert universal["records_digest_sha256"] == EXPECTED_UNIVERSAL_FORMULA_DIGEST
    assert universal["Cf"] == "K_p3-024*(K_p2-2 + 64*K_p4-0044)/8"
    assert universal["evaluations"] == {
        "F0_fixed": "9/8",
        "Cf_fixed": "0",
        "G0_fixed": "-56",
        "Cg_fixed": "0",
        "Delta_fixed": "0",
        "F0_escape": "-5/8",
        "Cf_escape": "131/2",
        "G0_escape": "-179/2",
        "Cg_escape": "-3",
        "Delta_escape": "-393/2",
    }
    assert len(universal["Delta_polynomial"]) == 10
    assert rebuilt["classification"] == {
        "fixed_k_choice_dependent_special_phenomenon": True,
        "Zariski_generic_in_CSG_h_fixed_k_family": False,
        "valid_for_all_harmonic_k": False,
        "answer": "CASE_I_K_CHOICE_DEPENDENT_ZARISKI_SPECIAL",
    }


def test_scope_and_supplemental_branches_remain_separate(
    rebuilt: dict[str, Any],
) -> None:
    inventory = rebuilt["raw_inventory"]
    assert inventory == {
        "CSG_h_path_independence_failures": {},
        "actual_ON_orbits": 131,
        "fixed_vector_GC_path_count_used_for_CSG_h": 407,
        "raw_CPOBC_operator_equations": 783,
        "raw_CPOBC_scalar_entries": 3132,
        "rows_used_by_this_audit": 2,
        "remaining_scalar_entries_not_solved": 3130,
    }
    supplemental = rebuilt["separate_unresolved_ledgers"]
    assert supplemental["Eq113"]["derived_Qn_records"] == 25
    assert supplemental["Eq113"]["literal_Qn_plus_1_records"] == 25
    assert supplemental["Eq113"]["branches_kept_separate"] is True
    assert supplemental["Eq139"]["printed_strict_instances"] == 4
    assert supplemental["Eq139"]["Eq145_completed_instances"] == 10
    assert supplemental["Eq139"]["domains_kept_separate"] is True
    assert rebuilt["scope_exclusions"]["SR2V_terminal_verdict"] is False


def test_semantic_digest_rejects_a_dimension_mutation(rebuilt: dict[str, Any]) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["dimension_and_gauge_ledger"]["all_rank2_state_assignment_moduli"][
        "dimension"
    ] = 121
    assert audit.semantic_digest(mutated) != EXPECTED_SEMANTIC_DIGEST
