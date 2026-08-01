"""Exact checks for the nonlinear aligned SR2-V principal open."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_aligned_principal_open_v042 as aligned
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return aligned.build_payload(ROOT)


def test_frozen_aligned_principal_open_rebuilds_exactly(
    rebuilt: dict[str, Any],
) -> None:
    frozen = _load(aligned.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == aligned.semantic_digest(frozen)
    assert frozen["verdict"] == aligned.VERDICT
    assert frozen["search_terminal"] == aligned.SEARCH_TERMINAL
    assert frozen["passed"] is True


def test_explicit_131_square_jacobian_is_nonsingular(
    rebuilt: dict[str, Any],
) -> None:
    subsystem = rebuilt["lower_relation_subsystem"]
    assert subsystem["row_count"] == 1187
    assert subsystem["selected_row_count"] == 131
    assert len(subsystem["selected_row_indices_zero_based"]) == 131
    assert len(subsystem["selected_row_labels"]) == 131
    assert len(subsystem["selected_column_labels"]) == 131
    assert torus.Q5 not in subsystem["selected_column_labels"]
    assert subsystem["jacobian_determinant_at_base"] != "0"
    assert subsystem["relation_domain_inventory"]["Eq113"] == {
        torus.EQ113_DERIVED: {
            "relation_count": 25,
            "operator_component_count": 100,
        },
        torus.EQ113_LITERAL: {
            "relation_count": 25,
            "operator_component_count": 100,
        },
    }
    assert subsystem["relation_domain_inventory"]["Eq139"] == {
        torus.EQ139_STRICT: {
            "relation_count": 4,
            "operator_component_count": 16,
            "scope_note": "audited subset of completed; not duplicated in the row system",
        },
        torus.EQ139_COMPLETED: {
            "relation_count": 10,
            "operator_component_count": 40,
            "row_system_scope": True,
        },
    }
    eq139_labels = [
        label for label in subsystem["selected_row_labels"] if label.startswith("Eq139:")
    ]
    assert len(eq139_labels) == 2
    assert all(
        label.startswith(f"Eq139:{torus.EQ139_COMPLETED}:") for label in eq139_labels
    )


def test_principal_open_upgrades_the_tangent_result_to_nonlinear_obstruction(
    rebuilt: dict[str, Any],
) -> None:
    theorem = rebuilt["principal_open_theorem"]
    assert theorem["factorisation"] == "F(y,z)=H(y,z)*y in the determinant-localised ring"
    assert theorem["principal_open"] == "Delta_align!=0"
    assert theorem["conclusion"] == "every solution in the principal open has y=0"
    assert "not merely first-order" in theorem["proof"][-1]
    assert "degeneracy hypersurface" in rebuilt["claim_boundary"]


def test_all_scope_and_digest_gates_hold(rebuilt: dict[str, Any]) -> None:
    assert all(rebuilt["gates"].values())
    assert (
        rebuilt["lower_relation_subsystem"]["source_tangent_normalised_rows_sha256"]
        == "dc8f354ac3726532365d48144024fcc1ca53d84957c777f190350d4f45a4ea9c"
    )
    assert len(
        rebuilt["lower_relation_subsystem"]["scoped_normalised_rows_sha256"]
    ) == 64
