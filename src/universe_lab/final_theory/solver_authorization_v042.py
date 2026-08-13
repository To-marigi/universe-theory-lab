"""Fail-closed runtime authorization for production solver campaigns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_PATH = "CURRENT_RESEARCH_STATE.json"


class SolverAuthorizationError(RuntimeError):
    """Raised when a production solver is invoked without current authorization."""


def _load_state(root: Path) -> dict[str, Any]:
    return json.loads((root / STATE_PATH).read_text(encoding="utf-8"))


def require_production_solver_authorization(
    root: Path,
    *,
    campaign_id: str,
    budget_path: str,
) -> dict[str, Any]:
    """Require an explicit current-state reopen authorization before solver use.

    Historical budgets and an explicit command-line flag are not sufficient.  A
    future campaign must first record a dedicated owner-approved reopen decision,
    the exact versioned budget path, a tool/version, and the supervision plan in
    the mutable live state.  The current Phase-A freeze intentionally fails this
    check.
    """

    state = _load_state(root.resolve())
    affected = state.get("affected_campaign", {})
    phase_c = affected.get("phase_C", {})
    reopen = phase_c.get("reopen_authorization")
    violations: list[str] = []
    if affected.get("solver_run_permitted") is not True:
        violations.append("affected_campaign.solver_run_permitted is not true")
    if not isinstance(reopen, dict):
        violations.append("phase_C.reopen_authorization is missing")
        reopen = {}
    if reopen.get("status") != "AUTHORIZED":
        violations.append("phase_C.reopen_authorization.status is not AUTHORIZED")
    for field in (
        "owner_reopen_approval_present",
        "versioned_reopen_budget_present",
        "dedicated_cas_authorized",
        "specified_cas_and_version_present",
        "corrected_preflight_benchmark_present",
        "hard_timeout_and_memory_supervision_present",
        "staged_input_plan_present",
    ):
        if reopen.get(field) is not True:
            violations.append(f"phase_C.reopen_authorization.{field} is not true")
    if reopen.get("versioned_reopen_budget_path") != budget_path:
        violations.append("requested budget path is not the explicitly authorized reopen budget")
    if not violations:
        authorized_budget = root.resolve() / budget_path
        if not authorized_budget.is_file():
            violations.append(f"authorized reopen budget is missing: {budget_path}")
    if violations:
        raise SolverAuthorizationError(
            f"production solver campaign {campaign_id!r} is fail-closed: "
            + "; ".join(violations)
        )
    return {
        "authorized": True,
        "campaign_id": campaign_id,
        "budget_path": budget_path,
        "authorization_status": reopen["status"],
    }
