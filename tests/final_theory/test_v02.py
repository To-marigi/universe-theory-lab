from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
)
from universe_lab.final_theory import v02 as v02_module
from universe_lab.final_theory.mutations_v02 import mutation_benchmark
from universe_lab.final_theory.v02 import (
    BASELINE_COMMIT,
    run_final_theory_bench_v0_2,
)

ROOT = Path(__file__).resolve().parents[2]
LEGACY_DIGESTS = LegacyRawDigestResolver(
    ROOT,
    load_line_ending_bridge(ROOT / "results/v0.3.8_line_ending_bridge.json"),
)


@pytest.fixture(scope="module", autouse=True)
def _bridge_legacy_raw_hashes() -> Iterator[None]:
    original = v02_module._sha256
    v02_module._sha256 = LEGACY_DIGESTS.sha256
    try:
        yield
    finally:
        v02_module._sha256 = original


def test_all_registered_mutations_are_killed() -> None:
    result = mutation_benchmark()
    assert result["passed"]
    assert result["killed"] == result["total"] == 8


def test_v01_baseline_files_are_unchanged() -> None:
    result = run_final_theory_bench_v0_2(ROOT)
    assert result["baseline"]["commit"] == BASELINE_COMMIT
    assert result["baseline"]["passed"]


def test_v02_verdict_preserves_claim_boundaries() -> None:
    result = run_final_theory_bench_v0_2(ROOT)
    assert result["benchmark_integrity_passed"]
    assert result["statuses"]["DYNAMICS_STATUS"] == "DYNAMICS_CANDIDATE_DEFINED"
    assert (
        result["statuses"]["CONTINUUM_STATUS"]
        == "CONTINUUM_PHASE_RESOURCE_BLOCKED"
    )
    assert (
        result["statuses"]["SPIN_GATE_STATUS"]
        == "SPIN2_GATE_BLOCKED_BY_CONTINUUM"
    )
    assert result["statuses"]["SCIENTIFIC_STATUS"] == "FINAL_THEORY_OPEN"
    assert "SPIN2_GATE_PASS" in result["prohibited_claims"]
    assert "DYNAMICS_CONSISTENCY_PASS" in result["prohibited_claims"]
