"""Exact guards for the global SR2-V bottom-MSR/CSG classification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as global_csg

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "d7978cac841bf725baa03df99aa661183a5c96367a2979b245b978f7d5dd08a4"
EXPECTED_SYSTEM_DIGEST = "0dbebe6206e2311b3e93fa98a43b9ba8d17490910b8ad63afbd8d6e98b69fd9f"
EXPECTED_CLEARED_DIGEST = "c1671278f0e12b48eb42d0af7deb4a468bb62d3ebcc01e7f3ac699c9aeac95ef"
EXPECTED_TRIANGULAR_DIGEST = "b682adfdf39e72050c66aa2b874887376cc82e50a39363a462c5f1ff64a28884"
EXPECTED_CSG_DIGEST = "e5e62838e558ce61fdcc6c2cbe5efbf1f9ce770a42388786a86f08c4a6076490"
EXPECTED_COORDINATE_DIGEST = "5eee27b5f7ce09b3bcdef69d591e1f0d38d7d9554b9cbd8e3c880c507c54b7ce"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return global_csg.build_payload(ROOT)


def test_global_artifact_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(global_csg.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == global_csg.SCHEMA
    assert frozen["verdict"] == global_csg.VERDICT
    assert frozen["search_terminal"] == global_csg.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert global_csg.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())
    for relative, binding in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == binding[
            "raw_sha256"
        ]


def test_all_24_laurent_equations_have_the_frozen_small_census(
    rebuilt: dict[str, Any],
) -> None:
    system = rebuilt["additive_MSR_system"]
    assert system["equation_count"] == 24
    assert system["source_stage_counts"] == {"p1": 1, "p2": 2, "p3": 5, "p4": 16}
    assert system["all_equations_distinct"] is True
    assert system["identically_zero_equations"] == []
    assert system["Q5_coordinate_occurs"] is False
    assert system["laurent_term_count"] == 145
    assert system["term_count_histogram"] == {
        "3": 1,
        "4": 2,
        "5": 4,
        "6": 9,
        "7": 4,
        "8": 4,
    }
    assert system["exponent_range"] == [-1, 1]
    assert system["maximum_parameter_support_per_equation"] == 8
    assert system["cleared_degree_histogram"] == {"2": 21, "3": 3}
    assert system["system_digest_sha256"] == EXPECTED_SYSTEM_DIGEST
    assert system["cleared_system_digest_sha256"] == EXPECTED_CLEARED_DIGEST


def test_the_cleared_system_is_globally_triangular(rebuilt: dict[str, Any]) -> None:
    certificate = rebuilt["global_triangular_classification"]
    assert certificate["pivot_indices"] == list(global_csg.PIVOT_INDICES)
    assert certificate["free_indices"] == list(global_csg.FREE_INDICES)
    assert certificate["free_coordinates"] == ["s18", "s21", "s25", "s26", "s28"]
    assert certificate["actual_edge_free_coordinates"] == ["s18", "s21", "s25", "s26"]
    assert certificate["cutoff_external_free_coordinate"] == "s28"
    assert len(certificate["records"]) == 24
    assert certificate["all_24_back_substitutions_are_zero"] is True
    assert certificate["records_digest_sha256"] == EXPECTED_TRIANGULAR_DIGEST

    first, second = certificate["records"][:2]
    assert first["constraint_id"] == "msr:p1-0"
    assert first["pivot_coordinate"] == "s24"
    assert first["pivot_coefficient"] == "s18*s21 + s25*s26"
    assert first["right_side"] == "s25*s26"
    assert first["solution"]["display"] == "s25*s26/(s18*s21 + s25*s26)"
    assert second["constraint_id"] == "msr:p2-0"
    assert second["pivot_coordinate"] == "s22"
    assert second["pivot_coefficient"] == "s18*s21 + s18*s26 + 2*s25*s26"
    assert second["right_side"] == "s18*s21"


def test_pivot_jacobian_is_a_unit_on_every_torus_solution(
    rebuilt: dict[str, Any],
) -> None:
    jacobian = rebuilt["global_triangular_classification"]["pivot_jacobian"]
    assert jacobian["shape"] == [24, 24]
    assert jacobian["strictly_above_diagonal_is_zero"] is True
    assert jacobian["diagonal"][2] == "s18*s22"
    assert jacobian["sequential_reduced_pivot_coefficients"][2] == (
        "s18**2*s21/(s18*s21 + s18*s26 + 2*s25*s26)"
    )
    assert jacobian["determinant"] == (
        "s18**21*s22*s26*(s18*s21 + s25*s26)*"
        "(s18*s21 + s18*s26 + 2*s25*s26)"
    )
    assert jacobian["quotient_ring_unit_form"] == "s18**22*s21*s25*s26**2/s24"
    assert jacobian["rank_on_every_torus_solution"] == 24


def test_global_parameterisation_is_exactly_the_finite_csg_family(
    rebuilt: dict[str, Any],
) -> None:
    csg = rebuilt["finite_CSG_identification"]
    assert csg["normalisation"] == "t0=1"
    assert csg["forward_map_to_selected_laurent_coordinates"] == {
        "s18": "t2/(3*t1 + 3*t2 + t3 + 1)",
        "s21": "1/(4*t1 + 6*t2 + 4*t3 + t4 + 1)",
        "s25": "t1/(3*t1 + 3*t2 + t3 + 1)",
        "s26": "t2/(4*t1 + 6*t2 + 4*t3 + t4 + 1)",
        "s28": "q5",
    }
    assert csg["inverse_map"] == {
        "t1": "s25*s26/(s18*s21)",
        "t2": "s26/s21",
        "t3": "-(s18*s21 + 3*s18*s26 + 3*s25*s26 - s26)/(s18*s21)",
        "t4": "(3*s18*s21 + 6*s18*s26 + s18 + 8*s25*s26 - 4*s26)/(s18*s21)",
        "q5": "s28",
    }
    checks = csg["direct_symbolic_checks"]
    assert checks["operator_monomial_rows"] == 843
    assert checks["fixed_vector_GC_monomial_rows"] == 320
    assert checks["combined_monomial_rows"] == 1163
    assert checks["additive_MSR_rows"] == 24
    assert checks["primitive_Laurent_coordinates_reconstructed"] == 132
    assert checks["actual_transition_coordinates_matching_CSG"] == 131
    assert checks["distinct_actual_transition_formulas"] == 24
    assert checks["monomial_failures"] == []
    assert checks["additive_MSR_failures"] == []
    assert checks["coordinate_failures"] == []
    assert checks["triangular_CSG_failures"] == []
    assert csg["all_132_coordinate_identities_digest_sha256"] == EXPECTED_COORDINATE_DIGEST
    assert csg["parameterisation_digest_sha256"] == EXPECTED_CSG_DIGEST


def test_global_scheme_scope_and_supersession_are_explicit(
    rebuilt: dict[str, Any],
) -> None:
    csg = rebuilt["finite_CSG_identification"]
    assert csg["scheme_properties"] == {
        "dimension": 5,
        "codimension_inside_Gm29": 24,
        "smooth": True,
        "irreducible": True,
        "rational": True,
    }
    supersession = rebuilt["supersession"]
    assert supersession["local_certificate"] == global_csg.LOCAL_CERTIFICATE_PATH
    assert supersession["superseded_boundary"] == "global_additive_MSR_variety_classified=False"
    assert "selected minor -5/2^45" in supersession["preserved_local_results"]

    boundary = rebuilt["resource_and_claim_boundaries"]
    assert boundary["global_bottom_scalar_locus_classified"] is True
    assert boundary["upper_operator_Gm49_classified_beyond_monomial_lattice"] is False
    assert boundary["upper_right_cocycle_fibre_solved"] is False
    assert boundary["commutator_principal_open_tested"] is False
    assert boundary["state_native_D12_manifest_modified_or_used"] is False
    assert rebuilt["witness"] is None
    assert "does not constrain the separate upper G_m^49" in rebuilt["claim_boundary"]
    assert "does not" in rebuilt["claim_boundary"]


def test_semantic_digest_rejects_a_global_dimension_mutation(
    rebuilt: dict[str, Any],
) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["finite_CSG_identification"]["scheme_properties"]["dimension"] = 4
    assert global_csg.semantic_digest(mutated) != EXPECTED_SEMANTIC_DIGEST
