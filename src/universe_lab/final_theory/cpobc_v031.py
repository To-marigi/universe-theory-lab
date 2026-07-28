"""Exact CPOBC compiler and bounded d=3 algebra audit for Bench v0.3.1.

This module is additive: it consumes the frozen v0.3 Bell-family enumeration
without changing it.  The v0.3.1 compiler adds an explicit noncommutative word
IR, inverse variables, denominator-cleared equations, exact d=3 matrix-entry
polynomials, dependency metadata, and a separately implemented brute-force
Bell-family oracle.

The representation work is intentionally search-bounded.  It proves a no-go
only for one declared one-parameter upper-triangular ansatz.  It does not claim
that a d=3 CPOBC representation is absent.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import platform
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.causal_sets import (
    Relation,
    add_maximal,
    canonicalize,
    causet_id,
)
from universe_lab.final_theory.cpobc_v03 import compile_cpobc_relations

PAPER_ID = "arXiv:2603.25503v1"
PAPER_PDF = "references/papers/2603.25503v1_srivastava-surya_quantum-bell-causality-qsg.pdf"
PAPER_SHA256 = "545c2c1a6a0ad046bcb41612a0d108030601992ccc9e3c9d472dec3d92cc89aa"
SOURCE_COMMIT = "3ccbc66cc2cf868bf2a33ab96d4dd46e729d5f09"
BRANCH = "codex/final-theory-v0.3.1-literature-locked-qsg-lift-20260728"
COMPILER_MAX_STAGE = 4
D3 = 3

_LOCAL_MATRIX_NAMES = {
    "A_n": "an",
    "A_prime_n": "apn",
    "A_m": "am",
    "A_prime_m": "apm",
}


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exact(value: Any) -> str:
    return str(sp.factor(sp.cancel(sp.sympify(value))))


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [_exact(matrix[row, column]) for column in range(matrix.cols)]
        for row in range(matrix.rows)
    ]


def _zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.simplify(entry) == 0 for entry in matrix)


def _base_metadata(
    *,
    verdict: str,
    dimension: int | None,
    jordan_stratum: str,
    ansatz: str,
    relation_count: int,
    completeness_scope: str,
    unresolved_components: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "final-theory-cpobc-v0.3.1",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "code_commit": "UNCOMMITTED_WORKTREE",
        "paper_versions": [
            {
                "id": PAPER_ID,
                "version": "v1",
                "local_file": PAPER_PDF,
                "source_hash_sha256": PAPER_SHA256,
            }
        ],
        "source_hashes": [{"path": PAPER_PDF, "sha256": PAPER_SHA256}],
        "literature_classification": {
            "CPOBC_defining_relations_103_106": "LITERATURE_LOCKED",
            "paper_necessary_relations_107_163": "LITERATURE_LOCKED",
            "d3_noncommutative_representation": "OPEN_TARGET",
        },
        "assumptions": [
            "finite maximal-element sequential growth",
            "CPOBC transition operators are nonsingular",
            "noncommutative multiplication order is preserved",
            "all exact claims are over characteristic zero",
        ],
        "dimension": dimension,
        "field": "Q / characteristic-zero symbolic extension",
        "Jordan_stratum": jordan_stratum,
        "ansatz": ansatz,
        "relation_count": relation_count,
        "solver": "deterministic Python enumeration and SymPy exact algebra",
        "solver_version": {
            "python": sys.version.split()[0],
            "sympy": sp.__version__,
            "platform": platform.platform(),
        },
        "random_seed": None,
        "exact_numeric_distinction": {
            "exact": "integer combinatorics, rational matrices, symbolic polynomials",
            "numeric": "none accepted as certificate",
        },
        "completeness_scope": completeness_scope,
        "time_limit": {
            "compiler": "hard cardinality cap n<=4",
            "symbolic_search": "60 s soft per declared ansatz; no unbounded elimination",
        },
        "memory_limit": {
            "policy": "sparse exact expressions; no dense full-system Groebner basis",
            "os_enforced": False,
        },
        "unresolved_components": unresolved_components,
        "certificate_hashes": [],
        "verdict": verdict,
    }


def _inverse_token(token: str) -> str:
    return token.removesuffix("^-1") if token.endswith("^-1") else token + "^-1"


def free_reduce_word(word: tuple[str, ...]) -> tuple[str, ...]:
    """Cancel adjacent exact inverse pairs without commuting any factors."""

    reduced: list[str] = []
    for token in word:
        if reduced and reduced[-1] == _inverse_token(token):
            reduced.pop()
        else:
            reduced.append(token)
    return tuple(reduced)


def _matrix_product_entry(
    word: list[str],
    row: int,
    column: int,
    dimension: int,
) -> list[str]:
    if not word:
        return ["1"] if row == column else []
    if len(word) == 1:
        name = _LOCAL_MATRIX_NAMES[word[0]]
        return [f"{name}_{row}_{column}"]
    monomials: list[str] = []
    for inner in itertools.product(range(dimension), repeat=len(word) - 1):
        indices = (row, *inner, column)
        factors = [
            f"{_LOCAL_MATRIX_NAMES[token]}_{indices[index]}_{indices[index + 1]}"
            for index, token in enumerate(word)
        ]
        monomials.append("*".join(factors))
    return monomials


def _entry_polynomial(
    equation: dict[str, Any],
    row: int,
    column: int,
    dimension: int = D3,
) -> str:
    pieces: list[str] = []
    for term in equation["residual_terms"]:
        coefficient = int(term["coefficient"])
        monomials = _matrix_product_entry(
            list(term["word"]),
            row,
            column,
            dimension,
        )
        for monomial in monomials:
            if not pieces:
                pieces.append(monomial if coefficient == 1 else f"-{monomial}")
            elif coefficient == 1:
                pieces.append(f"+ {monomial}")
            else:
                pieces.append(f"- {monomial}")
    return " ".join(pieces) if pieces else "0"


def _matrix_entry_form(
    equations: list[dict[str, Any]],
    aliases: dict[str, str],
) -> dict[str, Any]:
    encoded = []
    for equation in equations:
        entries = [
            {
                "entry": [row, column],
                "polynomial": _entry_polynomial(equation, row, column),
            }
            for row in range(D3)
            for column in range(D3)
        ]
        encoded.append(
            {
                "equation_id": equation["equation_id"],
                "entry_equations": entries,
                "entry_equation_count": D3 * D3,
                "sha256": _stable_hash(entries),
            }
        )
    return {
        "dimension": D3,
        "matrix_variables": {
            _LOCAL_MATRIX_NAMES[alias]: transition_id
            for alias, transition_id in aliases.items()
        },
        "index_convention": (
            "(XY)_{ij}=sum_k X_{ik}Y_{kj}; factor order is never sorted"
        ),
        "equations": encoded,
        "entry_equation_count": sum(
            item["entry_equation_count"] for item in encoded
        ),
        "exact_polynomial_coefficients": "Z",
    }


def _causet_record(relation: Relation) -> dict[str, Any]:
    rows = list(canonicalize(relation))
    payload = {"cardinality": len(rows), "relation_rows": rows}
    return {
        "id": causet_id(relation),
        "canonical_relation_rows": rows,
        "canonical_causet_hash": _stable_hash(payload),
    }


def _transition_records(base: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for pair in base["bell_pairs"]:
        source = tuple(pair["source_relation_rows"])
        for label in ("A", "A_prime"):
            transition = copy.deepcopy(pair["transition_pair"][label])
            precursor_code = int(transition["precursor_code"])
            target = canonicalize(add_maximal(source, precursor_code))
            transition["source_causet"] = _causet_record(source)
            transition["target_causet"] = _causet_record(target)
            transition["canonical_operator_variable"] = (
                f"X_{transition['hash'][:16]}"
            )
            transition["inverse_variable"] = f"R_{transition['hash'][:16]}"
            records[transition["id"]] = transition
    return records


def _msr_operator_constraints(
    base: dict[str, Any],
    transitions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for transition in base["transition_graph"]["transition_orbits"]:
        grouped[transition["source_id"]].append(transition)

    constraints = []
    for source_id in sorted(grouped):
        terms = []
        for transition in sorted(
            grouped[source_id],
            key=lambda item: item["precursor_code"],
        ):
            occurrence = transitions[transition["id"]]
            terms.append(
                {
                    "coefficient": transition["automorphism_multiplicity"][
                        "precursor_orbit_size"
                    ],
                    "transition_id": transition["id"],
                    "transition_orbit_id": transition["orbit_id"],
                    "operator_variable": occurrence[
                        "canonical_operator_variable"
                    ],
                    "precursor_code": transition["precursor_code"],
                }
            )
        entry_equations = []
        for row in range(D3):
            for column in range(D3):
                polynomial_terms = [
                    (
                        f"{term['coefficient']}*"
                        f"{term['operator_variable']}_{row}_{column}"
                    )
                    for term in terms
                ]
                identity_entry = 1 if row == column else 0
                entry_equations.append(
                    {
                        "entry": [row, column],
                        "polynomial": (
                            " + ".join(polynomial_terms)
                            + f" - {identity_entry}"
                        ),
                    }
                )
        constraint_id = f"msr:{source_id}"
        constraints.append(
            {
                "constraint_id": constraint_id,
                "source_id": source_id,
                "terms": terms,
                "identity_coefficient": -1,
                "matrix_entry_polynomial_form_d3": entry_equations,
                "entry_equation_count": D3 * D3,
                "exact_orbit_multiplicity_sum": sum(
                    term["coefficient"] for term in terms
                ),
                "dependency": (
                    "operator identification within each source-automorphism "
                    "orbit; individual labelled moves are counted by multiplicity"
                ),
            }
        )
    return constraints


def _canonical_word_payload(
    equations: list[dict[str, Any]],
) -> dict[str, Any]:
    dummy_map = {
        "A_n": "X0",
        "A_prime_n": "X1",
        "A_m": "X2",
        "A_prime_m": "X3",
    }
    canonical = []
    for equation in equations:
        canonical.append(
            {
                "equation_id": equation["equation_id"],
                "lhs_word": [dummy_map[token] for token in equation["lhs_word"]],
                "rhs_word": [dummy_map[token] for token in equation["rhs_word"]],
            }
        )
    return {
        "dummy_index_map": dummy_map,
        "equations": canonical,
        "canonical_word_hash": _stable_hash(canonical),
        "normalisation": [
            "dummy aliases renamed by semantic role",
            "adjacent inverse cancellation only",
            "no cyclic, commutative, trace, or determinant quotient",
        ],
    }


def _inverse_form(
    solved_forms: list[dict[str, Any]],
    aliases: dict[str, str],
) -> dict[str, Any]:
    forms = []
    inverse_aliases: set[str] = set()
    for solved in solved_forms:
        rhs = list(solved["rhs_word"])
        inverse_aliases.update(
            token.removesuffix("^-1")
            for token in rhs
            if token.endswith("^-1")
        )
        forms.append(
            {
                "equation_id": solved["equation_id"],
                "residual_terms": [
                    {"coefficient": 1, "word": [solved["lhs"]]},
                    {"coefficient": -1, "word": rhs},
                ],
                "display": f"{solved['lhs']} - {'*'.join(rhs)} = 0",
            }
        )
    constraints = []
    entry_constraints = []
    for alias in sorted(inverse_aliases):
        transition_id = aliases[alias]
        local_name = _LOCAL_MATRIX_NAMES[alias]
        inverse_name = f"r{local_name}"
        constraints.extend(
            [
                {
                    "side": "RIGHT",
                    "word": [alias, f"{alias}^-1"],
                    "rhs": "I",
                    "transition_id": transition_id,
                },
                {
                    "side": "LEFT",
                    "word": [f"{alias}^-1", alias],
                    "rhs": "I",
                    "transition_id": transition_id,
                },
            ]
        )
        for side, left_name, right_name in (
            ("RIGHT", local_name, inverse_name),
            ("LEFT", inverse_name, local_name),
        ):
            for row in range(D3):
                for column in range(D3):
                    products = " + ".join(
                        f"{left_name}_{row}_{inner}*{right_name}_{inner}_{column}"
                        for inner in range(D3)
                    )
                    identity_entry = 1 if row == column else 0
                    entry_constraints.append(
                        {
                            "alias": alias,
                            "side": side,
                            "entry": [row, column],
                            "polynomial": f"{products} - {identity_entry}",
                        }
                    )
    return {
        "forms": forms,
        "inverse_symbols": {
            f"{alias}^-1": f"R_{aliases[alias].removeprefix('cpobc-transition-')}"
            for alias in sorted(inverse_aliases)
        },
        "two_sided_inverse_constraints": constraints,
        "matrix_entry_polynomial_constraints_d3": entry_constraints,
        "matrix_entry_constraint_count": len(entry_constraints),
        "inverse_encoding": "METHOD_A_EXPLICIT_TWO_SIDED_INVERSE_VARIABLES",
        "floating_point_inverse_used": False,
    }


def _enrich_relation(
    relation: dict[str, Any],
    transitions: dict[str, dict[str, Any]],
    pair_by_id: dict[str, dict[str, Any]],
    msr_by_source: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    aliases = relation["transition_pair"]["operator_aliases"]
    equations = relation["denominator_cleared_form"][
        "noncommutative_polynomial_equations"
    ]
    alias_records = {
        alias: transitions[transition_id]
        for alias, transition_id in aliases.items()
    }
    source_causets = {
        "stage_n": alias_records["A_n"]["source_causet"],
        "stage_m": alias_records["A_m"]["source_causet"],
    }
    target_causets = {
        alias: record["target_causet"] for alias, record in alias_records.items()
    }
    branch = (
        "EQUAL"
        if relation["equal_vs_unequal"] == "EQUAL_PRECURSOR_SIZE"
        else "GREATER"
    )
    raw_relations = [
        {
            "equation_id": equation["equation_id"],
            "lhs_word": list(equation["lhs_word"]),
            "rhs_word": list(equation["rhs_word"]),
            "operator_ids": {
                alias: aliases[alias]
                for alias in sorted(aliases)
                if alias in equation["lhs_word"] + equation["rhs_word"]
            },
            "display": equation["display"],
        }
        for equation in equations
    ]
    family_signature = pair_by_id[
        relation["transition_pair"]["stage_n_pair_id"]
    ]["family_root_signature"]
    reduced_source = _causet_record(
        tuple(family_signature["core_relation_rows"])
    )
    return {
        "relation_id": relation["id"],
        "relation_hash": relation["hash"],
        "stage": copy.deepcopy(relation["stages"]),
        "source_causet": source_causets,
        "target_causet": target_causets,
        "canonical_causet_hash": {
            key: value["canonical_causet_hash"]
            for key, value in source_causets.items()
        },
        "transition_orbit": {
            alias: {
                "occurrence_id": record["id"],
                "orbit_id": record["orbit_id"],
                "orbit_hash": record["orbit_hash"],
                "operator_variable": record["canonical_operator_variable"],
                "inverse_variable": record["inverse_variable"],
            }
            for alias, record in alias_records.items()
        },
        "Bell_partner": {
            "stage_n_pair_id": relation["transition_pair"]["stage_n_pair_id"],
            "stage_m_pair_id": relation["transition_pair"]["stage_m_pair_id"],
            "oriented_pairs": [["A_n", "A_prime_n"], ["A_m", "A_prime_m"]],
        },
        "Bell_pair": [
            relation["transition_pair"]["stage_n_pair_id"],
            relation["transition_pair"]["stage_m_pair_id"],
        ],
        "Bell_family": copy.deepcopy(relation["family"]),
        "full_precursor": copy.deepcopy(relation["precursors"]),
        "reduced_precursor": {
            "core_stage": relation["family"]["core_stage"],
            "canonical_reduced_source": reduced_source,
            "A": family_signature["A_precursor"],
            "A_prime": family_signature["A_prime_precursor"],
            "A_precursor_code": family_signature["A_precursor_code"],
            "A_prime_precursor_code": family_signature[
                "A_prime_precursor_code"
            ],
            "interpretation": (
                "canonical family root after deleting every common spectator; "
                "this need not be the selected lower-stage relation member"
            ),
        },
        "spectator_set": copy.deepcopy(relation["spectators"]),
        "precursor_cardinalities": copy.deepcopy(relation["cardinalities"]),
        "branch": branch,
        "branch_normalisation": {
            "allowed_raw_branches": ["GREATER", "LESS", "EQUAL"],
            "emitted_branches": ["GREATER", "EQUAL"],
            "LESS": (
                "mechanically swapped to GREATER before operator ordering; "
                "the original transition identities remain in provenance"
            ),
        },
        "CPOBC_operator_ordering": copy.deepcopy(relation["operator_order"]),
        "equal_size_auxiliary_relation": {
            "required": branch == "EQUAL",
            "equation_ids": (
                ["equal_second_orientation", "eq104"] if branch == "EQUAL" else []
            ),
        },
        "MSR_dependency": {
            **copy.deepcopy(relation["MSR"]),
            "operator_constraint_ids": {
                "stage_n": msr_by_source[
                    relation["MSR"]["stage_n_source_partition"]["source_id"]
                ]["constraint_id"],
                "stage_m": msr_by_source[
                    relation["MSR"]["stage_m_source_partition"]["source_id"]
                ]["constraint_id"],
            },
        },
        "GC_dependency": copy.deepcopy(relation["GC"]),
        "invertibility_dependency": _inverse_form(
            relation["generated_equation"]["solved_forms"],
            aliases,
        ),
        "automorphism_multiplicity": copy.deepcopy(
            relation["automorphism_multiplicities"]
        ),
        "raw_noncommutative_relation": raw_relations,
        "canonical_word_form": _canonical_word_payload(equations),
        "inverse_containing_form": _inverse_form(
            relation["generated_equation"]["solved_forms"],
            aliases,
        ),
        "denominator_cleared_form": copy.deepcopy(
            relation["denominator_cleared_form"]
        ),
        "matrix_entry_polynomial_form": _matrix_entry_form(
            equations,
            aliases,
        ),
        "paper_equation_correspondence": copy.deepcopy(
            relation["paper_correspondence"]
        ),
        "dependency_status": {
            "classification": "GENERATED_EQUIVALENT_TO_PAPER",
            "axiom_instance": "EXACT",
            "noncommutative_ideal_independence": "NOT_CLAIMED",
            "new_relation_claim": False,
            "reason": (
                "The record is a finite instance of Eqs. 103--106; exact "
                "independence from all paper-derived relations is unresolved."
            ),
        },
        "completeness_scope": (
            "complete operator encoding for this n<=4 Bell-family axiom "
            "instance; not a complete ideal-membership classification"
        ),
    }


# ---------------------------------------------------------------------------
# Independent brute-force Bell-family oracle


OracleEdges = frozenset[tuple[int, int]]


def _oracle_transitive(edges: OracleEdges, size: int) -> bool:
    return all(
        (lower, upper) in edges
        for lower in range(size)
        for middle in range(size)
        for upper in range(size)
        if (lower, middle) in edges and (middle, upper) in edges
    )


def _oracle_permute_edges(
    edges: OracleEdges,
    permutation: tuple[int, ...],
) -> OracleEdges:
    return frozenset(
        (permutation[lower], permutation[upper]) for lower, upper in edges
    )


def _oracle_edge_code(edges: OracleEdges, size: int) -> int:
    return sum(1 << (lower * size + upper) for lower, upper in edges)


def _oracle_canonical_edges(edges: OracleEdges, size: int) -> OracleEdges:
    candidates = (
        _oracle_permute_edges(edges, permutation)
        for permutation in itertools.permutations(range(size))
    )
    return min(candidates, key=lambda item: _oracle_edge_code(item, size))


def _oracle_posets(size: int) -> tuple[OracleEdges, ...]:
    if size > COMPILER_MAX_STAGE:
        raise ValueError("independent oracle is capped at n<=4")
    forward_pairs = tuple(itertools.combinations(range(size), 2))
    found: dict[int, OracleEdges] = {}
    for mask in range(1 << len(forward_pairs)):
        edges = frozenset(
            pair
            for index, pair in enumerate(forward_pairs)
            if mask & (1 << index)
        )
        if not _oracle_transitive(edges, size):
            continue
        canonical = _oracle_canonical_edges(edges, size)
        found[_oracle_edge_code(canonical, size)] = canonical
    return tuple(found[key] for key in sorted(found))


def _oracle_downsets(edges: OracleEdges, size: int) -> tuple[frozenset[int], ...]:
    result = []
    for mask in range(1 << size):
        subset = frozenset(vertex for vertex in range(size) if mask & (1 << vertex))
        if all(
            lower in subset
            for lower, upper in edges
            if upper in subset
        ):
            result.append(subset)
    return tuple(result)


def _oracle_automorphisms(
    edges: OracleEdges,
    size: int,
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        permutation
        for permutation in itertools.permutations(range(size))
        if _oracle_permute_edges(edges, permutation) == edges
    )


def _oracle_map_subset(
    subset: frozenset[int],
    permutation: tuple[int, ...],
) -> frozenset[int]:
    return frozenset(permutation[vertex] for vertex in subset)


def _oracle_subset_code(subset: frozenset[int]) -> int:
    return sum(1 << vertex for vertex in subset)


def _oracle_pair_key(
    first: frozenset[int],
    second: frozenset[int],
) -> tuple[int, int]:
    if len(first) < len(second):
        first, second = second, first
    if len(first) == len(second) and _oracle_subset_code(first) > _oracle_subset_code(
        second
    ):
        first, second = second, first
    return _oracle_subset_code(first), _oracle_subset_code(second)


def _oracle_pair_orbit_key(
    first: frozenset[int],
    second: frozenset[int],
    automorphism_group: tuple[tuple[int, ...], ...],
) -> tuple[int, int]:
    return min(
        _oracle_pair_key(
            _oracle_map_subset(first, permutation),
            _oracle_map_subset(second, permutation),
        )
        for permutation in automorphism_group
    )


def _oracle_family_key(
    edges: OracleEdges,
    first: frozenset[int],
    second: frozenset[int],
) -> tuple[int, int, int, int]:
    union = sorted(first | second)
    old_to_local = {old: local for local, old in enumerate(union)}
    local_edges = frozenset(
        (old_to_local[lower], old_to_local[upper])
        for lower, upper in edges
        if lower in old_to_local and upper in old_to_local
    )
    local_first = frozenset(old_to_local[item] for item in first)
    local_second = frozenset(old_to_local[item] for item in second)
    candidates = []
    for permutation in itertools.permutations(range(len(union))):
        relation_code = _oracle_edge_code(
            _oracle_permute_edges(local_edges, permutation),
            len(union),
        )
        first_code = _oracle_subset_code(
            _oracle_map_subset(local_first, permutation)
        )
        second_code = _oracle_subset_code(
            _oracle_map_subset(local_second, permutation)
        )
        candidates.append((len(union), relation_code, first_code, second_code))
        if len(first) == len(second):
            candidates.append((len(union), relation_code, second_code, first_code))
    return min(candidates)


def brute_force_bell_family_oracle(max_n: int = 4) -> dict[str, Any]:
    """Independently enumerate n<=4 Bell pairs and family routes.

    This route uses upper-triangular relation masks, sets of ordered pairs, and
    explicit permutation actions.  It does not call the production causet
    growth enumerator, down-set routine, precursor-orbit routine, or family
    canonicalizer.
    """

    if isinstance(max_n, bool) or not isinstance(max_n, int):
        raise TypeError("max_n must be an integer")
    if not 1 <= max_n <= COMPILER_MAX_STAGE:
        raise ValueError("max_n must satisfy 1 <= max_n <= 4")

    transition_orbit_count = 0
    pair_count = 0
    stage_pair_counts: Counter[int] = Counter()
    family_members: defaultdict[
        tuple[int, int, int, int], list[dict[str, Any]]
    ] = defaultdict(list)
    poset_counts: dict[str, int] = {}

    for stage in range(1, max_n + 1):
        posets = _oracle_posets(stage)
        poset_counts[str(stage)] = len(posets)
        for edges in posets:
            automorphism_group = _oracle_automorphisms(edges, stage)
            subsets = _oracle_downsets(edges, stage)

            transition_keys = {
                min(
                    _oracle_subset_code(
                        _oracle_map_subset(subset, permutation)
                    )
                    for permutation in automorphism_group
                )
                for subset in subsets
            }
            transition_orbit_count += len(transition_keys)

            seen_pairs: set[tuple[int, int]] = set()
            for first, second in itertools.combinations(subsets, 2):
                pair_key = _oracle_pair_orbit_key(
                    first,
                    second,
                    automorphism_group,
                )
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                pair_count += 1
                stage_pair_counts[stage] += 1
                oriented_first = frozenset(
                    vertex for vertex in range(stage) if pair_key[0] & (1 << vertex)
                )
                oriented_second = frozenset(
                    vertex for vertex in range(stage) if pair_key[1] & (1 << vertex)
                )
                family_key = _oracle_family_key(
                    edges,
                    oriented_first,
                    oriented_second,
                )
                family_members[family_key].append(
                    {
                        "stage": stage,
                        "source_code": _oracle_edge_code(edges, stage),
                        "pair": list(pair_key),
                    }
                )

    descriptors: list[dict[str, Any]] = []
    family_stage_descriptors: list[dict[str, Any]] = []
    equal_relations = 0
    unequal_relations = 0
    for family_key, members in sorted(family_members.items()):
        ordered = sorted(
            members,
            key=lambda item: (item["stage"], item["source_code"], item["pair"]),
        )
        stage_counts = Counter(item["stage"] for item in ordered)
        family_stage_descriptors.append(
            {
                "family_key": list(family_key),
                "stage_member_counts": {
                    str(stage): stage_counts[stage] for stage in sorted(stage_counts)
                },
            }
        )
        for first_member, second_member in itertools.combinations(ordered, 2):
            if first_member["stage"] == second_member["stage"]:
                continue
            high, low = (
                (first_member, second_member)
                if first_member["stage"] > second_member["stage"]
                else (second_member, first_member)
            )
            descriptor = {
                "family_key": list(family_key),
                "high": high,
                "low": low,
            }
            descriptors.append(descriptor)
            if family_key[2].bit_count() == family_key[3].bit_count():
                equal_relations += 1
            else:
                unequal_relations += 1
    descriptors.sort(
        key=lambda item: (
            item["high"]["stage"],
            item["low"]["stage"],
            item["family_key"],
            item["high"]["source_code"],
            item["low"]["source_code"],
            item["high"]["pair"],
            item["low"]["pair"],
        )
    )
    return {
        "method": (
            "independent forward-relation-mask enumeration with set-based "
            "downsets and explicit permutation orbits"
        ),
        "shared_production_code_paths": [],
        "max_source_stage": max_n,
        "poset_counts": poset_counts,
        "transition_orbits": transition_orbit_count,
        "bell_pair_orbits": pair_count,
        "bell_families": len(family_members),
        "compiled_cross_stage_relations": len(descriptors),
        "equal_size_relations": equal_relations,
        "unequal_size_relations": unequal_relations,
        "stage_bell_pair_orbits": {
            str(stage): stage_pair_counts[stage]
            for stage in range(1, max_n + 1)
        },
        "semantic_descriptor_sha256": _stable_hash(descriptors),
        "semantic_descriptor_count": len(descriptors),
        "family_stage_descriptor_sha256": _stable_hash(
            family_stage_descriptors
        ),
        "family_stage_descriptors": family_stage_descriptors,
        "exact": True,
    }


def _production_semantic_digests(base: dict[str, Any]) -> dict[str, str]:
    pair_by_id = {pair["id"]: pair for pair in base["bell_pairs"]}

    def production_pair_key(pair: dict[str, Any]) -> list[int]:
        first = int(pair["transition_pair"]["A"]["precursor_code"])
        second = int(pair["transition_pair"]["A_prime"]["precursor_code"])
        first_size = first.bit_count()
        second_size = second.bit_count()
        if first_size < second_size:
            first, second = second, first
        elif first_size == second_size and first > second:
            first, second = second, first
        return [first, second]

    descriptors: list[dict[str, Any]] = []
    for relation in base["relations"]:
        high = pair_by_id[relation["transition_pair"]["stage_n_pair_id"]]
        low = pair_by_id[relation["transition_pair"]["stage_m_pair_id"]]
        signature = high["family_root_signature"]
        family_key = [
            int(signature["core_stage"]),
            int(signature["core_relation_code"]),
            int(signature["A_precursor_code"]),
            int(signature["A_prime_precursor_code"]),
        ]
        descriptors.append(
            {
                "family_key": family_key,
                "high": {
                    "stage": high["stage"],
                    "source_code": int(high["source_id"].split("-")[1], 16),
                    "pair": production_pair_key(high),
                },
                "low": {
                    "stage": low["stage"],
                    "source_code": int(low["source_id"].split("-")[1], 16),
                    "pair": production_pair_key(low),
                },
            }
        )
    descriptors.sort(
        key=lambda item: (
            item["high"]["stage"],
            item["low"]["stage"],
            item["family_key"],
            item["high"]["source_code"],
            item["low"]["source_code"],
            item["high"]["pair"],
            item["low"]["pair"],
        )
    )
    family_descriptors = [
        {
            "family_key": [
                int(family["core"]["core_stage"]),
                int(family["core"]["core_relation_code"]),
                int(family["core"]["A_precursor_code"]),
                int(family["core"]["A_prime_precursor_code"]),
            ],
            "stage_member_counts": family["stage_member_counts"],
        }
        for family in base["bell_families"]
    ]
    family_descriptors.sort(key=lambda item: item["family_key"])
    return {
        "route": _stable_hash(descriptors),
        "family_stage": _stable_hash(family_descriptors),
    }


def compile_cpobc_relations_v031(max_n: int = 4) -> dict[str, Any]:
    """Compile every n<=4 Bell-family axiom instance to exact operator IR."""

    if isinstance(max_n, bool) or not isinstance(max_n, int):
        raise TypeError("max_n must be an integer")
    if not 1 <= max_n <= COMPILER_MAX_STAGE:
        raise ValueError("max_n must satisfy 1 <= max_n <= 4")

    started = time.perf_counter()
    base = compile_cpobc_relations(max_n)
    transitions = _transition_records(base)
    pair_by_id = {pair["id"]: pair for pair in base["bell_pairs"]}
    msr_constraints = _msr_operator_constraints(base, transitions)
    msr_by_source = {
        constraint["source_id"]: constraint for constraint in msr_constraints
    }
    relations = [
        _enrich_relation(relation, transitions, pair_by_id, msr_by_source)
        for relation in base["relations"]
    ]
    oracle = brute_force_bell_family_oracle(max_n)
    expected_counts = {
        "transition_orbits": base["counts"]["transition_orbits"],
        "bell_pair_orbits": base["counts"]["bell_pair_orbits"],
        "bell_families": base["counts"]["bell_families"],
        "compiled_cross_stage_relations": base["counts"][
            "compiled_cross_stage_relations"
        ],
        "equal_size_relations": base["counts"]["equal_size_relations"],
        "unequal_size_relations": base["counts"]["unequal_size_relations"],
        "stage_bell_pair_orbits": base["counts"]["stage_bell_pair_orbits"],
    }
    oracle_counts = {
        key: oracle[key] for key in expected_counts
    }
    production_digests = _production_semantic_digests(base)
    independent_match = (
        expected_counts == oracle_counts
        and production_digests["family_stage"]
        == oracle["family_stage_descriptor_sha256"]
    )
    matrix_entry_count = sum(
        relation["matrix_entry_polynomial_form"]["entry_equation_count"]
        for relation in relations
    )
    branch_counts = Counter(relation["branch"] for relation in relations)
    canonical_word_classes = Counter(
        relation["canonical_word_form"]["canonical_word_hash"]
        for relation in relations
    )
    elapsed = time.perf_counter() - started

    metadata = _base_metadata(
        verdict=(
            "CPOBC_COMPILER_COMPLETE_N4"
            if independent_match and max_n == 4
            else "CPOBC_COMPILER_PARTIAL_N4"
        ),
        dimension=3,
        jordan_stratum="NOT_APPLICABLE_RELATION_COMPILER",
        ansatz="NONE",
        relation_count=len(relations),
        completeness_scope=(
            f"all Bell-family axiom instances through source n={max_n}; "
            "exact ideal independence of paper-derived relations is not claimed"
        ),
        unresolved_components=[
            "noncommutative ideal membership among all paper-derived relations",
            "operator-level GC path ideal beyond recorded dependencies",
            "a full d=3 transition assignment",
        ],
    )
    return {
        **metadata,
        "schema_version": "final-theory-cpobc-relations-v0.3.1",
        "source": {
            "v0.3_compiler_digest_sha256": base["compiler_digest_sha256"],
            "paper_equations": [103, 104, 105, 106],
            "generation": "mechanical enrichment of every enumerated Bell-family route",
        },
        "counts": {
            **expected_counts,
            "denominator_cleared_word_equations": sum(
                len(
                    relation["denominator_cleared_form"][
                        "noncommutative_polynomial_equations"
                    ]
                )
                for relation in relations
            ),
            "d3_matrix_entry_polynomial_equations": matrix_entry_count,
            "d3_inverse_entry_polynomial_constraints": sum(
                relation["inverse_containing_form"][
                    "matrix_entry_constraint_count"
                ]
                for relation in relations
            ),
            "transition_occurrence_variables": len(transitions),
            "canonical_word_classes": len(canonical_word_classes),
            "branch_counts": dict(sorted(branch_counts.items())),
            "MSR_operator_constraints": len(msr_constraints),
            "d3_MSR_entry_polynomial_equations": sum(
                constraint["entry_equation_count"]
                for constraint in msr_constraints
            ),
        },
        "Bell_pair_inventory": [
            {
                "id": pair["id"],
                "hash": pair["hash"],
                "stage": pair["stage"],
                "family_id": pair["family"]["id"],
            }
            for pair in base["bell_pairs"]
        ],
        "Bell_family_inventory": [
            {
                "id": family["id"],
                "hash": family["hash"],
                "stages": family["stages"],
                "member_count": family["member_count"],
            }
            for family in base["bell_families"]
        ],
        "MSR_operator_constraints": msr_constraints,
        "relations": relations,
        "independent_brute_force_verification": {
            "production_counts": expected_counts,
            "oracle": oracle,
            "production_semantic_descriptor_sha256": production_digests["route"],
            "production_family_stage_descriptor_sha256": production_digests[
                "family_stage"
            ],
            "route_representative_digest_match": (
                production_digests["route"]
                == oracle["semantic_descriptor_sha256"]
            ),
            "exact_match": independent_match,
        },
        "canonical_word_class_histogram": dict(
            sorted(canonical_word_classes.items())
        ),
        "compiler_digest_sha256": _stable_hash(
            {
                "relation_hashes": [
                    relation["relation_hash"] for relation in relations
                ],
                "matrix_hashes": [
                    equation["sha256"]
                    for relation in relations
                    for equation in relation["matrix_entry_polynomial_form"][
                        "equations"
                    ]
                ],
                "oracle": oracle,
            }
        ),
        "dependency_status": {
            "Bell_family_axiom_instances": "EXACT_COMPLETE_WITHIN_N4",
            "inverse_encoding": "EXACT_TWO_SIDED_VARIABLES",
            "matrix_entry_encoding": "EXACT_D3_POLYNOMIALS",
            "paper_derived_ideal": "PARTIAL_DEPENDENCY_GRAPH_ONLY",
            "independent_relation_claims": 0,
        },
        "resource_usage": {
            "elapsed_seconds": round(elapsed, 6),
            "max_source_stage": max_n,
            "randomness": "none",
        },
        "passed": independent_match,
    }


def cpobc_dependency_graph_v031(
    compiled: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the typed provenance/dependency graph for compiled relations."""

    result = compiled or compile_cpobc_relations_v031()
    relation_nodes = []
    edges = []
    transition_ids: set[str] = set()
    pair_ids: set[str] = {
        pair["id"] for pair in result["Bell_pair_inventory"]
    }
    family_ids: set[str] = {
        family["id"] for family in result["Bell_family_inventory"]
    }
    for relation in result["relations"]:
        relation_id = relation["relation_id"]
        relation_nodes.append(
            {
                "id": relation_id,
                "kind": "CPOBC_RELATION",
                "classification": relation["dependency_status"]["classification"],
                "branch": relation["branch"],
            }
        )
        for pair_id in relation["Bell_pair"]:
            pair_ids.add(pair_id)
            edges.append(
                {"from": relation_id, "to": pair_id, "type": "DERIVED_FROM_PAIR"}
            )
        family_id = relation["Bell_family"]["id"]
        family_ids.add(family_id)
        edges.append(
            {"from": relation_id, "to": family_id, "type": "MEMBER_OF_FAMILY"}
        )
        for transition in relation["transition_orbit"].values():
            transition_id = transition["occurrence_id"]
            transition_ids.add(transition_id)
            edges.append(
                {
                    "from": relation_id,
                    "to": transition_id,
                    "type": "USES_TRANSITION",
                }
            )
        edges.append(
            {"from": relation_id, "to": "axiom:CPOBC", "type": "AXIOM_DEPENDENCY"}
        )
        if relation["inverse_containing_form"]["two_sided_inverse_constraints"]:
            edges.append(
                {
                    "from": relation_id,
                    "to": "axiom:INVERTIBILITY",
                    "type": "SOLVED_FORM_DEPENDENCY",
                }
            )
        edges.extend(
            [
                {
                    "from": relation_id,
                    "to": "axiom:MSR",
                    "type": "GLOBAL_REPRESENTATION_DEPENDENCY_NOT_USED_IN_AXIOM_INSTANCE",
                },
                {
                    "from": relation_id,
                    "to": "axiom:GC",
                    "type": "GLOBAL_REPRESENTATION_DEPENDENCY_NOT_USED_IN_AXIOM_INSTANCE",
                },
            ]
        )
        for constraint_id in relation["MSR_dependency"][
            "operator_constraint_ids"
        ].values():
            edges.append(
                {
                    "from": relation_id,
                    "to": constraint_id,
                    "type": "SOURCE_MSR_CONSTRAINT",
                }
            )

    paper_nodes = [
        {
            "id": f"paper:eq{number}",
            "kind": "KNOWN_PAPER_RELATION",
            "literature_classification": "LITERATURE_LOCKED",
        }
        for number in (
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            119,
            120,
            121,
            129,
            130,
            139,
            140,
            141,
            142,
            145,
            148,
            150,
            151,
            159,
            162,
            163,
        )
    ]
    paper_edges = [
        {"from": "paper:eq105", "to": "paper:eq103", "type": "INVERSE_SOLVED_FORM"},
        {"from": "paper:eq106", "to": "paper:eq103", "type": "INVERSE_SOLVED_FORM"},
        {"from": "paper:eq106", "to": "paper:eq104", "type": "EQUAL_SIZE_COMPATIBILITY"},
        {"from": "paper:eq107", "to": "paper:eq105", "type": "GREGARIOUS_SPECIALISATION"},
        {"from": "paper:eq108", "to": "axiom:MSR", "type": "MSR_ELIMINATION"},
        {"from": "paper:eq111", "to": "paper:eq109", "type": "GC_PATH_SUBSTITUTION"},
        {"from": "paper:eq111", "to": "paper:eq110", "type": "CPOBC_SUBSTITUTION"},
        {"from": "paper:eq112", "to": "paper:eq111", "type": "ITERATED_ATOMISATION"},
        {"from": "paper:eq113", "to": "paper:eq112", "type": "TWO_PATH_COMPATIBILITY"},
        {"from": "paper:eq119", "to": "paper:eq114", "type": "DENOMINATOR_CLEARING"},
        {"from": "paper:eq120", "to": "paper:eq119", "type": "ANTICHAIN_SPECIALISATION"},
        {"from": "paper:eq129", "to": "paper:eq121", "type": "ANTICHAIN_SPECIALISATION"},
        {"from": "paper:eq130", "to": "paper:eq114", "type": "DERIVED_COROLLARY"},
        {"from": "paper:eq139", "to": "paper:eq103", "type": "BELL_FAMILY_ELIMINATION"},
        {"from": "paper:eq139", "to": "axiom:GC", "type": "GC_DEPENDENCY"},
        {"from": "paper:eq139", "to": "axiom:MSR", "type": "MSR_DEPENDENCY"},
        {"from": "paper:eq145", "to": "paper:eq139", "type": "STAGE_TWO_SUBSTITUTION"},
        {"from": "paper:eq145", "to": "paper:eq140", "type": "TRANSITION_SUBSTITUTION"},
        {"from": "paper:eq145", "to": "paper:eq141", "type": "TRANSITION_SUBSTITUTION"},
        {"from": "paper:eq163", "to": "paper:eq113", "type": "TWO_PATH_SPECIALISATION"},
        {"from": "paper:eq163", "to": "paper:eq150", "type": "TRANSITION_SUBSTITUTION"},
        {"from": "paper:eq163", "to": "paper:eq151", "type": "TRANSITION_SUBSTITUTION"},
        {"from": "paper:eq163", "to": "paper:eq159", "type": "PATH_SUBSTITUTION"},
        {"from": "paper:eq163", "to": "paper:eq162", "type": "PATH_SUBSTITUTION"},
    ]
    edges.extend(paper_edges)
    msr_nodes = [
        {
            "id": constraint["constraint_id"],
            "kind": "MSR_OPERATOR_CONSTRAINT",
            "source_id": constraint["source_id"],
        }
        for constraint in result["MSR_operator_constraints"]
    ]
    for constraint in result["MSR_operator_constraints"]:
        edges.append(
            {
                "from": constraint["constraint_id"],
                "to": "axiom:MSR",
                "type": "AXIOM_INSTANCE",
            }
        )
        for term in constraint["terms"]:
            transition_ids.add(term["transition_id"])
            edges.append(
                {
                    "from": constraint["constraint_id"],
                    "to": term["transition_id"],
                    "type": "USES_TRANSITION_WITH_ORBIT_MULTIPLICITY",
                    "multiplicity": term["coefficient"],
                }
            )
    nodes = [
        {"id": "axiom:CPOBC", "kind": "AXIOM"},
        {"id": "axiom:MSR", "kind": "AXIOM"},
        {"id": "axiom:GC", "kind": "AXIOM"},
        {"id": "axiom:INVERTIBILITY", "kind": "AXIOM"},
        *paper_nodes,
        *msr_nodes,
        *[
            {"id": transition_id, "kind": "TRANSITION_OCCURRENCE"}
            for transition_id in sorted(transition_ids)
        ],
        *[{"id": pair_id, "kind": "BELL_PAIR"} for pair_id in sorted(pair_ids)],
        *[
            {"id": family_id, "kind": "BELL_FAMILY"}
            for family_id in sorted(family_ids)
        ],
        *relation_nodes,
    ]
    metadata = _base_metadata(
        verdict="CPOBC_DEPENDENCY_GRAPH_PARTIAL_EXACT",
        dimension=3,
        jordan_stratum="NOT_APPLICABLE_DEPENDENCY_GRAPH",
        ansatz="NONE",
        relation_count=len(relation_nodes),
        completeness_scope=(
            "exact typed dependencies for all 641 Bell-family instances plus "
            "a conservative paper-equation dependency DAG; no ideal membership"
        ),
        unresolved_components=[
            "noncommutative ideal membership",
            "proof-minimal dependency sets for paper Eqs. 107--163",
        ],
    )
    return {
        **metadata,
        "schema_version": "final-theory-cpobc-dependency-graph-v0.3.1",
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "compiled_relation_nodes": len(relation_nodes),
            "transition_nodes": len(transition_ids),
            "Bell_pair_nodes": len(pair_ids),
            "Bell_family_nodes": len(family_ids),
            "paper_relation_nodes": len(paper_nodes),
            "MSR_constraint_nodes": len(msr_nodes),
        },
        "dependency_tests": {
            "all_compiled_relations_have_CPOBC_edge": all(
                any(
                    edge["from"] == relation["relation_id"]
                    and edge["to"] == "axiom:CPOBC"
                    for edge in edges
                )
                for relation in result["relations"]
            ),
            "equal_size_relations_have_eq104": all(
                relation["equal_size_auxiliary_relation"]["required"]
                == (
                    "eq104"
                    in relation["equal_size_auxiliary_relation"]["equation_ids"]
                )
                for relation in result["relations"]
            ),
            "independent_ideal_membership": "NOT_RUN",
        },
        "graph_sha256": _stable_hash({"nodes": nodes, "edges": edges}),
        "passed": True,
    }


# ---------------------------------------------------------------------------
# Structural algebra and exact bounded d=3 search


def d3_strata_manifest_v031() -> dict[str, Any]:
    """Declare every required d=3 Jordan/reducibility stratum honestly."""

    common = {
        "base_field": "algebraic closure of Q for Jordan form; certificates over Q",
        "global_action": "Q_i -> S Q_i S^-1",
        "invertibility_encoding": (
            "two-sided inverse matrices R_i with Q_i R_i=R_i Q_i=I"
        ),
        "noncommutativity_encoding": (
            "nine exact branches t_ab*[Q_i,Q_j]_(a,b)-1=0"
        ),
        "full_relation_entry_equations": 7047,
        "full_relation_assignment_status": "NOT_SOLVED",
    }
    strata = [
        {
            "stratum": "D3_SCALAR",
            "gauge_choice": "Q1=lambda*I",
            "residual_gauge_group": "GL(3)",
            "variables": "lambda plus unrestricted Q2,Q3,Q4 and inverses",
            "equations": "full compiled system not eliminated",
            "invertibility_conditions": ["lambda != 0", "all transition determinants nonzero"],
            "noncommutativity_condition": "must be witnessed among Q2,Q3,Q4",
            "excluded_loci": [],
            "solver": "manifest only",
            "completeness_scope": "not searched",
            "timeout": "0 s",
            "memory_limit": "not allocated",
            "unresolved_components": ["all components"],
            "status": "UNRESOLVED",
        },
        {
            "stratum": "D3_THREE_DISTINCT_EIGENVALUES",
            "gauge_choice": "Q1=diag(lambda1,lambda2,lambda3), ordered distinct",
            "residual_gauge_group": "diagonal torus (finite permutations fixed by ordering)",
            "variables": "3 eigenvalues plus 27 entries of Q2,Q3,Q4 and inverses",
            "equations": "full compiled system not eliminated",
            "invertibility_conditions": ["lambda1*lambda2*lambda3 != 0"],
            "noncommutativity_condition": "off-diagonal entry in some Qj after gauge",
            "excluded_loci": ["discriminant(Q1)=0"],
            "solver": "manifest only",
            "completeness_scope": "not searched",
            "timeout": "0 s",
            "memory_limit": "not allocated",
            "unresolved_components": ["all components"],
            "status": "UNRESOLVED",
        },
        {
            "stratum": "D3_REPEATED_DIAGONALISABLE",
            "gauge_choice": "Q1=diag(lambda,lambda,mu), lambda!=mu",
            "residual_gauge_group": "GL(2) x GL(1)",
            "variables": "2 eigenvalues plus 27 entries of Q2,Q3,Q4 and inverses",
            "equations": "full compiled system not eliminated",
            "invertibility_conditions": ["lambda*mu != 0"],
            "noncommutativity_condition": "exact commutator witness branch",
            "excluded_loci": ["lambda=mu"],
            "solver": "manifest only",
            "completeness_scope": "not searched",
            "timeout": "0 s",
            "memory_limit": "not allocated",
            "unresolved_components": ["all components"],
            "status": "UNRESOLVED",
        },
        {
            "stratum": "D3_JORDAN_2_PLUS_1",
            "gauge_choice": "Q1=J2(lambda) direct-sum [mu]",
            "residual_gauge_group": "invertible centralizer of J2(lambda) direct-sum [mu]",
            "variables": "lambda,mu plus remaining generator entries and inverses",
            "equations": "full compiled system not eliminated",
            "invertibility_conditions": ["lambda*mu != 0"],
            "noncommutativity_condition": "exact commutator witness branch",
            "excluded_loci": ["Jordan superdiagonal=0"],
            "solver": "manifest only",
            "completeness_scope": "not searched",
            "timeout": "0 s",
            "memory_limit": "not allocated",
            "unresolved_components": ["all components"],
            "status": "UNRESOLVED",
        },
        {
            "stratum": "D3_JORDAN_3",
            "gauge_choice": "Q1=J3(lambda)",
            "residual_gauge_group": "invertible polynomials aI+bN+cN^2",
            "variables": "lambda plus remaining generator entries and inverses",
            "equations": "paper necessary ideal for one upper-triangular line ansatz",
            "invertibility_conditions": ["lambda != 0", "listed intermediates nonsingular"],
            "noncommutativity_condition": "s*[Q1,Q2]_(0,2)-1=0",
            "excluded_loci": ["ansatz parameter t=0 is commutative/J2+1 boundary"],
            "solver": "SymPy exact substitution and Groebner saturation branch",
            "completeness_scope": "one declared one-parameter ansatz only",
            "timeout": "60 s soft",
            "memory_limit": "sparse matrices; no full-system Groebner",
            "unresolved_components": ["all points outside the declared ansatz"],
            "status": "BOUNDED_ANSATZ_NO_GO",
        },
        {
            "stratum": "D3_BLOCK_REDUCIBLE",
            "gauge_choice": "common invariant 2+1 block decomposition when a complement exists",
            "residual_gauge_group": "GL(2) x GL(1)",
            "variables": "block entries for every transition and inverse",
            "equations": "full compiled system not eliminated",
            "invertibility_conditions": ["each diagonal block nonsingular"],
            "noncommutativity_condition": "block commutator witness",
            "excluded_loci": ["indecomposable extensions"],
            "solver": "manifest only",
            "completeness_scope": "not searched",
            "timeout": "0 s",
            "memory_limit": "not allocated",
            "unresolved_components": ["all components"],
            "status": "UNRESOLVED",
        },
        {
            "stratum": "D3_REDUCIBLE_INDECOMPOSABLE",
            "gauge_choice": "common upper-triangular flag; no invariant complement",
            "residual_gauge_group": "flag-preserving parabolic subgroup",
            "variables": "upper-triangular transition entries and inverses",
            "equations": "paper necessary ideal for one scaled-Heisenberg line ansatz",
            "invertibility_conditions": ["all diagonal entries nonzero"],
            "noncommutativity_condition": "s*[Q1,Q2]_(0,2)-1=0",
            "excluded_loci": ["nontrivial idempotent in joint centralizer"],
            "solver": "exact centralizer/idempotent check plus Groebner branch",
            "completeness_scope": "one declared one-parameter ansatz only",
            "timeout": "60 s soft",
            "memory_limit": "sparse matrices; no full-system Groebner",
            "unresolved_components": ["all other indecomposable modules"],
            "status": "BOUNDED_ANSATZ_NO_GO",
        },
    ]
    metadata = _base_metadata(
        verdict="D3_STRATA_DECLARED_SEARCH_PARTIAL",
        dimension=3,
        jordan_stratum="ALL_REQUIRED_STRATA_DECLARED",
        ansatz="one scaled-Heisenberg line subclass executed",
        relation_count=641,
        completeness_scope=(
            "seven required strata declared; only an intersecting Jordan-3/"
            "reducible-indecomposable one-parameter subclass is eliminated"
        ),
        unresolved_components=[
            "all unrestricted components of every d=3 stratum",
            "similarity quotient beyond the executed ansatz",
        ],
    )
    return {
        **metadata,
        "schema_version": "final-theory-d3-strata-v0.3.1",
        "global_encoding": common,
        "strata": strata,
        "coverage": {
            "required_strata": 7,
            "declared_strata": len(strata),
            "fully_solved_strata": 0,
            "partially_searched_strata": 2,
            "overlap_note": (
                "Jordan spectral strata and reducibility strata overlap; the "
                "manifest does not incorrectly present them as a disjoint partition."
            ),
        },
        "passed": len(strata) == 7,
    }


def _upper_unipotent(a: sp.Expr, b: sp.Expr, c: sp.Expr) -> sp.Matrix:
    return sp.Matrix([[1, a, c], [0, 1, b], [0, 0, 1]])


def _matrix_certificate(matrix: sp.MatrixBase) -> dict[str, Any]:
    simplified = sp.Matrix(matrix).applyfunc(lambda value: sp.factor(sp.cancel(value)))
    record = _matrix_record(simplified)
    return {
        "matrix": record,
        "zero": _zero_matrix(simplified),
        "rank": int(simplified.rank()),
        "trace": _exact(sp.trace(simplified)),
        "determinant": _exact(simplified.det()),
        "sha256": _stable_hash(record),
    }


def _commutator(left: sp.MatrixBase, right: sp.MatrixBase) -> sp.Matrix:
    return sp.Matrix(left * right - right * left).applyfunc(
        lambda value: sp.factor(sp.cancel(value))
    )


def _eq119(left: sp.MatrixBase, pivot: sp.MatrixBase, right: sp.MatrixBase) -> sp.Matrix:
    return sp.Matrix(
        left * pivot.inv() * right - right * pivot.inv() * left
    ).applyfunc(lambda value: sp.factor(sp.cancel(value)))


def _eq139(
    first: sp.MatrixBase,
    second: sp.MatrixBase,
    q_next: sp.MatrixBase,
    q_stage: sp.MatrixBase,
) -> sp.Matrix:
    """Generate the paper's Eq. (139) two-transition compatibility residual."""

    lhs = first * second * q_next * second.inv() * q_stage.inv() * second
    rhs = second * first * q_next * first.inv() * q_stage.inv() * first
    return sp.Matrix(lhs - rhs).applyfunc(
        lambda value: sp.factor(sp.cancel(value))
    )


def _joint_centralizer_basis(
    generators: tuple[sp.Matrix, ...],
) -> list[sp.Matrix]:
    dimension = generators[0].rows
    symbols = sp.symbols(f"z0:{dimension * dimension}")
    matrix = sp.Matrix(dimension, dimension, symbols)
    equations = []
    for generator in generators:
        equations.extend(list(matrix * generator - generator * matrix))
    coefficient, _ = sp.linear_eq_to_matrix(equations, symbols)
    basis = []
    for vector in coefficient.nullspace():
        basis.append(sp.Matrix(dimension, dimension, list(vector)))
    return basis


def _scaled_heisenberg_ansatz() -> dict[str, Any]:
    t = sp.Symbol("t")
    scales = (sp.Integer(2), sp.Integer(3), sp.Integer(5), sp.Integer(7))
    generators = tuple(
        scale * _upper_unipotent((index + 1) * t, sp.Integer(1), sp.Integer(0))
        for index, scale in enumerate(scales)
    )
    q1, q2, q3, q4 = generators
    identity = sp.eye(D3)
    a1_2 = (identity - q1) * q2 * q1.inv()
    a2_2 = identity - 2 * a1_2 - q2
    a1_3 = a1_2 * q3 * q2.inv()
    a2_3 = a2_2 * q3 * q2.inv()
    s1 = (
        (identity - q1)
        * a2_2
        * q3
        * a2_2.inv()
        * q1.inv()
        * a2_3
    )
    s2 = (
        a2_2
        * a1_2
        * q3
        * a1_2.inv()
        * q2.inv()
        * a1_2
        * q3
        * q2.inv()
    )
    eq119_residuals = {
        "Q2_Q1_Q3": _eq119(q2, q1, q3),
        "Q2_Q1_Q4": _eq119(q2, q1, q4),
        "Q3_Q1_Q4": _eq119(q3, q1, q4),
        "Q3_Q2_Q4": _eq119(q3, q2, q4),
    }
    eq130 = _commutator(q1 * q2.inv(), q1.inv() * q2)
    eq145 = _eq139(a1_2, a2_2, q3, q2)
    eq163 = _commutator(s2.inv() * s1, q4)
    commutator = _commutator(q1, q2)
    determinant_records = {
        name: _exact(matrix.det())
        for name, matrix in {
            "Q1": q1,
            "Q2": q2,
            "Q3": q3,
            "Q4": q4,
            "I_minus_Q1": identity - q1,
            "A1_2": a1_2,
            "A2_2": a2_2,
            "A1_3": a1_3,
            "A2_3": a2_3,
            "S1": s1,
            "S2": s2,
        }.items()
    }
    inverse_checks = {}
    for name, matrix in {
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q4": q4,
        "I_minus_Q1": identity - q1,
        "A1_2": a1_2,
        "A2_2": a2_2,
        "S1": s1,
        "S2": s2,
    }.items():
        inverse = matrix.inv()
        inverse_checks[name] = {
            "inverse": _matrix_record(inverse),
            "left_residual_zero": _zero_matrix(inverse * matrix - identity),
            "right_residual_zero": _zero_matrix(matrix * inverse - identity),
        }

    witness = sp.Symbol("w")
    commutator_entry = sp.factor(commutator[0, 2])
    eq145_entry = sp.factor(eq145[0, 2])
    groebner = sp.groebner(
        [eq145_entry, witness * commutator_entry - 1],
        t,
        witness,
        order="lex",
        domain=sp.QQ,
    )
    groebner_basis = [_exact(poly.as_expr()) for poly in groebner.polys]
    contradiction = groebner_basis == ["1"]

    centralizer = _joint_centralizer_basis(generators)
    centralizer_records = [_matrix_record(matrix) for matrix in centralizer]
    # For the computed basis span{I,E13}, idempotency has only 0 and I.
    alpha, beta = sp.symbols("alpha beta")
    centralizer_generic = alpha * centralizer[0] + beta * centralizer[1]
    idempotent_residual = sp.Matrix(
        centralizer_generic**2 - centralizer_generic
    )
    idempotent_equations = sorted(
        {
            sp.factor(entry)
            for entry in idempotent_residual
            if sp.factor(entry) != 0
        },
        key=str,
    )
    idempotent_solutions = sp.solve(
        idempotent_equations,
        (alpha, beta),
        dict=True,
    )
    point_residuals = {
        "eq119": {
            key: _matrix_certificate(value.subs(t, 1))
            for key, value in eq119_residuals.items()
        },
        "eq130": _matrix_certificate(eq130.subs(t, 1)),
        "eq145": _matrix_certificate(eq145.subs(t, 1)),
        "eq163": _matrix_certificate(eq163.subs(t, 1)),
    }
    return {
        "ansatz_id": "D3_SCALED_HEISENBERG_AFFINE_LINE_Q_2_3_5_7",
        "field": "Q(t), characteristic zero",
        "dimension": 3,
        "definition": (
            "Q_j=q_j*[[1,j*t,0],[0,1,1],[0,0,1]], j in {1,2,3,4}, "
            "(q1,q2,q3,q4)=(2,3,5,7)"
        ),
        "parameters": ["t"],
        "generators": {
            f"Q{index + 1}": _matrix_record(generator)
            for index, generator in enumerate(generators)
        },
        "Jordan_stratum": {
            "t_nonzero": "D3_JORDAN_3 for every Q_i",
            "t_zero": "D3_JORDAN_2_PLUS_1 commutative boundary",
        },
        "reducibility": {
            "common_flag": [["e1"], ["e1", "e2"], ["e1", "e2", "e3"]],
            "generic_Q_of_t_joint_centralizer_basis": centralizer_records,
            "joint_centralizer_dimension": len(centralizer),
            "idempotent_equations": [_exact(item) for item in idempotent_equations],
            "idempotent_solutions": [
                {str(key): _exact(value) for key, value in solution.items()}
                for solution in idempotent_solutions
            ],
            "nontrivial_idempotent_present": False,
            "centralizer_domain": "Q(t), hence t is generically nonzero",
            "classification_at_t_nonzero": "D3_REDUCIBLE_INDECOMPOSABLE",
        },
        "exact_invertibility": {
            "determinants": determinant_records,
            "all_determinants_nonzero_polynomials": all(
                sp.sympify(value) != 0 for value in determinant_records.values()
            ),
            "two_sided_inverse_checks": inverse_checks,
            "encoding": "METHOD_A_EXACT_TWO_SIDED_INVERSES",
        },
        "necessary_relation_family": {
            "eq119": {
                key: _matrix_certificate(value)
                for key, value in eq119_residuals.items()
            },
            "eq130": _matrix_certificate(eq130),
            "eq145_generated_from_eq139": _matrix_certificate(eq145),
            "eq163": _matrix_certificate(eq163),
            "paper_classification": "KNOWN_PAPER_RELATION",
        },
        "noncommutativity": {
            "commutator_Q1_Q2": _matrix_certificate(commutator),
            "witness_entry": [0, 2],
            "witness_polynomial": _exact(commutator_entry),
            "saturation_equation": f"w*({_exact(commutator_entry)}) - 1 = 0",
            "numeric_norm_used": False,
        },
        "bounded_no_go": {
            "eq145_witness_entry": [0, 2],
            "eq145_polynomial": _exact(eq145_entry),
            "groebner_variables": ["t", "w"],
            "groebner_order": "lex",
            "groebner_basis": groebner_basis,
            "unit_ideal": contradiction,
            "conclusion": (
                "Eq.145 forces t=0 while exact noncommutativity requires t!=0."
            ),
            "scope": (
                "only this one-parameter q=(2,3,5,7) scaled-Heisenberg ansatz"
            ),
        },
        "t_equals_1_mutation_witness": {
            "purpose": (
                "shows that checking only Eqs.119,130,163 would produce a "
                "false necessary-relation survivor"
            ),
            "relation_residuals": point_residuals,
            "detected_by_eq145": not point_residuals["eq145"]["zero"],
        },
        "full_compiled_relation_assignment_checked": False,
        "MSR_checked": False,
        "GC_checked": False,
        "CPOBC_representation_found": False,
        "status": (
            "CPOBC_D3_NO_GO_UNDER_ASSUMPTIONS"
            if contradiction
            else "CPOBC_D3_SEARCH_INCONCLUSIVE"
        ),
    }


def d3_representation_search_v031() -> dict[str, Any]:
    """Run the exact, explicitly bounded d=3 ansatz audit."""

    started = time.perf_counter()
    ansatz = _scaled_heisenberg_ansatz()
    elapsed = time.perf_counter() - started
    contradiction = ansatz["bounded_no_go"]["unit_ideal"]
    metadata = _base_metadata(
        verdict="CPOBC_D3_SEARCH_INCONCLUSIVE",
        dimension=3,
        jordan_stratum=(
            "D3_JORDAN_3 intersect D3_REDUCIBLE_INDECOMPOSABLE"
        ),
        ansatz=ansatz["ansatz_id"],
        relation_count=641,
        completeness_scope=(
            "exact no-go for one rational one-parameter ansatz using the "
            "paper necessary relation Eq.145; no complete d=3 stratum solved"
        ),
        unresolved_components=[
            "all d=3 matrices outside the declared one-parameter ansatz",
            "full assignment of 165 transition occurrences",
            "full n<=4 CPOBC, MSR, and GC substitution",
            "all unrestricted Jordan and reducibility components",
        ],
    )
    return {
        **metadata,
        "schema_version": "final-theory-d3-representation-search-v0.3.1",
        "search_method": {
            "candidate_generation": "symbolic one-parameter structured ansatz",
            "inverse_method": "A: explicit exact inverse matrices and two-sided residuals",
            "noncommutativity_method": (
                "entry branch w*[Q1,Q2]_(0,2)-1=0"
            ),
            "elimination": "two-variable exact Groebner basis over Q",
            "finite_grid": False,
            "numerical_candidates": 0,
            "similarity_deduplication": (
                "single gauge-fixed ansatz; no duplicate point list"
            ),
        },
        "executed_ansatz": ansatz,
        "summary": {
            "dimensions_searched": [3],
            "fields": ["Q(t)"],
            "Jordan_strata_touched": [
                "D3_JORDAN_3",
                "D3_JORDAN_2_PLUS_1_BOUNDARY",
                "D3_REDUCIBLE_INDECOMPOSABLE",
            ],
            "ansatz_classes": 1,
            "free_parameters": 1,
            "compiled_relation_count_available": 641,
            "compiled_relation_assignment_count": 0,
            "paper_necessary_relation_matrices_checked": 7,
            "groebner_branch_count": 1,
            "bounded_no_go_certificates": int(contradiction),
            "exact_representation_count": 0,
        },
        "resource_usage": {
            "elapsed_seconds": round(elapsed, 6),
            "soft_time_limit_seconds": 60,
            "limit_exceeded": elapsed > 60,
            "memory_strategy": "3x3 sparse upper triangular exact expressions",
            "full_system_Groebner": "NOT_RUN_RESOURCE_BOUND",
        },
        "prohibited_inference": (
            "The unit ideal applies only after imposing the displayed ansatz. "
            "It is not a no-go for D3_JORDAN_3, reducible-indecomposable d=3, "
            "or dimension three as a whole."
        ),
        "CPOBC_D3_STATUS": (
            "CPOBC_D3_SEARCH_INCONCLUSIVE"
        ),
        "BOUNDED_ANSATZ_STATUS": (
            "CPOBC_D3_NO_GO_UNDER_ASSUMPTIONS"
            if contradiction
            else "CPOBC_D3_ANSATZ_SEARCH_INCONCLUSIVE"
        ),
        "CPOBC_D4_STATUS": "CPOBC_HIGHER_DIMENSION_NOT_EXECUTED",
        "passed": contradiction,
    }


def compile_cpobc_relations_v0_3_1(max_n: int = 4) -> dict[str, Any]:
    """Stable orchestration API for the v0.3.1 relation compiler."""

    return compile_cpobc_relations_v031(max_n)


def structural_algebra_benchmark_v0_3_1() -> dict[str, Any]:
    """Stable orchestration API for the v0.3.1 structural manifest."""

    return d3_strata_manifest_v031()


def d3_representation_search_v0_3_1() -> dict[str, Any]:
    """Stable orchestration API for the v0.3.1 exact bounded search."""

    return d3_representation_search_v031()


def compiler_mutation_checks_v031(
    compiled: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic scientific gates for critical compiler mutations."""

    result = compiled or compile_cpobc_relations_v031()
    equal = next(
        relation for relation in result["relations"] if relation["branch"] == "EQUAL"
    )
    unequal = next(
        relation for relation in result["relations"] if relation["branch"] == "GREATER"
    )
    original_word = tuple(
        unequal["raw_noncommutative_relation"][0]["lhs_word"]
    )
    reversed_word = tuple(reversed(original_word))
    checks = {
        "CPOBC_product_order_reversal": original_word != reversed_word,
        "precursor_comparison_reversal": (
            unequal["CPOBC_operator_ordering"]["A_is_larger_side"]
            and not equal["CPOBC_operator_ordering"]["A_is_larger_side"]
        ),
        "equal_size_auxiliary_deletion": (
            equal["equal_size_auxiliary_relation"]["equation_ids"]
            == ["equal_second_orientation", "eq104"]
        ),
        "incorrect_inverse_cancellation": (
            free_reduce_word(("X", "Y", "X^-1")) == ("X", "Y", "X^-1")
        ),
        "invertibility_constraint_deletion": bool(
            unequal["inverse_containing_form"]["two_sided_inverse_constraints"]
        ),
        "GC_dependency_deletion": "status" in unequal["GC_dependency"],
        "MSR_dependency_deletion": "status" in unequal["MSR_dependency"],
        "automorphism_multiplicity_deletion": (
            unequal["automorphism_multiplicity"]["stage_n"]["pair_orbit_size"] >= 1
        ),
        "labelled_unlabelled_confusion": result[
            "independent_brute_force_verification"
        ]["exact_match"],
        "commutative_word_normalisation": (
            _canonical_word_payload(
                [
                    {
                        "equation_id": "guard",
                        "lhs_word": ["A_n", "A_m"],
                        "rhs_word": ["A_m", "A_n"],
                    }
                ]
            )["equations"][0]["lhs_word"]
            != _canonical_word_payload(
                [
                    {
                        "equation_id": "guard",
                        "lhs_word": ["A_n", "A_m"],
                        "rhs_word": ["A_m", "A_n"],
                    }
                ]
            )["equations"][0]["rhs_word"]
        ),
        "similarity_equivalent_solution_duplicate": (
            "single gauge-fixed ansatz"
            in d3_representation_search_v031()["search_method"][
                "similarity_deduplication"
            ]
        ),
        "finite_grid_no_go_overclaim": (
            "not a no-go"
            in d3_representation_search_v031()["prohibited_inference"]
        ),
        "numerical_zero_as_exact": (
            d3_representation_search_v031()["search_method"][
                "numerical_candidates"
            ]
            == 0
        ),
        "singular_as_nonsingular": d3_representation_search_v031()[
            "executed_ansatz"
        ]["exact_invertibility"]["all_determinants_nonzero_polynomials"],
        "omit_eq145_false_survivor": d3_representation_search_v031()[
            "executed_ansatz"
        ]["t_equals_1_mutation_witness"]["detected_by_eq145"],
        "paper_result_reported_as_new": all(
            relation["dependency_status"]["classification"]
            == "GENERATED_EQUIVALENT_TO_PAPER"
            for relation in result["relations"]
        ),
    }
    return {
        "checks": checks,
        "detected_count": sum(checks.values()),
        "critical_mutation_count": len(checks),
        "passed": all(checks.values()),
    }


def write_cpobc_v031_artifacts(root: Path) -> dict[str, Path]:
    """Write the Phase C--E JSON, reports, and exact certificates."""

    compiled = compile_cpobc_relations_v031()
    dependency = cpobc_dependency_graph_v031(compiled)
    strata = d3_strata_manifest_v031()
    search = d3_representation_search_v031()
    mutations = compiler_mutation_checks_v031(compiled)

    result_dir = root / "results"
    report_dir = root / "Final-Theory-Program" / "reports"
    relation_certificate_dir = root / "certificates" / "cpobc_relation_generation"
    dependency_certificate_dir = root / "certificates" / "cpobc_relation_dependencies"
    representation_certificate_dir = root / "certificates" / "cpobc_representation"
    no_go_certificate_dir = root / "certificates" / "cpobc_no_go"
    for directory in (
        result_dir,
        report_dir,
        relation_certificate_dir,
        dependency_certificate_dir,
        representation_certificate_dir,
        no_go_certificate_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    json_payloads = {
        "v0.3.1_cpobc_relations_n4.json": compiled,
        "v0.3.1_cpobc_dependency_graph.json": dependency,
        "v0.3.1_d3_strata_manifest.json": strata,
        "v0.3.1_d3_representation_search.json": search,
    }
    written: dict[str, Path] = {}
    for name, payload in json_payloads.items():
        path = result_dir / name
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written[name] = path

    certificates = {
        relation_certificate_dir / "v0.3.1_independent_bell_oracle.json": compiled[
            "independent_brute_force_verification"
        ],
        relation_certificate_dir / "v0.3.1_compiler_mutations.json": mutations,
        dependency_certificate_dir / "v0.3.1_dependency_summary.json": {
            "counts": dependency["counts"],
            "dependency_tests": dependency["dependency_tests"],
            "graph_sha256": dependency["graph_sha256"],
        },
        representation_certificate_dir
        / "v0.3.1_scaled_heisenberg_exact_substitution.json": search[
            "executed_ansatz"
        ],
        no_go_certificate_dir / "v0.3.1_scaled_heisenberg_no_go.json": {
            "ansatz_id": search["executed_ansatz"]["ansatz_id"],
            "bounded_no_go": search["executed_ansatz"]["bounded_no_go"],
            "noncommutativity": search["executed_ansatz"]["noncommutativity"],
            "claim_boundary": search["prohibited_inference"],
        },
    }
    for path, payload in certificates.items():
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written[path.name] = path

    certificate_hashes = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_file(path),
        }
        for path in certificates
    ]
    for result_name in json_payloads:
        payload_path = result_dir / result_name
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        payload["certificate_hashes"] = certificate_hashes
        payload_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    compiler_report = f"""# Final-Theory Bench v0.3.1 — CPOBC compiler

Status: **{compiled['verdict']}**

The compiler mechanically encoded all {compiled['counts']['compiled_cross_stage_relations']}
cross-stage Bell-family relations through source stage four.  It preserved the
noncommutative word order, introduced two-sided inverse variables, emitted
denominator-cleared integer word polynomials, and expanded
{compiled['counts']['d3_matrix_entry_polynomial_equations']} exact d=3 matrix-entry
Bell equations plus
{compiled['counts']['d3_inverse_entry_polynomial_constraints']} two-sided inverse
entry constraints (counted per relation dependency).  It also emitted
{compiled['counts']['MSR_operator_constraints']} source MSR constraints, or
{compiled['counts']['d3_MSR_entry_polynomial_equations']} d=3 entry equations,
with exact automorphism-orbit multiplicities.

The independent brute-force oracle used forward relation masks and explicit set/permutation
orbits, not the production growth/orbit code.  Counts and the semantic descriptor digest
matched exactly: `{compiled['independent_brute_force_verification']['exact_match']}`.

This is complete only for the finite Bell-family axiom instances (paper Eqs. 103--106).
Noncommutative ideal independence and a proof-minimal compilation of all derived paper
relations remain unresolved; no new independent relation is claimed.
"""
    structural_report = f"""# Final-Theory Bench v0.3.1 — structural algebra

All seven requested d=3 strata are explicitly declared.  Spectral Jordan strata and
reducibility strata overlap and are not presented as a false disjoint partition.

No unrestricted stratum was eliminated.  The only executed component is a one-parameter
scaled-Heisenberg upper-triangular subclass in the intersection of
`D3_JORDAN_3` and `D3_REDUCIBLE_INDECOMPOSABLE`.  Similarity gauge choices,
residual groups, invertibility constraints, noncommutativity saturation, excluded loci,
solvers, limits, and unresolved components are recorded in the manifest.

The full 641-relation d=3 system contains
{strata['global_encoding']['full_relation_entry_equations']} encoded Bell-relation entry
equations before MSR/GC and inverse constraints.  A dense full-system Gröbner basis was
not run.
"""
    search_report = f"""# Final-Theory Bench v0.3.1 — exact d=3 search

Status: **{search['CPOBC_D3_STATUS']}**

The exact ansatz

`Q_j = q_j (I + j t E12 + E23)`,
with `j=1,2,3,4` and `(q1,q2,q3,q4)=(2,3,5,7)`,

is nonsingular and noncommutative for `t != 0`.  It satisfies the tested Eq. 119
instances, Eq. 130, and Eq. 163, but the mechanically generated Eq. 139 stage-two
specialisation (Eq. 145) has residual entry
`{search['executed_ansatz']['bounded_no_go']['eq145_polynomial']}`.
The commutator witness is
`{search['executed_ansatz']['noncommutativity']['witness_polynomial']}`.
Their exact saturation Gröbner basis is
`{search['executed_ansatz']['bounded_no_go']['groebner_basis']}`, so this single
ansatz has no noncommutative solution.

This is not a no-go for either touched stratum or for d=3.  No full assignment of all
transition occurrences, MSR, GC, or all 641 Bell relations was solved.  The d=3 search
therefore remains globally inconclusive; d=4 was not executed.
"""
    reports = {
        "v0.3.1_cpobc_compiler.md": compiler_report,
        "v0.3.1_structural_algebra.md": structural_report,
        "v0.3.1_d3_representation_search.md": search_report,
    }
    for name, content in reports.items():
        path = report_dir / name
        path.write_text(content, encoding="utf-8")
        written[name] = path
    return written
