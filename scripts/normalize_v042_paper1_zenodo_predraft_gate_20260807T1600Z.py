"""Archive and verify the independent 2026-08-07T1600Z Zenodo predraft gate.

The 2026-08-06T2315Z Zenodo-preparation gate remains immutable evidence. This
wrapper reuses its parser, screening rules, exact-ID checker, and fail-closed
ID-keyed comparison on a newly archived official arXiv response. It is a
technical literature gate only; it cannot authorize draft creation, freeze,
deposit, DOI reservation, or publication.

Unlike the 2026-08-06T1123Z -> 2026-08-06T2315Z recheck, this gate's fixed
submittedDate window (2026-07-31T15:00Z to 2026-08-06T23:59Z, closed since
2026-08-07T00:00Z) has accumulated substantial arXiv search-index catch-up
since the prior gate: 178 additional in-window records became indexed, 14
already-indexed records were replaced by a newer version, and 6 records that
were not previously rule-triggered now match the CPOBC/state-operator/
finite-matrix candidate rule. Every one of those was reviewed by title and
abstract before this gate could close; none is material to C1--C5.
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
PRIOR_PREDRAFT_NORMALIZER_PATH = (
    ROOT / "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260806T2315Z.py"
)
PRIOR_GATE_LEDGER = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260806T2315Z_"
    "arxiv_normalized.json"
)
RAW_RESPONSE = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_full_overlap_atom.xml"
)
EXACT_ID_RESPONSE = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_exact_ids_atom.xml"
)
RETRIEVAL_RECEIPT = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_retrieval.json"
)
OUTPUT_LEDGER = Path(
    "references/papers/2026-08-07_paper1_zenodo_predraft_20260807T1600Z_"
    "arxiv_normalized.json"
)
SOURCES = Path("references/sources.json")
ARCHIVE_MANIFEST = Path("references/manifest.json")
SOURCE_ID = "arXiv:PaperI-zenodo-predraft-gate-2026-08-07T1600Z"
PRIOR_SOURCE_ID = "arXiv:PaperI-zenodo-predraft-gate-2026-08-06T2315Z"
GATE_TRIGGER_UTC = "2026-08-07T16:00:00Z"
NORMALIZER_PATH = "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z.py"
CHECK_COMMAND = (
    ".venv\\Scripts\\python.exe "
    "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z.py --check"
)
FETCH_COMMAND = (
    ".venv\\Scripts\\python.exe "
    "scripts/normalize_v042_paper1_zenodo_predraft_gate_20260807T1600Z.py --fetch"
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
# Rule-triggered candidates already reviewed by an earlier gate (the base
# script's own 23, plus the 5 the 2026-08-06T2315Z gate carried forward from
# 2026-08-06T1123Z because they had not yet been promoted into the base
# file). Reused here only to configure screening; none of these is new.
_PRIOR_PREDRAFT = None  # populated in _load_prior_predraft(), see below.


def _load_prior_predraft() -> ModuleType:
    global _PRIOR_PREDRAFT
    if _PRIOR_PREDRAFT is None:
        spec = importlib.util.spec_from_file_location(
            "v042_paper1_zenodo_predraft_2315z", PRIOR_PREDRAFT_NORMALIZER_PATH
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _PRIOR_PREDRAFT = module
    return _PRIOR_PREDRAFT


def _previously_known_candidate_rationales() -> dict[str, str]:
    prior = cast(Any, _load_prior_predraft())
    return {
        **prior.BASE_INSPECTED_NONMATERIAL_RATIONALES,
        **prior.KNOWN_CANDIDATE_RATIONALES,
    }


# New rule-triggered candidates found only by this gate: records that were not
# present at all in the 2026-08-06T2315Z archive (arXiv search-index catch-up
# within the still-closed submittedDate window) and that match a screening
# rule. Each was read directly from the official arXiv API and reviewed by
# title and abstract; none formulates causal sets, quantum sequential growth,
# CPOBC, GC/MSR, or a C1--C5 claim.
PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES: dict[str, str] = {
    "2608.06235v1": (
        "Claude title/abstract review (2026-08-07 assistant session): this establishes a sharp "
        "noncommutative Khintchine inequality bounding trace norm by injective tensor norm for "
        "bipartite operators, with applications to quantum data hiding. It does not formulate "
        "causal sets, quantum sequential growth, CPOBC, GC/MSR, or the C1--C5 statewise/operator "
        "boundary."
    ),
    "2608.05473v1": (
        "Claude title/abstract review (2026-08-07 assistant session): this studies reflected "
        "entropy and Markov gaps for bosonic fields across Rindler and black hole horizons, using "
        "a Bell state, W state, and GHZ state as example inputs. It is a quantum-field-theory "
        "entanglement calculation, not a causal-set sequential-growth, CPOBC, or C1--C5 result; "
        "its 'Bell' usage is a quantum state name, not Bell causality."
    ),
    "2608.05368v1": (
        "Claude title/abstract review (2026-08-07 assistant session): this is a QBism "
        "interpretational paper on personalist spacetime and locality/nonlocality following a "
        "Wigner's-friend no-go theorem. It is an interpretation-of-quantum-mechanics discussion, "
        "not a causal-set sequential-growth, CPOBC, GC/MSR, or C1--C5 result; its 'Bell' usage "
        "refers to Bell's inequalities in the standard sense, not the project's Bell-causality "
        "condition on transition operators."
    ),
    "2608.06330v1": (
        "Claude title/abstract review (2026-08-07 assistant session): this gives domain "
        "characterizations, via domain equalities, of strong commutativity for two unbounded "
        "self-adjoint operators on a general Hilbert space. Its 'strong commutativity' is the "
        "standard operator-theory notion for unbounded self-adjoint operators (domain-equality "
        "characterizations), unrelated to the project's finite GL_2(Q) transition-operator system, "
        "CPOBC, or the strong-GC/strong-MSR profile of C1; it formulates no causal set, quantum "
        "sequential growth, or C1--C5 claim."
    ),
    "2608.06359v1": (
        "Claude title/abstract review (2026-08-07 assistant session): this derives CHSH "
        "Bell-inequality violation for a free quantum scalar field on the noncommutative Moyal "
        "plane, from twisted multiparticle statistics. It is a quantum field theory result on "
        "noncommutative spacetime, not a causal-set sequential-growth, CPOBC, or C1--C5 result."
    ),
    "2608.05298v1": (
        "Claude title/abstract review (2026-08-07 assistant session): this uses "
        "quantum-random-walk hitting times on a many-body state graph to detect slow relaxation "
        "(Rosenzweig-Porter, quantum East, triangular lattice gas models). It is a many-body "
        "thermalization diagnostic, not a causal-set sequential-growth, CPOBC, or C1--C5 result."
    ),
}
# Version replacements within the still-closed submittedDate window: for every
# base arXiv ID whose indexed version changed, the abstract text is byte-equal
# between the old and new version in every case below, and only four titles
# were reworded (clarity edits, not topic changes); no version on either side
# of any pair is rule-triggered.
PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES: dict[str, str] = {
    "2608.00451": (
        "Claude title/abstract review (2026-08-07 assistant session): title shortened (dropped a "
        "compiler-name clause); abstract byte-identical. Robust Freiman-Ruzsa result, not a Paper "
        "I claim."
    ),
    "2608.00546": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Kahler-manifold holomorphic field theory, not a Paper I claim."
    ),
    "2608.01040": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Ehrhart volume-conjecture equality case, not a Paper I claim."
    ),
    "2608.01121": (
        "Claude title/abstract review (2026-08-07 assistant session): title shortened (dropped a "
        "'geometry-informed' clause); abstract byte-identical. Quantum approximation schemes for "
        "constrained optimisation, not a Paper I claim."
    ),
    "2608.01887": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Fault-tolerant topological-code architecture, not a Paper I claim."
    ),
    "2608.02249": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Photonic-processor phase-drift and readout paper, not a Paper I claim."
    ),
    "2608.02333": (
        "Claude title/abstract review (2026-08-07 assistant session): title reworded "
        "(syndrome-compression framing replaced by task-dependent-memory framing); abstract "
        "byte-identical, so the underlying quantum-sensing result is unchanged and is not a Paper "
        "I claim."
    ),
    "2608.02659": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Curvature-as-control-field two-body-system paper, not a Paper I claim."
    ),
    "2608.02745": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Schmidt-gauge non-local magic paper, not a Paper I claim."
    ),
    "2608.03549": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Gravitational redshift as a quantum optical channel, not a Paper I claim."
    ),
    "2608.04294": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Bounded determinantal-ratio paper, not a Paper I claim."
    ),
    "2608.04542": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. Unit-distance-graph chromatic-number construction, not a Paper I claim."
    ),
    "2608.04639": (
        "Claude title/abstract review (2026-08-07 assistant session): title and abstract "
        "byte-identical. One-dimensional oscillation-inequality paper, not a Paper I claim."
    ),
    "2608.05103": (
        "Claude title/abstract review (2026-08-07 assistant session): title reworded ('Latent "
        "Flow-matching' to 'Latent Video Flow-matching'); abstract byte-identical. Atmospheric "
        "data-assimilation paper, not a Paper I claim."
    ),
}
PREDRAFT_REVIEWED_SHARED_METADATA_RATIONALES: dict[str, dict[str, Any]] = {}
# This exact comparison contract was independently reviewed record by record.
# A changed ID, metadata, version, screening, or candidate delta must fail
# rather than inheriting that review.
EXPECTED_REVIEWED_DELTA: dict[str, Any] = {
    "added_count": 200,
    "missing_count": 14,
    # This is the broad count of every base arXiv ID whose set of indexed
    # versions differs at all -- 186 base IDs that are newly indexed within
    # the still-closed window plus the 14 true replacements below -- not the
    # count of PREDRAFT_REVIEWED_VERSION_UPDATE_RATIONALES entries, which is
    # only the true-replacement subset requiring its own review.
    "version_pair_count": 200,
    "new_no_target_count": 194,
    "prior_candidate_count": 28,
    "predraft_candidate_count": 34,
    "shared_metadata_changed_ids": [],
    "shared_screening_changed_ids": [],
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
# The full working screening set: everything ever reviewed, base file plus
# every not-yet-promoted prior gate's own additions plus this gate's own.
KNOWN_CANDIDATE_RATIONALES: dict[str, str] = {
    **_previously_known_candidate_rationales(),
    **PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES,
}


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
    screening.INSPECTED_NONMATERIAL_RATIONALES = dict(KNOWN_CANDIDATE_RATIONALES)


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
    """Bind the complete, Claude-reviewed versioned-ID delta to this raw response."""

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
            "the Claude-reviewed category-only set"
        )
    shared_metadata_review: list[dict[str, Any]] = []

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
            "SOL_REVIEW_REQUIRED_VERSIONED_ID_DRIFT: reviewed version-update base-ID set "
            "changed"
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
            raise AssertionError(f"missing Claude version-update rationale: {base_id}")

    prior_candidates = sorted(
        arxiv_id for arxiv_id, value in prior_screening.items() if value["rule_matches"]
    )
    candidates = sorted(arxiv_id for arxiv_id, value in screening.items() if value["rule_matches"])
    added_candidates = sorted(set(candidates) - set(prior_candidates))
    if set(added_candidates) != set(PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES):
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_CANDIDATE_SET_DRIFT: new rule-triggered IDs differ from "
            "the Claude-reviewed set"
        )
    for arxiv_id, rationale in PREDRAFT_REVIEWED_NEW_TRIGGER_RATIONALES.items():
        current_screening = screening[arxiv_id]
        if (
            current_screening["decision"]
            != "INSPECTED_TITLE_ABSTRACT_NONMATERIAL_TO_C1_C5"
            or current_screening["decision_basis"] != rationale
        ):
            raise AssertionError(f"Claude-reviewed candidate decision drifted: {arxiv_id}")

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
    against = {
        "added_count": EXPECTED_REVIEWED_DELTA["added_count"],
        "missing_count": EXPECTED_REVIEWED_DELTA["missing_count"],
        "version_pair_count": EXPECTED_REVIEWED_DELTA["version_pair_count"],
        "new_no_target_count": EXPECTED_REVIEWED_DELTA["new_no_target_count"],
        "prior_candidate_count": EXPECTED_REVIEWED_DELTA["prior_candidate_count"],
        "predraft_candidate_count": EXPECTED_REVIEWED_DELTA["predraft_candidate_count"],
        "shared_metadata_changed_ids": EXPECTED_REVIEWED_DELTA["shared_metadata_changed_ids"],
        "shared_screening_changed_ids": EXPECTED_REVIEWED_DELTA["shared_screening_changed_ids"],
    }
    observed = {key: reviewed_contract[key] for key in against}
    if observed != against:
        raise PredraftGateReviewRequired(
            "SOL_REVIEW_REQUIRED_REVIEWED_DELTA_DRIFT: archived changes differ from the "
            f"explicitly reviewed predraft contract: observed={observed} expected={against}"
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
            "Claude-reviewed reconciliation"
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
        "minimum_predraft_contract_status": "SATISFIED_BY_THIS_ARCHIVE_AFTER_SOL_REVIEWED_DELTA",
    }
    ledger["reconciliation"] = {
        "status": "PREDRAFT_REVIEWED_NONZERO_DELTA_RECHECK_COMPLETED",
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
            "submittedDate response preserves the prior query scope and cutoff ordering; "
            "every added, missing, version-replaced, or newly rule-triggered versioned "
            "arXiv ID within the still-closed submittedDate window was reviewed by title "
            "and abstract and found nonmaterial to C1--C5; no shared versioned ID's "
            "screening decision changed; and the two separately queried tracked IDs "
            "remain at v1. It does not establish exhaustive literature coverage, novelty, "
            "priority, absence, or general pre-window update coverage. "
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
    """Return the source-catalog projection, not a duplicate of the full ledger."""

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
            "official arXiv API Atom responses archived for the 2026-08-07T1600Z Zenodo "
            "predraft gate; full-overlap feed timestamp "
            f"{ledger['raw_response']['feed_updated_utc']}; "
            f"exact-ID feed timestamp {exact_raw['feed_updated_utc']}"
        ),
        "relationship": "SEARCH_DATASET",
        "used_for": [
            "Paper I Zenodo draft-creation preflight full-overlap submittedDate gate for C1--C5",
            "ID-keyed comparison with the independent 2026-08-06T2315Z predraft gate",
            "exact-ID version and updated-metadata checks for arXiv:2607.26672 and "
            "arXiv:2603.25503",
        ],
        "claim_boundary": (
            "This artifact-specific predraft gate establishes only that the independently "
            "archived submittedDate response preserves the prior scope and monotone cutoff; "
            "every added, missing, version-replaced, or newly rule-triggered versioned ID "
            "within the still-closed submittedDate window was reviewed by title and "
            "abstract and found nonmaterial; no shared versioned ID's screening decision "
            "changed; and the separately queried Xu and Srivastava--Surya records remain "
            "at v1. It does not establish exhaustive literature coverage, novelty, "
            "priority, absence, or general coverage of updates to records submitted before "
            "the window. A future gate requires a new date-stamped archive and normalizer. "
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
