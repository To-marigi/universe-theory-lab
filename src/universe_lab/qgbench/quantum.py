"""有限次元量子チャネルと情報量の検証用部品。"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def von_neumann_entropy(
    density_matrix: NDArray[np.complexfloating], *, base: float = 2.0
) -> float:
    """密度行列の von Neumann エントロピー。"""

    matrix = np.asarray(density_matrix, dtype=complex)
    eigenvalues = np.linalg.eigvalsh((matrix + matrix.conj().T) / 2)
    if np.min(eigenvalues) < -1e-10 or not np.isclose(np.sum(eigenvalues), 1.0, atol=1e-10):
        raise ValueError("input must be a positive trace-one density matrix")
    positive = eigenvalues[eigenvalues > 1e-15]
    return float(-np.sum(positive * np.log(positive)) / np.log(base))


def depolarizing_choi(probability: float) -> NDArray[np.complex128]:
    """E(rho)=(1-p)rho+p I/2 の規格化 Choi 状態。"""

    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0,1]")
    bell = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2.0)
    identity_channel = np.outer(bell, bell.conj())
    completely_mixed_output = np.eye(4, dtype=complex) / 4.0
    return (1.0 - probability) * identity_channel + probability * completely_mixed_output


def validate_choi_channel(
    choi: NDArray[np.complexfloating],
    *,
    input_dimension: int,
    tolerance: float = 1e-10,
) -> dict[str, float | bool]:
    """規格化 Choi 状態から完全正値性とトレース保存性を検査する。"""

    matrix = np.asarray(choi, dtype=complex)
    expected = input_dimension**2
    if matrix.shape != (expected, expected):
        raise ValueError("Choi matrix shape does not match input dimension")
    hermitian = (matrix + matrix.conj().T) / 2
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(hermitian)))
    tensor = hermitian.reshape(input_dimension, input_dimension, input_dimension, input_dimension)
    # 添字 |input,output><input',output'| とし output を部分トレース。
    partial_trace_output = np.trace(tensor, axis1=1, axis2=3)
    target = np.eye(input_dimension) / input_dimension
    trace_preservation_error = float(np.linalg.norm(partial_trace_output - target))
    return {
        "completely_positive": minimum_eigenvalue >= -tolerance,
        "trace_preserving": trace_preservation_error <= tolerance,
        "minimum_choi_eigenvalue": minimum_eigenvalue,
        "trace_preservation_error": trace_preservation_error,
    }


def mutual_information_distance(
    mutual_information: NDArray[np.floating],
    *,
    correlation_length: float,
    reference: float = 1.0,
) -> NDArray[np.float64]:
    """仮説 I=I0 exp(-d/xi) の下で距離を復元する。

    これは幾何創発の証拠ではなく、geometry_reconstruction の toy oracle である。
    """

    values = np.asarray(mutual_information, dtype=float)
    if correlation_length <= 0 or reference <= 0 or np.any(values <= 0):
        raise ValueError("mutual information, reference and correlation length must be positive")
    return -correlation_length * np.log(values / reference)
