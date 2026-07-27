import json
from pathlib import Path

from universe_lab.stringbench.benchmarks import run_narain_period_v0_2
from universe_lab.stringbench.narain.branches import derive_branch_certificates
from universe_lab.stringbench.narain.bridge import audit_period_bridge


def test_local_and_global_records_are_separate_types() -> None:
    branches = derive_branch_certificates()
    bridge = audit_period_bridge(branches)
    assert bridge.local_chart_status == "LOCAL_HETEROTIC_LOWERING_PASS"
    assert bridge.global_orbit_status == "GLOBAL_WILSON_COORDINATES_NOT_DEFINED"
    assert all(orbit.period_vector is None for orbit in bridge.orbits)
    assert not bridge.raw_coordinate_round_trip_required


def test_period_oracle_is_not_falsely_promoted() -> None:
    result = run_narain_period_v0_2()
    bridge = result["narain_period_bridge"]
    assert bridge["forward_status"] == "FORWARD_FOUR_FIBRATIONS_PASS"
    assert bridge["period_status"] == "PERIOD_ORACLE_BLOCKED"
    assert bridge["reverse_status"] == "PERIOD_ORACLE_BLOCKED"
    assert result["scientific_status"] == "PARTIAL"
    assert result["overall_status"] == "DUALITY_PARTIAL"
    assert not result["known_8d_duality_reproduced"]


def test_branch_certificates_keep_non_root_metadata() -> None:
    branches = {
        item["branch"]: item["certificate"]
        for item in run_narain_period_v0_2()["local_heterotic_lowering"]["branches"]
    }
    assert "Z/2Z" in branches["alternate"]["gauge_group_global_data"]
    assert (
        branches["alternate"]["b_field_flux_class"]
        != branches["maximal"]["b_field_flux_class"]
    )
    assert "pointlike" in branches["standard"]["pointlike_instanton_behavior"]
    assert "II*" in branches["base_fiber_dual"]["pointlike_instanton_behavior"]


def test_v0_2_schema_is_valid_json() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads(
        (root / "String-Compiler-Bench/specs/narain_period_v0.2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(schema["$defs"]) == {
        "ComplexNumber",
        "WilsonLine",
        "LocalNarainChart",
        "NarainOrbit",
        "K3PeriodPoint",
        "ModularInvariantPoint",
        "HeteroticBranchCertificate",
    }
