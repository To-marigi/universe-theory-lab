"""Independent SymPy oracle for the v0.4 rational witness.

This test intentionally does not import ``weak_d2_v04``.  It reconstructs
the matrices from the frozen closed formula and evaluates the source
inventories with SymPy's exact ``Rational`` and ``Matrix`` arithmetic.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import sympy as sp

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _json(relative_path: str) -> dict[str, Any]:
    return json.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))


def _transition(stage: int, source_rows: list[int], precursor: int) -> sp.Matrix:
    width = precursor.bit_count()
    maximal_count = sum(
        1
        for vertex, upper_vertices in enumerate(source_rows)
        if precursor & (1 << vertex) and not upper_vertices & precursor
    )
    probability = sp.Rational(2 ** (width - maximal_count), 2**stage)
    upper_right = sp.Rational(4, 2**stage) if precursor == 0 else sp.Rational(0)
    return sp.Matrix([[probability, upper_right], [0, 1]])


def _q(stage: int) -> sp.Matrix:
    return _transition(stage, [0] * stage, 0)


def _word(factors: list[sp.Matrix]) -> sp.Matrix:
    product = sp.eye(2)
    for factor in factors:
        product *= factor
    return product


def _occurrence_assignments(
    reduction: dict[str, Any],
) -> dict[str, sp.Matrix]:
    return {
        record["occurrence_id"]: _transition(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        for record in reduction["reduction_map"]
    }


def test_independent_sympy_oracle_checks_cpobc_msr_and_inverses() -> None:
    cpobc = _json("results/v0.3.1_cpobc_relations_n4.json")
    reduction = _json("results/v0.3.2_cpobc_generator_reduction.json")
    assignments = _occurrence_assignments(reduction)

    cpobc_count = 0
    inverse_form_count = 0
    for relation in cpobc["relations"]:
        aliases: dict[str, str] = {}
        for equation in relation["raw_noncommutative_relation"]:
            aliases.update(equation["operator_ids"])
            lhs = _word([assignments[aliases[token]] for token in equation["lhs_word"]])
            rhs = _word([assignments[aliases[token]] for token in equation["rhs_word"]])
            assert lhs == rhs
            cpobc_count += 1

        for equation in relation["inverse_containing_form"]["forms"]:
            residual = sp.zeros(2)
            for term in equation["residual_terms"]:
                factors = []
                for token in term["word"]:
                    inverse = token.endswith("^-1")
                    factor = assignments[aliases[token.removesuffix("^-1")]]
                    factors.append(factor.inv() if inverse else factor)
                residual += int(term["coefficient"]) * _word(factors)
            assert residual == sp.zeros(2)
            inverse_form_count += 1

    assert cpobc_count == 783
    assert inverse_form_count == 712

    for matrix in assignments.values():
        assert matrix.det() != 0
        assert matrix.inv() * matrix == sp.eye(2)
        assert matrix * matrix.inv() == sp.eye(2)

    omega = sp.Matrix([1, 0])
    strong_failures = 0
    for constraint in cpobc["MSR_operator_constraints"]:
        residual = int(constraint["identity_coefficient"]) * sp.eye(2)
        for term in constraint["terms"]:
            residual += int(term["coefficient"]) * assignments[term["transition_id"]]
        assert residual * omega == sp.zeros(2, 1)
        strong_failures += residual != sp.zeros(2)
    assert strong_failures == 24


def test_independent_sympy_oracle_checks_all_fixed_vector_gc_pairs() -> None:
    operator_gc = _json("results/v0.3.3_local_operator_gc_n4.json")
    path_matrices: dict[str, sp.Matrix] = {}
    for stage_paths in operator_gc["path_inventory"].values():
        for path in stage_paths:
            product = sp.eye(2)
            for transition in path["transitions"]:
                product = (
                    _transition(
                        int(transition["stage"]),
                        transition["source_relation_rows"],
                        int(transition["precursor_code"]),
                    )
                    * product
                )
            path_matrices[path["path_id"]] = product

    omega = sp.Matrix([1, 0])
    strong_failures = 0
    for relation in operator_gc["all_pair_derivations"]:
        residual = (
            path_matrices[relation["left_path_id"]] - path_matrices[relation["right_path_id"]]
        )
        assert residual * omega == sp.zeros(2, 1)
        strong_failures += residual != sp.zeros(2)
    assert len(operator_gc["all_pair_derivations"]) == 1529
    assert strong_failures == 986


def _b_assignments(atomisation: dict[str, Any]) -> dict[str, sp.Matrix]:
    result: dict[str, sp.Matrix] = {}
    for causet in atomisation["causets"]:
        for path in causet["all_alternative_paths"]:
            for factor in path["B_operator_factors"]:
                identifier = factor["B_occurrence_id"].removeprefix("B-occurrence-")
                matrix = _transition(
                    int(factor["paper_stage_index"]),
                    factor["source_relation_rows"],
                    int(factor["precursor_code"]),
                )
                assert result.setdefault(identifier, matrix) == matrix
    return result


def test_independent_sympy_oracle_keeps_both_eq113_branches() -> None:
    atomisation = _json("results/v0.3.3_atomisation_paths_n4.json")
    eq112 = _json("results/v0.3.3_eq112_reduction_n4.json")
    b_assignments = _b_assignments(atomisation)

    def token_matrix(token: str) -> sp.Matrix:
        if token.startswith("Q_"):
            return _q(int(token.removeprefix("Q_")))
        kind, identifier = token.split(":", maxsplit=1)
        matrix = b_assignments[identifier]
        return matrix if kind == "BDEF" else matrix.inv()

    for branch in ("EQ113_QN_BRANCH", "EQ113_QN_PLUS_1_BRANCH"):
        relations = eq112["path_consistency_branches"][branch]
        assert len(relations) == 25
        for relation in relations:
            lhs = _word([token_matrix(token) for token in relation["lhs_word"]])
            rhs = _word([token_matrix(token) for token in relation["rhs_word"]])
            assert lhs == rhs


def test_independent_sympy_oracle_checks_eq139_and_noncommutativity() -> None:
    strict_instances = [
        (stage, left, right)
        for stage in (2, 3, 4)
        for left, right in itertools.combinations(range(1, stage), 2)
    ]
    completed_instances = [
        (stage, left, right)
        for stage in (2, 3, 4)
        for left, right in itertools.combinations(range(1, stage + 1), 2)
    ]
    assert len(strict_instances) == 4
    assert len(completed_instances) == 10

    for stage, left_index, right_index in completed_instances:
        left_transition = _transition(stage, [0] * stage, (1 << left_index) - 1)
        right_transition = _transition(stage, [0] * stage, (1 << right_index) - 1)
        lhs = _word(
            [
                left_transition,
                right_transition,
                _q(stage + 1),
                right_transition.inv(),
                _q(stage).inv(),
                right_transition,
            ]
        )
        rhs = _word(
            [
                right_transition,
                left_transition,
                _q(stage + 1),
                left_transition.inv(),
                _q(stage).inv(),
                left_transition,
            ]
        )
        assert lhs == rhs

    for left_stage, right_stage in itertools.combinations(range(1, 5), 2):
        commutator = _q(left_stage) * _q(right_stage) - _q(right_stage) * _q(left_stage)
        expected = sp.Matrix(
            [
                [0, 4 * (sp.Rational(1, 2**left_stage) - sp.Rational(1, 2**right_stage))],
                [0, 0],
            ]
        )
        assert commutator == expected
        assert commutator != sp.zeros(2)
