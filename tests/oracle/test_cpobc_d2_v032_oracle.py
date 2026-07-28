from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

ORACLE_PATH = Path(__file__).resolve().parents[2] / "oracle" / "cpobc_d2_v032_oracle.py"
SPEC = importlib.util.spec_from_file_location(
    "cpobc_d2_v032_independent_oracle",
    ORACLE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def test_eq120_generic_identity_implies_commuting_r_family() -> None:
    certificate = oracle.eq120_to_commuting_r_certificate()

    assert certificate["identity_verified"]
    assert certificate["certificate_residual"] == [["0", "0"], ["0", "0"]]
    assert certificate["assumption"] == "det(Q_1) != 0"
    assert "does not derive Eq.(120)" in certificate["scope_boundary"]


def test_s1_s2_s3_partition_is_supported_by_symbolic_certificates() -> None:
    certificate = oracle.commuting_family_strata_certificate()

    assert certificate["all_symbolic_identities_verified"]
    assert certificate["certificate_kind"] == ("SYMBOLIC_IDENTITY_NOT_FINITE_SAMPLE")
    assert certificate["single_matrix_dichotomy"]["identity_verified"]

    s1 = certificate["S1_distinct_eigenvalue_pivot"]
    assert s1["membership_verified"]
    assert s1["centralizer_form_commutes"]
    assert s1["ideal_membership_residuals"] == {
        "off_diagonal_0_1": "0",
        "off_diagonal_1_0": "0",
    }

    s2 = certificate["S2_common_nilpotent_direction"]
    assert s2["reconstruction_verified"]
    assert s2["normal_form_commutes"]
    assert s2["normal_form_discriminant"] == "0"
    assert s2["jordan_basis_certificate"]["identity_verified"]
    assert s2["residual_gauge_group"]["determinant"] == "stabilizer_alpha**2"

    s3 = certificate["S3_all_scalar"]
    assert s3["centralizer_is_full_M2"]
    assert s3["residual_gauge_group"] == "GL(2)"

    valid_rows = [row for row in certificate["logical_partition"]["truth_table"] if row["valid"]]
    assert [row["stratum"] for row in valid_rows] == ["S1", "S2", "S3"]
    assert len(certificate["unproved_or_external_steps"]) == 3
    assert any("641-relation" in item for item in certificate["unproved_or_external_steps"])


def test_monomial_family_checks_every_admissible_index_residual_exactly() -> None:
    certificate = oracle.monomial_family_all_index_certificate()

    eq120 = certificate["equation_120"]
    assert eq120["expected_count"] == len(eq120["residuals"]) == 8
    assert [item["indices"] for item in eq120["residuals"]] == [
        [2, 1, 3],
        [2, 1, 4],
        [3, 1, 2],
        [3, 1, 4],
        [3, 2, 4],
        [4, 1, 2],
        [4, 1, 3],
        [4, 2, 3],
    ]
    assert eq120["all_zero"]

    eq129 = certificate["equation_129"]
    assert eq129["expected_count"] == len(eq129["residuals"]) == 24
    assert eq129["residuals"][0]["indices"] == [1, 2, 3, 4]
    assert eq129["residuals"][-1]["indices"] == [4, 3, 2, 1]
    assert len({tuple(item["indices"]) for item in eq129["residuals"]}) == 24
    assert all(len(set(item["indices"])) == 4 for item in eq129["residuals"])
    assert eq129["all_zero"]

    assert certificate["equation_130"]["all_zero"]
    assert certificate["all_index_residuals_zero"]
    assert all(item["verified"] for item in certificate["inverse_certificates"].values())


def test_monomial_certificate_keeps_exact_noncommutative_witnesses() -> None:
    certificate = oracle.monomial_family_all_index_certificate()
    witnesses = certificate["noncommutativity_witnesses"]

    assert witnesses["[Q_1,Q_2]"]["matrix"] == [
        ["q1*(a2 - b2)", "0"],
        ["0", "-q1*(a2 - b2)"],
    ]
    assert witnesses["[Q_2,Q_3]"]["matrix"] == [
        ["-a2*b3 + a3*b2", "0"],
        ["0", "a2*b3 - a3*b2"],
    ]
    assert certificate["certificate_kind"] == (
        "SYMBOLIC_RATIONAL_FUNCTION_IDENTITIES_NOT_PARAMETER_SAMPLES"
    )
    assert any(
        "not a CPOBC representation certificate" in boundary
        for boundary in certificate["scope_boundary"]
    )


def test_independent_s3_digest_is_canonical_and_explicitly_limited() -> None:
    certificate = oracle.independent_s3_digest_certificate()
    descriptor = oracle.s3_semantic_descriptor()

    assert certificate["semantic_descriptor"] == descriptor
    assert certificate["semantic_descriptor_sha256"] == (
        "e8fc9944d049b0544a5e938e489033511db3f8925ce9fff975668077aa7013c2"
    )
    assert certificate["semantic_descriptor_sha256"] == (oracle.stable_json_sha256(descriptor))
    assert descriptor == {
        "stratum": "S3_SCALAR",
        "substitution": {
            "Q_2": "lambda_2*Q_1",
            "Q_3": "lambda_3*Q_1",
            "Q_4": "lambda_4*Q_1",
        },
        "checked_claim": "ANTICHAIN_Q_COMMUTATORS_ZERO_ONLY",
        "commutator_pairs": [
            [1, 2],
            [1, 3],
            [1, 4],
            [2, 3],
            [2, 4],
            [3, 4],
        ],
        "full_transition_system_status": ("UNASSESSED_GENERATOR_REDUCTION_INCOMPLETE"),
    }
    assert certificate["all_checked_commutators_zero"]
    assert certificate["shared_production_code_paths"] == []
    assert certificate["g1_status"] == ("LIMITED_DIGEST_ROUTE_NOT_FULL_PHASE1_REPRODUCTION")
    assert "641 compiled CPOBC relations" in certificate["unresolved_components"]


def test_oracle_has_no_production_phase1_import_or_finite_sample_route() -> None:
    source = inspect.getsource(oracle)

    assert "from universe_lab.final_theory" not in source
    assert "import universe_lab.final_theory" not in source
    assert "random" not in source

    complete = oracle.build_oracle_certificate()
    assert complete["passed"]
    assert complete["implementation_role"] == ("INDEPENDENT_PHASE2_AND_LIMITED_G1_ORACLE")
    assert "does not imply existence or nonexistence" in complete["verdict_boundary"]
