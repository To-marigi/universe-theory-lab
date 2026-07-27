import pytest

from universe_lab.qgaudit.mutations import run_all_mutations


@pytest.mark.parametrize(
    "mutation",
    [
        "jump_sign",
        "mass_coefficient",
        "ads_measure",
        "geodesic_branch",
        "label_dependence",
        "non_cp_channel",
    ],
)
def test_critical_mutation_is_detected(mutation: str) -> None:
    result = run_all_mutations()[mutation]
    assert result["detected"], result
