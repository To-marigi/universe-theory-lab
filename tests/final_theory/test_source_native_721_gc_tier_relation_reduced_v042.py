from __future__ import annotations

import json
from pathlib import Path

import pytest

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_gc_tier_relation_reduced_v042 import (
    VERDICT_TEMPLATE,
    result_path,
)

ROOT = Path(__file__).resolve().parents[2]

# (path_count, pair_count, still_nonzero_under_reduction)
ALL_TIERS = [
    (3, 33, 22),
    (4, 54, 39),
    (5, 100, 78),
    (6, 45, 33),
    (7, 84, 70),
    (8, 84, 62),
    (9, 144, 123),
    (10, 315, 254),
    (11, 55, 46),
    (15, 315, 259),
    (25, 300, 260),
]


@pytest.mark.parametrize("path_count,pair_count,still_nonzero", ALL_TIERS)
def test_tier_reduces_with_no_newly_zero_pair(
    path_count: int, pair_count: int, still_nonzero: int
) -> None:
    result = json.loads((ROOT / result_path(path_count)).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT_TEMPLATE.format(path_count=path_count)
    assert result["pairs"]["count"] == pair_count
    assert result["pairs"]["newly_zero_under_reduction_count"] == 0
    assert result["pairs"]["still_nonzero_under_reduction_count"] == still_nonzero
    assert result["global_gc_boundary"]["all_inventory_pair_count"] == 1529
    assert result["global_gc_boundary"]["reduced_here"] == pair_count


@pytest.mark.parametrize("path_count", [tier[0] for tier in ALL_TIERS])
def test_tier_reduced_digest_is_self_consistent(path_count: int) -> None:
    result = json.loads((ROOT / result_path(path_count)).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["solver_status"]["Groebner_or_saturation_runs"] == 0


def test_all_1529_gc_pairs_are_reduced_with_zero_newly_zero() -> None:
    total_pairs = 0
    total_newly_zero = 0
    total_still_nonzero = 0
    for path_count, _pair_count, _still_nonzero in ALL_TIERS:
        result = json.loads(
            (ROOT / result_path(path_count)).read_text(encoding="utf-8")
        )
        total_pairs += result["pairs"]["count"]
        total_newly_zero += result["pairs"]["newly_zero_under_reduction_count"]
        total_still_nonzero += result["pairs"]["still_nonzero_under_reduction_count"]

    assert total_pairs == 1529
    assert total_newly_zero == 0
    assert total_still_nonzero == 1246


def test_reduction_exhausts_the_whole_721_native_ir_with_no_closure() -> None:
    """The combined CPOBC + strong-MSR + GC picture: of all 1,967 originally
    scalar-nonzero residuals, 0 close under the exact defining-relation
    reduction (not mere substitution)."""

    gc_still_nonzero = sum(
        json.loads((ROOT / result_path(path_count)).read_text(encoding="utf-8"))[
            "pairs"
        ]["still_nonzero_under_reduction_count"]
        for path_count, _pair_count, _still_nonzero in ALL_TIERS
    )
    cpobc_msr_still_nonzero = 700 + 21
    assert gc_still_nonzero + cpobc_msr_still_nonzero == 1967
