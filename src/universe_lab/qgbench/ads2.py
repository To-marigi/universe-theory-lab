"""AdS(1+1) 因果集合上の遅延スカラー伝播関数。

式番号は Kastrati & Hinrichsen, arXiv:2504.12919v1 に対応する。
この実装は論文のソースコードを流用せず、記載式から独立に構成している。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import solve_triangular
from scipy.special import eval_legendre

from universe_lab.qgbench.causal import validate_causal_matrix


@dataclass(frozen=True)
class Sprinkling:
    """固定個数条件付き Poisson sprinkling の標本。"""

    points: NDArray[np.float64]
    curvature_radius: float
    epsilon: float
    volume: float
    density: float
    seed: int


def rhombus_volume(curvature_radius: float, epsilon: float) -> float:
    """論文 Eq. (51) の AdS 菱形領域体積。"""

    if curvature_radius <= 0:
        raise ValueError("curvature_radius must be positive")
    if not 0 < epsilon < np.pi / 2:
        raise ValueError("epsilon must lie in (0, pi/2)")
    return float(-4 * curvature_radius**2 * np.log(np.sin(epsilon)))


def sprinkle_ads2_rhombus(
    count: int,
    *,
    curvature_radius: float = 1.0,
    epsilon: float = 0.2,
    seed: int = 0,
) -> Sprinkling:
    """論文 Eq. (50) により AdS(1+1) の因果菱形へ点を撒く。

    `count` を固定するため、これは Poisson 点過程を点数 N で条件付けた標本である。
    密度は N/V と記録し、点数自体を Poisson 抽出したとは主張しない。
    """

    if count < 2:
        raise ValueError("count must be at least 2")
    volume = rhombus_volume(curvature_radius, epsilon)
    rng = np.random.default_rng(seed)
    z1 = rng.uniform(-1.0, 1.0, count)
    z2 = rng.uniform(-1.0, 1.0, count)
    # sign(0)=0 の測度ゼロ事象も式どおり扱う。
    w = np.sin(epsilon) ** np.abs(z1)
    time = np.sign(z1) * (np.arcsin(w) - epsilon)
    space = np.arctan2(np.sqrt(np.maximum(0.0, 1.0 - w**2)) * z2, w)
    points = np.column_stack((time, space))
    # 自然ラベルにして上三角行列を保証する。同時刻は確率1で生じない。
    points = points[np.argsort(points[:, 0], kind="stable")]
    return Sprinkling(
        points=points,
        curvature_radius=float(curvature_radius),
        epsilon=float(epsilon),
        volume=volume,
        density=float(count / volume),
        seed=seed,
    )


def causal_matrix(points: NDArray[np.float64]) -> NDArray[np.bool_]:
    """共形座標での因果順序（論文 Eq. (9)）を構成する。"""

    coordinates = np.asarray(points, dtype=float)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise ValueError("points must have shape (N, 2)")
    time = coordinates[:, 0]
    space = coordinates[:, 1]
    delta_t = time[None, :] - time[:, None]
    delta_x = np.abs(space[None, :] - space[:, None])
    relation = (delta_t > 0.0) & (delta_x < delta_t)
    validate_causal_matrix(relation)
    return relation


def ads2_invariant_cosine(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
) -> NDArray[np.float64]:
    """cos(tau/L) に等しい AdS 不変量（論文 Eq. (16)）。"""

    x1 = np.asarray(source, dtype=float)
    x2 = np.asarray(target, dtype=float)
    delta_t = x1[..., 0] - x2[..., 0]
    numerator = np.cos(delta_t) - np.sin(x1[..., 1]) * np.sin(x2[..., 1])
    denominator = np.cos(x1[..., 1]) * np.cos(x2[..., 1])
    return numerator / denominator


def ads2_proper_time(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    *,
    curvature_radius: float,
) -> NDArray[np.float64]:
    """時間的に結ばれた点の主値測地固有時を返す。

    不変量が [-1,1] 外なら主値の時間的測地線が定義できないため NaN とする。
    """

    invariant = ads2_invariant_cosine(source, target)
    valid = (invariant >= -1.0) & (invariant <= 1.0)
    return np.where(valid, curvature_radius * np.arccos(np.clip(invariant, -1.0, 1.0)), np.nan)


def continuum_retarded_propagator(
    proper_time: NDArray[np.float64] | float,
    *,
    mass: float,
    curvature_radius: float,
) -> NDArray[np.float64]:
    """AdS(1+1) の連続遅延伝播関数（論文 Eq. (22) の光円錐内部）。"""

    if mass < 0 or curvature_radius <= 0:
        raise ValueError("mass must be non-negative and curvature_radius positive")
    tau = np.asarray(proper_time, dtype=float)
    ell = 0.5 * (np.sqrt(1.0 + 4.0 * curvature_radius**2 * mass**2) - 1.0)
    argument = np.cos(tau / curvature_radius)
    values = 0.5 * eval_legendre(ell, argument)
    return np.where(np.isfinite(tau) & (tau >= 0), values, 0.0)


def discrete_retarded_propagator(
    causal: NDArray[np.bool_],
    *,
    mass: float,
    density: float,
) -> NDArray[np.float64]:
    """論文 Eq. (56) を自然ラベルの因果行列について計算する。

    逆行列を明示的には作らず、三角連立方程式を解く。
    """

    if mass < 0 or density <= 0:
        raise ValueError("mass must be non-negative and density positive")
    relation = np.asarray(causal, dtype=bool)
    validate_causal_matrix(relation)
    if np.any(np.tril(relation)):
        raise ValueError("discrete propagator requires a natural (upper-triangular) labeling")
    adjacency = relation.astype(float)
    coefficient = mass**2 / (2.0 * density)
    right_factor = np.eye(len(adjacency)) + coefficient * adjacency
    # X R = A/2  <=>  R^T X^T = A^T/2
    solution_t = solve_triangular(
        right_factor.T,
        (0.5 * adjacency).T,
        lower=True,
        unit_diagonal=True,
        check_finite=True,
    )
    result = solution_t.T
    result[np.abs(result) < 1e-15] = 0.0
    return result


def propagator_pairs(
    sprinkling: Sprinkling,
    propagator: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """比較可能な因果対について (tau, K) を一次元配列で返す。"""

    relation = causal_matrix(sprinkling.points)
    rows, columns = np.nonzero(relation)
    tau = ads2_proper_time(
        sprinkling.points[rows],
        sprinkling.points[columns],
        curvature_radius=sprinkling.curvature_radius,
    )
    valid = np.isfinite(tau)
    return tau[valid], np.asarray(propagator)[rows[valid], columns[valid]]
