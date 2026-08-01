"""Regression tests for the independent exact v0.4.1 triangular scout."""

from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.one_sided_d2_v041_scout import (
    CLASSIFICATION,
    RESULT_PATH,
    VERDICT,
    compile_one_sided_d2_v041_scout,
    semantic_digest,
    write_one_sided_d2_v041_scout,
)

ROOT = Path(__file__).resolve().parents[2]


def test_exact_qq_scout_reproduces_both_one_sided_no_survivor_results() -> None:
    payload = compile_one_sided_d2_v041_scout(ROOT)
    assert payload["verdict"] == VERDICT
    assert payload["classification"] == CLASSIFICATION
    assert payload["identification_mode"] == "ON_QUOTIENT"
    assert payload["no_numeric_or_finite_field_evidence_used"] is True
    assert payload["solver_invoked"] is False
    assert payload["source_relation_counts"] == {
        "CPOBC_raw_word_equations": 783,
        "strong_MSR_source_constraints": 24,
        "strong_GC_generating_basis_relations": 320,
    }
    expected = {
        "fixed_vector_GC__strong_MSR": (130, 2),
        "strong_GC__reachable_state_MSR": (114, 18),
    }
    for name, (rank, nullity) in expected.items():
        record = payload["profiles"][name]
        assert (record["rank"], record["nullity"]) == (rank, nullity)
        assert record["independent_commutator_conditions_remaining"] == 0
        assert record["all_Q1_through_Q4_commutators_forced_zero_within_declared_ansatz"]
        assert len(record["commutators"]) == 6
        assert all(
            item["forced_zero_within_declared_ansatz"]
            for item in record["commutators"].values()
        )


def test_claim_boundary_and_canonical_result_are_stable(tmp_path: Path) -> None:
    payload = compile_one_sided_d2_v041_scout(ROOT)
    assert "not a general GL_2(QQ) proof" in payload["claim_boundary"]
    assert "OFF naturally labelled" in payload["claim_boundary"]
    assert payload["semantic_digest_sha256"] == semantic_digest(payload)
    output_root = tmp_path / "output"
    (output_root / "results").mkdir(parents=True)
    output = write_one_sided_d2_v041_scout(output_root, payload)
    assert output == output_root / RESULT_PATH
    assert "\r\n" not in output.read_bytes().decode("utf-8")
    canonical = ROOT / RESULT_PATH
    if canonical.is_file():
        assert json.loads(canonical.read_text(encoding="utf-8")) == payload
