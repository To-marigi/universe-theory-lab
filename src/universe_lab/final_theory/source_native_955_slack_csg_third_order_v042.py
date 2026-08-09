"""Audit third-order 955 compatibility and Q escape at the CSG point.

The predecessor preflight fixes the full second-order jet fibre

``x(t)=x_CSG+t*K*z+t^2*(w_particular(z)+K*a)+t^3*v``.

This module streams every exact core order-three jet, simultaneously reduces
the pair ``(Jacobian row, weighted third form)``, and forms the compatibility
span from the 3,985 dependent rows.  The 24 Q-commutator jets are then reduced
through both the core Jacobian-jet basis and that compatibility span.

All sparse operations are fail-closed under the versioned 8 GiB budget.  No
generic solver, dense 23,226-column matrix, Groebner basis, saturation,
finite-field, numerical, or Sage computation is used.
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
    source_native_955_slack_csg_third_order_preflight_v042 as preflight,
)
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

SLACK_INVENTORY_PATH = preflight.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = preflight.MIXED_MANIFEST_PATH
TANGENT_PATH = preflight.TANGENT_PATH
SECOND_ORDER_PATH = preflight.SECOND_ORDER_PATH
BUDGET_PATH = preflight.BUDGET_PATH
PREFLIGHT_PATH = preflight.RESULT_PATH
RESULT_PATH = "results/v0.4.2_955_slack_csg_third_order.json"

SCHEMA = "final-theory-v042-955-slack-csg-third-order-v1"
VERDICT_ALL_LIFT_Q_BLOCKED = (
    "V042_955_SLACK_CSG_THIRD_ORDER_ALL_SECOND_ORDER_JETS_LIFT_"
    "Q_ESCAPE_BLOCKED_CERTIFIED"
)
VERDICT_COMPATIBILITY_Q_BLOCKED = (
    "V042_955_SLACK_CSG_THIRD_ORDER_CORE_COMPATIBILITY_"
    "Q_ESCAPE_BLOCKED_BY_SPAN_CERTIFIED"
)
VERDICT_Q_SPAN_ESCAPE = (
    "V042_955_SLACK_CSG_THIRD_ORDER_Q_LINEAR_SPAN_ESCAPE_CANDIDATE_CERTIFIED"
)

ThirdForm = preflight.ThirdForm
ThirdMonomial = preflight.ThirdMonomial
_ZERO = Fraction(0)


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


def _reduce_third_form(
    form: ThirdForm,
    basis: dict[ThirdMonomial, ThirdForm],
    ledger: ThirdReductionLedger | None = None,
) -> ThirdForm:
    result = dict(form)
    for pivot in sorted(basis):
        factor = result.get(pivot, _ZERO)
        if not factor:
            continue
        if ledger is not None:
            ledger.observe_add_scaled(basis[pivot])
        second._add_scaled(result, basis[pivot], -factor)
    return result


def _extend_third_basis(
    basis: dict[ThirdMonomial, ThirdForm],
    form: ThirdForm,
    ledger: ThirdReductionLedger | None = None,
) -> bool:
    reduced = _reduce_third_form(form, basis, ledger)
    if not reduced:
        return False
    pivot = min(reduced)
    basis[pivot] = preflight._scale_form(reduced, Fraction(1, 1) / reduced[pivot])
    return True


def _basis_digest(basis: dict[ThirdMonomial, ThirdForm]) -> str:
    return preflight._third_form_digest([basis[pivot] for pivot in sorted(basis)])


def _blind_occurrences(form: ThirdForm, blind_indices: set[int]) -> int:
    occurrences = 0
    for monomial in form:
        kind = preflight._third_kind(monomial)
        if kind == "z_cubic":
            occurrences += any(index in blind_indices for index in monomial[1:])
        else:
            occurrences += monomial[1] in blind_indices or monomial[2] in blind_indices
    return occurrences


@dataclass
class ThirdReductionLedger:
    add_scaled_calls: int = 0
    source_term_visits: int = 0
    maximum_source_terms_one_call: int = 0

    def observe_add_scaled(self, source: ThirdForm) -> None:
        self.add_scaled_calls += 1
        terms_count = len(source)
        self.source_term_visits += terms_count
        self.maximum_source_terms_one_call = max(
            self.maximum_source_terms_one_call, terms_count
        )

    def serialize(self) -> dict[str, int]:
        return {
            "add_scaled_calls": self.add_scaled_calls,
            "source_term_visits": self.source_term_visits,
            "maximum_source_terms_one_call": self.maximum_source_terms_one_call,
        }


@dataclass
class ThirdJetBasisRecord:
    jacobian: tangent.SparseRow
    third: ThirdForm


@dataclass
class ThirdOrderEliminator:
    budget: dict[str, Any]
    jacobian_basis: dict[int, ThirdJetBasisRecord] = field(default_factory=dict)
    compatibility_basis: dict[ThirdMonomial, ThirdForm] = field(default_factory=dict)
    scalar_slots: int = 0
    independent_jacobian_rows: int = 0
    dependent_jacobian_rows: int = 0
    raw_nonzero_compatibility_forms: int = 0
    raw_zero_compatibility_forms: int = 0
    raw_compatibility_term_histogram: Counter[int] = field(default_factory=Counter)
    maximum_raw_compatibility_terms: int = 0
    maximum_raw_compatibility_ties: int = 0
    selected_maximum_raw_records: list[dict[str, Any]] = field(default_factory=list)
    raw_compatibility_digest: Any = field(default_factory=hashlib.sha256)
    jacobian_reduction_ledger: ThirdReductionLedger = field(
        default_factory=ThirdReductionLedger
    )
    compatibility_reduction_ledger: ThirdReductionLedger = field(
        default_factory=ThirdReductionLedger
    )

    def _check_caps(self, form: ThirdForm) -> None:
        if len(form) > int(self.budget["single_weighted_form_term_limit"]):
            raise RuntimeError("one third-order form exceeded the fail-closed term cap")
        total_basis_terms = sum(len(value) for value in self.compatibility_basis.values())
        if total_basis_terms > int(self.budget["compatibility_basis_term_limit"]):
            raise RuntimeError("the third-order compatibility basis exceeded its term cap")
        visits = (
            self.jacobian_reduction_ledger.source_term_visits
            + self.compatibility_reduction_ledger.source_term_visits
        )
        if visits > int(self.budget["total_add_scaled_source_term_visits_limit"]):
            raise RuntimeError("third-order reductions exceeded their source-term visit cap")

    def _reduce_jacobian_jet(
        self,
        jacobian: tangent.SparseRow,
        third: ThirdForm,
    ) -> tuple[tangent.SparseRow, ThirdForm]:
        reduced_jacobian = dict(jacobian)
        reduced_third = dict(third)
        for pivot in sorted(self.jacobian_basis):
            factor = reduced_jacobian.get(pivot, _ZERO)
            if not factor:
                continue
            record = self.jacobian_basis[pivot]
            second._add_scaled(reduced_jacobian, record.jacobian, -factor)
            self.jacobian_reduction_ledger.observe_add_scaled(record.third)
            second._add_scaled(reduced_third, record.third, -factor)
        self._check_caps(reduced_third)
        return reduced_jacobian, reduced_third

    def add(
        self,
        identifier: dict[str, Any],
        jacobian: tangent.SparseRow,
        third: ThirdForm,
    ) -> None:
        self.scalar_slots += 1
        reduced_jacobian, reduced_third = self._reduce_jacobian_jet(jacobian, third)
        if reduced_jacobian:
            pivot = min(reduced_jacobian)
            scale = reduced_jacobian[pivot]
            self.jacobian_basis[pivot] = ThirdJetBasisRecord(
                {
                    index: value / scale
                    for index, value in reduced_jacobian.items()
                    if value
                },
                preflight._scale_form(reduced_third, Fraction(1, 1) / scale),
            )
            self.independent_jacobian_rows += 1
            return

        self.dependent_jacobian_rows += 1
        terms_count = len(reduced_third)
        self.raw_compatibility_term_histogram[terms_count] += 1
        self.raw_compatibility_digest.update(
            _canonical_json(
                [identifier, preflight._third_form_record(reduced_third)]
            ).encode("utf-8")
        )
        self.raw_compatibility_digest.update(b"\n")
        if reduced_third:
            self.raw_nonzero_compatibility_forms += 1
            if terms_count > self.maximum_raw_compatibility_terms:
                self.maximum_raw_compatibility_terms = terms_count
                self.maximum_raw_compatibility_ties = 1
                self.selected_maximum_raw_records = [
                    {**identifier, "weighted_terms": terms_count}
                ]
            elif terms_count == self.maximum_raw_compatibility_terms:
                self.maximum_raw_compatibility_ties += 1
                if len(self.selected_maximum_raw_records) < 20:
                    self.selected_maximum_raw_records.append(
                        {**identifier, "weighted_terms": terms_count}
                    )
            _extend_third_basis(
                self.compatibility_basis,
                reduced_third,
                self.compatibility_reduction_ledger,
            )
        else:
            self.raw_zero_compatibility_forms += 1
        self._check_caps(reduced_third)

    def reduce_external_jet(
        self,
        jacobian: tangent.SparseRow,
        third: ThirdForm,
    ) -> tuple[tangent.SparseRow, ThirdForm]:
        return self._reduce_jacobian_jet(jacobian, third)

    def serialize(self) -> dict[str, Any]:
        jacobian_forms = [
            self.jacobian_basis[pivot].third for pivot in sorted(self.jacobian_basis)
        ]
        compatibility_forms = [
            self.compatibility_basis[pivot] for pivot in sorted(self.compatibility_basis)
        ]
        return {
            "scalar_slots": self.scalar_slots,
            "Jacobian_rank": len(self.jacobian_basis),
            "independent_Jacobian_rows": self.independent_jacobian_rows,
            "dependent_Jacobian_rows": self.dependent_jacobian_rows,
            "raw_nonzero_compatibility_forms": self.raw_nonzero_compatibility_forms,
            "raw_zero_compatibility_forms": self.raw_zero_compatibility_forms,
            "raw_compatibility_term_histogram": {
                str(count): occurrences
                for count, occurrences in sorted(
                    self.raw_compatibility_term_histogram.items()
                )
            },
            "maximum_terms_one_raw_compatibility_form": (
                self.maximum_raw_compatibility_terms
            ),
            "maximum_nonzero_raw_compatibility_term_record_ties": (
                self.maximum_raw_compatibility_ties
            ),
            "selected_maximum_nonzero_raw_compatibility_records": (
                self.selected_maximum_raw_records
            ),
            "compatibility_span_rank": len(self.compatibility_basis),
            "compatibility_basis_total_terms": sum(map(len, compatibility_forms)),
            "compatibility_basis_maximum_terms_one_form": max(
                map(len, compatibility_forms), default=0
            ),
            "compatibility_basis_digest_sha256": _basis_digest(
                self.compatibility_basis
            ),
            "raw_compatibility_stream_digest_sha256": (
                self.raw_compatibility_digest.hexdigest()
            ),
            "Jacobian_echelon_digest_sha256": tangent._echelon_digest(
                {
                    pivot: record.jacobian
                    for pivot, record in self.jacobian_basis.items()
                }
            ),
            "Jacobian_third_forms_digest_sha256": preflight._third_form_digest(
                jacobian_forms
            ),
            "Jacobian_reduction_ledger": self.jacobian_reduction_ledger.serialize(),
            "compatibility_reduction_ledger": (
                self.compatibility_reduction_ledger.serialize()
            ),
        }


def compile_slack_csg_third_order_v042(root: Path) -> dict[str, Any]:
    """Compile the exact third-order compatibility and Q audit."""

    root = root.resolve()
    paths = {
        "slack": root / SLACK_INVENTORY_PATH,
        "mixed": root / MIXED_MANIFEST_PATH,
        "tangent": root / TANGENT_PATH,
        "second": root / SECOND_ORDER_PATH,
        "budget": root / BUDGET_PATH,
        "preflight": root / PREFLIGHT_PATH,
    }
    slack = _load(paths["slack"])
    mixed = _load(paths["mixed"])
    tangent_predecessor = _load(paths["tangent"])
    second_predecessor = _load(paths["second"])
    budget = _load(paths["budget"])
    preflight_predecessor = _load(paths["preflight"])
    preflight._validate_budget(budget)
    if (
        preflight_predecessor.get("verdict") != preflight.VERDICT
        or preflight_predecessor.get("semantic_digest_sha256")
        != preflight._semantic_digest(preflight_predecessor)
        or preflight_predecessor.get("semantic_digest_sha256")
        != "a7cac5ae64b3debdc8c98e5df18ba739b87b37fca91715f9c5236f14b56cf490"
        or preflight_predecessor["resource_decision"][
            "fail_closed_streamed_third_order_audit_authorised"
        ]
        is not True
    ):
        raise AssertionError("the third-order preflight binding failed")
    if second_predecessor.get("semantic_digest_sha256") != second._semantic_digest(
        second_predecessor
    ):
        raise AssertionError("the second-order predecessor binding failed")

    names: list[str] = []
    matrices, _states, expansion = terms._compile_matrices(slack, names)
    assignment, basepoint, _target = tangent._build_csg_assignment(
        slack, mixed, matrices, names
    )

    jacobian_rows: list[tangent.SparseRow] = []
    setup_ledger = terms.OperationLedger()
    for _identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, setup_ledger
    ):
        value, gradient = tangent._value_and_gradient(polynomial, assignment)
        if value:
            raise AssertionError("the CSG point failed during the third-order setup")
        if gradient:
            jacobian_rows.append(gradient)
    core_basis = tangent._echelon(jacobian_rows)
    free_coordinates, kernel_vectors, tangent_coordinate_forms = second._tangent_kernel(
        core_basis, len(names)
    )
    if len(core_basis) != 427 or len(kernel_vectors) != 49:
        raise AssertionError("the CSG Jacobian or tangent dimension changed")

    second_eliminator = second.SecondOrderEliminator(len(kernel_vectors))
    second_ledger = terms.OperationLedger()
    for identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, second_ledger
    ):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        quadratic = second._quadratic_restriction(
            polynomial, assignment, tangent_coordinate_forms
        )
        second_eliminator.add(identifier, gradient, quadratic)
    if second_eliminator.nonzero_raw_obstruction_forms:
        raise AssertionError("the second-order all-lift result changed")
    particular_forms = preflight._particular_second_order_forms(
        second_eliminator, len(names)
    )
    particular_profile = preflight._particular_profile(particular_forms, names)
    if (
        particular_profile
        != preflight_predecessor["full_second_order_jet_fibre"][
            "particular_second_order_correction"
        ]
    ):
        raise AssertionError("the canonical second-order correction changed")

    blind_names = second_predecessor["terminal_slack_blind_directions"][
        "ambient_coordinate_names"
    ]
    free_name_to_tangent = {
        names[ambient_index]: tangent_index
        for tangent_index, ambient_index in enumerate(free_coordinates)
    }
    blind_indices = {free_name_to_tangent[name] for name in blind_names}

    eliminator = ThirdOrderEliminator(budget)
    block_censuses = {
        "CPOBC": preflight.WeightedThirdCensus("CPOBC"),
        "strong_GC": preflight.WeightedThirdCensus("strong_GC"),
    }
    combined_census = preflight.WeightedThirdCensus("CPOBC_plus_strong_GC")
    third_ledger = terms.OperationLedger()
    raw_core_blind_occurrences = 0
    for identifier, polynomial in second._iter_core_polynomials(
        slack, matrices, third_ledger
    ):
        _value, gradient = tangent._value_and_gradient(polynomial, assignment)
        third_form = preflight._third_order_restriction(
            polynomial,
            assignment,
            tangent_coordinate_forms,
            particular_forms,
        )
        raw_core_blind_occurrences += _blind_occurrences(third_form, blind_indices)
        block_censuses[identifier["block"]].add(identifier, third_form)
        combined_census.add(identifier, third_form)
        eliminator.add(identifier, gradient, third_form)

    core_census = combined_census.finalize()
    if (
        core_census["stream_digest_sha256"]
        != preflight_predecessor["raw_third_order_core_stream"]["combined"][
            "stream_digest_sha256"
        ]
    ):
        raise AssertionError("the raw third-order core stream changed")
    core_profile = eliminator.serialize()
    expected_basis = preflight_predecessor[
        "independent_Jacobian_basis_third_jet_preflight"
    ]
    if (
        core_profile["Jacobian_rank"] != 427
        or core_profile["dependent_Jacobian_rows"] != 3985
        or core_profile["Jacobian_echelon_digest_sha256"]
        != expected_basis["Jacobian_echelon_digest_sha256"]
        or core_profile["Jacobian_third_forms_digest_sha256"]
        != expected_basis["basis_forms_digest_sha256"]
    ):
        raise AssertionError("the retained third-order Jacobian basis changed")

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    q_ledger = terms.OperationLedger()
    q_records: list[dict[str, Any]] = []
    q_raw_census = preflight.WeightedThirdCensus("Q_commutators")
    q_intrinsic_forms: list[ThirdForm] = []
    q_compatibility_remainders: list[ThirdForm] = []
    q_jacobian_remainder_failures = 0
    raw_q_blind_occurrences = 0
    intrinsic_q_blind_occurrences = 0
    remainder_q_blind_occurrences = 0
    for identifier, polynomial in second._iter_q_polynomials(
        q_representatives, matrices, q_ledger
    ):
        third_form = preflight._third_order_restriction(
            polynomial,
            assignment,
            tangent_coordinate_forms,
            particular_forms,
        )
        q_raw_census.add(identifier, third_form)
        raw_q_blind_occurrences += _blind_occurrences(third_form, blind_indices)
        jacobian_remainder, intrinsic = eliminator.reduce_external_jet(
            tangent._value_and_gradient(polynomial, assignment)[1], third_form
        )
        q_jacobian_remainder_failures += bool(jacobian_remainder)
        compatibility_remainder = _reduce_third_form(
            intrinsic,
            eliminator.compatibility_basis,
            eliminator.compatibility_reduction_ledger,
        )
        eliminator._check_caps(compatibility_remainder)
        intrinsic_q_blind_occurrences += _blind_occurrences(intrinsic, blind_indices)
        remainder_q_blind_occurrences += _blind_occurrences(
            compatibility_remainder, blind_indices
        )
        q_intrinsic_forms.append(intrinsic)
        q_compatibility_remainders.append(compatibility_remainder)
        q_records.append(
            {
                **identifier,
                "raw_weighted_terms": len(third_form),
                "intrinsic_terms_after_core_Jacobian_jet_elimination": len(intrinsic),
                "terms_modulo_core_compatibility_span": len(compatibility_remainder),
                "compatibility_span_remainder": preflight._third_form_record(
                    compatibility_remainder
                ),
            }
        )
    if q_jacobian_remainder_failures:
        raise AssertionError("a Q third jet escaped the core first-order rowspace")
    q_raw_profile = q_raw_census.finalize()
    if (
        q_raw_profile["stream_digest_sha256"]
        != preflight_predecessor["raw_Q_third_order_stream"]["stream_digest_sha256"]
    ):
        raise AssertionError("the raw Q third-order stream changed")

    intrinsic_q_basis: dict[ThirdMonomial, ThirdForm] = {}
    remainder_q_basis: dict[ThirdMonomial, ThirdForm] = {}
    for intrinsic, remainder in zip(
        q_intrinsic_forms, q_compatibility_remainders, strict=True
    ):
        _extend_third_basis(intrinsic_q_basis, intrinsic)
        _extend_third_basis(remainder_q_basis, remainder)
    q_modulo_rank = len(remainder_q_basis)

    all_second_order_jets_lift = core_profile["raw_nonzero_compatibility_forms"] == 0
    q_blocked = q_modulo_rank == 0
    if all_second_order_jets_lift and q_blocked:
        verdict = VERDICT_ALL_LIFT_Q_BLOCKED
    elif q_blocked:
        verdict = VERDICT_COMPATIBILITY_Q_BLOCKED
    else:
        verdict = VERDICT_Q_SPAN_ESCAPE

    compatibility_terms = core_profile["compatibility_basis_total_terms"]
    per_term = int(budget["conservative_python_bytes_per_sparse_term"])
    reserve = int(budget["fixed_runtime_reserve_bytes"])
    jacobian_terms = expected_basis["basis_total_weighted_terms"]
    conservative_memory = reserve + per_term * (jacobian_terms + compatibility_terms)
    if conservative_memory >= int(budget["hard_memory_limit_bytes"]):
        raise RuntimeError("actual third-order bases exceeded the hard memory estimate")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "basepoint": "diagonal CSG t_j=1 source matrices",
            "formal_order": 3,
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
            PREFLIGHT_PATH: {
                "raw_sha256": _sha256(paths["preflight"]),
                "semantic_digest_sha256": preflight_predecessor[
                    "semantic_digest_sha256"
                ],
                "verdict": preflight_predecessor["verdict"],
            },
            BUDGET_PATH: {"raw_sha256": _sha256(paths["budget"])},
        },
        "basepoint_and_jet_fibre_recheck": {
            "assignment_sha256": basepoint["assignment_sha256"],
            "all_131_matrices_equal_diag_p_e_1": (
                basepoint["all_131_matrices_equal_diag_p_e_1"]
            ),
            "all_131_determinants_nonzero": basepoint[
                "all_131_determinants_nonzero"
            ],
            "tangent_variables_z": 49,
            "second_order_fibre_variables_a": 49,
            "weighted_third_monomial_dimension": preflight.WEIGHTED_MONOMIALS,
            "particular_second_order_forms_digest_sha256": particular_profile[
                "forms_digest_sha256"
            ],
        },
        "raw_third_order_core_stream_recheck": {
            "combined": core_census,
            "per_block": {
                block: census.finalize() for block, census in block_censuses.items()
            },
            "all_raw_forms_retained": False,
            "ambient_polynomial_operation_ledger": third_ledger.serialize(),
        },
        "third_order_core_compatibility": {
            **core_profile,
            "formal_equation": "J_core*v + r_core(z,a) = 0",
            "all_second_order_core_jets_lift_through_third_order": (
                all_second_order_jets_lift
            ),
        },
        "Q_third_order_modulo_core": {
            "scalar_entry_slots": len(q_records),
            "raw_weighted_third_stream_recheck": q_raw_profile,
            "first_order_Jacobian_remainder_failures": q_jacobian_remainder_failures,
            "nonzero_intrinsic_weighted_third_forms": sum(
                bool(form) for form in q_intrinsic_forms
            ),
            "intrinsic_weighted_third_span_rank": len(intrinsic_q_basis),
            "intrinsic_echelon_digest_sha256": _basis_digest(intrinsic_q_basis),
            "nonzero_compatibility_span_remainders": sum(
                bool(form) for form in q_compatibility_remainders
            ),
            "rank_modulo_core_compatibility_span": q_modulo_rank,
            "Q_escape_blocked_through_order_three_by_linear_span": q_blocked,
            "Q_commutators_vanish_through_order_three_on_every_core_lift": (
                q_blocked
            ),
            "remainder_echelon_digest_sha256": _basis_digest(remainder_q_basis),
            "records": q_records,
            "operation_ledger": q_ledger.serialize(),
        },
        "terminal_slack_blind_directions": {
            "ambient_coordinate_names": blind_names,
            "weighted_coordinate_indices": sorted(blind_indices),
            "count": len(blind_names),
            "raw_core_weighted_third_monomial_occurrences": (
                raw_core_blind_occurrences
            ),
            "raw_Q_weighted_third_monomial_occurrences": raw_q_blind_occurrences,
            "intrinsic_Q_weighted_third_monomial_occurrences": (
                intrinsic_q_blind_occurrences
            ),
            "Q_remainder_weighted_third_monomial_occurrences": (
                remainder_q_blind_occurrences
            ),
            "remain_core_and_Q_silent_through_order_three": (
                raw_core_blind_occurrences
                == raw_q_blind_occurrences
                == intrinsic_q_blind_occurrences
                == remainder_q_blind_occurrences
                == 0
            ),
        },
        "resource_usage": {
            "versioned_budget": budget,
            "actual_Jacobian_basis_terms": jacobian_terms,
            "actual_compatibility_basis_terms": compatibility_terms,
            "conservative_basis_memory_estimate_bytes": conservative_memory,
            "below_hard_memory_limit": (
                conservative_memory < int(budget["hard_memory_limit_bytes"])
            ),
            "raw_forms_streamed_and_discarded": True,
            "dense_23226_column_matrix_materialised": False,
        },
        "execution_boundary": {
            "exact_sparse_QQ_third_order_compatibility_audit_runs": 1,
            "dependent_core_compatibility_reductions": 3985,
            "Q_intrinsic_third_order_reductions": 24,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "generic_solver_run": False,
        },
        "execution_decision": {
            "generic_solver_authorised": False,
            "higher_order_formal_audit_authorised": q_blocked,
            "next_gate": (
                "DESIGN_THE_FOURTH_ORDER_FULL_THIRD_JET_FIBER_PREFLIGHT"
                if q_blocked
                else "ANALYSE_THE_NONZERO_Q_THIRD_ORDER_REMAINDER_ON_THE_CORE_CONE"
            ),
        },
        "claim_boundary": [
            "All conclusions are formal and local at the diagonal CSG point through order three.",
            "Linear-span containment is sufficient to block Q on compatible third-order jets.",
            "No claim is made about fourth order, formal convergence, or remote components.",
            "Eq113 and Eq139 remain separate downstream witness-validation gates.",
            "No unrestricted source-native 955 terminal verdict is claimed.",
        ],
        "unrestricted_source_native_955_status": "OPEN",
        "passed": True,
        "verdict": verdict,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_slack_csg_third_order_v042(root: Path) -> Path:
    payload = compile_slack_csg_third_order_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_slack_csg_third_order_v042(repository_root))
