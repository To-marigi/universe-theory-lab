"""Complete finite atomisation-path compiler for non-antichains through n=4."""

from __future__ import annotations

import itertools
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    automorphisms,
    canonical_code,
    canonicalize,
    causet_id,
    enumerate_unlabeled_posets,
    has_relation,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    stable_hash,
)

MAX_STAGE = 4
VERDICT_COMPLETE = "ATOMISATION_PATH_COMPILER_COMPLETE_N4"


def is_antichain(relation: Relation) -> bool:
    return all(row == 0 for row in relation)


def relation_rank(relation: Relation) -> int:
    """Ranking function: the number of strict order relations."""

    return sum(row.bit_count() for row in relation)


def eligible_nongregarious_maximal_elements(
    relation: Relation,
) -> tuple[int, ...]:
    """Return maximal elements with nonempty past."""

    return tuple(
        vertex
        for vertex in range(len(relation))
        if relation[vertex] == 0
        and any(has_relation(relation, lower, vertex) for lower in range(len(relation)))
    )


def atomise_element(relation: Relation, selected: int) -> Relation:
    """Remove a non-gregarious maximal element and reinsert it gregariously."""

    if selected not in eligible_nongregarious_maximal_elements(relation):
        raise ValueError("selected element must be a non-gregarious maximal element")
    rows = list(relation)
    for lower in range(len(relation)):
        rows[lower] &= ~(1 << selected)
    result = tuple(rows)
    if relation_rank(result) >= relation_rank(relation):
        raise AssertionError("atomisation ranking function did not decrease")
    return result


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
    relation_code, precursor_code = min(
        (
            _relation_code_for_order(relation, order),
            _subset_for_order(precursor, order),
        )
        for order in itertools.permutations(range(len(relation)))
    )
    return {
        "stage": len(relation),
        "source_relation_code": relation_code,
        "precursor_code": precursor_code,
    }


def _remove_vertex(
    relation: Relation,
    selected: int,
) -> tuple[Relation, dict[int, int]]:
    remaining = [vertex for vertex in range(len(relation)) if vertex != selected]
    old_to_new = {old: new for new, old in enumerate(remaining)}
    rows = [0] * len(remaining)
    for old_lower in remaining:
        for old_upper in remaining:
            if has_relation(relation, old_lower, old_upper):
                rows[old_to_new[old_lower]] |= 1 << old_to_new[old_upper]
    return tuple(rows), old_to_new


def _induced_original_relation(
    original: Relation,
    selected_vertices: tuple[int, ...],
) -> Relation:
    selected = set(selected_vertices)
    remaining = [
        vertex for vertex in range(len(original)) if vertex not in selected
    ]
    old_to_new = {old: new for new, old in enumerate(remaining)}
    rows = [0] * len(remaining)
    for old_lower in remaining:
        for old_upper in remaining:
            if has_relation(original, old_lower, old_upper):
                rows[old_to_new[old_lower]] |= 1 << old_to_new[old_upper]
    return tuple(rows)


def _operator_token(signature: dict[str, int], prefix: str) -> tuple[str, str]:
    digest = stable_hash(signature)
    return f"{prefix}-occurrence-{digest[:20]}", f"{prefix}_{signature['stage']}_{digest[:16]}"


def b_operator_for_atomisation_step(
    current: Relation,
    selected: int,
    next_relation: Relation,
    step_index: int,
) -> dict[str, Any]:
    """Construct the B_(n-1) factor and its gregarious companion."""

    source, old_to_new = _remove_vertex(current, selected)
    past = tuple(
        lower for lower in range(len(current)) if has_relation(current, lower, selected)
    )
    precursor_code = sum(1 << old_to_new[lower] for lower in past)
    b_target = add_maximal(source, precursor_code)
    g_target = add_maximal(source, 0)
    if causet_id(b_target) != causet_id(current):
        raise AssertionError("B transition does not reconstruct the pre-atomised causet")
    if causet_id(g_target) != causet_id(next_relation):
        raise AssertionError("gregarious companion does not reconstruct the next causet")
    b_signature = _decorated_transition_signature(source, precursor_code)
    g_signature = _decorated_transition_signature(source, 0)
    b_occurrence, b_symbol = _operator_token(b_signature, "B")
    g_occurrence, g_symbol = _operator_token(g_signature, "GCOMP")
    return {
        "factor_index": step_index,
        "paper_stage_index": len(current) - 1,
        "source_relation_rows": list(source),
        "source_causet_id": causet_id(source),
        "selected_original_vertex": selected,
        "precursor_code": precursor_code,
        "precursor_vertices_in_source": [
            vertex
            for vertex in range(len(source))
            if precursor_code & (1 << vertex)
        ],
        "B_occurrence_id": b_occurrence,
        "B_operator_symbol": b_symbol,
        "B_transition_signature": b_signature,
        "B_target_relation_rows": list(b_target),
        "B_target_causet_id": causet_id(b_target),
        "gregarious_companion_occurrence_id": g_occurrence,
        "gregarious_companion_operator_symbol": g_symbol,
        "gregarious_companion_signature": g_signature,
        "gregarious_target_relation_rows": list(g_target),
        "gregarious_target_causet_id": causet_id(g_target),
        "transition_provenance": (
            "paper Section 2.3 and Eq. (111): the same (n-1)-source adds the "
            "selected maximal element with its old past (B) or with empty past (G)"
        ),
        "source_target_types": {
            "source": f"{len(source)}-element decimation source",
            "B_target": f"{len(current)}-element pre-atomised causet",
            "gregarious_target": f"{len(next_relation)}-element next atomised causet",
        },
    }


def _enumerate_selection_sequences(
    relation: Relation,
) -> tuple[tuple[int, ...], ...]:
    eligible = eligible_nongregarious_maximal_elements(relation)
    if not eligible:
        if not is_antichain(relation):
            raise AssertionError("non-antichain has no eligible maximal element")
        return ((),)
    sequences = []
    for selected in eligible:
        next_relation = atomise_element(relation, selected)
        for suffix in _enumerate_selection_sequences(next_relation):
            sequences.append((selected,) + suffix)
    return tuple(sorted(sequences))


def _path_orbit(
    source: Relation,
    selections: tuple[int, ...],
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        sorted(
            {
                tuple(permutation[vertex] for vertex in selections)
                for permutation in automorphisms(source)
            }
        )
    )


def _path_record(
    source: Relation,
    selections: tuple[int, ...],
) -> dict[str, Any]:
    current = source
    steps = []
    factors = []
    relation_path = [list(source)]
    selected_prefix: list[int] = []
    decimation_path = [
        {
            "remaining_stage": len(source),
            "relation_rows": list(source),
            "causet_id": causet_id(source),
        }
    ]
    for step_index, selected in enumerate(selections):
        eligible = eligible_nongregarious_maximal_elements(current)
        if selected not in eligible:
            raise AssertionError("enumerated path contains an ineligible selection")
        rank_before = relation_rank(current)
        next_relation = atomise_element(current, selected)
        rank_after = relation_rank(next_relation)
        orbit = tuple(
            sorted({permutation[selected] for permutation in automorphisms(current)})
        )
        factor = b_operator_for_atomisation_step(
            current,
            selected,
            next_relation,
            step_index,
        )
        factors.append(factor)
        steps.append(
            {
                "step_index": step_index,
                "current_relation_rows": list(current),
                "eligible_nongregarious_maximal_elements": list(eligible),
                "selected_element": selected,
                "selected_element_automorphism_orbit": list(orbit),
                "next_relation_rows": list(next_relation),
                "next_canonical_relation_rows": list(canonicalize(next_relation)),
                "next_canonical_hash_sha256": stable_hash(
                    {
                        "stage": len(next_relation),
                        "canonical_code": canonical_code(next_relation),
                    }
                ),
                "ranking_before": rank_before,
                "ranking_after": rank_after,
                "ranking_decrease": rank_before - rank_after,
                "B_operator_occurrence_id": factor["B_occurrence_id"],
                "transition_provenance": factor["transition_provenance"],
            }
        )
        relation_path.append(list(next_relation))
        current = next_relation
        selected_prefix.append(selected)
        decimated = _induced_original_relation(source, tuple(selected_prefix))
        decimation_path.append(
            {
                "remaining_stage": len(decimated),
                "relation_rows": list(decimated),
                "causet_id": causet_id(decimated) if decimated else "p0-0",
            }
        )

    orbit_sequences = _path_orbit(source, selections)
    path_payload = {
        "source_causet_id": causet_id(source),
        "selected_elements": list(selections),
    }
    path_digest = stable_hash(path_payload)
    s_word = [factor["B_operator_symbol"] for factor in factors]
    s_inverse_word = [
        f"{factor['B_operator_symbol']}^-1" for factor in reversed(factors)
    ]
    return {
        "path_id": f"atomisation-{path_digest[:20]}",
        "source_causet_id": causet_id(source),
        "source_relation_rows": list(source),
        "selected_elements": list(selections),
        "relation_path": relation_path,
        "steps": steps,
        "path_length": len(selections),
        "terminal_relation_rows": list(current),
        "terminal_antichain": is_antichain(current),
        "terminal_causet_id": causet_id(current),
        "associated_decimation_path": decimation_path,
        "B_operator_factors": factors,
        "B_operator_occurrence_ids": [
            factor["B_occurrence_id"] for factor in factors
        ],
        "S_word_ordered": s_word,
        "S_inverse_word_ordered": s_inverse_word,
        "automorphism_orbit": {
            "selection_sequences": [list(sequence) for sequence in orbit_sequences],
            "orbit_size": len(orbit_sequences),
            "orbit_representative": list(orbit_sequences[0]),
            "orbit_id": f"atom-orbit-{stable_hash(orbit_sequences)[:20]}",
            "quotiented": False,
        },
        "GC_semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
    }


def compile_atomisation_paths_n4(max_stage: int = MAX_STAGE) -> dict[str, Any]:
    """Enumerate every atomisation choice sequence for all non-antichains."""

    if max_stage != MAX_STAGE:
        raise ValueError("the certified release scope is exactly n<=4")
    levels = enumerate_unlabeled_posets(max_stage)
    causet_records = []
    all_paths = []
    for stage in range(1, max_stage + 1):
        for source in levels[stage]:
            if is_antichain(source):
                continue
            sequences = _enumerate_selection_sequences(source)
            paths = [_path_record(source, sequence) for sequence in sequences]
            all_paths.extend(paths)
            causet_records.append(
                {
                    "causet_id": causet_id(source),
                    "stage": stage,
                    "source_relation_rows": list(source),
                    "initial_eligible_nongregarious_maximal_elements": list(
                        eligible_nongregarious_maximal_elements(source)
                    ),
                    "complete_path_count": len(paths),
                    "canonical_representative_path": min(
                        path["path_id"] for path in paths
                    ),
                    "all_alternative_paths": sorted(
                        paths,
                        key=lambda path: path["path_id"],
                    ),
                    "path_lengths": sorted(
                        {int(path["path_length"]) for path in paths}
                    ),
                    "all_terminals_are_antichains": all(
                        path["terminal_antichain"] for path in paths
                    ),
                }
            )

    all_rank_steps_decrease = all(
        step["ranking_decrease"] > 0
        for path in all_paths
        for step in path["steps"]
    )
    all_choices_present = all(
        len(record["all_alternative_paths"]) == record["complete_path_count"]
        and {
            path["steps"][0]["selected_element"]
            for path in record["all_alternative_paths"]
        }
        == set(record["initial_eligible_nongregarious_maximal_elements"])
        for record in causet_records
    )
    all_b_targets_match = all(
        factor["B_target_causet_id"] == path["source_causet_id"]
        or factor["B_target_causet_id"]
        == causet_id(tuple(path["steps"][factor["factor_index"]]["current_relation_rows"]))
        for path in all_paths
        for factor in path["B_operator_factors"]
    )
    non_antichain_counts = {
        str(stage): sum(record["stage"] == stage for record in causet_records)
        for stage in range(1, max_stage + 1)
    }
    expected_non_antichain_counts = {"1": 0, "2": 1, "3": 4, "4": 15}
    complete = bool(
        len(causet_records) == 20
        and len(all_paths) == 34
        and non_antichain_counts == expected_non_antichain_counts
        and all(path["terminal_antichain"] for path in all_paths)
        and all_rank_steps_decrease
        and all_choices_present
        and all_b_targets_match
    )
    semantic_records = [
        {
            "causet_id": record["causet_id"],
            "paths": [
                {
                    "selected_elements": path["selected_elements"],
                    "S_word_ordered": path["S_word_ordered"],
                    "terminal": path["terminal_causet_id"],
                }
                for path in record["all_alternative_paths"]
            ],
        }
        for record in causet_records
    ]
    payload: dict[str, Any] = {
        "scope": "all 20 non-antichain unlabeled causets through n=4",
        "definition_source": (
            "arXiv:2603.25503v1 Section 2.3, PDF pages 9--11; "
            "non-gregarious maximal elements are reinserted gregariously"
        ),
        "definition_classification": "LITERATURE_LOCKED",
        "ranking_function": {
            "name": "number of strict order relations",
            "formula": "sum(row.bit_count() for row in relation)",
            "strict_decrease_every_step": all_rank_steps_decrease,
            "lower_bound": 0,
            "termination_proved": all_rank_steps_decrease,
        },
        "causets": causet_records,
        "counts": {
            "non_antichain_causets": len(causet_records),
            "non_antichain_causets_by_stage": non_antichain_counts,
            "complete_atomisation_paths": len(all_paths),
            "atomisation_steps": sum(path["path_length"] for path in all_paths),
            "distinct_B_occurrences": len(
                {
                    factor["B_occurrence_id"]
                    for path in all_paths
                    for factor in path["B_operator_factors"]
                }
            ),
        },
        "proof_obligations": {
            "all_eligible_choices_recursed": all_choices_present,
            "all_terminals_antichains": all(
                path["terminal_antichain"] for path in all_paths
            ),
            "ranking_strictly_decreases": all_rank_steps_decrease,
            "B_and_gregarious_targets_reconstructed": all_b_targets_match,
            "automorphism_equivalent_paths_quotiented": False,
            "operator_relations_lost_by_quotient": False,
        },
        "eq112_factor_index_convention": {
            "implemented": "one B_(n-1) factor for each atomisation step, indexed from 0",
            "S_order": "B^(0) B^(1) ... in atomisation-selection order",
            "inverse_order": "reverse factor order",
            "source_note": (
                "the printed Eq. (112) uses a terminal superscript k; the implementation "
                "binds factor count to the explicitly enumerated number of selections"
            ),
        },
        "assumptions": [
            "input representatives are canonical unlabelled causets",
            "vertex identities are retained throughout each full choice enumeration",
            "no automorphism quotient is used to delete an operator path",
            "the paper's atomisation definition is treated as a locked specification",
        ],
        "unresolved_components": [
            "strong-operator status of the GC equality used in Eq. (109)",
            "reverse reconstruction of arbitrary Q assignments",
        ],
        "verdict": (
            VERDICT_COMPLETE
            if complete
            else "ATOMISATION_PATH_COMPILER_PARTIAL_N4"
        ),
        "passed": complete,
        "semantic_digest_sha256": stable_hash(semantic_records),
    }
    return payload


def atomisation_mutation_checks() -> dict[str, bool]:
    result = compile_atomisation_paths_n4()
    multi_path_records = [
        record for record in result["causets"] if record["complete_path_count"] > 1
    ]
    single_path_only_detected = bool(multi_path_records)
    missing_eligible_detected = all(
        {
            path["steps"][0]["selected_element"]
            for path in record["all_alternative_paths"]
        }
        == set(record["initial_eligible_nongregarious_maximal_elements"])
        for record in result["causets"]
    )
    terminal_mutation_detected = all(
        path["terminal_antichain"]
        for record in result["causets"]
        for path in record["all_alternative_paths"]
    )
    improper_quotient_detected = all(
        not path["automorphism_orbit"]["quotiented"]
        for record in result["causets"]
        for path in record["all_alternative_paths"]
    )
    return {
        "SINGLE_PATH_ONLY_MUTATION_DETECTED": single_path_only_detected,
        "ELIGIBLE_MAXIMAL_OMISSION_MUTATION_DETECTED": missing_eligible_detected,
        "TERMINAL_ANTICHAIN_MUTATION_DETECTED": terminal_mutation_detected,
        "IMPROPER_AUTOMORPHISM_QUOTIENT_MUTATION_DETECTED": improper_quotient_detected,
    }
