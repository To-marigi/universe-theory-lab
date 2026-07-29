from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
)
from universe_lab.final_theory.d2_sage_backend_v035 import (
    build_chart_payload,
)
from universe_lab.final_theory.d2_solver_v034 import cas_inventory
from universe_lab.final_theory.d2_strata_v034 import (
    S1,
    S2,
    stratum_charts,
)

ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_chart_cover_has_all_49_s1_s2_charts() -> None:
    charts = [
        chart
        for branch in (DERIVED_BRANCH, LITERAL_BRANCH)
        for chart in stratum_charts(branch)
        if chart.stratum in {S1, S2}
    ]
    assert len(charts) == 49
    assert sum(chart.stratum == S1 for chart in charts) == 28
    assert sum(chart.stratum == S2 for chart in charts) == 21


def test_full_payload_requests_real_sage_operations() -> None:
    chart = stratum_charts(DERIVED_BRANCH)[0]
    payload = build_chart_payload(
        DERIVED_BRANCH,
        chart.chart_id,
        operation="solve",
        maximum_source_stage=4,
        saturation=True,
        check_noncommutativity=True,
    )
    assert payload["expression_source"] == "direct_operator"
    assert payload["saturation"]
    assert payload["check_noncommutativity"]
    assert payload["include_all_transition_predicates"]
    assert payload["groebner_algorithm"] == "libsingular:slimgb"


def test_cas_inventory_uses_embedded_singular_probe(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "compose.yaml").write_text("services: {}\n")

    def fake_run(command, **_kwargs):
        assert command[-2] == "-c"
        assert "singular.version()" in command[-1]
        return SimpleNamespace(
            returncode=0,
            stdout=(
                '{"sage":"SageMath version 10.9",'
                '"singular":"Singular version 4.4.1"}\n'
            ),
            stderr="",
        )

    monkeypatch.setattr(
        "universe_lab.final_theory.d2_solver_v034.subprocess.run",
        fake_run,
    )
    inventory = cas_inventory(tmp_path)
    assert inventory["sage"] == "SageMath version 10.9"
    assert inventory["singular"] == "Singular version 4.4.1"


def test_solver_input_integrity_and_direct_system_are_exact() -> None:
    integrity = _load("results/v0.3.5_solver_input_integrity.json")
    direct = _load(
        "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
    )
    assert integrity["passed"]
    assert all(integrity["equation_id_checks"].values())
    assert integrity["denominator_ids_match"]
    assert direct["passed"]
    assert direct["counts"]["relations"] == {
        DERIVED_BRANCH: 1001,
        LITERAL_BRANCH: 1001,
    }
    assert direct["counts"]["reconstructed_transition_predicates"] == 165
    for coverage in direct[
        "relation_to_scalar_equation_coverage"
    ].values():
        assert coverage["passed"]
        assert coverage["direct_matrix_relation_count"] == 1001
        assert (
            coverage[
                "relations_represented_in_nonzero_scalar_numerators"
            ]
            == 979
        )
        assert coverage["identically_zero_path_relation_count"] == 22
        assert coverage["frozen_canonical_scalar_numerator_count"] == 2564


def test_all_modular_and_exact_subset_runs_completed() -> None:
    campaign = _load("results/v0.3.5_stage3_subset_campaign.json")
    assert campaign["campaign_complete"]
    assert campaign["planned_run_count"] == 147
    assert campaign["completed_or_terminal_run_count"] == 147
    assert all(
        record["exit_status"] == "COMPLETED"
        for record in campaign["runs"]
    )
    assert {
        record["coefficient_field"] for record in campaign["runs"]
    } == {"GF(32003)", "GF(32009)", "QQ"}
    assert campaign["modular_scout_agreement"]
    assert not campaign["modular_scout_disagreements"]


def test_full_campaign_has_no_unresolved_chart() -> None:
    campaign = _load("results/v0.3.5_full_stage4_campaign.json")
    assert campaign["campaign_complete"]
    assert campaign["completed_or_terminal_run_count"] == campaign[
        "planned_run_count"
    ]
    assert all(
        record["final_resaturates_pre_stage4_factors"]
        for record in campaign["runs"]
    )
    assert all(
        record["final_saturation_trace_complete"]
        for record in campaign["runs"]
    )
    assert campaign["planned_run_count"] == 78
    assert campaign["modular_scout_agreement"]
    assert not campaign["modular_scout_disagreements"]
    assert not campaign["unresolved_charts"]
    assert set(campaign["chart_classifications"].values()) <= {
        "EXACT_EMPTY_BY_LOCALISED_STAGE3_SUBSYSTEM",
        "EXACT_STRUCTURALLY_COMMUTATIVE_CHART",
        "EXACT_EMPTY_CHART",
        "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART",
        "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES",
    }
    for record in campaign["runs"]:
        certificate = _load(record["certificate"])
        assert certificate["final_resaturates_pre_stage4_factors"]
        final_steps = [
            step
            for step in certificate["saturation_trace"]
            if step.get("phase") != "PRE_STAGE4_LOCALISATION"
        ]
        assert certificate["saturated_unit_ideal"] or len(
            final_steps
        ) == certificate["effective_saturation_factor_count"]


def test_independent_reverse_order_oracle_agrees() -> None:
    oracle = _load("results/v0.3.5_independent_oracle.json")
    assert oracle["passed"]
    assert oracle["agreement"]
    assert len(oracle["runs"]) == 2
    assert all(record["proof_eligible"] for record in oracle["runs"])
    assert all(record["saturated_unit_ideal"] for record in oracle["runs"])
    assert {
        record["groebner_algorithm"] for record in oracle["runs"]
    } == {"libsingular:std"}
    assert {
        record["saturation_factor_order"] for record in oracle["runs"]
    } == {"reverse"}


def test_explicit_rational_witness_checks_every_required_condition() -> None:
    witness = _load("results/v0.3.5_explicit_rational_witness.json")
    assert witness["passed"]
    assert (
        witness["verdict"]
        == "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
    )
    assert witness["coefficient_field"] == "QQ"
    assert witness["relation_check"]["count"] == 1001
    assert witness["relation_check"]["all_zero"]
    assert witness["canonical_scalar_numerator_check"]["count"] == 2564
    assert witness["canonical_scalar_numerator_check"]["all_zero"]
    assert witness["canonical_scalar_numerator_check"][
        "compact_arena_source_hash_matches"
    ]
    assert witness["transition_check"]["count"] == 165
    assert witness["transition_check"]["all_nonsingular"]
    assert witness["two_sided_inverse_check"]["count"] == 26
    assert witness["two_sided_inverse_check"]["all_passed"]
    assert witness["chart_localisation_check"]["all_conditions_passed"]
    assert witness["nonzero_commutator"]["nonzero"]
    assert witness["not_pauli_ansatz"]
    assert witness["similarity_audit"][
        "not_a_commutative_similarity_duplicate"
    ]
    independent_witnesses = [
        _load("results/v0.3.5_explicit_rational_witness.json"),
        _load("results/v0.3.5_explicit_rational_witness_upper.json"),
        _load("results/v0.3.5_explicit_rational_witness_lower.json"),
    ]
    assert len({record["chart"] for record in independent_witnesses}) == 3
    assert all(record["passed"] for record in independent_witnesses)
    assert all(
        record["relation_check"]["count"] == 1001
        and record["relation_check"]["all_zero"]
        and record["canonical_scalar_numerator_check"]["count"] == 2564
        and record["canonical_scalar_numerator_check"]["all_zero"]
        and record["transition_check"]["count"] == 165
        and record["transition_check"]["all_nonsingular"]
        and record["two_sided_inverse_check"]["count"] == 26
        and record["two_sided_inverse_check"]["all_passed"]
        and record["nonzero_commutator"]["nonzero"]
        for record in independent_witnesses
    )


def test_classification_keeps_global_claim_open() -> None:
    result = _load("results/v0.3.5_d2_classification.json")
    assert result["semantic_profile"] == "PAPER_STRONG_OPERATOR_PROFILE"
    assert result["finite_scope"] == "n<=4"
    assert result["global_scientific_verdict"] == "FINAL_THEORY_OPEN"
    assert (
        result["verdict"]
        == "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
    )
    assert result["explicit_rational_witness"]["passed"]
    assert len(result["independent_explicit_witnesses"]) == 3
    assert all(
        witness["passed"]
        for witness in result["independent_explicit_witnesses"]
    )
    assert _load("results/v0.3.5_S1_saturated.json")["verdict"] == (
        "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
    )
    assert _load("results/v0.3.5_S2_saturated.json")["verdict"] == (
        "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
    )
    assert result["source_branch_verdicts"] == {
        DERIVED_BRANCH: "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4",
        LITERAL_BRANCH: (
            "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
        ),
    }
