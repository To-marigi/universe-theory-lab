"""Regression checks for the exact v0.4.2 955 growth-family core identity."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_growth_family_identity_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_growth_family_identity_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_core_vanishes_identically_in_the_couplings() -> None:
    identity = _compiled()["core_identity"]

    assert identity["field"] == "QQ(t_0,...,t_4)"
    assert identity["streamed_nonzero_entries"] == 4152
    assert identity["per_block"] == {"CPOBC": 3132, "strong_GC": 1020}
    assert identity["entries_not_vanishing_identically"] == 0


def test_timid_first_column_identity_holds_symbolically_at_every_source() -> None:
    identity = _compiled()["timid_first_column_identity"]

    assert identity["sources_checked"] == 24
    assert identity["symbolic_failures"] == 0


def test_symbolic_characters_specialise_to_the_frozen_values() -> None:
    characters = _compiled()["symbolic_characters"]

    assert characters["orbits"] == 131
    assert characters["distinct_values"] == 24
    assert characters["specialisation_at_all_ones_reproduces_frozen_values"] is True


def test_lambda_matches_the_reference_growth_formula() -> None:
    couplings = gate._couplings()

    assert gate._lambda(1, 0, couplings) == couplings[0] + couplings[1]
    assert gate._lambda(2, 0, couplings) == couplings[0] + 2 * couplings[1] + couplings[2]
    assert (
        sympy.expand(
            gate._lambda(4, 0, couplings)
            - (couplings[0] + 4 * couplings[1] + 6 * couplings[2] + 4 * couplings[3] + couplings[4])
        )
        == 0
    )
    assert gate._lambda(2, 2, couplings) == couplings[2]


def test_excluded_locus_names_the_four_coupling_denominators() -> None:
    excluded = _compiled()["excluded_locus"]

    assert excluded["coupling_denominators_required_nonzero"] == [
        "t0 + 2*t1 + t2",
        "t0 + 3*t1 + 3*t2 + t3",
        "t0 + 4*t1 + 6*t2 + 4*t3 + t4",
        "t0 + t1",
    ]
    assert excluded["reachable_product_numerators_required_nonzero"]
    assert excluded["count"] == len(excluded["coupling_denominators_required_nonzero"]) + len(
        excluded["reachable_product_numerators_required_nonzero"]
    )


def test_the_second_diagonal_limitation_is_stated_not_hidden() -> None:
    payload = _compiled()

    assert payload["core_identity"]["second_diagonal_value"] == (
        "every A:*:11 is fixed to 1 by the growth assignment"
    )
    assert any(
        "second diagonal is still never varied" in claim for claim in payload["claim_boundary"]
    )
    assert any(
        "witness outcome off the growth family" in claim for claim in payload["claim_boundary"]
    )


def test_gate_stays_open_and_runs_no_solver() -> None:
    payload = _compiled()

    assert payload["verdict"] == gate.VERDICT
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["witness_certified"] is False
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
    assert payload["solver_status"]["Groebner_or_saturation_runs"] == 0
    assert payload["solver_status"]["solver_run"] is False
