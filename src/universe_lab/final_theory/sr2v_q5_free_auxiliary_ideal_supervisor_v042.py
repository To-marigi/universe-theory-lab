"""Pure-Python supervision primitives for the SR2-V auxiliary-ideal campaign.

This module deliberately does not launch Docker or Sage.  It supplies the
fail-closed control-plane pieces needed around a future worker: strict budget
validation, content-addressed requests, immutable attempt directories, durable
hash-chained logs, aggregate budget accounting, and process-exit classification.

The mathematical worker and its container lifecycle remain separate.  Keeping
this module free of Sage imports makes every supervision rule fast to test
before an expensive CAS request is authorised.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import tempfile
import uuid
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import IO, Final

type JsonScalar = None | bool | int | float | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

BUDGET_KEYS: Final = frozenset(
    {"timeout_seconds_per_chart", "total_wall_time_seconds", "memory_limit_gib"}
)
RECIPE_ENVELOPE_SCHEMA: Final = "sr2v-q5-free-recipe-envelope-v1"
ATTEMPT_IDENTITY_SCHEMA: Final = "sr2v-q5-free-attempt-identity-v1"
ATTEMPT_MANIFEST_SCHEMA: Final = "sr2v-q5-free-attempt-manifest-v1"
ATTEMPT_STATE_SCHEMA: Final = "sr2v-q5-free-attempt-state-v1"
ATTEMPT_RESULT_SCHEMA: Final = "sr2v-q5-free-attempt-result-v1"
HASH_CHAIN_SCHEMA: Final = "sr2v-q5-free-hash-chain-event-v1"
ZERO_SHA256: Final = "0" * 64

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_ATTEMPT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")


class SupervisorError(RuntimeError):
    """Base class for fail-closed supervision failures."""


class EnvelopeValidationError(SupervisorError):
    """A content-addressed envelope is malformed or has the wrong digest."""


class AttemptHistoryError(SupervisorError):
    """Persisted attempt history is malformed or internally inconsistent."""


class HashChainValidationError(SupervisorError):
    """A JSONL event stream is truncated, noncanonical, or has a broken chain."""


def _normalise_json_value(value: object, *, path: str = "$") -> JsonValue:
    """Return an independent JSON value, rejecting ambiguous Python objects."""

    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path}: non-finite floats are not canonical JSON")
        return value
    if isinstance(value, list):
        return [
            _normalise_json_value(item, path=f"{path}[{index}]") for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        result: JsonObject = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path}: JSON object keys must be strings")
            result[key] = _normalise_json_value(item, path=f"{path}.{key}")
        return result
    raise TypeError(f"{path}: unsupported canonical JSON type {type(value).__name__}")


def _normalise_json_object(value: Mapping[str, object], *, label: str) -> JsonObject:
    normalised = _normalise_json_value(value, path=label)
    if not isinstance(normalised, dict):  # pragma: no cover - Mapping always normalises to dict
        raise TypeError(f"{label} must be a JSON object")
    return normalised


def canonical_json_bytes(value: object) -> bytes:
    """Encode a JSON-compatible value with one deterministic representation."""

    normalised = _normalise_json_value(value)
    return json.dumps(
        normalised,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_payload_sha256(value: object) -> str:
    """Return the SHA-256 of :func:`canonical_json_bytes`."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_exact_keys(
    payload: Mapping[str, object],
    expected: set[str] | frozenset[str],
    *,
    label: str,
) -> None:
    actual = set(payload)
    missing = sorted(expected - actual)
    unsupported = sorted(actual - expected)
    if missing or unsupported:
        raise ValueError(
            f"{label} keys do not match the contract; missing={missing}, unsupported={unsupported}"
        )


def _strict_positive_int(value: object, *, label: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be a positive integer (bool and non-integers are rejected)")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def _strict_nonnegative_int(value: object, *, label: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{label} must be non-negative")
    return value


def _require_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase 64-character SHA-256 digest")
    return value


def _require_nonempty_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class CampaignBudget:
    """Strict, externally authorised campaign limits."""

    timeout_seconds_per_chart: int
    total_wall_time_seconds: int
    memory_limit_gib: int

    @property
    def memory_limit_bytes(self) -> int:
        return self.memory_limit_gib * 1024**3

    def to_payload(self) -> JsonObject:
        return {
            "memory_limit_gib": self.memory_limit_gib,
            "timeout_seconds_per_chart": self.timeout_seconds_per_chart,
            "total_wall_time_seconds": self.total_wall_time_seconds,
        }

    @property
    def payload_sha256(self) -> str:
        return canonical_payload_sha256(self.to_payload())


def validate_budget(payload: Mapping[str, object]) -> CampaignBudget:
    """Validate the exact three-field human budget without coercion or defaults."""

    _require_exact_keys(payload, BUDGET_KEYS, label="budget")
    timeout = _strict_positive_int(
        payload["timeout_seconds_per_chart"], label="timeout_seconds_per_chart"
    )
    total = _strict_positive_int(
        payload["total_wall_time_seconds"], label="total_wall_time_seconds"
    )
    memory = _strict_positive_int(payload["memory_limit_gib"], label="memory_limit_gib")
    if timeout > total:
        raise ValueError("timeout_seconds_per_chart cannot exceed total_wall_time_seconds")
    return CampaignBudget(timeout, total, memory)


@dataclass(frozen=True, slots=True)
class VerifiedRecipeEnvelope:
    """A verified copy of a canonical recipe envelope."""

    payload: JsonObject
    payload_digest_sha256: str

    def to_payload(self) -> JsonObject:
        return {
            "payload": _normalise_json_object(self.payload, label="recipe payload"),
            "payload_digest_sha256": self.payload_digest_sha256,
            "schema_version": RECIPE_ENVELOPE_SCHEMA,
        }

    @property
    def envelope_digest_sha256(self) -> str:
        return canonical_payload_sha256(self.to_payload())


def create_recipe_envelope(recipe_payload: Mapping[str, object]) -> JsonObject:
    """Copy a recipe into an envelope bound by its canonical payload digest."""

    payload = _normalise_json_object(recipe_payload, label="recipe payload")
    digest = canonical_payload_sha256(payload)
    return VerifiedRecipeEnvelope(payload, digest).to_payload()


def verify_recipe_envelope(envelope: Mapping[str, object]) -> VerifiedRecipeEnvelope:
    """Fail closed unless an envelope has the exact schema and payload digest."""

    expected_keys = {"schema_version", "payload_digest_sha256", "payload"}
    try:
        _require_exact_keys(envelope, expected_keys, label="recipe envelope")
        if envelope["schema_version"] != RECIPE_ENVELOPE_SCHEMA:
            raise ValueError("recipe envelope schema_version is unsupported")
        claimed = _require_sha256(envelope["payload_digest_sha256"], label="recipe payload digest")
        raw_payload = envelope["payload"]
        if not isinstance(raw_payload, Mapping):
            raise TypeError("recipe envelope payload must be a JSON object")
        payload = _normalise_json_object(raw_payload, label="recipe payload")
        observed = canonical_payload_sha256(payload)
        if not hmac.compare_digest(claimed, observed):
            raise ValueError("recipe payload digest does not match its canonical content")
    except (TypeError, ValueError) as error:
        raise EnvelopeValidationError(str(error)) from error
    return VerifiedRecipeEnvelope(payload, claimed)


@dataclass(frozen=True, slots=True)
class AttemptFingerprint:
    """Canonical attempt identity and its content-addressed SHA-256."""

    identity: JsonObject
    sha256: str


def create_attempt_fingerprint(
    *,
    chart: str,
    coefficient_modulus: int,
    recipe_payload_digest_sha256: str,
    budget_payload_digest_sha256: str,
    worker_source_sha256: str,
    container_image_digest: str,
    monomial_order: str,
    execution_policy: Mapping[str, object],
) -> AttemptFingerprint:
    """Build a timestamp-free identity for one unchanged solver request."""

    identity: JsonObject = {
        "budget_payload_digest_sha256": _require_sha256(
            budget_payload_digest_sha256, label="budget payload digest"
        ),
        "chart": _require_nonempty_string(chart, label="chart"),
        "coefficient_modulus": _strict_nonnegative_int(
            coefficient_modulus, label="coefficient_modulus"
        ),
        "container_image_digest": _require_nonempty_string(
            container_image_digest, label="container_image_digest"
        ),
        "execution_policy": _normalise_json_object(execution_policy, label="execution_policy"),
        "monomial_order": _require_nonempty_string(monomial_order, label="monomial_order"),
        "recipe_payload_digest_sha256": _require_sha256(
            recipe_payload_digest_sha256, label="recipe payload digest"
        ),
        "schema_version": ATTEMPT_IDENTITY_SCHEMA,
        "worker_source_sha256": _require_sha256(worker_source_sha256, label="worker source digest"),
    }
    return AttemptFingerprint(identity=identity, sha256=canonical_payload_sha256(identity))


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_json(path: Path, payload: object, *, overwrite: bool = False) -> None:
    """Durably publish canonical JSON, atomically and without overwrite by default."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(payload) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    published = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
            temporary.unlink()
        published = True
        _fsync_directory(path.parent)
    finally:
        if not published and temporary.exists():
            temporary.unlink()


def read_json_object(path: Path) -> JsonObject:
    """Read and normalise one JSON object."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise TypeError(f"{path}: expected a JSON object")
    return _normalise_json_object(raw, label=str(path))


@dataclass(frozen=True, slots=True)
class AttemptDirectory:
    """Paths belonging to one immutable attempt instance."""

    path: Path
    fingerprint_sha256: str
    attempt_id: str

    @property
    def manifest_path(self) -> Path:
        return self.path / "attempt.json"

    @property
    def state_path(self) -> Path:
        return self.path / "state.json"

    @property
    def events_path(self) -> Path:
        return self.path / "events.jsonl"

    @property
    def result_path(self) -> Path:
        return self.path / "result.json"


def _new_attempt_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{uuid.uuid4().hex}"


def create_attempt_directory(
    attempts_root: Path,
    fingerprint: AttemptFingerprint,
    *,
    attempt_id: str | None = None,
    created_at_utc: str | None = None,
) -> AttemptDirectory:
    """Create a never-overwritten ``fingerprint/attempt-id`` directory."""

    digest = _require_sha256(fingerprint.sha256, label="attempt fingerprint")
    if canonical_payload_sha256(fingerprint.identity) != digest:
        raise ValueError("attempt identity does not reproduce its fingerprint")
    identifier = attempt_id or _new_attempt_id()
    if _ATTEMPT_ID_RE.fullmatch(identifier) is None:
        raise ValueError("attempt_id contains unsafe characters or has an invalid length")
    created = created_at_utc or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    _require_nonempty_string(created, label="created_at_utc")

    fingerprint_directory = attempts_root / digest
    fingerprint_directory.mkdir(parents=True, exist_ok=True)
    path = fingerprint_directory / identifier
    path.mkdir(exist_ok=False)
    attempt = AttemptDirectory(path, digest, identifier)
    manifest: JsonObject = {
        "attempt_id": identifier,
        "created_at_utc": created,
        "fingerprint_sha256": digest,
        "identity": _normalise_json_object(fingerprint.identity, label="attempt identity"),
        "schema_version": ATTEMPT_MANIFEST_SCHEMA,
    }
    atomic_write_json(attempt.manifest_path, manifest)
    write_attempt_state(attempt, "PREPARED", {}, overwrite=False)
    return attempt


def write_attempt_state(
    attempt: AttemptDirectory,
    lifecycle_status: str,
    details: Mapping[str, object],
    *,
    overwrite: bool = True,
) -> None:
    """Atomically publish the latest lifecycle state; the event log keeps history."""

    payload: JsonObject = {
        "attempt_id": attempt.attempt_id,
        "details": _normalise_json_object(details, label="state details"),
        "fingerprint_sha256": attempt.fingerprint_sha256,
        "lifecycle_status": _require_nonempty_string(lifecycle_status, label="lifecycle_status"),
        "schema_version": ATTEMPT_STATE_SCHEMA,
    }
    atomic_write_json(attempt.state_path, payload, overwrite=overwrite)


@dataclass(frozen=True, slots=True)
class HashChainSummary:
    record_count: int
    head_sha256: str


class HashChainJsonlWriter:
    """Exclusive, flush-on-append canonical JSONL with a SHA-256 hash chain."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._handle: IO[str] = path.open("x", encoding="utf-8", newline="\n")
        self._sequence = 0
        self._head = ZERO_SHA256
        self._closed = False

    @property
    def summary(self) -> HashChainSummary:
        return HashChainSummary(self._sequence, self._head)

    def append(self, payload: Mapping[str, object]) -> str:
        if self._closed:
            raise ValueError("cannot append to a closed hash-chain log")
        core: JsonObject = {
            "payload": _normalise_json_object(payload, label="event payload"),
            "previous_sha256": self._head,
            "schema_version": HASH_CHAIN_SCHEMA,
            "sequence": self._sequence,
        }
        record_digest = canonical_payload_sha256(core)
        record: JsonObject = {**core, "record_sha256": record_digest}
        self._handle.write(canonical_json_bytes(record).decode("utf-8") + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._head = record_digest
        self._sequence += 1
        return record_digest

    def close(self) -> None:
        if self._closed:
            return
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        self._closed = True

    def __enter__(self) -> HashChainJsonlWriter:
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()


def verify_hash_chain_jsonl(path: Path) -> HashChainSummary:
    """Verify LF framing, canonical records, sequence numbers, and every link."""

    head = ZERO_SHA256
    count = 0
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.endswith("\n") or line.endswith("\r\n"):
                    raise ValueError(f"line {line_number} is not LF-terminated")
                text = line[:-1]
                raw = json.loads(text)
                if not isinstance(raw, Mapping):
                    raise TypeError(f"line {line_number} is not a JSON object")
                record = _normalise_json_object(raw, label=f"line {line_number}")
                expected_keys = {
                    "schema_version",
                    "sequence",
                    "previous_sha256",
                    "payload",
                    "record_sha256",
                }
                _require_exact_keys(record, expected_keys, label=f"line {line_number}")
                if text.encode("utf-8") != canonical_json_bytes(record):
                    raise ValueError(f"line {line_number} is not canonical JSON")
                if record["schema_version"] != HASH_CHAIN_SCHEMA:
                    raise ValueError(f"line {line_number} has an unsupported schema")
                if type(record["sequence"]) is not int or record["sequence"] != count:
                    raise ValueError(f"line {line_number} has a non-contiguous sequence")
                if not isinstance(record["payload"], dict):
                    raise TypeError(f"line {line_number} payload is not a JSON object")
                previous = _require_sha256(
                    record["previous_sha256"], label=f"line {line_number} previous digest"
                )
                if not hmac.compare_digest(previous, head):
                    raise ValueError(f"line {line_number} breaks the previous-digest chain")
                claimed = _require_sha256(
                    record["record_sha256"], label=f"line {line_number} record digest"
                )
                core: JsonObject = {
                    "payload": record["payload"],
                    "previous_sha256": previous,
                    "schema_version": HASH_CHAIN_SCHEMA,
                    "sequence": count,
                }
                observed = canonical_payload_sha256(core)
                if not hmac.compare_digest(claimed, observed):
                    raise ValueError(f"line {line_number} has the wrong record digest")
                head = claimed
                count += 1
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HashChainValidationError(f"{path}: {error}") from error
    return HashChainSummary(count, head)


class StatusClassification(StrEnum):
    SUCCESS = "SUCCESS"
    NONTERMINAL = "NONTERMINAL"
    OPERATIONAL_ERROR = "OPERATIONAL_ERROR"
    INVALID = "INVALID"


SUCCESS_STATUSES: Final = frozenset(
    {
        "BUILD_COMPLETED",
        "COMPLETED",
        "RECIPE_ONLY_COMPLETED",
        "REDUNDANCY_AUDIT_COMPLETED",
    }
)
NONTERMINAL_STATUSES: Final = frozenset(
    {
        "TIMEOUT",
        "SOFT_RESOURCE_LIMIT",
        "NOT_RUN_TOTAL_BUDGET_EXHAUSTED",
        "UNIT_IDEAL_FOUND_CERTIFICATE_PENDING",
        "WEAK_D2_OPEN_RESOURCE_LIMIT",
    }
)
OPERATIONAL_ERROR_STATUSES: Final = frozenset(
    {
        "EMPTY_BACKEND_RESPONSE",
        "NON_JSON_BACKEND_RESPONSE",
        "HOST_INTERRUPTED",
        "KILL_UNVERIFIED",
        "DOCKER_DAEMON_LOST",
        "OOM",
    }
)
UNSAFE_TERMINATION_STATUSES: Final = frozenset({"KILL_UNVERIFIED", "DOCKER_DAEMON_LOST"})
EXIT_CODE_BY_CLASSIFICATION: Final = {
    StatusClassification.SUCCESS: 0,
    StatusClassification.NONTERMINAL: 2,
    StatusClassification.OPERATIONAL_ERROR: 3,
    StatusClassification.INVALID: 4,
}


def classify_status(status: str) -> StatusClassification:
    """Classify a worker status; every non-success class maps to nonzero."""

    if status in SUCCESS_STATUSES:
        return StatusClassification.SUCCESS
    if status in NONTERMINAL_STATUSES:
        return StatusClassification.NONTERMINAL
    if status in OPERATIONAL_ERROR_STATUSES or status.startswith("ERROR_"):
        return StatusClassification.OPERATIONAL_ERROR
    return StatusClassification.INVALID


def exit_code_for_status(status: str) -> int:
    return EXIT_CODE_BY_CLASSIFICATION[classify_status(status)]


def _validated_wall_time(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{label} must be a finite non-negative number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} must be a finite non-negative number")
    return result


def record_attempt_result(
    attempt: AttemptDirectory,
    *,
    status: str,
    wall_time_seconds: int | float,
    details: Mapping[str, object],
) -> JsonObject:
    """Write a result exactly once and bind it to its attempt fingerprint."""

    status_value = _require_nonempty_string(status, label="status")
    classification = classify_status(status_value)
    payload: JsonObject = {
        "attempt_id": attempt.attempt_id,
        "details": _normalise_json_object(details, label="result details"),
        "fingerprint_sha256": attempt.fingerprint_sha256,
        "recommended_exit_code": EXIT_CODE_BY_CLASSIFICATION[classification],
        "schema_version": ATTEMPT_RESULT_SCHEMA,
        "status": status_value,
        "status_classification": classification.value,
        "wall_time_seconds": _validated_wall_time(wall_time_seconds, label="wall_time_seconds"),
    }
    atomic_write_json(attempt.result_path, payload)
    return payload


@dataclass(frozen=True, slots=True)
class AttemptHistory:
    aggregate_wall_time_seconds: float
    completed_attempt_count: int
    incomplete_attempt_count: int
    timed_out_fingerprints: frozenset[str]
    incomplete_fingerprints: frozenset[str]
    unsafe_termination_fingerprints: frozenset[str]
    status_counts: tuple[tuple[str, int], ...]


def _validate_attempt_manifest(
    attempt_path: Path, fingerprint_from_path: str, attempt_id_from_path: str
) -> JsonObject:
    manifest_path = attempt_path / "attempt.json"
    if not manifest_path.is_file():
        raise AttemptHistoryError(f"{attempt_path}: attempt.json is missing")
    manifest = read_json_object(manifest_path)
    expected_keys = {
        "schema_version",
        "attempt_id",
        "created_at_utc",
        "fingerprint_sha256",
        "identity",
    }
    _require_exact_keys(manifest, expected_keys, label=str(manifest_path))
    if manifest["schema_version"] != ATTEMPT_MANIFEST_SCHEMA:
        raise AttemptHistoryError(f"{manifest_path}: unsupported manifest schema")
    if manifest["attempt_id"] != attempt_id_from_path:
        raise AttemptHistoryError(f"{manifest_path}: attempt_id disagrees with its directory")
    if manifest["fingerprint_sha256"] != fingerprint_from_path:
        raise AttemptHistoryError(f"{manifest_path}: fingerprint disagrees with its directory")
    identity = manifest["identity"]
    if (
        not isinstance(identity, dict)
        or canonical_payload_sha256(identity) != fingerprint_from_path
    ):
        raise AttemptHistoryError(f"{manifest_path}: identity does not reproduce the fingerprint")
    return manifest


def _validate_attempt_result(result_path: Path, fingerprint: str, attempt_id: str) -> JsonObject:
    result = read_json_object(result_path)
    expected_keys = {
        "schema_version",
        "attempt_id",
        "fingerprint_sha256",
        "status",
        "status_classification",
        "recommended_exit_code",
        "wall_time_seconds",
        "details",
    }
    _require_exact_keys(result, expected_keys, label=str(result_path))
    if result["schema_version"] != ATTEMPT_RESULT_SCHEMA:
        raise AttemptHistoryError(f"{result_path}: unsupported result schema")
    if result["attempt_id"] != attempt_id or result["fingerprint_sha256"] != fingerprint:
        raise AttemptHistoryError(f"{result_path}: result binding disagrees with its directory")
    status = result["status"]
    if not isinstance(status, str):
        raise AttemptHistoryError(f"{result_path}: status must be a string")
    classification = classify_status(status)
    if result["status_classification"] != classification.value:
        raise AttemptHistoryError(f"{result_path}: status classification is inconsistent")
    if result["recommended_exit_code"] != EXIT_CODE_BY_CLASSIFICATION[classification]:
        raise AttemptHistoryError(f"{result_path}: recommended exit code is inconsistent")
    _validated_wall_time(result["wall_time_seconds"], label=f"{result_path} wall time")
    return result


_PRODUCTION_BINDING_DETAIL_KEYS: Final = frozenset(
    {
        "cleanup_verified",
        "container_image_digest",
        "event_log_head_sha256",
        "event_log_record_count",
        "process_returncode",
        "request_payload_sha256",
        "worker_result",
        "worker_source_sha256",
    }
)
_RUNTIME_BINDING_DETAIL_KEYS: Final = frozenset(
    {
        "container_contract_verified",
        "host_process_termination_verified",
        "postflight_audit_verified",
        "postflight_legacy_processes",
        "postflight_stale_containers",
        "terminal_attempt_status",
        "terminal_cleanup_verified",
        "terminal_process_returncode",
    }
)
RUNTIME_BINDING_SCHEMA: Final = "sr2v-runtime-binding-v1"


def _validate_source_snapshot(
    attempt_path: Path, source_bindings: Mapping[str, object]
) -> dict[str, str]:
    snapshot_path = attempt_path / "source_snapshot.json"
    snapshot = read_json_object(snapshot_path)
    _require_exact_keys(snapshot, {"schema_version", "records"}, label=str(snapshot_path))
    if snapshot["schema_version"] != "sr2v-solver-source-snapshot-v1":
        raise ValueError(f"{snapshot_path}: unsupported source snapshot schema")
    records = snapshot["records"]
    if not isinstance(records, Mapping):
        raise TypeError(f"{snapshot_path}: records must be an object")
    observed: dict[str, str] = {}
    for source_path, raw_record in records.items():
        if not isinstance(source_path, str) or not isinstance(raw_record, Mapping):
            raise TypeError(f"{snapshot_path}: malformed source record")
        _require_exact_keys(raw_record, {"sha256", "text"}, label=f"{snapshot_path}:{source_path}")
        claimed = _require_sha256(
            raw_record["sha256"], label=f"{snapshot_path}:{source_path} digest"
        )
        text = raw_record["text"]
        if not isinstance(text, str):
            raise TypeError(f"{snapshot_path}:{source_path}: text must be a string")
        actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(claimed, actual):
            raise ValueError(f"{snapshot_path}:{source_path}: text digest mismatch")
        observed[source_path] = claimed
    expected = {
        path: _require_sha256(digest, label=f"source binding {path}")
        for path, digest in source_bindings.items()
        if isinstance(path, str)
    }
    if len(expected) != len(source_bindings) or observed != expected:
        raise ValueError(f"{snapshot_path}: records disagree with fingerprint source bindings")
    return observed


def _last_hash_chain_payload(path: Path) -> Mapping[str, object]:
    lines = path.read_bytes().splitlines()
    if not lines:
        raise ValueError(f"{path}: event log is empty")
    record = json.loads(lines[-1])
    if not isinstance(record, Mapping) or not isinstance(record.get("payload"), Mapping):
        raise TypeError(f"{path}: terminal event record is malformed")
    return record["payload"]


def _validate_production_attempt_bindings(
    attempt_path: Path,
    manifest: Mapping[str, object],
    result: Mapping[str, object],
) -> None:
    details = result["details"]
    if not isinstance(details, Mapping):
        raise AttemptHistoryError(f"{attempt_path}: result details must be an object")
    identity = manifest["identity"]
    if not isinstance(identity, Mapping):  # already checked by manifest validation
        raise AttemptHistoryError(f"{attempt_path}: identity must be an object")
    execution_policy = identity["execution_policy"]
    if not isinstance(execution_policy, Mapping):
        raise AttemptHistoryError(f"{attempt_path}: identity execution_policy must be an object")
    runtime_binding_schema = execution_policy.get("runtime_binding_schema")
    if runtime_binding_schema not in {None, RUNTIME_BINDING_SCHEMA}:
        raise AttemptHistoryError(f"{attempt_path}: unsupported runtime binding schema")
    if runtime_binding_schema == RUNTIME_BINDING_SCHEMA:
        missing_runtime = sorted(_RUNTIME_BINDING_DETAIL_KEYS - set(details))
        if missing_runtime:
            raise AttemptHistoryError(
                f"{attempt_path}: runtime result bindings missing {missing_runtime}"
            )
    is_production_attempt = execution_policy.get("single_worker") is True
    present = _PRODUCTION_BINDING_DETAIL_KEYS & set(details)
    if not is_production_attempt and not present:
        return
    missing = sorted(_PRODUCTION_BINDING_DETAIL_KEYS - set(details))
    if missing:
        raise AttemptHistoryError(f"{attempt_path}: production result bindings missing {missing}")
    try:
        status = result["status"]
        if not isinstance(status, str):
            raise TypeError("result status must be a string")
        prelaunch_artifact_failure = bool(
            (
                status.startswith("ERROR_CAMPAIGN_")
                or status in {"HOST_INTERRUPTED", "KILL_UNVERIFIED"}
            )
            and details.get("failure_phase") == "ARTIFACT_WRITE"
            and details.get("launch_may_have_occurred") is False
        )
        request_digest = _require_sha256(
            details["request_payload_sha256"], label="result request payload digest"
        )
        identity_request_digest = _require_sha256(
            identity["recipe_payload_digest_sha256"], label="identity recipe payload digest"
        )
        request_path = attempt_path / "request.json"
        if request_path.is_file():
            request = verify_recipe_envelope(read_json_object(request_path))
            request_content_matches = hmac.compare_digest(
                request_digest, request.payload_digest_sha256
            )
        else:
            request_content_matches = prelaunch_artifact_failure
        if (
            not hmac.compare_digest(request_digest, identity_request_digest)
            or not request_content_matches
        ):
            raise ValueError("request digest disagrees across request, result, and manifest")

        worker_digest = _require_sha256(
            details["worker_source_sha256"], label="result worker source digest"
        )
        identity_worker_digest = _require_sha256(
            identity["worker_source_sha256"], label="identity worker source digest"
        )
        if not hmac.compare_digest(worker_digest, identity_worker_digest):
            raise ValueError("worker source digest disagrees with manifest identity")
        if details["container_image_digest"] != identity["container_image_digest"]:
            raise ValueError("container image digest disagrees with manifest identity")

        cleanup_verified = details["cleanup_verified"]
        if type(cleanup_verified) is not bool:
            raise TypeError("cleanup_verified must be boolean")
        if status in UNSAFE_TERMINATION_STATUSES:
            if cleanup_verified:
                raise ValueError("unsafe termination cannot claim verified cleanup")
        elif not cleanup_verified:
            raise ValueError("unverified cleanup must be classified as an unsafe termination")
        enhanced_runtime_binding = runtime_binding_schema == RUNTIME_BINDING_SCHEMA
        if enhanced_runtime_binding:
            container_contract_verified = details["container_contract_verified"]
            host_process_verified = details.get("host_process_termination_verified")
            postflight_verified = details.get("postflight_audit_verified")
            stale_containers = details.get("postflight_stale_containers")
            legacy_processes = details.get("postflight_legacy_processes")
            if type(container_contract_verified) is not bool:
                raise TypeError("container_contract_verified must be boolean")
            if type(host_process_verified) is not bool or type(postflight_verified) is not bool:
                raise TypeError("host-process and postflight audit fields must be boolean")
            if not isinstance(stale_containers, list) or not isinstance(legacy_processes, list):
                raise TypeError("postflight survivor fields must be lists")
            if cleanup_verified and not (
                host_process_verified
                and postflight_verified
                and not stale_containers
                and not legacy_processes
            ):
                raise ValueError("verified cleanup lacks zero-survivor runtime evidence")
            if (
                classify_status(status)
                in {
                    StatusClassification.SUCCESS,
                    StatusClassification.NONTERMINAL,
                }
                and not container_contract_verified
            ):
                raise ValueError(
                    "successful/nonterminal attempt lacks a verified container contract"
                )

        event_log_valid = details.get("event_log_valid", True)
        if type(event_log_valid) is not bool:
            raise TypeError("event_log_valid must be boolean when present")
        if event_log_valid:
            event_summary = verify_hash_chain_jsonl(attempt_path / "events.jsonl")
            event_head = _require_sha256(
                details["event_log_head_sha256"], label="result event-log head"
            )
            event_count = details["event_log_record_count"]
            if type(event_count) is not int or event_count < 0:
                raise TypeError("event_log_record_count must be a non-negative integer")
            if event_summary != HashChainSummary(event_count, event_head):
                raise ValueError("event log head/count disagree with result details")
            if details.get("event_log_valid") is True:
                terminal_event = _last_hash_chain_payload(attempt_path / "events.jsonl")
                if terminal_event.get("event") != "CONTAINER_ATTEMPT_FINISHED":
                    raise ValueError("event log has no authenticated terminal attempt event")
                if "failure_phase" in details:
                    expected_terminal_status = details.get("terminal_attempt_status")
                    expected_terminal_cleanup = details.get("terminal_cleanup_verified")
                    expected_terminal_returncode = details.get("terminal_process_returncode")
                    if not isinstance(expected_terminal_status, str):
                        raise TypeError("finalizer result must bind terminal_attempt_status")
                    if type(expected_terminal_cleanup) is not bool:
                        raise TypeError("finalizer result must bind terminal_cleanup_verified")
                    if (
                        expected_terminal_returncode is not None
                        and type(expected_terminal_returncode) is not int
                    ):
                        raise TypeError("terminal_process_returncode must be an integer or null")
                else:
                    expected_terminal_status = status
                    expected_terminal_cleanup = cleanup_verified
                    expected_terminal_returncode = details["process_returncode"]
                    if enhanced_runtime_binding and (
                        details["terminal_attempt_status"] != expected_terminal_status
                        or details["terminal_cleanup_verified"] is not expected_terminal_cleanup
                        or details["terminal_process_returncode"] != expected_terminal_returncode
                    ):
                        raise ValueError("runtime terminal bindings disagree with result")
                if terminal_event.get("status") != expected_terminal_status:
                    raise ValueError("terminal event status disagrees with result status")
                if terminal_event.get("cleanup_verified") is not expected_terminal_cleanup:
                    raise ValueError("terminal event cleanup state disagrees with result")
                if terminal_event.get("process_returncode") != expected_terminal_returncode:
                    raise ValueError("terminal event process return code disagrees with result")
                if "host_process_termination_verified" in details:
                    host_process_verified = details["host_process_termination_verified"]
                    if type(host_process_verified) is not bool:
                        raise TypeError("host_process_termination_verified must be boolean")
                    if (
                        terminal_event.get("host_process_termination_verified")
                        is not host_process_verified
                    ):
                        raise ValueError("terminal event host-process audit disagrees with result")
                if enhanced_runtime_binding:
                    if (
                        terminal_event.get("container_contract_verified")
                        is not details["container_contract_verified"]
                    ):
                        raise ValueError("terminal event container contract disagrees with result")
                    if (
                        terminal_event.get("postflight_audit_verified")
                        is not details["postflight_audit_verified"]
                    ):
                        raise ValueError("terminal event postflight audit disagrees with result")
        elif not (
            status.startswith("ERROR_CAMPAIGN_")
            or status in {"HOST_INTERRUPTED", "KILL_UNVERIFIED"}
        ):
            raise ValueError("only an operational finalizer result may bind an invalid event log")

        source_bindings = execution_policy.get("source_bindings")
        if source_bindings is not None:
            if not isinstance(source_bindings, Mapping):
                raise TypeError("source_bindings must be an object")
            snapshot_path = attempt_path / "source_snapshot.json"
            if snapshot_path.is_file():
                observed_sources = _validate_source_snapshot(attempt_path, source_bindings)
                worker_path = (
                    "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_worker_v042.py"
                )
                if observed_sources.get(worker_path) != identity_worker_digest:
                    raise ValueError("worker snapshot digest disagrees with worker identity")
            elif not prelaunch_artifact_failure:
                raise ValueError("source snapshot is missing")

        worker_result = details["worker_result"]
        process_returncode = details["process_returncode"]
        if process_returncode is not None and type(process_returncode) is not int:
            raise TypeError("process_returncode must be an integer or null")
        if worker_result is not None:
            if not isinstance(worker_result, Mapping):
                raise TypeError("worker_result must be an object or null")
            if (
                worker_result.get("schema_version") != "sr2v-q5-free-worker-message-v1"
                or worker_result.get("message_type") != "result"
                or worker_result.get("event") not in {"WORKER_FINISHED", "WORKER_FAILED"}
            ):
                raise ValueError("worker_result has an invalid worker protocol envelope")
            worker_status = worker_result.get("status")
            worker_authoritative = (
                classify_status(status) is StatusClassification.SUCCESS or worker_status == status
            )
            if worker_authoritative:
                if worker_status != status:
                    raise ValueError("worker status disagrees with attempt status")
                if process_returncode != exit_code_for_status(status):
                    raise ValueError("worker process return code disagrees with attempt status")
                expected_event = (
                    "WORKER_FAILED"
                    if classify_status(status) is StatusClassification.OPERATIONAL_ERROR
                    else "WORKER_FINISHED"
                )
                if worker_result.get("event") != expected_event:
                    raise ValueError("worker result event disagrees with attempt status")
        elif classify_status(status) is StatusClassification.SUCCESS:
            raise ValueError("a successful attempt must carry an authenticated worker result")
    except (
        OSError,
        TypeError,
        ValueError,
        EnvelopeValidationError,
        HashChainValidationError,
    ) as error:
        raise AttemptHistoryError(f"{attempt_path}: {error}") from error


def load_attempt_history(attempts_root: Path) -> AttemptHistory:
    """Load all attempts, failing closed on malformed or partially bound records."""

    if not attempts_root.exists():
        return AttemptHistory(0.0, 0, 0, frozenset(), frozenset(), frozenset(), ())
    aggregate = 0.0
    complete = 0
    incomplete = 0
    timed_out: set[str] = set()
    incomplete_fingerprints: set[str] = set()
    unsafe_termination_fingerprints: set[str] = set()
    status_counter: Counter[str] = Counter()
    for fingerprint_directory in sorted(attempts_root.iterdir()):
        if not fingerprint_directory.is_dir() or fingerprint_directory.name.startswith("."):
            continue
        fingerprint = _require_sha256(
            fingerprint_directory.name, label="attempt history fingerprint directory"
        )
        for attempt_path in sorted(fingerprint_directory.iterdir()):
            if not attempt_path.is_dir() or attempt_path.name.startswith("."):
                continue
            attempt_id = attempt_path.name
            if _ATTEMPT_ID_RE.fullmatch(attempt_id) is None:
                raise AttemptHistoryError(f"{attempt_path}: invalid attempt directory name")
            attempt_manifest = _validate_attempt_manifest(attempt_path, fingerprint, attempt_id)
            result_path = attempt_path / "result.json"
            if not result_path.is_file():
                incomplete += 1
                incomplete_fingerprints.add(fingerprint)
                continue
            result = _validate_attempt_result(result_path, fingerprint, attempt_id)
            _validate_production_attempt_bindings(attempt_path, attempt_manifest, result)
            aggregate += _validated_wall_time(
                result["wall_time_seconds"], label=f"{result_path} wall time"
            )
            status = result["status"]
            if not isinstance(status, str):  # validated above; keeps type narrowing local
                raise AttemptHistoryError(f"{result_path}: status must be a string")
            status_counter[status] += 1
            details = result["details"]
            terminal_status = (
                details.get("terminal_attempt_status") if isinstance(details, Mapping) else None
            )
            authenticated_statuses = {status}
            if isinstance(terminal_status, str):
                authenticated_statuses.add(terminal_status)
            if "TIMEOUT" in authenticated_statuses:
                timed_out.add(fingerprint)
            if authenticated_statuses & UNSAFE_TERMINATION_STATUSES:
                unsafe_termination_fingerprints.add(fingerprint)
            complete += 1
    return AttemptHistory(
        aggregate_wall_time_seconds=aggregate,
        completed_attempt_count=complete,
        incomplete_attempt_count=incomplete,
        timed_out_fingerprints=frozenset(timed_out),
        incomplete_fingerprints=frozenset(incomplete_fingerprints),
        unsafe_termination_fingerprints=frozenset(unsafe_termination_fingerprints),
        status_counts=tuple(sorted(status_counter.items())),
    )


@dataclass(frozen=True, slots=True)
class AttemptPermission:
    allowed: bool
    reason: str | None
    aggregate_wall_time_seconds: float
    remaining_wall_time_seconds: float
    effective_timeout_seconds: int | None


def evaluate_attempt_permission(
    attempts_root: Path,
    *,
    budget: CampaignBudget,
    fingerprint_sha256: str,
    current_campaign_elapsed_seconds: int | float = 0,
    finalization_reserve_seconds: int | float = 0,
) -> AttemptPermission:
    """Apply single-worker recovery, timeout replay, and aggregate-budget gates."""

    fingerprint = _require_sha256(fingerprint_sha256, label="attempt fingerprint")
    current_elapsed = _validated_wall_time(
        current_campaign_elapsed_seconds,
        label="current_campaign_elapsed_seconds",
    )
    finalization_reserve = _validated_wall_time(
        finalization_reserve_seconds,
        label="finalization_reserve_seconds",
    )
    history = load_attempt_history(attempts_root)
    remaining = max(
        0.0,
        budget.total_wall_time_seconds - history.aggregate_wall_time_seconds - current_elapsed,
    )
    if history.incomplete_attempt_count:
        return AttemptPermission(
            False,
            "INCOMPLETE_ATTEMPT_REQUIRES_RECOVERY",
            history.aggregate_wall_time_seconds,
            remaining,
            None,
        )
    if history.unsafe_termination_fingerprints:
        return AttemptPermission(
            False,
            "UNSAFE_TERMINATION_REQUIRES_RECOVERY",
            history.aggregate_wall_time_seconds,
            remaining,
            None,
        )
    if fingerprint in history.timed_out_fingerprints:
        return AttemptPermission(
            False,
            "SAME_FINGERPRINT_TIMEOUT_RETRY_FORBIDDEN",
            history.aggregate_wall_time_seconds,
            remaining,
            None,
        )
    effective_timeout = min(
        budget.timeout_seconds_per_chart,
        math.floor(max(0.0, remaining - finalization_reserve)),
    )
    if effective_timeout < 1:
        return AttemptPermission(
            False,
            "TOTAL_WALL_TIME_BUDGET_EXHAUSTED",
            history.aggregate_wall_time_seconds,
            remaining,
            None,
        )
    return AttemptPermission(
        True,
        None,
        history.aggregate_wall_time_seconds,
        remaining,
        effective_timeout,
    )
