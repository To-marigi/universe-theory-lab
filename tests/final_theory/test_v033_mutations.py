from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from universe_lab.final_theory.cpobc_q_presentation_v033 import (
    critical_mutation_matrix_v033,
    production_oracle_summary,
)

ROOT = Path(__file__).resolve().parents[2]
ORACLE_PATH = ROOT / "oracle" / "cpobc_gc_atomisation_v033_oracle.py"


def _load_oracle() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "cpobc_gc_atomisation_v033_independent_oracle",
        ORACLE_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_all_twenty_required_critical_mutations_are_detected() -> None:
    result = critical_mutation_matrix_v033()
    assert result["passed"]
    assert result["verdict"] == "ALL_CRITICAL_MUTATIONS_DETECTED"
    assert result["counts"] == {"required": 20, "detected": 20}
    assert len(result["mutations"]) == 20
    assert all(mutation["detected"] for mutation in result["mutations"])


def test_independent_oracle_has_no_production_import() -> None:
    source = ORACLE_PATH.read_text(encoding="utf-8")
    assert "from universe_lab" not in source
    assert "import universe_lab" not in source


def test_independent_oracle_matches_the_full_semantic_digest() -> None:
    oracle = _load_oracle()
    production = production_oracle_summary()
    result = oracle.run_oracle(production)
    assert result["passed"]
    assert result["verdict"] == "INDEPENDENT_ORACLE_COMPLETE_MATCH_N4"
    assert result["production_comparison"]["semantic_digest_match"]
    assert result["production_comparison"]["mismatched_sections"] == []
    assert (
        result["semantic_summary"]["semantic_digest_sha256"]
        == production["semantic_digest_sha256"]
    )
