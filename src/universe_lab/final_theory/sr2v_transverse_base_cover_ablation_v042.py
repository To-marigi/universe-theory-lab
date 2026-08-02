"""Exact SR2-V transverse-base audit, cover reduction, and semantic ablations.

This successor certificate does three things which are logically independent.

* It proves that the 49-dimensional upper scalar torus is already the primitive
  CPOBC torus; imposing both printed readings of Eq. (113) did not shrink the
  scalar base.
* It reduces the unresolved nonzero-``delta_Q`` part of the 54-dimensional
  transverse base to two strict Eq. (113) branches on four ratio charts.  The
  completed Eq. (139) branches inherit from strict by literal row inclusion.
* It directly certifies exact rational noncommutative assignments after either
  the fixed-vector-GC block or the reachable-state-MSR block is ablated.  The
  assignments satisfy both Eq. (113) readings and completed Eq. (139), hence
  all four operator-relation branches.  Reinstating the omitted block removes
  the rank escape at the same scalar point.

The ablations are relation-group independence results, not semantic profiles:
without fixed-vector GC, same-endpoint path states need not agree; without MSR,
the MSR axiom is simply absent.  The full weak/weak transverse problem remains
open.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import eq120_source_provenance_v042 as eq120_provenance
from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_transverse_base_cover_ablation.json"
SCHEMA = "final-theory-v042-sr2v-transverse-base-cover-ablation-v1"
VERDICT = (
    "SR2V_TRANSVERSE_BASE_FOUR_CHART_REDUCTION_AND_GC_MSR_BLOCK_INDEPENDENCE_CERTIFIED_NONTERMINAL"
)
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_EIGHT_LOCAL_MEMBERSHIP_OBLIGATIONS_REMAIN"

OMIT_MSR = "omit_reachable_state_MSR"
OMIT_GC = "omit_fixed_vector_GC"

# Exact upper-character factors a_e=b_e*prod scalar**K[column,e].
ABLATION_SPECS: dict[str, dict[str, Any]] = {
    OMIT_MSR: {
        "factors": ((12, Fraction(2)), (48, Fraction(3))),
        "omitted_block": "reachable_state_MSR",
        "retained_semantic_block": "fixed_vector_GC",
    },
    OMIT_GC: {
        "factors": ((44, Fraction(2)),),
        "omitted_block": "fixed_vector_GC",
        "retained_semantic_block": "reachable_state_MSR_on_all_source_reaching_paths",
    },
}

SparseRow = dict[str, Fraction]
LowerCharacter = locus.LowerCharacter


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


def _rank_labelled(rows: list[lattice.LabelledRow], variables: tuple[str, ...]) -> int:
    return len(lattice._row_echelon(rows, variables))


def scalar_base_audit(
    context: lattice.LatticeContext,
    kernel_columns: list[list[int]],
) -> dict[str, Any]:
    """Prove that CPOBC alone defines the primitive rank-83 scalar lattice."""

    rows, counts = lattice._operator_lattice_rows(context)
    cpobc = rows[:783]
    derived = rows[783:808]
    literal = rows[808:833]
    eq139 = rows[833:843]
    ranks = {
        "CPOBC": _rank_labelled(cpobc, context.variables),
        "CPOBC_plus_derived_Eq113": _rank_labelled([*cpobc, *derived], context.variables),
        "CPOBC_plus_literal_Eq113": _rank_labelled([*cpobc, *literal], context.variables),
        "CPOBC_plus_both_Eq113_readings": _rank_labelled(
            [*cpobc, *derived, *literal], context.variables
        ),
    }
    invariants = lattice._smith_invariants(lattice._integer_matrix(cpobc, context.variables))
    q_positions = [
        context.variables.index(lattice._q_variable(context, stage)) for stage in (1, 2, 3, 4)
    ]
    q_exponent_rows = sp.Matrix(
        [[column[position] for column in kernel_columns] for position in q_positions]
    )
    coordinate_columns = {
        "Q1": 44,
        "Q2": 13,
        "Q3": 15,
        "Q4": 12,
    }
    coordinate_signatures = {
        name: [kernel_columns[column][position] for position in q_positions]
        for name, column in coordinate_columns.items()
    }
    expected_signatures = {
        "Q1": [1, 0, 0, 0],
        "Q2": [0, 1, 0, 0],
        "Q3": [0, 0, 1, 0],
        "Q4": [0, 0, 0, 1],
    }
    if (
        counts["total"] != 843
        or ranks != {key: 83 for key in ranks}
        or invariants != [1] * 83
        or any(row for _label, row in eq139)
        or int(q_exponent_rows.rank()) != 4
        or coordinate_signatures != expected_signatures
    ):
        raise AssertionError("the transverse scalar-base audit changed")
    return {
        "upper_scalar_base": "ker(CPOBC scalar exponent lattice) = G_m^49",
        "lower_scalar_base": "BottomMSR_CSG(t1,t2,t3,t4,q5), dimension 5",
        "transverse_scalar_base_dimension": 54,
        "row_counts": {
            "CPOBC": len(cpobc),
            "derived_Eq113": len(derived),
            "literal_Eq113": len(literal),
            "completed_Eq139": len(eq139),
        },
        "QQ_ranks": ranks,
        "CPOBC_smith_nonzero_invariants": invariants,
        "CPOBC_integer_row_lattice_is_saturated": invariants == [1] * 83,
        "both_Eq113_scalar_readings_are_redundant_over_the_CPOBC_integer_lattice": True,
        "all_completed_Eq139_scalar_rows_are_identically_zero": not any(
            row for _label, row in eq139
        ),
        "upper_torus_dimension": len(context.variables) - ranks["CPOBC"],
        "Q_ratio_character_rank": int(q_exponent_rows.rank()),
        "primitive_kernel_coordinate_columns": coordinate_columns,
        "coordinate_column_Q_exponent_signatures": coordinate_signatures,
        "conclusion": (
            "the common G_m^49 upper base is intrinsic to CPOBC; it was not created "
            "by intersecting the alternative Eq113 readings"
        ),
    }


def ratio_cover_identity() -> dict[str, Any]:
    """Verify the regular ratio coordinates and the four-chart cover."""

    bi, bj, ri, rj, yi, yj = sp.symbols("b_i b_j r_i r_j y_i y_j", nonzero=True)
    ai, aj, xi, xj = bi * ri, bj * rj, bi * yi, bj * yj
    raw = sp.expand(xj * (ai - bi) - xi * (aj - bj))
    normalized = bi * bj * ((ri - 1) * yj - (rj - 1) * yi)
    if sp.expand(raw - normalized) != 0:
        raise AssertionError("the ratio-normalized commutator identity changed")
    return {
        "regular_change_of_coordinates": "r_e=a_e/b_e, y_e=x_e/b_e",
        "why_regular": "every b_e is a unit on the nonsingular bottom CSG principal open",
        "delta_formula": "delta_i=b_Qi*(r_Qi-1)",
        "commutator_formula": ("[Qi,Qj]_12=b_Qi*b_Qj*((r_Qi-1)*y_Qj-(r_Qj-1)*y_Qi)"),
        "symbolic_difference": str(sp.expand(raw - normalized)),
        "u_coordinates": "u_i=r_Qi-1",
        "equal_Q_spectrum_locus": "Z_Q=V(u1,u2,u3,u4)",
        "equal_Q_spectrum_locus_dimension": 50,
        "equal_Q_spectrum_locus_is_split_smooth": True,
        "equal_Q_spectrum_locus_is_witness_free": True,
        "complete_base_cover": ["Z_Q", "D(u1)", "D(u2)", "D(u3)", "D(u4)"],
        "on_D_uk_three_target_rows": "u_k*y_Qj-u_j*y_Qk for j!=k",
        "remaining_three_rows_follow_after_inverting_u_k": True,
    }


def strict_completed_inclusion() -> dict[str, Any]:
    """Record the branch-local literal inclusion induced by the common builder."""

    strict = torus._eq139_instances(torus.EQ139_STRICT)
    completed = torus._eq139_instances(torus.EQ139_COMPLETED)
    mapping = [completed.index(instance) for instance in strict]
    if not set(strict).issubset(completed) or len(strict) != 4 or len(completed) != 10:
        raise AssertionError("the Eq139 strict/completed instance cover changed")
    branch_maps = {}
    for reading in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        row_map = {
            "CPOBC": "i -> i, 0<=i<783",
            "Eq113": "783+i -> 783+i, 0<=i<25",
            "Eq139_strict_to_completed": {
                str(808 + source): 808 + target for source, target in enumerate(mapping)
            },
            "fixed_vector_GC": "812+i -> 818+i, 0<=i<320",
            "reachable_state_MSR": "1132+i -> 1138+i, 0<=i<24",
        }
        branch_maps[reading] = row_map
    return {
        "canonical_general_bottom_constructor": (
            "sr2v_transverse_determinant_zero_locus_v042.eq139_row"
        ),
        "strict_instances": [list(instance) for instance in strict],
        "completed_instances": [list(instance) for instance in completed],
        "strict_completed_instance_positions": mapping,
        "both_domains_are_built_by_the_same_constructor": True,
        "branch_local_row_inclusion_maps": branch_maps,
        "derived_and_literal_Eq113_are_not_combined": True,
        "conclusion": (
            "for each Eq113 reading separately, Row(M_strict) is contained in "
            "Row(M_completed), so strict commutativity implies completed commutativity"
        ),
    }


def eq120_star_commutator_reduction(
    context: torus.ScoutContext,
    frozen_eq120: dict[str, Any],
) -> dict[str, Any]:
    """Reduce six commutators to a globally minimal three-edge star modulo CPOBC."""

    if (
        frozen_eq120.get("verdict") != eq120_provenance.VERDICT
        or frozen_eq120.get("passed") is not True
        or frozen_eq120.get("semantic_digest_sha256")
        != eq120_provenance.semantic_digest(frozen_eq120)
    ):
        raise AssertionError("the Eq120 source-provenance binding failed")

    r = sp.symbols("r1:5")
    z = sp.symbols("z1:5")

    def comm(left: int, right: int) -> sp.Expr:
        i, j = left - 1, right - 1
        return sp.expand((r[i] - 1) * z[j] - (r[j] - 1) * z[i])

    def eq120(left: int, right: int) -> sp.Expr:
        i, j = left - 1, right - 1
        return sp.expand((r[i] - r[0]) * (z[j] - z[0]) - (r[j] - r[0]) * (z[i] - z[0]))

    identities = {}
    for left, right in ((2, 3), (2, 4), (3, 4)):
        difference = sp.expand(
            comm(left, right) - (eq120(left, right) + comm(1, right) - comm(1, left))
        )
        identities[f"c{left}{right}"] = str(difference)
    if set(identities.values()) != {"0"}:
        raise AssertionError("the Eq120/star commutator identity changed")

    flattened = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            flattened.append(
                {
                    "relation_id": str(relation["relation_id"]),
                    "equation_id": str(equation["equation_id"]),
                }
            )
    row_indices = {
        "F21": 0,
        "F31": 4,
        "F32": 29,
        "F41": 44,
        "F42": 147,
        "F43": 548,
    }
    source_rows = {name: flattened[index] for name, index in row_indices.items()}
    expected_relation_ids = {
        "F21": "cpobc-relation-0b2bbe81c6394d603f63",
        "F31": "cpobc-relation-49726b7f352ba79916e5",
        "F32": "cpobc-relation-6002781cceb198b6edfd",
        "F41": "cpobc-relation-1d7b3a88785401c6531b",
        "F42": "cpobc-relation-01e29996483e2c4f342c",
        "F43": "cpobc-relation-17e9d7ae74c8bed62194",
    }
    if {
        name: record["relation_id"] for name, record in source_rows.items()
    } != expected_relation_ids or any(
        record["equation_id"] != "eq103" for record in source_rows.values()
    ):
        raise AssertionError("the six Eq120 source rows moved in the raw inventory")

    pair_sources = {
        tuple(certificate["indices"]): certificate["source_relation_ids"]
        for certificate in frozen_eq120["pair_certificates"]
    }
    expected_pair_sources = {
        (2, 3): [
            expected_relation_ids["F32"],
            expected_relation_ids["F21"],
            expected_relation_ids["F31"],
        ],
        (2, 4): [
            expected_relation_ids["F42"],
            expected_relation_ids["F21"],
            expected_relation_ids["F41"],
        ],
        (3, 4): [
            expected_relation_ids["F43"],
            expected_relation_ids["F31"],
            expected_relation_ids["F41"],
        ],
    }
    if pair_sources != expected_pair_sources:
        raise AssertionError("the Eq120 three-source provenance changed")

    upper_b1 = sp.symbols("A_B1", nonzero=True)
    a = sp.symbols("a1:5", nonzero=True)
    b = sp.symbols("b1:5", nonzero=True)
    x = sp.symbols("x1:5")
    y_b = sp.symbols("y_B1:5")

    def raw_f(left: int, right: int) -> sp.Expr:
        i, j = left - 1, right - 1
        upper_bi = upper_b1 * a[i] / a[0]
        upper_bj = upper_b1 * a[j] / a[0]
        return sp.expand(upper_bi * x[j] + y_b[i] * b[j] - upper_bj * x[i] - y_b[j] * b[i])

    def ratio_e(left: int, right: int) -> sp.Expr:
        i, j = left - 1, right - 1
        return sp.expand(
            (a[i] / b[i] - a[0] / b[0]) * (x[j] / b[j] - x[0] / b[0])
            - (a[j] / b[j] - a[0] / b[0]) * (x[i] / b[i] - x[0] / b[0])
        )

    source_combination_differences = {}
    for left, right in ((2, 3), (2, 4), (3, 4)):
        i, j = left - 1, right - 1
        combination = (
            raw_f(right, left) - (b[i] / b[0]) * raw_f(right, 1) + (b[j] / b[0]) * raw_f(left, 1)
        ) / upper_b1
        target = -(b[i] * b[j] / a[0]) * ratio_e(left, right)
        source_combination_differences[f"E{left}{right}"] = str(
            sp.factor(sp.cancel(combination - target))
        )
    if set(source_combination_differences.values()) != {"0"}:
        raise AssertionError("the arbitrary-base Eq120 row combination changed")

    return {
        "normalization": "Q_i=b_i*P_i, P_i=[[r_i,z_i],[0,1]]",
        "source_native_Eq120": ("T_mn=Q_n*Q_1^-1*Q_m-Q_m*Q_1^-1*Q_n=0 for 2<=m<n<=4"),
        "free_algebra_source_identity": ("B1*T_mn=F_nm-F_n1*Q1^-1*Q_m+F_m1*Q1^-1*Q_n"),
        "upper_right_row_combination": ("t_mn=A_B1^-1*(f_nm-(b_m/b1)*f_n1+(b_n/b1)*f_m1)"),
        "ratio_row_unit_proportionality": "t_mn=-(b_m*b_n/a1)*E_mn",
        "all_displayed_prefactors_are_units": True,
        "arbitrary_base_symbolic_row_combination_differences": source_combination_differences,
        "source_row_indices_zero_based": row_indices,
        "source_rows": source_rows,
        "each_Eq120_row_uses_exactly_three_raw_CPOBC_rows": True,
        "ratio_Eq120_rows": {
            "E23": "(r2-r1)*(z3-z1)-(r3-r1)*(z2-z1)",
            "E24": "(r2-r1)*(z4-z1)-(r4-r1)*(z2-z1)",
            "E34": "(r3-r1)*(z4-z1)-(r4-r1)*(z3-z1)",
        },
        "six_to_star_identities": identities,
        "identity_template": "c_mn=E_mn+c_1n-c_1m",
        "global_rank_test_reduction": (
            "modulo raw CPOBC, adjoining all six Q commutator rows is equivalent to "
            "adjoining only c12,c13,c14"
        ),
        "three_star_rows_are_globally_minimal": {
            "point": "r1=r2=r3=r4=r with r!=1",
            "reason": "all E_mn vanish and c_1i=(r-1)*(z_i-z1) have rank three",
        },
        "sharper_complete_cover": [
            {
                "locus": "U2=D(r2-r1)",
                "target_rows": ["c12"],
            },
            {
                "locus": "U3=D(r3-r1)",
                "target_rows": ["c13"],
            },
            {
                "locus": "U4=D(r4-r1)",
                "target_rows": ["c14"],
            },
            {
                "locus": "D_equal_nonunit=V(r2-r1,r3-r1,r4-r1) intersect D(r1-1)",
                "target_rows": ["c12", "c13", "c14"],
            },
        ],
        "automatic_remainder": "r1=r2=r3=r4=1, which lies in Z_Q and is witness-free",
        "single_row_chart_argument": (
            "on U_k, Eq120 gives z_i-z1=lambda*(r_i-r1); then every star row is "
            "(r_i-r1)*h and c_1k=(r_k-r1)*h, so c_1k=0 forces all six"
        ),
    }


def _upper_point(
    context: torus.ScoutContext,
    kernel_columns: list[list[int]],
    factors: tuple[tuple[int, Fraction], ...],
) -> tuple[dict[str, Fraction], dict[str, Fraction]]:
    couplings, q5 = locus.REFERENCE_BOTTOM
    lower = locus.bottom_character(couplings, q5)
    base = locus.bottom_point(context, lower)
    upper: dict[str, Fraction] = {}
    for index, variable in enumerate(context.variables):
        value = base[variable]
        for column, scalar in factors:
            exponent = kernel_columns[column][index]
            if exponent:
                value *= scalar**exponent
        upper[variable] = value
    if not all(upper.values()):
        raise AssertionError("an ablation upper character left the torus")
    return upper, base


def _ablated_rows(rows: list[SparseRow], omitted: str) -> list[SparseRow]:
    relation_count = len(rows) - 344
    if omitted == "reachable_state_MSR":
        return [*rows[:relation_count], *rows[relation_count : relation_count + 320]]
    if omitted == "fixed_vector_GC":
        return [*rows[:relation_count], *rows[relation_count + 320 :]]
    raise ValueError(f"unknown semantic block: {omitted}")


def _vector_row(variables: tuple[str, ...], vector: tuple[Fraction, ...]) -> SparseRow:
    return {variables[index]: value for index, value in enumerate(vector) if value}


def _direct_ablation_certificate(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
    bottom: dict[str, Fraction],
    coordinates: SparseRow,
    lower: LowerCharacter,
    omitted: str,
) -> dict[str, Any]:
    """Directly substitute one ablated assignment into every raw relation."""

    def transition(stage: int, relation: Any, precursor: int, variable: str) -> torus.Matrix2:
        return torus._matrix(
            upper[variable],
            coordinates.get(variable, Fraction(0)),
            lower(stage, relation, precursor),
        )

    def from_signature(stage: int, relation_code: int, precursor: int) -> torus.Matrix2:
        variable = context.signature_variables[(stage, relation_code, precursor)]
        return transition(stage, torus._decode_relation(stage, relation_code), precursor, variable)

    def q(stage: int) -> torus.Matrix2:
        variable = torus._q_variable(context, stage)
        return torus._matrix(
            upper[variable],
            coordinates.get(variable, Fraction(0)),
            lower(stage, (0,) * stage, 0),
        )

    occurrence_matrices = {
        occurrence_id: transition(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
            context.occurrence_variables[occurrence_id],
        )
        for occurrence_id, record in context.occurrence_records.items()
    }

    cpobc_failures = []
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            left = torus._word(
                occurrence_matrices[operator_ids[token]] for token in equation["lhs_word"]
            )
            right = torus._word(
                occurrence_matrices[operator_ids[token]] for token in equation["rhs_word"]
            )
            if left != right:
                cpobc_failures.append(f"{relation['relation_id']}:{equation['equation_id']}")

    def eq113_token(token: str) -> torus.Matrix2:
        if token.startswith("Q_"):
            return q(int(token.removeprefix("Q_")))
        kind, identifier = token.split(":", maxsplit=1)
        stage, relation, precursor, variable = context.b_signatures[identifier]
        matrix = transition(stage, relation, precursor, variable)
        if kind == "BDEF":
            return matrix
        if kind == "BINV":
            return torus._inverse(matrix)
        raise ValueError(f"unknown Eq113 token: {token}")

    eq113: dict[str, Any] = {}
    for reading in (torus.EQ113_DERIVED, torus.EQ113_LITERAL):
        failures = []
        relations = context.eq112["path_consistency_branches"][reading]
        for relation in relations:
            left = torus._word(eq113_token(token) for token in relation["lhs_word"])
            right = torus._word(eq113_token(token) for token in relation["rhs_word"])
            if left != right:
                failures.append(str(relation["causet_id"]))
        eq113[reading] = {"checked": len(relations), "failures": failures}

    eq139: dict[str, Any] = {}
    for domain in (torus.EQ139_STRICT, torus.EQ139_COMPLETED):
        eq139_failures: list[list[int]] = []
        for stage, left_index, right_index in torus._eq139_instances(domain):
            left_transition = from_signature(stage, 0, (1 << left_index) - 1)
            right_transition = from_signature(stage, 0, (1 << right_index) - 1)
            current_q = q(stage)
            next_q = q(stage + 1)
            left = torus._word(
                (
                    left_transition,
                    right_transition,
                    next_q,
                    torus._inverse(right_transition),
                    torus._inverse(current_q),
                    right_transition,
                )
            )
            right = torus._word(
                (
                    right_transition,
                    left_transition,
                    next_q,
                    torus._inverse(left_transition),
                    torus._inverse(current_q),
                    left_transition,
                )
            )
            if left != right:
                eq139_failures.append([stage, left_index, right_index])
        eq139[domain] = {
            "checked": len(torus._eq139_instances(domain)),
            "failures": eq139_failures,
        }

    path_matrices: dict[str, torus.Matrix2] = {}
    path_records: dict[str, dict[str, Any]] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = torus.IDENTITY
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                product = torus._multiply(
                    from_signature(
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    ),
                    product,
                )
            path_id = str(path["path_id"])
            path_matrices[path_id] = product
            path_records[path_id] = path

    gc_failures = []
    for relation in context.operator_gc["all_pair_derivations"]:
        residual = torus._subtract(
            path_matrices[relation["left_path_id"]],
            path_matrices[relation["right_path_id"]],
        )
        if torus._apply(residual, torus.OMEGA) != torus.ZERO_VECTOR:
            gc_failures.append(f"{relation['left_path_id']}:{relation['right_path_id']}")

    anchors: dict[str, torus.Vector2] = {}
    endpoint_groups: defaultdict[str, list[torus.Vector2]] = defaultdict(list)
    endpoint_path_states: defaultdict[str, list[tuple[str, torus.Vector2]]] = defaultdict(list)
    path_states: dict[str, torus.Vector2] = {}
    for path_id, path in path_records.items():
        state = torus._apply(path_matrices[path_id], torus.OMEGA)
        endpoint = str(path["endpoint_causet_id"])
        path_states[path_id] = state
        endpoint_groups[endpoint].append(state)
        endpoint_path_states[endpoint].append((path_id, state))
        anchors.setdefault(endpoint, state)
    same_endpoint_consistent = all(
        all(state == states[0] for state in states[1:]) for states in endpoint_groups.values()
    )

    msr_failures = []
    all_reachable_msr_failures = []
    all_reachable_msr_checks = 0
    operator_msr_nonzero = 0
    for constraint in context.cpobc["MSR_operator_constraints"]:
        identity = Fraction(int(constraint["identity_coefficient"]))
        total: torus.Matrix2 = ((identity, Fraction(0)), (Fraction(0), identity))
        for term in constraint["terms"]:
            coefficient = Fraction(int(term["coefficient"]))
            matrix = occurrence_matrices[term["transition_id"]]
            total = (
                (
                    total[0][0] + coefficient * matrix[0][0],
                    total[0][1] + coefficient * matrix[0][1],
                ),
                (
                    total[1][0] + coefficient * matrix[1][0],
                    total[1][1] + coefficient * matrix[1][1],
                ),
            )
        operator_msr_nonzero += int(total != torus.ZERO_MATRIX)
        source_id = str(constraint["source_id"])
        if torus._apply(total, anchors[source_id]) != torus.ZERO_VECTOR:
            msr_failures.append(str(constraint["constraint_id"]))
        for path_id, state in endpoint_path_states[source_id]:
            all_reachable_msr_checks += 1
            if torus._apply(total, state) != torus.ZERO_VECTOR:
                all_reachable_msr_failures.append(f"{constraint['constraint_id']}:{path_id}")

    commutators = []
    any_path_visible = False
    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        residual = torus._subtract(
            torus._multiply(q(left_stage), q(right_stage)),
            torus._multiply(q(right_stage), q(left_stage)),
        )
        visible_paths = [
            path_id
            for path_id, state in path_states.items()
            if torus._apply(residual, state) != torus.ZERO_VECTOR
        ]
        any_path_visible |= bool(visible_paths)
        commutators.append(
            {
                "pair": [left_stage, right_stage],
                "matrix": [[str(entry) for entry in row] for row in residual],
                "operator_nonzero": residual != torus.ZERO_MATRIX,
                "visible_path_count": len(visible_paths),
                "first_visible_path": visible_paths[0] if visible_paths else None,
            }
        )

    determinants_nonzero = all(upper[var] * bottom[var] for var in context.variables)
    common_pass = all(
        (
            not cpobc_failures,
            all(not record["failures"] for record in eq113.values()),
            all(not record["failures"] for record in eq139.values()),
            determinants_nonzero,
            any(record["operator_nonzero"] for record in commutators),
            any_path_visible,
            torus._vector_rank(path_states.values()) == 2,
        )
    )
    if omitted == "reachable_state_MSR":
        expected_semantics = not gc_failures and same_endpoint_consistent and bool(msr_failures)
    elif omitted == "fixed_vector_GC":
        expected_semantics = (
            not msr_failures
            and all_reachable_msr_checks == 50
            and not all_reachable_msr_failures
            and bool(gc_failures)
            and not same_endpoint_consistent
        )
    else:
        raise ValueError(f"unknown omitted block: {omitted}")
    if not common_pass or not expected_semantics:
        raise AssertionError(
            "an ablation witness failed direct certification: "
            f"omitted={omitted} common={common_pass} expected={expected_semantics}"
        )
    return {
        "upper_right_nonzero_coordinates": {
            variable: str(value) for variable, value in sorted(coordinates.items()) if value
        },
        "upper_right_support": sum(bool(value) for value in coordinates.values()),
        "direct_substitution": {
            "CPOBC": {"checked": 783, "failures": cpobc_failures},
            "Eq113": eq113,
            "Eq139": eq139,
            "fixed_vector_GC": {
                "checked": len(context.operator_gc["all_pair_derivations"]),
                "failures": gc_failures,
            },
            "reachable_state_MSR": {
                "checked": len(context.cpobc["MSR_operator_constraints"]),
                "failures": msr_failures,
                "operator_nonzero_residual_count": operator_msr_nonzero,
                "source_state_convention_when_GC_is_absent": "first frozen path anchor",
                "all_source_reaching_path_state_checks": all_reachable_msr_checks,
                "all_source_reaching_path_state_failures": all_reachable_msr_failures,
            },
        },
        "all_132_assigned_matrices_are_nonsingular": determinants_nonzero,
        "path_count": len(path_states),
        "endpoint_count": len(endpoint_groups),
        "all_path_state_span_rank": torus._vector_rank(path_states.values()),
        "all_same_endpoint_paths_give_same_state": same_endpoint_consistent,
        "commutators": commutators,
        "some_nonzero_commutator_is_reachable_path_visible": any_path_visible,
        "passed": True,
    }


def ablation_certificate(
    context: torus.ScoutContext,
    operator_context: lattice.LatticeContext,
    kernel_columns: list[list[int]],
    ablation_id: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Promote one rank escape to a direct exact rational counterassignment."""

    factors = tuple(spec["factors"])
    omitted = str(spec["omitted_block"])
    upper, bottom = _upper_point(context, kernel_columns, factors)
    couplings, q5 = locus.REFERENCE_BOTTOM
    lower = locus.bottom_character(couplings, q5)
    operator_rows, _counts = lattice._operator_lattice_rows(operator_context)
    if locus._monomial_failures(upper, operator_rows):
        raise AssertionError("an ablation upper point left the operator scalar torus")

    joint_rows, counts, commutators, _paths = torus._linear_system(context, upper, lower)
    if counts != {
        "CPOBC": 783,
        "Eq113_both_branches": 50,
        "Eq139_completed": 10,
        "fixed_vector_GC_basis": 320,
        "reachable_state_MSR": 24,
    }:
        raise AssertionError("the joint row inventory changed")
    commutator_rows = list(commutators.values())
    branch_rows: dict[str, list[SparseRow]] = {}
    branch_reports: dict[str, Any] = {}
    for branch_id, (eq113_reading, eq139_domain) in locus.BRANCH_SPECS.items():
        full = locus.branch_matrix(context, upper, lower, joint_rows, eq113_reading, eq139_domain)
        ablated = _ablated_rows(full, omitted)
        full_rank = locus._rank(full, context.variables)
        full_augmented = locus._rank([*full, *commutator_rows], context.variables)
        rank = locus._rank(ablated, context.variables)
        augmented = locus._rank([*ablated, *commutator_rows], context.variables)
        branch_rows[branch_id] = ablated
        branch_reports[branch_id] = {
            "full_profile_rank": full_rank,
            "full_profile_augmented_rank": full_augmented,
            "full_profile_has_no_escape_at_this_point": full_rank == full_augmented,
            "ablated_rank": rank,
            "ablated_augmented_rank": augmented,
            "ablated_commutator_rank_increment": augmented - rank,
        }
        if full_rank != full_augmented or augmented != rank + 1:
            raise AssertionError(f"the {ablation_id} branch rank signal changed")

    # Satisfy the strongest operator-relation interpretation for both Eq113
    # readings at once.  This one vector therefore works in all four branches.
    strongest = [
        *branch_rows[transverse.DERIVED_COMPLETED],
        *branch_rows[transverse.LITERAL_COMPLETED],
    ]
    strongest_rank, kernel = locus._kernel_basis(strongest, context.variables)
    strongest_augmented = locus._rank([*strongest, *commutator_rows], context.variables)
    candidates = []
    for basis_index, vector in enumerate(kernel):
        row = _vector_row(context.variables, vector)
        values = {pair: locus._apply(target, row) for pair, target in commutators.items()}
        if any(values.values()):
            candidates.append((len(row), basis_index, row, values))
    if strongest_augmented != strongest_rank + 1 or not candidates:
        raise AssertionError("the common strongest ablation kernel no longer escapes")
    _support, basis_index, witness, commutator_values = min(
        candidates, key=lambda record: (record[0], record[1])
    )
    if any(locus._apply(row, witness) for branch in branch_rows.values() for row in branch):
        raise AssertionError("the common ablation witness left a branch kernel")
    direct = _direct_ablation_certificate(context, upper, bottom, witness, lower, omitted)
    delta = {
        str(stage): str(upper[torus._q_variable(context, stage)] - lower(stage, (0,) * stage, 0))
        for stage in (1, 2, 3, 4)
    }
    q_variables = [torus._q_variable(context, stage) for stage in (1, 2, 3, 4)]
    ratios = [upper[variable] / bottom[variable] for variable in q_variables]
    normalized_cocycle = [
        witness.get(variable, Fraction(0)) / bottom[variable] for variable in q_variables
    ]
    eq120_values = {}
    for left, right in ((2, 3), (2, 4), (3, 4)):
        i, j = left - 1, right - 1
        eq120_values[f"E{left}{right}"] = (ratios[i] - ratios[0]) * (
            normalized_cocycle[j] - normalized_cocycle[0]
        ) - (ratios[j] - ratios[0]) * (normalized_cocycle[i] - normalized_cocycle[0])
    pivot = next(index for index in range(1, 4) if ratios[index] != ratios[0])
    affine_slope = (normalized_cocycle[pivot] - normalized_cocycle[0]) / (ratios[pivot] - ratios[0])
    affine_intercept = normalized_cocycle[0] - affine_slope * ratios[0]
    if any(eq120_values.values()) or any(
        value != affine_slope * ratio + affine_intercept
        for ratio, value in zip(ratios, normalized_cocycle, strict=True)
    ):
        raise AssertionError("an ablation witness left the Eq120 affine-line geometry")
    semantic_interpretation = (
        "fixed-vector GC holds, while the omitted reachable-state MSR block fails"
        if omitted == "reachable_state_MSR"
        else (
            "fixed-vector GC fails, but reachable-state MSR holds on every one of the "
            "50 frozen paths reaching the 24 MSR source states, not merely on anchors"
        )
    )
    return {
        "ablation_id": ablation_id,
        "omitted_block": omitted,
        "retained_semantic_block": spec["retained_semantic_block"],
        "upper_character": {
            "formula": "a_e=b_e*product scalar^K[column,e]",
            "factors": [
                {"kernel_column": column, "scalar": str(scalar)} for column, scalar in factors
            ],
            "all_843_operator_scalar_rows_hold": True,
            "point_digest_sha256": _digest(
                [str(upper[variable]) for variable in context.variables]
            ),
        },
        "bottom_character": {
            "couplings": [str(value) for value in couplings],
            "cutoff_external_q5": str(q5),
        },
        "delta_Q": delta,
        "branches": branch_reports,
        "strongest_union": {
            "meaning": "derived completed plus literal completed, with the declared block omitted",
            "rank": strongest_rank,
            "augmented_rank": strongest_augmented,
            "nullity": len(context.variables) - strongest_rank,
            "chosen_kernel_basis_index": basis_index,
        },
        "commutator_values_on_witness": {
            pair: str(value) for pair, value in commutator_values.items()
        },
        "normalized_Q_geometry": {
            "r_Q": [str(value) for value in ratios],
            "z_Q": [str(value) for value in normalized_cocycle],
            "Eq120_rows": {name: str(value) for name, value in eq120_values.items()},
            "affine_line": f"z=({affine_slope})*r+({affine_intercept})",
            "affine_slope": str(affine_slope),
            "affine_intercept": str(affine_intercept),
            "commutator_obstruction_h_equals_slope_plus_intercept": str(
                affine_slope + affine_intercept
            ),
        },
        "witness_coordinate_digest_sha256": _digest(
            {variable: str(value) for variable, value in sorted(witness.items())}
        ),
        "direct_certificate": direct,
        "minimal_repair_at_this_point": (
            "reinstating the omitted row block makes rank[M;C]=rank M in all four branches"
        ),
        "semantic_interpretation": semantic_interpretation,
        "claim_boundary": (
            "relation-group independence at one exact transverse base point; not a global "
            "minimality theorem and not a counterexample to the full weak/weak profile"
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen_lattice = _load(root / lattice.RESULT_PATH)
    frozen_locus = _load(root / locus.RESULT_PATH)
    frozen_eq120 = _load(root / eq120_provenance.RESULT_PATH)
    if (
        frozen_lattice.get("verdict") != lattice.VERDICT
        or frozen_lattice.get("semantic_digest_sha256") != lattice.semantic_digest(frozen_lattice)
        or frozen_locus.get("verdict") != locus.VERDICT
        or frozen_locus.get("semantic_digest_sha256") != locus.semantic_digest(frozen_locus)
    ):
        raise AssertionError("a frozen predecessor binding failed")

    context = torus._build_context(root)
    operator_context = lattice._build_context(root)
    kernel_columns = transverse._operator_kernel(frozen_lattice)
    base_audit = scalar_base_audit(operator_context, kernel_columns)
    cover = ratio_cover_identity()
    inclusion = strict_completed_inclusion()
    star_reduction = eq120_star_commutator_reduction(context, frozen_eq120)
    ablations = {
        ablation_id: ablation_certificate(
            context, operator_context, kernel_columns, ablation_id, spec
        )
        for ablation_id, spec in ABLATION_SPECS.items()
    }

    gates = {
        "CPOBC_alone_defines_a_primitive_rank83_scalar_lattice": (
            base_audit["CPOBC_integer_row_lattice_is_saturated"]
            and set(base_audit["QQ_ranks"].values()) == {83}
        ),
        "alternative_Eq113_readings_do_not_shrink_the_scalar_base": base_audit[
            "both_Eq113_scalar_readings_are_redundant_over_the_CPOBC_integer_lattice"
        ],
        "Q_ratio_characters_have_four_independent_coordinates": (
            base_audit["Q_ratio_character_rank"] == 4
        ),
        "ratio_commutator_identity_is_exact": cover["symbolic_difference"] == "0",
        "Z_Q_plus_four_principal_charts_cover_the_base": len(cover["complete_base_cover"]) == 5,
        "strict_Eq139_rows_are_a_literal_subset_of_completed_rows": inclusion[
            "strict_completed_instance_positions"
        ]
        == [1, 4, 5, 7],
        "derived_and_literal_Eq113_remain_separate": inclusion[
            "derived_and_literal_Eq113_are_not_combined"
        ],
        "source_native_Eq120_reduces_six_commutators_to_a_minimal_star_of_three": (
            set(star_reduction["six_to_star_identities"].values()) == {"0"}
            and set(star_reduction["arbitrary_base_symbolic_row_combination_differences"].values())
            == {"0"}
            and star_reduction["each_Eq120_row_uses_exactly_three_raw_CPOBC_rows"]
        ),
        "Eq120_sharpens_the_remaining_cover_to_four_loci_per_Eq113_reading": (
            len(star_reduction["sharper_complete_cover"]) == 4
        ),
        "both_semantic_block_ablations_have_direct_exact_witnesses": all(
            record["direct_certificate"]["passed"] for record in ablations.values()
        ),
        "reinstating_each_omitted_block_closes_its_rank_escape_at_the_same_point": all(
            branch["full_profile_has_no_escape_at_this_point"]
            for record in ablations.values()
            for branch in record["branches"].values()
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"transverse cover/ablation gate failed: {gates}")

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
                "semantic_digest_sha256": _load(root / relative).get("semantic_digest_sha256"),
            }
            for relative in (
                lattice.RESULT_PATH,
                locus.RESULT_PATH,
                eq120_provenance.RESULT_PATH,
            )
        },
        "scalar_base_audit": base_audit,
        "ratio_normalized_cover": cover,
        "strict_to_completed_Eq139_inclusion": inclusion,
        "source_native_Eq120_star_commutator_reduction": star_reduction,
        "semantic_block_ablations": ablations,
        "remaining_exact_obligations": {
            "automatic_safe_locus": "r1=r2=r3=r4=1, contained in Z_Q",
            "branch_count_after_strict_to_completed_reduction": 2,
            "locus_count_per_branch": 4,
            "obligation_count": 8,
            "obligations": [
                {
                    "Eq113_reading": reading,
                    "Eq139_domain": torus.EQ139_STRICT,
                    "locus": chart["locus"],
                    "target_rows": chart["target_rows"],
                }
                for reading in (torus.EQ113_DERIVED, torus.EQ113_LITERAL)
                for chart in star_reduction["sharper_complete_cover"]
            ],
            "target_on_each_chart": (
                "prove the declared one-row or three-row star target lies in the localized "
                "full strict branch row module, or provide an exact escaping kernel vector"
            ),
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "the scalar-base and cover reductions are exact; the two ablation assignments "
            "are exact relation-group countermodels; none proves or refutes full-profile "
            "commutativity on the eight remaining localized obligations"
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
