from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import sympy as sp

ROOT = Path(__file__).resolve().parents[2]
ORACLE_PATH = ROOT / "oracle" / "d2_rational_v034_oracle.py"
SCALAR_CERTIFICATE_PATH = (
    ROOT
    / "certificates"
    / "independent_oracle"
    / "v0.3.4_scalar_fixture.json"
)


def _load_oracle() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "d2_rational_v034_independent_oracle",
        ORACLE_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_rational_pair_inverse_uses_d_adjugate_over_det_n() -> None:
    oracle = _load_oracle()
    matrix = oracle.RationalMatrix2([[1, 2], [3, 5]], 7)
    inverse = matrix.inverse()

    assert inverse.numerator == sp.ImmutableMatrix(
        [[35, -14], [-21, 7]]
    )
    assert inverse.denominator == -1
    assert (matrix @ inverse - oracle.RationalMatrix2.identity()).is_zero()
    assert (inverse @ matrix - oracle.RationalMatrix2.identity()).is_zero()

    generic = oracle.rational_inverse_identity_certificate()
    assert generic["formula"] == "(N/d)^-1 = d*adj(N)/det(N)"
    assert generic["formula_pair_matches"]
    assert generic["left_inverse_verified"]
    assert generic["right_inverse_verified"]
    assert generic["certificate_kind"] == "GENERIC_SYMBOLIC_IDENTITY"


def test_three_generic_symbolic_charts_are_present_and_classified() -> None:
    oracle = _load_oracle()
    fixtures = oracle.build_fixture_certificates()

    assert [fixture["fixture_id"] for fixture in fixtures] == [
        "ORACLE_S1_FIXTURE_01",
        "ORACLE_S2_FIXTURE_01",
        "ORACLE_S3_FIXTURE_01",
    ]
    assert [fixture["stratum"] for fixture in fixtures] == [
        "S1_DISTINCT_EIGENVALUE",
        "S2_COMMON_NILPOTENT",
        "S3_SCALAR",
    ]
    assert all(
        fixture["chart_kind"]
        == "GENERIC_SYMBOLIC_COORDINATE_CHART_NOT_FINITE_SAMPLE"
        for fixture in fixtures
    )
    assert all(
        fixture["ratio_pairwise_commutators_zero"]
        for fixture in fixtures
    )
    assert fixtures[0]["classification_identity"]["discriminant"] != "0"
    assert fixtures[1]["classification_identity"]["discriminant"] == "0"
    assert fixtures[2]["classification_identity"]["normal_form"] == (
        "R_j=(l_j/d_j)*I"
    )


def test_selected_relations_are_exact_and_do_not_fake_chart_solutions() -> None:
    oracle = _load_oracle()
    fixtures = oracle.build_fixture_certificates()
    expected_ids = [
        "ORACLE_EQ120_K1_N2_M3",
        "ORACLE_EQ120_K2_N3_M4",
        "ORACLE_EQ129_M1_N2_L3_K4",
        "ORACLE_EQ130_Q1_Q2",
        "ORACLE_EQ113_QN_N4",
        "ORACLE_EQ113_LITERAL_QN_PLUS_1_N4",
    ]

    for fixture in fixtures:
        relations = fixture["selected_exact_relations"]
        assert [relation["relation_id"] for relation in relations] == (
            expected_ids
        )
        identity_map = fixture["selected_relation_identity_map"]
        assert identity_map["ORACLE_EQ120_K1_N2_M3"]
        assert identity_map["ORACLE_EQ120_K2_N3_M4"]
        assert identity_map["ORACLE_EQ129_M1_N2_L3_K4"]
        assert "not a full representation" in fixture[
            "chart_decision_boundary"
        ]

    assert not fixtures[0]["selected_relation_identity_map"][
        "ORACLE_EQ130_Q1_Q2"
    ]
    assert not fixtures[1]["selected_relation_identity_map"][
        "ORACLE_EQ130_Q1_Q2"
    ]
    assert fixtures[2]["selected_relation_identity_map"][
        "ORACLE_EQ130_Q1_Q2"
    ]


def test_eq113_qn_and_literal_qn_plus_1_branches_never_merge() -> None:
    oracle = _load_oracle()

    for fixture in oracle.build_fixture_certificates():
        branch = fixture["Eq113_branch_separation"]
        assert branch["branches"] == [
            "EQ113_QN_BRANCH",
            "EQ113_QN_PLUS_1_BRANCH",
        ]
        assert branch["QN_target"] == "Q_4"
        assert branch["literal_QN_plus_1_target"] == "Q_5"
        assert branch["branch_records_are_distinct"]
        assert branch["QN_residual_identically_zero"]
        assert not branch["literal_residual_identically_zero"]
        assert branch["source_index_status"] == (
            "UNRESOLVED_BRANCHES_NOT_MERGED"
        )
        assert fixture["Q_5_scope"] == (
            "OUTSIDE_N_LE_4_Q_INVENTORY_LITERAL_BRANCH_ONLY"
        )
        assert fixture["path_holonomy_fixture"]["status"] == (
            "SYNTHETIC_BRANCH_DISCRIMINATOR_NOT_AN_ATOMISATION_PATH_DERIVATION"
        )


def test_exact_scalar_fixture_rechecks_every_frozen_inventory() -> None:
    oracle = _load_oracle()
    certificate = oracle.scalar_fixture_certificate(ROOT)

    assert certificate["passed"]
    assert certificate["verdict"] == "INDEPENDENT_ORACLE_PARTIAL"
    assert certificate["matrix_interpretation"] == (
        "each scalar s denotes s*I_2"
    )
    assert certificate["Q_assignment"] == {
        "shared_n_le_4": {
            "Q_1": "2",
            "Q_2": "3",
            "Q_3": "5",
            "Q_4": "7",
        },
        "literal_branch_only": {"Q_5": "11"},
    }
    assert all(certificate["schema_checks"].values())

    transitions = certificate["transition_reconstructions"]
    assert transitions["count"] == transitions["nonzero_count"] == 165
    assert transitions["zero_count"] == 0

    cpobc = certificate["original_CPOBC_word_equations"]
    assert cpobc["compiled_relation_record_count"] == 641
    assert cpobc["word_equation_count"] == 783
    assert cpobc["zero_residual_count"] == 783
    assert cpobc["nonzero_residual_count"] == 0
    assert cpobc["equation_kind_counts"] == {
        "eq103": 641,
        "equal_second_orientation": 71,
        "eq104": 71,
    }

    msr = certificate["strong_MSR"]
    assert msr["constraint_count"] == msr["zero_residual_count"] == 24
    assert msr["nonzero_residual_count"] == 0

    gc = certificate["local_operator_GC"]
    assert gc["basis_relation_count"] == (
        gc["basis_zero_residual_count"]
    ) == 320
    assert gc["same_endpoint_path_pair_count"] == (
        gc["same_endpoint_pair_zero_residual_count"]
    ) == 1529

    atomisation = certificate["atomisation"]
    assert atomisation["path_count"] == 34
    assert atomisation["G_node_zero_residual_count"] == 34
    assert atomisation["Q_stage_zero_residual_count"] == 34

    inverses = certificate["inverse_nodes"]
    assert inverses["count"] == inverses["base_nonzero_count"] == 26
    assert inverses["inverse_value_nonzero_count"] == 26
    assert inverses["two_sided_product_one_count"] == 26

    branches = certificate["Eq113_path_consistency_branches"]
    assert branches["EQ113_QN_BRANCH"]["relation_count"] == 25
    assert branches["EQ113_QN_BRANCH"]["zero_residual_count"] == 25
    assert branches["EQ113_QN_BRANCH"]["Q_5_word_relation_count"] == 0
    literal = branches["EQ113_QN_PLUS_1_BRANCH"]
    assert literal["relation_count"] == literal["zero_residual_count"] == 25
    assert literal["Q_5_word_relation_count"] == 24
    assert literal["Q_5_assignment_available"]

    assert certificate["semantic_digest_sha256"] == (
        "6c852125c0ec0b8ade2bf1a7ba2f87674c189a9597cbc5f99f3b929f848b5c35"
    )
    frozen_certificate = json.loads(
        SCALAR_CERTIFICATE_PATH.read_text(encoding="utf-8")
    )
    assert frozen_certificate == certificate


def test_denominator_inventory_is_explicit_and_conditionally_exact() -> None:
    oracle = _load_oracle()

    for fixture in oracle.build_fixture_certificates():
        inventory = fixture["denominator_inventory"]
        assert inventory["entry_count"] == len(inventory["entries"]) == 23
        assert inventory["expected_denominator_factors"] == (
            inventory["atomic_nonzero_factors"]
        )
        assert inventory["atomic_nonzero_factors"]
        assert not inventory["contains_identically_zero_denominator"]
        assert any(
            entry["kind"] == "INVERSE_DETERMINANT"
            for entry in inventory["entries"]
        )
        assert any(
            entry["kind"] == "SELECTED_RELATION_RESIDUAL"
            for entry in inventory["entries"]
        )
        assert "not the denominator inventory of all 641" in inventory[
            "scope_boundary"
        ]


def test_semantic_digest_and_partial_boundary_are_stable() -> None:
    oracle = _load_oracle()
    result = oracle.run_oracle()
    summary = result["semantic_summary"]

    assert result["passed"]
    assert result["verdict"] == "INDEPENDENT_ORACLE_PARTIAL"
    assert summary["semantic_digest_sha256"] == (
        "af6c4bcdb18409a711f7634b3b6c01ca60c90e483e1fd40aea9eddb9d9caee62"
    )
    assert summary["semantic_digest_sha256"] == oracle.stable_hash(
        summary["descriptor"]
    )
    assert summary["descriptor"]["coverage"][
        "compiled_relation_count_checked"
    ] == 641
    assert summary["descriptor"]["coverage"][
        "original_CPOBC_word_equation_count_checked"
    ] == 783
    assert summary["descriptor"]["coverage"]["full_641_relation_status"] == (
        "ALL_ZERO_AT_DECLARED_EXACT_SCALAR_FIXTURE"
    )
    assert result["self_checks"]["exact_scalar_fixture_full_inventory"]
    assert any(
        "evaluated only at one exact scalar fixture" in component
        for component in result["unresolved_components"]
    )
    assert json.loads(json.dumps(result, sort_keys=True)) == result


def test_oracle_source_has_no_production_import() -> None:
    source = ORACLE_PATH.read_text(encoding="utf-8")

    assert "from universe_lab" not in source
    assert "import universe_lab" not in source
    assert "src.universe_lab" not in source
    assert "v034" not in "\n".join(
        line
        for line in source.splitlines()
        if line.startswith("from ") or line.startswith("import ")
    )
