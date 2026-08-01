"""Exact conditional state-to-operator recovery lemmas for CPOBC v0.4.2.

The module certifies finite-dimensional linear-algebra statements used by the
SR3b-M semantic recovery layer.  It does not decide either open one-sided CPOBC
profile.  In particular, a globally spanning family of states attached to
different source residuals is kept separate from multiple probes applied to
the *same* residual.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

SR2V_AUDIT_PATH = "results/v0.4.2_sr2v_baseline_observability.json"
V039_RELEASE_PATH = "results/v0.3.9_release_manifest.json"
RESULT_PATH = "results/v0.4.2_sr3b_m_semantic_recovery.json"

SCHEMA = "final-theory-v042-sr3b-m-semantic-recovery-v1"
VERDICT = "SR3B_M_CONDITIONAL_RECOVERY_LEMMAS_CERTIFIED"

Matrix2 = tuple[
    tuple[Fraction, Fraction],
    tuple[Fraction, Fraction],
]
Vector2 = tuple[Fraction, Fraction]

ZERO_MATRIX: Matrix2 = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0)))
IDENTITY: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
E11: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(0)))
E12: Matrix2 = ((Fraction(0), Fraction(1)), (Fraction(0), Fraction(0)))
E21: Matrix2 = ((Fraction(0), Fraction(0)), (Fraction(1), Fraction(0)))
E22: Matrix2 = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(1)))
FULL_M2_BASIS = (E11, E12, E21, E22)

E1: Vector2 = (Fraction(1), Fraction(0))
E2: Vector2 = (Fraction(0), Fraction(1))
ZERO_VECTOR: Vector2 = (Fraction(0), Fraction(0))


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _matrix_record(matrix: Matrix2) -> list[list[str]]:
    return [[str(entry) for entry in row] for row in matrix]


def _vector_record(vector: Vector2) -> list[str]:
    return [str(entry) for entry in vector]


def _apply(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def _flatten(matrix: Matrix2) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    return matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1]


def _rank(rows: list[list[Fraction]]) -> int:
    if not rows:
        return 0
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise AssertionError("rank matrix has inconsistent row widths")
    work = [row[:] for row in rows]
    pivot_row = 0
    for column in range(width):
        pivot = next(
            (index for index in range(pivot_row, len(work)) if work[index][column]),
            None,
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        work[pivot_row] = [value / pivot_value for value in work[pivot_row]]
        for index in range(len(work)):
            if index == pivot_row or not work[index][column]:
                continue
            coefficient = work[index][column]
            work[index] = [
                value - coefficient * pivot_entry
                for value, pivot_entry in zip(work[index], work[pivot_row], strict=True)
            ]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def evaluation_certificate(
    residual_basis: tuple[Matrix2, ...],
    probes: tuple[Vector2, ...],
) -> dict[str, Any]:
    """Return the exact rank certificate for ``D -> (D v)_v`` on a basis."""

    if not residual_basis:
        raise ValueError("a nonempty residual basis is required")
    basis_rank = _rank([list(_flatten(matrix)) for matrix in residual_basis])
    if basis_rank != len(residual_basis):
        raise ValueError("residual_basis must be linearly independent")
    if not probes:
        raise ValueError("at least one probe is required")

    columns = [
        [entry for probe in probes for entry in _apply(matrix, probe)]
        for matrix in residual_basis
    ]
    evaluation_rows = [
        [columns[column][row] for column in range(len(columns))]
        for row in range(len(columns[0]))
    ]
    evaluation_rank = _rank(evaluation_rows)
    return {
        "residual_space_dimension": len(residual_basis),
        "probe_count": len(probes),
        "probe_span_rank": _rank([list(probe) for probe in probes]),
        "evaluation_matrix": [[str(entry) for entry in row] for row in evaluation_rows],
        "evaluation_rank": evaluation_rank,
        "kernel_dimension": len(residual_basis) - evaluation_rank,
        "injective": evaluation_rank == len(residual_basis),
    }


def _symbolic_multi_probe_certificate() -> dict[str, Any]:
    a, b, c, d, x, y, z, w = sp.symbols("a b c d x y z w")
    delta = a * d - b * c
    row1_v = x * a + y * b
    row1_w = x * c + y * d
    row2_v = z * a + w * b
    row2_w = z * c + w * d
    identities = {
        "delta_times_x": sp.expand(delta * x - (d * row1_v - b * row1_w)),
        "delta_times_y": sp.expand(delta * y - (-c * row1_v + a * row1_w)),
        "delta_times_z": sp.expand(delta * z - (d * row2_v - b * row2_w)),
        "delta_times_w": sp.expand(delta * w - (-c * row2_v + a * row2_w)),
    }
    return {
        "probe_matrix": "[[a,c],[b,d]]",
        "determinant": "a*d-b*c",
        "residual_matrix": "[[x,y],[z,w]]",
        "elimination_identities": {key: str(value) for key, value in identities.items()},
        "all_symbolic_identities_zero": all(value == 0 for value in identities.values()),
        "conclusion": (
            "If both residual actions vanish and a*d-b*c is nonzero, then x=y=z=w=0."
        ),
    }


def _symbolic_centralizer_certificate() -> dict[str, Any]:
    a, b, c, d, x, y, z, w = sp.symbols("a b c d x y z w")
    matrix_a = sp.Matrix([[a, b], [c, d]])
    matrix_b = sp.Matrix([[x, y], [z, w]])
    variables = (x, y, z, w)
    commutator_entries = list(matrix_a * matrix_b - matrix_b * matrix_a)
    coefficient_matrix = sp.Matrix(
        [
            [sp.expand(entry).coeff(variable) for variable in variables]
            for entry in commutator_entries
        ]
    )
    minors = {
        "b_nonzero_branch": sp.expand(coefficient_matrix.extract([0, 1], [0, 2]).det()),
        "c_nonzero_branch": sp.expand(coefficient_matrix.extract([0, 2], [1, 3]).det()),
        "diagonal_nonscalar_branch": sp.expand(
            coefficient_matrix.extract([1, 2], [1, 2]).det().subs({b: 0, c: 0})
        ),
    }
    identity_vector = sp.Matrix([1, 0, 0, 1])
    a_vector = sp.Matrix([a, b, c, d])
    kernel_checks = {
        "I": (coefficient_matrix * identity_vector).applyfunc(sp.expand) == sp.zeros(4, 1),
        "A": (coefficient_matrix * a_vector).applyfunc(sp.expand) == sp.zeros(4, 1),
    }
    expected = {
        "b_nonzero_branch": b**2,
        "c_nonzero_branch": c**2,
        "diagonal_nonscalar_branch": -(a - d) ** 2,
    }
    return {
        "ad_A_coefficient_matrix": [
            [str(coefficient_matrix[row, column]) for column in range(4)] for row in range(4)
        ],
        "rank_two_branch_minors": {key: str(value) for key, value in minors.items()},
        "branch_minors_match": {
            key: sp.expand(minors[key] - expected[key]) == 0 for key in minors
        },
        "I_and_A_are_in_kernel": kernel_checks,
        "proof": (
            "For non-scalar A, at least one of b,c,a-d is nonzero, so a displayed rank-two "
            "minor is nonzero. I and A are independent kernel vectors, hence rank(ad_A)<=2. "
            "Thus rank(ad_A)=2 and ker(ad_A)=span{I,A}."
        ),
    }


def _global_span_counterexample() -> dict[str, Any]:
    residual_1 = E12
    residual_2 = E21
    states = (E1, E2)
    actions = (_apply(residual_1, states[0]), _apply(residual_2, states[1]))
    return {
        "states": [_vector_record(state) for state in states],
        "global_state_span_rank": _rank([list(state) for state in states]),
        "source_residuals": [_matrix_record(residual_1), _matrix_record(residual_2)],
        "matched_actions": [_vector_record(action) for action in actions],
        "both_matched_actions_zero": all(action == ZERO_VECTOR for action in actions),
        "both_source_residuals_nonzero": all(
            residual != ZERO_MATRIX for residual in (residual_1, residual_2)
        ),
        "conclusion": (
            "States attached to different source residuals may span K^2 while each nonzero "
            "residual annihilates only its own matched state."
        ),
    }


def _cyclic_not_separating_counterexample() -> dict[str, Any]:
    cyclic_images = (_apply(IDENTITY, E1), _apply(E21, E1))
    annihilator = E12
    return {
        "vector": _vector_record(E1),
        "cyclic_generators": [_matrix_record(IDENTITY), _matrix_record(E21)],
        "cyclic_images": [_vector_record(vector) for vector in cyclic_images],
        "cyclic_image_span_rank": _rank([list(vector) for vector in cyclic_images]),
        "nonzero_annihilator": _matrix_record(annihilator),
        "annihilator_action": _vector_record(_apply(annihilator, E1)),
        "cyclic": _rank([list(vector) for vector in cyclic_images]) == 2,
        "separating_for_full_M2": False,
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_paths = {
        relative: root / relative for relative in (SR2V_AUDIT_PATH, V039_RELEASE_PATH)
    }
    sr2v = _load(input_paths[SR2V_AUDIT_PATH])
    v039 = _load(input_paths[V039_RELEASE_PATH])
    if sr2v.get("verdict") != "SR2V_BASELINE_OBSERVABILITY_AUDIT_CERTIFIED" or not sr2v.get(
        "passed"
    ):
        raise AssertionError("the SR2-V baseline audit is not certified")
    if (
        v039.get("version") != "0.3.9"
        or v039.get("semantic_digest_sha256")
        != "eb9eb81d911f194fe2b6c18dfe81389e3a6fc0856a1bae3a767d46753f348e47"
    ):
        raise AssertionError("the public v0.3.9 strong-profile baseline changed")

    full_one_probe = evaluation_certificate(FULL_M2_BASIS, (E1,))
    full_two_probe = evaluation_certificate(FULL_M2_BASIS, (E1, E2))
    small_one_probe = evaluation_certificate((IDENTITY, E21), (E1,))
    multi_probe = _symbolic_multi_probe_certificate()
    centralizer = _symbolic_centralizer_certificate()
    global_counterexample = _global_span_counterexample()
    cyclic_counterexample = _cyclic_not_separating_counterexample()

    gates = {
        "full_M2_one_probe_not_injective": not full_one_probe["injective"],
        "full_M2_two_basis_probes_injective": full_two_probe["injective"],
        "smaller_two_dimensional_residual_space_one_probe_injective": small_one_probe[
            "injective"
        ],
        "symbolic_multi_probe_elimination_identities_zero": multi_probe[
            "all_symbolic_identities_zero"
        ],
        "global_span_different_source_counterexample_exact": (
            global_counterexample["global_state_span_rank"] == 2
            and global_counterexample["both_matched_actions_zero"]
            and global_counterexample["both_source_residuals_nonzero"]
        ),
        "cyclicity_counterexample_exact": (
            cyclic_counterexample["cyclic"]
            and not cyclic_counterexample["separating_for_full_M2"]
        ),
        "centralizer_branch_minors_exact": (
            all(centralizer["branch_minors_match"].values())
            and all(centralizer["I_and_A_are_in_kernel"].values())
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"SR3b-M lemma gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-01",
        "field": "Q",
        "dimension": 2,
        "input_artifacts": {
            relative: _sha256(path) for relative, path in sorted(input_paths.items())
        },
        "assumption_ledger": {
            "residual_family": (
                "For a declared source/profile, admissible residuals lie in a specified finite-"
                "dimensional linear space R over Q."
            ),
            "evaluation": "ev_V(D)=(D*v) for every probe v in the declared probe family V.",
            "same_residual_requirement": (
                "Every probe in V must test the same residual D; probes attached to different "
                "source residuals cannot be pooled."
            ),
            "single_Omega_GC": (
                "Fixed-vector GC supplies one cylinder state per source, not two independent "
                "probes for the same source residual."
            ),
            "strong_profile_endpoint": (
                "Only after both GC and MSR residual families promote to operator identities may "
                "the finite nonsingular d=2 n<=4 ON v0.3.9 commutativity theorem be invoked."
            ),
        },
        "lemmas": {
            "residual_family_separation": {
                "statement": (
                    "Statewise equality promotes to D=0 for every D in R exactly when ev_V is "
                    "injective on R."
                ),
                "full_M2_one_probe": full_one_probe,
                "full_M2_two_basis_probes": full_two_probe,
                "smaller_residual_space_one_probe": small_one_probe,
                "minimality": (
                    "Injectivity is necessary and sufficient for the declared residual space; "
                    "separation of all M2 is not required when R is smaller."
                ),
            },
            "same_source_two_probe_recovery": multi_probe,
            "global_span_is_not_sourcewise_recovery": global_counterexample,
            "cyclicity_is_not_separation": cyclic_counterexample,
            "non_scalar_centralizer_endpoint": centralizer,
        },
        "cpobc_binding": {
            "fixed_vector_GC_residual": "D_(alpha,beta)=P_alpha-P_beta tested on Omega.",
            "reachable_MSR_residual": "D_c=sum_j A_(c,j)-I tested on v_c=P_alpha*Omega.",
            "ordinary_profile_probe_count_per_source": 1,
            "multi_probe_recovery_is_additional_assumption": True,
            "one_sided_profiles_resolved": False,
            "weak_weak_visible_witness_resolved": False,
            "conditional_commutativity_recovery": (
                "If evaluation is injective for every GC and MSR residual family, both become "
                "strong operator identities; under the frozen ON/nonsingular/n<=4 hypotheses, "
                "the v0.3.9 d=2 theorem then forces Q1,...,Q4 to commute."
            ),
        },
        "gates": gates,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "These are exact conditional linear-algebra recovery lemmas bound to the CPOBC "
            "residual semantics. They do not prove that the base single-Omega profile supplies "
            "the required separating probes, and they do not close either one-sided profile."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    result = run()
    print(f"{result['verdict']} {result['semantic_digest_sha256']}")
