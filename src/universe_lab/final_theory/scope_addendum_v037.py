"""Generate the v0.3.7 claim-scope correction without mutating frozen results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.q5_free_elimination_v037 import (
    BUDGET_PATH,
    SCOUT_MODULI,
    VERDICT_PROVED,
    _campaign_chart_id,
    _core_s1_s2_charts,
    _qq_resolves_noncommutativity,
    _s3_structural_certificate,
)

BRANCH = "codex/final-theory-v0.3.7-publication-20260729"
SCHEMA = "final-theory-scope-addendum-v0.3.7"
RESULT_PATH = "results/v0.3.7_scope_addendum.json"
REPORT_PATH = "reports/v0.3.7_scope_addendum.md"
VERDICT = "V037_SCOPE_ADDENDUM_CERTIFIED"

V034_SYSTEM = "results/v0.3.4_polynomial_systems.json"
V035_STAGE3 = "results/v0.3.5_stage3_subset_campaign.json"
V035_FULL = "results/v0.3.5_full_stage4_campaign.json"
V035_CLASSIFICATION = "results/v0.3.5_d2_classification.json"
V036_CENSUS = "results/v0.3.6_q5_constraint_census.json"
V036_VACUITY = "results/v0.3.6_q5_vacuity_proof.json"
V037_PARTITION = "results/v0.3.7_q5_free_partition.json"
V037_ELIMINATION = "results/v0.3.7_q5_free_elimination.json"

FROZEN_SHA256 = {
    V034_SYSTEM: (
        "018c1dccc4e08102c6de1fbdd9baf6e8e89dcf818e302ebb175e23e59f5a1283"
    ),
    V035_STAGE3: (
        "392c4b683e672468ec6c6d27d843edc69c3fc4fc728f6bf3fdb2775c1acf3299"
    ),
    V035_FULL: (
        "5295236d165d052c5d57a6fb2be7b9defab7a358fa8018e854c962c5fe667956"
    ),
    V035_CLASSIFICATION: (
        "59abc7d234e6a814206c72beec851a7fc08c4082ce2452ed38f29b76a257c342"
    ),
    V036_CENSUS: (
        "6454bd06f373e9e3a04faba2c59f435acd3cfba0d20c167863438e243a6860ca"
    ),
    V036_VACUITY: (
        "67ad76c98d9a39a5b182267d59e93f4d80af25203c77c28c2265e3efed9097fb"
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _v037_integrity(
    root: Path,
    partition: dict[str, Any],
    elimination: dict[str, Any],
) -> dict[str, Any]:
    partition_path = root / V037_PARTITION
    elimination_path = root / V037_ELIMINATION
    source_hashes_match = all(
        (root / path).is_file()
        and _sha256(root / path) == expected
        for path, expected in partition["source_artifacts"].items()
    )
    run_records: list[dict[str, Any]] = []
    certificate_projections: list[dict[str, Any]] = []
    for run in elimination.get("runs", []):
        relative = run.get("certificate")
        path = root / relative if isinstance(relative, str) else None
        exists = path is not None and path.is_file()
        actual_sha = _sha256(path) if exists and path is not None else None
        certificate = (
            _load_json(path)
            if exists and path is not None
            else {}
        )
        projection = {
            "chart": certificate.get("chart"),
            "chart_cover_id": certificate.get("chart_cover_id"),
            "stratum": certificate.get("stratum"),
            "coefficient_field": certificate.get("coefficient_field"),
            "exit_status": certificate.get("exit_status"),
            "chart_verdict": certificate.get("chart_verdict"),
            "proof_eligible": certificate.get("proof_eligible", False),
            "selected_canonical_equation_count": certificate.get(
                "selected_canonical_equation_count"
            ),
            "selected_matrix_relation_count": certificate.get(
                "selected_matrix_relation_count"
            ),
            "selected_denominator_record_count": certificate.get(
                "selected_denominator_record_count"
            ),
            "canonical_selection_checks_passed": certificate.get(
                "canonical_selection_checks_passed", False
            ),
            "saturated_unit_ideal": certificate.get(
                "saturated_unit_ideal", False
            ),
            "final_localisation_complete": certificate.get(
                "final_localisation_complete", False
            ),
            "commutator_component_count": certificate.get(
                "commutator_component_count"
            ),
            "covered_commutator_component_count": certificate.get(
                "covered_commutator_component_count"
            ),
            "commutator_coverage_complete": certificate.get(
                "commutator_coverage_complete", False
            ),
            "surviving_noncommutative_component_count": certificate.get(
                "surviving_noncommutative_component_count"
            ),
            "peak_rss_bytes": certificate.get("resource_usage", {}).get(
                "peak_rss_bytes"
            ),
            "memory_budget_satisfied": certificate.get(
                "resource_usage", {}
            ).get("memory_budget_satisfied", False),
            "budget_file_sha256": certificate.get(
                "budget_file_sha256"
            ),
            "request_semantic_digest_sha256": certificate.get(
                "request_semantic_digest_sha256"
            ),
            "semantic_digest_sha256": certificate.get(
                "semantic_digest_sha256"
            ),
        }
        summary_mismatches = sorted(
            key
            for key, value in projection.items()
            if run.get(key) != value
        )
        if exists:
            certificate_projections.append(projection)
        run_records.append(
            {
                "path": relative,
                "recorded_sha256": run.get("certificate_sha256"),
                "actual_sha256": actual_sha,
                "sha256_matches": (
                    exists
                    and actual_sha == run.get("certificate_sha256")
                ),
                "semantic_digest_matches": (
                    exists
                    and certificate.get("semantic_digest_sha256")
                    == run.get("semantic_digest_sha256")
                ),
                "budget_hash_matches": (
                    exists
                    and certificate.get("budget_file_sha256")
                    == elimination.get("budget", {}).get("sha256")
                    == run.get("budget_file_sha256")
                ),
                "request_binding_matches": (
                    exists
                    and certificate.get(
                        "request_semantic_digest_sha256"
                    )
                    == run.get("request_semantic_digest_sha256")
                ),
                "summary_matches_certificate": not summary_mismatches,
                "summary_mismatch_fields": summary_mismatches,
            }
        )
    unique_paths = {
        record["path"]
        for record in run_records
        if isinstance(record["path"], str)
    }
    certificates_passed = bool(
        len(run_records) == 63
        and len(unique_paths) == 63
        and all(
            record["sha256_matches"]
            and record["semantic_digest_matches"]
            and record["budget_hash_matches"]
            and record["request_binding_matches"]
            and record["summary_matches_certificate"]
            for record in run_records
        )
    )
    expected_chart_ids = {
        _campaign_chart_id(chart.chart_id)
        for chart in _core_s1_s2_charts()
    }
    qq_resolved_chart_ids = {
        record["chart"]
        for record in certificate_projections
        if _qq_resolves_noncommutativity(record)
    }
    qq_proof_recomputed = qq_resolved_chart_ids == expected_chart_ids
    scout_fields = [
        f"GF({modulus})" for modulus in SCOUT_MODULI
    ]
    scout_maps = {
        field: {
            record["chart"]: record["chart_verdict"]
            for record in certificate_projections
            if record["coefficient_field"] == field
            and record["exit_status"] == "COMPLETED"
        }
        for field in scout_fields
    }
    scouts_complete = all(
        set(records) == expected_chart_ids
        for records in scout_maps.values()
    )
    scouts_agree = bool(
        scouts_complete
        and scout_maps[scout_fields[0]] == scout_maps[scout_fields[1]]
    )
    s3 = _s3_structural_certificate(root)
    theorem_recomputed = bool(
        partition.get("passed")
        and qq_proof_recomputed
        and s3["passed"]
    )
    aggregate_verdict_matches = bool(
        elimination.get("QQ_exact_resolved_chart_count")
        == len(qq_resolved_chart_ids)
        and elimination.get("phase1_proof_complete")
        == theorem_recomputed
        and elimination.get("verdict")
        == (
            VERDICT_PROVED
            if theorem_recomputed
            else "LITERAL_Q5_FREE_ELIMINATION_PARTIAL"
        )
        and elimination.get("GF_scout_campaign_complete")
        == scouts_complete
        and elimination.get("GF_scout_agreement") == scouts_agree
        and elimination.get("S3_structural_certificate") == s3
        and elimination.get("budget", {}).get("sha256")
        == _sha256(root / BUDGET_PATH)
        and elimination.get("chart_geometry", {}).get(
            "S1_chart_count"
        )
        == 12
        and elimination.get("chart_geometry", {}).get(
            "S2_chart_count"
        )
        == 9
        and set(
            elimination.get("chart_geometry", {}).get(
                "chart_cover_ids", []
            )
        )
        == {
            chart.chart_id for chart in _core_s1_s2_charts()
        }
        and elimination.get("chart_geometry", {}).get("R5_included")
        is False
        and elimination.get("chart_geometry", {}).get(
            "Q5_variable_introduced"
        )
        is False
        and elimination.get("complete_chart_cover", {}).get(
            "Q5_or_R5_used"
        )
        is False
        and elimination.get("literal_forward_implication")
        == {
            "Q5_free_shared_core_forces_Q1_Q4_commutativity": (
                theorem_recomputed
            ),
            "literal_full_system_is_subset_of_shared_core_variety": True,
            "literal_full_system_Q1_Q4_commutativity": (
                theorem_recomputed
            ),
            "Q5_behaviour_used": False,
        }
        and (
            not theorem_recomputed
            or elimination.get("unresolved_components") == []
        )
    )
    partition_sha = _sha256(partition_path)
    elimination_sha = _sha256(elimination_path)
    passed = bool(
        partition.get("passed")
        and elimination.get("phase1_proof_complete")
        and source_hashes_match
        and elimination.get("selection_certificate") == V037_PARTITION
        and elimination.get("selection_certificate_sha256")
        == partition_sha
        and certificates_passed
        and theorem_recomputed
        and aggregate_verdict_matches
    )
    return {
        V037_PARTITION: {
            "sha256": partition_sha,
            "semantic_digest_sha256": partition.get(
                "semantic_digest_sha256"
            ),
            "source_artifact_hashes_match": source_hashes_match,
        },
        V037_ELIMINATION: {
            "sha256": elimination_sha,
            "semantic_digest_sha256": elimination.get(
                "semantic_digest_sha256"
            ),
            "selection_certificate_sha256_matches": (
                elimination.get("selection_certificate_sha256")
                == partition_sha
            ),
        },
        "certificate_count": len(run_records),
        "unique_certificate_path_count": len(unique_paths),
        "certificates": run_records,
        "all_certificate_bindings_passed": certificates_passed,
        "QQ_resolved_chart_ids_recomputed": sorted(
            qq_resolved_chart_ids
        ),
        "QQ_proof_recomputed": qq_proof_recomputed,
        "GF_scouts_complete_recomputed": scouts_complete,
        "GF_scouts_agree_recomputed": scouts_agree,
        "S3_structural_certificate_recomputed": s3,
        "theorem_recomputed": theorem_recomputed,
        "aggregate_verdict_matches_recomputation": (
            aggregate_verdict_matches
        ),
        "passed": passed,
    }


def compile_scope_addendum_v037(root: Path) -> dict[str, Any]:
    """Certify the corrected scope of v0.3.5 and retained v0.3.6 claims."""

    stage3 = _load_json(root / V035_STAGE3)
    full = _load_json(root / V035_FULL)
    classification = _load_json(root / V035_CLASSIFICATION)
    census = _load_json(root / V036_CENSUS)
    vacuity = _load_json(root / V036_VACUITY)
    partition = _load_json(root / V037_PARTITION)
    elimination = _load_json(root / V037_ELIMINATION)

    frozen_hashes = {
        path: {
            "expected_sha256": expected,
            "actual_sha256": _sha256(root / path),
            "unchanged": _sha256(root / path) == expected,
        }
        for path, expected in FROZEN_SHA256.items()
    }
    v037_integrity = _v037_integrity(root, partition, elimination)
    historical_run_count = (
        stage3["planned_run_count"] + full["planned_run_count"]
    )
    passed = bool(
        all(record["unchanged"] for record in frozen_hashes.values())
        and v037_integrity["passed"]
        and full["all_S1_S2_chart_count"] == 49
        and stage3["planned_run_count"] == 147
        and full["planned_run_count"] == 78
        and historical_run_count == 225
        and census["headline_counts"][
            "literal_canonical_scalar_numerators_total"
        ]
        == 2564
        and census["headline_counts"][
            "canonical_scalar_numerators_constraining_Q5"
        ]
        == 12
        and vacuity["passed"]
        and partition["passed"]
        and partition["partition"]["Q5_independent_count"] == 2552
        and partition["shared_core"]["matrix_relation_count"] == 976
        and elimination["phase1_proof_complete"]
        and elimination["QQ_exact_resolved_chart_count"] == 21
        and elimination["verdict"]
        == "LITERAL_Q1_Q4_COMMUTATIVITY_PROVED"
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "branch": BRANCH,
        "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
        "finite_scope": "frozen source stages n<=4",
        "frozen_artifact_integrity": frozen_hashes,
        "v0.3.7_artifact_integrity": v037_integrity,
        "v0.3.5_historical_campaign": {
            "combined_S1_S2_chart_count": full[
                "all_S1_S2_chart_count"
            ],
            "stage3_run_count": stage3["planned_run_count"],
            "full_stage4_run_count": full["planned_run_count"],
            "combined_backend_run_count": historical_run_count,
            "frozen_numeric_results_changed": False,
            "corrected_scope": (
                "The literal portion of the combined 49-chart campaign is "
                "complete only inside the simultaneous-standard-form ansatz "
                "for R2,R3,R4,R5. The compiled n<=4 system does not justify "
                "[R5,Rj]=0, so it is not a cover of all literal solutions. "
                "The derived R2,R3,R4 chart geometry remains a valid cover "
                "for the Q1-through-Q4 predicate."
            ),
            "literal_full_solution_cover_claim_withdrawn": True,
            "frozen_classification_verdict": classification["verdict"],
        },
        "v0.3.6_retained_claim": {
            "Q5_dependency_partition": {
                "total": census["headline_counts"][
                    "literal_canonical_scalar_numerators_total"
                ],
                "Q5_dependent": census["headline_counts"][
                    "canonical_scalar_numerators_constraining_Q5"
                ],
                "Q5_independent": (
                    census["headline_counts"][
                        "literal_canonical_scalar_numerators_total"
                    ]
                    - census["headline_counts"][
                        "canonical_scalar_numerators_constraining_Q5"
                    ]
                ),
            },
            "claim_boundary": vacuity["claim_boundary"],
            "retained_scope": (
                "The exact Q5-vacuity result remains valid at the frozen "
                "Q1-through-Q4 witness and conditionally over the scalar-chain "
                "base. It is not asserted for an arbitrary literal base."
            ),
        },
        "v0.3.7_replacement_argument": {
            "Q5_and_R5_in_elimination": False,
            "Q5_free_canonical_numerator_count": partition["partition"][
                "Q5_independent_count"
            ],
            "shared_matrix_relation_count": partition["shared_core"][
                "matrix_relation_count"
            ],
            "R2_R3_R4_S1_chart_count": elimination["chart_geometry"][
                "S1_chart_count"
            ],
            "R2_R3_R4_S2_chart_count": elimination["chart_geometry"][
                "S2_chart_count"
            ],
            "QQ_exact_resolved_chart_count": elimination[
                "QQ_exact_resolved_chart_count"
            ],
            "GF_scout_agreement": elimination["GF_scout_agreement"],
            "forward_implication_only": True,
            "literal_Q1_Q4_commutativity_proved": elimination[
                "phase1_proof_complete"
            ],
            "verdict": elimination["verdict"],
        },
        "prohibited_interpretations": [
            "The v0.3.5 literal charts cover every literal solution.",
            "The compiled n<=4 equations imply [R5,Rj]=0.",
            "The v0.3.6 Q5-vacuity calculation holds over every literal base.",
            "The finite n<=4 strong-profile result settles the full theory.",
        ],
        "global_scientific_verdict": "FINAL_THEORY_OPEN",
        "unresolved_components": [] if passed else [
            "one or more scope-addendum invariants failed"
        ],
        "passed": passed,
        "verdict": VERDICT if passed else "V037_SCOPE_ADDENDUM_PARTIAL",
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "frozen_artifact_integrity": frozen_hashes,
            "v0.3.7_artifact_integrity": v037_integrity,
            "v0.3.5_historical_campaign": payload[
                "v0.3.5_historical_campaign"
            ],
            "v0.3.6_retained_claim": payload["v0.3.6_retained_claim"],
            "v0.3.7_replacement_argument": payload[
                "v0.3.7_replacement_argument"
            ],
            "prohibited_interpretations": payload[
                "prohibited_interpretations"
            ],
            "verdict": payload["verdict"],
        }
    )
    return payload


def render_scope_addendum_markdown(payload: dict[str, Any]) -> str:
    """Render the human-readable correction from certified JSON fields."""

    historical = payload["v0.3.5_historical_campaign"]
    retained = payload["v0.3.6_retained_claim"]
    replacement = payload["v0.3.7_replacement_argument"]
    integrity = payload["v0.3.7_artifact_integrity"]
    return f"""# Final-Theory Bench v0.3.7 — scope addendum

This addendum changes claim scope, not the frozen v0.3.4–v0.3.6 numbers.
All recorded frozen hashes match their expected SHA-256 values.

## v0.3.5 chart campaign

The combined campaign retains its frozen
{historical["combined_S1_S2_chart_count"]} S1/S2 charts and
{historical["combined_backend_run_count"]} backend runs
({historical["stage3_run_count"]} localised-subsystem runs plus
{historical["full_stage4_run_count"]} full-stage runs).

Its literal portion is complete only inside the ansatz in which
R2, R3, R4, and R5 were put in simultaneous standard form. The compiled
n<=4 system supplies no premise forcing `[R5,R_j]=0`; consequently that
literal chart family is not a cover of all literal solutions. The frozen
counts and certificates remain unchanged.

## v0.3.6 claim retained with its boundary

The {retained["Q5_dependency_partition"]["total"]} literal canonical
numerators split into {retained["Q5_dependency_partition"]["Q5_dependent"]}
Q5-dependent and {retained["Q5_dependency_partition"]["Q5_independent"]}
Q5-independent expressions. Q5 vacuity remains exact at the frozen
Q1-through-Q4 witness and conditionally on the scalar-chain base. It is not
promoted to an arbitrary-base statement.

## v0.3.7 replacement

The decisive calculation removes Q5 and R5 entirely. It evaluates the
{replacement["Q5_free_canonical_numerator_count"]}-numerator,
{replacement["shared_matrix_relation_count"]}-relation shared core on the
R2–R4 cover
({replacement["R2_R3_R4_S1_chart_count"]} S1 charts and
{replacement["R2_R3_R4_S2_chart_count"]} S2 charts), with all
{replacement["QQ_exact_resolved_chart_count"]} charts resolved over QQ.
The two finite-field scouts agree, but are not used as proof.
The replacement aggregate is bound to
{integrity["certificate_count"]} individual backend-certificate hashes,
their request bindings, the external budget-file hash, and the exact
partition artifact.

Only the forward implication is required: every literal solution satisfies
the shared core, and the shared core forces `[Q_i,Q_j]=0` for
`1 <= i < j <= 4`. No assertion about Q5 is needed.

Verdict: `{replacement["verdict"]}`.
Global verdict: `FINAL_THEORY_OPEN`.
"""


def write_scope_addendum_v037(root: Path) -> dict[str, Any]:
    payload = compile_scope_addendum_v037(root)
    _write_json(root / RESULT_PATH, payload)
    report = root / REPORT_PATH
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        render_scope_addendum_markdown(payload),
        encoding="utf-8",
        newline="\n",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)
    if not arguments.write:
        raise SystemExit("select --write")
    payload = write_scope_addendum_v037(Path.cwd())
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
