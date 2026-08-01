"""Exact rebuild guards for the isolated SR2-V scalar-lattice artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_DIGEST = "155ddfd5ec1b90765acbb0eccfaa66991fc2d98a44432055b5481b09a0de5eb9"


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return lattice.build_payload(ROOT)


def test_scalar_lattice_artifact_rebuilds_with_fixed_digest(rebuilt: dict[str, Any]) -> None:
    frozen = _load(lattice.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == lattice.SCHEMA
    assert frozen["verdict"] == lattice.VERDICT
    assert frozen["search_terminal"] == lattice.SEARCH_TERMINAL
    assert frozen["semantic_digest_sha256"] == EXPECTED_DIGEST
    assert lattice.semantic_digest(frozen) == EXPECTED_DIGEST
    assert frozen["passed"] is True
    for relative, digest in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_operator_scalar_lattice_has_exact_saturated_snf(rebuilt: dict[str, Any]) -> None:
    block = rebuilt["operator_scalar_block"]
    assert block["matrix_shape"] == [843, 132]
    assert block["QQ_rank"] == 83
    assert block["QQ_nullity"] == 49
    assert block["split_torus_dimension_before_nonmonomial_equations"] == 49

    smith = block["relation_lattice_smith"]
    assert smith["arithmetic"] == "ZZ"
    assert smith["nonzero_invariants"] == [1] * 83
    assert smith["all_nonzero_invariants_are_one"] is True
    assert smith["saturated_row_lattice"] is True

    kernel = block["integer_kernel"]
    assert kernel["rank"] == 49
    assert len(kernel["basis_columns"]) == 49
    assert all(len(column) == 132 for column in kernel["basis_columns"])
    assert kernel["relation_matrix_times_basis_is_zero"] is True
    assert kernel["basis_smith_nonzero_invariants"] == [1] * 49
    assert kernel["primitive_full_kernel"] is True


def test_bottom_gc_lattice_has_exact_saturated_snf(rebuilt: dict[str, Any]) -> None:
    block = rebuilt["observed_bottom_plus_fixed_GC_block"]
    assert block["matrix_shape"] == [1163, 132]
    assert block["QQ_rank"] == 103
    assert block["QQ_nullity"] == 29
    assert block["split_torus_dimension_before_nonmonomial_equations"] == 29

    smith = block["relation_lattice_smith"]
    assert smith["nonzero_invariants"] == [1] * 103
    assert smith["all_nonzero_invariants_are_one"] is True
    assert smith["saturated_row_lattice"] is True

    kernel = block["integer_kernel"]
    assert kernel["rank"] == 29
    assert len(kernel["basis_columns"]) == 29
    assert all(len(column) == 132 for column in kernel["basis_columns"])
    assert kernel["relation_matrix_times_basis_is_zero"] is True
    assert kernel["basis_smith_nonzero_invariants"] == [1] * 29
    assert kernel["primitive_full_kernel"] is True


def test_eq113_branches_and_eq139_domains_are_not_merged(rebuilt: dict[str, Any]) -> None:
    scope = rebuilt["relation_scope"]
    assert scope["CPOBC"] == 783
    assert scope["Eq113"] == {
        "branches_kept_separate": True,
        "branch_counts": {
            lattice.EQ113_DERIVED: 25,
            lattice.EQ113_LITERAL: 25,
        },
        "total": 50,
    }

    eq139 = scope["Eq139"]
    assert eq139["domains_kept_separate"] is True
    assert eq139["printed_strict"]["domain"] == lattice.EQ139_STRICT
    assert eq139["printed_strict"]["count"] == 4
    assert eq139["printed_strict"]["included_as_additional_rows"] is False
    assert eq139["eq145_completed"]["domain"] == lattice.EQ139_COMPLETED
    assert eq139["eq145_completed"]["count"] == 10
    assert eq139["eq145_completed"]["included_as_scalar_zero_rows"] is True
    assert eq139["strict_is_subset_of_completed"] is True
    assert scope["total"] == 843
    assert scope["fixed_vector_GC_basis"] == {
        "count": 320,
        "applied_only_to_observed_bottom_character": True,
    }


def test_claim_boundary_is_explicitly_nonterminal(rebuilt: dict[str, Any]) -> None:
    assert all(rebuilt["gates"].values())
    assert rebuilt["field"] == {
        "relation_lattice": "ZZ",
        "rank_and_kernel_span": "QQ",
        "floating_point_used": False,
        "finite_field_used": False,
    }
    assert rebuilt["torus_interpretation"]["operator_scalar_laurent_locus"] == "split G_m^49"
    assert (
        rebuilt["torus_interpretation"]["observed_bottom_GC_laurent_locus"]
        == "split G_m^29"
    )
    boundary = rebuilt["claim_boundary"]
    assert "No additive MSR locus" in boundary
    assert "commutativity theorem" in boundary
    assert "SR2-V terminal" in boundary


def test_semantic_digest_rejects_a_mutated_headline(rebuilt: dict[str, Any]) -> None:
    mutated = json.loads(json.dumps(rebuilt))
    mutated["operator_scalar_block"]["QQ_rank"] = 82
    assert lattice.semantic_digest(mutated) != EXPECTED_DIGEST
