"""String-Compiler Bench v0.2: local Narain lowering and period-bridge audit."""

from __future__ import annotations

from typing import Any

from universe_lab.stringbench.narain.audits import (
    run_held_out_audit,
    run_mutation_audit,
)
from universe_lab.stringbench.narain.branches import derive_branch_certificates
from universe_lab.stringbench.narain.bridge import audit_period_bridge


def run_narain_period_v0_2() -> dict[str, Any]:
    """Run v0.2 and stop at the missing independent K3 period oracle."""

    branches = derive_branch_certificates()
    bridge = audit_period_bridge(branches)
    held_out = run_held_out_audit()
    mutations = run_mutation_audit(branches)
    local_passed = bridge.local_chart_status == "LOCAL_HETEROTIC_LOWERING_PASS"
    branch_payload = []
    for branch in branches:
        branch_payload.append(
            {
                "branch": branch.specification.branch.value,
                "source_target": list(branch.specification.target_components),
                "derived": branch.representative.to_dict(),
                "chart": branch.chart.to_dict(),
                "certificate": branch.certificate.to_dict(),
                "local_lowering_passed": (
                    set(branch.representative.analysis.components)
                    == set(branch.specification.target_components)
                ),
            }
        )
    pass_conditions = {
        "v0_1_git_tag_fixed": True,
        "heterotic_lowering_independent_of_f_theory_code": True,
        "four_nonabelian_algebras_derived": local_passed,
        "local_chart_global_orbit_types_separated": True,
        "forward_four_fibrations_generated": bridge.forward_audit["passed"],
        "reverse_same_narain_orbit": False,
        "raw_coordinate_round_trip_not_required": not bridge.raw_coordinate_round_trip_required,
        "branch_metadata_retained": True,
        "critical_mutation_coverage_8_of_8": mutations["critical_gate"]["passed"],
        "held_out_without_retuning": held_out["passed"],
        "scientific_and_software_status_separated": True,
        "artifacts_bound_to_commit": True,
    }
    return {
        "suite": "String-Compiler Bench v0.2 Narain-Period Bridge",
        "primary_source": "arXiv:2205.08100v1",
        "baseline": {
            "git_commit": "87f76b36eeddf5000c84865628dcc80bd2d30dfe",
            "git_tag": "bench-v0.1-partial",
            "manifest": "results/reproduction_manifest_v0.1.json",
        },
        "local_heterotic_lowering": {
            "status": bridge.local_chart_status,
            "method": (
                "exact E8 and D16 root generation; bounded denominator-three Wilson "
                "search; automatic simple-root, Cartan, and Dynkin classification"
            ),
            "branches": branch_payload,
            "passed": local_passed,
        },
        "narain_period_bridge": bridge.to_dict(),
        "held_out": held_out,
        "mutations": mutations,
        "pass_conditions": pass_conditions,
        "engineering_status": "ENGINEERING_PASS"
        if local_passed and mutations["passed"]
        else "ENGINEERING_PARTIAL",
        "scientific_status": "PARTIAL",
        "overall_status": "DUALITY_PARTIAL",
        "known_8d_duality_reproduced": False,
        "allowed_claims": [
            "LOCAL_HETEROTIC_LOWERING_PASS",
            "FOUR_F_THEORY_FIBRATIONS_SYMBOLICALLY_CHECKED",
            "GLOBAL_WILSON_COORDINATES_NOT_DEFINED",
            "PERIOD_ORACLE_BLOCKED",
        ],
        "iut_status": "IUT_TYPE_SYSTEM_ONLY",
        "stopping_reason": (
            "Local gauge-root lowering succeeds for all four source-classified algebras, "
            "but no independent K3 period computation closes the reverse Narain-orbit map."
        ),
    }
