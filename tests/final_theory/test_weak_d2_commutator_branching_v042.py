"""Exact checks for the SR2-V commutator-pivot branch cover."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_commutator_branching_v042 as branching

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return branching.build_payload(ROOT)


def test_frozen_branch_cover_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(branching.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == branching.semantic_digest(frozen)
    assert frozen["verdict"] == branching.VERDICT
    assert frozen["search_terminal"] == branching.SEARCH_TERMINAL
    assert frozen["passed"] is True


def test_six_nonzero_Q_commutator_pivots_have_complete_four_way_split(
    rebuilt: dict[str, Any],
) -> None:
    cover = rebuilt["pivot_cover"]
    assert cover["Q_pairs"] == [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]
    assert [record["branch"] for record in cover["complete_branches_on_each_pivot"]] == [
        "PAIR_IRREDUCIBLE",
        "TRIPLE_IRREDUCIBLE",
        "TRANSVERSE_GLOBALLY_REDUCIBLE",
        "ALIGNED_GLOBALLY_REDUCIBLE",
    ]


def test_symbolic_canonicalisation_and_tau_identities_are_exact(
    rebuilt: dict[str, Any],
) -> None:
    symbolic = rebuilt["symbolic_certificate"]
    assert symbolic["generic_commutator_trace"] == "0"
    assert symbolic["cayley_hamilton_residual"] == [["0", "0"], ["0", "0"]]
    assert symbolic["ideal_membership_identities"]["force_A21"] == "0"
    assert symbolic["ideal_membership_identities"]["force_B21"] == "0"
    assert symbolic["tau_in_canonical_basis"] == "x21"
    assert symbolic["all_zero_identity_checks"] is True


def test_transverse_chart_uses_upper_commutator_not_determinant_saturation(
    rebuilt: dict[str, Any],
) -> None:
    chart = rebuilt["canonical_transverse_chart"]
    assert chart["normalisation"] == [
        "S_ij^-1*Omega=e_2",
        "S_ij^-1*C_ij*S_ij=E_12",
    ]
    assert chart["residual_conjugation_after_normalisation"] == "identity only"
    assert chart["pivot_equation"].endswith("=1")
    assert "identically zero" in chart["warning"]


def test_scope_keeps_rank_and_external_Q5_separate(rebuilt: dict[str, Any]) -> None:
    inventory = rebuilt["generator_inventory"]
    assert inventory["actual_ON_transition_generators"] == 131
    assert inventory["compiled_operator_family_size"] == 132
    assert "must still be imposed" in rebuilt["reachable_rank_boundary"]
    assert "Supplemental Q5" in rebuilt["claim_boundary"]
    assert all(rebuilt["gates"].values())
