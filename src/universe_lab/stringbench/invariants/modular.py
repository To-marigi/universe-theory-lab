"""Modular-form combinations that are invariant under the quartic presentation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp


@dataclass(frozen=True, slots=True)
class K3ModularInvariants:
    """The ``J_2,...,J_6`` coordinates of arXiv:2205.08100, Eq. (25)."""

    j2: sp.Expr
    j3: sp.Expr
    j4: sp.Expr
    j5: sp.Expr
    j6: sp.Expr

    @property
    def automorphic_square(self) -> sp.Expr:
        """Return ``a^2 = J_5^2 - 4 J_4 J_6`` (paper, Eq. preceding (25))."""

        return sp.expand(self.j5**2 - 4 * self.j4 * self.j6)

    def weighted_scale(self, scale: Any) -> K3ModularInvariants:
        """Apply weighted-projective weights ``(2,3,4,5,6)``."""

        scale_expr = sp.sympify(scale)
        return K3ModularInvariants(
            *(
                value * scale_expr**weight
                for value, weight in zip(self.values, self.weights, strict=True)
            )
        )

    @property
    def values(self) -> tuple[sp.Expr, ...]:
        return (self.j2, self.j3, self.j4, self.j5, self.j6)

    @property
    def weights(self) -> tuple[int, ...]:
        return (2, 3, 4, 5, 6)

    @property
    def in_open_moduli_domain(self) -> bool | None:
        """Whether ``(J4,J5,J6) != (0,0,0)``, or ``None`` if symbolic."""

        tests = tuple(value.equals(0) for value in (self.j4, self.j5, self.j6))
        if all(test is True for test in tests):
            return False
        if any(test is False for test in tests):
            return True
        return None


def modular_invariants_from_quartic(
    alpha: Any,
    beta: Any,
    gamma: Any,
    delta: Any,
    epsilon: Any,
    zeta: Any,
) -> K3ModularInvariants:
    """Calculate Eq. (25) directly from the six quartic coefficients."""

    alpha, beta, gamma, delta, epsilon, zeta = map(
        sp.sympify,
        (alpha, beta, gamma, delta, epsilon, zeta),
    )
    return K3ModularInvariants(
        j2=alpha,
        j3=beta,
        j4=gamma * epsilon,
        j5=gamma * zeta + delta * epsilon,
        j6=delta * zeta,
    )
