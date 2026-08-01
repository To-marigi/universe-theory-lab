"""Exact, bounded triangular scout for the two v0.4.1 one-sided cores.

This module is deliberately independent of :mod:`weak_d2_v04`: it rereads the
frozen source inventories and performs sparse Gaussian elimination over
``fractions.Fraction``.  It tests only the occurrence-identified,
upper-triangular two-character family

    [[p_e, x_e], [0, q_e]],  p_e = CSG(t_j=1), q_e = CSG(t_j=2**j).

For each one-sided *sufficient no-go core*, all six ``Q_1``--``Q_4``
commutators vanish on the exact QQ-linear solution space.  This is a scout
result, not a statement about arbitrary ``GL_2(QQ)`` solutions, the complete
one-sided profiles, or naturally labelled occurrence semantics.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

RESULT_PATH = "results/v0.4.1_one_sided_scout.json"
VERDICT = "ONE_SIDED_TRIANGULAR_SCOUT_NO_NONCOMMUTATIVE_SURVIVOR"
CLASSIFICATION = "EXACT_QQ_LINEAR_SUFFICIENT_CORE_SCOUT_NOT_GENERAL_D2_PROOF"

_CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
_REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relation_code(relation: tuple[int, ...]) -> int:
    return sum(row << (index * len(relation)) for index, row in enumerate(relation))


def _csg_diagonal(
    stage: int,
    source_relation_rows: Iterable[int],
    precursor_code: int,
    *,
    coupling_ratio: int | None,
) -> Fraction:
    """Exact diagonal CSG character; ``None`` denotes ``t_j=1``."""

    relation = tuple(int(row) for row in source_relation_rows)
    width = precursor_code.bit_count()
    maximal_count = sum(
        1
        for vertex, upper_vertices in enumerate(relation)
        if precursor_code & (1 << vertex) and not upper_vertices & precursor_code
    )
    if coupling_ratio is None:
        return Fraction(2 ** (width - maximal_count), 2**stage)
    return Fraction(
        coupling_ratio**maximal_count * (1 + coupling_ratio) ** (width - maximal_count),
        (1 + coupling_ratio) ** stage,
    )


@dataclass(frozen=True)
class _LinearTriangular:
    upper_left: Fraction
    lower_right: Fraction
    upper_right: dict[str, Fraction]


def _matrix(
    upper_left: Fraction,
    lower_right: Fraction,
    variable: str | None = None,
) -> _LinearTriangular:
    return _LinearTriangular(
        upper_left,
        lower_right,
        {} if variable is None else {variable: Fraction(1)},
    )


def _multiply(left: _LinearTriangular, right: _LinearTriangular) -> _LinearTriangular:
    coefficients: defaultdict[str, Fraction] = defaultdict(Fraction)
    for variable, coefficient in right.upper_right.items():
        coefficients[variable] += left.upper_left * coefficient
    for variable, coefficient in left.upper_right.items():
        coefficients[variable] += right.lower_right * coefficient
    return _LinearTriangular(
        left.upper_left * right.upper_left,
        left.lower_right * right.lower_right,
        {variable: coefficient for variable, coefficient in coefficients.items() if coefficient},
    )


def _word(factors: Iterable[_LinearTriangular]) -> _LinearTriangular:
    product = _matrix(Fraction(1), Fraction(1))
    for factor in factors:
        product = _multiply(product, factor)
    return product


def _residual(left: _LinearTriangular, right: _LinearTriangular) -> dict[str, Fraction]:
    if left.upper_left != right.upper_left or left.lower_right != right.lower_right:
        raise AssertionError("the chosen diagonal CSG characters violate a source identity")
    variables = set(left.upper_right) | set(right.upper_right)
    return {
        variable: left.upper_right.get(variable, Fraction(0))
        - right.upper_right.get(variable, Fraction(0))
        for variable in variables
        if left.upper_right.get(variable, Fraction(0))
        != right.upper_right.get(variable, Fraction(0))
    }


def _row_echelon(
    rows: Iterable[dict[str, Fraction]], variables: list[str]
) -> dict[int, dict[int, Fraction]]:
    positions = {variable: index for index, variable in enumerate(variables)}
    basis: dict[int, dict[int, Fraction]] = {}
    for source in rows:
        row = {positions[key]: Fraction(value) for key, value in source.items() if value}
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                break
            scale = row[pivot]
            for column, coefficient in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * coefficient
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return basis


def _rank(rows: Iterable[dict[str, Fraction]], variables: list[str]) -> int:
    return len(_row_echelon(rows, variables))


def _profile_record(
    base_rows: list[dict[str, Fraction]],
    extra_rows: list[dict[str, Fraction]],
    commutators: dict[str, dict[str, Fraction]],
    variables: list[str],
) -> dict[str, Any]:
    rows = base_rows + extra_rows
    rank = _rank(rows, variables)
    joint_rank = _rank(rows + list(commutators.values()), variables)
    commutator_records = {
        pair: {
            "augmented_rank": _rank(rows + [functional], variables),
            "forced_zero_within_declared_ansatz": _rank(rows + [functional], variables)
            == rank,
        }
        for pair, functional in commutators.items()
    }
    return {
        "rank": rank,
        "nullity": len(variables) - rank,
        "joint_commutator_augmented_rank": joint_rank,
        "independent_commutator_conditions_remaining": joint_rank - rank,
        "all_Q1_through_Q4_commutators_forced_zero_within_declared_ansatz": all(
            record["forced_zero_within_declared_ansatz"]
            for record in commutator_records.values()
        ),
        "commutators": commutator_records,
    }


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def semantic_digest(payload: dict[str, Any]) -> str:
    return _stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def compile_one_sided_d2_v041_scout(root: Path) -> dict[str, Any]:
    """Compile the two exact one-sided QQ-linear scouts without a solver call."""

    root = root.resolve()
    cpobc_path = root / _CPOBC_PATH
    reduction_path = root / _REDUCTION_PATH
    gc_path = root / _GC_PATH
    cpobc = _load_json(cpobc_path)
    reduction = _load_json(reduction_path)
    operator_gc = _load_json(gc_path)

    records = {record["occurrence_id"]: record for record in reduction["reduction_map"]}
    signatures: dict[tuple[int, int, int], str] = {}
    for record in records.values():
        signature = (
            int(record["stage"]),
            _relation_code(tuple(int(row) for row in record["source_relation_rows"])),
            int(record["precursor_code"]),
        )
        previous = signatures.setdefault(signature, str(record["orbit_id"]))
        if previous != record["orbit_id"]:
            raise AssertionError("one transition signature maps to multiple quotient orbits")

    variables = sorted(set(signatures.values())) + ["Q_5_EXTERNAL"]

    def transition(record: dict[str, Any]) -> _LinearTriangular:
        return _matrix(
            _csg_diagonal(
                int(record["stage"]),
                record["source_relation_rows"],
                int(record["precursor_code"]),
                coupling_ratio=None,
            ),
            _csg_diagonal(
                int(record["stage"]),
                record["source_relation_rows"],
                int(record["precursor_code"]),
                coupling_ratio=2,
            ),
            str(record["orbit_id"]),
        )

    def signature_transition(signature: dict[str, Any]) -> _LinearTriangular:
        stage = int(signature["stage"])
        source_code = int(signature["source_relation_code"])
        precursor_code = int(signature["precursor_code"])
        mask = (1 << stage) - 1
        relation = tuple((source_code >> (stage * row)) & mask for row in range(stage))
        return _matrix(
            _csg_diagonal(stage, relation, precursor_code, coupling_ratio=None),
            _csg_diagonal(stage, relation, precursor_code, coupling_ratio=2),
            signatures[(stage, source_code, precursor_code)],
        )

    occurrence_matrices = {identifier: transition(record) for identifier, record in records.items()}
    cpobc_rows: list[dict[str, Fraction]] = []
    for relation in cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            identifiers = equation["operator_ids"]
            cpobc_rows.append(
                _residual(
                    _word(
                        occurrence_matrices[identifiers[token]] for token in equation["lhs_word"]
                    ),
                    _word(
                        occurrence_matrices[identifiers[token]] for token in equation["rhs_word"]
                    ),
                )
            )

    msr_rows: list[dict[str, Fraction]] = []
    for constraint in cpobc["MSR_operator_constraints"]:
        upper_left = Fraction(int(constraint["identity_coefficient"]))
        lower_right = Fraction(int(constraint["identity_coefficient"]))
        coefficients: defaultdict[str, Fraction] = defaultdict(Fraction)
        for term in constraint["terms"]:
            coefficient = Fraction(int(term["coefficient"]))
            matrix = occurrence_matrices[term["transition_id"]]
            upper_left += coefficient * matrix.upper_left
            lower_right += coefficient * matrix.lower_right
            for variable, value in matrix.upper_right.items():
                coefficients[variable] += coefficient * value
        if upper_left or lower_right:
            raise AssertionError("strong MSR diagonal residual is unexpectedly nonzero")
        msr_rows.append({variable: value for variable, value in coefficients.items() if value})

    path_matrices: dict[str, _LinearTriangular] = {}
    for paths in operator_gc["path_inventory"].values():
        for path in paths:
            product = _matrix(Fraction(1), Fraction(1))
            for transition_record in path["transitions"]:
                product = _multiply(
                    signature_transition(transition_record["quotient_signature"]), product
                )
            path_matrices[path["path_id"]] = product
    gc_rows = [
        _residual(path_matrices[relation["lhs_path_id"]], path_matrices[relation["rhs_path_id"]])
        for relation in operator_gc["generating_relation_basis"]
    ]

    def q(stage: int) -> _LinearTriangular:
        variable = "Q_5_EXTERNAL" if stage == 5 else signatures[(stage, 0, 0)]
        return _matrix(Fraction(1, 2**stage), Fraction(1, 3**stage), variable)

    commutators = {
        f"Q{left}_Q{right}": _residual(_multiply(q(left), q(right)), _multiply(q(right), q(left)))
        for left in range(1, 5)
        for right in range(left + 1, 5)
    }
    if len(cpobc_rows) != 783 or len(msr_rows) != 24 or len(gc_rows) != 320:
        raise AssertionError("frozen source relation counts changed")
    if len(variables) != 132 or len(commutators) != 6:
        raise AssertionError("declared triangular scout coordinate system changed")

    profiles = {
        "fixed_vector_GC__strong_MSR": {
            "core_relations": "CPOBC + strong operator MSR",
            "source_raw_linear_equation_count": 783 + 24,
            "weak_side_not_imposed": "fixed-vector GC is omitted only for a sufficient no-go core",
            **_profile_record(cpobc_rows, msr_rows, commutators, variables),
        },
        "strong_GC__reachable_state_MSR": {
            "core_relations": "CPOBC + strong operator GC basis",
            "source_raw_linear_equation_count": 783 + 320,
            "weak_side_not_imposed": (
                "reachable-state MSR is omitted only for a sufficient no-go core"
            ),
            **_profile_record(cpobc_rows, gc_rows, commutators, variables),
        },
    }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "version": "v0.4.1",
        "verdict": VERDICT,
        "classification": CLASSIFICATION,
        "identification_mode": "ON_QUOTIENT",
        "source_artifacts": {
            _CPOBC_PATH: _sha256(cpobc_path),
            _REDUCTION_PATH: _sha256(reduction_path),
            _GC_PATH: _sha256(gc_path),
        },
        "ansatz": {
            "coefficient_field": "QQ (Fraction exact arithmetic)",
            "matrix_form": "[[p_e,x_orbit(e)],[0,q_e]]",
            "first_diagonal_character": "CSG t_j=1",
            "second_diagonal_character": "CSG t_j=2^j",
            "upper_right_variables": (
                "identified by transition orbit plus unconstrained Q_5_EXTERNAL"
            ),
            "variable_count": len(variables),
            "occurrence_identification": "ON_QUOTIENT",
        },
        "source_relation_counts": {
            "CPOBC_raw_word_equations": len(cpobc_rows),
            "strong_MSR_source_constraints": len(msr_rows),
            "strong_GC_generating_basis_relations": len(gc_rows),
        },
        "profiles": profiles,
        "no_numeric_or_finite_field_evidence_used": True,
        "solver_invoked": False,
        "claim_boundary": (
            "Each result is exact only in the declared ON-quotient triangular two-character "
            "family and its sufficient no-go core. It is not a general GL_2(QQ) proof, not a "
            "complete one-sided-profile theorem, and says nothing about OFF naturally labelled "
            "occurrence semantics."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def write_one_sided_d2_v041_scout(root: Path, payload: dict[str, Any]) -> Path:
    """Write the canonical scout artifact using LF line endings."""

    path = root.resolve() / RESULT_PATH
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
