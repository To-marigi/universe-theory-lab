"""Exact checks for the transverse transitive-extension principal open."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_transitive_extension_v042 as extension
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return extension.build_payload(ROOT)


def test_frozen_principal_open_certificate_rebuilds_exactly(
    rebuilt: dict[str, Any],
) -> None:
    frozen = _load(extension.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == extension.semantic_digest(frozen)
    assert frozen["verdict"] == extension.VERDICT
    assert frozen["search_terminal"] == extension.SEARCH_TERMINAL
    assert frozen["passed"] is True


def test_scalar_family_identity_audit_keeps_all_relation_groups(
    rebuilt: dict[str, Any],
) -> None:
    audit = rebuilt["symbolic_scalar_identity_audit"]
    assert audit["all_passed"] is True
    assert audit["CPOBC"] == {"checked": 783, "failures": []}
    assert audit["Eq113_separate_branches"] == {
        torus.EQ113_DERIVED: {"checked": 25, "failures": []},
        torus.EQ113_LITERAL: {"checked": 25, "failures": []},
    }
    assert audit["Eq139_printed_strict"] == {"checked": 4, "failures": []}
    assert audit["Eq139_completed"] == {"checked": 10, "failures": []}
    assert audit["strong_GC_all_path_pairs"] == {
        "checked": 1529,
        "failures": [],
    }
    assert audit["strong_MSR_polynomial_identities"] == {
        "checked": 24,
        "failures": [],
    }
    assert rebuilt["linear_problem"]["relation_domain_inventory"]["Eq113"] == {
        torus.EQ113_DERIVED: {"relation_count": 25, "solver_row_count": 25},
        torus.EQ113_LITERAL: {"relation_count": 25, "solver_row_count": 25},
    }
    assert rebuilt["linear_problem"]["relation_domain_inventory"]["Eq139"] == {
        torus.EQ139_STRICT: {
            "relation_count": 4,
            "solver_row_count": 0,
            "scope_note": "audited separately; contained in completed and not duplicated",
        },
        torus.EQ139_COMPLETED: {"relation_count": 10, "solver_row_count": 10},
    }


def test_explicit_minor_certifies_a_nonempty_generic_splitting_open(
    rebuilt: dict[str, Any],
) -> None:
    certificate = rebuilt["principal_open_certificate"]
    assert certificate["minor_size"] == 130
    assert len(certificate["selected_row_indices_zero_based"]) == 130
    assert len(certificate["selected_row_labels"]) == 130
    assert len(certificate["selected_column_labels"]) == 130
    assert certificate["sample_actual_rank"] == 130
    assert certificate["sample_actual_nullity"] == 1
    assert certificate["sample_nullspace_to_coboundary_scale"] == "36"
    assert certificate["determinant_at_sample"] != "0"
    assert all(rebuilt["gates"].values())


def test_exact_grid_separates_same_and_distinct_character_ranks(
    rebuilt: dict[str, Any],
) -> None:
    scout = rebuilt["exact_grid_scout"]
    assert scout["pair_count"] == 25
    assert scout["rank_census"] == {"127": 5, "130": 20}
    assert all(not record["free_Q_commutators"] for record in scout["records"])
    assert all(
        record["actual_rank"] == (127 if record["diagonal_character_pair"] else 130)
        for record in scout["records"]
    )


def test_general_lower_character_is_used_by_q_tokens_and_commutators() -> None:
    context = torus._build_context(ROOT)
    ratio = extension.GRID_RATIOS[-1]
    assignment = extension._top_assignment(context, ratio)
    rows, _, commutators, _ = torus._linear_system(
        context,
        assignment,
        lower_character=extension._character(ratio),
    )
    assert len(rows) == 1187
    assert all(not row for row in commutators.values())
