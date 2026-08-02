"""Fail-closed Eq. (120) Schur-chart obligations for transverse SR2-V.

The global common-core unit minor reduces the transverse weak/weak problem to
five Schur columns ``Q1,...,Q5``.  Source-native Eq. (120) further controls the
first four columns.  This module computes the exact localized normal forms on
the three non-aligned ratio charts and on their aligned remainder.

It deliberately does not select repair rows.  Its conclusion is the precise
row-module membership problem a later certificate must solve, including the
external ``Q5`` column.  In particular, a finite rank scout, a nonzero minor at
one point, or a multivariate gcd equal to one is not promoted to a proof.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_transverse_base_cover_ablation_v042 as base_cover
from universe_lab.final_theory import sr2v_transverse_common_core_unit_minor_v042 as unit_minor

RESULT_PATH = "results/v0.4.2_sr2v_transverse_eq120_schur_chart_obligations.json"
SCHEMA = "final-theory-v042-sr2v-transverse-eq120-schur-chart-obligations-v1"
VERDICT = "SR2V_TRANSVERSE_EQ120_SCHUR_CHART_OBLIGATIONS_CERTIFIED_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_REPAIR_ROW_MODULE_MEMBERSHIP_UNRESOLVED"


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


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _digest(semantic)


def _normal(expression: sp.Expr) -> sp.Expr:
    return sp.factor(sp.cancel(expression))


def _is_zero(expression: sp.Expr) -> bool:
    return _normal(expression) == 0


def _chart_obligation_certificate() -> dict[str, Any]:
    b = tuple(sp.symbols("b1:5", nonzero=True))
    r = tuple(sp.symbols("r1:5", nonzero=True))
    x = tuple(sp.symbols("x1:5"))
    rho = tuple(sp.symbols("rho1:6"))
    h, w, q5 = sp.symbols("h w q5")

    delta = tuple(b[index] * (r[index] - 1) for index in range(4))
    visible = tuple(b[index] / b[0] for index in range(4))
    g = {index: r[index - 1] - r[0] for index in range(2, 5)}
    z = tuple(x[index] / b[index] for index in range(4))
    parametrized_x = tuple(delta[index] * h + visible[index] * w for index in range(4))
    parametrized_z = tuple(
        _normal(parametrized_x[index] / b[index]) for index in range(4)
    )

    def eq120(left: int, right: int, values: tuple[sp.Expr, ...]) -> sp.Expr:
        left_g = r[left - 1] - r[0]
        right_g = r[right - 1] - r[0]
        return sp.expand(
            left_g * (values[right - 1] - values[0])
            - right_g * (values[left - 1] - values[0])
        )

    forward_eq120 = {
        f"E{left}{right}": str(_normal(eq120(left, right, parametrized_z)))
        for left, right in ((2, 3), (2, 4), (3, 4))
    }
    if set(forward_eq120.values()) != {"0"}:
        raise AssertionError("the Eq120 chart parametrisation changed")

    chart_records: list[dict[str, Any]] = []
    for pivot in range(2, 5):
        pivot_g = g[pivot]
        chart_h = (z[pivot - 1] - z[0]) / pivot_g
        chart_w = b[0] * (z[0] - (r[0] - 1) * chart_h)
        reconstruction_checks = {}
        for index in range(1, 5):
            reconstructed = delta[index - 1] * chart_h + visible[index - 1] * chart_w
            numerator_difference = _normal(
                pivot_g * (x[index - 1] - reconstructed)
                - b[index - 1] * eq120(pivot, index, z)
            )
            reconstruction_checks[f"Q{index}"] = str(numerator_difference)
        if set(reconstruction_checks.values()) != {"0"}:
            raise AssertionError(f"the U{pivot} reverse reconstruction changed")

        commutator = _normal(
            delta[0] * parametrized_x[pivot - 1]
            - delta[pivot - 1] * parametrized_x[0]
        )
        expected_commutator = -b[pivot - 1] * pivot_g * w
        if not _is_zero(commutator - expected_commutator):
            raise AssertionError(f"the U{pivot} commutator factor changed")

        chart_records.append(
            {
                "chart": f"U{pivot}=D(g{pivot})",
                "localized_unit": f"g{pivot}=r{pivot}-r1",
                "parameter_reconstruction": {
                    "h": f"(z{pivot}-z1)/g{pivot}",
                    "w": "b1*(z1-(r1-1)*h)",
                    "x_Q1_through_Q4": "delta*h+(b/b1)*w",
                    "reverse_numerator_identity_checks": reconstruction_checks,
                },
                "target_commutator": f"c1{pivot}",
                "target_commutator_on_the_chart_kernel": str(expected_commutator),
                "commutativity_obstruction_coordinate": "w",
                "unit_equivalence": (
                    f"on D(g{pivot}), b{pivot} and g{pivot} are units, so "
                    f"c1{pivot}=0 iff w=0"
                ),
            }
        )

    all_commutator_checks = {}
    for left in range(1, 5):
        for right in range(left + 1, 5):
            commutator = _normal(
                delta[left - 1] * parametrized_x[right - 1]
                - delta[right - 1] * parametrized_x[left - 1]
            )
            expected = _normal(
                b[left - 1]
                * b[right - 1]
                / b[0]
                * (r[left - 1] - r[right - 1])
                * w
            )
            difference = _normal(commutator - expected)
            all_commutator_checks[f"c{left}{right}"] = str(difference)
    if set(all_commutator_checks.values()) != {"0"}:
        raise AssertionError("the six chart commutator identities changed")

    row_value = sum(rho[index] * parametrized_x[index] for index in range(4)) + rho[4] * q5
    row_a = _normal(sum(rho[index] * delta[index] for index in range(4)))
    row_b = _normal(sum(rho[index] * visible[index] for index in range(4)))
    row_c = rho[4]
    row_restriction_difference = _normal(row_value - (row_a * h + row_b * w + row_c * q5))
    if row_restriction_difference != 0:
        raise AssertionError("the generic Schur-row restriction changed")

    reference_ar, reference_br, reference_as, reference_bs = sp.symbols(
        "reference_A_r reference_B_r reference_A_s reference_B_s"
    )
    reference_base_minor = reference_ar * reference_bs - reference_as * reference_br
    reference_records = []
    for reference in range(1, 5):
        reference_visible = tuple(value / b[reference - 1] for value in b)
        reference_w = b[reference - 1] / b[0] * w
        reference_x = tuple(
            delta[index] * h + reference_visible[index] * reference_w
            for index in range(4)
        )
        parametrisation_differences = [
            _normal(reference_x[index] - parametrized_x[index]) for index in range(4)
        ]
        reference_b = _normal(
            sum(rho[index] * reference_visible[index] for index in range(4))
        )
        expected_reference_b = _normal(b[0] / b[reference - 1] * row_b)
        b_difference = _normal(reference_b - expected_reference_b)
        reference_scale = b[0] / b[reference - 1]
        reference_pair_minor = _normal(
            reference_ar * reference_scale * reference_bs
            - reference_as * reference_scale * reference_br
        )
        pair_minor_difference = _normal(
            reference_pair_minor - reference_scale * reference_base_minor
        )
        if (
            any(value != 0 for value in parametrisation_differences)
            or b_difference != 0
            or pair_minor_difference != 0
        ):
            raise AssertionError("the visible-reference invariance changed")
        reference_records.append(
            {
                "reference": f"Q{reference}",
                "obstruction_coordinate": f"w_{reference}=(b{reference}/b1)*w_1",
                "B_scaling": f"B^({reference})=(b1/b{reference})*B^(1)",
                "parametrisation_difference_checks": [
                    str(value) for value in parametrisation_differences
                ],
                "B_scaling_difference": str(b_difference),
                "pair_minor_scaling": f"D_rs^({reference})=(b1/b{reference})*D_rs^(1)",
                "pair_minor_scaling_difference": str(pair_minor_difference),
                "scaling_is_a_declared_unit": True,
            }
        )

    ar, br, as_, bs = sp.symbols("A_r B_r A_s B_s")
    ell_r = ar * h + br * w
    ell_s = as_ * h + bs * w
    pair_minor = ar * bs - as_ * br
    pair_identity = _normal(ar * ell_s - as_ * ell_r - pair_minor * w)
    if pair_identity != 0:
        raise AssertionError("the Q5-free pair-minor identity changed")

    generic_entries = sp.symbols("A1 B1 C1 A2 B2 C2 A3 B3 C3")
    generic_three = sp.Matrix(3, 3, generic_entries)
    unknown_three = sp.Matrix([h, w, q5])
    equations_three = generic_three * unknown_three
    determinant_three = sp.factor(generic_three.det())
    adjugate_w_identity = _normal(
        (generic_three.adjugate() * equations_three)[1] - determinant_three * w
    )
    if adjugate_w_identity != 0:
        raise AssertionError("the three-row adjugate identity changed")

    q5_counterexample = sp.Matrix([[1, 0, 1], [0, 1, 1]])
    target_w = sp.Matrix([[0, 1, 0]])
    q5_kernel = q5_counterexample.nullspace()
    if (
        q5_counterexample[:, :2].det() != 1
        or q5_counterexample.rank() != 2
        or q5_counterexample.col_join(target_w).rank() != 3
        or len(q5_kernel) != 1
    ):
        raise AssertionError("the Q5 fail-closed counterexample changed")

    u, v = sp.symbols("u v", nonzero=True)
    gcd_example = sp.gcd(u - 1, v - 1)
    groebner_example = sp.groebner([u - 1, v - 1], u, v, domain=sp.QQ)
    groebner_contains_one = any(poly.as_expr() == 1 for poly in groebner_example.polys)
    if gcd_example != 1 or groebner_contains_one:
        raise AssertionError("the gcd-versus-unit-ideal counterexample changed")

    return {
        "normalization": {
            "diagonal_units": "b_i",
            "ratios": "r_i=a_i/b_i",
            "upper_right_coordinates": "x_i=b_i*z_i",
            "spectral_difference": "delta_i=b_i*(r_i-1)",
            "ratio_differences": {f"g{index}": f"r{index}-r1" for index in range(2, 5)},
            "visible_vector": "v_i=b_i/b1",
        },
        "Eq120_rows": {
            "formula": "E_ij=g_i*(z_j-z1)-g_j*(z_i-z1)",
            "forward_parametrisation_checks": forward_eq120,
        },
        "three_non_aligned_charts": chart_records,
        "all_six_commutators_on_the_chart_kernel": {
            "formula": "c_ij=(b_i*b_j/b1)*(r_i-r_j)*w",
            "symbolic_difference_checks": all_commutator_checks,
        },
        "generic_Schur_row_restriction": {
            "row": "rho=(rho1,rho2,rho3,rho4,rho5)",
            "A": str(row_a),
            "B": str(row_b),
            "C": str(row_c),
            "restricted_equation": "A*h+B*w+C*q5",
            "symbolic_difference": str(row_restriction_difference),
        },
        "visible_reference_invariance": {
            "records": reference_records,
            "conclusion": (
                "changing the visible-vector reference rescales B and every AB pair "
                "minor by a declared diagonal unit; Q2/Q3/Q4 relabeling creates no new "
                "repair divisor or chart"
            ),
        },
        "exact_localized_obligation": {
            "ring_on_Uk": "S_k=R[g_k^-1] with every declared base unit already inverted",
            "restriction_matrix": "T_k has rows (A_r,B_r,C_r) for all Schur(M0) rows",
            "necessary_and_sufficient_condition": (
                "e_w=(0,1,0) belongs to Row_{S_k}(T_k); equivalently every "
                "Schur-kernel vector (h,w,q5) has w=0"
            ),
            "direct_certificate": "exhibit coefficients p_r in S_k with sum p_r*(A_r,B_r,C_r)=e_w",
            "Q5_free_pair_sufficient_condition": {
                "premise": "C_r=C_s=0",
                "minor": "D_rs=A_r*B_s-A_s*B_r",
                "identity_difference": str(pair_identity),
                "identity": "A_r*ell_s-A_s*ell_r=D_rs*w",
                "required_unit_test": "D_rs is a unit in S_k",
            },
            "three_row_sufficient_condition": {
                "minor": "det([[A_i,B_i,C_i]]_{i=1}^3)",
                "adjugate_w_identity_difference": str(adjugate_w_identity),
                "required_unit_test": "the 3x3 determinant is a unit in S_k",
            },
            "covered_minor_family_condition": (
                "for an ideal I of valid repair minors, require I*S_k=S_k; equivalently "
                "certify a Bezout identity after localization, or (I:g_k^infinity)=R "
                "after the declared base units are inverted"
            ),
        },
        "Q5_fail_closed_audit": {
            "naive_rows_ABC": [[1, 0, 1], [0, 1, 1]],
            "AB_minor": "1",
            "row_rank": 2,
            "rank_after_adjoining_e_w": 3,
            "kernel_generator_h_w_q5": [str(value) for value in q5_kernel[0]],
            "conclusion": (
                "a unit AB minor does not isolate w when either selected row has a Q5 "
                "coefficient; require C=0 or a genuine three-column module identity"
            ),
        },
        "gcd_fail_closed_audit": {
            "ring": "QQ[u^+-1,v^+-1]",
            "polynomials": ["u-1", "v-1"],
            "gcd": str(gcd_example),
            "common_torus_zero": ["u=1", "v=1"],
            "Groebner_basis_contains_one": groebner_contains_one,
            "conclusion": "multivariate gcd 1 is not a unit-ideal or cover certificate",
        },
    }


def _aligned_obligation_certificate() -> dict[str, Any]:
    b = tuple(sp.symbols("b1:5", nonzero=True))
    rho = tuple(sp.symbols("rho1:6"))
    f = sp.symbols("f")
    h, w2, w3, w4, q5 = sp.symbols("h w2 w3 w4 q5")
    aligned_x = (
        b[0] * h,
        b[1] * (h + w2),
        b[2] * (h + w3),
        b[3] * (h + w4),
    )
    aligned_delta = tuple(f * value for value in b)
    obstruction_coordinates = (w2, w3, w4)

    commutator_checks = {}
    for index in range(2, 5):
        commutator = _normal(
            aligned_delta[0] * aligned_x[index - 1]
            - aligned_delta[index - 1] * aligned_x[0]
        )
        expected = f * b[0] * b[index - 1] * obstruction_coordinates[index - 2]
        difference = _normal(commutator - expected)
        commutator_checks[f"c1{index}"] = str(difference)
    if set(commutator_checks.values()) != {"0"}:
        raise AssertionError("the aligned commutator identities changed")

    aligned_row = sum(rho[index] * aligned_x[index] for index in range(4)) + rho[4] * q5
    aligned_a = _normal(sum(rho[index] * b[index] for index in range(4)))
    aligned_b = tuple(rho[index] * b[index] for index in range(1, 4))
    aligned_c = rho[4]
    aligned_target = (
        aligned_a * h
        + aligned_b[0] * w2
        + aligned_b[1] * w3
        + aligned_b[2] * w4
        + aligned_c * q5
    )
    row_difference = _normal(aligned_row - aligned_target)
    if row_difference != 0:
        raise AssertionError("the aligned Schur-row restriction changed")

    quotient_entries = sp.symbols("B22 B23 B24 B32 B33 B34 B42 B43 B44")
    quotient_matrix = sp.Matrix(3, 3, quotient_entries)
    quotient_unknown = sp.Matrix([w2, w3, w4])
    quotient_equations = quotient_matrix * quotient_unknown
    quotient_adjugate_difference = quotient_matrix.adjugate() * quotient_equations - (
        quotient_matrix.det() * quotient_unknown
    )
    if any(_normal(value) != 0 for value in quotient_adjugate_difference):
        raise AssertionError("the aligned quotient-minor identity changed")

    r = tuple(sp.symbols("r1:5"))
    g = (r[1] - r[0], r[2] - r[0], r[3] - r[0])
    partition_identities = [
        _normal((r[index] - 1) - ((r[0] - 1) + g[index - 1]))
        for index in range(1, 4)
    ]
    if any(value != 0 for value in partition_identities):
        raise AssertionError("the four-locus partition identity changed")

    automatic_commutators = {}
    arbitrary_x = tuple(sp.symbols("x1:5"))
    for left in range(1, 5):
        for right in range(left + 1, 5):
            value = _normal(0 * arbitrary_x[right - 1] - 0 * arbitrary_x[left - 1])
            automatic_commutators[f"c{left}{right}"] = str(value)
    if set(automatic_commutators.values()) != {"0"}:
        raise AssertionError("the f=0 automatic-safe remainder changed")

    return {
        "locus": "L=V(g2,g3,g4) intersect D(f), with f=r1-1",
        "Eq120_effect": "all three exterior rows vanish identically on g2=g3=g4=0",
        "spectral_difference": "delta=f*b",
        "parameterisation": {
            "Q1": "x1=b1*h",
            "Q2": "x2=b2*(h+w2)",
            "Q3": "x3=b3*(h+w3)",
            "Q4": "x4=b4*(h+w4)",
            "Q5": "q5 is independent",
        },
        "star_commutators": {
            "formula": "c1i=f*b1*b_i*w_i for i=2,3,4",
            "symbolic_difference_checks": commutator_checks,
            "unit_equivalence": "on D(f), commutativity is equivalent to w2=w3=w4=0",
        },
        "generic_Schur_row_restriction": {
            "columns": ["A", "B2", "B3", "B4", "C"],
            "A": str(aligned_a),
            "B2_B3_B4": [str(value) for value in aligned_b],
            "C": str(aligned_c),
            "restricted_equation": "A*h+B2*w2+B3*w3+B4*w4+C*q5",
            "symbolic_difference": str(row_difference),
        },
        "exact_localized_obligation": {
            "ring": "S_L=(R/(g2,g3,g4))[f^-1]",
            "necessary_and_sufficient_condition": (
                "e_w2,e_w3,e_w4 all belong to the row module of the five-column "
                "aligned restriction matrix over S_L"
            ),
            "rank_form_over_each_residue_field": (
                "rank(T_L)=rank(T_L with e_w2,e_w3,e_w4 adjoined); this pointwise "
                "test is not by itself a global module certificate"
            ),
            "pure_quotient_minor_sufficient_condition": {
                "premise": "three selected rows have A=C=0",
                "minor": "det of their 3x3 (B2,B3,B4) block",
                "adjugate_identity_difference": [
                    str(_normal(value)) for value in quotient_adjugate_difference
                ],
                "required_unit_test": "the quotient minor is a unit in S_L",
            },
            "general_sufficient_conditions": [
                "directly exhibit all three target coordinate rows in Row(T_L)",
                "or exhibit a localized-unit 5x5 minor, which is stronger than needed",
                "or give local identities plus a certified unit-ideal/Bezout cover",
            ],
        },
        "automatic_safe_remainder": {
            "locus": "V(g2,g3,g4,f)",
            "consequence": "r1=r2=r3=r4=1, hence delta_Q=0",
            "all_six_commutator_checks": automatic_commutators,
            "needs_no_repair_rows": True,
        },
        "cover_partition": {
            "non_aligned_opens": ["D(g2)", "D(g3)", "D(g4)"],
            "aligned_nonunit_locus": "V(g2,g3,g4) intersect D(f)",
            "automatic_remainder": "V(g2,g3,g4,f)",
            "partition_identity_checks": [str(value) for value in partition_identities],
            "complete_set_theoretic_argument": (
                "either some g_k is nonzero, or every g_k is zero; in the latter case "
                "either f is nonzero (aligned obligation) or f=0 (delta_Q=0)"
            ),
        },
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen_base = _load(root / base_cover.RESULT_PATH)
    frozen_minor = _load(root / unit_minor.RESULT_PATH)
    base_binding_passed = (
        frozen_base.get("verdict") == base_cover.VERDICT
        and frozen_base.get("passed") is True
        and frozen_base.get("semantic_digest_sha256") == base_cover.semantic_digest(frozen_base)
    )
    minor_binding_passed = (
        frozen_minor.get("verdict") == unit_minor.VERDICT
        and frozen_minor.get("passed") is True
        and frozen_minor.get("semantic_digest_sha256")
        == unit_minor.semantic_digest(frozen_minor)
    )
    if not base_binding_passed or not minor_binding_passed:
        raise AssertionError("a frozen Eq120/Schur predecessor binding failed")

    expected_cover = [
        {"locus": "U2=D(r2-r1)", "target_rows": ["c12"]},
        {"locus": "U3=D(r3-r1)", "target_rows": ["c13"]},
        {"locus": "U4=D(r4-r1)", "target_rows": ["c14"]},
        {
            "locus": (
                "D_equal_nonunit=V(r2-r1,r3-r1,r4-r1) intersect D(r1-1)"
            ),
            "target_rows": ["c12", "c13", "c14"],
        },
    ]
    frozen_star = frozen_base["source_native_Eq120_star_commutator_reduction"]
    base_cover_shape_passed = (
        frozen_star["sharper_complete_cover"] == expected_cover
        and frozen_star["automatic_remainder"]
        == "r1=r2=r3=r4=1, which lies in Z_Q and is witness-free"
    )
    minor_shape_passed = (
        frozen_minor["unit_minor_certificate"]["matrix_shape"] == [127, 127]
        and frozen_minor["next_gate"]["ambient_columns_after_global_elimination"]
        == ["Q1", "Q2", "Q3", "Q4", "Q5"]
        and frozen_minor["next_gate"]["branch_count_if_common_core_succeeds"] == 0
    )
    if not base_cover_shape_passed or not minor_shape_passed:
        raise AssertionError("a frozen Eq120/Schur predecessor shape changed")

    chart = _chart_obligation_certificate()
    aligned = _aligned_obligation_certificate()
    gates = {
        "frozen_Eq120_four_locus_cover_is_bound": base_binding_passed
        and base_cover_shape_passed,
        "frozen_127_column_unit_minor_is_bound": minor_binding_passed
        and minor_shape_passed,
        "Eq120_kernel_is_reconstructed_on_all_three_g_charts": all(
            set(record["parameter_reconstruction"]["reverse_numerator_identity_checks"].values())
            == {"0"}
            for record in chart["three_non_aligned_charts"]
        ),
        "each_chart_commutator_is_a_unit_times_gk_times_w": len(
            chart["three_non_aligned_charts"]
        )
        == 3,
        "generic_five_column_Schur_restriction_is_exact": chart[
            "generic_Schur_row_restriction"
        ]["symbolic_difference"]
        == "0",
        "visible_reference_change_only_rescales_pair_minors_by_units": all(
            set(record["parametrisation_difference_checks"]) == {"0"}
            and record["B_scaling_difference"] == "0"
            and record["pair_minor_scaling_difference"] == "0"
            and record["scaling_is_a_declared_unit"]
            for record in chart["visible_reference_invariance"]["records"]
        ),
        "Q5_coupling_is_fail_closed": chart["Q5_fail_closed_audit"][
            "rank_after_adjoining_e_w"
        ]
        > chart["Q5_fail_closed_audit"]["row_rank"],
        "multivariate_gcd_is_not_promoted_to_unit_ideal": (
            chart["gcd_fail_closed_audit"]["gcd"] == "1"
            and not chart["gcd_fail_closed_audit"]["Groebner_basis_contains_one"]
        ),
        "aligned_three_obstruction_coordinates_are_derived": set(
            aligned["star_commutators"]["symbolic_difference_checks"].values()
        )
        == {"0"},
        "f_zero_remainder_is_automatically_safe": aligned["automatic_safe_remainder"][
            "needs_no_repair_rows"
        ],
        "four_loci_plus_automatic_remainder_are_complete": set(
            aligned["cover_partition"]["partition_identity_checks"]
        )
        == {"0"},
    }
    if not all(gates.values()):
        raise AssertionError(f"Eq120 Schur-chart obligation gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_under_study": (
            "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON"
        ),
        "input_artifacts": {
            relative: {
                "raw_sha256": _sha256(root / relative),
                "semantic_digest_sha256": _load(root / relative)[
                    "semantic_digest_sha256"
                ],
            }
            for relative in (base_cover.RESULT_PATH, unit_minor.RESULT_PATH)
        },
        "predecessor_bindings": {
            "Eq120_four_locus_cover_verdict": base_cover.VERDICT,
            "common_core_unit_minor_verdict": unit_minor.VERDICT,
            "global_non_Q_elimination_shape": [127, 127],
            "remaining_Schur_columns": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "uses_no_Eq113_or_Eq139_rows_in_the_unit_minor": True,
        },
        "non_aligned_chart_certificate": chart,
        "aligned_chart_certificate": aligned,
        "repair_certificate_contract": {
            "U2": "prove e_w in Row(T_2) over R[g2^-1] or give an exact escape",
            "U3": "prove e_w in Row(T_3) over R[g3^-1] or give an exact escape",
            "U4": "prove e_w in Row(T_4) over R[g4^-1] or give an exact escape",
            "aligned": (
                "prove e_w2,e_w3,e_w4 in Row(T_L) over "
                "(R/(g2,g3,g4))[f^-1] or give an exact escape"
            ),
            "accepted_global_proof_forms": [
                "direct localized row-module identities with only declared-unit denominators",
                "localized-unit minors whose hypotheses include the Q5 column",
                "a finite chart family with an exact saturation/unit-ideal or Bezout cover",
            ],
            "rejected_promotions": [
                "finite rational or finite-field rank agreement",
                "a minor nonzero at one or finitely many points",
                "multivariate gcd equal to one without a unit-ideal certificate",
                "an AB minor that ignores nonzero Q5 coefficients",
            ],
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "this exact successor derives the fail-closed row-module obligations on the "
            "three Eq120 ratio opens and the aligned remainder after the global 127-column "
            "unit elimination; it certifies no repair row, no localized repair minor, no "
            "unit-ideal cover, no global star membership, no noncommutative witness and no "
            "SR2-V terminal"
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    payload = build_payload(root)
    output = root / RESULT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["verdict"])
    print(payload["semantic_digest_sha256"])
    print(output)


if __name__ == "__main__":
    main()
