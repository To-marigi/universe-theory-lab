"""Narain-period bridge with an explicit independent-period stopping boundary."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

import sympy as sp

from universe_lab.stringbench.frames.f_theory import (
    FibrationKind,
    FTheoryInput,
    compile_f_theory,
)
from universe_lab.stringbench.invariants.modular import (
    K3ModularInvariants,
    modular_invariants_from_quartic,
)
from universe_lab.stringbench.narain.branches import DerivedBranch
from universe_lab.stringbench.narain.types import (
    K3PeriodPoint,
    ModularInvariantPoint,
    NarainOrbit,
)


def _expression_text(value: sp.Expr) -> str:
    return str(sp.factor(value))


def modular_point_from_quartic(
    coefficients: tuple[Any, Any, Any, Any, Any, Any],
) -> ModularInvariantPoint:
    invariants = modular_invariants_from_quartic(*coefficients)
    return ModularInvariantPoint(
        j2=_expression_text(invariants.j2),
        j3=_expression_text(invariants.j3),
        j4=_expression_text(invariants.j4),
        j5=_expression_text(invariants.j5),
        j6=_expression_text(invariants.j6),
        a_squared=_expression_text(invariants.automorphic_square),
        j30=None,
        weighted_projective_scale="equivalence under weights (2,3,4,5,6)",
        exactness="EXACT_SYMBOLIC_FROM_QUARTIC",
        error_budget={
            "arithmetic_error": 0,
            "period_error": "not evaluated; no independent period oracle",
            "J30": "not implemented",
        },
    )


def _orbit_record(branch: DerivedBranch) -> NarainOrbit:
    payload = repr(
        (
            branch.chart.chart_id,
            branch.representative.orbit_key,
            branch.representative.analysis.components,
        )
    ).encode()
    return NarainOrbit(
        lattice="L^(2,4)",
        signature=(2, 4),
        period_vector=None,
        arithmetic_group="O+(L^(2,4))",
        orbit_certificate=f"typed-placeholder:sha256:{sha256(payload).hexdigest()}",
        local_charts=(branch.chart.chart_id,),
        monodromy_data=("not computed",),
        evidence=(
            "GLOBAL_COORDINATE_NOT_DEFINED: local chart identity is recorded, but "
            "no arithmetic-orbit reduction or period vector is claimed"
        ),
    )


def _blocked_period_point() -> K3PeriodPoint:
    return K3PeriodPoint(
        period_vector=None,
        cycle_basis=(),
        intersection_matrix=(),
        normalization="not available",
        numerical_precision=None,
        integration_error=None,
        monodromy_orbit="not computed",
        evidence=(
            "PERIOD_ORACLE_BLOCKED: no Picard-Fuchs solver, numerical two-cycle "
            "integration, independent theta implementation, or monodromy continuation"
        ),
    )


def _forward_fibration_audit() -> dict[str, Any]:
    coefficients = (1, 2, 3, 5, 7, 11)
    invariant_point = modular_point_from_quartic(coefficients)
    records = []
    for kind in FibrationKind:
        compiled = compile_f_theory(FTheoryInput(*coefficients, kind))
        records.append(
            {
                "fibration": kind.value,
                "status": compiled.status.value,
                "equation_kind": compiled.equation_kind,
                "has_discriminant": compiled.discriminant is not None,
            }
        )
    return {
        "status": "EXACT_SYMBOLIC",
        "modular_point": asdict(invariant_point),
        "fibrations": records,
        "passed": all(record["has_discriminant"] for record in records),
        "scope": "quartic coefficients -> J2..J6 -> four Weierstrass presentations",
    }


@dataclass(frozen=True, slots=True)
class BridgeAudit:
    local_chart_status: str
    global_orbit_status: str
    period_status: str
    forward_status: str
    reverse_status: str
    raw_coordinate_round_trip_required: bool
    overall_status: str
    orbits: tuple[NarainOrbit, ...]
    k3_period_point: K3PeriodPoint
    forward_audit: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_chart_status": self.local_chart_status,
            "global_orbit_status": self.global_orbit_status,
            "period_status": self.period_status,
            "forward_status": self.forward_status,
            "reverse_status": self.reverse_status,
            "raw_coordinate_round_trip_required": self.raw_coordinate_round_trip_required,
            "overall_status": self.overall_status,
            "orbits": [orbit.to_dict() for orbit in self.orbits],
            "k3_period_point": self.k3_period_point.to_dict(),
            "forward_audit": self.forward_audit,
        }


def audit_period_bridge(branches: tuple[DerivedBranch, ...]) -> BridgeAudit:
    """Audit the bridge without using the production J-map as its own inverse."""

    forward = _forward_fibration_audit()
    local_passed = len(branches) == 4 and all(
        branch.representative.analysis.components
        == tuple(
            sorted(
                branch.specification.target_components,
                key=lambda item: (item[0], int(item[1:])),
            )
        )
        for branch in branches
    )
    return BridgeAudit(
        local_chart_status=(
            "LOCAL_HETEROTIC_LOWERING_PASS" if local_passed else "FAIL"
        ),
        global_orbit_status="GLOBAL_WILSON_COORDINATES_NOT_DEFINED",
        period_status="PERIOD_ORACLE_BLOCKED",
        forward_status="FORWARD_FOUR_FIBRATIONS_PASS"
        if forward["passed"]
        else "FAIL",
        reverse_status="PERIOD_ORACLE_BLOCKED",
        raw_coordinate_round_trip_required=False,
        overall_status="DUALITY_PARTIAL",
        orbits=tuple(_orbit_record(branch) for branch in branches),
        k3_period_point=_blocked_period_point(),
        forward_audit=forward,
    )


def weighted_projectively_equivalent(
    left: K3ModularInvariants,
    right: K3ModularInvariants,
    scale: Any,
) -> bool:
    expected = left.weighted_scale(scale)
    return all(
        sp.simplify(actual - target) == 0
        for actual, target in zip(right.values, expected.values, strict=True)
    )
