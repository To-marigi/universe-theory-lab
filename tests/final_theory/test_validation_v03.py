from __future__ import annotations

from universe_lab.final_theory.validation_v03 import (
    held_out_audit_v0_3,
    mutation_benchmark_v0_3,
)


def test_all_fourteen_critical_mutations_are_killed() -> None:
    result = mutation_benchmark_v0_3()
    assert result["passed"]
    assert result["killed"] == result["total"] == 14
    assert len({record["mutation_id"] for record in result["mutations"]}) == 14
    assert all(record["detector"] for record in result["mutations"])


def test_held_out_protocol_reports_blocked_partitions_without_retuning() -> None:
    result = held_out_audit_v0_3()
    assert not result["retuned_after_held_out"]
    assert result["status"] == "HELD_OUT_PROTOCOL_PARTIAL"
    statuses = {record["partition"]: record["status"] for record in result["partitions"]}
    assert statuses["causet size"] == "PASS_EXACT"
    assert statuses["initial state"] == "BLOCKED_BY_ONE_DIMENSIONAL_ROOT_SCHEMA"
    assert statuses["Kraus representation"] == "PASS_EXACT"
