"""Bounded Phase-B implementation preflight aggregator.

This module composes already bounded, non-production certificates.  It does
not sample candidate or control trajectories and does not run a solver.  The
approved budget is intentionally limited to fixture execution and replay
validation.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_labeled_sampler_cost_preflight_v042 import (
    REPORT_PATH as COST_REPORT_PATH,
)
from universe_lab.final_theory.phase_b_labeled_sampler_cost_preflight_v042 import (
    RESULT_PATH as COST_RESULT_PATH,
)
from universe_lab.final_theory.phase_b_labeled_sampler_cost_preflight_v042 import (
    build_preflight as build_cost_preflight,
)
from universe_lab.final_theory.phase_b_labeled_sampler_cost_preflight_v042 import (
    render_report as render_cost_report,
)
from universe_lab.final_theory.phase_b_large_n_runtime_audit_v042 import (
    REPORT_PATH as RUNTIME_AUDIT_REPORT_PATH,
)
from universe_lab.final_theory.phase_b_large_n_runtime_audit_v042 import (
    RESULT_PATH as RUNTIME_AUDIT_RESULT_PATH,
)
from universe_lab.final_theory.phase_b_large_n_runtime_audit_v042 import (
    build_audit,
)
from universe_lab.final_theory.phase_b_large_n_runtime_audit_v042 import (
    render_report as render_runtime_audit_report,
)
from universe_lab.final_theory.phase_b_supervisor_v042 import (
    REPORT_PATH as SUPERVISOR_REPORT_PATH,
)
from universe_lab.final_theory.phase_b_supervisor_v042 import (
    RESULT_PATH as SUPERVISOR_RESULT_PATH,
)
from universe_lab.final_theory.phase_b_supervisor_v042 import (
    build_preflight as build_supervisor_preflight,
)
from universe_lab.final_theory.phase_b_supervisor_v042 import (
    render_report as render_supervisor_report,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-implementation-preflight-v1"
PREPARED = "2026-08-16"
STATUS = "PHASE_B_IMPLEMENTATION_PREFLIGHT_COMPLETE_NON_EVIDENTIARY"
NEXT_GATE = "PHASE_B_CONTROL_FIRST_PROTOCOL_FREEZE"
CONFIG_PATH = Path(
    "config/v0.4.2_phase_b_implementation_preflight_budget_20260816.json"
)
DESIGN_PATH = Path(
    "config/v0.4.2_phase_b_large_n_sampler_extension_design.json"
)
RESULT_PATH = Path("results/v0.4.2_phase_b_implementation_preflight_20260816.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_implementation_preflight_2026-08-16.md")
MODULE_PATH = Path(
    "src/universe_lab/final_theory/phase_b_implementation_preflight_v042.py"
)


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def _binding(root: Path, relative: Path) -> dict[str, Any]:
    raw = (root / relative).read_bytes()
    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode(
        "utf-8"
    )
    return {
        "path": relative.as_posix(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(canonical).hexdigest(),
        "size_bytes": len(raw),
        "strict_utf8_lf": "\r" not in text,
    }


def _tracked(root: Path, relative: Path) -> dict[str, Any]:
    return _load_json(root, relative)


def _report_matches(root: Path, relative: Path, expected: str) -> bool:
    return (root / relative).read_text(encoding="utf-8") == expected


def _certificate_match(
    tracked: dict[str, Any], rebuilt: dict[str, Any], *, core_only: bool
) -> bool:
    if core_only:
        return (
            tracked.get("certificate_core") == rebuilt.get("certificate_core")
            and tracked.get("semantic_digest_sha256")
            == rebuilt.get("semantic_digest_sha256")
        )
    return tracked == rebuilt


def _source_forbidden_tokens_absent(root: Path) -> bool:
    source = (root / MODULE_PATH).read_text(encoding="utf-8")
    forbidden = (
        "enumerate_" + "unlabeled_posets",
        "transition_" + "instrument",
        "propagate_" + "distribution",
        "itertools." + "permutations",
        "canonicalize" + "(",
        "automorphisms" + "(",
    )
    return not any(token in source for token in forbidden)


def build_preflight(root: Path) -> dict[str, Any]:
    """Rebuild and compose the bounded Phase-B implementation certificates."""

    config = _load_json(root, CONFIG_PATH)
    design = _load_json(root, DESIGN_PATH)
    limits = config["limits"]
    started = time.perf_counter()
    runtime_rebuilt = build_audit(root)
    cost_rebuilt = build_cost_preflight(root)
    supervisor_rebuilt = build_supervisor_preflight(root)
    elapsed = time.perf_counter() - started
    peak_child_traced = int(
        cost_rebuilt["runtime_observation"]["max_peak_tracemalloc_bytes"]
    )

    runtime_tracked = _tracked(root, RUNTIME_AUDIT_RESULT_PATH)
    cost_tracked = _tracked(root, COST_RESULT_PATH)
    supervisor_tracked = _tracked(root, SUPERVISOR_RESULT_PATH)
    runtime_report_matches = _report_matches(
        root, RUNTIME_AUDIT_REPORT_PATH, render_runtime_audit_report(runtime_tracked)
    )
    cost_report_matches = _report_matches(
        root, COST_REPORT_PATH, render_cost_report(cost_tracked)
    )
    supervisor_report_matches = _report_matches(
        root, SUPERVISOR_REPORT_PATH, render_supervisor_report(supervisor_tracked)
    )

    runtime_ok = _certificate_match(runtime_tracked, runtime_rebuilt, core_only=False)
    cost_ok = _certificate_match(cost_tracked, cost_rebuilt, core_only=True)
    supervisor_ok = _certificate_match(
        supervisor_tracked, supervisor_rebuilt, core_only=True
    )
    child_checks = {
        "runtime_audit_rebuild_matches": runtime_ok,
        "runtime_audit_report_matches": runtime_report_matches,
        "cost_preflight_rebuild_matches": cost_ok,
        "cost_preflight_report_matches": cost_report_matches,
        "supervisor_rebuild_matches": supervisor_ok,
        "supervisor_report_matches": supervisor_report_matches,
        "runtime_audit_acceptance_passed": runtime_tracked[
            "all_acceptance_checks_passed"
        ],
        "cost_preflight_acceptance_passed": cost_tracked[
            "all_acceptance_checks_passed"
        ],
        "supervisor_acceptance_passed": supervisor_tracked[
            "all_acceptance_checks_passed"
        ],
    }
    boundary_checks = {
        "owner_approved_implementation_budget": (
            config["owner_approval_present"] is True
            and config["authorizes_gate"]
            == "PHASE_B_BOUNDED_IMPLEMENTATION_PREFLIGHT_ONLY"
        ),
        "design_production_boundary_remains_closed": (
            design["authorization_boundary"]["production_sampling_authorized"]
            is False
            and design["authorization_boundary"]["solver_run_permitted"] is False
        ),
        "large_n_forbidden_paths_absent": _source_forbidden_tokens_absent(root),
        "new_trajectories_zero": (
            all(
                tracked.get("new_trajectories", 0) == 0
                for tracked in (runtime_tracked, cost_tracked, supervisor_tracked)
            )
            and limits["new_sampled_trajectories"] == 0
        ),
        "solver_calls_zero": (
            all(
                tracked.get("solver_calls", 0) == 0
                for tracked in (runtime_tracked, cost_tracked, supervisor_tracked)
            )
            and limits["solver_calls"] == 0
        ),
        "production_sampling_closed": all(
            tracked.get("production_sampling_authorized") is False
            for tracked in (runtime_tracked, cost_tracked, supervisor_tracked)
        ),
        "no_retry_budget": limits["max_retries"] == 0,
    }
    resource_checks = {
        "within_total_wall_budget": elapsed <= limits["max_total_wall_seconds"],
        "within_traced_memory_budget": peak_child_traced
        <= limits["max_memory_mib"] * 1024 * 1024,
    }
    checks = {**child_checks, **boundary_checks, **resource_checks}
    certificate_core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "budget_config_sha256": hashlib.sha256(
            (root / CONFIG_PATH).read_bytes()
        ).hexdigest(),
        "design_config_sha256": hashlib.sha256(
            (root / DESIGN_PATH).read_bytes()
        ).hexdigest(),
        "limits": limits,
        "child_semantic_digests": {
            "runtime_audit": runtime_tracked["semantic_digest_sha256"],
            "cost_preflight": cost_tracked["semantic_digest_sha256"],
            "hard_supervisor": supervisor_tracked["semantic_digest_sha256"],
        },
        "checks": checks,
        "authorization_boundary": {
            "implementation_preflight_authorized": True,
            "new_trajectories_authorized": False,
            "production_sampling_authorized": False,
            "solver_run_permitted": False,
            "scientific_verdict_added": False,
            "global_verdict": "FINAL_THEORY_OPEN",
        },
        "source_bindings": [
            _binding(root, CONFIG_PATH),
            _binding(root, DESIGN_PATH),
            _binding(root, MODULE_PATH),
            _binding(root, RUNTIME_AUDIT_RESULT_PATH),
            _binding(root, COST_RESULT_PATH),
            _binding(root, SUPERVISOR_RESULT_PATH),
        ],
    }
    all_checks = all(checks.values())
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "next_gate": NEXT_GATE,
        "scope": config["authorization_scope"],
        "certificate_core": certificate_core,
        "runtime_observation": {
            "total_elapsed_seconds": elapsed,
            "max_child_tracemalloc_bytes": peak_child_traced,
            "within_total_wall_budget": resource_checks["within_total_wall_budget"],
            "within_traced_memory_budget": resource_checks[
                "within_traced_memory_budget"
            ],
        },
        "all_acceptance_checks_passed": all_checks,
        "new_trajectories": 0,
        "solver_calls": 0,
        "production_sampling_authorized": False,
        "implementation_preflight_authorized": True,
        "production_measurement_budget_still_required": True,
        "semantic_digest_sha256": stable_hash(certificate_core),
    }
    if not all_checks:
        raise RuntimeError("Phase-B implementation preflight failed closed")
    return payload


def render_report(payload: dict[str, Any]) -> str:
    core = payload["certificate_core"]
    checks = core["checks"]
    observation = payload["runtime_observation"]
    lines = [
        "# Phase-B bounded implementation preflight — 2026-08-16",
        "",
        f"Status: **`{payload['status']}`**",
        "",
        f"Semantic digest: `{payload['semantic_digest_sha256']}`",
        "",
        "## Scope",
        "",
        "This certificate composes the runtime, labeled-sampler cost, and hard",
        "supervisor preflights under the owner-approved implementation budget.",
        "It does not sample candidate or control trajectories and does not run",
        "a solver.",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | `{value}` |" for name, value in checks.items())
    lines.extend(
        [
            "",
            "## Runtime observation",
            "",
            f"- Total bounded wall time: `{observation['total_elapsed_seconds']:.6f}` s",
            "- Maximum child traced allocation: "
            f"`{observation['max_child_tracemalloc_bytes']}` bytes",
            f"- Within wall budget: `{observation['within_total_wall_budget']}`",
            f"- Within traced-memory budget: `{observation['within_traced_memory_budget']}`",
            "",
            "## Boundary",
            "",
            "Implementation preflight is authorized only for the bounded fixture",
            "scope. Production measurement still requires a separate versioned",
            "budget; no trajectory, solver, continuum, dimension, Spin-2, or",
            "universal-coupling claim is issued.",
            "",
            f"Next gate: `{payload['next_gate']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
    (root / RESULT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with (root / RESULT_PATH).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (root / REPORT_PATH).open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_report(payload))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_preflight(args.root)
    if args.check:
        tracked = _tracked(args.root, RESULT_PATH)
        if (
            tracked.get("certificate_core") != payload.get("certificate_core")
            or tracked.get("semantic_digest_sha256")
            != payload.get("semantic_digest_sha256")
        ):
            raise SystemExit("tracked implementation preflight differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            tracked
        ):
            raise SystemExit("tracked implementation preflight report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
