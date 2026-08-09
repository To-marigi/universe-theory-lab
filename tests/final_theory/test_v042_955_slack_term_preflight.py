"""Regression checks for the streamed unrestricted 955 slack preflight."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH
SLACK = ROOT / gate.SLACK_INVENTORY_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_term_preflight_v042(ROOT)


@cache
def _slack() -> dict[str, Any]:
    return json.loads(SLACK.read_text(encoding="utf-8"))


@cache
def _expanded() -> tuple[dict[str, gate.Matrix], dict[str, gate.Vector], list[str]]:
    names: list[str] = []
    matrices, states, _profile = gate._compile_matrices(_slack(), names)
    return matrices, states, names


def test_frozen_result_regenerates_exactly_and_binds_its_semantic_digest() -> None:
    frozen = json.loads(RESULT.read_text(encoding="utf-8"))

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == (
        "b61d611830ff89815b9046b8df3a8b284f6716cdeb687c4d2bb7bb960e5190ab"
    )
    assert frozen["verdict"] == gate.VERDICT


def test_476_coordinate_namespace_is_unique_and_has_the_expected_partition() -> None:
    namespace = _compiled()["variable_namespace"]
    names = namespace["names"]

    assert namespace["coordinates"] == len(names) == len(set(names)) == 476
    assert namespace["independent_matrix_entries"] == 428
    assert namespace["reachable_MSR_slack_coordinates"] == 48
    assert sum(name.startswith("A:") for name in names) == 428
    assert sum(name.startswith("u:") for name in names) == 48
    assert namespace["names_sha256"] == (
        "e5c9a43acd2760e185336c13cdab9ec6e4413e2b33b947ec65f9d246dd2c1982"
    )


def test_every_expanded_timid_residual_annihilates_its_reachable_state() -> None:
    matrices, states, _names = _expanded()
    ledger = gate.OperationLedger()
    checked = 0

    for record in _slack()["timid_slack_recurrences"]:
        representative = record["timid_orbit_representative"]
        residual = gate._matrix_add(
            matrices[representative],
            gate._matrix_scale(-1, gate._identity(), ledger),
            ledger,
        )
        for operator, coefficient in zip(
            record["non_timid_orbit_representatives"],
            record["non_timid_coefficients"],
            strict=True,
        ):
            residual = gate._matrix_add(
                residual,
                gate._matrix_scale(int(coefficient), matrices[operator], ledger),
                ledger,
            )
        value = gate._matrix_vector(residual, states[record["source_id"]], ledger)
        assert value == ({}, {})
        checked += 1

    assert checked == 24


def test_streamed_core_counts_and_content_digests_are_exact() -> None:
    streamed = _compiled()["streamed_core_system"]
    cpobc = streamed["per_block"]["CPOBC"]
    strong_gc = streamed["per_block"]["strong_GC"]
    combined = streamed["combined"]

    assert streamed["matrix_equation_blocks"] == 1103
    assert combined["scalar_entry_slots"] == 4412
    assert combined["nonzero_scalar_entries"] == 4152
    assert combined["identically_zero_scalar_entries"] == 260
    assert combined["total_terms"] == 101_200
    assert combined["maximum_terms_in_one_entry"] == 3723
    assert combined["maximum_total_degree"] == 9
    assert combined["maximum_coefficient_bit_length"] == 3

    assert (cpobc["scalar_entry_slots"], cpobc["total_terms"]) == (3132, 18_836)
    assert cpobc["identically_zero_scalar_entries"] == 0
    assert cpobc["maximum_terms_in_one_entry"] == 24
    assert cpobc["maximum_total_degree"] == 4
    assert cpobc["stream_digest_sha256"] == (
        "74bdc9d908f4492cda28813f25a0eeb7561f33656ac0779b8a27e47c92f193d5"
    )

    assert (strong_gc["scalar_entry_slots"], strong_gc["total_terms"]) == (1280, 82_364)
    assert strong_gc["identically_zero_scalar_entries"] == 260
    assert strong_gc["maximum_terms_in_one_entry"] == 3723
    assert strong_gc["maximum_total_degree"] == 9
    assert strong_gc["stream_digest_sha256"] == (
        "a8d7ac699a944927db5e689ba9008021829dc26f0fb59e544c18f60caec37825"
    )
    assert streamed["full_scalar_polynomials_retained"] is False


def test_sixteen_terminal_stage_slack_coordinates_are_absent_from_the_core() -> None:
    support = _compiled()["streamed_core_system"]["variable_support"]
    absent = support["coordinates_absent_from_entire_core"]

    assert support["coordinates_total"] == 476
    assert support["coordinates_occurring_in_union"] == 460
    assert support["entirely_absent_coordinate_count"] == 16
    assert support["all_entirely_absent_coordinates_are_slack"] is True
    assert absent == [
        f"u:{source}:{coordinate}"
        for source in (
            "p4-0000",
            "p4-000e",
            "p4-00cc",
            "p4-00ce",
            "p4-0888",
            "p4-088e",
            "p4-08cc",
            "p4-08ce",
        )
        for coordinate in range(2)
    ]


def test_no_exact_linear_equation_survives_but_the_degree_one_component_has_rank_304() -> None:
    linear = _compiled()["exact_linear_structure"]

    assert linear["exact_linear_nonzero_scalar_equations"] == 0
    assert linear["coefficient_matrix_rank"] == 0
    assert linear["augmented_matrix_rank"] == 0
    assert linear["linear_subsystem_consistent"] is True
    assert linear["degree_one_component_rows"] == 772
    assert linear["degree_one_component_rank"] == 304
    assert linear["degree_one_component_echelon_digest_sha256"] == (
        "1c58c2135b4a23af68a8ee03cbbb3c77ac68f6bd8b68a98d23064e550f7d3f3f"
    )


def test_determinants_are_nonzero_and_no_solver_or_full_manifest_is_authorised() -> None:
    payload = _compiled()
    determinant = payload["nonsingularity_preflight"]["determinant_profile"]

    assert determinant["scalar_entry_slots"] == determinant["nonzero_scalar_entries"] == 131
    assert determinant["total_terms"] == 6250
    assert determinant["maximum_terms_in_one_entry"] == 986
    assert determinant["maximum_total_degree"] == 5
    assert payload["nonsingularity_preflight"]["separate_inverse_coordinate_presentation"] == {
        "additional_coordinates": 131,
        "localisation_equations": 131,
        "total_terms": 6381,
        "maximum_terms_in_one_equation": 987,
        "maximum_total_degree": 6,
        "form": "rho_e*det(A_e)-1=0 for each of 131 quotient matrices",
        "compiled_polynomials_retained": False,
    }
    assert payload["execution_decision"]["heavy_solver_authorised"] is False
    assert payload["solver_status"] == {
        "streamed_scalar_expansion_runs": 1,
        "full_manifest_materialisations": 0,
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
