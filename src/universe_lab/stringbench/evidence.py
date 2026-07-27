"""Evidence labels that keep mathematical, numerical, and missing results distinct."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class EvidenceState(StrEnum):
    """Ordered only by meaning, never by a numeric confidence score."""

    PROVEN = "PROVEN"
    FORMALLY_DERIVED = "FORMALLY_DERIVED"
    EXACT_SYMBOLIC = "EXACT_SYMBOLIC"
    NUMERICALLY_REPRODUCED = "NUMERICALLY_REPRODUCED"
    NUMERICALLY_SUPPORTED = "NUMERICALLY_SUPPORTED"
    HEURISTIC = "HEURISTIC"
    CONJECTURAL = "CONJECTURAL"
    DISPUTED = "DISPUTED"
    CONTRADICTED = "CONTRADICTED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class SourceRef:
    """A precise, inspectable source pointer."""

    source_id: str
    title: str
    url: str
    locator: str
    primary: bool = True
    version: str | None = None

    def __post_init__(self) -> None:
        for name in ("source_id", "title", "url", "locator"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class Evidence:
    """Evidence plus assumptions and an explicit scope statement."""

    state: EvidenceState
    sources: tuple[SourceRef, ...]
    scope: str
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.scope.strip():
            raise ValueError("evidence scope must not be empty")
        if self.state not in {
            EvidenceState.BLOCKED,
            EvidenceState.HEURISTIC,
            EvidenceState.CONJECTURAL,
        } and not self.sources:
            raise ValueError(f"{self.state} evidence requires at least one source")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


PAPER_2205_08100 = SourceRef(
    source_id="arxiv:2205.08100v1",
    title="The duality between F-theory and the Heterotic String in D=8 "
    "with two Wilson lines",
    url="https://arxiv.org/abs/2205.08100v1",
    locator="Equations and propositions cited per record",
    version="v1",
)
