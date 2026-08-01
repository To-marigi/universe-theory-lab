"""Regression checks for the exact source-native 955 N!=0 scout."""

from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.source_native_955_n_nonzero_scout_v042 import (
    RESULT_PATH,
    VERDICT,
    compile_source_native_955_n_nonzero_scout_v042,
    semantic_digest,
)

ROOT = Path(__file__).resolve().parents[2]


def _compiled() -> dict[str, object]:
    return compile_source_native_955_n_nonzero_scout_v042(ROOT)


def test_exact_rank_and_commutator_result_is_stable() -> None:
    payload = _compiled()
    checks = payload["checks"]
    assert isinstance(checks, dict)
    assert checks["raw_CPOBC_rank"] == 108
    assert checks["combined_profile_rank"] == 114
    assert checks["combined_profile_nullity"] == 17
    assert checks["strong_GC_connectivity_evidence_sha256"] == (
        "1077ec8ce21902c5db6ce106aaf30dd92c4e5d0574edde75b06e3cbdd55c6b54"
    )
    assert checks["all_six_Q_commutators_forced_zero_in_ansatz"] is True
    assert all(
        record["forced_zero_within_declared_ansatz"] is True and record["augmented_rank"] == 114
        for record in checks["commutator_functionals"].values()
    )


def test_reachable_msr_and_n_nonzero_are_both_directly_checked() -> None:
    checks = _compiled()["checks"]
    assert isinstance(checks, dict)
    assert checks["reachable_state_MSR_sources"] == 24
    assert checks["all_reachable_state_residuals_zero"] is True
    assert checks["uniform_N_nonzero_certificate"] == {
        "source_id": "p1-0",
        "operator_residual_lower_right": "1",
        "independent_of_upper_right_coordinates": True,
    }
    assert checks["all_determinants_nonzero"] is True


def test_checked_in_result_is_reproduced_and_remains_open() -> None:
    stored = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    assert stored == _compiled()
    assert stored["verdict"] == VERDICT
    assert stored["passed"] is True
    assert stored["sage_status"] == "NOT_INVOKED"
    assert stored["semantic_digest_sha256"] == semantic_digest(stored)
    assert "does not prove general commutativity" in stored["claim_boundary"]
