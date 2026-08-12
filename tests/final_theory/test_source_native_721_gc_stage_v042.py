from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_gc_stage_v042 import (
    RESULT_PATH,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[2]


def test_p3_002_stage_is_small_and_exactly_bounded() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    assert result["scope"]["endpoint"] == "p3-002"
    assert result["paths"]["count"] == 3
    assert result["pairs"]["count"] == 3
    assert result["pairs"]["word_identity_count"] == 1
    assert result["pairs"]["scalar_zero_matrix_count"] == 1
    assert result["pairs"]["total_scalar_term_count"] == 48
    assert result["pairs"]["maximum_scalar_term_count"] == 6
    assert result["global_gc_boundary"]["remaining_pair_count"] == 1526


def test_p3_002_digest_is_self_consistent_and_does_not_overclaim() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["solver_status"]["inverse_saturation_runs"] == 0
    assert result["paths"]["records"][0]["path_length"] == 2
