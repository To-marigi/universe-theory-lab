"""Nonlinear principal-open upgrade of the aligned SR2-V tangent obstruction.

Let ``y`` be the 131 in-scope lower-left transition coordinates and let ``z``
collect all other matrix entries.  Every lower component of the frozen
operator/state relations vanishes identically when ``y=0``.  In the
determinant-localized coordinate ring it therefore has the form

``F(y,z) = H(y,z) y``.

An explicit 131-row selection has an invertible ``y``-Jacobian at the frozen
rank-one witness.  Its determinant defines a nonempty principal open on which
``F=0`` forces ``y=0``.  Thus no higher-order or disconnected transverse
branch can enter this open, and all reachable states remain on the invariant
line.  The determinant-zero complement remains open.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import weak_d2_transitive_extension_v042 as extension
from universe_lab.final_theory import weak_d2_visible_tangent_v042 as tangent
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_aligned_principal_open.json"
SCHEMA = "final-theory-v042-sr2v-aligned-principal-open-v1"
VERDICT = "SR2V_ALIGNED_PRINCIPAL_OPEN_VISIBILITY_OBSTRUCTED"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_SCOPED_PRINCIPAL_OPEN_ONLY"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _scoped_relation_label(label: str) -> str:
    """Expose the completed Eq. (139) domain in locally published row labels."""
    if label.startswith("Eq139:"):
        return label.replace("Eq139:", f"Eq139:{torus.EQ139_COMPLETED}:", 1)
    return label


def build_payload(root: Path) -> dict[str, Any]:
    compiled = tangent._compile(
        root,
        "pure_lower",
        include_exact_lower_rows=True,
    )
    context: torus.ScoutContext = compiled.pop("context")
    labelled_rows: list[tuple[str, torus.SparseRow]] = compiled.pop(
        "_exact_lower_component_rows"
    )
    scoped_labelled_rows = [
        (_scoped_relation_label(label), row) for label, row in labelled_rows
    ]
    actual_variables = [variable for variable in context.variables if variable != torus.Q5]
    exact_rows = extension._restrict_rows(
        [row for _, row in labelled_rows], actual_variables
    )
    selected_indices = extension._select_independent_rows(exact_rows, actual_variables)
    if len(selected_indices) != len(actual_variables):
        raise AssertionError("the aligned lower-component Jacobian lost rank")
    selected_matrix = [
        [exact_rows[index].get(variable, Fraction(0)) for variable in actual_variables]
        for index in selected_indices
    ]
    determinant = extension._determinant(selected_matrix)
    selected_labels = [scoped_labelled_rows[index][0] for index in selected_indices]

    breaking = compiled["invariant_line_breaking_subsystem"]
    group_counts = compiled["group_counts"]
    expected_group_counts = {
        "CPOBC_operator": 3132,
        "Eq113_operator_both_branches": 200,
        "Eq139_operator_completed": 40,
        "fixed_vector_GC_basis": 640,
        "reachable_state_MSR": 48,
    }
    relation_domain_inventory = {
        "CPOBC": {"relation_count": 783, "operator_component_count": 3132},
        "Eq113": {
            torus.EQ113_DERIVED: {
                "relation_count": 25,
                "operator_component_count": 100,
            },
            torus.EQ113_LITERAL: {
                "relation_count": 25,
                "operator_component_count": 100,
            },
        },
        "Eq139": {
            torus.EQ139_STRICT: {
                "relation_count": 4,
                "operator_component_count": 16,
                "scope_note": "audited subset of completed; not duplicated in the row system",
            },
            torus.EQ139_COMPLETED: {
                "relation_count": 10,
                "operator_component_count": 40,
                "row_system_scope": True,
            },
        },
        "fixed_vector_GC_basis": {
            "relation_count": 320,
            "vector_component_count": 640,
        },
        "reachable_state_MSR": {
            "relation_count": 24,
            "vector_component_count": 48,
        },
    }
    # The complete compiler stores all four matrix or two vector components;
    # the nonlinear certificate selects exactly one lower component per source
    # relation, giving the 1,187-row subsystem below.
    gates = {
        "complete_component_inventory_unchanged": group_counts == expected_group_counts,
        "Eq113_and_Eq139_domains_are_separate": (
            len(context.eq112["path_consistency_branches"][torus.EQ113_DERIVED])
            == 25
            and len(context.eq112["path_consistency_branches"][torus.EQ113_LITERAL])
            == 25
            and len(torus._eq139_instances(torus.EQ139_STRICT))
            == 4
            and len(torus._eq139_instances(torus.EQ139_COMPLETED))
            == 10
        ),
        "lower_component_row_count_is_1187": len(labelled_rows) == 1187,
        "in_scope_lower_variable_count_is_131": len(actual_variables) == 131,
        "lower_subsystem_rank_including_external_q5_is_131": breaking["rank"] == 131,
        "only_external_q5_survives_in_full_lower_kernel": breaking[
            "nullspace_basis"
        ]
        == [{torus.Q5: "1"}],
        "selected_actual_jacobian_is_square": len(selected_matrix) == 131
        and all(len(row) == 131 for row in selected_matrix),
        "selected_actual_jacobian_determinant_is_nonzero": bool(determinant),
        "selected_labels_match_frozen_independence_certificate": selected_labels
        == [
            _scoped_relation_label(label)
            for label in breaking["selected_labels"]
            if torus.Q5 not in label
        ],
        "selected_Eq139_rows_are_explicitly_completed": len(
            [label for label in selected_labels if label.startswith("Eq139:")]
        )
        == 2
        and all(
            label.startswith(f"Eq139:{torus.EQ139_COMPLETED}:")
            for label in selected_labels
            if label.startswith("Eq139:")
        ),
        "row_digest_matches_frozen_tangent_artifact": breaking[
            "normalised_rows_sha256"
        ]
        == "dc8f354ac3726532365d48144024fcc1ca53d84957c777f190350d4f45a4ea9c",
    }
    if not all(gates.values()):
        raise AssertionError(f"aligned principal-open gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "field": "Q",
        "dimension": 2,
        "finite_scope": "n<=4",
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "input_artifacts": {
            relative: torus._sha256(root / relative)
            for relative in sorted(
                (
                    torus.CPOBC_PATH,
                    torus.REDUCTION_PATH,
                    torus.OPERATOR_GC_PATH,
                    torus.ATOMISATION_PATH,
                    torus.EQ112_PATH,
                    tangent.RESULT_PATH,
                )
            )
        },
        "ambient_chart": {
            "initial_vector": "e_1",
            "matrix_coordinates": "all four entries of each ON transition matrix",
            "lower_coordinates_y": len(actual_variables),
            "other_coordinates_z": "all diagonal and upper-right entries",
            "localisation": "all transition determinants are inverted",
            "base_point": "the frozen exact rank-one noncommutative weak/weak witness",
        },
        "lower_relation_subsystem": {
            "row_count": len(labelled_rows),
            "relation_domain_inventory": relation_domain_inventory,
            "row_system_scope": (
                "CPOBC 783; Eq113 derived 25 and literal 25 as separate blocks; "
                "Eq139 completed 10 with strict 4 retained as an audited subset; "
                "fixed-vector GC basis 320; reachable-state MSR 24"
            ),
            "source_tangent_normalised_rows_sha256": breaking[
                "normalised_rows_sha256"
            ],
            "scoped_normalised_rows_sha256": tangent._labelled_rows_digest(
                scoped_labelled_rows
            ),
            "selected_row_count": len(selected_indices),
            "selected_row_indices_zero_based": selected_indices,
            "selected_row_labels": selected_labels,
            "selected_column_labels": actual_variables,
            "jacobian_determinant_at_base": str(determinant),
            "determinant_numerator_bits": abs(determinant.numerator).bit_length(),
            "determinant_denominator_bits": determinant.denominator.bit_length(),
        },
        "principal_open_theorem": {
            "factorisation": "F(y,z)=H(y,z)*y in the determinant-localised ring",
            "definition_of_Delta_align": "det(H(y,z)) for the listed 131 residuals",
            "base_value": str(determinant),
            "principal_open": "Delta_align!=0",
            "conclusion": "every solution in the principal open has y=0",
            "visibility_consequence": (
                "all reachable states remain in span(e_1), and every commutator "
                "of upper-triangular 2x2 matrices annihilates e_1"
            ),
            "proof": [
                (
                    "Each selected lower residual vanishes identically on y=0, "
                    "so it lies in the ideal generated by the lower coordinates."
                ),
                (
                    "A telescoping polynomial decomposition after determinant "
                    "localisation gives F=H*y and H(0,z_base)=dF/dy at the base."
                ),
                (
                    "The listed exact Jacobian determinant is nonzero, hence "
                    "Delta_align defines a nonempty principal open."
                ),
                "On this open H is invertible, so F=0 implies y=0 exactly.",
                (
                    "This excludes nonlinear higher-order transverse branches in "
                    "the open, not merely first-order tangent directions."
                ),
            ],
        },
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "witness": None,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "This is an exact nonlinear obstruction only on the explicit nonempty "
            "principal open Delta_align!=0 around the aligned rank-one witness.  "
            "It does not cover the degeneracy hypersurface Delta_align=0, arbitrary "
            "disconnected components, the transverse reducible chart, or irreducible "
            "GL_2 representations.  It is not a full SR2-V obstruction or terminal."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
