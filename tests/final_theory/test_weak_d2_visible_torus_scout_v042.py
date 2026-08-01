"""Exact checks for the bounded SR2-V rational-torus scout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as scout

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return scout.build_payload(ROOT)


def test_frozen_torus_scout_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(scout.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == scout.semantic_digest(frozen)
    assert frozen["verdict"] == scout.NO_WITNESS_VERDICT
    assert frozen["search_terminal"] == scout.NO_WITNESS_TERMINAL
    assert frozen["passed"] is True


def test_scalar_torus_and_candidate_campaign_are_exact(rebuilt: dict[str, Any]) -> None:
    torus = rebuilt["scalar_torus"]
    assert torus["variable_count"] == 132
    assert torus["raw_relation_counts"] == {
        "CPOBC": 783,
        "Eq113_both_branches": 50,
        "Eq139_completed": 10,
    }
    assert torus["exact_QQ_rank"] == 83
    assert torus["exact_QQ_dimension"] == 49
    assert torus["integer_nullspace_basis"] is True

    campaign = rebuilt["candidate_campaign"]
    assert campaign["planned_candidate_count"] == 180
    assert campaign["evaluated_candidate_count"] == 180
    assert campaign["stopped_on_first_certified_witness"] is False
    assert campaign["rank_census"] == {
        "127": 17,
        "129": 2,
        "130": 27,
        "131": 100,
        "132": 34,
    }
    assert campaign["maximum_linear_nullity"] == 5
    assert all(not record["free_Q_commutators"] for record in campaign["candidate_records"])


def test_declared_linear_relation_inventory_is_not_silently_reduced(
    rebuilt: dict[str, Any],
) -> None:
    assert rebuilt["linear_problem"]["relation_counts"] == {
        "CPOBC": 783,
        "Eq113_both_branches": 50,
        "Eq139_completed": 10,
        "fixed_vector_GC_basis": 320,
        "reachable_state_MSR": 24,
    }
    assert rebuilt["linear_problem"]["arithmetic"].startswith("fractions.Fraction")
    assert rebuilt["witness"] is None
    assert "not an obstruction" in rebuilt["claim_boundary"]


def test_constant_torus_point_has_no_commutator_escape_after_fixed_gc() -> None:
    context = scout._build_context(ROOT)
    scalar_rows, _ = scout._scalar_torus_rows(context)
    exponent_basis = scout._nullspace_basis_from_echelon(
        scout._row_echelon(scalar_rows, context.variables),
        context.variables,
    )
    candidates = scout._candidate_points(
        exponent_basis,
        scout._bottom_exponent_point(context),
        context.variables,
    )
    candidate = next(item for item in candidates if item["candidate_id"] == "constant-character")
    rows, counts, commutators, _ = scout._linear_system(
        context,
        scout._top_assignment(candidate, context.variables),
    )
    through_gc = sum(
        counts[name]
        for name in (
            "CPOBC",
            "Eq113_both_branches",
            "Eq139_completed",
            "fixed_vector_GC_basis",
        )
    )
    echelon = scout._row_echelon(rows[:through_gc], context.variables)
    assert len(echelon) == 115
    assert all(
        not scout._row_remainder(row, echelon, context.variables)
        for row in commutators.values()
    )
