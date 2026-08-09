"""Regression checks for the exact v0.4.2 955 symmetry and orbit reduction gate."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_symmetry_orbit_reduction_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH
MIXED_MANIFEST = ROOT / gate.MIXED_MANIFEST_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_symmetry_orbit_reduction_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_gauge_torus_grading_is_certified_over_the_whole_frozen_manifest() -> None:
    torus = _compiled()["gauge_torus"]

    assert torus["verdict"] == gate.TORUS_VERDICT
    assert torus["violations"] == 0
    assert torus["matrix_block_terms_checked"] == 22180
    assert torus["vector_terms_checked"] == 986
    assert torus["Q_commutator_terms_checked"] == 48
    assert torus["per_block"]["CPOBC"]["records"] == 783
    assert torus["per_block"]["strong_GC"]["records"] == 320
    assert torus["per_block"]["reachable_MSR_operator"]["records"] == 24
    assert torus["per_block"]["reachable_MSR_vector"]["records"] == 24
    assert torus["reduction_consequence"]["free_parameters"] == 1
    assert torus["relation_variety_is_a_union_of_G_m_orbits"] is True


def test_grading_is_independently_rechecked_against_the_manifest() -> None:
    manifest = json.loads(MIXED_MANIFEST.read_text(encoding="utf-8"))
    blocks = manifest["residual_blocks"]

    matrix_terms = 0
    for name in ("CPOBC", "strong_GC", "reachable_MSR_operator"):
        for record in blocks[name]["records"]:
            for key, polynomial in record["entries"].items():
                expected = int(key[1]) - int(key[0])
                for term in polynomial:
                    matrix_terms += 1
                    assert gate._monomial_grade(term["monomial"]) == expected
    assert matrix_terms == 22180

    vector_terms = 0
    for record in blocks["reachable_MSR_vector"]["records"]:
        for key, polynomial in record["entries"].items():
            for term in polynomial:
                vector_terms += 1
                assert gate._monomial_grade(term["monomial"]) == -int(key)
    assert vector_terms == 986


def test_preparation_vector_and_stabiliser_boundaries_are_recorded() -> None:
    torus = _compiled()["gauge_torus"]

    assert torus["preparation_vector_is_g_t_eigenvector"]["vector"] == "e_1"
    assert any("full stabiliser" in claim for claim in torus["nonclaims"])
    assert "own proof" in torus["no_degeneration_to_the_pure_families"]["consequence"]


def test_symmetry_refinement_is_discrete_and_pins_the_four_Q_generators() -> None:
    symmetry = _compiled()["combinatorial_symmetry"]

    assert symmetry["equation_inventory"] == {
        "CPOBC": 783,
        "reachable_state_MSR": 24,
        "strong_GC": 320,
    }
    assert sorted(symmetry["Q_orbits"].values()) == [1, 2, 3, 4]
    assert symmetry["incidence_label_is_side_agnostic"] is True
    assert symmetry["initial_colour_classes"] == 23
    assert symmetry["initial_equation_colour_classes"] == 5
    assert symmetry["stable_colour_classes"] == 131
    assert symmetry["class_size_histogram"] == {"1": 131}
    assert symmetry["nontrivial_classes"] == []
    assert symmetry["discrete"] is True
    assert [entry["orbit_classes"] for entry in symmetry["refinement_history"]] == [131, 131, 131]


def test_no_patch_reduction_is_claimed_and_no_permutation_is_emitted() -> None:
    payload = _compiled()
    outcome = payload["reduction_outcome"]
    soundness = payload["soundness_boundary"]

    assert payload["verdict"] == gate.TRIVIAL_VERDICT
    assert outcome["patches_before"] == 131
    assert outcome["symmetry_orbit_upper_bound_on_distinct_patches"] == 131
    assert outcome["patches_removed_by_symmetry"] == 0
    assert outcome["gauge_parameters_removed"] == 1
    assert outcome["brute_force_131_patch_sweep_authorised"] is False
    assert soundness["colouring_is_a_coarsening_of_the_true_symmetry_orbits"] is True
    assert soundness["discrete_implies_trivial_symmetry_group"] is True
    assert soundness["explicit_permutation_certificates_emitted"] == 0


def test_scout_schedule_is_declared_but_not_executed() -> None:
    schedule = _compiled()["deterministic_scout_schedule"]

    assert schedule["executed"] is False
    assert len(schedule["head"]) == 8
    assert [entry["rank"] for entry in schedule["head"]] == list(range(1, 9))
    assert all(entry["patch"].startswith("y_[") for entry in schedule["head"])


def test_gate_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()
    solver = payload["solver_status"]

    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
    assert solver == {
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
    assert payload["predecessor_binding"]["kind"] == "CANONICAL_JSON_SEMANTIC_DIGEST"
