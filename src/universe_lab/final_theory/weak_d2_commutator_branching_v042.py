"""Exact 2x2 commutator-pivot branch cover for the SR2-V search.

Every Q-noncommutative model has one of six nonzero commutators
``C_ij=[Q_i,Q_j]``.  On such a pivot, elementary 2x2 identities split the
search into pair-irreducible, triple-irreducible, transverse reducible, and
aligned reducible branches.  The theorem is pure linear algebra over ``QQ``;
it is a coverage certificate, not a CPOBC existence or obstruction result.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_commutator_pivot_branch_cover.json"
SCHEMA = "final-theory-v042-sr2v-commutator-pivot-branch-cover-v1"
VERDICT = "SR2V_COMMUTATOR_PIVOT_BRANCH_COVER_CERTIFIED"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_STRUCTURAL_COVER_ONLY"

Matrix2 = tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]
Vector2 = tuple[Fraction, Fraction]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _multiply(left: Matrix2, right: Matrix2) -> Matrix2:
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def _subtract(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _commutator(left: Matrix2, right: Matrix2) -> Matrix2:
    return _subtract(_multiply(left, right), _multiply(right, left))


def _apply(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def _determinant(matrix: Matrix2) -> Fraction:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _trace(matrix: Matrix2) -> Fraction:
    return matrix[0][0] + matrix[1][1]


def _symbolic_identities() -> dict[str, Any]:
    a, b, c, d, e, f, g, h = sp.symbols("a b c d e f g h")
    x11, x12, x21, x22 = sp.symbols("x11 x12 x21 x22")
    left = sp.Matrix([[a, b], [c, d]])
    right = sp.Matrix([[e, f], [g, h]])
    extra = sp.Matrix([[x11, x12], [x21, x22]])
    commutator = left * right - right * left
    determinant = sp.expand(commutator.det())
    cayley_hamilton = (commutator * commutator + determinant * sp.eye(2)).applyfunc(
        sp.expand
    )

    diagonal_residual = sp.expand(b * g - f * c)
    lower_residual = sp.expand(c * (e - h) + g * (d - a))
    upper_entry = sp.expand(f * (a - d) + b * (h - e))
    force_c_identity = sp.expand(
        c * upper_entry + b * lower_residual + diagonal_residual * (a - d)
    )
    force_g_identity = sp.expand(
        g * upper_entry + f * lower_residual - diagonal_residual * (h - e)
    )

    canonical_commutator = sp.Matrix([[0, 1], [0, 0]])
    tau = sp.expand(sp.trace(canonical_commutator * extra))
    return {
        "generic_commutator_trace": str(sp.expand(sp.trace(commutator))),
        "cayley_hamilton_residual": [
            [str(cayley_hamilton[row, column]) for column in range(2)]
            for row in range(2)
        ],
        "canonical_component_residuals": {
            "diagonal": str(diagonal_residual),
            "lower_left": str(lower_residual),
            "upper_right": str(upper_entry),
        },
        "ideal_membership_identities": {
            "force_A21_formula": "c*U+b*L+D*(a-d)=0",
            "force_A21": str(force_c_identity),
            "force_B21_formula": "g*U+f*L-D*(h-e)=0",
            "force_B21": str(force_g_identity),
            "interpretation": (
                "with diagonal=0, lower_left=0, and upper_right=1, "
                "the identities give c=A21=0 and g=B21=0"
            ),
        },
        "tau_in_canonical_basis": str(tau),
        "all_zero_identity_checks": (
            sp.trace(commutator) == 0
            and cayley_hamilton == sp.zeros(2)
            and force_c_identity == 0
            and force_g_identity == 0
            and tau == x21
        ),
    }


def _branch_examples() -> dict[str, Any]:
    q_left: Matrix2 = ((Fraction(2), Fraction(0)), (Fraction(0), Fraction(1)))
    q_right: Matrix2 = ((Fraction(1), Fraction(1)), (Fraction(0), Fraction(1)))
    canonical = _commutator(q_left, q_right)
    if canonical != ((Fraction(0), Fraction(1)), (Fraction(0), Fraction(0))):
        raise AssertionError("the canonical rational pair changed")
    pair_irreducible_left: Matrix2 = (
        (Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(-1)),
    )
    pair_irreducible_right: Matrix2 = (
        (Fraction(0), Fraction(1)),
        (Fraction(1), Fraction(0)),
    )
    pair_commutator = _commutator(pair_irreducible_left, pair_irreducible_right)
    breaker: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(1), Fraction(1)))
    omega_transverse: Vector2 = (Fraction(0), Fraction(1))
    omega_aligned: Vector2 = (Fraction(1), Fraction(0))
    return {
        "pair_irreducible": {
            "commutator": [[str(value) for value in row] for row in pair_commutator],
            "commutator_determinant": str(_determinant(pair_commutator)),
        },
        "triple_irreducible": {
            "canonical_commutator": [[str(value) for value in row] for row in canonical],
            "breaker": [[str(value) for value in row] for row in breaker],
            "tau": str(_trace(_multiply(canonical, breaker))),
        },
        "transverse_reducible": {
            "omega": [str(value) for value in omega_transverse],
            "det_C_omega__omega": str(
                _determinant(
                    (
                        _apply(canonical, omega_transverse),
                        omega_transverse,
                    )
                )
            ),
        },
        "aligned_reducible": {
            "omega": [str(value) for value in omega_aligned],
            "C_omega": [str(value) for value in _apply(canonical, omega_aligned)],
        },
    }


def build_payload(root: Path) -> dict[str, Any]:
    context = torus._build_context(root)
    q_pairs = [list(pair) for pair in itertools.combinations(range(1, 5), 2)]
    symbolic = _symbolic_identities()
    examples = _branch_examples()
    actual_variables = [variable for variable in context.variables if variable != torus.Q5]

    gates = {
        "six_Q_pair_pivots": len(q_pairs) == 6,
        "actual_ON_transition_generators_are_131": len(actual_variables) == 131,
        "compiled_family_with_external_Q5_has_132_generators": len(context.variables) == 132,
        "symbolic_2x2_identities_hold": symbolic["all_zero_identity_checks"],
        "pair_irreducible_example_has_invertible_commutator": examples[
            "pair_irreducible"
        ]["commutator_determinant"]
        != "0",
        "triple_breaker_example_has_nonzero_tau": examples["triple_irreducible"][
            "tau"
        ]
        != "0",
        "transverse_example_has_nonzero_frame_determinant": examples[
            "transverse_reducible"
        ]["det_C_omega__omega"]
        != "0",
        "aligned_example_is_annihilated": examples["aligned_reducible"]["C_omega"]
        == ["0", "0"],
    }
    if not all(gates.values()):
        raise AssertionError(f"commutator branch-cover gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_binding": (
            "structural cover for Q-noncommutative occurrence-identification-ON "
            "models before imposing the full CPOBC/GC/MSR relation ideal"
        ),
        "input_artifacts": {
            relative: torus._sha256(root / relative)
            for relative in sorted((torus.REDUCTION_PATH, torus.EQ112_PATH))
        },
        "generator_inventory": {
            "actual_ON_transition_generators": len(actual_variables),
            "supplemental_cutoff_external_Q5": torus.Q5,
            "compiled_operator_family_size": len(context.variables),
            "tau_rule": (
                "use all 131 actual generators for finite reducibility; include "
                "Q5 as a separate tau branch when triangularising the supplemental "
                "Eq139 compiler family"
            ),
        },
        "pivot_cover": {
            "Q_pairs": q_pairs,
            "cover_reason": (
                "Q-noncommutativity means at least one of the six listed "
                "commutators is nonzero"
            ),
            "pivot_assumption": "C_ij=[Q_i,Q_j]!=0",
            "branch_invariants": {
                "determinant": "det(C_ij)",
                "transition_trace": "tau_ij,e=tr(C_ij*A_e)",
                "initial_frame": "d_ij=det(C_ij*Omega,Omega)",
            },
            "complete_branches_on_each_pivot": [
                {
                    "branch": "PAIR_IRREDUCIBLE",
                    "conditions": ["det(C_ij)!=0"],
                    "conclusion": "Q_i,Q_j have no common invariant line",
                },
                {
                    "branch": "TRIPLE_IRREDUCIBLE",
                    "conditions": [
                        "det(C_ij)=0",
                        "tau_ij,e!=0 for at least one compiled generator",
                    ],
                    "conclusion": "Q_i,Q_j,A_e have no common invariant line",
                },
                {
                    "branch": "TRANSVERSE_GLOBALLY_REDUCIBLE",
                    "conditions": [
                        "det(C_ij)=0",
                        "tau_ij,e=0 for every actual transition generator",
                        "d_ij!=0",
                    ],
                    "conclusion": (
                        "all actual transitions preserve L=ker(C_ij), while "
                        "Omega is transverse to L"
                    ),
                },
                {
                    "branch": "ALIGNED_GLOBALLY_REDUCIBLE",
                    "conditions": [
                        "det(C_ij)=0",
                        "tau_ij,e=0 for every actual transition generator",
                        "d_ij=0",
                    ],
                    "conclusion": (
                        "Omega lies in L and every reachable state remains in L; "
                        "all upper-triangular commutators are unreachable-sector-only"
                    ),
                },
            ],
        },
        "canonical_transverse_chart": {
            "basis_matrix": "S_ij=[C_ij*Omega,Omega]",
            "normalisation": ["S_ij^-1*Omega=e_2", "S_ij^-1*C_ij*S_ij=E_12"],
            "tau_formula": "tau_ij(X)=X_21",
            "global_reducibility_test": "X_21=0 for every generator X",
            "residual_conjugation_after_normalisation": "identity only",
            "upper_parameterisation": "A_e=b_e*[[r_e,z_e],[0,1]]",
            "product_law": "M(r,z)M(s,w)=M(r*s,z+r*w)",
            "inverse_law": "M(r,z)^-1=M(r^-1,-r^-1*z)",
            "Q_commutator": (
                "[Q_i,Q_j]=b_i*b_j*((r_i-1)z_j-(r_j-1)z_i)*E_12"
            ),
            "pivot_equation": "b_i*b_j*((r_i-1)z_j-(r_j-1)z_i)=1",
            "warning": (
                "det[Q_i,Q_j] is identically zero in this chart and cannot be "
                "used as its noncommutativity saturation"
            ),
        },
        "symbolic_certificate": symbolic,
        "nonempty_branch_examples": examples,
        "reachable_rank_boundary": (
            "The branch cover classifies invariant-line geometry only.  Reachable "
            "span rank two must still be imposed through endpoint-state minors; it "
            "does not follow from irreducibility or transversality alone."
        ),
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "This proves a complete four-way linear-algebra branch cover after "
            "choosing one nonzero Q commutator.  It does not show that any branch "
            "contains a CPOBC solution, does not close any branch, and is not an "
            "SR2-V terminal.  Supplemental Q5 reducibility must be tracked "
            "separately from the 131-generator finite transition family."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
