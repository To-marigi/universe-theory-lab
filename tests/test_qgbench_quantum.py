import numpy as np
import pytest

from universe_lab.qgbench.quantum import (
    depolarizing_choi,
    mutual_information_distance,
    validate_choi_channel,
    von_neumann_entropy,
)


@pytest.mark.parametrize("probability", [0.0, 0.1, 0.5, 1.0])
def test_depolarizing_channel_is_cptp(probability: float) -> None:
    result = validate_choi_channel(
        depolarizing_choi(probability), input_dimension=2
    )
    assert result["completely_positive"]
    assert result["trace_preserving"]


def test_von_neumann_entropy_known_states() -> None:
    pure = np.diag([1.0, 0.0])
    mixed = np.eye(2) / 2
    assert np.isclose(von_neumann_entropy(pure), 0.0)
    assert np.isclose(von_neumann_entropy(mixed), 1.0)


def test_toy_mutual_information_distance_roundtrip() -> None:
    distance = np.linspace(0.0, 3.0, 20)
    scale = 0.7
    information = np.exp(-distance / scale)
    recovered = mutual_information_distance(information, correlation_length=scale)
    assert np.allclose(recovered, distance)
