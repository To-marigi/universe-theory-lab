"""Explicit gates for a proposed bridge from string backgrounds into IUT.

No such bridge is supplied here.  The evaluator makes that absence executable
instead of silently treating similar vocabulary as a mathematical map.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .arithmetic_fingerprint import (
    DerivedConstraint,
    StandardArithmeticFingerprint,
    assess_non_redundancy,
)
from .universe_tags import FrameIsolationAudit


class IUTStatus(StrEnum):
    PHYSICAL_BRIDGE_PASS = "IUT_PHYSICAL_BRIDGE_PASS"
    TYPE_SYSTEM_ONLY = "IUT_TYPE_SYSTEM_ONLY"
    ADDS_NO_NEW_CONSTRAINT = "IUT_ADDS_NO_NEW_CONSTRAINT"
    NOT_APPLICABLE = "IUT_NOT_APPLICABLE"
    BRIDGE_CONJECTURAL = "IUT_BRIDGE_CONJECTURAL"
    BRIDGE_FAIL = "IUT_BRIDGE_FAIL"


@dataclass(frozen=True, slots=True)
class InitialThetaData:
    """Minimal domain facts from the published IUT I abstract.

    Real initial Theta-data contains further technical conditions. Therefore this
    record can establish obvious non-applicability, but cannot certify that the
    full IUT hypotheses hold.
    """

    elliptic_curve_id: str
    number_field: str
    ell: int
    technical_conditions_verified: bool = False

    @property
    def basic_domain_valid(self) -> bool:
        return (
            bool(self.elliptic_curve_id.strip())
            and bool(self.number_field.strip())
            and self.ell >= 5
            and _is_prime(self.ell)
        )


@dataclass(frozen=True, slots=True)
class PhysicalToIUTMap:
    """A proposed, citable map, not merely a name correspondence."""

    map_id: str
    source_frame_id: str
    target_initial_theta_data: InitialThetaData
    construction: str
    source_reference: str
    model_independent: bool
    duality_compatible: bool | None
    physical_interpretation_defined: bool

    @property
    def explicitly_defined(self) -> bool:
        return all(
            (
                self.map_id.strip(),
                self.source_frame_id.strip(),
                self.construction.strip(),
                self.source_reference.strip(),
            )
        )


@dataclass(frozen=True, slots=True)
class PredictiveTest:
    """A preregistered held-out prediction."""

    target_id: str
    prediction: str
    observed_value: str | None
    coefficients_fit_after_observation: bool

    @property
    def passed(self) -> bool:
        return (
            bool(self.target_id.strip())
            and bool(self.prediction.strip())
            and self.observed_value is not None
            and not self.coefficients_fit_after_observation
            and self.prediction == self.observed_value
        )


@dataclass(frozen=True, slots=True)
class BridgeProposal:
    physical_map: PhysicalToIUTMap | None = None
    standard_fingerprint: StandardArithmeticFingerprint | None = None
    iut_constraint: DerivedConstraint | None = None
    predictive_test: PredictiveTest | None = None
    independent_verification_status: str = "BLOCKED"
    dispute_context_acknowledged: bool = False


@dataclass(frozen=True, slots=True)
class GateResult:
    gate: str
    passed: bool
    status: IUTStatus | None
    detail: str


@dataclass(frozen=True, slots=True)
class IUTBridgeEvaluation:
    """Separates a useful type system result from the absent native bridge."""

    overall_status: IUTStatus
    type_system_status: IUTStatus
    native_bridge_status: IUTStatus
    gates: tuple[GateResult, ...]


def evaluate_iut_bridge(
    isolation: FrameIsolationAudit,
    proposal: BridgeProposal | None = None,
) -> IUTBridgeEvaluation:
    """Evaluate H-IUT0 first, then refuse to infer an arithmetic/physical bridge."""

    gates: list[GateResult] = [
        GateResult(
            gate="H-IUT0 frame isolation",
            passed=isolation.passed,
            status=IUTStatus.TYPE_SYSTEM_ONLY if isolation.passed else IUTStatus.BRIDGE_FAIL,
            detail="runtime tags and explicit morphisms are enforced"
            if isolation.passed
            else "frame isolation controls are incomplete",
        )
    ]
    if not isolation.passed:
        return IUTBridgeEvaluation(
            overall_status=IUTStatus.BRIDGE_FAIL,
            type_system_status=IUTStatus.BRIDGE_FAIL,
            native_bridge_status=IUTStatus.BRIDGE_FAIL,
            gates=tuple(gates),
        )

    if proposal is None or proposal.physical_map is None:
        gates.append(
            GateResult(
                gate="I1 domain",
                passed=False,
                status=IUTStatus.NOT_APPLICABLE,
                detail="no explicit physical-background to initial Theta-data map was provided",
            )
        )
        return IUTBridgeEvaluation(
            overall_status=IUTStatus.TYPE_SYSTEM_ONLY,
            type_system_status=IUTStatus.TYPE_SYSTEM_ONLY,
            native_bridge_status=IUTStatus.NOT_APPLICABLE,
            gates=tuple(gates),
        )

    bridge_map = proposal.physical_map
    domain_ok = (
        bridge_map.explicitly_defined
        and bridge_map.target_initial_theta_data.basic_domain_valid
        and bridge_map.target_initial_theta_data.technical_conditions_verified
        and bridge_map.physical_interpretation_defined
    )
    gates.append(
        GateResult(
            gate="I1 domain",
            passed=domain_ok,
            status=None if domain_ok else IUTStatus.NOT_APPLICABLE,
            detail="full initial Theta-data and physical interpretation are explicit"
            if domain_ok
            else "minimal naming/data do not verify the full IUT domain and physical map",
        )
    )
    if not domain_ok:
        return _type_only(gates, IUTStatus.NOT_APPLICABLE)

    gates.append(
        GateResult(
            gate="I2 model independence",
            passed=bridge_map.model_independent,
            status=None if bridge_map.model_independent else IUTStatus.BRIDGE_FAIL,
            detail="map is model independent"
            if bridge_map.model_independent
            else "map depends on presentation/coordinates",
        )
    )
    if not bridge_map.model_independent:
        return _type_only(gates, IUTStatus.BRIDGE_FAIL)

    duality_ok = bridge_map.duality_compatible is True
    gates.append(
        GateResult(
            gate="I3 duality",
            passed=duality_ok,
            status=None if duality_ok else IUTStatus.BRIDGE_CONJECTURAL,
            detail="duality compatibility independently established"
            if duality_ok
            else "duality compatibility is absent or unresolved",
        )
    )
    if not duality_ok:
        return _type_only(gates, IUTStatus.BRIDGE_CONJECTURAL)

    if proposal.standard_fingerprint is None or proposal.iut_constraint is None:
        gates.append(
            GateResult(
                gate="I4 non-redundancy",
                passed=False,
                status=IUTStatus.BRIDGE_CONJECTURAL,
                detail="no auditable IUT-derived constraint and conventional baseline pair",
            )
        )
        return _type_only(gates, IUTStatus.BRIDGE_CONJECTURAL)

    novelty = assess_non_redundancy(proposal.iut_constraint, proposal.standard_fingerprint)
    novelty_status = (
        None
        if novelty.passed
        else IUTStatus(novelty.label)
    )
    gates.append(
        GateResult(
            gate="I4 non-redundancy",
            passed=novelty.passed,
            status=novelty_status,
            detail="; ".join(novelty.reasons),
        )
    )
    if not novelty.passed:
        return _type_only(gates, novelty_status or IUTStatus.BRIDGE_CONJECTURAL)

    predictive_ok = proposal.predictive_test is not None and proposal.predictive_test.passed
    gates.append(
        GateResult(
            gate="I5 predictive",
            passed=predictive_ok,
            status=None if predictive_ok else IUTStatus.BRIDGE_CONJECTURAL,
            detail="held-out prediction passed without post-hoc fitting"
            if predictive_ok
            else "no passing preregistered held-out prediction",
        )
    )
    if not predictive_ok:
        return _type_only(gates, IUTStatus.BRIDGE_CONJECTURAL)

    evidence_ok = (
        proposal.independent_verification_status in {"PROVEN", "FORMALLY_DERIVED"}
        and proposal.dispute_context_acknowledged
    )
    gates.append(
        GateResult(
            gate="evidence and dispute audit",
            passed=evidence_ok,
            status=None if evidence_ok else IUTStatus.BRIDGE_CONJECTURAL,
            detail="independent verification and dispute context recorded"
            if evidence_ok
            else "independent proof-grade verification is missing",
        )
    )
    status = IUTStatus.PHYSICAL_BRIDGE_PASS if evidence_ok else IUTStatus.BRIDGE_CONJECTURAL
    return IUTBridgeEvaluation(
        overall_status=status,
        type_system_status=IUTStatus.TYPE_SYSTEM_ONLY,
        native_bridge_status=status,
        gates=tuple(gates),
    )


def _type_only(
    gates: list[GateResult],
    native_status: IUTStatus,
) -> IUTBridgeEvaluation:
    return IUTBridgeEvaluation(
        overall_status=IUTStatus.TYPE_SYSTEM_ONLY,
        type_system_status=IUTStatus.TYPE_SYSTEM_ONLY,
        native_bridge_status=native_status,
        gates=tuple(gates),
    )


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    factor = 2
    while factor * factor <= value:
        if value % factor == 0:
            return False
        factor += 1
    return True
