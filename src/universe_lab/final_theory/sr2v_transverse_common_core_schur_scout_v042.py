"""Exact finite scout and adversarial ledger for the five-Q Schur module.

The global unit minor is a theorem.  This successor uses it to eliminate the
127 non-Q columns, records the original 81 exact rational samples, and freezes
two further exact points that reject two successive fixed-four row selections.
Both rejection points leave the complete common core and all four semantic
branches at rank 131 after adjoining every commutator.  The result is therefore
deliberately nonterminal: it rejects finite row selections, not commutativity.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import sr2v_transverse_common_core_unit_minor_v042 as unit_minor
from universe_lab.final_theory import sr2v_transverse_determinant_zero_locus_v042 as locus
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_transverse_common_core_schur_scout.json"
SCHEMA = "final-theory-v042-sr2v-transverse-common-core-schur-scout-v3"
VERDICT = "SR2V_TRANSVERSE_COMMON_CORE_FIXED4_REJECTED_FULL_M0_NO_ESCAPE_AT_ADVERSARIAL_POINT_OPEN"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_83_EXACT_EVALUATIONS_ONLY"

SECOND_CANDIDATE_SOURCES = (23, 147, 154, 688)
THIRD_CANDIDATE_SOURCES = (23, 31, 147, 688)
THIRD_CANDIDATE_FIXED5_PATCH = (23, 31, 147, 154, 688)
REJECTED_CANDIDATE_SOURCES = (83, 147, 154, 688)
EXPECTED_THREE_ROW_ELIGIBLE_SOURCES = (29, 147, 548)
F7_COLUMNS_AND_BASES = ((12, 2), (13, 3), (15, 5), (44, 7), (45, 11))
SECOND_CANDIDATE_ADVERSARIAL_FACTORS = (
    (12, Fraction(2)),
    (13, Fraction(3)),
    (15, Fraction(5)),
    (44, Fraction(21)),
    (45, Fraction(7)),
)
THIRD_CANDIDATE_ADVERSARIAL_FACTORS = (
    (12, Fraction(1, 2)),
    (13, Fraction(1)),
    (15, Fraction(1)),
    (44, Fraction(1)),
    (45, Fraction(2)),
)

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


def _power(base: int | Fraction, exponent: int) -> Fraction:
    value = Fraction(base)
    return value**exponent


def _samples(
    context: torus.ScoutContext,
    kernel: list[list[int]],
) -> tuple[locus.LowerCharacter, list[dict[str, Any]]]:
    lower = locus.bottom_character(unit_minor.REFERENCE_COUPLINGS, unit_minor.REFERENCE_Q5)
    bottom = locus.bottom_point(context, lower)
    records: list[dict[str, Any]] = []

    def add(identifier: str, factors: tuple[tuple[int, int], ...], family: str) -> None:
        upper = dict(bottom)
        for column, base in factors:
            for variable_index, variable in enumerate(context.variables):
                upper[variable] *= _power(base, kernel[column][variable_index])
        records.append(
            {
                "sample_id": identifier,
                "family": family,
                "factors": [
                    {"kernel_column": column, "base": base} for column, base in factors
                ],
                "upper": upper,
            }
        )

    add("B0_equal", (), "reference_equal")
    for column in range(49):
        add(f"F1_K{column:02d}", ((column, 2),), "all_49_single_directions")
    for mask in range(1, 1 << len(F7_COLUMNS_AND_BASES)):
        factors = tuple(
            factor for index, factor in enumerate(F7_COLUMNS_AND_BASES) if mask & (1 << index)
        )
        add(f"F7_mask_{mask:02d}", factors, "all_31_nonempty_F7_supports")
    if len(records) != 81:
        raise AssertionError("the exact Schur scout no longer has 81 evaluations")
    return lower, records


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


def _rank(rows: list[SparseRow], q_variables: tuple[str, ...]) -> int:
    return int(transverse._tracked_row_echelon(rows, q_variables)["rank"])


def _minor_record(rows: list[SparseRow], q_variables: tuple[str, ...]) -> dict[str, Any]:
    echelon = transverse._tracked_row_echelon(rows, q_variables)
    rank = int(echelon["rank"])
    determinant = Fraction(1)
    for pivot in echelon["raw_pivots"]:
        determinant *= pivot
    if int(echelon["column_permutation_inversion_parity"]):
        determinant *= -1
    return {
        "rank": rank,
        "selected_candidate_row_offsets": list(echelon["selected_indices"]),
        "selected_Q_column_offsets": list(echelon["pivot_sequence"]),
        "determinant": str(determinant),
        "nonzero_when_positive_rank": rank == 0 or bool(determinant),
    }


def _rank_key(candidate: int, star: int, augmented: int) -> str:
    return f"{candidate}/{star}/{augmented}"


def scout_certificate(
    root: Path,
    context: torus.ScoutContext,
    kernel: list[list[int]],
) -> dict[str, Any]:
    lower, samples = _samples(context, kernel)
    labels, _blocks = transverse._joint_row_labels(context)
    pivot_sources = (
        *unit_minor.CPOBC_ROWS,
        *(843 + offset for offset in unit_minor.GC_OFFSETS),
        *(1163 + offset for offset in unit_minor.MSR_OFFSETS),
    )
    m0_sources = (*range(783), *range(843, 1187))
    q_variables = tuple(torus._q_variable(context, stage) for stage in range(1, 5)) + (
        torus.Q5,
    )
    non_q = tuple(variable for variable in context.variables if variable not in q_variables)
    ordered_variables = (*non_q, *q_variables)

    second_candidate_ids = [labels[source] for source in SECOND_CANDIDATE_SOURCES]
    third_candidate_ids = [labels[source] for source in THIRD_CANDIDATE_SOURCES]
    rejected_ids = [labels[source] for source in REJECTED_CANDIDATE_SOURCES]
    records = []
    rank_census: Counter[str] = Counter()
    third_rank_census: Counter[str] = Counter()
    rejected_failures = []
    removal_failures: dict[str, list[str]] = {
        str(source): [] for source in SECOND_CANDIDATE_SOURCES
    }
    three_row_eligible = set(m0_sources)
    star_rank_three_samples = 0

    for sample in samples:
        joint, _counts, commutators, _paths = torus._linear_system(
            context, sample["upper"], lower
        )
        pivot_rows = [joint[source] for source in pivot_sources]
        pivot_echelon = transverse._tracked_row_echelon(pivot_rows, ordered_variables)
        if (
            pivot_echelon["rank"] != 127
            or set(pivot_echelon["basis"]) != set(range(127))
        ):
            raise AssertionError("the global unit block failed at an exact scout point")
        basis = pivot_echelon["basis"]

        def reduce(
            source: SparseRow,
            current_basis: dict[int, dict[int, Fraction]] = basis,
        ) -> SparseRow:
            return _remainder(source, current_basis, ordered_variables, q_variables)

        candidate = [reduce(joint[source]) for source in SECOND_CANDIDATE_SOURCES]
        third_candidate = [reduce(joint[source]) for source in THIRD_CANDIDATE_SOURCES]
        rejected = [reduce(joint[source]) for source in REJECTED_CANDIDATE_SOURCES]
        star = [
            reduce(commutators[name])
            for name in ("Q1_Q2", "Q1_Q3", "Q1_Q4")
        ]
        candidate_rank = _rank(candidate, q_variables)
        star_rank = _rank(star, q_variables)
        augmented_rank = _rank([*candidate, *star], q_variables)
        rejected_rank = _rank(rejected, q_variables)
        rejected_augmented = _rank([*rejected, *star], q_variables)
        third_candidate_rank = _rank(third_candidate, q_variables)
        third_augmented_rank = _rank([*third_candidate, *star], q_variables)
        rank_census[_rank_key(candidate_rank, star_rank, augmented_rank)] += 1
        third_rank_census[
            _rank_key(third_candidate_rank, star_rank, third_augmented_rank)
        ] += 1
        if rejected_rank != rejected_augmented:
            rejected_failures.append(sample["sample_id"])
        for removed_index, source in enumerate(SECOND_CANDIDATE_SOURCES):
            retained = [row for index, row in enumerate(candidate) if index != removed_index]
            if _rank(retained, q_variables) != _rank([*retained, *star], q_variables):
                removal_failures[str(source)].append(sample["sample_id"])

        if star_rank == 3:
            star_rank_three_samples += 1
            surviving = set()
            for source in three_row_eligible:
                row = reduce(joint[source])
                if _rank([row], q_variables) == 1 and _rank([*star, row], q_variables) == 3:
                    surviving.add(source)
            three_row_eligible = surviving

        record = {
            "sample_id": sample["sample_id"],
            "family": sample["family"],
            "factors": sample["factors"],
            "candidate_rank": candidate_rank,
            "star_rank": star_rank,
            "augmented_rank": augmented_rank,
            "candidate_spans_star": candidate_rank == augmented_rank,
            "candidate_rank_minor": _minor_record(candidate, q_variables),
            "rejected_candidate_rank": rejected_rank,
            "rejected_augmented_rank": rejected_augmented,
            "third_candidate_rank": third_candidate_rank,
            "third_augmented_rank": third_augmented_rank,
            "third_candidate_spans_star": third_candidate_rank == third_augmented_rank,
        }
        records.append(record)

    eligible = tuple(sorted(three_row_eligible))
    if eligible != EXPECTED_THREE_ROW_ELIGIBLE_SOURCES:
        raise AssertionError("the exact fixed-three eligibility filter changed")

    three_row_failures = []
    for sample in samples:
        joint, _counts, commutators, _paths = torus._linear_system(
            context, sample["upper"], lower
        )
        pivot_rows = [joint[source] for source in pivot_sources]
        basis = transverse._tracked_row_echelon(pivot_rows, ordered_variables)["basis"]
        triple = [
            _remainder(joint[source], basis, ordered_variables, q_variables)
            for source in eligible
        ]
        star = [
            _remainder(commutators[name], basis, ordered_variables, q_variables)
            for name in ("Q1_Q2", "Q1_Q3", "Q1_Q4")
        ]
        if _rank(triple, q_variables) != _rank([*triple, *star], q_variables):
            three_row_failures.append(sample["sample_id"])

    adversarial_upper = locus.bottom_point(context, lower)
    for column, base in SECOND_CANDIDATE_ADVERSARIAL_FACTORS:
        for variable_index, variable in enumerate(context.variables):
            adversarial_upper[variable] *= _power(base, kernel[column][variable_index])
    adversarial_joint, _counts, adversarial_commutators, _paths = torus._linear_system(
        context, adversarial_upper, lower
    )
    adversarial_pivot_rows = [adversarial_joint[source] for source in pivot_sources]
    adversarial_basis = transverse._tracked_row_echelon(
        adversarial_pivot_rows, ordered_variables
    )["basis"]
    adversarial_candidate = [
        _remainder(
            adversarial_joint[source],
            adversarial_basis,
            ordered_variables,
            q_variables,
        )
        for source in SECOND_CANDIDATE_SOURCES
    ]
    third_candidate_at_second_point = [
        _remainder(
            adversarial_joint[source],
            adversarial_basis,
            ordered_variables,
            q_variables,
        )
        for source in THIRD_CANDIDATE_SOURCES
    ]
    adversarial_star = [
        _remainder(
            adversarial_commutators[name],
            adversarial_basis,
            ordered_variables,
            q_variables,
        )
        for name in ("Q1_Q2", "Q1_Q3", "Q1_Q4")
    ]
    adversarial_candidate_rank = _rank(adversarial_candidate, q_variables)
    adversarial_star_rank = _rank(adversarial_star, q_variables)
    adversarial_augmented_rank = _rank(
        [*adversarial_candidate, *adversarial_star], q_variables
    )
    third_at_second_rank = _rank(third_candidate_at_second_point, q_variables)
    third_at_second_augmented_rank = _rank(
        [*third_candidate_at_second_point, *adversarial_star], q_variables
    )
    adversarial_m0 = [adversarial_joint[source] for source in m0_sources]
    adversarial_all_commutators = list(adversarial_commutators.values())
    adversarial_m0_rank = int(
        transverse._tracked_row_echelon(adversarial_m0, context.variables)["rank"]
    )
    adversarial_m0_star_rank = int(
        transverse._tracked_row_echelon(
            [*adversarial_m0, *adversarial_star], context.variables
        )["rank"]
    )
    adversarial_m0_all_commutator_rank = int(
        transverse._tracked_row_echelon(
            [*adversarial_m0, *adversarial_all_commutators], context.variables
        )["rank"]
    )
    adversarial_branches = {}
    for branch_id, (eq113, eq139) in locus.BRANCH_SPECS.items():
        branch = locus.branch_matrix(
            context,
            adversarial_upper,
            lower,
            adversarial_joint,
            eq113,
            eq139,
        )
        branch_rank = int(transverse._tracked_row_echelon(branch, context.variables)["rank"])
        augmented = int(
            transverse._tracked_row_echelon(
                [*branch, *adversarial_all_commutators], context.variables
            )["rank"]
        )
        adversarial_branches[branch_id] = {
            "rank": branch_rank,
            "rank_with_all_six_commutators": augmented,
            "escape": augmented > branch_rank,
        }
    adversarial_delta = [
        adversarial_upper[torus._q_variable(context, stage)]
        - lower(stage, (0,) * stage, 0)
        for stage in range(1, 5)
    ]

    # The third fixed-four selection passes the original 81 points and the
    # preceding adversarial point.  Its own determinant numerator is linear in
    # u12 on the five-direction B0 slice, so the following positive rational
    # point is an exact point of that hypersurface rather than a random sample.
    third_adversarial_upper = locus.bottom_point(context, lower)
    for column, base in THIRD_CANDIDATE_ADVERSARIAL_FACTORS:
        for variable_index, variable in enumerate(context.variables):
            third_adversarial_upper[variable] *= _power(
                base, kernel[column][variable_index]
            )
    third_joint, _counts, third_commutators, _paths = torus._linear_system(
        context, third_adversarial_upper, lower
    )
    third_pivot_rows = [third_joint[source] for source in pivot_sources]
    third_pivot_echelon = transverse._tracked_row_echelon(
        third_pivot_rows, ordered_variables
    )
    third_basis = third_pivot_echelon["basis"]

    def third_reduce(source: SparseRow) -> SparseRow:
        return _remainder(source, third_basis, ordered_variables, q_variables)

    third_candidate = [
        third_reduce(third_joint[source]) for source in THIRD_CANDIDATE_SOURCES
    ]
    third_fixed5 = [
        third_reduce(third_joint[source])
        for source in THIRD_CANDIDATE_FIXED5_PATCH
    ]
    third_star = [
        third_reduce(third_commutators[name])
        for name in ("Q1_Q2", "Q1_Q3", "Q1_Q4")
    ]
    third_candidate_rank = _rank(third_candidate, q_variables)
    third_star_rank = _rank(third_star, q_variables)
    third_augmented_rank = _rank([*third_candidate, *third_star], q_variables)
    third_fixed5_rank = _rank(third_fixed5, q_variables)
    third_m0 = [third_joint[source] for source in m0_sources]
    third_all_commutators = list(third_commutators.values())
    third_m0_rank = int(
        transverse._tracked_row_echelon(third_m0, context.variables)["rank"]
    )
    third_m0_star_rank = int(
        transverse._tracked_row_echelon(
            [*third_m0, *third_star], context.variables
        )["rank"]
    )
    third_m0_all_commutator_rank = int(
        transverse._tracked_row_echelon(
            [*third_m0, *third_all_commutators], context.variables
        )["rank"]
    )
    third_branches = {}
    for branch_id, (eq113, eq139) in locus.BRANCH_SPECS.items():
        branch = locus.branch_matrix(
            context,
            third_adversarial_upper,
            lower,
            third_joint,
            eq113,
            eq139,
        )
        branch_rank = int(
            transverse._tracked_row_echelon(branch, context.variables)["rank"]
        )
        augmented = int(
            transverse._tracked_row_echelon(
                [*branch, *third_all_commutators], context.variables
            )["rank"]
        )
        third_branches[branch_id] = {
            "rank": branch_rank,
            "rank_with_all_six_commutators": augmented,
            "escape": augmented > branch_rank,
        }
    third_delta = [
        third_adversarial_upper[torus._q_variable(context, stage)]
        - lower(stage, (0,) * stage, 0)
        for stage in range(1, 5)
    ]

    def dense_q(row: SparseRow) -> list[str]:
        return [str(row.get(variable, Fraction(0))) for variable in q_variables]

    third_candidate_dense = [dense_q(row) for row in third_candidate]
    third_star_dense = [dense_q(row) for row in third_star]
    third_row154_dense = dense_q(third_fixed5[3])
    escaping_q_vector = [Fraction(0), Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    star_evaluations = [
        sum(
            row.get(variable, Fraction(0)) * coordinate
            for variable, coordinate in zip(q_variables, escaping_q_vector, strict=True)
        )
        for row in third_star
    ]

    expected_census = {
        "0/0/0": 37,
        "1/0/1": 3,
        "2/1/2": 5,
        "3/1/3": 3,
        "3/3/3": 2,
        "4/1/4": 2,
        "4/3/4": 29,
    }
    expected_third_census = {
        "0/0/0": 39,
        "1/0/1": 1,
        "2/1/2": 5,
        "3/1/3": 3,
        "3/3/3": 2,
        "4/1/4": 2,
        "4/3/4": 29,
    }
    if (
        dict(sorted(rank_census.items())) != expected_census
        or dict(sorted(third_rank_census.items())) != expected_third_census
        or any(not record["candidate_spans_star"] for record in records)
        or any(not record["third_candidate_spans_star"] for record in records)
        or len(rejected_failures) != 5
        or star_rank_three_samples != 31
        or len(three_row_failures) != 41
        or (
            adversarial_candidate_rank,
            adversarial_star_rank,
            adversarial_augmented_rank,
        )
        != (3, 3, 4)
        or (third_at_second_rank, third_at_second_augmented_rank) != (4, 4)
        or (
            adversarial_m0_rank,
            adversarial_m0_star_rank,
            adversarial_m0_all_commutator_rank,
        )
        != (131, 131, 131)
        or any(record["escape"] for record in adversarial_branches.values())
        or int(third_pivot_echelon["rank"]) != 127
        or (third_candidate_rank, third_star_rank, third_augmented_rank) != (3, 3, 4)
        or third_fixed5_rank != 4
        or (third_m0_rank, third_m0_star_rank, third_m0_all_commutator_rank)
        != (131, 131, 131)
        or any(record["escape"] for record in third_branches.values())
        or third_delta
        != [Fraction(-1, 8), Fraction(0), Fraction(-1, 64), Fraction(-1, 164)]
        or third_candidate_dense
        != [
            ["5/192", "0", "0", "0", "0"],
            ["1/32", "0", "-1/4", "0", "0"],
            ["1/82", "0", "0", "-1/4", "0"],
            ["0", "0", "0", "0", "0"],
        ]
        or third_star_dense
        != [
            ["0", "-1/8", "0", "0", "0"],
            ["1/64", "0", "-1/8", "0", "0"],
            ["1/164", "0", "0", "-1/8", "0"],
        ]
        or third_row154_dense != ["19/1640", "153/3280", "-32/205", "-1/4", "0"]
        or star_evaluations != [Fraction(-1, 8), Fraction(0), Fraction(0)]
        or any(
            sum(
                row.get(variable, Fraction(0)) * coordinate
                for variable, coordinate in zip(
                    q_variables, escaping_q_vector, strict=True
                )
            )
            for row in third_candidate
        )
        or any(
            not record["candidate_rank_minor"]["nonzero_when_positive_rank"]
            for record in records
        )
    ):
        raise AssertionError("the exact five-Q Schur scout ledger changed")

    serial_records = [
        {
            **record,
            "candidate_rank_minor": record["candidate_rank_minor"],
        }
        for record in records
    ]
    return {
        "common_core": "raw CPOBC + fixed-vector GC + reachable-state MSR",
        "unit_minor_binding": {
            "verdict": unit_minor.VERDICT,
            "semantic_digest_sha256": _load(root / unit_minor.RESULT_PATH)[
                "semantic_digest_sha256"
            ],
        },
        "Q_column_order": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        "pivot_row_count": len(pivot_sources),
        "second_fixed_four_candidate": {
            "joint_sources": list(SECOND_CANDIDATE_SOURCES),
            "row_ids": second_candidate_ids,
            "row_id_digest_sha256": _digest(second_candidate_ids),
            "passes_all_81_exact_points": True,
            "global_candidate_status": "REJECTED_BY_EXACT_ADVERSARIAL_POINT",
            "rank_census_candidate_star_augmented": expected_census,
            "records_digest_sha256": _digest(serial_records),
            "rank_minor_records_digest_sha256": _digest(
                [record["candidate_rank_minor"] for record in serial_records]
            ),
            "each_single_row_removal_failure_counts": {
                source: len(failures) for source, failures in removal_failures.items()
            },
        },
        "third_fixed_four_candidate": {
            "joint_sources": list(THIRD_CANDIDATE_SOURCES),
            "row_ids": third_candidate_ids,
            "row_id_digest_sha256": _digest(third_candidate_ids),
            "passes_original_81_exact_points": True,
            "passes_preceding_82_point_ledger": third_at_second_rank
            == third_at_second_augmented_rank,
            "rank_census_over_original_81_candidate_star_augmented": (
                expected_third_census
            ),
            "rank_at_second_candidate_adversarial_point": third_at_second_rank,
            "augmented_rank_at_second_candidate_adversarial_point": (
                third_at_second_augmented_rank
            ),
            "global_candidate_status": "REJECTED_BY_83RD_EXACT_ADVERSARIAL_POINT",
            "records_digest_sha256": _digest(
                [
                    {
                        "sample_id": record["sample_id"],
                        "rank": record["third_candidate_rank"],
                        "star_rank": record["star_rank"],
                        "augmented_rank": record["third_augmented_rank"],
                    }
                    for record in serial_records
                ]
            ),
        },
        "rejected_predecessor_candidate": {
            "joint_sources": list(REJECTED_CANDIDATE_SOURCES),
            "row_ids": rejected_ids,
            "failure_count": len(rejected_failures),
            "failure_sample_ids": rejected_failures,
            "must_not_be_reused": True,
        },
        "second_fixed_four_adversarial_rejection": {
            "factors": [
                {"kernel_column": column, "base": str(base)}
                for column, base in SECOND_CANDIDATE_ADVERSARIAL_FACTORS
            ],
            "targeted_symbolic_hypersurface": "u13*u45-u44=0",
            "delta_Q": [str(value) for value in adversarial_delta],
            "candidate_rank": adversarial_candidate_rank,
            "star_rank": adversarial_star_rank,
            "candidate_plus_star_rank": adversarial_augmented_rank,
            "candidate_fails_to_span_star": adversarial_augmented_rank
            > adversarial_candidate_rank,
            "full_M0_rank": adversarial_m0_rank,
            "full_M0_plus_star_rank": adversarial_m0_star_rank,
            "full_M0_plus_all_six_commutators_rank": adversarial_m0_all_commutator_rank,
            "full_M0_has_no_escape_at_this_point": (
                adversarial_m0_rank
                == adversarial_m0_star_rank
                == adversarial_m0_all_commutator_rank
            ),
            "four_semantic_branches": adversarial_branches,
            "conclusion": (
                "the 81-point fixed-four candidate is false globally, but the complete "
                "common core and all four semantic branches still contain every "
                "commutator row at this adversarial point"
            ),
        },
        "third_fixed_four_adversarial_rejection": {
            "sample_id": "ADV3_positive_rational_determinant_zero",
            "family": "symbolic_determinant_hypersurface_adversarial",
            "exact_slice_point": {
                f"u{column}": str(base)
                for column, base in THIRD_CANDIDATE_ADVERSARIAL_FACTORS
            },
            "factors": [
                {"kernel_column": column, "base": str(base)}
                for column, base in THIRD_CANDIDATE_ADVERSARIAL_FACTORS
            ],
            "symbolic_determinant_numerator": {
                "slice_variables": ["u12", "u13", "u15", "u44", "u45"],
                "total_degree": 10,
                "term_count": 88,
                "degree_in_u12": 1,
                "factorization_over_Q": "irreducible",
                "value_at_exact_slice_point": "0",
            },
            "pivot_rank": int(third_pivot_echelon["rank"]),
            "delta_Q": [str(value) for value in third_delta],
            "candidate_schur_rows": third_candidate_dense,
            "star_schur_rows_c12_c13_c14": third_star_dense,
            "residual_data_digest_sha256": _digest(
                {
                    "candidate": third_candidate_dense,
                    "star": third_star_dense,
                }
            ),
            "candidate_rank": third_candidate_rank,
            "star_rank": third_star_rank,
            "candidate_plus_star_rank": third_augmented_rank,
            "candidate_fails_to_span_star": third_augmented_rank
            > third_candidate_rank,
            "escaping_Q_vector": [str(value) for value in escaping_q_vector],
            "candidate_evaluations_on_escape": ["0", "0", "0", "0"],
            "star_evaluations_on_escape": [str(value) for value in star_evaluations],
            "fixed5_patch": {
                "joint_sources": list(THIRD_CANDIDATE_FIXED5_PATCH),
                "rank": third_fixed5_rank,
                "row154_schur_residual": third_row154_dense,
                "status": "POINTWISE_PATCH_ONLY_NOT_A_GLOBAL_CANDIDATE",
            },
            "full_common_core_check": {
                "rank": third_m0_rank,
                "rank_with_star": third_m0_star_rank,
                "rank_with_all_six_commutators": third_m0_all_commutator_rank,
                "escape": not (
                    third_m0_rank
                    == third_m0_star_rank
                    == third_m0_all_commutator_rank
                ),
            },
            "four_branch_checks": third_branches,
            "conclusion": (
                "the third fixed-four candidate has the exact escape e_Q2, while the "
                "complete common core and all four semantic branches remain 131->131"
            ),
        },
        "sample_ledger": {
            "original_evaluation_count": len(samples),
            "total_evaluations_including_adversarial": len(samples) + 2,
            "distinct_point_count": 82,
            "families": {
                "reference_equal": 1,
                "all_49_single_directions": 49,
                "all_31_nonempty_F7_supports": 31,
                "symbolic_hypersurface_adversarial": 2,
            },
            "original_81_input_digest_sha256": _digest(
                [
                    {
                        "sample_id": sample["sample_id"],
                        "family": sample["family"],
                        "factors": sample["factors"],
                    }
                    for sample in samples
                ]
            ),
            "all_83_input_digest_sha256": _digest(
                [
                    *[
                        {
                            "sample_id": sample["sample_id"],
                            "family": sample["family"],
                            "factors": sample["factors"],
                        }
                        for sample in samples
                    ],
                    {
                        "sample_id": "ADV2_u13_u45_minus_u44",
                        "family": "symbolic_hypersurface_adversarial",
                        "factors": [
                            {"kernel_column": column, "base": str(base)}
                            for column, base in SECOND_CANDIDATE_ADVERSARIAL_FACTORS
                        ],
                    },
                    {
                        "sample_id": "ADV3_positive_rational_determinant_zero",
                        "family": "symbolic_hypersurface_adversarial",
                        "factors": [
                            {"kernel_column": column, "base": str(base)}
                            for column, base in THIRD_CANDIDATE_ADVERSARIAL_FACTORS
                        ],
                    },
                ]
            ),
            "records": serial_records,
            "adversarial_record_ids": [
                "ADV2_u13_u45_minus_u44",
                "ADV3_positive_rational_determinant_zero",
            ],
        },
        "fixed_three_row_sample_minimality": {
            "star_rank_three_sample_count": star_rank_three_samples,
            "all_1127_common_core_sources_filtered": True,
            "eligible_sources_nonzero_and_inside_star_at_all_rank_three_points": list(eligible),
            "eligible_row_ids": [labels[source] for source in eligible],
            "unique_eligible_triple_failure_count_over_81": len(three_row_failures),
            "unique_eligible_triple_failure_sample_ids": three_row_failures,
            "no_fixed_three_or_smaller_set_can_pass_this_ledger": True,
            "claim_scope": "finite 81-point ledger only",
        },
        "exact_arithmetic": "QQ",
        "full_common_core_witnesses_found": 0,
        "conclusion": (
            "two successive fixed-four raw CPOBC selections are exactly rejected at "
            "the 82nd and 83rd points; the full common core and all four semantic "
            "branches have no escape at either point, so global Schur membership "
            "remains open"
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen_unit = _load(root / unit_minor.RESULT_PATH)
    frozen_lattice = _load(root / lattice.RESULT_PATH)
    if (
        frozen_unit.get("verdict") != unit_minor.VERDICT
        or frozen_unit.get("semantic_digest_sha256") != unit_minor.semantic_digest(frozen_unit)
        or frozen_lattice.get("verdict") != lattice.VERDICT
        or frozen_lattice.get("semantic_digest_sha256") != lattice.semantic_digest(frozen_lattice)
    ):
        raise AssertionError("a frozen Schur-scout predecessor binding failed")
    context = torus._build_context(root)
    operator_context = lattice._build_context(root)
    operator_rows, _counts = lattice._operator_lattice_rows(operator_context)
    kernel = lattice._integer_kernel_columns(operator_rows[:783], operator_context.variables)
    certificate = scout_certificate(root, context, kernel)
    gates = {
        "global_unit_minor_is_bound": certificate["unit_minor_binding"]["verdict"]
        == unit_minor.VERDICT,
        "second_fixed_four_passes_original_81_points": certificate[
            "second_fixed_four_candidate"
        ]["passes_all_81_exact_points"],
        "second_fixed_four_is_rejected_at_point_82": certificate[
            "second_fixed_four_adversarial_rejection"
        ]["candidate_fails_to_span_star"],
        "third_fixed_four_passes_preceding_82_points": certificate[
            "third_fixed_four_candidate"
        ]["passes_preceding_82_point_ledger"],
        "third_fixed_four_is_rejected_at_point_83": certificate[
            "third_fixed_four_adversarial_rejection"
        ]["candidate_fails_to_span_star"],
        "full_common_core_has_no_escape_at_point_82": certificate[
            "second_fixed_four_adversarial_rejection"
        ]["full_M0_has_no_escape_at_this_point"],
        "full_common_core_has_no_escape_at_point_83": not certificate[
            "third_fixed_four_adversarial_rejection"
        ]["full_common_core_check"]["escape"],
        "old_undercovered_candidate_is_rejected": certificate[
            "rejected_predecessor_candidate"
        ]["failure_count"]
        == 5,
        "fixed_three_is_impossible_on_the_frozen_ledger": certificate[
            "fixed_three_row_sample_minimality"
        ]["no_fixed_three_or_smaller_set_can_pass_this_ledger"],
        "no_full_common_core_exact_sample_escape_was_found": certificate[
            "full_common_core_witnesses_found"
        ]
        == 0,
    }
    if not all(gates.values()):
        raise AssertionError(f"five-Q Schur scout gate failed: {gates}")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_under_study": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: {
                "raw_sha256": _sha256(root / relative),
                "semantic_digest_sha256": _load(root / relative).get("semantic_digest_sha256"),
            }
            for relative in (unit_minor.RESULT_PATH, lattice.RESULT_PATH)
        },
        "scout_certificate": certificate,
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "all ranks and residuals are exact over QQ; the original 81-point ledger "
            "proves only sample minimality and two successive fixed-four candidates are "
            "now exactly rejected at points 82 and 83; the pointwise 131->131 checks do "
            "not prove global Schur row-module membership or commutativity"
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
