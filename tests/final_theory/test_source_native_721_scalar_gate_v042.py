from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.source_native_721_scalar_gate_v042 import (
    RESULT_PATH,
    VERDICT,
    _matrix_expression,
)

ROOT = Path(__file__).resolve().parents[2]


def test_checked_in_scalar_gate_has_the_frozen_finite_counts() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))

    assert result["verdict"] == VERDICT
    assert result["CPOBC"]["summary"] == {
        "equation_count": 783,
        "word_identity_count": 83,
        "scalar_zero_matrix_count": 83,
        "scalar_nonzero_matrix_count": 700,
        "nonzero_scalar_entry_count": 2800,
        "total_scalar_term_count": 3557570,
        "maximum_scalar_term_count": 58604,
        "maximum_monomial_degree": 15,
        "total_scalar_term_distribution": {
            "0": 83,
            "72": 188,
            "192": 110,
            "360": 75,
            "944": 15,
            "952": 23,
            "954": 55,
            "1200": 9,
            "1912": 10,
            "2064": 124,
            "2872": 12,
            "4000": 20,
            "7536": 8,
            "9136": 12,
            "13072": 5,
            "13200": 6,
            "19784": 6,
            "19912": 6,
            "107566": 10,
            "229792": 6,
        },
        "record_digest_sha256": "5bbbf57c284137ea8248f1a47a67636f591da1d0e2aa9502efb8834b36b7c425",
    }
    assert result["strong_MSR"]["summary"] == {
        "equation_count": 24,
        "word_identity_count": 3,
        "scalar_zero_matrix_count": 3,
        "scalar_nonzero_matrix_count": 21,
        "nonzero_scalar_entry_count": 84,
        "total_scalar_term_count": 7704,
        "maximum_scalar_term_count": 186,
        "maximum_monomial_degree": 5,
        "total_scalar_term_distribution": {
            "0": 3,
            "120": 4,
            "216": 1,
            "240": 4,
            "312": 2,
            "336": 2,
            "432": 2,
            "552": 2,
            "648": 2,
            "744": 2,
        },
        "record_digest_sha256": "e607d5fbbfbdf9435a9cdeadeb1dd12a47dfa07a856f31f30a3738a8802c9d5d",
    }
    assert len(result["CPOBC"]["records"]) == 783
    assert len(result["strong_MSR"]["records"]) == 24


def test_scalar_gate_digest_is_self_consistent_and_gc_is_not_claimed() -> None:
    result = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    digest = result.pop("semantic_digest_sha256")

    assert stable_hash(result) == digest
    assert result["fixed_vector_GC"]["expanded"] is False
    assert result["fixed_vector_GC"]["same_endpoint_pair_count"] == 1529
    assert result["solver_status"]["inverse_saturation_runs"] == 0
    assert result["commutativity_proved_for_full_profile"] is False


def test_generic_matrix_product_preserves_word_order_before_commutative_sorting() -> None:
    matrix = _matrix_expression({("G_p2-2", "G_p3-002"): 1})

    assert matrix[0][0] == {
        ("M_G_p2_2_00", "M_G_p3_002_00"): 1,
        ("M_G_p2_2_01", "M_G_p3_002_10"): 1,
    }
    assert matrix != _matrix_expression({("G_p3-002", "G_p2-2"): 1})
