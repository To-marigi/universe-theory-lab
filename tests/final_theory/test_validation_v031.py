from universe_lab.final_theory.validation_v031 import (
    mutation_benchmark_v0_3_1,
)


def test_all_mandatory_and_scoped_no_go_mutations_are_killed() -> None:
    result = mutation_benchmark_v0_3_1()
    assert result["mandatory_mutation_count"] == 17
    assert result["additional_mutation_count"] == 1
    assert result["killed"] == result["total"] == 18
    assert result["passed"]
    assert len({item["mutation_id"] for item in result["mutations"]}) == 18
    assert all(item["detector"] for item in result["mutations"])
