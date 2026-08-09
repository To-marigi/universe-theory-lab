"""Stream exact scalar term counts for the unrestricted v0.4.2 955 slack chart.

The predecessor slack compiler solves the 24 reachable-state MSR rows by
monic triangular timid-matrix recurrences.  This module expands those 24
matrices over the 476 remaining integral coordinates, then streams the 783 raw
CPOBC and 320 strong-GC word equalities one block at a time.  Scalar residuals
are counted, hashed and discarded; no full polynomial manifest is retained.

The fixed nonzero preparation vector is put at ``Omega=e1``.  This is a basis
normalisation on the unrestricted general-matrix chart, not the diagonal mixed
ansatz.  Word equalities, nonsingularity and commutativity are invariant under
the simultaneous basis change.

The 131 determinant predicates are also expanded one at a time.  A valid
separate-localiser presentation and the 48 possible ``u!=0`` patch templates
are counted structurally, but no localisation, patch solver, Groebner basis,
saturation, finite-field or numerical run is performed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

SLACK_INVENTORY_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
COVERAGE_GAP_PATH = "results/v0.4.2_955_slack_coverage_gap.json"
RESULT_PATH = "results/v0.4.2_955_slack_term_preflight.json"

SCHEMA = "final-theory-v042-955-slack-streamed-term-preflight-v1"
VERDICT = "V042_955_SLACK_STREAMED_TERM_PREFLIGHT_CERTIFIED_NO_SOLVER"

MAX_ENTRY_TERMS = 1_000_000
MAX_RAW_PRODUCT_PAIRS = 25_000_000
MAX_STREAMED_RESIDUAL_TERMS = 50_000_000

Monomial = tuple[int, ...]
Polynomial = dict[Monomial, int]
Matrix = tuple[tuple[Polynomial, Polynomial], tuple[Polynomial, Polynomial]]
Vector = tuple[Polynomial, Polynomial]


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


def _constant(value: int) -> Polynomial:
    return {} if value == 0 else {(): value}


def _variable(index: int) -> Polynomial:
    return {(index,): 1}


def _merge_monomials(left: Monomial, right: Monomial) -> Monomial:
    merged: list[int] = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        if left[left_index] <= right[right_index]:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1
    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return tuple(merged)


@dataclass
class OperationLedger:
    polynomial_additions: int = 0
    polynomial_scales: int = 0
    polynomial_multiplications: int = 0
    raw_product_pairs_total: int = 0
    maximum_raw_product_pairs_one_multiply: int = 0
    maximum_input_terms_one_multiply: int = 0
    maximum_output_terms_one_multiply: int = 0
    maximum_polynomial_terms_seen: int = 0
    maximum_polynomial_degree_seen: int = 0
    maximum_coefficient_bits_seen: int = 0
    maximum_product_degree_bound: int = 0

    def observe(self, polynomial: Polynomial) -> None:
        terms = len(polynomial)
        if terms > MAX_ENTRY_TERMS:
            raise RuntimeError(f"sparse polynomial exceeds {MAX_ENTRY_TERMS} terms")
        self.maximum_polynomial_terms_seen = max(self.maximum_polynomial_terms_seen, terms)
        if polynomial:
            self.maximum_polynomial_degree_seen = max(
                self.maximum_polynomial_degree_seen,
                max(len(monomial) for monomial in polynomial),
            )
            self.maximum_coefficient_bits_seen = max(
                self.maximum_coefficient_bits_seen,
                max(abs(coefficient).bit_length() for coefficient in polynomial.values()),
            )

    def serialize(self) -> dict[str, int]:
        return {
            "polynomial_additions": self.polynomial_additions,
            "polynomial_scales": self.polynomial_scales,
            "polynomial_multiplications": self.polynomial_multiplications,
            "raw_product_pairs_total": self.raw_product_pairs_total,
            "maximum_raw_product_pairs_one_multiply": (self.maximum_raw_product_pairs_one_multiply),
            "maximum_input_terms_one_multiply": self.maximum_input_terms_one_multiply,
            "maximum_output_terms_one_multiply": self.maximum_output_terms_one_multiply,
            "maximum_polynomial_terms_seen": self.maximum_polynomial_terms_seen,
            "maximum_polynomial_degree_seen": self.maximum_polynomial_degree_seen,
            "maximum_coefficient_bits_seen": self.maximum_coefficient_bits_seen,
            "maximum_product_degree_bound": self.maximum_product_degree_bound,
        }


def _add(left: Polynomial, right: Polynomial, ledger: OperationLedger) -> Polynomial:
    ledger.polynomial_additions += 1
    result = dict(left)
    for monomial, coefficient in right.items():
        updated = result.get(monomial, 0) + coefficient
        if updated:
            result[monomial] = updated
        else:
            result.pop(monomial, None)
    ledger.observe(result)
    return result


def _scale(coefficient: int, value: Polynomial, ledger: OperationLedger) -> Polynomial:
    ledger.polynomial_scales += 1
    result = (
        {}
        if coefficient == 0
        else {monomial: coefficient * existing for monomial, existing in value.items()}
    )
    ledger.observe(result)
    return result


def _multiply(left: Polynomial, right: Polynomial, ledger: OperationLedger) -> Polynomial:
    ledger.polynomial_multiplications += 1
    raw_pairs = len(left) * len(right)
    if raw_pairs > MAX_RAW_PRODUCT_PAIRS:
        raise RuntimeError(f"one sparse product exceeds the {MAX_RAW_PRODUCT_PAIRS} raw-pair limit")
    ledger.raw_product_pairs_total += raw_pairs
    ledger.maximum_raw_product_pairs_one_multiply = max(
        ledger.maximum_raw_product_pairs_one_multiply, raw_pairs
    )
    ledger.maximum_input_terms_one_multiply = max(
        ledger.maximum_input_terms_one_multiply, len(left) + len(right)
    )
    if left and right:
        ledger.maximum_product_degree_bound = max(
            ledger.maximum_product_degree_bound,
            max(len(monomial) for monomial in left) + max(len(monomial) for monomial in right),
        )
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = _merge_monomials(left_monomial, right_monomial)
            updated = result.get(monomial, 0) + left_coefficient * right_coefficient
            if updated:
                result[monomial] = updated
            else:
                result.pop(monomial, None)
    ledger.maximum_output_terms_one_multiply = max(
        ledger.maximum_output_terms_one_multiply, len(result)
    )
    ledger.observe(result)
    return result


def _identity() -> Matrix:
    return ((_constant(1), _constant(0)), (_constant(0), _constant(1)))


def _matrix_add(left: Matrix, right: Matrix, ledger: OperationLedger) -> Matrix:
    return tuple(
        tuple(_add(left[row][column], right[row][column], ledger) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_scale(coefficient: int, value: Matrix, ledger: OperationLedger) -> Matrix:
    return tuple(
        tuple(_scale(coefficient, value[row][column], ledger) for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_multiply(left: Matrix, right: Matrix, ledger: OperationLedger) -> Matrix:
    return tuple(
        tuple(
            _add(
                _multiply(left[row][0], right[0][column], ledger),
                _multiply(left[row][1], right[1][column], ledger),
                ledger,
            )
            for column in range(2)
        )
        for row in range(2)
    )  # type: ignore[return-value]


def _matrix_vector(matrix: Matrix, vector: Vector, ledger: OperationLedger) -> Vector:
    return (
        _add(
            _multiply(matrix[0][0], vector[0], ledger),
            _multiply(matrix[0][1], vector[1], ledger),
            ledger,
        ),
        _add(
            _multiply(matrix[1][0], vector[0], ledger),
            _multiply(matrix[1][1], vector[1], ledger),
            ledger,
        ),
    )


def _operator(symbol: str) -> str:
    if not symbol.startswith("A:"):
        raise AssertionError(f"unexpected operator symbol: {symbol}")
    return symbol[2:]


def _word_matrix(
    symbols: list[str], matrices: dict[str, Matrix], ledger: OperationLedger
) -> Matrix:
    operators = [_operator(symbol) for symbol in symbols]
    if not operators:
        return _identity()
    result = matrices[operators[0]]
    for operator in operators[1:]:
        result = _matrix_multiply(result, matrices[operator], ledger)
    return result


def _word_on_e1(symbols: list[str], matrices: dict[str, Matrix], ledger: OperationLedger) -> Vector:
    vector: Vector = (_constant(1), _constant(0))
    for symbol in reversed(symbols):
        vector = _matrix_vector(matrices[_operator(symbol)], vector, ledger)
    return vector


def _histogram(values: Iterable[int]) -> dict[str, int]:
    return {str(value): count for value, count in sorted(Counter(values).items())}


def _quantiles(values: list[int]) -> dict[str, int]:
    if not values:
        return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
    ordered = sorted(values)

    def nearest_rank(percent: int) -> int:
        index = max(0, (percent * len(ordered) + 99) // 100 - 1)
        return ordered[index]

    return {f"p{percent}": nearest_rank(percent) for percent in (50, 90, 95, 99)}


def _compact_term_bytes(monomial: Monomial, coefficient: int) -> int:
    coefficient_bytes = max(1, (abs(coefficient).bit_length() + 7) // 8)
    return 16 + 4 * len(monomial) + coefficient_bytes


def _serialize_polynomial(polynomial: Polynomial) -> list[list[Any]]:
    return [
        [str(coefficient), list(monomial)] for monomial, coefficient in sorted(polynomial.items())
    ]


@dataclass
class StreamCensus:
    block_name: str
    scalar_entries: int = 0
    nonzero_entries: int = 0
    total_terms: int = 0
    total_factor_occurrences: int = 0
    compact_storage_model_bytes: int = 0
    constant_nonzero_entries: int = 0
    term_counts: list[int] = field(default_factory=list)
    maximum_degrees: list[int] = field(default_factory=list)
    term_degree_histogram: Counter[int] = field(default_factory=Counter)
    coefficient_bit_histogram: Counter[int] = field(default_factory=Counter)
    variables_seen: set[int] = field(default_factory=set)
    maximum_terms_in_one_entry: int = 0
    maximum_term_records: list[dict[str, Any]] = field(default_factory=list)
    maximum_term_record_ties: int = 0
    exact_linear_rows: list[tuple[dict[int, int], int]] = field(default_factory=list)
    jacobian_rows_at_origin: list[dict[int, int]] = field(default_factory=list)
    exact_linear_record_count: int = 0
    selected_exact_linear_records: list[dict[str, Any]] = field(default_factory=list)
    digest: Any = field(default_factory=hashlib.sha256)

    def add(self, identifier: dict[str, Any], polynomial: Polynomial) -> None:
        self.scalar_entries += 1
        terms = len(polynomial)
        self.term_counts.append(terms)
        if self.total_terms + terms > MAX_STREAMED_RESIDUAL_TERMS:
            raise RuntimeError(
                "streamed residual term total exceeds the fail-closed preflight limit"
            )
        self.total_terms += terms
        if polynomial:
            self.nonzero_entries += 1
            maximum_degree = max(len(monomial) for monomial in polynomial)
            self.maximum_degrees.append(maximum_degree)
            if maximum_degree == 0:
                self.constant_nonzero_entries += 1
            for monomial, coefficient in polynomial.items():
                self.total_factor_occurrences += len(monomial)
                self.term_degree_histogram[len(monomial)] += 1
                self.coefficient_bit_histogram[abs(coefficient).bit_length()] += 1
                self.variables_seen.update(monomial)
                self.compact_storage_model_bytes += _compact_term_bytes(monomial, coefficient)
            if terms > self.maximum_terms_in_one_entry:
                self.maximum_terms_in_one_entry = terms
                self.maximum_term_record_ties = 1
                self.maximum_term_records = [
                    {**identifier, "term_count": terms, "maximum_degree": maximum_degree}
                ]
            elif terms == self.maximum_terms_in_one_entry:
                self.maximum_term_record_ties += 1
                if len(self.maximum_term_records) < 20:
                    self.maximum_term_records.append(
                        {**identifier, "term_count": terms, "maximum_degree": maximum_degree}
                    )

            constant = polynomial.get((), 0)
            linear = {
                monomial[0]: coefficient
                for monomial, coefficient in polynomial.items()
                if len(monomial) == 1
            }
            if linear:
                self.jacobian_rows_at_origin.append(linear)
            if maximum_degree <= 1:
                self.exact_linear_record_count += 1
                self.exact_linear_rows.append((linear, constant))
                if len(self.selected_exact_linear_records) < 20:
                    self.selected_exact_linear_records.append(
                        {
                            **identifier,
                            "constant": str(constant),
                            "coefficients": {
                                str(index): str(coefficient)
                                for index, coefficient in sorted(linear.items())
                            },
                        }
                    )
        else:
            self.maximum_degrees.append(0)

        digest_record = [identifier, _serialize_polynomial(polynomial)]
        self.digest.update(_canonical_json(digest_record).encode("utf-8"))
        self.digest.update(b"\n")

    def finalize(self) -> dict[str, Any]:
        nonzero_counts = [count for count in self.term_counts if count]
        return {
            "equation_block": self.block_name,
            "scalar_entry_slots": self.scalar_entries,
            "nonzero_scalar_entries": self.nonzero_entries,
            "identically_zero_scalar_entries": self.scalar_entries - self.nonzero_entries,
            "total_terms": self.total_terms,
            "total_factor_occurrences": self.total_factor_occurrences,
            "term_count_histogram_all_entries": _histogram(self.term_counts),
            "term_count_quantiles_all_entries": _quantiles(self.term_counts),
            "term_count_quantiles_nonzero_entries": _quantiles(nonzero_counts),
            "maximum_terms_in_one_entry": self.maximum_terms_in_one_entry,
            "maximum_term_record_ties": self.maximum_term_record_ties,
            "selected_maximum_term_records": self.maximum_term_records,
            "entry_maximum_degree_histogram": _histogram(self.maximum_degrees),
            "term_degree_histogram": {
                str(degree): count for degree, count in sorted(self.term_degree_histogram.items())
            },
            "maximum_total_degree": max(self.maximum_degrees, default=0),
            "coefficient_bit_length_histogram": {
                str(bits): count for bits, count in sorted(self.coefficient_bit_histogram.items())
            },
            "maximum_coefficient_bit_length": max(self.coefficient_bit_histogram, default=0),
            "variables_occurring": len(self.variables_seen),
            "constant_nonzero_entries": self.constant_nonzero_entries,
            "exact_linear_nonzero_entries": self.exact_linear_record_count,
            "selected_exact_linear_records": self.selected_exact_linear_records,
            "compact_sparse_storage_model_bytes": self.compact_storage_model_bytes,
            "stream_digest_sha256": self.digest.hexdigest(),
        }


def _sparse_rank(
    rows: list[tuple[dict[int, int], int]], variable_count: int, augmented: bool
) -> tuple[int, list[dict[int, Fraction]]]:
    basis: dict[int, dict[int, Fraction]] = {}
    for coefficients, constant in rows:
        row = {
            index: Fraction(coefficient)
            for index, coefficient in coefficients.items()
            if coefficient
        }
        if augmented and constant:
            row[variable_count] = Fraction(constant)
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {index: value / scale for index, value in row.items() if value}
                break
            factor = row[pivot]
            pivot_row = basis[pivot]
            for index, value in pivot_row.items():
                updated = row.get(index, Fraction(0)) - factor * value
                if updated:
                    row[index] = updated
                else:
                    row.pop(index, None)
    return len(basis), [basis[pivot] for pivot in sorted(basis)]


def _row_digest(rows: list[dict[int, Fraction]]) -> str:
    serialized = [[[index, str(value)] for index, value in sorted(row.items())] for row in rows]
    return hashlib.sha256(_canonical_json(serialized).encode("utf-8")).hexdigest()


def _entry_profile(records: list[tuple[dict[str, Any], Polynomial]]) -> dict[str, Any]:
    census = StreamCensus("stored_elimination_objects")
    for identifier, polynomial in records:
        census.add(identifier, polynomial)
    profile = census.finalize()
    profile.pop("selected_exact_linear_records")
    profile.pop("exact_linear_nonzero_entries")
    return profile


def _compile_matrices(
    slack: dict[str, Any], names: list[str]
) -> tuple[dict[str, Matrix], dict[str, Vector], dict[str, Any]]:
    ledger = OperationLedger()
    orbit_inventory = slack["operator_namespace"]["orbit_inventory"]
    representatives = {str(record["representative_occurrence_id"]) for record in orbit_inventory}
    recurrences = slack["timid_slack_recurrences"]
    timid_to_record = {str(record["timid_orbit_representative"]): record for record in recurrences}
    if len(representatives) != 131 or len(timid_to_record) != 24:
        raise AssertionError("the 131/24 operator partition changed")
    independent = sorted(representatives - timid_to_record.keys())
    if len(independent) != 107:
        raise AssertionError("expected 107 independent non-timid matrices")

    variable_index: dict[str, int] = {}
    for representative in independent:
        for row in range(2):
            for column in range(2):
                name = f"A:{representative}:{row}{column}"
                variable_index[name] = len(names)
                names.append(name)
    for record in sorted(recurrences, key=lambda item: str(item["source_id"])):
        for coordinate in range(2):
            name = f"u:{record['source_id']}:{coordinate}"
            variable_index[name] = len(names)
            names.append(name)
    if len(names) != 476 or len(variable_index) != 476:
        raise AssertionError("the timid-eliminated variable namespace is not 476-dimensional")

    matrices: dict[str, Matrix] = {}
    for representative in independent:
        matrices[representative] = tuple(
            tuple(
                _variable(variable_index[f"A:{representative}:{row}{column}"])
                for column in range(2)
            )
            for row in range(2)
        )  # type: ignore[assignment]

    canonical_paths = {
        str(record["source_id"]): list(record["operator_word_later_on_left"])
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    states: dict[str, Vector] = {}
    dependency_records: list[dict[str, Any]] = []
    pending = set(timid_to_record)
    while pending:
        progress = False
        for representative in sorted(
            pending, key=lambda item: str(timid_to_record[item]["source_id"])
        ):
            record = timid_to_record[representative]
            source_id = str(record["source_id"])
            word = canonical_paths[source_id]
            if not all(_operator(symbol) in matrices for symbol in word):
                continue
            state = _word_on_e1(word, matrices, ledger)
            states[source_id] = state
            u0 = _variable(variable_index[f"u:{source_id}:0"])
            u1 = _variable(variable_index[f"u:{source_id}:1"])
            jv = (_scale(-1, state[1], ledger), state[0])
            outer: Matrix = (
                (
                    _multiply(u0, jv[0], ledger),
                    _multiply(u0, jv[1], ledger),
                ),
                (
                    _multiply(u1, jv[0], ledger),
                    _multiply(u1, jv[1], ledger),
                ),
            )
            timid = _matrix_add(_identity(), outer, ledger)
            non_timid = list(record["non_timid_orbit_representatives"])
            coefficients = list(record["non_timid_coefficients"])
            if len(non_timid) != len(coefficients):
                raise AssertionError("timid recurrence coefficients are malformed")
            for operator, coefficient in zip(non_timid, coefficients, strict=True):
                if operator not in matrices:
                    raise AssertionError("timid recurrence is not triangular")
                timid = _matrix_add(
                    timid,
                    _matrix_scale(-int(coefficient), matrices[operator], ledger),
                    ledger,
                )
            matrices[representative] = timid
            dependency_records.append(
                {
                    "source_id": source_id,
                    "timid_representative": representative,
                    "state_word": word,
                    "state_entry_terms": [len(state[0]), len(state[1])],
                    "timid_entry_terms": [
                        len(timid[row][column]) for row in range(2) for column in range(2)
                    ],
                    "state_maximum_degree": max(
                        (len(monomial) for entry in state for monomial in entry), default=0
                    ),
                    "timid_maximum_degree": max(
                        (len(monomial) for row in timid for entry in row for monomial in entry),
                        default=0,
                    ),
                }
            )
            pending.remove(representative)
            progress = True
        if not progress:
            raise AssertionError("timid recurrence is cyclic or unresolved")
    if len(matrices) != 131 or len(states) != 24:
        raise AssertionError("timid expansion did not cover all matrices and states")

    state_entries = [
        ({"source_id": source_id, "entry": str(entry)}, state[entry])
        for source_id, state in sorted(states.items())
        for entry in range(2)
    ]
    timid_entries = [
        (
            {"representative": representative, "entry": f"{row}{column}"},
            matrices[representative][row][column],
        )
        for representative in sorted(timid_to_record)
        for row in range(2)
        for column in range(2)
    ]
    return (
        matrices,
        states,
        {
            "independent_non_timid_matrices": len(independent),
            "eliminated_timid_matrices": len(timid_to_record),
            "expanded_matrix_count": len(matrices),
            "expanded_state_count": len(states),
            "state_entry_profile": _entry_profile(state_entries),
            "timid_matrix_entry_profile": _entry_profile(timid_entries),
            "dependency_records": dependency_records,
            "operation_ledger": ledger.serialize(),
        },
    )


def _stream_relation_block(
    block_name: str,
    records: list[dict[str, Any]],
    identifier_keys: tuple[str, ...],
    matrices: dict[str, Matrix],
) -> tuple[StreamCensus, dict[str, int]]:
    ledger = OperationLedger()
    census = StreamCensus(block_name)
    identifiers_seen: set[tuple[Any, ...]] = set()
    for block_index, record in enumerate(records):
        identifier_tuple = tuple(record.get(key) for key in identifier_keys)
        if identifier_tuple in identifiers_seen:
            raise AssertionError(f"duplicate {block_name} relation identifier")
        identifiers_seen.add(identifier_tuple)
        left = _word_matrix(record["lhs_source_word"], matrices, ledger)
        right = _word_matrix(record["rhs_source_word"], matrices, ledger)
        for row in range(2):
            for column in range(2):
                residual = _add(
                    left[row][column],
                    _scale(-1, right[row][column], ledger),
                    ledger,
                )
                identifier = {
                    "block_index": block_index,
                    **{key: record[key] for key in identifier_keys if key in record},
                    "entry": f"{row}{column}",
                }
                census.add(identifier, residual)
    return census, ledger.serialize()


def _stream_determinants(
    matrices: dict[str, Matrix], timid_representatives: set[str]
) -> tuple[StreamCensus, dict[str, int]]:
    ledger = OperationLedger()
    census = StreamCensus("source_nonsingularity_determinants")
    for representative in sorted(matrices):
        matrix = matrices[representative]
        determinant = _add(
            _multiply(matrix[0][0], matrix[1][1], ledger),
            _scale(-1, _multiply(matrix[0][1], matrix[1][0], ledger), ledger),
            ledger,
        )
        if not determinant:
            raise AssertionError(f"identically singular source matrix: {representative}")
        census.add(
            {
                "representative": representative,
                "matrix_role": (
                    "ELIMINATED_TIMID" if representative in timid_representatives else "INDEPENDENT"
                ),
            },
            determinant,
        )
    return census, ledger.serialize()


def _combined_census(censuses: list[StreamCensus]) -> dict[str, Any]:
    all_counts = [count for census in censuses for count in census.term_counts]
    nonzero_counts = [count for count in all_counts if count]
    degree_histogram: Counter[int] = Counter()
    coefficient_histogram: Counter[int] = Counter()
    variables: set[int] = set()
    digest = hashlib.sha256()
    for census in censuses:
        degree_histogram.update(census.term_degree_histogram)
        coefficient_histogram.update(census.coefficient_bit_histogram)
        variables.update(census.variables_seen)
        digest.update(census.block_name.encode("utf-8"))
        digest.update(b":")
        digest.update(census.digest.digest())
        digest.update(b"\n")
    return {
        "equation_blocks": sum(census.scalar_entries // 4 for census in censuses),
        "scalar_entry_slots": len(all_counts),
        "nonzero_scalar_entries": len(nonzero_counts),
        "identically_zero_scalar_entries": len(all_counts) - len(nonzero_counts),
        "total_terms": sum(all_counts),
        "term_count_quantiles_all_entries": _quantiles(all_counts),
        "term_count_quantiles_nonzero_entries": _quantiles(nonzero_counts),
        "maximum_terms_in_one_entry": max(all_counts, default=0),
        "term_degree_histogram": {
            str(degree): count for degree, count in sorted(degree_histogram.items())
        },
        "maximum_total_degree": max(degree_histogram, default=0),
        "coefficient_bit_length_histogram": {
            str(bits): count for bits, count in sorted(coefficient_histogram.items())
        },
        "maximum_coefficient_bit_length": max(coefficient_histogram, default=0),
        "variables_occurring": len(variables),
        "compact_sparse_storage_model_bytes": sum(
            census.compact_storage_model_bytes for census in censuses
        ),
        "combined_stream_digest_sha256": digest.hexdigest(),
    }


def compile_slack_term_preflight_v042(root: Path) -> dict[str, Any]:
    """Compile exact streamed term counts without retaining the scalar system."""

    root = root.resolve()
    slack_path = root / SLACK_INVENTORY_PATH
    coverage_path = root / COVERAGE_GAP_PATH
    slack = _load(slack_path)
    coverage = _load(coverage_path)
    if (
        slack.get("schema_version") != "final-theory-v042-955-source-native-slack-compiler-v1"
        or slack.get("verdict") != "V042_955_SOURCE_NATIVE_SLACK_INVENTORY_READY_NO_SOLVER_RUN"
        or slack.get("semantic_digest_sha256") != _semantic_digest(slack)
    ):
        raise AssertionError("source-native slack predecessor binding failed")
    if (
        coverage.get("schema_version") != "final-theory-v042-955-slack-coverage-gap-v1"
        or coverage.get("verdict")
        != "V042_955_SLACK_COVERAGE_GAP_214_NORMALS_DEGREE11_CEILING_CERTIFIED"
        or coverage.get("semantic_digest_sha256") != _semantic_digest(coverage)
    ):
        raise AssertionError("coverage-gap predecessor binding failed")
    if coverage["effective_slack_chart"]["effective_coordinates_after_timid_elimination"] != 476:
        raise AssertionError("coverage predecessor no longer exposes 476 coordinates")

    variable_names: list[str] = []
    matrices, _states, expansion = _compile_matrices(slack, variable_names)
    variable_namespace_digest = hashlib.sha256(
        _canonical_json(variable_names).encode("utf-8")
    ).hexdigest()

    cpobc_census, cpobc_operations = _stream_relation_block(
        "CPOBC",
        slack["raw_source_system"]["CPOBC_equations"],
        ("relation_id", "equation_id"),
        matrices,
    )
    gc_census, gc_operations = _stream_relation_block(
        "strong_GC",
        slack["raw_source_system"]["strong_GC_basis"],
        ("relation_id", "endpoint_causet_id"),
        matrices,
    )
    if cpobc_census.scalar_entries != 783 * 4 or gc_census.scalar_entries != 320 * 4:
        raise AssertionError("the 783/320 matrix-block census changed")

    core_censuses = [cpobc_census, gc_census]
    core = _combined_census(core_censuses)
    cpobc_variables = cpobc_census.variables_seen
    gc_variables = gc_census.variables_seen
    core_variables = cpobc_variables | gc_variables
    absent_from_core = sorted(set(range(len(variable_names))) - core_variables)
    absent_from_cpobc = sorted(set(range(len(variable_names))) - cpobc_variables)
    absent_from_gc = sorted(set(range(len(variable_names))) - gc_variables)
    if any(not variable_names[index].startswith("u:") for index in absent_from_core):
        raise AssertionError("a non-slack matrix coordinate is absent from the core system")
    exact_linear_rows = [row for census in core_censuses for row in census.exact_linear_rows]
    jacobian_rows = [(row, 0) for census in core_censuses for row in census.jacobian_rows_at_origin]
    coefficient_rank, coefficient_echelon = _sparse_rank(
        exact_linear_rows, len(variable_names), augmented=False
    )
    augmented_rank, augmented_echelon = _sparse_rank(
        exact_linear_rows, len(variable_names), augmented=True
    )
    jacobian_rank, jacobian_echelon = _sparse_rank(
        jacobian_rows, len(variable_names), augmented=False
    )

    timid_representatives = {
        str(record["timid_orbit_representative"]) for record in slack["timid_slack_recurrences"]
    }
    determinant_census, determinant_operations = _stream_determinants(
        matrices, timid_representatives
    )
    determinant_profile = determinant_census.finalize()
    localized_term_total = determinant_census.total_terms + determinant_census.scalar_entries
    localized_max_degree = max(determinant_census.maximum_degrees, default=0) + 1
    localized_max_terms = determinant_census.maximum_terms_in_one_entry + 1

    raw_pair_peak = max(
        expansion["operation_ledger"]["maximum_raw_product_pairs_one_multiply"],
        cpobc_operations["maximum_raw_product_pairs_one_multiply"],
        gc_operations["maximum_raw_product_pairs_one_multiply"],
        determinant_operations["maximum_raw_product_pairs_one_multiply"],
    )
    maximum_product_degree = max(
        expansion["operation_ledger"]["maximum_product_degree_bound"],
        cpobc_operations["maximum_product_degree_bound"],
        gc_operations["maximum_product_degree_bound"],
        determinant_operations["maximum_product_degree_bound"],
    )
    maximum_coefficient_bits = max(
        expansion["operation_ledger"]["maximum_coefficient_bits_seen"],
        cpobc_operations["maximum_coefficient_bits_seen"],
        gc_operations["maximum_coefficient_bits_seen"],
        determinant_operations["maximum_coefficient_bits_seen"],
    )
    coefficient_bytes = max(1, (maximum_coefficient_bits + 7) // 8)
    conservative_raw_pair_workset_bytes = raw_pair_peak * (
        16 + 4 * maximum_product_degree + coefficient_bytes
    )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "locus": "nonsingular unrestricted source-native slack chart",
        },
        "input_bindings": {
            SLACK_INVENTORY_PATH: {
                "raw_sha256": _sha256(slack_path),
                "semantic_digest_sha256": slack["semantic_digest_sha256"],
                "verdict": slack["verdict"],
            },
            COVERAGE_GAP_PATH: {
                "raw_sha256": _sha256(coverage_path),
                "semantic_digest_sha256": coverage["semantic_digest_sha256"],
                "verdict": coverage["verdict"],
            },
        },
        "basis_normalisation": {
            "preparation_vector": "Omega=e1",
            "justification": (
                "Every fixed nonzero Omega can be sent to e1 by one GL2 basis change; "
                "all source matrices are unrestricted general matrices and transform "
                "simultaneously by conjugation."
            ),
            "invariants_preserved": [
                "CPOBC word equalities",
                "strong-GC word equalities",
                "reachable-state MSR",
                "source nonsingularity",
                "Q commutativity or noncommutativity",
            ],
            "not_the_mixed_diagonal_ansatz": True,
        },
        "variable_namespace": {
            "coordinates": len(variable_names),
            "independent_matrix_entries": 107 * 4,
            "reachable_MSR_slack_coordinates": 48,
            "names": variable_names,
            "names_sha256": variable_namespace_digest,
        },
        "timid_elimination_expansion": expansion,
        "streamed_core_system": {
            "matrix_equation_blocks": 783 + 320,
            "expected_scalar_entry_slots_after_24_timid_definitions_are_eliminated": (
                (783 + 320) * 4
            ),
            "per_block": {
                "CPOBC": cpobc_census.finalize(),
                "strong_GC": gc_census.finalize(),
            },
            "combined": core,
            "variable_support": {
                "coordinates_total": len(variable_names),
                "coordinates_occurring_in_CPOBC": len(cpobc_variables),
                "coordinates_occurring_in_strong_GC": len(gc_variables),
                "coordinates_occurring_in_union": len(core_variables),
                "coordinates_absent_from_CPOBC": [
                    variable_names[index] for index in absent_from_cpobc
                ],
                "coordinates_absent_from_strong_GC": [
                    variable_names[index] for index in absent_from_gc
                ],
                "coordinates_absent_from_entire_core": [
                    variable_names[index] for index in absent_from_core
                ],
                "all_entirely_absent_coordinates_are_slack": True,
                "entirely_absent_coordinate_count": len(absent_from_core),
            },
            "operation_ledgers": {
                "CPOBC": cpobc_operations,
                "strong_GC": gc_operations,
            },
            "full_scalar_polynomials_retained": False,
            "only_counts_hashes_and_selected_extrema_retained": True,
        },
        "exact_linear_structure": {
            "exact_linear_nonzero_scalar_equations": len(exact_linear_rows),
            "coefficient_matrix_rank": coefficient_rank,
            "augmented_matrix_rank": augmented_rank,
            "linear_subsystem_consistent": coefficient_rank == augmented_rank,
            "coefficient_echelon_digest_sha256": _row_digest(coefficient_echelon),
            "augmented_echelon_digest_sha256": _row_digest(augmented_echelon),
            "degree_one_component_rows": len(jacobian_rows),
            "degree_one_component_rank": jacobian_rank,
            "degree_one_component_echelon_digest_sha256": _row_digest(jacobian_echelon),
            "degree_one_component_role": (
                "Jacobian-at-origin planning data only; it is not an exact elimination "
                "of equations that also contain higher-degree terms."
            ),
        },
        "nonsingularity_preflight": {
            "source_determinant_predicates": determinant_census.scalar_entries,
            "determinant_profile": determinant_profile,
            "operation_ledger": determinant_operations,
            "separate_inverse_coordinate_presentation": {
                "additional_coordinates": determinant_census.scalar_entries,
                "localisation_equations": determinant_census.scalar_entries,
                "total_terms": localized_term_total,
                "maximum_terms_in_one_equation": localized_max_terms,
                "maximum_total_degree": localized_max_degree,
                "form": "rho_e*det(A_e)-1=0 for each of 131 quotient matrices",
                "compiled_polynomials_retained": False,
            },
        },
        "N_nonzero_patch_preflight": {
            "equivalent_condition_on_nonsingular_reachable_states": (
                "at least one of the 48 slack coordinates u:c:i is nonzero"
            ),
            "principal_open_patches": 48,
            "one_patch_additional_coordinates": 1,
            "one_patch_localisation_equations": 1,
            "one_patch_localisation_terms": 2,
            "one_patch_localisation_degree": 2,
            "patch_form": "w:c:i*u:c:i-1=0",
            "patches_solved": 0,
        },
        "portable_storage_and_workset_model": {
            "model_not_a_CPython_RSS_measurement": True,
            "compact_term_bytes_formula": (
                "16 fixed bytes + 4 bytes per variable-index factor + minimal signed "
                "integer coefficient bytes"
            ),
            "core_if_fully_retained_bytes": core["compact_sparse_storage_model_bytes"],
            "maximum_raw_product_pairs_one_multiply": raw_pair_peak,
            "maximum_product_degree_bound_at_that_campaign": maximum_product_degree,
            "maximum_coefficient_bits_observed": maximum_coefficient_bits,
            "conservative_one_product_raw_pair_workset_bytes": (
                conservative_raw_pair_workset_bytes
            ),
            "does_not_estimate_solver_basis_growth": True,
        },
        "fail_closed_limits": {
            "maximum_terms_one_sparse_entry": MAX_ENTRY_TERMS,
            "maximum_raw_pairs_one_product": MAX_RAW_PRODUCT_PAIRS,
            "maximum_streamed_core_residual_terms": MAX_STREAMED_RESIDUAL_TERMS,
            "limits_reached": False,
        },
        "execution_decision": {
            "streamed_scalar_expansion_completed": True,
            "full_retained_scalar_manifest_authorised": False,
            "heavy_solver_authorised": False,
            "reason": (
                "The input is streamable, but it has no exact linear scalar equations and "
                "still reaches exact degree nine. The 16 globally absent terminal-stage slack "
                "coordinates make an exact CSG-basepoint tangent audit more informative than "
                "authorising a generic solver."
            ),
            "next_gate": (
                "CSG_BASEPOINT_EXACT_JACOBIAN_AND_Q_COMMUTATOR_TANGENT_ESCAPE_AUDIT_"
                "INCLUDING_THE_16_TERMINAL_SLACK_BLIND_DIRECTIONS"
            ),
        },
        "solver_status": {
            "streamed_scalar_expansion_runs": 1,
            "full_manifest_materialisations": 0,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "Exact term counts are for the Omega=e1 unrestricted source-native QQ chart.",
            "The 24 timid matrices are retained; the 1,103 relation residual blocks are streamed.",
            "Determinants are counted but their localisation equations are not materialised.",
            "Eq113 and Eq139 remain separate downstream witness-validation gates.",
            "Term sparsity does not predict Groebner or saturation basis growth.",
            "No witness, obstruction or unrestricted 955 terminal verdict is claimed.",
        ],
        "unrestricted_source_native_955_status": "OPEN",
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_term_preflight_v042(root: Path) -> Path:
    payload = compile_slack_term_preflight_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_term_preflight_v042(repository_root))
