"""Build the first Phase-C claim-boundary and frozen-artifact ledger."""

# ruff: noqa: E501 -- claim text is intentionally kept as atomic ledger strings.

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from universe_lab.artifact_migration_v038 import line_ending_hashes
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

SCHEMA_VERSION = "final-theory-v042-phase-c-claim-boundary-ledger-v1"
VERDICT = "PHASE_C_CLAIM_BOUNDARY_LEDGER_AND_FROZEN_ARTIFACT_INDEX_CERTIFIED"
RESULT_PATH = Path("results/v0.4.2_phase_c_claim_boundary_ledger.json")
REPORT_PATH = Path("reports/v0.4.2_phase_c_claim_boundary_ledger.md")
NEXT_GATE = "AUDIT_VERDICT_GRAMMAR_AND_PREFLIGHT_BUDGET_SEPARATION"


def _files(*paths: str) -> list[str]:
    return list(paths)


GROUP_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "phase_a_termination_decision_packet",
        "scope": "phase_a_cross_profile",
        "classification": "owner_decision_aid",
        "terminality": "predecessor_owner_decision_pending",
        "files": _files(
            "reports/v0.4.2_phase_a_termination_decision_packet.md",
            "results/v0.4.2_phase_a_termination_decision_packet.json",
        ),
        "project_derivations": [
            "The packet aggregates the bounded 955 and 721 evidence available at evidence head 077c721."
        ],
        "unresolved_gaps": [
            "Neither full profile was resolved by this predecessor packet."
        ],
        "forbidden_inferences": [
            "Do not read the recommended freeze as already executed in this predecessor."
        ],
        "predecessors": [],
    },
    {
        "id": "phase_a_freeze_execution",
        "scope": "phase_a_cross_profile",
        "classification": "owner_state_transition",
        "terminality": "owner_approved_resource_limit_boundary",
        "files": _files(
            "reports/v0.4.2_phase_a_freeze_execution.md",
            "results/v0.4.2_phase_a_freeze_execution.json",
        ),
        "project_derivations": [
            "The owner-approved transition freezes 955 and 721 at explicit resource-limit boundaries and starts Phase C."
        ],
        "unresolved_gaps": [
            "Both full one-sided profiles remain mathematically unresolved."
        ],
        "forbidden_inferences": [
            "A resource-limit boundary is not a witness, obstruction, empty-set result, or commutativity theorem."
        ],
        "predecessors": ["phase_a_termination_decision_packet"],
    },
    {
        "id": "phase_c_methodology_charter",
        "scope": "phase_c_methodology",
        "classification": "methodology_control",
        "terminality": "active_charter",
        "files": _files(
            "reports/v0.4.2_phase_c_methodology_charter.md",
            "results/v0.4.2_phase_c_methodology_charter.json",
        ),
        "project_derivations": [
            "Phase C requires semantic identity, claim boundaries, verdict grammar, frozen-artifact invariance, and budget separation."
        ],
        "unresolved_gaps": [
            "The charter itself adds no scientific verdict."
        ],
        "forbidden_inferences": [
            "Do not use Phase C methodology work to reopen 955 or 721 implicitly."
        ],
        "predecessors": ["phase_a_freeze_execution"],
    },
    {
        "id": "phase_c_state_reconciliation",
        "scope": "phase_c_methodology",
        "classification": "mutable_index_correction_record",
        "terminality": "prestart_control_complete",
        "files": _files(
            "reports/v0.4.2_phase_c_state_reconciliation_2026-08-14.md",
            "results/v0.4.2_phase_c_state_reconciliation_2026-08-14.json",
        ),
        "project_derivations": [
            "Stale pending and not-yet-done fields were reconciled in the mutable live index without rewriting historical evidence."
        ],
        "unresolved_gaps": [
            "The reconciliation changes no scientific claim."
        ],
        "forbidden_inferences": [
            "Do not treat a live-index cleanup as a new proof certificate."
        ],
        "predecessors": ["phase_c_methodology_charter"],
    },
    {
        "id": "955_localized_row_module_preflight",
        "scope": "955_strong_GC_reachable_state_MSR",
        "classification": "exact_nonterminal_preflight",
        "terminality": "nonterminal_evidence",
        "files": _files(
            "reports/v0.4.2_955_localized_row_module_preflight.md",
            "results/v0.4.2_955_localized_row_module_preflight.json",
        ),
        "project_derivations": [
            "The localized row-module formulation identifies a finite minor-cover obligation."
        ],
        "unresolved_gaps": ["No finite cover or full 955 theorem is certified."],
        "forbidden_inferences": [
            "A preflight formulation is not row-module membership or a global obstruction."
        ],
        "predecessors": [],
    },
    {
        "id": "955_minor_cover_preflight",
        "scope": "955_strong_GC_reachable_state_MSR",
        "classification": "exact_nonterminal_preflight",
        "terminality": "nonterminal_evidence",
        "files": _files(
            "reports/v0.4.2_955_minor_cover_preflight.md",
            "results/v0.4.2_955_minor_cover_preflight.json",
        ),
        "project_derivations": [
            "A finite sample found a 107-of-119 monomial matching and a two-minor sample cover."
        ],
        "unresolved_gaps": ["The finite sample is not a certified global cover."],
        "forbidden_inferences": [
            "Do not promote sampled minor coverage to a theorem over the full stratum."
        ],
        "predecessors": ["955_localized_row_module_preflight"],
    },
    {
        "id": "955_unit_pivot_matching",
        "scope": "955_strong_GC_reachable_state_MSR",
        "classification": "exact_nonterminal_matching",
        "terminality": "nonterminal_evidence",
        "files": _files(
            "reports/v0.4.2_955_unit_pivot_matching.md",
            "results/v0.4.2_955_unit_pivot_matching.json",
        ),
        "project_derivations": [
            "All 111 required non-Q columns admit distinct unit-edge matches after source-determinant localization."
        ],
        "unresolved_gaps": ["A unit determinant for the selected 111-by-111 minor is not certified."],
        "forbidden_inferences": [
            "A perfect matching of unit entries does not imply that the signed determinant is a unit."
        ],
        "predecessors": ["955_minor_cover_preflight"],
    },
    {
        "id": "955_block_determinant",
        "scope": "955_strong_GC_reachable_state_MSR",
        "classification": "exact_nonterminal_route_boundary",
        "terminality": "supports_owner_resource_limit_boundary",
        "files": _files(
            "reports/v0.4.2_955_block_determinant.md",
            "results/v0.4.2_955_block_determinant.json",
        ),
        "project_derivations": [
            "The DM decomposition has 60 components, largest size 15, and the 19 evaluated small-block determinants are non-units carrying ten new factors."
        ],
        "unresolved_gaps": [
            "Alternative row selections remain mathematically possible; the route is not proved impossible."
        ],
        "forbidden_inferences": [
            "Do not interpret failure of this unit-minor route as full-profile obstruction."
        ],
        "predecessors": ["955_unit_pivot_matching"],
    },
    {
        "id": "721_inverse_token_incidence",
        "scope": "721_fixed_vector_GC_strong_MSR",
        "classification": "exact_correction_and_nonterminal_measurement",
        "terminality": "nonterminal_evidence",
        "files": _files(
            "reports/v0.4.2_721_inverse_token_incidence.md",
            "results/v0.4.2_721_inverse_token_incidence.json",
        ),
        "project_derivations": [
            "1961 of 1967 nonzero residuals contain inverse tokens; 21 of 24 strong-MSR residuals contain them."
        ],
        "unresolved_gaps": ["Incidence alone gives no elimination or commutativity result."],
        "forbidden_inferences": [
            "Do not revive the corrected claim that MSR words contain no inverse tokens."
        ],
        "predecessors": [],
    },
    {
        "id": "721_inverse_relation_reduction_cpobc_msr",
        "scope": "721_fixed_vector_GC_strong_MSR",
        "classification": "exact_exhaustive_nonterminal_reduction",
        "terminality": "nonterminal_evidence",
        "files": _files(
            "reports/v0.4.2_721_inverse_relation_reduction_cpobc_msr.md",
            "results/v0.4.2_721_inverse_relation_reduction_cpobc_msr.json",
        ),
        "project_derivations": [
            "Exact single-token defining-relation reduction closes zero of 700 CPOBC and 21 strong-MSR nonzero residuals."
        ],
        "unresolved_gaps": [
            "This confluent single-relation reduction is not a full cross-relation Gröbner elimination."
        ],
        "forbidden_inferences": [
            "Zero newly-zero residuals under this reduction is not a witness or obstruction."
        ],
        "predecessors": ["721_inverse_token_incidence"],
    },
    {
        "id": "721_gc_relation_reduction",
        "scope": "721_fixed_vector_GC_strong_MSR",
        "classification": "exact_exhaustive_nonterminal_reduction",
        "terminality": "nonterminal_evidence",
        "files": _files(
            "reports/v0.4.2_721_gc_tier_relation_reduced.md",
            *[
                f"results/v0.4.2_721_gc_tier{tier:02d}_relation_reduced.json"
                for tier in (3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 25)
            ],
        ),
        "project_derivations": [
            "All 1529 fixed-vector GC pairs were reduced tier by tier; zero new pairs vanished and 1246 remained nonzero."
        ],
        "unresolved_gaps": [
            "The tiered reduction does not decide the full ideal or commutativity."
        ],
        "forbidden_inferences": [
            "Exhaustiveness over this reduction rule is not exhaustiveness over all algebraic consequences."
        ],
        "predecessors": ["721_inverse_relation_reduction_cpobc_msr"],
    },
    {
        "id": "721_corrected_groebner_preflight",
        "scope": "721_fixed_vector_GC_strong_MSR",
        "classification": "bounded_corrected_preflight",
        "terminality": "supports_owner_resource_limit_boundary",
        "files": _files(
            "reports/v0.4.2_721_groebner_preflight.md",
            "scripts/build_v042_721_groebner_residual_cache.py",
            "scripts/probe_v042_721_groebner_preflight_worker.py",
            "scripts/run_v042_721_groebner_preflight.py",
            "tests/final_theory/test_v042_721_groebner_preflight.py",
        ),
        "project_derivations": [
            "The corrected complete-residual-unit probe took 1.078 seconds for one unit and timed out at 90 seconds for two units under current SymPy tooling."
        ],
        "unresolved_gaps": [
            "No full-profile solver was run, and dedicated-CAS impossibility is not proved."
        ],
        "forbidden_inferences": [
            "Do not extrapolate the bounded probe into a universal runtime or impossibility theorem."
        ],
        "predecessors": ["721_gc_relation_reduction"],
    },
)


CORRECTIONS: tuple[dict[str, str], ...] = (
    {
        "id": "721_inverse_token_presence_correction",
        "authority_group": "721_inverse_token_incidence",
        "incorrect_claim": "strong-MSR words contain no inverse tokens",
        "corrected_claim": "21 of 24 strong-MSR residuals contain inverse tokens; unchanged term counts arise from monomial-to-monomial substitution",
    },
    {
        "id": "721_groebner_residual_unit_correction",
        "authority_group": "721_corrected_groebner_preflight",
        "superseded_commit": "e989dff",
        "correcting_commit": "077c721",
        "incorrect_claim": "individual scalar entries were reported as complete residual counts",
        "corrected_claim": "the corrected preflight passes every nonzero scalar entry of each complete 2-by-2 residual unit together",
    },
)


def _bind_file(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    hashes = line_ending_hashes(path, require_canonical_lf=True)
    binding: dict[str, Any] = {
        "path": relative_path,
        "kind": (
            "machine_evidence"
            if path.suffix == ".json"
            else "human_report"
            if path.suffix == ".md"
            else "reproducer_or_test"
        ),
        "raw_sha256": hashes["current_raw_sha256"],
        "canonical_lf_sha256": hashes["canonical_lf_sha256"],
        "size_bytes": hashes["current_raw_size_bytes"],
        "strict_utf8_lf": True,
    }
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        semantic_digest = payload.pop("semantic_digest_sha256", None)
        if semantic_digest is None:
            raise ValueError(f"missing semantic_digest_sha256: {relative_path}")
        if stable_hash(payload) != semantic_digest:
            raise ValueError(f"semantic digest mismatch: {relative_path}")
        binding.update(
            {
                "schema_version": payload.get("schema_version"),
                "verdict_or_status": payload.get("verdict", payload.get("status")),
                "semantic_digest_sha256": semantic_digest,
                "semantic_digest_verified": True,
            }
        )
    return binding


def build_ledger(root: Path) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    duplicate_paths: set[str] = set()
    group_ids = {str(spec["id"]) for spec in GROUP_SPECS}
    unknown_predecessors = sorted(
        {
            str(predecessor)
            for spec in GROUP_SPECS
            for predecessor in spec["predecessors"]
            if predecessor not in group_ids
        }
    )
    if unknown_predecessors:
        raise ValueError(f"unknown predecessor groups: {unknown_predecessors}")
    for spec in GROUP_SPECS:
        bindings = []
        for relative_path in spec["files"]:
            if relative_path in seen_paths:
                duplicate_paths.add(relative_path)
            seen_paths.add(relative_path)
            bindings.append(_bind_file(root, relative_path))
        groups.append(
            {
                "id": spec["id"],
                "scope": spec["scope"],
                "classification": spec["classification"],
                "terminality": spec["terminality"],
                "claim_layers": {
                    "external_source_claims": [],
                    "project_derivations": spec["project_derivations"],
                    "unresolved_gaps": spec["unresolved_gaps"],
                },
                "forbidden_inferences": spec["forbidden_inferences"],
                "predecessor_group_ids": spec["predecessors"],
                "files": bindings,
            }
        )

    mission = _bind_file(root, "MISSION.md")
    state = json.loads((root / "CURRENT_RESEARCH_STATE.json").read_text(encoding="utf-8"))
    charter = json.loads(
        (root / "results/v0.4.2_phase_c_methodology_charter.json").read_text(
            encoding="utf-8"
        )
    )
    decision_packet = json.loads(
        (root / "results/v0.4.2_phase_a_termination_decision_packet.json").read_text(
            encoding="utf-8"
        )
    )
    freeze_record = json.loads(
        (root / "results/v0.4.2_phase_a_freeze_execution.json").read_text(
            encoding="utf-8"
        )
    )
    required_path_sets = {
        "charter_frozen_inputs": sorted(
            {str(record["path"]) for record in charter["frozen_inputs"]}
        ),
        "decision_packet_evidence": sorted(
            {
                str(path)
                for profile in decision_packet["profiles"].values()
                for path in profile["evidence"]
            }
        ),
        "freeze_record_evidence": sorted(
            {
                str(profile[key])
                for profile in freeze_record["profiles"].values()
                for key in ("evidence_report", "evidence_artifact")
            }
        ),
    }
    missing_required_paths = {
        name: sorted(set(paths) - seen_paths)
        for name, paths in required_path_sets.items()
    }
    if any(missing_required_paths.values()):
        raise ValueError(f"unindexed required evidence: {missing_required_paths}")
    machine_bindings = [
        binding
        for group in groups
        for binding in group["files"]
        if binding["kind"] == "machine_evidence"
    ]
    all_bindings = [binding for group in groups for binding in group["files"]]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": "2026-08-14",
        "evidence_head": "1211595",
        "status": VERDICT,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "complete_finite_on_semantics_lattice_claim_available": False,
        "authorities": {
            "mission_snapshot": mission,
            "live_state": {
                "path": "CURRENT_RESEARCH_STATE.json",
                "binding": "mutable_live_authority_not_frozen",
                "schema_version": state["schema_version"],
                "mutable_index_not_a_proof_certificate": state[
                    "mutable_index_not_a_proof_certificate"
                ],
                "global_verdict": state["global_verdict"],
            },
        },
        "verdict_grammar": {
            "OPEN_RESOURCE_LIMIT": {
                "means": "the declared route stopped at a recorded resource or finite-theorem-path boundary",
                "does_not_mean": [
                    "witness certified",
                    "obstruction proved",
                    "empty solution set",
                    "commutativity proved",
                    "solver impossibility proved",
                ],
            },
            "PREFLIGHT": {
                "means": "a bounded feasibility or structure measurement",
                "does_not_mean": ["authorized production solver campaign", "full-profile result"],
            },
            "CERTIFIED": {
                "means": "machine-checked only within the artifact's explicit scope and claim boundary",
                "does_not_mean": ["automatic promotion to a broader profile"],
            },
        },
        "correction_records": list(CORRECTIONS),
        "coverage_controls": {
            "required_path_sets": required_path_sets,
            "missing_required_paths": missing_required_paths,
            "all_charter_frozen_inputs_indexed": not missing_required_paths[
                "charter_frozen_inputs"
            ],
            "all_decision_packet_evidence_indexed": not missing_required_paths[
                "decision_packet_evidence"
            ],
            "all_freeze_record_evidence_indexed": not missing_required_paths[
                "freeze_record_evidence"
            ],
            "all_predecessor_group_ids_valid": not unknown_predecessors,
        },
        "artifact_groups": groups,
        "inventory_summary": {
            "group_count": len(groups),
            "file_binding_count": len(all_bindings),
            "machine_evidence_count": len(machine_bindings),
            "all_paths_unique": not duplicate_paths,
            "duplicate_paths": sorted(duplicate_paths),
            "all_frozen_files_strict_utf8_lf": all(
                binding["strict_utf8_lf"] for binding in all_bindings
            ),
            "all_machine_semantic_digests_verified": all(
                binding["semantic_digest_verified"] for binding in machine_bindings
            ),
            "self_reference_excluded": True,
            "mutable_live_state_excluded_from_raw_freeze": True,
        },
        "phase_a_boundaries": {
            "955": "REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT",
            "721": "FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT",
            "both_full_profiles_resolved": False,
        },
        "next_gate": NEXT_GATE,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["inventory_summary"]
    rows = []
    for group in payload["artifact_groups"]:
        rows.append(
            "| `{}` | `{}` | `{}` | {} |".format(
                group["id"],
                group["scope"],
                group["terminality"],
                len(group["files"]),
            )
        )
    corrections = []
    for correction in payload["correction_records"]:
        corrections.append(
            f"- `{correction['id']}`: {correction['incorrect_claim']} → "
            f"{correction['corrected_claim']}"
        )
    return "\n".join(
        [
            "# Phase C claim-boundary ledger and frozen-artifact index",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The first substantive Phase-C gate is complete. The ledger binds the",
            "Phase-A decision/freeze chain, the exact 955 route boundary, the complete",
            "721 single-relation reduction evidence, and the corrected bounded Gröbner",
            "preflight without adding a scientific verdict.",
            "",
            f"- Artifact groups: **{summary['group_count']}**",
            f"- Frozen file bindings: **{summary['file_binding_count']}**",
            f"- Machine evidence objects with verified semantic digests: **{summary['machine_evidence_count']}**",
            "- Every input named by the Phase-C charter, Phase-A decision packet, and",
            "  freeze execution record is covered by the index.",
            "- Every frozen text file is strict UTF-8 LF.",
            "- `CURRENT_RESEARCH_STATE.json` is recorded as a mutable authority and is",
            "  deliberately excluded from the raw-byte freeze to avoid a self-referential",
            "  state update.",
            "",
            "## Indexed groups",
            "",
            "| group | scope | terminality | files |",
            "|---|---|---|---:|",
            *rows,
            "",
            "## Claim boundary",
            "",
            "- 955 remains unresolved beyond `REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT`.",
            "- 721 remains unresolved beyond `FIXED_VECTOR_GC_STRONG_MSR_OPEN_RESOURCE_LIMIT`.",
            "- `FINAL_THEORY_OPEN` remains the global verdict.",
            "- No complete finite ON semantics lattice, witness, obstruction, empty-set",
            "  result, full-profile solver result, or dedicated-CAS impossibility is claimed.",
            "- `OPEN_RESOURCE_LIMIT`, `PREFLIGHT`, and scoped `CERTIFIED` meanings are",
            "  recorded machine-readably in the result JSON.",
            "",
            "## Corrections preserved",
            "",
            *corrections,
            "",
            "## Integrity model",
            "",
            "Each JSON evidence member is checked in two distinct ways: raw/canonical-LF",
            "SHA-256 binds its tracked bytes, while its existing semantic digest is",
            "recomputed after removing `semantic_digest_sha256`. Markdown, scripts, and",
            "tests receive raw and canonical-LF bindings. The ledger excludes its own",
            "output files, so its semantic digest has no self-reference.",
            "",
            "## Next gate",
            "",
            f"`{payload['next_gate']}`",
            "",
            "This next gate audits verdict-string usage and the separation between",
            "preflight measurements, versioned budgets, and authorized solver runs.",
            "",
        ]
    )


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
    result_path = root / RESULT_PATH
    report_path = root / REPORT_PATH
    result_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_report(payload))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_ledger(args.root)
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked Phase-C ledger differs from rebuilt payload")
        tracked_report = (args.root / REPORT_PATH).read_text(encoding="utf-8")
        if tracked_report != render_report(payload):
            raise SystemExit("tracked Phase-C report differs from rebuilt report")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
