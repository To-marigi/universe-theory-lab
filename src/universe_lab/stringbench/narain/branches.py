"""Independent local lowering and source-bounded certificates for four branches."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from universe_lab.stringbench.narain.roots import (
    WilsonRepresentative,
    discover_wilson_representative,
)
from universe_lab.stringbench.narain.types import (
    HeteroticBranchCertificate,
    LocalNarainChart,
)


class BranchId(StrEnum):
    STANDARD = "standard"
    BASE_FIBER_DUAL = "base_fiber_dual"
    ALTERNATE = "alternate"
    MAXIMAL = "maximal"


@dataclass(frozen=True, slots=True)
class BranchSpecification:
    branch: BranchId
    parent_string: str
    target_components: tuple[str, ...]
    gauge_algebra: str
    mordell_weil: str
    b_field: str
    instanton_behavior: str
    enhancement_loci: tuple[str, ...]
    source_locator: str


BRANCH_SPECIFICATIONS = (
    BranchSpecification(
        BranchId.STANDARD,
        "E8xE8",
        ("E7", "E7"),
        "e7 + e7",
        "trivial",
        "branch-dependent sign/double-cover data; not reconstructed from local roots",
        "pointlike-instanton relation is source-classified",
        ("J4 = 0", "J4 = J5 = 0"),
        "arXiv:2205.08100v1, Proposition 4.2",
    ),
    BranchSpecification(
        BranchId.BASE_FIBER_DUAL,
        "E8xE8",
        ("E8", "D6"),
        "e8 + so(12)",
        "trivial",
        "source-classified E8xE8 branch",
        "fixed II* fiber; generic pointlike-instanton avoidance is source-classified",
        ("J4 = 0", "J30 = 0"),
        "arXiv:2205.08100v1, Proposition 4.1",
    ),
    BranchSpecification(
        BranchId.ALTERNATE,
        "Spin32_Z2",
        ("D12", "A1", "A1"),
        "so(24) + su(2) + su(2)",
        "Z/2Z",
        "non-trivial quantized B-field class (source-classified)",
        "not the E8xE8 pointlike-instanton branch",
        ("J4 = 0", "J30 = 0"),
        "arXiv:2205.08100v1, Proposition 4.3",
    ),
    BranchSpecification(
        BranchId.MAXIMAL,
        "Spin32_Z2",
        ("D14",),
        "so(28)",
        "trivial",
        "Spin32_Z2 branch distinct from the alternate torsion/B-field branch",
        "not the E8xE8 pointlike-instanton branch",
        ("a = 0 gives so(30)", "J4 = 0"),
        "arXiv:2205.08100v1, discussion following Equation (53)",
    ),
)


@dataclass(frozen=True, slots=True)
class DerivedBranch:
    specification: BranchSpecification
    representative: WilsonRepresentative
    chart: LocalNarainChart
    certificate: HeteroticBranchCertificate


def _chart(
    specification: BranchSpecification,
    representative: WilsonRepresentative,
) -> LocalNarainChart:
    return LocalNarainChart(
        tau=1j,
        rho=5j,
        wilson_line_1=representative.wilson_line_1,
        wilson_line_2=representative.wilson_line_2,
        gauge_lattice=specification.parent_string,
        chart_id=f"local-narain:{specification.branch.value}:bounded-search",
        validity_domain=(
            "semiclassical large-radius chart",
            "zero-winding gauge-root sector",
            "raw coordinates are not continued globally across O+(L^(2,4))",
        ),
        approximation_status="LOCAL_ROOT_SECTOR_EXACT",
        source="representative discovered by bounded denominator search",
    )


def _certificate(
    specification: BranchSpecification,
    representative: WilsonRepresentative,
) -> HeteroticBranchCertificate:
    rank = representative.analysis.rank
    return HeteroticBranchCertificate(
        parent_string=specification.parent_string,
        local_wilson_line_representative=representative.to_dict(),
        surviving_root_system=representative.analysis.components,
        nonabelian_gauge_algebra=specification.gauge_algebra,
        abelian_rank=16 - rank,
        gauge_group_global_data=(
            f"Mordell-Weil torsion={specification.mordell_weil}; "
            "full global gauge group is not independently reconstructed"
        ),
        b_field_flux_class=specification.b_field,
        pointlike_instanton_behavior=specification.instanton_behavior,
        enhancement_loci=specification.enhancement_loci,
        corresponding_fibration=specification.branch.value,
        validity_domain=(
            "local Narain representative only",
            "branch binding beyond the gauge algebra is source-backed",
        ),
        evidence=(
            "massless roots and Cartan/Dynkin type independently derived with exact rationals",
            specification.source_locator,
            "MW torsion, B-field, and instanton fields are not inferred from the root system",
        ),
    )


def derive_branch_certificates() -> tuple[DerivedBranch, ...]:
    """Discover local representatives and derive all four root systems."""

    results = []
    for specification in BRANCH_SPECIFICATIONS:
        representative = discover_wilson_representative(
            specification.parent_string,
            specification.target_components,
            denominator_bound=3,
        )
        results.append(
            DerivedBranch(
                specification,
                representative,
                _chart(specification, representative),
                _certificate(specification, representative),
            )
        )
    return tuple(results)


def fraction(value: int, denominator: int = 1) -> Fraction:
    """Small public helper used by exact held-out fixtures."""

    return Fraction(value, denominator)
