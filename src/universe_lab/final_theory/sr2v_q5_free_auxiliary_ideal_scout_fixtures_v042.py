"""Fail-closed tracked inputs for the bounded v0.4.2 U2 scouts.

The two Sage scouts intentionally operate on a fixed 20-record subset rather
than scanning the untracked full polynomial arena.  This module has no Sage
dependency so fixture selection and subset authentication are testable in a
fresh clone.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Final

STAGE7_REQUEST_FIXTURE: Final = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_stage7_request.json"
)
STAGE7_RESULT_FIXTURE: Final = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_stage7_result.json"
)
POLYNOMIAL_SUBSET_FIXTURE: Final = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_polynomial_subset.json"
)
SCOUT_REPRODUCTION_MANIFEST: Final = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json"
)
SCOUT_EXPECTATIONS: Final = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)

STAGE7_REQUEST_RAW_SHA256: Final = (
    "456330c1fdb2abacea6b8a98d03dc9a78dbdbb72dcae7adff8f56740ae23098f"
)
STAGE7_RESULT_RAW_SHA256: Final = "f6f4d0c04cef65dcd454e61a23fcbcd7f932a500b3e2177fa69bf45447e04c14"
POLYNOMIAL_SUBSET_RAW_SHA256: Final = (
    "718d484df2e3bb111383b49e90aba4cd3244ce6a3b907da016fc888635307c94"
)

ROOT_SEMANTIC_DIGEST_SHA256: Final = (
    "09b8ab346af957016be9a11f0f38b6fa94a1bee7310b2fe046633baef2f15688"
)
POLYNOMIAL_ARENA_ID_TO_SHA256_DIGEST_SHA256: Final = (
    "da1f36484ea8b03a16bfd84f05104f27e66c61c8fbb144d2ea36d3d26acc1402"
)
POLYNOMIAL_SUBSET_SCHEMA: Final = "sr2v-q5-free-bounded-scout-polynomial-subset-v1"
POLYNOMIAL_SUBSET_CLAIM_BOUNDARY: Final = (
    "Only the 20 polynomial records needed by the bounded U2 row-185 and "
    "candidate-row-10 scouts are included. This fixture does not reproduce the "
    "full 3,161-record polynomial arena, full bundle, or stage-8 raw "
    "event/postflight artifacts."
)
REQUIRED_POLYNOMIAL_IDS: Final = (
    1,
    2,
    6,
    7,
    11,
    12,
    69,
    75,
    76,
    297,
    298,
    301,
    302,
    545,
    546,
    1143,
    1144,
    1146,
    1147,
    3157,
)
ROW185_NEEDED_POLYNOMIAL_IDS: Final = frozenset(
    {
        1,
        2,
        6,
        7,
        69,
        75,
        76,
        297,
        298,
        301,
        302,
        545,
        546,
        1143,
        1144,
        1146,
        1147,
        3157,
    }
)
CANDIDATE_ROW10_NEEDED_POLYNOMIAL_IDS: Final = frozenset(REQUIRED_POLYNOMIAL_IDS)
ROW185_LOADED_TERM_COUNT: Final = 2307
CANDIDATE_ROW10_LOADED_TERM_COUNT: Final = 2508
POLYNOMIAL_SUBSET_RECORDS_CANONICAL_SHA256: Final = (
    "02fa681dd799fe42c4a5b9f8a6d636ccc4ba098b4f41bbd9967f636a3d77c2a6"
)

STAGE7_FINGERPRINT_SHA256: Final = (
    "a52d38ca87ad472f76746510c518dad76e041f00d489093aa6c015319b000be8"
)
LEGACY_OBSERVATION_STATUS: Final = (
    "NONDETERMINISTIC_LEGACY_OBSERVATION_NOT_A_REPRODUCTION_EXPECTATION"
)
SCOUT_REPRODUCTION_MANIFEST_SCHEMA: Final = (
    "sr2v-q5-free-bounded-scout-reproduction-input-manifest-v1"
)
SCOUT_EXPECTATIONS_SCHEMA: Final = "sr2v-q5-free-bounded-scout-expectations-v1"
SCOUT_EXPECTATIONS_PENDING: Final = "PENDING_BOUNDED_SAGE_RECOMPUTATION"
SCOUT_EXPECTATIONS_PINNED: Final = "PINNED"
SCOUT_INPUT_MODE: Final = "BOUNDED_SCOUT_SUBSET_ONLY"
STAGE7_DERIVATION_STATUS: Final = "DERIVED_CALCULATION_NOT_STAGE7_WORKER_REEXECUTION"
SAGE_IMAGE: Final = "sagemath/sagemath:10.9"
SAGE_IMAGE_REPO_DIGEST: Final = (
    "sha256:e068670ae5863b54b2550e72437ec637b0283acb0dc712c8584c124dbf44e667"
)
SCOUT_REPRODUCTION_CLAIM_BOUNDARY: Final = (
    "These bounded scouts derive from the pinned stage-7 request/result and the "
    "20-record subset fixture. They are not a reexecution of the historical "
    "stage-7 worker and do not reproduce the full 3,161-record polynomial arena, "
    "full bundle, or stage-8 raw event/postflight artifacts."
)
SCOUT_REPRODUCTION_NONCLAIMS: Final = (
    "FULL_3161_RECORD_POLYNOMIAL_ARENA_NOT_REPRODUCED",
    "FULL_BUNDLE_NOT_REPRODUCED",
    "STAGE8_RAW_EVENT_POSTFLIGHT_NOT_REPRODUCED",
)

_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_SUBSET_EXPECTED_KEYS: Final = frozenset(
    {
        "claim_boundary",
        "polynomial_arena_id_to_sha256_digest_sha256",
        "record_count",
        "records",
        "records_canonical_sha256",
        "required_polynomial_ids",
        "root_semantic_digest_sha256",
        "schema_version",
        "term_count_total",
    }
)
_RECORD_EXPECTED_KEYS: Final = frozenset({"polynomial_id", "sha256", "term_count", "terms"})
_MANIFEST_EXPECTED_KEYS: Final = frozenset(
    {
        "claim_boundary",
        "fixture_raw_sha256",
        "input_mode",
        "nonclaims",
        "root_semantic_digest_sha256",
        "sage_image",
        "schema_version",
        "semantic_digest_sha256",
        "source_normalized_lf_sha256",
        "stage7_derivation",
        "subset_records_canonical_sha256",
    }
)
_EXPECTATIONS_EXPECTED_KEYS: Final = frozenset(
    {
        "certificate_core_digests",
        "input_manifest_semantic_digest_sha256",
        "legacy_full_result_semantic_digests",
        "legacy_observation_status",
        "schema_version",
        "semantic_digest_sha256",
        "status",
    }
)
_MANIFEST_SOURCE_PATHS: Final = frozenset(
    {
        "compose.yaml",
        "scripts/reproduce_v042_candidate_minor_only_scout.py",
        "scripts/extract_v042_bounded_scout_polynomial_subset.py",
        "scripts/reproduce_v042_row185_normal_form_scout.py",
        "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042.py",
        "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_worker_v042.py",
        "uv.lock",
    }
)
_MANIFEST_FIXTURE_RAW_SHA256: Final = {
    STAGE7_REQUEST_FIXTURE.as_posix(): STAGE7_REQUEST_RAW_SHA256,
    STAGE7_RESULT_FIXTURE.as_posix(): STAGE7_RESULT_RAW_SHA256,
    POLYNOMIAL_SUBSET_FIXTURE.as_posix(): POLYNOMIAL_SUBSET_RAW_SHA256,
}
_LEGACY_FULL_RESULT_SEMANTIC_DIGESTS: Final = {
    "candidate_minor_only": "02f2ab4fbb53e8c91b5e67eb686a35543e61a51db2f912191f7621a002e4f947",
    "row185_normal_form": "dc89668ac743214b4c84ee732672f7542e1517c2c200409cff2db54cc1d5d177",
}
_SCOUT_EXPECTATION_NAMES: Final = frozenset(_LEGACY_FULL_RESULT_SEMANTIC_DIGESTS)
_RUNTIME_OBSERVATION_KEYS: Final = frozenset(
    {
        "elapsed_seconds",
        "groebner_seconds",
        "saturation_seconds",
        "ru_maxrss_kib",
        "ru_stime_seconds",
        "ru_utime_seconds",
        "runtime_observation",
    }
)


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


def normalized_lf_sha256(path: Path) -> str:
    """Hash bytes after normalizing every line ending to LF."""

    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _safe_repository_path(repository_root: Path, relative: str) -> Path:
    root = repository_root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise RuntimeError(f"path escapes repository root: {relative}") from error
    return candidate


def _require_exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise RuntimeError(
            f"{label} keys disagree with the contract; "
            f"missing={sorted(expected - actual)}, unsupported={sorted(actual - expected)}"
        )


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise RuntimeError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_int(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RuntimeError(f"{label} must be an integer >= {minimum}")
    return value


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_bytes())
    except FileNotFoundError as error:
        raise RuntimeError(f"{label} is missing: {path}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"{label} is not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object: {path}")
    return payload


def _read_verified_fixture(path: Path, expected_sha256: str, label: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise RuntimeError(f"tracked {label} fixture is missing: {path}") from error
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"tracked {label} fixture SHA-256 mismatch: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"tracked {label} fixture is not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"tracked {label} fixture must be a JSON object: {path}")
    return payload


def is_canonical_stage7_result(payload: Mapping[str, Any]) -> bool:
    """Recognize the one result shape that can be a local stage-7 mirror."""

    details = payload.get("details")
    worker_result = details.get("worker_result") if isinstance(details, Mapping) else None
    return (
        payload.get("status") == "DETERMINANTAL_SUBSET_INCONCLUSIVE"
        and isinstance(worker_result, Mapping)
        and worker_result.get("method") == "determinantal_cegar_v1"
        and worker_result.get("coefficient_field") == "GF(32003)"
        and worker_result.get("raw_selected_row_count") == 7
    )


def load_tracked_stage7_fixture(
    repository_root: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Load the pinned stage-7 request/result pair and verify its binding."""

    request_path = repository_root / STAGE7_REQUEST_FIXTURE
    result_path = repository_root / STAGE7_RESULT_FIXTURE
    request = _read_verified_fixture(
        request_path,
        STAGE7_REQUEST_RAW_SHA256,
        "stage-7 request",
    )
    result = _read_verified_fixture(
        result_path,
        STAGE7_RESULT_RAW_SHA256,
        "stage-7 result",
    )
    details = result.get("details")
    request_payload = request.get("payload")
    payload_digest = request.get("payload_digest_sha256")
    if (
        not is_canonical_stage7_result(result)
        or not isinstance(details, Mapping)
        or not isinstance(request_payload, Mapping)
        or _require_sha256(payload_digest, "stage-7 request payload digest")
        != canonical_sha256(request_payload)
        or result.get("fingerprint_sha256") != STAGE7_FINGERPRINT_SHA256
        or details.get("request_payload_sha256") != payload_digest
        or request_payload.get("chart") != "U2"
        or request_payload.get("method") != "determinantal_cegar_v1"
        or request_payload.get("modulus") != 32003
        or request_payload.get("selected_entry_indices") != [8, 9, 97, 98, 327, 328, 31]
    ):
        raise RuntimeError("tracked stage-7 fixtures disagree with the canonical binding")
    return request_path, request, result


def _load_self_bound_reproduction_manifest(repository_root: Path) -> dict[str, Any]:
    path = _safe_repository_path(repository_root, str(SCOUT_REPRODUCTION_MANIFEST))
    manifest = _read_json_object(path, "bounded-scout reproduction manifest")
    _require_exact_keys(manifest, _MANIFEST_EXPECTED_KEYS, "bounded-scout reproduction manifest")
    semantic_digest = _require_sha256(
        manifest.get("semantic_digest_sha256"),
        "bounded-scout reproduction manifest semantic digest",
    )
    unbound = {key: value for key, value in manifest.items() if key != "semantic_digest_sha256"}
    if canonical_sha256(unbound) != semantic_digest:
        raise RuntimeError("bounded-scout reproduction manifest semantic digest mismatch")
    return manifest


def load_bounded_scout_expectations(
    repository_root: Path,
    input_manifest_semantic_digest_sha256: str,
) -> dict[str, Any]:
    """Load the self-bound core-digest expectation artifact without Docker."""

    _require_sha256(
        input_manifest_semantic_digest_sha256,
        "bounded-scout input manifest semantic digest",
    )
    path = _safe_repository_path(repository_root, str(SCOUT_EXPECTATIONS))
    expectations = _read_json_object(path, "bounded-scout expectations")
    _require_exact_keys(expectations, _EXPECTATIONS_EXPECTED_KEYS, "bounded-scout expectations")
    semantic_digest = _require_sha256(
        expectations.get("semantic_digest_sha256"),
        "bounded-scout expectations semantic digest",
    )
    unbound = {key: value for key, value in expectations.items() if key != "semantic_digest_sha256"}
    if canonical_sha256(unbound) != semantic_digest:
        raise RuntimeError("bounded-scout expectations semantic digest mismatch")
    if (
        expectations.get("schema_version") != SCOUT_EXPECTATIONS_SCHEMA
        or expectations.get("input_manifest_semantic_digest_sha256")
        != input_manifest_semantic_digest_sha256
        or expectations.get("legacy_observation_status") != LEGACY_OBSERVATION_STATUS
        or expectations.get("legacy_full_result_semantic_digests")
        != _LEGACY_FULL_RESULT_SEMANTIC_DIGESTS
    ):
        raise RuntimeError("bounded-scout expectations provenance binding mismatch")
    digests = expectations.get("certificate_core_digests")
    if not isinstance(digests, Mapping) or frozenset(digests) != _SCOUT_EXPECTATION_NAMES:
        raise RuntimeError("bounded-scout expectations certificate-core names mismatch")
    status = expectations.get("status")
    if status == SCOUT_EXPECTATIONS_PENDING:
        if any(value is not None for value in digests.values()):
            raise RuntimeError("pending bounded-scout expectations must not pin a core digest")
    elif status == SCOUT_EXPECTATIONS_PINNED:
        for scout_name, digest in digests.items():
            _require_sha256(digest, f"bounded-scout expected core digest for {scout_name}")
    else:
        raise RuntimeError("unsupported bounded-scout expectations status")
    return expectations


def verify_scout_certificate_core_expectation(
    repository_root: Path,
    input_manifest: Mapping[str, Any],
    scout_name: str,
    certificate_core_digest_sha256: str,
) -> dict[str, Any]:
    """Fail closed on a pinned mathematical-core mismatch after a Sage run."""

    if scout_name not in _SCOUT_EXPECTATION_NAMES:
        raise RuntimeError(f"unsupported bounded-scout expectation name: {scout_name}")
    _require_sha256(certificate_core_digest_sha256, "computed certificate core digest")
    input_manifest_digest = _require_sha256(
        input_manifest.get("semantic_digest_sha256"),
        "bounded-scout input manifest semantic digest",
    )
    expectations = load_bounded_scout_expectations(repository_root, input_manifest_digest)
    expected = expectations["certificate_core_digests"][scout_name]
    if expectations["status"] == SCOUT_EXPECTATIONS_PINNED:
        if expected != certificate_core_digest_sha256:
            raise RuntimeError(
                f"bounded-scout {scout_name} certificate core digest mismatch: "
                f"expected {expected}, got {certificate_core_digest_sha256}"
            )
    elif expected is not None:
        raise RuntimeError("pending bounded-scout expectation unexpectedly pins a core digest")
    return expectations


def _validate_manifest_source_hashes(
    repository_root: Path,
    source_hashes: object,
) -> None:
    if not isinstance(source_hashes, Mapping) or frozenset(source_hashes) != _MANIFEST_SOURCE_PATHS:
        raise RuntimeError("bounded-scout reproduction source-hash paths mismatch")
    for relative in sorted(_MANIFEST_SOURCE_PATHS):
        expected = _require_sha256(
            source_hashes[relative],
            f"bounded-scout reproduction source hash for {relative}",
        )
        path = _safe_repository_path(repository_root, relative)
        try:
            actual = normalized_lf_sha256(path)
        except FileNotFoundError as error:
            raise RuntimeError(
                f"bounded-scout reproduction source is missing: {relative}"
            ) from error
        if actual != expected:
            raise RuntimeError(
                f"bounded-scout reproduction source hash mismatch for {relative}: "
                f"expected {expected}, got {actual}"
            )


def _validate_manifest_fixture_hashes(
    repository_root: Path,
    fixture_hashes: object,
) -> None:
    if (
        not isinstance(fixture_hashes, Mapping)
        or dict(fixture_hashes) != _MANIFEST_FIXTURE_RAW_SHA256
    ):
        raise RuntimeError("bounded-scout reproduction fixture-hash binding mismatch")
    for relative, expected in _MANIFEST_FIXTURE_RAW_SHA256.items():
        _read_verified_fixture(
            _safe_repository_path(repository_root, relative),
            expected,
            f"bounded-scout {relative}",
        )


def _validate_root_semantic_digest(repository_root: Path) -> dict[str, Any]:
    root = _read_json_object(
        _safe_repository_path(
            repository_root,
            "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.json",
        ),
        "bounded-scout bundle root",
    )
    observed = canonical_sha256(
        {key: value for key, value in root.items() if key != "semantic_digest_sha256"}
    )
    if observed != ROOT_SEMANTIC_DIGEST_SHA256:
        raise RuntimeError("bounded-scoped subset root semantic digest mismatch")
    _root_polynomial_digest_by_id(root)
    return root


def validate_bounded_scout_reproduction_inputs(repository_root: Path) -> dict[str, Any]:
    """Verify every tracked input/source binding required before a Sage run.

    This deliberately does not inspect Docker.  The pinned image RepoDigest is
    checked by the explicit Docker gate documented beside the execution command.
    """

    manifest = _load_self_bound_reproduction_manifest(repository_root)
    if (
        manifest.get("schema_version") != SCOUT_REPRODUCTION_MANIFEST_SCHEMA
        or manifest.get("claim_boundary") != SCOUT_REPRODUCTION_CLAIM_BOUNDARY
        or manifest.get("input_mode") != SCOUT_INPUT_MODE
        or manifest.get("stage7_derivation") != STAGE7_DERIVATION_STATUS
        or manifest.get("nonclaims") != list(SCOUT_REPRODUCTION_NONCLAIMS)
        or manifest.get("root_semantic_digest_sha256") != ROOT_SEMANTIC_DIGEST_SHA256
        or manifest.get("subset_records_canonical_sha256")
        != POLYNOMIAL_SUBSET_RECORDS_CANONICAL_SHA256
    ):
        raise RuntimeError("bounded-scout reproduction manifest claim binding mismatch")
    sage_image = manifest.get("sage_image")
    if not isinstance(sage_image, Mapping) or dict(sage_image) != {
        "image": SAGE_IMAGE,
        "repo_digest": SAGE_IMAGE_REPO_DIGEST,
    }:
        raise RuntimeError("bounded-scout reproduction Sage image binding mismatch")
    _validate_manifest_source_hashes(repository_root, manifest.get("source_normalized_lf_sha256"))
    _validate_manifest_fixture_hashes(repository_root, manifest.get("fixture_raw_sha256"))
    root = _validate_root_semantic_digest(repository_root)
    root_by_id = _root_polynomial_digest_by_id(root)
    subset = _read_verified_fixture(
        _safe_repository_path(repository_root, str(POLYNOMIAL_SUBSET_FIXTURE)),
        POLYNOMIAL_SUBSET_RAW_SHA256,
        "bounded-scoped polynomial subset",
    )
    _validate_subset_records(subset, root_by_id)
    load_tracked_stage7_fixture(repository_root)
    load_bounded_scout_expectations(repository_root, manifest["semantic_digest_sha256"])
    return manifest


def find_stage7_request(repository_root: Path) -> tuple[Path, dict[str, Any]]:
    """Use fixtures as authority and reject a conflicting local attempt mirror."""

    fixture_request_path, fixture_request, fixture_result = load_tracked_stage7_fixture(
        repository_root
    )
    candidates: list[tuple[Path, dict[str, Any]]] = []
    attempts = repository_root / "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_supervised/attempts"
    if attempts.is_dir():
        for result_path in attempts.glob("*/**/result.json"):
            payload = _read_json_object(result_path, "local supervised result")
            if is_canonical_stage7_result(payload):
                candidates.append((result_path.parent / "request.json", payload))
    if len(candidates) > 1:
        raise RuntimeError(f"ambiguous local canonical stage-7 attempts: {len(candidates)}")
    if candidates:
        local_request_path, local_result = candidates[0]
        local_request = _read_json_object(local_request_path, "local stage-7 request")
        if canonical_sha256(local_request) != canonical_sha256(fixture_request):
            raise RuntimeError("local stage-7 request differs from the tracked canonical fixture")
        if canonical_sha256(local_result) != canonical_sha256(fixture_result):
            raise RuntimeError("local stage-7 result differs from the tracked canonical fixture")
    return fixture_request_path, fixture_result


def _root_polynomial_digest_by_id(root: Mapping[str, Any]) -> dict[int, str]:
    if root.get("semantic_digest_sha256") != ROOT_SEMANTIC_DIGEST_SHA256:
        raise RuntimeError("bounded-scoped subset root semantic digest mismatch")
    arena_index = root.get("arena_index")
    if not isinstance(arena_index, Mapping):
        raise RuntimeError("bundle root has no polynomial arena index")
    arena = arena_index.get("polynomial_arena")
    if not isinstance(arena, Mapping):
        raise RuntimeError("bundle root has no polynomial arena")
    correspondence = arena.get("polynomial_id_to_sha256")
    if not isinstance(correspondence, list):
        raise RuntimeError("polynomial arena identifier ledger must be a list")
    if (
        arena.get("polynomial_id_to_sha256_digest_sha256")
        != POLYNOMIAL_ARENA_ID_TO_SHA256_DIGEST_SHA256
        or canonical_sha256(correspondence) != POLYNOMIAL_ARENA_ID_TO_SHA256_DIGEST_SHA256
        or arena.get("record_count") != 3161
        or arena.get("term_count_total") != 19119187
    ):
        raise RuntimeError("polynomial arena identifier ledger binding mismatch")

    by_id: dict[int, str] = {}
    for index, pair in enumerate(correspondence):
        if not isinstance(pair, list) or len(pair) != 2:
            raise RuntimeError(f"polynomial arena identifier ledger entry {index} is malformed")
        identifier = _require_int(pair[0], f"polynomial arena identifier ledger entry {index}")
        digest = _require_sha256(pair[1], f"polynomial arena identifier ledger entry {index}")
        if identifier in by_id:
            raise RuntimeError(f"duplicate polynomial arena identifier ledger id: {identifier}")
        by_id[identifier] = digest
    if len(by_id) != 3161:
        raise RuntimeError("polynomial arena identifier ledger record count mismatch")
    return by_id


def _validate_required_ids(value: object) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise RuntimeError("bounded-scoped subset required polynomial ids must be a list")
    identifiers = tuple(
        _require_int(identifier, f"bounded-scoped subset required id {index}")
        for index, identifier in enumerate(value)
    )
    if identifiers != REQUIRED_POLYNOMIAL_IDS:
        raise RuntimeError("bounded-scoped subset required polynomial ids mismatch")
    return identifiers


def _validate_subset_records(
    payload: Mapping[str, Any],
    root_by_id: Mapping[int, str],
) -> dict[int, dict[str, Any]]:
    _require_exact_keys(payload, _SUBSET_EXPECTED_KEYS, "bounded-scoped polynomial subset")
    if (
        payload.get("schema_version") != POLYNOMIAL_SUBSET_SCHEMA
        or payload.get("claim_boundary") != POLYNOMIAL_SUBSET_CLAIM_BOUNDARY
        or payload.get("root_semantic_digest_sha256") != ROOT_SEMANTIC_DIGEST_SHA256
        or payload.get("polynomial_arena_id_to_sha256_digest_sha256")
        != POLYNOMIAL_ARENA_ID_TO_SHA256_DIGEST_SHA256
        or payload.get("record_count") != len(REQUIRED_POLYNOMIAL_IDS)
        or payload.get("term_count_total") != CANDIDATE_ROW10_LOADED_TERM_COUNT
        or payload.get("records_canonical_sha256") != POLYNOMIAL_SUBSET_RECORDS_CANONICAL_SHA256
    ):
        raise RuntimeError("bounded-scoped polynomial subset metadata binding mismatch")
    _validate_required_ids(payload.get("required_polynomial_ids"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("bounded-scoped polynomial subset records must be a list")
    if canonical_sha256(records) != payload["records_canonical_sha256"]:
        raise RuntimeError("bounded-scoped polynomial subset canonical records digest mismatch")

    by_id: dict[int, dict[str, Any]] = {}
    term_count_total = 0
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise RuntimeError(f"bounded-scoped subset record {index} must be an object")
        _require_exact_keys(record, _RECORD_EXPECTED_KEYS, f"bounded-scoped subset record {index}")
        identifier = _require_int(
            record["polynomial_id"], f"bounded-scoped subset record {index} id"
        )
        digest = _require_sha256(record["sha256"], f"bounded-scoped subset record {identifier}")
        term_count = _require_int(
            record["term_count"],
            f"bounded-scoped subset record {identifier} term count",
        )
        terms = record["terms"]
        if not isinstance(terms, list):
            raise RuntimeError(f"bounded-scoped subset record {identifier} terms must be a list")
        if term_count != len(terms):
            raise RuntimeError(f"bounded-scoped subset record {identifier} term count mismatch")
        if canonical_sha256(terms) != digest:
            raise RuntimeError(f"bounded-scoped subset record {identifier} term digest mismatch")
        if root_by_id.get(identifier) != digest:
            raise RuntimeError(
                f"bounded-scoped subset record {identifier} root identifier/digest mismatch"
            )
        if identifier in by_id:
            raise RuntimeError(f"duplicate bounded-scoped subset polynomial id: {identifier}")
        by_id[identifier] = record
        term_count_total += term_count

    if tuple(by_id) != REQUIRED_POLYNOMIAL_IDS:
        raise RuntimeError("bounded-scoped subset records are not the required sorted id set")
    if len(by_id) != len(REQUIRED_POLYNOMIAL_IDS) or term_count_total != 2508:
        raise RuntimeError("bounded-scoped subset record or term count mismatch")
    return by_id


def load_polynomial_subset(
    repository_root: Path,
    root: Mapping[str, Any],
    needed: Iterable[int],
) -> tuple[dict[int, dict[str, Any]], int]:
    """Authenticate the subset fixture and return only the requested records."""

    root_by_id = _root_polynomial_digest_by_id(root)
    payload = _read_verified_fixture(
        repository_root / POLYNOMIAL_SUBSET_FIXTURE,
        POLYNOMIAL_SUBSET_RAW_SHA256,
        "bounded-scoped polynomial subset",
    )
    by_id = _validate_subset_records(payload, root_by_id)
    needed_ids = {
        _require_int(identifier, "requested bounded-scoped subset polynomial id")
        for identifier in needed
    }
    missing = sorted(needed_ids - set(by_id))
    if missing:
        raise RuntimeError(f"bounded-scoped subset is missing requested ids: {missing}")
    selected = {identifier: by_id[identifier] for identifier in sorted(needed_ids)}
    return selected, sum(int(record["term_count"]) for record in selected.values())


def build_bounded_polynomial_subset_fixture(
    records_by_id: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the exact fixture payload from authenticated full-arena records."""

    records: list[dict[str, Any]] = []
    for identifier in REQUIRED_POLYNOMIAL_IDS:
        record = records_by_id.get(identifier)
        if not isinstance(record, Mapping):
            raise RuntimeError(f"full arena extraction is missing polynomial id {identifier}")
        copied = dict(record)
        _require_exact_keys(
            copied,
            _RECORD_EXPECTED_KEYS,
            f"full arena extraction record {identifier}",
        )
        if copied["polynomial_id"] != identifier:
            raise RuntimeError(f"full arena extraction id mismatch for polynomial {identifier}")
        if canonical_sha256(copied["terms"]) != copied["sha256"]:
            raise RuntimeError(
                f"full arena extraction term digest mismatch for polynomial {identifier}"
            )
        if copied["term_count"] != len(copied["terms"]):
            raise RuntimeError(
                f"full arena extraction term count mismatch for polynomial {identifier}"
            )
        records.append(copied)
    if set(records_by_id) != set(REQUIRED_POLYNOMIAL_IDS):
        raise RuntimeError("full arena extraction has unsupported polynomial ids")
    term_count_total = sum(int(record["term_count"]) for record in records)
    if term_count_total != CANDIDATE_ROW10_LOADED_TERM_COUNT:
        raise RuntimeError("full arena extraction term total mismatch")
    payload = {
        "claim_boundary": POLYNOMIAL_SUBSET_CLAIM_BOUNDARY,
        "polynomial_arena_id_to_sha256_digest_sha256": (
            POLYNOMIAL_ARENA_ID_TO_SHA256_DIGEST_SHA256
        ),
        "record_count": len(records),
        "records": records,
        "records_canonical_sha256": canonical_sha256(records),
        "required_polynomial_ids": list(REQUIRED_POLYNOMIAL_IDS),
        "root_semantic_digest_sha256": ROOT_SEMANTIC_DIGEST_SHA256,
        "schema_version": POLYNOMIAL_SUBSET_SCHEMA,
        "term_count_total": term_count_total,
    }
    if payload["records_canonical_sha256"] != POLYNOMIAL_SUBSET_RECORDS_CANONICAL_SHA256:
        raise RuntimeError("full arena extraction records digest mismatch")
    return payload


def _local_polynomial_arena_chunk_paths(
    repository_root: Path,
    root: Mapping[str, Any],
) -> list[Path]:
    ledger = root.get("chunk_ledger")
    if not isinstance(ledger, Mapping) or not isinstance(ledger.get("chunks"), list):
        raise RuntimeError("bundle root has no usable chunk ledger")
    directory_value = ledger.get("directory")
    if not isinstance(directory_value, str):
        raise RuntimeError("bundle root chunk directory is malformed")
    directory = _safe_repository_path(repository_root, directory_value)
    paths: list[Path] = []
    for index, chunk in enumerate(ledger["chunks"]):
        if not isinstance(chunk, Mapping):
            raise RuntimeError(f"bundle root chunk ledger entry {index} is malformed")
        if chunk.get("arena") != "polynomial_arena":
            continue
        relative = chunk.get("path")
        if not isinstance(relative, str):
            raise RuntimeError(f"polynomial arena chunk path {index} is malformed")
        paths.append(_safe_repository_path(directory, relative))
    if not paths:
        raise RuntimeError("bundle root has no polynomial arena chunks")
    return paths


def verify_local_polynomial_arena_mirror(
    repository_root: Path,
    root: Mapping[str, Any],
    records: Mapping[int, Mapping[str, Any]],
    loaded_terms: int,
    needed: Iterable[int],
) -> bool:
    """Check a present full arena as an unused, authenticated mirror.

    A clone without all arena chunks succeeds with the bounded fixture alone.
    If any local full-arena chunk is present, every chunk is required and the
    legacy authenticated scanner must reproduce exactly the subset records.
    """

    needed_ids = {
        _require_int(identifier, "requested bounded-scoped subset polynomial id")
        for identifier in needed
    }
    if set(records) != needed_ids:
        raise RuntimeError("bounded-scoped subset mirror records do not match requested ids")
    if loaded_terms != sum(int(record["term_count"]) for record in records.values()):
        raise RuntimeError("bounded-scoped subset mirror term count mismatch")
    chunk_paths = _local_polynomial_arena_chunk_paths(repository_root, root)
    present = [path.exists() for path in chunk_paths]
    if not any(present):
        return False
    if not all(present):
        missing = [
            str(path) for path, exists in zip(chunk_paths, present, strict=True) if not exists
        ]
        raise RuntimeError(f"incomplete local polynomial-arena mirror: {missing[:4]}")
    if not all(path.is_file() for path in chunk_paths):
        raise RuntimeError("local polynomial-arena mirror contains a non-file chunk")

    from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker

    mirror_records, mirror_terms = worker._scan_needed_records(
        repository_root,
        root,
        needed_ids,
        worker.Emitter(),
    )
    if mirror_terms != loaded_terms:
        raise RuntimeError("local polynomial-arena mirror term count differs from subset")
    ordered_ids = sorted(needed_ids)
    if canonical_sha256(
        [mirror_records[identifier] for identifier in ordered_ids]
    ) != canonical_sha256([records[identifier] for identifier in ordered_ids]):
        raise RuntimeError("local polynomial-arena mirror records differ from subset")
    return True


def deterministic_basis_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only mathematical basis fields into a certificate core."""

    keys = (
        "basis_digest_sha256",
        "basis_size",
        "basis_term_count",
        "largest_basis_polynomial_terms",
        "is_unit_ideal",
    )
    missing = [key for key in keys if key not in summary]
    if missing:
        raise RuntimeError(f"basis summary has no deterministic fields: {missing}")
    return {key: summary[key] for key in keys}


def runtime_basis_observation(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Copy runtime-only basis observations outside the certificate core."""

    keys = ("groebner_seconds", "saturation_seconds")
    missing = [key for key in keys if key not in summary]
    if missing:
        raise RuntimeError(f"basis summary has no runtime fields: {missing}")
    return {key: summary[key] for key in keys}


def _reject_runtime_observation_fields(value: object, location: str = "certificate core") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise RuntimeError(f"{location} has a non-string object key")
            if key in _RUNTIME_OBSERVATION_KEYS:
                raise RuntimeError(
                    f"{location} contains runtime-observation field {key!r}; "
                    "move it to runtime_observation"
                )
            _reject_runtime_observation_fields(nested, f"{location}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_runtime_observation_fields(nested, f"{location}[{index}]")


def certificate_core_digest(certificate_core: Mapping[str, Any]) -> str:
    """Hash a deterministic core after rejecting all timing/resource observations."""

    if "certificate_core_digest_sha256" in certificate_core:
        raise RuntimeError("unbound certificate core must not contain its digest")
    _reject_runtime_observation_fields(certificate_core)
    return canonical_sha256(certificate_core)


def bind_certificate_core(certificate_core: Mapping[str, Any]) -> dict[str, Any]:
    """Return a self-describing deterministic certificate core."""

    bound = dict(certificate_core)
    bound["certificate_core_digest_sha256"] = certificate_core_digest(certificate_core)
    return bound


def verify_bound_certificate_core(certificate_core: Mapping[str, Any]) -> None:
    """Verify that a core's digest excludes itself and runtime observations."""

    _require_sha256(
        certificate_core.get("certificate_core_digest_sha256"),
        "certificate core digest",
    )
    unbound = {
        key: value
        for key, value in certificate_core.items()
        if key != "certificate_core_digest_sha256"
    }
    if certificate_core_digest(unbound) != certificate_core["certificate_core_digest_sha256"]:
        raise RuntimeError("certificate core digest mismatch")
