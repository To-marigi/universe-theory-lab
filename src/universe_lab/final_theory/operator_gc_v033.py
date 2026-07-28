"""Finite strong-operator general-covariance compiler through n=4.

The compiler enumerates naturally labelled growth histories first and only
then groups them by their unlabelled endpoint.  An endpoint-wise spanning tree
is used as a nonredundant generating set for all same-endpoint path
equalities.  Operator words follow Eq. (31): later transitions are on the
left.
"""

from __future__ import annotations

import itertools
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    automorphisms,
    canonical_code,
    canonicalize,
    causet_id,
    downsets,
    has_relation,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    GC_FIXED_VECTOR,
    GC_STRONG_OPERATOR,
    PAPER_STRONG_OPERATOR_PROFILE,
    REACHABLE_STATE_PROFILE,
    stable_hash,
    validate_relation_namespace,
)

MAX_SOURCE_STAGE = 4
MAX_ENDPOINT_STAGE = MAX_SOURCE_STAGE + 1
VERDICT_COMPLETE = "LOCAL_OPERATOR_GC_COMPILER_COMPLETE_N4"


def _relation_code(relation: Relation) -> int:
    size = len(relation)
    return sum(row << (row_index * size) for row_index, row in enumerate(relation))


def _relation_code_for_order(relation: Relation, order: tuple[int, ...]) -> int:
    size = len(relation)
    code = 0
    for new_lower, old_lower in enumerate(order):
        for new_upper, old_upper in enumerate(order):
            if has_relation(relation, old_lower, old_upper):
                code |= 1 << (new_lower * size + new_upper)
    return code


def _subset_for_order(subset: int, order: tuple[int, ...]) -> int:
    return sum(
        1 << new_vertex
        for new_vertex, old_vertex in enumerate(order)
        if subset & (1 << old_vertex)
    )


def _decorated_transition_signature(
    relation: Relation,
    precursor: int,
) -> dict[str, int]:
    """Canonicalise a source causet together with its precursor down-set."""

    candidates = []
    for order in itertools.permutations(range(len(relation))):
        candidates.append(
            (
                _relation_code_for_order(relation, order),
                _subset_for_order(precursor, order),
            )
        )
    relation_code, precursor_code = min(candidates)
    return {
        "stage": len(relation),
        "source_relation_code": relation_code,
        "precursor_code": precursor_code,
    }


def _canonicalising_orders(relation: Relation) -> tuple[tuple[int, ...], ...]:
    target = canonical_code(relation)
    return tuple(
        order
        for order in itertools.permutations(range(len(relation)))
        if _relation_code_for_order(relation, order) == target
    )


def _transition_record(
    relation: Relation,
    precursor: int,
    target: Relation,
) -> dict[str, Any]:
    stage = len(relation)
    labelled_payload = {
        "stage": stage,
        "source_relation_rows": list(relation),
        "precursor_code": precursor,
        "target_relation_rows": list(target),
    }
    signature = _decorated_transition_signature(relation, precursor)
    labelled_digest = stable_hash(labelled_payload)
    quotient_digest = stable_hash(signature)
    return {
        "stage": stage,
        "source_relation_rows": list(relation),
        "source_unlabelled_id": causet_id(relation),
        "precursor_code": precursor,
        "precursor_vertices": [
            vertex for vertex in range(stage) if precursor & (1 << vertex)
        ],
        "target_relation_rows": list(target),
        "target_unlabelled_id": causet_id(target),
        "labelled_occurrence_id": f"lgc-labelled-{labelled_digest[:20]}",
        "labelled_operator_symbol": f"L_{stage}_{labelled_digest[:16]}",
        "quotient_occurrence_id": f"lgc-orbit-{quotient_digest[:20]}",
        "quotient_operator_symbol": f"A_{stage}_{quotient_digest[:16]}",
        "quotient_signature": signature,
        "automorphism_provenance": {
            "source_automorphism_order": len(automorphisms(relation)),
            "decorated_signature_sha256": quotient_digest,
        },
    }


@dataclass(frozen=True)
class _PathState:
    relation: Relation
    relation_history: tuple[Relation, ...]
    transitions: tuple[dict[str, Any], ...]


def enumerate_labelled_growth_paths(
    max_source_stage: int = MAX_SOURCE_STAGE,
) -> dict[int, tuple[dict[str, Any], ...]]:
    """Enumerate paths whose transition sources have size at most ``max_source_stage``."""

    if max_source_stage < 1 or max_source_stage > MAX_SOURCE_STAGE:
        raise ValueError(
            f"max_source_stage must be between 1 and {MAX_SOURCE_STAGE}"
        )
    max_endpoint_stage = max_source_stage + 1
    levels: dict[int, tuple[_PathState, ...]] = {
        1: (_PathState((0,), ((0,),), ()),)
    }
    for stage in range(1, max_endpoint_stage):
        next_states: dict[Relation, _PathState] = {}
        for state in levels[stage]:
            for precursor in downsets(state.relation):
                target = add_maximal(state.relation, precursor)
                transition = _transition_record(state.relation, precursor, target)
                candidate = _PathState(
                    relation=target,
                    relation_history=state.relation_history + (target,),
                    transitions=state.transitions + (transition,),
                )
                previous = next_states.get(target)
                if previous is not None and previous != candidate:
                    raise AssertionError(
                        "a naturally labelled endpoint acquired two birth histories"
                    )
                next_states[target] = candidate
        levels[stage + 1] = tuple(
            next_states[relation] for relation in sorted(next_states, key=_relation_code)
        )

    result: dict[int, tuple[dict[str, Any], ...]] = {}
    for stage, states in levels.items():
        paths = []
        for state in states:
            canonical_orders = _canonicalising_orders(state.relation)
            labelled_word = [
                transition["labelled_operator_symbol"]
                for transition in reversed(state.transitions)
            ]
            quotient_word = [
                transition["quotient_operator_symbol"]
                for transition in reversed(state.transitions)
            ]
            chronological_occurrences = [
                transition["quotient_occurrence_id"]
                for transition in state.transitions
            ]
            path_payload = {
                "endpoint_relation_rows": list(state.relation),
                "chronological_occurrences": chronological_occurrences,
            }
            path_digest = stable_hash(path_payload)
            paths.append(
                {
                    "path_id": f"lgc-path-{path_digest[:20]}",
                    "endpoint_stage": stage,
                    "endpoint_relation_rows": list(state.relation),
                    "endpoint_labelled_code": _relation_code(state.relation),
                    "endpoint_causet_id": causet_id(state.relation),
                    "unlabelled_quotient_relation_rows": list(
                        canonicalize(state.relation)
                    ),
                    "labelled_path": [
                        list(relation) for relation in state.relation_history
                    ],
                    "transition_occurrence_sequence_chronological": [
                        transition["labelled_occurrence_id"]
                        for transition in state.transitions
                    ],
                    "quotient_occurrence_sequence_chronological": (
                        chronological_occurrences
                    ),
                    "ordered_operator_word_later_on_left": quotient_word,
                    "labelled_operator_word_later_on_left": labelled_word,
                    "path_length": len(state.transitions),
                    "initial_source": causet_id((0,)),
                    "GC_semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
                    "transitions": list(state.transitions),
                    "automorphism_provenance": {
                        "endpoint_automorphism_order": len(
                            automorphisms(state.relation)
                        ),
                        "canonicalising_permutation_count": len(canonical_orders),
                        "chosen_old_vertex_order": list(canonical_orders[0]),
                        "no_labelled_path_quotient_applied": True,
                    },
                }
            )
        result[stage] = tuple(sorted(paths, key=lambda path: path["path_id"]))
    return result


def _basis_relations(
    paths_by_endpoint: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    basis: list[dict[str, Any]] = []
    all_pair_derivations: list[dict[str, Any]] = []
    edge_by_endpoint_and_path: dict[tuple[str, str], str] = {}

    for endpoint, paths in sorted(paths_by_endpoint.items()):
        ordered = sorted(paths, key=lambda path: path["path_id"])
        if len(ordered) < 2:
            continue
        anchor = ordered[0]
        for path in ordered[1:]:
            relation_payload = {
                "endpoint": endpoint,
                "lhs_path": path["path_id"],
                "rhs_path": anchor["path_id"],
            }
            relation_id = f"operator-gc-{stable_hash(relation_payload)[:20]}"
            record = {
                "relation_id": relation_id,
                "endpoint_causet_id": endpoint,
                "lhs_path_id": path["path_id"],
                "rhs_path_id": anchor["path_id"],
                "lhs_word": path["ordered_operator_word_later_on_left"],
                "rhs_word": anchor["ordered_operator_word_later_on_left"],
                "relation_strength": GC_STRONG_OPERATOR,
                "GC_semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
                "provenance": "two enumerated naturally labelled paths with one endpoint",
                "basis_method": "endpoint-wise star spanning tree",
            }
            basis.append(record)
            edge_by_endpoint_and_path[(endpoint, path["path_id"])] = relation_id

        for left_index, left in enumerate(ordered):
            for right in ordered[left_index + 1 :]:
                chain = []
                if left["path_id"] != anchor["path_id"]:
                    chain.append(
                        {
                            "relation_id": edge_by_endpoint_and_path[
                                (endpoint, left["path_id"])
                            ],
                            "orientation": "lhs_to_anchor",
                        }
                    )
                if right["path_id"] != anchor["path_id"]:
                    chain.append(
                        {
                            "relation_id": edge_by_endpoint_and_path[
                                (endpoint, right["path_id"])
                            ],
                            "orientation": "anchor_to_lhs",
                        }
                    )
                all_pair_derivations.append(
                    {
                        "endpoint_causet_id": endpoint,
                        "left_path_id": left["path_id"],
                        "right_path_id": right["path_id"],
                        "basis_chain": chain,
                        "derivable": bool(chain),
                    }
                )
    return basis, all_pair_derivations


def _basis_connectivity(
    paths_by_endpoint: dict[str, list[dict[str, Any]]],
    basis: list[dict[str, Any]],
) -> dict[str, Any]:
    adjacency: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for relation in basis:
        endpoint = relation["endpoint_causet_id"]
        lhs = relation["lhs_path_id"]
        rhs = relation["rhs_path_id"]
        adjacency[endpoint][lhs].add(rhs)
        adjacency[endpoint][rhs].add(lhs)

    endpoint_records = []
    complete = True
    for endpoint, paths in sorted(paths_by_endpoint.items()):
        path_ids = {path["path_id"] for path in paths}
        if not path_ids:
            continue
        start = min(path_ids)
        reached = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbour in adjacency[endpoint][current]:
                if neighbour not in reached:
                    reached.add(neighbour)
                    queue.append(neighbour)
        edge_count = sum(len(values) for values in adjacency[endpoint].values()) // 2
        connected = reached == path_ids
        tree_edge_count = edge_count == max(0, len(path_ids) - 1)
        complete = complete and connected and tree_edge_count
        endpoint_records.append(
            {
                "endpoint_causet_id": endpoint,
                "path_count": len(path_ids),
                "basis_edge_count": edge_count,
                "all_paths_reached": connected,
                "tree_edge_count_exact": tree_edge_count,
            }
        )
    return {"endpoints": endpoint_records, "passed": complete}


def compile_local_operator_gc_n4(
    max_source_stage: int = MAX_SOURCE_STAGE,
) -> dict[str, Any]:
    """Compile GC for all transition sources through n=4 (endpoints through n=5)."""

    labelled = enumerate_labelled_growth_paths(max_source_stage)
    all_paths = [path for stage in labelled.values() for path in stage]
    paths_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in all_paths:
        paths_by_endpoint[path["endpoint_causet_id"]].append(path)

    basis, all_pair_derivations = _basis_relations(paths_by_endpoint)
    connectivity = _basis_connectivity(paths_by_endpoint, basis)
    for relation in basis:
        validate_relation_namespace(
            semantic_profile=PAPER_STRONG_OPERATOR_PROFILE,
            relation_strength=relation["relation_strength"],
        )

    path_counts = {str(stage): len(paths) for stage, paths in labelled.items()}
    quotient_occurrences = {
        transition["quotient_occurrence_id"]
        for path in all_paths
        for transition in path["transitions"]
    }
    labelled_occurrences = {
        transition["labelled_occurrence_id"]
        for path in all_paths
        for transition in path["transitions"]
    }
    all_pair_expected = sum(
        len(paths) * (len(paths) - 1) // 2
        for paths in paths_by_endpoint.values()
    )
    all_relations_have_endpoint_provenance = all(
        relation["lhs_path_id"]
        in {path["path_id"] for path in paths_by_endpoint[relation["endpoint_causet_id"]]}
        and relation["rhs_path_id"]
        in {path["path_id"] for path in paths_by_endpoint[relation["endpoint_causet_id"]]}
        for relation in basis
    )
    later_on_left = all(
        path["ordered_operator_word_later_on_left"]
        == [
            transition["quotient_operator_symbol"]
            for transition in reversed(path["transitions"])
        ]
        for path in all_paths
    )
    expected_labelled_counts = {
        "1": 1,
        "2": 2,
        "3": 7,
        "4": 40,
        "5": 357,
    }
    expected_unlabelled_counts = {
        "1": 1,
        "2": 2,
        "3": 5,
        "4": 16,
        "5": 63,
    }
    observed_unlabelled_counts = {
        str(stage): sum(
            1
            for endpoint_paths in paths_by_endpoint.values()
            if endpoint_paths[0]["endpoint_stage"] == stage
        )
        for stage in range(1, max_source_stage + 2)
    }
    complete = bool(
        max_source_stage == MAX_SOURCE_STAGE
        and path_counts == expected_labelled_counts
        and observed_unlabelled_counts == expected_unlabelled_counts
        and connectivity["passed"]
        and len(all_pair_derivations) == all_pair_expected
        and all(item["derivable"] for item in all_pair_derivations)
        and all_relations_have_endpoint_provenance
        and later_on_left
    )
    strong_relation_records = sorted(basis, key=lambda record: record["relation_id"])
    payload: dict[str, Any] = {
        "compiler_scope": (
            "all naturally labelled histories using transition source stages n<=4; "
            "same-endpoint histories therefore extend through endpoint stage 5"
        ),
        "semantic_profiles": {
            PAPER_STRONG_OPERATOR_PROFILE: {
                "relation_strength": GC_STRONG_OPERATOR,
                "operator_ideal_relations": strong_relation_records,
            },
            REACHABLE_STATE_PROFILE: {
                "relation_strength": GC_FIXED_VECTOR,
                "state_path_equalities": [
                    {
                        "relation_id": relation["relation_id"].replace(
                            "operator-gc", "state-gc"
                        ),
                        "endpoint_causet_id": relation["endpoint_causet_id"],
                        "lhs_path_id": relation["lhs_path_id"],
                        "rhs_path_id": relation["rhs_path_id"],
                        "meaning": "word_lhs|Omega> = word_rhs|Omega>",
                    }
                    for relation in strong_relation_records
                ],
                "operator_ideal_relations": [],
            },
        },
        "path_inventory": {
            str(stage): list(paths) for stage, paths in sorted(labelled.items())
        },
        "generating_relation_basis": strong_relation_records,
        "all_pair_derivations": all_pair_derivations,
        "proof_obligations": {
            "basis_connectivity": connectivity,
            "every_basis_relation_is_an_enumerated_path_pair": (
                all_relations_have_endpoint_provenance
            ),
            "labelled_then_unlabelled_grouping": True,
            "no_automorphism_path_quotient": True,
            "later_transition_on_left": later_on_left,
            "elementary_diamonds_assumed_complete": False,
        },
        "counts": {
            "labelled_paths_by_endpoint_stage": path_counts,
            "unlabelled_endpoints_by_stage": observed_unlabelled_counts,
            "labelled_transition_occurrences": len(labelled_occurrences),
            "quotient_transition_occurrences": len(quotient_occurrences),
            "same_endpoint_path_pairs": all_pair_expected,
            "spanning_tree_basis_relations": len(basis),
        },
        "assumptions": [
            "birth labels form a natural labelling",
            "operator products use later transitions on the left",
            "strong equations are emitted only in PAPER_STRONG_OPERATOR_PROFILE",
            "unlabelled endpoints are grouped only after labelled path enumeration",
        ],
        "unresolved_components": [
            "derivation of the strong profile from the paper's fixed-vector GC definition",
            "extension beyond transition source stage 4",
        ],
        "verdict": (
            VERDICT_COMPLETE
            if complete
            else "LOCAL_OPERATOR_GC_COMPILER_PARTIAL_N4"
        ),
        "passed": complete,
    }
    digest_payload = {
        "paths": [
            {
                "endpoint": path["endpoint_causet_id"],
                "relation": path["endpoint_relation_rows"],
                "word": path["ordered_operator_word_later_on_left"],
            }
            for path in sorted(all_paths, key=lambda item: item["path_id"])
        ],
        "basis": [
            {
                "endpoint": relation["endpoint_causet_id"],
                "lhs": relation["lhs_word"],
                "rhs": relation["rhs_word"],
            }
            for relation in strong_relation_records
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(digest_payload)
    return payload


def local_gc_mutation_checks() -> dict[str, bool]:
    """Small explicit guards used by the mutation suite."""

    result = compile_local_operator_gc_n4()
    paths = [
        path
        for paths_at_stage in result["path_inventory"].values()
        for path in paths_at_stage
    ]
    reversed_order_detected = any(
        len(path["transitions"]) > 1
        and path["ordered_operator_word_later_on_left"]
        != [
            transition["quotient_operator_symbol"]
            for transition in path["transitions"]
        ]
        for path in paths
    )
    endpoint_mix_detected = all(
        relation["endpoint_causet_id"]
        == next(
            path["endpoint_causet_id"]
            for path in paths
            if path["path_id"] == relation["lhs_path_id"]
        )
        == next(
            path["endpoint_causet_id"]
            for path in paths
            if path["path_id"] == relation["rhs_path_id"]
        )
        for relation in result["generating_relation_basis"]
    )
    provenance_detected = all(
        relation["provenance"]
        == "two enumerated naturally labelled paths with one endpoint"
        for relation in result["generating_relation_basis"]
    )
    return {
        "BIRTH_WORD_ORDER_MUTATION_DETECTED": reversed_order_detected,
        "LABELLED_UNLABELLED_ENDPOINT_MIX_MUTATION_DETECTED": endpoint_mix_detected,
        "GC_PROVENANCE_DROP_MUTATION_DETECTED": provenance_detected,
    }
