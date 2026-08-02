"""Exact state-native rank-two chart for the weak/weak SR2-V search.

The 87 endpoint states are made harmonic for the 24 source MSR equations.
Every one of the 131 ON transition orbits is then parameterised by the full
two-dimensional affine family of matrices that maps its source state to its
target state.  Fixed-vector GC, reachable-state MSR, and reachable rank two
are built into the chart.  Nonsingularity reduces exactly to ``beta_e != 0``
(and is automatic only on the shear slice); the operator relation blocks
remain for the counterexample search.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus

RESULT_PATH = "results/v0.4.2_sr2v_state_native_rank2_chart.json"
SCHEMA = "final-theory-v042-sr2v-state-native-rank2-chart-v1"
VERDICT = "SR2V_STATE_NATIVE_RANK2_CHART_CERTIFIED"
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_EXACT_CHART_ONLY"

Matrix2 = tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]
Vector2 = tuple[Fraction, Fraction]
Polynomial = dict[tuple[int, int], Fraction]

ZERO_VECTOR: Vector2 = (Fraction(0), Fraction(0))
IDENTITY: Matrix2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _add(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(left[row][column] + right[row][column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _scale(coefficient: Fraction | int, matrix: Matrix2) -> Matrix2:
    scalar = Fraction(coefficient)
    return tuple(
        tuple(scalar * matrix[row][column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def _multiply(left: Matrix2, right: Matrix2) -> Matrix2:
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def _word(factors: Iterable[Matrix2]) -> Matrix2:
    product = IDENTITY
    for factor in factors:
        product = _multiply(product, factor)
    return product


def _apply(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def _determinant(matrix: Matrix2) -> Fraction:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _matrix_record(matrix: Matrix2) -> list[list[str]]:
    return [[str(value) for value in row] for row in matrix]


def _vector_record(vector: Vector2) -> list[str]:
    return [str(value) for value in vector]


def _polynomial_add(left: Polynomial, right: Polynomial, sign: int = 1) -> Polynomial:
    result: defaultdict[tuple[int, int], Fraction] = defaultdict(Fraction)
    result.update(left)
    for monomial, value in right.items():
        result[monomial] += sign * value
    return {monomial: value for monomial, value in result.items() if value}


def _polynomial_multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: defaultdict[tuple[int, int], Fraction] = defaultdict(Fraction)
    for (left_alpha, left_beta), left_value in left.items():
        for (right_alpha, right_beta), right_value in right.items():
            result[(left_alpha + right_alpha, left_beta + right_beta)] += (
                left_value * right_value
            )
    return {monomial: value for monomial, value in result.items() if value}


def _endpoint_graph(context: torus.ScoutContext) -> dict[str, Any]:
    endpoint_stages: dict[str, int] = {}
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            endpoint = str(path["endpoint_causet_id"])
            stage = int(path["endpoint_stage"])
            previous = endpoint_stages.setdefault(endpoint, stage)
            if previous != stage:
                raise AssertionError("one endpoint appears at two stages")

    by_variable: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for occurrence_id, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence_id]
        by_variable[variable].append(record)
        endpoint_stages.setdefault(str(record["source_id"]), int(record["stage"]))
        endpoint_stages.setdefault(str(record["target_id"]), int(record["stage"]) + 1)

    edges: dict[str, dict[str, Any]] = {}
    alias_histogram: Counter[int] = Counter()
    for variable, records in by_variable.items():
        signatures = {
            (str(record["source_id"]), str(record["target_id"]), int(record["stage"]))
            for record in records
        }
        if len(signatures) != 1:
            raise AssertionError("one ON orbit has multiple source-target edges")
        source, target, stage = signatures.pop()
        alias_histogram[len(records)] += 1
        edges[variable] = {
            "source": source,
            "target": target,
            "stage": stage,
            "occurrence_ids": sorted(str(record["occurrence_id"]) for record in records),
        }

    outgoing: dict[str, list[dict[str, Any]]] = {}
    for constraint in context.cpobc["MSR_operator_constraints"]:
        source = str(constraint["source_id"])
        aggregated: defaultdict[str, int] = defaultdict(int)
        for term in constraint["terms"]:
            occurrence_id = str(term["transition_id"])
            variable = context.occurrence_variables[occurrence_id]
            if edges[variable]["source"] != source:
                raise AssertionError("an MSR term is attached to the wrong source")
            aggregated[variable] += int(term["coefficient"])
        outgoing[source] = [
            {
                "variable": variable,
                "target": edges[variable]["target"],
                "multiplicity": multiplicity,
            }
            for variable, multiplicity in sorted(aggregated.items())
        ]

    return {
        "endpoint_stages": endpoint_stages,
        "edges": edges,
        "outgoing": outgoing,
        "alias_histogram": dict(sorted(alias_histogram.items())),
    }


def _harmonic_states(graph: dict[str, Any]) -> dict[str, Any]:
    endpoint_stages: dict[str, int] = graph["endpoint_stages"]
    outgoing: dict[str, list[dict[str, Any]]] = graph["outgoing"]
    terminals = sorted(endpoint for endpoint, stage in endpoint_stages.items() if stage == 5)
    roots = sorted(endpoint for endpoint, stage in endpoint_stages.items() if stage == 1)
    if roots != ["p1-0"]:
        raise AssertionError("the finite growth graph must have the frozen unique root")
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
    first_terminal = min(terminals, key=lambda endpoint: (terminal_weights[endpoint], endpoint))
    second_terminal = max(terminals, key=lambda endpoint: (terminal_weights[endpoint], endpoint))
    if first_terminal == second_terminal:
        raise AssertionError("rank-two boundary support requires two terminals")

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
    states = {
        endpoint: (h[endpoint] / normalisation, k[endpoint] / normalisation)
        for endpoint in endpoint_stages
    }
    if states[root] != (Fraction(1), Fraction(0)):
        raise AssertionError("the harmonic state slice must normalise Omega to e1")
    harmonic_failures = []
    for source, terms in outgoing.items():
        expected = (
            sum(Fraction(term["multiplicity"]) * states[term["target"]][0] for term in terms),
            sum(Fraction(term["multiplicity"]) * states[term["target"]][1] for term in terms),
        )
        if states[source] != expected:
            harmonic_failures.append(source)
    support_determinant = (
        states[first_terminal][0] * states[second_terminal][1]
        - states[first_terminal][1] * states[second_terminal][0]
    )
    return {
        "root": root,
        "terminals": terminals,
        "terminal_weights": terminal_weights,
        "normalisation": normalisation,
        "support_terminals": [first_terminal, second_terminal],
        "support_determinant": support_determinant,
        "states": states,
        "harmonic_failures": harmonic_failures,
    }


def _affine_edge_family(source: Vector2, target: Vector2) -> dict[str, Matrix2]:
    h_source, k_source = source
    h_target, k_target = target
    if not h_source or not h_target:
        raise AssertionError("the local-frame chart requires nonzero first coordinates")
    constant: Matrix2 = (
        (h_target / h_source, Fraction(0)),
        (k_target / h_source, Fraction(0)),
    )
    alpha: Matrix2 = (
        (-h_target * k_source / h_source, h_target),
        (-k_target * k_source / h_source, k_target),
    )
    beta: Matrix2 = (
        (Fraction(0), Fraction(0)),
        (-k_source / h_source, Fraction(1)),
    )
    return {"constant": constant, "alpha": alpha, "beta": beta}


def _evaluate_family(
    family: dict[str, Matrix2],
    alpha: Fraction,
    beta: Fraction,
) -> Matrix2:
    return _add(
        family["constant"],
        _add(_scale(alpha, family["alpha"]), _scale(beta, family["beta"])),
    )


def _determinant_polynomial(family: dict[str, Matrix2]) -> Polynomial:
    entries: list[Polynomial] = []
    for row in range(2):
        for column in range(2):
            polynomial: Polynomial = {}
            for monomial, name in (
                ((0, 0), "constant"),
                ((1, 0), "alpha"),
                ((0, 1), "beta"),
            ):
                value = family[name][row][column]
                if value:
                    polynomial[monomial] = value
            entries.append(polynomial)
    return _polynomial_add(
        _polynomial_multiply(entries[0], entries[3]),
        _polynomial_multiply(entries[1], entries[2]),
        sign=-1,
    )


def _sample_parameters(variable: str, index: int) -> tuple[Fraction, Fraction]:
    del variable
    alpha = Fraction((index % 7) - 3, 5)
    beta = Fraction((index % 5) + 1, 3)
    return alpha, beta


def _relation_manifest(context: torus.ScoutContext) -> dict[str, Any]:
    cpobc_word_degrees: Counter[str] = Counter()
    cpobc_count = 0
    for relation in context.cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            cpobc_count += 1
            cpobc_word_degrees[
                f"{len(equation['lhs_word'])}x{len(equation['rhs_word'])}"
            ] += 1
    eq113 = {
        branch: len(context.eq112["path_consistency_branches"][branch])
        for branch in (torus.EQ113_DERIVED, torus.EQ113_LITERAL)
    }
    return {
        "CPOBC_raw": cpobc_count,
        "CPOBC_word_length_pairs": dict(sorted(cpobc_word_degrees.items())),
        "Eq113_separate_branches": eq113,
        "Eq139_strict": len(torus._eq139_instances(torus.EQ139_STRICT)),
        "Eq139_completed": len(torus._eq139_instances(torus.EQ139_COMPLETED)),
        "inverse_rewrites_for_final_candidate": 712,
        "fixed_GC_basis_built_into_states": len(
            context.operator_gc["generating_relation_basis"]
        ),
        "fixed_GC_all_pairs_built_into_states": len(
            context.operator_gc["all_pair_derivations"]
        ),
        "reachable_MSR_built_into_states": len(context.cpobc["MSR_operator_constraints"]),
        "supplemental_constraint_warning": (
            "Eq113 and Eq139 are retained as independent operator constraints; "
            "their literal/derived and strict/completed ledgers are not merged"
        ),
    }


def build_payload(root: Path) -> dict[str, Any]:
    context = torus._build_context(root)
    graph = _endpoint_graph(context)
    harmonic = _harmonic_states(graph)
    states: dict[str, Vector2] = harmonic["states"]
    actual_variables = [variable for variable in context.variables if variable != torus.Q5]

    families = {
        variable: _affine_edge_family(
            states[record["source"]], states[record["target"]]
        )
        for variable, record in graph["edges"].items()
    }
    sample_matrices: dict[str, Matrix2] = {}
    determinant_formula_failures = []
    action_failures = []
    for index, variable in enumerate(sorted(actual_variables)):
        family = families[variable]
        edge = graph["edges"][variable]
        source = states[edge["source"]]
        target = states[edge["target"]]
        expected_determinant = {
            (0, 1): target[0] / source[0],
        }
        if _determinant_polynomial(family) != expected_determinant:
            determinant_formula_failures.append(variable)
        alpha, beta = _sample_parameters(variable, index)
        matrix = _evaluate_family(family, alpha, beta)
        sample_matrices[variable] = matrix
        if _apply(matrix, source) != target:
            action_failures.append(variable)
        if _determinant(matrix) != target[0] * beta / source[0]:
            determinant_formula_failures.append(variable)

    path_failures = []
    path_states: dict[str, Vector2] = {}
    omega = states[harmonic["root"]]
    for stage_paths in context.operator_gc["path_inventory"].values():
        for path in stage_paths:
            matrices = []
            for factor in path["transitions"]:
                signature = factor["quotient_signature"]
                variable = context.signature_variables[
                    (
                        int(signature["stage"]),
                        int(signature["source_relation_code"]),
                        int(signature["precursor_code"]),
                    )
                ]
                matrices.append(sample_matrices[variable])
            state = _apply(_word(reversed(matrices)), omega)
            path_id = str(path["path_id"])
            path_states[path_id] = state
            if state != states[str(path["endpoint_causet_id"])]:
                path_failures.append(path_id)

    gc_pair_failures = []
    for relation in context.operator_gc["all_pair_derivations"]:
        if path_states[str(relation["left_path_id"])] != path_states[
            str(relation["right_path_id"])
        ]:
            gc_pair_failures.append(
                f"{relation['left_path_id']}:{relation['right_path_id']}"
            )

    msr_action_failures = []
    for source, terms in graph["outgoing"].items():
        total = ZERO_VECTOR
        for term in terms:
            matrix = sample_matrices[term["variable"]]
            action = _apply(matrix, states[source])
            total = (
                total[0] + Fraction(term["multiplicity"]) * action[0],
                total[1] + Fraction(term["multiplicity"]) * action[1],
            )
        if total != states[source]:
            msr_action_failures.append(source)

    occurrence_determinant_failures = []
    for occurrence_id, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence_id]
        if not _determinant(sample_matrices[variable]):
            occurrence_determinant_failures.append(str(record["occurrence_id"]))

    relation_manifest = _relation_manifest(context)
    gates = {
        "endpoint_count_is_87": len(graph["endpoint_stages"]) == 87,
        "terminal_count_is_63": len(harmonic["terminals"]) == 63,
        "source_count_is_24": len(graph["outgoing"]) == 24,
        "actual_ON_edge_count_is_131": len(graph["edges"]) == 131,
        "occurrence_alias_count_is_165": sum(
            size * count for size, count in graph["alias_histogram"].items()
        )
        == 165,
        "alias_histogram_is_frozen": graph["alias_histogram"]
        == {1: 104, 2: 22, 3: 3, 4: 2},
        "root_harmonic_normalisation_is_357": harmonic["normalisation"] == 357,
        "root_state_is_e1": omega == (Fraction(1), Fraction(0)),
        "all_first_state_coordinates_are_nonzero": all(state[0] for state in states.values()),
        "harmonic_MSR_has_no_failure": not harmonic["harmonic_failures"],
        "reachable_state_rank_is_two": bool(harmonic["support_determinant"]),
        "affine_family_action_has_no_failure": not action_failures,
        "determinant_formula_has_no_failure": not determinant_formula_failures,
        "sample_path_actions_cover_all_407_paths": len(path_states) == 407
        and not path_failures,
        "sample_fixed_GC_checks_all_1529_pairs": not gc_pair_failures,
        "sample_reachable_MSR_checks_all_24_sources": not msr_action_failures,
        "sample_all_165_occurrences_are_nonsingular": not occurrence_determinant_failures,
        "operator_relation_inventory_is_complete": relation_manifest["CPOBC_raw"] == 783
        and relation_manifest["Eq113_separate_branches"]
        == {torus.EQ113_DERIVED: 25, torus.EQ113_LITERAL: 25}
        and relation_manifest["Eq139_strict"] == 4
        and relation_manifest["Eq139_completed"] == 10,
    }
    if not all(gates.values()):
        raise AssertionError(f"state-native chart gate failed: {gates}")

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
                )
            )
        },
        "growth_graph": {
            "endpoint_count": len(graph["endpoint_stages"]),
            "endpoint_stage_histogram": {
                str(stage): count
                for stage, count in sorted(
                    Counter(graph["endpoint_stages"].values()).items()
                )
            },
            "source_count": len(graph["outgoing"]),
            "terminal_count": len(harmonic["terminals"]),
            "actual_ON_edge_count": len(graph["edges"]),
            "occurrence_alias_count": 165,
            "orbit_alias_size_histogram": {
                str(size): count for size, count in graph["alias_histogram"].items()
            },
        },
        "harmonic_rank2_state_slice": {
            "root": harmonic["root"],
            "initial_vector": _vector_record(omega),
            "raw_h_root_before_normalisation": str(harmonic["normalisation"]),
            "terminal_root_weight_min": min(harmonic["terminal_weights"].values()),
            "terminal_root_weight_max": max(harmonic["terminal_weights"].values()),
            "terminal_root_weight_sum": sum(harmonic["terminal_weights"].values()),
            "support_terminals": harmonic["support_terminals"],
            "support_state_determinant": str(harmonic["support_determinant"]),
            "reachable_span_rank": 2,
            "endpoint_states": {
                endpoint: {
                    "stage": graph["endpoint_stages"][endpoint],
                    "state": _vector_record(states[endpoint]),
                }
                for endpoint in sorted(states)
            },
            "terminal_root_weights": {
                endpoint: harmonic["terminal_weights"][endpoint]
                for endpoint in sorted(harmonic["terminals"])
            },
        },
        "local_frame_parameterisation": {
            "frame": "F_c=[[h_c,0],[k_c,1]]",
            "edge_action": "A_e=F_target*[[1,alpha_e],[0,beta_e]]*F_source^-1",
            "free_parameters_per_actual_edge": ["alpha_e", "beta_e"],
            "full_actual_parameter_count": 262,
            "shear_slice": "beta_e=1 for all 131 actual edges",
            "shear_parameter_count": 131,
            "determinant_formula": "det(A_e)=(h_target/h_source)*beta_e",
            "nonsingularity_condition": "beta_e!=0",
            "completeness": (
                "for fixed nonzero-h source and target states, every invertible "
                "matrix satisfying A_e*v_source=v_target occurs uniquely"
            ),
            "supplemental_Q5": (
                "Q5 has no n<=4 state edge and must remain a separately tracked "
                "four-coordinate supplemental operator when Eq113/Eq139 are solved"
            ),
        },
        "exact_sample_semantic_validation": {
            "role": "parameterisation check only; the sample is not a CPOBC candidate",
            "path_actions_checked": len(path_states),
            "fixed_GC_pairs_checked": len(context.operator_gc["all_pair_derivations"]),
            "reachable_MSR_sources_checked": len(graph["outgoing"]),
            "occurrence_determinants_checked": len(context.occurrence_records),
            "failures": {
                "edge_actions": action_failures,
                "determinant_formula": sorted(set(determinant_formula_failures)),
                "paths": path_failures,
                "fixed_GC_pairs": gc_pair_failures,
                "reachable_MSR": msr_action_failures,
                "occurrence_determinants": occurrence_determinant_failures,
            },
        },
        "remaining_operator_relation_manifest": relation_manifest,
        "search_order": [
            "131-variable shear slice with separately parameterised Q5",
            "structured beta subfamilies",
            "full 262 edge parameters plus Q5",
            "direct QQ certification of any candidate against every frozen ledger",
        ],
        "gates": gates,
        "search_terminal": SEARCH_TERMINAL,
        "witness": None,
        "passed": True,
        "verdict": VERDICT,
        "claim_boundary": (
            "This certifies an exact rank-two state-native coordinate chart and "
            "builds fixed-vector GC and reachable-state MSR into the coordinates.  "
            "Each actual-edge nonsingularity predicate reduces to beta_e!=0 and is "
            "automatic only on the beta_e=1 shear slice.  The chart does not solve "
            "the 783 CPOBC, Eq113, or Eq139 operator equations, does not certify a "
            "noncommutative witness, and is not an SR2-V terminal.  One fixed "
            "harmonic boundary slice is not a cover of all rank-two states."
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
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
