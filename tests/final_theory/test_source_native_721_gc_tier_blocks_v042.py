from __future__ import annotations

import json
from pathlib import Path

import pytest

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_gc_tier_blocks_v042 import (
    VERDICT_TEMPLATE,
    result_path,
)

ROOT = Path(__file__).resolve().parents[2]

# (path_count, selected_endpoint_count, pair_count, word_identity_count)
REMAINING_TIERS = [
    (5, 10, 100, 22),
    (6, 3, 45, 12),
    (7, 4, 84, 14),
    (8, 3, 84, 22),
    (9, 4, 144, 21),
    (10, 7, 315, 61),
    (11, 1, 55, 9),
    (15, 3, 315, 56),
    (25, 1, 300, 40),
]


@pytest.mark.parametrize(
    "path_count,endpoint_count,pair_count,word_identity_count", REMAINING_TIERS
)
def test_tier_block_has_exact_coverage_and_finite_counts(
    path_count: int,
    endpoint_count: int,
    pair_count: int,
    word_identity_count: int,
) -> None:
    result = json.loads((ROOT / result_path(path_count)).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT_TEMPLATE.format(path_count=path_count)
    assert result["scope"]["selected_endpoint_count"] == endpoint_count
    assert result["pairs"]["count"] == pair_count
    assert result["pairs"]["word_identity_count"] == word_identity_count
    assert result["pairs"]["scalar_zero_matrix_count"] == word_identity_count
    assert result["global_gc_boundary"]["all_inventory_pair_count"] == 1529
    assert result["global_gc_boundary"]["expanded_here"] == pair_count
    assert all(
        summary["path_count"] == path_count
        for summary in result["per_endpoint"].values()
    )
    assert all(
        summary["pair_count"] == path_count * (path_count - 1) // 2
        for summary in result["per_endpoint"].values()
    )


@pytest.mark.parametrize("path_count", [tier[0] for tier in REMAINING_TIERS])
def test_tier_block_digest_is_self_consistent(path_count: int) -> None:
    result = json.loads((ROOT / result_path(path_count)).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["solver_status"]["inverse_saturation_runs"] == 0


def test_remaining_tiers_sum_to_the_predecessor_gap() -> None:
    total_pairs = 0
    total_word_identities = 0
    for path_count, _endpoints, _pair_count, _word_identity_count in REMAINING_TIERS:
        result = json.loads(
            (ROOT / result_path(path_count)).read_text(encoding="utf-8")
        )
        total_pairs += result["pairs"]["count"]
        total_word_identities += result["pairs"]["word_identity_count"]

    assert total_pairs == 1442
    assert total_word_identities == 257
    # 3-path (33) + 4-path (54) predecessor gates plus these tiers exhaust
    # every same-endpoint GC pair in the 407-path/1,529-pair inventory.
    assert 33 + 54 + total_pairs == 1529
