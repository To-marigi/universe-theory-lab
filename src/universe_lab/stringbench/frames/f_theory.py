"""F-theory frontend for paper-supported K3 fibrations.

The formulas are transcribed from arXiv:2205.08100v1, Eqs. (4)--(18). The
frontend does not use expected benchmark answers when deriving invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import sympy as sp

from universe_lab.stringbench.evidence import EvidenceState
from universe_lab.stringbench.invariants.modular import (
    K3ModularInvariants,
    modular_invariants_from_quartic,
)
from universe_lab.stringbench.invariants.weierstrass import (
    cubic_discriminant,
    short_weierstrass_discriminant,
    two_torsion_discriminant,
)


class FibrationKind(StrEnum):
    STANDARD = "standard"
    ALTERNATE = "alternate"
    BASE_FIBER_DUAL = "base_fiber_dual"
    MAXIMAL = "maximal"


@dataclass(frozen=True, slots=True)
class FTheoryInput:
    alpha: Any
    beta: Any
    gamma: Any
    delta: Any
    epsilon: Any
    zeta: Any
    fibration: FibrationKind
    frame_id: str = "f-theory:k3"

    @property
    def coefficients(self) -> tuple[sp.Expr, ...]:
        return tuple(
            map(
                sp.sympify,
                (
                    self.alpha,
                    self.beta,
                    self.gamma,
                    self.delta,
                    self.epsilon,
                    self.zeta,
                ),
            )
        )

    @property
    def modular_invariants(self) -> K3ModularInvariants:
        return modular_invariants_from_quartic(*self.coefficients)

    def domain_violations(self) -> tuple[str, ...]:
        _, _, gamma, delta, epsilon, zeta = self.coefficients
        violations = []
        if gamma.equals(0) is True and delta.equals(0) is True:
            violations.append("(gamma, delta) must not equal (0, 0)")
        if epsilon.equals(0) is True and zeta.equals(0) is True:
            violations.append("(epsilon, zeta) must not equal (0, 0)")
        return tuple(violations)


@dataclass(frozen=True, slots=True)
class FTheoryCompilation:
    fibration: FibrationKind
    status: EvidenceState
    equation_kind: str
    coefficients: dict[str, sp.Expr]
    discriminant: sp.Expr | None
    generic_singular_fibers: tuple[str, ...]
    mordell_weil_rank: int | None
    mordell_weil_torsion: str | None
    lattice_polarization: str
    limitations: tuple[str, ...] = ()


def _standard(data: FTheoryInput, u: sp.Symbol, v: sp.Symbol) -> FTheoryCompilation:
    alpha, beta, gamma, delta, epsilon, zeta = data.coefficients
    f = -4 * u**3 * v**3 * (gamma * u**2 + 3 * alpha * u * v + epsilon * v**2)
    g = 8 * u**5 * v**5 * (delta * u**2 - 2 * beta * u * v + zeta * v**2)
    return FTheoryCompilation(
        data.fibration,
        EvidenceState.EXACT_SYMBOLIC,
        "short_weierstrass",
        {"f": sp.expand(f), "g": sp.expand(g)},
        short_weierstrass_discriminant(f, g),
        ("III*", "III*", *(("I1",) * 6)),
        0,
        "trivial",
        "H + E7(-1) + E7(-1)",
    )


def _alternate(data: FTheoryInput, u: sp.Symbol, v: sp.Symbol) -> FTheoryCompilation:
    alpha, beta, gamma, delta, epsilon, zeta = data.coefficients
    a = 4 * v * (4 * u**3 - 3 * alpha * u * v**2 - beta * v**3)
    b = 4 * v**6 * (2 * gamma * u - delta * v) * (2 * epsilon * u - zeta * v)
    return FTheoryCompilation(
        data.fibration,
        EvidenceState.EXACT_SYMBOLIC,
        "two_torsion_weierstrass",
        {"A": sp.expand(a), "B": sp.expand(b)},
        two_torsion_discriminant(a, b),
        ("I8*", "I2", "I2", *(("I1",) * 6)),
        0,
        "Z/2Z",
        "H + E7(-1) + E7(-1)",
    )


def _base_fiber_dual(
    data: FTheoryInput,
    u: sp.Symbol,
    v: sp.Symbol,
) -> FTheoryCompilation:
    alpha, beta, gamma, delta, epsilon, zeta = data.coefficients
    f = -108 * u**2 * v**4 * (
        9 * alpha * u**2
        - 3 * (gamma * zeta + delta * epsilon) * u * v
        + gamma**2 * epsilon**2 * v**2
    )
    g = -216 * u**3 * v**5 * (
        27 * u**4
        + 54 * beta * u**3 * v
        + 27 * (alpha * gamma * epsilon + delta * zeta) * u**2 * v**2
        - 9 * gamma * epsilon * (gamma * zeta + delta * epsilon) * u * v**3
        + 2 * gamma**3 * epsilon**3 * v**4
    )
    return FTheoryCompilation(
        data.fibration,
        EvidenceState.EXACT_SYMBOLIC,
        "short_weierstrass",
        {"F": sp.expand(f), "G": sp.expand(g)},
        short_weierstrass_discriminant(f, g),
        ("II*", "I2*", *(("I1",) * 6)),
        0,
        "trivial",
        "H + E7(-1) + E7(-1)",
    )


def _maximal(data: FTheoryInput, u: sp.Symbol, v: sp.Symbol) -> FTheoryCompilation:
    alpha, beta, gamma, delta, epsilon, zeta = data.coefficients
    a = -2 * delta * zeta * v * (
        u**3
        - 6 * beta * gamma * epsilon * u**2 * v
        + 3 * (4 * beta**2 * gamma**2 * epsilon**2 - alpha * delta**2 * zeta**2)
        * u
        * v**2
        - 2
        * beta
        * (
            4 * beta**2 * gamma**3 * epsilon**3
            - 3 * alpha * gamma * delta**2 * epsilon * zeta**2
            - delta**3 * zeta**3
        )
        * v**3
    )
    b = -4 * delta**6 * zeta**6 * v**6 * (
        2 * gamma * epsilon * u**2
        - (
            8 * beta * gamma**2 * epsilon**2
            + gamma * delta * zeta**2
            + delta**2 * epsilon * zeta
        )
        * u
        * v
        + (
            8 * beta**2 * gamma**3 * epsilon**3
            - 3 * alpha * gamma * delta**2 * epsilon * zeta**2
            + 2 * beta * gamma**2 * delta * epsilon * zeta**2
            + 2 * beta * gamma * delta**2 * epsilon**2 * zeta
            - delta**3 * zeta**3
        )
        * v**2
    )
    c = -8 * gamma * delta**11 * epsilon * zeta**11 * v**11 * (
        gamma * epsilon * u
        - (
            2 * beta * gamma**2 * epsilon**2
            + gamma * delta * zeta**2
            + delta**2 * epsilon * zeta
        )
        * v
    )
    return FTheoryCompilation(
        data.fibration,
        EvidenceState.EXACT_SYMBOLIC,
        "general_cubic_weierstrass",
        {"a": sp.expand(a), "b": sp.expand(b), "c": sp.expand(c)},
        cubic_discriminant(a, b, c),
        ("I10*", *(("I1",) * 8)),
        0,
        "trivial",
        "H + E7(-1) + E7(-1)",
    )


def compile_f_theory(
    data: FTheoryInput,
    *,
    base_coordinates: tuple[sp.Symbol, sp.Symbol] | None = None,
) -> FTheoryCompilation:
    """Compile a supported presentation, rejecting the source validity exclusions."""

    violations = data.domain_violations()
    if violations:
        return FTheoryCompilation(
            data.fibration,
            EvidenceState.BLOCKED,
            "unavailable",
            {},
            None,
            (),
            None,
            None,
            "H + E7(-1) + E7(-1)",
            violations,
        )
    u, v = base_coordinates or sp.symbols("u v")
    if data.fibration is FibrationKind.STANDARD:
        return _standard(data, u, v)
    if data.fibration is FibrationKind.ALTERNATE:
        return _alternate(data, u, v)
    if data.fibration is FibrationKind.BASE_FIBER_DUAL:
        return _base_fiber_dual(data, u, v)
    if data.fibration is FibrationKind.MAXIMAL:
        return _maximal(data, u, v)
    raise ValueError(f"unsupported fibration: {data.fibration}")
