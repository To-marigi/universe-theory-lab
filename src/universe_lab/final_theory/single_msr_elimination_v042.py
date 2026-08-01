"""Fail-closed provenance audit for the proposed v0.4.2 single-MSR campaign.

The v0.4 triangular scout names three *source-stage* MSR constraints.  The
frozen Q5-free direct-operator system used by the 21-chart Sage worker instead
contains 21 reduced relation IDs at stages three and four.  No accepted map
from the former to a single direct relation is present.  This module records
that boundary without scheduling a solver or pretending that a 701-relation
direct system exists.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_AUDIT = "final-theory-single-strong-msr-source-to-direct-audit-v0.4.2"
VERSION = "0.4.2"
VERDICT = "V042_SOURCE_TO_DIRECT_PROVENANCE_REQUIRED"
MSR_CANDIDATES = ("msr:p1-0", "msr:p2-0", "msr:p2-2")
INVENTORY_PATH = "results/v0.4.1_one_sided_inventory.json"
WEAK_PATH = "results/v0.4_weak_d2_classification.json"
CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
DIRECT_SYSTEM_PATH = "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
BACKEND_PATH = "src/universe_lab/final_theory/d2_sage_backend_v035.py"
RESULT_PATH = "results/v0.4.2_source_to_direct_audit.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_digest(payload: dict[str, Any]) -> str:
    return stable_hash(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def _bound_sources(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    paths = (INVENTORY_PATH, WEAK_PATH, CPOBC_PATH, DIRECT_SYSTEM_PATH, BACKEND_PATH)
    missing = [relative for relative in paths if not (root / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"v0.4.2 provenance audit is missing frozen inputs: {missing}")
    hashes = {relative: _sha256(root / relative) for relative in paths}
    inventory = _load(root / INVENTORY_PATH)
    if inventory.get("schema_version") != "final-theory-one-sided-d2-v0.4.1":
        raise ValueError("unexpected v0.4.1 inventory schema")
    if inventory.get("semantic_digest_sha256") != semantic_digest(inventory):
        raise ValueError("v0.4.1 inventory semantic digest does not recompute")
    for relative in (WEAK_PATH, CPOBC_PATH, DIRECT_SYSTEM_PATH):
        expected = inventory.get("source_artifacts", {}).get(relative)
        if expected != hashes[relative]:
            raise ValueError(f"frozen source hash does not match v0.4.1 inventory: {relative}")
    return {
        "inventory": inventory,
        "weak": _load(root / WEAK_PATH),
        "cpobc": _load(root / CPOBC_PATH),
        "direct": _load(root / DIRECT_SYSTEM_PATH),
    }, hashes


def compile_single_msr_source_to_direct_audit_v042(root: Path) -> dict[str, Any]:
    """Compile the exact provenance audit, with no Sage/Singular side effect."""

    root = root.resolve()
    sources, hashes = _bound_sources(root)
    inventory, weak, cpobc, direct = (
        sources["inventory"],
        sources["weak"],
        sources["cpobc"],
        sources["direct"],
    )
    direct_semantic = stable_hash(
        {
            "dependency_nodes": direct["dependency_nodes"],
            "relations": direct["relations"],
            "transitions": direct["reconstructed_transition_predicates"],
        }
    )
    if direct.get("semantic_digest_sha256") != direct_semantic:
        raise ValueError("frozen direct-system semantic digest does not recompute")
    triangular = weak["minimal_semantic_recovery"]["triangular_ansatz_local_result"]
    selected_candidates = triangular["single_strong_MSR_relations_that_suffice"]
    if selected_candidates != list(MSR_CANDIDATES):
        raise ValueError("v0.4 triangular scout candidate list no longer matches the v0.4.2 scope")
    source_constraints = {
        record["constraint_id"]: record for record in cpobc["MSR_operator_constraints"]
    }
    if len(source_constraints) != 24 or set(MSR_CANDIDATES) - set(source_constraints):
        raise ValueError("v0.4 triangular-scout source MSR candidates no longer match CPOBC")
    witness_records = {
        record["constraint_id"]: record for record in weak["direct_substitution"]["MSR"]["records"]
    }
    direct_records = direct["relations"]["LITERAL_PRINTED_QN_PLUS_1_BRANCH"]
    direct_msr_ids = sorted(
        record["relation_id"]
        for record in direct_records
        if record["family"] == "STRONG_OPERATOR_MSR"
    )
    if len(direct_msr_ids) != 21:
        raise ValueError("frozen direct system no longer has 21 Q5-free strong-MSR relations")
    direct_record_keys = set().union(*(set(record) for record in direct_records))
    candidate_records: list[dict[str, Any]] = []
    for candidate in MSR_CANDIDATES:
        source = source_constraints[candidate]
        witness = witness_records.get(candidate)
        if witness is None or witness.get("strong_operator_zero") is not False:
            raise ValueError(f"v0.4 witness direct substitution no longer identifies {candidate}")
        candidate_records.append(
            {
                "source_constraint_id": candidate,
                "source_id": source["source_id"],
                "source_stage": int(source["source_id"].split("-")[0][1:]),
                "source_term_count": len(source["terms"]),
                "source_identity_coefficient": source["identity_coefficient"],
                "source_matrix_entry_equation_count_d3": source["entry_equation_count"],
                "triangular_scout_selected": True,
                "v04_witness_operator_residual": witness["operator_residual"],
                "v04_witness_strong_operator_zero": witness["strong_operator_zero"],
                "direct_relation_id_present": candidate in direct_msr_ids,
                "accepted_source_to_direct_relation_id": None,
                "mapping_status": "PROVENANCE_NOT_PRESENT",
            }
        )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_AUDIT,
        "version": VERSION,
        "finite_scope": "ON quotient; n<=4; d=2; static provenance audit only",
        "source_artifacts": hashes,
        "inventory": {
            "path": INVENTORY_PATH,
            "semantic_digest_sha256": inventory["semantic_digest_sha256"],
        },
        "direct_system": {
            "path": DIRECT_SYSTEM_PATH,
            "file_sha256": hashes[DIRECT_SYSTEM_PATH],
            "semantic_digest_sha256": direct_semantic,
            "literal_q5_free_strong_MSR_relation_ids": direct_msr_ids,
            "literal_q5_free_strong_MSR_relation_count": len(direct_msr_ids),
            "direct_relation_record_has_source_constraint_id_field": (
                "source_constraint_id" in direct_record_keys
            ),
        },
        "triangular_scout_selection": {
            "source_path": (
                "minimal_semantic_recovery.triangular_ansatz_local_result."
                "single_strong_MSR_relations_that_suffice"
            ),
            "single_strong_MSR_relations_that_suffice": selected_candidates,
            "CPOBC_commutator_quotient_dimension": triangular[
                "CPOBC_commutator_quotient_dimension"
            ],
            "claim_boundary": triangular["claim_boundary"],
        },
        "triangular_scout_source_candidates": candidate_records,
        "candidate_direct_relation_intersection": sorted(set(MSR_CANDIDATES) & set(direct_msr_ids)),
        "proposed_701_relation_direct_campaign": {
            "status": "NOT_COMPILED",
            "reason": (
                "The three candidate IDs identify source-stage matrix constraints, not "
                "relation IDs selectable by the frozen direct-operator worker."
            ),
            "no_false_direct_relation_count_claim": True,
            "solver_invoked": False,
            "finite_field_fallback_permitted": False,
        },
        "required_next_stage": {
            "status": "REQUIRED_BEFORE_ANY_701_RELATION_QQ_CAMPAIGN",
            "work_items": [
                "Compile a source-stage-to-Q direct lift for each named MSR constraint.",
                "Record a one-to-one-or-many provenance map and exact expression digest.",
                "Extend the Sage worker input contract to select lifted source constraints.",
                "Bind localisation, commutator coverage, memory limit, and result digest "
                "after the lift.",
            ],
            "backend_current_contract": "DIRECT_REDUCED_OPERATOR_WORDS_ONLY",
            "backend_source_sha256": hashes[BACKEND_PATH],
        },
        "verdict": VERDICT,
        "passed": True,
        "claim_boundary": (
            "This audit neither proves nor refutes one-relation sufficiency. It proves only "
            "that the proposed direct 701-relation campaign lacks required provenance."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def write_single_msr_source_to_direct_audit_v042(root: Path, payload: dict[str, Any]) -> Path:
    """Write the static audit with canonical UTF-8/LF formatting."""

    path = root.resolve() / RESULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
