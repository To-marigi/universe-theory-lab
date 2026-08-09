"""Certify the coverage gap beyond the terminal v0.4.2 955 mixed ansatz.

The source-native slack inventory starts with 131 general ``2 x 2`` quotient
operators (524 scalar entries) and 48 reachable-state slack coordinates.  Its
24 timid definitions are monic triangular equations in 24 distinct operator
matrices, so they eliminate 96 scalar entries exactly and leave a 476-coordinate
effective chart.

Inside that chart the mixed ansatz is the locus where every source operator has
diagonal ``(p_e, 1)``.  For the 107 independent non-timid matrices this gives
214 direct coordinate-linear equations of exact rank 214.  The 24 recursively
defined timid matrices contribute another 48 derived diagonal obligations.
Thus the terminal mixed proof omits at least 214 independent ambient diagonal
directions and cannot be promoted to the unrestricted source-native profile.

This module also computes substitution-degree ceilings through the acyclic timid
recurrence.  It does not expand scalar polynomials: state vectors reach degree
ceiling 7, timid matrices 8, raw CPOBC equations 5 and strong-GC basis equations
11.  These are exact syntactic upper bounds for planning a streamed expansion,
not claims that cancellation-free scalar entries of those degrees occur.

No Groebner basis, saturation, finite-field, numerical, Sage or scalar-polynomial
expansion run is performed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

SLACK_INVENTORY_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
MIXED_CLOSURE_PATH = "results/v0.4.2_955_mixed_branch_closure.json"
RESULT_PATH = "results/v0.4.2_955_slack_coverage_gap.json"

SCHEMA = "final-theory-v042-955-slack-coverage-gap-v1"
VERDICT = "V042_955_SLACK_COVERAGE_GAP_214_NORMALS_DEGREE11_CEILING_CERTIFIED"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _source_stage(source_id: str) -> int:
    if not source_id.startswith("p") or "-" not in source_id:
        raise AssertionError(f"unexpected source id: {source_id}")
    return int(source_id[1 : source_id.index("-")])


def _operator_from_symbol(symbol: str) -> str:
    if not symbol.startswith("A:"):
        raise AssertionError(f"unexpected source operator symbol: {symbol}")
    return symbol[2:]


def _degree_histogram(values: list[int]) -> dict[str, int]:
    return {str(degree): count for degree, count in sorted(Counter(values).items())}


def _equation_degree_profile(
    records: list[dict[str, Any]],
    matrix_degree: dict[str, int],
    identifier_keys: tuple[str, ...],
) -> dict[str, Any]:
    ceilings: list[int] = []
    selected_maximum: list[dict[str, Any]] = []
    maximum = 0
    for record in records:
        left = sum(
            matrix_degree[_operator_from_symbol(symbol)] for symbol in record["lhs_source_word"]
        )
        right = sum(
            matrix_degree[_operator_from_symbol(symbol)] for symbol in record["rhs_source_word"]
        )
        ceiling = max(left, right)
        ceilings.append(ceiling)
        identifier = {key: record[key] for key in identifier_keys if key in record}
        if ceiling > maximum:
            maximum = ceiling
            selected_maximum = [{**identifier, "degree_ceiling": ceiling}]
        elif ceiling == maximum:
            selected_maximum.append({**identifier, "degree_ceiling": ceiling})
    return {
        "equation_blocks": len(records),
        "degree_ceiling_histogram": _degree_histogram(ceilings),
        "maximum_degree_ceiling": maximum,
        "maximum_degree_records": selected_maximum,
    }


def compile_slack_coverage_gap_v042(root: Path) -> dict[str, Any]:
    """Compile the exact mixed-ansatz coverage gap and degree-ceiling preflight."""

    paths = {
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        MIXED_CLOSURE_PATH: root / MIXED_CLOSURE_PATH,
    }
    slack = _load(paths[SLACK_INVENTORY_PATH])
    mixed = _load(paths[MIXED_MANIFEST_PATH])
    closure = _load(paths[MIXED_CLOSURE_PATH])
    expected = {
        SLACK_INVENTORY_PATH: (
            "final-theory-v042-955-source-native-slack-compiler-v1",
            "V042_955_SOURCE_NATIVE_SLACK_INVENTORY_READY_NO_SOLVER_RUN",
        ),
        MIXED_MANIFEST_PATH: (
            "final-theory-v042-955-mixed-source-native-manifest-v1",
            "V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN",
        ),
        MIXED_CLOSURE_PATH: (
            "final-theory-v042-955-mixed-branch-closure-v1",
            "V042_955_MIXED_ANSATZ_17D_PURE_UPPER_COMMUTATIVE_TERMINAL_CERTIFIED",
        ),
    }
    for name, artifact in (
        (SLACK_INVENTORY_PATH, slack),
        (MIXED_MANIFEST_PATH, mixed),
        (MIXED_CLOSURE_PATH, closure),
    ):
        schema, verdict = expected[name]
        if artifact.get("schema_version") != schema or artifact.get("verdict") != verdict:
            raise AssertionError(f"unexpected predecessor schema or verdict: {name}")
        if artifact.get("semantic_digest_sha256") != _semantic_digest(artifact):
            raise AssertionError(f"predecessor semantic digest mismatch: {name}")

    orbit_inventory = slack["operator_namespace"]["orbit_inventory"]
    if len(orbit_inventory) != 131:
        raise AssertionError("the source-native quotient orbit count changed")
    representative_to_orbit = {
        str(record["representative_occurrence_id"]): str(record["orbit_id"])
        for record in orbit_inventory
    }
    if len(representative_to_orbit) != 131:
        raise AssertionError("operator representatives must be unique")
    orbit_to_representative = {
        orbit: representative for representative, orbit in representative_to_orbit.items()
    }

    recurrences = slack["timid_slack_recurrences"]
    if len(recurrences) != 24:
        raise AssertionError("the timid source recurrence count changed")
    timid_to_source = {
        str(record["timid_orbit_representative"]): str(record["source_id"])
        for record in recurrences
    }
    if len(timid_to_source) != 24 or not set(timid_to_source) <= set(representative_to_orbit):
        raise AssertionError("timid representatives do not form 24 quotient matrices")
    independent_representatives = sorted(set(representative_to_orbit) - set(timid_to_source))
    if len(independent_representatives) != 107:
        raise AssertionError("expected 107 independent non-timid quotient matrices")

    mixed_orbits = {
        str(name)[2:] for name in mixed["variables"]["names"] if str(name).startswith("x:")
    }
    if mixed_orbits != set(orbit_to_representative):
        raise AssertionError("the mixed and unrestricted charts index different quotient orbits")
    if mixed_orbits != {
        str(name)[2:] for name in mixed["variables"]["names"] if str(name).startswith("y:")
    }:
        raise AssertionError("the mixed x/y orbit sets differ")

    diagonal_character = mixed["variables"]["CSG_diagonal_character"]
    direct_diagonal_constraints: list[dict[str, Any]] = []
    for representative in independent_representatives:
        orbit = representative_to_orbit[representative]
        direct_diagonal_constraints.extend(
            [
                {
                    "orbit_id": orbit,
                    "representative_occurrence_id": representative,
                    "coordinate": "00",
                    "equation": f"A:{representative}:00-({diagonal_character[orbit]})=0",
                },
                {
                    "orbit_id": orbit,
                    "representative_occurrence_id": representative,
                    "coordinate": "11",
                    "equation": f"A:{representative}:11-1=0",
                },
            ]
        )
    if len(direct_diagonal_constraints) != 214:
        raise AssertionError("the direct mixed diagonal restriction count changed")

    recurrence_by_timid = {
        str(record["timid_orbit_representative"]): record for record in recurrences
    }
    derived_diagonal_obligations = [
        {
            "source_id": timid_to_source[representative],
            "orbit_id": representative_to_orbit[representative],
            "representative_occurrence_id": representative,
            "target_diagonal": [
                str(diagonal_character[representative_to_orbit[representative]]),
                "1",
            ],
            "definition_lhs": recurrence_by_timid[representative]["timid_definition"]["lhs"],
            "scalar_obligations": 2,
        }
        for representative in sorted(timid_to_source)
    ]
    if len(derived_diagonal_obligations) != 24:
        raise AssertionError("the derived timid diagonal obligation count changed")

    full_coordinates = slack["search_ready_inventory"]["base_scalar_unknowns"]
    if full_coordinates != {
        "ON_quotient_operator_matrix_entries": 524,
        "slack_coordinates": 48,
        "total": 572,
        "excluded": [
            "fixed initial vector Omega",
            "derived reachable-state symbols v:c",
            "localisation inverse auxiliaries",
        ],
    }:
        raise AssertionError("the 572-coordinate source-native namespace changed")
    triangular_scalar_pivots = 24 * 4
    effective_coordinates = 572 - triangular_scalar_pivots
    after_direct_diagonal_restrictions = effective_coordinates - len(direct_diagonal_constraints)
    if effective_coordinates != 476 or after_direct_diagonal_restrictions != 262:
        raise AssertionError("the 572 -> 476 -> 262 structural count changed")
    if mixed["variables"]["total"] != after_direct_diagonal_restrictions:
        raise AssertionError("the mixed ambient coordinate count no longer matches the chart cut")

    # Propagate degree ceilings through the triangular timid recurrence.  Every
    # independent matrix entry has degree one.  A state word has ceiling equal
    # to the sum of its matrix ceilings, and T_c has ceiling max(1, 1+deg(v_c)).
    canonical_paths = {
        str(record["source_id"]): [
            _operator_from_symbol(symbol) for symbol in record["operator_word_later_on_left"]
        ]
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    matrix_degree: dict[str, int] = {
        representative: 1 for representative in independent_representatives
    }
    state_degree: dict[str, int] = {}
    pending = set(timid_to_source)
    dependency_records: list[dict[str, Any]] = []
    while pending:
        progress = False
        for representative in sorted(pending, key=lambda value: timid_to_source[value]):
            source_id = timid_to_source[representative]
            word = canonical_paths[source_id]
            if not all(operator in matrix_degree for operator in word):
                continue
            state_ceiling = sum(matrix_degree[operator] for operator in word)
            timid_ceiling = max(1, 1 + state_ceiling)
            state_degree[source_id] = state_ceiling
            matrix_degree[representative] = timid_ceiling
            dependency_records.append(
                {
                    "source_id": source_id,
                    "source_stage": _source_stage(source_id),
                    "timid_representative": representative,
                    "state_word": [f"A:{operator}" for operator in word],
                    "state_degree_ceiling": state_ceiling,
                    "timid_matrix_degree_ceiling": timid_ceiling,
                    "timid_dependencies": [
                        operator for operator in word if operator in timid_to_source
                    ],
                }
            )
            pending.remove(representative)
            progress = True
        if not progress:
            raise AssertionError("the timid recurrence is cyclic or has an unresolved operator")
    if len(state_degree) != 24 or len(matrix_degree) != 131:
        raise AssertionError("degree propagation did not cover the source recurrence")

    cpobc_degree = _equation_degree_profile(
        slack["raw_source_system"]["CPOBC_equations"],
        matrix_degree,
        ("relation_id", "equation_id"),
    )
    gc_degree = _equation_degree_profile(
        slack["raw_source_system"]["strong_GC_basis"],
        matrix_degree,
        ("relation_id", "endpoint_causet_id"),
    )
    if cpobc_degree["maximum_degree_ceiling"] != 5:
        raise AssertionError("the CPOBC substitution degree ceiling changed")
    if gc_degree["maximum_degree_ceiling"] != 11:
        raise AssertionError("the strong-GC substitution degree ceiling changed")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "structural_coverage_gap_field": "characteristic-zero field",
            "bound_mixed_terminal_predecessor_field": "QQ",
            "field_scope_note": (
                "The coordinate/rank coverage gap is structural in characteristic zero; "
                "the imported mixed terminal verdict is quoted only over QQ."
            ),
            "identification_mode": "ON_QUOTIENT",
            "locus": "nonsingular source-native slack chart",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
            MIXED_CLOSURE_PATH: closure["semantic_digest_sha256"],
        },
        "effective_slack_chart": {
            "general_quotient_operator_matrices": 131,
            "general_operator_scalar_entries": 524,
            "reachable_state_slack_coordinates": 48,
            "coordinates_before_timid_elimination": 572,
            "timid_matrix_definitions": 24,
            "monic_triangular_scalar_pivots": triangular_scalar_pivots,
            "independent_non_timid_matrices": len(independent_representatives),
            "effective_coordinates_after_timid_elimination": effective_coordinates,
            "triangular_elimination_is_exact": True,
        },
        "dimension_two_annihilator_parameterisation": {
            "statement": (
                "For v!=0, every 2x2 residual R with Rv=0 has a unique expression "
                "R=u*(Jv)^T, J=[[0,-1],[1,0]]."
            ),
            "cover": ["v0!=0", "v1!=0"],
            "orthogonality_identity": "(Jv)^T*v=-v1*v0+v0*v1=0",
            "row_patch_formulas": {
                "v0!=0": "lambda=r1/v0 and r0=-r1*v1/v0",
                "v1!=0": "lambda=-r0/v1 and r1=-r0*v0/v1",
            },
            "reachable_states_nonzero_reason": (
                "Omega!=0 and every source transition on a canonical path is nonsingular."
            ),
            "slack_chart_complete_for_reachable_state_MSR_on_nonsingular_locus": True,
        },
        "mixed_ansatz_as_diagonal_restriction_locus": {
            "all_131_orbits_match": True,
            "independent_non_timid_matrices": len(independent_representatives),
            "direct_coordinate_linear_diagonal_constraints": len(direct_diagonal_constraints),
            "direct_linear_rank": len(direct_diagonal_constraints),
            "direct_constraints": direct_diagonal_constraints,
            "coordinates_after_direct_constraints": after_direct_diagonal_restrictions,
            "mixed_manifest_xy_coordinates": mixed["variables"]["total"],
            "derived_timid_matrices": len(derived_diagonal_obligations),
            "derived_timid_diagonal_obligations": 2 * len(derived_diagonal_obligations),
            "derived_obligation_records": derived_diagonal_obligations,
            "derived_obligation_rank_claimed": False,
            "structural_correspondence": (
                "The 214 free off-diagonal entries of the 107 independent matrices plus "
                "48 slack coordinates give the mixed manifest's 262-coordinate ambient "
                "namespace; the 48 derived timid diagonal obligations correspond to imposing "
                "the mixed diagonal form on the 24 eliminated timid matrices."
            ),
            "exact_locus_equivalence_on_nonsingular_reachable_MSR_chart": True,
        },
        "certified_coverage_gap": {
            "direct_independent_diagonal_normal_directions_omitted_by_mixed_ansatz": 214,
            "additional_derived_timid_diagonal_obligations": 48,
            "rank_of_additional_derived_obligations": "NOT_MEASURED",
            "mixed_ansatz_is_positive_codimension_closed_locus": True,
            "mixed_terminal_cannot_be_promoted_by_density": True,
            "mixed_terminal_verdict": closure["verdict"],
            "unrestricted_source_native_955_status": "OPEN",
        },
        "substitution_degree_ceiling": {
            "method": (
                "Acyclic syntactic degree propagation after exact timid elimination; "
                "ceilings may overestimate scalar degrees when entries cancel."
            ),
            "independent_matrix_entry_degree": 1,
            "state_vector_by_source": dict(sorted(state_degree.items())),
            "state_vector_histogram": _degree_histogram(list(state_degree.values())),
            "maximum_state_vector_degree_ceiling": max(state_degree.values()),
            "timid_matrix_by_source": {
                timid_to_source[representative]: matrix_degree[representative]
                for representative in sorted(timid_to_source)
            },
            "timid_matrix_histogram": _degree_histogram(
                [matrix_degree[representative] for representative in timid_to_source]
            ),
            "maximum_timid_matrix_degree_ceiling": max(
                matrix_degree[representative] for representative in timid_to_source
            ),
            "dependency_records": dependency_records,
            "raw_CPOBC_after_timid_substitution": cpobc_degree,
            "strong_GC_after_timid_substitution": gc_degree,
            "global_maximum_degree_ceiling": max(
                cpobc_degree["maximum_degree_ceiling"],
                gc_degree["maximum_degree_ceiling"],
                max(matrix_degree[representative] for representative in timid_to_source),
            ),
            "scalar_polynomial_expansion_performed": False,
            "expanded_term_count": None,
        },
        "execution_decision": {
            "full_scalar_expansion_authorised": False,
            "heavy_solver_authorised": False,
            "reason": (
                "The effective coordinate count and degree ceiling are now certified, but an "
                "exact streamed term-count preflight and a versioned memory/time budget are "
                "still missing."
            ),
            "next_gate": (
                "STREAMED_TERM_COUNT_ONLY_PREFLIGHT_FOR_THE_476_COORDINATE_TIMID_ELIMINATED_"
                "SYSTEM_THEN_VERSIONED_EXPANSION_BUDGET"
            ),
        },
        "solver_status": {
            "scalar_polynomial_expansion_runs": 0,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "The 214 count is an exact rank for direct independent diagonal coordinate forms.",
            "No rank is claimed for the 48 derived timid diagonal obligations.",
            (
                "Degree values are syntactic substitution ceilings, not cancellation-free "
                "exact degrees."
            ),
            "No scalar-polynomial term expansion or solver campaign was run.",
            "The imported mixed terminal verdict is limited to its predecessor field QQ.",
            "The unrestricted source-native 955 profile remains open.",
        ],
        "mixed_ansatz_search_terminal": True,
        "unrestricted_source_native_955_search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_coverage_gap_v042(root: Path) -> Path:
    payload = compile_slack_coverage_gap_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_coverage_gap_v042(repository_root))
