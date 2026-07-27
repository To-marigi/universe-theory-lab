"""Typed records that keep local coordinates separate from global period orbits."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any


def _require_text(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _complex_record(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


@dataclass(frozen=True, slots=True)
class LocalNarainChart:
    """A semiclassical coordinate chart; it is not a global Narain coordinate system."""

    tau: complex
    rho: complex
    wilson_line_1: tuple[Fraction, ...]
    wilson_line_2: tuple[Fraction, ...]
    gauge_lattice: str
    chart_id: str
    validity_domain: tuple[str, ...]
    approximation_status: str
    source: str

    def __post_init__(self) -> None:
        if self.tau.imag <= 0 or self.rho.imag <= 0:
            raise ValueError("tau and rho must lie in the upper half-plane")
        if len(self.wilson_line_1) != 16 or len(self.wilson_line_2) != 16:
            raise ValueError("each Wilson line must have 16 components")
        if self.gauge_lattice not in {"E8xE8", "Spin32_Z2"}:
            raise ValueError("unsupported heterotic gauge lattice")
        _require_text("chart_id", self.chart_id)
        _require_text("approximation_status", self.approximation_status)
        _require_text("source", self.source)
        if not self.validity_domain:
            raise ValueError("validity_domain must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tau": _complex_record(self.tau),
            "rho": _complex_record(self.rho),
            "wilson_line_1": [_fraction_text(value) for value in self.wilson_line_1],
            "wilson_line_2": [_fraction_text(value) for value in self.wilson_line_2],
            "gauge_lattice": self.gauge_lattice,
            "chart_id": self.chart_id,
            "validity_domain": list(self.validity_domain),
            "approximation_status": self.approximation_status,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class NarainOrbit:
    """A global orbit record; raw local coordinates are deliberately not equality keys."""

    lattice: str
    signature: tuple[int, int]
    period_vector: tuple[complex, ...] | None
    arithmetic_group: str
    orbit_certificate: str
    local_charts: tuple[str, ...]
    monodromy_data: tuple[str, ...]
    evidence: str

    def __post_init__(self) -> None:
        if self.signature != (2, 4):
            raise ValueError("v0.2 NarainOrbit must have signature (2, 4)")
        for name in ("lattice", "arithmetic_group", "orbit_certificate", "evidence"):
            _require_text(name, getattr(self, name))

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "period_vector": (
                [_complex_record(value) for value in self.period_vector]
                if self.period_vector is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class K3PeriodPoint:
    period_vector: tuple[complex, ...] | None
    cycle_basis: tuple[str, ...]
    intersection_matrix: tuple[tuple[int, ...], ...]
    normalization: str
    numerical_precision: int | None
    integration_error: float | None
    monodromy_orbit: str
    evidence: str

    def __post_init__(self) -> None:
        if self.integration_error is not None and self.integration_error < 0:
            raise ValueError("integration_error must be non-negative")
        if self.numerical_precision is not None and self.numerical_precision <= 0:
            raise ValueError("numerical_precision must be positive")
        for name in ("normalization", "monodromy_orbit", "evidence"):
            _require_text(name, getattr(self, name))

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "period_vector": (
                [_complex_record(value) for value in self.period_vector]
                if self.period_vector is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class ModularInvariantPoint:
    j2: str
    j3: str
    j4: str
    j5: str
    j6: str
    a_squared: str
    j30: str | None
    weighted_projective_scale: str
    exactness: str
    error_budget: dict[str, Any]

    def __post_init__(self) -> None:
        for name in (
            "j2",
            "j3",
            "j4",
            "j5",
            "j6",
            "a_squared",
            "weighted_projective_scale",
            "exactness",
        ):
            _require_text(name, getattr(self, name))
        if not self.error_budget:
            raise ValueError("error_budget must record exact or numerical uncertainty")


@dataclass(frozen=True, slots=True)
class HeteroticBranchCertificate:
    parent_string: str
    local_wilson_line_representative: dict[str, Any]
    surviving_root_system: tuple[str, ...]
    nonabelian_gauge_algebra: str
    abelian_rank: int
    gauge_group_global_data: str
    b_field_flux_class: str
    pointlike_instanton_behavior: str
    enhancement_loci: tuple[str, ...]
    corresponding_fibration: str
    validity_domain: tuple[str, ...]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.parent_string not in {"E8xE8", "Spin32_Z2"}:
            raise ValueError("unknown parent string")
        if self.abelian_rank < 0:
            raise ValueError("abelian_rank must be non-negative")
        if not self.surviving_root_system or not self.validity_domain or not self.evidence:
            raise ValueError("branch certificates require roots, validity, and evidence")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
