"""Exact scalar relation lattices for the SR2-V reducible search.

This module independently rebuilds the two integer exponent lattices used by
the transverse upper-triangular search.  It reads frozen source artifacts but
does not import the bounded torus scout or any of its linear-algebra helpers.

The first block contains the 783 raw CPOBC word equations, both 25-row
Eq. (113) branches, and ten explicitly retained scalar-zero rows for the
Eq. (145)-completed reading of Eq. (139).  The second block appends the 320
fixed-vector-GC path-basis exponent equations for the observed diagonal
character.  Smith normal forms and primitive integer kernels are computed
over ``ZZ``; no floating-point or finite-field arithmetic is used.

The result is a scalar-lattice/provenance certificate only.  It does not add
the 24 additive MSR equations, solve an upper-right cocycle fibre, prove
commutativity, or issue an SR2-V search terminal.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.matrices.normalforms import smith_normal_form
from sympy.polys.domains import ZZ

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
OPERATOR_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
ATOMISATION_PATH = "results/v0.3.3_atomisation_paths_n4.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
RESULT_PATH = "results/v0.4.2_sr2v_scalar_lattice.json"

SCHEMA = "final-theory-v042-sr2v-scalar-lattice-snf-v1"
VERDICT = "SR2V_SCALAR_LATTICE_SNF_CERTIFIED_NONTERMINAL"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_SCALAR_LATTICE_ONLY"

EQ113_DERIVED = "EQ113_QN_BRANCH"
EQ113_LITERAL = "EQ113_QN_PLUS_1_BRANCH"
EQ139_STRICT = "EQ139_PRINTED_STRICT_M_K_LT_N"
EQ139_COMPLETED = "EQ139_EQ145_COMPLETED_M_K_LE_N"
Q5 = "Q_5_EXTERNAL"

SparseIntegerRow = dict[str, int]
LabelledRow = tuple[str, SparseIntegerRow]


@dataclass(frozen=True)
class LatticeContext:
    """Frozen transition and path namespaces needed for the scalar lattices."""

    cpobc: dict[str, Any]
    reduction: dict[str, Any]
    operator_gc: dict[str, Any]
    atomisation: dict[str, Any]
    eq112: dict[str, Any]
    occurrence_records: dict[str, dict[str, Any]]
    occurrence_variables: dict[str, str]
    signature_variables: dict[tuple[int, int, int], str]
    b_signatures: dict[str, str]
    variables: tuple[str, ...]


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


def _relation_code(relation: Iterable[int]) -> int:
    rows = tuple(int(row) for row in relation)
    size = len(rows)
    return sum(row << (index * size) for index, row in enumerate(rows))


def _signature(stage: int, relation: Iterable[int], precursor: int) -> tuple[int, int, int]:
    return stage, _relation_code(relation), precursor


def _decode_relation(stage: int, relation_code: int) -> tuple[int, ...]:
    mask = (1 << stage) - 1
    return tuple((relation_code >> (row * stage)) & mask for row in range(stage))


def _clean(row: dict[str, int]) -> SparseIntegerRow:
    return {variable: int(value) for variable, value in row.items() if value}


def _add_rows(*rows: SparseIntegerRow) -> SparseIntegerRow:
    result: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        for variable, value in row.items():
            result[variable] += int(value)
    return _clean(dict(result))


def _scale_row(coefficient: int, row: SparseIntegerRow) -> SparseIntegerRow:
    return _clean({variable: coefficient * value for variable, value in row.items()})


def _word_exponents(tokens: Iterable[str], token_variables: dict[str, str]) -> SparseIntegerRow:
    result: defaultdict[str, int] = defaultdict(int)
    for token in tokens:
        result[token_variables[token]] += 1
    return _clean(dict(result))


def _build_context(root: Path) -> LatticeContext:
    artifacts = {
        CPOBC_PATH: _load(root / CPOBC_PATH),
        REDUCTION_PATH: _load(root / REDUCTION_PATH),
        OPERATOR_GC_PATH: _load(root / OPERATOR_GC_PATH),
        ATOMISATION_PATH: _load(root / ATOMISATION_PATH),
        EQ112_PATH: _load(root / EQ112_PATH),
    }
    reduction = artifacts[REDUCTION_PATH]
    reduction_map = reduction.get("reduction_map")
    if not isinstance(reduction_map, list) or len(reduction_map) != 165:
        raise AssertionError("expected the frozen 165 occurrence/alias records")

    occurrence_records = {
        str(record["occurrence_id"]): record for record in reduction_map
    }
    occurrence_variables = {
        occurrence: str(record["orbit_id"])
        for occurrence, record in occurrence_records.items()
    }
    if len(set(occurrence_variables.values())) != 131:
        raise AssertionError("expected 131 ON quotient transition orbits")

    signature_variables: dict[tuple[int, int, int], str] = {}
    for record in occurrence_records.values():
        key = _signature(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        variable = str(record["orbit_id"])
        previous = signature_variables.setdefault(key, variable)
        if previous != variable:
            raise AssertionError("one transition signature has two ON orbit variables")

    b_signatures: dict[str, str] = {}
    for causet in artifacts[ATOMISATION_PATH]["causets"]:
        for path in causet["all_alternative_paths"]:
            for factor in path["B_operator_factors"]:
                identifier = str(factor["B_occurrence_id"]).removeprefix("B-occurrence-")
                signature = factor["B_transition_signature"]
                stage = int(signature["stage"])
                relation_code = int(signature["source_relation_code"])
                precursor = int(signature["precursor_code"])
                variable = signature_variables[(stage, relation_code, precursor)]
                if len(_decode_relation(stage, relation_code)) != stage:
                    raise AssertionError("a B signature has an invalid relation encoding")
                previous = b_signatures.setdefault(identifier, variable)
                if previous != variable:
                    raise AssertionError("one Eq. (113) B token has two transition variables")

    variables = tuple(sorted(set(occurrence_variables.values())) + [Q5])
    if len(variables) != 132:
        raise AssertionError("expected 131 quotient variables plus cutoff-external Q5")

    return LatticeContext(
        cpobc=artifacts[CPOBC_PATH],
        reduction=reduction,
        operator_gc=artifacts[OPERATOR_GC_PATH],
        atomisation=artifacts[ATOMISATION_PATH],
        eq112=artifacts[EQ112_PATH],
        occurrence_records=occurrence_records,
        occurrence_variables=occurrence_variables,
        signature_variables=signature_variables,
        b_signatures=b_signatures,
        variables=variables,
    )


def _q_variable(context: LatticeContext, stage: int) -> str:
    return Q5 if stage == 5 else context.signature_variables[(stage, 0, 0)]


def _eq113_token_exponents(context: LatticeContext, token: str) -> SparseIntegerRow:
    if token.startswith("Q_"):
        return {_q_variable(context, int(token.removeprefix("Q_"))): 1}
    kind, identifier = token.split(":", maxsplit=1)
    variable = context.b_signatures[identifier]
    if kind == "BDEF":
        return {variable: 1}
    if kind == "BINV":
        return {variable: -1}
    raise ValueError(f"unknown Eq. (113) token: {token}")


def _eq139_instances(domain: str) -> tuple[tuple[int, int, int], ...]:
    instances: list[tuple[int, int, int]] = []
    for stage in (2, 3, 4):
        if domain == EQ139_STRICT:
            indices = range(1, stage)
        elif domain == EQ139_COMPLETED:
            indices = range(1, stage + 1)
        else:
            raise ValueError(f"unknown Eq. (139) domain: {domain}")
        instances.extend((stage, left, right) for left, right in itertools.combinations(indices, 2))
    return tuple(instances)


def _operator_lattice_rows(
    context: LatticeContext,
) -> tuple[list[LabelledRow], dict[str, Any]]:
    rows: list[LabelledRow] = []
    cpobc_count = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            operator_ids = equation["operator_ids"]
            token_variables = {
                token: context.occurrence_variables[str(occurrence)]
                for token, occurrence in operator_ids.items()
            }
            left = _word_exponents(equation["lhs_word"], token_variables)
            right = _word_exponents(equation["rhs_word"], token_variables)
            rows.append(
                (
                    f"CPOBC:{relation['relation_id']}:{equation['equation_id']}",
                    _add_rows(left, _scale_row(-1, right)),
                )
            )
            cpobc_count += 1

    eq113_counts: dict[str, int] = {}
    for branch in (EQ113_DERIVED, EQ113_LITERAL):
        branch_rows = context.eq112["path_consistency_branches"][branch]
        eq113_counts[branch] = len(branch_rows)
        for relation in branch_rows:
            left = _add_rows(
                *(
                    _eq113_token_exponents(context, token)
                    for token in relation["lhs_word"]
                )
            )
            right = _add_rows(
                *(
                    _eq113_token_exponents(context, token)
                    for token in relation["rhs_word"]
                )
            )
            rows.append(
                (
                    f"Eq113:{branch}:{relation['causet_id']}",
                    _add_rows(left, _scale_row(-1, right)),
                )
            )

    strict_instances = _eq139_instances(EQ139_STRICT)
    completed_instances = _eq139_instances(EQ139_COMPLETED)
    for stage, left_index, right_index in completed_instances:
        # The two Eq. (139) words have the same scalar multiset.  Explicit zero
        # rows keep the completed ten-instance scope attached to this block.
        rows.append(
            (f"Eq139:{EQ139_COMPLETED}:{stage}:{left_index}:{right_index}", {})
        )

    counts: dict[str, Any] = {
        "CPOBC": cpobc_count,
        "Eq113": {
            "branches_kept_separate": True,
            "branch_counts": eq113_counts,
            "total": sum(eq113_counts.values()),
        },
        "Eq139": {
            "domains_kept_separate": True,
            "printed_strict": {
                "domain": EQ139_STRICT,
                "count": len(strict_instances),
                "instances": [list(instance) for instance in strict_instances],
                "included_as_additional_rows": False,
            },
            "eq145_completed": {
                "domain": EQ139_COMPLETED,
                "count": len(completed_instances),
                "instances": [list(instance) for instance in completed_instances],
                "included_as_scalar_zero_rows": True,
            },
            "strict_is_subset_of_completed": set(strict_instances).issubset(completed_instances),
        },
        "total": len(rows),
    }
    return rows, counts


def _fixed_gc_rows(context: LatticeContext) -> list[LabelledRow]:
    path_exponents: dict[str, SparseIntegerRow] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            row: defaultdict[str, int] = defaultdict(int)
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                variable = context.signature_variables[
                    (
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    )
                ]
                row[variable] += 1
            path_exponents[str(path["path_id"])] = _clean(dict(row))

    rows: list[LabelledRow] = []
    for relation in context.operator_gc["generating_relation_basis"]:
        left = path_exponents[str(relation["lhs_path_id"])]
        right = path_exponents[str(relation["rhs_path_id"])]
        rows.append(
            (
                f"fixed-GC:{relation['relation_id']}",
                _add_rows(left, _scale_row(-1, right)),
            )
        )
    return rows


def _rows_digest(rows: list[LabelledRow], variables: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for label, row in rows:
        record = [label, [row.get(variable, 0) for variable in variables]]
        digest.update(_canonical_json(record).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _integer_matrix(rows: list[LabelledRow], variables: tuple[str, ...]) -> sp.Matrix:
    positions = {variable: index for index, variable in enumerate(variables)}
    matrix = sp.zeros(len(rows), len(variables))
    for row_index, (_, row) in enumerate(rows):
        for variable, value in row.items():
            matrix[row_index, positions[variable]] = int(value)
    return matrix


def _row_echelon(
    rows: list[LabelledRow],
    variables: tuple[str, ...],
) -> dict[int, dict[int, Fraction]]:
    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    for _, source in rows:
        row = {
            positions[variable]: Fraction(value)
            for variable, value in source.items()
            if value
        }
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {
                    column: value / scale for column, value in row.items()
                }
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return basis


def _integer_kernel_columns(
    rows: list[LabelledRow],
    variables: tuple[str, ...],
) -> list[list[int]]:
    echelon = _row_echelon(rows, variables)
    free_columns = [column for column in range(len(variables)) if column not in echelon]
    result: list[list[int]] = []
    for free in free_columns:
        coordinates: dict[int, Fraction] = {free: Fraction(1)}
        for pivot in sorted(echelon, reverse=True):
            coordinates[pivot] = -sum(
                (
                    coefficient * coordinates.get(column, Fraction(0))
                    for column, coefficient in echelon[pivot].items()
                    if column != pivot
                ),
                Fraction(0),
            )
        dense = [coordinates.get(column, Fraction(0)) for column in range(len(variables))]
        if any(value.denominator != 1 for value in dense):
            raise AssertionError("the declared scalar lattice has a nonintegral kernel basis")
        result.append([value.numerator for value in dense])
    return result


def _smith_invariants(matrix: sp.Matrix) -> list[int]:
    diagonal = smith_normal_form(matrix, domain=ZZ)
    return [
        abs(int(diagonal[index, index]))
        for index in range(min(diagonal.rows, diagonal.cols))
        if diagonal[index, index] != 0
    ]


def _kernel_digest(columns: list[list[int]]) -> str:
    return hashlib.sha256(_canonical_json(columns).encode("utf-8")).hexdigest()


def _lattice_certificate(
    rows: list[LabelledRow],
    variables: tuple[str, ...],
    *,
    expected_rank: int,
    expected_kernel_rank: int,
) -> dict[str, Any]:
    matrix = _integer_matrix(rows, variables)
    invariants = _smith_invariants(matrix)
    if len(invariants) != expected_rank or any(value != 1 for value in invariants):
        raise AssertionError("the frozen relation lattice Smith invariants changed")

    kernel_columns = _integer_kernel_columns(rows, variables)
    if len(kernel_columns) != expected_kernel_rank:
        raise AssertionError("the frozen relation lattice kernel dimension changed")
    kernel = sp.Matrix.hstack(*(sp.Matrix(column) for column in kernel_columns))
    kernel_invariants = _smith_invariants(kernel)
    product_zero = matrix * kernel == sp.zeros(matrix.rows, kernel.cols)
    primitive = (
        product_zero
        and len(kernel_invariants) == expected_kernel_rank
        and all(value == 1 for value in kernel_invariants)
    )
    if not primitive:
        raise AssertionError("the displayed integer kernel is not a primitive full kernel")

    return {
        "matrix_shape": [matrix.rows, matrix.cols],
        "row_digest_sha256": _rows_digest(rows, variables),
        "QQ_rank": len(invariants),
        "QQ_nullity": len(variables) - len(invariants),
        "relation_lattice_smith": {
            "arithmetic": "ZZ",
            "nonzero_invariants": invariants,
            "all_nonzero_invariants_are_one": all(value == 1 for value in invariants),
            "saturated_row_lattice": all(value == 1 for value in invariants),
        },
        "integer_kernel": {
            "rank": len(kernel_columns),
            "basis_orientation": "columns_in_declared_variable_order",
            "basis_columns": kernel_columns,
            "basis_digest_sha256": _kernel_digest(kernel_columns),
            "relation_matrix_times_basis_is_zero": product_zero,
            "basis_smith_nonzero_invariants": kernel_invariants,
            "primitive_full_kernel": primitive,
        },
        "split_torus_dimension_before_nonmonomial_equations": len(kernel_columns),
    }


def build_payload(root: Path) -> dict[str, Any]:
    """Rebuild the two exact scalar lattices and their SNF certificates."""

    context = _build_context(root)
    operator_rows, relation_scope = _operator_lattice_rows(context)
    fixed_gc_rows = _fixed_gc_rows(context)
    bottom_rows = [*operator_rows, *fixed_gc_rows]

    if relation_scope["CPOBC"] != 783:
        raise AssertionError("the raw CPOBC scalar row count changed")
    if relation_scope["Eq113"]["branch_counts"] != {
        EQ113_DERIVED: 25,
        EQ113_LITERAL: 25,
    }:
        raise AssertionError("the separated Eq. (113) branch counts changed")
    if relation_scope["Eq139"]["printed_strict"]["count"] != 4:
        raise AssertionError("the printed-strict Eq. (139) scope changed")
    if relation_scope["Eq139"]["eq145_completed"]["count"] != 10:
        raise AssertionError("the Eq. (145)-completed Eq. (139) scope changed")
    if len(operator_rows) != 843 or len(fixed_gc_rows) != 320 or len(bottom_rows) != 1163:
        raise AssertionError("the declared scalar lattice matrix shapes changed")

    operator = _lattice_certificate(
        operator_rows,
        context.variables,
        expected_rank=83,
        expected_kernel_rank=49,
    )
    bottom = _lattice_certificate(
        bottom_rows,
        context.variables,
        expected_rank=103,
        expected_kernel_rank=29,
    )

    gates = {
        "operator_block_is_843_by_132_rank_83": (
            operator["matrix_shape"] == [843, 132] and operator["QQ_rank"] == 83
        ),
        "operator_smith_nonzero_invariants_are_all_one": operator[
            "relation_lattice_smith"
        ]["all_nonzero_invariants_are_one"],
        "operator_kernel_is_primitive_rank_49": (
            operator["integer_kernel"]["rank"] == 49
            and operator["integer_kernel"]["primitive_full_kernel"]
        ),
        "bottom_gc_block_is_1163_by_132_rank_103": (
            bottom["matrix_shape"] == [1163, 132] and bottom["QQ_rank"] == 103
        ),
        "bottom_gc_smith_nonzero_invariants_are_all_one": bottom[
            "relation_lattice_smith"
        ]["all_nonzero_invariants_are_one"],
        "bottom_gc_kernel_is_primitive_rank_29": (
            bottom["integer_kernel"]["rank"] == 29
            and bottom["integer_kernel"]["primitive_full_kernel"]
        ),
        "Eq113_branches_and_Eq139_domains_remain_separate": (
            relation_scope["Eq113"]["branches_kept_separate"]
            and relation_scope["Eq139"]["domains_kept_separate"]
            and relation_scope["Eq139"]["strict_is_subset_of_completed"]
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"SR2-V scalar lattice gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": {
            "relation_lattice": "ZZ",
            "rank_and_kernel_span": "QQ",
            "floating_point_used": False,
            "finite_field_used": False,
        },
        "finite_scope": "n<=4",
        "dimension": 2,
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: _sha256(root / relative)
            for relative in sorted(
                (CPOBC_PATH, REDUCTION_PATH, OPERATOR_GC_PATH, ATOMISATION_PATH, EQ112_PATH)
            )
        },
        "variable_namespace": {
            "count": len(context.variables),
            "ON_quotient_transition_orbits": 131,
            "cutoff_external_variables": [Q5],
            "ordered_variables": list(context.variables),
        },
        "relation_scope": {
            **relation_scope,
            "fixed_vector_GC_basis": {
                "count": len(fixed_gc_rows),
                "applied_only_to_observed_bottom_character": True,
            },
        },
        "operator_scalar_block": operator,
        "observed_bottom_plus_fixed_GC_block": bottom,
        "torus_interpretation": {
            "operator_scalar_laurent_locus": "split G_m^49",
            "observed_bottom_GC_laurent_locus": "split G_m^29",
            "reason": (
                "all nonzero relation-lattice Smith invariants and all displayed "
                "kernel-basis Smith invariants equal one"
            ),
            "not_included": [
                "24 additive source-matched reachable-state MSR equations",
                "upper-right affine-cocycle equations",
                "commutator nonzero or reachable-rank principal opens",
            ],
        },
        "gates": gates,
        "passed": True,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "This exact ZZ/QQ artifact certifies only the two declared scalar monomial "
            "relation lattices and primitive integer parameter kernels in the ON quotient. "
            "The Eq. (113) branches and Eq. (139) domains remain separate provenance "
            "inventories.  The ten completed Eq. (139) rows are scalar-zero multiset "
            "identities, not a derivation or merger of the two source readings.  No additive "
            "MSR locus, cocycle fibre, commutativity theorem, witness, chart cover, rational-"
            "point classification, or SR2-V terminal follows."
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
