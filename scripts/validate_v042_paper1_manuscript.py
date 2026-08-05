"""Validate the non-frozen Paper I v0.4.2 manuscript scaffold.

The validator is deliberately read-only.  It verifies the manuscript snapshot,
its bibliography closure, and the claim/publication boundaries without
building a PDF or changing any research artifact.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from validate_v042_paper1_claim_boundary import validate_claim_boundary

from universe_lab.final_theory import (
    sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042 as bounded_scout_fixtures,
)

MANIFEST_PATH = Path("results/v0.4.2_paper1_manuscript_manifest.json")
MANUSCRIPT_ROOT = Path("paper/v0.4.2_paper1_statewise_operator")
CLAIM_LEDGER_PATH = Path("results/v0.4.2_paper1_claim_boundary.json")
EXPECTED_MANUSCRIPT_PATHS = {
    MANUSCRIPT_ROOT / "main.tex",
    MANUSCRIPT_ROOT / "REPRODUCING.md",
    MANUSCRIPT_ROOT / "references.bib",
}
EXPECTED_CLAIM_LABELS = ["C1", "C2", "C3", "C4", "C5"]
EXPECTED_NONCLAIM_LABELS = ["N1", "N2", "N3", "N4", "N5", "N6"]
MANIFEST_SCHEMA = "final-theory-v042-paper1-manuscript-manifest-v1"
CLAIM_LEDGER_SCHEMA = "final-theory-v042-paper1-claim-boundary-v1"
BOUNDED_SCOUT_MANIFEST_PATH = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_reproduction_manifest.json"
)
BOUNDED_SCOUT_EXPECTATIONS_PATH = Path(
    "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_bounded_scout_expectations.json"
)
BOUNDED_SCOUT_MANIFEST_SCHEMA = "sr2v-q5-free-bounded-scout-reproduction-input-manifest-v1"
BOUNDED_SCOUT_EXPECTATIONS_SCHEMA = "sr2v-q5-free-bounded-scout-expectations-v1"
BOUNDED_SCOUT_EXPECTATION_NAMES = ["row185_normal_form", "candidate_minor_only"]
BOUNDED_SCOUT_PENDING_STATUS = "PENDING_BOUNDED_SAGE_RECOMPUTATION"
BOUNDED_SCOUT_FINAL_STATUS = "PINNED"
BOUNDED_SCOUT_EXPECTATIONS_RAW_SHA256 = (
    "346aa987d9e29babc13b16c95fb088ea0c566a6e0704f8ae82c126e13a4e3f60"
)
BOUNDED_SCOUT_EXPECTATIONS_SEMANTIC_DIGEST_SHA256 = (
    "fd4a7fb3c9734abb324bf7d2e4bcb6c4296c3bb7e15f0c218b408a46f7f745da"
)
BOUNDED_SCOUT_EXPECTED_CORE_DIGESTS = {
    "row185_normal_form": "bd2d390ea996ea5149578bb569d6bba98fecbcb96b1b00d0fe8ff7b365f00deb",
    "candidate_minor_only": "cb9252dbc9d1610d3d0410f0d8f111a862b341cee59a4ced20bb8527c66a1c87",
}
LEGACY_OBSERVATION_STATUS = "NONDETERMINISTIC_LEGACY_OBSERVATION_NOT_A_REPRODUCTION_EXPECTATION"
LITERATURE_DELTA_STATUS = "CLOSED_NO_MATERIAL_DELTA_AS_OF_2026-08-05T01:43Z"
LITERATURE_AUDIT_REPORT_PATH = Path("reports/v0.4.2_paper1_literature_delta_2026-08-05.md")
LITERATURE_NOTE_PATH = Path("references/notes/v0.4.2_paper1_literature_delta_2026-08-05.md")
LITERATURE_SOURCES_PATH = Path("references/sources.json")
LITERATURE_ARCHIVE_MANIFEST_PATH = Path("references/manifest.json")
LITERATURE_AUDIT_REPORT_SHA256 = "8a592316412d9e5210dc80c9e891bac1575632d805f1f9b31cb6f8e9081018d9"
LITERATURE_NOTE_SHA256 = "b9334cf591c13ade693e3d145969d0add02e175a8807ae7e57361bcee717bfe8"
LITERATURE_CATEGORY_API_URL = (
    "https://export.arxiv.org/api/query?search_query="
    "lastUpdatedDate%3A%5B202607311500%20TO%20202608052359%5D%20AND%20"
    "(cat%3Agr-qc%20OR%20cat%3Aquant-ph%20OR%20cat%3Amath-ph%20OR%20"
    "cat%3Amath.OA%20OR%20cat%3Amath.RA%20OR%20cat%3Amath.AC%20OR%20"
    "cat%3Amath.FA%20OR%20cat%3Amath.CO)&start=0&max_results=2000&"
    "sortBy=lastUpdatedDate&sortOrder=descending"
)
LITERATURE_SOURCE_RECORD_IDS = [
    "arXiv:PaperI-literature-delta-query-2026-08-05",
    "arXiv:2608.03273v1",
    "arXiv:2608.02166v1",
]
LITERATURE_REFERENCE_ARCHIVE = {
    "sources_path": LITERATURE_SOURCES_PATH.as_posix(),
    "manifest_path": LITERATURE_ARCHIVE_MANIFEST_PATH.as_posix(),
    "status": "HASH_ONLY_SKIP_TEXT_PYPDF_UNAVAILABLE",
    "command": "scripts/archive_references.py --skip-text",
}
LITERATURE_SEARCH_WINDOW = {
    "start_utc": "2026-07-31T15:00:00Z",
    "effective_assessment_cutoff_utc": "2026-08-05T01:43:02Z",
    "category_api_coarse_upper_bound_utc": "2026-08-05T23:59Z",
}
LITERATURE_SCREENED_CATEGORIES = [
    "gr-qc",
    "quant-ph",
    "math-ph",
    "math.OA",
    "math.RA",
    "math.AC",
    "math.FA",
    "math.CO",
]
LITERATURE_REPORT_REQUIRED_FRAGMENTS = [
    f"Status: `{LITERATURE_DELTA_STATUS}`",
    "screened 524",
    "HTTP 429",
    "arXiv:PaperI-literature-delta-query-2026-08-05",
    "arXiv:2608.03273v1",
    "arXiv:2608.02166v1",
    "Before submission, repeat the official-arXiv version checks",
]
LITERATURE_NOTE_REQUIRED_FRAGMENTS = [
    f"Status: `{LITERATURE_DELTA_STATUS}`",
    "524 records",
    "arXiv:PaperI-literature-delta-query-2026-08-05",
    "arXiv:2608.03273v1",
    "arXiv:2608.02166v1",
    "mandatory immediately before public submission",
]
CANONICAL_LEDGER_DIGEST_METHOD = (
    "sha256(UTF-8 canonical JSON: ensure_ascii=true, sort_keys=true, separators=(',', ':'))"
)
BEGIN_END_PATTERN = re.compile(r"\\(begin|end)\{([^{}]+)\}")
CITATION_PATTERN = re.compile(r"\\cite[a-zA-Z*]*(?:\[[^\]]*\]){0,2}\{([^{}]+)\}")
BIB_ENTRY_PATTERN = re.compile(r"(?m)^\s*@\w+\s*\{\s*([^,\s]+)\s*,")
TEX_COMMENT_PATTERN = re.compile(r"(?<!\\)%[^\n]*")
NONCLAIM_ENUMERATION_PATTERN = re.compile(
    r"\\begin\{enumerate\}\[label=N\\arabic\*\.\](.*?)\\end\{enumerate\}", re.DOTALL
)
ITEM_PATTERN = re.compile(r"(?m)^\s*\\item\b")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json_object(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {label}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object")
        return None
    return payload


def _strip_tex_comments(source: str) -> str:
    return TEX_COMMENT_PATTERN.sub("", source)


def _normalise_whitespace(source: str) -> str:
    return " ".join(_strip_tex_comments(source).split())


def _validate_environment_balance(source: str, errors: list[str]) -> None:
    stack: list[str] = []
    for match in BEGIN_END_PATTERN.finditer(_strip_tex_comments(source)):
        action, environment = match.groups()
        if action == "begin":
            stack.append(environment)
        elif not stack:
            errors.append(f"unexpected \\end{{{environment}}}")
        elif stack[-1] != environment:
            errors.append(
                "environment nesting mismatch: "
                f"expected \\end{{{stack[-1]}}}, got \\end{{{environment}}}"
            )
            stack.pop()
        else:
            stack.pop()
    for environment in reversed(stack):
        errors.append(f"unclosed \\begin{{{environment}}}")


def _citation_keys(source: str) -> set[str]:
    keys: set[str] = set()
    for match in CITATION_PATTERN.finditer(_strip_tex_comments(source)):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return keys


def _bibliography_keys(path: Path, errors: list[str]) -> set[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read bibliography {path.as_posix()}: {exc}")
        return set()
    return set(BIB_ENTRY_PATTERN.findall(source))


def _manifest_file_records(
    manifest: dict[str, Any], errors: list[str]
) -> dict[Path, dict[str, Any]]:
    records = manifest.get("manuscript_files")
    if not isinstance(records, list):
        errors.append("manifest manuscript_files must be a list")
        return {}

    by_path: dict[Path, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            errors.append("manifest manuscript_files entry must be an object")
            continue
        path_value = record.get("path")
        if not isinstance(path_value, str):
            errors.append("manifest manuscript_files entry has no string path")
            continue
        path = Path(path_value)
        if path in by_path:
            errors.append(f"manifest repeats manuscript file {path.as_posix()}")
            continue
        by_path[path] = record

    _require(
        set(by_path) == EXPECTED_MANUSCRIPT_PATHS,
        "manifest must pin exactly main.tex, REPRODUCING.md, and references.bib",
        errors,
    )
    return by_path


def _validate_manifest_hashes(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    for relative, record in _manifest_file_records(manifest, errors).items():
        path = root / relative
        _require(path.is_file(), f"missing manuscript file: {relative.as_posix()}", errors)
        expected = record.get("raw_sha256")
        _require(
            isinstance(expected, str) and len(expected) == 64,
            f"invalid manuscript SHA-256 for {relative.as_posix()}",
            errors,
        )
        if path.is_file() and isinstance(expected, str):
            _require(
                _sha256(path) == expected,
                f"raw SHA-256 mismatch for {relative.as_posix()}",
                errors,
            )

    ledger_binding = manifest.get("claim_ledger")
    if not isinstance(ledger_binding, dict):
        errors.append("manifest claim_ledger must be an object")
        return
    _require(
        ledger_binding.get("path") == CLAIM_LEDGER_PATH.as_posix(),
        "manifest claim ledger path changed",
        errors,
    )
    ledger_path = root / CLAIM_LEDGER_PATH
    expected_raw = ledger_binding.get("raw_sha256")
    _require(
        isinstance(expected_raw, str) and len(expected_raw) == 64,
        "manifest claim ledger raw SHA-256 is invalid",
        errors,
    )
    if ledger_path.is_file() and isinstance(expected_raw, str):
        _require(
            _sha256(ledger_path) == expected_raw,
            "claim ledger raw SHA-256 mismatch",
            errors,
        )


def _validate_claim_ledger(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> dict[str, Any] | None:
    for error in validate_claim_boundary(root):
        errors.append(f"claim-boundary validator: {error}")

    ledger_path = root / CLAIM_LEDGER_PATH
    if not ledger_path.is_file():
        errors.append(f"missing claim ledger: {CLAIM_LEDGER_PATH.as_posix()}")
        return None
    ledger = _read_json_object(ledger_path, errors, "claim ledger")
    if ledger is None:
        return None

    binding = manifest.get("claim_ledger")
    if not isinstance(binding, dict):
        return ledger
    _require(
        binding.get("schema_version") == CLAIM_LEDGER_SCHEMA
        and ledger.get("schema_version") == CLAIM_LEDGER_SCHEMA,
        "claim ledger schema binding changed",
        errors,
    )
    _require(
        binding.get("semantic_digest_method") == CANONICAL_LEDGER_DIGEST_METHOD,
        "claim ledger semantic digest method changed",
        errors,
    )
    _require(
        binding.get("semantic_digest_sha256") == _canonical_json_sha256(ledger),
        "claim ledger semantic digest mismatch",
        errors,
    )
    _require(
        binding.get("ledger_status") == "SCOPED_MANUSCRIPT_ASSEMBLY_READY"
        and ledger.get("status") == "SCOPED_MANUSCRIPT_ASSEMBLY_READY",
        "claim ledger status changed",
        errors,
    )

    claims = ledger.get("claims")
    labels = (
        [
            item.get("id", "").split("_", 1)[0]
            for item in claims
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        if isinstance(claims, list)
        else []
    )
    _require(labels == EXPECTED_CLAIM_LABELS, "claim ledger C1--C5 labels changed", errors)
    _require(
        manifest.get("claim_labels") == EXPECTED_CLAIM_LABELS,
        "manifest C1--C5 labels changed",
        errors,
    )

    nonclaims = ledger.get("nonclaims")
    nonclaim_labels = (
        [
            item.get("id", "").split("_", 1)[0]
            for item in nonclaims
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        if isinstance(nonclaims, list)
        else []
    )
    _require(
        nonclaim_labels == EXPECTED_NONCLAIM_LABELS,
        "claim ledger N1--N6 nonclaims changed",
        errors,
    )
    _require(
        manifest.get("nonclaim_labels") == EXPECTED_NONCLAIM_LABELS,
        "manifest N1--N6 nonclaims changed",
        errors,
    )
    return ledger


def _validate_bibliography_and_tex(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    tex_path = root / MANUSCRIPT_ROOT / "main.tex"
    if not tex_path.is_file():
        errors.append(f"missing TeX source: {tex_path.as_posix()}")
        return
    try:
        tex = tex_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read TeX source: {exc}")
        return

    _validate_environment_balance(tex, errors)
    bibliography = manifest.get("bibliography")
    if not isinstance(bibliography, dict):
        errors.append("manifest bibliography must be an object")
        return
    expected_entries = bibliography.get("tex_entries")
    _require(
        expected_entries == ["../v0.3.9_d2_commutativity_short_report/references", "references"],
        "manifest bibliography TeX entries changed",
        errors,
    )
    matches = re.findall(r"\\bibliography\{([^{}]+)\}", _strip_tex_comments(tex))
    _require(len(matches) == 1, "TeX source must contain exactly one bibliography command", errors)
    entries = [part.strip() for part in matches[0].split(",")] if len(matches) == 1 else []
    _require(entries == expected_entries, "TeX bibliography entries do not match manifest", errors)

    shared_relative = Path("paper/v0.3.9_d2_commutativity_short_report/references.bib")
    local_relative = MANUSCRIPT_ROOT / "references.bib"
    _require(
        bibliography.get("shared_bib_path") == shared_relative.as_posix(),
        "shared bibliography path changed",
        errors,
    )
    _require(
        bibliography.get("local_bib_path") == local_relative.as_posix(),
        "local bibliography path changed",
        errors,
    )
    _require((root / shared_relative).is_file(), "shared bibliography file is missing", errors)
    _require((root / local_relative).is_file(), "local bibliography file is missing", errors)

    cited = _citation_keys(tex)
    _require(bool(cited), "TeX source has no citation keys", errors)
    shared_keys = _bibliography_keys(root / shared_relative, errors)
    local_keys = _bibliography_keys(root / local_relative, errors)
    missing = sorted(cited - shared_keys - local_keys)
    _require(
        not missing,
        f"citation keys absent from shared/local bibliographies: {missing}",
        errors,
    )
    _require("Xu2026Relational" in local_keys, "local bibliography lacks Xu2026Relational", errors)
    _require(
        {"RideoutSorkin2000", "SrivastavaSurya2026"} <= shared_keys,
        "shared bibliography lacks manuscript baseline citations",
        errors,
    )

    for label in EXPECTED_CLAIM_LABELS:
        _require(f"\\subsection{{{label}:" in tex, f"TeX source lacks {label} subsection", errors)
        _require(f"[{label}:" in tex, f"TeX source lacks {label} theorem/lemma label", errors)
    _require(
        "\\begin{enumerate}[label=N\\arabic*.]" in tex,
        "TeX source lacks the N1--N6 nonclaim enumeration",
        errors,
    )
    nonclaim_requirements = manifest.get("nonclaim_text_requirements")
    if not isinstance(nonclaim_requirements, list):
        errors.append("manifest nonclaim_text_requirements must be a list")
    else:
        requirement_ids = [
            item.get("id") for item in nonclaim_requirements if isinstance(item, dict)
        ]
        _require(
            requirement_ids == EXPECTED_NONCLAIM_LABELS,
            "manifest nonclaim text requirements must map N1--N6 in order",
            errors,
        )
        nonclaim_matches = NONCLAIM_ENUMERATION_PATTERN.findall(_strip_tex_comments(tex))
        _require(
            len(nonclaim_matches) == 1,
            "TeX source must contain exactly one N1--N6 nonclaim enumeration",
            errors,
        )
        item_count = len(ITEM_PATTERN.findall(nonclaim_matches[0])) if nonclaim_matches else 0
        _require(item_count == 6, "N1--N6 nonclaim enumeration must contain six items", errors)
        normalised_tex = _normalise_whitespace(tex)
        for requirement in nonclaim_requirements:
            if not isinstance(requirement, dict):
                errors.append("nonclaim text requirement must be an object")
                continue
            identifier = requirement.get("id")
            fragment = requirement.get("required_fragment")
            _require(
                isinstance(fragment, str) and fragment in normalised_tex,
                f"TeX source lacks explicit {identifier} nonclaim boundary",
                errors,
            )

    markers = manifest.get("draft_markers")
    if not isinstance(markers, dict):
        errors.append("manifest draft_markers must be an object")
        return
    token = markers.get("required_token")
    minimum = markers.get("minimum_invocations")
    _require(
        isinstance(token, str) and token in tex,
        "required DRAFT marker token is absent",
        errors,
    )
    _require(isinstance(minimum, int) and minimum > 0, "invalid DRAFT marker minimum", errors)
    invocation_count = len(re.findall(r"\\draftmarker\s*\{", _strip_tex_comments(tex)))
    if isinstance(minimum, int):
        _require(invocation_count >= minimum, "insufficient DRAFT marker invocations", errors)
    fragments = markers.get("required_tex_fragments")
    _require(isinstance(fragments, list), "draft marker fragments must be a list", errors)
    if isinstance(fragments, list):
        for fragment in fragments:
            _require(
                isinstance(fragment, str) and fragment in tex,
                f"required DRAFT boundary text is absent: {fragment!r}",
                errors,
            )


def _validate_state_boundary_text(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    requirements = manifest.get("state_boundary_text")
    if not isinstance(requirements, dict):
        errors.append("manifest state_boundary_text must be an object")
        return

    documents = {
        "main_tex_required_fragments": root / MANUSCRIPT_ROOT / "main.tex",
        "reproducing_required_fragments": root / MANUSCRIPT_ROOT / "REPRODUCING.md",
    }
    for field, path in documents.items():
        fragments = requirements.get(field)
        if not isinstance(fragments, list) or not fragments:
            errors.append(f"manifest {field} must be a nonempty list")
            continue
        try:
            source = _normalise_whitespace(path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"cannot read state-boundary document {path.as_posix()}: {exc}")
            continue
        for fragment in fragments:
            _require(
                isinstance(fragment, str) and fragment in source,
                f"state-boundary text missing from {path.name}: {fragment!r}",
                errors,
            )

    forbidden = requirements.get("reproducing_forbidden_fragments")
    if not isinstance(forbidden, list):
        errors.append("manifest reproducing_forbidden_fragments must be a list")
        return
    reproducing_path = root / MANUSCRIPT_ROOT / "REPRODUCING.md"
    try:
        reproducing_source = _normalise_whitespace(reproducing_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"cannot read state-boundary document {reproducing_path.as_posix()}: {exc}")
        return
    for fragment in forbidden:
        _require(
            isinstance(fragment, str) and fragment not in reproducing_source,
            f"forbidden reproduction-expectation text remains in REPRODUCING.md: {fragment!r}",
            errors,
        )


def _validate_bounded_scout_reproduction(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    """Require a pinned mathematical core without binding timing observations.

    The input manifest M authenticates the scripts, fixtures, and Sage image.
    The self-bound expectations artifact E records the two deterministic
    certificate-core digests after bounded Sage recomputation.  The Paper I
    manifest F then externally pins E's raw bytes, self semantic digest, and
    both core digests.  This acyclic M -> E -> F contract rejects a changed E
    even if E is self-rebound; timing observations remain outside the cores.
    """

    contract = manifest.get("bounded_scout_reproduction")
    if not isinstance(contract, dict):
        errors.append("manifest bounded_scout_reproduction must be an object")
        return

    expected_contract_keys = {
        "input_manifest",
        "expectations",
        "legacy_observation_status",
    }
    _require(
        set(contract) == expected_contract_keys,
        "bounded-scout reproduction contract keys changed",
        errors,
    )
    _require(
        contract.get("input_manifest")
        == {
            "path": BOUNDED_SCOUT_MANIFEST_PATH.as_posix(),
            "schema_version": BOUNDED_SCOUT_MANIFEST_SCHEMA,
        },
        "bounded-scout input-manifest binding changed",
        errors,
    )
    _require(
        contract.get("expectations")
        == {
            "path": BOUNDED_SCOUT_EXPECTATIONS_PATH.as_posix(),
            "schema_version": BOUNDED_SCOUT_EXPECTATIONS_SCHEMA,
            "pending_status": BOUNDED_SCOUT_PENDING_STATUS,
            "required_final_status": BOUNDED_SCOUT_FINAL_STATUS,
            "certificate_core_names": BOUNDED_SCOUT_EXPECTATION_NAMES,
            "raw_sha256": BOUNDED_SCOUT_EXPECTATIONS_RAW_SHA256,
            "semantic_digest_sha256": BOUNDED_SCOUT_EXPECTATIONS_SEMANTIC_DIGEST_SHA256,
            "certificate_core_digests": BOUNDED_SCOUT_EXPECTED_CORE_DIGESTS,
        },
        "bounded-scout expectations binding changed",
        errors,
    )
    _require(
        contract.get("legacy_observation_status") == LEGACY_OBSERVATION_STATUS,
        "legacy bounded-scout observations are not explicitly non-deterministic",
        errors,
    )

    try:
        input_manifest = bounded_scout_fixtures.validate_bounded_scout_reproduction_inputs(root)
        expectations = bounded_scout_fixtures.load_bounded_scout_expectations(
            root,
            str(input_manifest["semantic_digest_sha256"]),
        )
    except (OSError, RuntimeError, ValueError) as exc:
        errors.append(f"bounded-scout reproduction validation: {exc}")
        return

    _require(
        input_manifest.get("schema_version") == BOUNDED_SCOUT_MANIFEST_SCHEMA,
        "bounded-scout input-manifest schema changed",
        errors,
    )
    _require(
        expectations.get("schema_version") == BOUNDED_SCOUT_EXPECTATIONS_SCHEMA,
        "bounded-scout expectations schema changed",
        errors,
    )
    _require(
        _sha256(root / BOUNDED_SCOUT_EXPECTATIONS_PATH) == BOUNDED_SCOUT_EXPECTATIONS_RAW_SHA256,
        "bounded-scout expectations raw SHA-256 mismatch",
        errors,
    )
    _require(
        expectations.get("semantic_digest_sha256")
        == BOUNDED_SCOUT_EXPECTATIONS_SEMANTIC_DIGEST_SHA256,
        "bounded-scout expectations self semantic digest mismatch",
        errors,
    )
    _require(
        expectations.get("input_manifest_semantic_digest_sha256")
        == input_manifest.get("semantic_digest_sha256"),
        "bounded-scout expectations no longer bind the authenticated input manifest",
        errors,
    )
    _require(
        expectations.get("legacy_observation_status") == LEGACY_OBSERVATION_STATUS,
        "bounded-scout legacy result digests are not labelled as non-deterministic observations",
        errors,
    )

    core_digests = expectations.get("certificate_core_digests")
    legacy_digests = expectations.get("legacy_full_result_semantic_digests")
    if not isinstance(core_digests, dict):
        errors.append("bounded-scout certificate_core_digests must be an object")
        return
    if not isinstance(legacy_digests, dict):
        errors.append("bounded-scout legacy_full_result_semantic_digests must be an object")
        return
    _require(
        set(core_digests) == set(BOUNDED_SCOUT_EXPECTATION_NAMES),
        "bounded-scout certificate-core names changed",
        errors,
    )
    _require(
        core_digests == BOUNDED_SCOUT_EXPECTED_CORE_DIGESTS,
        "bounded-scout certificate-core digests differ from the Paper I binding",
        errors,
    )
    _require(
        set(legacy_digests) == set(BOUNDED_SCOUT_EXPECTATION_NAMES),
        "bounded-scout legacy result names changed",
        errors,
    )
    _require(
        not (set(core_digests.values()) & set(legacy_digests.values())),
        "legacy full-result digests must not serve as certificate-core expectations",
        errors,
    )

    status = expectations.get("status")
    _require(
        status in {BOUNDED_SCOUT_PENDING_STATUS, BOUNDED_SCOUT_FINAL_STATUS},
        "bounded-scout expectations status is unsupported",
        errors,
    )
    _require(
        status == BOUNDED_SCOUT_FINAL_STATUS,
        "bounded-scout certificate-core expectations remain "
        "PENDING_BOUNDED_SAGE_RECOMPUTATION; final Paper I validation requires PINNED",
        errors,
    )


def _validate_literature_source_archive(root: Path, errors: list[str]) -> None:
    """Authenticate the three metadata-only records used by the dated gate."""

    catalog = _read_json_object(root / LITERATURE_SOURCES_PATH, errors, "reference source catalog")
    archive = _read_json_object(
        root / LITERATURE_ARCHIVE_MANIFEST_PATH,
        errors,
        "reference archive manifest",
    )
    if catalog is None or archive is None:
        return
    _require(
        catalog.get("schema_version") == "1.0" and catalog.get("retrieved_on") == "2026-08-05",
        "reference source catalog schema or retrieval date changed",
        errors,
    )
    source_records = catalog.get("sources")
    archive_records = archive.get("records")
    if not isinstance(source_records, list):
        errors.append("reference source catalog sources must be a list")
        return
    if not isinstance(archive_records, list):
        errors.append("reference archive manifest records must be a list")
        return

    def by_id(records: list[Any], label: str) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                errors.append(f"{label} has a malformed record")
                continue
            identifier = record["id"]
            if identifier in indexed:
                errors.append(f"{label} repeats record {identifier}")
                continue
            indexed[identifier] = record
        return indexed

    catalog_by_id = by_id(source_records, "reference source catalog")
    archive_by_id = by_id(archive_records, "reference archive manifest")
    _require(
        archive.get("schema_version") == "1.0"
        and archive.get("catalog") == LITERATURE_SOURCES_PATH.as_posix(),
        "reference archive manifest schema or catalog binding changed",
        errors,
    )
    for identifier in LITERATURE_SOURCE_RECORD_IDS:
        _require(
            identifier in catalog_by_id,
            f"reference source catalog lacks literature-delta record {identifier}",
            errors,
        )
        _require(
            identifier in archive_by_id,
            f"reference archive manifest lacks literature-delta record {identifier}",
            errors,
        )
        if identifier not in catalog_by_id or identifier not in archive_by_id:
            continue
        source = catalog_by_id[identifier]
        archived = archive_by_id[identifier]
        _require(
            archived.get("archive_status") == "METADATA_ONLY"
            and archived.get("sha256") is None
            and archived.get("bytes") is None
            and archived.get("pages") is None
            and archived.get("text_file") is None,
            f"literature-delta record {identifier} must remain metadata-only",
            errors,
        )
        archived_source = {
            key: value
            for key, value in archived.items()
            if key not in {"archive_status", "sha256", "bytes", "pages", "text_file"}
        }
        _require(
            archived_source == source,
            f"reference archive manifest differs from source catalog for {identifier}",
            errors,
        )

    query = catalog_by_id.get(LITERATURE_SOURCE_RECORD_IDS[0])
    if query is not None:
        _require(
            query.get("url") == LITERATURE_CATEGORY_API_URL
            and query.get("relationship") == "SEARCH_DATASET"
            and query.get("local_file") is None,
            "literature-delta official query provenance changed",
            errors,
        )
        _require(
            query.get("used_for")
            == [
                "bounded Paper I literature-delta gate for C1--C5",
                "checking new records and later version updates after the 2026-08-01 ledger cutoff",
            ],
            "literature-delta official query use boundary changed",
            errors,
        )
        _require(
            isinstance(query.get("claim_boundary"), str)
            and "HTTP 429" in query["claim_boundary"]
            and "No local PDF applies" in query["claim_boundary"],
            "literature-delta official query claim boundary changed",
            errors,
        )

    expected_hits = {
        "arXiv:2608.03273v1": {
            "title": (
                "On the Asymptotic of Coupled Spherical Integrals: An Operator-Valued "
                "Extension of the Free Fourier Transform"
            ),
            "authors": ["Levi-Pascal V. G. Bohnacker", "Ralf R. Müller"],
            "url": "https://arxiv.org/abs/2608.03273v1",
            "pdf_url": "https://arxiv.org/pdf/2608.03273v1",
            "version": "v1, 2026-08-04",
        },
        "arXiv:2608.02166v1": {
            "title": (
                "Generalized Temporal Coupled Mode Theory (g-TCMT) applied to Coupled "
                "Resonator Optical Waveguides with Exchange Symmetry (CROWe)"
            ),
            "authors": ["Tianrui Li", "Matthew P. Halsall", "Iain F. Crowe"],
            "url": "https://arxiv.org/abs/2608.02166v1",
            "pdf_url": "https://arxiv.org/pdf/2608.02166v1",
            "version": "v1, 2026-08-03",
        },
    }
    for identifier, expected in expected_hits.items():
        record = catalog_by_id.get(identifier)
        if record is None:
            continue
        _require(
            all(record.get(key) == value for key, value in expected.items())
            and record.get("retrieved_on") == "2026-08-05"
            and record.get("relationship") == "SCREENED_NONMATERIAL"
            and record.get("local_file") is None,
            f"nonmaterial literature-hit metadata changed: {identifier}",
            errors,
        )
        _require(
            isinstance(record.get("claim_boundary"), str)
            and "no local PDF or extracted text is retained" in record["claim_boundary"],
            f"nonmaterial literature-hit PDF-retention boundary changed: {identifier}",
            errors,
        )


def _validate_literature_delta_search(
    root: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    """Fail closed on the bounded Paper I literature-delta record.

    The record is deliberately a dated screening gate, not an absence or
    priority assertion.  Both the detailed report and the required research
    note are byte-pinned because their interpretive boundary affects whether
    the draft may proceed to its still-owner-gated publication steps.
    """

    literature = manifest.get("literature_delta_search")
    if not isinstance(literature, dict):
        errors.append("manifest literature_delta_search must be an object")
        return

    expected_keys = {
        "since",
        "search_window",
        "status",
        "completed",
        "audit_report",
        "note_path",
        "note_raw_sha256",
        "official_repository",
        "screened_record_count",
        "screened_categories",
        "targeted_categories",
        "tracked_source_versions",
        "keyword_hits_not_material",
        "companion_public_arxiv_record_located",
        "post_completion_requery",
        "source_catalog_record_ids",
        "reference_archive",
        "material_delta_for_claim_labels",
        "recheck_before_submission",
        "priority_or_absolute_absence_claimed",
    }
    _require(
        set(literature) == expected_keys,
        "literature delta search keys changed",
        errors,
    )
    _require(literature.get("since") == "2026-08-01", "literature delta baseline changed", errors)
    _require(
        literature.get("search_window") == LITERATURE_SEARCH_WINDOW,
        "literature delta search window changed",
        errors,
    )
    _require(
        literature.get("status") == LITERATURE_DELTA_STATUS,
        "literature delta status is not the closed 2026-08-05 result",
        errors,
    )
    _require(literature.get("completed") is True, "literature delta search is incomplete", errors)
    _require(
        literature.get("official_repository") == "arXiv",
        "literature delta official repository changed",
        errors,
    )
    _require(
        literature.get("screened_record_count") == 524,
        "literature delta screened-record count changed",
        errors,
    )
    _require(
        literature.get("screened_categories") == LITERATURE_SCREENED_CATEGORIES,
        "literature delta screened categories changed",
        errors,
    )
    _require(
        literature.get("targeted_categories") == ["math.PR", "physics.*"],
        "literature delta targeted categories changed",
        errors,
    )
    _require(
        literature.get("tracked_source_versions")
        == {"arXiv:2607.26672": "v1", "arXiv:2603.25503": "v1"},
        "literature delta direct version checks changed",
        errors,
    )
    _require(
        literature.get("keyword_hits_not_material") == ["arXiv:2608.03273", "arXiv:2608.02166"],
        "literature delta keyword-hit boundary changed",
        errors,
    )
    _require(
        literature.get("companion_public_arxiv_record_located") is False,
        "literature delta companion-record boundary changed",
        errors,
    )
    _require(
        literature.get("post_completion_requery")
        == {
            "status": "HTTP_429_RATE_LIMITED_AFTER_COMPLETION",
            "affects_completed_screening": False,
        },
        "literature delta rate-limit record changed",
        errors,
    )
    _require(
        literature.get("source_catalog_record_ids") == LITERATURE_SOURCE_RECORD_IDS,
        "literature delta source-catalog record IDs changed",
        errors,
    )
    _require(
        literature.get("reference_archive") == LITERATURE_REFERENCE_ARCHIVE,
        "literature delta reference-archive validation boundary changed",
        errors,
    )
    _require(
        literature.get("material_delta_for_claim_labels") == [],
        "literature delta no longer records an empty C1--C5 material delta",
        errors,
    )
    _require(
        literature.get("recheck_before_submission") is True,
        "literature delta must require a pre-submission recheck",
        errors,
    )
    _require(
        literature.get("priority_or_absolute_absence_claimed") is False,
        "literature delta must not make priority or absolute-absence claims",
        errors,
    )

    report_binding = literature.get("audit_report")
    _require(
        report_binding
        == {
            "path": LITERATURE_AUDIT_REPORT_PATH.as_posix(),
            "raw_sha256": LITERATURE_AUDIT_REPORT_SHA256,
        },
        "literature delta audit-report binding changed",
        errors,
    )
    _require(
        literature.get("note_path") == LITERATURE_NOTE_PATH.as_posix(),
        "literature delta research-note path changed",
        errors,
    )
    _require(
        literature.get("note_raw_sha256") == LITERATURE_NOTE_SHA256,
        "literature delta research-note SHA-256 changed",
        errors,
    )

    for path, expected_hash, fragments, label in (
        (
            LITERATURE_AUDIT_REPORT_PATH,
            LITERATURE_AUDIT_REPORT_SHA256,
            LITERATURE_REPORT_REQUIRED_FRAGMENTS,
            "literature delta audit report",
        ),
        (
            LITERATURE_NOTE_PATH,
            LITERATURE_NOTE_SHA256,
            LITERATURE_NOTE_REQUIRED_FRAGMENTS,
            "literature delta research note",
        ),
    ):
        absolute = root / path
        _require(absolute.is_file(), f"missing {label}: {path.as_posix()}", errors)
        if not absolute.is_file():
            continue
        _require(
            _sha256(absolute) == expected_hash,
            f"raw SHA-256 mismatch for {label}",
            errors,
        )
        try:
            source = absolute.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot read {label}: {exc}")
            continue
        for fragment in fragments:
            _require(
                fragment in source,
                f"{label} lacks required boundary text: {fragment!r}",
                errors,
            )

    _validate_literature_source_archive(root, errors)


def _validate_status_boundaries(
    manifest: dict[str, Any], ledger: dict[str, Any] | None, errors: list[str]
) -> None:
    _require(
        manifest.get("schema_version") == MANIFEST_SCHEMA,
        "unexpected manuscript manifest schema_version",
        errors,
    )
    _require(
        manifest.get("status") == "DRAFT_SCAFFOLD_NOT_FROZEN",
        "manuscript is not marked as a non-frozen draft scaffold",
        errors,
    )
    tex_build = manifest.get("tex_build")
    if not isinstance(tex_build, dict):
        errors.append("manifest tex_build must be an object")
    else:
        _require(
            tex_build.get("toolchain_status") == "ABSENT",
            "TeX toolchain status changed",
            errors,
        )
        _require(tex_build.get("pdf_status") == "UNBUILT", "PDF status changed", errors)
        _require(tex_build.get("pdf_verified") is False, "PDF must remain unverified", errors)

    freeze = manifest.get("freeze")
    if not isinstance(freeze, dict):
        errors.append("manifest freeze must be an object")
    else:
        _require(freeze.get("status") == "NOT_FROZEN", "freeze status changed", errors)
        _require(freeze.get("frozen") is False, "manuscript must remain unfrozen", errors)
        _require(
            freeze.get("authorized") is False,
            "manuscript freeze must remain unauthorized",
            errors,
        )

    gates = manifest.get("publication_gates")
    if not isinstance(gates, dict):
        errors.append("manifest publication_gates must be an object")
    else:
        for gate_name in ("submission", "deposit"):
            gate = gates.get(gate_name)
            if not isinstance(gate, dict):
                errors.append(f"manifest {gate_name} gate must be an object")
                continue
            _require(
                gate.get("status") == "OWNER_ONLY_NOT_AUTHORIZED",
                f"{gate_name} is not owner-only and unauthorized",
                errors,
            )
            _require(gate.get("owner_only") is True, f"{gate_name} must remain owner-only", errors)
            _require(
                gate.get("authorized") is False,
                f"{gate_name} must remain unauthorized",
                errors,
            )

    boundary = manifest.get("version_boundary")
    if not isinstance(boundary, dict):
        errors.append("manifest version_boundary must be an object")
        return
    _require(
        boundary.get("global_sr2v_status") == "SEARCH_OPEN_NO_TERMINAL",
        "global SR2-V status changed",
        errors,
    )
    _require(
        boundary.get("u2_role") == "SUBROUTE_ONLY_NONTERMINAL",
        "U2 must remain a subroute-only nonterminal boundary",
        errors,
    )
    _require(
        boundary.get("u2_is_global_terminal") is False,
        "U2 cannot be a global terminal",
        errors,
    )
    reproducibility = manifest.get("reproducibility_boundary")
    if not isinstance(reproducibility, dict):
        errors.append("manifest reproducibility_boundary must be an object")
    else:
        expected_reproducibility = {
            "stage7_fixture_inputs_tracked": True,
            "bounded_scout_subset_fixture_tracked": True,
            "bounded_scouts_clone_portable": True,
            "full_3161_record_polynomial_arena_tracked": False,
            "full_bundle_clone_reproducible": False,
            "stage7_worker_reexecution": False,
            "derived_bounded_scout_calculation": True,
            "raw_stage8_event_replay_available": False,
            "sage_free_fixture_selection_test_available": True,
            "certificate_core_expectations_final_status": BOUNDED_SCOUT_FINAL_STATUS,
        }
        for field, expected in expected_reproducibility.items():
            _require(
                reproducibility.get(field) == expected,
                f"reproducibility boundary changed: {field}",
                errors,
            )
    if ledger is not None:
        version_lanes = ledger.get("version_lanes")
        if not isinstance(version_lanes, dict):
            errors.append("claim ledger version_lanes must be an object")
        else:
            _require(
                version_lanes.get("sr2v_global_status") == "SEARCH_OPEN_NO_TERMINAL",
                "claim ledger global SR2-V status changed",
                errors,
            )
            _require(
                version_lanes.get("u2_subroute_is_not_sr2v_terminal") is True,
                "claim ledger no longer marks U2 as subroute-only",
                errors,
            )


def validate_paper1_manuscript(root: Path) -> list[str]:
    """Return validation errors; an empty list means the draft boundary holds."""

    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH
    _require(manifest_path.is_file(), f"missing manuscript manifest: {MANIFEST_PATH}", errors)
    if errors:
        return errors
    manifest = _read_json_object(manifest_path, errors, "manuscript manifest")
    if manifest is None:
        return errors

    _validate_manifest_hashes(root, manifest, errors)
    ledger = _validate_claim_ledger(root, manifest, errors)
    _validate_bibliography_and_tex(root, manifest, errors)
    _validate_state_boundary_text(root, manifest, errors)
    _validate_bounded_scout_reproduction(root, manifest, errors)
    _validate_literature_delta_search(root, manifest, errors)
    _validate_status_boundaries(manifest, ledger, errors)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_paper1_manuscript(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("paper1_manuscript=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
