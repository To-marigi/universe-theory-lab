"""String-Compiler Bench v0.3 special-divisor and period closure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from universe_lab.stringbench.j4_period import audit_period_oracle
from universe_lab.stringbench.j30_locus import J30Point, certify_j30_point

J30_FIXTURES = (
    J30Point(1, 2, 3, 6, 12, 1, "j30-training-001", "training"),
    J30Point(1, -1, 4, -2, -16, 2, "j30-validation-001", "validation"),
    J30Point(3, 1, 2, -20, 48, -2, "j30-held-out-001", "held_out"),
)

J30_NEGATIVES = (
    J30Point(1, 2, 3, 6, 13, 1, "simple-root", "negative"),
    J30Point(1, 2, -9, -18, 0, 1, "triple-root", "negative"),
    J30Point(1, -1, -1, 2, 3, -1, "resultant-intersection", "negative"),
    J30Point(-1, -2, -2, 4, -2, -1, "a-intersection", "negative"),
    J30Point(1, 2, 0, 0, 9, 1, "j4-intersection", "negative"),
    J30Point(1, 2, 3, 6, 0, 1, "j6-zero", "negative"),
)


def run_j30_v0_3() -> dict[str, Any]:
    fixtures = [certify_j30_point(point) for point in J30_FIXTURES]
    negatives = [
        certify_j30_point(point, include_fibrations=False) for point in J30_NEGATIVES
    ]
    scaled = certify_j30_point(
        J30_FIXTURES[-1].weighted_scale(2),
        include_fibrations=False,
    )
    mutations = {
        "simple_root_rejected": not negatives[0]["passed"],
        "triple_root_rejected": not negatives[1]["passed"],
        "Res_D_E_intersection_rejected": not negatives[2]["passed"],
        "a_zero_intersection_rejected": not negatives[3]["passed"],
        "J4_zero_intersection_rejected": not negatives[4]["passed"],
        "J6_zero_normalization_rejected": not negatives[5]["passed"],
        "oracle_b_required": all(
            certificate["checks"]["oracle_b_disc_d_zero"] for certificate in fixtures
        ),
        "normalization_J6_power_checked": all(
            certificate["oracle_b"]["definition"].endswith("/ J6^16")
            for certificate in fixtures
        ),
        "standard_I2_derived": all(
            any(
                item["fibration"] == "standard"
                and item["root_multiplicity_counts"].get("2") == 1
                for item in certificate["four_fibrations"]
            )
            for certificate in fixtures
        ),
        "alternate_extra_I2_derived": all(
            any(
                item["fibration"] == "alternate"
                and item["root_multiplicity_counts"].get("2") == 3
                for item in certificate["four_fibrations"]
            )
            for certificate in fixtures
        ),
        "maximal_residual_degree_eight": all(
            certificate["four_fibrations"][3]["residual_degree"] == 8
            for certificate in fixtures
        ),
        "weighted_projective_scale_invariant": scaled["passed"],
    }
    passed = (
        all(certificate["passed"] for certificate in fixtures)
        and all(not certificate["passed"] for certificate in negatives)
        and all(mutations.values())
    )
    return {
        "suite": "J30 exact locus v0.3",
        "primary_source": "arXiv:2205.08100v1, Eqs. (2.40), (2.43), (2.44), Table 1",
        "fixtures": fixtures,
        "negative_fixtures": negatives,
        "weighted_scale_check": scaled,
        "mutations": mutations,
        "mutation_detected": sum(mutations.values()),
        "mutation_required": len(mutations),
        "status": "J30_EXACT_LOCUS_PASS" if passed else "J30_FAIL",
        "passed": passed,
        "classification_boundary": (
            "Four known confluences are reproduced. Completeness of the four-fibration "
            "classification remains theorem-dependent."
        ),
    }


def run_stringbench_v0_3(root: Path) -> dict[str, Any]:
    j30 = run_j30_v0_3()
    period = audit_period_oracle(root / "results" / "period_oracle_raw")
    engineering_pass = j30["passed"] and period["passed"]
    scientific = (
        "DUALITY_PARTIAL_STRONGER" if engineering_pass else "DUALITY_PARTIAL"
    )
    return {
        "suite": "String-Compiler Bench v0.3 Special Divisor and Period Oracle Closure",
        "j30": j30,
        "period": period,
        "statuses": {
            "ENGINEERING_STATUS": "ENGINEERING_PASS"
            if engineering_pass
            else "ENGINEERING_PARTIAL",
            "J30_STATUS": j30["status"],
            "PERIOD_ORACLE_STATUS": period["oracle_status"],
            "PERIOD_SLICE_STATUS": period["period_slice_status"],
            "PERIOD_GENERIC_STATUS": period["period_generic_status"],
            "NARAIN_ORBIT_STATUS": "GLOBAL_WILSON_COORDINATE_OBSTRUCTION_CONFIRMED",
            "SCIENTIFIC_STATUS": scientific,
        },
        "known_8d_duality_reproduced": False,
        "duality_round_trip_pass": False,
        "narain_period_bridge_complete": False,
        "allowed_claims": [
            j30["status"],
            period["oracle_status"],
            period["period_slice_status"],
            period["period_generic_status"],
            "GLOBAL_WILSON_COORDINATE_OBSTRUCTION_CONFIRMED",
            scientific,
        ],
        "prohibited_claims": [
            "KNOWN_8D_DUALITY_REPRODUCED",
            "DUALITY_ROUND_TRIP_PASS",
            "STRING_THEORY_COMPLETED",
            "NARAIN_PERIOD_BRIDGE_COMPLETE",
        ],
        "overall_status": scientific,
        "passed": engineering_pass,
        "stopping_reason": (
            "The exact J30 held-out and the marked J4=0 period slice close. Generic "
            "H_(2,2) period inversion and the global Narain-orbit reverse map remain "
            "outside v0.3 and blocked."
        ),
    }
