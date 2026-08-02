"""Exact rejection scout for two proposed Eq. (120) chart-repair row pairs.

The certified 127-column unit minor reduces the common-core problem to five
``Q`` columns.  Two finite-ledger repair pairs looked sufficient on the
``g2`` and ``g3`` Eq. (120) charts.  This module evaluates exact positive
rational points on additional zero factors of their maximal minors and rejects
both pairs while checking that the complete common core still contains all six
commutators.  It does not reject either chart or the full common core.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_base_cover_ablation_v042 as base_cover
from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import sr2v_transverse_common_core_unit_minor_v042 as unit_minor
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_transverse_eq120_repair_pair_scout.json"
SCHEMA = "final-theory-v042-sr2v-transverse-eq120-repair-pair-scout-v2"
VERDICT = (
    "SR2V_TRANSVERSE_EQ120_THREE_PAIR_MINOR_SUBCOVER_EXACTLY_REJECTED_"
    "FULL_M0_SURVIVES_NONTERMINAL"
)
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_THREE_PAIR_MINOR_SUBCOVER_REJECTION_ONLY"

PAIR_SPECS: dict[str, dict[str, Any]] = {
    "g2": {
        "chart_index": 2,
        "eq120_base_sources": (29, 147),
        "proposed_patch_sources": (32, 120),
        "factors": (
            (12, Fraction(1)),
            (13, Fraction(2)),
            (15, Fraction(1)),
            (44, Fraction(3)),
            (45, Fraction(3)),
        ),
        "targeting_rationale": "the sampled maximal minor has an extra u44-u45 zero factor",
        "expected_g": Fraction(-1, 48),
        "expected_8_14_minor": Fraction(975, 2048),
        "expected_candidate_rows": (
            ("5/32", "-3/16", "-3/4", "0", "0"),
            ("3/82", "0", "0", "-3/4", "0"),
            ("0", "0", "0", "0", "0"),
            ("185/738", "5/41", "-80/123", "-10", "0"),
        ),
        "expected_star_rows": (
            ("-1/12", "0", "0", "0", "0"),
            ("1/48", "0", "0", "0", "0"),
            ("0", "0", "0", "0", "0"),
        ),
    },
    "g3": {
        "chart_index": 3,
        "eq120_base_sources": (29, 548),
        "proposed_patch_sources": (424, 544),
        "factors": (
            (12, Fraction(1)),
            (13, Fraction(3)),
            (15, Fraction(1)),
            (44, Fraction(2)),
            (45, Fraction(2)),
        ),
        "targeting_rationale": (
            "the sampled maximal minor has an extra u12*u45-u44 zero factor"
        ),
        "expected_g": Fraction(1, 256),
        "expected_8_14_minor": Fraction(225, 4096),
        "expected_candidate_rows": (
            ("5/32", "-3/32", "-1", "0", "0"),
            ("-3/656", "0", "0", "3/32", "0"),
            ("-125/1312", "-45/1312", "-15/82", "15/4", "0"),
            ("0", "0", "0", "0", "0"),
        ),
        "expected_star_rows": (
            ("-1/6", "0", "0", "0", "0"),
            ("1/64", "0", "0", "0", "0"),
            ("0", "0", "0", "0", "0"),
        ),
    },
}

COMMON_ZERO_FACTORS = (
    (12, Fraction(1)),
    (13, Fraction(1, 2)),
    (15, Fraction(1)),
    (44, Fraction(2)),
    (45, Fraction(2)),
)
PAIR_MINOR_SOURCES = ((32, 120), (424, 544), (8, 14))
EXPECTED_COMMON_ZERO_ROWS = {
    "32_120": (
        ("0", "0", "0", "0", "0"),
        ("5/1312", "15/164", "-15/82", "-5/16", "0"),
    ),
    "424_544": (
        ("25/1312", "-45/1312", "45/164", "-15/16", "0"),
        ("0", "0", "0", "0", "0"),
    ),
    "8_14": (
        ("0", "0", "0", "0", "0"),
        ("-1/8", "9/16", "0", "0", "0"),
    ),
}
EXPECTED_COMMON_ZERO_ABC = {
    "32_120": (("0", "0", "0"), ("-5/5248", "-5/1312", "0")),
    "424_544": (("-15/5248", "-5/1312", "0"), ("0", "0", "0")),
    "8_14": (("0", "0", "0"), ("-3/128", "1/16", "0")),
}

SparseRow = dict[str, Fraction]


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


def _remainder(
    source: SparseRow,
    basis: dict[int, dict[int, Fraction]],
    variables: tuple[str, ...],
    q_variables: tuple[str, ...],
) -> SparseRow:
    positions = {variable: index for index, variable in enumerate(variables)}
    row = {positions[variable]: value for variable, value in source.items() if value}
    while row:
        pivot = min(row)
        if pivot not in basis:
            break
        scale = row[pivot]
        for column, value in basis[pivot].items():
            updated = row.get(column, Fraction(0)) - scale * value
            if updated:
                row[column] = updated
            else:
                row.pop(column, None)
    return {
        variable: row.get(positions[variable], Fraction(0))
        for variable in q_variables
        if row.get(positions[variable], Fraction(0))
    }


def _rank(rows: list[SparseRow], variables: tuple[str, ...]) -> int:
    return int(transverse._tracked_row_echelon(rows, variables)["rank"])


def _dense(row: SparseRow, q_variables: tuple[str, ...]) -> list[str]:
    return [str(row.get(variable, Fraction(0))) for variable in q_variables]


def _restriction_row(
    row: SparseRow,
    delta: tuple[Fraction, ...],
    visible: tuple[Fraction, ...],
    q_variables: tuple[str, ...],
) -> SparseRow:
    return {
        "h": sum(
            (
                row.get(q_variables[index], Fraction(0)) * delta[index]
                for index in range(4)
            ),
            start=Fraction(0),
        ),
        "w": sum(
            (
                row.get(q_variables[index], Fraction(0)) * visible[index]
                for index in range(4)
            ),
            start=Fraction(0),
        ),
        "q5": row.get(q_variables[4], Fraction(0)),
    }


def _pair_minor_certificate(
    rows: list[SparseRow],
    delta: tuple[Fraction, ...],
    visible: tuple[Fraction, ...],
    q_variables: tuple[str, ...],
) -> dict[str, Any]:
    if len(rows) != 2:
        raise AssertionError("a pair-minor certificate requires exactly two rows")
    restriction_variables = ("h", "w", "q5")
    restricted = [
        _restriction_row(row, delta, visible, q_variables) for row in rows
    ]
    target = {"w": Fraction(1)}
    pair_minor = (
        restricted[0]["h"] * restricted[1]["w"]
        - restricted[1]["h"] * restricted[0]["w"]
    )
    candidate_rank = _rank(restricted, restriction_variables)
    target_rank = _rank([target], restriction_variables)
    augmented_rank = _rank([*restricted, target], restriction_variables)
    return {
        "restriction_column_order": ["h", "w", "q5"],
        "restriction_rows_ABC": [
            _dense(row, restriction_variables) for row in restricted
        ],
        "all_C_Q5_coefficients_are_zero": all(not row["q5"] for row in restricted),
        "pair_minor_D_AB": str(pair_minor),
        "candidate_rank": candidate_rank,
        "target_e_w_rank": target_rank,
        "candidate_plus_target_e_w_rank": augmented_rank,
        "target_e_w_is_spanned": augmented_rank == candidate_rank,
    }


def _point_certificate(
    context: torus.ScoutContext,
    kernel: list[list[int]],
    lower: locus.LowerCharacter,
    chart_id: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    bottom = locus.bottom_point(context, lower)
    upper = dict(bottom)
    factors: tuple[tuple[int, Fraction], ...] = spec["factors"]
    for column, base in factors:
        for variable_index, variable in enumerate(context.variables):
            upper[variable] *= base ** kernel[column][variable_index]

    joint, _counts, commutators, _paths = torus._linear_system(context, upper, lower)
    q_variables = tuple(
        torus._q_variable(context, stage) for stage in range(1, 5)
    ) + (torus.Q5,)
    non_q = tuple(variable for variable in context.variables if variable not in q_variables)
    ordered_variables = (*non_q, *q_variables)
    pivot_sources = (
        *unit_minor.CPOBC_ROWS,
        *(843 + offset for offset in unit_minor.GC_OFFSETS),
        *(1163 + offset for offset in unit_minor.MSR_OFFSETS),
    )
    pivot_echelon = transverse._tracked_row_echelon(
        [joint[source] for source in pivot_sources], ordered_variables
    )
    basis = pivot_echelon["basis"]

    def reduce(source: SparseRow) -> SparseRow:
        return _remainder(source, basis, ordered_variables, q_variables)

    sources = (*spec["eq120_base_sources"], *spec["proposed_patch_sources"])
    candidate = [reduce(joint[source]) for source in sources]
    star = [
        reduce(commutators[name]) for name in ("Q1_Q2", "Q1_Q3", "Q1_Q4")
    ]
    repair_8_14_rows = [reduce(joint[source]) for source in (8, 14)]
    all_commutators = list(commutators.values())
    m0_sources = (*range(783), *range(843, 1187))
    m0 = [joint[source] for source in m0_sources]
    chart_index = int(spec["chart_index"])
    b1 = lower(1, (0,), 0)
    bi = lower(chart_index, (0,) * chart_index, 0)
    g_value = upper[q_variables[0]] * bi - upper[q_variables[chart_index - 1]] * b1
    delta = tuple(upper[variable] - bottom[variable] for variable in q_variables[:4])
    visible = tuple(
        bottom[variable] / bottom[q_variables[0]] for variable in q_variables[:4]
    )
    repair_8_14 = _pair_minor_certificate(
        repair_8_14_rows, delta, visible, q_variables
    )
    candidate_rank = _rank(candidate, q_variables)
    star_rank = _rank(star, q_variables)
    augmented_rank = _rank([*candidate, *star], q_variables)
    m0_rank = _rank(m0, context.variables)
    m0_all_rank = _rank([*m0, *all_commutators], context.variables)
    candidate_dense = [_dense(row, q_variables) for row in candidate]
    star_dense = [_dense(row, q_variables) for row in star]
    labels, _blocks = transverse._joint_row_labels(context)

    expected_candidate = [list(row) for row in spec["expected_candidate_rows"]]
    expected_star = [list(row) for row in spec["expected_star_rows"]]
    if (
        int(pivot_echelon["rank"]) != 127
        or g_value != spec["expected_g"]
        or not g_value
        or candidate_dense != expected_candidate
        or star_dense != expected_star
        or (candidate_rank, star_rank, augmented_rank) != (3, 1, 4)
        or any(row.get(q_variables[-1], Fraction(0)) for row in candidate)
        or repair_8_14["pair_minor_D_AB"] != str(spec["expected_8_14_minor"])
        or not repair_8_14["all_C_Q5_coefficients_are_zero"]
        or not repair_8_14["target_e_w_is_spanned"]
        or (m0_rank, m0_all_rank) != (131, 131)
    ):
        raise AssertionError(f"the exact {chart_id} repair-pair rejection changed")

    return {
        "chart_id": chart_id,
        "chart_function": f"g{chart_index}=a_Q1*b_Q{chart_index}-a_Q{chart_index}*b_Q1",
        "eq120_base_sources": list(spec["eq120_base_sources"]),
        "proposed_patch_sources": list(spec["proposed_patch_sources"]),
        "all_joint_sources": list(sources),
        "row_ids": [labels[source] for source in sources],
        "row_id_digest_sha256": _digest([labels[source] for source in sources]),
        "exact_positive_rational_slice_point": {
            f"u{column}": str(base) for column, base in factors
        },
        "targeting_rationale": spec["targeting_rationale"],
        "targeting_rationale_is_not_a_global_factorization_certificate": True,
        "g_value": str(g_value),
        "point_is_inside_declared_chart": bool(g_value),
        "pivot_rank": int(pivot_echelon["rank"]),
        "Q_column_order": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        "candidate_schur_rows": candidate_dense,
        "star_schur_rows_c12_c13_c14": star_dense,
        "all_candidate_Q5_components_are_zero": all(
            row[-1] == "0" for row in candidate_dense
        ),
        "candidate_rank": candidate_rank,
        "star_rank": star_rank,
        "candidate_plus_star_rank": augmented_rank,
        "pair_is_rejected_on_its_declared_chart": augmented_rank > candidate_rank,
        "pointwise_eq120_kernel_repair_by_sources_8_14": {
            "joint_sources": [8, 14],
            **repair_8_14,
            "scope": "this exact point on the Eq. (120) kernel only",
        },
        "full_M0_rank": m0_rank,
        "full_M0_plus_all_six_commutators_rank": m0_all_rank,
        "full_M0_has_no_escape_at_this_point": m0_rank == m0_all_rank,
        "residual_data_digest_sha256": _digest(
            {"candidate": candidate_dense, "star": star_dense}
        ),
    }


def _common_zero_certificate(
    context: torus.ScoutContext,
    kernel: list[list[int]],
    lower: locus.LowerCharacter,
) -> dict[str, Any]:
    bottom = locus.bottom_point(context, lower)
    upper = dict(bottom)
    for column, base in COMMON_ZERO_FACTORS:
        for variable_index, variable in enumerate(context.variables):
            upper[variable] *= base ** kernel[column][variable_index]

    joint, _counts, commutators, _paths = torus._linear_system(
        context, upper, lower
    )
    q_variables = tuple(
        torus._q_variable(context, stage) for stage in range(1, 5)
    ) + (torus.Q5,)
    non_q = tuple(variable for variable in context.variables if variable not in q_variables)
    ordered_variables = (*non_q, *q_variables)
    pivot_sources = (
        *unit_minor.CPOBC_ROWS,
        *(843 + offset for offset in unit_minor.GC_OFFSETS),
        *(1163 + offset for offset in unit_minor.MSR_OFFSETS),
    )
    pivot_echelon = transverse._tracked_row_echelon(
        [joint[source] for source in pivot_sources], ordered_variables
    )
    basis = pivot_echelon["basis"]

    def reduce(source: SparseRow) -> SparseRow:
        return _remainder(source, basis, ordered_variables, q_variables)

    star = [
        reduce(commutators[name]) for name in ("Q1_Q2", "Q1_Q3", "Q1_Q4")
    ]
    star_dense = [_dense(row, q_variables) for row in star]
    expected_star = [
        ["1/24", "0", "0", "0", "0"],
        ["1/64", "0", "0", "0", "0"],
        ["0", "0", "0", "0", "0"],
    ]
    delta = tuple(upper[variable] - bottom[variable] for variable in q_variables[:4])
    visible = tuple(
        bottom[variable] / bottom[q_variables[0]] for variable in q_variables[:4]
    )
    labels, _blocks = transverse._joint_row_labels(context)
    pair_records: dict[str, dict[str, Any]] = {}
    for sources in PAIR_MINOR_SOURCES:
        key = f"{sources[0]}_{sources[1]}"
        rows = [reduce(joint[source]) for source in sources]
        dense = [_dense(row, q_variables) for row in rows]
        restriction = _pair_minor_certificate(rows, delta, visible, q_variables)
        q_candidate_rank = _rank(rows, q_variables)
        q_star_rank = _rank(star, q_variables)
        q_augmented_rank = _rank([*rows, *star], q_variables)
        expected_dense = [list(row) for row in EXPECTED_COMMON_ZERO_ROWS[key]]
        expected_abc = [list(row) for row in EXPECTED_COMMON_ZERO_ABC[key]]
        if (
            dense != expected_dense
            or restriction["restriction_rows_ABC"] != expected_abc
            or restriction["pair_minor_D_AB"] != "0"
            or restriction["target_e_w_is_spanned"]
            or (
                restriction["candidate_rank"],
                restriction["target_e_w_rank"],
                restriction["candidate_plus_target_e_w_rank"],
            )
            != (1, 1, 2)
            or (q_candidate_rank, q_star_rank, q_augmented_rank) != (1, 1, 2)
            or any(row.get(q_variables[-1], Fraction(0)) for row in rows)
        ):
            raise AssertionError(f"the exact common-zero pair {sources} changed")
        pair_records[key] = {
            "joint_sources": list(sources),
            "row_ids": [labels[source] for source in sources],
            "Q_column_order": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "Q_schur_rows": dense,
            "Q_candidate_rank": q_candidate_rank,
            "Q_star_rank": q_star_rank,
            "Q_candidate_plus_star_rank": q_augmented_rank,
            "Q_star_is_not_spanned": q_augmented_rank > q_candidate_rank,
            **restriction,
        }

    b1 = lower(1, (0,), 0)
    g_values = {
        f"g{index}": upper[q_variables[0]] * lower(index, (0,) * index, 0)
        - upper[q_variables[index - 1]] * b1
        for index in range(2, 5)
    }
    m0_sources = (*range(783), *range(843, 1187))
    m0 = [joint[source] for source in m0_sources]
    all_commutators = list(commutators.values())
    m0_rank = _rank(m0, context.variables)
    m0_all_rank = _rank([*m0, *all_commutators], context.variables)
    if (
        int(pivot_echelon["rank"]) != 127
        or star_dense != expected_star
        or g_values
        != {"g2": Fraction(1, 96), "g3": Fraction(1, 256), "g4": Fraction(0)}
        or (m0_rank, m0_all_rank) != (131, 131)
    ):
        raise AssertionError("the exact three-pair-minor common zero changed")

    return {
        "exact_positive_rational_slice_point": {
            f"u{column}": str(base) for column, base in COMMON_ZERO_FACTORS
        },
        "chart_function_values": {
            name: str(value) for name, value in g_values.items()
        },
        "lies_in_D_g2_intersect_D_g3": bool(g_values["g2"] and g_values["g3"]),
        "lies_on_V_g4": not g_values["g4"],
        "g4_eq120_base_sources": [147, 548],
        "pivot_rank": int(pivot_echelon["rank"]),
        "Q_column_order": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        "star_schur_rows_c12_c13_c14": star_dense,
        "pair_minor_records": pair_records,
        "all_three_pair_minors_vanish": all(
            record["pair_minor_D_AB"] == "0" for record in pair_records.values()
        ),
        "all_three_pair_restrictions_fail_to_span_e_w": all(
            not record["target_e_w_is_spanned"] for record in pair_records.values()
        ),
        "proposed_pair_minor_opens_do_not_cover_D_g2_or_D_g3": True,
        "full_M0_rank": m0_rank,
        "full_M0_plus_all_six_commutators_rank": m0_all_rank,
        "full_M0_has_no_escape_at_this_point": m0_rank == m0_all_rank,
        "scope": (
            "rejects only the three recorded two-row repair-minor opens as a "
            "subcover; it does not reject D(g2), D(g3), D(g4), or full M0"
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen_unit = _load(root / unit_minor.RESULT_PATH)
    frozen_cover = _load(root / base_cover.RESULT_PATH)
    if (
        frozen_unit.get("verdict") != unit_minor.VERDICT
        or frozen_unit.get("semantic_digest_sha256")
        != unit_minor.semantic_digest(frozen_unit)
        or frozen_cover.get("verdict") != base_cover.VERDICT
        or frozen_cover.get("semantic_digest_sha256")
        != base_cover.semantic_digest(frozen_cover)
    ):
        raise AssertionError("a frozen Eq. (120) repair-pair predecessor binding failed")

    context = torus._build_context(root)
    operator_context = lattice._build_context(root)
    operator_rows, _counts = lattice._operator_lattice_rows(operator_context)
    kernel = lattice._integer_kernel_columns(operator_rows[:783], operator_context.variables)
    lower = locus.bottom_character(unit_minor.REFERENCE_COUPLINGS, unit_minor.REFERENCE_Q5)
    records = {
        chart_id: _point_certificate(context, kernel, lower, chart_id, spec)
        for chart_id, spec in PAIR_SPECS.items()
    }
    common_zero = _common_zero_certificate(context, kernel, lower)
    gates = {
        "unit_minor_is_frozen_and_bound": frozen_unit["verdict"] == unit_minor.VERDICT,
        "eq120_base_cover_is_frozen_and_bound": frozen_cover["verdict"]
        == base_cover.VERDICT,
        "both_points_are_inside_their_declared_charts": all(
            record["point_is_inside_declared_chart"] for record in records.values()
        ),
        "both_proposed_pairs_are_exactly_rejected": all(
            record["pair_is_rejected_on_its_declared_chart"]
            for record in records.values()
        ),
        "both_complete_common_core_checks_remain_131_to_131": all(
            record["full_M0_rank"]
            == record["full_M0_plus_all_six_commutators_rank"]
            == 131
            for record in records.values()
        ),
        "all_selected_Q5_components_are_zero": all(
            record["all_candidate_Q5_components_are_zero"]
            for record in records.values()
        ),
        "sources_8_14_repair_both_older_points_on_the_eq120_kernel": all(
            record["pointwise_eq120_kernel_repair_by_sources_8_14"][
                "target_e_w_is_spanned"
            ]
            for record in records.values()
        ),
        "new_point_is_in_both_g2_and_g3_charts": common_zero[
            "lies_in_D_g2_intersect_D_g3"
        ],
        "all_three_proposed_pair_minors_vanish_at_the_new_point": common_zero[
            "all_three_pair_minors_vanish"
        ],
        "all_three_pair_restrictions_fail_at_the_new_point": common_zero[
            "all_three_pair_restrictions_fail_to_span_e_w"
        ],
        "new_point_complete_common_core_check_remains_131_to_131": common_zero[
            "full_M0_rank"
        ]
        == common_zero["full_M0_plus_all_six_commutators_rank"]
        == 131,
    }
    if not all(gates.values()):
        raise AssertionError(f"Eq. (120) repair-pair scout gate failed: {gates}")

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
                "semantic_digest_sha256": _load(root / relative).get(
                    "semantic_digest_sha256"
                ),
            }
            for relative in (unit_minor.RESULT_PATH, base_cover.RESULT_PATH)
        },
        "frozen_bindings": {
            "unit_minor_verdict": frozen_unit["verdict"],
            "base_cover_verdict": frozen_cover["verdict"],
        },
        "older_repair_pair_rejections": records,
        "three_pair_minor_common_zero": common_zero,
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "the two older chart-open points reject their recorded finite repair "
            "selections, while sources 8 and 14 repair the Eq. (120) kernel there; "
            "the third exact point shows that all three proposed two-row minor opens "
            "still fail to cover D(g2) or D(g3). This rejects only that finite "
            "pair-minor subcover, not an Eq. (120) chart, the complete common core, "
            "or commutativity, and the targeting rationales are not global determinant "
            "factorization certificates"
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
