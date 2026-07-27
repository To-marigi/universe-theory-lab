"""Typed, serialization-friendly records shared by stringbench frontends."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from universe_lab.stringbench.evidence import Evidence


def _nonempty(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class UniverseTagged[T]:
    """A value that cannot be compared across frames without an allowed morphism."""

    universe_id: str
    frame_id: str
    arithmetic_model_id: str
    value: T
    allowed_morphisms: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _nonempty("universe_id", self.universe_id)
        _nonempty("frame_id", self.frame_id)
        _nonempty("arithmetic_model_id", self.arithmetic_model_id)

    def comparable_to(
        self,
        other: UniverseTagged[Any],
        *,
        certificate_id: str | None = None,
    ) -> bool:
        if (
            self.universe_id == other.universe_id
            and self.frame_id == other.frame_id
            and self.arithmetic_model_id == other.arithmetic_model_id
        ):
            return True
        return bool(
            certificate_id
            and certificate_id in self.allowed_morphisms
            and certificate_id in other.allowed_morphisms
        )

    def require_comparable(
        self,
        other: UniverseTagged[Any],
        *,
        certificate_id: str | None = None,
    ) -> None:
        if not self.comparable_to(other, certificate_id=certificate_id):
            raise ValueError(
                "cross-frame comparison requires a shared explicit DualityLinkCertificate"
            )


@dataclass(frozen=True, slots=True)
class FrameCard:
    frame_id: str
    theory: str
    spacetime_dimension: int
    supersymmetry: str
    background_geometry: str
    moduli: tuple[str, ...]
    fluxes: tuple[str, ...]
    branes: tuple[str, ...]
    charge_lattice: str
    gauge_data: dict[str, Any]
    validity_domain: tuple[str, ...]
    approximation_order: str
    evidence: Evidence

    def __post_init__(self) -> None:
        _nonempty("frame_id", self.frame_id)
        _nonempty("theory", self.theory)
        if self.spacetime_dimension <= 0:
            raise ValueError("spacetime_dimension must be positive")
        if not self.validity_domain:
            raise ValueError("validity_domain must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InvariantRecord:
    name: str
    value: Any
    representation: str
    source_frame: str
    transformation_rule: str
    exactness: Evidence
    numerical_error: float | None
    source_claim: str

    def __post_init__(self) -> None:
        _nonempty("name", self.name)
        _nonempty("source_frame", self.source_frame)
        _nonempty("source_claim", self.source_claim)
        if self.numerical_error is not None and self.numerical_error < 0:
            raise ValueError("numerical_error must be non-negative")
