from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from universe_lab.artifact_migration_v038 import (
    LegacyRawDigestResolver,
    load_line_ending_bridge,
)
from universe_lab.final_theory import q5_free_elimination_v037 as phase1_module
from universe_lab.final_theory import scalar_chain_v037 as phase2_module
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_sage_backend_v035 import (
    _request_semantic_digest,
)
from universe_lab.final_theory.q5_free_elimination_v037 import (
    load_human_budget_v037,
)
from universe_lab.final_theory.scalar_chain_v037 import (
    CANONICAL_ROUTE,
    DIRECT_ROUTE,
    LEMMA,
    SCHEMA_RESPONSE,
    _bound_terminal_result,
    _valid_direct_identity_result,
    build_scalar_chain_request_v037,
    verify_general_scalar_chain_lemma_v037,
)

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = load_line_ending_bridge(ROOT / "results/v0.3.8_line_ending_bridge.json")
LEGACY_DIGESTS = LegacyRawDigestResolver(ROOT, BRIDGE)


@pytest.fixture(autouse=True)
def _bridge_legacy_raw_hashes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(phase1_module, "_sha256", LEGACY_DIGESTS.sha256)
    monkeypatch.setattr(phase2_module, "_sha256", LEGACY_DIGESTS.sha256)


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha256(relative: str) -> str:
    return LEGACY_DIGESTS.sha256(ROOT / relative)


def test_scalar_chain_requests_have_exact_variable_inventories() -> None:
    budget = load_human_budget_v037(ROOT)
    literal_direct = build_scalar_chain_request_v037(
        ROOT,
        LITERAL_BRANCH,
        budget,
        expression_source=DIRECT_ROUTE,
    )
    literal_canonical = build_scalar_chain_request_v037(
        ROOT,
        LITERAL_BRANCH,
        budget,
        expression_source=CANONICAL_ROUTE,
    )
    derived_direct = build_scalar_chain_request_v037(
        ROOT,
        DERIVED_BRANCH,
        budget,
        expression_source=DIRECT_ROUTE,
    )
    derived_canonical = build_scalar_chain_request_v037(
        ROOT,
        DERIVED_BRANCH,
        budget,
        expression_source=CANONICAL_ROUTE,
    )
    assert literal_direct["variables"] == [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "l2",
        "l3",
        "l4",
    ]
    assert derived_direct["variables"] == [
        "a",
        "b",
        "c",
        "d",
        "l2",
        "l3",
        "l4",
    ]
    assert any(name.startswith("q5_") for name in literal_direct["q_substitutions"])
    assert not any(name.startswith("q5_") for name in derived_direct["q_substitutions"])
    for request in (literal_direct, derived_direct):
        assert request["coefficient_modulus"] == 0
        assert request["groebner_strategy"] == "none"
        assert request["expected_selected_relation_count"] == 1001
        assert request["expected_reconstructed_transition_count"] == 165
        assert request["expected_direct_system_file_sha256"] == _sha256(
            "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
        )
        assert request["expected_direct_system_semantic_digest_sha256"]
        assert request["selection_label"] == "ALL_1001_DIRECT_MATRIX_RELATIONS_ACTUAL"
        assert "expected_selected_canonical_equation_count" not in request
        assert "expected_frozen_denominator_factor_count" not in request
    for request in (literal_canonical, derived_canonical):
        assert request["coefficient_modulus"] == 0
        assert request["groebner_strategy"] == "none"
        assert request["expected_selected_relation_count"] == 979
        assert request["expected_selected_canonical_equation_count"] == 2564
        assert request["expected_frozen_denominator_factor_count"] == 191
        assert request["selection_label"] == "ALL_2564_CANONICAL_NUMERATORS_ACTUAL"
    for request in (
        literal_direct,
        literal_canonical,
        derived_direct,
        derived_canonical,
    ):
        assert request["request_semantic_digest_sha256"] == (_request_semantic_digest(request))


def test_general_scalar_chain_lemma_is_exact_on_recorded_open_locus() -> None:
    result = _load("results/v0.3.7_general_scalar_chain_fiber.json")
    assert result["passed"]
    assert result["verdict"] == LEMMA
    assert result["field"] == "QQ fraction field; characteristic zero"
    assert result["global_scientific_verdict"] == "FINAL_THEORY_OPEN"
    assert not result["unresolved_components"]
    assert "open locus" in result["claim_boundary"]
    assert "No assertion is made on excluded denominator loci" in (result["claim_boundary"])

    literal = result["exact_runs"][LITERAL_BRANCH]
    derived = result["exact_runs"][DERIVED_BRANCH]
    assert literal["passed"] and derived["passed"]
    literal_direct = literal["direct_relation_evaluation"]
    literal_coverage = literal["coverage_certificate"]
    derived_direct = derived["direct_relation_evaluation"]
    derived_coverage = derived["coverage_certificate"]
    assert literal_direct["variable_count"] == 11
    assert derived_direct["variable_count"] == 7
    for record in (literal_direct, derived_direct):
        assert record["matrix_relation_count"] == 1001
        assert record["relations_evaluated_count"] == 1001
        assert record["nonzero_residual_count"] == 0
        assert record["reconstructed_transitions_checked"] == 165
        assert record["identity_proof_eligible"]
        assert not record["proof_eligible"]
        assert record["direct_system_file_sha256"] == _sha256(
            "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
        )
        assert record["direct_system_semantic_digest_sha256"]
        assert _sha256(record["path"]) == record["sha256"]
        assert record["factor_domain"]["all_source_factorisations_reconstructed_exactly"]
        assert not record["factor_domain"]["zero_required_factor"]
    for record in (literal_coverage, derived_coverage):
        assert record["passed"]
        assert record["direct_matrix_relation_count"] == 1001
        assert record["canonical_equation_count"] == 2564
        assert record["frozen_canonical_scalar_numerator_count"] == 2564
        assert record["provenance_entry_count"] == 3916
        assert record["represented_relation_count"] == 979
        assert record["identically_zero_path_relation_count"] == 22
        assert record["represented_relations_have_all_four_entries"]
        assert record["represented_relations_are_exact_complement_of_zero_paths"]
        assert record["zero_path_relations_are_exact_path_family"]
        assert record["all_provenance_v033_digests_cross_bound"]
        assert record["all_representative_expression_ids_are_provenance_originals"]
        assert record["direct_source_binding_valid"]
        assert record["system_schema_and_status_valid"]
        assert record["compact_arena_source_binding_valid"]
        assert record["compact_arena_counts_consistent"]
        assert record["compact_arena_target_indices_valid"]
        assert record["compact_arena_reference_complete"]
        assert not record["missing_compact_arena_expression_ids"]
        assert not record["provenance_errors"]
        assert _sha256(record["path"]) == record["sha256"]
        assert _sha256(record["system_path"]) == record["system_sha256"]
        assert _sha256(record["compact_arena_path"]) == record["compact_arena_sha256"]

    literal_domain = literal_direct["factor_domain"]
    derived_domain = derived_direct["factor_domain"]
    assert literal_domain["effective_irreducible_factor_count"] == 15
    assert derived_domain["effective_irreducible_factor_count"] == 14
    assert "f*g - e*h" in literal_domain["effective_irreducible_factors"]
    assert "f*g - e*h" not in derived_domain["effective_irreducible_factors"]
    assert result["literal_identity"]["all_1001_matrix_relations_directly_evaluated_and_zero"]
    assert result["literal_identity"][
        "all_2564_canonical_numerators_deduced_zero_from_direct_relations_and_coverage"
    ]
    assert (
        result["literal_identity"]["Q5_equality_constraints_after_scalar_chain_substitution"] == 0
    )
    assert result["literal_identity"]["distinct_proof_components"]
    assert not result["literal_identity"]["distinct_evaluation_routes"]
    assert not result["literal_identity"]["independent_implementation"]
    assert result["literal_identity"]["shared_backend_and_compiler_lineage"]
    assert result["derived_comparison"]["all_1001_matrix_relations_directly_evaluated_and_zero"]
    assert result["derived_comparison"][
        "all_2564_canonical_numerators_deduced_zero_from_direct_relations_and_coverage"
    ]
    assert not result["derived_comparison"]["noncommutative_solution_on_scalar_chain"]


def test_scalar_chain_validators_reject_residual_and_budget_mutations() -> None:
    aggregate = _load("results/v0.3.7_general_scalar_chain_fiber.json")
    budget = load_human_budget_v037(ROOT)
    direct_request = build_scalar_chain_request_v037(
        ROOT,
        LITERAL_BRANCH,
        budget,
        expression_source=DIRECT_ROUTE,
    )
    literal = aggregate["exact_runs"][LITERAL_BRANCH]
    direct = _load(literal["direct_relation_evaluation"]["path"])
    assert _valid_direct_identity_result(direct, direct_request)

    direct["nonzero_specialised_equation_count"] = 1
    assert not _valid_direct_identity_result(direct, direct_request)

    direct = _load(literal["direct_relation_evaluation"]["path"])
    direct["identity_proof_eligible"] = False
    assert not _valid_direct_identity_result(direct, direct_request)

    direct = _load(literal["direct_relation_evaluation"]["path"])
    direct["budget_file_sha256"] = "0" * 64
    assert not _valid_direct_identity_result(direct, direct_request)

    direct = _load(literal["direct_relation_evaluation"]["path"])
    direct["request_semantic_digest_sha256"] = "0" * 64
    assert not _valid_direct_identity_result(direct, direct_request)


def test_scalar_chain_strict_verifier_rebuilds_both_routes() -> None:
    verification = verify_general_scalar_chain_lemma_v037(ROOT)
    assert verification["passed"]
    assert verification["certificate_role_counts"] == {"PHASE2_QQ_DIRECT_IDENTITY_EXACT": 2}
    assert set(verification["branch_checks"]) == {
        LITERAL_BRANCH,
        DERIVED_BRANCH,
    }
    assert all(
        record["certificate_semantic_digest_recomputes"]
        and record["request_binding_and_identity_gate_pass"]
        and record["coverage_recomputes_exactly"]
        for record in verification["branch_checks"].values()
    )

    mutated = copy.deepcopy(_load("results/v0.3.7_general_scalar_chain_fiber.json"))
    mutated["literal_identity"]["distinct_evaluation_routes"] = True
    rejected = verify_general_scalar_chain_lemma_v037(
        ROOT,
        aggregate=mutated,
    )
    assert not rejected["passed"]
    assert not rejected["aggregate_checks"]["literal_direct_and_coverage_claims_exact"]

    mutated = copy.deepcopy(_load("results/v0.3.7_general_scalar_chain_fiber.json"))
    mutated["source_artifacts"]["results/v0.3.4_polynomial_systems.json"] = "0" * 64
    rejected = verify_general_scalar_chain_lemma_v037(
        ROOT,
        aggregate=mutated,
    )
    assert not rejected["passed"]
    assert not rejected["aggregate_checks"]["source_artifact_copies_match"]


def test_scalar_timeout_is_bound_and_not_silently_retried() -> None:
    budget = load_human_budget_v037(ROOT)
    request = build_scalar_chain_request_v037(
        ROOT,
        LITERAL_BRANCH,
        budget,
        expression_source=CANONICAL_ROUTE,
    )
    terminal = {
        "schema_version": SCHEMA_RESPONSE,
        "chart": request["chart"],
        "coefficient_field": "QQ",
        "budget_file_sha256": request["budget_file_sha256"],
        "request_semantic_digest_sha256": request["request_semantic_digest_sha256"],
        "exit_status": "TIMEOUT",
        "wall_time_seconds": request["authorised_timeout_seconds_per_run"],
        "proof_eligible": False,
    }
    assert _bound_terminal_result(terminal, request)
    terminal["request_semantic_digest_sha256"] = "0" * 64
    assert not _bound_terminal_result(terminal, request)
