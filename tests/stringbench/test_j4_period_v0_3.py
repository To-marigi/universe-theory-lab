from __future__ import annotations

import json
from pathlib import Path

from universe_lab.stringbench.j4_period import (
    find_integral_period_marking,
    j4_symbolic_certificate,
)

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "period_oracle_raw"


def test_j4_symbolic_equivalences_and_two_form() -> None:
    certificate = j4_symbolic_certificate()
    assert certificate["passed"]
    assert certificate["checks"]["holomorphic_two_form_preserved"]
    assert certificate["checks"]["J30_nonzero"]


def test_standard_bfd_integral_period_marking_at_256_bits() -> None:
    source = json.loads((RAW / "j4-standard-256.json").read_text(encoding="utf-8"))
    target = json.loads((RAW / "j4-bfd-256.json").read_text(encoding="utf-8"))
    certificate = find_integral_period_marking(source, target)
    assert certificate["passed"]
    assert certificate["determinant"] == 1
    assert certificate["gram_isometry_exact"]
    assert certificate["certified_period_balls_overlap"]


def test_alternate_maximal_integral_period_marking_at_256_bits() -> None:
    source = json.loads((RAW / "j4-alternate-256.json").read_text(encoding="utf-8"))
    target = json.loads((RAW / "j4-maximal-256.json").read_text(encoding="utf-8"))
    certificate = find_integral_period_marking(source, target)
    assert certificate["passed"]
    assert abs(certificate["determinant"]) == 1
