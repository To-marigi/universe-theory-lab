"""Isolated Sage worker for bounded SR2-V auxiliary-ideal stages.

The legacy solver embeds a large program in ``sage -c`` and materialises every
generator before its first subset stage.  This worker is a normal
``sage -python`` module.  It authenticates the frozen root and every arena
chunk, parses only the polynomial records needed by the requested stage, and
supports the native-saturation pilot without the 1,494-term Rabinowitsch
equation.

The module intentionally contains no host-side Docker lifecycle code.  Its
stdout is an LF-delimited stream of canonical JSON messages; a supervisor can
persist those messages while the calculation is still running.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import time
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

_resource: Any = None
try:
    _resource = __import__("resource")
except ImportError:  # pragma: no cover - exercised by host-side Windows imports
    pass

REQUEST_ENVELOPE_SCHEMA: Final = "sr2v-q5-free-recipe-envelope-v1"
REQUEST_SCHEMA: Final = "sr2v-q5-free-stage-request-v3"
WORKER_MESSAGE_SCHEMA: Final = "sr2v-q5-free-worker-message-v1"
DETERMINANTAL_METHOD: Final = "determinantal_cegar_v1"
DETERMINANTAL_INVENTORY_METHOD: Final = "determinantal_inventory_v1"
DETERMINANTAL_METHODS: Final = frozenset({DETERMINANTAL_METHOD, DETERMINANTAL_INVENTORY_METHOD})
DETERMINANTAL_POLICY_SCHEMA: Final = "sr2v-determinantal-cegar-policy-v1"
FROZEN_ROOT_VERDICT: Final = (
    "SR2V_Q5_FREE_AUXILIARY_IDEAL_FULL_MANIFEST_DIGEST_AND_SOLVER_INPUTS_FROZEN_NO_SOLVER_RUN"
)
NON_ALIGNED_CHARTS: Final = frozenset({"U2", "U3", "U4"})
METHODS: Final = frozenset(
    {
        "build_only",
        *DETERMINANTAL_METHODS,
        "incremental_native_saturation",
        "libsingular_ab_saturation",
        "libsingular_system_saturation",
        "native_saturation",
        "redundancy_audit",
    }
)
MONOMIAL_ORDERS: Final = frozenset({"degrevlex", "negdeglex", "deglex", "lex"})
GROEBNER_ALGORITHMS: Final = frozenset({"libsingular:slimgb", "libsingular:std"})
FACTOR_GROUPS: Final = frozenset({"chart", "bottom", "torus"})

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_POLYNOMIAL_HEADER_RE = re.compile(
    rb'^\{"polynomial_id":([0-9]+),"sha256":"([0-9a-f]{64})",'
    rb'"term_count":([0-9]+),"terms":'
)


class WorkerInputError(RuntimeError):
    """The request or frozen input failed a fail-closed validation gate."""


def canonical_json_bytes(value: object) -> bytes:
    """Return the repository's compact, key-sorted canonical JSON bytes."""

    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def semantic_digest(payload: Mapping[str, object]) -> str:
    """Recompute a self-bound JSON artifact's semantic digest."""

    return canonical_sha256(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def worker_source_sha256(path: Path | None = None) -> str:
    return hashlib.sha256((path or Path(__file__)).read_bytes()).hexdigest()


def _require_exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise WorkerInputError(
            f"{label} keys disagree with the contract; "
            f"missing={sorted(expected - actual)}, unsupported={sorted(actual - expected)}"
        )


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise WorkerInputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_positive_int(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise WorkerInputError(f"{label} must be a positive integer")
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkerInputError(f"{label} must be a non-negative integer")
    return value


def determinantal_prefix_sizes(candidate_count: int) -> list[int]:
    """Return deterministic 1/2/4/... escalation boundaries including the full set."""

    if type(candidate_count) is not int or candidate_count < 0:
        raise ValueError("candidate_count must be a non-negative integer")
    if candidate_count == 0:
        return []
    sizes: list[int] = []
    boundary = 1
    while boundary < candidate_count:
        sizes.append(boundary)
        boundary *= 2
    sizes.append(candidate_count)
    return sizes


def determinantal_pair_schedule(
    component_term_counts: Sequence[tuple[int, int]],
) -> list[dict[str, int]]:
    """Order pair minors by a cheapest-row pivot star, then by product-cost bound."""

    if len(component_term_counts) < 2:
        return []
    if any(
        type(a_terms) is not int or type(b_terms) is not int or a_terms < 0 or b_terms < 0
        for a_terms, b_terms in component_term_counts
    ):
        raise ValueError("component term counts must be non-negative integers")
    pivot = min(
        range(len(component_term_counts)),
        key=lambda index: (sum(component_term_counts[index]), index),
    )
    records: list[dict[str, int]] = []
    for left in range(len(component_term_counts)):
        for right in range(left + 1, len(component_term_counts)):
            left_a, left_b = component_term_counts[left]
            right_a, right_b = component_term_counts[right]
            records.append(
                {
                    "cost_upper_bound": left_a * right_b + right_a * left_b,
                    "left_index": left,
                    "pivot_star_priority": 0 if pivot in {left, right} else 1,
                    "right_index": right,
                }
            )
    return sorted(
        records,
        key=lambda record: (
            record["pivot_star_priority"],
            record["cost_upper_bound"],
            record["left_index"],
            record["right_index"],
        ),
    )


def load_verified_request(path: Path) -> dict[str, Any]:
    """Load the canonical recipe envelope and strictly validate its stage request."""

    raw_bytes = path.read_bytes()
    if not raw_bytes.endswith(b"\n") or raw_bytes.endswith(b"\r\n"):
        raise WorkerInputError("request envelope must have one LF-terminated canonical JSON line")
    envelope = json.loads(raw_bytes)
    if not isinstance(envelope, dict):
        raise WorkerInputError("request envelope must be a JSON object")
    if raw_bytes != canonical_json_bytes(envelope) + b"\n":
        raise WorkerInputError("request envelope is not canonical JSON")
    _require_exact_keys(
        envelope,
        {"schema_version", "payload_digest_sha256", "payload"},
        "request envelope",
    )
    if envelope["schema_version"] != REQUEST_ENVELOPE_SCHEMA:
        raise WorkerInputError("unsupported request envelope schema")
    request = envelope["payload"]
    if not isinstance(request, dict):
        raise WorkerInputError("request envelope payload must be a JSON object")
    claimed = _require_sha256(envelope["payload_digest_sha256"], "request payload digest")
    if canonical_sha256(request) != claimed:
        raise WorkerInputError("request payload digest mismatch")
    validate_request(request)
    return request


def validate_request(request: Mapping[str, object]) -> None:
    """Validate all non-Sage parts of one immutable stage request."""

    expected = {
        "bottom_factor_records",
        "chart",
        "chart_factor_polynomial_id",
        "chart_factor_sha256",
        "determinantal_policy",
        "expected_root_semantic_digest_sha256",
        "expected_worker_source_sha256",
        "factor_group_order",
        "groebner_algorithm",
        "incremental_batch_sizes",
        "max_live_basis_terms",
        "max_loaded_terms",
        "memory_limit_bytes",
        "method",
        "modulus",
        "monomial_order",
        "root_manifest_path",
        "schema_version",
        "selected_entry_indices",
        "selected_generator_rows_sha256",
        "soft_rss_limit_bytes",
        "stage_plan_sha256",
    }
    _require_exact_keys(request, expected, "stage request")
    if request["schema_version"] != REQUEST_SCHEMA:
        raise WorkerInputError("unsupported stage request schema")
    chart = request["chart"]
    if chart not in NON_ALIGNED_CHARTS:
        raise WorkerInputError("this worker revision permits only non-aligned U2/U3/U4 stages")
    method = request["method"]
    if method not in METHODS:
        raise WorkerInputError(f"unsupported worker method: {method!r}")
    if request["monomial_order"] not in MONOMIAL_ORDERS:
        raise WorkerInputError("unsupported monomial order")
    if request["groebner_algorithm"] not in GROEBNER_ALGORITHMS:
        raise WorkerInputError("unsupported Groebner algorithm")
    modulus = _require_nonnegative_int(request["modulus"], "modulus")
    if modulus == 1:
        raise WorkerInputError("modulus must be zero (QQ) or a prime greater than one")
    _require_nonnegative_int(request["chart_factor_polynomial_id"], "chart factor id")
    _require_sha256(request["chart_factor_sha256"], "chart factor digest")
    _require_sha256(request["expected_root_semantic_digest_sha256"], "root digest")
    _require_sha256(request["expected_worker_source_sha256"], "worker digest")
    _require_sha256(request["selected_generator_rows_sha256"], "selected rows digest")
    _require_sha256(request["stage_plan_sha256"], "stage-plan digest")
    limits = {
        key: _require_positive_int(request[key], key)
        for key in (
            "max_live_basis_terms",
            "max_loaded_terms",
            "memory_limit_bytes",
            "soft_rss_limit_bytes",
        )
    }
    if limits["soft_rss_limit_bytes"] >= limits["memory_limit_bytes"]:
        raise WorkerInputError("soft RSS limit must be below the hard memory limit")
    path = request["root_manifest_path"]
    if not isinstance(path, str) or not path or Path(path).is_absolute():
        raise WorkerInputError("root_manifest_path must be a non-empty repository-relative path")
    if ".." in Path(path).parts:
        raise WorkerInputError("root_manifest_path may not escape the repository")
    indices = request["selected_entry_indices"]
    if not isinstance(indices, list) or not indices:
        raise WorkerInputError("selected_entry_indices must be a non-empty list")
    if any(type(index) is not int or index < 0 for index in indices):
        raise WorkerInputError("selected_entry_indices must contain non-negative integers")
    if len(indices) != len(set(indices)):
        raise WorkerInputError("selected_entry_indices contains duplicates")
    raw_batch_sizes = request["incremental_batch_sizes"]
    if not isinstance(raw_batch_sizes, list) or not raw_batch_sizes:
        raise WorkerInputError("incremental_batch_sizes must be a non-empty list")
    if any(type(size) is not int or size <= 0 for size in raw_batch_sizes):
        raise WorkerInputError("incremental batch sizes must be positive integers")
    batch_sizes = [int(size) for size in raw_batch_sizes]
    if batch_sizes != sorted(set(batch_sizes)) or batch_sizes[-1] != len(indices):
        raise WorkerInputError(
            "incremental batch sizes must increase strictly and end at the selected row count"
        )
    if method != "incremental_native_saturation" and batch_sizes != [len(indices)]:
        raise WorkerInputError("non-incremental methods require one full-size batch")
    records = request["bottom_factor_records"]
    if not isinstance(records, list) or len(records) != 14:
        raise WorkerInputError("exactly fourteen bottom localization factors are required")
    group_order = request["factor_group_order"]
    if (
        not isinstance(group_order, list)
        or len(group_order) != 3
        or set(group_order) != FACTOR_GROUPS
    ):
        raise WorkerInputError("factor_group_order must be a permutation of chart/bottom/torus")
    _validate_determinantal_policy(request)


def _validate_determinantal_policy(request: Mapping[str, object]) -> None:
    policy = request["determinantal_policy"]
    if request["method"] not in DETERMINANTAL_METHODS:
        if policy is not None:
            raise WorkerInputError("non-determinantal methods require a null determinantal policy")
        return
    if not isinstance(policy, Mapping):
        raise WorkerInputError("the determinantal method requires a policy object")
    expected = {
        "certificate_requirement",
        "coefficient_scope",
        "max_certificate_bytes",
        "max_certificate_terms",
        "max_generated_minor_terms",
        "max_minor_count",
        "max_rounds",
        "minor_pair_policy",
        "radical_target_policy",
        "row_universe_sha256",
        "schema_version",
        "selected_entry_indices_sha256",
        "semantic_digest_sha256",
        "task_kind",
        "verification_mode",
    }
    _require_exact_keys(policy, expected, "determinantal policy")
    if policy["schema_version"] != DETERMINANTAL_POLICY_SCHEMA:
        raise WorkerInputError("unsupported determinantal policy schema")
    if semantic_digest(policy) != policy["semantic_digest_sha256"]:
        raise WorkerInputError("determinantal policy semantic digest mismatch")
    _require_sha256(policy["row_universe_sha256"], "determinantal row-universe digest")
    _require_sha256(
        policy["selected_entry_indices_sha256"],
        "determinantal selected-entry digest",
    )
    for key in (
        "max_certificate_bytes",
        "max_certificate_terms",
        "max_generated_minor_terms",
        "max_minor_count",
        "max_rounds",
    ):
        _require_positive_int(policy[key], f"determinantal {key}")
    if policy["minor_pair_policy"] != "CHEAPEST_PIVOT_STAR_THEN_COST_PREFIXES_1_2_4":
        raise WorkerInputError("unsupported determinantal minor-pair policy")
    if policy["radical_target_policy"] != "ALL_EFFECTIVE_SELECTED_A_COMPONENTS":
        raise WorkerInputError("unsupported determinantal radical-target policy")
    if policy["certificate_requirement"] != "EXACT_EXPONENT_MEMBERSHIP_DIRECT_LIFT_PENDING":
        raise WorkerInputError("unsupported determinantal certificate requirement")
    if policy["verification_mode"] != "LIBSINGULAR_SAT_WITH_EXP_AND_CONTAINMENT":
        raise WorkerInputError("unsupported determinantal verification mode")
    expected_task = (
        "INVENTORY_ONLY"
        if request["method"] == DETERMINANTAL_INVENTORY_METHOD
        else "COMBINED_SUBSET_CERTIFICATE"
    )
    if policy["task_kind"] != expected_task:
        raise WorkerInputError("determinantal task kind disagrees with the method")
    expected_scope = "QQ_EXACT_CANDIDATE" if request["modulus"] == 0 else "FINITE_FIELD_SCOUT_ONLY"
    if policy["coefficient_scope"] != expected_scope:
        raise WorkerInputError("determinantal coefficient scope disagrees with the modulus")
    if policy["selected_entry_indices_sha256"] != canonical_sha256(
        request["selected_entry_indices"]
    ):
        raise WorkerInputError("determinantal selected-entry digest disagrees with the request")


def _safe_repository_path(repository_root: Path, relative: str) -> Path:
    root = repository_root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise WorkerInputError(f"path escapes repository root: {relative}") from error
    return candidate


def load_verified_root(repository_root: Path, request: Mapping[str, object]) -> dict[str, Any]:
    root_path = _safe_repository_path(repository_root, str(request["root_manifest_path"]))
    root = json.loads(root_path.read_text(encoding="utf-8"))
    if not isinstance(root, dict):
        raise WorkerInputError("bundle root must be a JSON object")
    observed = semantic_digest(root)
    expected = str(request["expected_root_semantic_digest_sha256"])
    if observed != expected or root.get("semantic_digest_sha256") != expected:
        raise WorkerInputError("bundle-root semantic digest mismatch")
    if root.get("verdict") != FROZEN_ROOT_VERDICT or root.get("passed") is not True:
        raise WorkerInputError("bundle root is not the verified frozen solver-input artifact")
    ledger = root.get("chunk_ledger")
    if not isinstance(ledger, dict) or not isinstance(ledger.get("chunks"), list):
        raise WorkerInputError("bundle root has no usable chunk ledger")
    if canonical_sha256(ledger["chunks"]) != ledger.get("chunk_ledger_digest_sha256"):
        raise WorkerInputError("chunk-ledger digest mismatch")
    return root


def selected_generator_rows(
    root: Mapping[str, Any], request: Mapping[str, object]
) -> list[list[int]]:
    """Derive selected row records directly from the authenticated root."""

    chart = root["chart_generator_ids"]["charts"][str(request["chart"])]
    entries = chart["generator_polynomial_ids"]
    rows: list[list[int]] = []
    seen_coefficients: set[tuple[int, int]] = set()
    raw_indices = request["selected_entry_indices"]
    if not isinstance(raw_indices, list):
        raise WorkerInputError("selected_entry_indices must be a list")
    for index in raw_indices:
        if not isinstance(index, int) or index >= len(entries):
            raise WorkerInputError(f"selected generator entry is out of range: {index}")
        entry = entries[index]
        if not isinstance(entry, list) or len(entry) != 3:
            raise WorkerInputError("non-aligned generator row must be [source,A_id,B_id]")
        row = [int(value) for value in entry]
        if row[0] != index:
            raise WorkerInputError("generator source index no longer matches its entry index")
        coefficients = (row[1], row[2])
        if coefficients == (0, 0):
            raise WorkerInputError("stage plan selected a zero generator")
        if coefficients in seen_coefficients:
            raise WorkerInputError("stage plan selected duplicate generators")
        seen_coefficients.add(coefficients)
        rows.append(row)
    if canonical_sha256(rows) != request["selected_generator_rows_sha256"]:
        raise WorkerInputError("selected generator rows disagree with the stage request")
    return rows


def _stream_sha256(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


class Emitter:
    """Canonical JSON progress stream with elapsed time and process RSS."""

    def __init__(self) -> None:
        self.started = time.monotonic()

    def emit(self, message_type: str, event: str, **fields: object) -> None:
        usage = None if _resource is None else _resource.getrusage(_resource.RUSAGE_SELF)
        payload = {
            "elapsed_seconds": time.monotonic() - self.started,
            "event": event,
            "message_type": message_type,
            "ru_maxrss_kib": 0 if usage is None else int(usage.ru_maxrss),
            "ru_stime_seconds": 0.0 if usage is None else float(usage.ru_stime),
            "ru_utime_seconds": 0.0 if usage is None else float(usage.ru_utime),
            "schema_version": WORKER_MESSAGE_SCHEMA,
            **fields,
        }
        sys.stdout.buffer.write(canonical_json_bytes(payload) + b"\n")
        sys.stdout.buffer.flush()


def _scan_needed_records(
    repository_root: Path,
    root: Mapping[str, Any],
    needed: set[int],
    emitter: Emitter,
) -> tuple[dict[int, dict[str, Any]], int]:
    """Authenticate all polynomial chunks but JSON-decode only needed records."""

    ledger = root["chunk_ledger"]
    directory = _safe_repository_path(repository_root, str(ledger["directory"]))
    chunks = [record for record in ledger["chunks"] if record["arena"] == "polynomial_arena"]
    arena = root["arena_index"]["polynomial_arena"]
    correspondence = arena["polynomial_id_to_sha256"]
    if canonical_sha256(correspondence) != arena["polynomial_id_to_sha256_digest_sha256"]:
        raise WorkerInputError("polynomial arena identifier ledger digest mismatch")
    expected_by_id = {int(identifier): str(digest) for identifier, digest in correspondence}

    found: dict[int, dict[str, Any]] = {}
    loaded_terms = 0
    scanned_records = 0
    for chunk_number, chunk in enumerate(chunks):
        path = _safe_repository_path(directory, str(chunk["path"]))
        compressed_bytes, compressed_sha256 = _stream_sha256(path)
        if compressed_bytes != int(chunk["gzip_bytes"]):
            raise WorkerInputError(f"{chunk['path']}: gzip byte count mismatch")
        if compressed_sha256 != chunk["gzip_sha256"]:
            raise WorkerInputError(f"{chunk['path']}: gzip digest mismatch")

        raw_digest = hashlib.sha256()
        raw_bytes = 0
        seen_in_chunk = 0
        with gzip.open(path, "rb") as handle:
            for line in handle:
                raw_digest.update(line)
                raw_bytes += len(line)
                seen_in_chunk += 1
                match = _POLYNOMIAL_HEADER_RE.match(line)
                if match is None or not line.endswith(b"}\n"):
                    raise WorkerInputError(f"{chunk['path']}: noncanonical polynomial record")
                identifier = int(match.group(1))
                record_sha256 = match.group(2).decode("ascii")
                term_count = int(match.group(3))
                if expected_by_id.get(identifier) != record_sha256:
                    raise WorkerInputError(
                        f"{chunk['path']}: polynomial identifier/digest ledger mismatch"
                    )
                if identifier in needed:
                    if identifier in found:
                        raise WorkerInputError(f"duplicate needed polynomial id: {identifier}")
                    terms_bytes = line[match.end() : -2]
                    if hashlib.sha256(terms_bytes).hexdigest() != record_sha256:
                        raise WorkerInputError(f"polynomial {identifier}: term digest mismatch")
                    record = json.loads(line)
                    if term_count != len(record["terms"]):
                        raise WorkerInputError(f"polynomial {identifier}: term count mismatch")
                    found[identifier] = record
                    loaded_terms += term_count
                scanned_records += 1
        if seen_in_chunk != int(chunk["record_count"]):
            raise WorkerInputError(f"{chunk['path']}: record count mismatch")
        if raw_bytes != int(chunk["uncompressed_bytes"]):
            raise WorkerInputError(f"{chunk['path']}: uncompressed byte count mismatch")
        if raw_digest.hexdigest() != chunk["uncompressed_sha256"]:
            raise WorkerInputError(f"{chunk['path']}: uncompressed digest mismatch")
        emitter.emit(
            "progress",
            "CHUNK_VERIFIED",
            chunk_index=chunk_number,
            chunks_total=len(chunks),
            loaded_polynomials=len(found),
            loaded_terms=loaded_terms,
            needed_polynomials=len(needed),
            scanned_records=scanned_records,
        )
    missing = sorted(needed - set(found))
    if missing:
        raise WorkerInputError(f"polynomial arena is missing requested ids: {missing[:16]}")
    return found, loaded_terms


def _materialize_polynomial(record: Mapping[str, Any], ring: Any, field: Any, width: int) -> Any:
    coefficients: dict[tuple[int, ...], Any] = {}
    for exponent_pairs, numerator, denominator in record["terms"]:
        exponent = [0] * width
        for raw_index, raw_power in exponent_pairs:
            index = int(raw_index)
            if index >= width:
                raise WorkerInputError("arena exponent exceeds the worker ring width")
            exponent[index] = int(raw_power)
        denominator_value = field(int(denominator))
        if not denominator_value:
            raise WorkerInputError("chosen modulus annihilates an arena denominator")
        coefficients[tuple(exponent)] = field(int(numerator)) / denominator_value
    return ring(coefficients)


def _bottom_factor_polynomial(record: Mapping[str, Any], ring: Any, field: Any, width: int) -> Any:
    synthetic = {"terms": record["polynomial"]}
    return _materialize_polynomial(synthetic, ring, field, width)


def _unit_associate_ratio(left: Any, right: Any) -> Any | None:
    """Return the ground-unit ratio when two nonzero polynomials are associates."""

    if not left or not right or left.parent() is not right.parent():
        return None
    ratio = left.lc() / right.lc()
    return ratio if left == ratio * right else None


def _exact_quotient(numerator: Any, denominator: Any) -> Any | None:
    if not denominator:
        return None
    quotient, remainder = numerator.quo_rem(denominator)
    return quotient if not remainder else None


def _common_pair_multiplier(kept: Sequence[Any], candidate: Sequence[Any]) -> Any | None:
    multiplier: Any | None = None
    for kept_component, candidate_component in zip(kept, candidate, strict=True):
        if not kept_component:
            if candidate_component:
                return None
            continue
        quotient = _exact_quotient(candidate_component, kept_component)
        if quotient is None:
            return None
        if multiplier is None:
            multiplier = quotient
        elif multiplier != quotient:
            return None
    if multiplier is None or not multiplier:
        return None
    return (
        multiplier
        if all(
            candidate_component == multiplier * kept_component
            for kept_component, candidate_component in zip(kept, candidate, strict=True)
        )
        else None
    )


def _polynomial_certificate(polynomial: Any) -> dict[str, Any]:
    terms: list[Any] = []

    def exponent_tuple(raw: Any) -> tuple[int, ...]:
        return (int(raw),) if type(raw) is int else tuple(int(power) for power in raw)

    for raw_exponent, coefficient in sorted(
        polynomial.dict().items(), key=lambda item: exponent_tuple(item[0])
    ):
        exponent = exponent_tuple(raw_exponent)
        try:
            numerator = int(coefficient.numerator())
            denominator = int(coefficient.denominator())
        except AttributeError:
            numerator = int(coefficient)
            denominator = 1
        exponent_pairs = [[index, int(power)] for index, power in enumerate(exponent) if power]
        terms.append([exponent_pairs, numerator, denominator])
    return {
        "sha256": canonical_sha256(terms),
        "term_count": len(terms),
        "terms": terms,
    }


def _raw_redundancy_relations(
    rows: Sequence[Sequence[int]],
    generator_pairs: Sequence[Sequence[Any]],
) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for left_index in range(len(rows)):
        for right_index in range(left_index + 1, len(rows)):
            directions = ((left_index, right_index), (right_index, left_index))
            for kept_index, redundant_index in directions:
                multiplier = _common_pair_multiplier(
                    generator_pairs[kept_index], generator_pairs[redundant_index]
                )
                if multiplier is None:
                    continue
                certificate = _polynomial_certificate(multiplier)
                core = {
                    "kept_row": list(rows[kept_index]),
                    "kept_stage_index": kept_index,
                    "multiplier": certificate,
                    "multiplier_is_ground_unit": bool(multiplier.is_unit()),
                    "redundant_row": list(rows[redundant_index]),
                    "redundant_stage_index": redundant_index,
                }
                core["relation_sha256"] = canonical_sha256(core)
                relations.append(core)
                break
    return relations


def _deduplicate_ground_unit_pairs(
    rows: Sequence[Sequence[int]],
    generator_pairs: Sequence[Sequence[Any]],
) -> tuple[list[int], list[dict[str, Any]]]:
    """Keep one representative of each pair related by a ground-ring unit."""

    representative_indices: list[int] = []
    relations: list[dict[str, Any]] = []
    for candidate_index, candidate in enumerate(generator_pairs):
        for representative_index in representative_indices:
            multiplier = _common_pair_multiplier(generator_pairs[representative_index], candidate)
            if multiplier is None or not bool(multiplier.is_unit()):
                continue
            multiplier_certificate = _polynomial_certificate(multiplier)
            core = {
                "kept_row": list(rows[representative_index]),
                "kept_stage_index": representative_index,
                "multiplier": multiplier_certificate,
                "redundant_row": list(rows[candidate_index]),
                "redundant_stage_index": candidate_index,
            }
            core["relation_sha256"] = canonical_sha256(core)
            relations.append(core)
            break
        else:
            representative_indices.append(candidate_index)
    return representative_indices, relations


def _polynomial_digest_record(polynomial: Any) -> dict[str, Any]:
    certificate = _polynomial_certificate(polynomial)
    return {
        "sha256": certificate["sha256"],
        "term_count": certificate["term_count"],
    }


def _determinantal_minor_candidates(
    rows: Sequence[Sequence[int]],
    generator_pairs: Sequence[Sequence[Any]],
    representative_indices: Sequence[int],
    *,
    max_generated_minor_terms: int,
) -> tuple[
    list[tuple[Any, dict[str, Any]]],
    list[dict[str, Any]],
    dict[str, Any] | None,
]:
    """Build a cost-ordered pivot-star prefix and discard zero/unit-associate minors."""

    effective_pairs = [generator_pairs[index] for index in representative_indices]
    component_counts = [
        (
            int(pair[0].number_of_terms()),
            int(pair[1].number_of_terms()),
        )
        for pair in effective_pairs
    ]
    kept: list[tuple[Any, dict[str, Any]]] = []
    discarded: list[dict[str, Any]] = []
    generated_cost_upper_bound = 0
    for schedule_index, schedule in enumerate(determinantal_pair_schedule(component_counts)):
        projected_cost_upper_bound = generated_cost_upper_bound + schedule["cost_upper_bound"]
        if projected_cost_upper_bound > max_generated_minor_terms:
            return (
                kept,
                discarded,
                {
                    "generated_minor_cost_upper_bound": generated_cost_upper_bound,
                    "max_generated_minor_terms": max_generated_minor_terms,
                    "next_minor_cost_upper_bound": schedule["cost_upper_bound"],
                    "next_schedule_index": schedule_index,
                    "projected_generated_minor_cost_upper_bound": projected_cost_upper_bound,
                    "reason": "MAX_GENERATED_MINOR_TERM_COST_BOUND_EXCEEDED",
                },
            )
        generated_cost_upper_bound = projected_cost_upper_bound
        left_effective = schedule["left_index"]
        right_effective = schedule["right_index"]
        left_stage = int(representative_indices[left_effective])
        right_stage = int(representative_indices[right_effective])
        left_a, left_b = generator_pairs[left_stage]
        right_a, right_b = generator_pairs[right_stage]
        minor = left_a * right_b - right_a * left_b
        identity = {
            "cost_upper_bound": schedule["cost_upper_bound"],
            "left_effective_index": left_effective,
            "left_row": list(rows[left_stage]),
            "left_stage_index": left_stage,
            "pivot_star_priority": schedule["pivot_star_priority"],
            "right_effective_index": right_effective,
            "right_row": list(rows[right_stage]),
            "right_stage_index": right_stage,
            "schedule_index": schedule_index,
        }
        if not minor:
            discarded.append({**identity, "reason": "ZERO_MINOR"})
            continue
        for kept_index, (kept_minor, _kept_record) in enumerate(kept):
            ratio = _unit_associate_ratio(minor, kept_minor)
            if ratio is None or not bool(ratio.is_unit()):
                continue
            discarded.append(
                {
                    **identity,
                    "kept_candidate_index": kept_index,
                    "reason": "GROUND_UNIT_ASSOCIATE_MINOR",
                    "unit_ratio": _polynomial_certificate(ratio),
                }
            )
            break
        else:
            record = {
                **identity,
                "candidate_index": len(kept),
                "minor": _polynomial_digest_record(minor),
            }
            record["candidate_sha256"] = canonical_sha256(record)
            kept.append((minor, record))
    return kept, discarded, None


def _basis_summary(basis: Sequence[Any]) -> dict[str, Any]:
    term_counts = [int(polynomial.number_of_terms()) for polynomial in basis]
    return {
        "basis_digest_sha256": canonical_sha256([str(polynomial) for polynomial in basis]),
        "basis_size": len(basis),
        "basis_term_count": sum(term_counts),
        "largest_basis_polynomial_terms": max(term_counts, default=0),
        "is_unit_ideal": bool(len(basis) == 1 and basis[0].is_unit()),
    }


def _basis_is_subset(left: Sequence[Any], right: Sequence[Any]) -> bool:
    divisors = list(right)
    return all(not polynomial.reduce(divisors) for polynomial in left)


def _saturate_standard_basis_by_factor(
    basis: Sequence[Any],
    factor: Any,
) -> tuple[Any, dict[str, Any]]:
    """Saturate a certified standard basis and verify the returned exponent witness."""

    from sage.libs.singular.function_factory import ff

    input_basis = basis
    started = time.monotonic()
    output_basis, raw_exponent = ff.elim__lib.sat_with_exp(
        input_basis,
        factor.parent().ideal([factor]),
        attributes={input_basis: {"isSB": 1}},
    )
    seconds = time.monotonic() - started
    exponent = int(raw_exponent)
    input_contained = _basis_is_subset(input_basis, output_basis)
    input_divisors = list(input_basis)
    exponent_certificate_verified = all(
        not (factor**exponent * polynomial).reduce(input_divisors) for polynomial in output_basis
    )
    if not (input_contained and exponent_certificate_verified):
        raise WorkerInputError("determinantal saturation failed exact containment verification")
    return output_basis, {
        "exponent_certificate_verified": True,
        "input_contained": True,
        "saturation_exponent": exponent,
        "seconds": seconds,
    }


def _localized_standard_basis(
    *,
    algorithm: str,
    emitter: Emitter,
    factors: Sequence[tuple[str, Any]],
    generators: Sequence[Any],
    max_live_basis_terms: int,
    phase: str,
    ring: Any,
) -> tuple[Any, dict[str, Any]]:
    """Compute and localize one ideal while retaining exact exponent certificates."""

    emitter.emit(
        "progress",
        "DETERMINANTAL_GROEBNER_STARTED",
        generator_count=len(generators),
        phase=phase,
    )
    started = time.monotonic()
    basis = ring.ideal(generators).groebner_basis(algorithm=algorithm)
    groebner_seconds = time.monotonic() - started
    summary = _basis_summary(basis)
    emitter.emit(
        "progress",
        "DETERMINANTAL_GROEBNER_COMPLETED",
        groebner_seconds=groebner_seconds,
        phase=phase,
        **summary,
    )
    trace: list[dict[str, Any]] = []
    saturation_seconds = 0.0
    limit_exceeded = summary["basis_term_count"] > max_live_basis_terms
    for factor_index, (factor_name, factor) in enumerate(factors):
        if limit_exceeded or summary["is_unit_ideal"]:
            break
        emitter.emit(
            "progress",
            "DETERMINANTAL_LOCALIZATION_STARTED",
            factor_index=factor_index,
            factor_name=factor_name,
            factor_terms=int(factor.number_of_terms()),
            phase=phase,
        )
        basis, certificate = _saturate_standard_basis_by_factor(basis, factor)
        saturation_seconds += float(certificate["seconds"])
        summary = _basis_summary(basis)
        record = {
            **certificate,
            "basis_size": summary["basis_size"],
            "basis_term_count": summary["basis_term_count"],
            "factor_index": factor_index,
            "factor_name": factor_name,
            "factor_terms": int(factor.number_of_terms()),
            "is_unit_ideal": summary["is_unit_ideal"],
        }
        trace.append(record)
        emitter.emit(
            "progress",
            "DETERMINANTAL_LOCALIZATION_COMPLETED",
            phase=phase,
            **record,
        )
        limit_exceeded = summary["basis_term_count"] > max_live_basis_terms
    return basis, {
        "groebner_seconds": groebner_seconds,
        "limit_exceeded": limit_exceeded,
        "localization_trace": trace,
        "saturation_seconds": saturation_seconds,
        **summary,
    }


def _run_determinantal_cegar(
    *,
    algorithm: str,
    common: Mapping[str, Any],
    emitter: Emitter,
    factors: Sequence[tuple[str, Any]],
    generator_pairs: Sequence[Sequence[Any]],
    max_live_basis_terms: int,
    policy: Mapping[str, Any],
    ring: Any,
    rows: Sequence[Sequence[int]],
) -> dict[str, Any]:
    """Run a subset-safe determinantal scout without constructing the full row universe."""

    representative_indices, row_relations = _deduplicate_ground_unit_pairs(rows, generator_pairs)
    effective_rows = [
        {
            "A": _polynomial_digest_record(generator_pairs[index][0]),
            "A_term_count": int(generator_pairs[index][0].number_of_terms()),
            "B": _polynomial_digest_record(generator_pairs[index][1]),
            "B_term_count": int(generator_pairs[index][1].number_of_terms()),
            "row": list(rows[index]),
            "stage_index": index,
        }
        for index in representative_indices
    ]
    possible_minor_count = len(representative_indices) * (len(representative_indices) - 1) // 2
    max_minor_count = int(policy["max_minor_count"])
    if possible_minor_count > max_minor_count:
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_DETERMINANTAL_MINOR_COUNT_EXCEEDED",
            "effective_row_count": len(effective_rows),
            "possible_minor_count": possible_minor_count,
            **common,
        }
    candidates, discarded_minors, minor_resource_limit = _determinantal_minor_candidates(
        rows,
        generator_pairs,
        representative_indices,
        max_generated_minor_terms=int(policy["max_generated_minor_terms"]),
    )
    generated_minor_terms = sum(int(record["minor"]["term_count"]) for _, record in candidates)
    if minor_resource_limit is not None:
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": minor_resource_limit["reason"],
            "discarded_minors": discarded_minors,
            "effective_row_count": len(effective_rows),
            "generated_minor_terms": generated_minor_terms,
            "minor_candidate_count": len(candidates),
            "minor_candidates": [record for _minor, record in candidates],
            "minor_resource_limit": minor_resource_limit,
            **common,
        }
    if generated_minor_terms > int(policy["max_generated_minor_terms"]):
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_GENERATED_MINOR_TERMS_EXCEEDED",
            "effective_row_count": len(effective_rows),
            "generated_minor_terms": generated_minor_terms,
            "minor_candidate_count": len(candidates),
            **common,
        }
    emitter.emit(
        "progress",
        "DETERMINANTAL_SUBSET_PLANNED",
        discarded_minor_count=len(discarded_minors),
        effective_row_count=len(effective_rows),
        generated_minor_terms=generated_minor_terms,
        minor_candidate_count=len(candidates),
        raw_selected_row_count=len(rows),
        row_unit_associate_relation_count=len(row_relations),
    )
    if policy["task_kind"] == "INVENTORY_ONLY":
        inventory_core = {
            "discarded_minors": discarded_minors,
            "effective_rows": effective_rows,
            "generated_minor_terms": generated_minor_terms,
            "minor_candidates": [record for _minor, record in candidates],
            "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
            "raw_selected_row_count": len(rows),
            "row_unit_associate_relations": row_relations,
        }
        return {
            "status": "DETERMINANTAL_INVENTORY_COMPLETED",
            "determinantal_inventory_schema": "sr2v-determinantal-inventory-v1",
            "discarded_minors": discarded_minors,
            "effective_row_count": len(effective_rows),
            "effective_rows": effective_rows,
            "generated_minor_terms": generated_minor_terms,
            "inventory_sha256": canonical_sha256(inventory_core),
            "minor_candidate_count": len(candidates),
            "minor_candidates": [record for _minor, record in candidates],
            "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
            "raw_selected_row_count": len(rows),
            "row_unit_associate_relations": row_relations,
            **common,
        }

    entry_generators = [
        component
        for index in representative_indices
        for component in generator_pairs[index]
        if component
    ]
    entry_basis, entry_computation = _localized_standard_basis(
        algorithm=algorithm,
        emitter=emitter,
        factors=factors,
        generators=entry_generators,
        max_live_basis_terms=max_live_basis_terms,
        phase="ENTRY_IDEAL_I1",
        ring=ring,
    )
    if entry_computation["limit_exceeded"]:
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_LIVE_BASIS_TERMS_EXCEEDED_IN_ENTRY_IDEAL",
            "entry_condition": entry_computation,
            "effective_rows": effective_rows,
            **common,
        }
    entry_unit = bool(entry_computation["is_unit_ideal"])
    boundaries = determinantal_prefix_sizes(len(candidates)) or [0]
    if len(boundaries) > int(policy["max_rounds"]):
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_DETERMINANTAL_ROUNDS_EXCEEDED",
            "planned_round_count": len(boundaries),
            **common,
        }

    prefix_trace: list[dict[str, Any]] = []
    conditions_certified = False
    for round_index, boundary in enumerate(boundaries):
        selected_candidates = candidates[:boundary]
        selected_minors = [minor for minor, _record in selected_candidates]
        emitter.emit(
            "progress",
            "DETERMINANTAL_ROUND_STARTED",
            minor_prefix_size=boundary,
            round_index=round_index,
        )
        if selected_minors:
            minor_basis, minor_computation = _localized_standard_basis(
                algorithm=algorithm,
                emitter=emitter,
                factors=factors,
                generators=selected_minors,
                max_live_basis_terms=max_live_basis_terms,
                phase=f"MINOR_PREFIX_{boundary}",
                ring=ring,
            )
        else:
            minor_basis = ()
            minor_computation = {
                "basis_digest_sha256": canonical_sha256([]),
                "basis_size": 0,
                "basis_term_count": 0,
                "groebner_seconds": 0.0,
                "is_unit_ideal": False,
                "largest_basis_polynomial_terms": 0,
                "limit_exceeded": False,
                "localization_trace": [],
                "saturation_seconds": 0.0,
                "zero_ideal_preserved_by_nonzero_localization": True,
            }
        if minor_computation["limit_exceeded"]:
            return {
                "status": "SOFT_RESOURCE_LIMIT",
                "reason": "MAX_LIVE_BASIS_TERMS_EXCEEDED_IN_MINOR_IDEAL",
                "entry_condition": entry_computation,
                "minor_prefix_trace": prefix_trace,
                "partial_minor_condition": minor_computation,
                **common,
            }
        radical_targets: list[dict[str, Any]] = []
        for effective_index, stage_index in enumerate(representative_indices):
            target = generator_pairs[stage_index][0]
            target_record: dict[str, Any] = {
                "A": _polynomial_digest_record(target),
                "effective_index": effective_index,
                "row": list(rows[stage_index]),
                "stage_index": stage_index,
            }
            if not target:
                target_record.update(
                    {
                        "membership_reason": "ZERO_TARGET",
                        "radical_membership_verified": True,
                        "saturation_exponent": 1,
                    }
                )
            elif minor_computation["is_unit_ideal"]:
                target_record.update(
                    {
                        "membership_reason": "MINOR_IDEAL_IS_UNIT",
                        "radical_membership_verified": True,
                        "saturation_exponent": 0,
                    }
                )
            elif not minor_basis:
                target_record.update(
                    {
                        "membership_reason": "NONZERO_TARGET_AGAINST_ZERO_MINOR_IDEAL",
                        "radical_membership_verified": False,
                        "saturation_exponent": None,
                    }
                )
            else:
                emitter.emit(
                    "progress",
                    "DETERMINANTAL_RADICAL_CHECK_STARTED",
                    effective_index=effective_index,
                    minor_prefix_size=boundary,
                    round_index=round_index,
                    stage_index=stage_index,
                )
                saturated, saturation_certificate = _saturate_standard_basis_by_factor(
                    minor_basis, target
                )
                saturation_summary = _basis_summary(saturated)
                target_record.update(
                    {
                        **saturation_certificate,
                        "membership_reason": "SATURATION_BY_TARGET",
                        "radical_membership_verified": saturation_summary["is_unit_ideal"],
                        "saturated_basis_digest_sha256": saturation_summary["basis_digest_sha256"],
                        "saturated_basis_size": saturation_summary["basis_size"],
                        "saturated_basis_term_count": saturation_summary["basis_term_count"],
                    }
                )
                emitter.emit(
                    "progress",
                    "DETERMINANTAL_RADICAL_CHECK_COMPLETED",
                    minor_prefix_size=boundary,
                    round_index=round_index,
                    **target_record,
                )
            radical_targets.append(target_record)
        all_targets_verified = all(
            bool(target["radical_membership_verified"]) for target in radical_targets
        )
        round_certified = entry_unit and all_targets_verified
        round_record = {
            "all_radical_targets_verified": all_targets_verified,
            "entry_ideal_is_unit": entry_unit,
            "minor_condition": minor_computation,
            "minor_prefix_candidate_sha256": canonical_sha256(
                [record["candidate_sha256"] for _minor, record in selected_candidates]
            ),
            "minor_prefix_size": boundary,
            "radical_targets": radical_targets,
            "round_certified": round_certified,
            "round_index": round_index,
        }
        prefix_trace.append(round_record)
        emitter.emit(
            "progress",
            "DETERMINANTAL_ROUND_COMPLETED",
            all_radical_targets_verified=all_targets_verified,
            entry_ideal_is_unit=entry_unit,
            minor_prefix_size=boundary,
            round_certified=round_certified,
            round_index=round_index,
        )
        if round_certified:
            conditions_certified = True
            break

    coefficient_scope = str(policy["coefficient_scope"])
    if conditions_certified and coefficient_scope == "FINITE_FIELD_SCOUT_ONLY":
        status = "DETERMINANTAL_GF_SCOUT_PASSED"
    elif conditions_certified:
        status = "DETERMINANTAL_CONDITIONS_CERTIFIED_DIRECT_LIFT_PENDING"
    else:
        status = "DETERMINANTAL_SUBSET_INCONCLUSIVE"
    certificate_core = {
        "certificate_requirement": policy["certificate_requirement"],
        "coefficient_scope": coefficient_scope,
        "conditions_certified_over_selected_field": conditions_certified,
        "direct_J_lift_verified": False,
        "effective_rows": effective_rows,
        "entry_condition": entry_computation,
        "minor_candidates": [record for _minor, record in candidates],
        "minor_prefix_trace": prefix_trace,
        "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
        "row_unit_associate_relations": row_relations,
        "subset_implication_rule": (
            "SELECTED_ENTRY_UNIT_AND_ALL_EFFECTIVE_SELECTED_A_IN_RADICAL_OF_"
            "SELECTED_MINOR_SUBIDEAL_IMPLIES_FULL_I1_AND_FULL_A_RADICAL_I2"
        ),
    }
    certificate_bytes = len(canonical_json_bytes(certificate_core))
    certificate_terms = (
        sum(
            int(generator_pairs[index][0].number_of_terms())
            + int(generator_pairs[index][1].number_of_terms())
            for index in representative_indices
        )
        + generated_minor_terms
    )
    if certificate_bytes > int(policy["max_certificate_bytes"]):
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_DETERMINANTAL_CERTIFICATE_BYTES_EXCEEDED",
            "certificate_bytes": certificate_bytes,
            **common,
        }
    if certificate_terms > int(policy["max_certificate_terms"]):
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_DETERMINANTAL_CERTIFICATE_TERMS_EXCEEDED",
            "certificate_terms": certificate_terms,
            **common,
        }
    return {
        "status": status,
        "certificate_bytes": certificate_bytes,
        "certificate_scope": "SCOUT_ONLY" if ring.base_ring().is_finite() else "QQ_CANDIDATE",
        "certificate_sha256": canonical_sha256(certificate_core),
        "certificate_term_accounting": certificate_terms,
        "determinantal_certificate_schema": "sr2v-determinantal-certificate-v1",
        "determinantal_conditions_certified": conditions_certified,
        "direct_J_lift_verified": False,
        "discarded_minors": discarded_minors,
        "effective_row_count": len(effective_rows),
        "effective_rows": effective_rows,
        "entry_condition": entry_computation,
        "generated_minor_terms": generated_minor_terms,
        "groebner_algorithm": algorithm,
        "minor_candidate_count": len(candidates),
        "minor_candidates": [record for _minor, record in candidates],
        "minor_prefix_trace": prefix_trace,
        "policy_semantic_digest_sha256": policy["semantic_digest_sha256"],
        "raw_selected_row_count": len(rows),
        "row_unit_associate_relations": row_relations,
        "subset_implication_verified": conditions_certified,
        **common,
    }


def _run_libsingular_saturation(
    *,
    algorithm: str,
    common: Mapping[str, Any],
    emitter: Emitter,
    factors: Sequence[tuple[str, Any]],
    generators: Sequence[Any],
    max_live_basis_terms: int,
    method: str,
    ring: Any,
) -> dict[str, Any]:
    from sage.libs.singular.function_factory import ff

    emitter.emit(
        "progress",
        "DIRECT_GROEBNER_STARTED",
        generator_count=len(generators),
        method=method,
    )
    groebner_started = time.monotonic()
    basis = ring.ideal(generators).groebner_basis(algorithm=algorithm)
    groebner_seconds = time.monotonic() - groebner_started
    summary = _basis_summary(basis)
    emitter.emit(
        "progress",
        "DIRECT_GROEBNER_COMPLETED",
        seconds=groebner_seconds,
        **summary,
    )
    if summary["basis_term_count"] > max_live_basis_terms:
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "reason": "MAX_LIVE_BASIS_TERMS_EXCEEDED",
            "direct_backend": method,
            "groebner_seconds_total": groebner_seconds,
            "saturation_trace": [],
            **common,
            **summary,
        }

    saturation_trace: list[dict[str, Any]] = []
    saturation_seconds_total = 0.0
    for factor_index, (factor_name, factor) in enumerate(factors):
        if summary["is_unit_ideal"]:
            break
        emitter.emit(
            "progress",
            "DIRECT_SATURATION_STARTED",
            factor_index=factor_index,
            factor_name=factor_name,
            factor_terms=int(factor.number_of_terms()),
            method=method,
        )
        factor_ideal = ring.ideal([factor])
        input_basis = basis
        system_started = time.monotonic()
        system_basis = ff.system(
            "sat",
            input_basis,
            factor_ideal,
            attributes={input_basis: {"isSB": 1}},
        )
        system_seconds = time.monotonic() - system_started
        saturation_seconds_total += system_seconds
        saturation_exponent: int | None = None
        ab_equivalent: bool | None = None
        exponent_certificate_verified: bool | None = None
        sat_with_exp_seconds: float | None = None
        if method == "libsingular_ab_saturation":
            with_exp_started = time.monotonic()
            with_exp_basis, raw_exponent = ff.elim__lib.sat_with_exp(
                input_basis,
                factor_ideal,
                attributes={input_basis: {"isSB": 1}},
            )
            sat_with_exp_seconds = time.monotonic() - with_exp_started
            saturation_seconds_total += sat_with_exp_seconds
            saturation_exponent = int(raw_exponent)
            ab_equivalent = _basis_is_subset(system_basis, with_exp_basis) and _basis_is_subset(
                with_exp_basis, system_basis
            )
            input_contained = _basis_is_subset(input_basis, system_basis)
            input_divisors = list(input_basis)
            exponent_certificate_verified = all(
                not (factor**saturation_exponent * polynomial).reduce(input_divisors)
                for polynomial in system_basis
            )
            if not (ab_equivalent and input_contained and exponent_certificate_verified):
                raise WorkerInputError(
                    "libSingular system(sat) failed exact A/B containment verification"
                )
        basis = system_basis
        summary = _basis_summary(basis)
        record = {
            "ab_equivalent": ab_equivalent,
            "basis_size": summary["basis_size"],
            "basis_term_count": summary["basis_term_count"],
            "exponent_certificate_verified": exponent_certificate_verified,
            "factor_index": factor_index,
            "factor_name": factor_name,
            "factor_terms": int(factor.number_of_terms()),
            "is_unit_ideal": summary["is_unit_ideal"],
            "sat_with_exp_seconds": sat_with_exp_seconds,
            "saturation_exponent": saturation_exponent,
            "system_sat_seconds": system_seconds,
        }
        saturation_trace.append(record)
        emitter.emit("progress", "DIRECT_SATURATION_COMPLETED", **record)
        if summary["basis_term_count"] > max_live_basis_terms:
            return {
                "status": "SOFT_RESOURCE_LIMIT",
                "reason": "MAX_LIVE_BASIS_TERMS_EXCEEDED",
                "direct_backend": method,
                "groebner_seconds_total": groebner_seconds,
                "saturation_seconds_total": saturation_seconds_total,
                "saturation_trace": saturation_trace,
                **common,
                **summary,
            }
    status = "UNIT_IDEAL_FOUND_CERTIFICATE_PENDING" if summary["is_unit_ideal"] else "COMPLETED"
    return {
        "status": status,
        "direct_backend": method,
        "groebner_algorithm": algorithm,
        "groebner_seconds_total": groebner_seconds,
        "saturation_seconds_total": saturation_seconds_total,
        "saturation_trace": saturation_trace,
        **common,
        **summary,
    }


def _run_sage(repository_root: Path, request: dict[str, Any], emitter: Emitter) -> dict[str, Any]:
    # Imports stay inside the execution function so pure-Python request tests do
    # not require Sage on the host.
    from sage.all import GF, QQ, PolynomialRing, is_prime
    from sage.env import SAGE_VERSION

    if worker_source_sha256() != request["expected_worker_source_sha256"]:
        raise WorkerInputError("running worker source differs from the request binding")
    if request["modulus"] and not bool(is_prime(request["modulus"])):
        raise WorkerInputError("modulus must be prime")

    hard_bytes = int(request["memory_limit_bytes"])
    if _resource is None:
        raise RuntimeError("POSIX resource limits are unavailable in the Sage worker")
    _resource.setrlimit(_resource.RLIMIT_AS, (hard_bytes, hard_bytes))
    root = load_verified_root(repository_root, request)
    rows = selected_generator_rows(root, request)
    bottom_records = request["bottom_factor_records"]
    if (
        canonical_sha256(bottom_records)
        != root["ring_binding"]["bottom_localization_factor_ledger_sha256"]
    ):
        raise WorkerInputError("bottom localization factor ledger is not root-bound")

    chart = root["chart_generator_ids"]["charts"][request["chart"]]
    is_determinantal = request["method"] in DETERMINANTAL_METHODS
    if is_determinantal:
        policy = request["determinantal_policy"]
        if not isinstance(policy, Mapping):  # validated before Sage starts; keeps narrowing local
            raise WorkerInputError("determinantal policy disappeared after request validation")
        if policy["row_universe_sha256"] != canonical_sha256(chart["generator_polynomial_ids"]):
            raise WorkerInputError("determinantal row universe disagrees with the root-bound chart")
    localizer_id = int(chart["planned_Rabinowitsch_localization_polynomial_id"])
    needed = {int(identifier) for _source, first, second in rows for identifier in (first, second)}
    chart_factor_id = int(request["chart_factor_polynomial_id"])
    needed.update({chart_factor_id, localizer_id})
    emitter.emit(
        "progress",
        "INPUT_AUTHENTICATED",
        chart=request["chart"],
        generator_count=len(rows),
        needed_polynomial_count=len(needed),
        root_semantic_digest_sha256=root["semantic_digest_sha256"],
    )
    records, loaded_terms = _scan_needed_records(repository_root, root, needed, emitter)
    if loaded_terms > int(request["max_loaded_terms"]):
        return {
            "status": "SOFT_RESOURCE_LIMIT",
            "chart": request["chart"],
            "coefficient_field": ("QQ" if request["modulus"] == 0 else f"GF({request['modulus']})"),
            "generator_count": len(rows),
            "reason": "MAX_LOADED_TERMS_EXCEEDED",
            "loaded_terms": loaded_terms,
            "method": request["method"],
            "representation": "BASE_MATRIX_A_B" if is_determinantal else "AFFINE_H_GENERATORS",
        }

    base_variables = list(root["ring_binding"]["polynomial_arena_variable_order"])
    if base_variables != [
        *(f"t{index}" for index in range(1, 5)),
        *(f"s{index}" for index in range(48)),
    ]:
        raise WorkerInputError("frozen polynomial arena variable order changed")
    ring_variables = base_variables if is_determinantal else [*base_variables, "h"]
    field = QQ if request["modulus"] == 0 else GF(request["modulus"])
    ring = PolynomialRing(field, ring_variables, order=request["monomial_order"])
    ring_generators = list(ring.gens())
    width = len(ring_variables)
    by_id = {
        identifier: _materialize_polynomial(record, ring, field, width)
        for identifier, record in records.items()
    }
    chart_record = records[chart_factor_id]
    if chart_record["sha256"] != request["chart_factor_sha256"]:
        raise WorkerInputError("chart factor content digest mismatch")
    chart_factor = by_id[chart_factor_id]
    bottom_factors = [
        _bottom_factor_polynomial(record, ring, field, width) for record in bottom_records
    ]
    torus_factor = ring.one()
    for generator in ring_generators[4:52]:
        torus_factor *= generator
    expected_localizer = chart_factor * torus_factor
    for factor in bottom_factors:
        expected_localizer *= factor
    localizer_ratio = _unit_associate_ratio(by_id[localizer_id], expected_localizer)
    if localizer_ratio is None:
        raise WorkerInputError(
            "native saturation factors do not reproduce the root-bound Rabinowitsch localizer"
        )

    generator_pairs = [(by_id[first], by_id[second]) for _source, first, second in rows]
    if any(not first and not second for first, second in generator_pairs):
        raise WorkerInputError("a selected root generator materialized as zero")
    if is_determinantal:
        generators: list[Any] = []
        generator_term_counts = [
            int(first.number_of_terms()) + int(second.number_of_terms())
            for first, second in generator_pairs
        ]
    else:
        h = ring_generators[52]
        generators = [h * first + second for first, second in generator_pairs]
        if any(not polynomial for polynomial in generators):
            raise WorkerInputError("a selected root generator materialized as zero")
        generator_term_counts = [int(polynomial.number_of_terms()) for polynomial in generators]
    emitter.emit(
        "progress",
        "STAGE_MATERIALIZED",
        generator_count=len(generator_pairs),
        generator_terms=sum(generator_term_counts),
        largest_generator_terms=max(generator_term_counts),
        loaded_polynomial_count=len(by_id),
        loaded_terms=loaded_terms,
        localizer_associate_ratio=str(localizer_ratio),
        representation="BASE_MATRIX_A_B" if is_determinantal else "AFFINE_H_GENERATORS",
        ring_variable_count=width,
    )
    common = {
        "chart": request["chart"],
        "coefficient_field": "QQ" if request["modulus"] == 0 else f"GF({request['modulus']})",
        "generator_count": len(generator_pairs),
        "generator_term_count": sum(generator_term_counts),
        "largest_generator_term_count": max(generator_term_counts),
        "loaded_polynomial_count": len(by_id),
        "loaded_terms": loaded_terms,
        "localizer_associate_ratio": str(localizer_ratio),
        "method": request["method"],
        "representation": "BASE_MATRIX_A_B" if is_determinantal else "AFFINE_H_GENERATORS",
        "ring_variable_count": width,
        "sage_version": str(SAGE_VERSION),
    }
    if request["method"] == "build_only":
        return {"status": "BUILD_COMPLETED", **common}
    if request["method"] == "redundancy_audit":
        relations = _raw_redundancy_relations(rows, generator_pairs)
        return {
            "status": "REDUNDANCY_AUDIT_COMPLETED",
            "raw_redundancy_relation_count": len(relations),
            "raw_redundancy_relations": relations,
            "relation_set_sha256": canonical_sha256(relations),
            **common,
        }

    algorithm = request["groebner_algorithm"]
    factor_groups = {
        "chart": [("chart", chart_factor)],
        "bottom": [
            (str(record["factor_id"]), factor)
            for record, factor in zip(bottom_records, bottom_factors, strict=True)
        ],
        "torus": [("torus_product_s0_through_s47", torus_factor)],
    }
    ordered_factors = [
        item for group in request["factor_group_order"] for item in factor_groups[group]
    ]
    if is_determinantal:
        return _run_determinantal_cegar(
            algorithm=algorithm,
            common=common,
            emitter=emitter,
            factors=ordered_factors,
            generator_pairs=generator_pairs,
            max_live_basis_terms=int(request["max_live_basis_terms"]),
            policy=policy,
            ring=ring,
            rows=rows,
        )
    if request["method"] in {
        "libsingular_ab_saturation",
        "libsingular_system_saturation",
    }:
        return _run_libsingular_saturation(
            algorithm=algorithm,
            common=common,
            emitter=emitter,
            factors=ordered_factors,
            generators=generators,
            max_live_basis_terms=int(request["max_live_basis_terms"]),
            method=str(request["method"]),
            ring=ring,
        )
    batch_sizes = [int(value) for value in request["incremental_batch_sizes"]]
    basis: list[Any] = []
    summary = _basis_summary(basis)
    previous_boundary = 0
    groebner_seconds_total = 0.0
    batch_trace: list[dict[str, Any]] = []
    saturation_trace: list[dict[str, Any]] = []
    global_factor_index = 0
    for batch_index, boundary in enumerate(batch_sizes):
        # Exact incremental localisation identity:
        #   ((I:S^infinity) + J):S^infinity = (I + J):S^infinity.
        # Reusing the already saturated basis prevents components supported on
        # the forbidden divisor from reappearing before every larger batch.
        added_generators = generators[previous_boundary:boundary]
        batch_generators = [*basis, *added_generators]
        emitter.emit(
            "progress",
            "BATCH_GROEBNER_STARTED",
            added_generator_count=len(added_generators),
            batch_index=batch_index,
            effective_generator_count=boundary,
            input_basis_count=len(basis),
        )
        groebner_started = time.monotonic()
        basis = list(ring.ideal(batch_generators).groebner_basis(algorithm=algorithm))
        groebner_seconds = time.monotonic() - groebner_started
        groebner_seconds_total += groebner_seconds
        summary = _basis_summary(basis)
        emitter.emit(
            "progress",
            "BATCH_GROEBNER_COMPLETED",
            added_generator_count=len(added_generators),
            batch_index=batch_index,
            effective_generator_count=boundary,
            seconds=groebner_seconds,
            **summary,
        )
        if summary["basis_term_count"] > int(request["max_live_basis_terms"]):
            return {
                "status": "SOFT_RESOURCE_LIMIT",
                "reason": "MAX_LIVE_BASIS_TERMS_EXCEEDED",
                "batch_trace": batch_trace,
                "groebner_seconds_total": groebner_seconds_total,
                "saturation_trace": saturation_trace,
                **common,
                **summary,
            }
        current_ideal = ring.ideal(basis)
        batch_saturation_seconds = 0.0
        for batch_factor_index, (factor_name, factor) in enumerate(ordered_factors):
            if summary["is_unit_ideal"]:
                break
            emitter.emit(
                "progress",
                "SATURATION_STEP_STARTED",
                batch_factor_index=batch_factor_index,
                batch_index=batch_index,
                effective_generator_count=boundary,
                factor_index=global_factor_index,
                factor_name=factor_name,
                factor_terms=int(factor.number_of_terms()),
            )
            factor_started = time.monotonic()
            current_ideal, exponent = current_ideal.saturation(ring.ideal([factor]))
            basis = list(current_ideal.groebner_basis(algorithm=algorithm))
            current_ideal = ring.ideal(basis)
            seconds = time.monotonic() - factor_started
            batch_saturation_seconds += seconds
            summary = _basis_summary(basis)
            record = {
                "basis_size": summary["basis_size"],
                "basis_term_count": summary["basis_term_count"],
                "batch_factor_index": batch_factor_index,
                "batch_index": batch_index,
                "effective_generator_count": boundary,
                "factor_index": global_factor_index,
                "factor_name": factor_name,
                "factor_terms": int(factor.number_of_terms()),
                "is_unit_ideal": summary["is_unit_ideal"],
                "saturation_exponent": int(exponent),
                "seconds": seconds,
            }
            global_factor_index += 1
            saturation_trace.append(record)
            emitter.emit("progress", "SATURATION_STEP_COMPLETED", **record)
            if summary["basis_term_count"] > int(request["max_live_basis_terms"]):
                return {
                    "status": "SOFT_RESOURCE_LIMIT",
                    "reason": "MAX_LIVE_BASIS_TERMS_EXCEEDED",
                    "batch_trace": batch_trace,
                    "groebner_seconds_total": groebner_seconds_total,
                    "saturation_trace": saturation_trace,
                    **common,
                    **summary,
                }
        batch_record = {
            "added_generator_count": len(added_generators),
            "basis_size": summary["basis_size"],
            "basis_term_count": summary["basis_term_count"],
            "batch_index": batch_index,
            "effective_generator_count": boundary,
            "groebner_seconds": groebner_seconds,
            "is_unit_ideal": summary["is_unit_ideal"],
            "saturation_seconds": batch_saturation_seconds,
        }
        batch_trace.append(batch_record)
        emitter.emit("progress", "INCREMENTAL_BATCH_COMPLETED", **batch_record)
        previous_boundary = boundary
        if summary["is_unit_ideal"]:
            break
    status = "UNIT_IDEAL_FOUND_CERTIFICATE_PENDING" if summary["is_unit_ideal"] else "COMPLETED"
    return {
        "status": status,
        "batch_trace": batch_trace,
        "factor_group_order": request["factor_group_order"],
        "groebner_algorithm": algorithm,
        "groebner_seconds_total": groebner_seconds_total,
        "incremental_batch_sizes": batch_sizes,
        "saturation_trace": saturation_trace,
        **common,
        **summary,
    }


def run(request_path: Path, repository_root: Path) -> int:
    emitter = Emitter()
    try:
        request = load_verified_request(request_path)
        emitter.emit(
            "progress",
            "REQUEST_VERIFIED",
            request_payload_sha256=canonical_sha256(request),
        )
        result = _run_sage(repository_root.resolve(), request, emitter)
        status = str(result["status"])
        emitter.emit("result", "WORKER_FINISHED", **result)
        return (
            0
            if status
            in {
                "BUILD_COMPLETED",
                "COMPLETED",
                "DETERMINANTAL_INVENTORY_COMPLETED",
                "REDUNDANCY_AUDIT_COMPLETED",
            }
            else 2
        )
    except Exception as error:  # noqa: BLE001 - worker must emit a machine-readable failure
        traceback.print_exc(file=sys.stderr)
        emitter.emit(
            "result",
            "WORKER_FAILED",
            error_message=str(error),
            error_type=type(error).__name__,
            status=f"ERROR_{type(error).__name__.upper()}",
        )
        return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(os.environ.get("SR2V_REPOSITORY_ROOT", "/home/sage/work")),
    )
    arguments = parser.parse_args(argv)
    return run(arguments.request, arguments.repository_root)


if __name__ == "__main__":
    raise SystemExit(main())
