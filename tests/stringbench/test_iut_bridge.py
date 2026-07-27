from __future__ import annotations

from universe_lab.stringbench.iut import (
    BridgeProposal,
    DerivedConstraint,
    FrameIsolationAudit,
    InitialThetaData,
    IUTStatus,
    PhysicalToIUTMap,
    PredictiveTest,
    StandardArithmeticFingerprint,
    assess_non_redundancy,
    evaluate_iut_bridge,
)


def passing_isolation() -> FrameIsolationAudit:
    return FrameIsolationAudit(
        raw_cross_frame_comparison_blocked=True,
        morphism_permission_checked=True,
        preserved_structure_recorded=True,
        forgotten_structure_recorded=True,
    )


def test_h_iut0_is_useful_while_native_bridge_is_not_applicable() -> None:
    result = evaluate_iut_bridge(passing_isolation())

    assert result.overall_status is IUTStatus.TYPE_SYSTEM_ONLY
    assert result.type_system_status is IUTStatus.TYPE_SYSTEM_ONLY
    assert result.native_bridge_status is IUTStatus.NOT_APPLICABLE
    assert [gate.gate for gate in result.gates] == ["H-IUT0 frame isolation", "I1 domain"]


def test_standard_arithmetic_digest_is_detected_as_redundant() -> None:
    standard = StandardArithmeticFingerprint(
        discriminant_valuations=(("2", 3), ("5", 1)),
        reduction_types=(("2", "I_3"),),
        j_invariant="1728",
        mordell_weil_rank=1,
    )
    claimed = DerivedConstraint(
        name="iut_fingerprint",
        value=standard.conventional_digest(),
        derivation_inputs=standard.field_names,
        derivation_description="serialize and hash standard fields",
        uses_iut_native_step=False,
    )

    assessment = assess_non_redundancy(claimed, standard)

    assert not assessment.passed
    assert assessment.label == "IUT_ADDS_NO_NEW_CONSTRAINT"
    assert any("digest" in reason for reason in assessment.reasons)


def test_relabeling_standard_fields_does_not_create_an_iut_constraint() -> None:
    standard = StandardArithmeticFingerprint(
        j_invariant="0",
        mordell_weil_rank=0,
        mordell_weil_torsion=(2, 2),
    )
    claimed = DerivedConstraint(
        name="theta_volume_signature",
        value="renamed-standard-data",
        derivation_inputs=frozenset({"j_invariant", "mordell_weil_rank", "mordell_weil_torsion"}),
        derivation_description="rename conventional fields with IUT terminology",
    )

    assessment = assess_non_redundancy(claimed, standard)

    assert assessment.label == "IUT_ADDS_NO_NEW_CONSTRAINT"


def test_failed_type_isolation_is_a_bridge_failure() -> None:
    result = evaluate_iut_bridge(
        FrameIsolationAudit(
            raw_cross_frame_comparison_blocked=False,
            morphism_permission_checked=True,
            preserved_structure_recorded=True,
            forgotten_structure_recorded=True,
        ),
        BridgeProposal(),
    )

    assert result.overall_status is IUTStatus.BRIDGE_FAIL


def test_elliptic_name_without_full_initial_theta_conditions_is_not_applicable() -> None:
    proposal = BridgeProposal(
        physical_map=PhysicalToIUTMap(
            map_id="name-only",
            source_frame_id="elliptic-k3",
            target_initial_theta_data=InitialThetaData(
                elliptic_curve_id="putative-fiber",
                number_field="Q",
                ell=5,
                technical_conditions_verified=False,
            ),
            construction="select an elliptic-looking fiber by name",
            source_reference="no theorem defines this map",
            model_independent=False,
            duality_compatible=None,
            physical_interpretation_defined=False,
        )
    )

    result = evaluate_iut_bridge(passing_isolation(), proposal)

    assert result.overall_status is IUTStatus.TYPE_SYSTEM_ONLY
    assert result.native_bridge_status is IUTStatus.NOT_APPLICABLE


def test_full_gate_detects_standard_fingerprint_redundancy() -> None:
    standard = StandardArithmeticFingerprint(j_invariant="1728", mordell_weil_rank=1)
    proposal = BridgeProposal(
        physical_map=PhysicalToIUTMap(
            map_id="synthetic-test-map",
            source_frame_id="test-frame",
            target_initial_theta_data=InitialThetaData(
                elliptic_curve_id="E/Q",
                number_field="Q",
                ell=5,
                technical_conditions_verified=True,
            ),
            construction="synthetic fixture, not a claimed physical map",
            source_reference="test fixture",
            model_independent=True,
            duality_compatible=True,
            physical_interpretation_defined=True,
        ),
        standard_fingerprint=standard,
        iut_constraint=DerivedConstraint(
            name="renamed_rank",
            value=1,
            derivation_inputs=frozenset({"mordell_weil_rank"}),
            derivation_description="rename a conventional invariant",
        ),
        predictive_test=PredictiveTest("held-out", "1", "1", False),
    )

    result = evaluate_iut_bridge(passing_isolation(), proposal)

    assert result.native_bridge_status is IUTStatus.ADDS_NO_NEW_CONSTRAINT
    assert result.gates[-1].gate == "I4 non-redundancy"
