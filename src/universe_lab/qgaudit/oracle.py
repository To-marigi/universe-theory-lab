"""An independent numerical oracle for the AdS2 causal-set benchmark.

The formulas are independently transcribed from Kastrati--Hinrichsen,
arXiv:2504.12919v1.  In particular, the continuum kernel is evaluated through
the hypergeometric representation of ``P_nu`` rather than the production
implementation's Legendre evaluator.  No module under ``universe_lab.qgbench``
is imported here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import solve_triangular
from scipy.special import hyp2f1


@dataclass(frozen=True)
class OracleSprinkling:
    """A fixed-cardinality sample from the AdS2 volume measure."""

    points: NDArray[np.float64]
    radius: float
    epsilon: float
    volume: float
    density: float
    seed: int


def diamond_volume(radius: float, epsilon: float) -> float:
    """Invariant volume of the regulated causal diamond (paper Eq. 51)."""

    if radius <= 0:
        raise ValueError("radius must be positive")
    if not 0 < epsilon < np.pi / 2:
        raise ValueError("epsilon must lie in (0, pi/2)")
    return float(-4.0 * radius**2 * np.log(np.sin(epsilon)))


def sprinkle(
    count: int,
    *,
    radius: float = 1.0,
    epsilon: float = 0.25,
    seed: int = 0,
) -> OracleSprinkling:
    """Sample the diamond by inverse CDF and condition on exactly ``count``.

    For ``A = pi/2 - epsilon``, the time marginal is proportional to
    ``tan(A-|t|)``.  Conditional on time, ``tan(x)`` is uniform on its allowed
    interval because the conformal volume density is ``sec(x)^2``.
    """

    if count < 2:
        raise ValueError("count must be at least two")
    rng = np.random.default_rng(seed)
    signed_uniform = rng.uniform(-1.0, 1.0, count)
    conditional_uniform = rng.uniform(-1.0, 1.0, count)
    sine_epsilon = np.sin(epsilon)
    transformed = sine_epsilon ** np.abs(signed_uniform)
    absolute_time = np.arcsin(transformed) - epsilon
    time = np.sign(signed_uniform) * absolute_time
    spatial_limit_tangent = np.sqrt(np.maximum(0.0, 1.0 - transformed**2)) / transformed
    space = np.arctan(conditional_uniform * spatial_limit_tangent)
    points = np.column_stack((time, space))
    points = points[np.argsort(points[:, 0], kind="stable")]
    volume = diamond_volume(radius, epsilon)
    return OracleSprinkling(
        points=points,
        radius=float(radius),
        epsilon=float(epsilon),
        volume=volume,
        density=float(count / volume),
        seed=seed,
    )


def causal_relation(points: NDArray[np.float64]) -> NDArray[np.bool_]:
    """Strict conformal causal order, independently constructed."""

    coordinates = np.asarray(points, dtype=float)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise ValueError("points must have shape (N, 2)")
    delta_time = coordinates[None, :, 0] - coordinates[:, None, 0]
    delta_space = np.abs(coordinates[None, :, 1] - coordinates[:, None, 1])
    return (delta_time > 0.0) & (delta_space < delta_time)


def invariant_cosine(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Return the AdS embedding invariant equal to cos(tau/L), paper Eq. 16."""

    first = np.asarray(source, dtype=float)
    second = np.asarray(target, dtype=float)
    numerator = np.cos(first[..., 0] - second[..., 0])
    numerator -= np.sin(first[..., 1]) * np.sin(second[..., 1])
    denominator = np.cos(first[..., 1]) * np.cos(second[..., 1])
    return numerator / denominator


def proper_time(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    *,
    radius: float,
) -> NDArray[np.float64]:
    """Principal timelike geodesic interval."""

    invariant = invariant_cosine(source, target)
    valid = np.isfinite(invariant) & (invariant >= -1.0) & (invariant <= 1.0)
    result = radius * np.arccos(np.clip(invariant, -1.0, 1.0))
    return np.where(valid, result, np.nan)


def continuum_kernel(
    tau: NDArray[np.float64] | float,
    *,
    mass: float,
    radius: float,
) -> NDArray[np.float64]:
    """Continuum retarded kernel via ``P_nu = 2F1(-nu,nu+1;1;(1-z)/2)``."""

    if mass < 0 or radius <= 0:
        raise ValueError("mass must be non-negative and radius positive")
    intervals = np.asarray(tau, dtype=float)
    degree = 0.5 * (np.sqrt(1.0 + 4.0 * (radius * mass) ** 2) - 1.0)
    z = np.cos(intervals / radius)
    values = 0.5 * hyp2f1(-degree, degree + 1.0, 1.0, (1.0 - z) / 2.0)
    return np.where(np.isfinite(intervals) & (intervals >= 0.0), values, 0.0)


def _topological_order(relation: NDArray[np.bool_]) -> NDArray[np.int64]:
    """Deterministic Kahn ordering, allowing arbitrary external labels."""

    order_matrix = np.asarray(relation, dtype=bool)
    if order_matrix.ndim != 2 or order_matrix.shape[0] != order_matrix.shape[1]:
        raise ValueError("relation must be square")
    if np.any(np.diag(order_matrix)) or np.any(order_matrix & order_matrix.T):
        raise ValueError("relation is not a strict acyclic order")
    indegree: NDArray[np.int64] = np.asarray(
        np.sum(order_matrix, axis=0, dtype=np.int64),
        dtype=np.int64,
    )
    available = list(np.flatnonzero(indegree == 0))
    ordering: list[int] = []
    while available:
        node = available.pop(0)
        ordering.append(node)
        successors = np.flatnonzero(order_matrix[node])
        indegree[successors] -= 1
        available.extend(int(index) for index in successors if indegree[index] == 0)
        available.sort()
    if len(ordering) != len(order_matrix):
        raise ValueError("relation contains a directed cycle")
    return np.asarray(ordering, dtype=np.int64)


def discrete_kernel(
    relation: NDArray[np.bool_],
    *,
    mass: float,
    density: float,
    jump: float = 0.5,
    mass_coefficient_scale: float = 1.0,
) -> NDArray[np.float64]:
    """Solve the discrete Volterra equation in an independently found order.

    The defining identity is
    ``K (I + m^2 C/(2 rho)) = C/2`` (paper Eq. 56).
    """

    if mass < 0 or density <= 0:
        raise ValueError("mass must be non-negative and density positive")
    relation_array = np.asarray(relation, dtype=bool)
    order = _topological_order(relation_array)
    natural = relation_array[np.ix_(order, order)].astype(float)
    if np.any(np.tril(natural)):
        raise ValueError("topological ordering failed")
    alpha = mass_coefficient_scale * mass**2 / (2.0 * density)
    system = np.eye(len(natural)) + alpha * natural
    natural_result_t = solve_triangular(
        system.T,
        (jump * natural).T,
        lower=True,
        unit_diagonal=True,
        check_finite=True,
    )
    natural_result = natural_result_t.T
    inverse = np.argsort(order)
    result = natural_result[np.ix_(inverse, inverse)]
    result[np.abs(result) < 1e-15] = 0.0
    return result


def causal_pair_values(
    sample: OracleSprinkling,
    kernel: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Extract principal proper times and kernel values for causal pairs."""

    relation = causal_relation(sample.points)
    rows, columns = np.nonzero(relation)
    intervals = proper_time(
        sample.points[rows],
        sample.points[columns],
        radius=sample.radius,
    )
    finite = np.isfinite(intervals)
    return intervals[finite], np.asarray(kernel)[rows[finite], columns[finite]]
