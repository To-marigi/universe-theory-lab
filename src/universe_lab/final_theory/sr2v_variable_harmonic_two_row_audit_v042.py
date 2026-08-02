"""Exact variable-harmonic audit of one fixed-k SR2-V obstruction.

The corrected CSG-compatible state-native chart found two raw CPOBC rows
which, for one frozen second harmonic coordinate ``k``, generate the unit
ideal after a required beta localization.  This module independently rebuilds
those rows from the raw ledgers and decides whether that *two-row mechanism*
persists when ``k`` ranges over all harmonic terminal boundary data.

Only exact ``QQ`` arithmetic and small sparse polynomials are used.  The
module does not solve the other 3,130 scalar CPOBC entries and does not issue
an SR2-V terminal verdict.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

RESULT_PATH = "results/v0.4.2_sr2v_variable_harmonic_two_row_audit.json"
CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
WEAK_D2_PATH = "results/v0.4_weak_d2_classification.json"

SCHEMA = "final-theory-v042-sr2v-variable-harmonic-two-row-audit-v1"
VERDICT = (
    "SR2V_FIXED_K_TWO_ROW_OBSTRUCTION_ZARISKI_SPECIAL_"
    "CERTIFIED_NONTERMINAL"
)
SEARCH_TERMINAL = "NOT_AN_SR2V_SEARCH_TERMINAL_TWO_ROW_MECHANISM_ONLY"

PINNED_INPUT_SHA256 = {
    CPOBC_PATH: "8e9498fd6be13ff7553f1e3d2df6919b5a1595294a8feb2134467c63c5c1dda9",
    REDUCTION_PATH: "88363a527e7f015457f51ae94da5ac5e03c83fca588fe07a8bfd9e4fbb0ca52b",
    GC_PATH: "7e884ad9bff83e9e1aba8048759802bcffddd4cffc4e59dbd6b799d4860f93ba",
    EQ112_PATH: "e217862b767eb69c946a5b011d43957c608d1c4748192ce8a5562193ada61678",
    WEAK_D2_PATH: "18e71f439913896fb370944c6479fc358d4d6d0d127162809ba46822ccd2fe65",
}

F_RELATION = "cpobc-relation-ecdf5451a0bcf06c8da5"
G_RELATION = "cpobc-relation-8c0a09869cf24abeac93"
EQUATION = "eq103"
ENTRY = (1, 0)

BETA_U_ORBIT = "cpobc-transition-orbit-92dc21cb80d8c56a73bf"
BETA_V_ORBIT = "cpobc-transition-orbit-983362874bc6f5900920"
ALPHA_E_ORBIT = "cpobc-transition-orbit-e072ba8f219cdc7a6cd0"

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
    product: Matrix = ((_constant(1), {}), ({}, _constant(1)))
    for factor in factors:
        product = _matrix_multiply(product, factor)
    return product


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


def _records_digest(records: Any) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def _evaluate(polynomial: Polynomial, values: dict[str, Fraction]) -> Fraction:
    total = Fraction(0)
    for monomial, coefficient in polynomial.items():
        term = coefficient
        for variable in monomial:
            term *= values[variable]
        total += term
    return total


def _substitute(
    polynomial: Polynomial, replacements: dict[str, Polynomial]
) -> Polynomial:
    result: Polynomial = {}
    for monomial, coefficient in polynomial.items():
        term = _constant(coefficient)
        for variable in monomial:
            term = _multiply(term, replacements.get(variable, _variable(variable)))
        result = _add(result, term)
    return result


def _split_affine_coefficient(
    polynomial: Polynomial, variable: str
) -> tuple[Polynomial, Polynomial]:
    constant: Polynomial = {}
    coefficient: Polynomial = {}
    for monomial, scalar in polynomial.items():
        exponent = monomial.count(variable)
        if exponent == 0:
            constant[monomial] = scalar
        elif exponent == 1:
            reduced = list(monomial)
            reduced.remove(variable)
            coefficient[tuple(reduced)] = scalar
        else:
            raise AssertionError(f"polynomial is not affine in {variable}")
    return constant, coefficient


def _relation_code(rows: tuple[int, ...]) -> int:
    return sum(row << (index * len(rows)) for index, row in enumerate(rows))


def _csg_probability(stage: int, rows: list[int], precursor_code: int) -> Fraction:
    width = precursor_code.bit_count()
    maximal_count = sum(
        1
        for vertex, upper_vertices in enumerate(rows)
        if precursor_code & (1 << vertex) and not int(upper_vertices) & precursor_code
    )
    return Fraction(2 ** (width - maximal_count), 2**stage)


def _build_context(cpobc: dict[str, Any], reduction: dict[str, Any]) -> dict[str, Any]:
    occurrence_records = {
        str(record["occurrence_id"]): record for record in reduction["reduction_map"]
    }
    if len(occurrence_records) != 165:
        raise AssertionError("expected 165 occurrence records")

    by_orbit: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    endpoint_stages: dict[str, int] = {}
    signature_orbits: dict[tuple[int, int, int], str] = {}
    for record in occurrence_records.values():
        orbit = str(record["orbit_id"])
        by_orbit[orbit].append(record)
        source = str(record["source_id"])
        target = str(record["target_id"])
        stage = int(record["stage"])
        for endpoint, expected_stage in ((source, stage), (target, stage + 1)):
            previous = endpoint_stages.setdefault(endpoint, expected_stage)
            if previous != expected_stage:
                raise AssertionError("one endpoint appears at two stages")
        signature = (
            stage,
            _relation_code(tuple(int(row) for row in record["source_relation_rows"])),
            int(record["precursor_code"]),
        )
        previous_orbit = signature_orbits.setdefault(signature, orbit)
        if previous_orbit != orbit:
            raise AssertionError("one quotient signature has two ON orbits")

    edges: dict[str, dict[str, Any]] = {}
    p_by_orbit: dict[str, Fraction] = {}
    for orbit, records in by_orbit.items():
        endpoint_signatures = {
            (str(record["source_id"]), str(record["target_id"]), int(record["stage"]))
            for record in records
        }
        p_values = {
            _csg_probability(
                int(record["stage"]),
                [int(row) for row in record["source_relation_rows"]],
                int(record["precursor_code"]),
            )
            for record in records
        }
        if len(endpoint_signatures) != 1 or len(p_values) != 1:
            raise AssertionError("orbit endpoint or CSG character is not invariant")
        source, target, stage = endpoint_signatures.pop()
        p_value = p_values.pop()
        if not p_value:
            raise AssertionError("actual CSG edge cannot vanish")
        edges[orbit] = {"source": source, "target": target, "stage": stage}
        p_by_orbit[orbit] = p_value
    if len(edges) != 131 or len(endpoint_stages) != 87:
        raise AssertionError("unexpected ON graph census")

    occurrence_orbits = {
        occurrence_id: str(record["orbit_id"])
        for occurrence_id, record in occurrence_records.items()
    }
    outgoing: dict[str, list[dict[str, Any]]] = {}
    identity_coefficients: dict[str, int] = {}
    for constraint in cpobc["MSR_operator_constraints"]:
        source = str(constraint["source_id"])
        identity_coefficients[source] = int(constraint["identity_coefficient"])
        if identity_coefficients[source] != -1:
            raise AssertionError("harmonic recurrence identity coefficient is not -1")
        aggregated: defaultdict[str, int] = defaultdict(int)
        for term in constraint["terms"]:
            orbit = occurrence_orbits[str(term["transition_id"])]
            if edges[orbit]["source"] != source:
                raise AssertionError("MSR occurrence has the wrong source")
            aggregated[orbit] += int(term["coefficient"])
        if not aggregated or any(multiplicity <= 0 for multiplicity in aggregated.values()):
            raise AssertionError("harmonic recurrence multiplicities must be positive")
        outgoing[source] = [
            {
                "orbit": orbit,
                "target": edges[orbit]["target"],
                "multiplicity": multiplicity,
            }
            for orbit, multiplicity in sorted(aggregated.items())
        ]
    if len(outgoing) != 24:
        raise AssertionError("expected 24 nonterminal harmonic recurrences")
    return {
        "occurrence_orbits": occurrence_orbits,
        "signature_orbits": signature_orbits,
        "endpoint_stages": endpoint_stages,
        "edges": edges,
        "p_by_orbit": p_by_orbit,
        "outgoing": outgoing,
        "identity_coefficients": identity_coefficients,
    }


def _path_product_h(gc: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    products: defaultdict[str, set[Fraction]] = defaultdict(set)
    path_count = 0
    for stage_paths in gc["path_inventory"].values():
        for path in stage_paths:
            product = Fraction(1)
            for transition in path["transitions"]:
                signature = transition["quotient_signature"]
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                product *= context["p_by_orbit"][context["signature_orbits"][key]]
            products[str(path["endpoint_causet_id"])].add(product)
            path_count += 1
    failures = {
        endpoint: sorted(str(value) for value in values)
        for endpoint, values in products.items()
        if len(values) != 1
    }
    if failures:
        raise AssertionError("CSG path product depends on path")
    return {
        "h": {endpoint: next(iter(values)) for endpoint, values in products.items()},
        "path_count": path_count,
        "failures": failures,
    }


def _root_weights(context: dict[str, Any]) -> dict[str, int]:
    endpoint_stages: dict[str, int] = context["endpoint_stages"]
    outgoing: dict[str, list[dict[str, Any]]] = context["outgoing"]
    weights: defaultdict[str, int] = defaultdict(int)
    weights["p1-0"] = 1
    for stage in range(1, 5):
        for source in sorted(
            endpoint for endpoint in outgoing if endpoint_stages[endpoint] == stage
        ):
            for term in outgoing[source]:
                weights[term["target"]] += weights[source] * int(term["multiplicity"])
    return {
        endpoint: weights[endpoint]
        for endpoint, stage in sorted(endpoint_stages.items())
        if stage == 5
    }


def _harmonic_extension(
    context: dict[str, Any], boundary: dict[str, Fraction]
) -> dict[str, Fraction]:
    endpoint_stages: dict[str, int] = context["endpoint_stages"]
    outgoing: dict[str, list[dict[str, Any]]] = context["outgoing"]
    terminals = {
        endpoint for endpoint, stage in endpoint_stages.items() if stage == 5
    }
    if set(boundary) != terminals:
        raise AssertionError("terminal boundary inventory changed")
    values = dict(boundary)
    for stage in range(4, 0, -1):
        for source in sorted(
            endpoint for endpoint in outgoing if endpoint_stages[endpoint] == stage
        ):
            values[source] = sum(
                (
                    Fraction(term["multiplicity"]) * values[term["target"]]
                    for term in outgoing[source]
                ),
                start=Fraction(0),
            )
    return values


def _harmonic_failures(
    context: dict[str, Any], values: dict[str, Fraction]
) -> list[str]:
    failures: list[str] = []
    for source, terms in context["outgoing"].items():
        expected = sum(
            (
                Fraction(term["multiplicity"]) * values[term["target"]]
                for term in terms
            ),
            start=Fraction(0),
        )
        if values[source] != expected:
            failures.append(source)
    return failures


def _boundary_vector(
    terminals: list[str], first: str, first_value: int, second: str, second_value: int
) -> dict[str, Fraction]:
    boundary = {terminal: Fraction(0) for terminal in terminals}
    boundary[first] = Fraction(first_value)
    boundary[second] = Fraction(second_value)
    return boundary


def _state_native_matrix_polynomial(
    h_source: Fraction,
    h_target: Fraction,
    k_source: Polynomial,
    k_target: Polynomial,
    orbit: str,
) -> Matrix:
    if not h_source or not h_target:
        raise AssertionError("CSG h coordinates must be nonzero")
    alpha = _variable(f"alpha:{orbit}")
    beta = _variable(f"beta:{orbit}")
    # Direct expansion of F_t [[1,alpha],[0,beta]] F_s^-1.
    return (
        (
            _add(
                _constant(h_target / h_source),
                _scale(-h_target / h_source, _multiply(alpha, k_source)),
            ),
            _scale(h_target, alpha),
        ),
        (
            _add(
                _scale(Fraction(1, 1) / h_source, k_target),
                _add(
                    _scale(
                        Fraction(-1, 1) / h_source,
                        _multiply(_multiply(k_target, k_source), alpha),
                    ),
                    _scale(
                        Fraction(-1, 1) / h_source,
                        _multiply(k_source, beta),
                    ),
                ),
            ),
            _add(_multiply(k_target, alpha), beta),
        ),
    )


def _state_native_matrix(
    source: Vector2, target: Vector2, orbit: str
) -> Matrix:
    h_source, k_source = source
    h_target, k_target = target
    return _state_native_matrix_polynomial(
        h_source,
        h_target,
        _constant(k_source),
        _constant(k_target),
        orbit,
    )


def _selected_row(
    cpobc: dict[str, Any],
    context: dict[str, Any],
    h: dict[str, Fraction],
    k: dict[str, Fraction],
    relation_id: str,
) -> dict[str, Any]:
    relation = next(
        relation for relation in cpobc["relations"] if relation["relation_id"] == relation_id
    )
    equation = next(
        equation
        for equation in relation["raw_noncommutative_relation"]
        if equation["equation_id"] == EQUATION
    )
    needed_occurrences = {
        str(occurrence_id) for occurrence_id in equation["operator_ids"].values()
    }
    matrices: dict[str, Matrix] = {}
    orbit_records: dict[str, str] = {}
    for occurrence_id in needed_occurrences:
        orbit = context["occurrence_orbits"][occurrence_id]
        edge = context["edges"][orbit]
        matrices[occurrence_id] = _state_native_matrix(
            (h[edge["source"]], k[edge["source"]]),
            (h[edge["target"]], k[edge["target"]]),
            orbit,
        )
        orbit_records[occurrence_id] = orbit
    lhs = _matrix_word(
        [matrices[str(equation["operator_ids"][token])] for token in equation["lhs_word"]]
    )
    rhs = _matrix_word(
        [matrices[str(equation["operator_ids"][token])] for token in equation["rhs_word"]]
    )
    polynomial = _matrix_subtract(lhs, rhs)[ENTRY[0]][ENTRY[1]]
    return {
        "relation_id": relation_id,
        "equation_id": EQUATION,
        "entry": list(ENTRY),
        "operator_orbits": dict(sorted(orbit_records.items())),
        "polynomial_internal": polynomial,
        "polynomial": _serialize_polynomial(polynomial),
    }


def _selected_row_symbolic_k(
    cpobc: dict[str, Any],
    context: dict[str, Any],
    h: dict[str, Fraction],
    relation_id: str,
) -> Polynomial:
    relation = next(
        relation for relation in cpobc["relations"] if relation["relation_id"] == relation_id
    )
    equation = next(
        equation
        for equation in relation["raw_noncommutative_relation"]
        if equation["equation_id"] == EQUATION
    )
    matrices: dict[str, Matrix] = {}
    for occurrence_id_value in equation["operator_ids"].values():
        occurrence_id = str(occurrence_id_value)
        orbit = context["occurrence_orbits"][occurrence_id]
        edge = context["edges"][orbit]
        source = str(edge["source"])
        target = str(edge["target"])
        source_k = {} if source == "p1-0" else _variable(f"k:{source}")
        target_k = {} if target == "p1-0" else _variable(f"k:{target}")
        matrices[occurrence_id] = _state_native_matrix_polynomial(
            h[source], h[target], source_k, target_k, orbit
        )
    lhs = _matrix_word(
        [matrices[str(equation["operator_ids"][token])] for token in equation["lhs_word"]]
    )
    rhs = _matrix_word(
        [matrices[str(equation["operator_ids"][token])] for token in equation["rhs_word"]]
    )
    return _matrix_subtract(lhs, rhs)[ENTRY[0]][ENTRY[1]]


def _all_variable_values(context: dict[str, Any]) -> dict[str, Fraction]:
    values: dict[str, Fraction] = {}
    for orbit in context["edges"]:
        values[f"alpha:{orbit}"] = Fraction(0)
        values[f"beta:{orbit}"] = Fraction(1)
    return values


def _supplemental_ledgers(
    eq112: dict[str, Any], weak: dict[str, Any]
) -> dict[str, Any]:
    branches = eq112["path_consistency_branches"]
    derived = len(branches["EQ113_QN_BRANCH"])
    literal = len(branches["EQ113_QN_PLUS_1_BRANCH"])
    eq139 = weak["direct_substitution"]["Eq139"]["branches"]
    strict = eq139["EQ139_PRINTED_STRICT_M_K_LT_N"]["instance_count"]
    completed = eq139["EQ139_EQ145_COMPLETED_M_K_LE_N"]["instance_count"]
    if (derived, literal, strict, completed) != (25, 25, 4, 10):
        raise AssertionError("supplemental branch ledger changed")
    return {
        "Eq113": {
            "derived_Qn_records": derived,
            "literal_Qn_plus_1_records": literal,
            "branches_kept_separate": True,
            "compiled_into_two_row_audit": False,
        },
        "Eq139": {
            "printed_strict_instances": strict,
            "Eq145_completed_instances": completed,
            "domains_kept_separate": True,
            "compiled_into_two_row_audit": False,
        },
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_hashes = {path: _sha256(root / path) for path in PINNED_INPUT_SHA256}
    if input_hashes != PINNED_INPUT_SHA256:
        changed = sorted(
            path for path, digest in input_hashes.items() if digest != PINNED_INPUT_SHA256[path]
        )
        raise AssertionError(f"pinned variable-harmonic input changed: {changed}")

    cpobc = _load(root / CPOBC_PATH)
    reduction = _load(root / REDUCTION_PATH)
    gc = _load(root / GC_PATH)
    eq112 = _load(root / EQ112_PATH)
    weak = _load(root / WEAK_D2_PATH)
    context = _build_context(cpobc, reduction)
    path_data = _path_product_h(gc, context)
    h: dict[str, Fraction] = path_data["h"]
    terminals = sorted(
        endpoint
        for endpoint, stage in context["endpoint_stages"].items()
        if stage == 5
    )
    weights = _root_weights(context)
    if len(terminals) != 63 or set(weights) != set(terminals):
        raise AssertionError("expected 63 terminal boundary coordinates")
    if not all(weights.values()):
        raise AssertionError("root evaluation must be a nonzero linear functional")
    root_weight_reconstruction_failures: list[str] = []
    for terminal in terminals:
        delta_boundary = {item: Fraction(item == terminal) for item in terminals}
        delta_extension = _harmonic_extension(context, delta_boundary)
        if delta_extension["p1-0"] != weights[terminal]:
            root_weight_reconstruction_failures.append(terminal)
    if root_weight_reconstruction_failures:
        raise AssertionError("forward and backward root weights disagree")

    reference = terminals[0]
    root_kernel_basis = [
        {
            "free_terminal": terminal,
            "boundary_nonzero_values": {
                reference: -weights[terminal],
                terminal: weights[reference],
            },
        }
        for terminal in terminals[1:]
    ]
    if len(root_kernel_basis) != 62 or weights[reference] != 1:
        raise AssertionError("root-kernel basis census changed")

    fixed_first, fixed_second = terminals[:2]
    fixed_boundary = _boundary_vector(
        terminals,
        fixed_first,
        weights[fixed_second],
        fixed_second,
        -weights[fixed_first],
    )
    fixed_k = _harmonic_extension(context, fixed_boundary)

    escape_first = min(terminals, key=lambda endpoint: (weights[endpoint], endpoint))
    escape_second = max(terminals, key=lambda endpoint: (weights[endpoint], endpoint))
    escape_boundary = _boundary_vector(
        terminals,
        escape_first,
        weights[escape_second],
        escape_second,
        -weights[escape_first],
    )
    escape_k = _harmonic_extension(context, escape_boundary)

    fixed_f = _selected_row(cpobc, context, h, fixed_k, F_RELATION)
    fixed_g = _selected_row(cpobc, context, h, fixed_k, G_RELATION)
    beta_u = _variable(f"beta:{BETA_U_ORBIT}")
    beta_v = _variable(f"beta:{BETA_V_ORBIT}")
    expected_f = _add(beta_u, _constant(Fraction(1, 8)))
    expected_g = _add(_scale(8, beta_v), _scale(-64, _multiply(beta_u, beta_v)))
    if fixed_f["polynomial_internal"] != expected_f:
        raise AssertionError("fixed-k f row changed")
    if fixed_g["polynomial_internal"] != expected_g:
        raise AssertionError("fixed-k g row changed")

    rho_name = f"rho:beta:{BETA_V_ORBIT}"
    rho = _variable(rho_name)
    localizer = _subtract(_multiply(rho, beta_v), _constant(1))
    unit_identity = _subtract(
        _add(
            _scale(Fraction(1, 16), _multiply(rho, expected_g)),
            _scale(4, _multiply(_multiply(rho, beta_v), expected_f)),
        ),
        localizer,
    )
    if unit_identity != _constant(1):
        raise AssertionError("fixed-k localized unit identity failed")

    escape_f = _selected_row(cpobc, context, h, escape_k, F_RELATION)
    escape_g = _selected_row(cpobc, context, h, escape_k, G_RELATION)
    escape_values = _all_variable_values(context)
    escape_values[f"alpha:{ALPHA_E_ORBIT}"] = Fraction(5, 524)
    escape_values[f"alpha:{BETA_V_ORBIT}"] = Fraction(-179, 6)
    escape_f_value = _evaluate(escape_f["polynomial_internal"], escape_values)
    escape_g_value = _evaluate(escape_g["polynomial_internal"], escape_values)
    if escape_f_value or escape_g_value:
        raise AssertionError("escape harmonic does not solve the selected two rows")

    symbolic_f = _selected_row_symbolic_k(cpobc, context, h, F_RELATION)
    symbolic_g = _selected_row_symbolic_k(cpobc, context, h, G_RELATION)
    f_replacements = {
        f"alpha:{orbit}": (
            _variable(f"alpha:{orbit}") if orbit == ALPHA_E_ORBIT else {}
        )
        for orbit in context["edges"]
    }
    f_replacements.update(
        {f"beta:{orbit}": _constant(1) for orbit in context["edges"]}
    )
    g_replacements = {
        f"alpha:{orbit}": (
            _variable(f"alpha:{orbit}") if orbit == BETA_V_ORBIT else {}
        )
        for orbit in context["edges"]
    }
    g_replacements.update(
        {f"beta:{orbit}": _constant(1) for orbit in context["edges"]}
    )
    universal_f_constant, universal_f_coefficient = _split_affine_coefficient(
        _substitute(symbolic_f, f_replacements),
        f"alpha:{ALPHA_E_ORBIT}",
    )
    universal_g_constant, universal_g_coefficient = _split_affine_coefficient(
        _substitute(symbolic_g, g_replacements),
        f"alpha:{BETA_V_ORBIT}",
    )

    k_p20 = _variable("k:p2-0")
    k_p22 = _variable("k:p2-2")
    k_p3024 = _variable("k:p3-024")
    k_p40044 = _variable("k:p4-0044")
    k_p4004c = _variable("k:p4-004c")
    k_p40002 = _variable("k:p4-0002")
    k_p5000088 = _variable("k:p5-0000088")
    expected_universal_f_constant = _scale(
        Fraction(1, 8),
        _add(
            _add(_scale(8, k_p20), _scale(-1, k_p22)),
            _add(
                _scale(-64, k_p40044),
                _add(_scale(32, k_p4004c), _scale(32, k_p3024)),
            ),
        ),
    )
    expected_universal_f_coefficient = _scale(
        Fraction(1, 8),
        _multiply(k_p3024, _add(k_p22, _scale(64, k_p40044))),
    )
    expected_universal_g_constant = _scale(
        Fraction(1, 2),
        _add(
            _add(_scale(15, k_p4004c), _scale(-15, k_p3024)),
            _add(_scale(-112, k_p5000088), _scale(112, k_p40002)),
        ),
    )
    expected_universal_g_coefficient = _scale(
        Fraction(1, 2),
        _add(
            _add(
                _scale(16, _multiply(k_p4004c, k_p5000088)),
                _multiply(k_p4004c, k_p40002),
            ),
            _add(
                _scale(-16, _multiply(k_p3024, k_p5000088)),
                _add(
                    _scale(-1, _multiply(k_p3024, k_p40002)),
                    _scale(112, _multiply(k_p5000088, k_p40002)),
                ),
            ),
        ),
    )
    if (
        universal_f_constant != expected_universal_f_constant
        or universal_f_coefficient != expected_universal_f_coefficient
        or universal_g_constant != expected_universal_g_constant
        or universal_g_coefficient != expected_universal_g_coefficient
    ):
        raise AssertionError("universal selected-row formula changed")
    universal_open_determinant = _multiply(
        universal_f_coefficient, universal_g_coefficient
    )
    escape_k_values = {
        f"k:{endpoint}": value for endpoint, value in escape_k.items()
    }
    fixed_k_values = {f"k:{endpoint}": value for endpoint, value in fixed_k.items()}
    universal_evaluation = {
        "F0_fixed": _evaluate(universal_f_constant, fixed_k_values),
        "Cf_fixed": _evaluate(universal_f_coefficient, fixed_k_values),
        "G0_fixed": _evaluate(universal_g_constant, fixed_k_values),
        "Cg_fixed": _evaluate(universal_g_coefficient, fixed_k_values),
        "Delta_fixed": _evaluate(universal_open_determinant, fixed_k_values),
        "F0_escape": _evaluate(universal_f_constant, escape_k_values),
        "Cf_escape": _evaluate(universal_f_coefficient, escape_k_values),
        "G0_escape": _evaluate(universal_g_constant, escape_k_values),
        "Cg_escape": _evaluate(universal_g_coefficient, escape_k_values),
        "Delta_escape": _evaluate(universal_open_determinant, escape_k_values),
    }

    coefficient_values = _all_variable_values(context)
    f_constant = _evaluate(escape_f["polynomial_internal"], coefficient_values)
    coefficient_values[f"alpha:{ALPHA_E_ORBIT}"] = Fraction(1)
    f_with_alpha = _evaluate(escape_f["polynomial_internal"], coefficient_values)
    coefficient_f = f_with_alpha - f_constant

    coefficient_values = _all_variable_values(context)
    g_constant = _evaluate(escape_g["polynomial_internal"], coefficient_values)
    coefficient_values[f"alpha:{BETA_V_ORBIT}"] = Fraction(1)
    g_with_alpha = _evaluate(escape_g["polynomial_internal"], coefficient_values)
    coefficient_g = g_with_alpha - g_constant
    open_determinant = coefficient_f * coefficient_g
    if (
        f_constant,
        coefficient_f,
        g_constant,
        coefficient_g,
        open_determinant,
    ) != (
        Fraction(-5, 8),
        Fraction(131, 2),
        Fraction(-179, 2),
        Fraction(-3),
        Fraction(-393, 2),
    ):
        raise AssertionError("generic-open coefficient certificate changed")
    if universal_evaluation != {
        "F0_fixed": Fraction(9, 8),
        "Cf_fixed": Fraction(0),
        "G0_fixed": Fraction(-56),
        "Cg_fixed": Fraction(0),
        "Delta_fixed": Fraction(0),
        "F0_escape": Fraction(-5, 8),
        "Cf_escape": Fraction(131, 2),
        "G0_escape": Fraction(-179, 2),
        "Cg_escape": Fraction(-3),
        "Delta_escape": Fraction(-393, 2),
    }:
        raise AssertionError("universal selected-row evaluation changed")

    # Variables chosen for the two rational solves are structurally disjoint:
    # alpha_E does not occur in g, and alpha_V does not occur in f.
    f_variables = {
        variable
        for monomial in escape_f["polynomial_internal"]
        for variable in monomial
    }
    g_variables = {
        variable
        for monomial in escape_g["polynomial_internal"]
        for variable in monomial
    }
    cross_support_failures = []
    if f"alpha:{BETA_V_ORBIT}" in f_variables:
        cross_support_failures.append("alpha_V_occurs_in_f")
    if f"alpha:{ALPHA_E_ORBIT}" in g_variables:
        cross_support_failures.append("alpha_E_occurs_in_g")

    fixed_support_determinant = next(
        h[terminal] * fixed_k[other] - fixed_k[terminal] * h[other]
        for terminal in terminals
        for other in terminals
        if h[terminal] * fixed_k[other] - fixed_k[terminal] * h[other]
    )
    escape_support_determinant = next(
        h[terminal] * escape_k[other] - escape_k[terminal] * h[other]
        for terminal in terminals
        for other in terminals
        if h[terminal] * escape_k[other] - escape_k[terminal] * h[other]
    )

    raw_equation_count = sum(
        len(relation["raw_noncommutative_relation"]) for relation in cpobc["relations"]
    )
    supplemental = _supplemental_ledgers(eq112, weak)
    root_weight_records = [
        {"terminal": terminal, "root_path_multiplicity": weights[terminal]}
        for terminal in terminals
    ]
    fixed_state_records = [
        {"endpoint": endpoint, "h": str(h[endpoint]), "k": str(fixed_k[endpoint])}
        for endpoint in sorted(h)
    ]
    escape_state_records = [
        {"endpoint": endpoint, "h": str(h[endpoint]), "k": str(escape_k[endpoint])}
        for endpoint in sorted(h)
    ]

    gates = {
        "all_five_input_SHA256_bindings_hold": input_hashes == PINNED_INPUT_SHA256,
        "harmonic_recurrence_matrix_has_24_unit_pivots": len(context["outgoing"]) == 24,
        "all_MSR_identity_coefficients_are_minus_one_and_multiplicities_positive": all(
            coefficient == -1 for coefficient in context["identity_coefficients"].values()
        )
        and all(
            int(term["multiplicity"]) > 0
            for terms in context["outgoing"].values()
            for term in terms
        ),
        "terminal_restriction_identifies_H_with_Q63": len(terminals) == 63,
        "root_evaluation_is_nonzero_and_kernel_basis_has_dimension_62": bool(weights)
        and len(root_kernel_basis) == 62
        and not root_weight_reconstruction_failures,
        "CSG_h_has_root_one_and_is_harmonic": h["p1-0"] == 1
        and not _harmonic_failures(context, h),
        "fixed_and_escape_k_are_root_zero_harmonic_rank2": fixed_k["p1-0"] == 0
        and escape_k["p1-0"] == 0
        and not _harmonic_failures(context, fixed_k)
        and not _harmonic_failures(context, escape_k)
        and fixed_support_determinant != 0
        and escape_support_determinant != 0,
        "fixed_k_two_raw_rows_equal_f_and_g": fixed_f["polynomial_internal"] == expected_f
        and fixed_g["polynomial_internal"] == expected_g,
        "fixed_k_two_rows_plus_beta_v_localizer_generate_one": unit_identity
        == _constant(1),
        "escape_k_solves_both_rows_with_all_betas_nonzero": escape_f_value == 0
        and escape_g_value == 0
        and all(
            value
            for variable, value in escape_values.items()
            if variable.startswith("beta:")
        ),
        "nonempty_open_rational_section_has_nonzero_diagonal_coefficient_determinant": (
            open_determinant != 0 and not cross_support_failures
        ),
        "universal_small_F0_Cf_G0_Cg_formulas_reconstruct_exactly": (
            universal_f_constant == expected_universal_f_constant
            and universal_f_coefficient == expected_universal_f_coefficient
            and universal_g_constant == expected_universal_g_constant
            and universal_g_coefficient == expected_universal_g_coefficient
            and universal_evaluation["Delta_escape"] != 0
        ),
        "Eq113_and_Eq139_semantic_branches_remain_separate": supplemental["Eq113"][
            "branches_kept_separate"
        ]
        and supplemental["Eq139"]["domains_kept_separate"],
    }
    if not all(gates.values()):
        failed = sorted(name for name, passed in gates.items() if not passed)
        raise AssertionError(f"variable-harmonic two-row gate failed: {failed}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_slice": (
            "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON__"
            "normalized_CSG_primary_h__variable_harmonic_secondary_k"
        ),
        "input_artifacts": input_hashes,
        "exact_harmonic_space": {
            "endpoint_count": len(context["endpoint_stages"]),
            "nonterminal_recurrence_count": len(context["outgoing"]),
            "terminal_boundary_coordinate_count": len(terminals),
            "recurrence_pivot_coefficient": "1",
            "identity_coefficients": sorted(
                set(context["identity_coefficients"].values())
            ),
            "transition_multiplicities_are_positive": True,
            "dimension_H": 63,
            "terminal_restriction": "H -> Q^63 is an exact linear isomorphism",
            "root_evaluation": "sum_T root_path_multiplicity(T)*boundary(T)",
            "root_weight_records": root_weight_records,
            "root_weight_records_digest_sha256": _records_digest(root_weight_records),
            "root_weight_reconstruction_failures": root_weight_reconstruction_failures,
            "root_kernel_basis_count": len(root_kernel_basis),
            "root_kernel_basis": root_kernel_basis,
            "root_kernel_basis_digest_sha256": _records_digest(root_kernel_basis),
            "dimension_kernel_ev_root": 62,
        },
        "dimension_and_gauge_ledger": {
            "ordered_root_normalized_pair": {
                "conditions": "h(root)=1, k(root)=0",
                "dimension": 124,
                "rank2_condition": "Zariski-open linear-independence condition",
            },
            "global_basis_gauge_preserving_Omega_e1": {
                "action": "h -> h+a*k, k -> b*k",
                "parameters": "a in G_a, b in G_m",
                "dimension": 2,
            },
            "all_rank2_state_assignment_moduli": {
                "identification": "open subset of Gr(2,H)=Gr(2,63)",
                "dimension": 122,
            },
            "CSG_h_fixed_family": {
                "before_residual_scaling": "ker(ev_root) minus {0}",
                "dimension_before_scaling": 62,
                "residual_gauge": "k -> b*k, b in G_m",
                "moduli_identification": "P(ker(ev_root)) = P^61",
                "dimension_after_scaling": 61,
                "covers_all_rank2_state_assignments": False,
            },
        },
        "fixed_k_localized_obstruction": {
            "boundary_support": {
                fixed_first: str(fixed_boundary[fixed_first]),
                fixed_second: str(fixed_boundary[fixed_second]),
            },
            "state_records_digest_sha256": _records_digest(fixed_state_records),
            "rank2_support_determinant": str(fixed_support_determinant),
            "f_raw_row": {
                key: value for key, value in fixed_f.items() if key != "polynomial_internal"
            },
            "g_raw_row": {
                key: value for key, value in fixed_g.items() if key != "polynomial_internal"
            },
            "f_formula": f"beta:{BETA_U_ORBIT} + 1/8",
            "g_formula": (
                f"8*beta:{BETA_V_ORBIT} - 64*beta:{BETA_U_ORBIT}*"
                f"beta:{BETA_V_ORBIT}"
            ),
            "localizer": f"{rho_name}*beta:{BETA_V_ORBIT} - 1",
            "unit_identity": "1=(rho/16)*g+4*rho*beta_v*f-localizer",
            "unit_identity_residual": _serialize_polynomial(
                _subtract(unit_identity, _constant(1))
            ),
            "classification": "VALID_FOR_THIS_FIXED_K_NONSINGULAR_SLICE",
        },
        "escape_k_certificate": {
            "boundary_support": {
                escape_first: str(escape_boundary[escape_first]),
                escape_second: str(escape_boundary[escape_second]),
            },
            "state_records_digest_sha256": _records_digest(escape_state_records),
            "rank2_support_determinant": str(escape_support_determinant),
            "f_raw_row": {
                key: value for key, value in escape_f.items() if key != "polynomial_internal"
            },
            "g_raw_row": {
                key: value for key, value in escape_g.items() if key != "polynomial_internal"
            },
            "assignment": {
                "all_beta": "1",
                "all_unlisted_alpha": "0",
                f"alpha:{ALPHA_E_ORBIT}": "5/524",
                f"alpha:{BETA_V_ORBIT}": "-179/6",
            },
            "f_value": str(escape_f_value),
            "g_value": str(escape_g_value),
            "all_131_beta_values_nonzero": True,
            "selected_two_row_localized_ideal_is_proper": True,
            "full_CPOBC_solution_claimed": False,
        },
        "nonempty_Zariski_open_failure_of_the_fixed_k_mechanism": {
            "specialization": "all beta=1; all alpha=0 except alpha_E in f and alpha_V in g",
            "f_constant_at_escape": str(f_constant),
            "coefficient_of_alpha_E_at_escape": str(coefficient_f),
            "g_constant_at_escape": str(g_constant),
            "coefficient_of_alpha_V_at_escape": str(coefficient_g),
            "cross_support_failures": cross_support_failures,
            "diagonal_coefficient_determinant_at_escape": str(open_determinant),
            "universal_small_formula": {
                "endpoint_variable_convention": "K_c=k(c)",
                "F0": (
                    "(8*K_p2-0 - K_p2-2 - 64*K_p4-0044 + "
                    "32*K_p4-004c + 32*K_p3-024)/8"
                ),
                "Cf": "K_p3-024*(K_p2-2 + 64*K_p4-0044)/8",
                "G0": (
                    "(15*K_p4-004c - 15*K_p3-024 - 112*K_p5-0000088 + "
                    "112*K_p4-0002)/2"
                ),
                "Cg": (
                    "(16*K_p4-004c*K_p5-0000088 + K_p4-004c*K_p4-0002 - "
                    "16*K_p3-024*K_p5-0000088 - K_p3-024*K_p4-0002 + "
                    "112*K_p5-0000088*K_p4-0002)/2"
                ),
                "Delta": "Cf*Cg",
                "F0_polynomial": _serialize_polynomial(universal_f_constant),
                "Cf_polynomial": _serialize_polynomial(universal_f_coefficient),
                "G0_polynomial": _serialize_polynomial(universal_g_constant),
                "Cg_polynomial": _serialize_polynomial(universal_g_coefficient),
                "Delta_polynomial": _serialize_polynomial(universal_open_determinant),
                "records_digest_sha256": _records_digest(
                    {
                        "F0": _serialize_polynomial(universal_f_constant),
                        "Cf": _serialize_polynomial(universal_f_coefficient),
                        "G0": _serialize_polynomial(universal_g_constant),
                        "Cg": _serialize_polynomial(universal_g_coefficient),
                        "Delta": _serialize_polynomial(universal_open_determinant),
                    }
                ),
                "evaluations": {
                    key: str(value) for key, value in universal_evaluation.items()
                },
            },
            "open_condition": "C_f(k)*C_g(k) != 0 on ker(ev_root)",
            "rational_section": "alpha_E=-F_0(k)/C_f(k), alpha_V=-G_0(k)/C_g(k)",
            "proof": (
                "Every row coefficient is a regular polynomial in terminal boundary k. "
                "The displayed nonzero value proves C_f*C_g is not the zero polynomial. "
                "On its nonempty principal open the two structurally disjoint affine "
                "alpha variables solve the rows with every beta equal to one."
            ),
        },
        "classification": {
            "fixed_k_choice_dependent_special_phenomenon": True,
            "Zariski_generic_in_CSG_h_fixed_k_family": False,
            "valid_for_all_harmonic_k": False,
            "answer": "CASE_I_K_CHOICE_DEPENDENT_ZARISKI_SPECIAL",
        },
        "raw_inventory": {
            "actual_ON_orbits": len(context["edges"]),
            "fixed_vector_GC_path_count_used_for_CSG_h": path_data["path_count"],
            "CSG_h_path_independence_failures": path_data["failures"],
            "raw_CPOBC_operator_equations": raw_equation_count,
            "raw_CPOBC_scalar_entries": 4 * raw_equation_count,
            "rows_used_by_this_audit": 2,
            "remaining_scalar_entries_not_solved": 4 * raw_equation_count - 2,
        },
        "separate_unresolved_ledgers": supplemental,
        "scope_exclusions": {
            "other_3130_raw_CPOBC_scalar_entries": "UNRESOLVED",
            "full_783_equation_relation_variety": "UNRESOLVED",
            "full_CSG_h_fixed_P61_family": "NOT_CLASSIFIED_BEYOND_TWO_ROWS",
            "all_rank2_state_assignments_Gr2_63_open": "NOT_COVERED",
            "supplemental_Q5": "UNRESOLVED_NOT_COMPILED",
            "Eq113_both_branches": "UNRESOLVED_NOT_COMPILED",
            "Eq139_both_domains": "UNRESOLVED_NOT_COMPILED",
            "commutativity_or_noncommutativity": "NOT_DECIDED",
            "SR2V_terminal_verdict": False,
        },
        "execution": {
            "solver": "NOT_RUN",
            "groebner": "NOT_RUN",
            "sage": "NOT_INVOKED",
            "finite_field": "NOT_RUN",
            "numerical": "NOT_RUN",
            "arithmetic": "EXACT_QQ_SPARSE_SYMBOLIC_ONLY",
        },
        "gates": gates,
        "passed": True,
        "verdict": VERDICT,
        "search_terminal": SEARCH_TERMINAL,
        "claim_boundary": (
            "The localized two-row unit certificate is exact for the frozen first-two-"
            "terminal k, but it is a Zariski-special k-choice mechanism. An exact "
            "rank-two harmonic escape k and a nonempty open rational section solve "
            "those same two rows with all betas nonzero. This does not exhibit a full "
            "CPOBC point or settle any larger state-assignment family."
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
