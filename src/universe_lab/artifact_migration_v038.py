"""Validate the v0.3.8 compatibility bridge for legacy CRLF byte hashes.

The bridge does not rewrite historical artifacts.  It records, and verifies,
that a hash embedded in an immutable v0.2--v0.3.7 JSON artifact is the SHA-256
of a target's virtual CRLF serialization while the checked-out target is the
canonical LF serialization of the same UTF-8 text.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "universe-line-ending-bridge-v0.3.8"
BINDING_KIND = "RAW_FILE_BYTES_LEGACY_CRLF"
EXPECTED_BINDING_COUNT = 1007
EXPECTED_CONSUMER_COUNT = 84
EXPECTED_TARGET_COUNT = 207

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_ARRAY_INDEX_RE = re.compile(r"0|[1-9][0-9]*")
_NON_RAW_POINTER_MARKERS = (
    "semantic_digest",
    "request_digest",
    "request_sha256",
    "expression_digest",
    "polynomial_digest",
    "budget_digest",
)


class TextArtifactError(ValueError):
    """Raised when bytes are not a supported canonicalizable text artifact."""


class LedgerValidationError(ValueError):
    """Raised when a bridge ledger or one of its repository bindings is invalid."""


class LegacyRawDigestResolver:
    """Resolve frozen raw-byte hashes from a canonical-LF checkout.

    Files declared as bridge targets are hashed after virtual LF-to-CRLF
    serialization.  Every other file is hashed exactly as checked out.  The
    distinction is deliberately path based: digest equality alone must not
    silently opt an unrelated file into legacy serialization.
    """

    def __init__(self, root: Path, payload: Any) -> None:
        validate_ledger_structure(payload)
        ledger = _require_mapping(payload, "ledger")
        targets = _require_list(ledger["targets"], "targets")
        self.root = root.resolve()
        self.virtual_crlf_targets = frozenset(
            _require_string(target["path"], "target.path")
            for target in targets
        )

    def repository_path(self, path: Path) -> str | None:
        """Return a normalized repository-relative path, if *path* is inside."""

        candidate = path.resolve()
        try:
            return candidate.relative_to(self.root).as_posix()
        except ValueError:
            return None

    def strategy(self, path: Path) -> str:
        """Return the explicit raw-byte strategy selected for *path*."""

        relative_path = self.repository_path(path)
        if relative_path in self.virtual_crlf_targets:
            return "VIRTUAL_CRLF_FOR_LEGACY_LEDGER_TARGET"
        return "CURRENT_RAW_BYTES"

    def sha256(self, path: Path) -> str:
        """Resolve the digest required by immutable pre-v0.3.8 records."""

        if self.strategy(path) == "VIRTUAL_CRLF_FOR_LEGACY_LEDGER_TARGET":
            return virtual_crlf_sha256(path)
        return raw_sha256(path)


def sha256_bytes(data: bytes) -> str:
    """Return the lower-case SHA-256 hex digest of *data*."""

    return hashlib.sha256(data).hexdigest()


def raw_sha256(path: Path) -> str:
    """Hash the exact bytes stored at *path*."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_lf_bytes(data: bytes, *, source: str = "<bytes>") -> bytes:
    """Decode UTF-8 strictly, normalize CRLF to LF, and reject lone CR/NUL.

    A lone carriage return has no unambiguous line-ending interpretation, so
    it is rejected instead of being silently rewritten.
    """

    text = data.decode("utf-8", errors="strict")
    if "\x00" in text:
        raise TextArtifactError(f"{source} contains NUL and is not a text artifact")
    canonical = text.replace("\r\n", "\n")
    if "\r" in canonical:
        raise TextArtifactError(f"{source} contains a lone carriage return")
    return canonical.encode("utf-8")


def strict_lf_bytes(data: bytes, *, source: str = "<bytes>") -> bytes:
    """Return *data* only when it is already strict UTF-8 with canonical LF."""

    canonical = canonical_lf_bytes(data, source=source)
    if canonical != data:
        raise TextArtifactError(f"{source} is UTF-8 text but is not canonical LF")
    return data


def virtual_crlf_bytes(canonical: bytes, *, source: str = "<bytes>") -> bytes:
    """Create the legacy CRLF byte serialization of canonical LF UTF-8 bytes."""

    strict_lf_bytes(canonical, source=source)
    return canonical.replace(b"\n", b"\r\n")


def canonical_lf_sha256(path: Path) -> str:
    """Hash the canonical LF serialization of a strict UTF-8 text file."""

    data = path.read_bytes()
    return sha256_bytes(canonical_lf_bytes(data, source=str(path)))


def virtual_crlf_sha256(path: Path) -> str:
    """Hash the virtual CRLF serialization of a strict UTF-8 text file."""

    data = path.read_bytes()
    canonical = canonical_lf_bytes(data, source=str(path))
    return sha256_bytes(virtual_crlf_bytes(canonical, source=str(path)))


def line_ending_hashes(path: Path, *, require_canonical_lf: bool = False) -> dict[str, Any]:
    """Return exact, canonical-LF, and virtual-CRLF hashes and byte counts."""

    raw = path.read_bytes()
    canonical = canonical_lf_bytes(raw, source=str(path))
    if require_canonical_lf:
        strict_lf_bytes(raw, source=str(path))
    virtual = virtual_crlf_bytes(canonical, source=str(path))
    return {
        "current_raw_sha256": sha256_bytes(raw),
        "current_raw_size_bytes": len(raw),
        "canonical_lf_sha256": sha256_bytes(canonical),
        "canonical_lf_size_bytes": len(canonical),
        "virtual_crlf_sha256": sha256_bytes(virtual),
        "virtual_crlf_size_bytes": len(virtual),
        "lf_count": canonical.count(b"\n"),
    }


def escape_json_pointer_token(token: str) -> str:
    """Escape one RFC 6901 JSON Pointer token."""

    return token.replace("~", "~0").replace("/", "~1")


def _unescape_json_pointer_token(token: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(token):
        character = token[index]
        if character != "~":
            result.append(character)
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
            raise LedgerValidationError(f"invalid JSON Pointer escape in token {token!r}")
        result.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(result)


def json_pointer_get(document: Any, pointer: str) -> Any:
    """Resolve an RFC 6901 JSON Pointer against a decoded JSON document."""

    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise LedgerValidationError(f"JSON Pointer must be empty or start with '/': {pointer!r}")

    current = document
    for encoded_token in pointer[1:].split("/"):
        token = _unescape_json_pointer_token(encoded_token)
        if isinstance(current, Mapping):
            if token not in current:
                raise LedgerValidationError(
                    f"JSON Pointer {pointer!r} has no object member {token!r}"
                )
            current = current[token]
        elif isinstance(current, list):
            if not _ARRAY_INDEX_RE.fullmatch(token):
                raise LedgerValidationError(
                    f"JSON Pointer {pointer!r} has invalid array index {token!r}"
                )
            item_index = int(token)
            if item_index >= len(current):
                raise LedgerValidationError(
                    f"JSON Pointer {pointer!r} array index {item_index} is out of range"
                )
            current = current[item_index]
        else:
            raise LedgerValidationError(
                f"JSON Pointer {pointer!r} traverses scalar value at {token!r}"
            )
    return current


def is_v038_owned_path(path: str) -> bool:
    """Return whether a path belongs to the bridge release itself."""

    lowered = path.lower()
    return any(marker in lowered for marker in ("v0.3.8", "v038", "v0_3_8"))


def is_non_raw_digest_pointer(pointer: str) -> bool:
    """Identify digest fields explicitly reserved for semantic/request identities."""

    lowered = pointer.lower()
    return any(marker in lowered for marker in _NON_RAW_POINTER_MARKERS)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LedgerValidationError(f"{label} must be a JSON object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise LedgerValidationError(f"{label} must be a JSON array")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise LedgerValidationError(f"{label} must be a string")
    return value


def _require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LedgerValidationError(f"{label} must be an integer")
    return value


def _require_digest(value: Any, label: str) -> str:
    digest = _require_string(value, label)
    if not _SHA256_RE.fullmatch(digest):
        raise LedgerValidationError(f"{label} must be a lower-case SHA-256 digest")
    return digest


def _require_repository_path(value: Any, label: str) -> str:
    path = _require_string(value, label)
    pure = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() != path
    ):
        raise LedgerValidationError(f"{label} must be a normalized relative POSIX path")
    return path


def _repository_file(root: Path, relative_path: str) -> Path:
    resolved_root = root.resolve()
    candidate = (resolved_root / Path(*PurePosixPath(relative_path).parts)).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise LedgerValidationError(
            f"repository path escapes the root: {relative_path!r}"
        ) from error
    if not candidate.is_file():
        raise LedgerValidationError(f"repository file is missing: {relative_path}")
    return candidate


def validate_ledger_structure(payload: Any) -> dict[str, int]:
    """Validate schema, deterministic ordering, and cross-record counts."""

    ledger = _require_mapping(payload, "ledger")
    if ledger.get("schema_version") != SCHEMA_VERSION:
        raise LedgerValidationError(f"unexpected schema_version: {ledger.get('schema_version')!r}")
    if ledger.get("version") != "0.3.8":
        raise LedgerValidationError("ledger version must be 0.3.8")

    targets = _require_list(ledger.get("targets"), "targets")
    bindings = _require_list(ledger.get("bindings"), "bindings")
    counts = _require_mapping(ledger.get("counts"), "counts")

    target_by_path: dict[str, Mapping[str, Any]] = {}
    target_edge_counts: Counter[str] = Counter()
    target_paths_in_order: list[str] = []
    for index, value in enumerate(targets):
        target = _require_mapping(value, f"targets[{index}]")
        path = _require_repository_path(target.get("path"), f"targets[{index}].path")
        if path in target_by_path:
            raise LedgerValidationError(f"duplicate target path: {path}")
        if is_v038_owned_path(path):
            raise LedgerValidationError(f"v0.3.8-owned target must be excluded: {path}")

        raw_digest = _require_digest(
            target.get("current_raw_sha256"),
            f"targets[{index}].current_raw_sha256",
        )
        canonical_digest = _require_digest(
            target.get("canonical_lf_sha256"),
            f"targets[{index}].canonical_lf_sha256",
        )
        virtual_digest = _require_digest(
            target.get("virtual_crlf_sha256"),
            f"targets[{index}].virtual_crlf_sha256",
        )
        raw_size = _require_int(
            target.get("current_raw_size_bytes"),
            f"targets[{index}].current_raw_size_bytes",
        )
        canonical_size = _require_int(
            target.get("canonical_lf_size_bytes"),
            f"targets[{index}].canonical_lf_size_bytes",
        )
        virtual_size = _require_int(
            target.get("virtual_crlf_size_bytes"),
            f"targets[{index}].virtual_crlf_size_bytes",
        )
        lf_count = _require_int(target.get("lf_count"), f"targets[{index}].lf_count")
        _require_int(
            target.get("legacy_binding_count"),
            f"targets[{index}].legacy_binding_count",
        )
        if min(raw_size, canonical_size, virtual_size, lf_count) < 0:
            raise LedgerValidationError(f"target sizes/counts cannot be negative: {path}")
        if raw_digest != canonical_digest or raw_size != canonical_size:
            raise LedgerValidationError(f"target is not recorded as current canonical LF: {path}")
        if lf_count == 0 or virtual_size != canonical_size + lf_count:
            raise LedgerValidationError(f"target has inconsistent LF/CRLF byte counts: {path}")
        if virtual_digest == canonical_digest:
            raise LedgerValidationError(f"target has no line-ending-dependent hash: {path}")

        target_by_path[path] = target
        target_paths_in_order.append(path)

    if target_paths_in_order != sorted(target_paths_in_order):
        raise LedgerValidationError("targets must be sorted by path")

    binding_identities: set[tuple[str, str]] = set()
    consumer_paths: set[str] = set()
    ambiguous_bindings = 0
    binding_sort_keys: list[tuple[str, str, str]] = []
    for index, value in enumerate(bindings):
        binding = _require_mapping(value, f"bindings[{index}]")
        consumer_path = _require_repository_path(
            binding.get("consumer_path"),
            f"bindings[{index}].consumer_path",
        )
        if is_v038_owned_path(consumer_path):
            raise LedgerValidationError(
                f"v0.3.8-owned consumer must be excluded: {consumer_path}"
            )
        pointer = _require_string(binding.get("json_pointer"), f"bindings[{index}].json_pointer")
        if pointer and not pointer.startswith("/"):
            raise LedgerValidationError(f"invalid JSON Pointer in binding: {pointer!r}")
        if is_non_raw_digest_pointer(pointer):
            raise LedgerValidationError(
                f"semantic/request digest cannot be classified as raw bytes: {pointer}"
            )
        recorded_value = _require_string(
            binding.get("recorded_value"),
            f"bindings[{index}].recorded_value",
        )
        legacy_digest = _require_digest(
            binding.get("legacy_raw_sha256"),
            f"bindings[{index}].legacy_raw_sha256",
        )
        prefix_present = binding.get("sha256_prefix_present")
        if not isinstance(prefix_present, bool):
            raise LedgerValidationError(
                f"bindings[{index}].sha256_prefix_present must be boolean"
            )
        expected_recorded = f"sha256:{legacy_digest}" if prefix_present else legacy_digest
        if recorded_value != expected_recorded:
            raise LedgerValidationError(
                f"recorded digest/prefix mismatch at {consumer_path}{pointer}"
            )
        if binding.get("binding_kind") != BINDING_KIND:
            raise LedgerValidationError(f"unexpected binding kind at {consumer_path}{pointer}")

        candidates_value = _require_list(
            binding.get("target_paths"),
            f"bindings[{index}].target_paths",
        )
        candidate_paths = [
            _require_repository_path(candidate, f"bindings[{index}].target_paths")
            for candidate in candidates_value
        ]
        if not candidate_paths or candidate_paths != sorted(set(candidate_paths)):
            raise LedgerValidationError(
                f"target_paths must be a non-empty sorted unique list at {consumer_path}{pointer}"
            )
        for candidate in candidate_paths:
            if candidate not in target_by_path:
                raise LedgerValidationError(
                    f"binding references undeclared target {candidate!r}"
                )
            if target_by_path[candidate]["virtual_crlf_sha256"] != legacy_digest:
                raise LedgerValidationError(
                    f"binding digest differs from virtual CRLF target {candidate!r}"
                )
            target_edge_counts[candidate] += 1

        identity = (consumer_path, pointer)
        if identity in binding_identities:
            raise LedgerValidationError(f"duplicate binding location: {consumer_path}{pointer}")
        binding_identities.add(identity)
        consumer_paths.add(consumer_path)
        ambiguous_bindings += len(candidate_paths) > 1
        binding_sort_keys.append((consumer_path, pointer, legacy_digest))

    if binding_sort_keys != sorted(binding_sort_keys):
        raise LedgerValidationError("bindings must be sorted by consumer, pointer, and digest")

    for path, target in target_by_path.items():
        if target_edge_counts[path] != target["legacy_binding_count"]:
            raise LedgerValidationError(f"legacy binding count mismatch for target {path}")

    computed_counts = {
        "legacy_raw_bindings": len(bindings),
        "unique_consumers": len(consumer_paths),
        "unique_targets": len(targets),
        "target_candidate_edges": sum(target_edge_counts.values()),
        "ambiguous_bindings": ambiguous_bindings,
    }
    for key, computed in computed_counts.items():
        recorded = _require_int(counts.get(key), f"counts.{key}")
        if recorded != computed:
            raise LedgerValidationError(
                f"counts.{key} is {recorded}, expected computed value {computed}"
            )
    expected_counts = {
        "legacy_raw_bindings": EXPECTED_BINDING_COUNT,
        "unique_consumers": EXPECTED_CONSUMER_COUNT,
        "unique_targets": EXPECTED_TARGET_COUNT,
    }
    for key, expected in expected_counts.items():
        if computed_counts[key] != expected:
            raise LedgerValidationError(
                f"frozen v0.3.8 scope requires {key}={expected}, got {computed_counts[key]}"
            )
    return computed_counts


def verify_line_ending_bridge(root: Path, payload: Any) -> dict[str, Any]:
    """Verify every target hash and every JSON Pointer binding against *root*."""

    counts = validate_ledger_structure(payload)
    ledger = _require_mapping(payload, "ledger")
    targets = _require_list(ledger["targets"], "targets")
    bindings = _require_list(ledger["bindings"], "bindings")

    target_hashes: dict[str, dict[str, Any]] = {}
    for value in targets:
        target = _require_mapping(value, "target")
        relative_path = _require_string(target["path"], "target.path")
        artifact_path = _repository_file(root, relative_path)
        observed = line_ending_hashes(artifact_path, require_canonical_lf=True)
        for field, observed_value in observed.items():
            if target.get(field) != observed_value:
                raise LedgerValidationError(
                    f"{relative_path}: recorded {field} does not match repository bytes"
                )
        target_hashes[relative_path] = observed

    parsed_consumers: dict[str, Any] = {}
    for value in bindings:
        binding = _require_mapping(value, "binding")
        consumer_path = _require_string(binding["consumer_path"], "binding.consumer_path")
        if consumer_path not in parsed_consumers:
            path = _repository_file(root, consumer_path)
            data = strict_lf_bytes(path.read_bytes(), source=consumer_path)
            try:
                parsed_consumers[consumer_path] = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError as error:
                raise LedgerValidationError(
                    f"consumer is not valid JSON: {consumer_path}"
                ) from error
        pointer = _require_string(binding["json_pointer"], "binding.json_pointer")
        observed_value = json_pointer_get(parsed_consumers[consumer_path], pointer)
        if observed_value != binding["recorded_value"]:
            raise LedgerValidationError(
                f"JSON Pointer value changed at {consumer_path}{pointer}"
            )
        legacy_digest = _require_string(
            binding["legacy_raw_sha256"],
            "binding.legacy_raw_sha256",
        )
        for target_path in binding["target_paths"]:
            if target_hashes[target_path]["virtual_crlf_sha256"] != legacy_digest:
                raise LedgerValidationError(
                    f"virtual CRLF bridge failed at {consumer_path}{pointer}"
                )

    return {
        "passed": True,
        **counts,
        "all_targets_currently_canonical_lf": True,
        "all_bindings_resolve_by_json_pointer": True,
    }


def load_line_ending_bridge(path: Path) -> dict[str, Any]:
    """Load a bridge ledger as strict UTF-8 canonical-LF JSON."""

    data = strict_lf_bytes(path.read_bytes(), source=str(path))
    try:
        payload = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise LedgerValidationError(f"bridge ledger is not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise LedgerValidationError("bridge ledger root must be a JSON object")
    return payload
