"""Convention-explicit symbolic invariants for characteristic-zero Weierstrass models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp


def short_weierstrass_discriminant(f: Any, g: Any) -> sp.Expr:
    """Return the paper's ``4 f^3 + 27 g^2`` discriminant convention.

    The standard algebraic discriminant of ``y^2=x^3+f*x+g`` is minus sixteen
    times this value. Its zero locus and vanishing orders are unchanged.
    """

    return sp.expand(4 * sp.sympify(f) ** 3 + 27 * sp.sympify(g) ** 2)


def short_j_invariant(f: Any, g: Any) -> sp.Expr:
    """Return ``1728*4*f^3/(4*f^3+27*g^2)`` without cancelling by default."""

    f_expr = sp.sympify(f)
    denominator = short_weierstrass_discriminant(f_expr, g)
    return sp.cancel(1728 * 4 * f_expr**3 / denominator)


def cubic_discriminant(a: Any, b: Any, c: Any) -> sp.Expr:
    """Discriminant of ``x^3 + a*x^2 + b*x + c``.

    This is the formula used for the maximal fibration in arXiv:2205.08100,
    Eq. (18), independent of that paper's long coefficient parameterization.
    """

    a_expr, b_expr, c_expr = map(sp.sympify, (a, b, c))
    return sp.expand(
        b_expr**2 * (a_expr**2 - 4 * b_expr)
        - 2 * a_expr * c_expr * (2 * a_expr**2 - 9 * b_expr)
        - 27 * c_expr**2
    )


def two_torsion_discriminant(a: Any, b: Any) -> sp.Expr:
    """Discriminant convention for ``y^2=x*(x^2+a*x+b)``."""

    a_expr, b_expr = map(sp.sympify, (a, b))
    return sp.expand(b_expr**2 * (a_expr**2 - 4 * b_expr))


@dataclass(frozen=True, slots=True)
class ScalingCheck:
    equivalent: bool
    f_residual: sp.Expr
    g_residual: sp.Expr


def check_short_weierstrass_scaling(
    f_source: Any,
    g_source: Any,
    f_target: Any,
    g_target: Any,
    scale: Any,
) -> ScalingCheck:
    """Check the declared coordinate scaling ``f' = s^4 f, g' = s^6 g``."""

    scale_expr = sp.sympify(scale)
    f_residual = sp.simplify(sp.sympify(f_target) - scale_expr**4 * sp.sympify(f_source))
    g_residual = sp.simplify(sp.sympify(g_target) - scale_expr**6 * sp.sympify(g_source))
    return ScalingCheck(f_residual == 0 and g_residual == 0, f_residual, g_residual)
