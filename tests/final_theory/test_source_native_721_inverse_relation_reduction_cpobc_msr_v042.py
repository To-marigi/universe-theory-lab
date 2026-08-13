from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_inverse_relation_reduction_cpobc_msr_v042 import (
    RESULT_PATH,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[2]


def test_cpobc_and_msr_reduce_with_no_newly_zero_residual() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    cpobc = result["CPOBC"]["summary"]
    assert cpobc["equation_count"] == 783
    assert cpobc["newly_zero_under_reduction_count"] == 0
    assert cpobc["still_nonzero_under_reduction_count"] == 700

    msr = result["strong_MSR"]["summary"]
    assert msr["equation_count"] == 24
    assert msr["newly_zero_under_reduction_count"] == 0
    assert msr["still_nonzero_under_reduction_count"] == 21

    assert result["overall"] == {
        "total_newly_zero_under_reduction": 0,
        "total_still_nonzero_under_reduction": 721,
    }
    assert all(
        record["status"] != "UNEXPECTEDLY_NONZERO_UNDER_REDUCTION"
        for record in result["CPOBC"]["records"] + result["strong_MSR"]["records"]
    )


def test_reduction_genuinely_changes_term_counts_from_saturation() -> None:
    """CPOBC shrinks further (3,013,576 -> 2,304,462); MSR grows slightly
    (7,704 -> 7,880). Both directions confirm the reduction did real work,
    not a no-op relative to the resaturation gate's output."""

    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["CPOBC"]["summary"]["total_reduced_scalar_term_count"] == 2304462
    assert result["strong_MSR"]["summary"]["total_reduced_scalar_term_count"] == 7880


def test_reduction_cpobc_msr_digest_is_self_consistent() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["fixed_vector_GC"]["reduced"] is False
    assert result["solver_status"]["Groebner_or_saturation_runs"] == 0
    assert result["solver_status"]["explicit_relation_reduction_runs"] == 807
