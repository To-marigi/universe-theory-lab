"""Regression checks for the nonzero-fibre Lambda audit."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / gate.RESULT_PATH


@cache
def _compiled() -> dict[str, Any]:
    return gate.compile_lambda_fibre_audit_v042(ROOT)


def test_frozen_result_regenerates_exactly() -> None:
    assert json.loads(RESULT.read_text(encoding="utf-8")) == _compiled()


def test_numeric_audit_is_not_the_zero_section() -> None:
    points = _compiled()["numeric_nonzero_fibre_audit"]["points"]

    assert len(points) == 4
    assert all(point["D"] != "0" for point in points)
    assert all(point["core_failures"] == 0 for point in points)
    assert all(point["non_q_rank"] == 111 for point in points)
    assert all(point["pure_rows"] == 706 for point in points)
    assert all(point["pure_q_rank"] == 3 for point in points)
    assert all(point["lambda_row_remainder_terms"] == 0 for point in points)
    assert all(point["kernel_q_is_nonzero"] for point in points)
    assert all(point["lambda_on_kernel"] == "0" for point in points)


def test_symbolic_subfamily_has_zero_lambda_remainder() -> None:
    symbolic = _compiled()["symbolic_subfamily_audit"]

    assert symbolic["field"] == "QQ(t,s)"
    assert symbolic["core_failures"] == 0
    assert symbolic["rows"] == 1038
    assert symbolic["non_q_rank"] == 111
    assert symbolic["pure_rows"] == 706
    assert symbolic["pure_q_rank"] == 3
    assert symbolic["D_nonzero_as_rational_function"] is True
    assert symbolic["D"] == "s*(t + 13)/(2*(t + 15))"
    assert symbolic["lambda_row_remainder_zero"] is True
    assert symbolic["lambda_row_remainder_terms"] == 0


def test_d_zero_branch_has_one_explicit_nonsingular_anchor() -> None:
    branch = _compiled()["D_zero_branch_audit"]

    assert branch["D"] == "0"
    assert branch["core_failures"] == 0
    assert branch["non_q_rank"] == 111
    assert branch["pure_q_rank"] == 3
    assert branch["lambda_row_remainder_terms"] == 0
    assert branch["kernel_q_is_nonzero"] is True
    assert branch["lambda_on_kernel"] == "0"
    assert branch["source_determinants_checked"] == 131
    assert branch["source_determinant_failures"] == 0
    assert branch["nonsingular_source_fibre"] is True
    assert branch["D_zero_branch_sample_only"] is True


def test_q_mapping_and_claim_boundary_are_explicit() -> None:
    payload = _compiled()

    assert payload["q_stage_mapping"] == {
        "1": "cpobc-transition-7137acaa934673cc789d",
        "2": "cpobc-transition-3b93b9f523031a23c77f",
        "3": "cpobc-transition-779d09aa463a38abdba6",
        "4": "cpobc-transition-9fabc20614d5b2aa595d",
    }
    assert payload["scope"]["full_S_claim"] is False
    assert payload["unrestricted_source_native_955_status"] == "OPEN"
    assert payload["commutativity_proved_for_full_profile"] is False
    assert payload["witness_certified"] is False
    assert payload["search_terminal"] is False
    assert payload["passed"] is True
