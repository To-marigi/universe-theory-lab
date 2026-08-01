"""Independent tests for the v0.4.2 pure-lower manifest oracle."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from universe_lab.final_theory import source_native_955_pure_lower_oracle_v042 as oracle

ROOT = Path(__file__).resolve().parents[2]


def test_pure_lower_oracle_rebuilds_checked_in_artifacts() -> None:
    payload = oracle.build_payload(ROOT)
    assert payload["passed"] is True
    assert payload["verdict"] == oracle.VERDICT
    assert payload["specialization"]["checks"]["record_counts"] == {
        "CPOBC": 783,
        "strong_GC": 320,
        "reachable_MSR_vector": 24,
    }
    assert payload["specialization"]["checks"]["max_y_degree"] == {
        "CPOBC": 1,
        "strong_GC": 1,
        "reachable_MSR_vector": 1,
    }
    crosscheck = payload["selected_row_crosscheck"]
    assert crosscheck["matrix_shape"] == [131, 131]
    assert crosscheck["sympy_QQ_rank"] == 131
    assert crosscheck["all_131_labels_and_QQ_coefficients_match_nonlinear_specialization"] is True


def test_result_is_current_and_semantically_hashed() -> None:
    expected = oracle.build_payload(ROOT)
    checked_in = json.loads((ROOT / oracle.RESULT_PATH).read_text(encoding="utf-8"))
    assert checked_in == expected
    assert checked_in["semantic_digest_sha256"] == oracle.semantic_digest(checked_in)
    for relative, digest in checked_in["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_oracle_is_independent_from_tangent_rank_implementation() -> None:
    source = (
        ROOT / "src/universe_lab/final_theory/source_native_955_pure_lower_oracle_v042.py"
    ).read_text(encoding="utf-8")
    assert "mixed_xy_nonneutral_scout_v042" not in source
    assert "_rank(" not in source
    assert "sp.SparseMatrix" in source


def test_oracle_rejects_a_semantically_tampered_input(tmp_path: Path) -> None:
    target_results = tmp_path / "results"
    target_results.mkdir()
    for relative in (oracle.MIXED_MANIFEST_PATH, oracle.TANGENT_CERTIFICATE_PATH):
        shutil.copy2(ROOT / relative, tmp_path / relative)
    tangent_path = tmp_path / oracle.TANGENT_CERTIFICATE_PATH
    tangent = json.loads(tangent_path.read_text(encoding="utf-8"))
    tangent["diagonal_base_tangent"]["rank"] = 244
    tangent_path.write_text(json.dumps(tangent), encoding="utf-8", newline="\n")
    with pytest.raises(AssertionError, match="digest gate"):
        oracle.build_payload(tmp_path)
