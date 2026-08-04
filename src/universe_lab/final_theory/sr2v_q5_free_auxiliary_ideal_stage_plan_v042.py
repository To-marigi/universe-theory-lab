"""Pure-Python stage planning for the frozen SR2-V auxiliary ideals.

This module deliberately performs no file or CAS I/O.  Its arena-cache builder
accepts an already verified record iterator, binds the resulting lightweight
metadata to the frozen bundle root, and produces nested generator stages that a
separate Sage worker can materialise one at a time.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypedDict, cast

ARENA_CACHE_SCHEMA_VERSION = 1
STAGE_PLAN_SCHEMA_VERSION = 1
POLYNOMIAL_ARENA = "polynomial_arena"

NON_ALIGNED_CHARTS = ("U2", "U3", "U4")
ALIGNED_CHARTS = (
    "aligned_w2_equals_1",
    "aligned_w3_equals_1",
    "aligned_w4_equals_1",
)
ALL_CHARTS = (*NON_ALIGNED_CHARTS, *ALIGNED_CHARTS)
REQUIRED_ALIGNED_QUOTIENT_NAMES = ("d2", "d3", "d4")
DEFAULT_STAGE_SIZES: tuple[int | None, ...] = (16, 32, 64, 128, 256, None)

_HEX_DIGITS = frozenset("0123456789abcdef")


class ArenaMetadata(TypedDict):
    """The only arena information needed by the stage planner."""

    term_count: int
    sha256: str


def canonical_digest(value: Any) -> str:
    """Return the repository's canonical-JSON SHA-256 digest."""

    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _semantic_digest(value: Mapping[str, Any]) -> str:
    return canonical_digest(
        {key: item for key, item in value.items() if key != "semantic_digest_sha256"}
    )


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return cast(Mapping[str, Any], value)


def _as_sequence(value: Any, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be an array")
    return cast(Sequence[Any], value)


def _as_nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _as_positive_int(value: Any, label: str) -> int:
    result = _as_nonnegative_int(value, label)
    if result == 0:
        raise ValueError(f"{label} must be positive")
    return result


def _as_sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _validate_root(frozen_root: Mapping[str, Any]) -> dict[str, Any]:
    root_digest = _as_sha256(
        frozen_root.get("semantic_digest_sha256"),
        "root semantic_digest_sha256",
    )
    if _semantic_digest(frozen_root) != root_digest:
        raise ValueError("frozen root semantic digest mismatch")

    chunk_ledger = _as_mapping(frozen_root.get("chunk_ledger"), "root chunk_ledger")
    chunks = _as_sequence(chunk_ledger.get("chunks"), "root chunk_ledger.chunks")
    chunk_digest = _as_sha256(
        chunk_ledger.get("chunk_ledger_digest_sha256"),
        "root chunk ledger digest",
    )
    if canonical_digest(chunks) != chunk_digest:
        raise ValueError("frozen root chunk-ledger digest mismatch")

    arena_index = _as_mapping(frozen_root.get("arena_index"), "root arena_index")
    polynomial_index = _as_mapping(
        arena_index.get(POLYNOMIAL_ARENA),
        f"root arena_index.{POLYNOMIAL_ARENA}",
    )
    correspondence = _as_sequence(
        polynomial_index.get("polynomial_id_to_sha256"),
        "root polynomial id-to-digest index",
    )
    correspondence_digest = _as_sha256(
        polynomial_index.get("polynomial_id_to_sha256_digest_sha256"),
        "root polynomial id-to-digest index digest",
    )
    if canonical_digest(correspondence) != correspondence_digest:
        raise ValueError("frozen root polynomial id-to-digest index mismatch")

    expected: dict[int, str] = {}
    for position, raw_pair in enumerate(correspondence):
        pair = _as_sequence(raw_pair, f"root polynomial index entry {position}")
        if len(pair) != 2:
            raise ValueError(f"root polynomial index entry {position} must have two fields")
        identifier = _as_nonnegative_int(pair[0], f"root polynomial index id {position}")
        digest = _as_sha256(pair[1], f"root polynomial index digest {position}")
        if identifier in expected:
            raise ValueError(f"duplicate polynomial id in root index: {identifier}")
        expected[identifier] = digest
    if sorted(expected) != list(range(len(expected))):
        raise ValueError("root polynomial identifiers must be contiguous from zero")
    if expected.get(0) != canonical_digest([]):
        raise ValueError("root polynomial id zero must be the empty polynomial sentinel")

    record_count = _as_nonnegative_int(
        polynomial_index.get("record_count"),
        "root polynomial arena record_count",
    )
    if record_count != len(expected):
        raise ValueError("root polynomial arena record count mismatch")
    term_count_total = _as_nonnegative_int(
        polynomial_index.get("term_count_total"),
        "root polynomial arena term_count_total",
    )
    return {
        "root_digest": root_digest,
        "chunk_ledger_digest": chunk_digest,
        "arena_index_digest": correspondence_digest,
        "expected_polynomial_sha256": expected,
        "record_count": record_count,
        "term_count_total": term_count_total,
    }


def _cache_key(bindings: Mapping[str, Any]) -> str:
    return canonical_digest(
        {
            "arena": POLYNOMIAL_ARENA,
            "committed_root_semantic_digest_sha256": bindings["root_digest"],
            "committed_chunk_ledger_digest_sha256": bindings["chunk_ledger_digest"],
            "committed_arena_index_digest_sha256": bindings["arena_index_digest"],
        }
    )


def build_arena_metadata_cache(
    records: Iterable[Mapping[str, Any]],
    frozen_root: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a content-addressed metadata cache from an arena-record iterator.

    The function is pure: it neither opens the two-gigabyte arena nor writes the
    result.  The caller supplies records, normally from the bundle's checked
    chunk iterator.  Every record is independently checked against its terms and
    against the frozen root's complete polynomial-id index.
    """

    bindings = _validate_root(frozen_root)
    expected = cast(dict[int, str], bindings["expected_polynomial_sha256"])
    metadata: dict[int, ArenaMetadata] = {}
    term_count_total = 0

    for position, raw_record in enumerate(records):
        record = _as_mapping(raw_record, f"arena record {position}")
        identifier = _as_nonnegative_int(
            record.get("polynomial_id"),
            f"arena record {position} polynomial_id",
        )
        if identifier in metadata:
            raise ValueError(f"duplicate polynomial arena id: {identifier}")
        if identifier not in expected:
            raise ValueError(f"polynomial arena id absent from frozen root: {identifier}")

        terms = _as_sequence(record.get("terms"), f"arena record {identifier} terms")
        term_count = _as_nonnegative_int(
            record.get("term_count"),
            f"arena record {identifier} term_count",
        )
        if term_count != len(terms):
            raise ValueError(f"arena record {identifier} term count mismatch")
        digest = _as_sha256(record.get("sha256"), f"arena record {identifier} sha256")
        if canonical_digest(terms) != digest:
            raise ValueError(f"arena record {identifier} terms digest mismatch")
        if expected[identifier] != digest:
            raise ValueError(f"arena record {identifier} disagrees with frozen root")

        metadata[identifier] = {"term_count": term_count, "sha256": digest}
        term_count_total += term_count

    missing = sorted(set(expected) - set(metadata))
    if missing:
        raise ValueError(f"arena metadata cache is incomplete; first missing id: {missing[0]}")
    if len(metadata) != bindings["record_count"]:
        raise ValueError("arena metadata cache record count mismatch")
    if term_count_total != bindings["term_count_total"]:
        raise ValueError("arena metadata cache total term count mismatch")

    ordered_records = [
        [identifier, metadata[identifier]["term_count"], metadata[identifier]["sha256"]]
        for identifier in sorted(metadata)
    ]
    payload: dict[str, Any] = {
        "schema_version": ARENA_CACHE_SCHEMA_VERSION,
        "arena": POLYNOMIAL_ARENA,
        "committed_root_semantic_digest_sha256": bindings["root_digest"],
        "committed_chunk_ledger_digest_sha256": bindings["chunk_ledger_digest"],
        "committed_arena_index_digest_sha256": bindings["arena_index_digest"],
        "cache_key_sha256": _cache_key(bindings),
        "record_count": len(metadata),
        "term_count_total": term_count_total,
        "polynomial_metadata": {
            str(identifier): metadata[identifier] for identifier in sorted(metadata)
        },
        "polynomial_metadata_digest_sha256": canonical_digest(ordered_records),
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def validate_arena_metadata_cache(
    cache: Mapping[str, Any],
    frozen_root: Mapping[str, Any],
) -> dict[int, ArenaMetadata]:
    """Validate a cache envelope and return integer-keyed metadata."""

    bindings = _validate_root(frozen_root)
    expected_keys = {
        "schema_version",
        "arena",
        "committed_root_semantic_digest_sha256",
        "committed_chunk_ledger_digest_sha256",
        "committed_arena_index_digest_sha256",
        "cache_key_sha256",
        "record_count",
        "term_count_total",
        "polynomial_metadata",
        "polynomial_metadata_digest_sha256",
        "semantic_digest_sha256",
    }
    if set(cache) != expected_keys:
        raise ValueError("arena metadata cache has an unexpected schema")
    cache_schema = _as_nonnegative_int(cache.get("schema_version"), "cache schema_version")
    if cache_schema != ARENA_CACHE_SCHEMA_VERSION:
        raise ValueError("unsupported arena metadata cache schema")
    if cache.get("arena") != POLYNOMIAL_ARENA:
        raise ValueError("arena metadata cache names the wrong arena")

    binding_checks = {
        "committed_root_semantic_digest_sha256": bindings["root_digest"],
        "committed_chunk_ledger_digest_sha256": bindings["chunk_ledger_digest"],
        "committed_arena_index_digest_sha256": bindings["arena_index_digest"],
    }
    for field, expected_value in binding_checks.items():
        if cache.get(field) != expected_value:
            raise ValueError(f"arena metadata cache {field} mismatch")
    if cache.get("cache_key_sha256") != _cache_key(bindings):
        raise ValueError("arena metadata cache key mismatch")

    declared_semantic_digest = _as_sha256(
        cache.get("semantic_digest_sha256"),
        "arena metadata cache semantic digest",
    )
    if _semantic_digest(cache) != declared_semantic_digest:
        raise ValueError("arena metadata cache semantic digest mismatch")

    raw_metadata = _as_mapping(cache.get("polynomial_metadata"), "polynomial_metadata")
    expected = cast(dict[int, str], bindings["expected_polynomial_sha256"])
    metadata: dict[int, ArenaMetadata] = {}
    for raw_identifier, raw_entry in raw_metadata.items():
        if not isinstance(raw_identifier, str) or not raw_identifier.isdecimal():
            raise ValueError("polynomial metadata keys must be decimal identifiers")
        identifier = int(raw_identifier)
        entry = _as_mapping(raw_entry, f"polynomial metadata {identifier}")
        if set(entry) != {"term_count", "sha256"}:
            raise ValueError(f"polynomial metadata {identifier} has unexpected fields")
        if identifier in metadata:
            raise ValueError(f"duplicate polynomial metadata id: {identifier}")
        term_count = _as_nonnegative_int(
            entry.get("term_count"),
            f"polynomial metadata {identifier} term_count",
        )
        digest = _as_sha256(entry.get("sha256"), f"polynomial metadata {identifier} sha256")
        if expected.get(identifier) != digest:
            raise ValueError(f"polynomial metadata {identifier} disagrees with frozen root")
        metadata[identifier] = {"term_count": term_count, "sha256": digest}

    if set(metadata) != set(expected):
        raise ValueError("polynomial metadata identifiers do not cover the frozen arena")
    record_count = _as_nonnegative_int(cache.get("record_count"), "cache record_count")
    if record_count != len(metadata) or record_count != bindings["record_count"]:
        raise ValueError("arena metadata cache record count mismatch")
    term_count_total = sum(entry["term_count"] for entry in metadata.values())
    declared_term_count_total = _as_nonnegative_int(
        cache.get("term_count_total"),
        "cache term_count_total",
    )
    if (
        declared_term_count_total != term_count_total
        or term_count_total != bindings["term_count_total"]
    ):
        raise ValueError("arena metadata cache total term count mismatch")
    ordered_records = [
        [identifier, metadata[identifier]["term_count"], metadata[identifier]["sha256"]]
        for identifier in sorted(metadata)
    ]
    metadata_digest = _as_sha256(
        cache.get("polynomial_metadata_digest_sha256"),
        "polynomial metadata digest",
    )
    if canonical_digest(ordered_records) != metadata_digest:
        raise ValueError("polynomial metadata digest mismatch")
    return metadata


def _chart_entry(frozen_root: Mapping[str, Any], chart_name: str) -> Mapping[str, Any]:
    if chart_name not in ALL_CHARTS:
        raise ValueError(f"unknown chart: {chart_name}")
    chart_generator_ids = _as_mapping(
        frozen_root.get("chart_generator_ids"),
        "root chart_generator_ids",
    )
    charts = _as_mapping(chart_generator_ids.get("charts"), "root chart_generator_ids.charts")
    return _as_mapping(charts.get(chart_name), f"root chart {chart_name}")


def build_chart_row_references(
    frozen_root: Mapping[str, Any],
    chart_name: str,
) -> dict[str, Any]:
    """Drop zero/duplicate coefficient rows while retaining first provenance."""

    _validate_root(frozen_root)
    chart = _chart_entry(frozen_root, chart_name)
    raw_rows = _as_sequence(
        chart.get("generator_polynomial_ids"),
        f"chart {chart_name} generator_polynomial_ids",
    )
    declared_count = _as_nonnegative_int(
        chart.get("generator_count"),
        f"chart {chart_name} generator_count",
    )
    if declared_count != len(raw_rows):
        raise ValueError(f"chart {chart_name} generator count mismatch")

    if chart_name in NON_ALIGNED_CHARTS:
        component_count = 2
    else:
        key_order = _as_sequence(
            chart.get("generator_auxiliary_key_order"),
            f"chart {chart_name} generator_auxiliary_key_order",
        )
        component_count = len(key_order)
        if component_count == 0:
            raise ValueError(f"chart {chart_name} has no generator components")

    seen_rows: set[tuple[int, ...]] = set()
    seen_source_indices: set[int] = set()
    references: list[dict[str, Any]] = []
    dropped_zero = 0
    dropped_duplicate = 0
    for source_position, raw_row in enumerate(raw_rows):
        row = _as_sequence(raw_row, f"chart {chart_name} row {source_position}")
        if len(row) != component_count + 1:
            raise ValueError(f"chart {chart_name} row {source_position} has the wrong width")
        source_index = _as_nonnegative_int(
            row[0],
            f"chart {chart_name} row {source_position} source index",
        )
        if source_index in seen_source_indices:
            raise ValueError(f"chart {chart_name} repeats source index {source_index}")
        seen_source_indices.add(source_index)
        components = tuple(
            _as_nonnegative_int(
                value,
                f"chart {chart_name} row {source_position} component {component_position}",
            )
            for component_position, value in enumerate(row[1:])
        )
        if not any(components):
            dropped_zero += 1
            continue
        if components in seen_rows:
            dropped_duplicate += 1
            continue
        seen_rows.add(components)
        references.append(
            {
                "unique_row_index": len(references),
                "first_source_index": source_index,
                "source_position": source_position,
                "component_polynomial_ids": list(components),
            }
        )

    return {
        "source_row_count": len(raw_rows),
        "component_count": component_count,
        "dropped_zero_row_count": dropped_zero,
        "dropped_duplicate_row_count": dropped_duplicate,
        "unique_row_count": len(references),
        "rows": references,
    }


def _normalise_stage_sizes(stage_sizes: Sequence[int | None]) -> list[int | None]:
    if not stage_sizes:
        raise ValueError("at least one stage size is required")
    result: list[int | None] = []
    previous_size = -1
    full_stage_seen = False
    for position, value in enumerate(stage_sizes):
        if value is None:
            result.append(None)
            full_stage_seen = True
            continue
        size = _as_nonnegative_int(value, f"stage size {position}")
        if full_stage_seen or size < previous_size:
            raise ValueError("stage sizes must be non-decreasing, with None only at the end")
        result.append(size)
        previous_size = size
    return result


def _required_quotient_generators(
    chart_name: str,
    values: Mapping[str, int] | None,
    metadata: Mapping[int, ArenaMetadata],
) -> list[dict[str, Any]]:
    supplied = {} if values is None else dict(values)
    if chart_name in NON_ALIGNED_CHARTS:
        if supplied:
            raise ValueError("non-aligned charts cannot have aligned quotient generators")
        return []
    if set(supplied) != set(REQUIRED_ALIGNED_QUOTIENT_NAMES):
        raise ValueError("aligned charts require exactly the d2, d3 and d4 quotient generators")

    identifiers: list[int] = []
    result: list[dict[str, Any]] = []
    for name in REQUIRED_ALIGNED_QUOTIENT_NAMES:
        identifier = _as_positive_int(supplied[name], f"required quotient generator {name}")
        if identifier not in metadata:
            raise ValueError(f"required quotient generator {name} is absent from arena metadata")
        identifiers.append(identifier)
        result.append(
            {
                "name": name,
                "polynomial_id": identifier,
                "term_count": metadata[identifier]["term_count"],
                "sha256": metadata[identifier]["sha256"],
            }
        )
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("required aligned quotient generators must be distinct")
    return result


def build_stage_plan(
    frozen_root: Mapping[str, Any],
    chart_name: str,
    arena_metadata_cache: Mapping[str, Any],
    *,
    stage_sizes: Sequence[int | None] = DEFAULT_STAGE_SIZES,
    required_aligned_quotient_polynomial_ids: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Build nested, cost-ordered materialisation stages for one frozen chart."""

    bindings = _validate_root(frozen_root)
    metadata = validate_arena_metadata_cache(arena_metadata_cache, frozen_root)
    chart = _chart_entry(frozen_root, chart_name)
    row_selection = build_chart_row_references(frozen_root, chart_name)

    costed_rows: list[dict[str, Any]] = []
    for raw_reference in row_selection["rows"]:
        reference = _as_mapping(raw_reference, "row reference")
        component_ids = [int(value) for value in reference["component_polynomial_ids"]]
        missing = [
            identifier for identifier in component_ids if identifier and identifier not in metadata
        ]
        if missing:
            raise ValueError(
                f"chart {chart_name} references polynomial id absent from metadata: {missing[0]}"
            )
        cost = sum(metadata[identifier]["term_count"] for identifier in component_ids if identifier)
        costed_rows.append({**reference, "generator_cost_terms": cost})
    ordered_rows = sorted(
        costed_rows,
        key=lambda row: (
            row["generator_cost_terms"],
            row["first_source_index"],
            row["source_position"],
        ),
    )

    localization_id = _as_positive_int(
        chart.get("planned_Rabinowitsch_localization_polynomial_id"),
        f"chart {chart_name} planned Rabinowitsch localization id",
    )
    if localization_id not in metadata:
        raise ValueError("planned Rabinowitsch localization polynomial is absent from metadata")
    localization_generator = {
        "polynomial_id": localization_id,
        "term_count": metadata[localization_id]["term_count"],
        "sha256": metadata[localization_id]["sha256"],
    }
    quotient_generators = _required_quotient_generators(
        chart_name,
        required_aligned_quotient_polynomial_ids,
        metadata,
    )

    normalised_sizes = _normalise_stage_sizes(stage_sizes)
    stages: list[dict[str, Any]] = []
    previous_effective_size: int | None = None
    for target_size in normalised_sizes:
        effective_size = (
            len(ordered_rows) if target_size is None else min(target_size, len(ordered_rows))
        )
        if effective_size == previous_effective_size:
            continue
        selected = ordered_rows[:effective_size]
        needed_ids = {
            identifier
            for row in selected
            for identifier in row["component_polynomial_ids"]
            if identifier
        }
        needed_ids.add(localization_id)
        needed_ids.update(record["polynomial_id"] for record in quotient_generators)
        stages.append(
            {
                "stage_index": len(stages),
                "target_optional_row_count": target_size,
                "effective_optional_row_count": effective_size,
                "selected_unique_row_indices": [row["unique_row_index"] for row in selected],
                "selected_source_row_indices": [row["first_source_index"] for row in selected],
                "selected_row_cost_terms": sum(row["generator_cost_terms"] for row in selected),
                "selected_generator_count": effective_size + len(quotient_generators) + 1,
                "needed_polynomial_ids": sorted(needed_ids),
            }
        )
        previous_effective_size = effective_size

    row_selection_with_cost = {
        **row_selection,
        "rows": costed_rows,
        "cost_ordered_unique_row_indices": [row["unique_row_index"] for row in ordered_rows],
        "cost_ordered_source_row_indices": [row["first_source_index"] for row in ordered_rows],
    }
    payload: dict[str, Any] = {
        "schema_version": STAGE_PLAN_SCHEMA_VERSION,
        "chart": chart_name,
        "bindings": {
            "committed_root_semantic_digest_sha256": bindings["root_digest"],
            "committed_chunk_ledger_digest_sha256": bindings["chunk_ledger_digest"],
            "committed_arena_index_digest_sha256": bindings["arena_index_digest"],
            "arena_metadata_cache_semantic_digest_sha256": arena_metadata_cache[
                "semantic_digest_sha256"
            ],
            "chart_manifest_sha256": _as_sha256(
                chart.get("chart_manifest_sha256"),
                f"chart {chart_name} manifest digest",
            ),
            "generator_manifest_sha256": _as_sha256(
                chart.get("generator_manifest_sha256"),
                f"chart {chart_name} generator manifest digest",
            ),
        },
        "configured_stage_sizes": normalised_sizes,
        "row_selection": row_selection_with_cost,
        "fixed_generators": {
            "rabinowitsch_localization": localization_generator,
            "aligned_quotient_generators": quotient_generators,
        },
        "stages": stages,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def validate_stage_plan(
    plan: Mapping[str, Any],
    frozen_root: Mapping[str, Any],
    arena_metadata_cache: Mapping[str, Any],
) -> dict[str, Any]:
    """Detect plan mutation by digest check and deterministic reconstruction."""

    declared_digest = _as_sha256(
        plan.get("semantic_digest_sha256"),
        "stage plan semantic digest",
    )
    if _semantic_digest(plan) != declared_digest:
        raise ValueError("stage plan semantic digest mismatch")
    plan_schema = _as_nonnegative_int(plan.get("schema_version"), "stage plan schema_version")
    if plan_schema != STAGE_PLAN_SCHEMA_VERSION:
        raise ValueError("unsupported stage plan schema")

    chart_name = plan.get("chart")
    if not isinstance(chart_name, str):
        raise ValueError("stage plan chart must be a string")
    stage_sizes = _as_sequence(plan.get("configured_stage_sizes"), "configured_stage_sizes")
    fixed = _as_mapping(plan.get("fixed_generators"), "fixed_generators")
    quotient_records = _as_sequence(
        fixed.get("aligned_quotient_generators"),
        "aligned quotient generators",
    )
    quotient_ids: dict[str, int] = {}
    for position, raw_record in enumerate(quotient_records):
        record = _as_mapping(raw_record, f"aligned quotient generator {position}")
        name = record.get("name")
        if not isinstance(name, str):
            raise ValueError("aligned quotient generator name must be a string")
        quotient_ids[name] = _as_positive_int(
            record.get("polynomial_id"),
            f"aligned quotient generator {name} id",
        )

    rebuilt = build_stage_plan(
        frozen_root,
        chart_name,
        arena_metadata_cache,
        stage_sizes=cast(Sequence[int | None], stage_sizes),
        required_aligned_quotient_polynomial_ids=quotient_ids or None,
    )
    if dict(plan) != rebuilt:
        raise ValueError("stage plan does not match its frozen inputs")
    return rebuilt
