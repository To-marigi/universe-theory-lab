"""Independent heterotic-frame primitives for a two-torus with two Wilson lines."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations, product
from math import isclose

import numpy as np

from universe_lab.stringbench.evidence import EvidenceState
from universe_lab.stringbench.invariants.lattices import (
    LatticeInvariants,
    analyze_gram_matrix,
    narain_2_18_gram,
)


def e8_roots() -> tuple[tuple[float, ...], ...]:
    """Construct the 240 roots of E8 in the standard orthonormal realization."""

    roots: list[tuple[float, ...]] = []
    for left, right in combinations(range(8), 2):
        for signs in product((-1.0, 1.0), repeat=2):
            vector = [0.0] * 8
            vector[left], vector[right] = signs
            roots.append(tuple(vector))
    for signs in product((-0.5, 0.5), repeat=8):
        minus_count = sum(value < 0 for value in signs)
        if minus_count % 2 == 0:
            roots.append(signs)
    if len(roots) != 240:
        raise AssertionError("internal E8 root construction failed")
    return tuple(roots)


def e8_plus_e8_roots() -> tuple[tuple[float, ...], ...]:
    zero = (0.0,) * 8
    roots = e8_roots()
    return tuple((*root, *zero) for root in roots) + tuple((*zero, *root) for root in roots)


@dataclass(frozen=True, slots=True)
class HeteroticInput:
    complex_structure: complex
    kahler_modulus: complex
    wilson_line_1: tuple[float, ...]
    wilson_line_2: tuple[float, ...]
    gauge_lattice: str = "E8+E8"
    frame_id: str = "heterotic:T2"

    def __post_init__(self) -> None:
        if self.complex_structure.imag <= 0:
            raise ValueError("complex_structure must lie in the upper half-plane")
        if self.kahler_modulus.imag <= 0:
            raise ValueError("kahler_modulus must lie in the upper half-plane")
        if len(self.wilson_line_1) != 16 or len(self.wilson_line_2) != 16:
            raise ValueError("each Wilson line must have 16 gauge-lattice components")
        if self.gauge_lattice != "E8+E8":
            raise NotImplementedError(
                "v0.1 constructs E8+E8 roots; Spin(32)/Z2 is evidence-tagged but not compiled"
            )


@dataclass(frozen=True, slots=True)
class HeteroticCompilation:
    status: EvidenceState
    narain_lattice: LatticeInvariants
    surviving_roots: tuple[tuple[float, ...], ...]
    root_count: int
    gauge_algebra: str | None
    limitations: tuple[str, ...]


def root_survives_wilson_lines(
    root: Iterable[float],
    wilson_lines: Iterable[Iterable[float]],
    *,
    absolute_tolerance: float = 1e-10,
) -> bool:
    """Test the holonomy condition ``root · A_i ∈ Z`` for both torus cycles."""

    root_array = np.asarray(tuple(root), dtype=float)
    for line in wilson_lines:
        phase = float(np.dot(root_array, np.asarray(tuple(line), dtype=float)))
        if not isclose(phase, round(phase), rel_tol=0.0, abs_tol=absolute_tolerance):
            return False
    return True


def compile_heterotic(data: HeteroticInput) -> HeteroticCompilation:
    """Compile the Narain signature and unbroken roots without classifying by answer key."""

    roots = e8_plus_e8_roots()
    surviving = tuple(
        root
        for root in roots
        if root_survives_wilson_lines(
            root,
            (data.wilson_line_1, data.wilson_line_2),
        )
    )
    return HeteroticCompilation(
        EvidenceState.PARTIAL,
        analyze_gram_matrix(narain_2_18_gram()),
        surviving,
        len(surviving),
        None,
        (
            "Narain and root-survival calculations are exact for the supplied vectors, "
            "but this aggregate compilation remains PARTIAL.",
            "The unbroken root set is computed independently, but automatic Dynkin "
            "decomposition and global gauge-group reconstruction are not implemented.",
            "The frontend does not identify raw (tau,rho,A1,A2) coordinates across "
            "O(2,18;Z) orbits.",
        ),
    )
