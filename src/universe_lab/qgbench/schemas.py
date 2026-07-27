"""QG-Atlas と Claim Graph の軽量検証器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

THEORY_CARD_FIELDS = {
    "id",
    "name",
    "family",
    "fundamental_degrees_of_freedom",
    "state_space",
    "time_and_causality",
    "dynamics",
    "observables",
    "gauge_symmetry",
    "background_dependence",
    "continuum_limit",
    "general_relativity_recovery",
    "quantum_mechanics_recovery",
    "matter_inclusion",
    "black_hole_results",
    "cosmology_results",
    "proven",
    "numerical_evidence",
    "conjectures",
    "known_failures",
    "open_problems",
    "assumptions",
    "sources",
}

CLAIM_STATUSES = {
    "PROVEN",
    "FORMALLY_DERIVED",
    "NUMERICALLY_SUPPORTED",
    "HEURISTIC",
    "CONJECTURAL",
    "CONTRADICTED",
}


def load_json_yaml(path: Path) -> dict[str, Any]:
    """JSON 互換 YAML 1.2 ファイルを標準ライブラリだけで読む。"""

    return json.loads(path.read_text(encoding="utf-8"))


def validate_theory_card(card: dict[str, Any]) -> list[str]:
    """TheoryCard の欠落・余剰フィールドを返す。"""

    actual = set(card)
    errors = [f"missing field: {field}" for field in sorted(THEORY_CARD_FIELDS - actual)]
    errors.extend(f"unknown field: {field}" for field in sorted(actual - THEORY_CARD_FIELDS))
    if "sources" in card and not card["sources"]:
        errors.append("sources must not be empty")
    if "assumptions" in card and not card["assumptions"]:
        errors.append("assumptions must not be empty")
    return errors


def validate_claim(claim: dict[str, Any]) -> list[str]:
    """Claim Graph の一レコードを検証する。"""

    required = {
        "id",
        "claim",
        "kind",
        "status",
        "assumptions",
        "scope",
        "sources",
        "depends_on",
    }
    errors = [f"missing field: {field}" for field in sorted(required - set(claim))]
    if claim.get("status") not in CLAIM_STATUSES:
        errors.append(f"invalid status: {claim.get('status')}")
    if not claim.get("sources"):
        errors.append("sources must not be empty")
    if not claim.get("scope"):
        errors.append("scope must not be empty")
    return errors


def validate_claim_graph(paths: list[Path]) -> list[str]:
    """複数 JSONL を一つの依存グラフとして検証する。"""

    claims: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                claim = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
                continue
            errors.extend(
                f"{path}:{line_number}: {message}" for message in validate_claim(claim)
            )
            claims.append(claim)
    identifiers = [claim.get("id") for claim in claims]
    duplicates = {item for item in identifiers if identifiers.count(item) > 1}
    errors.extend(f"duplicate claim id: {identifier}" for identifier in sorted(duplicates))
    known = set(identifiers)
    for claim in claims:
        for dependency in claim.get("depends_on", []):
            if dependency not in known:
                errors.append(f"{claim.get('id')}: unknown dependency: {dependency}")
    return errors
