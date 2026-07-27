from universe_lab.stringbench.benchmarks.f_heterotic_8d import (
    run_f_heterotic_8d,
)


def test_all_four_f_theory_fibrations_are_derived() -> None:
    result = run_f_heterotic_8d()
    assert result["f_theory"]["passed"]
    fibrations = result["f_theory"]["all_four_fibrations"]
    assert {item["fibration"] for item in fibrations} == {
        "standard",
        "alternate",
        "base_fiber_dual",
        "maximal",
    }
    assert all(item["discriminant_total_degree"] == 24 for item in fibrations)


def test_heterotic_round_trip_is_not_falsely_promoted() -> None:
    result = run_f_heterotic_8d()
    assert result["heterotic"]["status"] == "BLOCKED"
    assert not result["round_trip"]["passed"]
    assert result["overall_status"] == "PARTIAL"
    assert not result["string_compiler_v0_1_pass"]


def test_mutation_coverage_remains_explicitly_partial() -> None:
    result = run_f_heterotic_8d()
    mutations = result["mutations"]
    assert mutations["detected"] == 4
    assert mutations["required"] == 8
    assert not mutations["passed"]


def test_precision_error_shrinks_with_bits() -> None:
    errors = run_f_heterotic_8d()["precision"]["absolute_errors"]
    assert errors[2] < errors[1] < errors[0]
