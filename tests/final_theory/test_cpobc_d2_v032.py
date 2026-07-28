from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from universe_lab.final_theory.cpobc_d2_v032 import (
    FROZEN_D3_PATH,
    FROZEN_D3_SHA256,
    FROZEN_RELATIONS_PATH,
    FROZEN_RELATIONS_SHA256,
    VERDICT_FOUND,
    VERDICT_NO_GO,
    VERDICT_PARTIAL,
    classification_result_v032,
    d2_strata_manifest_v032,
    generator_reduction_v032,
    phase0_exact_audit_v032,
    timid_generator_expression,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def reduction() -> dict[str, object]:
    return generator_reduction_v032()


def test_phase0_rechecks_frozen_inputs_pdf_and_exact_f4() -> None:
    audit = phase0_exact_audit_v032(ROOT)

    assert audit["passed"]
    assert audit["paper"]["hash_match"]
    assert audit["pdf_visual_verification"]["inspection_status"] == (
        "VISUALLY_CONFIRMED_THIS_RELEASE"
    )
    equations = audit["pdf_visual_verification"]["equations"]
    assert equations["107"]["pdf_page"] == 27
    assert equations["120"]["pdf_page"] == 28
    assert equations["129"]["pdf_page"] == 29
    assert equations["130"]["pdf_page"] == 29
    assert equations["165"]["pdf_page"] == 35

    assert audit["F1_counts"]["exact_match"]
    assert audit["F1_counts"]["observed"] == {
        "compiled_cross_stage_relations": 641,
        "denominator_cleared_word_equations": 783,
        "transition_occurrence_variables": 165,
        "MSR_operator_constraints": 24,
        "bell_families": 146,
        "transition_orbits": 131,
    }
    assert audit["F4_R_commutation"]["verified"]
    assert audit["F4_R_commutation"]["certificate_residual"] == [
        ["0", "0"],
        ["0", "0"],
    ]
    monomial = audit["F4_monomial_family"]
    assert monomial["eq120"] == {
        "admissible_index_count": 8,
        "all_residuals_zero": True,
    }
    assert monomial["eq129"] == {
        "admissible_index_count": 24,
        "all_residuals_zero": True,
    }
    assert monomial["eq130"]["all_residuals_zero"]
    assert monomial["full_641_relation_status"] == ("UNASSESSED_NOT_A_REPRESENTATION")

    restriction = audit["restriction_lemma"]
    assert restriction["mechanical_checks"]["all_compiled_relation_stages_at_most_4"]
    assert restriction["mechanical_checks"]["compiled_relation_count"] == 641
    assert restriction["mechanical_checks"]["MSR_source_count"] == 24
    assert restriction["no_go_lifting_status"].startswith("NOT_AVAILABLE")


def test_eq108_timid_reduction_preserves_noncommutative_word_order() -> None:
    # The one-element causet has one maximal element and G_empty=I, so Eq.
    # (108) reduces to the familiar exact expression I-Q_1.
    assert timid_generator_expression((0,)) == {(): 1, ("Q_1",): -1}

    # For the two-element antichain, the lower-stage conjugation words remain
    # ordered; they must never be commuted or cyclically normalised.
    expression = timid_generator_expression((0, 0))
    assert expression[()] == 1
    assert ("Q_2",) in expression
    assert any(word == ("Q_1", "Q_2", "Q_1^-1") for word in expression)


def test_phase1_maps_all_occurrences_and_rewrites_every_constraint(
    reduction: dict[str, object],
) -> None:
    assert reduction["passed"]
    counts = reduction["counts"]
    assert isinstance(counts, dict)
    assert counts == {
        "occurrence_variables": 165,
        "transition_kind_counts": {
            "GREGARIOUS": 24,
            "NON_TIMID": 117,
            "TIMID": 24,
        },
        "independent_matrix_generators_after_eq107_eq108": 24,
        "antichain_Q_generators": 4,
        "eq112_unreduced_gregarious_generators": 20,
        "d2_scalar_unknowns_before_inverse_saturation_and_gauge": 96,
        "rewritten_word_equations": 783,
        "Bell_free_word_identities_after_reduction": 83,
        "Bell_residual_constraints_after_reduction": 700,
        "rewritten_MSR_constraints": 24,
        "MSR_free_word_identities_after_reduction": 3,
        "MSR_residual_constraints_after_reduction": 21,
    }

    mapping = reduction["reduction_map"]
    assert isinstance(mapping, list)
    assert len(mapping) == 165
    assert len({item["occurrence_id"] for item in mapping}) == 165
    assert all(item["reduced_expression"] for item in mapping)
    assert all(item["exact"] for item in mapping)
    assert reduction["still_unreduced_occurrences"] == []
    assert len(reduction["still_unreduced_generators"]) == 20

    rewritten = reduction["rewritten_relation_inventory"]
    assert isinstance(rewritten, list)
    assert len(rewritten) == 783
    assert all(len(item["reduced_residual_sha256"]) == 64 for item in rewritten)

    rewritten_msr = reduction["rewritten_MSR_inventory"]
    assert isinstance(rewritten_msr, list)
    assert len(rewritten_msr) == 24
    assert all(not item["missing_occurrences"] for item in rewritten_msr)
    assert sum(item["identity_after_reduction"] for item in rewritten_msr) == 3
    assert any(item["reduced_residual"] for item in rewritten_msr)

    obligations = reduction["equivalence_obligations"]
    assert obligations["all_occurrences_mapped"]
    assert obligations["all_denominator_cleared_relations_rewritten"]
    assert obligations["all_MSR_constraints_rewritten"]
    assert not obligations["all_MSR_constraints_reduce_to_word_identities"]
    assert obligations["full_equivalence_status"].endswith("EQ112_ATOMISATION_AND_GC_UNPROVED")
    gate = reduction["phase3_strategy_gate"]
    assert gate["threshold_exceeded"]
    assert gate["observed_d2_scalar_unknowns"] == 96
    assert reduction["verdict"] == VERDICT_PARTIAL


def test_phase2_s1_s2_s3_cover_is_exact_but_not_eliminated() -> None:
    manifest = d2_strata_manifest_v032()

    assert manifest["coverage"] == {
        "declared_strata": 3,
        "exhaustiveness_lemma_passed": True,
        "fully_eliminated_strata": 0,
        "representation_witness_strata": 0,
    }
    assert manifest["exhaustiveness_proof"]["strata_are_exhaustive"]
    assert manifest["exhaustiveness_proof"]["strata_are_disjoint_by_predicate"]
    strata = manifest["strata"]
    assert [item["stratum"] for item in strata] == [
        "S1_DISTINCT_EIGENVALUE",
        "S2_COMMON_NILPOTENT",
        "S3_SCALAR",
    ]
    assert all(
        item["elimination_status"] == "NOT_EXECUTED_PHASE1_EQ112_GC_BLOCKED" for item in strata
    )
    assert "diagonal torus" in strata[0]["residual_gauge_group"]
    assert "stabilizer" in strata[1]["residual_gauge_group"]
    assert strata[2]["residual_gauge_group"] == "GL(2)"
    assert strata[2]["antichain_commutators_zero"]
    assert strata[2]["semantic_descriptor_sha256"] == (
        "e8fc9944d049b0544a5e938e489033511db3f8925ce9fff975668077aa7013c2"
    )
    assert strata[2]["full_transition_commutativity"].startswith("UNRESOLVED")
    assert manifest["verdict"] == VERDICT_PARTIAL


def test_phase4_uses_partial_token_and_never_rounds_up(
    reduction: dict[str, object],
) -> None:
    result = classification_result_v032(ROOT, reduction=reduction)

    assert result["passed"]
    assert result["verdict"] == VERDICT_PARTIAL
    requirements = result["verdict_requirements"]
    assert set(requirements) == {
        VERDICT_FOUND,
        VERDICT_NO_GO,
        VERDICT_PARTIAL,
    }
    assert not all(requirements[VERDICT_FOUND].values())
    assert not all(requirements[VERDICT_NO_GO].values())
    assert requirements[VERDICT_PARTIAL]["triggered"]
    assert result["unresolved_components"]
    assert result["phase3_elimination"]["groebner_or_primary_decomposition_runs"] == 0
    assert all(
        not item["solution_found"] and not item["no_go_certificate"]
        for item in result["phase3_elimination"]["strata"]
    )
    oracle = result["independent_oracle_gate"]
    assert oracle["limited_digest_match"]
    assert oracle["G1_status"].startswith("PARTIAL_ONLY")
    assert result["frozen_v031_d3"]["status"] == ("FROZEN_UNRESOLVED_NOT_MODIFIED")


def test_v031_frozen_artifacts_have_not_changed() -> None:
    assert hashlib.sha256((ROOT / FROZEN_RELATIONS_PATH).read_bytes()).hexdigest() == (
        FROZEN_RELATIONS_SHA256
    )
    assert hashlib.sha256((ROOT / FROZEN_D3_PATH).read_bytes()).hexdigest() == (FROZEN_D3_SHA256)


def test_checked_in_v032_artifacts_are_honest_and_hash_linked() -> None:
    result_dir = ROOT / "results"
    reduction = json.loads(
        (result_dir / "v0.3.2_cpobc_generator_reduction.json").read_text(encoding="utf-8")
    )
    classification = json.loads(
        (result_dir / "v0.3.2_cpobc_d2_classification.json").read_text(encoding="utf-8")
    )
    assert reduction["verdict"] == VERDICT_PARTIAL
    assert classification["verdict"] == VERDICT_PARTIAL
    assert reduction["unresolved_components"]
    assert classification["unresolved_components"]
    assert reduction["certificate_hashes"]
    assert classification["certificate_hashes"]
    for record in classification["certificate_hashes"]:
        certificate = ROOT / record["path"]
        assert certificate.is_file()
        assert hashlib.sha256(certificate.read_bytes()).hexdigest() == record["sha256"]

    assert (
        ROOT / "Final-Theory-Program" / "reports" / "v0.3.2_cpobc_d2_classification.md"
    ).is_file()
    assert (
        ROOT / "references" / "notes" / "final_theory_v0.3.2_d2_frontier_2026-07-28.md"
    ).is_file()
