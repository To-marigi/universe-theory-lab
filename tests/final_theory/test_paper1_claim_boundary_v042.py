from __future__ import annotations

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
