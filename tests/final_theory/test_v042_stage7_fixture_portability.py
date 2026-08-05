"""Sage-free portability and provenance tests for the bounded v0.4.2 U2 scouts."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from universe_lab.final_theory import (
    sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042 as fixtures,
)
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker

ROOT = Path(__file__).resolve().parents[2]
ATTEMPTS_RELATIVE = Path("results/v0.4.2_sr2v_q5_free_auxiliary_ideal_supervised/attempts")
SCOUT_PATHS = {
    "row185": ROOT / "scripts/reproduce_v042_row185_normal_form_scout.py",
    "candidate": ROOT / "scripts/reproduce_v042_candidate_minor_only_scout.py",
}
PORTABLE_INPUTS = (
    Path("compose.yaml"),
    Path("uv.lock"),
    Path("results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.json"),
    fixtures.STAGE7_REQUEST_FIXTURE,
    fixtures.STAGE7_RESULT_FIXTURE,
    fixtures.POLYNOMIAL_SUBSET_FIXTURE,
    fixtures.SCOUT_REPRODUCTION_MANIFEST,
    fixtures.SCOUT_EXPECTATIONS,
    Path("scripts/extract_v042_bounded_scout_polynomial_subset.py"),
    Path("scripts/reproduce_v042_candidate_minor_only_scout.py"),
    Path("scripts/reproduce_v042_row185_normal_form_scout.py"),
    Path("src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042.py"),
    Path("src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_worker_v042.py"),
)


def _load_scout(name: str, path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(f"test_{name}_stage7_fixture", path)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


SCOUTS = tuple(_load_scout(name, path) for name, path in SCOUT_PATHS.items())


def _copy_portable_inputs(repository_root: Path) -> None:
    """Build a clone-shaped tree without attempts or arena chunks."""

    for relative in PORTABLE_INPUTS:
        target = repository_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def _fixture_bytes(repository_root: Path) -> tuple[bytes, bytes]:
    return (
        (repository_root / fixtures.STAGE7_REQUEST_FIXTURE).read_bytes(),
        (repository_root / fixtures.STAGE7_RESULT_FIXTURE).read_bytes(),
    )


def _write_local_attempt(
    repository_root: Path,
    name: str,
    request_bytes: bytes,
    result_bytes: bytes,
) -> None:
    attempt = repository_root / ATTEMPTS_RELATIVE / name / "attempt"
    attempt.mkdir(parents=True)
    (attempt / "request.json").write_bytes(request_bytes)
    (attempt / "result.json").write_bytes(result_bytes)


def _load_root(repository_root: Path) -> dict[str, Any]:
    request_path, _prior_result = fixtures.find_stage7_request(repository_root)
    request = worker.load_verified_request(request_path)
    return worker.load_verified_root(repository_root, request)


def _write_canonical_json(path: Path, payload: object) -> bytes:
    raw = fixtures.canonical_json_bytes(payload) + b"\n"
    path.write_bytes(raw)
    return raw


@pytest.mark.parametrize("scout", SCOUTS, ids=tuple(SCOUT_PATHS))
def test_tracked_stage7_fixture_selection_and_binding(scout: Any) -> None:
    request_path, prior_result = scout._find_stage7_request(ROOT)
    assert request_path == ROOT / scout._STAGE7_REQUEST_FIXTURE
    assert hashlib.sha256(request_path.read_bytes()).hexdigest() == scout._STAGE7_REQUEST_RAW_SHA256
    assert (
        hashlib.sha256((ROOT / scout._STAGE7_RESULT_FIXTURE).read_bytes()).hexdigest()
        == scout._STAGE7_RESULT_RAW_SHA256
    )
    request = json.loads(request_path.read_bytes())
    assert scout._is_canonical_stage7_result(prior_result)
    assert prior_result["fingerprint_sha256"] == fixtures.STAGE7_FINGERPRINT_SHA256
    assert prior_result["details"]["request_payload_sha256"] == request["payload_digest_sha256"]
    assert request["payload"]["selected_entry_indices"] == [8, 9, 97, 98, 327, 328, 31]
    assert scout._canonical(prior_result) == (
        "3241c5ff07eb476da4ff0541e797a353f466cafeae72d0e901ec1a8ccc4e9434"
    )


def test_fresh_clone_validates_all_bounded_scout_inputs_without_sage(tmp_path: Path) -> None:
    _copy_portable_inputs(tmp_path)
    assert not (tmp_path / ATTEMPTS_RELATIVE).exists()
    assert not list(tmp_path.rglob("polynomial_arena.*.jsonl.gz"))

    manifest = fixtures.validate_bounded_scout_reproduction_inputs(tmp_path)
    root = _load_root(tmp_path)

    assert manifest["input_mode"] == fixtures.SCOUT_INPUT_MODE
    assert root["semantic_digest_sha256"] == fixtures.ROOT_SEMANTIC_DIGEST_SHA256
    expectations = fixtures.load_bounded_scout_expectations(
        tmp_path,
        manifest["semantic_digest_sha256"],
    )
    assert expectations["status"] == fixtures.SCOUT_EXPECTATIONS_PINNED
    assert expectations["certificate_core_digests"] == {
        "candidate_minor_only": (
            "cb9252dbc9d1610d3d0410f0d8f111a862b341cee59a4ced20bb8527c66a1c87"
        ),
        "row185_normal_form": ("bd2d390ea996ea5149578bb569d6bba98fecbcb96b1b00d0fe8ff7b365f00deb"),
    }
    assert (
        fixtures.verify_scout_certificate_core_expectation(
            tmp_path,
            manifest,
            "row185_normal_form",
            expectations["certificate_core_digests"]["row185_normal_form"],
        )["status"]
        == fixtures.SCOUT_EXPECTATIONS_PINNED
    )
    assert (
        fixtures.normalized_lf_sha256(
            tmp_path / "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_worker_v042.py"
        )
        == manifest["source_normalized_lf_sha256"][
            "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_worker_v042.py"
        ]
    )


@pytest.mark.parametrize(
    ("needed", "expected_count", "expected_terms"),
    (
        (
            fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
            len(fixtures.ROW185_NEEDED_POLYNOMIAL_IDS),
            fixtures.ROW185_LOADED_TERM_COUNT,
        ),
        (
            fixtures.CANDIDATE_ROW10_NEEDED_POLYNOMIAL_IDS,
            len(fixtures.CANDIDATE_ROW10_NEEDED_POLYNOMIAL_IDS),
            fixtures.CANDIDATE_ROW10_LOADED_TERM_COUNT,
        ),
    ),
    ids=("row185", "candidate_row10"),
)
def test_bounded_scout_needed_sets_select_only_fixture_records(
    tmp_path: Path,
    needed: frozenset[int],
    expected_count: int,
    expected_terms: int,
) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    records, loaded_terms = fixtures.load_polynomial_subset(tmp_path, root, needed)

    assert set(records) == set(needed)
    assert len(records) == expected_count
    assert loaded_terms == expected_terms


def test_fresh_clone_skips_absent_full_arena_mirror(tmp_path: Path) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    records, loaded_terms = fixtures.load_polynomial_subset(
        tmp_path,
        root,
        fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
    )

    assert not fixtures.verify_local_polynomial_arena_mirror(
        tmp_path,
        root,
        records,
        loaded_terms,
        fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
    )


def test_partial_full_arena_mirror_is_rejected(tmp_path: Path) -> None:
    """One local legacy chunk is an incomplete mirror, not a clone shortcut."""

    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    records, loaded_terms = fixtures.load_polynomial_subset(
        tmp_path,
        root,
        fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
    )
    partial_chunk = fixtures._local_polynomial_arena_chunk_paths(tmp_path, root)[0]
    partial_chunk.parent.mkdir(parents=True, exist_ok=True)
    partial_chunk.write_bytes(b"incomplete mirror placeholder")

    with pytest.raises(RuntimeError, match="incomplete local polynomial-arena mirror"):
        fixtures.verify_local_polynomial_arena_mirror(
            tmp_path,
            root,
            records,
            loaded_terms,
            fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
        )


def test_present_full_arena_is_authenticated_subset_mirror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    records, loaded_terms = fixtures.load_polynomial_subset(
        tmp_path,
        root,
        fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
    )
    for path in fixtures._local_polynomial_arena_chunk_paths(tmp_path, root):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test mirror placeholder")

    def mirror_scan(
        repository_root: Path,
        authenticated_root: dict[str, Any],
        needed: set[int],
        emitter: object,
    ) -> tuple[dict[int, dict[str, Any]], int]:
        assert repository_root == tmp_path
        assert authenticated_root == root
        assert needed == fixtures.ROW185_NEEDED_POLYNOMIAL_IDS
        del emitter
        return dict(records), loaded_terms

    monkeypatch.setattr(worker, "_scan_needed_records", mirror_scan)
    assert fixtures.verify_local_polynomial_arena_mirror(
        tmp_path,
        root,
        records,
        loaded_terms,
        fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
    )


def test_present_full_arena_mirror_difference_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    records, loaded_terms = fixtures.load_polynomial_subset(
        tmp_path,
        root,
        fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
    )
    for path in fixtures._local_polynomial_arena_chunk_paths(tmp_path, root):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test mirror placeholder")
    mismatched_records = copy.deepcopy(records)
    mismatched_records[1]["terms"][0][1] = 2

    def mirror_scan(
        repository_root: Path,
        authenticated_root: dict[str, Any],
        needed: set[int],
        emitter: object,
    ) -> tuple[dict[int, dict[str, Any]], int]:
        del repository_root, authenticated_root, needed, emitter
        return mismatched_records, loaded_terms

    monkeypatch.setattr(worker, "_scan_needed_records", mirror_scan)
    with pytest.raises(RuntimeError, match="mirror records differ"):
        fixtures.verify_local_polynomial_arena_mirror(
            tmp_path,
            root,
            records,
            loaded_terms,
            fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
        )


def test_subset_builder_round_trips_the_tracked_fixture(tmp_path: Path) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    records, _loaded_terms = fixtures.load_polynomial_subset(
        tmp_path,
        root,
        fixtures.CANDIDATE_ROW10_NEEDED_POLYNOMIAL_IDS,
    )

    expected = (
        fixtures.canonical_json_bytes(fixtures.build_bounded_polynomial_subset_fixture(records))
        + b"\n"
    )
    assert expected == (tmp_path / fixtures.POLYNOMIAL_SUBSET_FIXTURE).read_bytes()


def test_subset_raw_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    subset_path = tmp_path / fixtures.POLYNOMIAL_SUBSET_FIXTURE
    subset_path.write_bytes(subset_path.read_bytes() + b" ")

    with pytest.raises(RuntimeError, match="subset fixture SHA-256 mismatch"):
        fixtures.load_polynomial_subset(
            tmp_path,
            root,
            fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
        )


def test_subset_canonical_records_hash_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    subset_path = tmp_path / fixtures.POLYNOMIAL_SUBSET_FIXTURE
    subset = json.loads(subset_path.read_bytes())
    subset["records"][0]["terms"][0][1] = 2
    raw = _write_canonical_json(subset_path, subset)
    monkeypatch.setattr(fixtures, "POLYNOMIAL_SUBSET_RAW_SHA256", hashlib.sha256(raw).hexdigest())

    with pytest.raises(RuntimeError, match="canonical records digest mismatch"):
        fixtures.load_polynomial_subset(
            tmp_path,
            root,
            fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
        )


def test_subset_record_root_binding_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_portable_inputs(tmp_path)
    root = _load_root(tmp_path)
    subset_path = tmp_path / fixtures.POLYNOMIAL_SUBSET_FIXTURE
    subset = json.loads(subset_path.read_bytes())
    altered_record = subset["records"][0]
    altered_record["terms"][0][1] = 2
    altered_record["sha256"] = fixtures.canonical_sha256(altered_record["terms"])
    subset["records_canonical_sha256"] = fixtures.canonical_sha256(subset["records"])
    raw = _write_canonical_json(subset_path, subset)
    monkeypatch.setattr(fixtures, "POLYNOMIAL_SUBSET_RAW_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(
        fixtures,
        "POLYNOMIAL_SUBSET_RECORDS_CANONICAL_SHA256",
        subset["records_canonical_sha256"],
    )

    with pytest.raises(RuntimeError, match="root identifier/digest mismatch"):
        fixtures.load_polynomial_subset(
            tmp_path,
            root,
            fixtures.ROW185_NEEDED_POLYNOMIAL_IDS,
        )


@pytest.mark.parametrize("scout", SCOUTS, ids=tuple(SCOUT_PATHS))
def test_matching_local_stage7_attempt_is_only_a_checked_mirror(
    tmp_path: Path,
    scout: Any,
) -> None:
    _copy_portable_inputs(tmp_path)
    request_bytes, result_bytes = _fixture_bytes(tmp_path)
    _write_local_attempt(tmp_path, "matching", request_bytes, result_bytes)
    request_path, prior_result = scout._find_stage7_request(tmp_path)
    assert request_path == tmp_path / scout._STAGE7_REQUEST_FIXTURE
    assert prior_result == json.loads(result_bytes)


@pytest.mark.parametrize("scout", SCOUTS, ids=tuple(SCOUT_PATHS))
def test_local_stage7_mismatch_is_rejected(tmp_path: Path, scout: Any) -> None:
    _copy_portable_inputs(tmp_path)
    request_bytes, result_bytes = _fixture_bytes(tmp_path)
    mismatched_result = json.loads(result_bytes)
    mismatched_result["attempt_id"] = "local-mismatch"
    altered_bytes = _write_canonical_json(tmp_path / "altered-result.json", mismatched_result)
    _write_local_attempt(tmp_path, "mismatch", request_bytes, altered_bytes)

    with pytest.raises(RuntimeError, match="local stage-7 result differs"):
        scout._find_stage7_request(tmp_path)


@pytest.mark.parametrize("scout", SCOUTS, ids=tuple(SCOUT_PATHS))
def test_multiple_local_stage7_candidates_are_rejected(tmp_path: Path, scout: Any) -> None:
    _copy_portable_inputs(tmp_path)
    request_bytes, result_bytes = _fixture_bytes(tmp_path)
    _write_local_attempt(tmp_path, "first", request_bytes, result_bytes)
    _write_local_attempt(tmp_path, "second", request_bytes, result_bytes)

    with pytest.raises(RuntimeError, match="ambiguous local canonical stage-7 attempts: 2"):
        scout._find_stage7_request(tmp_path)


def test_reproduction_manifest_rejects_source_drift(tmp_path: Path) -> None:
    _copy_portable_inputs(tmp_path)
    drifted = tmp_path / "scripts/reproduce_v042_candidate_minor_only_scout.py"
    drifted.write_bytes(drifted.read_bytes() + b"\n# source drift\n")

    with pytest.raises(RuntimeError, match="source hash mismatch"):
        fixtures.validate_bounded_scout_reproduction_inputs(tmp_path)


def test_candidate_scout_rejects_nonfixed_source_before_input_or_sage_loading(
    tmp_path: Path,
) -> None:
    candidate_scout = SCOUTS[1]
    with pytest.raises(RuntimeError, match="fixed to the cost-next source row 10"):
        candidate_scout.run(tmp_path, candidate_source=11)


def test_candidate_scout_rejects_a_live_basis_cap_before_core_construction() -> None:
    candidate_scout = SCOUTS[1]

    with pytest.raises(
        RuntimeError,
        match="candidate differential minor ideal exceeded the live basis cap",
    ):
        candidate_scout._require_complete_basis({"limit_exceeded": True})


def test_compose_pins_both_sage_services_to_the_authenticated_digest() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    qualified_image = (
        "image: sagemath/sagemath:10.9@sha256:"
        "e068670ae5863b54b2550e72437ec637b0283acb0dc712c8584c124dbf44e667"
    )

    assert compose.count(qualified_image) == 2


def test_pinned_expectation_rejects_a_core_digest_mismatch(tmp_path: Path) -> None:
    _copy_portable_inputs(tmp_path)
    manifest = fixtures.validate_bounded_scout_reproduction_inputs(tmp_path)
    expectations_path = tmp_path / fixtures.SCOUT_EXPECTATIONS
    expectations = json.loads(expectations_path.read_bytes())
    expectations["status"] = fixtures.SCOUT_EXPECTATIONS_PINNED
    expectations["certificate_core_digests"] = {
        "candidate_minor_only": "a" * 64,
        "row185_normal_form": "b" * 64,
    }
    _write_canonical_json(
        expectations_path,
        {
            **expectations,
            "semantic_digest_sha256": fixtures.canonical_sha256(
                {
                    key: value
                    for key, value in expectations.items()
                    if key != "semantic_digest_sha256"
                }
            ),
        },
    )

    with pytest.raises(RuntimeError, match="certificate core digest mismatch"):
        fixtures.verify_scout_certificate_core_expectation(
            tmp_path,
            manifest,
            "row185_normal_form",
            "c" * 64,
        )


def _sample_certificate_core() -> dict[str, Any]:
    return {
        "schema_version": "test-certificate-core-v1",
        "selected_rows": [8, 97, 185],
        "polynomial_digests": {"A": "a" * 64, "B": "b" * 64},
        "normal_forms": {"A": {"is_zero": False, "sha256": "c" * 64}},
        "basis": {
            "basis_digest_sha256": "d" * 64,
            "basis_size": 4,
            "basis_term_count": 1215,
            "is_unit_ideal": False,
        },
    }


def test_certificate_core_digest_excludes_runtime_observation() -> None:
    core = _sample_certificate_core()
    first = fixtures.bind_certificate_core(core)
    runtime_one = {"elapsed_seconds": 1.0, "basis": {"groebner_seconds": 0.5}}
    runtime_two = {"elapsed_seconds": 999.0, "basis": {"groebner_seconds": 888.0}}

    assert runtime_one != runtime_two
    assert first["certificate_core_digest_sha256"] == fixtures.certificate_core_digest(core)
    assert (
        first["certificate_core_digest_sha256"]
        == fixtures.bind_certificate_core(core)["certificate_core_digest_sha256"]
    )
    fixtures.verify_bound_certificate_core(first)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("selected_rows",), [8, 97, 186]),
        (("polynomial_digests", "A"), "e" * 64),
        (("normal_forms", "A", "is_zero"), True),
        (("basis", "basis_digest_sha256"), "f" * 64),
    ),
    ids=("selected_rows", "polynomial_digest", "normal_form", "basis"),
)
def test_certificate_core_digest_changes_with_deterministic_evidence(
    path: tuple[str, ...],
    value: object,
) -> None:
    original = _sample_certificate_core()
    changed = copy.deepcopy(original)
    cursor: dict[str, Any] = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value

    assert fixtures.certificate_core_digest(original) != fixtures.certificate_core_digest(changed)


@pytest.mark.parametrize(
    "core",
    (
        {"elapsed_seconds": 1.0},
        {"basis": {"groebner_seconds": 1.0}},
        {"nested": [{"saturation_seconds": 1.0}]},
        {"runtime_observation": {"elapsed_seconds": 1.0}},
    ),
)
def test_certificate_core_rejects_runtime_keys(core: dict[str, Any]) -> None:
    with pytest.raises(RuntimeError, match="runtime-observation field"):
        fixtures.certificate_core_digest(core)
