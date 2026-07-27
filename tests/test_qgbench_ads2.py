import numpy as np

from universe_lab.qgbench.ads2 import (
    ads2_invariant_cosine,
    causal_matrix,
    continuum_retarded_propagator,
    discrete_retarded_propagator,
    rhombus_volume,
    sprinkle_ads2_rhombus,
)
from universe_lab.qgbench.causal import link_matrix, validate_causal_matrix


def test_sprinkling_is_reproducible_and_inside_rhombus() -> None:
    first = sprinkle_ads2_rhombus(200, curvature_radius=1.7, epsilon=0.2, seed=42)
    second = sprinkle_ads2_rhombus(200, curvature_radius=1.7, epsilon=0.2, seed=42)
    assert np.array_equal(first.points, second.points)
    assert np.all(np.abs(first.points[:, 0]) + np.abs(first.points[:, 1]) < np.pi / 2)
    assert np.isclose(first.volume, rhombus_volume(1.7, 0.2))
    assert np.isclose(first.density, 200 / first.volume)


def test_causal_matrix_is_a_strict_partial_order() -> None:
    sprinkling = sprinkle_ads2_rhombus(120, epsilon=0.25, seed=7)
    relation = causal_matrix(sprinkling.points)
    validate_causal_matrix(relation)
    assert not np.any(np.tril(relation))
    links = link_matrix(relation)
    assert np.all(links <= relation)


def test_massless_propagators_are_half_inside_lightcone() -> None:
    sprinkling = sprinkle_ads2_rhombus(60, epsilon=0.3, seed=9)
    relation = causal_matrix(sprinkling.points)
    discrete = discrete_retarded_propagator(relation, mass=0.0, density=sprinkling.density)
    assert np.array_equal(discrete, 0.5 * relation)
    continuum = continuum_retarded_propagator(
        np.array([0.0, 0.2, 0.8]), mass=0.0, curvature_radius=1.0
    )
    assert np.allclose(continuum, 0.5)


def test_ads_invariant_is_symmetric_and_identity_is_one() -> None:
    points = np.array([[0.1, 0.2], [0.4, -0.1]])
    forward = ads2_invariant_cosine(points[0], points[1])
    backward = ads2_invariant_cosine(points[1], points[0])
    identity = ads2_invariant_cosine(points, points)
    assert np.isclose(forward, backward)
    assert np.allclose(identity, 1.0)


def test_discrete_matrix_satisfies_defining_equation() -> None:
    sprinkling = sprinkle_ads2_rhombus(80, epsilon=0.3, seed=11)
    relation = causal_matrix(sprinkling.points)
    mass = 2.5
    result = discrete_retarded_propagator(
        relation, mass=mass, density=sprinkling.density
    )
    adjacency = relation.astype(float)
    coefficient = mass**2 / (2 * sprinkling.density)
    residual = result @ (np.eye(len(relation)) + coefficient * adjacency) - 0.5 * adjacency
    assert np.max(np.abs(residual)) < 1e-12
