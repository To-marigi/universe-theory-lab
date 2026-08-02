"""Superseded, fail-closed Q5/budget preflight for the SR2-V shear D12 manifest.

This module performs no elimination and imports no solver.  It independently
reconstructs ``det(Q5)`` over ``QQ``, adds the localization

``sigma:detQ5 * det(Q5) - 1 = 0``,

and records the frozen D12 manifest's campaign-specific, owner-approved
resource budget.  A later exact unit-ideal certificate proved the fixed-state
relation slice empty.  A successful rebuild therefore certifies that execution
is cancelled; it must never re-authorise the historical solver campaign.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from math import isfinite
from pathlib import Path
from typing import Any

RESULT_PATH = "results/v0.4.2_sr2v_state_native_shear_D12_preflight.json"
D12_MANIFEST_PATH = "results/v0.4.2_sr2v_state_native_shear_D12_manifest.json"
BUDGET_PATH = "config/v0.4.2_sr2v_state_native_shear_D12_budget.json"
SUPERSEDING_OBSTRUCTION_PATH = (
    "results/v0.4.2_sr2v_fixed_harmonic_cpobc_obstruction.json"
)

SCHEMA = "final-theory-v042-sr2v-state-native-shear-D12-Q5-budget-preflight-v1"
VERDICT = "SR2V_STATE_NATIVE_SHEAR_D12_PREFLIGHT_SUPERSEDED_EXECUTION_CANCELLED"
SEARCH_TERMINAL = "EXECUTION_CANCELLED_BY_LATER_UNIT_IDEAL"

PINNED_D12_RAW_SHA256 = "125d21520df39578e102300c5e0d15509631e1c579506c361fdd58f216312d82"
PINNED_D12_SEMANTIC_SHA256 = (
    "82cd51ddd29e5923b003c8cf8f75a5a26cf5a36edf68728ad58d298d3f573090"
)
PINNED_BUDGET_RAW_SHA256 = "f192a37b97e70c84aeae594db75832bdcf632bf00a78009ff45f09b1bcca2e50"
PINNED_Q5_DETERMINANT_SHA256 = (
    "81da7f043537e1b7a7943135e03e9e7be3edfb3119ba064243df4e6304256124"
)
PINNED_SUPERSEDING_OBSTRUCTION_RAW_SHA256 = (
    "25abf593a2f8cae1ca75d5d164bc60b1c79327111544c04278621e6b0ed37183"
)
PINNED_SUPERSEDING_OBSTRUCTION_SEMANTIC_SHA256 = (
    "d5514f31bf6caef5ca102ef8ce78f0bcf137e72922c0f230c716386f22cffc7d"
)

APPROVED_LIMITS = {
    "timeout_seconds_per_chart": 3600,
    "total_wall_time_seconds": 43200,
    "memory_limit_gib": 8,
}

Monomial = tuple[str, ...]
Polynomial = dict[Monomial, Fraction]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON object required: {path}")
    return payload


def _add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        updated = result.get(monomial, Fraction(0)) + coefficient
        if updated:
            result[monomial] = updated
        else:
            result.pop(monomial, None)
    return result


def _multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(sorted(left_monomial + right_monomial))
            updated = result.get(monomial, Fraction(0)) + left_coefficient * right_coefficient
            if updated:
                result[monomial] = updated
            else:
                result.pop(monomial, None)
    return result


def _scale(coefficient: Fraction | int, polynomial: Polynomial) -> Polynomial:
    scalar = Fraction(coefficient)
    return {
        monomial: scalar * value
        for monomial, value in polynomial.items()
        if scalar * value
    }


def _variable(name: str) -> Polynomial:
    return {(name,): Fraction(1)}


def _constant(value: Fraction | int) -> Polynomial:
    scalar = Fraction(value)
    return {(): scalar} if scalar else {}


def reconstruct_q5_determinant() -> Polynomial:
    """Return the exact generic 2x2 determinant, independent of the D12 compiler."""

    q00 = _variable("Q5:00")
    q01 = _variable("Q5:01")
    q10 = _variable("Q5:10")
    q11 = _variable("Q5:11")
    return _add(_multiply(q00, q11), _scale(-1, _multiply(q01, q10)))


def q5_localization_polynomial(determinant: Polynomial) -> Polynomial:
    return _add(
        _multiply(_variable("sigma:detQ5"), determinant),
        _constant(-1),
    )


def _serialize_polynomial(polynomial: Polynomial) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": str(coefficient),
            "monomial": [
                {"variable": variable, "exponent": monomial.count(variable)}
                for variable in sorted(set(monomial))
            ],
        }
        for monomial, coefficient in sorted(polynomial.items())
    ]


def _deserialize_polynomial(records: Any) -> Polynomial:
    if not isinstance(records, list):
        raise TypeError("serialized polynomial must be a list")
    result: Polynomial = {}
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("serialized polynomial record must be an object")
        coefficient = Fraction(str(record["coefficient"]))
        factors: list[str] = []
        for factor in record["monomial"]:
            variable = str(factor["variable"])
            exponent = factor["exponent"]
            if isinstance(exponent, bool) or not isinstance(exponent, int) or exponent < 1:
                raise ValueError("monomial exponents must be positive integers")
            factors.extend([variable] * exponent)
        monomial = tuple(sorted(factors))
        result = _add(result, {monomial: coefficient})
    return result


def _polynomial_digest(polynomial: Polynomial) -> str:
    return hashlib.sha256(
        _canonical_json(_serialize_polynomial(polynomial)).encode("utf-8")
    ).hexdigest()


def _evaluate(polynomial: Polynomial, assignment: dict[str, Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in polynomial.items():
        value = coefficient
        for variable in monomial:
            value *= assignment.get(variable, Fraction(0))
        total += value
    return total


def _load_budget(root: Path) -> dict[str, Any]:
    path = root / BUDGET_PATH
    if not path.is_file():
        raise FileNotFoundError(f"campaign-specific budget required: {BUDGET_PATH}")
    supplied = _load_object(path)
    required = set(APPROVED_LIMITS)
    missing = sorted(required - supplied.keys())
    unsupported = sorted(supplied.keys() - required)
    if missing:
        raise ValueError(f"campaign budget is missing required keys: {missing}")
    if unsupported:
        raise ValueError(f"campaign budget has unsupported keys: {unsupported}")
    for name, approved in APPROVED_LIMITS.items():
        value = supplied[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"campaign budget {name} must be numeric")
        if not isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"campaign budget {name} must be positive and finite")
        if value != approved:
            raise ValueError(
                f"campaign budget {name}={value!r} differs from owner-approved {approved!r}"
            )
    if supplied["timeout_seconds_per_chart"] > supplied["total_wall_time_seconds"]:
        raise ValueError("per-chart timeout cannot exceed total wall time")
    raw_sha256 = _sha256(path)
    if raw_sha256 != PINNED_BUDGET_RAW_SHA256:
        raise AssertionError("campaign budget raw SHA-256 changed")
    return {
        "path": BUDGET_PATH,
        "raw_sha256": raw_sha256,
        "provenance": (
            "CAMPAIGN_SPECIFIC_VERSIONED_OWNER_APPROVED_FILE; "
            "NO_RUNTIME_DEFAULT_OR_FALLBACK"
        ),
        "authorised_limits": {
            **APPROVED_LIMITS,
            "memory_limit_bytes": APPROVED_LIMITS["memory_limit_gib"] * 1024**3,
        },
        "fallback_budget_used": False,
        "solver_executed": False,
    }


def _load_d12_manifest(root: Path) -> tuple[dict[str, Any], str]:
    path = root / D12_MANIFEST_PATH
    if not path.is_file():
        raise FileNotFoundError(f"frozen D12 manifest required: {D12_MANIFEST_PATH}")
    raw_sha256 = _sha256(path)
    if raw_sha256 != PINNED_D12_RAW_SHA256:
        raise AssertionError("frozen D12 manifest raw SHA-256 changed")
    manifest = _load_object(path)
    if manifest.get("semantic_digest_sha256") != semantic_digest(manifest):
        raise AssertionError("frozen D12 manifest semantic digest does not recompute")
    if manifest.get("semantic_digest_sha256") != PINNED_D12_SEMANTIC_SHA256:
        raise AssertionError("unexpected frozen D12 manifest semantic digest")
    if manifest.get("verdict") != "SR2V_STATE_NATIVE_SHEAR_D12_MANIFEST_CERTIFIED_NO_SOLVER_RUN":
        raise AssertionError("unexpected frozen D12 manifest verdict")
    if manifest.get("passed") is not True:
        raise AssertionError("frozen D12 manifest did not pass")
    boundary = manifest.get("resource_and_claim_boundaries", {})
    expected_statuses = {
        "solver_status": "NOT_RUN",
        "groebner_status": "NOT_RUN",
        "sage_status": "NOT_INVOKED",
        "finite_field_status": "NOT_RUN",
        "D12_open_meets_relation_variety": "UNRESOLVED",
    }
    if any(boundary.get(key) != value for key, value in expected_statuses.items()):
        raise AssertionError("frozen D12 manifest crossed its non-solver claim boundary")
    if manifest.get("witness") is not None:
        raise AssertionError("preflight cannot bind a manifest that claims a witness")
    return manifest, raw_sha256


def _load_superseding_obstruction(root: Path) -> tuple[dict[str, Any], str]:
    path = root / SUPERSEDING_OBSTRUCTION_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"superseding unit-ideal certificate required: {SUPERSEDING_OBSTRUCTION_PATH}"
        )
    raw_sha256 = _sha256(path)
    if raw_sha256 != PINNED_SUPERSEDING_OBSTRUCTION_RAW_SHA256:
        raise AssertionError("superseding obstruction raw SHA-256 changed")
    obstruction = _load_object(path)
    if obstruction.get("semantic_digest_sha256") != semantic_digest(obstruction):
        raise AssertionError("superseding obstruction semantic digest does not recompute")
    if (
        obstruction.get("semantic_digest_sha256")
        != PINNED_SUPERSEDING_OBSTRUCTION_SEMANTIC_SHA256
    ):
        raise AssertionError("unexpected superseding obstruction semantic digest")
    if obstruction.get("verdict") != (
        "SR2V_FIXED_HARMONIC_FULL_ALPHA_BETA_CPOBC_UNIT_IDEAL_"
        "OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN"
    ):
        raise AssertionError("unexpected superseding obstruction verdict")
    if obstruction.get("passed") is not True:
        raise AssertionError("superseding obstruction did not pass")
    if obstruction.get("search_terminal") != (
        "FIXED_HARMONIC_STATE_ASSIGNMENT_CHART_TERMINAL_ONLY"
    ):
        raise AssertionError("unexpected superseding obstruction scope")
    return obstruction, raw_sha256


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest, manifest_raw_sha256 = _load_d12_manifest(root)
    budget = _load_budget(root)
    obstruction, obstruction_raw_sha256 = _load_superseding_obstruction(root)

    q5 = reconstruct_q5_determinant()
    localization = q5_localization_polynomial(q5)
    stored_q5 = manifest["shear_parameterisation"]["supplemental_Q5"]
    stored_polynomial = _deserialize_polynomial(stored_q5["determinant_polynomial"])
    q5_digest = _polynomial_digest(q5)

    q5_identity_assignment = {
        "Q5:00": Fraction(1),
        "Q5:01": Fraction(0),
        "Q5:10": Fraction(0),
        "Q5:11": Fraction(1),
        "sigma:detQ5": Fraction(1),
    }
    q5_value = _evaluate(q5, q5_identity_assignment)
    localization_value = _evaluate(localization, q5_identity_assignment)
    d12_point = manifest["D12_pair_open_certificate"]["exact_nonempty_ambient_open_point"]
    d12_value = Fraction(str(d12_point["D12_value"]))

    expected_q5 = {
        ("Q5:00", "Q5:11"): Fraction(1),
        ("Q5:01", "Q5:10"): Fraction(-1),
    }
    gates = {
        "frozen_D12_manifest_raw_SHA256_is_bound": (
            manifest_raw_sha256 == PINNED_D12_RAW_SHA256
        ),
        "frozen_D12_manifest_semantic_digest_is_bound": (
            manifest["semantic_digest_sha256"] == PINNED_D12_SEMANTIC_SHA256
        ),
        "frozen_D12_manifest_remains_solver_free": (
            manifest["resource_and_claim_boundaries"]["solver_status"] == "NOT_RUN"
            and manifest["resource_and_claim_boundaries"]["groebner_status"] == "NOT_RUN"
            and manifest["resource_and_claim_boundaries"]["sage_status"] == "NOT_INVOKED"
            and manifest["resource_and_claim_boundaries"]["finite_field_status"] == "NOT_RUN"
        ),
        "Q5_has_four_distinct_generic_coordinates": set(
            manifest["variables"]["names"][-5:-1]
        )
        == {"Q5:00", "Q5:01", "Q5:10", "Q5:11"},
        "Q5_determinant_reconstructed_exactly": q5 == expected_q5,
        "Q5_determinant_is_nonzero_polynomial": bool(q5)
        and q5.get(("Q5:00", "Q5:11")) == 1,
        "Q5_determinant_agrees_with_bound_manifest": q5 == stored_polynomial,
        "Q5_determinant_digest_agrees_with_bound_manifest": q5_digest
        == stored_q5["determinant_digest_sha256"]
        == PINNED_Q5_DETERMINANT_SHA256,
        "Q5_localization_has_exact_identity_point": q5_value == 1
        and localization_value == 0,
        "combined_D12_Q5_ambient_open_is_nonempty": d12_value != 0 and q5_value != 0,
        "combined_ambient_point_is_not_promoted_to_relation_solution": (
            d12_point["is_required_relation_solution"] is False
        ),
        "campaign_specific_budget_raw_SHA256_is_bound": (
            budget["raw_sha256"] == PINNED_BUDGET_RAW_SHA256
        ),
        "campaign_budget_equals_owner_approved_limits": (
            budget["authorised_limits"]["timeout_seconds_per_chart"] == 3600
            and budget["authorised_limits"]["total_wall_time_seconds"] == 43200
            and budget["authorised_limits"]["memory_limit_gib"] == 8
            and budget["authorised_limits"]["memory_limit_bytes"] == 8 * 1024**3
        ),
        "no_budget_fallback_or_solver_execution": (
            budget["fallback_budget_used"] is False and budget["solver_executed"] is False
        ),
        "historical_manifest_was_unresolved_at_preflight_time": (
            manifest["resource_and_claim_boundaries"]["D12_open_meets_relation_variety"]
            == "UNRESOLVED"
        ),
        "later_fixed_state_unit_ideal_certificate_is_bound": (
            obstruction_raw_sha256 == PINNED_SUPERSEDING_OBSTRUCTION_RAW_SHA256
            and obstruction["semantic_digest_sha256"]
            == PINNED_SUPERSEDING_OBSTRUCTION_SEMANTIC_SHA256
        ),
        "historical_execution_is_fail_closed_cancelled": True,
    }
    if not all(gates.values()):
        failed = sorted(name for name, passed in gates.items() if not passed)
        raise AssertionError(f"SR2-V D12 preflight failed closed: {failed}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_bindings": {
            "D12_manifest": {
                "path": D12_MANIFEST_PATH,
                "raw_sha256": manifest_raw_sha256,
                "semantic_digest_sha256": manifest["semantic_digest_sha256"],
            },
            "campaign_budget": budget,
            "superseding_fixed_state_unit_ideal_obstruction": {
                "path": SUPERSEDING_OBSTRUCTION_PATH,
                "raw_sha256": obstruction_raw_sha256,
                "semantic_digest_sha256": obstruction["semantic_digest_sha256"],
                "verdict": obstruction["verdict"],
            },
        },
        "Q5_nonsingularity_localization": {
            "matrix": [["Q5:00", "Q5:01"], ["Q5:10", "Q5:11"]],
            "definition": "detQ5=Q5:00*Q5:11-Q5:01*Q5:10",
            "determinant_polynomial": _serialize_polynomial(q5),
            "determinant_content_digest_sha256": q5_digest,
            "nonzero_polynomial_certificate": {
                "term_count": len(q5),
                "total_degree": max(len(monomial) for monomial in q5),
                "primitive_integer_content": 1,
                "distinguished_nonzero_term": {
                    "coefficient": "1",
                    "monomial": ["Q5:00", "Q5:11"],
                },
                "exact_Q5_identity_evaluation": str(q5_value),
            },
            "inverse_coordinate": "sigma:detQ5",
            "localization_equation_display": "sigma:detQ5*det(Q5)-1=0",
            "localization_polynomial": _serialize_polynomial(localization),
            "localization_content_digest_sha256": _polynomial_digest(localization),
            "exact_localization_point": {
                "assignment": {
                    name: str(value) for name, value in q5_identity_assignment.items()
                },
                "detQ5_value": str(q5_value),
                "localization_residual": str(localization_value),
            },
        },
        "combined_principal_open": {
            "coordinates_before_Q5_localization": manifest["variables"][
                "saturated_chart_coordinates"
            ],
            "coordinates_after_Q5_localization": (
                manifest["variables"]["saturated_chart_coordinates"] + 1
            ),
            "localizations": ["rho:D12*D12-1", "sigma:detQ5*det(Q5)-1"],
            "exact_ambient_nonempty_point": {
                "D12_value": str(d12_value),
                "detQ5_value": str(q5_value),
                "is_required_relation_solution": False,
                "role": (
                    "ambient simultaneous-principal-open nonemptiness only; "
                    "not a relation-variety point"
                ),
            },
            "historical_preflight_status": "UNRESOLVED_AT_PREFLIGHT_TIME",
            "meets_relation_variety": "EMPTY_ON_FIXED_HARMONIC_SLICE_CERTIFIED",
        },
        "execution_and_claim_boundary": {
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
        },
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "Exact QQ historical preflight provenance only: det(Q5), its localization, "
            "and the approved budget remain certified. The later fixed-harmonic raw-"
            "CPOBC unit-ideal certificate is now bound here, so the D12 execution is "
            "permanently cancelled. No solver was run. This cancellation is terminal "
            "only for the fixed harmonic state assignment, not for SR2-V."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
