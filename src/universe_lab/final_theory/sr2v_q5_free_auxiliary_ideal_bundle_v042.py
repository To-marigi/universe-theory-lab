"""Two-tier freeze for the SR2-V Q5-free auxiliary-ideal Phase-A manifest.

The complete Phase-A payload is far too large to track in Git as one pretty
JSON object.  This module splits it in two:

* a small **root manifest** that Git tracks -- ordered per-row digests, the
  arena ``polynomial_id -> sha256`` correspondence, the six chart generator
  identifier tables, the predecessor/code/ring bindings, the chunk ledger, and
  the digest of the full logical payload;
* the two coefficient **arenas**, written outside Git as compact canonical
  JSONL split into fixed-size chunks and compressed with deterministic gzip.

The mathematical authority is the uncompressed canonical byte stream: every
chunk records both the uncompressed and the gzip digest, and the compressed
digest exists only to detect transport damage.

Writing the root and the chunks is a digest commitment, nothing more, and it
carries ``FULL_BUILD_DIGEST_OBSERVED_UNFROZEN_NONTERMINAL``.  Only a verifier
run that streams every chunk *and* independently recompiles the 1,127 rows --
source and pivot rebuild, the Schur identities, Q5 and spectator vanishing,
denominator clearing with its inverse reconstruction, the six chart manifests,
the six frozen rational cross-check points, and the code binding the root was
produced from -- may raise the verdict, and then only if every entry of
``REQUIRED_RECOMPILATION_CHECKS`` is present and true.  A failing check, a
missing chunk or any digest mismatch drops it to ``OPEN_ARTIFACT_INCOMPLETE``;
an absent check leaves it unfrozen rather than counting as a pass.

The frozen verdict names what is actually retained: the arenas plus digest
commitments to the rest, not every byte of the logical payload.

No Groebner basis, saturation, unit ideal, commutativity theorem, counterexample
or SR2-V terminal is claimed here.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import subprocess
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_manifest_v042 as manifest

ROOT_RESULT_PATH = "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.json"
ROOT_REPORT_PATH = "reports/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.md"
BUNDLE_DIRECTORY = "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle"

SCHEMA = "final-theory-v042-sr2v-q5-free-auxiliary-ideal-bundle-root-v1"

#: The bundle stores the arenas and commits to the rest by digest; it does not
#: retain every byte of the full manifest.  The verdict says exactly that.
FROZEN_VERDICT = (
    "SR2V_Q5_FREE_AUXILIARY_IDEAL_FULL_MANIFEST_DIGEST_AND_SOLVER_INPUTS_FROZEN_NO_SOLVER_RUN"
)
OBSERVED_VERDICT = "FULL_BUILD_DIGEST_OBSERVED_UNFROZEN_NONTERMINAL"
INCOMPLETE_VERDICT = "OPEN_ARTIFACT_INCOMPLETE"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_NO_GROEBNER_OR_UNIT_IDEAL_CERTIFICATE"

#: Every one of these must be present and True before the frozen verdict is
#: reachable.  Adding a check here makes older verification records unfreezable
#: until they are re-run, which is the intended direction of failure.
REQUIRED_RECOMPILATION_CHECKS = (
    "arena_correspondence",
    "chart_generator_tables_digest",
    "code_binding_hashes",
    "compiler_payload_passed",
    "cross_check_digest",
    "denominator_audit_digest",
    "full_logical_payload_digest",
    "ring_binding",
    "row_index_digest",
    "streamed_arena_matches_recompiled_arena",
)

#: Uncompressed canonical bytes per chunk.  Chunks are closed at the first
#: record that would exceed this, so a single record is never split.
CHUNK_TARGET_BYTES = 256 * 1024 * 1024
GZIP_LEVEL = 6
GZIP_MTIME = 0
CODEC = "gzip"
CANONICALIZATION = (
    "one record per line, "
    "json.dumps(ensure_ascii=True, sort_keys=True, separators=(',', ':')), "
    "UTF-8, LF terminated"
)

ARENA_NAMES = ("localized_coefficient_arena", "polynomial_arena")

COMPILER_MODULE_PATH = "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_manifest_v042.py"
BUNDLE_MODULE_PATH = "src/universe_lab/final_theory/sr2v_q5_free_auxiliary_ideal_bundle_v042.py"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def semantic_digest(payload: Mapping[str, Any]) -> str:
    return _digest(
        {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    )


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _normalised_text_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _code_commit(root: Path) -> str:
    """Record the commit the bundle was produced from, or that it was dirty."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            check=True,
            text=True,
        )
        if completed.stdout.strip():
            return "UNCOMMITTED_WORKTREE"
        revision = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "GIT_UNAVAILABLE"
    return revision.stdout.strip()


@dataclass(frozen=True)
class ChunkRecord:
    """Everything needed to re-derive and re-check one compressed chunk."""

    arena: str
    chunk_index: int
    path: str
    first_polynomial_id: int
    last_polynomial_id: int
    record_count: int
    uncompressed_bytes: int
    uncompressed_sha256: str
    gzip_bytes: int
    gzip_sha256: str

    def as_json(self) -> dict[str, Any]:
        return {
            "arena": self.arena,
            "chunk_index": self.chunk_index,
            "path": self.path,
            "first_polynomial_id": self.first_polynomial_id,
            "last_polynomial_id": self.last_polynomial_id,
            "record_count": self.record_count,
            "uncompressed_bytes": self.uncompressed_bytes,
            "uncompressed_sha256": self.uncompressed_sha256,
            "gzip_bytes": self.gzip_bytes,
            "gzip_sha256": self.gzip_sha256,
            "codec": CODEC,
            "codec_level": GZIP_LEVEL,
            "codec_mtime": GZIP_MTIME,
            "canonicalization": CANONICALIZATION,
            "authoritative_digest": "uncompressed_sha256",
        }


def _chunk_name(arena: str, index: int) -> str:
    return f"{arena}.{index:04d}.jsonl.gz"


def _compress(payload: bytes) -> bytes:
    """Deterministic gzip: no embedded filename, fixed mtime, fixed level."""

    buffer = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=buffer,
        compresslevel=GZIP_LEVEL,
        mtime=GZIP_MTIME,
    ) as handle:
        handle.write(payload)
    return buffer.getvalue()


def write_arena_chunks(
    directory: Path,
    arena: str,
    records: Sequence[Mapping[str, Any]],
    *,
    target_bytes: int = CHUNK_TARGET_BYTES,
) -> list[ChunkRecord]:
    """Serialise one arena to deterministic gzip chunks of canonical JSONL."""

    directory.mkdir(parents=True, exist_ok=True)
    chunks: list[ChunkRecord] = []
    buffer = bytearray()
    first_id: int | None = None
    last_id: int | None = None
    count = 0

    def flush() -> None:
        nonlocal buffer, first_id, last_id, count
        if not count:
            return
        if first_id is None or last_id is None:
            raise AssertionError("chunk identifier range was not tracked")
        raw = bytes(buffer)
        compressed = _compress(raw)
        name = _chunk_name(arena, len(chunks))
        (directory / name).write_bytes(compressed)
        chunks.append(
            ChunkRecord(
                arena=arena,
                chunk_index=len(chunks),
                path=name,
                first_polynomial_id=first_id,
                last_polynomial_id=last_id,
                record_count=count,
                uncompressed_bytes=len(raw),
                uncompressed_sha256=hashlib.sha256(raw).hexdigest(),
                gzip_bytes=len(compressed),
                gzip_sha256=hashlib.sha256(compressed).hexdigest(),
            )
        )
        buffer = bytearray()
        first_id = None
        last_id = None
        count = 0

    expected_id = 0
    for record in records:
        identifier = int(record["polynomial_id"])
        if identifier != expected_id:
            raise AssertionError(f"{arena} identifiers are not contiguous at {identifier}")
        expected_id += 1
        line = (_canonical_json(record) + "\n").encode("utf-8")
        if count and len(buffer) + len(line) > target_bytes:
            flush()
        if first_id is None:
            first_id = identifier
        buffer.extend(line)
        last_id = identifier
        count += 1
    flush()
    return chunks


def read_arena_chunks(
    directory: Path,
    chunks: Iterable[Mapping[str, Any]],
) -> Iterator[dict[str, Any]]:
    """Stream records back, checking both digests before yielding any of them.

    The uncompressed digest is the authority; the gzip digest is checked first
    so transport damage is reported as such rather than as a canonical-byte
    mismatch.
    """

    for chunk in chunks:
        path = directory / str(chunk["path"])
        if not path.is_file():
            raise FileNotFoundError(f"missing bundle chunk: {path}")
        compressed = path.read_bytes()
        if len(compressed) != int(chunk["gzip_bytes"]):
            raise ValueError(f"{chunk['path']}: gzip byte count does not match the ledger")
        if hashlib.sha256(compressed).hexdigest() != str(chunk["gzip_sha256"]):
            raise ValueError(f"{chunk['path']}: gzip digest does not match the ledger")
        raw = gzip.decompress(compressed)
        if len(raw) != int(chunk["uncompressed_bytes"]):
            raise ValueError(f"{chunk['path']}: uncompressed byte count does not match the ledger")
        if hashlib.sha256(raw).hexdigest() != str(chunk["uncompressed_sha256"]):
            raise ValueError(f"{chunk['path']}: uncompressed digest does not match the ledger")
        lines = raw.decode("utf-8").splitlines()
        if len(lines) != int(chunk["record_count"]):
            raise ValueError(f"{chunk['path']}: record count does not match the ledger")
        for line in lines:
            yield json.loads(line)


def _arena_index(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    correspondence = [[int(record["polynomial_id"]), str(record["sha256"])] for record in records]
    return {
        "record_count": len(records),
        "term_count_total": sum(int(record["term_count"]) for record in records),
        "polynomial_id_to_sha256": correspondence,
        "polynomial_id_to_sha256_digest_sha256": _digest(correspondence),
    }


def _row_index(payload: Mapping[str, Any]) -> dict[str, Any]:
    ledger = payload["Schur_reconstruction"]["ledger"]
    rows = [
        {
            "joint_source": record["joint_source"],
            "row_id": record["row_id"],
            "block": record["block"],
            "source_row_sha256": record["source_row_sha256"],
            "pivot_combination_sha256": record["pivot_combination_sha256"],
            "pivot_combination_nonzero_count": record["pivot_combination_nonzero_count"],
            "Schur_row_sha256": record["Schur_row_sha256"],
            "Schur_Q1_Q4_polynomial_ids": record["Schur_Q1_Q4_polynomial_ids"],
        }
        for record in ledger
    ]
    return {
        "row_count": len(rows),
        "ordered_rows": rows,
        "ordered_rows_digest_sha256": _digest(rows),
        "ledger_digest_sha256": payload["Schur_reconstruction"]["ledger_digest_sha256"],
    }


def _chart_generator_ids(payload: Mapping[str, Any]) -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for name, chart in payload["non_aligned_charts"].items():
        tables[name] = {
            "chart_polynomial": chart["chart_polynomial"],
            "generator_count": chart["generator_count_from_full_M0"],
            "planned_Rabinowitsch_localization_polynomial_id": chart[
                "planned_Rabinowitsch_localization_polynomial_id"
            ],
            "generator_polynomial_ids": [
                [
                    generator["joint_source"],
                    generator["cleared_coefficient_polynomial_ids"]["A"],
                    generator["cleared_coefficient_polynomial_ids"]["B"],
                ]
                for generator in chart["generators"]
            ],
            "generator_manifest_sha256": chart["generator_manifest_sha256"],
            "chart_manifest_sha256": chart["chart_manifest_sha256"],
        }
    for name, chart in payload["aligned_obstruction_charts"].items():
        tables[name] = {
            "normalised_obstruction_coordinate": chart["normalised_obstruction_coordinate"],
            "generator_count": chart["generator_count_from_full_M0"],
            "planned_Rabinowitsch_localization_polynomial_id": chart[
                "planned_Rabinowitsch_localization_polynomial_id"
            ],
            "auxiliary_variables": chart["auxiliary_variables"],
            "generator_polynomial_ids": [
                [
                    generator["joint_source"],
                    *(
                        generator["auxiliary_coefficients"][key]
                        for key in sorted(generator["auxiliary_coefficients"])
                    ),
                ]
                for generator in chart["generators"]
            ],
            "generator_auxiliary_key_order": sorted(
                chart["generators"][0]["auxiliary_coefficients"]
            )
            if chart["generators"]
            else [],
            "generator_manifest_sha256": chart["generator_manifest_sha256"],
            "chart_manifest_sha256": chart["chart_manifest_sha256"],
        }
    return {
        "chart_count": len(tables),
        "charts": tables,
        "charts_digest_sha256": _digest(tables),
    }


def _ring_binding(payload: Mapping[str, Any]) -> dict[str, Any]:
    base = payload["base_ring"]
    return {
        "active_ring": base["active_ring"],
        "bottom_coefficient_ring": base["bottom_coefficient_ring"],
        "initial_dimension": base["initial_dimension"],
        "active_dimension": base["active_dimension"],
        "active_variables": base["active_variables"],
        "active_variable_digest_sha256": base["active_variable_digest_sha256"],
        "localized_arena_upper_variable_order": payload["localized_coefficient_arena"][
            "upper_Laurent_variable_order"
        ],
        "localized_arena_bottom_variables": payload["localized_coefficient_arena"][
            "bottom_coefficient_variables"
        ],
        "polynomial_arena_variable_order": payload["polynomial_arena"]["variable_order"],
        "polynomial_arena_ring": payload["polynomial_arena"]["ring"],
        "bottom_localization_factor_count": base["bottom_localization_ledger"]["factor_count"],
        "bottom_localization_factor_ledger_sha256": base["bottom_localization_ledger"][
            "factor_ledger_sha256"
        ],
        "pure_Laurent_52_torus_claimed": base["pure_Laurent_52_torus_claimed"],
    }


def _code_binding(root: Path, *, code_commit: str) -> dict[str, Any]:
    uv_lock = root / "uv.lock"
    return {
        "code_commit": code_commit,
        "compiler_module": COMPILER_MODULE_PATH,
        "compiler_module_normalised_LF_sha256": _normalised_text_digest(
            root / COMPILER_MODULE_PATH
        ),
        "bundle_module": BUNDLE_MODULE_PATH,
        "bundle_module_normalised_LF_sha256": _normalised_text_digest(root / BUNDLE_MODULE_PATH),
        "uv_lock_normalised_LF_sha256": _normalised_text_digest(uv_lock)
        if uv_lock.is_file()
        else None,
    }


def build_root_manifest(
    root: Path,
    payload: Mapping[str, Any],
    chunks: Sequence[ChunkRecord],
    *,
    code_commit: str,
    verification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the Git-tracked root from an in-memory full payload."""

    root = root.resolve()
    arena_indices = {name: _arena_index(payload[name]["records"]) for name in ARENA_NAMES}
    chunk_ledger = [chunk.as_json() for chunk in chunks]
    by_arena: dict[str, list[dict[str, Any]]] = {name: [] for name in ARENA_NAMES}
    for record in chunk_ledger:
        by_arena[str(record["arena"])].append(record)
    verification_record = (
        dict(verification)
        if verification is not None
        else {
            "performed": False,
            "chunk_streaming_verified": False,
            "independent_recompilation_verified": False,
            "reason": "root written without a verifier pass; this is a digest commitment only",
        }
    )
    verdict = _verdict_for(verification_record)
    manifest_root: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-03",
        "storage_model": "two_tier_root_manifest_plus_out_of_tree_gzip_chunks",
        "full_logical_payload": {
            "semantic_digest_sha256": payload["semantic_digest_sha256"],
            "compiler_verdict": payload["verdict"],
            "compiler_passed": payload["passed"],
            "canonical_form": (
                "compact canonical JSON of the complete build_payload object; "
                "not tracked in Git and not stored by this bundle"
            ),
            "tracked_in_git": False,
        },
        "code_binding": _code_binding(root, code_commit=code_commit),
        "predecessor_bindings": payload["predecessor_bindings"],
        "authority": payload["authority"],
        "ring_binding": _ring_binding(payload),
        "row_index": _row_index(payload),
        "arena_index": arena_indices,
        "chart_generator_ids": _chart_generator_ids(payload),
        "source_inventory_summary": {
            "M0_row_count": payload["source_inventory"]["M0_row_count"],
            "block_counts": payload["source_inventory"]["block_counts"],
            "source_index_digest_sha256": payload["source_inventory"]["source_index_digest_sha256"],
            "row_label_digest_sha256": payload["source_inventory"]["row_label_digest_sha256"],
            "inventory_digest_sha256": payload["source_inventory"]["inventory_digest_sha256"],
        },
        "pivot_inventory_summary": {
            "pivot_row_count": payload["pivot_inventory"]["pivot_row_count"],
            "perfect_matching_digest_sha256": payload["pivot_inventory"][
                "perfect_matching_digest_sha256"
            ],
            "elimination_order_digest_sha256": payload["pivot_inventory"][
                "elimination_order_digest_sha256"
            ],
        },
        "denominator_audit_summary": {
            "record_count": payload["denominator_audit"]["record_count"],
            "records_digest_sha256": payload["denominator_audit"]["records_digest_sha256"],
            "unknown_denominator_factor_count": payload["denominator_audit"][
                "unknown_denominator_factor_count"
            ],
            "all_inverse_reconstructions_verified": payload["denominator_audit"][
                "all_inverse_reconstructions_verified"
            ],
        },
        "cross_check_summary": {
            "point_count": payload["frozen_exact_rational_cross_checks"]["point_count"],
            "records_digest_sha256": payload["frozen_exact_rational_cross_checks"][
                "records_digest_sha256"
            ],
            "all_points_in_declared_charts": payload["frozen_exact_rational_cross_checks"][
                "all_points_in_declared_charts"
            ],
        },
        "aligned_equal_ratio_SNF_audit": payload["aligned_equal_ratio_SNF_audit"],
        "chunk_ledger": {
            "directory": BUNDLE_DIRECTORY,
            "tracked_in_git": False,
            "chunk_target_uncompressed_bytes": CHUNK_TARGET_BYTES,
            "codec": CODEC,
            "codec_level": GZIP_LEVEL,
            "codec_mtime": GZIP_MTIME,
            "canonicalization": CANONICALIZATION,
            "authority": (
                "the uncompressed canonical byte stream is the mathematical authority; "
                "the gzip digest is a transport check only"
            ),
            "chunk_count": len(chunk_ledger),
            "total_uncompressed_bytes": sum(
                int(record["uncompressed_bytes"]) for record in chunk_ledger
            ),
            "total_gzip_bytes": sum(int(record["gzip_bytes"]) for record in chunk_ledger),
            "per_arena_chunk_counts": {name: len(by_arena[name]) for name in ARENA_NAMES},
            "chunks": chunk_ledger,
            "chunk_ledger_digest_sha256": _digest(chunk_ledger),
        },
        "verification": verification_record,
        "storage_policy": {
            "git": "root manifest and verifier only",
            "local_ssd": "authoring, verification and any solver run",
            "nas": "immutable cold backup of the finished compressed bundle; never expanded there",
            "publication": "Zenodo supplemental dataset",
        },
        "gates": {},
        "verdict": verdict,
        "search_terminal": SEARCH_TERMINAL,
        "claim_boundary": (
            "This root is a two-tier freeze of the no-Sage Phase-A input manifest. It "
            "commits to the 1,127-row Schur ledger, both coefficient arenas, and the six "
            "auxiliary-generator charts by digest, and it stores the arenas outside Git as "
            "deterministic gzip chunks of compact canonical JSONL. It does not retain the "
            "full logical payload byte for byte, so the frozen verdict claims frozen "
            "digests and solver inputs rather than a stored full manifest. Writing the "
            "root and the chunks is a digest commitment only. It computes no Groebner "
            "basis, saturation, unit ideal, witness, commutativity theorem, "
            "counterexample, or SR2-V terminal."
        ),
    }
    manifest_root["gates"] = _gates(manifest_root, compiler_passed=bool(payload["passed"]))
    manifest_root["passed"] = all(manifest_root["gates"].values())
    manifest_root["semantic_digest_sha256"] = semantic_digest(manifest_root)
    return manifest_root


def _gates(manifest_root: Mapping[str, Any], *, compiler_passed: bool) -> dict[str, bool]:
    verification = manifest_root["verification"]
    chunk_ledger = manifest_root["chunk_ledger"]
    return {
        "compiler_payload_passed_every_gate": compiler_passed,
        "canonical_semantic_predecessor_bindings": all(
            record["canonical_semantic_binding_passed"]
            for record in manifest_root["predecessor_bindings"].values()
        ),
        "row_index_covers_all_1127_rows": manifest_root["row_index"]["row_count"] == 1127,
        "six_chart_generator_tables_present": manifest_root["chart_generator_ids"]["chart_count"]
        == 6,
        "every_arena_record_is_chunked": all(
            sum(
                int(record["record_count"])
                for record in chunk_ledger["chunks"]
                if record["arena"] == name
            )
            == manifest_root["arena_index"][name]["record_count"]
            for name in ARENA_NAMES
        ),
        "chunks_are_deterministic_gzip": all(
            record["codec"] == CODEC
            and record["codec_level"] == GZIP_LEVEL
            and record["codec_mtime"] == GZIP_MTIME
            for record in chunk_ledger["chunks"]
        ),
        "uncompressed_bytes_are_the_declared_authority": all(
            record["authoritative_digest"] == "uncompressed_sha256"
            for record in chunk_ledger["chunks"]
        ),
        "chunk_streaming_verified": bool(verification.get("chunk_streaming_verified")),
        "independent_recompilation_verified": bool(
            verification.get("independent_recompilation_verified")
        ),
        "no_solver_or_unit_ideal_claim": True,
    }


def _verdict_for(verification: Mapping[str, Any]) -> str:
    """Decide the verdict from the whole verification record, not two flags.

    Fail-closed in both directions: a check that reports failure yields
    ``OPEN_ARTIFACT_INCOMPLETE``, while a check that is simply absent -- an
    older record, a partial run, a hand-assembled dictionary -- leaves the
    verdict at the unfrozen digest commitment.  Every entry of
    ``REQUIRED_RECOMPILATION_CHECKS`` must be present and ``True`` before the
    frozen verdict can be reached.
    """

    checks = verification.get("recompilation_checks") or {}
    if verification.get("artifact_incomplete") or verification.get("failures"):
        return INCOMPLETE_VERDICT
    if any(value is not True for value in checks.values()):
        return INCOMPLETE_VERDICT
    if not verification.get("performed"):
        return OBSERVED_VERDICT
    if not verification.get("chunk_streaming_verified"):
        return OBSERVED_VERDICT
    if not verification.get("independent_recompilation_verified"):
        return OBSERVED_VERDICT
    if any(checks.get(name) is not True for name in REQUIRED_RECOMPILATION_CHECKS):
        return OBSERVED_VERDICT
    return FROZEN_VERDICT


def write_bundle(
    root: Path,
    *,
    code_commit: str | None = None,
    progress: manifest.ProgressCallback = None,
    target_bytes: int = CHUNK_TARGET_BYTES,
) -> dict[str, Any]:
    """Compile Phase A, write the arena chunks, and emit the unverified root."""

    root = root.resolve()
    payload = manifest.build_payload(root, progress=progress)
    directory = root / BUNDLE_DIRECTORY
    chunks: list[ChunkRecord] = []
    for name in ARENA_NAMES:
        chunks.extend(
            write_arena_chunks(
                directory,
                name,
                payload[name]["records"],
                target_bytes=target_bytes,
            )
        )
    manifest_root = build_root_manifest(
        root,
        payload,
        chunks,
        code_commit=code_commit if code_commit is not None else _code_commit(root),
    )
    _write_root(root, manifest_root)
    return manifest_root


def verify_bundle(
    root: Path,
    *,
    recompile: bool = True,
    progress: manifest.ProgressCallback = None,
) -> dict[str, Any]:
    """Stream every chunk and, unless told otherwise, recompile Phase A from source.

    Fail-closed: a missing chunk, a digest mismatch, or any disagreement between
    the recompiled payload and the committed digests yields
    ``OPEN_ARTIFACT_INCOMPLETE`` rather than a partial pass.
    """

    root = root.resolve()
    committed = _load(root / ROOT_RESULT_PATH)
    directory = root / BUNDLE_DIRECTORY
    failures: list[str] = []

    streamed: dict[str, list[list[Any]]] = {}
    for name in ARENA_NAMES:
        chunks = [
            record for record in committed["chunk_ledger"]["chunks"] if record["arena"] == name
        ]
        correspondence: list[list[Any]] = []
        try:
            for record in read_arena_chunks(directory, chunks):
                observed = _digest(record["terms"])
                if observed != str(record["sha256"]):
                    failures.append(
                        f"{name}: record {record['polynomial_id']} terms do not match its digest"
                    )
                    break
                correspondence.append([int(record["polynomial_id"]), str(record["sha256"])])
        except (FileNotFoundError, ValueError, OSError) as error:
            failures.append(f"{name}: {error}")
        streamed[name] = correspondence
        expected = committed["arena_index"][name]
        if _digest(correspondence) != expected["polynomial_id_to_sha256_digest_sha256"]:
            failures.append(f"{name}: streamed identifier/digest correspondence does not match")

    chunk_streaming_verified = not failures

    recompilation_checks: dict[str, bool] = {}
    if recompile:
        payload = manifest.build_payload(root, progress=progress)
        rebuilt = build_root_manifest(
            root,
            payload,
            [
                ChunkRecord(**_chunk_fields(record))
                for record in committed["chunk_ledger"]["chunks"]
            ],
            code_commit=str(committed["code_binding"]["code_commit"]),
        )
        recompilation_checks = {
            # The compiler and bundle sources, and the locked environment, must
            # be the ones the root was produced from; otherwise the recompiled
            # digests would attest to different code.
            "code_binding_hashes": all(
                rebuilt["code_binding"].get(field) == committed["code_binding"].get(field)
                for field in (
                    "compiler_module_normalised_LF_sha256",
                    "bundle_module_normalised_LF_sha256",
                    "uv_lock_normalised_LF_sha256",
                )
            ),
            "full_logical_payload_digest": payload["semantic_digest_sha256"]
            == committed["full_logical_payload"]["semantic_digest_sha256"],
            "compiler_payload_passed": bool(payload["passed"]),
            "row_index_digest": rebuilt["row_index"]["ordered_rows_digest_sha256"]
            == committed["row_index"]["ordered_rows_digest_sha256"],
            "chart_generator_tables_digest": rebuilt["chart_generator_ids"]["charts_digest_sha256"]
            == committed["chart_generator_ids"]["charts_digest_sha256"],
            "denominator_audit_digest": rebuilt["denominator_audit_summary"][
                "records_digest_sha256"
            ]
            == committed["denominator_audit_summary"]["records_digest_sha256"],
            "cross_check_digest": rebuilt["cross_check_summary"]["records_digest_sha256"]
            == committed["cross_check_summary"]["records_digest_sha256"],
            "ring_binding": rebuilt["ring_binding"] == committed["ring_binding"],
            "arena_correspondence": all(
                rebuilt["arena_index"][name]["polynomial_id_to_sha256_digest_sha256"]
                == committed["arena_index"][name]["polynomial_id_to_sha256_digest_sha256"]
                for name in ARENA_NAMES
            ),
            "streamed_arena_matches_recompiled_arena": all(
                streamed[name]
                == [
                    [int(record["polynomial_id"]), str(record["sha256"])]
                    for record in payload[name]["records"]
                ]
                for name in ARENA_NAMES
            ),
        }
        failures.extend(
            f"recompilation: {key}" for key, value in recompilation_checks.items() if not value
        )

    verification = {
        "performed": True,
        "chunk_streaming_verified": chunk_streaming_verified,
        "independent_recompilation_verified": bool(recompile) and not failures,
        "independent_recompilation_requested": bool(recompile),
        "recompilation_checks": recompilation_checks,
        "artifact_incomplete": bool(failures),
        "failures": failures,
        "recomputed": sorted(
            [
                "source_and_pivot_rebuild",
                "Schur_identities",
                "Q5_and_spectator_vanishing",
                "denominator_clearing_and_inverse_reconstruction",
                "six_chart_generator_manifests",
                "six_frozen_rational_cross_check_points",
            ]
        )
        if recompile
        else [],
    }
    return verification


def _chunk_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "arena": str(record["arena"]),
        "chunk_index": int(record["chunk_index"]),
        "path": str(record["path"]),
        "first_polynomial_id": int(record["first_polynomial_id"]),
        "last_polynomial_id": int(record["last_polynomial_id"]),
        "record_count": int(record["record_count"]),
        "uncompressed_bytes": int(record["uncompressed_bytes"]),
        "uncompressed_sha256": str(record["uncompressed_sha256"]),
        "gzip_bytes": int(record["gzip_bytes"]),
        "gzip_sha256": str(record["gzip_sha256"]),
    }


def apply_verification(
    manifest_root: Mapping[str, Any],
    verification: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the root with a verifier result folded in and the verdict recomputed."""

    updated = {
        key: value for key, value in manifest_root.items() if key != "semantic_digest_sha256"
    }
    compiler_passed = bool(updated["gates"]["compiler_payload_passed_every_gate"])
    updated["verification"] = dict(verification)
    updated["verdict"] = _verdict_for(verification)
    updated["gates"] = _gates(updated, compiler_passed=compiler_passed)
    updated["passed"] = all(updated["gates"].values())
    updated["semantic_digest_sha256"] = semantic_digest(updated)
    return updated


def render_root_report(manifest_root: Mapping[str, Any]) -> str:
    ledger = manifest_root["chunk_ledger"]
    verification = manifest_root["verification"]
    lines = [
        "# SR2-V Q5-free auxiliary-ideal Phase-A bundle root",
        "",
        f"Date: {manifest_root['date']}",
        "",
        f"Verdict: `{manifest_root['verdict']}`",
        "",
        f"Semantic digest: `{manifest_root['semantic_digest_sha256']}`",
        "",
        "## Storage model",
        "",
        "The root manifest below is tracked in Git. Both coefficient arenas are stored",
        f"outside Git under `{ledger['directory']}` as compact canonical JSONL split into",
        "deterministic gzip chunks. The uncompressed canonical byte stream is the",
        "mathematical authority; the gzip digest is a transport check only.",
        "",
        (
            "- Full logical payload digest: "
            f"`{manifest_root['full_logical_payload']['semantic_digest_sha256']}`"
        ),
        f"- Chunks: {ledger['chunk_count']}",
        f"- Uncompressed bytes: {ledger['total_uncompressed_bytes']}",
        f"- Gzip bytes: {ledger['total_gzip_bytes']}",
        f"- Rows committed: {manifest_root['row_index']['row_count']}",
        f"- Charts committed: {manifest_root['chart_generator_ids']['chart_count']}",
        (
            "- Arena records: "
            + ", ".join(
                f"{name}={manifest_root['arena_index'][name]['record_count']}"
                for name in ARENA_NAMES
            )
        ),
        "",
        "## Verification state",
        "",
        f"- Verifier run: {verification['performed']}",
        f"- Chunk streaming verified: {verification['chunk_streaming_verified']}",
        (
            "- Independent recompilation verified: "
            f"{verification['independent_recompilation_verified']}"
        ),
        f"- Artifact incomplete: {bool(verification.get('artifact_incomplete'))}",
        "",
        "Writing the root and the chunks is a digest commitment. The frozen verdict",
        "requires a verifier pass that streams every chunk and independently recompiles",
        "the source and pivot rebuild, the Schur identities, Q5 and spectator vanishing,",
        "denominator clearing with its inverse reconstruction, the six chart generator",
        "manifests, the six frozen rational cross-check points, and the compiler,",
        "bundle and lockfile digests the root was produced from. Every required check",
        "must be present and true; an absent one leaves the bundle unfrozen.",
        "",
        "The verdict says digest and solver inputs, not full manifest: the arenas are",
        "retained and everything else is committed to by digest, so the roughly",
        "20.9 GiB logical payload is not stored byte for byte.",
        "",
        "## Scope boundary",
        "",
        manifest_root["claim_boundary"],
        "",
    ]
    return "\n".join(lines)


def _write_root(root: Path, manifest_root: Mapping[str, Any]) -> None:
    manifest._write_json(root / ROOT_RESULT_PATH, manifest_root)  # noqa: SLF001
    (root / ROOT_REPORT_PATH).write_text(
        render_root_report(manifest_root),
        encoding="utf-8",
        newline="\n",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--verify",
        action="store_true",
        help="stream the committed chunks and recheck them against the root manifest",
    )
    parser.add_argument(
        "--no-recompile",
        action="store_true",
        help=(
            "with --verify, check chunk integrity only; the frozen verdict still "
            "requires an independent recompilation"
        ),
    )
    arguments = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]

    if arguments.verify:
        verification = verify_bundle(root, recompile=not arguments.no_recompile)
        manifest_root = apply_verification(_load(root / ROOT_RESULT_PATH), verification)
        _write_root(root, manifest_root)
    else:
        manifest_root = write_bundle(root)

    print(
        _canonical_json(
            {
                "verdict": manifest_root["verdict"],
                "semantic_digest_sha256": manifest_root["semantic_digest_sha256"],
                "chunk_count": manifest_root["chunk_ledger"]["chunk_count"],
                "total_gzip_bytes": manifest_root["chunk_ledger"]["total_gzip_bytes"],
                "passed": manifest_root["passed"],
            }
        )
    )
    return 0 if manifest_root["verdict"] != INCOMPLETE_VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
