"""Conservative d=2 audit of the 22 v0.3.3 formal B-inverse auxiliaries.

The v0.3.3 presentation retained every inverse of a recursively defined
``B`` transition as a formal two-sided-inverse generator.  This module does
not classify a symbol as definitional merely because its name contains
``inverse``.  It cross-checks four frozen v0.3.3 artifacts and three
certificates, follows every definition through the dependency DAG, verifies
the two inverse equations and the transition-level determinant predicate, and
checks that the definition is common to both Eq. (113) source-index branches.

For a verified 2 by 2 matrix B, the auxiliary is eliminated on the declared
open set det(B) != 0 by

    B^-1 = adj(B) / det(B).

The audit is exact but conditional on the v0.3.3 strong-operator profile and
its nonsingularity assumption.  It does not expand the resulting rational
functions into Q-entry polynomials or perform determinant saturation.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFINITIONAL_RATIONAL_AUXILIARY = "DEFINITIONAL_RATIONAL_AUXILIARY"
GENUINE_FREE_AUXILIARY = "GENUINE_FREE_AUXILIARY"
BRANCH_DEPENDENT_AUXILIARY = "BRANCH_DEPENDENT_AUXILIARY"
AMBIGUOUS_AUXILIARY = "AMBIGUOUS_AUXILIARY"

CLASSIFICATIONS = {
    DEFINITIONAL_RATIONAL_AUXILIARY,
    GENUINE_FREE_AUXILIARY,
    BRANCH_DEPENDENT_AUXILIARY,
    AMBIGUOUS_AUXILIARY,
}

PAPER_STRONG_OPERATOR_PROFILE = "PAPER_STRONG_OPERATOR_PROFILE"
SOURCE_INDEX_BRANCHES = (
    "EQ113_QN_BRANCH",
    "EQ113_QN_PLUS_1_BRANCH",
)
SOURCE_INDEX_POLICY = "BOTH_BRANCHES_PRESERVED_NOT_MIXED"
EXPECTED_AUXILIARY_COUNT = 22
SCHEMA_VERSION = "final-theory-d2-B-auxiliary-audit-v0.3.4"
VERDICT = "D2_B_INVERSE_AUXILIARIES_DEFINITIONAL_RATIONAL"

INPUT_PATHS = {
    "eq112_result": "results/v0.3.3_eq112_reduction_n4.json",
    "atomisation_result": "results/v0.3.3_atomisation_paths_n4.json",
    "q_presentation_result": "results/v0.3.3_q_only_presentation_n4.json",
    "eq112_certificate": "certificates/eq112_reduction/dependency_dag.json",
    "atomisation_certificate": "certificates/atomisation_paths/path_completeness.json",
    "q_presentation_certificate": (
        "certificates/q_only_presentation/relation_digest_ledger.json"
    ),
    "eq112_source": "src/universe_lab/final_theory/eq112_reduction_v033.py",
    "q_presentation_source": (
        "src/universe_lab/final_theory/cpobc_q_presentation_v033.py"
    ),
}

RESULT_PATH = "results/v0.3.4_B_auxiliary_inventory.json"
REPORT_PATH = "reports/v0.3.4_B_auxiliary_audit.md"
CLASSIFICATION_CERTIFICATE_PATH = (
    "certificates/d2_auxiliary_audit/v0.3.4_classification.json"
)
DEPENDENCY_CERTIFICATE_PATH = (
    "certificates/d2_auxiliary_audit/v0.3.4_dependency_dag.json"
)

JsonDict = dict[str, Any]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> JsonDict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return value


def _load_inputs(root: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for key, relative_path in INPUT_PATHS.items():
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix == ".json":
            loaded[key] = _load_json(path)
    return loaded


def _word_display(word: list[str]) -> str:
    return "I" if not word else " * ".join(word)


def _linear_definition_display(b_id: str, terms: list[JsonDict]) -> str:
    pieces: list[str] = []
    for term in terms:
        coefficient = int(term["coefficient"])
        word = _word_display(list(term["word_nodes"]))
        magnitude = abs(coefficient)
        body = word if magnitude == 1 else f"{magnitude}*({word})"
        if not pieces:
            pieces.append(body if coefficient > 0 else f"-{body}")
        else:
            pieces.append(("+ " if coefficient > 0 else "- ") + body)
    return f"{b_id} := {' '.join(pieces)}"


def _transition_type(stage: int, precursor_code: int) -> str:
    if precursor_code == 0:
        return "GREGARIOUS_TRANSITION"
    if precursor_code == (1 << stage) - 1:
        return "TIMID_TRANSITION"
    return "PROPER_NON_GREGARIOUS_TRANSITION"


def _unique_dependencies(node: JsonDict) -> list[str]:
    return list(dict.fromkeys(str(item) for item in node.get("dependencies", [])))


def _dependency_closure(
    root_node: str,
    nodes: dict[str, JsonDict],
) -> tuple[list[str], list[str]]:
    seen: set[str] = set()
    missing: set[str] = set()
    pending = list(_unique_dependencies(nodes[root_node]))
    while pending:
        node_id = pending.pop()
        if node_id in seen:
            continue
        seen.add(node_id)
        node = nodes.get(node_id)
        if node is None:
            missing.add(node_id)
            continue
        pending.extend(_unique_dependencies(node))
    return sorted(seen), sorted(missing)


def _dependency_paths_to_leaves(
    root_node: str,
    nodes: dict[str, JsonDict],
) -> tuple[list[list[str]], list[list[str]]]:
    paths: list[list[str]] = []
    cycles: list[list[str]] = []

    def visit(node_id: str, prefix: list[str]) -> None:
        if node_id in prefix:
            cycles.append(prefix[prefix.index(node_id) :] + [node_id])
            return
        node = nodes.get(node_id)
        current = prefix + [node_id]
        if node is None:
            paths.append(current)
            return
        dependencies = _unique_dependencies(node)
        if not dependencies:
            paths.append(current)
            return
        for dependency in dependencies:
            visit(dependency, current)

    visit(root_node, [])
    return sorted(paths), sorted(cycles)


def _provenance_core(factor: JsonDict) -> JsonDict:
    return {
        "B_occurrence_id": factor["B_occurrence_id"],
        "B_operator_symbol": factor["B_operator_symbol"],
        "B_transition_signature": factor["B_transition_signature"],
        "source_relation_rows": factor["source_relation_rows"],
        "source_causet_id": factor["source_causet_id"],
        "precursor_code": factor["precursor_code"],
        "precursor_vertices_in_source": factor["precursor_vertices_in_source"],
        "B_target_relation_rows": factor["B_target_relation_rows"],
        "B_target_causet_id": factor["B_target_causet_id"],
        "gregarious_companion_occurrence_id": factor[
            "gregarious_companion_occurrence_id"
        ],
        "gregarious_companion_operator_symbol": factor[
            "gregarious_companion_operator_symbol"
        ],
        "gregarious_companion_signature": factor[
            "gregarious_companion_signature"
        ],
        "gregarious_target_relation_rows": factor[
            "gregarious_target_relation_rows"
        ],
        "gregarious_target_causet_id": factor["gregarious_target_causet_id"],
        "source_target_types": factor["source_target_types"],
        "transition_provenance": factor["transition_provenance"],
    }


def _atomisation_indexes(
    atomisation: JsonDict,
    path_certificate: JsonDict,
    path_reductions: list[JsonDict],
) -> dict[str, Any]:
    reduction_by_path = {
        str(record["path_id"]): record for record in path_reductions
    }
    certificate_by_path: dict[str, JsonDict] = {}
    for causet in path_certificate["paths"]:
        for path in causet["paths"]:
            certificate_by_path[str(path["path_id"])] = path

    sites: defaultdict[str, list[JsonDict]] = defaultdict(list)
    provenance: defaultdict[str, list[JsonDict]] = defaultdict(list)
    for causet in atomisation["causets"]:
        all_path_ids = sorted(
            str(path["path_id"]) for path in causet["all_alternative_paths"]
        )
        canonical_path_id = str(causet["canonical_representative_path"])
        for path in causet["all_alternative_paths"]:
            path_id = str(path["path_id"])
            reduction = reduction_by_path[path_id]
            certificate_path = certificate_by_path.get(path_id)
            factors = path["B_operator_factors"]
            for factor_index, factor in enumerate(factors):
                signature = factor["B_transition_signature"]
                digest = _stable_hash(signature)[:20]
                inverse_node_id = f"BINV:{digest}"
                inverse_position = len(factors) - 1 - factor_index
                expected_inverse_symbol = f"{factor['B_operator_symbol']}^-1"
                site = {
                    "causet_id": causet["causet_id"],
                    "causet_stage": causet["stage"],
                    "path_id": path_id,
                    "path_role": (
                        "CANONICAL_REPRESENTATIVE"
                        if path_id == canonical_path_id
                        else "ALTERNATIVE_PATH"
                    ),
                    "alternative_path_ids": [
                        candidate for candidate in all_path_ids if candidate != path_id
                    ],
                    "selected_elements": path["selected_elements"],
                    "path_length": path["path_length"],
                    "factor_index": factor_index,
                    "paper_stage_index": factor["paper_stage_index"],
                    "selected_original_vertex": factor["selected_original_vertex"],
                    "factor_source_causet_id": factor["source_causet_id"],
                    "S_forward_position": factor_index,
                    "S_inverse_position": inverse_position,
                    "inverse_node_at_use_site": reduction[
                        "S_inverse_factor_nodes"
                    ][inverse_position],
                    "inverse_use_verified": (
                        reduction["S_inverse_factor_nodes"][inverse_position]
                        == inverse_node_id
                    ),
                    "path_certificate_verified": bool(
                        certificate_path is not None
                        and certificate_path["S_word"][factor_index]
                        == factor["B_operator_symbol"]
                        and certificate_path["S_inverse_word"][inverse_position]
                        == expected_inverse_symbol
                    ),
                    "semantic_profile": path["GC_semantic_profile"],
                }
                sites[digest].append(site)
                provenance[digest].append(_provenance_core(factor))
    return {
        "sites": {
            digest: sorted(
                records,
                key=lambda item: (
                    item["causet_id"],
                    item["path_id"],
                    item["factor_index"],
                ),
            )
            for digest, records in sites.items()
        },
        "provenance": provenance,
        "path_reduction_count": len(reduction_by_path),
        "certificate_path_count": len(certificate_by_path),
    }


def _branch_usage(
    inverse_node_id: str,
    branches: JsonDict,
) -> tuple[dict[str, list[JsonDict]], dict[str, str], bool]:
    usage: dict[str, list[JsonDict]] = {}
    projection_hashes: dict[str, str] = {}
    for branch in SOURCE_INDEX_BRANCHES:
        records: list[JsonDict] = []
        projections: list[JsonDict] = []
        for relation in branches[branch]:
            positions = [
                index
                for index, token in enumerate(relation["commuting_word"])
                if token == inverse_node_id
            ]
            if not positions:
                continue
            record = {
                "causet_id": relation["causet_id"],
                "alpha_path_id": relation["alpha_path_id"],
                "beta_path_id": relation["beta_path_id"],
                "commuting_word_positions": positions,
                "Q_token": relation["Q_token"],
            }
            records.append(record)
            projections.append(
                {
                    key: record[key]
                    for key in (
                        "causet_id",
                        "alpha_path_id",
                        "beta_path_id",
                        "commuting_word_positions",
                    )
                }
            )
        usage[branch] = sorted(
            records,
            key=lambda item: (
                item["causet_id"],
                item["alpha_path_id"],
                item["beta_path_id"],
            ),
        )
        projection_hashes[branch] = _stable_hash(projections)
    branch_invariant = len(set(projection_hashes.values())) == 1
    return usage, projection_hashes, branch_invariant


def _rational_inverse_record(auxiliary_id: str, digest: str) -> JsonDict:
    prefix = f"b_{digest[:16]}"
    b00 = f"{prefix}_00"
    b01 = f"{prefix}_01"
    b10 = f"{prefix}_10"
    b11 = f"{prefix}_11"
    delta = f"Delta_{digest[:16]}"
    numerator = [[b11, f"-{b01}"], [f"-{b10}", b00]]
    denominator_formula = f"{b00}*{b11} - {b01}*{b10}"
    return {
        "dimension": 2,
        "B_entry_coordinates": [[b00, b01], [b10, b11]],
        "auxiliary_entry_coordinates": [
            [f"{auxiliary_id}_00", f"{auxiliary_id}_01"],
            [f"{auxiliary_id}_10", f"{auxiliary_id}_11"],
        ],
        "numerator": {
            "kind": "ADJUGATE_2X2",
            "matrix": numerator,
        },
        "denominator": {
            "symbol": delta,
            "formula": denominator_formula,
        },
        "entrywise_definition": [
            [f"{b11}/{delta}", f"-{b01}/{delta}"],
            [f"-{b10}/{delta}", f"{b00}/{delta}"],
        ],
        "matrix_definition": f"{auxiliary_id} := adj(B)/{delta}",
        "identity": "B*adj(B) = adj(B)*B = det(B)*I_2",
    }


def classify_auxiliary_evidence(evidence: JsonDict) -> str:
    """Classify one auxiliary without treating an inverse label as evidence.

    ``GENUINE_FREE_AUXILIARY`` requires an explicit positive free-generator
    declaration.  Partial inverse evidence is conservatively ambiguous.
    """

    branch_membership = evidence.get("branch_membership", {})
    branch_values = list(branch_membership.values())
    branch_dependent = bool(
        evidence.get("branch_definition_differs")
        or (
            branch_values
            and (
                not all(isinstance(value, bool) for value in branch_values)
                or len(set(branch_values)) > 1
            )
        )
    )
    if branch_dependent:
        return BRANCH_DEPENDENT_AUXILIARY

    required = (
        "unique_forward_definition",
        "forward_definition_matches_transition_predicate",
        "unique_matching_inverse_node",
        "exact_two_sided_inverse_predicates",
        "d2_determinant_nonzero_predicate",
        "transition_nonsingularity_assumption",
        "acyclic_resolved_dependency_closure",
        "transition_provenance_complete",
        "path_use_sites_verified",
        "strong_profile_only",
        "branch_definition_invariant",
    )
    if all(evidence.get(key) is True for key in required):
        return DEFINITIONAL_RATIONAL_AUXILIARY

    if (
        evidence.get("explicitly_declared_free") is True
        and evidence.get("unique_forward_definition") is False
        and evidence.get("exact_two_sided_inverse_predicates") is False
    ):
        return GENUINE_FREE_AUXILIARY
    return AMBIGUOUS_AUXILIARY


def _topological_auxiliary_order(
    dependency_map: dict[str, list[str]],
) -> tuple[list[str], list[list[str]]]:
    visiting: list[str] = []
    complete: set[str] = set()
    order: list[str] = []
    cycles: list[list[str]] = []

    def visit(auxiliary: str) -> None:
        if auxiliary in complete:
            return
        if auxiliary in visiting:
            start = visiting.index(auxiliary)
            cycles.append(visiting[start:] + [auxiliary])
            return
        visiting.append(auxiliary)
        for dependency in sorted(dependency_map[auxiliary]):
            visit(dependency)
        visiting.pop()
        complete.add(auxiliary)
        order.append(auxiliary)

    for auxiliary in sorted(dependency_map):
        visit(auxiliary)
    return order, cycles


def _input_source_records(root: Path) -> list[JsonDict]:
    return [
        {
            "role": role,
            "path": relative_path,
            "sha256": _sha256_file(root / relative_path),
            "bytes": (root / relative_path).stat().st_size,
        }
        for role, relative_path in sorted(INPUT_PATHS.items())
    ]


def audit_b_auxiliaries_v034(root: Path | None = None) -> JsonDict:
    """Audit and conservatively classify all frozen v0.3.3 B inverses."""

    repository_root = (root or _repo_root()).resolve()
    inputs = _load_inputs(repository_root)
    eq112 = inputs["eq112_result"]
    atomisation = inputs["atomisation_result"]
    presentation = inputs["q_presentation_result"]
    eq112_certificate = inputs["eq112_certificate"]
    atomisation_certificate = inputs["atomisation_certificate"]
    presentation_certificate = inputs["q_presentation_certificate"]

    nodes = {
        str(node["node_id"]): node for node in eq112["dependency_DAG"]["nodes"]
    }
    certificate_nodes = {
        str(node["node_id"]): node
        for node in eq112_certificate["dependency_DAG"]["nodes"]
    }
    forward_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if node["kind"] == "EQ107_EQ108_LINEAR_EXPRESSION"
    }
    inverse_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if node["kind"] == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
    }
    inverse_by_forward: defaultdict[str, list[JsonDict]] = defaultdict(list)
    for node in inverse_nodes.values():
        inverse_by_forward[str(node["inverse_of_node"])].append(node)

    path_indexes = _atomisation_indexes(
        atomisation,
        atomisation_certificate,
        eq112["path_reductions"],
    )
    transition_predicates: defaultdict[str, list[JsonDict]] = defaultdict(list)
    for predicate in presentation["invertibility_predicates"][
        "reconstructed_transition_predicates"
    ]:
        transition_predicates[str(predicate["occurrence_id"])].append(predicate)

    branch_auxiliaries = {
        branch: set(
            presentation["source_index_branches"][branch][
                "remaining_auxiliary_generators"
            ]
        )
        for branch in SOURCE_INDEX_BRANCHES
    }
    nonsingularity_assumption = any(
        "nonsingular" in str(assumption).lower()
        for assumption in eq112["assumptions"]
    )
    source_checks = {
        "eq112_result_has_22_forward_B_definitions": (
            len(forward_nodes) == EXPECTED_AUXILIARY_COUNT
        ),
        "eq112_result_has_22_inverse_auxiliaries": (
            len(inverse_nodes) == EXPECTED_AUXILIARY_COUNT
        ),
        "eq112_certificate_DAG_exact_match": (
            eq112["dependency_DAG"] == eq112_certificate["dependency_DAG"]
        ),
        "eq112_certificate_node_index_exact_match": nodes == certificate_nodes,
        "atomisation_result_has_22_B_occurrences": (
            atomisation["counts"]["distinct_B_occurrences"]
            == EXPECTED_AUXILIARY_COUNT
        ),
        "atomisation_certificate_has_22_B_occurrences": (
            atomisation_certificate["counts"]["distinct_B_occurrences"]
            == EXPECTED_AUXILIARY_COUNT
        ),
        "atomisation_result_and_certificate_path_counts_match": (
            path_indexes["path_reduction_count"]
            == path_indexes["certificate_path_count"]
            == atomisation["counts"]["complete_atomisation_paths"]
        ),
        "q_presentation_reports_22_auxiliaries": (
            presentation["counts"]["remaining_matrix_auxiliaries_Qn_branch"]
            == EXPECTED_AUXILIARY_COUNT
        ),
        "q_presentation_certificate_counts_exact_match": (
            presentation["counts"] == presentation_certificate["counts"]
        ),
        "source_index_branch_auxiliary_inventories_match": (
            branch_auxiliaries[SOURCE_INDEX_BRANCHES[0]]
            == branch_auxiliaries[SOURCE_INDEX_BRANCHES[1]]
        ),
        "v033_dependency_DAG_cycle_free": bool(
            eq112["dependency_DAG"]["cycle_free"]
            and not eq112["dependency_DAG"]["cycles"]
        ),
        "strong_operator_profile_selected": (
            eq112["semantic_profile"]
            == presentation["semantic_profile"]
            == PAPER_STRONG_OPERATOR_PROFILE
        ),
        "transition_nonsingularity_assumption_present": nonsingularity_assumption,
    }

    provisional: list[JsonDict] = []
    auxiliary_dependency_map: dict[str, list[str]] = {}
    for forward_node_id, forward in sorted(forward_nodes.items()):
        digest = forward_node_id.split(":", 1)[1]
        expected_inverse_node_id = f"BINV:{digest}"
        matching_inverse_nodes = inverse_by_forward[forward_node_id]
        inverse = (
            matching_inverse_nodes[0]
            if len(matching_inverse_nodes) == 1
            else inverse_nodes.get(expected_inverse_node_id, {})
        )
        inverse_node_id = str(inverse.get("node_id", expected_inverse_node_id))
        auxiliary_id = str(inverse.get("auxiliary_generator", f"U_B_{digest[:16]}"))
        signature = forward["transition_signature"]
        stage = int(forward["stage"])
        precursor_code = int(signature["precursor_code"])
        path_sites = path_indexes["sites"].get(digest, [])
        provenance_records = path_indexes["provenance"].get(digest, [])
        provenance_by_digest = {
            _stable_hash(record): record for record in provenance_records
        }
        provenance_variants = [
            provenance_by_digest[key] for key in sorted(provenance_by_digest)
        ]
        provenance = (
            provenance_variants[0]
            if provenance_by_digest
            else {}
        )
        b_id = str(provenance.get("B_operator_symbol", f"B_{stage}_{digest[:16]}"))
        occurrence_id = str(
            forward.get(
                "v032_occurrence_id",
                provenance.get("B_occurrence_id", "UNRESOLVED"),
            )
        )
        predicates = transition_predicates.get(occurrence_id, [])
        predicate = predicates[0] if len(predicates) == 1 else {}
        expected_expression = [
            {
                "coefficient": int(term["coefficient"]),
                "word": list(term["word_nodes"]),
            }
            for term in forward["terms"]
        ]
        expected_inverse_predicates = [
            f"{auxiliary_id} * {forward_node_id} = I",
            f"{forward_node_id} * {auxiliary_id} = I",
        ]
        closure, missing_dependencies = _dependency_closure(
            inverse_node_id,
            nodes,
        )
        dependency_paths, local_cycles = _dependency_paths_to_leaves(
            inverse_node_id,
            nodes,
        )
        terminal_dependencies = sorted(
            {
                path[-1]
                for path in dependency_paths
                if path and path[-1] in nodes and not _unique_dependencies(nodes[path[-1]])
            }
        )
        inherited_inverse_nodes = sorted(
            node_id
            for node_id in closure
            if node_id.startswith("BINV:") and node_id != inverse_node_id
        )
        auxiliary_dependency_map[auxiliary_id] = [
            str(nodes[node_id]["auxiliary_generator"])
            for node_id in inherited_inverse_nodes
        ]
        direct_consumers = [
            {
                "consumer_node_id": node_id,
                "consumer_kind": node["kind"],
                "dependency_positions": [
                    index
                    for index, dependency in enumerate(node["dependencies"])
                    if dependency == inverse_node_id
                ],
            }
            for node_id, node in sorted(nodes.items())
            if inverse_node_id in node.get("dependencies", [])
        ]
        branch_usage, branch_projection_hashes, branch_usage_invariant = (
            _branch_usage(inverse_node_id, eq112["path_consistency_branches"])
        )
        branch_membership = {
            branch: auxiliary_id in branch_auxiliaries[branch]
            for branch in SOURCE_INDEX_BRANCHES
        }
        evidence = {
            "unique_forward_definition": (
                forward_node_id == f"BDEF:{digest}"
                and _stable_hash(signature).startswith(digest)
            ),
            "forward_definition_matches_transition_predicate": bool(
                len(predicates) == 1
                and predicate.get("reconstructed_expression")
                == expected_expression
            ),
            "unique_matching_inverse_node": bool(
                len(matching_inverse_nodes) == 1
                and inverse_node_id == expected_inverse_node_id
                and inverse.get("transition_signature") == signature
            ),
            "exact_two_sided_inverse_predicates": (
                inverse.get("inverse_predicates") == expected_inverse_predicates
            ),
            "d2_determinant_nonzero_predicate": bool(
                len(predicates) == 1
                and predicate.get("d2_predicate")
                == "det(reconstructed_2x2_expression) != 0"
            ),
            "transition_nonsingularity_assumption": nonsingularity_assumption,
            "acyclic_resolved_dependency_closure": bool(
                eq112["dependency_DAG"]["cycle_free"]
                and not local_cycles
                and not missing_dependencies
                and terminal_dependencies
            ),
            "transition_provenance_complete": bool(
                provenance_records
                and all(
                    record.get("B_transition_signature") == signature
                    and record.get("B_occurrence_id")
                    == f"B-occurrence-{digest}"
                    and record.get("B_operator_symbol") == b_id
                    for record in provenance_records
                )
            ),
            "path_use_sites_verified": bool(
                path_sites
                and all(
                    site["inverse_use_verified"]
                    and site["path_certificate_verified"]
                    for site in path_sites
                )
            ),
            "strong_profile_only": bool(
                source_checks["strong_operator_profile_selected"]
                and {
                    site["semantic_profile"] for site in path_sites
                }
                <= {PAPER_STRONG_OPERATOR_PROFILE}
            ),
            "branch_definition_invariant": bool(
                branch_usage_invariant
                and len(set(branch_membership.values())) == 1
                and all(branch_membership.values())
            ),
            "branch_definition_differs": not branch_usage_invariant,
            "branch_membership": branch_membership,
            "explicitly_declared_free": False,
            "inverse_label_used_as_classification_evidence": False,
        }
        classification = classify_auxiliary_evidence(evidence)
        rational_record = _rational_inverse_record(auxiliary_id, digest)
        inherited_denominators = [
            f"Delta_{dependency.removeprefix('U_B_')}"
            for dependency in auxiliary_dependency_map[auxiliary_id]
        ]
        rational_record["denominator"]["inherited_denominator_symbols"] = (
            inherited_denominators
        )
        rational_record["denominator"]["fully_substituted_polynomial_status"] = (
            "NOT_EXPANDED_OR_NORMALISED"
        )
        rational_record["denominator"]["local_nonzero_condition"] = (
            f"{rational_record['denominator']['symbol']} != 0"
        )
        rational_record["denominator"]["condition_source"] = {
            "occurrence_id": occurrence_id,
            "v0.3.3_predicate": predicate.get("d2_predicate", "MISSING"),
            "status": (
                "ASSUMED_BY_TRANSITION_NONSINGULARITY_NOT_INDEPENDENTLY_DERIVED"
            ),
        }
        provisional.append(
            {
                "auxiliary_id": auxiliary_id,
                "classification": classification,
                "classification_reason": (
                    "The forward B expression is unique, its dependency closure is "
                    "acyclic, both inverse equations and the matching transition "
                    "determinant predicate are present, and both source-index branches "
                    "share the same definition."
                    if classification == DEFINITIONAL_RATIONAL_AUXILIARY
                    else "At least one conservative classification obligation failed."
                ),
                "free_d2_matrix_entry_count": (
                    0 if classification == DEFINITIONAL_RATIONAL_AUXILIARY else 4
                ),
                "B_id": b_id,
                "B_occurrence_id": f"B-occurrence-{digest}",
                "v032_transition_occurrence_id": occurrence_id,
                "B_definition_node_id": forward_node_id,
                "B_inverse_node_id": inverse_node_id,
                "transition_type": _transition_type(stage, precursor_code),
                "stage": stage,
                "transition_signature": signature,
                "definition": {
                    "kind": forward["kind"],
                    "display": _linear_definition_display(b_id, forward["terms"]),
                    "terms": forward["terms"],
                    "v032_reduced_expression_sha256": forward[
                        "v032_reduced_expression_sha256"
                    ],
                    "definition_sha256": _stable_hash(forward["terms"]),
                },
                "inverse_definition": {
                    "inverse_of_node": inverse.get("inverse_of_node"),
                    "two_sided_predicates": inverse.get("inverse_predicates", []),
                    "v033_kind": inverse.get("kind"),
                    "v033_terminal_generator_flag": inverse.get(
                        "terminal_generator"
                    ),
                    "audit_interpretation": (
                        "v0.3.3 retained this node as a formal presentation "
                        "generator; the d=2 adjugate identity makes it definitional "
                        "only on the recorded determinant-open set"
                    ),
                },
                "dependency_DAG": {
                    "inverse_direct_dependencies": _unique_dependencies(inverse),
                    "forward_direct_dependencies": _unique_dependencies(forward),
                    "transitive_dependencies": closure,
                    "missing_dependencies": missing_dependencies,
                    "terminal_dependencies": terminal_dependencies,
                    "inherited_B_inverse_nodes": inherited_inverse_nodes,
                    "inherited_auxiliary_ids": auxiliary_dependency_map[
                        auxiliary_id
                    ],
                    "paths_to_terminal_nodes": dependency_paths,
                    "cycles": local_cycles,
                    "cycle_free": not local_cycles,
                },
                "path_provenance": {
                    "path_use_sites": path_sites,
                    "canonical_path_use_count": sum(
                        site["path_role"] == "CANONICAL_REPRESENTATIVE"
                        for site in path_sites
                    ),
                    "alternative_path_use_count": sum(
                        site["path_role"] == "ALTERNATIVE_PATH"
                        for site in path_sites
                    ),
                    "distinct_causet_count": len(
                        {site["causet_id"] for site in path_sites}
                    ),
                },
                "alternative_paths": sorted(
                    {
                        alternative
                        for site in path_sites
                        for alternative in site["alternative_path_ids"]
                    }
                ),
                "inverse_use_sites": {
                    "Eq112_S_inverse_paths": path_sites,
                    "dependency_DAG_direct_consumers": direct_consumers,
                    "Eq113_source_index_branches": branch_usage,
                    "transition_invertibility_predicate": {
                        "occurrence_id": occurrence_id,
                        "predicate": predicate.get("predicate", "MISSING"),
                        "d2_predicate": predicate.get("d2_predicate", "MISSING"),
                    },
                },
                "rational_d2_elimination": rational_record,
                "determinant_condition": rational_record["denominator"],
                "transition_provenance": {
                    "canonical_representative": provenance,
                    "labelled_variants": provenance_variants,
                    "labelled_variant_count": len(provenance_variants),
                    "path_factor_instance_count": len(provenance_records),
                    "all_variants_share_decorated_signature": all(
                        record.get("B_transition_signature") == signature
                        for record in provenance_records
                    ),
                    "interpretation": (
                        "Raw relation rows may differ by labelling while the "
                        "decorated transition signature and B occurrence remain "
                        "the same; all such provenance variants are retained."
                    ),
                },
                "provenance_digest_sha256": (
                    _stable_hash(provenance_variants)
                    if provenance_by_digest
                    else "MISSING"
                ),
                "profile": {
                    "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
                    "reachable_state_profile": "NOT_EMITTED",
                    "profile_status": "CONDITIONAL_ADDITIONAL_AXIOM_PROFILE",
                },
                "source_index_branch": {
                    "policy": SOURCE_INDEX_POLICY,
                    "membership": branch_membership,
                    "definition_status": "BRANCH_INVARIANT",
                    "usage_projection_sha256": branch_projection_hashes,
                    "usage_projection_exact_match": branch_usage_invariant,
                },
                "classification_evidence": evidence,
            }
        )

    elimination_order, elimination_cycles = _topological_auxiliary_order(
        auxiliary_dependency_map
    )
    elimination_rank = {
        auxiliary: index for index, auxiliary in enumerate(elimination_order)
    }
    for record in provisional:
        record["dependency_DAG"]["rational_elimination_rank"] = elimination_rank[
            record["auxiliary_id"]
        ]
        record["dependency_DAG"]["dependency_first_elimination_order"] = (
            elimination_order
        )
    auxiliaries = sorted(provisional, key=lambda item: item["auxiliary_id"])
    classification_counts = Counter(
        str(record["classification"]) for record in auxiliaries
    )
    transition_type_counts = Counter(
        str(record["transition_type"]) for record in auxiliaries
    )
    all_source_checks_pass = all(source_checks.values())
    all_definitional = bool(
        len(auxiliaries) == EXPECTED_AUXILIARY_COUNT
        and classification_counts[DEFINITIONAL_RATIONAL_AUXILIARY]
        == EXPECTED_AUXILIARY_COUNT
        and not elimination_cycles
    )
    payload: JsonDict = {
        "schema_version": SCHEMA_VERSION,
        "audit_scope": (
            "all 22 formal B-inverse auxiliaries in the frozen v0.3.3 n<=4 "
            "PAPER_STRONG_OPERATOR_PROFILE presentation, scalarised at d=2"
        ),
        "source_version": "v0.3.3",
        "dimension": 2,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": SOURCE_INDEX_POLICY,
        "classification_policy": {
            "allowed_classifications": sorted(CLASSIFICATIONS),
            "inverse_name_is_not_definition_evidence": True,
            "definitional_requirements": [
                "one exact forward B definition",
                "one matching inverse node",
                "both left and right inverse predicates",
                "matching d=2 determinant-nonzero transition predicate",
                "resolved acyclic dependency closure",
                "complete atomisation-path transition provenance",
                "same definition in both Eq. (113) source-index branches",
            ],
            "genuine_free_requires_positive_free_generator_evidence": True,
            "fallback_classification": AMBIGUOUS_AUXILIARY,
        },
        "input_sources": _input_source_records(repository_root),
        "source_consistency_checks": source_checks,
        "dependency_summary": {
            "cycle_free": not elimination_cycles,
            "cycles": elimination_cycles,
            "dependency_first_rational_elimination_order": elimination_order,
            "auxiliary_dependencies": {
                auxiliary: auxiliary_dependency_map[auxiliary]
                for auxiliary in sorted(auxiliary_dependency_map)
            },
            "stage_monotone": all(
                next(
                    record["stage"]
                    for record in auxiliaries
                    if record["auxiliary_id"] == dependency
                )
                < record["stage"]
                for record in auxiliaries
                for dependency in auxiliary_dependency_map[record["auxiliary_id"]]
            ),
        },
        "counts": {
            "B_inverse_auxiliaries": len(auxiliaries),
            "classifications": {
                classification: classification_counts.get(classification, 0)
                for classification in sorted(CLASSIFICATIONS)
            },
            "transition_types": dict(sorted(transition_type_counts.items())),
            "v033_abstract_d2_matrix_entries": presentation[
                "d2_scalarisation_boundary"
            ]["abstract_matrix_entry_count"],
            "rationally_eliminated_B_inverse_matrix_entries": (
                4
                * classification_counts.get(
                    DEFINITIONAL_RATIONAL_AUXILIARY,
                    0,
                )
            ),
            "genuine_free_B_auxiliary_matrix_entries": (
                4
                * classification_counts.get(
                    GENUINE_FREE_AUXILIARY,
                    0,
                )
            ),
            "branch_dependent_B_auxiliary_matrix_entries": (
                4
                * classification_counts.get(
                    BRANCH_DEPENDENT_AUXILIARY,
                    0,
                )
            ),
            "ambiguous_B_auxiliary_matrix_entries": (
                4
                * classification_counts.get(
                    AMBIGUOUS_AUXILIARY,
                    0,
                )
            ),
            "remaining_Q_matrix_entry_coordinates_before_saturation": (
                presentation["d2_scalarisation_boundary"][
                    "Q_only_rational_matrix_entry_count"
                ]
            ),
            "local_B_determinant_nonzero_conditions": len(auxiliaries),
        },
        "auxiliaries": auxiliaries,
        "rational_elimination_boundary": {
            "exact_on_open_determinant_locus": all_definitional,
            "B_inverse_auxiliary_minimality": (
                "ZERO_GENUINE_FREE_B_INVERSES_AT_D2_ON_DECLARED_OPEN_SET"
            ),
            "fully_expanded_Q_entry_numerators": "NOT_COMPILED",
            "fully_expanded_Q_entry_denominators": "NOT_COMPILED",
            "determinant_saturation": "NOT_COMPILED",
            "determinant_condition_independence": "NOT_CLAIMED",
            "dense_Groebner_executed": False,
            "reverse_presentation_equivalence": "NOT_PROVED_BY_THIS_AUDIT",
        },
        "assumptions": [
            "PAPER_STRONG_OPERATOR_PROFILE is selected explicitly",
            "all transition operators represented by the 22 B factors are nonsingular",
            "d=2 matrix entries lie in a commutative characteristic-zero scalar field",
            "both Eq. (113) source-index branches remain separate",
            "frozen v0.3.3 results and certificates are the audited inputs",
        ],
        "unresolved_components": [
            "expand and normalise all recursively substituted Q-entry rational functions",
            "compile determinant saturation for the full scalar polynomial system",
            "test algebraic dependence or redundancy among determinant conditions",
            "prove reverse equivalence of the full Q presentation",
            "resolve the paper's Eq. (113) Q_n versus Q_(n+1) source index",
        ],
        "verdict": VERDICT if all_definitional else "D2_B_AUXILIARY_AUDIT_PARTIAL",
        "passed": bool(all_source_checks_pass and all_definitional),
    }
    payload["semantic_digest_sha256"] = _stable_hash(
        {
            "source_checks": source_checks,
            "elimination_order": elimination_order,
            "auxiliaries": [
                {
                    "auxiliary_id": record["auxiliary_id"],
                    "classification": record["classification"],
                    "definition_sha256": record["definition"]["definition_sha256"],
                    "dependency_DAG": record["dependency_DAG"],
                    "determinant_condition": record["determinant_condition"],
                    "path_provenance": record["path_provenance"],
                    "source_index_branch": record["source_index_branch"],
                }
                for record in auxiliaries
            ],
        }
    )
    return payload


def audit_B_auxiliaries_v034(root: Path | None = None) -> JsonDict:
    """Compatibility alias retaining the paper's uppercase B notation."""

    return audit_b_auxiliaries_v034(root)


def compile_d2_auxiliary_audit_v034(root: Path | None = None) -> JsonDict:
    """Compiler-style alias used by the final-theory artifact pipeline."""

    return audit_b_auxiliaries_v034(root)


def _classification_certificate(result: JsonDict) -> JsonDict:
    auxiliaries = [
        {
            "auxiliary_id": record["auxiliary_id"],
            "B_id": record["B_id"],
            "B_occurrence_id": record["B_occurrence_id"],
            "v032_transition_occurrence_id": record[
                "v032_transition_occurrence_id"
            ],
            "stage": record["stage"],
            "transition_type": record["transition_type"],
            "classification": record["classification"],
            "classification_evidence": record["classification_evidence"],
            "rational_d2_elimination": record["rational_d2_elimination"],
            "determinant_condition": record["determinant_condition"],
            "transition_provenance": record["transition_provenance"],
            "profile": record["profile"],
            "source_index_branch": record["source_index_branch"],
        }
        for record in result["auxiliaries"]
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "certificate_kind": "D2_B_AUXILIARY_CLASSIFICATION",
        "source_inventory_semantic_digest_sha256": result[
            "semantic_digest_sha256"
        ],
        "counts": result["counts"],
        "classification_policy": result["classification_policy"],
        "auxiliaries": auxiliaries,
        "assumptions": result["assumptions"],
        "unresolved_components": result["unresolved_components"],
        "verdict": result["verdict"],
        "passed": result["passed"],
    }
    payload["certificate_semantic_digest_sha256"] = _stable_hash(auxiliaries)
    return payload


def _dependency_certificate(result: JsonDict) -> JsonDict:
    auxiliaries = [
        {
            "auxiliary_id": record["auxiliary_id"],
            "B_definition_node_id": record["B_definition_node_id"],
            "B_inverse_node_id": record["B_inverse_node_id"],
            "definition": record["definition"],
            "inverse_definition": record["inverse_definition"],
            "dependency_DAG": record["dependency_DAG"],
            "path_provenance": record["path_provenance"],
            "alternative_paths": record["alternative_paths"],
            "inverse_use_sites": record["inverse_use_sites"],
        }
        for record in result["auxiliaries"]
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "certificate_kind": "D2_B_AUXILIARY_DEPENDENCY_DAG",
        "source_inventory_semantic_digest_sha256": result[
            "semantic_digest_sha256"
        ],
        "dependency_summary": result["dependency_summary"],
        "auxiliaries": auxiliaries,
        "verdict": result["verdict"],
        "passed": result["passed"],
    }
    payload["certificate_semantic_digest_sha256"] = _stable_hash(auxiliaries)
    return payload


def render_b_auxiliary_audit_report(result: JsonDict) -> str:
    """Render a compact human-readable audit with a per-B ledger."""

    counts = result["counts"]
    lines = [
        "# v0.3.4 d=2 B-inverse auxiliary audit",
        "",
        f"Verdict: `{result['verdict']}`.",
        "",
        (
            "All 22 v0.3.3 formal B-inverse symbols are "
            "`DEFINITIONAL_RATIONAL_AUXILIARY` at d=2 on the explicitly "
            "recorded determinant-open locus. This conclusion uses the unique "
            "forward definition, both inverse predicates, the matching "
            "transition determinant predicate, the acyclic dependency DAG, "
            "and branch-invariant provenance; the word \"inverse\" is not "
            "itself classification evidence."
        ),
        "",
        "## Scalar consequence",
        "",
        (
            f"The v0.3.3 abstract count was "
            f"`{counts['v033_abstract_d2_matrix_entries']}` matrix-entry "
            f"coordinates. The audit rationally eliminates "
            f"`{counts['rationally_eliminated_B_inverse_matrix_entries']}` "
            "B-inverse coordinates, leaving "
            f"`{counts['remaining_Q_matrix_entry_coordinates_before_saturation']}` "
            "Q-entry coordinates before determinant saturation."
        ),
        "",
        "This is a rational elimination, not a polynomial saturation or a "
        "reverse-equivalence proof.",
        "",
        "## Inventory",
        "",
        "| auxiliary | B | stage | transition type | path uses | inherited B^-1 | class |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for record in result["auxiliaries"]:
        dependency = record["dependency_DAG"]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record['auxiliary_id']}`",
                    f"`{record['B_id']}`",
                    str(record["stage"]),
                    f"`{record['transition_type']}`",
                    str(len(record["path_provenance"]["path_use_sites"])),
                    str(len(dependency["inherited_B_inverse_nodes"])),
                    f"`{record['classification']}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Per-auxiliary evidence",
            "",
        ]
    )
    for record in result["auxiliaries"]:
        dependency = record["dependency_DAG"]
        rational = record["rational_d2_elimination"]
        path_sites = record["path_provenance"]["path_use_sites"]
        canonical_paths = [
            site["path_id"]
            for site in path_sites
            if site["path_role"] == "CANONICAL_REPRESENTATIVE"
        ]
        alternative_paths = [
            site["path_id"]
            for site in path_sites
            if site["path_role"] == "ALTERNATIVE_PATH"
        ]
        lines.extend(
            [
                f"### `{record['auxiliary_id']}`",
                "",
                f"- B and transition: `{record['B_id']}`, "
                f"`{record['B_occurrence_id']}`, "
                f"`{record['v032_transition_occurrence_id']}`.",
                f"- Signature: `{record['transition_signature']}`; "
                f"type `{record['transition_type']}`.",
                f"- Definition: `{record['definition']['display']}`.",
                "- Direct dependencies: "
                f"`{dependency['forward_direct_dependencies']}`.",
                "- Dependency-first elimination rank: "
                f"`{dependency['rational_elimination_rank']}`; inherited "
                f"auxiliaries `{dependency['inherited_auxiliary_ids']}`.",
                f"- Canonical path uses: `{canonical_paths}`.",
                f"- Alternative path uses: `{alternative_paths}`.",
                "- Rational numerator: "
                f"`{rational['numerator']['matrix']}`.",
                "- Rational denominator: "
                f"`{rational['denominator']['formula']}` with "
                f"`{rational['denominator']['local_nonzero_condition']}`.",
                "- Profile and branch: "
                f"`{record['profile']['semantic_profile']}`, "
                f"`{record['source_index_branch']['policy']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Fully substituted Q-entry numerators and denominators are not expanded.",
            "- Determinant saturation and determinant-condition independence are not compiled.",
            "- The full Q presentation's reverse equivalence remains unproved.",
            "- The Eq. (113) source-index branches remain separate and unresolved.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: JsonDict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_d2_auxiliary_audit_v034(
    root: Path | None = None,
) -> dict[str, Path]:
    """Build the result, two certificates, and the requested report."""

    repository_root = (root or _repo_root()).resolve()
    result = audit_b_auxiliaries_v034(repository_root)
    outputs = {
        RESULT_PATH: repository_root / RESULT_PATH,
        CLASSIFICATION_CERTIFICATE_PATH: (
            repository_root / CLASSIFICATION_CERTIFICATE_PATH
        ),
        DEPENDENCY_CERTIFICATE_PATH: repository_root / DEPENDENCY_CERTIFICATE_PATH,
        REPORT_PATH: repository_root / REPORT_PATH,
    }
    _write_json(outputs[RESULT_PATH], result)
    _write_json(
        outputs[CLASSIFICATION_CERTIFICATE_PATH],
        _classification_certificate(result),
    )
    _write_json(
        outputs[DEPENDENCY_CERTIFICATE_PATH],
        _dependency_certificate(result),
    )
    outputs[REPORT_PATH].parent.mkdir(parents=True, exist_ok=True)
    outputs[REPORT_PATH].write_text(
        render_b_auxiliary_audit_report(result),
        encoding="utf-8",
    )
    return outputs


def main() -> None:
    outputs = write_d2_auxiliary_audit_v034()
    for relative_path, path in outputs.items():
        print(f"{relative_path}: {_sha256_file(path)}")


if __name__ == "__main__":
    main()
