"""Conventional arithmetic fingerprints and an IUT non-redundancy gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StandardArithmeticFingerprint:
    """Arithmetic data already available without IUT.

    These fields deliberately mirror the conventional controls named by the
    benchmark request.  Hashing or repackaging them does not create a new
    arithmetic constraint.
    """

    discriminant_valuations: tuple[tuple[str, int], ...] = ()
    reduction_types: tuple[tuple[str, str], ...] = ()
    j_invariant: str | None = None
    mordell_weil_rank: int | None = None
    mordell_weil_torsion: tuple[int, ...] = ()
    height_pairings: tuple[tuple[str, str], ...] = ()
    local_galois_data: tuple[str, ...] = ()
    conductor_data: tuple[tuple[str, int], ...] = ()
    extra_standard_data: tuple[tuple[str, str], ...] = ()

    @property
    def field_names(self) -> frozenset[str]:
        return frozenset(asdict(self))

    def canonical_payload(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def conventional_digest(self) -> str:
        """A serialization checksum, explicitly not a new invariant."""

        return hashlib.sha256(self.canonical_payload().encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class DerivedConstraint:
    """A proposed output together with its complete derivation lineage."""

    name: str
    value: Any
    derivation_inputs: frozenset[str]
    derivation_description: str
    uses_iut_native_step: bool = False
    iut_theorem_locator: str | None = None
    independent_derivation_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NonRedundancyAssessment:
    passed: bool
    label: str
    reasons: tuple[str, ...]


def assess_non_redundancy(
    candidate: DerivedConstraint,
    standard: StandardArithmeticFingerprint,
) -> NonRedundancyAssessment:
    """Reject outputs reconstructible from conventional arithmetic data."""

    reasons: list[str] = []
    unknown_inputs = candidate.derivation_inputs - standard.field_names
    if not candidate.uses_iut_native_step:
        reasons.append("derivation declares no IUT-native step")
    if not unknown_inputs:
        reasons.append("all declared inputs are conventional arithmetic fingerprint fields")
    if candidate.value == standard.conventional_digest():
        reasons.append("candidate is only a digest of the conventional fingerprint")

    if reasons:
        return NonRedundancyAssessment(
            passed=False,
            label="IUT_ADDS_NO_NEW_CONSTRAINT",
            reasons=tuple(reasons),
        )

    if not candidate.iut_theorem_locator:
        return NonRedundancyAssessment(
            passed=False,
            label="IUT_BRIDGE_CONJECTURAL",
            reasons=("IUT-native step has no theorem/definition locator",),
        )
    if not candidate.independent_derivation_reference:
        return NonRedundancyAssessment(
            passed=False,
            label="IUT_BRIDGE_CONJECTURAL",
            reasons=("claimed non-redundancy lacks an independent derivation",),
        )
    return NonRedundancyAssessment(
        passed=True,
        label="NON_REDUNDANCY_GATE_PASS",
        reasons=("candidate is not reconstructible from the declared conventional fields",),
    )
