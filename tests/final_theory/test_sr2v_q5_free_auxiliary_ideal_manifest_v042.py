"""Fail-closed guards for the Phase-A auxiliary-ideal resource checkpoint."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_manifest_v042 as result

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTIC_DIGEST = "357d739091d2bf36740895f35c9227ba912e69f8d455f9e91dd8a6ea7ce6c605"
T1, T2, T3, T4 = result.T_SYMBOLS


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def rebuilt() -> dict[str, Any]:
    return result.build_resource_open_payload(ROOT)


def test_checkpoint_rebuilds_exactly_and_remains_nonterminal(
    rebuilt: dict[str, Any],
) -> None:
    frozen = _load(result.RESULT_PATH)
    assert frozen == rebuilt
    assert frozen["schema_version"] == result.SCHEMA
    assert frozen["verdict"] == result.OPEN_VERDICT
    assert frozen["semantic_digest_sha256"] == EXPECTED_SEMANTIC_DIGEST
    assert result.semantic_digest(frozen) == EXPECTED_SEMANTIC_DIGEST
    assert frozen["passed"] is False
    assert frozen["search_terminal"] == result.SEARCH_TERMINAL


def test_canonical_inputs_and_bottom_localization_are_bound(
    rebuilt: dict[str, Any],
) -> None:
    assert len(rebuilt["predecessor_bindings"]) == 4
    assert all(
        record["canonical_semantic_binding_passed"]
        for record in rebuilt["predecessor_bindings"].values()
    )
    machine_scope = rebuilt["machine_certified_scope"]
    localization = machine_scope["bottom_localization_ledger"]
    assert localization["factor_count"] == 14
    assert localization["passed"] is True
    assert all(localization["gates"].values())
    assert "F_lambda" in machine_scope["active_ring"]
    assert machine_scope["pure_Laurent_52_torus_claimed"] is False

    base = machine_scope["lightweight_base_ring_certificate"]
    assert base["upper_kernel_storage_shape"] == [49, 132]
    assert base["Q5_context_index"] == 131
    assert base["Q5_only_upper_columns"] == [48]
    assert base["Q5_only_upper_column_support"] == [131]
    assert base["bottom_q5_violation_count"] == 0
    assert base["dropped_spectator_names"] == ["bottom_q5", "s48"]
    assert base["active_variable_count"] == 52
    assert base["active_variables"] == [
        "t1",
        "t2",
        "t3",
        "t4",
        *(f"s{index}" for index in range(48)),
    ]
    assert base["reconstructed_active_ring"] == result.ACTIVE_RING
    assert base["declared_active_ring"] == result.ACTIVE_RING
    assert base["passed"] is True
    assert all(base["gates"].values())


def test_resource_attempt_is_manual_and_fail_closed(
    rebuilt: dict[str, Any],
) -> None:
    provenance = rebuilt["resource_attempt_provenance"]
    assert provenance["classification"] == "MANUALLY_RECORDED_LOCAL_OBSERVATION"
    for unavailable in (
        "attempt_provenance_machine_reproducible",
        "source_snapshot_available",
        "source_snapshot_sha256_available",
        "raw_monitor_log_available",
        "timeout_exit_record_available",
        "file_probe_record_available",
        "stdout_sha256_available",
        "stderr_sha256_available",
        "current_command_reproduces_attempt",
        "partial_source_rebuild_progress_machine_certified",
        "partial_pivot_progress_machine_certified",
        "partial_Schur_row_progress_machine_certified",
    ):
        assert provenance[unavailable] is False
    assert provenance["certified_partial_completion_count"] is None

    attempt = rebuilt["bounded_attempt"]
    assert attempt["provenance"] == "MANUALLY_RECORDED_LOCAL_OBSERVATION"
    assert attempt["declared_hard_request_limit_seconds"] == 3600
    assert attempt["partial_progress_claimed"] is False
    assert "hard_request_limit_enforced" not in rebuilt["gates"]
    assert rebuilt["gates"]["full_1127_source_Schur_ledger_generated"] is False
    assert rebuilt["gates"]["full_six_chart_generator_manifests_generated"] is False
    assert rebuilt["gates"]["denominator_inverse_reconstruction_ledger_completed"] is False


def test_no_solver_or_mathematical_terminal_is_claimed(rebuilt: dict[str, Any]) -> None:
    solver = rebuilt["manually_recorded_solver_observation"]
    assert solver["provenance"] == "MANUALLY_RECORDED_LOCAL_OBSERVATION"
    assert not any(value for key, value in solver.items() if key != "provenance")
    assert rebuilt["gates"]["no_solver_or_unit_ideal_claim"] is True
    boundary = rebuilt["claim_boundary"]
    for excluded in (
        "only the canonical bound inputs",
        "manually recorded local observations",
        "Groebner/unit-ideal claims",
        "witness claims",
        "commutativity claims",
        "every SR2-V terminal remain open",
    ):
        assert excluded.lower() in boundary.lower()


def test_report_is_an_exact_LF_render_of_the_payload(rebuilt: dict[str, Any]) -> None:
    frozen = (ROOT / result.REPORT_PATH).read_text(encoding="utf-8")
    assert frozen == result.render_resource_open_report(rebuilt)
    assert "\r" not in frozen


# The compiler represents every Laurent coefficient as a reduced element of the
# rational function field QQ(t1,t2,t3,t4) rather than as a generic SymPy
# expression normalised by ``sp.cancel``.  The guards below pin the properties
# that make the faster representation and its trial-division denominator handling
# mathematically interchangeable with the expression-level path.

COEFFICIENT_SAMPLES = (
    sp.Integer(1),
    sp.Integer(-3),
    sp.Rational(4, 7),
    T1 * T2 - 1,
    (T1 * T2 - 1) / (T3 + 2),
    (T1**2 - T4) / (T1 * T2 * T3 - 5),
    (2 * T1 + 3 * T2 * T3) / (T1 - T2),
    (T1 * T2 * T3 * T4 + T1 - 1) / (7 * T2**2 - 3),
)


@pytest.fixture(scope="module")
def factor_basis() -> dict[str, dict[str, Any]]:
    return result._lambda_factor_basis()


@pytest.mark.parametrize("expression", COEFFICIENT_SAMPLES)
def test_coefficients_land_in_the_declared_QQ_t_fraction_field(expression: sp.Expr) -> None:
    coefficient = result._normal_coefficient(expression)
    assert coefficient.field is result.COEFFICIENT_FIELD
    assert result.COEFFICIENT_RING.symbols == result.T_SYMBOLS
    assert sp.cancel(coefficient.as_expr() - expression) == 0


def test_normal_coefficient_accepts_python_scalars() -> None:
    assert result._normal_coefficient(5).as_expr() == 5
    assert result._normal_coefficient(Fraction(3, 8)).as_expr() == sp.Rational(3, 8)
    already = result._normal_coefficient(T1 / T2)
    assert result._normal_coefficient(already) is already


@pytest.mark.parametrize("expression", COEFFICIENT_SAMPLES)
def test_serialisation_is_the_denominator_monic_reduced_pair(expression: sp.Expr) -> None:
    """The sparse serialiser must agree with the sp.cancel/sp.fraction normal form."""

    serial = result._serial_coefficient(result._normal_coefficient(expression))
    numerator, denominator = sp.fraction(sp.cancel(expression))
    leading = sp.Poly(denominator, *result.T_SYMBOLS, domain=sp.QQ).LC()
    assert serial == {
        "numerator": result._serial_qq_polynomial(sp.expand(numerator / leading)),
        "denominator": result._serial_qq_polynomial(sp.expand(denominator / leading)),
    }
    assert serial["denominator"][0][1:] == [1, 1]


def test_lambda_factor_basis_is_irreducible(factor_basis: dict[str, dict[str, Any]]) -> None:
    """Trial division is only equivalent to factorisation over an irreducible basis."""

    assert len(factor_basis) == 14
    for record in factor_basis.values():
        unit, factors = sp.factor_list(record["polynomial"], *result.T_SYMBOLS)
        assert sp.sympify(unit).is_Rational
        assert len(factors) == 1
        assert int(factors[0][1]) == 1
        assert record["ring_polynomial"].as_expr() == record["polynomial"]


def test_trial_division_agrees_with_full_factorisation(
    factor_basis: dict[str, dict[str, Any]],
) -> None:
    """Denominators built from lambda factors must split into the same multiplicities."""

    records = sorted(factor_basis.values(), key=lambda record: str(record["factor_id"]))
    cases = [
        {str(records[0]["factor_id"]): 1},
        {str(records[0]["factor_id"]): 2, str(records[3]["factor_id"]): 1},
        {str(records[1]["factor_id"]): 1, str(records[5]["factor_id"]): 3},
    ]
    for exponents in cases:
        denominator, _expression = result._certified_denominator_product(exponents, factor_basis)
        coefficient = result.COEFFICIENT_ONE / result.COEFFICIENT_FIELD(denominator)
        factors, certified, unknown = result._denominator_factorisation(coefficient, factor_basis)
        assert certified
        assert not unknown
        assert factors == exponents

    outside = result._normal_coefficient(1 / (T1 + T2 + T3 + T4 + 11))
    _factors, certified, unknown = result._denominator_factorisation(outside, factor_basis)
    assert not certified
    assert unknown == ["t1 + t2 + t3 + t4 + 11"]


def _clearing_sample(
    factor_basis: dict[str, dict[str, Any]],
    exponents: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]],
) -> dict[str, dict[tuple[int, ...], Any]]:
    records = sorted(factor_basis.values(), key=lambda record: str(record["factor_id"]))
    first, second = (result.COEFFICIENT_FIELD(record["ring_polynomial"]) for record in records[:2])
    plain, upper, mixed = exponents
    return {
        "A": {plain: result.COEFFICIENT_ONE / first, upper: second / first**2},
        "B": {mixed: result._normal_coefficient(Fraction(3, 4)) / second},
    }


def test_clearing_certificate_inverts_exactly(factor_basis: dict[str, dict[str, Any]]) -> None:
    """Clearing by the certified product must be reversible term by term."""

    width = 52
    coefficients = _clearing_sample(
        factor_basis,
        (
            (0,) * width,
            (0, 0, 0, 0, 3, *(0,) * (width - 5)),
            (0, 0, 0, 0, -2, 1, *(0,) * (width - 6)),
        ),
    )
    certificate = result._clearing_certificate(
        coefficients,
        result.LocalizedArena(),
        result.PolynomialArena(),
        factor_basis,
    )
    assert certificate["inverse_reconstruction_verified"] is True
    assert certificate["cleared_exponents_are_nonnegative"] is True
    assert certificate["cleared_coefficients_are_integers"] is True
    assert certificate["bottom_polynomial_clearing_exponent"] == [0, 0, 0, 0]
    assert certificate[
        "denominator_is_product_of_rational_Laurent_monomial_and_certified_CSG_factors"
    ]
    assert certificate["unknown_denominator_factors"] == []


def test_clearing_certificate_fails_closed_on_bottom_Laurent_exponents(
    factor_basis: dict[str, dict[str, Any]],
) -> None:
    """A bottom exponent outside the upper lattice must not pass as reconstructed.

    Every Laurent exponent the compiler produces is zero in the four bottom
    coordinates, so folding them back into the coefficients is injective.  If that
    ever stops holding, the round trip merges distinct terms and the gate has to
    report a failure rather than a silent match.
    """

    width = 52
    coefficients = _clearing_sample(
        factor_basis,
        (
            (0,) * width,
            (0, 1, *(0,) * (width - 2)),
            (0, 0, 0, 0, -2, *(0,) * (width - 5)),
        ),
    )
    certificate = result._clearing_certificate(
        coefficients,
        result.LocalizedArena(),
        result.PolynomialArena(),
        factor_basis,
    )
    assert certificate["inverse_reconstruction_verified"] is False


def test_evaluate_matches_direct_substitution() -> None:
    """Rational evaluation must reproduce substitution into the equivalent expression."""

    width = 6
    polynomial = {
        (1, 0, -1, 0, 2, 0): result._normal_coefficient((T1 * T2 - 1) / (T3 + 2)),
        (0, 1, 0, 0, 0, -1): result._normal_coefficient(T4 / (T1 + 3)),
    }
    assert all(len(exponent) == width for exponent in polynomial)
    point = (
        Fraction(2),
        Fraction(3),
        Fraction(5),
        Fraction(7),
        Fraction(1, 2),
        Fraction(3),
    )
    substitutions = dict(zip(result.T_SYMBOLS, point[:4], strict=True))
    expected = sp.Integer(0)
    for exponent, coefficient in polynomial.items():
        term = coefficient.as_expr().subs(substitutions)
        for value, power in zip(point, exponent, strict=True):
            term *= sp.Rational(value.numerator, value.denominator) ** power
        expected += term
    value = result._evaluate(polynomial, point)
    assert sp.Rational(value.numerator, value.denominator) == sp.cancel(expected)


def test_progress_callback_is_optional_and_reports_row_digests() -> None:
    """The row observer defaults to a no-op so the compiler entry point is unchanged."""

    seen: list[tuple[str, int, int, str]] = []
    reporter = result._progress_reporter(lambda *record: seen.append(record))
    reporter("schur_row", 1, 1127, "deadbeef")
    assert seen == [("schur_row", 1, 1127, "deadbeef")]
    assert result._progress_reporter(None)("schur_row", 1, 1127, "deadbeef") is None
