"""Independent linear spin-2 reference controls.

These controls validate the benchmark machinery. They are not evidence that a
registered microscopic candidate produces a graviton.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def transverse_projector(momentum: np.ndarray) -> np.ndarray:
    """Return the Euclidean projector transverse to a nonzero momentum."""

    vector = np.asarray(momentum, dtype=float)
    norm_squared = float(vector @ vector)
    if norm_squared <= 0.0:
        raise ValueError("the Euclidean reference momentum must be nonzero")
    return np.eye(len(vector)) - np.outer(vector, vector) / norm_squared


def barnes_rivers_spin2(momentum: np.ndarray) -> np.ndarray:
    """Return the off-shell transverse-traceless spin-2 projector."""

    theta = transverse_projector(momentum)
    dimension = len(theta)
    first = 0.5 * (
        np.einsum("mr,ns->mnrs", theta, theta)
        + np.einsum("ms,nr->mnrs", theta, theta)
    )
    trace = np.einsum("mn,rs->mnrs", theta, theta) / (dimension - 1)
    return first - trace


def barnes_rivers_reference_audit(
    momentum: tuple[float, ...] = (1.0, 2.0, 3.0, 4.0),
    *,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Audit projector algebra at a generic non-null Euclidean momentum."""

    vector = np.asarray(momentum, dtype=float)
    projector = barnes_rivers_spin2(vector)
    composed = np.einsum("mnab,abrs->mnrs", projector, projector)
    identity = np.eye(len(vector))
    operator = projector.reshape(len(vector) ** 2, len(vector) ** 2)
    checks = {
        "idempotent": float(np.max(np.abs(composed - projector))) < tolerance,
        "pair_symmetric": (
            float(np.max(np.abs(projector - projector.swapaxes(0, 1)))) < tolerance
            and float(np.max(np.abs(projector - projector.swapaxes(2, 3))))
            < tolerance
        ),
        "exchange_symmetric": (
            float(np.max(np.abs(projector - projector.transpose(2, 3, 0, 1))))
            < tolerance
        ),
        "transverse": (
            float(np.max(np.abs(np.einsum("m,mnrs->nrs", vector, projector))))
            < tolerance
        ),
        "traceless": (
            float(np.max(np.abs(np.einsum("mn,mnrs->rs", identity, projector))))
            < tolerance
        ),
        "off_shell_projector_rank_five": (
            int(np.linalg.matrix_rank(operator, tol=tolerance)) == 5
        ),
    }
    return {
        "name": "barnes_rivers_spin2_projector",
        "role": "REFERENCE_CONTROL_ONLY",
        "dimension": len(vector),
        "momentum": vector.tolist(),
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "Rank five is the rank of the off-shell D=4 transverse-traceless "
            "projector. It is not the two-helicity on-shell graviton count."
        ),
    }


def massless_helicity_reference_audit(*, tolerance: float = 1e-12) -> dict[str, Any]:
    """Check the plus/cross helicity basis for a fixed null D=4 momentum."""

    metric = np.diag([-1.0, 1.0, 1.0, 1.0])
    momentum = np.asarray([1.0, 0.0, 0.0, 1.0])
    plus = np.zeros((4, 4))
    plus[1, 1] = 1.0 / np.sqrt(2.0)
    plus[2, 2] = -1.0 / np.sqrt(2.0)
    cross = np.zeros((4, 4))
    cross[1, 2] = cross[2, 1] = 1.0 / np.sqrt(2.0)
    polarizations = np.stack([plus, cross])
    gram = np.einsum(
        "amn,mr,ns,brs->ab",
        polarizations,
        metric,
        metric,
        polarizations,
        optimize=True,
    )
    checks = {
        "momentum_is_null": abs(float(momentum @ metric @ momentum)) < tolerance,
        "transverse": (
            float(np.max(np.abs(np.einsum("m,amn->an", momentum, polarizations))))
            < tolerance
        ),
        "traceless": (
            float(np.max(np.abs(np.einsum("mn,amn->a", metric, polarizations))))
            < tolerance
        ),
        "orthonormal": float(np.max(np.abs(gram - np.eye(2)))) < tolerance,
        "two_independent_polarizations": (
            int(np.linalg.matrix_rank(polarizations.reshape(2, 16), tol=tolerance)) == 2
        ),
    }
    return {
        "name": "massless_spin2_helicity_basis",
        "role": "REFERENCE_CONTROL_ONLY",
        "momentum": momentum.tolist(),
        "polarizations": ["plus", "cross"],
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "This is the known D=4 massless spin-2 kinematic target, not a "
            "derivation from any registered microscopic candidate."
        ),
    }


def _linearized_einstein(
    field: np.ndarray, momentum_up: np.ndarray, metric: np.ndarray
) -> np.ndarray:
    """Momentum-space linearized Einstein tensor, up to an overall sign."""

    momentum_down = metric @ momentum_up
    momentum_squared = float(momentum_up @ momentum_down)
    trace = float(np.einsum("mn,mn", metric, field))
    divergence = np.einsum("m,mn->n", momentum_up, field)
    double_divergence = float(momentum_up @ field @ momentum_up)
    return 0.5 * (
        momentum_squared * field
        - np.outer(momentum_down, divergence)
        - np.outer(divergence, momentum_down)
        + np.outer(momentum_down, momentum_down) * trace
        - metric * (momentum_squared * trace - double_divergence)
    )


def fierz_pauli_ward_reference_audit(*, tolerance: float = 1e-12) -> dict[str, Any]:
    """Verify gauge-null and Bianchi identities for the linear spin-2 oracle."""

    metric = np.diag([-1.0, 1.0, 1.0, 1.0])
    momentum_up = np.asarray([2.0, 1.0, 0.0, 0.0])
    momentum_down = metric @ momentum_up
    gauge_errors: list[float] = []
    for direction in np.eye(4):
        direction_down = metric @ direction
        pure_gauge = np.outer(momentum_down, direction_down) + np.outer(
            direction_down, momentum_down
        )
        gauge_errors.append(
            float(
                np.max(
                    np.abs(_linearized_einstein(pure_gauge, momentum_up, metric))
                )
            )
        )
    trial = np.arange(16, dtype=float).reshape(4, 4)
    trial = 0.5 * (trial + trial.T)
    einstein = _linearized_einstein(trial, momentum_up, metric)
    bianchi_error = float(
        np.max(np.abs(np.einsum("m,mn->n", momentum_up, einstein)))
    )
    checks = {
        "four_gauge_directions_are_null": max(gauge_errors) < tolerance,
        "linearized_bianchi_identity": bianchi_error < tolerance,
    }
    return {
        "name": "fierz_pauli_ward_identity",
        "role": "REFERENCE_CONTROL_ONLY",
        "checks": checks,
        "max_gauge_error": max(gauge_errors),
        "bianchi_error": bianchi_error,
        "passed": all(checks.values()),
        "claim_boundary": (
            "The oracle starts from the linearized Einstein/Fierz-Pauli "
            "operator. Passing it cannot be counted as emergent gravity."
        ),
    }


def run_spin2_reference_controls() -> dict[str, Any]:
    """Run all independent positive controls for the Spin-2 Gate."""

    controls = [
        barnes_rivers_reference_audit(),
        massless_helicity_reference_audit(),
        fierz_pauli_ward_reference_audit(),
    ]
    return {
        "suite": "Emergent Spin-2 Gate reference controls",
        "controls": controls,
        "passed": all(control["passed"] for control in controls),
        "candidate_evidence": False,
    }
