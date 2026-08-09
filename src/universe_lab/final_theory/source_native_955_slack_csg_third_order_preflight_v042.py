"""Preflight third-order 955 jets on the full second-order CSG jet fibre.

At the diagonal CSG point the predecessor proves that every tangent vector
``z`` lifts through order two.  Fix the canonical particular correction
``w_particular(z)`` obtained by back-substitution through the 427 Jacobian
pivots and retain the homogeneous fibre

``w = w_particular(z) + K a``.

The order-three coefficient space therefore has two monomial kinds:
``z^3`` (20,825 possibilities) and ``z*a`` (2,401 possibilities).  This
module streams the exact raw third jets, retains only the 427 independent
Jacobian-basis jets, and records deterministic sparse storage bounds.  It
does not reduce the 3,985 dependent rows to compatibility obstructions and
does not make a third-order commutativity claim.
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
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

SLACK_INVENTORY_PATH = second.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = second.MIXED_MANIFEST_PATH
TANGENT_PATH = second.TANGENT_PATH
SECOND_ORDER_PATH = second.RESULT_PATH
BUDGET_PATH = "config/v0.4.2_955_slack_csg_third_order_budget.json"
RESULT_PATH = "results/v0.4.2_955_slack_csg_third_order_preflight.json"

SCHEMA = "final-theory-v042-955-slack-csg-third-order-preflight-v1"
VERDICT = "V042_955_SLACK_CSG_THIRD_ORDER_FULL_JET_FIBER_PREFLIGHT_CERTIFIED"

TANGENT_DIMENSION = 49
AMBIENT_COORDINATES = 476
CUBIC_MONOMIALS = TANGENT_DIMENSION * 50 * 51 // 6
BILINEAR_MONOMIALS = TANGENT_DIMENSION**2
WEIGHTED_MONOMIALS = CUBIC_MONOMIALS + BILINEAR_MONOMIALS

_ZERO = Fraction(0)

LinearForm = dict[int, Fraction]
QuadraticForm = second.QuadraticForm
CubicForm = dict[tuple[int, int, int], Fraction]
BilinearForm = dict[tuple[int, int], Fraction]
ThirdMonomial = tuple[int, ...]
ThirdForm = dict[ThirdMonomial, Fraction]


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


def _third_form_record(form: ThirdForm) -> list[list[Any]]:
    return [[list(monomial), str(value)] for monomial, value in sorted(form.items())]


def _third_form_digest(forms: list[ThirdForm]) -> str:
    return hashlib.sha256(
        _canonical_json([_third_form_record(form) for form in forms]).encode("utf-8")
    ).hexdigest()


def _fraction_bits(value: Fraction) -> int:
    return max(abs(value.numerator).bit_length(), value.denominator.bit_length())


def _fraction_bytes(value: Fraction) -> int:
    numerator = max(1, (abs(value.numerator).bit_length() + 7) // 8)
    denominator = max(1, (value.denominator.bit_length() + 7) // 8)
    return numerator + denominator


def _third_kind(monomial: ThirdMonomial) -> str:
    if len(monomial) == 4 and monomial[0] == 0:
        return "z_cubic"
    if len(monomial) == 3 and monomial[0] == 1:
        return "z_times_a"
    raise AssertionError(f"invalid weighted third monomial: {monomial}")


def _compact_third_term_bytes(monomial: ThirdMonomial, coefficient: Fraction) -> int:
    index_count = 3 if _third_kind(monomial) == "z_cubic" else 2
    return 20 + 4 * index_count + _fraction_bytes(coefficient)


def _compact_quadratic_term_bytes(
    monomial: tuple[int, int], coefficient: Fraction
) -> int:
    return 20 + 4 * len(monomial) + _fraction_bytes(coefficient)


def _particular_second_order_forms(
    eliminator: second.SecondOrderEliminator,
    variable_count: int,
) -> list[QuadraticForm]:
    """Choose free order-two coordinates zero and solve the pivot equations."""

    forms: list[QuadraticForm] = [{} for _ in range(variable_count)]
    for pivot in sorted(eliminator.jacobian_basis, reverse=True):
        record = eliminator.jacobian_basis[pivot]
        value = second._scaled(record.quadratic, Fraction(-1))
        for index, coefficient in record.jacobian.items():
            if index != pivot and forms[index]:
                second._add_scaled(value, forms[index], -coefficient)
        forms[pivot] = value
    for record in eliminator.jacobian_basis.values():
        residual: QuadraticForm = dict(record.quadratic)
        for index, coefficient in record.jacobian.items():
            if forms[index]:
                second._add_scaled(residual, forms[index], coefficient)
        if residual:
            raise AssertionError("the canonical second-order correction failed back-substitution")
    return forms


def _particular_profile(forms: list[QuadraticForm], names: list[str]) -> dict[str, Any]:
    term_counts = [len(form) for form in forms]
    maximum = max(term_counts, default=0)
    selected = [
        {"coordinate": names[index], "terms": len(form)}
        for index, form in enumerate(forms)
        if len(form) == maximum
    ][:20]
    compact_bytes = sum(
        _compact_quadratic_term_bytes(monomial, coefficient)
        for form in forms
        for monomial, coefficient in form.items()
    )
    return {
        "ambient_coordinates": len(forms),
        "free_second_order_fibre_coordinates": TANGENT_DIMENSION,
        "nonzero_particular_coordinate_forms": sum(bool(form) for form in forms),
        "total_particular_quadratic_terms": sum(term_counts),
        "term_count_histogram": terms._histogram(term_counts),
        "maximum_terms_one_particular_coordinate": maximum,
        "selected_maximum_coordinate_records": selected,
        "maximum_coefficient_bits": max(
            (_fraction_bits(value) for form in forms for value in form.values()),
            default=0,
        ),
        "portable_compact_storage_model_bytes": compact_bytes,
        "forms_digest_sha256": hashlib.sha256(
            _canonical_json(
                [second._form_record(form) for form in forms]
            ).encode("utf-8")
        ).hexdigest(),
        "normalisation": "all_49_free_order_two_ambient_coordinates_set_to_zero",
    }


def _third_order_restriction(
    polynomial: terms.Polynomial,
    assignment: list[Fraction],
    tangent_coordinate_forms: list[LinearForm],
    particular_second_order_forms: list[QuadraticForm],
) -> ThirdForm:
    """Return the order-three part on ``x0+t*Kz+t^2*(w0(z)+Ka)``."""

    output_cubic: CubicForm = {}
    output_bilinear: BilinearForm = {}
    for ambient_monomial, integer_coefficient in polynomial.items():
        constant = Fraction(integer_coefficient)
        linear: LinearForm = {}
        quadratic: QuadraticForm = {}
        fibre: LinearForm = {}
        cubic: CubicForm = {}
        bilinear: BilinearForm = {}

        for ambient_index in ambient_monomial:
            factor_constant = assignment[ambient_index]
            factor_linear = tangent_coordinate_forms[ambient_index]
            factor_quadratic = particular_second_order_forms[ambient_index]
            factor_fibre = factor_linear

            next_cubic = _scale_form(cubic, factor_constant)
            next_bilinear = _scale_form(bilinear, factor_constant)

            for (left, right), coefficient in quadratic.items():
                for tangent_index, factor in factor_linear.items():
                    monomial = tuple(sorted((left, right, tangent_index)))
                    _accumulate(next_cubic, monomial, coefficient * factor)
            for tangent_index, coefficient in linear.items():
                for (left, right), factor in factor_quadratic.items():
                    monomial = tuple(sorted((tangent_index, left, right)))
                    _accumulate(next_cubic, monomial, coefficient * factor)

            for fibre_index, coefficient in fibre.items():
                for tangent_index, factor in factor_linear.items():
                    _accumulate(
                        next_bilinear,
                        (tangent_index, fibre_index),
                        coefficient * factor,
                    )
            for tangent_index, coefficient in linear.items():
                for fibre_index, factor in factor_fibre.items():
                    _accumulate(
                        next_bilinear,
                        (tangent_index, fibre_index),
                        coefficient * factor,
                    )

            next_quadratic = _scale_form(quadratic, factor_constant)
            for left, coefficient in linear.items():
                for right, factor in factor_linear.items():
                    monomial = (left, right) if left <= right else (right, left)
                    _accumulate(next_quadratic, monomial, coefficient * factor)
            if constant:
                for monomial, factor in factor_quadratic.items():
                    _accumulate(next_quadratic, monomial, constant * factor)

            next_fibre = _scale_form(fibre, factor_constant)
            if constant:
                for fibre_index, factor in factor_fibre.items():
                    _accumulate(next_fibre, fibre_index, constant * factor)

            next_linear = _scale_form(linear, factor_constant)
            if constant:
                for tangent_index, factor in factor_linear.items():
                    _accumulate(next_linear, tangent_index, constant * factor)

            constant *= factor_constant
            linear = next_linear
            quadratic = next_quadratic
            fibre = next_fibre
            cubic = next_cubic
            bilinear = next_bilinear
            if not (constant or linear or quadratic or fibre or cubic or bilinear):
                break

        for monomial, coefficient in cubic.items():
            _accumulate(output_cubic, monomial, coefficient)
        for monomial, coefficient in bilinear.items():
            _accumulate(output_bilinear, monomial, coefficient)

    result: ThirdForm = {(0, *monomial): value for monomial, value in output_cubic.items()}
    result.update({(1, *monomial): value for monomial, value in output_bilinear.items()})
    if len(result) > WEIGHTED_MONOMIALS:
        raise AssertionError("a weighted third form exceeded its finite monomial space")
    return result


@dataclass
class WeightedThirdCensus:
    block_name: str
    scalar_slots: int = 0
    nonzero_forms: int = 0
    total_terms: int = 0
    cubic_terms: int = 0
    bilinear_terms: int = 0
    compact_storage_bytes: int = 0
    maximum_compact_bytes_one_form: int = 0
    term_counts: list[int] = field(default_factory=list)
    maximum_terms: int = 0
    maximum_ties: int = 0
    selected_maximum_records: list[dict[str, Any]] = field(default_factory=list)
    coefficient_bit_histogram: Counter[int] = field(default_factory=Counter)
    digest: Any = field(default_factory=hashlib.sha256)

    def add(self, identifier: dict[str, Any], form: ThirdForm) -> None:
        self.scalar_slots += 1
        count = len(form)
        self.term_counts.append(count)
        self.total_terms += count
        if form:
            self.nonzero_forms += 1
        compact = 0
        for monomial, coefficient in form.items():
            kind = _third_kind(monomial)
            if kind == "z_cubic":
                self.cubic_terms += 1
            else:
                self.bilinear_terms += 1
            bits = _fraction_bits(coefficient)
            self.coefficient_bit_histogram[bits] += 1
            compact += _compact_third_term_bytes(monomial, coefficient)
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
        self.digest.update(
            _canonical_json([identifier, _third_form_record(form)]).encode("utf-8")
        )
        self.digest.update(b"\n")

    def finalize(self) -> dict[str, Any]:
        nonzero_counts = [count for count in self.term_counts if count]
        return {
            "block": self.block_name,
            "scalar_slots": self.scalar_slots,
            "nonzero_third_forms": self.nonzero_forms,
            "zero_third_forms": self.scalar_slots - self.nonzero_forms,
            "total_terms": self.total_terms,
            "z_cubic_terms": self.cubic_terms,
            "z_times_a_terms": self.bilinear_terms,
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
            "portable_compact_storage_model_bytes_if_all_retained": (
                self.compact_storage_bytes
            ),
            "maximum_portable_compact_bytes_one_streamed_form": (
                self.maximum_compact_bytes_one_form
            ),
            "stream_digest_sha256": self.digest.hexdigest(),
        }


@dataclass
class ThirdBasisRecord:
    jacobian: tangent.SparseRow
    third: ThirdForm


@dataclass
class ThirdJacobianBasisPreflight:
    basis: dict[int, ThirdBasisRecord] = field(default_factory=dict)
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
        third: ThirdForm,
    ) -> None:
        reduced_jacobian = dict(jacobian)
        factors: list[tuple[int, Fraction]] = []
        for pivot in sorted(self.basis):
            factor = reduced_jacobian.get(pivot, _ZERO)
            if not factor:
                continue
            factors.append((pivot, factor))
            second._add_scaled(reduced_jacobian, self.basis[pivot].jacobian, -factor)

        source_visits = sum(len(self.basis[pivot].third) for pivot, _factor in factors)
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

        reduced_third = dict(third)
        for pivot, factor in factors:
            second._add_scaled(reduced_third, self.basis[pivot].third, -factor)
        pivot = min(reduced_jacobian)
        scale = reduced_jacobian[pivot]
        normalized_jacobian = {
            index: value / scale for index, value in reduced_jacobian.items() if value
        }
        normalized_third = _scale_form(reduced_third, Fraction(1, 1) / scale)
        self.basis[pivot] = ThirdBasisRecord(normalized_jacobian, normalized_third)
        self.independent_rows += 1
        self.independent_add_scaled_calls += len(factors)
        self.independent_add_scaled_source_term_visits += source_visits

    def serialize(self, budget: dict[str, Any]) -> dict[str, Any]:
        forms = [self.basis[pivot].third for pivot in sorted(self.basis)]
        term_counts = [len(form) for form in forms]
        compact_bytes = sum(
            _compact_third_term_bytes(monomial, coefficient)
            for form in forms
            for monomial, coefficient in form.items()
        )
        conservative_bytes = (
            sum(term_counts) * int(budget["conservative_python_bytes_per_sparse_term"])
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
            "basis_forms_digest_sha256": _third_form_digest(forms),
            "Jacobian_echelon_digest_sha256": tangent._echelon_digest(
                {pivot: record.jacobian for pivot, record in self.basis.items()}
            ),
            "independent_add_scaled_calls": self.independent_add_scaled_calls,
            "independent_add_scaled_source_term_visits": (
                self.independent_add_scaled_source_term_visits
            ),
            "predicted_dependent_add_scaled_calls": (
                self.predicted_dependent_add_scaled_calls
            ),
            "predicted_dependent_source_term_visits": (
                self.predicted_dependent_source_term_visits
            ),
            "maximum_predicted_source_term_visits_one_dependent": (
                self.maximum_predicted_source_term_visits_one_dependent
            ),
            "selected_maximum_dependent_records": self.selected_maximum_dependent_records,
            "dependent_compatibility_forms_actually_reduced": 0,
        }


def _validate_budget(budget: dict[str, Any]) -> None:
    expected = {
        "schema_version": "final-theory-v042-955-slack-csg-third-order-budget-v1",
        "campaign": "955_CSG_FULL_SECOND_ORDER_JET_FIBER_THIRD_ORDER",
        "field": "QQ",
        "hard_memory_limit_bytes": 8 * 1024**3,
        "soft_memory_limit_bytes": 4 * 1024**3,
        "preflight_timeout_seconds": 600,
        "audit_timeout_seconds": 3600,
        "conservative_python_bytes_per_sparse_term": 512,
        "fixed_runtime_reserve_bytes": 512 * 1024**2,
        "compatibility_basis_term_limit": 10_000_000,
        "single_weighted_form_term_limit": WEIGHTED_MONOMIALS,
        "total_add_scaled_source_term_visits_limit": 200_000_000,
    }
    for key, value in expected.items():
        if budget.get(key) != value:
            raise AssertionError(f"third-order budget field changed: {key}")


def compile_slack_csg_third_order_preflight_v042(root: Path) -> dict[str, Any]:
    """Compile the bounded third-order full-jet-fibre resource preflight."""

    root = root.resolve()
    slack_path = root / SLACK_INVENTORY_PATH
    mixed_path = root / MIXED_MANIFEST_PATH
    tangent_path = root / TANGENT_PATH
    second_path = root / SECOND_ORDER_PATH
    budget_path = root / BUDGET_PATH
    slack = _load(slack_path)
    mixed = _load(mixed_path)
    tangent_predecessor = _load(tangent_path)
    second_predecessor = _load(second_path)
    budget = _load(budget_path)
    _validate_budget(budget)

    if slack.get("semantic_digest_sha256") != terms._semantic_digest(slack):
        raise AssertionError("slack inventory predecessor binding failed")
    if mixed.get("semantic_digest_sha256") != terms._semantic_digest(mixed):
        raise AssertionError("mixed manifest predecessor binding failed")
    if tangent_predecessor.get("semantic_digest_sha256") != tangent._semantic_digest(
        tangent_predecessor
    ):
        raise AssertionError("tangent predecessor binding failed")
    if (
        second_predecessor.get("verdict") != second.VERDICT
        or second_predecessor.get("semantic_digest_sha256")
        != second._semantic_digest(second_predecessor)
        or second_predecessor.get("semantic_digest_sha256")
        != "2c84fa6af833e320fe9e292a359808a7fcc162e225ce30edf038b5d352ae35f0"
    ):
        raise AssertionError("second-order predecessor binding failed")

    names: list[str] = []
    matrices, _states, expansion = terms._compile_matrices(slack, names)
    assignment, basepoint, _target = tangent._build_csg_assignment(
        slack, mixed, matrices, names
    )
    if len(names) != AMBIENT_COORDINATES:
        raise AssertionError("the unrestricted slack coordinate count changed")

    jacobian_rows: list[tangent.SparseRow] = []
    jacobian_ledger = terms.OperationLedger()
    for _identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, jacobian_ledger
    ):
        value, gradient = tangent._value_and_gradient(polynomial, assignment)
        if value:
            raise AssertionError("the CSG basepoint failed in the third-order preflight")
        if gradient:
            jacobian_rows.append(gradient)
    core_basis = tangent._echelon(jacobian_rows)
    if (
        len(core_basis) != 427
        or tangent._echelon_digest(core_basis)
        != second_predecessor["second_order_core_compatibility"][
            "Jacobian_echelon_digest_sha256"
        ]
    ):
        raise AssertionError("the core Jacobian changed before third order")

    free_coordinates, kernel_vectors, tangent_coordinate_forms = second._tangent_kernel(
        core_basis, len(names)
    )
    if len(kernel_vectors) != TANGENT_DIMENSION:
        raise AssertionError("the CSG tangent dimension changed")

    second_eliminator = second.SecondOrderEliminator(TANGENT_DIMENSION)
    second_ledger = terms.OperationLedger()
    for identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, second_ledger
    ):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        quadratic = second._quadratic_restriction(
            polynomial, assignment, tangent_coordinate_forms
        )
        second_eliminator.add(identifier, gradient, quadratic)
    if (
        second_eliminator.obstruction_basis
        or second_eliminator.nonzero_raw_obstruction_forms
        or second_eliminator.zero_raw_obstruction_forms != 3985
    ):
        raise AssertionError("the all-lift second-order conclusion changed")

    particular_forms = _particular_second_order_forms(second_eliminator, len(names))
    particular_profile = _particular_profile(particular_forms, names)

    block_censuses = {
        "CPOBC": WeightedThirdCensus("CPOBC"),
        "strong_GC": WeightedThirdCensus("strong_GC"),
    }
    combined_census = WeightedThirdCensus("CPOBC_plus_strong_GC")
    third_basis = ThirdJacobianBasisPreflight()
    third_ledger = terms.OperationLedger()
    second_order_residual_failures = 0
    for identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, third_ledger
    ):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        quadratic = second._quadratic_restriction(
            polynomial, assignment, tangent_coordinate_forms
        )
        residual = dict(quadratic)
        for index, coefficient in gradient.items():
            if particular_forms[index]:
                second._add_scaled(residual, particular_forms[index], coefficient)
        second_order_residual_failures += bool(residual)

        third_form = _third_order_restriction(
            polynomial,
            assignment,
            tangent_coordinate_forms,
            particular_forms,
        )
        if len(third_form) > int(budget["single_weighted_form_term_limit"]):
            raise RuntimeError("one raw third form exceeded the versioned term limit")
        block_censuses[identifier["block"]].add(identifier, third_form)
        combined_census.add(identifier, third_form)
        third_basis.add(identifier, gradient, third_form)
    if second_order_residual_failures:
        raise AssertionError("the canonical second-order correction failed a raw core equation")

    basis_profile = third_basis.serialize(budget)
    if (
        basis_profile["Jacobian_rank"] != 427
        or basis_profile["dependent_rows_not_compatibility_reduced"] != 3985
        or basis_profile["Jacobian_echelon_digest_sha256"]
        != tangent._echelon_digest(core_basis)
    ):
        raise AssertionError("the third-order preflight Jacobian basis drifted")

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    q_census = WeightedThirdCensus("Q_commutators")
    q_ledger = terms.OperationLedger()
    for identifier, polynomial in second._iter_q_polynomials(
        q_representatives, matrices, q_ledger
    ):
        third_form = _third_order_restriction(
            polynomial,
            assignment,
            tangent_coordinate_forms,
            particular_forms,
        )
        q_census.add(identifier, third_form)

    core_census = combined_census.finalize()
    q_profile = q_census.finalize()
    hard_memory = int(budget["hard_memory_limit_bytes"])
    soft_memory = int(budget["soft_memory_limit_bytes"])
    per_term = int(budget["conservative_python_bytes_per_sparse_term"])
    reserve = int(budget["fixed_runtime_reserve_bytes"])
    compatibility_cap = int(budget["compatibility_basis_term_limit"])
    bounded_audit_memory = (
        reserve
        + per_term
        * (basis_profile["basis_total_weighted_terms"] + compatibility_cap)
    )
    dense_worst_case_terms = 3985 * WEIGHTED_MONOMIALS
    dense_worst_case_bytes = reserve + per_term * dense_worst_case_terms
    preflight_safe = (
        basis_profile["basis_conservative_python_storage_estimate_bytes"] < soft_memory
        and core_census["maximum_terms_one_form"]
        <= int(budget["single_weighted_form_term_limit"])
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
            "formal_order_preflight": 3,
        },
        "input_bindings": {
            SLACK_INVENTORY_PATH: {
                "raw_sha256": _sha256(slack_path),
                "semantic_digest_sha256": slack["semantic_digest_sha256"],
            },
            MIXED_MANIFEST_PATH: {
                "raw_sha256": _sha256(mixed_path),
                "semantic_digest_sha256": mixed["semantic_digest_sha256"],
            },
            TANGENT_PATH: {
                "raw_sha256": _sha256(tangent_path),
                "semantic_digest_sha256": tangent_predecessor["semantic_digest_sha256"],
            },
            SECOND_ORDER_PATH: {
                "raw_sha256": _sha256(second_path),
                "semantic_digest_sha256": second_predecessor["semantic_digest_sha256"],
                "verdict": second_predecessor["verdict"],
            },
            BUDGET_PATH: {
                "raw_sha256": _sha256(budget_path),
                "content_digest_sha256": _object_digest(budget),
            },
        },
        "basepoint_recheck": {
            "assignment_sha256": basepoint["assignment_sha256"],
            "all_131_matrices_equal_diag_p_e_1": (
                basepoint["all_131_matrices_equal_diag_p_e_1"]
            ),
            "all_131_determinants_nonzero": basepoint["all_131_determinants_nonzero"],
        },
        "full_second_order_jet_fibre": {
            "first_order_tangent_variables_z": TANGENT_DIMENSION,
            "second_order_homogeneous_fibre_variables_a": TANGENT_DIMENSION,
            "coordinate_model": "w=w_particular(z)+K*a",
            "weighted_degrees": {"z": 1, "a": 2},
            "z_cubic_monomial_dimension": CUBIC_MONOMIALS,
            "z_times_a_monomial_dimension": BILINEAR_MONOMIALS,
            "total_weighted_third_monomial_dimension": WEIGHTED_MONOMIALS,
            "particular_second_order_correction": particular_profile,
            "tangent_basis_digest_sha256": second_predecessor["tangent_kernel"][
                "basis_digest_sha256"
            ],
            "free_ambient_coordinate_names": [names[index] for index in free_coordinates],
        },
        "raw_third_order_core_stream": {
            "per_block": {
                block: census.finalize() for block, census in block_censuses.items()
            },
            "combined": core_census,
            "all_raw_forms_retained": False,
            "streaming_rule": "expand_one_scalar_form_count_digest_then_discard",
            "ambient_polynomial_operation_ledger": third_ledger.serialize(),
        },
        "independent_Jacobian_basis_third_jet_preflight": basis_profile,
        "raw_Q_third_order_stream": {
            **q_profile,
            "intrinsic_Q_reduction_executed": False,
            "operation_ledger": q_ledger.serialize(),
        },
        "resource_decision": {
            "versioned_budget": budget,
            "basis_estimate_below_soft_memory_limit": (
                basis_profile["basis_conservative_python_storage_estimate_bytes"]
                < soft_memory
            ),
            "bounded_audit_conservative_peak_estimate_bytes": bounded_audit_memory,
            "bounded_audit_estimate_below_hard_memory_limit": (
                bounded_audit_memory < hard_memory
            ),
            "unbounded_dense_compatibility_basis_worst_case_terms": dense_worst_case_terms,
            "unbounded_dense_compatibility_basis_worst_case_bytes": dense_worst_case_bytes,
            "unbounded_dense_strategy_rejected": dense_worst_case_bytes > hard_memory,
            "fail_closed_streamed_third_order_audit_authorised": preflight_safe,
            "generic_solver_authorised": False,
            "next_gate": (
                "RUN_FAIL_CLOSED_STREAMED_THIRD_ORDER_CORE_COMPATIBILITY_AND_Q_ESCAPE_AUDIT"
                if preflight_safe
                else "STOP_AT_REACHABLE_VISIBILITY_OPEN_RESOURCE_LIMIT"
            ),
        },
        "execution_boundary": {
            "exact_sparse_QQ_weighted_jet_preflight_runs": 1,
            "independent_Jacobian_basis_third_jet_forms_retained": 427,
            "dependent_core_compatibility_reductions": 0,
            "Q_intrinsic_third_order_reductions": 0,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "generic_solver_run": False,
            "ambient_full_third_tensor_materialised": False,
            "dense_23226_column_matrix_materialised": False,
        },
        "claim_boundary": [
            (
                "This artifact is a deterministic resource preflight, not a third-order "
                "obstruction audit."
            ),
            "No dependent core row was reduced to a third-order compatibility form.",
            "Raw Q third jets were counted but not reduced modulo the core jet basis.",
            (
                "No claim is made about third-order Q escape, formal convergence, or remote "
                "components."
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
        payload["verdict"] = "V042_955_SLACK_CSG_THIRD_ORDER_PREFLIGHT_RESOURCE_LIMIT"
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_csg_third_order_preflight_v042(root: Path) -> Path:
    payload = compile_slack_csg_third_order_preflight_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_csg_third_order_preflight_v042(repository_root))
