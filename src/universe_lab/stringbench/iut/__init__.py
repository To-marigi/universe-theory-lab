"""Skeptical IUT-inspired type discipline and bridge gates."""

from .arithmetic_fingerprint import (
    DerivedConstraint,
    NonRedundancyAssessment,
    StandardArithmeticFingerprint,
    assess_non_redundancy,
)
from .bridge import (
    BridgeProposal,
    GateResult,
    InitialThetaData,
    IUTBridgeEvaluation,
    IUTStatus,
    PhysicalToIUTMap,
    PredictiveTest,
    evaluate_iut_bridge,
)
from .universe_tags import (
    CrossUniverseComparisonError,
    FrameAddress,
    FrameIsolationAudit,
    MorphismCertificate,
    MorphismValidationError,
    UniverseTagged,
    compare_after_transport,
)

__all__ = [
    "BridgeProposal",
    "CrossUniverseComparisonError",
    "DerivedConstraint",
    "FrameAddress",
    "FrameIsolationAudit",
    "GateResult",
    "IUTBridgeEvaluation",
    "IUTStatus",
    "InitialThetaData",
    "MorphismCertificate",
    "MorphismValidationError",
    "NonRedundancyAssessment",
    "PhysicalToIUTMap",
    "PredictiveTest",
    "StandardArithmeticFingerprint",
    "UniverseTagged",
    "assess_non_redundancy",
    "compare_after_transport",
    "evaluate_iut_bridge",
]
