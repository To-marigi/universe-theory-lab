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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


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
        data.get("status") == "SCOPED_MANUSCRIPT_ASSEMBLY_READY",
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
    publication = data.get("publication_gates", {})
    _require(
        publication.get("zenodo_or_doi") == "OWNER_ONLY_NOT_AUTHORIZED",
        "external publication action is not owner-gated",
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
