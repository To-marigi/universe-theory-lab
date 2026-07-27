"""Exact heterotic root enumeration and automatic simply-laced classification."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product

import sympy as sp

Root = tuple[Fraction, ...]
WilsonLine = tuple[Fraction, ...]


def _dot(left: Root, right: Root | WilsonLine) -> Fraction:
    return sum((a * b for a, b in zip(left, right, strict=True)), Fraction())


def _vector_subtract(left: Root, right: Root) -> Root:
    return tuple(a - b for a, b in zip(left, right, strict=True))


def _positive(root: Root) -> bool:
    return next(value for value in root if value) > 0


def e8_roots_exact() -> tuple[Root, ...]:
    """Generate E8 roots in an exact orthonormal realization."""

    roots: list[Root] = []
    zero = Fraction()
    for left, right in combinations(range(8), 2):
        for signs in product((-1, 1), repeat=2):
            vector = [zero] * 8
            vector[left], vector[right] = map(Fraction, signs)
            roots.append(tuple(vector))
    half = Fraction(1, 2)
    for half_signs in product((-half, half), repeat=8):
        if sum(value < 0 for value in half_signs) % 2 == 0:
            roots.append(half_signs)
    result = tuple(sorted(set(roots)))
    if len(result) != 240 or any(_dot(root, root) != 2 for root in result):
        raise AssertionError("E8 root construction failed")
    return result


def e8_plus_e8_roots_exact() -> tuple[Root, ...]:
    roots = e8_roots_exact()
    zero = (Fraction(),) * 8
    return tuple((*root, *zero) for root in roots) + tuple(
        (*zero, *root) for root in roots
    )


def d_roots(rank: int) -> tuple[Root, ...]:
    """Generate all roots ``±e_i ±e_j`` of D_rank."""

    if rank < 4:
        raise ValueError("D rank must be at least four")
    roots: list[Root] = []
    for left, right in combinations(range(rank), 2):
        for signs in product((-1, 1), repeat=2):
            vector = [Fraction()] * rank
            vector[left], vector[right] = map(Fraction, signs)
            roots.append(tuple(vector))
    result = tuple(sorted(roots))
    if len(result) != 2 * rank * (rank - 1):
        raise AssertionError("D root construction failed")
    return result


def massless_gauge_roots(
    roots: tuple[Root, ...],
    wilson_lines: tuple[WilsonLine, WilsonLine],
) -> tuple[Root, ...]:
    """Return roots satisfying ``q·A_i ∈ Z`` in the local zero-winding sector.

    This is the exact gauge-root specialization of the Narain mass formula in
    a semiclassical chart. It does not claim that raw Wilson coordinates exist
    globally on the arithmetic quotient.
    """

    if not roots:
        return ()
    dimension = len(roots[0])
    if any(len(line) != dimension for line in wilson_lines):
        raise ValueError("root and Wilson-line dimensions differ")
    return tuple(
        root
        for root in roots
        if all(_dot(root, line).denominator == 1 for line in wilson_lines)
    )


@dataclass(frozen=True, slots=True)
class RootSystemAnalysis:
    components: tuple[str, ...]
    rank: int
    root_count: int
    cartan_matrix: tuple[tuple[int, ...], ...]
    simple_roots: tuple[Root, ...]

    @property
    def algebra_label(self) -> str:
        return " + ".join(self.components)


def _simple_roots(roots: tuple[Root, ...]) -> tuple[Root, ...]:
    positives = tuple(root for root in roots if _positive(root))
    positive_set = set(positives)
    simple = []
    for root in positives:
        decomposable = any(
            _vector_subtract(root, candidate) in positive_set
            for candidate in positives
            if candidate != root
        )
        if not decomposable:
            simple.append(root)
    return tuple(simple)


def _connected_components(cartan: sp.Matrix) -> tuple[tuple[int, ...], ...]:
    unseen = set(range(cartan.rows))
    components = []
    while unseen:
        start = min(unseen)
        stack = [start]
        current: set[int] = set()
        while stack:
            node = stack.pop()
            if node in current:
                continue
            current.add(node)
            unseen.discard(node)
            stack.extend(
                other
                for other in range(cartan.rows)
                if other not in current and cartan[node, other] != 0
            )
        components.append(tuple(sorted(current)))
    return tuple(components)


def _classify_component(cartan: sp.Matrix) -> str:
    rank = cartan.rows
    determinant = int(cartan.det())
    degrees = tuple(
        sum(cartan[row, column] != 0 for column in range(rank) if row != column)
        for row in range(rank)
    )
    if rank == 1 and determinant == 2:
        return "A1"
    if max(degrees, default=0) <= 2 and determinant == rank + 1:
        return f"A{rank}"
    if rank >= 4 and degrees.count(3) == 1 and determinant == 4:
        return f"D{rank}"
    exceptional = {(6, 3): "E6", (7, 2): "E7", (8, 1): "E8"}
    if (rank, determinant) in exceptional:
        return exceptional[(rank, determinant)]
    return f"UNCLASSIFIED(rank={rank},det={determinant})"


def derive_root_system(roots: tuple[Root, ...]) -> RootSystemAnalysis:
    """Derive simple roots, the Cartan matrix, and Dynkin components."""

    if not roots:
        return RootSystemAnalysis((), 0, 0, (), ())
    simple = _simple_roots(roots)
    cartan = sp.Matrix([[_dot(left, right) for right in simple] for left in simple])
    if any(cartan[index, index] != 2 for index in range(cartan.rows)):
        raise ValueError("only simply-laced length-two root systems are supported")
    components = []
    for indices in _connected_components(cartan):
        block = cartan.extract(indices, indices)
        components.append(_classify_component(block))
    labels = tuple(sorted(components, key=lambda item: (item[0], int(item[1:]))))
    return RootSystemAnalysis(
        labels,
        len(simple),
        len(roots),
        tuple(tuple(int(value) for value in cartan.row(index)) for index in range(cartan.rows)),
        simple,
    )


@dataclass(frozen=True, slots=True)
class WilsonRepresentative:
    gauge_lattice: str
    wilson_line_1: WilsonLine
    wilson_line_2: WilsonLine
    analysis: RootSystemAnalysis
    search_certificate: str
    orbit_key: str

    def to_dict(self) -> dict[str, object]:
        def encode(line: WilsonLine) -> list[str]:
            return [
                str(value.numerator)
                if value.denominator == 1
                else f"{value.numerator}/{value.denominator}"
                for value in line
            ]

        return {
            "gauge_lattice": self.gauge_lattice,
            "wilson_line_1": encode(self.wilson_line_1),
            "wilson_line_2": encode(self.wilson_line_2),
            "search_certificate": self.search_certificate,
            "orbit_key": self.orbit_key,
            "derived_root_system": list(self.analysis.components),
            "derived_root_count": self.analysis.root_count,
            "derived_cartan_matrix": [list(row) for row in self.analysis.cartan_matrix],
        }


def _e8x_e8_candidates(denominator: int) -> tuple[tuple[str, WilsonLine, WilsonLine], ...]:
    zero8 = (Fraction(),) * 8
    third = Fraction(1, denominator)
    diagonal = (third,) * 8
    axis_one = (Fraction(),) * 6 + (third, Fraction())
    axis_two = (Fraction(),) * 7 + (third,)
    block_modes = {
        "zero": (zero8, zero8),
        "diagonal": (diagonal, zero8),
        "two_axis": (axis_one, axis_two),
    }
    candidates = []
    for left_name, left in block_modes.items():
        for right_name, right in block_modes.items():
            if (right_name, left_name) < (left_name, right_name):
                continue
            line_one = (*left[0], *right[0])
            line_two = (*left[1], *right[1])
            key = f"E8blocks:{left_name}+{right_name}:denominator={denominator}"
            candidates.append((key, line_one, line_two))
    return tuple(candidates)


def _d16_candidates(denominator: int) -> tuple[tuple[str, WilsonLine, WilsonLine], ...]:
    value = Fraction(1, denominator)
    candidates = []
    for zero_count in range(1, 15):
        for first_count in range(1, 16 - zero_count):
            second_count = 16 - zero_count - first_count
            if first_count > second_count:
                continue
            labels = (
                *((Fraction(), Fraction()),) * zero_count,
                *((value, Fraction()),) * first_count,
                *((Fraction(), value),) * second_count,
            )
            line_one = tuple(item[0] for item in labels)
            line_two = tuple(item[1] for item in labels)
            key = (
                f"D16-color-partition:{zero_count}+{first_count}+{second_count}:"
                f"denominator={denominator}"
            )
            candidates.append((key, line_one, line_two))
    return tuple(candidates)


def discover_wilson_representative(
    gauge_lattice: str,
    target_components: tuple[str, ...],
    *,
    denominator_bound: int = 3,
) -> WilsonRepresentative:
    """Search a bounded rational template space and return the first Dynkin match."""

    if denominator_bound < 3:
        raise ValueError("denominator_bound must be at least three")
    normalized_target = tuple(
        sorted(target_components, key=lambda item: (item[0], int(item[1:])))
    )
    for denominator in range(3, denominator_bound + 1):
        if gauge_lattice == "E8xE8":
            roots = e8_plus_e8_roots_exact()
            candidates = _e8x_e8_candidates(denominator)
        elif gauge_lattice == "Spin32_Z2":
            roots = d_roots(16)
            candidates = _d16_candidates(denominator)
        else:
            raise ValueError("unsupported gauge lattice")
        for key, first, second in candidates:
            surviving = massless_gauge_roots(roots, (first, second))
            analysis = derive_root_system(surviving)
            if analysis.components == normalized_target:
                return WilsonRepresentative(
                    gauge_lattice,
                    first,
                    second,
                    analysis,
                    (
                        "bounded rational search; candidates are classified from the "
                        "enumerated massless roots, not selected by root count alone"
                    ),
                    key,
                )
    raise LookupError(
        f"no representative found for {gauge_lattice} -> {normalized_target} "
        f"with denominator <= {denominator_bound}"
    )
