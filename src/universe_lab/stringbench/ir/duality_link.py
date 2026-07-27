"""Explicit certificates for mappings between otherwise isolated frames."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from universe_lab.stringbench.evidence import Evidence, EvidenceState
from universe_lab.stringbench.ir.vacuum_ir import VacuumIR


@dataclass(frozen=True, slots=True)
class InvariantComparison:
    name: str
    matched: bool
    source_value: Any
    target_value: Any
    reason: str


@dataclass(frozen=True, slots=True)
class DualityLinkCertificate:
    certificate_id: str
    source_frame: str
    target_frame: str
    forward_map: str
    inverse_map: str | None
    validity_domain: tuple[str, ...]
    preserved_invariants: tuple[str, ...]
    transformed_quantities: dict[str, str]
    frame_specific_quantities: tuple[str, ...]
    discarded_information: tuple[str, ...]
    reconstructible_information: tuple[str, ...]
    known_corrections: tuple[str, ...]
    exactness: EvidenceState
    evidence: Evidence
    failure_modes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.certificate_id.strip():
            raise ValueError("certificate_id must not be empty")
        if not self.validity_domain:
            raise ValueError("validity_domain must not be empty")
        if not self.failure_modes:
            raise ValueError("failure_modes must not be empty")

    def compare_ir(
        self,
        source: VacuumIR,
        target: VacuumIR,
        *,
        comparator: Callable[[Any, Any], bool] | None = None,
    ) -> tuple[InvariantComparison, ...]:
        compare = comparator or (lambda left, right: left == right)
        source_records = source.invariant_map()
        target_records = target.invariant_map()
        results = []
        for name in self.preserved_invariants:
            if name not in source_records or name not in target_records:
                results.append(
                    InvariantComparison(name, False, None, None, "missing invariant record")
                )
                continue
            left = source_records[name].value
            right = target_records[name].value
            results.append(
                InvariantComparison(
                    name,
                    compare(left, right),
                    left,
                    right,
                    "values compared in the declared common representation",
                )
            )
        return tuple(results)
