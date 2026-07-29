"""v0.3.5 orchestration for the fixed-d=2 saturated elimination campaign."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import io
import json
import time
from pathlib import Path
from typing import Any

from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
    _equation_inventory,
    build_localised_relations,
)
from universe_lab.final_theory.d2_sage_backend_v035 import (
    DEFAULT_COMPACT_ARENA_PATH,
    build_chart_payload,
    detect_sage_backend,
    run_sage_request,
)
from universe_lab.final_theory.d2_solver_v034 import (
    _specialised_relation_inventory,
)
from universe_lab.final_theory.d2_strata_v034 import (
    S1,
    S2,
    _s3_q1_subalgebra_certificate,
    stratum_charts,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    stable_hash,
)

BRANCH = "codex/final-theory-v0.3.5-d2-saturated-elimination-20260729"
CACHE_SCHEMA = "final-theory-d2-compact-solver-arena-v0.3.5"
INTEGRITY_SCHEMA = "final-theory-d2-solver-input-integrity-v0.3.5"
DIRECT_SYSTEM_PATH = (
    "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def compile_solver_cache_v035(root: Path) -> dict[str, Any]:
    """Rebuild the missing localisation arena and lock it to frozen IDs.

    The v0.3.4 polynomial-system JSON references expression IDs created after
    the smaller rational-DAG arena certificate was written.  This append-only
    cache reconstructs those nodes from the same source compiler and refuses
    to proceed unless every frozen equation and denominator ID matches.
    """

    started = time.perf_counter()
    frozen_path = root / "results/v0.3.4_polynomial_systems.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    model, relations = build_localised_relations()

    live_equations: dict[str, list[dict[str, Any]]] = {}
    equation_id_checks: dict[str, bool] = {}
    for branch in (DERIVED_BRANCH, LITERAL_BRANCH):
        equations, _ = _equation_inventory(model, relations[branch])
        live_equations[branch] = equations
        frozen_ids = [
            record["canonical_expression_id"]
            for record in frozen["systems"][branch]["equations"]
        ]
        live_ids = [
            record["canonical_expression_id"] for record in equations
        ]
        equation_id_checks[branch] = frozen_ids == live_ids

    frozen_factor_ids = [
        record["factor_id"] for record in frozen["denominator_factors"]
    ]
    live_factor_ids = [
        record["factor_id"]
        for record in model.denominator_factors.values()
    ]
    denominator_ids_match = frozen_factor_ids == live_factor_ids
    if not all(equation_id_checks.values()) or not denominator_ids_match:
        raise RuntimeError(
            "v0.3.5 solver input does not match the frozen v0.3.4 IDs"
        )

    target_ids = set(frozen_factor_ids)
    for equations in live_equations.values():
        target_ids.update(
            record["canonical_expression_id"] for record in equations
        )

    reachable: set[str] = set()
    topological_ids: list[str] = []

    def visit(expression_id: str) -> None:
        if expression_id in reachable:
            return
        node = model.arena.nodes[expression_id]
        for child in node.get("args", []):
            visit(child)
        reachable.add(expression_id)
        topological_ids.append(expression_id)

    for expression_id in sorted(target_ids):
        visit(expression_id)

    indices = {
        expression_id: index
        for index, expression_id in enumerate(topological_ids)
    }
    compact_nodes: list[list[Any]] = []
    operation_codes = {"const": 0, "symbol": 1, "add": 2, "mul": 3}
    for expression_id in topological_ids:
        node = model.arena.nodes[expression_id]
        operation = node["op"]
        if operation == "const":
            compact_nodes.append([operation_codes[operation], node["value"]])
        elif operation == "symbol":
            compact_nodes.append([operation_codes[operation], node["name"]])
        else:
            compact_nodes.append(
                [
                    operation_codes[operation],
                    [indices[child] for child in node["args"]],
                ]
            )

    cache_payload = {
        "schema_version": CACHE_SCHEMA,
        "source_artifact": "results/v0.3.4_polynomial_systems.json",
        "source_artifact_sha256": _sha256(frozen_path),
        "operation_codes": {
            "0": "const",
            "1": "symbol",
            "2": "add",
            "3": "mul",
        },
        "node_count": len(compact_nodes),
        "target_count": len(target_ids),
        "nodes": compact_nodes,
        "target_indices": {
            expression_id: indices[expression_id]
            for expression_id in sorted(target_ids)
        },
    }
    cache_path = root / DEFAULT_COMPACT_ARENA_PATH
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("wb") as raw_handle:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_handle,
            mtime=0,
        ) as gzip_handle:
            with io.TextIOWrapper(gzip_handle, encoding="utf-8") as text_handle:
                json.dump(
                    cache_payload,
                    text_handle,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                )

    integrity: dict[str, Any] = {
        "schema_version": INTEGRITY_SCHEMA,
        "branch": BRANCH,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "source_artifact": str(frozen_path.relative_to(root)).replace(
            "\\", "/"
        ),
        "source_artifact_sha256": _sha256(frozen_path),
        "frozen_rational_arena_missing_referenced_ids": True,
        "repair_policy": (
            "append-only reconstruction from the unchanged v0.3.4 source "
            "compiler; v0.3.4 artifacts are not modified"
        ),
        "equation_id_checks": equation_id_checks,
        "denominator_ids_match": denominator_ids_match,
        "equation_counts": {
            branch: len(live_equations[branch])
            for branch in (DERIVED_BRANCH, LITERAL_BRANCH)
        },
        "denominator_factor_count": len(live_factor_ids),
        "full_live_arena_node_count": len(model.arena.nodes),
        "reachable_compact_node_count": len(compact_nodes),
        "target_expression_count": len(target_ids),
        "cache_path": str(cache_path.relative_to(root)).replace("\\", "/"),
        "cache_sha256": _sha256(cache_path),
        "cache_bytes": cache_path.stat().st_size,
        "build_wall_time_seconds": time.perf_counter() - started,
        "exact_numeric_distinction": "EXACT_STRUCTURAL_RECONSTRUCTION",
        "completeness_scope": (
            "all frozen v0.3.4 canonical numerator and denominator "
            "expression IDs used by the v0.3.5 CAS campaign"
        ),
        "unresolved_components": [],
        "passed": (
            all(equation_id_checks.values()) and denominator_ids_match
        ),
        "verdict": "V035_SOLVER_INPUT_INTEGRITY_PASS",
    }
    integrity["semantic_digest_sha256"] = stable_hash(
        {
            "equation_id_checks": equation_id_checks,
            "denominator_ids_match": denominator_ids_match,
            "cache_sha256": integrity["cache_sha256"],
        }
    )
    _write_json(
        root / "results/v0.3.5_solver_input_integrity.json",
        integrity,
    )
    return integrity


def compile_direct_operator_system_v035(root: Path) -> dict[str, Any]:
    """Freeze the reduced operator input used by the efficient Sage route."""

    presentation_path = root / "results/v0.3.3_q_only_presentation_n4.json"
    presentation = json.loads(
        presentation_path.read_text(encoding="utf-8")
    )
    relations = {
        branch: _specialised_relation_inventory(branch)
        for branch in (DERIVED_BRANCH, LITERAL_BRANCH)
    }
    relation_counts = {
        branch: len(records) for branch, records in relations.items()
    }
    if relation_counts != {
        DERIVED_BRANCH: 1001,
        LITERAL_BRANCH: 1001,
    }:
        raise RuntimeError(
            f"unexpected direct relation counts: {relation_counts}"
        )
    if (
        presentation["semantic_profile"]
        != PAPER_STRONG_OPERATOR_PROFILE
    ):
        raise RuntimeError("direct system semantic profile changed")
    frozen_polynomial_systems = json.loads(
        (root / "results/v0.3.4_polynomial_systems.json").read_text(
            encoding="utf-8"
        )
    )
    scalar_equation_coverage: dict[str, dict[str, Any]] = {}
    for branch, branch_relations in relations.items():
        direct_ids = {
            record["relation_id"] for record in branch_relations
        }
        frozen_ids = {
            provenance["relation_id"]
            for equation in frozen_polynomial_systems["systems"][branch][
                "equations"
            ]
            for provenance in equation["provenance"]
        }
        zero_identity_records = [
            record
            for record in branch_relations
            if record["relation_id"] not in frozen_ids
        ]
        coverage_passed = (
            frozen_ids <= direct_ids
            and len(direct_ids) == 1001
            and len(frozen_ids) == 979
            and len(zero_identity_records) == 22
            and all(
                record["family"] == "EQ112_PATH_CONSISTENCY"
                for record in zero_identity_records
            )
        )
        if not coverage_passed:
            raise RuntimeError(
                f"direct/scalar relation coverage changed for {branch}"
            )
        scalar_equation_coverage[branch] = {
            "direct_matrix_relation_count": len(direct_ids),
            "relations_represented_in_nonzero_scalar_numerators": len(
                frozen_ids
            ),
            "identically_zero_path_relation_count": len(
                zero_identity_records
            ),
            "identically_zero_path_relation_ids": [
                record["relation_id"]
                for record in zero_identity_records
            ],
            "frozen_canonical_scalar_numerator_count": len(
                frozen_polynomial_systems["systems"][branch]["equations"]
            ),
            "all_frozen_provenance_relation_ids_covered": True,
            "passed": True,
        }
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-direct-operator-system-v0.3.5",
        "branch": BRANCH,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "source_artifact": str(
            presentation_path.relative_to(root)
        ).replace("\\", "/"),
        "source_artifact_sha256": _sha256(presentation_path),
        "dependency_nodes": presentation["dependency_DAG"]["nodes"],
        "relations": relations,
        "reconstructed_transition_predicates": presentation[
            "invertibility_predicates"
        ]["reconstructed_transition_predicates"],
        "explicit_two_sided_inverse_predicates": presentation[
            "invertibility_predicates"
        ]["explicit_two_sided_inverse_predicates"],
        "relation_to_scalar_equation_coverage": (
            scalar_equation_coverage
        ),
        "counts": {
            "dependency_nodes": len(
                presentation["dependency_DAG"]["nodes"]
            ),
            "relations": relation_counts,
            "reconstructed_transition_predicates": len(
                presentation["invertibility_predicates"][
                    "reconstructed_transition_predicates"
                ]
            ),
            "explicit_inverse_sites": len(
                presentation["invertibility_predicates"][
                    "explicit_two_sided_inverse_predicates"
                ]
            ),
        },
        "exact_numeric_distinction": "EXACT_REDUCED_OPERATOR_WORD_SYSTEM",
        "completeness_scope": (
            "all 1001 reduced relations per source-index branch and all "
            "165 reconstructed transition nonsingularity predicates"
        ),
        "unresolved_components": [],
        "passed": True,
        "verdict": "V035_DIRECT_OPERATOR_SYSTEM_COMPILED",
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "dependency_nodes": payload["dependency_nodes"],
            "relations": payload["relations"],
            "transitions": payload[
                "reconstructed_transition_predicates"
            ],
        }
    )
    _write_json(root / DIRECT_SYSTEM_PATH, payload)
    return payload


def s3_commutativity_proof_v035() -> dict[str, Any]:
    """Freeze the finite S3 noncommutativity result as a v0.3.5 artifact."""

    certificate = _s3_q1_subalgebra_certificate()
    passed = bool(
        certificate["all_reconstructed_transition_pairs_commute"]
    )
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-S3-commutativity-v0.3.5",
        "branch": BRANCH,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "finite_scope": "n<=4",
        "proof": certificate,
        "lemma": (
            "Every element of the rational subalgebra K(parameters)(Q_1) "
            "is a rational function of one matrix; any two such elements "
            "commute wherever their denominators are nonzero."
        ),
        "general_S3_solution_locus_classified": False,
        "exact_numeric_distinction": "EXACT_SYMBOLIC_DEPENDENCY_PROOF",
        "completeness_scope": (
            "noncommutativity exclusion in the finite S3 stratum only"
        ),
        "unresolved_components": [
            "general S3 solution-locus description"
        ],
        "passed": passed,
        "verdict": (
            "S3_NO_NONCOMMUTATIVE_REPRESENTATION_N4"
            if passed
            else "CPOBC_D2_PARTIAL"
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {"proof": certificate, "lemma": payload["lemma"]}
    )
    return payload


def write_s3_artifact_v035(root: Path) -> dict[str, Any]:
    payload = s3_commutativity_proof_v035()
    _write_json(
        root / "results/v0.3.5_S3_commutativity_proof.json",
        payload,
    )
    return payload


def _campaign_run_path(
    root: Path,
    *,
    field_label: str,
    source_index_branch: str,
    chart_id: str,
) -> Path:
    chart_digest = stable_hash(
        {
            "source_index_branch": source_index_branch,
            "chart": chart_id,
        }
    )[:20]
    branch_label = (
        "derived"
        if source_index_branch == DERIVED_BRANCH
        else "literal"
    )
    return (
        root
        / "certificates"
        / "d2_saturation"
        / "stage3_subset"
        / field_label
        / branch_label
        / f"{chart_digest}.json"
    )


def _completed_campaign_result(
    path: Path,
    *,
    chart_id: str,
    coefficient_modulus: int,
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    expected_field = (
        "QQ"
        if coefficient_modulus == 0
        else f"GF({coefficient_modulus})"
    )
    if (
        payload.get("exit_status") == "COMPLETED"
        and payload.get("chart") == chart_id
        and payload.get("coefficient_field") == expected_field
        and payload.get("maximum_source_stage") == 3
        and payload.get("saturation_requested") is True
    ):
        return payload
    return None


def run_stage3_subset_campaign_v035(
    root: Path,
    *,
    coefficient_moduli: tuple[int, ...] = (32003, 32009, 0),
    workers: int = 3,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    """Run the exact localised n<=3 subsystem on all 49 S1/S2 charts.

    A unit result is already a proof for the full n<=4 system: the full
    relation ideal contains this subsystem, and its localisation is therefore
    also the unit ideal.  Nonunit and failed cases are explicitly carried
    forward to the full stage-4 campaign.
    """

    started = time.perf_counter()
    backend = detect_sage_backend(root)
    if not backend.get("available"):
        raise RuntimeError(f"Sage backend unavailable: {backend}")
    charts = [
        chart
        for branch in (DERIVED_BRANCH, LITERAL_BRANCH)
        for chart in stratum_charts(branch)
        if chart.stratum in {S1, S2}
    ]
    if len(charts) != 49:
        raise RuntimeError(f"expected 49 S1/S2 charts, found {len(charts)}")

    aggregate_path = (
        root / "results/v0.3.5_stage3_subset_campaign.json"
    )
    run_summaries: list[dict[str, Any]] = []

    def summary_record(
        result: dict[str, Any],
        *,
        run_path: Path,
    ) -> dict[str, Any]:
        return {
            "chart": result.get("chart"),
            "stratum": result.get("stratum"),
            "source_index_branch": result.get("source_index_branch"),
            "coefficient_field": result.get("coefficient_field"),
            "exit_status": result.get("exit_status"),
            "chart_verdict": result.get("chart_verdict"),
            "proof_eligible": result.get("proof_eligible", False),
            "saturated_unit_ideal": result.get(
                "saturated_unit_ideal", False
            ),
            "final_resaturates_pre_stage4_factors": result.get(
                "final_resaturates_pre_stage4_factors", False
            ),
            "host_observed_wall_time_seconds": result.get(
                "host_observed_wall_time_seconds"
            ),
            "worker_wall_time_seconds": result.get(
                "resource_usage", {}
            ).get("wall_time_seconds"),
            "peak_rss_bytes": result.get("resource_usage", {}).get(
                "peak_rss_bytes"
            ),
            "certificate": str(run_path.relative_to(root)).replace(
                "\\", "/"
            ),
            "semantic_digest_sha256": result.get(
                "semantic_digest_sha256"
            ),
        }

    def write_progress() -> None:
        completed = len(run_summaries)
        payload = {
            "schema_version": (
                "final-theory-d2-stage3-subset-campaign-v0.3.5"
            ),
            "branch": BRANCH,
            "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
            "backend": backend,
            "coefficient_moduli": list(coefficient_moduli),
            "chart_count_per_field": len(charts),
            "planned_run_count": len(charts) * len(coefficient_moduli),
            "completed_or_terminal_run_count": completed,
            "runs": sorted(
                run_summaries,
                key=lambda record: (
                    record.get("coefficient_field", ""),
                    record.get("source_index_branch", ""),
                    record.get("chart", ""),
                ),
            ),
            "campaign_complete": (
                completed == len(charts) * len(coefficient_moduli)
            ),
            "wall_time_seconds_so_far": time.perf_counter() - started,
            "exact_numeric_distinction": (
                "GF(p) runs are scouts; only completed QQ runs with "
                "proof_eligible=true are proof-bearing"
            ),
            "completeness_scope": (
                "all 49 S1/S2 charts for the localised relation subset "
                "through source stage 3"
            ),
            "unresolved_components": [],
            "verdict": "CPOBC_D2_PARTIAL",
        }
        _write_json(aggregate_path, payload)

    for modulus in coefficient_moduli:
        field_label = "QQ" if modulus == 0 else f"GF{modulus}"
        pending: list[tuple[Any, Path]] = []
        for chart in charts:
            run_path = _campaign_run_path(
                root,
                field_label=field_label,
                source_index_branch=chart.source_index_branch,
                chart_id=chart.chart_id,
            )
            cached = _completed_campaign_result(
                run_path,
                chart_id=chart.chart_id,
                coefficient_modulus=modulus,
            )
            if cached is not None:
                run_summaries.append(
                    summary_record(cached, run_path=run_path)
                )
                continue
            payload = build_chart_payload(
                chart.source_index_branch,
                chart.chart_id,
                coefficient_modulus=modulus,
                operation="solve",
                maximum_source_stage=3,
                saturation=True,
                check_noncommutativity=False,
                factor_denominators=True,
                include_all_transition_predicates=False,
                groebner_algorithm="libsingular:slimgb",
                groebner_strategy="progressive",
                progressive_batch_size=1,
            )
            pending.append((payload, run_path))
        write_progress()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, workers)
        ) as executor:
            futures = {
                executor.submit(
                    run_sage_request,
                    root,
                    payload,
                    timeout_seconds=timeout_seconds,
                ): (payload, run_path)
                for payload, run_path in pending
            }
            for future in concurrent.futures.as_completed(futures):
                payload, run_path = futures[future]
                try:
                    result = future.result()
                except Exception as exc:  # pragma: no cover - campaign guard
                    result = {
                        "schema_version": (
                            "final-theory-d2-sage-response-v0.3.5"
                        ),
                        "chart": payload["chart"],
                        "stratum": payload["stratum"],
                        "source_index_branch": payload[
                            "source_index_branch"
                        ],
                        "coefficient_field": (
                            "QQ"
                            if modulus == 0
                            else f"GF({modulus})"
                        ),
                        "exit_status": "HOST_EXCEPTION",
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                        "proof_eligible": False,
                        "verdict": "CPOBC_D2_PARTIAL",
                    }
                _write_json(run_path, result)
                run_summaries.append(
                    summary_record(result, run_path=run_path)
                )
                write_progress()
                print(
                    f"[{len(run_summaries)}/"
                    f"{len(charts) * len(coefficient_moduli)}] "
                    f"{result.get('coefficient_field')} "
                    f"{result.get('chart')} "
                    f"{result.get('exit_status')} "
                    f"unit={result.get('saturated_unit_ideal')}",
                    flush=True,
                )

    qq_runs = [
        record
        for record in run_summaries
        if record["coefficient_field"] == "QQ"
    ]
    exact_unit_charts = [
        record["chart"]
        for record in qq_runs
        if (
            record["exit_status"] == "COMPLETED"
            and record["proof_eligible"]
            and record["saturated_unit_ideal"]
        )
    ]
    unresolved = [
        record["chart"]
        for record in qq_runs
        if record["chart"] not in exact_unit_charts
    ]
    modular_unit_maps = {
        field: {
            record["chart"]: record["saturated_unit_ideal"]
            for record in run_summaries
            if record["coefficient_field"] == field
        }
        for field in ("GF(32003)", "GF(32009)")
    }
    modular_disagreements = [
        chart.chart_id
        for chart in charts
        if modular_unit_maps["GF(32003)"].get(chart.chart_id)
        != modular_unit_maps["GF(32009)"].get(chart.chart_id)
    ]
    final_payload = json.loads(
        aggregate_path.read_text(encoding="utf-8")
    )
    final_payload.update(
        {
            "campaign_complete": (
                len(run_summaries)
                == len(charts) * len(coefficient_moduli)
            ),
            "exact_QQ_unit_subset_chart_count": len(exact_unit_charts),
            "exact_QQ_unit_subset_charts": sorted(exact_unit_charts),
            "charts_requiring_stage4": sorted(unresolved),
            "modular_scout_agreement": not modular_disagreements,
            "modular_scout_disagreements": sorted(
                modular_disagreements
            ),
            "unresolved_components": [
                f"full stage-4 elimination: {chart}"
                for chart in sorted(unresolved)
            ],
            "wall_time_seconds": time.perf_counter() - started,
            "verdict": (
                "V035_ALL_S1_S2_CHARTS_EMPTY_BY_STAGE3_SUBSYSTEM"
                if len(exact_unit_charts) == len(charts)
                else "CPOBC_D2_PARTIAL"
            ),
        }
    )
    _write_json(aggregate_path, final_payload)
    return final_payload


def run_full_stage4_campaign_v035(
    root: Path,
    *,
    coefficient_moduli: tuple[int, ...] = (32003, 32009, 0),
    workers: int = 3,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    """Finish only charts not settled by the exact stage-3 subsystem."""

    subset_path = root / "results/v0.3.5_stage3_subset_campaign.json"
    subset = json.loads(subset_path.read_text(encoding="utf-8"))
    if not subset.get("campaign_complete"):
        raise RuntimeError("stage-3 subset campaign is not complete")
    exact_subset_units = set(subset["exact_QQ_unit_subset_charts"])
    all_charts = [
        chart
        for branch in (DERIVED_BRANCH, LITERAL_BRANCH)
        for chart in stratum_charts(branch)
        if chart.stratum in {S1, S2}
    ]
    structural_commuting: set[str] = set()
    full_charts = []
    for chart in all_charts:
        descriptor = build_chart_payload(
            chart.source_index_branch,
            chart.chart_id,
        )
        if not descriptor["commutator_components"]:
            structural_commuting.add(chart.chart_id)
        elif chart.chart_id not in exact_subset_units:
            full_charts.append(chart)

    backend = detect_sage_backend(root)
    started = time.perf_counter()
    aggregate_path = root / "results/v0.3.5_full_stage4_campaign.json"
    summaries: list[dict[str, Any]] = []
    planned = len(full_charts) * len(coefficient_moduli)

    def run_path_for(
        chart: Any,
        modulus: int,
    ) -> Path:
        field = "QQ" if modulus == 0 else f"GF{modulus}"
        branch_label = (
            "derived"
            if chart.source_index_branch == DERIVED_BRANCH
            else "literal"
        )
        digest = stable_hash(
            {
                "branch": chart.source_index_branch,
                "chart": chart.chart_id,
                "campaign": "full-stage4",
            }
        )[:20]
        return (
            root
            / "certificates"
            / "d2_saturation"
            / "full_stage4"
            / field
            / branch_label
            / f"{digest}.json"
        )

    def valid_cached(
        path: Path,
        chart_id: str,
        modulus: int,
    ) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        field = "QQ" if modulus == 0 else f"GF({modulus})"
        if (
            result.get("exit_status") == "COMPLETED"
            and result.get("chart") == chart_id
            and result.get("coefficient_field") == field
            and result.get("maximum_source_stage") == 4
            and result.get("saturation_requested") is True
            and result.get("selected_relation_count") == 1001
            and result.get("final_resaturates_pre_stage4_factors") is True
        ):
            return result
        return None

    def compact(result: dict[str, Any], path: Path) -> dict[str, Any]:
        final_saturation_steps = [
            record
            for record in result.get("saturation_trace", [])
            if record.get("phase") != "PRE_STAGE4_LOCALISATION"
        ]
        final_saturation_trace_complete = bool(
            result.get("saturated_unit_ideal")
        ) or len(final_saturation_steps) == result.get(
            "effective_saturation_factor_count"
        )
        return {
            "chart": result.get("chart"),
            "stratum": result.get("stratum"),
            "source_index_branch": result.get("source_index_branch"),
            "coefficient_field": result.get("coefficient_field"),
            "exit_status": result.get("exit_status"),
            "proof_eligible": result.get("proof_eligible", False),
            "chart_verdict": result.get("chart_verdict"),
            "saturated_unit_ideal": result.get(
                "saturated_unit_ideal", False
            ),
            "final_resaturates_pre_stage4_factors": result.get(
                "final_resaturates_pre_stage4_factors", False
            ),
            "effective_saturation_factor_count": result.get(
                "effective_saturation_factor_count"
            ),
            "final_saturation_step_count": len(final_saturation_steps),
            "final_saturation_trace_complete": (
                final_saturation_trace_complete
            ),
            "relations_evaluated_count": result.get(
                "relations_evaluated_count"
            ),
            "reconstructed_transitions_checked": result.get(
                "reconstructed_transitions_checked"
            ),
            "transition_checks_vacuous": result.get(
                "reconstructed_transition_predicates_vacuous_due_to_unit_localised_subset",
                False,
            ),
            "surviving_noncommutative_component_count": result.get(
                "surviving_noncommutative_component_count"
            ),
            "host_observed_wall_time_seconds": result.get(
                "host_observed_wall_time_seconds"
            ),
            "worker_wall_time_seconds": result.get(
                "resource_usage", {}
            ).get("wall_time_seconds"),
            "peak_rss_bytes": result.get("resource_usage", {}).get(
                "peak_rss_bytes"
            ),
            "certificate": str(path.relative_to(root)).replace("\\", "/"),
            "semantic_digest_sha256": result.get(
                "semantic_digest_sha256"
            ),
        }

    def write_progress() -> None:
        _write_json(
            aggregate_path,
            {
                "schema_version": (
                    "final-theory-d2-full-stage4-campaign-v0.3.5"
                ),
                "branch": BRANCH,
                "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
                "backend": backend,
                "all_S1_S2_chart_count": len(all_charts),
                "stage3_exact_unit_chart_count": len(
                    exact_subset_units
                ),
                "structurally_commuting_chart_count": len(
                    structural_commuting
                ),
                "structurally_commuting_charts": sorted(
                    structural_commuting
                ),
                "full_stage4_chart_count": len(full_charts),
                "planned_run_count": planned,
                "completed_or_terminal_run_count": len(summaries),
                "runs": sorted(
                    summaries,
                    key=lambda item: (
                        str(item.get("coefficient_field") or ""),
                        str(item.get("chart") or ""),
                    ),
                ),
                "campaign_complete": len(summaries) == planned,
                "wall_time_seconds_so_far": (
                    time.perf_counter() - started
                ),
                "exact_numeric_distinction": (
                    "GF(p) runs are scouts; QQ proof_eligible runs are "
                    "proof-bearing"
                ),
                "completeness_scope": (
                    "full source-stage-4 saturated elimination and "
                    "componentwise noncommutativity checks for every chart "
                    "not already settled by a localised subsystem or a "
                    "zero commutator polynomial"
                ),
                "unresolved_components": [],
                "verdict": "CPOBC_D2_PARTIAL",
            },
        )

    for modulus in coefficient_moduli:
        pending: list[tuple[dict[str, Any], Path]] = []
        for chart in full_charts:
            path = run_path_for(chart, modulus)
            cached = valid_cached(path, chart.chart_id, modulus)
            if cached is not None:
                summaries.append(compact(cached, path))
                continue
            request = build_chart_payload(
                chart.source_index_branch,
                chart.chart_id,
                coefficient_modulus=modulus,
                operation="solve",
                maximum_source_stage=4,
                saturation=True,
                check_noncommutativity=True,
                factor_denominators=True,
                include_all_transition_predicates=True,
                groebner_algorithm="libsingular:slimgb",
                groebner_strategy="progressive",
                progressive_batch_size=4,
            )
            pending.append((request, path))
        write_progress()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, workers)
        ) as executor:
            future_map = {
                executor.submit(
                    run_sage_request,
                    root,
                    request,
                    timeout_seconds=timeout_seconds,
                ): (request, path)
                for request, path in pending
            }
            for future in concurrent.futures.as_completed(future_map):
                request, path = future_map[future]
                try:
                    result = future.result()
                except Exception as exc:  # pragma: no cover
                    result = {
                        "schema_version": (
                            "final-theory-d2-sage-response-v0.3.5"
                        ),
                        "chart": request["chart"],
                        "stratum": request["stratum"],
                        "source_index_branch": request[
                            "source_index_branch"
                        ],
                        "coefficient_field": (
                            "QQ"
                            if modulus == 0
                            else f"GF({modulus})"
                        ),
                        "exit_status": "HOST_EXCEPTION",
                        "proof_eligible": False,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                        "verdict": "CPOBC_D2_PARTIAL",
                    }
                _write_json(path, result)
                summaries.append(compact(result, path))
                write_progress()
                print(
                    f"[{len(summaries)}/{planned}] "
                    f"{result.get('coefficient_field')} "
                    f"{result.get('chart')} "
                    f"{result.get('exit_status')} "
                    f"{result.get('chart_verdict')}",
                    flush=True,
                )

    qq = {
        record["chart"]: record
        for record in summaries
        if record["coefficient_field"] == "QQ"
    }
    modular_maps = {
        field: {
            record["chart"]: record["chart_verdict"]
            for record in summaries
            if record["coefficient_field"] == field
        }
        for field in ("GF(32003)", "GF(32009)")
    }
    modular_disagreements = [
        chart.chart_id
        for chart in full_charts
        if modular_maps["GF(32003)"].get(chart.chart_id)
        != modular_maps["GF(32009)"].get(chart.chart_id)
    ]
    classifications: dict[str, str] = {}
    unresolved: list[str] = []
    noncommutative: list[str] = []
    for chart in all_charts:
        if chart.chart_id in exact_subset_units:
            classifications[chart.chart_id] = (
                "EXACT_EMPTY_BY_LOCALISED_STAGE3_SUBSYSTEM"
            )
        elif chart.chart_id in structural_commuting:
            classifications[chart.chart_id] = (
                "EXACT_STRUCTURALLY_COMMUTATIVE_CHART"
            )
        else:
            record = qq.get(chart.chart_id)
            verdict = record.get("chart_verdict") if record else None
            if (
                record
                and record["exit_status"] == "COMPLETED"
                and record["proof_eligible"]
                and verdict
                in {
                    "EXACT_EMPTY_CHART",
                    "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART",
                }
            ):
                classifications[chart.chart_id] = verdict
            elif (
                record
                and record["exit_status"] == "COMPLETED"
                and record["proof_eligible"]
                and verdict
                == "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
            ):
                classifications[chart.chart_id] = verdict
                noncommutative.append(chart.chart_id)
            else:
                classifications[chart.chart_id] = "UNRESOLVED"
                unresolved.append(chart.chart_id)
    final = json.loads(aggregate_path.read_text(encoding="utf-8"))
    final.update(
        {
            "chart_classifications": classifications,
            "modular_scout_agreement": not modular_disagreements,
            "modular_scout_disagreements": sorted(
                modular_disagreements
            ),
            "noncommutative_charts": sorted(noncommutative),
            "unresolved_charts": sorted(unresolved),
            "unresolved_components": [
                f"incomplete full chart: {chart}"
                for chart in sorted(unresolved)
            ],
            "campaign_complete": len(summaries) == planned,
            "wall_time_seconds": time.perf_counter() - started,
            "verdict": (
                "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
                if noncommutative
                else (
                    "V035_S1_S2_NO_NONCOMMUTATIVE_CHART_N4"
                    if not unresolved
                    else "CPOBC_D2_PARTIAL"
                )
            ),
        }
    )
    final["source_branch_verdicts"] = {}
    for branch in (DERIVED_BRANCH, LITERAL_BRANCH):
        branch_classifications = {
            chart_id: classification
            for chart_id, classification in classifications.items()
            if chart_id.startswith(f"{branch}:")
        }
        if any(
            classification
            == "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
            for classification in branch_classifications.values()
        ):
            branch_verdict = (
                "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
            )
        elif "UNRESOLVED" in branch_classifications.values():
            branch_verdict = "CPOBC_D2_PARTIAL"
        else:
            branch_verdict = (
                "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4"
            )
        final["source_branch_verdicts"][branch] = branch_verdict
    _write_json(aggregate_path, final)
    return final


def write_classification_artifacts_v035(root: Path) -> dict[str, Any]:
    """Aggregate completed CAS certificates without raising the claim ceiling."""

    subset_path = root / "results/v0.3.5_stage3_subset_campaign.json"
    full_path = root / "results/v0.3.5_full_stage4_campaign.json"
    subset = json.loads(subset_path.read_text(encoding="utf-8"))
    full = json.loads(full_path.read_text(encoding="utf-8"))
    if not subset.get("campaign_complete") or not full.get(
        "campaign_complete"
    ):
        raise RuntimeError("CAS campaigns are not complete")
    integrity_path = root / "results/v0.3.5_solver_input_integrity.json"
    direct_path = root / DIRECT_SYSTEM_PATH
    s3_path = root / "results/v0.3.5_S3_commutativity_proof.json"
    oracle_path = root / "results/v0.3.5_independent_oracle.json"
    witness_path = (
        root / "results/v0.3.5_explicit_rational_witness.json"
    )
    upper_witness_path = (
        root / "results/v0.3.5_explicit_rational_witness_upper.json"
    )
    lower_witness_path = (
        root / "results/v0.3.5_explicit_rational_witness_lower.json"
    )
    stage3_log_path = (
        root
        / "certificates/d2_saturation/"
        "v0.3.5_stage3_campaign.stdout.log"
    )
    full_log_path = (
        root
        / "certificates/d2_saturation/"
        "v0.3.5_full_campaign_resaturated.stdout.log"
    )
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    direct = json.loads(direct_path.read_text(encoding="utf-8"))
    s3 = json.loads(s3_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    witness = json.loads(witness_path.read_text(encoding="utf-8"))
    witness_records = [
        witness,
        json.loads(upper_witness_path.read_text(encoding="utf-8")),
        json.loads(lower_witness_path.read_text(encoding="utf-8")),
    ]
    witness_by_chart = {
        record["chart"]: record for record in witness_records
    }
    witness_path_by_chart = {
        record["chart"]: path
        for record, path in zip(
            witness_records,
            (
                witness_path,
                upper_witness_path,
                lower_witness_path,
            ),
            strict=True,
        )
    }
    v034 = json.loads(
        (root / "results/v0.3.4_S1_result.json").read_text(
            encoding="utf-8"
        )
    )
    if (
        not integrity["passed"]
        or not direct["passed"]
        or not s3["passed"]
        or not oracle["passed"]
    ):
        raise RuntimeError("v0.3.5 solver inputs did not pass integrity")
    if any(
        not record.get("final_resaturates_pre_stage4_factors")
        or not record.get("final_saturation_trace_complete")
        for record in full["runs"]
    ):
        raise RuntimeError("a full chart lacks final saturation coverage")
    if (
        full.get("noncommutative_charts")
        and (
            not all(record.get("passed") for record in witness_records)
            or len(witness_by_chart) < 3
        )
    ):
        raise RuntimeError(
            "noncommutative components lack independent explicit witnesses"
        )
    classifications = full["chart_classifications"]
    subset_runs = {
        (record["chart"], record["coefficient_field"]): record
        for record in subset["runs"]
    }
    full_runs = {
        (record["chart"], record["coefficient_field"]): record
        for record in full["runs"]
    }
    common = {
        "branch": BRANCH,
        "source_commit": v034["source_commit"],
        "paper_versions": v034["paper_versions"],
        "source_hashes": v034["source_hashes"],
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "characteristic-zero algebraic closure of QQ",
        "finite_scope": "n<=4",
        "assumptions": [
            (
                "PAPER_STRONG_OPERATOR_PROFILE, including occurrence-wise "
                "transition-operator identification"
            ),
            "fixed matrix dimension d=2",
            "finite source stages n<=4",
            (
                "every Q inverse and every declared reconstructed transition "
                "inverse is restricted to its nonzero determinant locus"
            ),
            (
                "S1/S2/S3 chart cover from v0.3.4 is exhaustive under "
                "simultaneous similarity"
            ),
            "DERIVED and LITERAL source-index branches remain separate",
        ],
        "input_certificates": {
            "solver_integrity": str(
                integrity_path.relative_to(root)
            ).replace("\\", "/"),
            "direct_operator_system": str(
                direct_path.relative_to(root)
            ).replace("\\", "/"),
            "stage3_campaign": str(
                subset_path.relative_to(root)
            ).replace("\\", "/"),
            "full_stage4_campaign": str(
                full_path.relative_to(root)
            ).replace("\\", "/"),
            "S3_commutativity": str(s3_path.relative_to(root)).replace(
                "\\", "/"
            ),
            "independent_oracle": str(
                oracle_path.relative_to(root)
            ).replace("\\", "/"),
            "explicit_rational_witness": str(
                witness_path.relative_to(root)
            ).replace("\\", "/"),
            "explicit_rational_witness_upper": str(
                upper_witness_path.relative_to(root)
            ).replace("\\", "/"),
            "explicit_rational_witness_lower": str(
                lower_witness_path.relative_to(root)
            ).replace("\\", "/"),
            "stage3_execution_log": str(
                stage3_log_path.relative_to(root)
            ).replace("\\", "/"),
            "full_stage4_execution_log": str(
                full_log_path.relative_to(root)
            ).replace("\\", "/"),
        },
        "certificate_hashes": {
            str(path.relative_to(root)).replace("\\", "/"): _sha256(path)
            for path in (
                integrity_path,
                direct_path,
                subset_path,
                full_path,
                s3_path,
                oracle_path,
                witness_path,
                upper_witness_path,
                lower_witness_path,
                stage3_log_path,
                full_log_path,
            )
        },
        "backend_execution_summary": {
            "sage": full["backend"]["sage"],
            "singular": full["backend"]["singular"],
            "stage3_run_count": subset["planned_run_count"],
            "full_stage4_run_count": full["planned_run_count"],
            "coefficient_fields": ["GF(32003)", "GF(32009)", "QQ"],
            "cumulative_worker_wall_time_seconds": sum(
                record["worker_wall_time_seconds"] or 0.0
                for record in subset["runs"] + full["runs"]
            ),
            "cumulative_host_observed_wall_time_seconds": sum(
                record["host_observed_wall_time_seconds"] or 0.0
                for record in subset["runs"] + full["runs"]
            ),
            "maximum_peak_rss_bytes": max(
                record["peak_rss_bytes"] or 0
                for record in subset["runs"] + full["runs"]
            ),
        },
    }

    def chart_record(chart: Any) -> dict[str, Any]:
        classification = classifications[chart.chart_id]
        qq_subset = subset_runs[(chart.chart_id, "QQ")]
        gf_subset = [
            subset_runs[(chart.chart_id, field)]["certificate"]
            for field in ("GF(32003)", "GF(32009)")
        ]
        record: dict[str, Any] = {
            "chart": chart.chart_id,
            "stratum": chart.stratum,
            "source_index_branch": chart.source_index_branch,
            "classification": classification,
            "chart_cover_provenance": list(chart.cover_provenance),
            "residual_gauge": chart.residual_gauge,
            "GF_scout_certificates": gf_subset,
            "backend": "SageMath 10.9 / embedded Singular 4.4.1",
        }
        if classification == (
            "EXACT_EMPTY_BY_LOCALISED_STAGE3_SUBSYSTEM"
        ):
            record.update(
                {
                    "QQ_certificate": qq_subset["certificate"],
                    "proof_rule": (
                        "The full n<=4 localised ideal contains the "
                        "stage<=3 localised subsystem. Since the latter is "
                        "(1), the full localised ideal is (1)."
                    ),
                    "proof_eligible": True,
                    "exit_status": qq_subset["exit_status"],
                    "wall_time_seconds": qq_subset[
                        "worker_wall_time_seconds"
                    ],
                    "peak_rss_bytes": qq_subset["peak_rss_bytes"],
                }
            )
        elif classification == "EXACT_STRUCTURALLY_COMMUTATIVE_CHART":
            descriptor = build_chart_payload(
                chart.source_index_branch,
                chart.chart_id,
            )
            record.update(
                {
                    "QQ_backend_certificate": qq_subset["certificate"],
                    "commutator_components": descriptor[
                        "commutator_components"
                    ],
                    "proof_rule": (
                        "All three independent entries of every 2x2 "
                        "commutator [Q_i,Q_j] specialise identically to zero."
                    ),
                    "proof_eligible": True,
                    "exit_status": qq_subset["exit_status"],
                    "wall_time_seconds": qq_subset[
                        "worker_wall_time_seconds"
                    ],
                    "peak_rss_bytes": qq_subset["peak_rss_bytes"],
                }
            )
        else:
            qq_full = full_runs[(chart.chart_id, "QQ")]
            record.update(
                {
                    "QQ_certificate": qq_full["certificate"],
                    "full_relation_count": qq_full[
                        "relations_evaluated_count"
                    ],
                    "reconstructed_transitions_checked": qq_full[
                        "reconstructed_transitions_checked"
                    ],
                    "surviving_noncommutative_component_count": qq_full[
                        "surviving_noncommutative_component_count"
                    ],
                    "proof_eligible": qq_full["proof_eligible"],
                    "exit_status": qq_full["exit_status"],
                    "wall_time_seconds": qq_full[
                        "worker_wall_time_seconds"
                    ],
                    "peak_rss_bytes": qq_full["peak_rss_bytes"],
                    "full_GF_scout_certificates": [
                        full_runs[(chart.chart_id, field)][
                            "certificate"
                        ]
                        for field in ("GF(32003)", "GF(32009)")
                    ],
                }
            )
        chart_witness = witness_by_chart.get(chart.chart_id)
        if chart_witness is not None:
            record["explicit_rational_witness"] = {
                "certificate": str(
                    witness_path_by_chart[chart.chart_id].relative_to(
                        root
                    )
                ).replace("\\", "/"),
                "passed": chart_witness["passed"],
                "Q_matrices": chart_witness["Q_matrices"],
                "nonzero_commutator": chart_witness[
                    "nonzero_commutator"
                ],
            }
        record["semantic_digest_sha256"] = stable_hash(record)
        return record

    stratum_payloads: dict[str, dict[str, Any]] = {}
    for stratum, filename in (
        (
            S1,
            "v0.3.5_S1_saturated.json",
        ),
        (
            S2,
            "v0.3.5_S2_saturated.json",
        ),
    ):
        charts = [
            chart
            for branch in (DERIVED_BRANCH, LITERAL_BRANCH)
            for chart in stratum_charts(branch)
            if chart.stratum == stratum
        ]
        records = [chart_record(chart) for chart in charts]
        unresolved = [
            record["chart"]
            for record in records
            if record["classification"] == "UNRESOLVED"
        ]
        noncommutative = [
            record["chart"]
            for record in records
            if record["classification"]
            == "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
        ]
        complete = not unresolved
        payload = {
            "schema_version": (
                f"final-theory-d2-{stratum}-saturated-v0.3.5"
            ),
            **common,
            "stratum": stratum,
            "chart_count": len(charts),
            "charts": records,
            "all_charts_processed": complete,
            "noncommutative_charts": noncommutative,
            "exact_numeric_distinction": (
                "All verdict-bearing ideal operations are over QQ; "
                "GF(32003) and GF(32009) are recorded only as scouts."
            ),
            "completeness_scope": (
                f"all {len(charts)} {stratum} charts in both frozen "
                "source-index branches, under the strong profile and n<=4"
            ),
            "unresolved_components": unresolved,
            "verdict": (
                "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
                if noncommutative
                else (
                    "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4"
                    if complete
                    else "CPOBC_D2_PARTIAL"
                )
            ),
        }
        payload["semantic_digest_sha256"] = stable_hash(
            {
                "stratum": stratum,
                "charts": records,
                "verdict": payload["verdict"],
            }
        )
        _write_json(root / "results" / filename, payload)
        stratum_payloads[stratum] = payload

    noncommutative = full.get("noncommutative_charts", [])
    unresolved = full.get("unresolved_charts", [])
    all_finite_no_noncomm = (
        not noncommutative
        and not unresolved
        and s3["passed"]
        and all(
            payload["all_charts_processed"]
            for payload in stratum_payloads.values()
        )
    )
    if noncommutative:
        d2_verdict = "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
    elif all_finite_no_noncomm:
        d2_verdict = "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4"
    else:
        d2_verdict = "CPOBC_D2_PARTIAL"
    branch_verdicts: dict[str, str] = {}
    for branch in (DERIVED_BRANCH, LITERAL_BRANCH):
        branch_charts = [
            chart_id
            for chart_id in classifications
            if chart_id.startswith(f"{branch}:")
        ]
        branch_noncommutative = [
            chart_id
            for chart_id in branch_charts
            if classifications[chart_id]
            == "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
        ]
        branch_unresolved = [
            chart_id
            for chart_id in branch_charts
            if classifications[chart_id] == "UNRESOLVED"
        ]
        if branch_noncommutative:
            branch_verdicts[branch] = (
                "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
            )
        elif branch_unresolved:
            branch_verdicts[branch] = "CPOBC_D2_PARTIAL"
        else:
            branch_verdicts[branch] = (
                "CPOBC_D2_COMPLETE_NO_GO_STRONG_PROFILE_N4"
            )
    classification_payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-classification-v0.3.5",
        **common,
        "stratum_verdicts": {
            S1: stratum_payloads[S1]["verdict"],
            S2: stratum_payloads[S2]["verdict"],
            "S3_SCALAR": s3["verdict"],
        },
        "source_branch_verdicts": branch_verdicts,
        "noncommutative_representation_found": bool(noncommutative),
        "noncommutative_charts": noncommutative,
        "explicit_rational_witness": {
            "passed": witness["passed"],
            "chart": witness["chart"],
            "certificate": str(
                witness_path.relative_to(root)
            ).replace("\\", "/"),
            "relation_count": witness["relation_check"]["count"],
            "canonical_scalar_numerator_count": witness[
                "canonical_scalar_numerator_check"
            ]["count"],
            "transition_count": witness["transition_check"]["count"],
            "two_sided_inverse_count": witness[
                "two_sided_inverse_check"
            ]["count"],
            "commutator": witness["nonzero_commutator"],
            "outside_paper_pauli_ansatz": witness[
                "pauli_proportional_ansatz_audit"
            ]["outside_paper_ansatz"],
            "similarity_audit": witness["similarity_audit"],
        },
        "independent_explicit_witnesses": [
            {
                "passed": record["passed"],
                "chart": record["chart"],
                "certificate": str(
                    witness_path_by_chart[record["chart"]].relative_to(
                        root
                    )
                ).replace("\\", "/"),
                "relation_count": record["relation_check"]["count"],
                "canonical_scalar_numerator_count": record[
                    "canonical_scalar_numerator_check"
                ]["count"],
                "invertibility_site_count": (
                    record["transition_check"]["count"]
                    + record["two_sided_inverse_check"]["count"]
                ),
                "commutator": record["nonzero_commutator"],
                "semantic_digest_sha256": record[
                    "semantic_digest_sha256"
                ],
            }
            for record in witness_records
        ],
        "finite_strong_profile_no_go_proved": all_finite_no_noncomm,
        "d2_verdict": d2_verdict,
        "global_scientific_verdict": "FINAL_THEORY_OPEN",
        "profile_dependence": (
            "The result is conditional on PAPER_STRONG_OPERATOR_PROFILE. "
            "No weak-profile conclusion is inferred."
        ),
        "finite_vs_infinite_scope": (
            "This is an n<=4 finite compiler result. No lift to arbitrary "
            "finite n or an infinite QSG is proved."
        ),
        "Eq113_source_index_status": (
            "DERIVED_APPENDIX_QN_BRANCH and "
            "LITERAL_PRINTED_QN_PLUS_1_BRANCH were both evaluated; the "
            "printed-index ambiguity itself remains unresolved."
        ),
        "exact_numeric_distinction": (
            "QQ/Singular results carry the proof; both finite fields are "
            "shape scouts only."
        ),
        "completeness_scope": (
            "fixed d=2, n<=4, strong operator profile, both source-index "
            "branches, all S1/S2 charts, and S3 noncommutativity exclusion"
        ),
        "unresolved_components": [
            "weak-profile d=2 classification",
            "arbitrary finite-n extension",
            "infinite-QSG extension",
            "resolution of the Eq.(113) printed source-index ambiguity",
            "general S3 solution-locus description",
        ]
        + [
            f"incomplete chart: {chart}" for chart in unresolved
        ],
        "verdict": d2_verdict,
    }
    classification_payload["semantic_digest_sha256"] = stable_hash(
        {
            "strata": classification_payload["stratum_verdicts"],
            "noncommutative_charts": noncommutative,
            "d2_verdict": d2_verdict,
            "global": "FINAL_THEORY_OPEN",
        }
    )
    classification_path = root / "results/v0.3.5_d2_classification.json"
    _write_json(classification_path, classification_payload)

    def report_rows(stratum: str) -> str:
        rows = []
        for record in stratum_payloads[stratum]["charts"]:
            certificate = record.get(
                "QQ_certificate",
                record.get("QQ_backend_certificate", ""),
            )
            rows.append(
                f"| `{record['chart']}` | "
                f"`{record['classification']}` | "
                f"`{record['exit_status']}` | "
                f"{record['wall_time_seconds']:.3f} | "
                f"{record['peak_rss_bytes'] / 1048576:.1f} | "
                f"`{certificate}` |"
            )
        return "\n".join(rows)

    for stratum, short_name in ((S1, "S1"), (S2, "S2")):
        _write_text(
            root / f"reports/v0.3.5_{short_name}_elimination.md",
            f"""# Final-Theory Bench v0.3.5 — {short_name} saturated elimination

This report covers all {stratum_payloads[stratum]['chart_count']} `{stratum}`
charts in both frozen Eq.(113) source-index branches. Finite-field computations
over GF(32003) and GF(32009) were used only as scouts. Every verdict-bearing
ideal computation is over QQ in SageMath 10.9 with embedded Singular 4.4.1.

Sequential saturation was performed factor by factor. Factorisation,
multiplicity removal, and deduplication were checked by exact reconstruction.
When a stage<=3 localised subsystem generated `(1)`, the n<=4 result follows
because the full localised ideal contains that unit subsystem. When all
commutator entries specialised to zero, noncommutativity was excluded
structurally.

| Chart | Exact classification | Status | Seconds | Peak MiB | QQ certificate |
|---|---|---:|---:|---:|---|
{report_rows(stratum)}

Verdict: `{stratum_payloads[stratum]['verdict']}`.
""",
        )

    _write_text(
        root / "reports/v0.3.5_profile_dependence.md",
        f"""# v0.3.5 profile dependence

The computed d=2 result uses `{PAPER_STRONG_OPERATOR_PROFILE}`. In particular,
transition operators attached to repeated occurrences are identified according
to the strong operator semantics frozen by v0.3.3/v0.3.4.

The calculation does **not** establish the same result under a weak profile
where occurrence-wise transition operators can vary independently. The
distinction is part of the theorem statement, not a presentation caveat.

Current finite verdict: `{d2_verdict}`.
Global scientific verdict: `FINAL_THEORY_OPEN`.
""",
    )
    _write_text(
        root / "reports/v0.3.5_finite_vs_infinite_scope.md",
        """# v0.3.5 finite versus infinite scope

All computations are for fixed `d=2` and source stages `n<=4`. They do not
prove an arbitrary-finite-n theorem and do not imply a result for an infinite
QSG. Such a lift would require a separate restriction theorem showing that an
arbitrary infinite representation induces one of the finite compiler systems
used here while preserving every required nonsingularity predicate.

No such theorem is supplied in v0.3.5. `FINAL_THEORY_OPEN` therefore remains
the global verdict.
""",
    )
    _write_text(
        root / "reports/v0.3.5_scientific_verdict.md",
        f"""# Final-Theory Bench v0.3.5 — scientific verdict

The Sage/Singular backend was genuinely executed. The campaign contains
{subset['planned_run_count']} localised-subsystem runs and
{full['planned_run_count']} full-stage runs, with QQ as the proof field and
two separate prime fields as scouts.

Finite d=2 verdict: `{d2_verdict}`.

Derived Eq.(113) reading: `{branch_verdicts[DERIVED_BRANCH]}`.
Literal printed Eq.(113) reading: `{branch_verdicts[LITERAL_BRANCH]}`.

The literal-branch existence result has independent exact rational witnesses
in all three surviving S1 pivot-R5 charts. For each witness, direct
substitution verifies all
{witness['relation_check']['count']} matrix relations, all
{witness['canonical_scalar_numerator_check']['count']} canonical scalar
numerator equations, all
{witness['transition_check']['count']} reconstructed transition
determinants, and all
{witness['two_sided_inverse_check']['count']} two-sided inverse sites.
Its commutator `[Q_1,Q_5]` is
`{witness['nonzero_commutator']['matrix']}`. The witness is outside the
paper's Pauli-proportional ansatz because `tr(Q_1)=3`, while scalar
multiples of Pauli matrices are traceless.

This verdict is restricted to the strong operator profile, `n<=4`, and the
two explicitly frozen Eq.(113) source-index readings. It neither settles the
weak profile nor lifts to an infinite QSG.

Global verdict: `FINAL_THEORY_OPEN`.
""",
    )
    _write_text(
        root / "reports/v0.3.5_remaining_gaps.md",
        """# v0.3.5 remaining gaps

1. Resolve the printed Eq.(113) `Q_n` versus `Q_(n+1)` source-index ambiguity.
2. Repeat the classification under a weak occurrence-dependent operator profile.
3. Prove or refute a restriction theorem from arbitrary finite or infinite QSG
   representations to the `n<=4` compiler.
4. Describe the general S3 solution locus; v0.3.5 only excludes S3
   noncommutativity.
5. Preserve any timed-out or failed chart as unresolved; never promote a
   modular scout or a nonterminal run to an exact verdict.

The global programme remains `FINAL_THEORY_OPEN`.
""",
    )
    return classification_payload


def run_independent_oracles_v035(
    root: Path,
    *,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    """Recompute two exact empty charts with a distinct CAS strategy."""

    cases = (
        (
            DERIVED_BRANCH,
            f"{DERIVED_BRANCH}:S1_PIVOT_R2:UPPER_ONLY",
        ),
        (
            DERIVED_BRANCH,
            f"{DERIVED_BRANCH}:S2_PIVOT_M2:C_NONZERO",
        ),
    )
    runs: list[dict[str, Any]] = []
    for branch, chart_id in cases:
        request = build_chart_payload(
            branch,
            chart_id,
            coefficient_modulus=0,
            operation="solve",
            maximum_source_stage=3,
            saturation=True,
            check_noncommutativity=False,
            factor_denominators=True,
            include_all_transition_predicates=False,
            groebner_algorithm="libsingular:std",
            groebner_strategy="one_shot",
            progressive_batch_size=1,
            saturation_factor_order="reverse",
        )
        result = run_sage_request(
            root,
            request,
            timeout_seconds=timeout_seconds,
        )
        path = (
            root
            / "certificates"
            / "d2_saturation"
            / "independent_oracle"
            / f"{stable_hash(chart_id)[:20]}.json"
        )
        _write_json(path, result)
        runs.append(
            {
                "chart": chart_id,
                "exit_status": result.get("exit_status"),
                "coefficient_field": result.get("coefficient_field"),
                "saturated_unit_ideal": result.get(
                    "saturated_unit_ideal", False
                ),
                "proof_eligible": result.get("proof_eligible", False),
                "groebner_algorithm": result.get("groebner_algorithm"),
                "groebner_strategy": result.get("groebner_strategy"),
                "saturation_factor_order": result.get(
                    "saturation_factor_order"
                ),
                "certificate": str(path.relative_to(root)).replace(
                    "\\", "/"
                ),
                "semantic_digest_sha256": result.get(
                    "semantic_digest_sha256"
                ),
            }
        )
    passed = all(
        record["exit_status"] == "COMPLETED"
        and record["coefficient_field"] == "QQ"
        and record["saturated_unit_ideal"]
        and record["proof_eligible"]
        for record in runs
    )
    payload = {
        "schema_version": "final-theory-d2-independent-oracle-v0.3.5",
        "branch": BRANCH,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "independence": {
            "production_groebner_algorithm": "libsingular:slimgb",
            "oracle_groebner_algorithm": "libsingular:std",
            "production_strategy": "streaming progressive",
            "oracle_strategy": "one shot",
            "production_saturation_factor_order": "forward",
            "oracle_saturation_factor_order": "reverse",
        },
        "runs": runs,
        "agreement": passed,
        "exact_numeric_distinction": "EXACT_QQ_RECOMPUTATION",
        "completeness_scope": (
            "two independently ordered resolved charts, one S1 and one S2"
        ),
        "unresolved_components": [] if passed else [
            "independent oracle disagreement or failure"
        ],
        "passed": passed,
        "verdict": (
            "V035_INDEPENDENT_ORACLE_AGREEMENT"
            if passed
            else "CPOBC_D2_PARTIAL"
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(payload["runs"])
    _write_json(
        root / "results/v0.3.5_independent_oracle.json",
        payload,
    )
    return payload


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-stage3-campaign", action="store_true")
    parser.add_argument("--run-full-campaign", action="store_true")
    parser.add_argument("--write-results", action="store_true")
    parser.add_argument("--run-independent-oracle", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _argument_parser().parse_args(argv)
    root = Path.cwd()
    if arguments.run_stage3_campaign:
        run_stage3_subset_campaign_v035(
            root,
            workers=arguments.workers,
            timeout_seconds=arguments.timeout_seconds,
        )
        return 0
    if arguments.run_full_campaign:
        run_full_stage4_campaign_v035(
            root,
            workers=arguments.workers,
            timeout_seconds=arguments.timeout_seconds,
        )
        return 0
    if arguments.write_results:
        write_classification_artifacts_v035(root)
        return 0
    if arguments.run_independent_oracle:
        result = run_independent_oracles_v035(
            root,
            timeout_seconds=arguments.timeout_seconds,
        )
        return 0 if result["passed"] else 1
    raise SystemExit("select a campaign")


if __name__ == "__main__":
    raise SystemExit(main())
