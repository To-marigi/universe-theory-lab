from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_inverse_token_incidence_v042 import (
    RESULT_PATH,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[2]


def test_incidence_counts_match_the_resaturation_gates() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    assert result["CPOBC"]["nonzero_count"] == 700
    assert result["strong_MSR"]["nonzero_count"] == 21
    assert result["fixed_vector_GC"]["nonzero_count"] == 1246


def test_almost_all_nonzero_residuals_contain_an_inverse_token() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["CPOBC"]["nonzero_containing_inverse_token_count"] == 700
    assert result["CPOBC"]["nonzero_without_inverse_token_count"] == 0
    assert result["strong_MSR"]["nonzero_containing_inverse_token_count"] == 21
    assert result["strong_MSR"]["nonzero_without_inverse_token_count"] == 0
    assert result["fixed_vector_GC"]["nonzero_containing_inverse_token_count"] == 1240
    assert result["fixed_vector_GC"]["nonzero_without_inverse_token_count"] == 6

    assert result["overall"] == {
        "total_nonzero_residuals": 1967,
        "containing_inverse_token": 1961,
        "structurally_unreachable_by_inverse_elimination": 6,
        "elimination_ceiling_fraction_of_total": "1961/1967",
    }


def test_incidence_digest_is_self_consistent() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["solver_status"]["generic_2x2_scalar_expansion"] is False
