"""Bounded measurement preflight for the Phase-B continuum design.

The preflight is confined to the existing exact n<=5 domain.  It validates
measurement code and controls while explicitly refusing the planned large-N
campaign, which still lacks a sampler extension, a BDG ensemble control, and a
production budget.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

from universe_lab.final_theory.causal_sets import (
    causet_id,
    enumerate_unlabeled_posets,
    height,
)
from universe_lab.final_theory.continuum_observables_v042 import (
    connected_component_sizes,
    correlation_length_record,
    height_scaling_dimension,
    lazy_transition_matrix,
    minkowski_ordering_fraction,
    ordering_fraction,
    ordering_fraction_dimension,
    relabel_relation,
    spectral_dimension_from_curve,
    spectral_return_curve,
)
from universe_lab.final_theory.dynamics_v02 import (
    BDG_CONTROL_PROFILE,
    CANDIDATE_PROFILE,
    RANDOM_CONTROL_PROFILE,
    propagate_distribution,
    transition_instrument,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash
from universe_lab.final_theory.phase_b_continuum_dimension_design_v042 import (
    CONTINUUM_SOURCES_LEDGER_FROZEN_BINDING,
    build_design,
    validate_continuum_reference_records,
)
from universe_lab.final_theory.phase_b_continuum_dimension_design_v042 import (
    RESULT_PATH as DESIGN_RESULT_PATH,
)
from universe_lab.final_theory.phase_b_continuum_dimension_design_v042 import (
    STATUS as DESIGN_STATUS,
)

SCHEMA_VERSION = "final-theory-v042-phase-b-continuum-dimension-preflight-v1"
PREPARED = "2026-08-15"
STATUS = (
    "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_MEASUREMENT_PREFLIGHT_COMPLETE_"
    "PRODUCTION_EXTENSION_REQUIRED"
)
START_GATE = "PHASE_B_CONTINUUM_DIMENSION_BOUNDED_MEASUREMENT_PREFLIGHT"
NEXT_GATE = "PHASE_B_CONTINUUM_DIMENSION_LARGE_N_SAMPLER_EXTENSION_DESIGN"
RESULT_PATH = Path("results/v0.4.2_phase_b_continuum_dimension_preflight.json")
REPORT_PATH = Path("reports/v0.4.2_phase_b_continuum_dimension_preflight.md")
BUDGET_PATH = Path(
    "config/v0.4.2_phase_b_continuum_dimension_bounded_preflight_budget.json"
)
DESIGN_CONFIG_PATH = Path("config/v0.4.2_phase_b_continuum_dimension_design.json")
OBSERVABLES_PATH = Path(
    "src/universe_lab/final_theory/continuum_observables_v042.py"
)
CAUSAL_SETS_PATH = Path("src/universe_lab/final_theory/causal_sets.py")
DYNAMICS_PATH = Path("src/universe_lab/final_theory/dynamics_v02.py")
V2_SPEC_PATH = Path("Final-Theory-Program/models/causal_information_v2/model_spec.json")
CAPABILITIES_PATH = Path(
    "config/v0.4.2_phase_b_continuum_dimension_capabilities.json"
)
SOURCES_LEDGER_PATH = Path("references/sources.json")
CALIBRATION_NOTE_PATH = Path(
    "references/notes/v0.4.2_myrheim_meyer_calibration_audit_2026-08-15.md"
)


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _binding(root: Path, relative: Path) -> dict[str, Any]:
    raw = (root / relative).read_bytes()
    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return {
        "path": relative.as_posix(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(canonical).hexdigest(),
        "size_bytes": len(raw),
        "strict_utf8_lf": "\r" not in text,
    }


def _fraction_record(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _rounded(value: float | None) -> float | None:
    return None if value is None else float(f"{value:.12g}")


def _weighted_height(
    distribution: dict[str, Fraction], relation_by_id: dict[str, tuple[int, ...]]
) -> Fraction:
    return sum(
        (
            probability * height(relation_by_id[identifier])
            for identifier, probability in distribution.items()
        ),
        start=Fraction(0),
    )


def _ensemble_measurement(
    level: tuple[tuple[int, ...], ...],
    distribution: dict[str, Fraction],
    *,
    max_walk_steps: int,
    spectral_fit_steps: tuple[int, ...],
) -> dict[str, Any]:
    n = len(level[0]) if level else 0
    relation_by_id = {causet_id(relation): relation for relation in level}
    normalized = sum(distribution.values(), start=Fraction(0)) == 1

    mean_ordering: Fraction | None = None
    ordering_dimension: float | None = None
    if n >= 2:
        mean_ordering = Fraction(0)
        for identifier, probability in distribution.items():
            relation_ordering = ordering_fraction(relation_by_id[identifier])
            if relation_ordering is None:
                raise TypeError(
                    "ordering fraction must be defined for n >= 2"
                )
            mean_ordering += probability * relation_ordering
        ordering_dimension = ordering_fraction_dimension(mean_ordering)

    spectral_returns: list[Fraction] = []
    spectral_dimension: float | None = None
    component_signature_masses: dict[tuple[int, ...], Fraction] = {}
    expected_component_count: Fraction | None = None
    connected_mass: Fraction | None = None
    expected_largest_component_fraction: Fraction | None = None
    expected_saturation_floor: Fraction | None = None
    if n >= 1:
        curves = {
            identifier: spectral_return_curve(relation, max_walk_steps)
            for identifier, relation in relation_by_id.items()
        }
        for step_index in range(max_walk_steps):
            step_total = Fraction(0)
            for identifier, probability in distribution.items():
                return_probability = curves[identifier][
                    "return_probabilities"
                ][step_index]
                if not isinstance(return_probability, Fraction):
                    raise TypeError(
                        "spectral return probability must be an exact Fraction"
                    )
                step_total += probability * return_probability
            spectral_returns.append(step_total)
        if len(spectral_fit_steps) >= 4 and all(
            1 <= step <= max_walk_steps for step in spectral_fit_steps
        ):
            fit_returns = [
                float(spectral_returns[step - 1]) for step in spectral_fit_steps
            ]
            spectral_dimension = spectral_dimension_from_curve(
                spectral_fit_steps, fit_returns
            )
        expected_component_count = Fraction(0)
        connected_mass = Fraction(0)
        expected_largest_component_fraction = Fraction(0)
        expected_saturation_floor = Fraction(0)
        for identifier, probability in distribution.items():
            sizes = tuple(curves[identifier]["component_sizes"])
            component_signature_masses[sizes] = (
                component_signature_masses.get(sizes, Fraction(0)) + probability
            )
            component_count = len(sizes)
            expected_component_count += probability * component_count
            connected_mass += probability * (component_count == 1)
            expected_largest_component_fraction += probability * Fraction(
                max(sizes), n
            )
            expected_saturation_floor += probability * Fraction(component_count, n)

    valid_mass = Fraction(0)
    weighted_xi_squared = 0.0
    weighted_ratio_squared = 0.0
    ratio_valid_mass = Fraction(0)
    weighted_coverage = 0.0
    for identifier, probability in distribution.items():
        correlation = correlation_length_record(relation_by_id[identifier])
        weighted_coverage += float(probability) * correlation[
            "nontrivial_vertex_coverage"
        ]
        if correlation["defined"]:
            valid_mass += probability
            weighted_xi_squared += float(probability) * correlation["xi_squared"]
            if correlation["xi_over_diameter"] is not None:
                ratio_valid_mass += probability
                weighted_ratio_squared += (
                    float(probability) * correlation["xi_over_diameter"] ** 2
                )

    return {
        "n": n,
        "state_count": len(level),
        "normalized_exactly": normalized,
        "expected_ordering_fraction": _fraction_record(mean_ordering),
        "ordering_fraction_dimension": _rounded(ordering_dimension),
        "expected_height": _fraction_record(
            _weighted_height(distribution, relation_by_id)
        ),
        "spectral_return_probabilities": [
            _fraction_record(value) for value in spectral_returns
        ],
        "spectral_fit_steps": list(spectral_fit_steps),
        "spectral_dimension_diagnostic": _rounded(spectral_dimension),
        "spectral_component_diagnostics": {
            "signature_probability_masses": [
                {
                    "component_sizes": list(signature),
                    "probability_mass": _fraction_record(probability),
                }
                for signature, probability in sorted(
                    component_signature_masses.items()
                )
            ],
            "expected_component_count": _fraction_record(
                expected_component_count
            ),
            "connected_probability_mass": _fraction_record(connected_mass),
            "expected_largest_component_fraction": _fraction_record(
                expected_largest_component_fraction
            ),
            "expected_finite_size_saturation_floor": _fraction_record(
                expected_saturation_floor
            ),
        },
        "correlation_length_valid_probability_mass": _fraction_record(valid_mass),
        "conditional_rms_correlation_length": (
            _rounded(math.sqrt(weighted_xi_squared / float(valid_mass)))
            if valid_mass
            else None
        ),
        "correlation_length_ratio_valid_probability_mass": _fraction_record(
            ratio_valid_mass
        ),
        "conditional_rms_correlation_length_over_diameter": (
            _rounded(math.sqrt(weighted_ratio_squared / float(ratio_valid_mass)))
            if ratio_valid_mass
            else None
        ),
        "mean_nontrivial_vertex_coverage": _rounded(weighted_coverage),
    }


def _label_invariance_audit(
    levels: tuple[tuple[tuple[int, ...], ...], ...], max_walk_steps: int
) -> dict[str, Any]:
    relation_checks = 0
    permutation_checks = 0
    failure_count = 0
    failed_relation_ids: set[str] = set()
    failed_cases: list[dict[str, Any]] = []
    maximum_xi_error = 0.0
    for n, level in enumerate(levels):
        for relation in level:
            relation_checks += 1
            identifier = causet_id(relation)
            original_correlation = correlation_length_record(relation)
            original_ordering = ordering_fraction(relation)
            original_height = height(relation)
            original_components = connected_component_sizes(relation)
            original_spectral = spectral_return_curve(relation, max_walk_steps)
            for permutation in itertools.permutations(range(n)):
                permutation_checks += 1
                relabeled = relabel_relation(relation, permutation)
                relabeled_correlation = correlation_length_record(relabeled)
                invariant = (
                    original_ordering == ordering_fraction(relabeled)
                    and original_height == height(relabeled)
                    and original_components == connected_component_sizes(relabeled)
                    and original_spectral
                    == spectral_return_curve(relabeled, max_walk_steps)
                    and original_correlation["defined"]
                    == relabeled_correlation["defined"]
                    and original_correlation.get("reason")
                    == relabeled_correlation.get("reason")
                    and original_correlation.get("graph_diameter")
                    == relabeled_correlation.get("graph_diameter")
                    and original_correlation["nontrivial_vertex_coverage"]
                    == relabeled_correlation["nontrivial_vertex_coverage"]
                )
                if (
                    original_correlation["defined"]
                    and relabeled_correlation["defined"]
                ):
                    error = abs(
                        original_correlation["xi"] - relabeled_correlation["xi"]
                    )
                    maximum_xi_error = max(maximum_xi_error, error)
                    invariant = (
                        invariant
                        and error <= 1e-12
                        and abs(
                            original_correlation["xi_squared"]
                            - relabeled_correlation["xi_squared"]
                        )
                        <= 1e-12
                    )
                if not invariant:
                    failure_count += 1
                    failed_relation_ids.add(identifier)
                    if len(failed_cases) < 100:
                        failed_cases.append(
                            {
                                "relation_id": identifier,
                                "permutation": list(permutation),
                            }
                        )
    return {
        "relations_checked": relation_checks,
        "permutations_checked": permutation_checks,
        "failed_permutation_count": failure_count,
        "failed_relation_ids": sorted(failed_relation_ids),
        "failed_cases_first_100": failed_cases,
        "maximum_correlation_length_abs_error": _rounded(maximum_xi_error),
        "passed": failure_count == 0,
    }


def _analytic_control_audit(
    levels: tuple[tuple[tuple[int, ...], ...], ...], max_walk_steps: int
) -> dict[str, Any]:
    calibration_dimensions = (1.5, 2.0, 3.0, 4.0, 5.0)
    recovered = [
        ordering_fraction_dimension(minkowski_ordering_fraction(dimension))
        for dimension in calibration_dimensions
    ]
    ordering_errors = [
        abs(float(found) - expected)
        for found, expected in zip(recovered, calibration_dimensions, strict=True)
        if found is not None
    ]
    ordering_anchor_expected = {"2": 0.5, "4": 0.1}
    ordering_anchor_computed = {
        dimension: minkowski_ordering_fraction(float(dimension))
        for dimension in ordering_anchor_expected
    }
    ordering_anchor_errors = [
        abs(ordering_anchor_computed[dimension] - expected)
        for dimension, expected in ordering_anchor_expected.items()
    ]
    synthetic_sizes = (16.0, 81.0, 256.0, 625.0)
    synthetic_heights = tuple(size ** 0.25 for size in synthetic_sizes)
    height_dimension = height_scaling_dimension(synthetic_sizes, synthetic_heights)
    spectral_steps = tuple(float(step) for step in range(1, max_walk_steps + 1))
    spectral_returns = tuple(step**-2 for step in spectral_steps)
    spectral_dimension = spectral_dimension_from_curve(
        spectral_steps, spectral_returns
    )
    transition_rows_checked = 0
    transition_row_failures = 0
    for level in levels:
        for relation in level:
            matrix = lazy_transition_matrix(relation)
            for row in matrix:
                transition_rows_checked += 1
                if sum(row, start=Fraction(0)) != 1:
                    transition_row_failures += 1
    return {
        "control_scope": {
            "ordering_anchor_check": "external source-backed known values",
            "ordering_round_trip": "arithmetic smoke test",
            "height_power_law": "synthetic regression smoke test",
            "spectral_power_law": "synthetic regression smoke test",
            "end_to_end_bdg_ensemble_control": False,
        },
        "ordering_calibration_dimensions": list(calibration_dimensions),
        "ordering_max_abs_error": _rounded(max(ordering_errors, default=0.0)),
        "ordering_anchor_expected": ordering_anchor_expected,
        "ordering_anchor_computed": {
            dimension: _rounded(value)
            for dimension, value in ordering_anchor_computed.items()
        },
        "ordering_anchor_max_abs_error": _rounded(
            max(ordering_anchor_errors, default=0.0)
        ),
        "height_dimension_four_recovered": _rounded(height_dimension),
        "spectral_dimension_four_recovered": _rounded(spectral_dimension),
        "lazy_transition_rows_checked": transition_rows_checked,
        "lazy_transition_row_failures": transition_row_failures,
        "passed": (
            max(ordering_errors, default=0.0) <= 1e-7
            and max(ordering_anchor_errors, default=0.0) <= 1e-12
            and height_dimension is not None
            and abs(height_dimension - 4.0) <= 1e-12
            and spectral_dimension is not None
            and abs(spectral_dimension - 4.0) <= 1e-12
            and transition_row_failures == 0
        ),
    }


def _transition_capability(profile_id: str) -> dict[str, Any]:
    try:
        transition_instrument((), profile_id=profile_id)
    except ValueError as error:
        expected = f"profile does not define this instrument: {profile_id}"
        return {
            "profile_id": profile_id,
            "transition_instrument_available": False,
            "expected_unsupported_error": str(error) == expected,
            "reason": str(error),
        }
    return {
        "profile_id": profile_id,
        "transition_instrument_available": True,
        "expected_unsupported_error": None,
        "reason": None,
    }


def _capability_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    records = {
        "candidate": _transition_capability(CANDIDATE_PROFILE.profile_id),
        "negative_control": _transition_capability(
            RANDOM_CONTROL_PROFILE.profile_id
        ),
        "positive_control": _transition_capability(BDG_CONTROL_PROFILE.profile_id),
    }
    manifest_records = {
        "candidate": manifest["candidate_profile"],
        "negative_control": manifest["negative_control_profile"],
        "positive_control": manifest["positive_control_profile"],
    }
    passed = all(
        records[name]["profile_id"] == expected["profile_id"]
        and records[name]["transition_instrument_available"]
        is expected["transition_instrument_available"]
        for name, expected in manifest_records.items()
    ) and records["positive_control"]["expected_unsupported_error"] is True
    return {
        "manifest_records": manifest_records,
        "runtime_probe_records": records,
        "passed": passed,
    }


def build_preflight(root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    validate_continuum_reference_records(root)
    budget = _load_json(root, BUDGET_PATH)
    config = _load_json(root, DESIGN_CONFIG_PATH)
    capabilities = _load_json(root, CAPABILITIES_PATH)
    v2_spec = _load_json(root, V2_SPEC_PATH)
    design = build_design(root)
    tracked_design = _load_json(root, DESIGN_RESULT_PATH)
    limits = budget["limits"]
    max_n = limits["max_n"]
    max_walk_steps = limits["max_lazy_walk_steps"]
    spectral_estimator = next(
        estimator
        for estimator in config["dimension_estimators"]
        if estimator["id"] == "spectral_return_plateau"
    )
    spectral_fit_steps = tuple(
        spectral_estimator["bounded_preflight_fit"]["walk_time_steps"]
    )
    if max_n > config["exact_pilot_domain"]["max_n"]:
        raise ValueError("preflight max_n exceeds the frozen exact pilot domain")
    if limits["new_sampled_trajectories"] != 0 or limits["solver_calls"] != 0:
        raise ValueError("bounded preflight must not sample or call a solver")

    def enforce_runtime_budget(stage: str) -> None:
        if time.perf_counter() - started > limits["max_runtime_seconds"]:
            raise TimeoutError(f"bounded preflight exceeded runtime budget at {stage}")

    levels = enumerate_unlabeled_posets(max_n)
    relation_count = sum(len(level) for level in levels)
    if relation_count > limits["max_unlabeled_relations"]:
        raise ValueError("preflight relation count exceeds the versioned budget")
    candidate_stages = propagate_distribution(
        max_n, profile_id=CANDIDATE_PROFILE.profile_id
    )
    random_stages = propagate_distribution(
        max_n, profile_id=RANDOM_CONTROL_PROFILE.profile_id
    )
    candidate_measurements = [
        _ensemble_measurement(
            level,
            distribution,
            max_walk_steps=max_walk_steps,
            spectral_fit_steps=spectral_fit_steps,
        )
        for level, distribution in zip(levels, candidate_stages, strict=True)
    ]
    random_measurements = [
        _ensemble_measurement(
            level,
            distribution,
            max_walk_steps=max_walk_steps,
            spectral_fit_steps=spectral_fit_steps,
        )
        for level, distribution in zip(levels, random_stages, strict=True)
    ]
    enforce_runtime_budget("ensemble measurements")

    height_sizes = [float(record["n"]) for record in candidate_measurements if record["n"] >= 2]
    candidate_heights = [
        record["expected_height"]["numerator"]
        / record["expected_height"]["denominator"]
        for record in candidate_measurements
        if record["n"] >= 2
    ]
    random_heights = [
        record["expected_height"]["numerator"]
        / record["expected_height"]["denominator"]
        for record in random_measurements
        if record["n"] >= 2
    ]
    label_audit = _label_invariance_audit(levels, max_walk_steps)
    enforce_runtime_budget("exhaustive relabeling audit")
    analytic_controls = _analytic_control_audit(levels, max_walk_steps)
    capability_audit = _capability_audit(capabilities)
    planned_sizes = config["scaling_protocol"]["planned_sizes"]
    candidate_capability = capabilities["candidate_profile"]
    positive_control_capability = capabilities["positive_control_profile"]
    current_max_n = candidate_capability["exact_enumeration_verified_max_n"]
    production_max_n = candidate_capability["production_sampler_max_n"]
    large_n_domain_available = (
        candidate_capability["production_sampler_available"] is True
        and production_max_n is not None
        and production_max_n >= max(planned_sizes)
    )
    exact_normalization_passed = all(
        record["normalized_exactly"]
        for record in (*candidate_measurements, *random_measurements)
    )
    checks = {
        "versioned_scope_and_gate_authorization_are_bounded": {
            "passed": (
                budget["owner_approval_present"] is True
                and budget["authorizes_gate"] == START_GATE
                and budget["authorization_relationship"][
                    "supersedes_design_field_for_this_gate_only"
                ]
                == "authorization_boundary.bounded_measurement_preflight_authorized"
                and budget["authorization_relationship"]["prior_value"] is False
                and budget["authorization_relationship"]["effective_value"] is True
                and budget["authorization_relationship"][
                    "production_authorization_unchanged"
                ]
                is True
                and config["authorization_boundary"][
                    "bounded_measurement_preflight_authorized"
                ]
                is False
                and budget["production_sampling_authorized"] is False
                and budget["large_n_extension_authorized"] is False
                and budget["solver_run_permitted"] is False
                and relation_count <= limits["max_unlabeled_relations"]
                and time.perf_counter() - started <= limits["max_runtime_seconds"]
            ),
            "evidence": {
                **limits,
                "authorizes_gate": budget["authorizes_gate"],
                "internal_runtime_guard_checked_during_build": True,
                "hard_memory_supervisor_used": False,
            },
        },
        "frozen_design_rebuilds_exactly": {
            "passed": (
                design == tracked_design
                and design["status"] == DESIGN_STATUS
                and design["all_acceptance_checks_passed"] is True
            ),
            "evidence": design["semantic_digest_sha256"],
        },
        "exact_candidate_and_negative_control_normalize": {
            "passed": exact_normalization_passed,
            "evidence": {"max_n": max_n, "relations": relation_count},
        },
        "analytic_smoke_and_source_anchor_controls_pass": {
            "passed": analytic_controls["passed"],
            "evidence": analytic_controls,
        },
        "all_bounded_relations_are_label_invariant": {
            "passed": label_audit["passed"],
            "evidence": label_audit,
        },
        "spectral_preflight_window_and_component_diagnostics_are_explicit": {
            "passed": (
                spectral_fit_steps == (2, 3, 4, 5)
                and spectral_estimator["production_plateau_window_frozen"] is False
                and all(
                    record["spectral_fit_steps"] == list(spectral_fit_steps)
                    and "spectral_component_diagnostics" in record
                    for record in (*candidate_measurements, *random_measurements)
                )
            ),
            "evidence": {
                "bounded_preflight_fit_steps": list(spectral_fit_steps),
                "production_plateau_window_frozen": spectral_estimator[
                    "production_plateau_window_frozen"
                ],
            },
        },
        "correlation_ensemble_aggregation_matches_design": {
            "passed": (
                config["correlation_length_observable"]["ensemble_aggregation"]
                == "conditional root-mean-square sqrt(E[xi^2 | xi defined])"
                and all(
                    "conditional_rms_correlation_length" in record
                    and "conditional_rms_correlation_length_over_diameter" in record
                    for record in (*candidate_measurements, *random_measurements)
                )
            ),
            "evidence": config["correlation_length_observable"],
        },
        "structured_capability_manifest_matches_runtime": {
            "passed": (
                capability_audit["passed"]
                and v2_spec["model_id"] == candidate_capability["profile_id"]
                and current_max_n == config["exact_pilot_domain"]["max_n"]
            ),
            "evidence": capability_audit,
        },
        "large_n_domain_gap_is_fail_closed": {
            "passed": (
                large_n_domain_available is False
                and current_max_n < min(planned_sizes)
                and candidate_capability["production_sampler_available"] is False
                and production_max_n is None
            ),
            "evidence": {
                "current_max_n": current_max_n,
                "planned_sizes": planned_sizes,
            },
        },
        "bdg_positive_control_gap_is_fail_closed": {
            "passed": (
                positive_control_capability["ensemble_sampler_available"] is False
                and positive_control_capability["implemented_dimension"] is None
                and capability_audit["runtime_probe_records"]["positive_control"][
                    "transition_instrument_available"
                ]
                is False
            ),
            "evidence": positive_control_capability,
        },
        "no_scientific_or_production_authorization_is_added": {
            "passed": (
                config["authorization_boundary"]["production_sampling_authorized"]
                is False
                and budget["production_sampling_authorized"] is False
                and budget["solver_run_permitted"] is False
            ),
            "evidence": {
                "production_sampling_authorized": False,
                "solver_run_permitted": False,
            },
        },
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prepared": PREPARED,
        "status": STATUS,
        "global_verdict": "FINAL_THEORY_OPEN",
        "scientific_verdict_added": False,
        "scientific_evidence": False,
        "starting_gate": START_GATE,
        "next_gate": NEXT_GATE,
        "scope": (
            "Exact n<=5 arithmetic, source-calibration, schema, normalization, "
            "and exhaustive label-invariance preflight. No new histories, planned "
            "production sizes, parameter fits, or solver calls are permitted."
        ),
        "budget": {
            "path": BUDGET_PATH.as_posix(),
            "limits": limits,
            "owner_approval_present": budget["owner_approval_present"],
            "authorizes_gate": budget["authorizes_gate"],
            "authorization_relationship": budget["authorization_relationship"],
        },
        "resource_controls": {
            "finite_domain_structurally_bounded": True,
            "internal_elapsed_time_guard_present": True,
            "hard_wall_time_supervisor_used": False,
            "hard_memory_supervisor_used": False,
            "claim_boundary": (
                "The preflight is structurally finite and checks elapsed time "
                "between stages. The recorded 30-second and 512-MiB limits are "
                "not a production-grade external hard supervisor."
            ),
        },
        "numeric_backend": {
            "numpy_version": np.__version__,
            "artifact_rounding_significant_digits": 12,
        },
        "analytic_controls": analytic_controls,
        "label_invariance": label_audit,
        "capability_audit": capability_audit,
        "candidate_measurements": candidate_measurements,
        "random_control_measurements": random_measurements,
        "finite_size_diagnostics": {
            "sizes_used": [int(value) for value in height_sizes],
            "candidate_height_scaling_dimension": _rounded(
                height_scaling_dimension(height_sizes, candidate_heights)
            ),
            "random_height_scaling_dimension": _rounded(
                height_scaling_dimension(height_sizes, random_heights)
            ),
            "protocol_sizes_available": False,
            "claim_boundary": (
                "n=2..5 diagnostic fits do not satisfy the preregistered size "
                "set or scale separation and are not dimension evidence."
            ),
        },
        "readiness": {
            "bounded_arithmetic_and_invariance_checks_passed": True,
            "ordering_source_calibration_validated": True,
            "production_measurement_pipeline_validated": False,
            "current_exact_max_n": current_max_n,
            "planned_sizes": planned_sizes,
            "large_n_sampler_extension_available": large_n_domain_available,
            "bdg_positive_control_ensemble_available": positive_control_capability[
                "ensemble_sampler_available"
            ],
            "versioned_production_budget_present": False,
            "production_sampling_authorized": False,
            "blocking_requirements": config["production_design_gaps"],
        },
        "acceptance_checks": checks,
        "all_preflight_checks_passed": all(
            record["passed"] for record in checks.values()
        ),
        "continuum_phase_supported": False,
        "dimension_claim_issued": False,
        "production_sampling_authorized": False,
        "solver_run_permitted": False,
        "source_bindings": [
            _binding(root, BUDGET_PATH),
            _binding(root, DESIGN_CONFIG_PATH),
            _binding(root, DESIGN_RESULT_PATH),
            _binding(root, OBSERVABLES_PATH),
            _binding(root, CAUSAL_SETS_PATH),
            _binding(root, DYNAMICS_PATH),
            _binding(root, V2_SPEC_PATH),
            _binding(root, CAPABILITIES_PATH),
            dict(CONTINUUM_SOURCES_LEDGER_FROZEN_BINDING),
            _binding(root, CALIBRATION_NOTE_PATH),
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    analytic = payload["analytic_controls"]
    labels = payload["label_invariance"]
    readiness = payload["readiness"]
    return "\n".join(
        [
            "# Phase-B continuum dimension bounded measurement preflight",
            "",
            f"Status: **`{payload['status']}`**",
            "",
            f"Semantic digest: `{payload['semantic_digest_sha256']}`",
            "",
            "## Result",
            "",
            "The bounded arithmetic and source-calibration checks run successfully",
            "in the existing exact n<=5 domain. Candidate and random-control",
            "distributions normalize exactly, and every label permutation in the",
            "bounded domain passes the invariance audit.",
            "",
            "| check | result |",
            "|---|---:|",
            f"| unlabeled relations checked | `{labels['relations_checked']}` |",
            f"| relabeling permutations checked | `{labels['permutations_checked']}` |",
            f"| label-invariance failures | `{len(labels['failed_relation_ids'])}` |",
            f"| lazy transition rows checked | `{analytic['lazy_transition_rows_checked']}` |",
            f"| lazy transition row failures | `{analytic['lazy_transition_row_failures']}` |",
            f"| ordering calibration max error | `{analytic['ordering_max_abs_error']}` |",
            f"| ordering source-anchor max error | `{analytic['ordering_anchor_max_abs_error']}` |",
            f"| height d=4 control | `{analytic['height_dimension_four_recovered']}` |",
            f"| spectral d=4 control | `{analytic['spectral_dimension_four_recovered']}` |",
            "",
            "The finite n=2..5 dimension fits are diagnostics only. They do not",
            "satisfy the frozen planned sizes `[8, 12, 18, 27, 40, 60]`.",
            "",
            "## Blocking boundary",
            "",
            f"Current exact maximum: `{readiness['current_exact_max_n']}`.",
            f"Large-N sampler available: `{readiness['large_n_sampler_extension_available']}`.",
            "BDG positive-control ensemble available: "
            f"`{readiness['bdg_positive_control_ensemble_available']}`.",
            f"Production sampling authorized: `{readiness['production_sampling_authorized']}`.",
            "Production measurement pipeline validated: "
            f"`{readiness['production_measurement_pipeline_validated']}`.",
            "",
            "Therefore this preflight closes as a bounded arithmetic, schema, and",
            "invariance audit. It does not validate an end-to-end production",
            "measurement pipeline or open the production campaign. No continuum",
            "phase or dimension claim is issued.",
            "",
            "## Acceptance checks",
            "",
            "| check | passed |",
            "|---|---:|",
            *[
                f"| `{name}` | `{record['passed']}` |"
                for name, record in payload["acceptance_checks"].items()
            ],
            "",
            f"Next gate: `{payload['next_gate']}`",
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_preflight(args.root)
    if not payload["all_preflight_checks_passed"]:
        raise SystemExit("bounded continuum measurement preflight failed")
    if args.check:
        tracked = json.loads((args.root / RESULT_PATH).read_text(encoding="utf-8"))
        if tracked != payload:
            raise SystemExit("tracked continuum measurement preflight differs")
        if (args.root / REPORT_PATH).read_text(encoding="utf-8") != render_report(
            payload
        ):
            raise SystemExit("tracked continuum measurement report differs")
        return
    write_outputs(args.root, payload)


if __name__ == "__main__":
    main()
