"""Independent v0.3.3 GC/atomisation oracle.

This file intentionally uses only the Python standard library.  It does not
import production canonicalisation, path, transition, or atomisation helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

Relation = tuple[int, ...]


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def has_relation(relation: Relation, lower: int, upper: int) -> bool:
    return bool(relation[lower] & (1 << upper))


def validate_relation(relation: Relation) -> bool:
    size = len(relation)
    for vertex, row in enumerate(relation):
        if row & (1 << vertex):
            return False
        if row & ~((1 << size) - 1):
            return False
    return all(
        not (
            has_relation(relation, lower, middle)
            and has_relation(relation, middle, upper)
        )
        or has_relation(relation, lower, upper)
        for lower in range(size)
        for middle in range(size)
        for upper in range(size)
    )


def raw_relation_code(relation: Relation) -> int:
    size = len(relation)
    return sum(row << (index * size) for index, row in enumerate(relation))


def relation_code_for_order(
    relation: Relation,
    order: tuple[int, ...],
) -> int:
    size = len(relation)
    code = 0
    for new_lower, old_lower in enumerate(order):
        for new_upper, old_upper in enumerate(order):
            if has_relation(relation, old_lower, old_upper):
                code |= 1 << (new_lower * size + new_upper)
    return code


def relation_from_code(size: int, code: int) -> Relation:
    mask = (1 << size) - 1
    return tuple((code >> (row * size)) & mask for row in range(size))


def canonical_code(relation: Relation) -> int:
    if not validate_relation(relation):
        raise ValueError("invalid strict order")
    if not relation:
        return 0
    return min(
        relation_code_for_order(relation, order)
        for order in itertools.permutations(range(len(relation)))
    )


def canonicalize(relation: Relation) -> Relation:
    return relation_from_code(len(relation), canonical_code(relation))


def causet_id(relation: Relation) -> str:
    size = len(relation)
    width = max(1, math.ceil(size * size / 4))
    return f"p{size}-{canonical_code(relation):0{width}x}"


def is_downset(relation: Relation, subset: int) -> bool:
    for member in range(len(relation)):
        if not subset & (1 << member):
            continue
        for predecessor in range(len(relation)):
            if has_relation(relation, predecessor, member) and not subset & (
                1 << predecessor
            ):
                return False
    return True


def downsets(relation: Relation) -> tuple[int, ...]:
    return tuple(
        subset
        for subset in range(1 << len(relation))
        if is_downset(relation, subset)
    )


def add_maximal(relation: Relation, precursor: int) -> Relation:
    if not is_downset(relation, precursor):
        raise ValueError("precursor is not a down-set")
    size = len(relation)
    rows = list(relation) + [0]
    for predecessor in range(size):
        if precursor & (1 << predecessor):
            rows[predecessor] |= 1 << size
    result = tuple(rows)
    if not validate_relation(result):
        raise AssertionError("growth created a non-poset")
    return result


def subset_for_order(subset: int, order: tuple[int, ...]) -> int:
    return sum(
        1 << new_vertex
        for new_vertex, old_vertex in enumerate(order)
        if subset & (1 << old_vertex)
    )


def decorated_transition_signature(
    relation: Relation,
    precursor: int,
) -> dict[str, int]:
    relation_code, precursor_code = min(
        (
            relation_code_for_order(relation, order),
            subset_for_order(precursor, order),
        )
        for order in itertools.permutations(range(len(relation)))
    )
    return {
        "stage": len(relation),
        "source_relation_code": relation_code,
        "precursor_code": precursor_code,
    }


def transition_record(
    source: Relation,
    precursor: int,
    target: Relation,
) -> dict[str, Any]:
    signature = decorated_transition_signature(source, precursor)
    quotient_digest = stable_hash(signature)
    labelled_payload = {
        "stage": len(source),
        "source_relation_rows": list(source),
        "precursor_code": precursor,
        "target_relation_rows": list(target),
    }
    labelled_digest = stable_hash(labelled_payload)
    return {
        "quotient_occurrence_id": f"lgc-orbit-{quotient_digest[:20]}",
        "quotient_operator_symbol": f"A_{len(source)}_{quotient_digest[:16]}",
        "labelled_occurrence_id": f"lgc-labelled-{labelled_digest[:20]}",
    }


def enumerate_labelled_paths() -> dict[int, list[dict[str, Any]]]:
    states: dict[int, list[dict[str, Any]]] = {
        1: [
            {
                "relation": (0,),
                "relations": ((0,),),
                "transitions": (),
            }
        ]
    }
    for stage in range(1, 5):
        next_states: dict[Relation, dict[str, Any]] = {}
        for state in states[stage]:
            for precursor in downsets(state["relation"]):
                target = add_maximal(state["relation"], precursor)
                transition = transition_record(
                    state["relation"],
                    precursor,
                    target,
                )
                candidate = {
                    "relation": target,
                    "relations": state["relations"] + (target,),
                    "transitions": state["transitions"] + (transition,),
                }
                if target in next_states and next_states[target] != candidate:
                    raise AssertionError("duplicate labelled growth history")
                next_states[target] = candidate
        states[stage + 1] = [
            next_states[relation]
            for relation in sorted(next_states, key=raw_relation_code)
        ]

    result: dict[int, list[dict[str, Any]]] = {}
    for stage, stage_states in states.items():
        paths = []
        for state in stage_states:
            chronological = [
                transition["quotient_occurrence_id"]
                for transition in state["transitions"]
            ]
            path_digest = stable_hash(
                {
                    "endpoint_relation_rows": list(state["relation"]),
                    "chronological_occurrences": chronological,
                }
            )
            paths.append(
                {
                    "path_id": f"lgc-path-{path_digest[:20]}",
                    "stage": stage,
                    "endpoint_relation": state["relation"],
                    "endpoint_causet_id": causet_id(state["relation"]),
                    "endpoint_labelled_code": raw_relation_code(
                        state["relation"]
                    ),
                    "ordered_operator_word": [
                        transition["quotient_operator_symbol"]
                        for transition in reversed(state["transitions"])
                    ],
                }
            )
        result[stage] = sorted(paths, key=lambda path: path["path_id"])
    return result


def local_gc_basis(
    paths: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for stage_paths in paths.values():
        for path in stage_paths:
            grouped[path["endpoint_causet_id"]].append(path)
    relations = []
    all_pair_count = 0
    for endpoint, endpoint_paths in sorted(grouped.items()):
        ordered = sorted(endpoint_paths, key=lambda path: path["path_id"])
        all_pair_count += len(ordered) * (len(ordered) - 1) // 2
        if len(ordered) < 2:
            continue
        anchor = ordered[0]
        for path in ordered[1:]:
            relation_id = (
                "operator-gc-"
                + stable_hash(
                    {
                        "endpoint": endpoint,
                        "lhs_path": path["path_id"],
                        "rhs_path": anchor["path_id"],
                    }
                )[:20]
            )
            relations.append(
                {
                    "relation_id": relation_id,
                    "endpoint_causet_id": endpoint,
                    "lhs_path_id": path["path_id"],
                    "rhs_path_id": anchor["path_id"],
                    "lhs_word": path["ordered_operator_word"],
                    "rhs_word": anchor["ordered_operator_word"],
                }
            )
    return sorted(relations, key=lambda item: item["relation_id"]), all_pair_count


def enumerate_unlabelled_levels(max_stage: int = 4) -> list[list[Relation]]:
    levels: list[list[Relation]] = [[()]]
    for _stage in range(max_stage):
        next_level: dict[int, Relation] = {}
        for source in levels[-1]:
            for precursor in downsets(source):
                target = canonicalize(add_maximal(source, precursor))
                next_level[canonical_code(target)] = target
        levels.append(
            [next_level[code] for code in sorted(next_level)]
        )
    return levels


def is_antichain(relation: Relation) -> bool:
    return all(row == 0 for row in relation)


def eligible(relation: Relation) -> tuple[int, ...]:
    return tuple(
        vertex
        for vertex in range(len(relation))
        if relation[vertex] == 0
        and any(
            has_relation(relation, lower, vertex)
            for lower in range(len(relation))
        )
    )


def atomise(relation: Relation, selected: int) -> Relation:
    if selected not in eligible(relation):
        raise ValueError("ineligible atomisation element")
    rows = list(relation)
    for lower in range(len(relation)):
        rows[lower] &= ~(1 << selected)
    return tuple(rows)


def atomisation_sequences(relation: Relation) -> tuple[tuple[int, ...], ...]:
    choices = eligible(relation)
    if not choices:
        if not is_antichain(relation):
            raise AssertionError("atomisation stalled before an antichain")
        return ((),)
    sequences = []
    for selected in choices:
        for suffix in atomisation_sequences(atomise(relation, selected)):
            sequences.append((selected,) + suffix)
    return tuple(sorted(sequences))


def remove_vertex(
    relation: Relation,
    selected: int,
) -> tuple[Relation, dict[int, int]]:
    remaining = [
        vertex for vertex in range(len(relation)) if vertex != selected
    ]
    old_to_new = {old: new for new, old in enumerate(remaining)}
    rows = [0] * len(remaining)
    for old_lower in remaining:
        for old_upper in remaining:
            if has_relation(relation, old_lower, old_upper):
                rows[old_to_new[old_lower]] |= 1 << old_to_new[old_upper]
    return tuple(rows), old_to_new


def b_symbol(current: Relation, selected: int) -> str:
    source, old_to_new = remove_vertex(current, selected)
    past = [
        lower
        for lower in range(len(current))
        if has_relation(current, lower, selected)
    ]
    precursor = sum(1 << old_to_new[lower] for lower in past)
    signature = decorated_transition_signature(source, precursor)
    digest = stable_hash(signature)
    return f"B_{len(source)}_{digest[:16]}"


def atomisation_inventory() -> tuple[list[dict[str, Any]], int]:
    levels = enumerate_unlabelled_levels()
    causets = []
    total_steps = 0
    for stage in range(1, 5):
        for source in levels[stage]:
            if is_antichain(source):
                continue
            paths = []
            for selections in atomisation_sequences(source):
                current = source
                symbols = []
                for selected in selections:
                    symbols.append(b_symbol(current, selected))
                    current = atomise(current, selected)
                if not is_antichain(current):
                    raise AssertionError("nonterminal atomisation path")
                total_steps += len(selections)
                path_id = (
                    "atomisation-"
                    + stable_hash(
                        {
                            "source_causet_id": causet_id(source),
                            "selected_elements": list(selections),
                        }
                    )[:20]
                )
                paths.append(
                    {
                        "path_id": path_id,
                        "causet_id": causet_id(source),
                        "selected_elements": list(selections),
                        "S_word": symbols,
                        "S_inverse_word": [
                            f"{symbol}^-1" for symbol in reversed(symbols)
                        ],
                    }
                )
            paths.sort(key=lambda path: path["path_id"])
            canonical_path = min(path["path_id"] for path in paths)
            causets.append(
                {
                    "causet_id": causet_id(source),
                    "stage": stage,
                    "paths": paths,
                    "canonical_path_id": canonical_path,
                }
            )
    return causets, total_steps


def semantic_summary() -> dict[str, Any]:
    labelled = enumerate_labelled_paths()
    basis, all_pair_count = local_gc_basis(labelled)
    atom_causets, atom_steps = atomisation_inventory()
    all_labelled_paths = [
        path for stage_paths in labelled.values() for path in stage_paths
    ]
    atom_paths = [
        path for record in atom_causets for path in record["paths"]
    ]
    endpoint_groups = {
        stage: {
            path["endpoint_causet_id"] for path in stage_paths
        }
        for stage, stage_paths in labelled.items()
    }
    summary: dict[str, Any] = {
        "labelled_path_counts": {
            str(stage): len(stage_paths)
            for stage, stage_paths in labelled.items()
        },
        "unlabelled_endpoint_counts": {
            str(stage): len(endpoints)
            for stage, endpoints in endpoint_groups.items()
        },
        "local_gc_basis_relation_count": len(basis),
        "same_endpoint_path_pair_count": all_pair_count,
        "non_antichain_causet_count": len(atom_causets),
        "atomisation_path_count": len(atom_paths),
        "atomisation_step_count": atom_steps,
        "atomisation_path_counts_by_causet": {
            record["causet_id"]: len(record["paths"])
            for record in atom_causets
        },
        "endpoint_path_provenance": [
            {
                "path_id": path["path_id"],
                "stage": path["stage"],
                "endpoint_causet_id": path["endpoint_causet_id"],
                "endpoint_labelled_code": path["endpoint_labelled_code"],
                "ordered_operator_word": path["ordered_operator_word"],
            }
            for path in sorted(
                all_labelled_paths,
                key=lambda item: item["path_id"],
            )
        ],
        "local_gc_basis_provenance": basis,
        "atomisation_path_provenance": [
            {
                "path_id": path["path_id"],
                "causet_id": path["causet_id"],
                "selected_elements": path["selected_elements"],
                "S_word": path["S_word"],
                "S_inverse_word": path["S_inverse_word"],
            }
            for path in sorted(atom_paths, key=lambda item: item["path_id"])
        ],
        "reduced_generator_mapping": [
            {
                "causet_id": record["causet_id"],
                "canonical_path_id": record["canonical_path_id"],
                "ordered_word": next(
                    path["S_word"]
                    + [f"Q_{record['stage']}"]
                    + path["S_inverse_word"]
                    for path in record["paths"]
                    if path["path_id"] == record["canonical_path_id"]
                ),
            }
            for record in sorted(
                atom_causets,
                key=lambda item: item["causet_id"],
            )
        ],
    }
    summary["semantic_digest_sha256"] = stable_hash(summary)
    return summary


def run_oracle(
    production_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = semantic_summary()
    expected_counts = {
        "labelled_path_counts": {
            "1": 1,
            "2": 2,
            "3": 7,
            "4": 40,
            "5": 357,
        },
        "unlabelled_endpoint_counts": {
            "1": 1,
            "2": 2,
            "3": 5,
            "4": 16,
            "5": 63,
        },
        "local_gc_basis_relation_count": 320,
        "same_endpoint_path_pair_count": 1529,
        "non_antichain_causet_count": 20,
        "atomisation_path_count": 34,
        "atomisation_step_count": 76,
    }
    independent_checks = {
        key: summary[key] == value for key, value in expected_counts.items()
    }
    comparison: dict[str, Any] = {
        "performed": production_summary is not None,
        "semantic_digest_match": None,
        "section_matches": {},
        "mismatched_sections": [],
    }
    if production_summary is not None:
        keys = sorted(set(summary) | set(production_summary))
        section_matches = {
            key: summary.get(key) == production_summary.get(key) for key in keys
        }
        comparison = {
            "performed": True,
            "semantic_digest_match": (
                summary["semantic_digest_sha256"]
                == production_summary.get("semantic_digest_sha256")
            ),
            "section_matches": section_matches,
            "mismatched_sections": [
                key for key, matched in section_matches.items() if not matched
            ],
        }
    passed = all(independent_checks.values()) and (
        production_summary is None
        or bool(comparison["semantic_digest_match"])
        and not comparison["mismatched_sections"]
    )
    return {
        "schema_version": "final-theory-independent-oracle-v0.3.3",
        "implementation_boundary": (
            "standard-library-only brute-force implementation; no production imports"
        ),
        "independent_checks": independent_checks,
        "semantic_summary": summary,
        "production_comparison": comparison,
        "unresolved_components": [],
        "verdict": (
            "INDEPENDENT_ORACLE_COMPLETE_MATCH_N4"
            if passed and production_summary is not None
            else (
                "INDEPENDENT_ORACLE_SELF_CHECK_COMPLETE_N4"
                if passed
                else "INDEPENDENT_ORACLE_MISMATCH"
            )
        ),
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    production = None
    if arguments.compare is not None:
        production = json.loads(arguments.compare.read_text(encoding="utf-8"))
    result = run_oracle(production)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
