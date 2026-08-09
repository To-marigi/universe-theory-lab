"""Regression checks for the v0.4.2 unrestricted-slack coverage gap."""

from __future__ import annotations

import json
from collections import Counter
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_coverage_gap_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH
SLACK = ROOT / gate.SLACK_INVENTORY_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_slack_coverage_gap_v042(ROOT)


@cache
def _slack() -> dict[str, Any]:
    return json.loads(SLACK.read_text(encoding="utf-8"))


def _operator(symbol: str) -> str:
    assert symbol.startswith("A:")
    return symbol[2:]


def _independent_degree_propagation() -> tuple[dict[str, int], dict[str, int]]:
    slack = _slack()
    representatives = {
        record["representative_occurrence_id"]
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    timid_to_source = {
        record["timid_orbit_representative"]: record["source_id"]
        for record in slack["timid_slack_recurrences"]
    }
    paths = {
        record["source_id"]: [_operator(symbol) for symbol in record["operator_word_later_on_left"]]
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }

    matrix_degree = {
        representative: 1 for representative in representatives - timid_to_source.keys()
    }
    state_degree: dict[str, int] = {}
    pending = set(timid_to_source)
    while pending:
        ready = [
            representative
            for representative in pending
            if all(operator in matrix_degree for operator in paths[timid_to_source[representative]])
        ]
        assert ready
        for representative in ready:
            source_id = timid_to_source[representative]
            state_degree[source_id] = sum(matrix_degree[operator] for operator in paths[source_id])
            matrix_degree[representative] = max(1, 1 + state_degree[source_id])
            pending.remove(representative)
    return matrix_degree, state_degree


def _equation_degrees(records: list[dict[str, Any]], matrix_degree: dict[str, int]) -> list[int]:
    result = []
    for record in records:
        left = sum(matrix_degree[_operator(symbol)] for symbol in record["lhs_source_word"])
        right = sum(matrix_degree[_operator(symbol)] for symbol in record["rhs_source_word"])
        result.append(max(left, right))
    return result


def test_frozen_result_regenerates_exactly_and_has_a_valid_semantic_digest() -> None:
    frozen = json.loads(RESULT.read_text(encoding="utf-8"))

    assert frozen == _compiled()
    assert frozen["semantic_digest_sha256"] == gate._semantic_digest(frozen)
    assert frozen["verdict"] == gate.VERDICT


def test_timid_elimination_gives_the_exact_572_to_476_effective_chart() -> None:
    chart = _compiled()["effective_slack_chart"]

    assert chart == {
        "general_quotient_operator_matrices": 131,
        "general_operator_scalar_entries": 524,
        "reachable_state_slack_coordinates": 48,
        "coordinates_before_timid_elimination": 572,
        "timid_matrix_definitions": 24,
        "monic_triangular_scalar_pivots": 96,
        "independent_non_timid_matrices": 107,
        "effective_coordinates_after_timid_elimination": 476,
        "triangular_elimination_is_exact": True,
    }

    recurrences = _slack()["timid_slack_recurrences"]
    timid = [record["timid_orbit_representative"] for record in recurrences]
    assert len(timid) == len(set(timid)) == 24
    assert all(
        record["timid_definition"]["lhs"] == f"A:{representative}"
        for record, representative in zip(recurrences, timid, strict=True)
    )


def test_dimension_two_annihilator_parameterisation_is_complete_on_both_patches() -> None:
    certificate = _compiled()["dimension_two_annihilator_parameterisation"]

    assert certificate["cover"] == ["v0!=0", "v1!=0"]
    assert certificate["slack_chart_complete_for_reachable_state_MSR_on_nonsingular_locus"]

    for v0, v1, u0, u1 in [(2, 3, 5, 7), (-4, 9, 2, -3), (0, 6, 8, 1), (11, 0, -2, 4)]:
        residual = [[-u0 * v1, u0 * v0], [-u1 * v1, u1 * v0]]
        assert [row[0] * v0 + row[1] * v1 for row in residual] == [0, 0]
        if v0:
            assert [row[1] / v0 for row in residual] == [u0, u1]
        if v1:
            assert [-row[0] / v1 for row in residual] == [u0, u1]


def test_mixed_ansatz_cuts_214_distinct_independent_diagonal_coordinates() -> None:
    locus = _compiled()["mixed_ansatz_as_diagonal_restriction_locus"]
    direct = locus["direct_constraints"]

    assert locus["independent_non_timid_matrices"] == 107
    assert len(direct) == locus["direct_coordinate_linear_diagonal_constraints"] == 214
    assert locus["direct_linear_rank"] == 214
    coordinate_pivots = {
        (record["representative_occurrence_id"], record["coordinate"]) for record in direct
    }
    assert len(coordinate_pivots) == 214
    assert {record["coordinate"] for record in direct} == {"00", "11"}
    assert locus["coordinates_after_direct_constraints"] == 476 - 214 == 262
    assert locus["mixed_manifest_xy_coordinates"] == 262


def test_the_24_eliminated_timid_matrices_supply_48_derived_obligations() -> None:
    locus = _compiled()["mixed_ansatz_as_diagonal_restriction_locus"]
    records = locus["derived_obligation_records"]

    assert locus["derived_timid_matrices"] == len(records) == 24
    assert locus["derived_timid_diagonal_obligations"] == 48
    assert locus["derived_obligation_rank_claimed"] is False
    assert len({record["representative_occurrence_id"] for record in records}) == 24
    assert all(record["scalar_obligations"] == 2 for record in records)
    assert all(record["target_diagonal"][1] == "1" for record in records)


def test_degree_ceilings_recompute_from_the_raw_acyclic_recurrence() -> None:
    payload = _compiled()["substitution_degree_ceiling"]
    matrix_degree, state_degree = _independent_degree_propagation()
    slack = _slack()

    assert Counter(state_degree.values()) == {0: 1, 1: 2, 2: 3, 3: 11, 4: 2, 5: 3, 7: 2}
    timid = {record["timid_orbit_representative"] for record in slack["timid_slack_recurrences"]}
    assert Counter(matrix_degree[representative] for representative in timid) == {
        1: 1,
        2: 2,
        3: 3,
        4: 11,
        5: 2,
        6: 3,
        8: 2,
    }

    cpobc = _equation_degrees(slack["raw_source_system"]["CPOBC_equations"], matrix_degree)
    strong_gc = _equation_degrees(slack["raw_source_system"]["strong_GC_basis"], matrix_degree)
    assert Counter(cpobc) == {2: 559, 3: 140, 4: 59, 5: 25}
    assert Counter(strong_gc) == {2: 2, 3: 17, 4: 158, 5: 65, 6: 47, 7: 15, 8: 14, 11: 2}
    assert payload["maximum_state_vector_degree_ceiling"] == 7
    assert payload["maximum_timid_matrix_degree_ceiling"] == 8
    assert payload["global_maximum_degree_ceiling"] == 11


def test_coverage_certificate_does_not_promote_the_mixed_terminal_or_run_a_solver() -> None:
    payload = _compiled()
    gap = payload["certified_coverage_gap"]

    assert payload["scope"]["structural_coverage_gap_field"] == "characteristic-zero field"
    assert payload["scope"]["bound_mixed_terminal_predecessor_field"] == "QQ"
    assert gap["direct_independent_diagonal_normal_directions_omitted_by_mixed_ansatz"] == 214
    assert gap["additional_derived_timid_diagonal_obligations"] == 48
    assert gap["rank_of_additional_derived_obligations"] == "NOT_MEASURED"
    assert gap["mixed_terminal_cannot_be_promoted_by_density"] is True
    assert gap["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["mixed_ansatz_search_terminal"] is True
    assert payload["unrestricted_source_native_955_search_terminal"] is False
    assert payload["substitution_degree_ceiling"]["scalar_polynomial_expansion_performed"] is False
    assert payload["solver_status"] == {
        "scalar_polynomial_expansion_runs": 0,
        "Groebner_or_saturation_runs": 0,
        "finite_field_runs": 0,
        "numerical_runs": 0,
        "Sage_runs": 0,
        "solver_run": False,
    }
