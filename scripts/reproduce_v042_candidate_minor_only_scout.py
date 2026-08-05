"""Run one bounded, authenticated candidate-driven minor-only scout."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from universe_lab.final_theory import (
    sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042 as fixtures,
)

_STAGE7_REQUEST_FIXTURE = fixtures.STAGE7_REQUEST_FIXTURE
_STAGE7_RESULT_FIXTURE = fixtures.STAGE7_RESULT_FIXTURE
_STAGE7_REQUEST_RAW_SHA256 = fixtures.STAGE7_REQUEST_RAW_SHA256
_STAGE7_RESULT_RAW_SHA256 = fixtures.STAGE7_RESULT_RAW_SHA256


def _canonical(value: object) -> str:
    return fixtures.canonical_sha256(value)


def _is_canonical_stage7_result(payload: dict[str, Any]) -> bool:
    return fixtures.is_canonical_stage7_result(payload)


def _load_tracked_stage7_fixture(
    repository_root: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    return fixtures.load_tracked_stage7_fixture(repository_root)


def _find_stage7_request(repository_root: Path) -> tuple[Path, dict[str, Any]]:
    return fixtures.find_stage7_request(repository_root)


def _require_complete_basis(summary: Mapping[str, Any]) -> None:
    if summary["limit_exceeded"]:
        raise RuntimeError("candidate differential minor ideal exceeded the live basis cap")


def run(repository_root: Path, candidate_source: int = 10) -> dict[str, Any]:
    if candidate_source != 10:
        raise RuntimeError("this bounded follow-up is fixed to the cost-next source row 10")
    reproduction_manifest = fixtures.validate_bounded_scout_reproduction_inputs(repository_root)

    from sage.all import GF, PolynomialRing

    from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker

    request_path, prior_result = _find_stage7_request(repository_root)
    request = worker.load_verified_request(request_path)
    root = worker.load_verified_root(repository_root, request)
    if request["chart"] != "U2" or request["modulus"] != 32003:
        raise RuntimeError("the scout is bound to the canonical U2/GF(32003) request")
    chart = root["chart_generator_ids"]["charts"][request["chart"]]
    entries = chart["generator_polynomial_ids"]
    candidate = [int(value) for value in entries[candidate_source]]
    if candidate[0] != candidate_source:
        raise RuntimeError(f"candidate source index changed: {candidate!r}")
    old_rows = worker.selected_generator_rows(root, request)
    row185 = [int(value) for value in entries[185]]
    rows = [*old_rows, row185, candidate]
    if [row[0] for row in old_rows] != [8, 9, 97, 98, 327, 328, 31]:
        raise RuntimeError("stage-7 request selected rows changed")

    base_variables = list(root["ring_binding"]["polynomial_arena_variable_order"])
    ring = PolynomialRing(GF(request["modulus"]), base_variables, order=request["monomial_order"])
    field = GF(request["modulus"])
    width = len(base_variables)
    needed = {int(identifier) for _source, first, second in rows for identifier in (first, second)}
    chart_factor_id = int(request["chart_factor_polynomial_id"])
    localizer_id = int(chart["planned_Rabinowitsch_localization_polynomial_id"])
    needed.update({chart_factor_id, localizer_id})
    if needed != fixtures.CANDIDATE_ROW10_NEEDED_POLYNOMIAL_IDS:
        raise RuntimeError(f"candidate row-10 bounded subset ids changed: {sorted(needed)}")
    records, loaded_terms = fixtures.load_polynomial_subset(repository_root, root, needed)
    if (
        len(records) != len(fixtures.CANDIDATE_ROW10_NEEDED_POLYNOMIAL_IDS)
        or loaded_terms != fixtures.CANDIDATE_ROW10_LOADED_TERM_COUNT
    ):
        raise RuntimeError("candidate row-10 bounded subset record or term count changed")
    local_arena_mirror_verified = fixtures.verify_local_polynomial_arena_mirror(
        repository_root,
        root,
        records,
        loaded_terms,
        needed,
    )
    emitter = worker.Emitter()
    by_id = {
        identifier: worker._materialize_polynomial(record, ring, field, width)
        for identifier, record in records.items()
    }
    ring_generators = list(ring.gens())
    chart_factor = by_id[chart_factor_id]
    bottom_factors = [
        worker._bottom_factor_polynomial(record, ring, field, width)
        for record in request["bottom_factor_records"]
    ]
    torus_factor = ring.one()
    for generator in ring_generators[4:52]:
        torus_factor *= generator
    expected_localizer = chart_factor * torus_factor
    for factor in bottom_factors:
        expected_localizer *= factor
    if worker._unit_associate_ratio(by_id[localizer_id], expected_localizer) is None:
        raise RuntimeError("root-bound Rabinowitsch localizer reconstruction failed")

    pairs = [(by_id[first], by_id[second]) for _source, first, second in rows]
    representatives, relations = worker._deduplicate_ground_unit_pairs(rows, pairs)
    candidates, discarded, resource_limit = worker._determinantal_minor_candidates(
        rows,
        pairs,
        representatives,
        max_generated_minor_terms=int(request["determinantal_policy"]["max_generated_minor_terms"]),
    )
    old_pairs = pairs[: len(old_rows)]
    old_representatives, old_relations = worker._deduplicate_ground_unit_pairs(old_rows, old_pairs)
    old_candidates, _old_discarded, old_limit = worker._determinantal_minor_candidates(
        old_rows,
        old_pairs,
        old_representatives,
        max_generated_minor_terms=40_000,
    )
    if old_limit is not None or len(old_candidates) < 2:
        raise RuntimeError("the authenticated stage-7 two-minor prefix changed")
    source_to_index = {int(row[0]): index for index, row in enumerate(rows)}

    def selected_pair(left_source: int, right_source: int) -> tuple[Any, dict[str, Any]]:
        left_index = source_to_index[left_source]
        right_index = source_to_index[right_source]
        left_a, left_b = pairs[left_index]
        right_a, right_b = pairs[right_index]
        minor = left_a * right_b - right_a * left_b
        if not minor:
            raise RuntimeError(f"selected pair {left_source},{right_source} is zero")
        cost_upper_bound = int(left_a.number_of_terms()) * int(right_b.number_of_terms()) + int(
            right_a.number_of_terms()
        ) * int(left_b.number_of_terms())
        record: dict[str, Any] = {
            "left_row": rows[left_index],
            "right_row": rows[right_index],
            "cost_upper_bound": cost_upper_bound,
            "minor": worker._polynomial_digest_record(minor),
        }
        record["candidate_sha256"] = _canonical(record)
        return minor, record

    differential_candidates = [
        *old_candidates[:2],
        selected_pair(8, 185),
        selected_pair(97, 185),
        selected_pair(31, 10),
    ]
    differential_cost_upper_bound = sum(
        int(record["cost_upper_bound"]) for _minor, record in differential_candidates
    )
    if differential_cost_upper_bound > 40_000:
        raise RuntimeError(
            f"selected differential minor subset exceeds cap: {differential_cost_upper_bound}"
        )
    certificate_core: dict[str, Any] = {
        "schema_version": "sr2v-candidate-minor-only-certificate-core-v1",
        "chart": "U2",
        "coefficient_field": "GF(32003)",
        "candidate_source": candidate_source,
        "candidate_row": candidate,
        "row185": row185,
        "selected_old_source_rows": [row[0] for row in old_rows],
        "root_semantic_digest_sha256": root["semantic_digest_sha256"],
        "prior_attempt_result_sha256": _canonical(prior_result),
        "prior_request_sha256": _canonical(request),
        "loaded_polynomial_count": len(records),
        "loaded_terms": loaded_terms,
        "effective_rows": [rows[index] for index in representatives],
        "unit_associate_relations": relations,
        "old_unit_associate_relations": old_relations,
        "discarded_minors": discarded,
        "minor_candidates": [record for _minor, record in candidates],
        "minor_resource_limit": resource_limit,
        "differential_minor_candidates": [record for _minor, record in differential_candidates],
        "differential_selection": {
            "policy": "OLD_MINOR_PREFIX_2_PLUS_8_185_PLUS_97_185_PLUS_31_10",
            "projected_cost_upper_bound": differential_cost_upper_bound,
            "cap": 40_000,
            "subset_safe": True,
        },
    }
    runtime_observation: dict[str, Any] = {}
    if resource_limit is None or differential_candidates != candidates:
        factors = [
            ("chart", chart_factor),
            *[
                (str(record["factor_id"]), factor)
                for record, factor in zip(
                    request["bottom_factor_records"], bottom_factors, strict=True
                )
            ],
            ("torus_product_s0_through_s47", torus_factor),
        ]
        basis, summary = worker._localized_standard_basis(
            algorithm=str(request["groebner_algorithm"]),
            emitter=emitter,
            factors=factors,
            generators=[minor for minor, _record in differential_candidates],
            max_live_basis_terms=int(request["max_live_basis_terms"]),
            phase="CANDIDATE_ROW10_DIFFERENTIAL_MINOR_ONLY",
            ring=ring,
        )
        _require_complete_basis(summary)
        del basis
        certificate_core["expanded_minor_only"] = {
            "generator_count": len(differential_candidates),
            **fixtures.deterministic_basis_summary(summary),
        }
        runtime_observation["expanded_minor_only"] = fixtures.runtime_basis_observation(summary)
    certificate_core = fixtures.bind_certificate_core(certificate_core)
    fixtures.verify_bound_certificate_core(certificate_core)
    expectations = fixtures.verify_scout_certificate_core_expectation(
        repository_root,
        reproduction_manifest,
        "candidate_minor_only",
        certificate_core["certificate_core_digest_sha256"],
    )
    return {
        "schema_version": "sr2v-candidate-minor-only-scout-v2",
        "certificate_core": certificate_core,
        "certificate_core_digest_sha256": certificate_core["certificate_core_digest_sha256"],
        "runtime_observation": {
            "local_full_arena_mirror_verified": local_arena_mirror_verified,
            **runtime_observation,
        },
        "reproduction_contract": {
            "certificate_core_expectation_status": expectations["status"],
            "expectations_semantic_digest_sha256": expectations["semantic_digest_sha256"],
            "input_manifest_semantic_digest_sha256": reproduction_manifest[
                "semantic_digest_sha256"
            ],
        },
        "legacy_observation": {
            "legacy_full_result_semantic_digest_sha256": (
                "02f2ab4fbb53e8c91b5e67eb686a35543e61a51db2f912191f7621a002e4f947"
            ),
            "legacy_observation_status": fixtures.LEGACY_OBSERVATION_STATUS,
        },
    }


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    source = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(
        json.dumps(
            run(root.resolve(), source),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
