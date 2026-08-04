from __future__ import annotations

import copy
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_stage_plan_v042 as plan


def _record(identifier: int, term_count: int) -> dict[str, Any]:
    terms = [[identifier, position] for position in range(term_count)]
    return {
        "polynomial_id": identifier,
        "term_count": term_count,
        "sha256": plan.canonical_digest(terms),
        "terms": terms,
    }


def _fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    term_counts = [0, 2, 3, 2, 2, 1, 1, 2, 3, 4]
    records = [_record(identifier, term_count) for identifier, term_count in enumerate(term_counts)]
    correspondence = [[record["polynomial_id"], record["sha256"]] for record in records]
    chunks = [
        {
            "arena": "polynomial_arena",
            "first_polynomial_id": 0,
            "last_polynomial_id": len(records) - 1,
            "record_count": len(records),
            "uncompressed_sha256": "c" * 64,
        }
    ]
    root: dict[str, Any] = {
        "schema_version": 1,
        "arena_index": {
            "polynomial_arena": {
                "record_count": len(records),
                "term_count_total": sum(term_counts),
                "polynomial_id_to_sha256": correspondence,
                "polynomial_id_to_sha256_digest_sha256": plan.canonical_digest(correspondence),
            }
        },
        "chunk_ledger": {
            "chunks": chunks,
            "chunk_ledger_digest_sha256": plan.canonical_digest(chunks),
        },
        "chart_generator_ids": {
            "charts": {
                "U2": {
                    "chart_manifest_sha256": "a" * 64,
                    "generator_manifest_sha256": "b" * 64,
                    "generator_count": 6,
                    "generator_polynomial_ids": [
                        [0, 0, 0],
                        [1, 1, 2],
                        [2, 3, 0],
                        [3, 1, 2],
                        [4, 4, 0],
                        [5, 5, 0],
                    ],
                    "planned_Rabinowitsch_localization_polynomial_id": 9,
                },
                "aligned_w2_equals_1": {
                    "chart_manifest_sha256": "d" * 64,
                    "generator_manifest_sha256": "e" * 64,
                    "generator_count": 5,
                    "generator_auxiliary_key_order": ["constant", "h", "w3", "w4"],
                    "generator_polynomial_ids": [
                        [0, 0, 0, 0, 0],
                        [1, 1, 0, 0, 0],
                        [2, 3, 4, 0, 0],
                        [3, 1, 0, 0, 0],
                        [4, 5, 0, 0, 0],
                    ],
                    "planned_Rabinowitsch_localization_polynomial_id": 9,
                },
            }
        },
    }
    root["semantic_digest_sha256"] = plan.canonical_digest(root)
    return root, records


def _cache() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    root, records = _fixture()
    return root, records, plan.build_arena_metadata_cache(iter(records), root)


def _resign(payload: dict[str, Any]) -> None:
    payload["semantic_digest_sha256"] = plan.canonical_digest(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def test_arena_metadata_cache_is_content_addressed_and_root_bound() -> None:
    root, records, cache = _cache()

    metadata = plan.validate_arena_metadata_cache(cache, root)

    assert metadata[0] == {"term_count": 0, "sha256": plan.canonical_digest([])}
    assert metadata[2]["term_count"] == 3
    assert cache["record_count"] == len(records)
    assert cache["term_count_total"] == sum(record["term_count"] for record in records)
    assert cache["committed_root_semantic_digest_sha256"] == root["semantic_digest_sha256"]
    assert cache["cache_key_sha256"] == plan.canonical_digest(
        {
            "arena": "polynomial_arena",
            "committed_root_semantic_digest_sha256": root["semantic_digest_sha256"],
            "committed_chunk_ledger_digest_sha256": root["chunk_ledger"][
                "chunk_ledger_digest_sha256"
            ],
            "committed_arena_index_digest_sha256": root["arena_index"]["polynomial_arena"][
                "polynomial_id_to_sha256_digest_sha256"
            ],
        }
    )


def test_arena_metadata_builder_is_an_iterator_pure_function_and_fails_closed() -> None:
    root, records = _fixture()
    yielded: list[int] = []

    def source() -> Iterator[dict[str, Any]]:
        for record in reversed(records):
            yielded.append(record["polynomial_id"])
            yield record

    cache = plan.build_arena_metadata_cache(source(), root)

    assert yielded == list(reversed(range(len(records))))
    assert list(cache["polynomial_metadata"]) == [str(value) for value in range(len(records))]

    bad_count = copy.deepcopy(records)
    bad_count[1]["term_count"] += 1
    with pytest.raises(ValueError, match="term count mismatch"):
        plan.build_arena_metadata_cache(iter(bad_count), root)

    missing = records[:-1]
    with pytest.raises(ValueError, match="incomplete"):
        plan.build_arena_metadata_cache(iter(missing), root)

    bad_root = copy.deepcopy(root)
    bad_root["chunk_ledger"]["chunks"][0]["record_count"] -= 1
    _resign(bad_root)
    with pytest.raises(ValueError, match="chunk-ledger digest mismatch"):
        plan.build_arena_metadata_cache(iter(records), bad_root)


def test_cache_validation_detects_metadata_mutation_even_when_envelope_is_resigned() -> None:
    root, _records, cache = _cache()
    tampered = copy.deepcopy(cache)
    tampered["polynomial_metadata"]["1"]["term_count"] += 1
    tampered["term_count_total"] += 1
    _resign(tampered)

    with pytest.raises(ValueError, match="total term count mismatch|metadata digest mismatch"):
        plan.validate_arena_metadata_cache(tampered, root)


def test_non_aligned_plan_drops_rows_and_stably_orders_by_cost() -> None:
    root, _records, cache = _cache()

    stage_plan = plan.build_stage_plan(
        root,
        "U2",
        cache,
        stage_sizes=(1, 3, None),
    )

    selection = stage_plan["row_selection"]
    assert selection["source_row_count"] == 6
    assert selection["dropped_zero_row_count"] == 1
    assert selection["dropped_duplicate_row_count"] == 1
    assert selection["unique_row_count"] == 4
    assert selection["cost_ordered_source_row_indices"] == [5, 2, 4, 1]
    assert [row["generator_cost_terms"] for row in selection["rows"]] == [5, 2, 2, 1]

    stages = stage_plan["stages"]
    assert [stage["selected_source_row_indices"] for stage in stages] == [
        [5],
        [5, 2, 4],
        [5, 2, 4, 1],
    ]
    assert stages[0]["needed_polynomial_ids"] == [5, 9]
    assert stages[1]["needed_polynomial_ids"] == [3, 4, 5, 9]
    assert stages[2]["needed_polynomial_ids"] == [1, 2, 3, 4, 5, 9]
    assert [stage["selected_generator_count"] for stage in stages] == [2, 4, 5]
    assert set(stages[0]["selected_unique_row_indices"]) < set(
        stages[1]["selected_unique_row_indices"]
    )
    assert set(stages[1]["selected_unique_row_indices"]) < set(
        stages[2]["selected_unique_row_indices"]
    )
    assert plan.validate_stage_plan(stage_plan, root, cache) == stage_plan


def test_aligned_plan_pins_all_required_generators_into_every_stage() -> None:
    root, _records, cache = _cache()
    required = {"d2": 6, "d3": 7, "d4": 8}

    stage_plan = plan.build_stage_plan(
        root,
        "aligned_w2_equals_1",
        cache,
        stage_sizes=(0, 1, None),
        required_aligned_quotient_polynomial_ids=required,
    )

    assert stage_plan["row_selection"]["cost_ordered_source_row_indices"] == [4, 1, 2]
    assert [
        record["name"] for record in stage_plan["fixed_generators"]["aligned_quotient_generators"]
    ] == ["d2", "d3", "d4"]
    for stage in stage_plan["stages"]:
        assert {6, 7, 8, 9} <= set(stage["needed_polynomial_ids"])
    assert stage_plan["stages"][0]["selected_source_row_indices"] == []
    assert stage_plan["stages"][0]["selected_generator_count"] == 4
    assert stage_plan["stages"][1]["selected_source_row_indices"] == [4]
    assert stage_plan["stages"][1]["selected_generator_count"] == 5
    assert plan.validate_stage_plan(stage_plan, root, cache) == stage_plan

    with pytest.raises(ValueError, match="require exactly"):
        plan.build_stage_plan(root, "aligned_w2_equals_1", cache, stage_sizes=(1,))
    with pytest.raises(ValueError, match="cannot have aligned"):
        plan.build_stage_plan(
            root,
            "U2",
            cache,
            stage_sizes=(1,),
            required_aligned_quotient_polynomial_ids=required,
        )


def test_plan_validation_reconstructs_instead_of_trusting_a_resigned_plan() -> None:
    root, _records, cache = _cache()
    stage_plan = plan.build_stage_plan(root, "U2", cache, stage_sizes=(1, None))

    unsigned_tamper = copy.deepcopy(stage_plan)
    unsigned_tamper["stages"][0]["needed_polynomial_ids"].append(1)
    with pytest.raises(ValueError, match="semantic digest mismatch"):
        plan.validate_stage_plan(unsigned_tamper, root, cache)

    resigned_tamper = copy.deepcopy(stage_plan)
    resigned_tamper["stages"][0]["needed_polynomial_ids"].append(1)
    _resign(resigned_tamper)
    with pytest.raises(ValueError, match="does not match its frozen inputs"):
        plan.validate_stage_plan(resigned_tamper, root, cache)


def test_stage_sizes_must_preserve_nested_subsets() -> None:
    root, _records, cache = _cache()

    with pytest.raises(ValueError, match="non-decreasing"):
        plan.build_stage_plan(root, "U2", cache, stage_sizes=(3, 1))
    with pytest.raises(ValueError, match="None only at the end"):
        plan.build_stage_plan(root, "U2", cache, stage_sizes=(None, 1))


def test_real_frozen_rows_reduce_without_scanning_the_arena() -> None:
    root_path = (
        Path(__file__).resolve().parents[2]
        / "results"
        / "v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.json"
    )
    frozen_root = json.loads(root_path.read_text(encoding="utf-8"))

    expected = {
        "U2": (336, 248, 543, 2),
        "U3": (336, 248, 543, 2),
        "U4": (336, 248, 543, 2),
        "aligned_w2_equals_1": (332, 243, 552, 4),
        "aligned_w3_equals_1": (332, 243, 552, 4),
        "aligned_w4_equals_1": (332, 243, 552, 4),
    }
    for chart, counts in expected.items():
        references = plan.build_chart_row_references(frozen_root, chart)
        assert references["source_row_count"] == 1127
        assert (
            references["dropped_zero_row_count"],
            references["dropped_duplicate_row_count"],
            references["unique_row_count"],
            references["component_count"],
        ) == counts
