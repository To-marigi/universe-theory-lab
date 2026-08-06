"""Archive and verify the independent 2026-08-06T2315Z Zenodo predraft gate.

The earlier 2026-08-06 Zenodo-preparation gate remains immutable evidence.
This wrapper reuses its parser, screening rules, exact-ID checker, and
fail-closed ID-keyed comparison on newly archived official arXiv responses.
It is a technical literature gate only; it cannot authorize draft creation,
freeze, deposit, DOI reservation, or publication.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PRIOR_NORMALIZER_PATH = ROOT / "scripts/normalize_v042_paper1_zenodo_gate_20260806.py"
PRIOR_GATE_LEDGER = Path(
    "references/papers/2026-08-06_paper1_zenodo_predraft_20260806T1123Z_"
    "arxiv_normalized.json"
)
RAW_RESPONSE = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_full_overlap_atom.xml"
)
EXACT_ID_RESPONSE = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_exact_ids_atom.xml"
)
RETRIEVAL_RECEIPT = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_retrieval.json"
)
OUTPUT_LEDGER = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_normalized.json"
)
SOURCES = Path("references/sources.json")
ARCHIVE_MANIFEST = Path("references/manifest.json")
SOURCE_ID = "arXiv:PaperI-zenodo-predraft-gate-2026-08-06T2315Z"
PRIOR_SOURCE_ID = "arXiv:PaperI-zenodo-predraft-gate-2026-08-06T1123Z"
GATE_TRIGGER_UTC = "2026-08-06T23:15:00Z"
NORMALIZER_PATH = "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py"
CHECK_COMMAND = (
    ".venv\\Scripts\\python.exe "
    "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py --check"
)
FETCH_COMMAND = (
    ".venv\\Scripts\\python.exe "
    "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py --fetch"
)
USER_AGENT = "universe-theory-lab/0.4.2 (Paper I Zenodo predraft literature gate)"
OWNER_ONLY_AUTHORIZATION_FRAGMENT = (
    "This artifact closes only a technical literature-delta gate. It does not authorize "
    "manuscript freeze, submission, deposit, or publication; all such actions are "
    "owner-only and remain unapproved."
)
AUTHORIZATION_BOUNDARY = {
    "technical_literature_gate_only": True,
    "manuscript_freeze_authorized": False,
    "submission_authorized": False,
    "deposit_authorized": False,
    "publication_authorized": False,
    "owner_only": True,
}
KNOWN_CANDIDATE_RATIONALES = {
    "2608.04947v1": (
        "Sol title/abstract review: this is a trace-distance continuity result for Petz and "
        "sandwiched Renyi conditional entropies. Its Schmidt-rank and noncommutative matrix "
        "calibration language does not formulate causal sets, quantum sequential growth, "
        "CPOBC, GC/MSR, or statewise-to-operator recovery."
    ),
    "2608.05077v1": (
        "Sol title/abstract review: this is operator-theoretic quantitative homogenization, "
        "using Schur complements and a Sylvester commutator. It contains no causal-growth "
        "semantics, CPOBC relation system, or C1--C5 claim."
    ),
    "2608.04456v1": (
        "Sol title/abstract review: this studies free-splitting graph complexes and "
        "connectivity of Outer space. Its commutative-graph-complex phrase is unrelated to "
        "finite matrix CPOBC or statewise recovery."
    ),
    "2608.04263v1": (
        "Sol title/abstract review: this concerns QSVT, block encodings, a Weyl--Poisson "
        "identity, and LCHS quadrature. It does not study quantum sequential growth, CPOBC, "
        "or the state/operator semantic boundaries C1--C5."
    ),
    "2608.04685v1": (
        "Sol title/abstract review: this concerns indefinite causal order and open-system "
        "memory in the quantum SWITCH. It is not a causal-set growth or CPOBC transition "
        "relation result."
    ),
}
PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES: dict[str, str] = {}
HISTORICAL_VERSION_UPDATE_RATIONALES = {
    "2607.29501": (
        "Sol title/abstract v1-to-v2 review: the summary/comment remains about polaritons, "
        "not CPOBC, quantum sequential growth, or any C1--C5 boundary."
    ),
    "2608.00710": (
        "Sol title/abstract v1-to-v2 review: the expansion concerns a Poisson fixed-point "
        "and multiset-permutation result, not the finite CPOBC/statewise recovery problem."
    ),
    "2608.01121": (
        "Sol title/abstract v1-to-v2 review: the summary remains a QAOA optimization result, "
        "with no causal-set growth, CPOBC, or C1--C5 content."
    ),
    "2608.01680": (
        "Sol title/abstract v1-to-v2 review: the unchanged subject is a PT optical-lattice "
        "BEC, not a CPOBC or statewise/operator result."
    ),
    "2608.01774": (
        "Sol title/abstract v1-to-v2 review: changes are typos or ancillary material in a "
        "post-Newtonian binary study, with no Paper I relation."
    ),
    "2608.02350": (
        "Sol title/abstract v1-to-v2 review: the unchanged subject is NV-diamond sensing, "
        "not causal-set sequential growth or CPOBC."
    ),
    "2608.02546": (
        "Sol title/abstract v1-to-v2 review: the unchanged subject is a variable-radius disk "
        "transform, not the finite matrix CPOBC relation system."
    ),
    "2608.02652": (
        "Sol title/abstract v1-to-v2 review: the discussion-only change concerns wormhole "
        "energy conditions, not CPOBC/statewise semantics."
    ),
    "2608.03697": (
        "Sol title/abstract v1-to-v2 review: typo and clarification changes concern general-"
        "relativistic enstrophy, not any C1--C5 claim."
    ),
    "2608.03714": (
        "Sol title/abstract v1-to-v2 review: capitalization-only changes concern a Kondo "
        "lattice, not causal-set growth or CPOBC."
    ),
    "2608.03828": (
        "Sol title/abstract v1-to-v2 review: expanded complementary-measurement/CQC/ECQC "
        "content and classical rank-two states do not state CPOBC or statewise recovery."
    ),
    "2608.03987": (
        "Sol title/abstract v1-to-v2 review: the unchanged subject is realified tensor "
        "networks, not a Paper I CPOBC or semantic-recovery result."
    ),
}
PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES: dict[str, str] = {}
HISTORICAL_SHARED_METADATA_RATIONALES = {
    "2608.02182v1": {
        "changed_fields": ["categories"],
        "prior_categories": ["math-ph", "math.DS"],
        "predraft_categories": ["astro-ph.EP", "math-ph", "math.DS"],
        "rationale": (
            "Sol title/abstract review: the added astro-ph.EP category concerns Laskar "
            "frequency-map analysis, Diophantine/Brjuno nonresonance, celestial mechanics, "
            "and weighted Birkhoff averages; it has no CPOBC, QSG, GC/MSR, or statewise "
            "operator claim."
        ),
    },
    "2608.02458v1": {
        "changed_fields": ["categories"],
        "prior_categories": ["astro-ph.CO", "gr-qc"],
        "predraft_categories": ["astro-ph.CO", "gr-qc", "hep-th"],
        "rationale": (
            "Sol title/abstract review: the added hep-th category accompanies preferred-"
            "direction matter, FLRW perturbation mixing, and gravitational-wave content; it "
            "does not formulate causal sets, QSG, CPOBC, or statewise recovery."
        ),
    },
}
PREDRAFT_REVIEWED_SHARED_METADATA_RATIONALES: dict[str, dict[str, Any]] = {}
# This exact zero-delta comparison was independently reviewed by Sol. A changed
# ID, metadata, version, screening, or candidate delta must fail rather than
# inheriting that review.
EXPECTED_REVIEWED_DELTA: dict[str, Any] = {
    "added_count": 0,
    "added_ids_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "missing_count": 0,
    "missing_ids_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "version_pair_count": 0,
    "version_pairs_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "replacement_base_ids": [],
    "new_no_target_count": 0,
    "new_rule_triggered_ids": [],
    "new_rule_triggered_ids_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
    "prior_candidate_count": 28,
    "predraft_candidate_count": 28,
    "shared_metadata_changed_ids": [],
    "shared_screening_changed_ids": [],
    "shared_metadata_review_ids_sha256": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    ),
}


class PredraftGateReviewRequired(ValueError):
    """An unclassified literature change prevents automatic predraft closure."""


def _load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load prior gate normalizer: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


PRIOR_GATE = _load_module(PRIOR_NORMALIZER_PATH, "v042_paper1_zenodo_predraft_prior_gate")
FULL_OVERLAP_REQUEST_URL = PRIOR_GATE.FULL_OVERLAP_REQUEST_URL
EXACT_ID_REQUEST_URL = PRIOR_GATE.EXACT_ID_REQUEST_URL
QUERY_WINDOW_START = PRIOR_GATE.QUERY_WINDOW_START
QUERY_WINDOW_END = PRIOR_GATE.QUERY_WINDOW_END
QUERY_CATEGORIES = PRIOR_GATE.QUERY_CATEGORIES
BASE_INSPECTED_NONMATERIAL_RATIONALES = dict(
    PRIOR_GATE.SCREENING_NORMALIZER.INSPECTED_NONMATERIAL_RATIONALES
)


def _canonical_bytes(value: Any) -> bytes:
    return PRIOR_GATE._canonical_bytes(value)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return PRIOR_GATE._load_json(path)


def _gate_status(feed_updated_utc: str) -> str:
    return f"CLOSED_NO_MATERIAL_DELTA_WITHIN_ZENODO_PREDRAFT_GATE_AS_OF_{feed_updated_utc}"


def _configure_prior_gate_endpoints() -> None:
    """Point the reusable fetch/exact-ID helpers at this distinct artifact set."""

    reusable = cast(Any, PRIOR_GATE)
    reusable.RAW_RESPONSE = RAW_RESPONSE
    reusable.EXACT_ID_RESPONSE = EXACT_ID_RESPONSE
    reusable.RETRIEVAL_RECEIPT = RETRIEVAL_RECEIPT
    reusable.OUTPUT_LEDGER = OUTPUT_LEDGER
    reusable.FULL_OVERLAP_REQUEST_URL = FULL_OVERLAP_REQUEST_URL
    reusable.EXACT_ID_REQUEST_URL = EXACT_ID_REQUEST_URL
    reusable.USER_AGENT = USER_AGENT


def _configure_screening_normalizer(feed_updated_utc: str) -> None:
    """Reuse the established offline title/abstract screening contract unchanged."""

    screening = cast(Any, PRIOR_GATE.SCREENING_NORMALIZER)
    screening.RAW_RESPONSE = RAW_RESPONSE
    screening.OUTPUT_LEDGER = OUTPUT_LEDGER
    screening.SOURCE_ID = SOURCE_ID
    screening.GATE_STATUS = _gate_status(feed_updated_utc)
    screening.QUERY_FIELD = "submittedDate"
    screening.QUERY_WINDOW_START = QUERY_WINDOW_START
    screening.QUERY_WINDOW_END = QUERY_WINDOW_END
    screening.QUERY_CATEGORIES = QUERY_CATEGORIES
    screening.QUERY_START = 0
    screening.QUERY_MAX_RESULTS = 2000
    screening.INSPECTED_NONMATERIAL_RATIONALES = {
        **BASE_INSPECTED_NONMATERIAL_RATIONALES,
        **KNOWN_CANDIDATE_RATIONALES,
    }


def fetch() -> None:
    """Fetch once, retrying only when no evidence artifact was written."""

    _configure_prior_gate_endpoints()
    attempts = 3
    targets = [ROOT / RAW_RESPONSE, ROOT / EXACT_ID_RESPONSE, ROOT / RETRIEVAL_RECEIPT]
    for attempt in range(1, attempts + 1):
        try:
            PRIOR_GATE.fetch()
            return
        except FileExistsError:
            raise
        except (OSError, RuntimeError) as exc:
            existing = [path for path in targets if path.exists()]
            if existing or attempt == attempts:
                raise RuntimeError(
                    "official arXiv predraft retrieval failed without a safely repeatable "
                    f"state on attempt {attempt}/{attempts}: {exc}"
                ) from exc
            print(
                f"arXiv predraft retrieval attempt {attempt}/{attempts} failed; retrying: {exc}",
                file=sys.stderr,
            )
            time.sleep(3)


def _candidate_ids_sha256(ledger: dict[str, Any]) -> str:
    candidates = sorted(ledger["screening"]["inspected_candidate_ids"])
    payload = json.dumps(candidates, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(payload)


def _compact_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return _sha256_bytes(payload.encode("utf-8"))


def _record_map(records: list[dict[str, Any]], transform: Any) -> dict[str, Any]:
    result = {record["arxiv_id"]: transform(record) for record in records}
    if len(result) != len(records):
        raise ValueError("duplicate versioned arXiv ID in normalized predraft response")
    return result


def _metadata_without_order_or_screening(record: dict[str, Any]) -> dict[str, Any]:
    excluded = {"response_index", "screening"}
    return {key: value for key, value in record.items() if key not in excluded}


def _base_version_map(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    versions: dict[str, list[str]] = {}
    for record in records:
        versions.setdefault(record["base_id"], []).append(record["arxiv_id"])
    return {base_id: sorted(ids) for base_id, ids in versions.items()}


def _require_scope_and_cutoff_progression(
    prior: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    prior_query = prior["effective_response_query"]
    query = current["effective_response_query"]
    required_equal = [
        "field",
        "window_start_compact_utc",
        "window_end_compact_utc",
        "categories",
        "start",
        "max_results",
        "id_list",
    ]
    changed = [key for key in required_equal if prior_query.get(key) != query.get(key)]
    prior_cutoff = PRIOR_GATE.SCREENING_NORMALIZER._parse_utc(
        prior["raw_response"]["feed_updated_utc"], label="prior feed cutoff"
    )
    current_cutoff = PRIOR_GATE.SCREENING_NORMALIZER._parse_utc(
        current["raw_response"]["feed_updated_utc"], label="predraft feed cutoff"
    )
    if changed:
        raise PredraftGateReviewRequired(
            f"SOL_REVIEW_REQUIRED_QUERY_SCOPE_DRIFT: changed prior query fields={changed}"
        )
    if current_cutoff < prior_cutoff:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_NONMONOTONE_FEED_CUTOFF: predraft feed predates prior gate"
        )
    return {
        "query_semantics_equal": True,
        "feed_cutoff_monotone": True,
        "prior_feed_updated_utc": prior["raw_response"]["feed_updated_utc"],
        "predraft_feed_updated_utc": current["raw_response"]["feed_updated_utc"],
        "prior_response_entry_count": len(prior["records"]),
        "predraft_response_entry_count": len(current["records"]),
    }


def _reviewed_delta_decisions(
    prior: dict[str, Any],
    current: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind the complete, Sol-reviewed versioned-ID delta to this raw response."""

    scope = _require_scope_and_cutoff_progression(prior, current)
    prior_records = prior["records"]
    records = current["records"]
    prior_metadata = _record_map(prior_records, _metadata_without_order_or_screening)
    metadata = _record_map(records, _metadata_without_order_or_screening)
    prior_screening = _record_map(prior_records, lambda record: record["screening"])
    screening = _record_map(records, lambda record: record["screening"])
    prior_ids = set(prior_metadata)
    ids = set(metadata)
    added_ids = sorted(ids - prior_ids)
    missing_ids = sorted(prior_ids - ids)
    metadata_changed_ids = sorted(
        arxiv_id
        for arxiv_id in ids & prior_ids
        if metadata[arxiv_id] != prior_metadata[arxiv_id]
    )
    screening_changed_ids = sorted(
        arxiv_id
        for arxiv_id in ids & prior_ids
        if screening[arxiv_id] != prior_screening[arxiv_id]
    )
    if screening_changed_ids:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: shared versioned-ID screening changed: "
            f"{screening_changed_ids}"
        )
    if set(metadata_changed_ids) != set(PREDRAFT_REVIEWED_SHARED_METADATA_RATIONALES):
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_SHARED_METADATA_DRIFT: shared metadata IDs differ from "
            "the Sol-reviewed category-only set"
        )
    shared_metadata_review = []
    for arxiv_id in sorted(PREDRAFT_REVIEWED_SHARED_METADATA_RATIONALES):
        review = PREDRAFT_REVIEWED_SHARED_METADATA_RATIONALES[arxiv_id]
        changed_fields = sorted(
            key
            for key in metadata[arxiv_id]
            if metadata[arxiv_id][key] != prior_metadata[arxiv_id][key]
        )
        if changed_fields != review["changed_fields"]:
            raise PredraftGateReviewRequired(
                "SOL_REVIEW_REQUIRED_SHARED_METADATA_SHAPE_DRIFT: "
                f"{arxiv_id} changed fields={changed_fields}"
            )
        if (
            prior_metadata[arxiv_id]["categories"] != review["prior_categories"]
            or metadata[arxiv_id]["categories"] != review["predraft_categories"]
        ):
            raise PredraftGateReviewRequired(
                f"SOL_REVIEW_REQUIRED_SHARED_METADATA_CATEGORY_DRIFT: {arxiv_id}"
            )
        if prior_screening[arxiv_id]["rule_matches"] or screening[arxiv_id]["rule_matches"]:
            raise PredraftGateReviewRequired(
                "SOL_REVIEW_REQUIRED_SHARED_METADATA_CANDIDATE_DRIFT: "
                f"{arxiv_id} gained or had a rule trigger"
            )
        shared_metadata_review.append(
            {
                "arxiv_id": arxiv_id,
                "changed_fields": changed_fields,
                "prior_categories": review["prior_categories"],
                "predraft_categories": review["predraft_categories"],
                "decision": "SOL_TITLE_ABSTRACT_REVIEW_NONMATERIAL_TO_C1_C5",
                "rationale": review["rationale"],
            }
        )

    prior_versions = _base_version_map(prior_records)
    current_versions = _base_version_map(records)
    version_pairs = [
        {
            "base_id": base_id,
            "prior_versioned_ids": prior_versions.get(base_id, []),
            "predraft_versioned_ids": current_versions.get(base_id, []),
        }
        for base_id in sorted(set(prior_versions) | set(current_versions))
        if prior_versions.get(base_id, []) != current_versions.get(base_id, [])
    ]
    replacements = [
        pair
        for pair in version_pairs
        if pair["prior_versioned_ids"] and pair["predraft_versioned_ids"]
    ]
    replacement_by_base = {pair["base_id"]: pair for pair in replacements}
    if set(replacement_by_base) != set(PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES):
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_VERSIONED_ID_DRIFT: reviewed v1-to-v2 base-ID set changed"
        )
    for base_id, rationale in PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES.items():
        pair = replacement_by_base[base_id]
        for arxiv_id in pair["prior_versioned_ids"]:
            if prior_screening[arxiv_id]["rule_matches"]:
                raise PredraftGateReviewRequired(
                    "SOL_REVIEW_REQUIRED_VERSIONED_CANDIDATE_UPDATE: prior replacement was a "
                    f"screening candidate: {arxiv_id}"
                )
        for arxiv_id in pair["predraft_versioned_ids"]:
            if screening[arxiv_id]["rule_matches"]:
                raise PredraftGateReviewRequired(
                    "SOL_REVIEW_REQUIRED_VERSIONED_CANDIDATE_UPDATE: predraft replacement is "
                    f"a screening candidate: {arxiv_id}"
                )
        if not rationale:
            raise AssertionError(f"missing Sol version-update rationale: {base_id}")

    prior_candidates = sorted(
        arxiv_id for arxiv_id, value in prior_screening.items() if value["rule_matches"]
    )
    candidates = sorted(arxiv_id for arxiv_id, value in screening.items() if value["rule_matches"])
    added_candidates = sorted(set(candidates) - set(prior_candidates))
    if set(added_candidates) != set(PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES):
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_CANDIDATE_SET_DRIFT: new rule-triggered IDs differ from "
            "the Sol-reviewed set"
        )
    for arxiv_id, rationale in PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES.items():
        current_screening = screening[arxiv_id]
        if (
            current_screening["decision"]
            != "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5"
            or current_screening["decision_basis"] != rationale
        ):
            raise AssertionError(f"Sol-reviewed candidate decision drifted: {arxiv_id}")

    new_no_target_ids = sorted(
        arxiv_id for arxiv_id in added_ids if not screening[arxiv_id]["rule_matches"]
    )
    if len(new_no_target_ids) + len(added_candidates) != len(added_ids):
        raise AssertionError("new response IDs are not exhaustively screened")
    reviewed_contract = {
        "added_count": len(added_ids),
        "added_ids_sha256": _compact_digest(added_ids),
        "missing_count": len(missing_ids),
        "missing_ids_sha256": _compact_digest(missing_ids),
        "version_pair_count": len(version_pairs),
        "version_pairs_sha256": _compact_digest(version_pairs),
        "replacement_base_ids": sorted(replacement_by_base),
        "new_no_target_count": len(new_no_target_ids),
        "new_rule_triggered_ids": added_candidates,
        "new_rule_triggered_ids_sha256": _compact_digest(added_candidates),
        "prior_candidate_count": len(prior_candidates),
        "predraft_candidate_count": len(candidates),
        "shared_metadata_changed_ids": metadata_changed_ids,
        "shared_screening_changed_ids": screening_changed_ids,
        "shared_metadata_review_ids_sha256": _compact_digest(metadata_changed_ids),
    }
    if reviewed_contract != EXPECTED_REVIEWED_DELTA:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_REVIEWED_DELTA_DRIFT: archived changes differ from the "
            "explicitly reviewed predraft contract"
        )
    decisions = {
        "sol_title_abstract_review_required": False,
        "sol_title_abstract_review_completed": True,
        "full_text_or_pdf_required": False,
        "manuscript_change_required": False,
        "new_rule_triggered_nonmaterial": [
            {
                "arxiv_id": arxiv_id,
                "rule_matches": screening[arxiv_id]["rule_matches"],
                "decision": screening[arxiv_id]["decision"],
                "rationale": PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES[arxiv_id],
            }
            for arxiv_id in sorted(PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES)
        ],
        "version_replacement_nonmaterial": [
            {
                **replacement_by_base[base_id],
                "decision": "SOL_TITLE_ABSTRACT_REVIEW_NONMATERIAL_TO_C1_C5",
                "rationale": PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES[base_id],
            }
            for base_id in sorted(PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES)
        ],
        "shared_versioned_metadata_nonmaterial": shared_metadata_review,
    }
    comparison = {
        **scope,
        "id_set_equal": not added_ids and not missing_ids,
        "added_ids": added_ids,
        "missing_ids": missing_ids,
        "metadata_changed_ids": metadata_changed_ids,
        "screening_changed_ids": screening_changed_ids,
        "version_pair_diagnostics": version_pairs,
        "reviewed_delta_contract": reviewed_contract,
        "material_delta_ids": [],
        "response_order_not_a_materiality_contract": True,
        "metadata_by_id_sha256": _compact_digest(metadata),
        "screening_by_id_sha256": _compact_digest(screening),
    }
    return comparison, decisions


def build_ledger() -> dict[str, Any]:
    _configure_prior_gate_endpoints()
    receipt = PRIOR_GATE._retrieval_receipt()
    feed_updated = PRIOR_GATE._response_feed_updated(RAW_RESPONSE, label="predraft full-overlap")
    _configure_screening_normalizer(feed_updated)
    try:
        ledger = PRIOR_GATE.SCREENING_NORMALIZER.build_ledger()
    except ValueError as exc:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_UNCLASSIFIED_DELTA: reusable screening normalizer failed closed"
        ) from exc
    if ledger["gate_status"] != _gate_status(feed_updated):
        raise ValueError("predraft status is not derived from the archived feed cutoff")

    prior = _load_json(PRIOR_GATE_LEDGER)
    comparison, reviewed_delta = _reviewed_delta_decisions(prior, ledger)
    metadata_changed_ids = comparison["metadata_changed_ids"]
    reviewed_metadata_changed_ids = [
        record["arxiv_id"]
        for record in reviewed_delta["shared_versioned_metadata_nonmaterial"]
    ]
    metadata_equal_by_id = not metadata_changed_ids
    metadata_changes_reviewed = (
        reviewed_metadata_changed_ids == metadata_changed_ids
        and all(
            record["decision"] == "SOL_TITLE_ABSTRACT_REVIEW_NONMATERIAL_TO_C1_C5"
            for record in reviewed_delta["shared_versioned_metadata_nonmaterial"]
        )
    )
    if metadata_equal_by_id and reviewed_metadata_changed_ids:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_RECONCILIATION_DRIFT: reviewed metadata exists despite "
            "metadata equality"
        )
    if not metadata_equal_by_id and not metadata_changes_reviewed:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_RECONCILIATION_DRIFT: metadata changes lack an exact "
            "Sol-reviewed reconciliation"
        )
    try:
        exact_ids = PRIOR_GATE._exact_id_snapshot()
    except PRIOR_GATE.ZenodoGateReviewRequired as exc:
        raise PredraftGateReviewRequired(str(exc)) from exc
    except ValueError as exc:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_EXACT_ID_UPDATE: tracked version or metadata changed"
        ) from exc
    exact_versions = {record["base_id"]: record["version"] for record in exact_ids["records"]}
    if exact_versions != PRIOR_GATE.EXPECTED_EXACT_VERSIONS:
        raise PredraftGateReviewRequired("SOL_REVIEW_REQUIRED_EXACT_ID_VERSION_UPDATE")
    candidate_ids = sorted(ledger["screening"]["inspected_candidate_ids"])

    ledger["schema_version"] = "1.4"
    ledger["coverage_boundary"] = {
        "archived_submitted_date_snapshot_only": True,
        "general_pre_window_version_updates_covered": False,
        "tracked_exact_id_version_checks_archived_with_gate": [
            "arXiv:2607.26672",
            "arXiv:2603.25503",
        ],
        "minimum_predraft_contract": [
            "archive and rescreen the bounded full-overlap submittedDate response",
            "preserve the prior interval and a monotone feed cutoff",
            "repeat the two tracked exact-ID version checks",
            "compare IDs, normalized metadata, and screening decisions by versioned arXiv ID",
        ],
        "minimum_predraft_contract_status": "SATISFIED_BY_THIS_ARCHIVE_AFTER_SOL_ZERO_DELTA_REVIEW",
    }
    ledger["reconciliation"] = {
        "status": "PREDRAFT_REVIEWED_ZERO_DELTA_RECHECK_COMPLETED",
        "prior_source_id": PRIOR_SOURCE_ID,
        "id_set_equal": comparison["id_set_equal"],
        "metadata_equal_by_id": metadata_equal_by_id,
        "metadata_changes_reviewed": metadata_changes_reviewed,
        "reviewed_metadata_changed_ids": reviewed_metadata_changed_ids,
        "screening_decisions_equal_by_shared_versioned_id": True,
        "materiality_reassessment_status": "COMPLETED_REVIEWED_NO_MATERIAL_DELTA",
    }
    ledger["predraft_gate_recheck"] = {
        "authorization_boundary": dict(AUTHORIZATION_BOUNDARY),
        "gate_trigger_utc": GATE_TRIGGER_UTC,
        "prior_gate": {
            "source_id": PRIOR_SOURCE_ID,
            "normalized_ledger_path": PRIOR_GATE_LEDGER.as_posix(),
            "raw_response_path": prior["raw_response"]["path"],
            "raw_response_sha256": prior["raw_response"]["sha256"],
            "feed_updated_utc": prior["raw_response"]["feed_updated_utc"],
            "response_entry_count": prior["response_entry_count"],
        },
        "retrieval_receipt": {
            "path": RETRIEVAL_RECEIPT.as_posix(),
            "sha256": _sha256_bytes((ROOT / RETRIEVAL_RECEIPT).read_bytes()),
            "bytes": (ROOT / RETRIEVAL_RECEIPT).stat().st_size,
            "retrievals": receipt["retrievals"],
        },
        "full_overlap_comparison": comparison,
        "reviewed_versioned_id_delta": reviewed_delta,
        "title_abstract_rescreen": {
            "records_screened": len(ledger["records"]),
            "rule_triggered_candidates": len(candidate_ids),
            "candidate_ids": candidate_ids,
            "candidate_ids_sha256": _candidate_ids_sha256(ledger),
            "candidate_metadata_changed_ids": comparison["metadata_changed_ids"],
            "candidate_decision_changed_ids": comparison["screening_changed_ids"],
            "material_delta_ids": ledger["screening"]["material_delta_ids"],
            "status": "COMPLETED_REVIEWED_NO_MATERIAL_DELTA",
        },
        "exact_id_checks": {
            **exact_ids,
            "versions": exact_versions,
            "status": "BOTH_TRACKED_RECORDS_REMAIN_V1",
        },
        "claim_boundary": (
            "This gate proves only that its independently archived predraft full-overlap "
            "submittedDate response preserves the prior query scope and cutoff ordering; the "
            "versioned-ID set, normalized metadata, screening decisions, and candidate set "
            "are unchanged from the prior predraft archive; no new title/abstract review was "
            "required; and the two separately queried tracked IDs remain at v1. It does not "
            "establish exhaustive literature coverage, novelty, priority, absence, or general "
            "pre-window update coverage. "
            + OWNER_ONLY_AUTHORIZATION_FRAGMENT
        ),
    }
    return ledger


def _exact_summary(exact_checks: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_response": exact_checks["raw_response"],
        "effective_response_query": exact_checks["effective_response_query"],
        "response_entry_count": exact_checks["response_entry_count"],
        "versions": exact_checks["versions"],
        "status": exact_checks["status"],
    }


def _rescreen_summary(rescreen: dict[str, Any]) -> dict[str, Any]:
    return {
        "records_screened": rescreen["records_screened"],
        "rule_triggered_candidates": rescreen["rule_triggered_candidates"],
        "candidate_ids_sha256": rescreen["candidate_ids_sha256"],
        "candidate_metadata_changed_ids": rescreen["candidate_metadata_changed_ids"],
        "candidate_decision_changed_ids": rescreen["candidate_decision_changed_ids"],
        "material_delta_ids": rescreen["material_delta_ids"],
        "status": rescreen["status"],
    }


def _dataset_snapshot(ledger: dict[str, Any]) -> dict[str, Any]:
    """Return the source-catalog projection, not a duplicate of the full ledger.

    The normalized ledger is the immutable, complete record of the zero-delta
    comparison.  Repeating its ID lists and version-pair diagnostics
    in ``sources.json`` would obscure the reviewed delta and make the catalog
    unnecessarily hard to audit.  This projection retains the fixed review
    contract and outcome, while directing complete per-record Sol rationales
    and detailed comparison evidence to the normalized ledger artifact.
    """

    recheck = ledger["predraft_gate_recheck"]
    comparison = recheck["full_overlap_comparison"]
    reviewed = recheck["reviewed_versioned_id_delta"]
    reviewed_contract = comparison["reviewed_delta_contract"]
    return {
        "gate_status": ledger["gate_status"],
        "gate_trigger_utc": recheck["gate_trigger_utc"],
        "full_overlap_feed_updated_utc": ledger["raw_response"]["feed_updated_utc"],
        "query_scope": {
            "authority": ledger["effective_response_query"]["authority"],
            "field": ledger["effective_response_query"]["field"],
            "window_start_compact_utc": ledger["effective_response_query"][
                "window_start_compact_utc"
            ],
            "window_end_compact_utc": ledger["effective_response_query"][
                "window_end_compact_utc"
            ],
            "categories": ledger["effective_response_query"]["categories"],
            "start": ledger["effective_response_query"]["start"],
            "max_results": ledger["effective_response_query"]["max_results"],
        },
        "normalizer": NORMALIZER_PATH,
        "fetch_command": FETCH_COMMAND,
        "check_command": CHECK_COMMAND,
        "response_entry_count": ledger["response_entry_count"],
        "entries_published_in_submitted_date_window": ledger[
            "entries_published_in_submitted_date_window"
        ],
        "entries_published_outside_submitted_date_window": ledger[
            "entries_published_outside_submitted_date_window"
        ],
        "entries_published_at_or_before_feed_cutoff": ledger[
            "entries_published_at_or_before_feed_cutoff"
        ],
        "entries_published_after_feed_cutoff": ledger["entries_published_after_feed_cutoff"],
        "minimum_published_utc": ledger["minimum_published_utc"],
        "maximum_published_utc": ledger["maximum_published_utc"],
        "ordered_arxiv_ids_sha256": f"sha256:{ledger['ordered_arxiv_ids_sha256']}",
        "records_sha256": f"sha256:{ledger['records_sha256']}",
        "screening_decision_counts": ledger["screening"]["decision_counts"],
        "authorization_boundary": recheck["authorization_boundary"],
        "retrieval_receipt": {
            key: recheck["retrieval_receipt"][key] for key in ("path", "sha256", "bytes")
        },
        "full_overlap_comparison": {
            "query_semantics_equal": comparison["query_semantics_equal"],
            "feed_cutoff_monotone": comparison["feed_cutoff_monotone"],
            "prior_feed_updated_utc": comparison["prior_feed_updated_utc"],
            "predraft_feed_updated_utc": comparison["predraft_feed_updated_utc"],
            "prior_response_entry_count": comparison["prior_response_entry_count"],
            "predraft_response_entry_count": comparison[
                "predraft_response_entry_count"
            ],
            "added_count": reviewed_contract["added_count"],
            "added_ids_sha256": reviewed_contract["added_ids_sha256"],
            "missing_count": reviewed_contract["missing_count"],
            "missing_ids_sha256": reviewed_contract["missing_ids_sha256"],
            "version_pair_count": reviewed_contract["version_pair_count"],
            "version_pairs_sha256": reviewed_contract["version_pairs_sha256"],
            "metadata_changed_ids": comparison["metadata_changed_ids"],
            "screening_changed_ids": comparison["screening_changed_ids"],
            "material_delta_ids": comparison["material_delta_ids"],
            "metadata_by_id_sha256": comparison["metadata_by_id_sha256"],
            "screening_by_id_sha256": comparison["screening_by_id_sha256"],
        },
        "metadata_reconciliation": {
            "metadata_equal_by_id": ledger["reconciliation"]["metadata_equal_by_id"],
            "metadata_changes_reviewed": ledger["reconciliation"][
                "metadata_changes_reviewed"
            ],
            "reviewed_metadata_changed_ids": ledger["reconciliation"][
                "reviewed_metadata_changed_ids"
            ],
        },
        "reviewed_versioned_id_delta": {
            "status": "COMPLETED_REVIEWED_NO_MATERIAL_DELTA",
            "sol_title_abstract_review_required": reviewed[
                "sol_title_abstract_review_required"
            ],
            "sol_title_abstract_review_completed": reviewed[
                "sol_title_abstract_review_completed"
            ],
            "full_text_or_pdf_required": reviewed["full_text_or_pdf_required"],
            "manuscript_change_required": reviewed["manuscript_change_required"],
            "reviewed_delta_contract": reviewed_contract,
            "complete_per_record_rationales": {
                "path": OUTPUT_LEDGER.as_posix(),
                "field": "predraft_gate_recheck.reviewed_versioned_id_delta",
            },
        },
        "title_abstract_rescreen": _rescreen_summary(recheck["title_abstract_rescreen"]),
        "exact_id_checks": {
            "raw_response": recheck["exact_id_checks"]["raw_response"],
            "response_entry_count": recheck["exact_id_checks"]["response_entry_count"],
            "versions": recheck["exact_id_checks"]["versions"],
            "status": recheck["exact_id_checks"]["status"],
        },
    }


def source_record(ledger: dict[str, Any], ledger_bytes: bytes) -> dict[str, Any]:
    recheck = ledger["predraft_gate_recheck"]
    receipt_bytes = (ROOT / RETRIEVAL_RECEIPT).read_bytes()
    exact_raw = recheck["exact_id_checks"]["raw_response"]
    return {
        "id": SOURCE_ID,
        "title": "Official arXiv API responses: Paper I Zenodo predraft literature gate",
        "authors": ["arXiv"],
        "url": ledger["effective_response_query"]["self_link"],
        "exact_id_url": EXACT_ID_REQUEST_URL,
        "retrieved_on": "2026-08-07",
        "local_file": None,
        "local_artifacts": [
            {
                "role": "FULL_OVERLAP_RAW_API_RESPONSE",
                "path": RAW_RESPONSE.relative_to("references").as_posix(),
                "media_type": "application/atom+xml",
                "sha256": f"sha256:{ledger['raw_response']['sha256']}",
                "bytes": ledger["raw_response"]["bytes"],
            },
            {
                "role": "EXACT_ID_RAW_API_RESPONSE",
                "path": EXACT_ID_RESPONSE.relative_to("references").as_posix(),
                "media_type": "application/atom+xml",
                "sha256": f"sha256:{exact_raw['sha256']}",
                "bytes": exact_raw["bytes"],
            },
            {
                "role": "RETRIEVAL_PROVENANCE",
                "path": RETRIEVAL_RECEIPT.relative_to("references").as_posix(),
                "media_type": "application/json",
                "sha256": f"sha256:{_sha256_bytes(receipt_bytes)}",
                "bytes": len(receipt_bytes),
            },
            {
                "role": "NORMALIZED_SCREENING_LEDGER",
                "path": OUTPUT_LEDGER.relative_to("references").as_posix(),
                "media_type": "application/json",
                "sha256": f"sha256:{_sha256_bytes(ledger_bytes)}",
                "bytes": len(ledger_bytes),
            },
        ],
        "dataset_snapshot": _dataset_snapshot(ledger),
        "version": (
            "official arXiv API Atom responses archived for the 2026-08-06T2315Z Zenodo "
            "predraft gate; full-overlap feed timestamp "
            f"{ledger['raw_response']['feed_updated_utc']}; "
            f"exact-ID feed timestamp {exact_raw['feed_updated_utc']}"
        ),
        "relationship": "SEARCH_DATASET",
        "used_for": [
            "Paper I Zenodo draft-creation preflight full-overlap submittedDate gate for C1--C5",
            "ID-keyed comparison with the independent 2026-08-06T1123Z predraft gate",
            "exact-ID version and updated-metadata checks for arXiv:2607.26672 and "
            "arXiv:2603.25503",
        ],
        "claim_boundary": (
            "This artifact-specific predraft gate establishes only that the independently "
            "archived submittedDate response preserves the prior scope and monotone cutoff; "
            "the prior Sol-reviewed candidate set remains unchanged, and the current delta "
            "has no new candidate, metadata, screening, or version pair, so no new Sol "
            "title/abstract review was required; and the separately queried Xu and "
            "Srivastava--Surya records remain at v1. It does not establish exhaustive "
            "literature coverage, novelty, priority, absence, or general coverage of updates "
            "to records submitted before the window. A future gate requires a new date-"
            "stamped archive and normalizer. "
            + OWNER_ONLY_AUTHORIZATION_FRAGMENT
        ),
    }


def _record_by_id(path: Path, collection_key: str) -> dict[str, Any]:
    document = _load_json(path)
    matches = [record for record in document[collection_key] if record.get("id") == SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {SOURCE_ID} record in {path}")
    return matches[0]


def _validate_reference_bindings(ledger: dict[str, Any], ledger_bytes: bytes) -> None:
    expected = source_record(ledger, ledger_bytes)
    source = _record_by_id(SOURCES, "sources")
    archived = _record_by_id(ARCHIVE_MANIFEST, "records")
    for label, record in (("source catalog", source), ("archive manifest", archived)):
        for field, value in expected.items():
            if record.get(field) != value:
                raise ValueError(f"{label} {field} binding drifted")
    if not (
        archived.get("archive_status") == "LOCAL_ARTIFACTS"
        and archived.get("sha256") is None
        and archived.get("bytes") is None
        and archived.get("pages") is None
        and archived.get("text_file") is None
    ):
        raise ValueError("archive manifest non-PDF dataset archive status drifted")


def _print_source_record() -> None:
    ledger = build_ledger()
    output = ROOT / OUTPUT_LEDGER
    ledger_bytes = output.read_bytes() if output.exists() else _canonical_bytes(ledger)
    print(json.dumps(source_record(ledger, ledger_bytes), ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="archive new official API responses")
    parser.add_argument("--write", action="store_true", help="write the normalized predraft ledger")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify predraft artifacts, ledger, and source/manifest bindings",
    )
    parser.add_argument(
        "--print-source-record",
        action="store_true",
        help="print the exact source-catalog record to add with apply_patch",
    )
    args = parser.parse_args()
    if not any((args.fetch, args.write, args.check, args.print_source_record)):
        parser.error("choose --fetch, --write, --check, or --print-source-record")
    if args.fetch:
        fetch()
    if args.write:
        ledger = build_ledger()
        output = ROOT / OUTPUT_LEDGER
        if output.exists():
            raise FileExistsError(
                f"refusing to overwrite normalized predraft ledger: {OUTPUT_LEDGER}"
            )
        output.write_bytes(_canonical_bytes(ledger))
        print(f"Wrote normalized Paper I Zenodo predraft ledger: {OUTPUT_LEDGER}")
    if args.print_source_record:
        _print_source_record()
    if args.check:
        ledger = build_ledger()
        expected = _canonical_bytes(ledger)
        output = ROOT / OUTPUT_LEDGER
        if not output.exists():
            print(f"missing predraft ledger: {output}", file=sys.stderr)
            return 1
        if output.read_bytes() != expected:
            print(f"predraft ledger drift: {output}", file=sys.stderr)
            return 1
        _validate_reference_bindings(ledger, expected)
        print(f"OK: normalized Paper I Zenodo predraft ledger ({OUTPUT_LEDGER})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
