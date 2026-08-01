"""Independent regression checks for the v0.4.1 QQ certificate oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from universe_lab.final_theory.one_sided_elimination_oracle_v041 import (
    HISTORICAL_CAMPAIGN_PATH,
    HISTORICAL_MANIFEST_PATH,
    HISTORICAL_RESULT_PATH,
    RESTRICTED_CAMPAIGN_VERDICT,
    RESTRICTED_MANIFEST_VERDICT,
    RESTRICTED_ORACLE_VERDICT,
    RESULT_PATH,
    SOURCE_MODE_CURRENT,
    SOURCE_MODE_HISTORICAL,
    WITHDRAWN_FULL_PROFILE_VERDICT,
    _verify_source_semantic_scope,
    compile_one_sided_elimination_oracle_v041,
    validate_current_oracle_scope_v041,
    write_one_sided_elimination_oracle_v041,
)
from universe_lab.final_theory.one_sided_elimination_v041 import (
    compile_one_sided_qq_manifest_v041,
    write_one_sided_qq_manifest_v041,
)

ROOT = Path(__file__).resolve().parents[2]


def test_oracle_rebuilds_the_two_on_quotient_cores_and_all_certificates() -> None:
    payload = compile_one_sided_elimination_oracle_v041(ROOT)
    assert payload["verdict"] == RESTRICTED_ORACLE_VERDICT
    assert payload["terminal_verdict"] == RESTRICTED_CAMPAIGN_VERDICT
    assert payload["terminal_verdict"] != WITHDRAWN_FULL_PROFILE_VERDICT
    assert payload["source_artifact_mode"] == SOURCE_MODE_HISTORICAL
    assert payload["semantic_scope"]["classification"] == "RESTRICTED_LOCUS_ONLY"
    assert payload["historical_claim_handling"] == {
        "withdrawn_full_profile_verdict_encountered": True,
        "status": "ARITHMETIC_INPUT_ONLY_FULL_PROFILE_INFERENCE_REJECTED",
    }
    assert payload["verified_certificate_count"] == 42
    assert payload["raw_direct_system"]["q5_free_shared_relation_count"] == 976
    assert (
        payload["profile_results"]["fixed_vector_GC__strong_MSR"]["core"]["sha256"]
        == "461445fdc9fb03ac4f26a4c327b7020a864163a28380e9cf40ac9d6f2a3e0bd3"
    )
    assert (
        payload["profile_results"]["strong_GC__reachable_state_MSR"]["core"]["sha256"]
        == "d86c3a7170774209a3d09eb44391d889388482a78eae97004fbf46256cb5a970"
    )
    for profile in payload["profile_results"].values():
        assert profile["restricted_locus_commutativity_proved"] is True
        assert profile["profile_native_coverage_certified"] is False
        assert profile["full_profile_forward_implication_permitted"] is False
        assert profile["full_profile_commutativity_proved_by_forward_implication"] is False
    stored = json.loads((ROOT / HISTORICAL_RESULT_PATH).read_text(encoding="utf-8"))
    assert stored["terminal_verdict"] == WITHDRAWN_FULL_PROFILE_VERDICT
    assert stored != payload


def test_oracle_result_roundtrip_has_stable_newlines(tmp_path: Path) -> None:
    payload = compile_one_sided_elimination_oracle_v041(ROOT)
    written = write_one_sided_elimination_oracle_v041(tmp_path, payload)
    assert written == tmp_path / RESULT_PATH
    assert "restricted_locus" in written.name
    assert "\r\n" not in written.read_bytes().decode("utf-8")


def test_oracle_writer_rejects_withdrawn_terminal_verdict(tmp_path: Path) -> None:
    payload = compile_one_sided_elimination_oracle_v041(ROOT)
    poisoned = dict(payload)
    poisoned["terminal_verdict"] = WITHDRAWN_FULL_PROFILE_VERDICT
    with pytest.raises(ValueError, match="withdrawn full-profile verdict"):
        validate_current_oracle_scope_v041(poisoned)
    with pytest.raises(ValueError, match="withdrawn full-profile verdict"):
        write_one_sided_elimination_oracle_v041(tmp_path, poisoned)


def test_current_source_mode_rejects_withdrawn_campaign_verdict() -> None:
    manifest = compile_one_sided_qq_manifest_v041(ROOT)
    assert manifest["verdict"] == RESTRICTED_MANIFEST_VERDICT
    poisoned_campaign = {
        "semantic_scope": manifest["semantic_scope"],
        "verdict": WITHDRAWN_FULL_PROFILE_VERDICT,
    }
    with pytest.raises(ValueError, match="withdrawn verdict exclusion"):
        _verify_source_semantic_scope(manifest, poisoned_campaign, SOURCE_MODE_CURRENT)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_scope_corrected_compile_and_writes_leave_all_historical_bytes_unchanged(
    tmp_path: Path,
) -> None:
    historical_json = [
        ROOT / HISTORICAL_MANIFEST_PATH,
        ROOT / HISTORICAL_CAMPAIGN_PATH,
        ROOT / HISTORICAL_RESULT_PATH,
    ]
    historical_certificates = sorted(
        (ROOT / "certificates/d2_saturation/one_sided_v041").rglob("*.json")
    )
    assert len(historical_certificates) == 42
    paths = historical_json + historical_certificates
    before = {path: path.read_bytes() for path in paths}
    assert [_sha256_bytes(before[path]) for path in historical_json] == [
        "b5ca2f2994d07617026cea0f6eb749a0e9e0bc35363e5cf0862a9fe92e04068a",
        "629e263bfb507d4678e80de1679aeaa927797c4753487b435a4799297eb04959",
        "cb709d1123bc8c435ad14f419cd2275fa048c07a9ff665142f8c0a87e2c752f6",
    ]
    certificate_aggregate = hashlib.sha256()
    for path in historical_certificates:
        certificate_aggregate.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        certificate_aggregate.update(b"\0")
        certificate_aggregate.update(before[path])
    assert certificate_aggregate.hexdigest() == (
        "e0ac10c0fe1f77771c5403ac413f641f67af13e2617025027cfac6a6c1efc8b8"
    )

    manifest = compile_one_sided_qq_manifest_v041(ROOT)
    write_one_sided_qq_manifest_v041(tmp_path, manifest)
    oracle = compile_one_sided_elimination_oracle_v041(ROOT)
    write_one_sided_elimination_oracle_v041(tmp_path, oracle)

    after = {path: path.read_bytes() for path in paths}
    assert after == before
