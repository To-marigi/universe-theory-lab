"""Focused exact tests for the source-native k=1 Eq. (120) certificate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory.eq120_source_provenance_v042 import (
    RESULT_PATH,
    SCHEMA,
    SOURCE_CPOBC_PATH,
    VERDICT,
    _select_raw_relations,
    compile_eq120_source_provenance_v042,
    semantic_digest,
    verify_eq120_source_provenance_v042,
)

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_RAW = {
    (2, 1): (
        "cpobc-relation-0b2bbe81c6394d603f63",
        "0b2bbe81c6394d603f638117ddf72f52e3e0d251b6adb9932b996e26eb7e7d71",
    ),
    (3, 1): (
        "cpobc-relation-49726b7f352ba79916e5",
        "49726b7f352ba79916e5ebc57fc7e05bd2f42ef43d4c9c57ed2733b613ee7469",
    ),
    (3, 2): (
        "cpobc-relation-6002781cceb198b6edfd",
        "6002781cceb198b6edfd06e63b9920798363076ce6d9ed50bfb886bbb16b6728",
    ),
    (4, 1): (
        "cpobc-relation-1d7b3a88785401c6531b",
        "1d7b3a88785401c6531b0b369736fedc3a128da982b8f32984b44ce58c7b90b5",
    ),
    (4, 2): (
        "cpobc-relation-01e29996483e2c4f342c",
        "01e29996483e2c4f342c5aceeec8212e1466f8481cd8f9dcd3fab3ed19a285fd",
    ),
    (4, 3): (
        "cpobc-relation-17e9d7ae74c8bed62194",
        "17e9d7ae74c8bed621949c5847f822ba987e510fc20a05e0638721020ea23f4a",
    ),
}

EXPECTED_Q_OCCURRENCES = {
    "Q_1": "cpobc-transition-7137acaa934673cc789d",
    "Q_2": "cpobc-transition-3b93b9f523031a23c77f",
    "Q_3": "cpobc-transition-779d09aa463a38abdba6",
    "Q_4": "cpobc-transition-9fabc20614d5b2aa595d",
}

EXPECTED_PAIR_RELATIONS = {
    (2, 3): [
        "cpobc-relation-6002781cceb198b6edfd",
        "cpobc-relation-0b2bbe81c6394d603f63",
        "cpobc-relation-49726b7f352ba79916e5",
    ],
    (2, 4): [
        "cpobc-relation-01e29996483e2c4f342c",
        "cpobc-relation-0b2bbe81c6394d603f63",
        "cpobc-relation-1d7b3a88785401c6531b",
    ],
    (3, 4): [
        "cpobc-relation-17e9d7ae74c8bed62194",
        "cpobc-relation-49726b7f352ba79916e5",
        "cpobc-relation-1d7b3a88785401c6531b",
    ],
}


def _load(relative_path: str) -> dict[str, Any]:
    payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_compiler_reproduces_the_frozen_certificate_byte_semantics() -> None:
    frozen = _load(RESULT_PATH)
    compiled = compile_eq120_source_provenance_v042(ROOT)
    assert compiled == frozen
    assert frozen["schema_version"] == SCHEMA
    assert frozen["verdict"] == VERDICT
    assert frozen["passed"] is True
    assert frozen["semantic_digest_sha256"] == semantic_digest(frozen)
    assert verify_eq120_source_provenance_v042(ROOT, frozen)


def test_raw_antichain_singleton_empty_instances_are_unique_and_exact() -> None:
    source = _load(SOURCE_CPOBC_PATH)
    selected = _select_raw_relations(source)
    assert set(selected) == set(EXPECTED_RAW)
    assert {
        key: (record["relation_id"], record["relation_hash"]) for key, record in selected.items()
    } == EXPECTED_RAW


def test_q_bindings_use_only_gregarious_definition_records() -> None:
    payload = compile_eq120_source_provenance_v042(ROOT)
    observed = {
        item["semantic_name"]: item["occurrence_id"]
        for item in payload["q_occurrence_identification"]
    }
    assert observed == EXPECTED_Q_OCCURRENCES
    assert all(
        item["identifier_rule"] == "definition of the source-causet gregarious transition"
        and item["used_as_identifier_only"] is True
        for item in payload["q_occurrence_identification"]
    )


def test_three_pair_derivations_end_in_exact_k1_eq120_words() -> None:
    payload = compile_eq120_source_provenance_v042(ROOT)
    pairs = {tuple(item["indices"]): item for item in payload["pair_certificates"]}
    assert set(pairs) == set(EXPECTED_PAIR_RELATIONS)
    for (m, n), relation_ids in EXPECTED_PAIR_RELATIONS.items():
        record = pairs[(m, n)]
        assert record["source_relation_ids"] == relation_ids
        assert record["target_residual"] == [
            {"coefficient": 1, "word": [f"Q_{n}", "Q_1^-1", f"Q_{m}"]},
            {"coefficient": -1, "word": [f"Q_{m}", "Q_1^-1", f"Q_{n}"]},
        ]
        assert record["verified"] is True


def test_dependency_closure_excludes_b_reduction_and_strong_semantics() -> None:
    payload = compile_eq120_source_provenance_v042(ROOT)
    closure = payload["dependency_closure"]
    assert closure["B_reduced_expressions_used"] is False
    assert closure["MSR_used"] is False
    assert closure["GC_used"] is False
    assert closure["Eq108_used"] is False
    assert closure["Eq112_used"] is False
    assert closure["dependency_closed"] is True
    assert payload["chart_cover_gate"]["partial_slice_955"] == (
        "CLOSED_SOURCE_NATIVE_EQ120_PREMISES"
    )
    assert payload["chart_cover_gate"]["selected_700_direct_ideal_membership_claimed"] is False


def test_selected_700_binding_is_exact_but_not_misreported_as_ideal_membership() -> None:
    payload = compile_eq120_source_provenance_v042(ROOT)
    selected = payload["selected_700_relation_ids"]
    assert selected == {
        "branch": "LITERAL_PRINTED_QN_PLUS_1_BRANCH",
        "family": "CPOBC",
        "count": 700,
        "ordered_ids_sha256": ("cef66f304c7aff361bd92b44eba9a453a01331566d1becf0e73b1cf5895d2431"),
    }
    assert len(payload["selected_700_pair_bindings"]) == 3
    assert all(
        item["direct_expression_used_as_source_proof"] is False
        for item in payload["selected_700_pair_bindings"]
    )


def test_missing_raw_relation_and_tampered_certificate_fail_closed() -> None:
    source = _load(SOURCE_CPOBC_PATH)
    missing_id = EXPECTED_RAW[(4, 3)][0]
    source["relations"] = [
        record for record in source["relations"] if record["relation_id"] != missing_id
    ]
    with pytest.raises(AssertionError, match="inventory changed"):
        _select_raw_relations(source)

    certificate = _load(RESULT_PATH)
    certificate["pair_certificates"][0]["verified"] = False
    assert not verify_eq120_source_provenance_v042(ROOT, certificate)
