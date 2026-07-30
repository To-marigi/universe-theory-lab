"""Build the canonical-LF v0.3.8 release manifest."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

from universe_lab.artifact_migration_v038 import (
    TextArtifactError,
    load_line_ending_bridge,
    raw_sha256,
    strict_lf_bytes,
)

RESULT_PATH = "results/v0.3.8_release_manifest.json"
V037_MANIFEST_PATH = "results/v0.3.7_release_manifest.json"
BRIDGE_PATH = "results/v0.3.8_line_ending_bridge.json"

EXPECTED_HISTORICAL_CLASS_COUNTS = {
    "UNCHANGED_RAW_BYTES": 52,
    "CANONICAL_LF_WITH_LEGACY_CRLF_BRIDGE": 81,
    "V038_INTENTIONAL_SUPPORT_OR_WRITER_UPDATE": 26,
}

V038_SUPPORT_WRITER_PATHS = (
    ".gitattributes",
    ".github/workflows/ci.yml",
    ".gitignore",
    ".zenodo.json",
    "CITATION.cff",
    "README.md",
    "oracle/cpobc_gc_atomisation_v033_oracle.py",
    "oracle/d2_rational_v034_oracle.py",
    "oracle/d2_saturation_v035_witness.py",
    "oracle/sage_periods/run_period_oracle.sage",
    "scripts/archive_references.py",
    "scripts/build_stringbench_v0_3_artifacts.py",
    "scripts/build_v037_release_manifest.py",
    "paper/paper.md",
    "src/universe_lab/cli.py",
    "src/universe_lab/final_theory/artifacts_v034.py",
    "src/universe_lab/final_theory/cli.py",
    "src/universe_lab/final_theory/cpobc_d2_v032.py",
    "src/universe_lab/final_theory/cpobc_q_presentation_v033.py",
    "src/universe_lab/final_theory/cpobc_v031.py",
    "src/universe_lab/final_theory/d2_auxiliary_audit_v034.py",
    "src/universe_lab/final_theory/d2_sage_backend_v035.py",
    "src/universe_lab/final_theory/d2_saturation_v035.py",
    "src/universe_lab/final_theory/q5_closure_v036.py",
    "src/universe_lab/final_theory/q5_free_elimination_v037.py",
    "src/universe_lab/final_theory/q5_vacuity_v036.py",
    "src/universe_lab/final_theory/scalar_chain_v037.py",
    "src/universe_lab/final_theory/scope_addendum_v037.py",
    "src/universe_lab/final_theory/v02.py",
    "src/universe_lab/final_theory/v03.py",
    "src/universe_lab/final_theory/v031.py",
    "src/universe_lab/qgaudit/audit.py",
    "src/universe_lab/qgbench/benchmarks.py",
    "src/universe_lab/stringbench/cli.py",
    "tests/final_theory/test_audit_v03.py",
    "tests/final_theory/test_audit_v031.py",
    "tests/final_theory/test_cpobc_d2_v032.py",
    "tests/final_theory/test_cpobc_v031.py",
    "tests/final_theory/test_d2_auxiliary_audit_v034.py",
    "tests/final_theory/test_d2_rational_v034_oracle.py",
    "tests/final_theory/test_q5_free_elimination_v037.py",
    "tests/final_theory/test_q5_vacuity_v036.py",
    "tests/final_theory/test_reproduce_v037.py",
    "tests/final_theory/test_scalar_chain_v037.py",
    "tests/final_theory/test_v02.py",
    "tests/final_theory/test_v03.py",
    "tests/final_theory/test_v031.py",
)

V038_MIGRATION_PATHS = (
    BRIDGE_PATH,
    V037_MANIFEST_PATH,
    "REPRODUCING_v0.3.8.md",
    "reports/v0.3.8_line_ending_migration.md",
    "reports/v0.3.8_publication_readiness.md",
    "results/v0.3.8_publication_readiness.json",
    "scripts/build_v038_line_ending_bridge.py",
    "scripts/build_v038_release_manifest.py",
    "scripts/reproduce_v038.py",
    "src/universe_lab/artifact_migration_v038.py",
    "tests/final_theory/test_line_ending_bridge_v038.py",
    "tests/final_theory/test_reproduce_v038.py",
    "tests/test_line_endings.py",
)

_BINARY_SUFFIXES = {".gz", ".pdf", ".whl"}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return payload


def _stable_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_script_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _historical_manifest_audit(
    root: Path,
    bridge: dict[str, Any],
) -> dict[str, Any]:
    legacy = _load_json(root / V037_MANIFEST_PATH)
    if legacy.get("schema_version") != "final-theory-release-manifest-v0.3.7":
        raise RuntimeError("unexpected v0.3.7 release manifest schema")
    if legacy.get("file_count") != len(legacy.get("files", [])):
        raise RuntimeError("v0.3.7 release manifest file count is inconsistent")

    target_by_path = {target["path"]: target for target in bridge["targets"]}
    intentional = set(V038_SUPPORT_WRITER_PATHS)
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    unexpected: list[str] = []
    historical_intentional_paths: set[str] = set()
    for record in legacy["files"]:
        relative_path = record["path"]
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"historical release file is missing: {relative_path}")
        current_digest = raw_sha256(path)
        recorded_digest = record["sha256"]
        target = target_by_path.get(relative_path)
        if current_digest == recorded_digest:
            classification = "UNCHANGED_RAW_BYTES"
        elif target is not None and target["virtual_crlf_sha256"] == recorded_digest:
            classification = "CANONICAL_LF_WITH_LEGACY_CRLF_BRIDGE"
        elif relative_path in intentional:
            classification = "V038_INTENTIONAL_SUPPORT_OR_WRITER_UPDATE"
            historical_intentional_paths.add(relative_path)
        else:
            classification = "UNEXPECTED_CHANGE"
            unexpected.append(relative_path)
        counts[classification] += 1
        records.append(
            {
                "path": relative_path,
                "v0.3.7_recorded_sha256": recorded_digest,
                "v0.3.8_current_raw_sha256": current_digest,
                "classification": classification,
            }
        )

    if unexpected:
        raise RuntimeError(f"unexpected changes relative to v0.3.7 manifest: {unexpected}")
    observed_counts = dict(sorted(counts.items()))
    if observed_counts != EXPECTED_HISTORICAL_CLASS_COUNTS:
        raise RuntimeError(
            "historical manifest classification changed: "
            f"expected {EXPECTED_HISTORICAL_CLASS_COUNTS}, got {observed_counts}"
        )
    expected_intentional = {
        record["path"]
        for record in legacy["files"]
        if record["path"] in intentional
        and record["path"] not in target_by_path
        and raw_sha256(root / record["path"]) != record["sha256"]
    }
    if historical_intentional_paths != expected_intentional:
        raise RuntimeError("historical intentional-support classification is inconsistent")
    return {
        "artifact": V037_MANIFEST_PATH,
        "historical_semantic_digest_sha256": legacy["semantic_digest_sha256"],
        "historical_file_count": legacy["file_count"],
        "classification_counts": observed_counts,
        "unexpected_changes": [],
        "records": records,
        "passed": True,
    }


def _serialization(path: Path, relative_path: str) -> str:
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return "BINARY_RAW_BYTES"
    data = path.read_bytes()
    try:
        strict_lf_bytes(data, source=relative_path)
    except UnicodeDecodeError as error:
        raise RuntimeError(
            f"non-UTF-8 release file lacks an explicit binary suffix: {relative_path}"
        ) from error
    except TextArtifactError as error:
        raise RuntimeError(
            f"release text file is not canonical LF: {relative_path}"
        ) from error
    return "CANONICAL_LF_UTF8"


def _role_for_path(
    path: str,
    legacy_roles: dict[str, str],
) -> str:
    explicit = {
        BRIDGE_PATH: "V038_LINE_ENDING_BRIDGE",
        V037_MANIFEST_PATH: "V037_HISTORICAL_MANIFEST",
        "REPRODUCING_v0.3.8.md": "V038_REPRODUCTION_GUIDE",
        "reports/v0.3.8_line_ending_migration.md": "V038_MIGRATION_REPORT",
        "reports/v0.3.8_publication_readiness.md": "V038_PUBLICATION_READINESS",
        "results/v0.3.8_publication_readiness.json": "V038_PUBLICATION_READINESS",
        "scripts/build_v038_line_ending_bridge.py": "V038_MIGRATION_TOOL",
        "scripts/build_v038_release_manifest.py": "V038_RELEASE_TOOL",
        "scripts/reproduce_v038.py": "V038_REPRODUCTION_TOOL",
        "src/universe_lab/artifact_migration_v038.py": "V038_MIGRATION_SOURCE",
        "tests/final_theory/test_line_ending_bridge_v038.py": "V038_MIGRATION_TEST",
        "tests/final_theory/test_reproduce_v038.py": "V038_REPRODUCTION_TEST",
        "tests/test_line_endings.py": "V038_LINE_ENDING_REGRESSION_TEST",
    }
    if path in explicit:
        return explicit[path]
    if path in V038_SUPPORT_WRITER_PATHS:
        return "V038_CANONICAL_LF_WRITER_OR_SUPPORT"
    return legacy_roles.get(path, "V037_RELEASE_CARRY_FORWARD")


def _verify_migration_and_science(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    reproducer = _load_script_module(
        "reproduce_v038_for_release_manifest",
        root / "scripts/reproduce_v038.py",
    )
    bridge_summary, resolver = reproducer.verify_bridge(root)
    science = reproducer.verify_scientific_artifacts(root, resolver)
    if not bridge_summary["passed"]:
        raise RuntimeError("strict line-ending bridge verification did not pass")
    if not science["passed"]:
        raise RuntimeError("bridge-aware v0.3.7 scientific verification did not pass")
    return bridge_summary, science


def build_manifest(root: Path) -> dict[str, Any]:
    """Build the deterministic canonical-LF release inventory."""

    root = root.resolve()
    bridge_summary, science = _verify_migration_and_science(root)
    bridge = load_line_ending_bridge(root / BRIDGE_PATH)
    historical_audit = _historical_manifest_audit(root, bridge)
    legacy = _load_json(root / V037_MANIFEST_PATH)
    legacy_roles = {record["path"]: record["role"] for record in legacy["files"]}

    paths = sorted(
        {
            *(record["path"] for record in legacy["files"]),
            *V038_SUPPORT_WRITER_PATHS,
            *V038_MIGRATION_PATHS,
        }
    )
    if RESULT_PATH in paths:
        raise RuntimeError("v0.3.8 release manifest must exclude itself")
    missing = [path for path in paths if not (root / path).is_file()]
    if missing:
        raise FileNotFoundError(f"v0.3.8 release files are missing: {missing}")

    files = [
        {
            "path": relative_path,
            "sha256": raw_sha256(root / relative_path),
            "size_bytes": (root / relative_path).stat().st_size,
            "serialization": _serialization(root / relative_path, relative_path),
            "role": _role_for_path(relative_path, legacy_roles),
        }
        for relative_path in paths
    ]
    role_counts = dict(sorted(Counter(record["role"] for record in files).items()))
    payload: dict[str, Any] = {
        "schema_version": "final-theory-release-manifest-v0.3.8",
        "version": "0.3.8",
        "status": "LOCAL_RELEASE_CANDIDATE_NOT_EXTERNALLY_DEPOSITED",
        "publication_readiness": (
            "BLOCKED_PENDING_EXTERNAL_CI_AND_HUMAN_MATURITY_REVIEW"
        ),
        "migration": {
            "kind": "BYTE_SERIALIZATION_ONLY_CRLF_TO_CANONICAL_LF",
            "canonical_serialization": "STRICT_UTF8_WITH_LF",
            "legacy_hash_resolution": {
                "ledger_targets": "VIRTUAL_CRLF_FOR_LEGACY_LEDGER_TARGET",
                "all_other_paths": "CURRENT_RAW_BYTES",
            },
            "bridge": {
                "path": BRIDGE_PATH,
                "regenerated_exactly": bridge_summary["regenerated_exactly"],
                "legacy_raw_bindings": bridge_summary["legacy_raw_bindings"],
                "unique_consumers": bridge_summary["unique_consumers"],
                "unique_targets": bridge_summary["unique_targets"],
            },
            "historical_v0.3.7_manifest": historical_audit,
        },
        "scientific_verdicts": science["scientific_verdicts"],
        "scientific_change": "NONE",
        "claim_boundary": (
            "v0.3.8 changes byte serialization and compatibility verification only; "
            "it does not rerun Sage, alter frozen v0.3.7 JSON values, or strengthen "
            "any scientific claim."
        ),
        "certificate_inventory": legacy["certificate_inventory"],
        "file_count": len(files),
        "total_size_bytes": sum(record["size_bytes"] for record in files),
        "role_counts": role_counts,
        "files": files,
    }
    payload["semantic_digest_sha256"] = _stable_digest(payload)
    return payload


def render_manifest(payload: dict[str, Any]) -> bytes:
    """Render deterministic UTF-8 JSON with canonical LF line endings."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--output",
        default=RESULT_PATH,
        help=f"repository-relative output path (default: {RESULT_PATH})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless the saved manifest exactly matches regeneration",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = args.root.resolve()
    output = Path(args.output)
    output_path = output if output.is_absolute() else root / output
    payload = build_manifest(root)
    expected_bytes = render_manifest(payload)
    if args.check:
        if not output_path.is_file():
            print(f"missing release manifest: {output_path}", file=sys.stderr)
            return 1
        if output_path.read_bytes() != expected_bytes:
            print(f"stale or invalid release manifest: {output_path}", file=sys.stderr)
            return 1
        print(
            f"{output_path}: verified {payload['file_count']} files, "
            f"{payload['semantic_digest_sha256']}"
        )
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(expected_bytes)
    print(
        f"{output_path}: {payload['file_count']} files, "
        f"{payload['semantic_digest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
