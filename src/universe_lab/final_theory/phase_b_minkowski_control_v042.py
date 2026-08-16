"""Fixed-cardinality four-dimensional Minkowski sprinkling control.

The target dimension is intentionally an input here because this is a positive
pipeline control.  The generated relation is never candidate evidence.  Two
independent coordinate/relation implementations share only the frozen counter
stream wire format and are compared by relation digest.
"""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from typing import Literal

from universe_lab.final_theory.causal_sets import Relation, validate_relation
from universe_lab.final_theory.continuum_observables_v042 import (
    minkowski_ordering_fraction,
    ordering_fraction,
)
from universe_lab.final_theory.phase_b_control_sampler_v042 import relation_digest

MINKOWSKI_DIMENSION = 4
MAX_N = 60
PointImplementation = Literal["primary", "independent"]
_STREAM_DOMAIN = b"universe-lab/v0.4.2/phase-b-minkowski-control\0"
_REPLAY_STREAM_DOMAIN = _STREAM_DOMAIN
_UINT64_SCALE = float(1 << 64)


@dataclass(frozen=True)
class Point4D:
    time: float
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class SprinklingControl:
    target_n: int
    sampling_seed: int
    trajectory_index: int
    target_dimension: int
    implementation: PointImplementation
    points: tuple[Point4D, ...]
    relation: Relation

    @property
    def relation_digest(self) -> str:
        return relation_digest(self.relation)

    @property
    def candidate_evidence(self) -> bool:
        return False


def _uniform_primary(
    *, sampling_seed: int, trajectory_index: int, point_index: int, component: int
) -> float:
    coordinates = b"".join(
        (
            struct.pack(">Q", sampling_seed),
            struct.pack(">Q", trajectory_index),
            struct.pack(">Q", point_index),
            struct.pack(">Q", component),
            struct.pack(">Q", 0),
        )
    )
    raw = hashlib.sha256(_STREAM_DOMAIN + coordinates).digest()[:8]
    return (int.from_bytes(raw, "big") + 0.5) / _UINT64_SCALE


def _uniform_independent(
    *, sampling_seed: int, trajectory_index: int, point_index: int, component: int
) -> float:
    coordinates = b"".join(
        (
            struct.pack(">Q", sampling_seed),
            struct.pack(">Q", trajectory_index),
            struct.pack(">Q", point_index),
            struct.pack(">Q", component),
            struct.pack(">Q", 0),
        )
    )
    raw = hashlib.sha256(_REPLAY_STREAM_DOMAIN + coordinates).digest()[:8]
    return (int.from_bytes(raw, "big") + 0.5) / _UINT64_SCALE


def _point_from_uniforms(uniforms: tuple[float, ...]) -> Point4D:
    side = uniforms[0] < 0.5
    half_time = 0.5 * uniforms[1] ** 0.25
    time = half_time if side else 1.0 - half_time
    spatial_radius = min(time, 1.0 - time) * uniforms[2] ** (1.0 / 3.0)
    cos_theta = 2.0 * uniforms[3] - 1.0
    sin_theta = math.sqrt(max(0.0, 1.0 - cos_theta * cos_theta))
    phi = 2.0 * math.pi * uniforms[4]
    return Point4D(
        time=time,
        x=spatial_radius * sin_theta * math.cos(phi),
        y=spatial_radius * sin_theta * math.sin(phi),
        z=spatial_radius * cos_theta,
    )


def _generate_points(
    target_n: int, *, sampling_seed: int, trajectory_index: int, implementation: PointImplementation
) -> tuple[Point4D, ...]:
    uniform = _uniform_primary if implementation == "primary" else _uniform_independent
    points = tuple(
        _point_from_uniforms(
            tuple(
                uniform(
                    sampling_seed=sampling_seed,
                    trajectory_index=trajectory_index,
                    point_index=point_index,
                    component=component,
                )
                for component in range(5)
            )
        )
        for point_index in range(target_n)
    )
    return tuple(
        point
        for _original_index, point in sorted(
            enumerate(points), key=lambda item: (item[1].time, item[0])
        )
    )


def _causal_rows_primary(points: tuple[Point4D, ...]) -> Relation:
    rows = [0] * len(points)
    for lower, first in enumerate(points):
        for upper in range(lower + 1, len(points)):
            second = points[upper]
            delta_time = second.time - first.time
            spatial_distance = (
                (second.x - first.x) ** 2
                + (second.y - first.y) ** 2
                + (second.z - first.z) ** 2
            )
            if spatial_distance <= delta_time * delta_time + 1e-14:
                rows[lower] |= 1 << upper
    return _transitive_closure_primary(tuple(rows))


def _causal_rows_independent(points: tuple[Point4D, ...]) -> Relation:
    rows = [0 for _ in points]
    for upper, later in enumerate(points):
        for lower in range(upper):
            earlier = points[lower]
            dt = later.time - earlier.time
            dx = later.x - earlier.x
            dy = later.y - earlier.y
            dz = later.z - earlier.z
            interval = math.fsum((dx * dx, dy * dy, dz * dz))
            if interval <= math.fsum((dt * dt, 1e-14)):
                rows[lower] = rows[lower] | (1 << upper)
    return _transitive_closure_independent(tuple(rows))


def _transitive_closure_primary(rows: Relation) -> Relation:
    closed = list(rows)
    for middle in range(len(rows)):
        middle_bit = 1 << middle
        for lower in range(middle):
            if closed[lower] & middle_bit:
                closed[lower] |= closed[middle]
    return tuple(closed)


def _transitive_closure_independent(rows: Relation) -> Relation:
    result = list(rows)
    for upper in range(len(rows) - 1, -1, -1):
        bit = 1 << upper
        ancestors = [index for index in range(upper) if result[index] & bit]
        for ancestor in ancestors:
            result[ancestor] |= result[upper]
    return tuple(result)


def sprinkle_4d_control(
    target_n: int,
    *,
    sampling_seed: int,
    trajectory_index: int,
    implementation: PointImplementation = "primary",
) -> SprinklingControl:
    """Generate one fixed-cardinality 4D control relation."""

    if type(target_n) is not int or not 1 <= target_n <= MAX_N:
        raise ValueError(f"target_n must be in [1, {MAX_N}]")
    if type(sampling_seed) is not int or not 0 <= sampling_seed < 1 << 64:
        raise ValueError("sampling_seed must be an unsigned 64-bit integer")
    if type(trajectory_index) is not int or not 0 <= trajectory_index < 1 << 64:
        raise ValueError("trajectory_index must be an unsigned 64-bit integer")
    if implementation not in ("primary", "independent"):
        raise ValueError(f"unsupported implementation: {implementation}")
    points = _generate_points(
        target_n,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        implementation=implementation,
    )
    relation = (
        _causal_rows_primary(points)
        if implementation == "primary"
        else _causal_rows_independent(points)
    )
    errors = validate_relation(relation)
    if errors:
        raise AssertionError("Minkowski control relation is invalid: " + "; ".join(errors))
    return SprinklingControl(
        target_n=target_n,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        target_dimension=MINKOWSKI_DIMENSION,
        implementation=implementation,
        points=points,
        relation=relation,
    )


def compare_control_replay(
    target_n: int, *, sampling_seed: int, trajectory_index: int
) -> dict[str, object]:
    primary = sprinkle_4d_control(
        target_n,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        implementation="primary",
    )
    replay = sprinkle_4d_control(
        target_n,
        sampling_seed=sampling_seed,
        trajectory_index=trajectory_index,
        implementation="independent",
    )
    return {
        "target_n": target_n,
        "sampling_seed": sampling_seed,
        "trajectory_index": trajectory_index,
        "target_dimension": MINKOWSKI_DIMENSION,
        "primary_relation_digest": primary.relation_digest,
        "replay_relation_digest": replay.relation_digest,
        "relation_digest_match": primary.relation_digest == replay.relation_digest,
        "points_match": primary.points == replay.points,
        "primary_ordering_fraction": (
            {
                "numerator": ordering.numerator,
                "denominator": ordering.denominator,
            }
            if (ordering := ordering_fraction(primary.relation)) is not None
            else None
        ),
        "candidate_evidence": False,
    }


def independent_anchor_audit() -> dict[str, object]:
    value = minkowski_ordering_fraction(float(MINKOWSKI_DIMENSION))
    return {
        "dimension": MINKOWSKI_DIMENSION,
        "expected_ordering_fraction": 0.1,
        "computed_ordering_fraction": value,
        "absolute_error": abs(value - 0.1),
        "passed": abs(value - 0.1) <= 1e-12,
        "candidate_evidence": False,
    }
