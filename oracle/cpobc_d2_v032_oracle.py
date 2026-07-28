"""Independent exact oracle for the v0.3.2 CPOBC d=2 audit.

This module deliberately does not import the production Phase-1 reduction
code.  It provides three narrowly scoped checks:

* symbolic 2x2 identities supporting the S1/S2/S3 partition of a commuting
  family ``R_2, R_3, R_4`` over an algebraically closed field of
  characteristic different from two;
* every admissible n<=4 index residual of paper Eqs. (120), (129), and (130)
  for the declared monomial family;
* an independently constructed semantic digest for the S3 antichain
  commutator consequence only.

The certificates are identities in symbolic polynomial/rational functions,
not evidence from finitely many sampled matrices.  They do not reduce the 641
compiled CPOBC relations, the MSR constraints, or the GC constraints.  The
remaining logical dependencies and those unassessed systems are listed
explicitly in each returned record.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from typing import Any

import sympy as sp

INDEX_SET = (1, 2, 3, 4)
R_INDEX_SET = (2, 3, 4)


def _exact(value: Any) -> str:
    """Return a deterministic exact expression, with no numeric evaluation."""

    return str(sp.factor(sp.cancel(sp.sympify(value))))


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [_exact(matrix[row, column]) for column in range(matrix.cols)] for row in range(matrix.rows)
    ]


def _is_zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.cancel(sp.expand(entry)) == 0 for entry in matrix)


def stable_json_sha256(value: Any) -> str:
    """Hash a canonical ASCII JSON encoding.

    This implementation is local to the oracle so that the G1 route shares no
    production digest helper.
    """

    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def eq120_to_commuting_r_certificate() -> dict[str, Any]:
    """Certify the k=1 Eq. (120) implication after clearing det(Q_1).

    For ``R_j = Q_1^{-1} Q_j``, the numerator of ``[R_n, R_m]`` is
    ``adj(Q_1)`` times the denominator-cleared Eq. (120) residual.  The
    returned zero matrix is a generic polynomial identity in all twelve
    matrix entries, rather than a pointwise sample.
    """

    q11, q12, q21, q22 = sp.symbols("q11 q12 q21 q22")
    n11, n12, n21, n22 = sp.symbols("n11 n12 n21 n22")
    m11, m12, m21, m22 = sp.symbols("m11 m12 m21 m22")

    q1 = sp.Matrix([[q11, q12], [q21, q22]])
    qn = sp.Matrix([[n11, n12], [n21, n22]])
    qm = sp.Matrix([[m11, m12], [m21, m22]])
    adj_q1 = sp.Matrix([[q22, -q12], [-q21, q11]])
    det_q1 = sp.expand(q1.det())

    eq120_cleared = qn * adj_q1 * qm - qm * adj_q1 * qn
    r_commutator_numerator = adj_q1 * qn * adj_q1 * qm - adj_q1 * qm * adj_q1 * qn
    certificate_residual = sp.expand(r_commutator_numerator - adj_q1 * eq120_cleared)

    return {
        "identity": ("numerator([Q_1^-1*Q_n,Q_1^-1*Q_m]) = adj(Q_1)*cleared_residual(Eq.120,k=1)"),
        "det_Q1": _exact(det_q1),
        "assumption": "det(Q_1) != 0",
        "cleared_eq120_residual": _matrix_record(eq120_cleared),
        "r_commutator_numerator": _matrix_record(r_commutator_numerator),
        "certificate_residual": _matrix_record(certificate_residual),
        "identity_verified": _is_zero_matrix(certificate_residual),
        "consequence": ("For each distinct m,n in {2,3,4}, Eq.(120) with k=1 implies [R_n,R_m]=0."),
        "scope_boundary": (
            "This checks the algebraic implication from Eq.(120); it does not "
            "derive Eq.(120) from the full compiled transition system."
        ),
    }


def _single_matrix_discriminant_certificate() -> dict[str, Any]:
    a, b, c, d = sp.symbols("a b c d")
    matrix = sp.Matrix([[a, b], [c, d]])
    identity = sp.eye(2)
    trace = sp.expand(matrix.trace())
    determinant = sp.expand(matrix.det())
    discriminant = sp.expand(trace**2 - 4 * determinant)
    eigenvalue = trace / 2
    nilpotent_part = matrix - eigenvalue * identity
    cayley_hamilton_residual = sp.expand(nilpotent_part**2 - discriminant * identity / 4)

    return {
        "generic_matrix": _matrix_record(matrix),
        "trace": _exact(trace),
        "determinant": _exact(determinant),
        "characteristic_discriminant": _exact(discriminant),
        "repeated_eigenvalue": _exact(eigenvalue),
        "nilpotent_part": _matrix_record(nilpotent_part),
        "identity": "(A-tr(A)/2*I)^2 = discriminant(A)/4*I",
        "certificate_residual": _matrix_record(cayley_hamilton_residual),
        "identity_verified": _is_zero_matrix(cayley_hamilton_residual),
        "consequences": [
            "discriminant != 0 gives two distinct eigenvalues over the base field",
            "discriminant = 0 gives a square-zero nilpotent part",
            "the square-zero part is zero exactly when A is scalar",
        ],
    }


def _s1_centralizer_certificate() -> dict[str, Any]:
    alpha, beta = sp.symbols("alpha beta")
    x, y, z, w = sp.symbols("x y z w")
    inverse_gap = sp.symbols("inverse_gap")

    pivot = sp.diag(alpha, beta)
    candidate = sp.Matrix([[x, y], [z, w]])
    commutator = pivot * candidate - candidate * pivot
    gap_relation = sp.expand(inverse_gap * (alpha - beta) - 1)

    # Explicit ideal-membership witnesses on the open chart alpha != beta.
    y_membership = sp.expand(inverse_gap * commutator[0, 1] - y * gap_relation - y)
    z_membership = sp.expand(-inverse_gap * commutator[1, 0] - z * gap_relation - z)

    diagonal = sp.diag(x, w)
    return {
        "pivot_normal_form": _matrix_record(pivot),
        "generic_centralizer_candidate": _matrix_record(candidate),
        "commutator": _matrix_record(commutator),
        "open_chart_relation": _exact(gap_relation),
        "ideal_membership_residuals": {
            "off_diagonal_0_1": _exact(y_membership),
            "off_diagonal_1_0": _exact(z_membership),
        },
        "membership_verified": y_membership == 0 and z_membership == 0,
        "centralizer_normal_form": _matrix_record(diagonal),
        "centralizer_form_commutes": _is_zero_matrix(pivot * diagonal - diagonal * pivot),
        "family_consequence": (
            "A commuting family containing a distinct-eigenvalue pivot is "
            "simultaneously diagonal in an eigenbasis of that pivot."
        ),
        "residual_gauge_group": (
            "invertible diagonal matrices; include the basis swap when the "
            "two eigenline labels are not ordered"
        ),
    }


def _nilpotent_jordan_basis_certificate() -> dict[str, Any]:
    p, q, r = sp.symbols("p q r")
    u, v = sp.symbols("u v")

    nilpotent = sp.Matrix([[p, q], [r, -p]])
    vector = sp.Matrix([u, v])
    nilpotence_polynomial = sp.expand(p**2 + q * r)
    jordan = sp.Matrix([[0, 1], [0, 0]])
    basis = sp.Matrix.hstack(nilpotent * vector, vector)
    intertwining_residual = sp.expand(nilpotent * basis - basis * jordan)
    expected = sp.Matrix.hstack(
        nilpotence_polynomial * vector,
        sp.zeros(2, 1),
    )
    certificate_residual = sp.expand(intertwining_residual - expected)

    return {
        "trace_zero_nilpotent_candidate": _matrix_record(nilpotent),
        "nilpotence_polynomial": _exact(nilpotence_polynomial),
        "candidate_basis_P": _matrix_record(basis),
        "jordan_N": _matrix_record(jordan),
        "identity": "N*P-P*J = [(p^2+q*r)*v, 0]",
        "certificate_residual": _matrix_record(certificate_residual),
        "identity_verified": _is_zero_matrix(certificate_residual),
        "basis_determinant": _exact(basis.det()),
        "logical_side_condition": (
            "For nonzero square-zero N choose v with N*v != 0. Then "
            "columns (N*v,v) are independent, so det(P) != 0."
        ),
    }


def _s2_centralizer_certificate() -> dict[str, Any]:
    x, y, z, w = sp.symbols("x y z w")
    candidate = sp.Matrix([[x, y], [z, w]])
    nilpotent = sp.Matrix([[0, 1], [0, 0]])
    commutator = nilpotent * candidate - candidate * nilpotent
    normal_form = x * sp.eye(2) + y * nilpotent
    reconstruction_residual = sp.expand(
        candidate - normal_form - sp.Matrix([[0, 0], [commutator[0, 0], commutator[0, 1]]])
    )

    stabilizer_alpha, stabilizer_beta = sp.symbols("stabilizer_alpha stabilizer_beta")
    stabilizer = stabilizer_alpha * sp.eye(2) + stabilizer_beta * nilpotent

    return {
        "common_nilpotent_normal_form": _matrix_record(nilpotent),
        "generic_centralizer_candidate": _matrix_record(candidate),
        "commutator": _matrix_record(commutator),
        "centralizer_normal_form": _matrix_record(normal_form),
        "reconstruction_certificate_residual": _matrix_record(reconstruction_residual),
        "reconstruction_verified": _is_zero_matrix(reconstruction_residual),
        "normal_form_commutes": _is_zero_matrix(nilpotent * normal_form - normal_form * nilpotent),
        "normal_form_discriminant": _exact(normal_form.trace() ** 2 - 4 * normal_form.det()),
        "family_consequence": (
            "If all family members have repeated eigenvalues and one is "
            "nonscalar, choose its nonzero square-zero part N. Every commuting "
            "member is lambda_i*I+mu_i*N in the same basis."
        ),
        "residual_gauge_group": {
            "form": _matrix_record(stabilizer),
            "determinant": _exact(stabilizer.det()),
            "invertibility_condition": "stabilizer_alpha != 0",
        },
        "jordan_basis_certificate": _nilpotent_jordan_basis_certificate(),
    }


def _s3_scalar_certificate() -> dict[str, Any]:
    scalar, x, y, z, w = sp.symbols("scalar x y z w")
    scalar_matrix = scalar * sp.eye(2)
    arbitrary = sp.Matrix([[x, y], [z, w]])
    commutator = scalar_matrix * arbitrary - arbitrary * scalar_matrix

    return {
        "normal_form": _matrix_record(scalar_matrix),
        "commutator_with_generic_matrix": _matrix_record(commutator),
        "centralizer_is_full_M2": _is_zero_matrix(commutator),
        "residual_gauge_group": "GL(2)",
        "family_consequence": (
            "If every R_n is scalar, R_n=lambda_n*I and therefore Q_n=lambda_n*Q_1."
        ),
        "scope_boundary": (
            "This proves antichain Q-commutativity only. It does not show that "
            "all transition operators in a CPOBC representation commute."
        ),
    }


def commuting_family_strata_certificate() -> dict[str, Any]:
    """Return symbolic lemmas supporting the exhaustive S1/S2/S3 split."""

    truth_table = [
        {
            "exists_distinct_eigenvalue_member": True,
            "exists_nonscalar_member": True,
            "stratum": "S1",
            "valid": True,
        },
        {
            "exists_distinct_eigenvalue_member": True,
            "exists_nonscalar_member": False,
            "stratum": None,
            "valid": False,
            "reason": "a distinct-eigenvalue matrix cannot be scalar",
        },
        {
            "exists_distinct_eigenvalue_member": False,
            "exists_nonscalar_member": True,
            "stratum": "S2",
            "valid": True,
        },
        {
            "exists_distinct_eigenvalue_member": False,
            "exists_nonscalar_member": False,
            "stratum": "S3",
            "valid": True,
        },
    ]

    eq120 = eq120_to_commuting_r_certificate()
    dichotomy = _single_matrix_discriminant_certificate()
    s1 = _s1_centralizer_certificate()
    s2 = _s2_centralizer_certificate()
    s3 = _s3_scalar_certificate()
    checked_flags = [
        eq120["identity_verified"],
        dichotomy["identity_verified"],
        s1["membership_verified"],
        s1["centralizer_form_commutes"],
        s2["reconstruction_verified"],
        s2["normal_form_commutes"],
        s2["jordan_basis_certificate"]["identity_verified"],
        s3["centralizer_is_full_M2"],
    ]

    return {
        "scope": {
            "family": ["R_2", "R_3", "R_4"],
            "dimension": 2,
            "base_field": ("algebraically closed, characteristic != 2 (the project target is C)"),
            "assumptions": [
                "Q_1 is invertible",
                "the relevant Eq.(120) k=1 instances hold",
                "R_n=Q_1^-1*Q_n",
            ],
            "method": (
                "generic symbolic polynomial identities and explicit "
                "ideal-membership witnesses; no finite matrix sampling"
            ),
        },
        "eq120_to_pairwise_commutation": eq120,
        "single_matrix_dichotomy": dichotomy,
        "S1_distinct_eigenvalue_pivot": s1,
        "S2_common_nilpotent_direction": s2,
        "S3_all_scalar": s3,
        "logical_partition": {
            "truth_table": truth_table,
            "valid_rows_are_unique": True,
            "exhaustive_predicate": ("D or ((not D) and N) or ((not D) and (not N))"),
            "definitions": {
                "D": "some R_n has nonzero characteristic discriminant",
                "N": "some R_n is nonscalar",
            },
        },
        "all_symbolic_identities_verified": all(checked_flags),
        "certificate_kind": "SYMBOLIC_IDENTITY_NOT_FINITE_SAMPLE",
        "unproved_or_external_steps": [
            (
                "Standard 2x2 linear algebra over an algebraically closed "
                "field: nonzero discriminant implies diagonalizability."
            ),
            (
                "For a nonzero linear map N there exists v with N*v != 0; "
                "for square-zero N, (N*v,v) is then a basis. The returned "
                "intertwining identity checks the resulting Jordan form."
            ),
            (
                "No claim here establishes that the full 641-relation "
                "compiled CPOBC system, MSR, GC, or every transition "
                "invertibility condition reduces to these antichain lemmas."
            ),
        ],
    }


def _monomial_family() -> tuple[
    dict[int, sp.Matrix],
    dict[int, sp.Matrix],
    dict[str, sp.Symbol],
]:
    q1, a2, b2, a3, b3, a4, b4 = sp.symbols(
        "q1 a2 b2 a3 b3 a4 b4",
        nonzero=True,
    )
    symbols = {
        "q1": q1,
        "a2": a2,
        "b2": b2,
        "a3": a3,
        "b3": b3,
        "a4": a4,
        "b4": b4,
    }
    x_pauli = sp.Matrix([[0, 1], [1, 0]])
    q_matrices = {
        1: q1 * x_pauli,
        2: x_pauli * sp.diag(a2, b2),
        3: x_pauli * sp.diag(a3, b3),
        4: x_pauli * sp.diag(a4, b4),
    }
    inverses = {
        1: sp.Matrix([[0, 1 / q1], [1 / q1, 0]]),
        2: sp.Matrix([[0, 1 / a2], [1 / b2, 0]]),
        3: sp.Matrix([[0, 1 / a3], [1 / b3, 0]]),
        4: sp.Matrix([[0, 1 / a4], [1 / b4, 0]]),
    }
    return q_matrices, inverses, symbols


def _residual_record(
    indices: tuple[int, ...],
    residual: sp.MatrixBase,
) -> dict[str, Any]:
    simplified = residual.applyfunc(lambda entry: sp.factor(sp.cancel(entry)))
    return {
        "indices": list(indices),
        "residual": _matrix_record(simplified),
        "is_zero": _is_zero_matrix(simplified),
    }


def monomial_family_all_index_certificate() -> dict[str, Any]:
    """Check all n<=4 admissible residuals for Eqs. (120), (129), (130)."""

    q_matrices, inverses, symbols = _monomial_family()

    eq120_indices = sorted(
        (n, k, m) for n, k, m in itertools.product(INDEX_SET, repeat=3) if m != n and k < min(m, n)
    )
    eq120_residuals = [
        _residual_record(
            indices,
            q_matrices[indices[0]] * inverses[indices[1]] * q_matrices[indices[2]]
            - q_matrices[indices[2]] * inverses[indices[1]] * q_matrices[indices[0]],
        )
        for indices in eq120_indices
    ]

    # Paper Cor. 3.8 requires four distinct indices.  At n<=4 this is every
    # ordered permutation of (1,2,3,4).  Tuple order below is (m,n,l,k).
    eq129_indices = sorted(itertools.permutations(INDEX_SET, 4))
    eq129_residuals = []
    for indices in eq129_indices:
        m, n, ell, k = indices
        first = q_matrices[m] * inverses[n]
        second = q_matrices[ell] * inverses[k]
        eq129_residuals.append(_residual_record(indices, first * second - second * first))

    eq130_first = q_matrices[1] * inverses[2]
    eq130_second = inverses[1] * q_matrices[2]
    eq130_residual = _residual_record(
        (1, 2),
        eq130_first * eq130_second - eq130_second * eq130_first,
    )

    inverse_checks = {
        str(index): {
            "left": _matrix_record(q_matrices[index] * inverses[index] - sp.eye(2)),
            "right": _matrix_record(inverses[index] * q_matrices[index] - sp.eye(2)),
            "verified": _is_zero_matrix(q_matrices[index] * inverses[index] - sp.eye(2))
            and _is_zero_matrix(inverses[index] * q_matrices[index] - sp.eye(2)),
        }
        for index in INDEX_SET
    }

    q1_q2_commutator = q_matrices[1] * q_matrices[2] - q_matrices[2] * q_matrices[1]
    q2_q3_commutator = q_matrices[2] * q_matrices[3] - q_matrices[3] * q_matrices[2]

    all_residuals = eq120_residuals + eq129_residuals + [eq130_residual]
    return {
        "family": {
            "Q_1": "q1*sigma_x",
            "Q_n": "sigma_x*diag(a_n,b_n), n=2,3,4",
            "matrices": {str(index): _matrix_record(q_matrices[index]) for index in INDEX_SET},
            "nonzero_parameter_assumptions": sorted(symbols),
            "field": "Q(q1,a2,b2,a3,b3,a4,b4)",
        },
        "inverse_certificates": inverse_checks,
        "equation_120": {
            "index_tuple_order": ["n", "k", "m"],
            "admissibility": "m != n and k < min(m,n)",
            "expected_count": 8,
            "residuals": eq120_residuals,
            "all_zero": all(item["is_zero"] for item in eq120_residuals),
        },
        "equation_129": {
            "index_tuple_order": ["m", "n", "ell", "k"],
            "admissibility": "m,n,ell,k pairwise distinct in {1,2,3,4}",
            "expected_count": 24,
            "residuals": eq129_residuals,
            "all_zero": all(item["is_zero"] for item in eq129_residuals),
        },
        "equation_130": {
            "indices": [1, 2],
            "residual": eq130_residual,
            "all_zero": eq130_residual["is_zero"],
        },
        "noncommutativity_witnesses": {
            "[Q_1,Q_2]": {
                "matrix": _matrix_record(q1_q2_commutator),
                "nonzero_condition": "q1*(a2-b2) != 0",
            },
            "[Q_2,Q_3]": {
                "matrix": _matrix_record(q2_q3_commutator),
                "nonzero_condition": "a3*b2-a2*b3 != 0",
            },
        },
        "all_index_residuals_zero": all(item["is_zero"] for item in all_residuals),
        "certificate_kind": ("SYMBOLIC_RATIONAL_FUNCTION_IDENTITIES_NOT_PARAMETER_SAMPLES"),
        "scope_boundary": [
            (
                "The certificate covers every admissible n<=4 index tuple of "
                "paper Eqs. (120), (129), and (130) for this family."
            ),
            (
                "It does not check the 641 compiled CPOBC relations, the 24 "
                "MSR constraints, GC, or construct a vector measure."
            ),
            (
                "It is therefore a necessary-relation witness, not a CPOBC "
                "representation certificate."
            ),
        ],
    }


def s3_semantic_descriptor() -> dict[str, Any]:
    """Build the canonical, deliberately limited S3 comparison descriptor."""

    return {
        "stratum": "S3_SCALAR",
        "substitution": {
            "Q_2": "lambda_2*Q_1",
            "Q_3": "lambda_3*Q_1",
            "Q_4": "lambda_4*Q_1",
        },
        "checked_claim": "ANTICHAIN_Q_COMMUTATORS_ZERO_ONLY",
        "commutator_pairs": [
            [1, 2],
            [1, 3],
            [1, 4],
            [2, 3],
            [2, 4],
            [3, 4],
        ],
        "full_transition_system_status": ("UNASSESSED_GENERATOR_REDUCTION_INCOMPLETE"),
    }


def independent_s3_digest_certificate() -> dict[str, Any]:
    """Compute the S3 digest without importing or calling Phase-1 code."""

    q11, q12, q21, q22 = sp.symbols("q11 q12 q21 q22")
    lambda2, lambda3, lambda4 = sp.symbols("lambda_2 lambda_3 lambda_4")
    q1 = sp.Matrix([[q11, q12], [q21, q22]])
    q_matrices = {
        1: q1,
        2: lambda2 * q1,
        3: lambda3 * q1,
        4: lambda4 * q1,
    }
    pairs = itertools.combinations(INDEX_SET, 2)
    residuals = []
    for left, right in pairs:
        residual = q_matrices[left] * q_matrices[right] - q_matrices[right] * q_matrices[left]
        residuals.append(_residual_record((left, right), residual))

    descriptor = s3_semantic_descriptor()
    return {
        "semantic_descriptor": descriptor,
        "semantic_descriptor_sha256": stable_json_sha256(descriptor),
        "symbolic_commutator_residuals": residuals,
        "all_checked_commutators_zero": all(item["is_zero"] for item in residuals),
        "method": (
            "standalone generic 2x2 SymPy substitution followed by a local "
            "canonical-JSON SHA-256 implementation"
        ),
        "shared_production_code_paths": [],
        "comparison_scope": "S3_ANTICHAIN_Q_COMMUTATORS_ONLY",
        "g1_status": "LIMITED_DIGEST_ROUTE_NOT_FULL_PHASE1_REPRODUCTION",
        "unresolved_components": [
            "production Phase-1 occurrence-variable reduction",
            "641 compiled CPOBC relations",
            "24 MSR constraints",
            "GC constraints",
            "two-sided transition invertibility",
            "non-antichain transition operators",
        ],
    }


def build_oracle_certificate() -> dict[str, Any]:
    """Build the complete JSON-safe oracle result."""

    strata = commuting_family_strata_certificate()
    monomial = monomial_family_all_index_certificate()
    s3_digest = independent_s3_digest_certificate()
    return {
        "schema_version": "final-theory-cpobc-d2-oracle-v0.3.2",
        "implementation_role": "INDEPENDENT_PHASE2_AND_LIMITED_G1_ORACLE",
        "strata_certificate": strata,
        "monomial_family_certificate": monomial,
        "independent_s3_digest_certificate": s3_digest,
        "passed": (
            strata["all_symbolic_identities_verified"]
            and monomial["all_index_residuals_zero"]
            and s3_digest["all_checked_commutators_zero"]
        ),
        "verdict_boundary": (
            "Passing this oracle does not imply existence or nonexistence of a "
            "full d=2 CPOBC representation."
        ),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            build_oracle_certificate(),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
