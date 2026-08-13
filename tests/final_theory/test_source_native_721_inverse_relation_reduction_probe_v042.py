from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_inverse_relation_reduction_probe_v042 import (
    RELATIONS,
    RESULT_PATH,
    VERDICT,
    _reduce_scalar,
)

ROOT = Path(__file__).resolve().parents[2]


def test_reduction_rewrites_the_relation_left_hand_side_exactly() -> None:
    det_variable, a, b, c, d = RELATIONS[0]
    monomial = tuple(sorted((det_variable, a, d)))
    result = _reduce_scalar({monomial: 1}, RELATIONS)

    assert result == {(): 1, tuple(sorted((det_variable, b, c))): 1}


def test_reduction_is_identity_when_the_pattern_is_absent() -> None:
    det_variable, a, _b, _c, _d = RELATIONS[0]
    monomial = (det_variable, a)
    result = _reduce_scalar({monomial: 5}, RELATIONS)

    assert result == {monomial: 5}


def test_probe_ran_a_bounded_sample_with_a_fast_measured_cost() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    assert result["measurement"]["sample_size"] == 24
    assert result["scope"]["cpobc_sample_size"] == 12
    assert result["scope"]["gc_sample_size"] == 12
    assert result["measurement"]["maximum_reduction_seconds_single_residual"] < 1.0
    assert result["solver_status"]["Groebner_or_saturation_runs"] == 0


def test_reduction_genuinely_changes_term_counts_in_the_sample() -> None:
    """The reduction is real algebraic work, not a no-op: term counts in the
    sample both increase and decrease relative to the pre-reduction matrix."""

    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    all_records = result["CPOBC_sample"] + result["GC_sample"]

    deltas = [
        record["reduced_scalar_matrix"]["total_scalar_term_count"]
        - record["saturated_scalar_matrix"]["total_scalar_term_count"]
        for record in all_records
    ]
    assert any(delta < 0 for delta in deltas)
    assert any(delta > 0 for delta in deltas)
    assert any(delta != 0 for delta in deltas)


def test_probe_digest_is_self_consistent() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["commutativity_proved_for_full_profile"] is False
