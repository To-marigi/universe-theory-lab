from __future__ import annotations

from universe_lab.final_theory.d2_rational_dag_v034 import (
    VERDICT_COMPLETE,
    build_d2_rational_model,
    compile_d2_rational_dag_v034,
)


def test_fixed_d2_rational_dag_reconstructs_every_required_operator() -> None:
    result = compile_d2_rational_dag_v034()
    assert result["verdict"] == VERDICT_COMPLETE
    assert result["scheme"] == "FIXED_D2_RATIONAL_Q_SCHEME"
    assert not result["abstract_free_algebra_Q_only_claim"]
    assert result["counts"]["B_inverses_rationally_reconstructed"] == 22
    assert result["counts"]["transition_occurrences"] == 165
    assert result["counts"]["atomisation_paths"] == 34
    assert result["counts"]["local_GC_path_products"] == 407
    assert result["denominator_discipline"]["unproved_cancellations"] == 0


def test_adjugate_inverse_has_correct_order_and_two_sided_identity() -> None:
    model = build_d2_rational_model()
    q = model.matrices["Q_1"]
    q_inverse = model.matrices["Q_1^-1"]
    determinant = model.determinant_numerator(q)
    zero = model.arena.zero
    for left, right in ((q, q_inverse), (q_inverse, q)):
        product = model.multiply(left, right, provenance="TEST_TWO_SIDED")
        assert product.denominator == determinant
        assert product.numerator == (
            (determinant, zero),
            (zero, determinant),
        )


def test_literal_q5_is_not_identified_with_q4() -> None:
    model = build_d2_rational_model()
    assert model.q_matrices["Q_4"].numerator != model.q_matrices["Q_5"].numerator
