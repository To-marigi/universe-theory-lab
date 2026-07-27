from pathlib import Path

from universe_lab.stringbench.benchmarks import run_stringbench_v0_3


def test_v0_3_statuses_and_claim_boundary() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_stringbench_v0_3(root)
    assert result["passed"]
    assert result["statuses"]["J30_STATUS"] == "J30_EXACT_LOCUS_PASS"
    assert result["statuses"]["PERIOD_ORACLE_STATUS"] == "PERIOD_ORACLE_VALIDATED"
    assert result["statuses"]["PERIOD_SLICE_STATUS"] == "PERIOD_J4_SLICE_PASS"
    assert result["statuses"]["PERIOD_GENERIC_STATUS"] == "PERIOD_GENERIC_BLOCKED"
    assert result["overall_status"] == "DUALITY_PARTIAL_STRONGER"
    assert not result["known_8d_duality_reproduced"]
