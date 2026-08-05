"""Run one bounded, authenticated candidate-driven minor-only scout."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _canonical(value: object) -> str:
    from universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_worker_v042 import (
        canonical_sha256,
    )

    return canonical_sha256(value)


def _find_stage7_request(repository_root: Path) -> tuple[Path, dict[str, Any]]:
    candidates: list[tuple[Path, dict[str, Any]]] = []
    attempts = repository_root / "results/v0.4.2_sr2v_q5_free_auxiliary_ideal_supervised/attempts"
    for result_path in attempts.glob("*/**/result.json"):
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        details = payload.get("details")
        worker_result = details.get("worker_result") if isinstance(details, dict) else None
        if not isinstance(worker_result, dict):
            continue
        if (
            payload.get("status") == "DETERMINANTAL_SUBSET_INCONCLUSIVE"
            and worker_result.get("method") == "determinantal_cegar_v1"
            and worker_result.get("coefficient_field") == "GF(32003)"
            and worker_result.get("raw_selected_row_count") == 7
        ):
            candidates.append((result_path.parent / "request.json", payload))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one canonical stage-7 request, found {len(candidates)}")
    return candidates[0]


def run(repository_root: Path, candidate_source: int = 10) -> dict[str, Any]:
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
    emitter = worker.Emitter()
    records, loaded_terms = worker._scan_needed_records(repository_root, root, needed, emitter)
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
    if candidate_source != 10:
        raise RuntimeError("this bounded follow-up is fixed to the cost-next source row 10")
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
    result: dict[str, Any] = {
        "schema_version": "sr2v-candidate-minor-only-scout-v1",
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
        del basis
        result["expanded_minor_only"] = {
            "generator_count": len(differential_candidates),
            **{
                key: summary[key]
                for key in (
                    "basis_digest_sha256",
                    "basis_size",
                    "basis_term_count",
                    "largest_basis_polynomial_terms",
                    "is_unit_ideal",
                    "groebner_seconds",
                    "saturation_seconds",
                )
            },
        }
    result["semantic_digest_sha256"] = _canonical(result)
    return result


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
