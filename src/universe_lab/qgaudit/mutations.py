"""Deterministic negative controls for the independent audit."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from universe_lab.qgaudit.oracle import (
    causal_relation,
    diamond_volume,
    discrete_kernel,
    proper_time,
    sprinkle,
)


def defining_equation_residual(
    kernel: NDArray[np.float64],
    relation: NDArray[np.bool_],
    *,
    mass: float,
    density: float,
) -> float:
    """Residual against the unmutated Eq. 56 contract."""

    causal = np.asarray(relation, dtype=float)
    expected = 0.5 * causal
    system = np.eye(len(causal)) + mass**2 * causal / (2.0 * density)
    return float(np.max(np.abs(np.asarray(kernel) @ system - expected)))


def jump_sign_control() -> dict[str, float | bool]:
    sample = sprinkle(36, seed=101)
    relation = causal_relation(sample.points)
    reference = discrete_kernel(relation, mass=2.0, density=sample.density)
    mutant = discrete_kernel(relation, mass=2.0, density=sample.density, jump=-0.5)
    reference_residual = defining_equation_residual(
        reference, relation, mass=2.0, density=sample.density
    )
    mutant_residual = defining_equation_residual(
        mutant, relation, mass=2.0, density=sample.density
    )
    return {
        "detected": reference_residual < 1e-12 and mutant_residual > 0.5,
        "reference_residual": reference_residual,
        "mutant_residual": mutant_residual,
    }


def mass_coefficient_control() -> dict[str, float | bool]:
    sample = sprinkle(42, seed=102)
    relation = causal_relation(sample.points)
    reference = discrete_kernel(relation, mass=3.0, density=sample.density)
    mutant = discrete_kernel(
        relation,
        mass=3.0,
        density=sample.density,
        mass_coefficient_scale=2.0,
    )
    reference_residual = defining_equation_residual(
        reference, relation, mass=3.0, density=sample.density
    )
    mutant_residual = defining_equation_residual(
        mutant, relation, mass=3.0, density=sample.density
    )
    return {
        "detected": reference_residual < 1e-12 and mutant_residual > 1e-4,
        "reference_residual": reference_residual,
        "mutant_residual": mutant_residual,
    }


def ads_measure_control() -> dict[str, float | bool]:
    radius = 1.3
    epsilon = 0.27
    analytic = diamond_volume(radius, epsilon)
    mutant = -2.0 * radius**2 * np.log(np.sin(epsilon))
    relative_error = float(abs(mutant - analytic) / analytic)
    return {"detected": relative_error > 0.49, "mutant_relative_error": relative_error}


def geodesic_branch_control() -> dict[str, float | bool]:
    radius = 1.0
    first = np.array([0.0, 0.0])
    second = np.array([1e-4, 0.0])
    reference = float(proper_time(first, second, radius=radius))
    mutant = float(2.0 * np.pi * radius - reference)
    local_coordinate_interval = 1e-4 * radius
    reference_error = abs(reference - local_coordinate_interval)
    mutant_error = abs(mutant - local_coordinate_interval)
    return {
        "detected": reference_error < 1e-8 and mutant_error > 6.0,
        "reference_local_error": reference_error,
        "mutant_local_error": mutant_error,
    }


def label_dependence_control() -> dict[str, float | bool]:
    sample = sprinkle(45, seed=104)
    relation = causal_relation(sample.points)
    reference = discrete_kernel(relation, mass=2.5, density=sample.density)
    permutation = np.random.default_rng(105).permutation(len(relation))
    permuted_relation = relation[np.ix_(permutation, permutation)]
    equivariant = discrete_kernel(permuted_relation, mass=2.5, density=sample.density)
    inverse = np.argsort(permutation)
    recovered = equivariant[np.ix_(inverse, inverse)]
    reference_error = float(np.max(np.abs(recovered - reference)))
    weights = 1.0 + np.arange(len(reference), dtype=float) / len(reference)
    mutated_permuted = equivariant * weights[:, None]
    mutated_recovered = mutated_permuted[np.ix_(inverse, inverse)]
    mutant_error = float(np.max(np.abs(mutated_recovered - reference)))
    return {
        "detected": reference_error < 1e-12 and mutant_error > 1e-3,
        "reference_equivariance_error": reference_error,
        "mutant_equivariance_error": mutant_error,
    }


def _validate_normalized_choi(
    choi: NDArray[np.complex128],
) -> tuple[bool, float, float]:
    hermitian = (choi + choi.conj().T) / 2.0
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(hermitian)))
    tensor = hermitian.reshape(2, 2, 2, 2)
    trace_error = float(
        np.linalg.norm(np.trace(tensor, axis1=1, axis2=3) - np.eye(2) / 2.0)
    )
    return minimum_eigenvalue >= -1e-12 and trace_error <= 1e-12, minimum_eigenvalue, trace_error


def non_cp_channel_control() -> dict[str, float | bool]:
    bell = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2.0)
    reference = np.outer(bell, bell.conj())
    mutant = np.diag(np.array([0.6, -0.1, -0.1, 0.6], dtype=complex))
    reference_valid, reference_minimum, _ = _validate_normalized_choi(reference)
    mutant_valid, mutant_minimum, mutant_trace_error = _validate_normalized_choi(mutant)
    return {
        "detected": reference_valid and not mutant_valid and mutant_trace_error < 1e-12,
        "reference_minimum_eigenvalue": reference_minimum,
        "mutant_minimum_eigenvalue": mutant_minimum,
        "mutant_trace_preservation_error": mutant_trace_error,
    }


def run_all_mutations() -> dict[str, dict[str, float | bool]]:
    return {
        "jump_sign": jump_sign_control(),
        "mass_coefficient": mass_coefficient_control(),
        "ads_measure": ads_measure_control(),
        "geodesic_branch": geodesic_branch_control(),
        "label_dependence": label_dependence_control(),
        "non_cp_channel": non_cp_channel_control(),
    }
