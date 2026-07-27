"""Resource preflight for dense causal-set calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import psutil


@dataclass(frozen=True)
class ResourceEstimate:
    count: int
    seeds: int
    estimated_peak_bytes: int
    estimated_dense_flops: float
    estimated_seconds: float
    available_memory_bytes: int
    memory_budget_bytes: int
    wall_time_budget_seconds: float
    executable: bool
    reason: str | None


def estimate_resources(
    count: int,
    *,
    seeds: int,
    measured_count: int,
    measured_seconds_per_seed: float,
    memory_fraction: float = 0.25,
    wall_time_budget_seconds: float = 180.0,
) -> ResourceEstimate:
    """Conservative preflight using measured cubic time and dense-array memory."""

    if min(count, seeds, measured_count) <= 0 or measured_seconds_per_seed <= 0:
        raise ValueError("counts, seeds, and measured time must be positive")
    available = int(psutil.virtual_memory().available)
    memory_budget = int(available * memory_fraction)
    # Relation, float work arrays, pair masks/coordinates, and allocator margin.
    peak_bytes = int(72 * count**2)
    dense_flops = float(seeds * count**3 / 3.0)
    estimated_seconds = float(
        seeds * measured_seconds_per_seed * (count / measured_count) ** 3
    )
    reason: str | None = None
    if peak_bytes > memory_budget:
        reason = "estimated peak dense memory exceeds 25% of currently available RAM"
    elif estimated_seconds > wall_time_budget_seconds:
        reason = "measured cubic extrapolation exceeds the per-level audit wall-time budget"
    return ResourceEstimate(
        count=count,
        seeds=seeds,
        estimated_peak_bytes=peak_bytes,
        estimated_dense_flops=dense_flops,
        estimated_seconds=estimated_seconds,
        available_memory_bytes=available,
        memory_budget_bytes=memory_budget,
        wall_time_budget_seconds=wall_time_budget_seconds,
        executable=reason is None,
        reason=reason,
    )


def as_payload(estimate: ResourceEstimate) -> dict[str, object]:
    """JSON-friendly resource estimate."""

    return asdict(estimate)
