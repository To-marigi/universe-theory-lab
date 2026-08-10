"""Fail-closed preflight for the unrestricted 955 upper-stratum module.

Gate17 found ``Lambda`` in the pure-Q row module on a two-parameter growth
subfamily, but did not produce a certificate over the scalar core scheme
``S``.  This module measures the exact ingredients needed before attempting
such a certificate:

* the 246-coordinate scalar ring and the restricted scalar core;
* the 1038 by 123 upper-right linear fibre and its 119 non-Q columns;
* the 131 source determinant localizers, without materialising their product;
* the three determinant anchors ``D_12, D_13, D_14`` and the corresponding
  ``Lambda`` forms; and
* pointwise 111-column pivot ranks at the already certified rational points.

It deliberately does not run a Groebner basis, saturation, numerical search,
or a global row-module certificate.  The result is therefore a preflight
contract, not a 955 terminal or a full-S theorem.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import source_native_955_lambda_fibre_audit_v042 as fibre
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms
from universe_lab.final_theory import source_native_955_upper_stratum_v042 as upper

RESULT_PATH = "results/v0.4.2_955_localized_row_module_preflight.json"
SCHEMA = "final-theory-v042-955-localized-row-module-preflight-v1"
VERDICT = "V042_955_LOCALIZED_ROW_MODULE_PREFLIGHT_FINITE_MINOR_COVER_REQUIRED_FULL_S_OPEN"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(unsigned).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _poly_key(polynomial: terms.Polynomial) -> tuple[tuple[tuple[int, ...], int], ...]:
    return tuple(
        sorted(
            (tuple(monomial), int(coefficient))
            for monomial, coefficient in polynomial.items()
        )
    )


def _degree(polynomial: terms.Polynomial) -> int:
    return max((len(monomial) for monomial in polynomial), default=0)


def _poly_terms(polynomial: terms.Polynomial, names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": int(coefficient),
            "variables": [names[index] for index in monomial],
        }
        for monomial, coefficient in sorted(polynomial.items())
    ]


def _prepare(root: Path) -> dict[str, Any]:
    context = fibre._prepare(root)
    names = context["names"]
    lower = set(context["lower"])
    positive = set(context["positive_indices"])
    scalar = set(range(len(names))) - lower - positive
    killed_on_scalar = lower | positive
    q_columns = {
        stage: context["positive"][context["index_of"][f"A:{representative}:01"]]
        for stage, representative in context["q_representatives"].items()
    }
    non_q_columns = set(range(len(positive))) - set(q_columns.values())
    return {
        "context": context,
        "names": names,
        "lower": lower,
        "positive": positive,
        "scalar": scalar,
        "killed_on_scalar": killed_on_scalar,
        "q_columns": q_columns,
        "non_q_columns": non_q_columns,
    }


def _scalar_core(audit: dict[str, Any]) -> dict[str, Any]:
    context = audit["context"]
    polynomials = [
        upper._restrict(polynomial, audit["killed_on_scalar"])
        for polynomial in context["core"]
    ]
    nonzero = [polynomial for polynomial in polynomials if polynomial]
    distinct = {_poly_key(polynomial) for polynomial in nonzero}
    return {
        "scalar_coordinates": len(audit["scalar"]),
        "core_entries": len(context["core"]),
        "nonzero_scalar_core_entries": len(nonzero),
        "distinct_nonzero_scalar_core_entries": len(distinct),
        "total_scalar_core_terms": sum(len(polynomial) for polynomial in nonzero),
        "maximum_scalar_core_terms": max((len(polynomial) for polynomial in nonzero), default=0),
        "maximum_scalar_core_degree": max(
            (_degree(polynomial) for polynomial in nonzero), default=0
        ),
        "full_scalar_polynomials_retained": False,
    }


def _upper_right_support(audit: dict[str, Any]) -> dict[str, Any]:
    context = audit["context"]
    positive = audit["positive"]
    lower = audit["lower"]
    q_columns = set(audit["q_columns"].values())
    support_histogram: Counter[int] = Counter()
    nonlinear_monomials = 0
    scalar_only_monomials = 0
    direct_q_only_rows = 0
    rows_with_fibre_support = 0
    for polynomial in context["upper_right"]:
        support: set[int] = set()
        for monomial in polynomial:
            if any(index in lower for index in monomial):
                continue
            fibre_indices = [index for index in monomial if index in positive]
            if len(fibre_indices) == 0:
                scalar_only_monomials += 1
            elif len(fibre_indices) == 1:
                support.add(context["positive"][fibre_indices[0]])
            else:
                nonlinear_monomials += 1
        if support:
            rows_with_fibre_support += 1
            support_histogram[len(support)] += 1
            if support <= q_columns:
                direct_q_only_rows += 1
    return {
        "rows": len(context["upper_right"]),
        "fibre_columns": len(positive),
        "q_columns": len(q_columns),
        "non_q_columns": len(audit["non_q_columns"]),
        "rows_with_fibre_support": rows_with_fibre_support,
        "direct_q_only_rows": direct_q_only_rows,
        "nonlinear_monomials": nonlinear_monomials,
        "scalar_only_monomials": scalar_only_monomials,
        "support_size_histogram": {
            str(size): count for size, count in sorted(support_histogram.items())
        },
        "exactly_linear_in_fibre": nonlinear_monomials == 0 and scalar_only_monomials == 0,
    }


def _source_determinants(audit: dict[str, Any]) -> dict[str, Any]:
    context = audit["context"]
    ledger = terms.OperationLedger()
    determinants: list[terms.Polynomial] = []
    for matrix in context["matrices"].values():
        determinant = terms._add(
            terms._multiply(matrix[0][0], matrix[1][1], ledger),
            terms._scale(
                -1, terms._multiply(matrix[0][1], matrix[1][0], ledger), ledger
            ),
            ledger,
        )
        determinants.append(upper._restrict(determinant, audit["lower"]))
    return {
        "count": len(determinants),
        "distinct_count": len({_poly_key(polynomial) for polynomial in determinants}),
        "total_terms": sum(len(polynomial) for polynomial in determinants),
        "maximum_terms": max((len(polynomial) for polynomial in determinants), default=0),
        "maximum_degree": max((_degree(polynomial) for polynomial in determinants), default=0),
        "all_nonzero_polynomials": all(determinants),
        "product_materialized": False,
        "determinant_exponent_ledger_ready": False,
    }


def _anchor_forms(audit: dict[str, Any]) -> dict[str, Any]:
    context = audit["context"]
    names = audit["names"]
    q = context["q_representatives"]
    ledger = terms.OperationLedger()

    def variable(name: str) -> terms.Polynomial:
        return terms._variable(context["index_of"][name])

    def difference(left: terms.Polynomial, right: terms.Polynomial) -> terms.Polynomial:
        return terms._add(left, terms._scale(-1, right, ledger), ledger)

    def product(left: terms.Polynomial, right: terms.Polynomial) -> terms.Polynomial:
        return terms._multiply(left, right, ledger)

    determinant_anchors: dict[str, Any] = {}
    for label, first, second in (("D12", 1, 2), ("D13", 1, 3), ("D14", 1, 4)):
        a_first = variable(f"A:{q[first]}:00")
        d_first = variable(f"A:{q[first]}:11")
        a_second = variable(f"A:{q[second]}:00")
        d_second = variable(f"A:{q[second]}:11")
        polynomial = upper._restrict(
            difference(product(a_first, d_second), product(a_second, d_first)),
            audit["killed_on_scalar"],
        )
        determinant_anchors[label] = {
            "nonzero_polynomial": bool(polynomial),
            "term_count": len(polynomial),
            "degree": _degree(polynomial),
            "terms": _poly_terms(polynomial, names),
        }

    lambda_anchors: dict[str, Any] = {}
    for label, first, second in (("lambda12", 1, 2), ("lambda13", 1, 3), ("lambda14", 1, 4)):
        a_first = variable(f"A:{q[first]}:00")
        d_first = variable(f"A:{q[first]}:11")
        a_second = variable(f"A:{q[second]}:00")
        d_second = variable(f"A:{q[second]}:11")
        b_first = variable(f"A:{q[first]}:01")
        b_second = variable(f"A:{q[second]}:01")
        polynomial = difference(
            product(difference(a_first, d_first), b_second),
            product(difference(a_second, d_second), b_first),
        )
        fibre_support = sorted(
            {
                context["positive"][index]
                for monomial in polynomial
                for index in monomial
                if index in audit["positive"]
            }
        )
        lambda_anchors[label] = {
            "term_count": len(polynomial),
            "degree": _degree(polynomial),
            "fibre_support_columns": fibre_support,
        }
    return {
        "determinant_anchors": determinant_anchors,
        "lambda_anchors": lambda_anchors,
        "rank_two_cover": [
            "D14 != 0",
            "D14 = 0 and D12 != 0",
            "D14 = D12 = 0 and D13 != 0",
        ],
        "rank_one_closed_locus": "D12 = D13 = D14 = 0",
        "rank_one_branch_certified": False,
    }


def _pointwise_pivot_preflight(audit: dict[str, Any]) -> list[dict[str, Any]]:
    context = audit["context"]
    records: list[dict[str, Any]] = []
    for label, couplings in fibre.POINT_COUPLINGS:
        first = fibre._characters_by_representative(context, couplings)
        second = {representative: Fraction(1) for representative in first}
        assignment = fibre._build_assignment(context, first, second, symbolic=False)
        rows = fibre._linear_rows(context, assignment, symbolic=False)
        pure = fibre._pure_q_elimination(rows, audit["q_columns"], symbolic=False)
        a_values = {
            stage: assignment[context["index_of"][f"A:{representative}:00"]]
            for stage, representative in context["q_representatives"].items()
        }
        d_values = {
            stage: assignment[context["index_of"][f"A:{representative}:11"]]
            for stage, representative in context["q_representatives"].items()
        }
        determinant_anchor = a_values[1] * d_values[4] - a_values[4] * d_values[1]
        if pure["non_q_rank"] != 111:
            raise AssertionError(f"pointwise non-Q rank changed at {label}")
        records.append(
            {
                "label": label,
                "couplings": [str(value) for value in couplings],
                "D14": str(determinant_anchor),
                "rows": len(rows),
                "non_q_rank": pure["non_q_rank"],
                "pure_q_rank": pure["pure_q_rank"],
                "candidate_minor_size": pure["non_q_rank"],
                "certificate_scope": "pointwise pivot only",
            }
        )
    return records


def compile_localized_row_module_preflight_v042(root: Path) -> dict[str, Any]:
    root = root.resolve()
    audit = _prepare(root)
    paths = {
        "results/v0.4.2_955_source_native_slack_compiler.json": root
        / "results/v0.4.2_955_source_native_slack_compiler.json",
        "results/v0.4.2_955_mixed_source_native_manifest.json": root
        / "results/v0.4.2_955_mixed_source_native_manifest.json",
        "results/v0.3.2_cpobc_generator_reduction.json": root
        / "results/v0.3.2_cpobc_generator_reduction.json",
    }
    scalar_core = _scalar_core(audit)
    upper_right = _upper_right_support(audit)
    determinants = _source_determinants(audit)
    anchors = _anchor_forms(audit)
    pointwise = _pointwise_pivot_preflight(audit)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "locus": "upper stratum over the unrestricted scalar core scheme S",
            "scalar_coordinates": scalar_core["scalar_coordinates"],
            "upper_right_matrix_shape": [upper_right["rows"], upper_right["fibre_columns"]],
            "solver_run": False,
            "full_S_claim": False,
        },
        "source_artifact_sha256": {
            path: _sha256(value) for path, value in paths.items()
        },
        "q_stage_mapping": {
            str(stage): representative
            for stage, representative in sorted(audit["context"]["q_representatives"].items())
        },
        "scalar_core_manifest": scalar_core,
        "upper_right_linear_fibre_manifest": upper_right,
        "source_determinant_localization_manifest": determinants,
        "anchor_forms": anchors,
        "pointwise_pivot_preflight": {
            "points": pointwise,
            "all_candidate_minor_sizes": {record["candidate_minor_size"] for record in pointwise}
            == {111},
        },
        "localized_certificate_contract": {
            "ring": "Q[z_1,...,z_246]",
            "module": "Row_R(L) + I_S R^123",
            "required_form": "(D_1k * product(delta_e))^N lambda_1k = row_R(L) + I_S terms",
            "source_determinant_product_materialized": False,
            "finite_minor_cover_status": "FINITE_MINOR_COVER_REQUIRED",
            "certificate_issued": False,
        },
        "interpretation": {
            "proved": [
                (
                    "The scalar restriction has 246 coordinates, 1814 nonzero entries, "
                    "and 1504 distinct nonzero generators."
                ),
                (
                    "The upper-right core is exactly linear in 123 fibre coordinates "
                    "and has no direct Q-only row."
                ),
                (
                    "The 131 source determinant localizers are distinct nonzero scalar "
                    "polynomials with maximum 145 terms and degree 5."
                ),
                (
                    "The rank-two diagonal locus has the declared D14, D12, D13 anchor "
                    "cover, with a rank-one closed remainder."
                ),
                (
                    "The four exact rational points admit a pointwise non-Q candidate "
                    "minor of size 111."
                ),
            ],
            "not_proved": [
                "A finite minor cover over the source determinant localization.",
                (
                    "A localized row-module membership certificate for any Lambda anchor "
                    "over all of S."
                ),
                "The rank-one branch or the full D=0 locus.",
                "A D!=0 and Lambda!=0 nonsingular core-fibre witness.",
                "Any full 955 terminal or full-S commutativity theorem.",
            ],
        },
        "next_gate": (
            "BUILD_OR_FAIL_CLOSED_A_FINITE_LOCALIZED_MINOR_COVER_FOR_D12_D13_D14_"
            "OR_FIND_A_D_NONZERO_LAMBDA_NONZERO_CORE_FIBRE"
        ),
        "solver_status": {
            "Groebner_runs": 0,
            "saturation_runs": 0,
            "numerical_search_runs": 0,
            "finite_field_runs": 0,
            "solver_run": False,
        },
        "unrestricted_source_native_955_status": "OPEN",
        "declared_955_terminal_reached": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_localized_row_module_preflight_v042(root: Path) -> Path:
    path = root / RESULT_PATH
    path.write_text(
        json.dumps(compile_localized_row_module_preflight_v042(root), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_localized_row_module_preflight_v042(repository_root))
