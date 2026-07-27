from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory.v03 import (
    REQUIRED_PROVENANCE_FIELDS,
    RESULT_NAMES,
    build_v0_3_payloads,
    verify_v0_3_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(scope="module")
def payloads() -> dict[str, dict[str, Any]]:
    return build_v0_3_payloads(ROOT, code_commit="TEST_COMMIT")


def test_every_required_payload_has_the_provenance_envelope(
    payloads: dict[str, dict[str, Any]],
) -> None:
    assert set(payloads) == set(RESULT_NAMES)
    assert all(
        REQUIRED_PROVENANCE_FIELDS <= payload.keys()
        for payload in payloads.values()
    )
    assert all(payload["code_commit"] == "TEST_COMMIT" for payload in payloads.values())
    assert all(payload["input_hashes"] for payload in payloads.values())
    assert all(payload["source_paper_versions"] for payload in payloads.values())


def test_novelty_first_status_axes_remain_independent(
    payloads: dict[str, dict[str, Any]],
) -> None:
    final = payloads["final_theory_bench_v0.3.json"]
    assert final["statuses"] == {
        "ENGINEERING_STATUS": "ENGINEERING_PASS",
        "LITERATURE_BOUNDARY_STATUS": "LITERATURE_BOUNDARY_LOCKED",
        "PAPER_REGRESSION_STATUS": "PAPER_REGRESSION_PASS",
        "GEOMETRY_QUANTUMNESS_STATUS": "CLASSICAL_GEOMETRY_WITH_QUANTUM_MEMORY",
        "KRAUS_BELL_STATUS": "KRAUS_BELL_CAUSALITY_UNDEFINED",
        "CPOBC_RELATION_STATUS": "CPOBC_RELATION_COMPILER_PARTIAL",
        "CPOBC_REPRESENTATION_STATUS": "CPOBC_SEARCH_INCONCLUSIVE",
        "INFINITE_EXTENSION_STATUS": "INFINITE_EXTENSION_BLOCKED",
        "SCIENTIFIC_STATUS": "FINAL_THEORY_OPEN",
    }
    assert final["benchmark_integrity_passed"]
    assert final["mutations"]["killed"] == final["mutations"]["total"] == 14


def test_prohibited_claims_are_not_promoted(
    payloads: dict[str, dict[str, Any]],
) -> None:
    final = payloads["final_theory_bench_v0.3.json"]
    assert final["verdict"] == "FINAL_THEORY_OPEN"
    assert "QUANTUM_GEOMETRY_CANDIDATE" in final["prohibited_claims"]
    assert "KRAUS_BELL_CAUSALITY_PASS" in final["prohibited_claims"]
    assert "CPOBC_NONCOMMUTATIVE_REPRESENTATION_FOUND" in final[
        "prohibited_claims"
    ]
    assert "FINAL_THEORY_COMPLETED" in final["prohibited_claims"]


def test_v02_baseline_is_still_hash_locked(
    payloads: dict[str, dict[str, Any]],
) -> None:
    baseline = payloads["final_theory_bench_v0.3.json"]["baseline"]
    assert baseline["passed"]
    assert baseline["v02_files_modified_by_v03"] is False
    assert all(record["unchanged"] for record in baseline["frozen_artifacts"])


def test_checked_in_artifact_manifest_verifies() -> None:
    result = verify_v0_3_artifacts(ROOT)
    assert result["passed"]
    assert all(result["checks"].values())
