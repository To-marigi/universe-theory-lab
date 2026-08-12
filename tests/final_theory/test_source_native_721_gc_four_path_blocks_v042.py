from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_gc_four_path_blocks_v042 import (
    RESULT_PATH,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[2]


def test_four_path_gc_blocks_have_exact_coverage_and_finite_counts() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    assert result["scope"]["selected_endpoint_count"] == 9
    assert result["paths"]["count"] == 36
    assert result["basis"]["relation_count"] == 27
    assert result["pairs"]["count"] == 54
    assert result["pairs"]["word_identity_count"] == 15
    assert result["pairs"]["scalar_zero_matrix_count"] == 15
    assert result["pairs"]["nonzero_scalar_entry_count"] == 156
    assert result["global_gc_boundary"]["expanded_here"] == 54
    assert result["global_gc_boundary"]["expanded_cumulative_with_predecessor"] == 87
    assert result["global_gc_boundary"]["remaining_pair_count"] == 1442
    assert all(summary["path_count"] == 4 for summary in result["per_endpoint"].values())
    assert all(summary["pair_count"] == 6 for summary in result["per_endpoint"].values())


def test_four_path_gc_digest_and_claim_boundary_are_self_consistent() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["solver_status"]["inverse_saturation_runs"] == 0
    assert result["global_gc_boundary"]["all_inventory_pair_count"] == 1529
