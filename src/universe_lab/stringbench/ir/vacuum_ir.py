"""Frame-neutral protected data used for duality comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from universe_lab.stringbench.schemas import InvariantRecord


@dataclass(frozen=True, slots=True)
class VacuumIR:
    charge_lattice: InvariantRecord
    lattice_pairing: InvariantRecord
    monodromy: tuple[InvariantRecord, ...]
    modular_invariants: tuple[InvariantRecord, ...]
    gauge_algebra: InvariantRecord
    gauge_group_global_data: InvariantRecord | None
    mordell_weil_rank: InvariantRecord | None
    mordell_weil_torsion: InvariantRecord | None
    singular_fibers: tuple[InvariantRecord, ...]
    bps_or_protected_data: tuple[InvariantRecord, ...]
    anomaly_data: tuple[InvariantRecord, ...]
    flux_quantization_data: tuple[InvariantRecord, ...]
    source_frames: tuple[str, ...]
    uncertainty_budget: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.source_frames:
            raise ValueError("source_frames must not be empty")
        if not self.uncertainty_budget:
            raise ValueError("uncertainty_budget must describe omissions and uncertainties")

    def invariant_map(self) -> dict[str, InvariantRecord]:
        records = (
            self.charge_lattice,
            self.lattice_pairing,
            self.gauge_algebra,
            *self.monodromy,
            *self.modular_invariants,
            *self.singular_fibers,
            *self.bps_or_protected_data,
            *self.anomaly_data,
            *self.flux_quantization_data,
        )
        optional = (
            self.gauge_group_global_data,
            self.mordell_weil_rank,
            self.mordell_weil_torsion,
        )
        return {record.name: record for record in (*records, *(r for r in optional if r))}
