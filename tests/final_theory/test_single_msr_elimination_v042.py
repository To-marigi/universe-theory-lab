from __future__ import annotations

from pathlib import Path

from universe_lab.final_theory.single_msr_elimination_v042 import (
    MSR_CANDIDATES,
    VERDICT,
    compile_single_msr_source_to_direct_audit_v042,
    semantic_digest,
    write_single_msr_source_to_direct_audit_v042,
)

ROOT = Path(__file__).resolve().parents[2]


def test_source_candidates_are_not_direct_operator_relation_ids() -> None:
    audit = compile_single_msr_source_to_direct_audit_v042(ROOT)
    assert audit["verdict"] == VERDICT
    assert audit["candidate_direct_relation_intersection"] == []
    selection = audit["triangular_scout_selection"]
    assert selection["single_strong_MSR_relations_that_suffice"] == list(MSR_CANDIDATES)
    assert selection["CPOBC_commutator_quotient_dimension"] == 1
    assert audit["direct_system"]["literal_q5_free_strong_MSR_relation_count"] == 21
    assert audit["direct_system"]["direct_relation_record_has_source_constraint_id_field"] is False
    records = audit["triangular_scout_source_candidates"]
    assert [item["source_constraint_id"] for item in records] == list(MSR_CANDIDATES)
    assert all(item["triangular_scout_selected"] is True for item in records)
    assert all(item["mapping_status"] == "PROVENANCE_NOT_PRESENT" for item in records)
    assert all(item["direct_relation_id_present"] is False for item in records)
    assert all("v04_witness_operator_residual" in item for item in records)
    assert all("triangular_scout_operator_residual" not in item for item in records)


def test_audit_rejects_the_false_701_relation_campaign_and_has_no_solver() -> None:
    audit = compile_single_msr_source_to_direct_audit_v042(ROOT)
    campaign = audit["proposed_701_relation_direct_campaign"]
    assert campaign["status"] == "NOT_COMPILED"
    assert campaign["no_false_direct_relation_count_claim"] is True
    assert campaign["solver_invoked"] is False
    assert audit["required_next_stage"]["status"] == "REQUIRED_BEFORE_ANY_701_RELATION_QQ_CAMPAIGN"
    assert audit["semantic_digest_sha256"] == semantic_digest(audit)


def test_write_round_trip(tmp_path: Path) -> None:
    audit = compile_single_msr_source_to_direct_audit_v042(ROOT)
    path = write_single_msr_source_to_direct_audit_v042(tmp_path, audit)
    assert path.relative_to(tmp_path).as_posix() == "results/v0.4.2_source_to_direct_audit.json"
    assert path.read_text(encoding="utf-8").endswith("\n")
