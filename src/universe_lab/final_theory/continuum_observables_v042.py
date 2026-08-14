"""Relational continuum observables for the bounded Phase-B preflight.

The functions in this module are measurement primitives.  They neither sample
new histories nor issue a continuum or dimension verdict.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Sequence
from fractions import Fraction
from typing import Any

import numpy as np

from universe_lab.final_theory.causal_sets import (
    Relation,
    comparable_pairs,
    has_relation,
    validate_relation,
)


def ordering_fraction(relation: Relation) -> Fraction | None:
    """Return the comparable-pair fraction, undefined below cardinality two."""

    n = len(relation)
    if n < 2:
        return None
    return Fraction(comparable_pairs(relation), n * (n - 1) // 2)


def minkowski_ordering_fraction(dimension: float) -> float:
    """Return the preregistered ordering-fraction calibration curve."""

    if dimension <= 0:
        raise ValueError("dimension must be positive")
    return (
        math.gamma(dimension + 1.0)
        * math.gamma(dimension / 2.0)
        / (2.0 * math.gamma(3.0 * dimension / 2.0))
    )


def ordering_fraction_dimension(
    value: Fraction | float | None,
    *,
    lower: float = 1.0,
    upper: float = 6.0,
    tolerance: float = 1e-8,
) -> float | None:
    """Invert the calibration curve by deterministic bisection."""

    if value is None:
        return None
    if not 0 < lower < upper or tolerance <= 0:
        raise ValueError("invalid inversion interval or tolerance")
    observed = float(value)
    lower_value = minkowski_ordering_fraction(lower)
    upper_value = minkowski_ordering_fraction(upper)
    if not upper_value < observed < lower_value:
        return None
    while upper - lower > tolerance:
        middle = (lower + upper) / 2.0
        if minkowski_ordering_fraction(middle) > observed:
            lower = middle
        else:
            upper = middle
    return (lower + upper) / 2.0


def _log_log_slope(x_values: Sequence[float], y_values: Sequence[float]) -> float:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        raise ValueError("at least two paired values are required")
    if any(value <= 0 for value in (*x_values, *y_values)):
        raise ValueError("log-log inputs must be positive")
    x_logs = [math.log(value) for value in x_values]
    y_logs = [math.log(value) for value in y_values]
    x_mean = sum(x_logs) / len(x_logs)
    y_mean = sum(y_logs) / len(y_logs)
    denominator = sum((value - x_mean) ** 2 for value in x_logs)
    if denominator == 0:
        raise ValueError("x values must not all coincide")
    return sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x_logs, y_logs, strict=True)
    ) / denominator


def height_scaling_dimension(
    sizes: Sequence[float], expected_heights: Sequence[float]
) -> float | None:
    """Fit log(H)=a+(1/d_H)log(n) and return d_H."""

    slope = _log_log_slope(sizes, expected_heights)
    return None if slope <= 0 else 1.0 / slope


def spectral_dimension_from_curve(
    steps: Sequence[float], return_probabilities: Sequence[float]
) -> float | None:
    """Fit P_return(s) proportional to s^(-d_s/2)."""

    slope = _log_log_slope(steps, return_probabilities)
    dimension = -2.0 * slope
    return None if dimension <= 0 else dimension


def cover_edges(relation: Relation) -> tuple[tuple[int, int], ...]:
    """Return directed Hasse-cover edges."""

    n = len(relation)
    return tuple(
        (lower, upper)
        for lower in range(n)
        for upper in range(n)
        if has_relation(relation, lower, upper)
        and not any(
            has_relation(relation, lower, middle)
            and has_relation(relation, middle, upper)
            for middle in range(n)
        )
    )


def symmetrized_hasse_adjacency(relation: Relation) -> tuple[tuple[int, ...], ...]:
    """Return deterministic undirected adjacency from cover relations."""

    adjacency = [set() for _ in relation]
    for lower, upper in cover_edges(relation):
        adjacency[lower].add(upper)
        adjacency[upper].add(lower)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency)


def _connected_components(relation: Relation) -> tuple[tuple[int, ...], ...]:
    adjacency = symmetrized_hasse_adjacency(relation)
    unseen = set(range(len(relation)))
    components: list[tuple[int, ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        members: list[int] = []
        while queue:
            vertex = queue.popleft()
            members.append(vertex)
            for neighbor in adjacency[vertex]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(tuple(sorted(members)))
    return tuple(sorted(components, key=lambda item: (-len(item), item)))


def connected_component_sizes(relation: Relation) -> tuple[int, ...]:
    """Return symmetrized-Hasse component sizes in descending order."""

    return tuple(len(component) for component in _connected_components(relation))


def lazy_transition_matrix(relation: Relation) -> tuple[tuple[Fraction, ...], ...]:
    """Build the exact lazy walk matrix with absorbing isolated vertices."""

    adjacency = symmetrized_hasse_adjacency(relation)
    n = len(relation)
    rows: list[tuple[Fraction, ...]] = []
    for vertex, neighbors in enumerate(adjacency):
        row = [Fraction(0) for _ in range(n)]
        if not neighbors:
            row[vertex] = Fraction(1)
        else:
            row[vertex] = Fraction(1, 2)
            step = Fraction(1, 2 * len(neighbors))
            for neighbor in neighbors:
                row[neighbor] = step
        rows.append(tuple(row))
    return tuple(rows)


def _matrix_product(
    left: tuple[tuple[Fraction, ...], ...],
    right: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    n = len(left)
    if any(len(row) != n for row in (*left, *right)) or len(right) != n:
        raise ValueError("matrices must be square and have equal size")
    return tuple(
        tuple(
            sum(
                (left[row][inner] * right[inner][column] for inner in range(n)),
                start=Fraction(0),
            )
            for column in range(n)
        )
        for row in range(n)
    )


def spectral_return_curve(relation: Relation, max_steps: int) -> dict[str, Any]:
    """Return exact uniform-start lazy-walk return probabilities."""

    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    n = len(relation)
    if n == 0:
        return {
            "steps": [],
            "return_probabilities": [],
            "component_sizes": [],
            "defined": False,
        }
    transition = lazy_transition_matrix(relation)
    power = transition
    returns: list[Fraction] = []
    for _step in range(1, max_steps + 1):
        returns.append(sum((power[i][i] for i in range(n)), start=Fraction(0)) / n)
        power = _matrix_product(power, transition)
    return {
        "steps": list(range(1, max_steps + 1)),
        "return_probabilities": returns,
        "component_sizes": list(connected_component_sizes(relation)),
        "defined": True,
    }


def _all_pairs_graph_distances(
    adjacency: tuple[tuple[int, ...], ...],
) -> tuple[tuple[int | None, ...], ...]:
    rows: list[tuple[int | None, ...]] = []
    for source in range(len(adjacency)):
        distances: list[int | None] = [None] * len(adjacency)
        distances[source] = 0
        queue = deque([source])
        while queue:
            vertex = queue.popleft()
            current = distances[vertex]
            if current is None:
                raise AssertionError("queued graph vertex must have a distance")
            for neighbor in adjacency[vertex]:
                if distances[neighbor] is None:
                    distances[neighbor] = current + 1
                    queue.append(neighbor)
        rows.append(tuple(distances))
    return tuple(rows)


def correlation_length_record(relation: Relation) -> dict[str, Any]:
    """Evaluate the preregistered lazy-walk spectral-gap length proxy."""

    n = len(relation)
    if n == 0:
        return {
            "defined": False,
            "reason": "empty_graph",
            "component_sizes": [],
            "component_records": [],
            "nontrivial_vertex_coverage": 0.0,
            "graph_diameter": 0,
            "xi_squared": None,
            "xi": None,
            "xi_over_diameter": None,
        }
    adjacency = symmetrized_hasse_adjacency(relation)
    distances = _all_pairs_graph_distances(adjacency)
    components = _connected_components(relation)
    component_records: list[dict[str, Any]] = []
    weighted_xi_squared = 0.0
    nontrivial_vertices = 0
    for component in components:
        size = len(component)
        if size == 1:
            component_records.append(
                {
                    "size": 1,
                    "defined": False,
                    "reason": "isolated_vertex",
                    "lambda_2": None,
                    "spectral_gap": None,
                    "xi_squared": None,
                }
            )
            continue
        index = {vertex: offset for offset, vertex in enumerate(component)}
        normalized = np.zeros((size, size), dtype=float)
        for vertex in component:
            degree = len(adjacency[vertex])
            if degree == 0:
                raise AssertionError("nontrivial component cannot contain degree zero")
            for neighbor in adjacency[vertex]:
                normalized[index[vertex], index[neighbor]] = 1.0 / math.sqrt(
                    degree * len(adjacency[neighbor])
                )
        lazy_symmetric = 0.5 * (np.eye(size) + normalized)
        eigenvalues = np.linalg.eigvalsh(lazy_symmetric)
        lambda_2 = float(eigenvalues[-2])
        gap = 1.0 - lambda_2
        if gap <= 1e-12:
            component_records.append(
                {
                    "size": size,
                    "defined": False,
                    "reason": "non_positive_spectral_gap",
                    "lambda_2": lambda_2,
                    "spectral_gap": gap,
                    "xi_squared": None,
                }
            )
            continue
        xi_squared = 1.0 / gap
        nontrivial_vertices += size
        weighted_xi_squared += size * xi_squared
        component_records.append(
            {
                "size": size,
                "defined": True,
                "reason": None,
                "lambda_2": lambda_2,
                "spectral_gap": gap,
                "xi_squared": xi_squared,
            }
        )
    diameter = max(
        (
            distance
            for row in distances
            for distance in row
            if distance is not None
        ),
        default=0,
    )
    base = {
        "component_sizes": [len(component) for component in components],
        "component_records": component_records,
        "nontrivial_vertex_coverage": nontrivial_vertices / n,
        "graph_diameter": diameter,
        "xi_squared": None,
        "xi": None,
        "xi_over_diameter": None,
    }
    if nontrivial_vertices == 0:
        return {
            **base,
            "defined": False,
            "reason": "no_nontrivial_connected_component",
        }
    xi_squared = weighted_xi_squared / nontrivial_vertices
    xi = math.sqrt(xi_squared)
    return {
        **base,
        "defined": True,
        "reason": None,
        "xi_squared": xi_squared,
        "xi": xi,
        "xi_over_diameter": xi / diameter if diameter else None,
    }


def relabel_relation(relation: Relation, permutation: Sequence[int]) -> Relation:
    """Relabel a relation where permutation maps old vertices to new vertices."""

    n = len(relation)
    if sorted(permutation) != list(range(n)):
        raise ValueError("permutation must be a bijection of the vertex set")
    rows = [0] * n
    for old_lower in range(n):
        for old_upper in range(n):
            if has_relation(relation, old_lower, old_upper):
                rows[permutation[old_lower]] |= 1 << permutation[old_upper]
    relabeled = tuple(rows)
    errors = validate_relation(relabeled)
    if errors:
        raise AssertionError("relabeling produced an invalid relation")
    return relabeled
