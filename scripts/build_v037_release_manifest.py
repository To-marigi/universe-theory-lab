"""Build the hash inventory for the local v0.3.7 release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from universe_lab.final_theory.q5_free_elimination_v037 import (
    SCOUT_MODULI,
    VERDICT_PROVED,
    load_human_budget_v037,
    verify_q5_free_campaign_v037,
)
from universe_lab.final_theory.scalar_chain_v037 import (
    DERIVED_BRANCH,
    LEMMA,
    LITERAL_BRANCH,
    verify_general_scalar_chain_lemma_v037,
)

RESULT_PATH = "results/v0.3.7_release_manifest.json"

STATIC_PATHS = [
    ".zenodo.json",
    "CITATION.cff",
    "LICENSE",
    "CONTRIBUTING.md",
    ".github/workflows/ci.yml",
    ".gitattributes",
    "README.md",
    "REPRODUCING_v0.3.7.md",
    ".python-version",
    "compose.yaml",
    "pyproject.toml",
    "uv.lock",
    "config/v0.3.7_budget.json",
    "results/v0.3.2_cpobc_d2_classification.json",
    "results/v0.3.3_q_only_presentation_n4.json",
    "results/v0.3.4_polynomial_systems.json",
    "results/v0.3.5_stage3_subset_campaign.json",
    "results/v0.3.5_full_stage4_campaign.json",
    "results/v0.3.5_d2_classification.json",
    "results/v0.3.6_q5_constraint_census.json",
    "results/v0.3.6_q5_vacuity_proof.json",
    "results/v0.3.7_q5_free_partition.json",
    "results/v0.3.7_q5_free_elimination.json",
    "results/v0.3.7_scope_addendum.json",
    "results/v0.3.7_general_scalar_chain_fiber.json",
    "results/v0.3.7_publication_readiness.json",
    "certificates/d2_saturation/v0.3.5_direct_operator_system.json",
    "certificates/d2_saturation/v0.3.5_compact_expression_arena.json.gz",
    "certificates/d2_saturation/q5_free_v037/preflight_compact_arena_timeout.json",
    "reports/v0.3.7_scope_addendum.md",
    "reports/v0.3.7_literature_frontier.md",
    "reports/v0.3.7_publication_readiness.md",
    "references/sources.json",
    "references/manifest.json",
    "references/notes/final_theory_v0.3.7_literature_frontier_2026-07-30.md",
    "references/notes/v0.3.7_publication_metadata_requirements_2026-07-30.md",
    "paper/paper.md",
    "paper/paper.bib",
    "paper/v0.3.7_d2_commutativity/main.tex",
    "paper/v0.3.7_d2_commutativity/references.bib",
    "output/pdf/v0.3.7_d2_commutativity_short_report.pdf",
    "scripts/reproduce_v037.py",
    "scripts/build_v037_release_manifest.py",
    "scripts/sage.ps1",
    "src/universe_lab/__init__.py",
    "tests/final_theory/test_d2_saturation_v035.py",
    "tests/final_theory/test_q5_free_elimination_v037.py",
    "tests/final_theory/test_scalar_chain_v037.py",
    "tests/final_theory/test_reproduce_v037.py",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _semantic_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _code_paths(root: Path) -> list[str]:
    package = root / "src/universe_lab/final_theory"
    return sorted(path.relative_to(root).as_posix() for path in package.glob("*.py"))


def _certificate_inventory(
    root: Path,
) -> tuple[dict[str, list[str]], dict[str, Any], dict[str, Any]]:
    phase1_verification = verify_q5_free_campaign_v037(root)
    phase2_verification = verify_general_scalar_chain_lemma_v037(root)
    if not phase1_verification["passed"] or phase1_verification["verdict"] != VERDICT_PROVED:
        raise RuntimeError("strict Phase 1 verification did not pass")
    if not phase2_verification["passed"] or phase2_verification["verdict"] != LEMMA:
        raise RuntimeError("strict Phase 2 verification did not pass")

    phase1 = _load_json(root / "results/v0.3.7_q5_free_elimination.json")
    scalar = _load_json(root / "results/v0.3.7_general_scalar_chain_fiber.json")
    phase1_runs = phase1.get("runs", [])
    field_counts = Counter(record.get("coefficient_field") for record in phase1_runs)
    expected_field_counts = Counter(
        {
            "QQ": 21,
            f"GF({SCOUT_MODULI[0]})": 21,
            f"GF({SCOUT_MODULI[1]})": 21,
        }
    )
    if len(phase1_runs) != 63 or field_counts != expected_field_counts:
        raise RuntimeError("expected Phase 1 certificate roles QQ=21 and two GF=21")
    if set(scalar.get("exact_runs", {})) != {
        LITERAL_BRANCH,
        DERIVED_BRANCH,
    }:
        raise RuntimeError("expected exactly two Phase 2 branches")

    roles = {
        "PHASE1_QQ_EXACT_PROOF": [
            record["certificate"] for record in phase1_runs if record["coefficient_field"] == "QQ"
        ],
        f"PHASE1_GF{SCOUT_MODULI[0]}_SCOUT": [
            record["certificate"]
            for record in phase1_runs
            if record["coefficient_field"] == f"GF({SCOUT_MODULI[0]})"
        ],
        f"PHASE1_GF{SCOUT_MODULI[1]}_SCOUT": [
            record["certificate"]
            for record in phase1_runs
            if record["coefficient_field"] == f"GF({SCOUT_MODULI[1]})"
        ],
        "PHASE2_QQ_DIRECT_IDENTITY_EXACT": [
            scalar["exact_runs"][branch]["direct_relation_evaluation"]["path"]
            for branch in (LITERAL_BRANCH, DERIVED_BRANCH)
        ],
        "NEGATIVE_TIMEOUT_RECORD_NOT_PROOF": [
            ("certificates/d2_saturation/q5_free_v037/preflight_compact_arena_timeout.json")
        ],
    }
    proof_paths = [
        path
        for role, paths in roles.items()
        if role != "NEGATIVE_TIMEOUT_RECORD_NOT_PROOF"
        for path in paths
    ]
    if len(proof_paths) != 65 or len(set(proof_paths)) != 65:
        raise RuntimeError("expected exactly 63 Phase 1 and 2 Phase 2 certificates")
    return roles, phase1_verification, phase2_verification


def build_manifest(root: Path) -> dict[str, Any]:
    budget = load_human_budget_v037(root)
    roles, phase1_verification, phase2_verification = _certificate_inventory(root)
    readiness = _load_json(root / "results/v0.3.7_publication_readiness.json")
    if readiness.get("status") != "BLOCKED":
        raise RuntimeError("publication readiness must retain the current BLOCKED status")
    certificate_paths = [path for paths in roles.values() for path in paths]
    paths = sorted(set(STATIC_PATHS + _code_paths(root) + certificate_paths))
    missing = [path for path in paths if not (root / path).is_file()]
    if missing:
        raise FileNotFoundError(f"release files are missing: {missing}")
    role_by_path = {path: role for role, role_paths in roles.items() for path in role_paths}
    files: list[dict[str, Any]] = [
        {
            "path": path,
            "sha256": _sha256(root / path),
            "size_bytes": (root / path).stat().st_size,
            "role": role_by_path.get(
                path,
                "RELEASE_SUPPORT_SOURCE_OR_FROZEN_INPUT",
            ),
        }
        for path in paths
    ]
    total_size = sum(int(record["size_bytes"]) for record in files)
    role_inventory = {
        role: {
            "count": len(role_paths),
            "paths_sha256": _semantic_digest(sorted(role_paths)),
        }
        for role, role_paths in sorted(roles.items())
    }
    payload: dict[str, Any] = {
        "schema_version": "final-theory-release-manifest-v0.3.7",
        "version": "0.3.7",
        "status": "LOCAL_RELEASE_CANDIDATE_NOT_EXTERNALLY_DEPOSITED",
        "scientific_verdicts": {
            "phase1": phase1_verification["verdict"],
            "phase2": phase2_verification["verdict"],
            "global": phase1_verification["global_scientific_verdict"],
        },
        "publication_readiness": readiness["status"],
        "inventory_scope": (
            "The v0.3.7 proof certificates, frozen inputs, full "
            "universe_lab.final_theory Python package, tests, paper, "
            "metadata, and documented Sage launcher; not a full-repository "
            "source archive."
        ),
        "budget": {
            "path": budget["path"],
            "sha256": budget["sha256"],
            "provenance": budget["provenance"],
        },
        "certificate_inventory": role_inventory,
        "file_count": len(files),
        "total_size_bytes": total_size,
        "files": files,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(
        {
            "version": payload["version"],
            "status": payload["status"],
            "scientific_verdicts": payload["scientific_verdicts"],
            "publication_readiness": payload["publication_readiness"],
            "inventory_scope": payload["inventory_scope"],
            "budget": payload["budget"],
            "certificate_inventory": payload["certificate_inventory"],
            "files": files,
        }
    )
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    payload = build_manifest(root)
    output = root / RESULT_PATH
    if arguments.check:
        if not output.is_file():
            raise SystemExit(f"release manifest is missing: {output}")
        saved = _load_json(output)
        if saved != payload:
            raise SystemExit("release manifest is stale or invalid")
        print(
            f"{output}: verified {payload['file_count']} files, {payload['semantic_digest_sha256']}"
        )
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{output}: {payload['file_count']} files, {payload['semantic_digest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
