"""Exact CPOBC unit-ideal obstruction for one fixed harmonic state assignment.

The certificate is independent of the D12 compiler's polynomial machinery.
It rebuilds the ON endpoint graph from the frozen raw CPOBC and occurrence
reduction ledgers, reconstructs the harmonic rank-two states over ``QQ``, and
forms every full affine edge as

``F_target * [[1, alpha_e], [0, beta_e]] * F_source^-1``.

One raw Eq. (103) residual has the constant entry ``2/117`` even with all 262
alpha/beta coordinates free.  Hence the raw CPOBC ideal for this fixed state
assignment is the unit ideal.  The beta=1 shear value ``7/663`` is retained as
an independent manifest cross-check.  This does not cover other rank-two state
assignments or SR2-V.  No solver is imported or invoked.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

RESULT_PATH = "results/v0.4.2_sr2v_fixed_harmonic_cpobc_obstruction.json"
CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
D12_MANIFEST_PATH = "results/v0.4.2_sr2v_state_native_shear_D12_manifest.json"

SCHEMA = "final-theory-v042-sr2v-fixed-harmonic-full-affine-cpobc-unit-ideal-v1"
VERDICT = (
    "SR2V_FIXED_HARMONIC_FULL_ALPHA_BETA_CPOBC_UNIT_IDEAL_"
    "OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN"
)
SEARCH_TERMINAL = "FIXED_HARMONIC_STATE_ASSIGNMENT_CHART_TERMINAL_ONLY"

PINNED_INPUT_SHA256 = {
    CPOBC_PATH: "8e9498fd6be13ff7553f1e3d2df6919b5a1595294a8feb2134467c63c5c1dda9",
    REDUCTION_PATH: "88363a527e7f015457f51ae94da5ac5e03c83fca588fe07a8bfd9e4fbb0ca52b",
    D12_MANIFEST_PATH: "125d21520df39578e102300c5e0d15509631e1c579506c361fdd58f216312d82",
}
PINNED_D12_SEMANTIC_SHA256 = (
    "82cd51ddd29e5923b003c8cf8f75a5a26cf5a36edf68728ad58d298d3f573090"
)

FULL_CORE_RELATION_ID = "cpobc-relation-0ca7a22bed9cdf4bc14a"
FULL_CORE_EQUATION_ID = "eq103"
FULL_CORE_ENTRY = (0, 0)
FULL_CORE_VALUE = Fraction(2, 117)
FULL_UNIT_MULTIPLIER = Fraction(117, 2)

SHEAR_CORE_RELATION_ID = "cpobc-relation-1decb1e77431d5355ada"
SHEAR_CORE_EQUATION_ID = "eq103"
SHEAR_CORE_ENTRY = (1, 0)
SHEAR_CORE_VALUE = Fraction(7, 663)
SHEAR_UNIT_MULTIPLIER = Fraction(663, 7)

Monomial = tuple[str, ...]
Polynomial = dict[Monomial, Fraction]
Matrix = tuple[tuple[Polynomial, Polynomial], tuple[Polynomial, Polynomial]]
Vector2 = tuple[Fraction, Fraction]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON object required: {path}")
    return payload


def _constant(value: Fraction | int) -> Polynomial:
    scalar = Fraction(value)
    return {(): scalar} if scalar else {}


def _variable(name: str) -> Polynomial:
    return {(name,): Fraction(1)}


def _add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        updated = result.get(monomial, Fraction(0)) + coefficient
        if updated:
            result[monomial] = updated
        else:
            result.pop(monomial, None)
    return result


def _scale(coefficient: Fraction | int, value: Polynomial) -> Polynomial:
    scalar = Fraction(coefficient)
    return {
        monomial: scalar * item
        for monomial, item in value.items()
        if scalar * item
    }


def _subtract(left: Polynomial, right: Polynomial) -> Polynomial:
    return _add(left, _scale(-1, right))


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
    return result


def _matrix_constant(value: tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]) -> Matrix:
    return cast(
        Matrix,
        tuple(tuple(_constant(value[row][column]) for column in range(2)) for row in range(2)),
    )


def _identity() -> Matrix:
    return ((_constant(1), _constant(0)), (_constant(0), _constant(1)))


def _matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return cast(
        Matrix,
        tuple(
            tuple(
                _add(
                    _multiply(left[row][0], right[0][column]),
                    _multiply(left[row][1], right[1][column]),
                )
                for column in range(2)
            )
            for row in range(2)
        ),
    )


def _matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return cast(
        Matrix,
        tuple(
            tuple(_subtract(left[row][column], right[row][column]) for column in range(2))
            for row in range(2)
        ),
    )


def _matrix_word(factors: list[Matrix]) -> Matrix:
    product = _identity()
    for factor in factors:
        product = _matrix_multiply(product, factor)
    return product


def _determinant(matrix: Matrix) -> Polynomial:
    return _subtract(
        _multiply(matrix[0][0], matrix[1][1]),
        _multiply(matrix[0][1], matrix[1][0]),
    )


def _serialize_polynomial(polynomial: Polynomial) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": str(coefficient),
            "monomial": [
                {"variable": variable, "exponent": monomial.count(variable)}
                for variable in sorted(set(monomial))
            ],
        }
        for monomial, coefficient in sorted(polynomial.items())
    ]


def _serialize_matrix(matrix: Matrix) -> dict[str, list[dict[str, Any]]]:
    return {
        f"{row}{column}": _serialize_polynomial(matrix[row][column])
        for row in range(2)
        for column in range(2)
    }


def _deserialize_polynomial(records: Any) -> Polynomial:
    if not isinstance(records, list):
        raise TypeError("serialized polynomial must be a list")
    result: Polynomial = {}
    for record in records:
        coefficient = Fraction(str(record["coefficient"]))
        monomial: list[str] = []
        for factor in record["monomial"]:
            exponent = factor["exponent"]
            if isinstance(exponent, bool) or not isinstance(exponent, int) or exponent < 1:
                raise ValueError("monomial exponent must be a positive integer")
            monomial.extend([str(factor["variable"])] * exponent)
        result = _add(result, {tuple(sorted(monomial)): coefficient})
    return result


def _records_digest(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def _build_graph(
    cpobc: dict[str, Any],
    reduction: dict[str, Any],
) -> dict[str, Any]:
    occurrence_records = {
        str(record["occurrence_id"]): record for record in reduction["reduction_map"]
    }
    if len(occurrence_records) != 165:
        raise AssertionError("expected 165 occurrence records")
    occurrence_orbits = {
        occurrence_id: str(record["orbit_id"])
        for occurrence_id, record in occurrence_records.items()
    }

    endpoint_stages: dict[str, int] = {}
    by_orbit: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in occurrence_records.values():
        source = str(record["source_id"])
        target = str(record["target_id"])
        stage = int(record["stage"])
        for endpoint, expected_stage in ((source, stage), (target, stage + 1)):
            previous = endpoint_stages.setdefault(endpoint, expected_stage)
            if previous != expected_stage:
                raise AssertionError("one endpoint appears at two stages")
        by_orbit[str(record["orbit_id"])].append(record)

    edges: dict[str, dict[str, Any]] = {}
    for orbit, records in by_orbit.items():
        signatures = {
            (str(record["source_id"]), str(record["target_id"]), int(record["stage"]))
            for record in records
        }
        if len(signatures) != 1:
            raise AssertionError("one ON orbit has multiple endpoint signatures")
        source, target, stage = signatures.pop()
        edges[orbit] = {
            "source": source,
            "target": target,
            "stage": stage,
            "occurrence_ids": sorted(str(record["occurrence_id"]) for record in records),
        }
    if len(edges) != 131:
        raise AssertionError("expected 131 ON transition orbits")

    outgoing: dict[str, list[dict[str, Any]]] = {}
    for constraint in cpobc["MSR_operator_constraints"]:
        source = str(constraint["source_id"])
        aggregated: defaultdict[str, int] = defaultdict(int)
        for term in constraint["terms"]:
            occurrence_id = str(term["transition_id"])
            orbit = occurrence_orbits[occurrence_id]
            if edges[orbit]["source"] != source:
                raise AssertionError("MSR transition is attached to the wrong source")
            aggregated[orbit] += int(term["coefficient"])
        outgoing[source] = [
            {
                "orbit": orbit,
                "target": edges[orbit]["target"],
                "multiplicity": multiplicity,
            }
            for orbit, multiplicity in sorted(aggregated.items())
        ]
    if len(outgoing) != 24:
        raise AssertionError("expected 24 nonterminal MSR sources")
    return {
        "occurrence_records": occurrence_records,
        "occurrence_orbits": occurrence_orbits,
        "endpoint_stages": endpoint_stages,
        "edges": edges,
        "outgoing": outgoing,
    }


def _harmonic_states(graph: dict[str, Any]) -> dict[str, Any]:
    endpoint_stages: dict[str, int] = graph["endpoint_stages"]
    outgoing: dict[str, list[dict[str, Any]]] = graph["outgoing"]
    roots = sorted(endpoint for endpoint, stage in endpoint_stages.items() if stage == 1)
    terminals = sorted(endpoint for endpoint, stage in endpoint_stages.items() if stage == 5)
    if roots != ["p1-0"]:
        raise AssertionError("expected the unique frozen root p1-0")
    root = roots[0]

    h: dict[str, Fraction] = {terminal: Fraction(1) for terminal in terminals}
    for stage in range(4, 0, -1):
        for source in sorted(
            endpoint for endpoint in outgoing if endpoint_stages[endpoint] == stage
        ):
            h[source] = sum(
                (
                    Fraction(term["multiplicity"]) * h[term["target"]]
                    for term in outgoing[source]
                ),
                start=Fraction(0),
            )

    root_weights: defaultdict[str, int] = defaultdict(int)
    root_weights[root] = 1
    for stage in range(1, 5):
        for source in sorted(
            endpoint for endpoint in outgoing if endpoint_stages[endpoint] == stage
        ):
            for term in outgoing[source]:
                root_weights[term["target"]] += (
                    root_weights[source] * int(term["multiplicity"])
                )
    terminal_weights = {terminal: root_weights[terminal] for terminal in terminals}
    first_terminal = min(terminals, key=lambda item: (terminal_weights[item], item))
    second_terminal = max(terminals, key=lambda item: (terminal_weights[item], item))
    if first_terminal == second_terminal:
        raise AssertionError("two distinct support terminals are required")

    k: dict[str, Fraction] = {terminal: Fraction(0) for terminal in terminals}
    k[first_terminal] = Fraction(terminal_weights[second_terminal])
    k[second_terminal] = -Fraction(terminal_weights[first_terminal])
    for stage in range(4, 0, -1):
        for source in sorted(
            endpoint for endpoint in outgoing if endpoint_stages[endpoint] == stage
        ):
            k[source] = sum(
                (
                    Fraction(term["multiplicity"]) * k[term["target"]]
                    for term in outgoing[source]
                ),
                start=Fraction(0),
            )

    normalisation = h[root]
    states: dict[str, Vector2] = {
        endpoint: (h[endpoint] / normalisation, k[endpoint] / normalisation)
        for endpoint in endpoint_stages
    }
    harmonic_failures: list[str] = []
    for source, terms in outgoing.items():
        expected = (
            sum(
                Fraction(term["multiplicity"]) * states[term["target"]][0]
                for term in terms
            ),
            sum(
                Fraction(term["multiplicity"]) * states[term["target"]][1]
                for term in terms
            ),
        )
        if states[source] != expected:
            harmonic_failures.append(source)
    support_determinant = (
        states[first_terminal][0] * states[second_terminal][1]
        - states[first_terminal][1] * states[second_terminal][0]
    )
    if states[root] != (Fraction(1), Fraction(0)):
        raise AssertionError("harmonic normalization failed")
    return {
        "states": states,
        "normalisation": normalisation,
        "support_terminals": [first_terminal, second_terminal],
        "support_determinant": support_determinant,
        "harmonic_failures": harmonic_failures,
    }


def _state_native_matrix(
    source: Vector2,
    target: Vector2,
    orbit: str,
    *,
    beta_is_one: bool,
) -> Matrix:
    h_source, k_source = source
    h_target, k_target = target
    if not h_source or not h_target:
        raise AssertionError("local frames require nonzero first coordinates")
    source_frame_inverse = _matrix_constant(
        (
            (Fraction(1, 1) / h_source, Fraction(0)),
            (-k_source / h_source, Fraction(1)),
        )
    )
    target_frame = _matrix_constant(
        ((h_target, Fraction(0)), (k_target, Fraction(1)))
    )
    lower_right = _constant(1) if beta_is_one else _variable(f"beta:{orbit}")
    local_matrix: Matrix = (
        (_constant(1), _variable(f"alpha:{orbit}")),
        (_constant(0), lower_right),
    )
    return _matrix_multiply(
        _matrix_multiply(target_frame, local_matrix),
        source_frame_inverse,
    )


def _pure_constant_record(
    relation_id: str,
    equation_id: str,
    row: int,
    column: int,
    polynomial: Polynomial,
) -> dict[str, Any] | None:
    if set(polynomial) != {()} or not polynomial[()]:
        return None
    return {
        "relation_id": relation_id,
        "equation_id": equation_id,
        "entry": [row, column],
        "value": str(polynomial[()]),
    }


def _constant_entries_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relation in manifest["residual_blocks"]["CPOBC_raw"]["records"]:
        for entry, serialized in relation["entries"].items():
            polynomial = _deserialize_polynomial(serialized)
            record = _pure_constant_record(
                str(relation["relation_id"]),
                str(relation["equation_id"]),
                int(entry[0]),
                int(entry[1]),
                polynomial,
            )
            if record is not None:
                records.append(record)
    return sorted(records, key=_constant_record_key)


def _constant_record_key(record: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        str(record["relation_id"]),
        str(record["equation_id"]),
        int(record["entry"][0]),
        int(record["entry"][1]),
    )


def _reconstruct_raw_cpobc(
    cpobc: dict[str, Any],
    graph: dict[str, Any],
    occurrence_matrices: dict[str, Matrix],
    core_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    constant_records: list[dict[str, Any]] = []
    core_details: dict[tuple[str, str], dict[str, Any]] = {}
    raw_equation_count = 0
    scalar_entry_count = 0
    for relation in cpobc["relations"]:
        relation_id = str(relation["relation_id"])
        for equation in relation["raw_noncommutative_relation"]:
            equation_id = str(equation["equation_id"])
            operator_ids = equation["operator_ids"]
            lhs = _matrix_word(
                [occurrence_matrices[str(operator_ids[token])] for token in equation["lhs_word"]]
            )
            rhs = _matrix_word(
                [occurrence_matrices[str(operator_ids[token])] for token in equation["rhs_word"]]
            )
            residual = _matrix_subtract(lhs, rhs)
            raw_equation_count += 1
            scalar_entry_count += 4
            for row in range(2):
                for column in range(2):
                    record = _pure_constant_record(
                        relation_id,
                        equation_id,
                        row,
                        column,
                        residual[row][column],
                    )
                    if record is not None:
                        constant_records.append(record)
            key = (relation_id, equation_id)
            if key in core_keys:
                aliases = {
                    alias: {
                        "occurrence_id": str(occurrence_id),
                        "orbit_id": graph["occurrence_orbits"][str(occurrence_id)],
                        "source_id": str(
                            graph["occurrence_records"][str(occurrence_id)]["source_id"]
                        ),
                        "target_id": str(
                            graph["occurrence_records"][str(occurrence_id)]["target_id"]
                        ),
                    }
                    for alias, occurrence_id in operator_ids.items()
                }
                core_details[key] = {
                    "raw_display": equation["display"],
                    "lhs_word": equation["lhs_word"],
                    "rhs_word": equation["rhs_word"],
                    "aliases": aliases,
                    "matrices": {
                        alias: _serialize_matrix(
                            occurrence_matrices[str(operator_ids[alias])]
                        )
                        for alias in sorted(operator_ids)
                    },
                    "lhs_matrix": _serialize_matrix(lhs),
                    "rhs_matrix": _serialize_matrix(rhs),
                    "residual_matrix": _serialize_matrix(residual),
                }
    constant_records.sort(key=_constant_record_key)
    return {
        "constant_records": constant_records,
        "core_details": core_details,
        "raw_equation_count": raw_equation_count,
        "scalar_entry_count": scalar_entry_count,
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_hashes = {
        path: _sha256(root / path) for path in (CPOBC_PATH, REDUCTION_PATH, D12_MANIFEST_PATH)
    }
    if input_hashes != PINNED_INPUT_SHA256:
        changed = sorted(
            path for path, digest in input_hashes.items() if digest != PINNED_INPUT_SHA256[path]
        )
        raise AssertionError(f"pinned obstruction input changed: {changed}")

    cpobc = _load(root / CPOBC_PATH)
    reduction = _load(root / REDUCTION_PATH)
    manifest = _load(root / D12_MANIFEST_PATH)
    if cpobc.get("passed") is not True or reduction.get("passed") is not True:
        raise AssertionError("raw CPOBC or reduction input did not pass")
    if manifest.get("semantic_digest_sha256") != semantic_digest(manifest):
        raise AssertionError("D12 manifest semantic digest does not recompute")
    if manifest.get("semantic_digest_sha256") != PINNED_D12_SEMANTIC_SHA256:
        raise AssertionError("unexpected D12 manifest semantic digest")

    graph = _build_graph(cpobc, reduction)
    harmonic = _harmonic_states(graph)
    states: dict[str, Vector2] = harmonic["states"]
    full_edge_matrices = {
        orbit: _state_native_matrix(
            states[str(edge["source"])],
            states[str(edge["target"])],
            orbit,
            beta_is_one=False,
        )
        for orbit, edge in graph["edges"].items()
    }
    shear_edge_matrices = {
        orbit: _state_native_matrix(
            states[str(edge["source"])],
            states[str(edge["target"])],
            orbit,
            beta_is_one=True,
        )
        for orbit, edge in graph["edges"].items()
    }
    full_edge_determinants = {
        orbit: _determinant(matrix) for orbit, matrix in full_edge_matrices.items()
    }
    shear_edge_determinants = {
        orbit: _determinant(matrix) for orbit, matrix in shear_edge_matrices.items()
    }
    full_occurrence_matrices = {
        occurrence_id: full_edge_matrices[orbit]
        for occurrence_id, orbit in graph["occurrence_orbits"].items()
    }
    shear_occurrence_matrices = {
        occurrence_id: shear_edge_matrices[orbit]
        for occurrence_id, orbit in graph["occurrence_orbits"].items()
    }
    full_key = (FULL_CORE_RELATION_ID, FULL_CORE_EQUATION_ID)
    shear_key = (SHEAR_CORE_RELATION_ID, SHEAR_CORE_EQUATION_ID)
    full_reconstruction = _reconstruct_raw_cpobc(
        cpobc,
        graph,
        full_occurrence_matrices,
        {full_key},
    )
    shear_reconstruction = _reconstruct_raw_cpobc(
        cpobc,
        graph,
        shear_occurrence_matrices,
        {shear_key},
    )
    full_constant_records: list[dict[str, Any]] = full_reconstruction["constant_records"]
    shear_constant_records: list[dict[str, Any]] = shear_reconstruction["constant_records"]
    full_core_detail = full_reconstruction["core_details"].get(full_key)
    shear_core_detail = shear_reconstruction["core_details"].get(shear_key)
    if full_core_detail is None or shear_core_detail is None:
        raise AssertionError("a declared core Eq. (103) relation is absent")

    full_entry_key = f"{FULL_CORE_ENTRY[0]}{FULL_CORE_ENTRY[1]}"
    shear_entry_key = f"{SHEAR_CORE_ENTRY[0]}{SHEAR_CORE_ENTRY[1]}"
    full_core_polynomial = _deserialize_polynomial(
        full_core_detail["residual_matrix"][full_entry_key]
    )
    shear_core_polynomial = _deserialize_polynomial(
        shear_core_detail["residual_matrix"][shear_entry_key]
    )
    manifest_constant_records = _constant_entries_from_manifest(manifest)
    manifest_shear_core_records = [
        record
        for record in manifest_constant_records
        if record["relation_id"] == SHEAR_CORE_RELATION_ID
        and record["equation_id"] == SHEAR_CORE_EQUATION_ID
        and record["entry"] == list(SHEAR_CORE_ENTRY)
    ]
    full_histogram = Counter(
        f"{record['entry'][0]}{record['entry'][1]}" for record in full_constant_records
    )
    shear_histogram = Counter(
        f"{record['entry'][0]}{record['entry'][1]}" for record in shear_constant_records
    )
    full_relation_ids = {record["relation_id"] for record in full_constant_records}
    shear_relation_ids = {record["relation_id"] for record in shear_constant_records}

    gates = {
        "raw_CPOBC_and_reduction_SHA256_are_bound": input_hashes[CPOBC_PATH]
        == PINNED_INPUT_SHA256[CPOBC_PATH]
        and input_hashes[REDUCTION_PATH] == PINNED_INPUT_SHA256[REDUCTION_PATH],
        "independent_graph_has_165_occurrences_131_orbits_87_states": len(
            graph["occurrence_records"]
        )
        == 165
        and len(graph["edges"]) == 131
        and len(states) == 87,
        "harmonic_state_equations_hold_exactly": not harmonic["harmonic_failures"],
        "harmonic_state_span_has_rank_two": harmonic["support_determinant"] != 0,
        "all_131_full_chart_determinants_are_nonzero_beta_monomials": len(
            full_edge_determinants
        )
        == 131
        and all(
            set(value) == {(f"beta:{orbit}",)} and value[(f"beta:{orbit}",)]
            for orbit, value in full_edge_determinants.items()
        ),
        "all_131_beta1_shear_determinants_are_nonzero_constants": len(
            shear_edge_determinants
        )
        == 131
        and all(
            set(value) == {()} and value[()] for value in shear_edge_determinants.values()
        ),
        "both_reconstructions_cover_all_783_raw_CPOBC_equations": (
            full_reconstruction["raw_equation_count"]
            == shear_reconstruction["raw_equation_count"]
            == 783
            and full_reconstruction["scalar_entry_count"]
            == shear_reconstruction["scalar_entry_count"]
            == 3132
        ),
        "full_alpha_beta_pure_nonzero_constant_entry_count_is_95": len(
            full_constant_records
        )
        == 95,
        "full_alpha_beta_core_Eq103_entry_is_exactly_2_over_117": (
            full_core_polynomial == {(): FULL_CORE_VALUE}
        ),
        "full_alpha_beta_unit_ideal_multiplier_is_exact": (
            FULL_UNIT_MULTIPLIER * FULL_CORE_VALUE == 1
        ),
        "beta1_shear_pure_nonzero_constant_entry_count_is_178": len(
            shear_constant_records
        )
        == 178,
        "beta1_shear_core_Eq103_entry_is_exactly_7_over_663": (
            shear_core_polynomial == {(): SHEAR_CORE_VALUE}
        ),
        "beta1_shear_unit_ideal_multiplier_is_exact": (
            SHEAR_UNIT_MULTIPLIER * SHEAR_CORE_VALUE == 1
        ),
        "manifest_pure_constant_census_count_is_178": len(manifest_constant_records) == 178,
        "manifest_census_matches_independent_beta1_reconstruction": (
            manifest_constant_records == shear_constant_records
        ),
        "manifest_beta1_core_entry_matches_exactly": manifest_shear_core_records
        == [
            {
                "relation_id": SHEAR_CORE_RELATION_ID,
                "equation_id": SHEAR_CORE_EQUATION_ID,
                "entry": list(SHEAR_CORE_ENTRY),
                "value": str(SHEAR_CORE_VALUE),
            }
        ],
        "unit_generators_are_Q5_D12_budget_independent": not any(
            variable.startswith(("Q5:", "rho:", "sigma:"))
            for polynomial in (full_core_polynomial, shear_core_polynomial)
            for monomial in polynomial
            for variable in monomial
        ),
        "D12_manifest_is_comparison_only_and_remains_no_solver": manifest[
            "resource_and_claim_boundaries"
        ]["solver_status"]
        == "NOT_RUN",
    }
    if not all(gates.values()):
        failed = sorted(name for name, passed in gates.items() if not passed)
        raise AssertionError(f"fixed-harmonic CPOBC obstruction failed: {failed}")

    full_involved_endpoints = sorted(
        {
            str(record[key])
            for record in full_core_detail["aliases"].values()
            for key in ("source_id", "target_id")
        }
    )
    shear_involved_endpoints = sorted(
        {
            str(record[key])
            for record in shear_core_detail["aliases"].values()
            for key in ("source_id", "target_id")
        }
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_slice": (
            "one_fixed_harmonic_rank2_state_assignment__all_131_alpha_e_and_"
            "all_131_beta_e_free__occurrence_identification_ON"
        ),
        "input_bindings": {
            "mathematical_inputs": {
                CPOBC_PATH: input_hashes[CPOBC_PATH],
                REDUCTION_PATH: input_hashes[REDUCTION_PATH],
            },
            "manifest_comparison_only": {
                "path": D12_MANIFEST_PATH,
                "raw_sha256": input_hashes[D12_MANIFEST_PATH],
                "semantic_digest_sha256": manifest["semantic_digest_sha256"],
                "not_used_to_construct_graph_states_matrices_or_residuals": True,
            },
        },
        "independent_reconstruction": {
            "imports_D12_polynomial_helpers": False,
            "graph_source": "raw occurrence reduction map plus raw MSR source ledger",
            "occurrence_count": len(graph["occurrence_records"]),
            "ON_orbit_count": len(graph["edges"]),
            "endpoint_state_count": len(states),
            "nonterminal_source_count": len(graph["outgoing"]),
            "harmonic_failures": harmonic["harmonic_failures"],
            "support_terminals": harmonic["support_terminals"],
            "support_determinant": str(harmonic["support_determinant"]),
            "parameterisation": (
                "A_e=F_target*[[1,alpha_e],[0,beta_e]]*F_source^-1"
            ),
            "alpha_coordinate_count": len(full_edge_matrices),
            "beta_coordinate_count": len(full_edge_matrices),
            "full_affine_coordinate_count": 2 * len(full_edge_matrices),
            "nonsingular_subdomain": "product_e(beta_e)!=0",
            "Q5_coordinate_count": 0,
            "D12_localization_coordinate_count": 0,
            "budget_input_count": 0,
        },
        "full_alpha_beta_core_unit_generator": {
            "relation_id": FULL_CORE_RELATION_ID,
            "equation_id": FULL_CORE_EQUATION_ID,
            "entry": list(FULL_CORE_ENTRY),
            "display": "(A_n*A_prime_m-A_m*A_prime_n)[0,0]=2/117",
            "involved_endpoint_states": {
                endpoint: [str(value) for value in states[endpoint]]
                for endpoint in full_involved_endpoints
            },
            **full_core_detail,
            "lhs_core_entry": full_core_detail["lhs_matrix"][full_entry_key],
            "rhs_core_entry": full_core_detail["rhs_matrix"][full_entry_key],
            "residual_core_entry": full_core_detail["residual_matrix"][full_entry_key],
            "exact_constant_value": str(FULL_CORE_VALUE),
            "unit_multiplier": str(FULL_UNIT_MULTIPLIER),
            "unit_identity": "(117/2)*(2/117)=1",
            "polynomial_variable_support": [],
        },
        "full_alpha_beta_constant_residual_census": {
            "raw_operator_equations": full_reconstruction["raw_equation_count"],
            "raw_scalar_entries": full_reconstruction["scalar_entry_count"],
            "pure_nonzero_constant_entries": len(full_constant_records),
            "relations_with_a_pure_nonzero_constant_entry": len(full_relation_ids),
            "entry_position_histogram": dict(sorted(full_histogram.items())),
            "records": full_constant_records,
            "records_digest_sha256": _records_digest(full_constant_records),
        },
        "beta1_shear_crosscheck": {
            "specialisation": "beta_e=1 for all 131 actual ON edge orbits",
            "core_unit_generator": {
                "relation_id": SHEAR_CORE_RELATION_ID,
                "equation_id": SHEAR_CORE_EQUATION_ID,
                "entry": list(SHEAR_CORE_ENTRY),
                "display": "(A_n*A_prime_m-A_m*A_prime_n)[1,0]=7/663",
                "involved_endpoint_states": {
                    endpoint: [str(value) for value in states[endpoint]]
                    for endpoint in shear_involved_endpoints
                },
                **shear_core_detail,
                "lhs_core_entry": shear_core_detail["lhs_matrix"][shear_entry_key],
                "rhs_core_entry": shear_core_detail["rhs_matrix"][shear_entry_key],
                "residual_core_entry": shear_core_detail["residual_matrix"][shear_entry_key],
                "exact_constant_value": str(SHEAR_CORE_VALUE),
                "unit_multiplier": str(SHEAR_UNIT_MULTIPLIER),
                "unit_identity": "(663/7)*(7/663)=1",
                "polynomial_variable_support": [],
            },
            "pure_nonzero_constant_entries": len(shear_constant_records),
            "relations_with_a_pure_nonzero_constant_entry": len(shear_relation_ids),
            "entry_position_histogram": dict(sorted(shear_histogram.items())),
            "records": shear_constant_records,
            "independent_records_digest_sha256": _records_digest(shear_constant_records),
            "manifest_records_digest_sha256": _records_digest(manifest_constant_records),
            "manifest_records_equal_independent_records": (
                manifest_constant_records == shear_constant_records
            ),
        },
        "algebraic_conclusion": {
            "coefficient_ring": (
                "QQ[alpha_e,beta_e : 131 actual ON edge orbits]"
            ),
            "raw_CPOBC_ideal": "UNIT_IDEAL",
            "proof": (
                "The full alpha/beta raw Eq. (103) scalar generator 2/117 belongs "
                "to the ideal; multiplication by 117/2 gives 1."
            ),
            "relation_variety_for_this_fixed_state_assignment": "EMPTY",
            "nonsingular_beta_localization_can_restore_a_point": False,
            "D12_localization_can_restore_a_point": False,
            "Q5_localization_can_restore_a_point": False,
            "reason_localizations_do_not_help": (
                "localization preserves 1 in an ideal that is already the unit ideal"
            ),
            "solver_required": False,
        },
        "execution_boundary": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "sage_status": "NOT_INVOKED",
            "finite_field_status": "NOT_RUN",
            "numerical_status": "NOT_RUN",
            "budget_consumed": False,
            "witness": None,
        },
        "scope_exclusions": {
            "this_fixed_harmonic_262_parameter_alpha_beta_chart": "COVERED_EMPTY",
            "other_rank_two_state_assignments": "NOT_COVERED",
            "all_rank_two_state_assignments": "NOT_COVERED",
            "weak_GC_weak_MSR_full_profile": "NOT_COVERED",
            "all_SR2V_branches": "NOT_COVERED",
            "SR2V_terminal_verdict": False,
            "global_commutativity_or_noncommutativity_claim": False,
        },
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "For one fixed harmonic rank-two state assignment, the full 262-parameter "
            "alpha/beta state-native chart has empty raw-CPOBC relation variety by an "
            "exact QQ unit generator. This does not obstruct other rank-two state "
            "assignments, the full weak/weak profile, or SR2-V."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
