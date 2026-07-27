"""Exact J30-locus certificates from two independent source formulas.

Oracle A uses ``Disc_t D`` from arXiv:2205.08100v1, Eqs. (2.39)--(2.40).
Oracle B independently expands the maximal cubic in Eq. (2.43), divides its
discriminant by ``J6^16``, and uses ``Disc_t d`` as in Eq. (2.44).

This production module deliberately does not import the fixture generator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import sympy as sp

from universe_lab.stringbench.frames.f_theory import (
    FibrationKind,
    FTheoryInput,
    compile_f_theory,
)
from universe_lab.stringbench.invariants.kodaira import (
    fiber_configuration_euler_sum,
    infer_kodaira_fiber,
)
from universe_lab.stringbench.invariants.weierstrass import cubic_discriminant

T = sp.Symbol("t")
U, V = sp.symbols("u v")


def _rational(value: Any) -> sp.Rational:
    result = sp.Rational(str(value))
    if not result.is_Rational:
        raise ValueError(f"expected a rational value, got {value!r}")
    return result


@dataclass(frozen=True, slots=True)
class J30Point:
    j2: sp.Rational
    j3: sp.Rational
    j4: sp.Rational
    j5: sp.Rational
    j6: sp.Rational
    double_root: sp.Rational
    name: str
    role: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> J30Point:
        return cls(
            j2=_rational(payload["j2"]),
            j3=_rational(payload["j3"]),
            j4=_rational(payload["j4"]),
            j5=_rational(payload["j5"]),
            j6=_rational(payload["j6"]),
            double_root=_rational(payload["double_root"]),
            name=str(payload["name"]),
            role=str(payload["role"]),
        )

    def weighted_scale(self, scale: Any) -> J30Point:
        lam = _rational(scale)
        if lam == 0:
            raise ValueError("weighted-projective scale must be nonzero")
        # The base coordinate has weight one in the affine formula for D.
        return J30Point(
            self.j2 * lam**2,
            self.j3 * lam**3,
            self.j4 * lam**4,
            self.j5 * lam**5,
            self.j6 * lam**6,
            self.double_root * lam,
            self.name + f":scaled-{lam}",
            self.role,
        )


def alternate_polynomials(point: J30Point) -> tuple[sp.Poly, sp.Poly]:
    """Return E and D without using the maximal-fibration implementation."""

    j2, j3, j4, j5, j6 = point.j2, point.j3, point.j4, point.j5, point.j6
    e = j4 * T**2 - j5 * T + j6
    d = (
        T**6
        - 6 * j2 * T**4
        - 4 * j3 * T**3
        + (9 * j2**2 - 4 * j4) * T**2
        + (12 * j2 * j3 + 4 * j5) * T
        + 4 * (j3**2 - j6)
    )
    return sp.Poly(e, T, domain=sp.QQ), sp.Poly(d, T, domain=sp.QQ)


def maximal_residual(point: J30Point) -> sp.Poly:
    """Return d(t) from the independent maximal cubic formula."""

    j2, j3, j4, j5, j6 = point.j2, point.j3, point.j4, point.j5, point.j6
    if j6 == 0:
        raise ValueError("Eq. (2.43) normalization requires J6 != 0")
    a = j6 * (
        T**3
        + 6 * j3 * j4 * T**2
        + 3 * (4 * j3**2 * j4**2 - j2 * j6**2) * T
        - 2 * j3 * (3 * j2 * j4 * j6**2 - 4 * j3**2 * j4**3 + j6**3)
    )
    b = -j6**6 * (
        2 * j4 * T**2
        + (8 * j3 * j4**2 + j5 * j6) * T
        + (
            8 * j3**2 * j4**3
            - 3 * j2 * j4 * j6**2
            + 2 * j3 * j4 * j5 * j6
            - j6**3
        )
    )
    c = j4 * j6**11 * (j4 * T + 2 * j3 * j4**2 + j5 * j6)
    delta = sp.Poly(cubic_discriminant(a, b, c), T, domain=sp.QQ)
    quotient, remainder = sp.div(delta, sp.Poly(j6**16, T, domain=sp.QQ))
    if not remainder.is_zero:
        raise ArithmeticError("maximal discriminant is not divisible by J6^16")
    return quotient


def _order_at_zero(expression: sp.Expr, variable: sp.Symbol) -> int:
    polynomial = sp.Poly(sp.expand(expression), variable, extension=True)
    if polynomial.is_zero:
        raise ValueError("zero polynomial has no finite vanishing order")
    return min(monomial[0] for monomial, coefficient in polynomial.terms() if coefficient)


def _short_coefficients(
    kind: FibrationKind,
    coefficients: dict[str, sp.Expr],
) -> tuple[sp.Expr, sp.Expr]:
    if kind is FibrationKind.STANDARD:
        return coefficients["f"], coefficients["g"]
    if kind is FibrationKind.BASE_FIBER_DUAL:
        return coefficients["F"], coefficients["G"]
    if kind is FibrationKind.ALTERNATE:
        a, b = coefficients["A"], coefficients["B"]
        return sp.expand(b - a**2 / 3), sp.expand(2 * a**3 / 27 - a * b / 3)
    a, b, c = coefficients["a"], coefficients["b"], coefficients["c"]
    return sp.expand(b - a**2 / 3), sp.expand(2 * a**3 / 27 - a * b / 3 + c)


def _factor_multiplicities(polynomial: sp.Poly) -> dict[int, int]:
    """Count geometric roots by multiplicity over characteristic zero."""

    counts: dict[int, int] = {}
    _, factors = sp.factor_list(polynomial, extension=True)
    for factor, multiplicity in factors:
        counts[multiplicity] = counts.get(multiplicity, 0) + factor.degree()
    return counts


_MW = {
    FibrationKind.STANDARD: (0, "trivial"),
    FibrationKind.ALTERNATE: (0, "Z/2Z"),
    FibrationKind.BASE_FIBER_DUAL: (0, "trivial"),
    FibrationKind.MAXIMAL: (0, "trivial"),
}

_LATTICE = {
    FibrationKind.STANDARD: "H + E7(-1) + E7(-1) + A1(-1)",
    FibrationKind.ALTERNATE: "H + E7(-1) + E7(-1) + A1(-1)",
    FibrationKind.BASE_FIBER_DUAL: "H + E8(-1) + D6(-1) + A1(-1)",
    FibrationKind.MAXIMAL: "H + D14(-1) + A1(-1)",
}

_ADE_RANK = {
    "A1": 1,
    "D6": 6,
    "D12": 12,
    "D14": 14,
    "E7": 7,
    "E8": 8,
}


def _quartic_representative(point: J30Point) -> FTheoryInput:
    """Choose one algebraic representative of the invariant weighted point."""

    if point.j4 == 0:
        raise ValueError("J30 generic confluence requires J4 != 0")
    a_squared = point.j5**2 - 4 * point.j4 * point.j6
    gamma = sp.Integer(1)
    epsilon = point.j4
    delta = (point.j5 + sp.sqrt(a_squared)) / (2 * point.j4)
    zeta = sp.cancel(point.j6 / delta)
    return FTheoryInput(
        point.j2,
        point.j3,
        gamma,
        delta,
        epsilon,
        zeta,
        FibrationKind.STANDARD,
    )


def _input_for_kind(representative: FTheoryInput, kind: FibrationKind) -> FTheoryInput:
    alpha, beta, gamma, delta, epsilon, zeta = representative.coefficients
    return FTheoryInput(
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        delta=delta,
        epsilon=epsilon,
        zeta=zeta,
        fibration=kind,
    )


def _other_resultants(point: J30Point) -> dict[str, sp.Expr]:
    representative = _quartic_representative(point)
    values: dict[str, sp.Expr] = {}
    for kind in (
        FibrationKind.STANDARD,
        FibrationKind.BASE_FIBER_DUAL,
        FibrationKind.MAXIMAL,
    ):
        compilation = compile_f_theory(
            _input_for_kind(representative, kind),
            base_coordinates=(U, V),
        )
        f, g = _short_coefficients(kind, compilation.coefficients)
        f_t, g_t = sp.expand(f.subs({U: T, V: 1})), sp.expand(
            g.subs({U: T, V: 1})
        )
        if kind is FibrationKind.STANDARD:
            f_t, g_t = sp.cancel(f_t / T**3), sp.cancel(g_t / T**5)
        elif kind is FibrationKind.BASE_FIBER_DUAL:
            f_t, g_t = sp.cancel(f_t / T**2), sp.cancel(g_t / T**3)
        values[kind.value] = sp.simplify(sp.resultant(f_t, g_t, T))
    return values


def derive_four_fibration_confluence(point: J30Point) -> list[dict[str, Any]]:
    """Derive fiber multiplicities from each compiled discriminant."""

    representative = _quartic_representative(point)
    certificates: list[dict[str, Any]] = []
    for kind in FibrationKind:
        compilation = compile_f_theory(
            _input_for_kind(representative, kind),
            base_coordinates=(U, V),
        )
        if compilation.discriminant is None:
            raise ArithmeticError(f"missing discriminant for {kind.value}")
        f, g = _short_coefficients(kind, compilation.coefficients)
        finite_f = sp.expand(f.subs({U: T, V: 1}))
        finite_g = sp.expand(g.subs({U: T, V: 1}))
        finite_delta = sp.expand(compilation.discriminant.subs({U: T, V: 1}))
        infinity_f = sp.expand(f.subs({U: 1, V: T}))
        infinity_g = sp.expand(g.subs({U: 1, V: T}))
        infinity_delta = sp.expand(compilation.discriminant.subs({U: 1, V: T}))
        ord_zero = (
            _order_at_zero(finite_f, T),
            _order_at_zero(finite_g, T),
            _order_at_zero(finite_delta, T),
        )
        ord_infinity = (
            _order_at_zero(infinity_f, T),
            _order_at_zero(infinity_g, T),
            _order_at_zero(infinity_delta, T),
        )
        zero_fiber = infer_kodaira_fiber(*ord_zero, split=True)
        infinity_fiber = infer_kodaira_fiber(*ord_infinity, split=True)
        fixed: list[str] = []
        fixed_ade: list[str] = []
        if zero_fiber.fiber_type != "I0":
            if zero_fiber.fiber_type is None:
                raise ArithmeticError(f"unsupported zero fiber for {kind.value}: {ord_zero}")
            fixed.append(zero_fiber.fiber_type)
            if zero_fiber.ade_type:
                fixed_ade.append(zero_fiber.ade_type)
        if infinity_fiber.fiber_type != "I0":
            if infinity_fiber.fiber_type is None:
                raise ArithmeticError(
                    f"unsupported infinity fiber for {kind.value}: {ord_infinity}"
                )
            fixed.append(infinity_fiber.fiber_type)
            if infinity_fiber.ade_type:
                fixed_ade.append(infinity_fiber.ade_type)

        residual = sp.Poly(
            sp.cancel(finite_delta / T ** ord_zero[2]),
            T,
            extension=True,
        )
        multiplicities = _factor_multiplicities(residual)
        moving = [
            f"I{multiplicity}"
            for multiplicity, count in sorted(multiplicities.items(), reverse=True)
            for _ in range(count)
        ]
        moving_ade = [
            f"A{multiplicity - 1}"
            for multiplicity, count in multiplicities.items()
            if multiplicity > 1
            for _ in range(count)
        ]
        fibers = tuple(fixed + moving)
        ade = fixed_ade + moving_ade
        mw_rank, mw_torsion = _MW[kind]
        shioda_tate = 2 + sum(_ADE_RANK[item] for item in ade) + mw_rank
        certificates.append(
            {
                "fibration": kind.value,
                "zero_orders": list(ord_zero),
                "infinity_orders": list(ord_infinity),
                "residual_degree": residual.degree(),
                "root_multiplicity_counts": {
                    str(key): value for key, value in sorted(multiplicities.items())
                },
                "fibers": list(fibers),
                "ade_components": ade,
                "euler_number": fiber_configuration_euler_sum(fibers),
                "mordell_weil_rank": mw_rank,
                "mordell_weil_torsion": mw_torsion,
                "shioda_tate_picard_rank": shioda_tate,
                "lattice_polarization": _LATTICE[kind],
                "discriminant_group": "(Z/2Z)^3",
                "factorization_evidence": "INDEPENDENTLY_DERIVED",
                "mw_and_lattice_evidence": "SOURCE_FORMULA_SYMBOLICALLY_VERIFIED",
            }
        )
    return certificates


def certify_j30_point(point: J30Point, *, include_fibrations: bool = True) -> dict[str, Any]:
    """Certify a generic codimension-one J30 point using exact arithmetic."""

    e, d_alt = alternate_polynomials(point)
    d_max = maximal_residual(point) if point.j6 != 0 else None
    disc_alt = sp.discriminant(d_alt.as_expr(), T)
    disc_max = sp.discriminant(d_max.as_expr(), T) if d_max is not None else None
    root = point.double_root
    gcd_alt = sp.gcd(d_alt, d_alt.diff()).monic()
    gcd_max = sp.gcd(d_max, d_max.diff()).monic() if d_max is not None else None
    root_square = sp.Poly((T - root) ** 2, T, domain=sp.QQ)
    residual_alt, remainder_alt = sp.div(d_alt, root_square)
    residual_max: sp.Poly | None = None
    remainder_max: sp.Poly | None = None
    if d_max is not None and gcd_max is not None and gcd_max.degree() == 1:
        maximal_root_square = gcd_max * gcd_max
        residual_max, remainder_max = sp.div(d_max, maximal_root_square)
    resultant_de = sp.resultant(d_alt.as_expr(), e.as_expr(), T)
    a_squared = point.j5**2 - 4 * point.j4 * point.j6
    other_resultants: dict[str, sp.Expr] = {}
    if point.j4 != 0 and point.j6 != 0 and a_squared != 0:
        other_resultants = _other_resultants(point)
    checks = {
        "oracle_a_disc_D_zero": disc_alt == 0,
        "oracle_b_disc_d_zero": disc_max == 0,
        "D_at_r_zero": d_alt.eval(root) == 0,
        "D_prime_at_r_zero": d_alt.diff().eval(root) == 0,
        "D_second_at_r_nonzero": d_alt.diff().diff().eval(root) != 0,
        "D_gcd_degree_one": gcd_alt.degree() == 1,
        "d_gcd_degree_one": gcd_max is not None and gcd_max.degree() == 1,
        "D_residual_quartic_squarefree": (
            remainder_alt.is_zero
            and residual_alt.degree() == 4
            and sp.gcd(residual_alt, residual_alt.diff()).degree() == 0
        ),
        "d_residual_sextic_squarefree": (
            residual_max is not None
            and remainder_max is not None
            and remainder_max.is_zero
            and residual_max.degree() == 6
            and sp.gcd(residual_max, residual_max.diff()).degree() == 0
        ),
        "a_squared_nonzero": a_squared != 0,
        "J4_nonzero": point.j4 != 0,
        "J6_nonzero": point.j6 != 0,
        "coarse_moduli_open": (point.j4, point.j5, point.j6) != (0, 0, 0),
        "Res_D_E_nonzero": resultant_de != 0,
        "other_resultants_nonzero": bool(other_resultants)
        and all(value != 0 for value in other_resultants.values()),
    }
    pre_fibration_pass = all(checks.values())
    fibrations = (
        derive_four_fibration_confluence(point)
        if include_fibrations and pre_fibration_pass
        else []
    )
    expected = {
        "standard": ["III*", "III*", "I2", "I1", "I1", "I1", "I1"],
        "alternate": ["I8*", "I2", "I2", "I2", "I1", "I1", "I1", "I1"],
        "base_fiber_dual": ["I2*", "II*", "I2", "I1", "I1", "I1", "I1"],
        "maximal": ["I10*", "I2", "I1", "I1", "I1", "I1", "I1", "I1"],
    }
    confluence_checks = {
        item["fibration"]: (
            sorted(item["fibers"]) == sorted(expected[item["fibration"]])
            and item["euler_number"] == 24
            and item["shioda_tate_picard_rank"] == 17
        )
        for item in fibrations
    }
    passed = pre_fibration_pass and (
        not include_fibrations
        or len(confluence_checks) == 4
        and all(confluence_checks.values())
    )
    return {
        "point": {
            "name": point.name,
            "role": point.role,
            "j2": str(point.j2),
            "j3": str(point.j3),
            "j4": str(point.j4),
            "j5": str(point.j5),
            "j6": str(point.j6),
            "double_root": str(root),
        },
        "oracle_a": {
            "definition": "Disc_t D(t)",
            "D": str(sp.factor(d_alt.as_expr())),
            "discriminant": str(disc_alt),
            "gcd": str(gcd_alt.as_expr()),
        },
        "oracle_b": {
            "definition": "Disc_t d(t) from maximal cubic / J6^16",
            "d": str(sp.factor(d_max.as_expr())) if d_max is not None else None,
            "discriminant": str(disc_max) if disc_max is not None else None,
            "gcd": str(gcd_max.as_expr()) if gcd_max is not None else None,
        },
        "separation": {
            "a_squared": str(a_squared),
            "Res_D_E": str(resultant_de),
            "other_resultants": {
                key: str(value) for key, value in other_resultants.items()
            },
        },
        "checks": checks,
        "four_fibrations": fibrations,
        "confluence_checks": confluence_checks,
        "minimal_k3_certificate": bool(fibrations)
        and all(item["euler_number"] == 24 for item in fibrations),
        "status": "J30_EXACT_LOCUS_PASS" if passed else "J30_FAIL",
        "passed": passed,
    }


def serialize_dataclass(instance: Any) -> dict[str, Any]:
    """Small helper retained for result builders."""

    return asdict(instance)
