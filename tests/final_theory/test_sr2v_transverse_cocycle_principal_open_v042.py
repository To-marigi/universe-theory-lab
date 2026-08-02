"""Exact guards for the four branch-separated transverse cocycle matrices."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as open_
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "07e60a4d6b029d3cf08efd3ef3aae14598a1614090d3809d764973065b35eaf0"
EXPECTED_JOINT_MATRIX_DIGEST = (
    "dbfbc363201519cfef1c629382ee48afc2e86b969e39ebd1e101438f51a5f4ad"
)
EXPECTED_BRANCH_DIGESTS = {
    open_.DERIVED_STRICT: {
        "matrix": "9f4480c65143b8edd21fdd1e95e3861e2103b3cf7e912f709353afb861136b04",
        "selected": "e439194cf1cd0974cbf085fe28172fcb7da1c8b9001730b68b04e2916d71e170",
        "minor": "b283b22ccf965957946e4a8083a1ad370f288b9c14681ed5a5e217788e24ac93",
    },
    open_.DERIVED_COMPLETED: {
        "matrix": "da6ca66f69b33533423473eeb62bc7a550013244f902f3ebc7a1002b29fbb053",
        "selected": "27e32f82ccf0d108b18ed08a932be964028b3ad00bb782df9c05269a3449af1a",
        "minor": "e7ba28a8ff2979d51a413baec7a9f9d7f1d95891489a4c74409520b0acddfee6",
    },
    open_.LITERAL_STRICT: {
        "matrix": "84d5d915c7e3d4cc798217a3a5270470810e2d85ee41df8b675627daa6ca4466",
        "selected": "09144b7d8303e6b4f9e4d554ab6084f36e188743057f5792e18bdf5051b34e32",
        "minor": "becf31049ae10da021c898d3725127b94e1f0c095f4a8020d7bfdfe4f12d9c2c",
    },
    open_.LITERAL_COMPLETED: {
        "matrix": "c3d78f0def692986d437cf334a7505f276f08118cefbe7b538a89f53cafe8b30",
        "selected": "ddfd96f2d667b9bc29568a08051ead23f4931d8b16205b66b480ed55abbb283a",
        "minor": "e527e69b7313fcf200ae3c512e81843e098078264154facd34e7f41e6e03c863",
    },
}


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return open_.build_payload(ROOT)


def test_branch_separated_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(open_.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == open_.SCHEMA
    assert frozen["verdict"] == open_.VERDICT
    assert frozen["search_terminal"] == open_.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert open_.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())
    for relative, binding in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == binding[
            "raw_sha256"
        ]


def test_exact_scalar_base_point_is_fully_certified(rebuilt: dict[str, Any]) -> None:
    point = rebuilt["exact_scalar_base_point"]
    upper = point["upper"]
    assert upper["candidate_id"] == "basis-plus-20"
    assert upper["primitive_kernel_column"] == 20
    assert upper["base"] == 2
    assert len(upper["exponents_in_variable_order"]) == 132
    assert len(upper["nonzero_exponent_coordinates"]) == 7
    assert upper["all_843_operator_monomial_rows_hold"] is True

    bottom = point["bottom"]
    assert bottom["family"] == "normalized finite CSG t0=t1=t2=t3=t4=1"
    assert bottom["cutoff_external_Q5"] == "1/32"
    assert len(bottom["coordinates_in_variable_order"]) == 132
    assert bottom["all_1163_bottom_monomial_rows_hold"] is True
    assert bottom["all_24_additive_MSR_rows_hold"] is True

    nonsingularity = point["nonsingularity"]
    assert nonsingularity["occurrences_checked"] == 165
    assert nonsingularity["occurrence_determinant_failures"] == []
    assert nonsingularity["supplemental_Q5_determinant"] == "1/32"
    assert nonsingularity["all_165_occurrences_and_Q5_are_nonsingular"] is True


def test_eq113_and_eq139_are_alternative_not_joint_assumptions(
    rebuilt: dict[str, Any],
) -> None:
    rule = rebuilt["semantic_branch_rule"]
    assert rule == {
        "Eq113": "derived and literal readings are alternative branches, never simultaneous",
        "Eq139": "printed-strict and Eq145-completed domains are alternative branches",
        "matrix_count": 4,
        "joint_all_readings_inference_forbidden": True,
    }
    provenance = rebuilt["row_provenance"]
    assert provenance["Eq113_branches_merged"] is False
    assert provenance["Eq139_domains_merged"] is False
    assert provenance["common_counts"] == {
        "CPOBC": 783,
        "fixed_vector_GC_basis": 320,
        "reachable_state_MSR": 24,
    }
    assert provenance["alternative_counts"] == {
        "Eq113_derived": 25,
        "Eq113_literal": 25,
        "Eq139_printed_strict": 4,
        "Eq139_completed": 10,
    }
    ledgers = provenance["full_row_id_ledgers"]
    assert len(ledgers["CPOBC"]["row_ids"]) == 783
    assert len(ledgers["fixed_vector_GC_basis"]["row_ids"]) == 320
    assert len(ledgers["reachable_state_MSR"]["row_ids"]) == 24
    assert len(
        ledgers["Eq113_alternative_branches"][torus.EQ113_DERIVED]["row_ids"]
    ) == 25
    assert len(
        ledgers["Eq113_alternative_branches"][torus.EQ113_LITERAL]["row_ids"]
    ) == 25
    eq139 = ledgers["Eq139_alternative_domains"]
    assert len(eq139["printed_strict"]["row_ids"]) == 4
    assert len(eq139["eq145_completed"]["row_ids"]) == 10


def test_all_four_branch_matrices_have_fixed_exact_ranks_and_rows(
    rebuilt: dict[str, Any],
) -> None:
    branches = rebuilt["semantic_branch_certificates"]
    assert set(branches) == set(open_.EXPECTED_RANKS)
    for branch_id, expected_rank in open_.EXPECTED_RANKS.items():
        branch = branches[branch_id]
        expected_rows = 1156 if branch["Eq139_domain"] == torus.EQ139_STRICT else 1162
        assert branch["matrix_shape"] == [expected_rows, 132]
        assert branch["rank_at_exact_base_point"] == expected_rank
        assert branch["nullity_at_exact_base_point"] == 132 - expected_rank
        assert branch["selected_independent_row_count"] == expected_rank
        assert branch["selected_source_joint_inventory_rows"] == list(
            open_.EXPECTED_SOURCE_SELECTIONS[branch_id]
        )
        assert len(branch["selected_rows"]) == expected_rank
        assert branch["matrix_row_digest_sha256"] == EXPECTED_BRANCH_DIGESTS[
            branch_id
        ]["matrix"]
        assert branch["selected_rows_digest_sha256"] == EXPECTED_BRANCH_DIGESTS[
            branch_id
        ]["selected"]
        assert branch["all_131_actual_transition_columns_are_pivots"] is True


def test_literal_branches_have_independent_nonzero_exact_minors(
    rebuilt: dict[str, Any],
) -> None:
    branches = rebuilt["semantic_branch_certificates"]
    expected_factors = {
        open_.LITERAL_STRICT: {
            "sign": -1,
            "numerator_prime_powers": {"3": 18, "5": 4, "7": 1, "31": 1},
            "denominator_prime_powers": {"2": 299},
        },
        open_.LITERAL_COMPLETED: {
            "sign": 1,
            "numerator_prime_powers": {"3": 19, "5": 5, "7": 2, "31": 1},
            "denominator_prime_powers": {"2": 296},
        },
    }
    expected_blocks = {
        open_.LITERAL_STRICT: {
            "CPOBC": 108,
            torus.EQ113_LITERAL: 1,
            torus.EQ139_STRICT: 1,
            "fixed_vector_GC_basis": 6,
            "reachable_state_MSR": 16,
        },
        open_.LITERAL_COMPLETED: {
            "CPOBC": 108,
            torus.EQ113_LITERAL: 1,
            torus.EQ139_COMPLETED: 2,
            "fixed_vector_GC_basis": 6,
            "reachable_state_MSR": 15,
        },
    }
    for branch_id in (open_.LITERAL_STRICT, open_.LITERAL_COMPLETED):
        branch = branches[branch_id]
        determinant = str(open_.EXPECTED_DETERMINANTS[branch_id])
        minor = branch["full_rank_minor"]
        assert branch["selected_row_block_counts"] == expected_blocks[branch_id]
        assert branch["all_132_columns_are_pivots"] is True
        assert minor["tracked_elimination_determinant"] == determinant
        assert minor["direct_sympy_determinant"] == determinant
        assert minor["column_permutation_inversion_parity"] == 1
        assert minor["prime_factorisation"] == expected_factors[branch_id]
        assert minor["selected_matrix_digest_sha256"] == EXPECTED_BRANCH_DIGESTS[
            branch_id
        ]["minor"]
        principal_open = branch["formal_principal_open"]
        assert principal_open["exact_nonzero_evaluation"] == determinant
        assert principal_open["principal_open_is_nonempty"] is True
        assert principal_open["rank_on_principal_open"] == 132
        assert principal_open["unique_kernel"] == "x=0"
        assert principal_open["Q1_through_Q4_conclusion"] == (
            "diagonal and pairwise commuting"
        )


def test_derived_branches_have_actual_column_minors_and_decoupled_q5(
    rebuilt: dict[str, Any],
) -> None:
    branches = rebuilt["semantic_branch_certificates"]
    expected_blocks = {
        open_.DERIVED_STRICT: {
            "CPOBC": 108,
            torus.EQ113_DERIVED: 1,
            torus.EQ139_STRICT: 1,
            "fixed_vector_GC_basis": 5,
            "reachable_state_MSR": 16,
        },
        open_.DERIVED_COMPLETED: {
            "CPOBC": 108,
            torus.EQ113_DERIVED: 1,
            torus.EQ139_COMPLETED: 2,
            "fixed_vector_GC_basis": 5,
            "reachable_state_MSR": 15,
        },
    }
    expected_kernel = [
        {"column": 131, "variable": torus.Q5, "coefficient": "1"}
    ]
    expected_factors = {
        open_.DERIVED_STRICT: {
            "sign": 1,
            "numerator_prime_powers": {"3": 18, "5": 4, "7": 1, "31": 1},
            "denominator_prime_powers": {"2": 298},
        },
        open_.DERIVED_COMPLETED: {
            "sign": 1,
            "numerator_prime_powers": {"3": 19, "5": 5, "7": 2, "31": 1},
            "denominator_prime_powers": {"2": 295},
        },
    }
    expected_parity = {open_.DERIVED_STRICT: 0, open_.DERIVED_COMPLETED: 1}
    for branch_id in (open_.DERIVED_STRICT, open_.DERIVED_COMPLETED):
        branch = branches[branch_id]
        assert branch["selected_row_block_counts"] == expected_blocks[branch_id]
        assert branch["all_132_columns_are_pivots"] is False
        kernel = branch["rank_131_base_point_kernel"]
        assert kernel["nonzero_coordinates"] == expected_kernel
        assert kernel["direct_row_failures"] == []
        assert kernel["digest_sha256"] == (
            "57b48aab8f96474ad435e4fbe078c66d6f05d579c363ac0cdda6fc9e698ad001"
        )
        determinant = str(open_.EXPECTED_ACTUAL_131_DETERMINANTS[branch_id])
        minor = branch["actual_131_column_minor"]
        assert minor["tracked_elimination_determinant"] == determinant
        assert minor["direct_sympy_determinant"] == determinant
        assert minor["column_permutation_inversion_parity"] == expected_parity[branch_id]
        assert minor["prime_factorisation"] == expected_factors[branch_id]
        assert minor["selected_matrix_digest_sha256"] == EXPECTED_BRANCH_DIGESTS[
            branch_id
        ]["minor"]
        principal_open = branch["formal_principal_open"]
        assert principal_open["minor_shape"] == [131, 131]
        assert principal_open["exact_nonzero_evaluation"] == determinant
        assert principal_open["principal_open_is_nonempty"] is True
        assert principal_open["rank_on_principal_open"] == 131
        assert principal_open["kernel_on_principal_open"] == "span(e_Q5)"
        assert principal_open["actual_transition_cocycle"] == "x_actual=0"
        assert principal_open["cutoff_external_Q5_cocycle"] == (
            "free and universally decoupled"
        )
        assert branch["branch_status"] == (
            "ACTUAL_131_COLUMN_FULL_RANK_PRINCIPAL_OPEN_CERTIFIED_Q5_FREE_DECOUPLED"
        )
    status = rebuilt["derived_branch_status"]
    assert status["full_132_column_principal_open_certified"] is False
    assert status["actual_131_column_principal_opens_certified"] is True
    assert status["universal_kernel_direction"] == "cutoff-external Q5"
    assert status["Q1_through_Q4_splitting_on_each_open"] is True


def test_q5_decoupling_is_a_universal_source_and_word_identity(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["universal_cutoff_Q5_decoupling"]
    assert certificate["coordinate"] == torus.Q5
    assert certificate["column"] == 131
    assert certificate["actual_transition_column_count"] == 131
    assert certificate["common_source_Q5_failures"] == {
        "CPOBC": [],
        "fixed_vector_GC_paths": [],
        "reachable_state_MSR": [],
    }
    assert certificate["Eq113_Q5_token_occurrences"] == {
        torus.EQ113_DERIVED: 0,
        torus.EQ113_LITERAL: 48,
    }
    assert certificate["Eq113_Q_tokens"] == {
        torus.EQ113_DERIVED: ["Q_3", "Q_4"],
        torus.EQ113_LITERAL: ["Q_4", "Q_5"],
    }
    assert certificate["Eq139_stage_four_instances_where_next_Q_is_Q5"] == {
        "printed_strict": [[4, 1, 2], [4, 1, 3], [4, 2, 3]],
        "eq145_completed": [
            [4, 1, 2],
            [4, 1, 3],
            [4, 1, 4],
            [4, 2, 3],
            [4, 2, 4],
            [4, 3, 4],
        ],
    }
    assert certificate["Eq139_universal_next_Q_coefficient_template"] == {
        "lhs": "a_left*a_right/b_q",
        "rhs": "a_left*a_right/b_q",
        "difference": "0",
        "localisation_denominator": "b_q",
    }
    assert certificate["derived_Eq113_strict_universal_Q5_column_is_zero"] is True
    assert certificate["derived_Eq113_completed_universal_Q5_column_is_zero"] is True


def test_joint_matrix_is_auxiliary_and_cannot_support_branch_inference(
    rebuilt: dict[str, Any],
) -> None:
    joint = rebuilt["joint_all_readings_auxiliary"]
    assert joint["matrix_shape"] == [1187, 132]
    assert joint["rank_at_base_point"] == 132
    assert joint["matrix_row_digest_sha256"] == EXPECTED_JOINT_MATRIX_DIGEST
    assert joint["semantic_status"] == (
        "AUXILIARY_OVERCONSTRAINED_INTERSECTION_ONLY_NO_BRANCH_INFERENCE"
    )
    assert joint["used_for_any_principal_open_conclusion"] is False
    conclusion = rebuilt["literal_branch_principal_open_conclusion"]
    assert conclusion["Eq139_domains_covered_separately"] == [
        torus.EQ139_STRICT,
        torus.EQ139_COMPLETED,
    ]
    assert conclusion["each_principal_open_is_nonempty"] is True
    assert conclusion["operator_conclusion_on_each_open"] == (
        "Q1,Q2,Q3,Q4 are diagonal and pairwise commuting"
    )
    all_four = rebuilt["all_four_branch_principal_open_conclusion"]
    assert all_four["branches_covered_separately"] == [
        open_.DERIVED_STRICT,
        open_.DERIVED_COMPLETED,
        open_.LITERAL_STRICT,
        open_.LITERAL_COMPLETED,
    ]
    assert all_four["each_principal_open_is_nonempty"] is True
    assert all_four["actual_transition_kernel_on_each_open"] == "x_actual=0"
    assert all_four["operator_conclusion_on_each_open"] == (
        "Q1,Q2,Q3,Q4 are diagonal and pairwise commuting"
    )


def test_claim_is_scoped_away_from_open_loci_and_d12(rebuilt: dict[str, Any]) -> None:
    boundary = rebuilt["resource_and_claim_boundaries"]
    assert boundary["solver_status"] == "NOT_RUN"
    assert boundary["groebner_status"] == "NOT_RUN"
    assert boundary["determinants_expanded_over_54_base_parameters"] is False
    assert boundary["literal_determinant_zero_hypersurfaces_solved"] is False
    assert boundary["derived_actual_determinant_zero_hypersurfaces_solved"] is False
    assert boundary["derived_Eq113_branches_globally_solved"] is False
    assert boundary["full_transverse_scalar_base_obstructed"] is False
    assert boundary["pair_or_triple_irreducible_branch_touched"] is False
    assert boundary["state_native_D12_manifest_touched"] is False
    assert boundary["global_weak_weak_obstruction_claimed"] is False
    assert rebuilt["witness"] is None
    assert "never combines alternative semantic readings" in rebuilt["claim_boundary"]
    assert "131-by-131" in rebuilt["claim_boundary"]
    assert "state-native D12" in rebuilt["claim_boundary"]


def test_semantic_digest_rejects_a_branch_rank_mutation(
    rebuilt: dict[str, Any],
) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["semantic_branch_certificates"][open_.DERIVED_STRICT][
        "rank_at_exact_base_point"
    ] = 132
    assert open_.semantic_digest(mutated) != EXPECTED_SEMANTIC_DIGEST
