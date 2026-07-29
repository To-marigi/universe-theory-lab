from __future__ import annotations

import hashlib
import json
from pathlib import Path

from universe_lab.final_theory.q5_closure_v036 import (
    compile_q5_closure_audit,
    compile_q5_constraint_census,
)
from universe_lab.final_theory.q5_vacuity_v036 import (
    LITERAL_VERDICT,
    VERDICT,
    compile_eq113_eq139_audit,
    compile_q5_vacuity_proof,
)

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_q5_census_is_exact_and_unambiguous() -> None:
    census = _load("results/v0.3.6_q5_constraint_census.json")
    counts = census["headline_counts"]
    assert census["passed"]
    assert census["verdict"] == "V036_Q5_CONSTRAINT_CENSUS_COMPLETE"
    assert counts == {
        "literal_matrix_relations_total": 1001,
        "literal_canonical_scalar_numerators_total": 2564,
        "relations_with_direct_Q5_token": 24,
        "relations_with_transitive_Q5_dependency": 24,
        "Q5_relations_identically_zero_after_exact_reduction": 21,
        "total_relations_constraining_Q5": 3,
        "canonical_scalar_numerators_constraining_Q5": 12,
    }
    assert census["single_reported_total_relations_constraining_Q5"] == 3
    assert len(
        census["Q5_relation_ids"]["nonzero_relations_constraining_Q5"]
    ) == 3
    assert len(census["Q5_scalar_numerator_equations"]) == 12


def test_all_twelve_compiled_q5_numerators_are_symbolic_identities() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    compiled = proof["phase_1_compiled_system_vacuity"]
    records = compiled["twelve_equation_records"]
    assert proof["passed"]
    assert proof["verdict"] == VERDICT
    assert len(records) == 12
    assert compiled["twelve_equations_identically_zero"]
    assert all(record["identically_zero"] for record in records)
    assert all(
        record[
            "after_Q1_through_Q4_witness_and_symbolic_Q5_substitution"
        ]
        == "0"
        for record in records
    )
    assert all(not record["remaining_free_symbols"] for record in records)
    assert not compiled["symbolic_substitution"]["unresolved_symbol_names"]


def test_exact_dependency_argument_closes_all_2564_equations() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    compiled = proof["phase_1_compiled_system_vacuity"]
    counts = compiled["frozen_literal_system"]
    background = compiled["remaining_2552_equations_argument"]
    assert counts["matrix_relation_count"] == 1001
    assert counts["canonical_scalar_numerator_count"] == 2564
    assert counts["Q5_dependent_canonical_scalar_numerator_count"] == 12
    assert counts["Q5_independent_canonical_scalar_numerator_count"] == 2552
    assert counts["frozen_denominator_factor_count"] == 191
    assert counts["Q5_dependent_frozen_denominator_factor_count"] == 0
    assert background["fixed_base_point_check"][
        "all_2564_zero_at_frozen_witness"
    ]
    assert not background["fixed_base_point_check"]["failed_equation_ids"]
    assert compiled["all_2564_equations_zero_for_symbolic_Q5"]


def test_q5_fiber_is_four_dimensional_and_generically_noncommutative() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    compiled = proof["phase_1_compiled_system_vacuity"]
    commutator = compiled["symbolic_commutator_Q1_Q5"]
    ambient = compiled["ambient_localisation_boundary"]
    assert commutator["matrix"] == [
        ["-b + c", "-a - b + d"],
        ["a + c - d", "b - c"],
    ]
    assert commutator["centralizer_dimension_in_A4"] == 2
    assert commutator["generic_Q5_noncommutative"]
    assert ambient["polynomial_equation_ideal_in_Q5_coordinates"] == (
        "zero ideal"
    )
    assert not ambient["Q5_dependent_frozen_denominator_factors"]
    assert ambient["affine_fiber_dimension"] == 4
    assert ambient["representation_domain"] == "GL(2), det(Q5)=a*d-b*c != 0"
    samples = compiled["independent_integer_Q5_samples"]
    assert len(samples) == 3
    assert all(record["invertible"] for record in samples)
    assert all(record["noncommutative"] for record in samples)
    assert all(
        record["all_twelve_compiled_Q5_equations_pass"]
        for record in samples
    )


def test_three_operator_words_are_identity_on_the_scalar_chain() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    structure = proof["phase_1_scalar_chain_structure"]
    records = structure["relation_records"]
    assert structure["passed"]
    assert len(records) == 3
    assert all(record["projection_is_identity"] for record in records)
    assert all(record["scalar_chain_projection"] == "1" for record in records)
    assert all(record["resulting_relation"] == "[I,Q5]=0" for record in records)
    charts = structure["S1_pivot_R5_chart_evidence"]
    assert charts["chart_count"] == 4
    assert charts["all_impose_R2_R3_R4_scalar"]
    assert len(charts["v0.3.5_surviving_pivot_R5_chart_ids"]) == 3
    assert structure["fiber"]["polynomial_coordinates"] == 4
    assert structure["fiber"]["localised_domain"] == "GL(2)"


def test_paper_eq120_eq130_and_eq139_are_symbolically_zero() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    checks = proof["phase_0_independent_rechecks"]["paper_relations"]
    assert checks["passed"]
    assert checks["Eq120"]["instance_count"] == 10
    assert checks["Eq120"]["Q5_instance_count"] == 6
    assert checks["Eq120"]["all_identically_zero"]
    assert checks["Eq130"]["identically_zero"]
    assert checks["Eq139"]["instance_count"] == 3
    assert checks["Eq139"]["all_identically_zero"]
    assert all(
        record["identically_zero"] for record in checks["Eq139"]["records"]
    )


def test_reconstructed_antichain_msr_is_a_binomial_identity() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    msr = proof["phase_0_independent_rechecks"][
        "antichain_MSR_identity"
    ]
    assert msr["passed"]
    assert msr["all_MSR_residuals_zero"]
    assert len(msr["MSR_residuals_n1_through_n5"]) == 5
    assert all(
        record["identically_zero"]
        for record in msr["MSR_residuals_n1_through_n5"]
    )
    invalid = msr["deliberately_CPOBC_invalid_invertible_sample"]
    assert invalid["Eq120_failure_count"] == 10


def test_eq113_and_eq139_are_separated_without_resolving_source_intent() -> None:
    audit = compile_eq113_eq139_audit(ROOT)
    assert audit["passed"]
    assert audit["verdict"] == (
        "EQ113_EQ139_SEPARATED_SOURCE_AMBIGUITY_RETAINED"
    )
    path = audit["project_EQ112_PATH_CONSISTENCY_audit"]
    assert path["direct_literal_family_count"] == 25
    assert path["implements_Eq139"] is False
    assert path["Eq113_Eq139_conflation_detected"] is False
    for branch in path["branch_summary"].values():
        assert branch["record_count"] == 25
        assert branch["all_have_commutator_word_shape"]
    eq139 = audit["project_Eq139_audit"]
    assert len(eq139["explicit_helper_call_sites"]) == 1
    assert eq139["explicit_helper_call_sites"][0]["caller"] == (
        "_scaled_heisenberg_ansatz"
    )
    assert eq139["frozen_d2_named_EQ139_relation_count"] == 0
    assert "NO_SEPARATELY_MATERIALISED" in eq139["n3_status"]
    assert "NO_SEPARATELY_MATERIALISED" in eq139["n4_status"]
    source = audit["source_classification"]
    assert source["printed_Eq113_typo_suggested"]
    assert not source["author_intent_confirmed"]
    assert source["classification"] == "SOURCE_AMBIGUITY"
    assert source["both_branches_retained"]


def test_invalid_closure_remains_rejected_but_is_no_longer_needed() -> None:
    census = _load("results/v0.3.6_q5_constraint_census.json")
    audit = compile_q5_closure_audit(ROOT, census)
    assert not audit["requested_generator_symmetric_closure_established"]
    assert not audit["adopted_subset_is_sufficient_for_requested_step_A"]
    assert not audit["safe_to_run_verdict_bearing_elimination"]
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    closure = proof["phase_0_independent_rechecks"]["closure_step_A"]
    assert closure["status"] == "NOT_RUN_INVALID_AND_UNNECESSARY"
    assert closure["invalid_generator_shift_rejected"]


def test_verdict_is_reconstructed_without_any_compute_backend() -> None:
    proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    verdict = proof["phase_2_verdict_reconstruction"]
    execution = proof["execution"]
    assert verdict["v0.3.6_literal_verdict"] == LITERAL_VERDICT
    assert verdict["substantive_finite_result"] == (
        "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4"
    )
    assert not verdict["paper_overturned"]
    assert execution["Sage_runs"] == 0
    assert execution["Singular_runs"] == 0
    assert execution["finite_field_scout_runs"] == 0
    assert execution["QQ_Groebner_runs"] == 0
    assert execution["stage5_compiler_runs"] == 0
    assert not execution["budget_file_required"]
    assert not execution["budget_file_created"]
    assert not execution["genuine_stage5_construction_attempted"]
    assert not (ROOT / "config/v0.3.6_budget.json").exists()
    assert not (
        ROOT / "results/v0.3.6_q5_closure_elimination.json"
    ).exists()
    assert proof["global_scientific_verdict"] == "FINAL_THEORY_OPEN"


def test_reports_and_addenda_apply_the_new_claim_ceiling() -> None:
    v036_paths = (
        "reports/v0.3.6_q5_vacuity.md",
        "reports/v0.3.6_eq113_eq139_separation.md",
        "reports/v0.3.6_scientific_verdict.md",
        "reports/v0.3.6_remaining_gaps.md",
    )
    for relative in v036_paths:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "FINAL_THEORY_OPEN" in text or "SOURCE_AMBIGUITY" in text
        assert "LITERAL_Q5_CLOSURE_PARTIAL" not in text
    scientific = (
        ROOT / "reports/v0.3.5_scientific_verdict.md"
    ).read_text(encoding="utf-8")
    gaps = (ROOT / "reports/v0.3.5_remaining_gaps.md").read_text(
        encoding="utf-8"
    )
    for text in (scientific, gaps):
        assert text.count(
            "## v0.3.6 addendum - Q5 vacuity correction"
        ) == 1
        assert LITERAL_VERDICT in text
        assert "FINAL_THEORY_OPEN" in text
        assert "LITERAL_Q5_CLOSURE_PARTIAL" not in text


def test_frozen_v034_v035_artifacts_are_unchanged() -> None:
    assert _sha256("results/v0.3.4_polynomial_systems.json") == (
        "018c1dccc4e08102c6de1fbdd9baf6e8e89dcf818e302ebb175e23e59f5a1283"
    )
    assert _sha256("results/v0.3.5_explicit_rational_witness.json") == (
        "755bbe3743ced5d6594671f45733f1004bc88de1916e7fbeb9454444bbf8c300"
    )
    assert _sha256("results/v0.3.5_d2_classification.json") == (
        "59abc7d234e6a814206c72beec851a7fc08c4082ce2452ed38f29b76a257c342"
    )
    assert _sha256(
        "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
    ) == "c19c00438f94c55fa3d5a7662cbb425a170f497d25698fa050d245b97714d837"


def test_live_rebuild_matches_frozen_semantic_digests() -> None:
    frozen_census = _load("results/v0.3.6_q5_constraint_census.json")
    rebuilt_census = compile_q5_constraint_census(ROOT)
    assert rebuilt_census["passed"]
    assert rebuilt_census["semantic_digest_sha256"] == (
        frozen_census["semantic_digest_sha256"]
    )
    frozen_proof = _load("results/v0.3.6_q5_vacuity_proof.json")
    rebuilt_proof = compile_q5_vacuity_proof(
        ROOT,
        census=rebuilt_census,
    )
    assert rebuilt_proof["passed"]
    assert rebuilt_proof["semantic_digest_sha256"] == (
        frozen_proof["semantic_digest_sha256"]
    )
