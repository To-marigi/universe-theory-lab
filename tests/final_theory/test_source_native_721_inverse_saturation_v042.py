from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_inverse_saturation_v042 import (
    RESULT_PATH,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TOKENS = {
    "G_p2-2^-1",
    "G_p3-002^-1",
    "G_p3-006^-1",
    "G_p3-024^-1",
    "G_p3-026^-1",
    "Q_1^-1",
    "Q_2^-1",
    "Q_3^-1",
}


def test_all_eight_inverse_tokens_saturate() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    assert result["inverse_tokens_checked"] == 8
    assert result["matrix_entry_slots_checked"] == 64
    assert {record["inverse_token"] for record in result["records"]} == EXPECTED_TOKENS
    for record in result["records"]:
        assert record["saturates"] is True
        assert record["off_diagonal_zero_both_orderings"] is True
        assert record["diagonal_reduces_to_defining_relation_both_orderings"] is True
        assert record["determinant"]["term_count"] == 2
        assert record["defining_relation"]["term_count"] == 3
        assert len(record["checked_entries"]) == 8
        for entry in record["checked_entries"]:
            if entry["kind"] == "diagonal":
                assert entry["exactly_D_times_det"] is True
            else:
                assert entry["raw_polynomial_zero"] is True


def test_inverse_saturation_digest_is_self_consistent() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["solver_status"]["inverse_saturation_runs"] == 8
    assert result["solver_status"]["Groebner_or_saturation_runs"] == 0
    assert any(
        "not yet imposed" in claim for claim in result["claim_boundary"]
    )
