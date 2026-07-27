"""Evidence-aware intermediate representations for string-duality benchmarks."""

from universe_lab.stringbench.evidence import Evidence, EvidenceState, SourceRef
from universe_lab.stringbench.ir.duality_link import DualityLinkCertificate
from universe_lab.stringbench.ir.vacuum_ir import VacuumIR
from universe_lab.stringbench.schemas import FrameCard, InvariantRecord, UniverseTagged

__all__ = [
    "DualityLinkCertificate",
    "Evidence",
    "EvidenceState",
    "FrameCard",
    "InvariantRecord",
    "SourceRef",
    "UniverseTagged",
    "VacuumIR",
]
