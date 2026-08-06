from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_paper1_claim_boundary_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_v042_paper1_claim_boundary.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "paper1_claim_boundary=OK"


def test_paper1_report_keeps_the_scope_boundary() -> None:
    report = (ROOT / "reports/v0.4.2_paper1_claim_boundary_2026-08-05.md").read_text(
        encoding="utf-8"
    )
    assert "SCOPED_MANUSCRIPT_ASSEMBLY_READY / SUBMISSION_REVIEW_PENDING" in report
    assert "full 955" in report
    assert "resource-open" in report
    assert "complete finite ON semantics lattice" in report
    assert "v0.4.2_sr2v_baseline_observability.json" in report

    addendum = (
        ROOT / "reports/v0.4.2_paper1_editorial_disposition_2026-08-06.md"
    ).read_text(encoding="utf-8")
    assert "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED" in addendum
    assert "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED" in addendum
    assert "supplements rather than rewrites that" in addendum


def test_c2_observability_evidence_pins_the_off_reachable_boundary() -> None:
    ledger = json.loads(
        (ROOT / "results/v0.4.2_paper1_claim_boundary.json").read_text(encoding="utf-8")
    )
    c2 = next(claim for claim in ledger["claims"] if claim["id"] == "C2_SR2_WEAK_WEAK_SEPARATION")
    binding = next(
        item
        for item in c2["evidence"]
        if item["path"] == "results/v0.4.2_sr2v_baseline_observability.json"
    )
    assert binding["raw_sha256"] == (
        "4f57805e871c0589560669c5aa65181c29ca41cdf722420729279945770710de"
    )
    assert binding["semantic_digest"] == (
        "73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62"
    )

    artifact = json.loads(
        (ROOT / "results/v0.4.2_sr2v_baseline_observability.json").read_text(encoding="utf-8")
    )
    assert artifact["reachable_inventory"]["summary"]["reachable_span_rank"] == 1
    assert artifact["baseline_classification"]["reachable_visible"] is False
    records = artifact["commutator_visibility"]["records"]
    assert len(records) == 6
    assert all(record["annihilates_full_reachable_span"] is True for record in records)
    assert all(
        domain["nonzero_action_count"] == 0
        for record in records
        for domain in record["domains"].values()
    )
