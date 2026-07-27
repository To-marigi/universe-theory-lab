from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from universe_lab.final_theory.extension_v03 import (
    extension_benchmark,
    finite_path_distributions,
    verify_extension_certificate,
)

ROOT = Path(__file__).resolve().parents[2]


def test_recorded_path_distributions_are_exact_and_consistent() -> None:
    distributions = finite_path_distributions(5)
    assert len(distributions) == 6
    assert all(
        sum(distribution.values(), start=Fraction(0)) == 1
        for distribution in distributions
    )
    assert len(distributions[-1]) > 63


def test_three_extension_questions_are_not_conflated() -> None:
    result = extension_benchmark()
    assert (
        result["classical_outcome_measure"]["verdict"]
        == "CLASSICAL_OUTCOME_EXTENSION_PASS"
    )
    assert (
        result["operator_valued_instrument_measure"]["verdict"]
        == "INFINITE_EXTENSION_BLOCKED"
    )
    assert (
        result["decoherence_functional"]["verdict"]
        == "DECOHERENCE_FUNCTIONAL_EXTENSION_PASS"
    )
    assert result["verdict"] == "INFINITE_EXTENSION_BLOCKED"


def test_pass_uses_an_all_stage_kernel_proof_not_finite_extrapolation() -> None:
    result = extension_benchmark()
    assumptions = result["classical_outcome_measure"]["assumption_check"]
    assert assumptions["all_stage_definition"]
    assert result["finite_sequences"]["finite_checks_passed"]
    assert "not from extrapolating" in result["finite_sequences"][
        "finite_check_boundary"
    ]


def test_scalar_extension_does_not_promote_the_full_instrument() -> None:
    result = extension_benchmark()
    operator_measure = result["operator_valued_instrument_measure"]
    assert operator_measure["blocking_defects"]
    assert "cannot" in operator_measure["theorem_not_applied"]


def test_checked_in_extension_certificate_verifies() -> None:
    certificate = (
        ROOT
        / "certificates"
        / "infinite_extension"
        / "classical_diagonal_extension_v0.3.json"
    )
    result = verify_extension_certificate(certificate)
    assert result["passed"]
    assert all(result["checks"].values())
