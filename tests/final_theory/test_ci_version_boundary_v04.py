"""Fail-closed checks for the current-v0.4 versus frozen-v0.3.9 CI boundary."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/ci.yml"
PUBLIC_V039_COMMIT = "cba86eae795e1e985c4ba1bcd3dabe4eb2773fab"
HISTORICAL_TEST_FILES = (
    "tests/final_theory/test_reproduce_v037.py",
    "tests/final_theory/test_line_ending_bridge_v038.py",
    "tests/final_theory/test_reproduce_v038.py",
    "tests/final_theory/test_reproduce_v039.py",
)
FROZEN_RAW_SHA256 = {
    "results/v0.3.8_line_ending_bridge.json": (
        "0d35acd7cb5e7d9af700e1cc793b12ba74dc41d9b93062948a0ef7faba8a28c6"
    ),
    "results/v0.3.9_release_manifest.json": (
        "02e75a35c2d062e9017905c3da66b365f8c0f7907346027802affd283eabe516"
    ),
}


def test_current_ci_lane_verifies_v04_and_isolates_release_relative_tests() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    current_lane, historical_lane = workflow.split("\n  historical-v039:\n", maxsplit=1)

    assert "uv run python scripts/reproduce_v04.py" in current_lane
    assert "uv run python scripts/reproduce_v039.py" not in current_lane
    for path in HISTORICAL_TEST_FILES:
        assert f"--ignore={path}" in current_lane
        assert path in historical_lane


def test_historical_ci_lane_is_pinned_to_the_public_v039_source_commit() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    historical_lane = workflow.split("\n  historical-v039:\n", maxsplit=1)[1]

    assert f"ref: {PUBLIC_V039_COMMIT}" in historical_lane
    assert "fetch-depth: 0" in historical_lane
    assert "uv run python scripts/reproduce_v039.py" in historical_lane
    assert "build_v038_line_ending_bridge.py" not in workflow


def test_public_release_ledgers_remain_byte_frozen() -> None:
    observed = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in FROZEN_RAW_SHA256
    }
    assert observed == FROZEN_RAW_SHA256
