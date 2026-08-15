from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from universe_lab.artifact_migration_v038 import (
    EXPECTED_BINDING_COUNT,
    EXPECTED_CONSUMER_COUNT,
    EXPECTED_TARGET_COUNT,
    LedgerValidationError,
    TextArtifactError,
    canonical_lf_bytes,
    json_pointer_get,
    line_ending_hashes,
    load_line_ending_bridge,
    sha256_bytes,
    strict_lf_bytes,
    verify_line_ending_bridge,
    virtual_crlf_bytes,
)

ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "results/v0.3.8_line_ending_bridge.json"
BUILDER_PATH = ROOT / "scripts/build_v038_line_ending_bridge.py"


def _builder_module():
    spec = importlib.util.spec_from_file_location("build_v038_line_ending_bridge", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_line_ending_hash_primitives_are_strict(tmp_path: Path) -> None:
    lf = b'{"value": 1}\n'
    crlf = b'{"value": 1}\r\n'
    path = tmp_path / "artifact.json"
    path.write_bytes(lf)

    hashes = line_ending_hashes(path, require_canonical_lf=True)
    assert hashes["current_raw_sha256"] == sha256_bytes(lf)
    assert hashes["canonical_lf_sha256"] == sha256_bytes(lf)
    assert hashes["virtual_crlf_sha256"] == sha256_bytes(crlf)
    assert hashes["virtual_crlf_size_bytes"] == len(crlf)
    assert canonical_lf_bytes(crlf) == lf
    assert virtual_crlf_bytes(lf) == crlf

    with pytest.raises(UnicodeDecodeError):
        canonical_lf_bytes(b"\xff")
    with pytest.raises(TextArtifactError, match="lone carriage return"):
        canonical_lf_bytes(b"left\rright")
    with pytest.raises(TextArtifactError, match="not canonical LF"):
        strict_lf_bytes(crlf)


def test_json_pointer_resolves_escaped_objects_and_arrays() -> None:
    document = {"a/b": {"~key": [{"digest": "ok"}]}}
    assert json_pointer_get(document, "/a~1b/~0key/0/digest") == "ok"
    assert json_pointer_get(document, "") is document

    with pytest.raises(LedgerValidationError, match="invalid JSON Pointer escape"):
        json_pointer_get(document, "/a~2b")
    with pytest.raises(LedgerValidationError, match="invalid array index"):
        json_pointer_get([1], "/01")


def test_frozen_bridge_has_exact_audited_scope_and_resolves() -> None:
    ledger = load_line_ending_bridge(LEDGER_PATH)
    summary = verify_line_ending_bridge(ROOT, ledger)
    assert summary == {
        "passed": True,
        "legacy_raw_bindings": EXPECTED_BINDING_COUNT,
        "unique_consumers": EXPECTED_CONSUMER_COUNT,
        "unique_targets": EXPECTED_TARGET_COUNT,
        "target_candidate_edges": 1027,
        "ambiguous_bindings": 20,
        "all_targets_currently_canonical_lf": True,
        "all_bindings_resolve_by_json_pointer": True,
    }
    assert all(
        marker not in binding["json_pointer"].lower()
        for binding in ledger["bindings"]
        for marker in (
            "semantic_digest",
            "request_digest",
            "request_sha256",
            "expression_digest",
            "polynomial_digest",
            "budget_digest",
        )
    )


def test_living_manifest_is_not_a_current_legacy_resolver_target() -> None:
    ledger = load_line_ending_bridge(LEDGER_PATH)

    assert "references/manifest.json" in {
        target["path"] for target in ledger["targets"]
    }
    from universe_lab.artifact_migration_v038 import LegacyRawDigestResolver

    resolver = LegacyRawDigestResolver(ROOT, ledger)
    assert "references/manifest.json" not in resolver.virtual_crlf_targets


def test_bridge_matches_deterministic_regeneration() -> None:
    builder = _builder_module()
    saved = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    regenerated = builder.build_ledger(ROOT)
    assert regenerated == saved
    assert builder.render_ledger(regenerated) == LEDGER_PATH.read_bytes()
