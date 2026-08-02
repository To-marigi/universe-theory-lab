"""Corrected CSG-compatible state-native rank-two chart for SR2-V.

The former uniform-terminal harmonic slice is incompatible with raw CPOBC.
This module instead reconstructs the normalized ``t_j=1`` CSG character
``p_e`` and defines the first reachable coordinate by path products.  An
independent harmonic second coordinate gives exact reachable rank two.

For each actual ON edge ``e:s->t`` the complete affine fibre of matrices
mapping the fixed source state to the fixed target state is

``A_e = F_t * [[1, alpha_e], [0, beta_e]] * F_s^-1``.

All 783 raw CPOBC equations are expanded with custom sparse ``QQ`` arithmetic.
The old one-row constant obstruction disappears, but two alpha-free raw rows
and one required beta localizer give an exact unit identity on the nonsingular
locus.  This is an obstruction for the selected fixed ``(h,k)`` slice only.
No solver is imported or invoked.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import sympy as sp
from sympy.matrices.normalforms import smith_normal_form
from sympy.polys.domains import ZZ

RESULT_PATH = "results/v0.4.2_sr2v_corrected_csg_fixed_hk_obstruction.json"
CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
WEAK_D2_PATH = "results/v0.4_weak_d2_classification.json"

SCHEMA = "final-theory-v042-sr2v-corrected-csg-fixed-hk-nonsingular-obstruction-v1"
VERDICT = (
    "SR2V_CORRECTED_CSG_FIXED_HK_NONSINGULAR_CPOBC_UNIT_IDEAL_"
    "OBSTRUCTION_CERTIFIED_NO_SOLVER_RUN"
)
SEARCH_TERMINAL = "CORRECTED_CSG_FIXED_HK_NONSINGULAR_SLICE_TERMINAL_ONLY"

PINNED_INPUT_SHA256 = {
    CPOBC_PATH: "8e9498fd6be13ff7553f1e3d2df6919b5a1595294a8feb2134467c63c5c1dda9",
    REDUCTION_PATH: "88363a527e7f015457f51ae94da5ac5e03c83fca588fe07a8bfd9e4fbb0ca52b",
    GC_PATH: "7e884ad9bff83e9e1aba8048759802bcffddd4cffc4e59dbd6b799d4860f93ba",
    EQ112_PATH: "e217862b767eb69c946a5b011d43957c608d1c4748192ce8a5562193ada61678",
    WEAK_D2_PATH: "18e71f439913896fb370944c6479fc358d4d6d0d127162809ba46822ccd2fe65",
}

OLD_FULL_UNIT_RELATION = "cpobc-relation-0ca7a22bed9cdf4bc14a"
OLD_FULL_UNIT_EQUATION = "eq103"
OLD_FULL_UNIT_ENTRY = (0, 0)
OLD_SHEAR_UNIT_RELATION = "cpobc-relation-1decb1e77431d5355ada"
OLD_SHEAR_UNIT_EQUATION = "eq103"
OLD_SHEAR_UNIT_ENTRY = (1, 0)

TWO_ROW_F_RELATION = "cpobc-relation-ecdf5451a0bcf06c8da5"
TWO_ROW_F_EQUATION = "eq103"
TWO_ROW_F_ENTRY = (1, 0)
TWO_ROW_G_RELATION = "cpobc-relation-8c0a09869cf24abeac93"
TWO_ROW_G_EQUATION = "eq103"
TWO_ROW_G_ENTRY = (1, 0)
BETA_U_ORBIT = "cpobc-transition-orbit-92dc21cb80d8c56a73bf"
BETA_V_ORBIT = "cpobc-transition-orbit-983362874bc6f5900920"
RHO_V = "rho:beta:cpobc-transition-orbit-983362874bc6f5900920"

Monomial = tuple[str, ...]
Polynomial = dict[Monomial, Fraction]
Matrix = tuple[tuple[Polynomial, Polynomial], tuple[Polynomial, Polynomial]]
Vector = tuple[Polynomial, Polynomial]
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


def _matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
    return (
        _add(_multiply(matrix[0][0], vector[0]), _multiply(matrix[0][1], vector[1])),
        _add(_multiply(matrix[1][0], vector[0]), _multiply(matrix[1][1], vector[1])),
    )


def _vector_add(left: Vector, right: Vector) -> Vector:
    return (_add(left[0], right[0]), _add(left[1], right[1]))


def _vector_scale(coefficient: Fraction | int, vector: Vector) -> Vector:
    return (_scale(coefficient, vector[0]), _scale(coefficient, vector[1]))


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


def _serialize_matrix(matrix: Matrix) -> dict[str, list[dict[str, Any]]]:
    return {
        f"{row}{column}": _serialize_polynomial(matrix[row][column])
        for row in range(2)
        for column in range(2)
    }


def _serialize_vector(vector: Vector) -> dict[str, list[dict[str, Any]]]:
    return {str(index): _serialize_polynomial(vector[index]) for index in range(2)}


def _records_digest(records: Any) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


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


def _build_context(
    cpobc: dict[str, Any],
    reduction: dict[str, Any],
) -> dict[str, Any]:
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
        signatures = {
            (str(record["source_id"]), str(record["target_id"]), int(record["stage"]))
            for record in records
        }
        if len(signatures) != 1:
            raise AssertionError("one ON orbit has multiple endpoint signatures")
        p_values = {
            _csg_probability(
                int(record["stage"]),
                [int(row) for row in record["source_relation_rows"]],
                int(record["precursor_code"]),
            )
            for record in records
        }
        if len(p_values) != 1:
            raise AssertionError("normalized CSG character is not ON-orbit invariant")
        source, target, stage = signatures.pop()
        p_value = p_values.pop()
        if not p_value:
            raise AssertionError("normalized CSG character has a zero actual edge")
        edges[orbit] = {
            "source": source,
            "target": target,
            "stage": stage,
            "occurrence_ids": sorted(str(record["occurrence_id"]) for record in records),
        }
        p_by_orbit[orbit] = p_value
    if len(edges) != 131:
        raise AssertionError("expected 131 actual ON edge orbits")

    occurrence_orbits = {
        occurrence_id: str(record["orbit_id"])
        for occurrence_id, record in occurrence_records.items()
    }
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
        raise AssertionError("expected 24 nonterminal sources")
    return {
        "occurrence_records": occurrence_records,
        "occurrence_orbits": occurrence_orbits,
        "signature_orbits": signature_orbits,
        "endpoint_stages": endpoint_stages,
        "edges": edges,
        "p_by_orbit": p_by_orbit,
        "outgoing": outgoing,
    }


def _path_product_states(
    gc: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    products_by_endpoint: defaultdict[str, set[Fraction]] = defaultdict(set)
    path_records: list[dict[str, Any]] = []
    for stage_paths in gc["path_inventory"].values():
        for path in stage_paths:
            product = Fraction(1)
            orbit_sequence: list[str] = []
            for transition in path["transitions"]:
                signature = transition["quotient_signature"]
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                orbit = context["signature_orbits"][key]
                product *= context["p_by_orbit"][orbit]
                orbit_sequence.append(orbit)
            endpoint = str(path["endpoint_causet_id"])
            products_by_endpoint[endpoint].add(product)
            path_records.append(
                {
                    "path_id": str(path["path_id"]),
                    "endpoint_id": endpoint,
                    "endpoint_stage": int(path["endpoint_stage"]),
                    "orbit_sequence": orbit_sequence,
                    "product": str(product),
                }
            )
    path_independence_failures = {
        endpoint: sorted(str(value) for value in values)
        for endpoint, values in products_by_endpoint.items()
        if len(values) != 1
    }
    if path_independence_failures:
        raise AssertionError("normalized CSG path product is endpoint dependent")
    h = {endpoint: next(iter(values)) for endpoint, values in products_by_endpoint.items()}
    return {
        "h": h,
        "path_records": path_records,
        "path_independence_failures": path_independence_failures,
    }


def _independent_harmonic_coordinate(context: dict[str, Any]) -> dict[str, Any]:
    endpoint_stages: dict[str, int] = context["endpoint_stages"]
    outgoing: dict[str, list[dict[str, Any]]] = context["outgoing"]
    roots = sorted(endpoint for endpoint, stage in endpoint_stages.items() if stage == 1)
    terminals = sorted(endpoint for endpoint, stage in endpoint_stages.items() if stage == 5)
    if roots != ["p1-0"]:
        raise AssertionError("expected unique root p1-0")
    root = roots[0]

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
    # Freeze a deterministic independent boundary vector on the first two
    # terminal coordinates.  Their root weights make the root value cancel:
    # w_1*w_2 + w_2*(-w_1) = 0.
    first_terminal, second_terminal = terminals[:2]
    if first_terminal == second_terminal:
        raise AssertionError("two support terminals are required")

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
    failures: list[str] = []
    for source, terms in outgoing.items():
        expected = sum(
            (
                Fraction(term["multiplicity"]) * k[term["target"]]
                for term in terms
            ),
            start=Fraction(0),
        )
        if k[source] != expected:
            failures.append(source)
    return {
        "k": k,
        "root": root,
        "terminal_weights": terminal_weights,
        "support_terminals": [first_terminal, second_terminal],
        "harmonic_failures": failures,
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
        raise AssertionError("state-native frames require nonzero h coordinates")
    source_frame_inverse = _matrix_constant(
        (
            (Fraction(1) / h_source, Fraction(0)),
            (-k_source / h_source, Fraction(1)),
        )
    )
    target_frame = _matrix_constant(
        ((h_target, Fraction(0)), (k_target, Fraction(1)))
    )
    beta = _constant(1) if beta_is_one else _variable(f"beta:{orbit}")
    local_matrix: Matrix = (
        (_constant(1), _variable(f"alpha:{orbit}")),
        (_constant(0), beta),
    )
    return _matrix_multiply(
        _matrix_multiply(target_frame, local_matrix),
        source_frame_inverse,
    )


def _frame_inverse_checks(states: dict[str, Vector2]) -> list[str]:
    failures: list[str] = []
    for endpoint, (h, k) in states.items():
        frame = _matrix_constant(((h, Fraction(0)), (k, Fraction(1))))
        inverse = _matrix_constant(
            ((Fraction(1) / h, Fraction(0)), (-k / h, Fraction(1)))
        )
        if _matrix_multiply(frame, inverse) != _identity() or _matrix_multiply(
            inverse, frame
        ) != _identity():
            failures.append(endpoint)
    return failures


def _term_census(polynomials: list[Polynomial]) -> dict[str, Any]:
    term_counts = [len(polynomial) for polynomial in polynomials]
    degrees = [len(monomial) for polynomial in polynomials for monomial in polynomial]
    return {
        "scalar_entries": len(polynomials),
        "zero_entries": sum(not polynomial for polynomial in polynomials),
        "nonzero_entries": sum(bool(polynomial) for polynomial in polynomials),
        "total_terms": sum(term_counts),
        "maximum_terms_in_one_entry": max(term_counts, default=0),
        "maximum_total_degree": max(degrees, default=0),
        "entries_with_nonzero_constant_coefficient": sum(
            bool(polynomial.get((), Fraction(0))) for polynomial in polynomials
        ),
        "pure_nonzero_constant_entries": sum(
            set(polynomial) == {()} and bool(polynomial[()]) for polynomial in polynomials
        ),
    }


def _expand_raw_cpobc(
    cpobc: dict[str, Any],
    occurrence_matrices: dict[str, Matrix],
    tracked_entries: set[tuple[str, str, int, int]],
    *,
    retain_all_records: bool,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    all_entries: list[Polynomial] = []
    pure_constants: list[dict[str, Any]] = []
    alpha_free_records: list[dict[str, Any]] = []
    tracked: dict[str, dict[str, Any]] = {}
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
            entries = [residual[row][column] for row in range(2) for column in range(2)]
            all_entries.extend(entries)
            if retain_all_records:
                records.append(
                    {
                        "relation_id": relation_id,
                        "equation_id": equation_id,
                        "lhs_word_length": len(equation["lhs_word"]),
                        "rhs_word_length": len(equation["rhs_word"]),
                        "entries": _serialize_matrix(residual),
                    }
                )
            for row in range(2):
                for column in range(2):
                    polynomial = residual[row][column]
                    if set(polynomial) == {()} and polynomial[()]:
                        pure_constants.append(
                            {
                                "relation_id": relation_id,
                                "equation_id": equation_id,
                                "entry": [row, column],
                                "value": str(polynomial[()]),
                            }
                        )
                    if polynomial and not any(
                        variable.startswith("alpha:")
                        for monomial in polynomial
                        for variable in monomial
                    ):
                        alpha_free_records.append(
                            {
                                "relation_id": relation_id,
                                "equation_id": equation_id,
                                "entry": [row, column],
                                "polynomial": _serialize_polynomial(polynomial),
                            }
                        )
                    key = (relation_id, equation_id, row, column)
                    if key in tracked_entries:
                        tracked["|".join(map(str, key))] = {
                            "relation_id": relation_id,
                            "equation_id": equation_id,
                            "entry": [row, column],
                            "polynomial": _serialize_polynomial(polynomial),
                            "constant_coefficient": str(polynomial.get((), Fraction(0))),
                            "is_zero_polynomial": not polynomial,
                            "is_pure_nonzero_constant": (
                                set(polynomial) == {()} and bool(polynomial[()])
                            ),
                        }
    pure_constants.sort(
        key=lambda record: (
            record["relation_id"],
            record["equation_id"],
            record["entry"][0],
            record["entry"][1],
        )
    )
    return {
        "records": records,
        "records_digest_sha256": _records_digest(records),
        "term_census": _term_census(all_entries),
        "pure_constant_records": pure_constants,
        "pure_constant_records_digest_sha256": _records_digest(pure_constants),
        "alpha_free_nonzero_records": alpha_free_records,
        "alpha_free_nonzero_records_digest_sha256": _records_digest(alpha_free_records),
        "tracked_entries": tracked,
        "equation_count": len(all_entries) // 4,
    }


def _alpha_free_exponent_lattice(
    records: list[dict[str, Any]],
    beta_variables: list[str],
) -> dict[str, Any]:
    variable_index = {variable: index for index, variable in enumerate(beta_variables)}
    exponent_rows: list[list[int]] = []
    degree_histogram: Counter[int] = Counter()
    term_count = 0
    for record in records:
        polynomial = _deserialize_polynomial(record["polynomial"])
        if len(polynomial) != 2:
            raise AssertionError("an alpha-free CPOBC row is not binomial")
        monomials = sorted(polynomial)
        term_count += len(monomials)
        degree_histogram[max(len(monomial) for monomial in monomials)] += 1
        exponent_vectors: list[list[int]] = []
        for monomial in monomials:
            vector = [0] * len(beta_variables)
            for variable in monomial:
                vector[variable_index[variable]] += 1
            exponent_vectors.append(vector)
        exponent_rows.append(
            [left - right for left, right in zip(*exponent_vectors, strict=True)]
        )
    matrix = sp.Matrix(exponent_rows)
    rank = int(matrix.rank())
    smith = smith_normal_form(matrix, domain=ZZ)
    smith_diagonal = [
        abs(int(smith[index, index]))
        for index in range(min(smith.shape))
        if smith[index, index]
    ]
    return {
        "row_count": len(records),
        "variable_count": len(beta_variables),
        "all_rows_binomial": all(
            len(_deserialize_polynomial(record["polynomial"])) == 2
            for record in records
        ),
        "total_terms": term_count,
        "maximum_degree_histogram": {
            str(degree): count for degree, count in sorted(degree_histogram.items())
        },
        "variable_order": beta_variables,
        "variable_order_digest_sha256": _records_digest(beta_variables),
        "exponent_difference_matrix": exponent_rows,
        "exponent_difference_matrix_digest_sha256": _records_digest(exponent_rows),
        "audited_rows_digest_sha256": _records_digest(records),
        "rank": rank,
        "nullity": len(beta_variables) - rank,
        "smith_nonzero_diagonal": smith_diagonal,
        "smith_factor_histogram": {
            str(factor): count for factor, count in sorted(Counter(smith_diagonal).items())
        },
    }


def _supplemental_ledgers(
    eq112: dict[str, Any],
    weak: dict[str, Any],
) -> dict[str, Any]:
    branches = eq112["path_consistency_branches"]
    if len(branches["EQ113_QN_BRANCH"]) != 25 or len(
        branches["EQ113_QN_PLUS_1_BRANCH"]
    ) != 25:
        raise AssertionError("Eq. (113) branch census changed")
    eq139 = weak["direct_substitution"]["Eq139"]["branches"]
    strict = eq139["EQ139_PRINTED_STRICT_M_K_LT_N"]["instance_count"]
    completed = eq139["EQ139_EQ145_COMPLETED_M_K_LE_N"]["instance_count"]
    if strict != 4 or completed != 10:
        raise AssertionError("Eq. (139) domain census changed")
    return {
        "Eq113": {
            "derived_Qn_records": 25,
            "literal_Qn_plus_1_records": 25,
            "branches_kept_separate": True,
            "status_on_corrected_chart": "UNRESOLVED_NOT_COMPILED",
        },
        "Eq139": {
            "printed_strict_instances": 4,
            "Eq145_completed_instances": 10,
            "domains_kept_separate": True,
            "status_on_corrected_chart": "UNRESOLVED_NOT_COMPILED",
        },
    }


def build_payload(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_hashes = {path: _sha256(root / path) for path in PINNED_INPUT_SHA256}
    if input_hashes != PINNED_INPUT_SHA256:
        changed = sorted(
            path for path, digest in input_hashes.items() if digest != PINNED_INPUT_SHA256[path]
        )
        raise AssertionError(f"pinned corrected-chart input changed: {changed}")
    cpobc = _load(root / CPOBC_PATH)
    reduction = _load(root / REDUCTION_PATH)
    gc = _load(root / GC_PATH)
    eq112 = _load(root / EQ112_PATH)
    weak = _load(root / WEAK_D2_PATH)
    if not all(artifact.get("passed") is True for artifact in (cpobc, reduction, gc, eq112)):
        raise AssertionError("one corrected-chart source artifact did not pass")

    context = _build_context(cpobc, reduction)
    path_data = _path_product_states(gc, context)
    h: dict[str, Fraction] = path_data["h"]
    harmonic = _independent_harmonic_coordinate(context)
    k: dict[str, Fraction] = harmonic["k"]
    if set(h) != set(k) or set(h) != set(context["endpoint_stages"]):
        raise AssertionError("h, k, and endpoint inventories differ")
    states = {endpoint: (h[endpoint], k[endpoint]) for endpoint in sorted(h)}

    edge_character_failures: list[str] = []
    h_harmonic_failures: list[str] = []
    csg_msr_failures: list[str] = []
    for orbit, edge in context["edges"].items():
        if h[edge["target"]] != context["p_by_orbit"][orbit] * h[edge["source"]]:
            edge_character_failures.append(orbit)
    for source, terms in context["outgoing"].items():
        harmonic_value = sum(
            (
                Fraction(term["multiplicity"]) * h[term["target"]]
                for term in terms
            ),
            start=Fraction(0),
        )
        csg_sum = sum(
            (
                Fraction(term["multiplicity"]) * context["p_by_orbit"][term["orbit"]]
                for term in terms
            ),
            start=Fraction(0),
        )
        if harmonic_value != h[source]:
            h_harmonic_failures.append(source)
        if csg_sum != 1:
            csg_msr_failures.append(source)

    support_first, support_second = harmonic["support_terminals"]
    support_determinant = (
        h[support_first] * k[support_second] - k[support_first] * h[support_second]
    )
    frame_inverse_failures = _frame_inverse_checks(states)

    full_edge_matrices = {
        orbit: _state_native_matrix(
            states[edge["source"]], states[edge["target"]], orbit, beta_is_one=False
        )
        for orbit, edge in context["edges"].items()
    }
    shear_edge_matrices = {
        orbit: _state_native_matrix(
            states[edge["source"]], states[edge["target"]], orbit, beta_is_one=True
        )
        for orbit, edge in context["edges"].items()
    }
    edge_mapping_failures: list[str] = []
    determinant_failures: list[str] = []
    for orbit, matrix in full_edge_matrices.items():
        edge = context["edges"][orbit]
        edge_source_vector: Vector = (
            _constant(h[edge["source"]]),
            _constant(k[edge["source"]]),
        )
        target_vector: Vector = (_constant(h[edge["target"]]), _constant(k[edge["target"]]))
        if _matrix_vector(matrix, edge_source_vector) != target_vector:
            edge_mapping_failures.append(orbit)
        expected_determinant = {
            (f"beta:{orbit}",): context["p_by_orbit"][orbit]
        }
        if _determinant(matrix) != expected_determinant:
            determinant_failures.append(orbit)

    occurrence_full = {
        occurrence_id: full_edge_matrices[orbit]
        for occurrence_id, orbit in context["occurrence_orbits"].items()
    }
    occurrence_shear = {
        occurrence_id: shear_edge_matrices[orbit]
        for occurrence_id, orbit in context["occurrence_orbits"].items()
    }

    path_state_failures: list[str] = []
    path_states: dict[str, Vector] = {}
    omega: Vector = (_constant(1), _constant(0))
    for record in path_data["path_records"]:
        state = omega
        for orbit in record["orbit_sequence"]:
            state = _matrix_vector(full_edge_matrices[orbit], state)
        expected = (
            _constant(h[record["endpoint_id"]]),
            _constant(k[record["endpoint_id"]]),
        )
        path_states[record["path_id"]] = state
        if state != expected:
            path_state_failures.append(record["path_id"])
    gc_pair_failures: list[str] = []
    for relation in gc["all_pair_derivations"]:
        left = str(relation["left_path_id"])
        right = str(relation["right_path_id"])
        if path_states[left] != path_states[right]:
            gc_pair_failures.append(str(relation.get("relation_id", f"{left}|{right}")))

    reachable_msr_failures: list[str] = []
    for constraint in cpobc["MSR_operator_constraints"]:
        source = str(constraint["source_id"])
        msr_source_vector: Vector = (_constant(h[source]), _constant(k[source]))
        residual = _vector_scale(
            int(constraint["identity_coefficient"]),
            msr_source_vector,
        )
        for term in constraint["terms"]:
            residual = _vector_add(
                residual,
                _vector_scale(
                    int(term["coefficient"]),
                    _matrix_vector(
                        occurrence_full[str(term["transition_id"])], msr_source_vector
                    ),
                ),
            )
        if residual != ({}, {}):
            reachable_msr_failures.append(str(constraint["constraint_id"]))

    tracked = {
        (
            OLD_FULL_UNIT_RELATION,
            OLD_FULL_UNIT_EQUATION,
            OLD_FULL_UNIT_ENTRY[0],
            OLD_FULL_UNIT_ENTRY[1],
        ),
        (
            OLD_SHEAR_UNIT_RELATION,
            OLD_SHEAR_UNIT_EQUATION,
            OLD_SHEAR_UNIT_ENTRY[0],
            OLD_SHEAR_UNIT_ENTRY[1],
        ),
        (
            TWO_ROW_F_RELATION,
            TWO_ROW_F_EQUATION,
            TWO_ROW_F_ENTRY[0],
            TWO_ROW_F_ENTRY[1],
        ),
        (
            TWO_ROW_G_RELATION,
            TWO_ROW_G_EQUATION,
            TWO_ROW_G_ENTRY[0],
            TWO_ROW_G_ENTRY[1],
        ),
    }
    full_cpobc = _expand_raw_cpobc(
        cpobc,
        occurrence_full,
        tracked,
        retain_all_records=True,
    )
    shear_cpobc = _expand_raw_cpobc(
        cpobc,
        occurrence_shear,
        tracked,
        retain_all_records=False,
    )
    beta_variables = [f"beta:{orbit}" for orbit in sorted(context["edges"])]
    alpha_free_lattice = _alpha_free_exponent_lattice(
        full_cpobc["alpha_free_nonzero_records"],
        beta_variables,
    )
    supplemental = _supplemental_ledgers(eq112, weak)

    old_full_key = "|".join(
        map(
            str,
            (
                OLD_FULL_UNIT_RELATION,
                OLD_FULL_UNIT_EQUATION,
                OLD_FULL_UNIT_ENTRY[0],
                OLD_FULL_UNIT_ENTRY[1],
            ),
        )
    )
    old_shear_key = "|".join(
        map(
            str,
            (
                OLD_SHEAR_UNIT_RELATION,
                OLD_SHEAR_UNIT_EQUATION,
                OLD_SHEAR_UNIT_ENTRY[0],
                OLD_SHEAR_UNIT_ENTRY[1],
            ),
        )
    )
    two_row_f_key = "|".join(
        map(
            str,
            (
                TWO_ROW_F_RELATION,
                TWO_ROW_F_EQUATION,
                TWO_ROW_F_ENTRY[0],
                TWO_ROW_F_ENTRY[1],
            ),
        )
    )
    two_row_g_key = "|".join(
        map(
            str,
            (
                TWO_ROW_G_RELATION,
                TWO_ROW_G_EQUATION,
                TWO_ROW_G_ENTRY[0],
                TWO_ROW_G_ENTRY[1],
            ),
        )
    )
    f_polynomial = _add(_variable(f"beta:{BETA_U_ORBIT}"), _constant(Fraction(1, 8)))
    g_polynomial = _add(
        _scale(8, _variable(f"beta:{BETA_V_ORBIT}")),
        _scale(
            -64,
            _multiply(
                _variable(f"beta:{BETA_U_ORBIT}"),
                _variable(f"beta:{BETA_V_ORBIT}"),
            ),
        ),
    )
    localizer = _subtract(
        _multiply(_variable(RHO_V), _variable(f"beta:{BETA_V_ORBIT}")),
        _constant(1),
    )
    unit_identity = _subtract(
        _add(
            _scale(Fraction(1, 16), _multiply(_variable(RHO_V), g_polynomial)),
            _scale(
                4,
                _multiply(
                    _multiply(_variable(RHO_V), _variable(f"beta:{BETA_V_ORBIT}")),
                    f_polynomial,
                ),
            ),
        ),
        localizer,
    )
    f_actual = _deserialize_polynomial(
        full_cpobc["tracked_entries"][two_row_f_key]["polynomial"]
    )
    g_actual = _deserialize_polynomial(
        full_cpobc["tracked_entries"][two_row_g_key]["polynomial"]
    )
    gates = {
        "all_five_input_SHA256_bindings_hold": input_hashes == PINNED_INPUT_SHA256,
        "CSG_character_has_131_exact_nonzero_ON_orbit_values": len(
            context["p_by_orbit"]
        )
        == 131
        and all(context["p_by_orbit"].values()),
        "all_407_path_products_are_independent_on_87_endpoints": len(
            path_data["path_records"]
        )
        == 407
        and len(h) == 87
        and not path_data["path_independence_failures"],
        "h_root_is_one_and_all_h_are_nonzero": h["p1-0"] == 1 and all(h.values()),
        "all_131_edges_satisfy_h_target_equals_p_times_h_source": not edge_character_failures,
        "all_24_harmonic_and_CSG_MSR_equations_hold": not h_harmonic_failures
        and not csg_msr_failures,
        "independent_k_is_harmonic_and_k_root_is_zero": not harmonic[
            "harmonic_failures"
        ]
        and k["p1-0"] == 0
        and harmonic["support_terminals"] == ["p5-0000000", "p5-0000002"],
        "reachable_state_span_has_rank_two": support_determinant != 0,
        "all_87_local_frames_are_invertible": not frame_inverse_failures,
        "all_131_full_fibres_map_source_state_to_target_state": not edge_mapping_failures,
        "all_131_determinants_equal_p_e_times_beta_e": not determinant_failures,
        "all_407_fixed_vector_path_states_and_1529_GC_pairs_agree": not path_state_failures
        and not gc_pair_failures
        and len(gc["all_pair_derivations"]) == 1529,
        "all_24_reachable_state_MSR_residuals_are_zero": not reachable_msr_failures,
        "all_783_raw_CPOBC_equations_are_expanded_in_262_variables": full_cpobc[
            "equation_count"
        ]
        == 783
        and full_cpobc["term_census"]["scalar_entries"] == 3132,
        "corrected_full_chart_has_no_pure_nonzero_constant_CPOBC_entry": full_cpobc[
            "term_census"
        ]["pure_nonzero_constant_entries"]
        == 0,
        "alpha_free_census_is_327_binomials_654_terms": alpha_free_lattice[
            "row_count"
        ]
        == 327
        and alpha_free_lattice["all_rows_binomial"]
        and alpha_free_lattice["total_terms"] == 654
        and alpha_free_lattice["maximum_degree_histogram"]
        == {"1": 22, "2": 303, "3": 2},
        "alpha_free_exponent_lattice_rank89_nullity42_SNF_is_primitive": alpha_free_lattice[
            "rank"
        ]
        == 89
        and alpha_free_lattice["nullity"] == 42
        and alpha_free_lattice["smith_nonzero_diagonal"] == [1] * 89,
        "old_full_unit_entry_has_zero_constant_coefficient": full_cpobc[
            "tracked_entries"
        ][old_full_key]["constant_coefficient"]
        == "0",
        "alpha_free_row_f_is_beta_u_plus_one_eighth": f_actual == f_polynomial,
        "alpha_free_row_g_is_eight_beta_v_times_one_minus_eight_beta_u": (
            g_actual == g_polynomial
        ),
        "beta_v_is_an_actual_edge_with_determinant_p_v_times_beta_v": BETA_V_ORBIT
        in full_edge_matrices
        and _determinant(full_edge_matrices[BETA_V_ORBIT])
        == {(f"beta:{BETA_V_ORBIT}",): context["p_by_orbit"][BETA_V_ORBIT]},
        "localized_two_row_unit_identity_is_exact": unit_identity == {(): Fraction(1)},
        "corrected_beta1_shear_still_has_a_constant_obstruction": shear_cpobc[
            "term_census"
        ]["pure_nonzero_constant_entries"]
        > 0,
        "Q5_and_supplemental_ledgers_remain_separate": supplemental["Eq113"][
            "branches_kept_separate"
        ]
        and supplemental["Eq139"]["domains_kept_separate"],
    }
    if not all(gates.values()):
        failed = sorted(name for name, passed in gates.items() if not passed)
        raise AssertionError(f"corrected CSG fixed-hk obstruction gate failed: {failed}")

    p_records = [
        {
            "orbit_id": orbit,
            "source_id": context["edges"][orbit]["source"],
            "target_id": context["edges"][orbit]["target"],
            "stage": context["edges"][orbit]["stage"],
            "p_e": str(context["p_by_orbit"][orbit]),
        }
        for orbit in sorted(context["edges"])
    ]
    state_records = [
        {
            "endpoint_id": endpoint,
            "stage": context["endpoint_stages"][endpoint],
            "h": str(h[endpoint]),
            "k": str(k[endpoint]),
        }
        for endpoint in sorted(states)
    ]
    first_shear_constant = shear_cpobc["pure_constant_records"][0]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile_slice": (
            "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON__"
            "one_corrected_CSG_compatible_rank2_state_assignment"
        ),
        "input_artifacts": input_hashes,
        "normalized_CSG_character": {
            "couplings": "t_j=1",
            "formula": "p_e=2^(precursor_width-maximal_precursor_count)/2^stage",
            "actual_edge_count": len(p_records),
            "all_nonzero": all(context["p_by_orbit"].values()),
            "records": p_records,
            "records_digest_sha256": _records_digest(p_records),
        },
        "path_product_coordinate_h": {
            "definition": "h_endpoint=product_e_on_path(p_e)",
            "path_count": len(path_data["path_records"]),
            "endpoint_count": len(h),
            "path_counts_by_stage": dict(
                (
                    str(stage),
                    count,
                )
                for stage, count in sorted(
                    Counter(
                        record["endpoint_stage"] for record in path_data["path_records"]
                    ).items()
                )
            ),
            "path_independence_failures": path_data["path_independence_failures"],
            "root": "p1-0",
            "root_value": str(h["p1-0"]),
            "zero_values": sorted(endpoint for endpoint, value in h.items() if not value),
            "edge_character_failures": edge_character_failures,
            "harmonic_failures": h_harmonic_failures,
            "CSG_MSR_failures": csg_msr_failures,
            "path_records_digest_sha256": _records_digest(path_data["path_records"]),
        },
        "independent_harmonic_coordinate_k": {
            "construction": (
                "the lexicographically first two terminal boundary values are weighted "
                "by their opposite root weights to cancel at the root, then extended "
                "backward by exact harmonic recurrence"
            ),
            "root_value": str(k["p1-0"]),
            "support_terminals": harmonic["support_terminals"],
            "terminal_root_weights": {
                endpoint: weight
                for endpoint, weight in sorted(harmonic["terminal_weights"].items())
            },
            "harmonic_failures": harmonic["harmonic_failures"],
        },
        "reachable_states": {
            "records": state_records,
            "records_digest_sha256": _records_digest(state_records),
            "rank": 2,
            "support_pair": [support_first, support_second],
            "support_determinant": str(support_determinant),
            "initial_vector": ["1", "0"],
        },
        "complete_state_native_matrix_fibres": {
            "frame": "F_c=[[h_c,0],[k_c,1]]",
            "formula": "A_e=F_target*[[1,alpha_e],[0,beta_e]]*F_source^-1",
            "actual_edge_count": len(full_edge_matrices),
            "alpha_coordinates": len(full_edge_matrices),
            "beta_coordinates": len(full_edge_matrices),
            "total_affine_coordinates": 2 * len(full_edge_matrices),
            "coverage_proof": (
                "F_c sends e1 to v_c. For any A with A*v_s=v_t, "
                "M=F_t^-1*A*F_s has first column e1 and uniquely equals "
                "[[1,alpha],[0,beta]]."
            ),
            "frame_inverse_failures": frame_inverse_failures,
            "edge_mapping_failures": edge_mapping_failures,
            "determinant_formula": "det(A_e)=p_e*beta_e",
            "determinant_failures": determinant_failures,
            "nonsingular_iff": "beta_e!=0 because p_e!=0",
        },
        "built_in_semantics": {
            "fixed_vector_GC": {
                "path_count": len(path_states),
                "same_endpoint_pair_count": len(gc["all_pair_derivations"]),
                "path_state_failures": path_state_failures,
                "pair_failures": gc_pair_failures,
            },
            "reachable_state_MSR": {
                "source_count": len(cpobc["MSR_operator_constraints"]),
                "failures": reachable_msr_failures,
            },
        },
        "raw_CPOBC_full_alpha_beta_manifest": {
            "variable_count": 262,
            "Q5_included": False,
            "equation_count": full_cpobc["equation_count"],
            "term_census": full_cpobc["term_census"],
            "records": full_cpobc["records"],
            "records_digest_sha256": full_cpobc["records_digest_sha256"],
            "pure_constant_records": full_cpobc["pure_constant_records"],
            "pure_constant_records_digest_sha256": full_cpobc[
                "pure_constant_records_digest_sha256"
            ],
            "old_uniform_terminal_full_chart_unit_entry_after_correction": full_cpobc[
                "tracked_entries"
            ][old_full_key],
            "selected_exact_rows": {
                two_row_f_key: full_cpobc["tracked_entries"][two_row_f_key],
                two_row_g_key: full_cpobc["tracked_entries"][two_row_g_key],
            },
            "unrestricted_singular_relation_solution_exists": "UNRESOLVED",
            "constant_unit_generator": "NONE_DETECTED",
        },
        "alpha_free_raw_CPOBC_lattice_diagnostic": alpha_free_lattice,
        "nonsingular_two_row_unit_obstruction": {
            "coefficient_ring_before_localization": (
                "QQ[alpha_e,beta_e : 131 actual ON edge orbits]"
            ),
            "beta_u_orbit": BETA_U_ORBIT,
            "beta_v_orbit": BETA_V_ORBIT,
            "beta_u_variable": f"beta:{BETA_U_ORBIT}",
            "beta_v_variable": f"beta:{BETA_V_ORBIT}",
            "p_u": str(context["p_by_orbit"][BETA_U_ORBIT]),
            "p_v": str(context["p_by_orbit"][BETA_V_ORBIT]),
            "determinant_at_v": (
                f"{context['p_by_orbit'][BETA_V_ORBIT]}*beta:{BETA_V_ORBIT}"
            ),
            "nonsingularity_requires_beta_v_nonzero": True,
            "row_f": {
                "relation_id": TWO_ROW_F_RELATION,
                "equation_id": TWO_ROW_F_EQUATION,
                "entry": list(TWO_ROW_F_ENTRY),
                "display": f"f=beta:{BETA_U_ORBIT}+1/8",
                "polynomial": _serialize_polynomial(f_actual),
                "contains_alpha": False,
            },
            "row_g": {
                "relation_id": TWO_ROW_G_RELATION,
                "equation_id": TWO_ROW_G_EQUATION,
                "entry": list(TWO_ROW_G_ENTRY),
                "display": (
                    f"g=8*beta:{BETA_V_ORBIT}*(1-8*beta:{BETA_U_ORBIT})"
                ),
                "polynomial": _serialize_polynomial(g_actual),
                "contains_alpha": False,
            },
            "localizer": {
                "inverse_coordinate": RHO_V,
                "display": f"l={RHO_V}*beta:{BETA_V_ORBIT}-1",
                "polynomial": _serialize_polynomial(localizer),
            },
            "unit_identity": {
                "display": (
                    "1=(rho/16)*g+4*rho*beta_v*f-"
                    "(rho*beta_v-1)"
                ),
                "term_from_g": _serialize_polynomial(
                    _scale(Fraction(1, 16), _multiply(_variable(RHO_V), g_actual))
                ),
                "term_from_f": _serialize_polynomial(
                    _scale(
                        4,
                        _multiply(
                            _multiply(
                                _variable(RHO_V),
                                _variable(f"beta:{BETA_V_ORBIT}"),
                            ),
                            f_actual,
                        ),
                    )
                ),
                "minus_localizer": _serialize_polynomial(_scale(-1, localizer)),
                "reconstructed_result": _serialize_polynomial(unit_identity),
                "result_is_one": unit_identity == {(): Fraction(1)},
            },
            "localized_CPOBC_ideal": "UNIT_IDEAL",
            "nonsingular_relation_variety_on_selected_fixed_hk_slice": "EMPTY",
            "solver_required": False,
        },
        "beta1_shear_diagnostic": {
            "role": "DIAGNOSTIC_ONLY_DO_NOT_REUSE_OR_RERUN_OLD_D12_SHEAR",
            "term_census": shear_cpobc["term_census"],
            "pure_constant_records": shear_cpobc["pure_constant_records"],
            "pure_constant_records_digest_sha256": shear_cpobc[
                "pure_constant_records_digest_sha256"
            ],
            "first_pure_nonzero_constant": first_shear_constant,
            "tracked_old_shear_entry": shear_cpobc["tracked_entries"][old_shear_key],
            "relation_variety_on_beta1_slice": "EMPTY_BY_NONZERO_CONSTANT_GENERATOR",
            "D12_compiled_or_solved": False,
        },
        "separate_unresolved_ledgers": {
            "supplemental_Q5": {
                "coordinate_count": 4,
                "matrix": "[[Q5:00,Q5:01],[Q5:10,Q5:11]]",
                "status": "SEPARATE_NOT_COMPILED_NOT_SOLVED",
            },
            **supplemental,
        },
        "execution_and_claim_boundary": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "sage_status": "NOT_INVOKED",
            "finite_field_status": "NOT_RUN",
            "numerical_status": "NOT_RUN",
            "unrestricted_singular_relation_solution": "UNRESOLVED",
            "nonsingular_relation_solution_on_selected_fixed_hk_slice": "IMPOSSIBLE",
            "witness": None,
        },
        "scope_exclusions": {
            "selected_corrected_CSG_fixed_hk_nonsingular_slice": "COVERED_EMPTY",
            "all_rank2_state_assignments": "NOT_COVERED",
            "global_chart_cover": "NOT_COVERED",
            "Eq113_both_branches": "UNRESOLVED",
            "Eq139_both_domains": "UNRESOLVED",
            "supplemental_Q5": "UNRESOLVED",
            "SR2V_terminal_verdict": False,
        },
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "The corrected CSG h-coordinate removes the old constant unit row, but for "
            "the selected independent harmonic k-coordinate two alpha-free raw CPOBC "
            "rows and one beta nonsingularity localizer generate 1 exactly. Thus this "
            "selected fixed-(h,k) nonsingular slice is empty. Other rank-two state "
            "assignments and the separate Q5/Eq113/Eq139 ledgers remain unresolved; "
            "this is not an SR2-V terminal."
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
