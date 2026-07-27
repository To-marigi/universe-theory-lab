"""Eight-dimensional F-theory/heterotic compiler benchmark.

The F-theory side derives vanishing orders from the four Weierstrass models in
arXiv:2205.08100v1.  The heterotic side is deliberately not filled with the
paper's answer: the source does not provide compiler-ready Wilson vectors for
all four non-geometric branches, so the cross-frame certificate remains
BLOCKED in v0.1.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import sympy as sp

from universe_lab.stringbench.evidence import EvidenceState
from universe_lab.stringbench.frames.f_theory import (
    FibrationKind,
    FTheoryCompilation,
    FTheoryInput,
    compile_f_theory,
)
from universe_lab.stringbench.frames.heterotic import (
    HeteroticInput,
    compile_heterotic,
)
from universe_lab.stringbench.invariants.kodaira import infer_kodaira_fiber
from universe_lab.stringbench.invariants.lattices import (
    analyze_gram_matrix,
    n_polarization_gram,
    narain_2_18_gram,
)

SOURCE_EXPECTATIONS: dict[FibrationKind, tuple[tuple[str, str, str], ...]] = {
    FibrationKind.STANDARD: (("u", "III*", "E7"), ("v", "III*", "E7")),
    FibrationKind.ALTERNATE: (("v", "I8*", "D12"),),
    FibrationKind.BASE_FIBER_DUAL: (("u", "I2*", "D6"), ("v", "II*", "E8")),
    FibrationKind.MAXIMAL: (("v", "I10*", "D14"),),
}


def _vanishing_order(expression: sp.Expr, variable: sp.Symbol, other: sp.Symbol) -> int:
    local = sp.Poly(sp.expand(expression.subs(other, 1)), variable)
    if local.is_zero:
        raise ValueError("identically zero expression has no finite vanishing order")
    return min(monomial[0] for monomial, _coefficient in local.terms())


def _short_coefficients(
    compilation: FTheoryCompilation,
) -> tuple[sp.Expr, sp.Expr]:
    coefficients = compilation.coefficients
    if compilation.equation_kind == "short_weierstrass":
        keys = ("f", "g") if "f" in coefficients else ("F", "G")
        return coefficients[keys[0]], coefficients[keys[1]]
    if compilation.equation_kind == "two_torsion_weierstrass":
        a = coefficients["A"]
        b = coefficients["B"]
        return sp.expand(b - a**2 / 3), sp.expand(2 * a**3 / 27 - a * b / 3)
    if compilation.equation_kind == "general_cubic_weierstrass":
        a = coefficients["a"]
        b = coefficients["b"]
        c = coefficients["c"]
        return sp.expand(b - a**2 / 3), sp.expand(2 * a**3 / 27 - a * b / 3 + c)
    raise ValueError(f"unsupported equation kind: {compilation.equation_kind}")


def _fibration_check(kind: FibrationKind) -> dict[str, Any]:
    u, v = sp.symbols("u v")
    data = FTheoryInput(1, 2, 3, 5, 7, 11, kind)
    compilation = compile_f_theory(data, base_coordinates=(u, v))
    if compilation.discriminant is None:
        return {
            "fibration": kind.value,
            "status": EvidenceState.BLOCKED.value,
            "passed": False,
            "reason": compilation.limitations,
        }
    f, g = _short_coefficients(compilation)
    loci: list[dict[str, Any]] = []
    all_match = True
    for coordinate, expected_fiber, expected_ade in SOURCE_EXPECTATIONS[kind]:
        variable, other = (u, v) if coordinate == "u" else (v, u)
        orders = (
            _vanishing_order(f, variable, other),
            _vanishing_order(g, variable, other),
            _vanishing_order(compilation.discriminant, variable, other),
        )
        inferred = infer_kodaira_fiber(*orders, split=True)
        matched = (
            inferred.fiber_type == expected_fiber and inferred.ade_type == expected_ade
        )
        all_match &= matched
        loci.append(
            {
                "coordinate": coordinate,
                "orders": orders,
                "derived_fiber": inferred.fiber_type,
                "derived_ade": inferred.ade_type,
                "source_expected_fiber": expected_fiber,
                "source_expected_ade": expected_ade,
                "matched": matched,
            }
        )
    total_degree = int(sp.Poly(compilation.discriminant, u, v).total_degree())
    degree_ok = total_degree == 24
    return {
        "fibration": kind.value,
        "status": compilation.status.value,
        "equation_kind": compilation.equation_kind,
        "discriminant_total_degree": total_degree,
        "k3_degree_24": degree_ok,
        "loci": loci,
        "passed": bool(all_match and degree_ok),
        "mordell_weil": {
            "rank": compilation.mordell_weil_rank,
            "torsion": compilation.mordell_weil_torsion,
            "evidence": (
                "explicit two-torsion point (0,0) is visible for alternate; "
                "triviality for other branches is source-classified, not re-proved"
            ),
        },
    }


def _lattice_checks() -> dict[str, Any]:
    polarization = analyze_gram_matrix(n_polarization_gram())
    narain = analyze_gram_matrix(narain_2_18_gram())
    passed = (
        polarization.rank == 16
        and polarization.signature == (1, 15, 0)
        and polarization.discriminant_order == 4
        and narain.rank == 20
        and narain.signature == (2, 18, 0)
        and narain.even
        and narain.unimodular
    )
    return {
        "name": "lattice_invariants",
        "status": EvidenceState.EXACT_SYMBOLIC.value,
        "polarization": asdict(polarization),
        "narain": asdict(narain),
        "passed": passed,
    }


def _heterotic_independence_check() -> dict[str, Any]:
    zeros = (0.0,) * 16
    compilation = compile_heterotic(
        HeteroticInput(1j, 2j, zeros, zeros)
    )
    zero_line_sanity = compilation.root_count == 480
    return {
        "name": "heterotic_frontend",
        "status": EvidenceState.BLOCKED.value,
        "narain_signature": compilation.narain_lattice.signature,
        "zero_wilson_line_root_count": compilation.root_count,
        "zero_line_sanity_passed": zero_line_sanity,
        "four_branch_lowering_passed": False,
        "reason": (
            "arXiv:2205.08100 describes the four branches as non-geometric "
            "O(2,18) orbits but does not provide four compiler-ready pairs of "
            "Wilson vectors in the frontend basis"
        ),
        "limitations": compilation.limitations,
    }


def _negative_controls() -> dict[str, Any]:
    """Mutations that can be tested without a heterotic answer key."""

    u, v = sp.symbols("u v")
    alternate = compile_f_theory(
        FTheoryInput(1, 2, 3, 5, 7, 11, FibrationKind.ALTERNATE),
        base_coordinates=(u, v),
    )
    assert alternate.discriminant is not None
    original_degree = int(sp.Poly(alternate.discriminant, u, v).total_degree())
    degree_mutation_detected = (
        int(sp.Poly(alternate.discriminant * v, u, v).total_degree()) != 24
    )
    torsion_mutation_detected = (
        alternate.equation_kind == "two_torsion_weierstrass"
        and alternate.mordell_weil_torsion != "trivial"
    )
    bad_domain = compile_f_theory(
        FTheoryInput(1, 2, 0, 0, 0, 0, FibrationKind.STANDARD),
        base_coordinates=(u, v),
    )
    domain_mutation_detected = bad_domain.status is EvidenceState.BLOCKED
    signature = analyze_gram_matrix(-narain_2_18_gram()).signature
    signature_mutation_detected = signature != (2, 18, 0)
    checks = {
        "discriminant_degree_change": degree_mutation_detected,
        "mordell_weil_torsion_drop": torsion_mutation_detected,
        "validity_domain_violation": domain_mutation_detected,
        "lattice_signature_flip": signature_mutation_detected,
        "wilson_line_missing": False,
        "raw_coordinate_comparison": False,
        "wrong_gauge_correspondence": False,
        "branch_aliasing": False,
    }
    return {
        "name": "negative_controls",
        "status": EvidenceState.PARTIAL.value,
        "checks": checks,
        "detected": sum(checks.values()),
        "required": len(checks),
        "original_alternate_discriminant_degree": original_degree,
        "passed": False,
        "reason": "heterotic branch fixtures and typed-link integration remain incomplete",
    }


def _precision_convergence() -> dict[str, Any]:
    """Check 50/100/200-bit evaluation against a 400-bit reference."""

    expression = sp.sin(1) + sp.sqrt(2) + sp.log(3)
    reference = sp.N(expression, 125)
    errors: list[float] = []
    for bits in (50, 100, 200):
        decimal_digits = max(17, int(bits * np.log10(2)))
        approximation = sp.N(expression, decimal_digits)
        error = abs(float(sp.N(approximation - reference, 100)))
        errors.append(error)
    passed = errors[2] < errors[1] < errors[0]
    return {
        "name": "precision_convergence",
        "status": EvidenceState.EXACT_SYMBOLIC.value,
        "bits": [50, 100, 200],
        "absolute_errors": errors,
        "reference_bits": 400,
        "passed": passed,
        "scope": "arithmetic pipeline smoke test; no ill-conditioned moduli inversion is claimed",
    }


def run_f_heterotic_8d() -> dict[str, Any]:
    """Run v0.1 and keep local algebra success separate from duality completion."""

    fibrations = [_fibration_check(kind) for kind in FibrationKind]
    lattice = _lattice_checks()
    heterotic = _heterotic_independence_check()
    mutations = _negative_controls()
    precision = _precision_convergence()
    f_theory_passed = all(item["passed"] for item in fibrations)
    return {
        "suite": "f-heterotic-8d",
        "source": "arXiv:2205.08100v1",
        "f_theory": {
            "status": (
                EvidenceState.EXACT_SYMBOLIC.value
                if f_theory_passed
                else EvidenceState.CONTRADICTED.value
            ),
            "all_four_fibrations": fibrations,
            "passed": f_theory_passed,
        },
        "lattices": lattice,
        "heterotic": heterotic,
        "mutations": mutations,
        "precision": precision,
        "round_trip": {
            "status": EvidenceState.BLOCKED.value,
            "passed": False,
            "reason": "no independently compiled four-branch heterotic VacuumIR",
        },
        "held_out": {
            "status": EvidenceState.BLOCKED.value,
            "passed": False,
            "reason": "a non-leaking branch/locus split requires the blocked heterotic map",
        },
        "overall_status": EvidenceState.PARTIAL.value,
        "string_compiler_v0_1_pass": False,
        "allowed_claim": "FOUR_F_THEORY_FIBRATIONS_SYMBOLICALLY_CHECKED"
        if f_theory_passed
        else "F_THEORY_SYMBOLIC_CHECK_FAILED",
    }
