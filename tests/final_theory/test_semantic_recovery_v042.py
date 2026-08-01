"""Exact tests for the SR3b-M conditional semantic recovery lemmas."""

from __future__ import annotations

import hashlib
import json
import shutil
from fractions import Fraction
from pathlib import Path

import pytest
import sympy as sp

from universe_lab.final_theory import semantic_recovery_v042 as recovery

ROOT = Path(__file__).resolve().parents[2]


def test_semantic_recovery_artifact_rebuilds_exactly() -> None:
    expected = recovery.build_payload(ROOT)
    frozen = json.loads((ROOT / recovery.RESULT_PATH).read_text(encoding="utf-8"))
    assert frozen == expected
    assert frozen["passed"] is True
    assert frozen["verdict"] == recovery.VERDICT
    assert frozen["semantic_digest_sha256"] == recovery.semantic_digest(frozen)
    for relative, digest in frozen["input_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_residual_evaluation_injectivity_is_profile_specific() -> None:
    full_one = recovery.evaluation_certificate(recovery.FULL_M2_BASIS, (recovery.E1,))
    assert full_one["residual_space_dimension"] == 4
    assert full_one["evaluation_rank"] == 2
    assert full_one["kernel_dimension"] == 2
    assert full_one["injective"] is False

    full_two = recovery.evaluation_certificate(
        recovery.FULL_M2_BASIS,
        (recovery.E1, recovery.E2),
    )
    assert full_two["probe_span_rank"] == 2
    assert full_two["evaluation_rank"] == 4
    assert full_two["injective"] is True

    small_one = recovery.evaluation_certificate(
        (recovery.IDENTITY, recovery.E21),
        (recovery.E1,),
    )
    assert small_one["residual_space_dimension"] == 2
    assert small_one["probe_count"] == 1
    assert small_one["injective"] is True


def test_evaluation_certificate_fails_closed_on_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="nonempty"):
        recovery.evaluation_certificate((), (recovery.E1,))
    with pytest.raises(ValueError, match="linearly independent"):
        recovery.evaluation_certificate((recovery.E11, recovery.E11), (recovery.E1,))
    with pytest.raises(ValueError, match="at least one probe"):
        recovery.evaluation_certificate((recovery.E11,), ())


def test_global_rank_two_across_different_sources_is_not_recovery() -> None:
    counterexample = recovery.build_payload(ROOT)["lemmas"][
        "global_span_is_not_sourcewise_recovery"
    ]
    assert counterexample["global_state_span_rank"] == 2
    assert counterexample["both_matched_actions_zero"] is True
    assert counterexample["both_source_residuals_nonzero"] is True
    assert counterexample["source_residuals"] == [
        [["0", "1"], ["0", "0"]],
        [["0", "0"], ["1", "0"]],
    ]


def test_symbolic_two_probe_elimination_is_an_independent_identity() -> None:
    a, b, c, d, x, y, z, w = sp.symbols("a b c d x y z w")
    delta = a * d - b * c
    residual = sp.Matrix([[x, y], [z, w]])
    probes = sp.Matrix([[a, c], [b, d]])
    actions = residual * probes
    recovered = actions * sp.Matrix([[d, -c], [-b, a]])
    assert (recovered - delta * residual).applyfunc(sp.expand) == sp.zeros(2)
    certificate = recovery.build_payload(ROOT)["lemmas"]["same_source_two_probe_recovery"]
    assert certificate["all_symbolic_identities_zero"] is True


def test_cyclicity_does_not_imply_separation_for_full_M2() -> None:
    counterexample = recovery.build_payload(ROOT)["lemmas"]["cyclicity_is_not_separation"]
    assert counterexample["cyclic_image_span_rank"] == 2
    assert counterexample["cyclic"] is True
    assert counterexample["separating_for_full_M2"] is False
    assert counterexample["annihilator_action"] == ["0", "0"]


@pytest.mark.parametrize(
    "matrix",
    [
        sp.Matrix([[1, 1], [0, 1]]),
        sp.Matrix([[2, 0], [1, 2]]),
        sp.Matrix([[1, 0], [0, 3]]),
        sp.Matrix([[0, 2], [3, 4]]),
    ],
)
def test_non_scalar_centralizer_is_exactly_span_I_A(matrix: sp.Matrix) -> None:
    x, y, z, w = sp.symbols("x y z w")
    candidate = sp.Matrix([[x, y], [z, w]])
    equations = list(matrix * candidate - candidate * matrix)
    coefficient, _ = sp.linear_eq_to_matrix(equations, (x, y, z, w))
    nullspace = coefficient.nullspace()
    assert len(nullspace) == 2
    identity_vector = sp.Matrix([1, 0, 0, 1])
    matrix_vector = sp.Matrix(list(matrix))
    assert sp.Matrix.hstack(identity_vector, matrix_vector).rank() == 2
    assert coefficient * identity_vector == sp.zeros(4, 1)
    assert coefficient * matrix_vector == sp.zeros(4, 1)


def test_centralizer_symbolic_branch_minors_are_exact() -> None:
    centralizer = recovery.build_payload(ROOT)["lemmas"]["non_scalar_centralizer_endpoint"]
    assert centralizer["rank_two_branch_minors"] == {
        "b_nonzero_branch": "b**2",
        "c_nonzero_branch": "c**2",
        "diagonal_nonscalar_branch": "-a**2 + 2*a*d - d**2",
    }
    assert all(centralizer["branch_minors_match"].values())
    assert all(centralizer["I_and_A_are_in_kernel"].values())


def test_semantic_recovery_does_not_close_open_profiles() -> None:
    result = recovery.build_payload(ROOT)
    binding = result["cpobc_binding"]
    assert binding["ordinary_profile_probe_count_per_source"] == 1
    assert binding["multi_probe_recovery_is_additional_assumption"] is True
    assert binding["one_sided_profiles_resolved"] is False
    assert binding["weak_weak_visible_witness_resolved"] is False


def test_tampered_sr2v_input_is_rejected(tmp_path: Path) -> None:
    for relative in (recovery.SR2V_AUDIT_PATH, recovery.V039_RELEASE_PATH):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    audit_path = tmp_path / recovery.SR2V_AUDIT_PATH
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["passed"] = False
    audit_path.write_text(json.dumps(audit), encoding="utf-8", newline="\n")
    with pytest.raises(AssertionError, match="baseline audit"):
        recovery.build_payload(tmp_path)


def test_fraction_rank_path_is_exact_not_float() -> None:
    certificate = recovery.evaluation_certificate(
        (
            ((Fraction(1, 2), Fraction(0)), (Fraction(0), Fraction(0))),
            ((Fraction(0), Fraction(1, 3)), (Fraction(0), Fraction(0))),
        ),
        ((Fraction(1), Fraction(1)),),
    )
    assert certificate["evaluation_rank"] == 1
    assert certificate["kernel_dimension"] == 1
