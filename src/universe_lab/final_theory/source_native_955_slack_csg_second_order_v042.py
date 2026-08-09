"""Stream the second-order 955 core obstruction at the diagonal CSG point.

For the 49-dimensional exact tangent kernel ``K`` certified by the predecessor,
write a formal arc

``x(t) = x_CSG + t K z + t^2 w``.

Each core equation contributes ``J w + q(z)`` at order two.  This module
streams the exact scalar equations and performs simultaneous row elimination
on pairs ``(J-row, q-form)``.  Whenever the Jacobian part reduces to zero, the
remaining homogeneous quadratic form is a compatibility obstruction.  The Q
commutator jets are reduced by the same core basis, so their intrinsic order-2
forms can be compared with the compatibility span.

No ambient Hessian tensor, full scalar manifest, Groebner basis, saturation,
finite-field, numerical or Sage computation is used.  A second-order result is
still local and formal; it does not classify remote components.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

SLACK_INVENTORY_PATH = terms.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = tangent.MIXED_MANIFEST_PATH
TANGENT_PATH = tangent.RESULT_PATH
RESULT_PATH = "results/v0.4.2_955_slack_csg_second_order.json"

SCHEMA = "final-theory-v042-955-slack-csg-second-order-v1"
VERDICT = "V042_955_SLACK_CSG_SECOND_ORDER_ALL_TANGENTS_LIFT_Q_ESCAPE_BLOCKED_CERTIFIED"

QuadraticMonomial = tuple[int, int]
QuadraticForm = dict[QuadraticMonomial, Fraction]
TruncatedMonomial = tuple[int, ...]
TruncatedPolynomial = dict[TruncatedMonomial, Fraction]


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


def _add_scaled(
    target: dict[Any, Fraction], source: dict[Any, Fraction], coefficient: Fraction
) -> None:
    if not coefficient:
        return
    for key, value in source.items():
        updated = target.get(key, Fraction(0)) + coefficient * value
        if updated:
            target[key] = updated
        else:
            target.pop(key, None)


def _scaled(value: dict[Any, Fraction], coefficient: Fraction) -> dict[Any, Fraction]:
    return {key: coefficient * item for key, item in value.items() if coefficient * item}


def _truncated_multiply(
    left: TruncatedPolynomial, right: TruncatedPolynomial
) -> TruncatedPolynomial:
    result: TruncatedPolynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            if len(left_monomial) + len(right_monomial) > 2:
                continue
            monomial = tuple(sorted(left_monomial + right_monomial))
            updated = result.get(monomial, Fraction(0)) + left_coefficient * right_coefficient
            if updated:
                result[monomial] = updated
            else:
                result.pop(monomial, None)
    return result


def _quadratic_restriction(
    polynomial: terms.Polynomial,
    assignment: list[Fraction],
    tangent_coordinate_forms: list[dict[int, Fraction]],
) -> QuadraticForm:
    result: QuadraticForm = {}
    for ambient_monomial, integer_coefficient in polynomial.items():
        truncated: TruncatedPolynomial = {(): Fraction(integer_coefficient)}
        for ambient_index in ambient_monomial:
            factor: TruncatedPolynomial = {}
            constant = assignment[ambient_index]
            if constant:
                factor[()] = constant
            factor.update(
                {
                    (tangent_index,): coefficient
                    for tangent_index, coefficient in tangent_coordinate_forms[
                        ambient_index
                    ].items()
                    if coefficient
                }
            )
            truncated = _truncated_multiply(truncated, factor)
            if not truncated:
                break
        for monomial, coefficient in truncated.items():
            if len(monomial) != 2:
                continue
            quadratic_monomial = (monomial[0], monomial[1])
            updated = result.get(quadratic_monomial, Fraction(0)) + coefficient
            if updated:
                result[quadratic_monomial] = updated
            else:
                result.pop(quadratic_monomial, None)
    return result


def _form_record(form: QuadraticForm) -> list[list[Any]]:
    return [
        [[left, right], str(coefficient)] for (left, right), coefficient in sorted(form.items())
    ]


def _form_digest(forms: list[QuadraticForm]) -> str:
    return hashlib.sha256(
        _canonical_json([_form_record(form) for form in forms]).encode("utf-8")
    ).hexdigest()


def _reduce_form(
    form: QuadraticForm, basis: dict[QuadraticMonomial, QuadraticForm]
) -> QuadraticForm:
    result = dict(form)
    for pivot in sorted(basis):
        factor = result.get(pivot, Fraction(0))
        if factor:
            _add_scaled(result, basis[pivot], -factor)
    return result


def _extend_form_basis(basis: dict[QuadraticMonomial, QuadraticForm], form: QuadraticForm) -> bool:
    reduced = _reduce_form(form, basis)
    if not reduced:
        return False
    pivot = min(reduced)
    basis[pivot] = _scaled(reduced, Fraction(1, 1) / reduced[pivot])
    return True


def _form_basis_digest(basis: dict[QuadraticMonomial, QuadraticForm]) -> str:
    return _form_digest([basis[pivot] for pivot in sorted(basis)])


def _iter_relation_polynomials(
    block_name: str,
    records: list[dict[str, Any]],
    identifier_keys: tuple[str, ...],
    matrices: dict[str, terms.Matrix],
    ledger: terms.OperationLedger,
) -> Iterator[tuple[dict[str, Any], terms.Polynomial]]:
    for block_index, record in enumerate(records):
        left = terms._word_matrix(record["lhs_source_word"], matrices, ledger)
        right = terms._word_matrix(record["rhs_source_word"], matrices, ledger)
        for row in range(2):
            for column in range(2):
                residual = terms._add(
                    left[row][column],
                    terms._scale(-1, right[row][column], ledger),
                    ledger,
                )
                yield (
                    {
                        "block": block_name,
                        "block_index": block_index,
                        **{key: record[key] for key in identifier_keys if key in record},
                        "entry": f"{row}{column}",
                    },
                    residual,
                )


def _iter_core_polynomials(
    slack: dict[str, Any],
    matrices: dict[str, terms.Matrix],
    ledger: terms.OperationLedger,
) -> Iterator[tuple[dict[str, Any], terms.Polynomial]]:
    yield from _iter_relation_polynomials(
        "CPOBC",
        slack["raw_source_system"]["CPOBC_equations"],
        ("relation_id", "equation_id"),
        matrices,
        ledger,
    )
    yield from _iter_relation_polynomials(
        "strong_GC",
        slack["raw_source_system"]["strong_GC_basis"],
        ("relation_id", "endpoint_causet_id"),
        matrices,
        ledger,
    )


def _iter_q_polynomials(
    q_representatives: dict[int, str],
    matrices: dict[str, terms.Matrix],
    ledger: terms.OperationLedger,
) -> Iterator[tuple[dict[str, Any], terms.Polynomial]]:
    for left in range(1, 5):
        for right in range(left + 1, 5):
            left_right = terms._matrix_multiply(
                matrices[q_representatives[left]],
                matrices[q_representatives[right]],
                ledger,
            )
            right_left = terms._matrix_multiply(
                matrices[q_representatives[right]],
                matrices[q_representatives[left]],
                ledger,
            )
            for row in range(2):
                for column in range(2):
                    yield (
                        {
                            "pair": [left, right],
                            "entry": f"{row}{column}",
                        },
                        terms._add(
                            left_right[row][column],
                            terms._scale(-1, right_left[row][column], ledger),
                            ledger,
                        ),
                    )


@dataclass
class JetBasisRecord:
    jacobian: tangent.SparseRow
    quadratic: QuadraticForm


@dataclass
class SecondOrderEliminator:
    tangent_dimension: int
    jacobian_basis: dict[int, JetBasisRecord] = field(default_factory=dict)
    obstruction_basis: dict[QuadraticMonomial, QuadraticForm] = field(default_factory=dict)
    scalar_slots: int = 0
    independent_jacobian_rows: int = 0
    dependent_jacobian_rows: int = 0
    nonzero_raw_obstruction_forms: int = 0
    zero_raw_obstruction_forms: int = 0
    raw_obstruction_term_histogram: Counter[int] = field(default_factory=Counter)
    maximum_raw_obstruction_terms: int = 0
    maximum_raw_obstruction_records: list[dict[str, Any]] = field(default_factory=list)
    maximum_raw_obstruction_record_ties: int = 0
    maximum_jet_basis_quadratic_terms: int = 0
    quadratic_add_scaled_calls: int = 0
    obstruction_digest: Any = field(default_factory=hashlib.sha256)

    def _reduce_jet(
        self, jacobian: tangent.SparseRow, quadratic: QuadraticForm
    ) -> tuple[tangent.SparseRow, QuadraticForm]:
        reduced_jacobian = dict(jacobian)
        reduced_quadratic = dict(quadratic)
        for pivot in sorted(self.jacobian_basis):
            factor = reduced_jacobian.get(pivot, Fraction(0))
            if not factor:
                continue
            basis = self.jacobian_basis[pivot]
            _add_scaled(reduced_jacobian, basis.jacobian, -factor)
            _add_scaled(reduced_quadratic, basis.quadratic, -factor)
            self.quadratic_add_scaled_calls += 1
        return reduced_jacobian, reduced_quadratic

    def add(
        self,
        identifier: dict[str, Any],
        jacobian: tangent.SparseRow,
        quadratic: QuadraticForm,
    ) -> None:
        self.scalar_slots += 1
        reduced_jacobian, reduced_quadratic = self._reduce_jet(jacobian, quadratic)
        if reduced_jacobian:
            pivot = min(reduced_jacobian)
            scale = reduced_jacobian[pivot]
            normalized_jacobian = {
                index: value / scale for index, value in reduced_jacobian.items() if value
            }
            normalized_quadratic = _scaled(reduced_quadratic, Fraction(1, 1) / scale)
            self.jacobian_basis[pivot] = JetBasisRecord(normalized_jacobian, normalized_quadratic)
            self.independent_jacobian_rows += 1
            self.maximum_jet_basis_quadratic_terms = max(
                self.maximum_jet_basis_quadratic_terms,
                len(normalized_quadratic),
            )
            return

        self.dependent_jacobian_rows += 1
        terms_count = len(reduced_quadratic)
        self.raw_obstruction_term_histogram[terms_count] += 1
        self.obstruction_digest.update(
            _canonical_json([identifier, _form_record(reduced_quadratic)]).encode("utf-8")
        )
        self.obstruction_digest.update(b"\n")
        if reduced_quadratic:
            self.nonzero_raw_obstruction_forms += 1
            if terms_count > self.maximum_raw_obstruction_terms:
                self.maximum_raw_obstruction_terms = terms_count
                self.maximum_raw_obstruction_record_ties = 1
                self.maximum_raw_obstruction_records = [
                    {**identifier, "quadratic_terms": terms_count}
                ]
            elif terms_count == self.maximum_raw_obstruction_terms:
                self.maximum_raw_obstruction_record_ties += 1
                if len(self.maximum_raw_obstruction_records) < 20:
                    self.maximum_raw_obstruction_records.append(
                        {**identifier, "quadratic_terms": terms_count}
                    )
            _extend_form_basis(self.obstruction_basis, reduced_quadratic)
        else:
            self.zero_raw_obstruction_forms += 1

    def reduce_external_jet(
        self, jacobian: tangent.SparseRow, quadratic: QuadraticForm
    ) -> tuple[tangent.SparseRow, QuadraticForm]:
        return self._reduce_jet(jacobian, quadratic)

    def serialize(self) -> dict[str, Any]:
        return {
            "scalar_slots": self.scalar_slots,
            "Jacobian_rank": len(self.jacobian_basis),
            "independent_Jacobian_rows": self.independent_jacobian_rows,
            "dependent_Jacobian_rows": self.dependent_jacobian_rows,
            "raw_nonzero_compatibility_forms": self.nonzero_raw_obstruction_forms,
            "raw_zero_compatibility_forms": self.zero_raw_obstruction_forms,
            "raw_compatibility_term_histogram": {
                str(count): occurrences
                for count, occurrences in sorted(self.raw_obstruction_term_histogram.items())
            },
            "maximum_terms_one_raw_compatibility_form": (self.maximum_raw_obstruction_terms),
            "maximum_nonzero_term_record_ties": self.maximum_raw_obstruction_record_ties,
            "selected_maximum_nonzero_term_records": self.maximum_raw_obstruction_records,
            "compatibility_quadratic_span_rank": len(self.obstruction_basis),
            "quadratic_monomial_ambient_dimension": (
                self.tangent_dimension * (self.tangent_dimension + 1) // 2
            ),
            "Jacobian_echelon_digest_sha256": tangent._echelon_digest(
                {pivot: record.jacobian for pivot, record in self.jacobian_basis.items()}
            ),
            "compatibility_echelon_digest_sha256": _form_basis_digest(self.obstruction_basis),
            "raw_compatibility_stream_digest_sha256": (self.obstruction_digest.hexdigest()),
            "maximum_quadratic_terms_in_one_Jacobian_basis_jet": (
                self.maximum_jet_basis_quadratic_terms
            ),
            "quadratic_add_scaled_calls": self.quadratic_add_scaled_calls,
        }


def _tangent_kernel(
    core_basis: dict[int, tangent.SparseRow], variable_count: int
) -> tuple[list[int], list[tangent.SparseRow], list[dict[int, Fraction]]]:
    free_coordinates = sorted(set(range(variable_count)) - set(core_basis))
    vectors = [
        tangent._kernel_vector_for_free_coordinate(core_basis, variable_count, free_coordinate)
        for free_coordinate in free_coordinates
    ]
    coordinate_forms: list[dict[int, Fraction]] = [
        {
            tangent_index: vector[ambient_index]
            for tangent_index, vector in enumerate(vectors)
            if ambient_index in vector
        }
        for ambient_index in range(variable_count)
    ]
    return free_coordinates, vectors, coordinate_forms


def _kernel_profile(
    free_coordinates: list[int],
    vectors: list[tangent.SparseRow],
    coordinate_forms: list[dict[int, Fraction]],
    names: list[str],
) -> dict[str, Any]:
    vector_supports = [len(vector) for vector in vectors]
    coordinate_supports = [len(form) for form in coordinate_forms]
    digest = hashlib.sha256(
        _canonical_json(
            [[[index, str(value)] for index, value in sorted(vector.items())] for vector in vectors]
        ).encode("utf-8")
    ).hexdigest()
    return {
        "dimension": len(vectors),
        "free_ambient_coordinates": [names[index] for index in free_coordinates],
        "basis_support_histogram": {
            str(size): vector_supports.count(size) for size in sorted(set(vector_supports))
        },
        "maximum_basis_vector_support": max(vector_supports, default=0),
        "total_basis_vector_support": sum(vector_supports),
        "ambient_coordinate_tangent_support_histogram": {
            str(size): coordinate_supports.count(size) for size in sorted(set(coordinate_supports))
        },
        "maximum_tangent_variables_in_one_ambient_coordinate": max(coordinate_supports, default=0),
        "ambient_coordinates_zero_on_entire_tangent_kernel": sum(
            size == 0 for size in coordinate_supports
        ),
        "basis_digest_sha256": digest,
    }


def compile_slack_csg_second_order_v042(root: Path) -> dict[str, Any]:
    """Compile second-order compatibility and Q escape modulo the core."""

    root = root.resolve()
    slack_path = root / SLACK_INVENTORY_PATH
    mixed_path = root / MIXED_MANIFEST_PATH
    tangent_path = root / TANGENT_PATH
    slack = _load(slack_path)
    mixed = _load(mixed_path)
    tangent_predecessor = _load(tangent_path)
    if slack.get(
        "schema_version"
    ) != "final-theory-v042-955-source-native-slack-compiler-v1" or slack.get(
        "semantic_digest_sha256"
    ) != terms._semantic_digest(slack):
        raise AssertionError("slack inventory predecessor binding failed")
    if mixed.get(
        "schema_version"
    ) != "final-theory-v042-955-mixed-source-native-manifest-v1" or mixed.get(
        "semantic_digest_sha256"
    ) != terms._semantic_digest(mixed):
        raise AssertionError("mixed CSG-character predecessor binding failed")
    if (
        tangent_predecessor.get("schema_version") != "final-theory-v042-955-slack-csg-tangent-v1"
        or tangent_predecessor.get("verdict")
        != "V042_955_SLACK_CSG_Q_TANGENT_ESCAPE_FIRST_ORDER_BLOCKED_CERTIFIED"
        or tangent_predecessor.get("semantic_digest_sha256")
        != tangent._semantic_digest(tangent_predecessor)
    ):
        raise AssertionError("CSG tangent predecessor binding failed")

    names: list[str] = []
    matrices, _states, expansion = terms._compile_matrices(slack, names)
    assignment, basepoint, _target = tangent._build_csg_assignment(slack, mixed, matrices, names)

    jacobian_rows: list[tangent.SparseRow] = []
    jacobian_ledger = terms.OperationLedger()
    residual_failures = 0
    for _identifier, polynomial in _iter_core_polynomials(slack, matrices, jacobian_ledger):
        value, gradient = tangent._value_and_gradient(polynomial, assignment)
        residual_failures += bool(value)
        if gradient:
            jacobian_rows.append(gradient)
    if residual_failures:
        raise AssertionError("the diagonal CSG point failed during second-order setup")
    core_basis = tangent._echelon(jacobian_rows)
    if (
        len(core_basis) != tangent_predecessor["core_Jacobian"]["combined_rank"]
        or tangent._echelon_digest(core_basis)
        != tangent_predecessor["core_Jacobian"]["combined_echelon_digest_sha256"]
    ):
        raise AssertionError("the first-order core Jacobian drifted")

    free_coordinates, kernel_vectors, tangent_coordinate_forms = _tangent_kernel(
        core_basis, len(names)
    )
    if len(kernel_vectors) != 49:
        raise AssertionError("the CSG tangent kernel is no longer 49-dimensional")
    kernel_profile = _kernel_profile(
        free_coordinates, kernel_vectors, tangent_coordinate_forms, names
    )

    blind_names = tangent_predecessor["terminal_slack_blind_directions"]["coordinates"]
    free_name_to_tangent = {
        names[ambient_index]: tangent_index
        for tangent_index, ambient_index in enumerate(free_coordinates)
    }
    missing_blind_tangent_coordinates = [
        name for name in blind_names if name not in free_name_to_tangent
    ]
    if missing_blind_tangent_coordinates:
        raise AssertionError("a terminal slack blind coordinate is not a free tangent coordinate")
    blind_tangent_indices = {free_name_to_tangent[name] for name in blind_names}

    eliminator = SecondOrderEliminator(len(kernel_vectors))
    quadratic_ledger = terms.OperationLedger()
    restricted_linear_failures = 0
    basepoint_failures = 0
    core_raw_quadratic_blind_occurrences = 0
    for identifier, polynomial in _iter_core_polynomials(slack, matrices, quadratic_ledger):
        value, gradient = tangent._value_and_gradient(polynomial, assignment)
        basepoint_failures += bool(value)
        restricted_linear_failures += any(
            tangent._dot(gradient, vector) for vector in kernel_vectors
        )
        quadratic = _quadratic_restriction(polynomial, assignment, tangent_coordinate_forms)
        core_raw_quadratic_blind_occurrences += sum(
            any(index in monomial for index in blind_tangent_indices) for monomial in quadratic
        )
        eliminator.add(identifier, gradient, quadratic)
    if basepoint_failures or restricted_linear_failures:
        raise AssertionError("the selected kernel failed the streamed first-order checks")
    if (
        len(eliminator.jacobian_basis) != 427
        or tangent._echelon_digest(
            {pivot: record.jacobian for pivot, record in eliminator.jacobian_basis.items()}
        )
        != tangent_predecessor["core_Jacobian"]["combined_echelon_digest_sha256"]
    ):
        raise AssertionError("simultaneous jet elimination changed the Jacobian echelon")

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    q_ledger = terms.OperationLedger()
    q_records: list[dict[str, Any]] = []
    q_intrinsic_forms: list[QuadraticForm] = []
    q_jacobian_remainder_failures = 0
    q_basepoint_failures = 0
    q_compatibility_remainders: list[QuadraticForm] = []
    q_raw_quadratic_blind_occurrences = 0
    for identifier, polynomial in _iter_q_polynomials(q_representatives, matrices, q_ledger):
        value, gradient = tangent._value_and_gradient(polynomial, assignment)
        q_basepoint_failures += bool(value)
        quadratic = _quadratic_restriction(polynomial, assignment, tangent_coordinate_forms)
        q_raw_quadratic_blind_occurrences += sum(
            any(index in monomial for index in blind_tangent_indices) for monomial in quadratic
        )
        jacobian_remainder, intrinsic = eliminator.reduce_external_jet(gradient, quadratic)
        q_jacobian_remainder_failures += bool(jacobian_remainder)
        q_intrinsic_forms.append(intrinsic)
        compatibility_remainder = _reduce_form(intrinsic, eliminator.obstruction_basis)
        q_compatibility_remainders.append(compatibility_remainder)
        q_records.append(
            {
                **identifier,
                "ambient_Jacobian_terms": len(gradient),
                "restricted_raw_quadratic_terms": len(quadratic),
                "intrinsic_quadratic_terms_after_core_Jacobian_elimination": len(intrinsic),
                "compatibility_span_remainder_terms": len(compatibility_remainder),
                "compatibility_span_remainder": _form_record(compatibility_remainder),
            }
        )
    if q_basepoint_failures or q_jacobian_remainder_failures:
        raise AssertionError("Q jets failed their basepoint or first-order containment checks")

    intrinsic_q_basis: dict[QuadraticMonomial, QuadraticForm] = {}
    q_modulo_compatibility_basis: dict[QuadraticMonomial, QuadraticForm] = {}
    for intrinsic, remainder in zip(q_intrinsic_forms, q_compatibility_remainders, strict=True):
        _extend_form_basis(intrinsic_q_basis, intrinsic)
        _extend_form_basis(q_modulo_compatibility_basis, remainder)
    q_modulo_compatibility_rank = len(q_modulo_compatibility_basis)
    if (
        eliminator.nonzero_raw_obstruction_forms
        or eliminator.obstruction_basis
        or any(q_intrinsic_forms)
        or q_modulo_compatibility_rank
    ):
        raise AssertionError("the CSG second-order all-lift blocked verdict changed")

    compatibility_blind_occurrences = sum(
        any(index in monomial for index in blind_tangent_indices)
        for form in eliminator.obstruction_basis.values()
        for monomial in form
    )
    q_blind_occurrences = sum(
        any(index in monomial for index in blind_tangent_indices)
        for form in q_intrinsic_forms
        for monomial in form
    )
    if (
        core_raw_quadratic_blind_occurrences
        or q_raw_quadratic_blind_occurrences
        or compatibility_blind_occurrences
        or q_blind_occurrences
    ):
        raise AssertionError("globally blind slack coordinates appeared at second order")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "basepoint": "diagonal CSG t_j=1 source matrices",
            "formal_order": 2,
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
                "verdict": tangent_predecessor["verdict"],
            },
        },
        "basepoint_recheck": {
            "assignment_sha256": basepoint["assignment_sha256"],
            "nonzero_slack_coordinates": basepoint["nonzero_slack_coordinate_count"],
            "all_131_matrices_equal_diag_p_e_1": basepoint["all_131_matrices_equal_diag_p_e_1"],
            "all_131_determinants_nonzero": basepoint["all_131_determinants_nonzero"],
            "core_residual_failures": residual_failures,
        },
        "tangent_kernel": kernel_profile,
        "second_order_core_compatibility": {
            **eliminator.serialize(),
            "basepoint_failures": basepoint_failures,
            "restricted_linear_failures": restricted_linear_failures,
            "formal_equation": "J_core*w + q_core(z) = 0",
            "compatibility_meaning": (
                "The zero-Jacobian remainders after simultaneous jet elimination "
                "must vanish for a tangent vector z to lift through order two."
            ),
            "every_first_order_tangent_lifts_through_second_order": True,
            "operation_ledger": quadratic_ledger.serialize(),
        },
        "Q_second_order_modulo_core": {
            "Q_representatives": {
                f"Q{stage}": representative
                for stage, representative in sorted(q_representatives.items())
            },
            "scalar_entry_slots": len(q_records),
            "basepoint_failures": q_basepoint_failures,
            "first_order_Jacobian_remainder_failures": (q_jacobian_remainder_failures),
            "nonzero_intrinsic_quadratic_forms": sum(bool(form) for form in q_intrinsic_forms),
            "intrinsic_quadratic_span_rank": len(intrinsic_q_basis),
            "intrinsic_quadratic_echelon_digest_sha256": _form_basis_digest(intrinsic_q_basis),
            "compatibility_span_remainder_nonzero_forms": sum(
                bool(form) for form in q_compatibility_remainders
            ),
            "rank_modulo_core_compatibility_span": q_modulo_compatibility_rank,
            "all_Q_second_order_forms_in_compatibility_span": (q_modulo_compatibility_rank == 0),
            "second_order_Q_escape_blocked_by_linear_span": (q_modulo_compatibility_rank == 0),
            "Q_commutators_vanish_through_order_two_on_every_core_lift": True,
            "remainder_echelon_digest_sha256": _form_basis_digest(q_modulo_compatibility_basis),
            "records": q_records,
            "operation_ledger": q_ledger.serialize(),
        },
        "terminal_slack_blind_directions": {
            "ambient_coordinate_names": blind_names,
            "tangent_coordinate_indices": sorted(blind_tangent_indices),
            "count": len(blind_names),
            "raw_core_quadratic_monomial_occurrences": (
                core_raw_quadratic_blind_occurrences
            ),
            "raw_Q_quadratic_monomial_occurrences": q_raw_quadratic_blind_occurrences,
            "compatibility_quadratic_monomial_occurrences": (compatibility_blind_occurrences),
            "Q_intrinsic_quadratic_monomial_occurrences": q_blind_occurrences,
            "remain_core_and_Q_silent_through_order_two": True,
        },
        "resource_boundary": {
            "ambient_Hessian_tensor_materialised": False,
            "full_scalar_manifest_materialised": False,
            "maximum_possible_quadratic_monomials": 49 * 50 // 2,
            "timid_expansion_operation_ledger": expansion["operation_ledger"],
            "first_order_recheck_operation_ledger": jacobian_ledger.serialize(),
        },
        "execution_decision": {
            "generic_solver_authorised": False,
            "higher_order_formal_audit_authorised": (q_modulo_compatibility_rank == 0),
            "next_gate": (
                "PREFLIGHT_THEN_STREAM_THE_THIRD_ORDER_CORE_COMPATIBILITY_AND_Q_"
                "ESCAPE_ON_THE_FULL_SECOND_ORDER_CSG_JET_FIBER"
                if q_modulo_compatibility_rank == 0
                else "ANALYSE_THE_NONZERO_Q_SECOND_ORDER_REMAINDER_ON_THE_QUADRATIC_CONE"
            ),
        },
        "solver_status": {
            "exact_sparse_QQ_jet_linear_algebra_runs": 1,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "All results are formal and local at the diagonal CSG point through order two.",
            "Linear-span containment is sufficient to block Q at order two on compatible jets.",
            "No claim is made about third or higher order, convergence, or remote components.",
            "Eq113 and Eq139 remain separate downstream witness-validation gates.",
            "No unrestricted source-native 955 terminal verdict is claimed.",
        ],
        "unrestricted_source_native_955_status": "OPEN",
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_csg_second_order_v042(root: Path) -> Path:
    payload = compile_slack_csg_second_order_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_csg_second_order_v042(repository_root))
