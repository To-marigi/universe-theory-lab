from __future__ import annotations

import json
from pathlib import Path

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_active_candidate_manifest_v042 import (
    REPORT_PATH,
    RESULT_PATH,
    build_manifest,
    render_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> dict[str, object]:
    return json.loads((ROOT / RESULT_PATH).read_text(encoding="utf-8"))


def test_active_candidate_manifest_rebuilds_exactly() -> None:
    assert build_manifest(ROOT) == _tracked()
    assert (ROOT / REPORT_PATH).read_text(encoding="utf-8") == render_report(
        _tracked()
    )


def test_active_candidate_manifest_freezes_v2_without_relabeling_v1() -> None:
    payload = _tracked()
    digest = payload.pop("semantic_digest_sha256")

    assert stable_hash(payload) == digest
    assert payload["active_candidate"]["id"] == "causal_information_v2_sparse_kraus"
    assert payload["predecessor_boundary"]["id"] == "causal_information_v1"
    assert payload["predecessor_boundary"][
        "equivalence_to_active_candidate_certified"
    ] is False
    assert payload["predecessor_boundary"][
        "evidence_transfer_to_active_candidate"
    ] is False
    assert payload["measurement_boundary"]["sampling_authorized_by_manifest"] is False
    assert payload["all_acceptance_checks_passed"] is True
