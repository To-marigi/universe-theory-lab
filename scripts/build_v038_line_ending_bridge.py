"""Build or check the v0.3.8 legacy-CRLF compatibility bridge."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from universe_lab.artifact_migration_v038 import (
    BINDING_KIND,
    EXPECTED_BINDING_COUNT,
    EXPECTED_CONSUMER_COUNT,
    EXPECTED_TARGET_COUNT,
    LIVING_DOCUMENT_TARGET_EXCLUSIONS,
    LedgerValidationError,
    TextArtifactError,
    canonical_lf_bytes,
    escape_json_pointer_token,
    is_non_raw_digest_pointer,
    is_v038_owned_path,
    line_ending_hashes,
    sha256_bytes,
    validate_ledger_structure,
    verify_line_ending_bridge,
    virtual_crlf_bytes,
)

RESULT_PATH = "results/v0.3.8_line_ending_bridge.json"
_SHA256_VALUE_RE = re.compile(r"(?:(sha256):)?([0-9a-f]{64})")

# references/manifest.json is a living ledger.  Keep its v0.3.8 target and
# binding as explicit historical data, but never rediscover them from the
# current growing file.  This preserves byte-for-byte regeneration of the
# frozen bridge without treating the current manifest as immutable.
_LIVING_DOCUMENT_LEGACY_TARGET = {
    "current_raw_sha256": "80758632bdf49cb3dbf2988f7b630ded0768834db9d6da539be99fbd8b8becfb",
    "current_raw_size_bytes": 69627,
    "canonical_lf_sha256": "80758632bdf49cb3dbf2988f7b630ded0768834db9d6da539be99fbd8b8becfb",
    "canonical_lf_size_bytes": 69627,
    "virtual_crlf_sha256": "2d28c78da992c6f6e86c6572b762a01b90758b9f7dcc89665b08124101cfd028",
    "virtual_crlf_size_bytes": 71062,
    "lf_count": 1435,
}
_LIVING_DOCUMENT_LEGACY_BINDING = {
    "consumer_path": "results/v0.3.7_release_manifest.json",
    "json_pointer": "/files/85/sha256",
    "recorded_value": "2d28c78da992c6f6e86c6572b762a01b90758b9f7dcc89665b08124101cfd028",
    "legacy_raw_sha256": "2d28c78da992c6f6e86c6572b762a01b90758b9f7dcc89665b08124101cfd028",
    "sha256_prefix_present": False,
    "target_paths": ["references/manifest.json"],
    "binding_kind": BINDING_KIND,
}


def _tracked_paths(root: Path) -> list[str]:
    process = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    paths = [
        raw_path.decode("utf-8", errors="strict")
        for raw_path in process.stdout.split(b"\0")
        if raw_path
    ]
    return sorted(path for path in paths if not is_v038_owned_path(path))


def _canonical_text_inventory(root: Path, paths: list[str]) -> dict[str, bytes]:
    inventory: dict[str, bytes] = {}
    for relative_path in paths:
        path = root / relative_path
        if not path.is_file():
            continue
        raw = path.read_bytes()
        try:
            canonical = canonical_lf_bytes(raw, source=relative_path)
        except (UnicodeDecodeError, TextArtifactError):
            continue
        inventory[relative_path] = canonical
    return inventory


def _walk_json(value: Any, pointer: str = "") -> Iterator[tuple[str, Any]]:
    yield pointer, value
    if isinstance(value, dict):
        for key in sorted(value):
            token = escape_json_pointer_token(key)
            yield from _walk_json(value[key], f"{pointer}/{token}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_json(item, f"{pointer}/{index}")


def build_ledger(root: Path) -> dict[str, Any]:
    """Scan tracked pre-v0.3.8 files and build the deterministic bridge."""

    root = root.resolve()
    tracked_paths = _tracked_paths(root)
    text_inventory = _canonical_text_inventory(root, tracked_paths)

    canonical_digest_set = {
        sha256_bytes(canonical) for canonical in text_inventory.values()
    }
    virtual_digest_to_paths: dict[str, list[str]] = defaultdict(list)
    for relative_path, canonical in text_inventory.items():
        if relative_path in LIVING_DOCUMENT_TARGET_EXCLUSIONS:
            continue
        if b"\n" not in canonical:
            continue
        virtual = virtual_crlf_bytes(canonical, source=relative_path)
        virtual_digest_to_paths[sha256_bytes(virtual)].append(relative_path)
    for paths in virtual_digest_to_paths.values():
        paths.sort()

    bindings: list[dict[str, Any]] = []
    forbidden_matches: list[tuple[str, str]] = []
    for consumer_path in tracked_paths:
        if not consumer_path.lower().endswith(".json"):
            continue
        canonical = text_inventory.get(consumer_path)
        if canonical is None:
            continue
        try:
            document = json.loads(canonical.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        for pointer, value in _walk_json(document):
            if not isinstance(value, str):
                continue
            match = _SHA256_VALUE_RE.fullmatch(value)
            if match is None:
                continue
            legacy_digest = match.group(2)
            candidates = virtual_digest_to_paths.get(legacy_digest)
            if not candidates or legacy_digest in canonical_digest_set:
                continue
            if is_non_raw_digest_pointer(pointer):
                forbidden_matches.append((consumer_path, pointer))
                continue
            bindings.append(
                {
                    "consumer_path": consumer_path,
                    "json_pointer": pointer,
                    "recorded_value": value,
                    "legacy_raw_sha256": legacy_digest,
                    "sha256_prefix_present": match.group(1) is not None,
                    "target_paths": candidates,
                    "binding_kind": BINDING_KIND,
                }
            )
    if forbidden_matches:
        raise LedgerValidationError(
            "raw-byte candidate(s) occurred in semantic/request fields and require review: "
            f"{forbidden_matches}"
        )
    bindings.append(dict(_LIVING_DOCUMENT_LEGACY_BINDING))
    bindings.sort(
        key=lambda binding: (
            binding["consumer_path"],
            binding["json_pointer"],
            binding["legacy_raw_sha256"],
        )
    )

    target_edge_counts: Counter[str] = Counter(
        target_path
        for binding in bindings
        for target_path in binding["target_paths"]
    )
    targets: list[dict[str, Any]] = []
    for target_path in sorted(target_edge_counts):
        if target_path in LIVING_DOCUMENT_TARGET_EXCLUSIONS:
            hashes = dict(_LIVING_DOCUMENT_LEGACY_TARGET)
        else:
            hashes = line_ending_hashes(root / target_path, require_canonical_lf=True)
        targets.append(
            {
                "path": target_path,
                **hashes,
                "legacy_binding_count": target_edge_counts[target_path],
            }
        )

    consumer_count = len({binding["consumer_path"] for binding in bindings})
    counts = {
        "legacy_raw_bindings": len(bindings),
        "unique_consumers": consumer_count,
        "unique_targets": len(targets),
        "target_candidate_edges": sum(target_edge_counts.values()),
        "ambiguous_bindings": sum(
            len(binding["target_paths"]) > 1 for binding in bindings
        ),
    }
    expected = (
        EXPECTED_BINDING_COUNT,
        EXPECTED_CONSUMER_COUNT,
        EXPECTED_TARGET_COUNT,
    )
    observed = (
        counts["legacy_raw_bindings"],
        counts["unique_consumers"],
        counts["unique_targets"],
    )
    if observed != expected:
        raise LedgerValidationError(
            "legacy bridge scope changed; "
            f"expected bindings/consumers/targets={expected}, observed={observed}"
        )

    payload: dict[str, Any] = {
        "schema_version": "universe-line-ending-bridge-v0.3.8",
        "version": "0.3.8",
        "status": "COMPATIBILITY_BRIDGE_FOR_IMMUTABLE_LEGACY_ARTIFACTS",
        "scope": {
            "historical_versions": "v0.2--v0.3.7",
            "consumer_selection_rule": (
                "A JSON string is included only when its bare lower-case SHA-256 value "
                "equals a tracked text file's virtual-CRLF raw-byte digest and equals "
                "no tracked text file's canonical-LF raw-byte digest."
            ),
            "canonical_text_rule": (
                "Strict UTF-8; CRLF canonicalizes to LF; NUL and lone CR are rejected."
            ),
            "non_raw_digest_rule": (
                "Semantic, request, expression, polynomial, and budget digest fields "
                "are not raw-file bindings."
            ),
            "self_exclusion_rule": (
                "Paths owned by v0.3.8 (v0.3.8, v038, or v0_3_8 in the path) "
                "are excluded from both sides of the scan."
            ),
            "historical_mutation": "NONE",
        },
        "counts": counts,
        "targets": targets,
        "bindings": bindings,
    }
    validate_ledger_structure(payload)
    verify_line_ending_bridge(root, payload)
    return payload


def render_ledger(payload: dict[str, Any]) -> bytes:
    """Serialize the ledger deterministically as canonical LF UTF-8 JSON."""

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
        help="fail unless the committed ledger exactly matches regeneration",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = args.root.resolve()
    output = Path(args.output)
    output_path = output if output.is_absolute() else root / output
    payload = build_ledger(root)
    expected_bytes = render_ledger(payload)

    if args.check:
        if not output_path.is_file():
            print(f"missing bridge ledger: {output_path}", file=sys.stderr)
            return 1
        actual_bytes = output_path.read_bytes()
        if actual_bytes != expected_bytes:
            print(
                f"bridge ledger differs from deterministic regeneration: {output_path}",
                file=sys.stderr,
            )
            return 1
        print(
            "v0.3.8 line-ending bridge check passed: "
            f"{payload['counts']['legacy_raw_bindings']} bindings, "
            f"{payload['counts']['unique_consumers']} consumers, "
            f"{payload['counts']['unique_targets']} targets"
        )
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(expected_bytes.decode("utf-8"))
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
