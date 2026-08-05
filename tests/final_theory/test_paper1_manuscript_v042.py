from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "results/v0.4.2_paper1_manuscript_manifest.json"
EXPECTATIONS_PATH = (
    ROOT / "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)
LITERATURE_REPORT_PATH = ROOT / "reports/v0.4.2_paper1_literature_delta_2026-08-05.md"
LITERATURE_NOTE_PATH = ROOT / "references/notes/v0.4.2_paper1_literature_delta_2026-08-05.md"
LITERATURE_DELTA_STATUS = "CLOSED_NO_MATERIAL_DELTA_AS_OF_2026-08-05T01:43Z"
SCOUT_INPUT_MANIFEST_PATH = (
    ROOT / "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json"
)
SCOUT_EXPECTATIONS_RELATIVE = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)
PAPER1_VALIDATOR_PATH = ROOT / "scripts/validate_v042_paper1_manuscript.py"


def _load_paper1_validator() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_paper1_manuscript_validator",
        PAPER1_VALIDATOR_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    script_directory = str(PAPER1_VALIDATOR_PATH.parent)
    sys.path.insert(0, script_directory)
    try:
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
    finally:
        sys.path.remove(script_directory)
    return module


def _copy_bounded_scout_inputs(repository_root: Path) -> None:
    input_manifest = json.loads(SCOUT_INPUT_MANIFEST_PATH.read_text(encoding="utf-8"))
    relative_paths = {
        Path("compose.yaml"),
        Path("uv.lock"),
        Path("results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bundle_root.json"),
        Path(
            "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json"
        ),
        SCOUT_EXPECTATIONS_RELATIVE,
        *(Path(path) for path in input_manifest["fixture_raw_sha256"]),
        *(Path(path) for path in input_manifest["source_normalized_lf_sha256"]),
    }
    for relative in sorted(relative_paths):
        target = repository_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def test_paper1_manuscript_validator_passes_after_bounded_core_pinning() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_v042_paper1_manuscript.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "paper1_manuscript=OK"


def test_paper1_manuscript_remains_unfrozen_and_owner_gated() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["status"] == "DRAFT_SCAFFOLD_NOT_FROZEN"
    assert manifest["freeze"] == {
        "status": "NOT_FROZEN",
        "frozen": False,
        "authorized": False,
    }
    for gate_name in ("submission", "deposit"):
        gate = manifest["publication_gates"][gate_name]
        assert gate["status"] == "OWNER_ONLY_NOT_AUTHORIZED"
        assert gate["owner_only"] is True
        assert gate["authorized"] is False


def test_paper1_literature_delta_is_closed_bounded_and_recheck_gated() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    literature = manifest["literature_delta_search"]

    assert literature["status"] == LITERATURE_DELTA_STATUS
    assert literature["completed"] is True
    assert literature["search_window"] == {
        "start_utc": "2026-07-31T15:00:00Z",
        "effective_assessment_cutoff_utc": "2026-08-05T01:43:02Z",
        "category_api_coarse_upper_bound_utc": "2026-08-05T23:59Z",
    }
    assert literature["official_repository"] == "arXiv"
    assert literature["screened_record_count"] == 524
    assert literature["screened_categories"] == [
        "gr-qc",
        "quant-ph",
        "math-ph",
        "math.OA",
        "math.RA",
        "math.AC",
        "math.FA",
        "math.CO",
    ]
    assert literature["targeted_categories"] == ["math.PR", "physics.*"]
    assert literature["tracked_source_versions"] == {
        "arXiv:2607.26672": "v1",
        "arXiv:2603.25503": "v1",
    }
    assert literature["keyword_hits_not_material"] == [
        "arXiv:2608.03273",
        "arXiv:2608.02166",
    ]
    assert literature["companion_public_arxiv_record_located"] is False
    assert literature["post_completion_requery"] == {
        "status": "HTTP_429_RATE_LIMITED_AFTER_COMPLETION",
        "affects_completed_screening": False,
    }
    assert literature["source_catalog_record_ids"] == [
        "arXiv:PaperI-literature-delta-query-2026-08-05",
        "arXiv:2608.03273v1",
        "arXiv:2608.02166v1",
    ]
    assert literature["reference_archive"] == {
        "sources_path": "references/sources.json",
        "manifest_path": "references/manifest.json",
        "status": "HASH_ONLY_SKIP_TEXT_PYPDF_UNAVAILABLE",
        "command": "scripts/archive_references.py --skip-text",
    }
    assert literature["material_delta_for_claim_labels"] == []
    assert literature["recheck_before_submission"] is True
    assert literature["priority_or_absolute_absence_claimed"] is False

    assert literature["audit_report"]["path"] == LITERATURE_REPORT_PATH.relative_to(ROOT).as_posix()
    assert literature["note_path"] == LITERATURE_NOTE_PATH.relative_to(ROOT).as_posix()
    assert (
        literature["audit_report"]["raw_sha256"]
        == hashlib.sha256(LITERATURE_REPORT_PATH.read_bytes()).hexdigest()
    )
    assert (
        literature["note_raw_sha256"]
        == hashlib.sha256(LITERATURE_NOTE_PATH.read_bytes()).hexdigest()
    )

    report = " ".join(LITERATURE_REPORT_PATH.read_text(encoding="utf-8").split())
    note = LITERATURE_NOTE_PATH.read_text(encoding="utf-8")
    assert "lastUpdatedDate:[202607311500+TO+202608052359]" in report
    assert "HTTP 429" in report
    assert "not an absolute literature-absence, novelty, or priority determination" in report
    assert "mandatory immediately before public submission" in note
    for source_id in literature["source_catalog_record_ids"]:
        assert source_id in report
        assert source_id in note

    source_catalog = json.loads((ROOT / "references/sources.json").read_text(encoding="utf-8"))
    archive = json.loads((ROOT / "references/manifest.json").read_text(encoding="utf-8"))
    catalog_by_id = {record["id"]: record for record in source_catalog["sources"]}
    archive_by_id = {record["id"]: record for record in archive["records"]}
    assert source_catalog["retrieved_on"] == "2026-08-05"
    for source_id in literature["source_catalog_record_ids"]:
        assert catalog_by_id[source_id]["local_file"] is None
        assert archive_by_id[source_id]["archive_status"] == "METADATA_ONLY"


def test_paper1_manuscript_requires_pinned_certificate_cores() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    assert manifest["bounded_scout_reproduction"] == {
        "input_manifest": {
            "path": (
                "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_"
                "bounded_scout_reproduction_manifest.json"
            ),
            "schema_version": "sr2v-q5-free-bounded-scout-reproduction-input-manifest-v1",
        },
        "expectations": {
            "path": ("results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"),
            "schema_version": "sr2v-q5-free-bounded-scout-expectations-v1",
            "pending_status": "PENDING_BOUNDED_SAGE_RECOMPUTATION",
            "required_final_status": "PINNED",
            "certificate_core_names": ["row185_normal_form", "candidate_minor_only"],
            "raw_sha256": "346aa987d9e29babc13b16c95fb088ea0c566a6e0704f8ae82c126e13a4e3f60",
            "semantic_digest_sha256": (
                "fd4a7fb3c9734abb324bf7d2e4bcb6c4296c3bb7e15f0c218b408a46f7f745da"
            ),
            "certificate_core_digests": {
                "row185_normal_form": (
                    "bd2d390ea996ea5149578bb569d6bba98fecbcb96b1b00d0fe8ff7b365f00deb"
                ),
                "candidate_minor_only": (
                    "cb9252dbc9d1610d3d0410f0d8f111a862b341cee59a4ced20bb8527c66a1c87"
                ),
            },
        },
        "legacy_observation_status": (
            "NONDETERMINISTIC_LEGACY_OBSERVATION_NOT_A_REPRODUCTION_EXPECTATION"
        ),
    }
    assert expectations["status"] == "PINNED"
    assert expectations["certificate_core_digests"] == {
        "candidate_minor_only": "cb9252dbc9d1610d3d0410f0d8f111a862b341cee59a4ced20bb8527c66a1c87",
        "row185_normal_form": "bd2d390ea996ea5149578bb569d6bba98fecbcb96b1b00d0fe8ff7b365f00deb",
    }


def test_paper1_validator_rejects_a_self_rebound_expectations_artifact(tmp_path: Path) -> None:
    """F binds E externally, so rebinding E to itself cannot alter Paper I.

    This exercises the intended acyclic chain M -> E -> F.  The temporary E
    changes a certificate core and recomputes its own semantic digest; the
    Paper I validator must still reject it by the raw/semantic/core values
    pinned in F rather than accepting the self-rebound E.
    """

    _copy_bounded_scout_inputs(tmp_path)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expectations_path = tmp_path / SCOUT_EXPECTATIONS_RELATIVE
    expectations = json.loads(expectations_path.read_text(encoding="utf-8"))
    expectations["certificate_core_digests"]["row185_normal_form"] = "a" * 64
    unbound = {key: value for key, value in expectations.items() if key != "semantic_digest_sha256"}
    expectations["semantic_digest_sha256"] = hashlib.sha256(
        json.dumps(
            unbound,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    expectations_path.write_text(
        json.dumps(expectations, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    validator = _load_paper1_validator()
    errors: list[str] = []
    validator._validate_bounded_scout_reproduction(tmp_path, manifest, errors)

    assert any("raw SHA-256 mismatch" in error for error in errors)
    assert any("self semantic digest mismatch" in error for error in errors)
    assert any("certificate-core digests differ" in error for error in errors)
