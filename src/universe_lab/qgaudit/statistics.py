"""Statistical summaries and finite-size scaling for the independent audit."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import curve_fit
from scipy.stats import t

from universe_lab.qgaudit.oracle import continuum_kernel


@dataclass(frozen=True)
class Summary:
    count: int
    mean: float
    standard_deviation: float
    ci95_low: float
    ci95_high: float


def summarize(values: NDArray[np.float64] | Sequence[float | int]) -> Summary:
    """Mean, sample standard deviation and a two-sided Student-t 95% CI."""

    data = np.asarray(values, dtype=float)
    if data.ndim != 1 or len(data) < 2 or not np.all(np.isfinite(data)):
        raise ValueError("at least two finite one-dimensional observations are required")
    mean = float(np.mean(data))
    deviation = float(np.std(data, ddof=1))
    half_width = float(t.ppf(0.975, len(data) - 1) * deviation / np.sqrt(len(data)))
    return Summary(len(data), mean, deviation, mean - half_width, mean + half_width)


def binned_rmse(
    tau: NDArray[np.float64],
    observed: NDArray[np.float64],
    *,
    mass: float,
    radius: float,
    bins: int = 18,
    minimum_bin_count: int = 10,
) -> float:
    """RMSE of within-bin sample means against the independent continuum oracle."""

    intervals = np.asarray(tau, dtype=float)
    values = np.asarray(observed, dtype=float)
    valid = np.isfinite(intervals) & np.isfinite(values)
    intervals = intervals[valid]
    values = values[valid]
    if not len(intervals):
        raise ValueError("no finite causal pairs")
    edges = np.linspace(0.0, float(np.max(intervals)), bins + 1)
    bin_index = np.clip(np.digitize(intervals, edges) - 1, 0, bins - 1)
    centers: list[float] = []
    means: list[float] = []
    for index in range(bins):
        selected = bin_index == index
        if int(np.sum(selected)) >= minimum_bin_count:
            centers.append(float(np.mean(intervals[selected])))
            means.append(float(np.mean(values[selected])))
    if len(centers) < 3:
        raise ValueError("too few populated bins")
    expected = continuum_kernel(np.asarray(centers), mass=mass, radius=radius)
    return float(np.sqrt(np.mean((np.asarray(means) - expected) ** 2)))


def _scaling_model(
    count: NDArray[np.float64], a: float, p: float, b: float
) -> NDArray[np.float64]:
    return a * count ** (-p) + b


def finite_size_fit(
    counts: NDArray[np.int64] | list[int],
    seed_rmse: list[list[float]],
    *,
    bootstrap_samples: int = 500,
    seed: int = 90210,
) -> dict[str, object]:
    """Fit ``a N^-p + b`` and bootstrap seed-level uncertainty.

    All seed observations enter the nonlinear least-squares fit. Bootstrap
    resampling is stratified by N, so uncertainty does not pretend that three
    aggregate means are exact observations.
    """

    sizes = np.asarray(counts, dtype=float)
    if len(sizes) < 3 or len(seed_rmse) != len(sizes):
        raise ValueError("at least three sizes with matching observations are required")
    repeated_sizes = np.concatenate(
        [
            np.full(len(observations), size)
            for size, observations in zip(sizes, seed_rmse, strict=True)
        ]
    )
    repeated_rmse = np.concatenate(
        [np.asarray(observations, dtype=float) for observations in seed_rmse]
    )
    initial_b = max(0.0, float(np.min(repeated_rmse)) * 0.5)
    parameters, covariance = curve_fit(
        _scaling_model,
        repeated_sizes,
        repeated_rmse,
        p0=(1.0, 0.5, initial_b),
        bounds=([0.0, 0.0, -1.0], [10.0, 5.0, 1.0]),
        maxfev=50_000,
    )
    standard_errors = np.sqrt(np.maximum(0.0, np.diag(covariance)))
    rng = np.random.default_rng(seed)
    boot_parameters: list[NDArray[np.float64]] = []
    for _ in range(bootstrap_samples):
        resampled = [
            rng.choice(np.asarray(observations, dtype=float), len(observations), replace=True)
            for observations in seed_rmse
        ]
        boot_y = np.concatenate(resampled)
        try:
            candidate, _ = curve_fit(
                _scaling_model,
                repeated_sizes,
                boot_y,
                p0=parameters,
                bounds=([0.0, 0.0, -1.0], [10.0, 5.0, 1.0]),
                maxfev=20_000,
            )
        except (RuntimeError, ValueError):
            continue
        boot_parameters.append(candidate)
    if len(boot_parameters) < bootstrap_samples * 0.8:
        raise RuntimeError("finite-size bootstrap did not converge reliably")
    bootstrap = np.asarray(boot_parameters)
    low = np.percentile(bootstrap, 2.5, axis=0)
    high = np.percentile(bootstrap, 97.5, axis=0)
    names = ("a", "p", "b")
    return {
        "model": "RMSE(N) = a N^(-p) + b",
        "observations": int(len(repeated_rmse)),
        "parameters": {
            name: {
                "estimate": float(parameters[index]),
                "standard_error_asymptotic": float(standard_errors[index]),
                "bootstrap_ci95": [float(low[index]), float(high[index])],
            }
            for index, name in enumerate(names)
        },
        "bootstrap_requested": bootstrap_samples,
        "bootstrap_converged": len(boot_parameters),
        "b_ci_includes_zero": bool(low[2] <= 0.0 <= high[2]),
        "warning": (
            "The finite sampled N range makes p and b weakly identifiable; "
            "bootstrap intervals are primary."
        ),
    }
