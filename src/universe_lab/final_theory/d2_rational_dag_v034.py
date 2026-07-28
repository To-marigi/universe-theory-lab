"""Fixed-d=2 rational reconstruction of the finite v0.3.3 operator DAG.

This module deliberately works in the commutative coordinate ring of generic
2 by 2 matrices.  Matrix multiplication remains ordered, while scalar
coordinate expressions are hash-consed and kept unexpanded.

It does *not* assert an abstract free-algebra Q-only presentation.  The
adjugate reduction used here is valid only after fixing the matrix dimension
to two.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from universe_lab.final_theory.atomisation_v033 import (
    _decorated_transition_signature,
)
from universe_lab.final_theory.cpobc_d2_v032 import generator_reduction_v032
from universe_lab.final_theory.eq112_reduction_v033 import (
    compile_eq112_reduction_n4,
)
from universe_lab.final_theory.gc_semantics_v033 import (
    PAPER_STRONG_OPERATOR_PROFILE,
    stable_hash,
)
from universe_lab.final_theory.operator_gc_v033 import (
    compile_local_operator_gc_n4,
)

BRANCH = "codex/final-theory-v0.3.4-d2-rational-elimination-20260728"
SOURCE_COMMIT = "7105bac9ee95fbbf23099b9945e6e0d69b149498"
VERDICT_COMPLETE = "D2_RATIONAL_DAG_COMPLETE"
VERDICT_PARTIAL = "D2_RATIONAL_DAG_PARTIAL"
VERDICT_BLOCKED = "D2_RATIONAL_DAG_BLOCKED_BY_GENUINE_AUXILIARY"
SCHEME = "FIXED_D2_RATIONAL_Q_SCHEME"

ExprId = str
MatrixEntries = tuple[tuple[ExprId, ExprId], tuple[ExprId, ExprId]]


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


class ScalarArena:
    """A small commutative scalar-expression DAG with structural interning."""

    def __init__(self) -> None:
        self.nodes: dict[ExprId, dict[str, Any]] = {}
        self._payload_to_id: dict[str, ExprId] = {}
        self.zero = self.const(0)
        self.one = self.const(1)
        self.minus_one = self.const(-1)

    def _intern(self, payload: dict[str, Any]) -> ExprId:
        encoded = _canonical_json(payload)
        existing = self._payload_to_id.get(encoded)
        if existing is not None:
            return existing
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        node_id = f"e:{digest}"
        collision = self.nodes.get(node_id)
        if collision is not None and collision != payload:
            raise RuntimeError("scalar expression hash collision")
        self.nodes[node_id] = payload
        self._payload_to_id[encoded] = node_id
        return node_id

    def const(self, value: int) -> ExprId:
        return self._intern({"op": "const", "value": int(value)})

    def symbol(self, name: str) -> ExprId:
        return self._intern({"op": "symbol", "name": name})

    def add(self, *items: ExprId) -> ExprId:
        flattened: list[ExprId] = []
        for item in items:
            node = self.nodes[item]
            if node["op"] == "add":
                flattened.extend(node["args"])
            else:
                flattened.append(item)
        coefficients: dict[tuple[ExprId, ...], int] = {}
        for item in flattened:
            node = self.nodes[item]
            if node["op"] == "const":
                key: tuple[ExprId, ...] = ()
                coefficient = int(node["value"])
            elif node["op"] == "mul":
                coefficient = 1
                factors: list[ExprId] = []
                for factor in node["args"]:
                    factor_node = self.nodes[factor]
                    if factor_node["op"] == "const":
                        coefficient *= int(factor_node["value"])
                    else:
                        factors.append(factor)
                key = tuple(sorted(factors))
            else:
                key = (item,)
                coefficient = 1
            coefficients[key] = coefficients.get(key, 0) + coefficient
        terms: list[ExprId] = []
        for factor_key, coefficient in sorted(coefficients.items()):
            if coefficient == 0:
                continue
            if not factor_key:
                terms.append(self.const(coefficient))
                continue
            base = (
                factor_key[0]
                if len(factor_key) == 1
                else self._intern({"op": "mul", "args": list(factor_key)})
            )
            terms.append(base if coefficient == 1 else self.mul(self.const(coefficient), base))
        if not terms:
            return self.zero
        ordered = sorted(terms)
        if len(ordered) == 1:
            return ordered[0]
        return self._intern({"op": "add", "args": ordered})

    def mul(self, *items: ExprId) -> ExprId:
        flattened: list[ExprId] = []
        constant = 1
        for item in items:
            node = self.nodes[item]
            if node["op"] == "const":
                constant *= int(node["value"])
            elif node["op"] == "mul":
                flattened.extend(node["args"])
            else:
                flattened.append(item)
        nonconstants: list[ExprId] = []
        for item in flattened:
            node = self.nodes[item]
            if node["op"] == "const":
                constant *= int(node["value"])
            else:
                nonconstants.append(item)
        if constant == 0:
            return self.zero
        if constant != 1:
            nonconstants.append(self.const(constant))
        if not nonconstants:
            return self.one
        ordered = sorted(nonconstants)
        if len(ordered) == 1:
            return ordered[0]
        return self._intern({"op": "mul", "args": ordered})

    def neg(self, item: ExprId) -> ExprId:
        return self.mul(self.minus_one, item)

    def sub(self, left: ExprId, right: ExprId) -> ExprId:
        return self.add(left, self.neg(right))

    def square(self, item: ExprId) -> ExprId:
        return self.mul(item, item)

    def record(self) -> dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "nodes": [
                {"expression_id": node_id, **self.nodes[node_id]}
                for node_id in sorted(self.nodes)
            ],
            "semantic_sha256": stable_hash(
                [
                    {"expression_id": node_id, **self.nodes[node_id]}
                    for node_id in sorted(self.nodes)
                ]
            ),
        }


@dataclass(frozen=True)
class RationalMatrix:
    """A 2 by 2 polynomial numerator over a scalar polynomial denominator."""

    numerator: MatrixEntries
    denominator: ExprId
    required_nonzero_factors: tuple[ExprId, ...] = ()
    provenance: tuple[str, ...] = ()


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


@dataclass
class D2RationalModel:
    """In-memory rational model used by localisation and exact strata code."""

    arena: ScalarArena
    q_matrices: dict[str, RationalMatrix]
    matrices: dict[str, RationalMatrix]
    node_definitions: dict[str, dict[str, Any]]
    denominator_factors: dict[str, dict[str, Any]] = field(default_factory=dict)
    occurrence_matrices: dict[str, RationalMatrix] = field(default_factory=dict)
    atomisation_matrices: dict[str, RationalMatrix] = field(default_factory=dict)
    local_path_matrices: dict[str, RationalMatrix] = field(default_factory=dict)

    def zero_matrix(self, provenance: str = "ZERO") -> RationalMatrix:
        z = self.arena.zero
        return RationalMatrix(((z, z), (z, z)), self.arena.one, (), (provenance,))

    def identity_matrix(self, provenance: str = "IDENTITY") -> RationalMatrix:
        z = self.arena.zero
        o = self.arena.one
        return RationalMatrix(((o, z), (z, o)), o, (), (provenance,))

    def add(
        self,
        left: RationalMatrix,
        right: RationalMatrix,
        *,
        provenance: str,
    ) -> RationalMatrix:
        arena = self.arena
        numerator = tuple(
            tuple(
                arena.add(
                    arena.mul(left.numerator[row][column], right.denominator),
                    arena.mul(right.numerator[row][column], left.denominator),
                )
                for column in range(2)
            )
            for row in range(2)
        )
        return RationalMatrix(
            numerator,  # type: ignore[arg-type]
            arena.mul(left.denominator, right.denominator),
            _ordered_unique(
                left.required_nonzero_factors + right.required_nonzero_factors
            ),
            _ordered_unique(left.provenance + right.provenance + (provenance,)),
        )

    def scale(
        self,
        coefficient: int,
        matrix: RationalMatrix,
        *,
        provenance: str,
    ) -> RationalMatrix:
        scalar = self.arena.const(coefficient)
        numerator = tuple(
            tuple(self.arena.mul(scalar, matrix.numerator[row][column]) for column in range(2))
            for row in range(2)
        )
        return RationalMatrix(
            numerator,  # type: ignore[arg-type]
            matrix.denominator,
            matrix.required_nonzero_factors,
            _ordered_unique(matrix.provenance + (provenance,)),
        )

    def subtract(
        self,
        left: RationalMatrix,
        right: RationalMatrix,
        *,
        provenance: str,
    ) -> RationalMatrix:
        return self.add(
            left,
            self.scale(-1, right, provenance=f"{provenance}:NEGATE"),
            provenance=provenance,
        )

    def multiply(
        self,
        left: RationalMatrix,
        right: RationalMatrix,
        *,
        provenance: str,
    ) -> RationalMatrix:
        arena = self.arena
        numerator = tuple(
            tuple(
                arena.add(
                    arena.mul(left.numerator[row][0], right.numerator[0][column]),
                    arena.mul(left.numerator[row][1], right.numerator[1][column]),
                )
                for column in range(2)
            )
            for row in range(2)
        )
        return RationalMatrix(
            numerator,  # type: ignore[arg-type]
            arena.mul(left.denominator, right.denominator),
            _ordered_unique(
                left.required_nonzero_factors + right.required_nonzero_factors
            ),
            _ordered_unique(left.provenance + right.provenance + (provenance,)),
        )

    def product(
        self,
        factors: Iterable[RationalMatrix],
        *,
        provenance: str,
    ) -> RationalMatrix:
        result = self.identity_matrix(f"{provenance}:EMPTY_PRODUCT")
        for index, factor in enumerate(factors):
            result = self.multiply(
                result,
                factor,
                provenance=f"{provenance}:FACTOR:{index}",
            )
        return result

    def determinant_numerator(self, matrix: RationalMatrix) -> ExprId:
        arena = self.arena
        return arena.sub(
            arena.mul(matrix.numerator[0][0], matrix.numerator[1][1]),
            arena.mul(matrix.numerator[0][1], matrix.numerator[1][0]),
        )

    def register_nonzero_factor(
        self,
        factor: ExprId,
        *,
        origin: str,
        stage: int | None,
        required_by: str,
        branch: str = "SHARED_CORE",
    ) -> None:
        key = stable_hash(
            {
                "factor": factor,
                "origin": origin,
                "required_by": required_by,
                "branch": branch,
            }
        )
        self.denominator_factors.setdefault(
            key,
            {
                "factor_record_id": f"denominator-factor-{key[:20]}",
                "factor_id": factor,
                "origin": origin,
                "branch": branch,
                "stage": stage,
                "required_by": [required_by],
                "square_free_form": factor,
                "multiplicity": 1,
                "saturation_status": "REQUIRED_NOT_YET_EXECUTED",
            },
        )

    def inverse(
        self,
        matrix: RationalMatrix,
        *,
        provenance: str,
        stage: int | None,
    ) -> RationalMatrix:
        arena = self.arena
        determinant = self.determinant_numerator(matrix)
        self.register_nonzero_factor(
            determinant,
            origin=f"det(numerator({provenance}))",
            stage=stage,
            required_by=provenance,
        )
        a, b = matrix.numerator[0]
        c, d = matrix.numerator[1]
        numerator: MatrixEntries = (
            (arena.mul(matrix.denominator, d), arena.mul(matrix.denominator, arena.neg(b))),
            (arena.mul(matrix.denominator, arena.neg(c)), arena.mul(matrix.denominator, a)),
        )
        return RationalMatrix(
            numerator,
            determinant,
            _ordered_unique(matrix.required_nonzero_factors + (determinant,)),
            _ordered_unique(matrix.provenance + (provenance,)),
        )

    def matrix_record(self, matrix: RationalMatrix) -> dict[str, Any]:
        determinant = self.determinant_numerator(matrix)
        factor_records = [
            factor
            for factor in self.denominator_factors.values()
            if factor["factor_id"] in matrix.required_nonzero_factors
        ]
        payload = {
            "numerator_matrix": [list(row) for row in matrix.numerator],
            "denominator": matrix.denominator,
            "numerator_determinant": determinant,
            "matrix_determinant": {
                "numerator": determinant,
                "denominator": self.arena.square(matrix.denominator),
            },
            "denominator_factor_provenance": [
                {
                    "factor_record_id": factor["factor_record_id"],
                    "factor_id": factor["factor_id"],
                    "origin": factor["origin"],
                    "required_by": factor["required_by"],
                }
                for factor in factor_records
            ],
            "required_nonzero_factors": list(matrix.required_nonzero_factors),
            "cancelled_factors": [],
            "cancellation_justification": "NO_CANCELLATION_PERFORMED",
            "expression_sha256": stable_hash(
                {
                    "numerator": matrix.numerator,
                    "denominator": matrix.denominator,
                }
            ),
            "dependency_sha256": stable_hash(matrix.provenance),
        }
        return payload


def _generic_q(arena: ScalarArena, stage: int) -> RationalMatrix:
    entries: MatrixEntries = (
        (arena.symbol(f"q{stage}_11"), arena.symbol(f"q{stage}_12")),
        (arena.symbol(f"q{stage}_21"), arena.symbol(f"q{stage}_22")),
    )
    return RationalMatrix(entries, arena.one, (), (f"Q_{stage}",))


def _node_for_generator_token(token: str) -> str:
    inverse = token.endswith("^-1")
    base = token.removesuffix("^-1")
    if base.startswith("Q_"):
        return base + ("^-1" if inverse else "")
    if base.startswith("G_p"):
        return f"G:{base.removeprefix('G_')}" + (":INV" if inverse else "")
    raise ValueError(f"unexpected v0.3.2 generator token: {token}")


def build_d2_rational_model() -> D2RationalModel:
    """Build the full fixed-d=2 rational model without eager expansion."""

    eq112 = compile_eq112_reduction_n4()
    definitions = {
        record["node_id"]: record for record in eq112["dependency_DAG"]["nodes"]
    }
    arena = ScalarArena()
    q_matrices = {f"Q_{stage}": _generic_q(arena, stage) for stage in range(1, 6)}
    model = D2RationalModel(
        arena=arena,
        q_matrices=q_matrices,
        matrices={},
        node_definitions=definitions,
    )
    visiting: list[str] = []

    def evaluate(node_id: str) -> RationalMatrix:
        existing = model.matrices.get(node_id)
        if existing is not None:
            return existing
        if node_id in visiting:
            raise RuntimeError(f"cycle in v0.3.3 dependency DAG: {visiting + [node_id]}")
        if node_id.startswith("Q_") and node_id not in definitions:
            inverse = node_id.endswith("^-1")
            base = node_id.removesuffix("^-1")
            direct = q_matrices[base]
            result = (
                model.inverse(
                    direct,
                    provenance=f"{node_id}:FIXED_D2_ADJUGATE",
                    stage=int(base.split("_", 1)[1]),
                )
                if inverse
                else direct
            )
            model.matrices[node_id] = result
            return result
        definition = definitions[node_id]
        visiting.append(node_id)
        kind = definition["kind"]
        if kind == "Q_GENERATOR":
            result = q_matrices[node_id]
        elif kind == "Q_GENERATOR_INVERSE":
            base = node_id.removesuffix("^-1")
            result = model.inverse(
                q_matrices[base],
                provenance=f"{node_id}:FIXED_D2_ADJUGATE",
                stage=int(definition["stage"]),
            )
        elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
            result = model.zero_matrix(f"{node_id}:SUM_ZERO")
            for term_index, term in enumerate(definition["terms"]):
                word = model.product(
                    (evaluate(item) for item in term["word_nodes"]),
                    provenance=f"{node_id}:TERM:{term_index}:WORD",
                )
                result = model.add(
                    result,
                    model.scale(
                        int(term["coefficient"]),
                        word,
                        provenance=f"{node_id}:TERM:{term_index}:COEFFICIENT",
                    ),
                    provenance=f"{node_id}:TERM:{term_index}:ACCUMULATE",
                )
        elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            result = model.inverse(
                evaluate(definition["inverse_of_node"]),
                provenance=f"{node_id}:FIXED_D2_ADJUGATE",
                stage=int(definition["stage"]),
            )
        elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
            result = model.product(
                (evaluate(item) for item in definition["ordered_word"]),
                provenance=f"{node_id}:ORDERED_EQ112_WORD",
            )
        else:
            raise ValueError(f"unsupported dependency-node kind: {kind}")
        visiting.pop()
        model.matrices[node_id] = result
        return result

    for node_id in sorted(definitions):
        evaluate(node_id)

    reduction = generator_reduction_v032()
    for occurrence in reduction["reduction_map"]:
        occurrence_id = occurrence["occurrence_id"]
        result = model.zero_matrix(f"{occurrence_id}:SUM_ZERO")
        for term_index, term in enumerate(occurrence["reduced_expression"]):
            word = model.product(
                (
                    evaluate(_node_for_generator_token(token))
                    for token in term["word"]
                ),
                provenance=f"{occurrence_id}:TERM:{term_index}:WORD",
            )
            result = model.add(
                result,
                model.scale(
                    int(term["coefficient"]),
                    word,
                    provenance=f"{occurrence_id}:TERM:{term_index}:COEFFICIENT",
                ),
                provenance=f"{occurrence_id}:TERM:{term_index}:ACCUMULATE",
            )
        model.occurrence_matrices[occurrence_id] = result
        determinant = model.determinant_numerator(result)
        model.register_nonzero_factor(
            determinant,
            origin=f"det(numerator({occurrence_id}))",
            stage=int(occurrence["stage"]),
            required_by=f"NONSINGULAR_TRANSITION:{occurrence_id}",
        )

    for path in eq112["path_reductions"]:
        model.atomisation_matrices[path["path_id"]] = model.product(
            (evaluate(node_id) for node_id in path["G_reduced_ordered_word"]),
            provenance=f"{path['path_id']}:EQ112_PATH_WORD",
        )

    local_gc = compile_local_operator_gc_n4()
    occurrence_by_signature: dict[
        tuple[tuple[str, int], ...], RationalMatrix
    ] = {}
    for occurrence in reduction["reduction_map"]:
        signature = _decorated_transition_signature(
            tuple(occurrence["source_relation_rows"]),
            int(occurrence["precursor_code"]),
        )
        occurrence_by_signature[tuple(sorted(signature.items()))] = (
            model.occurrence_matrices[occurrence["occurrence_id"]]
        )
    symbol_to_matrix: dict[str, RationalMatrix] = {}
    for stage_paths in local_gc["path_inventory"].values():
        for path in stage_paths:
            for transition in path["transitions"]:
                signature = transition["quotient_signature"]
                matrix = occurrence_by_signature.get(
                    tuple(sorted(signature.items()))
                )
                if matrix is None:
                    raise KeyError(f"missing rational B node for {signature}")
                symbol_to_matrix[transition["quotient_operator_symbol"]] = matrix
    for stage_paths in local_gc["path_inventory"].values():
        for path in stage_paths:
            model.local_path_matrices[path["path_id"]] = model.product(
                (
                    symbol_to_matrix[symbol]
                    for symbol in path["ordered_operator_word_later_on_left"]
                ),
                provenance=f"{path['path_id']}:LOCAL_GC_PATH_PRODUCT",
            )
    return model


def compile_d2_rational_dag_v034(
    *,
    include_expression_arena: bool = False,
) -> dict[str, Any]:
    """Return a serialisable certificate summary of the rational DAG."""

    model = build_d2_rational_model()
    definitions = model.node_definitions
    b_nodes = sorted(
        node_id
        for node_id, record in definitions.items()
        if record["kind"] == "EQ107_EQ108_LINEAR_EXPRESSION"
    )
    binv_nodes = sorted(
        node_id
        for node_id, record in definitions.items()
        if record["kind"] == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY"
    )
    g_nodes = sorted(
        node_id
        for node_id, record in definitions.items()
        if record["kind"] in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}
    )
    all_definitional = len(b_nodes) == 22 and len(binv_nodes) == 22
    complete = bool(
        all_definitional
        and len(model.occurrence_matrices) == 165
        and len(model.atomisation_matrices) == 34
        and len(model.local_path_matrices) == 407
    )
    verdict = VERDICT_COMPLETE if complete else VERDICT_PARTIAL
    rational_nodes = [
        {
            "node_id": node_id,
            "source_kind": definitions[node_id]["kind"],
            "stage": definitions[node_id].get("stage"),
            **model.matrix_record(model.matrices[node_id]),
        }
        for node_id in sorted(definitions)
    ]
    occurrences = generator_reduction_v032()["reduction_map"]
    occurrence_by_id = {record["occurrence_id"]: record for record in occurrences}
    payload: dict[str, Any] = {
        "schema_version": "final-theory-d2-rational-dag-v0.3.4",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "semantic_profile": PAPER_STRONG_OPERATOR_PROFILE,
        "source_index_branch": "SHARED_CORE_BRANCH_INDEPENDENT",
        "dimension": 2,
        "field": "characteristic-zero algebraically closed field",
        "scheme": SCHEME,
        "abstract_free_algebra_Q_only_claim": False,
        "coordinate_variables": [
            f"q{stage}_{row}{column}"
            for stage in range(1, 5)
            for row in range(1, 3)
            for column in range(1, 3)
        ],
        "rational_nodes": rational_nodes,
        "B_auxiliary_status": {
            "forward_B_nodes": b_nodes,
            "former_inverse_auxiliary_nodes": binv_nodes,
            "fixed_d2_treatment": "ADJUGATE_OVER_DETERMINANT",
            "all_are_definitional_in_fixed_d2_model": all_definitional,
        },
        "reconstructed_G_nodes": g_nodes,
        "reconstructed_transition_occurrences": [
            {
                "occurrence_id": occurrence_id,
                "operator_variable": occurrence_by_id[occurrence_id][
                    "operator_variable"
                ],
                "transition_kind": occurrence_by_id[occurrence_id][
                    "transition_kind"
                ],
                "stage": occurrence_by_id[occurrence_id]["stage"],
                "source_id": occurrence_by_id[occurrence_id]["source_id"],
                "target_id": occurrence_by_id[occurrence_id]["target_id"],
                **model.matrix_record(matrix),
            }
            for occurrence_id, matrix in sorted(model.occurrence_matrices.items())
        ],
        "atomisation_path_products": [
            {
                "path_id": path_id,
                **model.matrix_record(matrix),
            }
            for path_id, matrix in sorted(model.atomisation_matrices.items())
        ],
        "local_GC_path_products": [
            {
                "path_id": path_id,
                **model.matrix_record(matrix),
            }
            for path_id, matrix in sorted(model.local_path_matrices.items())
        ],
        "denominator_factors": list(model.denominator_factors.values()),
        "expression_arena": (
            model.arena.record()
            if include_expression_arena
            else {
                "node_count": len(model.arena.nodes),
                "semantic_sha256": stable_hash(
                    [
                        {
                            "expression_id": node_id,
                            **model.arena.nodes[node_id],
                        }
                        for node_id in sorted(model.arena.nodes)
                    ]
                ),
                "nodes_embedded": False,
                "certificate_path": (
                    "certificates/d2_rational_dag/"
                    "scalar_expression_arena.json"
                ),
            }
        ),
        "counts": {
            "Q_coordinate_variables_core": 16,
            "Q_coordinate_variables_literal_branch_extension": 20,
            "dependency_nodes": len(definitions),
            "B_forward_definitions": len(b_nodes),
            "B_inverses_rationally_reconstructed": len(binv_nodes),
            "G_and_G_inverse_nodes": len(g_nodes),
            "transition_occurrences": len(model.occurrence_matrices),
            "atomisation_paths": len(model.atomisation_matrices),
            "local_GC_path_products": len(model.local_path_matrices),
            "scalar_expression_DAG_nodes": len(model.arena.nodes),
            "nonzero_factor_occurrences": len(model.denominator_factors),
        },
        "denominator_discipline": {
            "unproved_cancellations": 0,
            "all_inverse_sites_register_numerator_determinants": True,
            "all_transition_occurrences_register_nonsingularity": True,
            "saturation_executed_here": False,
        },
        "assumptions": [
            "PAPER_STRONG_OPERATOR_PROFILE",
            "fixed matrix dimension d=2",
            "characteristic zero",
            "all inverse-site determinants are nonzero",
            "all 165 reconstructed transition determinants are nonzero",
        ],
        "completeness_scope": (
            "rational reconstruction DAG for all n<=4 source-stage operators; "
            "polynomial elimination is delegated to localisation/stratum modules"
        ),
        "exact_numeric_distinction": "EXACT_STRUCTURAL_RATIONAL_DAG",
        "unresolved_components": [
            "forward/reverse equivalence of the reduced and original ideals",
            "saturation and S1/S2/S3 elimination",
            "literal Eq.(113) branch requires independent Q_5 coordinates",
        ],
        "passed": complete,
        "verdict": verdict,
    }
    payload["semantic_digest_sha256"] = stable_hash(
        {
            "scheme": payload["scheme"],
            "node_hashes": [
                (record["node_id"], record["expression_sha256"])
                for record in rational_nodes
            ],
            "occurrence_hashes": [
                (record["occurrence_id"], record["expression_sha256"])
                for record in payload["reconstructed_transition_occurrences"]
            ],
            "denominator_factors": [
                record["factor_id"] for record in payload["denominator_factors"]
            ],
        }
    )
    return payload


d2_rational_dag_v034 = compile_d2_rational_dag_v034
