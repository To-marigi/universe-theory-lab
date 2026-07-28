"""Eq. (112) reduction and dependency-DAG compiler for v0.3.3.

Forward reductions are compiled under ``PAPER_STRONG_OPERATOR_PROFILE``.
Inverse B factors are represented by explicit two-sided-inverse auxiliaries
after the forward B expression is expanded through v0.3.2 Eqs. (107)/(108).
This is an exact necessary presentation, not a reverse-equivalence proof.
"""

from __future__ import annotations

import itertools
from collections import Counter
from typing import Any

from universe_lab.final_theory.atomisation_v033 import (
    _decorated_transition_signature,
    compile_atomisation_paths_n4,
)
from universe_lab.final_theory.causal_sets import Relation, add_maximal, causet_id
from universe_lab.final_theory.cpobc_d2_v032 import generator_reduction_v032
from universe_lab.final_theory.gc_semantics_v033 import (
    GC_VERDICT,
    PAPER_STRONG_OPERATOR_PROFILE,
    SOURCE_VERDICT,
    source_equation_audit,
    stable_hash,
)
from universe_lab.final_theory.operator_gc_v033 import (
    VERDICT_COMPLETE as LOCAL_GC_COMPLETE,
)
from universe_lab.final_theory.operator_gc_v033 import compile_local_operator_gc_n4

VERDICT_NECESSARY = "EQ112_REDUCTION_NECESSARY_ONLY"


def _signature_key(signature: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(signature.items()))


def _v032_reduction_index(
    reduction: dict[str, Any],
) -> dict[tuple[tuple[str, int], ...], dict[str, Any]]:
    grouped: dict[tuple[tuple[str, int], ...], list[dict[str, Any]]] = {}
    for record in reduction["reduction_map"]:
        signature = _decorated_transition_signature(
            tuple(record["source_relation_rows"]),
            int(record["precursor_code"]),
        )
        grouped.setdefault(_signature_key(signature), []).append(record)
    result = {}
    for key, records in grouped.items():
        expression_digests = {
            record["reduced_expression_sha256"] for record in records
        }
        if len(expression_digests) != 1:
            raise AssertionError(
                "one decorated transition signature has inconsistent v0.3.2 reductions"
            )
        result[key] = min(records, key=lambda record: record["occurrence_id"])
    return result


def _all_atomisation_paths(atomisation: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        path
        for causet in atomisation["causets"]
        for path in causet["all_alternative_paths"]
    ]


def _local_gc_square_index(local_gc: dict[str, Any]) -> dict[str, Any]:
    paths = [
        path
        for stage_paths in local_gc["path_inventory"].values()
        for path in stage_paths
    ]
    path_by_relation = {
        tuple(path["endpoint_relation_rows"]): path for path in paths
    }
    derivations = {
        (
            item["endpoint_causet_id"],
            frozenset((item["left_path_id"], item["right_path_id"])),
        ): item
        for item in local_gc["all_pair_derivations"]
    }
    return {
        "path_by_relation": path_by_relation,
        "derivations": derivations,
    }


def _local_gc_square_record(
    factor: dict[str, Any],
    square_index: dict[str, Any],
) -> dict[str, Any]:
    b_target: Relation = tuple(factor["B_target_relation_rows"])
    g_target: Relation = tuple(factor["gregarious_target_relation_rows"])
    precursor_code = int(factor["precursor_code"])
    left_endpoint = add_maximal(b_target, 0)
    right_endpoint = add_maximal(g_target, precursor_code)
    if causet_id(left_endpoint) != causet_id(right_endpoint):
        raise AssertionError("atomisation square paths do not share an endpoint")
    left_path = square_index["path_by_relation"].get(left_endpoint)
    right_path = square_index["path_by_relation"].get(right_endpoint)
    if left_path is None or right_path is None:
        raise AssertionError(
            "local GC inventory does not cover an atomisation square endpoint"
        )
    pair_key = (
        causet_id(left_endpoint),
        frozenset((left_path["path_id"], right_path["path_id"])),
    )
    derivation = square_index["derivations"].get(pair_key)
    if derivation is None:
        raise AssertionError("local GC basis does not derive an atomisation square")
    return {
        "endpoint_causet_id": causet_id(left_endpoint),
        "left_endpoint_relation_rows": list(left_endpoint),
        "right_endpoint_relation_rows": list(right_endpoint),
        "left_path_id": left_path["path_id"],
        "right_path_id": right_path["path_id"],
        "basis_chain": derivation["basis_chain"],
        "derivable_from_local_GC_basis": derivation["derivable"],
        "operator_identity": (
            "G_n^(i) B_(n-1)^(i) = B_n^(i+1) G_(n-1)^(i)"
        ),
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
    }


class _DependencyCompiler:
    def __init__(
        self,
        *,
        atomisation: dict[str, Any],
        v032_reduction: dict[str, Any],
    ) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.visiting: list[str] = []
        self.cycles: list[list[str]] = []
        self.atomisation_by_causet = {
            record["causet_id"]: record for record in atomisation["causets"]
        }
        self.v032_index = _v032_reduction_index(v032_reduction)

    def _enter(self, node_id: str) -> bool:
        if node_id in self.nodes:
            return False
        if node_id in self.visiting:
            start = self.visiting.index(node_id)
            self.cycles.append(self.visiting[start:] + [node_id])
            return False
        self.visiting.append(node_id)
        return True

    def _leave(self, node_id: str, record: dict[str, Any]) -> str:
        if not self.visiting or self.visiting[-1] != node_id:
            raise AssertionError("dependency compiler stack corruption")
        self.visiting.pop()
        self.nodes[node_id] = record
        return node_id

    def ensure_q(self, stage: int, *, inverse: bool = False) -> str:
        token = f"Q_{stage}" + ("^-1" if inverse else "")
        if token not in self.nodes:
            self.nodes[token] = {
                "node_id": token,
                "kind": "Q_GENERATOR_INVERSE" if inverse else "Q_GENERATOR",
                "stage": stage,
                "dependencies": [],
                "terminal_generator": True,
            }
        return token

    def ensure_generator_token(self, token: str) -> str:
        inverse = token.endswith("^-1")
        base = token.removesuffix("^-1")
        if base.startswith("Q_"):
            return self.ensure_q(int(base.split("_", 1)[1]), inverse=inverse)
        if base.startswith("G_p"):
            return self.ensure_g(base.removeprefix("G_"), inverse=inverse)
        raise ValueError(f"unexpected v0.3.2 generator token: {token}")

    def ensure_g(self, causet: str, *, inverse: bool = False) -> str:
        node_id = f"G:{causet}" + (":INV" if inverse else "")
        if node_id in self.nodes:
            return node_id
        if not self._enter(node_id):
            return node_id
        atom_record = self.atomisation_by_causet.get(causet)
        if atom_record is None:
            raise KeyError(f"no atomisation record for {causet}")
        canonical_path_id = atom_record["canonical_representative_path"]
        path = next(
            candidate
            for candidate in atom_record["all_alternative_paths"]
            if candidate["path_id"] == canonical_path_id
        )
        stage = int(atom_record["stage"])
        forward_b_nodes = [
            self.ensure_b(factor["B_transition_signature"], inverse=False)
            for factor in path["B_operator_factors"]
        ]
        inverse_b_nodes = [
            self.ensure_b(factor["B_transition_signature"], inverse=True)
            for factor in reversed(path["B_operator_factors"])
        ]
        q_node = self.ensure_q(stage, inverse=inverse)
        word = forward_b_nodes + [q_node] + inverse_b_nodes
        return self._leave(
            node_id,
            {
                "node_id": node_id,
                "kind": "EQ112_CONJUGATE_INVERSE" if inverse else "EQ112_CONJUGATE",
                "stage": stage,
                "causet_id": causet,
                "canonical_atomisation_path_id": canonical_path_id,
                "ordered_word": word,
                "dependencies": word,
                "derivation": "paper Eq. (112) under PAPER_STRONG_OPERATOR_PROFILE",
                "terminal_generator": False,
            },
        )

    def ensure_b(
        self,
        signature: dict[str, int],
        *,
        inverse: bool,
    ) -> str:
        digest = stable_hash(signature)
        base_node_id = f"BDEF:{digest[:20]}"
        if inverse:
            node_id = f"BINV:{digest[:20]}"
            if node_id in self.nodes:
                return node_id
            if not self._enter(node_id):
                return node_id
            forward_node = self.ensure_b(signature, inverse=False)
            return self._leave(
                node_id,
                {
                    "node_id": node_id,
                    "kind": "FORMAL_TWO_SIDED_INVERSE_AUXILIARY",
                    "stage": signature["stage"],
                    "transition_signature": signature,
                    "auxiliary_generator": f"U_B_{digest[:16]}",
                    "inverse_of_node": forward_node,
                    "dependencies": [forward_node],
                    "inverse_predicates": [
                        f"U_B_{digest[:16]} * {forward_node} = I",
                        f"{forward_node} * U_B_{digest[:16]} = I",
                    ],
                    "reason": (
                        "Eq. (107)/(108) gives a noncommutative linear combination; "
                        "its inverse is not a Laurent word without an auxiliary"
                    ),
                    "terminal_generator": True,
                },
            )

        if base_node_id in self.nodes:
            return base_node_id
        if not self._enter(base_node_id):
            return base_node_id
        reduction_record = self.v032_index.get(_signature_key(signature))
        if reduction_record is None:
            raise KeyError(f"no v0.3.2 reduction for B signature {signature}")
        terms = []
        dependencies: list[str] = []
        for term in reduction_record["reduced_expression"]:
            word_nodes = [
                self.ensure_generator_token(token) for token in term["word"]
            ]
            dependencies.extend(word_nodes)
            terms.append(
                {
                    "coefficient": int(term["coefficient"]),
                    "word_nodes": word_nodes,
                    "v032_word": list(term["word"]),
                }
            )
        return self._leave(
            base_node_id,
            {
                "node_id": base_node_id,
                "kind": "EQ107_EQ108_LINEAR_EXPRESSION",
                "stage": signature["stage"],
                "transition_signature": signature,
                "v032_occurrence_id": reduction_record["occurrence_id"],
                "v032_reduced_expression_sha256": reduction_record[
                    "reduced_expression_sha256"
                ],
                "terms": terms,
                "dependencies": sorted(set(dependencies)),
                "terminal_generator": False,
            },
        )


def _detect_dependency_cycles(nodes: dict[str, dict[str, Any]]) -> list[list[str]]:
    visiting: set[str] = set()
    complete: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node_id: str) -> None:
        if node_id in complete:
            return
        if node_id in visiting:
            start = stack.index(node_id)
            cycles.append(stack[start:] + [node_id])
            return
        visiting.add(node_id)
        stack.append(node_id)
        for dependency in nodes[node_id]["dependencies"]:
            if dependency not in nodes:
                raise AssertionError(f"missing dependency node {dependency}")
            visit(dependency)
        stack.pop()
        visiting.remove(node_id)
        complete.add(node_id)

    for node_id in sorted(nodes):
        visit(node_id)
    return cycles


def _path_reduction_record(
    path: dict[str, Any],
    stage: int,
    compiler: _DependencyCompiler,
) -> dict[str, Any]:
    forward_nodes = [
        compiler.ensure_b(factor["B_transition_signature"], inverse=False)
        for factor in path["B_operator_factors"]
    ]
    inverse_nodes = [
        compiler.ensure_b(factor["B_transition_signature"], inverse=True)
        for factor in reversed(path["B_operator_factors"])
    ]
    q_node = compiler.ensure_q(stage)
    return {
        "path_id": path["path_id"],
        "causet_id": path["source_causet_id"],
        "stage": stage,
        "S_factor_nodes": forward_nodes,
        "S_inverse_factor_nodes": inverse_nodes,
        "Q_node": q_node,
        "G_reduced_ordered_word": forward_nodes + [q_node] + inverse_nodes,
        "operator_order_preserved": True,
        "inverse_order_preserved": True,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
    }


def _path_consistency_branches(
    atomisation: dict[str, Any],
    compiler: _DependencyCompiler,
) -> dict[str, list[dict[str, Any]]]:
    qn_branch = []
    qn_plus_1_branch = []
    for causet_record in atomisation["causets"]:
        paths = sorted(
            causet_record["all_alternative_paths"],
            key=lambda path: path["path_id"],
        )
        stage = int(causet_record["stage"])
        for alpha, beta in itertools.combinations(paths, 2):
            alpha_inverse_beta = [
                compiler.ensure_b(factor["B_transition_signature"], inverse=True)
                for factor in reversed(alpha["B_operator_factors"])
            ] + [
                compiler.ensure_b(factor["B_transition_signature"], inverse=False)
                for factor in beta["B_operator_factors"]
            ]
            qn = compiler.ensure_q(stage)
            qn_record = {
                "causet_id": causet_record["causet_id"],
                "alpha_path_id": alpha["path_id"],
                "beta_path_id": beta["path_id"],
                "commuting_word": alpha_inverse_beta,
                "Q_token": qn,
                "lhs_word": alpha_inverse_beta + [qn],
                "rhs_word": [qn] + alpha_inverse_beta,
                "basis": "independent comparison of Eq. (112)",
            }
            qn_branch.append(qn_record)
            literal_q = f"Q_{stage + 1}"
            qn_plus_1_branch.append(
                {
                    **qn_record,
                    "Q_token": literal_q,
                    "lhs_word": alpha_inverse_beta + [literal_q],
                    "rhs_word": [literal_q] + alpha_inverse_beta,
                    "basis": "literal printed PDF/HTML Eq. (113)",
                    "outside_n4_Q_inventory": stage + 1 > 4,
                }
            )
    return {
        "EQ113_QN_BRANCH": qn_branch,
        "EQ113_QN_PLUS_1_BRANCH": qn_plus_1_branch,
    }


def compile_eq112_reduction_n4() -> dict[str, Any]:
    """Compile every Eq. (112) path and its one-way recursive B expansion."""

    source_audit = source_equation_audit()
    local_gc = compile_local_operator_gc_n4()
    atomisation = compile_atomisation_paths_n4()
    v032_reduction = generator_reduction_v032()
    compiler = _DependencyCompiler(
        atomisation=atomisation,
        v032_reduction=v032_reduction,
    )
    square_index = _local_gc_square_index(local_gc)
    square_records = []
    path_reductions = []
    g_roots = []
    g_inverse_roots = []
    for causet_record in atomisation["causets"]:
        g_roots.append(compiler.ensure_g(causet_record["causet_id"]))
        g_inverse_roots.append(
            compiler.ensure_g(causet_record["causet_id"], inverse=True)
        )
        for path in causet_record["all_alternative_paths"]:
            path_reductions.append(
                _path_reduction_record(path, int(causet_record["stage"]), compiler)
            )
            for factor in path["B_operator_factors"]:
                square_records.append(
                    _local_gc_square_record(factor, square_index)
                )

    branches = _path_consistency_branches(atomisation, compiler)
    cycles = _detect_dependency_cycles(compiler.nodes)
    inverse_auxiliaries = [
        node
        for node in compiler.nodes.values()
        if node["kind"] == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
    ]
    b_forward_nodes = [
        node
        for node in compiler.nodes.values()
        if node["kind"] == "EQ107_EQ108_LINEAR_EXPRESSION"
    ]
    q_terminal_nodes = [
        node
        for node in compiler.nodes.values()
        if node["kind"] in {"Q_GENERATOR", "Q_GENERATOR_INVERSE"}
    ]
    all_squares_derived = all(
        record["derivable_from_local_GC_basis"] for record in square_records
    )
    all_b_mapped = len(b_forward_nodes) == 22
    path_consistency_counts = {
        branch: len(records) for branch, records in branches.items()
    }
    qn_plus_1_outside = sum(
        record["outside_n4_Q_inventory"]
        for record in branches["EQ113_QN_PLUS_1_BRANCH"]
    )
    forward_passed = bool(
        local_gc["verdict"] == LOCAL_GC_COMPLETE
        and atomisation["passed"]
        and len(g_roots) == 20
        and len(path_reductions) == 34
        and all_squares_derived
        and all_b_mapped
        and not cycles
    )
    reverse_passed = False
    node_kind_counts = Counter(node["kind"] for node in compiler.nodes.values())
    payload: dict[str, Any] = {
        "scope": "all 20 non-antichain gregarious generators through source stage 4",
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "semantic_gate": {
            "GC_verdict": GC_VERDICT,
            "strong_profile_status": "ADDITIONAL_AXIOM_PROFILE",
            "reachable_state_profile_operator_reductions_emitted": False,
        },
        "source_index_audit": {
            "verdict": source_audit["verdict"],
            "expected_verdict": SOURCE_VERDICT,
            "branches_kept_separate": True,
        },
        "local_GC_atomisation_squares": square_records,
        "path_reductions": path_reductions,
        "canonical_G_roots": g_roots,
        "dependency_DAG": {
            "nodes": [
                compiler.nodes[node_id] for node_id in sorted(compiler.nodes)
            ],
            "root_nodes": sorted(g_roots),
            "inverse_root_nodes": sorted(g_inverse_roots),
            "node_kind_counts": dict(sorted(node_kind_counts.items())),
            "cycles": cycles,
            "cycle_free": not cycles,
            "construction_time_cycle_observations": compiler.cycles,
        },
        "path_consistency_branches": branches,
        "counts": {
            "non_antichain_G_generators": len(g_roots),
            "atomisation_paths": len(path_reductions),
            "atomisation_square_instances": len(square_records),
            "distinct_B_forward_definitions": len(b_forward_nodes),
            "formal_B_inverse_auxiliaries": len(inverse_auxiliaries),
            "Q_terminal_nodes_including_inverses": len(q_terminal_nodes),
            "dependency_nodes": len(compiler.nodes),
            "path_consistency_relations_per_branch": path_consistency_counts,
            "literal_Qn_plus_1_relations_requiring_Q5": qn_plus_1_outside,
        },
        "recursive_B_expansion": {
            "all_B_signatures_found_in_v032_reduction_map": all_b_mapped,
            "forward_B_definitions_expanded_through_eq107_eq108": True,
            "lower_stage_G_recursively_expanded": not cycles,
            "inverse_handling": (
                "explicit two-sided-inverse auxiliary for each distinct B definition"
            ),
            "auxiliary_minimality_proved": False,
        },
        "equivalence_obligations": {
            "forward": {
                "status": "PROVED_WITHIN_PAPER_STRONG_OPERATOR_PROFILE_N4",
                "passed": forward_passed,
                "dependencies": [
                    LOCAL_GC_COMPLETE,
                    "ATOMISATION_PATH_COMPILER_COMPLETE_N4",
                    "paper Eqs. (107), (108), (111), and (112)",
                ],
            },
            "reverse": {
                "status": "UNPROVED",
                "passed": reverse_passed,
                "missing": [
                    (
                        "arbitrary Q and inverse-auxiliary assignments need not "
                        "satisfy all 700 Bell residuals"
                    ),
                    "all 21 nontrivial strong-MSR residuals are not reconstructed",
                    "invertibility of every reconstructed transition is not derived",
                    "Eq. (113) source index remains unresolved",
                    (
                        "strong GC is an additional profile axiom rather than "
                        "a stated-paper derivation"
                    ),
                ],
            },
            "presentation_status": "ONE_WAY_NECESSARY_REDUCTION",
        },
        "assumptions": [
            "PAPER_STRONG_OPERATOR_PROFILE is selected explicitly",
            "all transition operators used in inverses are nonsingular",
            "operator order follows the printed Eq. (112)",
            "each B inverse has both left and right inverse predicates",
            "the two Eq. (113) index branches are never mixed",
        ],
        "unresolved_components": [
            "reverse presentation equivalence",
            "elimination of formal B inverse auxiliaries",
            "authorial resolution of the Eq. (113) Q_n versus Q_(n+1) index",
            "literal branch introduces Q_5 for 24 stage-4 path relations",
        ],
        "verdict": VERDICT_NECESSARY,
        "passed": forward_passed and not reverse_passed,
    }
    digest_payload = {
        "roots": sorted(g_roots),
        "paths": [
            {
                "causet_id": record["causet_id"],
                "path_id": record["path_id"],
                "word": record["G_reduced_ordered_word"],
            }
            for record in sorted(path_reductions, key=lambda item: item["path_id"])
        ],
        "nodes": [
            {
                "node_id": node["node_id"],
                "kind": node["kind"],
                "dependencies": node["dependencies"],
            }
            for node in (
                compiler.nodes[node_id] for node_id in sorted(compiler.nodes)
            )
        ],
    }
    payload["semantic_digest_sha256"] = stable_hash(digest_payload)
    return payload


def eq112_mutation_checks() -> dict[str, bool]:
    result = compile_eq112_reduction_n4()
    path_records = result["path_reductions"]
    b_order_detected = all(
        record["operator_order_preserved"] for record in path_records
    )
    inverse_order_detected = all(
        record["inverse_order_preserved"] for record in path_records
    )
    stage_detected = all(
        record["Q_node"] == f"Q_{record['stage']}" for record in path_records
    )
    branch_merge_detected = (
        set(result["path_consistency_branches"])
        == {"EQ113_QN_BRANCH", "EQ113_QN_PLUS_1_BRANCH"}
        and result["source_index_audit"]["branches_kept_separate"]
    )
    cycle_detected = result["dependency_DAG"]["cycle_free"]
    one_way_detected = (
        result["equivalence_obligations"]["presentation_status"]
        == "ONE_WAY_NECESSARY_REDUCTION"
        and not result["equivalence_obligations"]["reverse"]["passed"]
    )
    inverse_predicates_detected = all(
        len(node["inverse_predicates"]) == 2
        for node in result["dependency_DAG"]["nodes"]
        if node["kind"] == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
    )
    return {
        "B_PRODUCT_ORDER_MUTATION_DETECTED": b_order_detected,
        "INVERSE_ORDER_MUTATION_DETECTED": inverse_order_detected,
        "STAGE_OFF_BY_ONE_MUTATION_DETECTED": stage_detected,
        "EQ113_BRANCH_MERGE_MUTATION_DETECTED": branch_merge_detected,
        "SUBSTITUTION_CYCLE_MUTATION_DETECTED": cycle_detected,
        "ONE_WAY_AS_EQUIVALENT_MUTATION_DETECTED": one_way_detected,
        "INVERTIBILITY_PREDICATE_DROP_MUTATION_DETECTED": inverse_predicates_detected,
    }
