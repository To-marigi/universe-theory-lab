from __future__ import annotations

import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.weak_d2_v04 import (
    IDENTITY,
    OMEGA,
    ZERO,
    _csg_diagonal,
    _evaluate_cpobc,
    _evaluate_cpobc_inverse_forms,
    _evaluate_msr,
    _matrix_multiply,
    _matrix_subtract,
)

ROOT = Path(__file__).resolve().parents[2]
TARGET_IDENTITIES = {"msr:p1-0", "msr:p2-0", "msr:p2-2"}


def _load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _diagonal_transition(
    stage: int,
    source_relation_rows: list[int],
    precursor_code: int,
) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    probability = _csg_diagonal(
        stage,
        source_relation_rows,
        precursor_code,
        coupling_ratio=None,
    )
    return (
        (probability, Fraction(0)),
        (Fraction(0), Fraction(1)),
    )


def _source_residual_after_reconstruction(
    constraint: dict[str, Any],
    reduction_by_occurrence: dict[str, dict[str, Any]],
) -> dict[tuple[str, ...], int]:
    residual: defaultdict[tuple[str, ...], int] = defaultdict(int)
    residual[()] = int(constraint["identity_coefficient"])
    for term in constraint["terms"]:
        occurrence = reduction_by_occurrence[term["transition_id"]]
        for summand in occurrence["reduced_expression"]:
            residual[tuple(summand["word"])] += int(term["coefficient"]) * int(
                summand["coefficient"]
            )
    return {word: coefficient for word, coefficient in residual.items() if coefficient}


def test_q_reconstruction_is_bound_to_the_strong_operator_profile() -> None:
    dependency = _load("results/v0.3.1_cpobc_dependency_graph.json")
    reduction = _load("results/v0.3.2_cpobc_generator_reduction.json")
    eq112 = _load("results/v0.3.3_eq112_reduction_n4.json")
    presentation = _load("results/v0.3.3_q_only_presentation_n4.json")
    direct = _load("certificates/d2_saturation/v0.3.5_direct_operator_system.json")

    assert {
        "from": "paper:eq108",
        "to": "axiom:MSR",
        "type": "MSR_ELIMINATION",
    } in dependency["edges"]
    assert Counter(record["transition_kind"] for record in reduction["reduction_map"]) == {
        "GREGARIOUS": 24,
        "NON_TIMID": 117,
        "TIMID": 24,
    }
    assert all(
        "Eq.(108)" in record["derivation"]
        for record in reduction["reduction_map"]
        if record["transition_kind"] != "GREGARIOUS"
    )
    assert eq112["equivalence_obligations"]["forward"]["status"] == (
        "PROVED_WITHIN_PAPER_STRONG_OPERATOR_PROFILE_N4"
    )
    assert "paper Eqs. (107), (108), (111), and (112)" in (
        eq112["equivalence_obligations"]["forward"]["dependencies"]
    )
    assert presentation["semantic_profile"] == "PAPER_STRONG_OPERATOR_PROFILE"
    assert presentation["separate_reachable_state_namespace"] == {
        "profile": "REACHABLE_STATE_PROFILE",
        "operator_GC_relations_in_ideal": 0,
        "strong_MSR_relations_in_ideal": 0,
        "not_mixed_with_presentation": True,
    }
    assert direct["semantic_profile"] == "PAPER_STRONG_OPERATOR_PROFILE"
    assert direct["source_artifact"] == "results/v0.3.3_q_only_presentation_n4.json"
    assert len(direct["reconstructed_transition_predicates"]) == 165


def test_three_early_strong_msr_constraints_are_hardcoded_as_identities() -> None:
    source = _load("results/v0.3.1_cpobc_relations_n4.json")
    reduction = _load("results/v0.3.2_cpobc_generator_reduction.json")
    presentation = _load("results/v0.3.3_q_only_presentation_n4.json")
    direct = _load("certificates/d2_saturation/v0.3.5_direct_operator_system.json")

    reduction_by_occurrence = {
        record["occurrence_id"]: record for record in reduction["reduction_map"]
    }
    source_constraints = {
        record["constraint_id"]: record
        for record in source["MSR_operator_constraints"]
        if record["constraint_id"] in TARGET_IDENTITIES
    }
    assert set(source_constraints) == TARGET_IDENTITIES
    assert all(
        _source_residual_after_reconstruction(record, reduction_by_occurrence) == {}
        for record in source_constraints.values()
    )
    assert {
        record["constraint_id"]
        for record in presentation["relation_inventory"]["strong_MSR_identities"]
    } == TARGET_IDENTITIES
    direct_ids = {
        record["relation_id"]
        for records in direct["relations"].values()
        for record in records
    }
    assert TARGET_IDENTITIES.isdisjoint(direct_ids)


def test_exact_source_profile_point_lies_outside_the_q_reconstruction_image() -> None:
    """A full strong-GC/reachable-MSR point violates hardcoded strong MSR."""

    source = _load("results/v0.3.1_cpobc_relations_n4.json")
    reduction = _load("results/v0.3.2_cpobc_generator_reduction.json")
    operator_gc = _load("results/v0.3.3_local_operator_gc_n4.json")

    assignments = {
        record["occurrence_id"]: _diagonal_transition(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        for record in reduction["reduction_map"]
    }
    by_orbit: defaultdict[str, set[Any]] = defaultdict(set)
    for record in reduction["reduction_map"]:
        by_orbit[record["orbit_id"]].add(assignments[record["occurrence_id"]])
    assert len(by_orbit) == 131
    assert all(len(values) == 1 for values in by_orbit.values())
    assert all(matrix[0][0] * matrix[1][1] != 0 for matrix in assignments.values())

    cpobc = _evaluate_cpobc(source, assignments)
    inverse_cpobc = _evaluate_cpobc_inverse_forms(source, assignments)
    msr = _evaluate_msr(source, assignments)
    assert cpobc["checked_equations"] == 783 and cpobc["all_zero"]
    assert inverse_cpobc["checked_inverse_containing_equations"] == 712
    assert inverse_cpobc["all_zero"]
    assert msr["all_reachable_state_equalities_hold"]
    assert not msr["all_strong_operator_equalities_hold"]
    assert msr["strong_operator_failure_count"] == 24
    assert next(
        record for record in msr["records"] if record["constraint_id"] == "msr:p1-0"
    )["operator_residual"] == [["0", "0"], ["0", "1"]]

    path_matrices: dict[str, Any] = {}
    for paths in operator_gc["path_inventory"].values():
        for path in paths:
            product = IDENTITY
            for transition in path["transitions"]:
                product = _matrix_multiply(
                    _diagonal_transition(
                        int(transition["stage"]),
                        transition["source_relation_rows"],
                        int(transition["precursor_code"]),
                    ),
                    product,
                )
            path_matrices[path["path_id"]] = product
    assert len(operator_gc["all_pair_derivations"]) == 1529
    assert all(
        _matrix_subtract(
            path_matrices[relation["left_path_id"]],
            path_matrices[relation["right_path_id"]],
        )
        == ZERO
        for relation in operator_gc["all_pair_derivations"]
    )

    # Every reachable source state is a nonzero scalar multiple of Omega, so
    # the stored residual-on-Omega checks are exactly the source-state checks.
    assert OMEGA == (Fraction(1), Fraction(0))


def test_v041_955_campaign_drops_msr_relations_but_keeps_strong_profile_coordinates() -> None:
    manifest = _load("results/v0.4.1_one_sided_elimination_manifest.json")
    requests = [
        request
        for request in manifest["requests"]
        if request["profile"] == "strong_GC__reachable_state_MSR"
    ]
    assert len(requests) == 21
    assert all(request["expected_selected_relation_count"] == 955 for request in requests)
    assert all(
        request["included_relation_families"] == ["CPOBC", "LOCAL_OPERATOR_GC"]
        for request in requests
    )
    assert all(
        "STRONG_OPERATOR_MSR" in request["forbidden_relation_families"]
        for request in requests
    )
    assert all(request["include_all_transition_predicates"] for request in requests)
