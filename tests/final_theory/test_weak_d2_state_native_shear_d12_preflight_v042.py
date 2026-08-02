"""Exact checks for the SR2-V state-native shear D12 preflight."""

from __future__ import annotations

import hashlib
import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import weak_d2_state_native_shear_d12_preflight_v042 as gate

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "58b77ba00838a1051364c2c7feebbbe99bf3104b957c15d4e356fe2fdd8aa524"


def _load(relative: str) -> dict[str, Any]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return gate.build_payload(ROOT)


def test_frozen_preflight_rebuilds_exactly(rebuilt: dict[str, Any]) -> None:
    frozen = _load(gate.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["semantic_digest_sha256"] == gate.semantic_digest(frozen)
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert frozen["verdict"] == gate.VERDICT
    assert frozen["search_terminal"] == gate.SEARCH_TERMINAL
    assert frozen["passed"] is True
    assert all(frozen["gates"].values())


def test_raw_and_semantic_inputs_are_independently_bound(rebuilt: dict[str, Any]) -> None:
    bindings = rebuilt["input_bindings"]
    d12 = bindings["D12_manifest"]
    assert d12["raw_sha256"] == _sha256(gate.D12_MANIFEST_PATH)
    assert d12["raw_sha256"] == gate.PINNED_D12_RAW_SHA256
    assert d12["semantic_digest_sha256"] == gate.PINNED_D12_SEMANTIC_SHA256

    budget = bindings["campaign_budget"]
    assert budget["raw_sha256"] == _sha256(gate.BUDGET_PATH)
    assert budget["raw_sha256"] == gate.PINNED_BUDGET_RAW_SHA256
    assert budget["fallback_budget_used"] is False
    assert budget["solver_executed"] is False


def test_Q5_determinant_is_an_exact_nonzero_polynomial(rebuilt: dict[str, Any]) -> None:
    determinant = gate.reconstruct_q5_determinant()
    assert determinant == {
        ("Q5:00", "Q5:11"): Fraction(1),
        ("Q5:01", "Q5:10"): Fraction(-1),
    }
    certificate = rebuilt["Q5_nonsingularity_localization"]
    nonzero = certificate["nonzero_polynomial_certificate"]
    assert nonzero["term_count"] == 2
    assert nonzero["total_degree"] == 2
    assert nonzero["primitive_integer_content"] == 1
    assert nonzero["distinguished_nonzero_term"] == {
        "coefficient": "1",
        "monomial": ["Q5:00", "Q5:11"],
    }
    assert nonzero["exact_Q5_identity_evaluation"] == "1"
    assert certificate["determinant_content_digest_sha256"] == (
        gate.PINNED_Q5_DETERMINANT_SHA256
    )


def test_Q5_localization_is_exact_and_simultaneous_open_is_nonempty(
    rebuilt: dict[str, Any],
) -> None:
    determinant = gate.reconstruct_q5_determinant()
    localization = gate.q5_localization_polynomial(determinant)
    assignment = {
        "Q5:00": Fraction(1),
        "Q5:01": Fraction(0),
        "Q5:10": Fraction(0),
        "Q5:11": Fraction(1),
        "sigma:detQ5": Fraction(1),
    }
    assert gate._evaluate(determinant, assignment) == 1
    assert gate._evaluate(localization, assignment) == 0
    assert localization == {
        (): Fraction(-1),
        ("Q5:00", "Q5:11", "sigma:detQ5"): Fraction(1),
        ("Q5:01", "Q5:10", "sigma:detQ5"): Fraction(-1),
    }

    combined = rebuilt["combined_principal_open"]
    assert combined["coordinates_before_Q5_localization"] == 136
    assert combined["coordinates_after_Q5_localization"] == 137
    assert combined["exact_ambient_nonempty_point"]["D12_value"] == (
        "155389/220996566"
    )
    assert combined["exact_ambient_nonempty_point"]["detQ5_value"] == "1"
    assert combined["exact_ambient_nonempty_point"]["is_required_relation_solution"] is False
    assert combined["historical_preflight_status"] == "UNRESOLVED_AT_PREFLIGHT_TIME"
    assert combined["meets_relation_variety"] == (
        "EMPTY_ON_FIXED_HARMONIC_SLICE_CERTIFIED"
    )


def test_campaign_budget_is_exactly_owner_approved_and_version_bound(
    rebuilt: dict[str, Any],
) -> None:
    budget = rebuilt["input_bindings"]["campaign_budget"]
    assert budget["path"] == gate.BUDGET_PATH
    assert budget["authorised_limits"] == {
        "timeout_seconds_per_chart": 3600,
        "total_wall_time_seconds": 43200,
        "memory_limit_gib": 8,
        "memory_limit_bytes": 8 * 1024**3,
    }
    assert budget["authorised_limits"]["timeout_seconds_per_chart"] <= budget[
        "authorised_limits"
    ]["total_wall_time_seconds"]
    assert budget["provenance"].endswith("NO_RUNTIME_DEFAULT_OR_FALLBACK")


def test_budget_gate_fails_closed_without_or_beyond_approved_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="campaign-specific budget required"):
        gate._load_budget(tmp_path)

    budget_path = tmp_path / gate.BUDGET_PATH
    budget_path.parent.mkdir(parents=True)
    budget_path.write_text(
        json.dumps(
            {
                "timeout_seconds_per_chart": 3601,
                "total_wall_time_seconds": 43200,
                "memory_limit_gib": 8,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="differs from owner-approved"):
        gate._load_budget(tmp_path)

    shutil.copy2(ROOT / gate.BUDGET_PATH, budget_path)
    assert gate._load_budget(tmp_path)["raw_sha256"] == gate.PINNED_BUDGET_RAW_SHA256


def test_manifest_binding_fails_closed_on_raw_drift(tmp_path: Path) -> None:
    manifest_path = tmp_path / gate.D12_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes((ROOT / gate.D12_MANIFEST_PATH).read_bytes() + b" ")
    with pytest.raises(AssertionError, match="raw SHA-256 changed"):
        gate._load_d12_manifest(tmp_path)


def test_preflight_is_fail_closed_cancelled_by_later_unit_ideal(
    rebuilt: dict[str, Any],
) -> None:
    boundary = rebuilt["execution_and_claim_boundary"]
    assert boundary == {
        "preflight_status": "HISTORICAL_PROVENANCE_CERTIFIED_SUPERSEDED",
        "solver_status": "NOT_RUN",
        "groebner_status": "NOT_RUN",
        "sage_status": "NOT_INVOKED",
        "finite_field_status": "NOT_RUN",
        "relation_variety_intersection": (
            "EMPTY_ON_FIXED_HARMONIC_SLICE_BY_RAW_CPOBC_UNIT_IDEAL"
        ),
        "witness": None,
        "execution_triggered_by_this_artifact": False,
        "execution_authorised": False,
        "execution_cancellation": "EXECUTION_CANCELLED_BY_LATER_UNIT_IDEAL",
        "future_resource_limit_rule": "NOT_APPLICABLE_CAMPAIGN_CANCELLED",
        "future_numerical_or_finite_field_output_role": (
            "NOT_APPLICABLE_CAMPAIGN_CANCELLED"
        ),
    }
    assert "No solver was run" in rebuilt["claim_boundary"]
    assert "permanently cancelled" in rebuilt["claim_boundary"]
    assert rebuilt["search_terminal"] == "EXECUTION_CANCELLED_BY_LATER_UNIT_IDEAL"


def test_superseding_obstruction_is_raw_and_semantically_bound(
    rebuilt: dict[str, Any],
) -> None:
    binding = rebuilt["input_bindings"][
        "superseding_fixed_state_unit_ideal_obstruction"
    ]
    assert binding["path"] == gate.SUPERSEDING_OBSTRUCTION_PATH
    assert binding["raw_sha256"] == _sha256(gate.SUPERSEDING_OBSTRUCTION_PATH)
    assert binding["raw_sha256"] == gate.PINNED_SUPERSEDING_OBSTRUCTION_RAW_SHA256
    assert binding["semantic_digest_sha256"] == (
        gate.PINNED_SUPERSEDING_OBSTRUCTION_SEMANTIC_SHA256
    )
    assert binding["verdict"].endswith("OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN")
