from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_inverse_resaturated_cpobc_msr_v042 import (
    RESULT_PATH,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[2]


def test_cpobc_and_msr_resaturate_with_no_newly_zero_residual() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    cpobc = result["CPOBC"]["summary"]
    assert cpobc["equation_count"] == 783
    assert cpobc["newly_zero_under_saturation_count"] == 0
    assert cpobc["still_nonzero_under_saturation_count"] == 700

    msr = result["strong_MSR"]["summary"]
    assert msr["equation_count"] == 24
    assert msr["newly_zero_under_saturation_count"] == 0
    assert msr["still_nonzero_under_saturation_count"] == 21

    assert result["overall"] == {
        "total_newly_zero_under_saturation": 0,
        "total_still_nonzero_under_saturation": 721,
    }
    assert all(
        record["status"] != "UNEXPECTEDLY_NONZERO_UNDER_SATURATION"
        for record in result["CPOBC"]["records"] + result["strong_MSR"]["records"]
    )


def test_msr_terms_are_unaffected_by_saturation() -> None:
    """No MSR constraint's word contains an inverse token, so its saturated
    scalar-term statistics must equal the original unsaturated scalar gate's."""

    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    msr = result["strong_MSR"]["summary"]

    assert msr["total_saturated_scalar_term_count"] == 7704
    assert msr["maximum_saturated_scalar_term_count"] == 186


def test_resaturated_cpobc_msr_digest_is_self_consistent() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
    assert result["fixed_vector_GC"]["resaturated"] is False
    assert result["solver_status"]["Groebner_or_saturation_runs"] == 0
