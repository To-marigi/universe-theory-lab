from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "results/v0.4.2_paper1_manuscript_manifest.json"
MAIN_TEX_PATH = ROOT / "paper/v0.4.2_paper1_statewise_operator/main.tex"
EXPECTATIONS_PATH = (
    ROOT / "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)
LITERATURE_REPORT_PATH = ROOT / "reports/v0.4.2_paper1_literature_delta_2026-08-05.md"
LITERATURE_NOTE_PATH = ROOT / "references/notes/v0.4.2_paper1_literature_delta_2026-08-05.md"
LITERATURE_DELTA_STATUS = (
    "CLOSED_NO_MATERIAL_DELTA_WITHIN_ARCHIVED_SUBMITTEDDATE_SCOPE_AS_OF_2026-08-05T04:52:45Z"
)
SCOUT_INPUT_MANIFEST_PATH = (
    ROOT / "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json"
)
SCOUT_EXPECTATIONS_RELATIVE = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)
PAPER1_VALIDATOR_PATH = ROOT / "scripts/validate_v042_paper1_manuscript.py"
PDF_BUILD_HELPER_RELATIVE = Path("scripts/build_v042_paper1_pdf.py")
PDF_BUILD_REPORT_RELATIVE = Path("reports/v0.4.2_paper1_pdf_build_2026-08-06.md")
PDF_BUILD_OUTPUT_RELATIVE = Path("output/pdf/paper1_statewise_operator_v0.4.2.pdf")
PDF_BUILD_IMAGE = (
    "texlive/texlive:latest-medium@"
    "sha256:d79913b74afcf48a53ec2ad0d54b70ad3e36d65b4f1de13d811435883c2f1fd9"
)
C3_RELATION_IDS = (
    "cpobc-relation-0b2bbe81c6394d603f63",
    "cpobc-relation-49726b7f352ba79916e5",
    "cpobc-relation-6002781cceb198b6edfd",
    "cpobc-relation-1d7b3a88785401c6531b",
    "cpobc-relation-01e29996483e2c4f342c",
    "cpobc-relation-17e9d7ae74c8bed62194",
)


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


def test_completed_proofs_and_closed_marker_gate_are_pinned_fail_closed() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tex = MAIN_TEX_PATH.read_text(encoding="utf-8")
    validator = _load_paper1_validator()
    c3 = tex.split(r"\subsection{C3:", 1)[1].split(r"\subsection{C4:", 1)[0]
    c5 = tex.split(r"\subsection{C5:", 1)[1].split(r"\section{Proof roadmap", 1)[0]
    recovery = tex.split(r"\section{Recovery conditions and their boundary}", 1)[1].split(
        r"\section{Explicit nonclaims}",
        1,
    )[0]

    def normalise(value: str) -> str:
        return " ".join(value.split())

    assert manifest["draft_markers"] == validator.EXPECTED_DRAFT_MARKER_CONTRACT
    assert tex.count(r"\draftmarker{") == 0
    assert tex.count("DRAFT PROOF INSERT REQUIRED.") == 0
    assert r"\newcommand{\draftmarker}" not in tex
    assert r"\draftmarker{" not in c3
    assert r"\draftmarker{" not in c5
    assert r"\draftmarker{" not in recovery
    for relation_id in C3_RELATION_IDS:
        assert c3.count(relation_id) == 1
    for identity in (
        "B_2Q_1=B_1Q_2",
        "B_3Q_1=B_1Q_3",
        "B_3Q_2=B_2Q_3",
        "B_4Q_1=B_1Q_4",
        "B_4Q_2=B_2Q_4",
        "B_4Q_3=B_3Q_4",
    ):
        assert identity in c3
    for fragment in (
        r"\cite[Eqs.~(103), (105), and (115)--(120)]{SrivastavaSurya2026}",
        "Only associativity and adjacent unit cancellation were used",
        r"Neither GC nor MSR, Eq.~(108), Eq.~(112), B-reduction, \(d=2\), or \(Q_5\)",
        "arbitrary point of the direct system",
        r"R_i:=Q_1^{-1}Q_i",
    ):
        assert normalise(fragment) in normalise(c3)
    c5_evidence = c5 + recovery
    for fragment in (
        r"\ker(\operatorname{ev}_V)=\{0\}",
        r"\(DP=0\)",
        r"kernel dimension \(2\)",
        r"rank \(4\) and zero kernel",
        r"\mathcal R=\operatorname{span}\{I,E_{21}\}",
        "Independent non-scalar",
        r"b^2,\qquad c^2,\qquad -(a-d)^2",
        "Cyclicity does not imply separation.",
        "general linear-algebra counterexamples",
        "solution of the CPOBC equations",
        "same-residual multi-probe data",
        "has not been proved by the current artifacts",
        "all declared GC and MSR residuals",
        "frozen occurrence-ON",
    ):
        assert normalise(fragment) in normalise(c5_evidence)

    for reappearance in (
        "\n\\draftmarker{reappeared}\n",
        "\nDRAFT PROOF INSERT REQUIRED.\n",
        "\n\\newcommand{\\draftmarker}[1]{#1}\n",
    ):
        errors: list[str] = []
        validator._validate_draft_marker_contract(
            tex + reappearance,
            manifest["draft_markers"],
            errors,
        )
        assert any("DRAFT marker" in error for error in errors), reappearance


def test_completed_proof_validator_rejects_c3_or_c5_evidence_drift() -> None:
    validator = _load_paper1_validator()
    tex = MAIN_TEX_PATH.read_text(encoding="utf-8")

    for needle in (
        C3_RELATION_IDS[0],
        "arbitrary point of the\ndirect system",
        r"b^2,\qquad c^2,\qquad -(a-d)^2",
        "same-residual multi-probe data",
    ):
        altered = tex.replace(needle, "", 1)
        assert altered != tex
        errors: list[str] = []
        validator._validate_completed_c3_c5_proofs(altered, errors)
        assert errors, needle


def test_citation_closure_rejects_missing_and_duplicate_bibtex_keys() -> None:
    validator = _load_paper1_validator()
    assert validator._citation_keys(r"\cite[see][p.~1]{Alpha, Beta}\cite{Gamma}") == {
        "Alpha",
        "Beta",
        "Gamma",
    }
    tex = MAIN_TEX_PATH.read_text(encoding="utf-8")
    shared_path = ROOT / "paper/v0.3.9_d2_commutativity_short_report/references.bib"
    local_path = ROOT / "paper/v0.4.2_paper1_statewise_operator/references.bib"
    read_errors: list[str] = []
    shared_counts = validator._bibliography_key_counts(shared_path, read_errors)
    local_counts = validator._bibliography_key_counts(local_path, read_errors)
    assert not read_errors

    errors: list[str] = []
    validator._validate_citation_closure(tex, (shared_counts, local_counts), errors)
    assert not errors

    missing_source = shared_counts.copy()
    del missing_source["SrivastavaSurya2026"]
    errors = []
    validator._validate_citation_closure(tex, (missing_source, local_counts), errors)
    assert any("citation keys absent" in error for error in errors)

    duplicate_source = Counter({"SrivastavaSurya2026": 1})
    errors = []
    validator._validate_citation_closure(
        tex,
        (shared_counts, local_counts, duplicate_source),
        errors,
    )
    assert any("occur more than once" in error for error in errors)


def test_paper1_manuscript_remains_unfrozen_and_owner_gated() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["status"] == "PAPER_I_SCOPED_ARCHIVE_SUBMISSION_CANDIDATE_NOT_FROZEN"
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
    assert manifest["publication_gates"]["pdf_source_rebind"] == {
        "status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
        "required_before_submission_or_deposit": True,
        "completed": True,
        "publication_authorized": False,
    }


def test_electronic_supplement_and_weak_q5_authorities_are_pinned() -> None:
    validator = _load_paper1_validator()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["electronic_supplement"] == validator._expected_electronic_supplement()
    contract = manifest["electronic_supplement"]
    assert contract["policy"] == {
        "complete_weak_ledger_remains_authority": True,
        "compact_result_replaces_complete_ledger": False,
        "embed_all_3283_records_in_pdf": False,
        "ordinary_reproduction_mode": "--check",
        "write_requires_review_and_manifest_rebinding": True,
    }
    assert contract["result"]["schema_version"] == ("final-theory-v042-paper1-witness-tables-v1")
    assert contract["result"]["expected_total_top_level_records"] == 3283
    assert contract["result"]["transition_occurrence_count"] == 165
    assert contract["result"]["transition_orbit_count"] == 131
    assert contract["q5_free_elimination_authority"]["result"]["schema_version"] == (
        "final-theory-q5-free-campaign-v0.3.7"
    )

    errors: list[str] = []
    validator._validate_electronic_supplement(ROOT, manifest, errors)
    assert not errors

    altered = copy.deepcopy(manifest)
    altered["electronic_supplement"]["result"]["semantic_digest_sha256"] = "0" * 64
    errors = []
    validator._validate_electronic_supplement(ROOT, altered, errors)
    assert any("electronic supplement contract changed" in error for error in errors)


def test_pdf_build_contract_is_pinned_but_generated_pdf_is_not_required(tmp_path: Path) -> None:
    validator = _load_paper1_validator()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tex_build = manifest["tex_build"]

    assert tex_build["toolchain_status"] == "HOST_ABSENT_PINNED_CONTAINER_AVAILABLE"
    assert tex_build["pdf_status"] == "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED"
    assert tex_build["pdf_verified"] is True
    assert tex_build["submission_ready"] is False
    assert tex_build["pinned_container_image"] == PDF_BUILD_IMAGE
    assert tex_build["generated_pdf"] == {
        "tracked": False,
        "required_for_manifest_validation": False,
        "raw_sha256_role": "DATED_OBSERVATION_NOT_REPRODUCIBILITY_CONTRACT",
    }
    current = tex_build["current_observation"]
    assert current["main_tex_raw_sha256"] == (
        "e3a39aac3ba2593666a772b4d04c86bff2faf19936a5d8eb45a2a341248101b1"
    )
    assert current["pdf"] == {
        "page_count": 18,
        "bytes": 427745,
        "raw_sha256": "9f58867d91673c09229077cd651a35d16d10e90c618cc6ef6083fd4fb644fd43",
    }
    assert current["diagnostics"] == {
        "blocking_total": 0,
        "overfull_hbox": 0,
        "undefined_reference_or_citation": 0,
        "latex_or_package_error": 0,
        "underfull_box": 0,
    }
    assert current["visual_qa"] == {
        "render_dpi": 144,
        "pages_inspected": 18,
        "all_pages_inspected": True,
        "clipping_or_overlap_found": False,
        "intentional_draft_boxes_remain": False,
    }
    assert current["source_pdf_binding"] == {
        "status": "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED",
        "source_hash_matches_current_observation": True,
        "report_hash_pinned": True,
        "publication_authorized": False,
    }
    assert tex_build["prior_observations"] == [
        {
            "status": "PRIOR_SOURCE_OBSERVATION_NOT_CURRENT_BINDING",
            "date": "2026-08-05",
            "main_tex_raw_sha256": (
                "6cf9855b1822f0c16a9ab2b3fff1fc37cd87395cbf8352e2b8322885f195cdbd"
            ),
            "pdf": {
                "page_count": 10,
                "bytes": 371899,
                "raw_sha256": ("cf8c4c01210b010127ce29750165031a7a83788aa4cd525a829f7dddfd1adaca"),
            },
            "diagnostics": {
                "blocking_total": 0,
                "overfull_hbox": 0,
                "undefined_reference_or_citation": 0,
                "latex_or_package_error": 0,
                "underfull_box": 0,
            },
            "visual_qa": {
                "pages_inspected": 10,
                "all_pages_inspected": True,
                "clipping_or_overlap_found": False,
                "intentional_draft_boxes_remain": True,
            },
        }
    ]

    for relative in (PDF_BUILD_HELPER_RELATIVE, PDF_BUILD_REPORT_RELATIVE):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    assert not (tmp_path / PDF_BUILD_OUTPUT_RELATIVE).exists()

    errors: list[str] = []
    validator._validate_tex_build(tmp_path, manifest, errors)
    assert not errors

    generated = tmp_path / PDF_BUILD_OUTPUT_RELATIVE
    generated.parent.mkdir(parents=True)
    generated.write_bytes(b"deliberately unrelated local observation")
    errors = []
    validator._validate_tex_build(tmp_path, manifest, errors)
    assert not errors

    altered = copy.deepcopy(manifest)
    altered["tex_build"]["pinned_container_image"] = "texlive/texlive:latest-medium"
    errors = []
    validator._validate_tex_build(tmp_path, altered, errors)
    assert any("build contract" in error for error in errors)

    (tmp_path / PDF_BUILD_HELPER_RELATIVE).write_text("drift\n", encoding="utf-8")
    errors = []
    validator._validate_tex_build(tmp_path, manifest, errors)
    assert any("build helper SHA-256 mismatch" in error for error in errors)
    shutil.copyfile(ROOT / PDF_BUILD_HELPER_RELATIVE, tmp_path / PDF_BUILD_HELPER_RELATIVE)

    (tmp_path / PDF_BUILD_REPORT_RELATIVE).write_text("drift\n", encoding="utf-8")
    errors = []
    validator._validate_tex_build(tmp_path, manifest, errors)
    assert any("build report SHA-256 mismatch" in error for error in errors)


def test_paper1_literature_delta_is_closed_bounded_and_recheck_gated() -> None:
    validator = _load_paper1_validator()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    literature = manifest["literature_delta_search"]

    assert literature["status"] == LITERATURE_DELTA_STATUS
    assert literature["completed"] is True
    assert literature["search_window"] == {
        "field": "submittedDate",
        "window_start_utc": "2026-07-31T15:00:00Z",
        "window_end_minute_utc": "2026-08-05T23:59:00Z",
        "window_end_exclusive_utc": "2026-08-06T00:00:00Z",
        "feed_cutoff_utc": "2026-08-05T04:52:45Z",
    }
    assert literature["official_repository"] == "arXiv"
    assert literature["screened_record_count"] == 556
    assert literature["archived_snapshot"] == validator._expected_literature_archived_snapshot()
    snapshot = literature["archived_snapshot"]
    assert snapshot["response_entry_count"] == 556
    assert snapshot["effective_response_query"]["field"] == "submittedDate"
    assert snapshot["entries_published_in_submitted_date_window"] == 556
    assert snapshot["entries_published_outside_submitted_date_window"] == 0
    assert snapshot["entries_published_at_or_before_feed_cutoff"] == 556
    assert snapshot["entries_published_after_feed_cutoff"] == 0
    assert snapshot["coverage_boundary"]["general_pre_window_version_updates_covered"] is False
    assert snapshot["reconciliation"]["comparison_to_archived_556_authorized"] is False
    assert snapshot["screening_decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 533,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 23,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }
    assert snapshot["ordered_arxiv_ids_sha256"] == (
        "5f8a03534e8ce34f289f0bccf7457ee6e808e6dc8efccb41cb54e8515d99c18d"
    )
    assert snapshot["records_sha256"] == (
        "1d53423d64956f4901980d315dee87ef834c775d17cacaefa3f6440778b14bb3"
    )
    for binding_name in ("raw_response", "normalized_ledger"):
        binding = snapshot[binding_name]
        path = ROOT / binding["path"]
        assert path.stat().st_size == binding["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["raw_sha256"]
    for binding_name in ("normalizer", "dedicated_test"):
        binding = snapshot[binding_name]
        assert (
            hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest()
            == (binding["raw_sha256"])
        )
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
        "historical_unarchived_observation": {
            "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
            "screened_record_count": 524,
            "query_provenance_known": False,
            "id_membership_known": False,
            "comparison_to_archived_556_authorized": False,
            "authoritative": False,
        },
        "historical_http_429": {
            "status": "NO_RESPONSE_RETAINED_NOT_EVIDENCE",
            "affects_archived_screening": False,
        },
        "archival_retrieval": {
            "status": "SUCCESS_NO_RETRY",
            "feed_updated_utc": "2026-08-05T04:52:45Z",
        },
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
        "query_archive_status": "LOCAL_ARTIFACTS",
        "excluded_hit_archive_status": "METADATA_ONLY",
        "excluded_hit_ids": ["arXiv:2608.03273v1", "arXiv:2608.02166v1"],
    }
    assert literature["material_delta_for_claim_labels"] == []
    assert literature["recheck_before_submission"] is True
    assert literature["full_overlap_recheck_before_submission"] is True
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
    note = " ".join(LITERATURE_NOTE_PATH.read_text(encoding="utf-8").split())
    assert "effective response query is a `submittedDate` window" in report
    assert "556-entry Atom snapshot" in report
    assert "23 title/abstract candidates" in report
    assert "zero C1--C5 material deltas" in report
    assert "full-overlap `submittedDate` response beginning" in report
    assert "does not close a general later-version-update gate" in report
    assert "does not compare it to, subtract it from" in report
    assert "not an absolute literature-absence, novelty, or priority determination" in report
    assert "Immediately before public submission" in note
    assert "effective query provenance and membership are both unknown" in note
    assert "is not compared with the archived 556 response" in note
    for source_id in literature["source_catalog_record_ids"]:
        assert source_id in report
        assert source_id in note

    source_catalog = json.loads((ROOT / "references/sources.json").read_text(encoding="utf-8"))
    archive = json.loads((ROOT / "references/manifest.json").read_text(encoding="utf-8"))
    catalog_by_id = {record["id"]: record for record in source_catalog["sources"]}
    archive_by_id = {record["id"]: record for record in archive["records"]}
    assert source_catalog["retrieved_on"] == "2026-08-05"
    query_id, *excluded_ids = literature["source_catalog_record_ids"]
    assert catalog_by_id[query_id]["local_file"] is None
    assert archive_by_id[query_id]["archive_status"] == "LOCAL_ARTIFACTS"
    assert catalog_by_id[query_id]["historical_unarchived_observation"] == {
        "reported_screened_record_count": 524,
        "status": "NONAUTHORITATIVE_UNARCHIVED_HISTORY_QUERY_AND_MEMBERSHIP_UNKNOWN",
        "query_provenance_known": False,
        "membership_known": False,
        "comparison_to_archived_556_authorized": False,
    }
    for source_id in excluded_ids:
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


def test_zenodo_literature_gate_is_hash_bound_and_owner_gated() -> None:
    validator = _load_paper1_validator()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    gate = manifest["zenodo_literature_gate"]

    assert gate == validator._expected_zenodo_literature_gate()
    assert gate["response_entry_count"] == 556
    assert gate["screening_decision_counts"] == {
        "NO_REPORT_DEFINED_TARGET_RULE_MATCH": 533,
        "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5": 23,
        "MATERIAL_DELTA_TO_C1_C5": 0,
    }
    assert gate["tracked_source_versions"] == {
        "arXiv:2607.26672": "v1",
        "arXiv:2603.25503": "v1",
    }
    assert gate["later_deposit_requires_new_dated_gate"] is True
    assert gate["authorization_boundary"] == {
        "technical_literature_gate_only": True,
        "manuscript_freeze_authorized": False,
        "submission_authorized": False,
        "deposit_authorized": False,
        "publication_authorized": False,
        "owner_only": True,
    }

    errors: list[str] = []
    validator._validate_zenodo_literature_gate(ROOT, manifest, errors)
    assert not errors

    altered = copy.deepcopy(manifest)
    altered["zenodo_literature_gate"]["id_set_equal_to_prior_gate"] = False
    errors = []
    validator._validate_zenodo_literature_gate(ROOT, altered, errors)
    assert "Zenodo literature-gate contract changed" in errors
