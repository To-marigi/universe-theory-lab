"""Source-native inventory compiler for the v0.4.2 955 repair.

This is deliberately a *coverage and provenance compiler*, not a Gröbner
frontend.  It retains the 165 source transition occurrences (with their 131
ON-quotient orbit representatives) and replaces each raw source MSR equation
by its exact reachable-state slack definition.  In particular it never
substitutes the frozen Eq. (108) expressions into a timid transition.

For every source causet ``c`` the raw MSR row has one timid occurrence ``T``.
Writing ``v_c`` for the strong-GC path-independent state, the compiler records

    T = I - sum(non-timid A) + u_c (J v_c)^T,    J = [[0,-1],[1,0]].

Consequently the reachable-state residual is identically zero, while the
``u_c`` coordinates retain exactly the missing 48 scalar degrees of freedom.
The generated inventory is search-ready at the level of exact polynomial
blocks and localisation patches, but intentionally does not run Sage, invoke
the old Q solver, or assert commutativity.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
LOCAL_GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
EQ113_BRANCH_PATH = "results/v0.3.4_source_branches.json"
WEAK_D2_PATH = "results/v0.4_weak_d2_classification.json"
DEPENDENCY_PATH = "results/v0.3.1_cpobc_dependency_graph.json"
EQ120_PATH = "results/v0.4.2_eq120_source_provenance.json"

RESULT_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
SCHEMA = "final-theory-v042-955-source-native-slack-compiler-v1"
VERDICT = "V042_955_SOURCE_NATIVE_SLACK_INVENTORY_READY_NO_SOLVER_RUN"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"JSON object required: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_json(
            {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
        ).encode("utf-8")
    ).hexdigest()


def _signature_key(record: dict[str, Any]) -> tuple[int, int, int]:
    """Return the unlabelled quotient signature used by the GC path inventory."""

    relation = tuple(int(value) for value in record["source_relation_rows"])
    precursor = int(record["precursor_code"])

    def relation_code(order: tuple[int, ...]) -> int:
        size = len(relation)
        return sum(
            1 << (new_lower * size + new_upper)
            for new_lower, old_lower in enumerate(order)
            for new_upper, old_upper in enumerate(order)
            if relation[old_lower] & (1 << old_upper)
        )

    def subset_code(order: tuple[int, ...]) -> int:
        return sum(
            1 << new_vertex
            for new_vertex, old_vertex in enumerate(order)
            if precursor & (1 << old_vertex)
        )

    relation_code_canonical, precursor_code_canonical = min(
        (relation_code(order), subset_code(order))
        for order in itertools.permutations(range(len(relation)))
    )
    return int(record["stage"]), relation_code_canonical, precursor_code_canonical


def _source_word(word: list[str], occurrence_to_representative: dict[str, str]) -> list[str]:
    return [f"A:{occurrence_to_representative[occurrence]}" for occurrence in word]


def _eq120_binding(eq120: dict[str, Any], root: Path) -> dict[str, Any]:
    if eq120.get("schema_version") != (
        "final-theory-v042-eq120-source-provenance-certificate-v0.4.2"
    ):
        raise AssertionError("unexpected Eq.(120) source-native certificate schema")
    if eq120.get("verdict") != "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED":
        raise AssertionError("Eq.(120) source-native certificate is not proved")
    if eq120.get("passed") is not True:
        raise AssertionError("Eq.(120) source-native certificate did not pass")
    expected = _semantic_digest(eq120)
    if eq120.get("semantic_digest_sha256") != expected:
        raise AssertionError("Eq.(120) source-native certificate semantic digest mismatch")
    counts = eq120.get("counts", {})
    if counts.get("unique_raw_relations") != 6 or counts.get("k1_Eq120_instances") != 3:
        raise AssertionError("Eq.(120) source-native certificate count changed")
    closure = eq120.get("dependency_closure")
    if not isinstance(closure, dict) or closure.get("dependency_closed") is not True:
        raise AssertionError("Eq.(120) certificate dependency closure is not closed")
    expected_forbidden = {
        "B_reduced_expressions_used": False,
        "MSR_used": False,
        "GC_used": False,
        "Eq108_used": False,
        "Eq112_used": False,
    }
    if {key: closure.get(key) for key in expected_forbidden} != expected_forbidden:
        raise AssertionError("Eq.(120) certificate has an unexpected dependency closure")
    selected = eq120.get("selected_700_relation_ids", {})
    if selected.get("count") != 700:
        raise AssertionError("Eq.(120) selected CPOBC core count changed")
    return {
        "path": EQ120_PATH,
        "sha256": _sha256(root / EQ120_PATH),
        "semantic_digest_sha256": expected,
        "verdict": eq120["verdict"],
        "reusable_for": (
            "source-defined Q_1,...,Q_4 ratio/chart prerequisites on the "
            "nonsingular CPOBC locus only"
        ),
        "not_reused": [
            "frozen strong-MSR Q transition reconstruction",
            "frozen Eq.(112) B-factor definitions",
            "v0.4.1 42-chart commutativity conclusion as a full-profile theorem",
        ],
        "counts": {
            "raw_CPOBC_relations": counts["unique_raw_relations"],
            "k1_Eq120_instances": counts["k1_Eq120_instances"],
            "selected_direct_CPOBC_relations": selected["count"],
        },
    }


def _strong_gc_graph_audit(path_inventory: dict[str, Any], basis: list[Any]) -> dict[str, Any]:
    """Independently check that the stored basis spans every endpoint fibre."""

    endpoint_paths: dict[tuple[int, str], set[str]] = {}
    for stage_string, paths_at_stage in path_inventory.items():
        stage = int(stage_string)
        if not isinstance(paths_at_stage, list):
            raise AssertionError(f"path inventory stage {stage} is not a list")
        for path in paths_at_stage:
            endpoint = str(path["endpoint_causet_id"])
            path_id = str(path["path_id"])
            endpoint_paths.setdefault((stage, endpoint), set()).add(path_id)

    endpoint_edges: dict[tuple[int, str], list[tuple[str, str, str]]] = {
        key: [] for key in endpoint_paths
    }
    for relation in basis:
        endpoint = str(relation["endpoint_causet_id"])
        lhs = str(relation["lhs_path_id"])
        rhs = str(relation["rhs_path_id"])
        matching_keys = [
            key for key, paths in endpoint_paths.items() if key[1] == endpoint and lhs in paths
        ]
        if len(matching_keys) != 1:
            raise AssertionError(f"cannot bind strong-GC basis lhs to one endpoint: {lhs}")
        key = matching_keys[0]
        if rhs not in endpoint_paths[key] or lhs == rhs:
            raise AssertionError(f"malformed strong-GC basis edge at {relation['relation_id']}")
        endpoint_edges[key].append((lhs, rhs, str(relation["relation_id"])))

    evidence: list[dict[str, Any]] = []
    pair_count = 0
    edge_count = 0
    path_count = 0
    for (stage, endpoint), paths in sorted(endpoint_paths.items()):
        adjacency: dict[str, set[str]] = {path_id: set() for path_id in paths}
        edges = endpoint_edges[(stage, endpoint)]
        for lhs, rhs, _relation_id in edges:
            adjacency[lhs].add(rhs)
            adjacency[rhs].add(lhs)
        pending = set(paths)
        component_count = 0
        while pending:
            component_count += 1
            frontier = [pending.pop()]
            while frontier:
                current = frontier.pop()
                neighbours = adjacency[current] & pending
                pending.difference_update(neighbours)
                frontier.extend(neighbours)
        count = len(paths)
        path_count += count
        pair_count += count * (count - 1) // 2
        edge_count += len(edges)
        evidence.append(
            {
                "endpoint_stage": stage,
                "endpoint_causet_id": endpoint,
                "path_count": count,
                "unordered_same_endpoint_pairs": count * (count - 1) // 2,
                "basis_edge_count": len(edges),
                "component_count": component_count,
                "connected": component_count == 1,
                "tree_edge_count": count - 1,
                "path_ids_sha256": hashlib.sha256(
                    _canonical_json(sorted(paths)).encode("utf-8")
                ).hexdigest(),
                "basis_relation_ids_sha256": hashlib.sha256(
                    _canonical_json(sorted(relation_id for _, _, relation_id in edges)).encode(
                        "utf-8"
                    )
                ).hexdigest(),
            }
        )
    if path_count != 407 or len(evidence) != 87:
        raise AssertionError("strong-GC path inventory census changed")
    if pair_count != 1529 or edge_count != 320:
        raise AssertionError("strong-GC pair/basis census changed")
    if not all(
        item["connected"] and item["basis_edge_count"] == item["tree_edge_count"]
        for item in evidence
    ):
        raise AssertionError("strong-GC basis does not form an endpoint-wise spanning tree")
    return {
        "path_count": path_count,
        "endpoint_count": len(evidence),
        "unordered_same_endpoint_pair_count": pair_count,
        "basis_edge_count": edge_count,
        "all_endpoint_graphs_connected": True,
        "endpoint_evidence": evidence,
        "connectivity_evidence_sha256": hashlib.sha256(
            _canonical_json(evidence).encode("utf-8")
        ).hexdigest(),
    }


def _supplemental_gate_ledger(
    eq112: dict[str, Any], eq113: dict[str, Any], weak: dict[str, Any], root: Path
) -> dict[str, Any]:
    """Bind nonmerged Eq.(113)/(139) artifacts without importing their reductions."""

    path_branches = eq112.get("path_consistency_branches")
    source_branches = eq113.get("branches")
    if not isinstance(path_branches, dict) or not isinstance(source_branches, dict):
        raise AssertionError("supplemental branch artifacts are malformed")
    if eq113.get("branches_mixed") is not False:
        raise AssertionError("Eq.(113) branch artifact silently merges source readings")
    if eq113.get("literature_classification", {}).get("Eq113_indexing") != "SOURCE_AMBIGUITY":
        raise AssertionError("Eq.(113) source ambiguity classification changed")
    eq113_counts = {
        "EQ113_QN_BRANCH": len(path_branches.get("EQ113_QN_BRANCH", [])),
        "EQ113_QN_PLUS_1_BRANCH": len(path_branches.get("EQ113_QN_PLUS_1_BRANCH", [])),
    }
    source_counts = {
        "EQ113_QN_BRANCH": eq113.get("equations", {}).get("DERIVED_APPENDIX_QN_BRANCH"),
        "EQ113_QN_PLUS_1_BRANCH": eq113.get("equations", {}).get(
            "LITERAL_PRINTED_QN_PLUS_1_BRANCH"
        ),
    }
    if eq113_counts != {"EQ113_QN_BRANCH": 25, "EQ113_QN_PLUS_1_BRANCH": 25}:
        raise AssertionError("Eq.(113) 25/25 branch census changed")
    if (
        source_counts != eq113_counts
        or {
            "EQ113_QN_BRANCH": source_branches.get("DERIVED_APPENDIX_QN_BRANCH", {}).get(
                "relation_count"
            ),
            "EQ113_QN_PLUS_1_BRANCH": source_branches.get(
                "LITERAL_PRINTED_QN_PLUS_1_BRANCH", {}
            ).get("relation_count"),
        }
        != eq113_counts
    ):
        raise AssertionError("Eq.(113) source branch/equation counts disagree")

    eq139 = weak.get("direct_substitution", {}).get("Eq139", {}).get("branches")
    if not isinstance(eq139, dict):
        raise AssertionError("Eq.(139) coverage artifact is malformed")
    printed = eq139.get("EQ139_PRINTED_STRICT_M_K_LT_N", {})
    completed = eq139.get("EQ139_EQ145_COMPLETED_M_K_LE_N", {})
    if printed.get("instance_count") != 4 or completed.get("instance_count") != 10:
        raise AssertionError("Eq.(139) 4/10 domain census changed")
    coverage = weak.get("Eq139_coverage", {})
    if coverage.get("coverage_verdict") != "EQ139_TWO_SOURCE_DOMAINS_COMPLETE_N4":
        raise AssertionError("Eq.(139) two-domain coverage artifact changed")
    return {
        "authoritative_artifacts": {
            EQ112_PATH: _sha256(root / EQ112_PATH),
            EQ113_BRANCH_PATH: _sha256(root / EQ113_BRANCH_PATH),
            WEAK_D2_PATH: _sha256(root / WEAK_D2_PATH),
        },
        "Eq113": {
            "derived_Qn_branch_records": eq113_counts["EQ113_QN_BRANCH"],
            "literal_Qn_plus_1_branch_records": eq113_counts["EQ113_QN_PLUS_1_BRANCH"],
            "branches_kept_separate": True,
            "source_status": "SOURCE_AMBIGUITY",
            "source_native_role": "VALIDATION_ONLY_FAIL_CLOSED",
            "reason": (
                "The stored path records use Eq.(112) B definitions; no source-native "
                "weak-MSR derivation is compiled here."
            ),
        },
        "Eq139": {
            "printed_strict_instances": printed["instance_count"],
            "Eq145_completed_instances": completed["instance_count"],
            "domains_kept_separate": True,
            "under_strong_GC": "DERIVED_WHEN_THE_CORRESPONDING_GC_SQUARE_IS_IN_SCOPE",
            "source_native_role": "VALIDATION_ONLY_FAIL_CLOSED_FOR_FULL_N4_DOMAIN",
            "stage_coverage_boundary": {
                "n=2": "strong-GC endpoint stage 4 is present",
                "n=3": "strong-GC endpoint stage 5 is present",
                "n=4": "requires endpoint stage 6; absent from the n<=4 compiler",
            },
        },
        "downstream_witness_validation": {
            "required": True,
            "rule": (
                "Any proposed source-native witness must directly substitute all 25/25 "
                "Eq.(113) branch records and all 4/10 Eq.(139) domain records without "
                "merging branches or domains."
            ),
            "included_as_source_coordinate_equations": False,
        },
    }


def compile_source_native_955_slack_v042(root: Path) -> dict[str, Any]:
    """Return the exact source-native 955 inventory without running a solver."""

    paths = {
        SOURCE_CPOBC_PATH: root / SOURCE_CPOBC_PATH,
        REDUCTION_PATH: root / REDUCTION_PATH,
        LOCAL_GC_PATH: root / LOCAL_GC_PATH,
        EQ112_PATH: root / EQ112_PATH,
        EQ113_BRANCH_PATH: root / EQ113_BRANCH_PATH,
        WEAK_D2_PATH: root / WEAK_D2_PATH,
        DEPENDENCY_PATH: root / DEPENDENCY_PATH,
        EQ120_PATH: root / EQ120_PATH,
    }
    source, reduction, local_gc, eq112, eq113, weak, dependency, eq120 = (
        _load(paths[path])
        for path in (
            SOURCE_CPOBC_PATH,
            REDUCTION_PATH,
            LOCAL_GC_PATH,
            EQ112_PATH,
            EQ113_BRANCH_PATH,
            WEAK_D2_PATH,
            DEPENDENCY_PATH,
            EQ120_PATH,
        )
    )
    reduction_map = reduction.get("reduction_map")
    if not isinstance(reduction_map, list) or len(reduction_map) != 165:
        raise AssertionError("expected exactly 165 frozen occurrence records")
    by_occurrence = {str(record["occurrence_id"]): record for record in reduction_map}
    if len(by_occurrence) != 165:
        raise AssertionError("occurrence identifiers must be unique")
    by_orbit: dict[str, list[dict[str, Any]]] = {}
    for record in reduction_map:
        by_orbit.setdefault(str(record["orbit_id"]), []).append(record)
    if len(by_orbit) != 131:
        raise AssertionError("expected 131 ON quotient transition orbits")
    occurrence_to_representative = {
        str(record["occurrence_id"]): min(str(item["occurrence_id"]) for item in records)
        for records in by_orbit.values()
        for record in records
    }
    orbit_inventory: list[dict[str, Any]] = [
        {
            "orbit_id": orbit_id,
            "representative_occurrence_id": min(str(record["occurrence_id"]) for record in records),
            "representative_operator_variable": next(
                str(record["operator_variable"])
                for record in records
                if str(record["occurrence_id"])
                == min(str(item["occurrence_id"]) for item in records)
            ),
            "occurrence_ids": sorted(str(record["occurrence_id"]) for record in records),
            "alias_count": len(records),
            "transition_kinds": sorted({str(record["transition_kind"]) for record in records}),
        }
        for orbit_id, records in sorted(by_orbit.items())
    ]
    if sum(int(item["alias_count"]) for item in orbit_inventory) != 165:
        raise AssertionError("orbit aliases do not cover the occurrence inventory")

    kind_counts = Counter(str(record["transition_kind"]) for record in reduction_map)
    if kind_counts != Counter({"GREGARIOUS": 24, "NON_TIMID": 117, "TIMID": 24}):
        raise AssertionError("frozen transition-kind census changed")

    constraints = source.get("MSR_operator_constraints")
    if not isinstance(constraints, list) or len(constraints) != 24:
        raise AssertionError("expected exactly 24 raw source MSR constraints")
    source_recurrences: list[dict[str, Any]] = []
    timid_occurrences: set[str] = set()
    for constraint in sorted(constraints, key=lambda item: str(item["source_id"])):
        source_id = str(constraint["source_id"])
        terms = constraint.get("terms")
        if constraint.get("identity_coefficient") != -1 or not isinstance(terms, list):
            raise AssertionError(f"malformed raw MSR row at {source_id}")
        timid = [
            term
            for term in terms
            if by_occurrence[str(term["transition_id"])]["transition_kind"] == "TIMID"
        ]
        if len(timid) != 1:
            raise AssertionError(f"source {source_id} must have exactly one timid transition")
        timid_term = timid[0]
        timid_id = str(timid_term["transition_id"])
        timid_occurrences.add(timid_id)
        if int(timid_term["coefficient"]) != 1:
            raise AssertionError(f"timid MSR coefficient is not one at {source_id}")
        non_timid = [term for term in terms if term is not timid_term]
        source_recurrences.append(
            {
                "source_id": source_id,
                "raw_MSR_constraint_id": str(constraint["constraint_id"]),
                "timid_occurrence_id": timid_id,
                "timid_orbit_representative": occurrence_to_representative[timid_id],
                "non_timid_occurrence_ids": [str(term["transition_id"]) for term in non_timid],
                "non_timid_coefficients": [int(term["coefficient"]) for term in non_timid],
                "non_timid_orbit_representatives": [
                    occurrence_to_representative[str(term["transition_id"])] for term in non_timid
                ],
                "slack_parameters": [f"u:{source_id}:0", f"u:{source_id}:1"],
                "state_symbol": f"v:{source_id}",
                "timid_definition": {
                    "lhs": f"A:{occurrence_to_representative[timid_id]}",
                    "rhs": [
                        "I",
                        *[
                            f"-{int(term['coefficient'])}*A:"
                            f"{occurrence_to_representative[str(term['transition_id'])]}"
                            for term in non_timid
                        ],
                        f"+u:{source_id}*(J*v:{source_id})^T",
                    ],
                },
                "reachable_MSR_after_substitution": {
                    "residual": f"u:{source_id}*(J*v:{source_id})^T*v:{source_id}",
                    "identity": "u_c*(-v_2*v_1+v_1*v_2)=0",
                    "constraint_emitted": False,
                },
                "legacy_u_zero_recovery": {
                    "u": [0, 0],
                    "timid_definition": "T_c=I-sum_non_timid(A)",
                    "meaning": "raw source strong-operator-MSR slice only",
                },
            }
        )
    if len(timid_occurrences) != 24:
        raise AssertionError("the 24 source MSR rows do not expose 24 timid occurrences")

    signature_to_representative: dict[tuple[int, int, int], str] = {}
    for record in reduction_map:
        key = _signature_key(record)
        representative = occurrence_to_representative[str(record["occurrence_id"])]
        previous = signature_to_representative.setdefault(key, representative)
        if previous != representative:
            raise AssertionError(f"conflicting ON representative for source signature {key}")

    path_inventory = local_gc.get("path_inventory")
    basis = local_gc.get("generating_relation_basis")
    if not isinstance(path_inventory, dict) or not isinstance(basis, list) or len(basis) != 320:
        raise AssertionError("expected the 320-relation strong-GC path basis")
    strong_gc_graph = _strong_gc_graph_audit(path_inventory, basis)
    canonical_state_paths: list[dict[str, Any]] = []
    source_ids = {record["source_id"] for record in source_recurrences}
    for stage in (1, 2, 3, 4):
        paths_at_stage = path_inventory.get(str(stage))
        if not isinstance(paths_at_stage, list):
            raise AssertionError(f"missing strong-GC path inventory at stage {stage}")
        for endpoint in sorted({str(path["endpoint_causet_id"]) for path in paths_at_stage}):
            candidates = [
                path for path in paths_at_stage if str(path["endpoint_causet_id"]) == endpoint
            ]
            chosen = min(candidates, key=lambda path: str(path["path_id"]))
            mapped: list[str] = []
            for transition in chosen.get("transitions", []):
                signature = transition.get("quotient_signature")
                if not isinstance(signature, dict):
                    raise AssertionError("strong-GC path lacks quotient signature")
                key = (
                    int(signature["stage"]),
                    int(signature["source_relation_code"]),
                    int(signature["precursor_code"]),
                )
                mapped.append(f"A:{signature_to_representative[key]}")
            canonical_state_paths.append(
                {
                    "source_id": endpoint,
                    "state_symbol": f"v:{endpoint}",
                    "canonical_path_id": str(chosen["path_id"]),
                    "operator_word_later_on_left": list(reversed(mapped)),
                    "definition": (
                        "v:p1-0=Omega"
                        if endpoint == "p1-0"
                        else f"v:{endpoint}=({'*'.join(reversed(mapped))})*Omega"
                    ),
                }
            )
    if {record["source_id"] for record in canonical_state_paths} != source_ids:
        raise AssertionError("canonical state paths do not cover all 24 MSR sources")

    gc_basis_inventory: list[dict[str, Any]] = []
    for relation in basis:

        def map_word(word: list[str]) -> list[str]:
            # The path basis names ``A_stage_signature``.  Recover the source
            # signature from the named transitions rather than importing a Q reduction.
            mapped_word: list[str] = []
            for token in word:
                matching: str | None = None
                for stage_paths in path_inventory.values():
                    for path in stage_paths:
                        for transition in path.get("transitions", []):
                            if transition.get("quotient_operator_symbol") == token:
                                signature = transition["quotient_signature"]
                                key = (
                                    int(signature["stage"]),
                                    int(signature["source_relation_code"]),
                                    int(signature["precursor_code"]),
                                )
                                candidate = f"A:{signature_to_representative[key]}"
                                if matching is not None and matching != candidate:
                                    raise AssertionError("ambiguous strong-GC path token")
                                matching = candidate
                if matching is None:
                    raise AssertionError(f"unmapped strong-GC path token: {token}")
                mapped_word.append(matching)
            return mapped_word

        gc_basis_inventory.append(
            {
                "relation_id": str(relation["relation_id"]),
                "endpoint_causet_id": str(relation["endpoint_causet_id"]),
                "lhs_source_word": map_word(list(relation["lhs_word"])),
                "rhs_source_word": map_word(list(relation["rhs_word"])),
                "provenance": "strong-GC path equality; source occurrence aliases only",
            }
        )

    cpobc_equations: list[dict[str, Any]] = []
    for relation in source.get("relations", []):
        aliases = relation.get("transition_orbit")
        equations = relation.get("denominator_cleared_form", {}).get(
            "noncommutative_polynomial_equations"
        )
        if not isinstance(aliases, dict) or not isinstance(equations, list):
            raise AssertionError("malformed raw CPOBC relation")
        for equation in equations:
            lhs = [
                occurrence_to_representative[str(aliases[symbol]["occurrence_id"])]
                for symbol in equation["lhs_word"]
            ]
            rhs = [
                occurrence_to_representative[str(aliases[symbol]["occurrence_id"])]
                for symbol in equation["rhs_word"]
            ]
            cpobc_equations.append(
                {
                    "relation_id": str(relation["relation_id"]),
                    "equation_id": str(equation["equation_id"]),
                    "lhs_source_word": [f"A:{item}" for item in lhs],
                    "rhs_source_word": [f"A:{item}" for item in rhs],
                }
            )
    if len(cpobc_equations) != 783:
        raise AssertionError("expected 783 raw source CPOBC equations")

    eq108_edge = {
        "from": "paper:eq108",
        "to": "axiom:MSR",
        "type": "MSR_ELIMINATION",
    }
    if eq108_edge not in dependency.get("edges", []):
        raise AssertionError("dependency graph no longer records Eq.(108) MSR elimination")
    eq112_counts = eq112.get("counts", {})
    if eq112_counts.get("non_antichain_G_generators") != 20:
        raise AssertionError("Eq.(112) non-antichain generator census changed")
    eq120_binding = _eq120_binding(eq120, root)
    supplemental_gates = _supplemental_gate_ledger(eq112, eq113, weak, root)

    search_patches = [
        {
            "patch_id": f"N_NONZERO_{record['source_id']}_{coordinate}",
            "source_id": record["source_id"],
            "slack_coordinate": record["slack_parameters"][coordinate],
            "auxiliary_inverse": f"w:{record['source_id']}:{coordinate}",
            "saturation_equation": (
                f"w:{record['source_id']}:{coordinate}*u:{record['source_id']}:{coordinate}-1=0"
            ),
            "justification": "v_c!=0 implies N_c=0 iff u_c=(0,0)",
        }
        for record in source_recurrences
        for coordinate in range(2)
    ]
    if len(search_patches) != 48:
        raise AssertionError("N!=0 patch census must equal 48")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "characteristic-zero field",
            "identification_mode": "ON_QUOTIENT",
            "nonsingularity": "all 165 source occurrences; 131 quotient localisations",
        },
        "source_artifact_sha256": {
            path: _sha256(path_object) for path, path_object in paths.items()
        },
        "operator_namespace": {
            "raw_occurrences": 165,
            "ON_quotient_orbits": 131,
            "alias_occurrences": 34,
            "orbit_inventory": orbit_inventory,
            "all_165_occurrences_covered": True,
        },
        "source_state_recurrence": {
            "initial_state": "v:p1-0=Omega, Omega!=0",
            "derived_state_symbols": 24,
            "canonical_paths": canonical_state_paths,
            "path_independence_enforced_by": {
                "strong_GC_basis_relations": strong_gc_graph["basis_edge_count"],
                "all_same_endpoint_pairs_derivable": strong_gc_graph[
                    "unordered_same_endpoint_pair_count"
                ],
                "endpoint_graph_connectivity": strong_gc_graph,
            },
        },
        "timid_slack_recurrences": source_recurrences,
        "raw_source_system": {
            "CPOBC_equations": cpobc_equations,
            "strong_GC_basis": gc_basis_inventory,
            "reachable_MSR": {
                "source_constraints": 24,
                "vector_entry_constraints_before_substitution": 48,
                "constraints_after_substitution": 0,
                "identity_reason": "(Jv_c)^T v_c=0 for every source c",
            },
            "nonsingularity": {
                "raw_occurrence_determinant_localisations": 165,
                "distinct_ON_quotient_determinant_localisations": 131,
            },
        },
        "search_ready_inventory": {
            "base_scalar_unknowns": {
                "ON_quotient_operator_matrix_entries": 524,
                "slack_coordinates": 48,
                "total": 572,
                "excluded": [
                    "fixed initial vector Omega",
                    "derived reachable-state symbols v:c",
                    "localisation inverse auxiliaries",
                ],
            },
            "matrix_equation_blocks": {
                "raw_CPOBC": 783,
                "strong_GC_spanning_basis": 320,
                "timid_source_definitions": 24,
                "total": 1127,
                "dimension_two_scalar_entry_equations": 4508,
            },
            "reachable_MSR_identity_blocks": 24,
            "N_nonzero_open_cover": {
                "coordinate_patches": 48,
                "one_auxiliary_scalar_per_patch": True,
                "solver_runs": 0,
                "coverage": "union of u:c:i != 0 equals union of N_c != 0 under v_c!=0",
            },
        },
        "forbidden_or_retained_boundaries": {
            "retained": [
                "raw 783 CPOBC word equations",
                "raw 320 strong-GC spanning-basis word equations",
                "raw source MSR rows rewritten only by the displayed slack definitions",
                "165-occurrence nonsingularity with 131 ON quotient localisations",
            ],
            "forbidden_as_coordinate_definitions": [
                "paper Eq.(108) operator-MSR elimination",
                "117 frozen Eq.(107)-then-(108) non-timid reductions",
                "24 frozen Eq.(108) timid reductions",
                "Eq.(112) B-factor reconstruction and its 20 eliminated non-antichain generators",
                "v0.4.1 frozen Q transition predicates and 42-chart solver input ideals",
            ],
            "dependency_audit": {
                "Eq108_to_MSR_edge_present": True,
                "occurrences_requiring_Eq108_in_frozen_reduction": 141,
                "Eq112_eliminated_nonantichain_generators": 20,
            },
        },
        "Eq120_source_native_reuse": eq120_binding,
        "supplemental_gate_ledger": supplemental_gates,
        "legacy_slice": {
            "u_zero_at_all_24_sources": True,
            "recovered_semantics": "raw source strong-operator MSR",
            "not_claimed": "recovery of the frozen Eq.(108)-expanded Q presentation",
        },
        "solver_status": "NOT_RUN",
        "sage_status": "NOT_INVOKED",
        "claim_boundary": [
            (
                "This inventory is a source-native coverage/provenance verifier and "
                "structured word/matrix-block system declaration."
            ),
            (
                "It does not prove commutativity, find a noncommutative witness, "
                "expand a scalar-polynomial solver manifest, or establish a global chart cover."
            ),
            (
                "Eq.(120) reuse is limited to its separately certified "
                "source-nonsingular CPOBC prerequisite."
            ),
            (
                "Eq.(113) and Eq.(139) remain nonmerged downstream witness-validation "
                "gates, not source coordinate equations."
            ),
        ],
        "verdict": VERDICT,
        "passed": True,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_source_native_955_slack_v042(root: Path) -> Path:
    """Write the intentional v0.4.2 inventory artifact; never touch v0.4.1 bytes."""

    destination = root / RESULT_PATH
    payload = compile_source_native_955_slack_v042(root)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination
