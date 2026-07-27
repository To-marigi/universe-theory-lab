"""Exact Gram-matrix checks for lattices used in the eight-dimensional duality."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import sympy as sp


@dataclass(frozen=True, slots=True)
class LatticeInvariants:
    rank: int
    signature: tuple[int, int, int]
    determinant: int
    discriminant_order: int
    even: bool
    integral: bool
    unimodular: bool


def analyze_gram_matrix(
    matrix: Sequence[Sequence[Any]],
) -> LatticeInvariants:
    """Compute rank, inertia, determinant, parity, and unimodularity independently."""

    gram = sp.Matrix(matrix)
    if gram.rows != gram.cols:
        raise ValueError("Gram matrix must be square")
    if gram != gram.T:
        raise ValueError("Gram matrix must be symmetric")
    integral = all(value.is_integer is True for value in gram)
    determinant_expr = sp.det(gram)
    if determinant_expr.is_integer is not True:
        raise ValueError("determinant must be integral")
    determinant = int(determinant_expr)
    positive, negative, zero = _exact_inertia(gram)
    even = integral and all(int(gram[index, index]) % 2 == 0 for index in range(gram.rows))
    return LatticeInvariants(
        rank=int(gram.rank()),
        signature=(positive, negative, zero),
        determinant=determinant,
        discriminant_order=abs(determinant),
        even=even,
        integral=integral,
        unimodular=abs(determinant) == 1,
    )


def _exact_inertia(matrix: sp.Matrix) -> tuple[int, int, int]:
    """Compute rational symmetric inertia by exact congruence elimination."""

    work = matrix.applyfunc(sp.Rational)
    positive = negative = zero = 0
    while work.rows:
        diagonal_pivot = next(
            (index for index in range(work.rows) if work[index, index] != 0),
            None,
        )
        if diagonal_pivot is not None:
            work.row_swap(0, diagonal_pivot)
            work.col_swap(0, diagonal_pivot)
            pivot = work[0, 0]
            if pivot > 0:
                positive += 1
            else:
                negative += 1
            column = work[1:, 0]
            work = work[1:, 1:] - column * column.T / pivot
            continue
        off_diagonal = next(
            (
                (row, column)
                for row in range(work.rows)
                for column in range(row + 1, work.cols)
                if work[row, column] != 0
            ),
            None,
        )
        if off_diagonal is None:
            zero += work.rows
            break
        first, second = off_diagonal
        work.row_swap(0, first)
        work.col_swap(0, first)
        if second == 0:
            second = first
        work.row_swap(1, second)
        work.col_swap(1, second)
        pivot_block = work[:2, :2]
        coupling = work[:2, 2:]
        work = work[2:, 2:] - coupling.T * pivot_block.inv() * coupling
        positive += 1
        negative += 1
    return positive, negative, zero


def hyperbolic_plane_gram() -> tuple[tuple[int, int], tuple[int, int]]:
    return ((0, 1), (1, 0))


def cartan_a(rank: int) -> sp.Matrix:
    if rank < 1:
        raise ValueError("rank must be positive")
    matrix = 2 * sp.eye(rank)
    for index in range(rank - 1):
        matrix[index, index + 1] = matrix[index + 1, index] = -1
    return matrix


def cartan_d(rank: int) -> sp.Matrix:
    if rank < 4:
        raise ValueError("D rank must be at least four")
    matrix = 2 * sp.eye(rank)
    for index in range(rank - 3):
        matrix[index, index + 1] = matrix[index + 1, index] = -1
    branch = rank - 3
    matrix[branch, rank - 2] = matrix[rank - 2, branch] = -1
    matrix[branch, rank - 1] = matrix[rank - 1, branch] = -1
    return matrix


def cartan_e7() -> sp.Matrix:
    """Bourbaki-compatible E7 Cartan matrix (determinant two)."""

    matrix = 2 * sp.eye(7)
    edges = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (2, 6))
    for left, right in edges:
        matrix[left, right] = matrix[right, left] = -1
    return matrix


def cartan_e8() -> sp.Matrix:
    """E8 Cartan matrix (determinant one)."""

    matrix = 2 * sp.eye(8)
    edges = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (2, 7))
    for left, right in edges:
        matrix[left, right] = matrix[right, left] = -1
    return matrix


def block_diagonal(*blocks: Sequence[Sequence[Any]] | sp.Matrix) -> sp.Matrix:
    matrices = tuple(sp.Matrix(block) for block in blocks)
    return sp.diag(*matrices)


def n_polarization_gram() -> sp.Matrix:
    """Gram matrix for ``H ⊕ E7(-1) ⊕ E7(-1)``."""

    return block_diagonal(hyperbolic_plane_gram(), -cartan_e7(), -cartan_e7())


def narain_2_18_gram() -> sp.Matrix:
    """Gram matrix for ``H ⊕ H ⊕ E8(-1) ⊕ E8(-1)``."""

    h = hyperbolic_plane_gram()
    return block_diagonal(h, h, -cartan_e8(), -cartan_e8())
