"""Exact source-native mixed-ansatz manifest for the 955 profile.

This module expands the raw source equations, without Eq. (107), Eq. (108),
Eq. (112), a Q-only reconstruction, or a solver call.  Every ON quotient
orbit receives the mixed matrix

    A_e = [[p_e, x_e], [y_e, 1]],

where ``p_e`` is the exact ``t_j=1`` CSG character and ``Omega=e_1``.  The
output is a sparse QQ polynomial *manifest*: it is not a witness, a Gröbner
calculation, or a chart-cover theorem.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
EQ113_BRANCH_PATH = "results/v0.3.4_source_branches.json"
WEAK_D2_PATH = "results/v0.4_weak_d2_classification.json"
EQ120_PATH = "results/v0.4.2_eq120_source_provenance.json"

RESULT_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
SCHEMA = "final-theory-v042-955-mixed-source-native-manifest-v1"
VERDICT = "V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN"

Monomial = tuple[int, ...]
Polynomial = dict[Monomial, Fraction]
Matrix = tuple[tuple[Polynomial, Polynomial], tuple[Polynomial, Polynomial]]
Vector = tuple[Polynomial, Polynomial]

MAX_ENTRY_TERMS = 100_000
MAX_TOTAL_TERMS = 2_000_000


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"JSON object required: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_json(
            {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
        ).encode("utf-8")
    ).hexdigest()


def _constant(value: Fraction | int) -> Polynomial:
    scalar = Fraction(value)
    return {} if scalar == 0 else {(): scalar}


def _variable(index: int) -> Polynomial:
    return {(index,): Fraction(1)}


def _add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        updated = result.get(monomial, Fraction(0)) + coefficient
        if updated:
            result[monomial] = updated
        else:
            result.pop(monomial, None)
    return result


def _negate(value: Polynomial) -> Polynomial:
    return {monomial: -coefficient for monomial, coefficient in value.items()}


def _multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(sorted(left_monomial + right_monomial))
            updated = result.get(monomial, Fraction(0)) + left_coefficient * right_coefficient
            if updated:
                result[monomial] = updated
            else:
                result.pop(monomial, None)
    if len(result) > MAX_ENTRY_TERMS:
        raise RuntimeError("sparse polynomial entry exceeds manifest term limit")
    return result


def _matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(_add(left[row][column], right[row][column]) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_negate(value: Matrix) -> Matrix:
    return tuple(tuple(_negate(value[row][column]) for column in range(2)) for row in range(2))  # type: ignore[return-value]


def _matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return _matrix_add(left, _matrix_negate(right))


def _matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(
            _add(
                _multiply(left[row][0], right[0][column]),
                _multiply(left[row][1], right[1][column]),
            )
            for column in range(2)
        )
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
    return (
        _add(_multiply(matrix[0][0], vector[0]), _multiply(matrix[0][1], vector[1])),
        _add(_multiply(matrix[1][0], vector[0]), _multiply(matrix[1][1], vector[1])),
    )


def _identity() -> Matrix:
    return ((_constant(1), _constant(0)), (_constant(0), _constant(1)))


def _relation_code(rows: tuple[int, ...]) -> int:
    return sum(row << (index * len(rows)) for index, row in enumerate(rows))


def _csg_probability(stage: int, rows: list[int], precursor_code: int) -> Fraction:
    """Return the exact CSG ``t_j=1`` transition character."""

    width = precursor_code.bit_count()
    maximal_count = sum(
        1
        for vertex, upper_vertices in enumerate(rows)
        if precursor_code & (1 << vertex) and not upper_vertices & precursor_code
    )
    return Fraction(2 ** (width - maximal_count), 2**stage)


def _serialize_polynomial(value: Polynomial, names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": str(coefficient),
            "monomial": [
                {"variable": names[index], "exponent": monomial.count(index)}
                for index in sorted(set(monomial))
            ],
        }
        for monomial, coefficient in sorted(value.items())
    ]


def _serialize_matrix(value: Matrix, names: list[str]) -> dict[str, list[dict[str, Any]]]:
    return {
        f"{row}{column}": _serialize_polynomial(value[row][column], names)
        for row in range(2)
        for column in range(2)
    }


def _serialize_vector(value: Vector, names: list[str]) -> dict[str, list[dict[str, Any]]]:
    return {str(index): _serialize_polynomial(value[index], names) for index in range(2)}


def _term_census(values: list[Polynomial]) -> dict[str, int]:
    terms = [len(value) for value in values]
    degrees = [len(monomial) for value in values for monomial in value]
    return {
        "entries": len(values),
        "nonzero_entries": sum(bool(value) for value in values),
        "total_terms": sum(terms),
        "maximum_terms_in_one_entry": max(terms, default=0),
        "maximum_total_degree": max(degrees, default=0),
    }


def _residual_digest(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def _supplemental_ledger(
    eq112: dict[str, Any], branches: dict[str, Any], weak: dict[str, Any]
) -> dict[str, Any]:
    path_branches = eq112.get("path_consistency_branches", {})
    if not isinstance(path_branches, dict) or branches.get("branches_mixed") is not False:
        raise AssertionError("Eq.(113) branch artifacts are malformed or merged")
    if (
        len(path_branches.get("EQ113_QN_BRANCH", [])) != 25
        or len(path_branches.get("EQ113_QN_PLUS_1_BRANCH", [])) != 25
    ):
        raise AssertionError("Eq.(113) 25/25 census changed")
    if (
        branches.get("equations", {}).get("DERIVED_APPENDIX_QN_BRANCH") != 25
        or branches.get("equations", {}).get("LITERAL_PRINTED_QN_PLUS_1_BRANCH") != 25
    ):
        raise AssertionError("Eq.(113) authoritative branch count changed")
    eq139 = weak.get("direct_substitution", {}).get("Eq139", {}).get("branches", {})
    if (
        eq139.get("EQ139_PRINTED_STRICT_M_K_LT_N", {}).get("instance_count") != 4
        or eq139.get("EQ139_EQ145_COMPLETED_M_K_LE_N", {}).get("instance_count") != 10
    ):
        raise AssertionError("Eq.(139) 4/10 census changed")
    return {
        "Eq113": {
            "derived_Qn_records": 25,
            "literal_Qn_plus_1_records": 25,
            "branches_kept_separate": True,
            "role": "VALIDATION_ONLY_NOT_A_MIXED_SOURCE_COORDINATE",
        },
        "Eq139": {
            "printed_strict_instances": 4,
            "Eq145_completed_instances": 10,
            "domains_kept_separate": True,
            "role": "VALIDATION_ONLY_NOT_A_MIXED_SOURCE_COORDINATE",
        },
        "witness_rule": "direct substitution required before any witness promotion",
    }


def _eq120_binding(eq120: dict[str, Any], root: Path) -> dict[str, Any]:
    if (
        eq120.get("schema_version")
        != "final-theory-v042-eq120-source-provenance-certificate-v0.4.2"
        or eq120.get("verdict") != "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED"
        or eq120.get("passed") is not True
        or eq120.get("semantic_digest_sha256") != semantic_digest(eq120)
    ):
        raise AssertionError("Eq.(120) source-native certificate binding failed")
    counts = eq120.get("counts", {})
    if counts.get("unique_raw_relations") != 6 or counts.get("k1_Eq120_instances") != 3:
        raise AssertionError("Eq.(120) certificate count changed")
    return {
        "path": EQ120_PATH,
        "sha256": _sha256(root / EQ120_PATH),
        "semantic_digest_sha256": eq120["semantic_digest_sha256"],
        "source_locus_statement": (
            "all nonsingular source CPOBC points satisfy the three k=1 Eq.(120) "
            "instances for (R2,R3), (R2,R4), and (R3,R4)"
        ),
        "pairwise_ratio_prerequisites": ["R2_R3", "R2_R4", "R3_R4"],
        "old_chart_ideal_reused": False,
        "future_routing_metadata_only": ["S1", "S2", "S3"],
    }


def compile_source_native_955_mixed_manifest_v042(root: Path) -> dict[str, Any]:
    """Expand all declared source blocks into exact sparse QQ polynomials."""

    root = root.resolve()
    paths = {
        CPOBC_PATH: root / CPOBC_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        GC_PATH: root / GC_PATH,
        EQ112_PATH: root / EQ112_PATH,
        EQ113_BRANCH_PATH: root / EQ113_BRANCH_PATH,
        WEAK_D2_PATH: root / WEAK_D2_PATH,
        EQ120_PATH: root / EQ120_PATH,
    }
    cpobc, reduction, gc, eq112, branches, weak, eq120 = (
        _load(paths[path])
        for path in (
            CPOBC_PATH,
            REDUCTION_PATH,
            GC_PATH,
            EQ112_PATH,
            EQ113_BRANCH_PATH,
            WEAK_D2_PATH,
            EQ120_PATH,
        )
    )
    reduction_map = reduction.get("reduction_map")
    if not isinstance(reduction_map, list) or len(reduction_map) != 165:
        raise AssertionError("expected 165 source occurrence records")
    by_occurrence = {str(record["occurrence_id"]): record for record in reduction_map}
    if len(by_occurrence) != 165:
        raise AssertionError("occurrence IDs are not unique")
    orbit_records: dict[str, list[dict[str, Any]]] = {}
    for record in reduction_map:
        orbit_records.setdefault(str(record["orbit_id"]), []).append(record)
    orbit_ids = sorted(orbit_records)
    if len(orbit_ids) != 131:
        raise AssertionError("expected 131 ON quotient orbits")
    p_by_orbit: dict[str, Fraction] = {}
    for orbit_id, records in orbit_records.items():
        values = {
            _csg_probability(
                int(record["stage"]), record["source_relation_rows"], int(record["precursor_code"])
            )
            for record in records
        }
        if len(values) != 1:
            raise AssertionError(f"CSG character is not orbit-invariant: {orbit_id}")
        p_by_orbit[orbit_id] = values.pop()
    if not all(value != 0 for value in p_by_orbit.values()):
        raise AssertionError("CSG character is singular on an ON orbit")

    variable_names = [f"x:{orbit_id}" for orbit_id in orbit_ids] + [
        f"y:{orbit_id}" for orbit_id in orbit_ids
    ]
    x_index = {orbit_id: index for index, orbit_id in enumerate(orbit_ids)}
    y_index = {orbit_id: index + len(orbit_ids) for index, orbit_id in enumerate(orbit_ids)}

    def matrix_for_orbit(orbit_id: str) -> Matrix:
        return (
            (_constant(p_by_orbit[orbit_id]), _variable(x_index[orbit_id])),
            (_variable(y_index[orbit_id]), _constant(1)),
        )

    occurrence_matrices = {
        occurrence_id: matrix_for_orbit(str(record["orbit_id"]))
        for occurrence_id, record in by_occurrence.items()
    }
    signatures: dict[tuple[int, int, int], str] = {}
    for record in reduction_map:
        signature = (
            int(record["stage"]),
            _relation_code(tuple(int(row) for row in record["source_relation_rows"])),
            int(record["precursor_code"]),
        )
        previous = signatures.setdefault(signature, str(record["orbit_id"]))
        if previous != str(record["orbit_id"]):
            raise AssertionError("one source signature maps to multiple ON orbits")

    cpobc_residuals: list[dict[str, Any]] = []
    cpobc_entries: list[Polynomial] = []
    for relation in cpobc.get("relations", []):
        for equation in relation.get("raw_noncommutative_relation", []):
            identifiers = equation["operator_ids"]
            lhs = _identity()
            for token in equation["lhs_word"]:
                lhs = _matrix_multiply(lhs, occurrence_matrices[identifiers[token]])
            rhs = _identity()
            for token in equation["rhs_word"]:
                rhs = _matrix_multiply(rhs, occurrence_matrices[identifiers[token]])
            residual = _matrix_subtract(lhs, rhs)
            entries = [residual[row][column] for row in range(2) for column in range(2)]
            cpobc_entries.extend(entries)
            cpobc_residuals.append(
                {
                    "relation_id": str(relation["relation_id"]),
                    "equation_id": str(equation["equation_id"]),
                    "entries": _serialize_matrix(residual, variable_names),
                }
            )
    if len(cpobc_residuals) != 783:
        raise AssertionError("raw CPOBC equation census changed")

    def transition_matrix(signature: dict[str, Any]) -> Matrix:
        key = (
            int(signature["stage"]),
            int(signature["source_relation_code"]),
            int(signature["precursor_code"]),
        )
        return matrix_for_orbit(signatures[key])

    path_matrices: dict[str, Matrix] = {}
    path_inventory = gc.get("path_inventory")
    if not isinstance(path_inventory, dict):
        raise AssertionError("strong-GC path inventory absent")
    for paths_at_stage in path_inventory.values():
        for path in paths_at_stage:
            product = _identity()
            for transition in path.get("transitions", []):
                product = _matrix_multiply(
                    transition_matrix(transition["quotient_signature"]), product
                )
            path_matrices[str(path["path_id"])] = product
    if len(path_matrices) != 407:
        raise AssertionError("strong-GC path census changed")
    basis = gc.get("generating_relation_basis")
    if not isinstance(basis, list) or len(basis) != 320:
        raise AssertionError("strong-GC basis census changed")
    gc_residuals: list[dict[str, Any]] = []
    gc_entries: list[Polynomial] = []
    for relation in basis:
        residual = _matrix_subtract(
            path_matrices[str(relation["lhs_path_id"])],
            path_matrices[str(relation["rhs_path_id"])],
        )
        entries = [residual[row][column] for row in range(2) for column in range(2)]
        gc_entries.extend(entries)
        gc_residuals.append(
            {
                "relation_id": str(relation["relation_id"]),
                "endpoint_causet_id": str(relation["endpoint_causet_id"]),
                "entries": _serialize_matrix(residual, variable_names),
            }
        )

    constraints = cpobc.get("MSR_operator_constraints")
    if not isinstance(constraints, list) or len(constraints) != 24:
        raise AssertionError("reachable-MSR source census changed")
    source_ids = {str(record["source_id"]) for record in constraints}
    canonical_paths: dict[str, Matrix] = {}
    canonical_path_ids: dict[str, str] = {}
    for paths_at_stage in path_inventory.values():
        for endpoint in {str(path["endpoint_causet_id"]) for path in paths_at_stage}:
            candidates = [
                path for path in paths_at_stage if str(path["endpoint_causet_id"]) == endpoint
            ]
            chosen = min(candidates, key=lambda path: str(path["path_id"]))
            if endpoint in source_ids:
                canonical_paths[endpoint] = path_matrices[str(chosen["path_id"])]
                canonical_path_ids[endpoint] = str(chosen["path_id"])
    if set(canonical_paths) != source_ids:
        raise AssertionError("canonical strong-GC paths do not cover all MSR sources")
    omega: Vector = (_constant(1), _constant(0))
    msr_operator_residuals: list[dict[str, Any]] = []
    msr_vector_residuals: list[dict[str, Any]] = []
    msr_operator_entries: list[Polynomial] = []
    msr_vector_entries: list[Polynomial] = []
    p1_lower_right: Polynomial | None = None
    for constraint in sorted(constraints, key=lambda item: str(item["source_id"])):
        residual = _matrix_negate(_identity())
        for term in constraint["terms"]:
            coefficient = int(term["coefficient"])
            matrix = occurrence_matrices[str(term["transition_id"])]
            scaled = tuple(
                tuple(_multiply(_constant(coefficient), matrix[row][column]) for column in range(2))
                for row in range(2)
            )
            residual = _matrix_add(residual, scaled)  # type: ignore[arg-type]
        source_id = str(constraint["source_id"])
        vector = _matrix_vector(residual, _matrix_vector(canonical_paths[source_id], omega))
        operator_entries = [residual[row][column] for row in range(2) for column in range(2)]
        msr_operator_entries.extend(operator_entries)
        msr_vector_entries.extend(vector)
        msr_operator_residuals.append(
            {
                "constraint_id": str(constraint["constraint_id"]),
                "source_id": source_id,
                "entries": _serialize_matrix(residual, variable_names),
            }
        )
        msr_vector_residuals.append(
            {
                "constraint_id": str(constraint["constraint_id"]),
                "source_id": source_id,
                "canonical_state_from_path": canonical_path_ids[source_id],
                "entries": _serialize_vector(vector, variable_names),
            }
        )
        if source_id == "p1-0":
            p1_lower_right = residual[1][1]
    if p1_lower_right != _constant(1):
        raise AssertionError("p1 operator residual lower-right is not identically one")

    q_orbits = {}
    for stage, source_id in ((1, "p1-0"), (2, "p2-0"), (3, "p3-000"), (4, "p4-0000")):
        candidates = [
            record
            for record in reduction_map
            if record["source_id"] == source_id and record["transition_kind"] == "GREGARIOUS"
        ]
        if len(candidates) != 1 or int(candidates[0]["precursor_code"]) != 0:
            raise AssertionError(f"cannot bind source-defined Q_{stage}")
        q_orbits[stage] = str(candidates[0]["orbit_id"])
    commutators: list[dict[str, Any]] = []
    commutator_entries: list[Polynomial] = []
    for left in range(1, 5):
        for right in range(left + 1, 5):
            residual = _matrix_subtract(
                _matrix_multiply(
                    matrix_for_orbit(q_orbits[left]), matrix_for_orbit(q_orbits[right])
                ),
                _matrix_multiply(
                    matrix_for_orbit(q_orbits[right]), matrix_for_orbit(q_orbits[left])
                ),
            )
            commutator_entries.extend(
                residual[row][column] for row in range(2) for column in range(2)
            )
            commutators.append(
                {
                    "pair": [left, right],
                    "Q_orbits": [q_orbits[left], q_orbits[right]],
                    "entries": _serialize_matrix(residual, variable_names),
                }
            )

    all_entries = cpobc_entries + gc_entries + msr_operator_entries + msr_vector_entries
    total_manifest_terms = sum(len(value) for value in all_entries)
    if total_manifest_terms > MAX_TOTAL_TERMS:
        raise RuntimeError("manifest term count exceeds declared resource limit")
    supplemental = _supplemental_ledger(eq112, branches, weak)
    eq120_binding = _eq120_binding(eq120, root)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "field": "QQ",
            "dimension": 2,
            "finite_source_stages": "n<=4",
            "identification_mode": "ON_QUOTIENT",
            "ansatz": "A_e=[[p_e,x_e],[y_e,1]], p_e=CSG(t_j=1), Omega=e1",
        },
        "source_artifact_sha256": {path: _sha256(file_path) for path, file_path in paths.items()},
        "variables": {
            "x_coordinates": 131,
            "y_coordinates": 131,
            "total": 262,
            "names": variable_names,
            "CSG_diagonal_character": {
                orbit_id: str(p_by_orbit[orbit_id]) for orbit_id in orbit_ids
            },
        },
        "nonsingularity_localisation": {
            "raw_occurrence_factors": [
                {
                    "occurrence_id": occurrence_id,
                    "orbit_id": str(record["orbit_id"]),
                    "factor": (
                        f"({p_by_orbit[str(record['orbit_id'])]})-x:{record['orbit_id']}*"
                        f"y:{record['orbit_id']}"
                    ),
                }
                for occurrence_id, record in sorted(by_occurrence.items())
            ],
            "raw_occurrences": 165,
            "distinct_ON_quotient_factors": 131,
            "determinant_formula": "det(A_e)=p_e-x_e*y_e",
        },
        "residual_blocks": {
            "CPOBC": {
                "count": 783,
                "records": cpobc_residuals,
                "term_census": _term_census(cpobc_entries),
            },
            "strong_GC": {
                "count": 320,
                "records": gc_residuals,
                "term_census": _term_census(gc_entries),
            },
            "reachable_MSR_operator": {
                "count": 24,
                "records": msr_operator_residuals,
                "term_census": _term_census(msr_operator_entries),
            },
            "reachable_MSR_vector": {
                "count": 24,
                "records": msr_vector_residuals,
                "term_census": _term_census(msr_vector_entries),
            },
        },
        "residual_content_digests": {
            "CPOBC": _residual_digest(cpobc_residuals),
            "strong_GC": _residual_digest(gc_residuals),
            "reachable_MSR_operator": _residual_digest(msr_operator_residuals),
            "reachable_MSR_vector": _residual_digest(msr_vector_residuals),
        },
        "N_nonzero_certificate": {
            "source_id": "p1-0",
            "operator_residual_entry": [1, 1],
            "polynomial": _serialize_polynomial(p1_lower_right, variable_names),
            "conclusion": (
                "constant one, hence every ansatz point lies outside the strong-MSR N=0 slice"
            ),
        },
        "Q_commutator_polynomials": {
            "count": 6,
            "records": commutators,
            "term_census": _term_census(commutator_entries),
            "content_digest_sha256": _residual_digest(commutators),
        },
        "Eq120_source_native_binding": eq120_binding,
        "future_ratio_chart_routing": {
            "source_prerequisite_global_on_nonsingular_CPOBC_locus": True,
            "ratio_pairs": ["R2_R3", "R2_R4", "R3_R4"],
            "routes": ["S1", "S2", "S3"],
            "old_21_chart_ideals_reused": False,
            "status": "ROUTING_METADATA_ONLY_NO_CHART_COVER_CLAIM",
        },
        "supplemental_validation_ledger": supplemental,
        "prohibited_coordinate_dependencies": [
            "paper Eq.(107) reduction",
            "paper Eq.(108) operator-MSR elimination",
            "paper Eq.(112) B-factor reconstruction",
            "frozen Q-only presentation",
            "v0.4.1 chart input ideals",
        ],
        "resource_limits": {
            "maximum_terms_per_entry": MAX_ENTRY_TERMS,
            "maximum_total_manifest_terms": MAX_TOTAL_TERMS,
            "observed_total_manifest_terms": total_manifest_terms,
            "limit_exceeded": False,
        },
        "solver_status": "NOT_RUN",
        "sage_status": "NOT_INVOKED",
        "claim_boundary": [
            "This is an exact sparse QQ scalar-polynomial manifest for one mixed ansatz.",
            "It is not a solver result, witness, commutativity proof, or global chart cover.",
            "Eq.(113) and Eq.(139) are validation-only nonmerged gates.",
        ],
        "verdict": VERDICT,
        "passed": True,
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def write_source_native_955_mixed_manifest_v042(root: Path) -> Path:
    destination = root.resolve() / RESULT_PATH
    destination.write_text(
        json.dumps(
            compile_source_native_955_mixed_manifest_v042(root), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_source_native_955_mixed_manifest_v042(repository_root))
