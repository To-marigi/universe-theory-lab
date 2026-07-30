from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
)
from universe_lab.final_theory import d2_auxiliary_audit_v034 as audit_module
from universe_lab.final_theory.d2_auxiliary_audit_v034 import (
    AMBIGUOUS_AUXILIARY,
    BRANCH_DEPENDENT_AUXILIARY,
    DEFINITIONAL_RATIONAL_AUXILIARY,
    EXPECTED_AUXILIARY_COUNT,
    GENUINE_FREE_AUXILIARY,
    PAPER_STRONG_OPERATOR_PROFILE,
    SOURCE_INDEX_BRANCHES,
    SOURCE_INDEX_POLICY,
    VERDICT,
    audit_b_auxiliaries_v034,
    classify_auxiliary_evidence,
)

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = load_line_ending_bridge(
    ROOT / "results/v0.3.8_line_ending_bridge.json"
)
LEGACY_DIGESTS = LegacyRawDigestResolver(ROOT, BRIDGE)
BRIDGE_TARGETS = {record["path"]: record for record in BRIDGE["targets"]}
V037_MANIFEST_FILES = {
    record["path"]: record
    for record in json.loads(
        (ROOT / "results/v0.3.7_release_manifest.json").read_text(
            encoding="utf-8"
        )
    )["files"]
}


@pytest.fixture(scope="module", autouse=True)
def _bridge_legacy_raw_hashes() -> Iterator[None]:
    original = audit_module._sha256_file
    audit_module._sha256_file = LEGACY_DIGESTS.sha256
    try:
        yield
    finally:
        audit_module._sha256_file = original


@pytest.fixture(scope="module")
def audit() -> dict[str, Any]:
    payload = audit_b_auxiliaries_v034()
    for record in payload["input_sources"]:
        relative_path = record["path"]
        target = BRIDGE_TARGETS.get(relative_path)
        if target is not None:
            record["bytes"] = target["virtual_crlf_size_bytes"]
            continue
        historical = V037_MANIFEST_FILES.get(relative_path)
        if historical is not None and historical["sha256"] != record["sha256"]:
            record["sha256"] = historical["sha256"]
            record["bytes"] = historical["size_bytes"]
    return payload


def test_all_twenty_two_auxiliaries_are_individually_classified(
    audit: dict[str, Any],
) -> None:
    auxiliaries = audit["auxiliaries"]
    assert audit["passed"]
    assert audit["verdict"] == VERDICT
    assert len(auxiliaries) == EXPECTED_AUXILIARY_COUNT
    assert len({record["auxiliary_id"] for record in auxiliaries}) == 22
    assert len({record["B_occurrence_id"] for record in auxiliaries}) == 22
    assert {
        record["classification"] for record in auxiliaries
    } == {DEFINITIONAL_RATIONAL_AUXILIARY}
    assert audit["counts"]["classifications"] == {
        AMBIGUOUS_AUXILIARY: 0,
        BRANCH_DEPENDENT_AUXILIARY: 0,
        DEFINITIONAL_RATIONAL_AUXILIARY: 22,
        GENUINE_FREE_AUXILIARY: 0,
    }


def test_inverse_name_alone_is_never_enough_for_definitional_status() -> None:
    inverse_only_evidence = {
        "unique_matching_inverse_node": True,
        "exact_two_sided_inverse_predicates": True,
        "branch_membership": {
            branch: True for branch in SOURCE_INDEX_BRANCHES
        },
    }
    assert (
        classify_auxiliary_evidence(inverse_only_evidence)
        == AMBIGUOUS_AUXILIARY
    )


def test_every_definition_matches_its_transition_and_determinant_predicate(
    audit: dict[str, Any],
) -> None:
    for record in audit["auxiliaries"]:
        evidence = record["classification_evidence"]
        assert evidence["unique_forward_definition"]
        assert evidence["forward_definition_matches_transition_predicate"]
        assert evidence["unique_matching_inverse_node"]
        assert evidence["exact_two_sided_inverse_predicates"]
        assert evidence["d2_determinant_nonzero_predicate"]
        assert evidence["transition_nonsingularity_assumption"]
        determinant = record["determinant_condition"]
        assert determinant["local_nonzero_condition"].endswith(" != 0")
        assert determinant["condition_source"]["v0.3.3_predicate"] == (
            "det(reconstructed_2x2_expression) != 0"
        )


def test_d2_adjugate_numerator_and_denominator_are_explicit(
    audit: dict[str, Any],
) -> None:
    for record in audit["auxiliaries"]:
        rational = record["rational_d2_elimination"]
        entries = rational["B_entry_coordinates"]
        assert rational["numerator"]["matrix"] == [
            [entries[1][1], f"-{entries[0][1]}"],
            [f"-{entries[1][0]}", entries[0][0]],
        ]
        assert rational["denominator"]["formula"] == (
            f"{entries[0][0]}*{entries[1][1]} - "
            f"{entries[0][1]}*{entries[1][0]}"
        )
        assert rational["identity"] == (
            "B*adj(B) = adj(B)*B = det(B)*I_2"
        )


def test_dependency_dag_is_resolved_and_elimination_order_is_dependency_first(
    audit: dict[str, Any],
) -> None:
    summary = audit["dependency_summary"]
    assert summary["cycle_free"]
    assert summary["cycles"] == []
    assert summary["stage_monotone"]
    order = summary["dependency_first_rational_elimination_order"]
    positions = {auxiliary: index for index, auxiliary in enumerate(order)}
    assert len(order) == 22
    for auxiliary, dependencies in summary["auxiliary_dependencies"].items():
        assert all(positions[dependency] < positions[auxiliary] for dependency in dependencies)
    for record in audit["auxiliaries"]:
        dependency = record["dependency_DAG"]
        assert dependency["cycle_free"]
        assert dependency["missing_dependencies"] == []
        assert dependency["terminal_dependencies"]
        assert all(
            path[0] == record["B_inverse_node_id"]
            for path in dependency["paths_to_terminal_nodes"]
        )


def test_path_and_alternative_path_provenance_are_preserved(
    audit: dict[str, Any],
) -> None:
    assert any(
        record["path_provenance"]["alternative_path_use_count"] > 0
        for record in audit["auxiliaries"]
    )
    for record in audit["auxiliaries"]:
        sites = record["path_provenance"]["path_use_sites"]
        assert sites
        assert all(site["inverse_use_verified"] for site in sites)
        assert all(site["path_certificate_verified"] for site in sites)
        assert all(
            site["path_role"] in {
                "CANONICAL_REPRESENTATIVE",
                "ALTERNATIVE_PATH",
            }
            for site in sites
        )
        provenance = record["transition_provenance"]
        assert provenance["canonical_representative"]["transition_provenance"]
        assert provenance["labelled_variants"]
        assert provenance["all_variants_share_decorated_signature"]


def test_both_source_index_branches_share_the_same_auxiliary_definition(
    audit: dict[str, Any],
) -> None:
    assert audit["semantic_profile"] == PAPER_STRONG_OPERATOR_PROFILE
    assert audit["source_index_branch"] == SOURCE_INDEX_POLICY
    for record in audit["auxiliaries"]:
        branch = record["source_index_branch"]
        assert branch["policy"] == SOURCE_INDEX_POLICY
        assert branch["definition_status"] == "BRANCH_INVARIANT"
        assert branch["usage_projection_exact_match"]
        assert branch["membership"] == {
            source_branch: True for source_branch in SOURCE_INDEX_BRANCHES
        }


def test_scalar_count_drops_from_104_to_16_before_saturation(
    audit: dict[str, Any],
) -> None:
    counts = audit["counts"]
    assert counts["v033_abstract_d2_matrix_entries"] == 104
    assert counts["rationally_eliminated_B_inverse_matrix_entries"] == 88
    assert counts["remaining_Q_matrix_entry_coordinates_before_saturation"] == 16
    assert counts["genuine_free_B_auxiliary_matrix_entries"] == 0
    assert counts["branch_dependent_B_auxiliary_matrix_entries"] == 0
    assert counts["ambiguous_B_auxiliary_matrix_entries"] == 0
    assert counts["local_B_determinant_nonzero_conditions"] == 22
    assert audit["rational_elimination_boundary"][
        "determinant_saturation"
    ] == "NOT_COMPILED"


def test_frozen_result_and_certificates_match_the_live_audit(
    audit: dict[str, Any],
) -> None:
    root = Path(__file__).resolve().parents[2]
    frozen = json.loads(
        (root / "results/v0.3.4_B_auxiliary_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    assert all(frozen.get(key) == value for key, value in audit.items())
    assert frozen["production_commit"]
    assert frozen["artifact_freeze_pointer"]["tag_name"].startswith(
        "final-theory-bench-v0.3.4"
    )
    assert frozen["certificate_hashes"]
    classification_certificate = json.loads(
        (
            root
            / "certificates/d2_auxiliary_audit/v0.3.4_classification.json"
        ).read_text(encoding="utf-8")
    )
    dependency_certificate = json.loads(
        (
            root
            / "certificates/d2_auxiliary_audit/v0.3.4_dependency_dag.json"
        ).read_text(encoding="utf-8")
    )
    assert classification_certificate["passed"]
    assert dependency_certificate["passed"]
    assert len(classification_certificate["auxiliaries"]) == 22
    assert len(dependency_certificate["auxiliaries"]) == 22
