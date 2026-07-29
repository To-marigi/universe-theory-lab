"""v0.3.6 census and rejected-closure audit for the literal Q5 generator.

This module deliberately separates three questions:

1. Which frozen n<=4 relations genuinely constrain Q5?
2. Which all-stage Q-only consequences are safe to test at index 5?
3. Is the proposed generator-shift closure proved to be a subset of the
   genuine n=5 relation ideal?

The third gate is negative.  The final v0.3.6 result does not attempt that
closure: :mod:`q5_vacuity_v036` instead proves directly that the twelve
compiled scalar equations containing Q5 vanish identically on the frozen
witness base point.  This module remains the reproducible census supporting
that proof.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.d2_localisation_v034 import LITERAL_BRANCH
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

BRANCH = "codex/final-theory-v0.3.6-q5-closure-20260729"
SCHEMA_CENSUS = "final-theory-q5-constraint-census-v0.3.6"
DIRECT_SYSTEM_PATH = (
    "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
)
COMPACT_ARENA_PATH = (
    "certificates/d2_saturation/v0.3.5_compact_expression_arena.json.gz"
)
POLYNOMIAL_SYSTEM_PATH = "results/v0.3.4_polynomial_systems.json"
WITNESS_PATH = "results/v0.3.5_explicit_rational_witness.json"
PAPER_PATH = (
    "references/papers/"
    "2603.25503v1_srivastava-surya_quantum-bell-causality-qsg.pdf"
)
Q_SYMBOL_PATTERN = re.compile(r"^q([1-9][0-9]*)_[12][12]$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _matrix_from_strings(entries: list[list[str]]) -> sp.Matrix:
    return sp.Matrix(
        [[sp.Rational(value) for value in row] for row in entries]
    )


def _matrix_record(matrix: sp.Matrix) -> list[list[str]]:
    return [[str(sp.cancel(value)) for value in matrix.row(row)] for row in range(2)]


def _is_zero_matrix(matrix: sp.Matrix) -> bool:
    return all(sp.cancel(value) == 0 for value in matrix)


def _commutator(left: sp.Matrix, right: sp.Matrix) -> sp.Matrix:
    return (left * right - right * left).applyfunc(sp.cancel)


def _relation_words(record: dict[str, Any]) -> list[list[str]]:
    if "expression" in record:
        return [term["word"] for term in record["expression"]]
    return [record["lhs_word"], record["rhs_word"]]


def _direct_q_generators(words: Iterable[Iterable[str]]) -> set[str]:
    generators: set[str] = set()
    for word in words:
        for token in word:
            base = token.removesuffix("^-1")
            if base.startswith("Q_"):
                generators.add(base)
    return generators


def _dependency_resolver(
    dependency_nodes: list[dict[str, Any]],
) -> tuple[Any, list[str]]:
    definitions = {record["node_id"]: record for record in dependency_nodes}
    cache: dict[str, frozenset[str]] = {}
    unknown_tokens: set[str] = set()
    visiting: list[str] = []

    def resolve(token: str) -> frozenset[str]:
        base = token.removesuffix("^-1")
        if base.startswith("Q_"):
            return frozenset((base,))
        if token in cache:
            return cache[token]
        definition = definitions.get(token)
        if definition is None:
            unknown_tokens.add(token)
            return frozenset()
        if token in visiting:
            raise RuntimeError(f"cycle in dependency DAG: {visiting + [token]}")
        visiting.append(token)
        generators: set[str] = set()
        if definition["kind"] == "Q_GENERATOR":
            generators.add(token)
        elif definition["kind"] == "Q_GENERATOR_INVERSE":
            generators.add(token.removesuffix("^-1"))
        for dependency in definition.get("dependencies", []):
            generators.update(resolve(dependency))
        visiting.pop()
        result = frozenset(generators)
        cache[token] = result
        return result

    return resolve, sorted(unknown_tokens)


def _compact_arena_q_masks(root: Path) -> tuple[dict[str, int], dict[str, Any]]:
    arena_path = root / COMPACT_ARENA_PATH
    with gzip.open(arena_path, "rt", encoding="utf-8") as handle:
        arena = json.load(handle)
    masks: list[int] = []
    for index, node in enumerate(arena["nodes"]):
        operation = int(node[0])
        if operation == 0:
            mask = 0
        elif operation == 1:
            match = Q_SYMBOL_PATTERN.match(node[1])
            mask = 0 if match is None else 1 << int(match.group(1))
        else:
            mask = 0
            for child in node[1]:
                if child >= index:
                    raise RuntimeError("compact arena is not topologically ordered")
                mask |= masks[child]
        masks.append(mask)
    target_masks = {
        expression_id: masks[index]
        for expression_id, index in arena["target_indices"].items()
    }
    metadata = {
        "path": COMPACT_ARENA_PATH,
        "sha256": _sha256(arena_path),
        "schema_version": arena["schema_version"],
        "node_count": arena["node_count"],
        "target_count": arena["target_count"],
    }
    return target_masks, metadata


def _witness_reconfirmation(root: Path) -> dict[str, Any]:
    witness_path = root / WITNESS_PATH
    witness = _load_json(witness_path)
    q_matrices = {
        int(name.split("_", 1)[1]): _matrix_from_strings(entries)
        for name, entries in witness["Q_matrices"].items()
    }
    q1_inverse = q_matrices[1].inv()
    ratios = {
        f"R_{stage}": _matrix_record(q1_inverse * q_matrices[stage])
        for stage in sorted(q_matrices)
    }
    commutators: list[dict[str, Any]] = []
    for left, right in itertools.combinations(sorted(q_matrices), 2):
        residual = _commutator(q_matrices[left], q_matrices[right])
        commutators.append(
            {
                "pair": [f"Q_{left}", f"Q_{right}"],
                "matrix": _matrix_record(residual),
                "zero": _is_zero_matrix(residual),
                "involves_Q5": 5 in {left, right},
            }
        )
    q1_to_q4 = [
        record
        for record in commutators
        if record["pair"][1] != "Q_5"
    ]
    nonzero = [record for record in commutators if not record["zero"]]
    determinants = {
        f"Q_{stage}": str(sp.cancel(matrix.det()))
        for stage, matrix in sorted(q_matrices.items())
    }
    expected = {
        "Q_1": [["1", "1"], ["1", "2"]],
        "Q_2": [["2", "2"], ["2", "4"]],
        "Q_3": [["3", "3"], ["3", "6"]],
        "Q_4": [["4", "4"], ["4", "8"]],
        "Q_5": [["6", "5"], ["6", "10"]],
    }
    passed = bool(
        witness["Q_matrices"] == expected
        and determinants["Q_1"] == "1"
        and determinants["Q_5"] == "30"
        and all(record["zero"] for record in q1_to_q4)
        and nonzero
        and all(record["involves_Q5"] for record in nonzero)
        and ratios["R_1"] == [["1", "0"], ["0", "1"]]
        and ratios["R_2"] == [["2", "0"], ["0", "2"]]
        and ratios["R_3"] == [["3", "0"], ["0", "3"]]
        and ratios["R_4"] == [["4", "0"], ["0", "4"]]
        and ratios["R_5"] == [["6", "0"], ["0", "5"]]
    )
    return {
        "source": WITNESS_PATH,
        "source_sha256": _sha256(witness_path),
        "Q_matrices": witness["Q_matrices"],
        "determinants": determinants,
        "R_n_equals_Q1_inverse_Qn": ratios,
        "pairwise_commutators": commutators,
        "Q1_through_Q4_pairwise_commutative": all(
            record["zero"] for record in q1_to_q4
        ),
        "nonzero_commutator_pairs": [
            record["pair"] for record in nonzero
        ],
        "every_nonzero_commutator_involves_Q5": all(
            record["involves_Q5"] for record in nonzero
        ),
        "representative_Q1_Q5_commutator": next(
            record["matrix"]
            for record in nonzero
            if record["pair"] == ["Q_1", "Q_5"]
        ),
        "passed": passed,
    }


def compile_q5_constraint_census(root: Path) -> dict[str, Any]:
    """Compile the exact direct/transitive/nonzero Q5 constraint census."""

    direct_path = root / DIRECT_SYSTEM_PATH
    systems_path = root / POLYNOMIAL_SYSTEM_PATH
    direct = _load_json(direct_path)
    systems = _load_json(systems_path)
    witness = _witness_reconfirmation(root)
    resolve, _ = _dependency_resolver(direct["dependency_nodes"])
    unknown_tokens: set[str] = set()
    branch_dependencies: dict[str, list[dict[str, Any]]] = {}
    for branch, records in direct["relations"].items():
        compiled_records: list[dict[str, Any]] = []
        for record in records:
            words = _relation_words(record)
            direct_q = _direct_q_generators(words)
            transitive_q: set[str] = set()
            for word in words:
                for token in word:
                    resolved = resolve(token)
                    if not resolved and not token.removesuffix(
                        "^-1"
                    ).startswith("Q_"):
                        unknown_tokens.add(token)
                    transitive_q.update(resolved)
            compiled_records.append(
                {
                    "relation_id": record["relation_id"],
                    "family": record["family"],
                    "source_stage": record["source_stage"],
                    "direct_Q_generators": sorted(direct_q),
                    "transitive_Q_generators": sorted(transitive_q),
                }
            )
        branch_dependencies[branch] = compiled_records

    target_masks, arena_metadata = _compact_arena_q_masks(root)
    literal_equations = systems["systems"][LITERAL_BRANCH]["equations"]
    q5_bit = 1 << 5
    q5_scalar_records: list[dict[str, Any]] = []
    relation_to_equations: defaultdict[str, set[str]] = defaultdict(set)
    relation_to_entries: defaultdict[str, set[tuple[int, int]]] = defaultdict(
        set
    )
    relation_to_family: dict[str, str] = {}
    for equation in literal_equations:
        mask = target_masks[equation["canonical_expression_id"]]
        if not mask & q5_bit:
            continue
        provenance_records = []
        for provenance in equation["provenance"]:
            relation_id = provenance["relation_id"]
            entry = tuple(provenance["matrix_entry"])
            relation_to_equations[relation_id].add(equation["equation_id"])
            relation_to_entries[relation_id].add(entry)
            relation_to_family[relation_id] = provenance["family"]
            provenance_records.append(
                {
                    "relation_id": relation_id,
                    "family": provenance["family"],
                    "matrix_entry": list(entry),
                }
            )
        q_stages = [
            stage for stage in range(1, 10) if mask & (1 << stage)
        ]
        q5_scalar_records.append(
            {
                "equation_id": equation["equation_id"],
                "canonical_expression_id": equation[
                    "canonical_expression_id"
                ],
                "Q_generator_dependencies": [
                    f"Q_{stage}" for stage in q_stages
                ],
                "provenance": provenance_records,
            }
        )

    q5_constraining_relation_ids = sorted(relation_to_equations)
    q5_direct_records = [
        record
        for record in branch_dependencies[LITERAL_BRANCH]
        if "Q_5" in record["direct_Q_generators"]
    ]
    q5_transitive_records = [
        record
        for record in branch_dependencies[LITERAL_BRANCH]
        if "Q_5" in record["transitive_Q_generators"]
    ]
    identity_ids = set(
        direct["relation_to_scalar_equation_coverage"][LITERAL_BRANCH][
            "identically_zero_path_relation_ids"
        ]
    )
    q5_identity_ids = sorted(
        record["relation_id"]
        for record in q5_transitive_records
        if record["relation_id"] in identity_ids
    )

    family_totals = Counter(
        record["family"]
        for record in branch_dependencies[LITERAL_BRANCH]
    )
    family_direct_q5 = Counter(
        record["family"] for record in q5_direct_records
    )
    family_transitive_q5 = Counter(
        record["family"] for record in q5_transitive_records
    )
    family_constraining_q5 = Counter(
        relation_to_family[relation_id]
        for relation_id in q5_constraining_relation_ids
    )
    family_scalar_q5 = Counter(
        provenance["family"]
        for equation in q5_scalar_records
        for provenance in equation["provenance"]
    )
    family_census = {
        family: {
            "total_matrix_relations": family_totals[family],
            "relations_with_direct_Q5_token": family_direct_q5[family],
            "relations_with_transitive_Q5_dependency": (
                family_transitive_q5[family]
            ),
            "nonzero_matrix_relations_constraining_Q5": (
                family_constraining_q5[family]
            ),
            "canonical_scalar_numerators_depending_on_Q5": (
                family_scalar_q5[family]
            ),
        }
        for family in sorted(family_totals)
    }
    dependency_set_distributions = {
        branch: dict(
            sorted(
                Counter(
                    ",".join(record["transitive_Q_generators"]) or "NONE"
                    for record in records
                ).items()
            )
        )
        for branch, records in branch_dependencies.items()
    }
    dependency_node_kind_counts = dict(
        sorted(
            Counter(
                record["kind"] for record in direct["dependency_nodes"]
            ).items()
        )
    )
    system_summary = {
        branch: {
            "generator_inventory": len(record["generator_inventory"]),
            "generator_ids": record["generator_inventory"],
            "scalar_unknowns": record[
                "scalar_unknowns_before_stratum_substitution"
            ],
            "relation_count": record["relation_count"],
            "canonical_numerator_equation_count": record[
                "canonical_numerator_equation_count"
            ],
            "relation_family_counts": record["relation_family_counts"],
        }
        for branch, record in systems["systems"].items()
    }
    derived_q5 = [
        record
        for record in branch_dependencies[
            "DERIVED_APPENDIX_QN_BRANCH"
        ]
        if "Q_5" in record["transitive_Q_generators"]
    ]
    total_constraining = len(q5_constraining_relation_ids)
    passed = bool(
        witness["passed"]
        and system_summary["DERIVED_APPENDIX_QN_BRANCH"][
            "generator_inventory"
        ]
        == 4
        and system_summary[LITERAL_BRANCH]["generator_inventory"] == 5
        and system_summary["DERIVED_APPENDIX_QN_BRANCH"][
            "scalar_unknowns"
        ]
        == 16
        and system_summary[LITERAL_BRANCH]["scalar_unknowns"] == 20
        and all(
            record["relation_count"] == 1001
            and record["canonical_numerator_equation_count"] == 2564
            for record in system_summary.values()
        )
        and not derived_q5
        and len(q5_direct_records) == 24
        and len(q5_transitive_records) == 24
        and len(q5_identity_ids) == 21
        and total_constraining == 3
        and len(q5_scalar_records) == 12
        and not unknown_tokens
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_CENSUS,
        "branch": BRANCH,
        "finite_scope": "frozen source stages n<=4",
        "semantic_profile": "PAPER_STRONG_OPERATOR_PROFILE",
        "source_index_branch": LITERAL_BRANCH,
        "source_artifacts": {
            DIRECT_SYSTEM_PATH: _sha256(direct_path),
            POLYNOMIAL_SYSTEM_PATH: _sha256(systems_path),
            COMPACT_ARENA_PATH: arena_metadata["sha256"],
            WITNESS_PATH: witness["source_sha256"],
        },
        "witness_reconfirmation": witness,
        "polynomial_system_comparison": system_summary,
        "dependency_method": {
            "direct": "literal Q_i tokens in each reduced operator word",
            "transitive": (
                "recursive closure through all 92 frozen dependency-DAG nodes"
            ),
            "constraining": (
                "a matrix relation is counted only when at least one nonzero "
                "canonical scalar numerator has a q5_ab symbol and cites that "
                "relation in provenance"
            ),
            "unknown_dependency_tokens": sorted(unknown_tokens),
            "compact_arena": arena_metadata,
        },
        "dependency_DAG_census": {
            "node_count": len(direct["dependency_nodes"]),
            "node_kind_counts": dependency_node_kind_counts,
            "cycle_detected": False,
            "branch_relation_dependency_set_distributions": (
                dependency_set_distributions
            ),
        },
        "literal_relation_family_census": family_census,
        "Q5_relation_ids": {
            "direct_or_transitive_occurrence": sorted(
                record["relation_id"] for record in q5_transitive_records
            ),
            "identically_zero_after_exact_reduction": q5_identity_ids,
            "nonzero_relations_constraining_Q5": (
                q5_constraining_relation_ids
            ),
        },
        "Q5_scalar_numerator_equations": q5_scalar_records,
        "Q5_constraining_relation_coverage": {
            relation_id: {
                "family": relation_to_family[relation_id],
                "matrix_entries": [
                    list(entry)
                    for entry in sorted(relation_to_entries[relation_id])
                ],
                "canonical_scalar_equation_ids": sorted(
                    relation_to_equations[relation_id]
                ),
            }
            for relation_id in q5_constraining_relation_ids
        },
        "headline_counts": {
            "literal_matrix_relations_total": 1001,
            "literal_canonical_scalar_numerators_total": 2564,
            "relations_with_direct_Q5_token": len(q5_direct_records),
            "relations_with_transitive_Q5_dependency": len(
                q5_transitive_records
            ),
            "Q5_relations_identically_zero_after_exact_reduction": len(
                q5_identity_ids
            ),
            "total_relations_constraining_Q5": total_constraining,
            "canonical_scalar_numerators_constraining_Q5": len(
                q5_scalar_records
            ),
        },
        "single_reported_total_relations_constraining_Q5": (
            total_constraining
        ),
        "interpretation": (
            "Q5 occurs in 24 literal Eq.(113) path records, but 21 of those "
            "are exact identities. Exactly 3 nonzero matrix relations, "
            "scalarised to 12 canonical numerator equations, constrain Q5. "
            "No CPOBC, local-GC, or strong-MSR relation depends on Q5."
        ),
        "exact_numeric_distinction": "EXACT_STRUCTURAL_AND_RATIONAL_CENSUS",
        "unresolved_components": [],
        "passed": passed,
        "verdict": (
            "V036_Q5_CONSTRAINT_CENSUS_COMPLETE"
            if passed
            else "V036_Q5_CONSTRAINT_CENSUS_FAILED"
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "witness": witness,
            "systems": system_summary,
            "families": family_census,
            "headline_counts": payload["headline_counts"],
            "relation_ids": payload["Q5_relation_ids"],
            "dependency_DAG_census": payload["dependency_DAG_census"],
        }
    )
    return payload


def _verified_universal_q_subset(
    q_matrices: dict[int, sp.Matrix],
) -> dict[str, Any]:
    eq120_records: list[dict[str, Any]] = []
    for n, m in itertools.combinations(range(1, 6), 2):
        for k in range(1, min(n, m)):
            residual = (
                q_matrices[n] * q_matrices[k].inv() * q_matrices[m]
                - q_matrices[m] * q_matrices[k].inv() * q_matrices[n]
            ).applyfunc(sp.cancel)
            eq120_records.append(
                {
                    "instance": {"n": n, "k": k, "m": m},
                    "involves_Q5": 5 in {n, k, m},
                    "residual": _matrix_record(residual),
                    "zero": _is_zero_matrix(residual),
                }
            )
    eq128_records: list[dict[str, Any]] = []
    for m, n, k, ell in itertools.permutations(range(1, 6), 4):
        first = q_matrices[m].inv() * q_matrices[n]
        second = q_matrices[k].inv() * q_matrices[ell]
        residual = _commutator(first, second)
        eq128_records.append(
            {
                "instance": {"m": m, "n": n, "k": k, "ell": ell},
                "involves_Q5": 5 in {m, n, k, ell},
                "zero": _is_zero_matrix(residual),
            }
        )
    first = q_matrices[1] * q_matrices[2].inv()
    second = q_matrices[1].inv() * q_matrices[2]
    eq130_residual = _commutator(first, second)
    payload = {
        "proof_boundary": (
            "These are conservative instances of paper Eqs.(120), (128), "
            "and (130), visually checked in arXiv:2603.25503v1 PDF pages "
            "28-29. They are genuine all-stage CPOBC consequences, but they "
            "are not a complete stage-5 CPOBC/GC/MSR compiler."
        ),
        "Eq120": {
            "instance_count": len(eq120_records),
            "Q5_instance_count": sum(
                record["involves_Q5"] for record in eq120_records
            ),
            "failed_instances": [
                record for record in eq120_records if not record["zero"]
            ],
            "records": eq120_records,
        },
        "Eq128": {
            "raw_pairwise_distinct_instance_count": len(eq128_records),
            "Q5_raw_instance_count": sum(
                record["involves_Q5"] for record in eq128_records
            ),
            "failed_instances": [
                record for record in eq128_records if not record["zero"]
            ],
            "deduplication_claimed": False,
        },
        "Eq130": {
            "instance_count": 1,
            "residual": _matrix_record(eq130_residual),
            "zero": _is_zero_matrix(eq130_residual),
        },
        "witness_passes_every_checked_instance": bool(
            all(record["zero"] for record in eq120_records)
            and all(record["zero"] for record in eq128_records)
            and _is_zero_matrix(eq130_residual)
        ),
    }
    return payload


def compile_q5_closure_audit(
    root: Path,
    census: dict[str, Any],
) -> dict[str, Any]:
    """Audit, but do not assume, the proposed generator-index closure."""

    q_matrices = {
        int(name.split("_", 1)[1]): _matrix_from_strings(entries)
        for name, entries in census["witness_reconfirmation"][
            "Q_matrices"
        ].items()
    }
    verified_subset = _verified_universal_q_subset(q_matrices)
    candidates = [
        {
            "candidate": "SHIFT_N4_CPOBC_700_TO_Q5",
            "source_family_count": 700,
            "status": "EXCLUDED_NOT_PROVED_N5_NECESSARY",
            "reason": (
                "Each relation is tied to a decorated Bell-family pair and "
                "stage-specific transition occurrences. Replacing a Q index "
                "does not supply an injective map to a genuine source-stage-5 "
                "Bell pair."
            ),
        },
        {
            "candidate": "SHIFT_N4_LOCAL_OPERATOR_GC_255_TO_Q5",
            "source_family_count": 255,
            "status": "EXCLUDED_NOT_PROVED_N5_NECESSARY",
            "reason": (
                "Each local-GC residual comes from a concrete same-endpoint "
                "path square. A Q-index substitution does not construct the "
                "required n=5 endpoint or its two labelled paths."
            ),
        },
        {
            "candidate": "SHIFT_N4_STRONG_OPERATOR_MSR_21_TO_Q5",
            "source_family_count": 21,
            "status": "EXCLUDED_NOT_PROVED_N5_NECESSARY",
            "reason": (
                "MSR sums depend on the complete child-orbit inventory and "
                "multiplicities of a source causet. The stage-5 inventory is "
                "not a generator-index translate of the n<=4 inventory."
            ),
        },
        {
            "candidate": "USE_DERIVED_EQ113_Q5_AT_SOURCE_STAGE_5",
            "source_family_count": 1,
            "status": "EXCLUDED_FROM_LITERAL_BRANCH",
            "reason": (
                "The visually verified printed Eq.(113) uses Q_(n+1), hence "
                "Q6 at source stage 5. Replacing it by Q5 silently imports the "
                "separate derived-index branch into the literal branch."
            ),
        },
    ]
    adopted = [
        {
            "candidate": "PAPER_EQ120_ALL_INDICES_THROUGH_5",
            "status": "ADOPTED_GENUINE_N5_NECESSARY_SUBSET",
            "proof": "Theorem 3.7 and paper Eq.(120), PDF page 28.",
            "instance_count": verified_subset["Eq120"]["instance_count"],
            "Q5_instance_count": verified_subset["Eq120"][
                "Q5_instance_count"
            ],
        },
        {
            "candidate": "PAPER_EQ128_PAIRWISE_DISTINCT_INDICES_THROUGH_5",
            "status": "ADOPTED_GENUINE_N5_NECESSARY_SUBSET",
            "proof": "Corollary 3.8 and paper Eq.(128), PDF page 28.",
            "raw_instance_count": verified_subset["Eq128"][
                "raw_pairwise_distinct_instance_count"
            ],
            "Q5_raw_instance_count": verified_subset["Eq128"][
                "Q5_raw_instance_count"
            ],
        },
        {
            "candidate": "PAPER_EQ130_Q1_Q2",
            "status": "ADOPTED_GENUINE_N5_NECESSARY_SUBSET",
            "proof": "Corollary 3.9 and paper Eq.(130), PDF page 29.",
            "instance_count": 1,
            "Q5_instance_count": 0,
        },
    ]
    requested_closure_established = False
    payload = {
        "paper_source": {
            "path": PAPER_PATH,
            "sha256": _sha256(root / PAPER_PATH),
            "version": "arXiv:2603.25503v1",
            "visual_checks": {
                "Eq103_through_Eq120": "PDF pages 26-28",
                "Eq128_through_Eq130": "PDF pages 28-29",
                "Eq135_through_Eq139": "PDF page 30",
            },
        },
        "candidate_template_audit": candidates,
        "adopted_verified_subset": adopted,
        "verified_subset_witness_check": verified_subset,
        "adopted_subset_is_genuine_necessary": True,
        "requested_generator_symmetric_closure_established": (
            requested_closure_established
        ),
        "adopted_subset_is_sufficient_for_requested_step_A": False,
        "safe_to_run_verdict_bearing_elimination": False,
        "witness_status_under_verified_subset": (
            "SURVIVES_EXACT_SUBSTITUTION"
            if verified_subset["witness_passes_every_checked_instance"]
            else "DIES_EXACT_SUBSTITUTION"
        ),
        "claim_boundary": (
            "Survival under the verified universal Q-only subset does not "
            "prove survival under the full genuine stage-5 relation ideal. "
            "The excluded index-shift templates must not be used to claim "
            "witness death."
        ),
        "verdict": "V036_Q5_CLOSURE_TEMPLATE_AUDIT_PARTIAL",
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "candidate_template_audit": candidates,
            "adopted_verified_subset": adopted,
            "verified_subset_witness_check": verified_subset,
            "requested_generator_symmetric_closure_established": False,
            "verdict": payload["verdict"],
        }
    )
    return payload


def write_q5_census_artifact(root: Path) -> dict[str, dict[str, Any]]:
    """Write only the exact census and return the rejected-closure audit."""

    census = compile_q5_constraint_census(root)
    if not census["passed"]:
        raise RuntimeError("Phase-0 Q5 census failed its integrity checks")
    closure_audit = compile_q5_closure_audit(root, census)
    _write_json(
        root / "results/v0.3.6_q5_constraint_census.json",
        census,
    )
    return {
        "census": census,
        "closure_audit": closure_audit,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    arguments = parser.parse_args(argv)
    payloads = write_q5_census_artifact(arguments.root.resolve())
    print(
        json.dumps(
            {
                "census": payloads["census"]["verdict"],
                "closure": payloads["closure_audit"]["verdict"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
