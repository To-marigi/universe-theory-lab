from __future__ import annotations

from pathlib import Path

import pytest

from universe_lab.final_theory.solver_authorization_v042 import (
    SolverAuthorizationError,
    require_production_solver_authorization,
)

ROOT = Path(__file__).resolve().parents[2]


def test_current_frozen_state_blocks_legacy_production_solver_entrypoint() -> None:
    with pytest.raises(SolverAuthorizationError, match="fail-closed"):
        require_production_solver_authorization(
            ROOT,
            campaign_id="v041_restricted_locus_qq",
            budget_path="config/v0.4.1_budget.json",
        )


def test_guard_requires_exact_reopen_budget_path() -> None:
    with pytest.raises(SolverAuthorizationError, match="authorized reopen budget"):
        require_production_solver_authorization(
            ROOT,
            campaign_id="test-campaign",
            budget_path="config/v0.4.2_nonexistent_reopen_budget.json",
        )
