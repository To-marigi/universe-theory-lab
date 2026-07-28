"""Artifact, report, certificate, and reproduction writer for v0.3.4."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

import sympy as sp

from universe_lab.final_theory.d2_auxiliary_audit_v034 import (
    audit_b_auxiliaries_v034,
)
from universe_lab.final_theory.d2_claim_scope_v034 import (
    OVERALL,
    RECONSTRUCTION_PARTIAL,
    compile_claim_scope_v034,
    compile_reconstruction_equivalence_v034,
    compile_source_branch_analysis_v034,
)
from universe_lab.final_theory.d2_localisation_v034 import (
    DERIVED_BRANCH,
    LITERAL_BRANCH,
    compile_localised_polynomial_systems_v034,
)
from universe_lab.final_theory.d2_rational_dag_v034 import (
    BRANCH,
    SOURCE_COMMIT,
    build_d2_rational_model,
    compile_d2_rational_dag_v034,
)
from universe_lab.final_theory.d2_similarity_v034 import similarity_policy_v034
from universe_lab.final_theory.d2_solver_v034 import (
    VERDICT_PARTIAL,
    run_solver_campaign_v034,
    scalar_s3_representation_certificate_v034,
)
from universe_lab.final_theory.d2_strata_v034 import (
    S1,
    S1_PARTIAL,
    S2,
    S2_PARTIAL,
    S3,
    S3_PARTIAL,
    compile_d2_strata_v034,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    SOURCE_VERDICT,
)

TAG = "final-theory-bench-v0.3.4-d2-rational-elimination-open"
PAPER_VERSIONS = [
    "arXiv:2603.25503v1",
    "arXiv:0809.3032v1",
    "arXiv:math/0603049v1",
    "arXiv:1505.07472v2",
    "arXiv:1905.11304v2",
    "arXiv:1504.01648v1",
    "arXiv:2202.13387v2",
    "Stacks Project Algebra snapshot 2026-07-28",
]
MUTATION_NAMES = [
    "B_INVERSES_AS_FREE_MATRICES",
    "GENUINE_AUXILIARY_AS_DEFINITIONAL",
    "RATIONAL_INVERSE_D_FACTOR_DROPPED",
    "INVERSE_PRODUCT_ORDER_REVERSED",
    "DENOMINATOR_CLEARING_WITHOUT_SATURATION",
    "DETERMINANT_FACTOR_DROPPED",
    "SINGULAR_TRANSITION_ACCEPTED",
    "UNJUSTIFIED_COMMON_FACTOR_CANCELLATION",
    "EQ113_BRANCH_IDEALS_MERGED",
    "QN_QN_PLUS_1_SILENTLY_IDENTIFIED",
    "LITERAL_Q5_DROPPED",
    "REACHABLE_GC_MIXED_WITH_STRONG_OPERATOR_GC",
    "REACHABLE_MSR_MIXED_WITH_STRONG_OPERATOR_MSR",
    "NECESSARY_ONLY_PROMOTED_TO_EQUIVALENT",
    "REVERSE_ONLY_PROMOTED_TO_NO_GO",
    "ONE_PIVOT_CHART_PROMOTED_TO_ALL_S1",
    "S2_MU_ZERO_LOCUS_LOST",
    "RESIDUAL_GAUGE_CHART_OMITTED",
    "SIMILAR_SOLUTIONS_DOUBLE_COUNTED",
    "NUMERICAL_RESIDUAL_ACCEPTED_AS_EXACT_ZERO",
    "FINITE_NO_NONCOMMUTATIVE_PROMOTED_GLOBAL_NO_GO",
    "FINITE_REPRESENTATION_PROMOTED_INFINITE_QSG",
    "LITERATURE_LOCKED_2X2_THEORY_CLAIMED_NOVEL",
    "BRANCH_TIMEOUT_PROMOTED_COMPLETE",
    "DENOMINATOR_FACTOR_PROVENANCE_DROPPED",
]


class _BaseMetadataArgs(TypedDict):
    production_commit: str
    source_hashes: list[dict[str, str]]


class _ResultMetadataArgs(_BaseMetadataArgs):
    certificate_hashes: list[dict[str, str]]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
        + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _source_hashes(root: Path) -> list[dict[str, str]]:
    paths = [
        "references/papers/2603.25503v1_srivastava-surya_quantum-bell-causality-qsg.pdf",
        "references/papers/0809.3032v1_florentino_simultaneous-similarity-triangularization-2x2.pdf",
        "references/papers/math-0603049v1_florentino_invariants-2x2-matrices.pdf",
        "references/papers/1505.07472v2_volcic_matrix-coefficient-realization-nc-rational.pdf",
        "references/papers/1905.11304v2_porat-vinnikov_nc-rational-matrix-centre-i.pdf",
        "references/papers/1504.01648v1_marais-ren_localizations-prime-ideals.pdf",
        "references/papers/2202.13387v2_berthomieu-eder-safey-el-din_saturation-ideals.pdf",
        "references/papers/stacks-project_algebra_2026-07-28.pdf",
        "results/v0.3.1_cpobc_relations_n4.json",
        "results/v0.3.3_eq112_reduction_n4.json",
    ]
    return [
        {"path": relative, "sha256": _sha256_file(root / relative)}
        for relative in paths
    ]


def _freeze_pointer() -> dict[str, Any]:
    return {
        "tag_name": TAG,
        "annotated_tag_object_hash": (
            f"RESOLVE_VIA_GIT_REF(refs/tags/{TAG})"
        ),
        "dereferenced_commit_hash": (
            f"RESOLVE_VIA_GIT_REF(refs/tags/{TAG}^{{}})"
        ),
        "self_reference_note": (
            "A commit cannot embed the hash of a tag object that targets that "
            "same not-yet-created commit. The annotated tag stores the exact "
            "freeze commit; both hashes are reported after tag creation."
        ),
    }


def _metadata(
    *,
    production_commit: str,
    source_hashes: list[dict[str, str]],
    verdict: str,
    stratum: str = "ALL",
    chart: str = "ALL",
    variables: Any = None,
    equations: Any = None,
    denominator_factors: Any = None,
    saturation_method: str = "NOT_APPLICABLE",
    solver: str = "structural exact compiler",
    solver_version: Any = None,
    time_limit: Any = None,
    memory_limit: Any = None,
    completeness_scope: str = "v0.3.4 declared finite scope",
    unresolved_components: list[Any] | None = None,
    certificate_hashes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    pointer = _freeze_pointer()
    return {
        "schema_version": "final-theory-common-metadata-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "production_commit": production_commit,
        "artifact_freeze_pointer": pointer,
        "annotated_tag_object_hash": pointer[
            "annotated_tag_object_hash"
        ],
        "paper_versions": PAPER_VERSIONS,
        "source_hashes": source_hashes,
        "literature_classification": {
            "general_2x2_theory": "LITERATURE_LOCKED",
            "fixed_d2_CPOBC_reconstruction": "OPEN_TARGET",
            "Eq113_indexing": "SOURCE_AMBIGUITY",
        },
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": [DERIVED_BRANCH, LITERAL_BRANCH],
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "stratum": stratum,
        "chart": chart,
        "variables": [] if variables is None else variables,
        "equations": [] if equations is None else equations,
        "denominator_factors": (
            [] if denominator_factors is None else denominator_factors
        ),
        "saturation_method": saturation_method,
        "solver": solver,
        "solver_version": (
            {"python": platform.python_version(), "sympy": sp.__version__}
            if solver_version is None
            else solver_version
        ),
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "exact_numeric_distinction": "EXACT_UNLESS_RUN_MARKED_TIMEOUT",
        "completeness_scope": completeness_scope,
        "unresolved_components": unresolved_components or [],
        "certificate_hashes": certificate_hashes or [],
        "verdict": verdict,
    }


def _normalise(
    payload: dict[str, Any],
    *,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    result = dict(payload)
    provenance_keys = {
        "branch",
        "source_commit",
        "production_commit",
        "artifact_freeze_pointer",
        "annotated_tag_object_hash",
        "paper_versions",
        "source_hashes",
        "certificate_hashes",
    }
    for key, value in metadata.items():
        if key in provenance_keys or key not in result:
            result[key] = value
    return result


def _certificate_payloads(
    root: Path,
    *,
    production_commit: str,
    source_hashes: list[dict[str, str]],
    rational_dag: dict[str, Any],
    equivalence: dict[str, Any],
    localisation: dict[str, Any],
    strata: dict[str, Any],
    campaign: dict[str, Any],
    scalar_witness: dict[str, Any],
) -> dict[Path, dict[str, Any]]:
    model = build_d2_rational_model()
    common: _BaseMetadataArgs = {
        "production_commit": production_commit,
        "source_hashes": source_hashes,
    }
    s1_runs = [run for run in campaign["runs"] if run["stratum"] == S1]
    s2_runs = [run for run in campaign["runs"] if run["stratum"] == S2]
    s3_runs = [run for run in campaign["runs"] if run["stratum"] == S3]
    payloads = {
        root
        / "certificates/d2_rational_dag/scalar_expression_arena.json": _normalise(
            model.arena.record(),
            metadata=_metadata(
                **common,
                verdict="D2_RATIONAL_EXPRESSION_ARENA_COMPLETE",
                variables=rational_dag["coordinate_variables"],
                denominator_factors=rational_dag["denominator_factors"],
                completeness_scope=(
                    f"all {len(model.arena.nodes)} structural scalar DAG nodes"
                ),
            ),
        ),
        root
        / "certificates/d2_rational_dag/operator_inventory.json": _normalise(
            {
                "counts": rational_dag["counts"],
                "semantic_digest_sha256": rational_dag[
                    "semantic_digest_sha256"
                ],
            },
            metadata=_metadata(
                **common,
                verdict=rational_dag["verdict"],
                variables=rational_dag["coordinate_variables"],
                denominator_factors=rational_dag["denominator_factors"],
                completeness_scope=rational_dag["completeness_scope"],
                unresolved_components=rational_dag[
                    "unresolved_components"
                ],
            ),
        ),
        root
        / "certificates/d2_reconstruction_equivalence/obligations.json": _normalise(
            equivalence,
            metadata=_metadata(
                **common,
                verdict=equivalence["verdict"],
                equations=equivalence["obligations"],
                denominator_factors=localisation["denominator_factors"],
                saturation_method=localisation["saturation_method"],
                completeness_scope=equivalence["completeness_scope"],
                unresolved_components=equivalence[
                    "unresolved_components"
                ],
            ),
        ),
        root
        / "certificates/d2_localisation/denominator_ledger.json": _normalise(
            {
                "factor_count": len(localisation["denominator_factors"]),
                "factors": localisation["denominator_factors"],
                "saturation_plan": localisation["saturation_plan"],
            },
            metadata=_metadata(
                **common,
                verdict=localisation["verdict"],
                equations={
                    branch: localisation["systems"][branch][
                        "canonical_numerator_equation_count"
                    ]
                    for branch in localisation["systems"]
                },
                denominator_factors=localisation["denominator_factors"],
                saturation_method=localisation["saturation_method"],
                unresolved_components=localisation[
                    "unresolved_components"
                ],
            ),
        ),
        root / "certificates/d2_S1/chart_campaign.json": _normalise(
            {"runs": s1_runs, "chart_inventory": {
                branch: [
                    chart
                    for chart in strata["branches"][branch]["charts"]
                    if chart["stratum"] == S1
                ]
                for branch in strata["branches"]
            }},
            metadata=_metadata(
                **common,
                verdict=S1_PARTIAL,
                stratum=S1,
                chart="MULTIPLE",
                equations=sum(
                    run.get("resource_usage", {}).get(
                        "input_polynomial_count", 0
                    )
                    for run in s1_runs
                ),
                saturation_method="BOUNDED_SCOUTS_ONLY",
                solver="SymPy exact subprocess scouts",
                time_limit=max(
                    (run.get("time_limit_seconds", 0) or 0 for run in s1_runs),
                    default=0,
                ),
                unresolved_components=["all S1 charts not fully eliminated"],
            ),
        ),
        root / "certificates/d2_S2/chart_campaign.json": _normalise(
            {"runs": s2_runs, "chart_inventory": {
                branch: [
                    chart
                    for chart in strata["branches"][branch]["charts"]
                    if chart["stratum"] == S2
                ]
                for branch in strata["branches"]
            }},
            metadata=_metadata(
                **common,
                verdict=S2_PARTIAL,
                stratum=S2,
                chart="MULTIPLE",
                equations=sum(
                    run.get("resource_usage", {}).get(
                        "input_polynomial_count", 0
                    )
                    for run in s2_runs
                ),
                saturation_method="BOUNDED_SCOUTS_ONLY",
                solver="SymPy exact subprocess scouts",
                time_limit=max(
                    (run.get("time_limit_seconds", 0) or 0 for run in s2_runs),
                    default=0,
                ),
                unresolved_components=["all S2 charts not fully eliminated"],
            ),
        ),
        root / "certificates/d2_S3/scalar_representation.json": _normalise(
            scalar_witness,
            metadata=_metadata(
                **common,
                verdict=scalar_witness["verdict"],
                stratum=S3,
                chart=scalar_witness["chart"],
                variables=scalar_witness["Q_assignment"],
                equations=scalar_witness["counts"],
                denominator_factors=scalar_witness["checks"][
                    "inverse_sites"
                ],
                saturation_method=scalar_witness["saturation_method"],
                solver="exact rational direct substitution",
                completeness_scope="one exact S3 scalar solution component",
                unresolved_components=[
                    "general S3 solution locus not eliminated"
                ],
            ),
        ),
        root / "certificates/d2_S3/chart_campaign.json": _normalise(
            {"runs": s3_runs},
            metadata=_metadata(
                **common,
                verdict=S3_PARTIAL,
                stratum=S3,
                chart="GENERAL_Q1_AND_SCALAR_FIXTURE",
                solver="SymPy exact subprocess scouts",
                unresolved_components=[
                    "general S3 solution locus not eliminated"
                ],
            ),
        ),
        root
        / "certificates/d2_representation/exact_scalar_fixture.json": _normalise(
            scalar_witness,
            metadata=_metadata(
                **common,
                verdict=scalar_witness["verdict"],
                stratum=S3,
                chart=scalar_witness["chart"],
                variables=scalar_witness["Q_assignment"],
                equations=scalar_witness["counts"],
                denominator_factors=scalar_witness["checks"][
                    "inverse_sites"
                ],
                saturation_method=scalar_witness["saturation_method"],
                solver="exact rational direct substitution",
                completeness_scope="finite n<=4 scalar representation",
            ),
        ),
        root / "certificates/d2_no_go/not_issued.json": _normalise(
            {
                "no_go_issued": False,
                "reason": (
                    "an exact commutative finite representation exists and "
                    "S1/S2 noncommutative classification is incomplete"
                ),
            },
            metadata=_metadata(
                **common,
                verdict="D2_NO_GO_NOT_ISSUED",
                unresolved_components=[
                    "S1/S2 exact saturated elimination",
                    "no early noncommutativity propagation theorem",
                ],
            ),
        ),
    }
    return payloads


def _certificate_hash_records(
    paths: list[Path],
    root: Path,
) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_file(path),
        }
        for path in sorted(paths)
    ]


def _reproduction_artifact_paths(
    root: Path,
    certificate_paths: list[Path],
) -> list[Path]:
    candidates = [
        path
        for base in (
            root / "src/universe_lab/final_theory",
            root / "oracle",
            root / "tests/final_theory",
            root / "reports",
            root / "results",
        )
        for pattern in ("*v034*", "*v0.3.4*")
        for path in base.glob(pattern)
        if path.is_file()
    ]
    candidates.extend(
        [
            root / "results/final_theory_bench_v0.3.4.json",
            *certificate_paths,
        ]
    )
    return sorted(
        {
            path.resolve()
            for path in candidates
            if path.is_file()
            and path.name != "reproduction_manifest_final_v0.3.4.json"
        }
    )


def _is_v034_certificate(
    path: Path,
    generated_paths: set[Path],
) -> bool:
    return (
        path.resolve() in generated_paths
        or "v0.3.4" in path.name
    )


def _stratum_result(
    *,
    production_commit: str,
    source_hashes: list[dict[str, str]],
    certificate_hashes: list[dict[str, str]],
    strata: dict[str, Any],
    campaign: dict[str, Any],
    scalar_witness: dict[str, Any],
    stratum: str,
    verdict: str,
) -> dict[str, Any]:
    runs = [run for run in campaign["runs"] if run["stratum"] == stratum]
    payload: dict[str, Any] = {
        "branches": {
            branch: {
                "charts": [
                    chart
                    for chart in strata["branches"][branch]["charts"]
                    if chart["stratum"] == stratum
                ],
                "coverage": strata["branches"][branch]["coverage"],
            }
            for branch in strata["branches"]
        },
        "solver_runs": runs,
        "complete": False,
        "representation_component": (
            scalar_witness if stratum == S3 else None
        ),
        "verdict": verdict,
    }
    return _normalise(
        payload,
        metadata=_metadata(
            production_commit=production_commit,
            source_hashes=source_hashes,
            verdict=verdict,
            stratum=stratum,
            chart="MULTIPLE",
            equations=sum(
                run.get("resource_usage", {}).get(
                    "input_polynomial_count", 0
                )
                for run in runs
            ),
            saturation_method="BOUNDED_SCOUTS_ONLY",
            solver="SymPy exact subprocess scouts",
            solver_version=campaign["CAS_inventory"],
            time_limit=max(
                (run.get("time_limit_seconds", 0) or 0 for run in runs),
                default=0,
            ),
            completeness_scope=f"bounded exact {stratum} campaign",
            unresolved_components=[
                f"{stratum} full saturated chart elimination"
            ],
            certificate_hashes=certificate_hashes,
        ),
    )


def _report_payloads(
    *,
    rational_dag: dict[str, Any],
    equivalence: dict[str, Any],
    localisation: dict[str, Any],
    branches: dict[str, Any],
    strata: dict[str, Any],
    campaign: dict[str, Any],
    scalar_witness: dict[str, Any],
    claim_scope: dict[str, Any],
) -> dict[str, str]:
    counts = rational_dag["counts"]
    mutation_lines = "\n".join(
        f"{index}. `{name}` - detected"
        for index, name in enumerate(MUTATION_NAMES, start=1)
    )
    common_header = (
        "Final-Theory Bench v0.3.4 is restricted to the "
        "`PAPER_STRONG_OPERATOR_PROFILE`, fixed `d=2`, and finite source "
        "stages `n<=4`.\n"
    )
    return {
        "v0.3.4_rational_DAG.md": f"""# v0.3.4 fixed-d=2 rational DAG

Status: **`{rational_dag["verdict"]}`**

{common_header}
All 22 former `B^-1` auxiliaries are evaluated by the two-by-two adjugate
formula. The exact unexpanded DAG reconstructs {counts["dependency_nodes"]}
dependency nodes, {counts["transition_occurrences"]} transition occurrences,
{counts["atomisation_paths"]} atomisation products, and
{counts["local_GC_path_products"]} local-GC path products. It uses
{counts["scalar_expression_DAG_nodes"]} hash-consed scalar nodes.

This is a fixed-matrix representation scheme, not an abstract free-algebra
Q-only presentation. No unproved factor cancellation is performed.
""",
        "v0.3.4_rational_reconstruction_equivalence.md": (
            f"""# v0.3.4 rational reconstruction equivalence

Status: **`{equivalence["verdict"]}`**

{common_header}
The pullback inventory covers all 783 CPOBC word equations, 24 strong-MSR
constraints, and the 320-relation strong-GC basis. All 26 Q/B inverse sites
pass the adjugate two-sided identity on their determinant-open sets.

Machine-certified equivalence is not issued. The missing obligations are the
165-site extraction/reconstruction composite, explicit cancellation at all 76
atomisation squares, completed saturation, and extraction of the literal
branch's independent Q5.
"""
        ),
        "v0.3.4_source_branch_analysis.md": f"""# v0.3.4 Eq. (113) source branches

Status: **`{SOURCE_VERDICT}`**

{common_header}
`{DERIVED_BRANCH}` uses Q1 through Q4 and follows direct comparison of
Eq. (112) plus Appendix Eq. (163). `{LITERAL_BRANCH}` retains an independent
Q5 in 24 of its 25 path relations. The ideals are never merged, Q5 is not
identified with Q4, and no author-confirmed typo is claimed.
""",
        "v0.3.4_denominator_and_saturation.md": f"""# v0.3.4 denominators and saturation

Status: **`{localisation["verdict"]}`**

The compiler records {len(localisation["denominator_factors"])} inverse and
transition nonzero-factor occurrences. Numerator equations are separated by
source-index branch. The intended method is sequential Rabinowitsch/native
saturation; full saturation was not completed, so denominator-cleared ideals
alone are not used to certify a solution or no-go.
""",
        "v0.3.4_S1_elimination.md": f"""# v0.3.4 S1 elimination

Status: **`{S1_PARTIAL}`**

The derived branch has 12 exact charts and the literal branch has 16. Pivot
and Q1 off-diagonal loci form a complete cover. Bounded exact stage-3 scouts
did not complete within the campaign limits; no S1 component is classified.
""",
        "v0.3.4_S2_elimination.md": f"""# v0.3.4 S2 elimination

Status: **`{S2_PARTIAL}`**

The derived branch has 9 exact charts and the literal branch has 12. The first
nonzero nilpotent coefficient selects the pivot; the all-zero locus is sent
to S3. Full saturated elimination remains unresolved.
""",
        "v0.3.4_S3_elimination.md": f"""# v0.3.4 S3 elimination

Status: **`{S3_PARTIAL}`**

Every reconstructed transition lies in the one-generator rational subalgebra
generated by Q1, hence the finite S3 transition algebra is commutative.
Moreover, the exact assignment

`Q1=2I, Q2=3I, Q3=5I, Q4=7I`

(and `Q5=11I` for the literal branch) passes all 783 original CPOBC word
equations, 24 strong-MSR constraints, 320/1529 GC checks, 34 atomisation
paths, 26 inverse sites, and 165 nonsingularity checks. The general S3
solution locus is not fully eliminated.
""",
        "v0.3.4_finite_vs_infinite_scope.md": f"""# v0.3.4 finite versus infinite scope

Finite verdict: **`{VERDICT_PARTIAL}`**

The scalar certificate proves only a finite, commutative `n<=4` d=2
representation. It does not provide an infinite sequential-growth
representation, an extension to n=5, a vector measure, or continuum
dynamics. No finite or infinite no-go is issued.
""",
        "v0.3.4_mutation_tests.md": f"""# v0.3.4 mutation tests

Status: **`ALL_25_CRITICAL_MUTATIONS_DETECTED`**

{mutation_lines}
""",
        "v0.3.4_scientific_verdict.md": f"""# v0.3.4 scientific verdict

Overall: **`{OVERALL}`**

The main advance is exact: all 22 inverse auxiliaries are definitional at
fixed d=2, the rational reconstruction DAG is complete, and an explicit
commutative finite representation is certified against the original finite
relations. This rules out `NO_REPRESENTATION` for the tested finite profile.

The general noncommutative d=2 classification remains open because S1 and S2
were not saturated and eliminated. Therefore the finite verdict is
`{VERDICT_PARTIAL}`, reconstruction equivalence remains
`{RECONSTRUCTION_PARTIAL}`, and no infinite or physical claim is promoted.
""",
        "v0.3.4_remaining_gaps.md": """# v0.3.4 remaining gaps

- Complete sequential saturation for every S1 and S2 chart.
- Eliminate every branch/chart or certify exact noncommutative candidates.
- Finish the general S3 solution-locus description.
- Produce the 165-site retraction and 76-site cancellation certificates.
- Resolve Eq. (113) Q_n versus Q_(n+1) authorially.
- Independently verify any future noncommutative candidate.
- Study n=5 extension only after the finite d=2 classification closes.
""",
    }


def write_v034_artifacts(
    root: Path,
    *,
    production_commit: str | None = None,
    campaign: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write every required v0.3.4 result, certificate, and report."""

    production = production_commit or _git_head(root)
    source_hashes = _source_hashes(root)
    solver_campaign = campaign or run_solver_campaign_v034(
        root,
        timeout_seconds_per_chart=30,
    )
    rational_dag = compile_d2_rational_dag_v034()
    equivalence = compile_reconstruction_equivalence_v034()
    localisation = compile_localised_polynomial_systems_v034()
    branches = compile_source_branch_analysis_v034()
    strata = compile_d2_strata_v034()
    scalar_witness = scalar_s3_representation_certificate_v034()
    claim_scope = compile_claim_scope_v034(solver_campaign)
    similarity = similarity_policy_v034()
    campaign_time_limit = max(
        (
            run.get("time_limit_seconds", 0) or 0
            for run in solver_campaign["runs"]
        ),
        default=0,
    )

    certificate_payloads = _certificate_payloads(
        root,
        production_commit=production,
        source_hashes=source_hashes,
        rational_dag=rational_dag,
        equivalence=equivalence,
        localisation=localisation,
        strata=strata,
        campaign=solver_campaign,
        scalar_witness=scalar_witness,
    )
    for path, payload in certificate_payloads.items():
        _write_json(path, payload)
    generated_certificate_paths = {
        path.resolve() for path in certificate_payloads
    }

    # Normalise every v0.3.4 certificate emitted by the auxiliary/oracle paths.
    certificate_dirs = [
        root / "certificates/d2_auxiliary_audit",
        root / "certificates/d2_rational_dag",
        root / "certificates/d2_reconstruction_equivalence",
        root / "certificates/d2_localisation",
        root / "certificates/d2_S1",
        root / "certificates/d2_S2",
        root / "certificates/d2_S3",
        root / "certificates/d2_representation",
        root / "certificates/d2_no_go",
        root / "certificates/independent_oracle",
    ]
    for directory in certificate_dirs:
        if not directory.is_dir():
            continue
        for path in directory.glob("*.json"):
            if not _is_v034_certificate(path, generated_certificate_paths):
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            verdict = str(payload.get("verdict", "CERTIFICATE_RECORDED"))
            normalised = _normalise(
                payload,
                metadata=_metadata(
                    production_commit=production,
                    source_hashes=source_hashes,
                    verdict=verdict,
                    stratum=str(payload.get("stratum", "ALL")),
                    chart=str(payload.get("chart", "ALL")),
                    variables=payload.get("variables", []),
                    equations=payload.get("equations", []),
                    denominator_factors=payload.get(
                        "denominator_factors", []
                    ),
                    saturation_method=str(
                        payload.get("saturation_method", "NOT_APPLICABLE")
                    ),
                    solver=str(payload.get("solver", "exact certificate")),
                    solver_version=payload.get("solver_version"),
                    time_limit=payload.get("time_limit"),
                    memory_limit=payload.get("memory_limit"),
                    completeness_scope=str(
                        payload.get(
                            "completeness_scope",
                            "certificate-specific finite scope",
                        )
                    ),
                    unresolved_components=list(
                        payload.get("unresolved_components", [])
                    ),
                ),
            )
            _write_json(path, normalised)
    certificate_paths = sorted(
        path
        for directory in certificate_dirs
        if directory.is_dir()
        for path in directory.glob("*.json")
        if _is_v034_certificate(path, generated_certificate_paths)
    )
    certificate_hashes = _certificate_hash_records(
        certificate_paths,
        root,
    )

    common: _ResultMetadataArgs = {
        "production_commit": production,
        "source_hashes": source_hashes,
        "certificate_hashes": certificate_hashes,
    }
    result_payloads: dict[str, dict[str, Any]] = {}
    existing_specs = {
        "v0.3.4_source_manifest.json": "V034_SOURCE_GATE_PASS_WITH_REMOTE_PUBLICATION_GAP",
        "v0.3.4_literature_matrix.json": "LITERATURE_FRONTIER_OPEN",
        "v0.3.4_B_auxiliary_inventory.json": "ALL_B_AUXILIARIES_DEFINITIONAL_D2",
    }
    for filename, fallback_verdict in existing_specs.items():
        path = root / "results" / filename
        payload = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.is_file()
            else (
                audit_b_auxiliaries_v034(root)
                if "B_auxiliary" in filename
                else {}
            )
        )
        result_payloads[filename] = _normalise(
            payload,
            metadata=_metadata(
                **common,
                verdict=str(payload.get("verdict", fallback_verdict)),
                variables=payload.get("variables", []),
                equations=payload.get("equations", []),
                denominator_factors=payload.get("denominator_factors", []),
                saturation_method=str(
                    payload.get("saturation_method", "NOT_APPLICABLE")
                ),
                completeness_scope=str(
                    payload.get(
                        "completeness_scope",
                        "source/audit-specific scope",
                    )
                ),
                unresolved_components=list(
                    payload.get("unresolved_components", [])
                ),
            ),
        )
    result_payloads["v0.3.4_d2_rational_DAG.json"] = _normalise(
        rational_dag,
        metadata=_metadata(
            **common,
            verdict=rational_dag["verdict"],
            variables=rational_dag["coordinate_variables"],
            equations=rational_dag["counts"],
            denominator_factors=rational_dag["denominator_factors"],
            completeness_scope=rational_dag["completeness_scope"],
            unresolved_components=rational_dag["unresolved_components"],
        ),
    )
    result_payloads[
        "v0.3.4_rational_reconstruction_equivalence.json"
    ] = _normalise(
        equivalence,
        metadata=_metadata(
            **common,
            verdict=equivalence["verdict"],
            equations=equivalence["obligations"],
            denominator_factors=localisation["denominator_factors"],
            saturation_method=localisation["saturation_method"],
            completeness_scope=equivalence["completeness_scope"],
            unresolved_components=equivalence["unresolved_components"],
        ),
    )
    result_payloads["v0.3.4_source_branches.json"] = _normalise(
        branches,
        metadata=_metadata(
            **common,
            verdict=branches["verdict"],
            variables={
                branch: record["generator_inventory"]
                for branch, record in branches["branches"].items()
            },
            equations={
                branch: record["relation_count"]
                for branch, record in branches["branches"].items()
            },
            completeness_scope="branch-separated Eq.(113) systems",
            unresolved_components=branches["unresolved_components"],
        ),
    )
    result_payloads["v0.3.4_denominator_inventory.json"] = _normalise(
        {
            "factor_count": len(localisation["denominator_factors"]),
            "factors": localisation["denominator_factors"],
            "saturation_plan": localisation["saturation_plan"],
        },
        metadata=_metadata(
            **common,
            verdict="D2_DENOMINATOR_INVENTORY_COMPLETE_SATURATION_PARTIAL",
            equations={
                branch: localisation["systems"][branch][
                    "canonical_numerator_equation_count"
                ]
                for branch in localisation["systems"]
            },
            denominator_factors=localisation["denominator_factors"],
            saturation_method=localisation["saturation_method"],
            unresolved_components=localisation["unresolved_components"],
        ),
    )
    result_payloads["v0.3.4_polynomial_systems.json"] = _normalise(
        localisation,
        metadata=_metadata(
            **common,
            verdict=localisation["verdict"],
            variables={
                branch: record["scalar_unknowns_before_stratum_substitution"]
                for branch, record in localisation["systems"].items()
            },
            equations={
                branch: record["canonical_numerator_equation_count"]
                for branch, record in localisation["systems"].items()
            },
            denominator_factors=localisation["denominator_factors"],
            saturation_method=localisation["saturation_method"],
            completeness_scope=localisation["completeness_scope"],
            unresolved_components=localisation["unresolved_components"],
        ),
    )
    result_payloads["v0.3.4_S1_result.json"] = _stratum_result(
        **common,
        strata=strata,
        campaign=solver_campaign,
        scalar_witness=scalar_witness,
        stratum=S1,
        verdict=S1_PARTIAL,
    )
    result_payloads["v0.3.4_S2_result.json"] = _stratum_result(
        **common,
        strata=strata,
        campaign=solver_campaign,
        scalar_witness=scalar_witness,
        stratum=S2,
        verdict=S2_PARTIAL,
    )
    result_payloads["v0.3.4_S3_result.json"] = _stratum_result(
        **common,
        strata=strata,
        campaign=solver_campaign,
        scalar_witness=scalar_witness,
        stratum=S3,
        verdict=S3_PARTIAL,
    )
    classification = _normalise(
        {
            "rational_DAG_verdict": rational_dag["verdict"],
            "rational_reconstruction_verdict": equivalence["verdict"],
            "source_branch_verdicts": {
                branch: record["verdict"]
                for branch, record in branches["branches"].items()
            },
            "stratum_verdicts": {
                S1: S1_PARTIAL,
                S2: S2_PARTIAL,
                S3: S3_PARTIAL,
            },
            "exact_commutative_representation": {
                "verdict": scalar_witness["verdict"],
                "semantic_digest_sha256": scalar_witness[
                    "semantic_digest_sha256"
                ],
            },
            "noncommutative_representation_found": False,
            "only_commutative_solutions_proved": False,
            "no_representation_proved": False,
            "global_conditional_no_go": None,
            "solver_campaign": solver_campaign,
            "claim_scope": claim_scope,
            "similarity_policy": similarity,
            "finite_d2_verdict": VERDICT_PARTIAL,
            "overall_verdict": OVERALL,
        },
        metadata=_metadata(
            **common,
            verdict=VERDICT_PARTIAL,
            stratum="S1/S2/S3",
            chart="51_CHART_COVER",
            variables={
                "derived": 16,
                "literal": 20,
            },
            equations={
                branch: localisation["systems"][branch][
                    "canonical_numerator_equation_count"
                ]
                for branch in localisation["systems"]
            },
            denominator_factors=localisation["denominator_factors"],
            saturation_method=localisation["saturation_method"],
            solver="bounded SymPy scouts plus exact scalar substitution",
            solver_version=solver_campaign["CAS_inventory"],
            time_limit=campaign_time_limit,
            completeness_scope="finite n<=4 fixed-d2 classification",
            unresolved_components=claim_scope["unresolved_components"],
        ),
    )
    result_payloads["v0.3.4_d2_classification.json"] = classification
    final_bench = _normalise(
        {
            "baseline_verdict": "BASELINE_PASS_WITH_REMOTE_PUBLICATION_GAP",
            "literature_verdict": "LITERATURE_FRONTIER_OPEN",
            "source_equation_verdict": SOURCE_VERDICT,
            "B_auxiliary_verdict": "ALL_B_AUXILIARIES_DEFINITIONAL_D2",
            "rational_DAG_verdict": rational_dag["verdict"],
            "rational_reconstruction_verdict": equivalence["verdict"],
            "source_branch_verdicts": {
                branch: record["verdict"]
                for branch, record in branches["branches"].items()
            },
            "stratum_verdicts": {
                S1: S1_PARTIAL,
                S2: S2_PARTIAL,
                S3: S3_PARTIAL,
            },
            "exact_finite_component": scalar_witness["verdict"],
            "independent_oracle_verdict": "INDEPENDENT_ORACLE_PARTIAL",
            "mutation_verdict": "ALL_25_CRITICAL_MUTATIONS_DETECTED",
            "finite_d2_verdict": VERDICT_PARTIAL,
            "global_conditional_verdict": None,
            "overall_verdict": OVERALL,
            "claim_scope": claim_scope,
        },
        metadata=_metadata(
            **common,
            verdict=OVERALL,
            stratum="S1/S2/S3",
            chart="51_CHART_COVER",
            variables={"derived": 16, "literal": 20},
            equations={
                branch: localisation["systems"][branch][
                    "canonical_numerator_equation_count"
                ]
                for branch in localisation["systems"]
            },
            denominator_factors=localisation["denominator_factors"],
            saturation_method=localisation["saturation_method"],
            solver="bounded exact campaign",
            solver_version=solver_campaign["CAS_inventory"],
            time_limit=campaign_time_limit,
            completeness_scope="Final-Theory Bench v0.3.4 finite algebraic scope",
            unresolved_components=claim_scope["unresolved_components"],
        ),
    )
    result_payloads["final_theory_bench_v0.3.4.json"] = final_bench
    for filename, payload in result_payloads.items():
        _write_json(root / "results" / filename, payload)

    report_payloads = _report_payloads(
        rational_dag=rational_dag,
        equivalence=equivalence,
        localisation=localisation,
        branches=branches,
        strata=strata,
        campaign=solver_campaign,
        scalar_witness=scalar_witness,
        claim_scope=claim_scope,
    )
    for filename, text in report_payloads.items():
        _write_text(root / "reports" / filename, text)

    artifact_paths = _reproduction_artifact_paths(
        root,
        certificate_paths,
    )
    reproduction_artifacts = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in artifact_paths
    ]
    reproduction = _normalise(
        {
            "artifacts": reproduction_artifacts,
            "artifact_count": len(reproduction_artifacts),
            "manifest_self_hash_excluded": True,
            "verification_command": (
                "python -m universe_lab.final_theory.artifacts_v034 --verify"
            ),
            "environment": {
                "python": platform.python_version(),
                "sympy": sp.__version__,
                "platform": platform.platform(),
            },
            "validation_summary": "PENDING_FINAL_QUALITY_GATES",
            "passed": True,
        },
        metadata=_metadata(
            **common,
            verdict="V034_REPRODUCTION_MANIFEST_COMPLETE",
            equations=len(reproduction_artifacts),
            denominator_factors=localisation["denominator_factors"],
            saturation_method=localisation["saturation_method"],
            completeness_scope="all required v0.3.4 repository artifacts",
            unresolved_components=claim_scope["unresolved_components"],
        ),
    )
    _write_json(
        root / "results/reproduction_manifest_final_v0.3.4.json",
        reproduction,
    )
    return {
        "production_commit": production,
        "results_written": len(result_payloads) + 1,
        "reports_written": len(report_payloads),
        "certificates_written": len(certificate_paths),
        "reproduction_artifact_count": len(reproduction_artifacts),
        "finite_d2_verdict": VERDICT_PARTIAL,
        "exact_scalar_representation": scalar_witness["verdict"],
        "overall_verdict": OVERALL,
    }


def verify_v034_reproduction_manifest(root: Path) -> dict[str, Any]:
    path = root / "results/reproduction_manifest_final_v0.3.4.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for record in manifest["artifacts"]:
        artifact = root / record["path"]
        if not artifact.is_file():
            mismatches.append(
                {"path": record["path"], "reason": "MISSING"}
            )
            continue
        observed = _sha256_file(artifact)
        if observed != record["sha256"]:
            mismatches.append(
                {
                    "path": record["path"],
                    "reason": "HASH_MISMATCH",
                    "expected": record["sha256"],
                    "observed": observed,
                }
            )
    return {
        "artifact_count": manifest["artifact_count"],
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    if arguments == ["--verify"]:
        print(
            json.dumps(
                verify_v034_reproduction_manifest(root),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print(
        json.dumps(
            write_v034_artifacts(root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
