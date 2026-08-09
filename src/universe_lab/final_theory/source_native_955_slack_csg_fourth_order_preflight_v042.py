"""Preflight fourth-order 955 jets on the full third-order CSG jet fibre.

The exact predecessor proves that every second-order CSG jet lifts through
order three and that Q vanishes on every such lift.  Choose the canonical
particular third correction by back-substitution through the 427 retained
Jacobian jets and keep its homogeneous kernel fibre::

    x(t) = x_CSG + t*K*z + t^2*(w_particular(z) + K*a)
           + t^3*(v_particular(z, a) + K*b) + t^4*u.

The order-four residual space has four monomial kinds: ``z^4`` (270,725),
``z^2*a`` (60,025), ``a^2`` (1,225), and ``z*b`` (2,401), for 334,376
possible columns.  This module streams exact sparse residuals, retains only
the 427 independent Jacobian-basis jets, and records fail-closed resource
bounds.  It does not reduce the 3,985 dependent rows to compatibility
obstructions and does not make a fourth-order commutativity claim.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_second_order_v042 as second
from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import (
    source_native_955_slack_csg_third_order_preflight_v042 as third_preflight,
)
from universe_lab.final_theory import source_native_955_slack_csg_third_order_v042 as third
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

SLACK_INVENTORY_PATH = third_preflight.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = third_preflight.MIXED_MANIFEST_PATH
TANGENT_PATH = third_preflight.TANGENT_PATH
SECOND_ORDER_PATH = third_preflight.SECOND_ORDER_PATH
THIRD_ORDER_PATH = third.RESULT_PATH
BUDGET_PATH = "config/v0.4.2_955_slack_csg_fourth_order_budget.json"
RESULT_PATH = "results/v0.4.2_955_slack_csg_fourth_order_preflight.json"

SCHEMA = "final-theory-v042-955-slack-csg-fourth-order-preflight-v1"
VERDICT = "V042_955_SLACK_CSG_FOURTH_ORDER_FULL_JET_FIBER_PREFLIGHT_CERTIFIED"

TANGENT_DIMENSION = 49
AMBIENT_COORDINATES = 476
Z_OFFSET = 0
A_OFFSET = TANGENT_DIMENSION
B_OFFSET = 2 * TANGENT_DIMENSION
WEIGHTED_VARIABLES = 3 * TANGENT_DIMENSION

QUARTIC_MONOMIALS = 49 * 50 * 51 * 52 // 24
Z_SQUARED_A_MONOMIALS = (49 * 50 // 2) * 49
A_SQUARED_MONOMIALS = 49 * 50 // 2
Z_TIMES_B_MONOMIALS = 49**2
WEIGHTED_MONOMIALS = (
    QUARTIC_MONOMIALS + Z_SQUARED_A_MONOMIALS + A_SQUARED_MONOMIALS + Z_TIMES_B_MONOMIALS
)

_ZERO = Fraction(0)

LinearForm = dict[int, Fraction]
ThirdForm = third_preflight.ThirdForm
FourthMonomial = tuple[int, ...]
FourthForm = dict[FourthMonomial, Fraction]
WeightedForm = dict[tuple[int, ...], Fraction]
WeightedSeries = list[WeightedForm]


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


def _object_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _accumulate(target: dict[Any, Fraction], key: Any, value: Fraction) -> None:
    if not value:
        return
    updated = target.get(key, _ZERO) + value
    if updated:
        target[key] = updated
    else:
        target.pop(key, None)


def _scale_form(form: dict[Any, Fraction], coefficient: Fraction) -> dict[Any, Fraction]:
    if not coefficient:
        return {}
    return {key: coefficient * value for key, value in form.items() if coefficient * value}


def _variable_weight(index: int) -> int:
    if Z_OFFSET <= index < A_OFFSET:
        return 1
    if A_OFFSET <= index < B_OFFSET:
        return 2
    if B_OFFSET <= index < WEIGHTED_VARIABLES:
        return 3
    raise AssertionError(f"invalid weighted variable index: {index}")


def _monomial_weight(monomial: tuple[int, ...]) -> int:
    return sum(_variable_weight(index) for index in monomial)


def _fourth_kind(monomial: FourthMonomial) -> str:
    if tuple(sorted(monomial)) != monomial or _monomial_weight(monomial) != 4:
        raise AssertionError(f"invalid weighted fourth monomial: {monomial}")
    if len(monomial) == 4:
        return "z_quartic"
    if len(monomial) == 3:
        return "z_squared_times_a"
    if len(monomial) == 2 and monomial[0] >= A_OFFSET:
        return "a_squared"
    if len(monomial) == 2:
        return "z_times_b"
    raise AssertionError(f"invalid weighted fourth monomial: {monomial}")


def _fourth_form_record(form: FourthForm) -> list[list[Any]]:
    return [[list(monomial), str(value)] for monomial, value in sorted(form.items())]


def _fourth_form_digest(forms: list[FourthForm]) -> str:
    records = [_fourth_form_record(form) for form in forms]
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def _fraction_bits(value: Fraction) -> int:
    return max(abs(value.numerator).bit_length(), value.denominator.bit_length())


def _fraction_bytes(value: Fraction) -> int:
    numerator = max(1, (abs(value.numerator).bit_length() + 7) // 8)
    denominator = max(1, (value.denominator.bit_length() + 7) // 8)
    return numerator + denominator


def _compact_fourth_term_bytes(monomial: FourthMonomial, coefficient: Fraction) -> int:
    _fourth_kind(monomial)
    return 20 + 4 * len(monomial) + _fraction_bytes(coefficient)


def _particular_third_order_forms(
    basis: dict[int, third_preflight.ThirdBasisRecord],
    variable_count: int,
) -> list[ThirdForm]:
    """Set all free third-order ambient coordinates to zero and solve pivots."""

    forms: list[ThirdForm] = [{} for _ in range(variable_count)]
    for pivot in sorted(basis, reverse=True):
        record = basis[pivot]
        value = _scale_form(record.third, Fraction(-1))
        for index, coefficient in record.jacobian.items():
            if index != pivot and forms[index]:
                second._add_scaled(value, forms[index], -coefficient)
        forms[pivot] = value
    for record in basis.values():
        residual = dict(record.third)
        for index, coefficient in record.jacobian.items():
            if forms[index]:
                second._add_scaled(residual, forms[index], coefficient)
        if residual:
            raise AssertionError("the canonical third-order correction failed back-substitution")
    return forms


def _particular_third_profile(forms: list[ThirdForm], names: list[str]) -> dict[str, Any]:
    term_counts = [len(form) for form in forms]
    maximum = max(term_counts, default=0)
    compact_bytes = sum(
        third_preflight._compact_third_term_bytes(monomial, coefficient)
        for form in forms
        for monomial, coefficient in form.items()
    )
    return {
        "ambient_coordinates": len(forms),
        "free_third_order_fibre_coordinates": TANGENT_DIMENSION,
        "nonzero_particular_coordinate_forms": sum(bool(form) for form in forms),
        "total_particular_weighted_third_terms": sum(term_counts),
        "term_count_histogram": terms._histogram(term_counts),
        "maximum_terms_one_particular_coordinate": maximum,
        "selected_maximum_coordinate_records": [
            {"coordinate": names[index], "terms": len(form)}
            for index, form in enumerate(forms)
            if len(form) == maximum
        ][:20],
        "maximum_coefficient_bits": max(
            (_fraction_bits(value) for form in forms for value in form.values()),
            default=0,
        ),
        "portable_compact_storage_model_bytes": compact_bytes,
        "forms_digest_sha256": hashlib.sha256(
            _canonical_json([third_preflight._third_form_record(form) for form in forms]).encode(
                "utf-8"
            )
        ).hexdigest(),
        "normalisation": "all_49_free_order_three_ambient_coordinates_set_to_zero",
    }


def _third_to_global_monomial(monomial: third_preflight.ThirdMonomial) -> tuple[int, ...]:
    kind = third_preflight._third_kind(monomial)
    if kind == "z_cubic":
        return tuple(monomial[1:])
    return (monomial[1], A_OFFSET + monomial[2])


def _coordinate_factor_series(
    assignment: list[Fraction],
    tangent_coordinate_forms: list[LinearForm],
    particular_second_forms: list[second.QuadraticForm],
    particular_third_forms: list[ThirdForm],
) -> list[WeightedSeries]:
    factors: list[WeightedSeries] = []
    for ambient_index, constant in enumerate(assignment):
        series: WeightedSeries = [{} for _ in range(5)]
        if constant:
            series[0][()] = constant
        for tangent_index, coefficient in tangent_coordinate_forms[ambient_index].items():
            _accumulate(series[1], (tangent_index,), coefficient)
            _accumulate(series[2], (A_OFFSET + tangent_index,), coefficient)
            _accumulate(series[3], (B_OFFSET + tangent_index,), coefficient)
        for monomial, coefficient in particular_second_forms[ambient_index].items():
            _accumulate(series[2], monomial, coefficient)
        for monomial, coefficient in particular_third_forms[ambient_index].items():
            _accumulate(series[3], _third_to_global_monomial(monomial), coefficient)
        factors.append(series)
    return factors


def _multiply_series(left: WeightedSeries, right: WeightedSeries) -> WeightedSeries:
    output: WeightedSeries = [{} for _ in range(5)]
    for left_weight, left_form in enumerate(left):
        if not left_form:
            continue
        for right_weight, right_form in enumerate(right[: 5 - left_weight]):
            if not right_form:
                continue
            target = output[left_weight + right_weight]
            for left_monomial, left_value in left_form.items():
                for right_monomial, right_value in right_form.items():
                    monomial = tuple(sorted(left_monomial + right_monomial))
                    _accumulate(target, monomial, left_value * right_value)
    return output


def _weighted_third_and_fourth_restriction(
    polynomial: terms.Polynomial,
    factor_series: list[WeightedSeries],
) -> tuple[WeightedForm, FourthForm]:
    """Return coefficients of weights three and four after the jet substitution."""

    output_third: WeightedForm = {}
    output_fourth: FourthForm = {}
    for ambient_monomial, integer_coefficient in polynomial.items():
        product: WeightedSeries = [{} for _ in range(5)]
        product[0][()] = Fraction(integer_coefficient)
        for ambient_index in ambient_monomial:
            product = _multiply_series(product, factor_series[ambient_index])
            if not any(product):
                break
        for monomial, coefficient in product[3].items():
            _accumulate(output_third, monomial, coefficient)
        for monomial, coefficient in product[4].items():
            _accumulate(output_fourth, monomial, coefficient)
    for monomial in output_fourth:
        _fourth_kind(monomial)
    if len(output_fourth) > WEIGHTED_MONOMIALS:
        raise AssertionError("a weighted fourth form exceeded its finite monomial space")
    return output_third, output_fourth


@dataclass
class WeightedFourthCensus:
    block_name: str
    scalar_slots: int = 0
    nonzero_forms: int = 0
    total_terms: int = 0
    kind_terms: Counter[str] = field(default_factory=Counter)
    compact_storage_bytes: int = 0
    maximum_compact_bytes_one_form: int = 0
    term_counts: list[int] = field(default_factory=list)
    maximum_terms: int = 0
    maximum_ties: int = 0
    selected_maximum_records: list[dict[str, Any]] = field(default_factory=list)
    coefficient_bit_histogram: Counter[int] = field(default_factory=Counter)
    digest: Any = field(default_factory=hashlib.sha256)

    def add(self, identifier: dict[str, Any], form: FourthForm) -> None:
        self.scalar_slots += 1
        count = len(form)
        self.term_counts.append(count)
        self.total_terms += count
        self.nonzero_forms += bool(form)
        compact = 0
        for monomial, coefficient in form.items():
            self.kind_terms[_fourth_kind(monomial)] += 1
            self.coefficient_bit_histogram[_fraction_bits(coefficient)] += 1
            compact += _compact_fourth_term_bytes(monomial, coefficient)
        self.compact_storage_bytes += compact
        self.maximum_compact_bytes_one_form = max(self.maximum_compact_bytes_one_form, compact)
        if count > self.maximum_terms:
            self.maximum_terms = count
            self.maximum_ties = 1
            self.selected_maximum_records = [{**identifier, "terms": count}]
        elif count == self.maximum_terms:
            self.maximum_ties += 1
            if len(self.selected_maximum_records) < 20:
                self.selected_maximum_records.append({**identifier, "terms": count})
        self.digest.update(_canonical_json([identifier, _fourth_form_record(form)]).encode("utf-8"))
        self.digest.update(b"\n")

    def finalize(self) -> dict[str, Any]:
        nonzero_counts = [count for count in self.term_counts if count]
        return {
            "block": self.block_name,
            "scalar_slots": self.scalar_slots,
            "nonzero_fourth_forms": self.nonzero_forms,
            "zero_fourth_forms": self.scalar_slots - self.nonzero_forms,
            "total_terms": self.total_terms,
            "z_quartic_terms": self.kind_terms["z_quartic"],
            "z_squared_times_a_terms": self.kind_terms["z_squared_times_a"],
            "a_squared_terms": self.kind_terms["a_squared"],
            "z_times_b_terms": self.kind_terms["z_times_b"],
            "term_count_histogram_all_slots": terms._histogram(self.term_counts),
            "term_count_quantiles_all_slots": terms._quantiles(self.term_counts),
            "term_count_quantiles_nonzero_forms": terms._quantiles(nonzero_counts),
            "maximum_terms_one_form": self.maximum_terms,
            "maximum_term_record_ties": self.maximum_ties,
            "selected_maximum_records": self.selected_maximum_records,
            "coefficient_bit_histogram": {
                str(bits): count for bits, count in sorted(self.coefficient_bit_histogram.items())
            },
            "maximum_coefficient_bits": max(self.coefficient_bit_histogram, default=0),
            "portable_compact_storage_model_bytes_if_all_retained": self.compact_storage_bytes,
            "maximum_portable_compact_bytes_one_streamed_form": self.maximum_compact_bytes_one_form,
            "stream_digest_sha256": self.digest.hexdigest(),
        }


@dataclass
class FourthBasisRecord:
    jacobian: tangent.SparseRow
    fourth: FourthForm


@dataclass
class FourthJacobianBasisPreflight:
    budget: dict[str, Any]
    basis: dict[int, FourthBasisRecord] = field(default_factory=dict)
    independent_rows: int = 0
    dependent_rows: int = 0
    independent_add_scaled_calls: int = 0
    independent_add_scaled_source_term_visits: int = 0
    predicted_dependent_add_scaled_calls: int = 0
    predicted_dependent_source_term_visits: int = 0
    maximum_predicted_source_term_visits_one_dependent: int = 0
    selected_maximum_dependent_records: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self,
        identifier: dict[str, Any],
        jacobian: tangent.SparseRow,
        fourth: FourthForm,
    ) -> None:
        if len(fourth) > int(self.budget["single_weighted_form_term_limit"]):
            raise RuntimeError("one raw fourth form exceeded the versioned term cap")
        reduced_jacobian = dict(jacobian)
        factors: list[tuple[int, Fraction]] = []
        for pivot in sorted(self.basis):
            factor = reduced_jacobian.get(pivot, _ZERO)
            if not factor:
                continue
            factors.append((pivot, factor))
            second._add_scaled(reduced_jacobian, self.basis[pivot].jacobian, -factor)

        source_visits = sum(len(self.basis[pivot].fourth) for pivot, _factor in factors)
        if not reduced_jacobian:
            self.dependent_rows += 1
            self.predicted_dependent_add_scaled_calls += len(factors)
            self.predicted_dependent_source_term_visits += source_visits
            if source_visits > self.maximum_predicted_source_term_visits_one_dependent:
                self.maximum_predicted_source_term_visits_one_dependent = source_visits
                self.selected_maximum_dependent_records = [
                    {**identifier, "predicted_source_term_visits": source_visits}
                ]
            elif source_visits == self.maximum_predicted_source_term_visits_one_dependent:
                if len(self.selected_maximum_dependent_records) < 20:
                    self.selected_maximum_dependent_records.append(
                        {**identifier, "predicted_source_term_visits": source_visits}
                    )
            return

        reduced_fourth = dict(fourth)
        for pivot, factor in factors:
            second._add_scaled(reduced_fourth, self.basis[pivot].fourth, -factor)
        pivot = min(reduced_jacobian)
        scale = reduced_jacobian[pivot]
        normalized_fourth = _scale_form(reduced_fourth, Fraction(1, 1) / scale)
        if len(normalized_fourth) > int(self.budget["single_weighted_form_term_limit"]):
            raise RuntimeError("one retained fourth form exceeded the versioned term cap")
        self.basis[pivot] = FourthBasisRecord(
            {index: value / scale for index, value in reduced_jacobian.items() if value},
            normalized_fourth,
        )
        self.independent_rows += 1
        self.independent_add_scaled_calls += len(factors)
        self.independent_add_scaled_source_term_visits += source_visits
        if sum(len(record.fourth) for record in self.basis.values()) > int(
            self.budget["independent_basis_term_limit"]
        ):
            raise RuntimeError("the retained fourth Jacobian basis exceeded its term cap")

    def serialize(self) -> dict[str, Any]:
        forms = [self.basis[pivot].fourth for pivot in sorted(self.basis)]
        term_counts = [len(form) for form in forms]
        compact_bytes = sum(
            _compact_fourth_term_bytes(monomial, coefficient)
            for form in forms
            for monomial, coefficient in form.items()
        )
        conservative_bytes = (
            sum(term_counts) * int(self.budget["conservative_python_bytes_per_sparse_term"])
            + len(forms) * 4096
        )
        return {
            "Jacobian_rank": len(self.basis),
            "independent_rows": self.independent_rows,
            "dependent_rows_not_compatibility_reduced": self.dependent_rows,
            "basis_total_weighted_terms": sum(term_counts),
            "basis_term_count_histogram": terms._histogram(term_counts),
            "basis_maximum_terms_one_form": max(term_counts, default=0),
            "basis_portable_compact_storage_model_bytes": compact_bytes,
            "basis_conservative_python_storage_estimate_bytes": conservative_bytes,
            "basis_maximum_coefficient_bits": max(
                (_fraction_bits(value) for form in forms for value in form.values()),
                default=0,
            ),
            "basis_forms_digest_sha256": _fourth_form_digest(forms),
            "Jacobian_echelon_digest_sha256": tangent._echelon_digest(
                {pivot: record.jacobian for pivot, record in self.basis.items()}
            ),
            "independent_add_scaled_calls": self.independent_add_scaled_calls,
            "independent_add_scaled_source_term_visits": (
                self.independent_add_scaled_source_term_visits
            ),
            "predicted_dependent_add_scaled_calls": self.predicted_dependent_add_scaled_calls,
            "predicted_dependent_source_term_visits": self.predicted_dependent_source_term_visits,
            "maximum_predicted_source_term_visits_one_dependent": (
                self.maximum_predicted_source_term_visits_one_dependent
            ),
            "selected_maximum_dependent_records": self.selected_maximum_dependent_records,
            "dependent_compatibility_forms_actually_reduced": 0,
        }


def _validate_budget(budget: dict[str, Any]) -> None:
    expected = {
        "schema_version": "final-theory-v042-955-slack-csg-fourth-order-budget-v1",
        "campaign": "955_CSG_FULL_THIRD_ORDER_JET_FIBER_FOURTH_ORDER",
        "field": "QQ",
        "hard_memory_limit_bytes": 8 * 1024**3,
        "soft_memory_limit_bytes": 4 * 1024**3,
        "preflight_timeout_seconds": 1200,
        "audit_timeout_seconds": 7200,
        "conservative_python_bytes_per_sparse_term": 512,
        "fixed_runtime_reserve_bytes": 512 * 1024**2,
        "independent_basis_term_limit": 5_000_000,
        "compatibility_basis_term_limit": 10_000_000,
        "single_weighted_form_term_limit": WEIGHTED_MONOMIALS,
        "raw_stream_total_term_limit": 50_000_000,
        "total_add_scaled_source_term_visits_limit": 200_000_000,
    }
    for key, value in expected.items():
        if budget.get(key) != value:
            raise AssertionError(f"fourth-order budget field changed: {key}")


def compile_slack_csg_fourth_order_preflight_v042(root: Path) -> dict[str, Any]:
    """Compile the bounded fourth-order full-third-jet-fibre preflight."""

    root = root.resolve()
    paths = {
        "slack": root / SLACK_INVENTORY_PATH,
        "mixed": root / MIXED_MANIFEST_PATH,
        "tangent": root / TANGENT_PATH,
        "second": root / SECOND_ORDER_PATH,
        "third": root / THIRD_ORDER_PATH,
        "budget": root / BUDGET_PATH,
    }
    slack = _load(paths["slack"])
    mixed = _load(paths["mixed"])
    tangent_predecessor = _load(paths["tangent"])
    second_predecessor = _load(paths["second"])
    third_predecessor = _load(paths["third"])
    budget = _load(paths["budget"])
    _validate_budget(budget)

    if slack.get("semantic_digest_sha256") != terms._semantic_digest(slack):
        raise AssertionError("slack inventory predecessor binding failed")
    if mixed.get("semantic_digest_sha256") != terms._semantic_digest(mixed):
        raise AssertionError("mixed manifest predecessor binding failed")
    if tangent_predecessor.get("semantic_digest_sha256") != tangent._semantic_digest(
        tangent_predecessor
    ):
        raise AssertionError("tangent predecessor binding failed")
    if second_predecessor.get("semantic_digest_sha256") != second._semantic_digest(
        second_predecessor
    ):
        raise AssertionError("second-order predecessor binding failed")
    if (
        third_predecessor.get("verdict") != third.VERDICT_ALL_LIFT_Q_BLOCKED
        or third_predecessor.get("semantic_digest_sha256")
        != third._semantic_digest(third_predecessor)
        or third_predecessor.get("semantic_digest_sha256")
        != "53d7818f4bff6e5d3c556cdb137644feeae73a4bde50f74d5cb84feb8db16bfa"
        or third_predecessor["third_order_core_compatibility"][
            "all_second_order_core_jets_lift_through_third_order"
        ]
        is not True
        or third_predecessor["Q_third_order_modulo_core"][
            "Q_commutators_vanish_through_order_three_on_every_core_lift"
        ]
        is not True
    ):
        raise AssertionError("third-order predecessor binding failed")

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    assignment, basepoint, _target = tangent._build_csg_assignment(slack, mixed, matrices, names)
    if len(names) != AMBIENT_COORDINATES:
        raise AssertionError("the unrestricted slack coordinate count changed")

    jacobian_rows: list[tangent.SparseRow] = []
    setup_ledger = terms.OperationLedger()
    for _identifier, polynomial in second._iter_core_polynomials(slack, matrices, setup_ledger):
        value, gradient = tangent._value_and_gradient(polynomial, assignment)
        if value:
            raise AssertionError("the CSG point failed during fourth-order setup")
        if gradient:
            jacobian_rows.append(gradient)
    core_basis = tangent._echelon(jacobian_rows)
    free_coordinates, kernel_vectors, tangent_coordinate_forms = second._tangent_kernel(
        core_basis, len(names)
    )
    if len(core_basis) != 427 or len(kernel_vectors) != TANGENT_DIMENSION:
        raise AssertionError("the CSG Jacobian or tangent dimension changed")

    second_eliminator = second.SecondOrderEliminator(TANGENT_DIMENSION)
    second_ledger = terms.OperationLedger()
    for identifier, polynomial in second._iter_core_polynomials(slack, matrices, second_ledger):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        quadratic = second._quadratic_restriction(polynomial, assignment, tangent_coordinate_forms)
        second_eliminator.add(identifier, gradient, quadratic)
    if second_eliminator.nonzero_raw_obstruction_forms:
        raise AssertionError("the second-order all-lift conclusion changed")
    particular_second_forms = third_preflight._particular_second_order_forms(
        second_eliminator, len(names)
    )

    reconstructed_third_basis = third_preflight.ThirdJacobianBasisPreflight()
    third_setup_ledger = terms.OperationLedger()
    for identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, third_setup_ledger
    ):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        third_form = third_preflight._third_order_restriction(
            polynomial,
            assignment,
            tangent_coordinate_forms,
            particular_second_forms,
        )
        reconstructed_third_basis.add(identifier, gradient, third_form)
    reconstructed_profile = reconstructed_third_basis.serialize(
        third_predecessor["resource_usage"]["versioned_budget"]
    )
    expected_third_core = third_predecessor["third_order_core_compatibility"]
    if (
        reconstructed_profile["Jacobian_rank"] != 427
        or reconstructed_profile["dependent_rows_not_compatibility_reduced"] != 3985
        or reconstructed_profile["basis_forms_digest_sha256"]
        != expected_third_core["Jacobian_third_forms_digest_sha256"]
        or reconstructed_profile["Jacobian_echelon_digest_sha256"]
        != expected_third_core["Jacobian_echelon_digest_sha256"]
    ):
        raise AssertionError("the retained third-order Jacobian jets changed")

    particular_third_forms = _particular_third_order_forms(
        reconstructed_third_basis.basis, len(names)
    )
    particular_third_profile = _particular_third_profile(particular_third_forms, names)
    factor_series = _coordinate_factor_series(
        assignment,
        tangent_coordinate_forms,
        particular_second_forms,
        particular_third_forms,
    )

    block_censuses = {
        "CPOBC": WeightedFourthCensus("CPOBC"),
        "strong_GC": WeightedFourthCensus("strong_GC"),
    }
    combined_census = WeightedFourthCensus("CPOBC_plus_strong_GC")
    fourth_basis = FourthJacobianBasisPreflight(budget)
    fourth_ledger = terms.OperationLedger()
    third_residual_failures = 0
    for identifier, polynomial in second._iter_core_polynomials(slack, matrices, fourth_ledger):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        third_residual, fourth_form = _weighted_third_and_fourth_restriction(
            polynomial, factor_series
        )
        third_residual_failures += bool(third_residual)
        block_censuses[identifier["block"]].add(identifier, fourth_form)
        combined_census.add(identifier, fourth_form)
        fourth_basis.add(identifier, gradient, fourth_form)
    if third_residual_failures:
        raise AssertionError("the canonical third correction failed a raw core equation")

    core_census = combined_census.finalize()
    basis_profile = fourth_basis.serialize()
    if (
        basis_profile["Jacobian_rank"] != 427
        or basis_profile["dependent_rows_not_compatibility_reduced"] != 3985
        or basis_profile["Jacobian_echelon_digest_sha256"]
        != expected_third_core["Jacobian_echelon_digest_sha256"]
    ):
        raise AssertionError("the fourth-order preflight Jacobian basis drifted")

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    q_census = WeightedFourthCensus("Q_commutators")
    q_ledger = terms.OperationLedger()
    q_third_residual_failures = 0
    for identifier, polynomial in second._iter_q_polynomials(q_representatives, matrices, q_ledger):
        third_residual, fourth_form = _weighted_third_and_fourth_restriction(
            polynomial, factor_series
        )
        q_third_residual_failures += bool(third_residual)
        q_census.add(identifier, fourth_form)
    if q_third_residual_failures:
        raise AssertionError("the canonical third correction failed a Q equation")
    q_profile = q_census.finalize()

    hard_memory = int(budget["hard_memory_limit_bytes"])
    soft_memory = int(budget["soft_memory_limit_bytes"])
    per_term = int(budget["conservative_python_bytes_per_sparse_term"])
    reserve = int(budget["fixed_runtime_reserve_bytes"])
    compatibility_cap = int(budget["compatibility_basis_term_limit"])
    bounded_audit_memory = reserve + per_term * (
        basis_profile["basis_total_weighted_terms"] + compatibility_cap
    )
    dense_worst_case_terms = 3985 * WEIGHTED_MONOMIALS
    dense_worst_case_bytes = reserve + per_term * dense_worst_case_terms
    preflight_safe = (
        basis_profile["basis_conservative_python_storage_estimate_bytes"] < soft_memory
        and basis_profile["basis_total_weighted_terms"]
        <= int(budget["independent_basis_term_limit"])
        and core_census["total_terms"] <= int(budget["raw_stream_total_term_limit"])
        and core_census["maximum_terms_one_form"] <= int(budget["single_weighted_form_term_limit"])
        and basis_profile["predicted_dependent_source_term_visits"]
        <= int(budget["total_add_scaled_source_term_visits_limit"])
        and bounded_audit_memory < hard_memory
    )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "basepoint": "diagonal CSG t_j=1 source matrices",
            "formal_order_preflight": 4,
        },
        "input_bindings": {
            SLACK_INVENTORY_PATH: {
                "raw_sha256": _sha256(paths["slack"]),
                "semantic_digest_sha256": slack["semantic_digest_sha256"],
            },
            MIXED_MANIFEST_PATH: {
                "raw_sha256": _sha256(paths["mixed"]),
                "semantic_digest_sha256": mixed["semantic_digest_sha256"],
            },
            TANGENT_PATH: {
                "raw_sha256": _sha256(paths["tangent"]),
                "semantic_digest_sha256": tangent_predecessor["semantic_digest_sha256"],
            },
            SECOND_ORDER_PATH: {
                "raw_sha256": _sha256(paths["second"]),
                "semantic_digest_sha256": second_predecessor["semantic_digest_sha256"],
            },
            THIRD_ORDER_PATH: {
                "raw_sha256": _sha256(paths["third"]),
                "semantic_digest_sha256": third_predecessor["semantic_digest_sha256"],
                "verdict": third_predecessor["verdict"],
            },
            BUDGET_PATH: {
                "raw_sha256": _sha256(paths["budget"]),
                "content_digest_sha256": _object_digest(budget),
            },
        },
        "basepoint_recheck": {
            "assignment_sha256": basepoint["assignment_sha256"],
            "all_131_matrices_equal_diag_p_e_1": basepoint["all_131_matrices_equal_diag_p_e_1"],
            "all_131_determinants_nonzero": basepoint["all_131_determinants_nonzero"],
        },
        "full_third_order_jet_fibre": {
            "first_order_tangent_variables_z": TANGENT_DIMENSION,
            "second_order_homogeneous_fibre_variables_a": TANGENT_DIMENSION,
            "third_order_homogeneous_fibre_variables_b": TANGENT_DIMENSION,
            "coordinate_model": "v=v_particular(z,a)+K*b",
            "weighted_degrees": {"z": 1, "a": 2, "b": 3},
            "z_quartic_monomial_dimension": QUARTIC_MONOMIALS,
            "z_squared_times_a_monomial_dimension": Z_SQUARED_A_MONOMIALS,
            "a_squared_monomial_dimension": A_SQUARED_MONOMIALS,
            "z_times_b_monomial_dimension": Z_TIMES_B_MONOMIALS,
            "total_weighted_fourth_monomial_dimension": WEIGHTED_MONOMIALS,
            "particular_second_order_forms_digest_sha256": third_predecessor[
                "basepoint_and_jet_fibre_recheck"
            ]["particular_second_order_forms_digest_sha256"],
            "particular_third_order_correction": particular_third_profile,
            "tangent_basis_digest_sha256": second_predecessor["tangent_kernel"][
                "basis_digest_sha256"
            ],
            "free_ambient_coordinate_names": [names[index] for index in free_coordinates],
        },
        "raw_fourth_order_core_stream": {
            "per_block": {block: census.finalize() for block, census in block_censuses.items()},
            "combined": core_census,
            "all_raw_forms_retained": False,
            "streaming_rule": "expand_one_scalar_form_count_digest_then_discard",
            "canonical_third_correction_residual_failures": third_residual_failures,
            "ambient_polynomial_operation_ledger": fourth_ledger.serialize(),
        },
        "independent_Jacobian_basis_fourth_jet_preflight": basis_profile,
        "raw_Q_fourth_order_stream": {
            **q_profile,
            "canonical_third_correction_residual_failures": q_third_residual_failures,
            "intrinsic_Q_reduction_executed": False,
            "operation_ledger": q_ledger.serialize(),
        },
        "resource_decision": {
            "versioned_budget": budget,
            "basis_estimate_below_soft_memory_limit": (
                basis_profile["basis_conservative_python_storage_estimate_bytes"] < soft_memory
            ),
            "bounded_audit_conservative_peak_estimate_bytes": bounded_audit_memory,
            "bounded_audit_estimate_below_hard_memory_limit": (bounded_audit_memory < hard_memory),
            "unbounded_dense_compatibility_basis_worst_case_terms": dense_worst_case_terms,
            "unbounded_dense_compatibility_basis_worst_case_bytes": dense_worst_case_bytes,
            "unbounded_dense_strategy_rejected": dense_worst_case_bytes > hard_memory,
            "fail_closed_streamed_fourth_order_audit_authorised": preflight_safe,
            "generic_solver_authorised": False,
            "next_gate": (
                "RUN_FAIL_CLOSED_STREAMED_FOURTH_ORDER_CORE_COMPATIBILITY_AND_Q_ESCAPE_AUDIT"
                if preflight_safe
                else "STOP_AT_REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT"
            ),
        },
        "execution_boundary": {
            "exact_sparse_QQ_weighted_jet_preflight_runs": 1,
            "independent_Jacobian_basis_fourth_jet_forms_retained": 427,
            "dependent_core_compatibility_reductions": 0,
            "Q_intrinsic_fourth_order_reductions": 0,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "generic_solver_run": False,
            "ambient_full_fourth_tensor_materialised": False,
            "dense_334376_column_matrix_materialised": False,
        },
        "claim_boundary": [
            (
                "This artifact is a deterministic resource preflight, not a "
                "fourth-order obstruction audit."
            ),
            "No dependent core row was reduced to a fourth-order compatibility form.",
            "Raw Q fourth jets were counted but not reduced modulo the core jet basis.",
            (
                "No claim is made about fourth-order Q escape, formal convergence, "
                "or remote components."
            ),
            "Eq113 and Eq139 remain separate downstream witness-validation gates.",
            "Unrestricted source-native 955 remains open.",
        ],
        "unrestricted_source_native_955_status": "OPEN",
        "passed": True,
        "verdict": VERDICT,
    }
    if not preflight_safe:
        payload["passed"] = False
        payload["verdict"] = "V042_955_SLACK_CSG_FOURTH_ORDER_PREFLIGHT_RESOURCE_LIMIT"
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_csg_fourth_order_preflight_v042(root: Path) -> Path:
    payload = compile_slack_csg_fourth_order_preflight_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_csg_fourth_order_preflight_v042(repository_root))
