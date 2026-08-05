"""Run the bounded, authenticated row-185 normal-form scout in Sage.

The scout deliberately reuses the canonical stage-7 CEGAR request and does
not mutate any frozen artifact.  It recomputes the stage-7 localized entry and
minor bases, then records normal forms for row 185 and its pair minors.  The
output is a compact canonical JSON result suitable for a report appendix.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


def _canonical(value: object) -> str:
    from universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_worker_v042 import (
        canonical_sha256,
    )

    return canonical_sha256(value)


def _normal_form_record(polynomial: Any, basis: Any) -> dict[str, Any]:
    from universe_lab.final_theory.sr2v_q5_free_auxiliary_ideal_worker_v042 import (
        _polynomial_digest_record,
    )

    remainder = polynomial.reduce(list(basis))
    record = _polynomial_digest_record(remainder)
    record["is_zero"] = not bool(remainder)
    return record


def _find_stage7_request(repository_root: Path) -> tuple[Path, dict[str, Any]]:
    """Find the unique recorded GF stage-7 CEGAR attempt."""

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
            request_path = result_path.parent / "request.json"
            candidates.append((request_path, payload))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one canonical stage-7 CEGAR attempt, found {len(candidates)}")
    return candidates[0]


def run(repository_root: Path) -> dict[str, Any]:
    from sage.all import GF, PolynomialRing

    from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker

    request_path, prior_result = _find_stage7_request(repository_root)
    request = worker.load_verified_request(request_path)
    root = worker.load_verified_root(repository_root, request)
    if request["chart"] != "U2" or request["modulus"] != 32003:
        raise RuntimeError("the scout is bound to the canonical U2/GF(32003) stage-7 request")

    chart = root["chart_generator_ids"]["charts"][request["chart"]]
    raw_entries = chart["generator_polynomial_ids"]
    row185 = [int(value) for value in raw_entries[185]]
    if row185[0] != 185 or row185[1:] != [545, 546]:
        raise RuntimeError(f"row 185 changed in the frozen root: {row185!r}")
    old_rows = worker.selected_generator_rows(root, request)
    if len(old_rows) != 7 or [row[0] for row in old_rows] != [8, 9, 97, 98, 327, 328, 31]:
        raise RuntimeError("stage-7 request selected rows changed")
    rows = [*old_rows, row185]

    base_variables = list(root["ring_binding"]["polynomial_arena_variable_order"])
    ring = PolynomialRing(GF(request["modulus"]), base_variables, order=request["monomial_order"])
    ring_generators = list(ring.gens())
    needed = {int(identifier) for _source, first, second in rows for identifier in (first, second)}
    chart_factor_id = int(request["chart_factor_polynomial_id"])
    localizer_id = int(chart["planned_Rabinowitsch_localization_polynomial_id"])
    needed.update({chart_factor_id, localizer_id})
    emitter = worker.Emitter()
    records, loaded_terms = worker._scan_needed_records(repository_root, root, needed, emitter)
    field = GF(request["modulus"])
    width = len(base_variables)
    by_id = {
        identifier: worker._materialize_polynomial(record, ring, field, width)
        for identifier, record in records.items()
    }
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
    localizer_ratio = worker._unit_associate_ratio(by_id[localizer_id], expected_localizer)
    if localizer_ratio is None:
        raise RuntimeError("root-bound Rabinowitsch localizer reconstruction failed")

    pairs = [(by_id[first], by_id[second]) for _source, first, second in rows]
    old_pairs = pairs[: len(old_rows)]
    old_representatives, old_relations = worker._deduplicate_ground_unit_pairs(old_rows, old_pairs)
    all_representatives, all_relations = worker._deduplicate_ground_unit_pairs(rows, pairs)
    if all_representatives[-1] != len(rows) - 1:
        raise RuntimeError("row 185 was unexpectedly a ground-unit associate")

    factors = [
        ("chart", chart_factor),
        *[
            (str(record["factor_id"]), factor)
            for record, factor in zip(request["bottom_factor_records"], bottom_factors, strict=True)
        ],
        ("torus_product_s0_through_s47", torus_factor),
    ]
    max_basis_terms = int(request["max_live_basis_terms"])
    algorithm = str(request["groebner_algorithm"])
    started = time.monotonic()
    old_entry_generators = [
        component for index in old_representatives for component in old_pairs[index] if component
    ]
    old_entry_basis, old_entry_summary = worker._localized_standard_basis(
        algorithm=algorithm,
        emitter=emitter,
        factors=factors,
        generators=old_entry_generators,
        max_live_basis_terms=max_basis_terms,
        phase="ROW185_OLD_ENTRY_IDEAL",
        ring=ring,
    )
    if old_entry_summary["limit_exceeded"]:
        raise RuntimeError("stage-7 entry basis exceeded the audited live basis cap")

    old_candidates, discarded, resource_limit = worker._determinantal_minor_candidates(
        old_rows,
        old_pairs,
        old_representatives,
        max_generated_minor_terms=int(request["determinantal_policy"]["max_generated_minor_terms"]),
    )
    if resource_limit is not None:
        raise RuntimeError(f"stage-7 minor inventory unexpectedly hit a cap: {resource_limit}")

    new_entry_records = {
        "A": _normal_form_record(pairs[-1][0], old_entry_basis),
        "B": _normal_form_record(pairs[-1][1], old_entry_basis),
    }
    new_minor_records: list[dict[str, Any]] = []
    for old_index in old_representatives:
        old_a, old_b = old_pairs[old_index]
        new_a, new_b = pairs[-1]
        minor = old_a * new_b - new_a * old_b
        record: dict[str, Any] = {
            "left_row": old_rows[old_index],
            "right_row": row185,
            "minor": worker._polynomial_digest_record(minor),
            "old_entry_normal_form": _normal_form_record(minor, old_entry_basis),
        }
        new_minor_records.append(record)

    prefix_records: list[dict[str, Any]] = []
    for prefix_size in (1, 2, len(old_candidates)):
        selected_minors = [minor for minor, _record in old_candidates[:prefix_size]]
        minor_basis, minor_summary = worker._localized_standard_basis(
            algorithm=algorithm,
            emitter=emitter,
            factors=factors,
            generators=selected_minors,
            max_live_basis_terms=max_basis_terms,
            phase=f"ROW185_OLD_MINOR_PREFIX_{prefix_size}",
            ring=ring,
        )
        if minor_summary["limit_exceeded"]:
            raise RuntimeError(f"old minor prefix {prefix_size} exceeded the live basis cap")
        for record in new_minor_records:
            left = next(
                index for index in old_representatives if old_rows[index] == record["left_row"]
            )
            old_a, old_b = old_pairs[left]
            new_a, new_b = pairs[-1]
            candidate_minor = old_a * new_b - new_a * old_b
            record[f"prefix_{prefix_size}_normal_form"] = _normal_form_record(
                candidate_minor, minor_basis
            )
        prefix_records.append(
            {
                "prefix_size": prefix_size,
                "basis": {
                    key: minor_summary[key]
                    for key in (
                        "basis_digest_sha256",
                        "basis_size",
                        "basis_term_count",
                        "largest_basis_polynomial_terms",
                        "is_unit_ideal",
                    )
                },
            }
        )

    new_pair_minors: list[Any] = []
    for old_index in old_representatives:
        old_a, old_b = old_pairs[old_index]
        new_a, new_b = pairs[-1]
        minor = old_a * new_b - new_a * old_b
        if minor:
            new_pair_minors.append(minor)
    expanded_minor_generators = [minor for minor, _record in old_candidates] + new_pair_minors
    expanded_minor_basis, expanded_minor_summary = worker._localized_standard_basis(
        algorithm=algorithm,
        emitter=emitter,
        factors=factors,
        generators=expanded_minor_generators,
        max_live_basis_terms=max_basis_terms,
        phase="ROW185_EXPANDED_MINOR_ONLY",
        ring=ring,
    )
    if expanded_minor_summary["limit_exceeded"]:
        raise RuntimeError("row-185 expanded minor ideal exceeded the live basis cap")

    result: dict[str, Any] = {
        "schema_version": "sr2v-row185-normal-form-scout-v1",
        "chart": "U2",
        "coefficient_field": "GF(32003)",
        "root_semantic_digest_sha256": root["semantic_digest_sha256"],
        "prior_attempt_result_sha256": _canonical(prior_result),
        "prior_request_sha256": _canonical(request),
        "selected_old_source_rows": [row[0] for row in old_rows],
        "row185": row185,
        "row185_component_polynomial_ids": row185[1:],
        "row185_component_digests": {
            "A": worker._polynomial_digest_record(pairs[-1][0]),
            "B": worker._polynomial_digest_record(pairs[-1][1]),
        },
        "loaded_polynomial_count": len(records),
        "loaded_terms": loaded_terms,
        "old_unit_associate_relations": old_relations,
        "all_unit_associate_relations": all_relations,
        "old_entry_basis": {
            key: old_entry_summary[key]
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
        "row185_entry_normal_forms": new_entry_records,
        "old_minor_inventory": {
            "candidate_count": len(old_candidates),
            "discarded_count": len(discarded),
            "candidate_digests": [record["candidate_sha256"] for _minor, record in old_candidates],
        },
        "row185_pair_minor_normal_forms": new_minor_records,
        "old_minor_prefix_bases": prefix_records,
        "expanded_minor_only": {
            "generator_count": len(expanded_minor_generators),
            "new_nonzero_minor_count": len(new_pair_minors),
            "basis": {
                key: expanded_minor_summary[key]
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
        },
        "elapsed_seconds": time.monotonic() - started,
    }
    result["semantic_digest_sha256"] = _canonical(result)
    return result


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print(json.dumps(run(root.resolve()), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
