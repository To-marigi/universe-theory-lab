"""Validate the machine-readable Paper I claim boundary ledger.

The validator is deliberately read-only.  It checks that every pinned result
artifact still exists and has the raw/semantic digest recorded by the ledger,
and that the ledger retains the fail-closed publication boundary.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

LEDGER_PATH = Path("results/v0.4.2_paper1_claim_boundary.json")
FORBIDDEN_ACTIVE_VERDICTS = {
    "WEAK_D2_ON_ONE_SIDED_COMMUTATIVITY_PROVED",
    "AT_LEAST_ONE_STRONG_SIDE_IFF_COMMUTATIVE",
}
REQUIRED_NONCLAIM_IDS = {
    "N1_FULL_955",
    "N2_PROFILE_721",
    "N3_COMPLETE_ON_CLASSIFICATION",
    "N4_REACHABLE_VISIBLE_WITNESS",
    "N5_U2_FULL_IDEAL",
    "N6_EXTENSIONS",
}
EDITORIAL_DISPOSITION = "PAPER_I_SCOPED_U2_RESOURCE_OPEN_LIMITATION_ACCEPTED"
EDITORIAL_DISPOSITION_AUTHORITY = "reports/v0.4.2_paper1_editorial_disposition_2026-08-06.md"
CLAIM_LEDGER_STATUS = "PAPER_I_SCOPED_ARCHIVE_SUBMISSION_CANDIDATE_NOT_FROZEN"
PDF_SOURCE_REBIND_STATUS = "CURRENT_SOURCE_FINAL_BUILD_AND_ALL_PAGE_VISUAL_QA_VERIFIED"
C2_CLAIM_ID = "C2_SR2_WEAK_WEAK_SEPARATION"
C2_OBSERVABILITY_PATH = "results/v0.4.2_sr2v_baseline_observability.json"
C2_OBSERVABILITY_RAW_SHA256 = "4f57805e871c0589560669c5aa65181c29ca41cdf722420729279945770710de"
C2_OBSERVABILITY_SEMANTIC_DIGEST = (
    "73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62"
)
C2_COMMUTATOR_PAIRS = {(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_c2_observability_binding(
    root: Path, claims: list[dict[str, Any]], errors: list[str]
) -> None:
    c2_claim = next((claim for claim in claims if claim.get("id") == C2_CLAIM_ID), None)
    _require(c2_claim is not None, "C2 claim is missing", errors)
    if c2_claim is None:
        return

    evidence = c2_claim.get("evidence")
    matching_evidence = (
        [
            item
            for item in evidence
            if isinstance(item, dict) and item.get("path") == C2_OBSERVABILITY_PATH
        ]
        if isinstance(evidence, list)
        else []
    )
    _require(
        len(matching_evidence) == 1,
        "C2 observability artifact must appear exactly once in its evidence",
        errors,
    )
    if len(matching_evidence) != 1:
        return
    binding = matching_evidence[0]
    _require(
        binding.get("raw_sha256") == C2_OBSERVABILITY_RAW_SHA256,
        "C2 observability raw SHA-256 binding changed",
        errors,
    )
    _require(
        binding.get("semantic_digest") == C2_OBSERVABILITY_SEMANTIC_DIGEST,
        "C2 observability semantic digest binding changed",
        errors,
    )

    artifact_path = root / C2_OBSERVABILITY_PATH
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read C2 observability artifact: {exc}")
        return
    if not isinstance(artifact, dict):
        errors.append("C2 observability artifact must be a JSON object")
        return

    _require(
        artifact.get("semantic_digest_sha256") == C2_OBSERVABILITY_SEMANTIC_DIGEST,
        "C2 observability artifact semantic digest changed",
        errors,
    )
    summary = artifact.get("reachable_inventory", {}).get("summary", {})
    baseline = artifact.get("baseline_classification", {})
    _require(
        isinstance(summary, dict) and summary.get("reachable_span_rank") == 1,
        "C2 observability reachable span rank is not one",
        errors,
    )
    _require(
        isinstance(baseline, dict)
        and baseline.get("reachable_span_rank") == 1
        and baseline.get("reachable_visible") is False,
        "C2 observability is no longer rank-one and off-reachable",
        errors,
    )

    visibility = artifact.get("commutator_visibility", {})
    _require(isinstance(visibility, dict), "C2 commutator visibility must be an object", errors)
    if not isinstance(visibility, dict):
        return
    _require(
        visibility.get("reachable_visible_on_any_compiled_cylinder_state") is False,
        "C2 commutator is unexpectedly reachable-visible",
        errors,
    )
    _require(
        visibility.get("all_six_annihilate_full_reachable_span") is True,
        "C2 commutators no longer all annihilate the reachable span",
        errors,
    )
    records = visibility.get("records")
    _require(
        isinstance(records, list) and len(records) == 6,
        "C2 must bind six commutators",
        errors,
    )
    if not isinstance(records, list):
        return

    observed_pairs: set[tuple[int, int]] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("C2 commutator record is not an object")
            continue
        pair = record.get("pair")
        if (
            isinstance(pair, list)
            and len(pair) == 2
            and all(isinstance(value, int) for value in pair)
        ):
            observed_pairs.add((pair[0], pair[1]))
        else:
            errors.append("C2 commutator record has an invalid pair")
        _require(
            record.get("operator_nonzero") is True,
            "C2 commutator record is no longer operator-nonzero",
            errors,
        )
        _require(
            record.get("annihilates_full_reachable_span") is True,
            "C2 commutator record no longer annihilates the reachable span",
            errors,
        )
        domains = record.get("domains")
        if not isinstance(domains, dict) or not domains:
            errors.append("C2 commutator record has no visibility domains")
            continue
        for domain_name, domain in domains.items():
            _require(
                isinstance(domain, dict) and domain.get("nonzero_action_count") == 0,
                f"C2 commutator action is nonzero in domain {domain_name!r}",
                errors,
            )
    _require(observed_pairs == C2_COMMUTATOR_PAIRS, "C2 commutator pair set changed", errors)
    gates = artifact.get("gates", {})
    _require(
        isinstance(gates, dict)
        and gates.get("reachable_span_rank_is_exactly_one") is True
        and gates.get("no_Q_commutator_is_detected_on_any_compiled_cylinder_state") is True,
        "C2 observability gates are incomplete",
        errors,
    )


def validate_claim_boundary(root: Path) -> list[str]:
    """Return validation errors; an empty list means the ledger is sound."""

    ledger_file = root / LEDGER_PATH
    errors: list[str] = []
    _require(ledger_file.is_file(), f"missing ledger: {LEDGER_PATH}", errors)
    if errors:
        return errors

    try:
        data: dict[str, Any] = json.loads(ledger_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read ledger: {exc}"]

    _require(
        data.get("schema_version") == "final-theory-v042-paper1-claim-boundary-v1",
        "unexpected ledger schema_version",
        errors,
    )
    _require(
        data.get("status") == CLAIM_LEDGER_STATUS,
        "ledger is not scoped-ready",
        errors,
    )
    claims = data.get("claims")
    _require(isinstance(claims, list) and len(claims) == 5, "expected five active claims", errors)
    nonclaims = data.get("nonclaims")
    nonclaim_ids = (
        {item.get("id") for item in nonclaims if isinstance(item, dict)}
        if isinstance(nonclaims, list)
        else set()
    )
    _require(
        REQUIRED_NONCLAIM_IDS <= nonclaim_ids, "required nonclaim boundary is incomplete", errors
    )

    serialized = ledger_file.read_text(encoding="utf-8")
    for verdict in FORBIDDEN_ACTIVE_VERDICTS:
        _require(
            verdict not in serialized,
            f"superseded verdict appears in active ledger: {verdict}",
            errors,
        )

    for claim in claims if isinstance(claims, list) else []:
        _require(isinstance(claim, dict), "claim entry is not an object", errors)
        if not isinstance(claim, dict):
            continue
        _require(bool(claim.get("id")), "claim has no id", errors)
        evidence = claim.get("evidence")
        _require(
            isinstance(evidence, list) and bool(evidence),
            f"claim {claim.get('id')} has no evidence",
            errors,
        )
        for item in evidence if isinstance(evidence, list) else []:
            if not isinstance(item, dict):
                errors.append(f"claim {claim.get('id')} has malformed evidence")
                continue
            relative = item.get("path")
            _require(
                isinstance(relative, str) and bool(relative),
                f"claim {claim.get('id')} has invalid evidence path",
                errors,
            )
            if not isinstance(relative, str) or not relative:
                continue
            path = root / relative
            _require(path.is_file(), f"missing evidence for {claim.get('id')}: {relative}", errors)
            if not path.is_file():
                continue
            expected_raw = item.get("raw_sha256")
            if expected_raw:
                _require(
                    _sha256(path) == expected_raw,
                    f"raw SHA-256 mismatch for {relative}",
                    errors,
                )
            expected_semantic = item.get("semantic_digest")
            if expected_semantic:
                try:
                    artifact = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f"cannot read semantic artifact {relative}: {exc}")
                else:
                    _require(
                        artifact.get("semantic_digest_sha256") == expected_semantic,
                        f"semantic digest mismatch for {relative}",
                        errors,
                    )

    typed_claims = (
        [claim for claim in claims if isinstance(claim, dict)] if isinstance(claims, list) else []
    )
    _validate_c2_observability_binding(root, typed_claims, errors)

    resource_boundary = data.get("resource_boundary", {})
    _require(
        resource_boundary.get("status") == "SOFT_RESOURCE_LIMIT_NONTERMINAL",
        "U2 resource boundary is not fail-closed",
        errors,
    )
    _require(
        resource_boundary.get("full_unit_theorem_claimed") is False,
        "U2 full-unit theorem must remain unclaimed",
        errors,
    )
    _require(
        resource_boundary.get("scientific_global_sr2v_status") == "SEARCH_OPEN_NO_TERMINAL"
        and resource_boundary.get("u2_is_global_terminal") is False,
        "resource boundary scientific two-layer status changed",
        errors,
    )
    _require(
        resource_boundary.get("paper_I_editorial_disposition") == EDITORIAL_DISPOSITION
        and resource_boundary.get("editorial_disposition_authority")
        == EDITORIAL_DISPOSITION_AUTHORITY,
        "resource boundary editorial disposition binding changed",
        errors,
    )
    _require(
        resource_boundary.get("manuscript_freeze_requires_SR2_V_terminal") is False
        and resource_boundary.get(
            "manuscript_freeze_requires_SR2_V_outcome_or_scoped_open_limitation"
        )
        is True,
        "resource boundary manuscript freeze gate changed",
        errors,
    )
    publication = data.get("publication_gates", {})
    _require(
        publication.get("zenodo_or_doi") == "OWNER_ONLY_NOT_AUTHORIZED",
        "external publication action is not owner-gated",
        errors,
    )
    _require(
        publication.get("paper_I_editorial_disposition") == EDITORIAL_DISPOSITION
        and publication.get("editorial_disposition_authority")
        == EDITORIAL_DISPOSITION_AUTHORITY,
        "publication editorial disposition binding changed",
        errors,
    )
    _require(
        publication.get("manuscript_freeze_requires_SR2_V_terminal") is False
        and publication.get(
            "manuscript_freeze_requires_SR2_V_outcome_or_scoped_open_limitation"
        )
        is True,
        "publication manuscript freeze gate changed",
        errors,
    )
    pdf_source_rebind = publication.get("pdf_source_rebind")
    _require(
        isinstance(pdf_source_rebind, dict)
        and pdf_source_rebind.get("status") == PDF_SOURCE_REBIND_STATUS
        and pdf_source_rebind.get("required_before_submission_or_deposit") is True
        and pdf_source_rebind.get("completed") is True
        and pdf_source_rebind.get("publication_authorized") is False,
        "publication PDF/source rebind gate changed",
        errors,
    )
    lanes = data.get("version_lanes", {})
    _require(
        isinstance(lanes, dict)
        and lanes.get("sr2v_global_status") == "SEARCH_OPEN_NO_TERMINAL"
        and lanes.get("scientific_global_sr2v_status") == "SEARCH_OPEN_NO_TERMINAL"
        and lanes.get("u2_status") == "SOFT_RESOURCE_LIMIT_NONTERMINAL"
        and lanes.get("u2_subroute_is_not_sr2v_terminal") is True
        and lanes.get("u2_is_global_terminal") is False,
        "version-lane scientific two-layer status changed",
        errors,
    )
    _require(
        isinstance(lanes, dict)
        and lanes.get("paper_I_editorial_disposition") == EDITORIAL_DISPOSITION
        and lanes.get("editorial_disposition_authority") == EDITORIAL_DISPOSITION_AUTHORITY,
        "version-lane editorial disposition binding changed",
        errors,
    )
    _require(
        isinstance(lanes, dict)
        and lanes.get("manuscript_freeze_requires_SR2_V_terminal") is False
        and lanes.get("manuscript_freeze_requires_SR2_V_outcome_or_scoped_open_limitation")
        is True,
        "version-lane manuscript freeze gate changed",
        errors,
    )
    _require(
        data.get("validation", {}).get("full_profile_claimed") is False,
        "full profile is accidentally claimed",
        errors,
    )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_claim_boundary(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("paper1_claim_boundary=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
