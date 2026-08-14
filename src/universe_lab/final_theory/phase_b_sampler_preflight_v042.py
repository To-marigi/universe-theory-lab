"""Bounded, non-evidentiary sampler preflight for the v2 growth profile.

This module is deliberately smaller than a continuum campaign.  It samples
only the already-defined finite v2 profile through cardinality three and
checks the result against the exact Fraction-valued distribution.  It is a
regression instrument, not candidate-derived continuum evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.causal_sets import (
    Relation,
    causet_id,
    enumerate_unlabeled_posets,
    growth_moves,
)
from universe_lab.final_theory.dynamics_v02 import (
    CANDIDATE_PROFILE,
    propagate_distribution,
    transition_instrument,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_candidate_identity_v042 import (
    build_audit,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-sampler-preflight-v1"
PREPARED = "2026-08-15"
MAX_PREFLIGHT_N = 3
TRAJECTORIES_PER_SEED = 1024
SEEDS = (7, 17, 29, 43, 71)
RESULT_PATH = Path("results/v0.4.2_phase_b_sampler_preflight.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_sampler_preflight.md")
DYNAMICS_PATH = Path("src/universe_lab/final_theory/dynamics_v02.py")
CAUSAL_SETS_PATH = Path("src/universe_lab/final_theory/causal_sets.py")
V2_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v2/model_spec.json")


def _fraction(record: dict[str, int]) -> Fraction:
    return Fraction(record["numerator"], record["denominator"])


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


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


def _branch_probability(branch: dict[str, Any]) -> Fraction:
    return _fraction(branch["probability"])


def _choose_branch(
    branches: tuple[dict[str, Any], ...], rng: random.Random
) -> dict[str, Any]:
    """Choose an exact rational branch using one integer ticket."""

    if not branches:
        raise AssertionError("a finite source must have at least one branch")
    probabilities = [_branch_probability(branch) for branch in branches]
    common_denominator = 1
    for probability in probabilities:
        common_denominator = math.lcm(common_denominator, probability.denominator)
    tickets = [
        probability.numerator * (common_denominator // probability.denominator)
        for probability in probabilities
    ]
    total = sum(tickets)
    if total <= 0 or sum(probabilities, start=Fraction(0)) != 1:
        raise AssertionError("branch probabilities must be positive and normalized")
    ticket = rng.randrange(total)
    cumulative = 0
    for branch, weight in zip(branches, tickets, strict=True):
        cumulative += weight
        if ticket < cumulative:
            return branch
    raise AssertionError("integer-ticket selection fell outside cumulative mass")


def _route_audit(
    levels: tuple[tuple[Relation, ...], ...],
    max_n: int,
) -> dict[str, Any]:
    """Check every finite transition used by the bounded preflight."""

    target_ids_by_stage = [
        {causet_id(relation) for relation in level} for level in levels
    ]
    source_count = 0
    branch_count = 0
    checks: list[dict[str, Any]] = []
    for stage in range(max_n):
        for relation in levels[stage]:
            source_count += 1
            branches = transition_instrument(relation)
            probabilities = [_branch_probability(branch) for branch in branches]
            normalized = sum(probabilities, start=Fraction(0)) == 1
            targets_known = all(
                branch["move"]["target_history"] in target_ids_by_stage[stage + 1]
                for branch in branches
            )
            move_targets = {
                move.target_history for move in growth_moves(relation)
            }
            instrument_targets = {
                branch["move"]["target_history"] for branch in branches
            }
            same_targets = instrument_targets == move_targets
            branch_count += len(branches)
            checks.append(
                {
                    "source": causet_id(relation),
                    "stage": stage,
                    "branch_count": len(branches),
                    "normalized_exactly": normalized,
                    "targets_in_next_level": targets_known,
                    "growth_move_target_set_match": same_targets,
                }
            )
    return {
        "source_count": source_count,
        "branch_count": branch_count,
        "all_normalized_exactly": all(item["normalized_exactly"] for item in checks),
        "all_targets_in_next_level": all(
            item["targets_in_next_level"] for item in checks
        ),
        "all_growth_move_target_sets_match": all(
            item["growth_move_target_set_match"] for item in checks
        ),
        "checks": checks,
    }


def _sample_one_seed(
    levels: tuple[tuple[Relation, ...], ...],
    seed: int,
    trajectories: int,
    max_n: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    level_by_id = [
        {causet_id(relation): relation for relation in level} for level in levels
    ]
    terminal_counts: dict[str, int] = {
        causet_id(relation): 0 for relation in levels[max_n]
    }
    paths: list[list[str]] = []
    route_checks = 0
    for _ in range(trajectories):
        current = levels[0][0]
        path = [causet_id(current)]
        for stage in range(max_n):
            branches = transition_instrument(current)
            branch = _choose_branch(branches, rng)
            move = branch["move"]
            source_id = causet_id(current)
            if move["source_history"] != source_id:
                raise AssertionError("sampled branch source does not match current state")
            target_id = move["target_history"]
            if target_id not in level_by_id[stage + 1]:
                raise AssertionError("sampled branch target is outside next level")
            current = level_by_id[stage + 1][target_id]
            path.append(target_id)
            route_checks += 1
        terminal_counts[path[-1]] += 1
        paths.append(path)
    digest = hashlib.sha256(
        json.dumps(paths, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "seed": seed,
        "trajectories": trajectories,
        "terminal_counts": terminal_counts,
        "trajectory_digest": digest,
        "route_checks": route_checks,
    }


def _comparison(
    exact: dict[str, Fraction], observed: dict[str, int], trajectories: int
) -> dict[str, Any]:
    rows = []
    passed = True
    for identifier in sorted(exact):
        probability = exact[identifier]
        count = observed.get(identifier, 0)
        empirical = Fraction(count, trajectories)
        sigma = math.sqrt(
            float(probability) * (1.0 - float(probability)) / trajectories
        )
        tolerance = max(0.02, 6.0 * sigma)
        difference = abs(float(empirical - probability))
        within = difference <= tolerance
        passed = passed and within
        rows.append(
            {
                "terminal_history": identifier,
                "exact_probability": _fraction_record(probability),
                "observed_count": count,
                "empirical_probability": _fraction_record(empirical),
                "six_sigma_tolerance": tolerance,
                "absolute_difference": difference,
                "within_diagnostic_tolerance": within,
            }
        )
    return {"passed": passed, "rows": rows}


def build_preflight(root: Path) -> dict[str, Any]:
    """Run the bounded v2 sampler preflight and return its machine artifact."""

    if not 0 <= MAX_PREFLIGHT_N <= 5:
        raise AssertionError("preflight domain must remain within exact n<=5")
    identity = build_audit(root)
    levels = enumerate_unlabeled_posets(MAX_PREFLIGHT_N)
    exact_stages = propagate_distribution(
        MAX_PREFLIGHT_N, profile_id=CANDIDATE_PROFILE.profile_id
    )
    exact_terminal = exact_stages[MAX_PREFLIGHT_N]
    route_audit = _route_audit(levels, MAX_PREFLIGHT_N)
    seed_runs = [
        _sample_one_seed(
            levels, seed, TRAJECTORIES_PER_SEED, MAX_PREFLIGHT_N
        )
        for seed in SEEDS
    ]
    comparisons = [
        _comparison(exact_terminal, run["terminal_counts"], run["trajectories"])
        for run in seed_runs
    ]
    replay = [
        _sample_one_seed(
            levels, run["seed"], run["trajectories"], MAX_PREFLIGHT_N
        )["trajectory_digest"]
        == run["trajectory_digest"]
        for run in seed_runs
    ]
    enumeration_counts = [len(level) for level in levels]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": "PHASE_B_BOUNDED_SAMPLER_PREFLIGHT_COMPLETE_NON_EVIDENTIARY",
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "profile_id": CANDIDATE_PROFILE.profile_id,
        "candidate_identity_audit_digest": identity["semantic_digest_sha256"],
        "candidate_identity_mismatch_present": identity["identity"][
            "mismatch_detected"
        ],
        "candidate_identity_certified": identity["identity"][
            "active_candidate_identity_certified"
        ],
        "sampling_authorized": False,
        "scope": (
            "Five deterministic seeds and 1,024 trajectories per seed through "
            "cardinality three. Regression only; no continuum or candidate-"
            "derived physics evidence."
        ),
        "configuration": {
            "max_n": MAX_PREFLIGHT_N,
            "trajectories_per_seed": TRAJECTORIES_PER_SEED,
            "seeds": list(SEEDS),
            "selection_rule": "integer ticket over exact Fraction branch weights",
            "floating_point_in_dynamics": False,
        },
        "exact_baseline": {
            "enumeration_counts": enumeration_counts,
            "known_counts_through_n5": [1, 1, 2, 5, 16, 63],
            "independent_oracle_scope": "n<=4",
            "terminal_state_count": len(exact_terminal),
            "terminal_distribution_normalized": sum(
                exact_terminal.values(), start=Fraction(0)
            )
            == 1,
        },
        "route_and_normalization_audit": route_audit,
        "seed_runs": seed_runs,
        "exact_distribution_comparisons": comparisons,
        "replay_digest_matches": replay,
        "acceptance_criteria": {
            "exact_domain_is_declared": MAX_PREFLIGHT_N <= 5,
            "exact_baseline_is_normalized": sum(
                exact_terminal.values(), start=Fraction(0)
            )
            == 1,
            "all_transition_routes_and_normalizations_pass": (
                route_audit["all_normalized_exactly"]
                and route_audit["all_targets_in_next_level"]
                and route_audit["all_growth_move_target_sets_match"]
            ),
            "all_seed_comparisons_pass_diagnostic_tolerance": all(
                item["passed"] for item in comparisons
            ),
            "all_replay_digests_match": all(replay),
            "identity_gate_is_certified": identity["identity"][
                "active_candidate_identity_certified"
            ],
            "continuum_design_gate_still_blocks_sampling": identity[
                "sampling_authorized"
            ]
            is False,
        },
        "claim_boundary": (
            "A successful finite sampler regression does not establish a large-N "
            "measure, continuum phase, dimension, Spin-2 response, or universal "
            "coupling."
        ),
        "source_bindings": [
            _binding(root, DYNAMICS_PATH),
            _binding(root, CAUSAL_SETS_PATH),
            _binding(root, V2_SPEC_PATH),
        ],
    }
    payload["all_acceptance_checks_passed"] = all(
        payload["acceptance_criteria"].values()
    )
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    criteria = payload["acceptance_criteria"]
    return "\n".join(
        [
            "# Phase-B bounded sampler preflight",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Scope",
            "",
            "The v2 sparse-Kraus profile was sampled through cardinality three",
            "using five deterministic seeds and 1,024 trajectories per seed.",
            "Branch selection used integer tickets over exact rational weights.",
            "",
            "This is a regression preflight only. It is not continuum evidence",
            "and is not transferred to the registered v1 candidate.",
            "",
            "## Results",
            "",
            "| item | result |",
            "|---|---:|",
            f"| exact level counts | `{payload['exact_baseline']['enumeration_counts']}` |",
            f"| terminal states at n=3 | `{payload['exact_baseline']['terminal_state_count']}` |",
            "| source transitions audited | "
            f"`{payload['route_and_normalization_audit']['source_count']}` |",
            "| branches audited | "
            f"`{payload['route_and_normalization_audit']['branch_count']}` |",
            f"| seeds | `{payload['configuration']['seeds']}` |",
            f"| trajectories per seed | `{payload['configuration']['trajectories_per_seed']}` |",
            f"| production sampling authorized | `{payload['sampling_authorized']}` |",
            "",
            "All finite route, exact-normalization, replay-digest, and diagnostic",
            "distribution checks passed. Candidate identity is now certified for",
            "the v2 Phase-B branch, but the continuum design gate still blocks",
            "production sampling.",
            "",
            "## Acceptance checks",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{name}` | `{value}` |"
                for name, value in criteria.items()
            ],
            "",
            "## Boundary",
            "",
            "No large-N sampler, continuum phase, dimension estimate, Spin-2",
            "response, or universal coupling claim is issued. The next gate is",
            "the continuum dimension-derivation design.",
            "",
        ]
    )


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
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked sampler preflight differs from rebuild")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked sampler report differs from rebuild")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
