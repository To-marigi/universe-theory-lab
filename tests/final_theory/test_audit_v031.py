from pathlib import Path

from universe_lab.final_theory.audit_v031 import (
    V03_ARTIFACT_FREEZE,
    V03_ARTIFACT_HASHES,
    baseline_audit_v0_3_1,
    repository_inventory_v0_3_1,
)

ROOT = Path(__file__).resolve().parents[2]


def test_v03_baseline_is_immutable() -> None:
    audit = baseline_audit_v0_3_1(ROOT)
    assert audit["passed"]
    assert audit["artifact_freeze"] == V03_ARTIFACT_FREEZE
    assert audit["v03_artifacts_unchanged"]
    assert len(audit["frozen_artifacts"]) == len(V03_ARTIFACT_HASHES)


def test_v031_inventory_marks_known_gaps() -> None:
    inventory = repository_inventory_v0_3_1(ROOT)
    by_capability = {
        item["capability"]: item["classification"]
        for item in inventory["capabilities"]
    }
    assert inventory["all_inspected_paths_exist"]
    assert by_capability["CPOBC equation generation"] == "IMPLEMENTED_BUT_PARTIAL"
    assert by_capability["extendible commutative CSG positive control"] == "ABSENT"
    assert by_capability["complete d=3 Jordan-stratum solver"] == "ABSENT"
