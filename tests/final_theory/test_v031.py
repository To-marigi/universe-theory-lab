from pathlib import Path

from universe_lab.final_theory.v031 import (
    CERTIFICATE_PATHS,
    PROHIBITED_VERDICTS,
    REQUIRED_PROVENANCE_FIELDS,
    RESULT_NAMES,
    build_v0_3_1_payloads,
    verify_v0_3_1_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]


def test_v031_gate_statuses_and_claim_ceiling() -> None:
    payloads = build_v0_3_1_payloads(ROOT, code_commit="TEST_COMMIT")
    final = payloads["final_theory_bench_v0.3.1.json"]
    statuses = final["statuses"]

    assert statuses == {
        "ENGINEERING_STATUS": "ENGINEERING_PASS",
        "LITERATURE_FRONTIER_STATUS": "FRONTIER_CONFIRMED_OPEN",
        "COMMUTATIVE_REFERENCE_STATUS": "COMMUTATIVE_CSG_REFERENCE_PASS",
        "CPOBC_COMPILER_STATUS": "CPOBC_COMPILER_COMPLETE_N4",
        "CPOBC_D3_STATUS": "CPOBC_D3_SEARCH_INCONCLUSIVE",
        "CPOBC_D4_STATUS": "CPOBC_HIGHER_DIMENSION_NOT_EXECUTED",
        "NONCOMMUTATIVE_QSG_STATUS": "NOT_EXECUTED_NO_REPRESENTATION",
        "GEOMETRY_INTERFERENCE_STATUS": "NOT_ASSESSED_NO_REPRESENTATION",
        "EXTENSION_BOUNDARY_STATUS": "NONCOMMUTATIVE_EXTENSION_NOT_ASSESSED",
        "SCIENTIFIC_STATUS": "FINAL_THEORY_OPEN",
    }
    assert not set(PROHIBITED_VERDICTS) & set(final["allowed_claims"])


def test_v031_compiler_and_scoped_no_go_counts() -> None:
    payloads = build_v0_3_1_payloads(ROOT, code_commit="TEST_COMMIT")
    compiler = payloads["v0.3.1_cpobc_relations_n4.json"]
    search = payloads["v0.3.1_d3_representation_search.json"]

    assert compiler["counts"]["transition_orbits"] == 131
    assert compiler["counts"]["bell_pair_orbits"] == 373
    assert compiler["counts"]["bell_families"] == 146
    assert compiler["counts"]["compiled_cross_stage_relations"] == 641
    assert compiler["counts"]["d3_matrix_entry_polynomial_equations"] == 7047
    assert compiler["independent_brute_force_verification"]["exact_match"]
    assert search["executed_ansatz"]["bounded_no_go"]["unit_ideal"]
    assert search["executed_ansatz"]["independent_coordinate_verification"][
        "eq145_matches_matrix_route"
    ]
    assert search["executed_ansatz"]["independent_coordinate_verification"][
        "commutator_matches_matrix_route"
    ]
    assert search["summary"]["compiled_relation_assignment_count"] == 0


def test_v031_all_in_memory_results_have_required_provenance() -> None:
    payloads = build_v0_3_1_payloads(ROOT, code_commit="TEST_COMMIT")

    assert set(payloads) == set(RESULT_NAMES)
    assert all(
        REQUIRED_PROVENANCE_FIELDS <= payload.keys()
        for payload in payloads.values()
    )
    assert {payload["source_commit"] for payload in payloads.values()} == {
        "3ccbc66cc2cf868bf2a33ab96d4dd46e729d5f09"
    }


def test_frozen_v031_artifacts_and_certificates_verify() -> None:
    result = verify_v0_3_1_artifacts(ROOT)

    assert len(result["artifact_hash_checks"]) == len(RESULT_NAMES)
    assert len(result["certificate_hash_checks"]) == len(CERTIFICATE_PATHS)
    assert result["passed"], result
