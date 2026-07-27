import ast
from pathlib import Path

import numpy as np

from universe_lab.qgaudit.oracle import (
    causal_relation,
    continuum_kernel,
    diamond_volume,
    discrete_kernel,
    proper_time,
    sprinkle,
)


def test_oracle_has_no_qgbench_import() -> None:
    package = Path(__file__).parents[2] / "src" / "universe_lab" / "qgaudit"
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(name.startswith("universe_lab.qgbench") for name in imported)


def test_massless_and_defining_equation() -> None:
    sample = sprinkle(70, radius=1.2, epsilon=0.3, seed=7)
    relation = causal_relation(sample.points)
    massless = discrete_kernel(relation, mass=0.0, density=sample.density)
    assert np.array_equal(massless, 0.5 * relation)
    mass = 2.3
    massive = discrete_kernel(relation, mass=mass, density=sample.density)
    causal = relation.astype(float)
    residual = massive @ (np.eye(len(relation)) + mass**2 * causal / (2 * sample.density))
    assert np.max(np.abs(residual - 0.5 * causal)) < 1e-12


def test_general_label_equivariance() -> None:
    sample = sprinkle(55, seed=8)
    relation = causal_relation(sample.points)
    original = discrete_kernel(relation, mass=2.0, density=sample.density)
    permutation = np.random.default_rng(9).permutation(len(relation))
    changed = relation[np.ix_(permutation, permutation)]
    changed_result = discrete_kernel(changed, mass=2.0, density=sample.density)
    inverse = np.argsort(permutation)
    assert np.allclose(changed_result[np.ix_(inverse, inverse)], original, atol=1e-13)


def test_independent_continuum_known_limits() -> None:
    tau = np.array([0.0, 0.2, 0.8])
    assert np.allclose(continuum_kernel(tau, mass=0.0, radius=1.0), 0.5)
    points = np.array([[0.0, 0.0], [0.1, 0.0]])
    interval = proper_time(points[0], points[1], radius=1.0)
    assert np.isclose(interval, 0.1)
    assert np.isclose(diamond_volume(1.0, 0.25), -4.0 * np.log(np.sin(0.25)))
