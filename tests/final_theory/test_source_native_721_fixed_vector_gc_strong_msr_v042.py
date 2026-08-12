from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.source_native_721_fixed_vector_gc_strong_msr_v042 import (
    RESULT_PATH,
    VERDICT,
    _expression_from_record,
    compile_source_native_721_v042,
)

ROOT = Path(__file__).resolve().parents[2]


def test_free_reduction_is_applied_before_native_matching() -> None:
    expression = _expression_from_record(
        [
            {"coefficient": 1, "word": ["G_p2-2", "G_p2-2^-1"]},
            {"coefficient": 2, "word": []},
        ]
    )
    assert expression == {(): 3}


def test_native_ir_retains_all_twenty_non_antichain_generators() -> None:
    result = compile_source_native_721_v042(ROOT)

    assert result["verdict"] == VERDICT
    assert result["native_generators"]["base_generator_count"] == 24
    assert result["native_generators"]["non_antichain_generator_count"] == 20
    assert result["native_generators"]["used_token_count"] == 32
    assert result["native_generators"]["eq112_tokens_present"] is False
    assert result["occurrence_map"] == {
        "transition_occurrences": 165,
        "decorated_signatures": 165,
        "matrix_entry_variables_per_token": 4,
        "inverse_relation_entry_slots": 64,
        "occurrence_determinant_nonzero_predicates": 165,
    }


def test_native_ir_reproduces_frozen_finite_counts_and_path_order() -> None:
    result = compile_source_native_721_v042(ROOT)

    assert result["CPOBC"]["source_relation_count"] == 641
    assert result["CPOBC"]["word_equation_count"] == 783
    assert result["CPOBC"]["free_word_identity_count"] == 83
    assert result["CPOBC"]["free_word_residual_count"] == 700
    assert result["strong_MSR"]["constraint_count"] == 24
    assert result["strong_MSR"]["free_word_identity_count"] == 3
    assert result["strong_MSR"]["free_word_residual_count"] == 21

    gc = result["fixed_vector_GC"]
    assert gc["path_count"] == 407
    assert gc["basis_relation_count"] == 320
    assert gc["same_endpoint_pair_count"] == 1529
    assert gc["operator_word_identity_pair_count"] == 283
    assert gc["operator_word_residual_pair_count"] == 1246
    assert gc["path_product_convention"] == "later_transition_multiplies_on_left"
    assert gc["fixed_vector_action"]["compiled"] is False


def test_checked_in_native_result_recompiles_byte_for_byte() -> None:
    expected = json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))
    assert compile_source_native_721_v042(ROOT) == expected
