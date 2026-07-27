"""Runtime type discipline for data that live in distinct mathematical frames.

This module is *inspired* by the separation of Hodge theaters in IUT.  It does
not implement a Hodge theater and it makes no IUT-native mathematical claim.
The useful, testable idea is much smaller: an isomorphism is not an identity,
and values from separately tagged frames cannot be compared without a declared
morphism.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class CrossUniverseComparisonError(TypeError):
    """Raised when values from different tagged frames are compared directly."""


class MorphismValidationError(ValueError):
    """Raised when an explicit morphism does not match its tagged operands."""


@dataclass(frozen=True, slots=True)
class FrameAddress:
    """The full address needed to distinguish otherwise isomorphic values."""

    universe_id: str
    frame_id: str
    arithmetic_model_id: str

    def __post_init__(self) -> None:
        for name in ("universe_id", "frame_id", "arithmetic_model_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True, eq=False)
class UniverseTagged[T]:
    """A value coupled to its universe, physical frame, and arithmetic model."""

    universe_id: str
    frame_id: str
    arithmetic_model_id: str
    value: T
    allowed_morphisms: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        # Constructing the address performs the shared non-empty validation.
        _ = self.address

    @property
    def address(self) -> FrameAddress:
        return FrameAddress(self.universe_id, self.frame_id, self.arithmetic_model_id)

    def _require_same_address(self, other: object) -> UniverseTagged[Any]:
        if not isinstance(other, UniverseTagged):
            raise TypeError("UniverseTagged values can only be compared with UniverseTagged values")
        if self.address != other.address:
            raise CrossUniverseComparisonError(
                "raw cross-universe comparison is forbidden; supply an explicit "
                "MorphismCertificate"
            )
        return other

    def __eq__(self, other: object) -> bool:
        tagged_other = self._require_same_address(other)
        return bool(self.value == tagged_other.value)

    def __lt__(self, other: object) -> bool:
        tagged_other = self._require_same_address(other)
        return bool(self.value < tagged_other.value)

    def __le__(self, other: object) -> bool:
        tagged_other = self._require_same_address(other)
        return bool(self.value <= tagged_other.value)

    def __gt__(self, other: object) -> bool:
        tagged_other = self._require_same_address(other)
        return bool(self.value > tagged_other.value)

    def __ge__(self, other: object) -> bool:
        tagged_other = self._require_same_address(other)
        return bool(self.value >= tagged_other.value)

    __hash__: Any = None


@dataclass(frozen=True, slots=True)
class MorphismCertificate:
    """An auditable, directional permission to transport a tagged value."""

    morphism_id: str
    source: FrameAddress
    target: FrameAddress
    preserved_structure: tuple[str, ...]
    forgotten_structure: tuple[str, ...]
    evidence_status: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.morphism_id.strip():
            raise ValueError("morphism_id must be non-empty")
        if not self.preserved_structure:
            raise ValueError("preserved_structure must be stated explicitly")
        if not self.evidence_status.strip() or not self.source_reference.strip():
            raise ValueError("morphism evidence status and source are required")
        overlap = set(self.preserved_structure) & set(self.forgotten_structure)
        if overlap:
            raise ValueError(f"structure cannot be both preserved and forgotten: {overlap}")

    def transport[T, U](
        self,
        tagged: UniverseTagged[T],
        transform: Callable[[T], U],
        *,
        allowed_target_morphisms: frozenset[str] = frozenset(),
    ) -> UniverseTagged[U]:
        """Apply the declared map only when its source and permission both match."""

        if tagged.address != self.source:
            raise MorphismValidationError("morphism source does not match tagged value")
        if self.morphism_id not in tagged.allowed_morphisms:
            raise MorphismValidationError("tagged value does not permit this morphism")
        return UniverseTagged(
            universe_id=self.target.universe_id,
            frame_id=self.target.frame_id,
            arithmetic_model_id=self.target.arithmetic_model_id,
            value=transform(tagged.value),
            allowed_morphisms=allowed_target_morphisms,
        )


def compare_after_transport[T, U](
    source: UniverseTagged[T],
    target: UniverseTagged[U],
    certificate: MorphismCertificate,
    transform: Callable[[T], U],
    comparator: Callable[[U, U], bool] | None = None,
) -> bool:
    """Compare only after a certified transport into the target address."""

    if target.address != certificate.target:
        raise MorphismValidationError("comparison target does not match morphism target")
    transported = certificate.transport(source, transform)
    compare = comparator or (lambda left, right: left == right)
    return bool(compare(transported.value, target.value))


@dataclass(frozen=True, slots=True)
class FrameIsolationAudit:
    """Evidence that the software layer enforces the H-IUT0 discipline."""

    raw_cross_frame_comparison_blocked: bool
    morphism_permission_checked: bool
    preserved_structure_recorded: bool
    forgotten_structure_recorded: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.raw_cross_frame_comparison_blocked,
                self.morphism_permission_checked,
                self.preserved_structure_recorded,
                self.forgotten_structure_recorded,
            )
        )
