from universe_lab.stringbench.narain.audits import (
    run_held_out_audit,
    run_mutation_audit,
)
from universe_lab.stringbench.narain.branches import derive_branch_certificates


def test_critical_mutations_are_detected() -> None:
    audit = run_mutation_audit(derive_branch_certificates())
    assert audit["detected"] == 12
    assert audit["required"] == 12
    assert audit["critical_gate"] == {
        "detected": 12,
        "required": 8,
        "passed": True,
    }
    assert audit["passed"]


def test_held_out_audit_records_blocked_j30() -> None:
    audit = run_held_out_audit()
    assert audit["passed_cases"] == 5
    assert audit["required_cases"] == 6
    assert not audit["passed"]
    j30 = next(item for item in audit["cases"] if item["name"] == "J30=0")
    assert j30["status"] == "BLOCKED"


def test_special_loci_are_exact_and_not_retuned() -> None:
    audit = run_held_out_audit()
    executed = [item for item in audit["cases"] if item["name"] != "J30=0"]
    assert all(item["checks"]["expected_locus"] for item in executed)
    assert all(item["checks"]["no_parameter_retuning"] for item in executed)
    assert all(item["checks"]["weighted_scale_not_fixed"] for item in executed)
